from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import AgentArray, Range, Routines
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill
from HeroAI.targeting import GetAllAlliesArray

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["ProtectionPrayers"]


class ProtectionPrayers:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region D
    def Draw_Conditions(self) -> BuildCoroutine:
        draw_conditions_id: int = Skill.GetID("Draw_Conditions")
        draw_conditions: CustomSkill = self.build.GetCustomSkill(draw_conditions_id)

        def _resolve_draw_conditions_target() -> int:
            return self.build.ResolveAllyTarget(
                draw_conditions_id,
                draw_conditions,
            )

        if not self.build.IsSkillEquipped(draw_conditions_id):
            return False

        target_agent_id = _resolve_draw_conditions_target()
        return (yield from self.build.CastSkillIDAndRestoreTarget(
            draw_conditions_id,
            target_agent_id,
        ))
    #endregion

    #region P
    def Protective_Spirit(self) -> BuildCoroutine:
        protective_spirit_id: int = Skill.GetID("Protective_Spirit")
        protective_spirit: CustomSkill = self.build.GetCustomSkill(protective_spirit_id)
        sample_interval_ms = 500
        focused_drop_threshold = 0.10

        def _resolve_protective_spirit_target() -> int:
            ally_array: list[int] = list(GetAllAlliesArray(Range.Spellcast.value) or [])
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.IsAlive(agent_id),
            )
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.GetHealth(agent_id) < protective_spirit.Conditions.LessLife,
            )
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: not Routines.Checks.Effects.HasBuff(agent_id, protective_spirit_id),
            )

            best_target = 0
            best_drop = focused_drop_threshold
            best_health = 1.0
            for agent_id in ally_array:
                if not self.build.IsPartySpikeTarget(
                    agent_id,
                    drop_threshold=focused_drop_threshold,
                    sample_interval_ms=sample_interval_ms,
                ):
                    continue
                sampled_drop = self.build.GetPartyHealthDelta(agent_id)
                current_health = float(Agent.GetHealth(agent_id))
                if sampled_drop > best_drop or (sampled_drop == best_drop and current_health < best_health):
                    best_target = agent_id
                    best_drop = sampled_drop
                    best_health = current_health

            return best_target

        if not self.build.IsSkillEquipped(protective_spirit_id):
            return False
        if not Routines.Checks.Agents.InAggro():
            return False

        target_agent_id = _resolve_protective_spirit_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            protective_spirit_id,
            target_agent_id,
        ))
    #endregion

    def Reversal_of_Fortune(self) -> BuildCoroutine:
        reversal_of_fortune_id: int = Skill.GetID("Reversal_of_Fortune")
        reversal_of_fortune: CustomSkill = self.build.GetCustomSkill(reversal_of_fortune_id)
        sample_interval_ms = 500
        focused_drop_threshold = 0.05

        def _resolve_reversal_of_fortune_target() -> int:
            ally_array: list[int] = list(GetAllAlliesArray(Range.Spellcast.value) or [])
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.IsAlive(agent_id),
            )
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: Agent.GetHealth(agent_id) < reversal_of_fortune.Conditions.LessLife,
            )
            ally_array = AgentArray.Filter.ByCondition(
                ally_array,
                lambda agent_id: not Routines.Checks.Effects.HasBuff(agent_id, reversal_of_fortune_id),
            )

            def _priority(agent_id: int) -> tuple[int, int, float, float]:
                is_spiking = self.build.IsPartySpikeTarget(
                    agent_id,
                    drop_threshold=focused_drop_threshold,
                    sample_interval_ms=sample_interval_ms,
                )
                role_rank = 2
                if Agent.IsMelee(agent_id):
                    role_rank = 0
                elif Agent.IsCaster(agent_id):
                    role_rank = 1

                return (
                    0 if is_spiking else 1,
                    role_rank,
                    Agent.GetHealth(agent_id),
                    -self.build.GetPartyHealthDelta(agent_id),
                )

            ally_array.sort(key=_priority)
            return ally_array[0] if ally_array else 0

        if not self.build.IsSkillEquipped(reversal_of_fortune_id):
            return False
        if not Routines.Checks.Agents.InAggro():
            return False

        target_agent_id = _resolve_reversal_of_fortune_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            reversal_of_fortune_id,
            target_agent_id,
        ))
