from enum import Enum
import math
from pathlib import Path
from types import FunctionType
from typing import Optional, overload
from unittest import case
import Py4GW
import PyImGui

from Py4GWCoreLib import IniHandler, Overlay
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import Timer
from Py4GWCoreLib import SplitTexture
from Py4GWCoreLib import MapTexture
from Py4GWCoreLib import TextureState
from Py4GWCoreLib import Style
from Py4GWCoreLib import ControlAppearance
from Py4GWCoreLib import IconsFontAwesome5

import os
import time

from Py4GWCoreLib.Py4GWcorelib import ConsoleLog, ThrottledTimer, Utils
module_name = "Style Manager"

'''
Roadmap for those interested in contributing:
- Adding theme selection for the recently pushed Themes ('Guild Wars', 'Minimalus', 'ImGUI') [COMPLETED]
- Expand to support styling so users can select colors and values for various elements
    > Add a export / import feature for styles
'''

TEXTURE_FOLDER = "Textures\\Game UI\\"
MINIMALUS_FOLDER = "Textures\\Themes\\Minimalus\\"


class ImGuiDev:
    pass


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

window_x = ini_handler.read_int(module_name + str(" Config"), "x", 100)
window_y = ini_handler.read_int(module_name + str(" Config"), "y", 100)

window_width = ini_handler.read_int(module_name + str(" Config"), "width", 600)
window_height = ini_handler.read_int(
    module_name + str(" Config"), "height", 500)

window_collapsed = ini_handler.read_bool(
    module_name + str(" Config"), "collapsed", False)

window_module = ImGui.WindowModule(
    module_name,
    window_name="Style Manager",
    window_size=(window_width, window_height),
    window_flags=PyImGui.WindowFlags.NoFlag,
    collapse=window_collapsed,
    can_close=False
)

window_module.window_pos = (window_x, window_y)
window_module.open = False
control_compare = False
theme_compare = False
match_style_vars = False

py4_gw_ini_handler = IniHandler("Py4GW.ini")
selected_theme = Style.StyleTheme[py4_gw_ini_handler.read_key(
    "settings", "style_theme", Style.StyleTheme.ImGui.name)]
themes = [theme.name.replace("_", " ") for theme in Style.StyleTheme]

ImGui.reload_theme(Style.StyleTheme(selected_theme))
ImGui.set_theme(selected_theme)

org_style: Style = ImGui.Selected_Style.copy()

# TODO: Fix collapsing UIs that are not gw themed
# TODO: Remove style pushing on a window level

mouse_down_timer = ThrottledTimer(125)
input_int_value = 150
input_float_value = 150.0
input_text_value = "Text"
search_value = ""


class preview_states:
    def __init__(self):
        self.input_int_value = 150
        self.input_float_value = 150.0
        self.input_text_value = "Text"
        self.search_value = ""
        self.combo = 0
        self.toggle_button_1 = True
        self.toggle_button_2 = False
        self.toggle_button_3 = False
        self.toggle_button_4 = False
        self.image_toggle_button_1 = True
        self.image_toggle_button_2 = False
        self.image_toggle_button_3 = False
        self.image_toggle_button_4 = False
        self.objective_1 = True
        self.objective_2 = False
        self.checkbox = True
        self.checkbox_2 = False
        self.radio_button = 0
        self.slider_int = 25
        self.slider_float = 33.0


preview = preview_states()

def configure():
    window_module.open = True


textures = [
    ("Textures/Item Models/[17081] - Battle Commendation.png",
     ControlAppearance.Default, True),
    ("Textures/Item Models/[514] - Molten Heart.png",
     ControlAppearance.Primary, True),
    ("Textures/Item Models/[35] - Bag.png", ControlAppearance.Danger, True),
    ("Textures/Item Models/[30855] - Bottle of Grog.png",
     ControlAppearance.Default, False),
]


def draw_button(theme: Style.StyleTheme):

    if ImGui.button("Default" + "##" + theme.name):
        ConsoleLog(module_name, "Button clicked")
    PyImGui.same_line(0, 5)
    ImGui.button("Primary" + "##" + theme.name,
                 appearance=ControlAppearance.Primary)
    PyImGui.same_line(0, 5)
    ImGui.button("Danger" + "##" + theme.name,
                 appearance=ControlAppearance.Danger)
    PyImGui.same_line(0, 5)
    ImGui.button("Disabled" + "##" + theme.name, enabled=False)


def draw_small_button(theme: Style.StyleTheme):
    if ImGui.small_button("Default" + "##" + theme.name):
        ConsoleLog(module_name, "Small Button clicked")
    PyImGui.same_line(0, 5)
    ImGui.small_button("Primary" + "##" + theme.name,
                       appearance=ControlAppearance.Primary)
    PyImGui.same_line(0, 5)
    ImGui.small_button("Danger" + "##" + theme.name,
                       appearance=ControlAppearance.Danger)
    PyImGui.same_line(0, 5)
    ImGui.small_button("Disabled" + "##" + theme.name, enabled=False)


def draw_icon_button(theme: Style.StyleTheme):
    if ImGui.icon_button(IconsFontAwesome5.ICON_SYNC + " With Text" + "##" + theme.name):
        ConsoleLog(module_name, "Icon Button clicked")
    PyImGui.same_line(0, 5)
    ImGui.icon_button(IconsFontAwesome5.ICON_SYNC + "##" + theme.name)
    PyImGui.same_line(0, 5)
    ImGui.icon_button(IconsFontAwesome5.ICON_SYNC + "##" +
                      theme.name, appearance=ControlAppearance.Primary)
    PyImGui.same_line(0, 5)
    ImGui.icon_button(IconsFontAwesome5.ICON_SYNC + "##" +
                      theme.name, appearance=ControlAppearance.Danger)
    PyImGui.same_line(0, 5)
    ImGui.icon_button(
        IconsFontAwesome5.ICON_SYNC, enabled=False)


def draw_toggle_button(theme: Style.StyleTheme):
    preview.toggle_button_1 = ImGui.toggle_button(
        ("On" if preview.toggle_button_1 else "Off") + "##Toggle" + theme.name, preview.toggle_button_1)
    PyImGui.same_line(0, 5)
    preview.toggle_button_2 = ImGui.toggle_button(
        ("On" if preview.toggle_button_2 else "Off") + "##Toggle2" + theme.name, preview.toggle_button_2)
    PyImGui.same_line(0, 5)
    preview.toggle_button_3 = ImGui.toggle_button(
        "Disabled" + "##Toggle3" + theme.name, preview.toggle_button_3, enabled=False)


def draw_image_toggle(theme: Style.StyleTheme):
    preview.image_toggle_button_1 = ImGui.image_toggle_button(
        ("On" if preview.image_toggle_button_1 else "Off") + "##ImageToggle_1" + theme.name, textures[0][0], preview.image_toggle_button_1)
    PyImGui.same_line(0, 5)
    preview.image_toggle_button_2 = ImGui.image_toggle_button(
        ("On" if preview.image_toggle_button_2 else "Off") + "##ImageToggle_2" + theme.name, textures[1][0], preview.image_toggle_button_2)
    PyImGui.same_line(0, 5)
    preview.image_toggle_button_3 = ImGui.image_toggle_button(
        ("On" if preview.image_toggle_button_3 else "Off") + "##ImageToggle_3" + theme.name, textures[2][0], preview.image_toggle_button_3, enabled=False)


def draw_image_button(theme: Style.StyleTheme):
    for (texture, appearance, enabled) in textures:
        ImGui.image_button("Image Button" + "##" + theme.name +
                           texture, texture, appearance=appearance, enabled=enabled)
        PyImGui.same_line(0, 5)


def draw_combo(theme: Style.StyleTheme):
    preview.combo = ImGui.combo("Combo##" + theme.name, preview.combo, [
                                "Option 1", "Option 2", "Option 3"])


def draw_checkbox(theme: Style.StyleTheme):
    preview.checkbox_2 = ImGui.checkbox(
        "##Checkbox 2" + "##" + theme.name, preview.checkbox_2)
    PyImGui.same_line(0, 5)
    preview.checkbox = ImGui.checkbox(
        "Checkbox" + "##" + theme.name, preview.checkbox)


def draw_radio_button(theme: Style.StyleTheme):
    preview.radio_button = ImGui.radio_button(
        "Option 1##Radio Button 1" + "##" + theme.name, preview.radio_button, 0)
    preview.radio_button = ImGui.radio_button(
        "Option 2##Radio Button 2" + "##" + theme.name, preview.radio_button, 1)
    preview.radio_button = ImGui.radio_button(
        "Option 3##Radio Button 3" + "##" + theme.name, preview.radio_button, 2)


def draw_slider(theme: Style.StyleTheme):
    preview.slider_int = ImGui.slider_int(
        "Slider Int##" + theme.name, preview.slider_int, 0, 100)
    preview.slider_float = ImGui.slider_float(
        "Slider Float##" + theme.name, preview.slider_float, 0.0, 100.0)


def draw_input(theme: Style.StyleTheme):
    changed, preview.search_value = ImGui.search_field(
        "Search##" + theme.name, preview.search_value)
    preview.input_text_value = ImGui.input_text(
        "Text##" + theme.name, preview.input_text_value)
    preview.input_float_value = ImGui.input_float(
        "Float##" + theme.name, preview.input_float_value)
    preview.input_int_value = ImGui.input_int(
        "Int##3" + theme.name, preview.input_int_value, 0, 10000, 0)
    preview.input_int_value = ImGui.input_int(
        "Int Buttons##2" + theme.name, preview.input_int_value)


def draw_separator(theme: Style.StyleTheme):
    ImGui.separator()


def draw_progress_bar(theme: Style.StyleTheme):
    ImGui.progress_bar(0.25, 0, 20, "25 points")


def draw_text(theme: Style.StyleTheme):
    ImGui.text("This is some text.")


def draw_hyperlink(theme: Style.StyleTheme):
    ImGui.hyperlink("Click Me")


def draw_bullet_text(theme: Style.StyleTheme):
    ImGui.bullet_text("Bullet Text 1")
    ImGui.bullet_text("Bullet Text 2")


def draw_objective_text(theme: Style.StyleTheme):
    preview.objective_1 = ImGui.objective_text(
        "Objective 1", preview.objective_1)
    preview.objective_2 = ImGui.objective_text(
        "Objective 2", preview.objective_2)


def draw_tree_node(theme: Style.StyleTheme):
    if ImGui.tree_node("Tree Node 1##" + theme.name):
        if ImGui.tree_node("Tree Node 1.1##" + theme.name):
            ImGui.text("This is a tree node content.")
            ImGui.tree_pop()

        ImGui.tree_pop()


def draw_collapsing_header(theme: Style.StyleTheme):
    if ImGui.collapsing_header("Collapsing Header##" + theme.name, 0):
        ImGui.text("This is a collapsible header content.")


def draw_child(theme: Style.StyleTheme):
    if ImGui.begin_child("Child##" + theme.name, (0, 68), True, PyImGui.WindowFlags.AlwaysHorizontalScrollbar):
        ImGui.text("This is a child content.")
        ImGui.text("This is a child content.")
        ImGui.text("This is a child content.")
        ImGui.text("This is a child content.")
        ImGui.text("This is a child content.")
    ImGui.end_child()


def draw_tab_bar(theme: Style.StyleTheme):
    if ImGui.begin_tab_bar("Tab Bar PyImGui##" + theme.name):
        if ImGui.begin_tab_item("Tab 1##" + theme.name):
            ImGui.text("Content for Tab 1")
            PyImGui.end_tab_item()

        if ImGui.begin_tab_item("Tab 2##" + theme.name):
            ImGui.text("Content for Tab 2")
            PyImGui.end_tab_item()

        ImGui.end_tab_bar()


controls = {
    "Button": draw_button,
    "Small Button": draw_small_button,
    "Icon Button": draw_icon_button,
    "Toggle Button": draw_toggle_button,
    "Image Toggle Button": draw_image_toggle,
    "Image Button": draw_image_button,
    "Combo": draw_combo,
    "Checkbox": draw_checkbox,
    "Radio Button": draw_radio_button,
    "Slider": draw_slider,
    "Input": draw_input,
    "Separator": draw_separator,
    "Progress Bar": draw_progress_bar,
    "Text": draw_text,
    "Hyperlink": draw_hyperlink,
    "Bullet Text": draw_bullet_text,
    "Objective Text": draw_objective_text,
    "Tree Node": draw_tree_node,
    "Collapsing Header": draw_collapsing_header,
    "Child & Scrollbars": draw_child,
    "Tab Bar": draw_tab_bar,
}


def DrawThemeCompare():
    global match_style_vars

    if ImGui.begin("Theme Compare"):
        if PyImGui.is_rect_visible(50, 50):
            themes = [style for style in Style.StyleTheme]

            PyImGui.push_item_width(150)
            style = ImGui.get_style()

            # region Header
            PyImGui.push_style_var2(ImGui.ImGuiStyleVar.CellPadding, 4, 8)
            if ImGui.begin_table("Control Preview#Header", 4, PyImGui.TableFlags.BordersOuterH, 0, 30):
                PyImGui.table_setup_column(
                    "Control", PyImGui.TableColumnFlags.WidthFixed, 150)
                PyImGui.table_setup_column(
                    "ImGui", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column(
                    "Guild Wars", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column(
                    "Minimalus", PyImGui.TableColumnFlags.WidthStretch)

                PyImGui.table_next_row()
                PyImGui.table_next_column()

                checked = ImGui.checkbox("Match Style Vars", match_style_vars)
                if checked != match_style_vars:
                    match_style_vars = checked

                    for theme in themes:
                        ConsoleLog(
                            module_name, f"Reloading theme {theme.name} to match style vars")
                        ImGui.reload_theme(theme)

                if match_style_vars:
                    for theme in themes:
                        s = ImGui.Styles[theme]

                        for var_enum, var in s.StyleVars.items():
                            var.value1 = style.StyleVars[var_enum].value1
                            var.value2 = style.StyleVars[var_enum].value2

                PyImGui.table_next_column()

                ImGui.text("ImGui")
                PyImGui.table_next_column()

                ImGui.text("Guild Wars")
                PyImGui.table_next_column()

                ImGui.text("Minimalus")
                ImGui.end_table()
            PyImGui.pop_style_var(1)
            # endregion

            if ImGui.begin_table("Control Preview", len(themes) + 1, PyImGui.TableFlags.ScrollX | PyImGui.TableFlags.ScrollY):
                PyImGui.table_setup_column(
                    "Control", PyImGui.TableColumnFlags.WidthFixed, 150)
                PyImGui.table_setup_column(
                    "ImGui", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column(
                    "Guild Wars", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column(
                    "Minimalus", PyImGui.TableColumnFlags.WidthStretch)

                PyImGui.table_next_row()
                PyImGui.table_next_column()

                for control_name, control_draw_func in controls.items():
                    ImGui.text(control_name)
                    PyImGui.table_next_column()

                    for style in themes:
                        ImGui.push_theme(style)
                        control_draw_func(style)
                        PyImGui.table_next_column()
                        ImGui.pop_theme()

                ImGui.end_table()

            PyImGui.pop_item_width()
    ImGui.end()


def DrawControlCompare():
    if ImGui.begin("Control Compare"):
        if PyImGui.is_rect_visible(50, 50):

            PyImGui.push_item_width(150)
            style = ImGui.get_style()

            if ImGui.begin_table("Control Preview", 4, PyImGui.TableFlags.ScrollX):
                PyImGui.table_setup_column(
                    "ControlName", PyImGui.TableColumnFlags.WidthFixed, 150)
                PyImGui.table_setup_column(
                    "PyImgui", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column(
                    "ImGui", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column(
                    "ImGui Style Pushed", PyImGui.TableColumnFlags.WidthStretch)

                PyImGui.table_next_row()
                PyImGui.table_next_column()

                ImGui.text("Control")
                PyImGui.table_next_column()

                PyImGui.combo("##1", ImGui.Selected_Style.Theme.value, themes)
                ImGui.combo("##2", ImGui.Selected_Style.Theme.value, themes)
                ImGui.push_theme(Style.StyleTheme.Minimalus)
                ImGui.combo("##3", ImGui.Selected_Style.Theme.value, themes)
                ImGui.pop_theme()
                ImGui.combo("##4", ImGui.Selected_Style.Theme.value, themes)

                PyImGui.table_next_column()
                
                ImGui.button("Button")
                ImGui.button("Button")
                ImGui.push_theme(Style.StyleTheme.Minimalus)
                ImGui.button("Button")  
                ImGui.pop_theme()
                
                ImGui.end_table()
            PyImGui.pop_item_width()
    ImGui.end()


def theme_selector(style: Style, func: FunctionType, control_colors: list[str] = []) -> dict[str, Style.CustomColor | Style.StyleColor]:
    PyImGui.push_item_width(200)

    pushed_colors = {}

    value = ImGui.combo(f"Theme##theme_selector{func.__name__}",
                        style.Theme.value, themes)

    if value != style.Theme.value:
        control_styles[func.__name__] = Style.load_theme(
            Style.StyleTheme(value))

    for col_name in control_colors:
        col = style.Colors.get(col_name) or style.CustomColors.get(col_name)

        if not col:
            continue

        color_tuple = ImGui.color_edit4(
            f"{col.img_color_enum.name if col.img_color_enum else "color"}##{func.__name__}", col.color_tuple)

        if color_tuple != col.color_tuple:
            col.set_tuple_color(color_tuple)

        col.push_color()
        pushed_colors[col_name] = col

    PyImGui.pop_item_width()
    PyImGui.table_next_column()
    return pushed_colors


def display_code_with_copy(code):
    if ImGui.button("Copy Code"):
        PyImGui.set_clipboard_text(code)

    ImGui.show_tooltip(code)
    PyImGui.table_next_column()


def format_arg(arg):
    if isinstance(arg, str):
        return f'"{arg}"'   # wrap in quotes
    return str(arg)


def get_code(func: FunctionType, *args, control_colors: list[str] = []) -> str:
    og_style = ImGui.get_style()

    if func.__name__ not in control_styles:
        control_styles[func.__name__] = og_style.copy()

    style = control_styles[func.__name__]
    pushed_colors = theme_selector(style, func, control_colors)

    ImGui.Selected_Style = style
    func.__call__(*args)  # Call the function to render the control
    ImGui.Selected_Style = org_style

    for _, col in pushed_colors.items():
        col.pop_color()

    PyImGui.table_next_column()

    code = f"def draw_custom_{func.__name__.lower()}():\n"
    code += f"\t##Only if you need a different theme than current\n"
    code += f"\tImGui.push_theme(Style.StyleTheme.{control_styles[func.__name__].Theme.name})"
    code += f"\n\tstyle = ImGui.get_style()\n"

    for col_name, col in pushed_colors.items():
        r, g, b, a = col.rgb_tuple
        code += f"\tstyle.{col_name}.push_color(({r}, {g}, {b}, {a}))\n"

    code += f"\n\tImGui.{func.__name__}({', '.join(format_arg(a) for a in args)})\n\n"

    for col_name, col in pushed_colors.items():
        code += f"\tstyle.{col_name}.pop_color()\n"

    return code


def customizing_control(func: FunctionType, *args, control_colors: list[str] = []):
    code = get_code(func, *args, control_colors=control_colors)

    display_code_with_copy(code)


control_styles: dict[str, Style] = {}
use_controls = {
    "Button": lambda: customizing_control(ImGui.button, "Button", 100, control_colors=["Button", "ButtonHovered", "ButtonActive"]),
    "Small Button": lambda: customizing_control(ImGui.small_button, "Small Button", control_colors=["Button", "ButtonHovered", "ButtonActive"]),
    "Progress Bar": lambda: customizing_control(ImGui.progress_bar, 0.5, 150, 20, "50% Progress", control_colors=["PlotHistogram"]),
    "Text": lambda: customizing_control(ImGui.text, "This is some text.", control_colors=["Text"]),
    "Bullet Text": lambda: customizing_control(ImGui.bullet_text, "Bullet Text", control_colors=["Text"]),
    "Tree Node": lambda: customizing_control(ImGui.tree_node, "Tree Node", control_colors=["TextTreeNode"]),
}


def DrawUsageTab():
    if PyImGui.is_rect_visible(50, 50):
        # region Header
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.CellPadding, 4, 8)
        if ImGui.begin_table("Control Preview#Header", 4, PyImGui.TableFlags.BordersOuterH, 0, 30):
            PyImGui.table_setup_column(
                "Control", PyImGui.TableColumnFlags.WidthFixed, 100)
            PyImGui.table_setup_column(
                "Color Edit", PyImGui.TableColumnFlags.WidthFixed, 320)
            PyImGui.table_setup_column(
                "Preview", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column(
                "Code", PyImGui.TableColumnFlags.WidthFixed, 100)

            PyImGui.table_next_row()
            PyImGui.table_next_column()

            PyImGui.table_next_column()

            ImGui.text("Edit Colors")
            PyImGui.table_next_column()

            ImGui.text("Preview")
            PyImGui.table_next_column()

            ImGui.text("Code")
            ImGui.end_table()
        PyImGui.pop_style_var(1)
        # endregion

        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.CellPadding, 4, 8)
        if ImGui.begin_table("Control Preview", 4, PyImGui.TableFlags.ScrollX | PyImGui.TableFlags.ScrollY | PyImGui.TableFlags.BordersInnerH):
            PyImGui.table_setup_column(
                "Control", PyImGui.TableColumnFlags.WidthFixed, 100)
            PyImGui.table_setup_column(
                "Color Edit", PyImGui.TableColumnFlags.WidthFixed, 320)
            PyImGui.table_setup_column(
                "Preview", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column(
                "Code", PyImGui.TableColumnFlags.WidthFixed, 100)

            PyImGui.table_next_row()
            PyImGui.table_next_column()

            for control_name, control_draw_func in use_controls.items():
                ImGui.text(control_name)
                PyImGui.table_next_column()

                control_draw_func()

            ImGui.end_table()
        PyImGui.pop_style_var(1)


def DrawWindow():
    global window_module, module_name, ini_handler, window_x, window_y, window_collapsed, control_compare, theme_compare, org_style, window_width, window_height
    global game_throttle_time, game_throttle_timer, save_throttle_time, save_throttle_timer

    # try:
    if not window_module.open:
        return

    if window_module.begin():
        PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() + 5)
        ImGui.text("Selected Theme")
        PyImGui.same_line(0, 5)
        PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 5)
        remaining = PyImGui.get_content_region_avail()
        PyImGui.push_item_width(remaining[0] - 30)
        value = ImGui.combo("##theme_selector",
                            ImGui.Selected_Style.Theme.value, themes)

        if value != ImGui.Selected_Style.Theme.value:
            theme = Style.StyleTheme(value)
            ImGui.reload_theme(theme)
            ImGui.set_theme(theme)

            org_style = ImGui.Selected_Style.copy()
            py4_gw_ini_handler.write_key(
                "settings", "style_theme", ImGui.Selected_Style.Theme.name)

        PyImGui.same_line(0, 5)
        PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 5)
        theme_compare = ImGui.checkbox(
            "##show_theme_compare", theme_compare)
        ImGui.show_tooltip(
            "Show Theme Compare window")

        PyImGui.spacing()
        ImGui.separator()
        PyImGui.spacing()
        any_changed = False

        if ImGui.begin_tab_bar("Style Customization"):
            if ImGui.begin_tab_item("Style Customization"):
                ImGui.begin_child("Style Customization")

                if ImGui.Selected_Style:
                    remaining = PyImGui.get_content_region_avail()
                    button_width = (remaining[0] - 10) / 2

                    any_changed = any(
                        var != org_style.StyleVars[enum] for enum, var in ImGui.Selected_Style.StyleVars.items())
                    any_changed |= any(
                        col != org_style.Colors[enum] for enum, col in ImGui.Selected_Style.Colors.items())
                    any_changed |= any(
                        col != org_style.CustomColors[enum] for enum, col in ImGui.Selected_Style.CustomColors.items())
                    any_changed |= any(
                        col != org_style.TextureColors[enum] for enum, col in ImGui.Selected_Style.TextureColors.items())

                    if ImGui.button("Save Changes", button_width, enabled=any_changed):
                        ImGui.Selected_Style.save_to_json()
                        ImGui.Selected_Style.apply_to_style_config()
                        org_style = ImGui.Selected_Style.copy()

                    PyImGui.same_line(0, 5)

                    if ImGui.button("Reset to Default", button_width, enabled=any_changed):
                        theme = ImGui.Selected_Style.Theme
                        ImGui.Selected_Style.delete()
                        ImGui.reload_theme(theme)
                        org_style = ImGui.Selected_Style.copy()

                    ImGui.show_tooltip(
                        "Delete the current style and replace it with the default style for the theme.")

                    PyImGui.spacing()

                    if PyImGui.is_rect_visible(50, 50):
                        column_width = 0
                        item_width = 0

                        if ImGui.begin_table("Style Variables", 3, PyImGui.TableFlags.ScrollY):
                            PyImGui.table_setup_column(
                                "Variable", PyImGui.TableColumnFlags.WidthFixed, 150)
                            PyImGui.table_setup_column(
                                "Value", PyImGui.TableColumnFlags.WidthStretch)
                            PyImGui.table_setup_column(
                                "Undo", PyImGui.TableColumnFlags.WidthFixed, 35)

                            PyImGui.table_next_row()
                            PyImGui.table_next_column()
                            
                            ImGui.Selected_Style.Hyperlink.push_color()
                            ImGui.push_font("Regular", 18)
                            PyImGui.separator()
                            PyImGui.text("Style Vars")
                            PyImGui.separator()
                            ImGui.pop_font()
                            ImGui.Selected_Style.Hyperlink.pop_color()
                            PyImGui.table_next_column()
                            PyImGui.table_next_column()
                            PyImGui.table_next_column()

                            for enum, var in ImGui.Selected_Style.StyleVars.items():
                                PyImGui.set_cursor_pos_y(
                                    PyImGui.get_cursor_pos_y() + 5)
                                ImGui.text(f"{enum}")
                                PyImGui.table_next_column()

                                column_width = column_width or PyImGui.get_content_region_avail()[
                                    0]
                                item_width = item_width or (
                                    column_width - 5) / 2
                                PyImGui.push_item_width(item_width)
                                var.value1 = ImGui.input_float(
                                    f"##{enum}_value1", var.value1)

                                if var.value2 is not None:
                                    PyImGui.same_line(0, 5)

                                    PyImGui.push_item_width(item_width)
                                    var.value2 = ImGui.input_float(
                                        f"##{enum}_value2", var.value2)

                                PyImGui.table_next_column()

                                changed = org_style.StyleVars[
                                    enum].value1 != var.value1 or org_style.StyleVars[enum].value2 != var.value2

                                if changed:
                                    if ImGui.icon_button(f"{IconsFontAwesome5.ICON_UNDO}##{enum}_undo", 30):
                                        var.value1 = org_style.StyleVars[enum].value1
                                        var.value2 = org_style.StyleVars[enum].value2

                                PyImGui.table_next_column()

                            for enum, col in ImGui.Selected_Style.Colors.items():
                                PyImGui.set_cursor_pos_y(
                                    PyImGui.get_cursor_pos_y() + 5)
                                ImGui.text(f"{enum}")
                                PyImGui.table_next_column()

                                column_width = column_width or PyImGui.get_content_region_avail()[
                                    0]

                                PyImGui.push_item_width(column_width)
                                color_tuple = ImGui.color_edit4(
                                    f"##{enum}_color", col.color_tuple)
                                if color_tuple != col.color_tuple:
                                    col.set_tuple_color(color_tuple)

                                PyImGui.table_next_column()

                                changed = col.color_int != org_style.Colors[enum].color_int

                                if changed:
                                    if ImGui.icon_button(f"{IconsFontAwesome5.ICON_UNDO}##{enum}_undo", 30):
                                        col.color_tuple = org_style.Colors[enum].color_tuple

                                PyImGui.table_next_column()

                            PyImGui.table_next_row()
                            PyImGui.table_next_column()
                            
                            ImGui.Selected_Style.Hyperlink.push_color()
                            ImGui.push_font("Regular", 18)
                            PyImGui.separator()
                            PyImGui.text("Custom Colors")
                            PyImGui.separator()
                            ImGui.pop_font()
                            ImGui.Selected_Style.Hyperlink.pop_color()

                            PyImGui.table_next_column()
                            PyImGui.table_next_column()
                            PyImGui.table_next_column()

                            for enum, col in ImGui.Selected_Style.CustomColors.items():
                                PyImGui.set_cursor_pos_y(
                                    PyImGui.get_cursor_pos_y() + 5)
                                ImGui.text(f"{enum}")
                                PyImGui.table_next_column()

                                column_width = column_width or PyImGui.get_content_region_avail()[
                                    0]

                                PyImGui.push_item_width(column_width)
                                color_tuple = ImGui.color_edit4(
                                    f"##{enum}_color", col.color_tuple)
                                if color_tuple != col.color_tuple:
                                    col.set_tuple_color(color_tuple)

                                PyImGui.table_next_column()

                                changed = col.color_int != org_style.CustomColors[enum].color_int

                                if changed:
                                    if ImGui.icon_button(f"{IconsFontAwesome5.ICON_UNDO}##{enum}_undo", 30):
                                        col.color_tuple = org_style.CustomColors[enum].color_tuple
                                PyImGui.table_next_column()

                            PyImGui.table_next_row()
                            PyImGui.table_next_column()
                            
                            ImGui.Selected_Style.Hyperlink.push_color()
                            ImGui.push_font("Regular", 18)
                            PyImGui.separator()
                            PyImGui.text("Texture Colors")
                            PyImGui.separator()
                            ImGui.pop_font()
                            ImGui.Selected_Style.Hyperlink.pop_color()
                            PyImGui.table_next_column()
                            PyImGui.table_next_column()
                            PyImGui.table_next_column()
                            
                            for enum, col in ImGui.Selected_Style.TextureColors.items():
                                PyImGui.set_cursor_pos_y(
                                    PyImGui.get_cursor_pos_y() + 5)
                                ImGui.text(f"{enum}")
                                PyImGui.table_next_column()

                                column_width = column_width or PyImGui.get_content_region_avail()[
                                    0]

                                PyImGui.push_item_width(column_width)
                                color_tuple = ImGui.color_edit4(
                                    f"##{enum}_color", col.color_tuple)
                                if color_tuple != col.color_tuple:
                                    col.set_tuple_color(color_tuple)

                                PyImGui.table_next_column()

                                changed = col.color_int != org_style.TextureColors[enum].color_int

                                if changed:
                                    if ImGui.icon_button(f"{IconsFontAwesome5.ICON_UNDO}##{enum}_undo", 30):
                                        col.color_tuple = org_style.TextureColors[enum].color_tuple
                                PyImGui.table_next_column()
                            
                            ImGui.end_table()

                ImGui.end_child()

                ImGui.end_tab_item()

            if ImGui.begin_tab_item("Control Preview"):
                style = ImGui.get_style()

                if PyImGui.is_rect_visible(50, 50):
                    column_width = 0
                    item_width = 0

                    PyImGui.push_item_width(150)
                    if ImGui.begin_table("Control Preview", 2, PyImGui.TableFlags.ScrollX):
                        PyImGui.table_setup_column(
                            "Control", PyImGui.TableColumnFlags.WidthFixed, 150)
                        PyImGui.table_setup_column(
                            "Preview", PyImGui.TableColumnFlags.WidthStretch)

                        PyImGui.table_next_row()
                        PyImGui.table_next_column()

                        for control_name, control_draw_func in controls.items():
                            ImGui.text(control_name)
                            PyImGui.table_next_column()

                            control_draw_func(style.Theme)
                            PyImGui.table_next_column()

                        ImGui.end_table()
                    PyImGui.pop_item_width()
                ImGui.end_tab_item()

            if ImGui.begin_tab_item("How to Use"):
                DrawUsageTab()
                ImGui.end_tab_item()

            ImGui.end_tab_bar()

            if control_compare:
                DrawControlCompare()

            if theme_compare:
                DrawThemeCompare()

        window_module.process_window()

    window_module.end()

    if save_throttle_timer.HasElapsed(save_throttle_time):
        if window_module.window_pos[0] != window_module.end_pos[0] or window_module.window_pos[1] != window_module.end_pos[1]:
            window_module.window_pos = window_module.end_pos
            ini_handler.write_key(
                module_name + " Config", "x", str(int(window_module.window_pos[0])))
            ini_handler.write_key(
                module_name + " Config", "y", str(int(window_module.window_pos[1])))

        if window_width != window_module.window_size[0] or window_height != window_module.window_size[1]:
            ini_handler.write_key(
                module_name + " Config", "width", str(int(window_module.window_size[0])))
            ini_handler.write_key(
                module_name + " Config", "height", str(int(window_module.window_size[1])))
            window_width, window_height = window_module.window_size

        if window_module.collapsed_status != window_module.collapse:
            window_module.collapse = window_module.collapsed_status
            ini_handler.write_key(
                module_name + " Config", "collapsed", str(window_module.collapse))

        save_throttle_timer.Reset()

    # except Exception as e:
    #     Py4GW.Console.Log(
    #         module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Debug)


def main():
    """Required main function for the widget"""
    global game_throttle_timer, game_throttle_time, window_module

    # try:
    DrawWindow()
    window_module.open = False

    # except Exception as e:
    #     Py4GW.Console.Log(
    #         module_name, f"Error in main: {str(e)}", Py4GW.Console.MessageType.Debug)
    #     return False
    return True


# These functions need to be available at module level
__all__ = ['main', 'configure']

if __name__ == "__main__":
    main()
