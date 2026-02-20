"""
Mission runner with GUI selection.

Select a mission from the Settings tab, then start the bot.
"""

import PyImGui

from Sources.modular_bot import ModularBot, Phase
from Sources.modular_bot.recipes import list_available_missions, mission_run


MISSION_NAMES = list_available_missions()
MISSION_LABELS = [name.replace("_", " ").title() for name in MISSION_NAMES]
SELECTED_INDEX = 0


def _get_selected_mission() -> str:
    if not MISSION_NAMES:
        return "the_great_northern_wall"
    idx = max(0, min(SELECTED_INDEX, len(MISSION_NAMES) - 1))
    return MISSION_NAMES[idx]


def _draw_settings() -> None:
    global SELECTED_INDEX

    if not MISSION_NAMES:
        PyImGui.text("No mission files found in Sources/modular_bot/missions")
        return

    SELECTED_INDEX = PyImGui.combo("Mission", SELECTED_INDEX, MISSION_LABELS)
    PyImGui.text(f"Selected: {_get_selected_mission()}")
    PyImGui.text("Selection is applied on next Start.")


def _run_selected_mission(bot) -> None:
    mission_run(bot, _get_selected_mission())


bot = ModularBot(
    name="Mission Runner",
    phases=[Phase("Run Selected Mission", _run_selected_mission, condition=lambda: True)],
    loop=False,
    template="aggressive",
    use_custom_behaviors=True,
    settings_ui=_draw_settings,
)


def main():
    bot.update()
