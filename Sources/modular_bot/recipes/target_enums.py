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
    "RASTIGAN_THE_ETERNAL": (((147, 60, 51, 178, 63, 250, 201, 17, 0, 0),), "Rastigan the Eternal"),
    "ETERNAL_FORGEMASTER": (((149, 60, 95, 250, 204, 193, 241, 13, 0, 0),), "Eternal Forgemaster"),
    "ETERNAL_LORD_TAERES": (((145, 60, 28, 148, 190, 146, 92, 75, 0, 0),), "Eternal Lord Taeres"),
    "ETERNAL_WEAPONSMITH": (((161, 60, 142, 182, 136, 229, 188, 67, 0, 0),), "Eternal Weaponsmith"),
    "KROMRIL_THE_ETERNAL": (((143, 60, 231, 221, 50, 213, 172, 33, 0, 0),), "Kromril the Eternal"),
    "MIKO_THE_UNCHAINED": (((153, 60, 144, 135, 227, 178, 148, 90, 0, 0),), "Miko the Unchained"),
    "NIMROS_THE_HUNTER": (((151, 60, 106, 254, 155, 244, 189, 59, 0, 0),), "Nimros the Hunter"),
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
