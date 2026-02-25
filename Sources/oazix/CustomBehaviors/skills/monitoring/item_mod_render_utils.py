import re

EXPECTED_RUNTIME_ERRORS = (TypeError, ValueError, RuntimeError, AttributeError, IndexError, KeyError, OSError)


SPELLCASTING_ITEM_TYPE_IDS = {22, 26, 41}
FOE_TYPE_32896_NAMES = {
    0: "Undead",
    1: "Charr",
    2: "Trolls",
    3: "Plants",
    4: "Skeletons",
    5: "Giants",
    6: "Dwarves",
    7: "Tengu",
    8: "Demons",
    9: "Dragons",
    10: "Ogres",
}
ATTRIBUTE_TOKEN_RULES = {
    # Rune attribute encoding: id 8680 stores attribute id in arg1.
    (8680, "arg1"): "attribute_id",
    # Damage-vs-foe encoding: id 32896 stores foe class id in arg1.
    (32896, "arg1"): "foe_type_32896",
}

_BASE_DAMAGE_RE = re.compile(r"(?i)^damage:\s*\d+\s*-\s*\d+")
_BASE_ARMOR_RE = re.compile(r"(?i)^armor:\s*\d+")
_BASE_ENERGY_RE = re.compile(r"(?i)^energy\s*[:+-]\s*\d+")
_BASE_HEALTH_RE = re.compile(r"(?i)^health\s*[:+-]\s*\d+")
_REQUIRES_RE = re.compile(r"(?i)^requires\s+\d+\b")
_VALUE_RE = re.compile(r"(?i)^value:\s*\d+\s*gold\b")
_SALE_VALUE_RE = re.compile(r"(?i)^improved sale value$")
_INSCRIPTION_RE = re.compile(r"(?i)^inscription:")
_RUNE_OR_INSIGNIA_RE = re.compile(r"(?i)\b(rune|insignia)\b")
_HCT_RE = re.compile(r"(?i)^halves casting time\b")
_HSR_RE = re.compile(r"(?i)^halves skill recharge\b")
_CONDITIONAL_RE = re.compile(r"(?i)\b(while|stance|enchanted|hexed|attacking|health|energy)\b")
_DURATION_RE = re.compile(r"(?i)^(reduces|lengthens)\s+[a-z][a-z '()-]*\s+duration\b")
_ENERGY_REGEN_RE = re.compile(r"(?i)^energy regeneration\s*[+-]\s*\d+")
_MOD_HINT_RE = re.compile(
    r"(?i)^(halves|reduces|lengthens|increases|while\b|chance\b|damage\s*\+\d+|armor\s*\+\d+|energy\s*[+-]\d+|health\s*[+-]\d+)"
)
_ATTRIBUTE_BONUS_RE = re.compile(r"(?i)^([a-z][a-z ']+|attribute\s+\d+|\d+)\s*\+\s*\d+")


def _safe_int(value, default=0):
    try:
        return int(value)
    except EXPECTED_RUNTIME_ERRORS:
        return default


def _looks_like_stat_line(text: str) -> bool:
    txt = str(text or "").strip()
    if not txt:
        return False
    return bool(
        _BASE_DAMAGE_RE.match(txt)
        or _BASE_ARMOR_RE.match(txt)
        or _BASE_ENERGY_RE.match(txt)
        or _BASE_HEALTH_RE.match(txt)
        or _REQUIRES_RE.match(txt)
        or _VALUE_RE.match(txt)
        or _SALE_VALUE_RE.match(txt)
        or _INSCRIPTION_RE.match(txt)
        or _RUNE_OR_INSIGNIA_RE.search(txt)
        or _MOD_HINT_RE.match(txt)
        or _ATTRIBUTE_BONUS_RE.match(txt)
    )


def _is_title_candidate(text: str) -> bool:
    txt = str(text or "").strip()
    if not txt:
        return False
    if ":" in txt:
        return False
    if len(txt.split()) > 10:
        return False
    if _BASE_DAMAGE_RE.match(txt) or _BASE_ARMOR_RE.match(txt) or _BASE_ENERGY_RE.match(txt) or _BASE_HEALTH_RE.match(txt):
        return False
    if _REQUIRES_RE.match(txt) or _VALUE_RE.match(txt) or _SALE_VALUE_RE.match(txt):
        return False
    if _INSCRIPTION_RE.match(txt) or _HCT_RE.match(txt) or _HSR_RE.match(txt):
        return False
    if re.search(r"(?i)\(\s*chance:", txt):
        return False
    if re.search(r"\d+%", txt):
        return False
    if re.search(r"\+\s*\d+", txt):
        return False
    return True


def _mod_subrank(text: str, caster_context: bool) -> int:
    txt = str(text or "").strip()
    if _HCT_RE.match(txt):
        return 0 if caster_context else 4
    if _HSR_RE.match(txt):
        return 1 if caster_context else 4
    if _BASE_ENERGY_RE.match(txt) or _ENERGY_REGEN_RE.match(txt):
        return 2 if caster_context else 4
    if _DURATION_RE.match(txt):
        return 3 if caster_context else 4
    if _INSCRIPTION_RE.match(txt):
        return 2
    if _ATTRIBUTE_BONUS_RE.match(txt):
        return 3 if caster_context else 2
    if _BASE_HEALTH_RE.match(txt):
        return 5 if caster_context else 4
    if _CONDITIONAL_RE.search(txt):
        return 5
    if _RUNE_OR_INSIGNIA_RE.search(txt):
        return 6
    return 4


def sort_stats_lines_like_ingame(lines) -> list[str]:
    """Sort stat lines in a stable, in-game-like tooltip order."""
    source_lines = [str(raw or "").strip() for raw in list(lines or []) if str(raw or "").strip()]
    has_core_stat_line = any(
        _BASE_DAMAGE_RE.match(txt)
        or _BASE_ARMOR_RE.match(txt)
        or _BASE_ENERGY_RE.match(txt)
        or _BASE_HEALTH_RE.match(txt)
        or _REQUIRES_RE.match(txt)
        or _VALUE_RE.match(txt)
        or _SALE_VALUE_RE.match(txt)
        for txt in source_lines
    )
    title_index = -1
    if has_core_stat_line:
        for idx, txt in enumerate(source_lines):
            if not _is_title_candidate(txt):
                continue
            title_index = idx
            break

    title_text = source_lines[title_index].lower() if 0 <= title_index < len(source_lines) else ""
    has_damage_line = any(_BASE_DAMAGE_RE.match(txt) for txt in source_lines)
    has_armor_line = any(_BASE_ARMOR_RE.match(txt) for txt in source_lines)
    has_hct = any(_HCT_RE.match(txt) for txt in source_lines)
    has_hsr = any(_HSR_RE.match(txt) for txt in source_lines)
    caster_title_tokens = ("wand", "staff", "scepter", "focus", "offhand")
    caster_context = any(token in title_text for token in caster_title_tokens) or (has_hct and has_hsr)

    ranked = []
    for idx, txt in enumerate(source_lines):

        if idx == title_index:
            rank_key = (0, 0)
        elif _BASE_DAMAGE_RE.match(txt) or _BASE_ARMOR_RE.match(txt):
            if _BASE_DAMAGE_RE.match(txt):
                rank_key = (20, 0)
            else:
                rank_key = (20, 1)
        elif _BASE_ENERGY_RE.match(txt):
            # Focus-like energy bases can appear before requirements.
            if not has_damage_line and not has_armor_line:
                rank_key = (22, 0)
            else:
                rank_key = (60, _mod_subrank(txt, caster_context))
        elif _BASE_HEALTH_RE.match(txt):
            # Health lines are usually modifiers, not base header stats.
            rank_key = (60, _mod_subrank(txt, caster_context))
        elif _REQUIRES_RE.match(txt):
            rank_key = (30, 0)
        elif _INSCRIPTION_RE.match(txt):
            rank_key = (40, 0)
        elif _SALE_VALUE_RE.match(txt):
            rank_key = (80, 0)
        elif _VALUE_RE.match(txt):
            rank_key = (90, 0)
        else:
            rank_key = (60, _mod_subrank(txt, caster_context))
        ranked.append((rank_key[0], rank_key[1], idx, txt))

    ranked.sort(key=lambda item: (item[0], item[1], item[2]))
    return [txt for _, _, _, txt in ranked]


def is_wand_or_staff_type(item_type) -> bool:
    if item_type is None:
        return False
    item_type_int = _safe_int(item_type, -1)
    return item_type_int in SPELLCASTING_ITEM_TYPE_IDS


def _resolve_attribute_name(attribute_id: int, resolve_attribute_name_fn) -> str:
    if resolve_attribute_name_fn is None:
        return ""
    try:
        return str(resolve_attribute_name_fn(int(attribute_id)) or "").strip()
    except EXPECTED_RUNTIME_ERRORS:
        return ""


def _extract_chance(arg1: int, arg2: int, use_range_chance: bool) -> int:
    if not use_range_chance:
        return arg1 if arg1 > 0 else 0
    if 5 <= arg1 <= 25:
        return arg1
    # Only use arg2 as fallback when arg1 is not carrying a meaningful value.
    # This prevents treating attribute IDs as chance percentages.
    if arg1 <= 0 and 5 <= arg2 <= 25:
        return arg2
    return 0


def _apply_attribute_format(attribute_name: str, format_attribute_name_fn) -> str:
    txt = str(attribute_name or "").strip()
    if not txt:
        return ""
    if format_attribute_name_fn is None:
        return txt
    try:
        return str(format_attribute_name_fn(txt) or "").strip()
    except EXPECTED_RUNTIME_ERRORS:
        return txt


def render_mod_description_template(
    description: str,
    matched_modifiers,
    default_value: int = 0,
    attribute_name: str = "",
    resolve_attribute_name_fn=None,
    format_attribute_name_fn=None,
    attribute_token_rules=None,
    unknown_attribute_template: str = "Attribute {id}",
    unknown_foe_type_template: str = "FoeType {id}",
) -> list[str]:
    desc = str(description or "").strip()
    if not desc:
        return []

    by_id = {}
    mods = list(matched_modifiers or [])
    for ident, arg1, arg2 in mods:
        by_id[_safe_int(ident)] = (_safe_int(arg1), _safe_int(arg2))

    rules = dict(ATTRIBUTE_TOKEN_RULES)
    if isinstance(attribute_token_rules, dict):
        rules.update(attribute_token_rules)

    def _resolve(token: str, ident_text: str) -> int:
        idx = 1 if token == "arg1" else 2
        if ident_text:
            pair = by_id.get(_safe_int(ident_text))
            if pair:
                return int(pair[idx - 1])
            return 0
        for _ident, arg1, arg2 in mods:
            value = _safe_int(arg1) if idx == 1 else _safe_int(arg2)
            if value != 0:
                return value
        return _safe_int(default_value) if idx == 2 else 0

    def _resolve_render_token(token: str, ident_text: str) -> str:
        value = _resolve(token, ident_text)
        ident_i = _safe_int(ident_text)
        decode_kind = rules.get((ident_i, token), "")
        if decode_kind == "attribute_id" and int(value) > 0:
            attr_name = _resolve_attribute_name(int(value), resolve_attribute_name_fn)
            attr_name = _apply_attribute_format(attr_name, format_attribute_name_fn)
            if attr_name:
                return attr_name
            if unknown_attribute_template:
                return str(unknown_attribute_template).format(id=int(value))
        if decode_kind == "foe_type_32896" and int(value) >= 0:
            foe_name = FOE_TYPE_32896_NAMES.get(int(value), "")
            if foe_name:
                return foe_name
            if unknown_foe_type_template:
                return str(unknown_foe_type_template).format(id=int(value))
        return str(value)

    rendered = re.sub(
        r"\{(arg1|arg2)(?:\[(\d+)\])?\}",
        lambda m: _resolve_render_token(m.group(1), m.group(2) or ""),
        desc,
    )
    attr_txt = _apply_attribute_format(str(attribute_name or ""), format_attribute_name_fn)
    if attr_txt:
        rendered = rendered.replace("item's attribute", attr_txt).replace("Item's attribute", attr_txt)
    rendered = rendered.replace("(Chance: +", "(Chance: ")
    rendered = re.sub(r"[ \t]{2,}", " ", rendered).strip()
    return [line.strip() for line in rendered.splitlines() if line.strip()]


def build_spellcast_hct_hsr_lines(
    raw_mods,
    item_attr_txt: str = "",
    item_type=None,
    resolve_attribute_name_fn=None,
    include_raw_when_no_chance: bool = False,
    use_range_chance: bool = True,
) -> list[str]:
    lines = []
    attr_txt = str(item_attr_txt or "").strip()
    attr_phrase = f"{attr_txt} " if attr_txt else "item's attribute "
    is_spellcasting_weapon = is_wand_or_staff_type(item_type)

    for ident, arg1, arg2 in list(raw_mods or []):
        ident_i = _safe_int(ident)
        arg1_i = _safe_int(arg1)
        arg2_i = _safe_int(arg2)
        chance = _extract_chance(arg1_i, arg2_i, use_range_chance=use_range_chance)

        if ident_i == 8712:
            if chance > 0:
                lines.append(f"Halves casting time of spells (Chance: {chance}%)")
            elif include_raw_when_no_chance:
                lines.append(f"Halves casting time of spells (raw: arg1={arg1_i}, arg2={arg2_i})")
            continue

        if ident_i == 8728:
            if not is_spellcasting_weapon:
                continue
            attr_from_mod = _resolve_attribute_name(arg2_i, resolve_attribute_name_fn)
            if chance > 0:
                if attr_from_mod:
                    lines.append(f"Halves casting time of {attr_from_mod} spells (Chance: {chance}%)")
                else:
                    lines.append(f"Halves casting time of {attr_phrase}spells (Chance: {chance}%)")
            elif include_raw_when_no_chance:
                if attr_from_mod:
                    lines.append(f"Halves casting time of {attr_from_mod} spells (raw: arg1={arg1_i}, arg2={arg2_i})")
                else:
                    lines.append(f"Halves casting time of {attr_phrase}spells (raw: arg1={arg1_i}, arg2={arg2_i})")
            continue

        if ident_i in (9128, 9112):
            if ident_i == 9112 and not is_spellcasting_weapon:
                continue
            attr_from_mod = _resolve_attribute_name(arg2_i, resolve_attribute_name_fn) if ident_i == 9112 else ""
            if chance > 0:
                if attr_from_mod:
                    lines.append(f"Halves skill recharge of {attr_from_mod} spells (Chance: {chance}%)")
                else:
                    lines.append("Halves skill recharge of spells (Chance: {chance}%)".format(chance=chance))
            elif include_raw_when_no_chance:
                if attr_from_mod:
                    lines.append(f"Halves skill recharge of {attr_from_mod} spells (raw: arg1={arg1_i}, arg2={arg2_i})")
                else:
                    lines.append(f"Halves skill recharge of spells (raw: arg1={arg1_i}, arg2={arg2_i})")
            continue

        if ident_i == 10248:
            if chance > 0:
                lines.append(f"Halves casting time of {attr_phrase}spells (Chance: {chance}%)")
            elif include_raw_when_no_chance:
                lines.append(f"Halves casting time of {attr_phrase}spells (raw: arg1={arg1_i}, arg2={arg2_i})")
            continue

        if ident_i == 10280:
            if chance > 0:
                lines.append(f"Halves skill recharge of {attr_phrase}spells (Chance: {chance}%)")
            elif include_raw_when_no_chance:
                lines.append(f"Halves skill recharge of {attr_phrase}spells (raw: arg1={arg1_i}, arg2={arg2_i})")
            continue

    return lines


def build_known_spellcasting_mod_lines(
    raw_mods,
    item_attr_txt: str = "",
    item_type=None,
    resolve_attribute_name_fn=None,
    include_raw_when_no_chance: bool = False,
    use_range_chance: bool = True,
) -> list[str]:
    lines = []
    attr_txt = str(item_attr_txt or "").strip()
    attr_phrase = f"{attr_txt} " if attr_txt else "item's attribute "

    for ident, arg1, arg2 in list(raw_mods or []):
        ident_i = _safe_int(ident)
        arg1_i = _safe_int(arg1)
        arg2_i = _safe_int(arg2)

        if ident_i == 10328:
            cond_by_arg1 = {
                0: "Bleeding",
                1: "Blind",
                3: "Crippled",
                4: "Deep Wound",
                5: "Disease",
                6: "Poison",
                7: "Dazed",
                8: "Weakness",
            }
            cond = cond_by_arg1.get(arg1_i, "")
            if cond:
                lines.append(f"Reduces {cond} duration on you by 20%")
            continue

        if ident_i == 9880:
            # 9880 is seen on many caster weapons as a metadata marker and is not a
            # reliable standalone "reduces crippled duration" stat line.
            continue

        if ident_i == 9240:
            if arg1_i <= 0:
                continue
            attr_name = _resolve_attribute_name(arg1_i, resolve_attribute_name_fn)
            if not attr_name:
                attr_name = f"Attribute {arg1_i}"
            chance = arg2_i if 5 <= arg2_i <= 25 else 0
            if chance > 0:
                lines.append(f"{attr_name} +1 ({chance}% chance while using skills)")
            elif include_raw_when_no_chance:
                lines.append(f"{attr_name} +1 (raw: arg1={arg1_i}, arg2={arg2_i})")
            continue

        if ident_i == 10296:
            chance = arg1_i if 5 <= arg1_i <= 25 else 0
            if chance > 0:
                lines.append(f"{attr_phrase}+1 (Chance: {chance}%)")
            elif include_raw_when_no_chance:
                lines.append(f"{attr_phrase}+1 (raw: arg1={arg1_i}, arg2={arg2_i})")
            continue

        if ident_i in (26568, 25288, 8920):
            # Common spellcaster/offhand base-energy encodings.
            # 26568 (offhand focus base) commonly carries full energy in arg1 and
            # a half-scale mirror in arg2 (e.g. arg1=12, arg2=6).
            if ident_i == 26568:
                if arg1_i > 0:
                    energy_val = arg1_i
                elif arg2_i > 0:
                    energy_val = arg2_i * 2
                else:
                    energy_val = 0
            elif ident_i == 25288:
                energy_val = arg1_i if arg1_i > 0 else arg2_i
            else:
                # 8920 can carry noisy arg1 values on some payloads; prefer arg2.
                energy_val = arg2_i if arg2_i > 0 else arg1_i
            if energy_val > 0:
                lines.append(f"Energy +{energy_val}")
            continue

        if ident_i == 8392:
            regen_penalty = arg2_i if arg2_i > 0 else arg1_i
            if regen_penalty > 0:
                lines.append(f"Energy regeneration -{regen_penalty}")
            continue

        if ident_i == 8984:
            if arg2_i > 0 and arg1_i > 0:
                lines.append(f"Energy +{arg2_i} (while Health is below +{arg1_i}%)")
            continue

        if ident_i == 8968:
            if arg2_i > 0 and arg1_i > 0:
                lines.append(f"Energy +{arg2_i} (while health is above +{arg1_i}%)")
            continue

        if ident_i == 8952:
            if arg2_i > 0:
                lines.append(f"Energy +{arg2_i} (while Enchanted)")
            continue

        if ident_i == 9000:
            if arg2_i > 0:
                lines.append(f"Energy +{arg2_i} (while hexed)")
            continue

    lines.extend(
        build_spellcast_hct_hsr_lines(
            raw_mods,
            item_attr_txt=attr_txt,
            item_type=item_type,
            resolve_attribute_name_fn=resolve_attribute_name_fn,
            include_raw_when_no_chance=include_raw_when_no_chance,
            use_range_chance=use_range_chance,
        )
    )
    return lines


def prune_generic_attribute_bonus_lines(lines: list[str]) -> list[str]:
    if not lines:
        return lines
    detailed_bonus_re = re.compile(r"^([A-Za-z][A-Za-z ]+)\s*\+\s*(\d+)\s*\((\d+)% chance while using skills\)$", re.IGNORECASE)
    generic_bonus_re = re.compile(r"^(?:Attribute\s+\d+|\d+)\s*\+\s*(\d+)\s*\((\d+)% chance while using skills\)$", re.IGNORECASE)
    detailed_pairs = set()

    for line in lines:
        txt = str(line or "").strip()
        m = detailed_bonus_re.match(txt)
        if not m:
            continue
        attr_text = str(m.group(1) or "").strip().lower()
        if not attr_text or attr_text.startswith("attribute "):
            continue
        detailed_pairs.add((m.group(2), m.group(3)))

    if not detailed_pairs:
        return lines

    filtered = []
    for line in lines:
        txt = str(line or "").strip()
        m = generic_bonus_re.match(txt)
        if m and (m.group(1), m.group(2)) in detailed_pairs:
            continue
        filtered.append(line)
    return filtered

