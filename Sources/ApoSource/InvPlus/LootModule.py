import Py4GW
import PyImGui

from Py4GWCoreLib import ColorPalette, get_texture_for_model
from Py4GWCoreLib import IconsFontAwesome5
from Py4GWCoreLib import ImGui
#from Py4GWCoreLib import LootConfig
from Py4GWCoreLib import LootConfig
from Py4GWCoreLib import ModelID
from Py4GWCoreLib import UIManager
from Py4GWCoreLib import Utils
from Sources.ApoSource.InvPlus.GUI_Helpers import (Frame, game_toggle_button, _get_parent_hash)

#region LootGroups

class LootModule:
    def __init__(self, inventory_frame: Frame):
        self.MODULE_NAME = "Loot Config"
        self.inventory_frame = inventory_frame
        self.loot_singleton = LootConfig()
        
    def DrawLootConfig(self):
        global global_vars
        
        content_frame = UIManager.GetChildFrameID(_get_parent_hash(), [0])
        left, top, right, bottom = UIManager.GetFrameCoords(content_frame)
        y_offset = 2
        x_offset = 0
        height = bottom - top + y_offset
        width = right - left + x_offset
        if width < 100:
            width = 100
        if height < 100:
            height = 100
            
        UIManager().DrawFrame(content_frame, Utils.RGBToColor(0, 0, 0, 255))
        

        flags = ( PyImGui.WindowFlags.NoCollapse | 
                PyImGui.WindowFlags.NoTitleBar |
                PyImGui.WindowFlags.NoResize
        )
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
        
        PyImGui.set_next_window_pos(left, top)
        PyImGui.set_next_window_size(width, height)
        
        if PyImGui.begin("Embedded Loot config",True, flags):
           
            PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 5, 5)
            PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0, 0)
            
            if PyImGui.button(IconsFontAwesome5.ICON_SAVE + "##save_loot_config", width=25, height=25):
                pass
            PyImGui.show_tooltip("Save Loot Config")
            
            PyImGui.same_line(0,-1)
            PyImGui.text("|")
            PyImGui.same_line(0,-1)
            if PyImGui.button(IconsFontAwesome5.ICON_FILE_EXPORT + "##export_loot_config", width=25, height=25):
                # Reset loot config logic here
                pass
            PyImGui.show_tooltip("Export Loot Config to File")
            
            PyImGui.same_line(0,-1)
            if PyImGui.button(IconsFontAwesome5.ICON_FILE_IMPORT + "##import_loot_config", width=25, height=25):
                # Import loot config logic here
                pass
            PyImGui.show_tooltip("Import Loot Config from File")
            PyImGui.separator()

            state = self.loot_singleton.loot_whites
            color = ColorPalette.GetColor("GW_White")
            if game_toggle_button("##BasicLootFilterWhiteButton","Loot White Items",state, width=20, height=20, color=color):
                self.loot_singleton.loot_whites = not self.loot_singleton.loot_whites
            PyImGui.same_line(0,3)  
            state = self.loot_singleton.loot_blues
            color = ColorPalette.GetColor("GW_Blue")
            if game_toggle_button("##BasicLootFilterBlueButton","Loot Blue Items",state, width=20, height=20, color=color):
                self.loot_singleton.loot_blues = not self.loot_singleton.loot_blues
            PyImGui.same_line(0,3)
            state = self.loot_singleton.loot_purples
            color = ColorPalette.GetColor("GW_Purple")  
            if game_toggle_button("##BasicLootFilterPurpleButton","Loot Purple Items",state, width=20, height=20, color=color):
                self.loot_singleton.loot_purples = not self.loot_singleton.loot_purples
            PyImGui.same_line(0,3)
            state = self.loot_singleton.loot_golds
            color = ColorPalette.GetColor("GW_Gold")
            if game_toggle_button("##BasicLootFilterGoldButton","Loot Gold Items",state, width=20, height=20, color=color):
                self.loot_singleton.loot_golds = not self.loot_singleton.loot_golds
            PyImGui.same_line(0,3)
            state = self.loot_singleton.loot_greens
            color = ColorPalette.GetColor("GW_Green")
            if game_toggle_button("##BasicLootFilterGreenButton","Loot Green Items",state, width=20, height=20, color=color):
                self.loot_singleton.loot_greens = not self.loot_singleton.loot_greens
            PyImGui.same_line(0,3)
            self.loot_singleton.loot_gold_coins = ImGui.toggle_button(IconsFontAwesome5.ICON_COINS + "##BasicLootFilterGoldCoinsButton", self.loot_singleton.loot_gold_coins, width=20, height=20)
            ImGui.show_tooltip("Loot Gold Coins")
            PyImGui.separator()

            if PyImGui.tree_node("Advanced Loot Filters"):
                for group_name, group_items in self.loot_singleton.LootGroups.items():
                    if PyImGui.tree_node(group_name):
                        for subgroup, items in group_items.items():
                            if PyImGui.tree_node(subgroup):
                                if PyImGui.begin_table(f"##table_{group_name}_{subgroup}", 3, PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg):
                                    col = 0
                                    for item_model_id in items:
                                        item_texture = get_texture_for_model(item_model_id)
                                        enum_entry = ModelID(item_model_id)
                                        enum_name = ' '.join(word.capitalize() for word in enum_entry.name.split('_'))

                                        PyImGui.table_next_column()
                                        PyImGui.begin_group()

                                        state = self.loot_singleton.IsWhitelisted(item_model_id)
                                        new_state = ImGui.image_toggle_button(
                                            f"##loot_toggle_{item_model_id}",
                                            item_texture,
                                            state,
                                            width=48,
                                            height=48
                                        )

                                        if new_state != state:
                                            if new_state:
                                                self.loot_singleton.AddToWhitelist(item_model_id)
                                            else:
                                                self.loot_singleton.RemoveFromWhitelist(item_model_id)

                                        PyImGui.text_wrapped(enum_name)
                                        PyImGui.end_group()

                                        col += 1
                                        if col % 3 == 0:
                                            PyImGui.table_next_row()
                                    PyImGui.end_table()
                                PyImGui.tree_pop()
                        PyImGui.tree_pop()
                PyImGui.tree_pop()

            
        PyImGui.end() 
        PyImGui.pop_style_var(3)