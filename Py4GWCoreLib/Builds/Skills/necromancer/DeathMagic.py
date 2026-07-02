from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import AgentArray, GLOBAL_CACHE, Profession, Range, Routines, Utils
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill
from HeroAI.targeting import TargetMinionNonEnchanted

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["DeathMagic"]


class DeathMagic:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region C
    def Contagion(
        self,
        *,
        prefer_after_skill_id: int | None = None,
        refresh_window_ms: int = 2000,
        assume_active_ms: int = 5000,
    ) -> BuildCoroutine:
        """Maintain Contagion (elite enchantment) on the caster.

        Unlike most combat skills this has no aggro gate: Contagion is kept up
        even out of combat so its condition-mirroring is ready the moment a
        condition lands on the caster.

        ``prefer_after_skill_id`` (Masochism by default) encodes a soft ordering
        preference: while in or close to aggro, if that skill is equipped but not
        yet active on the caster, Contagion is deferred for this tick so the
        other skill can go up first. Out of aggro the preference is ignored
        (the other skill would not cast there anyway), so upkeep is never
        blocked.
        """
        contagion_id: int = Skill.GetID("Contagion")

        if not self.build.IsSkillEquipped(contagion_id):
            return False

        player_agent_id = Player.GetAgentID()

        # Soft ordering preference: hold Contagion until the preferred skill
        # (Masochism) is active, but only while near aggro where that skill can
        # actually cast. Out of aggro we maintain Contagion regardless.
        if prefer_after_skill_id is None:
            prefer_after_skill_id = Skill.GetID("Masochism")
        if (
            (self.build.IsInAggro() or self.build.IsCloseToAggro())
            and self.build.IsSkillEquipped(prefer_after_skill_id)
            and not Routines.Checks.Agents.HasEffect(player_agent_id, prefer_after_skill_id)
        ):
            return False

        now_ms = int(Utils.GetBaseTimestamp())
        assumed_effects = getattr(self.build, "_self_effect_assumed_until", {})

        # Anti-spam debounce: skip while a recent cast is still assumed active
        # (covers the gap before the effect registers in the cache).
        if int(assumed_effects.get(contagion_id, 0) or 0) > now_ms:
            return False

        # Refresh window: skip when Contagion is already up with more than the
        # refresh window remaining. Cast otherwise — initial application when
        # the effect is gone, or refresh inside the last window.
        if Routines.Checks.Agents.HasEffect(player_agent_id, contagion_id):
            remaining_ms = int(GLOBAL_CACHE.Effects.GetEffectTimeRemaining(
                player_agent_id, contagion_id,
            ) or 0)
            if remaining_ms > refresh_window_ms:
                assumed_effects.pop(contagion_id, None)
                return False

        cast_result = yield from self.build.CastSkillID(
            skill_id=contagion_id,
            log=False,
            aftercast_delay=250,
        )
        if cast_result:
            assumed_effects[contagion_id] = now_ms + max(0, int(assume_active_ms))
            setattr(self.build, "_self_effect_assumed_until", assumed_effects)
            return True

        return False
    #endregion

    #region D
    def Death_Nova(self) -> BuildCoroutine:
        death_nova_id: int = Skill.GetID("Death_Nova")
        death_nova = self.build.GetCustomSkill(death_nova_id)

        if not self.build.IsSkillEquipped(death_nova_id):
            return False

        target_agent_id = TargetMinionNonEnchanted(distance=Range.Spellcast.value)
        if not target_agent_id:
            return False

        max_health_threshold = float(death_nova.Conditions.LessLife or 1.0) if death_nova is not None else 1.0
        if Agent.GetHealth(target_agent_id) > max_health_threshold:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=death_nova_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    def _animate_minion(self, skill_name: str, *, aftercast_delay: int = 250) -> BuildCoroutine:
        skill_id: int = Skill.GetID(skill_name)

        if not self.build.IsSkillEquipped(skill_id):
            return False

        target_corpse_id = Routines.Agents.GetNearestExploitableCorpse(
            Range.Spellcast.value,
            reserve=True,
            skill_id=skill_id,
            aftercast_delay=aftercast_delay,
        )
        if not target_corpse_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=skill_id,
            target_agent_id=target_corpse_id,
            log=False,
            aftercast_delay=aftercast_delay,
        ))

    def Animate_Bone_Fiend(self) -> BuildCoroutine:
        return (yield from self._animate_minion("Animate_Bone_Fiend"))

    def Animate_Bone_Horror(self) -> BuildCoroutine:
        return (yield from self._animate_minion("Animate_Bone_Horror"))

    def Animate_Bone_Minions(self) -> BuildCoroutine:
        return (yield from self._animate_minion("Animate_Bone_Minions"))

    def Animate_Flesh_Golem(self) -> BuildCoroutine:
        return (yield from self._animate_minion("Animate_Flesh_Golem"))

    def Animate_Shambling_Horror(self) -> BuildCoroutine:
        return (yield from self._animate_minion("Animate_Shambling_Horror"))

    def Animate_Vampiric_Horror(self) -> BuildCoroutine:
        return (yield from self._animate_minion("Animate_Vampiric_Horror"))

    def Dark_Aura(
        self,
        *,
        required_profession: Profession = Profession.Necromancer,
        required_skill_id: int | None = None,
        other_ally: bool = False,
        assume_active_ms: int = 25000,
    ) -> BuildCoroutine:
        dark_aura_id: int = Skill.GetID("Dark_Aura")
        if required_skill_id is None:
            required_skill_id = Skill.GetID("Soul_Taker")

        if not self.build.IsSkillEquipped(dark_aura_id):
            return False
        if not (self.build.IsInAggro() or self.build.IsCloseToAggro()):
            return False

        target_agent_id = Routines.Targeting.TargetAllyByProfession(
            required_profession,
            required_skill_id=required_skill_id,
            other_ally=other_ally,
            filter_skill_id=dark_aura_id,
            distance=Range.Spellcast.value,
        )

        if not target_agent_id and not other_ally:
            player_agent_id = Player.GetAgentID()
            primary_profession, _ = Agent.GetProfessions(player_agent_id)
            if (
                int(primary_profession or 0) == int(required_profession)
                and self.build.IsSkillEquipped(required_skill_id)
                and not Routines.Checks.Agents.HasEffect(player_agent_id, dark_aura_id)
            ):
                target_agent_id = player_agent_id

        if not target_agent_id:
            return False

        now_ms = int(Utils.GetBaseTimestamp())
        assumed_targets = getattr(self.build, "_dark_aura_assumed_targets", {})
        if int(assumed_targets.get(target_agent_id, 0) or 0) > now_ms:
            return False

        cast_result = yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=dark_aura_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        )
        if cast_result:
            assumed_targets[target_agent_id] = now_ms + max(0, int(assume_active_ms))
            setattr(self.build, "_dark_aura_assumed_targets", assumed_targets)
            return True

        return False
    #endregion

    #region P
    def Putrid_Bile(self) -> BuildCoroutine:
        putrid_bile_id: int = Skill.GetID("Putrid_Bile")
        assassins_promise_id: int = Skill.GetID("Assassins_Promise")

        if not self.build.IsSkillEquipped(putrid_bile_id):
            return False
        if not self.build.IsInAggro():
            return False

        # Snapshot alive enemies in spellcast range — used by the Assasins promise-focus
        # search and the single-target fallback.
        player_pos = Player.GetXY()
        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByDistance(enemy_array, player_pos, Range.Spellcast.value)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsAlive(agent_id))
        if not enemy_array:
            return False

        def _has_putrid_bile(agent_id: int) -> bool:
            return putrid_bile_id in self.build.GetEffectAndBuffIds(agent_id)

        # Tier 1: live Assassins Promise-hexed enemy without Putrid Bile already up. Piggybacks
        # on the Assassins Promise focus so both hexes detonate when the target dies.
        target_agent_id = 0
        for enemy_id in enemy_array:
            effect_ids = self.build.GetEffectAndBuffIds(enemy_id)
            if assassins_promise_id in effect_ids and putrid_bile_id not in effect_ids:
                target_agent_id = enemy_id
                break

        # Tier 2: best cluster with 2+ neighbors in Range.Nearby. Anchor must
        # be < 25% HP (about to die) so the detonation pays off.
        if not target_agent_id:
            target_agent_id = Routines.Targeting.PickClusteredTarget(
                cluster_radius=Range.Nearby.value,
                preferred_condition=lambda agent_id: (
                    Routines.Targeting.CountNearbyEnemies(agent_id, Range.Nearby.value) >= 2
                    and Agent.GetHealth(agent_id) < 0.25
                    and not _has_putrid_bile(agent_id)
                ),
                filter_radius=Range.Spellcast.value,
            )

        # Tier 3: best cluster with 1+ neighbor in Range.Nearby. Anchor must
        # be < 35% HP.
        if not target_agent_id:
            target_agent_id = Routines.Targeting.PickClusteredTarget(
                cluster_radius=Range.Nearby.value,
                preferred_condition=lambda agent_id: (
                    Routines.Targeting.CountNearbyEnemies(agent_id, Range.Nearby.value) >= 1
                    and Agent.GetHealth(agent_id) < 0.35
                    and not _has_putrid_bile(agent_id)
                ),
                filter_radius=Range.Spellcast.value,
            )

        # Tier 4: any enemy < 35% HP without Putrid Bile (no cluster
        # requirement). Closest first so the cast is least likely to whiff.
        if not target_agent_id:
            candidates = [
                aid for aid in enemy_array
                if Agent.GetHealth(aid) < 0.35 and not _has_putrid_bile(aid)
            ]
            if candidates:
                target_agent_id = sorted(
                    candidates,
                    key=lambda aid: Utils.Distance(player_pos, Agent.GetXY(aid)),
                )[0]

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=putrid_bile_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    def Putrid_Explosion(self) -> BuildCoroutine:
        putrid_explosion_id: int = Skill.GetID("Putrid_Explosion")

        if not self.build.IsSkillEquipped(putrid_explosion_id):
            return False
        if not self.build.IsInAggro():
            return False

        # Tiered fallback: prefer corpses with the largest enemy-target cluster
        # around them. If no corpse has 4+ enemy targets in Range.Nearby, fall
        # through to 3+, 2+, 1+. Each tier returns the highest-scoring corpse
        # meeting its floor.
        target_corpse_id = (
            Routines.Targeting.PickClusteredEnemiesAroundCorpse(
                cluster_radius=Range.Nearby.value,
                filter_radius=Range.Spellcast.value,
                min_enemy_targets=4,
            )
            or Routines.Targeting.PickClusteredEnemiesAroundCorpse(
                cluster_radius=Range.Nearby.value,
                filter_radius=Range.Spellcast.value,
                min_enemy_targets=3,
            )
            or Routines.Targeting.PickClusteredEnemiesAroundCorpse(
                cluster_radius=Range.Nearby.value,
                filter_radius=Range.Spellcast.value,
                min_enemy_targets=2,
            )
            or Routines.Targeting.PickClusteredEnemiesAroundCorpse(
                cluster_radius=Range.Nearby.value,
                filter_radius=Range.Spellcast.value,
                min_enemy_targets=1,
            )
        )
        if not target_corpse_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=putrid_explosion_id,
            target_agent_id=target_corpse_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region R
    def Rising_Bile(self) -> BuildCoroutine:
        rising_bile_id: int = Skill.GetID("Rising_Bile")

        if not self.build.IsSkillEquipped(rising_bile_id):
            return False
        if not self.build.IsInAggro():
            return False

        # Pure cluster pick: anchor with the most alive enemies in Range.Area.
        # Hard floor of 2+ neighbors (3+ total foes damaged) — Rising Bile only
        # pays off when the on-end AoE hits a real cluster. Cast as the opening
        # hex so the 20s timer accumulates maximum per-second damage.
        target_agent_id = Routines.Targeting.PickClusteredTarget(
            cluster_radius=Range.Area.value,
            preferred_condition=lambda agent_id: (
                Routines.Targeting.CountNearbyEnemies(agent_id, Range.Area.value) >= 2
                and rising_bile_id not in self.build.GetEffectAndBuffIds(agent_id)
            ),
            filter_radius=Range.Spellcast.value,
        )

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=rising_bile_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
