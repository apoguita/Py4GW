from typing import override

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
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
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.arcane_conundrum_utility import ArcaneConundrumUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.cry_of_frustration_utility import CryOfFrustrationUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.cry_of_pain_utility import CryOfPainUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.drain_enchantment_utility import DrainEnchantmentUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.ineptitude_utility import IneptitudeUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.keystone_signet_utility import KeystoneSignetUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.mistrust_utility import MistrustUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.power_drain_utility import PowerDrainUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.shatter_enchantment_utility import ShatterEnchantmentUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.shatter_hex_utility import ShatterHexUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.signet_of_clumsiness_utility import SignetOfClumsinessUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.signet_under_keystone_utility import SignetUnderKeystoneUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.unnatural_signet_utility import UnnaturalSignetUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.wandering_eye_utility import WanderingEyeUtility
from Sources.oazix.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.spiritual_pain_utility import SpiritualPainUtility

class MesmerIneptitude_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # interrupt
        self.cry_of_pain_utility: CustomSkillUtilityBase = CryOfPainUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(90))
        self.power_drain_utility: CustomSkillUtilityBase = PowerDrainUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(92))

#         Cast Glyph of Lesser Energy↦Arcane Conundrum↦Cry of Pain on the largest group of foes, preferably hitting casters.
#         Deal damage against balled up attacking foes utilizing Ineptitude, Wandering Eye and Signet of Clumsiness.

        # core
        self.ineptitude_utility: CustomSkillUtilityBase = IneptitudeUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 75 if enemy_qte >= 2 else 40 if enemy_qte <= 2 else 0))
        self.wandering_eye_utility: CustomSkillUtilityBase = WanderingEyeUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 74 if enemy_qte >= 2 else 39 if enemy_qte <= 2 else 0))
        self.signet_of_clumsiness_utility: CustomSkillUtilityBase = SignetOfClumsinessUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 76 if enemy_qte >= 2 else 41 if enemy_qte <= 2 else 0))
        self.arcane_conundrum_utility: CustomSkillUtilityBase = ArcaneConundrumUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 77 if enemy_qte >= 2 else 42 if enemy_qte <= 2 else 0))
        
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
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.signet_of_clumsiness_utility,
            self.ebon_vanguard_assassin_support,
            self.ebon_battle_standard_of_wisdom,
            self.i_am_unstopabble,
            self.breath_of_the_great_dwarf_utility,
            self.by_urals_hammer_utility,
            self.flesh_of_my_flesh_utility,
            self.signet_of_return_utility,
            self.fall_back_utility,
            self.ineptitude_utility,
            self.cry_of_pain_utility,
            self.power_drain_utility,
            self.wandering_eye_utility,
            self.arcane_conundrum_utility,
            self.drain_enchantment_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.ineptitude_utility.custom_skill,
        ]