from Py4GWCoreLib import PyImGui, ImGui, time, Overlay, IconsFontAwesome5, Py4GW, ConsoleLog
from . import state
from .handler import handler
from .ui_widget_menu import draw_widget_popup_menus
from .ui_old_menu import draw_old_widget_ui
from .ui_quickdock import quick_dock_menu
from .ui_embedded_config import draw_embedded_widget_config

def draw_floating_menu():
    
    if state.enable_quick_dock:
        quick_dock_menu()
    
    draw_embedded_widget_config()
    
    if state.old_menu:
        draw_old_widget_ui()

    io = PyImGui.get_io()
    screen_w = io.display_size_x
    screen_h = io.display_size_y

    if not state.floating_drag_locked and (state.hovering_floating_button or state.is_dragging_floating_button):
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
            state.floating_write_pending = True
            state.floating_write_timer = time.time()

    button_x, button_y = state.floating_window_pos       
    base   = (0.08, 0.08, 0.08, 1.0)
    hover  = (0.16, 0.16, 0.16, 1.0)
    active = (0.05, 0.05, 0.05, 1.0)
    border = (0.25, 0.25, 0.25, 1.0)
    
    if state.floating_custom_colors_enabled:
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
            
        button_label = f"{icon} Widgets##WigetUIButton"
        
        state.hovering_floating_button = False
        if PyImGui.button(button_label, 0, 0):
            PyImGui.open_popup("FloatingMenu")
            state.popup_open = True
            
        state.hovering_floating_button = PyImGui.is_item_hovered()
            
        PyImGui.set_next_window_pos(menu_x, menu_y)
        PyImGui.pop_style_color(5)
        PyImGui.pop_style_var(2)
        if state.reopen_floating_menu:
            PyImGui.open_popup("FloatingMenu")
            state.reopen_floating_menu = False
        if PyImGui.begin_popup("FloatingMenu"):
            state.popup_height = PyImGui.get_window_height()
            state.popup_height_known = True
            if PyImGui.button(IconsFontAwesome5.ICON_RETWEET + "##Reload Widgets"):
                ConsoleLog(state.module_name, "Reloading Widgets...", Py4GW.Console.MessageType.Info)
                handler.discover_widgets()
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

    if state.floating_write_pending:
        if time.time() - state.floating_write_timer > 0.2:
            x, y = state.floating_window_pos
            handler._write_setting("FloatingMenu", "fmx", x)
            handler._write_setting("FloatingMenu", "fmy", y)
            state.floating_write_pending = False

    PyImGui.end()
