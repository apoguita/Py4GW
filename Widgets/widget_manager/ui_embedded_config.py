from Py4GWCoreLib import *
from . import state
from .ui_config_sections import draw_account_widget_config, draw_quick_dock_config

def draw_embedded_widget_config():
    interface_frame_id = UIManager.GetChildFrameID(1431953425, [1,4294967291])
    options_inner_frame_id = UIManager.GetChildFrameID(1431953425, [1])

    options_inner_left, options_inner_top, options_inner_right, options_inner_bottom = UIManager.GetFrameCoords(options_inner_frame_id) 
    width = options_inner_right - options_inner_left
    height = options_inner_bottom - options_inner_top 
    
    interface_tab_left, interface_tab_top, interface_tab_right, interface_tab_bottom = UIManager.GetFrameCoords(interface_frame_id) 
    button_x = interface_tab_right - 12
    button_y = interface_tab_top - 11
    
    ui_size = UIManager.GetEnumPreference(EnumPreference.InterfaceSize)
    ui_button_size = {
        4294967295: (70, 18),   # Small
        0: (78, 19),   # Medium
        1: (86, 22),   # Large
        2: (94, 24),   # Largest
    }
    ui_button_size_offsets = {
        4294967295: (5, 5),   # Small
        0: (5, 8),   # Normal
        1: (5, 8),   # Large
        2: (5, 10),  # Largest
    }
    ui_offsets = {
        4294967295: (22, 24),  # Small
        0: (25, 25),  # Normal
        1: (29, 29),  # Large
        2: (33, 33),  # Largest
    }
    
    button_flags = (PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.AlwaysAutoResize | 
                    PyImGui.WindowFlags.NoResize | PyImGui.WindowFlags.NoMove | 
                    PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoBackground)
    embedded_window_flags = (PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.AlwaysAutoResize | 
                    PyImGui.WindowFlags.NoResize | PyImGui.WindowFlags.NoMove | 
                    PyImGui.WindowFlags.NoScrollbar)

    label = "Widgets"

    if not UIManager.IsWindowVisible(interface_frame_id):
        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.10, 0.10, 0.10, 0.0))        # transparent base
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.25, 0.25, 0.25, 1.0)) # light on hover
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.15, 0.15, 0.15, 1.0))  # darker when clicked
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 1.0, 1.0, 1.0))            # pure white
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameRounding, 4.0)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.FramePadding , 0)
        x_off, y_off = ui_button_size_offsets.get(ui_size, (5, 6))
        PyImGui.set_next_window_pos(button_x + x_off, button_y + y_off)
        if PyImGui.begin("##floating_config_button", button_flags):
            button_w, button_h = ui_button_size.get(ui_size, (78, 20))
            if PyImGui.button(label, button_w, button_h):
                state.show_config_window = not state.show_config_window
        PyImGui.end()
        PyImGui.pop_style_color(4)
        PyImGui.pop_style_var(2)

    if state.show_config_window:
        if not UIManager.IsWindowVisible(interface_frame_id):
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,4.0)
            # PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg , (0.0, 0.0, 0.0, 1.0))
            PyImGui.push_style_color(PyImGui.ImGuiCol.WindowBg, (0.05, 0.05, 0.05, 1.0))
            top_offset, height_offset = ui_offsets.get(ui_size, (25, 23))
            PyImGui.set_next_window_pos(options_inner_left, options_inner_top + top_offset)
            PyImGui.set_next_window_size(width, height - height_offset)
            if PyImGui.begin("##widget_config_content",state.show_config_window, embedded_window_flags):
                #config options go here
                PyImGui.spacing()
                PyImGui.text_colored("Widget Configuration", (1.0, 0.94, 0.75, 1.0))
                PyImGui.spacing()

                draw_quick_dock_config()
                
                PyImGui.spacing()
                PyImGui.separator()
                PyImGui.spacing()
                
                draw_account_widget_config()
                
                PyImGui.spacing()
                PyImGui.separator()
                PyImGui.spacing()
                
                PyImGui.text("Previous Widget UI Settings")
                PyImGui.spacing()    
                state.old_menu = PyImGui.checkbox("Disable Old Floating Menu" if state.old_menu else "Enable Old Floating Menu", state.old_menu)
                ImGui.show_tooltip("Disable Old Floating Menu" if state.old_menu else "Enable Old Floating Menu")
                
                PyImGui.spacing()
                state.show_hidden_widgets = PyImGui.checkbox("Show Hidden Widgets", state.show_hidden_widgets)
                ImGui.show_tooltip("Toggle visibility of hidden/internal widgets in menus")
                PyImGui.separator()
                
            PyImGui.end()
            PyImGui.pop_style_var(1)
            PyImGui.pop_style_color(1)
        else:
            state.show_config_window = False
