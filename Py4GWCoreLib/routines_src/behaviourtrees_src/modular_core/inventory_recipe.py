"""
inventory_recipe module

This module is part of the modular runtime surface.
"""
from __future__ import annotations

from typing import Any

from Py4GWCoreLib.enums_src.Model_enums import ModelID

DEFAULT_ID_KITS_TARGET = 3
DEFAULT_SALVAGE_KITS_TARGET = 10
DEFAULT_MATERIAL_MODE = "deposit_cons_sell_non_cons"

CONS_COMMON_MATERIAL_MODEL_IDS: tuple[int, ...] = (
    int(ModelID.Bone.value),
    int(ModelID.Pile_Of_Glittering_Dust.value),
    int(ModelID.Feather.value),
    int(ModelID.Iron_Ingot.value),
)

NON_CONS_COMMON_MATERIAL_MODEL_IDS: tuple[int, ...] = (
    int(ModelID.Bolt_Of_Cloth.value),
    int(ModelID.Chitin_Fragment.value),
    int(ModelID.Granite_Slab.value),
    int(ModelID.Plant_Fiber.value),
    int(ModelID.Scale.value),
    int(ModelID.Tanned_Hide_Square.value),
    int(ModelID.Wood_Plank.value),
)


def _parse_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("1", "true", "yes", "on"):
            return True
        if normalized in ("0", "false", "no", "off"):
            return False
    return default


def _parse_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _infer_return_map_id(recipe_kind: str, data: dict[str, Any]) -> int:
    if recipe_kind == "quest":
        take_quest = data.get("take_quest") or {}
        return _parse_int(take_quest.get("outpost_id", 0), 0)

    if recipe_kind == "mission":
        entry = data.get("entry") or {}
        entry_map_id = _parse_int(entry.get("target_map_id", 0), 0)
        if entry_map_id > 0:
            return entry_map_id
        return _parse_int(data.get("outpost_id", 0), 0)

    return 0


def build_auto_inventory_guard_step(recipe_kind: str, data: dict[str, Any]) -> dict[str, Any] | None:
    inventory = data.get("inventory")
    if inventory is False:
        return None

    inventory_cfg = inventory if isinstance(inventory, dict) else {}
    if not _parse_bool(inventory_cfg.get("enabled", True), True):
        return None

    return_map_id = _infer_return_map_id(recipe_kind, data)
    if return_map_id <= 0:
        return None

    id_target = max(0, _parse_int(inventory_cfg.get("id_kits_target", DEFAULT_ID_KITS_TARGET), DEFAULT_ID_KITS_TARGET))
    salvage_target = max(
        0,
        _parse_int(inventory_cfg.get("salvage_kits_target", DEFAULT_SALVAGE_KITS_TARGET), DEFAULT_SALVAGE_KITS_TARGET),
    )
    id_min_default = id_target
    salvage_min_default = salvage_target

    return {
        "type": "inventory_guard",
        "name": str(inventory_cfg.get("name", "Inventory Guard")),
        "check_on_start": _parse_bool(inventory_cfg.get("check_on_start", True), True),
        "multibox": _parse_bool(inventory_cfg.get("multibox", True), True),
        "leave_party": _parse_bool(inventory_cfg.get("leave_party", True), True),
        "location": str(inventory_cfg.get("location", "auto") or "auto"),
        "return_map_id": return_map_id,
        "id_kits_min": max(0, _parse_int(inventory_cfg.get("id_kits_min", id_min_default), id_min_default)),
        "salvage_kits_min": max(0, _parse_int(inventory_cfg.get("salvage_kits_min", salvage_min_default), salvage_min_default)),
        "id_kits_target": id_target,
        "salvage_kits_target": salvage_target,
        "restock_consumables": _parse_bool(inventory_cfg.get("restock_consumables", False), False),
        "buy_ectoplasm": _parse_bool(inventory_cfg.get("buy_ectoplasm", False), False),
        "material_mode": str(inventory_cfg.get("material_mode", DEFAULT_MATERIAL_MODE) or DEFAULT_MATERIAL_MODE),
    }
