from Py4GWCoreLib import GLOBAL_CACHE,Console, ConsoleLog, BehaviorTree, Routines
from Py4GWCoreLib import TITLE_NAME
import PyImGui


test_bt: BehaviorTree | None = None
finished: bool = False

def draw_window():
    global test_bt, finished

    hard_mode = True
    if PyImGui.begin("map travel tester"):
        if PyImGui.button("Interact Target"):
            def _coro_hm(hard_mode=True, log=True):
                yield from Routines.Yield.Player.InteractTarget()
            GLOBAL_CACHE.Coroutines.append(_coro_hm(hard_mode=hard_mode, log=True))
            
        if PyImGui.button("Interact Target (Behavior Tree)"):
            # Build a fresh tree when button is pressed
            test_bt = Routines.BT.Player.InteractTarget(log=True)

        # If a tree is active, tick it every frame
        if test_bt is not None and not finished:
            state = test_bt.tick()

            # When finished (success or failure), clear it
            if state != BehaviorTree.NodeState.RUNNING:
                ConsoleLog("SetHardMode", f"SetHardMode finished with state: {state.name}", log=True)
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
