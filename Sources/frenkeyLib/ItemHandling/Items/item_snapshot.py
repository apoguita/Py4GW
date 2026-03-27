
from typing import Optional

import Py4GW
import PyInventory
from PyItem import DyeInfo, PyItem

from Py4GWCoreLib.Item import Bag, Item
from Py4GWCoreLib.enums_src.GameData_enums import Attribute, Profession, DyeColor
from Py4GWCoreLib.enums_src.Item_enums import ItemType, Rarity
from Py4GWCoreLib.native_src.internals import string_table
from Sources.frenkeyLib.ItemHandling.Items.ItemData import ITEM_DATA, ItemData
from Sources.frenkeyLib.ItemHandling.Items.types import INVENTORY_BAGS, STORAGE_BAGS
from Sources.frenkeyLib.ItemHandling.Mods.ItemMod import ItemMod
from Sources.frenkeyLib.ItemHandling.Mods.item_modifier_parser import ItemModifierParser
from Sources.frenkeyLib.ItemHandling.Mods.properties import AttributeRequirement, DamageProperty, TargetItemTypeProperty
from Sources.frenkeyLib.ItemHandling.Mods.upgrades import Upgrade
from Sources.frenkeyLib.ItemHandling.encoded_strings import GWStringEncoded


def get_item_bag(item_id: int, item_instance: Optional[PyItem] = None) -> Bag:
    item = item_instance if item_instance and item_instance.item_id == item_id else Item.item_instance(item_id) if item_id > 0 else None

    if not item or not item.IsItemValid(item_id):
        return Bag.NoBag

    bags_to_check : list[Bag] = []
    if item.is_inventory_item:
        bags_to_check.extend(INVENTORY_BAGS)
        
    if item.is_storage_item:
        bags_to_check.extend(STORAGE_BAGS)

    for bag in bags_to_check:
        inventory_bag = PyInventory.Bag(bag.value, bag.name)
        if inventory_bag.FindItemById(item_id):
            return bag

    return Bag.NoBag


class ItemSnapshot:
    def __init__(self, item_id: int, item_instance: Optional[PyItem] = None, bag: Optional[Bag] = None):
        item = item_instance if item_instance and item_id == item_instance.item_id else Item.item_instance(item_id) if item_id > 0 else None
        
        self.id: int = item_id
        self.is_valid: bool = item.IsItemValid(item_id) if item else False
                
        self.name_enc = bytes(PyItem.GetNameEnc(item_id)) if item_id > 0 and self.is_valid else None
        self.info_string = "DISABLED"  # PyItem.GetInfoString(item_id) if item_id > 0 and self.is_valid else None
        self.singular_name = bytes(PyItem.GetSingleItemName(item_id)) if item_id > 0 and self.is_valid else None
        self.complete_name_enc = bytes(PyItem.GetCompleteNameEnc(item_id)) if item_id > 0 and self.is_valid else None
        self.names : GWStringEncoded = GWStringEncoded(self.name_enc or bytes(), "Unknown Item")
        
        self.bag: Bag = bag if bag is not None else get_item_bag(item_id, item) if item and (item.is_inventory_item or item.is_storage_item) else Bag.NoBag
                
        self.model_id: int = item.model_id if item else -1
        self.model_file_id: int = item.model_file_id if item else -1
        self.gw_dat_file_path = f"gwdat://{self.model_file_id}" if self.model_file_id > 0 else ""
        
        self.item_type: ItemType = ItemType(
            item.item_type.ToInt()) if item else ItemType.Unknown
        self.rarity: Rarity = Rarity(item.rarity.value) if item and item.rarity and item.rarity.value in Rarity._value2member_map_ else Rarity.White
        self.profession : Profession = Profession(
            item.profession) if item and item.profession in Profession else Profession._None
        
        self.is_identified: bool = item.is_identified if item else False
        self.value: int = item.value if item else 0
        self.is_usable: bool = item.is_usable if item else False
        self.is_salvageable: bool = item.is_salvageable if item else False
        self.is_salvage_kit: bool = item.is_salvage_kit if item else False
        self.is_perfect_salvage_kit: bool = item.is_perfect_salvage_kit if item else False
        
        self.is_inscribable: bool = item.is_inscribable if item else False        
        self.is_prefix_upgradable: bool = item.is_prefix_upgradable if item else False
        self.is_suffix_upgradable: bool = item.is_suffix_upgradable if item else False
        
        self.quantity: int = item.quantity if item else 0
        self.uses: int = item.uses if item else 0
        self.is_stackable: bool = Item.Customization.IsStackable(item_id) if item_id > 0 else False
        self.is_customized: bool = item.is_customized if item else False
        self.dye_info: DyeInfo = item.dye_info if item else DyeInfo()
        
        self.slot: int = item.slot if item else -1
        self.is_inventory_item: bool = item.is_inventory_item if item else False
        self.is_storage_item: bool = item.is_storage_item if item else False
        
        self.is_material = item.is_material if item else False
        self.is_rare_material = item.is_rare_material if item else False
        self.is_material_salvageable = item.is_material_salvageable if item else False

        self.color: DyeColor = ItemSnapshot.get_color_from_info(self.dye_info)

        self.attribute: Attribute = Attribute.None_
        self.requirement: int = 0
        
        self.prefix : Optional[Upgrade] = None
        self.suffix : Optional[Upgrade] = None
        self.inscription : Optional[Upgrade] = None
        
        self.modifiers = Item.Customization.Modifiers.GetModifiers(item_id)
        parser = ItemModifierParser(self.modifiers, self.rarity)
        self.properties = parser.get_properties()
        
        self.prefix, self.suffix, self.inscription = ItemMod.get_item_upgrades_from_properties(self.properties, self.rarity)
        
        requirement = next((p for p in self.properties if isinstance(p, AttributeRequirement)), None)        
        self.attribute = requirement.attribute if requirement else Attribute.None_
        self.requirement = requirement.attribute_level if requirement else 0
        
        damage = next((p for p in self.properties if isinstance(p, DamageProperty)), None)
        self.min_damage : int = damage.min_damage if damage else 0
        self.max_damage : int = damage.max_damage if damage else 0
        
        target_item_type = next((p for p in self.properties if isinstance(p, TargetItemTypeProperty)), None)
        self.target_item_type : ItemType = target_item_type.item_type if target_item_type else ItemType.Unknown
        
        self.data : Optional[ItemData] = ITEM_DATA.get_item_data(model_id=self.model_id, item_type=self.item_type) if self.model_id != -1 else None
        
    @property
    def name(self) -> str:
        return string_table.decode(self.name_enc) if self.name_enc else ""

    def same_kind_as(self, other: 'ItemSnapshot') -> bool:
        """
        Check if this item snapshot represents the same kind of item as another snapshot.
        Args:
            other (ItemSnapshot): The other item snapshot to compare against.   
        Returns:
            bool: True if both snapshots represent the same item kind, False otherwise.
        """
        return self.model_id == other.model_id and self.item_type == other.item_type and (self.item_type != ItemType.Dye or self.color == other.color)
    
    def update(self):
        item = Item.item_instance(self.id) if self.id > 0 else None
        self.is_valid = item.IsItemValid(self.id) if item else False
        
        if not self.is_valid or not item:
            return
        
        self.is_identified = item.is_identified
        self.quantity = item.quantity
        self.uses = item.uses
        self.is_customized = item.is_customized
        self.dye_info = item.dye_info
        self.slot = item.slot
        self.is_inventory_item = item.is_inventory_item
        self.is_storage_item = item.is_storage_item
        self.bag = get_item_bag(self.id, item) if item.is_inventory_item or item.is_storage_item else Bag.NoBag
        self.color = ItemSnapshot.get_color_from_info(self.dye_info)
        
        self.modifiers = Item.Customization.Modifiers.GetModifiers(self.id)
        
        parser = ItemModifierParser(self.modifiers, self.rarity)
        self.properties = parser.get_properties()
        self.prefix, self.suffix, self.inscription = ItemMod.get_item_upgrades_from_properties(self.properties, self.rarity)
        
    
    @staticmethod
    def get_color_from_info(dye_info: Optional[DyeInfo]) -> DyeColor:
        """
        Get the dye color associated with the dye info.
        Args:
            dye_info (DyeInfo): The dye information.
        Returns:
            DyeColor: The dye color of the item.
        """

        if dye_info is not None:
            color_id = dye_info.dye1.ToInt() if dye_info.dye1 else -1
            color = DyeColor(color_id) if color_id != -1 else None
            return color if color is not None else DyeColor.NoColor

        return DyeColor.NoColor
    
    @classmethod
    def create(cls, item_id: int, item_instance: Optional[PyItem] = None, bag: Optional[Bag] = None) -> 'Optional[ItemSnapshot]':
        """
        Create an item snapshot for the given item ID and instance.
        Args:
            item_id (int): The ID of the item to create a snapshot for.
            item_instance (Optional[PyItem]): An optional PyItem instance to use for creating the snapshot. If not provided, a new instance will be created based on the item ID.
        Returns:
            ItemSnapshot: The created item snapshot.
        """
        item = item_instance if item_instance is not None else Item.item_instance(item_id) if item_id > 0 else None
        is_valid = item.IsItemValid(item_id) if item else False
        
        return cls(item_id, item, bag) if is_valid else None
