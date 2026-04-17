from Py4GWCoreLib import Botting
from Sources.oazix.CustomBehaviors.gui.flag_panel.flag_backward_grid_placement import FlagBackwardGridPlacement
from Sources.oazix.CustomBehaviors.primitives.botting.botting_fsm_helper import BottingFsmHelpers
from Sources.oazix.CustomBehaviors.primitives.following_behavior_priority import FollowingBehaviorPriority
from Sources.oazix.CustomBehaviors.primitives.botting.botting_helpers import BottingHelpers
from Sources.oazix.CustomBehaviors.primitives.botting.botting_manager import BottingManager
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.parties.party_flagging_manager import PartyFlaggingManager
from Sources.oazix.CustomBehaviors.primitives.parties.party_following_manager import PartyFollowingManager
from Sources.oazix.CustomBehaviors.skills.botting.move_to_enemy_if_close_enough import MoveToEnemyIfCloseEnoughUtility
from Sources.oazix.CustomBehaviors.skills.botting.move_to_party_member_if_dead import MoveToPartyMemberIfDeadUtility
from Sources.oazix.CustomBehaviors.skills.botting.move_to_party_member_if_in_aggro import MoveToPartyMemberIfInAggroUtility
from Sources.oazix.CustomBehaviors.skills.botting.wait_if_in_aggro import WaitIfInAggroUtility
from Sources.oazix.CustomBehaviors.skills.botting.wait_if_lock_taken import WaitIfLockTakenUtility
from Sources.oazix.CustomBehaviors.skills.botting.wait_if_party_member_mana_too_low import WaitIfPartyMemberManaTooLowUtility
from Sources.oazix.CustomBehaviors.skills.botting.wait_if_party_member_needs_to_loot import WaitIfPartyMemberNeedsToLootUtility
from Sources.oazix.CustomBehaviors.skills.botting.wait_if_party_member_too_far import WaitIfPartyMemberTooFarUtility

def bot_routine(bot_instance: Botting):

    bot_instance.States.AddHeader("INIT")

    bot_instance.Templates.Routines.UseCustomBehaviors(
        on_player_critical_death=BottingHelpers.botting_unrecoverable_issue,
        on_party_death=BottingHelpers.botting_unrecoverable_issue,
        on_player_critical_stuck=BottingHelpers.botting_unrecoverable_issue)

    BottingFsmHelpers.SetBottingBehaviorAsAggressive(bot_instance)
    bot_instance.Wait.ForTime(3000)
    BottingFsmHelpers.SetBottingBehaviorAsPacifist(bot_instance)
    bot_instance.Wait.ForTime(3000)
    BottingFsmHelpers.SetBottingBehaviorAsAggressive(bot_instance)
    bot_instance.Wait.ForTime(3000)

    
    CustomBehaviorParty().set_party_is_blessing_enabled(True)
    PartyFollowingManager().set_party_following_behavior_state(FollowingBehaviorPriority.LOW_PRIORITY) 

    # we just disable all to be super speed, the farm is trivial
    BottingManager().configure_aggressive_skill(MoveToEnemyIfCloseEnoughUtility.Name, enabled=True)
    BottingManager().configure_aggressive_skill(MoveToPartyMemberIfInAggroUtility.Name,enabled=True)
    BottingManager().configure_aggressive_skill(WaitIfLockTakenUtility.Name, enabled=True)
    BottingManager().configure_aggressive_skill(WaitIfPartyMemberTooFarUtility.Name, enabled=True)
    BottingManager().configure_aggressive_skill(MoveToPartyMemberIfDeadUtility.Name, enabled=True)
    BottingManager().configure_aggressive_skill(WaitIfPartyMemberManaTooLowUtility.Name, enabled=True)
    BottingManager().configure_aggressive_skill(WaitIfPartyMemberNeedsToLootUtility.Name, enabled=True)
    BottingManager().configure_aggressive_skill(WaitIfInAggroUtility.Name, enabled=True)

    # Set Flags
    FlagBackwardGridPlacement.apply_backward_grid_to_flag_manager()

    # Clear Flags
    PartyFlaggingManager().clear_all_flags()

    # Set up the FSM states properly
    bot_instance.States.AddHeader("MAIN_LOOP")
    bot_instance.Map.Travel(target_map_id=381)
    bot_instance.Wait.ForMapLoad(target_map_id=381)

    bot_instance.Party.SetHardMode(False)

    bot_instance.States.AddHeader("EXIT_OUTPOST")
    bot_instance.UI.PrintMessageToConsole("Debug", "Added header: EXIT_OUTPOST")
    bot_instance.Move.XY(5987, 1241, "Exit Outpost")
    bot_instance.Wait.ForMapLoad(target_map_id=380)

    bot_instance.States.AddHeader("FARM LOOP")

    for farm_coordinate in farm_coordinates():
        bot_instance.Move.XY(farm_coordinate[0], farm_coordinate[1])

    bot_instance.States.AddHeader("GO BACK TO OUTPOST")
    bot_instance.Move.XY(-21789, -14798, "Enter Outpost")
    bot_instance.Wait.ForMapLoad(target_map_id=381)

    bot_instance.States.AddHeader("END")
    bot_instance.config.FSM.AddSelfManagedYieldStep( "wait for party resign.", lambda: BottingHelpers.wrapper(action=BottingHelpers.wait_until_party_resign(timeout_ms = 50_000), on_failure=BottingHelpers.botting_unrecoverable_issue))

    bot_instance.UI.PrintMessageToConsole("END", "Finished routine")

    # Loop back to farm loop
    bot_instance.States.JumpToStepName("[H]MAIN_LOOP_2")

def farm_coordinates() -> list[tuple[float, float]]:
    return [ (-18872, -14304), (-17545, -12840), (-18249, -11494), (-18251, -9614), (-18255, -14646), (-18393, -15739), (-17499, -16418), (-16845, -17140), (-16535, -17567), (-17916, -16217), (-18763, -14359) ]

bot = Botting("[FARM] sunspear title")
bot.SetMainRoutine(bot_routine)

def main():
    bot.Update()
    bot.UI.draw_window()

if __name__ == "__main__":
    main()