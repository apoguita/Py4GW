
from Py4GWCoreLib.py4gwcorelib_src.IniHandler import IniHandler
from .ImGui_src.types import ImGuiStyleVar, StyleTheme, StyleColorType
from .ImGui_src import Style
from .ImGui_src.ImGuisrc import ImGui
from .ImGui_src.Textures import TextureState, SplitTexture, MapTexture, ThemeTexture, ThemeTextures

__all__ = ["ImGuiStyleVar", 
           "StyleTheme", 
           "StyleColorType",
           "Style",
           "ImGui",
           "TextureState",
           "SplitTexture",
           "MapTexture",
           "ThemeTexture",
           "ThemeTextures"
        ]

py4_gw_ini_handler = IniHandler("Py4GW.ini")
ImGui.set_theme(Style.StyleTheme[py4_gw_ini_handler.read_key("settings", "style_theme", StyleTheme.ImGui.name)])