from Py4GWCoreLib import GLOBAL_CACHE,Console, ConsoleLog, BehaviorTree, Routines, Utils
from Py4GWCoreLib import TITLE_NAME, ControlAction
import PyImGui
from typing import List, Tuple, Callable, Optional


test_bt: BehaviorTree | None = None
finished: bool = False
input_data = ""
result_agent_id = 0

@staticmethod
def FollowPath(
    path_points: List[Tuple[float, float]],
    custom_exit_condition: Callable[[], bool] = lambda: False,
    tolerance: float = 150,
    log: bool = False,
    timeout: int = -1,
    progress_callback: Optional[Callable[[float], None]] = None,
    custom_pause_fn: Optional[Callable[[], bool]] = None,
    stop_on_party_wipe: bool = True
):
    """
    Builds a Behavior Tree that follows a path defined by a list of (x, y) coordinates.

    Args:
        path_points (List[Tuple[float, float]]): A list of (x, y) tuples defining the path to follow.
        custom_exit_condition (Callable[[], bool], optional): A function that returns True to exit the path following early.
        tolerance (float, optional): The distance tolerance to consider a point reached.
        log (bool, optional): Whether to log actions.
        timeout (int, optional): Maximum time in seconds to follow the path. -1 for no timeout.
        progress_callback (Optional[Callable[[float], None]], optional): A callback function that receives progress percentage.
        custom_pause_fn (Optional[Callable[[], bool]], optional): A function that returns True to pause movement.
        stop_on_party_wipe (bool, optional): Whether to stop if the party is wiped.

    Returns:
        BehaviorTree: A Behavior Tree that follows the specified path.
    """
    def _initialize(node):
        node.blackboard["path_points"] = path_points
        node.blackboard["custom_exit_condition"] = custom_exit_condition
        node.blackboard["tolerance"] = tolerance
        node.blackboard["log"] = log
        node.blackboard["timeout"] = timeout
        node.blackboard["progress_callback"] = progress_callback
        node.blackboard["custom_pause_fn"] = custom_pause_fn
        node.blackboard["stop_on_party_wipe"] = stop_on_party_wipe
        
        node.blackboard["current_index"] = 0
        node.blackboard["total_points"] = len(path_points)
        node.blackboard["retries"] = 0
        node.blackboard["max_retries"] = 30
        node.blackboard["stuck_counter"] = 0
        node.blackboard["max_stuck_counter"] = 2
        return BehaviorTree.NodeState.SUCCESS
    
    def continue_checks(node):
        def _failure(msg: str) -> BehaviorTree.NodeState:
            ConsoleLog("FollowPath", msg, Console.MessageType.Warning, log)
            return BehaviorTree.NodeState.FAILURE
        
        def _success(msg: str) -> BehaviorTree.NodeState:
            ConsoleLog("FollowPath", msg, Console.MessageType.Info, log)
            return BehaviorTree.NodeState.SUCCESS
        
        if not Routines.Checks.Map.MapValid():
            pass
        
        
            
        
        
    
    tree = BehaviorTree.SequenceNode(
        name="FollowPath",
        children=[
            BehaviorTree.ActionNode(name="Initialize", action_fn=_initialize),
            BehaviorTree.RepeaterUntilSuccessNode(name="FollowPoints", timeout_ms=timeout,
                child=BehaviorTree.SequenceNode(name="FollowPointSequence",
                    children=[  ])
            )
        ]
    )
    
    
def draw_window():
    global test_bt, finished, input_data, result_agent_id

    hard_mode = True
    if PyImGui.begin("map travel tester"):
        input_data = PyImGui.input_text("agent name", input_data)
        if PyImGui.button("search for agent with name(tree):"):
            test_bt = None
            finished = False
            test_bt = Routines.BT.Agents.TargetAgentByName(input_data)
            
        if PyImGui.button("search for agent with name(coro):"):
            def _coro_get_name(agent_name=input_data, hard_mode=True, log=True):
                yield from Routines.Yield.Agents.TargetAgentByName(agent_name)
            GLOBAL_CACHE.Coroutines.append(_coro_get_name(agent_name=input_data, hard_mode=hard_mode, log=True))
        
        
        if PyImGui.button("Interact Target"):
            def _coro_hm(hard_mode=True, log=True):
                yield from Routines.Yield.Player.InteractTarget()
            GLOBAL_CACHE.Coroutines.append(_coro_hm(hard_mode=hard_mode, log=True))
            
        if PyImGui.button("Interact Target (Behavior Tree)"):
            # Build a fresh tree when button is pressed
            test_bt = None
            finished = False
            test_bt = Routines.BT.Player.InteractTarget(log=True)
        
        if PyImGui.button("travel to 248 (by tree)"):
            test_bt = None
            finished = False
            test_bt = Routines.BT.Map.TravelToOutpost(outpost_id=248, log=True)
            
        if PyImGui.button("ToggleInventory(by coro)"):
            def _coro_toggle_inventory():
                yield from Routines.Yield.Keybinds.ToggleInventory(log=True)
            GLOBAL_CACHE.Coroutines.append(_coro_toggle_inventory())
            
        if PyImGui.button("ToggleInventory(by tree)"):
            test_bt = None
            finished = False
            test_bt = Routines.BT.Keybinds.PressKeybind(ControlAction.ControlAction_ToggleInventoryWindow.value, duration_ms=100, log=True)

        # If a tree is active, tick it every frame
        if test_bt is not None and not finished:
            state = test_bt.tick()

            # When finished (success or failure), clear it
            if state != BehaviorTree.NodeState.RUNNING:
                #result_agent_id = test_bt.blackboard.get("result", 0)
                #ConsoleLog("AgentIDResult", f"Result Agent ID: {result_agent_id}", log=True)
                #test_bt = None
                finished = True
                
        if PyImGui.button("Debug Print Tree"):
            if test_bt is not None:
                test_bt.print()
                
        
                
        if test_bt is not None:
            test_bt.draw()

    PyImGui.end()


def main():
    draw_window()


if __name__ == "__main__":
    main()
