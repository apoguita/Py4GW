"""
Debug script for Verdant Cascades pathing crash.
Tests the first 4 waypoints repeatedly to reproduce the pathing cache bug.
"""

from Py4GWCoreLib import Botting

BOT_NAME = "Debug: Verdant Cascades Pathing"

UMBRAL_GROTTO_MAP_ID = 639
VERDANT_CASCADES_MAP_ID = 566

TEST_WAYPOINTS = [
    (-19887, 6074),
    (-10273, 3251),
]


def debug_routine(bot_instance: Botting):
    """
    Minimal debug routine to reproduce pathing crash.

    Flow:
    1. Travel to Umbral Grotto
    2. Exit to Verdant Cascades
    3. Path first 4 waypoints
    4. Resign party (returns to outpost)
    5. Loop back to step 2

    The crash should occur on the second iteration when pathing uses cached data.
    """

    # Disable combat and pause_on_danger to ensure continuous pathing
    bot_instance.Properties.Disable('pause_on_danger')
    bot_instance.Properties.Disable('auto_combat')

    # === MAIN LOOP ===
    bot_instance.States.AddHeader("TRAVEL_TO_OUTPOST")
    bot_instance.Map.Travel(target_map_id=UMBRAL_GROTTO_MAP_ID)

    # === EXIT TO VERDANT CASCADES ===
    bot_instance.States.AddHeader("EXIT_TO_VERDANT_CASCADES")
    bot_instance.Move.XY(-22735, 6339, "exit to Verdant Cascades")
    bot_instance.Wait.ForMapLoad(target_map_id=VERDANT_CASCADES_MAP_ID)
    bot_instance.Wait.ForTime(2_000)

    # === PATH TEST WAYPOINTS ===
    bot_instance.States.AddHeader("PATH_TEST_WAYPOINTS")
    for i, waypoint in enumerate(TEST_WAYPOINTS, 1):
        bot_instance.Move.XY(
            waypoint[0],
            waypoint[1],
            f"test waypoint {i}/{len(TEST_WAYPOINTS)}"
        )

    # === RESIGN AND RETURN ===
    bot_instance.States.AddHeader("RESIGN_AND_RETURN")
    bot_instance.Party.Resign()
    bot_instance.Wait.ForTime(5_000)
    bot_instance.Wait.UntilOnOutpost()

    # === LOOP BACK ===
    bot_instance.States.AddHeader("LOOP_BACK")
    bot_instance.States.JumpToStepName("[H]EXIT_TO_VERDANT_CASCADES_2")

    bot_instance.States.AddHeader("END")


# Initialize bot
bot = Botting(BOT_NAME)
bot.SetMainRoutine(debug_routine)


def main():
    """Main update loop."""
    bot.Update()
    bot.UI.draw_window()


if __name__ == "__main__":
    main()
