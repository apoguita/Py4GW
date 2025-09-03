from typing import List, Any, Generator, Callable, override
import time
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.skills.assassin.disrupting_dagger_utility import DisruptingDaggerUtility
from Widgets.CustomBehaviors.skills.assassin.shroud_of_distress_utility import ShroudOfDistressUtility
from Widgets.CustomBehaviors.skills.botting.move_if_stuck import MoveIfStuckUtility
from Widgets.CustomBehaviors.skills.botting.move_to_enemy_if_close_enough import MoveToEnemyIfCloseEnoughUtility
from Widgets.CustomBehaviors.skills.botting.move_to_party_member_if_dead import MoveToPartyMemberIfDeadUtility
from Widgets.CustomBehaviors.skills.botting.move_to_party_member_if_in_aggro import MoveToPartyMemberIfInAggroUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_mana_too_low import WaitIfPartyMemberManaTooLowUtility
from Widgets.CustomBehaviors.skills.botting.wait_if_party_member_too_far import WaitIfPartyMemberTooFarUtility
from Widgets.CustomBehaviors.skills.common.auto_attack_utility import AutoAttackUtility
from Widgets.CustomBehaviors.skills.common.ebon_battle_standard_of_honor_utility import EbonBattleStandardOfHonorUtility
from Widgets.CustomBehaviors.skills.common.ebon_battle_standard_of_wisdom_utility import EbonBattleStandardOfWisdom
from Widgets.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Widgets.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Widgets.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility

class AssassinCriticalHit_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        self.shroud_of_distress_utility: CustomSkillUtilityBase = ShroudOfDistressUtility(score_definition=ScoreStaticDefinition(81), current_build=in_game_build, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO])
        self.critical_eye_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Critical_Eye"), current_build=in_game_build, score_definition=ScoreStaticDefinition(80), allowed_states=[BehaviorState.IN_AGGRO])
        self.way_of_the_assassin_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Way_of_the_Assassin"), current_build=in_game_build, score_definition=ScoreStaticDefinition(75), allowed_states=[BehaviorState.IN_AGGRO])
        self.critical_agility_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Critical_Agility"), current_build=in_game_build, score_definition=ScoreStaticDefinition(70), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.way_of_the_master_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Way_of_the_Master"), current_build=in_game_build, score_definition=ScoreStaticDefinition(60), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.critical_defenses_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Critical_Defenses"), current_build=in_game_build, score_definition=ScoreStaticDefinition(50), allowed_states=[BehaviorState.IN_AGGRO])
        self.disrupting_dagger_utility: CustomSkillUtilityBase = DisruptingDaggerUtility(score_definition=ScoreStaticDefinition(90), current_build=in_game_build)
        
        #common
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(score_definition=ScoreStaticDefinition(66), current_build=in_game_build, mana_required_to_cast=15)
        self.ebon_battle_standard_of_honor_utility: CustomSkillUtilityBase = EbonBattleStandardOfHonorUtility(score_definition=ScorePerAgentQuantityDefinition(lambda agent_qte: 45 if agent_qte >= 3 else 35 if agent_qte <= 2 else 25), current_build=in_game_build,  mana_required_to_cast=15)
        self.ebon_battle_standard_of_wisdom: CustomSkillUtilityBase = EbonBattleStandardOfWisdom(score_definition=ScorePerAgentQuantityDefinition(lambda agent_qte: 45 if agent_qte >= 3 else 35 if agent_qte <= 2 else 25), current_build=in_game_build, mana_required_to_cast=18)
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(99))

    @property
    @override
    def complete_build_with_generic_skills(self) -> bool:
        return True # because I'm playing it myself
    
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
            self.way_of_the_assassin_utility,
            self.critical_defenses_utility,
            self.shroud_of_distress_utility,
            self.disrupting_dagger_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.critical_eye_utility.custom_skill,
        ]