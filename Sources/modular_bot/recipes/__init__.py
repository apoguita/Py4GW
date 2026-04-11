"""
Recipes - Higher-level building blocks for common bot patterns.

Each recipe provides two APIs:

- Phase factory (uppercase) - returns a Phase for ModularBot:
    ``ModularBlock(...)`` and compatibility aliases
    ``Route(...)``, ``Mission(...)``, ``Quest(...)``, ``Farm(...)``,
    ``Dungeon(...)``, ``Vanquish(...)``, ``Bounty(...)``

- Direct function (lowercase) - registers states on a Botting instance:
    ``modular_block_run(bot, ...)`` and compatibility aliases
    ``route_run(bot, ...)``, ``mission_run(bot, ...)``, ``quest_run(bot, ...)``,
    ``farm_run(bot, ...)``, ``dungeon_run(bot, ...)``, ``vanquish_run(bot, ...)``,
    ``bounty_run(bot, ...)``
"""

# Unified modular block API
from .modular_block import ModularBlock, modular_block_run, list_available_blocks

# Backward-compatible aliases
from .modular_block import (
    Route,
    Mission,
    Quest,
    Farm,
    Dungeon,
    Vanquish,
    Bounty,
    route_run,
    mission_run,
    quest_run,
    farm_run,
    dungeon_run,
    vanquish_run,
    bounty_run,
    list_available_routes,
    list_available_missions,
    list_available_quests,
    list_available_farms,
    list_available_dungeons,
    list_available_vanquishes,
    list_available_bounties,
)

__all__ = [
    "ModularBlock",
    "modular_block_run",
    "list_available_blocks",
    "Route",
    "Mission",
    "Quest",
    "Farm",
    "Dungeon",
    "Vanquish",
    "Bounty",
    "route_run",
    "mission_run",
    "quest_run",
    "farm_run",
    "dungeon_run",
    "vanquish_run",
    "bounty_run",
    "list_available_routes",
    "list_available_missions",
    "list_available_quests",
    "list_available_farms",
    "list_available_dungeons",
    "list_available_vanquishes",
    "list_available_bounties",
]
