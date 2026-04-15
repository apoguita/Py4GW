from typing import override

from Py4GWCoreLib.enums import SpiritModelID
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.common.by_urals_hammer_utility import ByUralsHammerUtility
from Sources.oazix.CustomBehaviors.skills.common.ebon_vanguard_assassin_support_utility import EbonVanguardAssassinSupportUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_spirit_utility import RawSpiritUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.life_utility import LifeUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.mend_body_and_soul_utility import MendBodyAndSoulUtility
from Sources.oazix.CustomBehaviors.skills.ritualist.spirit_light_utility import SpiritLightUtility


class RitualistSpiritChanneling_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus)
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # core skills
        self.spirit_channeling_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Spirit_Channeling"), current_build=in_game_build, score_definition=ScoreStaticDefinition(90), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.spirit_light_utility: CustomSkillUtilityBase = SpiritLightUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(8))
        self.mend_body_and_soul_utility: CustomSkillUtilityBase = MendBodyAndSoulUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(7))
        self.life_utility: CustomSkillUtilityBase = LifeUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerHealthGravityDefinition(5))
        self.rejuvenation_utility: CustomSkillUtilityBase = RawSpiritUtility(event_bus=self.event_bus, skill=CustomSkill("Rejuvenation"), current_build=in_game_build, owned_spirit_model_id=SpiritModelID.REJUVENATION, score_definition=ScoreStaticDefinition(82), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])
        self.recovery_utility: CustomSkillUtilityBase = RawSpiritUtility(event_bus=self.event_bus, skill=CustomSkill("Recovery"), current_build=in_game_build, owned_spirit_model_id=SpiritModelID.RECOVERY, score_definition=ScoreStaticDefinition(82), allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO])

        # pve skills
        self.ebon_vanguard_assassin_support: CustomSkillUtilityBase = EbonVanguardAssassinSupportUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(71), mana_required_to_cast=15)

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.spirit_channeling_utility,
            self.spirit_light_utility,
            self.mend_body_and_soul_utility,
            self.life_utility,
            self.rejuvenation_utility,
            self.recovery_utility,
            self.ebon_vanguard_assassin_support,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.spirit_channeling_utility.custom_skill,
            self.spirit_light_utility.custom_skill,
            self.mend_body_and_soul_utility.custom_skill,
        ]
