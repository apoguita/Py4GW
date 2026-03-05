from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from PyItem import ItemModifier

from Sources.frenkeyLib.ItemHandling.Mods.types import ItemModifierParam, ItemUpgradeId, ModifierIdentifier

@dataclass(frozen=True)
class DecodedModifier:
    modifier: ItemModifier
    raw_identifier: int
    identifier: ModifierIdentifier
    param: ItemModifierParam
    arg1: int
    arg2: int
    arg: int
    raw_bits: int
    upgrade_id: ItemUpgradeId
    flags: int
    
    @staticmethod
    def _parse_raw_bits(value) -> int:
        if isinstance(value, int):
            return value

        if not isinstance(value, str):
            raise TypeError("Invalid raw modifier type")

        value = value.strip()

        # Binary
        if all(c in "01" for c in value):
            return int(value, 2)

        # Hex
        if value.lower().startswith("0x"):
            return int(value, 16)

        # Decimal fallback
        return int(value)
    
    @classmethod
    def from_runtime(cls, modifier : ItemModifier) -> Optional["DecodedModifier"]:
        if modifier is None or not modifier.IsValid():
            return None

        runtime_identifier = modifier.GetIdentifier()
        stripped_identifier = (runtime_identifier >> 4) & 0x3FF
        raw_identifier = runtime_identifier
        if stripped_identifier not in ModifierIdentifier._value2member_map_:
            return None
        
        raw = cls._parse_raw_bits(modifier.GetModBits())

        identifier = ModifierIdentifier(stripped_identifier)
        param_value = ItemModifierParam((runtime_identifier  >> 16) & 0xF)
        upgrade_id = ItemUpgradeId(raw & 0xFFFF) if (raw & 0xFFFF) in ItemUpgradeId._value2member_map_ else ItemUpgradeId.Unknown
        flags = (raw >> 30) & 0x3

        arg1 = modifier.GetArg1()
        arg2 = modifier.GetArg2()

        return cls(
            modifier=modifier,
            raw_identifier=raw_identifier,
            identifier=identifier,
            param=param_value,
            arg1=arg1,
            arg2=arg2,
            arg=(arg1 << 8) | arg2,
            raw_bits=raw,
            upgrade_id=upgrade_id,
            flags=flags,
        )