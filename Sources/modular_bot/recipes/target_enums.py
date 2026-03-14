from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TargetRegistryKind(str, Enum):
    NPC = "npc"
    ENEMY = "enemy"
    GADGET = "gadget"
    ITEM = "item"


@dataclass(frozen=True)
class AgentTargetDefinition:
    display_name: str = ""
    encoded_names: tuple[tuple[int, ...], ...] = ()
    model_id: int | None = None


@dataclass(frozen=True)
class ItemTargetDefinition:
    display_name: str = ""
    model_id: int | None = None


AgentTargetValue = AgentTargetDefinition | tuple[tuple[int, ...], str] | tuple[tuple[tuple[int, ...], ...], str]
ItemTargetValue = ItemTargetDefinition | tuple[int, str]


NPC_TARGETS: dict[str, AgentTargetValue] = {
    "MERCHANT": ((223, 12, 0, 0), "Merchant"),
    "CRAFTING_MATERIAL_TRADER": (((218, 12, 0, 0),), "Crafting Material Trader"),
    "RARE_MATERIAL_TRADER": (((219, 12, 0, 0),), "Rare Material Trader"),
    "MARYANN_MERCHANT": (((2, 129, 174, 30, 76, 243, 39, 168, 94, 124, 0, 0),), "Maryann [Merchant]"),
    "IDA_MATERIAL_TRADER": (((2, 129, 176, 30, 206, 207, 175, 180, 46, 22, 0, 0),), "Ida [Material Trader]"),
    "ROLAND_RARE_MATERIAL_TRADER": (
        ((2, 129, 177, 30, 121, 158, 107, 174, 125, 37, 0, 0),),
        "Roland [Rare Material Trader]",
    ),
    "ADRIANA_MERCHANT": (((2, 129, 168, 30, 186, 208, 140, 169, 52, 21, 0, 0),), "Adriana [Merchant]"),
    "ANDERS_MATERIAL_TRADER": (((2, 129, 169, 30, 23, 235, 100, 134, 4, 116, 0, 0),), "Anders [Material Trader]"),
    "HELENA_RARE_MATERIAL_TRADER": (
        ((2, 129, 170, 30, 160, 235, 64, 210, 12, 77, 0, 0),),
        "Helena [Rare Material Trader]",
    ),
    "ABJORN_MERCHANT": (((2, 129, 182, 30, 106, 181, 11, 203, 35, 83, 0, 0),), "Abjorn [Merchant]"),
    "VATHI_MATERIAL_TRADER": (((2, 129, 183, 30, 66, 135, 156, 218, 94, 9, 0, 0),), "Vathi [Material Trader]"),
    "BIRNA_RARE_MATERIAL_TRADER": (
        ((2, 129, 184, 30, 4, 141, 74, 238, 47, 64, 0, 0),),
        "Birna [Rare Material Trader]",
    ),
    "LOKAI_MERCHANT": (((1, 129, 198, 63, 103, 215, 156, 210, 48, 50, 0, 0),), "Lokai [Merchant]"),
    "GUUL_MATERIAL_TRADER": (((1, 129, 199, 63, 243, 201, 146, 243, 222, 35, 0, 0),), "Guul [Material Trader]"),
    "NEHGOYO_RARE_MATERIAL_TRADER": (
        ((1, 129, 200, 63, 176, 139, 78, 232, 74, 58, 0, 0),),
        "Nehgoyo [Rare Material Trader]",
    ),
    "RASTIGAN_THE_ETERNAL": (((147, 60, 51, 178, 63, 250, 201, 17, 0, 0),), "Rastigan the Eternal"),
    "ETERNAL_FORGEMASTER": (((149, 60, 95, 250, 204, 193, 241, 13, 0, 0),), "Eternal Forgemaster"),
    "ETERNAL_LORD_TAERES": (((145, 60, 28, 148, 190, 146, 92, 75, 0, 0),), "Eternal Lord Taeres"),
    "ETERNAL_WEAPONSMITH": (((161, 60, 142, 182, 136, 229, 188, 67, 0, 0),), "Eternal Weaponsmith"),
    "KROMRIL_THE_ETERNAL": (((143, 60, 231, 221, 50, 213, 172, 33, 0, 0),), "Kromril the Eternal"),
    "MIKO_THE_UNCHAINED": (((153, 60, 144, 135, 227, 178, 148, 90, 0, 0),), "Miko the Unchained"),
    "NIMROS_THE_HUNTER": (((151, 60, 106, 254, 155, 244, 189, 59, 0, 0),), "Nimros the Hunter"),
    "NIKA": (((203, 94, 0, 243, 160, 248, 38, 109, 0, 0),), "Nika"),
    "FISHMONGER_BIHZUN": (((113, 96, 50, 191, 11, 216, 178, 28, 0, 0),), "Fishmonger Bihzun"),
    "LOUD_KOU": (((213, 95, 115, 159, 143, 243, 151, 49, 0, 0),), "Loud Kou"),
    "ADEPT_NAI": (((173, 76, 22, 253, 52, 170, 169, 27, 0, 0),), "Adept Nai"),
    "WAILING_LORD": (((40, 31, 154, 140, 42, 223, 196, 52, 0, 0),), "Wailing Lord"),
    # "TOWER_OF_COURAGE_NPC": (((1, 129, 216, 71, 88, 179, 225, 255, 119, 64, 0, 0),), "Tower of Courage NPC"),
}

ENEMY_TARGETS: dict[str, AgentTargetValue] = {
    "INFERNAL_WURM": (((225, 20, 149, 206, 31, 225, 185, 90, 0, 0),), "Infernal Wurm"),
    "SHARD_WOLF": (((77, 31, 140, 221, 57, 157, 245, 44, 0, 0),), "Shard Wolf"),
    "WAILING_LORD": (((26, 31, 5, 191, 239, 149, 25, 80, 0, 0),), "Wailing Lord"),
    # "FANGED_IBOGA": (((1, 2, 3, 4),), "Fanged Iboga"),
}

GADGET_TARGETS: dict[str, AgentTargetValue] = {
    "CHEST": (((123, 32, 56, 239, 111, 184, 88, 49, 0, 0),), "Chest"),
    "CHEST_OF_WOE": (((2, 129, 148, 49, 154, 172, 124, 229, 33, 98, 0, 0),), "Chest of Woe"),
    # "CHAOS_GATE": (((1, 2, 3, 4),), "Chaos Gate"),
}

ITEM_TARGETS: dict[str, ItemTargetValue] = {
    "UNHOLY_TEXT": (2619, "Unholy Text"),
    # "LOCKPICK": (22751, "Lockpick"),
}


def _normalize_agent_target(value: AgentTargetValue | None) -> AgentTargetDefinition | None:
    if value is None:
        return None
    if isinstance(value, AgentTargetDefinition):
        return value

    encoded_names_raw, display_name = value
    if encoded_names_raw and isinstance(encoded_names_raw[0], int):
        encoded_names = (tuple(int(v) for v in encoded_names_raw),)
    else:
        encoded_names = tuple(tuple(int(v) for v in encoded_name) for encoded_name in encoded_names_raw)

    return AgentTargetDefinition(
        display_name=str(display_name or ""),
        encoded_names=encoded_names,
    )


def _normalize_item_target(value: ItemTargetValue | None) -> ItemTargetDefinition | None:
    if value is None:
        return None
    if isinstance(value, ItemTargetDefinition):
        return value

    model_id, display_name = value
    return ItemTargetDefinition(
        display_name=str(display_name or ""),
        model_id=int(model_id),
    )


def get_named_agent_target(kind: str, key: Any) -> AgentTargetDefinition | None:
    key_str = str(key or "").strip()
    if not key_str:
        return None

    registries = {
        TargetRegistryKind.NPC.value: NPC_TARGETS,
        TargetRegistryKind.ENEMY.value: ENEMY_TARGETS,
        TargetRegistryKind.GADGET.value: GADGET_TARGETS,
    }
    return _normalize_agent_target(registries.get(kind, {}).get(key_str))


def get_named_item_target(key: Any) -> ItemTargetDefinition | None:
    key_str = str(key or "").strip()
    if not key_str:
        return None
    return _normalize_item_target(ITEM_TARGETS.get(key_str))
