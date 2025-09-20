
from __future__ import annotations
from typing import Callable, Optional

from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .config import BotConfig  # for type checkers only
    
class Event:
    """
    Subclass overrides should_trigger() and should_reset().
    set_callback() assigns a single callback fired once per trigger cycle.
    run() is the forever-yielding coroutine you give to the FSM.
    """
    def __init__(self, parent: "BotConfig", name: str, *,
                 interval_ms: int = 250,
                 callback: Optional[Callable[[], None]] = None):
        self.parent = parent
        self.name = name
        self.interval_ms = interval_ms
        self.callback = callback
        self.triggered = False  # latched after fire until reset

    def set_callback(self, fn: Optional[Callable[[], None]]) -> None:
        self.callback = fn

    # ---- subclass hooks ----
    def should_trigger(self) -> bool:
        return False

    def should_reset(self) -> bool:
        return True

    # ---- driver ----
    def _fire_once(self) -> None:
        if self.callback:
            self.callback()

    def run(self):
        """Forever coroutine: trigger -> fire once -> wait until reset."""
        from Py4GWCoreLib import Routines  # local import to avoid cycles
        while True:
            if not self.triggered:
                if self.should_trigger():
                    self.triggered = True
                    self._fire_once()
            else:
                if self.should_reset():
                    self.triggered = False
            yield from Routines.Yield.wait(self.interval_ms)

# ---------- Concrete events ----------
class OnDeathEvent(Event):
    
    def should_trigger(self) -> bool:
        from Py4GWCoreLib import GLOBAL_CACHE  # local import!
        return GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID())

    def should_reset(self) -> bool:
        from Py4GWCoreLib import GLOBAL_CACHE
        return not GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID())

class OnPartyDefeated(Event):
    def should_trigger(self) -> bool:
        from Py4GWCoreLib import GLOBAL_CACHE  # <- you were missing this import
        return GLOBAL_CACHE.Party.IsPartyDefeated()

    def should_reset(self) -> bool:
        from Py4GWCoreLib import GLOBAL_CACHE
        return not GLOBAL_CACHE.Party.IsPartyDefeated()
    
class OnPartyWipe(Event):
    def should_trigger(self):
        from ..Routines import Checks  # local import to avoid cycles
        return Checks.Party.IsPartyWiped()
    
    def should_reset(self):
        from ..Routines import Checks  # local import to avoid cycles
        return not Checks.Party.IsPartyWiped()
    
class OnStuck(Event):
    def __init__(self, parent: "BotConfig", name: str = "OnStuckEvent", *, interval_ms: int = 1000, callback=None):
        super().__init__(parent, name, interval_ms=interval_ms, callback=callback)

        from Py4GWCoreLib import ThrottledTimer, BuildMgr  # local import to avoid cycles
        self.movement_check_timer = ThrottledTimer(3000)
        self.movement_check_timer.Start()
        self.stuck_counter = 0
        self.old_player_position = (0, 0)
        self.stuck_timer = ThrottledTimer(5000)
        self.stuck_timer.Start()
        self.in_waiting_routine = False
        self.finished_routine = False
        self.in_killing_routine = False
        
    def set_in_waiting_routine(self, value: bool):
        self.in_waiting_routine = value

    def set_finished_routine(self, value: bool):
        self.finished_routine = value
        
    def set_in_killing_routine(self, value: bool):
        self.in_killing_routine = value

    def should_trigger(self) -> bool:
        from Py4GWCoreLib import GLOBAL_CACHE, Routines

        def _reset_counter():
            self.in_killing_routine = False
            self.finished_routine = False
            self.in_waiting_routine = False
            self.timer_was_expired = False
            self.stuck_counter = 0
            return False

        if not Routines.Checks.Map.MapValid():
            return _reset_counter()
        if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            return _reset_counter()

        if self.in_waiting_routine or self.finished_routine or self.in_killing_routine:
            self.stuck_counter = 0
            self.stuck_timer.Reset()
            return False

        if self.stuck_timer.IsExpired():
            GLOBAL_CACHE.Player.SendChatCommand("stuck")
            self.stuck_timer.Reset()
          
        if self.movement_check_timer.IsExpired():
            current_player_pos = GLOBAL_CACHE.Player.GetXY()
            self.timer_was_expired = True
            self.movement_check_timer.Reset()
            if self.old_player_position == current_player_pos:
                GLOBAL_CACHE.Player.SendChatCommand("stuck")
                self.stuck_counter += 1
                return True
            else:
                self.old_player_position = current_player_pos
                return _reset_counter()

        return False
                
    def should_reset(self) -> bool:
        # once triggered and handled, reset the counter
        self.stuck_counter = 0
        result = self.stuck_counter == 0 or self.timer_was_expired
        self.timer_was_expired = False
        return result


# ---------- Container ----------
class Events:
    """
    Holds ready-made event instances and exposes tiny helpers
    to start/stop them on your FSM.
    """
    def __init__(self, parent: "BotConfig"):
        self.parent = parent
        self.on_death = OnDeathEvent(parent, "OnDeathEvent", interval_ms=250)
        self.on_party_defeated = OnPartyDefeated(parent, "OnPartyDefeatedEvent", interval_ms=250)
        self.on_party_wipe = OnPartyWipe(parent, "OnPartyWipeEvent", interval_ms=250)
        self.on_stuck = OnStuck(parent, "OnStuckEvent", interval_ms=1000)

    # Optional convenience: set callbacks
    def set_on_death_callback(self, fn: Callable[[], None]) -> None:
        self.on_death.set_callback(fn)

    def set_on_party_defeated_callback(self, fn: Callable[[], None]) -> None:
        self.on_party_defeated.set_callback(fn)
        
    def set_on_party_wipe_callback(self, fn: Callable[[], None]) -> None:
        self.on_party_wipe.set_callback(fn)
        
    def set_on_stuck_callback(self, fn: Callable[[], None]) -> None:
        self.on_stuck.set_callback(fn)

    # Start/stop all (names are arbitrary; use your FSM’s dedupe)
    def start(self) -> None:
        fsm = self.parent.FSM
        fsm.AddManagedCoroutine("OnDeathEvent", self.on_death.run())
        fsm.AddManagedCoroutine("OnPartyDefeatedEvent", self.on_party_defeated.run())
        fsm.AddManagedCoroutine("OnPartyWipeEvent", self.on_party_wipe.run())
        fsm.AddManagedCoroutine("OnStuckEvent", self.on_stuck.run())

    def stop(self) -> None:
        fsm = self.parent.FSM
        fsm.RemoveManagedCoroutine("OnDeathEvent")
        fsm.RemoveManagedCoroutine("OnPartyDefeatedEvent")
        fsm.RemoveManagedCoroutine("OnPartyWipeEvent")
        fsm.RemoveManagedCoroutine("OnStuckEvent")

