import PyImGui

import Py4GW
from Py4GWCoreLib import ImGui, Utils
from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.routines_src.BehaviourTrees import BT

MODULE_NAME = "HeroAI Parallel Tree Example"
MODULE_ICON = "Textures/Module_Icons/Template.png"

INI_KEY = ""
INI_PATH = "Widgets/HeroAIParallelTreeExample"
INI_FILENAME = "HeroAIParallelTreeExample.ini"

botting_tree = None
initialized = False
move_test_x = -4479.24
move_test_y = 3038.50


def _add_config_vars():
    global INI_KEY
    IniManager().add_bool(INI_KEY, "show_tree", "Display", "ShowTree", default=True)
    IniManager().add_bool(INI_KEY, "enable_headless_heroai", "Behavior", "EnableHeadlessHeroAI", default=True)


def _tick_planner_service(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
    node.blackboard["planner_status"] = "Planner idle"
    node.blackboard["planner_owner"] = "Planner"
    return BehaviorTree.NodeState.RUNNING


def _build_planner_tree() -> BehaviorTree:
    def _require_active_test(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        if bool(node.blackboard.get("move_test_active", False)):
            return BehaviorTree.NodeState.SUCCESS
        return BehaviorTree.NodeState.FAILURE

    def _set_outbound_status(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        node.blackboard["planner_status"] = "Planner moving to destination"
        node.blackboard["planner_owner"] = "Planner"
        Py4GW.Console.Log("HeroAIParallelTreeExample", f"Starting outbound move to {node.blackboard.get('move_test_target')}.", Py4GW.Console.MessageType.Info)
        return BehaviorTree.NodeState.SUCCESS

    def _set_return_status(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        node.blackboard["planner_status"] = "Planner returning to origin"
        node.blackboard["planner_owner"] = "Planner"
        Py4GW.Console.Log("HeroAIParallelTreeExample", f"Starting return move to {node.blackboard.get('move_test_origin')}.", Py4GW.Console.MessageType.Info)
        return BehaviorTree.NodeState.SUCCESS

    def _complete_test(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        node.blackboard["move_test_active"] = False
        node.blackboard["move_test_status"] = "Finished"
        node.blackboard["planner_status"] = "Planner move test finished"
        node.blackboard["planner_owner"] = "Planner"
        Py4GW.Console.Log("HeroAIParallelTreeExample", "Move test completed.", Py4GW.Console.MessageType.Success)
        return BehaviorTree.NodeState.SUCCESS

    def _idle(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        return _tick_planner_service(node)

    return BehaviorTree(
        root=BehaviorTree.ChoiceNode(
            name="PlannerRoot",
            children=[
                BehaviorTree.SequenceNode(
                    name="MoveThereAndBack",
                    children=[
                        BehaviorTree.ActionNode(
                            name="RequireActiveMoveTest",
                            action_fn=lambda node: _require_active_test(node),
                        ),
                        BehaviorTree.ActionNode(
                            name="SetOutboundStatus",
                            action_fn=lambda node: _set_outbound_status(node),
                        ),
                        BehaviorTree.SubtreeNode(
                            name="MoveToDestination",
                            subtree_fn=lambda node: BT.Player.Move(
                                node.blackboard["move_test_target"][0],
                                node.blackboard["move_test_target"][1],
                                pause_on_combat=True,
                                log=False,
                            ),
                        ),
                        BehaviorTree.ActionNode(
                            name="SetReturnStatus",
                            action_fn=lambda node: _set_return_status(node),
                        ),
                        BehaviorTree.SubtreeNode(
                            name="MoveBackToOrigin",
                            subtree_fn=lambda node: BT.Player.Move(
                                node.blackboard["move_test_origin"][0],
                                node.blackboard["move_test_origin"][1],
                                pause_on_combat=True,
                                log=False,
                            ),
                        ),
                        BehaviorTree.ActionNode(
                            name="CompleteMoveTest",
                            action_fn=lambda node: _complete_test(node),
                        ),
                    ],
                ),
                BehaviorTree.ActionNode(
                    name="PlannerIdle",
                    action_fn=lambda node: _idle(node),
                ),
            ],
        )
    )


def _get_sequence_builders():
    return [
        ("MoveThereAndBack", _build_planner_tree),
    ]


def draw_widget():
    global INI_KEY, botting_tree, move_test_x, move_test_y

    if ImGui.Begin(INI_KEY, MODULE_NAME, flags=PyImGui.WindowFlags.AlwaysAutoResize):
        bb = botting_tree.blackboard if botting_tree is not None else {}

        PyImGui.text("Parallel service pattern:")
        PyImGui.bullet_text("HeroAI branch keeps combat and OOC handling alive.")
        PyImGui.bullet_text("Planner branch keeps thinking without stealing combat ownership.")
        PyImGui.bullet_text("Both branches stay RUNNING, so ParallelNode does not collapse.")
        PyImGui.separator()

        in_aggro = bool(botting_tree.headless_heroai.cached_data.data.in_aggro) if botting_tree is not None else False
        PyImGui.text(f"In aggro: {in_aggro}")
        PyImGui.text(f"HeroAI status: {bb.get('HEROAI_STATUS', 'n/a')}")
        PyImGui.text(f"HeroAI tick success: {bb.get('HEROAI_SUCCESS', False)}")
        PyImGui.text(f"Planner status: {bb.get('planner_status', bb.get('PLANNER_STATUS', 'n/a'))}")
        PyImGui.text(f"Current owner: {bb.get('planner_owner', bb.get('PLANNER_OWNER', 'n/a'))}")
        PyImGui.text(f"Move test status: {bb.get('move_test_status', 'Idle')}")
        if "move_test_origin" in bb:
            PyImGui.text(f"Origin: {bb['move_test_origin']}")
        if "move_test_target" in bb:
            PyImGui.text(f"Target: {bb['move_test_target']}")
        if botting_tree is not None and PyImGui.button(
            "Disable Headless HeroAI" if botting_tree.IsHeadlessHeroAIEnabled() else "Enable Headless HeroAI"
        ):
            botting_tree.SetHeadlessHeroAIEnabled(not botting_tree.IsHeadlessHeroAIEnabled())

        move_test_x = PyImGui.input_float("Target X", move_test_x)
        move_test_y = PyImGui.input_float("Target Y", move_test_y)
        if botting_tree is not None and PyImGui.button("Start Move Test"):
            origin_x, origin_y = Player.GetXY()
            botting_tree.planner_tree.reset()
            bb["move_test_origin"] = (float(origin_x), float(origin_y))
            bb["move_test_target"] = (float(move_test_x), float(move_test_y))
            bb["move_test_active"] = True
            bb["move_test_status"] = "Running"
            bb["planner_status"] = "Planner move test armed"
            bb["BT_TRACE"] = False
            bb["move_state"] = ""
            bb["move_reason"] = ""
            bb["move_path_index"] = 0
            bb["move_path_count"] = 0
            Py4GW.Console.Log(
                "HeroAIParallelTreeExample",
                f"Armed move test from {(float(origin_x), float(origin_y))} to {(float(move_test_x), float(move_test_y))}.",
                Py4GW.Console.MessageType.Info,
            )
            if not botting_tree.IsStarted():
                botting_tree.Start()

        show_tree = bool(IniManager().get(INI_KEY, "show_tree", True))
        new_show_tree = PyImGui.checkbox("Show Tree Debug", show_tree)
        if new_show_tree != show_tree:
            IniManager().set(INI_KEY, "show_tree", new_show_tree)
            show_tree = new_show_tree

        if show_tree and botting_tree is not None:
            PyImGui.separator()
            botting_tree.tree.draw()

    ImGui.End(INI_KEY)


def tooltip():
    PyImGui.begin_tooltip()
    PyImGui.text(MODULE_NAME)
    PyImGui.separator()
    PyImGui.text("Minimal example of running HeroAI as one parallel service")
    PyImGui.text("while a second planning service ticks alongside it.")
    PyImGui.end_tooltip()


def main():
    global INI_KEY, initialized, botting_tree

    if not initialized:
        if not INI_KEY:
            INI_KEY = IniManager().ensure_key(INI_PATH, INI_FILENAME)
            if not INI_KEY:
                return
            _add_config_vars()
            IniManager().load_once(INI_KEY)

        botting_tree = BottingTree(INI_KEY)
        botting_tree.SetNamedPlannerSteps(
            _get_sequence_builders(),
            start_from="MoveThereAndBack",
            name="HeroAIParallelPlanner",
        )
        botting_tree.blackboard["planner_status"] = "Idle"
        botting_tree.blackboard["move_test_status"] = "Idle"
        initialized = True

    if botting_tree is not None:
        botting_tree.tick()

    draw_widget()


if __name__ == "__main__":
    main()
