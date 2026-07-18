# -*- coding: utf-8 -*-
from Py4GWCoreLib import *
import os
module_name = "Loot Pickit2 Manager"

#script_directory = os.path.dirname(os.path.abspath(__file__))
#root_directory = os.path.normpath(os.path.join(script_directory, ".."))
#ini_file_location = os.path.join(root_directory, "Widgets/Config/LootPickitManager.ini")
#matching_items = []

#ini_handler = IniHandler(ini_file_location)



# LootConfigclass to hold loot configurations
class LootConfigclass:
    def __init__(self):
    
        self.include_model_id_in_tooltip = False
        
        self.loot_whites = False
        self.loot_blues = False
        self.loot_purples = False
        self.loot_golds = False
        self.loot_greens = False
        
        # Alcohol Loot Configuration
        self.loot_bottle_of_rice_wine = False       # 1 Point
        self.loot_bottle_of_vabbian_wine = False    # 1 Point
        self.loot_dwarven_ale = False               # 1 Point
        self.loot_eggnog = False                    # 1 Point
        self.loot_hard_apple_cider = False          # 1 Point
        self.loot_hunters_ale = False               # 1 Point
        self.loot_shamrock_ale = False              # 1 Point
        self.loot_vial_of_absinthe = False          # 1 Point
        self.loot_witchs_brew = False               # 1 Point
        self.loot_zehtukas_jug = False              # 1 Point
        self.loot_aged_dwarven_ale = False          # 3 Points
        self.loot_bottle_of_grog = False            # 3 Points
        self.loot_krytan_brandy = False             # 3 Points
        self.loot_spiked_eggnog = False             # 3 Points
        self.loot_battle_isle_iced_tea = False      # 50 Points
        
        # Sweets Loot Configuration


# Ensure the Loot_Variables is initialized before using it
#no need to declare explicit types on python Loot_Variables = type('LootVariables', (object,), {})()  # Create a simple object to hold bot variables
#it is a good practice to define types as it helps with readability and maintainability
#but in python it is not strictly necessary
Loot_Variables = LootConfigclass()  # Initialize the LootConfigclass
#careful not mistaking both names, they are very similar
loot_filter_singleton = LootConfig()
temp_model_id = 0

window_module = ImGui.WindowModule(module_name, window_name="Loot Pickit2 Manager", window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)

#window_x = ini_handler.read_int(module_name + str(" Config"), "x", 100)
#window_y = ini_handler.read_int(module_name + str(" Config"), "y", 100)
#window_collapsed = ini_handler.read_bool(module_name + str(" Config"), "collapsed", False)

#window_module.window_pos = (window_x, window_y)
#window_module.collapse = window_collapsed

def DrawWindow():
    global Loot_Variables, loot_filter_singleton, temp_model_id

    try:
        if window_module.first_run:
            PyImGui.set_next_window_size(window_module.window_size[0], window_module.window_size[1])     
            PyImGui.set_next_window_pos(window_module.window_pos[0], window_module.window_pos[1])
            PyImGui.set_next_window_collapsed(window_module.collapse, 0)
            window_module.first_run = False

        new_collapsed = True
        end_pos = window_module.window_pos

        if PyImGui.begin(window_module.window_name, window_module.window_flags):
            new_collapsed = PyImGui.is_window_collapsed()
            
            PyImGui.text("basic loot settings")
            
            PyImGui.text(f"Loot Whites: {Loot_Variables.loot_whites}")
            PyImGui.text(f"Loot Blues: {Loot_Variables.loot_blues}")
            PyImGui.text(f"Loot Purples: {Loot_Variables.loot_purples}")
            PyImGui.text(f"Loot Golds: {Loot_Variables.loot_golds}")
            PyImGui.text(f"Loot Greens: {Loot_Variables.loot_greens}")
            
                
            PyImGui.separator()
            PyImGui.text("Filtered Loot Array")
            loot_array = loot_filter_singleton.GetfilteredLootArray()
            if loot_array:
                for item in loot_array:
                    PyImGui.text(f"ModelID: {item}")
            else:
                PyImGui.text("No items in the filtered loot array.")
            
            
            PyImGui.separator()
            PyImGui.text("Loot Settings")
            
                        # Add the checkbox for "Include ModelID In Hovered Text"
            Loot_Variables.include_model_id_in_tooltip = PyImGui.checkbox("ModelID In Hovered Text", Loot_Variables.include_model_id_in_tooltip)

            
            PyImGui.separator()

            PyImGui.end()
    except Exception as e:
        frame = inspect.currentframe()
        current_function = frame.f_code.co_name if frame else "Unknown"
        Py4GW.Console.Log("LootConfigGUI", f"Error in {current_function}: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def configure():
    pass

def main():
    DrawWindow()

if __name__ == "__main__":
    main()
