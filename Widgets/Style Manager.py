import Py4GW

from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import Timer
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import GameTextures
from Py4GWCoreLib import Style
from Py4GWCoreLib import IconsFontAwesome5

import os
import time

from Py4GWCoreLib.Py4GWcorelib import Utils
module_name = "Style Manager"

'''
Roadmap for those interested in contributing:
- Adding theme selection for the recently pushed Themes ('Guild Wars', 'Minimalus', 'ImGUI') [COMPLETED]
- Expand to support styling so users can select colors and values for various elements
    > Add a export / import feature for styles
'''
script_directory = os.path.dirname(os.path.abspath(__file__))
root_directory = os.path.normpath(os.path.join(script_directory, ".."))
ini_file_location = os.path.join(root_directory, "Widgets/Config/Style Manager.ini")
ini_handler = IniHandler(ini_file_location)


save_throttle_time = 1000
save_throttle_timer = Timer()
save_throttle_timer.Start()

game_throttle_time = 50
game_throttle_timer = Timer()
game_throttle_timer.Start()

window_x = ini_handler.read_int(module_name +str(" Config"), "x", 100)
window_y = ini_handler.read_int(module_name +str(" Config"), "y", 100)

window_width = ini_handler.read_int(module_name +str(" Config"), "width", 600)
window_height = ini_handler.read_int(module_name +str(" Config"), "height", 500)

window_collapsed = ini_handler.read_bool(module_name +str(" Config"), "collapsed", False)
window_open = ini_handler.read_bool(module_name +str(" Config"), "open", True)

window_module = ImGui.WindowModule(
    module_name, 
    window_name="Style Manager", 
    window_size=(window_width, window_height),
    window_flags=PyImGui.WindowFlags.NoFlag,
    collapse=window_collapsed,
    can_close=False
)

window_module.window_pos = (window_x, window_y)
window_module.open = window_open

py4_gw_ini_handler = IniHandler("Py4GW.ini")
selected_theme = Style.StyleTheme[py4_gw_ini_handler.read_key("settings", "style_theme", Style.StyleTheme.ImGui.name)]
themes = [theme.name.replace("_", " ") for theme in Style.StyleTheme]

ImGui.set_theme(Style.StyleTheme(selected_theme))
current_style : Style = ImGui.Styles.get(ImGui.Selected_Theme, Style())
org_style : Style = ImGui.Styles.get(ImGui.Selected_Theme, Style()).copy()

def themed_dropdown():
    pass

def configure():
    window_module.open = True        
    
def undo_button(label, width : float = 0, height: float = 25) -> bool:
    clicked = False
    remaining_space = PyImGui.get_content_region_avail()
    width = remaining_space[0] if width <= 0 else width
    height = remaining_space[1] - 1 if height <= 0 else height

    match(ImGui.Selected_Theme):
        case Style.StyleTheme.Guild_Wars:
            ImGui.push_font("Regular", 9)
            x,y = PyImGui.get_cursor_screen_pos()
            display_label = label.split("##")[0]

            button_rect = (x, y, width, height)
            
            GameTextures.Button.value.draw_in_drawlist(
                button_rect[0], 
                button_rect[1],
                (button_rect[2], button_rect[3]),
                tint=(255, 255, 255, 255) if ImGui.is_mouse_in_rect(button_rect) else (200, 200, 200, 255),
            )
            
            text_size = PyImGui.calc_text_size(display_label)
            text_x = x + ((width - text_size[0] + 1) / 2)
            text_y = y + ((height - text_size[1] - 2) / 2)

            PyImGui.push_clip_rect(
                button_rect[0] + 1,
                button_rect[1] - 2,
                button_rect[2] - 2,
                button_rect[3] - 4,
                False
            )

            PyImGui.draw_list_add_text(
                text_x,
                text_y,
                Utils.RGBToColor(255, 255, 255, 255),
                display_label,
            )

            PyImGui.pop_clip_rect()

            PyImGui.set_cursor_screen_pos(x, y)
            clicked = PyImGui.invisible_button(label, width, height)
            ImGui.pop_font()

        case Style.StyleTheme.Minimalus:
            clicked = PyImGui.button(label, width, height)
        
        case Style.StyleTheme.ImGui:
            clicked = PyImGui.button(label, width, height)

    return clicked

def DrawWindow():
    global window_module, module_name, ini_handler, window_x, window_y, window_collapsed, window_open, current_style, org_style, window_width, window_height
    global game_throttle_time, game_throttle_timer, save_throttle_time, save_throttle_timer
    
    try:                
        if not window_module.open:
            return
                
        if window_module.begin():
            PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() + 5)
            PyImGui.text("Selected Theme")
            PyImGui.same_line(0, 5)
            PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 5)
            remaining = PyImGui.get_content_region_avail()
            PyImGui.push_item_width(remaining[0])
            value = PyImGui.combo("##theme_selector", ImGui.Selected_Theme.value, themes)
            
            if value != ImGui.Selected_Theme.value:
                theme = Style.StyleTheme(value)
                ImGui.set_theme(theme)
                current_style = ImGui.Styles.get(theme, Style())
                org_style = current_style.copy()
                py4_gw_ini_handler.write_key("settings", "style_theme", ImGui.Selected_Theme.name)
                
                
            PyImGui.spacing()
            PyImGui.separator()
            PyImGui.spacing()

            PyImGui.begin_child("Style Customization")
            
            
            if current_style:
                remaining = PyImGui.get_content_region_avail()
                button_width = (remaining[0] - 5) / 2
                
                any_changed = any(var != org_style.StyleVars[enum] for enum, var in current_style.StyleVars.items())
                any_changed |= any(col != org_style.Colors[enum] for enum, col in current_style.Colors.items())
                
                if ImGui.themed_button("Save Changes", button_width, active=any_changed):
                    current_style.save_to_json(ImGui.Selected_Theme)
                    org_style = current_style.copy()
                
                PyImGui.same_line(0, 5)

                if ImGui.themed_button("Reset to Default", button_width, active=any_changed):
                    current_style.delete(ImGui.Selected_Theme)
                    ImGui.set_theme(ImGui.Selected_Theme)
                    
                    current_style = Style.load_default_from_json(ImGui.Selected_Theme)
                    org_style = current_style.copy()

                ImGui.show_tooltip("Delete the current style and replace it with the default style for the theme.")

                PyImGui.spacing()

                if PyImGui.is_rect_visible(50, 50):
                    column_width = 0
                    item_width = 0

                    if PyImGui.begin_table("Style Variables", 3, PyImGui.TableFlags.ScrollY):
                        PyImGui.table_setup_column("Variable", PyImGui.TableColumnFlags.WidthFixed, 150)
                        PyImGui.table_setup_column("Value", PyImGui.TableColumnFlags.WidthStretch)
                        PyImGui.table_setup_column("Undo", PyImGui.TableColumnFlags.WidthFixed, 35)

                        PyImGui.table_next_row()
                        PyImGui.table_next_column()
                            
                        for enum, var in current_style.StyleVars.items():
                            PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() + 5)
                            PyImGui.text(f"{enum.name}")
                            PyImGui.table_next_column()

                            column_width = column_width or PyImGui.get_content_region_avail()[0]
                            item_width = item_width or (column_width - 5) / 2
                            PyImGui.push_item_width(item_width)
                            var.value1 = PyImGui.input_float(f"##{enum.name}_value1", var.value1)
                            
                            if var.value2 is not None:
                                PyImGui.same_line(0, 5)
                                
                                PyImGui.push_item_width(item_width)
                                var.value2 = PyImGui.input_float(f"##{enum.name}_value2", var.value2)
                                
                            PyImGui.table_next_column()

                            changed = org_style.StyleVars[enum].value1 != var.value1 or org_style.StyleVars[enum].value2 != var.value2

                            if changed:
                                if undo_button(f"{IconsFontAwesome5.ICON_UNDO}##{enum.name}_undo", 30):
                                    var.value1 = org_style.StyleVars[enum].value1
                                    var.value2 = org_style.StyleVars[enum].value2

                            PyImGui.table_next_column()
                            
                        for enum, col in current_style.Colors.items():
                            PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() + 5)
                            PyImGui.text(f"{enum.name}")
                            PyImGui.table_next_column()

                            column_width = column_width or PyImGui.get_content_region_avail()[0]

                            PyImGui.push_item_width(column_width)
                            color_tuple = PyImGui.color_edit4(f"##{enum.name}_color", col.color_tuple)
                            if color_tuple != col.color_tuple:
                                col.set_tuple_color(color_tuple)    
                                
                            PyImGui.table_next_column()

                            changed = col.color_int != org_style.Colors[enum].color_int

                            if changed:
                                if undo_button(f"{IconsFontAwesome5.ICON_UNDO}##{enum.name}_undo", 30):
                                    col.color_tuple = org_style.Colors[enum].color_tuple
                            PyImGui.table_next_column()

                        PyImGui.end_table()

            PyImGui.end_child()
            window_module.process_window()
            
        window_module.end()

        if save_throttle_timer.HasElapsed(save_throttle_time):
            if window_module.window_pos[0] != window_module.end_pos[0] or window_module.window_pos[1] != window_module.end_pos[1]:
                window_module.window_pos = window_module.end_pos
                ini_handler.write_key(module_name + " Config", "x", str(int(window_module.window_pos[0])))
                ini_handler.write_key(module_name + " Config", "y", str(int(window_module.window_pos[1])))

            if window_width != window_module.window_size[0] or window_height != window_module.window_size[1]:
                ini_handler.write_key(module_name + " Config", "width", str(int(window_module.window_size[0])))
                ini_handler.write_key(module_name + " Config", "height", str(int(window_module.window_size[1])))
                window_width, window_height = window_module.window_size

            if window_module.collapsed_status != window_module.collapse:
                window_module.collapse = window_module.collapsed_status
                ini_handler.write_key(module_name + " Config", "collapsed", str(window_module.collapse))

            if window_open != window_module.open:
                window_open = window_module.open
                ini_handler.write_key(module_name + " Config", "open", str(window_module.open))
                
            save_throttle_timer.Reset()


    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Debug)


def main():
    """Required main function for the widget"""
    global game_throttle_timer, game_throttle_time, window_module
    
    try:            
        DrawWindow()
        window_module.open  = False
            
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in main: {str(e)}", Py4GW.Console.MessageType.Debug)
        return False
    return True

# These functions need to be available at module level
__all__ = ['main', 'configure']

if __name__ == "__main__":
    main()
