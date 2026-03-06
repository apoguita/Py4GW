import os
import re
import sys
from typing import Any, cast

from Py4GWCoreLib import Item, Py4GW

from Sources.oazix.CustomBehaviors.skills.monitoring.item_mod_render_utils import (
    build_known_spellcasting_mod_lines,
    normalize_identified_armor_name,
    prune_generic_attribute_bonus_lines,
    render_mod_description_template,
    sort_stats_lines_like_ingame,
)

IMPORT_OPTIONAL_ERRORS = (ImportError, ModuleNotFoundError, AttributeError)
EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError, NameError)

try:
    from Py4GWCoreLib.enums_src.Item_enums import ItemType
    from Sources.marks_sources.mods_parser import ModDatabase, parse_modifiers, is_matching_item_type
except IMPORT_OPTIONAL_ERRORS:
    ItemType = None
    ModDatabase = None
    parse_modifiers = None
    is_matching_item_type = None


def _runtime_module(sender):
    try:
        return sys.modules.get(sender.__class__.__module__)
    except EXPECTED_RUNTIME_ERRORS:
        return None


def _runtime_attr(sender, name: str, default=None):
    module = _runtime_module(sender)
    if module is not None and hasattr(module, name):
        return getattr(module, name)
    return default


def load_mod_database(sender):
    mod_database_cls = _runtime_attr(sender, "ModDatabase", ModDatabase)
    py4gw = _runtime_attr(sender, "Py4GW", Py4GW)
    if mod_database_cls is None:
        sender.mod_db = None
        return
    candidate_dirs = []
    try:
        sources_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        candidate_dirs.append(os.path.join(sources_root, "marks_sources", "mods_data"))
    except EXPECTED_RUNTIME_ERRORS:
        pass
    try:
        project_root = py4gw.Console.get_projects_path()
        if project_root:
            candidate_dirs.append(os.path.join(project_root, "Sources", "marks_sources", "mods_data"))
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
            sender.mod_db = mod_database_cls.load(data_dir)
            if sender.mod_db is not None:
                return
        except EXPECTED_RUNTIME_ERRORS:
            continue
    sender.mod_db = None


def format_attribute_name(_sender, attr_name: str) -> str:
    txt = str(attr_name or "").replace("_", " ").strip()
    if txt.lower() == "none":
        return ""
    return txt


def render_mod_description_template_local(
    sender,
    description: str,
    matched_modifiers: list[tuple[int, int, int]],
    default_value: int = 0,
    attribute_name: str = "",
) -> list[str]:
    def _resolve_attribute_name(attr_id: int) -> str:
        try:
            from Py4GWCoreLib.enums import Attribute
            return sender._format_attribute_name(getattr(Attribute(int(attr_id)), "name", ""))
        except EXPECTED_RUNTIME_ERRORS:
            return ""

    return render_mod_description_template(
        description=str(description or ""),
        matched_modifiers=list(matched_modifiers or []),
        default_value=int(default_value),
        attribute_name=str(attribute_name or ""),
        resolve_attribute_name_fn=_resolve_attribute_name,
        format_attribute_name_fn=sender._format_attribute_name,
        unknown_attribute_template="Attribute {id}",
    )


def match_mod_definition_against_raw(_sender, definition_modifiers, raw_mods) -> list[tuple[int, int, int]]:
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


def weapon_mod_type_matches(sender, weapon_mod, item_type) -> bool:
    matcher = _runtime_attr(sender, "is_matching_item_type", is_matching_item_type)
    if item_type is None or matcher is None:
        return False
    try:
        for target in list(getattr(weapon_mod, "target_types", []) or []):
            try:
                if matcher(item_type, target):
                    return True
            except EXPECTED_RUNTIME_ERRORS:
                continue
        item_mods = getattr(weapon_mod, "item_mods", {}) or {}
        for target in list(item_mods.keys()):
            try:
                if matcher(item_type, target):
                    return True
            except EXPECTED_RUNTIME_ERRORS:
                continue
    except EXPECTED_RUNTIME_ERRORS:
        return False
    return False


def collect_fallback_mod_lines(sender, raw_mods, item_attr_txt: str, item_type=None) -> list[str]:
    lines = []
    if sender.mod_db is None:
        return lines
    best_by_ident = {}
    try:
        for weapon_mod in list(getattr(sender.mod_db, "weapon_mods", {}).values()):
            matched = sender._match_mod_definition_against_raw(getattr(weapon_mod, "modifiers", []), raw_mods)
            if not matched:
                continue
            ident_set = {int(m[0]) for m in matched}
            if not ident_set:
                continue
            desc = str(getattr(weapon_mod, "description", "") or "").strip()
            rendered = sender._render_mod_description_template(desc, matched, 0, item_attr_txt)
            if rendered:
                first_line = rendered[0]
                lower_desc = desc.lower()
                has_old_school = "[old school]" in lower_desc
                type_match = sender._weapon_mod_type_matches(weapon_mod, item_type)
                score = 0
                if type_match:
                    score += 100
                if has_old_school:
                    score += 20
                if not type_match and not has_old_school:
                    score -= 60
                score += min(len(matched), 3)
                for ident in ident_set:
                    prev = best_by_ident.get(ident)
                    if prev is None or score > int(prev.get("score", -999)):
                        best_by_ident[ident] = {"line": first_line, "score": score}
    except EXPECTED_RUNTIME_ERRORS:
        return lines
    for ident in sorted(best_by_ident.keys()):
        line = str(best_by_ident[ident].get("line", "")).strip()
        if line:
            lines.append(line)
    return lines


def collect_fallback_rune_lines(sender, raw_mods, item_attr_txt: str) -> list[str]:
    lines = []
    if sender.mod_db is None:
        return lines
    best_by_ident = {}
    try:
        for rune in list(getattr(sender.mod_db, "runes", {}).values()):
            matched = sender._match_mod_definition_against_raw(getattr(rune, "modifiers", []), raw_mods)
            if not matched:
                continue
            ident_set = {int(m[0]) for m in matched}
            if not ident_set:
                continue
            desc = str(getattr(rune, "description", "") or "").strip()
            rune_name = str(getattr(rune, "name", "") or "").strip()
            rendered = sender._render_mod_description_template(desc, matched, 0, item_attr_txt)
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
            if not deduped_candidates:
                continue
            score = min(len(matched), 4)
            for ident in ident_set:
                prev = best_by_ident.get(ident)
                if prev is None or score > int(prev.get("score", -999)):
                    best_by_ident[ident] = {"lines": list(deduped_candidates), "score": score}
    except EXPECTED_RUNTIME_ERRORS:
        return lines
    for ident in sorted(best_by_ident.keys()):
        for line in list(best_by_ident[ident].get("lines", []) or []):
            txt = str(line or "").strip()
            if txt:
                lines.append(txt)
    return lines


def build_known_spellcast_mod_lines(sender, raw_mods, item_attr_txt: str, item_type=None) -> list[str]:
    def _resolve_attribute_name(attr_id: int) -> str:
        try:
            from Py4GWCoreLib.enums import Attribute
            return sender._format_attribute_name(getattr(Attribute(int(attr_id)), "name", ""))
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


def prune_generic_attribute_bonus_lines_local(_sender, lines: list[str]) -> list[str]:
    return prune_generic_attribute_bonus_lines(lines)


def normalize_stats_lines(_sender, lines: list[str]) -> list[str]:
    normalized = []
    for raw in list(lines or []):
        txt = str(raw or "").strip()
        if not txt:
            continue
        if txt:
            normalized.append(txt)
    return sort_stats_lines_like_ingame(normalized)


def extract_parsed_mod_name_parts(_sender, parsed_result) -> tuple[str, str, str]:
    if not parsed_result:
        return "", "", ""
    prefix = ""
    suffix = ""
    inscription = ""
    try:
        for record in list(parsed_result or []):
            if not isinstance(record, dict):
                continue
            label = str(record.get("name", "") or "").strip()
            if not label:
                continue
            source = str(record.get("source", "") or "").strip().lower()
            category = str(record.get("category", "") or "").strip().lower()
            label_lower = label.lower()
            if not prefix and (source == "prefix" or category == "prefix"):
                prefix = label
            elif not suffix and (source == "suffix" or category == "suffix"):
                suffix = label
            elif not inscription and (
                "inscription" in source
                or "inscription" in category
                or label_lower.startswith('"')
                or label_lower.startswith("(")
            ):
                inscription = label
    except EXPECTED_RUNTIME_ERRORS:
        return "", "", ""
    return prefix, suffix, inscription


def _clean_item_name(sender, text: str) -> str:
    try:
        clean_text = sender._strip_tags(str(text or "")).strip()
    except EXPECTED_RUNTIME_ERRORS:
        clean_text = str(text or "").strip()
    return re.sub(r"^[\d,]+\s+", "", clean_text).strip()


def _load_live_item_instance(item_api, item_id: int):
    try:
        return item_api.item_instance(item_id)
    except EXPECTED_RUNTIME_ERRORS:
        return None


def _extract_raw_mods(modifiers) -> list[tuple[int, int, int]]:
    raw_mods: list[tuple[int, int, int]] = []
    for mod in list(modifiers or []):
        try:
            raw_mods.append((int(mod.GetIdentifier()), int(mod.GetArg1()), int(mod.GetArg2())))
        except EXPECTED_RUNTIME_ERRORS:
            continue
    return raw_mods


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


def _collect_live_item_modifiers(item_api, item_id: int, item_instance=None) -> list[tuple[int, int, int]]:
    try:
        api_raw_mods = _extract_raw_mods(item_api.Customization.Modifiers.GetModifiers(item_id))
    except EXPECTED_RUNTIME_ERRORS:
        api_raw_mods = []
    if item_instance is None:
        item_instance = _load_live_item_instance(item_api, item_id)
    if item_instance is None:
        return list(api_raw_mods)
    try:
        instance_raw_mods = _extract_raw_mods(getattr(item_instance, "modifiers", []) or [])
    except EXPECTED_RUNTIME_ERRORS:
        instance_raw_mods = []
    return _merge_raw_mod_lists(api_raw_mods, instance_raw_mods)


def _resolve_live_item_type_int(item_api, item_id: int, item_instance=None) -> int:
    try:
        item_type_value = item_api.GetItemType(item_id)
        if isinstance(item_type_value, (list, tuple)):
            item_type_value = item_type_value[0] if item_type_value else 0
        return int(item_type_value or 0)
    except EXPECTED_RUNTIME_ERRORS:
        if item_instance is None:
            item_instance = _load_live_item_instance(item_api, item_id)
        try:
            if item_instance and getattr(item_instance, "item_type", None):
                return int(item_instance.item_type.ToInt())
        except EXPECTED_RUNTIME_ERRORS:
            return 0
    return 0


def _resolve_live_model_id(item_api, item_id: int, item_instance=None) -> int:
    try:
        return int(item_api.GetModelID(item_id))
    except EXPECTED_RUNTIME_ERRORS:
        if item_instance is None:
            item_instance = _load_live_item_instance(item_api, item_id)
        try:
            return int(getattr(item_instance, "model_id", 0) or 0)
        except EXPECTED_RUNTIME_ERRORS:
            return 0


def _resolve_live_is_inscribable(item_api, item_id: int, item_instance=None):
    try:
        return bool(item_api.Customization.IsInscribable(item_id))
    except EXPECTED_RUNTIME_ERRORS:
        if item_instance is None:
            item_instance = _load_live_item_instance(item_api, item_id)
        try:
            return bool(getattr(item_instance, "is_inscribable", False))
        except EXPECTED_RUNTIME_ERRORS:
            return None


def _decode_signed_16(value: int) -> int:
    raw = int(value or 0) & 0xFFFF
    if raw >= 0x8000:
        return raw - 0x10000
    return raw


def _is_likely_shield_item(item_name: str, item_type_int: int = 0) -> bool:
    name_txt = str(item_name or "").strip().lower()
    if "shield" in name_txt:
        return True
    # Runtime bindings consistently report classic shields as type 24 in this codebase.
    return int(item_type_int or 0) == 24


def collect_manual_shield_defense_mod_lines(raw_mods, item_name: str = "", item_type_int: int = 0) -> list[str]:
    if not _is_likely_shield_item(item_name, item_type_int):
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


def _infer_name_variant(prefix: str, suffix: str, inherent: str, is_inscribable_hint=None) -> str:
    if is_inscribable_hint is True:
        return "inscribable"
    if is_inscribable_hint is False:
        return "old_school"
    has_suffix = bool(str(suffix or "").strip())
    has_inherent = bool(str(inherent or "").strip())
    if has_suffix and has_inherent:
        return "mixed"
    if has_suffix:
        return "old_school"
    if has_inherent:
        return "inscribable"
    return "unknown"


def _compose_old_school_name(clean_base: str, prefix: str, suffix: str) -> str:
    lower_base = str(clean_base or "").lower()
    parts = []
    changed = False
    prefix_txt = str(prefix or "").strip()
    suffix_txt = str(suffix or "").strip()
    if prefix_txt and prefix_txt.lower() not in lower_base:
        parts.append(prefix_txt)
        changed = True
    parts.append(clean_base)
    if suffix_txt and suffix_txt.lower() not in lower_base:
        parts.append(suffix_txt)
        changed = True
    candidate = " ".join(str(part or "").strip() for part in parts if str(part or "").strip()).strip()
    return candidate if changed and candidate and candidate.lower() != lower_base else ""


def _compose_inscribable_name(clean_base: str, prefix: str, inherent: str) -> str:
    lower_base = str(clean_base or "").lower()
    parts = []
    changed = False
    prefix_txt = str(prefix or "").strip()
    inherent_txt = str(inherent or "").strip()
    if prefix_txt and prefix_txt.lower() not in lower_base:
        parts.append(prefix_txt)
        changed = True
    parts.append(clean_base)
    if inherent_txt and inherent_txt.lower() not in lower_base:
        parts.append(f"({inherent_txt})")
        changed = True
    candidate = " ".join(str(part or "").strip() for part in parts if str(part or "").strip()).strip()
    return candidate if changed and candidate and candidate.lower() != lower_base else ""


def _emit_name_variant_debug(
    sender,
    branch: str,
    item_id: int,
    model_id: int,
    item_type_int: int,
    base_name: str,
    prefix: str,
    suffix: str,
    inherent: str,
    candidate: str,
    is_inscribable_hint=None,
    parsed_variant: str = "",
) -> None:
    message = (
        f"NAME BUILD branch={branch} item_id={int(item_id or 0)} model={int(model_id or 0)} "
        f"type={int(item_type_int or 0)} base='{str(base_name or '').strip() or '-'}' "
        f"prefix='{str(prefix or '').strip() or '-'}' suffix='{str(suffix or '').strip() or '-'}' "
        f"inherent='{str(inherent or '').strip() or '-'}' out='{str(candidate or '').strip() or '-'}' "
        f"hint={str(is_inscribable_hint)} parsed_variant={str(parsed_variant or '').strip() or '-'}"
    )
    try:
        if hasattr(sender, "_log_name_trace"):
            sender._log_name_trace(message)
    except EXPECTED_RUNTIME_ERRORS:
        pass
    try:
        if hasattr(sender, "_append_live_debug_log"):
            cast(Any, sender._append_live_debug_log)(
                "name_build_variant",
                message,
                dedupe_key=(
                    f"name_build:{int(item_id or 0)}:"
                    f"{int(model_id or 0)}:{str(branch or '').strip().lower()}:"
                    f"{str(base_name or '').strip().lower()}:{str(candidate or '').strip().lower()}"
                ),
                dedupe_interval_s=0.9,
                branch=str(branch or "").strip() or "unknown",
                item_id=int(item_id or 0),
                model_id=int(model_id or 0),
                item_type=int(item_type_int or 0),
                base_name=str(base_name or "").strip(),
                prefix=str(prefix or "").strip(),
                suffix=str(suffix or "").strip(),
                inherent=str(inherent or "").strip(),
                output_name=str(candidate or "").strip(),
                is_inscribable_hint=is_inscribable_hint,
                parsed_variant=str(parsed_variant or "").strip() or "unknown",
            )
    except EXPECTED_RUNTIME_ERRORS:
        pass


def _synthesize_identified_name_from_parts(
    sender,
    base_name: str,
    raw_mods: list[tuple[int, int, int]],
    item_type_int: int,
    model_id: int,
    item_id: int = 0,
    is_inscribable_hint=None,
) -> str:
    parse_modifiers_fn = _runtime_attr(sender, "parse_modifiers", parse_modifiers)
    item_type_enum = _runtime_attr(sender, "ItemType", ItemType)
    clean_base = _clean_item_name(sender, base_name)
    if not clean_base or not raw_mods or sender.mod_db is None or parse_modifiers_fn is None or item_type_enum is None:
        return ""
    try:
        item_type = item_type_enum(int(item_type_int))
    except EXPECTED_RUNTIME_ERRORS:
        return ""
    try:
        parsed = parse_modifiers_fn(list(raw_mods), item_type, int(model_id or 0), sender.mod_db)
    except EXPECTED_RUNTIME_ERRORS:
        return ""
    prefix, suffix, inherent = sender._extract_parsed_mod_name_parts(parsed)
    parsed_variant = _infer_name_variant(prefix, suffix, inherent, None)
    branch = _infer_name_variant(prefix, suffix, inherent, is_inscribable_hint)
    if branch == "inscribable":
        candidate = _compose_inscribable_name(clean_base, prefix, inherent)
    elif branch == "old_school":
        candidate = _compose_old_school_name(clean_base, prefix, suffix)
    elif branch == "mixed":
        # Mixed marker set is treated as old-school naming to keep "of ..." suffix stable.
        candidate = _compose_old_school_name(clean_base, prefix, suffix)
    else:
        candidate = (
            _compose_old_school_name(clean_base, prefix, suffix)
            or _compose_inscribable_name(clean_base, prefix, inherent)
        )
    normalized_armor_name = normalize_identified_armor_name(clean_base, prefix, suffix, inherent)
    if normalized_armor_name:
        candidate = normalized_armor_name
    _emit_name_variant_debug(
        sender,
        branch,
        item_id=int(item_id or 0),
        model_id=int(model_id or 0),
        item_type_int=int(item_type_int or 0),
        base_name=clean_base,
        prefix=prefix,
        suffix=suffix,
        inherent=inherent,
        candidate=candidate,
        is_inscribable_hint=is_inscribable_hint,
        parsed_variant=parsed_variant,
    )
    return candidate


def build_identified_name_from_modifiers(sender, *args, **_kwargs) -> str:
    item_api = _runtime_attr(sender, "Item", Item)
    if len(args) >= 4:
        return _synthesize_identified_name_from_parts(
            sender,
            args[0],
            list(args[1] or []),
            int(args[2] or 0),
            int(args[3] or 0),
        )
    item_id = int(args[0] or 0) if len(args) >= 1 else 0
    fallback_name = str(args[1] or "").strip() if len(args) >= 2 else ""
    if item_id <= 0:
        return fallback_name
    item_instance = _load_live_item_instance(item_api, item_id)
    raw_mods = _collect_live_item_modifiers(item_api, item_id, item_instance)
    if not raw_mods:
        return _clean_item_name(sender, fallback_name)
    base_name = _clean_item_name(sender, fallback_name)
    if not base_name:
        try:
            if item_api.IsNameReady(item_id):
                base_name = _clean_item_name(sender, item_api.GetName(item_id) or "")
        except EXPECTED_RUNTIME_ERRORS:
            base_name = ""
    item_type_int = _resolve_live_item_type_int(item_api, item_id, item_instance)
    model_id = _resolve_live_model_id(item_api, item_id, item_instance)
    is_inscribable_hint = _resolve_live_is_inscribable(item_api, item_id, item_instance)
    synthesized = _synthesize_identified_name_from_parts(
        sender,
        base_name,
        raw_mods,
        item_type_int,
        model_id,
        item_id=item_id,
        is_inscribable_hint=is_inscribable_hint,
    )
    return synthesized or base_name


def resolve_best_live_item_name(sender, item_id: int, fallback_name: str = "") -> str:
    item_api = _runtime_attr(sender, "Item", Item)
    if item_id <= 0:
        return ""
    fallback_clean = _clean_item_name(sender, fallback_name)
    try:
        if item_api.IsNameReady(item_id):
            live_name = _clean_item_name(sender, item_api.GetName(item_id) or "")
        else:
            item_api.RequestName(item_id)
            live_name = ""
    except EXPECTED_RUNTIME_ERRORS:
        live_name = ""
    try:
        if item_api.Usage.IsIdentified(item_id):
            synthesized = sender._build_identified_name_from_modifiers(item_id, live_name or fallback_clean)
            if synthesized:
                live_name = synthesized
        else:
            if not live_name:
                live_name = fallback_clean
            return live_name
    except EXPECTED_RUNTIME_ERRORS:
        if not live_name:
            live_name = fallback_clean
        return live_name
    return live_name


def build_item_stats_text(sender, item_id: int, item_name: str = "") -> str:
    item_api = _runtime_attr(sender, "Item", Item)
    parse_modifiers_fn = _runtime_attr(sender, "parse_modifiers", parse_modifiers)
    item_type_enum = _runtime_attr(sender, "ItemType", ItemType)
    if item_id <= 0:
        return ""
    try:
        is_identified = None
        try:
            is_identified = bool(item_api.Usage.IsIdentified(item_id))
        except EXPECTED_RUNTIME_ERRORS:
            is_identified = None
        if is_identified is False:
            return "Unidentified"
        item_instance = _load_live_item_instance(item_api, item_id)
        if not item_instance:
            return ""
        model_id = int(getattr(item_instance, "model_id", 0) or 0)
        value = int(getattr(item_instance, "value", 0) or 0)
        lines: list[str] = []
        clean_name = sender._resolve_best_live_item_name(item_id, item_name)
        if clean_name:
            lines.append(clean_name)
        if value > 0:
            lines.append(f"Value: {value} gold")

        raw_mods = _collect_live_item_modifiers(item_api, item_id, item_instance)
        if is_identified is None and not raw_mods:
            return "\n".join(lines)
        req_attr = 0
        req_val = 0
        if raw_mods:
            for ident, arg1, arg2 in raw_mods:
                if ident in (42920, 42120):
                    if int(arg2) > 0 and int(arg1) > 0:
                        lines.append(f"Damage: {int(arg2)}-{int(arg1)}")
                elif ident == 42936:
                    if int(arg1) > 0:
                        if int(arg2) > 0:
                            lines.append(f"Armor: {int(arg1)} (vs {int(arg2)})")
                        else:
                            lines.append(f"Armor: {int(arg1)}")
                elif ident == 10136:
                    req_attr = int(arg1)
                    req_val = int(arg2)
            if req_val > 0:
                attr_txt = ""
                try:
                    from Py4GWCoreLib.enums import Attribute

                    attr_txt = sender._format_attribute_name(getattr(Attribute(req_attr), "name", ""))
                except EXPECTED_RUNTIME_ERRORS:
                    attr_txt = ""
                lines.append(f"Requires {req_val} {attr_txt}".rstrip())
            lines.extend(
                collect_manual_shield_defense_mod_lines(
                    raw_mods,
                    clean_name,
                    _resolve_live_item_type_int(item_api, item_id, item_instance),
                )
            )

        if not raw_mods or sender.mod_db is None:
            return "\n".join(lines)

        try:
            item_type = item_type_enum(_resolve_live_item_type_int(item_api, item_id, item_instance)) if item_type_enum is not None else None
        except EXPECTED_RUNTIME_ERRORS:
            item_type = None

        item_attr_txt_for_known = ""
        if req_val > 0:
            try:
                from Py4GWCoreLib.enums import Attribute

                item_attr_txt_for_known = sender._format_attribute_name(getattr(Attribute(req_attr), "name", ""))
            except EXPECTED_RUNTIME_ERRORS:
                item_attr_txt_for_known = ""

        if parse_modifiers_fn is not None and item_type is not None:
            parsed = parse_modifiers_fn(raw_mods, item_type, model_id, sender.mod_db)
            item_attr_txt = sender._format_attribute_name(getattr(parsed.attribute, "name", ""))
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
                attr_txt = sender._format_attribute_name(getattr(parsed.attribute, "name", ""))
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
                    rendered_lines = sender._render_mod_description_template(desc, matched_mods, value, item_attr_txt)
                    if rendered_lines:
                        lines.extend(rendered_lines)
                    else:
                        lines.append(f"{name} ({value})" if value else name)
            if parsed.runes:
                for rune in parsed.runes:
                    name = str(getattr(rune.rune, "name", "") or "").strip()
                    desc = str(getattr(rune.rune, "description", "") or "").strip()
                    rune_mods = list(getattr(rune, "modifiers", []) or [])
                    rendered_lines = sender._render_mod_description_template(desc, rune_mods, 0, item_attr_txt)
                    if name:
                        lines.append(name)
                    if rendered_lines:
                        lines.extend(rendered_lines)
            lines.extend(sender._collect_fallback_mod_lines(raw_mods, item_attr_txt, item_type))
            lines.extend(sender._collect_fallback_rune_lines(raw_mods, item_attr_txt))
        try:
            lines.extend(sender._build_known_spellcast_mod_lines(raw_mods, item_attr_txt_for_known, item_type))
        except EXPECTED_RUNTIME_ERRORS:
            pass

        lines = sender._normalize_stats_lines(lines)
    except EXPECTED_RUNTIME_ERRORS:
        return ""
    return "\n".join(lines)


def _normalize_name_for_identity(name: str) -> str:
    text = re.sub(r"[^a-z0-9]+", " ", str(name or "").strip().lower())
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    parts = []
    for token in text.split():
        if token.endswith("ies") and len(token) > 3:
            token = token[:-3] + "y"
        elif token.endswith("s") and len(token) > 2 and not token.endswith("ss"):
            token = token[:-1]
        parts.append(token)
    return " ".join(parts).strip()


def _item_names_compatible_for_identity(live_name: str, expected_name: str) -> bool:
    left = _normalize_name_for_identity(live_name)
    right = _normalize_name_for_identity(expected_name)
    if not left or not right:
        return True
    if left == right:
        return True
    return left.startswith(right) or right.startswith(left)


def _resolve_item_id_by_slot(sender, bag_id: int, slot_id: int) -> int:
    item_array_api = _runtime_attr(sender, "ItemArray")
    item_api = _runtime_attr(sender, "Item", Item)
    target_bag = int(bag_id or 0)
    target_slot = int(slot_id or 0)
    if item_array_api is None or target_bag <= 0 or target_slot <= 0:
        return 0
    try:
        bag_items = item_array_api.GetItemArray(item_array_api.CreateBagList(target_bag))
    except EXPECTED_RUNTIME_ERRORS:
        return 0
    for candidate_item_id_raw in list(bag_items or []):
        candidate_item_id = int(candidate_item_id_raw or 0)
        if candidate_item_id <= 0:
            continue
        try:
            item_instance = item_api.item_instance(candidate_item_id)
        except EXPECTED_RUNTIME_ERRORS:
            item_instance = None
        try:
            candidate_slot = int(getattr(item_instance, "slot", 0) or 0) if item_instance else int(item_api.GetSlot(candidate_item_id))
        except EXPECTED_RUNTIME_ERRORS:
            candidate_slot = 0
        if candidate_slot == target_slot:
            return int(candidate_item_id)
    return 0


def entry_item_identity_matches(
    sender,
    item_id: int,
    expected_model_id: int,
    expected_name_signature: str,
    expected_item_name: str = "",
    allow_unready_name: bool = False,
) -> bool:
    item_api = _runtime_attr(sender, "Item", Item)
    make_name_signature_fn = _runtime_attr(sender, "make_name_signature", lambda _s: "")
    live_item_id = int(item_id or 0)
    if live_item_id <= 0:
        return False
    wanted_model_id = int(expected_model_id or 0)
    wanted_signature = str(expected_name_signature or "").strip().lower()
    unknown_item_sig = str(make_name_signature_fn("Unknown Item") or "").strip().lower()
    try:
        live_model_id = int(item_api.GetModelID(live_item_id))
    except EXPECTED_RUNTIME_ERRORS:
        return False
    if wanted_model_id > 0 and live_model_id > 0 and live_model_id != wanted_model_id:
        return False
    if wanted_signature and wanted_signature != unknown_item_sig:
        try:
            if not item_api.IsNameReady(live_item_id):
                item_api.RequestName(live_item_id)
                return bool(allow_unready_name)
            live_name = item_api.GetName(live_item_id) or ""
            live_name = _clean_item_name(sender, live_name)
        except EXPECTED_RUNTIME_ERRORS:
            return False
        if not live_name:
            return False
        live_signature = str(make_name_signature_fn(live_name) or "").strip().lower()
        if live_signature != wanted_signature and (
            not _item_names_compatible_for_identity(live_name, str(expected_item_name or "").strip())
        ):
            return False
    return True


def resolve_event_item_id_for_stats(sender, entry: dict) -> int:
    item_array_api = _runtime_attr(sender, "ItemArray")
    if not isinstance(entry, dict):
        return 0
    expected_item_id = int(entry.get("item_id", 0) or 0)
    expected_model_id = int(entry.get("model_id", 0) or 0)
    expected_name_signature = str(entry.get("name_signature", "") or "").strip().lower()
    expected_item_name = str(entry.get("item_name", "") or "").strip()
    if expected_item_id > 0 and sender._entry_item_identity_matches(
        expected_item_id,
        expected_model_id,
        expected_name_signature,
        expected_item_name,
        allow_unready_name=True,
    ):
        return int(expected_item_id)
    slot_item_id = _resolve_item_id_by_slot(
        sender,
        int(entry.get("bag_id", 0) or 0),
        int(entry.get("slot_id", 0) or 0),
    )
    if slot_item_id > 0 and sender._entry_item_identity_matches(
        slot_item_id,
        expected_model_id,
        expected_name_signature,
        expected_item_name,
        allow_unready_name=True,
    ):
        return int(slot_item_id)
    if item_array_api is None:
        return 0
    try:
        bags = item_array_api.CreateBagList(1, 2, 3, 4)
        item_ids = item_array_api.GetItemArray(bags)
    except EXPECTED_RUNTIME_ERRORS:
        return 0
    candidates = []
    for candidate_item_id in list(item_ids or []):
        candidate_item_id = int(candidate_item_id or 0)
        if not sender._entry_item_identity_matches(
            candidate_item_id,
            expected_model_id,
            expected_name_signature,
            expected_item_name,
            allow_unready_name=False,
        ):
            continue
        candidates.append(candidate_item_id)
        if len(candidates) > 1:
            break
    if len(candidates) == 1:
        return int(candidates[0])
    if len(candidates) > 1 and slot_item_id > 0 and slot_item_id in candidates:
        return int(slot_item_id)
    return 0
