from typing import override

from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Sources.oazix.CustomBehaviors.skills.monk.castigation_signet_utility import CastigationSignetUtility
from Sources.oazix.CustomBehaviors.skills.monk.smite_hex_utility import SmiteHexUtility
from Sources.oazix.CustomBehaviors.skills.monk.smite_condition_utility import SmiteConditionUtility
from Sources.oazix.CustomBehaviors.skills.monk.strength_of_honor_utility import StrengthOfHonorUtility


class MonkSmite_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus)
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # core skills
        self.smite_hex_utility: CustomSkillUtilityBase = SmiteHexUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(60))
        self.smite_condition_utility: CustomSkillUtilityBase = SmiteConditionUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(60))
        self.castigation_signet_utility: CustomSkillUtilityBase = CastigationSignetUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(55))
        self.ray_of_judgment_utility: CustomSkillUtilityBase = RawAoeAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Ray_of_Judgment"), current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 70 if enemy_qte >= 3 else 55 if enemy_qte >= 2 else 40), mana_required_to_cast=10)
        self.strength_of_honor_utility: CustomSkillUtilityBase = StrengthOfHonorUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(50))
        
    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.ray_of_judgment_utility,
            self.castigation_signet_utility,
            self.smite_hex_utility,
            self.smite_condition_utility,
            self.strength_of_honor_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.ray_of_judgment_utility.custom_skill,
        ]

