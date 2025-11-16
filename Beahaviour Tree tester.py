from Py4GWCoreLib import GLOBAL_CACHE,Console, ConsoleLog, BehaviorTree, Routines
import PyImGui


travel_bt: BehaviorTree | None = None
finished: bool = False


def draw_window():
    global travel_bt, finished

    if PyImGui.begin("map travel tester"):
        if PyImGui.button("Travel to Outpost 248 gtob by coroutine"):
            def _coro_travel(map_id: int):
                yield from Routines.Yield.Map.TravelToOutpost(map_id, log=True)  
            GLOBAL_CACHE.Coroutines.append(_coro_travel(248))
            
        if PyImGui.button("Travel to Outpost 248 gtob"):
            # Build a fresh tree when button is pressed
            root = Routines.BT.Map.TravelToOutpost(248, log=True)
            travel_bt = BehaviorTree(root)

        # If a tree is active, tick it every frame
        if travel_bt is not None and not finished:
            state = travel_bt.tick()

            # When finished (success or failure), clear it
            if state != BehaviorTree.NodeState.RUNNING:
                ConsoleLog("TravelBT", f"Travel BT finished with state: {state.name}", log=True)
                #travel_bt = None
                finished = True
                
        if PyImGui.button("Debug Print Tree"):
            if travel_bt is not None:
                travel_bt.print()
                
        if travel_bt is not None:
            travel_bt.draw()

    PyImGui.end()


def main():
    draw_window()


if __name__ == "__main__":
    main()
