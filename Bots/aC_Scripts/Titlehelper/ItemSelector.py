import PyImGui
from Py4GWCoreLib import *
from Py4GWCoreLib.enums import ModelID
import os

show_item_selector = False
toggle_state = {
    "Alcohol": {},
    "Sweets": {},
    "Party": {}
}

alcohol_items = {
    "1 point - Alcohol": [
        ModelID.Bottle_Of_Rice_Wine,
        ModelID.Eggnog,
        ModelID.Dwarven_Ale,
        ModelID.Hard_Apple_Cider,
        ModelID.Hunters_Ale,
        ModelID.Bottle_Of_Juniberry_Gin,
        ModelID.Shamrock_Ale,
        ModelID.Bottle_Of_Vabbian_Wine,
        ModelID.Vial_Of_Absinthe,     
        ModelID.Witchs_Brew,      
        ModelID.Zehtukas_Jug,
    ],
    "3 points - Alcohol": [
        ModelID.Aged_Dwarven_Ale,
        ModelID.Aged_Hunters_Ale,
        ModelID.Bottle_Of_Grog,
        ModelID.Flask_Of_Firewater,
        ModelID.Keg_Of_Aged_Hunters_Ale,
        ModelID.Krytan_Brandy,
        ModelID.Spiked_Eggnog,
    ],
    "50 points - Alcohol": [
        ModelID.Battle_Isle_Iced_Tea,
    ],
}

sweets_items = {
    "1 Point - Sweets": [
        ModelID.Fruitcake,
        ModelID.Mandragor_Root_Cake,
        ModelID.Sugary_Blue_Drink,
    ],
    "2 Points - Sweets": [
        ModelID.Chocolate_Bunny,
        ModelID.Red_Bean_Cake,
        ModelID.Jar_Of_Honey,

    ],
    "3 Points - Sweets": [
        ModelID.Creme_Brulee,
        ModelID.Krytan_Lokum,
        ModelID.Minitreat_Of_Purity,
    ],
    "50 points - Sweets": [
        ModelID.Delicious_Cake,
    ],
}

party_items = {
    "1 Point - Party": [
        ModelID.Bottle_Rocket,
        ModelID.Champagne_Popper,
        ModelID.Sparkler,
        ModelID.Snowman_Summoner,
        ModelID.Squash_Serum,
    ],
    "50 Points - Party": [
        ModelID.Party_Beacon,
    ],
}

def init_toggle_state():
    for cat, items in [("Alcohol", alcohol_items), ("Sweets", sweets_items), ("Party", party_items)]:
        for model_id in items:
            toggle_state[cat][model_id] = False

def draw_item_selector_window():
    global show_item_selector
    
    expanded, show_item_selector = PyImGui.begin_with_close("TitleHelper Options", show_item_selector, PyImGui.WindowFlags.AlwaysAutoResize)

    if not show_item_selector:
        PyImGui.end()
        return
    
    for group_name, group_items in [
        ("Alcohol", alcohol_items),
        ("Sweets", sweets_items),
        ("Party", party_items)
    ]:
        if group_name not in toggle_state:
            toggle_state[group_name] = {}

        for row_items in group_items.values():  
            for model_id in row_items:
                if model_id not in toggle_state[group_name]:
                    toggle_state[group_name][model_id] = False


    for group_name, group_items in [
        ("Alcohol", alcohol_items),
        ("Sweets", sweets_items),
        ("Party", party_items)
    ]:
        #PyImGui.text_colored(group_name, (0.9, 0.8, 0.3, 1.0))

        for row_label, model_ids in group_items.items():
            PyImGui.text_colored(row_label, (0.9, 0.8, 0.3, 1.0))

            for i, model_id in enumerate(model_ids):
                PyImGui.push_id(f"{group_name}_{row_label}_{i}")
                selected = toggle_state[group_name][model_id]
                new_selected = ImGui.image_toggle_button(str(model_id), get_texture_for_model(model_id), selected, 32, 32)
                toggle_state[group_name][model_id] = new_selected
                PyImGui.pop_id()

                if (i + 1) % 6 != 0:
                    PyImGui.same_line(0, 5)

            if len(model_ids) % 6 != 0:
                PyImGui.new_line()

        PyImGui.separator()

    PyImGui.end()

init_toggle_state()
