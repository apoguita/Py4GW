from Py4GWCoreLib import *
from typing import Generator, Any

module_name = "Coroutine Traffic Light"

RED, GREEN, YELLOW, GRAY = "RED", "GREEN", "YELLOW", "GRAY"
current_state = RED
traffic_light_gen = None
traffic_light_timer = Timer()
traffic_light_timer.Start()

def wait(ms: int):
    start = time.time()
    while (time.time() - start) * 1000 < ms:
        yield

def traffic_light_coroutine() -> Generator[Any, Any, Any]:
    global current_state
    while True:
        current_state = RED
        yield from wait(3000)

        current_state = GREEN
        yield from wait(3000)

        current_state = YELLOW
        #flicker every 500 ms
        for _ in range(6):
            current_state = YELLOW if current_state == GRAY else GRAY
            yield from wait(500)


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
                
            if current_state == GRAY:
                PyImGui.text_colored("GRAY",(0.5, 0.5, 0, 1))

            PyImGui.text(f"Timer: {traffic_light_timer.GetElapsedTime()/1000:.2f} seconds.")
                    
            PyImGui.end()
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def main():
    global traffic_light_gen

    try:
        if traffic_light_gen is None:
            traffic_light_gen = traffic_light_coroutine()

        next(traffic_light_gen)
        DrawWindow()

    except StopIteration:
        traffic_light_gen = None  # Coroutine finished, restart next frame if needed
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in coroutine: {e}", Py4GW.Console.MessageType.Error)

if __name__ == "__main__":
    main()
