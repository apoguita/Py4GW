from Py4GWCoreLib import PyImGui, ImGui, UIManager, Map, Overlay, IconsFontAwesome5, Py4GW, ConsoleLog
from . import state
from .handler import handler
from .ui_widget_menu import draw_widget_popup_menus
from .config_scope import is_in_character_select

def draw_floating_menu():
    chara_select = is_in_character_select()
    index = state.floating_attachment_index
    io = PyImGui.get_io()
    screen_w = io.display_size_x
    screen_h = io.display_size_y

    if chara_select:
        content_frame_id = UIManager.GetChildFrameID(2232987037,[0])
    elif index == 0:  # Menu button 
        content_frame_id = UIManager.GetFrameIDByHash(1144678641)
    elif index == 1:  # District selection
        content_frame_id = UIManager.GetFrameIDByHash(3916130160)
    elif index == 2:  # Skill Bar
        content_frame_id = UIManager.GetFrameIDByHash(641635682)
    elif index == 3:  # Free Drag
        content_frame_id = None  # Do not assign an invalid frame ID
    else:
        content_frame_id = UIManager.GetFrameIDByHash(1144678641) #fallback to actual menu button
    
    if content_frame_id is not None:
        frame_left, frame_top, frame_right, frame_bottom = UIManager.GetFrameCoords(content_frame_id)
    else:
        frame_left = frame_top = frame_right = frame_bottom = 0

    if chara_select:
        button_x = frame_right - 8
        button_y = frame_top - 5.1
        base     = (0.20, 0.25, 0.32, 1.0) # dark slate blue-gray
        hover    = (0.30, 0.35, 0.42, 1.0) # lighter muted steel blue
        active   = (0.15, 0.18, 0.24, 1.0) # darker navy-charcoal mix
        border   = (0.50, 0.55, 0.60, 1.0) # neutral soft silver-blue
    elif content_frame_id is not None and index == 0 and not Map.IsMapLoading() and not UIManager.IsWindowVisible(content_frame_id): #Menu Button
        button_x = frame_right - 12
        button_y = frame_top - 11
        state.floating_menu_pos = (button_x, button_y)
        base   = (0.40, 0.36, 0.33, 1.0)
        hover  = (0.48, 0.44, 0.40, 1.0)
        active = (0.28, 0.26, 0.23, 1.0)
        border = (0.85, 0.82, 0.78, 1.0)
    elif content_frame_id is not None and index == 0: #Menu Button
        button_x, button_y =state.floating_menu_pos
        base   = (0.40, 0.36, 0.33, 1.0)
        hover  = (0.48, 0.44, 0.40, 1.0)
        active = (0.28, 0.26, 0.23, 1.0)
        border = (0.85, 0.82, 0.78, 1.0)
    elif content_frame_id is not None and index == 1 and not Map.IsMapLoading() and not UIManager.IsWindowVisible(content_frame_id): #District Selection
        button_x = frame_right - 35
        button_y = frame_top - 6
        state.floating_district_pos = (button_x, button_y)
        base     = (0.20, 0.25, 0.32, 1.0) # dark slate blue-gray
        hover    = (0.30, 0.35, 0.42, 1.0) # lighter muted steel blue
        active   = (0.15, 0.18, 0.24, 1.0) # darker navy-charcoal mix
        border   = (0.50, 0.55, 0.60, 1.0) # neutral soft silver-blue
    elif content_frame_id is not None and index == 1: #District Selection
        button_x, button_y =state.floating_district_pos
        base     = (0.20, 0.25, 0.32, 1.0) # dark slate blue-gray
        hover    = (0.30, 0.35, 0.42, 1.0) # lighter muted steel blue
        active   = (0.15, 0.18, 0.24, 1.0) # darker navy-charcoal mix
        border   = (0.50, 0.55, 0.60, 1.0) # neutral soft silver-blue
    elif content_frame_id is not None and index == 2 and not Map.IsMapLoading() and not UIManager.IsWindowVisible(content_frame_id): #Skill bar
        button_x = frame_right + 10
        button_y = frame_top + 25
        state.floating_skill_pos = (button_x, button_y)
        base   = (0.30, 0.30, 0.32, 1.0)  # medium gray
        hover  = (0.45, 0.45, 0.48, 1.0)  # brighter highlight
        active = (0.20, 0.20, 0.22, 1.0)  # darker pressed state
        border = (0.60, 0.60, 0.65, 1.0)  # silver-gray border
    elif content_frame_id is not None and index == 2: #Skill bar
        button_x, button_y =state.floating_skill_pos
        base   = (0.30, 0.30, 0.32, 1.0)  # medium gray
        hover  = (0.45, 0.45, 0.48, 1.0)  # brighter highlight
        active = (0.20, 0.20, 0.22, 1.0)  # darker pressed state
        border = (0.60, 0.60, 0.65, 1.0)  # silver-gray border
    elif index == 3:
        if not state.floating_drag_locked and state.hovering_floating_button:
            if not state.is_dragging_floating_button and PyImGui.is_mouse_clicked(0):
                mx, my = Overlay().GetMouseCoords()
                wx, wy = state.floating_window_pos
                state.floating_button_offset = (mx - wx, my - wy)
                state.is_dragging_floating_button = True

            if state.is_dragging_floating_button and PyImGui.is_mouse_down(0):
                mx, my = Overlay().GetMouseCoords()
                dx, dy = state.floating_button_offset
                
                new_x = mx - dx
                new_y = my - dy
                
                button_width = 35
                button_height = 25
                
                clamped_x = max(0, min(new_x, screen_w - button_width))
                clamped_y = max(0, min(new_y, screen_h - button_height))
                
                state.floating_window_pos = (clamped_x, clamped_y)

            elif state.is_dragging_floating_button and not PyImGui.is_mouse_down(0):
                state.is_dragging_floating_button = False
                x, y = state.floating_window_pos
                handler._write_setting("FloatingMenu", "fmx", x)
                handler._write_setting("FloatingMenu", "fmy", y)

        button_x, button_y = state.floating_window_pos       
        base   = (0.08, 0.08, 0.08, 1.0)
        hover  = (0.16, 0.16, 0.16, 1.0)
        active = (0.05, 0.05, 0.05, 1.0)
        border = (0.25, 0.25, 0.25, 1.0)
    else: #loading screen backup
        button_x = 20
        button_y = 100
        base   = (0.08, 0.08, 0.08, 1.0)
        hover  = (0.16, 0.16, 0.16, 1.0)
        active = (0.05, 0.05, 0.05, 1.0)
        border = (0.25, 0.25, 0.25, 1.0)
    
    if state.floating_custom_colors_enabled and not chara_select:
        base   = state.floating_custom_colors["base"]
        hover  = state.floating_custom_colors["hover"]
        active = state.floating_custom_colors["active"]
        border = state.floating_custom_colors["border"]
    
    window_flags = (PyImGui.WindowFlags.NoCollapse | PyImGui.WindowFlags.NoTitleBar | 
                    PyImGui.WindowFlags.AlwaysAutoResize | PyImGui.WindowFlags.NoScrollWithMouse |
                    PyImGui.WindowFlags.NoResize | PyImGui.WindowFlags.NoMove | 
                    PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoBackground)
    
    
    PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        base)
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, hover)
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  active)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Border,        border)
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 1.0)
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameRounding, 3.0)
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 1.0, 1.0, 1.0))

    flip_widgets = ((button_x - 50) > screen_w / 2)
    if flip_widgets:
        if content_frame_id is not None and index == 0 and not UIManager.IsWindowVisible(content_frame_id): #Menu Button
            button_x = frame_left - 90
        elif content_frame_id is not None and index == 1 and not UIManager.IsWindowVisible(content_frame_id): #District Selection
            button_x = frame_left - 100
        elif content_frame_id is not None and index == 2 and not UIManager.IsWindowVisible(content_frame_id): #Skill bar
            button_x = frame_left - 110
        state.left_side = True
    else:
        state.left_side = False


    PyImGui.set_next_window_pos(button_x, button_y)
    PyImGui.set_next_window_size(100, 0)
    
    if PyImGui.begin("##floating_button", window_flags):
        button_x, button_y = PyImGui.get_window_pos()
        menu_y = button_y + 35 
        menu_x = button_x + 12 

        if state.popup_open and state.popup_height_known:
            window_y = button_y
            window_center_y = window_y + 35 / 2
            if window_center_y < screen_h / 2:
                menu_y = button_y + 45  # open downward
                state.opening_downward = True
            else:
                menu_y = button_y - state.popup_height # open upward
                state.opening_downward = False
                
        
        icon = IconsFontAwesome5.ICON_CIRCLE if state.popup_open else IconsFontAwesome5.ICON_DOT_CIRCLE
            
        if state.left_side:
            button_label = f"Widgets {icon}##WigetUIButton"
        else:
            button_label = f"{icon} Widgets##WigetUIButton"
        
        state.hovering_floating_button = False
        if PyImGui.button(button_label, 0, 0):
            PyImGui.open_popup("FloatingMenu")
            state.popup_open = True
            
        state.hovering_floating_button = PyImGui.is_item_hovered()
            
        PyImGui.set_next_window_pos(menu_x, menu_y)
        PyImGui.pop_style_color(5)
        PyImGui.pop_style_var(2)
        if PyImGui.begin_popup("FloatingMenu"):
            state.popup_height = PyImGui.get_window_height()
            state.popup_height_known = True
            if PyImGui.button(IconsFontAwesome5.ICON_RETWEET + "##Reload Widgets"):
                ConsoleLog(state.module_name, "Reloading Widgets...", Py4GW.Console.MessageType.Info)
                state.initialized = False
                handler.discover_widgets()
                state.initialized = True
            ImGui.show_tooltip("Reloads all widgets")
            PyImGui.same_line(0.0, 10)
            is_enabled = state.enable_all
            toggle_label = IconsFontAwesome5.ICON_TOGGLE_ON if state.enable_all else IconsFontAwesome5.ICON_TOGGLE_OFF
            if is_enabled:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.153, 0.318, 0.929, 1.0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.6, 0.6, 0.9, 1.0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.6, 0.6, 0.6, 1.0))
            if PyImGui.button(toggle_label + "##widget_disable"):
                state.enable_all = not state.enable_all
                handler._write_global_setting(state.module_name, "state.enable_all", str(state.enable_all))
            if is_enabled:
                PyImGui.pop_style_color(3)
            ImGui.show_tooltip("Toggle all widgets")
            PyImGui.separator()
            draw_widget_popup_menus()
            PyImGui.end_popup()
        else:
            state.popup_open = False

    PyImGui.end()
