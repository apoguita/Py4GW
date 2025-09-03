import os
import PyImGui
from Py4GWCoreLib import *

show_consumables_selector = False
consumable_state = {
    "Cupcake": False,
    "Alcohol": False,
    "Morale": False,
    "CitySpeed": False,
}

# one icon per category, reusing your existing item-texture convention
ICON_MODEL = {
    "Cupcake":   ModelID.Birthday_Cupcake,
    "Alcohol":   ModelID.Hunters_Ale,
    "Morale":    ModelID.Honeycomb,
    "CitySpeed": ModelID.Sugary_Blue_Drink,
}
# === Paths and Constants ===

def _texture_path(model_id):
    base_path = os.path.abspath(os.path.join(os.getcwd(), '..', '..'))
    texture_name = f"[{model_id.value}] - {model_id.name.replace('_', ' ')}.png"
    return os.path.join(base_path, "Textures", "Item Models", texture_name)

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
        ("Alcohol",   ICON_MODEL["Alcohol"],   "Any Alcohol"),
        ("Morale",    ICON_MODEL["Morale"],    "Any Morale Boost"),
        ("CitySpeed", ICON_MODEL["CitySpeed"], "Any City Speed"),
    ]

    for i, (key, model_id, tip) in enumerate(items):
        PyImGui.push_id(key)
        selected = consumable_state[key]
        new_selected = ImGui.image_toggle_button(key, _texture_path(model_id), selected, 40, 40)
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