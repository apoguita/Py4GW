
import PyImGui
import Py4GW
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import ColorPalette
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import UIManager
from Py4GWCoreLib import Inventory
from Py4GWCoreLib import ItemArray
from Py4GWCoreLib import Item
from Py4GWCoreLib import Bags
from Widgets.InvPlus.GUI_Helpers import game_toggle_button
from Widgets.InvPlus.GUI_Helpers import (Frame,
                                        _get_parent_hash,
                                        _get_offsets,
                                        _get_frame_color,
                                        _get_frame_outline_color,
                                        XUNLAI_VAULT_FRAME_HASH
                                        )           
from Py4GWCoreLib import IniHandler

class ColorizeModule:
    def __init__(self, inventory_frame: Frame):
        self.colorize_whites = False
        self.colorize_blues = True
        self.colorize_purples = True
        self.colorize_golds = True
        self.colorize_greens = True
        self.MODULE_NAME = "Colorize"
        self.inventory_frame = inventory_frame
        projects_path = Py4GW.Console.get_projects_path()
        full_path = projects_path + "\\Widgets\\Config\\InventoryPlus.ini"
        self.ini = IniHandler(full_path)
        self.colorize_whites = self.ini.read_bool("ColorizeOptions", "colorize_whites", self.colorize_whites)
        self.colorize_blues = self.ini.read_bool("ColorizeOptions", "colorize_blues", self.colorize_blues)
        self.colorize_purples = self.ini.read_bool("ColorizeOptions", "colorize_purples", self.colorize_purples)
        self.colorize_golds = self.ini.read_bool("ColorizeOptions", "colorize_golds", self.colorize_golds)
        self.colorize_greens = self.ini.read_bool("ColorizeOptions", "colorize_greens", self.colorize_greens)
    #region ColorizeStrip

    def draw_colorize_bottom_strip(self):
        x = self.inventory_frame.left +5
        y = self.inventory_frame.bottom
        width = self.inventory_frame.width
        height = 30
        
        PyImGui.set_next_window_pos(x, y)
        PyImGui.set_next_window_size(0, height)

        flags = (
            PyImGui.WindowFlags.NoCollapse |
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.AlwaysAutoResize
        )
        
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 5, 5)
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0, 0)
        
        if PyImGui.begin("ColorizeButtons", flags):
            
            state = self.colorize_whites
            color = ColorPalette.GetColor("GW_White")
            if game_toggle_button("##ColorizeWhiteButton","Color Whites",state, width=20, height=20, color=color):
                self.colorize_whites = not self.colorize_whites
                ConsoleLog(self.MODULE_NAME, f"Colorize Whites is now {'enabled' if self.colorize_whites else 'disabled'}.", Py4GW.Console.MessageType.Info)
                self.ini.write_key("ColorizeOptions", "colorize_whites", self.colorize_whites)
            PyImGui.same_line(0,3)  
            state = self.colorize_blues
            color = ColorPalette.GetColor("GW_Blue")
            if game_toggle_button("##ColorizeBlueButton","Color Blues",state, width=20, height=20, color=color):
                self.colorize_blues = not self.colorize_blues
                ConsoleLog(self.MODULE_NAME, f"Colorize Blues is now {'enabled' if self.colorize_blues else 'disabled'}.", Py4GW.Console.MessageType.Info)
                self.ini.write_key("ColorizeOptions", "colorize_blues", self.colorize_blues)
            PyImGui.same_line(0,3)     
            state = self.colorize_purples
            color = ColorPalette.GetColor("GW_Purple")
            if game_toggle_button("##ColorizePurpleButton","Color Purples",state, width=20, height=20, color=color):
                self.colorize_purples = not self.colorize_purples
                ConsoleLog(self.MODULE_NAME, f"Colorize Purples is now {'enabled' if self.colorize_purples else 'disabled'}.", Py4GW.Console.MessageType.Info)
                self.ini.write_key("ColorizeOptions", "colorize_purples", self.colorize_purples)
            PyImGui.same_line(0,3)     
            state = self.colorize_golds
            color = ColorPalette.GetColor("GW_Gold")
            if game_toggle_button("##ColorizeGoldButton","Color Golds",state, width=20, height=20, color=color):
                self.colorize_golds = not self.colorize_golds
                ConsoleLog(self.MODULE_NAME, f"Colorize Golds is now {'enabled' if self.colorize_golds else 'disabled'}.", Py4GW.Console.MessageType.Info)
                self.ini.write_key("ColorizeOptions", "colorize_golds", self.colorize_golds)
            PyImGui.same_line(0,3)     
            state = self.colorize_greens
            color = ColorPalette.GetColor("GW_Green")
            if game_toggle_button("##ColorizeGreenButton","Color Greens",state, width=20, height=20, color=color):
                self.colorize_greens = not self.colorize_greens
                ConsoleLog(self.MODULE_NAME, f"Colorize Greens is now {'enabled' if self.colorize_greens else 'disabled'}.", Py4GW.Console.MessageType.Info)
                self.ini.write_key("ColorizeOptions", "colorize_greens", self.colorize_greens)

        PyImGui.end()
        PyImGui.pop_style_var(2)
    
    #endregion

    #region ColorizeItems
    
    def _can_draw_item(self, rarity:str):
        if rarity == "White":
            return self.colorize_whites
        elif rarity == "Blue":
            return self.colorize_blues
        elif rarity == "Green":
            return self.colorize_greens
        elif rarity == "Purple":
            return self.colorize_purples
        elif rarity == "Gold":
            return self.colorize_golds
        else:
            return False
    
    def colorize_items(self):
        for bag_id in range(Bags.Backpack, Bags.Bag2+1):
            bag_to_check = ItemArray.CreateBagList(bag_id)
            item_array = ItemArray.GetItemArray(bag_to_check)
            
            for item_id in item_array:
                _,rarity = Item.Rarity.GetRarity(item_id)
                slot = Item.GetSlot(item_id)
                if not self._can_draw_item(rarity):
                    continue
                frame_id = UIManager.GetChildFrameID(_get_parent_hash(),_get_offsets(bag_id, slot))
                is_visible = UIManager.FrameExists(frame_id)
                if not is_visible:
                    continue
                UIManager().DrawFrame(frame_id, _get_frame_color(rarity))
                UIManager().DrawFrameOutline(frame_id, _get_frame_outline_color(rarity))
         
    #endregion
    
        #region ColorizeVaultItems
    def colorize_vault_items(self):
        def _get_parent_hash():
            return XUNLAI_VAULT_FRAME_HASH
        
        def _get_offsets(bag_id:int, slot:int):        
            return [0,bag_id-8,slot+2]
        
        if not Inventory.IsStorageOpen():
            return
        
        for bag_id in range(Bags.Storage1, Bags.Storage14+1):
            bag_to_check = ItemArray.CreateBagList(bag_id)
            item_array = ItemArray.GetItemArray(bag_to_check)
            
            for item_id in item_array:
                _,rarity = Item.Rarity.GetRarity(item_id)
                slot = Item.GetSlot(item_id)

                if not self._can_draw_item(rarity):
                        continue
                
                frame_id = UIManager.GetChildFrameID(_get_parent_hash(), _get_offsets(bag_id, slot))
                is_visible = UIManager.FrameExists(frame_id)
                if not is_visible:
                    continue
                UIManager().DrawFrame(frame_id, _get_frame_color(rarity))
                UIManager().DrawFrameOutline(frame_id, _get_frame_outline_color(rarity))
                
    #endregion
