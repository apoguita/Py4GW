from typing import override

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.scores.score_combot_definition import ScoreCombotDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.common.auto_attack_utility import AutoAttackUtility
from Sources.oazix.CustomBehaviors.skills.common.by_urals_hammer_utility import ByUralsHammerUtility
from Sources.oazix.CustomBehaviors.skills.common.ebon_battle_standard_of_wisdom_utility import EbonBattleStandardOfWisdom
from Sources.oazix.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Sources.oazix.CustomBehaviors.skills.common.i_am_unstoppable_utility import IAmUnstoppableUtility
from Sources.oazix.CustomBehaviors.skills.generic.generic_resurrection_utility import GenericResurrectionUtility
from Sources.oazix.CustomBehaviors.skills.generic.auto_combat_utility import AutoCombatUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.protective_shout_utility import ProtectiveShoutUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_combot_attack_utility import RawCombotAttackUtility
from Sources.oazix.CustomBehaviors.skills.paragon.blazing_finale_utility import BlazingFinaleUtility
from Sources.oazix.CustomBehaviors.skills.paragon.fall_back_utility import FallBackUtility
from Sources.oazix.CustomBehaviors.skills.paragon.heroic_refrain_utility import HeroicRefrainUtility
from Sources.oazix.CustomBehaviors.skills.paragon.holy_spear_utility import HolySpearUtility
from Sources.oazix.CustomBehaviors.skills.warrior.protectors_defense_utility import ProtectorsDefenseUtility


class ParagonRefrain_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        #core
        self.heroic_refrain_utility: CustomSkillUtilityBase = HeroicRefrainUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(50))
        self.theyre_on_fire_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Theyre_on_Fire"), current_build=in_game_build, score_definition=ScoreStaticDefinition(80), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO])

        #optional
        self.theres_nothing_to_fear: CustomSkillUtilityBase = ProtectiveShoutUtility(event_bus=self.event_bus, skill=CustomSkill("Theres_Nothing_to_Fear"), current_build=in_game_build, allies_health_less_than_percent=0.9, allies_quantity_required=1,score_definition= ScoreStaticDefinition(90), allowed_states=[BehaviorState.IN_AGGRO])
        self.save_yourselves_luxon: CustomSkillUtilityBase = ProtectiveShoutUtility(event_bus=self.event_bus, skill=CustomSkill("Save_Yourselves_luxon"), current_build=in_game_build, allies_health_less_than_percent=0.7, allies_quantity_required=1,score_definition=ScoreStaticDefinition(89), allowed_states=[BehaviorState.IN_AGGRO])
        self.save_yourselves_kurzick: CustomSkillUtilityBase = ProtectiveShoutUtility(event_bus=self.event_bus, skill=CustomSkill("Save_Yourselves_kurzick"), current_build=in_game_build, allies_health_less_than_percent=0.7, allies_quantity_required=1,score_definition=ScoreStaticDefinition(89), allowed_states=[BehaviorState.IN_AGGRO])
        self.never_surrender: CustomSkillUtilityBase = ProtectiveShoutUtility(event_bus=self.event_bus, skill=CustomSkill("Never_Surrender"), current_build=in_game_build, allies_health_less_than_percent=0.7,allies_quantity_required=2,score_definition=ScoreStaticDefinition(88), allowed_states=[BehaviorState.IN_AGGRO])

        self.blazing_finale_utility: CustomSkillUtilityBase = BlazingFinaleUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(33))
        self.holy_spear_utility: CustomSkillUtilityBase = HolySpearUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 70 if enemy_qte >= 2 else 35 if enemy_qte <= 2 else 0))

        self.jagged_strike_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Jagged_Strike"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=13)
        self.fox_fangs_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Fox_Fangs"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=13)
        self.death_blossom_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Death_Blossom"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=13)

        #common
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(event_bus=self.event_bus, score_definition=ScoreStaticDefinition(71), current_build=in_game_build, mana_required_to_cast=15)
        self.ebon_battle_standard_of_wisdom: CustomSkillUtilityBase = EbonBattleStandardOfWisdom(event_bus=self.event_bus, score_definition= ScorePerAgentQuantityDefinition(lambda agent_qte: 80 if agent_qte >= 3 else 60 if agent_qte <= 2 else 40), current_build=in_game_build, mana_required_to_cast=18)
        self.i_am_unstopabble: CustomSkillUtilityBase = IAmUnstoppableUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(99))
        self.fall_back_utility: CustomSkillUtilityBase = FallBackUtility(event_bus=self.event_bus, current_build=in_game_build)
        self.protectors_defense_utility: CustomSkillUtilityBase = ProtectorsDefenseUtility(event_bus=self.event_bus, current_build=in_game_build,score_definition=ScoreStaticDefinition(60))
        self.signet_of_return_utility: CustomSkillUtilityBase = GenericResurrectionUtility(event_bus=self.event_bus, skill=CustomSkill("Signet_of_Return"), current_build=in_game_build,score_definition=ScoreStaticDefinition(12))
        self.by_urals_hammer_utility: CustomSkillUtilityBase = ByUralsHammerUtility(event_bus=self.event_bus, current_build=in_game_build)

    
    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.heroic_refrain_utility,
            self.theyre_on_fire_utility,
            self.theres_nothing_to_fear,
            self.save_yourselves_luxon,
            self.save_yourselves_kurzick,
            self.never_surrender,
            self.blazing_finale_utility,
            self.holy_spear_utility,

            self.jagged_strike_utility,
            self.fox_fangs_utility,
            self.death_blossom_utility,

            self.ebon_vanguard_assassin_support,
            self.ebon_battle_standard_of_wisdom,
            self.i_am_unstopabble,
            self.fall_back_utility,
            self.protectors_defense_utility,
            self.signet_of_return_utility,
            self.by_urals_hammer_utility,
            self.jagged_strike_utility,
            self.fox_fangs_utility,
            self.death_blossom_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.heroic_refrain_utility.custom_skill,
            self.theyre_on_fire_utility.custom_skill,
        ]