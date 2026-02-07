from typing import override

from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.common.by_urals_hammer_utility import ByUralsHammerUtility
from Sources.oazix.CustomBehaviors.skills.common.finish_him_utility import FinishHimUtility
from Sources.oazix.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Sources.oazix.CustomBehaviors.skills.dervich.dervich_enchantment_utility import DervichEnchantmentUtility
from Sources.oazix.CustomBehaviors.skills.dervich.scythe_requiring_enchantment_utility import ScytheRequiringEnchantmentUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.signet_of_lost_souls_utility import SignetOfLostSoulsUtility
from Sources.oazix.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility


class NecromancerSoulTaker_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # core skills
        self.soul_taker_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Soul_Taker"), current_build=in_game_build, score_definition=ScoreStaticDefinition(90))
        self.masochism_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Masochism"), current_build=in_game_build, score_definition=ScoreStaticDefinition(89))

        # scythe attacks
        self.twin_moon_sweep_utility: CustomSkillUtilityBase = ScytheRequiringEnchantmentUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Twin_Moon_Sweep"), score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 81 if enemy_qte >= 3 else 53 if enemy_qte <= 2 else 21))
        self.eremites_attack_utility: CustomSkillUtilityBase = ScytheRequiringEnchantmentUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Eremites_Attack"), score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 80 if enemy_qte >= 3 else 52 if enemy_qte <= 2 else 20))
        # dervish enchantments
        self.rending_aura_utility: CustomSkillUtilityBase = DervichEnchantmentUtility(event_bus=self.event_bus, skill=CustomSkill("Rending_Aura"), current_build=in_game_build, score_definition=ScoreStaticDefinition(88), renew_before_expiration_in_milliseconds=99999)
        self.hearth_of_holy_flame_utility: CustomSkillUtilityBase = DervichEnchantmentUtility(event_bus=self.event_bus, skill=CustomSkill("Hearth_of_Holy_Flame"), current_build=in_game_build, score_definition=ScoreStaticDefinition(88), renew_before_expiration_in_milliseconds=99999)
        self.staggering_force_utility: CustomSkillUtilityBase = DervichEnchantmentUtility(event_bus=self.event_bus, skill=CustomSkill("Staggering_Force"), current_build=in_game_build, score_definition=ScoreStaticDefinition(88), renew_before_expiration_in_milliseconds=99999)
        self.dust_cloak_utility: CustomSkillUtilityBase = DervichEnchantmentUtility(event_bus=self.event_bus, skill=CustomSkill("Dust_Cloak"), current_build=in_game_build, score_definition=ScoreStaticDefinition(88), renew_before_expiration_in_milliseconds=99999)

        # common
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(99))
        self.fall_back_utility: CustomSkillUtilityBase = FallBackUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.signet_of_lost_souls_utility: CustomSkillUtilityBase = SignetOfLostSoulsUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.by_urals_hammer_utility: CustomSkillUtilityBase = ByUralsHammerUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.finish_him_utility: CustomSkillUtilityBase = FinishHimUtility(event_bus=self.event_bus, current_build=in_game_build)

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.i_am_unstopabble,
            self.fall_back_utility,
            self.signet_of_lost_souls_utility,
            self.by_urals_hammer_utility,
            self.finish_him_utility,

            self.soul_taker_utility,
            self.masochism_utility,

            self.twin_moon_sweep_utility,
            self.eremites_attack_utility,

            self.rending_aura_utility,
            self.hearth_of_holy_flame_utility,
            self.staggering_force_utility,
            self.dust_cloak_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.soul_taker_utility.custom_skill,
        ]
