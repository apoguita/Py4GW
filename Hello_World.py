from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree


initialized = False
INI_KEY = ""
INI_PATH = "Widgets/BottingTree"
INI_FILENAME = "BottingTree.ini"
botting_tree = None


def _build_example_planner_tree() -> BehaviorTree:
    def _planner_tick(node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        node.blackboard["PLANNER_NOTE"] = "User planner ticked"
        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree(
        root=BehaviorTree.ActionNode(
            name="ExamplePlannerTick",
            action_fn=lambda node: _planner_tick(node),
        )
    )


def _add_config_vars():
    global INI_KEY
    IniManager().add_bool(INI_KEY, "show_tree", "Display", "ShowTree", default=True)
    IniManager().add_bool(INI_KEY, "enable_headless_heroai", "Behavior", "EnableHeadlessHeroAI", default=True)


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
        botting_tree.SetPlannerTree(_build_example_planner_tree())
        initialized = True

    if botting_tree is not None:
        botting_tree.tick()


if __name__ == "__main__":
    main()
