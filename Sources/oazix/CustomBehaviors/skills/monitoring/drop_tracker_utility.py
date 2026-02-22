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

try:
    from Py4GWCoreLib.enums_src.Item_enums import ItemType
    from Sources.marks_sources.mods_parser import ModDatabase, parse_modifiers, is_matching_item_type
except Exception:
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
    _STATE_VERSION = 11

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
                self.state_version = self._STATE_VERSION
                self._reset_tracking_state()
            return
        self._initialized = True
        self.state_version = self._STATE_VERSION
        self.inventory_poll_timer = ThrottledTimer(350)
        self.last_inventory_snapshot: dict[int, tuple[str, str, int]] = {}
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
        try:
            # .../Sources/oazix/CustomBehaviors/skills/monitoring -> .../Sources
            sources_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            data_dir = os.path.join(
                sources_root,
                "marks_sources",
                "mods_data",
            )
            self.mod_db = ModDatabase.load(data_dir)
        except Exception:
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
        desc = str(description or "").strip()
        if not desc:
            return []

        by_id = {}
        for ident, arg1, arg2 in matched_modifiers:
            by_id[int(ident)] = (int(arg1), int(arg2))

        def _resolve(token: str, ident_text: str) -> int:
            idx = 1 if token == "arg1" else 2
            if ident_text:
                pair = by_id.get(int(ident_text))
                if pair:
                    return int(pair[idx - 1])
                return 0
            for _ident, arg1, arg2 in matched_modifiers:
                value = int(arg1) if idx == 1 else int(arg2)
                if value != 0:
                    return value
            return int(default_value) if idx == 2 else 0

        rendered = re.sub(
            r"\{(arg1|arg2)(?:\[(\d+)\])?\}",
            lambda m: str(_resolve(m.group(1), m.group(2) or "")),
            desc,
        )
        if attribute_name:
            rendered = rendered.replace("item's attribute", attribute_name).replace("Item's attribute", attribute_name)
        rendered = rendered.replace("(Chance: +", "(Chance: ")
        rendered = rendered.replace("  ", " ").strip()
        return [line.strip() for line in rendered.splitlines() if line.strip()]

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
                except Exception:
                    continue
            item_mods = getattr(weapon_mod, "item_mods", {}) or {}
            for target in list(item_mods.keys()):
                try:
                    if is_matching_item_type(item_type, target):
                        return True
                except Exception:
                    continue
        except Exception:
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
        except Exception:
            return lines
        for ident in sorted(best_by_ident.keys()):
            line = str(best_by_ident[ident].get("line", "")).strip()
            if line:
                lines.append(line)
        return lines

    def _build_known_spellcast_mod_lines(self, raw_mods, item_attr_txt: str) -> list[str]:
        lines = []
        attr_txt = str(item_attr_txt or "").strip()
        attr_phrase = f"{attr_txt} " if attr_txt else "item's attribute "
        for ident, arg1, _arg2 in list(raw_mods or []):
            ident_i = int(ident)
            chance = int(arg1)
            if chance <= 0:
                continue
            if ident_i == 8712:
                lines.append(f"Halves casting time of spells (Chance: {chance}%)")
            elif ident_i == 9128:
                lines.append(f"Halves skill recharge of spells (Chance: {chance}%)")
            elif ident_i == 10248:
                lines.append(f"Halves casting time of {attr_phrase}spells (Chance: {chance}%)")
            elif ident_i == 10280:
                lines.append(f"Halves skill recharge of {attr_phrase}spells (Chance: {chance}%)")
        return lines

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
            except Exception:
                raw_mods = []
            if raw_mods:
                req_attr = 0
                req_val = 0
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
                    except Exception:
                        attr_txt = ""
                    lines.append(f"Requires {req_val} {attr_txt}".rstrip())

            if not raw_mods or self.mod_db is None:
                return "\n".join(lines)

            try:
                item_type_int, _ = Item.GetItemType(item_id)
                item_type = ItemType(item_type_int) if ItemType is not None else None
            except Exception:
                item_type = None

            item_attr_txt_for_known = ""
            if req_val > 0:
                try:
                    from Py4GWCoreLib.enums import Attribute
                    item_attr_txt_for_known = self._format_attribute_name(getattr(Attribute(req_attr), "name", ""))
                except Exception:
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
                elif parsed.runes:
                    for rune in parsed.runes:
                        name = str(getattr(rune.rune, "name", "") or "").strip()
                        desc = str(getattr(rune.rune, "description", "") or "").strip()
                        rune_mods = list(getattr(rune, "modifiers", []) or [])
                        rendered_lines = self._render_mod_description_template(desc, rune_mods, 0, item_attr_txt)
                        if rendered_lines:
                            lines.extend(rendered_lines)
                        elif name:
                            lines.append(name)
                lines.extend(self._collect_fallback_mod_lines(raw_mods, item_attr_txt, item_type))
            lines.extend(self._build_known_spellcast_mod_lines(raw_mods, item_attr_txt_for_known))

            return "\n".join(lines)
        except Exception:
            return ""

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

    def _strip_tags(self, text: str) -> str:
        return re.sub(r"<[^>]+>", "", text or "")

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
        except Exception:
            return None
        return None

    def _is_party_leader_client(self) -> bool:
        try:
            is_leader = int(Player.GetAgentID()) == int(Party.GetPartyLeaderID())
            self.last_known_is_leader = bool(is_leader)
            return bool(is_leader)
        except Exception:
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
        except Exception:
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
        except Exception:
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
        except Exception:
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
        except Exception:
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
            "stats_text": self._build_item_stats_text(int(item_id), item_name or "Unknown Item"),
            "attempts": 0,
            "next_retry_at": 0.0,
            "acked": False,
        }
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
                except Exception:
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
                for entry in self.outbox_queue:
                    if str(entry.get("event_id", "")) == str(event_id):
                        if not entry.get("acked", False):
                            entry["acked"] = True
                            acked_count += 1
                shmem.MarkMessageAsFinished(my_email, msg_idx)
            self.last_ack_count = acked_count
            return acked_count
        except Exception:
            return 0

    def _flush_outbox(self) -> int:
        if self.enable_delivery_ack and self.ack_poll_timer.IsExpired():
            self.ack_poll_timer.Reset()
            self._poll_ack_messages()

        now_ts = time.time()
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
        for entry in self.outbox_queue:
            if sent >= int(self.max_send_per_tick):
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
                        break
                entry["name_chunks_sent"] = True

            if not entry.get("stats_chunks_sent", False):
                ok_stats = self._send_stats_chunks(
                    receiver_email=receiver_email,
                    my_email=my_email,
                    event_id=str(entry.get("event_id", "")),
                    stats_text=str(entry.get("stats_text", "") or ""),
                )
                # Stats are best-effort; never block the drop event itself.
                if ok_stats:
                    entry["stats_chunks_sent"] = True

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
                break
            entry["attempts"] = int(entry.get("attempts", 0)) + 1
            if self.enable_delivery_ack:
                entry["next_retry_at"] = now_ts + float(self.retry_interval_seconds)
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
                        except Exception:
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
                    snapshot[(bag_id, slot_id)] = (clean_name, rarity, qty, model_id, int(item_id))

            self.last_snapshot_ready = ready_count
            self.last_snapshot_not_ready = not_ready_count
        except Exception:
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
        prev_item_ids = {int(v[4]) for v in self.last_inventory_snapshot.values() if isinstance(v, tuple) and len(v) > 4}
        # Only names from slots that changed this tick are safe for pending-name resolution.
        changed_itemid_to_ready_name: dict[int, tuple[str, str]] = {}
        changed_model_rarity_to_ready_name: dict[tuple[int, str], str] = {}
        live_slots = set()
        for slot_key, (name, rarity, qty, _model_id, _item_id) in current_snapshot.items():
            live_slots.add(slot_key)
            previous = self.last_inventory_snapshot.get(slot_key)
            is_unknown_name = name.startswith("Model#")
            changed_this_tick = False
            if previous is None:
                # Item moved between slots: do not treat as pickup.
                if int(_item_id) in prev_item_ids:
                    continue
                changed_this_tick = True
                if is_unknown_name:
                    pending = self.pending_slot_deltas.get(slot_key)
                    now_ts = time.time()
                    if pending is None or not isinstance(pending, dict):
                        self.pending_slot_deltas[slot_key] = {
                            "qty": int(qty),
                            "model_id": int(_model_id),
                            "item_id": int(_item_id),
                            "rarity": rarity,
                            "first_seen": now_ts,
                            "last_seen": now_ts,
                        }
                    else:
                        pending["qty"] = int(pending.get("qty", 0)) + int(qty)
                        pending["model_id"] = int(_model_id)
                        pending["item_id"] = int(_item_id)
                        pending["rarity"] = pending.get("rarity") or rarity
                        pending["last_seen"] = now_ts
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
                    continue
                changed_this_tick = True
                if is_unknown_name:
                    pending = self.pending_slot_deltas.get(slot_key)
                    now_ts = time.time()
                    if pending is None or not isinstance(pending, dict):
                        self.pending_slot_deltas[slot_key] = {
                            "qty": int(qty),
                            "model_id": int(_model_id),
                            "item_id": int(_item_id),
                            "rarity": rarity,
                            "first_seen": now_ts,
                            "last_seen": now_ts,
                        }
                    else:
                        pending["qty"] = int(pending.get("qty", 0)) + int(qty)
                        pending["model_id"] = int(_model_id)
                        pending["item_id"] = int(_item_id)
                        pending["rarity"] = pending.get("rarity") or rarity
                        pending["last_seen"] = now_ts
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
                    pending = self.pending_slot_deltas.get(slot_key)
                    now_ts = time.time()
                    if pending is None or not isinstance(pending, dict):
                        self.pending_slot_deltas[slot_key] = {
                            "qty": int(delta),
                            "model_id": int(_model_id),
                            "item_id": int(_item_id),
                            "rarity": rarity,
                            "first_seen": now_ts,
                            "last_seen": now_ts,
                        }
                    else:
                        pending["qty"] = int(pending.get("qty", 0)) + int(delta)
                        pending["model_id"] = int(_model_id)
                        pending["item_id"] = int(_item_id)
                        pending["rarity"] = pending.get("rarity") or rarity
                        pending["last_seen"] = now_ts
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
            pending_rarity = str(pending_entry.get("rarity") or "Unknown")

            # Best match: exact item identity.
            if pending_item_id > 0:
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
                                except Exception:
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
                except Exception:
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
        except Exception:
            return
