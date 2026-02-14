import re
import shutil
from typing import Callable
import webbrowser
from datetime import datetime

from Py4GWCoreLib.GlobalCache.ItemCache import Bag_enum
from Py4GWCoreLib.ImGui_src.types import Alignment, ControlAppearance, TextDecorator
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler
from Sources.frenkeyLib.Core.iterable import chunked
from Sources.frenkeyLib.Core.utility import ImGuiIniReader, string_similarity
from Sources.frenkeyLib.Core.gui import GUI
from Sources.frenkeyLib.Core import ex_style, texture_map
from Sources.frenkeyLib.LootEx import skin_rule, loot_handling, settings, price_check, utility, cache, ui_manager_extensions, inventory_handling, models, messaging
from Sources.frenkeyLib.LootEx.crafting import CraftingAction
from Sources.frenkeyLib.LootEx.data import Data
from Sources.frenkeyLib.LootEx.data_collection import DataCollector
from Sources.frenkeyLib.LootEx.enum import CHARACTER_INVENTORY, ITEM_CONVERSIONS, XUNLAI_STORAGE, ActionModsType, ItemAction, ItemCategory, ItemSubCategory, MaterialType, MerchantType, ModType, SalvageOption
from Sources.frenkeyLib.LootEx.item_configuration import ConfigurationCondition
from Sources.frenkeyLib.LootEx.filter import Filter
from Sources.frenkeyLib.LootEx.profile import Profile
from Sources.frenkeyLib.LootEx.texture_scraping_models import ScrapedItem
from Sources.frenkeyLib.LootEx.trading import ActionType, TraderAction, add_ingredients_to_buy
from Sources.frenkeyLib.LootEx.ui_manager_extensions import UIManagerExtensions
from Py4GWCoreLib import *

class SelectableItem:
    """
    Represents an item that can be selected and hovered over in a GUI.
    Attributes:
        item_info (self.data.Item): The information about the item.
        is_selected (bool): Indicates whether the item is currently selected. Defaults to False.
        is_hovered (bool): Indicates whether the item is currently being hovered over. Defaults to False.
    Methods:
        __str__(): Returns a string representation of the SelectableItem instance.
        __repr__(): Returns a string representation of the SelectableItem instance (same as __str__).
    """

    def __init__(self, item: models.Item, is_selected: bool = False):
        self.item_info: models.Item = item
        self.is_selected: bool = is_selected
        self.is_hovered: bool = False
        self.is_clicked: bool = False
        self.time_stamp : datetime = datetime.min

    def __str__(self):
        return f"SelectableItem(item={self.item_info}, is_selected={self.is_selected})"

    def __repr__(self):
        return self.__str__()

class SelectableWrapper:
    """
    Represents a selectable wrapper for an object, allowing it to be selected and hovered over in a GUI.
    Attributes:
        object (object): The object to be wrapped.
        is_selected (bool): Indicates whether the object is currently selected. Defaults to False.
        is_hovered (bool): Indicates whether the object is currently being hovered over. Defaults to False.
    """

    def __init__(self, object, is_selected: bool = False):
        self.object = object
        self.is_selected: bool = is_selected
        self.is_hovered: bool = False

class ItemFilter:
    def __init__(self, name: str, lambda_function: Callable[[models.Item], bool]):
        self.name: str = name
        self.lambda_function: Callable[[models.Item], bool] = lambda_function
        pass
    
    def match(self, item: models.Item) -> bool:
        """
        Checks if the item matches the filter criteria.
        
        Args:
            item (models.Item): The item to check against the filter.
        
        Returns:
            bool: True if the item matches the filter, False otherwise.
        """
        
        return self.lambda_function(item)
    
class RuleFilter:
    def __init__(self, name: str, lambda_function: Callable[[skin_rule.SkinRule], bool]):
        self.name: str = name
        self.lambda_function: Callable[[skin_rule.SkinRule], bool] = lambda_function
        pass
    
    def match(self, rule: skin_rule.SkinRule) -> bool:
        """
        Checks if the rule matches the filter criteria.
        
        Args:
            rule (skin_rule.SkinRule): The rule to check against the filter.
        
        Returns:
            bool: True if the rule matches the filter, False otherwise.
        """
        
        return self.lambda_function(rule)

class MouseTest:
    def __init__(self, frame_id: int, current_state: int, wparam_value: int, lparam: int):
        self.frame_id: int = frame_id
        self.current_state: int = current_state
        self.wparam_value: int = wparam_value
        self.lparam: int = lparam

class UI:
    _instance = None
    _initialized = False
    
    class ActionInfo:
        def __init__(self, name: str, description: str, icon: str):
            self.name: str = name
            self.description: str = description
            self.icon: str = icon
    
    class ActionInfos(dict[ItemAction, "UI.ActionInfo"]):
        def __init__(self, dict : dict[ItemAction, "UI.ActionInfo"] = {}):
            super().__init__()

            for action, info in dict.items():
                self[action] = info                
        
        def __getitem__(self, key: ItemAction) -> "UI.ActionInfo":
            return super().__getitem__(key)
        
        def get_texture(self, action: ItemAction, default = None):
            """
            Returns the texture path for the given action.
            
            Args:
                action (ItemAction): The action for which to get the texture.
            
            Returns:
                str: The texture path for the action.
            """
            if action not in self:
                return default
            
            return self[action].icon
        
        def get_name(self, action: ItemAction, default = None):
            """
            Returns the name for the given action.
            
            Args:
                action (ItemAction): The action for which to get the name.
            
            Returns:
                str: The name for the action.
            """
            if action not in self:
                return default
            
            return self[action].name
        
        def get_description(self, action: ItemAction, default = None):
            """
            Returns the description for the given action.
            
            Args:
                action (ItemAction): The action for which to get the description.
            
            Returns:
                str: The description for the action.
            """
            if action not in self:
                return default
            
            return self[action].description

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # only initialize once
        if self._initialized:
            return
        
        self._initialized = True
        self.MouseTest = MouseTest(0, 8, 0, 0)
                           
        from Sources.frenkeyLib.LootEx.settings import Settings
        self.settings = Settings()
        
        from Sources.frenkeyLib.LootEx.data import Data
        self.data = Data()
        
        self.widget_handler = get_widget_handler()        
        self.imgui_ini_reader = ImGuiIniReader()
        window_pos, window_size, collapse = self.get_window_info()
        
        
        # self.cached_item = cache.Cached_Item(1401) 
        self.collection_module_window : ImGui.WindowModule = ImGui.WindowModule(
            "LootEx Data Collection",
            "LootEx Data Collection",
            window_size=(800, 500),
            window_flags=PyImGui.WindowFlags.NoFlag,
            can_close=True,
            collapse=collapse
        )
        self.module_window : ImGui.WindowModule = ImGui.WindowModule(
            "LootEx",
            "LootEx",
            window_size=window_size,
            window_pos=window_pos,
            window_flags=PyImGui.WindowFlags.NoFlag,
            can_close=True,
            collapse=collapse
        )
        self.style = ex_style.ExStyle()
        file_directory = os.path.dirname(os.path.abspath(__file__))
        self.textures_folder = os.path.join(Console.get_projects_path(), "Textures")
        self.icon_textures_path = os.path.join(file_directory, "textures")
        self.item_textures_path = os.path.join(self.textures_folder, "Items")
        
        self.collection_timer = ThrottledTimer()
        self.collection_items: dict[str, dict[int, cache.Cached_Item]] = {}
        
        self.actions_timer = ThrottledTimer()
        self.action_summary: inventory_handling.InventoryHandler.ActionsSummary | None = None
        
        self.filtered_scraped_items : dict[str, ScrapedItem]= {}
        self.data_collection_item : models.Item | None = None
        self.scraped_item : ScrapedItem | None = None
        
        self.action_infos : UI.ActionInfos = UI.ActionInfos({
            ItemAction.Loot: UI.ActionInfo("Loot (Pick Up)", "If the item is dropped, pick it up.", texture_map.CoreTextures.UI_Reward_Bag_Hovered.value),
            ItemAction.Collect_Data: UI.ActionInfo("Collect Data", "Collect data about the item.", os.path.join(self.icon_textures_path, "wiki_logo.png")),
            ItemAction.Identify: UI.ActionInfo("Identify", "Use an Identification Kit to identify the item.", self.data.Items.get_texture_by_name("Identification Kit.png")),
            ItemAction.Hold: UI.ActionInfo("Hold", "Hold on to the item without stashing.", texture_map.CoreTextures.UI_Backpack.value),
            ItemAction.Stash: UI.ActionInfo("Stash", "Stash the item in your Xunlai Chest.", os.path.join(self.icon_textures_path, "xunlai_chest.png")),
            ItemAction.Salvage_Mods: UI.ActionInfo("Salvage Mods", "Salvage the mods from the item.", self.data.Items[ItemType.Rune_Mod][17059].texture_file),
            ItemAction.Salvage: UI.ActionInfo("Salvage for Common or Rare Materials", "Use a Salvage Kit to salvage the item.", os.path.join(self.icon_textures_path, "expert_or_common_salvage_kit.png")),
            ItemAction.Salvage_Common_Materials: UI.ActionInfo("Salvage Common Materials", "Use a Salvage Kit to salvage common materials from the item.", self.data.Items.get_texture_by_name("Salvage Kit.png")),
            ItemAction.Salvage_Rare_Materials: UI.ActionInfo("Salvage Rare Materials", "Use an Expert Salvage Kit to salvage rare materials from the item.", self.data.Items.get_texture_by_name("Expert Salvage Kit.png")),
            ItemAction.Sell_To_Merchant: UI.ActionInfo("Sell to Merchant", "Sell the item to a merchant for gold.", texture_map.CoreTextures.UI_Gold.value),
            ItemAction.Sell_To_Trader: UI.ActionInfo("Sell to Trader (Runes, Scrolls, Dyes...)", "Sell the item to a trader for gold.", texture_map.CoreTextures.UI_Gold.value),
            ItemAction.Destroy: UI.ActionInfo("Destroy", "Destroy the item permanently.", texture_map.CoreTextures.UI_Destroy.value),
            ItemAction.Deposit_Material: UI.ActionInfo("Deposit Material", "Deposit the item as a material in your Xunlai Chest.", os.path.join(self.icon_textures_path, "xunlai_chest.png")),
            ItemAction.NONE: UI.ActionInfo("No Action", "No action will be performed on the item.", ""),
        })        
        self.keep_actions = [
            ItemAction.Hold,
            ItemAction.Stash
        ]
        self.keep_action_names = [self.action_infos[action].name for action in self.keep_actions]
        self.py_io = PyImGui.get_io()
        self.selected_loot_items: list[SelectableItem] = []
        
        
        self.rule_search: str = ""
        self.selected_rule_changed: bool = True
        self.mod_range_popup: bool = False
        self.selected_rule: skin_rule.SkinRule | None = None
        self.selected_rule_mod: models.WeaponMod | None = None
        self.selected_mod_info: models.ModInfo | None = None
        self.selectable_rules: list[SelectableWrapper] = []
        self.selectable_items : list[models.Item] = []
        
        self.dmg_range_popup: bool = False
        self.selected_rule_damage_range: models.IntRange | None = None
        self.selected_damage_range: models.IntRange | None = None
        self.selected_damage_range_min: models.IntRange | None = None
        
        self.inventory_view: bool = True
        self.item_search: str = ""
        self.filtered_loot_items: list[SelectableItem] = []        
        self.filtered_skins: list[SelectableItem] = []        
        self.filtered_blacklist_items: list[SelectableItem] = []       
        
        self.selected_condition: Optional[ConfigurationCondition] = None
        self.filter_name: str = ""
        self.condition_name: str = ""
        self.new_profile_name: str = ""
        self.mod_search: str = ""
        
        self.filtered_weapon_mods: list[SelectableWrapper] = []
        
        self.scroll_bar_visible: bool = False
        self.trader_type: str = ""
        
        self.entered_price_threshold: int = 1000
        self.mark_to_sell_runes: bool = False
        
        self.show_price_check_popup: bool = False
        self.show_add_filter_popup: bool = False
        self.show_add_profile_popup: bool = False
        self.show_delete_profile_popup: bool = False
        self.first_draw: bool = True
        self.gui_open: bool = True
        
        self.window_flags: int = PyImGui.WindowFlags.NoFlag
        self.weapon_types = [
            ItemType.Axe,
            ItemType.Sword,
            ItemType.Spear,
            ItemType.Wand,
            ItemType.Daggers,
            ItemType.Hammer,
            ItemType.Scythe,
            ItemType.Bow,
            ItemType.Staff,
            ItemType.Offhand,
            ItemType.Shield,
        ]

        self.prefix_names = ["Any"]
        self.suffix_names = ["Any"]
        self.inherent_names = ["Any"]
        self.inventory_coords: Optional[settings.FrameCoords] = None
        
        self.mod_textures : dict[ItemType, dict[ModType, str]] = {
            ItemType.Axe: {
                ModType.Prefix: self.data.Items.get_texture_by_name("Axe Haft"),
                ModType.Suffix: self.data.Items.get_texture_by_name("Axe Grip"),
            },
            ItemType.Bow: {
                ModType.Prefix: self.data.Items.get_texture_by_name("Bow String"),
                ModType.Suffix: self.data.Items.get_texture_by_name("Bow Grip"),
            },
            ItemType.Offhand: {
                ModType.Suffix: self.data.Items.get_texture_by_name("Focus Core"),
            },
            ItemType.Hammer: {
                ModType.Prefix: self.data.Items.get_texture_by_name("Hammer Haft"),
                ModType.Suffix: self.data.Items.get_texture_by_name("Hammer Grip"),
            },
            ItemType.Wand: {
                ModType.Suffix: self.data.Items.get_texture_by_name("Wand Wrapping"),
            },
            ItemType.Shield: {
                ModType.Suffix: self.data.Items.get_texture_by_name("Shield Handle"),                        
            },
            ItemType.Staff: {
                ModType.Prefix: self.data.Items.get_texture_by_name("Staff Head"),
                ModType.Suffix: self.data.Items.get_texture_by_name("Staff Wrapping"),
            },
            ItemType.Sword: {
                ModType.Prefix: self.data.Items.get_texture_by_name("Sword Hilt"),
                ModType.Suffix: self.data.Items.get_texture_by_name("Sword Pommel"),
            },
            ItemType.Daggers: {
                ModType.Prefix: self.data.Items.get_texture_by_name("Dagger Tang"),
                ModType.Suffix: self.data.Items.get_texture_by_name("Dagger Handle"),
            },
            ItemType.Spear: {
                ModType.Prefix: self.data.Items.get_texture_by_name("Spearhead"),
                ModType.Suffix: self.data.Items.get_texture_by_name("Spear Grip"),
            },
            ItemType.Scythe: {
                ModType.Prefix: self.data.Items.get_texture_by_name("Scythe Snathe"),
                ModType.Suffix: self.data.Items.get_texture_by_name("Scythe Grip"),
            },                            
        }
        
        self.rarity_item_types : list[ItemType] = [
            ItemType.Axe,
            ItemType.Bow,
            ItemType.Daggers,
            ItemType.Hammer,
            ItemType.Scythe,
            ItemType.Spear,
            ItemType.Sword,
            ItemType.Staff,
            ItemType.Wand,
            ItemType.Offhand,
            ItemType.Shield, 
            ItemType.Salvage,                       
        ]
        
        self.item_type_textures: dict[ItemType, str] = {
            ItemType.Salvage: self.data.Items.get_texture_by_name("Axe Fiend Armor"),
            ItemType.Axe: self.data.Items.get_texture_by_name("Spiked Axe"),
            ItemType.Bag: self.data.Items.get_texture_by_name("Bag"),
            ItemType.Boots: os.path.join(self.icon_textures_path, "templar_armor_feet.png"),
            ItemType.Bow: self.data.Items.get_texture_by_name("Ivory Bow"),
            ItemType.Bundle: self.data.Items.get_texture_by_name("War Supplies"),
            ItemType.Chestpiece: os.path.join(self.icon_textures_path, "templar_armor_chestpiece.png"),
            ItemType.Rune_Mod: self.data.Items.get_texture_by_name("Rune (Superior)"),
            ItemType.Usable: self.data.Items.get_texture_by_name("Birthday Cupcake"),
            ItemType.Dye: os.path.join(self.textures_folder, "Dyes", "White.png"),
            ItemType.Materials_Zcoins: self.data.Items.get_texture_by_name("Wood Plank"),
            ItemType.Offhand: self.data.Items.get_texture_by_name("Channeling Focus"),
            ItemType.Gloves: os.path.join(self.icon_textures_path, "templar_armor_gloves.png"),
            ItemType.Hammer: self.data.Items.get_texture_by_name("Foehammer"),
            ItemType.Headpiece: os.path.join(self.icon_textures_path, "templar_armor_helmet.png"),
            ItemType.CC_Shards: self.data.Items.get_texture_by_name("Candy Cane Shard"),
            ItemType.Key: self.data.Items.get_texture_by_name("Zaishen Key"),
            ItemType.Leggings: os.path.join(self.icon_textures_path, "templar_armor_leggins.png"),
            ItemType.Gold_Coin: texture_map.CoreTextures.UI_Gold.value,
            ItemType.Quest_Item: self.data.Items.get_texture_by_name("Top Right Map Piece"),
            ItemType.Wand: self.data.Items.get_texture_by_name("Shaunur's Scepter"),
            ItemType.Shield: self.data.Items.get_texture_by_name("Round Shield"),
            ItemType.Staff : self.data.Items.get_texture_by_name("Bone Staff"),
            ItemType.Sword: self.data.Items.get_texture_by_name("Long Sword"),
            ItemType.Kit: self.data.Items.get_texture_by_name("Superior Salvage Kit"),
            ItemType.Trophy: self.data.Items.get_texture_by_name("Destroyer Core"),
            ItemType.Scroll: self.data.Items.get_texture_by_name("Scroll of the Lightbringer"),
            ItemType.Daggers: self.data.Items.get_texture_by_name("Kukris"),
            ItemType.Present: self.data.Items.get_texture_by_name("Birthday Present"),
            ItemType.Minipet: self.data.Items.get_texture_by_name("Miniature Mox"),
            ItemType.Scythe: self.data.Items.get_texture_by_name("Suntouched Scythe")  ,
            ItemType.Spear: self.data.Items.get_texture_by_name("Serrated Spear"),
            ItemType.Storybook: self.data.Items.get_texture_by_name("Young Heroes of Tyria [Hard Mode]"),
            ItemType.Costume: self.data.Items.get_texture_by_name("Shining Blade Uniform"),
            ItemType.Costume_Headpiece: self.data.Items.get_texture_by_name("Divine Halo"),
            ItemType.Unknown: "",
        }
                    
        self.dye_textures: dict[int, str] = {
            DyeColor.NoColor: os.path.join(self.textures_folder, "Dyes", "Gray.png"),
            DyeColor.Blue: os.path.join(self.textures_folder, "Dyes", "Blue.png"),
            DyeColor.Green: os.path.join(self.textures_folder, "Dyes", "Green.png"),
            DyeColor.Purple: os.path.join(self.textures_folder, "Dyes", "Purple.png"),
            DyeColor.Red: os.path.join(self.textures_folder, "Dyes", "Red.png"),
            DyeColor.Yellow: os.path.join(self.textures_folder, "Dyes", "Yellow.png"),
            DyeColor.Brown: os.path.join(self.textures_folder, "Dyes", "Brown.png"),
            DyeColor.Orange: os.path.join(self.textures_folder, "Dyes", "Orange.png"),
            DyeColor.Silver: os.path.join(self.textures_folder, "Dyes", "Silver.png"),
            DyeColor.Black: os.path.join(self.textures_folder, "Dyes", "Black.png"),
            DyeColor.Gray: os.path.join(self.textures_folder, "Dyes", "Gray.png"),
            DyeColor.White: os.path.join(self.textures_folder, "Dyes", "White.png"),
            DyeColor.Pink: os.path.join(self.textures_folder, "Dyes", "Pink.png"),
        }
        
        self.inscription_type_textures: dict[ItemType, str] = {
            ItemType.Weapon: self.data.Items[ItemType.Rune_Mod][15542].texture_file,
            ItemType.MartialWeapon: self.data.Items[ItemType.Rune_Mod][15540].texture_file,
            ItemType.Offhand: self.data.Items[ItemType.Rune_Mod][19123].texture_file,
            ItemType.OffhandOrShield: self.data.Items[ItemType.Rune_Mod][15541].texture_file,
            ItemType.EquippableItem: self.data.Items[ItemType.Rune_Mod][17059].texture_file,
            ItemType.SpellcastingWeapon: self.data.Items[ItemType.Rune_Mod][19122].texture_file,
        }
                
        self.merchant_item_textures: dict[str, str] = {
            "Superior Identification Kit": self.data.Items.get_texture_by_name("Superior Identification Kit"),
            "Salvage Kit": self.data.Items.get_texture_by_name("Salvage Kit"),
            "Expert Salvage Kit": self.data.Items.get_texture_by_name("Expert Salvage Kit"),
            "Lockpick": self.data.Items.get_texture_by_name("Lockpick"),
        }
        
        self.nick_textures: dict[str, str] = {
            "Gift of the Traveler": self.data.Items.get_texture_by_name("Gift of the Traveler"),
            "Red Iris Flower": self.data.Items.get_texture_by_name("Red Iris Flower"),
        }
            
        
        self.bag_ranges : dict[str, tuple[Bag, Bag]] = {
            "Inventory": (Bag.Backpack, Bag.Bag_2),   
            "Equipped Items": (Bag.Equipped_Items, Bag.Equipped_Items),       
            "Equipment Pack": (Bag.Equipment_Pack, Bag.Equipment_Pack),       
        }
        for bag in Bag:
            if bag.value <= Bag.Bag_2.value:
                continue
            
            if bag == Bag.Max:
                continue
            
            key = utility.Util.reformat_string(bag.name)
            if key in self.bag_ranges:
                continue
            
            self.bag_ranges[key] = (bag, bag)

        self.bag_ranges["Merchant/Trader"] = (Bag.NoBag, Bag.NoBag)
        
        self.bag_names = [key for key in self.bag_ranges.keys()]
        self.bag_index = 0
        
        for mod in self.data.Weapon_Mods.values():
            if mod.mod_type == ModType.Prefix:
                self.prefix_names.append(mod.name)

            elif mod.mod_type == ModType.Suffix:
                self.suffix_names.append(mod.name)

            elif mod.mod_type == ModType.Inherent:
                self.inherent_names.append(mod.name)

        sorted_item_types = [
            ItemType.Axe,
            ItemType.Bow,
            ItemType.Daggers,
            ItemType.Hammer,
            ItemType.Scythe,
            ItemType.Spear,
            ItemType.Sword,
            ItemType.Staff,
            ItemType.Wand,
            ItemType.Offhand,
            ItemType.Shield,
            
            ItemType.Headpiece,
            ItemType.Chestpiece,
            ItemType.Gloves,
            ItemType.Leggings,
            ItemType.Boots,
            
            ItemType.Scroll,
            ItemType.Usable,
            ItemType.Dye,
            ItemType.Key,
            ItemType.Gold_Coin,
            ItemType.Quest_Item,
            ItemType.Kit,
            ItemType.Rune_Mod,
            ItemType.CC_Shards,
            ItemType.Materials_Zcoins,
            ItemType.Salvage,
            ItemType.Present,
            ItemType.Minipet,
            ItemType.Trophy,
            
            ItemType.Weapon,
            ItemType.MartialWeapon,
            ItemType.OffhandOrShield,
            ItemType.EquippableItem,
            ItemType.SpellcastingWeapon,
            ItemType.Costume,
            ItemType.Costume_Headpiece,
            ItemType.Storybook,
            ItemType.Bundle,
            ItemType.Unknown,
        ]
        
        self.filter_actions = [
            ItemAction.Loot,
            ItemAction.Hold,
            ItemAction.Stash,
            ItemAction.Salvage,
            ItemAction.Salvage_Common_Materials,
            ItemAction.Salvage_Rare_Materials,
            ItemAction.Sell_To_Merchant,
            ItemAction.Sell_To_Trader,
            ItemAction.Destroy,
        ]
        
        default_item_types = [
            item_type for item_type in sorted_item_types if item_type not in [
                ItemType.Unknown,
                ItemType.Weapon,
                ItemType.MartialWeapon,
                ItemType.OffhandOrShield,
                ItemType.EquippableItem,
                ItemType.SpellcastingWeapon,
                ItemType.Costume,
                ItemType.Costume_Headpiece,
                ItemType.Storybook,
                ItemType.Bundle,                
                    
                ItemType.Headpiece,
                ItemType.Chestpiece,
                ItemType.Gloves,
                ItemType.Leggings,
                ItemType.Boots,
            ]
        ]
        
        self.action_item_types_map : dict[ItemAction, list[ItemType]] = {            
            ItemAction.Loot : [
                item_type for item_type in sorted_item_types if item_type not in [
                    ItemType.Weapon,
                    ItemType.MartialWeapon,
                    ItemType.OffhandOrShield,
                    ItemType.EquippableItem,
                    ItemType.SpellcastingWeapon,
                ]
            ],
            ItemAction.Stash : [
                item_type for item_type in sorted_item_types if item_type not in [
                    ItemType.Weapon,
                    ItemType.MartialWeapon,
                    ItemType.OffhandOrShield,
                    ItemType.EquippableItem,
                    ItemType.SpellcastingWeapon,
                    ItemType.Bundle,
                ]
            ],
            ItemAction.Salvage : [
                ItemType.Axe,
                ItemType.Bow,
                ItemType.Daggers,
                ItemType.Hammer,
                ItemType.Scythe,
                ItemType.Spear,
                ItemType.Sword,
                ItemType.Staff,
                ItemType.Wand,
                ItemType.Offhand,
                ItemType.Shield,
                ItemType.CC_Shards,
                ItemType.Materials_Zcoins,
                ItemType.Salvage,
                ItemType.Trophy,
            ],
            ItemAction.Salvage_Common_Materials : [
                ItemType.Axe,
                ItemType.Bow,
                ItemType.Daggers,
                ItemType.Hammer,
                ItemType.Scythe,
                ItemType.Spear,
                ItemType.Sword,
                ItemType.Staff,
                ItemType.Wand,
                ItemType.Offhand,
                ItemType.Shield,
                ItemType.CC_Shards,
                ItemType.Materials_Zcoins,
                ItemType.Salvage,
                ItemType.Trophy,
            ],
            ItemAction.Salvage_Rare_Materials : [
                ItemType.Axe,
                ItemType.Bow,
                ItemType.Daggers,
                ItemType.Hammer,
                ItemType.Scythe,
                ItemType.Spear,
                ItemType.Sword,
                ItemType.Staff,
                ItemType.Wand,
                ItemType.Offhand,
                ItemType.Shield,
                ItemType.CC_Shards,
                ItemType.Materials_Zcoins,
                ItemType.Salvage,
                ItemType.Trophy,
            ],
            ItemAction.Sell_To_Merchant : default_item_types,
            ItemAction.Sell_To_Trader : [
                ItemType.Scroll,
                ItemType.Dye,
                ItemType.Materials_Zcoins,
                ItemType.Rune_Mod,
            ],
            ItemAction.Destroy : default_item_types,
        }
        
        self.filter_action_names = [
            self.action_infos[a].name if a in self.action_infos else a.name for a in self.filter_actions 
        ]
                
        self.item_actions = [
            ItemAction.Loot,
            ItemAction.Hold,
            ItemAction.Stash,
            ItemAction.Sell_To_Merchant,
            ItemAction.Sell_To_Trader,
            ItemAction.Salvage,
            ItemAction.Salvage_Common_Materials,
            ItemAction.Salvage_Rare_Materials,
            ItemAction.Destroy,
        ]
        self.item_action_names = [
            self.action_infos[a].name if a in self.action_infos else a.name for a in self.item_actions 
        ]
                
        
        self.os_low_req_itemtype_selectables: list[SelectableWrapper] = [
            SelectableWrapper(ItemType.Axe, False),
            SelectableWrapper(ItemType.Bow, False),
            SelectableWrapper(ItemType.Daggers, False),
            SelectableWrapper(ItemType.Hammer, False),
            SelectableWrapper(ItemType.Scythe, False),
            SelectableWrapper(ItemType.Spear, False),
            SelectableWrapper(ItemType.Sword, False),
            SelectableWrapper(ItemType.Staff, False),
            SelectableWrapper(ItemType.Wand, False),
            SelectableWrapper(ItemType.Offhand, False),
            SelectableWrapper(ItemType.Shield, False),
        ]
        
        self.mod_heights: dict[str, float] = {}
        self.filter_popup = False

        self.action_heights: dict[ItemAction, float] = {
                            ItemAction.Salvage: 250,
                            ItemAction.Stash: 75,
                        }
        self.selected_filter: Optional[ItemFilter] = None
        self.filters : list[ItemFilter] = [
            ItemFilter("All Items", lambda item: True),
            
            ItemFilter("Weapons", lambda item: item.item_type in self.weapon_types),
            ItemFilter("Axe", lambda item: item.item_type == ItemType.Axe),
            ItemFilter("Bow", lambda item: item.item_type == ItemType.Bow),
            ItemFilter("Daggers", lambda item: item.item_type == ItemType.Daggers),            
            ItemFilter("Hammer", lambda item: item.item_type == ItemType.Hammer),
            ItemFilter("Scythe", lambda item: item.item_type == ItemType.Scythe),
            ItemFilter("Spear", lambda item: item.item_type == ItemType.Spear),
            ItemFilter("Sword", lambda item: item.item_type == ItemType.Sword),
            ItemFilter("Staff", lambda item: item.item_type == ItemType.Staff),
            ItemFilter("Wand", lambda item: item.item_type == ItemType.Wand),
            ItemFilter("Offhand", lambda item: item.item_type == ItemType.Offhand),
            ItemFilter("Shield", lambda item: item.item_type == ItemType.Shield),
            
            ItemFilter("Armor", lambda item: item.item_type in [
                ItemType.Chestpiece,
                ItemType.Headpiece,
                ItemType.Leggings,
                ItemType.Boots,
                ItemType.Gloves,
            ]),
            ItemFilter("Upgrades", lambda item: item.item_type == ItemType.Rune_Mod),
            ItemFilter("Consumables", lambda item: item.category == ItemCategory.Alcohol or
                                                    item.category == ItemCategory.Sweet or
                                                    item.category == ItemCategory.Party or
                                                    item.category == ItemCategory.DeathPenaltyRemoval),
            ItemFilter("Alcohol", lambda item: item.category == ItemCategory.Alcohol),
            ItemFilter("Sweets", lambda item: item.category == ItemCategory.Sweet),
            ItemFilter("Party", lambda item: item.category == ItemCategory.Party),
            ItemFilter("Death Penalty Removal", lambda item: item.category == ItemCategory.DeathPenaltyRemoval),
            ItemFilter("Scrolls", lambda item: item.category == ItemCategory.Scroll),
            ItemFilter("Tomes", lambda item: item.category == ItemCategory.Tome),
            ItemFilter("Keys", lambda item: item.category == ItemCategory.Key),
            ItemFilter("Materials", lambda item: item.category == ItemCategory.Material),
            ItemFilter("Trophies", lambda item: item.category == ItemCategory.Trophy),
            ItemFilter("Reward Trophies", lambda item: item.category == ItemCategory.RewardTrophy),
            ItemFilter("Quest Items", lambda item: item.category == ItemCategory.QuestItem), 
            ItemFilter("Miniatures", lambda item: item.item_type == ItemType.Minipet),   
        ]
        self.selected_skin_filter: Optional[ItemFilter] = None
        self.skin_search = ""
        self.skin_select_popup = False
        self.skin_select_popup_open = False
        self.show_add_rule_popup = False
        self.rule_name = ""        
        self.rule_filter_popup = False
        self.selected_rule_filter: Optional[RuleFilter] = None
        self.rule_filters : list[RuleFilter] = [
            RuleFilter("All Items", lambda rule: True),   
            RuleFilter("Weapons", lambda rule: any(item_type in self.weapon_types for item_type in [item.item_type for item in rule.get_items()])),
            RuleFilter("Axe", lambda rule: any(item_type == ItemType.Axe for item_type in [item.item_type for item in rule.get_items()])),
            RuleFilter("Bow", lambda rule: any(item_type == ItemType.Bow for item_type in [item.item_type for item in rule.get_items()])),
            RuleFilter("Daggers", lambda rule: any(item_type == ItemType.Daggers for item_type in [item.item_type for item in rule.get_items()])),
            RuleFilter("Hammer", lambda rule: any(item_type == ItemType.Hammer for item_type in [item.item_type for item in rule.get_items()])),
            RuleFilter("Scythe", lambda rule: any(item_type == ItemType.Scythe for item_type in [item.item_type for item in rule.get_items()])),
            RuleFilter("Spear", lambda rule: any(item_type == ItemType.Spear for item_type in [item.item_type for item in rule.get_items()])),
            RuleFilter("Sword", lambda rule: any(item_type == ItemType.Sword for item_type in [item.item_type for item in rule.get_items()])),
            RuleFilter("Staff", lambda rule: any(item_type == ItemType.Staff for item_type in [item.item_type for item in rule.get_items()])),
            RuleFilter("Wand", lambda rule: any(item_type == ItemType.Wand for item_type in [item.item_type for item in rule.get_items()])),
            RuleFilter("Offhand", lambda rule: any(item_type == ItemType.Offhand for item_type in [item.item_type for item in rule.get_items()])),
            RuleFilter("Shield", lambda rule: any(item_type == ItemType.Shield for item_type in [item.item_type for item in rule.get_items()])),
            RuleFilter("Armor", lambda rule: any(item_type in [
                ItemType.Chestpiece,
                ItemType.Headpiece,
                ItemType.Leggings,
                ItemType.Boots,
                ItemType.Gloves,
            ] for item_type in [item.item_type for item in rule.get_items()])),
            RuleFilter("Upgrades", lambda rule: any(item.item_type == ItemType.Rune_Mod for item in rule.get_items())),
            RuleFilter("Consumables", lambda rule: any(item.category in [
                ItemCategory.Alcohol,
                ItemCategory.Sweet,
                ItemCategory.Party,
                ItemCategory.DeathPenaltyRemoval
            ] for item in rule.get_items())),
            RuleFilter("Alcohol", lambda rule: any(item.category == ItemCategory.Alcohol for item in rule.get_items())),
            RuleFilter("Sweets", lambda rule: any(item.category == ItemCategory.Sweet for item in rule.get_items())),
            RuleFilter("Party", lambda rule: any(item.category == ItemCategory.Party for item in rule.get_items())),
            RuleFilter("Death Penalty Removal", lambda rule: any(item.category == ItemCategory .DeathPenaltyRemoval for item in rule.get_items())),
            RuleFilter("Scrolls", lambda rule: any(item.category == ItemCategory.Scroll for item in rule.get_items())),
            RuleFilter("Tomes", lambda rule: any(item.category == ItemCategory.Tome for item in rule.get_items())),
            RuleFilter("Keys", lambda rule: any(item.category == ItemCategory.Key for item in rule.get_items())),
            RuleFilter("Materials", lambda rule: any(item.category == ItemCategory.Material for item in rule.get_items())),
            RuleFilter("Trophies", lambda rule: any(item.category == ItemCategory.Trophy for item in rule.get_items())),
            RuleFilter("Reward Trophies", lambda rule: any(item.category == ItemCategory.RewardTrophy for item in rule.get_items())),
            RuleFilter("Quest Items", lambda rule: any(item.category == ItemCategory.QuestItem for item in rule.get_items())),            
        ]
        self.ensure_window_on_screen = True
        
        self.data_collector = DataCollector()
        self.filter_weapon_mods()        
        self.filter_items()    
        self.filter_rules()
            
    def get_window_info(self):
        window = self.imgui_ini_reader.get("LootEx")
        window_pos = window.pos if window else (100.0, 100.0)
        window_size = window.size if window else (800.0, 600.0)
        collapse = window.collapsed if window else False
        
        return window_pos, window_size, collapse
    
    def show_main_window(self, ensure_on_screen: bool = False):             
        widget_info = self.widget_handler.get_widget_info("LootEx")
        if not widget_info or widget_info.configuring:
            return
        
        widget_info.enable_configuring()
        
    def hide_main_window(self):              
        widget_info = self.widget_handler.get_widget_info("LootEx")
        if not widget_info or not widget_info.configuring:
            return
        
        widget_info.disable_configuring()
    
    def draw_disclaimer(self, active_inventory_widgets):
        if not self.InventoryBagsVisible():
            if self.inventory_coords is not None:
                self.inventory_coords = None
            return
        
        self.inventory_coords = settings.FrameCoords(UIManager.GetFrameIDByHash(291586130))

        if self.inventory_coords is None:
            return
        
        ui_size = UIManager.GetEnumPreference(EnumPreference.InterfaceSize)
        window_offsets = {
            4294967295: (160, 0),   # Small
            0: (160, 0),   # Medium
            1: (180, 0),   # Large
            2: (200, 0),   # Largest
        }
        width = self.inventory_coords.width - window_offsets.get(ui_size, (0, 0))[0] - 50
        height = 19
        
        PyImGui.set_next_window_pos(
            (self.inventory_coords.left + window_offsets.get(ui_size, (0, 0))[0], self.inventory_coords.top),
            PyImGui.ImGuiCond.Always,
        )
        PyImGui.set_next_window_size(
            (width, height),
            PyImGui.ImGuiCond.Always,
        )
        style = ImGui.get_style()
        style.WindowRounding.push_style_var(0)
        style.WindowPadding.push_style_var(5, 3)
        
        if PyImGui.begin(
            "Loot Ex Inventory Disclaimer",
            PyImGui.WindowFlags.NoTitleBar
            | PyImGui.WindowFlags.NoResize
            | PyImGui.WindowFlags.AlwaysAutoResize
            | PyImGui.WindowFlags.NoCollapse
            | PyImGui.WindowFlags.NoMove
            | PyImGui.WindowFlags.NoScrollbar
            | PyImGui.WindowFlags.NoScrollWithMouse
            | PyImGui.WindowFlags.NoSavedSettings            
            | PyImGui.WindowFlags.NoMouseInputs  
            | PyImGui.WindowFlags.NoBackground  
        ):
            screen_cursor_pos = PyImGui.get_cursor_screen_pos()
            PyImGui.same_line(25, 0)
            ImGui.text_decorated("LootEx disabled", decorator=TextDecorator.None_, font_style="Regular", font_size=14, color=style.Text.color_tuple)
            
            font_size = 10
            PyImGui.draw_list_add_rect_filled(screen_cursor_pos[0] + font_size / 2, screen_cursor_pos[1] - 2 + font_size / 2, screen_cursor_pos[0] + font_size - 1, screen_cursor_pos[1] - 1 + font_size + 2, Color().color_int, 0, 0)
            
            PyImGui.same_line(5, 0)
            PyImGui.set_cursor_pos_y(4)
            ImGui.text_colored(f"{IconsFontAwesome5.ICON_EXCLAMATION_TRIANGLE}", Color(255, 40, 40, 255).color_tuple, font_style="Regular", font_size=font_size)
            pass
            
            wp = PyImGui.get_window_pos()
            ws = PyImGui.get_window_size()
            if ImGui.is_mouse_in_rect((wp[0], wp[1], ws[0], ws[1])):
                PyImGui.begin_tooltip()            
                ImGui.text("LootEx is disabled to avoid conflicts")                
                ImGui.separator()
                ImGui.text_decorated("Conflicting Widgets:", TextDecorator.Underline)
                
                for widget in active_inventory_widgets:
                    ImGui.bullet_text(widget)
                PyImGui.end_tooltip()

        PyImGui.end()
        
        style.WindowPadding.pop_style_var()
        style.WindowRounding.pop_style_var()
    
    def draw_window(self):
        widget_info = self.widget_handler.get_widget_info("LootEx")
        
        self.settings.window_visible = widget_info.configuring if widget_info else False
        self.module_window.open = self.settings.window_visible
        
        if not widget_info or not widget_info.configuring:
            return       

        window_style = ex_style.ExStyle()
        window_style.push_style()
                
        if self.module_window.begin():
            style = ImGui.get_style()
            
            if self.ensure_window_on_screen:
                ImGui.set_window_within_displayport(300, 100)
                self.ensure_window_on_screen = False
            
            if self.settings.profile:
                self.window_flags = (
                    PyImGui.WindowFlags.NoMove if PyImGui.is_mouse_down(
                        0) else PyImGui.WindowFlags.NoFlag
                )

                profile_names = [
                    profile.name for profile in self.settings.profiles]
                profile_index = profile_names.index(self.settings.profile.name) if self.settings.profile else 0
                
                width = PyImGui.get_content_region_avail()[0]
                PyImGui.push_item_width(width - 90)
                selected_index = ImGui.combo(
                    "", profile_index, profile_names)
                PyImGui.pop_item_width()

                if profile_index != selected_index:
                    ConsoleLog(
                        "LootEx",
                        f"Profile changed to {profile_names[selected_index]}",
                        Console.MessageType.Info,
                    )
                    self.settings.SetProfile(profile_names[selected_index])                
                    self.settings.save()

                PyImGui.same_line(0, 2)
                
                if ImGui.icon_button(IconsFontAwesome5.ICON_PLUS, 28, 24):
                    self.show_add_profile_popup = not self.show_add_profile_popup
                    if self.show_add_profile_popup:
                        PyImGui.open_popup("Add Profile")
                    else:
                        PyImGui.close_current_popup()

                ImGui.show_tooltip("Add New Profile")
                PyImGui.same_line(0, 2)
                
                if ImGui.icon_button(IconsFontAwesome5.ICON_TRASH, 28, 24) and len(self.settings.profiles) > 1:
                # if GUI.image_button(texture_map.CoreTextures.UI_Destroy.value, (20, 20)) and len(self.settings.profiles) > 1:
                    self.show_delete_profile_popup = not self.show_delete_profile_popup
                    if self.show_delete_profile_popup:
                        PyImGui.open_popup("Delete Profile")
                    else:
                        PyImGui.close_current_popup()

                ImGui.show_tooltip("Delete Profile '" +
                                self.settings.profile.name + "'")
                PyImGui.same_line(0, 2)


                active = self.settings.automatic_inventory_handling
                
                if active:
                    style.Text.push_color((0, 255, 0, 255))
                
                if ImGui.icon_button(IconsFontAwesome5.ICON_CHECK, 28, 24):
                    
                    if active:
                        inventory_handling.InventoryHandler().Stop()
                    else:
                        inventory_handling.InventoryHandler().Start()

                if active:
                    style.Text.pop_color()

                
                ImGui.show_tooltip(
                    ("Disable" if self.settings.automatic_inventory_handling else "Enable") + " Inventory Handling")

                if ImGui.begin_tab_bar("LootExTabBar"):
                    self.draw_general_settings()
                    if ImGui.begin_tab_item("Rules"):
                        if self.first_draw:
                            self.filter_rules()
                            
                        if ImGui.begin_tab_bar("RulesTabBar"):
                            self.draw_by_item_type()
                            self.draw_by_item_skin()
                            self.draw_low_req()
                            ImGui.end_tab_bar()

                        ImGui.end_tab_item()
                    
                    self.draw_item_conversions()
                    self.draw_crafting()
                        
                    self.draw_weapon_mods()
                    self.draw_runes()
                    self.draw_rare_weapons()
                    self.draw_blacklist()
                    self.draw_prices_tab()
                    self.draw_data_collector_tab()
                    
                    self.first_draw = False

                ImGui.end_tab_bar()

                pos = PyImGui.get_window_pos()
                size = PyImGui.get_window_size()

                if self.module_window.window_size != (size[0], size[1]) and not self.module_window.collapse:
                    self.mod_heights.clear()

                self.draw_delete_profile_popup()
                self.draw_profiles_popup()

            self.module_window.process_window()
                
        self.module_window.end()
        window_style.pop_style()
        
        if self.module_window.open != self.settings.window_visible:
            self.settings.window_visible = self.module_window.open
            if widget_info.configuring != self.module_window.open:
                widget_info.set_configuring(self.module_window.open)
            self.settings.save()
    
    def InventoryBagsVisible(self) -> bool:
        # return UIManager.IsWindowVisible(WindowID.WindowID_InventoryBags) 
        return UIManagerExtensions.IsElementVisible(UIManager.GetFrameIDByHash(291586130))  # "Inventory Bags" frame hash
    
    def draw_vault_controls(self):    
        if not GLOBAL_CACHE.Inventory.IsStorageOpen():
            return
        
        storage_id = UIManager.GetFrameIDByHash(2315448754)  # "Xunlai Storage" frame hash
        
        if not UIManagerExtensions.IsElementVisible(storage_id):
            return
        
        coords = settings.FrameCoords(storage_id)  # "Xunlai Window" frame hash

        if coords is None:
            return
        
        width = 30
        PyImGui.set_next_window_pos(coords.right - (width) - 20, coords.top + 50)
        PyImGui.set_next_window_size(width, 0)
        PyImGui.push_style_color(PyImGui.ImGuiCol.WindowBg,
                                    Utils.ColorToTuple(Utils.RGBToColor(0, 0, 0, 125)))
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 0, 0)    
        if PyImGui.begin(
            "Loot Ex Vault Controls",
            PyImGui.WindowFlags.NoTitleBar
            | PyImGui.WindowFlags.NoResize
            | PyImGui.WindowFlags.NoBackground
            | PyImGui.WindowFlags.AlwaysAutoResize
            | PyImGui.WindowFlags.NoCollapse
            | PyImGui.WindowFlags.NoMove
            | PyImGui.WindowFlags.NoSavedSettings,
        ):
            PyImGui.pop_style_var(1)
            PyImGui.pop_style_color(1)

            if UI.transparent_button(IconsFontAwesome5.ICON_TH, True, width, width):
                imgui_io = self.py_io
                if imgui_io.key_ctrl:
                    # messaging.SendOpenXunlai(imgui_io.key_shift)
                    pass
                else:
                    inventory_handling.InventoryHandler().CondenseStacks(Bag.Storage_1, Bag.Storage_14)
                    inventory_handling.InventoryHandler().SortBags(Bag.Storage_1, Bag.Storage_14)
                    

            ImGui.show_tooltip("Condense items to full stacks" +
                            "\nHold Ctrl to send message to all accounts" +
                            "\nHold Shift to send message to all accounts excluding yourself")

            PyImGui.end()

    def draw_inventory_controls(self):    
        if not self.InventoryBagsVisible():
            if self.inventory_coords is not None:
                self.inventory_coords = None
            return
        
        self.inventory_coords = settings.FrameCoords(UIManager.GetFrameIDByHash(291586130))

        if self.inventory_coords is None:
            return

        width = 30
        PyImGui.set_next_window_pos(self.inventory_coords.left - (width - 5), self.inventory_coords.top + 20)
        PyImGui.set_next_window_size(width, 0)
        PyImGui.push_style_color(PyImGui.ImGuiCol.WindowBg,
                                Utils.ColorToTuple(Utils.RGBToColor(0, 0, 0, 125)))
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 0, 0)

        if PyImGui.begin(
            "Loot Ex Inventory Controls",
            PyImGui.WindowFlags.NoTitleBar
            | PyImGui.WindowFlags.NoResize
            | PyImGui.WindowFlags.NoBackground
            | PyImGui.WindowFlags.AlwaysAutoResize
            | PyImGui.WindowFlags.NoCollapse
            | PyImGui.WindowFlags.NoMove
            | PyImGui.WindowFlags.NoSavedSettings,
        ):
            PyImGui.pop_style_var(1)
            PyImGui.pop_style_color(1)

            self._draw_inventory_toggle_button(width)
            self._draw_date_collection_toggle_button(width)
            self._draw_manual_window_toggle_button(width)
            self._draw_xunlai_storage_button(width)
            self._draw_sort_inventory_button(width)

            PyImGui.end()
            
    def _draw_inventory_toggle_button(self, width):
        if UI.transparent_button(IconsFontAwesome5.ICON_CHECK, self.settings.automatic_inventory_handling, width, width):
            imgui_io = self.py_io

            if imgui_io.key_ctrl:
                if self.settings.automatic_inventory_handling:
                    messaging.SendStop(imgui_io.key_shift)
                else:
                    messaging.SendStart(imgui_io.key_shift)

            else:
                if self.settings.automatic_inventory_handling:
                    inventory_handling.InventoryHandler().Stop()
                else:
                    inventory_handling.InventoryHandler().Start()  
                     
        ImGui.show_tooltip(
            ("Disable" if self.settings.automatic_inventory_handling else "Enable") +
            " Inventory Handling" +
            "\nHold Ctrl to send message to all accounts" +
            "\nHold Shift to send message to all accounts excluding yourself"
        )
            
        if UI.transparent_button(IconsFontAwesome5.ICON_COINS, self.settings.enable_loot_filters, width, width):
            imgui_io = self.py_io

            if imgui_io.key_ctrl:
                if self.settings.enable_loot_filters:
                    messaging.SendLootingStop(imgui_io.key_shift)
                else:
                    messaging.SendLootingStart(imgui_io.key_shift)

            else:
                if self.settings.enable_loot_filters:
                    loot_handling.LootHandler().Stop()
                else:
                    loot_handling.LootHandler().Start()                    

        ImGui.show_tooltip(
            ("Disable" if self.settings.enable_loot_filters else "Enable") +
            " Loot Filters" +
            "\nHold Ctrl to send message to all accounts" +
            "\nHold Shift to send message to all accounts excluding yourself"
        )

    def _draw_sort_inventory_button(self, width):
        if UI.transparent_button(IconsFontAwesome5.ICON_SORT_ALPHA_DOWN, True, width, width):
            inventory_handling.InventoryHandler().CompactInventory()      
        
        ImGui.show_tooltip(
            "Sort/Compact Inventory" +
            "\nAutomatically stacks items and sorts them in your inventory")                  

    def _draw_date_collection_toggle_button(self, width):
        if UI.transparent_button(IconsFontAwesome5.ICON_LANGUAGE, self.settings.scraper_window_visible, width, width):
            self.settings.scraper_window_visible = not self.settings.scraper_window_visible

        #     imgui_io = self.py_io

        #     if imgui_io.key_ctrl:
        #         if self.settings.collect_items:
        #             messaging.SendPauseDataCollection(imgui_io.key_shift)
        #             self.settings.save()
        #         else:
        #             messaging.SendStartDataCollection(imgui_io.key_shift)
        #             self.settings.save()

        #     elif imgui_io.key_shift:
        #         self.settings.scraper_window_visible = not self.settings.scraper_window_visible
                
        #     else:
        #         if self.settings.collect_items:
        #             data_collector.instance.stop_collection()
        #             self.settings.save()
        #         else:
        #             data_collector.instance.start_collection()
        #             self.settings.save()

        ImGui.show_tooltip(
            ("Close" if self.settings.scraper_window_visible else "Open") +
            " Item Data Collection"
        )
    
    def _draw_manual_window_toggle_button(self, width):
        if UI.transparent_button(IconsFontAwesome5.ICON_COG, self.settings.window_visible, width, width):
            imgui_io = self.py_io
            if imgui_io.key_ctrl:
                if self.settings.window_visible:
                    messaging.SendHideLootExWindow(imgui_io.key_shift)
                    self.settings.save()
                else:
                    messaging.SendShowLootExWindow(imgui_io.key_shift)
                    self.settings.save()
            else:
                self.settings.window_visible = not self.settings.window_visible
                
                if self.settings.window_visible:
                    self.show_main_window(True) 
                else:
                    self.hide_main_window()
    
                self.settings.save()

        ImGui.show_tooltip(
            ("Hide" if self.settings.window_visible else "Show") + " Window" +
            "\nHold Ctrl to send message to all accounts" +
            "\nHold Shift to send message to all accounts excluding yourself")

    def _draw_xunlai_storage_button(self, width):
        xunlai_open = GLOBAL_CACHE.Inventory.IsStorageOpen()

        if UI.transparent_button(
            IconsFontAwesome5.ICON_BOX_OPEN if xunlai_open else IconsFontAwesome5.ICON_BOX, xunlai_open, width, width
        ):
            if xunlai_open:
                # Inventory.close_storage()
                pass
            else:
                imgui_io = self.py_io

                if imgui_io.key_ctrl:
                    messaging.SendOpenXunlai(imgui_io.key_shift)
                else:
                    Inventory.OpenXunlaiWindow()

        ImGui.show_tooltip("Open Xunlai Storage" +
                        "\nHold Ctrl to send message to all accounts" +
                        "\nHold Shift to send message to all accounts excluding yourself")

    def draw_debug_item(self, i : int, cached_item: cache.Cached_Item, button_width: int = 200, button_height: int = 50):
        style = ImGui.get_style()
        
        if PyImGui.is_rect_visible(button_width, button_height):       
            colored_item = 0
             
            if cached_item.id > 0 and (not cached_item.data or not cached_item.data.wiki_scraped):
                style.ChildBg.push_color((255, 0, 0, 125))
                colored_item += 1
            
            collected = cached_item.data.is_minimum_complete() if cached_item.id != 0 and cached_item.data else True
            localization_missing, missing_languages = self.data_collector.is_missing_localization(cached_item)
            mods_missing, mod_missing = self.data_collector.has_uncollected_mods(cached_item) if cached_item.id != 0 else (False, "")
            
            complete = True
            
            if not localization_missing:
                complete = (collected and not mods_missing)
                
                if not complete:
                    style.ChildBg.push_color((255, 255, 0, 125))
                    colored_item += 1
            else:
                style.ChildBg.push_color((255, 178, 102, 125))
                colored_item += 1

            style.Border.push_color(utility.Util.GetRarityColorDict(cached_item.rarity)["text"])
            border_popped = False
            
            if ImGui.begin_child(str(i), (button_width, button_height), True, PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse):    
                style.Border.pop_color()                                               
                image_size = (32, 32)     
                          
                if PyImGui.is_rect_visible(image_size[0], image_size[1]):                 
                    remaining_size = PyImGui.get_content_region_avail()
                    
                    ImGui.begin_table("ItemTable", 2, PyImGui.TableFlags.NoBordersInBody, remaining_size[0], remaining_size[1] - 30)
                    PyImGui.table_setup_column("Icon", PyImGui.TableColumnFlags.WidthFixed, image_size[0])
                    PyImGui.table_setup_column("Info", PyImGui.TableColumnFlags.WidthStretch)
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    
                    if cached_item.data and cached_item.data.texture_file:
                        if cached_item.item_type == ItemType.Dye:
                            dye = cached_item.dye_info.dye1
                            texture = self.dye_textures.get(dye.ToInt(), "")
                        else:
                            texture = cached_item.data.texture_file
                            
                        ImGui.DrawTexture(
                            texture,
                            image_size[0], image_size[1]
                        )
                    elif cached_item.id > 0:
                        texture = os.path.join(Py4GW.Console.get_projects_path(), "Textures", "missing_texture.png") ##TODO: Replace with wiki texture
                        ImGui.DrawTexture(
                            texture,
                            image_size[0], image_size[1]
                        )
                        
                    else:
                        PyImGui.dummy(image_size[0], image_size[1])
                        
                    PyImGui.table_next_column()
                        
                    ImGui.text_scaled(str(cached_item.id) if cached_item.id > 0 else "", (1,1,1,0.75), 0.7)
                    ImGui.text_scaled(str(cached_item.model_id) if cached_item.model_id > 0 else "", (1,1,1,1), 0.8)
                    ImGui.text_wrapped(cached_item.name if cached_item.name else "Unknown Item")
                    # ImGui.text_scaled(f"x{cached_item.quantity}" if cached_item.quantity > 1 else "", (1,1,1,1), 0.8)
                    
                    ImGui.end_table()
 
                style.WindowPadding.push_style_var(15.0, 5.0)
                style.ChildBg.push_color((50, 50, 50, 125))
                
                ImGui.begin_child("ItemInfoChild", (0, 0), True, PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse)
                action_texture = self.action_infos.get_texture(cached_item.action, None)                
                if action_texture:
                    ImGui.DrawTexture(action_texture, 14, 14)
                    PyImGui.same_line(0, 5)
                    ImGui.text(utility.Util.reformat_string(cached_item.action.name))
                    
                ImGui.end_child()
                style.ChildBg.pop_color()
                style.WindowPadding.pop_style_var()
                                
            
            ImGui.end_child()
            if not border_popped:
                style.Border.pop_color()
            
            for _ in range(colored_item):
                style.ChildBg.pop_color()
                
            if cached_item:
                if PyImGui.is_item_hovered():
                    PyImGui.set_next_window_size(500, 0)
                    
                    ImGui.begin_tooltip()
                    if cached_item.data:
                        self.draw_cached_item_header(item=cached_item)
                        
                    if PyImGui.is_rect_visible(0, 20):
                        ImGui.begin_table("ItemInfoTable", 2, PyImGui.TableFlags.Borders)
                        PyImGui.table_setup_column("Property")
                        PyImGui.table_setup_column("Value")
                        PyImGui.table_headers_row()
                        PyImGui.table_next_row()
                        
                        PyImGui.table_next_column()
                        ImGui.text(f"Item Id")
                        
                        PyImGui.table_next_column()
                        ImGui.text(str(cached_item.id) if cached_item.id > 0 else "N/A")
                        
                        PyImGui.table_next_column()
                        ImGui.text(f"Model File Id")
                        
                        PyImGui.table_next_column()
                        ImGui.text(str(cached_item.model_file_id) if cached_item.model_file_id > -1 else "N/A")
                        
                        PyImGui.table_next_column()
                        ImGui.text(f"Model Id")
                        
                        PyImGui.table_next_column()
                        ImGui.text(str(cached_item.model_id) if cached_item.model_id > -1 else "N/A")
                        
                        PyImGui.table_next_column()
                        ImGui.text(f"Quantity")
                        
                        PyImGui.table_next_column()
                        ImGui.text(str(cached_item.quantity) if cached_item.quantity > 0 else "N/A")
                        
                        PyImGui.table_next_column()
                        ImGui.text("Inscribable")

                        PyImGui.table_next_column()
                        inscribable = cached_item.is_inscribable
                        ImGui.text_colored(str(inscribable), (0, 1, 0, 1) if inscribable else (1, 0, 0, 1))
                        
                        
                        if cached_item.weapon_mods_to_keep and len(cached_item.weapon_mods_to_keep) > 1:
                            PyImGui.table_next_column()
                            ImGui.text("Mods to Keep")
                            
                            PyImGui.table_next_column()
                            for mod in cached_item.weapon_mods_to_keep:
                                ImGui.text(mod.WeaponMod.name)
                                
                        if cached_item.runes_to_keep and len(cached_item.runes_to_keep) > 1:
                            PyImGui.table_next_column()
                            ImGui.text("Runes to Keep")
                            
                            PyImGui.table_next_column()
                            for mod in cached_item.runes_to_keep:
                                ImGui.text(mod.Rune.name)
                        
                        if cached_item.runes:
                            PyImGui.table_next_column()
                            ImGui.text("Runes")
                            
                            PyImGui.table_next_column()
                            for mod in cached_item.runes:
                                ImGui.text(utility.Util.reformat_string(mod.Rune.name))
                        
                        if cached_item.weapon_mods:
                            PyImGui.table_next_column()
                            ImGui.text("Mods")
                            
                            PyImGui.table_next_column()
                            for mod in cached_item.weapon_mods:
                                ImGui.text(f"{utility.Util.reformat_string(mod.WeaponMod.name)}")
                                value = mod.Value
                                desc = mod.Description
                                ImGui.text(f"{utility.Util.reformat_string(desc)}", 12)
                                
                        if cached_item.max_weapon_mods:
                            PyImGui.table_next_column()
                            ImGui.text("Max Mods")
                            
                            PyImGui.table_next_column()
                            for mod in cached_item.max_weapon_mods:
                                ImGui.text(utility.Util.reformat_string(mod.WeaponMod.name))
                        
                        if cached_item.weapon_mods_to_keep:
                            PyImGui.table_next_column()
                            ImGui.text("Desired Mods")
                            
                            PyImGui.table_next_column()
                            for mod in cached_item.weapon_mods_to_keep:
                                ImGui.text(utility.Util.reformat_string(mod.WeaponMod.name))
                        
                        if cached_item.is_rare_weapon:
                            PyImGui.table_next_column()
                            ImGui.text("Rare Weapon")

                            PyImGui.table_next_column()
                            ImGui.text_colored("Yes", (0, 1, 0, 1))
                            
                        if cached_item.is_rare_weapon_to_keep:
                            PyImGui.table_next_column()
                            ImGui.text("Keep Rare Weapon")

                            PyImGui.table_next_column()
                            ImGui.text_colored("Yes", (0, 1, 0, 1))
                                                        
                        if cached_item.matches_weapon_rule:
                            PyImGui.table_next_column()
                            ImGui.text("By Weapon Rule Matched")

                            PyImGui.table_next_column()
                            ImGui.text_colored(cached_item.weapon_rule.item_type.name if cached_item.weapon_rule else "Unkown Weapon Rule", (0, 1, 0, 1))
                                                    
                        if cached_item.matches_skin_rule:
                            PyImGui.table_next_column()
                            ImGui.text("Skin Rule Matched")

                            PyImGui.table_next_column()
                            ImGui.text_colored(cached_item.skin_rule.skin if cached_item.skin_rule else "Unknown Rule Skin", (0, 1, 0, 1))
                        
                        if cached_item.is_customized:
                            PyImGui.table_next_column()
                            ImGui.text("Customized")

                            PyImGui.table_next_column()
                            ImGui.text_colored("Customized - Ignore!", (1, 0, 0, 1))
                        
                                
                        PyImGui.table_next_column()
                        ImGui.text("Action")
                        
                        PyImGui.table_next_column()
                        action_info = self.action_infos.get(cached_item.action, None)
                        action_texture = action_info.icon if action_info else None
                        
                        if action_texture:
                            ImGui.DrawTexture(action_texture, 14, 16)
                            PyImGui.same_line(0, 5)
                        
                        ImGui.text(utility.Util.reformat_string(cached_item.action.name))
                                                
                        ImGui.end_table()
                    
                    if not collected:
                        ImGui.text_colored("Minimum data missing (Inventory Icon or Name)", (255, 0, 0, 255))
                        
                    if localization_missing:
                        ImGui.text_colored(missing_languages, (255, 0, 0, 255))
                        
                    if mods_missing:
                        ImGui.text_colored(mod_missing, (255, 0, 0, 255))
                    
                    if cached_item.data and not cached_item.data.wiki_scraped:
                        ImGui.text_colored("Wiki data not scraped yet", (255, 0, 0, 255))
                        
                        
                        
                    ImGui.end_tooltip()
                pass
        else:
            PyImGui.dummy(int(button_width), int(button_height))
        
    def draw_data_collector_tab(self):
        if ImGui.begin_tab_item("Debug & Data"):
            tab_size = PyImGui.get_content_region_avail()
            child_width = tab_size[0] - 10
            tab1_size = (max(400, child_width * 0.25), tab_size[1])
            tab2_size = (child_width - tab1_size[0], tab_size[1])
            
            if ImGui.begin_child("DataCollectorChild", tab1_size, True, PyImGui.WindowFlags.NoFlag):
                ImGui.text("Data Collector")
                ImGui.separator()

                child_size = PyImGui.get_content_region_avail()
                if PyImGui.is_rect_visible(0, 20):
                    if ImGui.begin_table("DataCollectorTable", 2, PyImGui.TableFlags.ScrollY, 200, child_size[1] - 5):
                        PyImGui.table_setup_column("Data")
                        PyImGui.table_setup_column("Amount", PyImGui.TableColumnFlags.WidthFixed, 50)

                        # PyImGui.table_headers_row()
                        PyImGui.table_next_row()

                        PyImGui.table_next_column()
                        ImGui.text(f"Weapon Mods")
                        PyImGui.table_next_column()
                        ImGui.text(f"{len(self.data.Weapon_Mods)}")

                        PyImGui.table_next_column()
                        ImGui.text(f"Runes")
                        PyImGui.table_next_column()
                        ImGui.text(f"{len(self.data.Runes)}")

                        PyImGui.table_next_column()
                        ImGui.text(f"Items")
                        PyImGui.table_next_column()
                        ImGui.text(f"{len(self.data.Items.All)}")
                        
                        PyImGui.table_next_column()
                        ImGui.separator()
                        PyImGui.table_next_column()
                        ImGui.separator()
                        
                        
                        for item_type, items in self.data.Items.items():                            
                            item_count = len(items)
                            if item_count > 0:
                                PyImGui.table_next_column()
                                ImGui.text(f"{item_type.name}")
                                PyImGui.table_next_column()
                                ImGui.text(f"{item_count}")
                                
                    ImGui.end_table()
                
                PyImGui.same_line(0, 5)
                if ImGui.begin_child("DataCollectorButtonsChild", (0, child_size[1] - 5), False, PyImGui.WindowFlags.NoFlag):
                    PyImGui.indent(3)
                    
                    if ImGui.button("Merge Diffs into Data", 160, 30):
                        ConsoleLog(
                            "LootEx",
                            "Merging diffs into self.data...",
                            Console.MessageType.Info,
                        )

                        messaging.SendMergingMessage()

                    ImGui.show_tooltip("Merge all diff files into the data files.")
                                        
                    if False and ImGui.button("Move Textures", 160, 30):
                        items_folder = os.path.join(Py4GW.Console.get_projects_path(), "Textures", "Items")
                        item_model_files_folder = os.path.join(Py4GW.Console.get_projects_path(), "Textures", "ItemModelFiles")
                        
                        for item in self.data.Items.All:
                            if item.inventory_icon and item.model_file_id:
                                source_path = os.path.join(items_folder, f"{item.inventory_icon}")
                                dest_path = os.path.join(item_model_files_folder, f"{item.model_file_id}.png")
                                
                                if os.path.exists(source_path):
                                    if not os.path.exists(dest_path):
                                        shutil.copy2(source_path, dest_path)
                                        ConsoleLog("LootEx", f"Moved texture for Item {item.name}", Console.MessageType.Info)
                        pass

                    def on_test_button_clicked():
                        # items
                        return

                    if self.settings.development_mode and ImGui.button("Test 123", 160, 30):
                        on_test_button_clicked()
                                                 
                ImGui.end_child()
            
            ImGui.end_child()
                
            PyImGui.same_line(0, 5)
            
            if ImGui.begin_child("DataCollectorIventory", tab2_size, True, PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse):
                if True:
                    child_size = PyImGui.get_content_region_avail()
                                                                
                    PyImGui.push_item_width(child_size[0] - 135)
                    self.bag_index = ImGui.combo(
                        "##Bag",
                        self.bag_index,
                        self.bag_names
                    )
                    PyImGui.pop_item_width()
                                            
                    PyImGui.same_line(0, 5)
                    
                    PyImGui.push_item_width(100)
                    index = ImGui.input_int("##BagRange", self.bag_index)  
                    PyImGui.pop_item_width()
                            
                    if index > len(self.bag_names) - 1:
                        index = len(self.bag_names) - 1
                    elif index < 0:
                        index = 0
                    
                    if index != self.bag_index:
                        self.bag_index = index
                        self.action_summary = None
                    
                    bag_range = self.bag_ranges[self.bag_names[self.bag_index]]       
                    PyImGui.same_line(0, 5)
                    
                    self.inventory_view = ImGui.checkbox("##Inventory View", self.inventory_view)
                    ImGui.show_tooltip("Show items in a grid view instead of a list view.")
                                    
                    if self.actions_timer.IsExpired() or self.action_summary is None:
                        if self.bag_names[self.bag_index] == "Merchant/Trader":
                            self.action_summary = inventory_handling.InventoryHandler().GetActions(item_ids=GLOBAL_CACHE.Trading.Merchant.GetOfferedItems() or GLOBAL_CACHE.Trading.Trader.GetOfferedItems() or GLOBAL_CACHE.Trading.Collector.GetOfferedItems() or GLOBAL_CACHE.Trading.Crafter.GetOfferedItems(),  preview=True)
                        else:
                            self.action_summary = inventory_handling.InventoryHandler().GetActions(start_bag=bag_range[0], end_bag=bag_range[1],  preview=True)
                            
                        self.actions_timer.Reset()
                    
                    ImGui.separator()
                    child_size = PyImGui.get_content_region_avail()
                    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.CellPadding, 2, 2)
                    if self.inventory_view: 
                        if self.action_summary and self.action_summary.cached_inventory and self.inventory_coords: 
                            inventory_width = self.inventory_coords.right - self.inventory_coords.left
                            columns = math.floor((inventory_width - 24) // 37) if self.bag_index == 0 else 5
                            rows = math.ceil(len(self.action_summary.cached_inventory) / columns)
                            
                            if PyImGui.is_rect_visible(0, 20):
                                if ImGui.begin_table("Inventory Debug Table#InvView", columns, PyImGui.TableFlags.NoBordersInBody , child_size[0], child_size[1]):
                                    remaining_size = PyImGui.get_content_region_avail()
                                    button_width = math.floor(remaining_size[0] / columns) - 3                           
                                    button_height = math.floor((child_size[1] - 45) / rows)
                                    
                                    PyImGui.table_next_row()
                                    
                                    for i, item in enumerate(self.action_summary.cached_inventory):
                                        PyImGui.table_next_column()     
                                        self.draw_debug_item(i, item, button_width, button_height)   
                                        
                                            
                                ImGui.end_table()
                    else:
                        if self.action_summary and self.action_summary.cached_inventory: 
                            remaining_size = PyImGui.get_content_region_avail()
                            columns = math.floor(remaining_size[0] // 125)
                            
                            if PyImGui.is_rect_visible(0, 20):
                                if ImGui.begin_table("Inventory Debug Table##NoInvView", columns, PyImGui.TableFlags.ScrollY, remaining_size[0], child_size[1]):
                                    remaining_size = PyImGui.get_content_region_avail()
                                    button_width = math.floor(remaining_size[0] / columns) - 8
                                    button_height = 90
                                    
                                    PyImGui.table_next_row()
                                    
                                    for i, item in enumerate(self.action_summary.cached_inventory):
                                        PyImGui.table_next_column()     
                                        self.draw_debug_item(i, item, button_width, button_height)   
                                        
                                            
                                ImGui.end_table()
                    PyImGui.pop_style_var(1)
            
            ImGui.end_child()
            

            ImGui.end_tab_item()

    def draw_prices_tab(self):
        if ImGui.begin_tab_item("Prices"):
            tab_size = PyImGui.get_content_region_avail()
            child_width = (tab_size[0] - 10) / 2
            
            ImGui.begin_child("DataCollectorMaterialsChild", (child_width, tab_size[1]), True, PyImGui.WindowFlags.NoFlag)
            
            remaining_size = PyImGui.get_content_region_avail()
            if ImGui.button("Get Material Prices", remaining_size[0], 0):
                ConsoleLog(
                    "LootEx",
                    "Fetching material prices from the wiki...",
                    Console.MessageType.Info,
                )
                
                def assign_material_price(item_id, price):
                    if not self.settings.profile:
                        return
                                        
                    item = cache.Cached_Item(item_id)
                    if not item.material:
                        return
                    
                    ConsoleLog(
                        "LootEx",
                        f"Assigned price {utility.Util.format_currency(price)} to material {item.material.name} (Item ID: {item_id})",
                        Console.MessageType.Info,
                    )
                    item.material.vendor_value = price
                    item.material.vendor_updated = datetime.now()
                    
                    self.data.SaveMaterials()
                
                item_ids = Trading.Trader.GetOfferedItems()
                price_check_mgr = price_check.PriceCheckManager()
                price_check_mgr.request_prices(item_ids, assign_material_price)
            
            if PyImGui.is_rect_visible(0, 20):
                ImGui.begin_table("DataCollectorMaterialsTable", 3, PyImGui.TableFlags.ScrollY | PyImGui.TableFlags.NoBordersInBody, 0, 0)
                PyImGui.table_setup_column("Icon", PyImGui.TableColumnFlags.WidthFixed, 30)
                PyImGui.table_setup_column("Material")
                PyImGui.table_setup_column("Price")
                # PyImGui.table_headers_row()
                
                PyImGui.table_next_row()
                for material in self.data.Materials.values():
                    PyImGui.table_next_column()
                    ImGui.image(material.texture_file, (24, 24))
                    PyImGui.table_next_column()
                    if material.material_type is MaterialType.Common:
                        ImGui.text_aligned(f"{material.name} (10)", height=24, alignment=Alignment.MidLeft)
                    else:
                        ImGui.text_aligned(material.name, height=24, alignment=Alignment.MidLeft)
                        
                    PyImGui.table_next_column()
                    price_str = utility.Util.format_currency(material.vendor_value) if material.vendor_value is not None else "N/A"
                        
                    ImGui.text_aligned(price_str, height=24, alignment=Alignment.MidLeft)
                    
                    if PyImGui.is_item_hovered():
                        ImGui.show_tooltip("Last Checked: " + utility.Util.format_custom_time_ago(datetime.now() - material.vendor_updated) if material.vendor_updated else "Never Updated")

                # for material in self.data.Rare_Materials.values():
                #     PyImGui.table_next_row()
                #     PyImGui.table_next_column()
                #     ImGui.text(material.name)
                #     PyImGui.table_next_column()
                #     if material.vendor_value is not None:
                #         ImGui.text(utility.Util.format_currency(material.vendor_value))
                #     else:
                #         ImGui.text("N/A")
                #     ImGui.show_tooltip("Last Checked: " + utility.Util.format_time_ago(datetime.now() - material.vendor_updated) if material.vendor_updated else "Never Updated")
                        
                ImGui.end_table()
            
            
            ImGui.end_child()
            ImGui.end_tab_item()
        pass
    
    def draw_delete_profile_popup(self):

        if self.settings.profile is None:
            return

        if self.show_delete_profile_popup:
            PyImGui.open_popup("Delete Profile")

        if ImGui.begin_popup("Delete Profile"):
            ImGui.text(
                f"Are you sure you want to delete the profile '{self.settings.profile.name}'?")
            ImGui.separator()

            if ImGui.button("Yes", 100, 0):
                profile_names = [profile.name for profile in self.settings.profiles]
                profile_index = profile_names.index(self.settings.profile.name) if self.settings.profile else None
                
                if profile_index is None:
                    self.show_delete_profile_popup = False
                    PyImGui.close_current_popup()
                    return
                            
                self.settings.profiles.pop(profile_index)

                self.settings.SetProfile(self.settings.profiles[0].name if self.settings.profiles else None)
                self.settings.save()
                self.show_delete_profile_popup = False
                PyImGui.close_current_popup()

            PyImGui.same_line(0, 5)

            if ImGui.button("No", 100, 0):
                self.show_delete_profile_popup = False
                PyImGui.close_current_popup()

            ImGui.end_popup()

        if PyImGui.is_mouse_clicked(0) and not PyImGui.is_item_hovered():
            if self.show_delete_profile_popup:
                PyImGui.close_current_popup()
                self.show_delete_profile_popup = False

    def draw_profiles_popup(self):
        if self.show_add_profile_popup:
            PyImGui.open_popup("Add Profile")

        if ImGui.begin_popup("Add Profile"):
            ImGui.text("Please enter a name for the new profile:")
            ImGui.separator()

            profile_exists = self.new_profile_name == "" or any(
                profile.name.lower() == self.new_profile_name.lower() for profile in self.settings.profiles
            )

            if profile_exists:
                PyImGui.push_style_color(
                    PyImGui.ImGuiCol.Text, Utils.ColorToTuple(
                        Utils.RGBToColor(255, 0, 0, 255))
                )

            profile_name_input = ImGui.input_text(
                "##NewProfileName", self.new_profile_name)
            if profile_name_input is not None and profile_name_input != self.new_profile_name:
                self.new_profile_name = profile_name_input

            if profile_exists:
                PyImGui.pop_style_color(1)
                PyImGui.push_style_color(
                    PyImGui.ImGuiCol.Text, Utils.ColorToTuple(
                        Utils.RGBToColor(255, 255, 255, 120))
                )
                PyImGui.push_style_color(
                    PyImGui.ImGuiCol.Button, Utils.ColorToTuple(
                        Utils.RGBToColor(26, 38, 51, 125))
                )
                PyImGui.push_style_color(
                    PyImGui.ImGuiCol.ButtonHovered, Utils.ColorToTuple(
                        Utils.RGBToColor(26, 38, 51, 125))
                )
                PyImGui.push_style_color(
                    PyImGui.ImGuiCol.ButtonActive, Utils.ColorToTuple(
                        Utils.RGBToColor(26, 38, 51, 125))
                )

            PyImGui.same_line(0, 5)

            if ImGui.button("Create", 100, 0) and not profile_exists:
                if self.new_profile_name != "" and not profile_exists:
                    if self.settings.profile:
                        self.settings.profile.save()

                    new_profile = Profile(self.new_profile_name)
                    new_profile.save()
                    
                    self.settings.profiles.append(new_profile)
                    self.settings.SetProfile(new_profile.name)
                    
                    self.settings.save()

                    self.new_profile_name = ""
                    self.show_add_profile_popup = False
                    PyImGui.close_current_popup()
                else:
                    ConsoleLog("LootEx", "Profile name already exists!",
                            Console.MessageType.Error)

            if profile_exists:
                PyImGui.pop_style_color(4)
                PyImGui.push_style_color(
                    PyImGui.ImGuiCol.Text, Utils.ColorToTuple(
                        Utils.RGBToColor(255, 0, 0, 255))
                )
                ImGui.text("Profile name already exists!")
                PyImGui.pop_style_color(1)

            ImGui.end_popup()

        if PyImGui.is_mouse_clicked(0) and not PyImGui.is_item_hovered():
            if self.show_add_profile_popup:
                PyImGui.close_current_popup()
                self.show_add_profile_popup = False

    def draw_general_settings(self):
        style = ImGui.get_style()
        
        if ImGui.begin_tab_item("General"):
            tab_size = PyImGui.get_content_region_avail()
            dye_section_width = 250

            if ImGui.begin_child("GeneralSettingsChild", (tab_size[0] - dye_section_width - 5, tab_size[1]), True, PyImGui.WindowFlags.NoFlag) and self.settings.profile:
                subtab_size = PyImGui.get_content_region_avail()

                ImGui.text("General")
                ImGui.separator()
                if ImGui.begin_child("GeneralSettingsChildInner", (subtab_size[0], 110), True, PyImGui.WindowFlags.NoBackground):                    
                    # deposit_full_stacks = ImGui.checkbox("Deposit Full Stacks", self.settings.profile.deposit_full_stacks)
                    # if deposit_full_stacks != self.settings.profile.deposit_full_stacks:
                    #     self.settings.profile.deposit_full_stacks = deposit_full_stacks
                    #     self.settings.profile.save()
                    # ImGui.show_tooltip("When a full stack of items is found in the inventory, it will be deposited automatically.")
                    
                    xunlai_tabs = [utility.Util.reformat_string(tab.name) for tab in XUNLAI_STORAGE]
                    
                    max_xunlai_storage = ImGui.combo("Max Xunlai Tab", self.settings.max_xunlai_storage.value - Bag_enum.Storage_1.value, xunlai_tabs)
                    if max_xunlai_storage != self.settings.max_xunlai_storage.value - Bag_enum.Storage_1.value:
                        self.settings.max_xunlai_storage = Bag_enum(Bag_enum.Storage_1.value + max_xunlai_storage)
                        self.settings.profile.save()
                        
                    polling_interval = ImGui.slider_float("Polling Interval (sec)", self.settings.profile.polling_interval, 0.1, 5)
                    
                    if polling_interval != self.settings.profile.polling_interval:
                        self.settings.profile.polling_interval = polling_interval
                        inventory_handling.InventoryHandler().SetPollingInterval(polling_interval)
                        self.settings.profile.save()
                    ImGui.show_tooltip(f"Polling Interval: {polling_interval:.2f} seconds")
                    
                    loot_range = ImGui.slider_int("Loot Range", self.settings.profile.loot_range, 125, 5000)
                    
                    if loot_range != self.settings.profile.loot_range:
                        self.settings.profile.loot_range = loot_range
                        loot_handling.LootHandler().SetLootRange(loot_range)
                        self.settings.profile.save()

                    ImGui.show_tooltip(f"Loot Range: {loot_range} units")
                
                        
                ImGui.end_child()
                
                
                ImGui.text("Merchant Settings")
                def draw_hint():
                    ImGui.text_wrapped("These settings control the items that are automatically bought from merchants when opening a merchant window.")
                    ImGui.text_wrapped("Before buying items, LootEx will check your stash for these items and move them to your inventory if they are present.\n"+
                                 "If the item is not present in your stash, it will be bought from the merchant.\n")
                
                PyImGui.same_line(0, 5)
                self.draw_info_icon(draw_action=draw_hint, width=500)
                                        
                ImGui.separator()
                if ImGui.begin_child("GeneralSettings_Merchant", (subtab_size[0], 150), True, PyImGui.WindowFlags.NoBackground) and self.settings.profile:
                    self._input_int_setting("Identification Kits", self.settings.profile.identification_kits, self.merchant_item_textures["Superior Identification Kit"])
                    self._input_int_setting("Salvage Kits", self.settings.profile.salvage_kits, self.merchant_item_textures["Salvage Kit"])
                    self._input_int_setting("Expert Salvage Kits", self.settings.profile.expert_salvage_kits, self.merchant_item_textures["Expert Salvage Kit"])
                    self._input_int_setting("Lockpicks", self.settings.profile.lockpicks, self.merchant_item_textures["Lockpick"])

                ImGui.end_child()
                
                ImGui.text("Nick Settings")
                ImGui.separator()
                
                if ImGui.begin_child("GeneralSettings_Nick", (subtab_size[0], 0), True, PyImGui.WindowFlags.NoBackground) and self.settings.profile:
                    action_info = self.action_infos.get(self.settings.profile.nick_action, None)
                    action_texture = action_info.icon if action_info else None
                    height = 24
                    if action_texture:
                        ImGui.DrawTexture(action_texture, height, height)
                    else:
                        PyImGui.dummy(height, height)
                    PyImGui.same_line(0, 5)   
                    
                    current_action_index = self.keep_actions.index(self.settings.profile.nick_action) if self.settings.profile.nick_action in self.keep_actions else 0
                    action_index = ImGui.combo("Nick Action", current_action_index, self.keep_action_names)
                    
                    if action_index != current_action_index:
                        self.settings.profile.nick_action = self.keep_actions[action_index]
                        self.settings.profile.save()
                        
                    self._slider_int_setting("Nick Weeks to Keep", self.settings.profile.nick_weeks_to_keep, self.nick_textures["Gift of the Traveler"], -1, 137)                    
                    self._slider_int_setting("Nick Items to Keep", self.settings.profile.nick_items_to_keep, self.nick_textures["Red Iris Flower"], 0, 500)    
                    
                    PyImGui.spacing()
                     
                    height = 20                    
                    nick_gradient = GUI.get_gradient_colors((0.5, 1, 0, 0.5), (1, 0, 0, 0.5), self.settings.profile.nick_weeks_to_keep + 1)
                    nick_item_size = PyImGui.get_content_region_avail()
                    
                    if PyImGui.is_rect_visible(1, height + 4):
                        ImGui.begin_table("NickItemsTable", 3, PyImGui.TableFlags.ScrollY | PyImGui.TableFlags.BordersOuterV | PyImGui.TableFlags.BordersOuterH, nick_item_size[0], nick_item_size[1])    
                        # PyImGui.table_setup_column("Index", PyImGui.TableColumnFlags.WidthFixed, 25)
                        PyImGui.table_setup_column("Icon", PyImGui.TableColumnFlags.WidthFixed, 20)
                        PyImGui.table_setup_column("Name")
                        PyImGui.table_setup_column("Weeks Until Next Nick", PyImGui.TableColumnFlags.WidthFixed, 85)   
                        
                        for i, nick_item in enumerate(self.data.Nick_Cycle):
                             
                            if nick_item.weeks_until_next_nick is None:
                                # ConsoleLog("LootEx", f"Nick item '{nick_item.name}' has no 'weeks_until_next_nick' value set! But next week is {nick_item.next_nick_week}", Console.MessageType.Warning)
                                continue

                            if nick_item.weeks_until_next_nick > 0 and nick_item.weeks_until_next_nick > self.settings.profile.nick_weeks_to_keep:
                                continue
                            
                            # PyImGui.table_next_row()
                            if not PyImGui.is_rect_visible(1, height):
                                PyImGui.dummy(1, height)
                                PyImGui.table_next_column()
                                PyImGui.table_next_column()
                                PyImGui.table_next_column()
                                continue
                            
                            # PyImGui.table_next_column()
                            # ImGui.text(f"{i}.")
                            # hovered = PyImGui.is_item_hovered()
                            
                            PyImGui.table_next_column()
                            if nick_item.inventory_icon:
                                ImGui.DrawTexture(
                                    nick_item.texture_file, height, height)
                            else:
                                PyImGui.dummy(height, height)    
                                                        
                            hovered = PyImGui.is_item_hovered()
                            
                            PyImGui.table_next_column()                                                    
                            GUI.vertical_centered_text(nick_item.name, None, height)
                            hovered = PyImGui.is_item_hovered() or hovered
                            
                            
                            color = (0, 1, 0, 0.9) if nick_item.weeks_until_next_nick == 0 else \
                                    (0, 1, 0, 0.7) if nick_item.weeks_until_next_nick == 1 else \
                                    nick_gradient[nick_item.weeks_until_next_nick] if nick_item.weeks_until_next_nick < len(nick_gradient) else (1, 1, 1, 1) 

                            PyImGui.table_next_column()
                                                   
                            GUI.vertical_centered_text("current week" if nick_item.weeks_until_next_nick == 0 else f"next week"  if nick_item.weeks_until_next_nick == 1 else f"{nick_item.weeks_until_next_nick} weeks", None, height, color=color)
                            # ImGui.text_colored(
                            #     "current week" if nick_item.weeks_until_next_nick == 0 else f"next week"  if nick_item.weeks_until_next_nick == 1 else f"{nick_item.weeks_until_next_nick} weeks" , 
                            #     color
                            # )
                            hovered = PyImGui.is_item_hovered() or hovered
                            
                            if hovered:
                                PyImGui.set_next_window_size(400, 0)
                                ImGui.begin_tooltip()
                                
                                self.draw_item_header(item_info=nick_item, border=False, image_size=50)

                                ImGui.separator()
                                ImGui.text(f"Nicholas the Traveler collects these items in: {nick_item.weeks_until_next_nick} weeks")                
                                ImGui.text(nick_item.acquisition)                
                                ImGui.end_tooltip()
                                
                        ImGui.end_table()           
                        
                ImGui.end_child()
                

            ImGui.end_child()

            PyImGui.same_line(0, 5)

            if ImGui.begin_child("Dyes", (dye_section_width, tab_size[1]), True, PyImGui.WindowFlags.NoFlag) and self.settings.profile:
                ImGui.text("Dyes")
                ImGui.text_wrapped(
                    "Select the dyes you want to pick up and stash.")
                ImGui.separator()

                if ImGui.begin_child("DyesSelection", (dye_section_width - 20, 0), True, PyImGui.WindowFlags.NoFlag | PyImGui.WindowFlags.NoBackground):
                    style = ImGui.get_style()
                    
                    for dye in DyeColor:
                        if dye != DyeColor.NoColor:
                            file_path = self.dye_textures[dye]
                            if dye not in self.settings.profile.dyes:
                                self.settings.profile.dyes[dye] = False

                            color = utility.Util.GetDyeColor(
                                dye, 205 if self.settings.profile.dyes[dye] else 125)
                            PyImGui.push_style_color(
                                PyImGui.ImGuiCol.FrameBg, Utils.ColorToTuple(color))
                            
                            hover_color = utility.Util.GetDyeColor(dye)
                            PyImGui.push_style_color(
                                PyImGui.ImGuiCol.FrameBgHovered, Utils.ColorToTuple(hover_color))                            
                            UI.ImageToggleXX(file_path, 16.25, 20, 
                                           self.settings.profile.dyes[dye]
                            )
                            
                            PyImGui.same_line(0, 5)
                            
                            if style.Theme == Style.StyleTheme.Guild_Wars:
                                c = Utils.ColorToTuple(color)
                                style.CheckMark.push_color((int(c[0] * 255), int(c[1] * 255), int(c[2] * 255), int(c[3] * 255)))

                            selected = ImGui.checkbox(
                                dye.name, self.settings.profile.dyes[dye])

                            if style.Theme == Style.StyleTheme.Guild_Wars:
                                style.CheckMark.pop_color()

                            if self.settings.profile.dyes[dye] != selected:
                                self.settings.profile.dyes[dye] = selected
                                self.settings.profile.save()

                            PyImGui.pop_style_color(2)
                            ImGui.show_tooltip("Dye: " + dye.name)

                ImGui.end_child()

            ImGui.end_child()

            ImGui.end_tab_item()

    def _input_int_setting(self, label, current_value, item_textures_path=None):
        if self.settings.profile is None:
            return

        style = ImGui.get_style()
        PyImGui.push_item_width(150)
        new_value = ImGui.input_int("##" + label, current_value)
        PyImGui.pop_item_width()
        if new_value != current_value:
            setattr(self.settings.profile,
                    label.replace(" ", "_").lower(), new_value)
            self.settings.profile.save()

        rect_min = PyImGui.get_item_rect_min()
        rect_max = PyImGui.get_item_rect_max()
        height = rect_max[1] - rect_min[1]

        PyImGui.same_line(0, (0 if style.Theme == Style.StyleTheme.Guild_Wars else 5))
        if item_textures_path and os.path.exists(item_textures_path):
            ImGui.DrawTexture(
                item_textures_path, height, height)
        else:
            PyImGui.dummy(int(height), int(height))
        
        PyImGui.same_line(0, 5)
        ImGui.text(label)
        
    def _slider_int_setting(self, label, current_value, item_textures_path=None, min_value=0, max_value=100):
        if self.settings.profile is None:
            return

        PyImGui.push_item_width(150)
        new_value = ImGui.slider_int("##" + label, current_value, min_value, max_value)
        PyImGui.pop_item_width()
        if new_value != current_value:
            setattr(self.settings.profile,
                    label.replace(" ", "_").lower(), new_value)
            self.settings.profile.save()
            
        PyImGui.same_line(0, 5)
        if item_textures_path and os.path.exists(item_textures_path):
            ImGui.DrawTexture(
                item_textures_path, 16, 16)
        else:
            PyImGui.dummy(16, 16)
        
        PyImGui.same_line(0, 5)
        ImGui.text(label)

    def draw_by_item_type(self):
        style = ImGui.get_style()
        if ImGui.begin_tab_item("By Item Type") and self.settings.profile:
            # Get size of the tab
            tab_size = PyImGui.get_content_region_avail()

            # Left panel: Loot Filter Selection
            if ImGui.begin_child("filter_selection_child", (tab_size[0] * 0.3, tab_size[1]), True, PyImGui.WindowFlags.NoFlag):
                ImGui.text("Filter Selection")
                
                def draw_hint():
                    ImGui.text_wrapped(
                        "Add and configure filters to manage how item groups are handled in your inventory.\n")
                    
                    PyImGui.spacing()                    
                    ImGui.text_wrapped(
                        "- Filters are checked in the order they are listed, and the first matching filter will determine the action taken on an item. To adjust the order, use the up and down arrows next to each filter.\n" +
                        "- You can add, remove, and reorder filters to customize your inventory management.\n" +
                        "- To add a new filter, click the 'Add Filter' button below.")
                    
                    PyImGui.spacing()
                    ImGui.separator()
                    ImGui.text_wrapped("Salvage Filters")
                    PyImGui.spacing()
                    ImGui.text_wrapped(
                        "Salvage filters will only salvage items that contain the selected material to avoid getting too many unwanted materials.\n" +
                        "Adding another filter with the same criteria but with a different action will handle the items that do not match the first filter's criteria.")
                    
                PyImGui.same_line((tab_size[0] * 0.3) - 35 , 5)
                self.draw_info_icon(draw_action=draw_hint, width=500)
                
                ImGui.separator()
                subtab_size = PyImGui.get_content_region_avail()

                if ImGui.begin_child("filter_selection_child", (subtab_size[0], subtab_size[1] - 30), True, PyImGui.WindowFlags.NoBackground):
                    selection_size = PyImGui.get_content_region_avail()
                    button_size = (16, 16)
                    if self.settings.profile and self.settings.profile.filters:
                        for i in range(len(self.settings.profile.filters)):
                            filter = self.settings.profile.filters[i]
                            
                            if PyImGui.selectable(f"{i+1}. "+ filter.name, filter == self.settings.selected_filter, PyImGui.SelectableFlags.NoFlag, (selection_size[0] - 37, 0)):
                                self.settings.selected_filter = filter
                            
                            if PyImGui.is_item_hovered():
                                i = self.filter_actions.index(filter.action) if filter.action in self.filter_actions else 0
                                name = self.filter_action_names[i]
                                ImGui.show_tooltip(name)
                            
                            PyImGui.same_line(0, 10)
                            
                            screen_cursor = PyImGui.get_cursor_screen_pos()
                            down_rect = (screen_cursor[0], screen_cursor[1], button_size[0], button_size[1])
                            down_hovered = GUI.is_mouse_in_rect(down_rect)
                            is_clicked = PyImGui.is_mouse_clicked(0) and down_hovered
                            state = texture_map.TextureState.Active if is_clicked else texture_map.TextureState.Hovered if down_hovered else texture_map.TextureState.Normal
                            texture_map.CoreTextures.Down_Arrows.value.draw(size=button_size, state=state)
                            # ImGui.DrawTexture(texture_path=texture.value, width=button_size[0], height=button_size[1])
                            
                            if is_clicked:
                                if i < len(self.settings.profile.filters) - 1:
                                    self.settings.profile.move_filter(filter, i + 1)
                                    self.settings.profile.save()

                            PyImGui.same_line(0, 0)
                            
                            screen_cursor = PyImGui.get_cursor_screen_pos()
                            up_rect = (screen_cursor[0], screen_cursor[1], button_size[0], button_size[1])
                            up_hovered = GUI.is_mouse_in_rect(up_rect)
                            is_clicked = PyImGui.is_mouse_clicked(0) and up_hovered
                            state = texture_map.TextureState.Active if is_clicked else texture_map.TextureState.Hovered if up_hovered else texture_map.TextureState.Normal
                            texture_map.CoreTextures.Up_Arrows.value.draw(size=button_size, state=state)
                            
                            if is_clicked:
                                if i > 0:                                    
                                    self.settings.profile.move_filter(filter, i - 1)
                                    self.settings.profile.save()
                            
                ImGui.end_child()

                if ImGui.button("Add Filter", subtab_size[0]):
                    self.show_add_filter_popup = not self.show_add_filter_popup
                    if self.show_add_filter_popup:
                        PyImGui.open_popup("Add Filter")

            ImGui.end_child()

            PyImGui.same_line(tab_size[0] * 0.3 + 20, 0)

            # Right panel: Loot Filter Details
            if ImGui.begin_child("filter_child", (tab_size[0] - (tab_size[0] * 0.3) - 10, 0), self.settings.selected_filter is None, PyImGui.WindowFlags.NoFlag):
                if self.settings.selected_filter:
                    filter = self.settings.selected_filter

                    if ImGui.begin_child("filter_name_child", (0, 45), True, PyImGui.WindowFlags.NoFlag): 
                        PyImGui.push_item_width(tab_size[0] - (tab_size[0] * 0.3) - 63)
                        # Edit filter name
                        name = ImGui.input_text(
                            "##name_edit", filter.name)
                        PyImGui.pop_item_width()
                        if name and name != filter.name:
                            filter.name = name
                            self.settings.profile.save()

                        PyImGui.same_line(0, 5)

                        # Delete filter button
                        if GUI.image_button(texture_map.CoreTextures.UI_Destroy.value, (20, 20)):
                            self.settings.profile.remove_filter(
                                filter)
                            self.settings.profile.save()
                            self.settings.selected_filter = self.settings.profile.filters[
                                0] if self.settings.profile.filters else None
                            self.show_add_filter_popup = False
                            PyImGui.close_current_popup()               
                    ImGui.end_child()
                        
                    # Filter actions
                    remaining_size = PyImGui.get_content_region_avail()
                    height = min(self.action_heights.get(filter.action, 45), remaining_size[0])
                    if ImGui.begin_child("filter_actions", (0, height), True, PyImGui.WindowFlags.NoFlag):                         
                        if filter.action:
                            action_info = self.action_infos.get(filter.action, None)
                            action_texture = action_info.icon if action_info else None
                            height = 24
                            if action_texture:
                                ImGui.DrawTexture(action_texture, height, height)
                            else:
                                PyImGui.dummy(height, height)
                            PyImGui.same_line(0, 5)            
                            PyImGui.push_item_width(PyImGui.get_content_region_avail()[0])
                            action = ImGui.combo("##RuleAction", self.item_actions.index(
                                filter.action) if filter.action in self.item_actions else 0, self.item_action_names)
                            
                            PyImGui.pop_item_width()
                            
                            if self.item_actions[action] != filter.action:
                                filter.action = self.item_actions[action]
                                self.settings.profile.save()
                            
                            ImGui.show_tooltip((f"{self.action_infos.get_name(ItemAction.Loot)} and " if filter.action not in [ItemAction.NONE, ItemAction.Loot, ItemAction.Destroy] else "") + f"{self.action_infos.get_name(filter.action)}")
                                        
                        def draw_salvage_options():
                            if not self.settings.profile:
                                return
                            
                            ImGui.separator()                            
                            PyImGui.push_item_width(100)
                            value = PyImGui.slider_int(
                                "Max Item Value##salvage_threshold", filter.salvage_item_max_vendorvalue, 0, 1500)
                            
                            PyImGui.pop_item_width()
                            ImGui.show_tooltip(
                                "Items with a vendor value below this threshold will be salvaged.\n" +
                                "This is useful to avoid salvaging items that are worth more than the materials they yield.")
                            
                            if value != filter.salvage_item_max_vendorvalue:
                                filter.salvage_item_max_vendorvalue = value
                                self.settings.profile.save()
                                                    
                            ImGui.text_wrapped(f"Salvage only items which are worth less than {utility.Util.format_currency(filter.salvage_item_max_vendorvalue)} and which salvage for")
                            
                            width, height = PyImGui.get_content_region_avail()
                            width = width - 50
                            item_width = 36
                            columns = max(1, math.floor(width / item_width))
                            
                            has_common_materials = len(self.data.Common_Materials) > 0 if filter.action in [ItemAction.Salvage, ItemAction.Salvage_Common_Materials] else False
                            has_rare_materials = len(self.data.Rare_Materials) > 0 if filter.action in [ItemAction.Salvage, ItemAction.Salvage_Rare_Materials] else False
                            
                            rows = (math.ceil(len(self.data.Common_Materials) / columns) if has_common_materials else 0) + (math.ceil(len(self.data.Rare_Materials) / columns) if has_rare_materials else 0)
                                                            
                            self.action_heights[ItemAction.Salvage_Rare_Materials] = (rows * item_width) + 123 + 8
                            self.action_heights[ItemAction.Salvage_Common_Materials] = (rows * item_width) + 125 + 8
                            self.action_heights[ItemAction.Salvage] = (rows * item_width) + 123 + 8 + 20
                            
                            ImGui.begin_child("salvage_materials", (0, 0), True, PyImGui.WindowFlags.NoFlag)      
                                                                                        
                            if PyImGui.is_rect_visible(0, self.action_heights[ItemAction.Salvage] - 20):
                                style.CellPadding.push_style_var(0, 2)
                                ImGui.begin_table("salvage_materials_table", columns, PyImGui.TableFlags.ScrollY, 0, 0)                                
                                if filter.action == ItemAction.Salvage or filter.action == ItemAction.Salvage_Common_Materials:
                                    for material in self.data.Common_Materials.values():
                                        PyImGui.table_next_column()
                                        changed, selected = self.draw_material_selectable(material, filter.materials.get(material.model_id, False))
                                    
                                        if changed:
                                            if self.py_io.key_ctrl:
                                                for mat in self.data.Common_Materials.values():
                                                    if not selected:
                                                        if mat.model_id in filter.materials:
                                                            del filter.materials[mat.model_id]
                                                    else:
                                                        filter.materials[mat.model_id] = selected
                                                            
                                            else:
                                                if not selected:
                                                    if material.model_id in filter.materials:
                                                        del filter.materials[material.model_id]
                                                else:
                                                    filter.materials[material.model_id] = selected
                                            
                                            self.settings.profile.save()
                                    
                                    PyImGui.table_next_row()
                                
                                if filter.action == ItemAction.Salvage:
                                    ypos = PyImGui.get_cursor_pos_y() + 2
                                    for _ in range(columns):
                                        PyImGui.table_next_column()
                                        PyImGui.set_cursor_pos_y(ypos)
                                        ImGui.separator()
                                    
                                if filter.action == ItemAction.Salvage_Rare_Materials or filter.action == ItemAction.Salvage:    
                                    for material in self.data.Rare_Materials.values():
                                        PyImGui.table_next_column()
                                        changed, selected = self.draw_material_selectable(material, filter.materials.get(material.model_id, False))
                                    
                                        if changed:
                                            if self.py_io.key_ctrl:
                                                for mat in self.data.Rare_Materials.values():
                                                    if not selected:
                                                        if mat.model_id in filter.materials:
                                                            del filter.materials[mat.model_id]
                                                    else:
                                                        filter.materials[mat.model_id] = selected
                                                            
                                            else:
                                                if not selected:
                                                    if material.model_id in filter.materials:
                                                        del filter.materials[material.model_id]
                                                else:
                                                    filter.materials[material.model_id] = selected
                                            
                                            self.settings.profile.save()
                                    
                                ImGui.end_table()
                                style.CellPadding.pop_style_var()
                            ImGui.end_child()
                                
                        match filter.action:
                            case ItemAction.Salvage:
                                draw_salvage_options()                                        
                                pass
                            case ItemAction.Salvage_Common_Materials:
                                draw_salvage_options()                                        
                                pass
                            case ItemAction.Salvage_Rare_Materials:
                                draw_salvage_options()                                        
                                pass
                            
                            case ItemAction.Stash:                                        
                                if filter.action == ItemAction.Stash:
                                    PyImGui.indent(25)
                                    full_stack_only = ImGui.checkbox("Only stash full stacks", filter.full_stack_only)
                                    if full_stack_only != filter.full_stack_only:
                                        filter.full_stack_only = full_stack_only
                                        self.settings.profile.save()
                            
                            case _:
                                pass

                    ImGui.end_child()

                    # Filter item types
                    sub_subtab_size = PyImGui.get_content_region_avail()
                    rarity_width = 60 if sub_subtab_size[1] > 268 else 80
                    if ImGui.begin_child("loot_item_types_filter_table", (sub_subtab_size[0] - rarity_width - 5, 0), True, PyImGui.WindowFlags.NoFlag) and PyImGui.is_rect_visible(0, 20):  
                        ImGui.text("Item Types")
                        ImGui.separator()
                        width, height = PyImGui.get_content_region_avail()
                        width = width
                        item_width = 48
                        columns = max(1, math.floor(width / item_width))

                        if PyImGui.is_rect_visible(1, 20):
                            style.CellPadding.push_style_var(0, 2)

                            ImGui.begin_table(
                                "filter_table", columns, PyImGui.TableFlags.ScrollY)
                            for col in range(columns):
                                PyImGui.table_setup_column(f"Column {col + 1}", PyImGui.TableColumnFlags.WidthFixed, item_width)

                            PyImGui.table_next_column()

                            for item_type in self.action_item_types_map[filter.action]:
                                if item_type in self.item_type_textures:
                                    if filter.item_types[item_type] is None:
                                        continue

                                    changed, filter.item_types[item_type] = self.draw_item_type_selectable(
                                        item_type, filter.item_types[item_type])
                                    PyImGui.table_next_column()
                                     
                                    if changed:
                                        if self.py_io.key_ctrl:
                                            selected = filter.item_types[item_type]
                                            # Toggle all item types
                                            for it in self.action_item_types_map[filter.action] or ItemType:
                                                if it in filter.item_types:
                                                    filter.item_types[it] = selected
                                                    
                                        self.settings.profile.save()
                                        
                            ImGui.end_table()
                            style.CellPadding.pop_style_var()

                    ImGui.end_child()

                    PyImGui.same_line(0, 5)

                    # Filter rarities
                    if ImGui.begin_child("loot_rarity_filter_table", (0, 0), True, PyImGui.WindowFlags.NoFlag):
                        count = 0
                        # ConsoleLog("LootEx", PyImGui.get_content_region_max()[1])
                        
                        PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 5)
                        ImGui.text("Rarities")
                        
                        texture = self.item_type_textures[ItemType.Sword]
                        
                        # ImGui.separator()   
                        for rarity, selected in filter.rarities.items():  
                            factor = 52 / 64
                            skin_size = 42
                            frame_size = (skin_size * factor, skin_size)
                            PyImGui.set_cursor_pos_x(PyImGui.get_cursor_pos_x() + 3)
                            screen_cursor = PyImGui.get_cursor_screen_pos()
                            is_hovered = GUI.is_mouse_in_rect((screen_cursor[0], screen_cursor[1], frame_size[0], frame_size[1])) and PyImGui.is_window_hovered()
                            alpha = 255 if is_hovered else 225 if (selected) else 50
                            texture_alpha = 255 if is_hovered else 225 if (selected) else 100
                            frame_color =  GUI.get_rarity_rgba_color(rarity, texture_alpha) if selected else (100,100,100, texture_alpha)
                            texture_color =  (255 ,255,255 , texture_alpha) if selected else (100,100,100, 200 if is_hovered else 125 )
                            
                            # ImGui.begin_child(f"rarity_{rarity}", (frame_size[0], frame_size[1]), False, PyImGui.WindowFlags.NoFlag | PyImGui.WindowFlags.NoScrollWithMouse | PyImGui.WindowFlags.NoScrollbar)
                            
                            if is_hovered:
                                rect = (screen_cursor[0], screen_cursor[1], screen_cursor[0] + frame_size[0], screen_cursor[1] + frame_size[1])           
                                PyImGui.draw_list_add_rect_filled(rect[0], rect[1], rect[2], rect[3], Utils.RGBToColor(frame_color[0], frame_color[1], frame_color[2], 50), 1.0, 0)                                                     
                                                            
                            cursor = PyImGui.get_cursor_pos()
                            # PyImGui.set_cursor_pos(cursor[0] + (frame_size * count), cursor[1])
                            ImGui.DrawTextureExtended(texture_path=texture_map.CoreTextures.UI_Inventory_Slot.value, size=(frame_size[0], frame_size[1]), tint=frame_color)
                            PyImGui.set_cursor_pos(cursor[0], cursor[1] + ((frame_size[1] - skin_size) / 2))
                                                                  
                            ImGui.DrawTextureExtended(texture_path=texture, size=(skin_size, skin_size), tint=texture_color)
                            
                            if PyImGui.is_item_clicked(0) and is_hovered:                                
                                if self.py_io.key_ctrl:
                                    for r in filter.rarities.keys():
                                        filter.rarities[r] = not selected
                                else:
                                    filter.rarities[rarity] = not selected
                                    
                                self.settings.profile.save()
                            
                            if is_hovered:
                                ImGui.show_tooltip(f"Rarity: {rarity.name}")
                                
                            count += 1  
                            # PyImGui.same_line(10 + ((frame_size[0] + 2) * count), 0)
                                        
                    ImGui.end_child()

            ImGui.end_child()

            ImGui.end_tab_item()

            self.draw_add_filter_popup()

    def draw_add_filter_popup(self):
        if self.settings.profile is None:
            return

        if self.show_add_filter_popup:
            PyImGui.open_popup("Add Filter")

        if ImGui.begin_popup("Add Filter"):
            ImGui.text("Please enter a name for the new filter:")
            ImGui.separator()

            filter_exists = self.filter_name == "" or any(
                filter.name.lower() == self.filter_name.lower()
                for filter in self.settings.profile.filters
            )

            if filter_exists:
                PyImGui.push_style_color(
                    PyImGui.ImGuiCol.Text,
                    Utils.ColorToTuple(Utils.RGBToColor(255, 0, 0, 255)),
                )

            filter_name_input = ImGui.input_text("##NewFilterName", self.filter_name)
            if filter_name_input is not None and filter_name_input != self.filter_name:
                self.filter_name = filter_name_input

            if filter_exists:
                PyImGui.pop_style_color(1)
                PyImGui.push_style_color(
                    PyImGui.ImGuiCol.Text,
                    Utils.ColorToTuple(Utils.RGBToColor(255, 255, 255, 120)),
                )
                PyImGui.push_style_color(
                    PyImGui.ImGuiCol.Button,
                    Utils.ColorToTuple(Utils.RGBToColor(26, 38, 51, 125)),
                )
                PyImGui.push_style_color(
                    PyImGui.ImGuiCol.ButtonHovered,
                    Utils.ColorToTuple(Utils.RGBToColor(26, 38, 51, 125)),
                )
                PyImGui.push_style_color(
                    PyImGui.ImGuiCol.ButtonActive,
                    Utils.ColorToTuple(Utils.RGBToColor(26, 38, 51, 125)),
                )

            PyImGui.same_line(0, 5)

            if ImGui.button("Create", 100, 0) and not filter_exists:
                if self.filter_name != "" and not filter_exists:
                    self.settings.profile.add_filter(
                        Filter(self.filter_name)
                    )
                    self.settings.profile.save()

                    self.filter_name = ""
                    self.show_add_filter_popup = False
                    PyImGui.close_current_popup()
                else:
                    ConsoleLog(
                        "LootEx",
                        "Filter name already exists!",
                        Console.MessageType.Error,
                    )

            if filter_exists:
                PyImGui.pop_style_color(4)
                PyImGui.push_style_color(
                    PyImGui.ImGuiCol.Text,
                    Utils.ColorToTuple(Utils.RGBToColor(255, 0, 0, 255)),
                )
                ImGui.text("Filter name already exists!")
                PyImGui.pop_style_color(1)

            ImGui.end_popup()

        if PyImGui.is_mouse_clicked(0) and not PyImGui.is_item_hovered():
            if self.show_add_filter_popup:
                PyImGui.close_current_popup()
                self.show_add_filter_popup = False

    def draw_filter_popup(self):
        if self.filter_popup:
            PyImGui.open_popup("Filter Loot Items")

        if ImGui.begin_popup("Filter Loot Items"):
            
            remaining_size = PyImGui.get_content_region_avail()
            
            for filter in self.filters:
                if filter:
                    if PyImGui.selectable(filter.name, self.selected_filter == filter, PyImGui.SelectableFlags.NoFlag, (remaining_size[0], 0)):
                        self.selected_filter = filter
                        self.filter_items()
                        
                        self.filter_popup = False
                        PyImGui.close_current_popup()
        
            ImGui.end_popup()
        
        if PyImGui.is_mouse_clicked(0) and not PyImGui.is_item_hovered():
            if self.filter_popup:
                PyImGui.close_current_popup()
                self.filter_popup = False        
    
    #region By Skin Tab    
    def draw_rule_filter_popup(self):
        if self.rule_filter_popup:
            PyImGui.open_popup("Filter Rules")

        if ImGui.begin_popup("Filter Rules"):
            
            remaining_size = PyImGui.get_content_region_avail()
            
            for filter in self.rule_filters:
                if filter:
                    if PyImGui.selectable(filter.name, self.selected_rule_filter == filter, PyImGui.SelectableFlags.NoFlag, (remaining_size[0], 0)):
                        self.selected_rule_filter = filter
                        self.filter_rules()
                        
                        self.rule_filter_popup = False
                        PyImGui.close_current_popup()
        
            ImGui.end_popup()
        
        if PyImGui.is_mouse_clicked(0) and not PyImGui.is_item_hovered():
            if self.rule_filter_popup:
                PyImGui.close_current_popup()
                self.rule_filter_popup = False        
    
    def filter_rules(self):
        if not self.settings.profile:
            return
        
        self.selectable_rules = []
        search = self.rule_search.lower()
        
        for rule in self.settings.profile.skin_rules:
            if self.selected_rule_filter is None or self.selected_rule_filter.match(rule):
                if not search or \
                    search in rule.skin.lower() or \
                    any(search in str(model_id) for model_id in [
                            model_info.model_id for model_info in rule.models
                    ]):
                    
                    self.selectable_rules.append(SelectableWrapper(rule, self.selected_rule == rule))                

        pass
    
    def draw_selectable_rule(self, rule: skin_rule.SkinRule, is_selected: bool, is_hovered: bool = False) -> tuple[bool, bool]:
        size = 32        
        skin_size = size - 6        
        padding = (size - skin_size) / 2
        delete_clicked = False
        
        if PyImGui.is_rect_visible(1, size):
            if ImGui.begin_child(f"rule_{rule.skin}", (0, size), False, PyImGui.WindowFlags.NoFlag | PyImGui.WindowFlags.NoScrollWithMouse | PyImGui.WindowFlags.NoScrollbar):
                texture = os.path.join(self.item_textures_path, f"{rule.skin}")   
                remaining_size = PyImGui.get_content_region_avail()
                
                screen_cursor = PyImGui.get_cursor_screen_pos()   
                is_visible = PyImGui.is_rect_visible(10, 1)      
                is_hovered = GUI.is_mouse_in_rect((screen_cursor[0], screen_cursor[1], remaining_size[0], remaining_size[1])) and is_visible and PyImGui.is_window_hovered()
                
                if is_hovered:
                    PyImGui.draw_list_add_rect_filled(screen_cursor[0], screen_cursor[1], screen_cursor[0] + remaining_size[0], screen_cursor[1] + size, self.style.Hovered_Item.color_int, 1.0, 0)
                    PyImGui.draw_list_add_rect(screen_cursor[0], screen_cursor[1], screen_cursor[0] + remaining_size[0], screen_cursor[1] + size, self.style.Hovered_Item.color_int, 1.0, 0, 2.0)
                    
                if is_selected:
                    PyImGui.draw_list_add_rect_filled(screen_cursor[0], screen_cursor[1], screen_cursor[0] + remaining_size[0], screen_cursor[1] + size, self.style.Selected_Item.color_int, 1.0, 0)
                    PyImGui.draw_list_add_rect(screen_cursor[0], screen_cursor[1], screen_cursor[0] + remaining_size[0], screen_cursor[1] + size, self.style.Selected_Item.color_int, 1.0, 0, 2.0)
                
                cursor = PyImGui.get_cursor_pos()
                PyImGui.set_cursor_pos(cursor[0] + padding, cursor[1] + padding)
                
                ImGui.begin_child(f"skin_texture_child{rule.skin}", (skin_size, skin_size), False, PyImGui.WindowFlags.NoFlag| PyImGui.WindowFlags.NoScrollWithMouse | PyImGui.WindowFlags.NoScrollbar)
                if texture.endswith(((".jpg",".png"))) and os.path.exists(texture):
                    ImGui.DrawTextureExtended(texture_path=texture, size=(skin_size, skin_size))                    
                else:            
                    ImGui.push_font("Bold", 28)
                    text_size = PyImGui.calc_text_size(IconsFontAwesome5.ICON_QUESTION)
                    PyImGui.set_cursor_pos((((skin_size - text_size[0])) / 2), 4 + ((skin_size - text_size[1]) / 2))
                    ImGui.text(IconsFontAwesome5.ICON_QUESTION)
                    ImGui.pop_font()
                ImGui.end_child()
                            
                PyImGui.same_line(0, 5)
                without_file_ending = rule.skin.split(".")[0]
                
                GUI.vertical_centered_text(text=without_file_ending or "No Skin Selected", desired_height=skin_size + 4)
                
                if is_selected:
                    PyImGui.same_line(0, 5)
                    delete_rect = (screen_cursor[0] + remaining_size[0] - 30, screen_cursor[1] + 6, 24, 24)
                    delete_hovered = GUI.is_mouse_in_rect(delete_rect)
                    
                    PyImGui.set_cursor_screen_pos(delete_rect[0], delete_rect[1])
                    ImGui.DrawTextureExtended(texture_path=texture_map.CoreTextures.UI_Cancel_Hovered.value if delete_hovered else texture_map.CoreTextures.UI_Cancel.value, size=(24, 24), tint=(150,150,150,255) if not delete_hovered else (255,255,255,255))
                    
                    if PyImGui.is_item_clicked(0):                        
                        delete_clicked = True
                        
                        if self.settings.profile:
                            self.settings.profile.remove_rule(rule)
                            self.settings.profile.save()
                            
                        self.selected_rule = None
                        self.selected_rule_changed = True
                        self.filter_rules()                        
                        pass
                    
                    ImGui.show_tooltip("Delete Rule")
                                
            ImGui.end_child()
            
        else:
            PyImGui.dummy(0, skin_size)
        
        is_hovered = PyImGui.is_item_hovered()
        
        if not delete_clicked and PyImGui.is_item_clicked(0):
            is_selected = not is_selected
        
        return is_selected, is_hovered
    
    def draw_skin_selectable(self, skin: str, is_selected: bool) -> tuple[bool, bool]:
        size = 38
        padding = 4
        skin_size = size - (padding * 2)
        
        if PyImGui.is_rect_visible(0, size):            
            if ImGui.begin_child(f"skin_{skin}", (0, size), False, PyImGui.WindowFlags.NoFlag | PyImGui.WindowFlags.NoScrollWithMouse | PyImGui.WindowFlags.NoScrollbar):
                texture = os.path.join(self.item_textures_path, f"{skin}")   
                remaining_size = PyImGui.get_content_region_avail()
                
                cursor = PyImGui.get_cursor_screen_pos()   
                is_visible = PyImGui.is_rect_visible(10, 1)      
                is_hovered = GUI.is_mouse_in_rect((cursor[0], cursor[1], remaining_size[0], remaining_size[1])) and is_visible and PyImGui.is_window_hovered()
                
                if is_hovered:
                    PyImGui.draw_list_add_rect_filled(cursor[0], cursor[1], cursor[0] + remaining_size[0], cursor[1] + size, self.style.Hovered_Item.color_int, 1.0, 0)
                    PyImGui.draw_list_add_rect(cursor[0], cursor[1], cursor[0] + remaining_size[0], cursor[1] + size, self.style.Hovered_Item.color_int, 1.0, 0, 2.0)
                    
                if is_selected:
                    PyImGui.draw_list_add_rect_filled(cursor[0], cursor[1], cursor[0] + remaining_size[0], cursor[1] + size, self.style.Selected_Item.color_int, 1.0, 0)
                    PyImGui.draw_list_add_rect(cursor[0], cursor[1], cursor[0] + remaining_size[0], cursor[1] + size, self.style.Selected_Item.color_int, 1.0, 0, 2.0)
                
                cursor = PyImGui.get_cursor_pos()
                PyImGui.set_cursor_pos(cursor[0] + padding, cursor[1] + padding)
                
                ImGui.begin_child(f"skin_texture_child{skin}", (skin_size, skin_size), False, PyImGui.WindowFlags.NoFlag| PyImGui.WindowFlags.NoScrollWithMouse | PyImGui.WindowFlags.NoScrollbar)
                if texture.endswith((".jpg",".png")) and os.path.exists(texture):
                    ImGui.DrawTextureExtended(texture_path=texture, size=(skin_size, skin_size))                    
                else:            
                    ImGui.push_font("Bold", 28)
                    text_size = PyImGui.calc_text_size(IconsFontAwesome5.ICON_QUESTION)
                    PyImGui.set_cursor_pos((((skin_size - text_size[0])) / 2), 4 + ((skin_size - text_size[1]) / 2))
                    ImGui.text(IconsFontAwesome5.ICON_QUESTION)
                    ImGui.pop_font()
                ImGui.end_child()
                            
                PyImGui.same_line(0, 5)
                without_file_ending = skin.split(".")[0]
                
                GUI.vertical_centered_text(text=without_file_ending or "No Skin Selected", desired_height=skin_size + 4)
                                
            ImGui.end_child()
            
        else:
            PyImGui.dummy(0, skin_size)
        
        is_hovered = PyImGui.is_item_hovered()
        
        if PyImGui.is_item_clicked(0):
            is_selected = not is_selected
        
        return is_selected, is_hovered
            
    def draw_skin_select_popup(self):
        if not self.settings.profile or not self.selected_rule:
            return
        
        opened = False
        is_mouse_over = False
        if self.skin_select_popup:
            if not self.skin_select_popup_open:
                PyImGui.set_next_window_size(300, 600)
                PyImGui.set_next_window_pos(self.py_io.mouse_pos_x, self.py_io.mouse_pos_y)
                opened = True
        else:
            self.skin_select_popup_open = False
            return
            
        self.skin_select_popup_open = PyImGui.begin("Select Skin", PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.NoResize | PyImGui.WindowFlags.NoMove)
        
        if self.skin_select_popup_open:     
            popup_size = PyImGui.get_content_region_avail()       
            PyImGui.push_item_width(popup_size[0] - 30)
            changed, search = ImGui.search_field("##search_skin", self.skin_search, f"Search for skin name or model id ...")            
            PyImGui.pop_item_width()
            if changed:
                self.skin_search = search.lower()
        
            PyImGui.same_line(0, 5)
            
            if ImGui.button(IconsFontAwesome5.ICON_FILTER):
                self.filter_popup = not self.filter_popup
                if self.filter_popup:
                    PyImGui.open_popup("Filter Loot Items")
                pass
                
            
            existing_skins_from_rules = [
                rule.skin for rule in self.settings.profile.skin_rules if rule.skin and rule != self.selected_rule
            ]
            
            if ImGui.begin_child("skin_selection_list", (0, 0), True, PyImGui.WindowFlags.NoFlag):
                sorted_skins = sorted(self.data.ItemsBySkins.items(), key=lambda x: x[0].lower())
                
                for skin, items in sorted_skins:
                    if skin in existing_skins_from_rules:
                        continue
                    
                    if not self.skin_search or self.skin_search in skin.lower():
                        if not self.selected_filter or any(self.selected_filter.match(item) for item in items):
                            selected, hovered = self.draw_skin_selectable(skin, skin == self.selected_rule.skin if self.selected_rule else False)
                            
                            if self.selected_rule_changed and selected:
                                self.selected_rule_changed = False
                                PyImGui.set_scroll_here_y(0.5)
                                                            
                            if selected and skin != self.selected_rule.skin:
                                if self.selected_rule:
                                    self.selected_rule.skin = skin                                   
                                    self.selectable_items = self.data.ItemsBySkins.get(self.selected_rule.skin, []) if self.selected_rule else []
                                    
                                    self.skin_search = ""            
                                    self.settings.profile.save()     
                                    
                                    self.skin_select_popup = False  
                                
            ImGui.end_child()
                
            window_pos = PyImGui.get_window_pos()
            window_size = PyImGui.get_window_size()
            window_rect = (window_pos[0], window_pos[1], window_size[0], window_size[1])
            is_mouse_over = GUI.is_mouse_in_rect(window_rect)
        
        PyImGui.end()   

        if self.skin_select_popup_open and not is_mouse_over:
            if not self.filter_popup:
                if PyImGui.is_mouse_clicked(0):
                    self.skin_select_popup_open = False
                    self.skin_select_popup = False
                
        self.draw_filter_popup()
    
    def draw_item_selectable(self, item: models.Item, is_selected: bool) -> tuple[bool, bool]:
        size = 38
        padding = 4
        skin_size = size - (padding * 2)
        
        if PyImGui.is_rect_visible(size, size):            
            if ImGui.begin_child(f"item_{item.model_id}_{item.inventory_icon or ""}", (0, size), False, PyImGui.WindowFlags.NoFlag | PyImGui.WindowFlags.NoScrollWithMouse | PyImGui.WindowFlags.AlwaysAutoResize):
                texture = item.texture_file
                remaining_size = PyImGui.get_content_region_avail()
                
                cursor = PyImGui.get_cursor_screen_pos()   
                is_visible = PyImGui.is_rect_visible(10, 1)      
                is_hovered = GUI.is_mouse_in_rect((cursor[0], cursor[1], remaining_size[0], remaining_size[1])) and is_visible and PyImGui.is_window_hovered()
                
                if is_hovered:
                    PyImGui.draw_list_add_rect_filled(cursor[0], cursor[1], cursor[0] + remaining_size[0], cursor[1] + remaining_size[1], self.style.Hovered_Colored_Item.color_int, 1.0, 0)
                    PyImGui.draw_list_add_rect(cursor[0], cursor[1], cursor[0] + remaining_size[0], cursor[1] + remaining_size[1], self.style.Hovered_Colored_Item.color_int, 1.0, 0, 2.0)
                    
                if is_selected:
                    PyImGui.draw_list_add_rect_filled(cursor[0], cursor[1], cursor[0] + remaining_size[0], cursor[1] + remaining_size[1], self.style.Selected_Colored_Item.color_int, 1.0, 0)
                    PyImGui.draw_list_add_rect(cursor[0], cursor[1], cursor[0] + remaining_size[0], cursor[1] + remaining_size[1], self.style.Selected_Colored_Item.color_int, 1.0, 0, 2.0)
                
                cursor = PyImGui.get_cursor_pos()
                PyImGui.set_cursor_pos(cursor[0] + padding, cursor[1] + padding)
                
                ImGui.begin_child(f"skin_texture_child{item.model_id}_{item.inventory_icon or ""}", (skin_size, skin_size), False, PyImGui.WindowFlags.NoFlag| PyImGui.WindowFlags.NoScrollWithMouse | PyImGui.WindowFlags.NoScrollbar)
                if texture.endswith((".jpg",".png")) and os.path.exists(texture):
                    ImGui.DrawTextureExtended(texture_path=texture, size=(skin_size, skin_size))                    
                else:            
                    ImGui.push_font("Bold", 28)
                    text_size = PyImGui.calc_text_size(IconsFontAwesome5.ICON_QUESTION)
                    PyImGui.set_cursor_pos((((skin_size - text_size[0])) / 2), 4 + ((skin_size - text_size[1]) / 2))
                    ImGui.text(IconsFontAwesome5.ICON_QUESTION)
                    ImGui.pop_font()
                ImGui.end_child()
                            
                PyImGui.same_line(0, 5)
                
                color = (1, 1, 1, (255 / 255 if is_selected else 100 / 255))
                GUI.vertical_centered_text(text=item.name + ("\n" + "\n".join([utility.Util.reformat_string(attribute.name) for attribute in item.attributes]) if len(item.attributes) == 1 else ""), desired_height=skin_size + 4, color=color)
                                
            ImGui.end_child()
            
        else:
            PyImGui.dummy(size, size)
        
        is_hovered = PyImGui.is_item_hovered()
        
        if is_hovered:
            PyImGui.set_next_window_size(400, 0)
            ImGui.begin_tooltip()
            
            self.draw_item_header(item_info=item, border=False, image_size=50)
            PyImGui.dummy(50, 0)
            PyImGui.same_line(0, 10)
            height = len(item.attributes) * PyImGui.get_text_line_height() + (28 if item.attributes else 0)
            ImGui.begin_child("advanced details", (0, height), False, PyImGui.WindowFlags.NoFlag)
            if item.attributes:
                ImGui.text("Attributes")
                ImGui.separator()
                ImGui.text("\n".join([utility.Util.reformat_string(attribute.name) for attribute in item.attributes]) if item.attributes else "")
                
            ImGui.end_child()
            
            ImGui.end_tooltip()
            
        
        clicked = False
        
        if PyImGui.is_item_clicked(0):
            is_selected = not is_selected
            clicked = True
        
        return is_selected, clicked
    
    def draw_mod_selectable(self, mod: models.WeaponMod, is_selected: bool, mod_info : models.ModInfo | None) -> tuple[bool, bool]:
        clicked = False
        cog_clicked = False
        is_hovered = False
        cog_hovered = False
        
        if ImGui.begin_child(f"mod_{mod.identifier}_selectable", (0, 32), False, PyImGui.WindowFlags.NoFlag | PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse):
            size = PyImGui.get_content_region_avail()
            screen_cursor = PyImGui.get_cursor_screen_pos()
            is_hovered = GUI.is_mouse_in_rect((screen_cursor[0], screen_cursor[1], size[0], size[1])) and PyImGui.is_window_hovered()
            
            if is_hovered:
                PyImGui.draw_list_add_rect_filled(screen_cursor[0], screen_cursor[1], screen_cursor[0] + size[0], screen_cursor[1] + size[1], self.style.Hovered_Colored_Item.color_int, 1.0, 0)
                PyImGui.draw_list_add_rect(screen_cursor[0], screen_cursor[1], screen_cursor[0] + size[0], screen_cursor[1] + size[1], self.style.Hovered_Colored_Item.color_int, 1.0, 0, 2.0)
                
            if is_selected:
                PyImGui.draw_list_add_rect_filled(screen_cursor[0], screen_cursor[1], screen_cursor[0] + size[0], screen_cursor[1] + size[1], self.style.Selected_Colored_Item.color_int, 1.0, 0)
                PyImGui.draw_list_add_rect(screen_cursor[0], screen_cursor[1], screen_cursor[0] + size[0], screen_cursor[1] + size[1], self.style.Selected_Colored_Item.color_int, 1.0, 0, 2.0)
            
            PyImGui.set_cursor_screen_pos(screen_cursor[0] + 5, screen_cursor[1] + 4)
            mod_range = mod.get_modifier_range()
            args = (mod_info.min, mod_info.max) if mod_info else (mod_range.max, mod_range.max)
            color = (1, 1, 1, (255 / 255 if is_selected else 100 / 255))
            GUI.vertical_centered_text(text=mod.get_custom_description(arg1_min=args[0], arg1_max=args[1], arg2_min=args[0], arg2_max=args[1]), desired_height=int(size[1] - 4), color=color)
            # GUI.vertical_centered_text(mod.get_description(), None, int(size[1] - 4))
            
            if is_hovered and is_selected:
                cog_rect = (screen_cursor[0] + size[0] - 25, screen_cursor[1] + ((size[1] - 16) / 2), 16, 16)
                cog_hovered = GUI.is_mouse_in_rect(cog_rect)
                PyImGui.set_cursor_screen_pos(screen_cursor[0] + size[0] - 25, screen_cursor[1] + ((size[1] - 16) / 2))
                ImGui.DrawTextureExtended(texture_path=texture_map.CoreTextures.Cog.value, size=(16,16), tint=(150,150,150,255) if not cog_hovered else (255,255,255,255))
                
                if cog_hovered and PyImGui.is_item_clicked(0):
                    # ConsoleLog("LootEx", "Cog clicked for mod range selection.")
                    cog_clicked = True
                    self.mod_range_popup = True
                    
                    self.selected_rule_mod = mod
                    self.selected_mod_info = mod_info                                        
        
        ImGui.end_child()
        
        if not cog_clicked and PyImGui.is_item_clicked(0):
            is_selected = not is_selected
            clicked = True
        
        if is_hovered and not cog_hovered:
            self.weapon_mod_tooltip(mod)
        elif cog_hovered:
            ImGui.show_tooltip("Click to set modifier range for this mod.")
            
        return is_selected, clicked
    
    def draw_mod_range_popup(self, mod: models.WeaponMod | None, mod_info: models.ModInfo | None):
        if not self.settings.profile:
            return
        
        if not mod or not mod_info:
            return
        
        if self.mod_range_popup:
            PyImGui.open_popup("Mod Range")

        if ImGui.begin_popup("Mod Range"):
            mod_range = mod.get_modifier_range()
            
            ImGui.text(f"Set range for {mod.get_custom_description(arg1_min=mod_info.min, arg1_max=mod_info.max, arg2_min=mod_info.min, arg2_max=mod_info.max)}")
            ImGui.separator()
            
            min_value = mod_info.min
            max_value = mod_info.max
            
            min_value = PyImGui.slider_int("Min Value", min_value, mod_range.min, mod_range.max)
            if min_value != mod_info.min and min_value <= max_value:
                mod_info.min = min_value
                self.settings.profile.save()
            
            max_value = PyImGui.slider_int("Max Value", max_value, mod_range.min, mod_range.max)
            if max_value != mod_info.max and max_value >= min_value:
                mod_info.max = max_value
                self.settings.profile.save()            
                
            ImGui.end_popup()
            
        if PyImGui.is_mouse_clicked(0) and not PyImGui.is_item_hovered():
            if self.mod_range_popup:
                PyImGui.close_current_popup()
                self.mod_range_popup = False
    
    def draw_by_item_skin(self):            
        if ImGui.begin_tab_item("By Skin") and self.settings.profile:
                        # Get size of the tab
            tab_size = PyImGui.get_content_region_avail()
            tab_hovered = PyImGui.is_item_hovered()

            # Left panel: Loot Items Selection
            if ImGui.begin_child("skin_selection_child", (tab_size[0] * 0.3, tab_size[1]), False, PyImGui.WindowFlags.NoFlag):
                child_size = PyImGui.get_content_region_avail()

                PyImGui.push_item_width(child_size[0] - 30)
                changed, search = ImGui.search_field("##search_rule", self.rule_search, f"Search for rule name, skin name or model id ...")                
                PyImGui.pop_item_width()
                if changed:
                    self.rule_search = search
                    self.filter_rules()            

                # PyImGui.same_line(0, 5)
                # if ImGui.button(IconsFontAwesome5.ICON_FILTER):
                #     self.rule_filter_popup = not self.rule_filter_popup
                #     if self.rule_filter_popup:
                #         PyImGui.open_popup("Filter Rules")
                #     pass
                
                def draw_hint():
                    ImGui.text_wrapped(
                        "Select item skins to manage the actions performed on them once in your inventory.")
                                           
                PyImGui.same_line(0, 5)
                self.draw_info_icon(
                    draw_action=draw_hint,                 
                    width=500
                )            
                
                if ImGui.begin_child("skin selection region", (0, 0), True, PyImGui.WindowFlags.NoFlag):
                    subtab_size = PyImGui.get_content_region_avail()
                    
                    if ImGui.begin_child("selectable_skins", (subtab_size[0], subtab_size[1] - 30), False, PyImGui.WindowFlags.NoFlag):
                        for selectable_rule in self.selectable_rules:
                            rule : skin_rule.SkinRule = selectable_rule.object
                            
                            is_selected, is_hovered = self.draw_selectable_rule(rule, selectable_rule.is_selected, selectable_rule.is_hovered)
                            selectable_rule.is_hovered = is_hovered
                            
                            if is_selected != selectable_rule.is_selected:
                                selectable_rule.is_selected = is_selected
                                
                                if is_selected:
                                    self.selected_rule = selectable_rule.object
                                    self.selectable_items = self.data.ItemsBySkins.get(self.selected_rule.skin, []) if self.selected_rule else []
                                    
                                    for sel_rule in self.selectable_rules:
                                        if sel_rule.object != self.selected_rule:
                                            sel_rule.is_selected = False
                                else:
                                    self.selected_rule = None
                                
                                self.selected_rule_changed = True

                    ImGui.end_child()
                    
                    if ImGui.button("Add Rule", subtab_size[0]):
                        self.settings.profile.add_rule(
                            skin_rule.SkinRule()
                        )
                        self.filter_rules()
                        self.settings.profile.save()
                                        
                ImGui.end_child()
                
            ImGui.end_child()

            PyImGui.same_line(tab_size[0] * 0.3 + 20, 0)

            # Right panel: Loot Item Details
            if ImGui.begin_child("skin_child", (tab_size[0] - (tab_size[0] * 0.3) - 10, tab_size[1]), self.selected_rule is None, PyImGui.WindowFlags.NoFlag):
                if self.selected_rule:
                    rule : skin_rule.SkinRule = self.selected_rule
                    texture = os.path.join(self.item_textures_path, f"{rule.skin}")
                    texture_exists = texture.endswith(((".jpg",".png"))) and os.path.exists(texture)
                    
                    remaingng_size = PyImGui.get_content_region_avail()

                    has_rarities = any(item.item_type in self.rarity_item_types for item in self.selectable_items)
                    is_weapon = any(utility.Util.IsWeaponType(item.item_type) for item in self.selectable_items)
                    rarity_width = 200 if has_rarities else 0
                    
                    if ImGui.begin_child("skin_selection", ((remaingng_size[0] - ((rarity_width + 5) if has_rarities else 0)), 73), True, PyImGui.WindowFlags.NoFlag):
                        size = 52
                        padding = 8
                        skin_size = size - (padding * 2)
                        
                        cursor = PyImGui.get_cursor_screen_pos()
                        is_texture_hovered = GUI.is_mouse_in_rect((cursor[0], cursor[1], size, size))
                        is_mouse_down = PyImGui.is_mouse_down(0)
                        
                        rect = (cursor[0], cursor[1], cursor[0] + size, cursor[1] + size)   
                        if is_texture_hovered and not is_mouse_down:
                            PyImGui.draw_list_add_rect_filled(rect[0], rect[1], rect[2], rect[3], self.style.Hovered_Item.color_int, 1.0, 0)
                            PyImGui.draw_list_add_rect(rect[0], rect[1], rect[2], rect[3], self.style.Hovered_Item.color_int, 1.0, 0, 2.0)
                            
                        elif is_texture_hovered and is_mouse_down:
                            PyImGui.draw_list_add_rect_filled(rect[0], rect[1], rect[2], rect[3], self.style.Selected_Item.color_int, 1.0, 0)
                            PyImGui.draw_list_add_rect(rect[0], rect[1], rect[2], rect[3], self.style.Selected_Item.color_int, 1.0, 0, 2.0)
                            
                        ImGui.begin_child(f"selected_rule {rule.skin}", (size, size), False, PyImGui.WindowFlags.NoFlag| PyImGui.WindowFlags.NoScrollWithMouse | PyImGui.WindowFlags.NoScrollbar)
                        if texture_exists:
                            cursor = PyImGui.get_cursor_pos()
                            PyImGui.set_cursor_pos(cursor[0] + padding, cursor[1] + padding)
                            ImGui.DrawTextureExtended(texture_path=texture, size=(skin_size, skin_size))                    
                        else:            
                            ImGui.push_font("Bold", 28)
                            text_size = PyImGui.calc_text_size(IconsFontAwesome5.ICON_QUESTION)
                            PyImGui.set_cursor_pos((((size - text_size[0])) / 2), 4 + ((size - text_size[1]) / 2))
                            ImGui.text(IconsFontAwesome5.ICON_QUESTION)
                            ImGui.pop_font()
                            
                        ImGui.end_child()
                        
                        PyImGui.same_line(0, 20)
                        if PyImGui.is_item_clicked(0):
                            self.skin_select_popup = not self.skin_select_popup
                            self.selected_rule_changed = True
                            
                        ImGui.push_font("Bold", 22)
                        GUI.vertical_centered_text(text=rule.skin.split(".")[0] or "No Skin Selected", desired_height=size + padding)
                        ImGui.pop_font()
                                                
                    ImGui.end_child()                    
                                    
                    if has_rarities: 
                        PyImGui.same_line(0, 5)
                        
                        if ImGui.begin_child("rule rarities", (rarity_width, 73), True, PyImGui.WindowFlags.NoFlag | PyImGui.WindowFlags.NoScrollWithMouse | PyImGui.WindowFlags.NoScrollbar):   
                            count = 0
                            none_selected = False
                            
                            PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 5)
                            ImGui.text("Rarities")
                            
                            # ImGui.separator()   
                            for rarity, selected in rule.rarities.items():  
                                factor = 52 / 64
                                skin_size = 42
                                frame_size = (skin_size * factor, skin_size)
                                screen_cursor = PyImGui.get_cursor_screen_pos()
                                is_hovered = GUI.is_mouse_in_rect((screen_cursor[0], screen_cursor[1], frame_size[0], frame_size[1])) and PyImGui.is_window_hovered()
                                alpha = 255 if is_hovered else 225 if (selected) else 50
                                texture_alpha = 255 if is_hovered else 225 if (selected) else 100
                                frame_color =  GUI.get_rarity_rgba_color(rarity, texture_alpha) if selected else (100,100,100, texture_alpha)
                                texture_color =  (255 ,255,255 , texture_alpha) if selected else (100,100,100, 200 if is_hovered else 125 )
                                
                                # ImGui.begin_child(f"rarity_{rarity}", (frame_size[0], frame_size[1]), False, PyImGui.WindowFlags.NoFlag | PyImGui.WindowFlags.NoScrollWithMouse | PyImGui.WindowFlags.NoScrollbar)
                                
                                if is_hovered:
                                    rect = (screen_cursor[0], screen_cursor[1], screen_cursor[0] + frame_size[0], screen_cursor[1] + frame_size[1])           
                                    PyImGui.draw_list_add_rect_filled(rect[0], rect[1], rect[2], rect[3], Utils.RGBToColor(frame_color[0], frame_color[1], frame_color[2], 50), 1.0, 0)                                                     
                                                                
                                cursor = PyImGui.get_cursor_pos()
                                # PyImGui.set_cursor_pos(cursor[0] + (frame_size * count), cursor[1])
                                ImGui.DrawTextureExtended(texture_path=texture_map.CoreTextures.UI_Inventory_Slot.value, size=(frame_size[0], frame_size[1]), tint=frame_color)
                                PyImGui.set_cursor_pos(cursor[0], cursor[1] + ((frame_size[1] - skin_size) / 2))
                                
                                if texture_exists:                                        
                                    ImGui.DrawTextureExtended(texture_path=texture, size=(skin_size, skin_size), tint=texture_color)
                                else:
                                    PyImGui.dummy(skin_size, skin_size)  
                                # ImGui.end_child()
                                
                                if PyImGui.is_item_clicked(0):
                                    
                                    if self.py_io.key_ctrl:
                                        for r in rule.rarities.keys():
                                            rule.rarities[r] = not selected
                                    else:
                                        rule.rarities[rarity] = not selected
                                        
                                    self.settings.profile.save()
                                
                                ImGui.show_tooltip(f"Rarity: {rarity.name}")
                                count += 1  
                                PyImGui.same_line(10 + ((frame_size[0] + 2) * count), 0)
                                
                        ImGui.end_child()                                
                                                               
                    if ImGui.begin_child("rule action", (0, 75 if rule.action == ItemAction.Stash else 45), True, PyImGui.WindowFlags.NoFlag):    
                        action_info = self.action_infos.get(rule.action, None)
                        action_texture = action_info.icon if action_info else None
                        height = 24
                        if action_texture:
                            ImGui.DrawTexture(action_texture, height, height)
                        else:
                            PyImGui.dummy(height, height)
                        PyImGui.same_line(0, 5)            
                        PyImGui.push_item_width(PyImGui.get_content_region_avail()[0])
                        action = ImGui.combo("##RuleAction", self.item_actions.index(
                            rule.action) if rule.action in self.item_actions else 0, self.item_action_names)                        
                        PyImGui.pop_item_width()
                        
                        if self.item_actions[action] != rule.action:
                            rule.action = self.item_actions[action]
                            self.settings.profile.save()
                        
                        ImGui.show_tooltip((f"{self.action_infos.get_name(ItemAction.Loot)} and " if rule.action not in [ItemAction.NONE, ItemAction.Loot, ItemAction.Destroy] else "") + f"{self.action_infos.get_name(rule.action)}")
                    
                        if rule.action == ItemAction.Stash:
                            full_stack_only = ImGui.checkbox("Only stash full stacks", rule.full_stack_only)
                            if full_stack_only != rule.full_stack_only:
                                rule.full_stack_only = full_stack_only
                                self.settings.profile.save()
                    
                    ImGui.end_child()
                         
                    if ImGui.begin_child("rule_settings", (0, 0), False, PyImGui.WindowFlags.NoFlag):
                        remaining_size = PyImGui.get_content_region_avail()
                        config_width = min(480, remaining_size[0] / 3 * 2)
                        items_width = remaining_size[0] - config_width if is_weapon else remaining_size[0]
                        
                        if ImGui.begin_child("rule items", (items_width, 0), True, PyImGui.WindowFlags.NoFlag):
                            if PyImGui.is_rect_visible(1, 20):
                                ##TODO: FIX THIS AS ITS AN INVALID CALCULATION
                                items = len(self.selectable_items)
                                items_height = (items * 45) + 112
                                columns = int(max(1, math.floor(items_width / 210) if items_height > remaingng_size[1] else 1))
                                
                                if ImGui.begin_table("rule_items_table", columns, PyImGui.TableFlags.NoBordersInBody | PyImGui.TableFlags.ScrollY): 
                                    PyImGui.table_next_column()
                                                                                            
                                    for item in self.selectable_items:
                                        if item:
                                            existing_model_info = next((
                                                model_info for model_info in rule.models
                                                if model_info.model_id == item.model_id and model_info.item_type == item.item_type
                                            ), None)
                                            
                                            is_selected = existing_model_info is not None
                                            none_selected = rule.models is None or len(rule.models) == 0
                                            
                                            selected, clicked = self.draw_item_selectable(item, none_selected or is_selected)
                                            if clicked:
                                                if self.py_io.key_ctrl:
                                                    if existing_model_info:
                                                        rule.models.clear()
                                                        
                                                    else:
                                                        rule.models.clear()
                                                        rule.models.append(
                                                            skin_rule.ItemModelInfo(item_type=item.item_type, model_id=item.model_id)
                                                        )
                                                else:
                                                    if existing_model_info:
                                                        rule.models.remove(existing_model_info)
                                                        
                                                    else:
                                                        rule.models.append(
                                                            skin_rule.ItemModelInfo(item_type=item.item_type, model_id=item.model_id)
                                                        )
                                                self.settings.profile.save()
                                                
                                            PyImGui.table_next_column()
                                    
                                    ImGui.end_table()
                            
                        ImGui.end_child()
                        
                        if is_weapon:
                            PyImGui.same_line(0, 5)
                            
                            if ImGui.begin_child("rule configs", (config_width, 0), False, PyImGui.WindowFlags.NoFlag):    
                                remaingng_size = PyImGui.get_content_region_avail()
                                requirements_size = (remaingng_size[0], 90)
                                if ImGui.begin_child("rule requirements", (0, requirements_size[1]), True, PyImGui.WindowFlags.NoFlag):
                                    PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 5)
                                    ImGui.push_font("Bold", 15)
                                    range_text = f"{rule.requirements.min}...{rule.requirements.max}" if rule.requirements.min != rule.requirements.max else f"{rule.requirements.min}"
                                    ImGui.text(f"Requires {range_text} of Items Attribute")
                                    ImGui.pop_font()
                                    
                                    slider_width = 100
                                    
                                    GUI.vertical_centered_text("Attribute Range:", 115, 24)
                                    
                                    PyImGui.push_item_width(slider_width)
                                    min_value = ImGui.input_int("##MinReq", rule.requirements.min)
                                    PyImGui.pop_item_width()
                                    min_value = max(min_value, 0)
                                    if min_value != rule.requirements.min:
                                        if min_value > rule.requirements.max:
                                            min_value = rule.requirements.max
                                            
                                        rule.requirements.min = min_value
                                        self.settings.profile.save()                                        
                                        
                                    PyImGui.same_line(0, 5)
                                    
                                    PyImGui.push_item_width(slider_width)
                                    max_value = ImGui.input_int("##MaxReq", rule.requirements.max) 
                                    PyImGui.pop_item_width()
                                    max_value = min(max_value, 13)
                                    if max_value != rule.requirements.max or min_value != rule.requirements.min:
                                        if max_value < min_value:
                                            max_value = min_value
                                            
                                        rule.requirements.min = min_value
                                        rule.requirements.max = max_value
                                        self.settings.profile.save()
                                    
                                    is_shield = any(item.item_type == ItemType.Shield for item in self.selectable_items)
                                    is_focus = any(item.item_type == ItemType.Offhand for item in self.selectable_items)
                                    is_weapon = any(utility.Util.IsWeaponType(item.item_type) and item.item_type not in [ItemType.Shield, ItemType.Offhand] for item in self.selectable_items)
                                    stat_types = [f"{"Damage" if is_weapon else ""}", f"{"Energy" if is_focus else ""}", f"{"Armor" if is_shield else ""}", ] 
                                    stat_types = [stat for stat in stat_types if stat]  # Remove empty strings
                                    only_max = ImGui.checkbox(f"Only max {"/".join(stat_types)} for selected Attribute Range", rule.requirements.max_damage_only)            
                                    if only_max != rule.requirements.max_damage_only:
                                        rule.requirements.max_damage_only = only_max
                                        self.settings.profile.save()                   
                                    
                                ImGui.end_child()
                                
                                if ImGui.begin_child("rule mods", (0, (remaingng_size[1] - 6) - requirements_size[1]), True, PyImGui.WindowFlags.NoFlag):
                                    ImGui.push_font("Bold", 15)
                                    ImGui.text("Mods")
                                    ImGui.pop_font()
                                    
                                    combo_width = 150
                                    mods_size = PyImGui.get_content_region_avail()
                                    PyImGui.same_line(mods_size[0] - combo_width + 10, 0)
                                    PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 5)                                    
                                    PyImGui.push_item_width(combo_width)
                                    mod_type_selection = [utility.Util.reformat_string(mod.name) for mod in  ActionModsType]
                                    index = mod_type_selection.index(utility.Util.reformat_string(rule.mods_type.name))
                                    mod_index = ImGui.combo("##ModType", index, mod_type_selection)
                                    PyImGui.pop_item_width()
                                    
                                    if index != mod_index:
                                        rule.mods_type = ActionModsType(mod_index)
                                        self.settings.profile.save()
                                        
                                    PyImGui.spacing()
                                    if mod_index != 1:
                                        ImGui.push_font("Bold", 15)
                                        ImGui.text("Any inscribable version of the selected items.")
                                        ImGui.pop_font()
                                    
                                    if mod_index == 0:
                                        ImGui.separator()
                                    
                                    if mod_index != 2:
                                        ImGui.push_font("Bold", 15)
                                        target_text = "any max inherent mod" if not rule.mods else f"one of {len(rule.mods)} inherent mods"
                                        ImGui.text(f"Any old school version with {target_text}")    
                                        ImGui.pop_font()
                                                                          
                                        selectable_mods : list[models.WeaponMod] = []
                                        
                                        if ImGui.begin_child("selectable_mods", (0, 0), False, PyImGui.WindowFlags.NoFlag):
                                            for mod in self.data.Weapon_Mods.values():
                                                if mod.mod_type == ModType.Inherent:
                                                    for item in self.selectable_items:
                                                        if not mod.has_item_type(item.item_type):
                                                            continue
                                                        
                                                        if not mod in selectable_mods:
                                                            selectable_mods.append(mod)                                                
                                            
                                            #sort by is_selected (selectable_mod.identifier in rule.mods)
                                            # selectable_mods.sort(key=lambda x: x.identifier in rule.mods, reverse=True)
                                            
                                            #sort by name, but if mod.modifiers has 9240 put it to the end
                                            selectable_mods.sort(key=lambda x: (any(m.identifier == 9240 for m in x.modifiers), x.get_custom_description()), reverse=False)
                                            
                                            for selectable_mod in selectable_mods:
                                                is_selected = selectable_mod.identifier in rule.mods
                                                mod_info = rule.mods.get(selectable_mod.identifier, None)
                                                
                                                selected, clicked = self.draw_mod_selectable(selectable_mod, is_selected, mod_info)
                                                
                                                if selected != is_selected:             
                                                    if selected:
                                                        if self.py_io.key_ctrl:
                                                            for m in selectable_mods:
                                                                rule.add_mod(m)
                                                        else:
                                                            rule.add_mod(selectable_mod)                                       
                                                    else:
                                                        if self.py_io.key_ctrl:
                                                            rule.mods.clear()
                                                        else:
                                                            rule.remove_mod(selectable_mod)
                                                    
                                                    self.settings.profile.save()
                                                
                                        ImGui.end_child()
                                        
                                    ##Idea: draw info with range e.g. "Damage +13 ... 15% (while Health above 50%)"
                                ImGui.end_child()
                                
                            ImGui.end_child()
                    
                    ImGui.end_child()
                    
                    
                pass
            
            ImGui.end_child()
            
            # self.draw_rule_filter_popup()
            self.draw_skin_select_popup()
            self.draw_mod_range_popup(self.selected_rule_mod, self.selected_mod_info)
            
            ImGui.end_tab_item()
    
    #endregion
    
    #region Low Req
    ##TODO: Select requirements and damage, select OS mods ranges, rarities
    
    def draw_low_req_selectable(self, item: SelectableWrapper) -> bool:
        style = ImGui.get_style()
        # Apply background color for selected or hovered items
        
        if item.is_selected:
            selected_color = Utils.RGBToColor(34, 34, 34, 255)
            style.ChildBg.push_color((34, 34, 34, 255))

        if item.is_hovered:
            hovered_color = Utils.RGBToColor(63, 63, 63, 255)
            style.ChildBg.push_color((63, 63, 63, 255))

        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.ItemSpacing, 0, 0)
        texture_height = 30
        ImGui.begin_child(
            f"LowReqSelectableItem{item.object}",
            (0, texture_height),
            False,
            PyImGui.WindowFlags.NoFlag,
        )
        
        texture = self.item_type_textures.get(item.object, None)
        if texture:
            ImGui.DrawTexture(texture, texture_height, texture_height)
        else:
            PyImGui.dummy(texture_height, texture_height)
            
        PyImGui.same_line(0, 5)
        
        GUI.vertical_centered_text(
            utility.Util.reformat_string(item.object.name), None, texture_height
        )
        
        ImGui.end_child()
        PyImGui.pop_style_var(1)
        
        # Pop background color styles if applied
        if item.is_selected:
            style.ChildBg.pop_color()

        if item.is_hovered:
            style.ChildBg.pop_color()


        item.is_hovered = PyImGui.is_item_hovered()
        clicked = PyImGui.is_item_clicked(0)
        
        if clicked:
            item.is_selected = not item.is_selected            

        return clicked
    
    def draw_requirements_selectable(self, item_type : ItemType, requirement : int, damage_range : models.IntRange | None, damage_range_info : models.IntRange, selected : bool) -> bool:
        item_type_requirment_texts = {
            ItemType.Axe: "{0} Axe Mastery",
            ItemType.Bow: "{0} Marksmanship",
            ItemType.Daggers : "{0} Dagger Mastery",
            ItemType.Hammer: "{0} Hammer Mastery",
            ItemType.Scythe: "{0} Scythe Mastery",
            ItemType.Spear: "{0} Spear Mastery",
            ItemType.Sword: "{0} Sword Mastery",
            ItemType.Staff: "{0} Caster Attributes",
            ItemType.Wand: "{0} Caster Attributes",
            ItemType.Shield: "{0} Shield Attributes",
            ItemType.Offhand: "{0} Caster Attributes",
        }         
        
        damage_range_text = ""
        value_range = damage_range if damage_range else damage_range_info
        
        match (item_type):
            
            case ItemType.Axe | ItemType.Bow | ItemType.Daggers | ItemType.Hammer | ItemType.Scythe | ItemType.Spear | ItemType.Sword | ItemType.Staff | ItemType.Wand:
                min_damage_format = ("({0}...{1})" if damage_range and damage_range.min != damage_range_info.min else "{0}")
                max_damage_format = ("({0}...{1})" if  damage_range and damage_range.max != damage_range_info.max else "{0}")
                value_text = min_damage_format.format(value_range.min, damage_range_info.min) + "-" + max_damage_format.format(value_range.max, damage_range_info.max) if value_range.min != value_range.max else min_damage_format.format(value_range.min, damage_range_info.min)
                damage_range_text = "Damage: " + value_text
                
            case ItemType.Shield:
                min_damage_format = "{0}" 
                max_damage_format = "{0}"
                value_text = min_damage_format.format(value_range.min) + "..." + max_damage_format.format(value_range.max) if value_range.min != value_range.max else min_damage_format.format(value_range.min)
                damage_range_text = "Armor: " + value_text
            
            case ItemType.Offhand:
                min_damage_format = "{0}"
                max_damage_format = "{0}"
                value_text = min_damage_format.format(value_range.min) + "..." + max_damage_format.format(value_range.max) if value_range.min != value_range.max else min_damage_format.format(value_range.min)
                damage_range_text = "Energy: " + value_text
                
                
        cog_hovered = False
        cog_clicked = False
        is_hovered = False
        
        height = 40
        if PyImGui.is_rect_visible(1, height):
            if ImGui.begin_child(f"LowReqSelectable{item_type}_{requirement}_{damage_range}",(0, height), False, PyImGui.WindowFlags.NoFlag):
                size = PyImGui.get_content_region_avail()
                text_size = size[1] / 2 + 2
                screen_cursor = PyImGui.get_cursor_screen_pos()
                is_hovered = GUI.is_mouse_in_rect((screen_cursor[0], screen_cursor[1], size[0], size[1])) and PyImGui.is_window_hovered()
                style = ImGui.get_style()
                    
                if selected:
                    PyImGui.draw_list_add_rect_filled(screen_cursor[0], screen_cursor[1], screen_cursor[0] + size[0], screen_cursor[1] + size[1], self.style.Selected_Colored_Item.color_int, style.FrameRounding.value1, 0)
                
                if is_hovered:
                    PyImGui.draw_list_add_rect_filled(screen_cursor[0], screen_cursor[1], screen_cursor[0] + size[0], screen_cursor[1] + size[1], self.style.Hovered_Colored_Item.color_int, style.FrameRounding.value1, 0) 
                
                item_type_text = item_type_requirment_texts.get(item_type, "Unknown")
                PyImGui.set_cursor_pos_x(PyImGui.get_cursor_pos_x() + 5)
                
                ImGui.push_font("Regular", 15)
                GUI.vertical_centered_text(f"Requires {item_type_text.format(requirement)}", None, text_size + 6)
                ImGui.pop_font()
                
                PyImGui.set_cursor_pos_x(PyImGui.get_cursor_pos_x() + 5)
                PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 8)
                GUI.vertical_centered_text(damage_range_text, None, text_size)
                
                if is_hovered and selected:
                    cog_rect = (screen_cursor[0] + size[0] - 25, screen_cursor[1] + ((size[1] - 16) / 2), 16, 16)
                    cog_hovered = GUI.is_mouse_in_rect(cog_rect)
                    PyImGui.set_cursor_screen_pos(screen_cursor[0] + size[0] - 25, screen_cursor[1] + ((size[1] - 16) / 2))
                    ImGui.DrawTextureExtended(texture_path=texture_map.CoreTextures.Cog.value, size=(16,16), tint=(150,150,150,255) if not cog_hovered else (255,255,255,255))
                    
                    if cog_hovered and PyImGui.is_item_clicked(0):
                        # ConsoleLog("LootEx", "Cog clicked for mod range selection.")
                        cog_clicked = True
                        self.dmg_range_popup = True
                        
                        self.selected_rule_damage_range = damage_range
                        self.selected_damage_range = damage_range_info   
                        
                        requirements = self.data.DamageRanges.get(item_type, None)
                        self.selected_damage_range_min = requirements.get(0) if requirements else models.IntRange(0, 0)
            
            
            ImGui.end_child()
            
            if PyImGui.is_item_clicked(0) and is_hovered and not cog_clicked:
                selected = not selected
        else:
            PyImGui.dummy(0, height)
            
        return selected
    
    
    def draw_damage_range_popup(self, selected_rule_damage_range : models.IntRange | None, damage_range : models.IntRange | None, min_range : models.IntRange | None):
        if not self.settings.profile:
            return
        
        if not selected_rule_damage_range or not damage_range or not min_range:
            return
        
        if self.dmg_range_popup:
            PyImGui.open_popup("Damage Range")

        if ImGui.begin_popup("Damage Range"):            
            ImGui.text(f"Set damage range")
            ImGui.separator()
            
            min_value = selected_rule_damage_range.min
            max_value = selected_rule_damage_range.max
            
            min_value = PyImGui.slider_int("Min Value", min_value, min_range.min, damage_range.min)
            if min_value != selected_rule_damage_range.min and min_value <= max_value:
                selected_rule_damage_range.min = min_value
                self.settings.profile.save()
            
            max_value = PyImGui.slider_int("Max Value", max_value, damage_range.min, damage_range.max)
            if max_value != selected_rule_damage_range.max and max_value >= min_value:
                selected_rule_damage_range.max = max_value
                self.settings.profile.save()            
                
            ImGui.end_popup()
            
        if PyImGui.is_mouse_clicked(0) and not PyImGui.is_item_hovered():
            if self.dmg_range_popup:
                PyImGui.close_current_popup()
                self.dmg_range_popup = False
        
    def draw_low_req(self):
        if self.first_draw:
            # self.filter_items()
            pass
        
        if ImGui.begin_tab_item("By Weapon Type") and self.settings.profile:            
            selected_item_type : ItemType | None = None
            texture_height = 30
            
            tab_size = PyImGui.get_content_region_avail()

            # Left panel: Loot Items Selection
            if ImGui.begin_child("Low Req Child Left", (tab_size[0] * 0.15, 0), True, PyImGui.WindowFlags.NoFlag):
                    
                for selectable in self.os_low_req_itemtype_selectables:
                    if self.draw_low_req_selectable(selectable):
                        for other_selectable in self.os_low_req_itemtype_selectables:
                            if other_selectable != selectable:
                                other_selectable.is_selected = False
                    
                    if selectable.is_selected:
                        selected_item_type = selectable.object
                                
                    PyImGui.spacing()
                    
            ImGui.end_child()
            
            PyImGui.same_line(0, 5)
            
            rule = self.settings.profile.weapon_rules.get(selected_item_type, None) if selected_item_type else None
            if ImGui.begin_child("Low Req Child Right", (0, 0), True, PyImGui.WindowFlags.NoFlag):
                if selected_item_type and rule:                                
                    texture = self.item_type_textures.get(selected_item_type, None)
                    if texture:
                        ImGui.DrawTexture(texture, texture_height, texture_height)
                    else:
                        PyImGui.dummy(texture_height, texture_height)
                        
                    PyImGui.same_line(0, 5)
                    
                    GUI.vertical_centered_text(
                        utility.Util.reformat_string(selected_item_type.name), None, texture_height
                    )
                    ImGui.separator()
                                    
                    width_remaining = PyImGui.get_content_region_avail()[0] - 10
                    
                    if ImGui.begin_child("Low Req Req & Damage", (width_remaining / 2, 0), True, PyImGui.WindowFlags.NoFlag):
                        requirements = self.data.DamageRanges.get(selected_item_type, None)
                        
                        if requirements:
                            for req, damage_range in requirements.items():
                                rule_damage_range = rule.requirements.get(req, None)
                            
                                is_selected = rule_damage_range is not None                                
                                selected = self.draw_requirements_selectable(selected_item_type, req, rule_damage_range, damage_range, is_selected)   
                                
                                if selected != is_selected:
                                    if selected:
                                        if self.py_io.key_ctrl:
                                            for r in requirements.keys():
                                                rule.requirements[r] = rule_damage_range or models.IntRange(damage_range.min, damage_range.max)
                                        else:
                                            rule.requirements[req] = rule_damage_range or models.IntRange(damage_range.min, damage_range.max)
                                        
                                    else:
                                        if self.py_io.key_ctrl:
                                            rule.requirements.clear()
                                        else:
                                            if req in rule.requirements:
                                                del rule.requirements[req]
                                            
                                    self.settings.profile.save()
                                                        
                        pass
                    
                    ImGui.end_child()
                    
                    PyImGui.same_line(0, 5)  
                    
                    if ImGui.begin_child("Low Req Child Mods", (width_remaining / 2, 0), True, PyImGui.WindowFlags.NoFlag):
                        ImGui.push_font("Bold", 15)
                        ImGui.text("Mods")
                        ImGui.pop_font()
                        
                        combo_width = 150
                        mods_size = PyImGui.get_content_region_avail()
                        PyImGui.same_line(mods_size[0] - combo_width + 10, 0)
                        PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 5)                                    
                        PyImGui.push_item_width(combo_width)
                        mod_type_selection = [utility.Util.reformat_string(mod.name) for mod in  ActionModsType]
                        index = mod_type_selection.index(utility.Util.reformat_string(rule.mods_type.name))
                        mod_index = ImGui.combo("##ModType", index, mod_type_selection)
                        PyImGui.pop_item_width()
                        
                        if index != mod_index:
                            rule.mods_type = ActionModsType(mod_index)
                            self.settings.profile.save()
                            
                        PyImGui.spacing()
                        if mod_index != 1:
                            ImGui.push_font("Bold", 15)
                            ImGui.text("Any inscribable version of the selected items.")
                            ImGui.pop_font()
                        
                        if mod_index == 0:
                            ImGui.separator()
                        
                        if mod_index != 2:
                            ImGui.push_font("Bold", 15)
                            target_text = "any max inherent mod" if not rule.mods else f"one of {len(rule.mods)} inherent mods"
                            ImGui.text(f"Any old school version with {target_text}")    
                            ImGui.pop_font()
                                                                
                            selectable_mods : list[models.WeaponMod] = []
                            
                            if ImGui.begin_child("selectable_mods", (0, 0), False, PyImGui.WindowFlags.NoFlag):
                                for mod in self.data.Weapon_Mods.values():
                                    if mod.mod_type == ModType.Inherent:
                                        if not mod.has_item_type(selected_item_type):
                                            continue
                                        
                                        if not mod in selectable_mods:
                                            selectable_mods.append(mod)                                                
                                
                                #sort by is_selected (selectable_mod.identifier in rule.mods)
                                # selectable_mods.sort(key=lambda x: x.identifier in rule.mods, reverse=True)
                                
                                #sort by name, but if mod.modifiers has 9240 put it to the end
                                selectable_mods.sort(key=lambda x: (any(m.identifier == 9240 for m in x.modifiers), x.get_custom_description()), reverse=False)
                                
                                for selectable_mod in selectable_mods:
                                    is_selected = selectable_mod.identifier in rule.mods
                                    mod_info = rule.mods.get(selectable_mod.identifier, None)
                                    
                                    selected, clicked = self.draw_mod_selectable(selectable_mod, is_selected, mod_info)
                                    
                                    if selected != is_selected:             
                                        if selected:
                                            if self.py_io.key_ctrl:
                                                for m in selectable_mods:
                                                    rule.add_mod(m)
                                            else:
                                                rule.add_mod(selectable_mod)                                       
                                        else:
                                            if self.py_io.key_ctrl:
                                                rule.mods.clear()
                                            else:
                                                rule.remove_mod(selectable_mod)
                                        
                                        self.settings.profile.save()
                                    
                            ImGui.end_child()
                            
                    
                    ImGui.end_child()                  
                    
            ImGui.end_child()
            
            self.draw_mod_range_popup(self.selected_rule_mod, self.selected_mod_info)
            self.draw_damage_range_popup(self.selected_rule_damage_range, self.selected_damage_range, self.selected_damage_range_min)
            ImGui.end_tab_item()
    
    #endregion
   
    def draw_info_icon(self, draw_action : Callable | None = None, text : str = "", width : float = 200):
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0, 0)
        screen_cursor = PyImGui.get_cursor_screen_pos()
        rect = (screen_cursor[0], screen_cursor[1], 24, 24)
        hovered = GUI.is_mouse_in_rect(rect)
        
        texture = texture_map.CoreTextures.UI_Help_Icon_Hovered if hovered else texture_map.CoreTextures.UI_Help_Icon
        ImGui.DrawTexture(texture.value, rect[2], rect[3])
        # ImGui.text_colored(IconsFontAwesome5.ICON_QUESTION_CIRCLE, self.style.Info_Icon.color_tuple)
        PyImGui.pop_style_var(1)
        
        if PyImGui.is_item_hovered():
            PyImGui.set_next_window_size(width, 0)
            ImGui.begin_tooltip()
            
            if draw_action:
                draw_action()
            else:
                ImGui.text_wrapped(text)
            
            ImGui.end_tooltip()
    
    def draw_blacklist(self):
        if ImGui.begin_tab_item("Black- & Whitelist") and self.settings.profile:
            # Get size of the tab
            tab_size = PyImGui.get_content_region_avail()
            
            PyImGui.push_item_width(tab_size[0] - 73)
            changed, search = ImGui.search_field("##search_loot_items", self.item_search, f"Search for Item Name or Model ID...")
            PyImGui.pop_item_width()
            if changed:
                self.item_search = search
                self.filter_items() 
            
            PyImGui.same_line(0, 5)
            if ImGui.button(IconsFontAwesome5.ICON_FILTER):
                self.filter_popup = not self.filter_popup
                if self.filter_popup:
                    PyImGui.open_popup("Filter Loot Items")
            
            PyImGui.same_line(0, 5)
            
            def draw_hint():   
                ImGui.text_wrapped("Search for Items by Name or Model ID.\n"+
                             "You can also filter the items by clicking on the filter icon.\n"+
                             "This will open a popup where you can select the filters to apply.\n")
                             
                PyImGui.spacing()
                ImGui.separator()
                ImGui.text_wrapped("Blacklist")
                PyImGui.spacing()
                ImGui.text_wrapped(
                             "Items in the blacklist will not be processed by the inventory handler.\n"+
                             "This is useful for items that you do not want process in any way.\n"+
                             "You can add items to the blacklist by double-clicking them in the item whitelist.\n"+
                             "You can also remove items from the blacklist by double-clicking them in the blacklist panel.")
                
                PyImGui.spacing()
                ImGui.separator()
                ImGui.text_wrapped("Whitelist")
                PyImGui.spacing()
                ImGui.text_wrapped(
                             "Items in the whitelist will be processed by the inventory handler, if they are configured in either item actions or match a filter based action.\n"+
                             "This is useful for items that you want to keep in your inventory or vault.\n"+
                             "You can add items to the whitelist by double-clicking them in the loot items panel.\n"+
                             "You can also remove items from the whitelist by double-clicking them in the whitelist panel.")
                
            self.draw_info_icon(draw_action=
                                draw_hint, width=500)
            
            ImGui.separator()
            PyImGui.dummy(0, 5)
            
            tab_size = (PyImGui.get_content_region_avail()[0] - 20)/ 2
            
            ImGui.text("Whitelisted Items")
            PyImGui.same_line(tab_size, 20)
            ImGui.text("Blacklisted Items")
            
            # Left panel: Loot Items Selection
            if ImGui.begin_child("blacklisted_selection_items_child", (tab_size, 0), True, PyImGui.WindowFlags.NoFlag):
                for item in self.filtered_blacklist_items:
                    if item and not self.settings.profile.is_blacklisted(item.item_info.item_type, item.item_info.model_id):
                        if PyImGui.is_rect_visible(1, 20):
                            self.draw_blacklist_selectable_item(item)
                        else:
                            PyImGui.dummy(0, 20)

            ImGui.end_child()

            PyImGui.same_line(0, 5)
            

            # Right panel: Loot Item Details
            if ImGui.begin_child("blacklisted_items_child", (tab_size, 0), True, PyImGui.WindowFlags.NoFlag):
                for item in self.filtered_blacklist_items:                                                       
                    if item and self.settings.profile.is_blacklisted(item.item_info.item_type, item.item_info.model_id):
                        if PyImGui.is_rect_visible(1, 20):
                            self.draw_blacklist_selectable_item(item)
                        else:
                            PyImGui.dummy(0, 20)
                
            ImGui.end_child()

            self.draw_filter_popup()
            ImGui.end_tab_item()

    def draw_item_header(self, item_info : models.Item | None, border : bool = False, height : float | None = None, image_size : float = 110):       
        image_size = min(image_size, 64)
        height = height if height else self.get_tooltip_height(item_info) + (24 if border else 0) if item_info else 130
        
        if ImGui.begin_child("item_info", (0, max(height, image_size)), border, PyImGui.WindowFlags.NoFlag):            
            if ImGui.begin_child("item_texture", (image_size, image_size), False, PyImGui.WindowFlags.NoFlag): 
                if item_info:
                    posX, posY = PyImGui.get_cursor_screen_pos()
                    if GUI.is_mouse_in_rect((posX, posY, image_size, image_size)):                                
                        if ImGui.button(IconsFontAwesome5.ICON_GLOBE, image_size, image_size) and item_info.wiki_url:
                            Player.SendChatCommand(
                                                "wiki " + item_info.name)

                                            # start the url in the default browser
                            webbrowser.open(
                                                item_info.wiki_url)

                        ImGui.show_tooltip(
                                            "Open the wiki page for this item.\n" +
                                            "If the item is not found, it will search for the item name in the wiki." if item_info.wiki_url else "This item does not have a wiki page set yet."
                                        )
                    else:
                        color = Utils.RGBToColor(64, 64, 64, 255)
                        PyImGui.push_style_color(
                                            PyImGui.ImGuiCol.Button, Utils.ColorToTuple(color))
                        PyImGui.push_style_color(
                                            PyImGui.ImGuiCol.ButtonHovered, Utils.ColorToTuple(color))
                        PyImGui.push_style_color(
                                            PyImGui.ImGuiCol.ButtonActive, Utils.ColorToTuple(color))
                        if item_info.inventory_icon:
                            ImGui.DrawTexture(item_info.texture_file, image_size, image_size)
                        else:
                            ImGui.button(IconsFontAwesome5.ICON_SHIELD_ALT + "##" + str(
                                                item_info.model_id), image_size, image_size)
                        PyImGui.pop_style_color(3)                                    
            ImGui.end_child()

            PyImGui.same_line(0, 10)
            PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() + 3)

            if ImGui.begin_child("item_details", (0, 0), False, PyImGui.WindowFlags.NoFlag):
                if item_info:
                    ImGui.text("Name: " + item_info.name)

                    ImGui.text("Model ID: " + str(item_info.model_id))
                    ImGui.text("Type: " + utility.Util.GetItemType(item_info.item_type).name)
                                    
                    if item_info.nick_index:
                        ImGui.text("Next Nick Week: " + str(item_info.next_nick_week) + " in " + str(item_info.weeks_until_next_nick) + " weeks")
                                    
                    if item_info.common_salvage:
                        summaries = [salvage_info.summary for salvage_info in item_info.common_salvage.values()]                        
                        ImGui.text("Salvage: " + ", ".join(summaries))
                                    
                    if item_info.rare_salvage:
                        summaries = [salvage_info.summary for salvage_info in item_info.rare_salvage.values()]   
                        ImGui.text("Rare Salvage: " + ", ".join(summaries))
                        
                    if item_info.category is not ItemCategory.None_:
                        ImGui.text("Category: " + str(utility.Util.reformat_string(item_info.category.name)))
                        
                    if item_info.sub_category is not ItemSubCategory.None_:
                        ImGui.text("Sub Category: " + str(utility.Util.reformat_string(item_info.sub_category.name)))
                
            ImGui.end_child()
        ImGui.end_child()
    
    def draw_cached_item_header(self, item : cache.Cached_Item | None, border : bool = False, height : float | None = None, image_size : float = 110): 
        if not item:
            return
        
        image_size = min(image_size, 64)
        item_info = item.data if item else None
        height = height if height else self.get_tooltip_height(item_info) + (24 if border else 0) if item and item_info else 130
        
        if ImGui.begin_child("item_info", (0, max(height, image_size)), border, PyImGui.WindowFlags.NoFlag):            
            if ImGui.begin_child("item_texture", (image_size, image_size), False, PyImGui.WindowFlags.NoFlag): 
                if item_info:
                    posX, posY = PyImGui.get_cursor_screen_pos()
                    if GUI.is_mouse_in_rect((posX, posY, image_size, image_size)):                                
                        if ImGui.button(IconsFontAwesome5.ICON_GLOBE, image_size, image_size) and item_info.wiki_url:
                            Player.SendChatCommand(
                                                "wiki " + item_info.name)

                                            # start the url in the default browser
                            webbrowser.open(
                                                item_info.wiki_url)

                        ImGui.show_tooltip(
                                            "Open the wiki page for this item.\n" +
                                            "If the item is not found, it will search for the item name in the wiki." if item_info.wiki_url else "This item does not have a wiki page set yet."
                                        )
                    else:
                        color = Utils.RGBToColor(64, 64, 64, 255)
                        PyImGui.push_style_color(
                                            PyImGui.ImGuiCol.Button, Utils.ColorToTuple(color))
                        PyImGui.push_style_color(
                                            PyImGui.ImGuiCol.ButtonHovered, Utils.ColorToTuple(color))
                        PyImGui.push_style_color(
                                            PyImGui.ImGuiCol.ButtonActive, Utils.ColorToTuple(color))
                        if item_info.inventory_icon:
                            if item.item_type == ItemType.Dye:
                                dye = item.dye_info.dye1.ToInt()
                                texture = self.dye_textures[dye]
                                ImGui.DrawTexture(texture, image_size, image_size)
                            else:
                                ImGui.DrawTexture(item_info.texture_file, image_size, image_size)
                        else:
                            ImGui.button(IconsFontAwesome5.ICON_SHIELD_ALT + "##" + str(
                                                item_info.model_id), image_size, image_size)
                        PyImGui.pop_style_color(3)                                    
            ImGui.end_child()

            PyImGui.same_line(0, 10)
            PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() + 3)

            if ImGui.begin_child("item_details", (0, 0), False, PyImGui.WindowFlags.NoFlag) and item:
                if item_info:
                    ImGui.text("Name: " + item.name)

                    ImGui.text("Model ID: " + str(item_info.model_id))
                    ImGui.text("Type: " + utility.Util.GetItemType(item_info.item_type).name)
                                    
                    if item_info.nick_index:
                        ImGui.text("Next Nick Week: " + str(item_info.next_nick_week) + " in " + str(item_info.weeks_until_next_nick) + " weeks")
                                    
                    if item_info.common_salvage:
                        summaries = [salvage_info.summary for salvage_info in item_info.common_salvage.values()]                        
                        ImGui.text("Salvage: " + ", ".join(summaries))
                                    
                    if item_info.rare_salvage:
                        summaries = [salvage_info.summary for salvage_info in item_info.rare_salvage.values()]   
                        ImGui.text("Rare Salvage: " + ", ".join(summaries))
                        
                    if item_info.category is not ItemCategory.None_:
                        ImGui.text("Category: " + str(utility.Util.reformat_string(item_info.category.name)))
                        
                    if item_info.sub_category is not ItemSubCategory.None_:
                        ImGui.text("Sub Category: " + str(utility.Util.reformat_string(item_info.sub_category.name)))
                
            ImGui.end_child()
        ImGui.end_child()
    
    def get_tooltip_height(self, item_info: models.Item) -> float:
        """Calculate the number of lines needed for the tooltip based on the item info."""
        lines = 0
        
        if item_info.name is not None:
            lines += 1
        if item_info.model_id is not None:
            lines += 1
        if item_info.item_type is not None:
            lines += 1
        if item_info.nick_index is not None:
            lines += 1
        if item_info.common_salvage:
            lines += 1
        if item_info.rare_salvage:
            lines += 1
        if item_info.category is not ItemCategory.None_:
            lines += 1
        if item_info.sub_category is not ItemSubCategory.None_:
            lines += 1
                
        return (lines * PyImGui.get_text_line_height_with_spacing()) + 0

    def filter_items(self):       
        self.filtered_loot_items = [
                        SelectableItem(item) for item in self.data.Items.All
                        if item and item.item_type != ItemType.Unknown and item.name and (item.name.lower().find(self.item_search.lower()) != -1 or str(item.model_id).find(self.item_search.lower()) != -1) and (self.selected_filter is None or self.selected_filter.match(item))
                    ]
        self.filtered_blacklist_items = [
                        SelectableItem(item) for item in self.data.Items.All
                        if item and item.item_type != ItemType.Unknown and item.name and (item.name.lower().find(self.item_search.lower()) != -1 or str(item.model_id).find(self.item_search.lower()) != -1) and (self.selected_filter is None or self.selected_filter.match(item))
                    ]

    def _calc_mod_description_height(self, mod : models.WeaponMod, tab_width: float) -> float:
        base_height = 48
        
        weapon_types_height = 36
        text_size_x, text_size_y = PyImGui.calc_text_size(mod.description)

        lines_of_text = math.ceil(text_size_x / (tab_width - 60))
        required_text_height = (lines_of_text * text_size_y)

        height = base_height + required_text_height + (0 if mod.is_inscription else weapon_types_height)
                
        return height

    def filter_weapon_mods(self):
        if self.mod_search == "":
            self.filtered_weapon_mods = [SelectableWrapper(
                v) for k, v in self.data.Weapon_Mods.items() if v]

        else:
            self.filtered_weapon_mods = []
            lower_search = self.mod_search.lower()
            
            for mod in self.data.Weapon_Mods.values():
                if mod and ((mod.name and mod.name.lower().find(lower_search)) != -1 or mod.description.lower().find(lower_search) != -1 or mod.identifier.lower().find(lower_search) != -1):
                    self.filtered_weapon_mods.append(SelectableWrapper(mod))

    def draw_weapon_mods(self):
        if self.first_draw:
            self.filter_weapon_mods()
        style = ImGui.get_style()
        
        tab_name = "Weapon Mods"
        if ImGui.begin_tab_item(tab_name) and self.settings.profile:
            # Get size of the tab
            tab_size = PyImGui.get_content_region_avail()
            height = 24
            combo_width = 200
            
            # Search bar for weapon mods
            PyImGui.push_item_width(tab_size[0] - 25 - 5 - height - 5 - combo_width - 5)
            changed, search = ImGui.search_field(
                "##SearchWeaponMods",
                self.mod_search,
                f"Search for Mod Name, Description or internal Id..."
            )
            PyImGui.pop_item_width()
            
            if changed:
                self.mod_search = search
                self.filter_weapon_mods()
        
            PyImGui.same_line(0, 5)    
            action_info = self.action_infos.get(self.settings.profile.weapon_mod_action, None)
            action_texture = action_info.icon if action_info else None
            if action_texture:
                ImGui.DrawTexture(action_texture, height, height)
            else:
                PyImGui.dummy(height, height)
            PyImGui.same_line(0, 2)           
            
            current_action_index = self.keep_actions.index(self.settings.profile.weapon_mod_action) if self.settings.profile.weapon_mod_action in self.keep_actions else 0
            PyImGui.push_item_width(combo_width)
            action_index = ImGui.combo("##Weapon Mod Action", current_action_index, self.keep_action_names)
            PyImGui.pop_item_width()
            
            if action_index != current_action_index:
                self.settings.profile.weapon_mod_action = self.keep_actions[action_index]
                self.settings.profile.save()
                
            ImGui.show_tooltip(
                "Select the action to perform on extracted weapon mods and items containing more than one.\n" +
                "This will determine if the weapon mod / item is stashed or kept in your inventory."
            )                
                
            PyImGui.same_line(0, 5)
            # PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y())
            def draw_hint():
                ImGui.text_wrapped("Search for Weapon Mods by Name, Description or their internal Id.\n"+
                             "Selected Weapon Mods will be highlighted in the list.\n"+
                             "You can select a Weapon Mod by clicking on any weapon type which the mod can be applied to.\n"+
                             "Selected Weapon types will be highlighted as well.\n")
                
                PyImGui.spacing()
                ImGui.separator()
                
                ImGui.text_wrapped("Weapon Mods")
                PyImGui.spacing()
                ImGui.text_wrapped("Items containing the selected Weapon Mods will be picked up and processed by the inventory handler.\n"+
                                     "Items with more than one selected Weapon Mod will be stashed so you can choose which mod to keep.\n")
                
            self.draw_info_icon(draw_action=draw_hint, width=500)
            
            selection_width = tab_size[0]  # max(255, tab_size[0] * 0.3)
            
            ImGui.begin_child(
                "ModSelectionsChild", (selection_width, 0), False, PyImGui.WindowFlags.NoFlag)

            selected_weapon_mod = None
            
            remaining_size = PyImGui.get_content_region_avail()
            columns = max(1, math.floor(int(remaining_size[0] / 350)))
            column_width = int(remaining_size[0] / columns)
            effective_column_width = 0
            
            for chunk in chunked(self.filtered_weapon_mods, columns):
                max_height_in_row = max(self._calc_mod_description_height(
                    selectable.object, column_width) for selectable in chunk)
                
                for selectable in chunk:
                    m: models.WeaponMod = selectable.object
                    self.mod_heights[m.identifier] = max_height_in_row
            
            
            if PyImGui.is_rect_visible(1, 20):
                ImGui.begin_table(
                    "Weapon Mods Table",
                    columns,
                    PyImGui.TableFlags.NoBordersInBody |PyImGui.TableFlags.ScrollY,
                )          
                
                PyImGui.table_next_column()
                if effective_column_width == 0:
                    effective_column_width = int(PyImGui.get_content_region_avail()[0])                  

                for selectable in self.filtered_weapon_mods:                    
                    m: models.WeaponMod = selectable.object
                    selected_weapon_mod = m if selectable.is_selected else selected_weapon_mod

                    if not PyImGui.is_rect_visible(effective_column_width, self.mod_heights[m.identifier]):
                        PyImGui.dummy(effective_column_width, int(self.mod_heights[m.identifier]))
                        PyImGui.table_next_column()
                        continue
                    
                    is_in_profile = self.settings.profile.contains_weapon_mod(
                        m.identifier) if self.settings.profile else None

                    def get_frame_color():
                        style = ImGui.get_style()
                        base_color = style.Border if not is_in_profile else self.style.Selected_Colored_Item
                        return (base_color.r, base_color.g, base_color.b, (150 if is_in_profile else base_color.a))


                    color = get_frame_color()
                    style.Border.push_color(color)

                    if selectable.is_hovered:
                        style.ChildBg.push_color((255, 255, 255, 15))

                    ImGui.begin_child(
                        id=f"ModSelectable{m.identifier}", size=(effective_column_width, self.mod_heights[m.identifier]), border=True, flags=PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse)
                                  
                    style.Border.pop_color()
                    
                    if m.is_inscription:
                        texture = self.inscription_type_textures.get(m.target_types[0], None)
                        if texture and os.path.exists(texture):
                            ImGui.DrawTextureExtended(texture_path=texture, size=(16, 16), tint=(255,255,255,255) if is_in_profile else (150,150,150, 255) if selectable.is_hovered else (100, 100, 100, 255))
                            PyImGui.same_line(0, 5)
                        pass
                        
                    if is_in_profile:
                        style.Text.push_color((255, 204, 85, 255))
                        
                    ImGui.push_font("Regular", 16)
                    ImGui.text(m.applied_name)
                    ImGui.pop_font()

                    if is_in_profile:
                        style.Text.pop_color()

                    if selectable.is_hovered:
                        style.ChildBg.pop_color()

                    ImGui.separator()

                    # PyImGui.dummy(0, 0)
                    # PyImGui.same_line(0, 28)

                    style.Text.push_color((255, 255, 255, int(255 * 0.75)))
                    ImGui.text_wrapped(m.description)
                    style.Text.pop_color()

                    is_tooltip_visible = False
                    if self.settings.profile:               
                        texture_size = 32
                        offset_y = (PyImGui.get_content_region_avail()[1] - texture_size) / 2
                        cursor_y = PyImGui.get_cursor_pos_y()
                        
                        PyImGui.set_cursor_pos_y(self.mod_heights[m.identifier] - 8 - texture_size)
                        
                        if m.is_inscription:
                            pass
                        else:
                            for weapon_type in ItemType:
                                if not PyImGui.is_rect_visible(texture_size, texture_size):
                                    PyImGui.dummy(texture_size, texture_size)
                                    continue
                                
                                if not m.has_item_type(weapon_type) or m.is_inscription:
                                    continue

                                is_selected = m.identifier in self.settings.profile.weapon_mods and weapon_type.name in self.settings.profile.weapon_mods[
                                    m.identifier] and self.settings.profile.weapon_mods[m.identifier][weapon_type.name] or False

                                # textures = self.mod_textures.get(weapon_type, None)
                                # texture = textures.get(m.mod_type, None) if textures else None
                                texture = self.item_type_textures.get(weapon_type, None)         
                                                                
                                cursor = PyImGui.get_cursor_screen_pos() 
                                rect = (cursor[0], cursor[1], texture_size, texture_size)
                                hovered = GUI.is_mouse_in_rect(rect)
                                
                                style = ImGui.get_style()
                                
                                if texture:
                                    # ImGui.DrawTexture(texture, 24, 24)
                                    # tint = (255,255,255,255) if is_selected else (150,150,150, 255) if hovered else (64, 64,64, 255)
                                    # ImGui.DrawTextureExtended(texture_path=texture, size=(texture_size, texture_size))
                                    # background = (255, 204, 85, 180) if is_selected else (51, 77, 102, 255) if hovered else (26, 38, 51, 255)
                                    background = self.style.Selected_Colored_Item if is_selected else style.ButtonHovered if hovered else style.Button
                                    # selected = UI.ImageToggle(id=f"{m.identifier}{weapon_type.name}", selected=is_selected, texture_path=texture, size=(texture_size, texture_size), tint=(255,255,255,255), background=background.rgb_tuple)
                                    
                                    selected, hovered = GUI.item_toggle_button(texture, texture_size, is_selected)
                                    # ImGui.text(weapon_type.name)
                                
                                    if selected != is_selected:
                                        if not self.settings.profile.weapon_mods.get(m.identifier, None):
                                            self.settings.profile.weapon_mods[m.identifier] = {
                                            }

                                        if self.py_io.key_ctrl:
                                            for weapon_type in ItemType:
                                                self.settings.profile.weapon_mods[
                                                    m.identifier][weapon_type.name] = selected
                                        else:
                                            self.settings.profile.weapon_mods[m.identifier][weapon_type.name] = selected

                                        self.settings.profile.save()
                                        self.filter_weapon_mods()
                                else:
                                    PyImGui.dummy(texture_size, texture_size)                            
                                    
                                is_tooltip_visible = is_tooltip_visible or PyImGui.is_item_hovered()

                                ImGui.show_tooltip(
                                    f"Toggle {utility.Util.reformat_string(weapon_type.name)} for this mod.\n" +
                                    "If selected, the mod will be picked up and stored when found." +
                                    "\nHold CTRL to toggle all weapon types at once."
                                )

                                PyImGui.same_line(0, 5)
                                
                    PyImGui.new_line()
                    PyImGui.dummy(10, 12)  
                    ImGui.end_child()
                
                    if m.is_inscription:
                        if PyImGui.is_item_clicked(0):
                            selectable.is_selected = not selectable.is_selected
                            
                            if selectable.is_selected:
                                if not self.settings.profile.weapon_mods.get(m.identifier, None):
                                    self.settings.profile.weapon_mods[m.identifier] = {}
                                    
                                for weapon_type in ItemType:                                        
                                    self.settings.profile.weapon_mods[
                                        m.identifier][weapon_type.name] = selectable.is_selected
                            else:
                                self.settings.profile.weapon_mods.pop(m.identifier, None)
                            
                            self.settings.profile.save()
                            
                    selectable.is_hovered = PyImGui.is_item_hovered()

                    if not is_tooltip_visible:
                        UI.weapon_mod_tooltip(m)
                    
                    PyImGui.table_next_column()
                
                ImGui.end_table()
                
            ImGui.end_child()

            # PyImGui.same_line(0, 5)

            # ImGui.begin_child(
            #     "ModEditChild", (edit_width, tab_size[1]), True, PyImGui.WindowFlags.NoFlag)

            # ImGui.text("Mod Details")
            # ImGui.separator()

            # ImGui.text("Selected Mod: " + (selected_weapon_mod.name if selected_weapon_mod else "None"))

            # ImGui.end_child()

            if False:
                # Table headers
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.ChildBorderSize, 0)
                PyImGui.push_style_var2(ImGui.ImGuiStyleVar.CellPadding, 2, 2)
                if ImGui.begin_child(
                    f"{tab_name}TableHeaders#1",
                    (tab_size[0] - 20 if self.scroll_bar_visible else 0, 20),
                    True,
                    PyImGui.WindowFlags.NoBackground,
                ):
                    ImGui.begin_table(
                        "Weapon Mods Table",
                        len(weapon_types) + 4,
                        PyImGui.TableFlags.NoFlag,
                    )
                    PyImGui.table_setup_column(
                        "##Texture", PyImGui.TableColumnFlags.WidthFixed, 50)
                    PyImGui.table_setup_column(
                        "Name", PyImGui.TableColumnFlags.WidthFixed, 150)

                    PyImGui.table_setup_column(
                        "Description", PyImGui.TableColumnFlags.WidthFixed, 250)

                    PyImGui.table_setup_column(
                        "Inscription", PyImGui.TableColumnFlags.WidthFixed, 50
                    )

                    for weapon_type in self.weapon_types:
                        PyImGui.table_setup_column(
                            weapon_type.name, PyImGui.TableColumnFlags.WidthFixed, 50
                        )

                    PyImGui.table_headers_row()
                    ImGui.end_table()

                ImGui.end_child()

                # Table content
                self.scroll_bar_visible = False
                if ImGui.begin_child(
                    f"{tab_name}#1", (0, 0), True, PyImGui.WindowFlags.NoBackground
                ):
                    ImGui.begin_table(
                        "Weapon Mods Table",
                        len(weapon_types) + 4,
                        PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersInnerH | PyImGui.TableFlags.ScrollY,
                    )
                    PyImGui.table_setup_column(
                        "##Texture", PyImGui.TableColumnFlags.WidthFixed, 50)
                    PyImGui.table_setup_column(
                        "Name", PyImGui.TableColumnFlags.WidthFixed, 150)

                    PyImGui.table_setup_column(
                        "Description", PyImGui.TableColumnFlags.WidthFixed, 250)

                    PyImGui.table_setup_column(
                        "Inscription", PyImGui.TableColumnFlags.WidthFixed, 50
                    )

                    for weapon_type in self.weapon_types:
                        PyImGui.table_setup_column(
                            weapon_type.name, PyImGui.TableColumnFlags.WidthFixed, 50
                        )

                    server_language = utility.Util.get_server_language()
                    for mod in self.filtered_weapon_mods.values():
                        if not mod or not mod.identifier:
                            continue

                        keep = self.settings.profile.weapon_mods.get(
                            mod.identifier, None) if self.settings.profile else None

                        if keep:
                            color = utility.Util.GetRarityColorDict(Rarity.Gold)[
                                "text"]
                            PyImGui.push_style_color(
                                PyImGui.ImGuiCol.Text,
                                Utils.ColorToTuple(color),
                            )

                        PyImGui.table_next_row()
                        # Mod texture
                        PyImGui.table_next_column()
                        PyImGui.push_style_color(
                            PyImGui.ImGuiCol.Button, Utils.ColorToTuple(
                                Utils.RGBToColor(255, 255, 255, 0))
                        )
                        PyImGui.push_style_color(
                            PyImGui.ImGuiCol.ButtonHovered,
                            Utils.ColorToTuple(Utils.RGBToColor(255, 255, 255, 0)),
                        )
                        PyImGui.push_style_color(
                            PyImGui.ImGuiCol.ButtonActive,
                            Utils.ColorToTuple(Utils.RGBToColor(255, 255, 255, 0)),
                        )
                        PyImGui.push_style_var2(
                            ImGui.ImGuiStyleVar.FramePadding, 5, 8)
                        ImGui.button(
                            IconsFontAwesome5.ICON_SHIELD_ALT + f"##{mod.identifier}")
                        PyImGui.pop_style_color(3)
                        PyImGui.pop_style_var(1)

                        # Mod name
                        PyImGui.table_next_column()
                        color = utility.Util.GetRarityColorDict(Rarity.Green)[
                            "text"] if not server_language in mod.names else utility.Util.GetRarityColorDict(Rarity.White)["text"]
                        # PyImGui.push_style_color(
                        #     PyImGui.ImGuiCol.Text,
                        #     Utils.ColorToTuple(color),
                        # )
                        ImGui.text_wrapped(mod.applied_name)
                        # PyImGui.pop_style_color(1)
                        weapon_mod_tooltip(mod)
                        # ImGui.show_tooltip(
                        #     f"Mod: {mod.name}\nIdentifier: {mod.identifier}"
                        # )

                        # Mod name
                        PyImGui.table_next_column()
                        ImGui.text_wrapped(mod.description)
                        weapon_mod_tooltip(mod)
                        # ImGui.show_tooltip(
                        #     f"Mod: {mod.description}\nIdentifier: {mod.identifier}"
                        # )
                        if keep:
                            PyImGui.pop_style_color(1)

                        PyImGui.table_next_column()
                        inscription = "Inscription"

                        if mod.is_inscription:
                            unique_id = f"##{mod.identifier}{inscription}"
                            PyImGui.push_style_var2(
                                ImGui.ImGuiStyleVar.FramePadding, 0, 8)

                            is_selected = (
                                mod.identifier in self.settings.profile.weapon_mods
                                and inscription
                                in self.settings.profile.weapon_mods[mod.identifier]
                                and self.settings.profile.weapon_mods[mod.identifier][inscription]
                            )
                            mod_selected = ImGui.checkbox(unique_id, is_selected)

                            PyImGui.pop_style_var(1)
                            ImGui.show_tooltip(
                                f"{'Keep' if is_selected else 'Ignore'} {mod.name}"
                            )

                            if is_selected != mod_selected:
                                if mod_selected:
                                    if mod.identifier not in self.settings.profile.weapon_mods:
                                        self.settings.profile.weapon_mods[mod.identifier] = {
                                        }
                                    self.settings.profile.weapon_mods[mod.identifier][
                                        inscription
                                    ] = True
                                else:
                                    self.settings.profile.weapon_mods[mod.identifier].pop(
                                        inscription, None
                                    )
                                    if not self.settings.profile.weapon_mods[mod.identifier]:
                                        self.settings.profile.weapon_mods.pop(
                                            mod.identifier, None)

                                self.settings.profile.save()

                        # Weapon type checkboxes
                        for weapon_type in self.weapon_types:
                            PyImGui.table_next_column()

                            if not mod.is_inscription:
                                hasWeaponType = mod.has_item_type(weapon_type)

                                if hasWeaponType:
                                    unique_id = f"##{mod.identifier}{weapon_type}"
                                    PyImGui.push_style_var2(
                                        ImGui.ImGuiStyleVar.FramePadding, 0, 8)

                                    is_selected = (
                                        mod.identifier in self.settings.profile.weapon_mods
                                        and weapon_type.name
                                        in self.settings.profile.weapon_mods[mod.identifier]
                                        and self.settings.profile.weapon_mods[mod.identifier][weapon_type.name]
                                    )
                                    mod_selected = ImGui.checkbox(
                                        unique_id, is_selected)

                                    PyImGui.pop_style_var(1)
                                    ImGui.show_tooltip(
                                        f"{'Keep' if is_selected else 'Ignore'} {mod.name} for {weapon_type.name}"
                                    )

                                    if is_selected != mod_selected:
                                        if mod_selected:
                                            if mod.identifier not in self.settings.profile.weapon_mods:
                                                self.settings.profile.weapon_mods[mod.identifier] = {
                                                }
                                            self.settings.profile.weapon_mods[mod.identifier][
                                                weapon_type.name
                                            ] = True
                                        else:
                                            self.settings.profile.weapon_mods[mod.identifier].pop(
                                                weapon_type.name, None
                                            )
                                            if not self.settings.profile.weapon_mods[mod.identifier]:
                                                self.settings.profile.weapon_mods.pop(
                                                    mod.identifier, None)

                                        self.settings.profile.save()

                        self.scroll_bar_visible = self.scroll_bar_visible or PyImGui.get_scroll_max_y() > 0

                PyImGui.pop_style_var(2)
                ImGui.end_table()
                ImGui.end_child()

            ImGui.end_tab_item()

    def draw_runes(self):
        style = ImGui.get_style()
        tab_name = "Runes"
        if ImGui.begin_tab_item(tab_name) and self.settings.profile:
            if ImGui.begin_child(f"{tab_name}#1", (0, 0), False, PyImGui.WindowFlags.NoFlag):
                y_pos = PyImGui.get_cursor_pos_y()
                ImGui.push_font("Regular", 18)
                PyImGui.set_cursor_pos_y(y_pos + 10)
                ImGui.text("Rune Selection")
                ImGui.pop_font()

                height = 24
                button_width = 270
                combo_width = 270
                
                remaining_space = PyImGui.get_content_region_avail()
                PyImGui.same_line(remaining_space[0] - height - 5 - combo_width - 5 - button_width - 5 - 25 - 5, 5)                
                PyImGui.set_cursor_pos_y(y_pos)
                
                action_info = self.action_infos.get(self.settings.profile.rune_action, None)
                action_texture = action_info.icon if action_info else None
                if action_texture:
                    ImGui.DrawTexture(action_texture, height, height)
                else:
                    PyImGui.dummy(height, height)
                PyImGui.same_line(0, 2)           
                PyImGui.set_cursor_pos_y(y_pos)
                
                current_action_index = self.keep_actions.index(self.settings.profile.rune_action) if self.settings.profile.rune_action in self.keep_actions else 0
                PyImGui.push_item_width(combo_width)
                action_index = ImGui.combo("##Rune Action", current_action_index, self.keep_action_names)
                PyImGui.pop_item_width()
                
                if action_index != current_action_index:
                    self.settings.profile.rune_action = self.keep_actions[action_index]
                    self.settings.profile.save()
                    
                ImGui.show_tooltip(
                    "Select the action to perform when is not marked as sell.\n" +
                    "This will determine if the rune is stashed or kept in your inventory."
                )
                    
                PyImGui.same_line(0, 5)           
                PyImGui.set_cursor_pos_y(y_pos)
                if ImGui.button("Get Expensive Runes from Merchant", button_width, 0):
                    if self.settings.profile:
                        self.show_price_check_popup = not self.show_price_check_popup
                        if self.show_price_check_popup:
                            self.trader_type = "RUNES"
                            PyImGui.open_popup("Get Expensive Runes from Merchant")
                        else:
                            PyImGui.close_current_popup()
                
                def draw_help():
                    ImGui.text_wrapped(
                        "- Selecting a rune/insignia will mark it as valuable and items containing this rune/insignia will be picked up.\n" +
                        "- If the item is a salvage item and contains only one rune/insignia, the rune/insignia will be extracted by salvaging the item automatically.\n" +
                        "- If the item has multiple Runes/Insignias, the item will be stashed/kept intact so you can decide which to extract."
                    )
                    
                    PyImGui.spacing()
                    ImGui.separator()
                    ImGui.text_wrapped("Get Expensive Runes from Merchant")
                    PyImGui.spacing()
                    ImGui.text_wrapped(
                        "- Move to the Rune Trader in order to click this button.\n"+
                        "- This will check the current sell price for all runes and check those that are above the price threshold or currently unavailable.\n" +
                        "- You can set the price threshold in the popup that appears when you click the button.\n" +
                        "- The runes will be added to your profile and marked as valuable."
                    )
                    PyImGui.spacing()
                    ImGui.text_wrapped(
                        "If you click the button all selected runes/insignias will be first removed from your profile and then the expensive runes will be added.\n" + 
                        "This means that any runes/insignias you manually selected will be removed")
                
                PyImGui.same_line(0, 5)
                PyImGui.set_cursor_pos_y(y_pos)
                self.draw_info_icon(
                    draw_action=draw_help,
                    width=500
                )

                PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 5)
                ImGui.separator()

                if ImGui.begin_tab_bar("RunesTabBar"):
                    for profession, runes in self.data.Runes_by_Profession.items():

                        if not runes:
                            continue

                        profession_name = "Common" if profession == Profession._None else profession.name

                        if not ImGui.begin_tab_item(profession_name):
                            continue

                        if ImGui.begin_child("RunesSelection#1", (0, 0), True, PyImGui.WindowFlags.NoBackground):                            
                            for rune in runes.values():
                                if not rune or not rune.identifier:
                                    continue

                                if not PyImGui.is_rect_visible(0, 24):
                                    PyImGui.dummy(0, 24)
                                    continue

                                ImGui.begin_child(
                                    f"RuneSelectable{rune.identifier}",
                                    (0, 24),
                                    False,
                                    PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse
                                )
                                color = utility.Util.GetRarityColorDict(
                                    rune.rarity.value)
                                style.Text.push_color(color["text"])
                                style.FrameBg.push_color(color["content"])
                                style.FrameBgHovered.push_color(color["frame"])

                                texture = rune.texture_file if rune.texture_file else None
                                if texture:
                                    ImGui.DrawTexture(texture, 24, 24)
                                else:
                                    PyImGui.dummy(24, 24)
                                    
                                PyImGui.same_line(0, 5)
                                
                                label = f"{rune.full_name}"
                                unique_id = f"##{rune.identifier}"                                
                                is_valuable = rune.identifier in self.settings.profile.runes and self.settings.profile.runes[rune.identifier].valuable
                                rune_valuable = ImGui.checkbox(
                                    "##valuable" + unique_id,
                                    is_valuable
                                )
                                
                                is_item_hovered = False
                                hovered = PyImGui.is_item_hovered()
                                if hovered:
                                    ImGui.begin_tooltip()
                                    ImGui.text_colored("Mark", (1,1,1,1))
                                    PyImGui.same_line(0, 5)
                                    
                                    ImGui.text_colored(rune.name, Utils.ColorToTuple(Utils.RGBToColor(*color["text"])))
                                    PyImGui.same_line(0, 5)
                                    ImGui.text_colored("as valuable to pick them up and extract automatically.", (1,1,1,1))
                                    ImGui.end_tooltip()
                                
                                is_item_hovered = hovered or is_item_hovered

                                if is_valuable != rune_valuable:
                                    self.settings.profile.set_rune(rune.identifier, rune_valuable)
                                    self.settings.profile.save()

                                PyImGui.same_line(0, 5)
                                
                                is_rune_sell = (rune.identifier in self.settings.profile.runes and self.settings.profile.runes[rune.identifier].should_sell)
                                rune_sell = ImGui.checkbox(
                                    "##sell" + unique_id,
                                    is_rune_sell
                                )
                                
                                if rune_sell != is_rune_sell:
                                    self.settings.profile.set_rune(rune.identifier, rune_valuable, rune_sell)
                                    self.settings.profile.save()
                                
                                hovered = PyImGui.is_item_hovered()
                                if hovered:
                                    ImGui.begin_tooltip()
                                    ImGui.text_colored("Sell", (1,1,1,1))
                                    PyImGui.same_line(0, 5)
                                    
                                    ImGui.text_colored(rune.name, Utils.ColorToTuple(Utils.RGBToColor(*color["text"])))
                                    PyImGui.same_line(0, 5)
                                    ImGui.text_colored("to the trader for Gold.", (1,1,1,1))
                                    ImGui.end_tooltip()
                                    
                                is_item_hovered = hovered or is_item_hovered

                                
                                PyImGui.same_line(0, 5)
                                ImGui.text(utility.Util.reformat_string(rune.full_name))
                                style.Text.pop_color()
                                style.FrameBg.pop_color()
                                style.FrameBgHovered.pop_color()

                                PyImGui.same_line(0, 5)
                                ImGui.text_colored(utility.Util.format_currency(rune.vendor_value), Utils.ColorToTuple(Utils.RGBToColor(255, 255, 255, 125)))
                                ImGui.end_child()
                                
                                if not is_item_hovered:
                                    UI.rune_tooltip(rune)
                                
                                
                            ImGui.end_child()

                        ImGui.end_tab_item()

                    ImGui.end_tab_bar()

            ImGui.end_child()

            self.draw_price_check_popup()
            ImGui.end_tab_item()

    def draw_price_check_popup(self):
        if self.settings.profile is None:
            return

        if self.show_price_check_popup:
            PyImGui.open_popup("Get Expensive Runes from Merchant")

        if ImGui.begin_popup("Get Expensive Runes from Merchant"):
            ImGui.text("Please enter a price threshold:")
            ImGui.separator()

            price_input = ImGui.input_int(
                "##PriceThreshold", self.entered_price_threshold)
            if price_input is not None and price_input != self.entered_price_threshold:
                self.entered_price_threshold = price_input

            PyImGui.same_line(0, 5)

            if ImGui.button("Check Prices", 100, 0):
                if self.trader_type == "RUNES":
                    if self.entered_price_threshold is not None and self.entered_price_threshold > 0:
                        ConsoleLog(
                            "LootEx",
                            f"Checking for expensive runes from merchant with price threshold: {self.entered_price_threshold}",
                            Console.MessageType.Info,
                        )
                        
                        item_ids = Merchant.Trading.Trader.GetOfferedItems()
                        
                        def assign_rune_price(item_id: int, price: int):
                            if not self.settings.profile:
                                return
                            
                            item = cache.Cached_Item(item_id)
                            if not item.runes or len(item.runes) == 0:
                                return
                            
                            if not item.runes[0].Rune:
                                return
                            
                            rune = self.data.Runes.get(item.runes[0].Rune.identifier)
                            if not rune:
                                return
                            
                            rune.vendor_value = price
                            rune.vendor_updated = datetime.now()
                            if rune.vendor_value >= self.entered_price_threshold:
                                ConsoleLog(
                                    "LootEx",
                                    f"Rune {rune.full_name} has price {utility.Util.format_currency(rune.vendor_value)} which is above the threshold. Marking as valuable.",
                                    Console.MessageType.Info,
                                )
                                self.settings.profile.set_rune(rune.identifier, True, self.mark_to_sell_runes)
                                
                            self.settings.profile.save()
                            self.data.SaveRunes()
                        
                        
                        
                        self.settings.profile.runes.clear()
                        price_check_mgr = price_check.PriceCheckManager()
                        price_check_mgr.request_prices(item_ids, assign_rune_price)
                    else:
                        ConsoleLog(
                            "LootEx",
                            "Price threshold must be greater than 0!",
                            Console.MessageType.Error,
                        )

                self.show_price_check_popup = False
                PyImGui.close_current_popup()

            mark_to_sell = ImGui.checkbox("Mark to sell", self.mark_to_sell_runes)
            if mark_to_sell != self.mark_to_sell_runes:
                 self.mark_to_sell_runes = mark_to_sell
                 
            ImGui.end_popup()

        if PyImGui.is_mouse_clicked(0) and not PyImGui.is_item_hovered():
            if self.show_price_check_popup:
                PyImGui.close_current_popup()
                self.show_price_check_popup = False

    def draw_material_selectable(self, material : models.Material, is_selected) -> tuple[bool, bool]:
        """
        Draws a selectable checkbox for an item type in the GUI.

        Args:
            item_type: The item type to display.
            is_selected: Whether the item type is currently selected.

        Returns:
            A tuple containing:
            - A boolean indicating if the selection state has changed.
            - A boolean indicating the new selection state.
        """
        if self.settings.profile is None:
            return False, False

        texture = material.texture_file if material.texture_file else None
       
        texture_size = 32
        cursor = PyImGui.get_cursor_screen_pos()
        rect = (cursor[0], cursor[1], texture_size, texture_size)        
        hovered = GUI.is_mouse_in_rect(rect)        
        
        style = ImGui.get_style()
        background = self.style.Selected_Colored_Item.rgb_tuple if is_selected else style.ButtonHovered.rgb_tuple if hovered else style.Button.rgb_tuple
        is_now_selected = is_selected
        
        
        is_now_selected, hovered = GUI.item_toggle_button(texture, texture_size, is_selected)
        
        # if texture:
        #     is_now_selected = UI.ImageToggle(id=f"{texture}{material.model_id}", selected=is_selected, texture_path=texture, size=(texture_size, texture_size), tint=(255, 255, 255, 255) if is_selected else (200, 200, 200, 255) if hovered else (125, 125, 125, 255), background=background)
        # else:
        #     PyImGui.dummy(texture_size, texture_size)
        
        if hovered:
            ImGui.show_tooltip(f"{material.name}")
            
        return is_selected != is_now_selected, is_now_selected

    def draw_item_type_selectable(self, item_type, is_selected) -> tuple[bool, bool]:
        """
        Draws a selectable checkbox for an item type in the GUI.

        Args:
            item_type: The item type to display.
            is_selected: Whether the item type is currently selected.

        Returns:
            A tuple containing:
            - A boolean indicating if the selection state has changed.
            - A boolean indicating the new selection state.
        """
        if self.settings.profile is None:
            return False, False
        
        texture = self.item_type_textures.get(item_type, None)
        texture_size = 48
    
        is_now_selected = is_selected
      
        is_now_selected, hovered = GUI.item_toggle_button(texture, texture_size, is_selected)
        
        if hovered:
            ImGui.show_tooltip(f"Item Type: {utility.Util.reformat_string(item_type.name)}")
            
        return is_selected != is_now_selected, is_now_selected

    def draw_blacklist_selectable_item(self, item: SelectableItem):
        """
        Draws a selectable item in the GUI.

        Args:
            item (SelectableItem): The item to be displayed.
        """

        if self.settings.profile is None:
            return

        # Apply background color for selected or hovered items
        if item.is_selected:
            selected_color = Utils.RGBToColor(34, 34, 34, 255)
            PyImGui.push_style_color(
                PyImGui.ImGuiCol.ChildBg, Utils.ColorToTuple(selected_color))

        if item.is_hovered:
            hovered_color = Utils.RGBToColor(63, 63, 63, 255)
            PyImGui.push_style_color(
                PyImGui.ImGuiCol.ChildBg, Utils.ColorToTuple(hovered_color))

        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.ItemSpacing, 0, 0)
        ImGui.begin_child(
            f"SelectableItem{item.item_info.model_id}",
            (0, 20),
            False,
            PyImGui.WindowFlags.NoScrollbar,
        )

        if item.item_info.texture_file:
            ImGui.DrawTexture(item.item_info.texture_file, 20, 20)
        else:
            PyImGui.dummy(20, 20)
        
        PyImGui.same_line(0, 5)
        # Construct item name with attributes if available
        attributes = (
            [utility.Util.GetAttributeName(
                attr) + ", " for attr in item.item_info.attributes]
            if item.item_info.attributes
            else []
        )
        
        profession = utility.Util.GetProfessionName(item.item_info.profession) if item.item_info.profession else ""

        item_name = item.item_info.name
        
            
        if item.item_info.attributes and len(item.item_info.attributes) > 0:
            item_name = (
                f"{item_name} ({''.join(attributes).removesuffix(',')})"
                if len(item.item_info.attributes) > 1
                else f"{item_name} ({utility.Util.GetAttributeName(item.item_info.attributes[0])})"
            )
        elif item.item_info.attributes and len(item.item_info.attributes) == 1:
            item_name = f"{item_name} ({utility.Util.GetAttributeName(item.item_info.attributes[0])})"

        elif profession:
            item_name = f"{item_name} ({profession})"
        
        # Draw item name with vertical centering
        PyImGui.set_cursor_pos_x(PyImGui.get_cursor_pos_x() + 5)
        GUI.vertical_centered_text(item_name, None, 20)

        ImGui.end_child()
        PyImGui.pop_style_var(1)
        
        blacklisted = self.settings.profile.is_blacklisted(item.item_info.item_type, item.item_info.model_id)
        
        # Pop background color styles if applied
        if item.is_selected:
            PyImGui.pop_style_color(1)

        if item.is_hovered:
            PyImGui.pop_style_color(1)

        clicked = PyImGui.is_mouse_clicked(0) or PyImGui.is_mouse_double_clicked(0) or PyImGui.is_mouse_down(0)
        
        # Update hover and selection states
        item.is_hovered = PyImGui.is_item_hovered() or PyImGui.is_item_clicked(0) or (item.is_hovered and clicked)

        if not item.is_hovered and item.is_clicked:                            
            item.is_clicked = False

        # Show tooltip with item name
        if item.is_hovered:
            PyImGui.set_next_window_size(400, 0)
            ImGui.begin_tooltip()
            
            self.draw_item_header(item_info=item.item_info, border=False, image_size=50)

            ImGui.separator()
            ImGui.text(f"Double-click to {"blacklist" if not blacklisted else "whitelist"} the item.")                
            ImGui.end_tooltip()
            
            if (item.is_clicked and PyImGui.is_mouse_clicked(0)):
                time_since_click = datetime.now() - item.time_stamp
                
                if time_since_click.microseconds > 500000:
                    item.time_stamp = datetime.now()
                    return
                
                if blacklisted:
                    self.settings.profile.whitelist_item(item.item_info.item_type, item.item_info.model_id)            
                    self.settings.profile.save()
                    item.is_hovered = False
                    item.is_selected = False
                else:
                    self.settings.profile.blacklist_item(item.item_info.item_type, item.item_info.model_id)           
                    self.settings.profile.save()
                    item.is_hovered = False
                    item.is_selected = False
                    
            elif PyImGui.is_mouse_clicked(0) and item.is_hovered:
                item.is_clicked = True
                item.time_stamp = datetime.now()

    def draw_rare_weapons(self):
        style = ImGui.get_style()
        
        if ImGui.begin_tab_item("Rare Weapons") and self.settings.profile:
            ImGui.text("Select the rare weapons you want to keep")
            ImGui.separator()
            
            if ImGui.begin_child("Rare Weapons#1", (0, 0), True, PyImGui.WindowFlags.NoFlag):
                style.WindowPadding.push_style_var(5, 5)
                for (weapon_name, weapon_type), model_ids in self.data.Rare_Weapon_ModelIds.items():
                    if ImGui.begin_child(f"RareWeaponSelectable{weapon_name}", (0, 34), True, PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse):
                        items = self.data.Items.get(weapon_type, {})
                        
                        #get an item which has toe correct model id
                        weapon_info = next((item for item in items.values() if item.model_id in model_ids), None)                            
                        if weapon_info is None:
                            # get an item with the correct name as fallback
                            weapon_info = next((item for item in items.values() if item.name == weapon_name), None)
                            
                        weapon_texture = weapon_info.texture_file if weapon_info and weapon_info.texture_file else os.path.join(Py4GW.Console.get_projects_path(), "Textures", "missing_texture.png")
                        if weapon_texture:
                            ImGui.image(weapon_texture, (24, 24))
                        else:
                            PyImGui.dummy(24, 24)
                            
                        PyImGui.same_line(0, 5)
                        name = weapon_name
                        included = self.settings.profile.rare_weapons.get(name, False)
                        checked = ImGui.checkbox(name, included)
                        if checked != included:
                            self.settings.profile.rare_weapons[name] = checked
                            self.settings.profile.save()
                        
                    ImGui.end_child()
                    
                style.WindowPadding.pop_style_var()
            ImGui.end_child()
            ImGui.end_tab_item()

    def draw_item_conversions(self):
        style = ImGui.get_style()
        
        if ImGui.begin_tab_item("Auto Crafting"):
            if ImGui.begin_child("Auto Crafting#1", (0, 105), True, PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse):
                auto_crafting_enabled = ImGui.checkbox("Enable Auto Crafting", self.settings.auto_crafting_enabled)
                if auto_crafting_enabled != self.settings.auto_crafting_enabled:
                    self.settings.auto_crafting_enabled = auto_crafting_enabled
                    self.settings.save()
                
                auto_withdraw_materials = ImGui.checkbox("Auto Withdraw Materials", self.settings.auto_withdraw_materials)
                if auto_withdraw_materials != self.settings.auto_withdraw_materials:
                    self.settings.auto_withdraw_materials = auto_withdraw_materials
                    self.settings.save()
                                    
                auto_even_consets = ImGui.checkbox("Auto Even Consets", self.settings.auto_even_consets)
                if auto_even_consets != self.settings.auto_even_consets:
                    self.settings.auto_even_consets = auto_even_consets
                    self.settings.save()
                    
            ImGui.end_child()
            
            gold_coin = self.data.Items.get_item(ItemType.Gold_Coin, ModelID.Gold_Coins)
            gold_color = utility.Util.GetRarityColor(Rarity.Gold)
            disabled_color = style.TextDisabled            
            if gold_coin:            
                if self.settings.profile is not None:                                               
                    for recipe in self.data.Conversions + self.data.Recipes:
                        item = self.data.Items.get_item(recipe.item_type, recipe.model_id)
                        if item is None or not recipe.ingredients:
                            continue
                        
                        enabled = self.settings.conversions.get(item.get_name(ServerLanguage.English), False)
                            
                        if self.draw_recipe_selectable(style, gold_coin, gold_color, disabled_color, recipe, item, enabled, expand=True):     
                            self.settings.conversions[item.get_name(ServerLanguage.English)] = not self.settings.conversions.get(item.get_name(ServerLanguage.English), False)
                            self.settings.save()
                            
                            inventory_handling.InventoryHandler().auto_crafting_queue.clear()
            
            ImGui.end_tab_item()
        pass

    def draw_recipe_selectable(self, style : Style.Style, gold_coin : models.Item, gold_color : Color, disabled_color : Color, recipe : models.CraftingRecipe, item : models.Item, enabled : bool, amount : int = 1, expand : bool = False) -> bool:
        color = gold_color if enabled else disabled_color
        style.TableBorderStrong.push_color((color.rgb_tuple[:3] + (255 if enabled else 150,)))
        style.TableRowBg.push_color(color.rgb_tuple[:3] + (50 if enabled else 50,))        
        style.CellPadding.push_style_var(0, 4)       
        
        if ImGui.begin_table(f"Recipe{item.model_id}{item.item_type}", 5 if expand else 2, flags=PyImGui.TableFlags.BordersOuterH | PyImGui.TableFlags.BordersOuterV| PyImGui.TableFlags.RowBg):                        
            PyImGui.table_setup_column("ResultIcon", PyImGui.TableColumnFlags.WidthFixed, 32)
            PyImGui.table_setup_column("ResultName", PyImGui.TableColumnFlags.WidthStretch, 0.4 if expand else 1)
            PyImGui.table_setup_column("Ingredients", PyImGui.TableColumnFlags.WidthStretch, 0.6)
            PyImGui.table_setup_column("Gold", PyImGui.TableColumnFlags.WidthFixed, 64)
            PyImGui.table_setup_column("GoldTexture", PyImGui.TableColumnFlags.WidthFixed, 20)
                        # PyImGui.table_headers_row()
                        
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            if item.texture_file:
                ImGui.DrawTexture(item.texture_file, 32, 32)
            else:
                PyImGui.dummy(32, 32)
                        
                            
            PyImGui.table_next_column()
            ImGui.text_aligned(f"{(f"{recipe.amount * amount} " if recipe.amount != 1 or amount > 1 else '')}{utility.Util.reformat_string(item.name)}", height=32, alignment=Alignment.MidLeft, color=utility.Util.GetRarityColor(recipe.rarity).color_tuple if recipe.rarity is not Rarity.White else None, font_size=16)
            
            if expand:
                PyImGui.table_next_column()                
                self.draw_ingredients(f"{item.model_id}{item.item_type}", recipe.ingredients, amount)     
                                                           
                PyImGui.table_next_column()                
                if recipe.price > 0:
                    ImGui.text_aligned(utility.Util.format_currency_short(recipe.price * amount), alignment=Alignment.MidRight, height=32, font_size=12)
                else:
                    ImGui.text_aligned("-", alignment=Alignment.MidRight, height=32)
                            
                PyImGui.table_next_column()
                PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() + (32 - 20) / 2)

                if gold_coin and gold_coin.texture_file:
                    ImGui.DrawTexture(gold_coin.texture_file, 20, 20)
                else:
                    PyImGui.dummy(20, 20)
                                                    
                            
            ImGui.end_table()
                                            
        style.TableRowBg.pop_color()                    
        style.TableBorderStrong.pop_color()
        style.CellPadding.pop_style_var()
                    
        return PyImGui.is_item_clicked(0)

    def draw_ingredients(self, identifier : str, ingredients : list[models.Ingredient], amount : int = 1):
        if not ingredients:
            return
        
        style = ImGui.get_style()                
        style.CellPadding.push_style_var(0, 4)
        #Ingredients                        
        if ImGui.begin_table(f"Ingredient{identifier}", 2, flags=PyImGui.TableFlags.NoFlag):
            PyImGui.table_setup_column("IngredientIcon", PyImGui.TableColumnFlags.WidthFixed, 28)
            PyImGui.table_setup_column("IngredientName", PyImGui.TableColumnFlags.WidthStretch, 0)
            PyImGui.table_next_row()
                        
            for ingredient in ingredients:
                ingredient_item = self.data.Items.get_item(ingredient.item_type, ingredient.model_id)
                if ingredient_item is None:
                    continue
                                                            
                PyImGui.table_next_column()
                if ingredient_item.texture_file:
                    ImGui.DrawTexture(ingredient_item.texture_file, 24, 24)
                else:
                    PyImGui.dummy(24, 24)
                                
                PyImGui.table_next_column()
                ImGui.text_aligned(f"{(f"{ingredient.amount * amount} " if ingredient.amount != 1 else '')}{utility.Util.reformat_string(ingredient_item.name)}", color=utility.Util.GetRarityColor(ingredient.rarity).color_tuple if ingredient.rarity is not Rarity.White else None, alignment=Alignment.MidLeft, height=24)
                        
            ImGui.end_table()
        style.CellPadding.pop_style_var()

    def draw_crafting(self):
        style = ImGui.get_style()
        inventory_handler = inventory_handling.InventoryHandler()
            
        gold_coin = self.data.Items.get_item(ItemType.Gold_Coin, ModelID.Gold_Coins)
        gold_color = utility.Util.GetRarityColor(Rarity.Gold)
        disabled_color = style.TextDisabled     
        
        if not gold_coin:
            return     
        
        if not self.settings.profile:
            return
          
        if ImGui.begin_tab_item("Crafting"):
            if ImGui.begin_table("Layout##Crafting", 2, PyImGui.TableFlags.NoSavedSettings):
                PyImGui.table_setup_column("LeftColumn##Crafting", PyImGui.TableColumnFlags.WidthStretch, 0.25)
                PyImGui.table_setup_column("RightColumn##Crafting", PyImGui.TableColumnFlags.WidthStretch, 0.75)
                PyImGui.table_next_row()    
                PyImGui.table_next_column()
                
                # Left Column
                if ImGui.begin_child("Recipes", (0, 0), True, PyImGui.WindowFlags.NoFlag):
                   for recipe in self.data.Recipes:
                        item = self.data.Items.get_item(recipe.item_type, recipe.model_id) 
                        if item is None:
                            continue
                        
                        existing_action = next((action for action in inventory_handler.crafting_queue if action.recipe == recipe), None)
                        _ = self.draw_recipe_selectable(style, gold_coin, gold_color, disabled_color, recipe, item, existing_action is not None, expand=False)
                        if PyImGui.is_item_clicked(0) and PyImGui.is_mouse_double_clicked(0):          
                            if existing_action:
                                inventory_handler.crafting_queue.remove(existing_action)
                            else:
                                inventory_handler.crafting_queue.append(CraftingAction(recipe=recipe, max_amount=1))
                            
                ImGui.end_child()
                
                PyImGui.table_next_column()
                
                # Right Column                
                if ImGui.begin_child("CraftingQueue", (0, 0), True, PyImGui.WindowFlags.NoFlag):
                    ImGui.text("Crafting Queue")
                    ImGui.separator()
                    total_cost = sum(action.recipe.price * action.max_amount for action in inventory_handler.crafting_queue if action.recipe and action.recipe.price > 0)
                    ingredients : dict[int, models.Ingredient] = {}
                    for action in inventory_handler.crafting_queue:
                        if action.recipe:
                            for ingredient in action.recipe.ingredients:
                                if ingredient.model_id in ingredients:
                                    ingredients[ingredient.model_id].amount += ingredient.amount * action.max_amount
                                else:
                                    ingredients[ingredient.model_id] = models.Ingredient(
                                        item_type=ingredient.item_type,
                                        model_id=ingredient.model_id,
                                        amount=ingredient.amount * action.max_amount,
                                        rarity=ingredient.rarity
                                    )
                                    
                    all_ingredients = list(ingredients.values())
                    summary_height = max(140, (len(all_ingredients) + 1) * 34)
                    table_height = max(100, PyImGui.get_content_region_avail()[1] - summary_height - 50)
                                        
                    if ImGui.begin_table("CraftingQueueTable", 2, PyImGui.TableFlags.NoSavedSettings | PyImGui.TableFlags.ScrollY, 0, table_height):
                        PyImGui.table_setup_column("Recipe", PyImGui.TableColumnFlags.WidthStretch, 0.7)
                        PyImGui.table_setup_column("Amount", PyImGui.TableColumnFlags.WidthFixed, 120)
                        
                        PyImGui.table_next_row()
                        
                        # Display crafting queue items
                        for crafting_action in inventory_handler.crafting_queue:
                            if crafting_action.recipe is None or crafting_action.recipe.item is None:
                                ConsoleLog("LootEx", "Invalid crafting action in queue.", Console.MessageType.Warning)
                                continue
                            
                            PyImGui.table_next_column()
                            self.draw_recipe_selectable(style, gold_coin, gold_color, disabled_color, crafting_action.recipe, crafting_action.recipe.item, crafting_action._start_time is not None, crafting_action.max_amount, expand=True)
                            PyImGui.table_next_column()
                            
                            PyImGui.push_item_width(120)
                            crafting_action.max_amount = ImGui.input_int(f"##Amount{crafting_action.recipe.item.model_id}{crafting_action.recipe.item.item_type}", crafting_action.max_amount)
                            PyImGui.pop_item_width()
                            
                            crafting_action.include_storage = self.settings.profile.include_storage_materials
                            crafting_action.include_material_storage = self.settings.profile.include_storage_materials
                            
                        ImGui.end_table()
                        
                    ImGui.separator()
                    
                    if ImGui.begin_table("SummaryCraftingQueueTable", 2, PyImGui.TableFlags.NoSavedSettings, 0, summary_height):
                        PyImGui.table_setup_column("CraftingCost", PyImGui.TableColumnFlags.WidthStretch, 0.7)
                        PyImGui.table_setup_column("ActionsCraftingCost", PyImGui.TableColumnFlags.WidthFixed, 160)
                        
                        PyImGui.table_next_row()
                        PyImGui.table_next_column()
                        
                        if ImGui.begin_child("CraftingCost", (0, 0), True, PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse):
                            ImGui.DrawTexture(gold_coin.texture_file, 20, 20)
                            PyImGui.same_line(0, 5)
                            ImGui.text_aligned(f"{utility.Util.format_currency(total_cost)}", alignment=Alignment.MidLeft, height=24)                        
                            self.draw_ingredients("summary", all_ingredients)
                        
                        ImGui.end_child()
                        
                        PyImGui.table_next_column()
                        
                        if ImGui.begin_child("ActionsCraftingCost", (0, 0), False, PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse):
                            if ImGui.button("Buy Materials", 150, 30):
                                add_ingredients_to_buy(all_ingredients) 
                                        
                            if ImGui.button("Clear Queue", 150, 30):
                                inventory_handler.crafting_queue.clear()
                                
                            if ImGui.button("Start" if not inventory_handler.process_crafting else "Stop", 150, 30, appearance=ControlAppearance.Primary if not inventory_handler.process_crafting else ControlAppearance.Danger):
                                inventory_handler.process_crafting = not inventory_handler.process_crafting
                                
                            if ImGui.button("Buy Conset Evenly", 150, 30):        
                                from Sources.frenkeyLib.LootEx.crafting import get_missing_materials_to_evenout
                                missing_materials = get_missing_materials_to_evenout()         
                                add_ingredients_to_buy(missing_materials) 
                                
                            
                            grab_from_storage = ImGui.checkbox("Include Vault", self.settings.profile.include_storage_materials)
                            if grab_from_storage != self.settings.profile.include_storage_materials:
                                self.settings.profile.include_storage_materials = grab_from_storage
                                self.settings.profile.save()
                            
                            ImGui.show_tooltip("Include materials from your vault when crafting.")
                            
                        ImGui.end_child()
                        
                        ImGui.end_table()
                
                ImGui.end_child()
                
                ImGui.end_table()
                
            ImGui.end_tab_item()
        pass

    #region DataCollection View
    def draw_collected_item(self, key: str, item: ScrapedItem, is_selected: bool = False):             
        if ImGui.begin_child(key, (0, 120), True, PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse):
            if not PyImGui.is_rect_visible(0, 120):
                ImGui.end_child()
                return
            
            if ImGui.begin_child(key + "Icon", (64, 0), False, PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse):
                if item.IconExists:
                    ImGui.image(item.IconPath, (64, 64))
                else:
                    ImGui.dummy(64, 64)
                
                ImGui.show_tooltip("Path: " + item.IconPath + "\n" +
                                   "Exists: " + str(item.IconExists)  + "\n" +
                                      "Url: " + str(item.inventory_icon_url)
                                   )
                    
                if ImGui.button("Assign") and self.data_collection_item is not None:
                    self.assign_scraped_data(self.data_collection_item, item)
                    self.data_collection_item = None
                    self.filtered_scraped_items = {}
                    pass
            
            ImGui.end_child()
            
            PyImGui.same_line(0, 10)
            
            if ImGui.begin_child(key + "Details", (0, 0), False, PyImGui.WindowFlags.NoFlag):
                ImGui.text_colored(item.name, Color(0, 255, 125, 255).color_tuple, 16, "Bold")
                ImGui.text_wrapped(item.description if item.description else "No description available.")
                
                ImGui.separator()
                
                ImGui.text("Salvage Info:", 16, "Bold")
                ImGui.text_wrapped("\n".join(str(s) for s in item.common_salvage) if item.common_salvage else "No Common Salvage Info")
                ImGui.text_wrapped("\n".join(str(s) for s in item.rare_salvage) if item.rare_salvage else "No Rare Salvage Info")
                
                ImGui.separator()

                ImGui.text("Acquisition Info:", 16, "Bold")
                ImGui.text_wrapped(item.Acquisition)
                
            ImGui.end_child()
            
        ImGui.end_child()
                
    def draw_data_item(self, cached_item_id: int, data_item: models.Item, is_selected: bool = False) -> bool:
        clicked = False
        key = f"DataItem{id}{data_item.model_id}{data_item.item_type}"
        style = ImGui.get_style()
        if is_selected:
            style.ChildBg.push_color(self.style.Selected_Colored_Item.rgb_tuple)
            
        if ImGui.begin_child(key, (0, 100), True, PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse):
            if is_selected:
                style.ChildBg.pop_color()
                
            if not PyImGui.is_rect_visible(0, 100):
                ImGui.end_child()
                return False
            
            if data_item.texture_file:
                x,y = PyImGui.get_cursor_pos()
                ImGui.dummy(64, 64)
                
                PyImGui.set_cursor_pos(x, y)
                ImGui.image(data_item.texture_file, (64, 64))
            else:
                ImGui.dummy(64, 64)
                
            PyImGui.same_line(0, 10)
            
            if ImGui.begin_child(key + "Details", (0, 0), False, PyImGui.WindowFlags.NoFlag):
                ImGui.text_colored(data_item.name, Color(255, 255, 255, 255).color_tuple, 16, "Bold")
                
                ImGui.text_wrapped(str(data_item.model_id))
                
                ImGui.text_wrapped(data_item.description if data_item.description else "No description available.")
                
                ImGui.text_wrapped(data_item.acquisition if data_item.acquisition else "No acquisition info available.")
            
            ImGui.end_child()
            clicked = clicked or PyImGui.is_item_clicked(0)
            
        else:
            if is_selected:
                style.ChildBg.pop_color()
            
        ImGui.end_child()
        clicked = clicked or PyImGui.is_item_clicked(0)
        return clicked
    
    def assign_scraped_data(self, data_item : models.Item, scraped_item : ScrapedItem):
        data_item.assign_scraped_data(scraped_item, self.data)
        ConsoleLog("LootEx", f"Assigned data for item: {data_item.name}", Console.MessageType.Info)
        self.data.SaveItems(True)
    
    def get_matching_scraped_items(self, search_name: str, required_similarity : float) -> list[ScrapedItem]:
            matching_scraped_items = [scraped_item for (key, scraped_item) in self.data.ScrapedItems.items() if string_similarity(scraped_item.name, search_name) >= required_similarity]
            return matching_scraped_items
    
    def auto_assign_data_items(self):
        for itemsource, items in self.collection_items.items():
            for cached_item in items.values():
                data_item = cached_item.data
                self.data_collector.auto_assign_scraped_data(data_item)
                
        self.data.SaveItems(True)
                    
    def draw_data_collection(self): 
        self.collection_module_window.open = self.settings.scraper_window_visible
        
        if not self.collection_module_window.open:
            return
        
        if self.collection_timer.IsExpired():
            self.collection_timer.Reset()
            
            self.collection_items = {}
                
            crafter_open = ui_manager_extensions.UIManagerExtensions.IsCrafterOpen()
            collector_open = ui_manager_extensions.UIManagerExtensions.IsCollectorOpen()
            merchant_open = ui_manager_extensions.UIManagerExtensions.IsMerchantWindowOpen() and not crafter_open and not collector_open
            
            trader_array : list[int] = merchant_open and GLOBAL_CACHE.Trading.Trader.GetOfferedItems() or []
            if trader_array:
                cached_items = {item_id: cache.Cached_Item(item_id) for item_id in trader_array}
                self.collection_items["Trader"] = {item_id: cached_item for item_id, cached_item in cached_items.items() if cached_item.data and not cached_item.data.wiki_scraped}
                
            trader2_array : list[int] = merchant_open and GLOBAL_CACHE.Trading.Trader.GetOfferedItems2() or []
            if trader2_array:
                cached_items = {item_id: cache.Cached_Item(item_id) for item_id in trader2_array}
                self.collection_items["Trader 2"] = {item_id: cached_item for item_id, cached_item in cached_items.items() if cached_item.data and not cached_item.data.wiki_scraped}
                
            merchant_array : list[int] = merchant_open and GLOBAL_CACHE.Trading.Merchant.GetOfferedItems() or []
            if merchant_array:
                cached_items = {item_id: cache.Cached_Item(item_id) for item_id in merchant_array}
                self.collection_items["Merchant"] = {item_id: cached_item for item_id, cached_item in cached_items.items() if cached_item.data and not cached_item.data.wiki_scraped}
                
            crafter_array : list[int] = crafter_open and GLOBAL_CACHE.Trading.Crafter.GetOfferedItems() or []
            if crafter_array:
                cached_items = {item_id: cache.Cached_Item(item_id) for item_id in crafter_array}
                self.collection_items["Crafter"] = {item_id: cached_item for item_id, cached_item in cached_items.items() if cached_item.data and not cached_item.data.wiki_scraped}
                
            collector_array : list[int] = collector_open and GLOBAL_CACHE.Trading.Collector.GetOfferedItems() or []
            if collector_array:
                cached_items = {item_id: cache.Cached_Item(item_id) for item_id in collector_array}
                self.collection_items["Collector"] = {item_id: cached_item for item_id, cached_item in cached_items.items() if cached_item.data and not cached_item.data.wiki_scraped}
                
            inventory_array : list[int] = GLOBAL_CACHE.ItemArray.GetItemArray(CHARACTER_INVENTORY)
            if inventory_array:
                cached_items = {item_id: cache.Cached_Item(item_id) for item_id in inventory_array}
                self.collection_items["Inventory"] = {item_id: cached_item for item_id, cached_item in cached_items.items() if cached_item.data and not cached_item.data.wiki_scraped}
                
            for storage in XUNLAI_STORAGE:
                items = GLOBAL_CACHE.ItemArray.GetItemArray([storage])
                if items:
                    cached_items = {item_id: cache.Cached_Item(item_id) for item_id in items}
                    ## only those items with cached_item.data.wiki_scraped == False
                    self.collection_items[f"Xunlai Storage {storage}"] = {item_id: cached_item for item_id, cached_item in cached_items.items() if cached_item.data and not cached_item.data.wiki_scraped}
        
            empty_keys = []
            for k, items in self.collection_items.items():
                if not items:
                    # remove empty entries
                    empty_keys.append(k)
                else:
                    # remove all items which are armor
                    armor_keys = []
                    for item_id, cached_item in items.items():
                        if utility.Util.IsArmorType(cached_item.item_type):
                            armor_keys.append(item_id)
                            
                    for ak in armor_keys:
                        del items[ak]
                    
                    if not items:
                        empty_keys.append(k)
        
            for k in empty_keys:
                del self.collection_items[k]                

        style = ImGui.get_style()
        if self.collection_module_window.begin():
            avail = PyImGui.get_content_region_avail()
            
            ImGui.text("Collected Items: " + str(len(self.data.Items.All)), 16, "Bold")
            PyImGui.same_line(avail[0] - 120, 0)
            if ImGui.button("Auto Assign Data", 120, 0):
                self.auto_assign_data_items()
                
            PyImGui.same_line(avail[0] - 250, 0)
            if ImGui.button("Clear Cache", 120, 0):
                self.data_collector.reset()
                inventory_handling.InventoryHandler().scraped_items.clear()
                
            PyImGui.same_line(avail[0] - 380, 0)
            if ImGui.button("Merge Collected", 120, 0):
                messaging.SendMergingMessage()
                                
                
            ImGui.separator()
            
            avail = PyImGui.get_content_region_avail()
            if ImGui.begin_child("DataItemsChild", ((avail[0] - 10) / 2, avail[1]), False, PyImGui.WindowFlags.NoFlag):
                # for (data_item) in [item for item in self.data.Items.All if not item.wiki_scraped and utility.Util.IsArmorType(item.item_type) == False]:
                for itemsource, items in self.collection_items.items():
                    if not items:
                        continue
                    
                    ImGui.text_colored(f"{itemsource}", Color(255, 215, 0, 255).color_tuple, 16, "Bold")
                    ImGui.separator()
                        
                    for cached_item in items.values():
                        data_item = cached_item.data
                        
                        if data_item and not data_item.wiki_scraped:
                            if self.draw_data_item(cached_item.id, data_item, is_selected=data_item == self.data_collection_item):
                                self.data_collection_item = data_item if self.data_collection_item != data_item else None
                                english_name = data_item.names.get(ServerLanguage.English, "")
                                contains_amount = english_name.split(" ", 1)[0].isdigit() if english_name else False
                                search_name = english_name.replace("250", "").strip() if self.data_collection_item else ""
                                self.filtered_scraped_items = {}
                                
                                if self.data_collection_item:
                                    for (key, scraped_item) in self.data.ScrapedItems.items():
                                        if string_similarity(scraped_item.name, search_name) >= (0.9 if contains_amount else 1.0):
                                            self.filtered_scraped_items[key] = scraped_item
                                    
                                    if not self.filtered_scraped_items:
                                        ConsoleLog("LootEx", f"No exact matches found for '{search_name}'. Trying partial match...", Console.MessageType.Info)                                                                 
                                        item_name_words = english_name.split(" ")
                                        
                                        for (key, scraped_item) in self.data.ScrapedItems.items():                                    
                                            search_name_words = scraped_item.name.split(" ")
                                                                                
                                            if ((len(item_name_words) > 1 and len(search_name_words) > 1) or (len(item_name_words) == len(search_name_words))) and all(word.lower() in english_name.lower() for word in search_name_words):
                                                self.filtered_scraped_items[key] = scraped_item
                        
            ImGui.end_child()    
            
            PyImGui.same_line(0, 10)                    
            
            if ImGui.begin_child("CollectedItemsChild", ((avail[0] - 10) / 2, avail[1]), False, PyImGui.WindowFlags.NoFlag):                
                for (key, item) in self.filtered_scraped_items.items():
                    self.draw_collected_item(key, item, is_selected=item == self.scraped_item)        
                    
            ImGui.end_child()                        
            
            self.collection_module_window.process_window()
        
        self.collection_module_window.end()
        
        if not self.collection_module_window.open:
            self.settings.scraper_window_visible = False
    
    
    #endregion


    # region general ui elements
    @staticmethod
    def ImageToggle(id : str, selected : bool, texture_path: str, size : tuple[float, float], label : str = "",  padding : tuple[float, float] = (2, 2), tint: tuple[int, int, int, int] = (255, 255, 255, 255), background : tuple[int, int, int, int] = (255, 255, 255, 0)) -> bool:
        cursor = PyImGui.get_cursor_screen_pos()
        
        label_size = PyImGui.calc_text_size(label) if label else (0, 0)
        texture_size = (size[0] - padding[0] * 2, size[1] - padding[1] * 2)
        
        width = size[0] + 5 + label_size[0] if label else size[0]
        height = size[1]
        
        rect = (cursor[0], cursor[1], size[0] + 5 + label_size[0], size[1])
        hovered = GUI.is_mouse_in_rect(rect)
                
        tint = (255,255,255,255) if selected else (150,150,150,255) if hovered else (64,64,64,255)
        background_color = Utils.RGBToColor(background[0], background[1], background[2], background[3])
        
        # PyImGui.push_style_color(PyImGui.ImGuiCol.ChildBg, Utils.ColorToTuple(
        #     Utils.RGBToColor(background[0], background[1], background[2], background[3])))
        
        # cursor = PyImGui.get_cursor_pos()
        window_style = ex_style.ExStyle()
        
        imgui_style = ImGui.get_style()
        PyImGui.draw_list_add_rect_filled(cursor[0], cursor[1], cursor[0] + size[0],  cursor[1] + size[1], background_color, imgui_style.FrameRounding.value1, 0)
        
        ImGui.begin_child(f"ImageToggle{id}{texture_path}", (width, height), False, PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse)
        
        # cursor = PyImGui.get_cursor_pos()
        PyImGui.set_cursor_pos(padding[0], padding[1])
        
        if texture_path:
            ImGui.DrawTextureExtended(texture_path=texture_path, size=texture_size, tint=tint)
        else:
            ImGui.push_font("Bold", 28)
            text_size = PyImGui.calc_text_size(IconsFontAwesome5.ICON_QUESTION)
            PyImGui.set_cursor_pos((size[0] - text_size[0]) / 2, (size[1] - (28 - 6)) / 2)
            ImGui.text_colored(IconsFontAwesome5.ICON_QUESTION, (tint[0] / 255, tint[1] / 255, tint[2] / 255, tint[3] / 255))
            ImGui.pop_font()
            pass
                
        if label:
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Utils.ColorToTuple(Utils.RGBToColor(255, 255, 255, 255 if selected else 200 if hovered else 125)))
            PyImGui.set_cursor_pos(size[0] + 5, (size[1] - label_size[1]) / 2 + 3)
            ImGui.text(label)
            PyImGui.pop_style_color(1)
        
        ImGui.end_child()
        
        # PyImGui.pop_style_color(1)
                        
        if PyImGui.is_item_clicked(0):
            selected = not selected
            
        return selected
                        
    @staticmethod
    def ImageToggleXX(path : str, width : float, height : float, is_selected : bool) -> bool:
        """
        Draws an image toggle button with the specified icon and width.
        
        Args:
            path (str): The path to the image file.
            width (float): The width of the button.
            height (float): The height of the button.
            is_selected (bool): Whether the button is selected or not.
        
        Returns:
            bool: True if the button was clicked, False otherwise.
        """
        cursor_pos = PyImGui.get_cursor_screen_pos()
        rect = (cursor_pos[0], cursor_pos[1], width, height)
        transparent_color = Utils.ColorToTuple(Utils.RGBToColor(0, 0, 0, 0))   
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0, 0)
        PyImGui.push_style_color(
            PyImGui.ImGuiCol.Text,
            Utils.ColorToTuple(
                Utils.RGBToColor(255, 255, 255, 255)
                if is_selected
                else Utils.RGBToColor(255, 255, 255, 200)
                if GUI.is_mouse_in_rect(rect)
                else Utils.RGBToColor(255, 255, 255, 125)
            ),
        )
        PyImGui.push_style_color(PyImGui.ImGuiCol.Button,
                                transparent_color)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, Utils.ColorToTuple(
            Utils.RGBToColor(0, 0, 0, 125)))
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,
                                transparent_color)
        ## if file exists
        if os.path.exists(path):
            clicked = ImGui.ImageButton(f"##{path}", path, width, height)
        else:
            clicked = ImGui.button(f"##{path}", width, height)

        PyImGui.pop_style_var(1)
        PyImGui.pop_style_color(4)

        return clicked
 
    @staticmethod
    def weapon_mod_tooltip(mod: models.WeaponMod):
        if PyImGui.is_item_hovered():
            ImGui.begin_tooltip()

            PyImGui.push_style_color(
                PyImGui.ImGuiCol.Text,
                Utils.ColorToTuple(Utils.RGBToColor(255, 255, 255, 255)),
            )
            ImGui.text(f"{mod.name}")
            ImGui.text(f"{mod.description}")

            ImGui.separator()

            # ImGui.begin_child(
            #     f"WeaponModTooltip{mod.identifier}",
            #     (400, 0),
            #     True,
            #     PyImGui.WindowFlags.NoBackground,
            # )
            if PyImGui.is_rect_visible(0, 20):
                if ImGui.begin_table(mod.identifier, 2, PyImGui.TableFlags.Borders):
                    PyImGui.table_setup_column(
                        "Property", PyImGui.TableColumnFlags.WidthFixed, 150)
                    PyImGui.table_setup_column(
                        "Value", PyImGui.TableColumnFlags.WidthStretch)
                    PyImGui.table_headers_row()

                    PyImGui.table_next_row()

                    PyImGui.table_next_column()
                    ImGui.text(f"Id (internal)")

                    PyImGui.table_next_column()
                    ImGui.text(f"{mod.identifier}")

                    PyImGui.table_next_column()
                    ImGui.text(f"Mod Type")

                    PyImGui.table_next_column()
                    ImGui.text(f"{mod.mod_type.name}")

                    PyImGui.table_next_column()
                    ImGui.text(f"Applied to Item Types")

                    PyImGui.table_next_column()
                    for item_type in mod.target_types:
                        ImGui.text(f"{item_type.name}")

                ImGui.end_table()

            PyImGui.pop_style_color(1)
            # ImGui.end_child()
            ImGui.end_tooltip()

    @staticmethod
    def rune_tooltip(mod: models.Rune):
        if PyImGui.is_item_hovered():
            ImGui.begin_tooltip()

            PyImGui.push_style_color(
                PyImGui.ImGuiCol.Text,
                Utils.ColorToTuple(Utils.RGBToColor(255, 255, 255, 255)),
            )
            ImGui.text(f"{mod.name}")
            ImGui.text(f"{mod.description}")

            ImGui.separator()

            # ImGui.begin_child(
            #     f"WeaponModTooltip{mod.identifier}",
            #     (400, 0),
            #     True,
            #     PyImGui.WindowFlags.NoBackground,
            # )
            if PyImGui.is_rect_visible(0, 20):
                if ImGui.begin_table(mod.identifier, 2, PyImGui.TableFlags.Borders):
                    PyImGui.table_setup_column(
                        "Property", PyImGui.TableColumnFlags.WidthFixed, 150)
                    PyImGui.table_setup_column(
                        "Value", PyImGui.TableColumnFlags.WidthStretch)
                    PyImGui.table_headers_row()

                    PyImGui.table_next_row()

                    PyImGui.table_next_column()
                    ImGui.text(f"Id (internal)")

                    PyImGui.table_next_column()
                    ImGui.text(f"{mod.identifier}")

                    PyImGui.table_next_column()
                    ImGui.text(f"Mod Type")

                    PyImGui.table_next_column()
                    ImGui.text(f"{mod.mod_type.name}")

                    PyImGui.table_next_column()
                    ImGui.text(f"Applied")

                    PyImGui.table_next_column()            
                    ImGui.text(f"{mod.applied_name}")
                    
                    PyImGui.table_next_column()
                    ImGui.text(f"Vendor Value")
                    
                    PyImGui.table_next_column()
                    ImGui.text(utility.Util.format_currency(mod.vendor_value))
                                
                    PyImGui.table_next_column()
                    ImGui.text(f"Last Checked")
                    PyImGui.table_next_column()
                    time_ago = f"{utility.Util.format_custom_time_ago(datetime.now() - mod.vendor_updated)}\n" if mod.vendor_updated else ""
                    ImGui.text(f"{time_ago}")
                    
                ImGui.end_table()

            PyImGui.pop_style_color(1)
            # ImGui.end_child()
            ImGui.end_tooltip()

    @staticmethod
    def transparent_button(text : str, enabled : bool, width: float, height : float, draw_background : bool = True) -> bool:
        """
        Draws a transparent button with the specified icon and width.
        
        Args:
            icon (str): The icon to display on the button.
            width (int): The width of the button.
        
        Returns:
            bool: True if the button was clicked, False otherwise.
        """
        
        cursor_pos = PyImGui.get_cursor_screen_pos()
        rect = (cursor_pos[0], cursor_pos[1],
                width, height)
        transparent_color = Utils.ColorToTuple(Utils.RGBToColor(0, 0, 0, 0))   
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0, 0)
        PyImGui.push_style_color(
            PyImGui.ImGuiCol.Text,
            Utils.ColorToTuple(
                Utils.RGBToColor(255, 255, 255, 255)
                if enabled
                else Utils.RGBToColor(255, 255, 255, 200)
                if GUI.is_mouse_in_rect(rect)
                else Utils.RGBToColor(255, 255, 255, 125)
            ),
        )
        PyImGui.push_style_color(PyImGui.ImGuiCol.Button,
                                transparent_color)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, Utils.ColorToTuple(
            Utils.RGBToColor(0, 0, 0, 125)) if draw_background else transparent_color)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,
                                transparent_color)

        clicked = PyImGui.button(text, width, height)

        PyImGui.pop_style_var(1)
        PyImGui.pop_style_color(4)

        return clicked

    @staticmethod
    def toggle_button(label: str, v: bool, width=0, height=0,
                    default_color: tuple[float, float, float, float] = (
                        0.153, 0.318, 0.929, 1.0),
                    hover_color: tuple[float, float, float,
                                        float] = (0.6, 0.6, 0.9, 1.0),
                    active_color: tuple[float, float,
                                        float, float] = (0.6, 0.6, 0.6, 1.0)
                    ) -> bool:
        """
        Purpose: Create a toggle button that changes its state and color based on the current state.
        Args:
            label (str): The label of the button.
            v (bool): The current toggle state (True for on, False for off).
        Returns: bool: The new state of the button after being clicked.
        """
        clicked = False

        if v:
            PyImGui.push_style_color(
                PyImGui.ImGuiCol.Button, default_color)
            PyImGui.push_style_color(
                PyImGui.ImGuiCol.ButtonHovered, hover_color)
            PyImGui.push_style_color(
                PyImGui.ImGuiCol.ButtonActive, active_color)
            if width != 0 and height != 0:
                clicked = ImGui.button(label, width, height)
            else:
                clicked = ImGui.button(label)
            PyImGui.pop_style_color(3)
        else:
            if width != 0 and height != 0:
                clicked = ImGui.button(label, width, height)
            else:
                clicked = ImGui.button(label)

        if clicked:
            v = not v

        return v

    # endregion
    
    
@dataclass
class RichToken:
    type: str
    text: str = ""
    color: Optional[tuple] = None
    font: str = "Regular"
    font_size : int = 14
    texture_path: Optional[str] = None
    size: Optional[Tuple[float, float]] = None
    uv0: Optional[Tuple[float, float]] = None
    uv1: Optional[Tuple[float, float]] = None
    
class RichTextTokenizer:
    TAG_RE = re.compile(
        r"(<img[^>]+/>|</?[a-z]+[^>]*>|\{sc\}|\{s\}|\n+|[^\s<\{]+|\s+)",
        re.IGNORECASE
    )

    IMG_RE = re.compile(
        r'path="([^"]+)"|w=(\d+)|h=(\d+)|uv=([\d,]+)',
        re.IGNORECASE
    )
    
    COLOR_RE = re.compile(
    r'<c=([\d\.]+),([\d\.]+),([\d\.]+),([\d\.]+)>',
    re.IGNORECASE
    )

    @staticmethod
    def _parse_rgba(r, g, b, a):
        values = [float(r), float(g), float(b), float(a)]
        if any(v > 1.0 for v in values):
            return tuple(v / 255.0 for v in values)
        return tuple(values)
    
    @staticmethod
    def tokenize(text: str) -> List[RichToken]:
        tokens: List[RichToken] = []

        for part in RichTextTokenizer.TAG_RE.findall(text):
            low = part.lower()

            if low.startswith("<c="):
                m = RichTextTokenizer.COLOR_RE.match(part)
                if m:
                    rgba = RichTextTokenizer._parse_rgba(*m.groups())
                    tokens.append(RichToken(
                        type="color_push",
                        color=rgba
                    ))
                continue
            
            # --- Color pop ---
            if low == "</c>":
                tokens.append(RichToken(type="color_pop"))
                continue
            
            if low.startswith("<img"):
                tex_id = None
                w = h = 16
                uv0 = (0.0, 0.0)
                uv1 = (1.0, 1.0)

                for m in RichTextTokenizer.IMG_RE.finditer(part):
                    if m.group(1):
                        tex_id = m.group(1)
                    if m.group(2):
                        w = int(m.group(2))
                    if m.group(3):
                        h = int(m.group(3))
                    if m.group(4):
                        uvsource = tuple(map(int, m.group(4).split(",")))                        
                        if len(uvsource) == 6:
                            uvs = (uvsource[0], uvsource[1], uvsource[2], uvsource[3], uvsource[4], uvsource[5])
                            uv0, uv1 = Utils.PixelsToUV(*uvs)

                tokens.append(RichToken(
                    type="image",
                    texture_path=tex_id,
                    size=(w, h),
                    uv0=uv0,
                    uv1=uv1
                ))
                continue

            if low == "<b>":
                tokens.append(RichToken(type="font_push", font="Bold"))
                continue
            if low == "</b>":
                tokens.append(RichToken(type="font_pop"))
                continue

            if low == "<i>":
                tokens.append(RichToken(type="font_push", font="Italic"))
                continue
            if low == "</i>":
                tokens.append(RichToken(type="font_pop"))
                continue

            if low in ("<br>", "<brx>"):
                tokens.append(RichToken(type="newline"))
                continue

            if part.isspace():
                tokens.append(RichToken(type="space", text=part))
                continue

            tokens.append(RichToken(type="text", text=part))

        return tokens

class RichTextRenderer:

    @staticmethod
    def render(text: str, max_width: float = 0):
        tokens = RichTextTokenizer.tokenize(text)
        max_width = max_width or PyImGui.get_content_region_avail()[0]

        cursor_x_start = PyImGui.get_cursor_pos_x()
        line_height = PyImGui.get_text_line_height()
        x = cursor_x_start
        y = PyImGui.get_cursor_pos_y()

        for tok in tokens:
            if tok.type == "newline":
                x = cursor_x_start
                y += line_height
                PyImGui.set_cursor_pos(x, y)
                continue

            if tok.type == "font_push":
                ImGui.push_font(tok.font, tok.font_size)
                continue
            if tok.type == "font_pop":
                PyImGui.pop_font()
                continue

            if tok.type == "color_push":
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, tok.color or (1, 1, 1, 1))
                continue
            if tok.type == "color_pop":
                PyImGui.pop_style_color(1)
                continue

            if tok.type == "image":
                if not tok or not tok.texture_path:
                    continue
                
                w, h = tok.size or (16, 16)
                if x + w > cursor_x_start + max_width:
                    x = cursor_x_start
                    y += line_height
                    PyImGui.set_cursor_pos(x, y)

                PyImGui.set_cursor_pos(x, y)
                ImGui.image(tok.texture_path, (w, h), tok.uv0 or (0, 0), tok.uv1 or (1, 1))
                x += w
                continue

            if tok.type in ("text", "space"):
                size = PyImGui.calc_text_size(tok.text)
                if x + size[0] > cursor_x_start + max_width:
                    x = cursor_x_start
                    y += line_height
                    PyImGui.set_cursor_pos(x, y)
                    
                PyImGui.set_cursor_pos(x, y)
                PyImGui.text_unformatted(tok.text)
                x += size[0]

        PyImGui.set_cursor_pos(cursor_x_start, y + line_height)