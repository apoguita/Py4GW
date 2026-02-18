"""
Quest runner with GUI selection.

Select a quest from the Settings tab, then start the bot.
"""

import PyImGui

from Sources.modular_bot import ModularBot, Phase
from Sources.modular_bot.recipes import list_available_quests, quest_run


QUEST_NAMES = list_available_quests()
QUEST_LABELS = [name.replace("_", " ").title() for name in QUEST_NAMES]
SELECTED_INDEX = 0


def _get_selected_quest() -> str:
    if not QUEST_NAMES:
        return "ruins_of_surmia"
    idx = max(0, min(SELECTED_INDEX, len(QUEST_NAMES) - 1))
    return QUEST_NAMES[idx]


def _draw_settings() -> None:
    global SELECTED_INDEX

    if not QUEST_NAMES:
        PyImGui.text("No quest files found in Sources/modular_bot/quests")
        return

    SELECTED_INDEX = PyImGui.combo("Quest", SELECTED_INDEX, QUEST_LABELS)
    PyImGui.text(f"Selected: {_get_selected_quest()}")
    PyImGui.text("Selection is applied on next Start.")


def _run_selected_quest(bot) -> None:
    quest_run(bot, _get_selected_quest())


bot = ModularBot(
    name="Quest Runner",
    phases=[Phase("Run Selected Quest", _run_selected_quest, condition=lambda: True)],
    loop=False,
    template="aggressive",
    use_custom_behaviors=True,
    settings_ui=_draw_settings,
)


def main():
    bot.update()
