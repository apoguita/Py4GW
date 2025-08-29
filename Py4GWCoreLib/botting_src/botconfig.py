
from __future__ import annotations
from typing import Callable, Optional, List, Tuple


from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..Botting import BottingClass  # for type checkers only
    
from ..SkillManager import SkillManager
from ..Py4GWcorelib import FSM
from .property import StepNameCounters, UpkeepData, ConfigProperties
from .event import Events
    

class BotConfig:
    def __init__(self, parent: "BottingClass",  bot_name: str):
        self.parent:"BottingClass" = parent
        self.bot_name:str = bot_name
        self.initialized:bool = False
        self.FSM = FSM(bot_name)
        self.fsm_running:bool = False
        self.auto_combat_handler:SkillManager.Autocombat = SkillManager.Autocombat()

        self.counters = StepNameCounters()
        
        self.path:List[Tuple[float, float]] = []
        self.path_to_draw:List[Tuple[float, float]] = []
        
        #Overridable functions
        self.pause_on_danger_fn: Callable[[], bool] = lambda: False
        self._reset_pause_on_danger_fn()
        self.on_follow_path_failed: Callable[[], bool] = lambda: False
        
        #Properties
        self.config_properties = ConfigProperties(self)

        self.upkeep = UpkeepData(self)
        self.events = Events(self)



    def get_counter(self, name: str) -> Optional[int]:
        return self.counters.next_index(name)
   
    def _set_pause_on_danger_fn(self, executable_fn: Callable[[], bool]) -> None:
        self.pause_on_danger_fn = executable_fn
               
    def _reset_pause_on_danger_fn(self) -> None:
        from ..Routines import Checks  # local import to avoid cycles
        from ..Py4GWcorelib import Range
        self._set_pause_on_danger_fn(lambda: Checks.Agents.InDanger(aggro_area=Range.Earshot) or Checks.Party.IsPartyMemberDead() or Checks.Player.IsCasting())

    def _set_on_follow_path_failed(self, on_follow_path_failed: Callable[[], bool]) -> None:
        from ..Py4GWcorelib import ConsoleLog
        import Py4GW
        self.on_follow_path_failed = on_follow_path_failed
        if self.config_properties.log_actions.is_active():
            ConsoleLog("OnFollowPathFailed", f"Set OnFollowPathFailed to {on_follow_path_failed}", Py4GW.Console.MessageType.Info)


    #FSM HELPERS
    def set_pause_on_danger_fn(self, pause_on_combat_fn: Callable[[], bool]) -> None:
        self.FSM.AddState(name=f"PauseOnDangerFn_{self.get_counter("PAUSE_ON_DANGER")}",
                          execute_fn=lambda:self._set_pause_on_danger_fn(pause_on_combat_fn),)

    def reset_pause_on_danger_fn(self) -> None:
        self._reset_pause_on_danger_fn()
        self.FSM.AddState(name=f"ResetPauseOnDangerFn_{self.get_counter("PAUSE_ON_DANGER")}",
                          execute_fn=lambda:self._reset_pause_on_danger_fn(),)

    def set_on_follow_path_failed(self, on_follow_path_failed: Callable[[], bool]):
        self.FSM.AddState(name=f"OnFollowPathFailed_{self.get_counter("ON_FOLLOW_PATH_FAILED")}",
                          execute_fn=lambda:self._set_on_follow_path_failed(on_follow_path_failed),)

    def reset_on_follow_path_failed(self) -> None:
        self.set_on_follow_path_failed(lambda: self.parent.helpers.default_on_unmanaged_fail())

