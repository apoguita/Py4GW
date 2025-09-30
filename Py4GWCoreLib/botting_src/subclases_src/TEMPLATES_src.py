#region CONFIG_TEMPLATES
from typing import TYPE_CHECKING, List

from Py4GWCoreLib.routines_src.Agents import Routines

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass
    
#region TARGET
class _TEMPLATES:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers
        self.Routines = self._Routines(parent)
        
    #region Property configuration

    def Pacifist(self):
        properties = self.parent.Properties
        properties.Disable("pause_on_danger") #avoid combat
        properties.Enable("halt_on_death") 
        properties.Set("movement_timeout",value=15000)
        properties.Disable("auto_combat") #avoid combat
        properties.Disable("hero_ai") #no hero combat     
        properties.Disable("auto_loot") #no waiting for loot
        properties.Disable("imp")
        
    def Aggressive(self, enable_imp:bool=True):
        properties = self.parent.Properties
        properties.Enable("pause_on_danger") #engage in combat
        properties.Disable("halt_on_death") 
        properties.Set("movement_timeout",value=-1)
        properties.Enable("auto_combat") #engage in combat
        properties.Disable("hero_ai") #hero combat     
        properties.Enable("auto_loot") #wait for loot
        if enable_imp:
            properties.Enable("imp")
        
    def Multibox_Aggressive(self):
        properties = self.parent.Properties
        properties.Enable("pause_on_danger") #engage in combat
        properties.Disable("halt_on_death") 
        properties.Set("movement_timeout",value=-1)
        properties.Disable("auto_combat") #engage in combat
        properties.Enable("hero_ai") #hero combat     
        properties.Enable("auto_loot") #wait for loot
        properties.Enable("auto_inventory_management") #manage inventory



#region Routines
    class _Routines:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self._config = parent.config
            self._helpers = parent.helpers
            
        def _on_party_member_behind(self):
            from ...Routines import Routines
            from ...Py4GWcorelib import Utils
            from ...enums import Range
            bot = self.parent
            print("Party Member behind, emitting pixel stack")
            yield from Routines.Yield.Movement.StopMovement()
            yield from bot.helpers.Multibox._pixel_stack()

            last_emit = Utils.GetBaseTimestamp()
            while not Routines.Checks.Party.IsAllPartyMembersInRange(Range.Earshot.value):
                yield from bot.helpers.Wait._for_time(500)

                # Reissue pixel stack every 10000 ms
                now = Utils.GetBaseTimestamp()
                if now - last_emit >= 10000:
                    print("Re-emitting pixel stack")
                    yield from bot.helpers.Multibox._pixel_stack()
                    last_emit = now

                if not Routines.Checks.Agents.InDanger():
                    yield from Routines.Yield.Movement.StopMovement()
                if not Routines.Checks.Map.MapValid():
                    bot.config.FSM.resume()
                    yield
                    break

            print("Party Member in range, resuming")
            bot.config.FSM.resume()
            yield
   
        def OnPartyMemberBehind(self):
            bot = self.parent
            print ("Party Member behind, Triggered")
            fsm = bot.config.FSM
            fsm.pause()
            fsm.AddManagedCoroutine("OnBehind_OPD", self._on_party_member_behind())
            
        def _on_party_member_death_behind(self):
            from ...Routines import Routines
            from ...GlobalCache import GLOBAL_CACHE
            bot = self.parent
            dead_player = Routines.Party.GetDeadPartyMemberID()
            if dead_player == 0:
                bot.config.FSM.resume()
                return

            pos = GLOBAL_CACHE.Agent.GetXY(dead_player)
            path = [(pos[0], pos[1])]
            bot.helpers.Move.set_path_to(path)
            yield from bot.helpers.Move._follow_path()
            bot.config.FSM.resume()

        def OnPartyMemberDeathBehind(self):
            from ...Py4GWcorelib import ConsoleLog
            bot = self.parent
            ConsoleLog("on_party_member_dead_behind","event triggered")
            fsm = bot.config.FSM
            fsm.pause()
            fsm.AddManagedCoroutine("OnDeathBehind_OPD", lambda: self._on_party_member_death_behind())
                    
            
        def PrepareForFarm(self, map_id_to_travel:int):
            bot = self.parent
            bot.States.AddHeader("Prepare For Farm")
            bot.Events.OnPartyMemberBehindCallback(lambda: self.OnPartyMemberBehind())
            bot.Events.OnPartyMemberDeadBehindCallback(lambda: self.OnPartyMemberDeathBehind())
            bot.Multibox.KickAllAccounts()
            bot.Map.Travel(target_map_id=map_id_to_travel)
            bot.Multibox.SummonAllAccounts()
            bot.Wait.ForTime(4000)
            bot.Multibox.InviteAllAccounts()


       