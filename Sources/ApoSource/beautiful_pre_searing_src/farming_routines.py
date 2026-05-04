from typing import Callable, cast

from Py4GWCoreLib.enums import Range
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree

from .globals import *
from .helpers import *


def _coerce_tree(
    subtree_or_builder: Callable[[], object] | BehaviorTree | BehaviorTree.Node,
) -> BehaviorTree:
    subtree = subtree_or_builder() if callable(subtree_or_builder) else subtree_or_builder
    if isinstance(subtree, BehaviorTree):
        return subtree
    if isinstance(subtree, BehaviorTree.Node):
        return BehaviorTree(subtree)
    if hasattr(subtree, "root") and hasattr(subtree, "tick") and hasattr(subtree, "reset"):
        return cast(BehaviorTree, subtree)
    raise TypeError(f"Farming subtree returned invalid type {type(subtree).__name__}.")


def FarmUntilItemQuantityReached(
    start_map_id: int,
    perform_farming_tree: Callable[[], object] | BehaviorTree | BehaviorTree.Node,
    model_id: int,
    target_quantity: int,
    exclude_models: list[int] | None = None,
) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.RepeaterUntilSuccessNode(
            name="FarmUntilItemQuantityReached",
            child=BehaviorTree.SequenceNode(
                name="FarmUntilItemQuantityReachedLoop",
                children=[
                    LogMessage("Starting farming routine"),
                    BT.Travel(start_map_id),
                    merchant_cleanup(
                        exclude_models=exclude_models,
                        destroy_zero_value_items=True,
                    ),
                    exit_current_map(),
                    LogMessage("Running farming node"),
                    BehaviorTree.SubtreeNode(
                        name="PerformFarmingTree",
                        subtree_fn=lambda node: _coerce_tree(perform_farming_tree),
                    ),
                    BehaviorTree.SelectorNode(
                        name="ReachedTargetQuantityOrRepeat",
                        children=[
                            BehaviorTree.SequenceNode(
                                name="TargetQuantityReached",
                                children=[
                                    BT.HasItemQuantity(model_id, target_quantity),
                                    LogMessage("Target quantity reached"),
                                ],
                            ),
                            BehaviorTree.SequenceNode(
                                name="TravelBackAndRepeat",
                                children=[
                                    LogMessage("Target quantity not reached, restarting routine"),
                                    BT.Travel(start_map_id),
                                    BehaviorTree.FailerNode(
                                        name="RepeatFarmRoutine",
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        )
    )

#region Skale
def FarmSkale() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="PlaceholderSkaleFinFarmingTree",
            children=[
                BT.MoveAndKill(Vec2f(13065.83, -341.11)),
                BT.MoveAndKill(Vec2f(10418.65, -4477.17)),
                BT.MoveAndKill(Vec2f(12632.47, -5684.44)),
                BT.MoveAndKill(Vec2f(8144.24, -7266.16)),
                BT.MoveAndKill(Vec2f(4788.96, -2886.89)),
                BT.MoveAndKill(Vec2f(2088.00, -7671.96)),
                BT.MoveAndKill(Vec2f(141.71, -6063.07)),
                BT.MoveAndKill(Vec2f(-1927.23, -13360.05)),
                BT.MoveAndKill(Vec2f(-3635.13, -16086.29)),
            ],
        )
    )



def SkaleFarmLoopTree() -> BehaviorTree:
    return FarmUntilItemQuantityReached(
        start_map_id=ASCALON_CITY_MAP_ID,
        perform_farming_tree=FarmSkale,
        model_id=SKALE_FIN_MODEL_ID,
        target_quantity=5,
        exclude_models=ITEMS_BLACKLIST,
    )
    
def RunAllFarmsTree() -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="RunAllFarms",
            children=[
                subtree_step("Skale Fin Farm", lambda: SkaleFarmLoopTree()),
            ],
        )
    )
