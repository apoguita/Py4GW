from Py4GWCoreLib import GLOBAL_CACHE,Console, ConsoleLog, BehaviorTree, Routines, Utils
from Py4GWCoreLib import TITLE_NAME
import PyImGui


test_bt: BehaviorTree | None = None
finished: bool = False
input_data = ""
result_agent_id = 0
    
def draw_window():
    global test_bt, finished, input_data, result_agent_id

    hard_mode = True
    if PyImGui.begin("map travel tester"):
        input_data = PyImGui.input_text("agent name", input_data)
        if PyImGui.button("search for agent with name(tree):"):
            test_bt = None
            finished = False
            test_bt = Routines.BT.Agents.GetAgentIDByName(input_data)
            
        if PyImGui.button("search for agent with name(coro):"):
            def _coro_get_name(agent_name=input_data, hard_mode=True, log=True):
                result = yield from Routines.Yield.Agents.GetAgentIDByName(agent_name)
                ConsoleLog("AgentIDResult", f"Result Agent ID: {result}", log=log)
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

        # If a tree is active, tick it every frame
        if test_bt is not None and not finished:
            state = test_bt.tick()

            # When finished (success or failure), clear it
            if state != BehaviorTree.NodeState.RUNNING:
                ConsoleLog("SetHardMode", f"SetHardMode finished with state: {state.name}", log=True)
                result_agent_id = test_bt.blackboard.get("result", 0)
                ConsoleLog("AgentIDResult", f"Result Agent ID: {result_agent_id}", log=True)
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
