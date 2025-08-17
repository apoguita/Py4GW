import Py4GW

from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import Timer
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import IconsFontAwesome5

import os
import time

from Py4GWCoreLib.Py4GWcorelib import ConsoleLog
module_name = "Style Manager"

'''
Roadmap for those interested in contributing:
- Adding theme selection for the recently pushed Themes ('Guild Wars', 'Minimalus', 'ImGUI') [COMPLETED]
- Expand to support styling so users can select colors and values for various elements
    > Add a export / import feature for styles
'''
script_directory = os.path.dirname(os.path.abspath(__file__))
root_directory = os.path.normpath(os.path.join(script_directory, ".."))
ini_file_location = os.path.join(root_directory, "Widgets/Config/Style Manager.ini")

ini_handler = IniHandler(ini_file_location)
save_throttle_time = 1000
save_throttle_timer = Timer()
save_throttle_timer.Start()

game_throttle_time = 50
game_throttle_timer = Timer()
game_throttle_timer.Start()

window_module = ImGui.WindowModule(
    module_name, 
    window_name="Style Manager", 
    window_size=(235, 145),
    window_flags=PyImGui.WindowFlags.NoFlag,
    collapse=False,
    can_close=False
)

window_x = ini_handler.read_int(module_name +str(" Config"), "x", 100)
window_y = ini_handler.read_int(module_name +str(" Config"), "y", 100)
window_collapsed = ini_handler.read_bool(module_name +str(" Config"), "collapsed", False)
window_open = ini_handler.read_bool(module_name +str(" Config"), "open", True)

window_module.window_pos = (window_x, window_y)
window_module.collapse = window_collapsed
window_module.open = window_open
selected_theme = ini_handler.read_int(module_name + " Config", "theme", ImGui.StyleTheme.Guild_Wars.value)
themes = [theme.name.replace("_", " ") for theme in ImGui.StyleTheme]

ImGui.set_theme(ImGui.StyleTheme(selected_theme))

def configure():
    window_module.open = True        

def DrawWindow():
    global window_module, module_name, ini_handler, window_x, window_y, window_collapsed, window_open
    global game_throttle_time, game_throttle_timer, save_throttle_time, save_throttle_timer
    
    try:                
        if not window_module.open:
            return
                
        if window_module.begin():
            PyImGui.text("Selected Theme")
            value = PyImGui.combo("##theme_selector", ImGui.Theme.value, themes)
            
            if value != ImGui.Theme.value:
                ImGui.set_theme(ImGui.StyleTheme(value))
                ini_handler.write_key(module_name + " Config", "theme", ImGui.Theme.value)
                
                
            PyImGui.separator()
            PyImGui.text_wrapped("This widget will expand in the future to allow more customization of the styles.")        
        
            window_module.process_window()            
        window_module.end()

        if save_throttle_timer.HasElapsed(save_throttle_time):
            if window_module.window_pos[0] != window_module.end_pos[0] or window_module.window_pos[1] != window_module.end_pos[1]:
                window_module.window_pos = window_module.end_pos
                ini_handler.write_key(module_name + " Config", "x", str(int(window_module.window_pos[0])))
                ini_handler.write_key(module_name + " Config", "y", str(int(window_module.window_pos[1])))

            if window_module.collapsed_status != window_module.collapse:
                window_module.collapse = window_module.collapsed_status
                ini_handler.write_key(module_name + " Config", "collapsed", str(window_module.collapse))

            if window_open != window_module.open:
                window_open = window_module.open
                ini_handler.write_key(module_name + " Config", "open", str(window_module.open))
                
            save_throttle_timer.Reset()


    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Debug)


def main():
    """Required main function for the widget"""
    global game_throttle_timer, game_throttle_time, window_module
    
    try:            
        DrawWindow()
        window_module.open  = False
            
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in main: {str(e)}", Py4GW.Console.MessageType.Debug)
        return False
    return True

# These functions need to be available at module level
__all__ = ['main', 'configure']

if __name__ == "__main__":
    main()
