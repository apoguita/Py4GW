from Py4GWCoreLib import Botting
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Widgets.CustomBehaviors.primitives.botting.botting_helpers import BottingHelpers
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty

def bot_routine(bot_instance: Botting):

    CustomBehaviorParty().set_party_is_blessing_enabled(True)

    bot_instance.Templates.Routines.UseCustomBehaviors(
        on_player_critical_death=BottingHelpers.botting_unrecoverable_issue,
        on_party_death=BottingHelpers.botting_unrecoverable_issue,
        on_player_critical_stuck=BottingHelpers.botting_unrecoverable_issue)

    bot_instance.Templates.Aggressive()

    # Set up the FSM states properly
    bot_instance.States.AddHeader("MAIN_LOOP")

    bot_instance.Map.Travel(target_map_id=393)
    bot_instance.Party.SetHardMode(False)

    enter_fow(bot_instance)
    a_tower_of_courage(bot_instance)
    b_the_wailing_lord(bot_instance)
    c_a_gift_of_griffons(bot_instance)
    d_the_eternal_forgemaster(bot_instance)
    e_defend_the_temple_of_war(bot_instance)
    f_restore_the_temple_of_war(bot_instance)
    # f_army_of_darkness(bot_instance)
    # h_khobay_the_betrayer(bot_instance)
    # i_tower_of_strength(bot_instance)
    # j_slaves_of_menzies(bot_instance)
    # k_the_hunt(bot_instance)

    bot_instance.States.AddHeader("END")

def enter_fow(bot_instance: Botting):
    bot_instance.States.AddHeader("ENTER_FOW")
    bot_instance.Move.XY(-9943, 1052, "go to Statue of Balthazar")
    bot_instance.States.AddCustomState(lambda: GLOBAL_CACHE.Player.SendChatCommand("kneel"), "kneel")
    bot_instance.Wait.ForTime(6_000)
    bot_instance.Dialogs.AtXY(-9943, 1052, 0x85, "ask to enter")
    bot_instance.Dialogs.AtXY(-9943, 1052, 0x86, "accept to enter")
    bot_instance.Wait.ForMapLoad(target_map_id=34) # we are in the dungeon
    bot_instance.Wait.ForTime(5_000)

def a_tower_of_courage(bot_instance: Botting):
    bot_instance.States.AddHeader("TOWER_OF_COURAGE")
    bot_instance.Move.XYAndInteractNPC(-23246, -1286, "go to NPC")
    bot_instance.Dialogs.AtXY(-23234, -1284, 0x80D401, "take quest")
    bot_instance.Wait.ForTime(500)
    killing_waypoints = [ (-22420, -1235), (-20279, 2014), (-19436, -1661), (-21602, -3423), (-19830, -5028), (-17302, -2836), (-17663, -1806), (-16255, -3204), (-13777, -2691), (-13778, -1415), (-15178, 291), (-16031, 462), (-13745, -1080), (-13189, -2068), (-14322, -2705) ]
    for waypoint in killing_waypoints:
        bot_instance.Move.XY(waypoint[0], waypoint[1], "killing waypoints")
    bot_instance.Move.XY(-14615, -2521, "tower of courage entrance")
    bot_instance.Move.XY(-15676, -1697, "go to NPC")
    bot_instance.Dialogs.AtXY(-15676, -1697, 0x80D407, "accept quest reward")

def b_the_wailing_lord(bot_instance: Botting):
    bot_instance.States.AddHeader("THE_WAILING_LORD")
    bot_instance.Move.XY(-15676, -1697, "go to NPC")
    bot_instance.Dialogs.AtXY(-15676, -1697, 0x80CC01, "take quest")
    killing_waypoints = [ (-15594, -1787), (-9054, -5817), (-6404, -3746), (-7173, 5210), (-13534, 7028), (-20421, 9260), (-22306, 10507), (-22173, 11606), (-21292, 12210), (-20535, 13583), (-20371, 14170), (-21649, 14992) ]
    # this step can be problematic as we aggro the whole area...
    for waypoint in killing_waypoints:
        bot_instance.Move.XY(waypoint[0], waypoint[1], "killing waypoints")

def c_a_gift_of_griffons(bot_instance: Botting):
    bot_instance.States.AddHeader("A_GIFT_OF_GRIFFONS")
    bot_instance.Move.XY(-21553, 15044, "go to NPC")
    bot_instance.Dialogs.AtXY(-15676, -1697, 0x80CD01, "take quest")
    back_to_tower_of_courage_waypoints = [ (-20156, 13936), (-21610, 12094), (-22001, 11269), (-22083, 10129), (-16889, 9422), (-12887, 6830), (-7763, 5477), (-6543, 143), (-7514, -4715), (-9637, -5615), (-14001, -2631) ]
    for waypoint in back_to_tower_of_courage_waypoints:
        bot_instance.Move.XY(waypoint[0], waypoint[1], "back to tower of courage waypoints")
    bot_instance.Move.XY(-14615, -2521, "tower of courage entrance")
    bot_instance.Move.XY(-15676, -1697, "go to NPC")
    bot_instance.Dialogs.AtXY(-15676, -1697, 0x80CC07, "accept quest reward")
    bot_instance.Dialogs.AtXY(-15676, -1697, 0x80CD07, "accept quest reward")

def d_the_eternal_forgemaster(bot_instance: Botting):
    bot_instance.States.AddHeader("THE_ETERNAL_FORGEMASTER")
    bot_instance.Move.XY(-7397, 11649, "go to NPC")
    bot_instance.Dialogs.AtXY(-15676, -1697, 0x80D101, "take quest")
    move_to_temple_of_war_waypoints =[ (-14262, -2802), (-8518, -5789), (-6502, -3809), (-6574, 402), (-3912, 5910), (1629, 6054) ]
    for waypoint in move_to_temple_of_war_waypoints:
        bot_instance.Move.XY(waypoint[0], waypoint[1], "move to temple of war waypoints")
    bot_instance.Move.XY(1688, 5088, "temple of war entrance")
    clean_temple_of_war_waypoints = [ (1732, 4726), (1766, 2076), (3723, 1183), (4443, -659), (3666, -2156), (1852, -2876), (-162, -2185), (-882, -198), (10, 1558) , (1470, 102), (1803, 373)]
    for waypoint in clean_temple_of_war_waypoints:
        bot_instance.Move.XY(waypoint[0], waypoint[1], "clean temple of war waypoints")
    bot_instance.Move.XY(1843, -140, "go to NPC")
    bot_instance.Dialogs.AtXY(1843, -140, 0x80D107, "accept quest reward")

def e_defend_the_temple_of_war(bot_instance: Botting):
    bot_instance.States.AddHeader("DEFEND_THE_TEMPLE_OF_WAR")
    bot_instance.Move.XY(1843, -140, "go to NPC")
    bot_instance.Dialogs.AtXY(1843, -140, 0x80CA01, "take quest")
    defend_temple_of_war_waypoints = [ (1853, -97), (1855, 396), (1464, 139), (255, 1334), (1686, 2443), (181, 1416), (1450, 134), (1225, -227), (1421, -695), (57, -2091), (1793, -3437), (3557, -1999), (2296, -714), (2496, -312), (2245, 99), (1867, -132) ]
    for waypoint in defend_temple_of_war_waypoints:
        bot_instance.Move.XY(waypoint[0], waypoint[1], "defend temple of war waypoints")
    bot_instance.Move.XY(1843, -140, "go to NPC")
    bot_instance.Dialogs.AtXY(1843, -140, 0x80CA07, "accept quest reward")

def f_restore_the_temple_of_war(bot_instance: Botting):

    bot_instance.States.AddHeader("RESTORE_THE_TEMPLE_OF_WAR")
    bot_instance.Move.XY(1843, -140, "go to NPC")
    bot_instance.Dialogs.AtXY(1843, -140, 0x80CF03, "take quest")
    bot_instance.Dialogs.AtXY(1843, -140, 0x80CF01, "take quest")

    destroy_seeds_of_corruptions_waypoints = [ (1835, -84), (1884, 328), (1488, 150), (164, 1407), (-713, -1896), (1016, -2905), (1800, -3383), (1742, -5728), (2486, -8672), (1095, -10997), (389, -10784), (-1323, -8762), (-1727, -8163), (-3336, -8777), (-6345, -11427), (-7621, -13201), (-8465, -15582) ]
    for waypoint in destroy_seeds_of_corruptions_waypoints:
        bot_instance.Move.XY(waypoint[0], waypoint[1], "destroy seeds of corruptions waypoints")

    reverse = destroy_seeds_of_corruptions_waypoints.copy()
    reverse.reverse()
    for waypoint in reverse:
        bot_instance.Move.XY(waypoint[0], waypoint[1], "move to temple of war waypoints")


def h_khobay_the_betrayer(bot_instance: Botting):
    bot_instance.States.AddHeader("KHOBAY_THE_BETRAYER")
    bot_instance.Move.XY(1843, -140, "go to NPC")
    bot_instance.Dialogs.AtXY(1843, -140, 0x80E003, "take quest")
    bot_instance.Dialogs.AtXY(1843, -140, 0x80E001, "take quest")

def x_army_of_darkness(bot_instance: Botting):
    bot_instance.States.AddHeader("ARMY_OF_DARKNESS")
    bot_instance.Move.XY(-7323, 11909, "go to NPC") # but we want to take that when e_the_eternal_forgemaster
    bot_instance.Dialogs.AtXY(-7323, 11909, 0x80CB01, "take quest")

def i_tower_of_strength(bot_instance: Botting):
    bot_instance.States.AddHeader("TOWER_OF_STRENGTH")

def j_slaves_of_menzies(bot_instance: Botting):
    bot_instance.States.AddHeader("SLAVES_OF_MENZIES")

def k_the_hunt(bot_instance: Botting):
    bot_instance.States.AddHeader("THE_HUNT")

bot = Botting("[DUNGEON] FoW")
bot.SetMainRoutine(bot_routine)

def main():
    bot.Update()
    bot.UI.draw_window()

if __name__ == "__main__":
    main()