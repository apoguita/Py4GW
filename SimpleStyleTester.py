# Reload imports
import importlib
import os

import PyImGui

from Py4GWCoreLib import IconsFontAwesome5, ImGui, Routines
from Py4GWCoreLib.ImGui import Style
from Py4GWCoreLib.ImGui_src.types import StyleTheme
from Py4GWCoreLib.py4gwcorelib_src.IniHandler import IniHandler

MODULE_NAME = "SimpleStyleTester"

py4_gw_ini_handler = IniHandler("Py4GW.ini")
ImGui.set_theme(Style.StyleTheme[py4_gw_ini_handler.read_key("settings", "style_theme", StyleTheme.ImGui.name)])
org_style : Style.Style = ImGui.Selected_Style.copy()

def draw_ui():
    global org_style
    
    imgui_style = ImGui.get_style()
    imgui_style.apply_to_style_config()

    PyImGui.set_next_window_size((600, 400), PyImGui.ImGuiCond.Once)
    if PyImGui.begin("Style Editor"):
        remaining = PyImGui.get_content_region_avail()
        button_width = (remaining[0] - 10) / 2
        any_changed = False

        for k, col in imgui_style.Colors.items():            
            org_color = org_style.Colors.get(k, None)
            if org_color and col.color_int != org_color.color_int:
                any_changed = True
                break

        PyImGui.begin_disabled(not any_changed)
        if PyImGui.button("Save Changes", button_width):
            ImGui.Selected_Style.save_to_json()
            org_style = ImGui.Selected_Style.copy()
        
        PyImGui.end_disabled()
        PyImGui.same_line(0, 5)

        if PyImGui.button("Reset to Default", button_width):
            theme = ImGui.Selected_Style.Theme
            ImGui.Selected_Style.delete()
            ImGui.reload_theme(theme)
            org_style = ImGui.Selected_Style.copy()
            
        
        column_width = 0
        if PyImGui.is_rect_visible(0, 10):
            if PyImGui.begin_table("Style Variables", 3, PyImGui.TableFlags.ScrollY):
                PyImGui.table_setup_column("Variable", PyImGui.TableColumnFlags.WidthFixed, 150)
                PyImGui.table_setup_column("Value", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Undo", PyImGui.TableColumnFlags.WidthFixed, 35)

                PyImGui.table_next_row()
                PyImGui.table_next_column()
                   
                        
                for col_name, col in imgui_style.Colors.items():
                    PyImGui.text(col_name)
                    PyImGui.table_next_column()                                         

                    column_width = column_width or PyImGui.get_content_region_avail()[0]
                    PyImGui.push_item_width(column_width)
                                    
                    new_color = PyImGui.color_edit4(col_name, col.color_tuple)
                    if new_color:
                        col.set_tuple_color(new_color)
                    
                    PyImGui.pop_item_width()
                    PyImGui.table_next_column()
                    
                    org_color = org_style.Colors.get(col_name, None)
                    show_button = org_color is not None and (col.color_int != org_color.color_int)
                    
                    if show_button and col_name and org_style.Colors[col_name]:
                        if PyImGui.button(IconsFontAwesome5.ICON_UNDO + "##" + col_name, 25, 25):
                            col.set_rgba(*org_style.Colors[col_name].rgb_tuple)
                        
                    PyImGui.table_next_column()
                PyImGui.end_table()
                
    PyImGui.end()
    pass

def configure():
    pass


def main():                
    draw_ui()
                
        

__all__ = ['main', 'configure']

