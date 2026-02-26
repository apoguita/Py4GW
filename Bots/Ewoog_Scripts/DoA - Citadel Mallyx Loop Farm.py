from __future__ import annotations

import time
from typing import Generator

import Py4GW
from Py4GWCoreLib import Botting, Player, Routines, Range, Map


MODULE_NAME = "DoA - Citadel Mallyx Loop Farm"

# Maps
GATE_OF_ANGUISH = 474
EBONY_CITADEL_OF_MALLYX = 445

# NPC / positions (taken from proven GWA2 route)
OUTPOST_START_NPC_X = 6081.0
OUTPOST_START_NPC_Y = -13314.0
START_DIALOG_ID = 0x84

CITADEL_DEFEND_X = -3345.0
CITADEL_DEFEND_Y = -5217.0

# Wave complete detection / run complete detection
COMPASS_RANGE = 0.5*Range.Compass.value
NO_SPAWN_TIMEOUT_SECONDS = 60.0
REPOSITION_INTERVAL_SECONDS = 4.0


bot = Botting(
    MODULE_NAME,
    config_log_actions=False,
    upkeep_auto_combat_active=True,
    upkeep_auto_loot_active=False,
    upkeep_hero_ai_active=False,
)


def _count_enemies_in_compass() -> int:
    pos = Player.GetXY()
    if not pos:
        return 0
    enemy_array = Routines.Agents.GetFilteredEnemyArray(pos[0], pos[1], COMPASS_RANGE)
    return len(enemy_array)


def _wait_for_wave_logic() -> Generator:
    """
    Stay in the citadel and keep pulling the team back to Zhellix's spot.

    Rules:
    - Each wave is considered complete when no enemies are in compass range.
    - The full run is complete after 60 seconds with no enemies spawning in compass range.
    """
    last_enemy_seen = time.monotonic()
    last_reposition = 0.0

    while True:
        if not Routines.Checks.Map.MapValid() or Map.IsOutpost():
            return

        enemy_count = _count_enemies_in_compass()
        now = time.monotonic()

        if enemy_count > 0:
            last_enemy_seen = now
        else:
            if now - last_reposition >= REPOSITION_INTERVAL_SECONDS:
                yield from bot.Move._coro_xy(CITADEL_DEFEND_X, CITADEL_DEFEND_Y)
                last_reposition = now

            if now - last_enemy_seen >= NO_SPAWN_TIMEOUT_SECONDS:
                Py4GW.Console.Log(
                    MODULE_NAME,
                    "No enemies in compass range for 60 seconds. Run complete.",
                    Py4GW.Console.MessageType.Info,
                )
                return

        yield from bot.Wait._coro_for_time(800)


def _loop_runs() -> Generator:
    while True:
        Py4GW.Console.Log(MODULE_NAME, "Starting new run.", Py4GW.Console.MessageType.Info)

        # 1) Ensure outpost and start the run dialog from Gate of Anguish
        yield from bot.Map._coro_travel(target_map_id=GATE_OF_ANGUISH)
        yield from bot.Move._coro_xy_and_dialog(OUTPOST_START_NPC_X, OUTPOST_START_NPC_Y, START_DIALOG_ID)
        yield from bot.Wait._coro_for_map_load(target_map_id=EBONY_CITADEL_OF_MALLYX)

        # 2) In citadel: walk next to NPC position to trigger/start and between waves
        yield from bot.Move._coro_xy(CITADEL_DEFEND_X, CITADEL_DEFEND_Y)

        # 3) Hold position, detect wave transitions, finish when no spawn for 60s
        yield from _wait_for_wave_logic()

        # 4) End run: resign all multibox accounts and wait return to outpost
        bot.Multibox.ResignParty()
        yield from bot.Wait._coro_for_map_load(target_map_id=GATE_OF_ANGUISH)
        yield from bot.Wait._coro_for_time(1500)


def create_bot_routine(bot_instance: Botting) -> None:
    # Use custom behavior framework (HeroAI must remain disabled for compatibility)
    bot_instance.Templates.Aggressive(
        pause_on_danger=True,
        halt_on_death=False,
        movement_timeout=-1,
        auto_combat=True,
        auto_loot=False,
        enable_imp=False,
    )
    bot_instance.Properties.Disable("hero_ai")
    bot_instance.Templates.Routines.UseCustomBehaviors(map_id_to_travel=GATE_OF_ANGUISH)

    bot_instance.States.AddHeader("Citadel of Mallyx - Loop Farm")
    bot_instance.States.AddCustomState(lambda: _loop_runs(), name="MainLoop")


bot.SetMainRoutine(create_bot_routine)


def main():
    bot.Update()
    bot.UI.draw_window()


if __name__ == "__main__":
    main()
