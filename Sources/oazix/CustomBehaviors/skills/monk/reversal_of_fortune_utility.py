from typing import Any, Generator, override

from Py4GWCoreLib import Range, Agent, Routines
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Sources.oazix.CustomBehaviors.primitives.scores.healing_score import HealingScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import ScorePerHealthGravityDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_multiple_target import CustomBuffMultipleTarget
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_target_per_profession import BuffConfigurationPerProfession
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.skills.monk.spirit_bond_utility import SpiritBondUtility


class Reversal_of_Fortune_SpiritBondUtility(SpiritBondUtility):

    def __init__(self,
        event_bus: EventBus,
        current_build: list[CustomSkill],
        skill: CustomSkill = CustomSkill("Reversal_of_Fortune"),
        score_definition: ScorePerHealthGravityDefinition = ScorePerHealthGravityDefinition(5),
        mana_required_to_cast: int = 5,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=skill,
            current_build=current_build,
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast,
            allowed_states=allowed_states)
