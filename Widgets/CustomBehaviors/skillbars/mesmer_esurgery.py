from typing import override

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
from Widgets.CustomBehaviors.skills.mesmer.arcane_echo_utility import ArcaneEchoUtility
from Widgets.CustomBehaviors.skills.mesmer.auspicious_incantation_utility import AuspiciousIncantationUtility
from Widgets.CustomBehaviors.skills.mesmer.cry_of_frustration_utility import CryOfFrustrationUtility
from Widgets.CustomBehaviors.skills.mesmer.cry_of_pain_utility import CryOfPainUtility
from Widgets.CustomBehaviors.skills.mesmer.drain_enchantment_utility import DrainEnchantmentUtility
from Widgets.CustomBehaviors.skills.mesmer.mistrust_utility import MistrustUtility
from Widgets.CustomBehaviors.skills.mesmer.power_drain_utility import PowerDrainUtility
from Widgets.CustomBehaviors.skills.mesmer.shatter_enchantment_utility import ShatterEnchantmentUtility
from Widgets.CustomBehaviors.skills.mesmer.shatter_hex_utility import ShatterHexUtility
from Widgets.CustomBehaviors.skills.mesmer.spiritual_pain_utility import SpiritualPainUtility
from Widgets.CustomBehaviors.skills.mesmer.unnatural_signet_utility import UnnaturalSignetUtility
from Widgets.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility

class MesmerESurgery_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # interrupt
        self.cry_of_pain_utility: CustomSkillUtilityBase = CryOfPainUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(90))
        self.cry_of_frustration_utility: CustomSkillUtilityBase = CryOfFrustrationUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(91))
        self.power_drain_utility: CustomSkillUtilityBase = PowerDrainUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(92))

        # hex
        self.mistrust_utility: CustomSkillUtilityBase = MistrustUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 70 if enemy_qte >= 3 else 40 if enemy_qte <= 2 else 0), mana_required_to_cast=10)
        self.unnatural_signet_utility: CustomSkillUtilityBase = UnnaturalSignetUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 90 if enemy_qte >= 2 else 40 if enemy_qte <= 2 else 0))

        #shatter/drain
        self.shatter_hex_utility: CustomSkillUtilityBase = ShatterHexUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 95 if enemy_qte >= 2 else 20))
        self.shatter_enchantment_utility: CustomSkillUtilityBase = ShatterEnchantmentUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.drain_enchantment_utility: CustomSkillUtilityBase = DrainEnchantmentUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(89))

        # aoe
        self.energy_surge_utility: CustomSkillUtilityBase = RawAoeAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Energy_Surge"), current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 80 if enemy_qte >= 3 else 52 if enemy_qte <= 2 else 0), mana_required_to_cast=12)
        self.overload_utility: CustomSkillUtilityBase = RawAoeAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Overload"), current_build=in_game_build, mana_required_to_cast=15)
        self.chaos_storm_utility: CustomSkillUtilityBase = RawAoeAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Chaos_Storm"), current_build=in_game_build, mana_required_to_cast=15)
        self.wastrels_demise_utility: CustomSkillUtilityBase = RawAoeAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Wastrels_Demise"), current_build=in_game_build, mana_required_to_cast=15)
        self.spiritual_pain_utility: CustomSkillUtilityBase = SpiritualPainUtility(event_bus=self.event_bus, current_build=in_game_build, mana_required_to_cast=10)

        # utilities
        self.energy_tap_utility: CustomSkillUtilityBase = HeroAiUtility(event_bus=self.event_bus, skill=CustomSkill("Energy_Tap"), current_build=in_game_build, score_definition=ScoreStaticDefinition(85))
        self.fall_back_utility: CustomSkillUtilityBase = FallBackUtility(event_bus=self.event_bus, current_build=in_game_build)
        
        self.arcane_echo_utility: CustomSkillUtilityBase = ArcaneEchoUtility(
            event_bus=self.event_bus, 
            current_build=in_game_build, 
            original_skill_to_copy= self.energy_surge_utility, 
            new_copied_instance= RawAoeAttackUtility(
                event_bus=self.event_bus, 
                skill=CustomSkill("Energy_Surge"), 
                current_build=in_game_build, 
                score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 80 if enemy_qte >= 3 else 50 if enemy_qte <= 2 else 0), 
                mana_required_to_cast=12),
            arcane_echo_score_definition=ScoreStaticDefinition(82))
        self.auspicious_incantation_utility: CustomSkillUtilityBase = AuspiciousIncantationUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            original_skill_to_cast=self.arcane_echo_utility,
            auspicious_score_definition=ScoreStaticDefinition(82)
        )


        #common
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(event_bus=self.event_bus, score_definition=ScoreStaticDefinition(71), current_build=in_game_build, mana_required_to_cast=15)
        self.ebon_battle_standard_of_wisdom: CustomSkillUtilityBase = EbonBattleStandardOfWisdom(event_bus=self.event_bus, score_definition= ScorePerAgentQuantityDefinition(lambda agent_qte: 80 if agent_qte >= 3 else 60 if agent_qte <= 2 else 40), current_build=in_game_build, mana_required_to_cast=18)
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(99))
        self.breath_of_the_great_dwarf_utility: CustomSkillUtilityBase = BreathOfTheGreatDwarfUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(9))
        self.flesh_of_my_flesh_utility: CustomSkillUtilityBase = GenericResurrectionUtility(event_bus=self.event_bus, skill=CustomSkill("Flesh_of_My_Flesh"), current_build=in_game_build,score_definition=ScoreStaticDefinition(12))
        self.signet_of_return_utility: CustomSkillUtilityBase = GenericResurrectionUtility(event_bus=self.event_bus, skill=CustomSkill("Signet_of_Return"), current_build=in_game_build,score_definition=ScoreStaticDefinition(12))
        self.by_urals_hammer_utility: CustomSkillUtilityBase = ByUralsHammerUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.air_of_superiority_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Air_of_Superiority"), mana_required_to_cast=5, current_build=in_game_build, score_definition=ScoreStaticDefinition(50), allowed_states= [BehaviorState.IN_AGGRO])

    @property
    @override
    def skills_allowed_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.cry_of_pain_utility,
            self.cry_of_frustration_utility,

            self.shatter_hex_utility,
            self.shatter_enchantment_utility,
            self.drain_enchantment_utility,

            self.mistrust_utility,
            self.unnatural_signet_utility,

            self.energy_surge_utility,
            self.overload_utility,
            self.chaos_storm_utility,
            self.wastrels_demise_utility,
            self.spiritual_pain_utility,

            self.power_drain_utility,

            self.energy_tap_utility,
            self.overload_utility,

            self.fall_back_utility,
            self.arcane_echo_utility,
            self.auspicious_incantation_utility,

            self.ebon_vanguard_assassin_support,
            self.ebon_battle_standard_of_wisdom,
            self.i_am_unstopabble,
            self.breath_of_the_great_dwarf_utility,
            self.by_urals_hammer_utility,
            self.flesh_of_my_flesh_utility,
            self.signet_of_return_utility,
            self.air_of_superiority_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.energy_surge_utility.custom_skill,
        ]