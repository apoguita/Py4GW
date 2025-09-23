#region CONFIG_TEMPLATES
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass
    
#region TARGET
class _TEMPLATES:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers
        
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
        
    def Aggressive(self):
        properties = self.parent.Properties
        properties.Enable("pause_on_danger") #engage in combat
        properties.Disable("halt_on_death") 
        properties.Set("movement_timeout",value=-1)
        properties.Enable("auto_combat") #engage in combat
        properties.Disable("hero_ai") #hero combat     
        properties.Enable("auto_loot") #wait for loot
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
    def PrepareForFarm(self, map_id_to_travel:int):
        bot = self.parent
        bot.States.AddHeader("Prepare For Farm")
        bot.Multibox.KickAllAccounts()
        bot.Map.Travel(target_map_id=map_id_to_travel)
        bot.Multibox.SummonAllAccounts()
        bot.Wait.ForTime(4000)
        bot.Multibox.InviteAllAccounts()
