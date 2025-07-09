import Py4GW
import PyImGui
from enum import Enum, IntEnum
from .Overlay import Overlay
from Py4GWCoreLib.Py4GWcorelib import Color, ColorPalette
from Py4GWCoreLib.enums import get_texture_for_model, ImguiFonts

from enum import IntEnum

class SortDirection(Enum):
    No_Sort = 0
    Ascending = 1
    Descending = 2

class ImGui:
    class ImGuiStyleVar(IntEnum):
        Alpha = 0
        DisabledAlpha = 1
        WindowPadding = 2
        WindowRounding = 3
        WindowBorderSize = 4
        WindowMinSize = 5
        WindowTitleAlign = 6
        ChildRounding = 7
        ChildBorderSize = 8
        PopupRounding = 9
        PopupBorderSize = 10
        FramePadding = 11
        FrameRounding = 12
        FrameBorderSize = 13
        ItemSpacing = 14
        ItemInnerSpacing = 15
        IndentSpacing = 16
        CellPadding = 17
        ScrollbarSize = 18
        ScrollbarRounding = 19
        GrabMinSize = 20
        GrabRounding = 21
        TabRounding = 22
        ButtonTextAlign = 23
        SelectableTextAlign = 24
        SeparatorTextBorderSize = 25
        SeparatorTextAlign = 26
        SeparatorTextPadding = 27
        COUNT = 28
        
    @staticmethod
    def DrawTexture(texture_path: str, width: float = 32.0, height: float = 32.0):
        Overlay().DrawTexture(texture_path, width, height)
        
    @staticmethod
    def DrawTextureExtended(texture_path: str, size: tuple[float, float],
                            uv0: tuple[float, float] = (0.0, 0.0),
                            uv1: tuple[float, float] = (1.0, 1.0),
                            tint: tuple[int, int, int, int] = (255, 255, 255, 255),
                            border_color: tuple[int, int, int, int] = (0, 0, 0, 0)):
        Overlay().DrawTextureExtended(texture_path, size, uv0, uv1, tint, border_color)
     
    @staticmethod   
    def DrawTexturedRect(x: float, y: float, width: float, height: float, texture_path: str):
        Overlay().BeginDraw()
        Overlay().DrawTexturedRect(x, y, width, height, texture_path)
        Overlay().EndDraw()
        
    @staticmethod
    def DrawTexturedRectExtended(pos: tuple[float, float], size: tuple[float, float], texture_path: str,
                                    uv0: tuple[float, float] = (0.0, 0.0),  
                                    uv1: tuple[float, float] = (1.0, 1.0),
                                    tint: tuple[int, int, int, int] = (255, 255, 255, 255)):
        Overlay().BeginDraw()
        Overlay().DrawTexturedRectExtended(pos, size, texture_path, uv0, uv1, tint)
        Overlay().EndDraw()
        
    @staticmethod
    def ImageButton(caption: str, texture_path: str, width: float = 32.0, height: float = 32.0, frame_padding: int = -1) -> bool:
        return Overlay().ImageButton(caption, texture_path, width, height, frame_padding)
    
    @staticmethod
    def ImageButtonExtended(caption: str, texture_path: str, size: tuple[float, float],
                            uv0: tuple[float, float] = (0.0, 0.0),
                            uv1: tuple[float, float] = (1.0, 1.0),
                            bg_color: tuple[int, int, int, int] = (0, 0, 0, 0),
                            tint_color: tuple[int, int, int, int] = (255, 255, 255, 255),
                            frame_padding: int = -1) -> bool:
        return Overlay().ImageButtonExtended(caption, texture_path, size, uv0, uv1, bg_color, tint_color, frame_padding)
    
    @staticmethod
    def GetModelIDTexture(model_id: int) -> str:
        """
        Purpose: Get the texture path for a given model_id.
        Args:
            model_id (int): The model ID to get the texture for.
        Returns: str: The texture path or a fallback image path if not found.
        """
        return get_texture_for_model(model_id)
        
    @staticmethod
    def show_tooltip(text: str):
        """
        Purpose: Display a tooltip with the provided text.
        Args:
            text (str): The text to display in the tooltip.
        Returns: None
        """
        if PyImGui.is_item_hovered():
            PyImGui.begin_tooltip()
            PyImGui.text(text)
            PyImGui.end_tooltip()


    @staticmethod
    def colored_button(label: str, button_color:Color, hovered_color:Color, active_color:Color, width=0, height=0):
        clicked = False

        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, button_color.to_tuple_normalized())  # On color
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, hovered_color.to_tuple_normalized())  # Hover color
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, active_color.to_tuple_normalized())

        clicked = PyImGui.button(label, width, height)

        PyImGui.pop_style_color(3)
        
        return clicked

    @staticmethod
    def toggle_button(label: str, v: bool, width=0, height =0) -> bool:
        """
        Purpose: Create a toggle button that changes its state and color based on the current state.
        Args:
            label (str): The label of the button.
            v (bool): The current toggle state (True for on, False for off).
        Returns: bool: The new state of the button after being clicked.
        """
        clicked = False

        if v:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.153, 0.318, 0.929, 1.0))  # On color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.6, 0.6, 0.9, 1.0))  # Hover color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.6, 0.6, 0.6, 1.0))
            if width != 0 and height != 0:
                clicked = PyImGui.button(label, width, height)
            else:
                clicked = PyImGui.button(label)
            PyImGui.pop_style_color(3)
        else:
            if width != 0 and height != 0:
                clicked = PyImGui.button(label, width, height)
            else:
                clicked = PyImGui.button(label)

        if clicked:
            v = not v

        return v
    
    @staticmethod
    def image_toggle_button(label: str, texture_path: str, v: bool, width=0, height=0) -> bool:
        """
        Purpose: Create a toggle button that displays an image and changes its state when clicked.
        Args:
            label (str): The label of the button.
            texture_path (str): The path to the image texture.
            v (bool): The current toggle state (True for on, False for off).
        Returns: bool: The new state of the button after being clicked.
        """
        clicked = False

        if v:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, Color(156, 156, 230, 255).to_tuple_normalized())  # On color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, Color(156, 156, 230, 255).to_tuple_normalized())  # Hover color
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, Color(156, 156, 156, 255).to_tuple_normalized())
            if width != 0 and height != 0:
                clicked = ImGui.ImageButton(label, texture_path, width, height)      
            else:
                clicked = ImGui.ImageButton(label, texture_path)
            PyImGui.pop_style_color(3)
        else:
            if width != 0 and height != 0:
                clicked = ImGui.ImageButton(label, texture_path, width, height)
            else:
                clicked = ImGui.ImageButton(label, texture_path) 
        if clicked:
            v = not v
        return v

    @staticmethod
    def floating_button(caption, x, y, width = 18, height = 18 , color: Color = Color(255, 255, 255, 255), name = ""):
        if not name:
            name = caption
        
        PyImGui.set_next_window_pos(x, y)
        PyImGui.set_next_window_size(width, height)

        flags = (
            PyImGui.WindowFlags.NoCollapse |
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.AlwaysAutoResize |
            PyImGui.WindowFlags.NoBackground
        )

        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, -1, -0)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
        PyImGui.push_style_color(PyImGui.ImGuiCol.WindowBg, (0, 0, 0, 0))  # Fully transparent
        
        # Transparent button face
        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.0, 0.0, 0.0, 0.0))
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.0, 0.0, 0.0, 0.0))
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.0, 0.0, 0.0, 0.0))

        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, color.to_tuple_normalized())
        result = False
        if PyImGui.begin(f"{caption}##invisible_buttonwindow{name}", flags):
            result = PyImGui.button(f"{caption}##floating_button{name}", width=width, height=height)

            
        PyImGui.end()
        PyImGui.pop_style_color(5)  # Button, Hovered, Active, Text, WindowBg
        PyImGui.pop_style_var(2)

        return result
    
    @staticmethod
    def floating_checkbox(caption, state,  x, y, width = 18, height = 18 , color: Color = Color(255, 255, 255, 255)):
        # Set the position and size of the floating button
        PyImGui.set_next_window_pos(x, y)
        PyImGui.set_next_window_size(width, height)
        

        flags=( PyImGui.WindowFlags.NoCollapse | 
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.AlwaysAutoResize  ) 
        
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding,0.0,0.0)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 3, 5)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, color.to_tuple_normalized())
        
        result = state
        
        white = ColorPalette.GetColor("White")
        
        if PyImGui.begin(f"##invisible_window{caption}", flags):
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0.2, 0.3, 0.4, 0.1))  # Normal state color
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0.3, 0.4, 0.5, 0.1))  # Hovered state
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0.4, 0.5, 0.6, 0.1))  # Checked state
            PyImGui.push_style_color(PyImGui.ImGuiCol.CheckMark, color.shift(white, 0.5).to_tuple_normalized())  # Checkmark color

            result = PyImGui.checkbox(f"##floating_checkbox{caption}", state)
            PyImGui.pop_style_color(4)
        PyImGui.end()
        PyImGui.pop_style_var(3)
        PyImGui.pop_style_color(1)
        return result
            
    _last_font_scaled = False  # Module-level tracking flag
    @staticmethod
    def push_font(font_family: str, pixel_size: int):
        _available_sizes = [14, 22, 30, 46, 62, 124]
        _font_map = {
                "Regular": {
                    14: ImguiFonts.Regular_14,
                    22: ImguiFonts.Regular_22,
                    30: ImguiFonts.Regular_30,
                    46: ImguiFonts.Regular_46,
                    62: ImguiFonts.Regular_62,
                    124: ImguiFonts.Regular_124,
                },
                "Bold": {
                    14: ImguiFonts.Bold_14,
                    22: ImguiFonts.Bold_22,
                    30: ImguiFonts.Bold_30,
                    46: ImguiFonts.Bold_46,
                    62: ImguiFonts.Bold_62,
                    124: ImguiFonts.Bold_124,
                },
                "Italic": {
                    14: ImguiFonts.Italic_14,
                    22: ImguiFonts.Italic_22,
                    30: ImguiFonts.Italic_30,
                    46: ImguiFonts.Italic_46,
                    62: ImguiFonts.Italic_62,
                    124: ImguiFonts.Italic_124,
                },
                "BoldItalic": {
                    14: ImguiFonts.BoldItalic_14,
                    22: ImguiFonts.BoldItalic_22,
                    30: ImguiFonts.BoldItalic_30,
                    46: ImguiFonts.BoldItalic_46,
                    62: ImguiFonts.BoldItalic_62,
                    124: ImguiFonts.BoldItalic_124,
                }
            }

        global _last_font_scaled
        _last_font_scaled = False  # Reset the flag each time a font is pushed
        if pixel_size < 1:
            raise ValueError("Pixel size must be a positive integer")
        
        family_map = _font_map.get(font_family)
        if not family_map:
            raise ValueError(f"Unknown font family '{font_family}'")

        # Exact match
        if pixel_size in _available_sizes:
            font_enum = family_map[pixel_size]
            PyImGui.push_font(font_enum.value)
            _last_font_scaled = False
            return

        # Scale down using the next available size
        for defined_size in _available_sizes:
            if defined_size > pixel_size:
                font_enum = family_map[defined_size]
                scale = pixel_size / defined_size
                PyImGui.push_font_scaled(font_enum.value, scale)
                _last_font_scaled = True
                return

        # If requested size is larger than the largest available, scale up
        largest_size = _available_sizes[-1]
        font_enum = family_map[largest_size]
        scale = pixel_size / largest_size
        PyImGui.push_font_scaled(font_enum.value, scale)
        _last_font_scaled = True
        

    @staticmethod
    def pop_font():
        global _last_font_scaled
        if _last_font_scaled:
            PyImGui.pop_font_scaled()
        else:
            PyImGui.pop_font()

    @staticmethod
    def table(title:str, headers, data):
        """
        Purpose: Display a table using PyImGui.
        Args:
            title (str): The title of the table.
            headers (list of str): The header names for the table columns.
            data (list of values or tuples): The data to display in the table. 
                - If it's a list of single values, display them in one column.
                - If it's a list of tuples, display them across multiple columns.
            row_callback (function): Optional callback function for each row.
        Returns: None
        """
        if len(data) == 0:
            return  # No data to display

        first_row = data[0]
        if isinstance(first_row, tuple):
            num_columns = len(first_row)
        else:
            num_columns = 1  # Single values will be displayed in one column

        # Start the table with dynamic number of columns
        if PyImGui.begin_table(title, num_columns, PyImGui.TableFlags.Borders | PyImGui.TableFlags.SizingStretchSame | PyImGui.TableFlags.Resizable):
            for i, header in enumerate(headers):
                PyImGui.table_setup_column(header)
            PyImGui.table_headers_row()

            for row in data:
                PyImGui.table_next_row()
                if isinstance(row, tuple):
                    for i, cell in enumerate(row):
                        PyImGui.table_set_column_index(i)
                        PyImGui.text(str(cell))
                else:
                    PyImGui.table_set_column_index(0)
                    PyImGui.text(str(row))

            PyImGui.end_table()

    @staticmethod
    def DrawTextWithTitle(title, text_content, lines_visible=10):
        """
        Display a title and a scrollable text area with proper wrapping.
        """
        margin = 20
        line_padding = 4

        # Display title
        PyImGui.text(title)
        PyImGui.spacing()

        # Get window width with margin adjustments
        window_width = max(PyImGui.get_window_size()[0] - margin, 100)

        # Calculate content height based on number of visible lines
        line_height = PyImGui.get_text_line_height() + line_padding
        content_height = max(lines_visible * line_height, 100)

        # Set up a scrollable child window
        if PyImGui.begin_child(f"ScrollableTextArea_{title}", size=(window_width, content_height), border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):
            PyImGui.text_wrapped(text_content + "\n" + Py4GW.Console.GetCredits())
            PyImGui.end_child()



    class WindowModule:
        def __init__(self, module_name="", window_name="", window_size=(100,100), window_pos=(0,0), window_flags=PyImGui.WindowFlags.NoFlag, collapse= False):
            self.module_name = module_name
            if not self.module_name:
                return
            self.window_name = window_name if window_name else module_name
            self.window_size = window_size
            self.collapse = collapse
            if window_pos == (0,0):
                overlay = Overlay()
                screen_width, screen_height = overlay.GetDisplaySize().x, overlay.GetDisplaySize().y
                #set position to the middle of the screen
                self.window_pos = (screen_width / 2 - window_size[0] / 2, screen_height / 2 - window_size[1] / 2)
            else:
                self.window_pos = window_pos
            self.window_flags = window_flags
            self.first_run = True

            #debug variables
            self.collapsed_status = True
            self.tracking_position = self.window_pos

        def initialize(self):
            if not self.module_name:
                return
            if self.first_run:
                PyImGui.set_next_window_size(self.window_size[0], self.window_size[1])     
                PyImGui.set_next_window_pos(self.window_pos[0], self.window_pos[1])
                PyImGui.set_next_window_collapsed(self.collapse, 0)
                self.first_run = False

        def begin(self):
            if not self.module_name:
                return
            self.collapsed_status = True
            self.tracking_position = self.window_pos
            return PyImGui.begin(self.window_name, self.window_flags)

        def process_window(self):
            if not self.module_name:
                return
            self.collapsed_status = PyImGui.is_window_collapsed()
            self.end_pos = PyImGui.get_window_pos()

        def end(self):
            if not self.module_name:
                return
            PyImGui.end()
            """ INI FILE ROUTINES NEED WORK 
            if end_pos[0] != window_module.window_pos[0] or end_pos[1] != window_module.window_pos[1]:
                ini_handler.write_key(module_name + " Config", "config_x", str(int(end_pos[0])))
                ini_handler.write_key(module_name + " Config", "config_y", str(int(end_pos[1])))

            if new_collapsed != window_module.collapse:
                ini_handler.write_key(module_name + " Config", "collapsed", str(new_collapsed))
            """
       
    @staticmethod     
    def PushTransparentWindow():
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowPadding,0.0)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowBorderSize,0.0)
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding,0.0,0.0)
        
        flags=( PyImGui.WindowFlags.NoCollapse | 
                PyImGui.WindowFlags.NoTitleBar |
                PyImGui.WindowFlags.NoScrollbar |
                PyImGui.WindowFlags.NoScrollWithMouse |
                PyImGui.WindowFlags.AlwaysAutoResize |
                PyImGui.WindowFlags.NoResize |
                PyImGui.WindowFlags.NoBackground 
            ) 
        
        return flags

    @staticmethod
    def PopTransparentWindow():
        PyImGui.pop_style_var(4)