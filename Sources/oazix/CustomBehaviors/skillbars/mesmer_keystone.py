from typing import override

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib import Agent
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.common.breath_of_the_great_dwarf_utility import BreathOfTheGreatDwarfUtility
from Sources.oazix.CustomBehaviors.skills.common.by_urals_hammer_utility import ByUralsHammerUtility
from Sources.oazix.CustomBehaviors.skills.common.ebon_battle_standard_of_wisdom_utility import EbonBattleStandardOfWisdom
from Sources.oazix.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Sources.oazix.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Sources.oazix.CustomBehaviors.skills.generic.generic_resurrection_utility import GenericResurrectionUtility
from Sources.oazix.CustomBehaviors.skills.generic.auto_combat_utility import AutoCombatUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.preparation_utility import PreparationUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Sources.oazix.CustomBehaviors.skills.mesmer import keystone_signet_utility
from Sources.oazix.CustomBehaviors.skills.mesmer.cry_of_frustration_utility import CryOfFrustrationUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.cry_of_pain_utility import CryOfPainUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.drain_enchantment_utility import DrainEnchantmentUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.keystone_signet_utility import KeystoneSignetUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.mistrust_utility import MistrustUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.power_drain_utility import PowerDrainUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.shatter_enchantment_utility import ShatterEnchantmentUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.shatter_hex_utility import ShatterHexUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.signet_under_keystone_utility import SignetUnderKeystoneUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.unnatural_signet_utility import UnnaturalSignetUtility
from Sources.oazix.CustomBehaviors.skills.monk.castigation_signet_utility import CastigationSignetUtility
from Sources.oazix.CustomBehaviors.skills.monk.holy_veil_utility import HolyVeilUtility
from Sources.oazix.CustomBehaviors.skills.monk.mending_utility import MendingUtility
from Sources.oazix.CustomBehaviors.skills.monk.smite_hex_utility import SmiteHexUtility
from Sources.oazix.CustomBehaviors.skills.monk.strength_of_honor_utility import StrengthOfHonorUtility
from Sources.oazix.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.spiritual_pain_utility import SpiritualPainUtility

class MesmerKeystone_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # core
        self.keystone_signet_utility: CustomSkillUtilityBase = KeystoneSignetUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(83))

        self.symbolic_celerity_utility: CustomSkillUtilityBase = PreparationUtility(event_bus=self.event_bus, 
                                                                                    prep_skill=CustomSkill("Symbolic_Celerity"), 
                                                                                    target_utilities=[self.keystone_signet_utility],
                                                                                    current_build=in_game_build, score_definition=ScoreStaticDefinition(85), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        
        self.symabolic_posture_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Symbolic_Posture"), current_build=in_game_build, score_definition=ScoreStaticDefinition(84), renew_before_expiration_in_milliseconds=1500, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])

        # signets

        self.leech_signet_utility: CustomSkillUtilityBase = SignetUnderKeystoneUtility(
            event_bus=self.event_bus, skill=CustomSkill("Leech_Signet"), current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 75 if enemy_qte >= 2 else 40 if enemy_qte <= 2 else 0),
            condition = lambda agent_id:(Agent.IsCasting(agent_id) and GLOBAL_CACHE.Skill.Flags.IsSpell(Agent.GetCastingSkillID(agent_id) and GLOBAL_CACHE.Skill.Data.GetActivation(Agent.GetCastingSkillID(agent_id)) >= 0.200)))
        
        self.unnatural_signet_utility: CustomSkillUtilityBase = SignetUnderKeystoneUtility(
            event_bus=self.event_bus, skill=CustomSkill("Unnatural_Signet"), current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 75 if enemy_qte >= 2 else 40 if enemy_qte <= 2 else 0),
            condition = lambda agent_id: Agent.IsHexed(agent_id) or Agent.IsEnchanted(agent_id))
        
        self.signet_of_clumsiness_utility: CustomSkillUtilityBase = SignetUnderKeystoneUtility(
            event_bus=self.event_bus, skill=CustomSkill("Signet_of_Clumsiness"), current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 76 if enemy_qte >= 2 else 41 if enemy_qte <= 2 else 0),
            condition = lambda agent_id: Agent.IsAttacking(agent_id))
        
        self.signet_of_disruption_utility: CustomSkillUtilityBase = SignetUnderKeystoneUtility(
            event_bus=self.event_bus, skill=CustomSkill("Signet_of_Disruption"), current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 77 if enemy_qte >= 2 else 42 if enemy_qte <= 2 else 0),
            condition = lambda agent_id: 
            (
                (Agent.IsCasting(agent_id) and GLOBAL_CACHE.Skill.Flags.IsSpell(Agent.GetCastingSkillID(agent_id) and GLOBAL_CACHE.Skill.Data.GetActivation(Agent.GetCastingSkillID(agent_id)) >= 0.200))
                or
                (Agent.IsCasting(agent_id) and Agent.IsHexed(agent_id) and GLOBAL_CACHE.Skill.Data.GetActivation(Agent.GetCastingSkillID(agent_id)) >= 0.200))
            )
        self.signet_of_weariness_utility: CustomSkillUtilityBase = SignetUnderKeystoneUtility(
            event_bus=self.event_bus, skill=CustomSkill("Signet_of_Weariness"), current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 76 if enemy_qte >= 2 else 41 if enemy_qte <= 2 else 0),
            condition=lambda agent_id: True)

        self.bane_signet_utility: CustomSkillUtilityBase = SignetUnderKeystoneUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Bane_Signet"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 76 if enemy_qte >= 2 else 41 if enemy_qte <= 2 else 0),
            condition=lambda agent_id: Agent.IsAttacking(agent_id),
        )
        self.blessed_signet_utility: CustomSkillUtilityBase = AutoCombatUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Blessed_Signet"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(73),
        )
        self.castigation_signet_utility: CustomSkillUtilityBase = CastigationSignetUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(72),
        )

        # Upkeepers
        self.mending_utility: CustomSkillUtilityBase = MendingUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(70),
        )
        self.strength_of_honor_utility: CustomSkillUtilityBase = StrengthOfHonorUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(69),
        )
        self.holy_veil_utility: CustomSkillUtilityBase = HolyVeilUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(68),
        )

        # Support
        self.smite_hex_utility: CustomSkillUtilityBase = SmiteHexUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
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

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.wastrels_demise_utility,
            self.spiritual_pain_utility,
            self.symbolic_celerity_utility,
            self.symabolic_posture_utility,
            self.leech_signet_utility,
            self.keystone_signet_utility,
            self.signet_of_clumsiness_utility,
            self.unnatural_signet_utility,
            self.signet_of_disruption_utility,
            self.signet_of_weariness_utility,
            self.bane_signet_utility,
            self.blessed_signet_utility,
            self.castigation_signet_utility,
            self.mending_utility,
            self.strength_of_honor_utility,
            self.holy_veil_utility,
            self.smite_hex_utility,

            self.ebon_vanguard_assassin_support,
            self.ebon_battle_standard_of_wisdom,
            self.fall_back_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.keystone_signet_utility.custom_skill,
        ]
