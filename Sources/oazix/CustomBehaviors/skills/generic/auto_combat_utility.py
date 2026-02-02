from typing import Any, Generator, override

import PyImGui

from HeroAI.types import Skilltarget, SkillNature, SkillType
from Py4GWCoreLib.SkillManager import SkillManager
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus

class AutoCombatUtility(CustomSkillUtilityBase):

    def __init__(
            self,
            event_bus: EventBus,
            skill: CustomSkill,
            current_build: list[CustomSkill],
            score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.GENERIC_SKILL_HERO_AI.value),
            mana_required_to_cast: int = 0
        ) -> None:

            super().__init__(
                event_bus=event_bus,
                skill=skill,
                in_game_build=current_build,
                score_definition=ScoreStaticDefinition(CommonScore.GENERIC_SKILL_HERO_AI.value),
                mana_required_to_cast=mana_required_to_cast,
                allowed_states= [BehaviorState.IN_AGGRO, BehaviorState.FAR_FROM_AGGRO, BehaviorState.CLOSE_TO_AGGRO])

            self.score_definition: ScoreStaticDefinition = score_definition
            self._autocombat: SkillManager.Autocombat = SkillManager.Autocombat()

    def _get_combat_handler(self) -> SkillManager.Autocombat:
        """Get the autocombat instance, initializing skills if needed."""
        if self._autocombat.skills is None or len(self._autocombat.skills) == 0:
            self._autocombat.PrioritizeSkills()
        return self._autocombat

    def find_order(self) -> int:
        autocombat = self._get_combat_handler()
        for index, generic_skill in enumerate(autocombat.skills):
            if generic_skill.skill_id == self.custom_skill.skill_id:
                return index
        return -1  # Return -1 if skill_id not found

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        autocombat = self._get_combat_handler()

        if autocombat.skills is None or len(autocombat.skills) == 0:
            print("autocombat.skills is None or empty")
            return None

        order = self.find_order()
        if order == -1: return None

        is_out_of_combat_skill = autocombat.IsOOCSkill(order)  # skill is OK to be cast out_of_combat

        can_be_casted = ((current_state == BehaviorState.IN_AGGRO)
                        or (current_state == BehaviorState.CLOSE_TO_AGGRO and is_out_of_combat_skill)
                        or (current_state == BehaviorState.FAR_FROM_AGGRO and is_out_of_combat_skill)
                        )

        if not can_be_casted: return None

        is_ready_to_cast, target_agent_id = autocombat.IsReadyToCast(order)

        if not is_ready_to_cast: return None
        score = self.score_definition.get_score() + ((8 - order) * 0.01)  # prioritize skills based on order
        return score

    def _get_target_for_skill(self) -> int | None:
        """Get the appropriate target for this skill from autocombat."""
        autocombat = self._get_combat_handler()
        order = self.find_order()
        if order == -1:
            return None
        is_ready, target_agent_id = autocombat.IsReadyToCast(order)
        return target_agent_id if is_ready else None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_lambda(
            self.custom_skill,
            select_target=self._get_target_for_skill
        )
        return result
    
    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        autocombat = self._get_combat_handler()

        if autocombat.skills is None or len(autocombat.skills) == 0:
            PyImGui.text("SkillManager: No skills loaded")
            return

        PyImGui.text(f"SkillManager Autocombat Data")

        order = self.find_order()

        PyImGui.bullet_text(f"PriorityOrder: {order} (-1 if skill_id not found)")

        if order >= 0 and order < len(autocombat.skills):
            skill_data = autocombat.skills[order].custom_skill_data

            # CustomSkill info
            PyImGui.separator()
            PyImGui.text("CustomSkill Data:")
            PyImGui.bullet_text(f"SkillID: {skill_data.SkillID}")
            PyImGui.bullet_text(f"SkillType: {SkillType(skill_data.SkillType).name}")
            PyImGui.bullet_text(f"TargetAllegiance: {Skilltarget(skill_data.TargetAllegiance).name}")
            PyImGui.bullet_text(f"Nature: {SkillNature(skill_data.Nature).name}")

            # CastConditions info
            conditions = skill_data.Conditions
            PyImGui.separator()
            PyImGui.text("CastConditions:")
            PyImGui.bullet_text(f"IsOutOfCombat: {conditions.IsOutOfCombat}")
            PyImGui.bullet_text(f"IsPartyWide: {conditions.IsPartyWide}")
            PyImGui.bullet_text(f"SelfFirst: {conditions.SelfFirst}")
            PyImGui.bullet_text(f"LessLife: {conditions.LessLife}, MoreLife: {conditions.MoreLife}")
            PyImGui.bullet_text(f"EnemiesInRange: {conditions.EnemiesInRange}, AlliesInRange: {conditions.AlliesInRange}")

            # Autocombat evaluation
            PyImGui.separator()
            PyImGui.text("Autocombat Evaluation:")
            is_out_of_combat_skill = autocombat.IsOOCSkill(order)
            PyImGui.bullet_text(f"IsOOCSkill: {is_out_of_combat_skill}")

            appropriate_target_id = autocombat.GetAppropiateTarget(self.custom_skill.skill_slot - 1)
            PyImGui.bullet_text(f"GetAppropiateTarget AgentId: {appropriate_target_id}")

            are_cast_conditions_met = autocombat.AreCastConditionsMet(self.custom_skill.skill_slot - 1, appropriate_target_id)
            PyImGui.bullet_text(f"AreCastConditionsMet: {are_cast_conditions_met}")

            is_ready_to_cast, target_agent_id = autocombat.IsReadyToCast(order)
            PyImGui.bullet_text(f"IsReadyToCast: {is_ready_to_cast} on AgentId:{target_agent_id}")

            can_be_casted = ((current_state == BehaviorState.IN_AGGRO)
                            or (current_state == BehaviorState.CLOSE_TO_AGGRO and is_out_of_combat_skill)
                            or (current_state == BehaviorState.FAR_FROM_AGGRO and is_out_of_combat_skill)
                            )
            PyImGui.bullet_text(f"IsCurrentBehaviorStateAllowCast: {can_be_casted}")

