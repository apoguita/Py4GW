import Py4GW

from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Py4GWcorelib import ConsoleLog, Console, ActionQueueManager, Utils
from Py4GWCoreLib.routines_src.BehaviourTrees import BT as RoutinesBT
from Py4GWCoreLib.ImGui import ImGui

from Py4GWCoreLib.native_src.internals.types import Vec2f
from Sources.ApoSource.ApoBottingLib import wrappers as BT

from Sources.ApoSource.beautiful_pre_searing_src.getting_started import get_sequence_builders
from Sources.ApoSource.beautiful_pre_searing_src.unlock_ranger_secondary import UnlockPet

import PyImGui

from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Sources.ApoSource.beautiful_pre_searing_src.globals import  *


MODULE_NAME = "Beautiful Pre-Searing"
BANNER_WIDTH = 422
BANNER_HEIGHT = 200
initialized = False
INI_KEY = ""
INI_PATH = "Widgets/BeautifulPreSearing"
INI_FILENAME = "BeautifulPreSearing.ini"
projects_root = Py4GW.Console.get_projects_path()
TEXTURE_PATH = f"{projects_root}/Sources/ApoSource/beautiful_pre_searing_src/resources/Beautiful Pre-Searing-banner.png"
botting_trees: dict[str, BottingTree] = {}
selected_debug_tree_name = "Getting Started"
selected_start_sequence = "Sequence_001_Common"
draw_move_path = True
draw_move_path_labels = False
draw_move_path_thickness = 4.0
draw_move_waypoint_radius = 15.0
draw_move_current_waypoint_radius = 20.0


IMP_BAG_ID = 1
IMP_BAG_SLOT = 0
GETTING_STARTED_TREE_NAME = "Getting Started"
HEROAI_ONLY_TREE_NAME = "HeroAI Only"
UNLOCK_PET_TREE_NAME = "Unlock Pet"
ACQUIRE_WEAPON_TREE_NAME = "Acquire Weapon"


def EquipStarterBow() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name="Ensure Starter Bow Equipped",
            children=[
                BehaviorTree.SequenceNode(
                    name="Starter Bow Already Equipped",
                    children=[
                        BT.IsItemEquipped(STARTER_BOW_MODEL_ID),
                        LogMessage("Starter Bow is already equipped"),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name="Equip Starter Bow",
                    children=[
                        LogMessage("Equipping Starter Bow"),
                        BT.EquipItemByModelID(STARTER_BOW_MODEL_ID),
                        BT.IsItemEquipped(STARTER_BOW_MODEL_ID),
                    ],
                ),
            ],
        )
    )


def ExchangeCollectorItem(
    output_model_id: int,
    trade_model_ids: list[int],
    quantity_list: list[int],
    cost: int = 0,
    aftercast_ms: int = 500,
) -> BehaviorTree:
    def _exchange_item() -> BehaviorTree.NodeState:
        k = min(len(trade_model_ids), len(quantity_list))
        if k == 0:
            return BehaviorTree.NodeState.FAILURE

        requested_models = trade_model_ids[:k]
        requested_quantities = quantity_list[:k]

        offered_item_id = 0
        for candidate in GLOBAL_CACHE.Trading.Collector.GetOfferedItems():
            if GLOBAL_CACHE.Item.GetModelID(candidate) == output_model_id:
                offered_item_id = candidate
                break

        if offered_item_id == 0:
            return BehaviorTree.NodeState.FAILURE

        trade_item_ids: list[int] = []
        trade_item_quantities: list[int] = []

        for model_id, required_quantity in zip(requested_models, requested_quantities):
            remaining_quantity = int(required_quantity)

            for item_id in GLOBAL_CACHE.Inventory.GetAllInventoryItemIds():
                if item_id == 0:
                    continue
                if GLOBAL_CACHE.Item.GetModelID(item_id) != model_id:
                    continue

                item_quantity = int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id) or 1)
                if item_quantity <= 0:
                    continue

                used_quantity = min(item_quantity, remaining_quantity)
                trade_item_ids.append(item_id)
                trade_item_quantities.append(used_quantity)
                remaining_quantity -= used_quantity

                if remaining_quantity <= 0:
                    break

            if remaining_quantity > 0:
                return BehaviorTree.NodeState.FAILURE

        GLOBAL_CACHE.Trading.Collector.ExghangeItem(
            offered_item_id,
            cost,
            trade_item_ids,
            trade_item_quantities,
        )
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=f"ExchangeCollectorItem({output_model_id})",
            action_fn=_exchange_item,
            aftercast_ms=aftercast_ms,
        )
    )


def HasAtLeastItemQuantity(model_id: int, quantity: int) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.ConditionNode(
            name=f"HasAtLeastItemQuantity({model_id}, {quantity})",
            condition_fn=lambda: GLOBAL_CACHE.Inventory.GetModelCount(model_id) >= quantity,
        )
    )


def FarmBow(exclude_models: list[int] | None = None) -> BehaviorTree:
    LAKESIDE_COUNTY_EXIT_COORDS_001: Vec2f = Vec2f(-12508.46, -6135.42)
    LAKESIDE_COUNTY_EXIT_COORDS_002: Vec2f = Vec2f(-10905, -6287)
    
    REGENT_VALLEY_MID_001_EXIT_COORDS: Vec2f = Vec2f(-6316.87, -6808.10)
    REGENT_VALLEY_MID_002_EXIT_COORDS: Vec2f = Vec2f(-4833.97, -12199.93)
    REGENT_VALLEY_OVER_BRIDGE_EXIT_COORDS: list[Vec2f] = [Vec2f (-3464.73, -13135.62)]
    REGENT_VALLEY_EXIT_COORDS: Vec2f = Vec2f(6516, -19822)
    
    KILLSPOT_COORDS: Vec2f = Vec2f(-14696.82, 10211.46)

    ROWNAN_COORDS: Vec2f = Vec2f(-17002.54, 10695.05)
    ROWNAN_ENC_STR: str = "\\x328D\\xC36A\\x9B35\\x34A8"
    
    MELANDRU_STATUE_COORDS: Vec2f = Vec2f(-14990.32, -1139.84)

    def _build_runtime_merchant_cleanup(node: BehaviorTree.Node) -> BehaviorTree:
        merchant_coords = _get_merchant_coords_from_map_id()
        if merchant_coords is None:
            return BehaviorTree(
                BehaviorTree.ActionNode(
                    name="NoMerchantCleanup",
                    action_fn=lambda runtime_node: BehaviorTree.NodeState.SUCCESS,
                )
            )

        return MoveInteractAndSellItems(
            merchant_coords=merchant_coords,
            exclude_models=exclude_models,
            log=False,
        )
    
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="Farm Bow",
            children=[
                LogMessage("Traveling to Ashford Abbey to Farm for Ascalon Hornbow"),

                BT.TravelToOutpost(ASHFORD_ABBEY_MAP_ID),
                BehaviorTree.SubtreeNode(
                    name="RuntimeMerchantCleanup",
                    subtree_fn=_build_runtime_merchant_cleanup,
                ),
                LogMessage("Exiting to Lakeside County"),
                
                BT.Move(LAKESIDE_COUNTY_EXIT_COORDS_001),
                BT.Move(LAKESIDE_COUNTY_EXIT_COORDS_002),
                BT.WaitForMapLoad(LAKESIDE_COUNTY_MAP_ID),
                
                LogMessage("Exiting to Regent Valley"),
                
                BT.Move(REGENT_VALLEY_MID_001_EXIT_COORDS),
                BT.Move(REGENT_VALLEY_MID_002_EXIT_COORDS),
                BT.MoveDirect(REGENT_VALLEY_OVER_BRIDGE_EXIT_COORDS),
                BT.Move(REGENT_VALLEY_EXIT_COORDS),
                BT.WaitForMapLoad(REGENT_VALLEY_MAP_ID),
                
                LogMessage("Farming in Regent Valley for Ascalon Hornbow"),
                BT.Move(KILLSPOT_COORDS),
                LogMessage("Clearing enemies around killspot"),
                BT.ClearEnemiesInArea(pos=KILLSPOT_COORDS, radius=CLEAR_ENEMIES_AREA_RADIUS),
                LogMessage("Moving to Melandru Statue to kill more enemies"),
                BT.Move(Vec2f(-17670.05, 8973.73)),
                BT.Move(MELANDRU_STATUE_COORDS),
                LogMessage("Returning to Rownan"),
                BT.Move(ROWNAN_COORDS),
                LogMessage("Interacting with Rownan"),
                BT.MoveAndInteract(ROWNAN_COORDS, target_distance=Range.Area.value),
                
            ],
        )
    )

def _get_merchant_coords_from_map_id() -> Vec2f | None:
    curent_map_id = Map.GetMapID()
    
    if curent_map_id == ASCALON_CITY_MAP_ID:
        return Vec2f(8470.88, 4882.44)
    if curent_map_id == ASHFORD_ABBEY_MAP_ID:
        return Vec2f(-11477.68, -6431.78)
    else:
        return None

def FarmBowUntilFlatbowEquipped(
    exclude_models: list[int] | None = None,
) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.RepeaterUntilSuccessNode(
            name="Farm Until Flatbow Equipped",
            child=BehaviorTree.SelectorNode(
                name="Farm Bow Loop",
                children=[
                    BT.IsItemEquipped(NEVERMORE_FLATBOW_MODEL_ID),
                    BehaviorTree.SequenceNode(
                        name="Sell Trash And Farm Bow",
                        children=[
                            FarmBow(exclude_models=exclude_models),
                            BehaviorTree.SelectorNode(
                                name="Trade Bow Or Repeat",
                                children=[
                                    BehaviorTree.SequenceNode(
                                        name="Exchange And Equip Ascalon Hornbow",
                                        children=[
                                            HasAtLeastItemQuantity(DULL_CARAPACES_MODEL_ID, 3),
                                            LogMessage("Exchanging 3 Dull Carapaces for Ascalon Hornbow"),
                                            ExchangeCollectorItem(
                                                output_model_id=ASCALON_HORNBOW_MODEL_ID,
                                                trade_model_ids=[DULL_CARAPACES_MODEL_ID],
                                                quantity_list=[3],
                                            ),
                                            LogMessage("Equipping Ascalon Hornbow"),
                                            BT.EquipItemByModelID(ASCALON_HORNBOW_MODEL_ID),
                                            LogMessage("Traveling to Ashford Abbey, routine finished"),
                                            BT.TravelToOutpost(ASHFORD_ABBEY_MAP_ID),
                                            BT.IsItemEquipped(ASCALON_HORNBOW_MODEL_ID),
                                        ],
                                    ),
                                    BehaviorTree.FailerNode(
                                        name="NotEnoughCarapacesYet",
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        )
    )

"""
def AcquireWeapon(merchant_coords: Vec2f | None = None) -> BehaviorTree:
    destroy_exclude_list = [IGNEOUS_SUMMONING_STONE_MODEL_ID, NEVERMORE_FLATBOW_MODEL_ID]

    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name="Acquire Weapon",
            children=[
                BehaviorTree.SequenceNode(
                    name="Nevermore Already Equipped",
                    children=[
                        BT.IsItemEquipped(NEVERMORE_FLATBOW_MODEL_ID),
                        LogMessage("Bow is already equipped"),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name="Equip Nevermore From Inventory",
                    children=[
                        LogMessage("Checking if Nevermore Flatbow is in inventory bags"),
                        BT.IsItemInInventoryBags(NEVERMORE_FLATBOW_MODEL_ID),
                        LogMessage("Nevermore Flatbow found in inventory, equipping it"),
                        BT.EquipItemByModelID(NEVERMORE_FLATBOW_MODEL_ID),
                        BT.IsItemEquipped(NEVERMORE_FLATBOW_MODEL_ID),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name="Spawn And Equip Nevermore",
                    children=[
                        LogMessage("Nevermore Flatbow not found, spawning bonus items"),
                        BT.SpawnBonusItems(),
                        LogMessage("Deleting spawned bonus items except Igneous Summoning Stone and Nevermore Flatbow"),
                        BT.DestroyBonusItems(exclude_list=destroy_exclude_list),
                        BT.IsItemInInventoryBags(NEVERMORE_FLATBOW_MODEL_ID),
                        LogMessage("Nevermore Flatbow spawned into inventory, equipping it"),
                        BT.EquipItemByModelID(NEVERMORE_FLATBOW_MODEL_ID),
                        BT.IsItemEquipped(NEVERMORE_FLATBOW_MODEL_ID),
                    ],
                ),
                BehaviorTree.SequenceNode(
                    name="Farm For Bow",
                    children=[
                        EnsureStarterBowEquipped(),
                        FarmBowUntilNevermoreEquipped(
                            merchant_coords=merchant_coords,
                            exclude_models=destroy_exclude_list + [STARTER_BOW_MODEL_ID],
                        ),
                    ],
                ),
            ],
        )
    )
      
    """
    
def AcquireWeapon() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name="Acquire Weapon",
            children=[
                BehaviorTree.SequenceNode(
                    name="Farm For Bow",
                    children=[
                        EquipStarterBow(),
                        FarmBowUntilFlatbowEquipped(
                            exclude_models=ITEMS_BLACKLIST,
                        ),
                    ],
                ),
            ],
        )
    )
      

def _collect_sellable_inventory_item_ids(exclude_models: list[int] | None = None) -> list[int]:
    excluded_models = set(exclude_models or [])
    sellable_item_ids: list[int] = []

    for item_id in GLOBAL_CACHE.Inventory.GetAllInventoryItemIds():
        if item_id == 0:
            continue

        model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
        if model_id in excluded_models:
            continue

        item_value = GLOBAL_CACHE.Item.Properties.GetValue(item_id)
        if item_value <= 0:
            continue

        sellable_item_ids.append(item_id)

    return sellable_item_ids


def _collect_zero_value_inventory_item_ids(exclude_models: list[int] | None = None) -> list[int]:
    excluded_models = set(exclude_models or [])
    zero_value_item_ids: list[int] = []

    for item_id in GLOBAL_CACHE.Inventory.GetAllInventoryItemIds():
        if item_id == 0:
            continue

        model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
        if model_id in excluded_models:
            continue

        item_value = GLOBAL_CACHE.Item.Properties.GetValue(item_id)
        if item_value > 0:
            continue

        zero_value_item_ids.append(item_id)

    return zero_value_item_ids


def NeedsInventoryCleanup(exclude_models: list[int] | None = None) -> BehaviorTree:
    def _needs_inventory_cleanup() -> bool:
        return bool(_collect_sellable_inventory_item_ids(exclude_models=exclude_models)) or bool(
            _collect_zero_value_inventory_item_ids(exclude_models=exclude_models)
        )

    return BehaviorTree(
        BehaviorTree.ConditionNode(
            name="NeedsInventoryCleanupExcluding",
            condition_fn=_needs_inventory_cleanup,
        )
    )


def SellInventoryItems(
    exclude_models: list[int] | None = None,
    log: bool = False,
) -> BehaviorTree:
    """
    Local BT merchant helper for Beautiful Pre-Searing.

    Assumes the merchant window is already open and the character is ready to sell.
    Collects all inventory items except excluded model ids, enqueues merchant
    sell actions, and waits for the merchant queue to drain.
    """
    def _collect_items(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        sellable_item_ids = _collect_sellable_inventory_item_ids(exclude_models=exclude_models)
        node.blackboard["merchant_sell_item_ids"] = sellable_item_ids
        node.blackboard["merchant_sell_queued_count"] = 0

        if not sellable_item_ids:
            if log:
                ConsoleLog(
                    MODULE_NAME,
                    "No eligible inventory items found to sell.",
                    Console.MessageType.Info,
                    log=True,
                )
            return BehaviorTree.NodeState.SUCCESS

        if log:
            excluded_models_text = ", ".join(str(model_id) for model_id in sorted(set(exclude_models or []))) or "none"
            ConsoleLog(
                MODULE_NAME,
                f"Selling {len(sellable_item_ids)} inventory items. Excluded models: {excluded_models_text}.",
                Console.MessageType.Info,
                log=True,
            )

        return BehaviorTree.NodeState.SUCCESS

    def _queue_sell_items(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        item_ids = list(node.blackboard.get("merchant_sell_item_ids", []))
        if not item_ids:
            node.blackboard["merchant_sell_queued_count"] = 0
            return BehaviorTree.NodeState.SUCCESS

        merchant_queue = ActionQueueManager()
        merchant_queue.ResetQueue("MERCHANT")

        queued_count = 0
        for item_id in item_ids:
            quantity = GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)
            value = GLOBAL_CACHE.Item.Properties.GetValue(item_id)
            cost = quantity * value

            if quantity <= 0 or value <= 0:
                continue

            merchant_queue.AddAction(
                "MERCHANT",
                GLOBAL_CACHE.Trading._merchant_instance.merchant_sell_item,
                item_id,
                cost,
            )
            queued_count += 1

        node.blackboard["merchant_sell_queued_count"] = queued_count
        return BehaviorTree.NodeState.SUCCESS

    def _wait_for_sell_queue_to_finish(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        queued_count = int(node.blackboard.get("merchant_sell_queued_count", 0) or 0)
        if queued_count <= 0:
            return BehaviorTree.NodeState.SUCCESS

        if not ActionQueueManager().IsEmpty("MERCHANT"):
            return BehaviorTree.NodeState.RUNNING

        if log:
            ConsoleLog(
                MODULE_NAME,
                f"Sold {queued_count} inventory items through merchant queue.",
                Console.MessageType.Info,
                log=True,
            )
        return BehaviorTree.NodeState.SUCCESS

    tree = BehaviorTree.SequenceNode(
        name="SellInventoryItemsExcluding",
        children=[
            BehaviorTree.ActionNode(
                name="CollectSellableInventoryItems",
                action_fn=_collect_items,
                aftercast_ms=0,
            ),
            BehaviorTree.ActionNode(
                name="QueueMerchantSellItems",
                action_fn=_queue_sell_items,
                aftercast_ms=0,
            ),
            BehaviorTree.ActionNode(
                name="WaitForMerchantSellQueue",
                action_fn=_wait_for_sell_queue_to_finish,
                aftercast_ms=0,
            ),
        ],
    )
    return BehaviorTree(tree)


def DestroyZeroValueItems(
    exclude_models: list[int] | None = None,
    log: bool = False,
    aftercast_ms: int = 100,
) -> BehaviorTree:
    state = {
        "next_attempt_ms": 0,
    }

    def _collect_items(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        zero_value_item_ids = _collect_zero_value_inventory_item_ids(exclude_models=exclude_models)
        node.blackboard["zero_value_destroy_item_ids"] = zero_value_item_ids
        node.blackboard["zero_value_destroy_index"] = 0
        return BehaviorTree.NodeState.SUCCESS

    def _destroy_items(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        now = Utils.GetBaseTimestamp()
        if now < int(state["next_attempt_ms"]):
            return BehaviorTree.NodeState.RUNNING

        item_ids = list(node.blackboard.get("zero_value_destroy_item_ids", []))
        item_index = int(node.blackboard.get("zero_value_destroy_index", 0) or 0)
        if item_index >= len(item_ids):
            return BehaviorTree.NodeState.SUCCESS

        item_id = item_ids[item_index]
        model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
        GLOBAL_CACHE.Inventory.DestroyItem(item_id)
        node.blackboard["zero_value_destroy_index"] = item_index + 1
        state["next_attempt_ms"] = int(now + aftercast_ms)

        if log:
            ConsoleLog(
                MODULE_NAME,
                f"Queued destroy for zero-value item model {model_id} (item_id={item_id}).",
                Console.MessageType.Info,
                log=True,
            )

        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="DestroyZeroValueItemsExcluding",
            children=[
                BehaviorTree.ActionNode(
                    name="CollectZeroValueItems",
                    action_fn=_collect_items,
                    aftercast_ms=0,
                ),
                BehaviorTree.ConditionNode(
                    name="DestroyZeroValueItems",
                    condition_fn=_destroy_items,
                ),
            ],
        )
    )


def MoveInteractAndSellItems(
    merchant_coords: Vec2f,
    exclude_models: list[int] | None = None,
    log: bool = False,
    target_distance: float = Range.Area.value,
    destroy_zero_value_items: bool = False,
) -> BehaviorTree:
    merchant_frame_hash = 3613855137

    def _is_merchant_window_open() -> bool:
        from Py4GWCoreLib.UIManager import UIManager

        merchant_frame_id = UIManager.GetFrameIDByHash(merchant_frame_hash)
        return merchant_frame_id != 0 and UIManager.FrameExists(merchant_frame_id)

    return BehaviorTree(
        BehaviorTree.SelectorNode(
            name="MoveInteractAndSellItems",
            children=[
                BehaviorTree.SequenceNode(
                    name="MerchantCleanupRequired",
                    children=[
                        NeedsInventoryCleanup(exclude_models=exclude_models),
                        LogMessage("Inventory cleanup needed, visiting merchant"),
                        BT.MoveAndInteract(merchant_coords, target_distance=target_distance),
                        BehaviorTree.ConditionNode(
                            name="MerchantWindowOpen",
                            condition_fn=_is_merchant_window_open,
                        ),
                        SellInventoryItems(exclude_models=exclude_models, log=log),
                        BehaviorTree.SelectorNode(
                            name="OptionalDestroyZeroValueItems",
                            children=[
                                BehaviorTree.SequenceNode(
                                    name="DestroyZeroValueItemsWhenEnabled",
                                    children=[
                                        BehaviorTree.ConditionNode(
                                            name="DestroyZeroValueItemsEnabled",
                                            condition_fn=lambda: destroy_zero_value_items,
                                        ),
                                        DestroyZeroValueItems(exclude_models=exclude_models, log=log),
                                    ],
                                ),
                                BehaviorTree.SucceederNode(
                                    name="SkipDestroyZeroValueItems",
                                ),
                            ],
                        ),
                    ],
                ),
                LogMessage("No merchant cleanup needed"),
            ],
        )
    )



#region UI
def _configure_upkeep_trees(tree: BottingTree) -> BottingTree:
    tree.SetUpkeepTrees([
        (
            "OutpostImpService",
            lambda: RoutinesBT.Upkeepers.OutpostImpService(
                target_bag=IMP_BAG_ID,
                slot=IMP_BAG_SLOT,
                log=False,
            ),
        ),
        (
            "ExplorableImpService",
            lambda: RoutinesBT.Upkeepers.ExplorableImpService(
                log=False,
            ),
        ),
    ])
    return tree


def _build_getting_started_tree() -> BottingTree:
    tree = _configure_upkeep_trees(BottingTree(INI_KEY))
    tree.SetNamedPlannerSteps(
        get_sequence_builders(MODULE_NAME, print_to_console=print_log_to_console),
        start_from=selected_start_sequence,
        name="All quests sequence",
    )
    return tree


def _ensure_getting_started_tree(auto_start: bool = False) -> BottingTree:
    global botting_trees
    if GETTING_STARTED_TREE_NAME not in botting_trees:
        botting_trees[GETTING_STARTED_TREE_NAME] = _build_getting_started_tree()
    tree = botting_trees[GETTING_STARTED_TREE_NAME]
    if auto_start:
        tree.Start()
    return tree


def _build_unlock_pet_tree() -> BottingTree:
    tree = _configure_upkeep_trees(BottingTree(INI_KEY))
    tree.SetPlannerTree(UnlockPet())
    return tree


def _ensure_unlock_pet_tree(auto_start: bool = False) -> BottingTree:
    global botting_trees
    if UNLOCK_PET_TREE_NAME not in botting_trees:
        botting_trees[UNLOCK_PET_TREE_NAME] = _build_unlock_pet_tree()
    tree = botting_trees[UNLOCK_PET_TREE_NAME]
    if auto_start:
        tree.Start()
    return tree


def _build_acquire_weapon_tree() -> BottingTree:
    tree = _configure_upkeep_trees(BottingTree(INI_KEY))
    tree.SetPlannerTree(AcquireWeapon())
    return tree


def _ensure_acquire_weapon_tree(auto_start: bool = False) -> BottingTree:
    global botting_trees
    if ACQUIRE_WEAPON_TREE_NAME not in botting_trees:
        botting_trees[ACQUIRE_WEAPON_TREE_NAME] = _build_acquire_weapon_tree()
    tree = botting_trees[ACQUIRE_WEAPON_TREE_NAME]
    if auto_start:
        tree.Start()
    return tree


def _build_heroai_only_tree() -> BottingTree:
    tree = BottingTree(INI_KEY)
    tree.EnableHeadlessHeroAI(reset_runtime=True)
    return tree


def _ensure_heroai_only_tree(auto_start: bool = False) -> BottingTree:
    global botting_trees
    if HEROAI_ONLY_TREE_NAME not in botting_trees:
        botting_trees[HEROAI_ONLY_TREE_NAME] = _build_heroai_only_tree()
    tree = botting_trees[HEROAI_ONLY_TREE_NAME]
    if auto_start:
        tree.Start()
    return tree

def _get_debug_tree_names() -> list[str]:
    return list(botting_trees.keys())


def _get_selected_debug_tree() -> BottingTree | None:
    if selected_debug_tree_name in botting_trees:
        return botting_trees[selected_debug_tree_name]
    if botting_trees:
        first_name = next(iter(botting_trees))
        return botting_trees[first_name]
    return None


def _draw_welcome_tab():
    ImGui.push_font("Bold",22)
    ImGui.text("Welcome to Beautiful Pre-Searing!")
    ImGui.pop_font()               
    if ImGui.collapsing_header("About this script", flags=0):
        ImGui.text_wrapped("This script is a comprehensive collection of quests and activities for the Pre-Searing area.")
        ImGui.text_wrapped("Each tab contains a list of activities that can be completed, including quests, leveling, farming, and other content.")
        ImGui.separator()
    
    if ImGui.collapsing_header("How to use", flags=0):
        ImGui.bullet_text("Set your looting filters")
        ImGui.bullet_text("Deactivate Automatic Handling in Inventory+")
        ImGui.bullet_text("Deactivate HeroAI or any other combat automator")
        ImGui.bullet_text("Create a new character")
        ImGui.bullet_text('Press "Getting Started" to execute starting setup')
        ImGui.bullet_text("After finishing, explore the tabs and select the activities you want to do")
        ImGui.separator()
                
    ImGui.separator()
    
def _draw_getting_started_tab(botting_tree:BottingTree | None):
    global selected_debug_tree_name
    if ImGui.collapsing_header("1. Prepare Your Character"):
        ImGui.text_wrapped("This routine will complete important early quests that unlock essential features and quality of life improvements for the rest of the content in Pre-Searing.")
        ImGui.separator()
        
        if botting_tree is not None and botting_tree.IsStarted():
            if PyImGui.button("Stop Routines"):
                botting_tree.Stop()
        else:
            if PyImGui.button("Getting Started"):
                _ensure_getting_started_tree(auto_start=True)
        
        if botting_tree is not None and botting_tree.IsStarted():     
            PyImGui.same_line(0, -1)
            
            if botting_tree.IsPaused():
                if PyImGui.button("Unpause Routines"):
                    botting_tree.Pause(False)
            else:
                if PyImGui.button("Pause Routines"):
                    botting_tree.Pause(True)
                    
    if ImGui.collapsing_header("2. Capture Pet and Unlock Secondary Profession"):
        unlock_pet_tree = _ensure_unlock_pet_tree()
        ImGui.text_wrapped("This routine will capture the pet from the first quest and complete the necessary steps to unlock the secondary profession.")
        ImGui.text_wrapped("This is a separate routine because it involves a lot of waiting for the pet capture to succeed, which can take a long time and is not required to be done early on.")
        ImGui.separator()

        if unlock_pet_tree.IsStarted():
            if PyImGui.button("Stop Unlock Pet"):
                unlock_pet_tree.Stop()
        else:
            if PyImGui.button("Unlock Pet"):
                selected_debug_tree_name = UNLOCK_PET_TREE_NAME
                _ensure_unlock_pet_tree(auto_start=True)

        if unlock_pet_tree.IsStarted():
            PyImGui.same_line(0, -1)

            if unlock_pet_tree.IsPaused():
                if PyImGui.button("Unpause Unlock Pet"):
                    unlock_pet_tree.Pause(False)
            else:
                if PyImGui.button("Pause Unlock Pet"):
                    unlock_pet_tree.Pause(True)
                    
    if ImGui.collapsing_header("3. Acquire a Weapon"):
        acquire_weapon_tree = _ensure_acquire_weapon_tree()
        ImGui.text_wrapped("This section will cover acquiring a weapon for your character")
        ImGui.text_wrapped("Nevermore Flatbow is the best weapon to acquire in Pre-Searing, we will attempt to acquire it")
        ImGui.text_wrapped("If Nevermore is not available, we will fall back to Farming material for Buying a bow with a collector")
        ImGui.separator()

        if acquire_weapon_tree.IsStarted():
            if PyImGui.button("Stop Acquire Weapon"):
                acquire_weapon_tree.Stop()
        else:
            if PyImGui.button("Acquire Weapon"):
                selected_debug_tree_name = ACQUIRE_WEAPON_TREE_NAME
                _ensure_acquire_weapon_tree(auto_start=True)

        if acquire_weapon_tree.IsStarted():
            PyImGui.same_line(0, -1)

            if acquire_weapon_tree.IsPaused():
                if PyImGui.button("Unpause Acquire Weapon"):
                    acquire_weapon_tree.Pause(False)
            else:
                if PyImGui.button("Pause Acquire Weapon"):
                    acquire_weapon_tree.Pause(True)
              
      
def _draw_debug_tab():
    global selected_start_sequence, print_log_to_console, selected_debug_tree_name
    heroai_only_tree = _ensure_heroai_only_tree()

    if heroai_only_tree.IsStarted():
        if PyImGui.button("Stop HeroAI Only"):
            heroai_only_tree.Stop()
    else:
        if PyImGui.button("Start HeroAI Only"):
            selected_debug_tree_name = HEROAI_ONLY_TREE_NAME
            heroai_only_tree.Start()
    ImGui.separator()

    tree_names = _get_debug_tree_names()
    if tree_names:
        current_tree_index = tree_names.index(selected_debug_tree_name) if selected_debug_tree_name in tree_names else 0
        new_tree_index = PyImGui.combo("Debug Tree", current_tree_index, tree_names)
        if 0 <= new_tree_index < len(tree_names):
            selected_debug_tree_name = tree_names[new_tree_index]
    else:
        ImGui.text("No trees instantiated yet.")
        return

    botting_tree = _get_selected_debug_tree()
    if botting_tree is None:
        ImGui.text("Selected tree is unavailable.")
        return

    sequence_names = botting_tree.GetNamedPlannerStepNames()
    if sequence_names:
        current_index = sequence_names.index(selected_start_sequence) if selected_start_sequence in sequence_names else 0
        new_index = PyImGui.combo("Start From Sequence", current_index, sequence_names)
        if 0 <= new_index < len(sequence_names):
            selected_start_sequence = sequence_names[new_index]
        if PyImGui.button("Restart From Selected Sequence"):
            botting_tree = _ensure_getting_started_tree()
            botting_tree.RestartFromSequence(selected_start_sequence, auto_start=True, name="All quests sequence")
        ImGui.separator()
    else:
        ImGui.text("Selected tree has no planner sequences.")
        ImGui.separator()

    print_log_to_console = PyImGui.checkbox("Print Log To Console", print_log_to_console)
    if PyImGui.button("Clear UI Log"):
        botting_tree.ClearBlackboardLog()
        botting_tree.ClearBlackboardLogHistory()
    PyImGui.same_line(0, -1)
    if PyImGui.button("Copy UI Log"):
        log_history = botting_tree.GetBlackboardLogHistory()
        PyImGui.set_clipboard_text("\n".join(log_history))
    ImGui.separator()
    
    if ImGui.collapsing_header("Draw Move Path Debug Options", flags=PyImGui.TreeNodeFlags.DefaultOpen):
        global draw_move_path, draw_move_path_labels, draw_move_path_thickness, draw_move_waypoint_radius, draw_move_current_waypoint_radius
        draw_move_path = PyImGui.checkbox("Draw Move Path", draw_move_path)
        draw_move_path_labels = PyImGui.checkbox("Draw Path Labels", draw_move_path_labels)
        draw_move_path_thickness = PyImGui.slider_float("Path Thickness", draw_move_path_thickness, 1.0, 6.0)
        draw_move_waypoint_radius = PyImGui.slider_float("Waypoint Radius", draw_move_waypoint_radius, 15.0, 100.0)
        draw_move_current_waypoint_radius = PyImGui.slider_float("Current Waypoint Radius", draw_move_current_waypoint_radius, 20.0, 120.0)
        
    log_history = botting_tree.GetBlackboardLogHistory()
    if PyImGui.begin_child("BeautifulPreSearingLog", (0, 200), True, PyImGui.WindowFlags.HorizontalScrollbar):
        reversed_log_history = log_history[::-1]
        for entry in reversed_log_history:
            PyImGui.text_wrapped(entry)
        #if log_history:
        #    PyImGui.set_scroll_here_y(1.0)
    PyImGui.end_child()
  
    
def draw():
    global INI_KEY
    global draw_move_path, draw_move_path_labels
    global draw_move_path_thickness, draw_move_waypoint_radius, draw_move_current_waypoint_radius
    if not INI_KEY:
        return
    getting_started_tree = botting_trees.get(GETTING_STARTED_TREE_NAME)
    PyImGui.set_next_window_size((BANNER_WIDTH + 20, 0))
    if ImGui.Begin(ini_key=INI_KEY, name="Beautiful Pre-Searing", flags=PyImGui.WindowFlags.AlwaysAutoResize):
        if ImGui.begin_tab_bar("MainTabBar##BeautifulPreSearing"):
            if ImGui.begin_tab_item("Welcome"):
                ImGui.DrawTexture(TEXTURE_PATH, BANNER_WIDTH, BANNER_HEIGHT)
                ImGui.separator()
                _draw_welcome_tab()
                ImGui.end_tab_item()
            if ImGui.begin_tab_item("Getting Started"):
                _draw_getting_started_tab(getting_started_tree)
                ImGui.end_tab_item()
            if ImGui.begin_tab_item("Outpost Unlocks"):
                pass
                ImGui.end_tab_item()
            if ImGui.begin_tab_item("Quests"):
                pass
                ImGui.end_tab_item()    
            if ImGui.begin_tab_item("Farms"):
                pass
                ImGui.end_tab_item()
            if ImGui.begin_tab_item("Debug"):
                _draw_debug_tab()
                ImGui.end_tab_item() 
            ImGui.end_tab_bar()
    ImGui.End(ini_key=INI_KEY)

#region main
def _add_config_vars():
    global INI_KEY
    IniManager().add_bool(INI_KEY, "show_tree", "Display", "ShowTree", default=True)
    IniManager().add_bool(INI_KEY, "enable_headless_heroai", "Behavior", "EnableHeadlessHeroAI", default=True)
    IniManager().add_bool(INI_KEY, "print_log_to_console", "Display", "PrintLogToConsole", default=True)
    IniManager().add_bool(INI_KEY, "draw_move_path", "Display", "DrawMovePath", default=True)
    IniManager().add_bool(INI_KEY, "draw_move_path_labels", "Display", "DrawMovePathLabels", default=False)
    IniManager().add_float(INI_KEY, "draw_move_path_thickness", "Display", "DrawMovePathThickness", default=2.0)
    IniManager().add_float(INI_KEY, "draw_move_waypoint_radius", "Display", "DrawMoveWaypointRadius", default=45.0)
    IniManager().add_float(INI_KEY, "draw_move_current_waypoint_radius", "Display", "DrawMoveCurrentWaypointRadius", default=65.0)

def main():
    global INI_KEY, initialized, print_log_to_console

    if not initialized:
        if not INI_KEY:
            INI_KEY = IniManager().ensure_key(INI_PATH, INI_FILENAME)
            if not INI_KEY:
                return
            _add_config_vars()
            IniManager().load_once(INI_KEY)

        print_log_to_console = IniManager().getBool(INI_KEY, "print_log_to_console", default=True)
        initialized = True

    for tree in botting_trees.values():
        tree.tick()

    selected_tree = _get_selected_debug_tree()
    if selected_tree is not None and draw_move_path:
        selected_tree.DrawMovePath(
            draw_labels=draw_move_path_labels,
            path_thickness=draw_move_path_thickness,
            waypoint_radius=draw_move_waypoint_radius,
            current_waypoint_radius=draw_move_current_waypoint_radius,
        )


if __name__ == "__main__":
    main()
