import PyImGui
from Py4GWCoreLib import Routines, ImGui
from Py4GWCoreLib.IniManager import IniManager

# ------------------------------------------------------------
# Config
# ------------------------------------------------------------

MODULE_NAME = "Widget Template"

INI_KEY = ""
INI_PATH = "Widgets/WidgetTemplate"
INI_FILENAME = "WidgetTemplate.ini"

def _add_config_vars():
    global INI_KEY
    IniManager().add_bool(INI_KEY, "test_bool_var", "TestBoolVar", "value", default=False)


def draw_widget():
    global INI_KEY
    if ImGui.Begin(INI_KEY,MODULE_NAME, flags=PyImGui.WindowFlags.AlwaysAutoResize):
        
        PyImGui.text("Add your stuff here")
        
        val = bool(IniManager().get(INI_KEY, "test_bool_var", False))
        new_val = PyImGui.checkbox("Test Bool Variable", val)
        if new_val != val:
            IniManager().set(INI_KEY, "test_bool_var", new_val)

    ImGui.End(INI_KEY)

def configure():
    pass

def main():
    global INI_KEY
    if not Routines.Checks.Map.MapValid():
        return
    
    if not INI_KEY:
        INI_KEY = IniManager().ensure_key("Widgets/WidgetTemplate", "WidgetTemplate.ini")
        if not INI_KEY:
            return
        _add_config_vars()
        IniManager().load_once(INI_KEY)
        
    draw_widget()


if __name__ == "__main__":
    main()