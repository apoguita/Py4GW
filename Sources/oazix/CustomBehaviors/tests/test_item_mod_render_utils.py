from Sources.oazix.CustomBehaviors.skills.monitoring.item_mod_render_utils import (
    build_known_spellcasting_mod_lines,
    build_spellcast_hct_hsr_lines,
    normalize_identified_armor_name,
    sort_stats_lines_like_ingame,
)


def test_sort_stats_lines_like_ingame_places_core_lines_like_tooltip():
    lines = [
        "Value: 224 gold",
        "Halves casting time of spells (Chance: 20%)",
        "Holy Staff",
        "Requires 9 Divine Favor",
        "Damage: 11-22",
        "Improved sale value",
    ]

    ordered = sort_stats_lines_like_ingame(lines)

    assert ordered == [
        "Holy Staff",
        "Damage: 11-22",
        "Requires 9 Divine Favor",
        "Halves casting time of spells (Chance: 20%)",
        "Improved sale value",
        "Value: 224 gold",
    ]


def test_sort_stats_lines_like_ingame_keeps_modifier_relative_order():
    lines = [
        "Storm Bow",
        "Requires 9 Marksmanship",
        "Damage: 15-28",
        "Lengthens Bleeding duration on foes by 33%",
        "Halves skill recharge of spells (Chance: 20%)",
        "Value: 100 gold",
    ]

    ordered = sort_stats_lines_like_ingame(lines)

    assert ordered[:3] == ["Storm Bow", "Damage: 15-28", "Requires 9 Marksmanship"]
    assert ordered[3:5] == [
        "Lengthens Bleeding duration on foes by 33%",
        "Halves skill recharge of spells (Chance: 20%)",
    ]
    assert ordered[-1] == "Value: 100 gold"


def test_sort_stats_lines_like_ingame_prioritizes_inscription_before_other_mods():
    lines = [
        "Longbow",
        "Damage: 15-28",
        "Requires 9 Marksmanship",
        "Damage +15% (while Health is above 50%)",
        "Inscription: \"Guided by Fate\"",
    ]

    ordered = sort_stats_lines_like_ingame(lines)

    assert ordered == [
        "Longbow",
        "Damage: 15-28",
        "Requires 9 Marksmanship",
        "Inscription: \"Guided by Fate\"",
        "Damage +15% (while Health is above 50%)",
    ]


def test_sort_stats_lines_like_ingame_shield_layout():
    lines = [
        "Value: 128 gold",
        "Health +30",
        "Inscription: \"To the Pain!\"",
        "Tower Shield",
        "Requires 9 Tactics",
        "Armor: 16 (vs Physical Damage +10)",
    ]

    ordered = sort_stats_lines_like_ingame(lines)

    assert ordered == [
        "Tower Shield",
        "Armor: 16 (vs Physical Damage +10)",
        "Requires 9 Tactics",
        "Inscription: \"To the Pain!\"",
        "Health +30",
        "Value: 128 gold",
    ]


def test_sort_stats_lines_like_ingame_caster_hct_before_hsr():
    lines = [
        "Value: 75 gold",
        "Halves skill recharge of spells (Chance: 20%)",
        "Requires 9 Divine Favor",
        "Holy Wand",
        "Halves casting time of spells (Chance: 20%)",
        "Damage: 11-22",
    ]

    ordered = sort_stats_lines_like_ingame(lines)

    assert ordered == [
        "Holy Wand",
        "Damage: 11-22",
        "Requires 9 Divine Favor",
        "Halves casting time of spells (Chance: 20%)",
        "Halves skill recharge of spells (Chance: 20%)",
        "Value: 75 gold",
    ]


def test_sort_stats_lines_like_ingame_caster_mod_order_energy_then_duration_then_health():
    lines = [
        "Inscribed Staff",
        "Requires 12 Domination Magic",
        "Damage: 11-22",
        "+30 Health",
        "Reduces Crippled duration on you by 20% (Stacking)",
        "Energy +10",
        "Halves skill recharge of spells (Chance: 20%)",
        "Value: 400 gold",
    ]

    ordered = sort_stats_lines_like_ingame(lines)

    assert ordered == [
        "Inscribed Staff",
        "Damage: 11-22",
        "Requires 12 Domination Magic",
        "Halves skill recharge of spells (Chance: 20%)",
        "Energy +10",
        "Reduces Crippled duration on you by 20% (Stacking)",
        "+30 Health",
        "Value: 400 gold",
    ]


def test_build_known_spellcasting_mod_lines_ignores_9880_metadata_marker():
    lines = build_known_spellcasting_mod_lines(
        raw_mods=[(9880, 0, 1), (25288, 10, 0)],
        item_attr_txt="",
        item_type=26,
        resolve_attribute_name_fn=lambda _attr_id: "",
    )

    assert "Energy +10" in lines
    assert "Reduces Crippled duration on you by 20% (Stacking)" not in lines


def test_build_known_spellcasting_mod_lines_renders_10328_duration_line():
    lines = build_known_spellcasting_mod_lines(
        raw_mods=[(10328, 3, 0)],
        item_attr_txt="",
        item_type=26,
        resolve_attribute_name_fn=lambda _attr_id: "",
    )

    assert "Reduces Crippled duration on you by 20%" in lines


def test_build_known_spellcasting_mod_lines_renders_10328_duration_line_when_condition_in_arg2():
    lines = build_known_spellcasting_mod_lines(
        raw_mods=[(10328, 0, 7)],
        item_attr_txt="",
        item_type=24,
        resolve_attribute_name_fn=lambda _attr_id: "",
    )

    assert "Reduces Dazed duration on you by 20%" in lines


def test_build_known_spellcasting_mod_lines_renders_10328_duration_line_when_condition_is_bitpacked():
    lines = build_known_spellcasting_mod_lines(
        raw_mods=[(10328, 0x107, 0)],
        item_attr_txt="",
        item_type=24,
        resolve_attribute_name_fn=lambda _attr_id: "",
    )

    assert "Reduces Dazed duration on you by 20%" in lines


def test_build_known_spellcasting_mod_lines_renders_10328_burning_condition():
    lines = build_known_spellcasting_mod_lines(
        raw_mods=[(10328, 2, 0)],
        item_attr_txt="",
        item_type=24,
        resolve_attribute_name_fn=lambda _attr_id: "",
    )

    assert "Reduces Burning duration on you by 20%" in lines


def test_build_known_spellcasting_mod_lines_renders_32784_requirement_line():
    lines = build_known_spellcasting_mod_lines(
        raw_mods=[(32784, 14, 9)],
        item_attr_txt="",
        item_type=27,
        resolve_attribute_name_fn=lambda attr_id: {14: "Divine Favor"}.get(attr_id, ""),
    )

    assert "Requires 9 Divine Favor" in lines


def test_build_known_spellcasting_mod_lines_renders_42290_inscription_marker():
    lines = build_known_spellcasting_mod_lines(
        raw_mods=[(42290, 0, 177)],
        item_attr_txt="",
        item_type=27,
        resolve_attribute_name_fn=lambda _attr_id: "",
    )

    assert "Inscription: 177" in lines


def test_normalize_identified_armor_name_strips_insignia_wrapper_but_keeps_prefix():
    assert normalize_identified_armor_name(
        "Titan Armor",
        "Hydromancer Insignia [Elementalist]",
        "Elementalist Rune of Superior Energy Storage",
        "",
    ) == "Hydromancer Titan Armor of Superior Energy Storage"


def test_normalize_identified_armor_name_keeps_existing_thematic_prefix():
    assert normalize_identified_armor_name(
        "Titan Armor",
        "Prodigy's",
        "Monk Rune of Superior Healing Prayers",
        "",
    ) == "Prodigy's Titan Armor of Superior Healing Prayers"


def test_normalize_identified_armor_name_returns_empty_for_non_armor_items():
    assert normalize_identified_armor_name(
        "Raven Staff",
        "Hale",
        "Channeling Magic",
        "",
    ) == ""


def test_build_spellcast_hct_hsr_lines_does_not_use_attribute_id_as_chance():
    lines = build_spellcast_hct_hsr_lines(
        raw_mods=[(9112, 30, 14)],
        item_attr_txt="Divine Favor",
        item_type=26,
        resolve_attribute_name_fn=lambda attr_id: {14: "Divine Favor"}.get(attr_id, ""),
    )

    assert lines == []


def test_build_spellcast_hct_hsr_lines_uses_swapped_attr_chance_layout_for_9112():
    lines = build_spellcast_hct_hsr_lines(
        raw_mods=[(9112, 4, 19)],
        item_attr_txt="Death Magic",
        item_type=26,
        resolve_attribute_name_fn=lambda attr_id: {4: "Death Magic", 19: "Hammer Mastery"}.get(attr_id, ""),
    )

    assert "Halves skill recharge of Death Magic spells (Chance: 19%)" in lines


def test_build_spellcast_hct_hsr_lines_uses_swapped_attr_chance_layout_for_9112_offhand_focus():
    lines = build_spellcast_hct_hsr_lines(
        raw_mods=[(9112, 11, 19)],
        item_attr_txt="Inspiration Magic",
        item_type=12,
        resolve_attribute_name_fn=lambda attr_id: {11: "Inspiration Magic", 19: "Hammer Mastery"}.get(attr_id, ""),
    )

    assert "Halves skill recharge of Inspiration Magic spells (Chance: 19%)" in lines


def test_build_spellcast_hct_hsr_lines_uses_swapped_attr_chance_layout_for_8728():
    lines = build_spellcast_hct_hsr_lines(
        raw_mods=[(8728, 4, 19)],
        item_attr_txt="Blood Magic",
        item_type=22,
        resolve_attribute_name_fn=lambda attr_id: {4: "Blood Magic", 19: "Hammer Mastery"}.get(attr_id, ""),
    )

    assert "Halves casting time of Blood Magic spells (Chance: 19%)" in lines


def test_build_known_spellcasting_mod_lines_uses_arg2_for_energy_value():
    lines = build_known_spellcasting_mod_lines(
        raw_mods=[(8920, 99, 5)],
        item_attr_txt="",
        item_type=26,
        resolve_attribute_name_fn=lambda _attr_id: "",
    )

    assert "Energy +5" in lines
    assert "Energy +99" not in lines


def test_build_known_spellcasting_mod_lines_uses_arg1_for_offhand_26568():
    lines = build_known_spellcasting_mod_lines(
        raw_mods=[(26568, 12, 6)],
        item_attr_txt="",
        item_type=12,
        resolve_attribute_name_fn=lambda _attr_id: "",
    )

    assert "Energy +12" in lines
    assert "Energy +6" not in lines


def test_build_known_spellcasting_mod_lines_doubles_arg2_for_offhand_26568_when_arg1_missing():
    lines = build_known_spellcasting_mod_lines(
        raw_mods=[(26568, 0, 6)],
        item_attr_txt="",
        item_type=12,
        resolve_attribute_name_fn=lambda _attr_id: "",
    )

    assert "Energy +12" in lines


def test_build_known_spellcasting_mod_lines_rejects_invalid_10296_chance():
    lines = build_known_spellcasting_mod_lines(
        raw_mods=[(10296, 50, 0)],
        item_attr_txt="Domination Magic",
        item_type=26,
        resolve_attribute_name_fn=lambda _attr_id: "",
    )

    assert "Domination Magic +1 (Chance: 50%)" not in lines
