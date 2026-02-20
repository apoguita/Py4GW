MODULE_NAME = "Py4GW Library"

import os
import traceback
import Py4GW
import PyImGui
from Py4GWCoreLib import ImGui, IniManager, Player
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.HotkeyManager import HOTKEY_MANAGER
from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
from Py4GWCoreLib.ImGui_src.Style import Style
from Py4GWCoreLib.enums_src.IO_enums import Key, ModifierKey
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.py4gwcorelib_src.Color import Color, ColorPalette
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import Widget, get_widget_handler

Utils.ClearSubModules(MODULE_NAME.replace(" ", ""))
from Sources.frenkeyLib.Py4GWLibrary.enum import LayoutMode
from Sources.frenkeyLib.Py4GWLibrary.library import ModuleBrowser
from Sources.frenkeyLib.Py4GWLibrary.module_cards import draw_widget_card


widget_filter = ""
widget_manager = get_widget_handler()
filtered_widgets : list[Widget] = []

INI_KEY = ""
INI_PATH = f"Widgets/{MODULE_NAME}"
INI_FILENAME = f"{MODULE_NAME}.ini"
module_browser : ModuleBrowser | None = None

def _add_config_vars():
    global INI_KEY
    IniManager().add_bool(key=INI_KEY, var_name="enable_all", section="Configuration", name="enable_all", default=False)
    IniManager().add_str(key=INI_KEY, var_name="favorites", section="Favorites", name="favorites", default="")
    IniManager().add_str(key=INI_KEY, var_name="default_layout", section="Configuration", name="default_layout", default=LayoutMode.Minimalistic.name)  
    IniManager().add_str(key=INI_KEY, var_name="hotkey", section="Configuration", name="hotkey", default=Key.Unmapped.name)  
    IniManager().add_str(key=INI_KEY, var_name="hotkey_modifiers", section="Configuration", name="hotkey_modifiers", default="NoneKey")
                            
    IniManager().add_bool(key=INI_KEY, var_name="show_configure_button", section="Card Configuration", name="show_configure_button", default=True)
    IniManager().add_bool(key=INI_KEY, var_name="show_images", section="Card Configuration", name="show_images", default=True)
    IniManager().add_bool(key=INI_KEY, var_name="show_separator", section="Card Configuration", name="show_separator", default=True)
    IniManager().add_bool(key=INI_KEY, var_name="show_category", section="Card Configuration", name="show_category", default=True)
    IniManager().add_bool(key=INI_KEY, var_name="show_tags", section="Card Configuration", name="show_tags", default=True)
    IniManager().add_bool(key=INI_KEY, var_name="fixed_card_width", section="Card Configuration", name="fixed_card_width", default=False)
    IniManager().add_float(key=INI_KEY, var_name="card_width", section="Card Configuration", name="card_width", default=300)
    
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
        
def on_enable():
    Py4GW.Console.Log(MODULE_NAME, f"{MODULE_NAME} loaded successfully.")

def on_disable():
    Py4GW.Console.Log(MODULE_NAME, f"{MODULE_NAME} unloaded successfully.")
    
def configure():
    Py4GW.Console.Log(MODULE_NAME, f"{MODULE_NAME} configuration opened.")

def draw():    
    global widget_filter
    
    if not INI_KEY:
        return
            
    if INI_KEY:
        global module_browser
        
        if module_browser is None:
            module_browser = ModuleBrowser(INI_KEY, MODULE_NAME, widget_manager)
            
        module_browser.draw_window()
    
def update():
    pass

def main():
    global INI_KEY
    
    if not INI_KEY:
        if not os.path.exists(INI_PATH):
            os.makedirs(INI_PATH, exist_ok=True)

        INI_KEY = IniManager().ensure_global_key(
            INI_PATH,
            INI_FILENAME
        )
        
        if not INI_KEY: return
        
        # widget_manager.MANAGER_INI_KEY = INI_KEY
        
        # widget_manager.discover()
        _add_config_vars()
        IniManager().load_once(INI_KEY)

        # FIX 1: Explicitly load the global manager state into the handler
        widget_manager.enable_all = bool(IniManager().get(key=INI_KEY, var_name="enable_all", default=False, section="Configuration"))
        widget_manager._apply_ini_configuration()
        
    
# These functions need to be available at module level
__all__ = ['on_enable', 'on_disable', 'configure', 'draw', 'update', 'main']

if __name__ == "__main__":
    main()
