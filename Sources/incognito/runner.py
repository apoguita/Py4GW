"""Mission queue orchestration: travel, difficulty, dispatch, retries."""

from __future__ import annotations

from Py4GWCoreLib import Botting
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import Map
from Py4GWCoreLib import Routines

from Sources.incognito.catalog import get_name
from Sources.incognito.config import get_config
from Sources.incognito.config import is_playable
from Sources.incognito.helpers import free_inventory_slots
from Sources.incognito.helpers import mission_succeeded
from Sources.incognito.missions import DISPATCH
from Sources.incognito.options import OPTIONS

MAX_ATTEMPTS = 20
MIN_FREE_SLOTS = 8

# Per-quest attempt counters (reset when the routine is rebuilt).
_attempt_counts: dict[int, int] = {}


def build_queue_routine(bot: Botting) -> None:
    """Build FSM steps for all currently selected playable missions."""
    global _attempt_counts
    _attempt_counts = {}

    selected = [qid for qid in OPTIONS.get_selected_quest_ids() if is_playable(qid)]
    if not selected:
        bot.States.AddHeader('No Missions Selected')

        def _warn():
            ConsoleLog('RMA', 'Select at least one playable mission (Phase 1), then Start.')
            yield

        bot.States.AddCustomState(_warn, 'No Selection')
        return

    bot.Templates.Aggressive()

    for quest_id in selected:
        _build_mission_entry(bot, quest_id)

    bot.States.AddHeader('Queue Complete')

    def _done():
        ConsoleLog('RMA', 'Mission queue finished.')
        OPTIONS.status_message = 'Queue finished'
        yield

    bot.States.AddCustomState(_done, 'All Done')


def _build_mission_entry(bot: Botting, quest_id: int) -> None:
    cfg = get_config(quest_id)
    builder = DISPATCH.get(quest_id)
    if cfg is None or builder is None:
        ConsoleLog('RMA', f'Unsupported mission {quest_id}; skipping.')
        return

    name = get_name(quest_id)
    retry_step = f'RMA_RETRY_{quest_id}'

    bot.States.AddHeader(f'Mission: {name}')

    def _inventory_guard():
        slots = free_inventory_slots()
        if slots < MIN_FREE_SLOTS:
            ConsoleLog('RMA', f'Fewer than {MIN_FREE_SLOTS} inventory slots free; stopping.')
            OPTIONS.status_message = 'Stopped: inventory full'
            bot.Stop()
            return
        yield

    bot.States.AddCustomState(_inventory_guard, f'{name} Inventory Check')

    # Jump target for retries — must be a stable custom-state name.
    def _begin_attempt(cfg=cfg, name=name, quest_id=quest_id):
        count = _attempt_counts.get(quest_id, 0) + 1
        _attempt_counts[quest_id] = count
        ConsoleLog('RMA', f'{name}: attempt {count}/{MAX_ATTEMPTS}')
        OPTIONS.status_message = f'{name} attempt {count}/{MAX_ATTEMPTS}'
        yield from Routines.Yield.wait(100)

    bot.States.AddCustomState(_begin_attempt, retry_step)

    bot.Map.Travel_To_Random_District(target_map_id=cfg.town_map)
    bot.Wait.UntilOnOutpost()
    bot.Party.SetHardMode(OPTIONS.hard_mode)
    bot.Wait.ForTime(500)

    builder(bot, cfg)

    def _after_attempt(cfg=cfg, name=name, quest_id=quest_id, retry_step=retry_step):
        yield from Routines.Yield.wait(1500)
        if mission_succeeded(cfg.completion_map, OPTIONS.hard_mode, ran_attempt=True):
            ConsoleLog('RMA', f'{name}: completed.')
            OPTIONS.status_message = f'{name}: completed'
            return

        count = _attempt_counts.get(quest_id, 1)
        if count >= MAX_ATTEMPTS:
            ConsoleLog('RMA', f'{name}: failed after {MAX_ATTEMPTS} attempts; continuing queue.')
            OPTIONS.status_message = f'{name}: failed'
            return

        ConsoleLog('RMA', f'{name}: incomplete — returning to town for retry.')
        OPTIONS.status_message = f'{name}: retrying'
        try:
            if Map.IsExplorable():
                from Py4GWCoreLib import Party

                Party.ReturnToOutpost()
                yield from Routines.Yield.wait(4000)
        except Exception:
            pass

        # Jump back to the stable retry step name.
        bot.config.FSM.pause()
        yield
        bot.config.FSM.jump_to_state_by_name(retry_step)
        yield
        bot.config.FSM.resume()
        yield

    bot.States.AddCustomState(_after_attempt, f'{name} After Attempt')
