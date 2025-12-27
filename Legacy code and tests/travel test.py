import random
from time import sleep
from Py4GWCoreLib import *
import PyImGui

MODULE_NAME = "destroy item"
ping_handler = Py4GW.PingHandler()
map_id = 253
retries = 45
triggered = False

travel_coroutine = None  # active coroutine
wait_for_ping = True
ping_target = 70

started = False

def wait_for_map_load():
    global triggered, map_id, retries, started
    triggered = False
    while Map.GetMapID() != map_id:
        yield from Routines.Yield.wait(1)
    
    for _i in range(retries):
        Map.TravelToDistrict(map_id=795, district_number=2)
        yield from Routines.Yield.wait(0)
        
    triggered = True

def main():
    global map_id, travel_coroutine, triggered, retries, wait_for_ping, ping_target, started

    
    # Advance coroutine if running
    if travel_coroutine is not None:
        try:
            next(travel_coroutine)
        except StopIteration:
            travel_coroutine = None  # finished, ready for restart


    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        current_ping = ping_handler.GetCurrentPing()
        current_map = Map.GetMapName()
        if current_map is None:
            current_map = "Unknown"
        
        PyImGui.text(f"Current Map: {current_map} ({Map.GetMapID()})")
        PyImGui.text(f"Current Ping: {current_ping} ms")
        
        ping_target = PyImGui.input_int("Ping Target", ping_target)
        
        wait_for_ping = PyImGui.checkbox("Wait for ping under target", wait_for_ping)
        
        if wait_for_ping and current_ping <= ping_target and started and current_ping >0:
            started = False
            travel_coroutine = wait_for_map_load()
            Map.Travel(map_id)
            
        if not wait_for_ping and started:
            started = False
            travel_coroutine = wait_for_map_load()
            Map.Travel(map_id)
        
        retries = PyImGui.input_int("Retries", retries)
        
        map_id = PyImGui.input_int("Map ID", map_id)

        if PyImGui.button("travel"):
            started = True

        if started:
            PyImGui.text("Waiting  for ping..." if wait_for_ping else "Traveling...")
            
        if triggered:
            PyImGui.text("Travel complete!")
            
        PyImGui.separator()
        PyImGui.text("Tested Values:")
        PyImGui.text(f"Map ID: 253 Dwayna Vs grenth , retries = 25 to 35  ping target = 70")
        PyImGui.same_line(0,-1) 
        if PyImGui.button("Set Tested Values##dwayna"):
            map_id = 253
            retries = 27
            ping_target = 65
            wait_for_ping = False
            
        PyImGui.text(f"Map ID: 721 Costume Brawl, retries = 45 ping target = 70")
        PyImGui.same_line(0,-1)
        if PyImGui.button("Set Tested Values##costume"):
            map_id = 721
            retries = 45
            ping_target = 70
            wait_for_ping = False

        PyImGui.text(f"Map ID: 368 Dragon Arena, retries = 25 ping target = 70")
        PyImGui.same_line(0,-1)
        if PyImGui.button("Set Tested Values##dragon"):
            map_id = 368
            retries = 25
            ping_target = 70
            wait_for_ping = False
            
        PyImGui.text(f"Map ID: 467 Rollerbleetle racing, retries = 40 ping target = 70")
        PyImGui.same_line(0,-1)
        if PyImGui.button("Set Tested Values##roller"):
            map_id = 467
            retries = 40
            ping_target = 70
            wait_for_ping = False
            
        PyImGui.text(f"Map ID: 855 Snowball Fiht, retries = 45 ping target = 70")
        PyImGui.same_line(0,-1)
        if PyImGui.button("Set Tested Values##snowball"):
            map_id = 855
            retries = 45
            ping_target = 70
            wait_for_ping = False
            
        PyImGui.text(f"Map ID: 445 Cytadfel Of Mallyx, retries = 50 ping target = 85")
        PyImGui.same_line(0,-1)
        if PyImGui.button("Set Tested Values##mallyx"):
            map_id = 445
            retries = 50
            ping_target = 85
            wait_for_ping = False
        

    PyImGui.end()


if __name__ == "__main__":
    main()
