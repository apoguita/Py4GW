from __future__ import annotations

from enum import IntEnum
from typing import Any, ClassVar, Optional

import Py4GW

from Py4GWCoreLib.enums_src.GameData_enums import DyeColor
from Py4GWCoreLib.enums_src.Item_enums import ItemType, Rarity
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Sources.frenkeyLib.ItemHandling.Items.ItemCache import ITEM_CACHE
from Sources.frenkeyLib.ItemHandling.Items.ItemData import DAMAGE_RANGES
from Sources.frenkeyLib.ItemHandling.Items.item_snapshot import ItemSnapshot
from Sources.frenkeyLib.ItemHandling.Mods.properties import ItemProperty
from Sources.frenkeyLib.ItemHandling.Mods.upgrades import HeavyUpgrade, Upgrade
from Sources.frenkeyLib.ItemHandling.Rules.types import ItemAction

PropertyFilter = ItemProperty | dict[str, int | str]

class RulePriority(IntEnum):    
    WeaponSkinRule = 1000
    ItemSkinRule = 900
    ModelIdRule = 800
    UpgradeRule = 700
    WeaponTypeRule = 600
    DyesRule = 400
    SalvagesToMaterialRule = 350
    ItemTypeAndRarityRule = 300
    ItemTypesRule = 200
    RaritiesRule = 100
    Base = 0

class BaseRule:
    _registry: ClassVar[dict[str, type["BaseRule"]]] = {}
    priority: RulePriority = RulePriority.Base

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseRule._registry[cls.__name__] = cls

    def __init__(self, name: str, action: ItemAction = ItemAction.NONE):
        self.name = name
        self.action: ItemAction = action

    def is_valid(self) -> bool:
        return self.action != ItemAction.NONE

    def applies(self, item_id: int) -> bool:
        raise NotImplementedError("Subclasses must implement the applies method.")

    def get_item(self, item_id: int) -> Optional[ItemSnapshot]:
        return ITEM_CACHE.get_item_snapshot(item_id)

    def get_priority_score(self) -> int:
        return self.priority.value

    def _serialize_data(self) -> dict[str, Any]:
        return {}

    def _deserialize_data(self, data: dict[str, Any]) -> None:
        return

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "rule_type": type(self).__name__,
            "name": self.name,
            "action": self.action.name,
        }
        payload.update(self._serialize_data())
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> BaseRule | None:
        rule_type_name = str(payload.get("rule_type", ""))
        rule_cls = cls._registry.get(rule_type_name, None)
        if rule_cls is None:
            return None

        rule = rule_cls(str(payload.get("name", "Unnamed Rule")))

        action_name = str(payload.get("action", ItemAction.NONE.name))
        if action_name in ItemAction.__members__:
            rule.action = ItemAction[action_name]

        rule._deserialize_data(payload)
        return rule

class ModelIdRule(BaseRule):
    priority = RulePriority.ModelIdRule
    
    """
    ***CAUTION***: This rule is ***not recommended*** for general use, as model IDs can be shared between different items and item types!
    """

    def __init__(self, name: str, action: ItemAction = ItemAction.NONE, model_id: Optional[ModelID] = None):
        super().__init__(name, action)
        self.model_id: ModelID | None = model_id

    def is_valid(self) -> bool:
        return super().is_valid() and self.model_id is not None

    def applies(self, item_id):
        if not self.is_valid():
            return False

        item = self.get_item(item_id)
        return item.model_id == self.model_id.value if item and self.model_id else False

    def _serialize_data(self) -> dict[str, Any]:
        return {"model_id": int(self.model_id.value) if self.model_id is not None else None}

    def _deserialize_data(self, data: dict[str, Any]) -> None:
        model_id = data.get("model_id", None)
        if isinstance(model_id, int):
            try:
                self.model_id = ModelID(model_id)
            except ValueError:
                self.model_id = None

class ItemTypesRule(BaseRule):
    priority = RulePriority.ItemTypesRule
    
    """
    A rule that checks if an item :class:`ItemType` is a specified item type.
    """

    def __init__(self, name: str, action: ItemAction = ItemAction.NONE, item_types: Optional[list[ItemType]] = None):
        super().__init__(name, action)
        self.item_types: list[ItemType] = item_types if item_types is not None else []

    def is_valid(self) -> bool:
        return super().is_valid() and len(self.item_types) > 0

    def applies(self, item_id: int) -> bool:
        if not self.is_valid():
            return False

        item = self.get_item(item_id)
        return item.item_type in self.item_types if item else False

    def _serialize_data(self) -> dict[str, Any]:
        return {"item_types": [item_type.name for item_type in self.item_types]}

    def _deserialize_data(self, data: dict[str, Any]) -> None:
        self.item_types = [
            ItemType[name]
            for name in data.get("item_types", [])
            if isinstance(name, str) and name in ItemType.__members__
        ]

class RaritiesRule(BaseRule):
    priority = RulePriority.RaritiesRule
    
    """
    A rule that checks if an item :class:`Rarity` is a specified rarity.
    """

    def __init__(self, name: str, action: ItemAction = ItemAction.NONE, rarities: Optional[list[Rarity]] = None):
        super().__init__(name, action)
        self.rarities: list[Rarity] = rarities if rarities is not None else []

    def is_valid(self) -> bool:
        return super().is_valid() and len(self.rarities) > 0

    def applies(self, item_id: int) -> bool:
        if not self.is_valid():
            return False

        item = self.get_item(item_id)
        return item.rarity in self.rarities if item else False

    def _serialize_data(self) -> dict[str, Any]:
        return {"rarities": [rarity.name for rarity in self.rarities]}

    def _deserialize_data(self, data: dict[str, Any]) -> None:
        self.rarities = [
            Rarity[name]
            for name in data.get("rarities", [])
            if isinstance(name, str) and name in Rarity.__members__
        ]

class DyesRule(BaseRule):
    priority = RulePriority.DyesRule
    
    """
    A rule if an item is a **Vial of Dye** of a specific :class:`DyeColor`. This is determined by the item's dye color.
    """

    def __init__(self, name: str, action: ItemAction = ItemAction.NONE, dye_colors: Optional[list[DyeColor]] = None):
        super().__init__(name, action)
        self.dye_colors: list[DyeColor] = dye_colors if dye_colors is not None else []

    def is_valid(self) -> bool:
        return super().is_valid() and len(self.dye_colors) > 0

    def applies(self, item_id: int) -> bool:
        if not self.is_valid():
            return False

        item = self.get_item(item_id)
        return item.color in self.dye_colors and item.item_type == ItemType.Dye if item else False

    def _serialize_data(self) -> dict[str, Any]:
        return {"dye_colors": [color.name for color in self.dye_colors]}

    def _deserialize_data(self, data: dict[str, Any]) -> None:
        self.dye_colors = [
            DyeColor[name]
            for name in data.get("dye_colors", [])
            if isinstance(name, str) and name in DyeColor.__members__
        ]

class ItemSkinRule(BaseRule):
    priority = RulePriority.ItemSkinRule
    
    """
    A rule that checks if an item has a specific skin.

    This is determined by the item's skin property, which is derived
    from the item data in :file:`items.json`.

    See the raw file at `Sources/frenkeyLib/ItemHandling/Items/items.json`
    """

    def __init__(self, name: str, action: ItemAction = ItemAction.NONE, item_skins: Optional[list[str]] = None):
        super().__init__(name, action)
        self.item_skins: list[str] = []

    def is_valid(self) -> bool:
        return super().is_valid() and len(self.item_skins) > 0

    def applies(self, item_id: int) -> bool:
        if not self.is_valid():
            return False

        item = self.get_item(item_id)
        return item.data is not None and item.data.skin in self.item_skins if item else False

    def _serialize_data(self) -> dict[str, Any]:
        return {"item_skins": list(self.item_skins)}

    def _deserialize_data(self, data: dict[str, Any]) -> None:
        self.item_skins = [str(name) for name in data.get("item_skins", []) if isinstance(name, str)]

class ItemTypeAndRarityRule(BaseRule):
    priority = RulePriority.ItemTypeAndRarityRule
    
    """
    A rule that checks if an item is a specific item type and rarity.
    """

    def __init__(self, name: str, action: ItemAction = ItemAction.NONE, item_types: Optional[list[ItemType]] = None, rarities: Optional[list[Rarity]] = None):
        super().__init__(name, action)
        self.item_types: list[ItemType] = item_types if item_types is not None else []
        self.rarities: list[Rarity] = rarities if rarities is not None else []

    def is_valid(self) -> bool:
        return super().is_valid() and len(self.item_types) > 0 and len(self.rarities) > 0

    def applies(self, item_id: int) -> bool:
        if not self.is_valid():
            return False

        item = self.get_item(item_id)
        return item.item_type in self.item_types and item.rarity in self.rarities if item else False

    def _serialize_data(self) -> dict[str, Any]:
        return {
            "item_types": [item_type.name for item_type in self.item_types],
            "rarities": [rarity.name for rarity in self.rarities],
        }

    def _deserialize_data(self, data: dict[str, Any]) -> None:
        self.item_types = [
            ItemType[name]
            for name in data.get("item_types", [])
            if isinstance(name, str) and name in ItemType.__members__
        ]
        self.rarities = [
            Rarity[name]
            for name in data.get("rarities", [])
            if isinstance(name, str) and name in Rarity.__members__
        ]

class WeaponSkinRule(BaseRule):
    priority = RulePriority.WeaponSkinRule
    
    """
    A rule that checks if a weapon has a specific skin. This is determined by the item's skin property, which is derived from the item data in :file:`items.json`.

    In addition, the rule can check if the item's requirement is within a specified range and if the item's damage range is within a certain range.
    """

    def __init__(self, name: str, action: ItemAction = ItemAction.NONE, weapon_skins: Optional[list[str]] = None, requirement_min: int = 0, requirement_max: int = 0, only_max_damage: bool = True, properties: Optional[list[PropertyFilter]] = None):
        super().__init__(name, action)

        self.weapon_skins: list[str] = weapon_skins if weapon_skins is not None else []
        self.requirement_min: int = requirement_min
        self.requirement_max: int = requirement_max
        self.only_max_damage: bool = only_max_damage

        self.properties: list[PropertyFilter] = properties if properties is not None else []

    def is_valid(self) -> bool:
        return super().is_valid() and len(self.weapon_skins) > 0

    def applies(self, item_id: int) -> bool:
        if not self.is_valid():
            return False

        item = self.get_item(item_id)
        if item is None or item.data is None or item.data.skin not in self.weapon_skins:
            return False

        if self.requirement_min > item.requirement or self.requirement_max < item.requirement:
            return False

        if self.only_max_damage:
            damage_for_requirement = DAMAGE_RANGES.get(item.item_type, {}).get(item.model_id, (0, 0))
            if item.max_damage < damage_for_requirement[1] or item.min_damage < damage_for_requirement[0]:
                return False

        if len(self.properties) > 0:
            item_properties = {type(p): p for p in item.properties}
            item_properties_by_name = {type(p).__name__: p for p in item.properties}
            for prop in self.properties:
                if isinstance(prop, dict):
                    property_type_name = str(prop.get("property_type", ""))
                    expected_modifier_arg = int(prop.get("modifier_arg", -1))

                    if property_type_name not in item_properties_by_name:
                        return False

                    # item_prop = item_properties_by_name[property_type_name]
                    # if item_prop.modifier.arg != expected_modifier_arg:
                    #     return False
                else:
                    if type(prop) not in item_properties:
                        return False

                    # item_prop = item_properties[type(prop)]
                    # if prop.modifier.arg != item_prop.modifier.arg:
                    #     return False

        return True

    def _serialize_data(self) -> dict[str, Any]:
        properties: list[dict[str, int | str]] = []
        for prop in self.properties:
            if isinstance(prop, dict):
                properties.append(
                    {
                        "property_type": str(prop.get("property_type", "")),
                        "modifier_arg": int(prop.get("modifier_arg", -1)),
                    }
                )
            else:
                properties.append({"property_type": type(prop).__name__, "modifier_arg": int(prop.modifier.arg)})

        return {
            "weapon_skins": list(self.weapon_skins),
            "requirement_min": self.requirement_min,
            "requirement_max": self.requirement_max,
            "only_max_damage": self.only_max_damage,
            "properties": properties,
        }

    def _deserialize_data(self, data: dict[str, Any]) -> None:
        self.weapon_skins = [str(name) for name in data.get("weapon_skins", []) if isinstance(name, str)]
        self.requirement_min = int(data.get("requirement_min", 0))
        self.requirement_max = int(data.get("requirement_max", 0))
        self.only_max_damage = bool(data.get("only_max_damage", True))
        self.properties = [
            {
                "property_type": str(prop.get("property_type", "")),
                "modifier_arg": int(prop.get("modifier_arg", -1)),
            }
            for prop in data.get("properties", [])
            if isinstance(prop, dict)
        ]

class WeaponTypeRule(BaseRule):
    priority = RulePriority.WeaponTypeRule
    
    """
    A rule that checks if an item is a specific weapon type, requirement, damage range and specific properties.
    """

    def __init__(self, name: str, action: ItemAction = ItemAction.NONE, item_type: Optional[ItemType] = None, requirement_min: int = 0, requirement_max: int = 0, only_max_damage: bool = True, properties: Optional[list[PropertyFilter]] = None):
        super().__init__(name, action)

        self.item_type: ItemType | None = item_type
        self.requirement_min: int = requirement_min
        self.requirement_max: int = requirement_max
        self.only_max_damage: bool = only_max_damage

        self.properties: list[PropertyFilter] = properties if properties is not None else []

    def is_valid(self) -> bool:
        return super().is_valid() and self.item_type is not None

    def applies(self, item_id: int) -> bool:
        if not self.is_valid():
            return False

        item = self.get_item(item_id)
        if item is None or item.data is None or item.item_type != self.item_type:
            return False

        if self.requirement_min > item.requirement or self.requirement_max < item.requirement:
            return False

        if self.only_max_damage:
            damage_for_requirement = DAMAGE_RANGES.get(item.item_type, {}).get(item.model_id, (0, 0))
            if item.max_damage < damage_for_requirement[1] or item.min_damage < damage_for_requirement[0]:
                return False

        if len(self.properties) > 0:
            item_properties = {type(p): p for p in item.properties}
            item_properties_by_name = {type(p).__name__: p for p in item.properties}
            
            for prop in self.properties:
                if isinstance(prop, dict):
                    property_type_name = str(prop.get("property_type", ""))
                    expected_modifier_arg = int(prop.get("modifier_arg", -1))

                    if property_type_name not in item_properties_by_name:
                        return False

                    item_prop = item_properties_by_name[property_type_name]
                    # if item_prop.modifier.arg != expected_modifier_arg:
                    #     return False
                else:
                    if type(prop) not in item_properties:
                        return False

                    item_prop = item_properties[type(prop)]
                    # if prop.modifier.arg != item_prop.modifier.arg:
                    #     return False

        return True

    def _serialize_data(self) -> dict[str, Any]:
        properties: list[dict[str, int | str]] = []
        for prop in self.properties:
            if isinstance(prop, dict):
                properties.append(
                    {
                        "property_type": str(prop.get("property_type", "")),
                        "modifier_arg": int(prop.get("modifier_arg", -1)),
                    }
                )
            else:
                properties.append({"property_type": type(prop).__name__, "modifier_arg": int(prop.modifier.arg)})

        return {
            "item_type": self.item_type.name if self.item_type is not None else None,
            "requirement_min": self.requirement_min,
            "requirement_max": self.requirement_max,
            "only_max_damage": self.only_max_damage,
            "properties": properties,
        }

    def _deserialize_data(self, data: dict[str, Any]) -> None:
        item_type_name = data.get("item_type", None)
        if isinstance(item_type_name, str) and item_type_name in ItemType.__members__:
            self.item_type = ItemType[item_type_name]

        self.requirement_min = int(data.get("requirement_min", 0))
        self.requirement_max = int(data.get("requirement_max", 0))
        self.only_max_damage = bool(data.get("only_max_damage", True))
        self.properties = [
            {
                "property_type": str(prop.get("property_type", "")),
                "modifier_arg": int(prop.get("modifier_arg", -1)),
            }
            for prop in data.get("properties", [])
            if isinstance(prop, dict)
        ]

class UpgradeRule(BaseRule):
    priority = RulePriority.UpgradeRule
    
    """
    A rule that checks if an item has a specific upgrade. This is determined by the item's properties, which are derived from the item's modifiers.
    """

    def __init__(self, name: str, action: ItemAction = ItemAction.NONE, upgrade: Optional[Upgrade] = None):
        super().__init__(name, action)
        self.upgrade: Upgrade | None = upgrade

    def is_valid(self) -> bool:
        return super().is_valid() and self.upgrade is not None

    def applies(self, item_id: int) -> bool:
        if not self.is_valid():
            return False

        item = self.get_item(item_id)
        return self.upgrade.id in [item.prefix.id if item.prefix else None, item.suffix.id if item.suffix else None, item.inscription.id if item.inscription else None] if item and self.upgrade else False

    def _serialize_data(self) -> dict[str, Any]:
        return {"upgrade_class": type(self.upgrade).__name__ if self.upgrade is not None else None}

    def _deserialize_data(self, data: dict[str, Any]) -> None:
        upgrade_class_name = data.get("upgrade_class", None)
        if not isinstance(upgrade_class_name, str):
            return
        
        from Sources.frenkeyLib.ItemHandling.Mods import upgrades as upgrades_module        

        upgrade_cls = getattr(upgrades_module, upgrade_class_name, None)

        if not isinstance(upgrade_cls, type):
            return

        # Hot reloads / duplicate module imports can create a different Upgrade class identity,
        # so strict issubclass(upgrade_cls, Upgrade) may be False even for valid upgrade classes.
        mro = getattr(upgrade_cls, "__mro__", ())
        is_upgrade_like = any(base.__name__ == "Upgrade" for base in mro)

        if not is_upgrade_like:
            return

        try:
            instance = upgrade_cls()
            
        except Exception as ex: 
            Py4GW.Console.Log(
                "UpgradeRule",
                f"Failed to instantiate upgrade '{upgrade_class_name}' for rule '{self.name}': {type(ex).__name__}: {ex}",
                Py4GW.Console.MessageType.Warning
            )
            return

        self.upgrade = instance

class SalvagesToMaterialRule(BaseRule):
    priority = RulePriority.SalvagesToMaterialRule
    
    """
    A rule that checks if an item can be salvaged into a specific materials. This is determined by the item's salvage data, which is derived from the item data in :file:`items.json`.
    """

    def __init__(self, name: str, action: ItemAction = ItemAction.NONE, materials: Optional[list[ModelID]] = None):
        super().__init__(name, action)
        self.materials = materials if materials is not None else []

    def is_valid(self) -> bool:
        return super().is_valid() and len(self.materials) > 0

    def applies(self, item_id: int) -> bool:
        if not self.is_valid():
            return False

        item = self.get_item(item_id)
        if item is None or not item.is_salvageable or item.data is None:
            return False
        
        common = [m.model_id for m in (item.data.common_salvage.values() if item.data.common_salvage else {})]
        rare = [m.model_id for m in (item.data.rare_salvage.values() if item.data.rare_salvage else {})]
        
        return any(mat in common + rare for mat in self.materials)
    
    def _serialize_data(self) -> dict[str, Any]:
        return {"materials": [mat.name for mat in self.materials]}
    
    def _deserialize_data(self, data: dict[str, Any]) -> None:
        self.materials = [
            ModelID[mat] for mat in data.get("materials", []) if isinstance(mat, str) and mat in ModelID.__members__
        ]