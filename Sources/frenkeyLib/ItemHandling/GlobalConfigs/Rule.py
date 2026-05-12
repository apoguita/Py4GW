from __future__ import annotations

from typing import Any, ClassVar, Optional

from Py4GWCoreLib.Item import Item
from Py4GWCoreLib.enums_src.GameData_enums import DyeColor
from Py4GWCoreLib.enums_src.Item_enums import ItemType, Rarity
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.item_mods_src.item_mod import ItemMod
from Py4GWCoreLib.item_mods_src.upgrades import Upgrade
from Sources.frenkeyLib.ItemHandling.Items.item_snapshot import ItemSnapshot

class Rule:
    _registry: ClassVar[dict[str, type["Rule"]]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Rule._registry[cls.__name__] = cls

    def __init__(self):
        pass

    def get_item(self, item_id: int) -> Optional[ItemSnapshot]:
        try:
            return ItemSnapshot.from_item_id(item_id)
        
        except Exception:
            return None

    def is_valid(self) -> bool:
        return True

    def applies(self, item_id: int) -> bool:
        raise NotImplementedError("Subclasses must implement the applies method.")

    def _comparison_data(self) -> Any:
        return ()

    def equals(self, other: object) -> bool:
        if not isinstance(other, Rule):
            return False
        
        if type(self) is not type(other):
            return False
        
        return self._comparison_data() == other._comparison_data()

    def __eq__(self, other: object) -> bool:
        return self.equals(other)

    def _serialize_data(self) -> dict[str, Any]:
        return {}

    def _deserialize_data(self, data: dict[str, Any]) -> None:
        return

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "rule_type": type(self).__name__,
        }
        payload.update(self._serialize_data())
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Rule | None:
        rule_type_name = str(payload.get("rule_type", ""))
        rule_cls = cls._registry.get(rule_type_name, None)
        if rule_cls is None:
            return None

        rule = rule_cls()

        rule._deserialize_data(payload)
        return rule

#region Multi value rules
class ModelIdsRule(Rule):
    """
    A rule that checks if an item has a ModelID contained in a specified list of model IDs.
    **CAUTION**: This rule is very basic and can result in unwanted matches as model IDs can be shared between different items and item types!
    """

    def __init__(self, model_ids: Optional[list[ModelID|int]] = None):
        super().__init__()
        self.model_ids: list[ModelID|int] = model_ids if model_ids is not None else []

    def is_valid(self) -> bool:
        return len(self.model_ids) > 0

    def applies(self, item_id):
        if not self.is_valid():
            return False

        item_snapshot = self.get_item(item_id)
        if item_snapshot is None:
            return False

        model_id = item_snapshot.model_id
        if model_id is None:
            return False
        
        for mid in self.model_ids:
            if isinstance(mid, ModelID):
                if model_id == mid.value:
                    return True
            elif model_id == mid:
                return True
        
        return False

    def _serialize_data(self) -> dict[str, Any]:
        return {"model_ids": [int(mid.value) if isinstance(mid, ModelID) else mid for mid in self.model_ids]}

    def _comparison_data(self) -> Any:
        normalized_model_ids = {
            int(mid.value) if isinstance(mid, ModelID) else mid
            for mid in self.model_ids
        }
        return tuple(sorted(normalized_model_ids))

    def _deserialize_data(self, data: dict[str, Any]) -> None:
        self.model_ids = []
        for mid in data.get("model_ids", []):
            if isinstance(mid, int):
                try:
                    self.model_ids.append(ModelID(mid))
                except ValueError:
                    self.model_ids.append(mid)
                    
class ItemTypesRule(Rule):
    """
    A rule that checks if an item :class:`ItemType` is a specified item type.
    """

    def __init__(self, item_types: Optional[list[ItemType]] = None):
        super().__init__()
        self.item_types: list[ItemType] = item_types if item_types is not None else []

    def is_valid(self) -> bool:
        return len(self.item_types) > 0

    def applies(self, item_id: int) -> bool:
        if not self.is_valid():
            return False

        item_snapshot = self.get_item(item_id)
        if item_snapshot is None:
            return False

        item_type = item_snapshot.item_type
        return item_type in self.item_types if item_type else False

    def _serialize_data(self) -> dict[str, Any]:
        return {"item_types": [item_type.name for item_type in self.item_types]}

    def _comparison_data(self) -> Any:
        return tuple(sorted(item_type.name for item_type in self.item_types))

    def _deserialize_data(self, data: dict[str, Any]) -> None:
        self.item_types = [
            ItemType[name]
            for name in data.get("item_types", [])
            if isinstance(name, str) and name in ItemType.__members__
        ]

class RaritiesRule(Rule):
    """
    A rule that checks if an item :class:`Rarity` is a specified rarity.
    """

    def __init__(self, rarities: Optional[list[Rarity]] = None):
        super().__init__()
        self.rarities: list[Rarity] = rarities if rarities is not None else []

    def is_valid(self) -> bool:
        return len(self.rarities) > 0

    def applies(self, item_id: int) -> bool:
        if not self.is_valid():
            return False

        item_snapshot = self.get_item(item_id)
        if item_snapshot is None:
            return False

        rarity = item_snapshot.rarity
        return rarity in self.rarities if rarity else False

    def _serialize_data(self) -> dict[str, Any]:
        return {"rarities": [rarity.name for rarity in self.rarities]}

    def _comparison_data(self) -> Any:
        return tuple(sorted(rarity.name for rarity in self.rarities))

    def _deserialize_data(self, data: dict[str, Any]) -> None:
        self.rarities = [
            Rarity[name]
            for name in data.get("rarities", [])
            if isinstance(name, str) and name in Rarity.__members__
        ]

class DyesRule(Rule):
    """
    A rule if an item is a **Vial of Dye** of a specific :class:`DyeColor`. This is determined by the item's dye color.
    """

    def __init__(self, dye_colors: Optional[list[DyeColor]] = None):
        super().__init__()
        self.dye_colors: list[DyeColor] = dye_colors if dye_colors is not None else []

    def is_valid(self) -> bool:
        return self.dye_colors is not None and len(self.dye_colors) > 0

    def applies(self, item_id: int) -> bool:
        if not self.is_valid():
            return False

        item_snapshot = self.get_item(item_id)
        if item_snapshot is None:
            return False

        item_type = item_snapshot.item_type
        if not item_type or item_type != ItemType.Dye:
            return False
        
        item_color = item_snapshot.color
        return item_color in self.dye_colors if item_color else False

    def _serialize_data(self) -> dict[str, Any]:
        return {"dye_colors": [color.name for color in self.dye_colors]}

    def _comparison_data(self) -> Any:
        return tuple(sorted(color.name for color in self.dye_colors))

    def _deserialize_data(self, data: dict[str, Any]) -> None:
        self.dye_colors = [
            DyeColor[name]
            for name in data.get("dye_colors", [])
            if isinstance(name, str) and name in DyeColor.__members__
        ]

class UpgradeRule(Rule):
    """
    A rule that checks if an item has a one of the specified upgrades.
    """
    def __init__(self, upgrades: Optional[list[(tuple[Upgrade, list[ItemType]] | Upgrade)]] = None):
        super().__init__()
        #add ItemType.EquippableItem to all upgrades that are not already tuples
        normalized_upgrades: list[tuple[Upgrade, list[ItemType]]] = []
        if upgrades is not None:
            for upgrade in upgrades:
                if isinstance(upgrade, Upgrade):
                    normalized_upgrades.append((upgrade, []))
                    
                elif isinstance(upgrade, tuple) and len(upgrade) == 2 and isinstance(upgrade[0], Upgrade) and (isinstance(upgrade[1], list) and all(isinstance(item_type, ItemType) for item_type in upgrade[1]) or upgrade[1] is None):
                    normalized_upgrades.append((upgrade[0], upgrade[1] if upgrade[1] is not None else []))
                    
        self.upgrades: list[tuple[Upgrade, list[ItemType]]] = normalized_upgrades

    def is_valid(self) -> bool:
        return len(self.upgrades) > 0

    def applies(self, item_id: int) -> bool:
        if not self.is_valid():
            return False
        
        item_snapshot = self.get_item(item_id)
        if item_snapshot is None:
            return False
        
        item_type = item_snapshot.item_type
        if item_type == ItemType.Rune_Mod:
            item_type = ItemMod.get_target_item_type(item_id) or item_type
        
        prefix, suffix, inscription, inherent = ItemMod.get_item_upgrades(item_id)
        item_upgrades = [upgrade for upgrade in [prefix, suffix, inscription, *(inherent or [])] if upgrade is not None]
        
        ## check if any of the specified upgrades match an upgrade on the item, while also matching the item type requirement by checking ItemType.is_matching_item_type() to allow for meta types like Weapon or EquippableItem
        for rule_upgrade, valid_item_types in self.upgrades:
            if valid_item_types is not None and len(valid_item_types) > 0 and not any(item_type.matches(valid_type) for valid_type in valid_item_types):
                continue
            
            for item_upgrade in item_upgrades:
                if rule_upgrade.matches(item_upgrade):
                    return True

        return False

    def _serialize_data(self) -> dict[str, Any]:
        return {
            "upgrades": [
                {
                    "upgrade": upgrade.to_dict(),
                    "item_types": [item_type.name for item_type in item_types] if item_types is not None else None,
                }
                for upgrade, item_types in self.upgrades
            ]
        }

    def _comparison_data(self) -> Any:
        normalized_data = []
        for upgrade, item_types in self.upgrades:
            item_type_names = tuple(sorted(item_type.name for item_type in item_types)) if item_types is not None else None
            normalized_data.append((upgrade._comparison_data(), item_type_names))
        
        return tuple(sorted(normalized_data))

    def _deserialize_data(self, data: dict[str, Any]) -> None:
        self.upgrades = []
        for entry in data.get("upgrades", []):
            upgrade_data = entry.get("upgrade", None)
            item_type_names = entry.get("item_types", None)

            if upgrade_data is None:
                continue
            
            upgrade = Upgrade.from_dict(upgrade_data)
            if upgrade is None:
                continue
            
            item_types : list[ItemType] | None = None
            if item_type_names is not None:
                item_types = []
                for name in item_type_names:
                    if isinstance(name, str) and name in ItemType.__members__:
                        item_types.append(ItemType[name])
            
            self.upgrades.append((upgrade, item_types if item_types is not None else []))

#endregion Multi value rules
