from Sources.oazix.CustomBehaviors.primitives.skillbars.disabilities.disability_priority import DisabilityPriority
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill

class HexPriority():
    def __init__(self, hex: CustomSkill, priority: DisabilityPriority):
        self.hex = hex
        self.hex_skill_id = hex.skill_id
        self.priority = priority