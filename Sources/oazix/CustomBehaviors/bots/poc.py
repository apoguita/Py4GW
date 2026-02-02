from typing import Any, Generator, override
from Py4GWCoreLib import Botting
from Sources.oazix.CustomBehaviors.primitives.botting.botting_abstract import BottingAbstract
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers

class poc():
    def __init__(self):
        super().__init__()
        self.bot = Botting("fffff")
        self.bot.SetMainRoutine(self.bot_routine)

    def bot_routine(self):
        # Set up the FSM states properly
        self.bot.States.AddHeader("MAIN_LOOP")
        self.bot.Map.Travel(target_map_id=476)
        self.bot.Party.SetHardMode(False)

        self.bot.States.AddHeader("EXIT_OUTPOST")
        self.bot.UI.PrintMessageToConsole("Debug", "Added header: EXIT_OUTPOST")
        self.bot.Move.XY(-6191, -2498, "Exit Outpost")
        self.bot.Wait.ForMapLoad(target_map_id=397)

        self.bot.States.AddHeader("MOVE_TO_FARM_AREA") #todo correct name
        self.bot.Move.XY(17360, 9436)
        self.bot.Wait.ForTime(2000)
        self.bot.Wait.ForMapLoad(target_map_id=xxx)

        self.bot.States.AddHeader("FARM_LOOP")
        # self.bot.Move.XY(17432, -14629)
        # todo the farm loop
        self.bot.Wait.ForTime(2000)
        self.bot.Wait.ForMapLoad(target_map_id=xxx)
        
        # Loop back to farm loop
        self.bot.States.JumpToStepName("MOVE_TO_FARM_AREA")

    @property
    @override
    def name(self) -> str:
        return "qzdqzd"

    @property
    @override
    def description(self) -> str:
        return "qzidjofdgdsfg"

    @override
    def _act(self) -> Generator[Any | None, Any | None, Any | None]:
        while True:
            if self.bot.config.FSM.current_state is not None:
                print(f"{self.bot.config.FSM.current_state.name}")
            self.bot.Update()
            self.bot.UI.draw_window()
            yield

qzd = poc()

def main():
    global qzd
    qzd.act()

def configure():
    pass

__all__ = ["main", "configure"]

