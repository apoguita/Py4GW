from typing import override
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_combot_definition import ScoreCombotDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skillbars.disabilities.condition_priority import ConditionPriority
from Sources.oazix.CustomBehaviors.primitives.skillbars.disabilities.disability_priority import DisabilityPriority
from Sources.oazix.CustomBehaviors.primitives.skillbars.disabilities.hex_prioritiy import HexPriority
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.assassin.deadly_paradox_utility import DeadlyParadoxUtility
from Sources.oazix.CustomBehaviors.skills.assassin.disrupting_dagger_utility import DisruptingDaggerUtility
from Sources.oazix.CustomBehaviors.skills.assassin.shadow_form_utility import ShadowFormUtility
from Sources.oazix.CustomBehaviors.skills.assassin.shroud_of_distress_utility import ShroudOfDistressUtility
from Sources.oazix.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_combot_attack_utility import RawCombotAttackUtility

class AssassinTank_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus)
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        #core
        self.deadly_paradox_utility: CustomSkillUtilityBase = DeadlyParadoxUtility(event_bus=self.event_bus, score_definition=ScoreStaticDefinition(70), current_build=in_game_build, mana_required_to_cast=0, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.shroud_of_distress_utility: CustomSkillUtilityBase = ShroudOfDistressUtility(event_bus=self.event_bus, score_definition=ScoreStaticDefinition(66), current_build=in_game_build, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO])
        self.shadow_form_utility: CustomSkillUtilityBase = ShadowFormUtility(event_bus=self.event_bus, score_definition=ScoreStaticDefinition(65), is_deadly_paradox_required=True, current_build=in_game_build, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])


        #optional
        self.silver_armor_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Sliver_Armor"), current_build=in_game_build, score_definition=ScoreStaticDefinition(61), mana_required_to_cast=0, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.stoneflesh_aura_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Stoneflesh_Aura"), current_build=in_game_build, score_definition=ScoreStaticDefinition(60), mana_required_to_cast=0, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.armor_of_earth_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Armor_of_Earth"), current_build=in_game_build, score_definition=ScoreStaticDefinition(58), mana_required_to_cast=0, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.disrupting_dagger_utility: CustomSkillUtilityBase = DisruptingDaggerUtility(event_bus=self.event_bus, score_definition=ScoreStaticDefinition(90), current_build=in_game_build)
        self.critical_agility_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Critical_Agility"), current_build=in_game_build, score_definition=ScoreStaticDefinition(50), mana_required_to_cast=10, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.critical_eye_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Critical_Eye"), current_build=in_game_build, score_definition=ScoreStaticDefinition(80), allowed_states=[BehaviorState.IN_AGGRO])

        self.jagged_strike_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Jagged_Strike"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=15)
        self.fox_fangs_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Fox_Fangs"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=15)
        self.death_blossom_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Death_Blossom"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=15)

        #common
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(event_bus=self.event_bus, score_definition=ScoreStaticDefinition(40), current_build=in_game_build, mana_required_to_cast=24)

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.shroud_of_distress_utility,
            self.deadly_paradox_utility,
            self.shadow_form_utility,
            self.armor_of_earth_utility,
            self.critical_agility_utility,
            self.ebon_vanguard_assassin_support,
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
    
    @override
    def hexes_to_dispell_extra_priority(self) -> list[HexPriority]:
        return [
            HexPriority(CustomSkill("Deep_Freeze"), DisabilityPriority.HIGH),
            HexPriority(CustomSkill("Mind_Freeze"), DisabilityPriority.HIGH),
        ]
    
    @override
    def conditions_to_dispell_extra_priority(self) -> list[ConditionPriority]:
        return [
            ConditionPriority(CustomSkill("Blind"), DisabilityPriority.HIGH),
            ConditionPriority(CustomSkill("Crippled"), DisabilityPriority.HIGH),
        ]
