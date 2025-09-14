from Py4GWCoreLib import *
import time

wait_time = 0
times_to_retry_delay = 5
delay_retries = 0



map_to_travel = 445  # rollerbeetle map
travel_coroutine = None  # active coroutine

loading_start_time = 0.0
loading_end_time = 0.0
mallyx_explorable_start = 0.0
mallyx_explorable_end = 0.0

ping_handler = Py4GW.PingHandler()
stop = False

def wait_for_map_load():
    global wait_time, map_to_travel, stop
    global times_to_retry_delay, delay_retries

    traveled_to_795 = False  

    yield from Routines.Yield.wait(500) #time to wait for the map start loading
    while True:
        if Map.IsMapLoading():
            yield from Routines.Yield.wait(1)

        if Map.IsOutpost():
            map_id = Map.GetMapID()

            if map_id == 81:  # Ascalon City
                traveled_to_795 = False
                yield from Routines.Yield.wait(500) #time to wait on ascalon city
                Map.Travel(map_to_travel)
                yield from Routines.Yield.wait(500) #time to wait for the map start loading

            elif not traveled_to_795 and map_id == map_to_travel:  # Mallyx
                if not Map.IsMapLoading():
                    sleep(0.3)
                    yield from Routines.Yield.wait(wait_time)
                    Map.TravelToDistrict(map_id=795, district_number=2)
                    delay_retries += 1
                    ConsoleLog("retry",
                        f"Attempt {delay_retries}/{times_to_retry_delay} at wait {wait_time} ms"
                    )
                    traveled_to_795 = True

                    # 🔑 If we’ve exhausted retries, bump delay and reset counter
                    if delay_retries >= times_to_retry_delay:
                        wait_time += 1
                        delay_retries = 0
                        ConsoleLog("retry", f"Retries exhausted, increasing wait_time to {wait_time} ms")
                else:
                    ConsoleLog("travel", f"Too late, map is loading again")

        if stop:
            stop = False
            return

        yield from Routines.Yield.wait(1)


        
        
def DrawWindow():
    global travel_coroutine, wait_time, map_to_travel
    global mallyx_explorable_start, mallyx_explorable_end
    global loading_start_time, times_to_retry_delay, delay_retries, stop

    if PyImGui.begin("Travel Test", True, PyImGui.WindowFlags.AlwaysAutoResize):
        current_ping = ping_handler.GetCurrentPing()
        PyImGui.text(f"Current Ping: {current_ping} ms")
        times_to_retry_delay = PyImGui.input_int("Retries on delay", times_to_retry_delay)
        
        
        wait_time = PyImGui.input_int("Wait Time (ms)", wait_time)
        map_to_travel = PyImGui.input_int("Map ID", map_to_travel)

        if PyImGui.button("Travel"):
            loading_start_time = 0.0
            mallyx_explorable_end = 0.0
            mallyx_explorable_start = 0.0
            
            Map.Travel(map_to_travel)

            # Always start fresh coroutine on button press
            travel_coroutine = wait_for_map_load()
            
        if PyImGui.button("Stop"):
            stop = True  # signal coroutine to stop
            travel_coroutine = None  # clear coroutine

    PyImGui.end()

def main():
    global travel_coroutine, loading_start_time, loading_end_time
    global mallyx_explorable_start, mallyx_explorable_end

    # Detect map loading
    if Map.IsMapLoading():
        # Leaving explorable -> record duration
        if mallyx_explorable_end == 0.0 and mallyx_explorable_start != 0.0:
            mallyx_explorable_end = time.perf_counter()
            duration = mallyx_explorable_end - mallyx_explorable_start
            duration_ms = (mallyx_explorable_end - mallyx_explorable_start) * 1000.0
            ConsoleLog("map load", f"Mallyx explorable active time: {duration_ms:.1f} ms")

            mallyx_explorable_start = 0.0
            mallyx_explorable_end = 0.0

        # Loading start
        if loading_start_time == 0.0:
            loading_start_time = time.perf_counter()

    else:
        # Entering explorable -> mark start
        if mallyx_explorable_start == 0.0:
            map_id = Map.GetMapID()
            if map_id == 445:  # mallyx explorable
                mallyx_explorable_start = time.perf_counter()

        # Loading finished -> measure duration
        if loading_start_time != 0.0 and loading_end_time == 0.0:
            loading_end_time = time.perf_counter()
            load_duration = loading_end_time - loading_start_time
            map_name = Map.GetMapName()
            load_duration_ms = (loading_end_time - loading_start_time) * 1000.0
            #ConsoleLog("map load", f"Map loaded in {load_duration_ms:.1f} ms to {map_name}")

            loading_start_time = 0.0
            loading_end_time = 0.0

    DrawWindow()

    # Advance coroutine if running
    if travel_coroutine is not None:
        try:
            next(travel_coroutine)
        except StopIteration:
            travel_coroutine = None  # finished, ready for restart
