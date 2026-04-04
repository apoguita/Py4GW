from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.routines_src.BehaviourTrees import BT as RoutinesBT

from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.ApoSource.beautiful_pre_searing_src.helpers import LogMessage, exit_current_map, merchant_cleanup


botting_tree: BottingTree | None = None
selected_start_sequence = "Sequence_001_Common"


def configure_upkeep_trees(tree: BottingTree) -> BottingTree:
    tree.SetUpkeepTrees([
        (
            "OutpostImpService",
            lambda: RoutinesBT.Upkeepers.OutpostImpService(
                target_bag=1,
                slot=0,
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


def ensure_botting_tree() -> BottingTree:
    global botting_tree
    if botting_tree is None:
        botting_tree = configure_upkeep_trees(BottingTree())
    return botting_tree


def CommonMapExit(
    travel_map_id: int,
    path_tree: BehaviorTree,
    exclude_models: list[int] | None = None,
) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="CommonMapExit",
            children=[
                LogMessage("Starting outpost unlock routine"),
                BT.TravelToOutpost(travel_map_id),
                merchant_cleanup(
                    exclude_models=exclude_models,
                    destroy_zero_value_items=True,
                ),
                exit_current_map(),
                LogMessage("Running outpost path"),
                BehaviorTree.SubtreeNode(
                    name="PerformOutpostPath",
                    subtree_fn=lambda node: path_tree,
                ),
            ],
        ),
    )
