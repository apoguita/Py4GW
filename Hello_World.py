from Py4GWCoreLib import *
import PyMap, PyImGui

MODULE_NAME = "Pmap tester"

# Cache: map_id -> list of pathing maps
pathing_maps_cache: dict[int, list] = {}
current_map_id: int = 0


def main():
    global pathing_maps_cache, current_map_id

    if PyImGui.begin("Pmap Tester", PyImGui.WindowFlags.AlwaysAutoResize):
        # Show current map ID
        current_map_id = PyMap.PyMap().map_id.ToInt()
        PyImGui.text(f"Current Map ID: {current_map_id}")

        # Button to fetch pmaps
        if PyImGui.button("Fetch Pathing Maps"):
            pmaps = PyPathing.get_pathing_maps()
            pathing_maps_cache[current_map_id] = pmaps
            ConsoleLog(MODULE_NAME, f"Fetched {len(pmaps)} pmaps for map {current_map_id}")

        # If we already cached pmaps, show info
        if current_map_id in pathing_maps_cache:
            pmaps = pathing_maps_cache[current_map_id]
            PyImGui.text(f"Cached {len(pmaps)} pmaps for this map")

            for i, pmap in enumerate(pmaps):
                PyImGui.text(f"  Index {i}: zplane={pmap.zplane}, traps={len(pmap.trapezoids)}, portals={len(pmap.portals)}")

    PyImGui.end()


if __name__ == "__main__":
    main()
