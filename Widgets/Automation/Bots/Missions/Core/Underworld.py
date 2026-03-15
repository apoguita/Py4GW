# region â”€â”€ Imports â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

from Py4GWCoreLib import (
    Botting, Routines, Agent, AgentArray, Player,
    Utils, AutoPathing, GLOBAL_CACHE, ConsoleLog, Map, Pathing,
    FlagPreference, Party,
)
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

# endregion

# region â”€â”€ Module Setup â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

MODULE_NAME = "Underworld Helper"
MODULE_ICON = "Textures/Module_Icons/Underworld.png"
BOT_NAME    = "Underworld Helper"

bot = Botting(BOT_NAME, config_draw_path=True)
bot.Templates.Aggressive()
bot.UI.override_draw_help(lambda: _draw_help())
bot.UI.override_draw_config(lambda: _draw_settings())

MAIN_LOOP_HEADER_NAME = ""

# Set to True once the dungeon map (72) is loaded.
# The main-loop watchdog reads this to detect wipes that the event callback missed.
_entered_dungeon: bool = False


def _mark_entered_dungeon() -> None:
    global _entered_dungeon
    _entered_dungeon = True

# endregion

# region â”€â”€ Bot Settings â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class BotSettings:
    """Static configuration class â€“ all flags are toggled via the settings UI."""

    # -- Quest toggles --
    RestoreVale: bool = True       # Working
    WrathfullSpirits: bool = True  # Working (can be improved)
    EscortOfSouls: bool = True     # Working
    UnwantedGuests: bool = True    # Not working yet
    RestoreWastes: bool = True     # Working
    ServantsOfGrenth: bool = True  # Working
    PassTheMountains: bool = True  # Working
    RestoreMountains: bool = True  # Working
    DeamonAssassin: bool = True    # Working
    RestorePlanes: bool = True     # Working
    TheFourHorsemen: bool = True   # Working
    RestorePools: bool = True      # Working (Reaper sometimes dies)
    TerrorwebQueen: bool = True    # Working
    RestorePit: bool = True        # Not working yet
    ImprisonedSpirits: bool = True # Not working yet

    # -- Run options --
    Repeat: bool = False           # Resign and restart after completing a run
    UseCons: bool = False          # Withdraw + auto-renew + immediately use consets

# endregion

# region â”€â”€ Custom Behavior Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _get_custom_behavior(initialize_if_needed: bool = True):
    """Return the active custom combat behavior, optionally initializing it."""
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
    """Enable or disable a single utility in the active custom behavior by name or class."""
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

# endregion

# region â”€â”€ Behavior Toggles â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Thin wrappers around _set_custom_utility_enabled for each skill slot.
# Passing True enables the utility, False disables it.

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

# endregion

# region â”€â”€ Custom Behavior Integration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _setup_custom_behavior_integration(bot_instance: Botting) -> None:
    """One-time setup: load the custom behavior and attach it to the bot FSM."""
    behavior = _get_custom_behavior(initialize_if_needed=True)
    if behavior is None:
        ConsoleLog(BOT_NAME, "[CB] No custom behavior found. Bot runs without CB integration.", Py4GW.Console.MessageType.Warning)
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
    """Called every frame: keeps the CB daemon alive and the behavior initialized."""
    loader = CustomBehaviorLoader()
    loader.ensure_botting_daemon_running()

    behavior = loader.custom_combat_behavior
    if behavior is None:
        loader.initialize_custom_behavior_candidate()


def _ensure_custom_botting_skills_enabled() -> None:
    """Force-enable the required botting skills, in case they were turned off globally."""
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
        ConsoleLog(BOT_NAME, "[CB] Required botting skills were re-enabled for this bot.", Py4GW.Console.MessageType.Info)


def _reactivate_custom_behavior_for_step(bot_instance: Botting, step_label: str) -> None:
    """Re-attach CB integration before each major quest section."""
    behavior = _get_custom_behavior(initialize_if_needed=True)
    if behavior is None:
        ConsoleLog(BOT_NAME, f"[CB] No behavior available for step '{step_label}'.", Py4GW.Console.MessageType.Warning)
        return

    _ensure_custom_botting_skills_enabled()
    BottingFsmHelpers.SetBottingBehaviorAsAggressive(bot_instance)
    BottingFsmHelpers.UseCustomBehavior(
        bot_instance,
        on_player_critical_death=BottingHelpers.botting_unrecoverable_issue,
        on_party_death=BottingHelpers.botting_unrecoverable_issue,
        on_player_critical_stuck=BottingHelpers.botting_unrecoverable_issue,
    )

# endregion

# region â”€â”€ FSM / Section Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _enqueue_section(bot_instance: Botting, attr_name: str, label: str, section_fn) -> None:
    """Add a named FSM header and re-activate CB, then enqueue the section."""
    bot_instance.States.AddHeader(label)
    bot_instance.States.AddCustomState(
        lambda l=label: _reactivate_custom_behavior_for_step(bot_instance, l),
        f"[Setup] {label}",
    )
    section_fn(bot_instance)


def _add_header_with_name(bot_instance: Botting, step_name: str) -> str:
    """Insert a named no-op step used as a jump target (e.g. for the main loop restart)."""
    header_name = f"[H]{step_name}_{bot_instance.config.get_counter('HEADER_COUNTER')}"
    bot_instance.config.FSM.AddYieldRoutineStep(
        name=header_name,
        coroutine_fn=lambda: Routines.Yield.wait(100),
    )
    return header_name


def _restart_main_loop(bot_instance: Botting, reason: str) -> None:
    """Jump the FSM back to the main-loop header (used after wipes)."""
    global _entered_dungeon
    _entered_dungeon = False
    target = MAIN_LOOP_HEADER_NAME
    fsm = bot_instance.config.FSM
    fsm.pause()
    try:
        if target:
            fsm.jump_to_state_by_name(target)
            ConsoleLog(BOT_NAME, f"[WIPE] {reason} - restarting at {target}.", Py4GW.Console.MessageType.Info)
        else:
            ConsoleLog(BOT_NAME, "[WIPE] MAIN_LOOP header missing, restarting from first state.", Py4GW.Console.MessageType.Warning)
            fsm.jump_to_state_by_step_number(0)
    except ValueError:
        ConsoleLog(BOT_NAME, f"[WIPE] Header '{target}' not found, restarting from first state.", Py4GW.Console.MessageType.Error)
        fsm.jump_to_state_by_step_number(0)
    finally:
        fsm.resume()

# endregion

# region â”€â”€ Utility Functions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _use_consets_now() -> None:
    """Use conset items immediately at runtime (not via the FSM yield-step decorator).

    Called via AddCustomState so BotSettings.UseCons is evaluated at FSM
    *execution* time, not at build time.  Skips any conset whose buff is
    already active on the player.
    """
    if not BotSettings.UseCons:
        return
    from Py4GWCoreLib.enums_src.Model_enums import ModelID as _ModelID
    conset_info = (
        (_ModelID.Essence_Of_Celerity.value, GLOBAL_CACHE.Skill.GetID("Essence_of_Celerity_item_effect")),
        (_ModelID.Grail_Of_Might.value,      GLOBAL_CACHE.Skill.GetID("Grail_of_Might_item_effect")),
        (_ModelID.Armor_Of_Salvation.value,  GLOBAL_CACHE.Skill.GetID("Armor_of_Salvation_item_effect")),
    )
    player_id = Player.GetAgentID()
    for model_id, effect_id in conset_info:
        if GLOBAL_CACHE.Effects.HasEffect(player_id, effect_id):
            continue
        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
        if item_id:
            GLOBAL_CACHE.Inventory.UseItem(item_id)


def _ensure_minimum_gold(bot_instance: Botting, minimum_gold: int = 1000, withdraw_amount: int = 10000) -> None:
    """Withdraw gold from storage if the character carries less than minimum_gold."""
    def _check_and_restock():
        gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
        if gold_on_char >= minimum_gold:
            return

        gold_in_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()
        amount_to_withdraw = min(withdraw_amount, gold_in_storage)

        if amount_to_withdraw <= 0:
            ConsoleLog(BOT_NAME, "[GOLD] Storage empty - cannot restock gold.", Py4GW.Console.MessageType.Warning)
            return

        ConsoleLog(
            BOT_NAME,
            f"[GOLD] Only {gold_on_char}g on character. Withdrawing {amount_to_withdraw}g from storage.",
            Py4GW.Console.MessageType.Info,
        )
        GLOBAL_CACHE.Inventory.WithdrawGold(amount_to_withdraw)

    bot_instance.States.AddCustomState(_check_and_restock, "Ensure Minimum Gold")
    bot_instance.Wait.ForTime(1000)


def _flag_both(party_pos: int, flag_index: int, x, y) -> None:
    """Set hero flag via both the CB shared-memory system and the native GW API."""
    _set_flag_position(flag_index, x, y)
    agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(party_pos)
    if agent_id:
        GLOBAL_CACHE.Party.Heroes.FlagHero(agent_id, x, y)


def _enqueue_spread_flags(bot_instance: Botting, flag_points: list[tuple[int, int]]) -> None:
    """Clear all hero flags, auto-assign emails, then spread heroes to the given positions."""
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


def WaitTillQuestDone(bot_instance: Botting, quest_id: int) -> None:
    """Block the FSM until the given quest ID is marked as completed."""
    from Py4GWCoreLib.Quest import Quest
    bot_instance.Wait.UntilCondition(lambda: Quest.IsQuestCompleted(quest_id))


def FocusKeeperOfSouls(bot_instance: Botting) -> None:
    """Set the party\'s custom target to the nearest living Keeper of Souls."""
    KEEPER_OF_SOULS_MODEL_ID = 2373

    def _focus_logic():
        enemies = [
            e for e in AgentArray.GetEnemyArray()
            if Agent.IsAlive(e) and Agent.GetModelID(e) == KEEPER_OF_SOULS_MODEL_ID
        ]
        if not enemies:
            return
        player_pos = Player.GetXY()
        closest = min(
            enemies,
            key=lambda e: (player_pos[0] - Agent.GetXYZ(e)[0]) ** 2 + (player_pos[1] - Agent.GetXYZ(e)[1]) ** 2,
        )
        CustomBehaviorParty().set_party_custom_target(closest)

    bot_instance.States.AddCustomState(_focus_logic, "Focus Keeper of Souls")


def Wait_for_Spawns(bot_instance: Botting, x: float, y: float) -> None:
    """Move to (x, y) and wait until no Mindblade Spectres (model 2380) are nearby."""
    MINDBLADE_MODEL_ID = 2380

    bot_instance.Move.XY(x, y, "Move to spawn-check position")

    def _no_mindblades() -> bool:
        enemies = [
            e for e in AgentArray.GetEnemyArray()
            if Agent.IsAlive(e) and Agent.GetModelID(e) == MINDBLADE_MODEL_ID
        ]
        if not enemies:
            return True
        bot_instance.Move.XY(x, y, "Back to spawn-check position")
        return False

    # Check up to three times with a short pause between attempts
    for label in ("1", "2", "3"):
        bot_instance.Wait.UntilCondition(_no_mindblades)
        bot_instance.Wait.ForTime(1000)
        bot_instance.Move.XY(x, y, label)

    bot_instance.Wait.UntilCondition(_no_mindblades)

# endregion

# region â”€â”€ Movement: Unstuck â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _move_with_unstuck(
    bot_instance: Botting,
    target_x: float,
    target_y: float,
    step_name: str = "",
    stuck_check_ms: int = 1500,
    stuck_threshold: float = 80.0,
    backup_ms: int = 700,
    detour_offset: float = 600.0,
    max_detours: int = 3,
) -> None:
    """Move to (target_x, target_y) with automatic stuck recovery.

    Every stuck_check_ms milliseconds the coroutine checks whether the player
    advanced at least stuck_threshold units. If not:
      1. Issues /stuck to let GW attempt a server-side teleport.
      2. Walks backwards for backup_ms to create distance from the obstacle.
      3. Inserts a perpendicular detour waypoint (alternating left/right).
    Falls back to FollowPath after max_detours failed attempts.
    """
    import math
    import random

    def _coro():
        tolerance = 150.0
        tx, ty = target_x, target_y
        detour_parity = 1  # +1 = detour left, -1 = right; alternates each attempt

        for attempt in range(max_detours + 1):
            px, py = Player.GetXY()
            if math.sqrt((tx - px) ** 2 + (ty - py) ** 2) <= tolerance:
                return  # already at destination

            # GW ignores repeated Player.Move calls with identical coords - add jitter
            Player.Move(tx + random.uniform(-8, 8), ty + random.uniform(-8, 8))
            snapshot_pos = (px, py)
            snapshot_time = Utils.GetBaseTimestamp()
            reached = False
            cpx, cpy = px, py

            while True:
                yield from Routines.Yield.wait(250)
                cpx, cpy = Player.GetXY()

                if math.sqrt((tx - cpx) ** 2 + (ty - cpy) ** 2) <= tolerance:
                    reached = True
                    break

                # Re-issue movement each frame so GW never ignores the command
                Player.Move(tx + random.uniform(-8, 8), ty + random.uniform(-8, 8))

                now = Utils.GetBaseTimestamp()
                if now - snapshot_time >= stuck_check_ms:
                    movement = math.sqrt((cpx - snapshot_pos[0]) ** 2 + (cpy - snapshot_pos[1]) ** 2)
                    if movement < stuck_threshold:
                        break  # stuck detected
                    # Made enough progress - reset snapshot
                    snapshot_pos = (cpx, cpy)
                    snapshot_time = now

            if reached:
                return

            if attempt >= max_detours:
                ConsoleLog(BOT_NAME, f"[Unstuck] Max detours reached - using FollowPath fallback to ({tx:.0f},{ty:.0f})", Py4GW.Console.MessageType.Warning)
                yield from Routines.Yield.Movement.FollowPath(path_points=[(tx, ty)])
                return

            ConsoleLog(BOT_NAME, f"[Unstuck] Stuck en route to ({tx:.0f},{ty:.0f}), attempt {attempt + 1}/{max_detours}", Py4GW.Console.MessageType.Warning)

            # Step 1: /stuck - server-side recovery, may teleport us clear
            Player.SendChatCommand("stuck")
            yield from Routines.Yield.wait(1000)
            cpx, cpy = Player.GetXY()
            if math.sqrt((tx - cpx) ** 2 + (ty - cpy) ** 2) <= tolerance:
                return

            # Step 2: walk backwards to clear the obstacle
            yield from Routines.Yield.Movement.WalkBackwards(backup_ms)

            # Step 3: perpendicular bypass from the backed-up position
            px, py = Player.GetXY()
            dx, dy = tx - px, ty - py
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 50:
                return  # close enough after backing up

            nx, ny = dx / dist, dy / dist
            perp_x, perp_y = (-ny, nx) if detour_parity > 0 else (ny, -nx)
            detour_parity = -detour_parity

            mid_x = px + nx * min(dist * 0.4, 400.0) + perp_x * detour_offset
            mid_y = py + ny * min(dist * 0.4, 400.0) + perp_y * detour_offset

            ConsoleLog(BOT_NAME, f"[Unstuck] Detour via ({mid_x:.0f},{mid_y:.0f}) then ({tx:.0f},{ty:.0f})", Py4GW.Console.MessageType.Info)
            yield from Routines.Yield.Movement.FollowPath(path_points=[(mid_x, mid_y)])

    label = step_name or f"MoveUnstuck_{target_x:.0f}_{target_y:.0f}"
    bot_instance.config.FSM.AddYieldRoutineStep(name=label, coroutine_fn=_coro)

# endregion

# region â”€â”€ Default Party Behavior â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def enable_default_party_behavior(bot_instance: Botting) -> None:
    """Enable the standard set of party-behavior toggles used by most quest sections."""
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True),    "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True),   "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True),    "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(True), "Enable Follow")
    bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_looting_enabled(True),   "Enable Looting")


def _set_standard_toggles(bot_instance: Botting,
                           *,
                           move_to_enemy: bool = True,
                           move_to_dead: bool = True) -> None:
    """Apply the standard toggle block at the start of every quest section.

    Most sections share the same on/off values; pass keyword args for the few that differ.
    """
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True),                              "Enable  WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True),                             "Enable  WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True),                              "Enable  MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda v=move_to_enemy: _toggle_move_to_enemy_if_close_enough(v), "Toggle MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda v=move_to_dead:  _toggle_move_to_party_member_if_dead(v),  "Toggle MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False),        "Disable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False),                                      "Disable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False),         "Disable WaitIfPartyMemberManaTooLow")

# endregion

# region â”€â”€ Bot Routine (FSM builder) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def bot_routine(bot: Botting) -> None:
    """Build the full FSM for a single Underworld run."""
    global MAIN_LOOP_HEADER_NAME

    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    CustomBehaviorParty().set_party_is_blessing_enabled(True)
    _setup_custom_behavior_integration(bot)
    bot.Templates.Aggressive()

    # Named anchor used by _restart_main_loop to jump back to the top
    MAIN_LOOP_HEADER_NAME = _add_header_with_name(bot, "MAIN_LOOP")

    bot.Map.Travel(target_map_id=138)   # Travel to Chantry of Secrets (outpost)
    bot.Party.SetHardMode(False)

    Enter_UW(bot)
    Clear_the_Chamber(bot)

    _enqueue_section(bot, "RestoreVale",       "Restore Vale",       Restore_Vale)
    _enqueue_section(bot, "WrathfullSpirits",  "Wrathful Spirits",   Wrathfull_Spirits)
    #_enqueue_section(bot, "EscortOfSouls",    "Escort of Souls",    Escort_of_Souls)  # disabled - needs testing
    _enqueue_section(bot, "UnwantedGuests",    "Unwanted Guests",    Unwanted_Guests)
    _enqueue_section(bot, "RestoreWastes",     "Restore Wastes",     Restore_Wastes)
    _enqueue_section(bot, "ServantsOfGrenth",  "Servants of Grenth", Servants_of_Grenth)
    _enqueue_section(bot, "PassTheMountains",  "Pass the Mountains", Pass_The_Mountains)
    _enqueue_section(bot, "RestoreMountains",  "Restore Mountains",  Restore_Mountains)
    _enqueue_section(bot, "DeamonAssassin",    "Daemon Assassin",    Deamon_Assassin)
    _enqueue_section(bot, "RestorePlanes",     "Restore Planes",     Restore_Planes)
    _enqueue_section(bot, "TheFourHorsemen",   "The Four Horsemen",  The_Four_Horsemen)
    _enqueue_section(bot, "RestorePools",      "Restore Pools",      Restore_Pools)
    _enqueue_section(bot, "TerrorwebQueen",    "Terrorweb Queen",    Terrorweb_Queen)
    _enqueue_section(bot, "RestorePit",        "Restore Pit",        Restore_Pit)
    _enqueue_section(bot, "ImprisonedSpirits", "Imprisoned Spirits", Imprisoned_Spirits)
    _enqueue_section(bot, "Repeat",            "Resign and Repeat",  ResignAndRepeat)

    bot.States.AddHeader("END")

# endregion

# region â”€â”€ Quest: Enter Underworld â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def Enter_UW(bot_instance: Botting) -> None:
    """Travel to the Underworld, accept the entry dialog, and use consets if enabled."""
    bot_instance.States.AddHeader("Enter Underworld")
    _ensure_minimum_gold(bot_instance)

    if BotSettings.UseCons:
        # Withdraw 10 conset stacks (Essence / Grail / Armor) from the Xunlai chest
        bot_instance.Multibox.RestockConset(10)

    CustomBehaviorParty().set_party_leader_email(Player.GetAccountEmail())
    bot_instance.Move.XY(-4199, 19845, "Move to Reaper statue")
    bot_instance.States.AddCustomState(lambda: Player.SendChatCommand("kneel"), "Kneel")
    bot_instance.Wait.ForTime(3000)
    bot_instance.Dialogs.AtXY(-4199, 19845, 0x86, "Accept dungeon entry dialog")
    bot_instance.Wait.ForMapLoad(target_map_id=72)  # Wait until inside the Underworld (map 72)
    bot_instance.States.AddCustomState(_mark_entered_dungeon, "Mark: entered dungeon")
    bot_instance.Properties.ApplyNow("pause_on_danger", "active", True)

    # Enable conset auto-renewal and consume one set right after entering the dungeon.
    # Both AddCustomState calls are ALWAYS added to the FSM so that BotSettings.UseCons
    # is evaluated at *execution* time, not at build time.  The user can toggle the
    # 'Use Consets' checkbox in the UI without restarting the bot.
    bot_instance.States.AddCustomState(
        lambda: (
            bot_instance.Properties.ApplyNow("armor_of_salvation",  "active", True),
            bot_instance.Properties.ApplyNow("essence_of_celerity", "active", True),
            bot_instance.Properties.ApplyNow("grail_of_might",      "active", True),
        ) if BotSettings.UseCons else None,
        "Enable Conset Auto-renewal (runtime check)")
    bot_instance.States.AddCustomState(
        _use_consets_now,
        "Use Consets (runtime check)")

# endregion

# region â”€â”€ Quest: Clear the Chamber â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def Clear_the_Chamber(bot_instance: Botting) -> None:
    """Accept the first quest, clear the Chamber of Secrets, and talk to the Vale Reaper."""
    bot_instance.States.AddHeader("Clear the Chamber")
    CustomBehaviorParty().set_party_leader_email(Player.GetAccountEmail())
    enable_default_party_behavior(bot_instance)

    # Accept "Clear the Chamber" quest from the Reaper of the Labyrinth
    bot_instance.Move.XYAndInteractNPC(295, 7221, "Move to Labyrinth Reaper")
    bot_instance.Dialogs.AtXY(295, 7221, 0x806501, "Accept: Clear the Chamber")

    # Move into position and hold Close_to_Aggro for 5s to engage spawns
    bot_instance.Move.XY(769, 6564, "Prepare to engage")
    bot_instance.States.AddCustomState(
        lambda: CustomBehaviorParty().set_party_forced_state(BehaviorState.CLOSE_TO_AGGRO),
        "Force Close_to_Aggro",
    )
    bot_instance.Wait.ForTime(5000)
    bot_instance.States.AddCustomState(
        lambda: CustomBehaviorParty().set_party_forced_state(None),
        "Release Close_to_Aggro",
    )

    # Re-enable all combat toggles after the forced engage phase
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True),                       "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True),                      "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True),                       "Enable MoveIfPartyMemberInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_enemy_if_close_enough(True),       "Enable MoveToEnemyIfCloseEnough")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True),        "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_needs_to_loot(False), "Disable WaitIfPartyMemberNeedsToLoot")
    bot_instance.States.AddCustomState(lambda: _toggle_lock(False),                               "Disable WaitIfLockTaken")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_party_member_mana_too_low(False),  "Disable WaitIfPartyMemberManaTooLow")

    # Clear the chamber by sweeping key waypoints
    bot_instance.Move.XY(-1505,  6352, "Wing: Left")
    bot_instance.Move.XY(-755,   8982, "Wing: Mid")
    bot_instance.Move.XY(1259,  10214, "Wing: Right")
    bot_instance.Move.XY(-3729, 13414, "Wing: Far right")
    bot_instance.Move.XY(-5855, 11202, "Clear the room")
    bot_instance.Wait.ForTime(3000)

    # Talk to the Vale Reaper to hand in the quest
    bot_instance.Move.XYAndInteractNPC(-5806, 12831, "Move to Vale Reaper")
    bot_instance.Wait.ForTime(3000)
    bot_instance.Dialogs.AtXY(-5806, 12831, 0x806D01, "Accept: next quest from Vale Reaper")
    bot_instance.Wait.ForTime(3000)

# endregion

# region â”€â”€ Quest: Restore Vale â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def Restore_Vale(bot_instance: Botting) -> None:
    """Travel to the Vale and restore Grenth\'s Monument there."""
    _set_standard_toggles(bot_instance, move_to_enemy=False)

    if BotSettings.RestoreVale:
        if BotSettings.EscortOfSouls:
            # Accept Escort of Souls at the same time if it\'s enabled
            bot_instance.Dialogs.AtXY(-5806, 12831, 0x806C03, "Take: Escort of Souls (part 1)")
            bot_instance.Dialogs.AtXY(-5806, 12831, 0x806C01, "Take: Escort of Souls (part 2)")

        # Path to the Vale monument
        bot_instance.Move.XY(-8660,   5655, "To Vale 1")
        bot_instance.Move.XY(-9431,   1659, "To Vale 2")
        bot_instance.Move.XY(-11123,  2531, "To Vale 3")
        bot_instance.Move.XY(-10212,   251, "To Vale 4")
        bot_instance.Move.XY(-13085,   849, "To Vale 5")
        bot_instance.Move.XY(-15274,  1432, "To Vale 6")
        bot_instance.Move.XY(-13246,  5110, "To Vale 7")

        bot_instance.Move.XYAndInteractNPC(-13275, 5261, "Interact: Vale monument Reaper")

        if not BotSettings.WrathfullSpirits:
            bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "TP back to Chamber")

        bot_instance.Wait.ForTime(3000)

# endregion

# region â”€â”€ Quest: Wrathful Spirits â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def Wrathfull_Spirits(bot_instance: Botting) -> None:
    """Kill the Wrathful Spirits in the Vale without engaging other enemies."""
    _set_standard_toggles(bot_instance)

    if BotSettings.WrathfullSpirits:
        bot_instance.Move.XYAndInteractNPC(-13275, 5261, "Move to Vale Reaper")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x806E03, "Take: Wrathful Spirits (part 1)")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x806E01, "Take: Wrathful Spirits (part 2)")

        # Switch to Pacifist to move through enemies without fighting
        bot_instance.Templates.Pacifist()
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
        bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(False),  "Disable WaitIfInAggro")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_combat_enabled(False), "Disable Combat")

        bot_instance.Move.XY(-13422, 973, "Approach Wrathful Spirits")

        # Switch back to Aggressive to fight the spirits
        bot_instance.Templates.Aggressive()
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_combat_enabled(True), "Enable Combat")
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
        bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True),  "Enable WaitIfInAggro")

        bot_instance.Move.XY(-10207,  1746, "Wrathful Spirits 2")
        bot_instance.Move.XY(-13287,  1996, "Wrathful Spirits 3")
        bot_instance.Move.XY(-15226,  4129, "Wrathful Spirits 4")
        bot_instance.Move.XYAndInteractNPC(-13275, 5261, "Move to Vale Reaper")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "TP back to Chamber")
        bot_instance.Wait.ForTime(3000)

# endregion

# region â”€â”€ Quest: Escort of Souls â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def Escort_of_Souls(bot_instance: Botting) -> None:
    """Escort the Forgotten Souls from the Vale back to the Chamber."""
    _set_standard_toggles(bot_instance)

    if BotSettings.EscortOfSouls:
        bot_instance.Wait.ForTime(5000)
        bot_instance.Move.XY(-4764, 11845, "Escort start")
        bot_instance.Move.XYAndInteractNPC(-5806, 12831, "Move to Vale Reaper")
        bot_instance.Wait.ForTime(3000)
        bot_instance.Dialogs.AtXY(-5806, 12831, 0x806C03, "Take: Escort of Souls (part 1)")
        bot_instance.Dialogs.AtXY(-5806, 12831, 0x806C01, "Take: Escort of Souls (part 2)")
        bot_instance.Move.XY(-6833,  7077, "Escort 2")
        bot_instance.Move.XY(-9606,  2110, "Escort 3")
        bot_instance.Move.XYAndInteractNPC(-13275, 5261, "Move to Vale Reaper")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "TP back to Chamber")
        bot_instance.Wait.ForTime(3000)

# endregion

# region â”€â”€ Quest: Unwanted Guests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def Unwanted_Guests(bot_instance: Botting) -> None:
    """Kill all six Keepers of Souls spread across the Chamber area.

    NOTE: This quest is not fully reliable yet.
    """
    _set_standard_toggles(bot_instance)

    if BotSettings.UnwantedGuests:
        # --- 1st Keeper ---
        _move_with_unstuck(bot_instance, -2965, 10260, "1st Keeper approach")
        bot_instance.Wait.ForTime(5000)
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(False), "Disable Following")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_forced_state(BehaviorState.CLOSE_TO_AGGRO), "Force Close_to_Aggro")
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
        bot_instance.Move.XYAndInteractNPC(-5806, 12831, "Move to Vale Reaper")
        bot_instance.Dialogs.AtXY(-5806, 12831, 0x806701, "Take: Unwanted Guests")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_forced_state(None), "Release Close_to_Aggro")
        FocusKeeperOfSouls(bot_instance)
        bot_instance.Wait.ForTime(500)
        FocusKeeperOfSouls(bot_instance)
        bot_instance.Wait.ForTime(500)
        FocusKeeperOfSouls(bot_instance)
        bot_instance.Wait.ForTime(20000)
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(True), "Enable Following")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_forced_state(None), "Release Close_to_Aggro")

        # --- 2nd Keeper ---
        bot_instance.Move.XYAndInteractNPC(-5806, 12831, "Move to Vale Reaper")
        bot_instance.Dialogs.AtXY(-5806, 12831, 0x91, "Dialog: 2nd Keeper")
        _move_with_unstuck(bot_instance, -12953,  750, "2nd Keeper 1")
        _move_with_unstuck(bot_instance, -8371,  4865, "2nd Keeper 2")
        FocusKeeperOfSouls(bot_instance)
        bot_instance.Wait.ForTime(500)
        FocusKeeperOfSouls(bot_instance)
        _move_with_unstuck(bot_instance, -7589,  6801, "2nd Keeper killed")

        # --- 3rd Keeper ---
        _move_with_unstuck(bot_instance, -4095, 12964, "3rd Keeper approach")
        FocusKeeperOfSouls(bot_instance)
        bot_instance.Wait.ForTime(500)
        FocusKeeperOfSouls(bot_instance)
        _move_with_unstuck(bot_instance, -647,  13356, "3rd Keeper killed")

        # --- 4th Keeper ---
        _move_with_unstuck(bot_instance,  1098, 12215, "4th Keeper approach")
        FocusKeeperOfSouls(bot_instance)
        bot_instance.Wait.ForTime(500)
        FocusKeeperOfSouls(bot_instance)
        _move_with_unstuck(bot_instance,  3113,  9503, "4th Keeper killed")

        # --- 5th Keeper ---
        _move_with_unstuck(bot_instance,  1586, 10362, "5th Keeper approach")
        FocusKeeperOfSouls(bot_instance)
        bot_instance.Wait.ForTime(500)
        FocusKeeperOfSouls(bot_instance)
        _move_with_unstuck(bot_instance,   367,  7214, "5th Keeper killed")

        # --- 6th Keeper ---
        _move_with_unstuck(bot_instance, -3125,   916, "6th Keeper 1")
        _move_with_unstuck(bot_instance,  -344,  2155, "6th Keeper 2")
        FocusKeeperOfSouls(bot_instance)
        bot_instance.Wait.ForTime(500)
        FocusKeeperOfSouls(bot_instance)
        _move_with_unstuck(bot_instance,  1256,  4623, "6th Keeper killed")

# endregion

# region â”€â”€ Quest: Restore Wastes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def Restore_Wastes(bot_instance: Botting) -> None:
    """Travel to the Wastes monument and restore it."""
    _set_standard_toggles(bot_instance)

    if BotSettings.RestoreWastes:
        bot_instance.Templates.Aggressive()
        bot_instance.Properties.ApplyNow("pause_on_danger", "active", True)

        bot_instance.Move.XY(3891,   7572, "To Wastes 1")
        bot_instance.Move.XY(4106,  16031, "To Wastes 2")
        bot_instance.Move.XY(2486,  21723, "To Wastes 3")
        bot_instance.Move.XY(-1452, 21202, "To Wastes 4")
        bot_instance.Move.XY(542,   18310, "To Wastes 5")

        if not BotSettings.ServantsOfGrenth:
            bot_instance.Move.XYAndInteractNPC(554, 18384, "Move to Wastes Reaper")
            bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "TP back to Chamber")

        bot_instance.Wait.ForTime(3000)

# endregion

# region â”€â”€ Quest: Servants of Grenth â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def Servants_of_Grenth(bot_instance: Botting) -> None:
    """Spread heroes around the Servants of Grenth fight area and defeat them."""
    _set_standard_toggles(bot_instance)

    if BotSettings.ServantsOfGrenth:
        bot_instance.Templates.Aggressive()
        bot_instance.Move.XY(2700, 19952, "To Servants area 1")

        SERVANTS_FLAG_POINTS = [
            (2559, 20301),
            (3032, 20148),
            (2813, 20590),
            (2516, 19665),
            (3231, 19472),
            (3691, 19979),
            (2039, 20175),
        ]
        _enqueue_spread_flags(bot_instance, SERVANTS_FLAG_POINTS)

        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_forced_state(BehaviorState.CLOSE_TO_AGGRO), "Force Close_to_Aggro")
        bot_instance.Move.XYAndInteractNPC(554, 18384, "Move to Wastes Reaper")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(False), "Disable Following")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x806601, "Take: Servants of Grenth")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_forced_state(None), "Release Close_to_Aggro")

        bot_instance.Move.XY(2700, 19952, "To Servants area 2")
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(True), "Enable Following")

        bot_instance.Party.UnflagAllHeroes()
        bot_instance.Party.FlagAllHeroes(3032, 20148)
        bot_instance.Party.UnflagAllHeroes()
        bot_instance.Wait.ForTime(5000)
        bot_instance.Party.UnflagAllHeroes()
        bot_instance.States.AddCustomState(
            lambda: CustomBehaviorParty().party_flagging_manager.clear_all_flags(),
            "Clear Flags",
        )
        bot_instance.Wait.ForTime(10000)

        bot_instance.Move.XYAndInteractNPC(554, 18384, "Move to Wastes Reaper")
        bot_instance.Dialogs.AtXY(5755, 12769, 0x8D, "TP back to Chamber")
        bot_instance.Wait.ForTime(3000)

# endregion

# region â”€â”€ Quest: Pass the Mountains â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def Pass_The_Mountains(bot_instance: Botting) -> None:
    """Travel through the Mountains to reach the far areas."""
    _set_standard_toggles(bot_instance)

    if BotSettings.PassTheMountains:
        bot_instance.Move.XY(-220,   1691, "Mountains 1")
        bot_instance.Move.XY(7035,   1973, "Mountains 2")
        bot_instance.Move.XY(8089,  -3303, "Mountains 3")
        bot_instance.Move.XY(8121,  -6054, "Mountains 4")

# endregion

# region â”€â”€ Quest: Restore Mountains â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def Restore_Mountains(bot_instance: Botting) -> None:
    """Restore Grenth\'s Monument in the Mountains area."""
    _set_standard_toggles(bot_instance)

    if BotSettings.RestoreMountains:
        bot_instance.Move.XY(7013,  -7582, "Restore Mountains 1")
        bot_instance.Move.XY(1420,  -9126, "Restore Mountains 2")
        bot_instance.Move.XY(-8373, -5016, "Restore Mountains 3")

# endregion

# region â”€â”€ Quest: Daemon Assassin â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def Deamon_Assassin(bot_instance: Botting) -> None:
    """Kill the Demon Assassin (Grenth\'s Footprint). Slayer model ID: 2391."""
    _set_standard_toggles(bot_instance)

    if BotSettings.DeamonAssassin:
        bot_instance.Move.XYAndInteractNPC(-8250, -5171, "Move to Mountains Reaper")
        bot_instance.Wait.ForTime(3000)
        bot_instance.Dialogs.AtXY(-8250, -5171, 0x806801, "Take: Daemon Assassin")
        bot_instance.Move.XY(-1384, -3929, "Move to Assassin area")
        bot_instance.Wait.ForTime(30000)  # Wait for the kill

# endregion

# region â”€â”€ Quest: Restore Planes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def Restore_Planes(bot_instance: Botting) -> None:
    """Restore Grenth\'s Monument in the Planes, waiting for Mindblade Spectres to clear."""
    _set_standard_toggles(bot_instance)

    if BotSettings.RestorePlanes:
        Wait_for_Spawns(bot_instance,  10371, -10510)
        Wait_for_Spawns(bot_instance,  12795,  -8811)
        Wait_for_Spawns(bot_instance,  11180, -13780)
        Wait_for_Spawns(bot_instance,  13740, -15087)
        bot_instance.Move.XY(11546, -13787, "Restore Planes 1")
        bot_instance.Move.XY( 8530, -11585, "Restore Planes 2")
        Wait_for_Spawns(bot_instance,   8533, -13394)
        Wait_for_Spawns(bot_instance,   8579, -20627)
        Wait_for_Spawns(bot_instance,  11218, -17404)

# endregion

# region â”€â”€ Quest: The Four Horsemen â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def The_Four_Horsemen(bot_instance: Botting) -> None:
    """Defeat the Four Horsemen in two rounds, holding position around the monument."""
    _set_standard_toggles(bot_instance)

    if BotSettings.TheFourHorsemen:
        bot_instance.Move.XY(13473, -12091, "Move to Horsemen area")
        bot_instance.Wait.ForTime(10000)

        HORSEMEN_FLAGS_1 = [
            (13432, -12100),
            (13246, -12440),
            (13072, -12188),
            (13216, -11841),
            (13639, -11866),
            (13745, -12151),
            (13520, -12436),
        ]
        _enqueue_spread_flags(bot_instance, HORSEMEN_FLAGS_1)

        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_looting_enabled(False), "Disable Looting")
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
        bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(False),  "Disable MoveIfPartyMemberInAggro")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_forced_state(BehaviorState.CLOSE_TO_AGGRO), "Force Close_to_Aggro")
        bot_instance.Move.XYAndInteractNPC(11371, -17990, "Move to Planes Reaper")
        bot_instance.Dialogs.AtXY(-8250, -5171, 0x806A01, "Take: The Four Horsemen")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_forced_state(None), "Release Close_to_Aggro")
        bot_instance.Wait.ForTime(35000)  # Wait for first wave

        bot_instance.Move.XYAndInteractNPC(11371, -17990, "TP to Chamber")
        bot_instance.Dialogs.AtXY(11371, -17990, 0x8D, "Use TP: Chamber")
        bot_instance.States.AddCustomState(
            lambda: CustomBehaviorParty().party_flagging_manager.clear_all_flags(),
            "Clear Flags",
        )
        bot_instance.Wait.ForTime(1000)

        bot_instance.Move.XYAndInteractNPC(-5782, 12819, "TP back to Chaos Planes")
        bot_instance.Dialogs.AtXY(11371, -17990, 0x8B, "Use TP: Chaos Planes")
        bot_instance.Wait.ForTime(1000)
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(True), "Enable Following")

        HORSEMEN_FLAGS_2 = [
            (11318, -17670),
            (11318, -17670),
            (11221, -18335),
            (11479, -18361),
            (11806, -18134),
            (11697, -17748),
            (11354, -17530),
        ]
        _enqueue_spread_flags(bot_instance, HORSEMEN_FLAGS_2)
        bot_instance.Party.UnflagAllHeroes()
        bot_instance.Wait.ForTime(5000)

        bot_instance.Move.XY(11371, -17990, "Horsemen wave 2 position")
        bot_instance.Wait.ForTime(30000)
        bot_instance.Move.XY(11371, -17990, "Hold position")

        bot_instance.States.AddCustomState(
            lambda: CustomBehaviorParty().party_flagging_manager.clear_all_flags(),
            "Clear Flags",
        )
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_following_enabled(True), "Enable Following")
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
        bot_instance.States.AddCustomState(lambda: _toggle_move_if_aggro(True),  "Enable MoveIfPartyMemberInAggro")
        bot_instance.States.AddCustomState(lambda: CustomBehaviorParty().set_party_is_looting_enabled(True), "Enable Looting")

# endregion

# region â”€â”€ Quest: Restore Pools â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def Restore_Pools(bot_instance: Botting) -> None:
    """Restore Grenth\'s Monument in the Pools area."""
    _set_standard_toggles(bot_instance)

    if BotSettings.RestorePools:
        Wait_for_Spawns(bot_instance,  4647, -16833)
        Wait_for_Spawns(bot_instance,  2098, -15543)
        bot_instance.Move.XY(-12703, -10990, "Restore Pools 1")
        bot_instance.Move.XY(-11849, -11986, "Restore Pools 2")
        bot_instance.Move.XY( -7217, -19394, "Restore Pools 3")

        if not BotSettings.TerrorwebQueen:
            bot_instance.Move.XYAndInteractNPC(-6957, -19478, "Move to Pools Reaper")
            bot_instance.Dialogs.AtXY(-6957, -19478, 0x8B, "TP back to Chamber")

        bot_instance.Wait.ForTime(3000)

# endregion

# region â”€â”€ Quest: Terrorweb Queen â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def Terrorweb_Queen(bot_instance: Botting) -> None:
    """Kill the Terrorweb Queen in the Pools area."""
    _set_standard_toggles(bot_instance)

    if BotSettings.TerrorwebQueen:
        bot_instance.Move.XYAndInteractNPC(-6961, -19499, "Move to Pools Reaper")
        bot_instance.Dialogs.AtXY(-6961, -19499, 0x806B01, "Take: Terrorweb Queen")
        bot_instance.Move.XY(-12303, -15213, "Move to Queen area")
        bot_instance.Move.XYAndInteractNPC(-6957, -19478, "Move to Pools Reaper")
        bot_instance.Dialogs.AtXY(-6957, -19478, 0x8B, "TP back to Chamber")

# endregion

# region â”€â”€ Quest: Restore Pit â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def Restore_Pit(bot_instance: Botting) -> None:
    """Restore Grenth\'s Monument in the Pit area.

    NOTE: This quest is not fully reliable yet.
    """
    _set_standard_toggles(bot_instance, move_to_enemy=False)

    if BotSettings.RestorePit:
        _toggle_move_if_aggro(False)
        bot_instance.Move.XY(14178,   -57, "Restore Pit 1")
        bot_instance.Move.XY(15323,  2970, "Restore Pit 2")
        bot_instance.Move.XY(15393,   406, "Restore Pit 3")
        bot_instance.Move.FollowPath([
            (15252,  316),
            (13451, 1123),
            (13181, 1419),
            (13076, 1547),
        ], step_name="Cross the bridge")
        bot_instance.Move.XY(13216,  1428, "Restore Pit 4")
        bot_instance.Move.XY(13896,  3670, "Restore Pit 5")
        bot_instance.Move.XY(15382,  6581, "Restore Pit 6")
        bot_instance.Move.XY(10620,  2665, "Restore Pit 7")
        bot_instance.Move.XY( 8644,  6242, "Restore Pit 8")

        if not BotSettings.ImprisonedSpirits:
            bot_instance.Move.XYAndInteractNPC(8698, 6324, "Move to Pit Reaper")
            bot_instance.Dialogs.AtXY(8698, 6324, 0x8D, "TP back to Chamber")

        bot_instance.Wait.ForTime(3000)

# endregion

# region â”€â”€ Quest: Imprisoned Spirits â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def Imprisoned_Spirits(bot_instance: Botting) -> None:
    """Free the Imprisoned Spirits in the Pit area.

    NOTE: This quest is not fully reliable yet.
    """
    _set_standard_toggles(bot_instance, move_to_enemy=False)

    if BotSettings.ImprisonedSpirits:
        bot_instance.Move.XY(13212, 4978, "Approach Pit monument")

        IMPRISONED_FLAGS = [
            (13652,  6117),
            (13722,  6493),
            (13759,  6817),
            (12840,  3676),
            (12559,  3647),
            (12262,  3635),
            (11912,  3622),
        ]
        _enqueue_spread_flags(bot_instance, IMPRISONED_FLAGS)
        bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")

        bot_instance.Move.XY(8692, 6292, "Approach Pit Reaper")
        bot_instance.Move.XYAndInteractNPC(8666, 6308, "Move to Pit Reaper")
        bot_instance.Dialogs.AtXY(8666, 6308, 0x806901, "Take: Imprisoned Spirits")
        bot_instance.Move.XY(13652, 6117, "Move to left-flank team")
        bot_instance.Wait.ForTime(10000)

        bot_instance.States.AddCustomState(
            lambda: CustomBehaviorParty().party_flagging_manager.clear_all_flags(),
            "Clear Flags",
        )
        bot_instance.Move.XY(12593, 1814, "Hold position")
        WaitTillQuestDone(bot_instance, 105)  # Wait until quest 105 (Imprisoned Spirits) completes

        bot_instance.Move.XY(8692, 6292, "Return to Pit Reaper")
        bot_instance.Move.XYAndInteractNPC(8666, 6308, "Move to Pit Reaper")
        bot_instance.Multibox.SendDialogToTarget(0x806907)
        bot.Wait.ForTime(1000)
        bot_instance.Multibox.SendDialogToTarget(0x8C)

# endregion

# region â”€â”€ Resign and Repeat â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def ResignAndRepeat(bot_instance: Botting) -> None:
    """Resign the entire party to restart the run (only if Repeat is enabled)."""
    if BotSettings.Repeat:
        bot_instance.Multibox.ResignParty()

# endregion

# region â”€â”€ UI: Help Window â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _draw_help() -> None:
    PyImGui.text("Hey, this is my first bot in Python, be gentle :)")
    PyImGui.separator()
    PyImGui.text_wrapped("This bot automates the Underworld (The Underworld dungeon, map 72).")
    PyImGui.text("Optimised for 8x Custom Behaviors. HeroAI is untested; CB works but needs more testing.")
    PyImGui.text_wrapped("Watch the bot for at least one full run so you understand how it behaves.")
    PyImGui.text_wrapped("Some quests are still missing - feel free to contribute :)")
    PyImGui.separator()

    PyImGui.text("Working well:")
    PyImGui.bullet_text("Restoring all Grenth monuments (except Pit)")
    PyImGui.bullet_text("Wrathful Spirits, Escort of Souls, Servants of Grenth")
    PyImGui.bullet_text("Daemon Assassin, The Four Horsemen, Terrorweb Queen")

    PyImGui.text("Working poorly:")
    PyImGui.bullet_text("Imprisoned Spirits, Restore Pit")

    PyImGui.text("Not yet implemented:")
    PyImGui.bullet_text("Unwanted Guests (partially), The Nightman Cometh (Dhuum)")

    PyImGui.separator()
    PyImGui.text("Requirements:")
    PyImGui.bullet_text("High-end team (all 8 heroes with good builds)")
    PyImGui.bullet_text("Use consets for faster runs (enable via the settings tab)")
    PyImGui.bullet_text("Missing quests must be completed manually if enabled")
    PyImGui.bullet_text("The player character should NOT be the main healer")
    PyImGui.bullet_text("Have an Elementalist or melee char to trigger traps in the Mountains")
    PyImGui.separator()
    PyImGui.bullet_text("Have fun :)  - sch0l0ka")

# endregion

# region â”€â”€ UI: Settings Window â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _draw_settings() -> None:
    _draw_quest_settings()


def _draw_quest_settings() -> None:
    """Render the quest-selection checkboxes with dependency-aware disabling."""

    # Vale branch
    BotSettings.RestoreVale = PyImGui.checkbox("Restore Vale", BotSettings.RestoreVale)
    disable_vale = not BotSettings.RestoreVale
    if disable_vale:
        BotSettings.WrathfullSpirits = False
        BotSettings.EscortOfSouls   = False
    PyImGui.begin_disabled(disable_vale)
    BotSettings.WrathfullSpirits = PyImGui.checkbox("Wrathful Spirits", BotSettings.WrathfullSpirits)
    BotSettings.EscortOfSouls    = PyImGui.checkbox("Escort of Souls",  BotSettings.EscortOfSouls)
    BotSettings.UnwantedGuests   = PyImGui.checkbox("Unwanted Guests",  BotSettings.UnwantedGuests)
    PyImGui.end_disabled()

    # Wastes branch
    BotSettings.RestoreWastes = PyImGui.checkbox("Restore Wastes", BotSettings.RestoreWastes)
    disable_wastes = not BotSettings.RestoreWastes
    if disable_wastes:
        BotSettings.ServantsOfGrenth = False
    PyImGui.begin_disabled(disable_wastes)
    BotSettings.ServantsOfGrenth = PyImGui.checkbox("Servants of Grenth", BotSettings.ServantsOfGrenth)
    PyImGui.end_disabled()

    # Pass the Mountains is auto-computed (read-only checkbox)
    if not BotSettings.RestoreMountains and not BotSettings.RestorePlanes and not BotSettings.RestorePools:
        BotSettings.PassTheMountains = False
    else:
        BotSettings.PassTheMountains = True
    PyImGui.begin_disabled(True)
    PyImGui.checkbox("Pass the Mountains (auto)", BotSettings.PassTheMountains)
    PyImGui.end_disabled()

    # Mountains branch
    BotSettings.RestoreMountains = PyImGui.checkbox("Restore Mountains", BotSettings.RestoreMountains)
    disable_mountains = not BotSettings.RestoreMountains
    if disable_mountains:
        BotSettings.DeamonAssassin = False
    PyImGui.begin_disabled(disable_mountains)
    BotSettings.DeamonAssassin = PyImGui.checkbox("Daemon Assassin", BotSettings.DeamonAssassin)
    PyImGui.end_disabled()

    # Planes branch
    BotSettings.RestorePlanes = PyImGui.checkbox("Restore Planes", BotSettings.RestorePlanes)
    disable_planes = not BotSettings.RestorePlanes
    if disable_planes:
        BotSettings.TheFourHorsemen = False
        BotSettings.RestorePools    = False
        BotSettings.TerrorwebQueen  = False
    PyImGui.begin_disabled(disable_planes)
    BotSettings.TheFourHorsemen = PyImGui.checkbox("The Four Horsemen", BotSettings.TheFourHorsemen)
    BotSettings.RestorePools    = PyImGui.checkbox("Restore Pools",     BotSettings.RestorePools)
    PyImGui.end_disabled()

    # Pools branch
    disable_pools = not BotSettings.RestorePools
    if disable_pools:
        BotSettings.TerrorwebQueen = False
    PyImGui.begin_disabled(disable_pools)
    BotSettings.TerrorwebQueen = PyImGui.checkbox("Terrorweb Queen", BotSettings.TerrorwebQueen)
    PyImGui.end_disabled()

    # Pit area (not working yet)
    BotSettings.RestorePit        = PyImGui.checkbox("Restore Pit (WIP)",        BotSettings.RestorePit)
    BotSettings.ImprisonedSpirits = PyImGui.checkbox("Imprisoned Spirits (WIP)", BotSettings.ImprisonedSpirits)

    PyImGui.separator()
    BotSettings.Repeat  = PyImGui.checkbox("Resign and Repeat after run", BotSettings.Repeat)
    BotSettings.UseCons = PyImGui.checkbox("Use Consets",                 BotSettings.UseCons)

# endregion

# region â”€â”€ Wipe Handling â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

bot.SetMainRoutine(bot_routine)


def OnPartyWipe(bot: "Botting") -> None:
    """Event callback fired by the framework when a party wipe is detected."""
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_Underworld", lambda: _on_party_wipe(bot))


def _on_party_wipe(bot: "Botting"):
    """Coroutine: wait for resurrection or outpost return, then restart the run."""
    ConsoleLog(BOT_NAME, "[WIPE] Party wipe detected!", Py4GW.Console.MessageType.Warning)

    while Agent.IsDead(Player.GetAgentID()):
        yield from Routines.Yield.wait(1000)

        if not Routines.Checks.Map.MapValid():
            # Map changed - we are back in the outpost
            ConsoleLog(BOT_NAME, "[WIPE] Returned to outpost after wipe - restarting run.", Py4GW.Console.MessageType.Warning)
            yield from Routines.Yield.wait(3000)
            _restart_main_loop(bot, "Returned to outpost after wipe")
            return

    ConsoleLog(BOT_NAME, "[WIPE] Player resurrected in instance, resuming.", Py4GW.Console.MessageType.Info)
    _restart_main_loop(bot, "Player resurrected in instance")

# endregion

# region â”€â”€ Main Loop â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def main() -> None:
    if bot.config.fsm_running:
        _sync_custom_behavior_runtime()

        # Watchdog: the OnPartyWipe callback sometimes misses wipes.
        # If we entered the dungeon (map 72) and are now back in the outpost
        # (map 138 = Chantry of Secrets), force a restart.
        if _entered_dungeon and Map.GetMapID() == 138:
            ConsoleLog(BOT_NAME, "[WIPE] Watchdog: back in outpost (map 138) without wipe callback - restarting.", Py4GW.Console.MessageType.Warning)
            _restart_main_loop(bot, "Watchdog: returned to map 138")

    bot.Update()
    bot.UI.draw_window()


if __name__ == "__main__":
    main()

# endregion
