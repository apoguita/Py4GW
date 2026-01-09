from Py4GWCoreLib import *

module_name = "Simple State Machine"

RED,GREEN,YELLOW = "RED","GREEN","YELLOW"
current_state = RED
traffic_light_timer = Timer()
traffic_light_timer.Start()

def TrafficLight():
    global module_name, current_state, traffic_light_timer
    try:
        if current_state == RED:
            if traffic_light_timer.HasElapsed(5000):
                current_state = GREEN
                traffic_light_timer.Reset()
        elif current_state == GREEN:
            if traffic_light_timer.HasElapsed(5000):
                current_state = YELLOW
                traffic_light_timer.Reset()
        elif current_state == YELLOW:
            if traffic_light_timer.HasElapsed(2000):
                current_state = RED
                traffic_light_timer.Reset()

    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in TrafficLight: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def DrawWindow():
    global module_name, current_state, traffic_light_timer
    try:
        if PyImGui.begin(module_name):
        
            PyImGui.text("Traffic Light")
            PyImGui.separator()

            if current_state == RED:
                PyImGui.text_colored("RED",(1, 0, 0, 1))

            if current_state == GREEN:
                PyImGui.text_colored("GREEN",(0, 1, 0, 1))

            if current_state == YELLOW:
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
