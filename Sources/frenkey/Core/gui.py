import os
from typing import Optional
from Py4GW import Console
import PyImGui

from Py4GWCoreLib import IconsFontAwesome5, ImGui
from Py4GWCoreLib.Py4GWcorelib import ConsoleLog, Utils
from Py4GWCoreLib.enums import Profession, Rarity
from Sources.frenkey.Core import ex_style
from Sources.frenkey.Core import texture_map
from Sources.frenkey.Core.texture_map import CoreTextures

class GUI:
    @staticmethod
    def get_rarity_rgba_color(rarity : Rarity, alpha: int = 255) -> tuple[int, int, int, int]:        
        rarity_colors = {
            Rarity.White: (255, 255, 255, 255),
            Rarity.Blue: (153, 238, 255, 255),
            Rarity.Green: (0, 255, 0, 255),
            Rarity.Purple: (187, 136, 238, 255),
            Rarity.Gold: (255, 204, 85, 255),
        }
        
        col = rarity_colors.get(rarity, (255, 255, 255, alpha))
        return (col[0], col[1], col[2], alpha)
        
    @staticmethod
    def profession_square_texture(profession: Profession, size: int = 32, hovered : bool = False, tint : tuple[int, int, int, int] = (255, 255, 255, 255)) -> None:
        """
        Draws the texture for a given profession.

        Args:
            profession (str): The profession name.
            size (int): The size of the texture.
        """
        
        if profession != Profession._None:
            texture = CoreTextures.get_profession_texture(profession, hovered)
            
            if texture:
                ImGui.DrawTextureExtended(texture_path=texture, size=(size, size), tint=tint)
            else:
                PyImGui.dummy(size, size)
    
    @staticmethod
    def get_gradient_colors(start_color: tuple[float, float, float, float], end_color: tuple[float, float, float, float], steps: int) -> list[tuple[float, float, float, float]]:
        """
        Generates a list of gradient colors between two specified colors.

        Args:
            start_color (tuple): The starting color in RGBA format.
            end_color (tuple): The ending color in RGBA format.
            steps (int): The number of gradient steps.

        Returns:
            list: A list of colors representing the gradient.
        """
        return [
            (
                start_color[0] + (end_color[0] - start_color[0]) * i / (steps - 1),
                start_color[1] + (end_color[1] - start_color[1]) * i / (steps - 1),
                start_color[2] + (end_color[2] - start_color[2]) * i / (steps - 1),
                start_color[3] + (end_color[3] - start_color[3]) * i / (steps - 1)
            )
            for i in range(steps)
        ] if  steps > 1 else [start_color, end_color]
 
 
    @staticmethod
    def is_mouse_in_rect(rect: tuple[float, float, float, float]) -> bool:
        """
        Checks if the mouse is within a specified rectangle.

        Args:
            rect (tuple[float, float, float, float]): The rectangle defined by (x, y, width, height).

        Returns:
            bool: True if the mouse is within the rectangle, False otherwise.
        """
        pyimgui_io = PyImGui.get_io()
        mouse_pos = (pyimgui_io.mouse_pos_x, pyimgui_io.mouse_pos_y)
        
        return (rect[0] <= mouse_pos[0] <= rect[0] + rect[2] and
                rect[1] <= mouse_pos[1] <= rect[1] + rect[3])

    @staticmethod
    def is_hovered(width : float, height : float) -> bool:
        """
        Checks if the current item is hovered.

        Args:
            width (float): The width of the item.
            height (float): The height of the item.

        Returns:
            bool: True if the item is hovered, False otherwise.
        """
        screen_cursor = PyImGui.get_cursor_screen_pos()
        rect = (screen_cursor[0], screen_cursor[1], width, height)
        
        return GUI.is_mouse_in_rect(rect)
    
    @staticmethod
    def item_toggle_button(texture: str | None, skin_size : float = 42, selected : bool = False, background: bool = True, padding : tuple[float, float] = (0, 0), selected_color : tuple[int, int, int, int] | None = None) -> tuple[bool, bool]:
        if not PyImGui.is_rect_visible(skin_size, skin_size):
            PyImGui.dummy(int(skin_size), int(skin_size))
            return selected, False
        
        factor = 34 / 42 ## Width / Height ratio of the frame texture
        padding = (0, 0)
        frame_reduce = 0.85
        frame_size = (skin_size * frame_reduce + (padding[0] * 2), (skin_size * frame_reduce / factor) + (padding[1] * 2))
        
        screen_cursor = PyImGui.get_cursor_screen_pos()
        is_hovered = GUI.is_mouse_in_rect((screen_cursor[0], screen_cursor[1], frame_size[0], frame_size[1])) and PyImGui.is_window_hovered()
        
        window_style = ex_style.ExStyle()
        alpha = 255 if is_hovered else 225 if (selected) else 50
        texture_alpha = 255 if is_hovered else 225 if (selected) else 100
        frame_color =  selected_color if selected_color else window_style.Selected_Colored_Item.rgb_tuple if selected else (100,100,100, texture_alpha)
        texture_color =  (255, 255, 255, texture_alpha) if selected else (100,100,100, 200 if is_hovered else 125 )
        
        texture_exists = os.path.exists(texture) and os.path.isfile(texture) if texture else False
        if is_hovered:
            rect = (screen_cursor[0], screen_cursor[1], screen_cursor[0] + frame_size[0], screen_cursor[1] + frame_size[1])           
            PyImGui.draw_list_add_rect_filled(rect[0], rect[1], rect[2], rect[3], Utils.RGBToColor(frame_color[0], frame_color[1], frame_color[2], 50), 1.0, 0)                                                     
                                        
        ImGui.DrawTextureExtended(texture_path=texture_map.CoreTextures.UI_Inventory_Slot.value, size=(frame_size[0], frame_size[1]), tint=frame_color)
        
        if texture_exists and texture:     
            PyImGui.set_cursor_screen_pos(screen_cursor[0] + padding[0], screen_cursor[1] + padding[1])                                  
            ImGui.DrawTextureExtended(texture_path=texture, size=(skin_size, skin_size), tint=texture_color)
        else:
            ImGui.push_font("Bold", int(skin_size * factor))        
            text_size = PyImGui.calc_text_size(IconsFontAwesome5.ICON_QUESTION)
            
            PyImGui.set_cursor_screen_pos(screen_cursor[0] + ((frame_size[0] - text_size[0]) / 2), screen_cursor[1] + ((frame_size[1] - text_size[1]) / 2))
            PyImGui.push_style_color(
                PyImGui.ImGuiCol.Text, (texture_color[0] / 255, texture_color[1] / 255, texture_color[2] / 255, texture_color[3] / 255))
            PyImGui.text(IconsFontAwesome5.ICON_QUESTION)  
            PyImGui.pop_style_color(1)
            ImGui.pop_font()

        if PyImGui.is_item_clicked(0) and is_hovered: 
            selected = not selected 
                    
        return selected, is_hovered
    
    @staticmethod
    def image_button(texture_path: str, texture_size : tuple[float, float], hovered_texture_path: Optional[str] = None, background: bool = True, padding : tuple[float, float] = (2, 2)) -> bool:
        """
        Draws an image button with a specified texture and size.

        Args:
            texture_path (str): The path to the texture.
            width (float): The width of the button.
            height (float): The height of the button.
            hovered_texture_path (Optional[str]): The path to the texture when hovered.

        Returns:
            bool: True if the button is clicked, False otherwise.
        """
        size = (texture_size[0] + (padding[0] * 2), texture_size[1] + (padding[1] * 2))       
        
        screen_cursor = PyImGui.get_cursor_screen_pos()
        rect = (screen_cursor[0], screen_cursor[1], size[0], size[1]) 
        is_hovered = GUI.is_mouse_in_rect(rect)
        is_clicked = PyImGui.is_mouse_clicked(0) and is_hovered
        
        if background:
            window_style = ex_style.ExStyle()
            imgui_style = ImGui.get_style()
            color = imgui_style.ButtonActive if is_clicked else imgui_style.ButtonHovered if is_hovered else imgui_style.Button
            
            PyImGui.draw_list_add_rect_filled(rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3], color.color_int, imgui_style.FrameRounding.value1, 0)
        
        tint = (255, 255, 255, 255)  if is_hovered else (200, 200, 200, 255)         
        
        PyImGui.set_cursor_screen_pos(screen_cursor[0] + padding[0], screen_cursor[1] + padding[1])
        if is_hovered and hovered_texture_path:
            ImGui.DrawTextureExtended(hovered_texture_path, (texture_size[0], texture_size[1]))
        else:
            ImGui.DrawTextureExtended(texture_path, (texture_size[0], texture_size[1]), tint=tint)
        
        return is_clicked
    
    @staticmethod
    def vertical_centered_text(text: str, same_line_spacing: Optional[float] = None, desired_height: float = 24, color : tuple[float, float, float, float] | None = None) -> float:
        """
        Draws text vertically centered within a specified height.

        Args:
            text (str): The text to display.
            same_line_spacing (Optional[float]): Spacing to apply if the text is on the same line.
            desired_height (int): The height within which the text should be centered.

        Returns:
            float: The width of the rendered text.
        """
        # text_size = PyImGui.calc_text_size(text)
        # text_offset = (desired_height - text_size[1]) / 2

        # cursor_y = PyImGui.get_cursor_pos_y()

        # if text_offset > 0:
        #     PyImGui.set_cursor_pos_y(cursor_y + text_offset)

        # PyImGui.text(text)

        # if same_line_spacing:
        #     if text_offset > 0:
        #         PyImGui.set_cursor_pos_y(cursor_y)

        #     PyImGui.set_cursor_pos_x(
        #         PyImGui.get_cursor_pos_x() + text_size[0] + same_line_spacing)

        # return text_size[0]

        textSize = PyImGui.calc_text_size(text)
        textOffset = (desired_height - textSize[1]) / 2

        cursorY = PyImGui.get_cursor_pos_y()
        cusorX = PyImGui.get_cursor_pos_x()

        if textOffset > 0:
            PyImGui.set_cursor_pos_y(cursorY + textOffset)

        if color is not None:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, color)

        PyImGui.text(text)
            
        if color is not None:
            PyImGui.pop_style_color(1)

        if same_line_spacing:
            if textOffset > 0:
                PyImGui.set_cursor_pos_y(cursorY)

            # PyImGui.set_cursor_pos_x(cusorX + textSize[0] + sameline_spacing)
            PyImGui.set_cursor_pos_x(same_line_spacing)

        return textSize[0]
