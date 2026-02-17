"""
standalone_modifier_parser.py

This is unashamedly stolen from Frenkey, thanks brother :)

Usage:
    db = ModDatabase.load("path/to/data")
    result = parse_modifiers(raw_mods, item_type, model_id, db)
"""

import json
import os
from enum import IntEnum
from dataclasses import dataclass, field
from typing import Optional
from Py4GWCoreLib.enums_src.Item_enums import ItemType
from Py4GWCoreLib.enums import Attribute


# ══════════════════════════════════════════════
# Enums
# ══════════════════════════════════════════════


class ModifierValueArg(IntEnum):
    None_ = -1
    Arg1 = 0
    Arg2 = 1
    Fixed = 2


class ModifierIdentifier(IntEnum):
    None_ = 0
    Requirement = 10136
    Damage = 42920
    Damage_NoReq = 42120
    DamageType = 9400
    ShieldArmor = 42936
    TargetItemType = 9656
    RuneAttribute = 8680
    HealthLoss = 8408
    ImprovedVendorValue = 9720
    HighlySalvageable = 9736


class ModType(IntEnum):
    None_ = 0
    Prefix = 1
    Suffix = 2
    Inherent = 3


# ══════════════════════════════════════════════
# Constants
# ══════════════════════════════════════════════

WEAPON_TYPES = frozenset(
    {
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
    }
)

ARMOR_TYPES = frozenset(
    {
        ItemType.Headpiece,
        ItemType.Chestpiece,
        ItemType.Gloves,
        ItemType.Leggings,
        ItemType.Boots,
        ItemType.Salvage,
    }
)

ITEM_TYPE_META_TYPES: dict[ItemType, list[ItemType]] = {
    ItemType.Weapon: [
        ItemType.Axe,
        ItemType.Bow,
        ItemType.Daggers,
        ItemType.Hammer,
        ItemType.Scythe,
        ItemType.Spear,
        ItemType.Staff,
        ItemType.Sword,
        ItemType.Wand,
    ],
    ItemType.MartialWeapon: [
        ItemType.Axe,
        ItemType.Bow,
        ItemType.Daggers,
        ItemType.Hammer,
        ItemType.Scythe,
        ItemType.Spear,
        ItemType.Sword,
    ],
    ItemType.OffhandOrShield: [
        ItemType.Offhand,
        ItemType.Shield,
    ],
    ItemType.EquippableItem: [
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
    ],
    ItemType.SpellcastingWeapon: [
        ItemType.Staff,
        ItemType.Wand,
    ],
}


# ══════════════════════════════════════════════
# Modifier Data Structures
# ══════════════════════════════════════════════


@dataclass
class BaseModifierInfo:
    identifier: int = 0
    arg1: int = 0
    arg2: int = 0

    def __post_init__(self):
        self.arg = (self.arg1 << 8) | self.arg2

    @staticmethod
    def from_dict(data: dict) -> "BaseModifierInfo":
        return BaseModifierInfo(
            identifier=data.get("Identifier", 0),
            arg1=data.get("Arg1", 0),
            arg2=data.get("Arg2", 0),
        )


@dataclass
class ModifierInfo(BaseModifierInfo):
    modifier_value_arg: ModifierValueArg = ModifierValueArg.None_
    arg: int = 0
    min: int = 0
    max: int = 0

    @staticmethod
    def from_dict(data: dict) -> "ModifierInfo":
        return ModifierInfo(
            identifier=data["Identifier"],
            arg1=data["Arg1"],
            arg2=data["Arg2"],
            arg=data.get("Arg", 0),
            modifier_value_arg=ModifierValueArg[data["ModifierValueArg"]],
            min=data.get("Min", 0),
            max=data.get("Max", 0),
        )


# ══════════════════════════════════════════════
# Rune
# ══════════════════════════════════════════════


class Rune:
    def __init__(
        self, identifier: str, modifiers: list[ModifierInfo], name: str = "", mod_type: ModType = ModType.None_
    ):
        self.identifier = identifier
        self.modifiers = modifiers
        self.name = name
        self.mod_type = mod_type

    def matches_modifiers(self, modifiers: list[tuple[int, int, int]]) -> tuple[bool, bool]:
        results: list[tuple[bool, bool]] = []

        for mod in self.modifiers:
            matched = False
            maxed = False

            if mod.modifier_value_arg == ModifierValueArg.None_:
                continue

            for ident, arg1, arg2 in modifiers:
                if mod.identifier != ident:
                    continue

                if mod.modifier_value_arg == ModifierValueArg.Arg1:
                    if mod.min <= arg1 <= mod.max and arg2 == mod.arg2:
                        matched = True
                        maxed = arg1 >= mod.max
                        results.append((matched, maxed))

                elif mod.modifier_value_arg == ModifierValueArg.Arg2:
                    if mod.min <= arg2 <= mod.max and arg1 == mod.arg1:
                        matched = True
                        maxed = arg2 >= mod.max
                        results.append((matched, maxed))

                elif mod.modifier_value_arg == ModifierValueArg.Fixed:
                    if arg1 == mod.arg1 and arg2 == mod.arg2:
                        matched = True
                        maxed = True
                        results.append((matched, maxed))

            if not matched:
                return False, False

        if not results or any(not r[0] for r in results):
            return False, False

        return True, all(r[1] for r in results)

    @staticmethod
    def from_json(data: dict) -> "Rune":
        return Rune(
            identifier=data["Identifier"],
            name=data.get("Names", {}).get("English", ""),
            mod_type=ModType[data["ModType"]] if "ModType" in data else ModType.None_,
            modifiers=[ModifierInfo.from_dict(m) for m in data["Modifiers"]],
        )


# ══════════════════════════════════════════════
# WeaponMod
# ══════════════════════════════════════════════


class WeaponMod:
    def __init__(
        self,
        identifier: str,
        modifiers: list[ModifierInfo],
        name: str = "",
        mod_type: ModType = ModType.None_,
        item_mods: dict | None = None,
        item_type_specific: dict | None = None,
        target_types: list | None = None,
    ):
        self.identifier = identifier
        self.modifiers = modifiers
        self.name = name
        self.mod_type = mod_type
        self.item_mods: dict = item_mods or {}
        self.item_type_specific: dict = item_type_specific or {}
        self.target_types: list = target_types or []

    @staticmethod
    def from_json(data: dict) -> "WeaponMod":
        item_mods = {}
        for it_name, mod_name in data.get("ItemMods", {}).items():
            try:
                item_mods[ItemType[it_name]] = mod_name
            except KeyError:
                pass

        item_type_specific = {}
        for it_name, bmi_data in data.get("ItemTypeSpecific", {}).items():
            try:
                item_type_specific[ItemType[it_name]] = BaseModifierInfo.from_dict(bmi_data)
            except KeyError:
                pass

        target_types = []
        for tt_name in data.get("TargetTypes", []):
            try:
                target_types.append(ItemType[tt_name])
            except KeyError:
                pass

        return WeaponMod(
            identifier=data["Identifier"],
            name=data.get("Names", {}).get("English", ""),
            mod_type=ModType[data["ModType"]] if "ModType" in data else ModType.None_,
            item_mods=item_mods,
            item_type_specific=item_type_specific,
            target_types=target_types,
            modifiers=[ModifierInfo.from_dict(m) for m in data["Modifiers"]],
        )


# ══════════════════════════════════════════════
# Match Results
# ══════════════════════════════════════════════


class MatchedRuneInfo:
    def __init__(self, rune: Rune, modifiers: list[tuple[int, int, int]], is_maxed: bool):
        self.rune = rune
        self.modifiers = modifiers
        self.is_maxed = is_maxed
        self.mod_type = rune.mod_type

    def __repr__(self):
        return f"MatchedRune('{self.rune.name}', type={self.mod_type.name}, maxed={self.is_maxed})"


class MatchedWeaponModInfo:
    def __init__(
        self, weapon_mod: WeaponMod, matched_modifiers: list[tuple[int, int, int]], is_maxed: bool, value: int = 0
    ):
        self.weapon_mod = weapon_mod
        self.matched_modifiers = matched_modifiers
        self.is_maxed = is_maxed
        self.value = value
        self.mod_type = weapon_mod.mod_type

    def __repr__(self):
        return f"MatchedWeaponMod('{self.weapon_mod.name}', type={self.mod_type.name}, value={self.value}, maxed={self.is_maxed})"


@dataclass
class ParsedModifierResult:
    target_item_type: ItemType = ItemType.Unknown
    is_rune: bool = False
    damage: tuple[int, int] = (0, 0)
    shield_armor: tuple[int, int] = (0, 0)
    requirements: int = 0
    attribute: Attribute = Attribute.None_
    is_highly_salvageable: bool = False
    has_increased_value: bool = False

    runes: list[MatchedRuneInfo] = field(default_factory=list)
    max_runes: list[MatchedRuneInfo] = field(default_factory=list)

    weapon_mods: list[MatchedWeaponModInfo] = field(default_factory=list)
    max_weapon_mods: list[MatchedWeaponModInfo] = field(default_factory=list)

    # ── Convenience: access by mod slot ──

    @property
    def prefix(self) -> Optional[MatchedRuneInfo | MatchedWeaponModInfo]:
        """The Prefix mod (insignia on armor, weapon prefix like 'Fiery')."""
        return next((m for m in self.all_mods if m.mod_type == ModType.Prefix), None)

    @property
    def suffix(self) -> Optional[MatchedRuneInfo | MatchedWeaponModInfo]:
        """The Suffix mod (rune on armor, weapon suffix like 'of Fortitude')."""
        return next((m for m in self.all_mods if m.mod_type == ModType.Suffix), None)

    @property
    def inherent(self) -> Optional[MatchedRuneInfo | MatchedWeaponModInfo]:
        """The Inherent mod (built-in mod that can't be salvaged, e.g. 'Sundering')."""
        return next((m for m in self.all_mods if m.mod_type == ModType.Inherent), None)

    @property
    def inscription(self) -> Optional[MatchedWeaponModInfo]:
        """Alias — inscriptions are typically the Prefix on inscribable weapons."""
        # Inscriptions in GW are stored as prefix or suffix depending on the mod.
        # This returns any weapon mod whose name starts with a quote (inscription naming convention).
        return next((m for m in self.weapon_mods if m.weapon_mod.name.startswith('"')), None)

    @property
    def all_mods(self) -> list[MatchedRuneInfo | MatchedWeaponModInfo]:
        return self.runes + self.weapon_mods

    @property
    def has_mods(self) -> bool:
        return bool(self.runes or self.weapon_mods)

    def mods_by_type(self, mod_type: ModType) -> list[MatchedRuneInfo | MatchedWeaponModInfo]:
        """Get all matched mods of a specific ModType."""
        return [m for m in self.all_mods if m.mod_type == mod_type]

    def summary(self) -> str:
        """Human-readable summary of all mods on the item."""
        lines = []
        lines.append(
            f"Damage: {self.damage}  |  Armor: {self.shield_armor}  |  Req: {self.attribute.name} {self.requirements}"
        )

        for label, mod_type in [("Prefix", ModType.Prefix), ("Inherent", ModType.Inherent), ("Suffix", ModType.Suffix)]:
            mods = self.mods_by_type(mod_type)
            if mods:
                for m in mods:
                    name = m.rune.name if isinstance(m, MatchedRuneInfo) else m.weapon_mod.name
                    value_str = ""
                    if isinstance(m, MatchedWeaponModInfo) and m.value:
                        value_str = f" ({m.value})"
                    maxed_str = " ★" if m.is_maxed else ""
                    lines.append(f"  [{label}] {name}{value_str}{maxed_str}")
            else:
                lines.append(f"  [{label}] —")

        insc = self.inscription
        if insc:
            lines.append(f"  [Inscription] {insc.weapon_mod.name} ({insc.value}){'★' if insc.is_maxed else ''}")

        flags = []
        if self.is_highly_salvageable:
            flags.append("Highly Salvageable")
        if self.has_increased_value:
            flags.append("Increased Value")
        if flags:
            lines.append(f"  Flags: {', '.join(flags)}")

        return "\n".join(lines)


# ══════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════


def is_weapon_type(item_type: ItemType) -> bool:
    return item_type in WEAPON_TYPES


def is_armor_type(item_type: ItemType) -> bool:
    return item_type in ARMOR_TYPES


def is_matching_item_type(item_type: ItemType, target: ItemType) -> bool:
    if item_type == target:
        return True
    return item_type in ITEM_TYPE_META_TYPES.get(target, [])


# ══════════════════════════════════════════════
# Database
# ══════════════════════════════════════════════


class ModDatabase:
    def __init__(self, runes: dict[str, Rune] | None = None, weapon_mods: dict[str, WeaponMod] | None = None):
        self.runes: dict[str, Rune] = runes or {}
        self.weapon_mods: dict[str, WeaponMod] = weapon_mods or {}

    @staticmethod
    def load(data_directory: str) -> "ModDatabase":
        """
        Load runes.json and weapon_mods.json from the given directory.
        Matches the exact format saved by LootEx Data.SaveRunes() / Data.SaveWeaponMods().
        """
        runes_path = os.path.join(data_directory, "runes.json")
        weapon_mods_path = os.path.join(data_directory, "weapon_mods.json")

        runes: dict[str, Rune] = {}
        weapon_mods: dict[str, WeaponMod] = {}

        if os.path.exists(runes_path):
            with open(runes_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            for _key, value in raw.items():
                rune = Rune.from_json(value)
                runes[rune.identifier] = rune

        if os.path.exists(weapon_mods_path):
            with open(weapon_mods_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            for _key, value in raw.items():
                mod = WeaponMod.from_json(value)
                if mod.identifier not in weapon_mods:
                    weapon_mods[mod.identifier] = mod

        return ModDatabase(runes=runes, weapon_mods=weapon_mods)


# ══════════════════════════════════════════════
# Rune Matching
# ══════════════════════════════════════════════


def _match_runes(
    modifier_values: list[tuple[int, int, int]],
    runes: dict[str, Rune],
) -> list[MatchedRuneInfo]:
    results = []
    for rune in runes.values():
        matches, is_maxed = rune.matches_modifiers(modifier_values)
        if matches:
            results.append(MatchedRuneInfo(rune, modifier_values, is_maxed))
    return results


# ══════════════════════════════════════════════
# Weapon Mod Matching
# ══════════════════════════════════════════════


def _match_weapon_mods(
    modifier_values: list[tuple[int, int, int]],
    item_type: ItemType,
    model_id: int,
    weapon_mods: dict[str, WeaponMod],
) -> list[MatchedWeaponModInfo]:
    """
    Match raw item modifiers against weapon mod definitions.

    Key design decisions:
      - None_ modifiers (9520, 9522, 42288, etc.) are structural markers in the
        definition files. They may or may not exist in raw game data, and their
        values are irrelevant. We skip them entirely during matching.
      - Meaningful modifiers (Arg1, Arg2, Fixed) are matched independently against
        the full raw modifier list — NOT sequentially, since raw data interleaves
        modifiers from different sources.
      - Target type checking uses target_types first, falls back to item_mods keys.
    """
    results: list[MatchedWeaponModInfo] = []
    raw_idents = {ident for ident, _, _ in modifier_values}

    for weapon_mod in weapon_mods.values():

        # ══════════════════════════════════════════
        # Step 1: Filter to meaningful modifiers only
        # ══════════════════════════════════════════
        meaningful_mods = [m for m in weapon_mod.modifiers if m.modifier_value_arg != ModifierValueArg.None_]

        if not meaningful_mods:
            continue

        # Quick pre-check: do any meaningful identifiers exist in raw data?
        if not any(m.identifier in raw_idents for m in meaningful_mods):
            continue

        # ══════════════════════════════════════════
        # Step 2: Target type validation (early exit)
        # ══════════════════════════════════════════
        if item_type == ItemType.Rune_Mod:
            # For upgrade components, we check model_id later
            target_mod = next(
                ((ident, a1, a2) for ident, a1, a2 in modifier_values if ident == ModifierIdentifier.TargetItemType),
                None,
            )
            if target_mod is None:
                continue
            applied_item_type = ItemType(target_mod[1])

            # Check if the model_id matches what this mod expects for that item type
            mod_model_id = weapon_mod.item_mods.get(applied_item_type)
            if mod_model_id is None:
                # Also check meta types
                meta_match = False
                for meta_type, sub_types in ITEM_TYPE_META_TYPES.items():
                    if applied_item_type in sub_types and meta_type in weapon_mod.item_mods:
                        meta_match = True
                        break
                if not meta_match:
                    continue
        else:
            # For equipped items, check target_types first (more reliable),
            # then fall back to item_mods keys
            type_matched = False

            # Check target_types (preferred — includes meta types like "Weapon", "MartialWeapon")
            if weapon_mod.target_types:
                for target in weapon_mod.target_types:
                    if is_matching_item_type(item_type, target):
                        type_matched = True
                        break

            # Fallback: check item_mods keys
            if not type_matched and weapon_mod.item_mods:
                for target in weapon_mod.item_mods.keys():
                    if is_matching_item_type(item_type, target):
                        type_matched = True
                        break

            if not type_matched:
                continue

        # ══════════════════════════════════════════
        # Step 3: Match each meaningful modifier independently
        # ══════════════════════════════════════════
        all_matched = True
        all_maxed = True
        matched_raw: list[tuple[int, int, int]] = []
        used_indices: set[int] = set()  # prevent double-matching same raw mod

        for mod in meaningful_mods:
            mod_matched = False

            for idx, (ident, arg1, arg2) in enumerate(modifier_values):
                if idx in used_indices:
                    continue
                if mod.identifier != ident:
                    continue

                if mod.modifier_value_arg == ModifierValueArg.Arg1:
                    if mod.min <= arg1 <= mod.max and arg2 == mod.arg2:
                        mod_matched = True
                        matched_raw.append((ident, arg1, arg2))
                        used_indices.add(idx)
                        if arg1 < mod.max:
                            all_maxed = False
                        break

                elif mod.modifier_value_arg == ModifierValueArg.Arg2:
                    if mod.min <= arg2 <= mod.max and arg1 == mod.arg1:
                        mod_matched = True
                        matched_raw.append((ident, arg1, arg2))
                        used_indices.add(idx)
                        if arg2 < mod.max:
                            all_maxed = False
                        break

                elif mod.modifier_value_arg == ModifierValueArg.Fixed:
                    if arg1 == mod.arg1 and arg2 == mod.arg2:
                        mod_matched = True
                        matched_raw.append((ident, arg1, arg2))
                        used_indices.add(idx)
                        # Fixed is always "maxed"
                        break

            if not mod_matched:
                all_matched = False
                break

        if not all_matched:
            continue

        # ══════════════════════════════════════════
        # Step 4: ItemTypeSpecific validation
        # ══════════════════════════════════════════
        if item_type in weapon_mod.item_type_specific:
            spec = weapon_mod.item_type_specific[item_type]
            spec_found = any(
                ident == spec.identifier and a1 == spec.arg1 and a2 == spec.arg2 for ident, a1, a2 in modifier_values
            )
            if not spec_found:
                continue

        # ══════════════════════════════════════════
        # Step 5: Extract display value from primary variable modifier
        # ══════════════════════════════════════════
        variable_mod = None
        for m in meaningful_mods:
            if m.modifier_value_arg in (ModifierValueArg.Arg1, ModifierValueArg.Arg2):
                variable_mod = m
                break

        value = 0
        if variable_mod:
            for ident, a1, a2 in matched_raw:
                if ident == variable_mod.identifier:
                    if variable_mod.modifier_value_arg == ModifierValueArg.Arg1:
                        value = a1
                    elif variable_mod.modifier_value_arg == ModifierValueArg.Arg2:
                        value = a2
                    break

        results.append(MatchedWeaponModInfo(weapon_mod, matched_raw, all_maxed, value))

    return results


# ══════════════════════════════════════════════
# Main Parse Function
# ══════════════════════════════════════════════


def parse_modifiers(
    modifiers: list[tuple[int, int, int]],
    item_type: ItemType,
    model_id: int,
    db: ModDatabase,
) -> ParsedModifierResult:
    """
    Parse raw item modifiers and identify runes + weapon mods.
    Each matched mod carries its ModType (Prefix / Suffix / Inherent).
    """
    result = ParsedModifierResult()

    if not modifiers:
        return result

    is_weapon = is_weapon_type(item_type)
    is_armor = is_armor_type(item_type)
    is_upgrade = item_type == ItemType.Rune_Mod

    # ── Pass 1: Extract base item stats ──
    for ident, arg1, arg2 in modifiers:
        if ident == ModifierIdentifier.TargetItemType:
            result.target_item_type = ItemType(arg1)
            result.is_rune = arg1 == 0 and arg2 == 0 and is_upgrade

        elif ident == ModifierIdentifier.Damage:
            result.damage = (arg2, arg1)

        elif ident == ModifierIdentifier.Damage_NoReq:
            result.damage = (arg2, arg1)

        elif ident == ModifierIdentifier.ShieldArmor:
            result.shield_armor = (arg1, arg2)

        elif ident == ModifierIdentifier.Requirement:
            result.requirements = arg2
            try:
                result.attribute = Attribute(arg1)
            except ValueError:
                result.attribute = Attribute.None_

        elif ident == ModifierIdentifier.ImprovedVendorValue:
            result.has_increased_value = True

        elif ident == ModifierIdentifier.HighlySalvageable:
            result.is_highly_salvageable = True

    # ── Pass 2: Match runes (armor & rune upgrades) ──
    if is_armor or result.is_rune:
        result.runes = _match_runes(modifiers, db.runes)
        result.max_runes = [r for r in result.runes if r.is_maxed]

    # ── Pass 3: Match weapon mods (weapons & non-rune upgrades) ──
    if is_weapon or (is_upgrade and not result.is_rune):
        result.weapon_mods = _match_weapon_mods(modifiers, item_type, model_id, db.weapon_mods)
        result.max_weapon_mods = [m for m in result.weapon_mods if m.is_maxed]

    return result


# ══════════════════════════════════════════════
# Example Usage
# ══════════════════════════════════════════════

if __name__ == "__main__":
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

    db = ModDatabase.load(DATA_DIR)
    print(f"Loaded {len(db.runes)} runes, {len(db.weapon_mods)} weapon mods")

    # Example: gold max sword with mods
    raw_modifiers = [
        (42920, 15, 22),  # Damage: 15-22
        (10136, 21, 9),  # Requirement: Swordsmanship 9
        (9400, 4, 0),  # DamageType
        (9720, 0, 0),  # ImprovedVendorValue
    ]

    result = parse_modifiers(
        modifiers=raw_modifiers,
        item_type=ItemType.Sword,
        model_id=1234,
        db=db,
    )

    # Full summary
    print(result.summary())

    # Or access by slot directly
    if result.prefix:
        print(f"\nPrefix: {result.prefix}")
    if result.inherent:
        print(f"Inherent: {result.inherent}")
    if result.suffix:
        print(f"Suffix: {result.suffix}")
    if result.inscription:
        print(f"Inscription: {result.inscription}")
