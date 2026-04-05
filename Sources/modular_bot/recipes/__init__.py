"""
Recipes - Higher-level building blocks for common bot patterns.

Each recipe provides two APIs:

- Phase factory (uppercase) - returns a Phase for ModularBot:
    ``ModularBlock(...)`` and compatibility aliases
    ``Route(...)``, ``Mission(...)``, ``Quest(...)``

- Direct function (lowercase) - registers states on a Botting instance:
    ``modular_block_run(bot, ...)`` and compatibility aliases
    ``route_run(bot, ...)``, ``mission_run(bot, ...)``, ``quest_run(bot, ...)``
"""

# Unified modular block API
from .modular_block import ModularBlock, modular_block_run, list_available_blocks

# Backward-compatible aliases
from .modular_block import (
    Route,
    Mission,
    Quest,
    Farm,
    route_run,
    mission_run,
    quest_run,
    farm_run,
    list_available_routes,
    list_available_missions,
    list_available_quests,
    list_available_farms,
)

__all__ = [
    "ModularBlock",
    "modular_block_run",
    "list_available_blocks",
    "Route",
    "Mission",
    "Quest",
    "Farm",
    "route_run",
    "mission_run",
    "quest_run",
    "farm_run",
    "list_available_routes",
    "list_available_missions",
    "list_available_quests",
    "list_available_farms",
]
