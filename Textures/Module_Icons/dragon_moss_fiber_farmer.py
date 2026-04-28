from __future__ import annotations

from Py4GWCoreLib import (
    ActionQueueManager,
    Agent,
    AgentArray,
    Botting,
    BuildMgr,
    ConsoleLog,
    GLOBAL_CACHE,
    Inventory,
    Item,
    Map,
    Party,
    Player,
    Profession,
    Py4GW,
    Routines,
    Utils,
)
from Py4GWCoreLib.enums import ModelID, Range

BOT_NAME = "Dragon Moss Fiber Farmer"

ANJEKAS_SHRINE = 349
DRAZACH_THICKET = 195
MAATU_KEEP = 283

SKILL_TEMPLATE = "OgcTcX883Rghc0ZHQWZoT48cAA"

RETURN_SLOT = 1
SERPENTS_QUICKNESS_SLOT = 2
SHADOW_FORM_SLOT = 3
SHROUD_OF_DISTRESS_SLOT = 4
STORM_CHASER_SLOT = 5
SHADOW_OF_HASTE_SLOT = 6
WHIRLING_DEFENSE_SLOT = 7
WINNOWING_SLOT = 8

RETURN_SKILL_ID = 770
SERPENTS_QUICKNESS_SKILL_ID = 456
SHADOW_FORM_SKILL_ID = 826
SHROUD_OF_DISTRESS_SKILL_ID = 1031
STORM_CHASER_SKILL_ID = 1474
SHADOW_OF_HASTE_SKILL_ID = 929
WHIRLING_DEFENSE_SKILL_ID = 450
WINNOWING_SKILL_ID = 463
DRAGON_MOSS_MODEL_ID = 3722

RETURN_TARGET_COORD = (-8361.0, 18604.0)
POST_RETURN_COORD = (-7924.0, 18281.0)
STORM_CHASER_COORD = (-6900, 17396)
POST_RETURN_DEFENSE_TRIGGER_COORD = (-6785.0, 17299.0)
SHADOW_OF_HASTE_ANCHOR = (-6229, 17191)
WINNOWING_COORD = (-6604.0, 18585.0)
OUTPOST_EXIT_COORD = (-11209.0, -23100.0)

BALLING_PATH = [
    STORM_CHASER_COORD,
    (-6153.0, 16621.0),
    (-5117, 15469),
    SHADOW_OF_HASTE_ANCHOR,
]

MAATU_XUNLAI_COORD = (-11545.0, 13089.0)
MAATU_MERCHANT_COORD = (-12851.0, 13654.0)

MIN_FREE_SLOTS = 5
MAX_CHARACTER_GOLD = 90000
MERCHANT_GOLD_TARGET = 1000

KILL_TIMEOUT_MS = 20000
LOOT_SETTLE_MS = 9000
SHADOW_OF_HASTE_TIMEOUT_MS = 12000
MAP_LOAD_TIMEOUT_MS = 20000
MOVEMENT_TIMEOUT_MS = 15000
DEATH_RECOVERY_SETTLE_MS = 10000
RETURN_TO_OUTPOST_TIMEOUT_MS = 5000
MOVE_TOLERANCE = 125
LOOT_RANGE = 2000.0
RETURN_TARGET_SEARCH_RADIUS = 1200.0
RETURN_CAST_RANGE = Range.Spellcast.value
RETURN_CAST_BUFFER = 75.0
DEFENSE_TRIGGER_TOLERANCE = 175
KILL_CONFIRM_RANGE = Range.Nearby.value
KILL_CLEAR_POLLS_REQUIRED = 3
LOOT_COMPLETION_TIMEOUT_MS = 8000
LOOT_CLEAR_POLLS_REQUIRED = 2

DYE_MODEL_ID = 146
SPECIAL_LOOT_MODEL_IDS = {
    22751,
    ModelID.Golden_Egg.value,
    ModelID.Chocolate_Bunny.value,
}
VALUABLE_GOLD_MODEL_IDS = {940, 945, 951, 954}
MATERIAL_MODEL_IDS = {819, 934, 956}
VALUABLE_DYE_COLORS = {10, 12}


class FarmRuntime:
    def __init__(self) -> None:
        self.completed_runs: int = 0
        self.failed_runs: int = 0
        self.last_run_succeeded: bool = False
        self.failed_loot_agent_ids: list[int] = []
        self.recovery_coroutine = None


class DragonMossRangerAssassin(BuildMgr):
    def __init__(self) -> None:
        super().__init__(
            name="Dragon Moss Ranger Assassin",
            required_primary=Profession.Ranger,
            required_secondary=Profession.Assassin,
            template_code=SKILL_TEMPLATE,
            required_skills=[
                RETURN_SKILL_ID,
                SERPENTS_QUICKNESS_SKILL_ID,
                SHADOW_FORM_SKILL_ID,
                SHROUD_OF_DISTRESS_SKILL_ID,
                STORM_CHASER_SKILL_ID,
                SHADOW_OF_HASTE_SKILL_ID,
                WHIRLING_DEFENSE_SKILL_ID,
                WINNOWING_SKILL_ID,
            ],
        )
        self.upkeep_enabled = False
        self.SetSkillCastingFn(self._maintain_defenses)

    def EnableUpkeep(self, enabled: bool) -> None:
        self.upkeep_enabled = enabled

    def _maintain_defenses(self):
        player_id = Player.GetAgentID()
        if (
            not self.upkeep_enabled
            or not Routines.Checks.Map.MapValid()
            or not Map.IsExplorable()
            or not player_id
            or Agent.IsDead(player_id)
        ):
            yield from Routines.Yield.wait(250)
            return

        if not Routines.Checks.Skills.CanCast():
            yield from Routines.Yield.wait(100)
            return

        has_shadow_form = GLOBAL_CACHE.Effects.HasEffect(player_id, SHADOW_FORM_SKILL_ID)
        shadow_form_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_id, SHADOW_FORM_SKILL_ID)
        if (not has_shadow_form or shadow_form_remaining <= 3500) and Routines.Checks.Skills.IsSkillSlotReady(SHADOW_FORM_SLOT):
            if (
                yield from Routines.Yield.Skills.CastSkillSlot(
                    SHADOW_FORM_SLOT,
                    aftercast_delay=1750,
                    log=False,
                )
            ):
                return

        if not GLOBAL_CACHE.Effects.HasEffect(player_id, SHROUD_OF_DISTRESS_SKILL_ID):
            if (
                yield from Routines.Yield.Skills.CastSkillSlot(
                    SHROUD_OF_DISTRESS_SLOT,
                    aftercast_delay=1750,
                    log=False,
                )
            ):
                return

        yield from Routines.Yield.wait(150)


runtime = FarmRuntime()
build = DragonMossRangerAssassin()
bot = Botting(
    BOT_NAME,
    custom_build=build,
    config_movement_timeout=MOVEMENT_TIMEOUT_MS,
    config_movement_tolerance=MOVE_TOLERANCE,
    upkeep_auto_combat_active=True,
    upkeep_auto_inventory_management_active=False,
    upkeep_auto_loot_active=False,
    upkeep_identify_kits_active=True,
    upkeep_identify_kits_restock=1,
    upkeep_salvage_kits_active=True,
    upkeep_salvage_kits_restock=1,
)


def initialize_bot(bot_instance: Botting) -> None:
    bot_instance.Events.OnDeathCallback(lambda: on_death(bot_instance))
    bot_instance.Events.OnPartyWipeCallback(lambda: on_party_wipe(bot_instance))
    bot_instance.Events.OnPartyDefeatedCallback(lambda: on_party_defeated(bot_instance))
    bot_instance.States.AddHeader("Initialize Bot")
    bot_instance.Properties.Disable("auto_inventory_management")
    bot_instance.Properties.Disable("auto_loot")
    bot_instance.Properties.Disable("hero_ai")
    bot_instance.Properties.Enable("auto_combat")
    bot_instance.Properties.Disable("pause_on_danger")
    bot_instance.Properties.Enable("halt_on_death")
    bot_instance.Properties.Enable("identify_kits")
    bot_instance.Properties.Enable("salvage_kits")


def create_bot_routine(bot_instance: Botting) -> None:
    initialize_bot(bot_instance)

    bot_instance.States.AddHeader("Main Loop")
    bot_instance.States.AddCustomState(lambda: ensure_anjekas_shrine(bot_instance), "Ensure Anjeka")
    bot_instance.States.AddCustomState(check_inventory_gate, "Check Inventory")

    bot_instance.States.AddHeader("Inventory Management")
    bot_instance.Map.Travel(target_map_id=MAATU_KEEP)
    bot_instance.Move.XYAndInteractNPC(*MAATU_XUNLAI_COORD)
    bot_instance.Wait.ForTime(500)
    bot_instance.Items.AutoIDAndSalvageAndDepositItems()
    bot_instance.States.AddCustomState(ensure_merchant_gold, "Ensure Merchant Gold")
    bot_instance.Move.XYAndInteractNPC(*MAATU_MERCHANT_COORD)
    bot_instance.Wait.ForTime(500)
    bot_instance.Merchant.SellMaterialsToMerchant()
    bot_instance.Merchant.Restock.IdentifyKits()
    bot_instance.Merchant.Restock.SalvageKits()
    bot_instance.Items.AutoIDAndSalvageAndDepositItems()
    bot_instance.Merchant.SellMaterialsToMerchant()
    bot_instance.States.AddCustomState(lambda: return_from_inventory(bot_instance), "Return From Inventory")

    bot_instance.States.AddHeader("Prepare Run")
    bot_instance.States.AddCustomState(deposit_excess_gold, "Deposit Excess Gold")
    bot_instance.States.AddCustomState(lambda: load_skillbar(bot_instance), "Load Skillbar")
    bot_instance.Party.SetHardMode(True)
    bot_instance.Move.XYAndExitMap(*OUTPOST_EXIT_COORD, target_map_id=DRAZACH_THICKET)
    bot_instance.States.AddCustomState(lambda: run_dragon_moss_farm(bot_instance), "Farm Dragon Moss")
    bot_instance.States.AddCustomState(reset_run, "Reset Run")
    bot_instance.States.JumpToStepName("Ensure Anjeka")


def on_death(bot_instance: Botting) -> None:
    _begin_failure_recovery(bot_instance, "death")


def on_party_wipe(bot_instance: Botting) -> None:
    _begin_failure_recovery(bot_instance, "party wipe")


def on_party_defeated(bot_instance: Botting) -> None:
    _begin_failure_recovery(bot_instance, "party defeat")


def _is_normal_reset_in_progress(bot_instance: Botting) -> bool:
    current_state = bot_instance.config.FSM.current_state
    return bool(current_state and current_state.name == "Reset Run")


def _begin_failure_recovery(bot_instance: Botting, reason: str) -> None:
    if _is_normal_reset_in_progress(bot_instance):
        ConsoleLog(
            BOT_NAME,
            f"Ignoring {reason} because the normal reset flow is already in progress.",
            Py4GW.Console.MessageType.Info,
        )
        return
    if runtime.recovery_coroutine is not None:
        ConsoleLog(
            BOT_NAME,
            f"{reason.capitalize()} detected while recovery is already in progress; ignoring duplicate trigger.",
            Py4GW.Console.MessageType.Info,
        )
        return

    runtime.last_run_succeeded = False
    runtime.failed_loot_agent_ids.clear()
    runtime.failed_runs += 1
    ConsoleLog(
        BOT_NAME,
        f"Run failed ({runtime.failed_runs} total failures). Recovering from {reason}.",
        Py4GW.Console.MessageType.Warning,
    )
    ActionQueueManager().ResetAllQueues()
    build.EnableUpkeep(False)
    fsm = bot_instance.config.FSM
    if not bot_instance.config.fsm_running:
        bot_instance.config.fsm_running = True
    if not fsm.current_state or fsm.is_finished():
        fsm.jump_to_state_by_name("Ensure Anjeka")
    fsm.pause()
    ConsoleLog(BOT_NAME, f"Starting recovery sequence for {reason}.", Py4GW.Console.MessageType.Info)
    runtime.recovery_coroutine = _recover_from_failure(bot_instance, reason)


def _recover_from_failure(bot_instance: Botting, reason: str):
    ConsoleLog(BOT_NAME, f"Recovery coroutine started for {reason}.", Py4GW.Console.MessageType.Info)
    yield from Routines.Yield.wait(DEATH_RECOVERY_SETTLE_MS)
    ConsoleLog(BOT_NAME, f"Recovery settle wait finished for {reason}.", Py4GW.Console.MessageType.Info)
    yield from recover_to_anjekas(resign_if_alive=False)
    ConsoleLog(BOT_NAME, f"Recovery path returned to outpost for {reason}; jumping to Ensure Anjeka.", Py4GW.Console.MessageType.Info)
    bot_instance.config.FSM.jump_to_state_by_name("Ensure Anjeka")
    ConsoleLog(BOT_NAME, f"Resuming FSM after recovery for {reason}.", Py4GW.Console.MessageType.Info)
    bot_instance.config.FSM.resume()
    ConsoleLog(BOT_NAME, f"FSM resumed after recovery for {reason}.", Py4GW.Console.MessageType.Info)
    yield


def advance_failure_recovery(bot_instance: Botting) -> None:
    if runtime.recovery_coroutine is None:
        return

    try:
        next(runtime.recovery_coroutine)
    except StopIteration:
        ConsoleLog(BOT_NAME, "Recovery sequence finished.", Py4GW.Console.MessageType.Info)
        runtime.recovery_coroutine = None
    except Exception as exc:
        ConsoleLog(BOT_NAME, f"Recovery sequence failed: {exc}", Py4GW.Console.MessageType.Error)
        runtime.recovery_coroutine = None
        bot_instance.config.FSM.resume()


def run_failure_watchdog(bot_instance: Botting) -> None:
    if runtime.recovery_coroutine is not None or _is_normal_reset_in_progress(bot_instance):
        return

    player_id = Player.GetAgentID()
    if player_id and Agent.IsDead(player_id):
        _begin_failure_recovery(bot_instance, "death watchdog")
        return

    if not Routines.Checks.Map.MapValid():
        return

    if GLOBAL_CACHE.Party.IsPartyDefeated():
        _begin_failure_recovery(bot_instance, "party defeat watchdog")
        return

    if Routines.Checks.Party.IsPartyWiped():
        _begin_failure_recovery(bot_instance, "party wipe watchdog")


def recover_to_anjekas(resign_if_alive: bool):
    ActionQueueManager().ResetAllQueues()
    build.EnableUpkeep(False)
    ConsoleLog(
        BOT_NAME,
        f"Entering recover_to_anjekas(resign_if_alive={resign_if_alive}) on map {Map.GetMapID()}.",
        Py4GW.Console.MessageType.Info,
    )

    player_id = Player.GetAgentID()
    arrived_in_anjeka = Map.IsMapIDMatch(Map.GetMapID(), ANJEKAS_SHRINE)
    if Map.IsExplorable():
        if player_id and Agent.IsDead(player_id):
            ConsoleLog(BOT_NAME, "Player is dead during recovery; waiting briefly before returning to outpost.", Py4GW.Console.MessageType.Info)
            yield from Routines.Yield.wait(4000)
        elif resign_if_alive:
            yield from Routines.Yield.Player.Resign(log=False)
            if not (
                yield from wait_for_condition(
                    lambda: (
                        Map.IsMapLoading()
                        or GLOBAL_CACHE.Party.IsPartyDefeated()
                        or (Player.GetAgentID() and Agent.IsDead(Player.GetAgentID()))
                    ),
                    timeout_ms=5000,
                    step_ms=250,
                )
            ):
                ConsoleLog(
                    BOT_NAME,
                    "Normal reset resign did not settle quickly; continuing with outpost return fallback.",
                    Py4GW.Console.MessageType.Warning,
                )
            yield from Routines.Yield.wait(500)

        Party.ReturnToOutpost()
        ConsoleLog(BOT_NAME, "Issued direct ReturnToOutpost call.", Py4GW.Console.MessageType.Info)
        ConsoleLog(BOT_NAME, "Waiting 750 ms after ReturnToOutpost.", Py4GW.Console.MessageType.Info)
        yield from Routines.Yield.wait(750)
        ConsoleLog(
            BOT_NAME,
            f"Finished post-ReturnToOutpost wait. loading={Map.IsMapLoading()} explorable={Map.IsExplorable()} outpost={Map.IsOutpost()} map={Map.GetMapID()}",
            Py4GW.Console.MessageType.Info,
        )
        transition_started = (
            Map.IsMapLoading()
            or Map.IsOutpost()
            or Map.IsMapIDMatch(Map.GetMapID(), ANJEKAS_SHRINE)
        )
        if transition_started:
            ConsoleLog(
                BOT_NAME,
                f"Waiting briefly for Anjeka map load after ReturnToOutpost (timeout={RETURN_TO_OUTPOST_TIMEOUT_MS} ms).",
                Py4GW.Console.MessageType.Info,
            )
            arrived_in_anjeka = yield from Routines.Yield.Map.WaitforMapLoad(
                ANJEKAS_SHRINE,
                log=True,
                timeout=RETURN_TO_OUTPOST_TIMEOUT_MS,
            )
            ConsoleLog(
                BOT_NAME,
                f"WaitforMapLoad after ReturnToOutpost completed with success={arrived_in_anjeka}.",
                Py4GW.Console.MessageType.Info,
            )
        else:
            arrived_in_anjeka = False
            ConsoleLog(
                BOT_NAME,
                "ReturnToOutpost did not start a map transition; using TravelToOutpost fallback.",
                Py4GW.Console.MessageType.Warning,
            )

    if not Map.IsMapIDMatch(Map.GetMapID(), ANJEKAS_SHRINE):
        ConsoleLog(
            BOT_NAME,
            "Falling back to TravelToOutpost for Anjeka reset recovery.",
            Py4GW.Console.MessageType.Warning,
        )
        yield from Routines.Yield.Map.TravelToOutpost(ANJEKAS_SHRINE, log=True, timeout=MAP_LOAD_TIMEOUT_MS)

    arrived_in_anjeka = yield from Routines.Yield.Map.WaitforMapLoad(
        ANJEKAS_SHRINE,
        log=True,
        timeout=MAP_LOAD_TIMEOUT_MS,
    )
    ConsoleLog(
        BOT_NAME,
        f"Final WaitforMapLoad for Anjeka completed with success={arrived_in_anjeka}.",
        Py4GW.Console.MessageType.Info,
    )
    if not arrived_in_anjeka:
        ConsoleLog(
            BOT_NAME,
            "Failed to confirm Anjeka load during reset recovery.",
            Py4GW.Console.MessageType.Warning,
        )


def ensure_anjekas_shrine(bot_instance: Botting):
    del bot_instance
    build.EnableUpkeep(False)
    yield from recover_to_anjekas(resign_if_alive=True)


def check_inventory_gate():
    if not needs_inventory_management():
        bot.config.FSM.jump_to_state_by_name("Deposit Excess Gold")
    yield


def needs_inventory_management() -> bool:
    return (
        Inventory.GetFreeSlotCount() < MIN_FREE_SLOTS
        or Inventory.GetFirstIDKit() == 0
        or Inventory.GetFirstSalvageKit() == 0
    )


def ensure_merchant_gold():
    if Inventory.GetGoldOnCharacter() < MERCHANT_GOLD_TARGET:
        yield from Routines.Yield.Items.WithdrawGold(
            MERCHANT_GOLD_TARGET,
            deposit_all=False,
            log=False,
        )
    yield


def return_from_inventory(bot_instance: Botting):
    del bot_instance
    yield from Routines.Yield.Map.TravelToOutpost(ANJEKAS_SHRINE, log=True, timeout=MAP_LOAD_TIMEOUT_MS)


def deposit_excess_gold():
    gold_on_character = Inventory.GetGoldOnCharacter()
    if gold_on_character > MAX_CHARACTER_GOLD:
        Inventory.DepositGold(gold_on_character - MAX_CHARACTER_GOLD)
        yield from Routines.Yield.wait(350)
    yield


def load_skillbar(bot_instance: Botting):
    primary, secondary = Agent.GetProfessionNames(Player.GetAgentID())
    if primary != "Ranger" or secondary != "Assassin":
        ConsoleLog(
            BOT_NAME,
            f"Unsupported profession combo: {primary}/{secondary}. Expected Ranger/Assassin.",
            Py4GW.Console.MessageType.Error,
        )
        bot_instance.Stop()
        yield
        return

    build.EnableUpkeep(False)
    yield from build.LoadSkillBar()


def run_dragon_moss_farm(bot_instance: Botting):
    del bot_instance
    runtime.last_run_succeeded = False
    runtime.failed_loot_agent_ids.clear()

    try:
        if not Map.IsMapIDMatch(Map.GetMapID(), DRAZACH_THICKET):
            ConsoleLog(
                BOT_NAME,
                f"Run started on unexpected map {Map.GetMapID()} instead of {DRAZACH_THICKET}.",
                Py4GW.Console.MessageType.Error,
            )
            return

        yield from Routines.Yield.wait(500)
        ConsoleLog(BOT_NAME, "Entered Drazach, resolving Return anchor.", Py4GW.Console.MessageType.Info)
        return_target = get_return_target()
        if return_target == 0:
            ConsoleLog(
                BOT_NAME,
                "Unable to resolve the Return target near the gate; aborting run before reset.",
                Py4GW.Console.MessageType.Error,
            )
            return
        ConsoleLog(
            BOT_NAME,
            f"Using Return target {return_target} at {Agent.GetXY(return_target)} [{Agent.GetAllegiance(return_target)[1]}].",
            Py4GW.Console.MessageType.Info,
        )
        if not (
            yield from ensure_target_in_skill_range(
                return_target,
                "Return",
                max_distance=RETURN_CAST_RANGE - RETURN_CAST_BUFFER,
                timeout_ms=6000,
            )
        ):
            ConsoleLog(BOT_NAME, "Failed to move into Return cast range. Aborting run.", Py4GW.Console.MessageType.Warning)
            return

        if not (
            yield from cast_targeted_skill_when_ready(
                RETURN_SLOT,
                return_target,
                "Return",
                ready_timeout_ms=4000,
                aftercast_delay=2500,
            )
        ):
            ConsoleLog(BOT_NAME, "Return failed to cast on the gate anchor. Aborting run.", Py4GW.Console.MessageType.Warning)
            return
        ConsoleLog(BOT_NAME, f"Return completed. Player now at {Player.GetXY()}.", Py4GW.Console.MessageType.Info)

        ConsoleLog(
            BOT_NAME,
            f"Post-Return move: {Player.GetXY()} -> {POST_RETURN_COORD}.",
            Py4GW.Console.MessageType.Info,
        )
        if not (yield from follow_path([POST_RETURN_COORD], timeout=MOVEMENT_TIMEOUT_MS, tolerance=MOVE_TOLERANCE)):
            ConsoleLog(
                BOT_NAME,
                f"Failed moving to post-Return point {POST_RETURN_COORD} from {Player.GetXY()}.",
                Py4GW.Console.MessageType.Warning,
            )
            return
        ConsoleLog(BOT_NAME, f"Reached post-Return point at {Player.GetXY()}.", Py4GW.Console.MessageType.Info)
        ConsoleLog(BOT_NAME, "Waiting for a stable post-Return cast window.", Py4GW.Console.MessageType.Info)
        if not (
            yield from wait_for_condition(
                lambda: (
                    not Agent.IsDead(Player.GetAgentID())
                    and not Map.IsMapLoading()
                    and not Agent.IsCasting(Player.GetAgentID())
                    and Routines.Checks.Skills.CanCast()
                ),
                timeout_ms=4000,
                step_ms=100,
            )
        ):
            ConsoleLog(
                BOT_NAME,
                "Player never reached a stable post-Return cast state. Aborting run.",
                Py4GW.Console.MessageType.Warning,
            )
            return
        if not (yield from cast_post_return_setup()):
            return

        if not (yield from follow_path([STORM_CHASER_COORD], timeout=MOVEMENT_TIMEOUT_MS, tolerance=MOVE_TOLERANCE)):
            return

        if not (
            yield from follow_path(
                [POST_RETURN_DEFENSE_TRIGGER_COORD],
                timeout=MOVEMENT_TIMEOUT_MS,
                tolerance=DEFENSE_TRIGGER_TOLERANCE,
            )
        ):
            ConsoleLog(
                BOT_NAME,
                f"Failed reaching defense trigger point {POST_RETURN_DEFENSE_TRIGGER_COORD} from {Player.GetXY()}.",
                Py4GW.Console.MessageType.Warning,
            )
            return
        ConsoleLog(
            BOT_NAME,
            f"Reached defense trigger point near {POST_RETURN_DEFENSE_TRIGGER_COORD} at {Player.GetXY()}.",
            Py4GW.Console.MessageType.Info,
        )

        yield from cast_skill_slot(SHADOW_FORM_SLOT, aftercast_delay=1750)
        yield from cast_skill_slot(SHROUD_OF_DISTRESS_SLOT, aftercast_delay=1750)
        yield from cast_skill_slot(STORM_CHASER_SLOT, aftercast_delay=250)
        build.EnableUpkeep(True)

        if not (yield from follow_path(BALLING_PATH[1:], timeout=MOVEMENT_TIMEOUT_MS, tolerance=MOVE_TOLERANCE)):
            return

        yield from cast_skill_slot(SHADOW_OF_HASTE_SLOT, aftercast_delay=500)

        if not (yield from follow_path([WINNOWING_COORD], timeout=MOVEMENT_TIMEOUT_MS, tolerance=MOVE_TOLERANCE)):
            return

        yield from Routines.Yield.wait(1500)
        whirling_cast = yield from cast_skill_slot_when_ready(
            WHIRLING_DEFENSE_SLOT,
            "Whirling Defense",
            ready_timeout_ms=2500,
            aftercast_delay=500,
        )
        if not whirling_cast:
            ConsoleLog(
                BOT_NAME,
                "Whirling Defense was not cast before the kill window; continuing with caution.",
                Py4GW.Console.MessageType.Warning,
            )
        kill_window_completed = yield from wait_for_kill_window()
        if not kill_window_completed:
            ConsoleLog(BOT_NAME, "Kill window did not finish cleanly. Marking run as failed.", Py4GW.Console.MessageType.Warning)
            return

        yield from Routines.Yield.wait(LOOT_SETTLE_MS)
        loot_completed = yield from loot_run_drops()
        if not loot_completed:
            ConsoleLog(BOT_NAME, "Loot phase ended with pending drops. Marking run as failed.", Py4GW.Console.MessageType.Warning)
            return

        runtime.last_run_succeeded = not Agent.IsDead(Player.GetAgentID())
    finally:
        build.EnableUpkeep(False)


def reset_run():
    if runtime.last_run_succeeded:
        runtime.completed_runs += 1
        ConsoleLog(BOT_NAME, f"Run {runtime.completed_runs} completed.", Py4GW.Console.MessageType.Success)
    else:
        runtime.failed_runs += 1
        ConsoleLog(BOT_NAME, f"Run failed ({runtime.failed_runs} total failures).", Py4GW.Console.MessageType.Warning)

    build.EnableUpkeep(False)

    if Map.IsExplorable() or not Map.IsMapIDMatch(Map.GetMapID(), ANJEKAS_SHRINE):
        yield from recover_to_anjekas(resign_if_alive=True)

    yield


def get_return_target() -> int:
    def nearest_to_anchor(agent_ids: list[int]) -> int:
        if not agent_ids:
            return 0
        agent_ids.sort(key=lambda agent_id: Utils.Distance(Agent.GetXY(agent_id), RETURN_TARGET_COORD))
        return agent_ids[0]

    ally_array = Routines.Agents.GetFilteredAllyArray(
        RETURN_TARGET_COORD[0],
        RETURN_TARGET_COORD[1],
        RETURN_TARGET_SEARCH_RADIUS,
        other_ally=True,
    )
    target = nearest_to_anchor(ally_array)
    if target:
        return target

    npc_target = Routines.Agents.GetNearestNPCXY(
        RETURN_TARGET_COORD[0],
        RETURN_TARGET_COORD[1],
        RETURN_TARGET_SEARCH_RADIUS,
    )
    if npc_target:
        return npc_target

    agent_array = AgentArray.GetAgentArray()
    fallback_targets = [
        agent_id
        for agent_id in agent_array
        if agent_id != Player.GetAgentID()
        and Agent.IsLiving(agent_id)
        and Agent.IsAlive(agent_id)
        and Utils.Distance(Agent.GetXY(agent_id), RETURN_TARGET_COORD) <= RETURN_TARGET_SEARCH_RADIUS
        and Agent.GetAllegiance(agent_id)[1] in {"Ally", "Neutral", "NPC/Minipet", "Spirit/Pet"}
    ]
    return nearest_to_anchor(fallback_targets)


def cast_targeted_skill_when_ready(
    slot: int,
    target_agent_id: int,
    skill_name: str,
    ready_timeout_ms: int = 2000,
    aftercast_delay: int = 750,
):
    start_time = Utils.GetBaseTimestamp()
    while Utils.GetBaseTimestamp() - start_time <= ready_timeout_ms:
        if Agent.IsDead(Player.GetAgentID()):
            return False
        if target_agent_id == 0 or not Agent.IsValid(target_agent_id) or not Agent.IsAlive(target_agent_id):
            ConsoleLog(BOT_NAME, f"{skill_name} target {target_agent_id} is no longer valid.", Py4GW.Console.MessageType.Warning)
            return False

        if Routines.Checks.Skills.IsSkillSlotReady(slot) and Routines.Checks.Skills.CanCast():
            if (
                yield from build.CastSkillSlot(
                    slot,
                    log=False,
                    aftercast_delay=aftercast_delay,
                    target_agent_id=target_agent_id,
                )
            ):
                ConsoleLog(BOT_NAME, f"Casted {skill_name} on target {target_agent_id}.", Py4GW.Console.MessageType.Info)
                return True
        yield from Routines.Yield.wait(100)

    ConsoleLog(BOT_NAME, f"{skill_name} was not ready to cast on target {target_agent_id} in time.", Py4GW.Console.MessageType.Warning)
    return False


def ensure_target_in_skill_range(
    target_agent_id: int,
    skill_name: str,
    max_distance: float,
    timeout_ms: int = 6000,
):
    if target_agent_id == 0 or not Agent.IsValid(target_agent_id) or not Agent.IsAlive(target_agent_id):
        ConsoleLog(BOT_NAME, f"{skill_name} target {target_agent_id} is invalid before range check.", Py4GW.Console.MessageType.Warning)
        return False

    target_xy = Agent.GetXY(target_agent_id)
    current_distance = Utils.Distance(Player.GetXY(), target_xy)
    ConsoleLog(
        BOT_NAME,
        f"{skill_name} target {target_agent_id} is {current_distance:.0f} units away; required <= {max_distance:.0f}.",
        Py4GW.Console.MessageType.Info,
    )
    if current_distance <= max_distance:
        return True

    ConsoleLog(
        BOT_NAME,
        f"Moving into {skill_name} range toward target {target_agent_id} at {target_xy}.",
        Py4GW.Console.MessageType.Info,
    )
    yield from follow_path(
        [target_xy],
        timeout=timeout_ms,
        tolerance=max_distance,
    )

    updated_distance = Utils.Distance(Player.GetXY(), Agent.GetXY(target_agent_id))
    ConsoleLog(
        BOT_NAME,
        f"{skill_name} range check after move: {updated_distance:.0f} units from target {target_agent_id}.",
        Py4GW.Console.MessageType.Info,
    )
    return updated_distance <= max_distance


def cast_skill_slot(slot: int, aftercast_delay: int = 750):
    if slot == WINNOWING_SLOT:
        # Winnowing is a spirit skill, so use BuildMgr's cast path to wait for the
        # full spirit cast/spawn handling before the next action starts.
        return (
            yield from build.CastSkillSlot(
                slot,
                log=False,
                aftercast_delay=aftercast_delay,
            )
        )

    return (
        yield from Routines.Yield.Skills.CastSkillSlot(
            slot,
            aftercast_delay=aftercast_delay,
            log=False,
        )
    )


def cast_skill_slot_when_ready(
    slot: int,
    skill_name: str,
    ready_timeout_ms: int = 2000,
    aftercast_delay: int = 750,
):
    start_time = Utils.GetBaseTimestamp()
    while Utils.GetBaseTimestamp() - start_time <= ready_timeout_ms:
        if Agent.IsDead(Player.GetAgentID()):
            return False
        if Routines.Checks.Skills.IsSkillSlotReady(slot) and Routines.Checks.Skills.CanCast():
            if (yield from cast_skill_slot(slot, aftercast_delay=aftercast_delay)):
                ConsoleLog(BOT_NAME, f"Casted {skill_name}.", Py4GW.Console.MessageType.Info)
                return True
        yield from Routines.Yield.wait(100)

    ConsoleLog(BOT_NAME, f"{skill_name} was not ready in time.", Py4GW.Console.MessageType.Warning)
    return False


def cast_post_return_setup():
    ConsoleLog(BOT_NAME, "Post-Return setup: casting Winnowing then Serpent's Quickness.", Py4GW.Console.MessageType.Info)
    if not (
        yield from cast_skill_slot_when_ready(
            WINNOWING_SLOT,
            "Winnowing",
            ready_timeout_ms=4000,
            aftercast_delay=1250,
        )
    ):
        ConsoleLog(
            BOT_NAME,
            "Winnowing failed to cast after Return. Aborting run.",
            Py4GW.Console.MessageType.Warning,
        )
        return False

    if not (
        yield from cast_skill_slot_when_ready(
            SERPENTS_QUICKNESS_SLOT,
            "Serpent's Quickness",
            ready_timeout_ms=4000,
            aftercast_delay=300,
        )
    ):
        ConsoleLog(
            BOT_NAME,
            "Serpent's Quickness failed to cast after Winnowing. Aborting run.",
            Py4GW.Console.MessageType.Warning,
        )
        return False

    return True


def follow_path(path_points: list[tuple[float, float]], timeout: int, tolerance: float) -> bool:
    result = yield from Routines.Yield.Movement.FollowPath(
        path_points=path_points,
        custom_exit_condition=lambda: Agent.IsDead(Player.GetAgentID()) or Map.IsMapLoading(),
        timeout=timeout,
        tolerance=tolerance,
        log=False,
    )
    return bool(result)


def wait_for_condition(condition, timeout_ms: int, step_ms: int = 100) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if condition():
            return True
        yield from Routines.Yield.wait(step_ms)
        elapsed += step_ms
    return condition()


def wait_for_shadow_form_ready():
    yield from wait_for_condition(
        lambda: Routines.Checks.Skills.IsSkillSlotReady(SHADOW_FORM_SLOT) or Agent.IsDead(Player.GetAgentID()),
        timeout_ms=SHADOW_OF_HASTE_TIMEOUT_MS,
        step_ms=100,
    )


def wait_for_shadow_of_haste_return():
    player_id = Player.GetAgentID()
    yield from wait_for_condition(
        lambda: (
            Agent.IsDead(player_id)
            or not GLOBAL_CACHE.Effects.HasEffect(player_id, SHADOW_OF_HASTE_SKILL_ID)
            or Utils.Distance(Player.GetXY(), SHADOW_OF_HASTE_ANCHOR) <= 220
        ),
        timeout_ms=SHADOW_OF_HASTE_TIMEOUT_MS,
        step_ms=100,
    )

    if not Agent.IsDead(player_id) and Utils.Distance(Player.GetXY(), SHADOW_OF_HASTE_ANCHOR) > 300:
        yield from follow_path([SHADOW_OF_HASTE_ANCHOR], timeout=6000, tolerance=MOVE_TOLERANCE)


def refresh_shadow_form():
    for _ in range(2):
        if not Routines.Checks.Skills.IsSkillSlotReady(SHADOW_FORM_SLOT):
            break
        if not (yield from cast_skill_slot(SHADOW_FORM_SLOT, aftercast_delay=1750)):
            break


def wait_for_kill_window():
    start_time = Utils.GetBaseTimestamp()
    clear_polls = 0
    while True:
        if Agent.IsDead(Player.GetAgentID()):
            return False

        nearby_moss_count = get_nearby_dragon_moss_count(KILL_CONFIRM_RANGE)
        if nearby_moss_count == 0:
            clear_polls += 1
            if clear_polls >= KILL_CLEAR_POLLS_REQUIRED:
                ConsoleLog(BOT_NAME, "Kill window completed. No nearby Dragon Moss remain.", Py4GW.Console.MessageType.Success)
                return True
        else:
            clear_polls = 0

        if Utils.GetBaseTimestamp() - start_time > KILL_TIMEOUT_MS:
            ConsoleLog(
                BOT_NAME,
                f"Kill window timed out with {nearby_moss_count} Dragon Moss still nearby.",
                Py4GW.Console.MessageType.Warning,
            )
            return False
        yield from Routines.Yield.wait(500)


def get_nearby_dragon_moss_count(max_distance: float) -> int:
    px, py = Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(px, py, max_distance)
    return sum(1 for agent_id in enemy_array if Agent.GetModelID(agent_id) == DRAGON_MOSS_MODEL_ID)


def loot_run_drops():
    start_time = Utils.GetBaseTimestamp()
    seen_loot = False
    clear_polls = 0

    while True:
        if Agent.IsDead(Player.GetAgentID()):
            return False

        loot_agent_ids = get_loot_agent_ids()
        if loot_agent_ids:
            seen_loot = True
            clear_polls = 0
            ConsoleLog(BOT_NAME, f"Attempting to loot {len(loot_agent_ids)} item(s).", Py4GW.Console.MessageType.Info)
            runtime.failed_loot_agent_ids = yield from Routines.Yield.Items.LootItemsWithMaxAttempts(
                loot_agent_ids,
                log=True,
                pickup_timeout=3500,
                max_attempts=4,
                attempts_timeout_seconds=2,
            )
            yield from Routines.Yield.wait(500)
            continue

        clear_polls += 1
        if seen_loot and clear_polls >= LOOT_CLEAR_POLLS_REQUIRED:
            runtime.failed_loot_agent_ids.clear()
            ConsoleLog(BOT_NAME, "Loot phase completed. No eligible drops remain nearby.", Py4GW.Console.MessageType.Success)
            return True

        if Utils.GetBaseTimestamp() - start_time > LOOT_COMPLETION_TIMEOUT_MS:
            if seen_loot:
                remaining_loot = len(get_loot_agent_ids())
                if remaining_loot > 0:
                    ConsoleLog(
                        BOT_NAME,
                        f"Loot phase timed out with {remaining_loot} eligible item(s) still nearby.",
                        Py4GW.Console.MessageType.Warning,
                    )
                    return False
            ConsoleLog(BOT_NAME, "Loot phase completed.", Py4GW.Console.MessageType.Info)
            return True

        yield from Routines.Yield.wait(500)


def get_loot_agent_ids() -> list[int]:
    player_position = Player.GetXY()
    item_agent_ids = AgentArray.GetItemArray()
    item_agent_ids = [
        agent_id
        for agent_id in item_agent_ids
        if Agent.IsValid(agent_id)
        and Utils.Distance(player_position, Agent.GetXY(agent_id)) <= LOOT_RANGE
        and should_pick_up(agent_id)
    ]
    item_agent_ids.sort(key=lambda agent_id: Utils.Distance(player_position, Agent.GetXY(agent_id)))
    return item_agent_ids


def should_pick_up(agent_id: int) -> bool:
    item_id = Agent.GetItemAgentItemID(agent_id)
    if item_id == 0:
        return False

    model_id = Item.GetModelID(item_id)
    item_type, _ = Item.GetItemType(item_id)

    if Item.Type.IsTome(item_id):
        return True

    if item_type == 20:
        return True

    if model_id in MATERIAL_MODEL_IDS:
        return True

    if model_id in SPECIAL_LOOT_MODEL_IDS:
        return True

    if model_id == DYE_MODEL_ID and Item.GetDyeColor(item_id) in VALUABLE_DYE_COLORS:
        return True

    if model_id in VALUABLE_GOLD_MODEL_IDS and Item.Rarity.IsGold(item_id):
        return True

    return False


create_bot_routine(bot)

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color

    PyImGui.begin_tooltip()

    title_color = Color(255, 200, 100, 255)

    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Dragon Moss Fiber Farmer", title_color.to_tuple_normalized())
    ImGui.pop_font()

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    PyImGui.text("Automated Ranger / Assassin Dragon Moss fiber farm.")
    PyImGui.text("Designed for repeated HM farming with automatic reset and inventory handling.")

    PyImGui.spacing()
    PyImGui.text_colored("Requirements", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Primary / Secondary: Ranger / Assassin (R/A)")
    PyImGui.bullet_text('Quest "A New Escort"')
    PyImGui.bullet_text("Skill template: OgcTcX883Rghc0ZHQWZoT48cAA")
    PyImGui.bullet_text("Designed for Hard Mode")
    PyImGui.bullet_text("Starts from Anjeka's Shrine")
    PyImGui.bullet_text("Requires enough free inventory space")
    PyImGui.bullet_text("Requires ID kit / salvage kit support for full inventory handling")

    PyImGui.spacing()
    PyImGui.text_colored("Features", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Automatic outpost travel and run loop")
    PyImGui.bullet_text("Return anchor detection and cast range handling")
    PyImGui.bullet_text("Automated skill sequence and pathing")
    PyImGui.bullet_text("Kill window and loot phase handling")
    PyImGui.bullet_text("Inventory check before runs")
    PyImGui.bullet_text("Merchant / Xunlai recovery flow when needed")
    PyImGui.bullet_text("Auto identify / salvage / deposit support")
    PyImGui.bullet_text("Material, tome, dye, event item, and selected gold loot support")

    PyImGui.spacing()
    PyImGui.text_colored("Notes", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Built for unattended farming loops")
    PyImGui.bullet_text("Recovery / reset flow included")
    PyImGui.bullet_text("Loot filters can be extended if needed")

    PyImGui.spacing()
    PyImGui.text_colored("Credits", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by XLeek")

    PyImGui.end_tooltip()

def main():
    advance_failure_recovery(bot)
    run_failure_watchdog(bot)
    bot.Update()
    bot.UI.draw_window()


if __name__ == "__main__":
    main()