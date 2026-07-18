import os
import PyImGui
from Py4GWCoreLib import *

show_consumables_selector = False
consumable_state = {
    "Cupcake": False,
    "CandyApple": False,
    "Alcohol": False,
    "Morale": False,
    "WarSupplies": False,
    "CitySpeed": False,
}

# one icon per category, reusing your existing item-texture convention
ICON_MODEL = {
    "Cupcake":   ModelID.Birthday_Cupcake,
    "CandyApple": ModelID.Candy_Apple,
    "Alcohol":   ModelID.Hunters_Ale,
    "Morale":    ModelID.Honeycomb,
    "WarSupplies": ModelID.War_Supplies,
    "CitySpeed": ModelID.Sugary_Blue_Drink,
}
# === Paths and Constants ===

def draw_consumables_selector_window():
    global show_consumables_selector

    expanded, show_consumables_selector = PyImGui.begin_with_close(
        "Choose Consumables", show_consumables_selector, PyImGui.WindowFlags.AlwaysAutoResize
    )
    if not show_consumables_selector:
        PyImGui.end()
        return

    items = [
        ("Cupcake",   ICON_MODEL["Cupcake"],   "Birthday Cupcake"),
        ("CandyApple", ICON_MODEL["CandyApple"], "Candy Apple"),    
        ("Alcohol",   ICON_MODEL["Alcohol"],   "Any Alcohol"),
        ("Morale",    ICON_MODEL["Morale"],    "Any Morale Boost"),
        ("WarSupplies", ICON_MODEL["WarSupplies"], "War Supplies"),  
        ("CitySpeed", ICON_MODEL["CitySpeed"], "Any City Speed"),
    ]

    for i, (key, model_id, tip) in enumerate(items):
        PyImGui.push_id(key)
        selected = consumable_state[key]
        new_selected = ImGui.image_toggle_button(key, get_texture_for_model(model_id), selected, 40, 40)
        consumable_state[key] = new_selected

        # optional: show a hover tooltip since we removed labels
        if PyImGui.is_item_hovered():
            PyImGui.set_tooltip(tip)  # or BeginTooltip/EndTooltip if your wrapper uses that

        PyImGui.pop_id()

        # keep them on one line (remove this if you want a 2x2 grid)
        if i < len(items) - 1:
            PyImGui.same_line(0, 6)

    PyImGui.end()

#def main():
#    draw_consumables_selector_window()
