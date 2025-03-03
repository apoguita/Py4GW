from Py4GWCoreLib import *
from collections import defaultdict
from typing import Dict, List, Tuple
import json

MODULE_NAME = "Frame Tester"
json_file_name = "frame_aliases.json"
overlay = Overlay()

#region JSON
def save_entry_to_json(filename: str, frame_hash_id: int, alias: str):
    """Writes or updates an entry in a JSON file."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data: Dict[str, str] = json.load(file)  # Load existing data
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}  # Start fresh if file doesn't exist or is invalid

    data[str(frame_hash_id)] = alias  # Store as str key (JSON requires str keys)

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)  # Save back to file

def get_entry_from_json(filename: str, frame_hash_id: int) -> str | None:
    """Returns the alias for a given frame_hash_id, or None if not found."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data: Dict[str, str] = json.load(file)
        return data.get(str(frame_hash_id))  # Retrieve alias
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def entry_exists(filename: str, frame_hash_id: int) -> bool:
    """Checks if a frame_hash_id exists in the JSON file."""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data: Dict[str, str] = json.load(file)
        return str(frame_hash_id) in data  # Check if key exists
    except (FileNotFoundError, json.JSONDecodeError):
        return False

# endregion

#region config options

class ConfigOptions:
    def __init__(self):
        self.keep_data_updated = False
        self.show_frame_data = False
        self.recolor_frame_tree = True
        self.not_created_color = Utils.RGBToNormal(150, 150, 150, 255)
        self.not_visible_color = Utils.RGBToNormal(180, 0, 0, 255)
        self.no_hash_color = Utils.RGBToNormal(150, 0, 150, 255)
        self.identified_color = Utils.RGBToNormal(200, 180, 0, 255)
        self.base_color = Utils.RGBToNormal(255, 255, 255, 255)

        
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
        self.label = get_entry_from_json(json_file_name, self.frame_hash) or ""
        self.parent = None  # Will be set when building the tree
        self.children = []  # Stores child nodes
        self.show_frame_data = False
        
    def update(self):
        self.frame_obj.get_context()
        self.frame_hash = self.frame_obj.frame_hash
        self.label = get_entry_from_json(json_file_name, self.frame_hash) or ""

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
            elif not self.frame_hash or self.frame_hash == 0:
                return config_options.no_hash_color
            if self.label:
                return config_options.identified_color
            else:
                return config_options.base_color
            
        if self.children:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, choose_frame_color())
            if PyImGui.tree_node(f"Frame:[{self.frame_id}] <{self.frame_hash}> ({self.label}) ##{self.frame_id}"):
                PyImGui.pop_style_color(1)
                PyImGui.same_line(0,-1)
                self.show_frame_data = ImGui.toggle_button(f"Show Data##{self.frame_id}", self.show_frame_data, width=70,height=17)
                if self.frame_id != 0:
                    if config_options.show_frame_data:
                        if PyImGui.collapsing_header(f"Frame#{self.frame_id}Data##{self.frame_id}"):
                            headers = ["Value", "Data"]
                            data = [
                                ("Parent:", self.parent_id),
                                ("Is Visible:", self.frame_obj.is_visible),
                                ("Is Created:", self.frame_obj.is_created),
                            ]
                            ImGui.table("PingHandler info", headers, data)
                PyImGui.separator()
                
                for child in self.children:
                    child.draw()  # Recursively draw children
                PyImGui.tree_pop()  # Close tree node
            else:
                PyImGui.pop_style_color(1)
        else:
            PyImGui.text_colored(f"Frame:[{self.frame_id}] <{self.frame_hash}> ({self.label})",choose_frame_color())  # Leaf node
            PyImGui.same_line(0,-1)
            self.show_frame_data = ImGui.toggle_button(f"Show Data##{self.frame_id}", self.show_frame_data, width=70,height=17)
            if config_options.show_frame_data:
                if PyImGui.collapsing_header(f"Frame#{self.frame_id}Data##{self.frame_id}"):
                    headers = ["Value", "Data"]
                    data = [
                        ("Parent:", self.parent_id),
                        ("Is Visible:", self.frame_obj.is_visible),
                        ("Is Created:", self.frame_obj.is_created),
                    ]
                    ImGui.table("PingHandler info", headers, data)
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



#region InfoWindow

class InfoWindow:
    def __init__(self, frame_obj):
        self.frame = frame_obj #PyUIManager.UIFrame(frame_id)
        self.auto_update = True
        self.draw_frame = True
        self.draw_color :int = Utils.RGBToColor(0, 255, 0, 125)
        self.monitor_callbacks = False
        self.frame_alias = get_entry_from_json(json_file_name, self.frame.frame_hash)  
        self.submit_value = self.frame_alias or "" 
        self.window_name = ""
        self.setWindowName()
        
    def setWindowName(self):
        if self.frame_alias:
            self.window_name = f"Frame[{self.frame.frame_id}] Hash:<{self.frame.frame_hash}> Alias:\"{self.frame_alias}\"##{self.frame.frame_id}"
        else:
            self.window_name = f"Frame[{self.frame.frame_id}] Hash:<{self.frame.frame_hash}>##{self.frame.frame_id}"

          
      
    def DrawFrame(self):
        global overlay
        top = self.frame.position.top_on_screen
        left = self.frame.position.left_on_screen
        bottom = self.frame.position.bottom_on_screen
        right = self.frame.position.right_on_screen
                        
        overlay.BeginDraw()
        overlay.DrawQuadFilled(top, left, top,right, bottom, right, bottom, left,self.draw_color)
        overlay.EndDraw()
        
    def MonitorCallbacks(self):
        pass

    def Draw(self):
        global config_options
        if PyImGui.begin(f"{self.window_name}##{self.frame.frame_id}", True, PyImGui.WindowFlags.AlwaysAutoResize):
            if not config_options.keep_data_updated:
                self.auto_update = PyImGui.checkbox(f"Auto Update##{self.frame.frame_id}", self.auto_update)
            self.draw_frame = PyImGui.checkbox(f"Draw Frame##{self.frame.frame_id}", self.draw_frame)
            if self.draw_frame:
                PyImGui.same_line(0,-1)
                self.draw_color = Utils.TupleToColor(PyImGui.color_edit4("Color", Utils.ColorToTuple(self.draw_color)))
            
            self.monitor_callbacks = PyImGui.checkbox("Monitor Callbacks", self.monitor_callbacks)
            
            if self.auto_update:
                self.frame.get_context()
            if self.draw_frame:
                self.DrawFrame()   
            if self.monitor_callbacks:
                self.MonitorCallbacks()
                
            PyImGui.separator()
            if PyImGui.begin_child("FrameTreeChild",size=(500,600),border=True,flags=PyImGui.WindowFlags.HorizontalScrollbar):
                if PyImGui.begin_tab_bar(f"FrameDebuggerIndividualTabBar##{self.frame.frame_id}"):
                    if PyImGui.begin_tab_item(f"Frame Tree##{self.frame.frame_id}"):
                        PyImGui.text(f"Frame ID: {self.frame.frame_id}")
                        PyImGui.text(f"Frame Hash: {self.frame.frame_hash}")
                        PyImGui.text(f"Alias: {self.frame_alias}")
                        self.submit_value = PyImGui.input_text(f"Alias##Edit{self.frame.frame_id}", self.submit_value)
                        PyImGui.same_line(0,-1)
                        if PyImGui.button(f"Save Alias##{self.frame.frame_id}"):
                            save_entry_to_json(json_file_name, self.frame.frame_hash, self.submit_value)
                            self.frame_alias = get_entry_from_json(json_file_name, self.frame.frame_hash)  
                            self.setWindowName()          
                
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
                            PyImGui.text(f"{i}: {callback.get_address()}")
                        PyImGui.end_tab_item()
                    if PyImGui.begin_tab_item(f"Extra Fields##{self.frame.frame_id}"):
                        PyImGui.text(f"Field1_0x0: {self.frame.field1_0x0}")
                        PyImGui.text(f"Field2_0x4: {self.frame.field2_0x4}")
                        PyImGui.text(f"field3_0xc: {self.frame.field3_0xc}")
                        PyImGui.text(f"field4_0x10: {self.frame.field4_0x10}")
                        PyImGui.text(f"field5_0x14: {self.frame.field5_0x14}")
                        PyImGui.text(f"field7_0x1c: {self.frame.field7_0x1c}")
                        PyImGui.text(f"field10_0x28: {self.frame.field10_0x28}")
                        PyImGui.text(f"field11_0x2c: {self.frame.field11_0x2c}")
                        PyImGui.text(f"field12_0x30: {self.frame.field12_0x30}")
                        PyImGui.text(f"field13_0x34: {self.frame.field13_0x34}")
                        PyImGui.text(f"field14_0x38: {self.frame.field14_0x38}")
                        PyImGui.text(f"field15_0x3c: {self.frame.field15_0x3c}")
                        PyImGui.text(f"field16_0x40: {self.frame.field16_0x40}")
                        PyImGui.text(f"field17_0x44: {self.frame.field17_0x44}")
                        PyImGui.text(f"field18_0x48: {self.frame.field18_0x48}")
                        PyImGui.text(f"field19_0x4c: {self.frame.field19_0x4c}")
                        PyImGui.text(f"field20_0x50: {self.frame.field20_0x50}")
                        PyImGui.text(f"field21_0x54: {self.frame.field21_0x54}")
                        PyImGui.text(f"field22_0x58: {self.frame.field22_0x58}")
                        PyImGui.text(f"field23_0x5c: {self.frame.field23_0x5c}")
                        PyImGui.text(f"field24_0x60: {self.frame.field24_0x60}")
                        PyImGui.text(f"field25_0x64: {self.frame.field25_0x64}")
                        PyImGui.text(f"field26_0x68: {self.frame.field26_0x68}")
                        PyImGui.text(f"field27_0x6c: {self.frame.field27_0x6c}")
                        PyImGui.text(f"field28_0x70: {self.frame.field28_0x70}")
                        PyImGui.text(f"field29_0x74: {self.frame.field29_0x74}")
                        PyImGui.text(f"field30_0x78: {self.frame.field30_0x78}")
                        PyImGui.text(f"field31_0x7c: {self.frame.field31_0x7c}")
                        PyImGui.text(f"field32_0x8c: {self.frame.field32_0x8c}")
                        PyImGui.text(f"field33_0x90: {self.frame.field33_0x90}")
                        PyImGui.text(f"field34_0x94: {self.frame.field34_0x94}")
                        PyImGui.text(f"field35_0x98: {self.frame.field35_0x98}")
                        PyImGui.text(f"field36_0x9c: {self.frame.field36_0x9c}")
                        PyImGui.text(f"field40_0xb8: {self.frame.field40_0xb8}")
                        PyImGui.text(f"field41_0xbc: {self.frame.field41_0xbc}")
                        PyImGui.text(f"field42_0xc0: {self.frame.field42_0xc0}")
                        PyImGui.text(f"field43_0xc4: {self.frame.field43_0xc4}")
                        PyImGui.text(f"field44_0xc8: {self.frame.field44_0xc8}")
                        PyImGui.text(f"field45_0xcc: {self.frame.field45_0xcc}")
                        PyImGui.text(f"field63_0x114: {self.frame.field63_0x114}")
                        PyImGui.text(f"field64_0x118: {self.frame.field64_0x118}")
                        PyImGui.text(f"field65_0x11c: {self.frame.field65_0x11c}")
                        PyImGui.text(f"field73_0x13c: {self.frame.field73_0x13c}")
                        PyImGui.text(f"field74_0x140: {self.frame.field74_0x140}")
                        PyImGui.text(f"field75_0x144: {self.frame.field75_0x144}")
                        PyImGui.text(f"field76_0x148: {self.frame.field76_0x148}")
                        PyImGui.text(f"field77_0x14c: {self.frame.field77_0x14c}")
                        PyImGui.text(f"field78_0x150: {self.frame.field78_0x150}")
                        PyImGui.text(f"field79_0x154: {self.frame.field79_0x154}")
                        PyImGui.text(f"field80_0x158: {self.frame.field80_0x158}")
                        PyImGui.text(f"field81_0x15c: {self.frame.field81_0x15c}")
                        PyImGui.text(f"field82_0x160: {self.frame.field82_0x160}")
                        PyImGui.text(f"field83_0x164: {self.frame.field83_0x164}")
                        PyImGui.text(f"field84_0x168: {self.frame.field84_0x168}")
                        PyImGui.text(f"field85_0x16c: {self.frame.field85_0x16c}")
                        PyImGui.text(f"field86_0x170: {self.frame.field86_0x170}")
                        PyImGui.text(f"field87_0x174: {self.frame.field87_0x174}")
                        PyImGui.text(f"field88_0x178: {self.frame.field88_0x178}")
                        PyImGui.text(f"field89_0x17c: {self.frame.field89_0x17c}")
                        PyImGui.text(f"field90_0x180: {self.frame.field90_0x180}")
                        PyImGui.text(f"field91_0x184: {self.frame.field91_0x184}")
                        PyImGui.text(f"field92_0x188: {self.frame.field92_0x188}")
                        PyImGui.text(f"field93_0x18c: {self.frame.field93_0x18c}")
                        PyImGui.text(f"field94_0x190: {self.frame.field94_0x190}")
                        PyImGui.text(f"field95_0x194: {self.frame.field95_0x194}")
                        PyImGui.text(f"field96_0x198: {self.frame.field96_0x198}")
                        PyImGui.text(f"field97_0x19c: {self.frame.field97_0x19c}")
                        PyImGui.text(f"field98_0x1a0: {self.frame.field98_0x1a0}")
                        PyImGui.text(f"field100_0x1a8: {self.frame.field100_0x1a8}")
                        PyImGui.end_tab_item()
                    PyImGui.end_tab_bar()
                PyImGui.end_child()               
        PyImGui.end()
   
# endregion

#region MainWindow
module_name = "Frame Tester"
window_module = ImGui.WindowModule(
    module_name, 
    window_name="UI Frame Debugger", 
    window_size=(300, 200),
    window_flags=PyImGui.WindowFlags.AlwaysAutoResize
)

frame_array = []
full_tree = FrameTree()




def DrawMainWindow():
    global window_module
    global frame_array
    global full_tree
    global config_options
    
    if config_options.keep_data_updated:
        full_tree.update()
    
    if window_module.first_run:
        PyImGui.set_next_window_size(window_module.window_size[0], window_module.window_size[1])     
        PyImGui.set_next_window_pos(window_module.window_pos[0], window_module.window_pos[1])
        PyImGui.set_next_window_collapsed(window_module.collapse, 0)
        window_module.first_run = False

    if PyImGui.begin(window_module.window_name, window_module.window_flags):
        if PyImGui.begin_tab_bar("FrameDebuggerTabBar"):
            if PyImGui.begin_tab_item("Frame Tree"):
                if PyImGui.collapsing_header("options"):
                    config_options.keep_data_updated = PyImGui.checkbox("Keep all frame Data Updated", config_options.keep_data_updated)
                    ImGui.show_tooltip("This will lower fps!")
                    config_options.show_frame_data = PyImGui.checkbox("Show Frame Data", config_options.show_frame_data)
                    config_options.recolor_frame_tree = PyImGui.checkbox("Recolor Frame Tree", config_options.recolor_frame_tree)

                build_button_text = "Build Frame Tree"
                if frame_array:
                    build_button_text = "Rebuild Frame Tree"
                    
                if PyImGui.button(build_button_text):
                    frame_array = UIManager.GetFrameArray()
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
                
                if PyImGui.begin_child("FrameTreeChild",size=(500,600),border=True,flags=PyImGui.WindowFlags.HorizontalScrollbar):                                        
                    if frame_array:
                        full_tree.draw()
                        
                    PyImGui.end_child()


    PyImGui.end()
    
#endregion


def main():
    DrawMainWindow()


if __name__ == "__main__":
    main()
