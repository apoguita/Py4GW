from typing import cast, override

from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.common.by_urals_hammer_utility import ByUralsHammerUtility
from Sources.oazix.CustomBehaviors.skills.common.finish_him_utility import FinishHimUtility
from Sources.oazix.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Sources.oazix.CustomBehaviors.skills.dervich.scythe_requiring_enchantment_utility import ScytheRequiringEnchantmentUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.preparation_utility import PreparationUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_simple_heal_utility import RawSimpleHealUtility
from Sources.oazix.CustomBehaviors.skills.monk.cure_hex_utility import CureHexUtility
from Sources.oazix.CustomBehaviors.skills.monk.dismiss_condition_utility import DismissConditionUtility
from Sources.oazix.CustomBehaviors.skills.monk.protective_spirit_utility import ProtectiveSpiritUtility
from Sources.oazix.CustomBehaviors.skills.monk.seed_of_life_utility import SeedOfLifeUtility
from Sources.oazix.CustomBehaviors.skills.monk.shield_of_absorption_utility import ShieldOfAbsorptionUtility
from Sources.oazix.CustomBehaviors.skills.monk.unyielding_aura_drop_utility import UnyieldingAuraDropUtility
from Sources.oazix.CustomBehaviors.skills.monk.unyielding_aura_utility import UnyieldingAuraUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.signet_of_lost_souls_utility import SignetOfLostSoulsUtility
from Sources.oazix.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.arcane_mimicry_utility import ArcaneMimicryUtility


class MonkHealingBurst_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # core skills

        self.patient_spirit_utility: CustomSkillUtilityBase = RawSimpleHealUtility(event_bus=self.event_bus, skill=CustomSkill("Patient_Spirit"), current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(8))
        self.healing_burst_utility: CustomSkillUtilityBase = RawSimpleHealUtility(event_bus=self.event_bus, skill=CustomSkill("Healing_Burst"), current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(7))

        self.seed_of_life_utility: CustomSkillUtilityBase = SeedOfLifeUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(1))
       
        self.protective_spirit_utility: CustomSkillUtilityBase = ProtectiveSpiritUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(8))
        self.shield_of_absorption_utility: CustomSkillUtilityBase = ShieldOfAbsorptionUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(8))

        self.cure_hex_utility: CustomSkillUtilityBase = CureHexUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(50))
        self.dismiss_condition_utility: CustomSkillUtilityBase = DismissConditionUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(50))

        self.selfless_spirit_luxon_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Selfless_Spirit_luxon"), score_definition=ScoreStaticDefinition(88))
        self.selfless_spirit_kurzick_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Selfless_Spirit_kurzick"), score_definition=ScoreStaticDefinition(88))
        self.serpents_quickness_prep_utility: CustomSkillUtilityBase = PreparationUtility(event_bus=self.event_bus, 
                                                             prep_skill=CustomSkill("Serpents_Quickness"), 
                                                             target_utilities=[self.seed_of_life_utility, self.selfless_spirit_luxon_utility, self.selfless_spirit_kurzick_utility], current_build=in_game_build, score_definition=ScoreStaticDefinition(94))
        self.dwarven_stability_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Dwarven_Stability"), score_definition=ScoreStaticDefinition(95))

        # common
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(99))
        self.fall_back_utility: CustomSkillUtilityBase = FallBackUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.signet_of_lost_souls_utility: CustomSkillUtilityBase = SignetOfLostSoulsUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.by_urals_hammer_utility: CustomSkillUtilityBase = ByUralsHammerUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.finish_him_utility: CustomSkillUtilityBase = FinishHimUtility(event_bus=self.event_bus, current_build=in_game_build)

        # we have an additionnal utility to drop the buff that we could have aquired from mimicry
        self.unyielding_aura_drop_utility: CustomSkillUtilityBase = UnyieldingAuraDropUtility(event_bus=self.event_bus, current_build=in_game_build)

        self.arcane_mimicry_utility: CustomSkillUtilityBase = ArcaneMimicryUtility(event_bus=self.event_bus,
                                                                                   current_build=in_game_build,
                                                                                   pre_check_condition= lambda: not cast(UnyieldingAuraDropUtility, self.unyielding_aura_drop_utility).has_buff(),
                                                                                   skill_to_copy_instance= lambda: UnyieldingAuraUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(93)))
        

    @property
    @override
    def additional_autonomous_skills(self) -> list[CustomSkillUtilityBase]:
        base = super().additional_autonomous_skills
        # not part of the skillbar, if unyielding aura is aquired from mimicry
        base.append(self.unyielding_aura_drop_utility)
        return base

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.i_am_unstopabble,
            self.fall_back_utility,
            self.signet_of_lost_souls_utility,
            self.by_urals_hammer_utility,
            self.finish_him_utility,

            self.patient_spirit_utility,
            self.healing_burst_utility,
            self.seed_of_life_utility,
            self.protective_spirit_utility,
            self.shield_of_absorption_utility,
            self.cure_hex_utility,
            self.dismiss_condition_utility,
            self.serpents_quickness_prep_utility,
            self.selfless_spirit_luxon_utility,
            self.selfless_spirit_kurzick_utility,
            self.arcane_mimicry_utility,
            self.dwarven_stability_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.healing_burst_utility.custom_skill,
        ]
