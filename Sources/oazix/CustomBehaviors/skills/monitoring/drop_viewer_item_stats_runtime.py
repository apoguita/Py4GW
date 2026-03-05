import json
import re
import sys
import time
from typing import Any

from Py4GWCoreLib import Item, Player

from Sources.oazix.CustomBehaviors.skills.monitoring.drop_tracker_stats_render import (
    get_cached_rendered_stats,
    update_render_cache,
)

IMPORT_OPTIONAL_ERRORS = (ImportError, ModuleNotFoundError, AttributeError)
EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError, NameError)

try:
    from Py4GWCoreLib import Attribute
except IMPORT_OPTIONAL_ERRORS:
    Attribute = None

try:
    from Py4GWCoreLib.enums_src.Item_enums import ItemType
    from Sources.marks_sources.mods_parser import parse_modifiers
except IMPORT_OPTIONAL_ERRORS:
    ItemType = None
    parse_modifiers = None


def _decode_signed_16(value: int) -> int:
    raw = int(value or 0) & 0xFFFF
    if raw >= 0x8000:
        return raw - 0x10000
    return raw


def _is_likely_shield_item(snapshot: dict[str, Any]) -> bool:
    try:
        item_name = str(snapshot.get("name", "") or "").strip().lower()
    except EXPECTED_RUNTIME_ERRORS:
        item_name = ""
    if "shield" in item_name:
        return True
    try:
        item_type = int(snapshot.get("item_type", 0) or 0)
    except EXPECTED_RUNTIME_ERRORS:
        item_type = 0
    return item_type in {24, 30, 31, 32, 33}


def _collect_manual_shield_defense_mod_lines(raw_mods, snapshot: dict[str, Any]) -> list[str]:
    if not _is_likely_shield_item(snapshot):
        return []
    lines: list[str] = []
    seen: set[str] = set()
    for mod in list(raw_mods or []):
        if not isinstance(mod, (list, tuple)) or len(mod) < 3:
            continue
        arg1 = _decode_signed_16(int(mod[1] or 0))
        arg2 = _decode_signed_16(int(mod[2] or 0))
        chance = 0
        reduction = 0
        if 1 <= abs(int(arg1)) <= 25 and int(arg2) < 0:
            chance = abs(int(arg1))
            reduction = int(arg2)
        elif 1 <= abs(int(arg2)) <= 25 and int(arg1) < 0:
            chance = abs(int(arg2))
            reduction = int(arg1)
        if chance <= 0 or reduction >= 0:
            continue
        line = f"Received physical damage {int(reduction)} (Chance: {int(chance)}%)"
        key = re.sub(r"[^a-z0-9]+", "", line.lower())
        if key in seen:
            continue
        seen.add(key)
        lines.append(line)
    return lines


def _viewer_runtime_module(viewer):
    try:
        return sys.modules.get(viewer.__class__.__module__)
    except EXPECTED_RUNTIME_ERRORS:
        return None


def _runtime_attr(viewer, name: str, fallback):
    module = _viewer_runtime_module(viewer)
    if module is not None and hasattr(module, name):
        return getattr(module, name)
    return fallback


def _merge_raw_mod_lists(*mod_lists) -> list[tuple[int, int, int]]:
    merged: list[tuple[int, int, int]] = []
    seen: set[tuple[int, int, int]] = set()
    for mod_list in mod_lists:
        for mod in list(mod_list or []):
            if mod in seen:
                continue
            seen.add(mod)
            merged.append(mod)
    return merged


def get_live_item_snapshot(viewer, item_id: int, item_name: str = "") -> dict[str, Any]:
    item_api = _runtime_attr(viewer, "Item", Item)
    player_api = _runtime_attr(viewer, "Player", Player)
    item_id = int(item_id or 0)
    if item_id <= 0:
        return {}
    snapshot: dict[str, Any] = {
        "name": "",
        "value": 0,
        "model_id": 0,
        "item_type": 0,
        "identified": False,
        "raw_mods": [],
        "_source": "local_api",
        "_owner": "",
    }
    try:
        try:
            snapshot["_owner"] = viewer._ensure_text(player_api.GetName()).strip()
        except EXPECTED_RUNTIME_ERRORS:
            snapshot["_owner"] = ""
        clean_name = ""
        identified = False
        try:
            if item_api.IsNameReady(item_id):
                clean_name = viewer._clean_item_name(item_api.GetName(item_id))
            else:
                item_api.RequestName(item_id)
        except EXPECTED_RUNTIME_ERRORS:
            clean_name = ""

        try:
            snapshot["value"] = max(0, viewer._safe_int(item_api.Properties.GetValue(item_id), 0))
        except EXPECTED_RUNTIME_ERRORS:
            snapshot["value"] = 0
        try:
            snapshot["model_id"] = max(0, viewer._safe_int(item_api.GetModelID(item_id), 0))
        except EXPECTED_RUNTIME_ERRORS:
            snapshot["model_id"] = 0
        try:
            item_type_int, _ = item_api.GetItemType(item_id)
            snapshot["item_type"] = max(0, viewer._safe_int(item_type_int, 0))
        except EXPECTED_RUNTIME_ERRORS:
            snapshot["item_type"] = 0
            try:
                item_instance = item_api.item_instance(item_id)
                if item_instance and getattr(item_instance, "item_type", None):
                    snapshot["item_type"] = max(0, viewer._safe_int(item_instance.item_type.ToInt(), 0))
            except EXPECTED_RUNTIME_ERRORS:
                snapshot["item_type"] = 0

        try:
            identified = bool(item_api.Usage.IsIdentified(item_id))
        except EXPECTED_RUNTIME_ERRORS:
            identified = False
        snapshot["identified"] = identified

        if not clean_name and not identified:
            clean_name = viewer._clean_item_name(item_name)
        snapshot["name"] = clean_name

        raw_mods = []
        if identified:
            try:
                api_raw_mods = [
                    (int(mod.GetIdentifier()), int(mod.GetArg1()), int(mod.GetArg2()))
                    for mod in item_api.Customization.Modifiers.GetModifiers(item_id)
                ]
            except EXPECTED_RUNTIME_ERRORS:
                api_raw_mods = []
            try:
                item_instance = item_api.item_instance(item_id)
                instance_raw_mods = [
                    (int(mod.GetIdentifier()), int(mod.GetArg1()), int(mod.GetArg2()))
                    for mod in list(getattr(item_instance, "modifiers", []) or [])
                ]
            except EXPECTED_RUNTIME_ERRORS:
                instance_raw_mods = []
            raw_mods = _merge_raw_mod_lists(api_raw_mods, instance_raw_mods)
        snapshot["raw_mods"] = raw_mods
        if identified and raw_mods:
            synthesized_name = viewer._build_identified_name_from_modifiers(
                snapshot.get("name", ""),
                list(raw_mods),
                int(snapshot.get("item_type", 0) or 0),
                int(snapshot.get("model_id", 0) or 0),
            )
            if synthesized_name:
                snapshot["name"] = synthesized_name
    except EXPECTED_RUNTIME_ERRORS:
        return {}
    return snapshot


def build_item_snapshot_payload_from_live_item(viewer, item_id: int, item_name: str = "") -> str:
    snapshot = get_live_item_snapshot(viewer, item_id, item_name)
    if not snapshot:
        return ""
    try:
        payload = {
            "n": viewer._ensure_text(snapshot.get("name", "")),
            "v": int(viewer._safe_int(snapshot.get("value", 0), 0)),
            "m": int(viewer._safe_int(snapshot.get("model_id", 0), 0)),
            "t": int(viewer._safe_int(snapshot.get("item_type", 0), 0)),
            "i": 1 if bool(snapshot.get("identified", False)) else 0,
            "mods": [
                [int(mod[0]), int(mod[1]), int(mod[2])]
                for mod in list(snapshot.get("raw_mods", []) or [])
                if isinstance(mod, (list, tuple)) and len(mod) >= 3
            ],
        }
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
    except EXPECTED_RUNTIME_ERRORS:
        return ""


def build_item_stats_from_snapshot(viewer, snapshot: dict[str, Any]) -> str:
    attribute_api = _runtime_attr(viewer, "Attribute", Attribute)
    item_type_api = _runtime_attr(viewer, "ItemType", ItemType)
    parse_modifiers_fn = _runtime_attr(viewer, "parse_modifiers", parse_modifiers)
    try:
        if not isinstance(snapshot, dict):
            return ""
        lines = []
        clean_name = viewer._clean_item_name(snapshot.get("name", ""))
        if "|" in clean_name:
            clean_name = clean_name.split("|", 1)[0].strip()
        identified = bool(snapshot.get("identified", False))
        if not identified:
            return viewer._build_unidentified_stats_text()
        if clean_name:
            lines.append(clean_name)

        value = max(0, viewer._safe_int(snapshot.get("value", 0), 0))
        if value > 0:
            lines.append(f"Value: {value} gold")

        raw_mods = []
        for mod in list(snapshot.get("raw_mods", []) or []):
            if not isinstance(mod, (list, tuple)) or len(mod) < 3:
                continue
            raw_mods.append((int(mod[0]), int(mod[1]), int(mod[2])))
        if not raw_mods:
            return "\n".join(lines)

        req_attr = 0
        req_val = 0
        for ident, arg1, arg2 in raw_mods:
            if ident in (42920, 42120):
                if int(arg2) > 0 and int(arg1) > 0:
                    lines.append(f"Damage: {int(arg2)}-{int(arg1)}")
            elif ident == 42936:
                if int(arg1) > 0:
                    lines.append(f"Armor: {int(arg1)}" if int(arg2) <= 0 else f"Armor: {int(arg1)} (vs {int(arg2)})")
            elif ident == 10136:
                req_attr = int(arg1)
                req_val = int(arg2)
            elif ident == 9720:
                lines.append("Improved sale value")
            elif ident == 9736:
                lines.append("Highly salvageable")
        if req_val > 0:
            attr_txt = ""
            try:
                if attribute_api is not None:
                    attr_txt = viewer._format_attribute_name(getattr(attribute_api(req_attr), "name", ""))
            except EXPECTED_RUNTIME_ERRORS:
                attr_txt = ""
            lines.append(f"Requires {req_val} {attr_txt}".rstrip())

        item_type = None
        item_type_int = max(0, viewer._safe_int(snapshot.get("item_type", 0), 0))
        if item_type_api is not None:
            try:
                item_type = item_type_api(item_type_int)
            except EXPECTED_RUNTIME_ERRORS:
                item_type = None

        item_attr_txt_for_known = ""
        if req_val > 0:
            try:
                if attribute_api is not None:
                    item_attr_txt_for_known = viewer._format_attribute_name(getattr(attribute_api(req_attr), "name", ""))
            except EXPECTED_RUNTIME_ERRORS:
                item_attr_txt_for_known = ""

        parsed_any_mod_line = False
        suppress_unknown_ids: set[int] = set()
        if viewer.mod_db is not None:
            parser_attr_txt = item_attr_txt_for_known
            if parse_modifiers_fn is not None and item_type is not None:
                try:
                    parsed = parse_modifiers_fn(raw_mods, item_type, int(viewer._safe_int(snapshot.get("model_id", 0), 0)), viewer.mod_db)
                    item_attr_txt = viewer._format_attribute_name(getattr(parsed.attribute, "name", ""))
                    if item_attr_txt:
                        parser_attr_txt = item_attr_txt
                        item_attr_txt_for_known = item_attr_txt
                    for mod in parsed.weapon_mods:
                        nm = viewer._ensure_text(getattr(mod.weapon_mod, "name", "")).strip()
                        if not nm:
                            continue
                        val = int(getattr(mod, "value", 0))
                        matched_mods = list(getattr(mod, "matched_modifiers", []) or [])
                        desc = viewer._ensure_text(getattr(mod.weapon_mod, "description", "")).strip()
                        rendered_lines = viewer._render_mod_description_template(desc, matched_mods, val, parser_attr_txt)
                        if rendered_lines:
                            lines.extend(rendered_lines)
                            parsed_any_mod_line = True
                        else:
                            lines.append(f"{nm} ({val})" if val else nm)
                            parsed_any_mod_line = True
                        for matched in list(getattr(mod, "matched_modifiers", []) or []):
                            if isinstance(matched, (list, tuple)) and len(matched) >= 1:
                                suppress_unknown_ids.add(max(0, viewer._safe_int(matched[0], 0)))
                    for rune in parsed.runes:
                        rune_name = viewer._ensure_text(getattr(rune.rune, "name", "")).strip()
                        rune_desc = viewer._ensure_text(getattr(rune.rune, "description", "")).strip()
                        rune_mods = list(getattr(rune, "modifiers", []) or [])
                        rendered_lines = viewer._render_mod_description_template(rune_desc, rune_mods, 0, parser_attr_txt)
                        if rune_name:
                            lines.append(rune_name)
                            parsed_any_mod_line = True
                        if rendered_lines:
                            lines.extend(rendered_lines)
                            parsed_any_mod_line = True
                        for matched in list(getattr(rune, "modifiers", []) or []):
                            if isinstance(matched, (list, tuple)) and len(matched) >= 1:
                                suppress_unknown_ids.add(max(0, viewer._safe_int(matched[0], 0)))
                except EXPECTED_RUNTIME_ERRORS:
                    pass
            if item_type is not None:
                if not parsed_any_mod_line:
                    lines.extend(viewer._collect_fallback_mod_lines(raw_mods, parser_attr_txt, item_type))
                lines.extend(viewer._collect_fallback_rune_lines(raw_mods, parser_attr_txt))

        if not parsed_any_mod_line:
            name_mod_lines = viewer._extract_mod_lines_from_item_name(snapshot.get("name", ""))
            if name_mod_lines:
                lines.extend(name_mod_lines)
                parsed_any_mod_line = True

        lines.extend(viewer._collect_manual_named_mod_lines(raw_mods))
        lines.extend(_collect_manual_shield_defense_mod_lines(raw_mods, snapshot))
        try:
            lines.extend(viewer._build_known_spellcast_mod_lines(raw_mods, item_attr_txt_for_known, item_type))
        except EXPECTED_RUNTIME_ERRORS:
            pass
        viewer._record_unknown_mod_identifiers(
            raw_mods,
            snapshot=snapshot,
            source=viewer._ensure_text(snapshot.get("_source", "")),
            suppress_mod_ids=suppress_unknown_ids,
        )

        normalized_lines = []
        split_pattern = re.compile(
            r"(?i)(?<!^)(requires\s+\d+|damage:\s*\d|armor:\s*\d|energy\s*[+-]\d|halves\s|reduces\s|value:\s*\d|improved sale value)"
        )
        for line in lines:
            txt = viewer._ensure_text(line).strip()
            if not txt:
                continue
            while True:
                m = split_pattern.search(txt)
                if not m:
                    break
                left = txt[:m.start()].strip()
                right = txt[m.start():].strip()
                if left:
                    normalized_lines.append(left)
                txt = right
            if txt:
                normalized_lines.append(txt)

        return viewer._normalize_stats_text("\n".join(normalized_lines))
    except EXPECTED_RUNTIME_ERRORS:
        return ""


def build_item_stats_from_payload_text(
    viewer,
    payload_text: str,
    fallback_item_name: str = "",
    owner_name: str = "",
) -> str:
    payload_raw = viewer._ensure_text(payload_text).strip()
    if not payload_raw:
        return ""
    try:
        payload = json.loads(payload_raw)
        if not isinstance(payload, dict):
            return ""
    except EXPECTED_RUNTIME_ERRORS:
        return ""
    snapshot = {
        "name": viewer._clean_item_name(payload.get("n", "")) or viewer._clean_item_name(fallback_item_name),
        "value": viewer._safe_int(payload.get("v", 0), 0),
        "model_id": viewer._safe_int(payload.get("m", 0), 0),
        "item_type": viewer._safe_int(payload.get("t", 0), 0),
        "identified": bool(payload.get("i")) if "i" in payload else bool(list(payload.get("mods", []) or [])),
        "raw_mods": payload.get("mods", []),
        "_source": "shared_payload",
        "_owner": viewer._ensure_text(owner_name).strip(),
    }
    return build_item_stats_from_snapshot(viewer, snapshot)


def render_payload_stats_cached(
    viewer,
    cache_key: str,
    payload_text: str,
    fallback_item_name: str = "",
    owner_name: str = "",
) -> str:
    event_key = viewer._ensure_text(cache_key).strip()
    payload_raw = viewer._ensure_text(payload_text).strip()
    if not event_key or not payload_raw:
        return ""
    cached_rendered = get_cached_rendered_stats(viewer.stats_render_cache_by_event, event_key, payload_raw)
    if cached_rendered:
        cached = viewer.stats_render_cache_by_event.get(event_key, None)
        if isinstance(cached, dict):
            cached["updated_at"] = time.time()
        return cached_rendered
    rendered = build_item_stats_from_payload_text(viewer, payload_raw, fallback_item_name, owner_name=owner_name).strip()
    update_render_cache(viewer.stats_render_cache_by_event, event_key, payload_raw, rendered, time.time())
    return rendered
