#region STATES
from typing import TYPE_CHECKING, Callable, Optional, Tuple
from Py4GWCoreLib import Color
import PyImGui

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass

from ...enums import ModelID

#region Multibox
class _MULTIBOX:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers
        
    def ResignParty(self):
        self._helpers.Multibox.resign_party()
        
    def PixelStack(self):
        self._helpers.Multibox.pixel_stack()
        
    def InteractWithTarget(self):
        self._helpers.Multibox.interact_with_target()
        
    def UseEssenceOfCelerity(self):
        from ...GlobalCache import GLOBAL_CACHE
        self._helpers.Multibox.use_consumable((ModelID.Essence_Of_Celerity.value, GLOBAL_CACHE.Skill.GetID("Essence_of_Celerity_item_effect"), 0, 0))
        
    def UseGrailOfMight(self):
        from ...GlobalCache import GLOBAL_CACHE
        self._helpers.Multibox.use_consumable((ModelID.Grail_Of_Might.value, GLOBAL_CACHE.Skill.GetID("Grail_of_Might_item_effect"), 0, 0))
        
    def UseArmorOfSalvation(self):
        from ...GlobalCache import GLOBAL_CACHE
        self._helpers.Multibox.use_consumable((ModelID.Armor_Of_Salvation.value, GLOBAL_CACHE.Skill.GetID("Armor_of_Salvation_item_effect"), 0, 0))
        
    def UsePConSet(self):
        self.UseEssenceOfCelerity()
        self.UseGrailOfMight()
        self.UseArmorOfSalvation()

    def UseConsumable(self, item_id, skill_id):
        self._helpers.Multibox.use_consumable((item_id, skill_id, 0, 0))



#endregion
