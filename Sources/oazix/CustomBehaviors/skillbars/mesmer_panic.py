# python
from typing import override

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.common.finish_him_utility import FinishHimUtility

from Sources.oazix.CustomBehaviors.skills.generic.raw_simple_attack_utility import RawSimpleAttackUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.mistrust_utility import MistrustUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.cry_of_pain_utility import CryOfPainUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.unnatural_signet_utility import UnnaturalSignetUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.auspicious_incantation_utility import AuspiciousIncantationUtility

from Sources.oazix.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.panic_utility import PanicUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.spiritual_pain_utility import SpiritualPainUtility
from Sources.oazix.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility

class MesmerPanic_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        self.panic_utility: CustomSkillUtilityBase = PanicUtility(event_bus=self.event_bus,current_build=in_game_build,score_definition=ScoreStaticDefinition(88),mana_required_to_cast=0)

        # Optional damage utilities
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(event_bus=self.event_bus,score_definition=ScoreStaticDefinition(84),current_build=in_game_build,mana_required_to_cast=15)
        self.you_move_like_a_dwarf_utility: CustomSkillUtilityBase = RawSimpleAttackUtility(event_bus=self.event_bus,skill=CustomSkill("You_Move_Like_A_Dwarf"),current_build=in_game_build,score_definition=ScoreStaticDefinition(82),mana_required_to_cast=0)
        self.shatter_delusions_utility: CustomSkillUtilityBase = RawAoeAttackUtility(event_bus=self.event_bus,skill=CustomSkill("Shatter_Delusions"),current_build=in_game_build,score_definition=ScorePerAgentQuantityDefinition(lambda q: 85 if q >= 2 else 40),mana_required_to_cast=0)
        self.wastrels_worry_utility: CustomSkillUtilityBase = RawAoeAttackUtility(event_bus=self.event_bus,skill=CustomSkill("Wastrels_Worry"),current_build=in_game_build,mana_required_to_cast=15)
        self.chaos_storm_utility: CustomSkillUtilityBase = RawAoeAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Chaos_Storm"), current_build=in_game_build, mana_required_to_cast=15)

        # Energy utilities (made AOE-aware)
        self.guilt_utility: CustomSkillUtilityBase = RawAoeAttackUtility(
            event_bus=self.event_bus,
            skill=CustomSkill("Guilt"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(lambda q: 80 if q >= 3 else 52 if q <= 2 else 0),
            mana_required_to_cast=0
        )

        # Snare / combo pair (use per-agent scoring for AOE utility)
        self.deep_freeze_utility: CustomSkillUtilityBase = RawAoeAttackUtility(event_bus=self.event_bus,skill=CustomSkill("Deep_Freeze"),current_build=in_game_build,score_definition=ScorePerAgentQuantityDefinition(lambda q: 2 if q >= 3 else 1 if q <= 2 else 0),mana_required_to_cast=8)

        # Auspicious configured to cast Deep Freeze immediately after if appropriate
        self.auspicious_incantation_utility: CustomSkillUtilityBase = AuspiciousIncantationUtility(event_bus=self.event_bus,current_build=in_game_build,original_skill_to_cast=self.deep_freeze_utility,auspicious_score_definition=ScoreStaticDefinition(87))

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            # required first
            self.panic_utility,

            # high priority damage / interrupts
            self.ebon_vanguard_assassin_support,
            self.shatter_delusions_utility,

            # nukes
            self.wastrels_worry_utility,
            self.chaos_storm_utility,
            self.you_move_like_a_dwarf_utility,

            # energy management / combos
            self.guilt_utility,
            self.auspicious_incantation_utility,
            self.deep_freeze_utility,
        ]


    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.panic_utility.custom_skill,
     ]
