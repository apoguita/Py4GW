
import PyImGui
import Py4GW
from typing import Dict


from Py4GWCoreLib import ImGui
from Py4GWCoreLib import ColorPalette
from Py4GWCoreLib import ItemArray
from Py4GWCoreLib import Item
from Py4GWCoreLib import Bags
from Py4GWCoreLib import IconsFontAwesome5
from Py4GWCoreLib import ModelID
from Py4GWCoreLib import UIManager
from Py4GWCoreLib import GLOBAL_CACHE
from Widgets.InvPlus.GUI_Helpers import (TabIcon,
                                         Frame,
                                            floating_game_button,   
                                            game_button,
                                            game_toggle_button,
                                            _get_parent_hash,
                                            _get_offsets,
                                            _get_frame_color,
                                            _get_frame_outline_color,
                                            _get_checkbox_color,
                                            _get_floating_button_color,
                                            INVENTORY_FRAME_HASH,
                                            XUNLAI_VAULT_FRAME_HASH
                            )         
from Widgets.InvPlus.Coroutines import IdentifyCheckedItems
from Py4GWCoreLib import IniHandler

class XunlaiModule:   
    def __init__(self, inventory_frame: Frame):
        self.MODULE_NAME = "Xunlai"
        self.inventory_frame = inventory_frame
        self.show_transfer_buttons = True
        projects_path = Py4GW.Console.get_projects_path()
        full_path = projects_path + "\\Widgets\\Config\\InventoryPlus.ini"
        self.ini = IniHandler(full_path)
        self.show_transfer_buttons = self.ini.read_bool("XunlaiOptions", "show_transfer_buttons", self.show_transfer_buttons)   

    #region DrawXunlaiBottomStrip
    def draw_xunlai_bottom_strip(self):
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
        
        if PyImGui.begin("XunlaiButtons", flags):
            self.show_transfer_buttons = ImGui.toggle_button(IconsFontAwesome5.ICON_CARET_SQUARE_RIGHT, self.show_transfer_buttons, width=20, height=20)
            ImGui.show_tooltip("Show Deposit/Withdraw Buttons")
            PyImGui.same_line(0,-1)
            PyImGui.text("|")
            PyImGui.same_line(0,-1)  
            self.ini.write_key("XunlaiOptions", "show_transfer_buttons", self.show_transfer_buttons)
        PyImGui.end()
        PyImGui.pop_style_var(2)
        
    #region DrawDepositButtons
    def draw_deposit_buttons(self):
        for bag_id in range(Bags.Backpack, Bags.Bag2+1):
            bag_to_check = ItemArray.CreateBagList(bag_id)
            item_array = ItemArray.GetItemArray(bag_to_check)
            
            for item_id in item_array:
                _,rarity = Item.Rarity.GetRarity(item_id)
                slot = Item.GetSlot(item_id)

                frame_id = UIManager.GetChildFrameID(_get_parent_hash(),_get_offsets(bag_id, slot))
                is_visible = UIManager.FrameExists(frame_id)
                if not is_visible:
                    continue
                
                left,top, right, bottom = UIManager.GetFrameCoords(frame_id)
                if ImGui.floating_button(caption=IconsFontAwesome5.ICON_CARET_SQUARE_RIGHT,
                                        name=f"DepositButton{item_id}",
                                        x=right-25, 
                                        y=bottom-25, 
                                        width=25, 
                                        height=25, 
                                        color=_get_floating_button_color(rarity)):
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    
            
                    
    def draw_withdraw_buttons(self):
        def _get_parent_hash():
            return XUNLAI_VAULT_FRAME_HASH
        
        def _get_offsets(bag_id:int, slot:int):        
            return [0,bag_id-8,slot+2]
        
        for bag_id in range(Bags.Storage1, Bags.Storage14+1):
            bag_to_check = ItemArray.CreateBagList(bag_id)
            item_array = ItemArray.GetItemArray(bag_to_check)
            
            for item_id in item_array:
                _,rarity = Item.Rarity.GetRarity(item_id)
                slot = Item.GetSlot(item_id)

                frame_id = UIManager.GetChildFrameID(_get_parent_hash(),_get_offsets(bag_id, slot))
                is_visible = UIManager.FrameExists(frame_id)
                if not is_visible:
                    continue
                
                left,top, right, bottom = UIManager.GetFrameCoords(frame_id)
                if ImGui.floating_button(caption=IconsFontAwesome5.ICON_CARET_SQUARE_LEFT,
                                        name=f"WithdrawButton{item_id}",
                                        x=right-25, 
                                        y=bottom-25, 
                                        width=25, 
                                        height=25, 
                                        color=_get_floating_button_color(rarity)):
                    GLOBAL_CACHE.Inventory.WithdrawItemFromStorage(item_id)
                
         
    #endregion