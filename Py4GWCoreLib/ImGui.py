import Py4GW
import PyImGui
from enum import Enum, IntEnum
from .Overlay import Overlay
from Py4GWCoreLib.Py4GWcorelib import Color

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
    def DrawTexturedRect(x: float, y: float, width: float, height: float, texture_path: str):
        Overlay().BeginDraw()
        Overlay().DrawTexturedRect(x, y, width, height, texture_path)
        Overlay().EndDraw()
        
    @staticmethod
    def ImageButton(caption: str, texture_path: str, width: float = 32.0, height: float = 32.0, frame_padding: int = -1) -> bool:
        return Overlay().ImageButton(caption, texture_path, width, height, frame_padding)
        
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
    def floating_button(caption,x, y, width=45, height=40, font_color=None):
        # Set the position and size of the floating button
        PyImGui.set_next_window_pos(x-width/2, y-height/2)
        PyImGui.set_next_window_size(width, height)  # Button window size
        
        clicked = False

        # Create a floating, borderless window for the button
        flags=( PyImGui.WindowFlags.NoCollapse | 
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoMove |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.AlwaysAutoResize |
            PyImGui.WindowFlags.NoBackground |
            PyImGui.WindowFlags.NoBringToFrontOnFocus
        ) 
        
        if PyImGui.begin(f"FloatingButton_{caption}", flags):

            # Style adjustments for padding and alignment
            PyImGui.push_style_var2(ImGui.ImGuiStyleVar.ButtonTextAlign, 0.0, 0.0)  # Center text
            PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 5.0, 5.0)  # Padding inside the button

            # Create the button and check if it is clicked
            if font_color is None:
                clicked = PyImGui.button(caption, width, height)
            else:
                # Set the font color if provided
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, font_color)
                clicked = PyImGui.button(caption, width, height)
                # Restore the default font color
                PyImGui.pop_style_color(1)

            # Restore styles
            PyImGui.pop_style_var(2)

        PyImGui.end()

        return clicked  # Return True if clicked, False otherwise
    
    @staticmethod
    def floating_checkbox(caption, state,x,y):
        width=25
        height=25
        # Set the position and size of the floating button
        PyImGui.set_next_window_pos(x, y)
        PyImGui.set_next_window_size(width, height)
        

        flags=( PyImGui.WindowFlags.NoCollapse | 
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.AlwaysAutoResize |
            PyImGui.WindowFlags.NoBackground
        ) 
        
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding,0.0,0.0)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)

            
        result = state
        if PyImGui.begin(f"##invisible_window{caption}", flags):
            result = PyImGui.checkbox(f"##floating_checkbox{caption}", state)

        PyImGui.end()
        PyImGui.pop_style_var(2)
        return result
            
        


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