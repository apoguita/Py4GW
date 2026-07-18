"""Target registry exports for modular BT selectors."""
from __future__ import annotations

from .target_registry import AgentTargetDefinition
from .target_registry import AgentTargetValue
from .target_registry import ENEMY_TARGETS
from .target_registry import GADGET_TARGETS
from .target_registry import NPC_TARGETS
from .target_registry import TargetRegistryKind
from .target_registry import get_named_agent_target
from .target_registry import get_target_registry

__all__ = [
    "AgentTargetDefinition",
    "AgentTargetValue",
    "ENEMY_TARGETS",
    "GADGET_TARGETS",
    "NPC_TARGETS",
    "TargetRegistryKind",
    "get_named_agent_target",
    "get_target_registry",
]
