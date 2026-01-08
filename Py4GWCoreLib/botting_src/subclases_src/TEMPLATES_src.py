#region CONFIG_TEMPLATES
from typing import TYPE_CHECKING, Any, Callable, Generator

from Py4GWCoreLib.py4gwcorelib_src.FSM import FSM

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

    def Aggressive(self, pause_on_danger: bool = True,
                   halt_on_death: bool = False,
                   movement_timeout: int = -1,
                   auto_combat: bool = True, 
                   auto_loot: bool = True,
                   enable_imp: bool = True):
        properties = self.parent.Properties
        if pause_on_danger:
            properties.Enable("pause_on_danger") #engage in combat
        else:
            properties.Disable("pause_on_danger") #avoid combat

        if halt_on_death:
            properties.Enable("halt_on_death")
        else:
            properties.Disable("halt_on_death")

        properties.Set("movement_timeout", value=movement_timeout)
        if auto_combat:
            properties.Enable("auto_combat") #engage in combat
            properties.Disable("hero_ai") #hero combat 
        else:
            properties.Disable("auto_combat") #avoid combat
         
        if auto_loot:   
            properties.Enable("auto_loot") #wait for loot
        else:
            properties.Disable("auto_loot") #no waiting for loot
            
        if enable_imp:
            properties.Enable("imp")
        else:
            properties.Disable("imp")
        
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

        def UseCustomBehaviors(
                self, 
                on_player_critical_stuck: Callable[[FSM], Generator[Any, Any, Any]] | None = None,
                on_player_critical_death: Callable[[FSM], Generator[Any, Any, Any]] | None = None,
                on_party_death: Callable[[FSM], Generator[Any, Any, Any]] | None = None,
                map_id_to_travel:int | None = None):
            bot = self.parent

            from Widgets.CustomBehaviors.primitives.botting.botting_fsm_helper import BottingFsmHelpers
            BottingFsmHelpers.UseCustomBehavior(bot, on_player_critical_stuck, on_player_critical_death, on_party_death)
            if map_id_to_travel is not None:
                bot.Map.Travel(target_map_id=map_id_to_travel)
        
        def OnPartyMemberBehind(self):
            bot = self.parent
            print ("Party Member behind, Triggered")
            fsm = bot.config.FSM
            fsm.pause()
            fsm.AddManagedCoroutine("OnBehind_OPD", self.parent.Events._on_party_member_behind())
            

        def OnPartyMemberDeathBehind(self):
            from ...Py4GWcorelib import ConsoleLog
            bot = self.parent
            ConsoleLog("on_party_member_dead_behind","event triggered")
            fsm = bot.config.FSM
            fsm.pause()
            fsm.AddManagedCoroutine("OnDeathBehind_OPD", lambda: self.parent.Events._on_party_member_death_behind())
                    
            
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


       