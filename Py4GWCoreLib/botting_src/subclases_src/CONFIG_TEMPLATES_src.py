#region CONFIG_TEMPLATES
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass
    
#region TARGET
class _CONFIG_TEMPLATES:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers

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