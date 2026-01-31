# python
# File: `Widgets/CustomBehaviors/skillbars/elementalist_glimmeringmark.py`
from typing import List, override

from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import \
    ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.skills.assassin import deadly_paradox_utility
from Widgets.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Widgets.CustomBehaviors.skills.elementalist.arc_lightning_utility import ArcLightningUtility
from Widgets.CustomBehaviors.skills.elementalist.glimmering_mark_utility import GlimmeringMarkUtility
from Widgets.CustomBehaviors.skills.elementalist.chain_lightning_utility import ChainLightningUtility
from Widgets.CustomBehaviors.skills.elementalist.shock_arrow_utility import ShockArrowUtility
from Widgets.CustomBehaviors.skills.generic.preparation_targeted_utility import PreparationTargetedUtility
from Widgets.CustomBehaviors.skills.generic.preparation_utility import PreparationUtility
from Widgets.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Widgets.CustomBehaviors.skills.generic.raw_simple_attack_utility import RawSimpleAttackUtility
from Widgets.CustomBehaviors.skills.generic.simple_sequence_utility import SimpleSequenceUtility
from Widgets.CustomBehaviors.skills.generic.stub_utility import StubUtility
from Widgets.CustomBehaviors.skills.mesmer.arcane_echo_utility import ArcaneEchoUtility
from Widgets.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility
from Widgets.CustomBehaviors.skills.elementalist.shellshock_utility import ShellShockUtility
from Widgets.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility


class ElementalistInvokeLightning_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        self.stub_invoke_lightning_utility: CustomSkillUtilityBase = StubUtility(event_bus=self.event_bus, skill=CustomSkill("Invoke_Lightning"), current_build=in_game_build)
        self.stub_intensity_utility: CustomSkillUtilityBase = StubUtility(event_bus=self.event_bus, skill=CustomSkill("Intensity"), current_build=in_game_build)

        intensity_utility : CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus,skill=CustomSkill("Intensity"),current_build=in_game_build,score_definition=ScoreStaticDefinition(99),mana_required_to_cast=10,allowed_states=[BehaviorState.IN_AGGRO])
        invoke_lightning_utility : CustomSkillUtilityBase= RawAoeAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Invoke_Lightning"), current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 99), mana_required_to_cast=0, allowed_states=[BehaviorState.IN_AGGRO])
        self.sequence_utility : CustomSkillUtilityBase = SimpleSequenceUtility(event_bus=self.event_bus, utility_1=intensity_utility, utility_2=invoke_lightning_utility, current_build=in_game_build, score_definition=ScoreStaticDefinition(68))

        self.shock_arrow_utility: CustomSkillUtilityBase = ShockArrowUtility(event_bus=self.event_bus,current_build=in_game_build,score_definition=ScoreStaticDefinition(60))
        self.shell_shock_utility: CustomSkillUtilityBase = ShellShockUtility(event_bus=self.event_bus,current_build=in_game_build,score_definition=ScoreStaticDefinition(54))
        
        self.arc_lightning_utility: CustomSkillUtilityBase = ArcLightningUtility(event_bus=self.event_bus,current_build=in_game_build,score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 66 if enemy_qte >= 3 else 51 if enemy_qte <= 1 else 1),mana_required_to_cast=5,allowed_states=[BehaviorState.IN_AGGRO])

        self.elemental_lord_kurzick_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus,skill=CustomSkill("Elemental_Lord_kurzick"),current_build=in_game_build,score_definition=ScoreStaticDefinition(70),mana_required_to_cast=10,allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.elemental_lord_luxon_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus,skill=CustomSkill("Elemental_Lord_luxon"),current_build=in_game_build,score_definition=ScoreStaticDefinition(70),mana_required_to_cast=10,allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.air_attunement_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus,skill=CustomSkill("Air_Attunement"),current_build=in_game_build,score_definition=ScoreStaticDefinition(70),mana_required_to_cast=10,renew_before_expiration_in_milliseconds=1000,allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(event_bus=self.event_bus, score_definition=ScoreStaticDefinition(71), current_build=in_game_build, mana_required_to_cast=15)

    @property
    @override
    def additional_autonomous_skills(self) -> list[CustomSkillUtilityBase]:
        base = super().additional_autonomous_skills
        base.append(self.sequence_utility)
        return base

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.stub_invoke_lightning_utility,
            self.stub_intensity_utility,

            self.elemental_lord_kurzick_utility,
            self.elemental_lord_luxon_utility,
            self.air_attunement_utility,

            self.arc_lightning_utility,

            self.shell_shock_utility,
            self.shock_arrow_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.stub_invoke_lightning_utility.custom_skill, # this is a stub skill, as invoke lightning is managed by a sequence utility (intensity -> invoke lightning)
            self.stub_intensity_utility.custom_skill, # obviously required as part of sequence (additional_autonomous_skills)
        ]