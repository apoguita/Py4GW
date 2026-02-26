
import traceback
import Py4GW
import PyImGui

from Py4GWCoreLib import ImGui
from Py4GWCoreLib.ImGui_src.Style import Style
from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import Widget

IMAGE_SIZE = 40
PADDING = 10
TAG_HEIGHT = 18
BUTTON_HEIGHT = 24
ROUNDING = 6.0
NAME_COLOR = Color(255, 255, 255, 255)
NAME_ENABLED_COLOR = Color(150, 255, 150, 255)
CATEGORY_COLOR = Color(150, 150, 150, 255)
SYSTEM_COLOR = Color(255, 0, 0, 255)
TAG_COLOR = Color(38, 51, 59, 255)

CARD_BACKGROUND_COLOR = Color(200, 200, 200, 20)
CARD_ENABLED_BACKGROUND_COLOR = Color(90, 255, 90, 30)
FAVORITES_COLOR = Color(255, 215, 0, 255)  # Gold color for favorites


def _push_card_style(style : Style, enabled : bool):
    style.ChildBg.push_color(CARD_ENABLED_BACKGROUND_COLOR.rgb_tuple if enabled else CARD_BACKGROUND_COLOR.rgb_tuple)
    style.ChildBorderSize.push_style_var(2.0 if enabled else 1.0) 
    style.ChildRounding.push_style_var(4.0)
    style.Border.push_color(CARD_ENABLED_BACKGROUND_COLOR.opacity(0.6).rgb_tuple if enabled else CARD_BACKGROUND_COLOR.opacity(0.6).rgb_tuple)
    pass

def _pop_card_style(style : Style):
    style.ChildBg.pop_color()
    style.ChildBorderSize.pop_style_var()
    style.ChildRounding.pop_style_var()
    style.Border.pop_color()
    pass

def _push_tag_style(style : Style, color : tuple):
    style.FramePadding.push_style_var(4, 4)
    style.Button.push_color(color)
    style.ButtonHovered.push_color(color)
    style.ButtonActive.push_color(color)
    ImGui.push_font("Regular", 12)

def _pop_tag_style(style : Style):
    style.FramePadding.pop_style_var()
    style.Button.pop_color()
    style.ButtonHovered.pop_color()
    style.ButtonActive.pop_color()
    ImGui.pop_font()
   

def draw_widget_card(widget : Widget, CARD_WIDTH : float, is_favorite: bool = False):
    """
    Draws a single widget card.
    Must be called inside a grid / SameLine layout.
    """
    style = ImGui.get_style()
    _push_card_style(style, widget.enabled)
    
    opened = PyImGui.begin_child(
        f"##widget_card_{widget.folder_script_name}",
        (CARD_WIDTH, 88),
        border=True,
        flags=PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse
    )
    
    if opened and PyImGui.is_rect_visible(CARD_WIDTH, 88):
        available_width = PyImGui.get_content_region_avail()[0]
        
        # --- Top Row: Icon + Title ---
        PyImGui.begin_group()

        # Icon
        ImGui.image(widget.image, (IMAGE_SIZE, IMAGE_SIZE), border_color=CATEGORY_COLOR.rgb_tuple)

        PyImGui.same_line(0, 5)

        # Title + Category
        PyImGui.begin_group()
        # ImGui.push_font("Regular", 16)
        name = ImGui.trim_text_to_width(text=f"{widget.name}", max_width=CARD_WIDTH - IMAGE_SIZE - BUTTON_HEIGHT - PADDING * 4 - (15 if is_favorite else 0))
        if is_favorite:
            ImGui.text_colored(f"{IconsFontAwesome5.ICON_STAR} ", FAVORITES_COLOR.color_tuple, font_size=10)
            PyImGui.same_line(0, 3)
            
        ImGui.text_colored(name, NAME_COLOR.color_tuple if not widget.enabled else NAME_ENABLED_COLOR.color_tuple)
        # ImGui.pop_font()
        
        PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 4)
        PyImGui.separator()

        PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 2)
        ImGui.text_colored(f"{widget.category}", CATEGORY_COLOR.color_tuple if widget.category != "System" else SYSTEM_COLOR.color_tuple, 12)

        PyImGui.end_group()
                
        if widget.has_configure_property:
            PyImGui.set_cursor_pos(available_width - 10, 2)
            ImGui.toggle_icon_button(IconsFontAwesome5.ICON_COG, widget.configuring, BUTTON_HEIGHT, BUTTON_HEIGHT)
        PyImGui.end_group()

        # --- Tags ---
        _push_tag_style(style, TAG_COLOR.rgb_tuple)
        PyImGui.begin_group()
        for i, tag in enumerate(widget.tags):
            if i > 0:
                PyImGui.same_line(0, 2)

            PyImGui.button(tag)
        PyImGui.end_group()
        _pop_tag_style(style)


    PyImGui.end_child()
    clicked = False
    hovered = False
    _pop_card_style(style)
    
    if PyImGui.is_item_clicked(0):
        clicked = True
        widget.enable() if not widget.enabled else widget.disable()
        
    if PyImGui.is_item_hovered():
        hovered = True
        if widget.has_tooltip_property:
            try:
                if widget.tooltip:
                    widget.tooltip()
            except Exception as e:
                Py4GW.Console.Log("WidgetHandler", f"Error during tooltip of widget {widget.folder_script_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
        else:
            PyImGui.show_tooltip(f"Enable/Disable {widget.name} widget")

    return clicked or hovered
    
def draw_compact_widget_card(widget : Widget, CARD_WIDTH : float) -> bool:
    """
    Draws a single widget card.
    Must be called inside a grid / SameLine layout.
    """

    style = ImGui.get_style()
    _push_card_style(style, widget.enabled)
    
    opened = PyImGui.begin_child(
        f"##widget_card_{widget.folder_script_name}",
        (CARD_WIDTH, 30),
        border=True,
        flags=PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse
    )
    
    if opened and PyImGui.is_rect_visible(CARD_WIDTH, 30):
        available_width = PyImGui.get_content_region_avail()[0]

        ImGui.push_font("Regular", 15)
        name = ImGui.trim_text_to_width(text=widget.name, max_width=available_width - 20)
        ImGui.text_colored(name, NAME_COLOR.color_tuple if not widget.enabled else NAME_ENABLED_COLOR.color_tuple, 15)
        ImGui.pop_font()
                        
        if widget.has_configure_property:
            PyImGui.set_cursor_pos(available_width - 10, 2)
            ImGui.toggle_icon_button(IconsFontAwesome5.ICON_COG, widget.configuring, BUTTON_HEIGHT, BUTTON_HEIGHT)

    PyImGui.end_child()
    _pop_card_style(style)
    clicked = False
    hovered = False
    
    if PyImGui.is_item_clicked(0):
        clicked = True
        widget.enable() if not widget.enabled else widget.disable()
        
    if PyImGui.is_item_hovered():
        hovered = True
        if widget.has_tooltip_property:
            try:
                if widget.tooltip:
                    widget.tooltip()
            except Exception as e:
                Py4GW.Console.Log("WidgetHandler", f"Error during tooltip of widget {widget.folder_script_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
        else:
            PyImGui.show_tooltip(f"Enable/Disable {widget.name} widget")

    return clicked or hovered
    