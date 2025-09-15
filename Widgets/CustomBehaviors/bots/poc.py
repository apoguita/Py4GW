from typing import Any, Generator, override
from Py4GWCoreLib import Botting
from Widgets.CustomBehaviors.primitives.botting.botting_abstract import BottingAbstract
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers

class poc(BottingAbstract):
    def __init__(self):
        super().__init__()
        self.bot = Botting("qzd")
        self.bot.SetMainRoutine(self.bot_routine)

    def bot_routine(self):
            self.bot.Map.Travel(target_map_id=640) #Ratasum outpost
            self.bot.Party.SetHardMode(True)

            self.bot.States.AddHeader("EXIT OUTPOST HEADER")
            self.bot.UI.PrintMessageToConsole("Debug", "Added header: EXIT OUTPOST HEADER")
            self.bot.Move.XY(-6062, -2688,"Exit Outpost")
            self.bot.Wait.ForMapLoad(target_map_id=569)

            self.bot.Move.XY(15013, 13111)
            self.bot.Wait.ForTime(2000)

            self.bot.Wait.UntilOutOfCombat()
            self.bot.helpers.Multibox.resign_party()
            self.bot.UI.PrintMessageToConsole("qzd farm", "Finished routine")
            self.bot.States.JumpToStepName("EXIT OUTPOST HEADER")

    @override
    def  _act(self) -> Generator[Any | None, Any | None, Any | None]:
        self.bot.Update()
        yield
        

