
import PyImGui
from dataclasses import dataclass
from Py4GWCoreLib.py4gwcorelib_src.Color import ColorPalette, Color
from Py4GWCoreLib.UIManager import FrameInfo, UIManager

VIEW_LIST: list[tuple[bool, str]] = [
    #is_child, "View Name"
    (False, "Map"),
    (True,  "Mission Map"),
    (True,  "Mini Map"),
    (True,  "World Map"),
    (True,  "Pregame Data"),
    (True,  "Observing Matches Data"),
    (True,  "Geo Location and Pathing"),
    (False, "AgentArray"),
    (False, "Agents"),
]


SECTION_INFO = {
    "Map": {
        "title": "Map Library",
        "description": (
            "The Map Library provides a comprehensive set of methods to gather "
            "map-related data and interact with the game world.\n"
            "It allows you to retrieve information about locations, distances, and "
            "other geographical data within the game environment.\n"
            "It also offers pathing and geo-location functionalities to enhance "
            "navigation and spatial awareness."
            "Privides data for various map-related features, including:\n\n"
            "- Maps.\n"
            "- Mission Map.\n"
            "- Mini Map.\n"
            "- World Map.\n"
            "- Pregame Data.\n"
            "- Observing Matches Data.(WIP)\n"
            "- Geo Location and Pathing.\n"    
        ),
    },
}

_selected_view: str = "Map"

#region config_vars
@dataclass
class DisplayNode:
    visible: bool = True
    color: Color= ColorPalette.GetColor("white")
    thickness: float = 1.0
               
class MapVars:
    class Travel:
        map_id: int = 0
        region: int = 0
        district_number: int = 0
        language: int = 0
        
    class MissionMap:
        frame_info: FrameInfo | None = None
        draw_outline = DisplayNode(True, ColorPalette.GetColor("bright_green"), 3.0)
        draw_content_outline = DisplayNode(True, ColorPalette.GetColor("crimson"), 2.0)
        center_outline = DisplayNode(True, ColorPalette.GetColor("fuchsia"), 4.0)
        draw_last_click_pos = DisplayNode(True, ColorPalette.GetColor("gold"), 3.0)
        draw_last_right_click_pos = DisplayNode(True, ColorPalette.GetColor("crimson"), 3.0)
        player_outline = DisplayNode(True, ColorPalette.GetColor("crimson"), 3.0)
        
    class MiniMap:
        frame_info: FrameInfo | None = None
        draw_outline = DisplayNode(True, ColorPalette.GetColor("bright_green"), 3.0)
        draw_content_outline = DisplayNode(True, ColorPalette.GetColor("crimson"), 2.0)
        center_outline = DisplayNode(True, ColorPalette.GetColor("fuchsia"), 4.0)
        draw_last_click_pos = DisplayNode(True, ColorPalette.GetColor("gold"), 3.0)
        draw_last_right_click_pos = DisplayNode(True, ColorPalette.GetColor("crimson"), 3.0)
        player_outline = DisplayNode(True, ColorPalette.GetColor("crimson"), 3.0)

        
        
map_vars = MapVars()
        

def draw_kv_table(table_id: str, rows: list[tuple[str, str | int | float]]):
    flags = (
        PyImGui.TableFlags.BordersInnerV
        | PyImGui.TableFlags.RowBg
        | PyImGui.TableFlags.SizingStretchProp
    )

    if PyImGui.begin_table(table_id, 2, flags):
        PyImGui.table_setup_column("Field", PyImGui.TableColumnFlags.WidthFixed, 180)
        PyImGui.table_setup_column("Value", PyImGui.TableColumnFlags.WidthStretch)
        PyImGui.table_headers_row()

        for field, value in rows:
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            PyImGui.text_unformatted(str(field))
            PyImGui.table_next_column()
            PyImGui.text_unformatted(str(value))

        PyImGui.end_table()
 