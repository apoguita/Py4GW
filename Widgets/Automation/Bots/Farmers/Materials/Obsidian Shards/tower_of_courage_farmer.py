from __future__ import annotations

import importlib
import os

from Py4GWCoreLib import ActionQueueManager
from Py4GWCoreLib import Agent
from Py4GWCoreLib import AgentArray
from Py4GWCoreLib import AutoPathing
from Py4GWCoreLib import Botting
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Item
from Py4GWCoreLib import Map
from Py4GWCoreLib import Party
from Py4GWCoreLib import Player
from Py4GWCoreLib import Profession
from Py4GWCoreLib import Py4GW
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Utils
from Py4GWCoreLib.enums import Range
from Py4GWCoreLib.enums import name_to_map_id
import PyImGui

from Sources.tower_of_courage import loot_policy

loot_policy = importlib.reload(loot_policy)

BOT_NAME = 'Tower of Courage Obsidian Shard Farmer'
MODULE_ICON = 'Textures\\Module_Icons\\Tower of Courage Obsidian Shard Farmer.png'
BOT_TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), MODULE_ICON)

TEMPLE_OF_THE_AGES = name_to_map_id['Temple of the Ages']
FISSURE_OF_WOE = name_to_map_id['The Fissure of Woe']
TEMPLE_STATUE_COORD = (-2435.05, 18678.10)
CHAMPION_OF_BALTHAZAR_NAME = 'Champion of Balthazar'
TEMPLE_ENTRY_DIALOG_IDS = (0x85, 0x86)

SKILL_TEMPLATE = 'OgcTc5+8Z6ASn5uU4ABimsBKuEA'

SHROUD_OF_DISTRESS_SLOT = 1
SHADOW_FORM_SLOT = 2
DWARVEN_STABILITY_SLOT = 3
WHIRLING_DEFENSE_SLOT = 4
HEART_OF_SHADOW_SLOT = 5
I_AM_UNSTOPPABLE_SLOT = 6
DARK_ESCAPE_SLOT = 7
MENTAL_BLOCK_SLOT = 8

SHADOW_FORM_SKILL_ID = 826
SHROUD_OF_DISTRESS_SKILL_ID = 1031
I_AM_UNSTOPPABLE_SKILL_ID = 2356
DARK_ESCAPE_SKILL_ID = 1037
DWARVEN_STABILITY_SKILL_ID = 2423
WHIRLING_DEFENSE_SKILL_ID = 450
HEART_OF_SHADOW_SKILL_ID = 1032
MENTAL_BLOCK_SKILL_ID = 2417

ABYSSAL_MODEL_IDS = {2810, 2861, 5194}

INITIAL_PULL_PATH = [
    (-21131.0, -2390.0),
    (-16494.0, -3113.0),
]
ABYSSAL_BALL_PATH = [
    (-14453.0, -3536.0),
]
ABYSSAL_KILL_PATH = [
    (-13684.0, -2077.0),
    (-14113.0, -418.0),
]
RANGER_BALL_PATH = [
    (-13684.0, -2077.0),
    (-15826.0, -3046.0),
    (-16002.0, -3031.0),
]
RANGER_KILL_APPROACH_PATH = [
    (-16004.0, -3202.0),
    (-15272.0, -3004.0),
]
RANGER_KILL_PATH = [
    (-14453.0, -3536.0),
    (-14209.0, -2935.0),
    (-14535.0, -2615.0),
]
RANGER_LOOT_COORD = (-14506.0, -2633.0)

MOVE_TOLERANCE = 125.0
MOVEMENT_TIMEOUT_MS = 30000
MAP_LOAD_TIMEOUT_MS = 30000
RETURN_TO_OUTPOST_TIMEOUT_MS = 8000
DEATH_RECOVERY_SETTLE_MS = 5000
ENTRY_KNEEL_WAIT_MS = 4500
CHAMPION_WAIT_TIMEOUT_MS = 5000
CHAMPION_WAIT_POLL_MS = 250
CHAMPION_SEARCH_RADIUS = 1200.0
CHAMPION_INTERACT_TOLERANCE = 175.0
OPENING_PULL_SETTLE_MS = 1000
ABYSSAL_KILL_WINDOW_MS = 38000
RANGER_KILL_WINDOW_MS = 27000
WHIRLING_READY_TIMEOUT_MS = 70000
LOOT_SETTLE_MS = 750
LOOT_COMPLETION_TIMEOUT_MS = 8000
LOOT_CLEAR_POLLS_REQUIRED = 2
LOOT_RANGE = 2500.0
KILL_CONFIRM_RANGE = Range.Earshot.value
class FarmRuntime:
    def __init__(self) -> None:
        self.completed_runs = 0
        self.failed_runs = 0
        self.last_run_succeeded = False
        self.failed_loot_agent_ids: list[int] = []
        self.recovery_coroutine = None
        self.stop_reason = ''


class TowerOfCourageRangerAssassin(BuildMgr):
    def __init__(self) -> None:
        super().__init__(
            name='Tower of Courage Ranger Assassin',
            required_primary=Profession.Ranger,
            required_secondary=Profession.Assassin,
            template_code=SKILL_TEMPLATE,
            required_skills=[
                SHADOW_FORM_SKILL_ID,
                SHROUD_OF_DISTRESS_SKILL_ID,
                I_AM_UNSTOPPABLE_SKILL_ID,
                DARK_ESCAPE_SKILL_ID,
                DWARVEN_STABILITY_SKILL_ID,
                WHIRLING_DEFENSE_SKILL_ID,
                HEART_OF_SHADOW_SKILL_ID,
                MENTAL_BLOCK_SKILL_ID,
            ],
            is_combat_automator_compatible=False,
        )
        self.upkeep_enabled = False
        self.refresh_i_am_unstoppable = False
        self.refresh_mental_block = False
        self.heart_of_shadow_health_threshold: float | None = None
        self.SetSkillCastingFn(self._maintain_defenses)

    def ConfigureUpkeep(
        self,
        enabled: bool,
        *,
        refresh_i_am_unstoppable: bool = False,
        refresh_mental_block: bool = False,
        heart_of_shadow_health_threshold: float | None = None,
    ) -> None:
        self.upkeep_enabled = enabled
        self.refresh_i_am_unstoppable = refresh_i_am_unstoppable
        self.refresh_mental_block = refresh_mental_block
        self.heart_of_shadow_health_threshold = heart_of_shadow_health_threshold

    def EnableUpkeep(self, enabled: bool) -> None:
        self.ConfigureUpkeep(enabled)

    def StartRun(self) -> None:
        self.ConfigureUpkeep(False)

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
            return False

        if not Routines.Checks.Skills.CanCast():
            yield from Routines.Yield.wait(100)
            return False

        if (
            self.refresh_i_am_unstoppable
            and Routines.Checks.Skills.IsSkillSlotReady(I_AM_UNSTOPPABLE_SLOT)
        ):
            return (
                yield from Routines.Yield.Skills.CastSkillSlot(
                    I_AM_UNSTOPPABLE_SLOT,
                    aftercast_delay=200,
                    log=False,
                )
            )

        player_health = Agent.GetHealth(player_id)
        if (
            self.heart_of_shadow_health_threshold is not None
            and Routines.Checks.Skills.IsSkillSlotReady(HEART_OF_SHADOW_SLOT)
            and (
                player_health < self.heart_of_shadow_health_threshold
                or (Agent.IsConditioned(player_id) and player_health < 0.4)
            )
        ):
            return (
                yield from Routines.Yield.Skills.CastSkillSlot(
                    HEART_OF_SHADOW_SLOT,
                    aftercast_delay=350,
                    log=False,
                )
            )

        if Routines.Checks.Skills.IsSkillSlotReady(SHADOW_FORM_SLOT):
            return (
                yield from Routines.Yield.Skills.CastSkillSlot(
                    SHADOW_FORM_SLOT,
                    aftercast_delay=1250,
                    log=False,
                )
            )

        shroud_time_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_id, SHROUD_OF_DISTRESS_SKILL_ID)
        if (
            Routines.Checks.Skills.IsSkillSlotReady(SHROUD_OF_DISTRESS_SLOT)
            and (
                not GLOBAL_CACHE.Effects.HasEffect(player_id, SHROUD_OF_DISTRESS_SKILL_ID)
                or shroud_time_remaining < 10000
            )
        ):
            return (
                yield from Routines.Yield.Skills.CastSkillSlot(
                    SHROUD_OF_DISTRESS_SLOT,
                    aftercast_delay=1350,
                    log=False,
                )
            )

        if (
            self.refresh_mental_block
            and not GLOBAL_CACHE.Effects.HasEffect(player_id, MENTAL_BLOCK_SKILL_ID)
            and Routines.Checks.Skills.IsSkillSlotReady(MENTAL_BLOCK_SLOT)
        ):
            return (
                yield from Routines.Yield.Skills.CastSkillSlot(
                    MENTAL_BLOCK_SLOT,
                    aftercast_delay=250,
                    log=False,
                )
            )

        yield from Routines.Yield.wait(150)
        return False


runtime = FarmRuntime()
build = TowerOfCourageRangerAssassin()
bot = Botting(
    BOT_NAME,
    custom_build=build,
    config_movement_timeout=MOVEMENT_TIMEOUT_MS,
    config_movement_tolerance=MOVE_TOLERANCE,
    upkeep_auto_loot_active=False,
)


def initialize_bot(bot_instance: Botting) -> None:
    bot_instance.Events.OnDeathCallback(lambda: on_death(bot_instance))
    bot_instance.Events.OnPartyWipeCallback(lambda: on_party_wipe(bot_instance))
    bot_instance.Events.OnPartyDefeatedCallback(lambda: on_party_defeated(bot_instance))
    bot_instance.States.AddHeader('Initialize Bot')
    bot_instance.Properties.Disable('auto_loot')
    bot_instance.Properties.Disable('hero_ai')
    bot_instance.Properties.Enable('build_ticker')
    bot_instance.Properties.Disable('pause_on_danger')
    bot_instance.Properties.Enable('halt_on_death')


def create_bot_routine(bot_instance: Botting) -> None:
    initialize_bot(bot_instance)

    bot_instance.States.AddHeader('Main Loop')
    bot_instance.States.AddCustomState(lambda: ensure_temple(bot_instance), 'Ensure Temple')

    bot_instance.States.AddHeader('Prepare Run')
    bot_instance.States.AddCustomState(lambda: load_skillbar(bot_instance), 'Load Skillbar')
    bot_instance.States.AddCustomState(prepare_party, 'Prepare Solo Normal Mode')
    bot_instance.States.AddCustomState(enter_fissure_of_woe, 'Enter FoW')
    bot_instance.States.AddCustomState(run_tower_of_courage_farm, 'Farm Tower of Courage')
    bot_instance.States.AddCustomState(reset_run, 'Reset Run')
    bot_instance.States.JumpToStepName('Ensure Temple')


def on_death(bot_instance: Botting) -> None:
    _begin_failure_recovery(bot_instance, 'death')


def on_party_wipe(bot_instance: Botting) -> None:
    _begin_failure_recovery(bot_instance, 'party wipe')


def on_party_defeated(bot_instance: Botting) -> None:
    _begin_failure_recovery(bot_instance, 'party defeat')


def _is_normal_reset_in_progress(bot_instance: Botting) -> bool:
    current_state = bot_instance.config.FSM.current_state
    return bool(current_state and current_state.name == 'Reset Run')


def _begin_failure_recovery(bot_instance: Botting, reason: str) -> None:
    if not bot_instance.config.fsm_running:
        return

    if _is_normal_reset_in_progress(bot_instance) or runtime.recovery_coroutine is not None:
        return

    runtime.last_run_succeeded = False
    runtime.failed_loot_agent_ids.clear()
    runtime.failed_runs += 1
    ConsoleLog(
        BOT_NAME,
        f'Run failed ({runtime.failed_runs} total failures). Recovering from {reason}.',
        Py4GW.Console.MessageType.Warning,
    )
    ActionQueueManager().ResetAllQueues()
    build.EnableUpkeep(False)
    bot_instance.config.FSM.pause()
    runtime.recovery_coroutine = _recover_from_failure(bot_instance, reason)


def _recover_from_failure(bot_instance: Botting, reason: str):
    yield from Routines.Yield.wait(DEATH_RECOVERY_SETTLE_MS)
    yield from recover_to_temple(resign_if_alive=False)
    ConsoleLog(BOT_NAME, f'Recovery finished after {reason}.', Py4GW.Console.MessageType.Info)
    bot_instance.config.FSM.jump_to_state_by_name('Ensure Temple')
    bot_instance.config.FSM.resume()
    yield


def advance_failure_recovery(bot_instance: Botting) -> None:
    if runtime.recovery_coroutine is None:
        return

    try:
        next(runtime.recovery_coroutine)
    except StopIteration:
        runtime.recovery_coroutine = None
    except Exception as exc:
        ConsoleLog(BOT_NAME, f'Recovery sequence failed: {exc}', Py4GW.Console.MessageType.Error)
        runtime.recovery_coroutine = None
        bot_instance.config.FSM.resume()


def run_failure_watchdog(bot_instance: Botting) -> None:
    if (
        not bot_instance.config.fsm_running
        or runtime.recovery_coroutine is not None
        or _is_normal_reset_in_progress(bot_instance)
    ):
        return

    player_id = Player.GetAgentID()
    if player_id and Agent.IsDead(player_id):
        _begin_failure_recovery(bot_instance, 'death watchdog')
        return

    if not Routines.Checks.Map.MapValid():
        return

    if GLOBAL_CACHE.Party.IsPartyDefeated():
        _begin_failure_recovery(bot_instance, 'party defeat watchdog')
        return

    if Routines.Checks.Party.IsPartyWiped():
        _begin_failure_recovery(bot_instance, 'party wipe watchdog')


def recover_to_temple(resign_if_alive: bool):
    ActionQueueManager().ResetAllQueues()
    build.EnableUpkeep(False)

    if Map.IsExplorable():
        player_id = Player.GetAgentID()
        if player_id and Agent.IsDead(player_id):
            yield from Routines.Yield.wait(3000)
        elif resign_if_alive:
            yield from Routines.Yield.Player.Resign(log=False)
            yield from Routines.Yield.wait(500)

        Party.ReturnToOutpost()
        yield from Routines.Yield.wait(750)
        if Map.IsMapLoading() or Map.IsOutpost() or Map.IsMapIDMatch(Map.GetMapID(), TEMPLE_OF_THE_AGES):
            yield from Routines.Yield.Map.WaitforMapLoad(
                TEMPLE_OF_THE_AGES,
                log=True,
                timeout=RETURN_TO_OUTPOST_TIMEOUT_MS,
            )

    if not Map.IsMapIDMatch(Map.GetMapID(), TEMPLE_OF_THE_AGES):
        yield from Routines.Yield.Map.TravelToOutpost(
            TEMPLE_OF_THE_AGES,
            log=True,
            timeout=MAP_LOAD_TIMEOUT_MS,
        )

    return (
        yield from Routines.Yield.Map.WaitforMapLoad(
            TEMPLE_OF_THE_AGES,
            log=True,
            timeout=MAP_LOAD_TIMEOUT_MS,
        )
    )


def ensure_temple(bot_instance: Botting):
    del bot_instance
    yield from recover_to_temple(resign_if_alive=True)


def stop_safely(bot_instance: Botting, reason: str) -> None:
    runtime.stop_reason = reason
    build.EnableUpkeep(False)
    ConsoleLog(BOT_NAME, reason, Py4GW.Console.MessageType.Error)
    bot_instance.Stop()


def load_skillbar(bot_instance: Botting):
    primary, secondary = Agent.GetProfessionNames(Player.GetAgentID())
    if primary != 'Ranger' or secondary != 'Assassin':
        stop_safely(bot_instance, f'Unsupported profession combo: {primary}/{secondary}. Expected Ranger/Assassin.')
        yield
        return

    build.EnableUpkeep(False)
    yield from build.LoadSkillBar()


def prepare_party():
    Party.LeaveParty()
    yield from Routines.Yield.wait(500)
    Party.SetNormalMode()
    yield from Routines.Yield.wait(250)


def get_champion_of_balthazar() -> int:
    player_position = Player.GetXY()
    champion_ids: list[int] = []
    for agent_id in AgentArray.GetNPCMinipetArray():
        if not Agent.IsValid(agent_id):
            continue
        agent_name = (Agent.GetNameByID(agent_id) or '').strip().lower()
        if CHAMPION_OF_BALTHAZAR_NAME.lower() not in agent_name:
            continue
        if Utils.Distance(TEMPLE_STATUE_COORD, Agent.GetXY(agent_id)) > CHAMPION_SEARCH_RADIUS:
            continue
        champion_ids.append(agent_id)

    if not champion_ids:
        return 0

    return min(champion_ids, key=lambda agent_id: Utils.Distance(player_position, Agent.GetXY(agent_id)))


def wait_for_champion_of_balthazar():
    elapsed_ms = 0
    while elapsed_ms <= CHAMPION_WAIT_TIMEOUT_MS:
        champion_id = get_champion_of_balthazar()
        if champion_id:
            return champion_id
        yield from Routines.Yield.wait(CHAMPION_WAIT_POLL_MS)
        elapsed_ms += CHAMPION_WAIT_POLL_MS
    return 0


def enter_fissure_of_woe():
    runtime.last_run_succeeded = False
    if not Map.IsMapIDMatch(Map.GetMapID(), TEMPLE_OF_THE_AGES):
        ConsoleLog(
            BOT_NAME,
            'FoW entry skipped because Temple of the Ages is not loaded.',
            Py4GW.Console.MessageType.Warning,
        )
        return

    if not (yield from follow_path([TEMPLE_STATUE_COORD], timeout=MOVEMENT_TIMEOUT_MS, tolerance=MOVE_TOLERANCE)):
        ConsoleLog(BOT_NAME, 'Failed to reach the Temple statue.', Py4GW.Console.MessageType.Warning)
        return

    Player.SendChatCommand('kneel')
    yield from Routines.Yield.wait(ENTRY_KNEEL_WAIT_MS)
    champion_id = yield from wait_for_champion_of_balthazar()
    if not champion_id:
        ConsoleLog(BOT_NAME, 'Champion of Balthazar did not appear after /kneel.', Py4GW.Console.MessageType.Warning)
        return

    champion_position = Agent.GetXY(champion_id)
    if not (
        yield from follow_path(
            [champion_position],
            timeout=MOVEMENT_TIMEOUT_MS,
            tolerance=CHAMPION_INTERACT_TOLERANCE,
        )
    ):
        ConsoleLog(BOT_NAME, 'Failed to reach the Champion of Balthazar.', Py4GW.Console.MessageType.Warning)
        return

    yield from Routines.Yield.Player.InteractAgent(champion_id, log=False)
    yield from Routines.Yield.wait(500)
    for dialog_id in TEMPLE_ENTRY_DIALOG_IDS:
        Player.SendDialog(dialog_id)
        yield from Routines.Yield.wait(500)

    if not (
        yield from Routines.Yield.Map.WaitforMapLoad(
            FISSURE_OF_WOE,
            log=True,
            timeout=MAP_LOAD_TIMEOUT_MS,
        )
    ):
        ConsoleLog(BOT_NAME, 'FoW entry failed to confirm a map load.', Py4GW.Console.MessageType.Warning)


def run_tower_of_courage_farm():
    runtime.last_run_succeeded = False
    runtime.failed_loot_agent_ids.clear()

    try:
        if not Map.IsMapIDMatch(Map.GetMapID(), FISSURE_OF_WOE):
            ConsoleLog(BOT_NAME, 'Tower of Courage run started outside FoW.', Py4GW.Console.MessageType.Warning)
            return

        build.StartRun()
        log_opening_phase('Casting Shadow Form, Dwarven Stability, and Dark Escape at FoW departure.')
        if not (
            yield from cast_skill_slot_when_ready(
                SHADOW_FORM_SLOT,
                'Shadow Form',
                ready_timeout_ms=3000,
                aftercast_delay=1250,
            )
        ):
            return
        if not (
            yield from cast_skill_slot_when_ready(
                DWARVEN_STABILITY_SLOT,
                'Dwarven Stability',
                ready_timeout_ms=3000,
                aftercast_delay=1250,
            )
        ):
            return
        if not (
            yield from cast_skill_slot_when_ready(
                DARK_ESCAPE_SLOT,
                'Dark Escape',
                ready_timeout_ms=3000,
                aftercast_delay=250,
            )
        ):
            return

        build.ConfigureUpkeep(True, heart_of_shadow_health_threshold=0.2)
        log_opening_phase('Running the initial pull.')
        abyssal_detected = yield from follow_path_until_nearby_abyssal(
            INITIAL_PULL_PATH,
            timeout=MOVEMENT_TIMEOUT_MS,
            tolerance=MOVE_TOLERANCE,
        )
        if abyssal_detected is None:
            return

        build.ConfigureUpkeep(False)
        if abyssal_detected:
            ActionQueueManager().ResetQueue('ACTION')
            log_opening_phase('Abyssal detected during the initial pull. Casting I Am Unstoppable! immediately.')
        else:
            yield from Routines.Yield.wait(OPENING_PULL_SETTLE_MS)
            log_opening_phase('Initial pull complete. Casting I Am Unstoppable!')
        if not (
            yield from cast_skill_slot_when_ready(
                I_AM_UNSTOPPABLE_SLOT,
                'I Am Unstoppable!',
                ready_timeout_ms=3000,
                aftercast_delay=200,
            )
        ):
            return

        log_opening_phase('Casting Dwarven Stability and Mental Block before balling.')
        yield from cast_skill_slot_if_ready(DWARVEN_STABILITY_SLOT, 'Dwarven Stability', aftercast_delay=1250)
        if not (
            yield from cast_skill_slot_when_ready(
                MENTAL_BLOCK_SLOT,
                'Mental Block',
                ready_timeout_ms=3000,
                aftercast_delay=250,
            )
        ):
            return

        build.ConfigureUpkeep(True, heart_of_shadow_health_threshold=0.2)
        if not (yield from follow_path(ABYSSAL_BALL_PATH, timeout=MOVEMENT_TIMEOUT_MS, tolerance=MOVE_TOLERANCE)):
            return

        build.ConfigureUpkeep(False)
        log_opening_phase('Reached first ball spot. Casting Dwarven Stability and Whirling Defense.')
        yield from cast_skill_slot_if_ready(DWARVEN_STABILITY_SLOT, 'Dwarven Stability', aftercast_delay=1250)
        if not (
            yield from cast_skill_slot_when_ready(
                WHIRLING_DEFENSE_SLOT,
                'Whirling Defense',
                ready_timeout_ms=3000,
                aftercast_delay=250,
            )
        ):
            return

        whirling_start = Utils.GetBaseTimestamp()
        build.ConfigureUpkeep(
            True,
            refresh_i_am_unstoppable=True,
            refresh_mental_block=True,
            heart_of_shadow_health_threshold=0.3,
        )
        if not (yield from follow_path(ABYSSAL_KILL_PATH, timeout=MOVEMENT_TIMEOUT_MS, tolerance=MOVE_TOLERANCE)):
            return

        remaining_abyssal_window = max(0, ABYSSAL_KILL_WINDOW_MS - (Utils.GetBaseTimestamp() - whirling_start))
        if not (
            yield from wait_for_kill_window(
                remaining_abyssal_window,
                abyssals_only=True,
                stop_when_whirling_expires=True,
                finish_when_clear=True,
            )
        ):
            return

        yield from Routines.Yield.wait(500)
        build.ConfigureUpkeep(True, heart_of_shadow_health_threshold=0.2)
        if not (yield from follow_path(RANGER_BALL_PATH[:2], timeout=MOVEMENT_TIMEOUT_MS, tolerance=MOVE_TOLERANCE)):
            return
        yield from Routines.Yield.wait(1500)
        if not (yield from follow_path(RANGER_BALL_PATH[2:], timeout=MOVEMENT_TIMEOUT_MS, tolerance=MOVE_TOLERANCE)):
            return

        build.ConfigureUpkeep(
            True,
            refresh_i_am_unstoppable=True,
            refresh_mental_block=True,
            heart_of_shadow_health_threshold=0.3,
        )
        if not (yield from wait_for_ranger_kill_skills()):
            return

        build.ConfigureUpkeep(True, heart_of_shadow_health_threshold=0.2)
        if not (
            yield from follow_path(RANGER_KILL_APPROACH_PATH, timeout=MOVEMENT_TIMEOUT_MS, tolerance=MOVE_TOLERANCE)
        ):
            return

        build.ConfigureUpkeep(False)
        yield from cast_skill_slot_if_ready(I_AM_UNSTOPPABLE_SLOT, 'I Am Unstoppable!', aftercast_delay=200)
        yield from cast_skill_slot_if_ready(DWARVEN_STABILITY_SLOT, 'Dwarven Stability', aftercast_delay=1250)
        yield from cast_skill_slot_if_ready(MENTAL_BLOCK_SLOT, 'Mental Block', aftercast_delay=250)
        if not (
            yield from cast_skill_slot_when_ready(
                WHIRLING_DEFENSE_SLOT,
                'Whirling Defense',
                ready_timeout_ms=3000,
                aftercast_delay=250,
            )
        ):
            return

        build.ConfigureUpkeep(True, refresh_i_am_unstoppable=True)
        if not (yield from follow_path(RANGER_KILL_PATH, timeout=MOVEMENT_TIMEOUT_MS, tolerance=MOVE_TOLERANCE)):
            return
        if not (
            yield from wait_for_kill_window(
                RANGER_KILL_WINDOW_MS,
                abyssals_only=False,
                stop_when_whirling_expires=False,
                finish_when_clear=False,
            )
        ):
            return
        build.ConfigureUpkeep(True, heart_of_shadow_health_threshold=0.2)
        if not (yield from follow_path([RANGER_LOOT_COORD], timeout=MOVEMENT_TIMEOUT_MS, tolerance=MOVE_TOLERANCE)):
            return

        build.ConfigureUpkeep(False)
        yield from Routines.Yield.wait(LOOT_SETTLE_MS)
        if not (yield from loot_run_drops()):
            return

        runtime.last_run_succeeded = not Agent.IsDead(Player.GetAgentID())
    finally:
        build.EnableUpkeep(False)


def reset_run():
    if runtime.last_run_succeeded:
        runtime.completed_runs += 1
        ConsoleLog(BOT_NAME, f'Run {runtime.completed_runs} completed.', Py4GW.Console.MessageType.Success)
    else:
        runtime.failed_runs += 1
        ConsoleLog(BOT_NAME, f'Run failed ({runtime.failed_runs} total failures).', Py4GW.Console.MessageType.Warning)

    build.EnableUpkeep(False)
    yield from recover_to_temple(resign_if_alive=True)
    yield


def cast_skill_slot(slot: int, aftercast_delay: int = 250):
    return (
        yield from Routines.Yield.Skills.CastSkillSlot(
            slot,
            aftercast_delay=aftercast_delay,
            log=False,
        )
    )


def cast_skill_slot_when_ready(slot: int, skill_name: str, ready_timeout_ms: int, aftercast_delay: int = 250):
    start_time = Utils.GetBaseTimestamp()
    while Utils.GetBaseTimestamp() - start_time <= ready_timeout_ms:
        if Agent.IsDead(Player.GetAgentID()):
            return False
        if Routines.Checks.Skills.IsSkillSlotReady(slot) and Routines.Checks.Skills.CanCast():
            if (yield from cast_skill_slot(slot, aftercast_delay=aftercast_delay)):
                if (
                    yield from wait_for_condition(
                        lambda: not Routines.Checks.Skills.IsSkillSlotReady(slot)
                        or Agent.IsDead(Player.GetAgentID()),
                        timeout_ms=1000,
                        step_ms=50,
                    )
                ):
                    return not Agent.IsDead(Player.GetAgentID())
        yield from Routines.Yield.wait(100)

    ConsoleLog(BOT_NAME, f'{skill_name} was not cast in time.', Py4GW.Console.MessageType.Warning)
    return False


def cast_skill_slot_if_ready(slot: int, skill_name: str, aftercast_delay: int = 250):
    if not Routines.Checks.Skills.IsSkillSlotReady(slot):
        return False
    return (
        yield from cast_skill_slot_when_ready(
            slot,
            skill_name,
            ready_timeout_ms=1000,
            aftercast_delay=aftercast_delay,
        )
    )


def follow_path(path_points: list[tuple[float, float]], timeout: int, tolerance: float) -> bool:
    for target_x, target_y in path_points:
        generated_path = yield from AutoPathing().get_path_to(target_x, target_y)
        active_path = generated_path or [(target_x, target_y)]
        result = yield from Routines.Yield.Movement.FollowPath(
            path_points=active_path,
            custom_exit_condition=lambda: Agent.IsDead(Player.GetAgentID()) or Map.IsMapLoading(),
            timeout=timeout,
            tolerance=tolerance,
            log=False,
            autopath=True,
        )
        if not result:
            return False
    return True


def follow_path_until_nearby_abyssal(
    path_points: list[tuple[float, float]],
    timeout: int,
    tolerance: float,
) -> bool | None:
    for target_x, target_y in path_points:
        if has_nearby_abyssal():
            return True
        generated_path = yield from AutoPathing().get_path_to(target_x, target_y)
        if has_nearby_abyssal():
            return True
        active_path = generated_path or [(target_x, target_y)]
        result = yield from Routines.Yield.Movement.FollowPath(
            path_points=active_path,
            custom_exit_condition=lambda: Agent.IsDead(Player.GetAgentID())
            or Map.IsMapLoading()
            or has_nearby_abyssal(),
            timeout=timeout,
            tolerance=tolerance,
            log=False,
            autopath=True,
        )
        if Agent.IsDead(Player.GetAgentID()) or Map.IsMapLoading():
            return None
        if has_nearby_abyssal():
            return True
        if not result:
            return None
    return False


def wait_for_condition(condition, timeout_ms: int, step_ms: int = 100) -> bool:
    elapsed = 0
    while elapsed < timeout_ms:
        if condition():
            return True
        yield from Routines.Yield.wait(step_ms)
        elapsed += step_ms
    return condition()


def log_opening_phase(message: str) -> None:
    ConsoleLog(BOT_NAME, f'Opening phase: {message}', Py4GW.Console.MessageType.Info)


def has_nearby_abyssal() -> bool:
    return get_nearby_foe_count(Range.Earshot.value, abyssals_only=True) > 0


def wait_for_ranger_kill_skills() -> bool:
    start_time = Utils.GetBaseTimestamp()
    while Utils.GetBaseTimestamp() - start_time <= WHIRLING_READY_TIMEOUT_MS:
        if Agent.IsDead(Player.GetAgentID()):
            return False
        if (
            Routines.Checks.Skills.IsSkillSlotReady(MENTAL_BLOCK_SLOT)
            and Routines.Checks.Skills.IsSkillSlotReady(WHIRLING_DEFENSE_SLOT)
        ):
            return True
        yield from Routines.Yield.wait(100)

    ConsoleLog(BOT_NAME, 'Ranger kill skills did not recharge in time.', Py4GW.Console.MessageType.Warning)
    return False


def wait_for_kill_window(
    duration_ms: int,
    *,
    abyssals_only: bool,
    stop_when_whirling_expires: bool,
    finish_when_clear: bool,
) -> bool:
    start_time = Utils.GetBaseTimestamp()
    clear_polls = 0

    while Utils.GetBaseTimestamp() - start_time <= duration_ms:
        if Agent.IsDead(Player.GetAgentID()):
            return False

        if stop_when_whirling_expires and not GLOBAL_CACHE.Effects.HasEffect(
            Player.GetAgentID(),
            WHIRLING_DEFENSE_SKILL_ID,
        ):
            return True

        if finish_when_clear:
            if get_nearby_foe_count(KILL_CONFIRM_RANGE, abyssals_only) == 0:
                clear_polls += 1
                if clear_polls >= 3:
                    return True
            else:
                clear_polls = 0

        yield from Routines.Yield.wait(100)

    return not Agent.IsDead(Player.GetAgentID())


def get_nearby_foe_count(max_distance: float, abyssals_only: bool) -> int:
    px, py = Player.GetXY()
    enemy_array = Routines.Agents.GetFilteredEnemyArray(px, py, max_distance)
    if abyssals_only:
        enemy_array = [agent_id for agent_id in enemy_array if Agent.GetModelID(agent_id) in ABYSSAL_MODEL_IDS]
    return len(enemy_array)


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
            return True

        if Utils.GetBaseTimestamp() - start_time > LOOT_COMPLETION_TIMEOUT_MS:
            return len(get_loot_agent_ids()) == 0

        yield from Routines.Yield.wait(500)


def get_loot_agent_ids() -> list[int]:
    player_position = Player.GetXY()
    item_agent_ids = [
        agent_id
        for agent_id in AgentArray.GetItemArray()
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

    model_id = int(Item.GetModelID(item_id) or 0)
    is_weapon = bool(Item.Type.IsWeapon(item_id))
    _, requirement = Item.Properties.GetRequirement(item_id)
    _, rarity_name = Item.Rarity.GetRarity(item_id)
    return loot_policy.should_pick_up_item(model_id, is_weapon, int(requirement or 0), rarity_name)


create_bot_routine(bot)


def tooltip():
    from Py4GWCoreLib import Color
    from Py4GWCoreLib import ImGui

    title_color = Color(255, 200, 100, 255)

    ImGui.push_font('Regular', 20)
    PyImGui.text_colored(BOT_NAME, title_color.to_tuple_normalized())
    ImGui.pop_font()

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    PyImGui.text('Solo Ranger / Assassin Tower of Courage farmer.')
    PyImGui.text('Runs Normal Mode FoW from Temple of the Ages using /kneel.')

    PyImGui.spacing()
    PyImGui.text_colored('Requirements', title_color.to_tuple_normalized())
    PyImGui.bullet_text('Primary / Secondary: Ranger / Assassin (R/A)')
    PyImGui.bullet_text(f'Skill template: {SKILL_TEMPLATE}')
    PyImGui.bullet_text('Recommended: enchanted armor, enchanting weapon, piercing shield, rank 5+ PvE titles')

    PyImGui.spacing()
    PyImGui.text_colored('Ground loot', title_color.to_tuple_normalized())
    PyImGui.bullet_text('Obsidian Shards, Dark Remains, Rubies, Sapphires, and FoW passage scrolls')
    PyImGui.bullet_text('Purple or gold q7 and q8 weapons')
    PyImGui.bullet_text('q9 Chaos Axes only')
    PyImGui.bullet_text('All other drops are left on the ground')

    PyImGui.spacing()
    PyImGui.text_colored('Recovery', title_color.to_tuple_normalized())
    PyImGui.bullet_text('Returns to Temple after each run or recoverable failure')


bot.UI.override_draw_help(tooltip)


def main_window_extra_ui() -> None:
    PyImGui.text('Run statistics')
    PyImGui.text(f'Successful runs: {runtime.completed_runs}')
    PyImGui.text(f'Failed runs: {runtime.failed_runs}')


def main():
    advance_failure_recovery(bot)
    run_failure_watchdog(bot)
    bot.Update()
    bot.UI.draw_window(icon_path=BOT_TEXTURE, additional_ui=main_window_extra_ui)


if __name__ == '__main__':
    main()
