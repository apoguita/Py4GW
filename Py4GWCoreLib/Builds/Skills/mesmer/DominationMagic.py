from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib import Range, Routines
from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills._whiteboard import coordinates_whiteboard_skill_target
from Py4GWCoreLib.GlobalCache.HexRemovalPriority import HexRemovalPriority, cast_hex_removal_and_track, get_hexed_ally_for_removal

if TYPE_CHECKING:
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["DominationMagic"]


class DominationMagic:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

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
