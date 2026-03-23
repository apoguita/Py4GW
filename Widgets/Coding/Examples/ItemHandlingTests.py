import os
from typing import NamedTuple

import Py4GW
import PyImGui
from PyItem import PyItem

from Py4GWCoreLib.ImGui_src.ImGuisrc import ImGui
from Py4GWCoreLib.ImGui_src.types import Alignment
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Inventory import Inventory
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.Routines import Routines
from Py4GWCoreLib.enums_src.Item_enums import ItemType, Rarity
from Py4GWCoreLib.enums_src.Region_enums import ServerLanguage
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Py4GWCoreLib.native_src.internals import string_table
from Sources.frenkeyLib.ItemHandling.ConfigExamples.ExampleGUIs.LootConfigView import draw_loot_config_view

Utils.ClearSubModules("ItemHandling")
Utils.ClearSubModules("frenkeyLib.Core")
from Sources.frenkeyLib.Core.encoded_names import ItemName
from Sources.frenkeyLib.ItemHandling.Items.ItemCache import ITEM_CACHE
from Sources.frenkeyLib.ItemHandling.Mods.ItemMod import ItemMod
from Sources.frenkeyLib.ItemHandling.BTNodes import STORAGE_BAGS, BTNodes
from Sources.frenkeyLib.ItemHandling.Rules.types import SalvageMode
from Sources.frenkeyLib.ItemHandling.Items.item_collecting import ItemCollector


MODULE_NAME = "Item Handling Tests"
MODULE_ICON = "Textures/Module_Icons/Coding.png"
SALVAGE_MODES = [m.name for m in SalvageMode]

INI_KEY = ""
INI_PATH = f"Widgets/{MODULE_NAME}"
INI_FILENAME = f"{MODULE_NAME}.ini"

hovered_item_id = 0
tree : BehaviorTree | None = None
auto_tick = True
enc_input : str = ""
decoded_ouput : str = ""
decoded_name = ""

RED = Color(255, 0, 0, 255)
GREEN = Color(0, 255, 0, 255)

lang_names = [lang.name for lang in ServerLanguage]
languages = [lang for lang in ServerLanguage]
language : ServerLanguage = ServerLanguage.English
int_lang = language.value
language_index = languages.index(language)

ITEM_COLLECTOR = ItemCollector()
class encoded_strings(NamedTuple):
    item_id: int
    name_enc: list[int]
    info_string: list[int]
    singular_name: list[int]
    complete_name_enc: list[int]
    
class decoded_strings(NamedTuple):
    item_id: int
    name_enc: str
    info_string: str
    singular_name: str
    complete_name_enc: str
    

decoded : decoded_strings | None = None
encoded : encoded_strings | None = None
fully_decoded = False
collect = True

show_loot_config_view = False

# method to convert list of int to hex string
def int_list_to_hex_string(int_list: list[int]) -> str:
    try:
        return ", ".join(f"0x{v:X}" for v in int_list)
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error converting int list to hex string: {e}")
        return ""
    
def bytes_to_hex_string(byte: bytes) -> str:
    try:
        return " ".join(f"0x{v:X}" for v in byte)
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error converting int list to hex string: {e}")
        return ""

def main():
    global INI_KEY, hovered_item_id, auto_tick, tree, language, enc_input, decoded_ouput, decoded_name, int_lang, language_index, decoded, encoded, fully_decoded, collect, show_loot_config_view
    ITEM_CACHE.reset()
    
    if not Routines.Checks.Map.IsMapReady():
        encoded = None
        decoded = None
        hovered_item_id = None
        fully_decoded = True
        return
    
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
        item = ITEM_CACHE.get_item_snapshot(hovered_item_id) if hovered_item_id else None
        
        if not item or not item.is_valid:
            hovered_item_id = 0
                    
        item_name = item.data.english_name if item and item.data else f"Unknown {(f"{item.item_type.name}-Item" if item else 'Item')}"
        
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
            
            add_row("Item Data", item.data.english_name if item and item.data else "N/A")
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
                        PyImGui.text(str(prefix.display_summary) if prefix else "None")
                        if prefix and prefix.is_inherent:
                            PyImGui.same_line(0, 5)
                            PyImGui.text_colored(" (Inherent)", RED.color_tuple)
                        
                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        PyImGui.text("Inscription")
                        PyImGui.table_set_column_index(1)
                        PyImGui.text(str(inscription.display_summary) if inscription else "None")
                        if inscription and inscription.is_inherent:
                            PyImGui.same_line(0, 5)
                            PyImGui.text_colored(" (Inherent)", RED.color_tuple)

                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)
                        PyImGui.text("Suffix")
                        PyImGui.table_set_column_index(1)
                        PyImGui.text(str(suffix.display_summary) if suffix else "None")
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
                            PyImGui.text(str(prop.plain_description) if hasattr(prop, "plain_description") else "None")
                    
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
            
            if ImGui.begin_tab_item("Item Decoding"):
                global enc_input, decoded_name
                enc_bytes : bytes = b""
                switching_lang = False
                                
                collect = ImGui.checkbox("Collect Item Data", collect)
                                
                language_changed = ImGui.combo("Language", language_index, lang_names)
                if language_changed != language_index:
                    language_index = language_changed
                    language = languages[language_changed]
                    int_lang = language.value
                    switching_lang = True
                    
                int_lang_changed = ImGui.input_int("Language (Int)", int_lang)
                if int_lang_changed != int_lang:
                    try:
                        int_lang = int_lang_changed
                        
                        switching_lang = True
                        Py4GW.Console.Log(MODULE_NAME, f"Switching to language: {ServerLanguage(int_lang_changed).name if int_lang_changed in ServerLanguage._value2member_map_ else int_lang_changed}")
                        
                        try:
                            language = ServerLanguage(int_lang_changed)
                            language_index = languages.index(language)
                        except ValueError:
                            language = ServerLanguage.Unknown      
                                                
                    except ValueError:
                        Py4GW.Console.Log(MODULE_NAME, f"Invalid language value: {int_lang}", Py4GW.Console.MessageType.Error)
                                    
                PyImGui.separator()
                                    
                ImGui.begin_table("Decoded Data", 4, PyImGui.TableFlags.Borders | PyImGui.TableFlags.Resizable)
                PyImGui.table_setup_column("Part", PyImGui.TableColumnFlags.WidthFixed, 80)
                PyImGui.table_setup_column("Encoded", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Decoded", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("Copy", PyImGui.TableColumnFlags.WidthFixed, 50)
                PyImGui.table_headers_row()
                
                PyImGui.table_next_column()
                        
                description_item_types = [
                    ItemType.Axe,
                    ItemType.Bow,
                    ItemType.Daggers,
                    ItemType.Hammer,
                    ItemType.Offhand,
                    ItemType.Scythe,
                    ItemType.Shield,
                    ItemType.Spear,
                    ItemType.Staff,
                    ItemType.Sword,
                    ItemType.Wand, 
                    
                    ItemType.Headpiece,
                    ItemType.Chestpiece,
                    ItemType.Gloves,
                    ItemType.Leggings,
                    ItemType.Boots,
                    
                    ItemType.Rune_Mod]
                
                error_message = ""
                if item and (not encoded or encoded.item_id != item.id):
                    encoded = encoded_strings(
                        item_id=item.id,
                        name_enc = PyItem.GetNameEnc(item.id) or [],
                        info_string = PyItem.GetInfoString(item.id) or [] if item.item_type in description_item_types else [],
                        singular_name = PyItem.GetSingleItemName(item.id) or [],
                        complete_name_enc = PyItem.GetCompleteNameEnc(item.id) or []
                    )
                    
                    fully_decoded = False
                
                ImGui.text("Manual")
                PyImGui.table_next_column()
                
                PyImGui.push_item_width(-1)   
                enc_input = ImGui.input_text("##Encoded Input", enc_input)
                if enc_input:
                    try:
                        enc_bytes = bytes(int(x, 16) for x in enc_input.replace(",", " ").split())
                        decoded_ouput = string_table.decode(enc_bytes)
                    except Exception as e:
                        decoded_ouput = ""
                        error_message = f"Error decoding input: {e}"
                
                PyImGui.table_next_column()     
                PyImGui.push_item_width(-1)              
                ImGui.input_text("##Decoded Output", decoded_ouput if decoded_ouput else "", PyImGui.InputTextFlags.ReadOnly)
                PyImGui.table_next_column()  
                    
                for prop in ["name_enc", "singular_name", "complete_name_enc", "info_string"]:
                    PyImGui.table_next_column()
                    
                    ImGui.text(prop)
                    PyImGui.table_next_column()
                    
                    PyImGui.push_item_width(-1)           
                    ImGui.input_text(f"##{prop}", int_list_to_hex_string(getattr(encoded, prop)) if encoded and getattr(encoded, prop) else "", PyImGui.InputTextFlags.ReadOnly)
                    PyImGui.table_next_column()
                    
                    ImGui.text_wrapped(getattr(decoded, prop) if decoded and getattr(decoded, prop) else "")
                    PyImGui.table_next_column()
                    
                    if ImGui.button(f"Copy Decoded##{prop}", -1):
                        try:
                            copy_text = getattr(decoded, prop) if decoded and getattr(decoded, prop) else ""
                            PyImGui.set_clipboard_text(copy_text)
                            Py4GW.Console.Log(MODULE_NAME, f"Copied {prop} to clipboard: {copy_text}")
                        except Exception as e:
                            Py4GW.Console.Log(MODULE_NAME, f"Failed to copy {prop} to clipboard: {e}", Py4GW.Console.MessageType.Error)
                            
                    if ImGui.button(f"Copy Encoded##{prop}", -1):
                        try:
                            copy_text = int_list_to_hex_string(getattr(encoded, prop)) if encoded and getattr(encoded, prop) else ""
                            PyImGui.set_clipboard_text(copy_text)
                            Py4GW.Console.Log(MODULE_NAME, f"Copied {prop} to clipboard: {copy_text}")
                        except Exception as e:
                            Py4GW.Console.Log(MODULE_NAME, f"Failed to copy {prop} to clipboard: {e}", Py4GW.Console.MessageType.Error)
                    
                PyImGui.pop_item_width()
                PyImGui.pop_item_width()
                PyImGui.end_table()
                
                
                if error_message:
                    ImGui.text_colored(error_message, RED.color_tuple, font_size = 16)
                
                if switching_lang:
                    string_table.switch_language(language)
                    Py4GW.Console.Log(MODULE_NAME, f"Switching UI decode language override to: {language.name}")
                
                if ImGui.button("Decode from Clipboard", -1):
                    try:
                        clipboard = PyImGui.get_clipboard_text()
                        enc_input = clipboard
                        clipboard_bytes = bytes(int(x, 16) for x in clipboard.replace(",", " ").split())
                        enc_bytes = clipboard_bytes
                        decoded_name = string_table.decode(enc_bytes)
                        
                        Py4GW.Console.Log(MODULE_NAME, f"Decoded:")
                        Py4GW.Console.Log(MODULE_NAME, f"{decoded_name}")
                                                
                        # Write decoded name to file for easy copying
                        with open(os.path.join(INI_PATH, "Decoded_Item_Name.txt"), "w", encoding="utf-8") as f:
                            f.write(decoded_name) 
                        
                    except Exception as e:
                        Py4GW.Console.Log(MODULE_NAME, f"Failed to decode clipboard data: {e}", Py4GW.Console.MessageType.Error
                                        )
                ImGui.end_tab_item()
            
            if ImGui.begin_tab_item("Rule Testing"):
                ImGui.text_wrapped("Here we present the rule system like it would be used in the loot config or other item handling related systems. This is just a demonstration of how the rules can be created, edited and tested in a simple way.")
                
                show_loot_config_view = ImGui.toggle_button("Show Loot Config View", show_loot_config_view, -1)
                ImGui.end_tab_item()
                
            ImGui.end_tab_bar()
            
    ImGui.End(INI_KEY)
    
    if not fully_decoded and encoded:
        try:
            decoded = decoded_strings(
                item_id=encoded.item_id,
                name_enc=string_table.decode(bytes(encoded.name_enc)) if encoded.name_enc else "",
                info_string=string_table.decode(bytes(encoded.info_string)) if encoded.info_string else "",
                singular_name=string_table.decode(bytes(encoded.singular_name)) if encoded.singular_name else "",
            complete_name_enc=string_table.decode(bytes(encoded.complete_name_enc)) if encoded.complete_name_enc else ""
        )
        
            fully_decoded = (not encoded.name_enc or decoded.name_enc != "") and (not encoded.info_string or decoded.info_string != "") and (not encoded.singular_name or decoded.singular_name != "") and (not encoded.complete_name_enc or decoded.complete_name_enc != "")
        except Exception as e:
            Py4GW.Console.Log(MODULE_NAME, f"Error decoding item strings: {e}", Py4GW.Console.MessageType.Error)

    if show_loot_config_view:
        draw_loot_config_view()
        
    if collect:
        ITEM_COLLECTOR.run()