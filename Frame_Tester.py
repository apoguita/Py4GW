from Py4GWCoreLib import *
from collections import defaultdict
from typing import Dict, List, Tuple
import json

MODULE_NAME = "Frame Tester"

json_file_name = "frame_aliases.json"

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
#region InfoWindow

class InfoWindow:
    def __init__(self, frame_id):
        self.frame = PyUIManager.UIFrame(frame_id)
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
        if PyImGui.begin(self.window_name):
            self.auto_update = PyImGui.checkbox("Auto Update", self.auto_update)
            self.draw_frame = PyImGui.checkbox("Draw Frame", self.draw_frame)
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
            
            PyImGui.text(f"Frame ID: {self.frame.frame_id}")
            PyImGui.text(f"Frame Hash: {self.frame.frame_hash}")
            PyImGui.text(f"Alias: {self.frame_alias}")
            self.submit_value = PyImGui.input_text("Alias", self.submit_value)
            PyImGui.same_line(0,-1)
            if PyImGui.button("Save Alias"):
                save_entry_to_json(json_file_name, self.frame.frame_hash, self.submit_value)
                self.frame_alias = self.submit_value  
                self.setWindowName()          
            
            PyImGui.text(f"Parent ID: {self.frame.parent_id}")
            PyImGui.text(f"Visibility Flags: {self.frame.visibility_flags}")
            PyImGui.text(f"Type: {self.frame.type}")
            PyImGui.text(f"Template Type: {self.frame.template_type}")
            PyImGui.text(f"Frame Layout: {self.frame.frame_layout}")
            if PyImGui.collapsing_header("Position"):
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
            if PyImGui.collapsing_header("Relation"):
                PyImGui.text(f"Parent ID: {self.frame.relation.parent_id}")
                PyImGui.text(f"Field67_0x124: {self.frame.relation.field67_0x124}")
                PyImGui.text(f"Field68_0x128: {self.frame.relation.field68_0x128}")
                PyImGui.text(f"Frame Hash ID: {self.frame.relation.frame_hash_id}")
            if PyImGui.collapsing_header("Callbacks"):
                for i, callback in enumerate(self.frame.frame_callbacks):
                    PyImGui.text(f"{i}: {callback.get_address()}")
            if PyImGui.collapsing_header("Extra Fields"):
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
                      
        PyImGui.end()
   
# endregion

frame_toggles = {}  # Stores toggle states for each frame
info_windows = {}  # Stores active InfoWindow instances

def get_frame_hash(frame_id):
    """Search for the given frame_id inside frame_tree and return its frame_hash."""
    for children in frame_tree.values():
        for child in children:
            if child["frame_id"] == frame_id:
                return child["frame_hash"]  # ✅ Return the correct hash for the frame_id
    return 0  # Return "N/A" if frame_id is not found



def build_frame_tree(frame_hierarchy):
    """Builds a tree where each parent_frame_id maps to a list of (frame_id, frame_hash) pairs."""
    frame_tree = defaultdict(list)

    for parent_hash, frame_hash, parent_frame_id, frame_id in frame_hierarchy:
        frame_tree[parent_frame_id].append({"frame_id": frame_id, "frame_hash": frame_hash})  

    return frame_tree

def print_frame_tree(frame_tree):
    """Prints the frame tree in a more readable format."""
    for parent_frame_id, children in frame_tree.items():
        print(f"Frame {parent_frame_id}:")
        for child in children:
            print(f"  Frame {child['frame_id']} (Hash: {child['frame_hash']})")

def render_frame_tree(parent_frame_id=0):
    global frame_tree, frame_toggles, info_windows
    """Recursively renders the frame hierarchy using PyImGui."""
    children = frame_tree.get(parent_frame_id, [])

    frame_hash_look = get_frame_hash(parent_frame_id)
    frame_hash = children[0]["frame_hash"]
    frame_alias = get_entry_from_json(json_file_name, frame_hash_look) or ""
    if PyImGui.tree_node(f"Frame {parent_frame_id} (Hash: {frame_hash}) {frame_alias}##{parent_frame_id}"):
        # Parent node: Draw button first
        frame_toggles[parent_frame_id] = ImGui.toggle_button(f"Show Info##{parent_frame_id}", frame_toggles.get(parent_frame_id, False))

        if frame_toggles[parent_frame_id]:
            if parent_frame_id not in info_windows:
                info_windows[parent_frame_id] = InfoWindow(parent_frame_id)
            info_windows[parent_frame_id].Draw()

        for child in children:
            frame_id = child["frame_id"]
            frame_hash = child["frame_hash"]
            frame_alias = get_entry_from_json(json_file_name, frame_hash) or ""

            if frame_id in frame_tree:
                render_frame_tree(frame_id)
            else:
                # Leaf node: Draw text first, then button
                PyImGui.text(f"Frame {frame_id} (Hash: {frame_hash}) {frame_alias}")

                frame_toggles[frame_id] = ImGui.toggle_button(f"Show Info##{frame_id}", frame_toggles.get(frame_id, False))

                if frame_toggles[frame_id]:
                    if frame_id not in info_windows:
                        info_windows[frame_id] = InfoWindow(frame_id)
                    info_windows[frame_id].Draw()

        PyImGui.tree_pop()





frame_hash = 0
frame_id_by_hash = 0
frame_id_by_label = 0
frame_coords: list[tuple[int, int]] = []
frame_hierarchy: list[tuple[int, int, int, int]] = []
frame_tree = {}
frame = None

overlay = Overlay()

info_window : InfoWindow

def print_frame_hierarchy():
    for parent_hash, frame_hash, parent_frame_id, frame_id in frame_hierarchy:
        print(f"Parent Hash: {parent_hash}, Frame Hash: {frame_hash}, Parent Frame ID: {parent_frame_id}, Frame ID: {frame_id}")

def DrawWindow():
    global frame_hash, frame_id_by_hash, frame_id_by_label, frame_coords, overlay, frame_hierarchy, frame_tree
    global frame, info_window
    try:
        if PyImGui.begin("Frame Tester"):
                   

            if PyImGui.button("Populate Frame Hierarchy"):
                frame_hierarchy = UIManager.GetFrameHierarchy()  # Fetch hierarchy
                frame_tree = build_frame_tree(frame_hierarchy)  # Construct hierarchy
            
            if frame_hierarchy:
                if PyImGui.button("Print Frame Hierarchy"):
                    print_frame_hierarchy()
                
            if frame_tree:
                if PyImGui.button("Print Frame Tree"):
                    print_frame_tree(frame_tree)

                
            if frame_tree:
                render_frame_tree()
                
            
        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log("tester", f"Unexpected Error: {str(e)}", Py4GW.Console.MessageType.Error)






def main():
    DrawWindow()


if __name__ == "__main__":
    main()
