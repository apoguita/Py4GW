from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import AgentArray, Range, Routines, Utils
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.GlobalCache.HexRemovalPriority import HexRemovalPriority, cast_hex_removal_and_track, get_hexed_ally_for_removal
from HeroAI.targeting import GetAllAlliesArray
from HeroAI.types import Skilltarget

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["NoAttribute"]

class NoAttribute:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build


    #region R
    def Remove_Hex(self, min_priority: int = HexRemovalPriority.LOW) -> BuildCoroutine:
        remove_hex_id: int = Skill.GetID("Remove_Hex")

        if not self.build.IsSkillEquipped(remove_hex_id):
            return False

        target_agent_id = get_hexed_ally_for_removal(
            Range.Spellcast.value,
            reserve=True,
            skill_id=remove_hex_id,
            min_priority=min_priority,
        )
        if not target_agent_id:
            return False

        return (yield from cast_hex_removal_and_track(
            self.build,
            skill_id=remove_hex_id,
            target_agent_id=target_agent_id,
            aftercast_delay=250,
        ))
    #endregion

    #region S
    def Seed_of_Life(self) -> BuildCoroutine:
        seed_of_life_id: int = Skill.GetID("Seed_of_Life")
        seed_of_life: CustomSkill = self.build.GetCustomSkill(seed_of_life_id)
        health_threshold: float = max(0.0, min(1.0, float(seed_of_life.Conditions.LessLife or 0.80)))

        def _is_valid_seed_target(agent_id: int) -> bool:
            return (
                Agent.IsAlive(agent_id)
                and agent_id != Player.GetAgentID()
                and Agent.GetHealth(agent_id) <= health_threshold
            )

        def _resolve_seed_of_life_target() -> int:
            return self.build.ResolvePreferredPartySpikeAllyTarget(
                seed_of_life_id,
                seed_of_life,
                variants=[
                    lambda custom_skill: setattr(custom_skill, "TargetAllegiance", Skilltarget.AllyMartialMelee.value),
                    lambda custom_skill: setattr(custom_skill, "TargetAllegiance", Skilltarget.AllyMartial.value),
                    None,
                ],
                validator=_is_valid_seed_target,
                drop_threshold=0.08,
                sample_interval_ms=150,
                window_ms=1000,
            )

        if not self.build.IsSkillEquipped(seed_of_life_id):
            return False

        target_agent_id = _resolve_seed_of_life_target()
        return (yield from self.build.CastSkillIDAndRestoreTarget(
            seed_of_life_id,
            target_agent_id,
        ))
