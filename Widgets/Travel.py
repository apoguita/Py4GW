import Py4GW

from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import Timer
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import IconsFontAwesome5

import os
import time
module_name = "Outpost Travel"


projects_path = Py4GW.Console.get_projects_path()
ini_file_location = os.path.join(projects_path, "Widgets", "Config", "Travel.ini")

ini_handler = IniHandler(ini_file_location)
save_throttle_time = 1000
save_throttle_timer = Timer()
save_throttle_timer.Start()

game_throttle_time = 50
game_throttle_timer = Timer()
game_throttle_timer.Start()

class Config:
    global ini_handler, module_name
    def __init__(self):
        self.outposts = dict(zip(GLOBAL_CACHE.Map.GetOutpostIDs(), GLOBAL_CACHE.Map.GetOutpostNames()))
        self.selected_outpost_index = 0
        self.travel_history = []
        


widget_config = Config()
window_module = ImGui.WindowModule(
    module_name, 
    window_name="Outpost Travel", 
    window_size=(235, 145),
    window_flags=PyImGui.WindowFlags.NoFlag
)


config_module = ImGui.WindowModule(f"Config {module_name}", window_name="Travel to Outpost##Vanquish Monitor config", window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)

is_header1_expanded = False
is_header2_expanded = False


search_outpost = ""
is_traveling = False
is_map_ready = False
is_party_loaded = False

window_x = ini_handler.read_int(module_name +str(" Config"), "x", 100)
window_y = ini_handler.read_int(module_name +str(" Config"), "y", 100)
window_collapsed = ini_handler.read_bool(module_name +str(" Config"), "collapsed", False)

window_module.window_pos = (window_x, window_y)
window_module.collapse = window_collapsed

config_window_x = ini_handler.read_int(module_name +str(" Config"), "config_x", 100)
config_window_y = ini_handler.read_int(module_name +str(" Config"), "config_y", 100)
config_window_collapsed = ini_handler.read_bool(module_name +str(" Config"), "config_collapsed", False)

config_module.window_pos = (config_window_x, config_window_y)
config_module.collapse = config_window_collapsed

def configure():
    global widget_config, config_module, ini_handler
    global module_name, is_header1_expanded, is_header2_expanded

    if config_module.first_run:
        PyImGui.set_next_window_size(config_module.window_size[0], config_module.window_size[1])     
        PyImGui.set_next_window_pos(config_module.window_pos[0], config_module.window_pos[1])
        PyImGui.set_next_window_collapsed(config_module.collapse, 0)
        config_module.first_run = False

    new_collapsed = True
    end_pos = config_module.window_pos
    if PyImGui.begin(config_module.window_name, config_module.window_flags):
        new_collapsed = PyImGui.is_window_collapsed()
        
        PyImGui.text("Outpost Travel Configuration")
        PyImGui.separator()
        PyImGui.text("This widget allows you to travel to outposts.")
        PyImGui.text("You can search for outposts by name or initials.")
        PyImGui.text("you can also travel to an outpost by pressing Enter.")
        PyImGui.text("The travel history shows the last 5 outposts you traveled to.")
        PyImGui.separator()
        
        end_pos = PyImGui.get_window_pos()
    PyImGui.end()
    
    """if end_pos[0] != config_module.window_pos[0] or end_pos[1] != config_module.window_pos[1]:
        config_module.window_pos = (int(end_pos[0]), int(end_pos[1]))
        ini_handler.write_key(module_name + " Config", "config_x", str(int(end_pos[0])))
        ini_handler.write_key(module_name + " Config", "config_y", str(int(end_pos[1])))

    if new_collapsed != config_module.collapse:
        config_module.collapse = new_collapsed
        ini_handler.write_key(module_name + " Config", "config_collapsed", str(new_collapsed))"""
        

def DrawWindow():
    global is_traveling, widget_config, search_outpost, window_module
    global game_throttle_time, game_throttle_timer, save_throttle_time, save_throttle_timer
    global is_header1_expanded, is_header2_expanded, ini_handler, module_name
    
    padding1 = 80 if is_header1_expanded else 0
    padding2 = 80 if is_header2_expanded else 0
    
    try:
        if window_module.first_run:
              
            PyImGui.set_next_window_pos(window_module.window_pos[0], window_module.window_pos[1])
            PyImGui.set_next_window_collapsed(window_module.collapse, 0)
            window_module.first_run = False

        new_collapsed = True
        end_pos = window_module.window_pos

        if ImGui.gw_window.begin( name = window_module.window_name,
                                  pos  = (window_module.window_pos[0], window_module.window_pos[1]),
                                  size = (window_module.window_size[0], window_module.window_size[1] + padding1 + padding2),
                                  collapsed = window_module.collapse,
                                  pos_cond = PyImGui.ImGuiCond.FirstUseEver,
                                  size_cond = PyImGui.ImGuiCond.Always):
                                 
        #if PyImGui.begin(window_module.window_name, window_module.window_flags):
            new_collapsed = PyImGui.is_window_collapsed()
            PyImGui.push_item_width(150)
            search_outpost = PyImGui.input_text("##search outpost", search_outpost.lower())
            PyImGui.pop_item_width()
            ImGui.show_tooltip("You can search for full or partial outpost names and initials, press <Enter> to travel")
                            
            def generate_initials(name):
                return ''.join(word[0] for word in name.split() if word).lower()

            # Filter outposts based on search query
            filtered_outposts = [name for name in widget_config.outposts.values() if search_outpost.lower() in name.lower() or search_outpost.lower() in generate_initials(name)]
            filtered_ids = [k for k, v in widget_config.outposts.items() if v in filtered_outposts]

            PyImGui.same_line(0,-1)
            if PyImGui.button(IconsFontAwesome5.ICON_PLANE + "##Travel"):
                if filtered_outposts:
                    selected_id = filtered_ids[widget_config.selected_outpost_index]
                    GLOBAL_CACHE.Map.Travel(selected_id)
                    widget_config.travel_history.append(filtered_outposts[widget_config.selected_outpost_index])
                    is_traveling = True
            ImGui.show_tooltip("Travel")
            
            if PyImGui.collapsing_header("Outposts"):
                is_header1_expanded = True
                if PyImGui.begin_child("OutpostList",(195, 75), True, PyImGui.WindowFlags.NoFlag):
                    for index, outpost_name in enumerate(filtered_outposts):
                        is_selected = (index == widget_config.selected_outpost_index)
                        if PyImGui.selectable(outpost_name, is_selected, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0)):
                            widget_config.selected_outpost_index = index
                            selected_id = filtered_ids[index]
                            GLOBAL_CACHE.Map.Travel(selected_id)
                            widget_config.travel_history.append(outpost_name)
                            is_traveling = True
                    PyImGui.end_child()
            else:
                is_header1_expanded = False


            # Travel when pressing Enter in the search box
            imgui_io = PyImGui.get_io()
            if imgui_io.want_capture_keyboard and PyImGui.is_key_pressed(13):  # ASCII code for Enter key
                if filtered_outposts:
                    selected_id = filtered_ids[widget_config.selected_outpost_index]
                    GLOBAL_CACHE.Map.Travel(selected_id)
                    widget_config.travel_history.append(filtered_outposts[widget_config.selected_outpost_index])
                    is_traveling = True
                    
            if PyImGui.collapsing_header("History"):
                is_header2_expanded = True
                if PyImGui.begin_child("TravelHistoryList", (195, 75), True, PyImGui.WindowFlags.NoFlag):
                    for index, history_name in enumerate(widget_config.travel_history[-5:]):  # Last 5 entries
                        if PyImGui.selectable(history_name, False, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0)):
                            # Find outpost ID and travel
                            for k, v in widget_config.outposts.items():
                                if v == history_name:
                                    GLOBAL_CACHE.Map.Travel(k)
                                    is_traveling = True
                                    break
                    PyImGui.end_child()
            else:
                is_header2_expanded = False

            end_pos = PyImGui.get_window_pos()
        #PyImGui.end()
        ImGui.gw_window.end(window_module.window_name)

        """if save_throttle_timer.HasElapsed(save_throttle_time):
            if end_pos[0] != window_module.window_pos[0] or end_pos[1] != window_module.window_pos[1]:
                window_module.window_pos = (int(end_pos[0]), int(end_pos[1]))
                ini_handler.write_key(module_name + " Config", "x", str(int(end_pos[0])))
                ini_handler.write_key(module_name + " Config", "y", str(int(end_pos[1])))

            if new_collapsed != window_module.collapse:
                window_module.collapse = new_collapsed
                ini_handler.write_key(module_name + " Config", "collapsed", str(new_collapsed))"""
                
            #save_throttle_timer.Reset()

    except Exception as e:
        is_traveling = False
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Debug)


def main():
    """Required main function for the widget"""
    global game_throttle_timer, game_throttle_time
    global is_map_ready, is_party_loaded
    try:
        if game_throttle_timer.HasElapsed(game_throttle_time):
            is_map_ready = GLOBAL_CACHE.Map.IsMapReady()
            is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
            game_throttle_timer.Start()
            
        if is_map_ready and is_party_loaded:
            DrawWindow()
            
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in main: {str(e)}", Py4GW.Console.MessageType.Debug)
        return False
    return True

# These functions need to be available at module level
__all__ = ['main', 'configure']

if __name__ == "__main__":
    main()