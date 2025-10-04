import json
from Py4GWCoreLib import *

LOCATIONS_FILE = "locations.json"
recorded_locations = []


def save_locations():
    with open(LOCATIONS_FILE, "w") as f:
        json.dump(recorded_locations, f, indent=4)


def load_locations():
    try:
        with open(LOCATIONS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def main():
    global recorded_locations
    if not recorded_locations:
        recorded_locations = load_locations()

    if PyImGui.begin("Locations Manual"):
        PyImGui.text("Manually Record")
        PyImGui.separator()

        # === Buttons ===
        if PyImGui.button("RECORD"):
            x, y = GLOBAL_CACHE.Player.GetXY()
            recorded_locations.append((x, y))
            save_locations()
            ConsoleLog('Recorder', f"Recorded location: ({x}, {y})")

        if PyImGui.button("CLEAR ALL"):
            recorded_locations.clear()
            save_locations()
            ConsoleLog('Recorder', "Cleared all recorded locations.")

        PyImGui.separator()

        # === Table of recorded coords ===
        if PyImGui.begin_table("Recorded Locations", 2):  # 2 columns
            PyImGui.table_setup_column("X")
            PyImGui.table_setup_column("Y")
            PyImGui.table_headers_row()

            for loc in recorded_locations:
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text(str(loc[0]))
                PyImGui.table_next_column()
                PyImGui.text(str(loc[1]))

            PyImGui.end_table()

        PyImGui.end()


if __name__ == "__main__":
    main()
