#region CONFIG_TEMPLATES
from typing import TYPE_CHECKING


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

    def PacifistForceAutocombat(self):
        properties = self.parent.Properties
        properties.Disable("pause_on_danger") #avoid combat
        properties.Enable("halt_on_death") 
        properties.Set("movement_timeout",value=15000)
        properties.Disable("hero_ai") #no hero combat
        self.parent.Multibox.SetAccountIsolation(False) #single-account passive mode
        properties.Disable("auto_loot") #no waiting for loot
        properties.Disable("imp")
        
    def Pacifist(self):
        properties = self.parent.Properties
        properties.Disable("pause_on_danger") #avoid combat
        properties.Enable("halt_on_death") 
        properties.Set("movement_timeout",value=15000)
        properties.Disable("hero_ai") #no hero combat
        self.parent.Multibox.SetAccountIsolation(True) #single-account passive mode
        properties.Disable("auto_loot") #no waiting for loot
        properties.Disable("imp")
        


    def AggressiveForceHeroAI(self, pause_on_danger: bool = True,
                   halt_on_death: bool = False,
                   movement_timeout: int = -1,
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
        properties.Enable("hero_ai") #combat is always driven by HeroAI
         
        if auto_loot:   
            properties.Enable("auto_loot") #wait for loot
        else:
            properties.Disable("auto_loot") #no waiting for loot
            
        if enable_imp:
            properties.Enable("imp")
        else:
            properties.Disable("imp")
        
    def Aggressive(self, pause_on_danger: bool = True,
                   halt_on_death: bool = False,
                   movement_timeout: int = -1,
                   account_isolation: bool = True,
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
        properties.Enable("hero_ai") #combat is always driven by HeroAI
        if account_isolation:
            self.parent.Multibox.SetAccountIsolation(True) #single-account HeroAI
        else:
            self.parent.Multibox.SetAccountIsolation(False) #multi-account HeroAI
         
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
        properties.Enable("hero_ai") #hero combat
        self.parent.Multibox.SetAccountIsolation(False) #multibox mode must stay shared
        properties.Enable("auto_loot") #wait for loot
        properties.Enable("auto_inventory_management") #manage inventory
        

#region Routines
    class _Routines:
        def __init__(self, parent: "BottingClass"):
            self.parent = parent
            self._config = parent.config
            self._helpers = parent.helpers

        def OnPartyMemberBehind(self):
            bot = self.parent
            print ("Party Member behind, Triggered")
            fsm = bot.config.FSM
            fsm.pause()
            fsm.AddManagedCoroutine("OnBehind_OPD", self.parent.Events._on_party_member_behind())

        def OnPartyMemberInDanger(self):
            bot = self.parent
            fsm = bot.config.FSM
            fsm.pause()
            fsm.AddManagedCoroutine("OnPartyMemberInDanger_OPD", self.parent.Events._on_party_member_in_danger())
            

        def OnPartyMemberDeathBehind(self):
            from ...Py4GWcorelib import ConsoleLog
            bot = self.parent
            ConsoleLog("on_party_member_dead_behind","event triggered")
            fsm = bot.config.FSM
            fsm.pause()
            fsm.AddManagedCoroutine("OnDeathBehind_OPD", lambda: self.parent.Events._on_party_member_death_behind())
                    
            
        def PrepareForFarm(self, map_id_to_travel: int, party_reset_mode: str = "kick"):
            bot = self.parent
            bot.States.AddHeader("Prepare For Farm")
            bot.Events.OnPartyMemberBehindCallback(lambda: self.OnPartyMemberBehind())
            bot.Events.OnPartyMemberInDangerCallback(lambda: self.OnPartyMemberInDanger())
            bot.Events.OnPartyMemberDeadBehindCallback(lambda: self.OnPartyMemberDeathBehind())
            if str(party_reset_mode).lower() == "leave":
                bot.Multibox.LeavePartyOnAllAccounts()
            else:
                bot.Multibox.KickAllAccounts()
            #bot.Map.Travel(target_map_id=map_id_to_travel)
            bot.Travel_To_Random_District(target_map_id=map_id_to_travel)
            bot.Multibox.SummonAllAccounts()
            bot.Wait.ForTime(4000)
            bot.Multibox.InviteAllAccounts()
