#from Py4GWCoreLib import *
import PyImGui
import PyUIManager
import PyImGui
import json
import PyOverlay
from typing import Dict, List, Tuple

MODULE_NAME = "Frame Tester (Basic)"
MODULE_ICON = "Textures/Module_Icons/Frame Tester.png"
json_file_name = ".\\Py4GWCoreLib\\frame_aliases.json"

def RGBToNormal(r, g, b, a):
        """return a normalized RGBA tuple from 0-255 values"""
        return r / 255.0, g / 255.0, b / 255.0, a / 255.0
    
def RGBToColor(r, g, b, a) -> int:
        return (a << 24) | (b << 16) | (g << 8) | r
    
def ColorToTuple(color: int) -> Tuple[float, float, float, float]:
        """Convert a 32-bit integer color (ABGR) to a normalized (0.0 - 1.0) RGBA tuple."""
        a = (color >> 24) & 0xFF  # Extract Alpha (highest 8 bits)
        b = (color >> 16) & 0xFF  # Extract Blue  (next 8 bits)
        g = (color >> 8) & 0xFF   # Extract Green (next 8 bits)
        r = color & 0xFF          # Extract Red   (lowest 8 bits)
        return r / 255.0, g / 255.0, b / 255.0, a / 255.0  # Convert to RGBA float

def TupleToColor(color_tuple: Tuple[float, float, float, float]) -> int:
    """Convert a normalized (0.0 - 1.0) RGBA tuple back to a 32-bit integer color (ABGR)."""
    r = int(color_tuple[0] * 255)  # Convert R back to 0-255
    g = int(color_tuple[1] * 255)  # Convert G back to 0-255
    b = int(color_tuple[2] * 255)  # Convert B back to 0-255
    a = int(color_tuple[3] * 255)  # Convert A back to 0-255
    return RGBToColor(r, g, b, a)  # Encode back as ABGR
    
    
def toggle_button(label: str, v: bool, width:float =0.0, height:float =0.0, disabled:bool =False) -> bool:
        """
        Purpose: Create a toggle button that changes its state and color based on the current state.
        Args:
            label (str): The label of the button.
            v (bool): The current toggle state (True for on, False for off).
        Returns: bool: The new state of the button after being clicked.
        """
        clicked = False

        clicked = PyImGui.button(label, width, height)

        if clicked:
            v = not v
            
        return v
    
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
        


def ConstructFramePath(frame_id: int) -> str:
    """
    Constructs the full path for an offset-based frame by traversing up the parent chain.

    :param frame_id: The frame ID to construct the path for.
    :return: A string path in the format "hashed_parent,offset1,offset2,...", or None if no valid hashed parent is found.
    """
    if frame_id == 0:
        return ""
    try:
        current_frame = PyUIManager.UIFrame(frame_id)
    except Exception as e:
        print(f"[ERROR] Failed to create UIFrame with frame_id={frame_id}: {e}")
        return ""  # Return empty string on error
    
    # If the frame itself has a hash, return it immediately
    if current_frame.frame_hash != 0:
        return str(current_frame.frame_hash)

    path = []
    parent_hash = None

    # Traverse up the parent hierarchy until we find a hashed parent
    while current_frame.frame_id != 0:
        parent_frame = PyUIManager.UIFrame(current_frame.parent_id)

        # Store child offset
        path.append(str(current_frame.child_offset_id))

        # If we found a parent with a hash, stop and use it as the root
        if parent_frame.frame_hash:
            parent_hash = parent_frame.frame_hash
            break

        current_frame = parent_frame  # Move up to the parent

    # If no hashed parent was found, return None (invalid case)
    if parent_hash == 0:
        return ""

    # Construct and return the full path
    return str(parent_hash) + "," + ",".join(reversed(path))
    
def SaveEntryToJSON(filename: str, frame_id: int, alias: str):
    """Writes or updates an entry in a JSON file."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data: Dict[str, str] = json.load(file)  # Load existing data
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}  # Start fresh if file doesn't exist or is invalid

    frame_path = ConstructFramePath(frame_id)

    if frame_path:  # Ensure the path is valid before saving
        data[frame_path] = alias

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)  # Save back to file

def GetEntryFromJSON(filename: str, frame_id: int) -> str:
        """
        Reads an entry from a JSON file by constructing the frame's path.

        :param filename: The JSON file to read from.
        :param frame_id: The frame ID to locate.
        :return: The alias if found, otherwise None.
        """
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)  # Load JSON data
        except (FileNotFoundError, json.JSONDecodeError):
            return "" # Return empty string if file doesn't exist or is invalid

        frame_path = ConstructFramePath(frame_id)
        
        return data.get(frame_path) or ""  # Return the alias if found, otherwise an empty string

#region config options

class ConfigOptions:
    def __init__(self):
        self.keep_data_updated = False
        self.show_frame_data = False
        self.recolor_frame_tree = True
        self.not_created_color = RGBToNormal(150, 150, 150, 255)
        self.not_visible_color = RGBToNormal(180, 0, 0, 255)
        self.no_hash_color = RGBToNormal(150, 0, 150, 255)
        self.identified_color = RGBToNormal(200, 180, 0, 255)
        self.base_color = RGBToNormal(255, 255, 255, 255)
        
config_options = ConfigOptions()

#endregion


#region FrameTree

class FrameNode:
    global config_options
    def __init__(self, frame_id: int, parent_id: int):
        self.frame_id = frame_id
        self.parent_id = parent_id
        self.frame_obj = PyUIManager.UIFrame(self.frame_id)
        self.info_window = InfoWindow(self.frame_obj)
        self.frame_hash = self.frame_obj.frame_hash
        self.child_offset_id = self.frame_obj.child_offset_id
        self.label = GetEntryFromJSON(json_file_name, self.frame_id) or ""
        self.parent = None  # Will be set when building the tree
        self.children = []  # Stores child nodes
        self.show_frame_data = False
        
    def update(self):
        self.frame_obj.get_context()
        self.frame_hash = self.frame_obj.frame_hash
        self.label = GetEntryFromJSON(json_file_name, self.frame_id) or ""

    def get_parent(self):
        """Returns the parent node of this frame."""
        return self.parent

    def get_children(self):
        """Returns a list of all child nodes."""
        return self.children

    def draw(self):
        """Recursively renders the tree hierarchy using PyImGui."""
        def choose_frame_color():
            if not self.frame_obj.is_created:
                return config_options.not_created_color
            elif not self.frame_obj.is_visible:
                return config_options.not_visible_color
            elif self.label:
                return config_options.identified_color
            elif not self.frame_hash or self.frame_hash == 0:
                return config_options.no_hash_color
            else:
                return config_options.base_color
            
        if self.children:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, choose_frame_color())
            if PyImGui.tree_node(f"Frame:[{self.frame_id}] <{self.frame_hash}> ({self.label}) ##{self.frame_id}"):
                PyImGui.pop_style_color(1)
                PyImGui.same_line(0,-1)
                self.show_frame_data = toggle_button(f"Show Data##{self.frame_id}", self.show_frame_data, width=70,height=17)
                if self.frame_id != 0:
                    if config_options.show_frame_data:
                        if PyImGui.collapsing_header(f"Frame#{self.frame_id}Data##{self.frame_id}"):
                            headers = ["Value", "Data"]
                            data = [
                                ("Parent:", self.parent_id),
                                ("Is Visible:", self.frame_obj.is_visible),
                                ("Is Created:", self.frame_obj.is_created),
                            ]
                            table("frametester info##{self.frame_id}", headers, data)
                PyImGui.separator()
                
                for child in self.children:
                    child.draw()  # Recursively draw children
                PyImGui.tree_pop()  # Close tree node
            else:
                PyImGui.pop_style_color(1)
        else:
            PyImGui.text_colored(f"Frame:[{self.frame_id}] <{self.frame_hash}> ({self.label})",choose_frame_color())  # Leaf node
            PyImGui.same_line(0,-1)
            self.show_frame_data = toggle_button(f"Show Data##{self.frame_id}", self.show_frame_data, width=70,height=17)
            if config_options.show_frame_data:
                if PyImGui.collapsing_header(f"Frame#{self.frame_id}Data##{self.frame_id}"):
                    headers = ["Value", "Data"]
                    data = [
                        ("Parent:", self.parent_id),
                        ("Is Visible:", self.frame_obj.is_visible),
                        ("Is Created:", self.frame_obj.is_created),
                    ]
                    table("frametester info##{self.frame_id}", headers, data)
            PyImGui.separator()
                    
        if self.show_frame_data:
            self.info_window.Draw()


class FrameTree:
    def __init__(self):
        self.nodes = {}  # Stores frame_id -> FrameNode
        self.root = None  # Root of the tree
        
    def update(self):
        """Updates all nodes in the tree."""
        for node in self.nodes.values():
            node.update()

    def build_tree(self, frame_list: List[int]):
        """
        Builds the tree from a list of frame IDs.
        Uses PyUIManager.UIFrame to retrieve parent information.
        """
        # Step 1: Create nodes
        for frame_id in frame_list:
            frame_obj = PyUIManager.UIFrame(frame_id)  # Create UIFrame instance
            parent_id = frame_obj.parent_id  # Extract parent ID
            self.nodes[frame_id] = FrameNode(frame_id, parent_id)

        # Step 2: Assign parents and children
        for frame_id, node in self.nodes.items():
            if node.parent_id == 0:
                self.root = node  # Root node
            elif node.parent_id in self.nodes:
                node.parent = self.nodes[node.parent_id]  # Set parent reference
                self.nodes[node.parent_id].children.append(node)  # Add as child

    def get_node(self, frame_id: int):
        """Retrieves a node by its ID."""
        return self.nodes.get(frame_id, None)

    def draw(self):
        """Draws the entire hierarchy using PyImGui."""
        if self.root:
            self.root.draw()



#end region

_overlay = PyOverlay.Overlay()

def GetFrameArray():
    """
    Get the frame array.

    :return: list: The frame array.
    """
    return PyUIManager.UIManager.get_frame_array()

def IsFrameCreated(frame_id):
    """
    Check if a frame is created.

    :param frame_id: The ID of the frame.
    :return: bool: True if the frame is created, False otherwise.
    """
    return PyUIManager.UIFrame(frame_id).is_created

def IsVisible(frame_id):
    """
    Check if a frame is visible.

    :param frame_id: The ID of the frame.
    :return: bool: True if the frame is visible, False otherwise.
    """
    return PyUIManager.UIFrame(frame_id).is_visible

def FrameExists(frame_id):
    """
    Check if a frame exists.

    :param frame_id: The ID of the frame.
    :return: bool: True if the frame exists, False otherwise.
    """
    frame_aray = GetFrameArray()
    if frame_id not in frame_aray:
        return False
    return IsFrameCreated(frame_id) and IsVisible(frame_id)

def GetFrameCoords(frame_id):
    """
    Get the coordinates of a frame.

    :param frame_id: The ID of the frame.
    :return: top, left, bottom, right coordinates of the frame.
    """
    frame = PyUIManager.UIFrame(frame_id)
    top = frame.position.top_on_screen
    left = frame.position.left_on_screen
    bottom = frame.position.bottom_on_screen
    right = frame.position.right_on_screen
    return left,top, right, bottom

def DrawFrame(frame_id:int, draw_color:int):
    global _overlay
    """
    Draw a frame on the UI.

    :param frame_id: The ID of the frame.
    """
    if not FrameExists(frame_id):
        return
    
    left, top, right, bottom = GetFrameCoords(frame_id)
    p1 = PyOverlay.Point2D(left, top)
    p2 = PyOverlay.Point2D(right, top)
    p3 = PyOverlay.Point2D(right, bottom)
    p4 = PyOverlay.Point2D(left, bottom)
    _overlay.BeginDraw()
    _overlay.DrawQuadFilled(p1,p2,p3,p4, draw_color)
    _overlay.EndDraw()
    
def FrameClick(frame_id):
    """
    Click a frame on the UI.

    :param frame_id: The ID of the frame.
    """
    if not FrameExists(frame_id):
        return
    PyUIManager.UIManager.button_click(frame_id)
    
def TestMouseAction(frame_id, current_state, wparam_value, lparam_value=0):
    """
    Test mouse action on a frame.

    :param frame_id: The ID of the frame.
    :param current_state: The current state of the mouse.
    :param wparam_value: The wparam value.
    """
    if not FrameExists(frame_id):
        return
    PyUIManager.UIManager.test_mouse_action(frame_id, current_state, wparam_value, lparam_value)
    
def TestMouseClickAction(frame_id, current_state, wparam_value, lparam_value=0):
    """
    Test mouse click action on a frame.

    :param frame_id: The ID of the frame.
    :param current_state: The current state of the mouse.
    :param wparam_value: The wparam value.
    """
    if not FrameExists(frame_id):
        return
    PyUIManager.UIManager.test_mouse_click_action(frame_id, current_state, wparam_value, lparam_value)

#region InfoWindow
double_action = False

class InfoWindow:
    from PyUIManager import UIFrame
    def __init__(self, frame_obj:UIFrame):
        self.frame = frame_obj 
        self.auto_update = True
        self.draw_frame = True
        self.draw_color :int = RGBToColor(0, 255, 0, 125)
        self.monitor_callbacks = False
        self.frame_alias = GetEntryFromJSON(json_file_name, self.frame.frame_id)  
        self.submit_value = self.frame_alias or "" 
        self.window_name = ""
        self.setWindowName()
        self.current_state = 0
        self.wparam = 0
        self.lparam = 0
        
    def setWindowName(self):
        if self.frame_alias:
            self.window_name = f"Frame[{self.frame.frame_id}] Hash:<{self.frame.frame_hash}> Alias:\"{self.frame_alias}\"##{self.frame.frame_id}"
        else:
            self.window_name = f"Frame[{self.frame.frame_id}] Hash:<{self.frame.frame_hash}>##{self.frame.frame_id}"

          
      
    def DrawFrame(self):
        DrawFrame(self.frame.frame_id, self.draw_color)
        
    def MonitorCallbacks(self):
        pass
    
    def to_hex(self,value: int) -> str:
        return f"0x{value:X}"
    
    def to_bin(self,value: int) -> str:
        return bin(value)
    
    def to_char(self,value: int) -> str:
        byte_values = value.to_bytes(4, byteorder="little", signed=False)
        return "".join(chr(b) if 32 <= b <= 126 else "." for b in byte_values)


    
    def Draw(self):
        global config_options
        global full_tree
        global double_action
        if PyImGui.begin(f"{self.window_name}##{self.frame.frame_id}", True, PyImGui.WindowFlags.AlwaysAutoResize):
            if not config_options.keep_data_updated:
                self.auto_update = PyImGui.checkbox(f"Auto Update##{self.frame.frame_id}", self.auto_update)
            self.draw_frame = PyImGui.checkbox(f"Draw Frame##{self.frame.frame_id}", self.draw_frame)
            if self.draw_frame:
                PyImGui.same_line(0,-1)
                self.draw_color = TupleToColor(PyImGui.color_edit4("Color", ColorToTuple(self.draw_color)))
            
            self.monitor_callbacks = PyImGui.checkbox("Monitor Callbacks", self.monitor_callbacks)
            
            if self.auto_update:
                self.frame.get_context()
            if self.draw_frame:
                self.DrawFrame()   
            if self.monitor_callbacks:
                self.MonitorCallbacks()
                
            PyImGui.separator()
            if PyImGui.begin_child("FrameTreeChild",size=(1000,800),border=True,flags=PyImGui.WindowFlags.HorizontalScrollbar):
                if PyImGui.begin_tab_bar(f"FrameDebuggerIndividualTabBar##{self.frame.frame_id}"):
                    if PyImGui.begin_tab_item(f"Frame Tree##{self.frame.frame_id}"):
                        PyImGui.text(f"Frame ID: {self.frame.frame_id}")
                        PyImGui.text(f"Frame Hash: {self.frame.frame_hash}")
                        PyImGui.text(f"Alias: {self.frame_alias}")
                        
                        self.submit_value = PyImGui.input_text(f"Alias##Edit{self.frame.frame_id}", self.submit_value)
                        PyImGui.same_line(0,-1)
                        if PyImGui.button(f"Save Alias##{self.frame.frame_id}"):
                            SaveEntryToJSON(json_file_name, self.frame.frame_id, self.submit_value)
                            self.frame_alias = GetEntryFromJSON(json_file_name, self.frame.frame_id)  
                            self.setWindowName()          

                        if PyImGui.button(f"Click on frame{self.frame.frame_id}##click{self.frame.frame_id}"):
                            FrameClick(self.frame.frame_id)
                            print (f"Clicked on frame {self.frame.frame_id}")
                            
                        PyImGui.separator()
                        self.current_state = PyImGui.input_int(f"Current State##{self.frame.frame_id}", self.current_state)
                        self.wparam = PyImGui.input_int(f"wParam##{self.frame.frame_id}", self.wparam)
                        self.lparam = PyImGui.input_int(f"lParam##{self.frame.frame_id}", self.lparam)
                        if PyImGui.button((f"test mouse action##{self.frame.frame_id}")):
                            TestMouseAction(self.frame.frame_id, self.current_state, self.wparam, self.lparam)
                            self.current_state += 1
                            if self.current_state in (6, 10, 8):
                                self.current_state += 1
                            if self.current_state > 10:
                                self.current_state = 0
                                self.wparam += 1
                                if self.wparam > 10:
                                    self.wparam = 0
                                    self.lparam += 1
                                    
                            print (f"Tested on frame {self.frame.frame_id}")
                            
                        if PyImGui.button((f"test mouse click action##{self.frame.frame_id}")):
                            TestMouseClickAction(self.frame.frame_id, self.current_state, self.wparam, self.lparam)
                            self.current_state += 1
                            #if self.current_state in (6, 10, 8):
                            #    self.current_state += 1
                            if self.current_state > 10:
                                self.current_state = 0
                                self.wparam += 1
                                if self.wparam > 10:
                                    self.wparam = 0
                                    self.lparam += 1
                                    
                            print (f"Tested on frame {self.frame.frame_id}")


                        PyImGui.text(f"Parent ID: {self.frame.parent_id}")
                        PyImGui.text(f"Visibility Flags: {self.frame.visibility_flags}")
                        PyImGui.text(f"Is Visible: {self.frame.is_visible}")
                        PyImGui.text(f"Is Created: {self.frame.is_created}")
                        PyImGui.text(f"Type: {self.frame.type}")
                        PyImGui.text(f"Template Type: {self.frame.template_type}")
                        PyImGui.text(f"Frame Layout: {self.frame.frame_layout}")
                        PyImGui.text(f"Child Offset ID: {self.frame.child_offset_id}")
                        PyImGui.end_tab_item()
                    if PyImGui.begin_tab_item(f"Position##{self.frame.frame_id}"):
                        PyImGui.text(f"Top: {self.frame.position.top}")
                        PyImGui.text(f"Left: {self.frame.position.left}")
                        PyImGui.text(f"Bottom: {self.frame.position.bottom}")
                        PyImGui.text(f"Right: {self.frame.position.right}")
                        PyImGui.text(f"Content Top: {self.frame.position.content_top}")
                        PyImGui.text(f"Content Left: {self.frame.position.content_left}")
                        PyImGui.text(f"Content Bottom: {self.frame.position.content_bottom}")
                        PyImGui.text(f"Content Right: {self.frame.position.content_right}")
                        PyImGui.text(f"Unknown: {self.frame.position.unknown}")
                        PyImGui.text(f"Scale Factor: {self.frame.position.scale_factor}")
                        PyImGui.text(f"Viewport Width: {self.frame.position.viewport_width}")
                        PyImGui.text(f"Viewport Height: {self.frame.position.viewport_height}")
                        PyImGui.text(f"Screen Top: {self.frame.position.screen_top}")
                        PyImGui.text(f"Screen Left: {self.frame.position.screen_left}")
                        PyImGui.text(f"Screen Bottom: {self.frame.position.screen_bottom}")
                        PyImGui.text(f"Screen Right: {self.frame.position.screen_right}")
                        PyImGui.text(f"Top on Screen: {self.frame.position.top_on_screen}")
                        PyImGui.text(f"Left on Screen: {self.frame.position.left_on_screen}")
                        PyImGui.text(f"Bottom on Screen: {self.frame.position.bottom_on_screen}")
                        PyImGui.text(f"Right on Screen: {self.frame.position.right_on_screen}")
                        PyImGui.text(f"Width on Screen: {self.frame.position.width_on_screen}")
                        PyImGui.text(f"Height on Screen: {self.frame.position.height_on_screen}")
                        PyImGui.text(f"Viewport Scale X: {self.frame.position.viewport_scale_x}")
                        PyImGui.text(f"Viewport Scale Y: {self.frame.position.viewport_scale_y}")
                        PyImGui.end_tab_item()
                    if PyImGui.begin_tab_item(f"Relation##{self.frame.frame_id}"):
                        PyImGui.text(f"Parent ID: {self.frame.relation.parent_id}")
                        PyImGui.text(f"Field67_0x124: {self.frame.relation.field67_0x124}")
                        PyImGui.text(f"Field68_0x128: {self.frame.relation.field68_0x128}")
                        PyImGui.text(f"Frame Hash ID: {self.frame.relation.frame_hash_id}")
                        if PyImGui.collapsing_header("Siblings"):
                            for i, sibling in enumerate(self.frame.relation.siblings):
                                PyImGui.text(f"Siblings[{i}]: {sibling}")
                        PyImGui.end_tab_item()
                    if PyImGui.begin_tab_item(f"Callbacks##{self.frame.frame_id}"):
                        for i, callback in enumerate(self.frame.frame_callbacks):
                            PyImGui.text(f"{i}: {callback.get_address()} - Hex({self.to_hex(callback.get_address())})")


                        PyImGui.end_tab_item()

                    if PyImGui.begin_tab_item(f"Extra Fields##{self.frame.frame_id}"):
                        # Prepare data list
                        data = []
                        
                        # Define headers
                        headers = ["Field", "Dec", "Hex", "Bin", "Char"]
                        
                        data = [
                            ("Field1_0x0", str(self.frame.field1_0x0), self.to_hex(self.frame.field1_0x0), self.to_bin(self.frame.field1_0x0), self.to_char(self.frame.field1_0x0)),
                            ("Field2_0x4", str(self.frame.field2_0x4), self.to_hex(self.frame.field2_0x4), self.to_bin(self.frame.field2_0x4), self.to_char(self.frame.field2_0x4)),

                            ("Field3_0xC", str(self.frame.field3_0xc), self.to_hex(self.frame.field3_0xc), self.to_bin(self.frame.field3_0xc), self.to_char(self.frame.field3_0xc)),
                            ("Field4_0x10", str(self.frame.field4_0x10), self.to_hex(self.frame.field4_0x10), self.to_bin(self.frame.field4_0x10), self.to_char(self.frame.field4_0x10)),
                            ("Field5_0x14", str(self.frame.field5_0x14), self.to_hex(self.frame.field5_0x14), self.to_bin(self.frame.field5_0x14), self.to_char(self.frame.field5_0x14)),

                            ("Field7_0x1C", str(self.frame.field7_0x1c), self.to_hex(self.frame.field7_0x1c), self.to_bin(self.frame.field7_0x1c), self.to_char(self.frame.field7_0x1c)),

                            ("Field10_0x28", str(self.frame.field10_0x28), self.to_hex(self.frame.field10_0x28), self.to_bin(self.frame.field10_0x28), self.to_char(self.frame.field10_0x28)),
                            ("Field11_0x2C", str(self.frame.field11_0x2c), self.to_hex(self.frame.field11_0x2c), self.to_bin(self.frame.field11_0x2c), self.to_char(self.frame.field11_0x2c)),
                            ("Field12_0x30", str(self.frame.field12_0x30), self.to_hex(self.frame.field12_0x30), self.to_bin(self.frame.field12_0x30), self.to_char(self.frame.field12_0x30)),
                            ("Field13_0x34", str(self.frame.field13_0x34), self.to_hex(self.frame.field13_0x34), self.to_bin(self.frame.field13_0x34), self.to_char(self.frame.field13_0x34)),
                            ("Field14_0x38", str(self.frame.field14_0x38), self.to_hex(self.frame.field14_0x38), self.to_bin(self.frame.field14_0x38), self.to_char(self.frame.field14_0x38)),
                            ("Field15_0x3C", str(self.frame.field15_0x3c), self.to_hex(self.frame.field15_0x3c), self.to_bin(self.frame.field15_0x3c), self.to_char(self.frame.field15_0x3c)),
                            ("Field16_0x40", str(self.frame.field16_0x40), self.to_hex(self.frame.field16_0x40), self.to_bin(self.frame.field16_0x40), self.to_char(self.frame.field16_0x40)),
                            ("Field17_0x44", str(self.frame.field17_0x44), self.to_hex(self.frame.field17_0x44), self.to_bin(self.frame.field17_0x44), self.to_char(self.frame.field17_0x44)),
                            ("Field18_0x48", str(self.frame.field18_0x48), self.to_hex(self.frame.field18_0x48), self.to_bin(self.frame.field18_0x48), self.to_char(self.frame.field18_0x48)),
                            ("Field19_0x4C", str(self.frame.field19_0x4c), self.to_hex(self.frame.field19_0x4c), self.to_bin(self.frame.field19_0x4c), self.to_char(self.frame.field19_0x4c)),
                            ("Field20_0x50", str(self.frame.field20_0x50), self.to_hex(self.frame.field20_0x50), self.to_bin(self.frame.field20_0x50), self.to_char(self.frame.field20_0x50)),
                            ("Field21_0x54", str(self.frame.field21_0x54), self.to_hex(self.frame.field21_0x54), self.to_bin(self.frame.field21_0x54), self.to_char(self.frame.field21_0x54)),
                            ("Field22_0x58", str(self.frame.field22_0x58), self.to_hex(self.frame.field22_0x58), self.to_bin(self.frame.field22_0x58), self.to_char(self.frame.field22_0x58)),
                            ("Field23_0x5C", str(self.frame.field23_0x5c), self.to_hex(self.frame.field23_0x5c), self.to_bin(self.frame.field23_0x5c), self.to_char(self.frame.field23_0x5c)),
                            ("Field24_0x60", str(self.frame.field24_0x60), self.to_hex(self.frame.field24_0x60), self.to_bin(self.frame.field24_0x60), self.to_char(self.frame.field24_0x60)),

                            ("Field24a_0x64", str(self.frame.field24a_0x64), self.to_hex(self.frame.field24a_0x64), self.to_bin(self.frame.field24a_0x64), self.to_char(self.frame.field24a_0x64)),
                            ("Field24b_0x68", str(self.frame.field24b_0x68), self.to_hex(self.frame.field24b_0x68), self.to_bin(self.frame.field24b_0x68), self.to_char(self.frame.field24b_0x68)),

                            ("Field25_0x6C", str(self.frame.field25_0x6c), self.to_hex(self.frame.field25_0x6c), self.to_bin(self.frame.field25_0x6c), self.to_char(self.frame.field25_0x6c)),
                            ("Field26_0x70", str(self.frame.field26_0x70), self.to_hex(self.frame.field26_0x70), self.to_bin(self.frame.field26_0x70), self.to_char(self.frame.field26_0x70)),
                            ("Field27_0x74", str(self.frame.field27_0x74), self.to_hex(self.frame.field27_0x74), self.to_bin(self.frame.field27_0x74), self.to_char(self.frame.field27_0x74)),
                            ("Field28_0x78", str(self.frame.field28_0x78), self.to_hex(self.frame.field28_0x78), self.to_bin(self.frame.field28_0x78), self.to_char(self.frame.field28_0x78)),
                            ("Field29_0x7C", str(self.frame.field29_0x7c), self.to_hex(self.frame.field29_0x7c), self.to_bin(self.frame.field29_0x7c), self.to_char(self.frame.field29_0x7c)),
                            ("Field30_0x80", str(self.frame.field30_0x80), self.to_hex(self.frame.field30_0x80), self.to_bin(self.frame.field30_0x80), self.to_char(self.frame.field30_0x80)),
                        ]

                        parameter_list = self.frame.field31_0x84
                        for i, parameter in enumerate(parameter_list):
                            data.append((f"Field31_0x84[{i}]",
                                        str(parameter),
                                        self.to_hex(parameter),
                                        self.to_bin(parameter),
                                        self.to_char(parameter)))

                        data.extend([
                            ("Field32_0x94", str(self.frame.field32_0x94), self.to_hex(self.frame.field32_0x94), self.to_bin(self.frame.field32_0x94), self.to_char(self.frame.field32_0x94)),
                            ("Field33_0x98", str(self.frame.field33_0x98), self.to_hex(self.frame.field33_0x98), self.to_bin(self.frame.field33_0x98), self.to_char(self.frame.field33_0x98)),
                            ("Field34_0x9C", str(self.frame.field34_0x9c), self.to_hex(self.frame.field34_0x9c), self.to_bin(self.frame.field34_0x9c), self.to_char(self.frame.field34_0x9c)),
                            ("Field35_0xA0", str(self.frame.field35_0xa0), self.to_hex(self.frame.field35_0xa0), self.to_bin(self.frame.field35_0xa0), self.to_char(self.frame.field35_0xa0)),
                            ("Field36_0xA4", str(self.frame.field36_0xa4), self.to_hex(self.frame.field36_0xa4), self.to_bin(self.frame.field36_0xa4), self.to_char(self.frame.field36_0xa4)),

                            ("Field40_0xC0", str(self.frame.field40_0xc0), self.to_hex(self.frame.field40_0xc0), self.to_bin(self.frame.field40_0xc0), self.to_char(self.frame.field40_0xc0)),
                            ("Field41_0xC4", str(self.frame.field41_0xc4), self.to_hex(self.frame.field41_0xc4), self.to_bin(self.frame.field41_0xc4), self.to_char(self.frame.field41_0xc4)),
                            ("Field42_0xC8", str(self.frame.field42_0xc8), self.to_hex(self.frame.field42_0xc8), self.to_bin(self.frame.field42_0xc8), self.to_char(self.frame.field42_0xc8)),
                            ("Field43_0xCC", str(self.frame.field43_0xcc), self.to_hex(self.frame.field43_0xcc), self.to_bin(self.frame.field43_0xcc), self.to_char(self.frame.field43_0xcc)),
                            ("Field44_0xD0", str(self.frame.field44_0xd0), self.to_hex(self.frame.field44_0xd0), self.to_bin(self.frame.field44_0xd0), self.to_char(self.frame.field44_0xd0)),
                            ("Field45_0xD4", str(self.frame.field45_0xd4), self.to_hex(self.frame.field45_0xd4), self.to_bin(self.frame.field45_0xd4), self.to_char(self.frame.field45_0xd4)),

                            ("Field63_0x11C", str(self.frame.field63_0x11c), self.to_hex(self.frame.field63_0x11c), self.to_bin(self.frame.field63_0x11c), self.to_char(self.frame.field63_0x11c)),
                            ("Field64_0x120", str(self.frame.field64_0x120), self.to_hex(self.frame.field64_0x120), self.to_bin(self.frame.field64_0x120), self.to_char(self.frame.field64_0x120)),
                            ("Field65_0x124", str(self.frame.field65_0x124), self.to_hex(self.frame.field65_0x124), self.to_bin(self.frame.field65_0x124), self.to_char(self.frame.field65_0x124)),

                            ("Field73_0x144", str(self.frame.field73_0x144), self.to_hex(self.frame.field73_0x144), self.to_bin(self.frame.field73_0x144), self.to_char(self.frame.field73_0x144)),
                            ("Field74_0x148", str(self.frame.field74_0x148), self.to_hex(self.frame.field74_0x148), self.to_bin(self.frame.field74_0x148), self.to_char(self.frame.field74_0x148)),
                            ("Field75_0x14C", str(self.frame.field75_0x14c), self.to_hex(self.frame.field75_0x14c), self.to_bin(self.frame.field75_0x14c), self.to_char(self.frame.field75_0x14c)),
                            ("Field76_0x150", str(self.frame.field76_0x150), self.to_hex(self.frame.field76_0x150), self.to_bin(self.frame.field76_0x150), self.to_char(self.frame.field76_0x150)),
                            ("Field77_0x154", str(self.frame.field77_0x154), self.to_hex(self.frame.field77_0x154), self.to_bin(self.frame.field77_0x154), self.to_char(self.frame.field77_0x154)),
                            ("Field78_0x158", str(self.frame.field78_0x158), self.to_hex(self.frame.field78_0x158), self.to_bin(self.frame.field78_0x158), self.to_char(self.frame.field78_0x158)),
                            ("Field79_0x15C", str(self.frame.field79_0x15c), self.to_hex(self.frame.field79_0x15c), self.to_bin(self.frame.field79_0x15c), self.to_char(self.frame.field79_0x15c)),
                            ("Field80_0x160", str(self.frame.field80_0x160), self.to_hex(self.frame.field80_0x160), self.to_bin(self.frame.field80_0x160), self.to_char(self.frame.field80_0x160)),
                            ("Field81_0x164", str(self.frame.field81_0x164), self.to_hex(self.frame.field81_0x164), self.to_bin(self.frame.field81_0x164), self.to_char(self.frame.field81_0x164)),
                            ("Field82_0x168", str(self.frame.field82_0x168), self.to_hex(self.frame.field82_0x168), self.to_bin(self.frame.field82_0x168), self.to_char(self.frame.field82_0x168)),
                            ("Field83_0x16C", str(self.frame.field83_0x16c), self.to_hex(self.frame.field83_0x16c), self.to_bin(self.frame.field83_0x16c), self.to_char(self.frame.field83_0x16c)),
                            ("Field84_0x170", str(self.frame.field84_0x170), self.to_hex(self.frame.field84_0x170), self.to_bin(self.frame.field84_0x170), self.to_char(self.frame.field84_0x170)),
                            ("Field85_0x174", str(self.frame.field85_0x174), self.to_hex(self.frame.field85_0x174), self.to_bin(self.frame.field85_0x174), self.to_char(self.frame.field85_0x174)),
                            ("Field86_0x178", str(self.frame.field86_0x178), self.to_hex(self.frame.field86_0x178), self.to_bin(self.frame.field86_0x178), self.to_char(self.frame.field86_0x178)),
                            ("Field87_0x17C", str(self.frame.field87_0x17c), self.to_hex(self.frame.field87_0x17c), self.to_bin(self.frame.field87_0x17c), self.to_char(self.frame.field87_0x17c)),
                            ("Field88_0x180", str(self.frame.field88_0x180), self.to_hex(self.frame.field88_0x180), self.to_bin(self.frame.field88_0x180), self.to_char(self.frame.field88_0x180)),
                            ("Field89_0x184", str(self.frame.field89_0x184), self.to_hex(self.frame.field89_0x184), self.to_bin(self.frame.field89_0x184), self.to_char(self.frame.field89_0x184)),
                            ("Field90_0x188", str(self.frame.field90_0x188), self.to_hex(self.frame.field90_0x188), self.to_bin(self.frame.field90_0x188), self.to_char(self.frame.field90_0x188)),

                            ("Field92_0x190", str(self.frame.field92_0x190), self.to_hex(self.frame.field92_0x190), self.to_bin(self.frame.field92_0x190), self.to_char(self.frame.field92_0x190)),
                            ("Field93_0x194", str(self.frame.field93_0x194), self.to_hex(self.frame.field93_0x194), self.to_bin(self.frame.field93_0x194), self.to_char(self.frame.field93_0x194)),
                            ("Field94_0x198", str(self.frame.field94_0x198), self.to_hex(self.frame.field94_0x198), self.to_bin(self.frame.field94_0x198), self.to_char(self.frame.field94_0x198)),
                            ("Field95_0x19C", str(self.frame.field95_0x19c), self.to_hex(self.frame.field95_0x19c), self.to_bin(self.frame.field95_0x19c), self.to_char(self.frame.field95_0x19c)),
                            ("Field96_0x1A0", str(self.frame.field96_0x1a0), self.to_hex(self.frame.field96_0x1a0), self.to_bin(self.frame.field96_0x1a0), self.to_char(self.frame.field96_0x1a0)),
                            ("Field97_0x1A4", str(self.frame.field97_0x1a4), self.to_hex(self.frame.field97_0x1a4), self.to_bin(self.frame.field97_0x1a4), self.to_char(self.frame.field97_0x1a4)),
                            ("Field98_0x1A8", str(self.frame.field98_0x1a8), self.to_hex(self.frame.field98_0x1a8), self.to_bin(self.frame.field98_0x1a8), self.to_char(self.frame.field98_0x1a8)),

                            ("Field100_0x1B0", str(self.frame.field100_0x1b0), self.to_hex(self.frame.field100_0x1b0), self.to_bin(self.frame.field100_0x1b0), self.to_char(self.frame.field100_0x1b0)),
                            ("Field101_0x1B4", str(self.frame.field101_0x1b4), self.to_hex(self.frame.field101_0x1b4), self.to_bin(self.frame.field101_0x1b4), self.to_char(self.frame.field101_0x1b4)),
                            ("Field102_0x1B8", str(self.frame.field102_0x1b8), self.to_hex(self.frame.field102_0x1b8), self.to_bin(self.frame.field102_0x1b8), self.to_char(self.frame.field102_0x1b8)),
                            ("Field103_0x1BC", str(self.frame.field103_0x1bc), self.to_hex(self.frame.field103_0x1bc), self.to_bin(self.frame.field103_0x1bc), self.to_char(self.frame.field103_0x1bc)),
                            ("Field104_0x1C0", str(self.frame.field104_0x1c0), self.to_hex(self.frame.field104_0x1c0), self.to_bin(self.frame.field104_0x1c0), self.to_char(self.frame.field104_0x1c0)),
                            ("Field105_0x1C4", str(self.frame.field105_0x1c4), self.to_hex(self.frame.field105_0x1c4), self.to_bin(self.frame.field105_0x1c4), self.to_char(self.frame.field105_0x1c4)),
                        ])

                        
                        
    
                        table(f"Frame Data##{self.frame.frame_id}", headers, data)

                        PyImGui.end_tab_item()
                    PyImGui.end_tab_bar()
                PyImGui.end_child()               
        PyImGui.end()
   
# endregion

#region MainWindow
module_name = "Frame Tester"

frame_array = []
full_tree = FrameTree()




def DrawMainWindow():
    global frame_array
    global full_tree
    global config_options
    
    if config_options.keep_data_updated:
        full_tree.update()
    
    

    if PyImGui.begin("frame tester window", True, PyImGui.WindowFlags.AlwaysAutoResize):
        if PyImGui.begin_tab_bar("FrameDebuggerTabBar"):
            if PyImGui.begin_tab_item("Frame Tree"):
                if PyImGui.collapsing_header("options"):
                    config_options.keep_data_updated = PyImGui.checkbox("Keep all frame Data Updated", config_options.keep_data_updated)
                    #ImGui.show_tooltip("This will lower fps!")
                    config_options.show_frame_data = PyImGui.checkbox("Show Frame Data", config_options.show_frame_data)
                    config_options.recolor_frame_tree = PyImGui.checkbox("Recolor Frame Tree", config_options.recolor_frame_tree)

                build_button_text = "Build Frame Tree"
                if frame_array:
                    build_button_text = "Rebuild Frame Tree"
                    
                if PyImGui.button(build_button_text):
                    frame_array = GetFrameArray()
                    full_tree.build_tree(frame_array)    
                    
                PyImGui.text_colored("Not Created", config_options.not_created_color)
                PyImGui.same_line(0,-1)
                PyImGui.text_colored("Not Visible", config_options.not_visible_color)
                PyImGui.same_line(0,-1)
                PyImGui.text_colored("No Hash", config_options.no_hash_color)
                PyImGui.same_line(0,-1)
                PyImGui.text_colored("Identified", config_options.identified_color)
                PyImGui.same_line(0,-1)
                PyImGui.text_colored("Base", config_options.base_color)
                
                PyImGui.separator()
                
                if PyImGui.begin_child("FrameTreeChild",size=(900,800),border=True,flags=PyImGui.WindowFlags.HorizontalScrollbar):                                        
                    if frame_array:
                        full_tree.draw()
                        
                    PyImGui.end_child()


    PyImGui.end()
    
#endregion

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = (1.0,0.78, 0.4,1.0)

    PyImGui.text_colored("UI Frame Tester", title_color)

    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("Frame Tester with no Unnecessary Imports")

    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color)
    PyImGui.bullet_text("Frame Tree: Hierarchical visualization of all UI elements (AdvUI)")
    PyImGui.bullet_text("Visual Debugging: Real-time screen highlighting of selected UI Frames")
    PyImGui.bullet_text("State Tracking: Color-coded indicators for Visible, Hidden, and Uncreated frames")
    PyImGui.bullet_text("Alias Manager: Map frame hashes to human-readable names via JSON")
    PyImGui.bullet_text("Detail Inspector: View frame IDs, parentage, child counts, and internal hashes")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color)
    PyImGui.bullet_text("Developed by Apo")

    PyImGui.end_tooltip()



def main():
    DrawMainWindow()


if __name__ == "__main__":
    main()
