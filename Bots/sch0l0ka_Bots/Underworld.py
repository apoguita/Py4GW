from Py4GWCoreLib import Botting, Routines, Agent, AgentArray, Player, Utils, AutoPathing, GLOBAL_CACHE, ConsoleLog, Map, Pathing, FlagPreference
from Sources.oazix.CustomBehaviors.primitives.botting.botting_helpers import BottingHelpers
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.botting.botting_fsm_helper import BottingFsmHelpers
from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from pathlib import Path
import PyImGui
import Py4GW



# Override the help window
BOT_NAME = "Underworld Helper"
bot = Botting(BOT_NAME, config_draw_path=True)
bot.Templates.Aggressive()
# Override the help window
bot.UI.override_draw_help(lambda: _draw_help())
bot.UI.override_draw_config(lambda: _draw_settings())  # Disable default config window
MAIN_LOOP_HEADER_NAME = ""


class BotSettings:
    RestoreVale: bool = False           #Working
    WrathfullSpirits: bool = False      #Working but can be improved
    EscortOfSouls: bool = False         #Working but can be improved by doing it with Restoring Vale
    RestoreWastes: bool = True          #Working
    ServantsOfGrenth: bool = True       #Working
    PassTheMountains: bool = True       #Working
    RestoreMountains: bool = False      #Working
    DeamonAssassin: bool = False        #Working
    RestorePlanes: bool = True          #Working
    TheFourHorsemen: bool = True        #Working
    RestorePools: bool = True           #Working but sometimes the Reaper dies
    TerrorwebQueen: bool = True         #Working
    RestorePit: bool = False             #Not Working
    ImprisonedSpirits: bool = False      #Not Working  
    DEBUG: bool = False


# Precomputed spread points keep Servants of Grenth flags spaced without extra imports.
def _toggle_wait_if_aggro(enabled: bool) -> None:
    behavior = CustomBehaviorLoader().custom_combat_behavior
    if behavior is None:
        return
    for utility in behavior.get_skills_final_list():
        if utility.custom_skill.skill_name == "wait_if_in_aggro":
            utility.is_enabled = enabled
            break

def _toggle_wait_for_party(enabled: bool) -> None:
    behavior = CustomBehaviorLoader().custom_combat_behavior
    if behavior is None:
        return
    for utility in behavior.get_skills_final_list():
        if utility.custom_skill.skill_name == "wait_if_party_member_too_far":
            utility.is_enabled = enabled
            break

def _toggle_move_if_aggro(enabled: bool) -> None:
    behavior = CustomBehaviorLoader().custom_combat_behavior
    if behavior is None:
        return
    for utility in behavior.get_skills_final_list():
        if utility.custom_skill.skill_name == "move_to_party_member_if_in_aggro":
            utility.is_enabled = enabled
            break

def _toggle_lock(enabled: bool) -> None:
    behavior = CustomBehaviorLoader().custom_combat_behavior
    if behavior is None:
        return
    for utility in behavior.get_skills_final_list():
        if utility.custom_skill.skill_name == "wait_if_lock_taken":
            utility.is_enabled = enabled
            break

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

def _ensure_minimum_gold(bot_instance: Botting, minimum_gold: int = 1000, withdraw_amount: int = 10000) -> None:
    def _check_and_restock():
        gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
        if gold_on_char >= minimum_gold:
            return

        gold_in_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()
        amount_to_withdraw = min(withdraw_amount, gold_in_storage)

        if amount_to_withdraw <= 0:
            ConsoleLog(BOT_NAME, "[GOLD] Storage empty – cannot restock gold.", Py4GW.Console.MessageType.Warning)
            return

        ConsoleLog(
            BOT_NAME,
            f"[GOLD] Inventory only has {gold_on_char}g. Withdrawing {amount_to_withdraw}g from storage.",
            Py4GW.Console.MessageType.Info,
        )
        GLOBAL_CACHE.Inventory.WithdrawGold(amount_to_withdraw)

    bot_instance.States.AddCustomState(_check_and_restock, "Ensure Minimum Gold")
    bot_instance.Wait.ForTime(1000)


def _auto_assign_flag_emails() -> None:
    CustomBehaviorParty().party_flagging_manager.auto_assign_emails_if_none_assigned()


def _set_flag_position(index: int, flag_x: int, flag_y: int) -> None:
    CustomBehaviorParty().party_flagging_manager.set_flag_position(index, flag_x, flag_y)

def bot_routine(bot: Botting):

    global MAIN_LOOP_HEADER_NAME
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    CustomBehaviorParty().set_party_is_blessing_enabled(True)
    BottingFsmHelpers.SetBottingBehaviorAsAggressive(bot)
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
    _ensure_minimum_gold(bot_instance)
    CustomBehaviorParty().set_party_leader_email(Player.GetAccountEmail())
    bot_instance.Move.XY(-4199, 19845, "go to Statue")
    bot_instance.States.AddCustomState(lambda: Player.SendChatCommand("kneel"), "kneel")
    bot_instance.Wait.ForTime(3000)
    #bot_instance.Dialogs.AtXY(-4199, 19845, 0x85, "ask to enter")
    bot_instance.Dialogs.AtXY(-4199, 19845, 0x86, "accept to enter")
    bot_instance.Wait.ForMapLoad(target_map_id=72) # we are in the dungeon
    bot_instance.Properties.ApplyNow("pause_on_danger", "active", True)


def Clear_the_Chamber(bot_instance: Botting):
    bot_instance.States.AddHeader("Clear the Chamber")
    CustomBehaviorParty().set_party_leader_email(Player.GetAccountEmail())
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Disable Lock Wait")
    bot_instance.Wait.ForTime(30000)
    bot_instance.Move.XYAndInteractNPC(295, 7221, "go to NPC")
    bot_instance.Dialogs.AtXY(295, 7221, 0x806501, "take quest")
    bot_instance.Move.XY(-1505, 6352, "Left")
    bot_instance.Move.XY(-755, 8982, "Mid")
    bot_instance.Move.XY(1259, 10214, "Right")
    bot_instance.Move.XY(-3729, 13414, "Right")
    bot_instance.Move.XY(-5855, 11202, "Clear the Room")
    bot_instance.Wait.ForTime(3000)
    bot_instance.Move.XYAndInteractNPC(-5806, 12831, "go to NPC")
    bot_instance.Wait.ForTime(3000)
    #bot_instance.Dialogs.AtXY(-5806, 12831, 0x806507, "take quest")
    #bot_instance.Dialogs.AtXY(-5806, 12831, 0x806D03, "take quest")
    bot_instance.Dialogs.AtXY(-5806, 12831, 0x806D01, "take quest")
    bot_instance.Wait.ForTime(3000)

def Restore_Vale(bot_instance: Botting):
    if BotSettings.RestoreVale:
        bot_instance.States.AddHeader("Restore Vale")
        BottingFsmHelpers.SetBottingBehaviorAsAggressive(bot_instance)
        bot_instance.Move.XY(-8660, 5655, "To the Vale 1")
        bot_instance.Wait.ForTime(5000)
        bot_instance.Move.XY(-9431, 1659, "To the Vale 2")
        bot_instance.Move.XY(-11123, 2531, "To the Vale 3")
        bot_instance.Move.XY(-10212, 251 , "To the Vale 4")
        bot_instance.Move.XY(-13085, 849 , "To the Vale 5")
        bot_instance.Move.XY(-15274, 1432 , "To the Vale 6")
        bot_instance.Move.XY(-13246, 5110 , "To the Vale 7")
        
        bot_instance.Move.XYAndInteractNPC(-13275, 5261, "go to NPC")
        if BotSettings.WrathfullSpirits == False:
            #bot_instance.Dialogs.AtXY(5755, 12769, 0x7F, "Back to Chamber")
            #bot_instance.Dialogs.AtXY(5755, 12769, 0x86, "Back to Chamber")
            bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "Back to Chamber")
        bot_instance.Wait.ForTime(3000)

def Wrathfull_Spirits(bot_instance: Botting):
    if BotSettings.WrathfullSpirits:
        bot_instance.States.AddHeader("Wrathfull Spirits")
        bot_instance.Move.XYAndInteractNPC(-13275, 5261, "go to NPC")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x806E03, "Back to Chamber")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x806E01, "Back to Chamber")
        bot_instance.Templates.Pacifist()
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
        bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(False), "Disable WaitIfInAggro")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_combat_enabled(False), "Disable Combat")
        bot_instance.Move.XY(-13422, 973, "Wrathfull Spirits 1")
        bot_instance.Templates.Aggressive()
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_combat_enabled(True), "Enable Combat")
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar") 
        bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
        bot_instance.Move.XY(-10207, 1746, "Wrathfull Spirits 2")
        bot_instance.Move.XY(-13287, 1996, "Wrathfull Spirits 3")
        bot_instance.Move.XY(-15226, 4129 , "Wrathfull Spirits 4")
        bot_instance.Move.XYAndInteractNPC(-13275, 5261, "go to NPC")
        #bot_instance.Dialogs.AtXY(5755, 12769, 0x7F, "Back to Chamber")
        #bot_instance.Dialogs.AtXY(5755, 12769, 0x86, "Back to Chamber")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "Back to Chamber")
        bot_instance.Wait.ForTime(3000)

def Escort_of_Souls(bot_instance: Botting):
    if BotSettings.EscortOfSouls:
        bot_instance.States.AddHeader("Escort of Souls")
        bot_instance.Wait.ForTime(5000)
        bot_instance.Move.XY(-4764, 11845, "Escort of Souls 1")
        bot_instance.Move.XYAndInteractNPC(-5806, 12831, "go to NPC")
        bot_instance.Wait.ForTime(3000)
        bot_instance.Dialogs.AtXY(-5806, 12831, 0x806C03, "take quest")
        bot_instance.Dialogs.AtXY(-5806, 12831, 0x806C01, "take quest")
        bot_instance.Move.XY(-6833, 7077, "Escort of Souls 2")
        bot_instance.Move.XY(-9606, 2110, "Escort of Souls 3")
        bot_instance.Move.XYAndInteractNPC(-13275, 5261, "go to NPC")
        #bot_instance.Dialogs.AtXY(5755, 12769, 0x7F, "Back to Chamber")
        #bot_instance.Dialogs.AtXY(5755, 12769, 0x86, "Back to Chamber")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "Back to Chamber")
        bot_instance.Wait.ForTime(3000)

def Restore_Wastes(bot_instance: Botting):
    if BotSettings.RestoreWastes:
        bot_instance.Templates.Aggressive()
        bot_instance.Properties.ApplyNow("pause_on_danger", "active", True)
        bot_instance.States.AddHeader("Restore Wastes")
        bot_instance.Move.XY(3891, 7572, "Restore Wastes 1")
        bot_instance.Move.XY(4106, 16031, "Restore Wastes 2")
        bot_instance.Move.XY(2486, 21723, "Restore Wastes 3")
        bot_instance.Move.XY(-1452, 21202, "Restore Wastes 4")
        bot_instance.Move.XY(542, 18310, "Restore Wastes 5")
        if BotSettings.ServantsOfGrenth == False:
            bot_instance.Move.XYAndInteractNPC(554, 18384, "go to NPC")
            #bot_instance.Dialogs.AtXY(5755, 12769, 0x7F, "Back to Chamber")
            #bot_instance.Dialogs.AtXY(5755, 12769, 0x86, "Back to Chamber")
            bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "Back to Chamber")
        bot_instance.Wait.ForTime(3000)

def Servants_of_Grenth(bot_instance: Botting):
    if BotSettings.ServantsOfGrenth:
        bot_instance.Templates.Aggressive()
        bot_instance.States.AddHeader("Servants of Grenth")
        bot_instance.Move.XY(2700, 19952, "Servants of Grenth 1")

        SERVANTS_OF_GRENTH_FLAG_POINTS = [
            (2559, 20301),
            (3032, 20148),
            (2813, 20590),
            (2516, 19665),
            (3231, 19472),
            (3691, 19979),
            (2039, 20175),
            ]
        bot_instance.States.AddCustomState(
            lambda: _auto_assign_flag_emails(),
            "Set Flag",
        )
        for idx, (flag_x, flag_y) in enumerate(SERVANTS_OF_GRENTH_FLAG_POINTS, start=1):
            bot_instance.States.AddCustomState(
                lambda i=idx, x=flag_x, y=flag_y: _set_flag_position(i, x, y),
                f"Set Flag {idx}",
            )
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
        bot_instance.Move.XYAndInteractNPC(554, 18384, "go to NPC")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(False), "Disable Following")
        bot_instance.States.AddCustomState(
            lambda: CustomBehaviorParty().party_flagging_manager.clear_all_flags(),
            "Clear Flags",
        )
        
        #bot_instance.Dialogs.AtXY(5755, 12769, 0x806603, "Back to Chamber")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x806601, "Back to Chamber")
        bot_instance.Move.XY(2700, 19952, "Servants of Grenth 2")
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(True), "Enable Following")
        bot_instance.Wait.ForTime(10000)
        bot_instance.Move.XYAndInteractNPC(554, 18384, "go to NPC")
        #bot_instance.Dialogs.AtXY(5755, 12769, 0x7F, "Back to Chamber")
        #bot_instance.Dialogs.AtXY(5755, 12769, 0x86, "Back to Chamber")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "Back to Chamber")
        bot_instance.Wait.ForTime(3000)

def Pass_The_Mountains(bot_instance: Botting):
    if BotSettings.PassTheMountains:
        bot_instance.States.AddHeader("Pass the Mountains")
        bot_instance.Move.XY(-220, 1691, "Pass the Mountains 1")
        bot_instance.Move.XY(7035, 1973, "Pass the Mountains 2")
        bot_instance.Move.XY(8089, -3303, "Pass the Mountains 3")
        bot_instance.Move.XY(8121, -6054, "Pass the Mountains 4")
    

def Restore_Mountains(bot_instance: Botting):
    if BotSettings.RestoreMountains:
        bot_instance.States.AddHeader("Restore the Mountains")
        bot_instance.Move.XY(7013, -7582, "Restore the Mountains 1")
        bot_instance.Move.XY(1420, -9126, "Restore the Mountains 2")
        bot_instance.Move.XY(-8373, -5016, "Restore the Mountains 3")

def Deamon_Assassin(bot_instance: Botting):
    if BotSettings.DeamonAssassin:
        bot_instance.States.AddHeader("Deamon Assassin")
        bot_instance.Move.XYAndInteractNPC(-8250, -5171, "go to NPC")
        bot_instance.Wait.ForTime(3000)
        #bot_instance.Dialogs.AtXY(-8250, -5171, 0x806803, "take quest")
        bot_instance.Dialogs.AtXY(-8250, -5171, 0x806801, "take quest")
        bot_instance.Move.XY(-1384, -3929, "Deamon Assassin 1")
        bot_instance.Wait.ForTime(30000)
        #ModelID Slayer 2391

def Restore_Planes(bot_instance: Botting):
    if BotSettings.RestorePlanes:
        bot_instance.States.AddHeader("Restore Planes")
        Wait_for_Spawns(bot_instance,10371, -10510)
        Wait_for_Spawns(bot_instance,12795, -8811)
        Wait_for_Spawns(bot_instance,11180, -13780)
        Wait_for_Spawns(bot_instance,13740, -15087)
        bot_instance.Move.XY(11546, -13787, "Restore Planes 1")
        bot_instance.Move.XY(8530, -11585, "Restore Planes 2")
        Wait_for_Spawns(bot_instance,8533, -13394)
        Wait_for_Spawns(bot_instance,8579, -20627)
        Wait_for_Spawns(bot_instance,11218, -17404)

def The_Four_Horsemen(bot_instance: Botting):
    if BotSettings.TheFourHorsemen:
        bot_instance.States.AddHeader("The Four Horseman")
        bot_instance.Move.XY(13473, -12091, "The Four Horseman 1")
        bot_instance.Wait.ForTime(10000)
        bot_instance.Party.FlagAllHeroes(13473, -12091)
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(False), "Disable Following")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_looting_enabled(False), "Disable Looting")
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
        bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(False), "Disable MoveIfPartyMemberInAggro")
        bot_instance.Move.XYAndInteractNPC(11371, -17990, "go to NPC")
        #bot_instance.Dialogs.AtXY(-8250, -5171, 0x806A03, "take quest")
        bot_instance.Dialogs.AtXY(-8250, -5171, 0x806A01, "take quest")  

        bot_instance.Wait.ForTime(30000)

        bot_instance.Move.XYAndInteractNPC(11371, -17990, "TP to Chamber")
        #bot_instance.Dialogs.AtXY(11371, -17990, 0x7F, "take quest")
        #bot_instance.Dialogs.AtXY(11371, -17990, 0x86, "take quest") 
        bot_instance.Dialogs.AtXY(11371, -17990, 0x8D, "take quest") 

        bot_instance.Wait.ForTime(1000)

        bot_instance.Move.XYAndInteractNPC(-5782, 12819, "TP back to Chaos")
        #bot_instance.Dialogs.AtXY(11371, -17990, 0x7F, "take quest")
        #bot_instance.Dialogs.AtXY(11371, -17990, 0x84, "take quest") 
        bot_instance.Dialogs.AtXY(11371, -17990, 0x8B, "take quest") 
        bot_instance.Wait.ForTime(1000)
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(True), "Enable Following")
        bot_instance.Party.UnflagAllHeroes()
        bot_instance.Wait.ForTime(5000)
        bot_instance.Move.XY(11371, -17990, "The Four Horseman 2")
        bot_instance.Wait.ForTime(30000)
        bot_instance.Move.XY(11371, -17990, "The Four Horseman 3")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(True), "Enable Looting")
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
        bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")

def Restore_Pools(bot_instance: Botting):
    if BotSettings.RestorePools:
        bot_instance.States.AddHeader("Restore Pools")
        Wait_for_Spawns(bot_instance,4647, -16833)
        Wait_for_Spawns(bot_instance,2098, -15543)
        bot_instance.Move.XY(-12703, -10990, "Restore Pools 1")
        bot_instance.Move.XY(-11849, -11986, "Restore Pools 2")
        bot_instance.Move.XY(-7217, -19394, "Restore Pools 3")
        if BotSettings.TerrorwebQueen == False:
            bot_instance.Move.XYAndInteractNPC(-6957, -19478, "go to NPC")
            #bot_instance.Dialogs.AtXY(-6957, -19478, 0x7F, "Back to Chamber")
            #bot_instance.Dialogs.AtXY(-6957, -19478, 0x84, "Back to Chamber")
            bot_instance.Dialogs.AtXY(-6957, -19478, 0x8B, "Back to Chamber")
        bot_instance.Wait.ForTime(3000)

def Terrorweb_Queen(bot_instance: Botting):
    if BotSettings.TerrorwebQueen:
        bot_instance.States.AddHeader("Terrorweb Queen")
        bot_instance.Move.XYAndInteractNPC(-6961, -19499, "go to NPC")
        #bot_instance.Dialogs.AtXY(-6961, -19499, 0x806B03, "take quest")
        bot_instance.Dialogs.AtXY(-6961, -19499, 0x806B01, "take quest")   
        bot_instance.Move.XY(-12303, -15213, "Terrorweb Queen 1")
        bot_instance.Move.XYAndInteractNPC(-6957, -19478, "go to NPC")
        #bot_instance.Dialogs.AtXY(-6957, -19478, 0x7F, "Back to Chamber")
        #bot_instance.Dialogs.AtXY(-6957, -19478, 0x84, "Back to Chamber")
        bot_instance.Dialogs.AtXY(-6957, -19478, 0x8B, "Back to Chamber")
    
def Restore_Pit(bot_instance: Botting):
    if BotSettings.RestorePit:
        bot_instance.States.AddHeader("Restore Pit")
        bot_instance.Move.XY(13145, -8740, "Restore Pit 1")
        bot_instance.Move.XY(12188, 4249, "Restore Pit 2")
        bot_instance.Move.XY(14959, 4851, "Restore Pit 3")
        bot_instance.Move.XY(15460, 3125, "Restore Pit 4")
        bot_instance.Move.XY(8970, 6813, "Restore Pit 5")
        if BotSettings.ImprisonedSpirits == False:
            bot_instance.Move.XYAndInteractNPC(8698, 6324, "go to NPC")
            #bot_instance.Dialogs.AtXY(8698, 6324, 0x7F, "Back to Chamber")
            #bot_instance.Dialogs.AtXY(8698, 6324, 0x86, "Back to Chamber")
            bot_instance.Dialogs.AtXY(8698, 6324, 0x8D, "Back to Chamber")
        bot_instance.Wait.ForTime(3000)

def Imprisoned_Spirits(bot_instance: Botting):
    if BotSettings.ImprisonedSpirits:
        bot_instance.States.AddHeader("Imprisoned Spirits")
        bot_instance.Move.XY(12329, 4632, "Imprisoned Spirits 1")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().party_flagging_manager.assign_formation_for_current_party("preset_1"), "Set Flag")
        bot_instance.Party.FlagAllHeroes(12329, 4632)
        bot_instance.Move.XYAndInteractNPC(8666, 6308, "go to NPC")
        #bot_instance.Dialogs.AtXY(8666, 6308, 0x806903, "Back to Chamber")
        bot_instance.Dialogs.AtXY(8666, 6308, 0x806901, "Back to Chamber")
        bot_instance.Move.XY(12329, 4632, "Imprisoned Spirits 2")

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
    bot_instance.Wait.ForTime(1000)
    bot_instance.Move.XY(x, y, "To the Vale")
    bot_instance.Wait.UntilCondition(runtime_check_logic)
    bot_instance.Wait.ForTime(1000)
    bot_instance.Move.XY(x, y, "To the Vale")
    bot_instance.Wait.UntilCondition(runtime_check_logic)
    bot_instance.Wait.ForTime(1000)
    bot_instance.Move.XY(x, y, "To the Vale")
    bot_instance.Wait.UntilCondition(runtime_check_logic)


def _draw_help():
    import PyImGui
    PyImGui.text("Hey, this is my first bot in Python, be gentle :)")
    PyImGui.separator()
    PyImGui.text_wrapped("This Bot automates the Underworld")
    PyImGui.text("It is optimized for 8x Custom Behaviors, HeroAi dont wor atm")
    PyImGui.text_wrapped("Some quests are not easy to automate, so I recommend to watch the bot at least the first time to see how it works")
    PyImGui.text_wrapped("Some quests are missing, I will add them when I have time, but feel free to contribute :)")
    PyImGui.text_wrapped("Some quests are just not easy, because its the Underworld")
    PyImGui.separator()
    PyImGui.text("What is working Well:")
    PyImGui.bullet_text("Restoring Grenth's Monuments (exept Pits)")
    PyImGui.bullet_text("Wrathfull Spirits, Escort of Souls, Servants of Grenth(hard), Deamon Assassin, The Four Horsemen, Terrorweb Queen")
    PyImGui.text("What is working Bad:")
    PyImGui.bullet_text("Imprisoned Spirits, Restore Pits")
    PyImGui.text("What is not implemented::")
    PyImGui.bullet_text("Unwanted Guests, The Nightman Cometh (Dhuum)")
    PyImGui.separator()
    PyImGui.text("Req:")
    PyImGui.bullet_text("Highend Team")
    PyImGui.bullet_text("Cons (via Pcons widget)")
    PyImGui.bullet_text("You have to do the missing quests manually")
    PyImGui.bullet_text("Main Account sometimes leaves the team. Dont be the Healer")
    PyImGui.bullet_text("You should either have some evas or 1 melee char to trigger traps in the mountains")


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