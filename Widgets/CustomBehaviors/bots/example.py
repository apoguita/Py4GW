from typing import Any, Generator, override
from Py4GWCoreLib import Botting
from Widgets.CustomBehaviors.primitives.botting.botting_abstract import BottingAbstract
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers

class Example(BottingAbstract):
    def __init__(self):
        super().__init__()

    @override
    def bot_routine(self, bot_instance: Botting):
        # Set up the FSM states properly
        bot_instance.States.AddHeader("STARTING_POINT")
        bot_instance.Party.SetHardMode(False)
        bot_instance.States.AddHeader("MAIN_LOOP")
        bot_instance.States.JumpToStepName("[H]STARTING_POINT_1")

    @property
    @override
    def name(self) -> str:
        return "Example"

    @property
    @override
    def description(self) -> str:
        return "A bot template example"

example = Example()
example.open_bot()

def main():
    example.act()

def configure():
    pass

__all__ = ["main", "configure"]

