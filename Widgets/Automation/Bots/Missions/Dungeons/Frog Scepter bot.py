from collections.abc import Generator
import inspect
import os
import time
from typing import Any
import Py4GW
import PyImGui
from Py4GWCoreLib import (
    Agent,
    AgentArray,
    Botting,
    ConsoleLog,
    GLOBAL_CACHE,
    Map,
    Player,
    Quest,
    Routines,
    SharedCommandType)
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.py4gwcorelib_src import Utils
from Py4GWCoreLib.routines_src.Yield import Yield
from Py4GW_widget_manager import get_widget_handler
from Sources.oazix.CustomBehaviors.primitives.botting.botting_helpers import BottingHelpers as CustomBottingHelpers
# ==================== CONFIGURATION ====================
BOT_NAME = "Frog Scepter bot"
MODULE_ALIASES = [
    "Bog",
]
WIDGETS_TO_ENABLE: tuple[str, ...] = (
    "LootManager",
    "CustomBehaviors",
    "ResurrectionScroll",
    "Return to outpost on defeat",
)
WIDGETS_TO_DISABLE: tuple[str, ...] = ()
# Some launcher/widget contexts don't populate __file__; keep a safe fallback.
_this_file = globals().get("__file__", f"{BOT_NAME}.py")
_SCRIPT_DIR = os.path.dirname(os.path.abspath(_this_file))
TEXTURE = os.path.join(_SCRIPT_DIR, "Frog Scepter.png")
_ALT_ONLY_DISABLE_WIDGETS: tuple[str, ...] = (os.path.splitext(os.path.basename(_this_file))[0],)
_MERCHANT_MANAGED_WIDGETS: tuple[str, ...] = ("InventoryPlus", "CustomBehaviors")
_PRETRAVEL_DISABLE_WIDGETS: tuple[str, ...] = ("InventoryPlus",)

_DIFFICULTY_SECTION = "Bogroot"
_DIFFICULTY_VAR = "use_hard_mode"
_use_hard_mode: bool = True
_difficulty_loaded: bool = False

_MERCHANT_SECTION = "Bogroot Merchant"
_merchant_enabled: bool = False
_merchant_id_kits_target: int = 3
_merchant_salvage_kits_target: int = 10
_merchant_store_consumable_materials: bool = False
_merchant_sell_materials: bool = False
_merchant_sell_rare_mats: bool = False
_merchant_buy_ectos: bool = False
_merchant_ecto_threshold: int = 800_000
_merchant_alt_wait_ms: int = 2000
_merchant_loaded: bool = False
_MAX_ALT_SETTLE_WAIT_MS = 5000

# Map IDs
MAP_GADDS_ENCAMPMENT = 638
MAP_SPARKFLY = 558
MAP_BOGROOT_L1 = 615
MAP_BOGROOT_L2 = 616

# Dialog IDs
DWARVEN_BLESSING_DIALOG = 0x84
TEKKS_QUEST_TAKE_DIALOG = 0x833901
TEKKS_QUEST_REWARD_DIALOG = 0x833907

# Coordinates
CHEST_POSITION = (14982.66, -19122.0)
TEKKS_POSITION = (14067.01, -17253.24)
DUNGEON_PORTAL_POSITION = (13097.0, 26393.0)
TEKKS_QUEST_ID = 0x339

TEKKS_REWARD_PENDING = False

def _verify_reward_taken_from_quest_log() -> Generator:
    global TEKKS_REWARD_PENDING

    quest_ids = Quest.GetQuestLogIds()

    if TEKKS_QUEST_ID not in quest_ids:
        TEKKS_REWARD_PENDING = True
        ConsoleLog(BOT_NAME, "[FLAG] Reward confirmed: quest no longer in quest log", log=True)
    else:
        TEKKS_REWARD_PENDING = False
        ConsoleLog(BOT_NAME, "[FLAG] Reward NOT confirmed: quest still present in quest log", log=True)

    yield

# ==================== GLOBAL VARIABLES ====================
bot = Botting(
    bot_name=BOT_NAME,
    upkeep_auto_combat_active=True,
    upkeep_auto_loot_active=True,
    upkeep_morale_active=False,
    upkeep_four_leaf_clover_active=True,
    upkeep_honeycomb_active=True,
)

TEKKS_POS = (14067.01, -17253.24)

# ==================== CORE ROUTINE ====================

def farm_froggy_routine(bot: Botting) -> None:
    # ===== INITIAL CONFIGURATION =====
    bot.Templates.Routines.UseCustomBehaviors(
        on_player_critical_death=CustomBottingHelpers.botting_unrecoverable_issue,
        on_party_death=CustomBottingHelpers.botting_unrecoverable_issue,
        on_player_critical_stuck=CustomBottingHelpers.botting_unrecoverable_issue)
    widget_handler = get_widget_handler()
    widget_handler.enable_widget('Return to outpost on defeat')

    bot.Events.OnPartyWipeCallback(lambda: _handle_party_wipe_event(bot))

    # ===== STARTUP =====
    bot.States.AddHeader("Startup - Widget and Merchant Setup")
    bot.Properties.Enable('auto_combat')
    bot.States.AddCustomState(_apply_widget_policy_step, "Apply widget policy")
    bot.States.AddCustomState(lambda: _gh_merchant_setup(leave_party=True), "GH Merchant Setup")
    bot.Templates.Aggressive()

    bot.States.AddHeader("Startup - Party Setup")
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=MAP_GADDS_ENCAMPMENT)
    bot.Multibox.SummonAllAccounts()
    bot.Wait.ForTime(4000)
    bot.Multibox.InviteAllAccounts()
    bot.States.AddCustomState(_reenable_merchant_widgets, "Re-enable merchant widgets")
    bot.Multibox.RestockAllPcons()
    bot.Multibox.RestockResurrectionScroll(250)

    # ===== RUN LOOP =====
    bot.States.AddHeader("Run Loop")
    bot.States.AddCustomState(_step_anchor, "Reset farm")
    bot.States.AddCustomState(_loop_marker, "RUN_START_POINT")
    _load_difficulty_setting()
    bot.Party.SetHardMode(_use_hard_mode)
    bot.Properties.Enable('auto_combat')
    bot.Quest.AbandonQuest(TEKKS_QUEST_ID)

    bot.States.AddHeader("Go to Dungeon")
    bot.Templates.Aggressive()
    bot.Move.XYAndExitMap(-9451.37, -19766.40, target_map_id=MAP_SPARKFLY)
    bot.Wait.UntilOnExplorable()
    bot.Wait.ForTime(2000)
    bot.Multibox.UseAllConsumables()
    bot.Move.XYAndInteractNPC(-8950.0, -19843.0)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)

    # Path to Tekks
    bot.Move.XY(-8933.0, -18909.0)
    bot.Move.XY(-10361.0, -16332.0)
    bot.Move.XY(-11211.0, -13459.0)
    bot.Move.XY(-10755.0, -10552.0)
    bot.Move.XY(-9544.0, -7814.0)
    bot.Move.XY(-7662.0, -5532.0)
    bot.Wait.ForTime(8000)
    bot.Move.XY(-6185.0, -4182.0)
    bot.Move.XY(-4742.0, -2793.0)
    bot.Move.XY(-2150.0, -1301.0)
    bot.Move.XY(71.0, 733.0)
    bot.Wait.ForTime(8000)
    bot.Move.XY(1480.0, 3385.0)
    bot.Move.XY(2928.0, 4790.0)
    bot.Move.XY(4280.0, 6273.0)
    bot.Move.XY(5420.0, 7923.0)
    bot.Move.XY(6912.62, 8937.64)
    bot.Move.XY(7771.0, 11123.0)
    bot.Move.XY(8968.0, 12699.0)
    bot.Wait.ForTime(8000)
    bot.Move.XY(10876.0, 13304.0)
    bot.Move.XY(12481.0, 14496.0)
    bot.Move.XY(13080.0, 16405.0)
    bot.Move.XY(13487.0, 18372.0)
    bot.Move.XY(13476.0, 20370.0)
    bot.Move.XY(12503.0, 22721.0)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(3000)

    bot.States.AddCustomState(_loop_marker, "LOOP_RESTART_POINT")

    bot.States.AddCustomState(lambda: _search_and_talk_with_tekks(bot), "Find Tekks and talk")
    bot.Wait.ForTime(5000)
    bot.Multibox.SendDialogToTarget(TEKKS_QUEST_TAKE_DIALOG)
    bot.Wait.ForTime(4000)

    bot.Move.XY(11676.01, 22685.0)
    bot.Move.XY(11562.77, 24059.0)
    bot.Move.XY(13097.0, 26393.0)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(2000)

    # ===== LEVEL 1 =====
    bot.States.AddHeader("Level 1 - Entry and Blessing")
    bot.Templates.Aggressive()
    bot.Multibox.UseAllConsumables()
    bot.States.AddCustomState(_use_summons, "UseSummons")
    bot.Move.XY(18092.0, 4315.0)
    bot.Move.XY(19045.95, 7877.0)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(3000)

    bot.Move.XYAndInteractNPC(19045.95, 7877.0)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)

    bot.States.AddHeader("Level 1 - Secure Return Checkpoint 1")
    bot.States.AddCustomState(_step_anchor, "Secure return - L1")
    bot.Wait.ForTime(3000)
    bot.Move.XY(16541.48, 8558.94)
    bot.Move.XY(13038.90, 7792.40)
    bot.Move.XY(11666.15, 6464.53)
    bot.Move.XY(10030.42, 7026.09)
    bot.Move.XY(9752.17, 8241.79)
    bot.Move.XY(8238.36, 7434.97)
    bot.Move.XY(6491.41, 5310.56)

    bot.States.AddHeader("Level 1 - Secure Return Checkpoint 2")
    bot.States.AddCustomState(_step_anchor, "Secure return 2 - L1")

    bot.Move.XY(5097.64, 2204.33)
    bot.Move.XY(1228.15, 54.49)
    bot.Wait.ForTime(8000)
    bot.Move.XY(-140.87, 2741.86)
    bot.Wait.ForTime(3000)
    bot.Move.XY(1228.15, 54.49)
    bot.Move.XY(141.23, -1965.14)

    bot.States.AddHeader("Level 1 - Secure Return Checkpoint 3")
    bot.States.AddCustomState(_step_anchor, "Secure return 3 - L1")

    bot.Move.XY(-1540.98, -5820.18)
    bot.Move.XY(-269.32, -8533.17)
    bot.Move.XY(-1230.10, -8608.68)
    bot.Wait.ForTime(8000)
    bot.Move.XY(853.90, -9041.68)
    bot.Move.XY(1868.0, -10647.0)
    bot.Move.XY(1645.0, -11810.0)
    bot.Move.XY(1604.90, -12033.70)
    bot.Move.XY(1579.39, -14311.38)
    bot.Move.XY(7319.99, -17202.99)
    bot.Move.XY(8450.01, -16460.50)
    bot.Move.XY(7356.56, -18272.24)
    bot.Move.XY(7865.0, -19350.0)
    bot.Wait.ForTime(5000)
    bot.Wait.UntilOutOfCombat()

    bot.Wait.ForMapToChange(target_map_name="Bogroot Growths (level 2)")

    # ===== LEVEL 2 =====
    bot.States.AddHeader("Level 2 - Entry and Blessing")
    bot.Templates.Aggressive()
    bot.Multibox.UseAllConsumables()
    bot.States.AddCustomState(_use_summons, "UseSummons")
    bot.Wait.ForTime(3000)

    bot.Move.XY(-11055.0, -5551.0)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(3000)
    bot.Move.XYAndInteractNPC(-11055.0, -5551.0)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)

    bot.States.AddHeader("Level 2 - Secure Return Checkpoint 1")
    bot.States.AddCustomState(_step_anchor, "Secure return - L2")

    bot.Move.XY(-11522.0, -3486.0)
    bot.Move.XY(-10639.0, -4076.0)
    bot.Move.XY(-11321.0, -5033.0)
    bot.Move.XY(-11268.0, -3922.0)
    bot.Move.XY(-11187.0, -2190.0)
    bot.Move.XY(-10706.0, -1272.0)
    bot.Move.XY(-10535.0, -191.0)
    bot.Move.XY(-10262.0, -1167.0)
    bot.Wait.ForTime(8000)
    bot.Move.XY(-9390.0, -393.0)
    bot.Move.XY(-8427.0, 1043.0)
    bot.Move.XY(-7297.0, 2371.0)
    bot.Move.XY(-6460.0, 2964.0)
    bot.Move.XY(-5173.0, 3621.0)
    bot.Move.XY(-4225.0, 4452.0)
    bot.Move.XY(-3405.0, 5274.0)
    bot.Wait.ForTime(8000)
    bot.Move.XY(-2778.0, 6814.0)
    bot.Move.XY(-3725.0, 7823.0)
    bot.Move.XY(-3627.0, 8933.0)
    bot.Move.XY(-3014.0, 10554.0)
    bot.Move.XY(-1604.0, 11789.0)
    bot.Move.XY(-955.0, 10984.0)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(3000)

    bot.Move.XYAndInteractNPC(-955.0, 10984.0)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)

    bot.States.AddHeader("Level 2 - Secure Return Checkpoint 2")
    bot.States.AddCustomState(_step_anchor, "Secure return 2 - L2")

    bot.Move.XY(216.0, 11534.0)
    bot.Move.XY(1485.0, 12022.0)
    bot.Move.XY(2690.0, 12615.0)
    bot.Wait.ForTime(4000)
    bot.Move.XY(3343.0, 13721.0)
    bot.Move.XY(4693.0, 13577.0)
    bot.Move.XY(5693.0, 12927.0)
    bot.Move.XY(5942.0, 11067.0)
    bot.Move.XY(6878.0, 9657.0)
    bot.Wait.ForTime(8000)
    bot.Move.XY(8100.54, 8544.52)
    bot.Move.XY(8725.26, 7115.42)
    bot.Move.XY(9234.03, 6843.0)
    bot.Move.XY(8591.0, 4285.0)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(3000)

    bot.Move.XYAndInteractNPC(8591.0, 4285.0)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)

    bot.States.AddHeader("Level 2 - Secure Return Checkpoint 3")
    bot.States.AddCustomState(_step_anchor, "Secure return 3 - L2")

    bot.Move.XY(8372.0, 3448.0)
    bot.Move.XY(8714.0, 2151.0)
    bot.Move.XY(9268.0, 1261.0)
    bot.Move.XY(10207.0, -201.0)
    bot.Move.XY(10999.0, -1356.0)
    bot.Move.XY(10593.0, -2846.0)
    bot.Move.XY(10280.0, -4144.0)
    bot.Move.XY(11016.0, -5384.0)
    bot.Move.XY(12943.0, -6511.0)
    bot.Move.XY(15127.0, -6231.0)
    bot.Move.XY(16461.0, -6041.0)
    bot.Move.XY(16389.50, -4090.36)
    bot.Move.XY(15309.36, -2904.08)
    bot.Move.XY(14357.81, -5818.01)
    bot.Move.XY(16461.0, -6041.0)
    bot.Move.XY(17565.0, -6227.0)
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("Level 2 - Open Boss Door")
    ConsoleLog(BOT_NAME, "Opening boss door...")
    bot.Move.XYAndInteractGadget(17867.55, -6250.63)
    bot.Wait.ForTime(2000)
    bot.Move.XYAndInteractGadget(17867.55, -6250.63)
    bot.Wait.ForTime(2000)
    ConsoleLog(BOT_NAME, "Door should be open!")
    bot.Wait.ForTime(1000)

    bot.Move.XY(17623.87, -6546.0)
    bot.Move.XY(18024.0, -9191.0)
    bot.Move.XY(17110.0, -9842.0)
    bot.Move.XY(15867.0, -10866.0)
    bot.Move.XY(17555.0, -11963.0)
    bot.Move.XY(18761.0, -12747.0)
    bot.Move.XY(19619.0, -11498.0)
    bot.Wait.UntilOutOfCombat()

    bot.Move.XYAndInteractNPC(19619.0, -11498.0)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)

    bot.States.AddHeader("Level 2 - Boss Checkpoint")
    bot.States.AddCustomState(_step_anchor, "Secure return - Boss")

    bot.States.AddHeader("Boss Fight")
    bot.Templates.Aggressive()
    bot.Move.XY(17582.52, -14231.0)
    bot.Move.XY(14794.47, -14929.0)
    bot.Move.XY(13609.12, -17286.0)
    bot.Move.XY(14079.80, -17776.0)
    bot.Move.XY(15116.40, -18733.0)
    bot.Move.XY(15914.68, -19145.53)
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("Final Chest")
    bot.Move.XY(15030.00, -19168.00)
    bot.States.AddCustomState(_open_bogroot_chest, "Open chest with all accounts")

    bot.States.AddHeader("Quest Turn-In and Reset")
    bot.States.AddCustomState(lambda: _search_and_talk_with_tekks(bot), "Find Tekks and talk")
    bot.Wait.ForTime(5000)
    bot.Multibox.SendDialogToTarget(TEKKS_QUEST_REWARD_DIALOG)
    bot.Wait.ForTime(4000)
    bot.States.AddCustomState(_verify_reward_taken_from_quest_log, "Verify reward from quest log")

    bot.Wait.ForMapToChange(target_map_name="Sparkfly Swamp")
    bot.States.AddCustomState(lambda: _post_return_flow(bot), "Post-return quest handling")
    bot.States.JumpToStepName("LOOP_RESTART_POINT")

# ==================== CUSTOM HELPERS ====================

# --- Reward State ---

def _mark_reward_not_taken():
    global TEKKS_REWARD_PENDING
    TEKKS_REWARD_PENDING = False
    yield

def _mark_reward_taken():
    global TEKKS_REWARD_PENDING
    TEKKS_REWARD_PENDING = True
    yield

# --- Wipe Recovery ---

def _on_party_wipe(bot: "Botting"):
    # Wait until we are alive again
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            bot.config.FSM.resume()
            return

    ConsoleLog("Res Check", "We ressed retrying!")
    yield from bot.Wait._coro_for_time(3000)

    # Map-safe anchors (YOU said you replaced jumps by headers)
    # These should be the JUMPABLE step names (anchors), not just visual headers.
    SHRINES_BY_MAP = {
        MAP_BOGROOT_L1: [
            ("Secure return - L1", 19045.95, 7877.0),
            ("Secure return 2 - L1", 5083.0, 2155.0),
            ("Secure return 3 - L1", -1547.0, -8696.0)
        ],
        MAP_BOGROOT_L2: [
            ("Secure return - L2", -14076.0, -19457.0),
            ("Secure return 2 - L2", -955.0, 10984.0),
            ("Secure return 3 - L2", 216.0, 11534.0),
            ("Secure return - Boss", 19619.0, -11498.0)
        ]
    }

    def pick_nearest_anchor(map_id: int, px: float, py: float) -> str:
        candidates = SHRINES_BY_MAP.get(map_id)
        if not candidates:
            return "Reset farm"  # generic fallback anchor

        best_name = candidates[0][0]
        best_d2 = float("inf")
        for name, sx, sy in candidates:
            d2 = (px - sx) ** 2 + (py - sy) ** 2
            if d2 < best_d2:
                best_d2 = d2
                best_name = name
        return best_name

    player_x, player_y = Player.GetXY()
    map_id = int(Map.GetMapID())

    bot.config.FSM.pause()

    # Not in dungeon maps -> resign and go to generic secure return
    if map_id not in (MAP_BOGROOT_L1, MAP_BOGROOT_L2):
        bot.Multibox.ResignParty()
        yield from bot.Wait._coro_for_time(10000)
        bot.config.FSM.jump_to_state_by_name("Reset farm")
        bot.config.FSM.resume()
        return

    # Full party defeated -> let widget handle return
    if GLOBAL_CACHE.Party.IsPartyDefeated():
        yield from bot.Wait._coro_for_time(10000)
        bot.config.FSM.jump_to_state_by_name("Reset farm")
        bot.config.FSM.resume()
        return

    chosen = pick_nearest_anchor(map_id, float(player_x), float(player_y))

    ConsoleLog("Res Check", f"↩ wipe-route -> {chosen} (map={map_id}, pos=({player_x:.0f},{player_y:.0f}))")
    bot.config.FSM.jump_to_state_by_name(chosen)

    bot.config.FSM.resume()
    return

# --- Tekks Targeting Helpers ---

def _target_and_move_to_tekks(bot: Botting) -> Generator[Any, Any, None]:
    npc_name = "Tekks"

    ConsoleLog(BOT_NAME, "[TEST] _target_and_move_to_tekks -> start", log=True)

    while True:
        agent_id = yield from Yield.Agents.GetAgentIDByName(npc_name)

        if not agent_id:
            ConsoleLog(BOT_NAME, "[TEST] Tekks not found, retrying...", log=True)
            yield from Routines.Yield.wait(500)
            continue

        ConsoleLog(BOT_NAME, f"[TEST] Tekks found (agent_id={agent_id})", log=True)

        # Cibler Tekks
        Player.ChangeTarget(agent_id)
        yield from Routines.Yield.wait(500)

        # Récupérer ses coordonnées
        x, y = Agent.GetXY(agent_id)
        ConsoleLog(BOT_NAME, f"[TEST] Moving to Tekks at ({x}, {y})", log=True)

        # Se déplacer vers Tekks
        bot.Move.XYAndDialog(x, y, TEKKS_QUEST_TAKE_DIALOG)
        yield from Routines.Yield.wait(1000)

        # Cibler Tekks
        Player.ChangeTarget(agent_id)
        yield from Routines.Yield.wait(500)
        

        ConsoleLog(BOT_NAME, "[TEST] Target + move command sent", log=True)
        return

# --- FSM Anchor Helpers ---

def _step_anchor() -> Generator:
    yield

def _handle_party_wipe_event(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))

# --- Quest and Movement Helpers ---



def _move_to(x: float, y: float, tolerance: float = 180.0, max_tries: int = 60):
    Player.Move(x, y)

    for _ in range(max_tries):
        px, py = Player.GetXY()
        dist = Utils.Distance((px, py), (x, y))

        if dist <= tolerance:
            return True

        yield from Routines.Yield.wait(100)

    return False


def _wait_for_map(map_name: str, max_tries: int = 120):
    for _ in range(max_tries):
        if Map.GetMapName() == map_name:
            return True
        yield from Routines.Yield.wait(500)
    return False

def _interact_with_tekks(bot: Botting, dialog_id: int, tolerance: float = 220.0):
    npc_name = "Tekks"

    agent_id = yield from Yield.Agents.GetAgentIDByName(npc_name)
    if not agent_id:
        ConsoleLog(BOT_NAME, f"[Tekks] {npc_name} introuvable", log=True)
        return False

    x, y = Agent.GetXY(agent_id)
    ConsoleLog(BOT_NAME, f"[Tekks] Found {npc_name} at ({x}, {y})", log=True)
    
    ok = yield from _move_to(x, y, tolerance=tolerance)
    if not ok:
        ConsoleLog(BOT_NAME, "[Tekks] Impossible d'approcher Tekks", log=True)
        return False
        

    Player.ChangeTarget(agent_id)
    yield from Routines.Yield.wait(800)
    Player.Interact(agent_id)
    yield from Routines.Yield.wait(800)
    Player.SendDialog(dialog_id)
    bot.Multibox.SendDialogToTarget(dialog_id)
    yield from Routines.Yield.wait(1500)
    return True


# --- Reward Recovery Flow ---

def _recover_reward_and_retake_quest(bot: Botting) -> Generator:
    global TEKKS_REWARD_PENDING

    ConsoleLog(BOT_NAME, "[RECOVERY] Late reward flow -> start", log=True)

    # 1) Reward Tekks in Sparkfly
    if Map.GetMapName() != "Sparkfly Swamp":
        ConsoleLog(BOT_NAME, f"[RECOVERY] Mauvaise map pour reward: {Map.GetMapName()}", log=True)
        yield
        return

    
    ok = yield from _interact_with_tekks(bot, TEKKS_QUEST_REWARD_DIALOG)
    if not ok:
        ConsoleLog(BOT_NAME, "[RECOVERY] Reward Tekks failed", log=True)
        yield
        return

    # 2) Go to dungeon entrance
    for x, y in [
        (11676.01, 22685.0),
        (11562.77, 24059.0)]:
        ok = yield from _move_to(x, y)
        if not ok:
            ConsoleLog(BOT_NAME, f"[RECOVERY] Failed move to ({x}, {y})", log=True)
            yield
            return

    # Ici, si nécessaire, interaction explicite avec le portail
    # à adapter selon ton framework / la vraie coord du portail
    Player.Move(13097.0, 26393.0)
    yield from Routines.Yield.wait(1000)

    ok = yield from _wait_for_map("Bogroot Growths (level 1)")
    if not ok:
        ConsoleLog(BOT_NAME, "[RECOVERY] Impossible d'entrer en Bogroot Growths (level 1)", log=True)
        yield
        return

    ConsoleLog(BOT_NAME, "[RECOVERY] Entered Bogroot Growths (level 1)", log=True)

    # 3) Exit dungeon
    ok = yield from _move_to(14600.0, 470.0)
    if not ok:
        ConsoleLog(BOT_NAME, "[RECOVERY] Failed move to dungeon exit", log=True)
        yield
        return

    yield from Routines.Yield.wait(1000)

    ok = yield from _wait_for_map("Sparkfly Swamp")
    if not ok:
        ConsoleLog(BOT_NAME, "[RECOVERY] Impossible de revenir à Sparkfly Swamp", log=True)
        yield
        return

    ConsoleLog(BOT_NAME, "[RECOVERY] Back to Sparkfly Swamp", log=True)



    Player.Move(11193.21, 22787.21)
    yield from Routines.Yield.wait(8000)

    # 4) Retake quest from Tekks
    ok = yield from _interact_with_tekks(bot, TEKKS_QUEST_TAKE_DIALOG)
    if not ok:
        ConsoleLog(BOT_NAME, "[RECOVERY] Retake quest failed", log=True)
        yield
        return

    ConsoleLog(BOT_NAME, "[RECOVERY] Late reward flow -> done", log=True)



    bot.States.JumpToStepName("LOOP_RESTART_POINT")
    yield


def _post_return_flow(bot: Botting) -> Generator:
    global TEKKS_REWARD_PENDING

    ConsoleLog(BOT_NAME, f"[POST-RETURN] Flag value = {TEKKS_REWARD_PENDING}", log=True)

    if not TEKKS_REWARD_PENDING:
        ConsoleLog(BOT_NAME, "[POST-RETURN] Reward NOT taken -> recovery flow", log=True)
        yield from _recover_reward_and_retake_quest(bot)
        yield
        return

    ConsoleLog(BOT_NAME, "[POST-RETURN] Reward taken -> continue", log=True)
    yield

# --- Widget Policy Helpers ---

def _disable_widgets_on_alts_only(widget_names: tuple[str, ...]) -> Generator:
    if not widget_names:
        yield
        return

    my_email = Player.GetAccountEmail()
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        account_email = str(getattr(account, "AccountEmail", "") or "")
        if not account_email or account_email == my_email:
            continue
        for widget_name in widget_names:
            GLOBAL_CACHE.ShMem.SendMessage(
                my_email,
                account_email,
                SharedCommandType.DisableWidget,
                (0, 0, 0, 0),
                (widget_name, "", "", ""),
            )
    yield from Routines.Yield.wait(500)

def _apply_widget_policy_step() -> Generator:
    bot.Multibox.ApplyWidgetPolicy(
        enable_widgets=WIDGETS_TO_ENABLE,
        disable_widgets=WIDGETS_TO_DISABLE,
        apply_local=True,
    )
    yield from _disable_widgets_on_alts_only(_ALT_ONLY_DISABLE_WIDGETS)
    yield

# --- Settings and Widget UI Helpers ---

def _reenable_merchant_widgets() -> Generator:
    """Re-enable common managed widgets on leader and alts."""
    try:
        from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler as _get_wh
        wh = _get_wh()
        for widget_name in _MERCHANT_MANAGED_WIDGETS:
            wh.enable_widget(widget_name)
    except Exception:
        pass

    my_email = Player.GetAccountEmail()
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        account_email = str(getattr(account, "AccountEmail", "") or "")
        if not account_email or account_email == my_email:
            continue
        for widget_name in _MERCHANT_MANAGED_WIDGETS:
            GLOBAL_CACHE.ShMem.SendMessage(
                my_email,
                account_email,
                SharedCommandType.EnableWidget,
                (0, 0, 0, 0),
                (widget_name, "", "", ""),
            )
    yield from Routines.Yield.wait(500)
    yield

def _load_difficulty_setting() -> None:
    global _use_hard_mode, _difficulty_loaded
    if _difficulty_loaded:
        return

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

    _use_hard_mode = bool(
        IniManager().get(
            key=bot.config.ini_key,
            section=_DIFFICULTY_SECTION,
            var_name=_DIFFICULTY_VAR,
            default=True,
        )
    )
    _difficulty_loaded = True

def _save_difficulty_setting() -> None:
    if not bot.config.ini_key:
        return
    IniManager().set(
        key=bot.config.ini_key,
        section=_DIFFICULTY_SECTION,
        var_name=_DIFFICULTY_VAR,
        value=_use_hard_mode,
    )

def _draw_difficulty_setting() -> None:
    global _use_hard_mode
    _load_difficulty_setting()
    new_hard_mode = PyImGui.checkbox("Hard Mode (HM)", _use_hard_mode)
    if new_hard_mode != _use_hard_mode:
        _use_hard_mode = new_hard_mode
        _save_difficulty_setting()

def _load_merchant_settings() -> None:
    global _merchant_enabled, _merchant_id_kits_target, _merchant_salvage_kits_target
    global _merchant_store_consumable_materials, _merchant_sell_materials, _merchant_sell_rare_mats
    global _merchant_buy_ectos, _merchant_ecto_threshold, _merchant_alt_wait_ms, _merchant_loaded
    if _merchant_loaded:
        return

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

    _merchant_enabled = bool(IniManager().get(key=bot.config.ini_key, section=_MERCHANT_SECTION, var_name="enabled", default=False))
    _merchant_id_kits_target = int(IniManager().get(key=bot.config.ini_key, section=_MERCHANT_SECTION, var_name="id_kits_target", default=3))
    _merchant_salvage_kits_target = int(IniManager().get(key=bot.config.ini_key, section=_MERCHANT_SECTION, var_name="salvage_kits_target", default=10))
    _merchant_store_consumable_materials = bool(IniManager().get(key=bot.config.ini_key, section=_MERCHANT_SECTION, var_name="store_consumable_materials", default=False))
    _merchant_sell_materials = bool(IniManager().get(key=bot.config.ini_key, section=_MERCHANT_SECTION, var_name="sell_materials", default=False))
    _merchant_sell_rare_mats = bool(IniManager().get(key=bot.config.ini_key, section=_MERCHANT_SECTION, var_name="sell_rare_mats", default=False))
    _merchant_buy_ectos = bool(IniManager().get(key=bot.config.ini_key, section=_MERCHANT_SECTION, var_name="buy_ectos", default=False))
    _merchant_ecto_threshold = int(IniManager().get(key=bot.config.ini_key, section=_MERCHANT_SECTION, var_name="ecto_threshold", default=800_000))
    _merchant_alt_wait_ms = max(0, min(_MAX_ALT_SETTLE_WAIT_MS, int(IniManager().get(key=bot.config.ini_key, section=_MERCHANT_SECTION, var_name="alt_wait_ms", default=2000))))
    _merchant_loaded = True

def _save_merchant_settings() -> None:
    if not bot.config.ini_key:
        return
    IniManager().set(key=bot.config.ini_key, section=_MERCHANT_SECTION, var_name="enabled", value=_merchant_enabled)
    IniManager().set(key=bot.config.ini_key, section=_MERCHANT_SECTION, var_name="id_kits_target", value=_merchant_id_kits_target)
    IniManager().set(key=bot.config.ini_key, section=_MERCHANT_SECTION, var_name="salvage_kits_target", value=_merchant_salvage_kits_target)
    IniManager().set(key=bot.config.ini_key, section=_MERCHANT_SECTION, var_name="store_consumable_materials", value=_merchant_store_consumable_materials)
    IniManager().set(key=bot.config.ini_key, section=_MERCHANT_SECTION, var_name="sell_materials", value=_merchant_sell_materials)
    IniManager().set(key=bot.config.ini_key, section=_MERCHANT_SECTION, var_name="sell_rare_mats", value=_merchant_sell_rare_mats)
    IniManager().set(key=bot.config.ini_key, section=_MERCHANT_SECTION, var_name="buy_ectos", value=_merchant_buy_ectos)
    IniManager().set(key=bot.config.ini_key, section=_MERCHANT_SECTION, var_name="ecto_threshold", value=_merchant_ecto_threshold)
    IniManager().set(key=bot.config.ini_key, section=_MERCHANT_SECTION, var_name="alt_wait_ms", value=_merchant_alt_wait_ms)

def _draw_merchant_settings() -> None:
    global _merchant_enabled, _merchant_id_kits_target, _merchant_salvage_kits_target
    global _merchant_store_consumable_materials, _merchant_sell_materials, _merchant_sell_rare_mats
    global _merchant_buy_ectos, _merchant_ecto_threshold, _merchant_alt_wait_ms

    _load_merchant_settings()

    PyImGui.separator()
    PyImGui.text("Merchant (Guild Hall) - runs once on startup")
    PyImGui.separator()

    new_enabled = PyImGui.checkbox("Restock kits / sell materials on startup", _merchant_enabled)
    if new_enabled != _merchant_enabled:
        _merchant_enabled = new_enabled
        _save_merchant_settings()

    if not _merchant_enabled:
        return

    PyImGui.push_item_width(100)
    new_id = PyImGui.input_int("ID Kits target##bogroot_id", _merchant_id_kits_target)
    if new_id != _merchant_id_kits_target:
        _merchant_id_kits_target = max(0, int(new_id))
        _save_merchant_settings()

    new_sal = PyImGui.input_int("Salvage Kits target##bogroot_sal", _merchant_salvage_kits_target)
    if new_sal != _merchant_salvage_kits_target:
        _merchant_salvage_kits_target = max(0, int(new_sal))
        _save_merchant_settings()
    PyImGui.pop_item_width()

    new_sell = PyImGui.checkbox("Sell common materials##bogroot_sell", _merchant_sell_materials)
    if new_sell != _merchant_sell_materials:
        _merchant_sell_materials = new_sell
        _save_merchant_settings()

    new_store = PyImGui.checkbox(
        "Store consumable materials (Dust/Iron/Feather/Bone/Fiber)##bogroot_store_cons_mats",
        _merchant_store_consumable_materials,
    )
    if new_store != _merchant_store_consumable_materials:
        _merchant_store_consumable_materials = new_store
        _save_merchant_settings()

    new_rare = PyImGui.checkbox("Sell Diamond & Onyx to Rare Material Trader##bogroot_rare_mats", _merchant_sell_rare_mats)
    if new_rare != _merchant_sell_rare_mats:
        _merchant_sell_rare_mats = new_rare
        _save_merchant_settings()

    new_ectos = PyImGui.checkbox("Buy Glob of Ectoplasm when storage over threshold##bogroot_ectos", _merchant_buy_ectos)
    if new_ectos != _merchant_buy_ectos:
        _merchant_buy_ectos = new_ectos
        _save_merchant_settings()

    if _merchant_buy_ectos:
        new_thresh = PyImGui.input_int("Storage threshold (gold)##bogroot_ecto_thresh", _merchant_ecto_threshold)
        if new_thresh != _merchant_ecto_threshold:
            _merchant_ecto_threshold = max(0, int(new_thresh))
            _save_merchant_settings()

    PyImGui.push_item_width(100)
    new_wait = PyImGui.input_int("Alt settle wait (ms)##bogroot_alt_wait", _merchant_alt_wait_ms)
    if new_wait != _merchant_alt_wait_ms:
        _merchant_alt_wait_ms = max(0, min(_MAX_ALT_SETTLE_WAIT_MS, int(new_wait)))
        _save_merchant_settings()
    PyImGui.pop_item_width()
    PyImGui.same_line(0, 6)
    PyImGui.text("(time given to alts to finish)")

# --- Merchant and Inventory Helpers ---

def _find_npc_xy_by_name(name_fragment: str, max_dist: float = 15000.0):
    npcs = AgentArray.GetNPCMinipetArray()
    npcs = AgentArray.Filter.ByDistance(npcs, Player.GetXY(), max_dist)
    for npc_id in npcs:
        npc_name = Agent.GetNameByID(int(npc_id))
        if name_fragment.lower() in npc_name.lower():
            return Agent.GetXY(int(npc_id))
    return None

def _count_model_in_inventory(model_id: int) -> int:
    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    count = 0
    for item_id in item_array:
        if int(GLOBAL_CACHE.Item.GetModelID(item_id)) == int(model_id):
            count += max(1, int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)))
    return count

def _get_leftover_material_item_ids(batch_size: int = 10) -> list[int]:
    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    leftovers: list[int] = []
    for item_id in item_array:
        if not GLOBAL_CACHE.Item.Type.IsMaterial(item_id):
            continue
        if GLOBAL_CACHE.Item.Type.IsRareMaterial(item_id):
            continue
        qty = int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))
        if 0 < qty < batch_size:
            leftovers.append(int(item_id))
    return leftovers

def _get_material_item_ids_by_models(selected_models: set[int]) -> list[int]:
    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    result: list[int] = []
    for item_id in item_array:
        if not GLOBAL_CACHE.Item.Type.IsMaterial(item_id):
            continue
        if GLOBAL_CACHE.Item.Type.IsRareMaterial(item_id):
            continue
        model_id = int(GLOBAL_CACHE.Item.GetModelID(item_id))
        if model_id in selected_models:
            result.append(int(item_id))
    return result

def _coro_deposit_crafting_materials_to_storage(selected_models: set[int]) -> Generator:
    if not selected_models:
        yield
        return
    if not GLOBAL_CACHE.Inventory.IsStorageOpen():
        GLOBAL_CACHE.Inventory.OpenXunlaiWindow()
        yield from Routines.Yield.wait(1000)
    if not GLOBAL_CACHE.Inventory.IsStorageOpen():
        ConsoleLog(BOT_NAME, "[Merchant] Storage not open; skipping crafting material deposit", Py4GW.Console.MessageType.Warning)
        yield
        return

    item_ids = _get_material_item_ids_by_models(selected_models)
    if not item_ids:
        yield
        return

    for item_id in item_ids:
        GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
        yield from Routines.Yield.wait(40)

def _coro_sell_scrolls(mx: float, my: float) -> Generator:
    scroll_model_ids = {5594, 5595, 5611, 5853, 5975, 5976, 21233}
    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    sell_ids = [int(item_id) for item_id in item_array if int(GLOBAL_CACHE.Item.GetModelID(item_id)) in scroll_model_ids]
    if not sell_ids:
        yield
        return
    yield from bot.Move._coro_xy_and_interact_npc(mx, my, "GH Merchant (scrolls)")
    yield from Routines.Yield.wait(1200)
    yield from Routines.Yield.Merchant.SellItems(sell_ids, log=True)
    yield from Routines.Yield.wait(300)

def _coro_sell_nonsalvageable_golds(mx: float, my: float) -> Generator:
    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    sell_ids = []
    for item_id in item_array:
        _, rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
        if rarity != "Gold":
            continue
        if not GLOBAL_CACHE.Item.Usage.IsIdentified(item_id):
            continue
        if GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id):
            continue
        sell_ids.append(int(item_id))
    if not sell_ids:
        yield
        return
    yield from bot.Move._coro_xy_and_interact_npc(mx, my, "GH Merchant (golds)")
    yield from Routines.Yield.wait(1200)
    yield from Routines.Yield.Merchant.SellItems(sell_ids, log=True)
    yield from Routines.Yield.wait(300)

def _coro_sell_rare_mats_at_trader(x: float, y: float, model_ids: set[int]) -> Generator:
    yield from Routines.Yield.Movement.FollowPath([(x, y)])
    yield from Routines.Yield.wait(100)
    yield from Routines.Yield.Agents.InteractWithAgentXY(x, y)
    yield from Routines.Yield.wait(1000)

    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    for item_id in item_array:
        if int(GLOBAL_CACHE.Item.GetModelID(item_id)) not in model_ids:
            continue
        stack_qty = int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))
        while stack_qty > 0:
            quoted = yield from Routines.Yield.Merchant._wait_for_quote(
                GLOBAL_CACHE.Trading.Trader.RequestSellQuote, item_id,
                timeout_ms=750, step_ms=10)
            if quoted <= 0:
                break
            GLOBAL_CACHE.Trading.Trader.SellItem(item_id, quoted)
            new_qty = yield from Routines.Yield.Merchant._wait_for_stack_quantity_drop(
                item_id, stack_qty, timeout_ms=750, step_ms=10)
            if new_qty >= stack_qty:
                break
            stack_qty = new_qty

def _disable_merchant_widgets() -> Generator:
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler as _get_wh
    wh = _get_wh()
    for name in _MERCHANT_MANAGED_WIDGETS:
        wh.disable_widget(name)
    my_email = Player.GetAccountEmail()
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if acc.AccountEmail != my_email:
            for name in _MERCHANT_MANAGED_WIDGETS:
                GLOBAL_CACHE.ShMem.SendMessage(
                    my_email, acc.AccountEmail,
                    SharedCommandType.DisableWidget, (0, 0, 0, 0), (name, "", "", ""),
                )
    yield

def _disable_inventoryplus_pretravel() -> Generator:
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler as _get_wh
    wh = _get_wh()
    for name in _PRETRAVEL_DISABLE_WIDGETS:
        wh.disable_widget(name)
    my_email = Player.GetAccountEmail()
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if acc.AccountEmail != my_email:
            for name in _PRETRAVEL_DISABLE_WIDGETS:
                GLOBAL_CACHE.ShMem.SendMessage(
                    my_email, acc.AccountEmail,
                    SharedCommandType.DisableWidget, (0, 0, 0, 0), (name, "", "", ""),
                )
    yield from Routines.Yield.wait(1500)

def _gh_merchant_setup(leave_party: bool = True) -> Generator:
    from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
    from Sources.oazix.CustomBehaviors.primitives.parties.party_command_contants import PartyCommandConstants
    from Py4GWCoreLib.enums_src.Model_enums import ModelID as _ModelID

    _load_merchant_settings()
    if not _merchant_enabled:
        yield
        return

    if leave_party:
        ConsoleLog(BOT_NAME, "[Merchant] Leaving party on all accounts before GH travel")
        my_email = Player.GetAccountEmail()
        for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
            if acc.AccountEmail != my_email:
                GLOBAL_CACHE.ShMem.SendMessage(my_email, acc.AccountEmail, SharedCommandType.LeaveParty, (0, 0, 0, 0), ("", "", "", ""))
        GLOBAL_CACHE.Party.LeaveParty()
        yield from Routines.Yield.wait(2000)

    yield from _disable_inventoryplus_pretravel()

    cb_deadline = time.time() + 30
    while not CustomBehaviorParty().is_ready_for_action() and time.time() < cb_deadline:
        yield from Routines.Yield.wait(100)

    ok = bool(CustomBehaviorParty().schedule_action(PartyCommandConstants.travel_gh))
    if not ok and not Map.IsGuildHall():
        Map.TravelGH()

    cb_deadline = time.time() + 60
    while not CustomBehaviorParty().is_ready_for_action() and time.time() < cb_deadline:
        yield from Routines.Yield.wait(200)

    gh_deadline = time.time() + 30
    while not Map.IsGuildHall() and time.time() < gh_deadline:
        yield from Routines.Yield.wait(500)
    if not Map.IsGuildHall():
        ConsoleLog(BOT_NAME, "[Merchant] Failed to reach Guild Hall - skipping merchant step")
        yield
        return

    yield from Routines.Yield.wait(3000)
    yield from _disable_merchant_widgets()

    my_email = Player.GetAccountEmail()

    def _dispatch_to_alts(command, params, extra_data=("", "", "", "")) -> list[tuple[str, int]]:
        refs: list[tuple[str, int]] = []
        for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
            if acc.AccountEmail != my_email:
                msg_index = int(GLOBAL_CACHE.ShMem.SendMessage(my_email, acc.AccountEmail, command, params, extra_data))
                refs.append((acc.AccountEmail, msg_index))
        return refs

    def _wait_for_alt_dispatch_completion(stage_name: str, message_refs: list[tuple[str, int]], command, timeout_ms: int = 30000):
        pending = {(acc_email, msg_index): None for acc_email, msg_index in message_refs if int(msg_index) >= 0}
        deadline = time.monotonic() + (max(0, int(timeout_ms)) / 1000.0)
        while pending and time.monotonic() < deadline:
            completed: list[tuple[str, int]] = []
            for acc_email, msg_index in list(pending.keys()):
                message = GLOBAL_CACHE.ShMem.GetInbox(msg_index)
                is_same_message = (
                    bool(getattr(message, "Active", False))
                    and str(getattr(message, "ReceiverEmail", "") or "") == acc_email
                    and str(getattr(message, "SenderEmail", "") or "") == my_email
                    and int(getattr(message, "Command", -1)) == int(command)
                )
                if not is_same_message:
                    completed.append((acc_email, msg_index))
            for key in completed:
                pending.pop(key, None)
            if pending:
                yield from Routines.Yield.wait(50)
        if pending:
            ConsoleLog(BOT_NAME, f"[Merchant] {stage_name}: timeout waiting for alts", Py4GW.Console.MessageType.Warning)

    merchant_xy = _find_npc_xy_by_name("Merchant")
    mat_xy = _find_npc_xy_by_name("Material Trader") if _merchant_sell_materials else None
    rare_xy = _find_npc_xy_by_name("Rare") if (_merchant_buy_ectos or _merchant_sell_rare_mats) else None
    rare_mat_models = {935, 936}
    rare_mat_filter = "935,936"
    crafting_mat_models = {
        int(_ModelID.Pile_Of_Glittering_Dust.value),
        int(_ModelID.Bone.value),
        int(_ModelID.Iron_Ingot.value),
        int(_ModelID.Feather.value),
        int(_ModelID.Plant_Fiber.value),
    }
    crafting_mat_filter = ",".join(str(mid) for mid in sorted(crafting_mat_models))
    scroll_model_filter = "5594,5595,5611,5853,5975,5976,21233"

    if _merchant_store_consumable_materials:
        deposit_refs = _dispatch_to_alts(
            SharedCommandType.MerchantMaterials,
            (0, 0, 0, 0),
            ("deposit", crafting_mat_filter, "", "0"),
        )
        yield from _coro_deposit_crafting_materials_to_storage(crafting_mat_models)
        yield from _wait_for_alt_dispatch_completion("deposit_materials", deposit_refs, SharedCommandType.MerchantMaterials)

    if _merchant_sell_materials and mat_xy:
        tmx, tmy = mat_xy
        sell_mat_refs = _dispatch_to_alts(SharedCommandType.MerchantMaterials, (tmx, tmy, 0, 0), ("sell", "", "", ""))
        yield from Routines.Yield.Merchant.SellMaterialsAtTrader(tmx, tmy)
        yield from _wait_for_alt_dispatch_completion("sell_materials", sell_mat_refs, SharedCommandType.MerchantMaterials)

        if merchant_xy:
            mx, my = merchant_xy
            leftover_refs = _dispatch_to_alts(
                SharedCommandType.MerchantMaterials,
                (mx, my, 0, 0),
                ("sell_merchant_leftovers", "", "10", ""),
            )
            leftover_ids = _get_leftover_material_item_ids()
            if leftover_ids:
                yield from bot.Move._coro_xy_and_interact_npc(mx, my, "GH Merchant (leftovers)")
                yield from Routines.Yield.wait(1200)
                yield from Routines.Yield.Merchant.SellItems(leftover_ids, log=True)
                yield from Routines.Yield.wait(300)
            yield from _wait_for_alt_dispatch_completion("sell_merchant_leftovers", leftover_refs, SharedCommandType.MerchantMaterials)

    if merchant_xy:
        mx, my = merchant_xy
        sell_gold_refs = _dispatch_to_alts(SharedCommandType.MerchantMaterials, (mx, my, 0, 0), ("sell_nonsalvageable_golds", "", "", ""))
        yield from _coro_sell_nonsalvageable_golds(mx, my)
        yield from _wait_for_alt_dispatch_completion("sell_nonsalvageable_golds", sell_gold_refs, SharedCommandType.MerchantMaterials)

        sell_scroll_refs = _dispatch_to_alts(SharedCommandType.MerchantMaterials, (mx, my, 0, 0), ("sell_scrolls", scroll_model_filter, "", ""))
        yield from _coro_sell_scrolls(mx, my)
        yield from _wait_for_alt_dispatch_completion("sell_scrolls", sell_scroll_refs, SharedCommandType.MerchantMaterials)

        kit_refs = _dispatch_to_alts(SharedCommandType.MerchantItems, (mx, my, _merchant_id_kits_target, _merchant_salvage_kits_target))
        yield from bot.Move._coro_xy_and_interact_npc(mx, my, "GH Merchant")
        yield from Routines.Yield.wait(1200)
        id_kits = _count_model_in_inventory(_ModelID.Identification_Kit.value)
        sup_id_kits = _count_model_in_inventory(_ModelID.Superior_Identification_Kit.value)
        salvage_kits = _count_model_in_inventory(_ModelID.Salvage_Kit.value)
        id_to_buy = max(0, _merchant_id_kits_target - (id_kits + sup_id_kits))
        salvage_to_buy = max(0, _merchant_salvage_kits_target - salvage_kits)
        yield from Routines.Yield.Merchant.BuyIDKits(id_to_buy, log=True)
        yield from Routines.Yield.Merchant.BuySalvageKits(salvage_to_buy, log=True)
        yield from _wait_for_alt_dispatch_completion("restock_kits", kit_refs, SharedCommandType.MerchantItems)

    if _merchant_sell_rare_mats and rare_xy:
        rx, ry = rare_xy
        rare_refs = _dispatch_to_alts(SharedCommandType.MerchantMaterials, (rx, ry, 0, 0), ("sell", rare_mat_filter, "", "1"))
        yield from _coro_sell_rare_mats_at_trader(rx, ry, rare_mat_models)
        yield from _wait_for_alt_dispatch_completion("sell_rare_mats", rare_refs, SharedCommandType.MerchantMaterials)

    if _merchant_buy_ectos and rare_xy:
        rx, ry = rare_xy
        buy_refs = _dispatch_to_alts(
            SharedCommandType.MerchantMaterials,
            (rx, ry, _merchant_ecto_threshold, _merchant_ecto_threshold),
            ("buy_ectoplasm", "1", "0", ""),
        )
        leader_storage = int(GLOBAL_CACHE.Inventory.GetGoldInStorage())
        if leader_storage > _merchant_ecto_threshold:
            yield from Routines.Yield.Merchant.BuyEctoplasm(
                rx, ry,
                use_storage_gold=True,
                start_threshold=_merchant_ecto_threshold,
                stop_threshold=_merchant_ecto_threshold,
            )
        yield from _wait_for_alt_dispatch_completion("buy_ectoplasm", buy_refs, SharedCommandType.MerchantMaterials)

    if _merchant_alt_wait_ms > 0:
        yield from Routines.Yield.wait(_merchant_alt_wait_ms)

    yield


# --- Combat, Chest, and Quest Targeting Helpers ---

def command_type_routine_in_message_is_active(account_email, shared_command_type):
    """Checks if a multibox command is active for an account"""
    index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)
    if index == -1 or message is None:
        return False
    if message.Command != shared_command_type:
        return False
    return True


def _open_bogroot_chest():
    """Multibox coordination for opening the final chest"""
    ConsoleLog(BOT_NAME, "Opening final chest with multibox...")
    yield from Routines.Yield.Agents.TargetNearestGadgetXY(CHEST_POSITION[0], CHEST_POSITION[1], 500)
    target = Player.GetTargetID()
    if target == 0:
        ConsoleLog(BOT_NAME, "No chest found!")
        return
    
    sender_email = Player.GetAccountEmail()
    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    
    
    # --- LEADER: interact first ---
    Player.Interact(target, False)
    yield from Routines.Yield.wait(100)


    # Wait for the leader to finish
    while command_type_routine_in_message_is_active(sender_email, SharedCommandType.InteractWithTarget):
        yield from Routines.Yield.wait(250)
    while command_type_routine_in_message_is_active(sender_email, SharedCommandType.PickUpLoot):
        yield from Routines.Yield.wait(1000)
    yield from Routines.Yield.wait(5000)
    
    # Command opening for all members
    for account in accounts:
        if not account.AccountEmail or sender_email == account.AccountEmail:
            continue
        ConsoleLog(BOT_NAME, f"Ordering {account.AccountEmail} to open chest")
        GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.InteractWithTarget, (target, 0, 0, 0))
        while command_type_routine_in_message_is_active(account.AccountEmail, SharedCommandType.InteractWithTarget):
            yield from Routines.Yield.wait(1000)
        while command_type_routine_in_message_is_active(account.AccountEmail, SharedCommandType.PickUpLoot):
            yield from Routines.Yield.wait(1000)
        yield from Routines.Yield.wait(5000)
    
    ConsoleLog(BOT_NAME, "ALL accounts opened chest!")
    yield


def _use_summons():
    """
    Uses only ONE summon with priority:
    1. Summons (30209)
    2. Legionnary Crystal (37810)
    """

    summons = [
        ("Tengu", 30209),
        ("Legionnary Crystal", 37810),
    ]

    for name, model_id in summons:
        ConsoleLog("UseSummons", f"Searching for {name}...", log=True)

        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)

        if item_id:
            ConsoleLog("UseSummons", f"{name} found (item_id: {item_id}), using...", log=True)
            GLOBAL_CACHE.Inventory.UseItem(item_id)
            yield from Routines.Yield.wait(1000)
            ConsoleLog("UseSummons", f"{name} used!", log=True)

            yield
            return  # STOP ici → on ne teste pas le second

        else:
            ConsoleLog("UseSummons", f"{name} not found in inventory", log=True)

    ConsoleLog("UseSummons", "No summon found", log=True)
    yield

def _loop_marker():
    """Empty marker for loop restart point"""
    ConsoleLog(BOT_NAME, "Starting new dungeon run...")
    yield

def _search_and_talk_with_tekks(bot: Botting):
    npc_name = "Tekks"

    ConsoleLog(BOT_NAME, "[Tekks] Start quest take", log=True)

    for attempt in range(1, 21):
        ConsoleLog(BOT_NAME, f"[Tekks] Search {npc_name} attempt {attempt}/20", log=True)

        agent_id = yield from Yield.Agents.GetAgentIDByName(npc_name)

        if agent_id:
            ConsoleLog(BOT_NAME, f"[Tekks] Found {npc_name} agent_id={agent_id}", log=True)

            x, y = Agent.GetXY(agent_id)
            ConsoleLog(BOT_NAME, f"[Tekks] Move to ({x}, {y})", log=True)

            for i in range(150):
                if i % 10 == 0:
                    Player.Move(x, y)

                px, py = Player.GetXY()
                dist = Utils.Distance((px, py), (x, y))

                if dist < 150:
                    ConsoleLog(BOT_NAME, "[Tekks] Arrived near Tekks", log=True)
                    break

                yield from Routines.Yield.wait(100)
            else:
                ConsoleLog(BOT_NAME, "[Tekks] Could not reach Tekks", log=True)
                yield
                return

            Player.ChangeTarget(agent_id)
            yield from Routines.Yield.wait(500)

            current_target = Player.GetTargetID()
            ConsoleLog(BOT_NAME, f"[Tekks] Current target = {current_target}", log=True)

            Player.Interact(agent_id)
            yield from Routines.Yield.wait(800)

            Player.ChangeTarget(agent_id)
            yield from Routines.Yield.wait(500)

            Player.Interact(agent_id)
            yield from Routines.Yield.wait(800)

            ConsoleLog(BOT_NAME, "[Tekks] Quest/Reward taken", log=True)
            yield
            return

        yield from Routines.Yield.wait(500)

# ==================== INITIALIZATION ====================
def _draw_bogroot_settings():
    PyImGui.text("Bogroot Settings")
    PyImGui.separator()
    _draw_difficulty_setting()
    _draw_merchant_settings()
    PyImGui.separator()
    PyImGui.text(f"Bot: {BOT_NAME}")
    PyImGui.text(f"Quest ID: {TEKKS_QUEST_ID}")
    PyImGui.text(f"Reward pending: {TEKKS_REWARD_PENDING}")

bot.SetMainRoutine(farm_froggy_routine)
bot.UI.override_draw_config(_draw_bogroot_settings)


# ==================== UI AND ENTRYPOINT ====================

def main():
    bot.Update()
    draw_window_sig = inspect.signature(bot.UI.draw_window)
    if "extra_tabs" in draw_window_sig.parameters:
        bot.UI.draw_window(icon_path=TEXTURE, main_child_dimensions=(400, 450))
    else:
        bot.UI.draw_window(icon_path=TEXTURE, main_child_dimensions=(400, 450))


if __name__ == "__main__":
    main()
