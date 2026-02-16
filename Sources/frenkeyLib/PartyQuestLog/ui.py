import math
import time
import PyImGui
import PyOverlay
from HeroAI.ui import get_display_name
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.GlobalCache.SharedMemory import AccountStruct
from Py4GWCoreLib.ImGui_src.ImGuisrc import ImGui
from Py4GWCoreLib.ImGui_src.Textures import TextureState, ThemeTextures
from Py4GWCoreLib.ImGui_src.WindowModule import WindowModule
from Py4GWCoreLib.ImGui_src.types import Alignment
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Quest import Quest
from Py4GWCoreLib.Quest import Quest
from Py4GWCoreLib.enums_src.GameData_enums import ProfessionShort
from Py4GWCoreLib.enums_src.IO_enums import Key, ModifierKey
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.py4gwcorelib_src.Timer import Timer
from Py4GWCoreLib.py4gwcorelib_src.Color import Color, ColorPalette
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler
from Sources.frenkeyLib.PartyQuestLog.settings import Settings
from Sources.ApoSource.account_data_src.quest_data_src import QuestData, QuestNode

class UI():
    COLOR_MAP: dict[str, tuple[float, float, float, float]] = {
        "@warning": ColorPalette.GetColor("red").to_tuple_normalized(),
        "@Warning": ColorPalette.GetColor("red").to_tuple_normalized(),
        "@Quest":   ColorPalette.GetColor("bright_green").to_tuple_normalized(),
        "@quest":   ColorPalette.GetColor("bright_green").to_tuple_normalized(),
        "@completed":   ColorPalette.GetColor("creme").to_tuple_normalized(),
        "Header":  ColorPalette.GetColor("creme").to_tuple_normalized(),   
    }
    
    QUEST_STATE_COLOR_MAP: dict[str, Color] = {
        "Completed": ColorPalette.GetColor("bright_green").opacify(0.6),
        "Active": ColorPalette.GetColor("white").opacify(0.6),
        "Inactive": ColorPalette.GetColor("light_gray").opacify(0.3),
    }
    gray_color = Color(150, 150, 150, 255)
    
    Settings : "Settings" = Settings()
    QuestLogWindow : WindowModule = WindowModule("PartyQuestLog", "Party Quest Log", window_size=(Settings.LogPosWidth, Settings.LogPosHeight), window_pos=(Settings.LogPosX, Settings.LogPosY), can_close=True)
    ConfigWindow : WindowModule = WindowModule("PartyQuestLog#Config", "Party Quest Log - Settings", window_size=(500, 300), can_close=True)
    ActiveQuest : QuestNode | None = None
    AnimationTimer : Timer = Timer()
        
    @staticmethod
    def draw_log(quest_data : QuestData, accounts: dict[int, AccountStruct]):
        UI.QuestLogWindow.open = UI.Settings.LogOpen
        
        if not UI.QuestLogWindow.open:
            return
        
        active_quest_id = Quest.GetActiveQuest()
        has_mission = quest_data.mission_map_quest is not None

        UI.ActiveQuest = quest_data.quest_log.get(active_quest_id, quest_data.mission_map_quest if quest_data.mission_map_quest is not None and quest_data.mission_map_quest_loaded else None)
        
        UI.QuestLogWindow.window_name = f"Party Quest Log [{ModifierKey.Ctrl.name}+{Key.L.name.replace('VK_','')}]"
        open = UI.QuestLogWindow.begin()
        
        if open:
            style = ImGui.get_style()
            grouped_quests : dict[str, list[QuestNode]] = {}
            avail = PyImGui.get_content_region_avail()
            _, height = avail[0], avail[1] / 2
                    
            if quest_data.mission_map_quest is not None:
                grouped_quests.setdefault(quest_data.mission_map_quest.quest_location, []).append(quest_data.mission_map_quest)
            
            for quest in quest_data.quest_log.values():
                if quest.is_primary:
                    grouped_quests.setdefault("Primary", []).append(quest)
                else:
                    grouped_quests.setdefault(quest.quest_location, []).append(quest)
            
            # Sort quests by name for each location
            for location, quests in grouped_quests.items():
                sorted_quests = sorted(quests, key=lambda q: q.name)
                grouped_quests[location] = sorted_quests
            
            style.WindowPadding.push_style_var(2, 8)
            ImGui.begin_child("QuestLogChild", (0, height), border=True)
            style.WindowPadding.pop_style_var()
                        
            width = PyImGui.get_content_region_avail()[0]
            og_item_spacing = style.ItemSpacing.get_current()
            
            for location, quests in grouped_quests.items():
                contains_active_quest = any(quest == UI.ActiveQuest for quest in quests)
                
                if contains_active_quest:
                    PyImGui.set_next_item_open(True, PyImGui.ImGuiCond.Always)
                
                ImGui.push_font("Regular", 16)
                location_open = ImGui.tree_node(f"{location}")
                ImGui.pop_font()
                                
                if location_open:                    
                    style.ItemSpacing.push_style_var(4, 0)
                    
                    for quest in quests:  
                        max_width = max(1, width - (len(accounts) * 10) - 30)
                        tokenized_lines = Utils.TokenizeMarkupText(f"{quest.name}{(" <c=@completed>(Completed)</c>") if quest.is_completed else ""}", max_width=max_width)     
                                
                        posY = PyImGui.get_cursor_pos_y()               
                        cursor = PyImGui.get_cursor_screen_pos()
                        height_selectable = len(tokenized_lines) * PyImGui.get_text_line_height() + 4
                        computed_rect = (cursor[0], cursor[1], width, height_selectable)
                        color = Color(200, 200, 200, 40) if quest == UI.ActiveQuest else \
                                Color(200, 200, 200, 20) if ImGui.is_mouse_in_rect(computed_rect) else \
                                None
                                
                        if color:
                            style.ChildBg.push_color(color.rgb_tuple)                        
                            
                        style.Border.push_color(color.opacify(0.1).rgb_tuple if color else (0,0,0,0))
                        style.WindowPadding.push_style_var(4, 4)
                        ImGui.begin_child(f"QuestSelectable_{quest.quest_id}", (0, height_selectable), border=True, flags=PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse)  
                        ImGui.render_tokenized_markup(tokenized_lines, max_width=max_width, COLOR_MAP=UI.COLOR_MAP)
                        ImGui.end_child()
                        style.WindowPadding.pop_style_var()
                                    
                        style.Border.pop_color()
                        
                        if color:
                            style.ChildBg.pop_color()                        
                            
                        if PyImGui.is_item_clicked(0):
                            if PyImGui.is_mouse_double_clicked(0):
                                if Map.IsMapUnlocked(quest.map_to):
                                    ConsoleLog("Party Quest Log", f"Traveling to map '{Map.GetMapName(quest.map_to)}' ({quest.map_to}) for quest '{quest.name}'...")
                                    Map.Travel(quest.map_to)
                                else:
                                    ConsoleLog("Party Quest Log", f"Cannot travel to locked map '{Map.GetMapName(quest.map_to)}' ({quest.map_to}).")
                            else:
                                UI.ActiveQuest = quest
                                Quest.SetActiveQuest(quest.quest_id)
                            
                        if PyImGui.is_item_hovered():
                            if accounts: 
                                style.ItemSpacing.push_style_var(og_item_spacing.value1, og_item_spacing.value2)   
                                ImGui.begin_tooltip()
                                
                                bullet_col_width = PyImGui.get_text_line_height()
                                ImGui.begin_table("QuestStatusTable", 3, PyImGui.TableFlags.NoBordersInBody)
                                PyImGui.table_setup_column("bullet", PyImGui.TableColumnFlags.WidthFixed, bullet_col_width)
                                PyImGui.table_setup_column("professions", PyImGui.TableColumnFlags.WidthFixed, bullet_col_width * 2.5)
                                PyImGui.table_setup_column("text", PyImGui.TableColumnFlags.WidthStretch)
                                
                                for acc in accounts.values():
                                    name = get_display_name(acc)
                                    acc_quest = next((q for q in acc.QuestLog.Quests if q.QuestID == quest.quest_id), None)
                                    
                                    active = acc_quest is not None
                                    completed = acc_quest and acc_quest.IsCompleted
                                    
                                    color = UI.QUEST_STATE_COLOR_MAP["Completed"] if completed else (UI.QUEST_STATE_COLOR_MAP["Active"] if active else UI.QUEST_STATE_COLOR_MAP["Inactive"])
                                                        
                                    PyImGui.table_next_row()
                                    PyImGui.table_set_column_index(0)
                                    style.Text.push_color(color.rgb_tuple)  
                                    PyImGui.bullet_text("")
                                    style.Text.pop_color()
                                                                    
                                    prof_primary, prof_secondary = "", ""
                                    prof_primary = ProfessionShort(
                                        acc.AgentData.Profession[0]).name if acc.AgentData.Profession[0] != 0 else ""
                                    prof_secondary = ProfessionShort(
                                        acc.AgentData.Profession[1]).name if acc.AgentData.Profession[1] != 0 else ""
                                    PyImGui.table_next_column()
                                    ImGui.text(f"{prof_primary}{('/' if prof_secondary else '')}{prof_secondary}")
                                    
                                    PyImGui.table_next_column()
                                    ImGui.text(name)
                                
                                ImGui.end_table()   
                                
                                ImGui.separator()
                                ImGui.push_font("Regular", 12)
                                for name, col in UI.QUEST_STATE_COLOR_MAP.items():
                                    style.Text.push_color(col.rgb_tuple)  
                                    PyImGui.bullet_text("")
                                    style.Text.pop_color()
                                    
                                    PyImGui.same_line(0, 5)
                                    ImGui.text(f"{name}")
                                    PyImGui.same_line(0, 5)
                                    
                                ImGui.pop_font()
                                ImGui.end_tooltip()
                                style.ItemSpacing.pop_style_var() 
                        
                        after_y = PyImGui.get_cursor_pos_y()
                        for i, acc in enumerate(accounts.values()):
                            PyImGui.set_cursor_pos(width - (i * 10) - 20, posY + 2)
                            ## chek if quest.quest_id is in active quests (.QuestID) 
                            acc_quest = next((q for q in acc.QuestLog.Quests if q.QuestID == quest.quest_id), None)
                            
                            active = acc_quest is not None
                            completed = acc_quest and acc_quest.IsCompleted
                            
                            color = UI.QUEST_STATE_COLOR_MAP["Completed"] if completed else (UI.QUEST_STATE_COLOR_MAP["Active"] if active else UI.QUEST_STATE_COLOR_MAP["Inactive"])

                            style.Text.push_color(color.rgb_tuple)                              
                            PyImGui.bullet_text("")
                            style.Text.pop_color()
                        
                        PyImGui.set_cursor_pos_y(after_y + 4)
                            
                        # ImGui.show_tooltip(f"{acc.AccountEmail} | {acc.CharacterName} | {("Completed" if completed else "Active" if active else "Not Active")} " )
                        # ImGui.show_tooltip(f"{name.lower().replace(" ", "_")}@gmail.com | {name} | {("Completed" if completed else "Active" if active else "Not Active")} " )
                        
                    style.ItemSpacing.pop_style_var()
                    ImGui.tree_pop()
                    
                pass
            
            ImGui.end_child()
            
            ImGui.begin_child("QuestDetailsChild", (0, height - 10), border=False)
            if UI.ActiveQuest is not None:
                UI.draw_quest_details(UI.ActiveQuest, accounts)
            ImGui.end_child()
            
        if UI.QuestLogWindow.changed or (not UI.QuestLogWindow.open):
            pos = UI.QuestLogWindow.window_pos
            UI.Settings.LogPosX = pos[0]
            UI.Settings.LogPosY = pos[1]
            
            size = UI.QuestLogWindow.window_size
            UI.Settings.LogPosWidth = size[0]
            UI.Settings.LogPosHeight = size[1]
            
            UI.Settings.LogOpen = UI.QuestLogWindow.open
            UI.Settings.save_settings()
            UI.QuestLogWindow.changed = False
                                            
        UI.QuestLogWindow.end()
        
    
    @staticmethod
    def draw_quest_details(quest: QuestNode, accounts: dict[int, AccountStruct]):
        child_width = PyImGui.get_content_region_avail()[0]
        text_clip = child_width - 120
        cursor_pos = PyImGui.get_cursor_screen_pos()
        
        PyImGui.push_clip_rect(cursor_pos[0], cursor_pos[1], text_clip, 50, True)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, UI.COLOR_MAP["Header"])
        ImGui.text("Quest Summary", font_size=16)
        PyImGui.pop_style_color(1)
        PyImGui.pop_clip_rect()
        
        PyImGui.same_line(child_width - 110, 0)
        if ImGui.button("Abandon", 100, 20):
            if PyImGui.get_io().key_ctrl:
                ConsoleLog("Party Quest Log", f"Requesting to abandon quest '{quest.name}'...")
                Quest.AbandonQuest(quest.quest_id)
                
                for _, acc in accounts.items():                
                    GLOBAL_CACHE.ShMem.SendMessage(Player.GetAccountEmail(), acc.AccountEmail, SharedCommandType.AbandonQuest, (quest.quest_id,0,0,0))
        
        if PyImGui.is_item_hovered():
            ImGui.begin_tooltip()
            ImGui.text_colored("Ctrl + Click to abandon the quest on all party members.", UI.gray_color.color_tuple)    
            ImGui.end_tooltip()
        
        PyImGui.spacing()
                                                
        
        tokens = Utils.TokenizeMarkupText(quest.objectives, max_width=child_width)
        ImGui.render_tokenized_markup(tokens, max_width=child_width, COLOR_MAP=UI.COLOR_MAP)

        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, UI.COLOR_MAP["Header"])
        PyImGui.text_wrapped(f"{quest.npc_quest_giver}")
        PyImGui.pop_style_color(1)

        tokens = Utils.TokenizeMarkupText(quest.description, max_width=child_width)
        ImGui.render_tokenized_markup(tokens, max_width=child_width, COLOR_MAP=UI.COLOR_MAP)

        PyImGui.separator()
        PyImGui.text(f"From: {Map.GetMapName(quest.map_from)}")
        PyImGui.text(f"To: {Map.GetMapName(quest.map_to)}")
        PyImGui.text(f"Marker X,Y: ({quest.quest_marker[0]}, {quest.quest_marker[1]})")
        PyImGui.end_child()

    @staticmethod
    def draw_modal():
        pass
        
    @staticmethod
    def ConvertQuestMarkerCoordinates(marker_x, marker_y) -> tuple[float, float] | None:
        """Convert quest marker coordinates from unsigned to signed if needed.

        Returns None if coordinates are invalid, otherwise returns (x, y) as floats.
        """
        # Check for sentinel values
        if marker_x == 2147483648 or marker_y == 2147483648:
            return None
        if marker_x == 0 and marker_y == 0:
            return None

        # Convert unsigned to signed
        if marker_y > 2147483647:
            marker_y = marker_y - 4294967296
        if marker_x > 2147483647:
            marker_x = marker_x - 4294967296

        return float(marker_x), float(marker_y)
    
    @staticmethod
    def draw_edge_arrow(
        overlay: Overlay,
        target_x: float,
        target_y: float,
        rect: tuple[float, float, float, float],  # (x1, y1, x2, y2)
        color: int,
        size: float = 12.0,
        thickness: float = 2.0,
        rotation: float = 0.0,  # radians
    ):
        x1, y1, x2, y2 = rect
        cx = (x1 + x2) * 0.5
        cy = (y1 + y2) * 0.5

        dx = target_x - cx
        dy = target_y - cy

        if dx == 0 and dy == 0:
            return

        # Apply minimap rotation
        if rotation != 0.0:
            dx, dy = UI.rotate_vector(dx, dy, -rotation)

        length = math.hypot(dx, dy)
        dx /= length
        dy /= length

        # Edge intersection
        t_vals = []

        if dx != 0:
            t_vals.append((x1 - cx) / dx)
            t_vals.append((x2 - cx) / dx)
        if dy != 0:
            t_vals.append((y1 - cy) / dy)
            t_vals.append((y2 - cy) / dy)

        t = min(t for t in t_vals if t > 0)
        ix = cx + dx * t
        iy = cy + dy * t

        angle = math.atan2(dy, dx)
        left = angle + math.radians(150)
        right = angle - math.radians(150)

        tip_x = ix
        tip_y = iy

        left_x = tip_x + math.cos(left) * size
        left_y = tip_y + math.sin(left) * size

        right_x = tip_x + math.cos(right) * size
        right_y = tip_y + math.sin(right) * size

        overlay.DrawLine(tip_x, tip_y, left_x, left_y, color, thickness)
        overlay.DrawLine(tip_x, tip_y, right_x, right_y, color, thickness)

    @staticmethod
    def rotate_vector(x: float, y: float, angle: float) -> tuple[float, float]:
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return (
            x * cos_a - y * sin_a,
            x * sin_a + y * cos_a,
        )
        
    @staticmethod
    def draw_overlays(accounts : dict[int, AccountStruct]):
        if not UI.Settings.ShowFollowerActiveQuestOnMinimap and not UI.Settings.ShowFollowerActiveQuestOnMissionMap:
            return

        active_quests = [acc.QuestLog.ActiveQuest for acc in accounts.values() if acc.QuestLog.ActiveQuest.QuestID != 0 and UI.Settings.show_quests_for_accounts.get(acc.AccountEmail, True)]
        
        if not active_quests:
            return
        
        overlay = Overlay()
        overlay.BeginDraw()
        
        color_fill = Color(42, 249, 65, 255)
        color_outline = Color(30, 179, 47, 255)
     
        mission_map_open = Map.MissionMap.IsWindowOpen()
        mini_map_open = Map.MiniMap.IsWindowOpen()
        
        if not mission_map_open and not mini_map_open:
            overlay.EndDraw()
            return
        
        if not UI.AnimationTimer.running:
            UI.AnimationTimer.Start()
        
        map_coords = Map.MissionMap.GetMissionMapContentsCoords() # (x1, y1, x2, y2)
        mini_map_coords = Map.MiniMap.GetWindowCoords() # (x1, y1, x2, y2)  
        compass_center = Map.MiniMap.GetMapScreenCenter() # (x, y)  
        rotation = UI.AnimationTimer.GetElapsedTime() * 0.0005  # radians per milli second
        
        for active_quest in active_quests:              
            marker_pos = UI.ConvertQuestMarkerCoordinates(active_quest.MarkerX, active_quest.MarkerY)       
            if marker_pos is None:
                continue
            
            if mission_map_open and UI.Settings.ShowFollowerActiveQuestOnMissionMap:  
                mission_map_pos = Map.MissionMap.MapProjection.GameMapToScreen(marker_pos[0], marker_pos[1])       
                
                if not Utils.IsPointInRect(mission_map_pos[0], mission_map_pos[1], map_coords[0], map_coords[1], map_coords[2] - map_coords[0], map_coords[3] - map_coords[1]):
                    ## Draw arrow pointing to the quest marker at the edge of the mission map
                    UI.draw_edge_arrow(
                        overlay=overlay,
                        target_x=mission_map_pos[0],
                        target_y=mission_map_pos[1],
                        rect=map_coords,
                        color=color_fill.to_color(),
                        size=14.0,
                        thickness=3.0,
                    )
                    pass
                else:            
                    overlay.DrawStarFilled(mission_map_pos[0], mission_map_pos[1], 10.0, 5.0, color_fill.to_color(), 8, rotation)
                    overlay.DrawStar(mission_map_pos[0], mission_map_pos[1], 10.0, 5.0, color_outline.to_color(), 8, 1, rotation)
                
            if mini_map_open and UI.Settings.ShowFollowerActiveQuestOnMinimap:
                mini_map_pos = Map.MiniMap.MapProjection.GamePosToScreen(marker_pos[0], marker_pos[1])  
                        
                radius = ((mini_map_coords[2] - mini_map_coords[0]) * 0.81) / 2
                                        
                if not Utils.point_in_circle(mini_map_pos[0], mini_map_pos[1], compass_center[0], compass_center[1], radius):
                    dx = mini_map_pos[0] - compass_center[0]
                    dy = mini_map_pos[1] - compass_center[1]

                    length = math.hypot(dx, dy)
                    if length > 0:
                        dx /= length
                        dy /= length

                        tip_x = compass_center[0] + dx * radius
                        tip_y = compass_center[1] + dy * radius

                        angle = math.atan2(dy, dx)
                        size = 15.0

                        left = angle + math.radians(150)
                        right = angle - math.radians(150)

                        overlay.DrawLine(
                            tip_x, tip_y,
                            tip_x + math.cos(left) * size,
                            tip_y + math.sin(left) * size,
                            color_fill.to_color(), 3.0
                        )

                        overlay.DrawLine(
                            tip_x, tip_y,
                            tip_x + math.cos(right) * size,
                            tip_y + math.sin(right) * size,
                            color_fill.to_color(), 3.0
                        )
                    pass
                else:    
                    overlay.DrawStarFilled(mini_map_pos[0], mini_map_pos[1], 10.0, 5.0, color_fill.to_color(), 8, rotation)
                    overlay.DrawStar(mini_map_pos[0], mini_map_pos[1], 10.0, 5.0, color_outline.to_color(), 8, 1, rotation)
            
        overlay.EndDraw()
        
    
    @staticmethod
    def draw_configure(accounts : dict[int, AccountStruct]):
        if not UI.ConfigWindow.open:
            return
        
        open = UI.ConfigWindow.begin()
        
        if open:
            style = ImGui.get_style()
            
            if ImGui.begin_tab_bar("PartyQuestLogConfigTabs"):
                if ImGui.begin_tab_item("General Settings"):                        
                    avail = PyImGui.get_content_region_avail()
                    _, height = avail[0], avail[1]
                    
                    ImGui.text_aligned("Quest Log Hotkey", height=22, alignment=Alignment.MidLeft)
                    PyImGui.same_line(0, 5)
                    width_avail = PyImGui.get_content_region_avail()[0]
                    PyImGui.push_item_width(width_avail - 5)
                    key, modifiers = ImGui.keybinding("##HotkeyInfo", key=UI.Settings.HotKeyKey, modifiers=UI.Settings.Modifiers)
                    PyImGui.pop_item_width()
                    
                    if key != UI.Settings.HotKeyKey or modifiers != UI.Settings.Modifiers:
                        ConsoleLog("Party Quest Log", f"Setting new hotkey: {modifiers.name}+{key.name.replace('VK_','')}")
                        UI.Settings.set_questlog_hotkey_keys(key, modifiers)
                    
                    show_only_in_party = ImGui.checkbox("Show Quest Log only when in a Party", UI.Settings.ShowOnlyInParty)
                    if show_only_in_party != UI.Settings.ShowOnlyInParty:
                        UI.Settings.ShowOnlyInParty = show_only_in_party
                        UI.Settings.save_settings()
                        
                    show_only_on_leader = ImGui.checkbox("Show Quest Log only when Party Leader", UI.Settings.ShowOnlyOnLeader)
                    if show_only_on_leader != UI.Settings.ShowOnlyOnLeader:
                        UI.Settings.ShowOnlyOnLeader = show_only_on_leader
                        UI.Settings.save_settings()
                
                    show_follower_on_minimap = ImGui.checkbox("Show Follower Active Quest on Minimap", UI.Settings.ShowFollowerActiveQuestOnMinimap)
                    if show_follower_on_minimap != UI.Settings.ShowFollowerActiveQuestOnMinimap:
                        UI.Settings.ShowFollowerActiveQuestOnMinimap = show_follower_on_minimap
                        UI.Settings.save_settings()
                        
                    show_follower_on_mission_map = ImGui.checkbox("Show Follower Active Quest on Mission Map", UI.Settings.ShowFollowerActiveQuestOnMissionMap)
                    if show_follower_on_mission_map != UI.Settings.ShowFollowerActiveQuestOnMissionMap:
                        UI.Settings.ShowFollowerActiveQuestOnMissionMap = show_follower_on_mission_map
                        UI.Settings.save_settings()
                    ImGui.end_tab_item()
                
                if ImGui.begin_tab_item("Accounts"):
                    for acc in accounts.values():
                        name = get_display_name(acc)
                        enabled = UI.Settings.show_quests_for_accounts.get(acc.AccountEmail.lower(), True)
                        
                        changed = ImGui.checkbox(f"Show quests for {name}", enabled)
                        if changed != enabled:
                            UI.Settings.show_quests_for_accounts[acc.AccountEmail.lower()] = changed
                            UI.Settings.save_settings()
                    ImGui.end_tab_item()
                    
                ImGui.end_tab_bar()
                
                
        if UI.ConfigWindow.changed or not UI.ConfigWindow.open:
            get_widget_handler().set_widget_configuring("PartyQuestLog", UI.ConfigWindow.open)
        
        UI.ConfigWindow.end()
        
        pass