import datetime
import json
import os
import re
import time

from Py4GWCoreLib import GLOBAL_CACHE, Item, ItemArray, Map, Party, Player, Py4GW, Routines
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Py4GWCoreLib.enums import SharedCommandType
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.helpers.custom_behavior_helpers_party import CustomBehaviorHelperParty
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_protocol import (
    build_drop_meta,
    build_name_chunks,
    encode_name_chunk_meta,
    make_event_id,
    make_name_signature,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_inventory_delta_filter import (
    filter_candidate_events_by_model_delta,
)
from Sources.oazix.CustomBehaviors.skills.monitoring.item_mod_render_utils import (
    build_known_spellcasting_mod_lines,
    prune_generic_attribute_bonus_lines,
    render_mod_description_template,
    sort_stats_lines_like_ingame,
)

IMPORT_OPTIONAL_ERRORS = (ImportError, ModuleNotFoundError, AttributeError)
EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)

try:
    from Py4GWCoreLib.enums_src.Item_enums import ItemType
    from Sources.marks_sources.mods_parser import ModDatabase, parse_modifiers, is_matching_item_type
except IMPORT_OPTIONAL_ERRORS:
    ItemType = None
    ModDatabase = None
    parse_modifiers = None
    is_matching_item_type = None


class DropTrackerSender:
    """
    Non-blocking shared-memory drop sender.
    Runs from daemon() and never participates in utility score arbitration.
    """

    _instance = None
    _STATE_VERSION = 15

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DropTrackerSender, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            # Hot-reload/session safety: if schema/version changed, force a clean baseline.
            if getattr(self, "state_version", 0) != self._STATE_VERSION:
                if not hasattr(self, "pending_slot_deltas"):
                    self.pending_slot_deltas = {}
                if not hasattr(self, "outbox_queue"):
                    self.outbox_queue = []
                if not hasattr(self, "stable_snapshot_count"):
                    self.stable_snapshot_count = 0
                if not hasattr(self, "warmup_grace_seconds"):
                    self.warmup_grace_seconds = 3.0
                if not hasattr(self, "warmup_grace_until"):
                    self.warmup_grace_until = 0.0
                if not hasattr(self, "pending_ttl_seconds"):
                    self.pending_ttl_seconds = 6.0
                if not hasattr(self, "debug_pipeline_logs"):
                    self.debug_pipeline_logs = False
                if not hasattr(self, "max_outbox_size"):
                    self.max_outbox_size = 2000
                if not hasattr(self, "last_known_is_leader"):
                    self.last_known_is_leader = False
                if not hasattr(self, "enable_delivery_ack"):
                    self.enable_delivery_ack = True
                if not hasattr(self, "retry_interval_seconds"):
                    self.retry_interval_seconds = 1.0
                if not hasattr(self, "max_retry_attempts"):
                    self.max_retry_attempts = 12
                if not hasattr(self, "enable_perf_logs"):
                    self.enable_perf_logs = False
                if not hasattr(self, "event_sequence"):
                    self.event_sequence = 0
                if not hasattr(self, "last_seen_map_id"):
                    self.last_seen_map_id = 0
                if not hasattr(self, "runtime_config_path"):
                    self.runtime_config_path = os.path.join(
                        os.path.dirname(constants.DROP_LOG_PATH),
                        "drop_tracker_runtime_config.json",
                    )
                if not hasattr(self, "last_inventory_activity_ts"):
                    self.last_inventory_activity_ts = 0.0
                if not hasattr(self, "sent_event_stats_cache"):
                    self.sent_event_stats_cache = {}
                if not hasattr(self, "sent_event_stats_ttl_seconds"):
                    self.sent_event_stats_ttl_seconds = 600.0
                if not hasattr(self, "max_stats_builds_per_tick"):
                    self.max_stats_builds_per_tick = 2
                self.inventory_poll_timer = ThrottledTimer(250)
                self.state_version = self._STATE_VERSION
                self._reset_tracking_state()
            return
        self._initialized = True
        self.state_version = self._STATE_VERSION
        self.inventory_poll_timer = ThrottledTimer(250)
        self.last_inventory_snapshot: dict[tuple[int, int], tuple[str, str, int, int, int]] = {}
        self.enabled = True
        self.gold_regex = re.compile(r"^(?:\[([\d: ]+[ap]m)\] )?Your party shares ([\d,]+) gold\.$")
        self.warn_timer = ThrottledTimer(3000)
        self.debug_timer = ThrottledTimer(5000)
        self.snapshot_error_timer = ThrottledTimer(5000)
        self.debug_enabled = True
        self.last_snapshot_total = 0
        self.last_snapshot_ready = 0
        self.last_snapshot_not_ready = 0
        self.last_sent_count = 0
        self.last_candidate_count = 0
        self.last_enqueued_count = 0
        self.is_warmed_up = False
        self.stable_snapshot_count = 0
        self.pending_slot_deltas: dict[tuple[int, int], dict] = {}
        self.outbox_queue: list[dict] = []
        self.max_send_per_tick = 12
        self.max_outbox_size = 2000
        self.warmup_grace_seconds = 3.0
        self.warmup_grace_until = 0.0
        self.pending_ttl_seconds = 6.0
        self.debug_pipeline_logs = False
        self.last_known_is_leader = False
        self.enable_delivery_ack = True
        self.retry_interval_seconds = 1.0
        self.max_retry_attempts = 12
        self.enable_perf_logs = False
        self.event_sequence = 0
        self.last_seen_map_id = 0
        self.last_process_duration_ms = 0.0
        self.last_ack_count = 0
        self.last_inventory_activity_ts = 0.0
        self.sent_event_stats_cache: dict[str, dict] = {}
        self.sent_event_stats_ttl_seconds = 600.0
        self.max_stats_builds_per_tick = 2
        self.runtime_config_path = os.path.join(
            os.path.dirname(constants.DROP_LOG_PATH),
            "drop_tracker_runtime_config.json",
        )
        self.ack_poll_timer = ThrottledTimer(250)
        self.config_poll_timer = ThrottledTimer(2000)
        self.mod_db = None
        self._load_mod_database()

    def _load_mod_database(self):
        if ModDatabase is None:
            self.mod_db = None
            return
        candidate_dirs = []
        try:
            # .../Sources/oazix/CustomBehaviors/skills/monitoring -> .../Sources
            sources_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            candidate_dirs.append(
                os.path.join(
                    sources_root,
                    "marks_sources",
                    "mods_data",
                )
            )
        except EXPECTED_RUNTIME_ERRORS:
            pass
        try:
            project_root = Py4GW.Console.get_projects_path()
            if project_root:
                candidate_dirs.append(
                    os.path.join(
                        project_root,
                        "Sources",
                        "marks_sources",
                        "mods_data",
                    )
                )
        except EXPECTED_RUNTIME_ERRORS:
            pass

        seen = set()
        for data_dir in candidate_dirs:
            norm = os.path.normcase(os.path.normpath(str(data_dir or "")))
            if not norm or norm in seen:
                continue
            seen.add(norm)
            if not os.path.isdir(data_dir):
                continue
            try:
                self.mod_db = ModDatabase.load(data_dir)
                if self.mod_db is not None:
                    return
            except EXPECTED_RUNTIME_ERRORS:
                continue
        self.mod_db = None

    def _format_attribute_name(self, attr_name: str) -> str:
        txt = str(attr_name or "").replace("_", " ").strip()
        if txt.lower() == "none":
            return ""
        return txt

    def _render_mod_description_template(
        self,
        description: str,
        matched_modifiers: list[tuple[int, int, int]],
        default_value: int = 0,
        attribute_name: str = "",
    ) -> list[str]:
        def _resolve_attribute_name(attr_id: int) -> str:
            try:
                from Py4GWCoreLib.enums import Attribute
                return self._format_attribute_name(getattr(Attribute(int(attr_id)), "name", ""))
            except EXPECTED_RUNTIME_ERRORS:
                return ""

        return render_mod_description_template(
            description=str(description or ""),
            matched_modifiers=list(matched_modifiers or []),
            default_value=int(default_value),
            attribute_name=str(attribute_name or ""),
            resolve_attribute_name_fn=_resolve_attribute_name,
            format_attribute_name_fn=self._format_attribute_name,
            unknown_attribute_template="Attribute {id}",
        )

    def _match_mod_definition_against_raw(self, definition_modifiers, raw_mods) -> list[tuple[int, int, int]]:
        meaningful = []
        for dm in list(definition_modifiers or []):
            mode = str(getattr(dm, "modifier_value_arg", "")).lower()
            if "none" in mode:
                continue
            meaningful.append(dm)
        if not meaningful:
            return []

        matched = []
        for dm in meaningful:
            ident = int(getattr(dm, "identifier", 0))
            arg1 = int(getattr(dm, "arg1", 0))
            arg2 = int(getattr(dm, "arg2", 0))
            min_v = int(getattr(dm, "min", 0))
            max_v = int(getattr(dm, "max", 0))
            mode = str(getattr(dm, "modifier_value_arg", "")).lower()
            found = None
            for rid, ra1, ra2 in raw_mods:
                if int(rid) != ident:
                    continue
                if "arg1" in mode:
                    if int(ra2) == arg2 and min_v <= int(ra1) <= max_v:
                        found = (int(rid), int(ra1), int(ra2))
                        break
                elif "arg2" in mode:
                    if int(ra1) == arg1 and min_v <= int(ra2) <= max_v:
                        found = (int(rid), int(ra1), int(ra2))
                        break
                elif "fixed" in mode:
                    if int(ra1) == arg1 and int(ra2) == arg2:
                        found = (int(rid), int(ra1), int(ra2))
                        break
            if found is None:
                return []
            matched.append(found)
        return matched

    def _weapon_mod_type_matches(self, weapon_mod, item_type) -> bool:
        if item_type is None or is_matching_item_type is None:
            return False
        try:
            target_types = list(getattr(weapon_mod, "target_types", []) or [])
            for target in target_types:
                try:
                    if is_matching_item_type(item_type, target):
                        return True
                except EXPECTED_RUNTIME_ERRORS:
                    continue
            item_mods = getattr(weapon_mod, "item_mods", {}) or {}
            for target in list(item_mods.keys()):
                try:
                    if is_matching_item_type(item_type, target):
                        return True
                except EXPECTED_RUNTIME_ERRORS:
                    continue
        except EXPECTED_RUNTIME_ERRORS:
            return False
        return False

    def _collect_fallback_mod_lines(self, raw_mods, item_attr_txt: str, item_type=None) -> list[str]:
        lines = []
        if self.mod_db is None:
            return lines
        best_by_ident = {}
        try:
            for weapon_mod in list(getattr(self.mod_db, "weapon_mods", {}).values()):
                matched = self._match_mod_definition_against_raw(getattr(weapon_mod, "modifiers", []), raw_mods)
                if not matched:
                    continue
                ident_set = {int(m[0]) for m in matched}
                if not ident_set:
                    continue
                desc = str(getattr(weapon_mod, "description", "") or "").strip()
                rendered = self._render_mod_description_template(desc, matched, 0, item_attr_txt)
                if rendered:
                    first_line = rendered[0]
                    lower_desc = desc.lower()
                    has_old_school = "[old school]" in lower_desc
                    type_match = self._weapon_mod_type_matches(weapon_mod, item_type)
                    score = 0
                    if type_match:
                        score += 100
                    if has_old_school:
                        score += 20
                    if not type_match and not has_old_school:
                        score -= 60
                    score += min(len(matched), 3)
                    for ident in ident_set:
                        prev = best_by_ident.get(ident, None)
                        if prev is None or score > int(prev.get("score", -999)):
                            best_by_ident[ident] = {"line": first_line, "score": score}
        except EXPECTED_RUNTIME_ERRORS:
            return lines
        for ident in sorted(best_by_ident.keys()):
            line = str(best_by_ident[ident].get("line", "")).strip()
            if line:
                lines.append(line)
        return lines

    def _collect_fallback_rune_lines(self, raw_mods, item_attr_txt: str) -> list[str]:
        lines = []
        if self.mod_db is None:
            return lines
        best_by_ident = {}
        try:
            for rune in list(getattr(self.mod_db, "runes", {}).values()):
                matched = self._match_mod_definition_against_raw(getattr(rune, "modifiers", []), raw_mods)
                if not matched:
                    continue
                ident_set = {int(m[0]) for m in matched}
                if not ident_set:
                    continue
                desc = str(getattr(rune, "description", "") or "").strip()
                rune_name = str(getattr(rune, "name", "") or "").strip()
                rendered = self._render_mod_description_template(desc, matched, 0, item_attr_txt)
                candidate_lines = []
                if rune_name:
                    candidate_lines.append(rune_name)
                candidate_lines.extend(rendered)
                if not candidate_lines and rune_name:
                    candidate_lines = [rune_name]
                deduped_candidates = []
                seen_line_keys = set()
                for candidate in candidate_lines:
                    candidate_txt = str(candidate or "").strip()
                    if not candidate_txt:
                        continue
                    line_key = re.sub(r"[^a-z0-9]+", "", candidate_txt.lower())
                    if line_key in seen_line_keys:
                        continue
                    seen_line_keys.add(line_key)
                    deduped_candidates.append(candidate_txt)
                candidate_lines = deduped_candidates
                if not candidate_lines:
                    continue
                score = min(len(matched), 4)
                for ident in ident_set:
                    prev = best_by_ident.get(ident, None)
                    if prev is None or score > int(prev.get("score", -999)):
                        best_by_ident[ident] = {"lines": list(candidate_lines), "score": score}
        except EXPECTED_RUNTIME_ERRORS:
            return lines
        for ident in sorted(best_by_ident.keys()):
            for line in list(best_by_ident[ident].get("lines", []) or []):
                txt = str(line or "").strip()
                if txt:
                    lines.append(txt)
        return lines

    def _build_known_spellcast_mod_lines(self, raw_mods, item_attr_txt: str, item_type=None) -> list[str]:
        def _resolve_attribute_name(attr_id: int) -> str:
            try:
                from Py4GWCoreLib.enums import Attribute
                return self._format_attribute_name(getattr(Attribute(int(attr_id)), "name", ""))
            except EXPECTED_RUNTIME_ERRORS:
                return ""

        return build_known_spellcasting_mod_lines(
            raw_mods,
            item_attr_txt=str(item_attr_txt or ""),
            item_type=item_type,
            resolve_attribute_name_fn=_resolve_attribute_name,
            include_raw_when_no_chance=False,
            use_range_chance=True,
        )

    def _prune_generic_attribute_bonus_lines(self, lines: list[str]) -> list[str]:
        return prune_generic_attribute_bonus_lines(lines)

    def _normalize_stats_lines(self, lines: list[str]) -> list[str]:
        split_pattern = re.compile(
            r"(?i)(?<!^)(requires\s+\d+|damage:\s*\d|damage\s*\d|armor:\s*\d|armor\s*\d|energy\s*[+-]\d|halves\s|reduces\s|value:\s*\d|improved sale value)"
        )
        normalized = []
        for raw in list(lines or []):
            txt = str(raw or "").strip()
            if not txt:
                continue
            while True:
                match = split_pattern.search(txt)
                if not match:
                    break
                left = txt[:match.start()].strip()
                right = txt[match.start():].strip()
                if left:
                    normalized.append(left)
                txt = right
            if txt:
                normalized.append(txt)

        canonical = []
        seen = set()
        for raw in normalized:
            line = str(raw or "").strip()
            if not line:
                continue
            line = re.sub(r"(?i)^damage\s*(\d+\s*-\s*\d+)$", r"Damage: \1", line)
            line = re.sub(r"(?i)^armor\s*(\d+)(\b.*)$", r"Armor: \1\2", line)
            line = re.sub(r"(?i)^requires\s*(\d+)\s*", r"Requires \1 ", line)
            line = re.sub(r"\s+", " ", line).strip()
            key = re.sub(r"[^a-z0-9]+", "", line.lower())
            if not key or key in seen:
                continue
            seen.add(key)
            canonical.append(line)

        canonical = self._prune_generic_attribute_bonus_lines(canonical)
        canonical = sort_stats_lines_like_ingame(canonical)
        return canonical

    def _build_item_stats_text(self, item_id: int, item_name: str = "") -> str:
        item_id = int(item_id or 0)
        if item_id <= 0:
            return ""
        try:
            item_instance = Item.item_instance(item_id)
            if not item_instance:
                return ""
            model_id = int(getattr(item_instance, "model_id", 0))
            value = int(getattr(item_instance, "value", 0))
            lines: list[str] = []
            clean_name = str(item_name or "").strip()
            if clean_name:
                lines.append(clean_name)
            if value > 0:
                lines.append(f"Value: {value} gold")

            raw_mods = []
            try:
                for mod in Item.Customization.Modifiers.GetModifiers(item_id):
                    raw_mods.append((int(mod.GetIdentifier()), int(mod.GetArg1()), int(mod.GetArg2())))
            except EXPECTED_RUNTIME_ERRORS:
                raw_mods = []
            req_attr = 0
            req_val = 0
            if raw_mods:
                for ident, arg1, arg2 in raw_mods:
                    if ident in (42920, 42120):  # Damage, Damage_NoReq
                        if int(arg2) > 0 and int(arg1) > 0:
                            lines.append(f"Damage: {int(arg2)}-{int(arg1)}")
                    elif ident == 42936:  # ShieldArmor
                        if int(arg1) > 0:
                            if int(arg2) > 0:
                                lines.append(f"Armor: {int(arg1)} (vs {int(arg2)})")
                            else:
                                lines.append(f"Armor: {int(arg1)}")
                    elif ident == 10136:  # Requirement
                        req_attr = int(arg1)
                        req_val = int(arg2)
                if req_val > 0:
                    attr_txt = ""
                    try:
                        from Py4GWCoreLib.enums import Attribute
                        attr_txt = self._format_attribute_name(getattr(Attribute(req_attr), "name", ""))
                    except EXPECTED_RUNTIME_ERRORS:
                        attr_txt = ""
                    lines.append(f"Requires {req_val} {attr_txt}".rstrip())

            if not raw_mods or self.mod_db is None:
                return "\n".join(lines)

            try:
                item_type_int, _ = Item.GetItemType(item_id)
                item_type = ItemType(item_type_int) if ItemType is not None else None
            except EXPECTED_RUNTIME_ERRORS:
                item_type = None

            item_attr_txt_for_known = ""
            if req_val > 0:
                try:
                    from Py4GWCoreLib.enums import Attribute
                    item_attr_txt_for_known = self._format_attribute_name(getattr(Attribute(req_attr), "name", ""))
                except EXPECTED_RUNTIME_ERRORS:
                    item_attr_txt_for_known = ""

            if parse_modifiers is not None and item_type is not None:
                parsed = parse_modifiers(raw_mods, item_type, model_id, self.mod_db)
                item_attr_txt = self._format_attribute_name(getattr(parsed.attribute, "name", ""))
                if item_attr_txt:
                    item_attr_txt_for_known = item_attr_txt
                min_dmg, max_dmg = parsed.damage
                armor_val, armor_vs = parsed.shield_armor
                if int(min_dmg) > 0 and int(max_dmg) > 0:
                    lines.append(f"Damage: {int(min_dmg)}-{int(max_dmg)}")
                if int(armor_val) > 0:
                    if int(armor_vs) > 0:
                        lines.append(f"Armor: {int(armor_val)} (vs {int(armor_vs)})")
                    else:
                        lines.append(f"Armor: {int(armor_val)}")
                if int(parsed.requirements) > 0:
                    attr_txt = self._format_attribute_name(getattr(parsed.attribute, "name", ""))
                    if attr_txt:
                        lines.append(f"Requires {int(parsed.requirements)} {attr_txt}")
                    else:
                        lines.append(f"Requires {int(parsed.requirements)}")

                if parsed.weapon_mods:
                    for mod in parsed.weapon_mods:
                        name = str(getattr(mod.weapon_mod, "name", "") or "").strip()
                        value = int(getattr(mod, "value", 0))
                        if not name:
                            continue
                        matched_mods = list(getattr(mod, "matched_modifiers", []) or [])
                        desc = str(getattr(mod.weapon_mod, "description", "") or "").strip()
                        rendered_lines = self._render_mod_description_template(desc, matched_mods, value, item_attr_txt)
                        if rendered_lines:
                            lines.extend(rendered_lines)
                        else:
                            lines.append(f"{name} ({value})" if value else name)
                if parsed.runes:
                    for rune in parsed.runes:
                        name = str(getattr(rune.rune, "name", "") or "").strip()
                        desc = str(getattr(rune.rune, "description", "") or "").strip()
                        rune_mods = list(getattr(rune, "modifiers", []) or [])
                        rendered_lines = self._render_mod_description_template(desc, rune_mods, 0, item_attr_txt)
                        if name:
                            lines.append(name)
                        if rendered_lines:
                            lines.extend(rendered_lines)
                lines.extend(self._collect_fallback_mod_lines(raw_mods, item_attr_txt, item_type))
                lines.extend(self._collect_fallback_rune_lines(raw_mods, item_attr_txt))
            lines.extend(self._build_known_spellcast_mod_lines(raw_mods, item_attr_txt_for_known, item_type))

            lines = self._normalize_stats_lines(lines)
            return "\n".join(lines)
        except EXPECTED_RUNTIME_ERRORS:
            return ""

    def _entry_item_identity_matches(self, item_id: int, expected_model_id: int, expected_name_signature: str) -> bool:
        live_item_id = int(item_id or 0)
        if live_item_id <= 0:
            return False
        wanted_model_id = int(expected_model_id or 0)
        wanted_signature = str(expected_name_signature or "").strip().lower()
        unknown_item_sig = make_name_signature("Unknown Item")
        try:
            live_model_id = int(Item.GetModelID(live_item_id))
        except EXPECTED_RUNTIME_ERRORS:
            return False
        if wanted_model_id > 0 and live_model_id > 0 and live_model_id != wanted_model_id:
            return False
        if wanted_signature and wanted_signature != unknown_item_sig:
            try:
                if not Item.IsNameReady(live_item_id):
                    Item.RequestName(live_item_id)
                    return False
                live_name = Item.GetName(live_item_id) or ""
                live_name = re.sub(r"^[\d,]+\s+", "", self._strip_tags(str(live_name)).strip())
                if not live_name:
                    return False
                if make_name_signature(live_name) != wanted_signature:
                    return False
            except EXPECTED_RUNTIME_ERRORS:
                return False
        return True

    def _resolve_event_item_id_for_stats(self, entry: dict) -> int:
        if not isinstance(entry, dict):
            return 0
        expected_item_id = int(entry.get("item_id", 0))
        expected_model_id = int(entry.get("model_id", 0))
        expected_name_signature = str(entry.get("name_signature", "") or "").strip().lower()

        if self._entry_item_identity_matches(expected_item_id, expected_model_id, expected_name_signature):
            return expected_item_id

        try:
            bags = ItemArray.CreateBagList(1, 2, 3, 4)
            item_ids = list(ItemArray.GetItemArray(bags) or [])
        except EXPECTED_RUNTIME_ERRORS:
            return 0

        candidates: list[int] = []
        for inv_item_id in item_ids:
            inv_item_id = int(inv_item_id)
            if not self._entry_item_identity_matches(inv_item_id, expected_model_id, expected_name_signature):
                continue
            candidates.append(inv_item_id)
            if len(candidates) > 1:
                # Ambiguous matches are unsafe for stat attribution.
                return 0
        if len(candidates) == 1:
            return int(candidates[0])
        return 0

    def _reset_tracking_state(self, clear_outbox: bool = True):
        self.last_inventory_snapshot = {}
        self.pending_slot_deltas = {}
        if clear_outbox:
            self.outbox_queue = []
        self.last_sent_count = 0
        self.last_candidate_count = 0
        self.last_enqueued_count = 0
        self.is_warmed_up = False
        self.stable_snapshot_count = 0
        self.warmup_grace_until = 0.0
        self.last_process_duration_ms = 0.0
        self.last_ack_count = 0
        self.last_inventory_activity_ts = 0.0
        self.sent_event_stats_cache = {}

    def _strip_tags(self, text: str) -> str:
        return re.sub(r"<[^>]+>", "", text or "")

    def _prune_sent_event_stats_cache(self, now_ts: float | None = None):
        now = float(now_ts if now_ts is not None else time.time())
        ttl_s = max(30.0, float(getattr(self, "sent_event_stats_ttl_seconds", 600.0)))
        cache = getattr(self, "sent_event_stats_cache", {})
        if not isinstance(cache, dict) or not cache:
            return
        for event_id in list(cache.keys()):
            entry = cache.get(event_id)
            if not isinstance(entry, dict):
                cache.pop(event_id, None)
                continue
            created_at = float(entry.get("created_at", now))
            if (now - created_at) > ttl_s:
                cache.pop(event_id, None)

    def _remember_event_identity(
        self,
        event_id: str,
        item_id: int,
        model_id: int,
        item_name: str,
        name_signature: str = "",
    ):
        event_key = str(event_id or "").strip()
        if not event_key:
            return
        now_ts = time.time()
        self._prune_sent_event_stats_cache(now_ts)
        cache = getattr(self, "sent_event_stats_cache", None)
        if not isinstance(cache, dict):
            self.sent_event_stats_cache = {}
            cache = self.sent_event_stats_cache
        existing = cache.get(event_key, {})
        if not isinstance(existing, dict):
            existing = {}
        existing["item_id"] = int(item_id)
        existing["model_id"] = int(model_id)
        existing["item_name"] = str(item_name or "").strip()
        existing["name_signature"] = str(name_signature or "").strip().lower()
        existing["created_at"] = float(now_ts)
        # Preserve any already-built stats text.
        existing["stats_text"] = str(existing.get("stats_text", "") or "").strip()
        cache[event_key] = existing

    def get_cached_event_identity(self, event_id: str) -> dict:
        event_key = str(event_id or "").strip()
        if not event_key:
            return {}
        self._prune_sent_event_stats_cache()
        cache = getattr(self, "sent_event_stats_cache", {})
        if not isinstance(cache, dict):
            return {}
        entry = cache.get(event_key, None)
        if not isinstance(entry, dict):
            return {}
        return dict(entry)

    def resolve_live_item_id_for_event(self, event_id: str, preferred_item_id: int = 0) -> int:
        event_key = str(event_id or "").strip()
        preferred = int(preferred_item_id or 0)
        identity = self.get_cached_event_identity(event_key) if event_key else {}
        has_identity = bool(identity)
        if not has_identity:
            return max(0, preferred)
        probe_entry = {
            "item_id": max(0, preferred) if preferred > 0 else int(identity.get("item_id", 0)),
            "model_id": int(identity.get("model_id", 0)),
            "name_signature": str(identity.get("name_signature", "") or "").strip().lower(),
        }
        resolved = self._resolve_event_item_id_for_stats(probe_entry)
        if resolved > 0:
            return int(resolved)
        # Identity exists but cannot be matched unambiguously; avoid unsafe fallback.
        return 0

    def clear_cached_event_stats(self, event_id: str, item_id: int = 0):
        event_key = str(event_id or "").strip()
        if not event_key:
            return
        cache = getattr(self, "sent_event_stats_cache", {})
        if not isinstance(cache, dict):
            return
        entry = cache.get(event_key)
        if not isinstance(entry, dict):
            return
        wanted_item_id = int(item_id or 0)
        if wanted_item_id > 0 and int(entry.get("item_id", 0)) > 0 and int(entry.get("item_id", 0)) != wanted_item_id:
            return
        cache.pop(event_key, None)

    def clear_cached_event_stats_for_item(self, item_id: int = 0, model_id: int = 0):
        wanted_item_id = int(item_id or 0)
        wanted_model_id = int(model_id or 0)
        if wanted_item_id <= 0 and wanted_model_id <= 0:
            return
        cache = getattr(self, "sent_event_stats_cache", {})
        if not isinstance(cache, dict) or not cache:
            return
        to_remove: list[str] = []
        for event_key, entry in cache.items():
            if not isinstance(entry, dict):
                continue
            cached_item_id = int(entry.get("item_id", 0))
            cached_model_id = int(entry.get("model_id", 0))
            if wanted_item_id > 0 and cached_item_id > 0 and cached_item_id == wanted_item_id:
                to_remove.append(str(event_key))
                continue
            if wanted_model_id > 0 and cached_model_id > 0 and cached_model_id == wanted_model_id:
                to_remove.append(str(event_key))
        for event_key in to_remove:
            cache.pop(event_key, None)

    def _remember_event_stats_snapshot(
        self,
        event_id: str,
        item_id: int,
        model_id: int,
        item_name: str,
        stats_text: str,
        name_signature: str = "",
    ):
        event_key = str(event_id or "").strip()
        if not event_key:
            return
        stats_value = str(stats_text or "").strip()
        if not stats_value:
            return
        now_ts = time.time()
        self._prune_sent_event_stats_cache(now_ts)
        cache = getattr(self, "sent_event_stats_cache", None)
        if not isinstance(cache, dict):
            self.sent_event_stats_cache = {}
            cache = self.sent_event_stats_cache
        existing = cache.get(event_key, {})
        if not isinstance(existing, dict):
            existing = {}
        resolved_name_sig = str(name_signature or existing.get("name_signature", "") or "").strip().lower()
        cache[event_key] = {
            "item_id": int(item_id),
            "model_id": int(model_id),
            "item_name": str(item_name or "").strip(),
            "name_signature": resolved_name_sig,
            "stats_text": stats_value,
            "created_at": float(now_ts),
        }

    def get_cached_event_stats_text(self, event_id: str, item_id: int = 0, model_id: int = 0) -> str:
        event_key = str(event_id or "").strip()
        if not event_key:
            return ""
        self._prune_sent_event_stats_cache()
        cache = getattr(self, "sent_event_stats_cache", {})
        if not isinstance(cache, dict):
            return ""
        entry = cache.get(event_key, None)
        if not isinstance(entry, dict):
            return ""
        cached_item_id = int(entry.get("item_id", 0))
        cached_model_id = int(entry.get("model_id", 0))
        wanted_item_id = int(item_id or 0)
        wanted_model_id = int(model_id or 0)
        if wanted_item_id > 0 and cached_item_id > 0 and wanted_item_id != cached_item_id:
            return ""
        if wanted_model_id > 0 and cached_model_id > 0 and wanted_model_id != cached_model_id:
            return ""
        return str(entry.get("stats_text", "") or "").strip()

    def _make_orphan_pending_slot_key(self, item_id: int, now_ts: float) -> tuple[int, int]:
        if int(item_id) > 0:
            return 0, -abs(int(item_id))
        fallback_seed = int(now_ts * 1000.0) & 0x7FFFFFFF
        return 0, -max(1, fallback_seed)

    def _buffer_pending_slot_delta(
        self,
        slot_key: tuple[int, int],
        delta_qty: int,
        model_id: int,
        item_id: int,
        rarity: str,
        now_ts: float,
    ):
        qty_to_add = max(1, int(delta_qty))
        pending = self.pending_slot_deltas.get(slot_key)
        if pending is None or not isinstance(pending, dict):
            self.pending_slot_deltas[slot_key] = {
                "qty": int(qty_to_add),
                "model_id": int(model_id),
                "item_id": int(item_id),
                "rarity": rarity,
                "first_seen": now_ts,
                "last_seen": now_ts,
            }
            return

        pending_item_id = int(pending.get("item_id", 0))
        pending_model_id = int(pending.get("model_id", 0))
        same_item = pending_item_id > 0 and pending_item_id == int(item_id)
        same_model = pending_item_id <= 0 and pending_model_id > 0 and pending_model_id == int(model_id)
        if not (same_item or same_model):
            # Slot got reused by another unresolved item. Move previous pending to an
            # orphan key (by item_id) so we can still resolve it without mixing records.
            orphan_key = self._make_orphan_pending_slot_key(pending_item_id, now_ts)
            orphan_entry = self.pending_slot_deltas.get(orphan_key)
            if orphan_entry is None or not isinstance(orphan_entry, dict):
                preserved = dict(pending)
                preserved["last_seen"] = now_ts
                self.pending_slot_deltas[orphan_key] = preserved
            else:
                orphan_entry["qty"] = int(orphan_entry.get("qty", 0)) + int(pending.get("qty", 0))
                orphan_entry["model_id"] = int(pending.get("model_id", orphan_entry.get("model_id", 0)))
                orphan_entry["item_id"] = int(pending.get("item_id", orphan_entry.get("item_id", 0)))
                orphan_entry["rarity"] = orphan_entry.get("rarity") or pending.get("rarity") or rarity
                orphan_entry["first_seen"] = min(
                    float(orphan_entry.get("first_seen", now_ts)),
                    float(pending.get("first_seen", now_ts)),
                )
                orphan_entry["last_seen"] = now_ts
            self.pending_slot_deltas[slot_key] = {
                "qty": int(qty_to_add),
                "model_id": int(model_id),
                "item_id": int(item_id),
                "rarity": rarity,
                "first_seen": now_ts,
                "last_seen": now_ts,
            }
            return

        pending["qty"] = int(pending.get("qty", 0)) + int(qty_to_add)
        pending["model_id"] = int(model_id)
        pending["item_id"] = int(item_id)
        pending["rarity"] = pending.get("rarity") or rarity
        pending["last_seen"] = now_ts

    def _resolve_party_leader_email(self) -> str | None:
        try:
            helper_leader_email = CustomBehaviorHelperParty._get_party_leader_email()
            if helper_leader_email:
                return helper_leader_email

            leader_id = Party.GetPartyLeaderID()
            for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
                if int(account.AgentData.AgentID) == leader_id:
                    return account.AccountEmail

            # Fallback to leader slot in same party/map shard.
            my_party_id = GLOBAL_CACHE.Party.GetPartyID()
            for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
                if not account.IsAccount:
                    continue
                if int(account.AgentPartyData.PartyID) != int(my_party_id):
                    continue
                if int(account.AgentPartyData.PartyPosition) == 0:
                    return account.AccountEmail
        except EXPECTED_RUNTIME_ERRORS:
            return None
        return None

    def _is_party_leader_client(self) -> bool:
        try:
            is_leader = int(Player.GetAgentID()) == int(Party.GetPartyLeaderID())
            self.last_known_is_leader = bool(is_leader)
            return bool(is_leader)
        except EXPECTED_RUNTIME_ERRORS:
            # Preserve last known role to avoid transient misrouting.
            return bool(getattr(self, "last_known_is_leader", False))

    def _next_event_id(self) -> str:
        self.event_sequence = (int(self.event_sequence) + 1) & 0xFFFF
        return make_event_id(self.event_sequence)

    def _load_runtime_config(self):
        try:
            if not os.path.exists(self.runtime_config_path):
                return
            with open(self.runtime_config_path, mode="r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return
            self.debug_pipeline_logs = bool(data.get("debug_pipeline_logs", self.debug_pipeline_logs))
            self.enable_perf_logs = bool(data.get("enable_perf_logs", self.enable_perf_logs))
            self.enable_delivery_ack = bool(data.get("enable_delivery_ack", self.enable_delivery_ack))
            self.max_send_per_tick = max(1, int(data.get("max_send_per_tick", self.max_send_per_tick)))
            self.max_outbox_size = max(20, int(data.get("max_outbox_size", self.max_outbox_size)))
            self.retry_interval_seconds = max(0.2, float(data.get("retry_interval_seconds", self.retry_interval_seconds)))
            self.max_retry_attempts = max(1, int(data.get("max_retry_attempts", self.max_retry_attempts)))
            self.max_stats_builds_per_tick = max(
                0, int(data.get("max_stats_builds_per_tick", self.max_stats_builds_per_tick))
            )
        except EXPECTED_RUNTIME_ERRORS:
            return

    def _send_name_chunks(self, receiver_email: str, my_email: str, name_signature: str, full_name: str) -> bool:
        try:
            if not name_signature:
                return True
            chunks = build_name_chunks(full_name or "")
            for idx, total, chunk in chunks:
                sent_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email=my_email,
                    receiver_email=receiver_email,
                    command=SharedCommandType.CustomBehaviors,
                    params=(0.0, 0.0, 0.0, 0.0),
                    ExtraData=(
                        "TrackerNameV2",
                        (name_signature or "")[:31],
                        (chunk or "")[:31],
                        encode_name_chunk_meta(idx, total)[:31],
                    ),
                )
                if sent_index == -1:
                    return False
            return True
        except EXPECTED_RUNTIME_ERRORS:
            return False

    def _send_stats_chunks(self, receiver_email: str, my_email: str, event_id: str, stats_text: str) -> bool:
        try:
            if not event_id:
                return True
            if not stats_text:
                return True
            chunks = build_name_chunks(stats_text or "", 31)
            for idx, total, chunk in chunks:
                sent_index = GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email=my_email,
                    receiver_email=receiver_email,
                    command=SharedCommandType.CustomBehaviors,
                    params=(0.0, 0.0, 0.0, 0.0),
                    ExtraData=(
                        "TrackerStatsV1",
                        (event_id or "")[:31],
                        (chunk or "")[:31],
                        encode_name_chunk_meta(idx, total)[:31],
                    ),
                )
                if sent_index == -1:
                    return False
            return True
        except EXPECTED_RUNTIME_ERRORS:
            return False

    def _send_drop(
        self,
        item_name: str,
        quantity: int,
        rarity: str,
        display_time: str = "",
        item_id: int = 0,
        model_id: int = 0,
        slot_bag: int = 0,
        slot_index: int = 0,
        is_leader_sender: bool = False,
        event_id: str = "",
        name_signature: str = "",
    ) -> bool:
        try:
            my_email = Player.GetAccountEmail()
            if not my_email:
                return False
            if is_leader_sender:
                receiver_email = my_email
            else:
                receiver_email = self._resolve_party_leader_email()
                # Followers must never fallback to self; retry once leader email is known.
                if not receiver_email or receiver_email == my_email:
                    return False
            meta = build_drop_meta(event_id, name_signature, display_time)
            sent_index = GLOBAL_CACHE.ShMem.SendMessage(
                sender_email=my_email,
                receiver_email=receiver_email,
                command=SharedCommandType.CustomBehaviors,
                params=(
                    float(max(1, quantity)),
                    float(max(0, int(item_id))),
                    float(max(0, int(model_id))),
                    float((int(slot_bag) << 16) | int(slot_index)),
                ),
                ExtraData=(
                    "TrackerDrop",
                    (item_name or "Unknown Item")[:31],
                    (rarity or "Unknown")[:31],
                    (meta or "")[:31],
                ),
            )
            if sent_index == -1 and self.warn_timer.IsExpired():
                self.warn_timer.Reset()
                Py4GW.Console.Log(
                    "DropTrackerSender",
                    f"SendMessage failed (inbox full?): sender={my_email}, receiver={receiver_email}, item={item_name}",
                    Py4GW.Console.MessageType.Warning,
                )
            if sent_index != -1 and self.debug_pipeline_logs:
                Py4GW.Console.Log(
                    "DropTrackerSender",
                    (
                        f"SENT idx={sent_index} role={'leader' if is_leader_sender else 'follower'} "
                        f"item='{item_name}' qty={max(1, int(quantity))} rarity={rarity} "
                        f"item_id={int(item_id)} model_id={int(model_id)} slot={int(slot_bag)}:{int(slot_index)} "
                        f"event_id={event_id}"
                    ),
                    Py4GW.Console.MessageType.Info,
                )
            return sent_index != -1
        except EXPECTED_RUNTIME_ERRORS:
            return False

    def _queue_drop(
        self,
        item_name: str,
        quantity: int,
        rarity: str,
        display_time: str,
        item_id: int = 0,
        model_id: int = 0,
        slot_key: tuple[int, int] | None = None,
        reason: str = "delta",
        is_leader_sender: bool = False,
    ):
        bag_id = int(slot_key[0]) if slot_key else 0
        slot_id = int(slot_key[1]) if slot_key else 0
        entry = {
            "item_name": item_name or "Unknown Item",
            "full_name": item_name or "Unknown Item",
            "quantity": max(1, int(quantity)),
            "rarity": rarity or "Unknown",
            "display_time": display_time or "",
            "item_id": int(item_id),
            "model_id": int(model_id),
            "bag_id": bag_id,
            "slot_id": slot_id,
            "reason": reason or "delta",
            "is_leader_sender": bool(is_leader_sender),
            "event_id": self._next_event_id(),
            "name_signature": make_name_signature(item_name or "Unknown Item"),
            "name_chunks_sent": False,
            "stats_chunks_sent": False,
            # Build stats lazily in _flush_outbox; eager builds can stall on burst pickups.
            "stats_text": "",
            "attempts": 0,
            "next_retry_at": 0.0,
            "acked": False,
            "last_receiver_email": "",
        }
        self._remember_event_identity(
            event_id=str(entry.get("event_id", "")),
            item_id=int(entry.get("item_id", 0)),
            model_id=int(entry.get("model_id", 0)),
            item_name=str(entry.get("item_name", "") or ""),
            name_signature=str(entry.get("name_signature", "") or ""),
        )
        if len(self.outbox_queue) >= int(self.max_outbox_size):
            self.outbox_queue.pop(0)
            if self.warn_timer.IsExpired():
                self.warn_timer.Reset()
                Py4GW.Console.Log(
                    "DropTrackerSender",
                    f"Outbox full, dropped oldest entry (limit={self.max_outbox_size}).",
                    Py4GW.Console.MessageType.Warning,
                )
        self.outbox_queue.append(entry)
        if self.debug_pipeline_logs:
            Py4GW.Console.Log(
                "DropTrackerSender",
                (
                    f"ENQUEUE reason={entry['reason']} role={'leader' if entry['is_leader_sender'] else 'follower'} "
                    f"item='{entry['item_name']}' qty={entry['quantity']} rarity={entry['rarity']} "
                    f"item_id={entry['item_id']} model_id={entry['model_id']} "
                    f"slot={entry['bag_id']}:{entry['slot_id']} queue={len(self.outbox_queue)} "
                    f"event_id={entry['event_id']}"
                ),
                Py4GW.Console.MessageType.Info,
            )

    def _poll_ack_messages(self) -> int:
        if not self.enable_delivery_ack:
            return 0
        try:
            my_email = Player.GetAccountEmail()
            if not my_email:
                return 0
            shmem = getattr(GLOBAL_CACHE, "ShMem", None)
            if shmem is None:
                return 0
            acked_count = 0
            for msg_idx, shared_msg in shmem.GetAllMessages():
                receiver_email = str(getattr(shared_msg, "ReceiverEmail", "") or "").strip()
                if receiver_email != my_email:
                    continue
                command_value = int(getattr(shared_msg, "Command", 0))
                expected_custom_behavior_command = 997
                try:
                    expected_custom_behavior_command = int(SharedCommandType.CustomBehaviors.value)
                except EXPECTED_RUNTIME_ERRORS:
                    pass
                if command_value != expected_custom_behavior_command and command_value != 997:
                    continue
                extra_data_list = getattr(shared_msg, "ExtraData", None)
                if not extra_data_list or len(extra_data_list) == 0:
                    continue
                extra_0 = "".join(ch for ch in extra_data_list[0] if ch != "\0").rstrip()
                if extra_0 != "TrackerAckV2":
                    continue
                event_id = "".join(ch for ch in extra_data_list[1] if ch != "\0").rstrip() if len(extra_data_list) > 1 else ""
                ack_sender_email = str(getattr(shared_msg, "SenderEmail", "") or "").strip().lower()
                for entry in self.outbox_queue:
                    if str(entry.get("event_id", "")) == str(event_id):
                        if int(entry.get("attempts", 0)) <= 0:
                            continue
                        expected_sender = str(entry.get("last_receiver_email", "") or "").strip().lower()
                        if expected_sender and ack_sender_email and ack_sender_email != expected_sender:
                            continue
                        if not entry.get("acked", False):
                            entry["acked"] = True
                            acked_count += 1
                shmem.MarkMessageAsFinished(my_email, msg_idx)
            self.last_ack_count = acked_count
            return acked_count
        except EXPECTED_RUNTIME_ERRORS:
            return 0

    def _flush_outbox(self) -> int:
        if self.enable_delivery_ack and self.ack_poll_timer.IsExpired():
            self.ack_poll_timer.Reset()
            self._poll_ack_messages()

        now_ts = time.time()
        stats_build_budget = max(0, int(getattr(self, "max_stats_builds_per_tick", 2)))
        kept_entries = []
        for entry in self.outbox_queue:
            if entry.get("acked", False):
                continue
            attempts = int(entry.get("attempts", 0))
            if attempts >= int(self.max_retry_attempts):
                if self.warn_timer.IsExpired():
                    self.warn_timer.Reset()
                    Py4GW.Console.Log(
                        "DropTrackerSender",
                        f"Dropping unacked event after retries: {entry.get('event_id', '')}",
                        Py4GW.Console.MessageType.Warning,
                    )
                continue
            kept_entries.append(entry)
        self.outbox_queue = kept_entries

        sent = 0
        attempted = 0
        retry_delay_s = max(0.2, float(self.retry_interval_seconds))
        for entry in self.outbox_queue:
            if attempted >= int(self.max_send_per_tick):
                break
            if float(entry.get("next_retry_at", 0.0)) > now_ts:
                continue

            my_email = Player.GetAccountEmail()
            if not my_email:
                break
            is_leader_sender = bool(entry.get("is_leader_sender", False))
            receiver_email = my_email if is_leader_sender else self._resolve_party_leader_email()
            if not receiver_email:
                continue
            if not is_leader_sender and receiver_email == my_email:
                continue

            attempted += 1
            entry["last_receiver_email"] = str(receiver_email or "").strip().lower()
            send_failed = False

            if not entry.get("name_chunks_sent", False):
                full_name = str(entry.get("full_name", "") or "")
                short_name = str(entry.get("item_name", "") or "")
                if len(full_name) > 31 or full_name != short_name:
                    ok_chunks = self._send_name_chunks(
                        receiver_email=receiver_email,
                        my_email=my_email,
                        name_signature=str(entry.get("name_signature", "")),
                        full_name=full_name,
                    )
                    if not ok_chunks:
                        send_failed = True
                entry["name_chunks_sent"] = True

            if (not send_failed) and (not entry.get("stats_chunks_sent", False)):
                stats_text = str(entry.get("stats_text", "") or "")
                if not stats_text and stats_build_budget > 0:
                    stats_item_id = self._resolve_event_item_id_for_stats(entry)
                    built_text = ""
                    if stats_item_id > 0:
                        entry["item_id"] = int(stats_item_id)
                        built_text = self._build_item_stats_text(
                            int(stats_item_id),
                            str(entry.get("item_name", "Unknown Item") or "Unknown Item"),
                        )
                    entry["stats_text"] = str(built_text or "")
                    stats_text = str(entry.get("stats_text", "") or "")
                    stats_build_budget -= 1
                    if stats_text:
                        self._remember_event_stats_snapshot(
                            event_id=str(entry.get("event_id", "")),
                            item_id=int(entry.get("item_id", 0)),
                            model_id=int(entry.get("model_id", 0)),
                            item_name=str(entry.get("item_name", "") or ""),
                            stats_text=stats_text,
                            name_signature=str(entry.get("name_signature", "") or ""),
                        )
                ok_stats = self._send_stats_chunks(
                    receiver_email=receiver_email,
                    my_email=my_email,
                    event_id=str(entry.get("event_id", "")),
                    stats_text=stats_text,
                )
                # Stats are best-effort; never block the drop event itself.
                if ok_stats:
                    entry["stats_chunks_sent"] = True

            if not send_failed:
                if not self._send_drop(
                    entry.get("item_name", "Unknown Item"),
                    int(entry.get("quantity", 1)),
                    str(entry.get("rarity", "Unknown")),
                    str(entry.get("display_time", "")),
                    int(entry.get("item_id", 0)),
                    int(entry.get("model_id", 0)),
                    int(entry.get("bag_id", 0)),
                    int(entry.get("slot_id", 0)),
                    is_leader_sender,
                    str(entry.get("event_id", "")),
                    str(entry.get("name_signature", "")),
                ):
                    send_failed = True

            entry["attempts"] = int(entry.get("attempts", 0)) + 1
            if send_failed:
                # Count failed delivery attempts so stale head-of-queue entries can expire.
                entry["next_retry_at"] = now_ts + retry_delay_s
                continue
            if self.enable_delivery_ack:
                entry["next_retry_at"] = now_ts + retry_delay_s
            else:
                entry["acked"] = True
            sent += 1

        if not self.enable_delivery_ack:
            self.outbox_queue = [entry for entry in self.outbox_queue if not entry.get("acked", False)]
        return sent

    def _take_inventory_snapshot(self) -> dict[tuple[int, int], tuple[str, str, int, int, int]]:
        # key: (bag_id, slot_id)
        # value: (name, rarity, qty, model_id, item_id)
        snapshot: dict[tuple[int, int], tuple[str, str, int, int, int]] = {}
        try:
            # Player inventory only (avoid storage/material tabs).
            bag_ids = (1, 2, 3, 4)
            bags = ItemArray.CreateBagList(*bag_ids)
            item_ids = ItemArray.GetItemArray(bags)
            self.last_snapshot_total = len(item_ids)
            ready_count = 0
            not_ready_count = 0
            for bag_id in bag_ids:
                bag_items = ItemArray.GetItemArray(ItemArray.CreateBagList(bag_id))
                for item_id in bag_items:
                    item_instance = Item.item_instance(item_id)
                    if item_instance:
                        slot_id = int(item_instance.slot)
                        model_id = int(item_instance.model_id)
                        rarity = item_instance.rarity.name if getattr(item_instance, "rarity", None) else "Unknown"
                        qty = int(item_instance.quantity) if getattr(item_instance, "quantity", None) is not None else 1
                    else:
                        slot_id = int(Item.GetSlot(item_id))
                        model_id = int(Item.GetModelID(item_id))
                        rarity = Item.Rarity.GetRarity(item_id)[1]
                        qty = Item.Properties.GetQuantity(item_id)
                        qty = max(1, int(qty) if qty is not None else 1)

                    is_name_ready = Item.IsNameReady(item_id)
                    raw_name = ""
                    if is_name_ready:
                        raw_name = Item.GetName(item_id) or ""
                        ready_count += 1
                    else:
                        not_ready_count += 1
                        try:
                            Item.RequestName(item_id)
                        except EXPECTED_RUNTIME_ERRORS:
                            pass

                    clean_name = self._strip_tags(raw_name).strip() if raw_name else ""
                    clean_name = re.sub(r"^[\d,]+\s+", "", clean_name) if clean_name else ""
                    if not clean_name:
                        # Keep deterministic placeholder; never emit this as a drop.
                        clean_name = f"Model#{model_id}"

                    if Item.Type.IsTome(item_id):
                        rarity = "Tomes"
                    elif "Dye" in clean_name or "Vial of Dye" in clean_name:
                        rarity = "Dyes"
                    elif "Key" in clean_name:
                        rarity = "Keys"
                    elif Item.Type.IsMaterial(item_id) or Item.Type.IsRareMaterial(item_id):
                        rarity = "Material"
                    slot_key = (bag_id, int(slot_id))
                    existing_entry = snapshot.get(slot_key)
                    if (
                        existing_entry is not None
                        and isinstance(existing_entry, tuple)
                        and len(existing_entry) > 4
                        and int(existing_entry[4]) != int(item_id)
                    ):
                        # Transient slot collisions can happen while inventory is mutating.
                        # Keep both items by switching to a deterministic synthetic key.
                        synthetic_slot_id = -max(1, abs(int(item_id)))
                        slot_key = (bag_id, synthetic_slot_id)
                        while slot_key in snapshot:
                            synthetic_slot_id -= 1
                            slot_key = (bag_id, synthetic_slot_id)
                    snapshot[slot_key] = (clean_name, rarity, qty, model_id, int(item_id))

            self.last_snapshot_ready = ready_count
            self.last_snapshot_not_ready = not_ready_count
        except EXPECTED_RUNTIME_ERRORS:
            if self.snapshot_error_timer.IsExpired():
                self.snapshot_error_timer.Reset()
                Py4GW.Console.Log(
                    "DropTrackerSender",
                    "Inventory snapshot failed.",
                    Py4GW.Console.MessageType.Warning,
                )
            return snapshot
        return snapshot

    def _process_inventory_deltas(self):
        start_perf = time.perf_counter()
        current_snapshot = self._take_inventory_snapshot()

        # Guard against transient invalid snapshots (observed: ready=0/not_ready=N spikes).
        if self.last_snapshot_total > 0 and self.last_snapshot_ready == 0:
            self.last_sent_count = 0
            self.last_process_duration_ms = (time.perf_counter() - start_perf) * 1000.0
            return

        if not current_snapshot:
            self.last_sent_count = 0
            self.last_process_duration_ms = (time.perf_counter() - start_perf) * 1000.0
            return

        # Warm-up baseline to avoid counting existing inventory as drops.
        readiness = (float(self.last_snapshot_ready) / float(self.last_snapshot_total)) if self.last_snapshot_total else 0.0
        if not self.is_warmed_up:
            if readiness >= 0.7:
                self.stable_snapshot_count += 1
            else:
                self.stable_snapshot_count = 0
            self.last_inventory_snapshot = current_snapshot
            self.last_sent_count = 0
            if self.stable_snapshot_count >= 2:
                self.is_warmed_up = True
                self.warmup_grace_until = time.time() + self.warmup_grace_seconds
            self.last_process_duration_ms = (time.perf_counter() - start_perf) * 1000.0
            return

        # Extra grace after warm-up to ignore late startup snapshot churn.
        if time.time() < self.warmup_grace_until:
            self.last_inventory_snapshot = current_snapshot
            self.last_sent_count = 0
            self.last_process_duration_ms = (time.perf_counter() - start_perf) * 1000.0
            return

        # Guard against mass-delta churn due slot/index instability or inventory refresh.
        if abs(len(current_snapshot) - len(self.last_inventory_snapshot)) > 12:
            # Resync snapshot without clearing outbox/warmup to avoid losing captured events.
            self.pending_slot_deltas = {}
            self.last_inventory_snapshot = current_snapshot
            self.last_sent_count = 0
            self.last_process_duration_ms = (time.perf_counter() - start_perf) * 1000.0
            return

        time_str = datetime.datetime.now().strftime("%I:%M %p")
        candidate_events: list[dict] = []
        prev_model_qty: dict[int, int] = {}
        current_model_qty: dict[int, int] = {}
        for snapshot_entry in self.last_inventory_snapshot.values():
            if not isinstance(snapshot_entry, tuple) or len(snapshot_entry) < 4:
                continue
            prev_model_id = int(snapshot_entry[3])
            prev_qty = max(1, int(snapshot_entry[2])) if len(snapshot_entry) > 2 else 1
            prev_model_qty[prev_model_id] = int(prev_model_qty.get(prev_model_id, 0)) + int(prev_qty)
        for snapshot_entry in current_snapshot.values():
            if not isinstance(snapshot_entry, tuple) or len(snapshot_entry) < 4:
                continue
            curr_model_id = int(snapshot_entry[3])
            curr_qty = max(1, int(snapshot_entry[2])) if len(snapshot_entry) > 2 else 1
            current_model_qty[curr_model_id] = int(current_model_qty.get(curr_model_id, 0)) + int(curr_qty)
        prev_item_ids = {int(v[4]) for v in self.last_inventory_snapshot.values() if isinstance(v, tuple) and len(v) > 4}
        prev_item_state_by_id: dict[int, tuple[int, int]] = {
            int(v[4]): (int(v[3]), int(v[2]))
            for v in self.last_inventory_snapshot.values()
            if isinstance(v, tuple) and len(v) > 4
        }
        # Only names from slots that changed this tick are safe for pending-name resolution.
        changed_itemid_to_ready_name: dict[int, tuple[str, str]] = {}
        changed_model_rarity_to_ready_name: dict[tuple[int, str], str] = {}
        live_slots = set()
        live_item_ids = set()
        live_item_model_by_id: dict[int, int] = {}
        for slot_key, (name, rarity, qty, _model_id, _item_id) in current_snapshot.items():
            live_slots.add(slot_key)
            live_item_ids.add(int(_item_id))
            live_item_model_by_id[int(_item_id)] = int(_model_id)
            previous = self.last_inventory_snapshot.get(slot_key)
            is_unknown_name = name.startswith("Model#")
            changed_this_tick = False
            if previous is None:
                # Item moved between slots: do not treat as pickup.
                if int(_item_id) in prev_item_ids:
                    prev_state = prev_item_state_by_id.get(int(_item_id))
                    if prev_state is not None:
                        prev_model_for_item, prev_qty_for_item = prev_state
                        if int(prev_model_for_item) == int(_model_id) and int(prev_qty_for_item) == int(qty):
                            continue
                changed_this_tick = True
                if is_unknown_name:
                    now_ts = time.time()
                    self._buffer_pending_slot_delta(
                        slot_key=slot_key,
                        delta_qty=int(qty),
                        model_id=int(_model_id),
                        item_id=int(_item_id),
                        rarity=str(rarity or "Unknown"),
                        now_ts=now_ts,
                    )
                else:
                    candidate_events.append({
                        "name": name,
                        "qty": int(qty),
                        "rarity": rarity,
                        "item_id": int(_item_id),
                        "model_id": int(_model_id),
                        "slot_key": slot_key,
                        "reason": "new_slot",
                    })
                    changed_itemid_to_ready_name[int(_item_id)] = (name, str(rarity or "Unknown"))
                    changed_model_rarity_to_ready_name[(int(_model_id), str(rarity or "Unknown"))] = name
                continue
            prev_qty = int(previous[2])
            prev_model_id = int(previous[3])
            prev_item_id = int(previous[4])

            # Slot got replaced (common during fast pickups/sorting): treat as new item in this slot.
            if int(_item_id) != prev_item_id:
                # Replacement can be pure slot rearrangement; count only truly new item IDs.
                if int(_item_id) in prev_item_ids:
                    prev_state = prev_item_state_by_id.get(int(_item_id))
                    if prev_state is not None:
                        prev_model_for_item, prev_qty_for_item = prev_state
                        if int(prev_model_for_item) == int(_model_id) and int(prev_qty_for_item) == int(qty):
                            continue
                changed_this_tick = True
                if is_unknown_name:
                    now_ts = time.time()
                    self._buffer_pending_slot_delta(
                        slot_key=slot_key,
                        delta_qty=int(qty),
                        model_id=int(_model_id),
                        item_id=int(_item_id),
                        rarity=str(rarity or "Unknown"),
                        now_ts=now_ts,
                    )
                else:
                    candidate_events.append({
                        "name": name,
                        "qty": int(qty),
                        "rarity": rarity,
                        "item_id": int(_item_id),
                        "model_id": int(_model_id),
                        "slot_key": slot_key,
                        "reason": "slot_replaced",
                    })
                    changed_itemid_to_ready_name[int(_item_id)] = (name, str(rarity or "Unknown"))
                    changed_model_rarity_to_ready_name[(int(_model_id), str(rarity or "Unknown"))] = name
            elif qty > prev_qty:
                changed_this_tick = True
                delta = qty - prev_qty
                if is_unknown_name:
                    now_ts = time.time()
                    self._buffer_pending_slot_delta(
                        slot_key=slot_key,
                        delta_qty=int(delta),
                        model_id=int(_model_id),
                        item_id=int(_item_id),
                        rarity=str(rarity or "Unknown"),
                        now_ts=now_ts,
                    )
                else:
                    candidate_events.append({
                        "name": name,
                        "qty": int(delta),
                        "rarity": rarity,
                        "item_id": int(_item_id),
                        "model_id": int(_model_id),
                        "slot_key": slot_key,
                        "reason": "stack_increase",
                    })
                    changed_itemid_to_ready_name[int(_item_id)] = (name, str(rarity or "Unknown"))
                    changed_model_rarity_to_ready_name[(int(_model_id), str(rarity or "Unknown"))] = name

            # If an item name became ready after we buffered its delta, flush now.
            if not is_unknown_name and slot_key in self.pending_slot_deltas:
                pending_entry = self.pending_slot_deltas.get(slot_key)
                pending_qty = int(pending_entry.get("qty", 0)) if isinstance(pending_entry, dict) else 0
                pending_item_id = int(pending_entry.get("item_id", 0)) if isinstance(pending_entry, dict) else 0
                if pending_qty > 0 and pending_item_id == int(_item_id):
                    # Use current resolved rarity, not stale buffered rarity.
                    candidate_events.append({
                        "name": name,
                        "qty": int(pending_qty),
                        "rarity": rarity,
                        "item_id": int(_item_id),
                        "model_id": int(_model_id),
                        "slot_key": slot_key,
                        "reason": "pending_same_slot_name_ready",
                    })
                    self.pending_slot_deltas.pop(slot_key, None)
                    changed_this_tick = True
                elif pending_item_id != int(_item_id):
                    # Slot was reused by another item; keep old pending entry for TTL/model resolution.
                    pass

            if changed_this_tick and not is_unknown_name:
                changed_itemid_to_ready_name[int(_item_id)] = (name, str(rarity or "Unknown"))
                changed_model_rarity_to_ready_name[(int(_model_id), str(rarity or "Unknown"))] = name

        # Resolve pending unknowns by changed-slot lookups only (safer than whole-inventory matching).
        now_ts = time.time()
        resolved_pending_slots = []
        for pending_slot, pending_entry in self.pending_slot_deltas.items():
            if not isinstance(pending_entry, dict):
                continue
            pending_qty = int(pending_entry.get("qty", 0))
            if pending_qty <= 0:
                resolved_pending_slots.append(pending_slot)
                continue
            pending_model_id = int(pending_entry.get("model_id", 0))
            pending_item_id = int(pending_entry.get("item_id", 0))
            live_model_for_pending = int(live_item_model_by_id.get(pending_item_id, 0))
            pending_item_is_live = pending_item_id in live_item_ids and (
                pending_model_id <= 0 or live_model_for_pending <= 0 or live_model_for_pending == pending_model_id
            )
            pending_rarity = str(pending_entry.get("rarity") or "Unknown")

            # Best match: exact item identity.
            if pending_item_id > 0 and pending_item_is_live:
                try:
                    # Direct resolve from live item_id first (most accurate).
                    if Item.IsNameReady(pending_item_id):
                        raw_name = Item.GetName(pending_item_id) or ""
                        resolved_name = re.sub(r"^[\d,]+\s+", "", self._strip_tags(raw_name).strip())
                        if resolved_name:
                            resolved_rarity = pending_rarity
                            if resolved_rarity == "Unknown":
                                try:
                                    item_instance = Item.item_instance(pending_item_id)
                                    if item_instance and getattr(item_instance, "rarity", None):
                                        resolved_rarity = item_instance.rarity.name
                                except EXPECTED_RUNTIME_ERRORS:
                                    pass
                            if Item.Type.IsTome(pending_item_id):
                                resolved_rarity = "Tomes"
                            elif "Dye" in resolved_name or "Vial of Dye" in resolved_name:
                                resolved_rarity = "Dyes"
                            elif "Key" in resolved_name:
                                resolved_rarity = "Keys"
                            elif Item.Type.IsMaterial(pending_item_id) or Item.Type.IsRareMaterial(pending_item_id):
                                resolved_rarity = "Material"
                            candidate_events.append({
                                "name": resolved_name,
                                "qty": int(pending_qty),
                                "rarity": resolved_rarity,
                                "item_id": int(pending_item_id),
                                "model_id": int(pending_model_id),
                                "slot_key": pending_slot,
                                "reason": "pending_itemid_name_ready",
                            })
                            resolved_pending_slots.append(pending_slot)
                            continue
                    else:
                        Item.RequestName(pending_item_id)
                except EXPECTED_RUNTIME_ERRORS:
                    pass

                by_item_id = changed_itemid_to_ready_name.get(pending_item_id)
                if by_item_id:
                    resolved_name, resolved_rarity = by_item_id
                    final_rarity = pending_rarity if pending_rarity != "Unknown" else resolved_rarity
                    candidate_events.append({
                        "name": resolved_name,
                        "qty": int(pending_qty),
                        "rarity": final_rarity,
                        "item_id": int(pending_item_id),
                        "model_id": int(pending_model_id),
                        "slot_key": pending_slot,
                        "reason": "pending_changed_slot_lookup",
                    })
                    resolved_pending_slots.append(pending_slot)
                    continue

            # Prefer exact (model, rarity) match.
            exact_name = changed_model_rarity_to_ready_name.get((pending_model_id, pending_rarity))
            if exact_name:
                candidate_events.append({
                    "name": exact_name,
                    "qty": int(pending_qty),
                    "rarity": pending_rarity,
                    "item_id": int(pending_item_id),
                    "model_id": int(pending_model_id),
                    "slot_key": pending_slot,
                    "reason": "pending_model_rarity_lookup",
                })
                resolved_pending_slots.append(pending_slot)
                continue

            first_seen = float(pending_entry.get("first_seen", now_ts))
            if (now_ts - first_seen) >= self.pending_ttl_seconds:
                fallback_name = f"Item#{pending_model_id}" if pending_model_id > 0 else "Unknown Item"
                fallback_rarity = pending_entry.get("rarity") or "Unknown"
                candidate_events.append({
                    "name": fallback_name,
                    "qty": int(pending_qty),
                    "rarity": fallback_rarity,
                    "item_id": int(pending_item_id),
                    "model_id": int(pending_model_id),
                    "slot_key": pending_slot,
                    "reason": "pending_ttl_fallback",
                })
                resolved_pending_slots.append(pending_slot)

        for pending_slot in resolved_pending_slots:
            self.pending_slot_deltas.pop(pending_slot, None)

        # Drop stale pending slots (item moved/consumed before name became ready).
        stale_slots = [slot_key for slot_key in self.pending_slot_deltas.keys() if slot_key not in live_slots]
        for slot_key in stale_slots:
            entry = self.pending_slot_deltas.get(slot_key)
            if not isinstance(entry, dict):
                self.pending_slot_deltas.pop(slot_key, None)
                continue
            pending_item_id = int(entry.get("item_id", 0))
            pending_model_id = int(entry.get("model_id", 0))
            live_model_for_pending = int(live_item_model_by_id.get(pending_item_id, 0))
            pending_item_still_live = pending_item_id > 0 and pending_item_id in live_item_ids and (
                pending_model_id <= 0 or live_model_for_pending <= 0 or live_model_for_pending == pending_model_id
            )
            if pending_item_still_live:
                continue
            last_seen = float(entry.get("last_seen", now_ts))
            if (now_ts - last_seen) > self.pending_ttl_seconds:
                qty = int(entry.get("qty", 0))
                if qty > 0:
                    model_id = int(entry.get("model_id", 0))
                    rarity = entry.get("rarity") or "Unknown"
                    fallback_name = f"Item#{model_id}" if model_id > 0 else "Unknown Item"
                    candidate_events.append({
                        "name": fallback_name,
                        "qty": int(qty),
                        "rarity": rarity,
                        "item_id": int(entry.get("item_id", 0)),
                        "model_id": int(model_id),
                        "slot_key": slot_key,
                        "reason": "stale_slot_ttl_fallback",
                    })
                self.pending_slot_deltas.pop(slot_key, None)

        if candidate_events or self.pending_slot_deltas:
            self.last_inventory_activity_ts = time.time()

        # Suppress false positives caused by transient item-id churn/reordering.
        # Keep truly new item identities to avoid missing real pickups that are
        # picked/consumed between snapshots.
        candidate_events, suppressed_by_model_delta = filter_candidate_events_by_model_delta(
            candidate_events=candidate_events,
            prev_model_qty=prev_model_qty,
            current_model_qty=current_model_qty,
            prev_item_ids=prev_item_ids,
        )

        if self.debug_pipeline_logs and suppressed_by_model_delta > 0:
            Py4GW.Console.Log(
                "DropTrackerSender",
                f"SUPPRESSED by model-delta filter: {suppressed_by_model_delta}",
                Py4GW.Console.MessageType.Info,
            )

        if self.debug_pipeline_logs and candidate_events:
            for event in candidate_events[:20]:
                slot_key = event.get("slot_key")
                bag_id = int(slot_key[0]) if isinstance(slot_key, tuple) and len(slot_key) > 0 else 0
                slot_id = int(slot_key[1]) if isinstance(slot_key, tuple) and len(slot_key) > 1 else 0
                Py4GW.Console.Log(
                    "DropTrackerSender",
                    (
                        f"CANDIDATE reason={event.get('reason', 'delta')} "
                        f"item='{event.get('name', 'Unknown Item')}' qty={int(event.get('qty', 1))} "
                        f"rarity={event.get('rarity', 'Unknown')} "
                        f"item_id={int(event.get('item_id', 0))} model_id={int(event.get('model_id', 0))} "
                        f"slot={bag_id}:{slot_id}"
                    ),
                    Py4GW.Console.MessageType.Info,
                )
            if len(candidate_events) > 20:
                Py4GW.Console.Log(
                    "DropTrackerSender",
                    f"CANDIDATE truncated: showing 20/{len(candidate_events)}",
                    Py4GW.Console.MessageType.Info,
                )

        is_leader_sender = self._is_party_leader_client()
        enqueued_count = 0
        for event in candidate_events:
            self._queue_drop(
                str(event.get("name", "Unknown Item")),
                int(event.get("qty", 1)),
                str(event.get("rarity", "Unknown")),
                time_str,
                int(event.get("item_id", 0)),
                int(event.get("model_id", 0)),
                event.get("slot_key"),
                str(event.get("reason", "delta")),
                is_leader_sender=is_leader_sender,
            )
            enqueued_count += 1

        sent_count = self._flush_outbox()
        self.last_candidate_count = len(candidate_events)
        self.last_enqueued_count = enqueued_count
        self.last_inventory_snapshot = current_snapshot
        self.last_sent_count = sent_count if enqueued_count == 0 else min(enqueued_count, sent_count)
        self.last_process_duration_ms = (time.perf_counter() - start_perf) * 1000.0

    def act(self):
        if not self.enabled:
            return
        try:
            if not Routines.Checks.Map.MapValid():
                self._reset_tracking_state()
                self.last_seen_map_id = 0
                return
            current_map_id = int(Map.GetMapID() or 0)
            if current_map_id > 0:
                if int(self.last_seen_map_id) <= 0:
                    self.last_seen_map_id = current_map_id
                elif current_map_id != int(self.last_seen_map_id):
                    self.last_seen_map_id = current_map_id
                    self._reset_tracking_state()
                    return
            if self.config_poll_timer.IsExpired():
                self.config_poll_timer.Reset()
                self._load_runtime_config()
            if self.debug_enabled and self.debug_timer.IsExpired():
                self.debug_timer.Reset()
                Py4GW.Console.Log(
                    "DropTrackerSender",
                    (
                        "active "
                        f"snapshot_size={len(self.last_inventory_snapshot)} "
                        f"items={self.last_snapshot_total} "
                        f"ready={self.last_snapshot_ready} "
                        f"not_ready={self.last_snapshot_not_ready} "
                        f"sent={self.last_sent_count} "
                        f"candidates={self.last_candidate_count} "
                        f"enqueued={self.last_enqueued_count} "
                        f"queued={len(self.outbox_queue)} "
                        f"acks={self.last_ack_count} "
                        f"pending_names={len(self.pending_slot_deltas)} "
                        f"role={'leader' if self._is_party_leader_client() else 'follower'} "
                        f"warmed={self.is_warmed_up} "
                        f"proc_ms={self.last_process_duration_ms:.2f}"
                    ),
                    Py4GW.Console.MessageType.Info,
                )
            if self.inventory_poll_timer.IsExpired():
                self.inventory_poll_timer.Reset()
                self._process_inventory_deltas()
            if self.outbox_queue:
                self._flush_outbox()
        except EXPECTED_RUNTIME_ERRORS:
            return

