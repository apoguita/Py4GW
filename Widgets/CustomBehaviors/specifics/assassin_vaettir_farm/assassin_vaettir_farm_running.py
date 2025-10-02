from typing import List, Any, Generator, Callable, override
import time
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState

from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.skills.assassin.deadly_paradox_utility import DeadlyParadoxUtility
from Widgets.CustomBehaviors.skills.assassin.heart_of_shadow_utility import HeartofShadowUtility
from Widgets.CustomBehaviors.skills.assassin.shadow_form_utility import ShadowFormUtility
from Widgets.CustomBehaviors.skills.assassin.shroud_of_distress_utility import ShroudOfDistressUtility
from Widgets.CustomBehaviors.skills.common.auto_attack_utility import AutoAttackUtility
from Widgets.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility

class AssassinVaettirFarm_Running_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())
        self.auto_attack: CustomSkillUtilityBase = AutoAttackUtility(current_build=in_game_build)

        #core
        self.deadly_paradox_utility: CustomSkillUtilityBase = DeadlyParadoxUtility(score_definition=ScoreStaticDefinition(70), current_build=in_game_build, allowed_states=[BehaviorState.IN_AGGRO])
        self.shroud_of_distress_utility: CustomSkillUtilityBase = ShroudOfDistressUtility(score_definition=ScoreStaticDefinition(66), current_build=in_game_build)
        self.shadow_form_utility: CustomSkillUtilityBase = ShadowFormUtility(score_definition=ScoreStaticDefinition(65), is_deadly_paradox_required=True,  renew_before_expiration_in_milliseconds=3500, current_build=in_game_build, allowed_states=[BehaviorState.IN_AGGRO])
        self.heart_of_shadow_utility: CustomSkillUtilityBase = HeartofShadowUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(50), mana_required_to_cast=20, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO])

        # others
        self.dark_escape_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Dark_Escape"), current_build=in_game_build, score_definition=ScoreStaticDefinition(50), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO])
        self.way_of_perfection_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Way_of_Perfection"), current_build=in_game_build, score_definition=ScoreStaticDefinition(50), mana_required_to_cast=10)
        self.great_dwarf_armor_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Great_Dwarf_Armor"), current_build=in_game_build, score_definition=ScoreStaticDefinition(50), mana_required_to_cast=10)

        # how to make no coupling with hot-reload, dedicated folder for thoses ?

    @property
    @override
    def additional_autonomous_skills(self) -> list[CustomSkillUtilityBase]:
        return [
        ]

    @property
    @override
    def complete_build_with_generic_skills(self) -> bool:
        return False
    
    @property
    @override
    def skills_allowed_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.shroud_of_distress_utility,
            self.deadly_paradox_utility,
            self.shadow_form_utility,
            self.way_of_perfection_utility,
            self.great_dwarf_armor_utility,
            self.dark_escape_utility
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.shroud_of_distress_utility.custom_skill,
            self.deadly_paradox_utility.custom_skill,
            self.shadow_form_utility.custom_skill,
        ]