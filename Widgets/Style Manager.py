# Reload imports
import importlib
import os
from typing import Optional

import Py4GW
import PyImGui

from Py4GWCoreLib import IconsFontAwesome5, ImGui, Routines
from Py4GWCoreLib.ImGui import Style
from Py4GWCoreLib.ImGui_src.types import StyleTheme
from Py4GWCoreLib.py4gwcorelib_src.IniHandler import IniHandler
from Py4GWCoreLib import Timer
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer

MODULE_NAME = "Style Manager"

script_directory = os.path.dirname(os.path.abspath(__file__))
root_directory = os.path.normpath(os.path.join(script_directory, ".."))
ini_file_location = os.path.join(
    root_directory, "Widgets/Config/Style Manager.ini")
ini_handler = IniHandler(ini_file_location)


save_throttle_time = 1000
save_throttle_timer = Timer()
save_throttle_timer.Start()

game_throttle_time = 50
game_throttle_timer = Timer()
game_throttle_timer.Start()

window_x = ini_handler.read_int(MODULE_NAME + str(" Config"), "x", 100)
window_y = ini_handler.read_int(MODULE_NAME + str(" Config"), "y", 100)

window_width = ini_handler.read_int(MODULE_NAME + str(" Config"), "width", 600)
window_height = ini_handler.read_int(
    MODULE_NAME + str(" Config"), "height", 500)

window_collapsed = ini_handler.read_bool(
    MODULE_NAME + str(" Config"), "collapsed", False)

window_module = ImGui.WindowModule(
    MODULE_NAME,
    window_name="Style Manager",
    window_size=(window_width, window_height),
    window_flags=PyImGui.WindowFlags.NoFlag,
    collapse=window_collapsed,
)

window_module.window_pos = (window_x, window_y)

py4_gw_ini_handler = IniHandler("Py4GW.ini")
selected_theme = Style.StyleTheme[py4_gw_ini_handler.read_key(
    "settings", "style_theme", Style.StyleTheme.ImGui.name)]
themes = [theme.name.replace("_", " ") for theme in Style.StyleTheme]

ImGui.reload_theme(Style.StyleTheme(selected_theme))
ImGui.set_theme(selected_theme)
# ImGui.Selected_Style : Style = ImGui.Styles.get(ImGui.Selected_Theme, Style())
org_style: Style.Style = ImGui.Selected_Style.copy()

# TODO: Fix collapsing UIs that are not gw themed
# TODO: Remove style pushing on a window level

mouse_down_timer = ThrottledTimer(125)
input_int_value = 150
input_float_value = 150.0
input_text_value = "Text"
search_value = ""
window_open = False
control_compare = False
theme_compare = False

def DrawControlCompare():
    pass

def DrawThemeCompare():
    pass

def DrawWindow():
    global org_style, theme_compare, control_compare

    PyImGui.set_next_window_size((600, 400), PyImGui.ImGuiCond.Once)
    if window_module.begin():
        remaining = PyImGui.get_content_region_avail()
        button_width = (remaining[0] - 10) / 2

        PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() + 5)
        PyImGui.text("Selected Theme")
        PyImGui.same_line(0, 5)
        PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 5)
        remaining = PyImGui.get_content_region_avail()
        PyImGui.push_item_width(remaining[0] - 30)
        value = PyImGui.combo("##theme_selector",
                              ImGui.Selected_Style.Theme.value, themes)

        if value != ImGui.Selected_Style.Theme.value:
            theme = Style.StyleTheme(value)
            ImGui.reload_theme(theme)
            ImGui.set_theme(theme)

            org_style = ImGui.Selected_Style.copy()
            py4_gw_ini_handler.write_key(
                "settings", "style_theme", ImGui.Selected_Style.Theme.name)

        PyImGui.same_line(0, 5)
        PyImGui.begin_disabled(True)
        PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 5)
        theme_compare = PyImGui.checkbox(
            "##show_theme_compare", theme_compare)
        ImGui.show_tooltip(
            "Show Theme Compare window\nCurrently disabled.")
        PyImGui.end_disabled()

        PyImGui.spacing()
        PyImGui.separator()
        PyImGui.spacing()

        any_changed = False

        for k, col in ImGui.Selected_Style.Colors.items():
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

        PyImGui.spacing()
        PyImGui.separator()
        PyImGui.spacing()

        column_width = 0
        item_width = 0

        def table_separator_header(title: str, font_size: int = 20, font_family: str = "Regular", color: Optional[tuple] = None, tooltip: Optional[str] = None):
            PyImGui.spacing()
            PyImGui.spacing()
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            color = color or ImGui.Selected_Style.TextCollapsingHeader.color_tuple

            if color:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, color)

            ImGui.push_font(font_family, font_size)
            PyImGui.text(title)

            if tooltip:
                ImGui.show_tooltip(tooltip)

            ImGui.pop_font()

            if color:
                PyImGui.pop_style_color(1)

            PyImGui.table_next_row()
            for _ in range(4):
                PyImGui.separator()
                PyImGui.table_next_column()

        def table_collapsing_header(title: str, font_size: int = 20, font_family: str = "Regular", color: Optional[tuple] = None, tooltip: Optional[str] = None):
            PyImGui.spacing()
            PyImGui.spacing()
            PyImGui.table_next_row()
            PyImGui.table_next_column()

            if color:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, color)

            ImGui.push_font(font_family, font_size)
            open = PyImGui.collapsing_header(title)

            if tooltip:
                ImGui.show_tooltip(tooltip)

            ImGui.pop_font()

            if color:
                PyImGui.pop_style_color(1)

            PyImGui.table_next_row()
            for _ in range(4):
                PyImGui.separator()
                PyImGui.table_next_column()

            return open

        if PyImGui.begin_tab_bar("Style Customization"):
            if PyImGui.begin_tab_item("Style Customization"):

                if PyImGui.is_rect_visible(0, 10):
                    if PyImGui.begin_table("Style Variables", 3, PyImGui.TableFlags.ScrollY):
                        PyImGui.table_setup_column(
                            "Variable", PyImGui.TableColumnFlags.WidthFixed, 250)
                        PyImGui.table_setup_column(
                            "Value", PyImGui.TableColumnFlags.WidthStretch)
                        PyImGui.table_setup_column(
                            "Undo", PyImGui.TableColumnFlags.WidthFixed, 35)

                        PyImGui.table_next_row()
                        PyImGui.table_next_column()
                        table_separator_header("Control Colors")

                        for col_name, col in ImGui.Selected_Style.Colors.items():
                            PyImGui.text(col_name)
                            PyImGui.table_next_column()

                            column_width = column_width or PyImGui.get_content_region_avail()[
                                0]
                            PyImGui.push_item_width(column_width)

                            new_color = PyImGui.color_edit4(
                                col_name, col.color_tuple)
                            if new_color:
                                col.set_tuple_color(new_color)

                            PyImGui.pop_item_width()
                            PyImGui.table_next_column()

                            org_color = org_style.Colors.get(col_name, None)
                            show_button = org_color is not None and (
                                col.color_int != org_color.color_int)

                            if show_button and col_name and org_style.Colors[col_name]:
                                if PyImGui.button(IconsFontAwesome5.ICON_UNDO + "##" + col_name, 25, 25):
                                    col.set_rgba(
                                        *org_style.Colors[col_name].rgb_tuple)

                            PyImGui.table_next_column()

                        PyImGui.begin_disabled(True)
                        open = table_collapsing_header("Style Vars", tooltip="Currently disabled.", font_family="Italic") and False

                        if open:
                            for enum, var in ImGui.Selected_Style.StyleVars.items():
                                PyImGui.set_cursor_pos_y(
                                    PyImGui.get_cursor_pos_y() + 5)
                                PyImGui.text(f"{enum}")
                                PyImGui.table_next_column()

                                column_width = column_width or PyImGui.get_content_region_avail()[
                                    0]
                                item_width = item_width or (
                                    column_width - 5) / 2
                                PyImGui.push_item_width(item_width)
                                var.value1 = PyImGui.input_float(
                                    f"##{enum}_value1", var.value1)

                                if var.value2 is not None:
                                    PyImGui.same_line(0, 5)

                                    PyImGui.push_item_width(item_width)
                                    var.value2 = PyImGui.input_float(
                                        f"##{enum}_value2", var.value2)

                                PyImGui.table_next_column()

                                changed = org_style.StyleVars[
                                    enum].value1 != var.value1 or org_style.StyleVars[enum].value2 != var.value2

                                if changed:
                                    if PyImGui.button(f"{IconsFontAwesome5.ICON_UNDO}##{enum}_undo", 30):
                                        var.value1 = org_style.StyleVars[enum].value1
                                        var.value2 = org_style.StyleVars[enum].value2

                                PyImGui.table_next_column()

                        open = table_collapsing_header("Custom Colors", tooltip="Currently disabled.", font_family="Italic") and False

                        if open:
                            for col_name, col in ImGui.Selected_Style.CustomColors.items():
                                PyImGui.text(col_name)
                                PyImGui.table_next_column()

                                column_width = column_width or PyImGui.get_content_region_avail()[
                                    0]
                                PyImGui.push_item_width(column_width)

                                new_color = PyImGui.color_edit4(
                                    col_name, col.color_tuple)
                                if new_color:
                                    col.set_tuple_color(new_color)

                                PyImGui.pop_item_width()
                                PyImGui.table_next_column()

                                org_color = org_style.Colors.get(
                                    col_name, None)
                                show_button = org_color is not None and (
                                    col.color_int != org_color.color_int)

                                if show_button and col_name and org_style.Colors[col_name]:
                                    if PyImGui.button(IconsFontAwesome5.ICON_UNDO + "##" + col_name, 25, 25):
                                        col.set_rgba(
                                            *org_style.Colors[col_name].rgb_tuple)

                                PyImGui.table_next_column()

                        open = table_collapsing_header("Texture Colors", tooltip="Currently disabled.", font_family="Italic") and False

                        if open:
                            for col_name, col in ImGui.Selected_Style.TextureColors.items():
                                PyImGui.text(col_name)
                                PyImGui.table_next_column()

                                column_width = column_width or PyImGui.get_content_region_avail()[
                                    0]
                                PyImGui.push_item_width(column_width)

                                new_color = PyImGui.color_edit4(
                                    col_name, col.color_tuple)
                                if new_color:
                                    col.set_tuple_color(new_color)

                                PyImGui.pop_item_width()
                                PyImGui.table_next_column()

                                org_color = org_style.Colors.get(
                                    col_name, None)
                                show_button = org_color is not None and (
                                    col.color_int != org_color.color_int)

                                if show_button and col_name and org_style.Colors[col_name]:
                                    if PyImGui.button(IconsFontAwesome5.ICON_UNDO + "##" + col_name, 25, 25):
                                        col.set_rgba(
                                            *org_style.Colors[col_name].rgb_tuple)

                                PyImGui.table_next_column()

                        PyImGui.end_disabled()
                        PyImGui.end_table()

                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Control Preview"):
                
                PyImGui.begin_disabled(True)
                ImGui.push_font("Regular", 18)
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1, 0, 0, 1))
                PyImGui.spacing()
                PyImGui.spacing()
                PyImGui.spacing()
                PyImGui.indent(10)
                PyImGui.text("Coming soon ...")
                PyImGui.pop_style_color(1)
                ImGui.pop_font()
                PyImGui.end_disabled()
                
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("How to Use"):
                
                PyImGui.begin_disabled(True)
                ImGui.push_font("Regular", 18)
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1, 0, 0, 1))
                PyImGui.spacing()
                PyImGui.spacing()
                PyImGui.spacing()
                PyImGui.indent(10)
                PyImGui.text("Coming soon ...")
                PyImGui.pop_style_color(1)
                ImGui.pop_font()
                PyImGui.end_disabled()
                
                PyImGui.end_tab_item()

            PyImGui.end_tab_bar()

    window_module.end()

    if control_compare:
        DrawControlCompare()

    if theme_compare:
        DrawThemeCompare()

    pass


def configure():
    global window_open
    window_open = True


def main():
    """Required main function for the widget"""
    global game_throttle_timer, game_throttle_time, window_module, window_open

    try:
        if window_open:
            DrawWindow()

        window_open = False

    except Exception as e:
        Py4GW.Console.Log(
            MODULE_NAME, f"Error in main: {str(e)}", Py4GW.Console.MessageType.Debug)
        return False
    return True


__all__ = ['main', 'configure']
