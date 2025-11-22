from Py4GWCoreLib import Botting, Routines, ConsoleLog

# https://wiki.guildwars.com/wiki/The_Shadow_Nexus
BOT_NAME = "The Shadow Nexus"
OUTPOST_IDS = [
    450,  # Gate of Torment
    555,  # The Shadow Nexus
]
MISSION_IDS = [
    555,  # The Shadow Nexus
]

Loop_Path: list[tuple[float, float]] = [
    (4479, 2496),  # Portal 1
    (36, 3428),  # Portal 2
    (-3145, 3648),  # Portal 3
    (-4626, 1563),  # Portal 4
    (-1938, 1014),  # Portal 5
    (-4132, -3867),  # Portal 6
    (530, -3812),  # Portal 7
    (1321, -987),  # Portal 8
    # (2340, -2660),  # Portal 9
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
    bot.Move.XYAndInteractNPC(-2237, -4961)
    bot.Multibox.SendDialogToTarget(0x88)  # Start Mission
    # bot.Wait.ForMapLoad(MISSION_IDS[0]) # Having the same Map ID causes wait issues
    bot.Wait.ForTime(50000)
    bot.States.AddHeader("Loop")
    loop_count = 0
    while loop_count < 10:
        bot.Move.FollowAutoPath(Loop_Path)
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
