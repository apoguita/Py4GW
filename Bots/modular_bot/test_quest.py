"""
Quest runner with GUI selection.

Select a quest from the Settings tab, then start the bot.
"""

import PyImGui

from Sources.modular_bot import ModularBot, Phase
from Sources.modular_bot.recipes import list_available_quests, quest_run
from Sources.modular_bot.hero_setup import draw_setup_tab


QUEST_NAMES = list_available_quests()
SELECTED_INDEX = 0


def _get_selected_quest() -> str:
    if not QUEST_NAMES:
        return "ruins_of_surmia"
    idx = max(0, min(SELECTED_INDEX, len(QUEST_NAMES) - 1))
    return QUEST_NAMES[idx]


def _draw_settings() -> None:
    draw_setup_tab()


def _draw_main() -> None:
    global SELECTED_INDEX

    if not QUEST_NAMES:
        PyImGui.text("No quest files found in Sources/modular_bot/quests")
    else:
        PyImGui.text("Select quest:")
        if PyImGui.begin_table("quest_select_table", 2, PyImGui.TableFlags.SizingStretchSame):
            for idx, quest_name in enumerate(QUEST_NAMES):
                PyImGui.table_next_column()
                label = f"{idx + 1:02d}. {quest_name.replace('_', ' ').title()}"
                if PyImGui.button(f"{label}##quest_{idx}"):
                    SELECTED_INDEX = idx
            PyImGui.end_table()
        PyImGui.text(f"Selected: {_get_selected_quest()}")
        PyImGui.text("Press Start to run selected quest.")


def _run_selected_quest(bot) -> None:
    quest_run(bot, _get_selected_quest())


def _main_dimensions() -> tuple[int, int]:
    rows = (len(QUEST_NAMES) + 1) // 2
    height = max(320, 240 + (rows * 28))
    return (612, min(int(height * 1.15), 900))


bot = ModularBot(
    name="Quest Runner",
    phases=[Phase("Run Selected Quest", _run_selected_quest, condition=lambda: True)],
    loop=False,
    template="aggressive",
    use_custom_behaviors=True,
    main_ui=_draw_main,
    main_child_dimensions=_main_dimensions(),
    settings_ui=_draw_settings,
)


def main():
    bot.update()
