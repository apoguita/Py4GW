from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import AgentArray, GLOBAL_CACHE, Range, Routines
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.GlobalCache.HexRemovalPriority import HexRemovalPriority, cast_hex_removal_and_track, get_hexed_ally_for_removal
from Py4GWCoreLib.Builds.Skills._whiteboard import coordinates_whiteboard_skill_target

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["SmitingPrayers"]


class SmitingPrayers:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    #region J
    def Judges_Insight(self) -> BuildCoroutine:
        judges_insight_id: int = Skill.GetID("Judges_Insight")

        if not self.build.IsSkillEquipped(judges_insight_id):
            return False

        ally_array = Routines.Targeting.GetAllAlliesArray(Range.Spellcast.value)
        ally_array = AgentArray.Filter.ByCondition(
            ally_array,
            lambda agent_id: Agent.IsAlive(agent_id),
        )
        ally_array = AgentArray.Filter.ByCondition(
            ally_array,
            lambda agent_id: Agent.IsMartial(agent_id),
        )
        ally_array = AgentArray.Filter.ByCondition(
            ally_array,
            lambda agent_id: not Routines.Checks.Agents.HasEffect(agent_id, judges_insight_id),
        )

        target_agent_id = ally_array[0] if ally_array else 0

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=judges_insight_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region B
    def Bane_Signet(self) -> BuildCoroutine:
        bane_signet_id: int = Skill.GetID("Bane_Signet")
        target_acquired, _ = self.build._resolve_target("EnemyAttacking")
        if not target_acquired:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=bane_signet_id,
            target_agent_id=self.build.current_target_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region C
    def Castigation_Signet(self) -> BuildCoroutine:
        castigation_signet_id: int = Skill.GetID("Castigation_Signet")

        # Short-circuit before the (relatively expensive) target resolution if the
        # signet isn't equipped or is on cooldown / can't fire right now.
        if not self.build.IsSkillEquipped(castigation_signet_id):
            return False
        if not self.build.CanCastSkillID(castigation_signet_id):
            return False

        target_acquired, _ = self.build._resolve_target("EnemyAttacking")
        if not target_acquired:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=castigation_signet_id,
            target_agent_id=self.build.current_target_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region R
    @coordinates_whiteboard_skill_target(Skill.GetID("Ray_of_Judgment"))
    def Ray_of_Judgment(self, *, exclude_target_id: int = 0) -> BuildCoroutine:
        from Py4GWCoreLib.Player import Player

        ray_of_judgment_id: int = Skill.GetID("Ray_of_Judgment")

        if not self.build.IsSkillEquipped(ray_of_judgment_id):
            return False
        if not self.build.IsInAggro():
            return False

        # Find first ready slot holding RoJ. Required for Arcane Echo combo —
        # RoJ may live in two slots (original + echo copy) and CastSkillID
        # always picks the first slot regardless of readiness. Fast path: if
        # the primary slot is ready, skip scanning duplicates.
        primary_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(ray_of_judgment_id)
        if not primary_slot:
            return False
        if Routines.Checks.Skills.IsSkillSlotReady(primary_slot):
            ready_slot = primary_slot
        else:
            ready_slot = 0
            for slot in range(1, 9):
                if slot == primary_slot:
                    continue
                if GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(slot) == ray_of_judgment_id:
                    if Routines.Checks.Skills.IsSkillSlotReady(slot):
                        ready_slot = slot
                        break
            if not ready_slot:
                return False

        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(ray_of_judgment_id) or Range.Adjacent.value

        # Exclude a prior cluster so the echo copy lands on a different group.
        preferred_condition = None
        if exclude_target_id:
            preferred_condition = lambda agent_id: agent_id != exclude_target_id

        target_agent_id = Routines.Targeting.PickClusteredTarget(
            cluster_radius=aoe_range,
            preferred_condition=preferred_condition,
            filter_radius=Range.Spellcast.value,
        )
        if not target_agent_id:
            return False

        if ready_slot == primary_slot:
            cast_result = yield from self.build.CastSkillIDAndRestoreTarget(
                skill_id=ray_of_judgment_id,
                target_agent_id=target_agent_id,
                log=False,
                aftercast_delay=250,
            )
        else:
            # Echo-slot fallback: cast via slot directly. CastSkillID would block
            # because GetSlotBySkillID returns the on-cooldown primary slot.
            aftercast_delay = 250

            if (
                self.build._is_whiteboard_skill(ray_of_judgment_id)
                and self.build._whiteboard_is_claimed(ray_of_judgment_id, target_agent_id)
            ):
                return False

            previous_enemy_target = Player.GetTargetID()
            if previous_enemy_target != target_agent_id:
                yield from Routines.Yield.Agents.ChangeTarget(target_agent_id)

            if self.build._is_whiteboard_skill(ray_of_judgment_id):
                self.build._whiteboard_post_intent(ray_of_judgment_id, target_agent_id)

            GLOBAL_CACHE.SkillBar.UseSkill(
                ready_slot,
                target_agent_id=target_agent_id,
                aftercast_delay=aftercast_delay,
            )
            self.build._mark_local_cast_pending(aftercast_delay)
            self.build.SetTickSuccess()

            yield from self.build.RestoreEnemyTarget(previous_enemy_target)
            cast_result = True

        if cast_result:
            import time
            self.build._last_ray_of_judgment_target_id = target_agent_id
            self.build._last_ray_of_judgment_cast_ts_ms = time.monotonic() * 1000.0
        return cast_result

    def Reversal_of_Damage(self) -> BuildCoroutine:
        reversal_of_damage_id: int = Skill.GetID("Reversal_of_Damage")
        reversal_of_damage: CustomSkill = self.build.GetCustomSkill(reversal_of_damage_id)

        if not self.build.IsSkillEquipped(reversal_of_damage_id):
            return False

        scan_range = Range.Touch.value
        enemies_cache: dict[int, list[int]] = {}
        melee_count_cache: dict[int, int] = {}

        def _enemies_around(ally_id: int) -> list[int]:
            cached = enemies_cache.get(ally_id)
            if cached is not None:
                return cached
            ally_x, ally_y = Agent.GetXY(ally_id)
            nearby_enemies = Routines.Agents.GetFilteredEnemyArray(ally_x, ally_y, scan_range)
            nearby_enemies = AgentArray.Filter.ByCondition(
                nearby_enemies,
                lambda enemy_id: Agent.IsAlive(enemy_id),
            )
            enemies_cache[ally_id] = nearby_enemies
            return nearby_enemies

        def _melee_count(ally_id: int) -> int:
            cached = melee_count_cache.get(ally_id)
            if cached is not None:
                return cached
            count = sum(
                1 for enemy_id in _enemies_around(ally_id)
                if Routines.Checks.Agents.IsMelee(enemy_id)
            )
            melee_count_cache[ally_id] = count
            return count

        def _enemy_count(ally_id: int) -> int:
            return len(_enemies_around(ally_id))

        # Tier 1: ally with the most melee enemies in touch range — best Reversal of Damage value vs. melee.
        target_agent_id = self.build.ResolveRankedPartyAllyTarget(
            reversal_of_damage_id,
            reversal_of_damage,
            validator=lambda agent_id: _melee_count(agent_id) > 0,
            rank_key=lambda agent_id: -_melee_count(agent_id),
        )

        # Tier 2: ally with the most enemies (any type) in touch range.
        if not target_agent_id:
            target_agent_id = self.build.ResolveRankedPartyAllyTarget(
                reversal_of_damage_id,
                reversal_of_damage,
                validator=lambda agent_id: _enemy_count(agent_id) > 0,
                rank_key=lambda agent_id: -_enemy_count(agent_id),
            )

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=reversal_of_damage_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region S
    def Smite_Condition(self) -> BuildCoroutine:
        smite_condition_id: int = Skill.GetID("Smite_Condition")
        smite_condition: CustomSkill = self.build.GetCustomSkill(smite_condition_id)

        if not self.build.IsSkillEquipped(smite_condition_id):
            return False

        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(smite_condition_id) or Range.Area.value
        enemy_count_cache: dict[int, int] = {}

        def _enemies_around(ally_id: int) -> int:
            cached = enemy_count_cache.get(ally_id)
            if cached is not None:
                return cached
            ally_x, ally_y = Agent.GetXY(ally_id)
            nearby_enemies = Routines.Agents.GetFilteredEnemyArray(ally_x, ally_y, aoe_range)
            nearby_enemies = AgentArray.Filter.ByCondition(
                nearby_enemies,
                lambda enemy_id: Agent.IsAlive(enemy_id),
            )
            count = len(nearby_enemies)
            enemy_count_cache[ally_id] = count
            return count

        # Tier 1: conditioned ally with the MOST enemies inside the cleanse AoE — maximises offensive value.
        # Validator (>0) filters out zero-enemy candidates; rank_key sorts the remainder by enemy count desc.
        target_agent_id = self.build.ResolveRankedPartyAllyTarget(
            smite_condition_id,
            smite_condition,
            validator=lambda agent_id: _enemies_around(agent_id) > 0,
            rank_key=lambda agent_id: -_enemies_around(agent_id),
        )

        # Tier 2: any conditioned ally — pure cleanse fallback when no enemies are clustered around a candidate.
        if not target_agent_id:
            target_agent_id = self.build.ResolveAllyTarget(
                smite_condition_id,
                smite_condition,
            )

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=smite_condition_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    def Smiters_Boon(self) -> BuildCoroutine:
        smiters_boon_id: int = Skill.GetID("Smiters_Boon")
        refresh_window_ms = 2000

        if not self.build.IsSkillEquipped(smiters_boon_id):
            return False
        if not self.build.IsInAggro():
            return False

        player_agent_id = Player.GetAgentID()
        if Routines.Checks.Agents.HasEffect(player_agent_id, smiters_boon_id):
            remaining_ms = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(
                player_agent_id,
                smiters_boon_id,
            )
            if remaining_ms > refresh_window_ms:
                return False

        return (yield from self.build.CastSkillID(
            skill_id=smiters_boon_id,
            log=False,
            aftercast_delay=250,
        ))

    def Smite_Hex(self, min_priority: int = HexRemovalPriority.LOW) -> BuildCoroutine:
        smite_hex_id: int = Skill.GetID("Smite_Hex")

        if not self.build.IsSkillEquipped(smite_hex_id):
            return False

        target_agent_id = get_hexed_ally_for_removal(
            Range.Spellcast.value,
            reserve=True,
            skill_id=smite_hex_id,
            min_priority=min_priority,
        )
        if not target_agent_id:
            return False

        return (yield from cast_hex_removal_and_track(
            self.build,
            skill_id=smite_hex_id,
            target_agent_id=target_agent_id,
            aftercast_delay=250,
        ))
    #endregion
