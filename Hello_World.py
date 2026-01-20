import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Routines import Routines


def _coro_travel_in_loop():
    while True:
        Map.TravelGH()
        while True:
            in_guild_hall = Map.IsGuildHall()
            if not in_guild_hall:
                yield from Routines.Yield.wait(1000)
            else:
                break
        yield from Routines.Yield.wait(1500)
        Map.LeaveGH()
        while True:
            in_guild_hall = Map.IsGuildHall()
            if in_guild_hall or not Routines.Checks.Map.MapValid():
                yield from Routines.Yield.wait(1000)
            else:
                break
        yield from Routines.Yield.wait(1500)

input_string = ""

def draw_window():
    global input_string
    if PyImGui.begin("player test"): 
        if PyImGui.button("Start Travel GH Loop"):
            GLOBAL_CACHE.Coroutines.append(_coro_travel_in_loop())

        if PyImGui.button("Stop All Coroutines"):
            GLOBAL_CACHE.Coroutines.clear()

    PyImGui.end()

def main():
    draw_window()

if __name__ == "__main__":
    main()
