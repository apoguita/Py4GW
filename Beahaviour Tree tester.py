from Py4GWCoreLib import GLOBAL_CACHE,Console, ConsoleLog, BehaviorTree, Routines, Utils
from Py4GWCoreLib import ActionQueueManager, ControlAction
import PyImGui
from typing import List, Tuple, Callable, Optional
import random


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
    def _initialize(node: BehaviorTree.ActionNode):
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
        ConsoleLog("FollowPath", f"Starting path with {len(path_points)} points.", Console.MessageType.Info, log=log)
        return BehaviorTree.NodeState.SUCCESS
    
    def _set_node_timestamp(node: BehaviorTree.ActionNode):
        node.blackboard["node_start_time"] = Utils.GetBaseTimestamp()
        idx = node.blackboard["current_index"]
        total_points = node.blackboard["total_points"]
        target_x, target_y = node.blackboard["path_points"][idx]
        ConsoleLog("FollowPath", f"Starting point {idx+1}/{total_points} - ({target_x}, {target_y})", Console.MessageType.Info, log=log)
        return BehaviorTree.NodeState.SUCCESS
    
    def _path_end_check(node: BehaviorTree.ConditionNode):
        idx = node.blackboard["current_index"]
        total_points = node.blackboard["total_points"]
        if idx >= total_points:
            ConsoleLog("FollowPath", "Reached end of path.", Console.MessageType.Info, log=log)
            return BehaviorTree.NodeState.FAILURE
        return BehaviorTree.NodeState.SUCCESS
    
    def _map_valid_check(node: BehaviorTree.ConditionNode):
        if Routines.Checks.Map.MapValid():
            return BehaviorTree.NodeState.SUCCESS
        ConsoleLog("FollowPath", "Map invalid before starting point, aborting.", Console.MessageType.Error, log=log)
        ActionQueueManager().ResetAllQueues()
        return BehaviorTree.NodeState.FAILURE
    
    def _party_wipe_check(node: BehaviorTree.ConditionNode):
        stop_on_party_wipe = node.blackboard.get("stop_on_party_wipe", True)
        if not stop_on_party_wipe:
            return BehaviorTree.NodeState.SUCCESS
        if Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated():
            ConsoleLog("FollowPath", "Party wiped detected, stopping all movement.", Console.MessageType.Warning, log=log)
            ActionQueueManager().ResetAllQueues()
            return BehaviorTree.NodeState.FAILURE
        return BehaviorTree.NodeState.SUCCESS
    
    def _custom_exit_check(node: BehaviorTree.ConditionNode):
        custom_exit_condition = node.blackboard["custom_exit_condition"]
        if custom_exit_condition and custom_exit_condition():
            ConsoleLog("FollowPath", "Custom exit condition met, stopping movement.", Console.MessageType.Info, log=log)
            return BehaviorTree.NodeState.FAILURE
        return BehaviorTree.NodeState.SUCCESS
    
    def _pause_status(node: BehaviorTree.ConditionNode):
        #everything returns success to allow further checks to run
        #RUNNING will pause the movement loop
        
        custom_pause_fn = node.blackboard.get("custom_pause_fn", None)
        
        if custom_pause_fn is None:
            return BehaviorTree.NodeState.SUCCESS
        
        map_valid = Routines.Checks.Map.MapValid()
        if not map_valid:
            return BehaviorTree.NodeState.SUCCESS
        
        stop_on_party_wipe = node.blackboard.get("stop_on_party_wipe", True)
        if stop_on_party_wipe and (Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated()):
            return BehaviorTree.NodeState.SUCCESS
        
        custom_exit_condition = node.blackboard["custom_exit_condition"]
        if custom_exit_condition and custom_exit_condition():
            return BehaviorTree.NodeState.SUCCESS
        
        if custom_pause_fn is not None and custom_pause_fn():
            ConsoleLog("FollowPath", "Custom pause condition met, pausing movement.", Console.MessageType.Info, log=log)
            node.blackboard["node_start_time"] = Utils.GetBaseTimestamp()
            return BehaviorTree.NodeState.RUNNING
        
        if GLOBAL_CACHE.Agent.IsCasting(GLOBAL_CACHE.Player.GetAgentID()):
            ConsoleLog("FollowPath", "Player is casting, pausing movement.", Console.MessageType.Info, log=log)
            #node.blackboard["node_start_time"] = Utils.GetBaseTimestamp()
            return BehaviorTree.NodeState.RUNNING
        
        if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            ConsoleLog("FollowPath", "Player is dead, pausing movement.", Console.MessageType.Info, log=log)
            node.blackboard["node_start_time"] = Utils.GetBaseTimestamp()
            return BehaviorTree.NodeState.RUNNING
        
        return BehaviorTree.NodeState.SUCCESS
    
    def _timeout_check(node: BehaviorTree.ConditionNode):
        timeout = node.blackboard["timeout"]
        if timeout <= 0:
            return BehaviorTree.NodeState.SUCCESS
        node_start_time = node.blackboard.get("node_start_time", Utils.GetBaseTimestamp())
        elapsed = Utils.GetBaseTimestamp() - node_start_time
        if elapsed >= timeout:
            ConsoleLog("FollowPath", f"Timeout of {timeout} reached, aborting path.", Console.MessageType.Error, log=log)
            ActionQueueManager().ResetAllQueues()
            return BehaviorTree.NodeState.FAILURE
        
        return BehaviorTree.NodeState.SUCCESS
        
    def _stuck_check(node: BehaviorTree.ConditionNode):
        now = Utils.GetBaseTimestamp()

        # --- throttle: only check every 250 ms ---
        last_check = node.blackboard.get("last_stuck_check", 0)
        if now - last_check < 250:
            return BehaviorTree.NodeState.RUNNING

        node.blackboard["last_stuck_check"] = now

        # --- fetch values ---
        stuck_count = node.blackboard.get("stuck_counter", 0)
        max_stuck_commands = node.blackboard.get("max_stuck_counter", 2)

        # previous + current coordinates
        prev_x, prev_y = node.blackboard.get("stuck_prev_coordinates", GLOBAL_CACHE.Player.GetXY())
        cur_x, cur_y = GLOBAL_CACHE.Player.GetXY()

        # compute travel distance since last check
        dist = Utils.Distance((prev_x, prev_y), (cur_x, cur_y))

        # update previous position for next cycle
        node.blackboard["stuck_prev_coordinates"] = (cur_x, cur_y)

        # --- movement threshold ---
        MOVEMENT_THRESHOLD = 25.0  # adjust later

        if dist < MOVEMENT_THRESHOLD:
            # No progress → increase stuck counter
            stuck_count += 1
            node.blackboard["stuck_counter"] = stuck_count

            if stuck_count > max_stuck_commands:
                ConsoleLog("FollowPath",
                        f"Stuck for too long ({stuck_count}), triggering strafe recovery.",
                        Console.MessageType.Warning, log=log)
                return BehaviorTree.NodeState.FAILURE

            # not moving yet but still within evaluation window
            return BehaviorTree.NodeState.RUNNING

        # --- progress detected → reset ---
        node.blackboard["stuck_counter"] = 0
        return BehaviorTree.NodeState.SUCCESS

    
    def _issue_move_command(node: BehaviorTree.ActionNode):
        idx = node.blackboard["current_index"]
        target_x, target_y = node.blackboard["path_points"][idx]

        # Current position
        current_x, current_y = GLOBAL_CACHE.Player.GetXY()

        # Distance toward target at the moment of issuing the command
        previous_distance = Utils.Distance((current_x, current_y), (target_x, target_y))
        node.blackboard["previous_distance"] = previous_distance

        # Store where we were when the move was issued (for stuck check)
        node.blackboard["stuck_prev_coordinates"] = (current_x, current_y)

        # Store where we intend to go
        node.blackboard["current_coordinates"] = (target_x, target_y)

        # Reset timing for movement detection
        now = Utils.GetBaseTimestamp()
        node.blackboard["time_since_movement"] = now

        # Reset stuck-related counters
        node.blackboard["stuck_counter"] = 0
        node.blackboard["retries"] = 0

        # Reset stuck check timer
        node.blackboard["last_stuck_check"] = 0

        # Issue movement
        GLOBAL_CACHE.Player.Move(target_x, target_y)
        ConsoleLog("FollowPath", f"Issued move command to ({target_x}, {target_y}).",Console.MessageType.Debug, log=log)

        return BehaviorTree.NodeState.SUCCESS

    
    def _reissue_move_command(node: BehaviorTree.ActionNode):
        idx = node.blackboard["current_index"]
        target_x, target_y = node.blackboard["path_points"][idx]

        now = Utils.GetBaseTimestamp()
        last_move_time = node.blackboard.get("time_since_movement", now)

        # ----- Get movement progress -----
        current_x, current_y = GLOBAL_CACHE.Player.GetXY()
        previous_distance = node.blackboard.get("previous_distance", None)
        current_distance = Utils.Distance((current_x, current_y), (target_x, target_y))

        # Save for next tick
        node.blackboard["previous_distance"] = current_distance
        node.blackboard["stuck_prev_coordinates"] = (current_x, current_y)

        # ----- Determine if approaching -----
        approaching = False
        if previous_distance is not None:
            approaching = (current_distance < previous_distance - 20)  # small tolerance

        # ----- Only count as stuck if NO progress for >= 1000ms -----
        elapsed = now - last_move_time
        if elapsed >= 1000:

            if not approaching:
                # REAL STUCK
                node.blackboard["time_since_movement"] = now
                node.blackboard["stuck_counter"] = node.blackboard.get("stuck_counter", 0) + 1

                GLOBAL_CACHE.Player.SendChatCommand("stuck")
                ConsoleLog("FollowPath",
                        "No progress made, sending /stuck command.",
                        Console.MessageType.Warning,
                        log=log)

            else:
                # Progress detected → reset timer
                node.blackboard["time_since_movement"] = now

        # ----- Issue move with small random offset -----
        offset_x = random.uniform(-5, 5)
        offset_y = random.uniform(-5, 5)

        GLOBAL_CACHE.Player.Move(target_x + offset_x, target_y + offset_y)
        ConsoleLog("FollowPath",
                f"Re-issued move command to ({target_x}, {target_y}).",
                Console.MessageType.Debug,
                log=log)

        return BehaviorTree.NodeState.SUCCESS


    
    def _aproaching_point(node: BehaviorTree.SelectorNode):
        #aproaching_throttle_start = node.blackboard.get("aproaching_throttle_start", Utils.GetBaseTimestamp())
        #now = Utils.GetBaseTimestamp()
        
        #   if now - aproaching_throttle_start < 250:
        return BehaviorTree.NodeState.SUCCESS
        
        idx = node.blackboard["current_index"]
        target_x, target_y = node.blackboard["path_points"][idx]
        tolerance = node.blackboard["tolerance"]

        current_x, current_y = GLOBAL_CACHE.Player.GetXY()
        current_distance = Utils.Distance((current_x, current_y), (target_x, target_y))

        previous_distance = node.blackboard.get("previous_distance", current_distance + 99999)

        # ----- Progress / approaching -----
        if current_distance < previous_distance:
            # Reset counters
            node.blackboard["retries"] = 0
            node.blackboard["stuck_counter"] = 0
            node.blackboard["time_since_movement"] = Utils.GetBaseTimestamp()

            # Save distance for next tick
            node.blackboard["previous_distance"] = current_distance

            # ----- Reached point -----
            if current_distance <= tolerance:
                ConsoleLog("FollowPath", f"Reached point {idx+1}.", Console.MessageType.Info, log=log)
                node.blackboard["current_index"] += 1

            else:
                ConsoleLog("FollowPath", "Progress detected, reset retry counters.",
                        Console.MessageType.Debug, log=log)

            return BehaviorTree.NodeState.SUCCESS

        # ----- Not approaching -----
        node.blackboard["previous_distance"] = current_distance
        return BehaviorTree.NodeState.FAILURE
    
    def _arrived_at_point(node: BehaviorTree.ConditionNode):
        idx = node.blackboard["current_index"]
        path = node.blackboard["path_points"]
        tolerance = node.blackboard["tolerance"]

        target_x, target_y = path[idx]

        current_x, current_y = GLOBAL_CACHE.Player.GetXY()
        current_distance = Utils.Distance((current_x, current_y), (target_x, target_y))

        # ---------------------------------------------------
        # NOT ARRIVED → keep RUNNING
        # ---------------------------------------------------
        if current_distance > tolerance:
            # Update progress variables
            node.blackboard["previous_distance"] = current_distance
            node.blackboard["current_coordinates"] = (current_x, current_y)

            # This point is still in progress
            return BehaviorTree.NodeState.RUNNING

        # ---------------------------------------------------
        # ARRIVED → advance point, reset all movement trackers
        # ---------------------------------------------------
        ConsoleLog("FollowPath",
                f"Arrived at point {idx+1}.",
                Console.MessageType.Info,
                log=log)

        # Advance index
        node.blackboard["current_index"] = idx + 1

        # Reset stuck/ retry counters
        node.blackboard["stuck_counter"] = 0
        node.blackboard["retries"] = 0

        # Reset timing and coordinates
        node.blackboard["time_since_movement"] = Utils.GetBaseTimestamp()
        node.blackboard["previous_distance"] = 0
        node.blackboard["current_coordinates"] = (current_x, current_y)

        return BehaviorTree.NodeState.SUCCESS



                
     
    tree = BehaviorTree.SequenceNode(
        name="FollowPath_Root",
        children=[
            BehaviorTree.ActionNode(name="Initialize",action_fn=lambda node: _initialize(node)),
            BehaviorTree.RepeaterUntilFailureNode(name="FollowPath",
                child=BehaviorTree.SequenceNode(name="FollowPath_Sequence",
                    children=[
                        BehaviorTree.ConditionNode(name="PathEndCheck",condition_fn=lambda node: _path_end_check(node)),
                        BehaviorTree.WaitUntilNode(name="CustomPauseCheck",condition_fn=lambda node: _pause_status(node),throttle_interval_ms=500),
                        BehaviorTree.ConditionNode(name="MapValidCheck",condition_fn=lambda node: _map_valid_check(node)),
                        BehaviorTree.ConditionNode(name="PartyWipeCheck",condition_fn=lambda node: _party_wipe_check(node)),
                        BehaviorTree.ConditionNode(name="CustomExitCheck",condition_fn=lambda node: _custom_exit_check(node)),
                        BehaviorTree.ActionNode(name="SetNodeTimestamp",action_fn=lambda node: _set_node_timestamp(node)),
                        BehaviorTree.ActionNode(name="IssueMoveCommand",action_fn=lambda node: _issue_move_command(node), aftercast_ms=250),
                        BehaviorTree.RepeaterUntilFailureNode(name="FollowToPoint",
                            child=BehaviorTree.SequenceNode(name="FollowToPoint_Sequence",
                                children=[
                                    BehaviorTree.ConditionNode(name="PathEndCheck",condition_fn=lambda node: _path_end_check(node)),
                                    BehaviorTree.WaitUntilNode(name="CustomPauseCheck",condition_fn=lambda node: _pause_status(node),throttle_interval_ms=250),
                                    BehaviorTree.ConditionNode(name="MapValidCheck",condition_fn=lambda node: _map_valid_check(node)),
                                    BehaviorTree.ConditionNode(name="PartyWipeCheck",condition_fn=lambda node: _party_wipe_check(node)),
                                    BehaviorTree.ConditionNode(name="CustomExitCheck",condition_fn=lambda node: _custom_exit_check(node)),
                                    BehaviorTree.ConditionNode(name="TimeoutCheck",condition_fn=lambda node: _timeout_check(node)), 
                                    BehaviorTree.ConditionNode(name="ArrivedAtPointCheck",condition_fn=lambda node: _arrived_at_point(node)),    
                                ]
                            )
                        )
                    ]
                )
            )
        ]  
    )

            
    return BehaviorTree(tree)

path_points_to_traverse_bjora_marches: List[Tuple[float, float]] = [
    (17810, -17649),(17516, -17270),(17166, -16813),(16862, -16324),(16472, -15934),
    (15929, -15731),(15387, -15521),(14849, -15312),(14311, -15101),(13776, -14882),
    (13249, -14642),(12729, -14386),(12235, -14086),(11748, -13776),(11274, -13450),
    (10839, -13065),(10572, -12590),(10412, -12036),(10238, -11485),(10125, -10918),
    (10029, -10348),(9909, -9778)  ,(9599, -9327)  ,(9121, -9009)  ,(8674, -8645)  ,
    (8215, -8289)  ,(7755, -7945)  ,(7339, -7542)  ,(6962, -7103)  ,(6587, -6666)  ,
    (6210, -6226)  ,(5834, -5788)  ,(5457, -5349)  ,(5081, -4911)  ,(4703, -4470)  ,
    (4379, -3990)  ,(4063, -3507)  ,(3773, -3031)  ,(3452, -2540)  ,(3117, -2070)  ,
    (2678, -1703)  ,(2115, -1593)  ,(1541, -1614)  ,(960, -1563)   ,(388, -1491)   ,
    (-187, -1419)  ,(-770, -1426)  ,(-1343, -1440) ,(-1922, -1455) ,(-2496, -1472) ,
    (-3073, -1535) ,(-3650, -1607) ,(-4214, -1712) ,(-4784, -1759) ,(-5278, -1492) ,
    (-5754, -1164) ,(-6200, -796)  ,(-6632, -419)  ,(-7192, -300)  ,(-7770, -306)  ,
    (-8352, -286)  ,(-8932, -258)  ,(-9504, -226)  ,(-10086, -201) ,(-10665, -215) ,
    (-11247, -242) ,(-11826, -262) ,(-12400, -247) ,(-12979, -216) ,(-13529, -53)  ,
    (-13944, 341)  ,(-14358, 743)  ,(-14727, 1181) ,(-15109, 1620) ,(-15539, 2010) ,
    (-15963, 2380) ,(-18048, 4223 ), (-19196, 4986),(-20000, 5595) ,(-20300, 5600)
    ]
    
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

        if PyImGui.button("Follow Path (Behavior Tree)"):
            test_bt = None
            finished = False
            test_bt = FollowPath(
                path_points=path_points_to_traverse_bjora_marches,
                tolerance=100,
                log=True,
                timeout=10000,
                stop_on_party_wipe=True
            )
        
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
