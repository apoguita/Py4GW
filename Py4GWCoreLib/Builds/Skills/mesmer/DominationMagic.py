from __future__ import annotations

import time
from typing import TYPE_CHECKING

from Py4GWCoreLib import Range, Routines
from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills._whiteboard import coordinates_whiteboard_skill_target
from Py4GWCoreLib.GlobalCache.HexRemovalPriority import HexRemovalPriority, cast_hex_removal_and_track, get_hexed_ally_for_removal

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["DominationMagic"]

_WASTRELS_WORRY_COOLDOWN_S: float = 3.0
_WASTRELS_DEMISE_COOLDOWN_S: float = 5.0


class DominationMagic:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build
        self._wastrels_worry_last_cast: dict[int, float] = {}
        self._wastrels_demise_last_cast: dict[int, float] = {}

    @staticmethod
    def _agent_is_knocked_down(agent_id: int) -> bool:
        """Detect knockdown via model_state bit and the living-agent flag."""
        from Py4GWCoreLib import Agent

        model_state = Agent.GetModelState(agent_id)
        if model_state == 1104 or (model_state & 0x400):
            return True
        return bool(Agent.IsKnockedDown(agent_id))

    def _pick_wastrels_target(
        self,
        skill_id: int,
        last_cast: dict[int, float],
        cooldown_s: float,
        *,
        require_knockdown: bool = False,
        exclude_knockdown: bool = False,
        min_energy_abs: int = 0,
    ) -> int:
        from Py4GWCoreLib import Agent, Player, GLOBAL_CACHE
        from Py4GWCoreLib.AgentArray import AgentArray
        from Py4GWCoreLib.Py4GWcorelib import Utils

        if require_knockdown and exclude_knockdown:
            return 0

        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(skill_id) or Range.Adjacent.value
        now = time.monotonic()

        def _not_on_cooldown(agent_id: int) -> bool:
            last = last_cast.get(agent_id)
            return last is None or now - last >= cooldown_s

        if min_energy_abs > 0:
            player_id = Player.GetAgentID()
            current_energy = Agent.GetEnergy(player_id) * Agent.GetMaxEnergy(player_id)
            if current_energy < min_energy_abs:
                return 0

        player_pos = Player.GetXY()
        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByDistance(enemy_array, player_pos, Range.Spellcast.value)
        enemy_array = AgentArray.Filter.ByCondition(
            enemy_array,
            lambda agent_id: Agent.IsValid(agent_id) and Agent.IsAlive(agent_id) and _not_on_cooldown(agent_id),
        )
        if not enemy_array:
            return 0

        def _cluster_sort_key(agent_id: int) -> tuple[int, float]:
            return (
                -Routines.Targeting.CountNearbyEnemies(agent_id, aoe_range),
                Utils.Distance(player_pos, Agent.GetXY(agent_id)),
            )

        if require_knockdown:
            kd_enemies = [agent_id for agent_id in enemy_array if self._agent_is_knocked_down(agent_id)]
            if not kd_enemies:
                return 0
            return sorted(kd_enemies, key=_cluster_sort_key)[0]

        if exclude_knockdown:
            enemy_array = [agent_id for agent_id in enemy_array if not self._agent_is_knocked_down(agent_id)]
            if not enemy_array:
                return 0

        non_casting = [agent_id for agent_id in enemy_array if not Agent.IsCasting(agent_id)]
        if non_casting:
            return sorted(non_casting, key=_cluster_sort_key)[0]

        return sorted(enemy_array, key=_cluster_sort_key)[0]

    #region E
    def Energy_Surge(self) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, Player, Range, GLOBAL_CACHE

        energy_surge_id: int = Skill.GetID("Energy_Surge")
        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(energy_surge_id) or Range.Nearby.value

        if not self.build.IsSkillEquipped(energy_surge_id):
            return False

        def _is_enemy_casting_spell(agent_id: int) -> bool:
            if not Agent.IsCaster(agent_id):
                return False
            if not Agent.IsCasting(agent_id):
                return False
            casting_skill_id = Agent.GetCastingSkillID(agent_id)
            return bool(casting_skill_id and GLOBAL_CACHE.Skill.Flags.IsSpell(casting_skill_id))

        target_agent_id = Routines.Targeting.PickClusteredTarget(
            cluster_radius=aoe_range,
            preferred_condition=_is_enemy_casting_spell,
            filter_radius=Range.Spellcast.value,
        )

        if not target_agent_id:
            best_enemy_target_id = Routines.Targeting.PickClusteredTarget(
                cluster_radius=aoe_range,
                filter_radius=Range.Spellcast.value,
            )
            current_target_id = Player.GetTargetID()
            if Agent.IsValid(current_target_id) and not Agent.IsDead(current_target_id):
                current_target_score = Routines.Targeting.CountNearbyEnemies(current_target_id, aoe_range)
                best_enemy_score = Routines.Targeting.CountNearbyEnemies(best_enemy_target_id, aoe_range)
                if current_target_score >= best_enemy_score:
                    target_agent_id = current_target_id

            if not target_agent_id:
                target_agent_id = best_enemy_target_id

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=energy_surge_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region C
    @coordinates_whiteboard_skill_target(Skill.GetID("Cry_of_Frustration"))
    def Cry_of_Frustration(self) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, Range, GLOBAL_CACHE

        cry_of_frustration_id: int = Skill.GetID("Cry_of_Frustration")
        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(cry_of_frustration_id) or Range.Nearby.value

        target_agent_id = Routines.Targeting.PickClusteredTarget(
            cluster_radius=aoe_range,
            preferred_condition=lambda agent_id: Agent.IsCasting(agent_id),
            filter_radius=Range.Spellcast.value,
        )

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=cry_of_frustration_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region M
    @coordinates_whiteboard_skill_target(Skill.GetID("Mistrust"))
    def Mistrust(self) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, Range, GLOBAL_CACHE

        mistrust_id: int = Skill.GetID("Mistrust")
        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(mistrust_id) or Range.Nearby.value

        def _is_enemy_casting_spell(agent_id: int) -> bool:
            if not Agent.IsCasting(agent_id):
                return False
            casting_skill_id = Agent.GetCastingSkillID(agent_id)
            return bool(casting_skill_id and GLOBAL_CACHE.Skill.Flags.IsSpell(casting_skill_id))

        target_agent_id = Routines.Targeting.PickClusteredTarget(
            cluster_radius=aoe_range,
            preferred_condition=_is_enemy_casting_spell,
            filter_radius=Range.Spellcast.value,
        )

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=mistrust_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region O
    @coordinates_whiteboard_skill_target(Skill.GetID("Overload"))
    def Overload(self) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, Range, GLOBAL_CACHE

        overload_id: int = Skill.GetID("Overload")
        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(overload_id) or Range.Adjacent.value

        target_agent_id = Routines.Targeting.PickClusteredTarget(
            cluster_radius=aoe_range,
            preferred_condition=lambda agent_id: Agent.IsCasting(agent_id),
            filter_radius=Range.Spellcast.value,
        )

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=overload_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region P
    @coordinates_whiteboard_skill_target(Skill.GetID("Psychic_Instability"))
    def Psychic_Instability(self) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, GLOBAL_CACHE

        psychic_instability_id: int = Skill.GetID("Psychic_Instability")
        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(psychic_instability_id) or Range.Adjacent.value

        if not self.build.IsSkillEquipped(psychic_instability_id):
            return False

        # PI interrupts any skill or spell being cast, not only spells.
        # The interrupt fires and knocks down the target plus all adjacent foes.
        # Cast condition is hard – no fallback to non-casting targets.
        # Among all casting enemies in spellcast range, prefer the one with the
        # most adjacent enemies to maximise the knockdown area.
        target_agent_id = Routines.Targeting.PickClusteredTarget(
            cluster_radius=aoe_range,
            preferred_condition=lambda agent_id: Agent.IsCasting(agent_id),
            filter_radius=Range.Spellcast.value,
        )

        # Require at least one casting enemy – do not cast into the void.
        if not target_agent_id or not Agent.IsCasting(target_agent_id):
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=psychic_instability_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    @coordinates_whiteboard_skill_target(Skill.GetID("Panic"))
    def Panic(self) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, Range, GLOBAL_CACHE

        panic_id: int = Skill.GetID("Panic")
        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(panic_id) or Range.Nearby.value

        if not self.build.IsSkillEquipped(panic_id):
            return False

        # Tier 1: caster clusters. Panic's cascade only fires on activated
        # skills and spells (stances and shouts are instant and do NOT
        # trigger). Dense caster mobs cast spells constantly, maximising
        # the cascade.
        target_agent_id = Routines.Targeting.PickClusteredTarget(
            cluster_radius=aoe_range,
            preferred_condition=lambda agent_id: Agent.IsCaster(agent_id),
            filter_radius=Range.Spellcast.value,
        )

        # Tier 2: martial / melee clusters. Attack skills and signets have
        # activation times and trigger the cascade; stances and shouts do
        # not, so the trigger rate is lower than casters but still useful.
        if not target_agent_id:
            target_agent_id = Routines.Targeting.PickClusteredTarget(
                cluster_radius=aoe_range,
                preferred_condition=lambda agent_id: Agent.IsMartial(agent_id) or Agent.IsMelee(agent_id),
                filter_radius=Range.Spellcast.value,
            )

        # Tier 3: densest cluster of any foe. The hex still spreads on cast,
        # and any activated skill or spell from a hexed foe triggers the
        # cascade. Auto-attacks, stances, and shouts do not.
        if not target_agent_id:
            target_agent_id = Routines.Targeting.PickClusteredTarget(
                cluster_radius=aoe_range,
                filter_radius=Range.Spellcast.value,
            )

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=panic_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region S
    def Shatter_Hex(self, min_priority: int = HexRemovalPriority.LOW) -> BuildCoroutine:
        shatter_hex_id: int = Skill.GetID("Shatter_Hex")

        if not self.build.IsSkillEquipped(shatter_hex_id):
            return False

        target_agent_id = get_hexed_ally_for_removal(
            Range.Spellcast.value,
            reserve=True,
            skill_id=shatter_hex_id,
            min_priority=min_priority,
        )
        if not target_agent_id:
            return False

        return (yield from cast_hex_removal_and_track(
            self.build,
            skill_id=shatter_hex_id,
            target_agent_id=target_agent_id,
            aftercast_delay=250,
        ))
    #endregion

    #region W
    @coordinates_whiteboard_skill_target(Skill.GetID("Wastrels_Demise"))
    def Wastrels_Demise(
        self,
        *,
        require_knockdown: bool = False,
        exclude_knockdown: bool = False,
        min_energy_abs: int = 0,
    ) -> BuildCoroutine:
        wastrels_demise_id: int = Skill.GetID("Wastrels_Demise")

        if not self.build.IsSkillEquipped(wastrels_demise_id):
            return False

        now = time.monotonic()
        self._wastrels_demise_last_cast = {
            agent_id: t
            for agent_id, t in self._wastrels_demise_last_cast.items()
            if now - t < _WASTRELS_DEMISE_COOLDOWN_S
        }

        target_agent_id = self._pick_wastrels_target(
            wastrels_demise_id,
            self._wastrels_demise_last_cast,
            _WASTRELS_DEMISE_COOLDOWN_S,
            require_knockdown=require_knockdown,
            exclude_knockdown=exclude_knockdown,
            min_energy_abs=min_energy_abs,
        )
        if not target_agent_id:
            return False

        result = yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=wastrels_demise_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        )
        if result:
            self._wastrels_demise_last_cast[target_agent_id] = time.monotonic()
        return result

    @coordinates_whiteboard_skill_target(Skill.GetID("Wastrels_Worry"))
    def Wastrels_Worry(
        self,
        *,
        require_knockdown: bool = False,
        exclude_knockdown: bool = False,
        min_energy_abs: int = 0,
    ) -> BuildCoroutine:
        wastrels_worry_id: int = Skill.GetID("Wastrels_Worry")

        if not self.build.IsSkillEquipped(wastrels_worry_id):
            return False

        now = time.monotonic()
        self._wastrels_worry_last_cast = {
            agent_id: t
            for agent_id, t in self._wastrels_worry_last_cast.items()
            if now - t < _WASTRELS_WORRY_COOLDOWN_S
        }

        target_agent_id = self._pick_wastrels_target(
            wastrels_worry_id,
            self._wastrels_worry_last_cast,
            _WASTRELS_WORRY_COOLDOWN_S,
            require_knockdown=require_knockdown,
            exclude_knockdown=exclude_knockdown,
            min_energy_abs=min_energy_abs,
        )
        if not target_agent_id:
            return False

        result = yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=wastrels_worry_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        )
        if result:
            self._wastrels_worry_last_cast[target_agent_id] = time.monotonic()
        return result
    #endregion

    #region U
    def Unnatural_Signet(self) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, Range, GLOBAL_CACHE

        unnatural_signet_id: int = Skill.GetID("Unnatural_Signet")
        aoe_range = GLOBAL_CACHE.Skill.Data.GetAoERange(unnatural_signet_id) or Range.Adjacent.value

        if not self.build.IsSkillEquipped(unnatural_signet_id):
            return False

        target_agent_id = Routines.Targeting.PickClusteredTarget(
            cluster_radius=aoe_range,
            preferred_condition=lambda agent_id: Agent.IsHexed(agent_id) or Agent.IsEnchanted(agent_id),
            filter_radius=Range.Spellcast.value,
        )
        if not target_agent_id:
            target_agent_id = Routines.Targeting.PickClusteredTarget(
                cluster_radius=aoe_range,
                filter_radius=Range.Spellcast.value,
            )

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=unnatural_signet_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion
