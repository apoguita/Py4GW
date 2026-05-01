from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Builds.Skills._whiteboard import coordinates_whiteboard_skill_target
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["ChannelingMagic"]


class ChannelingMagic:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build
        self._recent_drains: dict[int, float] = {}

    #region A
    def Armor_of_Unfeeling(self) -> BuildCoroutine:
        """Cast Armor of Unfeeling on the lowest-health owned SoS-build
        spirit when at least 3 of the build's spirits (Anger, Hate,
        Suffering, Bloodsong, Vampirism) are alive.
        """
        from Py4GWCoreLib import Agent, AgentArray, Player, Range, SpiritModelID

        armor_of_unfeeling_id: int = Skill.GetID("Armor_of_Unfeeling")

        if not self.build.IsSkillEquipped(armor_of_unfeeling_id):
            return False

        build_spirit_models = {
            SpiritModelID.ANGER,
            SpiritModelID.HATE,
            SpiritModelID.SUFFERING,
            SpiritModelID.BLOODSONG,
            SpiritModelID.VAMPIRISM,
        }
        self_agent_id = self.build._resolve_self_agent_id()
        spirits = AgentArray.GetSpiritPetArray()
        spirits = AgentArray.Filter.ByDistance(spirits, Player.GetXY(), Range.Spellcast.value)

        def _is_owned_build_spirit(spirit_id: int) -> bool:
            if not (Agent.IsAlive(spirit_id) and Agent.IsSpawned(spirit_id)):
                return False
            if Agent.GetOwnerID(spirit_id) != self_agent_id:
                return False
            model_value = Agent.GetPlayerNumber(spirit_id)
            if model_value not in SpiritModelID._value2member_map_:
                return False
            return SpiritModelID(model_value) in build_spirit_models

        matching_spirits = [s for s in spirits if _is_owned_build_spirit(s)]
        if len(matching_spirits) < 3:
            return False

        sorted_spirits = AgentArray.Sort.ByHealth(matching_spirits)
        target_agent_id = sorted_spirits[0] if sorted_spirits else 0
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=armor_of_unfeeling_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region B
    def Bloodsong(self) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, AgentArray, Player, Range, SpiritModelID

        bloodsong_id: int = Skill.GetID("Bloodsong")

        if not self.build.IsSkillEquipped(bloodsong_id):
            return False
        if not self.build.IsInAggro():
            return False

        # Skip if an owned Bloodsong spirit already exists.
        self_agent_id = self.build._resolve_self_agent_id()
        spirits = AgentArray.GetSpiritPetArray()
        spirits = AgentArray.Filter.ByDistance(spirits, Player.GetXY(), Range.Compass.value)
        if any(
            Agent.IsAlive(spirit_id)
            and Agent.IsSpawned(spirit_id)
            and Agent.GetOwnerID(spirit_id) == self_agent_id
            and Agent.GetPlayerNumber(spirit_id) == SpiritModelID.BLOODSONG.value
            for spirit_id in spirits
        ):
            return False

        return (yield from self.build.CastSpiritSkillID(
            skill_id=bloodsong_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region P
    @coordinates_whiteboard_skill_target(Skill.GetID("Painful_Bond"))
    def Painful_Bond(self) -> BuildCoroutine:
        from Py4GWCoreLib import Range, GLOBAL_CACHE

        painful_bond_id: int = Skill.GetID("Painful_Bond")

        if not self.build.IsSkillEquipped(painful_bond_id):
            return False
        if not self.build.IsInAggro():
            return False

        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(painful_bond_id) or Range.Nearby.value

        target_agent_id = self.build._pick_clustered_target(
            cluster_radius=aoe_range,
            filter_radius=Range.Spellcast.value,
        )
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=painful_bond_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region S
    def Spirit_Siphon(
        self,
        *,
        max_self_energy_pct: float | None = None,
        drain_cooldown_s: float = 16.0,
    ) -> BuildCoroutine:
        """Drain the nearest spirit's energy, gaining a percentage of it.

        Optional ``max_self_energy_pct`` skips the cast when the caster's
        energy fraction is at or above the threshold (mirrors the
        Signet_of_Lost_Souls pattern).

        ``drain_cooldown_s`` skips the cast when the nearest owned spirit
        was drained within this many seconds — Spirit Siphon empties the
        target's entire energy pool, so re-targeting the same spirit too
        soon yields near-zero gain. The cooldown is per-spirit, so
        cycling between multiple owned spirits (e.g. by movement) drains
        each independently.
        """
        import time
        from Py4GWCoreLib import Agent, AgentArray, Player, Range, Utils

        spirit_siphon_id: int = Skill.GetID("Spirit_Siphon")

        if not self.build.IsSkillEquipped(spirit_siphon_id):
            return False
        if not (self.build.IsInAggro() or self.build.IsCloseToAggro()):
            return False

        if max_self_energy_pct is not None:
            if Agent.GetEnergy(Player.GetAgentID()) >= max_self_energy_pct:
                return False

        self_agent_id = self.build._resolve_self_agent_id()
        player_xy = Player.GetXY()

        owned_spirits = AgentArray.GetSpiritPetArray()
        owned_spirits = AgentArray.Filter.ByDistance(owned_spirits, player_xy, Range.Spellcast.value)
        owned_spirits = AgentArray.Filter.ByCondition(
            owned_spirits,
            lambda agent_id: (
                Agent.IsAlive(agent_id)
                and Agent.GetOwnerID(agent_id) == self_agent_id
            ),
        )
        if not owned_spirits:
            return False

        # Spirit Siphon auto-targets the nearest spirit at the engine
        # level. Pre-compute the nearest owned spirit client-side so we
        # can gate against recent drains.
        nearest_spirit_id = min(
            owned_spirits,
            key=lambda s: Utils.Distance(player_xy, Agent.GetXY(s)),
        )
        now = time.monotonic()
        last_drained_at = self._recent_drains.get(nearest_spirit_id, 0.0)
        if now - last_drained_at < drain_cooldown_s:
            return False

        result = (yield from self.build.CastSkillID(
            skill_id=spirit_siphon_id,
            log=False,
            aftercast_delay=250,
        ))
        if result:
            self._recent_drains[nearest_spirit_id] = now
        return result

    def Signet_of_Spirits(self) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, AgentArray, Player, Range, SpiritModelID

        sos_id: int = Skill.GetID("Signet_of_Spirits")

        if not self.build.IsSkillEquipped(sos_id):
            return False
        if not self.build.IsInAggro():
            return False

        # Skip the recast if 2 or more SoS spirits (Anger, Hate, Suffering)
        # are still alive. Cast only when 1 or fewer remain.
        sos_spirit_models = {
            SpiritModelID.ANGER,
            SpiritModelID.HATE,
            SpiritModelID.SUFFERING,
        }
        self_agent_id = self.build._resolve_self_agent_id()
        spirits = AgentArray.GetSpiritPetArray()
        spirits = AgentArray.Filter.ByDistance(spirits, Player.GetXY(), Range.Compass.value)

        def _is_owned_sos_spirit(spirit_id: int) -> bool:
            if not (Agent.IsAlive(spirit_id) and Agent.IsSpawned(spirit_id)):
                return False
            if Agent.GetOwnerID(spirit_id) != self_agent_id:
                return False
            model_value = Agent.GetPlayerNumber(spirit_id)
            if model_value not in SpiritModelID._value2member_map_:
                return False
            return SpiritModelID(model_value) in sos_spirit_models

        alive_sos_count = sum(1 for spirit_id in spirits if _is_owned_sos_spirit(spirit_id))
        if alive_sos_count >= 2:
            return False

        return (yield from self.build.CastSkillID(
            skill_id=sos_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
