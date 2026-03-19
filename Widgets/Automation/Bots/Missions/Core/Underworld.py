
from Py4GWCoreLib import Botting, Routines, Agent, AgentArray, Player, Utils, AutoPathing, GLOBAL_CACHE, ConsoleLog, Map, Pathing, FlagPreference, Party, IniHandler
import os
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Sources.oazix.CustomBehaviors.gui.flag_panel.flag_backward_grid_placement import FlagBackwardGridPlacement
from Sources.oazix.CustomBehaviors.primitives.botting.botting_helpers import BottingHelpers
from Sources.oazix.CustomBehaviors.primitives.botting.botting_manager import BottingManager
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.botting.botting_fsm_helper import BottingFsmHelpers
from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from pathlib import Path
import PyImGui
import Py4GW

#0x84
#3078 Dhuum Ghost buff
MODULE_NAME = "Underworld Helper"
MODULE_ICON = "Textures/Module_Icons/Underworld.png"

# Override the help window
BOT_NAME = "Underworld Helper"
_ini_file = os.path.join(Py4GW.Console.get_projects_path(), "Widgets", "Config", "UnderworldBot.ini")
_ini = IniHandler(_ini_file)
bot = Botting(BOT_NAME, config_draw_path=True, upkeep_auto_inventory_management_active=True)
bot.Templates.Aggressive()
# Override the help window
bot.UI.override_draw_help(lambda: _draw_help())
bot.UI.override_draw_config(lambda: _draw_settings())  # Disable default config window
MAIN_LOOP_HEADER_NAME = ""
_entered_dungeon: bool = False  # set True once map 72 is loaded; watchdog uses this


def _mark_entered_dungeon() -> None:
    global _entered_dungeon
    _entered_dungeon = True


class InventorySettings:
    """Settings for between-run inventory management."""
    RefillEnabled:    bool = bool(_ini.read_bool(BOT_NAME, "inv_refill_enabled", True))
    RestockKits:      bool = bool(_ini.read_bool(BOT_NAME, "inv_restock_kits",   True))
    RestockCons:      bool = bool(_ini.read_bool(BOT_NAME, "inv_restock_cons",   True))
    DepositMaterials: bool = bool(_ini.read_bool(BOT_NAME, "inv_deposit_mats",   True))

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, "inv_refill_enabled", str(cls.RefillEnabled))
        _ini.write_key(BOT_NAME, "inv_restock_kits",   str(cls.RestockKits))
        _ini.write_key(BOT_NAME, "inv_restock_cons",   str(cls.RestockCons))
        _ini.write_key(BOT_NAME, "inv_deposit_mats",   str(cls.DepositMaterials))


class BotSettings:
    RestoreVale: bool = True           #Working
    WrathfullSpirits: bool = True      #Working
    EscortOfSouls: bool = True         #Working
    UnwantedGuests: bool = True        #Working but can be improved
    RestoreWastes: bool = True          #Working
    ServantsOfGrenth: bool = True       #Working
    PassTheMountains: bool = True       #Working
    RestoreMountains: bool = True      #Working
    DeamonAssassin: bool = True        #Working
    RestorePlanes: bool = True          #Working
    TheFourHorsemen: bool = True        #Working
    RestorePools: bool = True           #Working but sometimes the Reaper dies
    TerrorwebQueen: bool = True         #Working
    RestorePit: bool = True            #Working
    ImprisonedSpirits: bool = True     #Working but can be improved
    Repeat: bool = False                 #Working
    UseCons: bool = True                #Use Consumables


# Precomputed spread points keep Servants of Grenth flags spaced without extra imports.
def _get_custom_behavior(initialize_if_needed: bool = True):
    loader = CustomBehaviorLoader()
    behavior = loader.custom_combat_behavior

    if behavior is None and initialize_if_needed:
        loader.initialize_custom_behavior_candidate()
        behavior = loader.custom_combat_behavior

    return behavior


def _set_custom_utility_enabled(
    enabled: bool,
    *,
    skill_names: tuple[str, ...] = (),
    class_names: tuple[str, ...] = (),
) -> bool:
    behavior = _get_custom_behavior(initialize_if_needed=True)
    if behavior is None:
        return False

    for utility in behavior.get_skills_final_list():
        utility_skill_name = getattr(getattr(utility, "custom_skill", None), "skill_name", None)
        utility_class_name = utility.__class__.__name__

        if utility_skill_name in skill_names or utility_class_name in class_names:
            utility.is_enabled = enabled
            return True

    return False


def _toggle_wait_if_aggro(enabled: bool) -> None:
    _set_custom_utility_enabled(
        enabled,
        skill_names=("wait_if_in_aggro",),
        class_names=("WaitIfInAggroUtility",),
    )

def _toggle_wait_for_party(enabled: bool) -> None:
    _set_custom_utility_enabled(
        enabled,
        skill_names=("wait_if_party_member_too_far",),
        class_names=("WaitIfPartyMemberTooFarUtility",),
    )

def _toggle_move_if_aggro(enabled: bool) -> None:
    _set_custom_utility_enabled(
        enabled,
        skill_names=("move_to_party_member_if_in_aggro",),
        class_names=("MoveToPartyMemberIfInAggroUtility",),
    )

def _toggle_move_to_enemy_if_close_enough(enabled: bool) -> None:
    _set_custom_utility_enabled(
        enabled,
        skill_names=("move_to_enemy_if_close_enough",),
        class_names=("MoveToEnemyIfCloseEnoughUtility",),
    )

def _toggle_move_to_party_member_if_dead(enabled: bool) -> None:
    _set_custom_utility_enabled(
        enabled,
        skill_names=("move_to_party_member_if_dead",),
        class_names=("MoveToPartyMemberIfDeadUtility",),
    )

def _toggle_wait_if_party_member_needs_to_loot(enabled: bool) -> None:
    _set_custom_utility_enabled(
        enabled,
        skill_names=("wait_if_party_member_needs_to_loot",),
        class_names=("WaitIfPartyMemberNeedsToLootUtility",),
    )

def _toggle_lock(enabled: bool) -> None:
    _set_custom_utility_enabled(
        enabled,
        skill_names=("wait_if_lock_taken",),
        class_names=("WaitIfLockTakenUtility",),
    )


def _toggle_wait_if_party_member_mana_too_low(enabled: bool) -> None:
    _set_custom_utility_enabled(
        enabled,
        skill_names=("wait_if_party_member_mana_too_low",),
        class_names=("WaitIfPartyMemberManaTooLowUtility",),
    )


def _setup_custom_behavior_integration(bot_instance: Botting) -> None:
    behavior = _get_custom_behavior(initialize_if_needed=True)
    if behavior is None:
        ConsoleLog(BOT_NAME, "[CB] Kein Custom-Behavior gefunden. Bot läuft ohne CB-Integration.", Py4GW.Console.MessageType.Warning)
        return

    _ensure_custom_botting_skills_enabled()
    BottingFsmHelpers.SetBottingBehaviorAsAggressive(bot_instance)
    BottingFsmHelpers.UseCustomBehavior(
        bot_instance,
        on_player_critical_death=BottingHelpers.botting_unrecoverable_issue,
        on_party_death=BottingHelpers.botting_unrecoverable_issue,
        on_player_critical_stuck=BottingHelpers.botting_unrecoverable_issue,
    )


def _sync_custom_behavior_runtime() -> None:
    loader = CustomBehaviorLoader()
    loader.ensure_botting_daemon_running()

    behavior = loader.custom_combat_behavior
    if behavior is None:
        loader.initialize_custom_behavior_candidate()


def _ensure_custom_botting_skills_enabled() -> None:
    """
    Erzwingt aktivierte Botting-Skills für diesen Bot beim Start,
    auch wenn sie in der globalen CB-Konfiguration zuvor deaktiviert wurden.
    """
    manager = BottingManager()

    required_skill_keys = {
        "wait_if_party_member_too_far",
        "wait_if_in_aggro",
        "move_to_party_member_if_in_aggro",
    }

    changed = False

    for entry in manager.aggressive_skills:
        if entry.name in required_skill_keys and not entry.enabled:
            entry.enabled = True
            changed = True

    if changed:
        manager.save()
        ConsoleLog(BOT_NAME, "[CB] Benötigte Botting-Skills wurden für diesen Bot aktiviert.", Py4GW.Console.MessageType.Info)


def _reactivate_custom_behavior_for_step(bot_instance: Botting, step_label: str) -> None:
    """
    Re-aktiviert die benötigte CB-Integration vor jedem größeren Schritt/Questabschnitt.
    """
    behavior = _get_custom_behavior(initialize_if_needed=True)
    if behavior is None:
        ConsoleLog(BOT_NAME, f"[CB] Kein Behavior für Schritt '{step_label}' verfügbar.", Py4GW.Console.MessageType.Warning)
        return

    _ensure_custom_botting_skills_enabled()
    BottingFsmHelpers.SetBottingBehaviorAsAggressive(bot_instance)
    BottingFsmHelpers.UseCustomBehavior(
        bot_instance,
        on_player_critical_death=BottingHelpers.botting_unrecoverable_issue,
        on_party_death=BottingHelpers.botting_unrecoverable_issue,
        on_player_critical_stuck=BottingHelpers.botting_unrecoverable_issue,
    )

def _enqueue_section(bot_instance: Botting, attr_name: str, label: str, section_fn):
    bot_instance.States.AddHeader(label)
    bot_instance.States.AddCustomState(
        lambda l=label: _reactivate_custom_behavior_for_step(bot_instance, l),
        f"[Setup] {label}",
    )
    section_fn(bot_instance)

def _add_header_with_name(bot_instance: Botting, step_name: str) -> str:
    header_name = f"[H]{step_name}_{bot_instance.config.get_counter('HEADER_COUNTER')}"
    bot_instance.config.FSM.AddYieldRoutineStep(
        name=header_name,
        coroutine_fn=lambda: Routines.Yield.wait(100),
    )
    return header_name

def _restart_main_loop(bot_instance: Botting, reason: str) -> None:
    global _entered_dungeon
    _entered_dungeon = False
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


def _flag_both(party_pos: int, flag_index: int, x, y) -> None:
    # CB: setzt Flagge per Shared Memory
    _set_flag_position(flag_index, x, y)
    # HeroAI / native GW: setzt Flagge direkt
    agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(party_pos)
    if agent_id:
        GLOBAL_CACHE.Party.Heroes.FlagHero(agent_id, x, y)


def _enqueue_spread_flags(bot_instance: Botting, flag_points: list[tuple[int, int]]) -> None:
    """Clear flags, auto-assign emails, then set CB + HeroAI flags for each position.
    Only heroes are flagged (player/party leader is excluded automatically)."""
    bot_instance.States.AddCustomState(
        lambda: CustomBehaviorParty().party_flagging_manager.clear_all_flags(),
        "Clear Flags",
    )
    bot_instance.States.AddCustomState(
        lambda: _auto_assign_flag_emails(),
        "Assign Flag Emails",
    )
    for idx, (flag_x, flag_y) in enumerate(flag_points):  # 0-based for CB
        bot_instance.States.AddCustomState(
            lambda i=idx, x=flag_x, y=flag_y: _set_flag_position(i, x, y),
            f"Set CB Flag {idx}",
        )
        bot_instance.Party.FlagHero(idx + 1, flag_x, flag_y)  # 1-based for native GW

def _auto_assign_flag_emails() -> None:
    CustomBehaviorParty().party_flagging_manager.auto_assign_emails_if_none_assigned()


def _set_flag_position(index: int, flag_x: int, flag_y: int) -> None:
    CustomBehaviorParty().party_flagging_manager.set_flag_position(index, flag_x, flag_y)


def WaitTillQuestDone(bot_instance: Botting) -> None:
    from Py4GWCoreLib.Quest import Quest
    bot_instance.Wait.UntilCondition(
        lambda: (Quest.GetActiveQuest() > 0) and Quest.IsQuestCompleted(Quest.GetActiveQuest())
    )



def _move_with_unstuck(
    bot_instance: Botting,
    target_x: float,
    target_y: float,
    step_name: str = "",
    stuck_check_ms: int = 2000,
    stuck_threshold: float = 80.0,
    backup_ms: int = 1000,
    max_retries: int = 30,
    timeout: int = 60_000,
) -> None:
    """Move to (target_x, target_y) using navmesh A* pathfinding.

    1. Build a navmesh path via AutoPathing().get_path_to() – walks around walls.
    2. Follow it with FollowPath (which already handles stuck/retry internally).
    3. If we get stuck anyway: /stuck → walk backwards → rebuild path and retry.
       After max_retries give up with a warning.
    """
    import math

    def _coro():
        import heapq as _heapq
        from Py4GWCoreLib.Pathing import AutoPathing, AStar, AStarNode, chaikin_smooth_path, densify_path2d
        from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist
        tolerance = 150.0
        tx, ty = target_x, target_y

        # ── Local A* subclass: treats blacklisted-enemy trapezoids as walls ──
        class _AStarBlocking(AStar):
            def __init__(
                self,
                navmesh,
                avoid_points,
                hard_block_radius: float = 50.0,
                soft_avoid_radius: float = 100.0,
                soft_penalty: float = 1400.0,
            ):
                super().__init__(navmesh)
                self._avoid_points = avoid_points
                self._hard_block_radius = hard_block_radius
                self._soft_avoid_radius = soft_avoid_radius
                self._soft_penalty = soft_penalty

            def _min_dist_to_avoid_points(self, node_id: int) -> float:
                if not self._avoid_points:
                    return float("inf")
                nx, ny = self.navmesh.get_position(node_id)
                return min(math.hypot(nx - ax, ny - ay) for ax, ay in self._avoid_points)

            def search(self, start_pos, goal_pos):
                s_id = self.navmesh.find_trapezoid_id_by_coord(start_pos)
                g_id = self.navmesh.find_trapezoid_id_by_coord(goal_pos)
                if s_id is None or g_id is None:
                    return False
                ol: list = []
                _heapq.heappush(ol, AStarNode(s_id, 0, self.heuristic(s_id, g_id)))
                came: dict = {}
                cost: dict = {s_id: 0}
                while ol:
                    cur = _heapq.heappop(ol)
                    if cur.id == g_id:
                        self._reconstruct(came, g_id)
                        self.path.insert(0, start_pos)
                        self.path.append(goal_pos)
                        return True
                    for nb in self.navmesh.get_neighbors(cur.id):
                        d = self._min_dist_to_avoid_points(nb)
                        if d <= self._hard_block_radius:
                            continue
                        penalty = 0.0
                        if d < self._soft_avoid_radius:
                            penalty = ((self._soft_avoid_radius - d) / self._soft_avoid_radius) * self._soft_penalty
                        nc = cost[cur.id] + self.heuristic(cur.id, nb) + penalty
                        if nb not in cost or nc < cost[nb]:
                            cost[nb] = nc
                            _heapq.heappush(ol, AStarNode(nb, nc, nc + self.heuristic(nb, g_id), cur.id))
                            came[nb] = cur.id
                return False

        # ── Collect positions of blacklisted enemies for soft avoidance ───
        _avoid_points: list[tuple[float, float]] = []
        _navmesh = AutoPathing().get_navmesh()
        if _navmesh:
            _bl = EnemyBlacklist()
            for _eid in AgentArray.GetEnemyArray():
                if _bl.is_blacklisted(_eid) and Agent.IsAlive(_eid):
                    _ex, _ey = Agent.GetXY(_eid)
                    _avoid_points.append((_ex, _ey))

        for attempt in range(max_retries + 1):
            px, py = Player.GetXY()
            if math.sqrt((tx - px) ** 2 + (ty - py) ** 2) <= tolerance:
                return  # already there

            # ── Step 1: build navmesh path ────────────────────────────────
            ConsoleLog(
                BOT_NAME,
                f"[Move] Building path to ({tx:.0f},{ty:.0f}) attempt {attempt + 1}/{max_retries + 1}",
                Py4GW.Console.MessageType.Info,
            )
            # Use obstacle-aware A* when blacklisted enemies block the way;
            # fall back to standard get_path_to otherwise.
            path = None
            if _avoid_points and _navmesh:
                _cpx, _cpy = Player.GetXY()
                _ast = _AStarBlocking(_navmesh, _avoid_points)
                if _ast.search((_cpx, _cpy), (tx, ty)):
                    _raw = _ast.get_path()
                    _sm  = _navmesh.smooth_path_by_los(_raw, margin=100, step_dist=200.0)
                    path = densify_path2d(_sm)
            if path is None:
                path = yield from AutoPathing().get_path_to(tx, ty)

            if path:
                # ── Step 2: follow the computed path ─────────────────────
                reached = yield from Routines.Yield.Movement.FollowPath(
                    path_points=path,
                    tolerance=tolerance,
                    timeout=timeout,
                )
                if reached:
                    return
                # FollowPath timed out or got stuck internally
                ConsoleLog(
                    BOT_NAME,
                    f"[Move] FollowPath did not reach ({tx:.0f},{ty:.0f}) on attempt {attempt + 1}.",
                    Py4GW.Console.MessageType.Warning,
                )
            else:
                # Navmesh returned nothing (same trapezoid / very close) → direct move
                ConsoleLog(
                    BOT_NAME,
                    f"[Move] No navmesh path to ({tx:.0f},{ty:.0f}), using direct FollowPath.",
                    Py4GW.Console.MessageType.Info,
                )
                reached = yield from Routines.Yield.Movement.FollowPath(
                    path_points=[(tx, ty)],
                    tolerance=tolerance,
                    timeout=timeout,
                )
                if reached:
                    return

            if attempt >= max_retries:
                ConsoleLog(
                    BOT_NAME,
                    f"[Move] Max retries reached for ({tx:.0f},{ty:.0f}), jumping to previous step.",
                    Py4GW.Console.MessageType.Warning,
                )
                fsm = bot_instance.config.FSM
                current_step_number = fsm.get_current_state_number()  # 1-based
                previous_step_index = current_step_number - 2  # convert to 0-based previous index
                if previous_step_index >= 0:
                    fsm.pause()
                    try:
                        fsm.jump_to_state_by_step_number(previous_step_index)
                    finally:
                        fsm.resume()
                else:
                    ConsoleLog(
                        BOT_NAME,
                        "[Move] No previous step available to jump to.",
                        Py4GW.Console.MessageType.Warning,
                    )
                return

            # ── Step 3: recovery before next attempt ─────────────────────
            Player.SendChatCommand("stuck")
            yield from Routines.Yield.wait(1000)

            cpx, cpy = Player.GetXY()
            if math.sqrt((tx - cpx) ** 2 + (ty - cpy) ** 2) <= tolerance:
                return  # /stuck teleported us close enough

            yield from Routines.Yield.Movement.WalkBackwards(backup_ms)
            yield from Routines.Yield.wait(300)

    label = step_name or f"MoveUnstuck_{target_x:.0f}_{target_y:.0f}"
    bot_instance.config.FSM.AddYieldRoutineStep(name=label, coroutine_fn=_coro)


def FocusKeeperOfSouls(bot_instance: Botting):
    KeeperOfSoulsModelID = 2373
    def _focus_logic():
        enemies = [e for e in AgentArray.GetEnemyArray() if Agent.IsAlive(e) and Agent.GetModelID(e) == KeeperOfSoulsModelID]
        
        if not enemies:
            return
        
        player_pos = Player.GetXY()
        closest_enemy = min(enemies, key=lambda e: ((player_pos[0] - Agent.GetXYZ(e)[0])**2 + (player_pos[1] - Agent.GetXYZ(e)[1])**2)**0.5)
        CustomBehaviorParty().set_party_custom_target(closest_enemy)

    bot_instance.States.AddCustomState(_focus_logic, "Focus Keeper of Souls")

def bot_routine(bot: Botting):

    global MAIN_LOOP_HEADER_NAME
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    CustomBehaviorParty().set_party_is_blessing_enabled(True)
    _setup_custom_behavior_integration(bot)
    
    bot.Templates.Aggressive()
    

    # Set up the FSM states properly
    MAIN_LOOP_HEADER_NAME = _add_header_with_name(bot, "MAIN_LOOP")

    bot.Map.Travel(target_map_id=138)
    bot.Party.SetHardMode(False)

    Enter_UW(bot)
    Clear_the_Chamber(bot)
    _enqueue_section(bot, "RestoreVale", "Restore Vale", Restore_Vale)
    _enqueue_section(bot, "WrathfullSpirits", "Wrathfull Spirits", Wrathfull_Spirits)
    #_enqueue_section(bot, "EscortOfSouls", "Escort of Souls", Escort_of_Souls)
    _enqueue_section(bot, "UnwantedGuests", "Unwanted Guests", Unwanted_Guests)
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
    _enqueue_section(bot, "Repeat", "Repeat the whole thing", ResignAndRepeat)
    bot.States.AddHeader("END")

def Enter_UW(bot_instance: Botting):
    bot_instance.States.AddHeader("Enter Underworld")
    #_do_inventory_refill(bot_instance)
    _ensure_minimum_gold(bot_instance)

    if BotSettings.UseCons:
        # Withdraw 10 consets (Essence, Grail, Armor) per account from Xunlai chest
        bot_instance.Multibox.RestockConset(10)

    CustomBehaviorParty().set_party_leader_email(Player.GetAccountEmail())
    bot_instance.Move.XY(-4199, 19845, "go to Statue")
    bot_instance.States.AddCustomState(lambda: Player.SendChatCommand("kneel"), "kneel")
    bot_instance.Wait.ForTime(3000)
    #bot_instance.Dialogs.AtXY(-4199, 19845, 0x85, "ask to enter")
    bot_instance.Dialogs.AtXY(-4199, 19845, 0x86, "accept to enter")
    bot_instance.Wait.ForMapLoad(target_map_id=72) # we are in the dungeon
    bot_instance.States.AddCustomState(_mark_entered_dungeon, "Mark entered dungeon")
    bot_instance.Properties.ApplyNow("pause_on_danger", "active", True)

    


def enable_default_party_behavior(bot_instance: Botting):
    """
    Enable the baseline party behavior toggles used across Underworld missions.
    """
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(True), "Enable Follow")
    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_looting_enabled(True), "Enable Looting")


def Clear_the_Chamber(bot_instance: Botting):
    bot_instance.States.AddHeader("Clear the Chamber")
    CustomBehaviorParty().set_party_leader_email(Player.GetAccountEmail())    
    enable_default_party_behavior(bot_instance)
    bot_instance.Move.XYAndInteractNPC(295, 7221, "go to NPC")
    bot_instance.Dialogs.AtXY(295, 7221, 0x806501, "take quest")
    bot_instance.Move.XY(769, 6564, "Prepare to clear the chamber")
    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_forced_state(BehaviorState.CLOSE_TO_AGGRO),"Force Close_to_Aggro",)
    bot_instance.Wait.ForTime(5000)

    if BotSettings.UseCons:
        # Enable auto-renewal: Properties system re-pops each conset when it expires
        bot_instance.Properties.ApplyNow("armor_of_salvation", "active", True)
        bot_instance.Properties.ApplyNow("essence_of_celerity", "active", True)
        bot_instance.Properties.ApplyNow("grail_of_might", "active", True)
        # Immediately use conset on dungeon entry
        #bot_instance.Items.UseConset()

    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_forced_state(None),"Release Close_to_Aggro",)

    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(True), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")

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

    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(False), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")

    if BotSettings.RestoreVale:
        if BotSettings.EscortOfSouls:
            bot_instance.Dialogs.AtXY(-5806, 12831, 0x806C03, "take quest")
            bot_instance.Dialogs.AtXY(-5806, 12831, 0x806C01, "take quest")
        bot_instance.Move.XY(-8660, 5655, "To the Vale 1")
        bot_instance.Move.XY(-9431, 1659, "To the Vale 2")
        bot_instance.Move.XY(-11123, 2531, "To the Vale 3")
        bot_instance.Move.XY(-11926, 1146 , "To the Vale 4")
        bot_instance.Move.XY(-10691, 98 , "To the Vale 5")
        bot_instance.Move.XY(-15424, 1319 , "To the Vale 6")
        bot_instance.Move.XY(-13246, 5110 , "To the Vale 7")
        
        bot_instance.Move.XYAndInteractNPC(-13275, 5261, "go to NPC")
        if BotSettings.WrathfullSpirits == False:
            #bot_instance.Dialogs.AtXY(5755, 12769, 0x7F, "Back to Chamber")
            #bot_instance.Dialogs.AtXY(5755, 12769, 0x86, "Back to Chamber")
            bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "Back to Chamber")
        bot_instance.Wait.ForTime(3000)

def Wrathfull_Spirits(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(True), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")
    if BotSettings.WrathfullSpirits:
        bot_instance.Move.XYAndInteractNPC(-13275, 5261, "go to NPC")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x806E03, "Back to Chamber")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x806E01, "Back to Chamber")
        bot_instance.Templates.Pacifist()
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
        bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(False), "Disable WaitIfInAggro")
        #bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_combat_enabled(False), "Disable Combat")
        bot_instance.States.AddCustomState(
            lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().add_name("tortured spirit"),
            "Blacklist Tortured Spirit",
        )
        bot_instance.Move.XY(-13422, 973, "Wrathfull Spirits 1")
        bot_instance.Templates.Aggressive()
        bot_instance.States.AddCustomState(
            lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().remove_name("tortured spirit"),
            "Unblacklist Tortured Spirit",
        )
        #bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_combat_enabled(True), "Enable Combat")
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar") 
        bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
        bot_instance.Move.XY(-10207, 1746, "Wrathfull Spirits 2")
        bot_instance.Move.XY(-13287, 1996, "Wrathfull Spirits 3")
        bot_instance.Move.XY(-14486, 7113, "Wrathfull Spirits 4")
        bot_instance.Move.XY(-15226, 4129 , "Wrathfull Spirits 5")
        bot_instance.Move.XYAndInteractNPC(-13275, 5261, "go to NPC")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x806E07, "Take Reward")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "Back to Chamber")
        bot_instance.Wait.ForTime(3000)

def Escort_of_Souls(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(True), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")
    if BotSettings.EscortOfSouls:
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

def Unwanted_Guests(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(True), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")
    #This Quest is not working
    if BotSettings.UnwantedGuests:
        
        #The Quest
        #1st Keeper
        _move_with_unstuck(bot_instance, -2965, 10260, "1st Keeper approach")
        bot_instance.Wait.ForTime(5000)
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(False), "Disable Following")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_forced_state(BehaviorState.CLOSE_TO_AGGRO),"Force Close_to_Aggro")
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable wait_for_party")

        bot_instance.Move.XYAndInteractNPC(-5806, 12831, "go to NPC")
        bot_instance.Dialogs.AtXY(-5806, 12831, 0x806701, "take quest")

        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_forced_state(None),"Release Close_to_Aggro")
        FocusKeeperOfSouls(bot_instance)
        bot_instance.Wait.ForTime(500)
        FocusKeeperOfSouls(bot_instance)
        bot_instance.Wait.ForTime(500)
        FocusKeeperOfSouls(bot_instance)
        bot_instance.Wait.ForTime(20000)
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(True), "Enable Following")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_forced_state(None),"Release Close_to_Aggro",)
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")

        #2nd Keeper
        bot_instance.Move.XYAndInteractNPC(-5806, 12831, "go to NPC")
        bot_instance.Dialogs.AtXY(-5806, 12831, 0x91, "take quest")
        _move_with_unstuck(bot_instance, -12953, 750, "2nd Keeper 1")
        _move_with_unstuck(bot_instance, -8371, 4865, "2nd Keeper 2")
        FocusKeeperOfSouls(bot_instance)
        bot_instance.Wait.ForTime(500)
        FocusKeeperOfSouls(bot_instance)
        _move_with_unstuck(bot_instance, -7589, 6801, "2nd Keeper killed")

        #3rd Keeper
        _move_with_unstuck(bot_instance, -4095, 12964, "3rd Keeper approach")
        FocusKeeperOfSouls(bot_instance)
        bot_instance.Wait.ForTime(500)
        FocusKeeperOfSouls(bot_instance)
        _move_with_unstuck(bot_instance, -647, 13356, "3rd Keeper killed")

        #4th Keeper
        _move_with_unstuck(bot_instance, 1098, 12215, "4th Keeper approach")
        FocusKeeperOfSouls(bot_instance)
        bot_instance.Wait.ForTime(500)
        FocusKeeperOfSouls(bot_instance)
        _move_with_unstuck(bot_instance, 3113, 9503, "4th Keeper killed")

        #5th Keeper
        _move_with_unstuck(bot_instance, 1586, 10362, "5th Keeper approach")
        FocusKeeperOfSouls(bot_instance)
        bot_instance.Wait.ForTime(500)
        FocusKeeperOfSouls(bot_instance)
        _move_with_unstuck(bot_instance, 367, 7214, "5th Keeper killed")

        #6th Keeper
        _move_with_unstuck(bot_instance, -3125, 916, "6th Keeper 1")
        _move_with_unstuck(bot_instance, -344, 2155, "6th Keeper 2")
        FocusKeeperOfSouls(bot_instance)
        bot_instance.Wait.ForTime(500)
        FocusKeeperOfSouls(bot_instance)
        _move_with_unstuck(bot_instance, 1256, 4623, "6th Keeper killed")

def Restore_Wastes(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(True), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")
    if BotSettings.RestoreWastes:
        bot_instance.Templates.Aggressive()
        bot_instance.Properties.ApplyNow("pause_on_danger", "active", True)
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
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(True), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")
    if BotSettings.ServantsOfGrenth:
        bot_instance.Templates.Aggressive()
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
        _enqueue_spread_flags(bot_instance, SERVANTS_OF_GRENTH_FLAG_POINTS)
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_forced_state(BehaviorState.CLOSE_TO_AGGRO),"Force Close_to_Aggro",)
        bot_instance.Move.XYAndInteractNPC(554, 18384, "go to NPC")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(False), "Disable Following")
        #bot_instance.Dialogs.AtXY(5755, 12769, 0x806603, "Back to Chamber")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x806601, "Back to Chamber")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_forced_state(None),"Release Close_to_Aggro",)

        bot_instance.Move.XY(2700, 19952, "Servants of Grenth 2")
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(True), "Enable Following")
        bot_instance.Party.UnflagAllHeroes()
        bot_instance.Party.FlagAllHeroes(3032, 20148)
        bot_instance.Party.UnflagAllHeroes()
        WaitTillQuestDone(bot_instance)
        bot_instance.Party.UnflagAllHeroes()
        bot_instance.States.AddCustomState(
            lambda: CustomBehaviorParty().party_flagging_manager.clear_all_flags(),
            "Clear Flags",
        )
        bot_instance.Move.XYAndInteractNPC(554, 18384, "go to NPC")
        #bot_instance.Dialogs.AtXY(5755, 12769, 0x7F, "Back to Chamber")
        #bot_instance.Dialogs.AtXY(5755, 12769, 0x86, "Back to Chamber")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "Back to Chamber")
        bot_instance.Wait.ForTime(3000)

def Pass_The_Mountains(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(False), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")
    if BotSettings.PassTheMountains:
        bot_instance.Move.XY(-220, 1691, "Pass the Mountains 1")
        bot_instance.Move.XY(7035, 1973, "Pass the Mountains 2")
        bot_instance.Move.XY(8089, -3303, "Pass the Mountains 3")
        bot_instance.Move.XY(8121, -6054, "Pass the Mountains 4")
    

def Restore_Mountains(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(False), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")
    if BotSettings.RestoreMountains:
        bot_instance.Move.XY(7013, -7582, "Restore the Mountains 1")
        bot_instance.Move.XY(1420, -9126, "Restore the Mountains 2")
        bot_instance.Move.XY(-8373, -5016, "Restore the Mountains 3")

def Deamon_Assassin(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(False), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")
    if BotSettings.DeamonAssassin:
        bot_instance.Move.XYAndInteractNPC(-8250, -5171, "go to NPC")
        bot_instance.Wait.ForTime(3000)
        bot_instance.Dialogs.AtXY(-8250, -5171, 0x806801, "take quest")
        bot_instance.Move.XY(-3645, -5820, "Deamon Assassin 1")
        WaitTillQuestDone(bot_instance)
        #ModelID Slayer 2391

def Restore_Planes(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(False), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")
    if BotSettings.RestorePlanes:
        Wait_for_Spawns(bot_instance,10371, -10510)
        bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(True), "Enable MoveToEnemyIfCloseEnough")
        Wait_for_Spawns(bot_instance,12795, -8811)
        Wait_for_Spawns(bot_instance,11180, -13780)
        Wait_for_Spawns(bot_instance,13740, -15087)
        bot_instance.Move.XY(11546, -13787, "Restore Planes 1")
        bot_instance.Move.XY(8530, -11585, "Restore Planes 2")
        Wait_for_Spawns(bot_instance,8533, -13394)
        Wait_for_Spawns(bot_instance,8579, -20627)
        Wait_for_Spawns(bot_instance,11218, -17404)

def The_Four_Horsemen(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(True), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")
    if BotSettings.TheFourHorsemen:
        bot_instance.Move.XY(13473, -12091, "The Four Horseman 1")
        bot_instance.Wait.ForTime(10000)
        THE_FOUR_HORSEMEN_FLAG_POINTS = [
            (13432, -12100),
            (13246, -12440),
            (13072, -12188),
            (13216, -11841),
            (13639, -11866),
            (13745, -12151),
            (13520, -12436),
        ]
        _enqueue_spread_flags(bot_instance, THE_FOUR_HORSEMEN_FLAG_POINTS)
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_looting_enabled(False), "Disable Looting")
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
        bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(False), "Disable MoveIfPartyMemberInAggro")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_forced_state(BehaviorState.CLOSE_TO_AGGRO),"Force Close_to_Aggro",)
        bot_instance.Move.XYAndInteractNPC(11371, -17990, "go to NPC")
        bot_instance.Dialogs.AtXY(-8250, -5171, 0x806A01, "take quest")  
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_forced_state(None),"Release Close_to_Aggro",)

        bot_instance.Wait.ForTime(35000)

        bot_instance.Move.XYAndInteractNPC(11371, -17990, "TP to Chamber")
        #bot_instance.Dialogs.AtXY(11371, -17990, 0x7F, "take quest")
        #bot_instance.Dialogs.AtXY(11371, -17990, 0x86, "take quest") 
        bot_instance.Dialogs.AtXY(11371, -17990, 0x8D, "take quest") 
        bot_instance.States.AddCustomState(
            lambda: CustomBehaviorParty().party_flagging_manager.clear_all_flags(),
            "Clear Flags",
        )

        bot_instance.Wait.ForTime(1000)

        bot_instance.Move.XYAndInteractNPC(-5782, 12819, "TP back to Chaos")
        #bot_instance.Dialogs.AtXY(11371, -17990, 0x7F, "take quest")
        #bot_instance.Dialogs.AtXY(11371, -17990, 0x84, "take quest") 
        bot_instance.Dialogs.AtXY(11371, -17990, 0x8B, "take quest") 
        bot_instance.Wait.ForTime(1000)
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(True), "Enable Following")
        THE_FOUR_HORSEMEN_FLAG_POINTS_2 = [
            (11318, -17670),
            (11318, -17670),
            (11221, -18335),
            (11479, -18361),
            (11806, -18134),
            (11697, -17748),
            (11354, -17530),
        ]
        _enqueue_spread_flags(bot_instance, THE_FOUR_HORSEMEN_FLAG_POINTS_2)
        bot_instance.Party.UnflagAllHeroes()
        WaitTillQuestDone(bot_instance)
        bot_instance.States.AddCustomState(
            lambda: CustomBehaviorParty().party_flagging_manager.clear_all_flags(),
            "Clear Flags",
        )
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(True), "Enable Follow")
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
        bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_looting_enabled(True), "Enable Looting")

def Restore_Pools(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(True), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")
    if BotSettings.RestorePools:
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
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(True), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")
    if BotSettings.TerrorwebQueen:
        bot_instance.Move.XYAndInteractNPC(-6961, -19499, "go to NPC")
        #bot_instance.Dialogs.AtXY(-6961, -19499, 0x806B03, "take quest")
        bot_instance.Dialogs.AtXY(-6961, -19499, 0x806B01, "take quest")   
        bot_instance.Move.XY(-12303, -15213, "Terrorweb Queen 1")
        bot_instance.Move.XYAndInteractNPC(-6957, -19478, "go to NPC")
        #bot_instance.Dialogs.AtXY(-6957, -19478, 0x7F, "Back to Chamber")
        #bot_instance.Dialogs.AtXY(-6957, -19478, 0x84, "Back to Chamber")
        bot_instance.Dialogs.AtXY(-6957, -19478, 0x8B, "Back to Chamber")
    
def Restore_Pit(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(False), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")
    if BotSettings.RestorePit:
        _toggle_move_if_aggro(False)
        bot_instance.Move.XY(14178, -57, "Restore Pit 1")
        bot_instance.Move.XY(15323, 2970, "Restore Pit 2")
        bot_instance.Move.XY(15393, 406, "Restore Pit 3")
        bot_instance.Move.FollowPath([
            (15252, 316),
            (13451, 1123),
            (13181, 1419),
            (13076, 1547),
        ], step_name="Über die Brücke")
        bot_instance.Move.XY(13216, 1428, "Restore Pit 4")
        bot_instance.Move.XY(13896, 3670, "Restore Pit 5")
        bot_instance.Move.XY(15382, 6581, "Restore Pit 6")
        bot_instance.Move.XY(10620, 2665, "Restore Pit 7")
        bot_instance.Move.XY(8644, 6242, "Restore Pit 8")
        if BotSettings.ImprisonedSpirits == False:
            bot_instance.Move.XYAndInteractNPC(8698, 6324, "go to NPC")
            #bot_instance.Dialogs.AtXY(8698, 6324, 0x7F, "Back to Chamber")
            #bot_instance.Dialogs.AtXY(8698, 6324, 0x86, "Back to Chamber")
            bot_instance.Dialogs.AtXY(8698, 6324, 0x8D, "Back to Chamber")
        bot_instance.Wait.ForTime(3000)

def Imprisoned_Spirits(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(False), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")
    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_looting_enabled(False), "Disable Looting")
    if BotSettings.ImprisonedSpirits:
        bot_instance.Move.XY(13212, 4978)
        IMPRISONED_SPIRITS_FLAG_POINTS = [
            (13652, 6117),
            (13722, 6493),
            (13759, 6817),
            (12840, 3676),
            (12559, 3647),
            (12262, 3635),
            (11912, 3622),
        ]
        _enqueue_spread_flags(bot_instance, IMPRISONED_SPIRITS_FLAG_POINTS)
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
        bot_instance.Move.XY(8692, 6292, "go to NPC")
        bot_instance.Move.XYAndInteractNPC(8666, 6308, "go to NPC")
        bot_instance.Dialogs.AtXY(8666, 6308, 0x806901, "take quest")  
        bot_instance.Move.XY(13652, 6117) #Runter rennen zum linken team
        bot_instance.Wait.ForTime(10000)
        bot_instance.States.AddCustomState(
            lambda: CustomBehaviorParty().party_flagging_manager.clear_all_flags(),
            "Clear Flags",
        )
        bot_instance.Move.XY(12593, 1814)
        WaitTillQuestDone(bot_instance)
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_looting_enabled(True), "Enable Looting")
        ##warten bis quest fertig

        bot_instance.Move.XY(8692, 6292, "go to NPC")
        bot_instance.Move.XYAndInteractNPC(8666, 6308, "go to NPC")
        bot_instance.Multibox.SendDialogToTarget(0x806907)
        bot.Wait.ForTime(1000)
        bot_instance.Multibox.SendDialogToTarget(0x8C)

def _do_inventory_refill(bot_instance: Botting) -> None:
    """Travel to Guild Hall and restock inventory between runs."""
    if not InventorySettings.RefillEnabled:
        return

    # 1. Travel to Guild Hall (same as FoW)
    bot_instance.Map.TravelGH(wait_time=7000)

    # 2. Restock ID kits + Salvage kits from GH merchant (3 rounds, like FoW)
    if InventorySettings.RestockKits:
        def _restock_kits_coro():
            npc_array = AgentArray.GetNPCMinipetArray()
            merchant_id = None
            for agent_id in npc_array:
                if "merchant" in (Agent.GetNameByID(agent_id) or "").lower():
                    merchant_id = agent_id
                    break
            if merchant_id is None:
                ConsoleLog(BOT_NAME, "[Inventory] No Merchant NPC found in Guild Hall.", Py4GW.Console.MessageType.Warning)
                yield
                return
            mx, my = Agent.GetXY(merchant_id)
            yield from Routines.Yield.Movement.FollowPath(path_points=[(mx, my)])
            yield from Routines.Yield.Player.InteractAgent(merchant_id)
            yield from Routines.Yield.wait(1500)
            yield from Routines.Yield.Merchant.BuyIDKits(2)
            yield from Routines.Yield.Merchant.BuySalvageKits(5)
            yield
        for _ in range(3):
            bot_instance.States.AddCustomState(_restock_kits_coro, "Restock Kits")

    # 3. Restock consets from Xunlai chest (same pattern as FoW's handle_restock_cons)
    if InventorySettings.RestockCons and BotSettings.UseCons:
        bot_instance.States.AddCustomState(
            lambda: GLOBAL_CACHE.Inventory.OpenXunlaiWindow() if not GLOBAL_CACHE.Inventory.IsStorageOpen() else None,
            "Open Xunlai for Cons Restock",
        )
        bot_instance.Wait.ForTime(1000)

        def _restock_cons_coro():
            from Py4GWCoreLib.enums_src.Model_enums import ModelID
            yield from Routines.Yield.Items.RestockItems(ModelID.Essence_Of_Celerity.value, 10)
            yield from Routines.Yield.Items.RestockItems(ModelID.Grail_Of_Might.value, 10)
            yield from Routines.Yield.Items.RestockItems(ModelID.Armor_Of_Salvation.value, 10)
        bot_instance.States.AddCustomState(_restock_cons_coro, "Restock Consets")

    # 4. Deposit full material stacks to Xunlai chest (same as FoW's handle_deposit_materials)
    if InventorySettings.DepositMaterials:
        def _deposit_coro():
            yield from Routines.Yield.Merchant.DepositMaterials()
        bot_instance.States.AddCustomState(_deposit_coro, "Deposit Materials")

    # 5. Travel back to UW outpost
    bot_instance.Map.Travel(target_map_id=138)
    bot_instance.Wait.ForMapLoad(target_map_id=138)


def ResignAndRepeat(bot_instance: Botting):
    if BotSettings.Repeat:
        bot_instance.Multibox.ResignParty()

def Wait_for_Spawns(bot_instance: Botting,x,y):
    bot_instance.Move.XY(x, y, "To the Vale")
    def runtime_check_logic():
        enemies = [e for e in AgentArray.GetEnemyArray() if Agent.IsAlive(e) and Agent.GetModelID(e) == 2380]
        
        if not enemies:
            print("No Mindblades found - Continuing...") 
            return True
        
        print("Mindblades ... Waiting.")
        bot_instance.Move.XY(x, y, "Go Back")
        return False
    
    bot_instance.Wait.UntilCondition(runtime_check_logic)
    bot_instance.Wait.ForTime(1000)
    bot_instance.Move.XY(x, y, "1")
    bot_instance.Wait.UntilCondition(runtime_check_logic)
    bot_instance.Wait.ForTime(1000)
    bot_instance.Move.XY(x, y, "2")
    bot_instance.Wait.UntilCondition(runtime_check_logic)
    bot_instance.Wait.ForTime(1000)
    bot_instance.Move.XY(x, y, "3")
    bot_instance.Wait.UntilCondition(runtime_check_logic)


def _draw_help():
    import PyImGui
    PyImGui.text("Hey, this is my first bot in Python, be gentle :)")
    PyImGui.separator()
    PyImGui.text_wrapped("This Bot automates the Underworld")
    PyImGui.text("It is optimized for 8x Custom Behaviors, HeroAi dont work atm, Custom Behaviors could but needs to be tested more")
    PyImGui.text_wrapped("Some quests are not easy to automate, so I recommend to watch the bot at least the first time to see how it works")
    PyImGui.text_wrapped("Some quests are missing, I will add them when I have time, but feel free to contribute :)")
    PyImGui.text_wrapped("Some quests are just not easy, because its the Underworld")
    PyImGui.separator()
    PyImGui.text("What is working Well:")
    PyImGui.bullet_text("Restoring Grenth's Monuments (exept Pits)")
    PyImGui.bullet_text("Wrathfull Spirits, Escort of Souls, Servants of Grenth, Deamon Assassin, The Four Horsemen, Terrorweb Queen")
    PyImGui.text("What is working Bad:")
    PyImGui.bullet_text("Imprisoned Spirits, Restore Pits")
    PyImGui.text("What is not implemented::")
    PyImGui.bullet_text("Unwanted Guests, The Nightman Cometh (Dhuum)")
    PyImGui.separator()
    PyImGui.text("Req:")
    PyImGui.bullet_text("Highend Team")
    PyImGui.bullet_text("For faster runs use Pcons (via Pcons widget)")
    PyImGui.bullet_text("You have to do the missing quests manually")
    PyImGui.bullet_text("Main Account sometimes leaves the team alone - Dont be the Healer")
    PyImGui.bullet_text("You should either have some evas or 1 melee char to trigger traps in the mountains")
    PyImGui.separator()
    PyImGui.bullet_text("Have fun :) - sch0l0ka")


def _draw_inventory_settings() -> None:
    changed = False
    new_val = PyImGui.checkbox("Enable Inventory Refill", InventorySettings.RefillEnabled)
    if new_val != InventorySettings.RefillEnabled:
        InventorySettings.RefillEnabled = new_val
        changed = True
    PyImGui.separator()
    PyImGui.begin_disabled(not InventorySettings.RefillEnabled)
    PyImGui.text_wrapped("After each run: travel to Guild Hall, restock, then return.")
    PyImGui.separator()
    new_val = PyImGui.checkbox("Restock ID & Salvage Kits (3 rounds)", InventorySettings.RestockKits)
    if new_val != InventorySettings.RestockKits:
        InventorySettings.RestockKits = new_val
        changed = True
    new_val = PyImGui.checkbox("Restock Consets from Xunlai Chest", InventorySettings.RestockCons)
    if new_val != InventorySettings.RestockCons:
        InventorySettings.RestockCons = new_val
        changed = True
    PyImGui.begin_disabled(not BotSettings.UseCons)
    PyImGui.text("  (requires 'Use Cons' to be enabled)")
    PyImGui.end_disabled()
    new_val = PyImGui.checkbox("Deposit Full Material Stacks to Chest", InventorySettings.DepositMaterials)
    if new_val != InventorySettings.DepositMaterials:
        InventorySettings.DepositMaterials = new_val
        changed = True
    PyImGui.end_disabled()
    if changed:
        InventorySettings.save()


def _draw_settings():
    if PyImGui.begin_tab_bar("##uw_settings_tabs"):
        if PyImGui.begin_tab_item("Quests"):
            _draw_quest_settings()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Inventory"):
            _draw_inventory_settings()
            PyImGui.end_tab_item()
        PyImGui.end_tab_bar()


def _draw_quest_settings():
    BotSettings.RestoreVale = PyImGui.checkbox("Restore Vale", BotSettings.RestoreVale)
    DisableVale = not BotSettings.RestoreVale
    if DisableVale: BotSettings.WrathfullSpirits = False
    if DisableVale: BotSettings.EscortOfSouls = False
    PyImGui.begin_disabled(DisableVale)
    BotSettings.WrathfullSpirits = PyImGui.checkbox("Wrathfull Spirits", BotSettings.WrathfullSpirits)
    BotSettings.EscortOfSouls = PyImGui.checkbox("Escort of Souls", BotSettings.EscortOfSouls)
    BotSettings.UnwantedGuests = PyImGui.checkbox("Unwanted Guests", BotSettings.UnwantedGuests)
    PyImGui.end_disabled()
    BotSettings.RestoreWastes = PyImGui.checkbox("Restore Wastes", BotSettings.RestoreWastes)
    DisableWastes = not BotSettings.RestoreWastes
    if DisableWastes: BotSettings.ServantsOfGrenth = False
    PyImGui.begin_disabled(DisableWastes)
    BotSettings.ServantsOfGrenth = PyImGui.checkbox("Servants of Grenth", BotSettings.ServantsOfGrenth)
    PyImGui.end_disabled()
    PyImGui.begin_disabled(True)
    if BotSettings.RestoreMountains == False and BotSettings.RestorePlanes == False and BotSettings.RestorePools == False:
        BotSettings.PassTheMountains = False
    else:
        BotSettings.PassTheMountains = True

    BotSettings.PassTheMountains = PyImGui.checkbox("Pass the Mountains", BotSettings.PassTheMountains)
    PyImGui.end_disabled()
    DisableMountains = not BotSettings.RestoreMountains
    if DisableMountains: BotSettings.DeamonAssassin = False    
    BotSettings.RestoreMountains = PyImGui.checkbox("Restore Mountains", BotSettings.RestoreMountains)
    PyImGui.begin_disabled(DisableMountains)
    BotSettings.DeamonAssassin = PyImGui.checkbox("Deamon Assassin", BotSettings.DeamonAssassin)
    PyImGui.end_disabled()
    BotSettings.RestorePlanes = PyImGui.checkbox("Restore Planes", BotSettings.RestorePlanes)
    DisablePlanes = not BotSettings.RestorePlanes
    if DisablePlanes: BotSettings.TheFourHorsemen = False
    if DisablePlanes: BotSettings.RestorePools = False
    if DisablePlanes: BotSettings.TerrorwebQueen = False
    PyImGui.begin_disabled(DisablePlanes)
    BotSettings.TheFourHorsemen = PyImGui.checkbox("The Four Horsemen", BotSettings.TheFourHorsemen)
    BotSettings.RestorePools = PyImGui.checkbox("Restore Pools", BotSettings.RestorePools)
    PyImGui.end_disabled()
    DisablePoolsAndTerrorweb = not BotSettings.RestorePools
    if DisablePoolsAndTerrorweb: BotSettings.TerrorwebQueen = False
    PyImGui.begin_disabled(DisablePoolsAndTerrorweb)
    BotSettings.TerrorwebQueen = PyImGui.checkbox("Terrorweb Queen", BotSettings.TerrorwebQueen)
    PyImGui.end_disabled()
    BotSettings.RestorePit = PyImGui.checkbox("Restore Pit - Disabled", BotSettings.RestorePit)
    BotSettings.ImprisonedSpirits = PyImGui.checkbox("Imprisoned Spirits - Disabled", BotSettings.ImprisonedSpirits)
    PyImGui.separator()
    BotSettings.Repeat = PyImGui.checkbox("Resign and Repeat after", BotSettings.Repeat)
    BotSettings.UseCons = PyImGui.checkbox("Use Cons", BotSettings.UseCons)
    



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
    if bot.config.fsm_running:
        _sync_custom_behavior_runtime()
        # Watchdog: callback sometimes misses wipes — detect return to outpost by map ID
        if _entered_dungeon and Map.GetMapID() == 138:
            ConsoleLog(BOT_NAME, "[WIPE] Watchdog: back in outpost (map 138) without wipe callback — restarting.", Py4GW.Console.MessageType.Warning)
            _restart_main_loop(bot, "Watchdog: returned to map 138")
    bot.Update()
    bot.UI.draw_window()

if __name__ == "__main__":
    main()