from typing import override

from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Sources.oazix.CustomBehaviors.skills.monk.castigation_signet_utility import CastigationSignetUtility
from Sources.oazix.CustomBehaviors.skills.monk.seed_of_life_utility import SeedOfLifeUtility
from Sources.oazix.CustomBehaviors.skills.monk.smite_hex_utility import SmiteHexUtility
from Sources.oazix.CustomBehaviors.skills.monk.smite_condition_utility import SmiteConditionUtility
from Sources.oazix.CustomBehaviors.skills.monk.strength_of_honor_utility import StrengthOfHonorUtility
from Sources.oazix.CustomBehaviors.skills.plugins.preconditions.should_wait_for_effect import ShouldWaitForEffect
from Sources.oazix.CustomBehaviors.skills.plugins.preconditions.should_wait_for_serpents_quickness import ShouldWaitForSerpentsQuickness


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

        # combo Serpents_Quickness + Selfless_Spirit + Dwarven_Stability
        self.selfless_spirit_kurzick_utility: CustomSkillUtilityBase = (KeepSelfEffectUpUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Selfless_Spirit_kurzick"), score_definition=ScoreStaticDefinition(88))
                                                                        .add_plugin_precondition(lambda x: ShouldWaitForSerpentsQuickness(x.custom_skill, True)))
        self.selfless_spirit_luxon_utility: CustomSkillUtilityBase = (KeepSelfEffectUpUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Selfless_Spirit_luxon"), score_definition=ScoreStaticDefinition(88))
                                                                      .add_plugin_precondition(lambda x: ShouldWaitForSerpentsQuickness(x.custom_skill, True)))

        self.serpents_quickness_utility = (KeepSelfEffectUpUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Serpents_Quickness"), score_definition=ScoreStaticDefinition(94))
                                                                    .add_plugin_precondition(lambda x: ShouldWaitForEffect(x.custom_skill, CustomSkill("Dwarven_Stability"), True)))
        
        self.seed_of_life_utility: CustomSkillUtilityBase = (SeedOfLifeUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(1)) 
                                                                .add_plugin_precondition(lambda x: ShouldWaitForSerpentsQuickness(x.custom_skill, True)))
       

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.ray_of_judgment_utility,
            self.castigation_signet_utility,
            self.smite_hex_utility,
            self.smite_condition_utility,
            self.strength_of_honor_utility,
            self.seed_of_life_utility,
            self.selfless_spirit_kurzick_utility,
            self.selfless_spirit_luxon_utility,
            self.serpents_quickness_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.ray_of_judgment_utility.custom_skill,
        ]

