"""Test bot: Route recipe."""

from Sources.modular_bot import ModularBot
from Sources.modular_bot.recipes import Route

bot = ModularBot(
    name="Test: Route",
    phases=[
        Route("la_to_beacons"),
    ],
    loop=False,
)


def main():
    bot.update()
