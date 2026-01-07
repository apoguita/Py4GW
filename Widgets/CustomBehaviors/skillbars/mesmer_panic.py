# python
from typing import override

from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.skills.common.finish_him_utility import FinishHimUtility

from Widgets.CustomBehaviors.skills.mesmer.mistrust_utility import MistrustUtility
from Widgets.CustomBehaviors.skills.mesmer.cry_of_pain_utility import CryOfPainUtility
from Widgets.CustomBehaviors.skills.mesmer.unnatural_signet_utility import UnnaturalSignetUtility
from Widgets.CustomBehaviors.skills.mesmer.auspicious_incantation_utility import AuspiciousIncantationUtility

from Widgets.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Widgets.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Widgets.CustomBehaviors.skills.mesmer.spiritual_pain_utility import SpiritualPainUtility
from Widgets.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility

class MesmerPanic_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # Required panic-related utilities (use generic RawAoeAttackUtility for skill ids that are simple casts)
        self.panic_utility: CustomSkillUtilityBase = RawAoeAttackUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Panic"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 80 if enemy_qte >= 3 else 52 if enemy_qte <= 2 else 0),
            mana_required_to_cast=0
        )
        self.mistrust_utility: CustomSkillUtilityBase = MistrustUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda q: 95 if q >= 3 else 80 if q == 2 else 90),
            mana_required_to_cast=10
        )
        self.cry_of_pain_utility: CustomSkillUtilityBase = CryOfPainUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            score_definition=ScoreStaticDefinition(90)
        )
        self.unnatural_signet_utility: CustomSkillUtilityBase = UnnaturalSignetUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 90 if enemy_qte >= 2 else 40 if enemy_qte <= 2 else 0)
        )

        # Optional damage utilities
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(
            event_bus=self.event_bus,
            score_definition=ScoreStaticDefinition(88),
            current_build=in_game_build,
            mana_required_to_cast=15
        )
        self.finish_him_utility: CustomSkillUtilityBase = FinishHimUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.you_move_like_a_dwarf_utility: CustomSkillUtilityBase = RawAoeAttackUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("You_Move_Like_A_Dwarf"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda q: 82 if q >= 3 else 50),
            mana_required_to_cast=0
        )
        self.cry_of_frustration_utility: CustomSkillUtilityBase = RawAoeAttackUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Cry_of_Frustration"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda q: 86 if q >= 3 else 70),
            mana_required_to_cast=0
        )
        self.shatter_delusions_utility: CustomSkillUtilityBase = RawAoeAttackUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Shatter_Delusions"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda q: 85 if q >= 2 else 40),
            mana_required_to_cast=0
        )
        self.wastrels_demise_utility: CustomSkillUtilityBase = RawAoeAttackUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Wastrels_Demise"),
            current_build=in_game_build,
            mana_required_to_cast=15
        )
        self.wastrels_worry_utility: CustomSkillUtilityBase = RawAoeAttackUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Wastrels_Worry"),
            current_build=in_game_build,
            mana_required_to_cast=15
        )
        self.chaos_storm_utility: CustomSkillUtilityBase = RawAoeAttackUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Chaos_Storm"),
            current_build=in_game_build,
            mana_required_to_cast=15
        )
        self.shatter_hex_utility: CustomSkillUtilityBase = RawAoeAttackUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Shatter_Hex"),
            current_build=in_game_build,
            mana_required_to_cast=0
        )
        self.spiritual_pain_utility: CustomSkillUtilityBase = SpiritualPainUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            mana_required_to_cast=10
        )

        # Energy utilities (made AOE-aware)
        self.guilt_utility: CustomSkillUtilityBase = RawAoeAttackUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Guilt"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda q: 80 if q >= 3 else 52 if q <= 2 else 0),
            mana_required_to_cast=0
        )

        # Snare / combo pair (use per-agent scoring for AOE utility)
        self.deep_freeze_utility: CustomSkillUtilityBase = RawAoeAttackUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Deep_Freeze"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda q: 2 if q >= 3 else 1 if q <= 2 else 0),
            mana_required_to_cast=8
        )

        # Auspicious configured to cast Deep Freeze immediately after if appropriate
        self.auspicious_incantation_utility: CustomSkillUtilityBase = AuspiciousIncantationUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
            original_skill_to_cast=self.deep_freeze_utility,
            auspicious_score_definition=ScoreStaticDefinition(87)
        )

        # Fallback / common
        self.fall_back_utility: CustomSkillUtilityBase = FallBackUtility(event_bus=self.event_bus, current_build=in_game_build)

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            # required first
            self.panic_utility,
            self.mistrust_utility,
            self.cry_of_pain_utility,
            self.unnatural_signet_utility,

            # high priority damage / interrupts
            self.ebon_vanguard_assassin_support,
            self.cry_of_frustration_utility,
            self.shatter_delusions_utility,
            self.shatter_hex_utility,

            # nukes
            self.wastrels_demise_utility,
            self.wastrels_worry_utility,
            self.chaos_storm_utility,
            self.spiritual_pain_utility,
            self.finish_him_utility,
            self.you_move_like_a_dwarf_utility,

            # energy management / combos
            self.guilt_utility,
            self.auspicious_incantation_utility,
            self.deep_freeze_utility,

            # fallback
            self.fall_back_utility,
        ]


    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            CustomSkill("Panic"),
            CustomSkill("Mistrust"),
            CustomSkill("Cry_of_Pain"),
            CustomSkill("Unnatural_Signet"),
     ]
