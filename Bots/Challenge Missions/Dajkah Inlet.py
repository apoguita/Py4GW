from Py4GWCoreLib import Botting, Routines, ConsoleLog

# https://wiki.guildwars.com/wiki/Dajkah_Inlet
BOT_NAME = "Dajkah Inlet"
OUTPOST_IDS = [
    387,  # Sunspear Sanctuary
    554,  # Dajkah Inlet
]
MISSION_IDS = [
    554,  # Dajkah Inlet
]

Loop_Path: list[list[tuple[float, float]]] = [
    # Island 1 Path
    [
        (29886, -3956),
        (23201, -1309),
        (20885, 5177)  # Guild Lord 1
    ],

    # Island 2 Path
    [
        (-3148, -3768),  # Guild Lord 2
        (-2150, 2100),
        (3573, 3008),  # Guild Lord 3
        (-1347, 2901)
    ],

    # Island 3 Path
    [
        (-28293, -4577),  # Guild Lord 4
        (-27578, 3338),
        (-19851, 3862)  # Guild Lord 5
    ]
]

bot = Botting(BOT_NAME)


def bot_routine(bot: Botting) -> None:
    global Loop_Path
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Properties.Enable("halt_on_death")
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_IDS[1])
    bot.States.AddHeader("Start Mission")
    bot.Move.XYAndInteractNPC(-2902, -2636)
    bot.Multibox.SendDialogToTarget(0x87)  # Start Mission
    # bot.Wait.ForMapLoad(MISSION_IDS[0])  # Having the same Map ID causes wait issues
    bot.Wait.ForTime(60000)
    bot.States.AddHeader("Loop")
    loop_count = 0
    while loop_count < 2:  # Invulnerable Corsair Ghosts catch the bot if you go past 2 loops
        bot.Move.FollowAutoPath(Loop_Path[0])
        bot.Move.XY(17525, 4168, forced_timeout=5000)  # Portal 1
        bot.Wait.ForTime(1000)
        bot.Move.FollowAutoPath(Loop_Path[1])
        bot.Move.XY(-2150, 2100, forced_timeout=5000)  # Portal 2
        bot.Wait.ForTime(1000)
        bot.Move.FollowAutoPath(Loop_Path[2])
        bot.Move.XY(-31716, 2927, forced_timeout=5000)  # Portal 3
        bot.Wait.ForTime(1000)
        loop_count += 1
    bot.Wait.UntilOutOfCombat()
    bot.States.AddHeader("Restart")
    bot.Map.Travel(OUTPOST_IDS[0])
    bot.Map.Travel(OUTPOST_IDS[1])
    bot.States.JumpToStepName("[H]Start Mission_3")


def _on_party_wipe(bot: "Botting"):
    yield from Routines.Yield.wait(5000)
    fsm = bot.config.FSM
    fsm.jump_to_state_by_name("[H]Restart_5")
    fsm.resume()
    yield


def OnPartyWipe(bot: "Botting"):
    ConsoleLog("Wipe detected", "Party Wiped - Restarting...", message_type=6)
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))


bot.SetMainRoutine(bot_routine)


def main():
    bot.Update()
    bot.UI.draw_window()


if __name__ == "__main__":
    main()
