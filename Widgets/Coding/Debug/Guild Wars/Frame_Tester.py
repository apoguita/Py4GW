from Py4GWCoreLib import *
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional
import json
import ctypes

MODULE_NAME = "Frame Tester"
projects_root = Py4GW.Console.get_projects_path()
json_file_name = f"{projects_root}\\Py4GWCoreLib\\frame_aliases.json"

overlay = Overlay()

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
        self.child_offset_id = self.frame_obj.child_offset_id
        self.label = UIManager.GetEntryFromJSON(json_file_name, self.frame_id) or ""
        self.parent = None  # Will be set when building the tree
        self.children = []  # Stores child nodes
        self.show_frame_data = False
        
    def update(self):
        self.frame_obj.get_context()
        self.frame_hash = self.frame_obj.frame_hash
        self.label = UIManager.GetEntryFromJSON(json_file_name, self.frame_id) or ""

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
                            ImGui.table("frametester info##{self.frame_id}", headers, data)
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
                    ImGui.table("frametester info##{self.frame_id}", headers, data)
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
double_action = False

class InfoWindow:
    from PyUIManager import UIFrame
    def __init__(self, frame_obj:UIFrame):
        self.frame = frame_obj 
        self.auto_update = True
        self.draw_frame = True
        self.draw_color :int = Utils.RGBToColor(0, 255, 0, 125)
        self.monitor_callbacks = False
        self.frame_alias = UIManager.GetEntryFromJSON(json_file_name, self.frame.frame_id)  
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
        UIManager().DrawFrame(self.frame.frame_id, self.draw_color)
        
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
                self.draw_color = Utils.TupleToColor(PyImGui.color_edit4("Color", Utils.ColorToTuple(self.draw_color)))
            
            self.monitor_callbacks = PyImGui.checkbox("Monitor Callbacks", self.monitor_callbacks)
            
            if self.auto_update:
                self.frame.get_context()
            if self.draw_frame:
                self.DrawFrame()   
            if self.monitor_callbacks:
                self.MonitorCallbacks()
                
            PyImGui.separator()
            if PyImGui.begin_child("FrameTreeChild",size=(800,600),border=True,flags=PyImGui.WindowFlags.HorizontalScrollbar):
                if PyImGui.begin_tab_bar(f"FrameDebuggerIndividualTabBar##{self.frame.frame_id}"):
                    if PyImGui.begin_tab_item(f"Frame Tree##{self.frame.frame_id}"):
                        PyImGui.text(f"Frame ID: {self.frame.frame_id}")
                        PyImGui.text(f"Frame Hash: {self.frame.frame_hash}")
                        PyImGui.text(f"Alias: {self.frame_alias}")
                        
                        self.submit_value = PyImGui.input_text(f"Alias##Edit{self.frame.frame_id}", self.submit_value)
                        PyImGui.same_line(0,-1)
                        if PyImGui.button(f"Save Alias##{self.frame.frame_id}"):
                            UIManager.SaveEntryToJSON(json_file_name, self.frame.frame_id, self.submit_value)
                            self.frame_alias = UIManager.GetEntryFromJSON(json_file_name, self.frame.frame_id)  
                            self.setWindowName()          

                        if PyImGui.button(f"Click on frame{self.frame.frame_id}##click{self.frame.frame_id}"):
                            UIManager.FrameClick(self.frame.frame_id)
                            print (f"Clicked on frame {self.frame.frame_id}")
                            
                        PyImGui.separator()
                        self.current_state = PyImGui.input_int(f"Current State##{self.frame.frame_id}", self.current_state)
                        self.wparam = PyImGui.input_int(f"wParam##{self.frame.frame_id}", self.wparam)
                        self.lparam = PyImGui.input_int(f"lParam##{self.frame.frame_id}", self.lparam)
                        if PyImGui.button((f"test mouse action##{self.frame.frame_id}")):
                            UIManager.TestMouseAction(self.frame.frame_id, self.current_state, self.wparam, self.lparam)
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
                            UIManager.TestMouseClickAction(self.frame.frame_id, self.current_state, self.wparam, self.lparam)
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
                            ("Field3_0xc", str(self.frame.field3_0xc), self.to_hex(self.frame.field3_0xc), self.to_bin(self.frame.field3_0xc), self.to_char(self.frame.field3_0xc)),
                            ("Field4_0x10", str(self.frame.field4_0x10), self.to_hex(self.frame.field4_0x10), self.to_bin(self.frame.field4_0x10), self.to_char(self.frame.field4_0x10)),
                            ("Field5_0x14", str(self.frame.field5_0x14), self.to_hex(self.frame.field5_0x14), self.to_bin(self.frame.field5_0x14), self.to_char(self.frame.field5_0x14)),
                            ("Field7_0x1c", str(self.frame.field7_0x1c), self.to_hex(self.frame.field7_0x1c), self.to_bin(self.frame.field7_0x1c), self.to_char(self.frame.field7_0x1c)),
                            ("Field10_0x28", str(self.frame.field10_0x28), self.to_hex(self.frame.field10_0x28), self.to_bin(self.frame.field10_0x28), self.to_char(self.frame.field10_0x28)),
                            ("Field11_0x2c", str(self.frame.field11_0x2c), self.to_hex(self.frame.field11_0x2c), self.to_bin(self.frame.field11_0x2c), self.to_char(self.frame.field11_0x2c)),
                            ("Field12_0x30", str(self.frame.field12_0x30), self.to_hex(self.frame.field12_0x30), self.to_bin(self.frame.field12_0x30), self.to_char(self.frame.field12_0x30)),
                            ("Field13_0x34", str(self.frame.field13_0x34), self.to_hex(self.frame.field13_0x34), self.to_bin(self.frame.field13_0x34), self.to_char(self.frame.field13_0x34)),
                            ("Field14_0x38", str(self.frame.field14_0x38), self.to_hex(self.frame.field14_0x38), self.to_bin(self.frame.field14_0x38), self.to_char(self.frame.field14_0x38)),
                            ("Field15_0x3c", str(self.frame.field15_0x3c), self.to_hex(self.frame.field15_0x3c), self.to_bin(self.frame.field15_0x3c), self.to_char(self.frame.field15_0x3c)),
                            ("Field16_0x40", str(self.frame.field16_0x40), self.to_hex(self.frame.field16_0x40), self.to_bin(self.frame.field16_0x40), self.to_char(self.frame.field16_0x40)),
                            ("Field17_0x44", str(self.frame.field17_0x44), self.to_hex(self.frame.field17_0x44), self.to_bin(self.frame.field17_0x44), self.to_char(self.frame.field17_0x44)),
                            ("Field18_0x48", str(self.frame.field18_0x48), self.to_hex(self.frame.field18_0x48), self.to_bin(self.frame.field18_0x48), self.to_char(self.frame.field18_0x48)),
                            ("Field19_0x4c", str(self.frame.field19_0x4c), self.to_hex(self.frame.field19_0x4c), self.to_bin(self.frame.field19_0x4c), self.to_char(self.frame.field19_0x4c)),
                            ("Field20_0x50", str(self.frame.field20_0x50), self.to_hex(self.frame.field20_0x50), self.to_bin(self.frame.field20_0x50), self.to_char(self.frame.field20_0x50)),
                            ("Field21_0x54", str(self.frame.field21_0x54), self.to_hex(self.frame.field21_0x54), self.to_bin(self.frame.field21_0x54), self.to_char(self.frame.field21_0x54)),
                            ("Field22_0x58", str(self.frame.field22_0x58), self.to_hex(self.frame.field22_0x58), self.to_bin(self.frame.field22_0x58), self.to_char(self.frame.field22_0x58)),
                            ("Field23_0x5c", str(self.frame.field23_0x5c), self.to_hex(self.frame.field23_0x5c), self.to_bin(self.frame.field23_0x5c), self.to_char(self.frame.field23_0x5c)),
                            ("Field24_0x60", str(self.frame.field24_0x60), self.to_hex(self.frame.field24_0x60), self.to_bin(self.frame.field24_0x60), self.to_char(self.frame.field24_0x60)),
                        ]
                        
                    
                        ImGui.table(f"Frame Data##{self.frame.frame_id}", headers, data)

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

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("UI Frame Tester", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("An advanced developer utility for inspecting and mapping the")
    PyImGui.text("game's internal User Interface (UI) hierarchy. It allows for")
    PyImGui.text("identifying, aliasing, and debugging UI Frame structures.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Frame Tree: Hierarchical visualization of all UI elements (AdvUI)")
    PyImGui.bullet_text("Visual Debugging: Real-time screen highlighting of selected UI Frames")
    PyImGui.bullet_text("State Tracking: Color-coded indicators for Visible, Hidden, and Uncreated frames")
    PyImGui.bullet_text("Alias Manager: Map frame hashes to human-readable names via JSON")
    PyImGui.bullet_text("Detail Inspector: View frame IDs, parentage, child counts, and internal hashes")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")

    PyImGui.end_tooltip()


def main():
    DrawMainWindow()


if __name__ == "__main__":
    main()
