from typing import override

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import ScorePerAgentQuantityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.common.great_dwarf_weapon_utility import GreatDwarfWeaponUtility
from Sources.oazix.CustomBehaviors.skills.generic.keep_self_effect_up_utility import KeepSelfEffectUpUtility
from Sources.oazix.CustomBehaviors.skills.generic.raw_simple_party_heal_utility import RawSimplePartyHealUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.arcane_conundrum_utility import ArcaneConundrumUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.auspicious_incantation_utility import AuspiciousIncantationUtility
from Sources.oazix.CustomBehaviors.skills.mesmer.shatter_hex_utility import ShatterHexUtility
from Sources.oazix.CustomBehaviors.skills.monk.judges_insight_utility import JudgesInsightUtility
from Sources.oazix.CustomBehaviors.skills.monk.strength_of_honor_utility import StrengthOfHonorUtility


class MesmerSignetOfIllusions_UtilitySkillBar(CustomBehaviorBaseUtility):

    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus)
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        # Core: maintain Signet of Illusions.
        # Set renew threshold to -1 so we only refresh when the effect is actually gone
        # (important because this signet does not expire by time and recasting resets charges).
        self.signet_of_illusions_utility: CustomSkillUtilityBase = KeepSelfEffectUpUtility(event_bus=self.event_bus, skill=CustomSkill("Signet_of_Illusions"), current_build=in_game_build, score_definition=ScoreStaticDefinition(97), renew_before_expiration_in_milliseconds=-1, allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO, BehaviorState.IDLE])

        self.shatter_hex_utility: CustomSkillUtilityBase = ShatterHexUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 92 if enemy_qte >= 2 else 55))
        self.great_dwarf_weapon_utility: CustomSkillUtilityBase = GreatDwarfWeaponUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(84))
        self.judges_insight_utility: CustomSkillUtilityBase = JudgesInsightUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(83))
        self.strength_of_honor_utility: CustomSkillUtilityBase = StrengthOfHonorUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScoreStaticDefinition(82))
        self.arcane_conundrum_utility: CustomSkillUtilityBase = ArcaneConundrumUtility(event_bus=self.event_bus, current_build=in_game_build, score_definition=ScorePerAgentQuantityDefinition(lambda enemy_qte: 84 if enemy_qte >= 2 else 48))

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        return [
            self.signet_of_illusions_utility,
            self.shatter_hex_utility,
            self.great_dwarf_weapon_utility,
            self.judges_insight_utility,
            self.strength_of_honor_utility,
            self.arcane_conundrum_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        return [
            self.signet_of_illusions_utility.custom_skill,
            self.judges_insight_utility.custom_skill,
        ]
