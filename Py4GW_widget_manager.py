from typing import Optional
import PyImGui
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.enums_src.IO_enums import Key

from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import LayoutMode, Py4GWLibrary, WidgetHandler, get_widget_handler
import os

MODULE_NAME = "Widget Manager"
          
#region Main
# ------------------------------------------------------------
# Config
# ------------------------------------------------------------
widget_manager : WidgetHandler = get_widget_handler()
py4_gw_library : Optional[Py4GWLibrary] = None 

INI_KEY = ""
INI_PATH = "Widgets/WidgetManager"
INI_FILENAME = "WidgetManager.ini"

def _add_config_vars():
    global INI_KEY
    IniManager().add_bool(key=INI_KEY, var_name="enable_all", section="Configuration", name="enable_all", default=True)
    IniManager().add_bool(key=INI_KEY, var_name="use_library", section="Configuration", name="use_library", default=True)
    
    IniManager().add_int(key=INI_KEY, var_name="max_suggestions", section="Configuration", name="max_suggestions", default=10)
    IniManager().add_int(key=INI_KEY, var_name="single_button_size", section="Configuration", name="single_button_size", default=48)
    IniManager().add_str(key=INI_KEY, var_name="startup_layout", section="Configuration", name="startup_layout", default=LayoutMode.LastView.name)  
    IniManager().add_str(key=INI_KEY, var_name="layout", section="Configuration", name="layout", default=LayoutMode.Library.name)  
    IniManager().add_str(key=INI_KEY, var_name="hotkey", section="Configuration", name="hotkey", default=Key.Unmapped.name)
    IniManager().add_str(key=INI_KEY, var_name="hotkey_modifiers", section="Configuration", name="hotkey_modifiers", default="NoneKey")
    IniManager().add_str(key=INI_KEY, var_name="reload_hotkey", section="Configuration", name="reload_hotkey", default=Key.Unmapped.name)
    IniManager().add_str(key=INI_KEY, var_name="reload_hotkey_modifiers", section="Configuration", name="reload_hotkey_modifiers", default="NoneKey")
    IniManager().add_bool(key=INI_KEY, var_name="single_filter", section="Configuration", name="single_filter", default=True)
    IniManager().add_bool(key=INI_KEY, var_name="jump_to_minimalistic", section="Configuration", name="jump_to_minimalistic", default=False)
    IniManager().add_float(key=INI_KEY, var_name="library_width", section="Configuration", name="library_width", default=900)
    IniManager().add_float(key=INI_KEY, var_name="library_height", section="Configuration", name="library_height", default=600)
                            
    IniManager().add_str(key=INI_KEY, var_name="favorites", section="Favorites", name="favorites", default="")
    
    IniManager().add_bool(key=INI_KEY, var_name="show_configure_button", section="Card Configuration", name="show_configure_button", default=True)
    IniManager().add_bool(key=INI_KEY, var_name="show_images", section="Card Configuration", name="show_images", default=True)
    IniManager().add_bool(key=INI_KEY, var_name="show_separator", section="Card Configuration", name="show_separator", default=True)
    IniManager().add_bool(key=INI_KEY, var_name="show_category", section="Card Configuration", name="show_category", default=True)
    IniManager().add_bool(key=INI_KEY, var_name="show_tags", section="Card Configuration", name="show_tags", default=True)
    IniManager().add_bool(key=INI_KEY, var_name="fixed_card_width", section="Card Configuration", name="fixed_card_width", default=False)
    
    IniManager().add_float(key=INI_KEY, var_name="card_width", section="Card Configuration", name="card_width", default=300)
    
    IniManager().add_bool(key=INI_KEY, var_name="show_images_compact", section="Card Configuration", name="show_images_compact", default=False)
    
    IniManager().add_str(key=INI_KEY, var_name="card_color", section="Card Configuration", name="card_color", default="200, 200, 200, 20")
    IniManager().add_str(key=INI_KEY, var_name="card_enabled_color", section="Card Configuration", name="card_enabled_color", default="90, 255, 90, 30")
    IniManager().add_str(key=INI_KEY, var_name="favorites_color", section="Card Configuration", name="favorites_color", default="255, 215, 0, 255")
    IniManager().add_str(key=INI_KEY, var_name="tag_color", section="Card Configuration", name="tag_color", default="38, 51, 59, 255")
    IniManager().add_str(key=INI_KEY, var_name="category_color", section="Card Configuration", name="category_color", default="150, 150, 150, 255")
    IniManager().add_str(key=INI_KEY, var_name="name_color", section="Card Configuration", name="name_color", default="255, 255, 255, 255")
    IniManager().add_str(key=INI_KEY, var_name="name_enabled_color", section="Card Configuration", name="name_enabled_color", default="255, 255, 255, 255")
    IniManager().add_float(key=INI_KEY, var_name="card_rounding", section="Card Configuration", name="card_rounding", default=4.0)
    
    for cv in widget_manager.config_vars:
        # Match the suffix to determine the 'name' inside the INI file
        ini_key_name = "enabled" if cv.var_name.endswith("__enabled") else "optional"

        IniManager().add_bool(
            key=INI_KEY,
            section=cv.section,
            var_name=cv.var_name,
            name=ini_key_name,
            default=False
        )
        
def update():
    #return #deprecated in place of callbacks
    if widget_manager.enable_all:
        widget_manager.execute_enabled_widgets_update()
    
def draw():
    return #deprecated in place of callbacks
    if widget_manager.enable_all:
        widget_manager.execute_enabled_widgets_draw()     
        
widget_manager_initialized = False
widget_manager_initializing = False

def main():
    global INI_KEY, widget_manager_initialized, widget_manager_initializing, py4_gw_library

    if not INI_KEY:
        if not os.path.exists(INI_PATH):
            os.makedirs(INI_PATH, exist_ok=True)

        INI_KEY = IniManager().ensure_global_key(
            INI_PATH,
            INI_FILENAME
        )
        
        if not INI_KEY: return
        
        widget_manager.MANAGER_INI_KEY = INI_KEY
        
        widget_manager.discover()
        _add_config_vars()
        IniManager().load_once(INI_KEY)

        # FIX 1: Explicitly load the global manager state into the handler
        widget_manager.enable_all = bool(IniManager().get(key=INI_KEY, var_name="enable_all", default=False, section="Configuration"))
        widget_manager._apply_ini_configuration()
            

    if INI_KEY:
        use_library = bool(IniManager().get(key=INI_KEY, var_name="use_library", default=True, section="Configuration"))
        if use_library:
            if py4_gw_library is None:
                py4_gw_library = Py4GWLibrary(INI_KEY, MODULE_NAME, widget_manager)
        
            py4_gw_library.draw_window()
        else:
            if ImGui.Begin(ini_key=INI_KEY, name="Widget Manager", flags=PyImGui.WindowFlags.AlwaysAutoResize):
                widget_manager.draw_ui(INI_KEY)
            ImGui.End(INI_KEY)
    
    if widget_manager.enable_all:
        #deprecated in place of callbacks
        #widget_manager.execute_enabled_widgets_main()
        widget_manager.execute_configuring_widgets()


if __name__ == "__main__":
    main()
