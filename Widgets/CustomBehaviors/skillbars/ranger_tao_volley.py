from typing import override

from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.skills.common.auto_attack_utility import AutoAttackUtility
from Widgets.CustomBehaviors.skills.common.breath_of_the_great_dwarf_utility import BreathOfTheGreatDwarfUtility
from Widgets.CustomBehaviors.skills.common.ebon_battle_standard_of_honor_utility import EbonBattleStandardOfHonorUtility
from Widgets.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import (
    EbonVanguardAssassinSupportUtility,
)
from Widgets.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Widgets.CustomBehaviors.skills.generic.hero_ai_utility import HeroAiUtility
from Widgets.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Widgets.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Widgets.CustomBehaviors.skills.generic.raw_simple_attack_utility import RawSimpleAttackUtility
from Widgets.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility
from Widgets.CustomBehaviors.skills.ranger.distracting_shot_utility import DistractingShotUtility
from Widgets.CustomBehaviors.skills.ranger.savage_shot_utility import SavageShotUtility
from Widgets.CustomBehaviors.skills.ranger.together_as_one import TogetherAsOneUtility


class RangerTaoVolleyUtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # core
        self.together_as_one_utility: CustomSkillUtilityBase = TogetherAsOneUtility(
            current_build=in_game_build, score_definition=ScoreStaticDefinition(95)
        )

        self.savage_shot_utility: CustomSkillUtilityBase = SavageShotUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(91))
        self.distracting_shot_utility: CustomSkillUtilityBase = DistractingShotUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(92))
        
        self.volley_utility: CustomSkillUtilityBase = RawAoeAttackUtility(skill=CustomSkill("Volley"), current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 70 if enemy_qte >= 3 else 65 if enemy_qte <= 2 else 25))

        self.volley_utility: CustomSkillUtilityBase = RawAoeAttackUtility(
            skill=CustomSkill("Volley"),
            current_build=in_game_build,
            score_definition=ScorePerAgentQuantityDefinition(
                lambda enemy_qte: 65 if enemy_qte >= 3 else 49 if enemy_qte <= 2 else 25
            ),
        )

        self.jagged_strike_utility: CustomSkillUtilityBase = HeroAiUtility(skill=CustomSkill("Jagged_Strike"), current_build=in_game_build, score_definition=ScoreStaticDefinition(40), mana_required_to_cast=10)
        self.fox_fangs_utility: CustomSkillUtilityBase = HeroAiUtility(skill=CustomSkill("Fox_Fangs"), current_build=in_game_build, score_definition=ScoreStaticDefinition(40), mana_required_to_cast=10)
        self.death_blossom_utility: CustomSkillUtilityBase = HeroAiUtility(skill=CustomSkill("Death_Blossom"), current_build=in_game_build, score_definition=ScoreStaticDefinition(40), mana_required_to_cast=10)

        #common
        self.ebon_battle_standard_of_honor_utility: CustomSkillUtilityBase = EbonBattleStandardOfHonorUtility(score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 68 if enemy_qte >= 3 else 50 if enemy_qte <= 2 else 25), current_build=in_game_build,  mana_required_to_cast=15)
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(score_definition=ScoreStaticDefinition(71), current_build=in_game_build, mana_required_to_cast=15)
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(99))
        self.fall_back_utility: CustomSkillUtilityBase = FallBackUtility(current_build=in_game_build)
        self.breath_of_the_great_dwarf_utility: CustomSkillUtilityBase = BreathOfTheGreatDwarfUtility(current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(9))
    
    @property
    @override
    def skills_allowed_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.together_as_one_utility,
            self.savage_shot_utility,
            self.distracting_shot_utility,
            self.volley_utility,
            self.never_rampage_alone_utility,
            self.ebon_battle_standard_of_honor_utility,
            self.ebon_vanguard_assassin_support,
            self.triple_shot_utility,
            self.sundering_attack_utility,
            self.breath_of_the_great_dwarf_utility,
            self.jagged_strike_utility,
            self.fox_fangs_utility,
            self.death_blossom_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.together_as_one_utility.custom_skill,
        ]
