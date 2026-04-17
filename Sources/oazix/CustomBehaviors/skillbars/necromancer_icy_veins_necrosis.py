from typing import override

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import \
    ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.minion_invocation_from_corpse_utility import \
    MinionInvocationFromCorpseUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.arcane_echo_utility import ArcaneEchoUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.auspicious_incantation_utility import AuspiciousIncantationUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.spiritual_pain_utility import SpiritualPainUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.wastrels_demise_utility import WastrelsDemiseUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.blood_of_the_master import BloodOfTheMasterUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.icy_veins_utility import IcyVeinsUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.putrid_bile_utility import PutridBile_NearDeathUtility
from Sources.oazix.CustomBehaviors.skills.necromancer.putrid_explosion_utility import PutridExplosionUtility


class NecromancerIcyVeinsNecrosis_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus)
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # MM skills
        self.animate_shambling_horror_utility: CustomSkillUtilityBase = MinionInvocationFromCorpseUtility(event_bus=self.event_bus, skill=CustomSkill("Animate_Shambling_Horror"), current_build=in_game_build, score_definition=ScoreStaticDefinition(62))
        self.animate_bone_fiend_utility: CustomSkillUtilityBase = MinionInvocationFromCorpseUtility(event_bus=self.event_bus, skill=CustomSkill("Animate_Bone_Fiend"), current_build=in_game_build, score_definition=ScoreStaticDefinition(61))
        self.animate_bone_horror_utility: CustomSkillUtilityBase = MinionInvocationFromCorpseUtility(event_bus=self.event_bus, skill=CustomSkill("Animate_Bone_Horror"), current_build=in_game_build, score_definition=ScoreStaticDefinition(59))
        self.animate_vampiric_horror_utility: CustomSkillUtilityBase = MinionInvocationFromCorpseUtility(event_bus=self.event_bus, skill=CustomSkill("Animate_Vampiric_Horror"), current_build=in_game_build, score_definition=ScoreStaticDefinition(60))
        self.blood_of_the_master_utility: CustomSkillUtilityBase = BloodOfTheMasterUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(33))

        # aoe
        self.overload_utility: CustomSkillUtilityBase = RawAoeAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Overload"), current_build=in_game_build, mana_required_to_cast=15)
        self.chaos_storm_utility: CustomSkillUtilityBase = RawAoeAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Chaos_Storm"), current_build=in_game_build, mana_required_to_cast=15)
        self.icy_veins_utility: CustomSkillUtilityBase = IcyVeinsUtility(event_bus=self.event_bus, current_build=in_game_build)

        self.arcane_echo_utility: CustomSkillUtilityBase = ArcaneEchoUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            original_skill_to_copy= self.icy_veins_utility,
            new_copied_instance= IcyVeinsUtility(
                event_bus=self.event_bus,
                current_build=in_game_build,
                score_definition=ScoreStaticDefinition(41) # slightly more than above
            ),
            arcane_echo_score_definition=ScoreStaticDefinition(82))
        
        self.auspicious_incantation_utility: CustomSkillUtilityBase = AuspiciousIncantationUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            original_skill_to_cast=self.arcane_echo_utility,
            score_definition=ScoreStaticDefinition(82)
        )

        # utilities
        self.masochism_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Masochism"),
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(92),
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO],
        )
        self.putrid_bile_utility: CustomSkillUtilityBase = PutridBile_NearDeathUtility(
            event_bus=self.event_bus,
            current_build=in_game_build
        )
        self.putrid_explosion_utility: CustomSkillUtilityBase = PutridExplosionUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(
                lambda enemy_qte: 80 if enemy_qte >= 2 else 35
            ),
            mana_required_to_cast=5,
        )

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.icy_veins_utility,
            self.putrid_bile_utility,

            self.animate_bone_fiend_utility,
            self.animate_bone_horror_utility,
            self.animate_vampiric_horror_utility,
            self.animate_shambling_horror_utility,
            self.blood_of_the_master_utility,

            self.overload_utility,
            self.chaos_storm_utility,
            self.arcane_echo_utility,
            self.auspicious_incantation_utility,

            self.putrid_explosion_utility,
            self.masochism_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.icy_veins_utility.custom_skill,
        ]
