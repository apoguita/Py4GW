import os
from typing import Generator, Optional, Tuple, List
import time, math
import PyInventory
from Py4GWCoreLib import *
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
from Py4GWCoreLib.botting_src.helpers import BottingHelpers
from Py4GW_widget_manager import get_widget_handler
from Sources.oazix.CustomBehaviors.primitives.botting.botting_helpers import BottingHelpers
from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader

# ==================== CONFIGURATION ====================
BOT_NAME = "BDS Farm secure wipe"
MODULE_NAME = "Shards of Orr (BDS Farm) [Wipe]" 
MODULE_ICON = "Textures\\Module_Icons\\Shards of Orr.png"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots","BDS","bds.png")

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
    upkeep_morale_active=True,
)

# ==================== UTILITY FUNCTIONS ====================

from typing import Dict, List, Tuple, Optional, Any, Callable, Generator

# ==================== AUTO SHRINE + STEP REGISTRY ====================

# Move step registry (per map)
_STEP_BY_NAME: Dict[str, int] = {}  # name -> global index
_STEP_META: List[Dict[str, Any]] = []  # {idx,name,map_id,x,y}

# “Learned shrines” per map (from rez positions)
_SHRINES: Dict[int, List[Tuple[float, float]]] = {}

_LAST_STEP_NAME: Optional[str] = None
_LAST_STEP_IDX: int = -1

# Tune these
SHRINE_MERGE_DIST = 450.0   # merge learned shrines within this radius
RESUME_SEARCH_DIST = 1200.0 # max dist to find a nearby move step at rez

def S_BlacklistModel(model_id: int):
    """Custom FSM step: add a MODEL ID to loot blacklist (script-only)."""
    from Py4GWCoreLib.Routines import Routines
    from Py4GWCoreLib.py4gwcorelib_src.Lootconfig_src import LootConfig

    def _gen():
        loot = LootConfig()
        loot.AddToBlacklist(model_id)     # <- MODEL blacklist
        yield from Routines.Yield.wait(100)
        yield
    return _gen()

def drop_bundle_safe(times: int = 2, delay_ms: int = 250) -> Generator:
    for _ in range(times):
        yield from Routines.Yield.Keybinds.DropBundle()
        yield from Routines.Yield.wait(delay_ms)
    yield

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

def _get_custom_behavior(initialize_if_needed: bool = True):
    loader = CustomBehaviorLoader()
    behavior = loader.custom_combat_behavior

    if behavior is None and initialize_if_needed:
        loader.initialize_custom_behavior_candidate()
        behavior = loader.custom_combat_behavior

    return behavior

def _toggle_wait_for_party(enabled: bool) -> None:
    _set_custom_utility_enabled(
        enabled,
        skill_names=("wait_if_party_member_too_far",),
        class_names=("WaitIfPartyMemberTooFarUtility",),
    )

def TrackCurrentStep(bot: "Botting") -> None:
    """Update last step name + idx (best-effort)."""
    global _LAST_STEP_NAME, _LAST_STEP_IDX

    cur = getattr(bot.config.FSM, "current_step_name", None)
    if not cur:
        cur = getattr(bot.States, "CurrentStepName", None)

    if isinstance(cur, str) and cur and cur != _LAST_STEP_NAME:
        _LAST_STEP_NAME = cur
        _LAST_STEP_IDX = _STEP_BY_NAME.get(cur, _LAST_STEP_IDX)
        ConsoleLog("STEP", f"👀 {cur} (idx={_LAST_STEP_IDX})")

def _dist(ax: float, ay: float, bx: float, by: float) -> float:
    return math.hypot(ax - bx, ay - by)


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
    (-10984, 486),
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
        yield from Routines.Yield.wait(100)

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



def pickup_torch(max_scan_dist: float = 5000, attempts: int = 40) -> Generator:
    inv = PyInventory.PyInventory()
    me = int(Player.GetAgentID())

    ConsoleLog("TORCH", "scan+pickup start")

    for _ in range(attempts):
        arr = AgentArray.GetItemArray()
        arr = AgentArray.Filter.ByDistance(arr, Player.GetXY(), max_scan_dist)
        arr = AgentArray.Sort.ByDistance(arr, Player.GetXY())

        target_agent: int = 0
        ground_item_id: int = 0
        owner: int = -1

        for a in arr:
            aid = int(a)
            it = Agent.GetItemAgentByID(aid)
            if not it:
                continue

            try:
                owner = int(it.owner)
                if owner not in (0, me):
                    continue
            except Exception:
                owner = -1  # si owner illisible, on tente quand même

            try:
                gid = int(Agent.GetItemAgentItemID(aid))
            except Exception:
                continue

            mid: Optional[int] = None
            if Item is not None:
                try:
                    m = Item.GetModelID(gid)
                    mid = int(m) if isinstance(m, int) else None
                except Exception:
                    mid = None

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

        # stop-move pour éviter annulation
        try:
            px, py = Player.GetXY()
            Player.Move(px, py)
        except Exception:
            pass
        yield from Routines.Yield.wait(80)

        # Ciblage
        Player.ChangeTarget(target_agent)
        yield from Routines.Yield.wait(120)

        ConsoleLog("TORCH", f"pickup try agent={target_agent} ground_item_id={ground_item_id} owner={owner}")

        # Essais : agent_id puis ground_item_id (compat multi-build)
        for _try in range(2):
            try:
                inv.PickUpItem(target_agent, True)
            except Exception:
                pass
            yield from Routines.Yield.wait(250)

            try:
                inv.PickUpItem(ground_item_id, True)
            except Exception:
                pass
            yield from Routines.Yield.wait(250)

            # fallback interact
            try:
                Player.Interact(target_agent, False)
            except Exception:
                pass
            yield from Routines.Yield.wait(450)

            # check disparition (ramassé)
            try:
                still_there = bool(Agent.GetItemAgentByID(target_agent))
            except Exception:
                still_there = False

            if not still_there:
                ConsoleLog("TORCH", "✅ picked")
                yield
                return

        ConsoleLog("TORCH", "pickup attempt failed -> retry")
        yield from Routines.Yield.wait(200)

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

    ConsoleLog(BOT_NAME, f"Interacting with gadget {gad_id}")
    Player.ChangeTarget(gad_id)
    yield from Routines.Yield.wait(100)

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


FENDI_GADGET_ID = 8934
FENDI_SCAN_RADIUS = 700.0  # un peu plus large que 500 pour être safe

def _target_fendi_chest_agent_id() -> int:
    """Retourne l'agent_id du coffre de Fendi (filtré par gadget_id)."""
    gadgets = AgentArray.GetGadgetArray()
    gadgets = AgentArray.Filter.ByDistance(gadgets, FENDI_CHEST_POSITION, FENDI_SCAN_RADIUS)
    gadgets = AgentArray.Sort.ByDistance(gadgets, FENDI_CHEST_POSITION)

    best = 0
    for a in gadgets:
        aid = int(a)
        g = Agent.GetGadgetAgentByID(aid)
        if not g:
            continue

        # g.gadget_id est la signature la plus fiable ici
        try:
            if int(g.gadget_id) == int(FENDI_GADGET_ID):
                best = aid
                break
        except Exception:
            continue

    return best



def debug_nearby_gadgets(max_print: int = 10) -> Generator:
    """Debug rapide si jamais tu veux vérifier les candidats autour du point."""
    gadgets = AgentArray.GetGadgetArray()
    gadgets = AgentArray.Filter.ByDistance(gadgets, FENDI_CHEST_POSITION, FENDI_SCAN_RADIUS)
    gadgets = AgentArray.Sort.ByDistance(gadgets, FENDI_CHEST_POSITION)

    ConsoleLog(BOT_NAME, f"[FENDI] gadgets_near={len(gadgets)}")
    for i, a in enumerate(gadgets[:max_print]):
        aid = int(a)
        g = Agent.GetGadgetAgentByID(aid)
        if not g:
            continue
        try:
            ConsoleLog(BOT_NAME, f"[FENDI] #{i} aid={aid} gadget_id={int(g.gadget_id)} extra_type={int(g.extra_type)}")
        except Exception:
            ConsoleLog(BOT_NAME, f"[FENDI] #{i} aid={aid} (no fields)")
        yield from Routines.Yield.wait(100)
    yield

def TargetNearestNPC():
    npc_array = AgentArray.GetNPCMinipetArray()
    npc_array = AgentArray.Filter.ByDistance(npc_array,Player.GetXY(), 200)
    npc_array = AgentArray.Sort.ByDistance(npc_array, Player.GetXY())
    if len(npc_array) > 0:
        Player.ChangeTarget(npc_array[0])

def open_fendi_chest():
    """Multibox coordination for opening the final chest"""
    ConsoleLog(BOT_NAME, "Opening final chest with multibox...")

    # (optionnel) debug si tu veux vérifier la zone
    # yield from debug_nearby_gadgets()

    target = _target_fendi_chest_agent_id()
    if target == 0:
        ConsoleLog(BOT_NAME, "No Fendi chest found (gadget_id filter)!")
        return

    Player.ChangeTarget(target)
    yield from Routines.Yield.wait(150)

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
        GLOBAL_CACHE.ShMem.SendMessage(
            sender_email,
            account.AccountEmail,
            SharedCommandType.InteractWithTarget,
            (target, 0, 0, 0),
        )

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
        SoO_lvl1: [
            ("Secure return - L1", -11686, 10427),
            ("Secure return 1 - L1", 15953.0, 11902.0)
        ],
        SoO_lvl2: [
            ("Secure return - L2", -14076.0, -19457.0)
        ],
        SoO_lvl3: [
            ("Secure return 1 - L3", 17544.0, 18810.0),
            ("Secure return 2 - L3", -2964.1,7302.1),
            ("Secure return boss - L3", -9686.32, 2632)
        ],
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
    if map_id not in (SoO_lvl1, SoO_lvl2, SoO_lvl3):
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


def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))

def S_Path(name: str, points: list[tuple[float, float]], map_id: Optional[int] = None) -> None:
    bot.States.AddHeader(name)

    # ✅ Step "ancre" jumpable
    bot.States.AddCustomState(_step_anchor, name)

    n = len(points)
    for i, (x, y) in enumerate(points, start=1):
        bot.Move.XY(float(x), float(y), step_name=f"{name} - {i}/{n}")

def UseSummons():
    """
    Uses:
    - Summons (model ID 30209)
    - Legionnary Summoning Crystal (model ID 37810)
    """

    summons = [
        ("Summons", 30209),
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
        else:
            ConsoleLog("UseSummons", f"{name} not found in inventory", log=True)

    yield

def _step_anchor() -> Generator:
    yield

def loop_marker():
    """Empty marker for loop restart point"""
    ConsoleLog(BOT_NAME, "Starting new dungeon run...")
    yield


# ==================== MAIN ROUTINE ====================

def farm_bds_routine(bot: Botting) -> None:
    
    # ===== INITIAL CONFIGURATION =====
    bot.Templates.Routines.UseCustomBehaviors(
        on_player_critical_death=BottingHelpers.botting_unrecoverable_issue,
        on_party_death=BottingHelpers.botting_unrecoverable_issue,
        on_player_critical_stuck=BottingHelpers.botting_unrecoverable_issue) 
    widget_handler = get_widget_handler()
    widget_handler.enable_widget('Return to outpost on defeat')
    bot.Properties.Enable("pause_on_danger")
    # Register wipe callback
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    

    
    # ===== START OF BOT =====
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=Vloxs_Fall)


    
    # ===== START OF LOOP =====
    bot.States.AddHeader(f"{BOT_NAME}_LOOP")
    bot.Party.SetHardMode(True)
    # Enable properties
    bot.Properties.Enable('auto_combat')
    bot.States.AddCustomState(_step_anchor, "Reset farm")  # anchor for secure return on wipe    
    # ===== GO TO DUNGEON =====
    bot.States.AddHeader("Go to Dungeon")
    bot.Move.XYAndExitMap(15505.38, 12460.59, target_map_id=Arbor_Bay)
    bot.Wait.UntilOnExplorable()
    bot.Wait.ForTime(2000)
    
    # First blessing in Arbor Bay
    bot.Move.XYAndInteractNPC(16327, 11607)
    bot.Wait.ForTime(4000)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)
    bot.Multibox.UseAllConsumables()

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
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path)
    bot.Wait.UntilOutOfCombat()
    

    
    bot.States.AddCustomState(lambda: bot.Move.XY(12056.00,-17882), "Go to Shandra")
    # Take Shandra' quest
    bot.Move.XYAndInteractNPC((12056.00,-17882)[0], (12056.00,-17882)[1])
    bot.Multibox.SendDialogToTarget(SHANDRA_TAKE_DIALOGS)
    bot.Wait.ForTime(4000)
    
    # Enter the dungeon
    bot.Move.XY(11177, -17683)
    bot.Move.XY(10218, -18864)
    bot.Move.XY(9519, -19968)
    bot.Move.XY(9240.07, -20260.95)


    # ===== LOOP RESTART POINT =====
    bot.States.AddCustomState(loop_marker, "LOOP_RESTART_POINT")


    # Wait for change to Level 1
    bot.States.AddCustomState(lambda: wait_for_map_change(SoO_lvl1, 60), "Wait for Level 1")
    bot.Wait.ForTime(2000)
    

    # =========================
    #           Level 1
    # =========================
    bot.States.AddHeader("Level 1")
    
    # First blessing Level 1
    bot.States.AddCustomState(lambda: S_BlacklistModel(22342),"Blacklist torch")
    bot.Move.XY(-11686, 10427)
    bot.Move.XYAndInteractNPC(-11686, 10427)
    bot.Wait.ForTime(2000)    
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)    

    
    # Use consumables
    bot.States.AddCustomState(UseSummons, "Use Summons")
    bot.Multibox.UseAllConsumables()
    bot.Templates.Aggressive()

    path_before_bridgant = [
        (-11685.5,10475.5),
        (-10682.6,9841.2),
        (-9670.9,9744.2),
        (-8661.9,9975.7),
        (-7653.5,10063.4),
        (-6652.0,10156.2),
        (-5646.1,10717.7),
        (-4642.3,11376.3),
        (-3640.8,11984.6),
        (-2634.2,12702.1),
        (-1630.8,13315.2),
        (-628.5,14075.6),
        (379.8,14700.8),
        (1384.7,15324.0),
        (2394.5,15950.3),
        (3409.5,15710.4),
        (4157.9,14705.9),
        (5089.4,13698.1),
        (6090.8,13172.6),
        (7091.1,13482.8),
        (8093.3,13148.6),
        (8503.9,12143.5),
        (7496.9,11676.0),
        (6494.3,10739.2)]
    bot.Templates.Aggressive()
    bot.Wait.UntilOutOfCombat()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_before_bridgant)



    path_before_door= [
        (9196.0,11484.4),
        (10196.0,12469.4),
        (11198.7,13401.8),
        (12201.3,14284.4),
        (13202.8,15176.3),
        (14207.0,16116.2),
        (15208.8,16871.6),
        (16213.2,16417.3),
        (16643.4,15416.6),
        (16994.9,14410.6),
        (17115.6,13405.6),
        (16689.2,12400.4),
        ]
    bot.Templates.Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_before_door)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(15953, 11902)
    bot.States.AddHeader("Secure return - L1")
    bot.States.AddCustomState(_step_anchor, "Secure return - L1")  # anchor for secure return on wipe    
    
    path_before_door2 = [    
        (15927.4,11684.7),
        (16037.8,10679.9),
        (15761.1,9679.7),
        (15289.5,8672.6),
        (14447.3,7672.0),
        (14526.2,6664.2),
        (14951.6,5657.9),
    ]

    bot.Templates.Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_before_door2)
    bot.Wait.UntilOutOfCombat()
    # Door gadget
    bot.Move.XY(15100, 5443)
    bot.States.AddCustomState(bot.Move.XYAndInteractGadget(15100.00, 5443),"Interact")

    # Path after door
    path_after_door = [
        (15364.9,4858.7),
        (15689.5,3857.7),
        (16026.7,2857.1),
        (17030.7,2262.6),
        (18035.7,1888.8),
        (19037.1,1384.6),
        (19679.2,1009.5),
        (20181.6,1203.7),
        (20400.5,1300),


    ]
    bot.Templates.Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_after_door)
    bot.Wait.UntilOutOfCombat()

    # Wait for change to Level 2
    bot.States.AddCustomState(lambda: wait_for_map_change(SoO_lvl2, 60), "Wait for Level 2")
    bot.Wait.ForTime(2000)

    # =========================
    #          Level 2
    # =========================
    bot.States.AddHeader("Level 2")
    # --- Entry + Blessing ---
    bot.Move.XY(-14076, -19457)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-14076, -19457)
    bot.Move.XYAndInteractNPC(-14076, -19457)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(2000)
    bot.States.AddHeader("Secure return - L2")
    bot.States.AddCustomState(_step_anchor, "Secure return - L2")  # anchor for secure return on wipe
 
    # Use consumables
    bot.States.AddCustomState(UseSummons, "Use Summons")
    bot.Multibox.UseAllConsumables()
    bot.Templates.Aggressive()
    # --- Path to torch area (atomisé) ---
    path_before_torch = [
        (-14977.9,-16480.2),
        (-15985.6,-16838.1),
        (-16985.9,-16929.4),
    ]
    bot.Templates.Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_before_torch)
    bot.Wait.UntilOutOfCombat()

    # --- Torch chest + pickup ---
    bot.States.AddCustomState(bot.Move.XYAndInteractGadget(-14709, -16548), "Open Torch Chest")

    bot.States.AddCustomState(pickup_torch, "Pickup Torch")
    # --- Move to brazier sequence 1 (avec drop bundle) ---
    bot.Move.XY(-11002, -17001)
    bot.States.AddCustomState(lambda: drop_bundle_safe(2, 250), "Drop bundle")



    bot.Move.XY(-9259, -17322)
    bot.States.AddCustomState(pickup_torch, "Pickup Torch")

    bot.Move.XY(-11030.3,-17474.0)
    bot.Move.XY(-11303, -14596)

    # --- Brazier sequence 1 ---
    bot.States.AddHeader("L2 - Brazier sequence 1")
    run_brazier_sequence([(float(x), float(y)) for x, y in BDS_L2_PART1])
    bot.States.AddHeader("L2 - Cleaning")
    bot.States.AddCustomState(lambda: drop_bundle_safe(2, 250), "Drop bundle")
    bot.Move.XY(-8996, -11987)
    bot.Move.XY(-8699, -10752)
    bot.States.AddCustomState(pickup_torch, "Pickup Torch")

    bot.States.AddHeader("Move to next room")
    bot.Move.XY(-11061.1,-7578.5)
    bot.States.AddCustomState(lambda: drop_bundle_safe(2, 250), "Drop bundle")
    
    bot.Move.XY(-10958.2,-4529.5)
    bot.States.AddCustomState(pickup_torch, "Pickup Torch")

    path_room2 = [
    (-11013.7,-6381.7),
    (-11081.9,-5378.8),
    (-10071.6,-4396.5),
    (-9069.4,-4301.1),
    (-8066.1,-4222.4),
    (-7058.8,-4191.0)]
    bot.Templates.Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_room2)
    bot.Wait.UntilOutOfCombat()



    bot.States.AddCustomState(lambda: drop_bundle_safe(2, 250), "Drop bundle")
    bot.Move.XY(-4245.2,-2101)
    bot.States.AddCustomState(pickup_torch, "Pickup Torch")


    # --- Brazier sequence 2 ---
    bot.States.AddHeader("L2 - Brazier sequence 2")

    run_brazier_sequence([(float(x), float(y)) for x, y in BDS_L2_PART2])

    bot.States.AddCustomState(lambda: drop_bundle_safe(2, 250), "Drop bundle")
    bot.Move.XY(-6798.8, -2436.4)

    bot.States.AddHeader("L2 - Move to door")
    path_after_second_room = [
    (-9069.4,-4301.1),
    (-10071.6,-4396.5),
    (-11106.6,-4747.1),
    (-10970.9,-5754.5),
    (-11033.4,-6755.6),
    (-11318.0,-7767.2),
    (-12320.7,-8417.1),
    (-13324.0,-8649.0),
    (-14326.3,-8773.0),
    (-15331.0,-8905.6),
    (-16335.1,-9004.5),
        

    ]
    bot.Templates.Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_after_second_room)
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("L2 - Open door")
    bot.Move.XY(-18725, -9171)
    bot.States.AddCustomState(bot.Move.XYAndInteractGadget(-18725, -9171), "Open Door")
    bot.Move.XY(-18610, -8636)
    bot.Move.XY(-19571.61, -8459.00)
    bot.States.AddCustomState(lambda: wait_for_map_change(SoO_lvl3, 60), "Wait for Level 3")
    bot.Wait.ForTime(2000)

    # =========================
    #           Level 3
    # =========================
    bot.States.AddHeader("Level 3")
    bot.Properties.Enable("pause_on_danger")
    # --- Blessing ---
    bot.Move.XY(17544, 18810)
    bot.Move.XYAndInteractNPC(17544, 18810)
    bot.Wait.ForTime(2000)    
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(2000) 
    bot.States.AddHeader("Secure return 1 - L3")
    bot.States.AddCustomState(_step_anchor, "Secure return 1 - L3")
    # Use consumables

    bot.States.AddCustomState(UseSummons, "Use Summons")
    bot.Multibox.UseAllConsumables()
    bot.Templates.Aggressive()

    bot.States.AddHeader("L3 - Cleaning level")
    path_before_secure_return = [
        (17544.5,18530.2),
        (17231.2,17523.3),
        (16811.3,16513.4),
        (15803.0,17071.6),
        (15004.8,18075.5),
        (13998.4,18866.7),
        (12990.9,19299.5),
        (11988.8,19353.2),
        (10986.4,19188.9),
        (9985.7,18719.2),
        (9402.1,17715.6),
        (9076.9,17383.4),
        (9133.0,16373.0),
        (8496.5,15367.3),
        (7978.0,14357.9),
        (7105.7,13350.9),
        (6236.1,12349.0),
        (5524.4,11344.1),
        (4813.8,10340.7),
        (4095.0,9332.7),
        (3091.4,8424.8),
        (2078.2,8286.5),
        (1069.7,8045.3),
        (619.8,7044.0),
        (-385.8,6478.3),
        (-1123.5,7481.9),
        (-2964.1,7302.1)]
    bot.Templates.Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_before_secure_return)
    bot.Wait.UntilOutOfCombat()     

    bot.States.AddHeader("Secure return 2 - L3")
    bot.States.AddCustomState(_step_anchor, "Secure return 2 - L3")


    bot.States.AddHeader("L3 - Cleaning level 2")
    path_after_secure_return = [    
        (-3139.7,7022.7),
        (-4152.0,6469.6),
        (-5154.0,5969.0),
        (-5837.7,4968.0),
        (-5832.1,3954.0),
        (-6838.3,3495.2),
        (-7845.7,4397.5),
        (-8049.0,5403.5),
        (-9049.9,5289.2),
        (-10051.1,4604.6),
        (-11057.4,4039.1),
        (-10381.7,3037.7),
    ]
    bot.Templates.Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_after_secure_return)
    bot.Wait.UntilOutOfCombat()


    bot.States.AddHeader("L3 - Path to torch")
    path_to_take_torch = [
        (-4723.00, 6703.00),
        (-1280.00, 7880.00),
        (3089.73, 8511.00),
        (4963.00, 9974.00),
        (9918.64, 19108.00),
        (14709.00, 19526.00),
        (16111.00, 17556.00),
    ]

    bot.Templates.Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_to_take_torch)
    bot.Wait.UntilOutOfCombat()

    bot.States.AddCustomState(bot.Move.XYAndInteractGadget(16111.00, 17556), "Open Torch Chest")
    bot.States.AddCustomState(pickup_torch, "Pickup Torch")

    # --- Brazier sequence ---
    bot.States.AddHeader("L3 - Brazier sequence")
    bot.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")    
    run_brazier_sequence([(float(x), float(y)) for x, y in BDS_L3])
    bot.States.AddCustomState(lambda: drop_bundle_safe(2, 250), "Drop bundle")
    bot.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")   
    bot.States.AddHeader("L3 - Kill Brigant")
    bot.Move.XY(-9686.32, 2632)
    bot.States.AddHeader("Secure return 2 - L3")
    bot.States.AddCustomState(_step_anchor, "Secure return boss - L3")
    bot.States.AddHeader("L3 - Move and open door")
    bot.Move.XY(-9252.32, 6396.40)
    bot.States.AddCustomState(bot.Move.XYAndInteractGadget(-9252.32, 6396.40), "Open Door")

    bot.States.AddHeader("L3 - Path to Fendi")
    # --- Boss path ---
    path_bds = [
        (-8751.4,6187.9),
        (-9254.5,6661.8),
        (-9548.7,7161.9),
        (-9842.2,7662.6),
        (-9860.5,8165.6),
        (-9378.4,8667.0),
        (-8870.8,9148.9),
        (-8736.4,9654.1),
        (-9112.1,10163.0),
        (-9541.0,10674.6),
        (-9930.0,11184.1),
        (-10433.0,11428.1),
        (-10938.3,11856.4),
        (-11444.7,12274.6),
        (-11956.5,12758.7),
        (-12457.3,13242.3),
        (-12960.7,13501.0),
        (-13466.4,13844.3),
        (-13970.4,14245.7),
        (-14475.7,14709.8),
        (-14979.2,15046.5),
        (-15480.8,15521.6),
        (-16022.9,17889.9),

    ]

    bot.Templates.Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_bds)
    bot.Wait.UntilOutOfCombat()
    bot.States.AddHeader("Chest opening")
        # ===== OPEN FINAL CHEST =====
    bot.Move.XY(-15800.98,16901.23) 
    bot.States.AddCustomState(open_fendi_chest, "Open Chest (All Accounts)")
    bot.States.AddCustomState(lambda:_wait_end_dungeon(), "Wait for end of dungeon and teleport")

    
    bot.States.AddHeader("Quest sequence (reward + retake)")
    # return to arbor bay and take reward

    bot.Move.XYAndInteractNPC(12056, -17882)
    bot.Multibox.SendDialogToTarget(SHANDRA_QUEST_REWARD_DIALOG)


    # enter the dungeon
    bot.Move.XY(9240.07, -20260.95)
    bot.States.AddCustomState(lambda: wait_for_map_change(SoO_lvl1, 60), "Wait for Level 1")

    #go out of the dungeon
    bot.Move.XY(-15650, 8900)
    bot.States.AddCustomState(lambda: wait_for_map_change(Arbor_Bay, 60), "Wait for Arbor_Bay")
    
    # Take Shandra' quest

    bot.Move.XY(12056, -17882)
    bot.Move.XYAndInteractNPC(12056, -17882)
    bot.Multibox.SendDialogToTarget(SHANDRA_TAKE_DIALOGS)
    bot.Wait.ForTime(4000)

    #enter the dungeon again
    
    bot.Move.XY(9240.07, -20260.95)

    
    # ===== LOOP =====
    bot.States.JumpToStepName("LOOP_RESTART_POINT")


# ==================== INITIALIZATION ====================

bot.SetMainRoutine(farm_bds_routine)


# ==================== MAIN ====================

def main():
    bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE, main_child_dimensions=(500, 350))


if __name__ == "__main__":
    main()