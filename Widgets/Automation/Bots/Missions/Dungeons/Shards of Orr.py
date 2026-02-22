import os
from typing import Generator, Optional, Tuple, List
import time, math
import PyInventory

import Py4GW
from Py4GWCoreLib import (
    Agent,
    Botting,
    ConsoleLog,
    GLOBAL_CACHE,
    Map,
    Player,
    Routines,
    SharedCommandType,
    AgentArray,  # Added import for AgentArray
)
from Py4GW_widget_manager import get_widget_handler

# ==================== CONFIGURATION ====================
BOT_NAME = "BDS Farm rezone"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots","Froggy","bds.png")

# Map IDs
Vloxs_Fall = 624
Arbor_Bay = 485
SoO_lvl1 = 581
SoO_lvl2 = 582
SoO_lvl3 = 583
Great_Temple_of_Balthazar = 248
EyeOfTheNorth = 642

# Dialog IDs
DWARVEN_BLESSING_DIALOG = 0x84
SHANDRA_TAKE_DIALOGS = 0x832401
SHANDRA_QUEST_REWARD_DIALOG = 0x832407

# Coordinates
FENDI_CHEST_POSITION = (-15800.98,16901.23)
SHANDRA_POSITION = (14067.01, -17253.24)

# ==================== GLOBAL VARIABLES ====================
bot = Botting(
    bot_name=BOT_NAME,
    upkeep_auto_combat_active=True,
    upkeep_auto_loot_active=True,
    upkeep_hero_ai_active=True,
)

# ==================== UTILITY FUNCTIONS ====================

BDS_L2_PART1 = [
    (-11303, -14596),  # allumage torche (premier brasier)
    (-11019, -11550),
    (-9028,  -9021),
    (-6805,  -11511),
    (-8984,  -13842),
]


BDS_L2_PART2 = [
    (-3717, -4254),
    (-8251, -3240),
    (-8278, -1670),
]
BDS_L3 = [
    (15692, 17111),
    (12969, 19842),
    (8236,  16950),
    (5549,  9920),
    (-536,  6109),
    (-3814, 5599),
    (-4959, 7558),
    (-7532, 4536),
    (-11044, 482),
    (-12621, 2948),
]


def command_type_routine_in_message_is_active(account_email, shared_command_type):
    """Checks if a multibox command is active for an account"""
    index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)
    if index == -1 or message is None:
        return False
    if message.Command != shared_command_type:
        return False
    return True


def debug_item_signature(max_dist: float = 2500.0) -> Generator:
    agents = AgentArray.GetItemArray()
    agents = AgentArray.Filter.ByDistance(agents, Player.GetXY(), max_dist)
    agents = AgentArray.Sort.ByDistance(agents, Player.GetXY())

    ConsoleLog(BOT_NAME, f"[DBG] items_near={len(agents)}")

    for i, a in enumerate(agents[:10]):
        it = Agent.GetItemAgentByID(int(a))
        if not it:
            continue
        ConsoleLog(
            BOT_NAME,
            f"[DBG] #{i} agent_id={a} item_id={it.item_id} extra_type={it.extra_type} h00CC={hex(int(it.h00CC))}"
        )
        yield from Routines.Yield.wait(50)

    yield


def _wait_end_dungeon() -> Generator:
    ConsoleLog(BOT_NAME,"[WAIT] Waiting for dungeon end teleport")

    timeout = time.time() + 180
    while True:
        if Map.GetMapID() == Arbor_Bay:
            ConsoleLog(BOT_NAME,"[WAIT] Teleported to Arbor Bay")
            yield
            return

        if time.time() > timeout:
            ConsoleLog(BOT_NAME,"[WAIT] Timeout waiting for Arbor Bay teleport")
            yield
            return

        yield from Routines.Yield.wait(500)


INTERACTABLE_TYPES = {0x200, 0x400}  # coffres / portes / brasiers (comme ton AutoIt)


try:
    from Py4GWCoreLib import Item
except Exception:
    Item = None

TORCH_MODEL_IDS = {22341, 22342}
PICKUP_DIST = 180.0
MOVE_TIMEOUT_MS = 9000

def _dist(ax: float, ay: float, bx: float, by: float) -> float:
    return math.hypot(ax - bx, ay - by)

def pickup_torch(max_scan_dist: float = 5000, attempts: int = 40) -> Generator:
    inv = PyInventory.PyInventory()
    me = int(Player.GetAgentID())

    ConsoleLog("TORCH", "scan+pickup start")

    for _ in range(attempts):
        arr = AgentArray.GetItemArray()
        arr = AgentArray.Filter.ByDistance(arr, Player.GetXY(), max_scan_dist)
        arr = AgentArray.Sort.ByDistance(arr, Player.GetXY())

        target_agent: int = 0
        ground_item_id: int = 0  # <-- LE vrai ItemId au sol (toolbox)

        for a in arr:
            aid = int(a)
            it = Agent.GetItemAgentByID(aid)
            if not it:
                continue

            # filtre loot groupe si owner est exploitable
            try:
                owner = int(it.owner)
                if owner not in (0, me):
                    continue
            except Exception:
                pass

            try:
                gid = int(Agent.GetItemAgentItemID(aid))  # <-- IMPORTANT
            except Exception:
                continue

            mid: Optional[int] = None
            if Item is not None:
                try:
                    m = Item.GetModelID(gid)
                    mid = int(m) if isinstance(m, int) else None
                except Exception:
                    mid = None

            ConsoleLog("TORCH", f"cand agent={aid} ground_item_id={gid} model_id={mid}")

            if mid in TORCH_MODEL_IDS:
                target_agent = aid
                ground_item_id = gid
                break

        if not target_agent:
            yield from Routines.Yield.wait(150)
            continue

        tx, ty = Agent.GetXY(target_agent)

        # Approche
        try:
            Player.Move(tx, ty)
        except Exception:
            pass

        start = time.time() * 1000
        while True:
            px, py = Player.GetXY()
            if _dist(px, py, tx, ty) <= PICKUP_DIST:
                break
            if (time.time() * 1000) - start > MOVE_TIMEOUT_MS:
                ConsoleLog("TORCH", "cant reach -> retry")
                target_agent = 0
                break
            yield from Routines.Yield.wait(100)

        if not target_agent:
            continue

        # Ciblage + pickup
        Player.ChangeTarget(target_agent)
        yield from Routines.Yield.wait(120)

        ConsoleLog("TORCH", f"PickUpItem ground_item_id={ground_item_id}")
        inv.PickUpItem(ground_item_id, True)  # True = call_target (souvent nécessaire)
        yield from Routines.Yield.wait(900)
        yield
        return

    ConsoleLog("TORCH", "❌ pickup failed")
    yield



def nearest_from_array(arr: List[int], max_dist: float) -> int:
    arr = AgentArray.Filter.ByDistance(arr, Player.GetXY(), max_dist)
    arr = AgentArray.Sort.ByDistance(arr, Player.GetXY())
    return int(arr[0]) if len(arr) > 0 else 0


def interact_nearest_gadget(max_dist: float = 220.0) -> Generator:
    gadgets = AgentArray.GetGadgetArray()
    gad_id = nearest_from_array(gadgets, max_dist)
    if not gad_id:
        ConsoleLog(BOT_NAME, f"❌ No gadget within {max_dist}")
        yield
        return

    ConsoleLog(BOT_NAME, f"[BRAZIER] gadget={gad_id} → interact x2")
    Player.ChangeTarget(gad_id)
    yield from Routines.Yield.wait(150)

    Player.Interact(gad_id, False)
    yield from Routines.Yield.wait(100)
    Player.Interact(gad_id, False)
    yield from Routines.Yield.wait(100)

    yield


def run_brazier_sequence(points: list[tuple[float,float]], interact_dist: float = 200.0) -> None:
    for idx, (x, y) in enumerate(points, 1):
        bot.Move.XY(x, y)
        bot.Wait.UntilOutOfCombat()
        bot.Wait.ForTime(250)
        bot.States.AddCustomState(lambda d=interact_dist: interact_nearest_gadget(d), f"Interact nearest ({idx})")
        bot.Wait.ForTime(350)


def open_fendi_chest():
    """Multibox coordination for opening the final chest"""
    ConsoleLog(BOT_NAME, "Opening final chest with multibox...")
    yield from Routines.Yield.Agents.TargetNearestGadgetXY(FENDI_CHEST_POSITION[0], FENDI_CHEST_POSITION[1], 500)
    target = Player.GetTargetID()
    if target == 0:
        ConsoleLog(BOT_NAME, "No chest found!")
        return
    
    sender_email = Player.GetAccountEmail()
    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    
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

def wait_for_map_change(target_map_id, timeout_seconds=60):
    """Wait for map change with timeout"""
    ConsoleLog(BOT_NAME, f"Waiting for map change to {target_map_id}...")
    timeout = time.time() + timeout_seconds
    while True:
        current_map = Map.GetMapID()
        if current_map == target_map_id:
            ConsoleLog(BOT_NAME, f"Map change detected! Now in map {target_map_id}")
            yield
            return
        if time.time() > timeout:
            ConsoleLog(BOT_NAME, f"Timeout waiting for map {target_map_id}")
            yield
            return
        yield from Routines.Yield.wait(500)



def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            bot.config.FSM.resume()
            return
        bot.States.JumpToStepName("[H]Combat_3")

    bot.config.FSM.resume()

_WIPE_HANDLER_RUNNING = False

def OnPartyWipe(bot: "Botting"):
    global _WIPE_HANDLER_RUNNING
    if _WIPE_HANDLER_RUNNING:
        return
    _WIPE_HANDLER_RUNNING = True

    ConsoleLog("on_party_wipe", "party wipe detected")
    fsm = bot.config.FSM
    fsm.pause()

    def _wrapped():
        global _WIPE_HANDLER_RUNNING
        try:
            yield from _on_party_wipe(bot)
        finally:
            _WIPE_HANDLER_RUNNING = False

    fsm.AddManagedCoroutine("OnWipe_OPD", _wrapped)

    
    
def UseTengu():
    """Uses Tengu (item ID 30209)"""
    ConsoleLog("UseTengu", "Searching for Tengu...", log=True)
    
    item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(30209)
    
    if item_id:
        ConsoleLog("UseTengu", f"Tengu found (item_id: {item_id}), using...", log=True)
        GLOBAL_CACHE.Inventory.UseItem(item_id)
        yield from Routines.Yield.wait(1000)
        ConsoleLog("UseTengu", "Tengu used!", log=True)
    else:
        ConsoleLog("UseTengu", "Tengu not found in inventory", log=True)
    
    yield    


def loop_marker():
    """Empty marker for loop restart point"""
    ConsoleLog(BOT_NAME, "Starting new dungeon run...")
    yield


# ==================== MAIN ROUTINE ====================

def farm_bds_routine(bot: Botting) -> None:
    # ===== INITIAL CONFIGURATION =====
    widget_handler = get_widget_handler()
    widget_handler.enable_widget('HeroAI')
    widget_handler.enable_widget('Return to outpost on defeat')
    
    # Register wipe callback
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(lambda *args, **kwargs: OnPartyWipe(bot))
    

    
    # ===== START OF BOT =====
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=Vloxs_Fall)
    
    # ===== START OF LOOP =====
    bot.States.AddHeader(f"{BOT_NAME}_LOOP")
    bot.Party.SetHardMode(True)
    # Enable properties
    bot.Properties.Enable('auto_combat')
    bot.Properties.Enable('hero_ai')
    
    # ===== GO TO DUNGEON =====
    bot.States.AddHeader("Go to Dungeon")
    bot.Move.XYAndExitMap(15505.38, 12460.59, target_map_id=Arbor_Bay)
    bot.Wait.UntilOnExplorable()
    bot.Wait.ForTime(2000)
    
    # First blessing in Arbor Bay
    bot.Move.XYAndInteractNPC(16327, 11607)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)
    
    # Use consumables
    bot.Multibox.UseAllConsumables()
    bot.Wait.ForTime(3000)
    bot.States.AddCustomState(UseTengu, "Use Tengu")

    IS_REPATHING = False
    # Path to Shandra
    path = [
    (13455.43, 10678.00),
    (9850.00, 5025.00),
    (11256.59, 1742.31),
    (11736.00, 70.00),
    (10782.86, -3321.00),
    (8360.94, -6550.00),
    (10382.85, -12342.00),
    (10080.30, -13995.00),
    (10667.00, -16116.00),
    (10747.49, -17546.00),
    (11156.00, -17802.00),
]

    bot.Templates.Multibox_Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path)
    bot.Wait.UntilOutOfCombat()
    

    
    # Take Shandra' quest
    bot.Move.XYAndInteractNPC((12056.00,-17882)[0], (12056.00,-17882)[1])
    bot.Multibox.SendDialogToTarget(SHANDRA_TAKE_DIALOGS)
    bot.Wait.ForTime(4000)
    
    # Enter the dungeon
    bot.Move.XY(11177, -17683)
    bot.Move.XY(10218, -18864)
    bot.Move.XY(9519, -19968)
    bot.Move.XY(9240.07, -20260.95)

    # Wait for change to Level 1
    bot.States.AddCustomState(lambda: wait_for_map_change(SoO_lvl1, 60), "Wait for Level 1")
    bot.Wait.ForTime(2000)
    
    # ===== LOOP RESTART POINT =====
    bot.States.AddCustomState(loop_marker, "LOOP_RESTART_POINT")


    
    # First blessing Level 1
    bot.Move.XY(-11686, 10427)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(3000)
    bot.Move.XYAndInteractNPC(-11686, 10427)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)
    
    # Use consumables
    bot.Multibox.UseAllConsumables()
    bot.Wait.ForTime(3000)
    bot.States.AddCustomState(UseTengu, "Use Tengu")
    

    bot.States.AddHeader("Level 1 - Path before door")
    # Full path Level 1
    path_before_door = [
        (-10486.00, 9587.00),
        (-6196.00, 10260.00),
        (-3819.00, 11737.00),
        (-1123.00, 13649.00),
        (2734.00, 16041.00),
        (3877.00, 14790.00),
        (5569.52, 13057.00),
        (6780.00, 13039.00),
        (8056.00, 12349.00),
        (9232.00, 11483.00),
        (6799.00, 11264.00),
        (11298.00, 13891.00),
        (13255.00, 15175.00),
        (15935.00, 17304.00),
        (17161.00, 13551.00),
        (16100.00, 11992.00),
        (15637.00, 9493.00),
        (14287.00, 7751.00),
        (14130.00, 6263.00),
    ]

    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_before_door)

    bot.Wait.UntilOutOfCombat()

    bot.Move.XY(15100, 5443)
    bot.Move.XYAndInteractGadget(15100.00, 5443)

    bot.Templates.Multibox_Aggressive()


    # ===== LEVEL 1 =====
    bot.States.AddHeader("Level 1 - Path after door")
    path_after_door = [
    (15331.00, 4637.00),
    (16494.00, 2662.00),
    (18270.00, 1439.00),
    (19812.00, 902.00),
    (20000.00, 950.00),
    (20400.00, 1300.00),
]


    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_after_door)

    bot.Wait.UntilOutOfCombat()

    # Wait for change to Level 2
    bot.States.AddCustomState(lambda: wait_for_map_change(SoO_lvl2, 60), "Wait for Level 2")
    bot.Wait.ForTime(2000)
    

    bot.States.AddHeader("Level 2 - First blessing and cleaning")
    # Enter Level 2 and first blessing
    bot.Move.XY(-14076, -19457)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(3000)
    bot.Move.XYAndInteractNPC(-14076, -19457)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)
    

    # Use consumables
    bot.Multibox.UseAllConsumables()
    bot.Wait.ForTime(3000)
    bot.States.AddCustomState(UseTengu, "Use Tengu")

    # Path to second blessing
    path_before_torch = [
    (-14050.64, -18215.56),
    (-14215.00, -17456.00),
    (-16191.00, -16740.00),
]


    bot.Templates.Multibox_Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_before_torch)
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("Level 2 - Open Torch Chest and take torch")
    # Open torch chest and take torch
    bot.Move.XYAndInteractGadget(-14709, -16548)
    bot.Items.AddModelToLootWhitelist(22342)  # ID de la torche
    bot.States.AddCustomState(pickup_torch, "Pickup Torch (if any)")   # si tu veux

    bot.States.AddHeader("Level 2 - Go to first brazier sequence")
    bot.Move.XY(-9259, -17322)
    bot.Wait.ForTime(1000)
    bot.Move.XY(-11303, -14596)
    bot.Wait.ForTime(1000)

    bot.States.AddHeader("Level 2 - Brazier sequence")
    run_brazier_sequence([(float(x), float(y)) for x, y in BDS_L2_PART1])
    bot.Items.RemoveModelFromLootWhitelist(22342)
    bot.UI.Keybinds.DropBundle()

    bot.States.AddHeader("Level 2 - Path first room")
    path_first_room = [
    (-9358.00, -12411.00),
    (-10143.00, -11136.00),
    (-8871.00, -9951.00),
    ]
    bot.Templates.Multibox_Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_first_room)
    bot.Wait.UntilOutOfCombat()
    bot.Items.AddModelToLootWhitelist(22342)  # ID de la torche
    bot.States.AddCustomState(pickup_torch, "Pickup Torch (if any)")   # si tu veux

    bot.States.AddHeader("Level 2 - Path after first room")
    path_after_first_room = [
     (-7722.00, -11522.00),
    (-11043.00, -7750.00),
    (-11058.00, -4487.00),
    (-6721.00, -4209.00),
    (-6531.00, -3469.00),
]
    bot.Items.AddModelToLootWhitelist(22342)  # ID de la torche
    pickup_torch()
    bot.Templates.Multibox_Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_after_first_room)
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("Level 2 - Brazier sequence")
    run_brazier_sequence([(float(x), float(y)) for x, y in BDS_L2_PART2])
    bot.Items.RemoveModelFromLootWhitelist(22342)    
    bot.UI.Keybinds.DropBundle()


    bot.States.AddHeader("Level 2 - Go to door of level 3")
    path_after_second_room = [
    (-6848.8,-4313.4),
    (-7850.0,-4316.8),
    (-8857.9,-4366.6),
    (-9865.0,-4405.9),
    (-10870.9,-4310.3),
    (-11885.0,-3916.0),
    (-12896.7,-3566.4),
    (-13903.8,-3524.7),
    (-14911.5,-4531.2),
    (-15827.1,-5535.1),
    (-15760.5,-6545.4),
    (-15862.0,-7561.2),
    (-16092.1,-8564.9),
    (-18725, -9171),
    ]

    bot.Templates.Multibox_Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_after_second_room)
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("Level 2 - Open door to Level 3")

    bot.Move.XY(-18725, -9171)
    bot.Move.XYAndInteractGadget(-18725, -9171)
    bot.Move.XY(-19500, -8500)
    # Wait for change to Level 3
    bot.States.AddCustomState(lambda: wait_for_map_change(SoO_lvl3, 60), "Wait for Level 3")
    bot.Wait.ForTime(2000)


    bot.Move.XY(17544, 18810)
    bot.Wait.UntilOutOfCombat()
    bot.Wait.ForTime(3000)
    bot.Move.XYAndInteractNPC(17544, 18810)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)

    bot.States.AddHeader("Level 3 - Cleaning")

    # Use consumables
    bot.Multibox.UseAllConsumables()
    bot.Wait.ForTime(3000)
    bot.States.AddCustomState(UseTengu, "Use Tengu")
    path_before_brazier_sequence = [
    (17544.00, 18810.00),
    (9452.00, 18513.00),
    (8908.00, 17239.00),
    (6527.00, 12936.00),
    (3025.00, 8401.00),
    (949.00, 7412.00),
    (-347.00, 6459.00),
    (-1265.00, 7891.00),
    (-5923.93, 6006.00),
    (-7993.65, 4588.00),
    ]
    bot.Templates.Multibox_Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_before_brazier_sequence)
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("Level 3 - Go to torch chest")
    path_to_take_torch = [
    (-10192.24, 3092.00),
    (-4723.00, 6703.00),
    (-1280.00, 7880.00),
    (3089.73, 8511.00),
    (4963.00, 9974.00),
    (9918.64, 19108.00),
    (14709.00, 19526.00),
    (16111.00, 17556.00),
    ]


    bot.Templates.Multibox_Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_to_take_torch)
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("Level 3 - Open Torch Chest and take torch")
    # Open torch chest and take torch
    bot.Move.XYAndInteractGadget(16111.00, 17556)
    bot.Items.AddModelToLootWhitelist(22342)  # ID de la torche
    bot.States.AddCustomState(pickup_torch, "Pickup Torch (if any)")   # si tu veux
    bot.Wait.ForTime(2000)
    
    bot.States.AddHeader("Level 3 - Brazier sequence")    
    run_brazier_sequence([(float(x), float(y)) for x, y in BDS_L3])
    bot.Items.RemoveModelFromLootWhitelist(22342)  # ID de la torche
    bot.UI.Keybinds.DropBundle()

    path_before_boss_door = [
    (-10637.00, 2904.00),
    (-9806.00, 2370.00),
]
    bot.Templates.Multibox_Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_before_boss_door)
    bot.Wait.UntilOutOfCombat()

    bot.States.AddCustomState(lambda: bot.Move.XY(-9252.32, 6396.40), "Move to Boss Door")
    bot.Move.XYAndInteractGadget(-9252.32, 6396.40)
    bot.Wait.ForTime(1000)

    bot.States.AddHeader("Boss fight")
    # ===== BOSS FIGHT =====
    path_bds = [
    (-9926.00, 8007.00),
    (-8490.00, 9370.00),
    (-9495.00, 10384.00),
    (-14610.40, 14787.00),
    (-16296.00, 15483.00),
    (-14953.65, 17336.73),
]
    bot.Templates.Multibox_Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_bds)
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("Boss Chest")


    # ===== OPEN FINAL CHEST =====
    bot.Interact.WithGadgetAtXY(-15800.98,16901.23)
    bot.Wait.ForTime(1500)
    bot.States.AddCustomState(open_fendi_chest, "Open Chest (All Accounts)")
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda:_wait_end_dungeon(), "Wait for end of dungeon and teleport")

    

    bot.States.AddHeader("Shandra Reward")

    bot.Move.XYAndInteractNPC(12056, -17882)
    bot.Multibox.SendDialogToTarget(SHANDRA_QUEST_REWARD_DIALOG)


    bot.States.AddHeader("Enter Dungeon")
    bot.Move.XY(9240.07, -20260.95)
    bot.States.AddCustomState(lambda: wait_for_map_change(SoO_lvl1, 60), "Wait for Level 1")

    bot.States.AddHeader("Go Out of Dungeon")
    bot.Move.XY(-15650, 8900)
    bot.States.AddCustomState(lambda: wait_for_map_change(Arbor_Bay, 60), "Wait for Arbor_Bay")
    bot.States.AddHeader("Take next quest")
    bot.Move.XY(12056, -17882)
    bot.Move.XYAndInteractNPC(12056, -17882)
    bot.Multibox.SendDialogToTarget(SHANDRA_TAKE_DIALOGS)
    bot.Wait.ForTime(4000)

    bot.States.AddHeader("Start New Run")
    bot.Move.XY(9240.07, -20260.95)

    
    # ===== LOOP =====
    bot.States.JumpToStepName("LOOP_RESTART_POINT")


# ==================== INITIALIZATION ====================

bot.SetMainRoutine(farm_bds_routine)


# ==================== MAIN ====================

def main():
    bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE, main_child_dimensions=(400, 450))


if __name__ == "__main__":
    main()