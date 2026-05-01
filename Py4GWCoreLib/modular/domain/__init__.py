"""
domain package exports

This module is part of the modular runtime surface.
"""
from .contracts import ModularPhaseRuntimeSpec, SelectorSpec, StepSpec
from .target_registry import (
    AgentTargetDefinition,
    AgentTargetValue,
    ENEMY_TARGETS,
    GADGET_TARGETS,
    NPC_TARGETS,
    TargetRegistryKind,
    get_named_agent_target,
    get_target_registry,
)

__all__ = [
    "AgentTargetDefinition",
    "AgentTargetValue",
    "ENEMY_TARGETS",
    "GADGET_TARGETS",
    "ModularPhaseRuntimeSpec",
    "NPC_TARGETS",
    "SelectorSpec",
    "StepSpec",
    "TargetRegistryKind",
    "get_named_agent_target",
    "get_target_registry",
]
