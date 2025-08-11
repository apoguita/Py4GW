
import PyImGui
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
from Py4GWCoreLib.enums import ItemModelTextureMap
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
from Widgets.InvPlus.Coroutines import SalvageCheckedItems

class SalvageModule:   
    def __init__(self, inventory_frame: Frame):
        self.MODULE_NAME = "Salvage"
        self.inventory_frame = inventory_frame
        self.salvage_checkboxes: Dict[int, bool] = {}
        self.keep_salvage_kits = 4
        self.deposit_materials = True

    #region DrawSalvBottomStrip
    def draw_salvage_bottom_strip(self):
        def _tick_checkboxes(rarity:str, tick_state:bool):
            for bag_id in range(Bags.Backpack, Bags.Bag2 + 1):
                bag_to_check = ItemArray.CreateBagList(bag_id)
                item_array = ItemArray.GetItemArray(bag_to_check)

                for item_id in item_array:
                    if not Item.Usage.IsSalvageable(item_id):
                        continue
                    
                    if Item.Usage.IsSalvageKit(item_id):
                        continue
                    
                    if not (Item.Rarity.IsWhite(item_id) or Item.Usage.IsIdentified(item_id)):
                        continue
                    
                    # Ensure checkbox state exists (if it was removed earlier)
                    if item_id not in self.salvage_checkboxes:
                        self.salvage_checkboxes[item_id] = False

                    # Apply state based on selected filter
                    if rarity == "All":
                        self.salvage_checkboxes[item_id] = tick_state
                    elif rarity == "White" and Item.Rarity.IsWhite(item_id):
                        self.salvage_checkboxes[item_id] = tick_state
                    elif rarity == "Blue" and Item.Rarity.IsBlue(item_id):
                        self.salvage_checkboxes[item_id] = tick_state
                    elif rarity == "Purple" and Item.Rarity.IsPurple(item_id):
                        self.salvage_checkboxes[item_id] = tick_state
                    elif rarity == "Gold" and Item.Rarity.IsGold(item_id):
                        self.salvage_checkboxes[item_id] = tick_state
                    elif rarity == "Green" and Item.Rarity.IsGreen(item_id):
                        self.salvage_checkboxes[item_id] = tick_state
                        
            # Remove checkbox states that are set to False
            for item_id in list(self.salvage_checkboxes):
                if not self.salvage_checkboxes[item_id]:
                    del self.salvage_checkboxes[item_id]
            
        
        
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
        
        if PyImGui.begin("SalvageButtonsWindow", window_flags):
            if PyImGui.begin_table("SalvageButtonsTable", 3, table_flags):
                PyImGui.table_setup_column("Buttons", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("MainButton", PyImGui.TableColumnFlags.WidthFixed, 40)
                PyImGui.table_setup_column("SalvageOptions", PyImGui.TableColumnFlags.WidthFixed, 150)

                PyImGui.table_next_row()
                PyImGui.table_next_column()
                
                if game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##SalvageAllButton","Select All", width=20, height=20, color=ColorPalette.GetColor("GW_Disabled")):
                    _tick_checkboxes("All", True)
                        
                        
                PyImGui.same_line(0,3)
                PyImGui.text("|")
                PyImGui.same_line(0,3)
                
                if game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##SalvageWhitesButton","Select All Whites", width=20, height=20, color=ColorPalette.GetColor("GW_White")):
                    print(ColorPalette.GetColor("GW_White").__repr__())
                    _tick_checkboxes("White", True)
                            
                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##SalvageBluesButton","Select All Blues", width=20, height=20, color=ColorPalette.GetColor("GW_Blue")):
                    print(ColorPalette.GetColor("GW_Blue").__repr__())
                    _tick_checkboxes("Blue", True)
                            
                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##SalvagePurplesButton","Select All Purples", width=20, height=20, color=ColorPalette.GetColor("GW_Purple")):
                    print(ColorPalette.GetColor("GW_Purple").__repr__())
                    _tick_checkboxes("Purple", True)
                            
                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##SalvageGoldsButton","Select All Golds", width=20, height=20, color=ColorPalette.GetColor("GW_Gold")):
                    print(ColorPalette.GetColor("GW_Gold").__repr__())
                    _tick_checkboxes("Gold", True)
                            
                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##SalvageGreensButton","Select All Greens", width=20, height=20, color=ColorPalette.GetColor("GW_Green")):
                    print(ColorPalette.GetColor("GW_Green").__repr__())
                    _tick_checkboxes("Green", True)           
                            
                #next row of buttons
                if game_button(IconsFontAwesome5.ICON_SQUARE,"##SalvageClearAllButton","Clear All", width=20, height=20, color=ColorPalette.GetColor("GW_Disabled")):
                    print(ColorPalette.GetColor("GW_White").__repr__())
                    _tick_checkboxes("All", False) 
                            
                PyImGui.same_line(0,3)
                PyImGui.text("|")
                PyImGui.same_line(0,3)
                
                if game_button(IconsFontAwesome5.ICON_SQUARE,"##SalvageClearWhitesButton","Clear Whites", width=20, height=20, color=ColorPalette.GetColor("GW_White")):
                    print(ColorPalette.GetColor("GW_White").__repr__())
                    _tick_checkboxes("White", False)
                    
                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_SQUARE,"##SalvageClearBluesButton","Clear Blues", width=20, height=20, color=ColorPalette.GetColor("GW_Blue")):
                    print(ColorPalette.GetColor("GW_Blue").__repr__())
                    _tick_checkboxes("Blue", False)
                    
                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_SQUARE,"##SalvageClearPurplesButton","Clear Purples", width=20, height=20, color=ColorPalette.GetColor("GW_Purple")):
                    print(ColorPalette.GetColor("GW_Purple").__repr__())
                    _tick_checkboxes("Purple", False)
                    
                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_SQUARE,"##SalvageClearGoldsButton","Clear Golds", width=20, height=20, color=ColorPalette.GetColor("GW_Gold")):
                    print(ColorPalette.GetColor("GW_Gold").__repr__())
                    _tick_checkboxes("Gold", False)
                PyImGui.same_line(0,3)
                
                if game_button(IconsFontAwesome5.ICON_SQUARE,"##SalvageClearGreensButton","Clear Greens", width=20, height=20, color=ColorPalette.GetColor("GW_Green")):
                    print(ColorPalette.GetColor("GW_Green").__repr__())
                    _tick_checkboxes("Green", False)
                    
            PyImGui.table_next_column()
            texture_file = ItemModelTextureMap[ModelID.Salvage_Kit.value]
            if ImGui.ImageButton("##text_unique_name", texture_file, 45, 45):
                GLOBAL_CACHE.Coroutines.append(SalvageCheckedItems(self.salvage_checkboxes,
                                                                   self.keep_salvage_kits, 
                                                                   self.deposit_materials))
            ImGui.show_tooltip("Salvage selected items.")    
            
            PyImGui.table_next_column()
            self.deposit_materials = PyImGui.checkbox("Deposit Materials", self.deposit_materials)
            self.keep_salvage_kits = PyImGui.input_int("Keep Kits", self.keep_salvage_kits)

            PyImGui.end_table()
                        
        PyImGui.end()
        PyImGui.pop_style_var(2)
    
    
    #endregion
    
    #region ColorizeSalvageMasks       
    def colorize_salvage_masks(self):
        for bag_id in range(Bags.Backpack, Bags.Bag2+1):
            bag_to_check = ItemArray.CreateBagList(bag_id)
            item_array = ItemArray.GetItemArray(bag_to_check)
            
            for item_id in item_array:
                _,rarity = Item.Rarity.GetRarity(item_id)
                slot = Item.GetSlot(item_id)

                frame_id = UIManager.GetChildFrameID(_get_parent_hash(), _get_offsets(bag_id, slot))
                is_visible = UIManager.FrameExists(frame_id)
                if not is_visible:
                    continue
                
                frame_color = _get_frame_color(rarity)
                frame_outline_color = _get_frame_outline_color(rarity)
                
                is_white =  rarity == "White"
                is_identified = Item.Usage.IsIdentified(item_id)
                is_salvageable = Item.Usage.IsSalvageable(item_id)
                is_salvage_kit = Item.Usage.IsLesserKit(item_id)
                
                if not (((is_white and is_salvageable) or (is_identified and is_salvageable)) or is_salvage_kit):
                    frame_color = _get_frame_color("Disabled")
                    frame_outline_color = _get_frame_outline_color("Disabled")
                
                UIManager().DrawFrame(frame_id, frame_color)
                UIManager().DrawFrameOutline(frame_id, frame_outline_color) 
                
                #--------------- Checkboxes ---------------
                if (((is_white and is_salvageable) or (is_identified and is_salvageable)) and not is_salvage_kit):
                    if item_id not in self.salvage_checkboxes:
                        self.salvage_checkboxes[item_id] = False
                    
                    left,top, right, bottom = UIManager.GetFrameCoords(frame_id)
                    self.salvage_checkboxes[item_id] = ImGui.floating_checkbox(
                        f"{item_id}", 
                        self.salvage_checkboxes[item_id], 
                        right -25, 
                        bottom-25,
                        width=25,
                        height=25,
                        color = _get_checkbox_color(rarity)
                    )
                            
                # Remove checkbox states that are set to False
                for item_id in list(self.salvage_checkboxes):
                    if not self.salvage_checkboxes[item_id]:
                        del self.salvage_checkboxes[item_id]