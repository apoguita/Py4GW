import os

import Py4GW
import PyImGui

from Py4GWCoreLib.ImGui_src.ImGuisrc import ImGui
from Py4GWCoreLib.ImGui_src.types import Alignment
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Inventory import Inventory
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.enums_src.Item_enums import Rarity
from Py4GWCoreLib.enums_src.Region_enums import ServerLanguage
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils

Utils.ClearSubModules("ItemHandling")
from Sources.frenkeyLib.ItemHandling.Items.ItemCache import ITEM_CACHE
from Sources.frenkeyLib.ItemHandling.Mods.ItemMod import ItemMod
from Sources.frenkeyLib.ItemHandling.BTNodes import STORAGE_BAGS, BTNodes
from Sources.frenkeyLib.ItemHandling.Rules.types import SalvageMode


MODULE_NAME = "Item Handling Tests"
MODULE_ICON = "Textures/Module_Icons/Coding.png"
SALVAGE_MODES = [m.name for m in SalvageMode]

INI_KEY = ""
INI_PATH = f"Widgets/{MODULE_NAME}"
INI_FILENAME = f"{MODULE_NAME}.ini"

hovered_item_id = 0
tree : BehaviorTree | None = None
auto_tick = True

RED = Color(255, 0, 0, 255)
GREEN = Color(0, 255, 0, 255)

def main():
    global INI_KEY, hovered_item_id, auto_tick, tree
    ITEM_CACHE.reset()
    
    if not INI_KEY:
        if not os.path.exists(INI_PATH):
            os.makedirs(INI_PATH, exist_ok=True)

        INI_KEY = IniManager().ensure_global_key(
            INI_PATH,
            INI_FILENAME
        )
        
        if not INI_KEY: return
        
        IniManager().load_once(INI_KEY)
    
    if tree:
        try:
            if auto_tick:
                state = tree.tick()
                if state != BehaviorTree.NodeState.RUNNING:
                    Py4GW.Console.Log(MODULE_NAME, f"Behavior tree '{tree.root.name}' finished with state: {state.name}", Py4GW.Console.MessageType.Success if state == BehaviorTree.NodeState.SUCCESS else Py4GW.Console.MessageType.Warning)
                    tree = None                    
                    
        except Exception as e:
            Py4GW.Console.Log(MODULE_NAME, f"Error ticking behavior tree: {e}")
    
    win_open = ImGui.Begin(INI_KEY, MODULE_NAME)
    if win_open:
        ImGui.text_aligned(tree.root.name if tree else "No Tree Loaded", alignment= Alignment.MidCenter, color=GREEN.color_tuple if tree else RED.color_tuple, font_size=16, height=20)
        avail = PyImGui.get_content_region_avail()[0]
        
        PyImGui.begin_disabled(not tree or not auto_tick)
        if ImGui.button("Stop Tree", (avail - 5) / 2):
            auto_tick = False
        PyImGui.end_disabled()      
        
        PyImGui.same_line(0, 5)
        
        PyImGui.begin_disabled(not tree or auto_tick)
        if ImGui.button("Start Tree", (avail - 5) / 2):
            auto_tick = True       
        PyImGui.end_disabled()
        
        PyImGui.separator()
        
        hovered_item_id = Inventory.GetHoveredItemID() or hovered_item_id
        item = ITEM_CACHE.get_item_snapshot(hovered_item_id)
        
        if not item or not item.is_valid:
            hovered_item_id = 0
        
        item_name = item.data.names.get(ServerLanguage.English, "Unknown Item") if item and item.data else f"Unknown {(f"{item.item_type.name}-Item" if item else 'Item')}"
        
        ImGui.input_text("Hovered Item Id", str(hovered_item_id), PyImGui.InputTextFlags.ReadOnly)
        style = ImGui.get_style()
        style.CellPadding.push_style_var_direct(2, 2)
        ImGui.push_font("Regular", 13)
        if PyImGui.begin_table("Item Info", 2, PyImGui.TableFlags.Borders):
            PyImGui.table_setup_column("Property", PyImGui.TableColumnFlags.WidthFixed, 150)
            PyImGui.table_setup_column("Value", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_headers_row()
            
            def add_row(property_name, value):
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                PyImGui.text(property_name)
                PyImGui.table_set_column_index(1)
                PyImGui.text(value)
            
            add_row("Item Data", item.data.names.get(ServerLanguage.English, "N/A") if item and item.data else "N/A")
            add_row("Model ID", str(item.model_id) if item else "N/A")
            add_row("Item Type", str(item.item_type.name) if item else "N/A")
            add_row("Rarity", Rarity(item.rarity).name if item else "N/A")
            add_row("Stack Size", str(item.quantity) if item else "N/A")
                
            PyImGui.end_table()
        style.CellPadding.pop_style_var_direct()
        ImGui.pop_font()
            
        ImGui.separator()
    
        if ImGui.begin_tab_bar("##tab_bar"):
            if ImGui.begin_tab_item("Item Upgrades"):
                ImGui.text("Item Upgrades", 16)                
                if PyImGui.begin_table("Item Upgrades", 2, PyImGui.TableFlags.Borders | PyImGui.TableFlags.Resizable):                    
                    PyImGui.table_setup_column("Upgrade Slot", PyImGui.TableColumnFlags.WidthFixed, 150)
                    PyImGui.table_setup_column("Upgrade Type", PyImGui.TableColumnFlags.WidthStretch)
                    PyImGui.table_headers_row()
                    
                    if item and item.is_valid:
                        prefix, suffix, inscription = ItemMod.get_item_upgrades(item.id)
                        
                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        PyImGui.text("Prefix")
                        PyImGui.table_set_column_index(1)
                        PyImGui.text(prefix.name if prefix else "None")
                        if prefix and prefix.is_inherent:
                            PyImGui.same_line(0, 5)
                            PyImGui.text_colored(" (Inherent)", RED.color_tuple)
                        
                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        PyImGui.text("Inscription")
                        PyImGui.table_set_column_index(1)
                        PyImGui.text(inscription.name if inscription else "None")
                        if inscription and inscription.is_inherent:
                            PyImGui.same_line(0, 5)
                            PyImGui.text_colored(" (Inherent)", RED.color_tuple)
                        
                        
                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        PyImGui.text("Suffix")
                        PyImGui.table_set_column_index(1)
                        PyImGui.text(suffix.name if suffix else "None")
                        if suffix and suffix.is_inherent:
                            PyImGui.same_line(0, 5)
                            PyImGui.text_colored(" (Inherent)", RED.color_tuple)
                        
                    PyImGui.end_table()
                                    
                ImGui.text("Item Properties", 16)
                if PyImGui.begin_table("Item Properties", 2, PyImGui.TableFlags.Borders | PyImGui.TableFlags.Resizable):                    
                    PyImGui.table_setup_column("Property Type", PyImGui.TableColumnFlags.WidthFixed, 250)
                    PyImGui.table_setup_column("Description", PyImGui.TableColumnFlags.WidthStretch)
                    PyImGui.table_headers_row()
                    
                    if item and item.is_valid:
                        for prop in item.properties:                            
                            PyImGui.table_next_row()
                            PyImGui.table_set_column_index(0)
                            PyImGui.text(prop.__class__.__name__)
                            PyImGui.table_set_column_index(1)
                            PyImGui.text(prop.describe() if hasattr(prop, "describe") else "None")
                    
                    PyImGui.end_table()
                ImGui.end_tab_item()
                
            if ImGui.begin_tab_item("Items"):   
                if item and item.is_valid:
                    # PyImGui.begin_disabled(not item.is_usable)
                    if ImGui.button(f"Use {item_name}", -1):
                        tree = BehaviorTree(BTNodes.Items.UseItems([item.id]))
                        pass
                    # PyImGui.end_disabled()
                    
                    PyImGui.begin_disabled(not Map.IsExplorable())
                    if ImGui.button(f"Drop {item_name}", -1):
                        tree = BehaviorTree(BTNodes.Items.DropItems([item.id]))
                        pass
                    ImGui.show_tooltip("Will only drop a single item on the ground at your current location.")
                    PyImGui.end_disabled()
                    
                    PyImGui.separator()
                    
                    PyImGui.begin_disabled(item.is_identified or not item.is_inventory_item)
                    if ImGui.button(f"Identify {item_name}", -1):
                        tree = BehaviorTree(BTNodes.Items.IdentifyItems([item.id]))
                    PyImGui.end_disabled()
                    PyImGui.separator()
                    
                    PyImGui.begin_disabled(not item.is_salvageable or not item.is_inventory_item)
                    PyImGui.begin_disabled(not item.prefix)
                    if ImGui.button(f"Extract {item.prefix.name if item.prefix else 'Prefix'} from {item_name}", -1):
                        tree = BehaviorTree(BTNodes.Items.SalvageItem(item.id, salvage_mode=SalvageMode.Prefix))
                    PyImGui.end_disabled()
                    
                    PyImGui.begin_disabled(not item.suffix)
                    if ImGui.button(f"Extract {item.suffix.name if item.suffix else 'Suffix'} from {item_name}", -1):
                        tree = BehaviorTree(BTNodes.Items.SalvageItem(item.id, salvage_mode=SalvageMode.Suffix))
                    PyImGui.end_disabled()
                    
                    PyImGui.begin_disabled(not item.inscription)
                    if ImGui.button(f"Extract {item.inscription.name if item.inscription else 'Inscription'} from {item_name}", -1):
                        tree = BehaviorTree(BTNodes.Items.SalvageItem(item.id, salvage_mode=SalvageMode.Inscription))
                    PyImGui.end_disabled()
                    
                    if ImGui.button(f"Salvage {item_name} for common materials", -1):
                        tree = BehaviorTree(BTNodes.Items.SalvageItem(item.id, salvage_mode=SalvageMode.LesserCraftingMaterials))
                    
                    if ImGui.button(f"Salvage {item_name} for rare materials", -1):
                        tree = BehaviorTree(BTNodes.Items.SalvageItem(item.id, salvage_mode=SalvageMode.RareCraftingMaterials))
                    PyImGui.end_disabled()
                    PyImGui.separator()
                    
                    PyImGui.begin_disabled(not item.is_inventory_item)
                    if ImGui.button(f"Destroy {item_name}", -1):
                        tree = BehaviorTree(BTNodes.Items.DestroyItems([item.id]))
                    PyImGui.end_disabled()
                    
                    PyImGui.separator()
                    PyImGui.begin_disabled(not item.is_inventory_item)
                    if ImGui.button(f"Deposit {item_name} into Storage", -1):
                        tree = BehaviorTree(BTNodes.Items.DepositItems([item.id]))
                    PyImGui.end_disabled()
                    
                    PyImGui.begin_disabled(not item.is_storage_item)
                    if ImGui.button(f"Withdraw {item_name} from Storage", -1):
                        tree = BehaviorTree(BTNodes.Items.WithdrawItems([item.id]))
                    PyImGui.end_disabled()
                                 
                ImGui.end_tab_item()
            
            if ImGui.begin_tab_item("Merchant"):
                if item and item.is_valid:
                    PyImGui.begin_disabled(not item or not item.is_valid or not item.is_inventory_item)
                    if ImGui.button(f"Sell {item_name}", -1):
                        tree = BehaviorTree(BTNodes.Merchant.SellItems([item.id]))
                    PyImGui.end_disabled()
                    
                    PyImGui.begin_disabled(not item or not item.is_valid or item.is_inventory_item)
                    if ImGui.button(f"Buy {item_name}", -1):
                        tree = BehaviorTree(BTNodes.Merchant.BuyItems([(item.id, 1)]))
                    PyImGui.end_disabled()
                    
                ImGui.end_tab_item()
                
            if ImGui.begin_tab_item("Trader"):
                if item and item.is_valid:
                    PyImGui.begin_disabled(not item or not item.is_valid or not item.is_inventory_item)
                    if ImGui.button(f"Sell {item_name}", -1):
                        tree = BehaviorTree(BTNodes.Trader.SellItem(item.id))
                    PyImGui.end_disabled()
                    
                    PyImGui.begin_disabled(not item or not item.is_valid or item.is_inventory_item)
                    if ImGui.button(f"Buy {item_name}", -1):
                        tree = BehaviorTree(BTNodes.Trader.BuyItem(item.id, 1))
                    PyImGui.end_disabled()
                ImGui.end_tab_item()
                                
            if ImGui.begin_tab_item("Bags"):                
                if ImGui.button("Compact Inventory", -1):
                    tree = BehaviorTree(BTNodes.Bags.CompactBags())
                
                if ImGui.button("Sort Inventory", -1):
                    tree = BehaviorTree(BTNodes.Bags.SortBags())
                
                PyImGui.new_line()
                PyImGui.separator()
                
                PyImGui.begin_disabled(Inventory.IsStorageOpen())
                if ImGui.button("Open Xunlai", -1):
                    Inventory.OpenXunlaiWindow()
                PyImGui.end_disabled()
                
                if ImGui.button("Compact Storage", -1):
                    tree = BehaviorTree(BTNodes.Bags.CompactBags(bags=STORAGE_BAGS))
                
                if ImGui.button("Sort Storage", -1):
                    tree = BehaviorTree(BTNodes.Bags.SortBags(bags=STORAGE_BAGS))
                
                ImGui.end_tab_item()
                
            if ImGui.begin_tab_item("Crafting"):
                style.Text.push_color_direct(RED.rgb_tuple)
                ImGui.text_wrapped("No out of the box tests available. Since we don't have a nice way to setup a test for everyone.")
                ImGui.text_wrapped("Check source code to setup your crafting tests.")
                style.Text.pop_color_direct()
                
                crafting_disabled = True
                price = 0
                material_item_ids = []
                material_amounts = []
                
                if item and item.is_valid:
                    PyImGui.begin_disabled(crafting_disabled or item.is_inventory_item)
                    if ImGui.button(f"Craft {item_name}", -1):
                        tree = BehaviorTree(BTNodes.Crafting.CraftItem(item.id, cost=price, material_item_ids=material_item_ids, material_quantities=material_amounts))
                    PyImGui.end_disabled()
                
                ImGui.end_tab_item()
            
            ImGui.end_tab_bar()
            
    ImGui.End(INI_KEY)