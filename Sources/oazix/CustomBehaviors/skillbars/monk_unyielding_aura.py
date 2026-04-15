from typing import override

from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_simple_heal_utility import RawSimpleHealUtility
from Sources.oazix.CustomBehaviors.skills.monk.cure_hex_utility import CureHexUtility
from Sources.oazix.CustomBehaviors.skills.monk.dismiss_condition_utility import DismissConditionUtility
from Sources.oazix.CustomBehaviors.skills.monk.protective_spirit_utility import ProtectiveSpiritUtility
from Sources.oazix.CustomBehaviors.skills.monk.seed_of_life_utility import SeedOfLifeUtility
from Sources.oazix.CustomBehaviors.skills.monk.shield_of_absorption_utility import ShieldOfAbsorptionUtility
from Sources.oazix.CustomBehaviors.skills.monk.unyielding_aura_utility import UnyieldingAuraUtility
from Sources.oazix.CustomBehaviors.skills.plugins.preconditions.should_wait_for_effect import ShouldWaitForEffect
from Sources.oazix.CustomBehaviors.skills.plugins.preconditions.should_wait_for_serpents_quickness import ShouldWaitForSerpentsQuickness


class MonkUnyieldingAura_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus)
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # core skills - Unyielding Aura
        self.unyielding_aura_utility: CustomSkillUtilityBase = UnyieldingAuraUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(95))

        self.patient_spirit_utility: CustomSkillUtilityBase = RawSimpleHealUtility(event_bus=self.event_bus, skill=CustomSkill("Patient_Spirit"), current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(8))
        self.healing_burst_utility: CustomSkillUtilityBase = RawSimpleHealUtility(event_bus=self.event_bus, skill=CustomSkill("Healing_Burst"), current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(7))
        self.protective_spirit_utility: CustomSkillUtilityBase = ProtectiveSpiritUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(8))
        self.shield_of_absorption_utility: CustomSkillUtilityBase = ShieldOfAbsorptionUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(8))
        self.cure_hex_utility: CustomSkillUtilityBase = CureHexUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(50))
        self.dismiss_condition_utility: CustomSkillUtilityBase = DismissConditionUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(50))

        # combo Serpents_Quickness + Selfless_Spirit + Dwarven_Stability

        self.selfless_spirit_kurzick_utility = (KeepSelfEffectUpUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Selfless_Spirit_kurzick"), score_definition=ScoreStaticDefinition(88))
                                                                        .add_plugin_precondition(lambda x: ShouldWaitForSerpentsQuickness(x.custom_skill, True)))

        self.selfless_spirit_luxon_utility = (KeepSelfEffectUpUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Selfless_Spirit_luxon"), score_definition=ScoreStaticDefinition(88))
                                                                      .add_plugin_precondition(lambda x: ShouldWaitForSerpentsQuickness(x.custom_skill, True)))

        self.serpents_quickness_utility = (KeepSelfEffectUpUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Serpents_Quickness"), score_definition=ScoreStaticDefinition(94))
                                                                    .add_plugin_precondition(lambda x: ShouldWaitForEffect(x.custom_skill, CustomSkill("Dwarven_Stability"), True)))

        self.seed_of_life_utility = (SeedOfLifeUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(1)) 
                                                        .add_plugin_precondition(lambda x: ShouldWaitForSerpentsQuickness(x.custom_skill, True)))

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.unyielding_aura_utility,
            self.patient_spirit_utility,
            self.healing_burst_utility,
            self.seed_of_life_utility,
            self.protective_spirit_utility,
            self.shield_of_absorption_utility,
            self.cure_hex_utility,
            self.dismiss_condition_utility,
            self.serpents_quickness_utility,
            self.selfless_spirit_luxon_utility,
            self.selfless_spirit_kurzick_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.unyielding_aura_utility.custom_skill,
            self.seed_of_life_utility.custom_skill,
        ]
