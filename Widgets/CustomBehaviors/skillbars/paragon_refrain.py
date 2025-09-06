from typing import override

from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.skills.common.auto_attack_utility import AutoAttackUtility
from Widgets.CustomBehaviors.skills.common.ebon_battle_standard_of_wisdom_utility import EbonBattleStandardOfWisdom
from Widgets.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Widgets.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Widgets.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Widgets.CustomBehaviors.skills.generic.protective_shout_utility import ProtectiveShoutUtility
from Widgets.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility
from Widgets.CustomBehaviors.skills.paragon.heroic_refrain_utility import HeroicRefrainUtility
from Widgets.CustomBehaviors.skills.warrior.protectors_defense_utility import ProtectorsDefenseUtility


class ParagonRefrain_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        #core
        self.heroic_refrain_utility: CustomSkillUtilityBase = HeroicRefrainUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(50))
        self.theyre_on_fire_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Theyre_on_Fire"), current_build=in_game_build, score_definition=ScoreStaticDefinition(80), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO])
        
        #optional
        self.theres_nothing_to_fear: CustomSkillUtilityBase = ProtectiveShoutUtility(skill=CustomSkill("Theres_Nothing_to_Fear"), current_build=in_game_build, allies_health_less_than_percent=0.9, allies_quantity_required=1,score_definition= ScoreStaticDefinition(90), allowed_states=[BehaviorState.IN_AGGRO])
        self.save_yourselves_luxon: CustomSkillUtilityBase = ProtectiveShoutUtility(skill=CustomSkill("Save_Yourselves_luxon"), current_build=in_game_build, allies_health_less_than_percent=0.7, allies_quantity_required=1,score_definition=ScoreStaticDefinition(89), allowed_states=[BehaviorState.IN_AGGRO])
        self.save_yourselves_kurzick: CustomSkillUtilityBase = ProtectiveShoutUtility(skill=CustomSkill("Save_Yourselves_kurzick"), current_build=in_game_build, allies_health_less_than_percent=0.7, allies_quantity_required=1,score_definition=ScoreStaticDefinition(89), allowed_states=[BehaviorState.IN_AGGRO])
        self.never_surrender: CustomSkillUtilityBase = ProtectiveShoutUtility(skill=CustomSkill("Never_Surrender"), current_build=in_game_build, allies_health_less_than_percent=0.7,allies_quantity_required=2,score_definition=ScoreStaticDefinition(88), allowed_states=[BehaviorState.IN_AGGRO])

        #common
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(score_definition=ScoreStaticDefinition(71), current_build=in_game_build, mana_required_to_cast=15)
        self.ebon_battle_standard_of_wisdom: CustomSkillUtilityBase = EbonBattleStandardOfWisdom(score_definition= ScorePerAgentQuantityDefinition(lambda agent_qte: 80 if agent_qte >= 3 else 60 if agent_qte <= 2 else 40), current_build=in_game_build, mana_required_to_cast=18)
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(99))
        self.fall_back_utility: CustomSkillUtilityBase = FallBackUtility(current_build=in_game_build)
        self.protectors_defense_utility: CustomSkillUtilityBase = ProtectorsDefenseUtility(current_build=in_game_build,score_definition=ScoreStaticDefinition(60))
    
    @property
    @override
    def skills_allowed_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.heroic_refrain_utility,
            self.theyre_on_fire_utility,
            self.theres_nothing_to_fear,
            self.save_yourselves_luxon,
            self.save_yourselves_kurzick,
            self.never_surrender,

            self.ebon_vanguard_assassin_support,
            self.ebon_battle_standard_of_wisdom,
            self.i_am_unstopabble,
            self.fall_back_utility,
            self.protectors_defense_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.heroic_refrain_utility.custom_skill,
            self.theyre_on_fire_utility.custom_skill,
        ]