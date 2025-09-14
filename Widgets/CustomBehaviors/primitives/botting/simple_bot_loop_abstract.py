from abc import abstractmethod
from typing import Any, Generator
from Widgets.CustomBehaviors.primitives.botting.botting_abstract import BottingAbstract


class SimpleBotLoopAbstract(BottingAbstract):
    def __init__(self):
        super().__init__()

    @property
    @abstractmethod
    def outpost_id(self) -> int:
        pass

    @property
    @abstractmethod
    def leave_outpost_coords(self) -> list[tuple[float, float]]:
        pass

    @property
    @abstractmethod
    def explorable_area_id(self) -> int:
        pass

    @property
    @abstractmethod
    def explorable_area_coords(self) -> list[tuple[float, float]]:
        pass
    
    def act(self)-> Generator[Any, None, bool]:
        while(True):
            result = yield from self.__teleport_to_outpost()
            if result == False:continue

            result = yield from self._move_to_explorable_area()
            if result == False:continue

            result = yield from self.__move_across_coords_and_kill_if_needed()
            if result == False:continue

            result = yield from self.__wait_being_back_to_outpost()
            if result == False:continue
            
            yield