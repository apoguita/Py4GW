# consumables_main.py
import PyImGui
from Py4GWCoreLib import *
import ConsumablesSelector

class ConsumablesHelper:
    def __init__(self):
        self.started = False

    def run(self):
        while True:
            if not self.started:
                yield from Routines.Yield.wait(500)
                continue

            # basic guards (same style as TitleHelper loop) :contentReference[oaicite:3]{index=3}
            if not Routines.Checks.Map.MapValid():
                yield from Routines.Yield.wait(1000)
                continue
            if Agent.IsDead(Player.GetAgentID()):
                yield from Routines.Yield.wait(1000)
                continue

            s = ConsumablesSelector.consumable_state

            if s.get("Cupcake", False):
                # uses ModelID.Birthday_Cupcake under the hood :contentReference[oaicite:4]{index=4}
                yield from Routines.Yield.Upkeepers.Upkeep_BirthdayCupcake()
            if s.get("Alcohol", False):
                # scans ALCOHOL_ITEMS and tops up drunk level :contentReference[oaicite:5]{index=5}
                yield from Routines.Yield.Upkeepers.Upkeep_Alcohol(target_alc_level=1,disable_drunk_effects=True)
            if s.get("Morale", False):
                # scans MORALE_ITEMS until morale >= 110 :contentReference[oaicite:6]{index=6}
                yield from Routines.Yield.Upkeepers.Upkeep_Morale(110)
            if s.get("CitySpeed", False):
                # outpost-only sugar rush/jolt upkeep via CITY_SPEED_ITEMS/EFFECTS :contentReference[oaicite:7]{index=7}
                yield from Routines.Yield.Upkeepers.Upkeep_City_Speed()

            # small idle between passes
            yield from Routines.Yield.wait(500)

def draw_consumables_window(helper):
    # --- Start/Stop toggle (green TEXT when running; default colors otherwise) ---
    was_running = helper.started
    label = "Cons: ON" if was_running else "Cons: OFF"

    if was_running:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.20, 0.90, 0.20, 1.0))

    clicked = PyImGui.button(label)

    if was_running:
        PyImGui.pop_style_color(1)  # pop green text

    if clicked:
        helper.started = not was_running
        if helper.started:
            ConsoleLog("FSM", "Starting consumable upkeep...", Console.MessageType.Debug)
        else:
            ConsoleLog("FSM", "Consumable upkeep stopped.", Console.MessageType.Debug)

    # --- Options button (yellow text, always) ---
    PyImGui.same_line(0, 10)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 1.0, 0.3, 1.0))
    if PyImGui.button("Options"):
        ConsumablesSelector.show_consumables_selector = True
    PyImGui.pop_style_color(1)

    if ConsumablesSelector.show_consumables_selector:
        ConsumablesSelector.draw_consumables_selector_window()

# === Instantiate & wire into your app loop (same as TitleHelper) ===
consumables_helper = ConsumablesHelper()
consumables_runner = consumables_helper.run()

def main():
    draw_consumables_window(consumables_helper)
    try:
        next(consumables_runner)
    except StopIteration:
        pass