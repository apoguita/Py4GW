
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
            if self.callback is not None:
                if not self.triggered:
                    if self.should_trigger():
                        self.triggered = True
                        self._fire_once()
                else:
                    if self.should_reset():
                        self.triggered = False
            else:
                self.triggered = False  # no callback means no triggering
            yield from Routines.Yield.wait(self.interval_ms)

# ---------- Concrete events ----------
class OnDeathEvent(Event):
    
    def should_trigger(self) -> bool:
        from Py4GWCoreLib import GLOBAL_CACHE  # local import!
        dead = GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID())
        if dead:
            print("OnDeathEvent triggered")
        return dead

    def should_reset(self) -> bool:
        from Py4GWCoreLib import GLOBAL_CACHE, Routines
        if not Routines.Checks.Map.MapValid():
            return True
        
        return not GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID())

class OnPartyDefeated(Event):
    def should_trigger(self) -> bool:
        from Py4GWCoreLib import GLOBAL_CACHE  # <- you were missing this import
        return GLOBAL_CACHE.Party.IsPartyDefeated()

    def should_reset(self) -> bool:
        from Py4GWCoreLib import GLOBAL_CACHE, Routines
        if not Routines.Checks.Map.MapValid():
            return True
        return not GLOBAL_CACHE.Party.IsPartyDefeated()
    
class OnPartyWipe(Event):
    def should_trigger(self):
        from ..Routines import Checks  # local import to avoid cycles
        return Checks.Party.IsPartyWiped()
    
    def should_reset(self):
        from ..Routines import Checks, Routines
        if not Routines.Checks.Map.MapValid():
            return True
        return not Checks.Party.IsPartyWiped()
    
class OnPartyMemberDead(Event):
    def should_trigger(self):
        from ..Routines import Checks  # local import to avoid cycles
        return Checks.Party.IsPartyMemberDead()
    
    def should_reset(self):
        from ..Routines import Checks, Routines
        if not Routines.Checks.Map.MapValid():
            return True
        return not Checks.Party.IsPartyMemberDead()
    
class OnPartyMemberBehind(Event):
    def should_trigger(self):
        from ..Routines import Checks  # local import to avoid cycles
        return Checks.Party.IsPartyMemberBehind()
    
    def should_reset(self):
        from ..Routines import Checks, Routines
        if not Routines.Checks.Map.MapValid():
            return True
        return not Checks.Party.IsPartyMemberBehind()
    
class OnPartyMemberDeadBehind(Event):
    def should_trigger(self):
        from ..Routines import Checks  # local import to avoid cycles
        return Checks.Party.IsDeadPartyMemberBehind()
    
    def should_reset(self):
        from ..Routines import Checks, Routines
        if not Routines.Checks.Map.MapValid():
            return True
        return not Checks.Party.IsDeadPartyMemberBehind()
    
class OnStuck(Event):
    def __init__(self, parent: "BotConfig", name: str = "OnStuckEvent", *, interval_ms: int = 1000, callback=None, active= False):
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
        self.active = active
        
    def set_in_waiting_routine(self, value: bool):
        self.in_waiting_routine = value

    def set_finished_routine(self, value: bool):
        self.finished_routine = value
        
    def set_in_killing_routine(self, value: bool):
        self.in_killing_routine = value
        
    def set_active(self, value: bool):
        self.active = value

    def should_trigger(self) -> bool:
        from Py4GWCoreLib import GLOBAL_CACHE, Routines

        if not self.active:
            return False

        def _reset_counter():
            self.in_killing_routine = False
            self.finished_routine = False
            self.in_waiting_routine = False
            self.timer_was_expired = False
            was_stuck = self.stuck_counter > 0   # <-- check if we were stuck
            self.stuck_counter = 0
            return was_stuck                     # <-- fire once when clearing

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
                return True   # stuck
            else:
                self.old_player_position = current_player_pos
                return _reset_counter()  # clears + signals if we were stuck

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
        self.stuck_enabled = False
        self.on_stuck = OnStuck(parent, "OnStuckEvent", interval_ms=1000, active=self.stuck_enabled)
        self.on_party_member_behind = OnPartyMemberBehind(parent, "OnPartyMemberBehindEvent", interval_ms=1000)
        self.on_party_member_dead_behind = OnPartyMemberDeadBehind(parent, "OnPartyMemberDeadBehindEvent", interval_ms=1000)
        self.on_party_member_dead = OnPartyMemberDead(parent, "OnPartyMemberDeadEvent", interval_ms=1000)


    # Optional convenience: set callbacks
    def set_on_death_callback(self, fn: Callable[[], None]) -> None:
        self.on_death.set_callback(fn)

    def set_on_party_defeated_callback(self, fn: Callable[[], None]) -> None:
        self.on_party_defeated.set_callback(fn)
        
    def set_on_party_wipe_callback(self, fn: Callable[[], None]) -> None:
        self.on_party_wipe.set_callback(fn)
        
    def set_on_stuck_callback(self, fn: Callable[[], None]) -> None:
        self.on_stuck.set_callback(fn)
        
    def set_stuck_routine_enabled(self, state: bool) -> None:
        self.stuck_enabled = state
        self.on_stuck.set_active(state)
        
    def set_on_party_member_behind_callback(self, fn: Callable[[], None]) -> None:
        self.on_party_member_behind.set_callback(fn)

    def set_on_party_member_dead_behind_callback(self, fn: Callable[[], None]) -> None:
        self.on_party_member_dead_behind.set_callback(fn)
        
    def set_on_party_member_dead_callback(self, fn: Callable[[], None]) -> None:
        self.on_party_member_dead.set_callback(fn)

    # Start/stop all (names are arbitrary; use your FSM’s dedupe)
    def start(self) -> None:
        fsm = self.parent.FSM
        fsm.AddManagedCoroutine("OnDeathEvent", self.on_death.run())
        fsm.AddManagedCoroutine("OnPartyDefeatedEvent", self.on_party_defeated.run())
        fsm.AddManagedCoroutine("OnPartyWipeEvent", self.on_party_wipe.run())
        fsm.AddManagedCoroutine("OnStuckEvent", self.on_stuck.run())
        fsm.AddManagedCoroutine("OnPartyMemberBehindEvent", self.on_party_member_behind.run())
        fsm.AddManagedCoroutine("OnPartyMemberDeadBehindEvent", self.on_party_member_dead_behind.run())

    def stop(self) -> None:
        fsm = self.parent.FSM
        fsm.RemoveManagedCoroutine("OnDeathEvent")
        fsm.RemoveManagedCoroutine("OnPartyDefeatedEvent")
        fsm.RemoveManagedCoroutine("OnPartyWipeEvent")
        fsm.RemoveManagedCoroutine("OnStuckEvent")
        fsm.RemoveManagedCoroutine("OnPartyMemberBehindEvent")
        fsm.RemoveManagedCoroutine("OnPartyMemberDeadBehindEvent")

