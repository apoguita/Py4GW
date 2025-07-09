
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
from Py4GWCoreLib import AutoInventoryHandler
from Py4GWCoreLib import Utils
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import Routines
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib.enums import ItemModelTextureMap
from Py4GWCoreLib.enums import WindowID
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

class AutoHandlderModule:
    def __init__(self, inventory_frame: Frame):
        self.MODULE_NAME = "AutoHandler"
        self.inventory_frame = inventory_frame
        self.inventory_frame_exists = False
        self.auto_handler = AutoInventoryHandler()
        self.inventory_check_throttle_timer = ThrottledTimer(100)

    def show_model_id_dialog_popup(self):
        if self.auto_handler.show_dialog_popup:
            PyImGui.open_popup("ModelID Lookup")
            self.auto_handler.show_dialog_popup = False  # trigger only once

        if PyImGui.begin_popup_modal("ModelID Lookup", True,PyImGui.WindowFlags.AlwaysAutoResize):
            PyImGui.text("ModelID Lookup")
            PyImGui.separator()

            # Input + filter mode
            self.auto_handler.model_id_search = PyImGui.input_text("Search", self.auto_handler.model_id_search)
            search_lower = self.auto_handler.model_id_search.strip().lower()

            self.auto_handler.model_id_search_mode = PyImGui.radio_button("Contains", self.auto_handler.model_id_search_mode, 0)
            PyImGui.same_line(0, -1)
            self.auto_handler.model_id_search_mode = PyImGui.radio_button("Starts With", self.auto_handler.model_id_search_mode, 1)

            # Build reverse lookup: model_id → name
            model_id_to_name = {member.value: name for name, member in ModelID.__members__.items()}

            PyImGui.separator()

            if PyImGui.begin_table("ModelIDTable", 2):
                PyImGui.table_setup_column("All Models", PyImGui.TableColumnFlags.WidthFixed)
                PyImGui.table_setup_column("Blacklisted Models", PyImGui.TableColumnFlags.WidthStretch)
            
                PyImGui.table_headers_row()
                PyImGui.table_next_column()
                # LEFT: All Models
                if PyImGui.begin_child("ModelIDList", (295, 375), True, PyImGui.WindowFlags.NoFlag):
                    sorted_model_ids = sorted(
                        [(name, member.value) for name, member in ModelID.__members__.items()],
                        key=lambda x: x[0].lower()
                    )
                    for name, model_id in sorted_model_ids:
                        name_lower = name.lower()
                        if search_lower:
                            if self.auto_handler.model_id_search_mode == 0 and search_lower not in name_lower:
                                continue
                            if self.auto_handler.model_id_search_mode == 1 and not name_lower.startswith(search_lower):
                                continue

                        label = f"{name} ({model_id})"
                        if PyImGui.selectable(label, False, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0)):
                            if model_id not in self.auto_handler.salvage_blacklist:
                                self.auto_handler.salvage_blacklist.append(model_id)
                PyImGui.end_child()

                # RIGHT: Blacklist
                PyImGui.table_next_column()
                if PyImGui.begin_child("BlacklistModelIDList", (295, 375), True, PyImGui.WindowFlags.NoFlag):
                    # Create list of (name, model_id) and sort by name
                    sorted_blacklist = sorted(
                        [(model_id_to_name.get(model_id, "Unknown"), model_id)
                        for model_id in self.auto_handler.salvage_blacklist],
                        key=lambda x: x[0].lower()
                    )

                    for name, model_id in sorted_blacklist:
                        label = f"{name} ({model_id})"
                        if PyImGui.selectable(label, False, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0)):
                            self.auto_handler.salvage_blacklist.remove(model_id)
                PyImGui.end_child()



                PyImGui.end_table()

            if PyImGui.button("Close"):
                PyImGui.close_current_popup()

            PyImGui.end_popup_modal()
    
    def DrawAutoHandler(self):
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
        
        #flags= ImGui.PushTransparentWindow()
        
        flags = ( PyImGui.WindowFlags.NoCollapse | 
                PyImGui.WindowFlags.NoTitleBar |
                PyImGui.WindowFlags.NoResize
        )
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
        
        PyImGui.set_next_window_pos(left, top)
        PyImGui.set_next_window_size(width, height)
        
        if PyImGui.begin("Embedded AutoHandler",True, flags):
            if self.auto_handler.module_active:
                active_button = IconsFontAwesome5.ICON_TOGGLE_ON
                active_tooltip = "AutoHandler is active"
            else:
                active_button = IconsFontAwesome5.ICON_TOGGLE_OFF
                active_tooltip = "AutoHandler is inactive"
                
            self.auto_handler.module_active = ImGui.toggle_button(active_button + "##AutoHandlerActive", self.auto_handler.module_active)
            ImGui.show_tooltip(active_tooltip)
            
            PyImGui.same_line(0,-1)
            PyImGui.text("|")
            PyImGui.same_line(0,-1)
            
            if PyImGui.button(IconsFontAwesome5.ICON_SAVE + "##autosalvsave"):
                self.auto_handler.save_to_ini()
                ConsoleLog(self.MODULE_NAME, "Settings saved to Auto Inv.ini", Py4GW.Console.MessageType.Success)
            ImGui.show_tooltip("Save Settings")
            PyImGui.same_line(0,-1)
            if PyImGui.button(IconsFontAwesome5.ICON_SYNC + "##autosalvreload"):
                self.auto_handler.load_from_ini(self.auto_handler.ini)
                self.auto_handler.lookup_throttle.SetThrottleTime(self.auto_handler._LOOKUP_TIME)
                self.auto_handler.lookup_throttle.Reset()
                ConsoleLog(self.MODULE_NAME, "Settings reloaded from Auto Inv.ini", Py4GW.Console.MessageType.Success)
            ImGui.show_tooltip("Reload Settings")
            
            PyImGui.separator()
            
            PyImGui.text("Lookup Time (ms):")
            PyImGui.same_line(0,-1)
            
            PyImGui.push_item_width(150)
            self.auto_handler._LOOKUP_TIME = PyImGui.input_int("##lookup_time",  self.auto_handler._LOOKUP_TIME)
            PyImGui.pop_item_width()
            ImGui.show_tooltip("Changes will take effect after the next lookup.")
            
            if not GLOBAL_CACHE.Map.IsExplorable():
                PyImGui.text("Auto Lookup only runs in explorable.")
            else:
                remaining = self.auto_handler.lookup_throttle.GetTimeRemaining() / 1000  # convert ms to seconds
                PyImGui.text(f"Next Lookup in: {remaining:.1f} s")
            
            PyImGui.separator()
            
            if PyImGui.begin_tab_bar("AutoID&SalvageTabs"):
                if PyImGui.begin_tab_item("Identification"):
                    state = self.auto_handler.id_whites
                    color = ColorPalette.GetColor("GW_White")
                    if game_toggle_button("##autoIDWhite","Identify White Items",state, width=20, height=20, color=color):
                        self.auto_handler.id_whites = not self.auto_handler.id_whites
                    PyImGui.same_line(0,3)
                    state = self.auto_handler.id_blues
                    color = ColorPalette.GetColor("GW_Blue")
                    if game_toggle_button("##autoIDBlue","Identify Blue Items",state, width=20, height=20, color=color):
                        self.auto_handler.id_blues = not self.auto_handler.id_blues
                        
                    PyImGui.same_line(0,3)
                    state = self.auto_handler.id_purples
                    color = ColorPalette.GetColor("GW_Purple")
                    if game_toggle_button("##autoIDPurple","Identify Purple Items",state, width=20, height=20, color=color):
                        self.auto_handler.id_purples = not self.auto_handler.id_purples
                    PyImGui.same_line(0,3)
                    state = self.auto_handler.id_golds
                    color = ColorPalette.GetColor("GW_Gold")
                    if game_toggle_button("##autoIDGold","Identify Gold Items",state, width=20, height=20, color=color):
                        self.auto_handler.id_golds = not self.auto_handler.id_golds
                        
                    PyImGui.end_tab_item()
                if PyImGui.begin_tab_item("Salvage"):
                    state = self.auto_handler.salvage_whites
                    color = ColorPalette.GetColor("GW_White")
                    if game_toggle_button("##autoSalvageWhite","Salvage White Items",state, width=20, height=20, color=color):
                        self.auto_handler.salvage_whites = not self.auto_handler.salvage_whites
                    
                    PyImGui.same_line(0,3)
                    state = self.auto_handler.salvage_blues
                    color = ColorPalette.GetColor("GW_Blue")
                    if game_toggle_button("##autoSalvageBlue","Salvage Blue Items",state, width=20, height=20, color=color):
                        self.auto_handler.salvage_blues = not self.auto_handler.salvage_blues
                        
                    PyImGui.same_line(0,3)
                    state = self.auto_handler.salvage_purples
                    color = ColorPalette.GetColor("GW_Purple")
                    if game_toggle_button("##autoSalvagePurple","Salvage Purple Items",state, width=20, height=20, color=color):
                        self.auto_handler.salvage_purples = not self.auto_handler.salvage_purples
                        
                    PyImGui.same_line(0,3)
                    state = self.auto_handler.salvage_golds
                    color = ColorPalette.GetColor("GW_Gold")
                    if game_toggle_button("##autoSalvageGold","Salvage Gold Items",state, width=20, height=20, color=color):
                        self.auto_handler.salvage_golds = not self.auto_handler.salvage_golds

                    PyImGui.separator()
                    
                    if PyImGui.collapsing_header("Ignore Items"):
                        PyImGui.text(f"{len(self.auto_handler.salvage_blacklist)} Blacklisted ModelIDs")

                        if PyImGui.button("Manage Ignore List"):
                            self.auto_handler.show_dialog_popup = True

                            
                    PyImGui.end_tab_item()
                if PyImGui.begin_tab_item("Deposit"):
                    self.auto_handler.deposit_materials = ImGui.toggle_button( IconsFontAwesome5.ICON_HAMMER + "##depositmaterials", self.auto_handler.deposit_materials)
                    ImGui.show_tooltip("Deposit Materials")
                    PyImGui.same_line(0,3)
                    self.auto_handler.deposit_trophies = ImGui.toggle_button(IconsFontAwesome5.ICON_TROPHY + "##deposittrophies", self.auto_handler.deposit_trophies)
                    ImGui.show_tooltip("Deposit Trophies")
                    PyImGui.same_line(0,3)
                    self.auto_handler.deposit_event_items = ImGui.toggle_button(IconsFontAwesome5.ICON_HAT_WIZARD + "##depositeventitems", self.auto_handler.deposit_event_items)
                    ImGui.show_tooltip("Deposit Event Items")
                    PyImGui.same_line(0,3)
                    self.auto_handler.deposit_dyes = ImGui.toggle_button(IconsFontAwesome5.ICON_FLASK + "##depositdyes", self.auto_handler.deposit_dyes)
                    ImGui.show_tooltip("Deposit Dyes")
                    
                    PyImGui.same_line(0,3)
                    state = self.auto_handler.deposit_blues
                    color = ColorPalette.GetColor("GW_Blue")
                    
                    if game_toggle_button("##depositBlue","Deposit Blue Items",state, width=20, height=20, color=color):
                        self.auto_handler.deposit_blues = not self.auto_handler.deposit_blues
                    PyImGui.same_line(0,3)
                    state = self.auto_handler.deposit_purples
                    color = ColorPalette.GetColor("GW_Purple")
                    if game_toggle_button("##depositPurple","Deposit Purple Items",state, width=20, height=20, color=color):
                        self.auto_handler.deposit_purples = not self.auto_handler.deposit_purples
                    PyImGui.same_line(0,3)
                    state = self.auto_handler.deposit_golds
                    color = ColorPalette.GetColor("GW_Gold")
                    if game_toggle_button("##depositGold","Deposit Gold Items",state, width=20, height=20, color=color):
                        self.auto_handler.deposit_golds = not self.auto_handler.deposit_golds
                    PyImGui.same_line(0,3)
                    state = self.auto_handler.deposit_greens
                    color = ColorPalette.GetColor("GW_Green")
                    if game_toggle_button("##depositGreen","Deposit Green Items",state, width=20, height=20, color=color):
                        self.auto_handler.deposit_greens = not self.auto_handler.deposit_greens
                    
                    PyImGui.separator()
                    PyImGui.text("Keep Gold:")
                    PyImGui.same_line(0,-1)
                    self.auto_handler.keep_gold = PyImGui.input_int("##keep_gold", self.auto_handler.keep_gold, 1, 1000, PyImGui.InputTextFlags.NoFlag)
                    ImGui.show_tooltip("Keep Gold in inventory, deposit the rest")
                    
                    PyImGui.end_tab_item()
                PyImGui.end_tab_bar()
        PyImGui.end() 
        PyImGui.pop_style_var(1)
        
    def update (self):
        auto_handler = self.auto_handler
        if not Routines.Checks.Map.MapValid():
            self.inventory_frame_exists = False
            self.inventory_frame_id = 0
            auto_handler.lookup_throttle.Reset()
            auto_handler.outpost_handled = False
            return False
        
        if not auto_handler.initialized:
            auto_handler.load_from_ini(auto_handler.ini)
            auto_handler.lookup_throttle.SetThrottleTime(auto_handler._LOOKUP_TIME)
            auto_handler.lookup_throttle.Reset()
            auto_handler.initialized = True
            ConsoleLog(self.MODULE_NAME, "Auto Widget Options initialized", Py4GW.Console.MessageType.Success)
            
        if not GLOBAL_CACHE.Map.IsExplorable():
            auto_handler.lookup_throttle.Stop()
            auto_handler.status = "Idle"
            if not auto_handler.outpost_handled and auto_handler.module_active:
                GLOBAL_CACHE.Coroutines.append(auto_handler.IDSalvageDepositItems())
                auto_handler.outpost_handled = True
        else:      
            if auto_handler.lookup_throttle.IsStopped():
                auto_handler.lookup_throttle.Start()
                auto_handler.status = "Idle"
                
        if auto_handler.lookup_throttle.IsExpired():
            auto_handler.lookup_throttle.SetThrottleTime(auto_handler._LOOKUP_TIME)
            auto_handler.lookup_throttle.Stop()
            if auto_handler.status == "Idle" and auto_handler.module_active:
                GLOBAL_CACHE.Coroutines.append(auto_handler.IDAndSalvageItems())
            auto_handler.lookup_throttle.Start()       
        
        if not UIManager.IsWindowVisible(WindowID.WindowID_InventoryBags):
            self.inventory_frame_exists = False
            self.inventory_frame_id = 0
            return False
        
        if not self.inventory_check_throttle_timer.IsExpired():
            return True
        
        self.inventory_frame_id = UIManager.GetFrameIDByHash(INVENTORY_FRAME_HASH)
        self.inventory_frame_exists = UIManager.FrameExists(self.inventory_frame_id)
        
        return self.inventory_frame_exists  
    
    def get_inventory_frame(self) -> int:
        if not self.inventory_frame_exists:
            return 0
        return self.inventory_frame_id