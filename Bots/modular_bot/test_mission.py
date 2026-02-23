"""
Mission runner with GUI selection.

Select a mission from the Settings tab, then start the bot.
"""

import PyImGui

from Sources.modular_bot import ModularBot, Phase
from Sources.modular_bot.recipes import list_available_missions, mission_run
from Sources.modular_bot.hero_setup import draw_setup_tab


MISSION_NAMES = list_available_missions()
SELECTED_INDEX = 0


def _get_selected_mission() -> str:
    if not MISSION_NAMES:
        return "the_great_northern_wall"
    idx = max(0, min(SELECTED_INDEX, len(MISSION_NAMES) - 1))
    return MISSION_NAMES[idx]


def _draw_settings() -> None:
    draw_setup_tab()


def _draw_main() -> None:
    global SELECTED_INDEX

    if not MISSION_NAMES:
        PyImGui.text("No mission files found in Sources/modular_bot/missions")
    else:
        PyImGui.text("Select mission:")
        if PyImGui.begin_table("mission_select_table", 2, PyImGui.TableFlags.SizingStretchSame):
            for idx, mission_name in enumerate(MISSION_NAMES):
                PyImGui.table_next_column()
                label = f"{idx + 1:02d}. {mission_name.replace('_', ' ').title()}"
                if PyImGui.button(f"{label}##mission_{idx}"):
                    SELECTED_INDEX = idx
            PyImGui.end_table()
        PyImGui.text(f"Selected: {_get_selected_mission()}")
        PyImGui.text("Press Start to run selected mission.")


def _run_selected_mission(bot) -> None:
    mission_run(bot, _get_selected_mission())


def _main_dimensions() -> tuple[int, int]:
    rows = (len(MISSION_NAMES) + 1) // 2
    height = max(320, 240 + (rows * 28))
    return (612, min(int(height * 1.15), 900))


bot = ModularBot(
    name="Mission Runner",
    phases=[Phase("Run Selected Mission", _run_selected_mission, condition=lambda: True)],
    loop=False,
    template="aggressive",
    use_custom_behaviors=True,
    main_ui=_draw_main,
    main_child_dimensions=_main_dimensions(),
    settings_ui=_draw_settings,
)


def main():
    bot.update()
