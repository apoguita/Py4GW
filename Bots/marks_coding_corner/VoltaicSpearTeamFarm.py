import math
import os

import Py4GW
from Bots.marks_coding_corner.utils.loot_utils import set_autoloot_options_for_custom_bots
from HeroAI.cache_data import CacheData
from Py4GW_widget_manager import get_widget_handler
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import AutoInventoryHandler
from Py4GWCoreLib import Botting
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines
from Py4GWCoreLib import SharedCommandType
from Py4GWCoreLib import ThrottledTimer

from Py4GWCoreLib import ChatChannel
from Py4GWCoreLib.Builds.ShadowTheftDaggerSpammer import AssassinShadowTheftDaggerSpammer
from Py4GWCoreLib.Builds.ShadowTheftDaggerSpammer import BuildStatus
from Widgets.CombatPrep import CombatPrep


BOT_NAME = "Voltaic Spear Farm [BETA]"
TEXTURE = os.path.join(
    Py4GW.Console.get_projects_path(), "Bots", "marks_coding_corner", "textures", "voltaic_spear.png"
)
OUTPOST_TO_TRAVEL = GLOBAL_CACHE.Map.GetMapIDByName('Umbral Grotto')
VERDANT_CASCADES_MAP_ID = 566
SALVERS_EXILE_MAP_ID = 577
JUSTICIAR_THOMMIS_ROOM_MAP_ID = 620

VERDANT_CASCADES_TRAVEL_PATH: list[tuple[float, float]] = [
    (-19887, 6074),
    (-10273, 3251),
    (-6878, -329),
    (-3041, -3446),
    (3571, -9501),
    (4721, -10626),
    (10764, -6448),
    (13063, -4396),
    (18054, -3275),
    (20966, -6476),
    (25298, -9456),
]

ENTER_DUNGEON_PATH: list[tuple[float, float]] = [
    (-16797, 9251),
    (-17835, 12524),
]

SLAVERS_EXILE_PATH_PRE_PATH_1 = (-12590, -17740)
SALVERS_EXILE_TRAVEL_PATH_1: list[tuple[float, float]] = [
    (-13480, -16570),
    (-13500, -15750),
    (-12500, -15000),
    (-10400, -14800),
    (-10837, -13823),
    (-11500, -13300),
    (-12175, -12211),
    (-13400, -11500),
    (-13700, -9550),
    (-14100, -8600),
    (-15000, -7500),
    (-16000, -7112),
    (-17347, -7438),
]

SLAVERS_EXILE_PATH_PRE_PATH_2 = (-18781, -8064)
SALVERS_EXILE_TRAVEL_PATH_2: list[tuple[float, float]] = [
    (-19083, -10150),
    (-18500, -11500),
    (-17700, -12500),
    (-17663, -13497),
]


bot = Botting(BOT_NAME)
cache_data = CacheData()
combat_prep = CombatPrep(cache_data, '60', 'row')  # Use Widget class to flag heroes
is_party_flagged = False
last_flagged_x_y = (0, 0)
last_flagged_map_id = VERDANT_CASCADES_MAP_ID
use_assassin_skillbar = True
flag_timer = ThrottledTimer(3000)
auto_inventory_handler = AutoInventoryHandler()


def _on_party_wipe(bot: "Botting"):
    while GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
        yield from bot.helpers.Wait._for_time(1000)
        if not Routines.Checks.Map.MapValid():
            # Map invalid → release FSM and exit
            bot.config.FSM.resume()
            return

    ConsoleLog("Res Check", "We ressed retrying!")
    yield from bot.helpers.Wait._for_time(3000)
    player_x, player_y = GLOBAL_CACHE.Player.GetXY()
    shrine_2_x, shrine_2_y = (-18673, -7701)

    # Compute distances
    dist_to_shrine_2 = math.hypot(player_x - shrine_2_x, player_y - shrine_2_y)

    bot.config.FSM.pause()
    # Check if within earshot
    if GLOBAL_CACHE.Map.GetMapID() == JUSTICIAR_THOMMIS_ROOM_MAP_ID:
        if GLOBAL_CACHE.Party.IsPartyDefeated():
            yield from bot.helpers.Wait._for_time(10000)
            bot.config.FSM.jump_to_state_by_name("[H]Exit To Farm_3")
            bot.config.FSM.resume()
            return

        if dist_to_shrine_2 <= Range.Spellcast.value:
            ConsoleLog("Res Check", "Player is near Shrine 2 (Res Point 2)")
            bot.config.FSM.jump_to_state_by_name("[H]Justiciar Tommis pt2_8")
        else:
            ConsoleLog("Res Check", "Player is in beginning shrine")
            bot.config.FSM.jump_to_state_by_name("[H]Justiciar Tommis pt1_6")
    else:
        bot.Multibox.ResignParty()
        yield from bot.helpers.Wait._for_time(10000)  # Allow the widget to take the party back to town
        bot.config.FSM.jump_to_state_by_name("[H]Exit To Farm_3")
    bot.config.FSM.resume()
    return


def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))


def open_final_chest():
    def command_type_routine_in_message_is_active(account_email, shared_command_type):
        index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)

        if index == -1 or message is None:
            return False

        if message.Command != shared_command_type:
            return False
        return True

    yield from Routines.Yield.Agents.TargetNearestGadgetXY(-17461.00, -14258.00, 100)
    target = GLOBAL_CACHE.Player.GetTargetID()
    if target == 0:
        ConsoleLog("Messaging", "No target to interact with.")
        return
    sender_email = GLOBAL_CACHE.Player.GetAccountEmail()
    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    while command_type_routine_in_message_is_active(sender_email, SharedCommandType.InteractWithTarget):
        yield from Routines.Yield.wait(250)

    while command_type_routine_in_message_is_active(sender_email, SharedCommandType.PickUpLoot):
        yield from Routines.Yield.wait(1000)
    yield from Routines.Yield.wait(5000)

    for account in accounts:
        if not account.AccountEmail or sender_email == account.AccountEmail:
            continue
        ConsoleLog("Messaging", f"Ordering {account.AccountEmail} to interact with target: {target}", log=False)

        hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account.AccountEmail)
        if hero_ai_options is None:
            continue
        hero_ai_options.Combat = False

        GLOBAL_CACHE.ShMem.SendMessage(
            sender_email, account.AccountEmail, SharedCommandType.InteractWithTarget, (target, 0, 0, 0)
        )

        # Interacting with chest
        while command_type_routine_in_message_is_active(account.AccountEmail, SharedCommandType.InteractWithTarget):
            yield from Routines.Yield.wait(1000)

        # Looting
        while command_type_routine_in_message_is_active(account.AccountEmail, SharedCommandType.PickUpLoot):
            yield from Routines.Yield.wait(1000)

        yield from Routines.Yield.wait(5000)
        hero_ai_options.Combat = True
    yield


def handle_on_danger_flagging(bot: Botting):
    global combat_prep
    global is_party_flagged
    global last_flagged_x_y
    global last_flagged_map_id

    spread_formation = [[-200, -200], [200, -200], [-200, 0], [200, 0], [-200, 300], [0, 300], [200, 300]]

    while True:
        player_x, player_y = GLOBAL_CACHE.Player.GetXY()
        map_id = GLOBAL_CACHE.Map.GetMapID()

        # === If currently in danger and paused ===
        if Routines.Checks.Agents.InDanger() and bot.config.pause_on_danger_fn():
            bot.config.build_handler.status = BuildStatus.Kill  # type: ignore
            # If not flagged yet, flag once
            if not is_party_flagged:
                last_flagged_x_y = (player_x, player_y)
                last_flagged_map_id = map_id
                is_party_flagged = True
                combat_prep.cb_shouts_prep(shouts_button_pressed=True)
                combat_prep.cb_spirits_prep(st_button_pressed=True)
                combat_prep.cb_set_formation(spread_formation, False)
                yield from Routines.Yield.wait(2500)
                combat_prep.cb_set_formation([], True)

            elif last_flagged_map_id == map_id:
                last_x, last_y = last_flagged_x_y
                dx, dy = player_x - last_x, player_y - last_y
                dist_sq = dx * dx + dy * dy
                max_dist_sq = (Range.Spellcast.value * 1.50) ** 2

                # Only reflag (and wait) if too far from previous position
                if dist_sq > max_dist_sq:
                    last_flagged_x_y = (player_x, player_y)
                    combat_prep.cb_set_formation(spread_formation, False)
                    yield from Routines.Yield.wait(2500)
                    combat_prep.cb_set_formation([], True)

        # === No longer in danger ===
        else:
            bot.config.build_handler.status = BuildStatus.Wait  # type: ignore
            if is_party_flagged:
                combat_prep.cb_set_formation([], True)
                is_party_flagged = False
                last_flagged_x_y = (0, 0)
                last_flagged_map_id = VERDANT_CASCADES_MAP_ID

        yield from Routines.Yield.wait(1000)


def disable_hero_ai_leader_combat(bot: Botting):
    bot.OverrideBuild(AssassinShadowTheftDaggerSpammer())
    if isinstance(bot.config.build_handler, AssassinShadowTheftDaggerSpammer):
        acount_email = GLOBAL_CACHE.Player.GetAccountEmail()
        hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(acount_email)

        if hero_ai_options is None:
            return
        hero_ai_options.Combat = False
    yield


def toggle_hero_ai_team_combat(toggle_value: bool):
    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    for account in accounts:
        if account.AccountEmail:
            hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account.AccountEmail)
            if hero_ai_options is None:
                continue
            hero_ai_options.Combat = toggle_value
    yield from Routines.Yield.wait(1000)


def setup_hero_ai_and_custom_builds(bot: Botting):
    global use_assassin_skillbar

    if not use_assassin_skillbar:
        yield
        return

    primary_profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    if primary_profession != "Assassin" and use_assassin_skillbar:
        GLOBAL_CACHE.Player.SendFakeChat(
            ChatChannel.CHANNEL_WARNING, "You are not allowed to use this skill bar! Not Assassin main"
        )
        yield
        return

    bot.OverrideBuild(AssassinShadowTheftDaggerSpammer())
    yield from bot.config.build_handler.LoadSkillBar()
    yield from disable_hero_ai_leader_combat(bot)


def farm_dungeon(bot: Botting) -> None:
    set_autoloot_options_for_custom_bots(salvage_golds=False, module_active=True)
    widget_handler = get_widget_handler()
    widget_handler.enable_widget('HeroAI')
    widget_handler.enable_widget('Return to outpost on defeat')
    widget_handler.enable_widget('CombatPrep')
    bot.Properties.Enable('auto_combat')

    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))

    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)

    bot.States.AddHeader('Exit To Farm')
    bot.Properties.Disable('pause_on_danger')
    bot.Templates.Multibox_Aggressive()
    bot.Properties.Enable('auto_combat')
    bot.States.AddCustomState(lambda: setup_hero_ai_and_custom_builds(bot), "Set up leader combat stuff")
    bot.Party.SetHardMode(True)
    bot.Move.XYAndExitMap(-22735, 6339, target_map_id=VERDANT_CASCADES_MAP_ID)
    bot.Properties.Enable('pause_on_danger')

    bot.States.AddHeader("Enter Dungeon")
    bot.Templates.Multibox_Aggressive()
    bot.Properties.Enable('auto_combat')
    bot.States.AddManagedCoroutine('handle_on_danger_flagging', lambda: handle_on_danger_flagging(bot))
    bot.Move.FollowAutoPath(VERDANT_CASCADES_TRAVEL_PATH, "To the dungeon route")
    bot.Move.XYAndExitMap(25729, -9360, target_map_id=SALVERS_EXILE_MAP_ID)

    bot.States.AddHeader("Enter Dungeon Room")
    bot.Move.FollowAutoPath(ENTER_DUNGEON_PATH, "To the dungeon room route")
    bot.Move.XYAndExitMap(-18300, 12527, target_map_id=JUSTICIAR_THOMMIS_ROOM_MAP_ID)

    bot.States.AddHeader("Justiciar Tommis pt1")
    bot.Multibox.UsePConSet()
    bot.Multibox.UsePumpkinPie()
    bot.Templates.Multibox_Aggressive()
    bot.Properties.Enable('auto_combat')
    bot.States.AddCustomState(lambda: disable_hero_ai_leader_combat(bot), "Set up leader combat stuff")
    bot.States.AddManagedCoroutine('handle_on_danger_flagging', lambda: handle_on_danger_flagging(bot))

    bot.States.AddHeader("Justiciar Tommis pathing 1")
    bot.Move.XY(SLAVERS_EXILE_PATH_PRE_PATH_1[0], SLAVERS_EXILE_PATH_PRE_PATH_1[1], "Part 1 pre-route")
    bot.Move.FollowAutoPath(SALVERS_EXILE_TRAVEL_PATH_1, "Part 1 killing route")

    bot.States.AddHeader("Justiciar Tommis pt2")
    bot.Multibox.UsePumpkinPie()
    bot.Templates.Multibox_Aggressive()
    bot.Properties.Enable('auto_combat')
    bot.States.AddCustomState(lambda: disable_hero_ai_leader_combat(bot), "Set up leader combat stuff")
    bot.States.AddManagedCoroutine('handle_on_danger_flagging', lambda: handle_on_danger_flagging(bot))

    bot.States.AddHeader("Justiciar Tommis pathing 2")
    bot.Move.XY(SLAVERS_EXILE_PATH_PRE_PATH_2[0], SLAVERS_EXILE_PATH_PRE_PATH_2[1], "Part 2 pre-route")
    bot.Move.FollowAutoPath(SALVERS_EXILE_TRAVEL_PATH_2, "Part 2 killing route")

    bot.States.AddHeader("Chest Rewards")
    bot.Properties.Disable('pause_on_danger')
    bot.Wait.ForTime(5000)
    bot.Interact.WithGadgetAtXY(-17461.00, -14258.00, "Main runner claim rewards")
    bot.States.AddCustomState(open_final_chest, "Open final chest")
    bot.Wait.ForTime(15000)
    bot.States.AddCustomState(lambda: toggle_hero_ai_team_combat(True), "Enable combat for rewards claim (in case of disabled)")
    bot.States.RemoveManagedCoroutine('handle_on_danger_flagging')
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(3000)
    bot.Wait.UntilOnOutpost()
    bot.States.JumpToStepName('[H]Exit To Farm_3')


def additional_ui():
    global use_assassin_skillbar

    if PyImGui.begin_child("Additional Options:"):
        PyImGui.text("Additional Options:")
        PyImGui.separator()

        full_width = PyImGui.get_content_region_avail()[0]

        # --- Buttons ---
        if PyImGui.button("Run my custom setup [Need to be in outpost]", full_width):
            bot.StartAtStep("[H]Exit To Farm_3")

        if PyImGui.button("Start with default setup", full_width):
            bot.StartAtStep("[H]Voltaic Spear Farm [BETA]_1")

        PyImGui.separator()

        # --- Label + Checkbox ---
        PyImGui.text("Skill Bar Options:")
        PyImGui.spacing()

        new_value_use_assassin_skillbar = PyImGui.checkbox(
            "[A/Any]: Shadow Theft Dagger Spammer", use_assassin_skillbar  # type: ignore
        )
        if new_value_use_assassin_skillbar != use_assassin_skillbar:
            ConsoleLog(BOT_NAME, f"Use SkillBar: {new_value_use_assassin_skillbar}")
            use_assassin_skillbar = new_value_use_assassin_skillbar

        PyImGui.end_child()


bot.SetMainRoutine(farm_dungeon)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE, main_child_dimensions=(400, 450), additional_ui=additional_ui)


if __name__ == "__main__":
    main()
