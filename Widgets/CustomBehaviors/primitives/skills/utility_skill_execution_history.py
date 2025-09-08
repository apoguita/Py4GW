from dataclasses import dataclass
from typing import Optional

from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


@dataclass
class UtilitySkillExecutionHistory:
    skill: CustomSkillUtilityBase
    score: Optional[float]
    result: Optional[BehaviorResult]
    started_at: float
    ended_at: Optional[float]

