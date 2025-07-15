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
from Widgets.CustomBehaviors.skills.paragon.heroic_refrain_utility import HeroicRefrainUtility

class AssassinCriticalHit_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self, cached_data: CacheData):
        super().__init__(cached_data)
        in_game_build = list(CustomBehaviorBase.get_in_game_build().values())
        self.auto_attack: CustomSkillUtilityBase = AutoAttackUtility(current_build=in_game_build)

        self.critical_eye_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Critical_Eye"), current_build=in_game_build, score_definition=ScoreStaticDefinition(80), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.critical_agility_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Critical_Agility"), current_build=in_game_build, score_definition=ScoreStaticDefinition(70), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.way_of_the_master_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Way_of_the_Master"), current_build=in_game_build, score_definition=ScoreStaticDefinition(60), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        
        #common
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(score_definition=ScoreStaticDefinition(66), current_build=in_game_build, mana_required_to_cast=15)
        self.ebon_battle_standard_of_honor_utility: CustomSkillUtilityBase = EbonBattleStandardOfHonorUtility(score_definition=ScorePerAgentQuantityDefinition(lambda agent_qte: 45 if agent_qte >= 3 else 35 if agent_qte <= 2 else 25), current_build=in_game_build,  mana_required_to_cast=15)
        self.ebon_battle_standard_of_wisdom: CustomSkillUtilityBase = EbonBattleStandardOfWisdom(score_definition=ScorePerAgentQuantityDefinition(lambda agent_qte: 45 if agent_qte >= 3 else 35 if agent_qte <= 2 else 25), current_build=in_game_build, mana_required_to_cast=18)
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(99))
    

    @property
    @override
    def additional_autonomous_skills(self) -> list[CustomSkillUtilityBase]:
        return [
        ]

    @property
    @override
    def complete_build_with_generic_skills(self) -> bool:
        return False # because I'm playing it myself
    
    @property
    @override
    def skills_allowed_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.critical_eye_utility,
            self.critical_agility_utility,
            self.way_of_the_master_utility,
            self.ebon_vanguard_assassin_support,
            self.ebon_battle_standard_of_honor_utility,
            self.ebon_battle_standard_of_wisdom,
            self.i_am_unstopabble,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.critical_eye_utility.custom_skill,
        ]