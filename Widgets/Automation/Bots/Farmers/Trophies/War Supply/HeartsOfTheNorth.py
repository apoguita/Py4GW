import PyImGui
from typing import Literal, Callable
from dataclasses import dataclass
import time

from Py4GW_widget_manager import get_widget_handler
from Py4GWCoreLib.Builds.Any.KeiranThackerayEOTN import KeiranThackerayEOTN
from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          Map, ImGui, IniManager, ActionQueueManager, Agent, Player, AgentArray,
                          Pathing, TitleID, TITLE_TIERS)
from Py4GWCoreLib import *

MODULE_NAME = "Hearts of the North - Keiran Missons (War Supplies)"
MODULE_ICON = "Textures\\Module_Icons\\Keiran Farm.png"
MODULE_TAGS = ["Automation", "Bots", "Farmers", "Trophies", "War Supply", "Keiran", "Missions", "EOTN", "HotN"]

@dataclass
class MissionConfig:
    name: str
    map_id: int
    dialog_id: int
    run_movement_fn: Callable  # fn(bot: Botting) -> adds mission-specific movement states


@dataclass
class MissionStats:
    successful_runs: int         = 0
    failed_runs: int             = 0
    total_run_time: float        = 0.0
    fastest_run: float           = float('inf')
    slowest_run: float           = 0.0

    @property
    def total_runs(self) -> int:
        return self.successful_runs + self.failed_runs

    def success_rate(self) -> str:
        if self.total_runs == 0:
            return "0.00%"
        return f"{self.successful_runs / self.total_runs * 100:.2f}%"

    def average_time(self) -> str:
        if self.successful_runs == 0:
            return "--:--"
        return _format_time(self.total_run_time / self.successful_runs)

    def fastest_time(self) -> str:
        return _format_time(self.fastest_run)

    def slowest_time(self) -> str:
        return _format_time(self.slowest_run)


class BotSettings:
    # Map/Outpost IDs
    EOTN_OUTPOST_ID = 642
    HOM_OUTPOST_ID = 646

    # Mission selection (set before starting the bot)
    SELECTED_MISSION: str = "Auspicious Beginnings"

    # Sequence mode
    SEQUENCE_MODE: bool = False
    SEQUENCE_INDEX: int = 0

    # Custom Bow ID - If this is left 0 you will automatically craft a suitable bow.
    CUSTOM_BOW_ID: int = 0

    # Gold threshold for deposit
    GOLD_THRESHOLD_DEPOSIT: int = 90000

    # Properties to enable/disable via setting tab
    WAR_SUPPLIES_ENABLED: bool = False

    # Runs counters
    TOTAL_RUNS: int = 0
    SUCCESSFUL_RUNS: int = 0
    FAILED_RUNS: int = 0

    # Material purchases
    ECTOS_BOUGHT: int = 0

    # Vanguard title cache (populated at start and after each successful run)
    VANGUARD_RANK: int = 0
    VANGUARD_TIER_NAME: str = "–"
    VANGUARD_POINTS: int = 0

    # Run timing
    CURRENT_RUN_START_TIME: float = 0.0
    TOTAL_RUN_TIME: float = 0.0
    FASTEST_RUN: float = float('inf')
    SLOWEST_RUN: float = 0.0

    # Per-mission stats (populated after MISSIONS dict is defined)
    MISSION_STATS: dict = None  # type: ignore[assignment]

    # Misc
    DEBUG: bool = False

    # UI
    SHOW_HELP: bool = True



# Module-level UI state (not persisted)
_reset_confirm:               bool            = False
_settings_ini:                IniHandler|None = None
_settings_ini_account_email:  str             = ""
_save_requested:              bool            = False

# ---------------------------------------------------------------------------
# Per-mission movement routines
# ---------------------------------------------------------------------------

def _run_ab_movement(bot: Botting) -> None:
    bot.Wait.ForMapLoad(849)
    bot.Move.XY(11714,-4590)
    bot.Wait.UntilOnCombat()
    bot.Move.XY(9973,-6394)
    bot.Move.XY(8448,-8676)
    bot.Move.XY(4284,-7384)
    bot.Move.XY(2442,-9532)
    bot.Move.XY(948,-11427)
    bot.Move.XY(-1605,-11181)
    bot.Move.XY(-2279,-9099)
    bot.Move.XY(-5688,-10252)
    bot.Move.XY(-9311,-8500)
    bot.Move.XY(-12904,-7805)
    bot.Move.XY(-15338,-8893)
    bot.Wait.UntilOnCombat()
    bot.Move.XY(-17952,-8940)

def _run_avob_movement(bot: Botting) -> None:
    bot.Properties.Disable("auto_combat")
    bot.Move.XY(15827,3742)
    bot.Move.XY(17666,5247)
    bot.Properties.Enable("auto_combat")
    bot.Move.XY(15484,3559)
    bot.Move.XY(16680,360)
    bot.Move.XY(15511,-2017)
    bot.Move.XY(10577,-1307)
    bot.Move.XY(9088,-3635)
    bot.Move.XY(7230,-2052)
    bot.Move.XY(6990,2470)
    bot.Move.XY(5819,4335)
    bot.Move.XY(2972,2707)
    bot.Move.XY(903,345)
    bot.Move.XY(-4050,-1905)
    bot.Move.XY(-7441,-2538)
    bot.Move.XY(-11014,-744)
    bot.Move.XY(-14120,1656)
    bot.Move.XY(-16702,-202)
    bot.Move.XY(-20921,418)
    bot.Wait.UntilOnCombat()
    bot.Move.XY(-22694,1015)

def _run_sitj_movement(bot: Botting) -> None:
    bot.Move.XY(-8661,-4032)
    bot.Move.XY(-6092,-4463)
    bot.Move.XY(-3489,-1162)
    bot.Move.XY(-2386,3966)
    bot.Move.XY(-6606,8215)
    bot.Move.XY(-4914,11700)
    bot.Move.XY(-65,12308)
    bot.Properties.Disable("auto_combat")
    bot.Move.XY(1165,10230)
    bot.Properties.Enable("auto_combat")
    bot.Move.XY(4549,10181)
    bot.Move.XY(7136,6288)
    bot.Move.XY(6073,3836)
    bot.Move.XY(7478,2800)
    bot.Move.XY(10116,4081)
    bot.Move.XY(12126,2201)
    bot.Move.XYAndInteractNPC(12047, 380)

def _run_rise_movement(bot: Botting) -> None:
    bot.Move.XY(21501.29, -11654.24, "First Group")
    bot.Wait.UntilOnCombat()
    bot.Move.XY(17606.40, -10386.07, "Second Group")
    bot.Wait.UntilOnCombat()
    bot.Move.XY(21501.29, -11654.24, "Third Group")
    bot.Wait.UntilOnCombat()
    bot.Move.XY(18833.73, -10746.32, "Fourth Group")
    bot.Wait.UntilOnCombat()
    bot.Move.XY(21501.29, -11654.24, "Fifth Group")
    bot.Wait.UntilOnCombat()
    bot.Move.XY(19678.33, -11051.54, "Sixth Group")
    bot.Wait.UntilOnCombat()
    bot.Move.XY(21501.29, -11654.24, "Seventh Group")
    bot.Wait.UntilOnCombat()
    bot.Move.XY(18833.73, -10746.32, "Eighth Group")
    bot.Wait.UntilOnCombat()

# ---------------------------------------------------------------------------
# Mission registry
# ---------------------------------------------------------------------------

MISSIONS: dict[str, MissionConfig] = {
    "Auspicious Beginnings": MissionConfig(
        name="Auspicious Beginnings",
        map_id=849,
        dialog_id=0x63F,
        run_movement_fn=_run_ab_movement,
    ),
    "A Vengance of Blades - WIP": MissionConfig(
        name="A Vengance of Blades - WIP",
        map_id=848,
        dialog_id=0x640,
        run_movement_fn=_run_avob_movement,
    ),
    "Shadows in the Jungle - WIP": MissionConfig(
        name="Shadows in the Jungle - WIP",
        map_id=847,
        dialog_id=0x641,
        run_movement_fn=_run_sitj_movement,
    ),
    "Rise - WIP": MissionConfig(
        name="Rise - WIP",
        map_id=846,
        dialog_id=0x642,
        run_movement_fn=_run_rise_movement,
    ),
}

MISSION_NAMES = list(MISSIONS.keys())

# Per-mission stats storage and short INI key prefixes
BotSettings.MISSION_STATS = {name: MissionStats() for name in MISSION_NAMES}
_MISSION_INI_PREFIX: dict[str, str] = {
    "Auspicious Beginnings":       "ab",
    "A Vengance of Blades - WIP":  "avob",
    "Shadows in the Jungle - WIP": "sitj",
    "Rise - WIP":                  "rise",
}

_MISSION_COL_LABEL: dict[str, str] = {
    "Auspicious Beginnings":       "AB",
    "A Vengance of Blades - WIP":  "AVoB",
    "Shadows in the Jungle - WIP": "SinJ",
    "Rise - WIP":                  "Rise",
}

# Fixed order for sequence mode: AB → AVoB → SitJ → Rise
SEQUENCE_ORDER: list[str] = [
    "Auspicious Beginnings",
    "A Vengance of Blades - WIP",
    "Shadows in the Jungle - WIP",
    "Rise - WIP",
]

# Gate state names used by the runtime dispatcher in RunQuest
_MISSION_GATE_NAMES: dict[str, str] = {
    "Auspicious Beginnings":       "GateAB",
    "A Vengance of Blades - WIP":  "GateAVoB",
    "Shadows in the Jungle - WIP": "GateSitJ",
    "Rise - WIP":                  "GateRise",
}


def _get_active_mission() -> MissionConfig:
    """Returns the mission to run this iteration (sequence-aware)."""
    if BotSettings.SEQUENCE_MODE:
        return MISSIONS[SEQUENCE_ORDER[BotSettings.SEQUENCE_INDEX]]
    return MISSIONS[BotSettings.SELECTED_MISSION]


def _advance_sequence() -> None:
    """Advance to the next mission in the sequence (wraps around)."""
    BotSettings.SEQUENCE_INDEX = (BotSettings.SEQUENCE_INDEX + 1) % len(SEQUENCE_ORDER)
    BotSettings.SELECTED_MISSION = SEQUENCE_ORDER[BotSettings.SEQUENCE_INDEX]
    if BotSettings.DEBUG:
        print(f"[DEBUG] Sequence advanced to: {BotSettings.SELECTED_MISSION}")


# ---------------------------------------------------------------------------
# Bot setup
# ---------------------------------------------------------------------------

_keiran_build = KeiranThackerayEOTN(debug_fn=lambda: BotSettings.DEBUG)
bot = Botting("Hearts of the North", custom_build=_keiran_build)
_keiran_build.set_fsm(bot.config.FSM)
bot.config.reset_pause_on_danger_fn(aggro_area=Range.Longbow)


def create_bot_routine(bot: Botting) -> None:
    widget_handler = get_widget_handler()
    if not widget_handler.is_widget_enabled("Return to outpost on defeat"):
        widget_handler.enable_widget("Return to outpost on defeat")

    InitializeBot(bot)
    def _initial_vanguard_scan():
        _update_vanguard_cache()
        yield
    bot.States.AddCustomState(lambda: _initial_vanguard_scan(), "ScanVanguardRank")
    GoToEOTN(bot)
    GetBonusBow(bot)
    QuestLoopEntry(bot)


def QuestLoopEntry(bot: Botting) -> None:
    """Main quest loop: checks gold, deposits if needed, then runs the selected mission."""
    CheckAndDepositGold(bot)
    ExitToHOM(bot)
    PrepareForQuest(bot)
    EnterQuest(bot)
    RunQuest(bot)


# ---------------------------------------------------------------------------
# Death handling
# ---------------------------------------------------------------------------

def _on_death(bot: "Botting"):
    _increment_runs_counters(bot, "fail")
    bot.Properties.ApplyNow("pause_on_danger", "active", False)
    bot.Properties.ApplyNow("halt_on_death", "active", True)
    bot.Properties.ApplyNow("movement_timeout", "value", 15000)
    bot.Properties.ApplyNow("auto_combat", "active", False)
    yield from Routines.Yield.wait(8000)
    yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.HOM_OUTPOST_ID, timeout=30000)
    bot.Properties.ApplyNow("halt_on_death", "active", False)
    fsm = bot.config.FSM
    fsm.jump_to_state_by_name("[H]Prepare for Quest_5")
    fsm.resume()
    yield


def on_death(bot: "Botting"):
    print("Player is dead. Run Failed, Restarting...")
    ActionQueueManager().ResetAllQueues()
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnDeath", _on_death(bot))


# ---------------------------------------------------------------------------
# Combat templates
# ---------------------------------------------------------------------------

def _enable_combat(bot: Botting) -> None:
    bot.OverrideBuild(KeiranThackerayEOTN(fsm=bot.config.FSM, debug_fn=lambda: BotSettings.DEBUG))
    bot.Templates.Aggressive(enable_imp=False)
def _disable_combat(bot: Botting) -> None:
    bot.Templates.Pacifist()


# ---------------------------------------------------------------------------
# Shared bot states
# ---------------------------------------------------------------------------

def InitializeBot(bot: Botting) -> None:
    condition = lambda: on_death(bot)
    bot.Events.OnDeathCallback(condition)


def _load_navmesh_object(bot) -> None:
    """Schedule async navmesh load for the current map into AutoPathing's internal cache."""
    try:
        if AutoPathing().get_navmesh() is not None:
            return  # Already loaded for this map
    except Exception as e:
        Py4GW.Console.Log("Navmesh", f"Navmesh check failed: {e}", Py4GW.Console.MessageType.Warning)
    def _load_coro():
        yield from AutoPathing().load_pathing_maps()
    GLOBAL_CACHE.Coroutines.append(_load_coro())


def GoToEOTN(bot: Botting) -> None:
    bot.States.AddHeader("Go to EOTN")

    def _go_to_eotn(bot: Botting):
        current_map = Map.GetMapID()
        should_skip_travel = current_map in [BotSettings.EOTN_OUTPOST_ID, BotSettings.HOM_OUTPOST_ID]
        if should_skip_travel:
            if BotSettings.DEBUG:
                print(f"[DEBUG] Already in EOTN or HOM, skipping travel")
            return

        Map.Travel(BotSettings.EOTN_OUTPOST_ID)
        yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.EOTN_OUTPOST_ID, timeout=15000)
        bot.Party.SetHardMode(False)

    bot.States.AddCustomState(lambda: _go_to_eotn(bot), "GoToEOTN")

def GetBonusBow(bot: Botting):
    bot.States.AddHeader("Check for Bonus Bow")

    def _bow_gate():
        if BotSettings.CUSTOM_BOW_ID != 0 or Routines.Checks.Inventory.IsModelInInventoryOrEquipped(11723):
            bot.config.FSM.jump_to_state_by_name("BowCraftEnd")
        yield

    bot.States.AddCustomState(_bow_gate, "BowCraftGate")
    bot.Map.Travel(194)
    bot.Move.XY(1592.00, -796.00)
    bot.Items.WithdrawGold(10000)
    bot.Move.XYAndInteractNPC(1592.00, -796.00)
    bot.States.AddCustomState(BuyLongbowMaterials, "Buy Weapon Materials")
    bot.Wait.ForTime(1500)
    bot.Move.XYAndInteractNPC(-1387.00, -3910.00)
    bot.Wait.ForTime(1000)
    bot.States.AddCustomState(lambda: DoCraftLongbow(bot), "Craft Weapons")
    bot.States.AddCustomState(_noop_gate, "BowCraftEnd")

_LONGBOW_DATA = {
    "buy":    [(ModelID.Wood_Plank.value, 10), (ModelID.Feather.value, 5)],
    "pieces": [(11723, [ModelID.Wood_Plank.value, ModelID.Feather.value], [100, 50])],
}

def BuyLongbowMaterials():
    for mat, count in _LONGBOW_DATA["buy"]:
        for _ in range(count):
            yield from Routines.Yield.Merchant.BuyMaterial(mat)

def DoCraftLongbow(bot: Botting):
    for weapon_id, mats, qtys in _LONGBOW_DATA["pieces"]:
        result = yield from Routines.Yield.Items.CraftItem(weapon_id, 5000, mats, qtys)
        if not result:
            ConsoleLog("DoCraftWeapon", f"Failed to craft weapon ({weapon_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield
        result = yield from Routines.Yield.Items.EquipItem(weapon_id)
        if not result:
            ConsoleLog("DoCraftWeapon", f"Failed to equip weapon ({weapon_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield
    return True


def CheckAndDepositGold(bot: Botting) -> None:
    """Check gold on character, deposit if needed."""
    bot.States.AddHeader("Check and Deposit Gold")

    def _check_and_deposit_gold(bot: Botting):
        current_map = Map.GetMapID()
        gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
        gold_in_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()

        if BotSettings.DEBUG:
            print(f"[DEBUG] CheckAndDepositGold: current_map={current_map}, gold={gold_on_char}, storage={gold_in_storage}")

        if gold_on_char > BotSettings.GOLD_THRESHOLD_DEPOSIT:
            if current_map != BotSettings.EOTN_OUTPOST_ID:
                if BotSettings.DEBUG:
                    print(f"[DEBUG] Traveling to EOTN from map {current_map}")
                Map.Travel(BotSettings.EOTN_OUTPOST_ID)
                yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.EOTN_OUTPOST_ID, timeout=15000)
                current_map = BotSettings.EOTN_OUTPOST_ID

            if gold_in_storage < 800000:
                if BotSettings.DEBUG:
                    print(f"Depositing {gold_on_char} gold in bank")
                GLOBAL_CACHE.Inventory.DepositGold(gold_on_char)
                yield from Routines.Yield.wait(1000)
            else:
                if BotSettings.DEBUG:
                    print(f"Storage ({gold_in_storage}) has reached 800k+, keeping gold on character for ecto purchases")
        else:
            if BotSettings.DEBUG:
                print(f"Gold ({gold_on_char}) below threshold ({BotSettings.GOLD_THRESHOLD_DEPOSIT}), skipping")

        current_map = Map.GetMapID()
        if current_map == BotSettings.EOTN_OUTPOST_ID:
            yield from BuyMaterials(bot)

        if BotSettings.DEBUG:
            print(f"[DEBUG] After gold check: current_map={current_map}, HOM={BotSettings.HOM_OUTPOST_ID}")

    bot.States.AddCustomState(lambda: _check_and_deposit_gold(bot), "CheckAndDepositGold")


def ExitToHOM(bot: Botting) -> None:
    bot.States.AddHeader("Exit to HOM")

    def _exit_to_hom(bot: Botting):
        current_map = Map.GetMapID()
        should_exit_to_hom = current_map != BotSettings.HOM_OUTPOST_ID
        should_travel_to_eotn = current_map != BotSettings.EOTN_OUTPOST_ID

        if should_exit_to_hom:
            if BotSettings.DEBUG:
                print(f"[DEBUG] Not in HOM, need to go there. Currently in map {current_map}")

            if should_travel_to_eotn:
                if BotSettings.DEBUG:
                    print(f"[DEBUG] Not in EOTN, traveling there first")
                Map.Travel(BotSettings.EOTN_OUTPOST_ID)
                yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.EOTN_OUTPOST_ID, timeout=15000)

            if BotSettings.DEBUG:
                print(f"[DEBUG] Moving to portal coordinates and exiting to HOM")

            yield from bot.Move._coro_xy_and_exit_map(-4873.00, 5284.00, target_map_id=BotSettings.HOM_OUTPOST_ID)
        else:
            if BotSettings.DEBUG:
                print(f"[DEBUG] Already in HOM, skipping travel")
        yield

    bot.States.AddCustomState(lambda: _exit_to_hom(bot), "ExitToHOM")

def PrepareForQuest(bot: Botting) -> None:
    """Prepare for quest in HOM: acquire and equip Keiran's Bow."""
    bot.States.AddHeader("Prepare for Quest")

    def _prepare_for_quest(bot: Botting):
        if not Routines.Checks.Inventory.IsModelInInventoryOrEquipped(ModelID.Keirans_Bow.value):
            yield from bot.Move._coro_xy_and_dialog(-6583.00, 6672.00, dialog_id=0x0000008A)

        if not Routines.Checks.Inventory.IsModelEquipped(ModelID.Keirans_Bow.value):
            yield from bot.helpers.Items._equip(ModelID.Keirans_Bow.value)

    bot.States.AddCustomState(lambda: _prepare_for_quest(bot), "PrepareForQuest")

def BuyMaterials(bot: Botting):
    """Buy Glob of Ectoplasm if gold conditions are met."""
    gold_in_inventory = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
    gold_in_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()

    if gold_in_inventory >= 90000 and gold_in_storage >= 800000:
        yield from bot.Move._coro_xy_and_dialog(-2079.00, 1046.00, dialog_id=0x00000001)

        for _ in range(100):
            current_gold = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
            if current_gold < 20000:
                if BotSettings.DEBUG:
                    print(f"[DEBUG] Stopping ecto purchases - gold ({current_gold}) below 20k")
                break
            yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Glob_Of_Ectoplasm.value)
            BotSettings.ECTOS_BOUGHT += 1
            yield from Routines.Yield.wait(500)


# ---------------------------------------------------------------------------
# Mission entry and run (mission-aware)
# ---------------------------------------------------------------------------

def _noop_gate():
    """Single-yield no-op used as a named gate state (avoids generator-lambda type errors)."""
    yield


def EnterQuest(bot: Botting) -> None:
    bot.States.AddHeader("Enter Quest")

    def _enter_quest(bot: Botting):
        mission = _get_active_mission()
        yield from bot.Move._coro_xy_and_dialog(-6662.00, 6584.00, dialog_id=mission.dialog_id)
        Py4GW.Console.Log("fail state", "I am after Dialog", Py4GW.Console.MessageType.Warning)

    bot.States.AddCustomState(lambda: _enter_quest(bot), "EnterQuest")

def _on_quest_success(bot: Botting) -> None:
    """Called at runtime after any mission completes successfully."""
    _increment_runs_counters(bot, "success")
    _update_vanguard_cache()
    if BotSettings.SEQUENCE_MODE:
        _advance_sequence()
    bot.config.FSM.jump_to_state_by_name("[H]Check and Deposit Gold_3")
    bot.config.FSM.resume()  # clear any stale pause left by the build (mirrors on_death pattern)

def RunQuest(bot: Botting) -> None:
    bot.States.AddHeader("Run Quest")

    def _start_run_timer():
        BotSettings.CURRENT_RUN_START_TIME = time.time()
        if BotSettings.DEBUG:
            print(f"[DEBUG] Started run timer at {BotSettings.CURRENT_RUN_START_TIME}")
        yield
    bot.States.AddCustomState(lambda: _start_run_timer(), "StartRunTimer")
    bot.States.AddCustomState(lambda: _load_navmesh_object(bot), "Navmesh Init")
    bot.States.AddCustomState(lambda: _handle_bonus_bow(bot), "HandleBonusBow")
    bot.States.AddCustomState(lambda: _handle_war_supplies(bot, BotSettings.WAR_SUPPLIES_ENABLED), "HandleWarSupplies")

    bot.Templates.Aggressive(enable_imp=False)

    def _fresh_build():
        bot.OverrideBuild(KeiranThackerayEOTN(fsm=bot.config.FSM, debug_fn=lambda: BotSettings.DEBUG))
        bot.Templates.Aggressive(enable_imp=False)  # re-arm combat template each run (Pacifist disables it at run end)
        yield
    bot.States.AddCustomState(_fresh_build, "FreshBuild")
    
    # Runtime dispatcher: jumps to the gate for the active mission
    def _dispatch(bot: Botting):
        gate = _MISSION_GATE_NAMES[_get_active_mission().name]
        bot.config.FSM.jump_to_state_by_name(gate)
        yield
    bot.States.AddCustomState(lambda: _dispatch(bot), "MissionDispatcher")

    # Shared success handler (defined once, reused by each section)
    def _mission_success(bot: Botting): 
        _disable_combat(bot)
        _on_quest_success(bot)
        yield

    # ---- Auspicious Beginnings ----
    bot.States.AddHeader("Auspicious Beginnings")
    bot.States.AddCustomState(_noop_gate, "GateAB")
    _run_ab_movement(bot)
    bot.Wait.ForMapLoad(target_map_id=BotSettings.HOM_OUTPOST_ID)
    bot.States.AddCustomState(lambda: _mission_success(bot), "AB_Success")

    # ---- A Vengance of Blades ----
    bot.States.AddHeader("Vengance")
    bot.States.AddCustomState(_noop_gate, "GateAVoB")
    _run_avob_movement(bot)
    bot.Wait.ForMapLoad(target_map_id=BotSettings.HOM_OUTPOST_ID)
    bot.States.AddCustomState(lambda: _mission_success(bot), "AVoB_Success")

    # ---- Shadows in the Jungle ----
    bot.States.AddHeader("Shadows")
    bot.States.AddCustomState(_noop_gate, "GateSitJ")
    _run_sitj_movement(bot)
    bot.Wait.ForMapLoad(target_map_id=BotSettings.HOM_OUTPOST_ID)
    bot.States.AddCustomState(lambda: _mission_success(bot), "SitJ_Success")

    # ---- Rise ----
    bot.States.AddHeader("Rise")
    bot.States.AddCustomState(_noop_gate, "GateRise")
    _run_rise_movement(bot)
    bot.Wait.ForMapLoad(target_map_id=BotSettings.HOM_OUTPOST_ID)
    bot.States.AddCustomState(lambda: _mission_success(bot), "Rise_Success")


# ---------------------------------------------------------------------------
# Runtime helpers
# ---------------------------------------------------------------------------

def _handle_bonus_bow(bot: Botting):
    bonus_bow_id = 11723

    if BotSettings.CUSTOM_BOW_ID != 0:
        bonus_bow_id = BotSettings.CUSTOM_BOW_ID
    has_bonus_bow = Routines.Checks.Inventory.IsModelInInventoryOrEquipped(bonus_bow_id)
    if has_bonus_bow:
        if BotSettings.DEBUG:
            print(f"[DEBUG] Bonus bow found, equipping")
        yield from bot.helpers.Items._equip(bonus_bow_id)
    else:
        if BotSettings.DEBUG:
            print(f"[DEBUG] Bonus bow not found in inventory or equipped")
    yield


def _handle_war_supplies(bot: Botting, value: bool):
    if BotSettings.DEBUG:
        print(f"[DEBUG] War supplies {'enabled' if value else 'disabled'}")
    bot.Properties.ApplyNow("war_supplies", "active", value)
    yield


def _ensure_ini_initialized() -> bool:
    """Lazy-initialize the per-account IniHandler using the account email as the directory.
    Returns True once the handler is ready."""
    global _settings_ini, _settings_ini_account_email
    import os as _os

    account_email = Player.GetAccountEmail()
    if not account_email:
        return False
    if account_email == _settings_ini_account_email and _settings_ini is not None:
        return True

    base_path = Py4GW.Console.get_projects_path()
    if not base_path:
        return False

    config_dir = _os.path.join(base_path, "Widgets", "Config", "Accounts", account_email)
    _os.makedirs(config_dir, exist_ok=True)
    ini_path = _os.path.join(config_dir, f"{bot.config.bot_name}.ini")
    _settings_ini = IniHandler(ini_path)
    _settings_ini_account_email = account_email

    # ── Load persisted settings ───────────────────────────────────────────────
    _S = "Settings"
    BotSettings.GOLD_THRESHOLD_DEPOSIT = _settings_ini.read_int( _S, "gold_threshold", BotSettings.GOLD_THRESHOLD_DEPOSIT)
    BotSettings.CUSTOM_BOW_ID          = _settings_ini.read_int( _S, "custom_bow_id",  BotSettings.CUSTOM_BOW_ID)
    BotSettings.WAR_SUPPLIES_ENABLED   = _settings_ini.read_bool(_S, "war_supplies",   BotSettings.WAR_SUPPLIES_ENABLED)
    BotSettings.DEBUG                  = _settings_ini.read_bool(_S, "debug",          BotSettings.DEBUG)
    BotSettings.SHOW_HELP              = _settings_ini.read_bool(_S, "show_help",      BotSettings.SHOW_HELP)

    # ── Load persisted statistics ─────────────────────────────────────────────
    _SS = "Statistics"
    BotSettings.TOTAL_RUNS      = _settings_ini.read_int(  _SS, "total_runs",      0)
    BotSettings.SUCCESSFUL_RUNS = _settings_ini.read_int(  _SS, "successful_runs", 0)
    BotSettings.FAILED_RUNS     = _settings_ini.read_int(  _SS, "failed_runs",     0)
    BotSettings.ECTOS_BOUGHT    = _settings_ini.read_int(  _SS, "ectos_bought",    0)
    BotSettings.TOTAL_RUN_TIME  = _settings_ini.read_float(_SS, "total_run_time",  0.0)
    _fastest = _settings_ini.read_float(_SS, "fastest_run", 0.0)
    BotSettings.FASTEST_RUN     = float('inf') if _fastest == 0.0 else _fastest
    BotSettings.SLOWEST_RUN     = _settings_ini.read_float(_SS, "slowest_run",     0.0)
    for _name, _ms in BotSettings.MISSION_STATS.items():
        _p = _MISSION_INI_PREFIX.get(_name, "")
        if not _p:
            continue
        _ms.successful_runs = _settings_ini.read_int(  _SS, f"{_p}_successful_runs", 0)
        _ms.failed_runs     = _settings_ini.read_int(  _SS, f"{_p}_failed_runs",     0)
        _ms.total_run_time  = _settings_ini.read_float(_SS, f"{_p}_total_run_time",  0.0)
        _f2 = _settings_ini.read_float(_SS, f"{_p}_fastest_run", 0.0)
        _ms.fastest_run     = float('inf') if _f2 == 0.0 else _f2
        _ms.slowest_run     = _settings_ini.read_float(_SS, f"{_p}_slowest_run",     0.0)

    _update_vanguard_cache()
    return True


def _write_settings() -> None:
    """Write all settings and statistics to the per-account INI if a save has been requested."""
    global _save_requested
    if not _save_requested or not _settings_ini:
        return

    _S  = "Settings"
    _settings_ini.write_key(_S, "gold_threshold", str(BotSettings.GOLD_THRESHOLD_DEPOSIT))
    _settings_ini.write_key(_S, "custom_bow_id",  str(BotSettings.CUSTOM_BOW_ID))
    _settings_ini.write_key(_S, "war_supplies",   str(BotSettings.WAR_SUPPLIES_ENABLED))
    _settings_ini.write_key(_S, "debug",          str(BotSettings.DEBUG))
    _settings_ini.write_key(_S, "show_help",      str(BotSettings.SHOW_HELP))

    _SS = "Statistics"
    _settings_ini.write_key(_SS, "total_runs",      str(BotSettings.TOTAL_RUNS))
    _settings_ini.write_key(_SS, "successful_runs", str(BotSettings.SUCCESSFUL_RUNS))
    _settings_ini.write_key(_SS, "failed_runs",     str(BotSettings.FAILED_RUNS))
    _settings_ini.write_key(_SS, "ectos_bought",    str(BotSettings.ECTOS_BOUGHT))
    _settings_ini.write_key(_SS, "total_run_time",  str(BotSettings.TOTAL_RUN_TIME))
    _fastest = 0.0 if BotSettings.FASTEST_RUN == float('inf') else BotSettings.FASTEST_RUN
    _settings_ini.write_key(_SS, "fastest_run",     str(_fastest))
    _settings_ini.write_key(_SS, "slowest_run",     str(BotSettings.SLOWEST_RUN))
    for name, ms in BotSettings.MISSION_STATS.items():
        p = _MISSION_INI_PREFIX.get(name, "")
        if not p:
            continue
        _settings_ini.write_key(_SS, f"{p}_successful_runs", str(ms.successful_runs))
        _settings_ini.write_key(_SS, f"{p}_failed_runs",     str(ms.failed_runs))
        _settings_ini.write_key(_SS, f"{p}_total_run_time",  str(ms.total_run_time))
        _f = 0.0 if ms.fastest_run == float('inf') else ms.fastest_run
        _settings_ini.write_key(_SS, f"{p}_fastest_run",     str(_f))
        _settings_ini.write_key(_SS, f"{p}_slowest_run",     str(ms.slowest_run))

    _save_requested = False


def _save_stats():
    global _save_requested
    _save_requested = True


def _reset_stats():
    BotSettings.TOTAL_RUNS      = 0
    BotSettings.SUCCESSFUL_RUNS = 0
    BotSettings.FAILED_RUNS     = 0
    BotSettings.ECTOS_BOUGHT    = 0
    BotSettings.TOTAL_RUN_TIME  = 0.0
    BotSettings.FASTEST_RUN     = float('inf')
    BotSettings.SLOWEST_RUN     = 0.0
    for name in BotSettings.MISSION_STATS:
        BotSettings.MISSION_STATS[name] = MissionStats()
    _save_stats()


def _increment_runs_counters(bot: Botting, result: Literal["success", "fail"]):
    ms = BotSettings.MISSION_STATS.get(BotSettings.SELECTED_MISSION)
    if BotSettings.CURRENT_RUN_START_TIME > 0:
        run_time = time.time() - BotSettings.CURRENT_RUN_START_TIME

        if result == "success":
            BotSettings.TOTAL_RUN_TIME += run_time
            if run_time < BotSettings.FASTEST_RUN:
                BotSettings.FASTEST_RUN = run_time
            if run_time > BotSettings.SLOWEST_RUN:
                BotSettings.SLOWEST_RUN = run_time
            if ms:
                ms.total_run_time += run_time
                if run_time < ms.fastest_run:
                    ms.fastest_run = run_time
                if run_time > ms.slowest_run:
                    ms.slowest_run = run_time

        if BotSettings.DEBUG:
            print(f"[DEBUG] Run completed in {run_time:.2f}s (result: {result})")

        BotSettings.CURRENT_RUN_START_TIME = 0.0
    BotSettings.TOTAL_RUNS += 1
    if result == "success":
        BotSettings.SUCCESSFUL_RUNS += 1
        if ms:
            ms.successful_runs += 1
    elif result == "fail":
        BotSettings.FAILED_RUNS += 1
        if ms:
            ms.failed_runs += 1
    _save_stats()


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------


def _get_vanguard_rank_info():
    tiers = TITLE_TIERS.get(TitleID.Ebon_Vanguard, [])
    title = Player.GetTitle(TitleID.Ebon_Vanguard)
    current_points = title.current_points if title is not None else 0

    current_rank = 0
    tier_name = "Unranked"
    for t in tiers:
        if current_points >= t.required:
            current_rank = t.tier
            tier_name = t.name
        else:
            break

    if current_rank >= len(tiers):
        return current_rank, tier_name, current_points, None

    next_required = tiers[current_rank].required
    return current_rank, tier_name, current_points, next_required


def _update_vanguard_cache():
    rank, tier_name, pts, _ = _get_vanguard_rank_info()
    BotSettings.VANGUARD_RANK = rank
    BotSettings.VANGUARD_TIER_NAME = tier_name
    BotSettings.VANGUARD_POINTS = pts



def _format_time(seconds: float) -> str:
    if seconds == float('inf') or seconds == 0.0:
        return "--:--"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"



def _current_run_time():
    # If the bot was stopped mid-run, clear the timer
    if not bot.config.fsm_running and BotSettings.CURRENT_RUN_START_TIME > 0:
        BotSettings.CURRENT_RUN_START_TIME = 0.0
    if BotSettings.CURRENT_RUN_START_TIME > 0:
        return _format_time(time.time() - BotSettings.CURRENT_RUN_START_TIME)
    return "--:--"


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

def _draw_mission_selector(width: int = 340) -> None:
    """
    Mission selector rendered as two rows of highlighted buttons.

    Row 1  ─ one button per mission (abbreviated label, full name as tooltip).
    Row 2  ─ full-width "All Missions (Sequence)" button.

    The active selection is highlighted with an amber tint.
    """
    # Abbreviated labels shown on the buttons (full names appear as tooltips)
    _SHORT_LABELS = ["Auspicious", "Blades - WIP", "Shadows - WIP", "Rise - WIP"]

    # Muted orange base for unselected option buttons
    OPT_BG  = (0.45, 0.26, 0.05, 1.0)
    OPT_HOV = (0.55, 0.33, 0.08, 1.0)
    OPT_ACT = (0.35, 0.20, 0.03, 1.0)

    # Green for the selected button; hover shifts to amber so it feels interactive
    SEL_BG  = (0.15, 0.50, 0.15, 1.0)
    SEL_HOV = (0.70, 0.40, 0.00, 1.0)
    SEL_ACT = (0.10, 0.38, 0.10, 1.0)

    # Resolve the active selection index
    if BotSettings.SEQUENCE_MODE:
        selected_idx = len(MISSION_NAMES)   # extra slot beyond missions = sequence
    else:
        selected_idx = MISSION_NAMES.index(BotSettings.SELECTED_MISSION)

    n        = len(MISSION_NAMES)
    gap      = 4                            # px between mission buttons
    btn_w    = max(1, (width - gap * (n - 1)) // n)
    btn_h    = 30

    # ── Row 1: individual mission buttons ────────────────────────────────────
    for i, (name, short) in enumerate(zip(MISSION_NAMES, _SHORT_LABELS)):
        is_sel = (selected_idx == i)
        bg, hov, act = (SEL_BG, SEL_HOV, SEL_ACT) if is_sel else (OPT_BG, OPT_HOV, OPT_ACT)

        PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        bg)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, hov)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  act)

        if PyImGui.button(f"{short}##m{i}", btn_w, btn_h):
            BotSettings.SELECTED_MISSION = name
            BotSettings.SEQUENCE_MODE    = False

        PyImGui.pop_style_color(3)

        if PyImGui.is_item_hovered():
            if PyImGui.begin_tooltip():
                PyImGui.text(name)
                PyImGui.end_tooltip()

        if i < n - 1:
            PyImGui.same_line(0, gap)

    # ── Row 2: full-width sequence button (disabled until sequence mode is ready) ──
    _DISABLED_BTN = (0.35, 0.35, 0.35, 1.0)
    _DISABLED_TXT = (0.55, 0.55, 0.55, 1.0)

    PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        _DISABLED_BTN)
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, _DISABLED_BTN)
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  _DISABLED_BTN)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text,          _DISABLED_TXT)

    PyImGui.button("All Missions (Sequence) - Coming Soon", width, btn_h)  # click ignored

    PyImGui.pop_style_color(4)

    # Current sequence position label (visible only in sequence mode)
    if BotSettings.SEQUENCE_MODE:
        seq_idx = BotSettings.SEQUENCE_INDEX
        PyImGui.text(f"  Current: {SEQUENCE_ORDER[seq_idx]} ({seq_idx + 1}/{len(SEQUENCE_ORDER)})")


_ROW_H = 26  # table row min-height — shared by table_next_row and centering helpers


def _vcenter() -> None:
    """Offset cursor Y to vertically centre text within the current row."""
    th = PyImGui.get_text_line_height()
    PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() + max(0.0, (_ROW_H - th) / 2))


def _ltext(label: str) -> None:
    """Render text left-justified and vertically centred within the current table cell."""
    _vcenter()
    PyImGui.text(label)


def _ctext(label: str) -> None:
    """Render text horizontally and vertically centred within the current table cell."""
    _vcenter()
    avail = PyImGui.get_content_region_avail()[0]
    tw    = PyImGui.calc_text_size(label)[0]
    PyImGui.set_cursor_pos_x(PyImGui.get_cursor_pos_x() + max(0.0, (avail - tw) / 2))
    PyImGui.text(label)


def _rtext(label: str) -> None:
    """Render text right-justified and vertically centred within the current table cell."""
    _vcenter()
    avail = PyImGui.get_content_region_avail()[0]
    tw    = PyImGui.calc_text_size(label)[0]
    PyImGui.set_cursor_pos_x(PyImGui.get_cursor_pos_x() + max(0.0, avail - tw))
    PyImGui.text(label)


def _draw_stats_tab():
    """Statistics tab content."""
    global _reset_confirm

    # ── Per-mission stats table ───────────────────────────────────────────────
    # Columns: label | mission 1 | mission 2 | mission 3 | mission 4
    _missions = list(BotSettings.MISSION_STATS.items())
    _ncols = 1 + len(_missions)

    _tflags = (PyImGui.TableFlags.Borders |
               PyImGui.TableFlags.RowBg   |
               PyImGui.TableFlags.SizingStretchSame)

    if PyImGui.begin_table("MissionStatsTable", _ncols, _tflags):
        PyImGui.table_setup_column("", PyImGui.TableColumnFlags.WidthFixed, 70)
        for _ in _missions:
            PyImGui.table_setup_column("")

        # ── Header row (manual, for centred labels) ───────────────────────────
        _hdr_color = 26 | (38 << 8) | (51 << 16) | (255 << 24)
        PyImGui.table_next_row(0, _ROW_H)
        PyImGui.table_set_bg_color(2, _hdr_color, -1)
        PyImGui.table_set_column_index(0)   # label column — leave blank
        for _i, (_mname, _ms) in enumerate(_missions, 1):
            PyImGui.table_set_column_index(_i)
            _ctext(_MISSION_COL_LABEL.get(_mname) or _mname)

        # ── Runs ──────────────────────────────────────────────────────────────
        PyImGui.table_next_row(0, _ROW_H)
        PyImGui.table_set_column_index(0); _ltext("Runs")
        for _i, (_, _ms) in enumerate(_missions, 1):
            PyImGui.table_set_column_index(_i)
            _rtext(str(_ms.total_runs))

        # ── Successful ────────────────────────────────────────────────────────
        PyImGui.table_next_row(0, _ROW_H)
        PyImGui.table_set_column_index(0); _ltext("Successful")
        for _i, (_, _ms) in enumerate(_missions, 1):
            PyImGui.table_set_column_index(_i)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.0, 1.0, 0.0, 1.0))
            _rtext(str(_ms.successful_runs))
            PyImGui.pop_style_color(1)

        # ── Failed ────────────────────────────────────────────────────────────
        PyImGui.table_next_row(0, _ROW_H)
        PyImGui.table_set_column_index(0); _ltext("Failed")
        for _i, (_, _ms) in enumerate(_missions, 1):
            PyImGui.table_set_column_index(_i)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 0.3, 0.3, 1.0))
            _rtext(str(_ms.failed_runs))
            PyImGui.pop_style_color(1)

        # ── Success % ─────────────────────────────────────────────────────────
        PyImGui.table_next_row(0, _ROW_H)
        PyImGui.table_set_column_index(0); _ltext("Success %")
        for _i, (_, _ms) in enumerate(_missions, 1):
            PyImGui.table_set_column_index(_i)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.0, 1.0, 0.0, 1.0))
            _rtext(_ms.success_rate())
            PyImGui.pop_style_color(1)

        # ── Avg Time ──────────────────────────────────────────────────────────
        PyImGui.table_next_row(0, _ROW_H)
        PyImGui.table_set_column_index(0); _ltext("Avg Time")
        for _i, (_, _ms) in enumerate(_missions, 1):
            PyImGui.table_set_column_index(_i)
            _rtext(_ms.average_time())

        # ── Fastest ───────────────────────────────────────────────────────────
        PyImGui.table_next_row(0, _ROW_H)
        PyImGui.table_set_column_index(0); _ltext("Fastest")
        for _i, (_, _ms) in enumerate(_missions, 1):
            PyImGui.table_set_column_index(_i)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.0, 1.0, 0.0, 1.0))
            _rtext(_ms.fastest_time())
            PyImGui.pop_style_color(1)

        # ── Slowest ───────────────────────────────────────────────────────────
        PyImGui.table_next_row(0, _ROW_H)
        PyImGui.table_set_column_index(0); _ltext("Slowest")
        for _i, (_, _ms) in enumerate(_missions, 1):
            PyImGui.table_set_column_index(_i)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 0.65, 0.0, 1.0))
            _rtext(_ms.slowest_time())
            PyImGui.pop_style_color(1)

        # ── Gold ──────────────────────────────────────────────────────────────
        PyImGui.table_next_row(0, _ROW_H)
        PyImGui.table_set_column_index(0); _ltext("Gold")
        for _i, (_, _ms) in enumerate(_missions, 1):
            PyImGui.table_set_column_index(_i)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 0.84, 0.0, 1.0))
            _rtext(f"{1000 * _ms.successful_runs:,}")
            PyImGui.pop_style_color(1)

        # ── War Supplies ──────────────────────────────────────────────────────
        PyImGui.table_next_row(0, _ROW_H)
        PyImGui.table_set_column_index(0); _ltext("War Supplies")
        for _i, (_, _ms) in enumerate(_missions, 1):
            PyImGui.table_set_column_index(_i)
            _rtext(str(5 * _ms.successful_runs))

        PyImGui.end_table()

    rank      = BotSettings.VANGUARD_RANK
    tier_name = BotSettings.VANGUARD_TIER_NAME
    pts       = BotSettings.VANGUARD_POINTS
    is_maxed  = rank >= 10
    _GOLD     = (1.0, 0.84, 0.0, 1.0)
    _vflags = (PyImGui.TableFlags.Borders |
               PyImGui.TableFlags.RowBg   |
               PyImGui.TableFlags.SizingStretchProp)
    if PyImGui.begin_table("VanguardTable", 2, _vflags):
        PyImGui.table_setup_column("", PyImGui.TableColumnFlags.WidthStretch, 0.4)
        PyImGui.table_setup_column("", PyImGui.TableColumnFlags.WidthStretch, 0.6)
        # ── Header row ────────────────────────────────────────────────────
        _hdr_color = 26 | (38 << 8) | (51 << 16) | (255 << 24)
        PyImGui.table_next_row(0, _ROW_H)
        PyImGui.table_set_bg_color(2, _hdr_color, -1)
        PyImGui.table_set_column_index(0); _ctext("Vanguard Rank")
        PyImGui.table_set_column_index(1); _ctext("Runs to Max")
        # ── Data row ──────────────────────────────────────────────────────
        PyImGui.table_next_row(0, _ROW_H)
        PyImGui.table_set_column_index(0)
        if is_maxed:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, _GOLD)
        rank_label = f"{rank} - {tier_name}" if rank > 0 else "Unranked"
        _ctext(rank_label)
        PyImGui.table_set_column_index(1)
        if is_maxed:
            _ctext("Title Maxed!")
            PyImGui.pop_style_color(1)
        else:
            remaining   = max(0, 160_000 - pts)
            runs_needed = (remaining + 1249) // 1250
            _ctext(str(runs_needed))
        PyImGui.end_table()

    PyImGui.separator()
    if PyImGui.collapsing_header("Reset"):
        _reset_confirm = PyImGui.checkbox("Confirm reset — this cannot be undone", _reset_confirm)
        _avail = PyImGui.get_content_region_avail()
        _reset_w = int(_avail[0]) if _avail[0] > 0 else 340
        if _reset_confirm:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        (0.55, 0.10, 0.10, 1.0))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.70, 0.15, 0.15, 1.0))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  (0.40, 0.07, 0.07, 1.0))
        else:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        (0.25, 0.25, 0.25, 1.0))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.25, 0.25, 0.25, 1.0))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  (0.25, 0.25, 0.25, 1.0))
        if PyImGui.button("Reset Statistics##ResetStats", _reset_w, 30):
            if _reset_confirm:
                _reset_stats()
                _reset_confirm = False
        PyImGui.pop_style_color(3)


def _draw_settings(bot: Botting):
    # Gold threshold controls
    gold_threshold = BotSettings.GOLD_THRESHOLD_DEPOSIT
    PyImGui.set_next_item_width(150)
    gold_threshold = PyImGui.input_int("Gold deposit threshold", gold_threshold)

    # Custom Bow ID
    custom_bow_id = BotSettings.CUSTOM_BOW_ID
    PyImGui.set_next_item_width(150)
    custom_bow_id = PyImGui.input_int("Custom Bow ID (0 = Craft Longbow)", custom_bow_id)

    # War Supplies controls
    use_war_supplies = BotSettings.WAR_SUPPLIES_ENABLED
    use_war_supplies = PyImGui.checkbox("Use War Supplies", use_war_supplies)

    # Debug controls
    debug = BotSettings.DEBUG
    debug = PyImGui.checkbox("Debug", debug)

    # Help tab visibility
    PyImGui.separator()
    show_help = BotSettings.SHOW_HELP
    show_help = PyImGui.checkbox("Show help tab", show_help)

    changed = (
        use_war_supplies != BotSettings.WAR_SUPPLIES_ENABLED   or
        custom_bow_id    != BotSettings.CUSTOM_BOW_ID          or
        gold_threshold   != BotSettings.GOLD_THRESHOLD_DEPOSIT or
        debug            != BotSettings.DEBUG                   or
        show_help        != BotSettings.SHOW_HELP
    )
    BotSettings.WAR_SUPPLIES_ENABLED   = use_war_supplies
    BotSettings.CUSTOM_BOW_ID         = custom_bow_id
    BotSettings.GOLD_THRESHOLD_DEPOSIT = gold_threshold
    BotSettings.DEBUG                  = debug
    BotSettings.SHOW_HELP             = show_help

    if changed:
        global _save_requested
        _save_requested = True


bot.SetMainRoutine(create_bot_routine)
bot.UI.override_draw_config(lambda: _draw_settings(bot))


def _draw_hotn_help() -> None:
    import PyImGui
    from Py4GWCoreLib import ImGui, Color, IconsFontAwesome5

    header_color = Color(255, 200, 100, 255)
    green_color  = Color(100, 220, 100, 255)
    red_color    = Color(220, 80,  80,  255)
    wip_color    = Color(220, 180, 60,  255)

    PyImGui.push_text_wrap_pos(PyImGui.get_cursor_pos_x() + 380.0)

    # ── Title ─────────────────────────────────────────────────────────────────
    PyImGui.spacing()
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Hearts of the North - Bot Help", header_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.separator()
    PyImGui.spacing()
    PyImGui.text_wrapped("Welcome to the complete Hearts of the North farming bot. This bot is still in development. As additional missions have been mapped they will be added. Expect issues with WIP missions, but feel free to test.")
    PyImGui.text_colored("Features", header_color.to_tuple_normalized())
    PyImGui.bullet_text("Access to all four Keiran missions.")
    PyImGui.bullet_text("Useable by any class, any specialization, any gear.")
    PyImGui.bullet_text("Capable of setting a custom weapon in Settings")
    PyImGui.bullet_text("Automatically crafts suitable longbow otherwise.")
    PyImGui.bullet_text("Advanced statistics to track lifetime stats.")
    PyImGui.spacing()

    # ── Requirements ──────────────────────────────────────────────────────────
    if PyImGui.collapsing_header("Currently Working Missions"):
        PyImGui.indent(10)
        PyImGui.text_colored(IconsFontAwesome5.ICON_CHECK         + "  Auspicious Beginnings",    green_color.to_tuple_normalized())
        PyImGui.text_colored(IconsFontAwesome5.ICON_ARROWS_ROTATE + "  A Vengance of Blades",     wip_color.to_tuple_normalized())
        PyImGui.text_colored(IconsFontAwesome5.ICON_ARROWS_ROTATE + "  Shadows in the Jungle",    wip_color.to_tuple_normalized())
        PyImGui.text_colored(IconsFontAwesome5.ICON_ARROWS_ROTATE + "  Rise",                     wip_color.to_tuple_normalized())
        PyImGui.text_colored(IconsFontAwesome5.ICON_TIMES         + "  All Missions in Sequence", red_color.to_tuple_normalized())
        PyImGui.unindent(10)
        PyImGui.spacing()

    # ── Quest Phases ──────────────────────────────────────────────────────────
    if PyImGui.collapsing_header("Optimized Farming"):
        PyImGui.spacing()
        PyImGui.text_wrapped("General Notes")
        PyImGui.bullet_text("Any modifications to Health or Mana are completely ignored.")
        PyImGui.bullet_text("Attunement/Survivor/Radiant/Vigor/Vitae are useless.")
        PyImGui.bullet_text("Focus on upgrades that give bonus armor.")
        PyImGui.bullet_text("All classes have a minimum of 70 armor for these missions.")
        PyImGui.bullet_text("Classes with 80 armor will have 80 armor.")
        PyImGui.spacing()
        PyImGui.text_wrapped("Best Classes")
        PyImGui.bullet_text("Paragon - 80 Armor")
        PyImGui.bullet_text("Warrior - 80 Armor")
        PyImGui.spacing()
        PyImGui.text_wrapped("Best Runes")
        PyImGui.bullet_text("Paragon - Centurion")
        PyImGui.bullet_text("Warrior - Knight's/Dreadnought")
        PyImGui.bullet_text("General - Stalwart/Brawler's")
        PyImGui.spacing()
        PyImGui.text_wrapped("Best Runes")
        PyImGui.bullet_text("Clarity")
        PyImGui.bullet_text("Purity")
        PyImGui.bullet_text("Recovery")
        PyImGui.bullet_text("Restoration")
        PyImGui.bullet_text("Absorption - if Warrior")
        PyImGui.spacing()
        PyImGui.text_wrapped("Best Weapons")
        PyImGui.bullet_text("Base: Max Damage Longbow/Flatbow")
        PyImGui.bullet_text("Inscription: 15% ^ 50 or 15% -5e")
        PyImGui.bullet_text("Prefix: Vampiric/Sundering.")
        PyImGui.bullet_text("Vamp will always do more damage, but Sunder may be safer.")
        PyImGui.bullet_text("Suffix: Defence/Shelter/Warding")
        PyImGui.bullet_text("Anniversary Suffixes do not work, as far as I know")
        PyImGui.spacing()

    # ── Known Issues / Tips ───────────────────────────────────────────────────
    if PyImGui.collapsing_header("Tips & Known Issues"):
        PyImGui.bullet_text("TODO: Add tips and known quirks here.")
        PyImGui.spacing()

    # ── Close button (centered, bottom) ───────────────────────────────────────
    PyImGui.separator()
    PyImGui.spacing()
    btn_label = "Close Help"
    btn_text_w, _ = PyImGui.calc_text_size(btn_label)
    btn_w = btn_text_w + 16.0
    avail_w = PyImGui.get_content_region_avail()[0]
    PyImGui.set_cursor_pos_x(PyImGui.get_cursor_pos_x() + (avail_w - btn_w) * 0.5)
    if PyImGui.button(btn_label):
        BotSettings.SHOW_HELP = False
        global _save_requested
        _save_requested = True
    PyImGui.spacing()
    PyImGui.pop_text_wrap_pos()


bot.UI.override_draw_help(_draw_hotn_help)


def _draw_hotn_window(icon_path: str) -> None:
    """
    Fully custom window for Hearts of the North.

    Layout of the Main tab child (top → bottom):
        Header table  (icon | bot-name / step / status)
        ───────────────────────────────────────────────
        ▶ Start / ■ Stop  button
        ═══════════════════════════════════════════════  ← thin separator
        Mission selector  (sequence checkbox + combo)
        ───────────────────────────────────────────────
        Overall Progress  [████░░░░]
        Step Progress     [██░░░░░░]
    """
    from Py4GWCoreLib import ImGui, IniManager, Color, Routines
    from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
    from Py4GWCoreLib.Py4GWcorelib import ConsoleLog, Console
    from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE

    WINDOW_W = 420
    CHILD_W,  CHILD_H  = 410, 400
    ICON_W             = 96

    # ── Window state INI (position/size) ─────────────────────────────────────
    if not bot.config.ini_key_initialized:
        bot.config.ini_key = IniManager().ensure_key(
            f"BottingClass/bot_{bot.config.bot_name}",
            f"bot_{bot.config.bot_name}.ini",
        )
        if bot.config.ini_key:
            IniManager().load_once(bot.config.ini_key)
        bot.config.ini_key_initialized = True

    if not bot.config.ini_key:
        return

    # ── Per-account settings/statistics INI (lazy, requires account email) ───
    _ensure_ini_initialized()
    _write_settings()

    # ── Outer window ─────────────────────────────────────────────────────────
    if ImGui.Begin(
        ini_key=bot.config.ini_key,
        name=bot.config.bot_name,
        p_open=True,
        flags=PyImGui.WindowFlags.AlwaysAutoResize,
    ):
        if PyImGui.begin_tab_bar(bot.config.bot_name + "_tabs"):

            # ── Help tab ──────────────────────────────────────────────────────
            if BotSettings.SHOW_HELP and PyImGui.begin_tab_item("Help"):
                bot.UI._draw_help_child()
                PyImGui.dummy(WINDOW_W, 0)
                PyImGui.end_tab_item()

            # ── Main tab ─────────────────────────────────────────────────────
            if PyImGui.begin_tab_item("Main"):
                PyImGui.dummy(WINDOW_W, 0)
                _avail = PyImGui.get_content_region_avail()
                inner_w = int(_avail[0]) if _avail[0] > 0 else (CHILD_W - 10)

                # ── Header table ──────────────────────────────────────────────
                (current_header_step, header_for_current,
                 current_step, total_steps, step_name, finished) = bot.UI._find_current_header_step()

                if PyImGui.begin_table(
                    "bot_header_table", 2,
                    PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersOuterH,
                ):
                    PyImGui.table_setup_column("Icon",   PyImGui.TableColumnFlags.WidthFixed,   ICON_W)
                    PyImGui.table_setup_column("titles", PyImGui.TableColumnFlags.WidthStretch)
                    PyImGui.table_next_row()

                    PyImGui.table_set_column_index(0)
                    bot.UI._draw_texture(texture_path=icon_path, size=(ICON_W, ICON_W))

                    PyImGui.table_set_column_index(1)
                    PyImGui.dummy(0, 3)
                    ImGui.push_font("Regular", 22)
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Color(255, 255, 0, 255).to_tuple_normalized())
                    PyImGui.text(bot.config.bot_name)
                    PyImGui.pop_style_color(1)
                    ImGui.pop_font()

                    # ── Active mission label ───────────────────────────────────
                    _active_label = "All Missions (Sequence)" if BotSettings.SEQUENCE_MODE else BotSettings.SELECTED_MISSION
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.65, 0.85, 1.0, 1.0))
                    PyImGui.text(_active_label)
                    PyImGui.pop_style_color(1)

                    ImGui.push_font("Bold", 18)
                    PyImGui.text(f"[{max(current_header_step, 0)}] {header_for_current or 'Not started'}")
                    ImGui.pop_font()

                    if total_steps <= 0:
                        PyImGui.text("Step: —/— - (No steps)")
                    elif finished:
                        PyImGui.text(f"Step: {total_steps-1}/{total_steps-1} - (Finished)")
                    else:
                        PyImGui.text(f"Step: {current_step}/{max(total_steps-1, 0)} - {step_name or '(…?)'}")

                    if not bot.config.fsm_running and finished:
                        bot.config.state_description = "Finished"
                    PyImGui.text(f"Status: {bot.config.state_description}")
                    # ── Current run timer + mission average ──────────────────────
                    _ms_active = BotSettings.MISSION_STATS.get(BotSettings.SELECTED_MISSION)
                    _avg = _ms_active.average_time() if _ms_active else "--:--"
                    if BotSettings.CURRENT_RUN_START_TIME > 0:
                        spinner_chars = ['|', '/', '-', '\\']
                        spinner_idx = int(time.time() * 4) % len(spinner_chars)
                        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.4, 0.8, 1.0, 1.0))
                        PyImGui.text(f"Run: {_current_run_time()} {spinner_chars[spinner_idx]}  |  Avg: {_avg}")
                        PyImGui.pop_style_color(1)
                    else:
                        PyImGui.text(f"Run: --:--  |  Avg: {_avg}")
                    PyImGui.end_table()

                # ── Mission selector ───────────────────────────────────────────
                #PyImGui.separator()
                _draw_mission_selector(inner_w)

                # ── Start / Stop button ────────────────────────────────────────
                PyImGui.separator()
                btn_icon   = IconsFontAwesome5.ICON_STOP_CIRCLE if bot.config.fsm_running else IconsFontAwesome5.ICON_PLAY_CIRCLE
                btn_legend = "  Stop" if bot.config.fsm_running else "  Start"
                if PyImGui.button(btn_icon + btn_legend + "##BotToggle", inner_w, 40):
                    if bot.config.fsm_running:
                        bot.config.fsm_running = False
                        ConsoleLog(bot.config.bot_name, "Script stopped", Console.MessageType.Info)
                        bot.config.state_description = "Idle"
                        bot.config.FSM.stop()
                        GLOBAL_CACHE.Coroutines.clear()
                    else:
                        bot.config.fsm_running = True
                        ConsoleLog(bot.config.bot_name, "Script started", Console.MessageType.Info)
                        bot.config.state_description = "Running"
                        bot.config.FSM.restart()

                # ── Progress bars ──────────────────────────────────────────────
                if total_steps > 1:
                    fraction = current_step / float(total_steps - 1)
                else:
                    fraction = 1.0 if (finished and total_steps == 1) else 0.0
                if finished and total_steps > 0:
                    fraction = 1.0
                fraction = max(0.0, min(1.0, fraction))

                PyImGui.separator()
                PyImGui.text("Overall Progress")
                PyImGui.progress_bar(fraction, inner_w, 0, f"{fraction * 100:.2f}%")

                PyImGui.separator()
                PyImGui.text("Step Progress")
                PyImGui.progress_bar(bot.config.state_percentage, inner_w, 0, f"{bot.config.state_percentage * 100:.2f}%")

                PyImGui.end_tab_item()

            # ── Navigation tab ────────────────────────────────────────────────
            if PyImGui.begin_tab_item("Navigation"):
                PyImGui.dummy(WINDOW_W, 0)
                PyImGui.text("Jump to step (filtered by step index):")
                bot.UI._draw_fsm_jump_button()
                PyImGui.separator()
                bot.UI.draw_fsm_tree_selector_ranged(child_size=(CHILD_W, CHILD_H))
                PyImGui.end_tab_item()

            # ── Settings tab ──────────────────────────────────────────────────
            if PyImGui.begin_tab_item("Settings"):
                bot.UI._draw_settings_child()
                PyImGui.dummy(WINDOW_W, 0)
                PyImGui.end_tab_item()

            # ── Debug tab ─────────────────────────────────────────────────────
            if PyImGui.begin_tab_item("Debug"):
                bot.UI.draw_debug_window()
                PyImGui.dummy(WINDOW_W, 0)
                PyImGui.end_tab_item()

            # ── Statistics tab ────────────────────────────────────────────────
            if PyImGui.begin_tab_item("Statistics"):
                _draw_stats_tab()                
                PyImGui.dummy(WINDOW_W, 0)
                PyImGui.end_tab_item()

            PyImGui.end_tab_bar()

    ImGui.End(bot.config.ini_key)


def main():
    try:
        projects_path = Py4GW.Console.get_projects_path()
        full_path = projects_path + "\\Sources\\ApoSource\\textures\\"

        bot.Update()
        _draw_hotn_window(full_path + "Keiran_art.png")

    except Exception as e:
        Py4GW.Console.Log(bot.config.bot_name, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


if __name__ == "__main__":
    main()
