import Py4GW
from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"

fsm = FSM("TestFSM",log_actions=False)

number = 0
def add_number():
    global number
    number += 1
    print(f"Current number: {number}")
    
def add_number_yield():
    global number
    number += 1
    print(f"Current number (yield): {number}")
    yield from Routines.Yield.wait(1000)  # Simulate a delay for demonstration purposes

fsm.AddState(name="Add1",
             execute_fn=lambda: add_number(),
             transition_delay_ms=1000,
             exit_condition=lambda: True
             )

fsm.AddState(name="Add2",
             execute_fn=lambda: add_number(),
             transition_delay_ms=1000,
             exit_condition=lambda: True
             )

fsm.AddState(name="Add3",
             execute_fn=lambda: add_number(),
             transition_delay_ms=1000,
             exit_condition=lambda: True
             )

fsm.AddState(name="Add4",
             execute_fn=lambda: add_number(),
             transition_delay_ms=1000,
             exit_condition=lambda: True
             )

fsm.AddState(name="Add5",
             execute_fn=lambda: add_number(),
             transition_delay_ms=1000,
             exit_condition=lambda: True
             )

fsm.AddYieldRoutineStep(
    name="AddNumberYield 6",
    coroutine_fn=add_number_yield,
)

fsm.AddYieldRoutineStep(
    name="AddNumberYield 7",
    coroutine_fn=add_number_yield,
)

fsm.AddYieldRoutineStep(
    name="AddNumberYield 8",
    coroutine_fn=add_number_yield,
)

fsm.AddYieldRoutineStep(
    name="AddNumberYield 9",
    coroutine_fn=add_number_yield,
)

fsm.AddYieldRoutineStep(
    name="AddNumberYield 10",
    coroutine_fn=add_number_yield,
)



fsm_started = False

def main():
    global fsm, fsm_started
    try:
        window_flags=PyImGui.WindowFlags.AlwaysAutoResize #| PyImGui.WindowFlags.MenuBar
        if PyImGui.begin("fsm test", window_flags):
            if PyImGui.button("start fsm"):
                fsm.restart()
            
            
        PyImGui.end()
        
        if fsm.is_started():
            fsm.update()


    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


    
if __name__ == "__main__":
    main()
