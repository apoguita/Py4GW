"""Run FoW quests one-by-one for testing."""

import os

import Py4GW
import PyImGui

from Sources.modular_bot import ModularBot, Phase
from Sources.modular_bot.hero_setup import draw_setup_tab
from Sources.modular_bot.recipes import quest_run


def _project_root() -> str:
    try:
        root = str(Py4GW.Console.get_projects_path() or "").strip()
    except Exception:
        root = ""
    if not root:
        root = os.getcwd()
    return os.path.normpath(root)


QUESTS_DIR = os.path.normpath(
    os.path.join(_project_root(), "Sources", "modular_bot", "quests", "FoW")
)


def _list_fow_quests() -> list[str]:
    if not os.path.isdir(QUESTS_DIR):
        return []

    names: list[str] = []
    for filename in os.listdir(QUESTS_DIR):
        if filename.lower().endswith(".json"):
            names.append(filename[:-5])

    return sorted(names)


QUEST_NAMES = _list_fow_quests()
SELECTED_INDEX = 0


def _selected_quest_key() -> str:
    if not QUEST_NAMES:
        return "FoW/defend_the_temple"

    idx = max(0, min(SELECTED_INDEX, len(QUEST_NAMES) - 1))
    return f"FoW/{QUEST_NAMES[idx]}"


def _selected_display_name() -> str:
    return _selected_quest_key().split("/", 1)[1]


def _draw_main() -> None:
    global SELECTED_INDEX

    PyImGui.text("FoW Quest Tester")
    PyImGui.separator()

    if not QUEST_NAMES:
        PyImGui.text("No FoW quest files found in Sources/modular_bot/quests/FoW")
        return

    if PyImGui.begin_table("fow_quest_select_table", 2, PyImGui.TableFlags.SizingStretchSame):
        for idx, quest_name in enumerate(QUEST_NAMES):
            PyImGui.table_next_column()
            label = f"{idx + 1:02d}. {quest_name.replace('_', ' ').title()}"
            if PyImGui.button(f"{label}##fow_quest_{idx}"):
                SELECTED_INDEX = idx
        PyImGui.end_table()

    PyImGui.separator()
    PyImGui.text(f"Selected: {_selected_display_name()}")
    PyImGui.text("Press Start to run the selected FoW quest.")


def _draw_settings() -> None:
    draw_setup_tab()


def _run_selected_quest(bot) -> None:
    quest_run(bot, _selected_quest_key())


def _main_dimensions() -> tuple[int, int]:
    rows = (len(QUEST_NAMES) + 1) // 2
    height = max(320, 240 + (rows * 28))
    return (612, min(int(height * 1.15), 900))


def _resolve_engine_runtime() -> tuple[bool, bool]:
    try:
        from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler

        handler = get_widget_handler()
        cb_enabled = bool(handler.is_widget_enabled("CustomBehaviors"))
        hero_ai_enabled = bool(handler.is_widget_enabled("HeroAI"))
        return cb_enabled, hero_ai_enabled
    except Exception:
        return (False, False)


_CB_ENABLED, _HERO_AI_ENABLED = _resolve_engine_runtime()

bot = ModularBot(
    name="FoW Quest Tester",
    phases=[Phase("Run Selected FoW Quest", _run_selected_quest, condition=lambda: True)],
    loop=False,
    template="multibox_aggressive" if _HERO_AI_ENABLED else "aggressive",
    use_custom_behaviors=bool(_CB_ENABLED and not _HERO_AI_ENABLED),
    upkeep_hero_ai_active=bool(_HERO_AI_ENABLED),
    main_ui=_draw_main,
    main_child_dimensions=_main_dimensions(),
    settings_ui=_draw_settings,
)


def main():
    bot.update()
