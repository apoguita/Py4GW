from typing import override

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib import Agent
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.skills.common.breath_of_the_great_dwarf_utility import BreathOfTheGreatDwarfUtility
from Widgets.CustomBehaviors.skills.common.by_urals_hammer_utility import ByUralsHammerUtility
from Widgets.CustomBehaviors.skills.common.ebon_battle_standard_of_wisdom_utility import EbonBattleStandardOfWisdom
from Widgets.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Widgets.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Widgets.CustomBehaviors.skills.generic.generic_resurrection_utility import GenericResurrectionUtility
from Widgets.CustomBehaviors.skills.generic.hero_ai_utility import HeroAiUtility
from Widgets.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Widgets.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Widgets.CustomBehaviors.skills.mesmer.cry_of_frustration_utility import CryOfFrustrationUtility
from Widgets.CustomBehaviors.skills.mesmer.cry_of_pain_utility import CryOfPainUtility
from Widgets.CustomBehaviors.skills.mesmer.drain_enchantment_utility import DrainEnchantmentUtility
from Widgets.CustomBehaviors.skills.mesmer.keystone_signet_utility import KeystoneSignetUtility
from Widgets.CustomBehaviors.skills.mesmer.mistrust_utility import MistrustUtility
from Widgets.CustomBehaviors.skills.mesmer.power_drain_utility import PowerDrainUtility
from Widgets.CustomBehaviors.skills.mesmer.shatter_enchantment_utility import ShatterEnchantmentUtility
from Widgets.CustomBehaviors.skills.mesmer.shatter_hex_utility import ShatterHexUtility
from Widgets.CustomBehaviors.skills.mesmer.signet_under_keystone_utility import SignetUnderKeystoneUtility
from Widgets.CustomBehaviors.skills.mesmer.unnatural_signet_utility import UnnaturalSignetUtility
from Widgets.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility
from Widgets.CustomBehaviors.skills.mesmer.spiritual_pain_utility import SpiritualPainUtility

class MesmerKeystone_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # core
        self.symbolic_celerity_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Symbolic_Celerity"), current_build=in_game_build, score_definition=ScoreStaticDefinition(85), renew_before_expiration_in_milliseconds=1500, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.symabolic_posture_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Symbolic_Posture"), current_build=in_game_build, score_definition=ScoreStaticDefinition(84), renew_before_expiration_in_milliseconds=1500, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.keystone_signet_utility: CustomSkillUtilityBase = KeystoneSignetUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(83))

        # signets

        self.unnatural_signet_utility: CustomSkillUtilityBase = SignetUnderKeystoneUtility(
            event_bus=self.event_bus, skill=CustomSkill("Unnatural_Signet"), current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 75 if enemy_qte >= 2 else 40 if enemy_qte <= 2 else 0),
            condition = lambda agent_id: Agent.IsHexed(agent_id))
        
        self.signet_of_clumsiness_utility: CustomSkillUtilityBase = SignetUnderKeystoneUtility(
            event_bus=self.event_bus, skill=CustomSkill("Signet_of_Clumsiness"), current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 76 if enemy_qte >= 2 else 41 if enemy_qte <= 2 else 0),
            condition = lambda agent_id: Agent.IsAttacking(agent_id))
        
        self.signet_of_disruption_utility: CustomSkillUtilityBase = SignetUnderKeystoneUtility(
            event_bus=self.event_bus, skill=CustomSkill("Signet_of_Disruption"), current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 77 if enemy_qte >= 2 else 42 if enemy_qte <= 2 else 0),
            condition = lambda agent_id: 
            (
                (Agent.IsCasting(agent_id) and GLOBAL_CACHE.Skill.Flags.IsSpell(Agent.GetCastingSkill(agent_id) and GLOBAL_CACHE.Skill.Data.GetActivation(Agent.GetCastingSkill(agent_id)) >= 0.200))
                or
                (Agent.IsCasting(agent_id) and Agent.IsHexed(agent_id) and GLOBAL_CACHE.Skill.Data.GetActivation(Agent.GetCastingSkill(agent_id)) >= 0.200))
            )

        # aoe
        self.wastrels_demise_utility: CustomSkillUtilityBase = RawAoeAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Wastrels_Demise"), current_build=in_game_build, mana_required_to_cast=10)
        self.spiritual_pain_utility: CustomSkillUtilityBase = SpiritualPainUtility(event_bus=self.event_bus, current_build=in_game_build, mana_required_to_cast=10)

        # utilities
        self.fall_back_utility: CustomSkillUtilityBase = FallBackUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.drain_enchantment_utility: CustomSkillUtilityBase = DrainEnchantmentUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(89))

        #common
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(event_bus=self.event_bus, score_definition=ScoreStaticDefinition(71), current_build=in_game_build, mana_required_to_cast=15)
        self.ebon_battle_standard_of_wisdom: CustomSkillUtilityBase = EbonBattleStandardOfWisdom(event_bus=self.event_bus, score_definition= ScorePerAgentQuantityDefinition(lambda agent_qte: 80 if agent_qte >= 3 else 60 if agent_qte <= 2 else 40), current_build=in_game_build, mana_required_to_cast=18)
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(99))
        self.breath_of_the_great_dwarf_utility: CustomSkillUtilityBase = BreathOfTheGreatDwarfUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(9))
        self.flesh_of_my_flesh_utility: CustomSkillUtilityBase = GenericResurrectionUtility(event_bus=self.event_bus, skill=CustomSkill("Flesh_of_My_Flesh"), current_build=in_game_build,score_definition=ScoreStaticDefinition(12))
        self.signet_of_return_utility: CustomSkillUtilityBase = GenericResurrectionUtility(event_bus=self.event_bus, skill=CustomSkill("Signet_of_Return"), current_build=in_game_build,score_definition=ScoreStaticDefinition(12))
        self.by_urals_hammer_utility: CustomSkillUtilityBase = ByUralsHammerUtility(event_bus=self.event_bus, current_build=in_game_build)

    @property
    @override
    def skills_allowed_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.wastrels_demise_utility,
            self.spiritual_pain_utility,
            self.symbolic_celerity_utility,
            self.symabolic_posture_utility,
            self.keystone_signet_utility,
            self.signet_of_clumsiness_utility,
            self.unnatural_signet_utility,
            self.signet_of_disruption_utility,

            self.ebon_vanguard_assassin_support,
            self.ebon_battle_standard_of_wisdom,
            self.i_am_unstopabble,
            self.breath_of_the_great_dwarf_utility,
            self.by_urals_hammer_utility,
            self.flesh_of_my_flesh_utility,
            self.signet_of_return_utility,
            self.fall_back_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.keystone_signet_utility.custom_skill,
        ]