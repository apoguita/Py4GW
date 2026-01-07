from collections.abc import Callable
from typing import Any, Generator, override
from Py4GWCoreLib import Botting, Item
from Widgets.CustomBehaviors.primitives.botting.botting_helpers import BottingHelpers
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty

def bot_routine(bot_instance: Botting):

    CustomBehaviorParty().set_party_is_blessing_enabled(True) # require ForMapLoad to have 30s timeout as we can be busy just after map changed.
    # todo DISABLE LOOT FOR SOME PART might be interessting
    
    bot_instance.Templates.Routines.UseCustomBehaviors(
        on_player_critical_death=BottingHelpers.botting_unrecoverable_issue,
        on_party_death=BottingHelpers.botting_unrecoverable_issue,
        on_player_critical_stuck=BottingHelpers.botting_unrecoverable_issue)
    
    bot_instance.Templates.Aggressive()

    bot_instance.States.AddHeader("MAIN_LOOP")
    bot_instance.Map.Travel(target_map_id=638)
    bot_instance.Party.SetHardMode(True)

    bot_instance.States.AddHeader("EXIT_OUTPOST")
    bot_instance.Move.XY(-9559, -19490, "exit outpost")
    bot_instance.config.FSM.AddSelfManagedYieldStep("we are out of the outpost", lambda: BottingHelpers.wrapper(action=BottingHelpers.wait_until_on_map(558 , timeout_ms = 15_000), on_failure=BottingHelpers.botting_unrecoverable_issue))

    bot_instance.States.AddHeader("GO_TO_NPC_QUEST")
    go_to_quest_npc_waypoint = [ (-8943, -17972), (-5884, -16116), (-1499, -14280), (-2306, -11017), (-3198, -9062), (-906, -7811), (732, -7466), (1839, -5173), (3377, -5290), (4687, -5077), (5758, -3946), (6667, -2805), (7509, -1731), (9623, -806), (10714, -853), (12196, 268), (11328, 4192), (10943, 8387), (11911, 11401), (12321, 14909), (13463, 19013), (12990, 20236), (12151, 22222), (12267, 22764) ]
    for waypoint in go_to_quest_npc_waypoint:
        bot_instance.Move.XY(waypoint[0], waypoint[1], "go to quest npc waypoint")
    bot_instance.Move.XY(12275, 22766, "go to quest npc giriff")

    bot_instance.States.AddHeader("MANAGE_NPC_QUEST_AND_ENTER_DUNGEON")

    bot_instance.Move.XY(12275, 22766, "go to quest npc giriff")
    bot_instance.Dialogs.AtXY(12275, 22766, 0x832201, "take quest")
    bot_instance.Wait.ForTime(1000)
    bot_instance.Dialogs.AtXY(12275, 22766, 0x832205, "talk to giriff again")
    bot_instance.Wait.ForTime(1000)
    bot_instance.Move.XY(14810, 27689, "enter dungeon instance")
    bot_instance.config.FSM.AddSelfManagedYieldStep("we are in the dungeon - level 1", lambda: BottingHelpers.wrapper(action=BottingHelpers.wait_until_on_map(615 , timeout_ms = 15_000), on_failure=BottingHelpers.botting_unrecoverable_issue))

    bot_instance.Wait.ForTime(500)

    bot_instance.States.AddHeader("GO_TO_DUNGEON_LEVEL_2")
    level1_waypoints = [ (15180, 1528), (15180, 5346), (18940, 8027), (16807, 8311), (15350, 8325), (12286, 7186), (9936, 6967), (9141, 7041), (8121, 6403), (6436, 5069), (4294, 605), (1345, -1254), (-869, -3962), (-1266, -5683), (-1086, -6701), (-658, -7382), (26, -8628), (2107, -11331), (5809, -12957), (6022, -13895), (6993, -16719), (7753, -19280) ]
    for waypoint in level1_waypoints:
        bot_instance.Move.XY(waypoint[0], waypoint[1], "level 1 waypoints")

    bot_instance.config.FSM.AddSelfManagedYieldStep("we are in the dungeon - level 2", lambda: BottingHelpers.wrapper(action=BottingHelpers.wait_until_on_map(616 , timeout_ms = 300_000), on_failure=BottingHelpers.botting_unrecoverable_issue))
    bot_instance.Wait.ForTime(500)

    bot_instance.States.AddHeader("GO_TO_BOSS_KEY")
    level2_waypoints = [ (-11195, -5346), (-8925, -3654), (-9103, -2458), (-9750, -966), (-8832, 291), (-6204, 3410), (-5058, 3652), (-4280, 4526), (-3806, 5217), (-2511, 5663), (-2633, 8081), (-1182, 7879), (-526, 8509), (21, 9996), (-383, 11207), (473, 11686), (2807, 12326), (3285, 13363), (3684, 13942), (4362, 13750), (5696, 13389), (5725, 12976), (5742, 11691), (6646, 10412), (6909, 9016), (8390, 6811), (8236, 5574), (8319, 4284), (8308, 2983), (8741, 2146), (9722, -1779) ]
    for waypoint in level2_waypoints:
        bot_instance.Move.XY(waypoint[0], waypoint[1], "level 2 waypoints")

    bot_instance.States.AddHeader("LOOT_BOSS_KEY")
    bot_instance.Move.XY(9722, -1779, "go to the boss key")
    bot_instance.config.FSM.AddSelfManagedYieldStep("loot the boss key.", lambda: BottingHelpers.wrapper(action=BottingHelpers.wait_until_item_looted("Boss Key" , timeout_ms = 15_000), on_failure=BottingHelpers.botting_unrecoverable_issue))

    bot_instance.States.AddHeader("OPEN_BOSS_LOCK")
    bot_instance.Move.XY(17900, -6256, "go to the boss lock")
    bot_instance.Interact.WithGadgetAtXY(17900, -6256)
    
    bot_instance.States.AddHeader("END_CHEST")
    chest_waypoints =[ (17609, -6362), (18153, -8601), (17379, -9724), (16787, -10330), (17585, -12000), (18212, -12660), (18037, -13641), (17140, -14356), (15665, -14777), (14965, -15159), (14789, -15820), (15262, -17614), (15326, -18086), (15138, -19140) ]
    for waypoint in chest_waypoints:
        bot_instance.Move.XY(waypoint[0], waypoint[1], "go to chest waypoints")

    bot_instance.Move.XY(15099, -19138, "GO TO THE END CHEST") # GadgetId=8932 IsGadget=true

    bot_instance.Wait.ForTime(30_000)

    bot_instance.States.AddHeader("TAKE_QUEST_REWARD_AND_WAIT_DUNGEON_ENDS")
    bot_instance.Move.XY(15279, -17354, "go to npc")
    bot_instance.Dialogs.WithModel(6745, 0x832207, "accept quest reward")
    bot_instance.Move.XY(15099, -19138, "go back to the end chest") # GadgetId=8932 IsGadget=true

    bot_instance.config.FSM.AddSelfManagedYieldStep("goes out of the dungeon", lambda: BottingHelpers.wrapper(action=BottingHelpers.wait_until_on_map(558 , timeout_ms = 400_000), on_failure=BottingHelpers.botting_unrecoverable_issue))

    bot_instance.States.JumpToStepName("[H]MANAGE_NPC_QUEST_AND_ENTER_DUNGEON_4")

    bot_instance.States.AddHeader("END")

bot = Botting("[DUNGEON] Bogroot Growths")
bot.SetMainRoutine(bot_routine)

def main():
    bot.Update()
    bot.UI.draw_window()

if __name__ == "__main__":
    main()
