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
        
    def _on_party_member_behind(self):
            from ...Routines import Routines
            from ...Py4GWcorelib import Utils
            from ...enums import Range
            from ...GlobalCache import GLOBAL_CACHE
            bot = self.parent

            left_direction  = True
            try:
                print("Party Member behind, emitting pixel stack")
                yield from Routines.Yield.Movement.StopMovement()

                retries = 0
                max_retries = 3  # <-- configurable number of retries
                emit_count = 0  # <--- added: count pixel-stack emits
                
                while retries < max_retries:
                    if Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated():
                        print("Party wiped, aborting OnPartyMemberBehind")
                        return
                    
                    
                    
                    yield from bot.helpers.Multibox._pixel_stack()
                    emit_count += 1
                    # call brute-force helper every 2 emits
                    if emit_count % 2 == 0:
                        yield from bot.helpers.Multibox._brute_force_unstuck()
                        
                    last_emit = Utils.GetBaseTimestamp()

                    # inner wait loop for this attempt
                    while not Routines.Checks.Party.IsAllPartyMembersInRange(Range.Spellcast.value):
                        yield from bot.helpers.Wait._for_time(500)

                        # re-emit pixel stack every 10s
                        now = Utils.GetBaseTimestamp()
                        if now - last_emit >= 10000:
                            print("Re-emitting pixel stack, and spinning in place!, weeeee")
                            yield from bot.helpers.Multibox._pixel_stack()
                            last_emit = now
                            emit_count += 1
                            # call brute-force helper every 2 emits
                            if emit_count % 2 == 0:
                                yield from bot.helpers.Multibox._brute_force_unstuck()


                        if not Routines.Checks.Agents.InDanger():
                            if left_direction:
                                yield from Routines.Yield.Movement.TurnLeft(300)
                                left_direction = False
                            else:
                                yield from Routines.Yield.Movement.TurnRight(300)
                                left_direction = True


                        if not Routines.Checks.Map.MapValid():
                            print("Map invalid, breaking pixel stack loop")
                            return

                        # success condition
                        if Routines.Checks.Party.IsAllPartyMembersInRange(Range.Spellcast.value):
                            print("Party Member in range, resuming")
                            return

                    retries += 1
                    print(f"Pixel stack attempt {retries} failed, retrying...")

                print("Pixel stack retries exhausted, giving up")

            finally:
                # guarantee FSM resume no matter what
                bot.config.FSM.resume()
                yield

    def _on_party_member_death_behind(self):
        from ...Routines import Routines
        from ...GlobalCache import GLOBAL_CACHE
        bot = self.parent
        
        if Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated():
                    print("Party wiped, aborting OnPartyMemberBehind")
                    return
                
        print ("Party Member dead behind")
        # Find a dead party member
        dead_player = Routines.Party.GetDeadPartyMemberID()
        if dead_player == 0:
            bot.config.FSM.resume()
            return

        # If we're in danger, end combat first (wait until safe)
        while Routines.Checks.Agents.InDanger():
            # You can replace with your combat reset routine if you have one
            #print ("In danger, waiting to be safe before moving to dead party member")
            if Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated():
                    print("Party wiped, aborting OnPartyMemberBehind")
                    return
                
            yield from Routines.Yield.wait(1000)  

        print ("Safe now, moving to dead party member")
        # Now safe → move to the dead party member
        dead_player = Routines.Party.GetDeadPartyMemberID()
        if dead_player == 0:
            print("All party members alive!")
            bot.config.FSM.resume()
            return

        exit_movement_condition = lambda: Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated()

        pos = GLOBAL_CACHE.Agent.GetXY(dead_player)
        path = [(pos[0], pos[1])]
        result = (yield from Routines.Yield.Movement.FollowPath(
            path,
            custom_exit_condition=exit_movement_condition,
            tolerance=10,
            timeout=30000,
        ))
        yield from Routines.Yield.wait(100)
        if not result:
            print("Failed to move to dead party member")
            bot.config.FSM.resume()
            return
        else:
            print("Arrived at dead party member, waiting for revival")
            
        yield from bot.helpers.Multibox._pixel_stack()

        bot.config.FSM.resume()
            

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
        
    