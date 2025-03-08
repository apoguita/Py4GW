from Py4GWCoreLib import *
from enum import Enum

module_name = "ID & Salvage"

MAX_BAGS = 4

inventory_frame_hash = 291586130
parent_frame_id = 0

rarity_colors = {
    "White": {
        "frame": Utils.RGBToColor(255, 255, 255, 125),
        "content": Utils.RGBToColor(255, 255, 255, 25),
        "text": Utils.RGBToColor(255, 255, 255, 255),
    },
    "Blue": {
        "frame": Utils.RGBToColor(0, 170, 255, 125),
        "content": Utils.RGBToColor(0, 170, 255, 25),
        "text": Utils.RGBToColor(0, 170, 255, 255),
    },
    "Green": {
        "frame": Utils.RGBToColor(25, 200, 0, 125),
        "content": Utils.RGBToColor(25, 200, 0, 25),
        "text": Utils.RGBToColor(25, 200, 0, 255),
    },
    "Purple": {
        "frame": Utils.RGBToColor(110, 65, 200, 125),
        "content": Utils.RGBToColor(110, 65, 200, 25),
        "text": Utils.RGBToColor(110, 65, 200, 255),
    },
    "Gold": {
        "frame": Utils.RGBToColor(225, 150, 0, 125),
        "content": Utils.RGBToColor(225, 150, 0, 25),
        "text": Utils.RGBToColor(225, 150, 0, 255),
    },
    "Ignored": {
        "frame": Utils.RGBToColor(26, 26, 26, 225),
        "content": Utils.RGBToColor(26, 26, 26, 225),
        "text": Utils.RGBToColor(26, 26, 26, 255),
    },
}

class ActionQueueClass:
    def __init__(self,throttle_time=250):
        self.action_queue = ActionQueue()
        self.action_queue_timer = Timer()
        self.action_queue_timer.Start()
        self.action_queue_time = throttle_time
        
identification_queue = ActionQueueClass()
salvage_queue = ActionQueueClass()

class ColorizeType(Enum):
    colorize = 1
    identification = 2
    salvage = 3
    text_filter = 4
    
class TabType(Enum):
    colorize = 1
    identification = 2
    salvage = 3
    xunlai_vault = 4
    config = 5

class ChildFrameCacheNode:
    def __init__(self, parent_hash, child_offsets):
        self.parent_hash = parent_hash
        self.child_offsets = child_offsets  # No tuple conversion
        self.frame_id = 0  # Initialize first
        self.frame_id = self.GetFrameID()

    def GetFrameID(self):
        if self.frame_id == 0:
            self.frame_id = UIManager.GetChildFrameID(self.parent_hash, self.child_offsets)
        return self.frame_id



class color_config:
    def __init__(self):
        self.colorize_whites = False
        self.colorize_blues = True
        self.colorize_greens = True
        self.colorize_purples = True
        self.colorize_golds = True
        self.colorize_ignored = True
        
colorize_config = color_config()


@staticmethod
def floating_checkbox(caption, state,x,y, color):
    width=20
    height=20
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
    PyImGui.push_style_color(PyImGui.ImGuiCol.Border, color)
       
    result = state
    if PyImGui.begin(f"##invisible_window{caption}", flags):
        PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0.2, 0.3, 0.4, 0.1))  # Normal state color
        PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0.3, 0.4, 0.5, 0.1))  # Hovered state
        PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0.4, 0.5, 0.6, 0.1))  # Checked state
        PyImGui.push_style_color(PyImGui.ImGuiCol.CheckMark, (1.0, 1.0, 1.0, 1.0))  # White checkmark

        result = PyImGui.checkbox(f"##floating_checkbox{caption}", state)
        PyImGui.pop_style_color(4)
    PyImGui.end()
    PyImGui.pop_style_var(2)
    PyImGui.pop_style_color(1)
    return result
            
identification_checkbox_states: Dict[int, bool] = {}
total_id_uses = 0
total_salvage_uses = 0
class item_config:
    global colorize_config
    global rarity_colors
    global parent_frame_id, inventory_frame_hash
    global total_id_uses, total_salvage_uses
    
    def __init__(self, bag_id, item_id):
        global total_id_uses
        self.item_id = item_id
        self.slot = Item.GetSlot(self.item_id)
        self.bags_offsets = [0,0,0,bag_id-1,self.slot+2]
        self.frame_id = UIManager.GetChildFrameID(inventory_frame_hash, self.bags_offsets)
        _, self.rarity = Item.Rarity.GetRarity(self.item_id)
        self.is_identified = Item.Usage.IsIdentified(self.item_id)
        self.is_id_kit = Item.Usage.IsIDKit(self.item_id)
        if self.is_id_kit:
            total_id_uses += Item.Usage.GetUses(self.item_id)
        self.left,self.top, self.right, self.bottom = UIManager.GetFrameCoords(self.frame_id)
      
    def can_draw(self):
        if self.rarity == "White" and not colorize_config.colorize_whites:
            return False
        if self.rarity == "Blue" and not colorize_config.colorize_blues:
            return False
        if self.rarity == "Green" and not colorize_config.colorize_greens:
            return False
        if self.rarity == "Purple" and not colorize_config.colorize_purples:
            return False
        if self.rarity == "Gold" and not colorize_config.colorize_golds:
            return False
        return True
    
    def draw_colorized(self, color_type=ColorizeType.colorize):
        if color_type== ColorizeType.colorize and self.can_draw():
            UIManager().DrawFrame(self.frame_id, rarity_colors[self.rarity]["content"])
            UIManager().DrawFrameOutline(self.frame_id, rarity_colors[self.rarity]["frame"])
            
    def draw_identification(self):
        color_content = rarity_colors[self.rarity]["content"]
        color_frame = rarity_colors[self.rarity]["frame"]
        if self.is_identified and not self.is_id_kit:
            color_content = rarity_colors["Ignored"]["content"]
            color_frame = rarity_colors["Ignored"]["frame"]
            
        UIManager().DrawFrame(self.frame_id, color_content)
        UIManager().DrawFrameOutline(self.frame_id, color_frame)
        
        if not self.is_identified and not self.is_id_kit:
            if self.item_id not in identification_checkbox_states:
                identification_checkbox_states[self.item_id] = False  # Set default state

            identification_checkbox_states[self.item_id] = floating_checkbox(
                f"{self.item_id}", 
                identification_checkbox_states[self.item_id], 
                self.right -20, 
                self.bottom-20,
                Utils.ColorToTuple(rarity_colors[self.rarity]["frame"])
            )

        


class xunlaivault_config:
    def __init__(self):
        self.synch_vault_with_inventory = True
        self.frame_id = 0
        self.xunlai_window_exists = False
        
xunlai_vault_config = xunlaivault_config()

class id_config:
    def __init__(self):
        self.enabled = False
        self.frame_id = 0
        self.inventory_window_exists = False
        
class salvage_config:
    def __init__(self):
        self.enabled = False
        self.frame_id = 0
        self.inventory_window_exists = False
        
        
class bag_config:
    def __init__(self):
        self.bag_id = 0
        self.items : List[item_config] = []

class config:
    global parent_frame_id, inventory_frame_hash, MAX_BAGS
    
    def __init__(self):
        self.map_valid = False
        self.is_map_loading = False
        self.is_map_ready = False
        self.is_party_loaded = False
        self.inventory_window_exists = False
        
        self.game_throttle_time = 500
        self.game_throttle_timer = Timer()
        self.game_throttle_timer.Start()
        self.id_vars = id_config()
        self.salvage_vars = salvage_config()
        self.bags: List[bag_config] = [bag_config() for _ in range(MAX_BAGS)]
        self.colorize_vars = ColorizeType.colorize
        self.selected_tab = TabType.colorize
        
            

widget_config = config()

window_module = ImGui.WindowModule(
    module_name, 
    window_name="ID & Salvage", 
    window_size=(300, 200),
    window_flags=PyImGui.WindowFlags.AlwaysAutoResize
)

def IdentifyItems():
    global identification_queue
    global identification_checkbox_states
    global total_id_uses
    for item_id in identification_checkbox_states:
        if identification_checkbox_states[item_id]:
            first_id_kit = Inventory.GetFirstIDKit()
            if first_id_kit == 0:
                return
            identification_queue.action_queue.add_action(Inventory.IdentifyItem, item_id, first_id_kit)
            identification_checkbox_states[item_id] = False
            total_id_uses -= 1
            if total_id_uses <= 0:
                return

def bottom_window_flags():
    return ( PyImGui.WindowFlags.NoCollapse | 
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoResize |
            PyImGui.WindowFlags.NoScrollWithMouse
    )
  
def push_transparent_window():
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowPadding,0.0)
    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowBorderSize,0.0)
    
    flags=( PyImGui.WindowFlags.NoCollapse | 
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.NoResize |
            PyImGui.WindowFlags.NoBackground 
        ) 
    
    return flags

def pop_transparent_window():
    PyImGui.pop_style_var(3)
    
def DrawColorizeOptions():
    global colorize_config, rarity_colors
    left, top, right, bottom = UIManager.GetFrameCoords(parent_frame_id)  
    title_offset = 20
    frame_offset = 5
    height = bottom - top - title_offset
    width = right - left - frame_offset

    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
    flags=bottom_window_flags()
    
    PyImGui.set_next_window_pos(left, bottom)
    PyImGui.set_next_window_size(width, 40)
    
    if PyImGui.begin("Colorize##ColorizeWindow",True, flags):
    
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Utils.ColorToTuple(rarity_colors["White"]["text"]))
        colorize_config.colorize_whites = PyImGui.checkbox("Whites", colorize_config.colorize_whites)
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Utils.ColorToTuple(rarity_colors["Blue"]["text"]))
        colorize_config.colorize_blues = PyImGui.checkbox("Blues", colorize_config.colorize_blues)
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Utils.ColorToTuple(rarity_colors["Purple"]["text"]))
        colorize_config.colorize_purples = PyImGui.checkbox("Purples", colorize_config.colorize_purples)
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Utils.ColorToTuple(rarity_colors["Gold"]["text"]))
        colorize_config.colorize_golds = PyImGui.checkbox("Golds", colorize_config.colorize_golds)
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Utils.ColorToTuple(rarity_colors["Green"]["text"]))
        colorize_config.colorize_greens = PyImGui.checkbox("Greens", colorize_config.colorize_greens)
        PyImGui.pop_style_color(4)
    PyImGui.end()
    PyImGui.pop_style_var(1)
  
selected_item = 0
def DrawIDOptions():
    global colorize_config, rarity_colors
    global selected_item
    global total_id_uses, total_salvage_uses
    left, top, right, bottom = UIManager.GetFrameCoords(parent_frame_id)  
    title_offset = 20
    frame_offset = 5
    height = bottom - top - title_offset
    width = right - left - frame_offset

    PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
    flags=bottom_window_flags()
    
    PyImGui.set_next_window_pos(left, bottom)
    PyImGui.set_next_window_size(width, 40)
    
    if PyImGui.begin("Identify##IdentifyWindow",True, flags):
        select_item_list = ["All", "Whites", "Blues", "Purples", "Golds", "None"]
        PyImGui.push_item_width(100)
        selected_item = PyImGui.combo("##IDCombo", selected_item, select_item_list)
        PyImGui.pop_item_width()
        PyImGui.same_line(0,-1)
        if PyImGui.button(f"Select {select_item_list[selected_item]}"):
            if selected_item == 0:
                for item_id in identification_checkbox_states:
                    identification_checkbox_states[item_id] = True
            elif selected_item == 1:
                for item_id in identification_checkbox_states:
                    if item_id in identification_checkbox_states:
                        if Item.Rarity.IsWhite(item_id):
                            identification_checkbox_states[item_id] = True                 
            elif selected_item == 2:
                for item_id in identification_checkbox_states:
                    if item_id in identification_checkbox_states:
                        if Item.Rarity.IsBlue(item_id):
                            identification_checkbox_states[item_id] = True
            elif selected_item == 3:
                for item_id in identification_checkbox_states:
                    if item_id in identification_checkbox_states:
                        if Item.Rarity.IsPurple(item_id):
                            identification_checkbox_states[item_id] = True
            elif selected_item == 4:
                for item_id in identification_checkbox_states:
                    if item_id in identification_checkbox_states:
                        if Item.Rarity.IsGold(item_id):
                            identification_checkbox_states[item_id] = True                
            elif selected_item == 5:
                for item_id in identification_checkbox_states:
                    identification_checkbox_states[item_id] = False

        PyImGui.same_line(0,-1)
        PyImGui.text(f"{total_id_uses} ID uses remaining")
        PyImGui.same_line(0,-1)
        available_width= PyImGui.get_window_width()
    
        PyImGui.set_cursor_pos_x(available_width -100)
        if PyImGui.button("ID Selected"):
            IdentifyItems()
        
    PyImGui.end()
    PyImGui.pop_style_var(1)

def DrawWindow():
    global parent_frame_id, MAX_BAGS
    global colorize_config, rarity_colors
    global xunlai_vault_config
    global total_id_uses, total_salvage_uses
    left, top, right, bottom = UIManager.GetFrameCoords(parent_frame_id)  
    title_offset = 20
    frame_offset = 5
    height = bottom - top - title_offset
    width = right - left - frame_offset
    
    
    flags= push_transparent_window()
    
    PyImGui.set_next_window_pos(left, top-35)
    PyImGui.set_next_window_size(width, 35)
    if PyImGui.begin(window_module.window_name,True, flags):
        widget_config.colorize_vars = ColorizeType.colorize
        if PyImGui.begin_tab_bar("InventoryTabs"):
            if PyImGui.begin_tab_item("Colorize##ColorizeTab"):
                widget_config.colorize_vars = ColorizeType.colorize
                widget_config.selected_tab = TabType.colorize
                PyImGui.end_tab_item()
            if PyImGui.begin_tab_item("ID##IDTab"):
                widget_config.colorize_vars = ColorizeType.identification
                widget_config.selected_tab = TabType.identification
                PyImGui.end_tab_item()
            if PyImGui.begin_tab_item("Salvage##SalvageTab"):
                widget_config.colorize_vars = ColorizeType.salvage
                widget_config.selected_tab = TabType.salvage
                PyImGui.end_tab_item()
            if PyImGui.begin_tab_item("Xunlai Vault##XunlaiVaultTab"):
                widget_config.colorize_vars = ColorizeType.colorize
                widget_config.selected_tab = TabType.xunlai_vault
                PyImGui.end_tab_item()
            if PyImGui.begin_tab_item("Config##configTab"):
                widget_config.colorize_vars = ColorizeType.colorize
                widget_config.selected_tab = TabType.config
                PyImGui.end_tab_item()
            PyImGui.end_tab_bar()
    PyImGui.end()
    pop_transparent_window()
    
    if widget_config.selected_tab == TabType.colorize:
        DrawColorizeOptions()

    if widget_config.selected_tab == TabType.identification:
        DrawIDOptions()
        
    
    items: List[item_config] = []
    total_id_uses = 0
    for bag_id in range(1, MAX_BAGS+1):
        bag_to_check = ItemArray.CreateBagList(bag_id)
        item_array = ItemArray.GetItemArray(bag_to_check)
        
        for item_id in item_array:
            items.append(item_config(bag_id, item_id))
            

    for item in items:
        if widget_config.colorize_vars == ColorizeType.colorize:
            item.draw_colorized()
        elif widget_config.colorize_vars == ColorizeType.identification:
            item.draw_identification()    
        
    

def configure():
    pass

def main():
    global parent_frame_id, inventory_frame_hash, bags_offsets, MAX_BAGS
    global widget_config
    global identification_queue, salvage_queue
    
    if widget_config.game_throttle_timer.HasElapsed(widget_config.game_throttle_time):
        widget_config.is_map_loading = Map.IsMapLoading()
        if widget_config.is_map_loading:
            return
        
        widget_config.is_map_ready = Map.IsMapReady()
        widget_config.is_party_loaded = Party.IsPartyLoaded()
        widget_config.map_valid = widget_config.is_map_ready and widget_config.is_party_loaded
        
        if widget_config.map_valid:
            parent_frame_id = UIManager.GetFrameIDByHash(inventory_frame_hash)
            if parent_frame_id != 0:
                previous_inventory_window_exists = widget_config.inventory_window_exists
                widget_config.inventory_window_exists = UIManager.FrameExists(parent_frame_id)
                
                #if not previous_inventory_window_exists and widget_config.inventory_window_exists:
                #    frame_cache.clear_cache()
                             
            else:
                widget_config.inventory_window_exists = False
        else:
            widget_config.inventory_window_exists = False
            
        widget_config.game_throttle_timer.Reset()
        
    if not (widget_config.map_valid and widget_config.inventory_window_exists):
        return
    
    if xunlai_vault_config.synch_vault_with_inventory and not Inventory.IsStorageOpen():
        Inventory.OpenXunlaiWindow()
    DrawWindow()

    
    if identification_queue.action_queue_timer.HasElapsed(identification_queue.action_queue_time):
        if not identification_queue.action_queue.is_empty():
            identification_queue.action_queue_timer.Reset()
            identification_queue.action_queue.execute_next()
        
        

if __name__ == "__main__":
    main()

