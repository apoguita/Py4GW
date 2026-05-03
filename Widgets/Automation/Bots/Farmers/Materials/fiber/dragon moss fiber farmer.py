from __future__ import annotations
import re
import unicodedata

from Py4GWCoreLib import (
    ActionQueueManager,
    Agent,
    AgentArray,
    AutoInventoryHandler,
    Botting,
    BuildMgr,
    ConsoleLog,
    GLOBAL_CACHE,
    IniManager,
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
from Py4GWCoreLib.enums_src.IO_enums import Key
from Py4GWCoreLib.py4gwcorelib_src.Keystroke import Keystroke
import PyImGui

BOT_NAME = "Dragon Moss Fiber Farmer"
MODULE_ICON = "Textures\\Module_Icons\\Dragon_Moss_Fiber_Farm.png"

ANJEKAS_SHRINE = 349
DRAZACH_THICKET = 195
MAATU_KEEP = 283
EMBARK_BEACH = 857

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
KWAT_NPC_NAME = "Kwat"
KWAT_NPC_COORD = (3589.15, 101.18)

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
DRAGON_ROOT_MODEL_ID = 819
PLANT_FIBER_MODEL_ID = ModelID.Plant_Fiber.value
BONE_MODEL_ID = ModelID.Bone.value
SCROLL_OF_RESURRECTION_MODEL_ID = ModelID.Scroll_Of_Resurrection.value
SCROLL_CRAFT_GOLD_COST = 250
SCROLL_CRAFT_FIBER_COST = 25
SCROLL_CRAFT_BONE_COST = 25
SCROLL_CRAFT_SKILL_POINTS_COST = 1
CRAFTING_THRESHOLD_OPTIONS = [250, 500, 750, 1000]
CRAFTING_REROLL_TIMEOUT_MS = 45000
CHARACTER_LIST_RETRY_TIMEOUT_MS = 15000
CHARACTER_LIST_RETRY_STEP_MS = 250
MIN_CRAFTING_GOLD_ON_CHARACTER = 20000
MAX_CRAFTING_GOLD_ON_CHARACTER = 100000
XUNLAI_INTERACT_TIMEOUT_MS = 6000
XUNLAI_INTERACT_TOLERANCE = 225.0
KWAT_CLOSE_ENOUGH_DISTANCE = 200.0
KWAT_MAX_REACH_ATTEMPTS = 5
KWAT_RETRY_DELAY_MS = 400
KWAT_MOVE_TIMEOUT_MS = 3000
MATERIAL_WITHDRAW_ATTEMPTS = 25
SPECIAL_LOOT_MODEL_IDS = {
    22751,
    ModelID.Golden_Egg.value,
    ModelID.Chocolate_Bunny.value,
}
VALUABLE_GOLD_MODEL_IDS = {940, 945, 951, 954}
MATERIAL_MODEL_IDS = {819, 934, 956}
VALUABLE_DYE_COLORS = {10, 12}
SETTINGS_PATH = "Bots/Farmers/Materials/Fiber"
SETTINGS_FILE = "dragon_moss_fiber_farmer.ini"
SETTINGS_SECTION_CRAFTING = "Crafting Rotation"
SETTINGS_SECTION_INVENTORY = "Inventory"


class FarmRuntime:
    def __init__(self) -> None:
        self.completed_runs: int = 0
        self.failed_runs: int = 0
        self.last_run_succeeded: bool = False
        self.failed_loot_agent_ids: list[int] = []
        self.recovery_coroutine = None
        self.crafting_rotation_status: str = "Idle"
        self.farmer_character_name: str = ""


class CraftingRotationSettings:
    def __init__(self) -> None:
        self.ini_key: str = ""
        self.loaded: bool = False
        self.enable_crafting_rotation: bool = False
        self.crafter_character: str = ""
        self.fiber_threshold: int = 250
        self.bones_threshold: int = 250
        self.switch_back_to_farmer: bool = True
        self.auto_salvage_dragon_root_on_town_return: bool = False


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
rotation_settings = CraftingRotationSettings()
build = DragonMossRangerAssassin()
bot = Botting(
    BOT_NAME,
    custom_build=build,
    config_movement_timeout=MOVEMENT_TIMEOUT_MS,
    config_movement_tolerance=MOVE_TOLERANCE,
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
    bot_instance.Properties.Enable("hero_ai")
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
    bot_instance.States.AddCustomState(lambda: salvage_dragon_root_on_town_return(bot_instance), "Salvage Dragon Root")
    bot_instance.States.AddCustomState(lambda: maybe_run_crafting_rotation(bot_instance), "Crafting Rotation Check")
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
    if not needs_inventory_management() and not requires_town_checkpoint():
        bot.config.FSM.jump_to_state_by_name("Deposit Excess Gold")
    yield


def needs_inventory_management() -> bool:
    return (
        Inventory.GetFreeSlotCount() < MIN_FREE_SLOTS
        or Inventory.GetFirstIDKit() == 0
        or Inventory.GetFirstSalvageKit() == 0
    )


def ensure_rotation_settings_loaded() -> None:
    if rotation_settings.loaded:
        return

    ini_key = IniManager().ensure_key(SETTINGS_PATH, SETTINGS_FILE)
    if not ini_key:
        return

    rotation_settings.ini_key = ini_key
    IniManager().add_bool(ini_key, "enable_crafting_rotation", SETTINGS_SECTION_CRAFTING, "Enable", False)
    IniManager().add_str(ini_key, "crafter_character", SETTINGS_SECTION_CRAFTING, "CrafterCharacter", "")
    IniManager().add_int(ini_key, "fiber_threshold", SETTINGS_SECTION_CRAFTING, "FiberThreshold", 250)
    IniManager().add_int(ini_key, "bones_threshold", SETTINGS_SECTION_CRAFTING, "BonesThreshold", 250)
    IniManager().add_bool(ini_key, "switch_back_to_farmer", SETTINGS_SECTION_CRAFTING, "SwitchBackToFarmer", True)
    IniManager().add_bool(
        ini_key,
        "auto_salvage_dragon_root_on_town_return",
        SETTINGS_SECTION_INVENTORY,
        "AutoSalvageDragonRootOnTownReturn",
        False,
    )
    IniManager().load_once(ini_key)

    rotation_settings.enable_crafting_rotation = IniManager().getBool(
        ini_key,
        "enable_crafting_rotation",
        False,
        SETTINGS_SECTION_CRAFTING,
    )
    rotation_settings.crafter_character = IniManager().getStr(
        ini_key,
        "crafter_character",
        "",
        SETTINGS_SECTION_CRAFTING,
    )
    rotation_settings.fiber_threshold = sanitize_threshold(
        IniManager().getInt(
            ini_key,
            "fiber_threshold",
            250,
            SETTINGS_SECTION_CRAFTING,
        )
    )
    rotation_settings.bones_threshold = sanitize_threshold(
        IniManager().getInt(
            ini_key,
            "bones_threshold",
            250,
            SETTINGS_SECTION_CRAFTING,
        )
    )
    rotation_settings.switch_back_to_farmer = IniManager().getBool(
        ini_key,
        "switch_back_to_farmer",
        True,
        SETTINGS_SECTION_CRAFTING,
    )
    rotation_settings.auto_salvage_dragon_root_on_town_return = IniManager().getBool(
        ini_key,
        "auto_salvage_dragon_root_on_town_return",
        False,
        SETTINGS_SECTION_INVENTORY,
    )
    rotation_settings.loaded = True


def sanitize_threshold(value: int) -> int:
    if value in CRAFTING_THRESHOLD_OPTIONS:
        return value
    return CRAFTING_THRESHOLD_OPTIONS[0]


def save_rotation_setting(var_name: str, value, section: str) -> None:
    ensure_rotation_settings_loaded()
    if not rotation_settings.ini_key:
        return
    IniManager().set(rotation_settings.ini_key, var_name, value, section)


def requires_town_checkpoint() -> bool:
    ensure_rotation_settings_loaded()
    return (
        rotation_settings.enable_crafting_rotation
        or rotation_settings.auto_salvage_dragon_root_on_town_return
    )


def get_total_material_count(model_id: int) -> int:
    return GLOBAL_CACHE.Inventory.GetModelCount(model_id) + GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)


def should_start_crafting_rotation() -> bool:
    ensure_rotation_settings_loaded()
    if not rotation_settings.enable_crafting_rotation:
        return False

    crafter_name = rotation_settings.crafter_character.strip()
    if not crafter_name:
        return False

    return (
        get_total_material_count(PLANT_FIBER_MODEL_ID) >= rotation_settings.fiber_threshold
        and get_total_material_count(BONE_MODEL_ID) >= rotation_settings.bones_threshold
    )


def set_crafting_rotation_status(status: str) -> None:
    runtime.crafting_rotation_status = status


def get_threshold_combo_index(value: int) -> int:
    try:
        return CRAFTING_THRESHOLD_OPTIONS.index(value)
    except ValueError:
        return 0


def draw_rotation_settings() -> None:
    ensure_rotation_settings_loaded()
    PyImGui.text("Dragon Moss Rotation Settings")
    PyImGui.separator()

    if not rotation_settings.ini_key:
        PyImGui.text("Waiting for account settings to become available...")
        return

    enable_crafting = PyImGui.checkbox("Enable crafting rotation", rotation_settings.enable_crafting_rotation)
    if enable_crafting != rotation_settings.enable_crafting_rotation:
        rotation_settings.enable_crafting_rotation = enable_crafting
        save_rotation_setting("enable_crafting_rotation", enable_crafting, SETTINGS_SECTION_CRAFTING)

    crafter_name = PyImGui.input_text("Crafter character", rotation_settings.crafter_character, 64)
    if crafter_name != rotation_settings.crafter_character:
        rotation_settings.crafter_character = crafter_name.strip()
        save_rotation_setting("crafter_character", rotation_settings.crafter_character, SETTINGS_SECTION_CRAFTING)

    fiber_index = get_threshold_combo_index(rotation_settings.fiber_threshold)
    new_fiber_index = PyImGui.combo("Fiber threshold", fiber_index, [str(value) for value in CRAFTING_THRESHOLD_OPTIONS])
    if new_fiber_index != fiber_index:
        rotation_settings.fiber_threshold = CRAFTING_THRESHOLD_OPTIONS[new_fiber_index]
        save_rotation_setting("fiber_threshold", rotation_settings.fiber_threshold, SETTINGS_SECTION_CRAFTING)

    bones_index = get_threshold_combo_index(rotation_settings.bones_threshold)
    new_bones_index = PyImGui.combo("Bones threshold", bones_index, [str(value) for value in CRAFTING_THRESHOLD_OPTIONS])
    if new_bones_index != bones_index:
        rotation_settings.bones_threshold = CRAFTING_THRESHOLD_OPTIONS[new_bones_index]
        save_rotation_setting("bones_threshold", rotation_settings.bones_threshold, SETTINGS_SECTION_CRAFTING)

    switch_back = PyImGui.checkbox("Switch back to farmer after crafting", rotation_settings.switch_back_to_farmer)
    if switch_back != rotation_settings.switch_back_to_farmer:
        rotation_settings.switch_back_to_farmer = switch_back
        save_rotation_setting("switch_back_to_farmer", switch_back, SETTINGS_SECTION_CRAFTING)

    salvage_dragon_root = PyImGui.checkbox(
        "Auto salvage Dragon Root on town return",
        rotation_settings.auto_salvage_dragon_root_on_town_return,
    )
    if salvage_dragon_root != rotation_settings.auto_salvage_dragon_root_on_town_return:
        rotation_settings.auto_salvage_dragon_root_on_town_return = salvage_dragon_root
        save_rotation_setting(
            "auto_salvage_dragon_root_on_town_return",
            salvage_dragon_root,
            SETTINGS_SECTION_INVENTORY,
        )

    PyImGui.separator()
    PyImGui.text(f"Fiber available: {get_total_material_count(PLANT_FIBER_MODEL_ID)}")
    PyImGui.text(f"Bones available: {get_total_material_count(BONE_MODEL_ID)}")
    PyImGui.text(f"Dragon Root available: {get_total_material_count(DRAGON_ROOT_MODEL_ID)}")
    PyImGui.text(f"Crafting status: {runtime.crafting_rotation_status}")
    if rotation_settings.enable_crafting_rotation and not rotation_settings.crafter_character.strip():
        PyImGui.text("Enter a crafter character name to enable the rotation trigger.")


def interact_with_maatu_xunlai() -> bool:
    if not (yield from follow_path([MAATU_XUNLAI_COORD], timeout=MOVEMENT_TIMEOUT_MS, tolerance=MOVE_TOLERANCE)):
        ConsoleLog(BOT_NAME, "Failed to reach the Maatu Xunlai chest.", Py4GW.Console.MessageType.Warning)
        return False

    interacted = yield from Routines.Yield.Agents.InteractWithAgentXY(
        MAATU_XUNLAI_COORD[0],
        MAATU_XUNLAI_COORD[1],
        timeout_ms=XUNLAI_INTERACT_TIMEOUT_MS,
        tolerance=XUNLAI_INTERACT_TOLERANCE,
    )
    if not interacted:
        ConsoleLog(BOT_NAME, "Failed to interact with the Maatu Xunlai chest.", Py4GW.Console.MessageType.Warning)
        return False

    yield from Routines.Yield.wait(500)
    return True


def auto_deposit_items_and_gold() -> None:
    inventory_handler = AutoInventoryHandler()
    current_state = inventory_handler.module_active
    inventory_handler.module_active = False
    try:
        yield from inventory_handler.DepositItemsAuto()
        yield from Routines.Yield.Items.DepositGold(inventory_handler.keep_gold, log=False)
    finally:
        inventory_handler.module_active = current_state


def salvage_dragon_root_on_town_return(bot_instance: Botting):
    del bot_instance
    ensure_rotation_settings_loaded()
    if not rotation_settings.auto_salvage_dragon_root_on_town_return:
        yield
        return

    if Inventory.GetFirstSalvageKit() == 0:
        ConsoleLog(
            BOT_NAME,
            "Dragon Root salvage is enabled, but no salvage kit is available after restock.",
            Py4GW.Console.MessageType.Warning,
        )
        yield
        return

    total_roots = get_total_material_count(DRAGON_ROOT_MODEL_ID)
    if total_roots <= 0:
        yield
        return

    set_crafting_rotation_status("Salvaging Dragon Root")
    ConsoleLog(
        BOT_NAME,
        f"Dragon Root salvage checkpoint started with {total_roots} total Dragon Root available.",
        Py4GW.Console.MessageType.Info,
    )

    if not (yield from interact_with_maatu_xunlai()):
        set_crafting_rotation_status("Idle")
        yield
        return

    while True:
        inventory_root_ids = GLOBAL_CACHE.Inventory.GetAllItemIdsByModelID(DRAGON_ROOT_MODEL_ID)
        storage_root_count = GLOBAL_CACHE.Inventory.GetModelCountInStorage(DRAGON_ROOT_MODEL_ID)
        if not inventory_root_ids and storage_root_count <= 0:
            break

        if not inventory_root_ids and storage_root_count > 0:
            max_withdraw = max(1, Inventory.GetFreeSlotCount()) * 250
            yield from Routines.Yield.Items.WithdrawUpTo(DRAGON_ROOT_MODEL_ID, max_withdraw)
            inventory_root_ids = GLOBAL_CACHE.Inventory.GetAllItemIdsByModelID(DRAGON_ROOT_MODEL_ID)

        if not inventory_root_ids:
            ConsoleLog(
                BOT_NAME,
                "Dragon Root remains in storage, but nothing could be withdrawn for salvage.",
                Py4GW.Console.MessageType.Warning,
            )
            break

        yield from Routines.Yield.Items.SalvageItems(inventory_root_ids, log=True)
        yield from auto_deposit_items_and_gold()

    ConsoleLog(BOT_NAME, "Dragon Root salvage checkpoint finished.", Py4GW.Console.MessageType.Success)
    set_crafting_rotation_status("Idle")
    yield


def calculate_scroll_crafting_batch_count(
    fiber_count: int,
    bone_count: int,
    gold_amount: int,
    skill_points: int,
) -> int:
    return min(
        fiber_count // SCROLL_CRAFT_FIBER_COST,
        bone_count // SCROLL_CRAFT_BONE_COST,
        gold_amount // SCROLL_CRAFT_GOLD_COST,
        skill_points // SCROLL_CRAFT_SKILL_POINTS_COST,
    )


def calculate_total_scroll_crafting_batch_count(gold_amount: int) -> int:
    total_fiber = get_total_material_count(PLANT_FIBER_MODEL_ID)
    total_bones = get_total_material_count(BONE_MODEL_ID)
    current_skill_points, _ = Player.GetSkillPointData()
    return calculate_scroll_crafting_batch_count(
        total_fiber,
        total_bones,
        gold_amount,
        current_skill_points,
    )


def calculate_inventory_scroll_crafting_batch_count() -> int:
    current_fiber = GLOBAL_CACHE.Inventory.GetModelCount(PLANT_FIBER_MODEL_ID)
    current_bones = GLOBAL_CACHE.Inventory.GetModelCount(BONE_MODEL_ID)
    current_gold = Inventory.GetGoldOnCharacter()
    current_skill_points, _ = Player.GetSkillPointData()
    if Inventory.GetFreeSlotCount() <= 0 and GLOBAL_CACHE.Inventory.GetFirstModelID(SCROLL_OF_RESURRECTION_MODEL_ID) == 0:
        return 0
    return calculate_scroll_crafting_batch_count(
        current_fiber,
        current_bones,
        current_gold,
        current_skill_points,
    )


def get_inventory_material_stack_headroom(model_id: int) -> int:
    headroom = 0
    for item_id in GLOBAL_CACHE.Inventory.GetAllItemIdsByModelID(model_id):
        quantity = Item.Properties.GetQuantity(item_id)
        if 0 < quantity < 250:
            headroom += 250 - quantity
    return headroom


def calculate_balanced_material_withdraw_targets(gold_amount: int) -> tuple[int, int, int]:
    current_fiber = GLOBAL_CACHE.Inventory.GetModelCount(PLANT_FIBER_MODEL_ID)
    current_bones = GLOBAL_CACHE.Inventory.GetModelCount(BONE_MODEL_ID)
    storage_fiber = GLOBAL_CACHE.Inventory.GetModelCountInStorage(PLANT_FIBER_MODEL_ID)
    storage_bones = GLOBAL_CACHE.Inventory.GetModelCountInStorage(BONE_MODEL_ID)
    total_fiber = current_fiber + storage_fiber
    total_bones = current_bones + storage_bones
    current_skill_points, _ = Player.GetSkillPointData()

    extra_inventory_capacity = (
        Inventory.GetFreeSlotCount() * 250
        + get_inventory_material_stack_headroom(PLANT_FIBER_MODEL_ID)
        + get_inventory_material_stack_headroom(BONE_MODEL_ID)
    )

    max_scroll_count = min(
        total_fiber // SCROLL_CRAFT_FIBER_COST,
        total_bones // SCROLL_CRAFT_BONE_COST,
        gold_amount // SCROLL_CRAFT_GOLD_COST,
        current_skill_points // SCROLL_CRAFT_SKILL_POINTS_COST,
    )

    low = 0
    high = max_scroll_count
    best_scroll_count = 0

    while low <= high:
        mid = (low + high) // 2
        target_quantity = mid * SCROLL_CRAFT_FIBER_COST
        extra_needed = max(0, target_quantity - current_fiber) + max(0, target_quantity - current_bones)
        if (
            target_quantity <= total_fiber
            and target_quantity <= total_bones
            and extra_needed <= extra_inventory_capacity
        ):
            best_scroll_count = mid
            low = mid + 1
        else:
            high = mid - 1

    target_quantity = best_scroll_count * SCROLL_CRAFT_FIBER_COST
    target_fiber = max(current_fiber, target_quantity)
    target_bones = max(current_bones, target_quantity)
    return best_scroll_count, target_fiber, target_bones


def has_scroll_of_resurrection_offer() -> bool:
    return any(
        Item.GetModelID(item_id) == SCROLL_OF_RESURRECTION_MODEL_ID
        for item_id in GLOBAL_CACHE.Trading.Merchant.GetOfferedItems()
    )


def normalize_character_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(name or ""))
    normalized = " ".join(normalized.strip().split())
    return normalized.casefold()


def loose_character_name(name: str) -> str:
    normalized = normalize_character_name(name)
    return re.sub(r"[\W_]+", "", normalized, flags=re.UNICODE)


def get_pregame_character_names() -> list[str]:
    names: list[str] = []
    for character in Map.Pregame.GetCharList():
        name = getattr(character, "character_name", "") or ""
        if name.strip():
            names.append(name)
    return names


def get_available_character_names() -> list[str]:
    names: list[str] = []
    for character in Map.Pregame.GetAvailableCharacterList():
        name = getattr(character, "player_name", "") or ""
        if name.strip():
            names.append(name)
    return names


def log_character_match_debug(configured_name: str, pregame_names: list[str], available_names: list[str]) -> None:
    configured_normalized = normalize_character_name(configured_name)
    configured_loose = loose_character_name(configured_name)
    ConsoleLog(
        BOT_NAME,
        (
            f"Crafter match debug: configured='{configured_name}' "
            f"normalized='{configured_normalized}' loose='{configured_loose}'."
        ),
        Py4GW.Console.MessageType.Info,
    )

    if not pregame_names:
        ConsoleLog(BOT_NAME, "Pregame character list is empty.", Py4GW.Console.MessageType.Info)
    else:
        ConsoleLog(BOT_NAME, f"Pregame character list ({len(pregame_names)} entries):", Py4GW.Console.MessageType.Info)
        for index, name in enumerate(pregame_names):
            ConsoleLog(
                BOT_NAME,
                (
                    f"Pregame[{index}]='{name}' "
                    f"normalized='{normalize_character_name(name)}' loose='{loose_character_name(name)}'"
                ),
                Py4GW.Console.MessageType.Info,
            )

    if not available_names:
        ConsoleLog(BOT_NAME, "Available character list is empty.", Py4GW.Console.MessageType.Info)
    else:
        ConsoleLog(BOT_NAME, f"Available character list ({len(available_names)} entries):", Py4GW.Console.MessageType.Info)
        for index, name in enumerate(available_names):
            ConsoleLog(
                BOT_NAME,
                (
                    f"Available[{index}]='{name}' "
                    f"normalized='{normalize_character_name(name)}' loose='{loose_character_name(name)}'"
                ),
                Py4GW.Console.MessageType.Info,
            )


def resolve_character_match(configured_name: str, character_names: list[str]) -> tuple[int, str, str] | None:
    if not character_names:
        return None

    configured_normalized = normalize_character_name(configured_name)
    configured_loose = loose_character_name(configured_name)

    exact_matches = [
        (index, name)
        for index, name in enumerate(character_names)
        if normalize_character_name(name) == configured_normalized
    ]
    if len(exact_matches) == 1:
        index, name = exact_matches[0]
        return index, name, "exact-normalized"
    if len(exact_matches) > 1:
        return None

    loose_matches = [
        (index, name)
        for index, name in enumerate(character_names)
        if loose_character_name(name) == configured_loose
    ]
    if len(loose_matches) == 1:
        index, name = loose_matches[0]
        return index, name, "exact-loose"
    if len(loose_matches) > 1:
        return None

    if configured_loose:
        partial_matches = [
            (index, name)
            for index, name in enumerate(character_names)
            if configured_loose in loose_character_name(name)
            or loose_character_name(name) in configured_loose
        ]
        if len(partial_matches) == 1:
            index, name = partial_matches[0]
            return index, name, "partial-loose"

    return None


def wait_for_character_select_match(
    configured_name: str,
    timeout_ms: int = CHARACTER_LIST_RETRY_TIMEOUT_MS,
):
    elapsed = 0
    last_pregame_names: list[str] = []
    last_available_names: list[str] = []
    while elapsed <= timeout_ms:
        pregame_names = get_pregame_character_names()
        available_names = get_available_character_names()
        if pregame_names:
            match = resolve_character_match(configured_name, pregame_names)
            if match is not None:
                return match

        last_pregame_names = pregame_names
        last_available_names = available_names
        yield from Routines.Yield.wait(CHARACTER_LIST_RETRY_STEP_MS)
        elapsed += CHARACTER_LIST_RETRY_STEP_MS

    log_character_match_debug(configured_name, last_pregame_names, last_available_names)
    return None


def wait_for_loaded_character(expected_name: str, timeout_ms: int = 30000):
    start = Utils.GetBaseTimestamp()
    logged_map_wait = False
    logged_name_wait = False
    last_name = ""

    while Utils.GetBaseTimestamp() - start <= timeout_ms:
        if not Routines.Checks.Map.MapValid() or Map.IsMapLoading() or not Map.IsOutpost():
            if not logged_map_wait:
                ConsoleLog(
                    BOT_NAME,
                    "Waiting for crafter map load to finish in an outpost.",
                    Py4GW.Console.MessageType.Info,
                )
                logged_map_wait = True
            yield from Routines.Yield.wait(500)
            continue

        current_name = Player.GetName() or ""
        if not normalize_character_name(current_name):
            if not logged_name_wait:
                ConsoleLog(
                    BOT_NAME,
                    "Map load finished. Waiting for current character name to become available.",
                    Py4GW.Console.MessageType.Info,
                )
                logged_name_wait = True
            yield from Routines.Yield.wait(500)
            continue

        last_name = current_name
        ConsoleLog(BOT_NAME, f"Loaded character detected: '{current_name}'.", Py4GW.Console.MessageType.Info)
        character_match = resolve_character_match(expected_name, [current_name])
        return character_match is not None, current_name

    return False, last_name


def reroll_character_for_crafting(target_character_name: str, timeout_ms: int = CRAFTING_REROLL_TIMEOUT_MS) -> bool:
    current_player_name = Player.GetName()
    if current_player_name and normalize_character_name(current_player_name) == normalize_character_name(target_character_name):
        ConsoleLog(
            BOT_NAME,
            f"Already logged in as crafter '{current_player_name}'. No character switch needed.",
            Py4GW.Console.MessageType.Info,
        )
        return True

    ActionQueueManager().ResetAllQueues()
    if not Map.Pregame.InCharacterSelectScreen():
        ConsoleLog(BOT_NAME, "Logging out to character select for crafting rotation.", Py4GW.Console.MessageType.Info)
        Map.Pregame.LogoutToCharacterSelect()
        if not (
            yield from wait_for_condition(
                Map.Pregame.InCharacterSelectScreen,
                timeout_ms=timeout_ms,
                step_ms=250,
            )
        ):
            ConsoleLog(
                BOT_NAME,
                "Timed out while waiting to reach the character select screen.",
                Py4GW.Console.MessageType.Error,
            )
            return False

    ConsoleLog(
        BOT_NAME,
        f"Waiting for character select list to populate for crafter '{target_character_name}'.",
        Py4GW.Console.MessageType.Info,
    )
    character_match = yield from wait_for_character_select_match(target_character_name)
    if character_match is None:
        ConsoleLog(
            BOT_NAME,
            f"Character '{target_character_name}' could not be matched uniquely in the character select list.",
            Py4GW.Console.MessageType.Error,
        )
        return False

    character_index, resolved_name, match_mode = character_match
    ConsoleLog(
        BOT_NAME,
        (
            f"Matched crafter '{target_character_name}' to '{resolved_name}' "
            f"at index {character_index} using {match_mode} matching."
        ),
        Py4GW.Console.MessageType.Info,
    )

    if not (
        yield from wait_for_condition(
            lambda: Map.Pregame.GetChosenCharacterIndex() >= 0,
            timeout_ms=3000,
            step_ms=100,
        )
    ):
        ConsoleLog(BOT_NAME, "Character select never reported a chosen character index.", Py4GW.Console.MessageType.Error)
        return False

    start_time = Utils.GetBaseTimestamp()
    current_index = Map.Pregame.GetChosenCharacterIndex()
    while current_index != character_index:
        if Utils.GetBaseTimestamp() - start_time > timeout_ms:
            ConsoleLog(
                BOT_NAME,
                f"Timed out while navigating to crafter '{resolved_name}' in character select.",
                Py4GW.Console.MessageType.Error,
            )
            log_character_match_debug(target_character_name, get_pregame_character_names(), get_available_character_names())
            return False

        direction_key = Key.RightArrow.value if character_index > current_index else Key.LeftArrow.value
        Keystroke.PressAndRelease(direction_key)
        yield from Routines.Yield.wait(250)
        current_index = Map.Pregame.GetChosenCharacterIndex()

    ConsoleLog(BOT_NAME, f"Selecting crafter '{resolved_name}'.", Py4GW.Console.MessageType.Info)
    Keystroke.PressAndRelease(Key.P.value)
    yield from Routines.Yield.wait(100)
    ConsoleLog(BOT_NAME, "Crafter character selected.", Py4GW.Console.MessageType.Info)

    if not (
        yield from wait_for_condition(
            lambda: not Map.Pregame.InCharacterSelectScreen(),
            timeout_ms=timeout_ms,
            step_ms=250,
        )
    ):
        ConsoleLog(
            BOT_NAME,
            f"Timed out waiting to leave character select after choosing '{resolved_name}'.",
            Py4GW.Console.MessageType.Error,
        )
        return False

    ConsoleLog(BOT_NAME, "Waiting for crafter map load.", Py4GW.Console.MessageType.Info)
    matched_loaded_character, active_name = yield from wait_for_loaded_character(
        resolved_name,
        timeout_ms=timeout_ms,
    )
    if not matched_loaded_character:
        ConsoleLog(
            BOT_NAME,
            (
                f"Character switch verification failed: expected '{resolved_name}', "
                f"but loaded '{active_name}'."
            ),
            Py4GW.Console.MessageType.Error,
        )
        return False

    ConsoleLog(
        BOT_NAME,
        f"Crafter verification succeeded with loaded character '{active_name}'.",
        Py4GW.Console.MessageType.Success,
    )
    ConsoleLog(BOT_NAME, f"Successfully switched to crafter '{active_name}'.", Py4GW.Console.MessageType.Success)
    return True


def travel_to_and_open_scroll_crafter() -> bool:
    if not Map.IsMapIDMatch(Map.GetMapID(), EMBARK_BEACH):
        ConsoleLog(BOT_NAME, "Traveling to Embark Beach for scroll crafting.", Py4GW.Console.MessageType.Info)
        if not (
            yield from Routines.Yield.Map.TravelToOutpost(
                EMBARK_BEACH,
                log=True,
                timeout=MAP_LOAD_TIMEOUT_MS,
            )
        ):
            ConsoleLog(BOT_NAME, "Failed to travel to Embark Beach.", Py4GW.Console.MessageType.Warning)
            return False

    return bool((yield from reach_and_interact_kwat()))


def deposit_scrolls_to_storage() -> None:
    deposited_scrolls = 0
    while True:
        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(SCROLL_OF_RESURRECTION_MODEL_ID)
        if item_id == 0:
            break
        GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
        deposited_scrolls += 1
        yield from Routines.Yield.wait(350)

    if deposited_scrolls > 0:
        ConsoleLog(
            BOT_NAME,
            f"Deposited {deposited_scrolls} Scroll of Resurrection stack(s) to storage.",
            Py4GW.Console.MessageType.Info,
        )
    remaining_scrolls = GLOBAL_CACHE.Inventory.GetModelCount(SCROLL_OF_RESURRECTION_MODEL_ID)
    if remaining_scrolls > 0:
        ConsoleLog(
            BOT_NAME,
            f"Scroll deposit finished, but {remaining_scrolls} Scroll(s) of Resurrection remain in inventory.",
            Py4GW.Console.MessageType.Warning,
        )
    else:
        ConsoleLog(BOT_NAME, "All crafted Scrolls of Resurrection were deposited to storage.", Py4GW.Console.MessageType.Success)


def withdraw_material_to_inventory_target(model_id: int, target_inventory_count: int, material_name: str) -> bool:
    current_inventory_count = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
    storage_before = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)
    ConsoleLog(
        BOT_NAME,
        f"{material_name} in inventory before withdrawal: {current_inventory_count}.",
        Py4GW.Console.MessageType.Info,
    )
    if current_inventory_count >= target_inventory_count:
        ConsoleLog(
            BOT_NAME,
            f"{material_name}: already carrying {current_inventory_count}, target is {target_inventory_count}.",
            Py4GW.Console.MessageType.Info,
        )
        ConsoleLog(BOT_NAME, f"{material_name} withdrawn from storage: 0.", Py4GW.Console.MessageType.Info)
        ConsoleLog(BOT_NAME, f"{material_name} in inventory after withdrawal: {current_inventory_count}.", Py4GW.Console.MessageType.Info)
        ConsoleLog(
            BOT_NAME,
            f"{material_name} remaining in storage after withdrawal: {storage_before}.",
            Py4GW.Console.MessageType.Info,
        )
        return True

    total_withdrawn = 0
    attempts = 0
    while attempts < MATERIAL_WITHDRAW_ATTEMPTS:
        current_inventory_count = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
        if current_inventory_count >= target_inventory_count:
            break

        storage_count = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)
        if storage_count <= 0:
            break

        needed = target_inventory_count - current_inventory_count
        withdraw_amount = min(needed, storage_count)
        if withdraw_amount <= 0:
            break

        before_inventory_count = current_inventory_count
        moved = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, withdraw_amount)
        yield from Routines.Yield.wait(350)
        after_inventory_count = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
        delta = max(0, after_inventory_count - before_inventory_count)
        total_withdrawn += delta
        attempts += 1

        if delta <= 0 and not moved:
            break

    final_inventory_count = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
    storage_after = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)
    ConsoleLog(
        BOT_NAME,
        f"{material_name} withdrawn from storage: {total_withdrawn}.",
        Py4GW.Console.MessageType.Info,
    )
    ConsoleLog(
        BOT_NAME,
        f"{material_name} in inventory after withdrawal: {final_inventory_count}.",
        Py4GW.Console.MessageType.Info,
    )
    ConsoleLog(
        BOT_NAME,
        f"{material_name} remaining in storage after withdrawal: {storage_after}.",
        Py4GW.Console.MessageType.Info,
    )
    return final_inventory_count >= target_inventory_count


def get_scroll_crafting_stop_reason() -> str:
    if GLOBAL_CACHE.Inventory.GetModelCount(PLANT_FIBER_MODEL_ID) < SCROLL_CRAFT_FIBER_COST:
        return "insufficient Fiber"
    if GLOBAL_CACHE.Inventory.GetModelCount(BONE_MODEL_ID) < SCROLL_CRAFT_BONE_COST:
        return "insufficient Bones"
    if Inventory.GetGoldOnCharacter() < SCROLL_CRAFT_GOLD_COST:
        return "insufficient gold"
    current_skill_points, _ = Player.GetSkillPointData()
    if current_skill_points < SCROLL_CRAFT_SKILL_POINTS_COST:
        return "insufficient skill points"
    if Inventory.GetFreeSlotCount() <= 0 and GLOBAL_CACHE.Inventory.GetFirstModelID(SCROLL_OF_RESURRECTION_MODEL_ID) == 0:
        return "insufficient inventory space"
    return "NPC interaction/crafting state"


def ensure_crafter_gold_reserve(min_gold: int = MIN_CRAFTING_GOLD_ON_CHARACTER) -> bool:
    gold_before = Inventory.GetGoldOnCharacter()
    storage_gold_before = Inventory.GetGoldInStorage()
    ConsoleLog(
        BOT_NAME,
        f"Crafter gold before withdrawal: {gold_before} on character, {storage_gold_before} in storage.",
        Py4GW.Console.MessageType.Info,
    )

    if gold_before >= min_gold:
        ConsoleLog(
            BOT_NAME,
            f"Crafter already has at least {min_gold} gold on character.",
            Py4GW.Console.MessageType.Info,
        )
        ConsoleLog(BOT_NAME, f"Crafter gold after withdrawal: {gold_before}.", Py4GW.Console.MessageType.Info)
        return True

    gold_needed = min_gold - gold_before
    if storage_gold_before < gold_needed:
        ConsoleLog(
            BOT_NAME,
            (
                f"Failed to reach {min_gold} gold on character: need {gold_needed} more gold, "
                f"but storage only has {storage_gold_before}."
            ),
            Py4GW.Console.MessageType.Warning,
        )
        return False

    yield from Routines.Yield.Items.WithdrawGold(min_gold, deposit_all=False, log=False)
    if not (
        yield from wait_for_condition(
            lambda: Inventory.GetGoldOnCharacter() >= min_gold,
            timeout_ms=3000,
            step_ms=100,
        )
    ):
        ConsoleLog(
            BOT_NAME,
            f"Timed out while withdrawing gold to reach {min_gold} on character.",
            Py4GW.Console.MessageType.Warning,
        )
        return False

    gold_after = Inventory.GetGoldOnCharacter()
    gold_withdrawn = max(0, gold_after - gold_before)
    ConsoleLog(BOT_NAME, f"Crafter gold withdrawn: {gold_withdrawn}.", Py4GW.Console.MessageType.Info)
    ConsoleLog(BOT_NAME, f"Crafter gold after withdrawal: {gold_after}.", Py4GW.Console.MessageType.Info)
    return gold_after >= min_gold


def switch_back_to_farmer_after_crafting(context_message: str) -> bool:
    farmer_name = runtime.farmer_character_name.strip()
    if not farmer_name:
        ConsoleLog(BOT_NAME, "No farmer character is recorded for the crafting rotation return path.", Py4GW.Console.MessageType.Warning)
        return False

    ConsoleLog(BOT_NAME, f"{context_message} -> switching back to farmer '{farmer_name}'.", Py4GW.Console.MessageType.Info)
    set_crafting_rotation_status("Switching back to farmer")
    if not (
        yield from reroll_character_for_crafting(
            farmer_name,
            timeout_ms=CRAFTING_REROLL_TIMEOUT_MS,
        )
    ):
        return False

    yield from Routines.Yield.wait(1000)
    ConsoleLog(BOT_NAME, f"Returned to farmer '{farmer_name}', resuming farm.", Py4GW.Console.MessageType.Success)
    return True


def reach_and_interact_kwat() -> bool:
    for attempt in range(1, KWAT_MAX_REACH_ATTEMPTS + 1):
        distance_to_kwat = Utils.Distance(Player.GetXY(), KWAT_NPC_COORD)
        ConsoleLog(
            BOT_NAME,
            f"Kwat attempt {attempt}/{KWAT_MAX_REACH_ATTEMPTS}: current distance is {distance_to_kwat:.1f}.",
            Py4GW.Console.MessageType.Info,
        )

        if distance_to_kwat > KWAT_CLOSE_ENOUGH_DISTANCE:
            moved = yield from follow_path(
                [KWAT_NPC_COORD],
                timeout=KWAT_MOVE_TIMEOUT_MS,
                tolerance=KWAT_CLOSE_ENOUGH_DISTANCE,
            )
            yield from Routines.Yield.wait(KWAT_RETRY_DELAY_MS)
            distance_to_kwat = Utils.Distance(Player.GetXY(), KWAT_NPC_COORD)
            if not moved and distance_to_kwat > KWAT_CLOSE_ENOUGH_DISTANCE:
                ConsoleLog(
                    BOT_NAME,
                    f"Kwat move attempt {attempt} reported failure; reissuing direct move.",
                    Py4GW.Console.MessageType.Warning,
                )
                Player.Move(KWAT_NPC_COORD[0], KWAT_NPC_COORD[1])
                yield from Routines.Yield.wait(KWAT_RETRY_DELAY_MS)
                distance_to_kwat = Utils.Distance(Player.GetXY(), KWAT_NPC_COORD)

        if distance_to_kwat <= KWAT_CLOSE_ENOUGH_DISTANCE:
            ConsoleLog(BOT_NAME, "Reached Kwat (close enough).", Py4GW.Console.MessageType.Info)

        interacted = yield from Routines.Yield.Agents.InteractWithAgentXY(
            KWAT_NPC_COORD[0],
            KWAT_NPC_COORD[1],
            timeout_ms=XUNLAI_INTERACT_TIMEOUT_MS,
            tolerance=XUNLAI_INTERACT_TOLERANCE,
        )
        if not interacted:
            yield from Routines.Yield.Agents.TargetAgentByName(KWAT_NPC_NAME, log=False)
            target_id = Player.GetTargetID()
            if target_id and Agent.IsValid(target_id):
                yield from Routines.Yield.Agents.InteractAgent(target_id, log=False)

        if (
            yield from wait_for_condition(
                has_scroll_of_resurrection_offer,
                timeout_ms=1500,
                step_ms=100,
            )
        ):
            ConsoleLog(BOT_NAME, f"Opened scroll crafter via {KWAT_NPC_NAME}.", Py4GW.Console.MessageType.Info)
            return True

        if attempt < KWAT_MAX_REACH_ATTEMPTS:
            ConsoleLog(BOT_NAME, "Kwat interaction did not open the crafter window yet; retrying.", Py4GW.Console.MessageType.Warning)
            yield from Routines.Yield.wait(KWAT_RETRY_DELAY_MS)

    ConsoleLog(BOT_NAME, f"Failed to interact with {KWAT_NPC_NAME} after {KWAT_MAX_REACH_ATTEMPTS} attempts.", Py4GW.Console.MessageType.Warning)
    return False


def run_scroll_crafting_rotation(bot_instance: Botting) -> bool:
    ensure_rotation_settings_loaded()
    crafter_name = rotation_settings.crafter_character.strip()
    if not crafter_name:
        ConsoleLog(BOT_NAME, "Crafting rotation is enabled, but no crafter character is configured.", Py4GW.Console.MessageType.Warning)
        return False

    farmer_name = Player.GetName()
    if farmer_name:
        runtime.farmer_character_name = farmer_name

    switched_characters = False
    switched_back_to_farmer = False
    set_crafting_rotation_status("Switching to crafter")
    try:
        if farmer_name and crafter_name != farmer_name:
            ConsoleLog(BOT_NAME, f"Switching from farmer '{farmer_name}' to crafter '{crafter_name}'.", Py4GW.Console.MessageType.Info)
            if not (
                yield from reroll_character_for_crafting(
                    crafter_name,
                    timeout_ms=CRAFTING_REROLL_TIMEOUT_MS,
                )
            ):
                return False
            switched_characters = True
            yield from Routines.Yield.wait(1000)
        elif Map.Pregame.InCharacterSelectScreen():
            if not (
                yield from reroll_character_for_crafting(
                    crafter_name,
                    timeout_ms=CRAFTING_REROLL_TIMEOUT_MS,
                )
            ):
                return False
            switched_characters = normalize_character_name(Player.GetName()) != normalize_character_name(farmer_name)
            yield from Routines.Yield.wait(1000)

        set_crafting_rotation_status("Preparing crafter materials")
        yield from Routines.Yield.Map.TravelToOutpost(MAATU_KEEP, log=True, timeout=MAP_LOAD_TIMEOUT_MS)
        if not (yield from interact_with_maatu_xunlai()):
            return False

        if not (yield from ensure_crafter_gold_reserve()):
            ConsoleLog(
                BOT_NAME,
                "Crafting rotation stopped because the crafter could not reach the 20,000 gold requirement.",
                Py4GW.Console.MessageType.Warning,
            )
            return False

        available_crafting_gold = min(
            Inventory.GetGoldOnCharacter() + Inventory.GetGoldInStorage(),
            MAX_CRAFTING_GOLD_ON_CHARACTER,
        )
        planned_scroll_count, target_fiber_inventory, target_bones_inventory = calculate_balanced_material_withdraw_targets(
            available_crafting_gold
        )
        if planned_scroll_count <= 0:
            ConsoleLog(
                BOT_NAME,
                "Crafting rotation triggered, but the crafter lacks enough Fiber, Bones, gold, or skill points to craft any scrolls.",
                Py4GW.Console.MessageType.Warning,
            )
            return False

        required_gold = planned_scroll_count * SCROLL_CRAFT_GOLD_COST

        if not (yield from ensure_crafter_gold_reserve(required_gold)):
            ConsoleLog(
                BOT_NAME,
                f"Crafting rotation stopped because the crafter could not reach the required {required_gold} gold for the planned batch.",
                Py4GW.Console.MessageType.Warning,
            )
            return False

        if not (
            yield from withdraw_material_to_inventory_target(
                PLANT_FIBER_MODEL_ID,
                target_fiber_inventory,
                "Fiber",
            )
        ):
            ConsoleLog(
                BOT_NAME,
                "Failed to withdraw the required Fiber for the crafting batch.",
                Py4GW.Console.MessageType.Warning,
            )
            return False
        if not (
            yield from withdraw_material_to_inventory_target(
                BONE_MODEL_ID,
                target_bones_inventory,
                "Bones",
            )
        ):
            ConsoleLog(
                BOT_NAME,
                "Failed to withdraw the required Bones for the crafting batch.",
                Py4GW.Console.MessageType.Warning,
            )
            return False

        craft_count = calculate_inventory_scroll_crafting_batch_count()
        ConsoleLog(BOT_NAME, f"Maximum craftable scroll count: {craft_count}.", Py4GW.Console.MessageType.Info)
        if craft_count <= 0:
            ConsoleLog(
                BOT_NAME,
                f"Crafting rotation stopped before Kwat because of {get_scroll_crafting_stop_reason()}.",
                Py4GW.Console.MessageType.Warning,
            )
            return False

        set_crafting_rotation_status("Opening scroll crafter")
        if not (yield from travel_to_and_open_scroll_crafter()):
            return False

        set_crafting_rotation_status("Crafting scrolls")
        crafted_count = 0
        stop_reason = ""
        max_craft_iterations = craft_count
        for _ in range(max_craft_iterations):
            remaining_craft_count = calculate_inventory_scroll_crafting_batch_count()
            if remaining_craft_count <= 0:
                stop_reason = get_scroll_crafting_stop_reason()
                break
            crafted = yield from Routines.Yield.Items.CraftItem(
                SCROLL_OF_RESURRECTION_MODEL_ID,
                SCROLL_CRAFT_GOLD_COST,
                [PLANT_FIBER_MODEL_ID, BONE_MODEL_ID],
                [SCROLL_CRAFT_FIBER_COST, SCROLL_CRAFT_BONE_COST],
            )
            if not crafted:
                stop_reason = "NPC interaction/crafting state"
                break
            crafted_count += 1
            ConsoleLog(
                BOT_NAME,
                f"Crafted Resurrection Scroll {crafted_count}/{max_craft_iterations}.",
                Py4GW.Console.MessageType.Info,
            )
            yield from Routines.Yield.wait(400)

        if crafted_count <= 0:
            ConsoleLog(
                BOT_NAME,
                f"No Scroll of Resurrection could be crafted. Stop reason: {stop_reason or get_scroll_crafting_stop_reason()}.",
                Py4GW.Console.MessageType.Warning,
            )
            return False

        if not stop_reason:
            stop_reason = get_scroll_crafting_stop_reason()

        ConsoleLog(
            BOT_NAME,
            f"Crafted {crafted_count} Scroll(s) of Resurrection from the Dragon Moss rotation batch.",
            Py4GW.Console.MessageType.Success,
        )
        ConsoleLog(BOT_NAME, f"Crafting stopped because of {stop_reason}.", Py4GW.Console.MessageType.Info)

        set_crafting_rotation_status("Depositing crafted scrolls")
        yield from Routines.Yield.Map.TravelToOutpost(MAATU_KEEP, log=True, timeout=MAP_LOAD_TIMEOUT_MS)
        if not (yield from interact_with_maatu_xunlai()):
            return False
        yield from deposit_scrolls_to_storage()

        if switched_characters and rotation_settings.switch_back_to_farmer and runtime.farmer_character_name:
            if not (yield from switch_back_to_farmer_after_crafting("Craft complete")):
                return False
            switched_back_to_farmer = True
        elif switched_characters and not rotation_settings.switch_back_to_farmer:
            ConsoleLog(
                BOT_NAME,
                "Crafting rotation finished on the crafter character. Stopping the bot because switch-back is disabled.",
                Py4GW.Console.MessageType.Info,
            )
            bot_instance.Stop()

        set_crafting_rotation_status("Idle")
        return True
    finally:
        if (
            switched_characters
            and rotation_settings.switch_back_to_farmer
            and runtime.farmer_character_name
            and not switched_back_to_farmer
            and normalize_character_name(Player.GetName()) != normalize_character_name(runtime.farmer_character_name)
        ):
            ConsoleLog(
                BOT_NAME,
                "Crafting rotation encountered an issue; attempting to return to the farmer before resuming farm.",
                Py4GW.Console.MessageType.Warning,
            )
            switched_back_to_farmer = yield from switch_back_to_farmer_after_crafting("Craft failure recovery")
        if runtime.crafting_rotation_status != "Idle" and not bot_instance.config.fsm_running:
            set_crafting_rotation_status("Idle")


def maybe_run_crafting_rotation(bot_instance: Botting):
    if not should_start_crafting_rotation():
        yield
        return

    ConsoleLog(
        BOT_NAME,
        (
            "Crafting rotation threshold reached. "
            f"Fiber={get_total_material_count(PLANT_FIBER_MODEL_ID)} / {rotation_settings.fiber_threshold}, "
            f"Bones={get_total_material_count(BONE_MODEL_ID)} / {rotation_settings.bones_threshold}."
        ),
        Py4GW.Console.MessageType.Info,
    )
    rotation_succeeded = yield from run_scroll_crafting_rotation(bot_instance)
    if not rotation_succeeded:
        farmer_restored = (
            bool(runtime.farmer_character_name)
            and normalize_character_name(Player.GetName()) == normalize_character_name(runtime.farmer_character_name)
        )
        if farmer_restored:
            ConsoleLog(
                BOT_NAME,
                "Crafting rotation failed, but the farmer was restored successfully. Resuming farm.",
                Py4GW.Console.MessageType.Warning,
            )
            set_crafting_rotation_status("Idle")
        else:
            ConsoleLog(
                BOT_NAME,
                "Crafting rotation failed and the farmer could not be restored safely. Stopping the bot to avoid a bad loop state.",
                Py4GW.Console.MessageType.Warning,
            )
            set_crafting_rotation_status("Failed")
            bot_instance.Stop()
    yield


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
    set_crafting_rotation_status("Idle")
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
    from Py4GWCoreLib import ImGui, Color

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
    PyImGui.bullet_text("Optional Dragon Root salvage and scroll crafting rotation")

    PyImGui.spacing()
    PyImGui.text_colored("Notes", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Built for unattended farming loops")
    PyImGui.bullet_text("Recovery / reset flow included")
    PyImGui.bullet_text("Loot filters can be extended if needed")
    PyImGui.bullet_text("Crafting rotation uses Scroll of Resurrection batches")

    PyImGui.spacing()
    PyImGui.text_colored("Credits", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by XLeek")

bot.UI.override_draw_config(draw_rotation_settings)
bot.UI.override_draw_help(tooltip)

def main():
    ensure_rotation_settings_loaded()
    advance_failure_recovery(bot)
    run_failure_watchdog(bot)
    bot.Update()
    bot.UI.draw_window()


if __name__ == "__main__":
    main()
