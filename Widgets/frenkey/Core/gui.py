from typing import Optional
import PyImGui

class GUI:
    @staticmethod
    def vertical_centered_text(text: str, same_line_spacing: Optional[float] = None, desired_height: int = 24, color : tuple[float, float, float, float] | None = None) -> float:
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

        if color:
            PyImGui.text_colored(text, color)
        else:
            PyImGui.text(text)

        if same_line_spacing:
            if textOffset > 0:
                PyImGui.set_cursor_pos_y(cursorY)

            # PyImGui.set_cursor_pos_x(cusorX + textSize[0] + sameline_spacing)
            PyImGui.set_cursor_pos_x(same_line_spacing)

        return textSize[0]
