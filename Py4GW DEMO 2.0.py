import PyImGui
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.py4gwcorelib_src.Timer import FormatTime
from Py4GWCoreLib.UIManager import FrameInfo, UIManager
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib.py4gwcorelib_src.Color import ColorPalette, Color
from dataclasses import dataclass


MODULE_NAME = "Py4GW DEMO 2.0"

VIEW_LIST = [
    "Map",
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
            "- Geo Location and Pathing.\n"
            "- Observing Matches Data.\n"
        ),
    },
}

_selected_view: str = "Map"

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
        player_outline = DisplayNode(True, ColorPalette.GetColor("crimson"), 3.0)

        
        
map_vars = MapVars()
        
def draw_map_data():
    global _selected_view, SECTION_INFO, map_vars
    if PyImGui.begin_tab_bar("MapDataTabBar"):
        if PyImGui.begin_tab_item("Map##MapInfoTab"):
            if _selected_view in SECTION_INFO:
                info = SECTION_INFO[_selected_view]
                #PyImGui.text(info["title"])
                #PyImGui.separator()
                PyImGui.text_wrapped(info["description"])
                
            PyImGui.separator()
        
            PyImGui.text("Common fields:")

            rows: list[tuple[str, str | int | float]] = [
                ("Instance Type", Map.GetInstanceTypeName()),
                ("Current Map", f"[{Map.GetMapID()}] - {Map.GetMapName()}"),
                ("Instance uptime (ms)", f"{FormatTime(Map.GetInstanceUptime(), 'hh:mm:ss:ms')}"),
                ("Region", f"[{Map.GetRegion()[0]}] - {Map.GetRegion()[1]}"),
                ("Region Type", f"[{Map.GetRegionType()[0]}] - {Map.GetRegionType()[1]}"),
                ("District", f"[{Map.GetDistrict()}]"),
                ("Language", f"[{Map.GetLanguage()[0]}] - {Map.GetLanguage()[1]}"),
                ("Amount of Players in Instance", f"{Map.GetAmountOfPlayersInInstance()}"),
            ]

            draw_kv_table("WorldMapTable", rows)
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Data##MapInfoDataTab"):
            if PyImGui.collapsing_header("Common fields:"):
                rows: list[tuple[str, str | int | float]] = [
                    ("Instance Type", Map.GetInstanceTypeName()),
                    ("Current Map", f"[{Map.GetMapID()}] - {Map.GetMapName()}"),
                    ("Instance uptime (ms)", f"{FormatTime(Map.GetInstanceUptime(), 'hh:mm:ss:ms')}"),
                    ("Campaign", f"[{Map.GetCampaign()[0]}] - {Map.GetCampaign()[1]}"),
                    ("Continent", f"[{Map.GetContinent()[0]}] - {Map.GetContinent()[1]}"),
                    ("Is Guild Hall", f"{Map.IsGuildHall()}"),
                    ("Region", f"[{Map.GetRegion()[0]}] - {Map.GetRegion()[1]}"),
                    ("Region Type", f"[{Map.GetRegionType()[0]}] - {Map.GetRegionType()[1]}"),
                    ("District", f"[{Map.GetDistrict()}]"),
                    ("Language", f"[{Map.GetLanguage()[0]}] - {Map.GetLanguage()[1]}"),
                    ("Amount of Players in Instance", f"{Map.GetAmountOfPlayersInInstance()}"),
                    ("Max Party Size", f"{Map.GetMaxPartySize()}"),
                    ("Foes Killed", f"{Map.GetFoesKilled()}"),
                    ("Foes to Kill", f"{Map.GetFoesToKill()}"),
                    ("Is Vanquishable", f"{Map.IsVanquishable()}"),
                    ("Is Vanquish Complete", f"{Map.IsVanquishComplete()}"),
                    ("Is in Cinematic", f"{Map.IsInCinematic()}"),
                    ("Has Enter Challenge Button", f"{Map.HasEnterChallengeButton()}"),  
                    ("Is Map Unlocked", f"{Map.IsMapUnlocked()}"),
                ]

                draw_kv_table("MissionMapTable", rows)
                
            if PyImGui.collapsing_header("Additional Fields:"):
                rows: list[tuple[str, str | int | float]] = [
                    ("Is Unlockable", f"{Map.IsUnlockable()}"),
                    ("Has Mission Maps To", f"{Map.HasMissionMapsTo()}"),
                    ("Mission Maps To", f"{Map.GetMissionMapsTo()} - {Map.GetMapName(Map.GetMissionMapsTo())}"),
                    ("Controlled Outpost ID", f"{Map.GetControlledOutpostID()} - {Map.GetMapName(Map.GetControlledOutpostID())}"),
                    ("Is on World Map", f"{Map.IsOnWorldMap()}"),
                    ("Is PvP Map", f"{Map.IsPVP()}"),
                    ("Min Party Size", f"{Map.GetMinPartySize()}"),
                    ("Min Player Size", f"{Map.GetMinPlayerSize()}"),
                    ("Max Player Size", f"{Map.GetMaxPlayerSize()}"),
                    ("flags", f"{Map.GetFlags()}"),
                    ("Min Level", f"{Map.GetMinLevel()}"),
                    ("Max Level", f"{Map.GetMaxLevel()}"),
                    ("Thumbnail ID", f"{Map.GetThumbnailID()}"),
                    ("Fraction Mission", f"{Map.GetFractionMission()}"),
                    ("Needed PQ", f"{Map.GetNeededPQ()}"),
                    ("Icon Position (x, y)", f"{Map.GetIconPosition()}"),
                    ("Icon Start Position (x, y)", f"{Map.GetIconStartPosition()}"),
                    ("Icon End Position (x, y)", f"{Map.GetIconEndPosition()}"),
                    ("File ID", f"{Map.GetFileID()}"),
                    ("Mission Chronology", f"{Map.GetMissionChronology()}"),
                    ("HA Chronology", f"{Map.GetHAChronology()}"),
                    ("Name ID", f"{Map.GetNameID()}"),
                    ("Description ID", f"{Map.GetDescriptionID()}"),
                    ("File ID 1", f"{Map.GetFileID1()}"),
                    ("File ID 2", f"{Map.GetFileID2()}"),
                    
                ]

                draw_kv_table("MissionMapTable", rows)
                
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Actions##MapInfoActionsTab"):
            PyImGui.text("SkipCinematic:")
            PyImGui.indent(20.0)
            if not Map.IsInCinematic():
                PyImGui.text("No cinematic is currently playing.")
            else:
                if PyImGui.button("Skip Cinematic"):
                    Map.SkipCinematic()
                    
            PyImGui.unindent(20.0)
            PyImGui.separator()
            if PyImGui.collapsing_header("Travel to Map:"):
                PyImGui.indent(20.0)
                map_vars.Travel.map_id = PyImGui.input_int("Map ID", map_vars.Travel.map_id)
                map_vars.Travel.region = PyImGui.input_int("Region", map_vars.Travel.region)
                map_vars.Travel.district_number = PyImGui.input_int("District Number", map_vars.Travel.district_number)
                map_vars.Travel.language = PyImGui.input_int("Language", map_vars.Travel.language)
                    
                if PyImGui.button("Travel"):
                    Map.TravelToRegion(
                        map_vars.Travel.map_id,
                        map_vars.Travel.region,
                        map_vars.Travel.district_number,
                        map_vars.Travel.language
                    )
                PyImGui.unindent(20.0)
                
            if PyImGui.collapsing_header("Guild Hall:"):
                PyImGui.indent(20.0)
                is_guild_hall = Map.IsGuildHall()
                if is_guild_hall:
                    if PyImGui.button("Leave Guild Hall"):    
                        Map.LeaveGH()
                else:
                    if PyImGui.button("Travel to Guild Hall"):
                        Map.TravelGH()
                PyImGui.unindent(20.0)
                
            if PyImGui.collapsing_header("Enter Challenge:"):
                PyImGui.indent(20.0)
                if not Map.HasEnterChallengeButton():
                    PyImGui.text("No 'Enter Challenge' button is available in this map.")
                else:
                    if not Map.IsEnteringChallenge():
                        if PyImGui.button("Enter Challenge"):
                            Map.EnterChallenge()
                    else:
                        if PyImGui.button("Cancel Enter Challenge"):
                            Map.CancelEnterChallenge()

                PyImGui.unindent(20.0)
            
                
                
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Mission Map##MapInfoMissionMapTab"):
            if not Map.MissionMap.IsWindowOpen():
                PyImGui.text("Mission Map window is not open.")
            else:
                map_vars.MissionMap.frame_info = Map.MissionMap.GetFrameInfo()
                _FI = map_vars.MissionMap.frame_info
                
                nx, ny = Map.MissionMap.GetLastClickCoords()
                sx, sy = Map.MissionMap.MapProjection.NormalizedScreenToScreen(nx, ny)
                wx, wy = Map.MissionMap.MapProjection.NormalizedScreenToWorldMap(nx, ny)
                gx, gy = Map.MissionMap.MapProjection.NormalizedScreenToGameMap(nx, ny)

                
                    
                rows: list[tuple[str, str | int | float]] = [
                    ("frame_id ", f"{Map.MissionMap.GetFrameID()}"),
                    ("Is Window Open", f"{Map.MissionMap.IsWindowOpen()}"),
                    ("Coords (l, t, r, b)", f"{Map.MissionMap.GetMissionMapWindowCoords()}"),
                    ("Contents Coords (l, t, r, b)", f"{Map.MissionMap.GetMissionMapContentsCoords()}"),
                    ("Scale", f"{Map.MissionMap.GetScale()}"),
                    ("Zoom", f"{Map.MissionMap.GetZoom()}"),
                    ("Adjusted Zoom (+0.5)", f"{Map.MissionMap.GetAdjustedZoom(Map.MissionMap.GetZoom(), 0.5)}"),
                    ("Center", f"{Map.MissionMap.GetCenter()}"),

                    ("Last Click (normalized):", f"({nx:.3f}, {ny:.3f})"),
                    ("Last Click (screen):", f"({sx:.1f}, {sy:.1f})"),
                    ("Last Click (world):", f"({wx:.1f}, {wy:.1f})"),
                    ("Last Click (game):", f"({gx:.1f}, {gy:.1f})"),

                    ("Pan Offset (x, y)", f"{Map.MissionMap.GetPanOffset()}"),
                    ("Map Screen Center (x, y)", f"{Map.MissionMap.GetMapScreenCenter()}"),
                    ("Player World Position (x, y)", f"{Player.GetXY()}"),
                    ("Player Map Position (x, y)", f"{Map.MissionMap.MapProjection.GameMapToScreen(*Player.GetXY())}"),

                ]

                draw_kv_table("MissionMapTable", rows)
                PyImGui.separator()
                PyImGui.text("Display Options:")
                if PyImGui.collapsing_header("Outline"):
                    PyImGui.indent(20.0)
                    map_vars.MissionMap.draw_outline.visible = PyImGui.checkbox("Draw Frame Outline", map_vars.MissionMap.draw_outline.visible)
                    PyImGui.same_line(0,-1)
                    PyImGui.set_next_item_width(100.0)
                    map_vars.MissionMap.draw_outline.thickness = PyImGui.slider_int("Outline Thickness", int(map_vars.MissionMap.draw_outline.thickness), 1, 10)
                    _color = PyImGui.color_edit4("Outline Color", map_vars.MissionMap.draw_outline.color.to_tuple_normalized())

                    map_vars.MissionMap.draw_outline.color = Color().from_tuple_normalized(_color)
                    if map_vars.MissionMap.draw_outline.visible:
                        if _FI:
                            _FI.DrawFrameOutline(map_vars.MissionMap.draw_outline.color.to_color(), map_vars.MissionMap.draw_outline.thickness)
                    PyImGui.unindent(20.0)
                    
                if PyImGui.collapsing_header("Content Outline"):
                    PyImGui.indent(20.0)
                    map_vars.MissionMap.draw_content_outline.visible = PyImGui.checkbox("Draw Content Outline", map_vars.MissionMap.draw_content_outline.visible)
                    PyImGui.same_line(0,-1)
                    PyImGui.set_next_item_width(100.0)
                    map_vars.MissionMap.draw_content_outline.thickness = PyImGui.slider_int("Content Outline Thickness", int(map_vars.MissionMap.draw_content_outline.thickness), 1, 10)
                    _color = PyImGui.color_edit4("Content Outline Color", map_vars.MissionMap.draw_content_outline.color.to_tuple_normalized())

                    map_vars.MissionMap.draw_content_outline.color = Color().from_tuple_normalized(_color)
                    if map_vars.MissionMap.draw_content_outline.visible:
                        content_coords = Map.MissionMap.GetMissionMapContentsCoords()
                        Overlay().BeginDraw()
                        left, top, right, bottom = content_coords
                        Overlay().DrawQuad(x1=left, y1=top,
                                          x2=right, y2=top,
                                          x3=right, y3=bottom,
                                          x4=left, y4=bottom,
                                          color=map_vars.MissionMap.draw_content_outline.color.to_color(),
                                          thickness=map_vars.MissionMap.draw_content_outline.thickness)
                        Overlay().EndDraw()
                    PyImGui.unindent(20.0)
                    
                if PyImGui.collapsing_header("Last Click Position"):
                    PyImGui.indent(20.0)
                    map_vars.MissionMap.draw_last_click_pos.visible = PyImGui.checkbox("Draw Last Click Position", map_vars.MissionMap.draw_last_click_pos.visible)
                    PyImGui.same_line(0,-1)
                    PyImGui.set_next_item_width(100.0)
                    map_vars.MissionMap.draw_last_click_pos.thickness = PyImGui.slider_int("Last Click Pos Thickness", int(map_vars.MissionMap.draw_last_click_pos.thickness), 1, 10)
                    _color = PyImGui.color_edit4("Last Click Pos Color", map_vars.MissionMap.draw_last_click_pos.color.to_tuple_normalized())
                    map_vars.MissionMap.draw_last_click_pos.color = Color().from_tuple_normalized(_color)
                    dc_color = map_vars.MissionMap.draw_last_click_pos.color.to_color()
                    PyImGui.text_colored("this feature will draw also in world space", ColorPalette.GetColor("gold").to_tuple_normalized())
                    if map_vars.MissionMap.draw_last_click_pos.visible:
                        sx, sy = Map.MissionMap.MapProjection.NormalizedScreenToScreen(nx, ny)
                        Overlay().BeginDraw()
                        Overlay().DrawPoly(sx, sy, 10.0, dc_color, 32, map_vars.MissionMap.draw_last_click_pos.thickness)
                        Overlay().EndDraw()
                        def DrawFlagAll(pos_x, pos_y):
                            overlay = Overlay()
                            pos_z = overlay.FindZ(pos_x, pos_y)

                            overlay.BeginDraw()
                            overlay.DrawLine3D(pos_x, pos_y, pos_z, pos_x, pos_y, pos_z - 150, dc_color, 3)    
                            overlay.DrawTriangleFilled3D(
                                pos_x, pos_y, pos_z - 150,               # Base point
                                pos_x, pos_y, pos_z - 120,               # 30 units up
                                pos_x - 50, pos_y, pos_z - 135,          # 50 units left, 15 units up
                                dc_color
                            )

                            overlay.EndDraw()
                        DrawFlagAll(gx, gy)
                    PyImGui.unindent(20.0)
                    
                    
                    
                if PyImGui.collapsing_header("Center Map Position"):
                    PyImGui.indent(20.0)
                    map_vars.MissionMap.center_outline.visible = PyImGui.checkbox("Draw Center Map Position", map_vars.MissionMap.center_outline.visible)
                    PyImGui.same_line(0,-1)
                    PyImGui.set_next_item_width(100.0)
                    map_vars.MissionMap.center_outline.thickness = PyImGui.slider_int("Center Pos Thickness", int(map_vars.MissionMap.center_outline.thickness), 1, 10)
                    _color = PyImGui.color_edit4("Center Pos Color", map_vars.MissionMap.center_outline.color.to_tuple_normalized())
                    map_vars.MissionMap.center_outline.color = Color().from_tuple_normalized(_color)
                    dc_color = map_vars.MissionMap.center_outline.color.to_color()
                    if map_vars.MissionMap.center_outline.visible:
                        center_world = Map.MissionMap.GetCenter()
                        center_screen = Map.MissionMap.MapProjection.WorldMapToScreen(center_world[0], center_world[1])
                        Overlay().BeginDraw()
                        Overlay().DrawPoly(center_screen[0], center_screen[1], 10.0, dc_color, 32, map_vars.MissionMap.center_outline.thickness)
                        Overlay().EndDraw()
                    PyImGui.unindent(20.0)
                if PyImGui.collapsing_header("Player Position"):
                    PyImGui.indent(20.0)
                    map_vars.MissionMap.player_outline.visible = PyImGui.checkbox("Draw Player Position", map_vars.MissionMap.player_outline.visible)
                    PyImGui.same_line(0,-1)
                    PyImGui.set_next_item_width(100.0)
                    map_vars.MissionMap.player_outline.thickness = PyImGui.slider_int("Player Pos Thickness", int(map_vars.MissionMap.player_outline.thickness), 1, 10)
                    _color = PyImGui.color_edit4("Player Pos Color", map_vars.MissionMap.player_outline.color.to_tuple_normalized())
                    map_vars.MissionMap.player_outline.color = Color().from_tuple_normalized(_color)
                    dc_color = map_vars.MissionMap.player_outline.color.to_color()
                    if map_vars.MissionMap.player_outline.visible:
                        player_pos = Player.GetXY()
                        player_screen = Map.MissionMap.MapProjection.GameMapToScreen(player_pos[0], player_pos[1])
                        Overlay().BeginDraw()
                        Overlay().DrawPoly(player_screen[0], player_screen[1], 10.0, dc_color, 32, map_vars.MissionMap.player_outline.thickness)
                        Overlay().EndDraw()
                    PyImGui.unindent(20.0)
                    

                    
            PyImGui.end_tab_item()
        PyImGui.end_tab_bar()
    

def draw_window():
    global _selected_view
    if PyImGui.begin(MODULE_NAME, True, PyImGui.WindowFlags.AlwaysAutoResize):
        # ================= LEFT PANEL =================
        PyImGui.begin_child(
            "left_panel",
            (180.0, 700.0),   # fixed width, full height
            True,
            0
        )

        PyImGui.text("Modules")
        PyImGui.separator()

        for name in VIEW_LIST:
            if PyImGui.selectable(
                name,
                _selected_view == name,
                PyImGui.SelectableFlags.NoFlag,
                (0.0, 0.0)
            ):
                _selected_view = name

        PyImGui.end_child()

        PyImGui.same_line(0,-1)
        
        # ================= RIGHT PANEL =================
        PyImGui.begin_child(
            "right_panel",
            (500.0, 700.0),     # take remaining space
            False,
            0
        )
        
        if _selected_view == "Map":
            draw_map_data()

        PyImGui.end_child()

    PyImGui.end()



def main():
    draw_window()

if __name__ == "__main__":
    main()
