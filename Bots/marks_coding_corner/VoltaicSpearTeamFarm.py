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
from Widgets.CombatPrep import CombatPrep

# from Py4GWCoreLib import GLOBAL_CACHE
# from Py4GWCoreLib import Routines
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Builds import AutoCombat

from Py4GWCoreLib import ActionQueueManager
from Py4GWCoreLib import Player
from Py4GWCoreLib import Weapon

# from Py4GWCoreLib import Range
from Py4GWCoreLib import Profession
from Py4GWCoreLib import Agent
from Py4GWCoreLib import Checks


# =========================================== BUILD ==================================================
class BuildStatus:
    Kill = 'kill'
    Wait = 'wait'


class AssassinShadowTheftDaggerSpammer(BuildMgr):
    def __init__(self):
        super().__init__(
            name="Assassin Shadow Theft Dagger Spammer",
            required_primary=Profession.Assassin,
            required_secondary=Profession.Warrior,  # change if needed
            template_code="OwFjUNd8ITPPOMMMHMvl0k6Pk1A",
            skills=[
                GLOBAL_CACHE.Skill.GetID("Exhausting_Assault"),
                GLOBAL_CACHE.Skill.GetID("Jagged_Strike"),
                GLOBAL_CACHE.Skill.GetID("Fox_Fangs"),
                GLOBAL_CACHE.Skill.GetID("Death_Blossom"),
                GLOBAL_CACHE.Skill.GetID("Asuran_Scan"),
                GLOBAL_CACHE.Skill.GetID("I_Am_Unstoppable"),
                GLOBAL_CACHE.Skill.GetID("Critical_Eye"),
                GLOBAL_CACHE.Skill.GetID("Shadow_Theft"),
            ],
        )
        self.auto_combat_handler = AutoCombat()

        # === Skill References ===
        (
            self.exhausting_assault,
            self.jagged_strike,
            self.fox_fangs,
            self.death_blossom,
            self.asuran_scan,
            self.i_am_unstoppable,
            self.critical_eye,
            self.shadow_theft,
        ) = self.skills

        self.status = BuildStatus.Wait
        self.last_dagger_attack_used = None

    def swap_to_daggers(self):
        while GLOBAL_CACHE.Agent.GetWeaponType(Player.GetAgentID())[0] != Weapon.Daggers:
            yield from Routines.Yield.Keybinds.ActivateWeaponSet(1)

    def swap_to_shield_set(self):
        while GLOBAL_CACHE.Agent.GetWeaponType(Player.GetAgentID())[0] == Weapon.Daggers:
            yield from Routines.Yield.Keybinds.ActivateWeaponSet(2)

    def ProcessSkillCasting(self):
        if not (
            Routines.Checks.Map.IsExplorable()
            and Routines.Checks.Player.CanAct()
            and Routines.Checks.Map.IsExplorable()
            and Routines.Checks.Skills.CanCast()
        ):
            ActionQueueManager().ResetAllQueues()
            yield from Routines.Yield.wait(1000)
            return

        if self.status == BuildStatus.Wait:
            yield from self.swap_to_shield_set()
            yield from Routines.Yield.wait(100)
            self.last_dagger_attack_used = None
            return

        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        has_critical_eye = Routines.Checks.Effects.HasBuff(player_agent_id, self.critical_eye)
        has_i_am_unstoppable = Routines.Checks.Effects.HasBuff(player_agent_id, self.i_am_unstoppable)
        has_shadow_theft = Routines.Checks.Effects.HasBuff(player_agent_id, self.shadow_theft)
        # px, py = GLOBAL_CACHE.Player.GetXY()

        if self.status == BuildStatus.Kill:
            yield from self.swap_to_daggers()
            yield from Routines.Yield.Keybinds.TargetNearestEnemy()
            nearest_enemy_agent_id = GLOBAL_CACHE.Player.GetTargetID()
            nearest_enemy_agent = Agent.GetAgentByID(nearest_enemy_agent_id)
            player_x, player_y = GLOBAL_CACHE.Player.GetXY()
            enemy_x, enemy_y = nearest_enemy_agent.x, nearest_enemy_agent.y

            # --- Compute squared distance between player and enemy ---
            dx = enemy_x - player_x
            dy = enemy_y - player_y
            dist_sq = dx * dx + dy * dy

            yield from Routines.Yield.Keybinds.Interact()
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.critical_eye)) and not has_critical_eye:
                yield from Routines.Yield.Skills.CastSkillID(self.critical_eye, aftercast_delay=100)
                return

            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.i_am_unstoppable)) and not has_i_am_unstoppable:
                yield from Routines.Yield.Skills.CastSkillID(self.i_am_unstoppable, aftercast_delay=100)
                return

            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.asuran_scan)) and nearest_enemy_agent_id:
                if (
                    nearest_enemy_agent.is_living
                    and nearest_enemy_agent.living_agent
                    and not nearest_enemy_agent.living_agent.is_spawned
                ):
                    GLOBAL_CACHE.Player.Interact(nearest_enemy_agent_id, True)
                    yield from Routines.Yield.Skills.CastSkillID(self.asuran_scan, aftercast_delay=250)
                    return

            if (
                nearest_enemy_agent_id
                and (yield from Routines.Yield.Skills.IsSkillIDUsable(self.shadow_theft))
                and not has_shadow_theft
                or (yield from Routines.Yield.Skills.IsSkillIDUsable(self.shadow_theft))
                and dist_sq <= Range.Area.value**2
            ):
                if (
                    nearest_enemy_agent.is_living
                    and nearest_enemy_agent.living_agent
                    and not nearest_enemy_agent.living_agent.is_spawned
                ):
                    GLOBAL_CACHE.Player.Interact(nearest_enemy_agent_id, True)
                    yield from Routines.Yield.Skills.CastSkillID(self.shadow_theft, aftercast_delay=500)
                    return

            # --- Only proceed if within adjacent range ---
            if dist_sq <= Range.Adjacent.value**2:
                if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.exhausting_assault)):
                    nearest_enemy_agent = GLOBAL_CACHE.Agent.GetAgentByID(nearest_enemy_agent_id)
                    if not nearest_enemy_agent:
                        return  # no valid target

                    MAX_RANGE_SQ = Range.Adjacent.value**2

                    # --- Wait for Jagged Strike to become usable ---
                    while not (yield from Routines.Yield.Skills.IsSkillIDUsable(self.jagged_strike)):
                        yield from Routines.Yield.wait(50)

                    # --- Confirm target is still in range before chaining ---
                    player_x, player_y = GLOBAL_CACHE.Player.GetXY()
                    dx, dy = nearest_enemy_agent.x - player_x, nearest_enemy_agent.y - player_y
                    if dx * dx + dy * dy > MAX_RANGE_SQ:
                        print("[Chain] Target too far for dagger chain.")
                        return

                    # --- Queue chain execution ---
                    jagged_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.jagged_strike)
                    exhausting_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.exhausting_assault)

                    # Interact and prepare to cast
                    GLOBAL_CACHE.Player.Interact(nearest_enemy_agent_id, True)
                    ActionQueueManager().ResetAllQueues()

                    # --- Cast Jagged Strike first ---
                    yield from Routines.Yield.Keybinds.TargetNearestEnemy()
                    yield from Routines.Yield.Keybinds.UseSkill(jagged_slot)

                    # --- Small wait to allow animation start ---
                    yield from Routines.Yield.wait(350)

                    # --- Cast Exhausting Assault right after ---
                    if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.exhausting_assault)):
                        yield from Routines.Yield.Keybinds.UseSkill(exhausting_slot)
                        yield from Routines.Yield.Skills.CastSkillID(self.exhausting_assault, aftercast_delay=100)

                # === Check that Death Blossom is ready (so full chain can be executed) ===
            if (yield from Routines.Yield.Skills.IsSkillIDUsable(self.death_blossom)):
                jagged = self.jagged_strike
                fox_fangs = self.fox_fangs
                death_blossom = self.death_blossom

                # === Check distance first ===
                player_x, player_y = GLOBAL_CACHE.Player.GetXY()
                target_x, target_y = GLOBAL_CACHE.Agent.GetXY(nearest_enemy_agent_id)
                dist_sq = (player_x - target_x) ** 2 + (player_y - target_y) ** 2
                if dist_sq > Range.Adjacent.value**2:
                    return False  # Too far, skip chain

                # === Lock on and clear old actions ===
                GLOBAL_CACHE.Player.Interact(nearest_enemy_agent_id, True)
                ActionQueueManager().ResetAllQueues()

                # === Execute chain sequence ===
                # Jagged Strike
                if (yield from Routines.Yield.Skills.IsSkillIDUsable(jagged)):
                    skill_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(jagged)
                    yield from Routines.Yield.Keybinds.TargetNearestEnemy()
                    yield from Routines.Yield.Keybinds.UseSkill(skill_slot)
                    yield from Routines.Yield.wait(200)  # small follow-up delay

                    # Fox Fangs
                    if (yield from Routines.Yield.Skills.IsSkillIDUsable(fox_fangs)):
                        skill_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(fox_fangs)
                        yield from Routines.Yield.Keybinds.UseSkill(skill_slot)
                        yield from Routines.Yield.wait(200)  # roughly same cast rhythm

                        # Death Blossom
                        if (yield from Routines.Yield.Skills.IsSkillIDUsable(death_blossom)):
                            skill_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(death_blossom)
                            yield from Routines.Yield.Keybinds.UseSkill(skill_slot)
                            yield from Routines.Yield.wait(500)  # DB has longer aftercast

            return


# ========================================================================================

BOT_NAME = "Voltaic Spear Farm"
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
    (-17500, -14250),
]


bot = Botting(BOT_NAME)
cache_data = CacheData()
combat_prep = CombatPrep(cache_data, '60', 'row')  # Use Widget class to flag heroes
is_party_flagged = False
last_flagged_x_y = (0, 0)
last_flagged_map_id = VERDANT_CASCADES_MAP_ID
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

    # Check if within earshot
    if GLOBAL_CACHE.Map.GetMapID() == JUSTICIAR_THOMMIS_ROOM_MAP_ID:
        if dist_to_shrine_2 <= Range.Spellcast.value:
            bot.config.FSM.pause()
            ConsoleLog("Res Check", "Player is near Shrine 2 (Res Point 2)")
            bot.States.JumpToStepName("[H]Justiciar Tommis pt2_8")
            bot.config.FSM.resume()
        else:
            bot.config.FSM.pause()
            ConsoleLog("Res Check", "Player is in beginning shrine")
            bot.States.JumpToStepName("[H]Justiciar Tommis pt1_6")
            bot.config.FSM.resume()

    else:
        bot.config.FSM.pause()
        bot.Multibox.ResignParty()
        yield from bot.helpers.Wait._for_time(10000)  # Allow the widget to take the party back to town
        bot.States.JumpToStepName("[H]Exit To Farm_3")
        bot.config.FSM.resume()


def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))


def open_final_chest():
    yield from Routines.Yield.Agents.TargetNearestGadgetXY(-17461.00, -14258.00, 100)
    target = GLOBAL_CACHE.Player.GetTargetID()
    if target == 0:
        ConsoleLog("Messaging", "No target to interact with.")
        return
    sender_email = GLOBAL_CACHE.Player.GetAccountEmail()
    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    yield from Routines.Yield.wait(5000)  # initial 3 second wait

    for account in accounts:
        if sender_email == account.AccountEmail:
            continue
        ConsoleLog("Messaging", f"Ordering {account.AccountEmail} to interact with target: {target}", log=False)
        GLOBAL_CACHE.ShMem.SendMessage(
            sender_email, account.AccountEmail, SharedCommandType.InteractWithTarget, (target, 0, 0, 0)
        )
        yield from Routines.Yield.wait(5000)
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
                max_dist_sq = (Range.Spellcast.value * 1.25) ** 2

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
    if isinstance(bot.config.build_handler, AssassinShadowTheftDaggerSpammer):
        acount_email = GLOBAL_CACHE.Player.GetAccountEmail()
        hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(acount_email)

        if hero_ai_options is None:
            return
        hero_ai_options.Combat = False
    yield


def farm_dungeon(bot: Botting) -> None:
    set_autoloot_options_for_custom_bots(salvage_golds=False, module_active=True)
    widget_handler = get_widget_handler()
    widget_handler.enable_widget('Return to outpost on defeat')
    widget_handler.enable_widget('CombatPrep')
    bot.Properties.Enable('auto_combat')
    # handle turning off combat for heroAI entirely

    # events
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    # end events

    bot.States.AddHeader(BOT_NAME)
    bot.OverrideBuild(AssassinShadowTheftDaggerSpammer())

    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OUTPOST_TO_TRAVEL)

    bot.States.AddHeader('Exit To Farm')
    bot.Properties.Disable('pause_on_danger')
    bot.Templates.Multibox_Aggressive()
    bot.Properties.Disable("auto_inventory_management")
    bot.Properties.Enable('auto_combat')
    bot.States.AddCustomState(lambda: disable_hero_ai_leader_combat(bot), "Disable Leader Combat")
    bot.States.AddManagedCoroutine('handle_on_danger_flagging', lambda: handle_on_danger_flagging(bot))
    bot.Party.SetHardMode(True)
    bot.Move.XYAndExitMap(-22735, 6339, target_map_id=VERDANT_CASCADES_MAP_ID)
    bot.Properties.Enable('pause_on_danger')

    bot.States.AddHeader("Enter Dungeon")
    bot.Templates.Multibox_Aggressive()
    bot.Properties.Disable("auto_inventory_management")
    bot.Properties.Enable('auto_combat')
    bot.Move.FollowAutoPath(VERDANT_CASCADES_TRAVEL_PATH, "To the dungeon route")
    bot.Move.XYAndExitMap(25729, -9360, target_map_id=SALVERS_EXILE_MAP_ID)

    bot.States.AddHeader("Enter Dungeon Room")
    bot.Move.FollowAutoPath(ENTER_DUNGEON_PATH, "To the dungeon room route")
    bot.Move.XYAndExitMap(-18300, 12527, target_map_id=JUSTICIAR_THOMMIS_ROOM_MAP_ID)

    bot.States.AddHeader("Justiciar Tommis pt1")
    bot.Multibox.UsePConSet()
    bot.Multibox.UsePumpkinPie()
    bot.Templates.Multibox_Aggressive()
    bot.Properties.Disable("auto_inventory_management")
    bot.Properties.Enable('auto_combat')
    bot.States.AddManagedCoroutine('handle_on_danger_flagging', lambda: handle_on_danger_flagging(bot))
    bot.States.AddHeader("Justiciar Tommis pathing 1")
    bot.Move.XY(SLAVERS_EXILE_PATH_PRE_PATH_1[0], SLAVERS_EXILE_PATH_PRE_PATH_1[1], "Part 1 pre-route")
    bot.Move.FollowAutoPath(SALVERS_EXILE_TRAVEL_PATH_1, "Part 1 killing route")

    bot.States.AddHeader("Justiciar Tommis pt2")
    bot.States.AddManagedCoroutine('handle_on_danger_flagging', lambda: handle_on_danger_flagging(bot))
    bot.Templates.Multibox_Aggressive()
    bot.Properties.Disable("auto_inventory_management")
    bot.Properties.Enable('auto_combat')
    bot.States.AddHeader("Justiciar Tommis pathing 2")
    bot.Move.XY(SLAVERS_EXILE_PATH_PRE_PATH_2[0], SLAVERS_EXILE_PATH_PRE_PATH_2[1], "Part 2 pre-route")
    bot.Move.FollowAutoPath(SALVERS_EXILE_TRAVEL_PATH_2, "Part 2 killing route")

    bot.Properties.Disable('pause_on_danger')
    bot.Wait.ForTime(20000)
    bot.Interact.WithGadgetAtXY(-17461.00, -14258.00, "Main runner claim rewards")
    bot.States.AddCustomState(open_final_chest, "Open final chest")

    bot.Wait.ForTime(10000)
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(3000)
    bot.Wait.UntilOnOutpost()
    bot.States.JumpToStepName('[H]Exit To Farm_3')


def additoinal_ui():
    if PyImGui.begin_child("Additional Options:"):
        PyImGui.text("Additional Options:")
        PyImGui.separator()

        full_width = PyImGui.get_content_region_avail()[0]
        # --- Draw two equal-width buttons on same line ---
        if PyImGui.button("Run my custom setup [Need to be in outpost]", full_width):
            bot.StartAtStep("[H]Exit To Farm_3")

        if PyImGui.button("Start with default setup", full_width):
            bot.StartAtStep("[H]Voltaic Spear Farm_1")

        PyImGui.end_child()


bot.SetMainRoutine(farm_dungeon)


def main():
    bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE, main_child_dimensions=(350, 450), addtional_ui=additoinal_ui)


if __name__ == "__main__":
    main()
