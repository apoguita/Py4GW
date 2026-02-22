from Sources.oazix.CustomBehaviors.skills.monitoring.item_mod_render_utils import sort_stats_lines_like_ingame


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
