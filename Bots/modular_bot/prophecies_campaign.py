"""Prophecies campaign chain (missions + primary quests)."""

import os
import re
import Py4GW
import PyImGui

from Sources.modular_bot import ModularBot
from Sources.modular_bot.recipes import Mission, Quest
from Sources.modular_bot.hero_setup import draw_setup_tab


def _project_root() -> str:
    try:
        root = str(Py4GW.Console.get_projects_path() or "").strip()
    except Exception:
        root = ""
    if not root:
        root = os.getcwd()
    return os.path.normpath(root)


CAMPAIGN_SEQUENCE = [
    ("mission", "the_great_northern_wall", "1. The Great Northern Wall"),
    ("mission", "fort_ranik", "2. Fort Ranik"),
    ("mission", "ruins_of_surmia", "3. Ruins of Surmia"),
    ("mission", "nolani_academy", "4. Nolani Academy"),
    ("quest", "the_way_is_blocked", "The Way Is Blocked"),
    ("mission", "borlis_pass", "5. Borlis Pass"),
    ("mission", "the_frost_gate", "6. The Frost Gate"),
    ("quest", "to_kryta_refugees", "To Kryta: Refugees"),
    ("quest", "to_kryta_the_ice_cave", "To Kryta: The Ice Cave"),
    ("quest", "to_kryta_the_journey_end", "To Kryta: Journey's End"),
    ("mission", "gates_of_kryta", "7. Gates of Kryta"),
    ("quest", "report_to_the_white_mantle", "Report to the White Mantle"),
    ("mission", "d_alessio_seaboard", "8. D'Alessio Seaboard"),
    ("mission", "divinity_coast", "9. Divinity Coast"),
    ("quest", "a_brothers_fury", "A Brother's Fury"),
    ("mission", "the_wilds", "10. The Wilds"),
    ("mission", "bloodstone_fen", "11. Bloodstone Fen"),
    ("quest", "white_mantle_wrath_demagogue_vanguard", "White Mantle Wrath: Demagogue's Vanguard"),
    ("quest", "urgent_warning", "Urgent Warning"),
    ("mission", "aurora_glade", "12. Aurora Glade"),
    ("quest", "passage_through_the_dark_river", "Passage Through The Dark River"),
    ("mission", "riverside_province", "13. Riverside Province"),
    ("mission", "sanctum_cay", "14. Sanctum Cay"),
]

START_INDEX = 0
GROUPS = [
    ("Ascalon", 0, 3),
    ("Northern Shiverpeaks", 4, 6),
    ("Kryta", 7, 13),
    ("Maguuma Jungle", 14, 20),
    ("Kryta extended", 21, 22),
]
SHOW_ALL_GROUPS = False


def _data_path(kind: str, name: str) -> str:
    root_dir = _project_root()
    if kind == "mission":
        return os.path.join(root_dir, "Sources", "modular_bot", "missions", f"{name}.json")
    return os.path.join(root_dir, "Sources", "modular_bot", "quests", f"{name}.json")


def _build_phases():
    phases = []
    for idx, (kind, key, label) in enumerate(CAMPAIGN_SEQUENCE):
        phase = Mission(key, label) if kind == "mission" else Quest(key, label)
        # Skip phases before selected start point.
        phase.condition = (lambda _i=idx: _i >= START_INDEX)
        phases.append(phase)
    return phases


PHASES = _build_phases()


def _clean_label(label: str) -> str:
    # Remove leading "N. " prefix from labels for cleaner UI output.
    return re.sub(r"^\s*\d+\.\s*", "", label).strip()


def _draw_main() -> None:
    global START_INDEX, SHOW_ALL_GROUPS

    PyImGui.text("Prophecies Phases")
    PyImGui.text(f"Total phases: {len(CAMPAIGN_SEQUENCE)}")
    PyImGui.text("Click a checkbox to set start point.")
    SHOW_ALL_GROUPS = PyImGui.checkbox("Show all regions", SHOW_ALL_GROUPS)

    for group_name, group_start, group_end in GROUPS:
        open_group = SHOW_ALL_GROUPS or PyImGui.collapsing_header(group_name)
        if not open_group:
            continue

        for idx in range(group_start, group_end + 1):
            kind, _key, label = CAMPAIGN_SEQUENCE[idx]
            checked = idx >= START_INDEX
            changed = PyImGui.checkbox(f"##phase_start_{idx}", checked)
            PyImGui.same_line(0, -1)
            PyImGui.text(f"{idx + 1:02d}. {kind}: {_clean_label(label)}")
            if changed != checked:
                START_INDEX = idx

    kind, _key, label = CAMPAIGN_SEQUENCE[START_INDEX]
    PyImGui.separator()
    PyImGui.text(f"Start from: {START_INDEX + 1:02d}. {kind}: {_clean_label(label)}")


def _draw_settings() -> None:
    draw_setup_tab()


def _main_dimensions() -> tuple[int, int]:
    # One row per phase plus header lines.
    height = max(520, 220 + (len(PHASES) * 28))
    return (700, min(height, 980))


bot = ModularBot(
    name="Prophecies Campaign",
    phases=PHASES,
    loop=False,
    template="aggressive",
    use_custom_behaviors=True,
    main_ui=_draw_main,
    icon_path=os.path.join(_project_root(), "Bots", "modular_bot", "assets", "prophecies.jpg"),
    main_child_dimensions=_main_dimensions(),
    settings_ui=_draw_settings,
)


def main():
    bot.update()
