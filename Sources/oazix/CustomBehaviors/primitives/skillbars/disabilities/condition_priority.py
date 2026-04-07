
from Sources.oazix.CustomBehaviors.primitives.skillbars.disabilities.disability_priority import DisabilityPriority
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill

class ConditionPriority():
    def __init__(self, condition: CustomSkill, priority: DisabilityPriority):
        self.condition = condition
        self.condition_skill_id = condition.skill_id
        self.priority = priority