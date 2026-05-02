from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import AgentArray, GLOBAL_CACHE, Player, Range, Routines, SpiritModelID, ThrottledTimer, Utils
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["NoAttribute"]


class NoAttribute:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build
        self._save_yourselves_throttle: ThrottledTimer = ThrottledTimer(4000)
        self._save_yourselves_throttle.Stop()

    #region B
    def Breath_of_the_Great_Dwarf(self) -> BuildCoroutine:
        breath_of_the_great_dwarf_id: int = Skill.GetID("Breath_of_the_Great_Dwarf")
        breath_of_the_great_dwarf: CustomSkill = self.build.GetCustomSkill(breath_of_the_great_dwarf_id)
        burning_id: int = Skill.GetID("Burning")

        def _party_has_burning() -> bool:
            ally_array = Routines.Targeting.GetAllAlliesArray(Range.SafeCompass.value)
            return any(
                Routines.Checks.Agents.HasEffect(agent_id, burning_id)
                for agent_id in (ally_array or [])
            )

        if not self.build.IsSkillEquipped(breath_of_the_great_dwarf_id):
            return False
        if not (
            self.build.EvaluatePartyWideThreshold(
                breath_of_the_great_dwarf_id,
                breath_of_the_great_dwarf,
            )
            or _party_has_burning()
        ):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=breath_of_the_great_dwarf_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region G
    def Great_Dwarf_Weapon(self) -> BuildCoroutine:
        great_dwarf_weapon_id: int = Skill.GetID("Great_Dwarf_Weapon")
        great_dwarf_weapon: CustomSkill = self.build.GetCustomSkill(great_dwarf_weapon_id)

        if not self.build.IsSkillEquipped(great_dwarf_weapon_id):
            return False

        target_agent_id = self.build.ResolveAllyTarget(
            great_dwarf_weapon_id,
            great_dwarf_weapon,
        )
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=great_dwarf_weapon_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250
        ))
    #endregion
    
    #region Y
    def You_Are_All_Weaklings(self) -> BuildCoroutine:
        you_are_all_weaklings_id: int = Skill.GetID("You_Are_All_Weaklings")

        if not self.build.IsSkillEquipped(you_are_all_weaklings_id):
            return False

        target_agent_id = Routines.Targeting.PickClusteredTarget(
            Range.Adjacent.value,
            filter_radius=Range.Spellcast.value,
        )
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillID(
            skill_id=you_are_all_weaklings_id,
            log=False,
            aftercast_delay=250,
            target_agent_id=target_agent_id,
        ))

    def You_Move_Like_a_Dwarf(
        self,
        *,
        energy_threshold_pct: float = 0.30,
        energy_threshold_abs: float | None = None,
    ) -> BuildCoroutine:
        you_move_id: int = Skill.GetID("You_Move_Like_a_Dwarf")
        assassins_promise_id: int = Skill.GetID("Assassins_Promise")

        if not self.build.IsSkillEquipped(you_move_id):
            return False
        if not self.build.IsInAggro():
            return False

        player_id = Player.GetAgentID()

        def _has_enough_energy() -> bool:
            if energy_threshold_abs is not None:
                current_energy_abs = Agent.GetEnergy(player_id) * Agent.GetMaxEnergy(player_id)
                return current_energy_abs >= energy_threshold_abs
            return Agent.GetEnergy(player_id) >= energy_threshold_pct

        # Snapshot alive enemies in earshot range — Norn-style shouts use
        # earshot reach.
        player_pos = Player.GetXY()
        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByDistance(enemy_array, player_pos, Range.Earshot.value)
        enemy_array = AgentArray.Filter.ByCondition(
            enemy_array,
            lambda agent_id: Agent.IsAlive(agent_id),
        )
        if not enemy_array:
            return False

        # Tier 1: Assassins_Promise-hexed target — chain the knockdown with the AP focus.
        # No energy gate; this synergy outweighs energy cost.
        target_agent_id = 0
        for enemy_id in enemy_array:
            if assassins_promise_id in self.build.GetEffectAndBuffIds(enemy_id):
                target_agent_id = enemy_id
                break

        # Tier 2 & 3 require caster energy at or above the threshold.
        if not target_agent_id and _has_enough_energy():
            # Tier 2: melee enemies, closest first — interrupt the runners.
            melee_candidates = [
                aid for aid in enemy_array
                if Agent.IsMelee(aid)
            ]
            if melee_candidates:
                target_agent_id = sorted(
                    melee_candidates,
                    key=lambda aid: Utils.Distance(player_pos, Agent.GetXY(aid)),
                )[0]

            # Tier 3: any enemy in earshot, closest first.
            if not target_agent_id:
                target_agent_id = sorted(
                    enemy_array,
                    key=lambda aid: Utils.Distance(player_pos, Agent.GetXY(aid)),
                )[0]

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=you_move_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region F
    def Finish_Him(self) -> BuildCoroutine:
        finish_him_id: int = Skill.GetID("Finish_Him")
        assassins_promise_id: int = Skill.GetID("Assassins_Promise")
        cracked_armor_id: int = Skill.GetID("Cracked_Armor")
        deep_wound_id: int = Skill.GetID("Deep_Wound")

        if not self.build.IsSkillEquipped(finish_him_id):
            return False
        if not self.build.IsInAggro():
            return False

        # Snapshot alive enemies in earshot range with HP < 50%. Finish Him!
        # is a Norn shout that only applies its conditions when the foe is
        # below 50% HP, so the trigger threshold gates every tier.
        player_pos = Player.GetXY()
        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByDistance(enemy_array, player_pos, Range.Earshot.value)
        enemy_array = AgentArray.Filter.ByCondition(
            enemy_array,
            lambda agent_id: Agent.IsAlive(agent_id) and Agent.GetHealth(agent_id) < 0.5,
        )
        if not enemy_array:
            return False

        def _has_cracked_armor(agent_id: int) -> bool:
            return Routines.Checks.Agents.HasEffect(agent_id, cracked_armor_id)

        def _has_deep_wound(agent_id: int) -> bool:
            return Routines.Checks.Agents.HasEffect(agent_id, deep_wound_id)

        # Tier 1: Assassins_Promise-hexed target — synergy with the AP focus. Cast regardless
        # of existing cracked armor / deep wound on the target.
        target_agent_id = 0
        for enemy_id in enemy_array:
            if assassins_promise_id in self.build.GetEffectAndBuffIds(enemy_id):
                target_agent_id = enemy_id
                break

        # Tier 2: clean target (no cracked armor, no deep wound) with the
        # highest max HP — Deep Wound's -20% max-HP penalty is most valuable
        # on the fattest target.
        if not target_agent_id:
            candidates = [
                aid for aid in enemy_array
                if not _has_cracked_armor(aid) and not _has_deep_wound(aid)
            ]
            if candidates:
                target_agent_id = sorted(
                    candidates,
                    key=lambda aid: -Agent.GetMaxHealth(aid),
                )[0]

        # Tier 3: target with exactly one of (cracked armor, deep wound) —
        # apply the missing condition for full value. Highest max HP first.
        if not target_agent_id:
            candidates = [
                aid for aid in enemy_array
                if _has_cracked_armor(aid) ^ _has_deep_wound(aid)
            ]
            if candidates:
                target_agent_id = sorted(
                    candidates,
                    key=lambda aid: -Agent.GetMaxHealth(aid),
                )[0]

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=finish_him_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region E
    def Ebon_Battle_Standard_of_Honor(self) -> BuildCoroutine:
        ebsoh_id: int = Skill.GetID("Ebon_Battle_Standard_of_Honor")

        if not self.build.IsSkillEquipped(ebsoh_id):
            return False
        if not self.build.IsInAggro():
            return False

        player_agent_id = Player.GetAgentID()

        # last 2-second refresh window.
        if not Routines.Checks.Agents.HasEffect(player_agent_id, ebsoh_id):
            return False
        remaining_ms = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(
            player_agent_id, ebsoh_id
        )
        if remaining_ms > 2000:
            return False

        return (yield from self.build.CastSkillID(
            skill_id=ebsoh_id,
            log=False,
            aftercast_delay=250,
        ))

    def Ebon_Battle_Standard_of_Wisdom(self) -> BuildCoroutine:
        ebon_battle_standard_of_wisdom_id: int = Skill.GetID("Ebon_Battle_Standard_of_Wisdom")
        player_agent_id = Player.GetAgentID()

        if not self.build.IsSkillEquipped(ebon_battle_standard_of_wisdom_id):
            return False
        if not self.build.IsInAggro():
            return False
        if Routines.Checks.Agents.HasEffect(player_agent_id, ebon_battle_standard_of_wisdom_id):
            return False

        ally_array = Routines.Targeting.GetAllAlliesArray(Range.Spellcast.value)
        ally_array = AgentArray.Filter.ByCondition(
            ally_array,
            lambda agent_id: Agent.IsAlive(agent_id) and Routines.Checks.Agents.IsCaster(agent_id),
        )
        if len(ally_array or []) < 2:
            return False

        return (yield from self.build.CastSkillID(
            skill_id=ebon_battle_standard_of_wisdom_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region I
    def I_Am_Unstoppable(self) -> BuildCoroutine:
        i_am_unstoppable_id: int = Skill.GetID("I_Am_Unstoppable")
        player_agent_id = Player.GetAgentID()

        if not self.build.IsSkillEquipped(i_am_unstoppable_id):
            return False
        if not self.build.IsInAggro():
            return False
        if Agent.GetHealth(player_agent_id) > 0.70 and not Agent.IsKnockedDown(player_agent_id):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=i_am_unstoppable_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region S
    def Save_Yourselves_kurzick(self) -> BuildCoroutine:
        save_yourselves_kurzick_id: int = Skill.GetID("Save_Yourselves_kurzick")
        return (yield from self._cast_protective_party_shout(
            save_yourselves_kurzick_id,
            health_threshold=1.1,
            minimum_allies=1,
        ))

    def Save_Yourselves_luxon(self) -> BuildCoroutine:
        save_yourselves_luxon_id: int = Skill.GetID("Save_Yourselves_luxon")
        return (yield from self._cast_protective_party_shout(
            save_yourselves_luxon_id,
            health_threshold=1.1,
            minimum_allies=0,
        ))

    def Summon_Spirits(self) -> BuildCoroutine:
        """Pull or heal owned spirits.

        Auto-detects whether the Kurzick or Luxon variant is on the bar.
        Three independent triggers — any one fires the cast:
        - Far from aggro: any owned spirit is more than 3750 GU
          (Compass * 0.75) away — pull lagging spirits while travelling.
        - Close to aggro or in aggro: any owned spirit is more than
          322 GU (Range.Area) away — keep the spirits tight on the
          caster during combat.
        - Any state: any owned spirit is below 90% health (Summon
          Spirits restores HP/energy on each owned spirit on cast).
        """
        summon_spirits_kurzick_id: int = Skill.GetID("Summon_Spirits_kurzick")
        summon_spirits_luxon_id: int = Skill.GetID("Summon_Spirits_luxon")

        if self.build.IsSkillEquipped(summon_spirits_kurzick_id):
            skill_id = summon_spirits_kurzick_id
        elif self.build.IsSkillEquipped(summon_spirits_luxon_id):
            skill_id = summon_spirits_luxon_id
        else:
            return False

        self_agent_id = self.build._resolve_self_agent_id()
        player_xy = Player.GetXY()

        owned_spirits = AgentArray.GetSpiritPetArray()
        owned_spirits = AgentArray.Filter.ByDistance(owned_spirits, player_xy, Range.Compass.value)
        owned_spirits = AgentArray.Filter.ByCondition(
            owned_spirits,
            lambda agent_id: (
                Agent.IsAlive(agent_id)
                and Agent.IsSpawned(agent_id)
                and Agent.GetOwnerID(agent_id) == self_agent_id
            ),
        )
        if not owned_spirits:
            return False

        in_aggro = self.build.IsInAggro()
        close_to_aggro = in_aggro or self.build.IsCloseToAggro()

        if close_to_aggro:
            combat_threshold = Range.Area.value
            combat_pull = any(
                Utils.Distance(player_xy, Agent.GetXY(spirit_id)) > combat_threshold
                for spirit_id in owned_spirits
            )
        else:
            combat_pull = False

        if not close_to_aggro:
            travel_threshold = Range.Compass.value * 0.75
            travel_pull = any(
                Utils.Distance(player_xy, Agent.GetXY(spirit_id)) > travel_threshold
                for spirit_id in owned_spirits
            )
        else:
            travel_pull = False

        needs_heal = any(Agent.GetHealth(spirit_id) < 0.9 for spirit_id in owned_spirits)

        if not (combat_pull or travel_pull or needs_heal):
            return False

        return (yield from self.build.CastSkillID(
            skill_id=skill_id,
            log=False,
            aftercast_delay=250,
        ))

    def Summon_Spirits_kurzick(self) -> BuildCoroutine:
        summon_spirits_kurzick_id: int = Skill.GetID("Summon_Spirits_kurzick")
        return (yield from self._summon_spirits(summon_spirits_kurzick_id))

    def Summon_Spirits_luxon(self) -> BuildCoroutine:
        summon_spirits_luxon_id: int = Skill.GetID("Summon_Spirits_luxon")
        return (yield from self._summon_spirits(summon_spirits_luxon_id))
    #endregion

    #region T
    def Theres_Nothing_to_Fear(self) -> BuildCoroutine:
        theres_nothing_to_fear_id: int = Skill.GetID("Theres_Nothing_to_Fear")
        return (yield from self._cast_protective_party_shout(
            theres_nothing_to_fear_id,
            health_threshold=1.1,
            minimum_allies=0,
        ))
    #endregion

    def _cast_protective_party_shout(
        self,
        skill_id: int,
        *,
        health_threshold: float,
        minimum_allies: int,
    ) -> BuildCoroutine:
        player_agent_id = Player.GetAgentID()

        if not (self._save_yourselves_throttle.IsStopped() or self._save_yourselves_throttle.IsExpired()):
            return False
        if not self.build.IsSkillEquipped(skill_id):
            return False
        if not self.build.IsInAggro():
            return False
        if Routines.Checks.Agents.HasEffect(player_agent_id, skill_id):
            return False

        ally_array = Routines.Targeting.GetAllAlliesArray(Range.Earshot.value)
        ally_array = AgentArray.Filter.ByCondition(
            ally_array,
            lambda agent_id: Agent.IsAlive(agent_id) and Agent.GetHealth(agent_id) < health_threshold,
        )
        if len(ally_array or []) < minimum_allies:
            return False

        cast_result = yield from self.build.CastSkillID(
            skill_id=skill_id,
            log=False,
            aftercast_delay=250,
        )
        if cast_result:
            self._save_yourselves_throttle.Reset()
        return cast_result

    def _get_owned_core_spirits(
        self,
        range_value: float = Range.Compass.value,
        include_owner_fallback: bool = False,
    ) -> list[int]:
        core_spirits = {
            SpiritModelID.SHELTER,
            SpiritModelID.UNION,
            SpiritModelID.DISPLACEMENT,
        }
        player_agent_id = Player.GetAgentID()
        spirit_array = AgentArray.GetSpiritPetArray()
        spirit_array = AgentArray.Filter.ByDistance(spirit_array, Player.GetXY(), range_value)
        spirit_array = AgentArray.Filter.ByCondition(
            spirit_array,
            lambda agent_id: Agent.IsAlive(agent_id) and Agent.IsSpawned(agent_id),
        )

        owned_core_spirits: list[int] = []
        nearby_core_spirits: list[int] = []
        ownerless_core_spirits: list[int] = []
        for spirit_id in spirit_array:
            model_value = Agent.GetPlayerNumber(spirit_id)
            if model_value not in SpiritModelID._value2member_map_:
                continue
            if SpiritModelID(model_value) not in core_spirits:
                continue
            nearby_core_spirits.append(spirit_id)

            owner_id = Agent.GetOwnerID(spirit_id)
            if owner_id == player_agent_id:
                owned_core_spirits.append(spirit_id)
            elif owner_id == 0:
                ownerless_core_spirits.append(spirit_id)

        if owned_core_spirits:
            return owned_core_spirits
        if include_owner_fallback:
            # Return the full nearby set when ownership metadata is unreliable.
            # Returning only ownerless spirits can hide valid distant spirits.
            return nearby_core_spirits
        return owned_core_spirits

    def _summon_spirits(self, skill_id: int) -> BuildCoroutine:
        if not self.build.IsSkillEquipped(skill_id):
            self.build._debug(f"Summon Spirits skipped: skill not equipped ({skill_id})", True)
            return False

        in_aggro = self.build.IsInAggro()

        spirits = self._get_owned_core_spirits()
        if not spirits:
            spirits = self._get_owned_core_spirits(
                Range.Compass.value,
                include_owner_fallback=True,
            )
            if spirits:
                self.build._debug(
                    "Summon Spirits owner fallback: nearby core spirits found with non-matching owner metadata",
                    True,
                )
            else:
                spirits_safe_compass = self._get_owned_core_spirits(
                    Range.SafeCompass.value,
                    include_owner_fallback=True,
                )
                if spirits_safe_compass:
                    self.build._debug(
                        "Summon Spirits skipped: owned core spirits found, but all are outside compass range",
                        True,
                    )
                else:
                    self.build._debug("Summon Spirits skipped: no owned core spirits found", True)
                return False

        if not spirits:
            return False

        player_xy = Player.GetXY()
        spirit_distances = [
            Utils.Distance(player_xy, Agent.GetXY(spirit_id))
            for spirit_id in spirits
        ]
        if in_aggro:
            # In combat, keep spirits tight: pull them once any core spirit leaves Nearby.
            should_reposition = any(
                Range.Nearby.value < distance <= Range.Compass.value
                for distance in spirit_distances
            )
            mode_label = "aggro-nearby"
        else:
            should_reposition = any(
                Range.Spirit.value < distance <= Range.Compass.value
                for distance in spirit_distances
            )
            mode_label = "ooc-compass"

        if not should_reposition:
            nearest_distance = min(spirit_distances) if spirit_distances else 0.0
            farthest_distance = max(spirit_distances) if spirit_distances else 0.0
            self.build._debug(
                (
                    "Summon Spirits skipped: all owned core spirits within threshold "
                    f"(nearest={nearest_distance:.1f}, farthest={farthest_distance:.1f}, mode={mode_label})"
                ),
                True,
            )
            return False

        self.build._debug(
            f"Summon Spirits trigger: owned core spirit is beyond spirit range (mode={mode_label})",
            True,
        )
        precheck_failure = self.build._get_can_cast_skill_failure_reason(skill_id)
        if precheck_failure is not None:
            self.build._debug(f"Summon Spirits precheck blocked: reason={precheck_failure}", True)
            return False

        result = (yield from self.build.CastSkillID(
            skill_id=skill_id,
            log=False,
            aftercast_delay=250,
        ))
        if result:
            self.build._debug("Summon Spirits cast success", True)
        else:
            self.build._debug("Summon Spirits cast failed (CanCastSkillID or runtime cast failure)", True)
        return result
