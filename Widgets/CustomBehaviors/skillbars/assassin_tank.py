from typing import List, Any, Generator, Callable, override
import time
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.skills.assassin.deadly_paradox_utility import DeadlyParadoxUtility
from Widgets.CustomBehaviors.skills.assassin.shadow_form_utility import ShadowFormUtility
from Widgets.CustomBehaviors.skills.assassin.shroud_of_distress_utility import ShroudOfDistressUtility
from Widgets.CustomBehaviors.skills.common.auto_attack_utility import AutoAttackUtility
from Widgets.CustomBehaviors.skills.common.ebon_battle_standard_of_honor_utility import EbonBattleStandardOfHonorUtility
from Widgets.CustomBehaviors.skills.common.ebon_battle_standard_of_wisdom_utility import EbonBattleStandardOfWisdom
from Widgets.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Widgets.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Widgets.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Widgets.CustomBehaviors.skills.generic.protective_shout_utility import ProtectiveShoutUtility
from Widgets.CustomBehaviors.skills.paragon.heroic_refrain_utility import HeroicRefrainUtility

class AssassinTank_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())
        self.auto_attack: CustomSkillUtilityBase = AutoAttackUtility(current_build=in_game_build)

        #core
        self.deadly_paradox_utility: CustomSkillUtilityBase = DeadlyParadoxUtility(score_definition=ScoreStaticDefinition(70), current_build=in_game_build, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.shroud_of_distress_utility: CustomSkillUtilityBase = ShroudOfDistressUtility(score_definition=ScoreStaticDefinition(66), current_build=in_game_build, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO])
        self.shadow_form_utility: CustomSkillUtilityBase = ShadowFormUtility(score_definition=ScoreStaticDefinition(65), is_deadly_paradox_required=True, current_build=in_game_build, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])

        
        #optional
        self.silver_armor_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Sliver_Armor"), current_build=in_game_build, score_definition=ScoreStaticDefinition(61), mana_required_to_cast=17, allowed_states=[BehaviorState.IN_AGGRO])
        self.stoneflesh_aura_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Stoneflesh_Aura"), current_build=in_game_build, score_definition=ScoreStaticDefinition(60), mana_required_to_cast=17, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.armor_of_earth_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Armor_of_Earth"), current_build=in_game_build, score_definition=ScoreStaticDefinition(58), mana_required_to_cast=17, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])

        self.critical_agility_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Critical_Agility"), current_build=in_game_build, score_definition=ScoreStaticDefinition(50), mana_required_to_cast=20, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])

        #common
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(45))
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(score_definition=ScoreStaticDefinition(40), current_build=in_game_build, mana_required_to_cast=20)
    

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
            self.shroud_of_distress_utility,
            self.deadly_paradox_utility,
            self.shadow_form_utility,
            self.armor_of_earth_utility,
            self.critical_agility_utility,
            self.ebon_vanguard_assassin_support,
            self.i_am_unstopabble,
            self.stoneflesh_aura_utility,
            self.silver_armor_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.shadow_form_utility.custom_skill,
            self.deadly_paradox_utility.custom_skill,
            self.i_am_unstopabble.custom_skill,
        ]