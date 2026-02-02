from Py4GWCoreLib import UIManager, EnumPreference, PyImGui, ImGui, Utils
from . import state
from .handler import handler
from .config_scope import use_account_settings
from .ui_config_sections import draw_account_widget_config, draw_quick_dock_config, draw_debug_config, draw_floating_menu_config

def draw_embedded_widget_config():
    interface_frame_id = UIManager.GetChildFrameID(1431953425, [1,4294967291])
    if isinstance(interface_frame_id, int) and interface_frame_id == 0:
        return
    
    options_inner_frame_id = UIManager.GetChildFrameID(1431953425, [1])
    if isinstance(options_inner_frame_id, int) and options_inner_frame_id == 0:
        return

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
    embedded_window_flags = (PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.NoMove |
                             PyImGui.WindowFlags.NoResize)

    label = "Widgets"

    if isinstance(interface_frame_id, int) and interface_frame_id > 0:
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
        if isinstance(interface_frame_id, int) and interface_frame_id > 0:
            int_tab = UIManager.GetChildFrameID(1431953425, [1, 4294967291])
            con_tab = UIManager.GetChildFrameID(1431953425, [1, 4294967292])
            gra_tab = UIManager.GetChildFrameID(1431953425, [1, 4294967293])
            sou_tab = UIManager.GetChildFrameID(1431953425, [1, 4294967294])
            gen_tab = UIManager.GetChildFrameID(1431953425, [1, 4294967295])
            frames = {
                "int_tab": int_tab,
                "con_tab": con_tab,
                "gra_tab": gra_tab,
                "sou_tab": sou_tab,
                "gen_tab": gen_tab,
            }
            visible = all(isinstance(f, int) and f > 0 for f in frames.values())
            if visible:
                UIManager().DrawFrame(UIManager.GetChildFrameID(1431953425, [1,4294967291]), Utils.RGBToColor(0, 0, 0, 255))
                UIManager().DrawFrame(UIManager.GetChildFrameID(1431953425, [1,4294967292]), Utils.RGBToColor(0, 0, 0, 255))
                UIManager().DrawFrame(UIManager.GetChildFrameID(1431953425, [1,4294967293]), Utils.RGBToColor(0, 0, 0, 255))
                UIManager().DrawFrame(UIManager.GetChildFrameID(1431953425, [1,4294967294]), Utils.RGBToColor(0, 0, 0, 255))
                UIManager().DrawFrame(UIManager.GetChildFrameID(1431953425, [1,4294967295]), Utils.RGBToColor(0, 0, 0, 255))

            PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,4.0)
            # PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg , (0.0, 0.0, 0.0, 1.0))
            PyImGui.push_style_color(PyImGui.ImGuiCol.WindowBg, (0.05, 0.05, 0.05, 1.0))
            top_offset, height_offset = ui_offsets.get(ui_size, (25, 23))
            PyImGui.set_next_window_pos(options_inner_left, options_inner_top + top_offset)
            PyImGui.set_next_window_size(width, height - height_offset)
            if PyImGui.begin("##widget_config_content", state.show_config_window, embedded_window_flags):
                avail_w, avail_h = PyImGui.get_content_region_avail()
                desired_scrollable_height = 1000  # Or any fixed height greater than min frame height
                scroll_h = max(avail_h, desired_scrollable_height)

                PyImGui.begin_child("##scrollable_config_area", (avail_w, scroll_h), False, PyImGui.WindowFlags.NoScrollbar)
                #config options go here
                PyImGui.spacing()
                PyImGui.text_colored("Widget Configuration", (1.0, 0.94, 0.75, 1.0))
                
                PyImGui.spacing()
                draw_floating_menu_config()
                
                PyImGui.spacing()
                draw_account_widget_config()

                PyImGui.spacing()
                PyImGui.separator()
                
                PyImGui.spacing()
                draw_quick_dock_config()

                PyImGui.spacing()
                PyImGui.separator()
                
                PyImGui.spacing()
                PyImGui.text("Previous Widget UI Settings")
                
                PyImGui.spacing()
                new_old_menu = PyImGui.checkbox("Disable Old Floating Menu" if state.old_menu else "Enable Old Floating Menu", state.old_menu)
                if new_old_menu != state.old_menu:
                    state.old_menu = new_old_menu
                    handler._write_setting("WidgetManager", "old_menu", str(state.old_menu), to_account=use_account_settings())
                PyImGui.show_tooltip("Disable Old Floating Menu" if state.old_menu else "Enable Old Floating Menu")
                
                PyImGui.spacing()              
                PyImGui.separator()
                
                PyImGui.spacing()
                
                draw_debug_config()
                
                PyImGui.dummy(0, 10)
                PyImGui.end_child()
            PyImGui.end()
            PyImGui.pop_style_var(1)
            PyImGui.pop_style_color(1)
        else:
            state.show_config_window = False