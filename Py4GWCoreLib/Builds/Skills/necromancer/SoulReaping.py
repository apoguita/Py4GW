from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import AgentArray, GLOBAL_CACHE, Range, Routines, Utils
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["SoulReaping"]


class SoulReaping:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region F
    def Foul_Feast(self) -> BuildCoroutine:
        foul_feast_id: int = Skill.GetID("Foul_Feast")
        foul_feast: CustomSkill = self.build.GetCustomSkill(foul_feast_id)

        if not self.build.IsSkillEquipped(foul_feast_id):
            return False

        target_agent_id = self.build.ResolveAllyTarget(
            foul_feast_id,
            foul_feast,
        )
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=foul_feast_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region M
    def Masochism(self, assume_active_ms: int = 25000) -> BuildCoroutine:
        masochism_id: int = Skill.GetID("Masochism")

        if not self.build.IsSkillEquipped(masochism_id):
            return False

        # Aggro gate: only cast when in aggro or close to aggro
        if not (self.build.IsInAggro() or self.build.IsCloseToAggro()):
            return False

        player_agent_id = Player.GetAgentID()
        now_ms = int(Utils.GetBaseTimestamp())
        assumed_effects = getattr(self.build, "_self_effect_assumed_until", {})

        if int(assumed_effects.get(masochism_id, 0) or 0) > now_ms:
            return False

        # Refresh window: skip when Masochism is already up with more than
        # 2 seconds remaining. Cast otherwise — initial application when
        # the effect is gone, or refresh inside the last 2-second window.
        if Routines.Checks.Agents.HasEffect(player_agent_id, masochism_id):
            remaining_ms = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(
                player_agent_id, masochism_id
            )
            if remaining_ms > 2000:
                assumed_effects.pop(masochism_id, None)
                return False

        cast_result = yield from self.build.CastSkillID(
            skill_id=masochism_id,
            log=False,
            aftercast_delay=250,
        )
        if cast_result:
            assumed_effects[masochism_id] = now_ms + max(0, int(assume_active_ms))
            setattr(self.build, "_self_effect_assumed_until", assumed_effects)
            return True

        return False
    #endregion

    #region S
    def Soul_Taker(self, refresh_window_ms: int = 2000) -> BuildCoroutine:
        soul_taker_id: int = Skill.GetID("Soul_Taker")
        player_agent_id = Player.GetAgentID()

        if not self.build.IsSkillEquipped(soul_taker_id):
            return False
        if not (self.build.IsInAggro() or self.build.IsCloseToAggro()):
            return False
        if Routines.Checks.Agents.HasEffect(player_agent_id, soul_taker_id):
            remaining_ms = int(GLOBAL_CACHE.Effects.GetEffectTimeRemaining(
                player_agent_id,
                soul_taker_id,
            ) or 0)
            if remaining_ms > refresh_window_ms:
                return False

        return (yield from self.build.CastSkillID(
            skill_id=soul_taker_id,
            log=False,
            aftercast_delay=250,
        ))

    def Signet_of_Lost_Souls(
        self,
        *,
        max_self_energy_pct: float | None = None,
    ) -> BuildCoroutine:
        from Py4GWCoreLib import Utils

        signet_of_lost_souls_id: int = Skill.GetID("Signet_of_Lost_Souls")

        if not self.build.IsSkillEquipped(signet_of_lost_souls_id):
            return False

        # Optional caster-energy gate. When set, fire only if the caster's energy
        # fraction is strictly below the threshold. When None (default) there is
        # no caster-side gate - the signet is free HP/energy whenever an eligible
        # target exists, so the caller's chain position bounds when it fires.
        if max_self_energy_pct is not None:
            if Agent.GetEnergy(Player.GetAgentID()) >= max_self_energy_pct:
                return False

        # Target filter: enemy within Spellcast range, alive, below the signet's
        # 50% trigger threshold. Sort closest-first with lower HP as tiebreak so
        # the target is both reliable (unlikely to slip out of range during the
        # 1/4s cast) and likely to still be <50% when the signet resolves.
        player_pos = Player.GetXY()
        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByDistance(enemy_array, player_pos, Range.Spellcast.value)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsAlive(agent_id))
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.GetHealth(agent_id) < 0.5)
        if not enemy_array:
            return False

        target_agent_id = sorted(
            enemy_array,
            key=lambda aid: (Utils.Distance(player_pos, Agent.GetXY(aid)), Agent.GetHealth(aid)),
        )[0]

        return (yield from self.build.CastSkillID(
            skill_id=signet_of_lost_souls_id,
            log=False,
            aftercast_delay=250,
            target_agent_id=target_agent_id,
        ))
    #endregion
