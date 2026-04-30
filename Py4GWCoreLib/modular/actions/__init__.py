"""Public modular action helpers."""
from __future__ import annotations

from .registry import (
    get_action_node,
    get_action_node_metadata,
    get_action_node_specs,
    get_action_nodes,
    get_registered_step_types,
    register_action_node,
)
from .runtime import register_runtime_action, run_step, run_steps

_LAZY_EXPORTS = {
    "DEFAULT_NPC_SELECTORS": (
        "Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.actions_inventory",
        "DEFAULT_NPC_SELECTORS",
    ),
    "SUPPORTED_MAP_NPC_SELECTORS": (
        "Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.actions_inventory",
        "SUPPORTED_MAP_NPC_SELECTORS",
    ),
    "resolve_agent_xy_from_step": (
        "Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.step_selectors",
        "resolve_agent_xy_from_step",
    ),
    "resolve_enemy_agent_id_from_step": (
        "Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.step_selectors",
        "resolve_enemy_agent_id_from_step",
    ),
    "resolve_item_model_id_from_step": (
        "Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.step_selectors",
        "resolve_item_model_id_from_step",
    ),
    "resolve_active_engine": (
        "Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.combat_engine",
        "resolve_active_engine",
    ),
    "resolve_engine_for_bot": (
        "Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.combat_engine",
        "resolve_engine_for_bot",
    ),
    "outbound_messages_done": (
        "Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.combat_engine",
        "outbound_messages_done",
    ),
    "set_auto_combat": (
        "Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.combat_engine",
        "set_auto_combat",
    ),
    "set_auto_looting": (
        "Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.combat_engine",
        "set_auto_looting",
    ),
    "set_auto_following": (
        "Py4GWCoreLib.routines_src.behaviourtrees_src.modular_core.combat_engine",
        "set_auto_following",
    ),
}


def __getattr__(name: str):
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = target
    from importlib import import_module

    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value

__all__ = [
    "get_registered_step_types",
    "get_action_node",
    "get_action_nodes",
    "get_action_node_metadata",
    "get_action_node_specs",
    "register_action_node",
    "register_runtime_action",
    "run_step",
    "run_steps",
    "DEFAULT_NPC_SELECTORS",
    "SUPPORTED_MAP_NPC_SELECTORS",
    "resolve_agent_xy_from_step",
    "resolve_enemy_agent_id_from_step",
    "resolve_item_model_id_from_step",
    "resolve_active_engine",
    "resolve_engine_for_bot",
    "outbound_messages_done",
    "set_auto_combat",
    "set_auto_looting",
    "set_auto_following",
]
