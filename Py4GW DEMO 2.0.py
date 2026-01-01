import PyImGui
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.AgentArray import AgentArray
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.py4gwcorelib_src.Timer import FormatTime
from Py4GWCoreLib.UIManager import FrameInfo, UIManager
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib.py4gwcorelib_src.Color import ColorPalette, Color
from dataclasses import dataclass


MODULE_NAME = "Py4GW DEMO 2.0"

VIEW_LIST = [
    "Map",
    "Agents",
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
            "- Observing Matches Data.\n"
            "- Geo Location and Pathing.\n"    
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
        
#region main_map_tab
def draw_main_map_tab():
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
    
#region map_data_tab
def draw_map_data_tab():
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
     
#region map_actions_tab   
def draw_map_actions_tab():
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
    
#region mission_map_tab
def draw_mission_map_tab():
    if not Map.MissionMap.IsWindowOpen():
        PyImGui.text("Mission Map window is not open.")
        if PyImGui.button("Open Mission Map"):
            Map.MissionMap.OpenWindow()
    else:
        if PyImGui.button("Close Mission Map"):
            Map.MissionMap.CloseWindow()
        map_vars.MissionMap.frame_info = Map.MissionMap.GetFrameInfo()
        _FI = map_vars.MissionMap.frame_info
        
        frame_id = Map.MissionMap.GetFrameID()
        is_mouse_over = Map.MissionMap.IsMouseOver()
        mm_coords = Map.MissionMap.GetMissionMapWindowCoords()
        mm_contents_coords = Map.MissionMap.GetMissionMapContentsCoords()
        scale = Map.MissionMap.GetScale()
        zoom = Map.MissionMap.GetZoom()
        adusted_zoom = Map.MissionMap.GetAdjustedZoom(zoom, 0.5)
        center = Map.MissionMap.GetCenter()
        map_center_screen = Map.MissionMap.GetMapScreenCenter()
        
        nx, ny = Map.MissionMap.GetLastClickCoords()
        sx, sy = Map.MissionMap.MapProjection.NormalizedScreenToScreen(nx, ny)
        wx, wy = Map.MissionMap.MapProjection.NormalizedScreenToWorldMap(nx, ny)
        gx, gy = Map.MissionMap.MapProjection.NormalizedScreenToGamePos(nx, ny)
        
        r_nx, r_ny = Map.MissionMap.GetLastRightClickCoords()
        r_sx, r_sy = Map.MissionMap.MapProjection.NormalizedScreenToScreen(r_nx, r_ny)  
        r_wx, r_wy = Map.MissionMap.MapProjection.NormalizedScreenToWorldMap(r_nx, r_ny)
        r_gx, r_gy = Map.MissionMap.MapProjection.NormalizedScreenToGamePos(r_nx, r_ny)
        
        pan_offset = Map.MissionMap.GetPanOffset()
        player_world_pos = Player.GetXY()
        player_map_pos = Map.MissionMap.MapProjection.GameMapToScreen(*player_world_pos)
        
        if PyImGui.collapsing_header("Mission Map Data:"):
            
        
            rows: list[tuple[str, str | int | float]] = [
                ("frame_id ", f"{frame_id}"),
                ("Is Mouse Over", f"{is_mouse_over}"),
                ("Coords (l, t, r, b)", f"{mm_coords}"),
                ("Contents Coords (l, t, r, b)", f"{mm_contents_coords}"),
                ("Scale", f"{scale[0]:.3f}, {scale[1]:.3f}"),
                ("Zoom", f"{zoom}"),
                ("Adjusted Zoom (+0.5)", f"{adusted_zoom:.3f}"),
                ("Center", f"{center[0]:.1f}, {center[1]:.1f}"),
                ("Map Screen Center (x, y)", f"{map_center_screen}"),

                ("Last Click (normalized):", f"({nx:.3f}, {ny:.3f})"),
                #("Last Click (screen):", f"({sx:.1f}, {sy:.1f})"),
                #("Last Click (game):", f"({gx:.1f}, {gy:.1f})"),
                
                ("Last Right Click (normalized):", f"({r_nx:.3f}, {r_ny:.3f})"),
                #("Last Right Click (screen):", f"({r_sx:.1f}, {r_sy:.1f})"),
                #("Last Right Click (game):", f"({r_gx:.1f}, {r_gy:.1f})"),

                ("Pan Offset (x, y)", f"{pan_offset[0]:.1f}, {pan_offset[1]:.1f}"),
                ("Player World Position (x, y)", f"{player_world_pos[0]:.1f}, {player_world_pos[1]:.1f}"),
                ("Player Map Position (x, y)", f"{player_map_pos[0]:.1f}, {player_map_pos[1]:.1f}"),

            ]

            draw_kv_table("MissionMapTable", rows)
            PyImGui.separator()
            
        if PyImGui.collapsing_header("Mission Map Display Options:"):
            PyImGui.text("Display Options:")
            #================ Outline Options ================
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
                
            #================ Content Outline Options ================
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
                
            #================ Last Click Position Options ================
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
                
            #================ Last Right Click Position Options ================
            if PyImGui.collapsing_header("Last Right Click Position"):
                PyImGui.indent(20.0)
                PyImGui.indent(20.0)
                map_vars.MissionMap.draw_last_right_click_pos.visible = PyImGui.checkbox("Draw Last Right Click Position", map_vars.MissionMap.draw_last_right_click_pos.visible)
                PyImGui.same_line(0,-1)
                PyImGui.set_next_item_width(100.0)
                map_vars.MissionMap.draw_last_right_click_pos.thickness = PyImGui.slider_int("Last Right Click Pos Thickness", int(map_vars.MissionMap.draw_last_right_click_pos.thickness), 1, 10)
                _color = PyImGui.color_edit4("Last Right Click Pos Color", map_vars.MissionMap.draw_last_right_click_pos.color.to_tuple_normalized())
                map_vars.MissionMap.draw_last_right_click_pos.color = Color().from_tuple_normalized(_color)
                dc_color = map_vars.MissionMap.draw_last_right_click_pos.color.to_color()
                PyImGui.text_colored("this feature will draw also in world space", ColorPalette.GetColor("gold").to_tuple_normalized())
                if map_vars.MissionMap.draw_last_right_click_pos.visible:
                    r_sx, r_sy = Map.MissionMap.MapProjection.NormalizedScreenToScreen(r_nx, r_ny)
                    Overlay().BeginDraw()
                    Overlay().DrawPoly(r_sx, r_sy, 10.0, dc_color, 32, map_vars.MissionMap.draw_last_right_click_pos.thickness)
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
                    DrawFlagAll(r_gx, r_gy)
                PyImGui.unindent(20.0)
                
                 
            #================ Center Map Position Options ================   
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
                
            #================ Player Position Options ================
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
            
            
#region mini_map_tab
def draw_mini_map_tab():
    if not Map.MiniMap.IsWindowOpen():
        PyImGui.text("Mini Map window is not open.")
        if PyImGui.button("Open Mini Map"):
            Map.MiniMap.OpenWindow()
    else:
        if PyImGui.button("Close Mini Map"):
            Map.MiniMap.CloseWindow()
        map_vars.MiniMap.frame_info = Map.MiniMap.GetFrameInfo()
        _FI = map_vars.MiniMap.frame_info
        
        frame_id = Map.MiniMap.GetFrameID()
        is_mouse_over = Map.MiniMap.IsMouseOver()
        mm_coords = Map.MiniMap.GetWindowCoords()
        scale = Map.MiniMap.GetScale()
        zoom = Map.MiniMap.GetZoom()
        map_center_screen = Map.MiniMap.GetMapScreenCenter()
        
        normalized_mouse_x, normalized_mouse_y = Map.MiniMap.GetLastClickCoords()
        screen_mouse_x, screen_mouse_y = Map.MiniMap.MapProjection.NormalizedScreenToScreen(normalized_mouse_x, normalized_mouse_y)
        gamepos_mouse_x, gamepos_mouse_y = Map.MiniMap.MapProjection.ScreenToGamePos(screen_mouse_x, screen_mouse_y)
        
        normalized_right_mouse_x, normalized_right_mouse_y = Map.MiniMap.GetLastRightClickCoords()
        screen_right_mouse_x, screen_right_mouse_y = Map.MiniMap.MapProjection.NormalizedScreenToScreen(normalized_right_mouse_x, normalized_right_mouse_y)  
        gamepos_right_mouse_x, gamepos_right_mouse_y = Map.MiniMap.MapProjection.ScreenToGamePos(screen_right_mouse_x, screen_right_mouse_y)
        
        pan_offset = Map.MiniMap.GetPanOffset()
        player_game_pos = Player.GetXY()
        player_map_pos = Map.MiniMap.MapProjection.GamePosToScreen(player_game_pos[0], player_game_pos[1])
        
        
        if PyImGui.collapsing_header("MiniMap Data:"):
            
        
            rows: list[tuple[str, str | int | float]] = [
                ("frame_id ", f"{frame_id}"),
                ("Is Mouse Over", f"{is_mouse_over}"),
                ("Coords (l, t, r, b)", f"{mm_coords}"),
                ("Scale", f"{scale:.3f}"),
                ("Zoom", f"{zoom}"),
                ("Map Screen Center (x, y)", f"{map_center_screen}"),

                ("Last Click (normalized):", f"({normalized_mouse_x:.3f}, {normalized_mouse_y:.3f})"),   
                ("Last Click (screen):", f"({screen_mouse_x:.1f}, {screen_mouse_y:.1f})"),
                ("Last Click (game):", f"({gamepos_mouse_x:.1f}, {gamepos_mouse_y:.1f})"),
                ("Last Right Click (normalized):", f"({normalized_right_mouse_x:.3f}, {normalized_right_mouse_y:.3f})"),
                ("Last Right Click (screen):", f"({screen_right_mouse_x:.1f}, {screen_right_mouse_y:.1f})"),
                ("Last Right Click (game):", f"({gamepos_right_mouse_x:.1f}, {gamepos_right_mouse_y:.1f})"),

                ("Pan Offset (x, y)", f"{pan_offset[0]:.1f}, {pan_offset[1]:.1f}"),
                ("Player World Position (x, y)", f"{player_game_pos[0]:.1f}, {player_game_pos[1]:.1f}"),
                ("Player Map Position (x, y)", f"{player_map_pos[0]:.1f}, {player_map_pos[1]:.1f}"),

            ]

            draw_kv_table("MiniMapTable", rows)
            PyImGui.separator()
            
        if PyImGui.collapsing_header("MiniMap Display Options:"):
            PyImGui.text("Display Options:")
            #================ Outline Options ================
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
                
            #================ Last Click Position Options ================
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
                    Overlay().BeginDraw()
                    Overlay().DrawPoly(screen_mouse_x, screen_mouse_y, 10.0, dc_color, 32, map_vars.MissionMap.draw_last_click_pos.thickness)
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
                    DrawFlagAll(gamepos_mouse_x, gamepos_mouse_y)
                PyImGui.unindent(20.0)
                
            #================ Last Right Click Position Options ================
            if PyImGui.collapsing_header("Last Right Click Position"):
                PyImGui.indent(20.0)
                PyImGui.indent(20.0)
                map_vars.MissionMap.draw_last_right_click_pos.visible = PyImGui.checkbox("Draw Last Right Click Position", map_vars.MissionMap.draw_last_right_click_pos.visible)
                PyImGui.same_line(0,-1)
                PyImGui.set_next_item_width(100.0)
                map_vars.MissionMap.draw_last_right_click_pos.thickness = PyImGui.slider_int("Last Right Click Pos Thickness", int(map_vars.MissionMap.draw_last_right_click_pos.thickness), 1, 10)
                _color = PyImGui.color_edit4("Last Right Click Pos Color", map_vars.MissionMap.draw_last_right_click_pos.color.to_tuple_normalized())
                map_vars.MissionMap.draw_last_right_click_pos.color = Color().from_tuple_normalized(_color)
                dc_color = map_vars.MissionMap.draw_last_right_click_pos.color.to_color()
                PyImGui.text_colored("this feature will draw also in world space", ColorPalette.GetColor("gold").to_tuple_normalized())
                if map_vars.MissionMap.draw_last_right_click_pos.visible:
                    Overlay().BeginDraw()
                    Overlay().DrawPoly(screen_right_mouse_x, screen_right_mouse_y, 10.0, dc_color, 32, map_vars.MissionMap.draw_last_right_click_pos.thickness)
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
                    DrawFlagAll(gamepos_right_mouse_x, gamepos_right_mouse_y)
                PyImGui.unindent(20.0)
                
                 
            #================ Center Map Position Options ================   
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
                    center_screen = Map.MiniMap.GetMapScreenCenter()
                    Overlay().BeginDraw()
                    Overlay().DrawPoly(center_screen[0], center_screen[1], 10.0, dc_color, 32, map_vars.MissionMap.center_outline.thickness)
                    Overlay().EndDraw()
                PyImGui.unindent(20.0)
                
            #================ Player Position Options ================
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
                    
                    player_screen = Map.MiniMap.MapProjection.GamePosToScreen(player_pos[0], player_pos[1])
                    Overlay().BeginDraw()
                    Overlay().DrawPoly(player_screen[0], player_screen[1], 10.0, dc_color, 32, map_vars.MissionMap.player_outline.thickness)
                    Overlay().EndDraw()
                PyImGui.unindent(20.0)
              
                
#region mini_map_tab
def draw_world_map_tab():
    if not Map.WorldMap.IsWindowOpen():
        PyImGui.text("World Map window is not open.")
        if PyImGui.button("Open World Map"):
            Map.WorldMap.OpenWindow()
    else:
        if PyImGui.button("Close World Map"):
            Map.WorldMap.CloseWindow()
            
        if PyImGui.collapsing_header("World Map Data:"):
            frame_id = Map.WorldMap.GetFrameID()
            is_mouse_over = Map.WorldMap.IsMouseOver()
            mm_coords = Map.WorldMap.GetWindowCoords()
            zoom = Map.WorldMap.GetZoom()

            screen_mouse_x, screen_mouse_y = Map.WorldMap.GetLastClickCoords()
            screen_right_mouse_x, screen_right_mouse_y = Map.WorldMap.GetLastRightClickCoords()

            # --- simple scalar rows ---
            rows: list[tuple[str, str | int | float]] = [
                ("frame_id",               f"{frame_id}"),
                ("Is Mouse Over",          f"{is_mouse_over}"),
                ("Coords (l,t,r,b)",       f"{mm_coords}"),
                ("Zoom",                   f"{zoom:.3f}"),
                ("Last Click (screen)",    f"({screen_mouse_x:.3f}, {screen_mouse_y:.3f})"),
                ("Last Right Click",       f"({screen_right_mouse_x:.3f}, {screen_right_mouse_y:.3f})"),
            ]

            draw_kv_table("WorldMapPrimary", rows)
            PyImGui.separator()

            # --- params section ---
            params = Map.WorldMap.GetParams()
            if params:
                if PyImGui.collapsing_header("Params (uint32 values)"):
                    PyImGui.begin_table("ParamsTable", 2, PyImGui.TableFlags.Borders)
                    PyImGui.table_setup_column("Index")
                    PyImGui.table_setup_column("Value")
                    PyImGui.table_headers_row()

                    for i, val in enumerate(params):
                        PyImGui.table_next_row()
                        PyImGui.table_next_column(); PyImGui.text(f"[{i:03d}]")
                        PyImGui.table_next_column(); PyImGui.text(f"{val}")

                    PyImGui.end_table()
                    PyImGui.separator()

            # --- extra data as KV list ---
            extra_data = Map.WorldMap.GetExtraData()
            if extra_data:
                if PyImGui.collapsing_header("Extra Data"):
                    PyImGui.begin_table("ExtraDataTable", 2, PyImGui.TableFlags.Borders)
                    for key, value in extra_data.items():
                        PyImGui.table_next_row()
                        PyImGui.table_next_column(); PyImGui.text(f"{key}")
                        PyImGui.table_next_column(); PyImGui.text(f"{value}")
                    PyImGui.end_table()
                    
def draw_pregame_tab():
    if not Map.Pregame.IsWindowOpen():
        PyImGui.text("Pregame context not ready.")
        if PyImGui.button("Log Out to Character Select"):
            Map.Pregame.LogOutToCharachterSelect()
            print ("clicked")
    else:
        if PyImGui.collapsing_header("Pregame Data:"):
            frame_id = Map.Pregame.GetFrameID()
            chosen_character_index = Map.Pregame.GetChosenCharacterIndex()
            
            character_list = Map.Pregame.GetCharList()
            
            chosen_char = character_list[chosen_character_index] if (0 <= chosen_character_index < len(character_list)) else None
            chosen_char_name = chosen_char.character_name if chosen_char else "N/A"
            chosen_char_level = chosen_char.level if chosen_char else "N/A"
            chosen_char_current_map_id = chosen_char.current_map_id if chosen_char else "N/A"

            # --- simple scalar rows ---
            rows: list[tuple[str, str | int | float]] = [
                ("frame_id",               f"{frame_id}"),
                
                ("Chosen Character Index", f"{chosen_character_index}"),
                ("Chosen Character Name",  f"{chosen_char_name}"),
                ("Chosen Character Level", f"{chosen_char_level}"),
                ("Chosen Character Current Map ID", f"{chosen_char_current_map_id} - {Map.GetMapName(chosen_char_current_map_id)}"),

            ]

            draw_kv_table("WorldMapPrimary", rows)
            PyImGui.separator()
            if PyImGui.collapsing_header("Extra Data:"):
                context = Map.Pregame.GetContextStruct()
                if context is None:
                    PyImGui.text("Pregame context struct is not available.")
                    return
                
                rows: list[tuple[str, str | int | float]] = [
                    ("Unk01",           f"{list(context.Unk01)}"),
                    ("h0054",          f"{context.h0054}"),
                    ("h0058",          f"{context.h0058}"),
                    ("Unk02_0",        f"{context.Unk02[0]} - {context.Unk02[1]}"),
                    ("h0060",          f"{context.h0060}"),
                    ("Unk03_0",        f"{context.Unk03[0]} - {context.Unk03[1]}"),
                    ("h0068",          f"{context.h0068}"),
                    ("Unk04",          f"{context.Unk04}"),
                    ("h0070",          f"{context.h0070}"),
                    ("Unk05",          f"{context.Unk05}"),
                    ("h0078",          f"{context.h0078}"),
                    ("Unk06",          f"{list(context.Unk06)}"),
                    ("h00a0",          f"{context.h00a0}"),
                    ("h00a4",          f"{context.h00a4}"),
                    ("h00a8",          f"{context.h00a8}"),
                    ("Unk07",          f"{list(context.Unk07)}"),
                    ("Unk08",          f"{context.Unk08}"),
                ]     
                draw_kv_table("PregameExtraData", rows)
                
                PyImGui.separator()
                
            if PyImGui.collapsing_header("Character List:"):
                for i, char in enumerate(character_list):
                    if PyImGui.collapsing_header(f"Character {i}: {char.character_name}"):
                        rows: list[tuple[str, str | int | float]] = [
                            ("Index",                   f"{i}"),
                            ("Character Name",          f"{char.character_name}"),
                            ("Level",                   f"{char.level}"),
                            ("Current Map ID",          f"{char.current_map_id} - {Map.GetMapName(char.current_map_id)}"),
                        ]
                        draw_kv_table(f"Character_{i}", rows)
                        PyImGui.separator()
                        
                        if PyImGui.collapsing_header("extra_data"):
                            rows: list[tuple[str, str | int | float]] = [
                                ("Unk00",           f"{char.Unk00}"),
                                ("pvp_or_campaign", f"{char.pvp_or_campaign}"),
                                ("UnkPvPData01",    f"{char.UnkPvPData01}"),
                                ("UnkPvPData02",    f"{char.UnkPvPData02}"),
                                ("UnkPvPData03",    f"{char.UnkPvPData03}"),
                                ("UnkPvPData04",    f"{char.UnkPvPData04}"),
                                ("Unk01",           f"{list(char.Unk01)}"),
                                ("Unk02",           f"{list(char.Unk02)}"),
                            ]
                            draw_kv_table(f"CharacterExtraData_{i}", rows)
                            PyImGui.separator()
                            
  

    

    
def draw_map_data():
    global _selected_view, SECTION_INFO, map_vars
    if PyImGui.begin_tab_bar("MapDataTabBar"):
        if PyImGui.begin_tab_item("Map##MapInfoTab"):
            
            draw_main_map_tab() # Map Info Tab
            
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Data##MapInfoDataTab"):
            
            draw_map_data_tab() # Map Data Tab
            
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Actions##MapInfoActionsTab"):
            
            draw_map_actions_tab() # Map Actions Tab
            
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Mission Map##MapInfoMissionMapTab"):
            
            draw_mission_map_tab() # Mission Map Tab
                   
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Mini Map##MapInfoMiniMapTab"):
            
            draw_mini_map_tab() # Mini Map Tab
                   
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("World Map##MapInfoWorldMapTab"):
            
            draw_world_map_tab() # World Map Tab
                   
            PyImGui.end_tab_item()
            
        if PyImGui.begin_tab_item("Pregame##MapInfoPregameTab"):
            
            draw_pregame_tab() # Pregame Tab
                   
            PyImGui.end_tab_item()
            
        PyImGui.end_tab_bar()

#region Agents
def draw_agents_view():
    PyImGui.text("Agents View")
    player_agent_id = Player.GetAgentID()
    agent = AgentArray.GetAgentByID(player_agent_id)
    if agent is None:
        PyImGui.text("Player agent not found.")
        return
    else:
        PyImGui.text(f"Player Agent ID: {player_agent_id}")
        PyImGui.separator()
    
#region Main Window
def draw_window():
    global _selected_view
    if PyImGui.begin(MODULE_NAME, True, PyImGui.WindowFlags.AlwaysAutoResize):
        # ================= LEFT PANEL =================
        PyImGui.begin_child(
            "left_panel",
            (180.0, 600.0),   # fixed width, full height
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
            (500.0, 600.0),     # take remaining space
            False,
            0
        )
        
        if _selected_view == "Map":
            draw_map_data()
        elif _selected_view == "Agents":
            draw_agents_view()

        PyImGui.end_child()

    PyImGui.end()



def main():
    draw_window()

if __name__ == "__main__":
    main()
