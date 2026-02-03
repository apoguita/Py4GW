import Py4GW
import PyImGui
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler
import os

module_name = "Widget Manager"
      
#region UI
def draw_window():
    global INI_KEY
    if ImGui.Begin(INI_KEY,MODULE_NAME, flags=PyImGui.WindowFlags.AlwaysAutoResize):
        
        val = bool(IniManager().get(key= INI_KEY, var_name="enable_all", default=False, section="Configuration"))
        new_val = PyImGui.checkbox("Enable All Widgets", val)
        if new_val != val:
            IniManager().set(key=INI_KEY, var_name="enable_all", value=new_val, section="Configuration")
            IniManager().save_vars(INI_KEY)

    ImGui.End(INI_KEY)

def configure():
    pass
    
#region Main
# ------------------------------------------------------------
# Config
# ------------------------------------------------------------
widget_manager = get_widget_handler()

MODULE_NAME = "Widget Template"

INI_KEY = ""
INI_PATH = "Widgets/WidgetManager"
INI_FILENAME = "WidgetManager.ini"

def _add_config_vars():
    global INI_KEY
    IniManager().add_bool(key=INI_KEY, var_name="enable_all", section="Configuration", name="enable_all", default=False)
    
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
    if widget_manager.enable_all:
        widget_manager.execute_enabled_widgets_update()
    
def draw():
    if widget_manager.enable_all:
        widget_manager.execute_enabled_widgets_draw()     

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
        
        widget_manager.MANAGER_INI_KEY = INI_KEY
        
        widget_manager.discover()
        _add_config_vars()
        IniManager().load_once(INI_KEY)

        # FIX 1: Explicitly load the global manager state into the handler
        widget_manager.enable_all = bool(IniManager().get(key=INI_KEY, var_name="enable_all", default=False, section="Configuration"))
        widget_manager._apply_ini_configuration()
            
                
    if INI_KEY:
        if ImGui.Begin(ini_key=INI_KEY, name="Widget Manager", flags=PyImGui.WindowFlags.AlwaysAutoResize):
            widget_manager.draw_ui(INI_KEY)
        ImGui.End(INI_KEY)
    
    if widget_manager.enable_all:
        widget_manager.execute_enabled_widgets_main()
        widget_manager.execute_configuring_widgets()


if __name__ == "__main__":
    main()