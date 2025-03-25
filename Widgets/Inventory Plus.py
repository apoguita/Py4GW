from Py4GWCoreLib import *
from enum import Enum

module_name = "ID & Salvage"

MAX_BAGS = 4

inventory_frame_hash = 291586130
parent_frame_id = 0

#region rarity colors

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

#endregion

#region Types
#ColorizeType
class ColorizeType(Enum):
    colorize = 1
    identification = 2
    salvage = 3
    text_filter = 4
    
#TabType 
class TabType(Enum):
    colorize = 1
    identification = 2
    salvage = 3
    xunlai_vault = 4
    config = 5
    
#Colorize config
class color_config:
    def __init__(self):
        self.colorize_whites = False
        self.colorize_blues = True
        self.colorize_greens = True
        self.colorize_purples = True
        self.colorize_golds = True
        self.colorize_ignored = True
        
#Xunlai Vault config
class xunlaivault_config:
    def __init__(self):
        self.synch_vault_with_inventory = True
        self.frame_id = 0
        self.xunlai_window_exists = False
    
#id config    
class id_config:
    def __init__(self):
        self.enabled = False
        self.frame_id = 0
        self.inventory_window_exists = False
  
#salvage config      
class salvage_config:
    def __init__(self):
        self.enabled = False
        self.frame_id = 0
        self.inventory_window_exists = False
        
#bag config       
class bag_config:
    def __init__(self):
        self.bag_id = 0
        self.items : List[item_config] = []
        
#global config
class config:
    global parent_frame_id, inventory_frame_hash, MAX_BAGS
    
    def __init__(self):
        self.inventory_window_exists = False
        
        self.game_throttle_time = 500
        self.game_throttle_timer = Timer()
        self.game_throttle_timer.Start()
        self.id_vars = id_config()
        self.salvage_vars = salvage_config()
        self.bags: List[bag_config] = [bag_config() for _ in range(MAX_BAGS)]
        self.colorize_vars = ColorizeType.colorize
        self.selected_tab = TabType.colorize
        
        
#endregion

#region Floating_Checkbox
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
#endregion

#region globals     
colorize_config = color_config()
identification_checkbox_states: Dict[int, bool] = {}
salvage_checkbox_states: Dict[int, bool] = {}
xunlai_vault_config = xunlaivault_config()
inventory_object = PyInventory.PyInventory()

widget_config = config()

window_module = ImGui.WindowModule(
    module_name, 
    window_name="ID & Salvage", 
    window_size=(300, 200),
    window_flags=PyImGui.WindowFlags.AlwaysAutoResize
)

total_id_uses = 0
total_salvage_uses = 0

#endregion

#region item config
class item_config:
    global colorize_config
    global rarity_colors
    global parent_frame_id, inventory_frame_hash
    global total_id_uses, total_salvage_uses
    
    def __init__(self, bag_id, item_id):
        global total_id_uses
        global total_salvage_uses
        self.item_id = item_id
        self.slot = Item.GetSlot(self.item_id)
        self.bags_offsets = [0,0,0,bag_id-1,self.slot+2]
        self.frame_id = UIManager.GetChildFrameID(inventory_frame_hash, self.bags_offsets)
        _, self.rarity = Item.Rarity.GetRarity(self.item_id)
        self.is_identified = Item.Usage.IsIdentified(self.item_id)
        self.is_salvageable = Item.Usage.IsSalvageable(self.item_id)
        self.is_id_kit = Item.Usage.IsIDKit(self.item_id)
        self.is_salv_kit = Item.Usage.IsLesserKit(self.item_id)
        if self.is_id_kit:
            total_id_uses += Item.Usage.GetUses(self.item_id)
        if self.is_salv_kit:
            total_salvage_uses += Item.Usage.GetUses(self.item_id)
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
            
    def draw_salvage(self):
        color_content = rarity_colors[self.rarity]["content"]
        color_frame = rarity_colors[self.rarity]["frame"]
        if not (self.is_identified and self.is_salvageable) and not self.is_salv_kit:
            color_content = rarity_colors["Ignored"]["content"]
            color_frame = rarity_colors["Ignored"]["frame"]
            
        UIManager().DrawFrame(self.frame_id, color_content)
        UIManager().DrawFrameOutline(self.frame_id, color_frame)
        
        if self.is_identified and self.is_salvageable:
            if self.item_id not in salvage_checkbox_states:
                salvage_checkbox_states[self.item_id] = False  # Set default state

            salvage_checkbox_states[self.item_id] = floating_checkbox(
                f"{self.item_id}", 
                salvage_checkbox_states[self.item_id], 
                self.right -20, 
                self.bottom-20,
                Utils.ColorToTuple(rarity_colors[self.rarity]["frame"])
            )
        


#endregion

#region ImGuiTemplates
def bottom_window_flags():
    return ( PyImGui.WindowFlags.NoCollapse | 
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoResize |
            PyImGui.WindowFlags.NoScrollWithMouse
    )
  
    
#endregion
    
#region colorize options
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
    
# endregion

#region ID options
  
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
    
#endregion

#region Salv options
def DrawSalvOptions():
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
    
    if PyImGui.begin("Salvage##SalvageWindow",True, flags):
        select_item_list = ["All", "Whites", "Blues", "Purples", "Golds", "None"]
        PyImGui.push_item_width(100)
        selected_item = PyImGui.combo("##SalvCombo", selected_item, select_item_list)
        PyImGui.pop_item_width()
        PyImGui.same_line(0,-1)
        if PyImGui.button(f"Select {select_item_list[selected_item]}"):
            if selected_item == 0:
                for item_id in salvage_checkbox_states:
                    salvage_checkbox_states[item_id] = True
            elif selected_item == 1:
                for item_id in salvage_checkbox_states:
                    if item_id in salvage_checkbox_states:
                        if Item.Rarity.IsWhite(item_id):
                            salvage_checkbox_states[item_id] = True                 
            elif selected_item == 2:
                for item_id in salvage_checkbox_states:
                    if item_id in salvage_checkbox_states:
                        if Item.Rarity.IsBlue(item_id):
                            salvage_checkbox_states[item_id] = True
            elif selected_item == 3:
                for item_id in salvage_checkbox_states:
                    if item_id in salvage_checkbox_states:
                        if Item.Rarity.IsPurple(item_id):
                            salvage_checkbox_states[item_id] = True
            elif selected_item == 4:
                for item_id in salvage_checkbox_states:
                    if item_id in salvage_checkbox_states:
                        if Item.Rarity.IsGold(item_id):
                            salvage_checkbox_states[item_id] = True                
            elif selected_item == 5:
                for item_id in salvage_checkbox_states:
                    salvage_checkbox_states[item_id] = False

        PyImGui.same_line(0,-1)
        PyImGui.text(f"{total_salvage_uses} Salvage uses remaining")
        PyImGui.same_line(0,-1)
        available_width= PyImGui.get_window_width()
    
        PyImGui.set_cursor_pos_x(available_width -125)
        if PyImGui.button("Salvage Selected"):
            SalvageItems()
        
    PyImGui.end()
    PyImGui.pop_style_var(1)
    
#endregion


#region DrawWindow
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
    
    
    flags= ImGui.PushTransparentWindow()
    
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
    
    ImGui.PopTransparentWindow()
    
    if widget_config.selected_tab == TabType.colorize:
        DrawColorizeOptions()

    if widget_config.selected_tab == TabType.identification:
        DrawIDOptions()
        
    if widget_config.selected_tab == TabType.salvage:
        DrawSalvOptions()
        
    
    items: List[item_config] = []
    total_id_uses = 0
    total_salvage_uses = 0
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
        elif widget_config.colorize_vars == ColorizeType.salvage:
            item.draw_salvage()  
 
 #endregion       
 
#region inventory routines
def IdentifyItems():
    global identification_checkbox_states
    global total_id_uses
    ActionQueueManager().ResetQueue("IDENTIFY")
    for item_id in identification_checkbox_states:
        if identification_checkbox_states[item_id]:
            first_id_kit = Inventory.GetFirstIDKit()
            if first_id_kit == 0:
                return
            ActionQueueManager().AddAction("IDENTIFY", Inventory.IdentifyItem, item_id, first_id_kit)
            identification_checkbox_states[item_id] = False
            total_id_uses -= 1
            if total_id_uses <= 0:
                return   

    for item_id in identification_checkbox_states:
        identification_checkbox_states[item_id] = False
            
def AutoSalvage(item_id):
    first_salv_kit = Inventory.GetFirstSalvageKit()
    if first_salv_kit == 0:
        return
    Inventory.SalvageItem(item_id, first_salv_kit)

def SalvageItems():
    global salvage_checkbox_states
    global total_salvage_uses
    global inventory_object
    ActionQueueManager().ResetQueue("SALVAGE")
    for item_id in salvage_checkbox_states:
        if salvage_checkbox_states[item_id]:
            quantity = Item.Properties.GetQuantity(item_id)
            if total_salvage_uses < quantity:
                quantity = total_salvage_uses
            for _ in range(quantity):
                first_salv_kit = Inventory.GetFirstSalvageKit()
                if first_salv_kit == 0:
                    return
                ActionQueueManager().AddAction("SALVAGE", AutoSalvage, item_id)
                ActionQueueManager().AddAction("SALVAGE",Inventory.AcceptSalvageMaterialsWindow)

            salvage_checkbox_states[item_id] = False
            total_salvage_uses -= quantity
            if total_salvage_uses <= 0:
                return   
    
    for item_id in salvage_checkbox_states:
        salvage_checkbox_states[item_id] = False
        
#endregion


def configure():
    pass

id_queue_reset_done = False
salv_queue_reset_done = False

def ResetInventoryEnvironment():
    global identification_checkbox_states, salvage_checkbox_states
    global total_id_uses, total_salvage_uses
    global widget_config
    global inventory_object
    
    identification_checkbox_states.clear()
    salvage_checkbox_states.clear()
    total_id_uses = 0
    total_salvage_uses = 0
    widget_config.bags = [bag_config() for _ in range(MAX_BAGS)]  # Reset bag configs
    inventory_object = PyInventory.PyInventory()  # Re-initialize inventory object


#region main
def main():
    global parent_frame_id, inventory_frame_hash, MAX_BAGS
    global widget_config
    global inventory_object
    global id_queue_reset_done, salv_queue_reset_done
    
    if Map.IsMapLoading():
        return
    
    if not (Map.IsMapReady() and Party.IsPartyLoaded()):
        return
    
    if widget_config.game_throttle_timer.HasElapsed(widget_config.game_throttle_time):
        parent_frame_id = UIManager.GetFrameIDByHash(inventory_frame_hash)
        if parent_frame_id != 0:
            widget_config.inventory_window_exists = UIManager.FrameExists(parent_frame_id)                         
        else:
            widget_config.inventory_window_exists = False

        widget_config.game_throttle_timer.Reset()
        
    if not (widget_config.inventory_window_exists):
        return
    
    if xunlai_vault_config.synch_vault_with_inventory and not Inventory.IsStorageOpen():
        Inventory.OpenXunlaiWindow()
    DrawWindow()

    
    ActionQueueManager().ProcessQueue("IDENTIFY")
    ActionQueueManager().ProcessQueue("SALVAGE")
    
    id_queue = ActionQueueManager().GetQueue("IDENTIFY")
    salv_queue = ActionQueueManager().GetQueue("SALVAGE")

    

    # IDENTIFY reset
    if id_queue.is_empty():
        if not id_queue_reset_done:
            ResetInventoryEnvironment()
            id_queue_reset_done = True
    else:
        id_queue_reset_done = False

    # SALVAGE reset
    if salv_queue.is_empty():
        if not salv_queue_reset_done:
            ResetInventoryEnvironment()
            salv_queue_reset_done = True
    else:
        salv_queue_reset_done = False
    
        
#endregion    

if __name__ == "__main__":
    main()

