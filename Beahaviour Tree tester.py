from Py4GWCoreLib import GLOBAL_CACHE,Console, ConsoleLog, BehaviorTree, Routines, Utils
from Py4GWCoreLib import ActionQueueManager, ControlAction
import PyImGui
from typing import List, Tuple, Callable, Optional
import random


test_bt: BehaviorTree | None = None
finished: bool = False
input_data = ""
result_agent_id = 0

def SellItems(item_array:list[int], log=False) -> BehaviorTree:
    def _valid_array_check(node, item_array:list[int]) -> BehaviorTree.NodeState:
        if len(item_array) == 0:
                ActionQueueManager().ResetQueue("MERCHANT")
                return BehaviorTree.NodeState.FAILURE
        node.blackboard.set("item_array", item_array)
        node.blackboard.set("current_index", 0)
        node.blackboard.set("total_items", len(item_array))
            
        return BehaviorTree.NodeState.SUCCESS
    
    def _sell_item_action(node) -> BehaviorTree.NodeState:
        item_array = node.blackboard.get("item_array", [])
        current_index = node.blackboard.get("current_index", 0)
        total_items = node.blackboard.get("total_items", 0)
        
        if current_index >= total_items:
            return BehaviorTree.NodeState.FAILURE
        
        item_id = item_array[current_index]

        ConsoleLog("SellItems", f"Selling item {current_index + 1}/{total_items}: ItemID {item_id}", log=log)
        
        quantity = GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)
        value = GLOBAL_CACHE.Item.Properties.GetValue(item_id)
        cost = quantity * value
        GLOBAL_CACHE.Trading.Merchant.SellItem(item_id, cost)
        
        return BehaviorTree.NodeState.SUCCESS
    
    def _wait_for_item_sold(node) -> BehaviorTree.NodeState:
        if ActionQueueManager().IsEmpty("MERCHANT"):
            ConsoleLog("SellItems", "Item sold successfully.", log=log)
            return BehaviorTree.NodeState.SUCCESS
        return BehaviorTree.NodeState.RUNNING
    
    tree = BehaviorTree.SequenceNode(name="SellItemsSequence",
        children=[
            BehaviorTree.ActionNode(name="ValidArrayCheck", action_fn=lambda node:_valid_array_check(node,item_array) , aftercast_ms=100),
            BehaviorTree.RepeaterUntilFailureNode(name="SellItemsRepeater",
                child=BehaviorTree.SequenceNode(name="SellItemSequence",
                    children=[
                        BehaviorTree.ActionNode(name="SellItemAction", action_fn=_sell_item_action, aftercast_ms=100),
                        BehaviorTree.WaitUntilNode(name="WaitForItemSold",condition_fn=lambda node:_wait_for_item_sold(node), throttle_interval_ms =50),
                    ]
                ),
            ),
        ],
    )
    return BehaviorTree(root=tree)

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
