from collections.abc import Generator
import os
from typing import Any
import Py4GW
from Py4GWCoreLib import (
    Agent,
    AgentArray,
    Botting,
    ConsoleLog,
    GLOBAL_CACHE,
    IniHandler,
    Map,
    Player,
    Quest,
    Routines,
    SharedCommandType)
from Py4GWCoreLib.py4gwcorelib_src import Utils
from Py4GWCoreLib.routines_src.Yield import Yield
from Py4GW_widget_manager import get_widget_handler
from Py4GWCoreLib.botting_src.helpers import BottingHelpers
from Sources.oazix.CustomBehaviors.primitives.botting.botting_helpers import BottingHelpers
from Py4GWCoreLib.routines_src.Yield import Utils
# ==================== CONFIGURATION ====================
BOT_NAME = "Froggy Farm rezone"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "textures", "froggy.png")
WIDGETS_TO_ENABLE: tuple[str, ...] = (
    "LootManager",
    "CustomBehaviors",
    "ResurrectionScroll",
    "Return to outpost on defeat",
)
WIDGETS_TO_DISABLE: tuple[str, ...] = ()
_ALT_ONLY_DISABLE_WIDGETS: tuple[str, ...] = (os.path.splitext(os.path.basename(__file__))[0],)

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

def _mark_reward_not_taken():
    global TEKKS_REWARD_PENDING
    TEKKS_REWARD_PENDING = False
    yield

def _mark_reward_taken():
    global TEKKS_REWARD_PENDING
    TEKKS_REWARD_PENDING = True
    yield

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
    if map_id not in ("Bogroot Growths (level 1)", "Bogroot Growths (level 2)"):
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

from typing import Generator, Any

def TargetAndMoveToTekks(bot: Botting) -> Generator[Any, Any, None]:
    npc_name = "Tekks"

    ConsoleLog(BOT_NAME, "[TEST] TargetAndMoveToTekks -> start", log=True)

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

def _step_anchor() -> Generator:
    yield

def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))

# ==================== UTILITY FUNCTIONS ====================



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
    ok = yield from _interact_with_tekks(bot, TEKKS_QUEST_REWARD_DIALOG)
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


def command_type_routine_in_message_is_active(account_email, shared_command_type):
    """Checks if a multibox command is active for an account"""
    index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)
    if index == -1 or message is None:
        return False
    if message.Command != shared_command_type:
        return False
    return True


def open_bogroot_chest():
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


def UseSummons():
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

def loop_marker():
    """Empty marker for loop restart point"""
    ConsoleLog(BOT_NAME, "Starting new dungeon run...")
    yield

def Search_and_talk_with_Tekks(bot: Botting):
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

# ==================== MAIN ROUTINE ====================

def farm_froggy_routine(bot: Botting) -> None:
    # ===== INITIAL CONFIGURATION =====
    bot.Templates.Routines.UseCustomBehaviors(
        on_player_critical_death=BottingHelpers.botting_unrecoverable_issue,
        on_party_death=BottingHelpers.botting_unrecoverable_issue,
        on_player_critical_stuck=BottingHelpers.botting_unrecoverable_issue)
    #CustomBehaviorParty().set_party_is_enabled(True)
    widget_handler = get_widget_handler()
    widget_handler.enable_widget('Return to outpost on defeat')
    
    # Register wipe callback
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    
    # Enable properties
    bot.Properties.Enable('auto_combat')
    bot.States.AddCustomState(_step_anchor, "Reset farm")  # anchor for secure return on wipe    
    # ===== START OF BOT =====
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=MAP_GADDS_ENCAMPMENT)
    bot.States.AddCustomState(_reenable_merchant_widgets, "Re-enable merchant widgets")
    
    # ===== START OF LOOP =====
    bot.States.AddHeader(f"{BOT_NAME}_LOOP")
    bot.States.AddCustomState(loop_marker, "RUN_START_POINT")
    bot.Party.SetHardMode(True)
    bot.Properties.Enable('auto_combat')
    bot.Quest.AbandonQuest(TEKKS_QUEST_ID)
    # ===== GO TO DUNGEON =====
    bot.States.AddHeader("Go to Dungeon")
    bot.Templates.Aggressive()
    bot.Move.XYAndExitMap(-9451.37, -19766.40, target_map_id=MAP_SPARKFLY)
    bot.Wait.UntilOnExplorable()
    bot.Wait.ForTime(2000)
    
    # First blessing in Sparkfly
    bot.Move.XYAndInteractNPC(-8950.0, -19843.0)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)
    
    bot.States.AddCustomState(UseSummons, "UseSummons")
    
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



        # ===== LOOP RESTART POINT =====
    bot.States.AddCustomState(loop_marker, "LOOP_RESTART_POINT")


    # Take Tekks' quest
    bot.States.AddCustomState(lambda: Search_and_talk_with_Tekks(bot), "Find Tekks and talk")
    bot.Wait.ForTime(5000)
    bot.Multibox.SendDialogToTarget(TEKKS_QUEST_TAKE_DIALOG)
    bot.Wait.ForTime(4000)
    


    # Enter the dungeon
    bot.Move.XY(11676.01, 22685.0)
    bot.Move.XY(11562.77, 24059.0)
    bot.Move.XY(13097.0, 26393.0)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(2000)


    
    # ===== LEVEL 1 =====
    bot.States.AddHeader("Level 1")
    bot.Templates.Aggressive()
    bot.Templates.Aggressive()
    bot.Move.XY(18092.0, 4315.0)
    bot.Move.XY(19045.95, 7877.0)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(3000)
    
    # First blessing Level 1
    bot.Move.XYAndInteractNPC(19045.95, 7877.0)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)
    
    bot.States.AddHeader("Secure return - L1")
    bot.States.AddCustomState(_step_anchor, "Secure return - L1")

    # Use consumables
    bot.Multibox.UseAllConsumables()
    bot.Wait.ForTime(3000)
    bot.States.AddCustomState(UseSummons, "UseSummons")
    
    # Full path Level 1
    bot.Move.XY(16541.48, 8558.94)
    bot.Move.XY(13038.90, 7792.40)
    bot.Move.XY(11666.15, 6464.53)
    bot.Move.XY(10030.42, 7026.09)
    bot.Move.XY(9752.17, 8241.79) #freez xy33
    bot.Move.XY(8238.36, 7434.97) # test antifreeze
    bot.Move.XY(6491.41, 5310.56)

    bot.States.AddHeader("Secure return 2 - L1")
    bot.States.AddCustomState(_step_anchor, "Secure return 2 - L1")

    bot.Move.XY(5097.64, 2204.33)
    bot.Move.XY(1228.15, 54.49)
    bot.Wait.ForTime(8000)
    bot.Move.XY(-140.87, 2741.86)
    bot.Wait.ForTime(3000)
    bot.Move.XY(1228.15, 54.49)
    bot.Move.XY(141.23, -1965.14)
    bot.States.AddHeader("Secure return 3 - L1")
    bot.States.AddCustomState(_step_anchor, "Secure return 3 - L1")  # anchor for secure return on wipe


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
    
    # Wait for change to Level 2
    bot.Wait.ForMapToChange(target_map_name="Bogroot Growths (level 2)")
    
    # ===== LEVEL 2 =====
    bot.States.AddHeader("Level 2")
    bot.Templates.Aggressive()
    
    # Refresh consumables
    bot.Multibox.UseAllConsumables()
    bot.Wait.ForTime(3000)
    
    
    # Enter Level 2 and first blessing
    bot.Move.XY(-11055.0, -5551.0)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(3000)
    bot.Move.XYAndInteractNPC(-11055.0, -5551.0)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)

    bot.States.AddHeader("Secure return - L2")
    bot.States.AddCustomState(_step_anchor, "Secure return - L2")
    
    # Path to second blessing
    bot.Move.XY(-11522.0, -3486.0)
    bot.Move.XY(-10639.0, -4076.0)
    bot.Move.XY(-11321.0, -5033.0)
    bot.Move.XY(-11268.0, -3922.0)
    bot.Move.XY(-11187.0, -2190.0)
    bot.Move.XY(-10706.0, -1272.0)
    bot.Move.XY(-10535.0, -191.0)
    bot.Move.XY(-10262.0, -1167.0)
    bot.Wait.ForTime(8000)
    bot.States.AddCustomState(UseSummons, "UseSummons")
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
    
    # Second blessing
    bot.Move.XYAndInteractNPC(-955.0, 10984.0)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)

    bot.States.AddHeader("Secure return 2 - L2")
    bot.States.AddCustomState(_step_anchor, "Secure return 2 - L2")

    # Path to Patriarch's blessing
    bot.Move.XY(216.0, 11534.0)
    bot.Move.XY(1485.0, 12022.0)
    bot.Move.XY(2690.0, 12615.0)
    bot.Wait.ForTime(4000)
    bot.Move.XY(3343.0, 13721.0)
    bot.Move.XY(4693.0, 13577.0)
    bot.Move.XY(5693.0, 12927.0)
    bot.Move.XY(5942.0, 11067.0)
    bot.Move.XY(6878.0, 9657.0) #xy81
    bot.Wait.ForTime(8000) #here
    bot.Move.XY(8100.54, 8544.52)#a moddif  old
    bot.Move.XY(8725.26, 7115.42)# a modif  old (7485.0, 6406.0)
    bot.Move.XY(9234.03, 6843.0)
    bot.Move.XY(8591.0, 4285.0)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(3000)
    
    # Patriarch's blessing
    bot.Move.XYAndInteractNPC(8591.0, 4285.0)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)
    
    bot.States.AddHeader("Secure return 3 - L2")
    bot.States.AddCustomState(_step_anchor, "Secure return 3 - L2")

    # Path to boss door
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
    bot.Move.XY(16461.0, -6041.0)#here boss and key
    bot.Move.XY(16389.50, -4090.36)
    bot.Move.XY(15309.36, -2904.08)
    bot.Move.XY(14357.81, -5818.01)
    bot.Move.XY(16461.0, -6041.0)#here boss and key
    bot.Move.XY(17565.0, -6227.0)
    bot.Wait.UntilOutOfCombat()
    
    # Open boss door
    ConsoleLog(BOT_NAME, "Opening boss door...")
    bot.Move.XYAndInteractGadget(17867.55, -6250.63)
    bot.Wait.ForTime(2000)
    bot.Move.XYAndInteractGadget(17867.55, -6250.63)
    bot.Wait.ForTime(2000)
    ConsoleLog(BOT_NAME, "Door should be open!")
    bot.Wait.ForTime(1000)
    
    # Path to final blessing
    bot.Move.XY(17623.87, -6546.0)
    bot.Move.XY(18024.0, -9191.0)
    bot.Move.XY(17110.0, -9842.0)
    bot.Move.XY(15867.0, -10866.0)
    bot.Move.XY(17555.0, -11963.0)
    bot.Move.XY(18761.0, -12747.0)
    bot.Move.XY(19619.0, -11498.0)
    bot.Wait.UntilOutOfCombat()
    
    # Final blessing
    bot.Templates.Aggressive()
    bot.Move.XYAndInteractNPC(19619.0, -11498.0)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)
    bot.States.AddHeader("Secure return - Boss")
    bot.States.AddCustomState(_step_anchor, "Secure return - Boss")


    # ===== BOSS FIGHT =====
    bot.States.AddHeader("Boss Fight")
    bot.Templates.Aggressive()
    bot.Move.XY(17582.52, -14231.0)
    bot.Move.XY(14794.47, -14929.0)
    bot.Move.XY(13609.12, -17286.0)
    bot.Move.XY(14079.80, -17776.0)
    bot.Move.XY(15116.40, -18733.0)
    bot.Move.XY(15914.68, -19145.53)
    bot.Wait.UntilOutOfCombat()
    
    # ===== CHEST =====
    bot.Move.XY(15030.00, -19168.00)
    bot.States.AddCustomState(open_bogroot_chest, "Open chest with all accounts")


    # ===== REWARD =====
    bot.States.AddHeader("End / Reward")
    bot.States.AddCustomState(lambda: Search_and_talk_with_Tekks(bot), "Find Tekks and talk")
    bot.Wait.ForTime(5000)
    bot.Multibox.SendDialogToTarget(TEKKS_QUEST_REWARD_DIALOG)
    bot.Wait.ForTime(4000)
    bot.States.AddCustomState(_verify_reward_taken_from_quest_log, "Verify reward from quest log")


    # ===== NEXT RUN =====
    bot.Wait.ForMapToChange(target_map_name="Sparkfly Swamp")
    bot.States.AddCustomState(lambda: _post_return_flow(bot), "Post-return quest handling")
    
    # ===== LOOP =====
    bot.States.JumpToStepName("LOOP_RESTART_POINT")


# ==================== INITIALIZATION ====================

bot.SetMainRoutine(farm_froggy_routine)
bot.UI.override_draw_config(_draw_bogroot_settings)


# ==================== MAIN ====================

def main():
    bot.Update()
    draw_window_sig = inspect.signature(bot.UI.draw_window)
    if "extra_tabs" in draw_window_sig.parameters:
        bot.UI.draw_window(icon_path=TEXTURE, main_child_dimensions=(400, 450))
    else:
        bot.UI.draw_window(icon_path=TEXTURE, main_child_dimensions=(400, 450))


if __name__ == "__main__":
    main()
