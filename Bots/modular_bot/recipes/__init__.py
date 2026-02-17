"""
Recipes — Higher-level building blocks for common bot patterns.

Each recipe provides two APIs:

- **Phase factory** (uppercase) — returns a Phase for ModularBot:
    ``Run(...)``, ``Mission(...)``

- **Direct function** (lowercase) — registers states on a Botting instance:
    ``run_route(bot, ...)``, ``mission_run(bot, ...)``

Examples:
    # ModularBot with recipes
    from modular_bot import ModularBot, Phase
    from modular_bot.recipes import Run, Mission

    bot = ModularBot(
        name="EotN Tour + Mission",
        phases=[
            Run("Eye Of The North - Full Tour", "_1_Eotn_To_Gunnars"),
            Run("Eye Of The North - Full Tour", "_2_Gunnars_To_Longeyes"),
            Mission("the_great_northern_wall"),
        ],
    )

    # Direct usage in a Botting routine
    from modular_bot.recipes import run_route, mission_run

    def my_routine(bot: Botting):
        run_route(bot, "Eye Of The North - Full Tour", "_1_Eotn_To_Gunnars")
        mission_run(bot, "the_great_northern_wall")
"""

# Phase factories (uppercase)
from .run import Run
from .mission import Mission

# Direct functions (lowercase)
from .run import run_route
from .mission import mission_run

__all__ = [
    # Phase factories
    "Run",
    "Mission",
    # Direct functions
    "run_route",
    "mission_run",
]
