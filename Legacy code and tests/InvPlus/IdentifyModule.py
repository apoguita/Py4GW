
import PyImGui
from typing import Dict


from Py4GWCoreLib import ImGui, get_texture_for_model
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

class IdentifyModule:
    def __init__(self, inventory_frame: Frame):
        self.MODULE_NAME = "Identify"
        self.inventory_frame = inventory_frame
        self.id_checkboxes: Dict[int, bool] = {}

    #region IdentifyStrip

    #region DrawIDBottomStrip
    def draw_id_bottom_strip(self):
        def _tick_checkboxes(rarity:str, tick_state:bool):
            for bag_id in range(Bags.Backpack, Bags.Bag2 + 1):
                bag_to_check = ItemArray.CreateBagList(bag_id)
                item_array = ItemArray.GetItemArray(bag_to_check)

                for item_id in item_array:
                    if Item.Usage.IsIdentified(item_id) or Item.Usage.IsIDKit(item_id):
                        continue
                    # Ensure checkbox state exists (if it was removed earlier)
                    if item_id not in self.id_checkboxes:
                        self.id_checkboxes[item_id] = False

                    # Apply state based on selected filter
                    if rarity == "All":
                        self.id_checkboxes[item_id] = tick_state
                    elif rarity == "White" and Item.Rarity.IsWhite(item_id):
                        self.id_checkboxes[item_id] = tick_state
                    elif rarity == "Blue" and Item.Rarity.IsBlue(item_id):
                        self.id_checkboxes[item_id] = tick_state
                    elif rarity == "Purple" and Item.Rarity.IsPurple(item_id):
                        self.id_checkboxes[item_id] = tick_state
                    elif rarity == "Gold" and Item.Rarity.IsGold(item_id):
                        self.id_checkboxes[item_id] = tick_state
                    elif rarity == "Green" and Item.Rarity.IsGreen(item_id):
                        self.id_checkboxes[item_id] = tick_state

            # Remove checkbox states that are set to False
            for item_id in list(self.id_checkboxes):
                if not self.id_checkboxes[item_id]:
                    del self.id_checkboxes[item_id]

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

        if PyImGui.begin("IDButtonsWindow", window_flags):
            if PyImGui.begin_table("IDButtonsTable", 2, table_flags):
                PyImGui.table_setup_column("Buttons", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("MainButton", PyImGui.TableColumnFlags.WidthFixed, 40)

                PyImGui.table_next_row()
                PyImGui.table_next_column()

                if game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##IDAllButton","Select All", width=20, height=20, color=ColorPalette.GetColor("GW_Disabled")):
                    _tick_checkboxes("All", True)


                PyImGui.same_line(0,3)
                PyImGui.text("|")
                PyImGui.same_line(0,3)

                if game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##IDWhitesButton","Select All Whites", width=20, height=20, color=ColorPalette.GetColor("GW_White")):
                    _tick_checkboxes("White", True)

                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##IDBluesButton","Select All Blues", width=20, height=20, color=ColorPalette.GetColor("GW_Blue")):
                    _tick_checkboxes("Blue", True)

                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##IDPurplesButton","Select All Purples", width=20, height=20, color=ColorPalette.GetColor("GW_Purple")):
                    _tick_checkboxes("Purple", True)

                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##IDGoldsButton","Select All Golds", width=20, height=20, color=ColorPalette.GetColor("GW_Gold")):
                    _tick_checkboxes("Gold", True)

                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##IDGreensButton","Select All Greens", width=20, height=20, color=ColorPalette.GetColor("GW_Green")):
                    _tick_checkboxes("Green", True)

                #next row of buttons
                if game_button(IconsFontAwesome5.ICON_SQUARE,"##IDClearAllButton","Clear All", width=20, height=20, color=ColorPalette.GetColor("GW_Disabled")):
                    _tick_checkboxes("All", False)

                PyImGui.same_line(0,3)
                PyImGui.text("|")
                PyImGui.same_line(0,3)

                if game_button(IconsFontAwesome5.ICON_SQUARE,"##IDClearWhitesButton","Clear Whites", width=20, height=20, color=ColorPalette.GetColor("GW_White")):
                    _tick_checkboxes("White", False)

                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_SQUARE,"##IDClearBluesButton","Clear Blues", width=20, height=20, color=ColorPalette.GetColor("GW_Blue")):
                    _tick_checkboxes("Blue", False)

                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_SQUARE,"##IDClearPurplesButton","Clear Purples", width=20, height=20, color=ColorPalette.GetColor("GW_Purple")):
                    _tick_checkboxes("Purple", False)

                PyImGui.same_line(0,3)
                if game_button(IconsFontAwesome5.ICON_SQUARE,"##IDClearGoldsButton","Clear Golds", width=20, height=20, color=ColorPalette.GetColor("GW_Gold")):
                    _tick_checkboxes("Gold", False)
                PyImGui.same_line(0,3)

                if game_button(IconsFontAwesome5.ICON_SQUARE,"##IDClearGreensButton","Clear Greens", width=20, height=20, color=ColorPalette.GetColor("GW_Green")):
                    _tick_checkboxes("Green", False)

            PyImGui.table_next_column()
            texture_file = get_texture_for_model(ModelID.Superior_Identification_Kit)
            if ImGui.ImageButton("##text_unique_name", texture_file, 45, 45):
                GLOBAL_CACHE.Coroutines.append(IdentifyCheckedItems(self.id_checkboxes))
            ImGui.show_tooltip("Identify selected items.")    

            PyImGui.end_table()
                        
        PyImGui.end()
        PyImGui.pop_style_var(2)
    
    
    #endregion
    
    
    #region ColorizeIDMasks       
    def colorize_id_masks(self):
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
                
                if Item.Usage.IsIdentified(item_id) and not Item.Usage.IsIDKit(item_id):
                    frame_color = _get_frame_color("Disabled")
                    frame_outline_color = _get_frame_outline_color("Disabled")
                
                UIManager().DrawFrame(frame_id, frame_color)
                UIManager().DrawFrameOutline(frame_id, frame_outline_color)
                
                #--------------- Checkboxes ---------------
                if not Item.Usage.IsIdentified(item_id) and not Item.Usage.IsIDKit(item_id):
                    if item_id not in self.id_checkboxes:
                        self.id_checkboxes[item_id] = False
                    
                    left,top, right, bottom = UIManager.GetFrameCoords(frame_id)
                    self.id_checkboxes[item_id] = ImGui.floating_checkbox(
                        f"{item_id}", 
                        self.id_checkboxes[item_id], 
                        right -25, 
                        bottom-25,
                        width=25,
                        height=25,
                        color = _get_checkbox_color(rarity)
                    )
                            
                # Remove checkbox states that are set to False
                for item_id in list(self.id_checkboxes):
                    if not self.id_checkboxes[item_id]:
                        del self.id_checkboxes[item_id]
         
    #endregion