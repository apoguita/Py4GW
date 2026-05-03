"""
modular_bot - Modular Bot Builder with native BottingTree orchestration.

Build bots by composing `Phase` objects. Each phase can keep using the current
modular state-registration surface, while `ModularBot` runs chaining through
named planner steps on `BottingTree`.
"""

from .phase import Phase
from .bot import ModularBot
from .actions import register_action_node
from .domain import get_target_registry

# Recipes are importable via Py4GWCoreLib.modular.recipes
# e.g.: from Py4GWCoreLib.modular.recipes import Route, Mission

__all__ = [
    "ModularBot",
    "Phase",
    "register_action_node",
    "get_target_registry",
]
__version__ = "1.1.0"
