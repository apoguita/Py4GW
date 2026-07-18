"""
Reforged Mission Assistant — Py4GW port of the GwAu3 title/mission farmer.

Select missions in the Missions tab, then press Start on the Main tab.
Phase 1 playable missions: Great Northern Wall, Fort Ranik, Chahbek Village.
"""

from __future__ import annotations

from Py4GWCoreLib import Botting

from Sources.incognito import ui as rma_ui
from Sources.incognito.options import OPTIONS
from Sources.incognito.runner import build_queue_routine

MODULE_NAME = 'Reforged Mission Assistant'
MODULE_ICON = ''

bot = Botting(
    MODULE_NAME,
    upkeep_hero_ai_active=True,
    upkeep_auto_loot_active=True,
)

_last_build_key: tuple | None = None


def create_bot_routine(botting: Botting) -> None:
    build_queue_routine(botting)


bot.SetMainRoutine(create_bot_routine)


def _rebuild_if_selection_changed() -> None:
    """Rebuild FSM when idle and the user changes selection/options."""
    global _last_build_key
    key = OPTIONS.selection_key()
    if bot.config.fsm_running:
        return
    if _last_build_key is None:
        _last_build_key = key
        return
    if key == _last_build_key:
        return
    _last_build_key = key
    try:
        bot.config.FSM.states.clear()
    except Exception:
        pass
    bot.config.initialized = False


def main() -> None:
    _rebuild_if_selection_changed()
    bot.Update()
    bot.UI.draw_window(
        main_child_dimensions=(380, 320),
        additional_ui=rma_ui.draw_main_summary,
        extra_tabs=[('Missions', rma_ui.draw_missions_tab)],
    )


if __name__ == '__main__':
    main()
