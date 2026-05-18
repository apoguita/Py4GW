
from typing import Optional, cast

import PyInventory
from PyItem import DyeInfo, ItemModifier, PyItem

from Py4GWCoreLib.Item import Item
from Py4GWCoreLib.enums_src.GameData_enums import Attribute, Profession, DyeColor
from Py4GWCoreLib.enums_src.Item_enums import INVENTORY_BAGS, STORAGE_BAGS, Bags, ItemType, Rarity
from Py4GWCoreLib.native_src.internals import string_table
from Py4GWCoreLib.py4gwcorelib_src.FrameCache import frame_cache
from Py4GWCoreLib.item_data.ItemData import ITEM_DATA, ItemData
from Py4GWCoreLib.item_mods_src.item_mod import ItemMod
from Py4GWCoreLib.item_mods_src.item_modifier_parser import ItemModifierParser
from Py4GWCoreLib.item_mods_src.properties import AttributeRequirement, DamageProperty, TargetItemTypeProperty
from Py4GWCoreLib.item_mods_src.upgrades import Upgrade
from Py4GWCoreLib.native_src.internals.encoded_strings import GWStringEncoded


class _UnsetType:
    __slots__ = ()


_UNSET = _UnsetType()


def get_item_bag(item_id: int, item_instance: Optional[PyItem] = None) -> Bags:
    item = item_instance if item_instance and item_instance.item_id == item_id else Item.item_instance(item_id) if item_id > 0 else None

    if not item or not item.IsItemValid(item_id):
        return Bags.NoBag

    bags_to_check : list[Bags] = []
    if item.is_inventory_item:
        bags_to_check.extend(INVENTORY_BAGS)
        
    if item.is_storage_item:
        bags_to_check.extend(STORAGE_BAGS)

    for bag in bags_to_check:
        inventory_bag = PyInventory.Bag(bag.value, bag.name)
        if inventory_bag.FindItemById(item_id):
            return bag

    return Bags.NoBag


class _LazyParsedItemData:
    __slots__ = (
        "modifiers",
        "properties",
        "prefix",
        "suffix",
        "inscription",
        "inherent",
        "attribute",
        "requirement",
        "min_damage",
        "max_damage",
        "target_item_type",
    )

    def __init__(
        self,
        modifiers: list[ItemModifier],
        properties,
        prefix: Optional[Upgrade],
        suffix: Optional[Upgrade],
        inscription: Optional[Upgrade],
        inherent: Optional[list[Upgrade]],
        attribute: Attribute,
        requirement: int,
        min_damage: int,
        max_damage: int,
        target_item_type: ItemType,
    ):
        self.modifiers = modifiers
        self.properties = properties
        self.prefix = prefix
        self.suffix = suffix
        self.inscription = inscription
        self.inherent = inherent
        self.attribute = attribute
        self.requirement = requirement
        self.min_damage = min_damage
        self.max_damage = max_damage
        self.target_item_type = target_item_type


class ItemSnapshot:
    __slots__ = (
        "id",
        "is_valid",
        "_name_enc",
        "_singular_name",
        "_complete_name_enc",
        "_names",
        "__bag",
        "model_id",
        "model_file_id",
        "gw_dat_file_path",
        "item_type",
        "is_weapon",
        "is_armor",
        "rarity",
        "profession",
        "is_identified",
        "value",
        "is_usable",
        "is_salvageable",
        "is_salvage_kit",
        "is_perfect_salvage_kit",
        "is_inscribable",
        "is_prefix_upgradable",
        "is_suffix_upgradable",
        "quantity",
        "uses",
        "_is_stackable",
        "is_customized",
        "dye_info",
        "slot",
        "is_inventory_item",
        "is_storage_item",
        "is_material",
        "is_rare_material",
        "is_material_salvageable",
        "color",
        "_parsed_item_data",
        "_data",
    )

    def __init__(self, item_id: int, item_instance: Optional[PyItem] = None, bag: Optional[Bags] = None):
        item = item_instance if item_instance and item_id == item_instance.item_id else Item.item_instance(item_id) if item_id > 0 else None

        self.id: int = item_id
        self.is_valid: bool = item.IsItemValid(item_id) if item else False

        self._name_enc: Optional[bytes] | _UnsetType = _UNSET
        self._singular_name: Optional[bytes] | _UnsetType = _UNSET
        self._complete_name_enc: Optional[bytes] | _UnsetType = _UNSET
        self._names: GWStringEncoded | _UnsetType = _UNSET

        self.__bag: Optional[Bags] = bag if item and (item.is_inventory_item or item.is_storage_item) else Bags.NoBag

        self.model_id: int = item.model_id if item else -1
        self.model_file_id: int = item.model_file_id if item else -1
        self.gw_dat_file_path = f"gwdat://{self.model_file_id}" if self.model_file_id > 0 else ""

        self.item_type: ItemType = ItemType(item.item_type.ToInt()) if item else ItemType.Unknown
        self.is_weapon = self.item_type.is_weapon_type() if item else False
        self.is_armor = self.item_type.is_armor_type() if item else False
        
        self.rarity: Rarity = Rarity(item.rarity.value) if item and item.rarity and item.rarity.value in Rarity._value2member_map_ else Rarity.White
        self.profession: Profession = Profession(item.profession) if item and item.profession in Profession else Profession._None

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
        self._is_stackable: bool | _UnsetType = _UNSET
        self.is_customized: bool = item.is_customized if item else False
        self.dye_info: DyeInfo = item.dye_info if item else DyeInfo()

        self.slot: int = item.slot if item else -1
        self.is_inventory_item: bool = item.is_inventory_item if item else False
        self.is_storage_item: bool = item.is_storage_item if item else False

        self.is_material = item.is_material if item else False
        self.is_rare_material = item.is_rare_material if item else False
        self.is_material_salvageable = item.is_material_salvageable if item else False

        self.color: DyeColor = DyeColor.from_dye_info(self.dye_info)

        self._parsed_item_data: _LazyParsedItemData | _UnsetType = _UNSET
        self._data: Optional[ItemData] | _UnsetType = _UNSET

    @classmethod
    @frame_cache(category="LazyItemSnapshot", source_lib="from_item_id")
    def from_item_id(cls, item_id: int, item_instance: Optional[PyItem] = None) -> Optional['ItemSnapshot']:
        item = item_instance if item_instance and item_id == item_instance.item_id else Item.item_instance(item_id) if item_id > 0 else None
        is_valid = item.IsItemValid(item.item_id) if item else False

        return cls(item.item_id, item) if item and is_valid else None

    @classmethod
    def create(cls, item_id: int, item_instance: Optional[PyItem] = None, bag: Optional[Bags] = None) -> Optional['ItemSnapshot']:
        item = item_instance if item_instance is not None else Item.item_instance(item_id) if item_id > 0 else None
        is_valid = item.IsItemValid(item_id) if item else False

        return cls(item_id, item, bag) if is_valid else None

    def _load_name_bytes(self, loader) -> Optional[bytes]:
        return bytes(loader(self.id)) if self.id > 0 and self.is_valid else None

    def _get_parsed_item_data(self) -> _LazyParsedItemData:
        if self._parsed_item_data is _UNSET:
            modifiers: list[ItemModifier] = Item.Customization.Modifiers.GetModifiers(self.id) if self.id > 0 and self.is_valid else []
            parser = ItemModifierParser(modifiers, self.rarity)
            properties = parser.get_properties()

            prefix, suffix, inscription, inherent = ItemMod.get_item_upgrades_from_properties(properties, self.rarity)

            requirement = next((p for p in properties if isinstance(p, AttributeRequirement)), None)
            damage = next((p for p in properties if isinstance(p, DamageProperty)), None)
            target_item_type = next((p for p in properties if isinstance(p, TargetItemTypeProperty)), None)

            self._parsed_item_data = _LazyParsedItemData(
                modifiers=modifiers,
                properties=properties,
                prefix=prefix,
                suffix=suffix,
                inscription=inscription,
                inherent=inherent,
                attribute=requirement.attribute if requirement else Attribute.None_,
                requirement=requirement.attribute_level if requirement else 0,
                min_damage=damage.min_damage if damage else 0,
                max_damage=damage.max_damage if damage else 0,
                target_item_type=target_item_type.item_type if target_item_type else ItemType.Unknown,
            )

        return cast(_LazyParsedItemData, self._parsed_item_data)
    
    @property
    def name_enc(self) -> Optional[bytes]:
        if self._name_enc is _UNSET:
            self._name_enc = self._load_name_bytes(PyItem.GetNameEnc)

        return cast(Optional[bytes], self._name_enc)

    @property
    def singular_name_enc(self) -> Optional[bytes]:
        if self._singular_name is _UNSET:
            self._singular_name = self._load_name_bytes(PyItem.GetSingleItemName)

        return cast(Optional[bytes], self._singular_name)

    @property
    def complete_name_enc(self) -> Optional[bytes]:
        if self._complete_name_enc is _UNSET:
            self._complete_name_enc = self._load_name_bytes(PyItem.GetCompleteNameEnc)

        return cast(Optional[bytes], self._complete_name_enc)

    @property
    def names(self) -> GWStringEncoded:
        if self._names is _UNSET:
            self._names = GWStringEncoded(self.name_enc or bytes(), "Unknown Item")

        return cast(GWStringEncoded, self._names)

    @property
    def info_string(self) -> str:
        return "DISABLED"

    @property
    def name(self) -> str:
        return string_table.decode(self.name_enc) if self.name_enc else ""

    @property
    def singular_name(self) -> str:
        return string_table.decode(self.singular_name_enc) if self.singular_name_enc else ""
    
    @property
    def complete_name(self) -> str:
        return string_table.decode(self.complete_name_enc) if self.complete_name_enc else ""

    @property
    def bag(self) -> Bags:
        if self.__bag is None:
            self.__bag = get_item_bag(self.id) if self.is_inventory_item or self.is_storage_item else Bags.NoBag

        return self.__bag

    @property
    def is_stackable(self) -> bool:
        if self._is_stackable is _UNSET:
            self._is_stackable = Item.Customization.IsStackable(self.id) if self.id > 0 else False

        return cast(bool, self._is_stackable)

    @property
    def modifiers(self) -> list[ItemModifier]:
        return self._get_parsed_item_data().modifiers

    @property
    def properties(self):
        return self._get_parsed_item_data().properties

    @property
    def has_upgrades(self) -> bool:
        parsed_data = self._get_parsed_item_data()
        return bool(parsed_data.prefix or parsed_data.suffix or parsed_data.inscription or (parsed_data.inherent and len(parsed_data.inherent) > 0))

    @property
    def prefix(self) -> Optional[Upgrade]:
        return self._get_parsed_item_data().prefix

    @property
    def suffix(self) -> Optional[Upgrade]:
        return self._get_parsed_item_data().suffix

    @property
    def inscription(self) -> Optional[Upgrade]:
        return self._get_parsed_item_data().inscription

    @property
    def inherents(self) -> Optional[list[Upgrade]]:
        return self._get_parsed_item_data().inherent

    @property
    def attribute(self) -> Attribute:
        return self._get_parsed_item_data().attribute

    @property
    def requirement(self) -> int:
        return self._get_parsed_item_data().requirement

    @property
    def min_damage(self) -> int:
        return self._get_parsed_item_data().min_damage

    @property
    def max_damage(self) -> int:
        return self._get_parsed_item_data().max_damage

    @property
    def target_item_type(self) -> ItemType:
        return self._get_parsed_item_data().target_item_type

    @property
    def data(self) -> Optional[ItemData]:
        if self._data is _UNSET:
            self._data = ITEM_DATA.get_item_data(model_id=self.model_id, item_type=self.item_type) if self.model_id != -1 else None

        return cast(Optional[ItemData], self._data)

    def same_kind_as(self, other: 'ItemSnapshot') -> bool:
        return self.model_id == other.model_id and self.item_type == other.item_type and (self.item_type != ItemType.Dye or self.color == other.color)
    
    def update(self):
        item = Item.item_instance(self.id) if self.id > 0 else None
        self.is_valid = item.IsItemValid(self.id) if item else False

        self._parsed_item_data = _UNSET
        self._data = _UNSET
        self._name_enc = _UNSET
        self._singular_name = _UNSET
        self._complete_name_enc = _UNSET
        self._names = _UNSET
        self._is_stackable = _UNSET

        if not self.is_valid or not item:
            self.__bag = Bags.NoBag
            return

        self.model_id = item.model_id
        self.model_file_id = item.model_file_id
        self.gw_dat_file_path = f"gwdat://{self.model_file_id}" if self.model_file_id > 0 else ""

        self.item_type = ItemType(item.item_type.ToInt())
        self.rarity = Rarity(item.rarity.value) if item.rarity and item.rarity.value in Rarity._value2member_map_ else Rarity.White
        self.profession = Profession(item.profession) if item.profession in Profession else Profession._None

        self.is_identified = item.is_identified
        self.value = item.value
        self.is_usable = item.is_usable
        self.is_salvageable = item.is_salvageable
        self.is_salvage_kit = item.is_salvage_kit
        self.is_perfect_salvage_kit = item.is_perfect_salvage_kit
        self.is_inscribable = item.is_inscribable
        self.is_prefix_upgradable = item.is_prefix_upgradable
        self.is_suffix_upgradable = item.is_suffix_upgradable
        self.quantity = item.quantity
        self.uses = item.uses
        self.is_customized = item.is_customized
        self.dye_info = item.dye_info
        self.slot = item.slot
        self.is_inventory_item = item.is_inventory_item
        self.is_storage_item = item.is_storage_item
        self.is_material = item.is_material
        self.is_rare_material = item.is_rare_material
        self.is_material_salvageable = item.is_material_salvageable
        self.color = DyeColor.from_dye_info(self.dye_info)
        self.__bag = None if item.is_inventory_item or item.is_storage_item else Bags.NoBag

    @staticmethod
    @frame_cache(category="ItemSnapshot", source_lib="get_bag_snapshot")
    def get_bag_snapshot(bag: Bags) -> dict[int, Optional['ItemSnapshot']]:
        inventory_bag = PyInventory.Bag(bag.value, bag.name)
        bag_snapshot: dict[int, Optional[ItemSnapshot]] = {}

        bag_size = inventory_bag.GetSize()

        for slot in range(bag_size):
            bag_snapshot[slot] = None

        for item in inventory_bag.GetItems():
            slot = item.slot  # real slot of the item
            bag_snapshot[slot] = ItemSnapshot.from_item_id(item.item_id, item) if item else None

        return bag_snapshot
    
    @staticmethod
    @frame_cache(category="ItemSnapshot", source_lib="get_inventory_snapshot")
    def get_inventory_snapshot(start_bag: Bags, end_bag: Bags) -> dict[Bags, dict[int, Optional['ItemSnapshot']]]:
        bags = [Bags(bag_id) for bag_id in range(start_bag.value, end_bag.value + 1)]
        return ItemSnapshot.get_bags_snapshot(bags)
    
    @staticmethod
    @frame_cache(category="ItemSnapshot", source_lib="get_bags_snapshot")
    def get_bags_snapshot(bags: list[Bags]) -> dict[Bags, dict[int, Optional['ItemSnapshot']]]:
        snapshot = {}

        for bag in bags:
            snapshot[bag] = ItemSnapshot.get_bag_snapshot(bag)

        return snapshot
    
    @staticmethod
    @frame_cache(category="ItemSnapshot", source_lib="get_items")
    def get_items(bags: list[Bags]) -> list['ItemSnapshot']:
        snapshot = ItemSnapshot.get_bags_snapshot(bags)
        items: list[ItemSnapshot] = []

        for bag in snapshot.values():
            for item in bag.values():
                if item is not None and item.is_valid:
                    items.append(item)

        return items