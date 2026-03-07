"""
Recipes - Higher-level building blocks for common bot patterns.

Each recipe provides two APIs:

- Phase factory (uppercase) - returns a Phase for ModularBot:
    ``Route(...)``, ``Mission(...)``, ``Quest(...)``

- Direct function (lowercase) - registers states on a Botting instance:
    ``route_run(bot, ...)``, ``mission_run(bot, ...)``, ``quest_run(bot, ...)``
"""

# Phase factories (uppercase)
from .route import Route
from .mission import Mission
from .quest import Quest

# Direct functions (lowercase)
from .route import route_run, list_available_routes
from .mission import mission_run, list_available_missions
from .quest import quest_run, list_available_quests

__all__ = [
    "Route",
    "Mission",
    "Quest",
    "route_run",
    "mission_run",
    "quest_run",
    "list_available_routes",
    "list_available_missions",
    "list_available_quests",
]
