from typing import override

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skillbars.disabilities.condition_priority import ConditionPriority
from Sources.oazix.CustomBehaviors.primitives.skillbars.disabilities.disability_priority import DisabilityPriority
from Sources.oazix.CustomBehaviors.primitives.skillbars.disabilities.hex_prioritiy import HexPriority
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.dervich.dervich_enchantment_utility import DervichEnchantmentUtility
from Sources.oazix.CustomBehaviors.skills.dervich.scythe_requiring_enchantment_utility import ScytheRequiringEnchantmentUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility


class NecromancerSoulTaker_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus)
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # core skills
        self.masochism_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Masochism"), current_build=in_game_build, score_definition=ScoreStaticDefinition(90), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.soul_taker_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Soul_Taker"), current_build=in_game_build, score_definition=ScoreStaticDefinition(89), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])

        # scythe attacks
        self.twin_moon_sweep_utility: CustomSkillUtilityBase = ScytheRequiringEnchantmentUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Twin_Moon_Sweep"), score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 81 if enemy_qte >= 3 else 53 if enemy_qte <= 2 else 21))
        self.eremites_attack_utility: CustomSkillUtilityBase = ScytheRequiringEnchantmentUtility(event_bus=self.event_bus, current_build=in_game_build, skill=CustomSkill("Eremites_Attack"), score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 80 if enemy_qte >= 3 else 52 if enemy_qte <= 2 else 20))
        # dervish enchantments
        self.sand_shards_utility: CustomSkillUtilityBase = DervichEnchantmentUtility(event_bus=self.event_bus, skill=CustomSkill("Sand_Shards"), current_build=in_game_build, score_definition=ScoreStaticDefinition(88), renew_before_expiration_in_milliseconds=99999)
        self.mirage_cloak_utility: CustomSkillUtilityBase = DervichEnchantmentUtility(event_bus=self.event_bus, skill=CustomSkill("Mirage_Cloak"), current_build=in_game_build, score_definition=ScoreStaticDefinition(88), renew_before_expiration_in_milliseconds=99999)

        self.rending_aura_utility: CustomSkillUtilityBase = DervichEnchantmentUtility(event_bus=self.event_bus, skill=CustomSkill("Rending_Aura"), current_build=in_game_build, score_definition=ScoreStaticDefinition(85), renew_before_expiration_in_milliseconds=99999)
        self.hearth_of_holy_flame_utility: CustomSkillUtilityBase = DervichEnchantmentUtility(event_bus=self.event_bus, skill=CustomSkill("Hearth_of_Holy_Flame"), current_build=in_game_build, score_definition=ScoreStaticDefinition(85), renew_before_expiration_in_milliseconds=99999)
        self.staggering_force_utility: CustomSkillUtilityBase = DervichEnchantmentUtility(event_bus=self.event_bus, skill=CustomSkill("Staggering_Force"), current_build=in_game_build, score_definition=ScoreStaticDefinition(85), renew_before_expiration_in_milliseconds=99999)
        self.dust_cloak_utility: CustomSkillUtilityBase = DervichEnchantmentUtility(event_bus=self.event_bus, skill=CustomSkill("Dust_Cloak"), current_build=in_game_build, score_definition=ScoreStaticDefinition(85), renew_before_expiration_in_milliseconds=99999)

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.soul_taker_utility,
            self.masochism_utility,

            self.twin_moon_sweep_utility,
            self.eremites_attack_utility,

            self.rending_aura_utility,
            self.hearth_of_holy_flame_utility,
            self.staggering_force_utility,
            self.dust_cloak_utility,
            self.mirage_cloak_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.soul_taker_utility.custom_skill,
        ]
    
    @override
    def hexes_to_dispell_extra_priority(self) -> list[HexPriority]:
        return [
            HexPriority(CustomSkill("Deep_Freeze"), DisabilityPriority.HIGH),
            HexPriority(CustomSkill("Mind_Freeze"), DisabilityPriority.HIGH),
        ]
    
    @override
    def conditions_to_dispell_extra_priority(self) -> list[ConditionPriority]:
        return [
            ConditionPriority(CustomSkill("Crippled"), DisabilityPriority.HIGH),
            ConditionPriority(CustomSkill("Blind"), DisabilityPriority.NORMAL), # not as much important as others
        ]
