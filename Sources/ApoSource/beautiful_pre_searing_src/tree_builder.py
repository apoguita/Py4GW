from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.routines_src.BehaviourTrees import BT as RoutinesBT

from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Sources.ApoSource.beautiful_pre_searing_src.helpers import (
    LogMessage,
    equip_build_for_level,
    exit_current_map,
    merchant_cleanup,
)


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
    alternate_exit: str | None = None,
) -> BehaviorTree:
    return BehaviorTree(
        BehaviorTree.SequenceNode(
            name="CommonMapExit",
            children=[
                LogMessage("Common map exit routine started"),
                BT.TravelToOutpost(travel_map_id),
                equip_build_for_level(),
                merchant_cleanup(
                    exclude_models=exclude_models,
                    destroy_zero_value_items=True,
                ),
                exit_current_map(alternate_exit=alternate_exit),
                LogMessage("Running outpost path"),
                BehaviorTree.SubtreeNode(
                    name="PerformOutpostPath",
                    subtree_fn=lambda node: path_tree,
                ),
            ],
        ),
    )
