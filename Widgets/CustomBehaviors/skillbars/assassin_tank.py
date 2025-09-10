from typing import override

from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.skills.assassin.deadly_paradox_utility import DeadlyParadoxUtility
from Widgets.CustomBehaviors.skills.assassin.disrupting_dagger_utility import DisruptingDaggerUtility
from Widgets.CustomBehaviors.skills.assassin.shadow_form_utility import ShadowFormUtility
from Widgets.CustomBehaviors.skills.assassin.shroud_of_distress_utility import ShroudOfDistressUtility
from Widgets.CustomBehaviors.skills.botting.move_if_stuck import MoveIfStuckUtility
from Widgets.CustomBehaviors.skills.botting.move_to_distant_chest_if_path_exists import MoveToDistantChestIfPathExistsUtility
from Widgets.CustomBehaviors.skills.botting.resign_if_needed import ResignIfNeededUtility
from Widgets.CustomBehaviors.skills.common.auto_attack_utility import AutoAttackUtility
from Widgets.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import (
    EbonVanguardAssassinSupportUtility,
)
from Widgets.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Widgets.CustomBehaviors.skills.deamon.map_changed import MapChangedUtility
from Widgets.CustomBehaviors.skills.deamon.stuck_detection import StuckDetectionUtility
from Widgets.CustomBehaviors.skills.generic.hero_ai_utility import HeroAiUtility
from Widgets.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Widgets.CustomBehaviors.skills.generic.protective_shout_utility import ProtectiveShoutUtility
from Widgets.CustomBehaviors.skills.looting.open_near_chest_utility import OpenNearChestUtility
from Widgets.CustomBehaviors.skills.paragon.heroic_refrain_utility import HeroicRefrainUtility


class AssassinTankUtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        #core
        self.deadly_paradox_utility: CustomSkillUtilityBase = DeadlyParadoxUtility(score_definition=ScoreStaticDefinition(70), current_build=in_game_build, mana_required_to_cast=0, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.shroud_of_distress_utility: CustomSkillUtilityBase = ShroudOfDistressUtility(score_definition=ScoreStaticDefinition(66), current_build=in_game_build, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO])
        self.shadow_form_utility: CustomSkillUtilityBase = ShadowFormUtility(score_definition=ScoreStaticDefinition(65), is_deadly_paradox_required=True, current_build=in_game_build, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])

    
        #optional
        self.silver_armor_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Sliver_Armor"), current_build=in_game_build, score_definition=ScoreStaticDefinition(61), mana_required_to_cast=0, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.stoneflesh_aura_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Stoneflesh_Aura"), current_build=in_game_build, score_definition=ScoreStaticDefinition(60), mana_required_to_cast=0, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.armor_of_earth_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Armor_of_Earth"), current_build=in_game_build, score_definition=ScoreStaticDefinition(58), mana_required_to_cast=0, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.disrupting_dagger_utility: CustomSkillUtilityBase = DisruptingDaggerUtility(score_definition=ScoreStaticDefinition(90), current_build=in_game_build)
        self.critical_agility_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Critical_Agility"), current_build=in_game_build, score_definition=ScoreStaticDefinition(50), mana_required_to_cast=10, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.critical_eye_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(skill=CustomSkill("Critical_Eye"), current_build=in_game_build, score_definition=ScoreStaticDefinition(80), allowed_states=[BehaviorState.IN_AGGRO])

        self.jagged_strike_utility: CustomSkillUtilityBase = HeroAiUtility(skill=CustomSkill("Jagged_Strike"), current_build=in_game_build, score_definition=ScoreStaticDefinition(40), mana_required_to_cast=15)
        self.fox_fangs_utility: CustomSkillUtilityBase = HeroAiUtility(skill=CustomSkill("Fox_Fangs"), current_build=in_game_build, score_definition=ScoreStaticDefinition(40), mana_required_to_cast=15)
        self.death_blossom_utility: CustomSkillUtilityBase = HeroAiUtility(skill=CustomSkill("Death_Blossom"), current_build=in_game_build, score_definition=ScoreStaticDefinition(40), mana_required_to_cast=15)


        #common
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(current_build=in_game_build, score_definition=ScoreStaticDefinition(45))
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(score_definition=ScoreStaticDefinition(40), current_build=in_game_build, mana_required_to_cast=24)

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
            self.disrupting_dagger_utility,
            self.critical_eye_utility,
            self.jagged_strike_utility,
            self.fox_fangs_utility,
            self.death_blossom_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.shadow_form_utility.custom_skill,
            self.deadly_paradox_utility.custom_skill,
        ]
