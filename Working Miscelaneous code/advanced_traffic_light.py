from Py4GWCoreLib import *

module_name = "Simple State Machine"

traffic_light_timer = Timer()
traffic_light_timer.Start()

state_machine = FSM("Traffic Light")

state_machine.AddState(name = "RED",
                       execute_fn = lambda: traffic_light_timer.Reset(),
                       exit_condition = lambda: traffic_light_timer.HasElapsed(5000))
state_machine.AddState(name = "GREEN",
                       execute_fn = lambda: traffic_light_timer.Reset(),
                       exit_condition = lambda: traffic_light_timer.HasElapsed(5000))
state_machine.AddState(name = "YELLOW",
                       execute_fn = lambda: traffic_light_timer.Reset(),
                       exit_condition = lambda: traffic_light_timer.HasElapsed(2000))
state_machine.start()
state_machine.SetLogBehavior(False)

def TrafficLight():
    global module_name, state_machine
    try:
        state_machine.update()   

        if state_machine.is_finished():
            state_machine.reset()

    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in TrafficLight: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def DrawWindow():
    global module_name, state_machine, traffic_light_timer
    try:
        if PyImGui.begin(module_name):
        
            PyImGui.text("Traffic Light")
            PyImGui.separator()

            if state_machine.get_current_step_name() == "RED":
                PyImGui.text_colored("RED",(1, 0, 0, 1))

            if state_machine.get_current_step_name() == "GREEN":
                PyImGui.text_colored("GREEN",(0, 1, 0, 1))

            if state_machine.get_current_step_name() == "YELLOW":
                PyImGui.text_colored("YELLOW",(1, 1, 0, 1))

            PyImGui.text(f"Timer: {traffic_light_timer.GetElapsedTime()/1000:.2f} seconds.")
                    
            PyImGui.end()
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def main():
    global module_name
    try:
        TrafficLight()
        DrawWindow()

    except ImportError as e:
        Py4GW.Console.Log(module_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(module_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(module_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass

if __name__ == "__main__":
    main()
