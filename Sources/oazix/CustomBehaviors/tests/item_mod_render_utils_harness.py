import sys
import re
from pathlib import Path

# Allow running as a standalone script from repository root.
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Sources.oazix.CustomBehaviors.skills.monitoring.item_mod_render_utils import (
    build_spellcast_hct_hsr_lines,
    prune_generic_attribute_bonus_lines,
    render_mod_description_template,
)


ATTRIBUTE_NAMES = {
    4: "Blood Magic",
    11: "Communing",
    14: "Divine Favor",
    19: "Hammer Mastery",
}


def _resolve_attr_name(attr_id: int) -> str:
    return ATTRIBUTE_NAMES.get(int(attr_id), "")


def _viewer_format(attr_name: str) -> str:
    txt = str(attr_name or "").replace("_", " ").strip()
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", txt)


def _sender_format(attr_name: str) -> str:
    txt = str(attr_name or "").replace("_", " ").strip()
    if txt.lower() == "none":
        return ""
    return txt


def test_unicorn_hct_line():
    raw_mods = [
        (10136, 32, 9),
        (9400, 11, 0),
        (8728, 20, 4),
        (9880, 0, 0),
        (42920, 22, 11),
        (49152, 0, 0),
    ]
    lines = build_spellcast_hct_hsr_lines(
        raw_mods,
        item_attr_txt="Communing",
        item_type=22,
        resolve_attribute_name_fn=_resolve_attr_name,
    )
    assert "Halves casting time of Blood Magic spells (Chance: 20%)" in lines


def test_holy_rod_hsr_line():
    raw_mods = [
        (10136, 16, 9),
        (9400, 5, 0),
        (9112, 19, 14),
        (9880, 0, 4),
        (42920, 22, 11),
        (49152, 0, 0),
    ]
    lines = build_spellcast_hct_hsr_lines(
        raw_mods,
        item_attr_txt="Divine Favor",
        item_type=22,
        resolve_attribute_name_fn=_resolve_attr_name,
    )
    assert "Halves skill recharge of Divine Favor spells (Chance: 19%)" in lines


def test_hct_uses_arg2_when_arg1_empty():
    lines = build_spellcast_hct_hsr_lines(
        [(8712, 0, 20)],
        item_attr_txt="",
        item_type=22,
        resolve_attribute_name_fn=_resolve_attr_name,
    )
    assert "Halves casting time of spells (Chance: 20%)" in lines


def test_hct_hsr_hidden_for_non_spellcasting_weapon():
    lines = build_spellcast_hct_hsr_lines(
        [(8728, 20, 4), (9112, 19, 14)],
        item_attr_txt="Swordsmanship",
        item_type=2,
        resolve_attribute_name_fn=_resolve_attr_name,
    )
    assert not lines


def test_prune_generic_bonus_when_detailed_exists():
    lines = [
        "25 +1 (19% chance while using skills)",
        "Marksmanship +1 (19% chance while using skills)",
    ]
    filtered = prune_generic_attribute_bonus_lines(lines)
    assert "Marksmanship +1 (19% chance while using skills)" in filtered
    assert "25 +1 (19% chance while using skills)" not in filtered


def test_keep_generic_bonus_when_no_match():
    lines = [
        "25 +1 (18% chance while using skills)",
        "Marksmanship +1 (19% chance while using skills)",
    ]
    filtered = prune_generic_attribute_bonus_lines(lines)
    assert "25 +1 (18% chance while using skills)" in filtered
    assert "Marksmanship +1 (19% chance while using skills)" in filtered


def test_render_rune_attribute_with_name():
    lines = render_mod_description_template(
        description="+{arg2[8680]} {arg1[8680]} (Non-stacking)\n-{arg2[8408]} Health",
        matched_modifiers=[(8680, 19, 2), (8408, 0, 35)],
        resolve_attribute_name_fn=_resolve_attr_name,
    )
    assert "+2 Hammer Mastery (Non-stacking)" in lines
    assert "-35 Health" in lines


def test_render_rune_attribute_unknown_fallback():
    lines = render_mod_description_template(
        description="+{arg2[8680]} {arg1[8680]} (Non-stacking)",
        matched_modifiers=[(8680, 999, 3)],
        resolve_attribute_name_fn=_resolve_attr_name,
    )
    assert "+3 Attribute 999 (Non-stacking)" in lines


def test_render_vs_foe_type_name():
    lines = render_mod_description_template(
        description="Damage +{arg1[41544]}% (vs. {arg1[32896]})",
        matched_modifiers=[(41544, 15, 0), (32896, 1, 0)],
        resolve_attribute_name_fn=_resolve_attr_name,
    )
    assert "Damage +15% (vs. Charr)" in lines


def test_render_vs_foe_type_unknown_fallback():
    lines = render_mod_description_template(
        description="Damage +{arg1[41544]}% (vs. {arg1[32896]})",
        matched_modifiers=[(41544, 15, 0), (32896, 99, 0)],
        resolve_attribute_name_fn=_resolve_attr_name,
    )
    assert "Damage +15% (vs. FoeType 99)" in lines


def test_wrapper_equivalent_viewer_options():
    lines = render_mod_description_template(
        description="Halves casting time on spells of item's attribute (Chance: {arg1[10248]}%)",
        matched_modifiers=[(10248, 20, 0)],
        attribute_name="HammerMastery",
        format_attribute_name_fn=_viewer_format,
    )
    assert "Halves casting time on spells of Hammer Mastery (Chance: 20%)" in lines


def test_wrapper_equivalent_sender_options():
    lines = render_mod_description_template(
        description="Halves casting time on spells of item's attribute (Chance: {arg1[10248]}%)",
        matched_modifiers=[(10248, 20, 0)],
        attribute_name="none",
        format_attribute_name_fn=_sender_format,
    )
    assert "Halves casting time on spells of item's attribute (Chance: 20%)" in lines


if __name__ == "__main__":
    test_unicorn_hct_line()
    test_holy_rod_hsr_line()
    test_hct_uses_arg2_when_arg1_empty()
    test_hct_hsr_hidden_for_non_spellcasting_weapon()
    test_prune_generic_bonus_when_detailed_exists()
    test_keep_generic_bonus_when_no_match()
    test_render_rune_attribute_with_name()
    test_render_rune_attribute_unknown_fallback()
    test_render_vs_foe_type_name()
    test_render_vs_foe_type_unknown_fallback()
    test_wrapper_equivalent_viewer_options()
    test_wrapper_equivalent_sender_options()
    print("[HARNESS] item_mod_render_utils OK")
