from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Any, ClassVar, Optional, Sequence, cast

from Py4GWCoreLib.enums_src.GameData_enums import DyeColor
from Py4GWCoreLib.enums_src.Item_enums import ItemAction, ItemType, Rarity, SalvageMode
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.item_mods_src.upgrades import ArmorUpgrade, Inherent, Upgrade
from Sources.frenkeyLib.ItemHandling.GlobalConfigs.Condition import (
    ArmorUpgradesCondition,
    Condition,
    ConditionEvaluationContext,
    DyeColorsCondition,
    EncodedNamesCondition,
    ExactItemTypeCondition,
    InherentFilter,
    InherentFilters,
    InherentFiltersCondition,
    InscribableCondition,
    ItemTypesCondition,
    IsMaterialCondition,
    MaxWeaponUpgradesCondition,
    ModelFileIdAndItemType,
    ModelFileIdsAndItemTypesCondition,
    ModelFileIdsCondition,
    ModelIdAndItemType,
    ModelIdsAndItemTypesCondition,
    ModelIdsCondition,
    NickItemCondition,
    QuantityCondition,
    RangedUpgrade,
    RaritiesCondition,
    SalvagesToMaterialsCondition,
    UnidentifiedCondition,
    UpgradeAndItemType,
    UpgradeMatchCondition,
    UpgradeRangesCondition,
    UpgradesCondition,
    WeaponRequirementCondition,
    WeaponRequirementRanges,
    normalize_inherent_filters,
    normalize_requirement_ranges,
)
from Py4GWCoreLib.item_data.item_snapshot import ItemSnapshot

class ResultInterpretation(IntEnum):
    Match = auto()
    NoMatch = auto()


class ConditionOperator(IntEnum):
    All = auto()
    Any = auto()


class Rule:
    """Base rule that evaluates one or more reusable conditions against an item."""
    _registry: ClassVar[dict[str, type["Rule"]]] = {}
    ui_selectable: ClassVar[bool] = True

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Rule._registry[cls.__name__] = cls

    def __init__(
        self,
        conditions: Optional[list[Condition]] = None,
        *,
        action: ItemAction = ItemAction.NONE,
        condition_operator: ConditionOperator = ConditionOperator.All,
    ):
        self.name = ""
        self.action = action
        self.enabled = True
        self.result_interpretation: ResultInterpretation = ResultInterpretation.Match
        self.condition_operator = condition_operator
        self.conditions: list[Condition] = conditions if conditions is not None else []

    def get_item(self, item_id: int) -> Optional[ItemSnapshot]:
        try:
            return ItemSnapshot.from_item_id(item_id)
        except Exception:
            return None

    def add_condition(self, condition: Condition) -> None:
        self.conditions.append(condition)

    def remove_condition(self, condition: Condition) -> None:
        self.conditions = [entry for entry in self.conditions if entry != condition]

    def clear_conditions(self) -> None:
        self.conditions.clear()

    def is_valid(self) -> bool:
        return self.enabled and len(self.conditions) > 0 and all(condition.is_valid() for condition in self.conditions)

    def _create_context(self, item_id: int) -> ConditionEvaluationContext:
        return ConditionEvaluationContext(item_id=item_id, item_snapshot=self.get_item(item_id))

    def _evaluate_conditions(self, context: ConditionEvaluationContext) -> bool:
        if not self.conditions:
            return False

        evaluations = [condition.evaluate(context) for condition in self.conditions]
        if self.condition_operator == ConditionOperator.Any:
            return any(evaluations)

        return all(evaluations)

    def applies(self, item_id: int) -> bool:
        if not self.is_valid():
            return False

        context = self._create_context(item_id)
        if context.item_snapshot is None:
            return False

        return self._apply_result_interpretation(self._evaluate_conditions(context))

    def _apply_result_interpretation(self, matched: bool) -> bool:
        if self.result_interpretation == ResultInterpretation.NoMatch:
            return not matched

        return matched

    def _comparison_data(self) -> Any:
        return (
            self.condition_operator.name,
            self.action.name,
            tuple((type(condition).__name__, condition._comparison_data()) for condition in self.conditions),
        )

    def equals(self, other: object) -> bool:
        return (
            isinstance(other, Rule)
            and type(self) is type(other)
            and self.result_interpretation == other.result_interpretation
            and self._comparison_data() == other._comparison_data()
        )

    def __eq__(self, other: object) -> bool:
        return self.equals(other)

    def _serialize_data(self) -> dict[str, Any]:
        return {
            "condition_operator": self.condition_operator.name,
            "conditions": [condition.to_dict() for condition in self.conditions],
        }

    def _deserialize_data(self, data: dict[str, Any]) -> None:
        operator_name = data.get("condition_operator")
        if isinstance(operator_name, str) and operator_name in ConditionOperator.__members__:
            self.condition_operator = ConditionOperator[operator_name]
        else:
            self.condition_operator = ConditionOperator.All

        self.conditions = []
        for entry in data.get("conditions", []):
            if not isinstance(entry, dict):
                continue

            condition = Condition.from_dict(entry)
            if condition is not None:
                self.conditions.append(condition)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "rule_type": type(self).__name__,
            "name": self.name,
            "action": self.action.name,
            "result_interpretation": self.result_interpretation.name,
        }
        payload.update(self._serialize_data())
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Rule | None":
        rule_type_name = str(payload.get("rule_type", ""))
        rule_cls = cls._registry.get(rule_type_name)
        if rule_cls is None:
            return None

        rule = rule_cls()
        rule.name = payload.get("name", "")
        action_name = payload.get("action", "NONE")
        rule.action = ItemAction[action_name] if isinstance(action_name, str) and action_name in ItemAction.__members__ else ItemAction.NONE

        result_interpretation_name = payload.get("result_interpretation")
        if isinstance(result_interpretation_name, str) and result_interpretation_name in ResultInterpretation.__members__:
            rule.result_interpretation = ResultInterpretation[result_interpretation_name]
        elif bool(payload.get("inverted", False)):
            rule.result_interpretation = ResultInterpretation.NoMatch

        rule._deserialize_data(payload)
        return rule


class CustomRule(Rule):
    """User-defined rule that can combine any supported condition sections."""
    pass


class ModelIdsRule(Rule):
    """Matches items whose model ID is in the configured list."""
    def __init__(self, model_ids: Optional[list[ModelID | int]] = None):
        super().__init__([ModelIdsCondition(model_ids)])

    @property
    def condition(self) -> ModelIdsCondition:
        return cast(ModelIdsCondition, self.conditions[0])
    
    @property
    def model_ids(self) -> list[ModelID | int]:
        return self.condition.model_ids

    @model_ids.setter
    def model_ids(self, value: list[ModelID | int]) -> None:
        self.condition.model_ids = value

class ItemTypesRule(Rule):
    """Matches items whose item type is one of the selected types."""
    def __init__(self, item_types: Optional[list[ItemType]] = None):
        super().__init__([ItemTypesCondition(item_types)])

    @property
    def condition(self) -> ItemTypesCondition:
        return cast(ItemTypesCondition, self.conditions[0])
    
    @property
    def item_types(self) -> list[ItemType]:
        return self.condition.item_types

    @item_types.setter
    def item_types(self, value: list[ItemType]) -> None:
        self.condition.item_types = value


class QuantityRule(Rule):
    """Matches items whose quantity falls inside the configured inclusive range."""
    def __init__(self, min_quantity: int = 0, max_quantity: int = 250):
        super().__init__([QuantityCondition(min_quantity, max_quantity)])

    @property
    def condition(self) -> QuantityCondition:
        return cast(QuantityCondition, self.conditions[0])

    @property
    def min_quantity(self) -> int:
        return self.condition.min_quantity

    @min_quantity.setter
    def min_quantity(self, value: int) -> None:
        self.condition.min_quantity = max(0, min(250, int(value)))
        if self.condition.min_quantity > self.condition.max_quantity:
            self.condition.max_quantity = self.condition.min_quantity

    @property
    def max_quantity(self) -> int:
        return self.condition.max_quantity

    @max_quantity.setter
    def max_quantity(self, value: int) -> None:
        self.condition.max_quantity = max(0, min(250, int(value)))
        if self.condition.max_quantity < self.condition.min_quantity:
            self.condition.min_quantity = self.condition.max_quantity


class NickItemRule(Rule):
    """Matches Nicholas the Traveler items that come up within the configured number of weeks."""
    def __init__(self, weeks_before_next_cycle: int = 0):
        super().__init__([NickItemCondition(weeks_before_next_cycle)])

    @property
    def condition(self) -> NickItemCondition:
        return cast(NickItemCondition, self.conditions[0])

    @property
    def weeks_before_next_cycle(self) -> int:
        return self.condition.weeks_before_next_cycle

    @weeks_before_next_cycle.setter
    def weeks_before_next_cycle(self, value: int) -> None:
        self.condition.weeks_before_next_cycle = max(0, min(137, int(value)))


class IsMaterialRule(Rule):
    """Matches material items, optionally restricted to rare materials only."""
    def __init__(self, rare_only: bool = False):
        super().__init__([IsMaterialCondition(rare_only)])

    @property
    def condition(self) -> IsMaterialCondition:
        return cast(IsMaterialCondition, self.conditions[0])

    @property
    def rare_only(self) -> bool:
        return self.condition.rare_materials

    @rare_only.setter
    def rare_only(self, value: bool) -> None:
        self.condition.rare_materials = bool(value)


class ModelIdsAndItemTypesRule(Rule):
    """Matches specific combinations of model ID and item type."""
    def __init__(self, model_ids: Optional[list[ModelIdAndItemType]] = None):
        super().__init__([ModelIdsAndItemTypesCondition(model_ids)])

    @property
    def condition(self) -> ModelIdsAndItemTypesCondition:
        return cast(ModelIdsAndItemTypesCondition, self.conditions[0])

    @property
    def items(self) -> list[ModelIdAndItemType]:
        return self.condition.modelids_and_itemtypes

    @items.setter
    def items(self, value: list[ModelIdAndItemType]) -> None:
        self.condition.modelids_and_itemtypes = value


class EncodedNameRule(Rule):
    """Matches items by their encoded name bytes."""
    def __init__(self, encoded_names: Optional[list[bytes]] = None):
        super().__init__([EncodedNamesCondition(encoded_names)])

    @property
    def condition(self) -> EncodedNamesCondition:
        return cast(EncodedNamesCondition, self.conditions[0])
    
    @property
    def encoded_names(self) -> list[bytes]:
        return self.condition.encoded_names

    @encoded_names.setter
    def encoded_names(self, value: list[bytes]) -> None:
        self.condition.encoded_names = value


class ModelFileIdRule(Rule):
    """Matches items whose model file ID is in the configured list."""
    def __init__(self, model_file_ids: Optional[list[int]] = None):
        super().__init__([ModelFileIdsCondition(model_file_ids)])

    @property
    def condition(self) -> ModelFileIdsCondition:
        return cast(ModelFileIdsCondition, self.conditions[0])

    @property
    def model_file_ids(self) -> list[int]:
        return self.condition.model_file_ids

    @model_file_ids.setter
    def model_file_ids(self, value: list[int]) -> None:
        self.condition.model_file_ids = value


class ModelFileIdAndItemTypeRule(Rule):
    """Matches specific combinations of model file ID and item type."""
    def __init__(self, model_file_ids_and_item_types: Optional[list[ModelFileIdAndItemType]] = None):
        super().__init__([ModelFileIdsAndItemTypesCondition(model_file_ids_and_item_types)])

    @property
    def condition(self) -> ModelFileIdsAndItemTypesCondition:
        return cast(ModelFileIdsAndItemTypesCondition, self.conditions[0])

    @property
    def model_file_ids_and_item_types(self) -> list[ModelFileIdAndItemType]:
        return self.condition.model_file_ids_and_item_types

    @model_file_ids_and_item_types.setter
    def model_file_ids_and_item_types(self, value: list[ModelFileIdAndItemType]) -> None:
        self.condition.model_file_ids_and_item_types = value


class WeaponSkinRule(Rule):
    """Matches weapon skins by model file ID with optional requirement and inherent filters."""
    def __init__(
        self,
        model_file_ids: Optional[list[int]] = None,
        requirement_min: int = 0,
        requirement_max: int = 13,
        only_max_damage: bool = True,
        requirements: Optional[WeaponRequirementRanges] = None,
        inherents: Optional[Sequence[InherentFilter | Inherent]] = None,
        inscribable: bool = False,
    ):
        conditions: list[Condition] = [
            ModelFileIdsCondition(model_file_ids),
            WeaponRequirementCondition(requirements, None, requirement_min, requirement_max),
            InherentFiltersCondition(normalize_inherent_filters(inherents)),
        ]

        super().__init__(conditions)
        self._only_max_damage = only_max_damage

    @property
    def model_file_ids(self) -> list[int]:
        return self._model_file_condition().model_file_ids

    @model_file_ids.setter
    def model_file_ids(self, value: list[int]) -> None:
        self._model_file_condition().model_file_ids = value

    @property
    def requirements(self) -> WeaponRequirementRanges:
        return self._requirement_condition().requirements

    @requirements.setter
    def requirements(self, value: WeaponRequirementRanges) -> None:
        self._requirement_condition().requirements = normalize_requirement_ranges(value)

    @property
    def inherents(self) -> InherentFilters:
        return self._inherent_condition().inherents

    @inherents.setter
    def inherents(self, value: Sequence[InherentFilter | Inherent]) -> None:
        normalized = normalize_inherent_filters(value)
        self._inherent_condition().inherents = normalized if normalized else []

    @property
    def requirement_min(self) -> int:
        return self._requirement_condition().requirement_min

    @requirement_min.setter
    def requirement_min(self, value: int) -> None:
        self._requirement_condition().requirements = normalize_requirement_ranges(None, None, int(value), self.requirement_max)

    @property
    def requirement_max(self) -> int:
        return self._requirement_condition().requirement_max

    @requirement_max.setter
    def requirement_max(self, value: int) -> None:
        self._requirement_condition().requirements = normalize_requirement_ranges(None, None, self.requirement_min, int(value))

    @property
    def only_max_damage(self) -> bool:
        return self._only_max_damage

    @only_max_damage.setter
    def only_max_damage(self, value: bool) -> None:
        self._only_max_damage = value

    @property
    def inscribable(self) -> bool:
        condition = self._inherent_condition()
        return condition.inscribable if condition is not None else False

    @inscribable.setter
    def inscribable(self, value: bool) -> None:
        condition = self._inherent_condition()
        if condition is not None:
            condition.inscribable = value

    def _serialize_data(self) -> dict[str, Any]:
        payload = super()._serialize_data()
        payload["only_max_damage"] = self.only_max_damage
        return payload

    def _deserialize_data(self, data: dict[str, Any]) -> None:
        super()._deserialize_data(data)
        self._only_max_damage = bool(data.get("only_max_damage", True))

    def _model_file_condition(self) -> ModelFileIdsCondition:
        return self.conditions[0]  # type: ignore[return-value]

    def _requirement_condition(self) -> WeaponRequirementCondition:
        return self.conditions[1]  # type: ignore[return-value]

    def _inherent_condition(self) -> InherentFiltersCondition:
        return self.conditions[2]  # type: ignore[return-value]
    
class WeaponTypeRule(Rule):
    """Matches one weapon type with optional requirement and inherent filters."""
    def __init__(
        self,
        item_type: Optional[ItemType] = None,
        requirement_min: int = 0,
        requirement_max: int = 13,
        only_max_damage: bool = True,
        requirements: Optional[WeaponRequirementRanges] = None,
        inherents: Optional[Sequence[InherentFilter | Inherent]] = None,
        inscribable: bool = False,
    ):
        conditions: list[Condition] = [
            ExactItemTypeCondition(item_type),
            WeaponRequirementCondition(requirements, item_type, requirement_min, requirement_max),
        ]
        normalized_inherents = normalize_inherent_filters(inherents)
        if normalized_inherents:
            conditions.append(InherentFiltersCondition(normalized_inherents))
        if inscribable:
            conditions.append(InscribableCondition())

        super().__init__(conditions)
        self._only_max_damage = only_max_damage

    @property
    def item_type(self) -> Optional[ItemType]:
        return self._item_type_condition().item_type

    @item_type.setter
    def item_type(self, value: Optional[ItemType]) -> None:
        self._item_type_condition().item_type = value
        self._requirement_condition().item_type = value

    @property
    def requirements(self) -> WeaponRequirementRanges:
        return self._requirement_condition().requirements

    @requirements.setter
    def requirements(self, value: WeaponRequirementRanges) -> None:
        self._requirement_condition().requirements = normalize_requirement_ranges(value, self.item_type)

    @property
    def inherents(self) -> InherentFilters:
        condition = self._inherent_condition()
        return condition.inherents if condition is not None else []

    @inherents.setter
    def inherents(self, value: Sequence[InherentFilter | Inherent]) -> None:
        normalized = normalize_inherent_filters(value)
        self._replace_optional_condition(InherentFiltersCondition, InherentFiltersCondition(normalized) if normalized else None)

    @property
    def requirement_min(self) -> int:
        return self._requirement_condition().requirement_min

    @requirement_min.setter
    def requirement_min(self, value: int) -> None:
        self._requirement_condition().requirements = normalize_requirement_ranges(None, self.item_type, int(value), self.requirement_max)

    @property
    def requirement_max(self) -> int:
        return self._requirement_condition().requirement_max

    @requirement_max.setter
    def requirement_max(self, value: int) -> None:
        self._requirement_condition().requirements = normalize_requirement_ranges(None, self.item_type, self.requirement_min, int(value))

    @property
    def only_max_damage(self) -> bool:
        return self._only_max_damage

    @only_max_damage.setter
    def only_max_damage(self, value: bool) -> None:
        self._only_max_damage = value

    @property
    def inscribable(self) -> bool:
        return any(isinstance(condition, InscribableCondition) for condition in self.conditions)

    @inscribable.setter
    def inscribable(self, value: bool) -> None:
        self._replace_optional_condition(InscribableCondition, InscribableCondition() if value else None)

    def _serialize_data(self) -> dict[str, Any]:
        payload = super()._serialize_data()
        payload["only_max_damage"] = self.only_max_damage
        return payload

    def _deserialize_data(self, data: dict[str, Any]) -> None:
        super()._deserialize_data(data)
        self._only_max_damage = bool(data.get("only_max_damage", True))

    def _item_type_condition(self) -> ExactItemTypeCondition:
        return self.conditions[0]  # type: ignore[return-value]

    def _requirement_condition(self) -> WeaponRequirementCondition:
        return self.conditions[1]  # type: ignore[return-value]

    def _inherent_condition(self) -> Optional[InherentFiltersCondition]:
        return next((condition for condition in self.conditions if isinstance(condition, InherentFiltersCondition)), None)

    def _replace_optional_condition(self, condition_type: type[Condition], replacement: Optional[Condition]) -> None:
        self.conditions = [condition for condition in self.conditions if not isinstance(condition, condition_type)]
        if replacement is not None:
            self.conditions.append(replacement)


class SalvagesToMaterialRule(Rule):
    """Matches items that can salvage into one of the selected materials."""
    def __init__(self, materials: Optional[list[ModelID | int]] = None):
        super().__init__([SalvagesToMaterialsCondition(materials)])

    @property
    def condition(self) -> SalvagesToMaterialsCondition:
        return cast(SalvagesToMaterialsCondition, self.conditions[0])
    
    @property
    def materials(self) -> list[ModelID | int]:
        return self.condition.materials

    @materials.setter
    def materials(self, value: list[ModelID | int]) -> None:
        self.condition.materials = value

class RaritiesRule(Rule):
    """Matches items whose rarity is one of the selected rarities."""
    def __init__(self, rarities: Optional[list[Rarity]] = None):
        super().__init__([RaritiesCondition(rarities)])

    @property
    def condition(self) -> RaritiesCondition:
        return cast(RaritiesCondition, self.conditions[0])
    
    @property
    def rarities(self) -> list[Rarity]:
        return self.condition.rarities

    @rarities.setter
    def rarities(self, value: list[Rarity]) -> None:
        self.condition.rarities = value


class RaritiesAndItemTypesRule(Rule):
    """Matches items by combining rarity and item type filters."""
    def __init__(self, rarities: Optional[list[Rarity]] = None, item_types: Optional[list[ItemType]] = None):
        super().__init__([RaritiesCondition(rarities), ItemTypesCondition(item_types)])

    @property
    def rarities(self) -> list[Rarity]:
        return self._rarity_condition().rarities

    @rarities.setter
    def rarities(self, value: list[Rarity]) -> None:
        self._rarity_condition().rarities = value

    @property
    def item_types(self) -> list[ItemType]:
        return self._item_type_condition().item_types

    @item_types.setter
    def item_types(self, value: list[ItemType]) -> None:
        self._item_type_condition().item_types = value

    def _rarity_condition(self) -> RaritiesCondition:
        return self.conditions[0]  # type: ignore[return-value]

    def _item_type_condition(self) -> ItemTypesCondition:
        return self.conditions[1]  # type: ignore[return-value]


class UnidentifiedRule(Rule):
    """Matches items that are still unidentified."""
    def __init__(self):
        super().__init__([UnidentifiedCondition()], action=ItemAction.Identify)
    
    @property
    def condition(self) -> UnidentifiedCondition:
        return cast(UnidentifiedCondition, self.conditions[0])

class UnidentifiedAndRarityRule(Rule):
    """Matches unidentified items limited to the selected rarities."""
    def __init__(self, rarities: Optional[list[Rarity]] = None):
        super().__init__([UnidentifiedCondition(), RaritiesCondition(rarities)], action=ItemAction.Identify)

    @property
    def rarities(self) -> list[Rarity]:
        return self._rarities_condition().rarities

    @rarities.setter
    def rarities(self, value: list[Rarity]) -> None:
        self._rarities_condition().rarities = value

    def _rarities_condition(self) -> RaritiesCondition:
        return cast(RaritiesCondition, self.conditions[1])

class DyesRule(Rule):
    """Matches dye items whose color is one of the selected dye colors."""
    def __init__(self, dye_colors: Optional[list[DyeColor]] = None):
        super().__init__([DyeColorsCondition(dye_colors)])

    @property
    def condition(self) -> DyeColorsCondition:
        return cast(DyeColorsCondition, self.conditions[0])
    
    @property
    def dye_colors(self) -> list[DyeColor]:
        return self.condition.dye_colors

    @dye_colors.setter
    def dye_colors(self, value: list[DyeColor]) -> None:
        self.condition.dye_colors = value


@dataclass
class StockInstruction:
    """Defines a desired stock target for a model ID and item type combination."""
    model_id: ModelID
    item_type: ItemType
    quantity: int
    include_storage: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": int(self.model_id.value),
            "item_type": self.item_type.name,
            "quantity": self.quantity,
            "include_storage": self.include_storage,
        }

    def comparison_data(self) -> tuple[int, str, int, bool]:
        return (
            int(self.model_id.value),
            self.item_type.name,
            self.quantity,
            self.include_storage,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StockInstruction | None":
        try:
            model_id = ModelID(int(data["model_id"]))
            item_type = ItemType[str(data["item_type"])]
            quantity = int(data["quantity"])
            include_storage = bool(data.get("include_storage", True))
        except (KeyError, ValueError, TypeError):
            return None

        return cls(
            model_id=model_id,
            item_type=item_type,
            quantity=quantity,
            include_storage=include_storage,
        )


class ExtractUpgradeRule(Rule):
    """Base rule for matching extractable upgrades on items."""
    ui_selectable: ClassVar[bool] = False

    def __init__(self, conditions: Optional[list[Condition]] = None):
        super().__init__(conditions)
        self.extracted_action : ItemAction = ItemAction.Stash

    def get_effective_action(self, item_id: int) -> ItemAction:
        item_snapshot = self.get_item(item_id)
        if item_snapshot is not None and item_snapshot.item_type is ItemType.Rune_Mod:
            return self.extracted_action

        return self.action
        
    def get_matching_upgrades(self, item_id: int) -> list[tuple[Upgrade, SalvageMode]]:
        if not self.is_valid():
            return []

        context = self._create_context(item_id)
        if context.item_snapshot is None:
            return []

        matches: list[tuple[Upgrade, SalvageMode]] = []
        for condition in self.conditions:
            if isinstance(condition, UpgradeMatchCondition):
                matches.extend(condition.get_matching_upgrades(context))

        deduped: list[tuple[Upgrade, SalvageMode]] = []
        seen_modes: set[SalvageMode] = set()
        for upgrade, salvage_mode in matches:
            if salvage_mode in seen_modes:
                continue

            seen_modes.add(salvage_mode)
            deduped.append((upgrade, salvage_mode))

        return deduped

    def _comparison_data(self) -> Any:
        return (
            super()._comparison_data(),
            self.extracted_action.name,
        )

    def _serialize_data(self) -> dict[str, Any]:
        payload = super()._serialize_data()
        payload["extracted_action"] = self.extracted_action.name
        return payload

    def _deserialize_data(self, data: dict[str, Any]) -> None:
        super()._deserialize_data(data)

        extracted_action_name = data.get("extracted_action", ItemAction.Stash.name)
        if isinstance(extracted_action_name, str) and extracted_action_name in ItemAction.__members__:
            self.extracted_action = ItemAction[extracted_action_name]
        else:
            self.extracted_action = ItemAction.Stash


class MaxWeaponUpgradeRule(ExtractUpgradeRule):
    """Matches weapons containing selected max-value weapon upgrades or inscriptions."""
    ui_selectable: ClassVar[bool] = True

    def __init__(self, upgrades: Optional[list[UpgradeAndItemType]] = None):
        super().__init__([MaxWeaponUpgradesCondition(upgrades)])

    @property
    def condition(self) -> MaxWeaponUpgradesCondition:
        return cast(MaxWeaponUpgradesCondition, self.conditions[0])

    @property
    def weapon_upgrades(self) -> list[UpgradeAndItemType]:
        return self.condition.weapon_upgrades

    @weapon_upgrades.setter
    def weapon_upgrades(self, value: list[UpgradeAndItemType]) -> None:
        self.condition.weapon_upgrades = value


class ArmorUpgradeRule(ExtractUpgradeRule):
    """Matches armor containing selected runes or insignias."""
    ui_selectable: ClassVar[bool] = True

    def __init__(self, runes: Optional[list[ArmorUpgrade]] = None):
        super().__init__([ArmorUpgradesCondition(runes)])
        self.extracted_action = ItemAction.Sell_To_Trader

    @property
    def condition(self) -> ArmorUpgradesCondition:
        return cast(ArmorUpgradesCondition, self.conditions[0])

    @property
    def armor_upgrades(self) -> list[ArmorUpgrade]:
        return self.condition.armor_upgrades

    @armor_upgrades.setter
    def armor_upgrades(self, value: list[ArmorUpgrade]) -> None:
        self.condition.armor_upgrades = value


class UpgradeRangeRule(ExtractUpgradeRule):
    """Matches upgrades whose numeric values fall inside configured ranges."""
    ui_selectable: ClassVar[bool] = True

    def __init__(self, upgrade_ranges: Optional[list[RangedUpgrade]] = None):
        super().__init__([UpgradeRangesCondition(upgrade_ranges)])

    @property
    def condition(self) -> UpgradeRangesCondition:
        return cast(UpgradeRangesCondition, self.conditions[0])

    @property
    def upgrade_ranges(self) -> list[RangedUpgrade]:
        return self.condition.upgrade_ranges

    @upgrade_ranges.setter
    def upgrade_ranges(self, value: list[RangedUpgrade]) -> None:
        self.condition.upgrade_ranges = value


class UpgradesRule(ExtractUpgradeRule):
    """Matches selected upgrades without requiring them to be maxed or ranged."""
    ui_selectable: ClassVar[bool] = True

    def __init__(self, upgrades: Optional[list[tuple[Upgrade, list[ItemType]] | Upgrade]] = None):
        super().__init__([UpgradesCondition(upgrades)])

    @property
    def condition(self) -> UpgradesCondition:
        return cast(UpgradesCondition, self.conditions[0])

    @property
    def upgrades(self) -> list[tuple[Upgrade, list[ItemType]]]:
        return self.condition.upgrades

    @upgrades.setter
    def upgrades(self, value: list[tuple[Upgrade, list[ItemType]] | Upgrade]) -> None:
        self.condition.upgrades = UpgradesCondition(value).upgrades
