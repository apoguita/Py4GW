from typing import List, Any, Generator, Callable, override
import time
from HeroAI.cache_data import CacheData
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base import CustomBehaviorBase
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.skills.common.auto_attack_utility import AutoAttackUtility
from Widgets.CustomBehaviors.skills.common.ebon_battle_standard_of_honor_utility import EbonBattleStandardOfHonorUtility
from Widgets.CustomBehaviors.skills.common.ebon_battle_standard_of_wisdom_utility import EbonBattleStandardOfWisdom
from Widgets.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Widgets.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Widgets.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Widgets.CustomBehaviors.skills.generic.protective_shout_utility import ProtectiveShoutUtility
from Widgets.CustomBehaviors.skills.generic.raw_aoe_attack_utility import RawAoeAttackUtility
from Widgets.CustomBehaviors.skills.generic.raw_simple_attack_utility import RawSimpleAttackUtility
from Widgets.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility
from Widgets.CustomBehaviors.skills.paragon.heroic_refrain_utility import HeroicRefrainUtility
from Widgets.CustomBehaviors.skills.ranger.distracting_shot_utility import DistractingShotUtility
from Widgets.CustomBehaviors.skills.ranger.savage_shot_utility import SavageShotUtility
from Widgets.CustomBehaviors.skills.ranger.together_as_one import TogetherAsOneUtility

class RangerTaoVolley_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self, cached_data: CacheData):
        super().__init__(cached_data)
        in_game_build = list(CustomBehaviorBase.get_in_game_build().values())
        self.auto_attack: CustomSkillUtilityBase = AutoAttackUtility(current_build=in_game_build)

        # core
        self.together_as_one_utility: CustomSkillUtilityBase = TogetherAsOneUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(95))

        self.savage_shot_utility: CustomSkillUtilityBase = SavageShotUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(91))
        self.distracting_shot_utility: CustomSkillUtilityBase = DistractingShotUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(92))
        
        self.volley_utility: CustomSkillUtilityBase = RawAoeAttackUtility(skill=CustomSkill("Volley"), current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 65 if enemy_qte >= 3 else 49 if enemy_qte <= 2 else 25))

        #optional
        self.never_rampage_alone_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Never_Rampage_Alone"), current_build=in_game_build, score_definition=ScoreStaticDefinition(80), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.triple_shot_utility: CustomSkillUtilityBase = RawSimpleAttackUtility(skill=CustomSkill("Triple_Shot_luxon"), current_build=in_game_build, mana_required_to_cast=10, score_definition=ScoreStaticDefinition(70))
        self.sundering_attack_utility: CustomSkillUtilityBase = RawSimpleAttackUtility(skill=CustomSkill("Sundering_Attack"), current_build=in_game_build, mana_required_to_cast=10, score_definition=ScoreStaticDefinition(60))

        #common
        self.ebon_battle_standard_of_honor_utility: CustomSkillUtilityBase = EbonBattleStandardOfHonorUtility(score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 68 if enemy_qte >= 3 else 50 if enemy_qte <= 2 else 25), current_build=in_game_build,  mana_required_to_cast=15)
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(score_definition=ScoreStaticDefinition(71), current_build=in_game_build, mana_required_to_cast=15)
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(99))
        self.fall_back_utility: CustomSkillUtilityBase = FallBackUtility(current_build=in_game_build)
    

    @property
    @override
    def additional_autonomous_skills(self) -> list[CustomSkillUtilityBase]:
        return [
            self.auto_attack,
        ]

    @property
    @override
    def complete_build_with_generic_skills(self) -> bool:
        return True
    
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
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.together_as_one_utility.custom_skill,
            self.volley_utility.custom_skill,
        ]