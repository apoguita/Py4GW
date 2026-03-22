
from Py4GWCoreLib import Botting, Routines, Agent, AgentArray, Player, Utils, AutoPathing, GLOBAL_CACHE, ConsoleLog, Map, Pathing, FlagPreference, Party, IniHandler
import os
import time
from typing import Any, Generator
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

# ╔══════════════════════════════════════════════════════════════════
# ║                     POSSIBLE IMPROVEMENTS                        
# ╠══════════════════════════════════════════════════════════════════
# ║                                                                  
# ║  [ ] Better antistuck at Unwanted Guests                                                         
# ║  [ ] Kill the Chained Souls when we wait till the quest is done                                                        
# ║  [ ] Blacklist Dreamrider to improve Plains speed                                                         
# ║  [ ] add Inventory Management                                                          
# ║  [ ] unequip armor at dhuum to sacrifice selected heroes  
# ║  [ ] add Heroai 
# ║  [ ] Take the Dhuum quest earlier   
# ║  [ ] Fix the move to dead ally                                             
# ║                                                                  
# ╚══════════════════════════════════════════════════════════════════



#3078 Dhuum Ghost buff
MODULE_NAME = "Underworld"
MODULE_ICON = "Textures/Module_Icons/Underworld.png"

# Override the help window
BOT_NAME = "Underworld"
_ini_file = os.path.join(Py4GW.Console.get_projects_path(), "Widgets", "Config", "UnderworldBot.ini")
_ini = IniHandler(_ini_file)
bot = Botting(BOT_NAME, config_draw_path=True, upkeep_auto_inventory_management_active=True)
bot.Templates.Aggressive()
# Override the help window
bot.UI.override_draw_help(lambda: _draw_help())
bot.UI.override_draw_config(lambda: _draw_settings())  # Disable default config window
MAIN_LOOP_HEADER_NAME = ""
_entered_dungeon: bool = False  # set True once map 72 is loaded; watchdog uses this
_king_frozenwind_model_id: int = 2403


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


class DhuumSettings:
    """Which multibox accounts are designated as sacrifice targets in the Dhuum fight."""
    _raw: str = _ini.read_key(BOT_NAME, "dhuum_sacrifice_emails", "")
    SacrificeEmails: set[str] = set(e.strip() for e in _raw.split(";") if e.strip())

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, "dhuum_sacrifice_emails", ";".join(sorted(cls.SacrificeEmails)))

    @classmethod
    def is_sacrifice(cls, email: str) -> bool:
        return email in cls.SacrificeEmails

    @classmethod
    def set_sacrifice(cls, email: str, value: bool) -> None:
        if value:
            cls.SacrificeEmails.add(email)
        else:
            cls.SacrificeEmails.discard(email)
        cls.save()


class BotSettings:
    Repeat:    bool = bool(_ini.read_bool(BOT_NAME, "quest_repeat",    False))
    UseCons:   bool = bool(_ini.read_bool(BOT_NAME, "quest_use_cons",  True))
    HardMode:  bool = bool(_ini.read_bool(BOT_NAME, "quest_hardmode",  False))

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, "quest_repeat",    str(cls.Repeat))
        _ini.write_key(BOT_NAME, "quest_use_cons",  str(cls.UseCons))
        _ini.write_key(BOT_NAME, "quest_hardmode",  str(cls.HardMode))


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
    bot.Party.SetHardMode(BotSettings.HardMode)

    Enter_UW(bot)
    Clear_the_Chamber(bot)
    _enqueue_section(bot, "PassTheMountains", "Pass the Mountains", Pass_The_Mountains)
    _enqueue_section(bot, "RestoreMountains", "Restore Mountains", Restore_Mountains)
    _enqueue_section(bot, "DeamonAssassin", "Deamon Assassin", Deamon_Assassin)
    _enqueue_section(bot, "RestorePlanes", "Restore Planes", Restore_Planes)
    _enqueue_section(bot, "TheFourHorsemen", "The Four Horsemen", The_Four_Horsemen)
    _enqueue_section(bot, "RestorePools", "Restore Pools", Restore_Pools)
    _enqueue_section(bot, "TerrorwebQueen", "Terrorweb Queen", Terrorweb_Queen)
    _enqueue_section(bot, "RestorePit", "Restore Pit", Restore_Pit)
    _enqueue_section(bot, "ImprisonedSpirits", "Imprisoned Spirits", Imprisoned_Spirits)
    _enqueue_section(bot, "RestoreVale", "Restore Vale", Restore_Vale)
    _enqueue_section(bot, "WrathfullSpirits", "Wrathfull Spirits", Wrathfull_Spirits)
    #_enqueue_section(bot, "EscortOfSouls", "Escort of Souls", Escort_of_Souls)
    _enqueue_section(bot, "UnwantedGuests", "Unwanted Guests", Unwanted_Guests)
    _enqueue_section(bot, "RestoreWastes", "Restore Wastes", Restore_Wastes)
    _enqueue_section(bot, "ServantsOfGrenth", "Servants of Grenth", Servants_of_Grenth)
    
    _enqueue_section(bot, "Dhuum", "Dhuum", Dhuum)
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
    #blacklist here
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().add_name("obsidian guardian"),
        "Blacklist Obsidian Guardian",
    )
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().add_name("vengeful aatxe"),
        "Blacklist Vengeful Aatxe",
    )
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().add_name("chained soul"),
        "Blacklist Chained Soul",
    )
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().remove_name("wastfull spirit"),
        "Unblacklist Wastfull Spirit",
    )
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().remove_name("obsidian behemoth"),
        "Unblacklist Obsidian Behemoth",
    )
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().remove_name("banished dream rider"),
        "Unblacklist Banished Dream Rider",
    )
    enable_default_party_behavior(bot_instance)
    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_combat_enabled(False), "Disable Combat")
    bot_instance.Move.XYAndInteractNPC(295, 7221, "go to NPC")
    bot_instance.Dialogs.AtXY(295, 7221, 0x806501, "take quest")
    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_combat_enabled(True), "Enable Combat")
    bot_instance.Move.XY(769, 6564, "Prepare to clear the chamber")
    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_forced_state(BehaviorState.CLOSE_TO_AGGRO),"Force Close_to_Aggro",)
    bot_instance.Wait.ForTime(5000)
    bot_instance.Multibox.UsePcons()
    bot_instance.Items.UseSummoningStone()

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
    bot_instance.Dialogs.AtXY(-5806, 12831, 0x806507, "take quest")
    bot_instance.Dialogs.AtXY(-5806, 12831, 0x806D01, "take quest")
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
    bot_instance.Move.XY(7013, -7582, "Restore the Mountains 1")
    bot_instance.Move.XY(1420, -9126, "Restore the Mountains 2")
    bot_instance.Move.XY(-8373, -5016, "Restore the Mountains 3")
    bot_instance.Wait.ForTime(5000)

def Deamon_Assassin(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(False), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")
    bot_instance.Move.XYAndInteractNPC(-8250, -5171, "go to NPC")
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
    '''
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
    '''
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().add_name("banished dream rider"),
        "Blacklist Banished Dream Rider",
    )
    bot_instance.Move.XY(13837, -14736, "Restore Planes 1 left Rider")
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().remove_name("banished dream rider"),
        "Unblacklist Banished Dream Rider",
    )
    Wait_for_Spawns(bot_instance,11287, -17921)


def The_Four_Horsemen(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(True), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")
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
    bot_instance.Move.XYAndInteractNPC(11371, -17990, "go to NPC")
    bot_instance.Dialogs.AtXY(-8250, -5171, 0x806A07, "take quest")  
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
    '''
    Wait_for_Spawns(bot_instance,4647, -16833)
    Wait_for_Spawns(bot_instance,2098, -15543)
    '''
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().add_name("banished dream rider"),
        "Blacklist Banished Dream Rider",
    )
    bot_instance.Move.XY(-12703, -10990, "Restore Pools 1")
    bot_instance.Move.XY(-11849, -11986, "Restore Pools 2")
    bot_instance.Move.XY(-5974, -19739, "Restore Pools 3")
    bot_instance.Move.XY(-7217, -19394, "Restore Pools 4")
    bot_instance.Move.XY(-5688, -19471, "Restore Pools 4")

def Terrorweb_Queen(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(True), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")
    bot_instance.Move.XYAndInteractNPC(-6890, -19454, "go to NPC")
    bot_instance.Dialogs.AtXY(-6890, -19454, 0x806B01, "take quest")   
    bot_instance.Move.XY(-12375, -15578, "Terrorweb Queen 1")
    bot_instance.Move.XYAndInteractNPC(-6957, -19478, "go to NPC")
    bot_instance.Dialogs.AtXY(-6957, -19478, 0x806B07, "Back to Chamber")
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
    _toggle_move_if_aggro(False)
    bot_instance.Move.XY(14178, -57, "Restore Pit 1")
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().remove_name("banished dream rider"),
        "Unblacklist Banished Dream Rider",
    )
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
    bot_instance.Move.XY(13212, 4978)
    IMPRISONED_SPIRITS_FLAG_POINTS = [
        (13652, 6117),
        (13652, 6117),
        (13652, 6117),
        (12439, 2750),
        (12439, 2761),
        (12682, 2793),
        (12322, 3016),
    ]
    _enqueue_spread_flags(bot_instance, IMPRISONED_SPIRITS_FLAG_POINTS)
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
    bot_instance.Move.XY(8692, 6292, "go to NPC")
    bot_instance.Move.XYAndInteractNPC(8666, 6308, "go to NPC")
    bot_instance.Dialogs.AtXY(8666, 6308, 0x806901, "take quest")  
    bot_instance.Move.XY(13652, 6117) #Runter rennen zum linken team
    bot_instance.States.AddCustomState(
        lambda: CustomBehaviorParty().party_flagging_manager.clear_all_flags(),
        "Clear Flags",
    )
    bot_instance.Move.XY(12593, 1814)
    bot_instance.Wait.ForTime(30000)
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().remove_name("chained soul"),
        "Unblacklist Chained Soul",
    )
    bot_instance.Move.XY(9815, 6763)
    WaitTillQuestDone(bot_instance)
    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_looting_enabled(True), "Enable Looting")
    ##warten bis quest fertig

    bot_instance.Move.XY(8692, 6292, "go to NPC")
    bot_instance.Dialogs.AtXY(8692, 6292, 0x8D, "Back to Chamber")
        

def Restore_Vale(bot_instance: Botting):

    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(False), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")

    bot_instance.Dialogs.AtXY(-5806, 12831, 0x806C03, "take quest")
    bot_instance.Dialogs.AtXY(-5806, 12831, 0x806C01, "take quest")
    bot_instance.Items.UseSummoningStone()
    bot_instance.Move.XY(-8660, 5655, "To the Vale 1")
    bot_instance.Move.XY(-9431, 1659, "To the Vale 2")
    bot_instance.Move.XY(-11123, 2531, "To the Vale 3")
    bot_instance.Move.XY(-11926, 1146 , "To the Vale 4")
    bot_instance.Move.XY(-10691, 98 , "To the Vale 5")
    bot_instance.Move.XY(-15424, 1319 , "To the Vale 6")
    bot_instance.Move.XY(-13246, 5110 , "To the Vale 7")
    bot_instance.Move.XYAndInteractNPC(-13275, 5261, "go to NPC")
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
    #The Quest
    #1st Keeper
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().add_name("obsidian behemoth"),
        "Blacklist Obsidian Behemoth",
    )
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

    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().remove_name("obsidian behemoth"),
        "Unblacklist Obsidian Behemoth",
    )

def Restore_Wastes(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True), "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(True), "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Enable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False), "Enable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False), "Enable WaitIfPartyMemberManaTooLow")
    bot_instance.Templates.Aggressive()
    bot_instance.Properties.ApplyNow("pause_on_danger", "active", True)
    bot_instance.Move.XY(3891, 7572, "Restore Wastes 1")
    bot_instance.Move.XY(4106, 16031, "Restore Wastes 2")
    bot_instance.Move.XY(2486, 21723, "Restore Wastes 3")
    bot_instance.Move.XY(-1452, 21202, "Restore Wastes 4")
    bot_instance.Move.XY(542, 18310, "Restore Wastes 5")
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
    

def Dhuum(bot_instance: Botting):
    bot_instance.States.AddHeader("Dhuum")
    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_forced_state(None),"Release Close_to_Aggro",)

    def _flag_sacrifice_accounts() -> None:
        flag_x, flag_y = -15022, 17277
        manager = CustomBehaviorParty().party_flagging_manager
        manager.clear_all_flags()

        sacrifice_emails = DhuumSettings.SacrificeEmails
        if not sacrifice_emails:
            ConsoleLog(BOT_NAME, "[Dhuum] No sacrifice accounts configured in Dhuum settings.", Py4GW.Console.MessageType.Warning)
            return

        cb_flagged_emails: list[str] = []
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            email = str(account.AccountEmail)
            if email not in sacrifice_emails:
                continue

            cb_index = len(cb_flagged_emails)
            if cb_index >= 12:
                break

            manager.set_flag_account_email(cb_index, email)
            manager.set_flag_position(cb_index, flag_x, flag_y)
            cb_flagged_emails.append(email)

        if not cb_flagged_emails:
            ConsoleLog(BOT_NAME, "[Dhuum] No sacrifice accounts found in shared memory.", Py4GW.Console.MessageType.Warning)
            return

        ConsoleLog(
            BOT_NAME,
            f"[Dhuum] Flagged {len(cb_flagged_emails)} sacrifice account(s): {cb_flagged_emails}",
            Py4GW.Console.MessageType.Info,
        )

    def _flag_survivor_accounts() -> None:
        flag_x, flag_y = -14144, 17286
        manager = CustomBehaviorParty().party_flagging_manager

        my_email = Player.GetAccountEmail()
        sacrifice_emails = DhuumSettings.SacrificeEmails

        # Start after the sacrifice account indices to avoid overwriting them
        all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        sacrifice_offset = sum(
            1 for account in all_accounts
            if str(account.AccountEmail) in sacrifice_emails
        )

        cb_flagged_emails: list[str] = []
        for account in all_accounts:
            email = str(account.AccountEmail)
            if email == my_email or email in sacrifice_emails:
                continue

            cb_index = sacrifice_offset + len(cb_flagged_emails)
            if cb_index >= 12:
                break

            manager.set_flag_account_email(cb_index, email)
            manager.set_flag_position(cb_index, flag_x, flag_y)
            cb_flagged_emails.append(email)

        if not cb_flagged_emails:
            ConsoleLog(BOT_NAME, "[Dhuum] No survivor accounts to flag.", Py4GW.Console.MessageType.Info)
            return

        ConsoleLog(
            BOT_NAME,
            f"[Dhuum] Flagged {len(cb_flagged_emails)} survivor account(s): {cb_flagged_emails}",
            Py4GW.Console.MessageType.Info,
        )

    
    _KING_TARGET_X = -11278.0
    _KING_TARGET_Y =  17297.0
    _KING_MODEL_ID =  2403
    _KING_DEST_RADIUS   = 1500.0  # how close the King must be to his destination
    _KING_FOLLOW_RADIUS = 1000.0  # how close we trail behind the King
    _KING_TIMEOUT_S     = 600.0   # 10 min hard-timeout

    def _coro_follow_king_to_destination():
        """Follow model 2403 until it reaches the area around the destination coords."""
        deadline = time.time() + _KING_TIMEOUT_S
        ConsoleLog(BOT_NAME, "[Dhuum] Waiting for the King to walk to position ...", Py4GW.Console.MessageType.Info)
        while time.time() < deadline:
            king_id = next(
                (a for a in AgentArray.GetAgentArray() if int(Agent.GetModelID(a)) == _KING_MODEL_ID),
                None,
            )
            if king_id is None:
                yield from Routines.Yield.wait(500)
                continue

            kx, ky = Agent.GetXY(king_id)

            # Stop following once the King has reached his destination
            if Utils.Distance((kx, ky), (_KING_TARGET_X, _KING_TARGET_Y)) <= _KING_DEST_RADIUS:
                ConsoleLog(BOT_NAME, "[Dhuum] King has reached the position.", Py4GW.Console.MessageType.Info)
                return

            # Move towards the King if we are too far away
            px, py = Player.GetXY()
            if Utils.Distance((px, py), (kx, ky)) > _KING_FOLLOW_RADIUS:
                Player.Move(kx, ky)

            yield from Routines.Yield.wait(500)

        ConsoleLog(BOT_NAME, "[Dhuum] Timed out waiting for the King - continuing anyway.", Py4GW.Console.MessageType.Warning)

    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
    bot_instance.config.FSM.AddYieldRoutineStep(
        name="Follow King to Destination",
        coroutine_fn=_coro_follow_king_to_destination,
    )
    bot_instance.Move.XY(-11278, 17297, "Wait For the King")
    bot_instance.Wait.UntilCondition(
        lambda: any(
            int(Agent.GetModelID(agent_id)) == 2403
            and Utils.Distance(Player.GetXY(), Agent.GetXY(agent_id)) <= 1100
            for agent_id in AgentArray.GetAgentArray()
        )
    )  # Wait until King is within interaction range

    bot_instance.Wait.ForTime(5000)
    bot_instance.Dialogs.WithModel(2403, 0x846901, "Talk to The King and start Dhuum fight")
    bot_instance.States.AddCustomState(_flag_sacrifice_accounts, "Flag Sacrifice Accounts")
    bot_instance.States.AddCustomState(_flag_survivor_accounts, "Flag Survivor Accounts")
    bot_instance.States.AddCustomState(
        lambda: bot_instance.Multibox.ApplyWidgetPolicy(enable_widgets=("Dhuum Helper",)),
        "Enable Dhuum Helper on all accounts",
    )

    bot_instance.Wait.ForTime(5000)  # Wait for the fight to properly start
    
    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_combat_enabled(False), "Disable Combat")
    bot_instance.Move.XY(-13987, 17291, "Move to Dhuum fight")
    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(False), "Disable Following")
    bot_instance.Wait.ForTime(2000)  # Wait till some Allies die
    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_combat_enabled(True), "Enable Combat")
    #Wait till Dhuum is dead
    bot_instance.Wait.UntilCondition(
        lambda: any(
            Agent.IsGadget(agent_id)
            and "underworld chest" in (Agent.GetNameByID(agent_id) or "").strip().lower()
            and Utils.Distance((-14381.0, 17283.0), Agent.GetXY(agent_id)) <= 300
            for agent_id in AgentArray.GetAgentArray()
        )
    )  # Wait until the Underworld Chest (Gadget) appears near (-14381, 17283)


    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_combat_enabled(False), "Disable Combat")


    def _loot_underworld_chest():
        chest_id = next(
            (
                agent_id for agent_id in AgentArray.GetAgentArray()
                if Agent.IsGadget(agent_id)
                and "underworld chest" in (Agent.GetNameByID(agent_id) or "").strip().lower()
                and Utils.Distance((-14381.0, 17283.0), Agent.GetXY(agent_id)) <= 300
            ),
            None,
        )
        if chest_id is None:
            ConsoleLog(BOT_NAME, "[Dhuum] Underworld Chest not found for looting!", Py4GW.Console.MessageType.Warning)
            return

        my_email = Player.GetAccountEmail()
        current_map_id = Map.GetMapID()
        all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        same_map_accounts = [
            acc for acc in all_accounts
            if acc.AgentData.Map.MapID == current_map_id
        ]

        ConsoleLog(BOT_NAME, f"[Dhuum] Looting chest with {len(same_map_accounts)} account(s)", Py4GW.Console.MessageType.Info)

        for account in same_map_accounts:
            email = str(account.AccountEmail)
            msg_index = GLOBAL_CACHE.ShMem.SendMessage(
                sender_email=my_email,
                receiver_email=email,
                command=SharedCommandType.InteractWithTarget,
                params=(chest_id, 0, 0, 0),
            )
            if msg_index < 0:
                ConsoleLog(BOT_NAME, f"[Dhuum] Failed to send InteractWithTarget to {email}", Py4GW.Console.MessageType.Warning)
            else:
                ConsoleLog(BOT_NAME, f"[Dhuum] Sent InteractWithTarget (chest) to {email}", Py4GW.Console.MessageType.Info)
            yield from Routines.Yield.wait(5000)

    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(True), "Enable Following")
    bot_instance.States.AddCustomState(
        lambda: CustomBehaviorParty().party_flagging_manager.clear_all_flags(),
        "Clear Flags",
    )        

    bot_instance.States.AddCustomState(_loot_underworld_chest, "Loot Underworld Chest")

    bot_instance.Wait.ForTime(5000)  # Wait for looting to finish    

    bot_instance.States.AddCustomState(_loot_underworld_chest, "Loot Underworld Chest")

    bot_instance.Wait.ForTime(5000)  # Wait for any stragglers to finish looting
    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_looting_enabled(False), "Disable Looting")
    bot_instance.Move.XY(-14324, 17549)
    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_looting_enabled(True), "Enable Looting")
    bot_instance.Wait.ForTime(5000)
    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_looting_enabled(False), "Disable Looting")
    bot_instance.Move.XY(-14243, 17017)
    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_looting_enabled(True), "Enable Looting")
    bot_instance.Wait.ForTime(5000)
    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_combat_enabled(True), "Enable Combat")



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


def _draw_dhuum_settings() -> None:
    PyImGui.text_wrapped("Select the multibox accounts to be sacrificed in the Dhuum fight.")
    PyImGui.separator()

    my_email = Player.GetAccountEmail()
    all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()

    if not all_accounts:
        PyImGui.text("No multibox account data available.")
        return

    for account in all_accounts:
        email = str(account.AccountEmail)
        char_name = str(account.AgentData.CharacterName) or email
        if email == my_email:
            PyImGui.begin_disabled(True)
            PyImGui.checkbox(f"{char_name}  (this account)", False)
            PyImGui.end_disabled()
        else:
            current = DhuumSettings.is_sacrifice(email)
            new_val = PyImGui.checkbox(char_name, current)
            if new_val != current:
                DhuumSettings.set_sacrifice(email, new_val)


def _draw_quest_settings():
    _snapshot = (BotSettings.Repeat, BotSettings.UseCons, BotSettings.HardMode)
    BotSettings.Repeat   = PyImGui.checkbox("Resign and Repeat after", BotSettings.Repeat)
    BotSettings.UseCons  = PyImGui.checkbox("Use Cons", BotSettings.UseCons)
    BotSettings.HardMode = PyImGui.checkbox("Hard Mode", BotSettings.HardMode)
    _current = (BotSettings.Repeat, BotSettings.UseCons, BotSettings.HardMode)
    if _current != _snapshot:
        BotSettings.save()




bot.SetMainRoutine(bot_routine)

def _draw_settings():
    if PyImGui.begin_tab_bar("##uw_settings_tabs"):
        if PyImGui.begin_tab_item("Quests"):
            _draw_quest_settings()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Inventory"):
            _draw_inventory_settings()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Dhuum"):
            _draw_dhuum_settings()
            PyImGui.end_tab_item()
        PyImGui.end_tab_bar()


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