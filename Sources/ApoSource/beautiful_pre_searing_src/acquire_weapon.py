from typing import Callable

from Py4GWCoreLib.enums import Range
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree

from Sources.ApoSource.ApoBottingLib import wrappers as BT
from .globals import *
from .helpers import *


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


def FarmBow(exclude_models: list[int] | None = None) -> BehaviorTree:
    LAKESIDE_COUNTY_EXIT_COORDS_001: Vec2f = Vec2f(-12508.46, -6135.42)
    LAKESIDE_COUNTY_EXIT_COORDS_002: Vec2f = Vec2f(-10905, -6287)

    REGENT_VALLEY_MID_001_EXIT_COORDS: Vec2f = Vec2f(-6316.87, -6808.10)
    REGENT_VALLEY_MID_002_EXIT_COORDS: Vec2f = Vec2f(-4833.97, -12199.93)
    REGENT_VALLEY_OVER_BRIDGE_EXIT_COORDS: list[Vec2f] = [Vec2f(-3464.73, -13135.62)]
    REGENT_VALLEY_EXIT_COORDS: Vec2f = Vec2f(6516, -19822)

    KILLSPOT_COORDS: Vec2f = Vec2f(-14696.82, 10211.46)
    ROWNAN_COORDS: Vec2f = Vec2f(-17002.54, 10695.05)

    def _build_runtime_merchant_cleanup(node: BehaviorTree.Node) -> BehaviorTree:
        merchant_coords = get_merchant_coords_from_map_id()
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
            destroy_zero_value_items=True,
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
                            LogMessage("Exchanging 3 Dull Carapaces for Ascalon Hornbow"),
                            BT.ExchangeCollectorItem(
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
                ],
            ),
        )
    )


def AcquireWeapon() -> BehaviorTree:
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
                        EquipStarterBow(),
                        FarmBowUntilFlatbowEquipped(
                            exclude_models=ITEMS_BLACKLIST,
                        ),
                    ],
                ),
            ],
        )
    )
