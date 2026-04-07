from typing import cast, override

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_combot_definition import ScoreCombotDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skillbars.disabilities.condition_priority import ConditionPriority
from Sources.oazix.CustomBehaviors.primitives.skillbars.disabilities.disability_priority import DisabilityPriority
from Sources.oazix.CustomBehaviors.primitives.skillbars.disabilities.hex_prioritiy import HexPriority
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.common.ebon_battle_standard_of_wisdom_utility import EbonBattleStandardOfWisdom
from Sources.oazix.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.protective_shout_utility import ProtectiveShoutUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_combot_attack_utility import RawCombotAttackUtility
from Sources.oazix.CustomBehaviors.skills.paragon.blazing_finale_utility import BlazingFinaleUtility
from Sources.oazix.CustomBehaviors.skills.paragon.heroic_refrain_utility import HeroicRefrainUtility
from Sources.oazix.CustomBehaviors.skills.paragon.hasty_refrain_utility import HastyRefrainUtility
from Sources.oazix.CustomBehaviors.skills.paragon.make_your_time_utility import MakeYourTimeUtility
from Sources.oazix.CustomBehaviors.skills.plugins.preconditions.should_wait_for_adrenaline_consumer import ShouldWaitForAdrenalineConsumer
from Sources.oazix.CustomBehaviors.skills.plugins.preconditions.should_wait_for_save_yourselves_finalized_on_allies import ShouldWaitForSaveYourselvesFinalizedOnAllies
from Sources.oazix.CustomBehaviors.skills.warrior.protectors_defense_utility import ProtectorsDefenseUtility
from Sources.oazix.CustomBehaviors.skills.warrior.save_yourselves import SaveYourselvesUtility
from Sources.oazix.CustomBehaviors.skills.warrior.to_the_limit_utility import ToTheLimitUtility


class ParagonRefrain_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus)
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        #core
        self.heroic_refrain_utility: CustomSkillUtilityBase = HeroicRefrainUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(50))
        self.theyre_on_fire_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Theyre_on_Fire"), current_build=in_game_build, score_definition=ScoreStaticDefinition(80), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO])
        self.theres_nothing_to_fear: CustomSkillUtilityBase = ProtectiveShoutUtility(event_bus=self.event_bus, skill=CustomSkill("Theres_Nothing_to_Fear"), current_build=in_game_build, allies_health_less_than_percent=0.9, allies_quantity_required=1,score_definition= ScoreStaticDefinition(90), allowed_states=[BehaviorState.IN_AGGRO])

        # adrenaline consumers
        self.save_yourselves_luxon: CustomSkillUtilityBase = SaveYourselvesUtility(event_bus=self.event_bus, skill=CustomSkill("Save_Yourselves_luxon"), current_build=in_game_build,score_definition=ScoreStaticDefinition(89))
        self.save_yourselves_kurzick: CustomSkillUtilityBase = SaveYourselvesUtility(event_bus=self.event_bus, skill=CustomSkill("Save_Yourselves_kurzick"), current_build=in_game_build, score_definition=ScoreStaticDefinition(89))

        # adrenaline generators
        self.for_great_justice: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("For_Great_Justice"), current_build=in_game_build, score_definition=ScoreStaticDefinition(80), allowed_states=[BehaviorState.IN_AGGRO])
        
        self.to_the_limit = ToTheLimitUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(79), allowed_states=[BehaviorState.IN_AGGRO])
        self.to_the_limit.add_plugin_precondition(lambda x: ShouldWaitForSaveYourselvesFinalizedOnAllies(x.custom_skill, default_value=True))
        self.to_the_limit.add_plugin_precondition(lambda x: ShouldWaitForAdrenalineConsumer(x.custom_skill, generated_strike_of_adrenaline=lambda: cast(ToTheLimitUtility, x).get_generated_strike_of_adrenaline(), adrenaline_consumers=[self.save_yourselves_luxon, self.save_yourselves_kurzick], default_value=True))
        
        self.make_your_time = MakeYourTimeUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(78), allowed_states=[BehaviorState.IN_AGGRO])
        self.make_your_time.add_plugin_precondition(lambda x: ShouldWaitForSaveYourselvesFinalizedOnAllies(x.custom_skill, default_value=True))
        self.make_your_time.add_plugin_precondition(lambda x: ShouldWaitForAdrenalineConsumer(x.custom_skill, generated_strike_of_adrenaline=lambda: cast(MakeYourTimeUtility, x).get_generated_strike_of_adrenaline(), adrenaline_consumers=[self.save_yourselves_luxon, self.save_yourselves_kurzick], default_value=True))

        #optional
        self.hasty_refrain_utility: CustomSkillUtilityBase = HastyRefrainUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(40))
        self.never_surrender: CustomSkillUtilityBase = ProtectiveShoutUtility(event_bus=self.event_bus, skill=CustomSkill("Never_Surrender"), current_build=in_game_build, allies_health_less_than_percent=0.7,allies_quantity_required=2,score_definition=ScoreStaticDefinition(88), allowed_states=[BehaviorState.IN_AGGRO])
        self.blazing_finale_utility: CustomSkillUtilityBase = BlazingFinaleUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(33))

        self.jagged_strike_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Jagged_Strike"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=13)
        self.fox_fangs_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Fox_Fangs"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=13)
        self.death_blossom_utility: CustomSkillUtilityBase = RawCombotAttackUtility(event_bus=self.event_bus, skill=CustomSkill("Death_Blossom"), current_build=in_game_build, score_definition=ScoreCombotDefinition(40), mana_required_to_cast=13)

        #common
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(event_bus=self.event_bus, score_definition=ScoreStaticDefinition(71), current_build=in_game_build, mana_required_to_cast=15)
        self.ebon_battle_standard_of_wisdom: CustomSkillUtilityBase = EbonBattleStandardOfWisdom(event_bus=self.event_bus, score_definition= ScorePerAgentQuantityDefinition(lambda agent_qte: 80 if agent_qte >= 3 else 60 if agent_qte <= 2 else 40), current_build=in_game_build, mana_required_to_cast=18)
        self.protectors_defense_utility: CustomSkillUtilityBase = ProtectorsDefenseUtility(event_bus=self.event_bus, current_build=in_game_build,score_definition=ScoreStaticDefinition(60))

    
    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.hasty_refrain_utility,
            self.heroic_refrain_utility,
            self.theyre_on_fire_utility,
            self.theres_nothing_to_fear,
            self.save_yourselves_luxon,
            self.save_yourselves_kurzick,
            self.never_surrender,
            self.blazing_finale_utility,
            self.for_great_justice,
            self.to_the_limit,
            self.make_your_time,

            self.jagged_strike_utility,
            self.fox_fangs_utility,
            self.death_blossom_utility,

            self.ebon_vanguard_assassin_support,
            self.ebon_battle_standard_of_wisdom,
            self.protectors_defense_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.heroic_refrain_utility.custom_skill,
            self.theyre_on_fire_utility.custom_skill,
        ]
    
    @override
    def hexes_to_dispell_extra_priority(self) -> list[HexPriority]:
        return [
            HexPriority(CustomSkill("Vocal_Minority"), DisabilityPriority.VERY_HIGH), # paragon shouts are most important for the party
            HexPriority(CustomSkill("Soothing_Images"), DisabilityPriority.VERY_HIGH), # paragon adrenaline generator is most important for the party
        ]

    @override
    def conditions_to_dispell_extra_priority(self) -> list[ConditionPriority]:
        return [
            ConditionPriority(CustomSkill("Blind"), DisabilityPriority.VERY_HIGH), # paragon adrenaline generator is most important for the party
        ]