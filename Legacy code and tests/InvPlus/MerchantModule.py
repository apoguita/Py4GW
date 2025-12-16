
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
from Py4GWCoreLib import Trading
from Py4GWCoreLib import Utils
from Py4GWCoreLib import ConsoleLog
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
                                            XUNLAI_VAULT_FRAME_HASH,
                                            MERCHANT_FRAME
                            )         
from Widgets.InvPlus.Coroutines import MerchantCheckedItems
from Widgets.InvPlus.Coroutines import BuyMerchantItems

class MerchantModule:
    def __init__(self, inventory_frame: Frame):
        self.MODULE_NAME = "Merchant"
        self.inventory_frame = inventory_frame
        self.merchant_checkboxes:Dict[int, bool] = {}
        self.selected_combo_merchant = 0
        self.merchant_buy_quantity = 0
        self.merchant_frame_exists = False

    def _is_merchant(self):
        merchant_item_list = Trading.Trader.GetOfferedItems()
        merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]
        
        salvage_kit = ModelID.Salvage_Kit.value

        if salvage_kit in merchant_item_models:
            return True
        return False
    
    def _is_material_trader(self):
        merchant_item_list = Trading.Trader.GetOfferedItems()
        merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]
        
        wood_planks = ModelID.Wood_Plank.value

        if wood_planks in merchant_item_models:
            return True
        return False
    
    def _is_rare_material_trader(self):
        merchant_item_list = Trading.Trader.GetOfferedItems()
        merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]
        
        glob_of_ectoplasm = ModelID.Glob_Of_Ectoplasm.value

        if glob_of_ectoplasm in merchant_item_models:
            return True
        return False
    
    def _is_rune_trader(self):
        merchant_item_list = Trading.Trader.GetOfferedItems()
        merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]
        
        rune_of_superior_vigor = ModelID.Rune_Of_Superior_Vigor.value

        if rune_of_superior_vigor in merchant_item_models:
            return True
        return False
    
    def _is_scroll_trader(self):
        merchant_item_list = Trading.Trader.GetOfferedItems()
        merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]
        
        scroll_of_berserkers_insitght = ModelID.Scroll_Of_Berserkers_Insight.value

        if scroll_of_berserkers_insitght in merchant_item_models:
            return True
        return False
    
    def _is_dye_trader(self):
        merchant_item_list = Trading.Trader.GetOfferedItems()
        merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]
        
        vial_of_dye = ModelID.Vial_Of_Dye.value

        if vial_of_dye in merchant_item_models and not self._is_material_trader():
            return True
        return False
    
    def _get_merchant_minimum_quantity(self) -> int:
        required_quantity = 10 #if is_material_trader else 1
        if not self._is_material_trader():
            required_quantity = 1
            
        return required_quantity
        
        
    def colorize_merchants(self):
        merchant_frame_id = UIManager.GetFrameIDByHash(MERCHANT_FRAME)
        merchant_frame_exists = UIManager.FrameExists(merchant_frame_id)
        if not merchant_frame_exists:
            content_frame = UIManager.GetChildFrameID(_get_parent_hash(), [0])
            left, top, right, bottom = UIManager.GetFrameCoords(content_frame)
            y_offset = 2
            x_offset = 0
            height = bottom - top + y_offset
            width = right - left + x_offset
            UIManager().DrawFrame(content_frame, Utils.RGBToColor(0, 0, 0, 255))
            flags = ( PyImGui.WindowFlags.NoCollapse | 
                    PyImGui.WindowFlags.NoTitleBar |
                    PyImGui.WindowFlags.NoResize
            )
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
            
            PyImGui.set_next_window_pos(left, top)
            PyImGui.set_next_window_size(width, height)
            
            if PyImGui.begin("MerchantDeny",True, flags):
                PyImGui.text_wrapped("Aproach a Merchant to use the Merchant features.")
                    
            PyImGui.end()
            PyImGui.pop_style_var(1)
            self.merchant_frame_exists = False
            return
        
        self.merchant_frame_exists = True
     
        merchant_item_list = Trading.Trader.GetOfferedItems()
        merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]

        for bag_id in range(Bags.Backpack, Bags.Bag2+1):
            bag_to_check = ItemArray.CreateBagList(bag_id)
            item_array = ItemArray.GetItemArray(bag_to_check)
            
            for item_id in item_array:
                model = Item.GetModelID(item_id)
                _,rarity = Item.Rarity.GetRarity(item_id)
                slot = Item.GetSlot(item_id)
                quantity = Item.Properties.GetQuantity(item_id)
                required_quantity = self._get_merchant_minimum_quantity()

                frame_id = UIManager.GetChildFrameID(_get_parent_hash(), _get_offsets(bag_id, slot))
                is_visible = UIManager.FrameExists(frame_id)
                if not is_visible:
                    continue
                
                frame_color = _get_frame_color(rarity)
                frame_outline_color = _get_frame_outline_color(rarity)
                
                is_on_list = model in merchant_item_models
                
                if self._is_merchant() and Item.Properties.GetValue(item_id) >= 1:
                    is_on_list = True
                
                
                enough_quantity = quantity >= required_quantity
                if not (is_on_list and enough_quantity):
                    frame_color = _get_frame_color("Disabled")
                    frame_outline_color = _get_frame_outline_color("Disabled")
                
                UIManager().DrawFrame(frame_id, frame_color)
                UIManager().DrawFrameOutline(frame_id, frame_outline_color)
                
                #--------------- Checkboxes ---------------
                
                if is_on_list and enough_quantity:
                    if item_id not in self.merchant_checkboxes:
                        self.merchant_checkboxes[item_id] = False
                    
                    left,top, right, bottom = UIManager.GetFrameCoords(frame_id)
                    self.merchant_checkboxes[item_id] = ImGui.floating_checkbox(
                        f"{item_id}", 
                        self.merchant_checkboxes[item_id], 
                        right -25, 
                        bottom-25,
                        width=25,
                        height=25,
                        color = _get_checkbox_color(rarity)
                    )
                            
                # Remove checkbox states that are set to False
                for item_id in list(self.merchant_checkboxes):
                    if not self.merchant_checkboxes[item_id]:
                        del self.merchant_checkboxes[item_id]
        
        #end merchant test area
        

        
    def draw_merchants_bottom_strip(self): 
        def _tick_checkboxes(rarity: str, tick_state: bool):
            merchant_item_list = Trading.Trader.GetOfferedItems()
            merchant_item_models = [Item.GetModelID(item_id) for item_id in merchant_item_list]
            required_quantity = self._get_merchant_minimum_quantity()

            for bag_id in range(Bags.Backpack, Bags.Bag2 + 1):
                bag_to_check = ItemArray.CreateBagList(bag_id)
                item_array = ItemArray.GetItemArray(bag_to_check)

                for item_id in item_array:
                    model = Item.GetModelID(item_id)
                    quantity = Item.Properties.GetQuantity(item_id)

                    if self._is_merchant() and Item.Properties.GetValue(item_id) >= 1:
                        is_on_list = True
                    else:
                        is_on_list = model in merchant_item_models

                    if not is_on_list or quantity < required_quantity:
                        continue

                    # Apply state based on selected rarity
                    if rarity == "All":
                        self.merchant_checkboxes[item_id] = tick_state
                    elif rarity == "White" and Item.Rarity.IsWhite(item_id):
                        self.merchant_checkboxes[item_id] = tick_state
                    elif rarity == "Blue" and Item.Rarity.IsBlue(item_id):
                        self.merchant_checkboxes[item_id] = tick_state
                    elif rarity == "Purple" and Item.Rarity.IsPurple(item_id):
                        self.merchant_checkboxes[item_id] = tick_state
                    elif rarity == "Gold" and Item.Rarity.IsGold(item_id):
                        self.merchant_checkboxes[item_id] = tick_state
                    elif rarity == "Green" and Item.Rarity.IsGreen(item_id):
                        self.merchant_checkboxes[item_id] = tick_state

            # Clean up unchecked checkboxes
            for item_id in list(self.merchant_checkboxes):
                if not self.merchant_checkboxes[item_id]:
                    del self.merchant_checkboxes[item_id]

                
            
        
        x = self.inventory_frame.left +5
        y = self.inventory_frame.bottom
        width = self.inventory_frame.width
        height = 57
        
        PyImGui.set_next_window_pos(x, y)
        PyImGui.set_next_window_size(0, height)

        window_flags = (
            PyImGui.WindowFlags.NoCollapse |
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.AlwaysAutoResize
        )
        
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 5, 5)
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0, 0)
        
        table_flags = (
            PyImGui.TableFlags.BordersInnerV |
            PyImGui.TableFlags.NoPadOuterX
        )
        
        if PyImGui.begin("MerchButtonsWindow", window_flags):
            if PyImGui.begin_table("MerchButtonsTable", 4, table_flags):
                PyImGui.table_setup_column("Buttons", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("MainButton", PyImGui.TableColumnFlags.WidthFixed, 40)
                PyImGui.table_setup_column("BuyCombo", PyImGui.TableColumnFlags.WidthFixed, 100)
                PyImGui.table_setup_column("BuyButton", PyImGui.TableColumnFlags.WidthFixed, 40)

                PyImGui.table_next_row()
                PyImGui.table_next_column()
                
                if game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##MerchAllButton","Select All", width=20, height=20, color=ColorPalette.GetColor("GW_Disabled")):
                    _tick_checkboxes("All", True)
                        
                        
                PyImGui.same_line(0,3)
                PyImGui.text("|")
                PyImGui.same_line(0,3)
                
                if game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##MerchWhitesButton","Select All Whites", width=20, height=20, color=ColorPalette.GetColor("GW_White")):
                    print(ColorPalette.GetColor("GW_White").__repr__())
                    _tick_checkboxes("White", True)
                            
                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##MerchBluesButton","Select All Blues", width=20, height=20, color=ColorPalette.GetColor("GW_Blue")):
                    print(ColorPalette.GetColor("GW_Blue").__repr__())
                    _tick_checkboxes("Blue", True)
                            
                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##MerchPurplesButton","Select All Purples", width=20, height=20, color=ColorPalette.GetColor("GW_Purple")):
                    print(ColorPalette.GetColor("GW_Purple").__repr__())
                    _tick_checkboxes("Purple", True)
                            
                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##MerchGoldsButton","Select All Golds", width=20, height=20, color=ColorPalette.GetColor("GW_Gold")):
                    print(ColorPalette.GetColor("GW_Gold").__repr__())
                    _tick_checkboxes("Gold", True)
                            
                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##MerchGreensButton","Select All Greens", width=20, height=20, color=ColorPalette.GetColor("GW_Green")):
                    print(ColorPalette.GetColor("GW_Green").__repr__())
                    _tick_checkboxes("Green", True)           
                            
                #next row of buttons
                if game_button(IconsFontAwesome5.ICON_SQUARE,"##MerchClearAllButton","Clear All", width=20, height=20, color=ColorPalette.GetColor("GW_Disabled")):
                    print(ColorPalette.GetColor("GW_White").__repr__())
                    _tick_checkboxes("All", False) 
                            
                PyImGui.same_line(0,3)
                PyImGui.text("|")
                PyImGui.same_line(0,3)
                
                if game_button(IconsFontAwesome5.ICON_SQUARE,"##MerchClearWhitesButton","Clear Whites", width=20, height=20, color=ColorPalette.GetColor("GW_White")):
                    print(ColorPalette.GetColor("GW_White").__repr__())
                    _tick_checkboxes("White", False)
                    
                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_SQUARE,"##MerchClearBluesButton","Clear Blues", width=20, height=20, color=ColorPalette.GetColor("GW_Blue")):
                    print(ColorPalette.GetColor("GW_Blue").__repr__())
                    _tick_checkboxes("Blue", False)
                    
                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_SQUARE,"##MerchClearPurplesButton","Clear Purples", width=20, height=20, color=ColorPalette.GetColor("GW_Purple")):
                    print(ColorPalette.GetColor("GW_Purple").__repr__())
                    _tick_checkboxes("Purple", False)
                    
                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_SQUARE,"##MerchClearGoldsButton","Clear Golds", width=20, height=20, color=ColorPalette.GetColor("GW_Gold")):
                    print(ColorPalette.GetColor("GW_Gold").__repr__())
                    _tick_checkboxes("Gold", False)
                PyImGui.same_line(0,3)
                
                if game_button(IconsFontAwesome5.ICON_SQUARE,"##MerchClearGreensButton","Clear Greens", width=20, height=20, color=ColorPalette.GetColor("GW_Green")):
                    print(ColorPalette.GetColor("GW_Green").__repr__())
                    _tick_checkboxes("Green", False)
                    
            PyImGui.table_next_column()
            if PyImGui.button(IconsFontAwesome5.ICON_FILE_INVOICE_DOLLAR + "##MerchSellButton", width=40, height=40):
                GLOBAL_CACHE.Coroutines.append(MerchantCheckedItems(self.merchant_checkboxes))
            ImGui.show_tooltip("Sell selected items.")  
            
            PyImGui.table_next_column()
            

            merchant_item_list = Trading.Trader.GetOfferedItems()
            combo_items = [GLOBAL_CACHE.Item.GetName(item_id) for item_id in merchant_item_list]

            PyImGui.push_item_width(100)
            self.selected_combo_merchant = PyImGui.combo("##MerchantCombo", self.selected_combo_merchant, combo_items) 
            self.merchant_buy_quantity = PyImGui.input_int("##MerchantBuyQuantity", self.merchant_buy_quantity, 1, 10, PyImGui.InputTextFlags.NoFlag)
            PyImGui.pop_item_width()
            PyImGui.table_next_column()
            if PyImGui.button(IconsFontAwesome5.ICON_SHOPPING_CART + "##MerchBuyButton", width=40, height=40):
                #ConsoleLog(MODULE_NAME, "Buying items from merchant.", Py4GW.Console.MessageType.Info)
                GLOBAL_CACHE.Coroutines.append(BuyMerchantItems(merchant_item_list.copy(), self.selected_combo_merchant, self.merchant_buy_quantity))
            ImGui.show_tooltip("Buy items.")
            
            PyImGui.end_table()
                        
        PyImGui.end()
        PyImGui.pop_style_var(2)