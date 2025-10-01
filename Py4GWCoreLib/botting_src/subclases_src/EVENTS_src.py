#region STATES
from typing import TYPE_CHECKING, Dict, Callable, Any

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass


#region EVENTS
class _EVENTS:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers
        self._events = parent.config.events

    def OnDeathCallback(self, callback: Callable[[], None]) -> None:
        self._config.events.on_death.set_callback(callback)

    def OnPartyWipeCallback(self, callback: Callable[[], None]) -> None:
        self._config.events.on_party_wipe.set_callback(callback)

    def OnPartyDefeatedCallback(self, callback: Callable[[], None]) -> None:
        self._config.events.on_party_defeated.set_callback(callback)
        
    #def OnStuckCallback(self, callback: Callable[[], None]) -> None:
    #    self._config.events.on_stuck.set_callback(callback)
        
    #def SetStuckRoutineEnabled(self, state: bool) -> None:
    #    self._config.events.set_stuck_routine_enabled(state)
        
    def OnPartyMemberBehindCallback(self, callback: Callable[[], None]) -> None:
        self._config.events.set_on_party_member_behind_callback(callback)

    def OnPartyMemberDeadCallback(self, callback: Callable[[], None]) -> None:
        self._config.events.set_on_party_member_dead_callback(callback)
        
    def OnPartyMemberDeadBehindCallback(self, callback: Callable[[], None]) -> None:
        self._config.events.set_on_party_member_dead_behind_callback(callback)