from Sources.oazix.CustomBehaviors.skills.monitoring.item_mod_render_utils import (
    build_known_spellcasting_mod_lines,
    build_spellcast_hct_hsr_lines,
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


def test_build_spellcast_hct_hsr_lines_does_not_use_attribute_id_as_chance():
    lines = build_spellcast_hct_hsr_lines(
        raw_mods=[(9112, 30, 14)],
        item_attr_txt="Divine Favor",
        item_type=26,
        resolve_attribute_name_fn=lambda attr_id: {14: "Divine Favor"}.get(attr_id, ""),
    )

    assert lines == []


def test_build_known_spellcasting_mod_lines_uses_arg2_for_energy_value():
    lines = build_known_spellcasting_mod_lines(
        raw_mods=[(8920, 99, 5)],
        item_attr_txt="",
        item_type=26,
        resolve_attribute_name_fn=lambda _attr_id: "",
    )

    assert "Energy +5" in lines
    assert "Energy +99" not in lines


def test_build_known_spellcasting_mod_lines_rejects_invalid_10296_chance():
    lines = build_known_spellcasting_mod_lines(
        raw_mods=[(10296, 50, 0)],
        item_attr_txt="Domination Magic",
        item_type=26,
        resolve_attribute_name_fn=lambda _attr_id: "",
    )

    assert "Domination Magic +1 (Chance: 50%)" not in lines
