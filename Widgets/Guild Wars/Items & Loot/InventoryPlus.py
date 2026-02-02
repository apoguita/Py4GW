import Py4GW
import PyImGui
from Py4GWCoreLib import *

from Widgets.Config.InvPlus.ColorizeModule import ColorizeModule
from Widgets.Config.InvPlus.GUI_Helpers import (TabIcon,Frame,floating_game_button)
from Widgets.Config.InvPlus.IdentifyModule import IdentifyModule
from Widgets.Config.InvPlus.SalvageModule import SalvageModule
from Widgets.Config.InvPlus.XunlaiModule import XunlaiModule
from Widgets.Config.InvPlus.AutoHandlerModule import AutoHandlderModule
from Widgets.Config.InvPlus.MerchantModule import MerchantModule
from Widgets.Config.InvPlus.LootModule import LootModule

MODULE_NAME = "Inventory +"

    
#region WidgetUI
class WidgetUI:     
    def __init__(self):
        self.inventory_frame_id = 0
        self.inventory_frame = Frame(0)
        self.tab_icons: List[TabIcon] = []
        self.initialize_tab_icons()
        self.selected_tab_icon_index = 0
        
        self.colorize_module = ColorizeModule(self.inventory_frame)
        self.identify_module = IdentifyModule(self.inventory_frame)
        self.salvage_module = SalvageModule(self.inventory_frame)
        self.xunlai_module = XunlaiModule(self.inventory_frame)
        self.auto_handler_module = AutoHandlderModule(self.inventory_frame)
        self.merchant_module = MerchantModule(self.inventory_frame)
        self.loot_module = LootModule(self.inventory_frame)
        
        self.widget_active = True
        
        
    def set_inventory_frame_id(self, inventory_frame_id):
        self.inventory_frame_id = inventory_frame_id
        self.inventory_frame.set_frame_id(inventory_frame_id)
        
    def initialize_tab_icons(self):
        # Initialize tab icons here if needed
        self.tab_icons.append(TabIcon(icon_name="##ColorizeTab",
                            icon=IconsFontAwesome5.ICON_PALETTE,
                            icon_color=Color(255, 0, 0, 255),
                            icon_tooltip="Inventory+",
                            rainbow_color=True))
        self.tab_icons.append(TabIcon(icon_name="##AutoHandlerTab",
                            icon=IconsFontAwesome5.ICON_STOPWATCH,
                            icon_tooltip="AutoHandler"))
        self.tab_icons.append(TabIcon(icon_name="##IDTab",
                            icon=IconsFontAwesome5.ICON_QUESTION_CIRCLE,
                            icon_tooltip="Mass ID"))
        self.tab_icons.append(TabIcon(icon_name="##SalvageTab",
                            icon=IconsFontAwesome5.ICON_RECYCLE,
                            icon_tooltip="Mass Salvage"))
        self.tab_icons.append(TabIcon(icon_name="##XunlaiVaultTab",
                            icon=IconsFontAwesome5.ICON_BOX_OPEN,
                            icon_tooltip="Xunlai Vault"))
        self.tab_icons.append(TabIcon(icon_name="##TradeTab",
                            icon=IconsFontAwesome5.ICON_BALANCE_SCALE,
                            icon_tooltip="Merchants"))
        self.tab_icons.append(TabIcon(icon_name="##PlayerTradeTab",
                            icon=IconsFontAwesome5.ICON_HANDSHAKE,
                            icon_tooltip="Player Trade"))
        self.tab_icons.append(TabIcon(icon_name="##LootfilterTab",
                            icon=IconsFontAwesome5.ICON_FILTER,
                            icon_tooltip="Lootfilter (WIP)"))
    
    #endregion

    
    #region WidgetToggleButton
    def draw_widget_toggle_button(self):
        x = self.inventory_frame.right - 43
        y = self.inventory_frame.top + 2
        color = Color(0, 255, 0, 255) if self.widget_active else Color(255, 0, 0, 255)
        tooltip = "Inventory + Active" if self.widget_active else "Inventory + Inactive"
        if floating_game_button("O", "InvPlus", tooltip,x, y, width=13, height=13, color=color):
            self.widget_active = not self.widget_active
            message = "Active" if self.widget_active else "Inactive"
            Py4GW.Console.Log(MODULE_NAME, f"Inventory + widget is now {message}.", Py4GW.Console.MessageType.Info)
      
    #endregion
    #region DrawButtonStrip      
    def draw_button_strip(self):
        x = self.inventory_frame.left -29
        y = self.inventory_frame.top
        width = 35
        height = self.inventory_frame.height -5
        compact_mode = False
        if height < 190:
            #height = 190
            width = 60
            x = x - 30
            compact_mode = True
        
        PyImGui.set_next_window_pos(x, y)
        PyImGui.set_next_window_size(width, height)

        flags = (
            PyImGui.WindowFlags.NoCollapse |
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.AlwaysAutoResize
        )
        
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 5, 5)
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0, 0)
        
        if PyImGui.begin("Inventory + Tabs", flags):
            # Draw the tab icons
            for index, icon in enumerate(self.tab_icons):
                icon.advance_rainbow_color()
                toggle_status = False
                if self.selected_tab_icon_index == index:
                    toggle_status = True

                if icon.rainbow_color:
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, icon.icon_color.to_tuple_normalized())

                toggle_status =  ImGui.toggle_button(icon.icon + icon.icon_name, toggle_status, width=25, height=25)
                if icon.rainbow_color:
                    PyImGui.pop_style_color(1)
                if toggle_status:
                    self.selected_tab_icon_index = self.tab_icons.index(icon)
                ImGui.show_tooltip(icon.icon_tooltip)
                
                if compact_mode and (index % 2 == 0):
                    PyImGui.same_line(0, 3)

        PyImGui.end()
        PyImGui.pop_style_var(2)
        
    #endregion

 
    def draw_options(self):
        selected_tab = self.tab_icons[self.selected_tab_icon_index]
        if selected_tab.icon_name == "##ColorizeTab":
            self.colorize_module.draw_colorize_bottom_strip()
            self.colorize_module.colorize_items()
            self.colorize_module.colorize_vault_items()
        elif selected_tab.icon_name == "##AutoHandlerTab":
            self.auto_handler_module.DrawAutoHandler()
            self.auto_handler_module.show_model_id_dialog_popup()
            self.auto_handler_module.show_item_type_dialog_popup()
        elif selected_tab.icon_name == "##IDTab":
            self.identify_module.draw_id_bottom_strip()
            self.identify_module.colorize_id_masks()
        elif selected_tab.icon_name == "##SalvageTab":
            self.salvage_module.draw_salvage_bottom_strip()
            self.salvage_module.colorize_salvage_masks()
        elif selected_tab.icon_name == "##XunlaiVaultTab":
            if not Inventory.IsStorageOpen():
                Inventory.OpenXunlaiWindow()
            self.colorize_module.colorize_items()
            self.colorize_module.colorize_vault_items()
            
            self.xunlai_module.draw_xunlai_bottom_strip()
            
            if self.xunlai_module.show_transfer_buttons:
                self.xunlai_module.draw_deposit_buttons()
                self.xunlai_module.draw_withdraw_buttons()
        elif selected_tab.icon_name == "##TradeTab":
            self.merchant_module.colorize_merchants()
            if self.merchant_module.merchant_frame_exists:
                self.merchant_module.draw_merchants_bottom_strip()
        elif selected_tab.icon_name == "##PlayerTradeTab":
            pass
        elif selected_tab.icon_name == "##LootfilterTab":
            self.loot_module.DrawLootConfig()
   
   
    #region AtuoHandler

widget_config = WidgetUI()

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Inventory +", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    #description
    PyImGui.text("Handles Identifying, Salvaging, Merchant Buying/Selling, Xunlai Vault management and more.")
    PyImGui.text("All features are accessible via the Inventory Window (F9).")

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Mass Identify checked items in your inventory.")
    PyImGui.bullet_text("Mass Salvage checked items in your inventory.")
    PyImGui.bullet_text("Buy and Sell items to Merchants automatically based on your settings.")
    PyImGui.bullet_text("Deposit and Withdraw items from your Xunlai Vault automatically.")
    PyImGui.bullet_text("Colorize items in your Inventory and Xunlai Vault based on rarity and type.")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")

    PyImGui.end_tooltip()
    

def main():
    global widget_config
    try:
        if not widget_config.auto_handler_module.update(): return
        widget_config.set_inventory_frame_id(widget_config.auto_handler_module.get_inventory_frame())

        widget_config.draw_widget_toggle_button()
        
        if not widget_config.widget_active: return  
        
        widget_config.draw_button_strip()
        widget_config.draw_options()
        

    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


    
if __name__ == "__main__":
    main()
