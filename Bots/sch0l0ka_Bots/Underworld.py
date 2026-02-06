from Py4GWCoreLib import Botting, Routines, Agent, AgentArray, Player, Utils, AutoPathing, GLOBAL_CACHE, ConsoleLog, Map, Pathing, FlagPreference
from Sources.oazix.CustomBehaviors.primitives.botting.botting_helpers import BottingHelpers
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
import PyImGui
import Py4GW



# Override the help window
BOT_NAME = "Underworld Helper"
bot = Botting(BOT_NAME, config_draw_path=True)
# Override the help window
bot.UI.override_draw_help(lambda: _draw_help())
bot.UI.override_draw_config(lambda: _draw_settings())  # Disable default config window
MAIN_LOOP_HEADER_NAME = ""

class BotSettings:
    RestoreVale: bool = True
    WrathfullSpirits: bool = True
    EscortOfSouls: bool = True
    RestoreWastes: bool = True
    ServantsOfGrenth: bool = True
    PassTheMountains: bool = True
    RestoreMountains: bool = True
    DeamonAssassin: bool = True
    RestorePlanes: bool = True
    TheFourHorsemen: bool = True
    RestorePools: bool = True
    TerrorwebQueen: bool = True
    RestorePit: bool = True
    ImprisonedSpirits: bool = True
    DEBUG: bool = False


def _enqueue_section(bot_instance: Botting, attr_name: str, label: str, section_fn):
    def _queue_section():
        if getattr(BotSettings, attr_name, False):
            section_fn(bot_instance)
    bot_instance.States.AddCustomState(_queue_section, f"[Toggle] {label}")

def _add_header_with_name(bot_instance: Botting, step_name: str) -> str:
    header_name = f"[H]{step_name}_{bot_instance.config.get_counter('HEADER_COUNTER')}"
    bot_instance.config.FSM.AddYieldRoutineStep(
        name=header_name,
        coroutine_fn=lambda: Routines.Yield.wait(100),
    )
    return header_name

def _restart_main_loop(bot_instance: Botting, reason: str) -> None:
    target = MAIN_LOOP_HEADER_NAME
    fsm = bot_instance.config.FSM
    fsm.pause()
    try:
        if target:
            fsm.jump_to_state_by_name(target)
            ConsoleLog(BOT_NAME, f"[WIPE] {reason} – restarting at {target}.", Py4GW.Console.MessageType.Info)
        else:
            ConsoleLog(BOT_NAME, "[WIPE] MAIN_LOOP header missing, restarting from first state.", Py4GW.Console.MessageType.Warning)
            fsm.jump_to_state_by_step_number(0)
    except ValueError:
        ConsoleLog(BOT_NAME, f"[WIPE] Header '{target}' not found, restarting from first state.", Py4GW.Console.MessageType.Error)
        fsm.jump_to_state_by_step_number(0)
    finally:
        fsm.resume()

def bot_routine(bot: Botting):

    global MAIN_LOOP_HEADER_NAME
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    CustomBehaviorParty().set_party_is_blessing_enabled(True)

    bot.Templates.Routines.UseCustomBehaviors(
    on_player_critical_death=BottingHelpers.botting_unrecoverable_issue,
    on_party_death=BottingHelpers.botting_unrecoverable_issue,
    on_player_critical_stuck=BottingHelpers.botting_unrecoverable_issue)

    bot.Templates.Aggressive()


    # Set up the FSM states properly
    MAIN_LOOP_HEADER_NAME = _add_header_with_name(bot, "MAIN_LOOP")

    bot.Map.Travel(target_map_id=138)
    bot.Party.SetHardMode(False)

    Enter_UW(bot)
    Clear_the_Chamber(bot)
    _enqueue_section(bot, "RestoreVale", "Restore Vale", Restore_Vale)
    _enqueue_section(bot, "WrathfullSpirits", "Wrathfull Spirits", Wrathfull_Spirits)
    _enqueue_section(bot, "EscortOfSouls", "Escort of Souls", Escort_of_Souls)
    _enqueue_section(bot, "RestoreWastes", "Restore Wastes", Restore_Wastes)
    _enqueue_section(bot, "ServantsOfGrenth", "Servants of Grenth", Servants_of_Grenth)
    _enqueue_section(bot, "PassTheMountains", "Pass the Mountains", Pass_The_Mountains)
    _enqueue_section(bot, "RestoreMountains", "Restore Mountains", Restore_Mountains)
    _enqueue_section(bot, "DeamonAssassin", "Deamon Assassin", Deamon_Assassin)
    _enqueue_section(bot, "RestorePlanes", "Restore Planes", Restore_Planes)
    _enqueue_section(bot, "TheFourHorsemen", "The Four Horsemen", The_Four_Horsemen)
    _enqueue_section(bot, "RestorePools", "Restore Pools", Restore_Pools)
    _enqueue_section(bot, "TerrorwebQueen", "Terrorweb Queen", Terrorweb_Queen)
    _enqueue_section(bot, "RestorePit", "Restore Pit", Restore_Pit)
    _enqueue_section(bot, "ImprisonedSpirits", "Imprisoned Spirits", Imprisoned_Spirits)

    bot.States.AddHeader("END")

def Enter_UW(bot_instance: Botting):
    bot_instance.States.AddHeader("Enter Underworld")
    CustomBehaviorParty().set_party_leader_email(Player.GetAccountEmail())
    bot_instance.Move.XY(-4199, 19845, "go to Statue")
    bot_instance.States.AddCustomState(lambda: Player.SendChatCommand("kneel"), "kneel")
    bot_instance.Wait.ForTime(3000)
    bot_instance.Dialogs.AtXY(-4199, 19845, 0x85, "ask to enter")
    bot_instance.Dialogs.AtXY(-4199, 19845, 0x86, "accept to enter")
    bot_instance.Wait.ForMapLoad(target_map_id=72) # we are in the dungeon
    bot.Properties.ApplyNow("pause_on_danger", "active", True)

def Clear_the_Chamber(bot_instance: Botting):
    bot_instance.States.AddHeader("Clear the Chamber")
    CustomBehaviorParty().set_party_leader_email(Player.GetAccountEmail())

    bot_instance.Wait.ForTime(30000)
    bot_instance.Move.XYAndInteractNPC(295, 7221, "go to NPC")
    bot_instance.Dialogs.AtXY(295, 7221, 0x806501, "take quest")
    bot_instance.Move.XY(-1505, 6352, "Left")
    bot_instance.Move.XY(-755, 8982, "Mid")
    bot_instance.Move.XY(1259, 10214, "Right")
    bot_instance.Move.XY(-3729, 13414, "Right")

    bot_instance.Move.XY(-5855, 11202, "Clear the Room")
    #bot_instance.Move.XY(5755, 12769, "Clear the Room")
    bot_instance.Wait.ForTime(3000)
    bot_instance.Move.XYAndInteractNPC(-5806, 12831, "go to NPC")
    bot_instance.Wait.ForTime(3000)
    bot_instance.Dialogs.AtXY(-5806, 12831, 0x806507, "take quest")
    bot_instance.Dialogs.AtXY(-5806, 12831, 0x806D03, "take quest")
    bot_instance.Dialogs.AtXY(-5806, 12831, 0x806D01, "take quest")
    bot_instance.Wait.ForTime(3000)

def Restore_Vale(bot_instance: Botting):
    if BotSettings.RestoreVale:
        bot_instance.States.AddHeader("Restore Vale")
        bot_instance.Move.XY(-8660, 5655, "To the Vale")
        bot_instance.Wait.ForTime(5000)
        bot_instance.Move.XY(-9431, 1659, "To the Vale")
        bot_instance.Move.XY(-11123, 2531, "To the Vale")
        bot_instance.Move.XY(-10212, 251 , "To the Vale")
        bot_instance.Move.XY(-13085, 849 , "To the Vale")
        bot_instance.Move.XY(-15274, 1432 , "To the Vale")
        bot_instance.Move.XY(-13246, 5110 , "To the Vale")
        bot_instance.Move.XYAndInteractNPC(-13275, 5261, "go to NPC")
        #bot_instance.Dialogs.AtXY(5755, 12769, 0x7F, "Back to Chamber")
        #bot_instance.Dialogs.AtXY(5755, 12769, 0x86, "Back to Chamber")
        #bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "Back to Chamber")
        bot_instance.Wait.ForTime(3000)

def Wrathfull_Spirits(bot_instance: Botting):
    if BotSettings.WrathfullSpirits:
        bot_instance.States.AddHeader("Wrathfull_Spirits")
        bot_instance.Move.XYAndInteractNPC(-13275, 5261, "go to NPC")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x806E03, "Back to Chamber")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x806E01, "Back to Chamber")
        bot_instance.Templates.Pacifist()
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_combat_enabled(False), "Disable Combat")
        bot_instance.Move.XY(-13422, 973, "To the Vale")
        bot_instance.Templates.Aggressive()
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_combat_enabled(True), "Enable Combat") 
        bot_instance.Move.XY(-10207, 1746, "To the Vale")
        bot_instance.Move.XY(-13287, 1996, "To the Vale")
        bot_instance.Move.XY(-15226, 4129 , "To the Vale")
        bot_instance.Move.XYAndInteractNPC(-13275, 5261, "go to NPC")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x7F, "Back to Chamber")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x86, "Back to Chamber")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "Back to Chamber")
        bot_instance.Wait.ForTime(3000)

def Escort_of_Souls(bot_instance: Botting):
    if BotSettings.EscortOfSouls:
        bot_instance.States.AddHeader("Escord of Souls")
        bot_instance.Wait.ForTime(5000)
        bot_instance.Move.XY(-4764, 11845, "To the Vale")
        bot_instance.Move.XYAndInteractNPC(-5806, 12831, "go to NPC")
        bot_instance.Wait.ForTime(3000)
        bot_instance.Dialogs.AtXY(-5806, 12831, 0x806C03, "take quest")
        bot_instance.Dialogs.AtXY(-5806, 12831, 0x806C01, "take quest")
        bot_instance.Move.XY(-6833, 7077, "To the Vale")
        bot_instance.Move.XY(-9606, 2110, "To the Vale")
        bot_instance.Move.XYAndInteractNPC(-13275, 5261, "go to NPC")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x7F, "Back to Chamber")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x86, "Back to Chamber")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "Back to Chamber")
        bot_instance.Wait.ForTime(3000)

def Restore_Wastes(bot_instance: Botting):
    if BotSettings.RestoreWastes:
        bot.Templates.Aggressive()
        bot.Properties.ApplyNow("pause_on_danger", "active", True)
        bot_instance.States.AddHeader("Restore Wastes")
        bot_instance.Move.XY(3891, 7572, "To the Vale")
        bot_instance.Move.XY(4106, 16031, "To the Vale")
        bot_instance.Move.XY(2486, 21723, "To the Vale")
        bot_instance.Move.XY(-1452, 21202, "To the Vale")
        bot_instance.Move.XY(542, 18310, "To the Vale")
        bot_instance.Move.XYAndInteractNPC(554, 18384, "go to NPC")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x7F, "Back to Chamber")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x86, "Back to Chamber")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "Back to Chamber")
        bot_instance.Wait.ForTime(3000)

def Servants_of_Grenth(bot_instance: Botting):
    if BotSettings.ServantsOfGrenth:
        bot.Templates.Aggressive()
        bot_instance.States.AddHeader("Servants of Grenth")
        bot_instance.Move.XY(2700, 19952, "To the Vale")
        bot_instance.Wait.ForTime(10000)
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(False), "Disable Following")
        bot_instance.Move.XYAndInteractNPC(554, 18384, "go to NPC")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x806603, "Back to Chamber")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x806601, "Back to Chamber")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(True), "Enable Following")
        bot_instance.Move.XY(2700, 19952, "To the Vale")
        bot_instance.Wait.ForTime(100000)
        bot_instance.Move.XYAndInteractNPC(554, 18384, "go to NPC")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x7F, "Back to Chamber")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x86, "Back to Chamber")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "Back to Chamber")
        bot_instance.Wait.ForTime(3000)

def Pass_The_Mountains(bot_instance: Botting):
    if BotSettings.PassTheMountains:
        bot_instance.States.AddHeader("Pass the Mountains")
        bot_instance.Move.XY(-220, 1691, "To the Vale")
        bot_instance.Move.XY(7035, 1973, "To the Vale")
        bot_instance.Move.XY(8089, -3303, "To the Vale")
        bot_instance.Move.XY(8121, -6054, "To the Vale")
    

def Restore_Mountains(bot_instance: Botting):
    if BotSettings.RestoreMountains:
        bot_instance.States.AddHeader("Restore the Mountains")
        bot_instance.Move.XY(7013, -7582, "To the Vale")
        bot_instance.Move.XY(1420, -9126, "To the Vale")
        bot_instance.Move.XY(-8373, -5016, "To the Vale")

def Deamon_Assassin(bot_instance: Botting):
    if BotSettings.DeamonAssassin:
        bot_instance.States.AddHeader("Deamon Assassin")
        bot_instance.Move.XYAndInteractNPC(-8250, -5171, "go to NPC")
        bot_instance.Wait.ForTime(3000)
        bot_instance.Dialogs.AtXY(-8250, -5171, 0x806803, "take quest")
        bot_instance.Dialogs.AtXY(-8250, -5171, 0x806801, "take quest")
        bot_instance.Move.XY(-1384, -3929, "To the Vale")
        bot_instance.Wait.ForTime(30000)
        #ModelID Slayer 2391

def Restore_Planes(bot_instance: Botting):
    if BotSettings.RestorePlanes:
        bot_instance.States.AddHeader("Restore Planes")
        Wait_for_Spawns(bot,10371, -10510)
        Wait_for_Spawns(bot,12795, -8811)
        Wait_for_Spawns(bot,11180, -13780)
        Wait_for_Spawns(bot,13740, -15087)
        bot_instance.Move.XY(11546, -13787, "To the Vale")
        bot_instance.Move.XY(8530, -11585, "To the Vale")
        Wait_for_Spawns(bot,8533, -13394)
        Wait_for_Spawns(bot,8579, -20627)
        Wait_for_Spawns(bot,11218, -17404)

def The_Four_Horsemen(bot_instance: Botting):
    if BotSettings.TheFourHorsemen:
        bot_instance.States.AddHeader("The Four Horseman")
        bot_instance.Move.XY(13473, -12091, "To the Vale")
        bot_instance.Wait.ForTime(10000)
        bot_instance.Party.FlagAllHeroes(13473, -12091)
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(False), "Disable Following")

        bot_instance.Move.XYAndInteractNPC(11371, -17990, "go to NPC")
        bot_instance.Dialogs.AtXY(-8250, -5171, 0x806A03, "take quest")
        bot_instance.Dialogs.AtXY(-8250, -5171, 0x806A01, "take quest")  

        bot_instance.Wait.ForTime(30000)

        bot_instance.Move.XYAndInteractNPC(11371, -17990, "TP to Chamber")
        bot_instance.Dialogs.AtXY(11371, -17990, 0x7F, "take quest")
        bot_instance.Dialogs.AtXY(11371, -17990, 0x86, "take quest") 
        bot_instance.Dialogs.AtXY(11371, -17990, 0x8D, "take quest") 

        bot_instance.Wait.ForTime(1000)

        bot_instance.Move.XYAndInteractNPC(-5782, 12819, "TP back to Chaos")
        bot_instance.Dialogs.AtXY(11371, -17990, 0x7F, "take quest")
        bot_instance.Dialogs.AtXY(11371, -17990, 0x84, "take quest") 
        bot_instance.Dialogs.AtXY(11371, -17990, 0x8B, "take quest") 
        bot_instance.Wait.ForTime(1000)
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(True), "Enable Following")
        bot_instance.Party.UnflagAllHeroes()
        bot_instance.Wait.ForTime(5000)
        bot_instance.Move.XY(11371, -17990, "To the Vale")
        bot_instance.Wait.ForTime(30000)
        bot_instance.Move.XY(11371, -17990, "To the Vale")

def Restore_Pools(bot_instance: Botting):
    if BotSettings.RestorePools:
        bot_instance.States.AddHeader("Restore Pools")
        Wait_for_Spawns(bot,4647, -16833)
        Wait_for_Spawns(bot,2098, -15543)
        bot_instance.Move.XY(-12703, -10990, "To the Vale")
        bot_instance.Move.XY(-11849, -11986, "To the Vale")
        bot_instance.Move.XY(-7217, -19394, "To the Vale")
        #bot_instance.Move.XYAndInteractNPC(-6957, -19478, "go to NPC")
        #bot_instance.Dialogs.AtXY(-6957, -19478, 0x7F, "Back to Chamber")
        #bot_instance.Dialogs.AtXY(-6957, -19478, 0x84, "Back to Chamber")
        #bot_instance.Dialogs.AtXY(-6957, -19478, 0x8B, "Back to Chamber")
        bot_instance.Wait.ForTime(3000)

def Terrorweb_Queen(bot_instance: Botting):
    if BotSettings.TerrorwebQueen:
        bot_instance.States.AddHeader("Terrorweb Queen")
        bot_instance.Move.XYAndInteractNPC(-6961, -19499, "go to NPC")
        bot_instance.Dialogs.AtXY(-6961, -19499, 0x806B03, "take quest")
        bot_instance.Dialogs.AtXY(-6961, -19499, 0x806B01, "take quest")   
        bot_instance.Move.XY(-12303, -15213, "To the Vale")
        bot_instance.Move.XYAndInteractNPC(-6957, -19478, "go to NPC")
        bot_instance.Dialogs.AtXY(-6957, -19478, 0x7F, "Back to Chamber")
        bot_instance.Dialogs.AtXY(-6957, -19478, 0x84, "Back to Chamber")
        bot_instance.Dialogs.AtXY(-6957, -19478, 0x8B, "Back to Chamber")
    
def Restore_Pit(bot_instance: Botting):
    if BotSettings.RestorePit:
        bot_instance.States.AddHeader("Restore Pit")
        bot_instance.Move.XY(13145, -8740, "To the Vale")
        bot_instance.Move.XY(12188, 4249, "To the Vale")
        bot_instance.Move.XY(14959, 4851, "To the Vale")
        bot_instance.Move.XY(15460, 3125, "To the Vale")
        bot_instance.Move.XY(8970, 6813, "To the Vale")
        #bot_instance.Move.XYAndInteractNPC(8698, 6324, "go to NPC")
        #bot_instance.Dialogs.AtXY(8698, 6324, 0x7F, "Back to Chamber")
        #bot_instance.Dialogs.AtXY(8698, 6324, 0x86, "Back to Chamber")
        #bot_instance.Dialogs.AtXY(8698, 6324, 0x8D, "Back to Chamber")

def Imprisoned_Spirits(bot_instance: Botting):
    if BotSettings.ImprisonedSpirits:
        bot_instance.States.AddHeader("Imprisoned Spirits")
        bot_instance.Move.XY(12329, 4632, "To the Vale")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().party_flagging_manager.assign_formation_for_current_party("preset_1"), "Set Flag")
        bot_instance.Party.FlagAllHeroes(12329, 4632)
        bot_instance.Move.XYAndInteractNPC(8666, 6308, "go to NPC")
        bot_instance.Dialogs.AtXY(8666, 6308, 0x806903, "Back to Chamber")
        bot_instance.Dialogs.AtXY(8666, 6308, 0x806901, "Back to Chamber")
        bot_instance.Move.XY(12329, 4632, "To the Vale")
#def c_a_gift_of_griffons(bot_instance: Botting):

def Wait_for_Spawns(bot_instance: Botting,x,y):
    # 1. Die Logik-Funktion definieren (Das hier läuft erst zur LAUFZEIT im Loop)
    bot_instance.Move.XY(x, y, "To the Vale")
    def runtime_check_logic():
        # Wir suchen Gegner
        enemies = [e for e in AgentArray.GetEnemyArray() if Agent.IsAlive(e) and Agent.GetModelID(e) == 2380]
        
        if not enemies:
            print("No Mindblades found - Continuing...") 
            return True  # True = Bedingung erfüllt, Warten beenden!
        
        # Optional: Nur alle paar Frames printen, um Spam zu vermeiden
        print("Mindblades ... Waiting.")
        return False # False = Bedingung nicht erfüllt, weiter warten

    # 2. Den Schritt zur Bot-Liste hinzufügen (Das passiert beim LADEN)
    # "ForCondition" ist das Äquivalent zu AddCustomState, aber speziell für Warteschleifen.
    bot_instance.Wait.UntilCondition(runtime_check_logic)
    bot_instance.Wait.ForTime(5000)
    bot_instance.Move.XY(x, y, "To the Vale")
    bot_instance.Wait.UntilCondition(runtime_check_logic)
    bot_instance.Wait.ForTime(5000)
    bot_instance.Move.XY(x, y, "To the Vale")
    bot_instance.Wait.UntilCondition(runtime_check_logic)
    bot_instance.Wait.ForTime(5000)
    bot_instance.Move.XY(x, y, "To the Vale")
    bot_instance.Wait.UntilCondition(runtime_check_logic)


def _draw_help():
    import PyImGui
    PyImGui.text("Snowball Dominance Farmer")
    PyImGui.separator()
    PyImGui.text_wrapped("This bot automates the repeatable 'Snowball Dominance' quest.")
    PyImGui.text("QUEST REWARDS:")
    PyImGui.bullet_text("500 Gold")
    PyImGui.bullet_text("Wintersday Gifts")
    PyImGui.bullet_text("Tonics")
    PyImGui.separator()
    PyImGui.text("PREREQUISITES:")
    PyImGui.text_wrapped("Must complete: 'The Three Wise Norn' & 'Charr-broiled Plans'.")
    PyImGui.separator()
    PyImGui.text("REQUIREMENTS:")
    PyImGui.bullet_text("Olias (Necromancer) MUST be unlocked.")
    PyImGui.bullet_text("Strategy: Olias with 'Charm Animal' + Polar Bear.")
    PyImGui.bullet_text("Weapon: 20/20 HCT Set recommended.")
    PyImGui.text(f"Instance Time: {Map.GetInstanceUptime()}")

def _draw_settings():
    BotSettings.RestoreVale = PyImGui.checkbox("Restore Vale", BotSettings.RestoreVale)
    BotSettings.WrathfullSpirits = PyImGui.checkbox("Wrathfull Spirits", BotSettings.WrathfullSpirits)
    BotSettings.EscortOfSouls = PyImGui.checkbox("Escort of Souls", BotSettings.EscortOfSouls)
    BotSettings.RestoreWastes = PyImGui.checkbox("Restore Wastes", BotSettings.RestoreWastes)
    BotSettings.ServantsOfGrenth = PyImGui.checkbox("Servants of Grenth", BotSettings.ServantsOfGrenth)
    BotSettings.PassTheMountains = PyImGui.checkbox("Pass the Mountains", BotSettings.PassTheMountains)
    BotSettings.RestoreMountains = PyImGui.checkbox("Restore Mountains", BotSettings.RestoreMountains)
    BotSettings.DeamonAssassin = PyImGui.checkbox("Deamon Assassin", BotSettings.DeamonAssassin)
    BotSettings.RestorePlanes = PyImGui.checkbox("Restore Planes", BotSettings.RestorePlanes)
    BotSettings.TheFourHorsemen = PyImGui.checkbox("The Four Horsemen", BotSettings.TheFourHorsemen)
    BotSettings.RestorePools = PyImGui.checkbox("Restore Pools", BotSettings.RestorePools)
    BotSettings.TerrorwebQueen = PyImGui.checkbox("Terrorweb Queen", BotSettings.TerrorwebQueen)
    BotSettings.RestorePit = PyImGui.checkbox("Restore Pit", BotSettings.RestorePit)
    BotSettings.ImprisonedSpirits = PyImGui.checkbox("Imprisoned Spirits", BotSettings.ImprisonedSpirits)
    PyImGui.separator()
    BotSettings.DEBUG = PyImGui.checkbox("Enable Debug Logs", BotSettings.DEBUG)




#bot = Botting("[DUNGEON] FoW")
bot.SetMainRoutine(bot_routine)

def OnPartyWipe(bot: "Botting"):
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_Underworld", lambda: _on_party_wipe(bot))


def _on_party_wipe(bot: "Botting"):
    ConsoleLog(BOT_NAME, "[WIPE] Party wipe detected!", Py4GW.Console.MessageType.Warning)

    while Agent.IsDead(Player.GetAgentID()):
        yield from Routines.Yield.wait(1000)

        if not Routines.Checks.Map.MapValid():
            ConsoleLog(BOT_NAME, "[WIPE] Returned to outpost after wipe, restarting run...", Py4GW.Console.MessageType.Warning)
            yield from Routines.Yield.wait(3000)
            _restart_main_loop(bot, "Returned to outpost after wipe")
            return

    ConsoleLog(BOT_NAME, "[WIPE] Player resurrected in instance, resuming...", Py4GW.Console.MessageType.Info)
    _restart_main_loop(bot, "Player resurrected in instance")


def main():
    bot.Update()
    bot.UI.draw_window()

if __name__ == "__main__":
    main()