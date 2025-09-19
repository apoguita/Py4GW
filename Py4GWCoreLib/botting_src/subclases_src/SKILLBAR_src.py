#region STATES
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass
    
#region SKILLBAR
class _SKILLBAR:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers

    def LoadSkillBar(self, skill_template: str):
        self._helpers.Skills.load_skillbar(skill_template)

    def LoadHeroSkillBar(self, hero_index: int, skill_template: str):
        self._helpers.Skills.load_hero_skillbar(hero_index, skill_template)

    def UseSkill(self, skill_id:int):
        self._helpers.Skills.cast_skill_id(skill_id)

    def UseSkillSlot(self, slot_index:int):
        self._helpers.Skills.cast_skill_slot(slot_index)

    