from __future__ import annotations

from collections.abc import Generator
from copy import deepcopy
import importlib
import inspect
import math
from pathlib import Path
import random
from typing import TYPE_CHECKING, Any, Callable, cast

import Py4GW

if TYPE_CHECKING:
    from HeroAI.custom_skill import CustomSkillClass
    from HeroAI.custom_skill_src.skill_types import CastConditions, CustomSkill
    from Py4GWCoreLib import Profession

BuildCoroutine = Generator[None, None, Any]
BuildHandler = Callable[[], Any]
TargetPredicate = Callable[[int], bool]
CustomSkillMutator = Callable[["CustomSkill"], None]

#region BuildMgr
class BuildMgr:
    from Py4GWCoreLib import Profession
    def __init__(
        self,
        name: str = "Generic Build",
        required_primary: Profession | None = None,
        required_secondary: Profession | None = None,
        template_code: str = "AAAAAAAAAAAAAAAA",
        required_skills: list[int] | None = None,
        optional_skills: list[int] | None = None,
        skills: list[int] | None = None,
        fallback_name: str | None = None,
        fallback_handler: "BuildMgr | None" = None,
        is_fallback_candidate: bool = False,
        IsFixedBuild: bool = False,
        is_combat_automator_compatible: bool = True,
        is_template_only: bool = False,
    ):
        from Py4GWCoreLib import Profession
        from Py4GWCoreLib import ThrottledTimer
        self.build_name = name
        self.required_primary: Profession = required_primary if required_primary is not None else Profession(0)
        self.required_secondary: Profession = required_secondary if required_secondary is not None else Profession(0)
        self.template_code = template_code
        legacy_skills = list(skills or [])
        self.required_skills = list(required_skills if required_skills is not None else legacy_skills)
        self.optional_skills = list(optional_skills or [])
        self.skills = list(self.required_skills)
        self.default_fallback_name = fallback_name
        self.current_fallback_name = fallback_name
        self.default_fallback_handler = fallback_handler
        self.current_fallback_handler = fallback_handler
        self.is_fallback_candidate = is_fallback_candidate
        self.IsFixedBuild = IsFixedBuild
        self.is_combat_automator_compatible = is_combat_automator_compatible
        self.is_template_only = is_template_only
        self.blocked_skills: list[int] = []
        self.priority_target = 0
        self._local_skill_casting_handler: BuildHandler | None = None
        self._local_ooc_handler: BuildHandler | None = None
        self._local_combat_handler: BuildHandler | None = None
        self._custom_skill_data_handler: CustomSkillClass | None = None
        self._cached_data: Any = None

        self.minimum_required_match = len(self.required_skills)
        self.tick_state = None
        self.current_target_id = 0
        self._was_in_aggro = False
        self._local_cast_timer = ThrottledTimer(0)
        self._local_cast_timer.Stop()
        self._auto_attack_timer = ThrottledTimer(0)
        self._auto_attack_timer.Stop()
        self._auto_attack_time = 0
        self._party_health_monitor: dict[int, dict[str, float]] = {}
        self._party_health_monitor_timer = ThrottledTimer(150)
        self._party_health_monitor_timer.Stop()
        self._party_health_monitor_window_ms = 1000

    def set_cached_data(self, cached_data: Any) -> None:
        """
        Optional hook for builds that need external cached runtime state.

        The base implementation stores the shared runtime cache so concrete
        builds can access HeroAI-backed helpers without reimplementing the hook.
        """
        self._cached_data = cached_data

    def GetEffectAndBuffIds(self, agent_id: int) -> list[int]:
        from HeroAI.utils import GetEffectAndBuffIds

        return GetEffectAndBuffIds(agent_id, cached_data=self._cached_data)
        
    def ValidatePrimary(self, profession: Profession) -> bool:
        return self.required_primary == profession

    def ValidateSecondary(self, profession: Profession) -> bool:
        return self.required_secondary == profession

    def _get_current_skills(self) -> list[int]:
        from Py4GWCoreLib.Skillbar import SkillBar

        skills: list[int] = []
        for i in range(8):
            skill = SkillBar.GetSkillIDBySlot(i + 1)
            if skill:
                skills.append(skill)
        return skills

    def ScoreMatch(
        self,
        current_primary=None,
        current_secondary=None,
        current_skills: list[int] | None = None,
    ) -> int:
        from Py4GWCoreLib import Player, Agent, Profession

        if current_primary is None or current_secondary is None:
            player_id = Player.GetAgentID()
            primary_value, secondary_value = Agent.GetProfessions(player_id)
            current_primary = current_primary if current_primary is not None else Profession(primary_value)
            current_secondary = current_secondary if current_secondary is not None else Profession(secondary_value)

        if current_skills is None:
            current_skills = self._get_current_skills()

        required_skills = [skill for skill in self.required_skills if skill]
        optional_skills = [skill for skill in self.optional_skills if skill and skill not in required_skills]
        current_skill_set = set(skill for skill in current_skills if skill)

        any_profession = Profession(0)
        primary_matches = self.required_primary in (any_profession, current_primary)
        secondary_matches = self.required_secondary in (any_profession, current_secondary)
        if not self.is_combat_automator_compatible or not primary_matches or not secondary_matches:
            return -1

        required_hits = sum(1 for skill in required_skills if skill in current_skill_set)
        minimum_required_hits = min(self.minimum_required_match, len(required_skills))
        if required_hits < minimum_required_hits:
            return -1

        optional_hits = sum(1 for skill in optional_skills if skill in current_skill_set)
        return required_hits + optional_hits

    def ValidateSkills(self) -> Generator[None, None, bool]:
        from Py4GWCoreLib import Routines
        skills = self._get_current_skills()

        all_valid = sorted(self.skills) == sorted(skills)

        if not all_valid:
            wait_interval = 1000
        else:
            wait_interval = 0
        yield from Routines.Yield.wait(wait_interval)
        return all_valid

    def SetFallback(self, fallback_name: str | None = None, fallback_handler: "BuildMgr | None" = None) -> None:
        self.current_fallback_name = fallback_name
        self.current_fallback_handler = fallback_handler

    def SetBlockedSkills(self, skill_ids: list[int] | None = None) -> None:
        self.blocked_skills = [int(skill_id) for skill_id in (skill_ids or []) if int(skill_id) != 0]

    def GetSupportedSkills(self) -> list[int]:
        supported_skills: list[int] = []
        for skill_id in self.required_skills + self.optional_skills:
            skill_id = int(skill_id)
            if skill_id == 0 or skill_id in supported_skills:
                continue
            supported_skills.append(skill_id)
        return supported_skills

    def GetBlockedSkills(self) -> list[int]:
        blocked_skills: list[int] = []
        for skill_id in self.GetSupportedSkills() + self.blocked_skills:
            skill_id = int(skill_id)
            if skill_id == 0 or skill_id in blocked_skills:
                continue
            blocked_skills.append(skill_id)
        return blocked_skills

    def ApplyBlockedSkillIDs(self, blocked_skill_ids: list[int] | None = None) -> None:
        pass

    def SetOOCFn(self, handler: BuildHandler | None) -> None:
        self._local_ooc_handler = handler

    def SetCombatFn(self, handler: BuildHandler | None) -> None:
        self._local_combat_handler = handler

    def SetSkillCastingFn(self, handler: BuildHandler | None) -> None:
        self._local_skill_casting_handler = handler

    def CanProcess(self) -> bool:
        from Py4GWCoreLib import Agent, Player, Routines

        return (
            Routines.Checks.Map.MapValid()
            and Routines.Checks.Map.IsExplorable()
            and Routines.Checks.Player.CanAct()
            and not Agent.IsDead(Player.GetAgentID())
        )

    def GetCustomSkill(self, skill_id: int) -> CustomSkill:
        from HeroAI.custom_skill import CustomSkillClass

        if self._custom_skill_data_handler is None:
            self._custom_skill_data_handler = CustomSkillClass()
        return self._custom_skill_data_handler.get_skill(skill_id)

    def GetEquippedSkillSlot(self, skill_id: int) -> int:
        from Py4GWCoreLib.Skillbar import SkillBar

        return int(SkillBar.GetSlotBySkillID(skill_id) or 0)

    def IsSkillEquipped(self, skill_id: int) -> bool:
        return 1 <= self.GetEquippedSkillSlot(skill_id) <= 8

    def GetEquippedCustomSkill(self, skill_id: int) -> CustomSkill | None:
        if not self.IsSkillEquipped(skill_id):
            return None
        return self.GetCustomSkill(skill_id)

    def _get_shared_skill_toggle(self, slot: int) -> bool:
        if not (1 <= int(slot) <= 8):
            return False

        options = getattr(self._cached_data, "account_options", None)
        if options is None:
            try:
                from Py4GWCoreLib import GLOBAL_CACHE, Player

                account_email = Player.GetAccountEmail()
                if account_email:
                    options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account_email)
            except Exception:
                options = None

        if options is None:
            return True

        skills = getattr(options, "Skills", None)
        if skills is None:
            return True

        try:
            return bool(skills[int(slot) - 1])
        except (IndexError, TypeError, ValueError):
            return True

    def IsSharedSkillToggleEnabled(self, slot: int) -> bool:
        return self._get_shared_skill_toggle(slot)
    
    def GetActiveScanRange(self) -> float:
        cached_data = getattr(self, "_cached_data", None)
        if cached_data is not None and hasattr(cached_data, "GetActiveScanRange"):
            return float(cached_data.GetActiveScanRange())
        
        try:
            from HeroAI.cache_data import CacheData
            cached_data = CacheData()
            cached_data.Update()
            return float(cached_data.GetActiveScanRange())
        except Exception:
            from Py4GWCoreLib import Range, Routines
            return Range.Spellcast.value if Routines.Checks.Agents.InAggro() else Range.Earshot.value
    
    def IsInAggro(self) -> bool:
        cached_data = getattr(self, "_cached_data", None)
        if cached_data is not None:
            data = getattr(cached_data, "data", None)
            if data is not None:
                return bool(data.in_aggro)
        
        from Py4GWCoreLib import Routines
        return bool(Routines.Checks.Agents.InAggro(self.GetActiveScanRange()))

    def IsCloseToAggro(self) -> bool:
        """Returns True when combat is imminent but the player is not yet engaged."""
        from Py4GWCoreLib import Routines
        return Routines.Checks.Agents.IsCloseToAggro()

    def ResolveAllyTarget(self, skill_id: int, custom_skill: CustomSkill | None = None) -> int:
        from HeroAI.targeting import (
            TargetAllyByPredicate,
            TargetLowestAlly,
            TargetLowestAllyCaster,
            TargetLowestAllyEnergy,
            TargetLowestAllyMartial,
            TargetLowestAllyMelee,
            TargetLowestAllyRanged,
            TargetAllyNonEnchanted,
            TargetAllyNonWeaponSpelled,
            TargetMinionNonEnchanted,
            TargetMinionOrAllyNonEnchanted,
            TargetDeadPartyMember,
        )
        from HeroAI.types import Skilltarget, SkillType
        from Py4GWCoreLib import Agent, AgentArray, Player, Routines, Skill

        if custom_skill is None:
            custom_skill = self.GetCustomSkill(skill_id)
        if custom_skill is None:
            return 0

        target_allegiance = custom_skill.TargetAllegiance
        targeting_strict = bool(custom_skill.Conditions.TargetingStrict)

        if target_allegiance == Skilltarget.MinionOrAllyNonEnchanted.value:
            return TargetMinionOrAllyNonEnchanted(filter_skill_id=skill_id)
        if target_allegiance == Skilltarget.MinionNonEnchanted.value:
            return TargetMinionNonEnchanted()
        if target_allegiance == Skilltarget.AllyNonEnchanted.value:
            return TargetAllyNonEnchanted()
        if target_allegiance == Skilltarget.NonWeaponSpelledAlly.value:
            return Player.GetAgentID() if TargetAllyNonWeaponSpelled() else 0

        if target_allegiance in (
            Skilltarget.Ally.value,
            Skilltarget.AllyCaster.value,
            Skilltarget.AllyMartial.value,
            Skilltarget.AllyMartialMelee.value,
            Skilltarget.AllyMartialRanged.value,
            Skilltarget.OtherAlly.value,
        ):
            base_predicate: TargetPredicate | None = None
            weapon_spell_predicate: TargetPredicate | None = None
            include_spirit_pets = False
            other_ally = target_allegiance == Skilltarget.OtherAlly.value
            base_target = 0
            if custom_skill.SkillType == SkillType.WeaponSpell.value:
                if custom_skill.Conditions.AllowOverlapWeaponSpell:
                    weapon_spell_predicate = lambda agent_id: not Routines.Checks.Agents.HasEffect(
                        agent_id,
                        skill_id,
                        exact_weapon_spell=True,
                    )
                else:
                    weapon_spell_predicate = lambda agent_id: not Routines.Checks.Agents.IsWeaponSpelled(agent_id)
            if target_allegiance == Skilltarget.Ally.value:
                base_target = TargetLowestAlly(other_ally=other_ally, filter_skill_id=skill_id)
            elif target_allegiance == Skilltarget.AllyCaster.value:
                base_target = TargetLowestAllyCaster(other_ally=other_ally, filter_skill_id=skill_id)
                base_predicate = lambda agent_id: Routines.Checks.Agents.IsCaster(agent_id)
            elif target_allegiance == Skilltarget.AllyMartial.value:
                base_target = TargetLowestAllyMartial(other_ally=other_ally, filter_skill_id=skill_id)
                base_predicate = lambda agent_id: Routines.Checks.Agents.IsMartial(agent_id)
                include_spirit_pets = True
            elif target_allegiance == Skilltarget.AllyMartialMelee.value:
                base_target = TargetLowestAllyMelee(other_ally=other_ally, filter_skill_id=skill_id)
                base_predicate = lambda agent_id: Routines.Checks.Agents.IsMelee(agent_id)
                include_spirit_pets = True
            elif target_allegiance == Skilltarget.AllyMartialRanged.value:
                base_target = TargetLowestAllyRanged(other_ally=other_ally, filter_skill_id=skill_id)
                base_predicate = lambda agent_id: Routines.Checks.Agents.IsRanged(agent_id)
            elif target_allegiance == Skilltarget.OtherAlly.value:
                base_target = TargetLowestAlly(other_ally=True, filter_skill_id=skill_id)

            if weapon_spell_predicate is not None:
                if base_predicate is None:
                    base_predicate = weapon_spell_predicate
                else:
                    prior_predicate = base_predicate
                    base_predicate = lambda agent_id: prior_predicate(agent_id) and weapon_spell_predicate(agent_id)

            if custom_skill.Conditions.LessEnergy > 0:
                return TargetLowestAllyEnergy(
                    other_ally=other_ally,
                    filter_skill_id=skill_id,
                    less_energy=custom_skill.Conditions.LessEnergy,
                )

            predicate = self._build_custom_skill_target_predicate(
                base_predicate=base_predicate,
                custom_skill=custom_skill,
            )
            if base_target and (predicate is None or predicate(base_target)):
                return base_target

            filtered_target = TargetAllyByPredicate(
                predicate=predicate,
                other_ally=other_ally,
                filter_skill_id=skill_id,
                include_spirit_pets=include_spirit_pets,
            )
            if filtered_target:
                return filtered_target

            if not targeting_strict and target_allegiance != Skilltarget.OtherAlly.value:
                return TargetLowestAlly(other_ally=other_ally, filter_skill_id=skill_id)
            return 0
        if target_allegiance == Skilltarget.DeadAlly.value:
            from Py4GWCoreLib.enums_src.GameData_enums import Range
            return Routines.Agents.GetDeadAlly(Range.Spellcast.value)
        if target_allegiance == Skilltarget.ResurrectionAlly.value:
            from Py4GWCoreLib.enums_src.GameData_enums import Range
            return Routines.Agents.GetResurrectionTarget(
                Range.Spellcast.value,
                reserve=True,
                skill_id=skill_id,
            )
        if target_allegiance == Skilltarget.Self.value:
            return Player.GetAgentID()

        return 0

    def ResolvePreferredAllyTarget(
        self,
        skill_id: int,
        custom_skill: CustomSkill | None = None,
        *,
        variants: list[CustomSkillMutator | None] | None = None,
        validator: TargetPredicate | None = None,
    ) -> int:
        if custom_skill is None:
            custom_skill = self.GetCustomSkill(skill_id)
        if custom_skill is None:
            return 0

        candidate_variants = list(variants or [])
        if not candidate_variants:
            candidate_variants = [None]

        for variant in candidate_variants:
            variant_skill = custom_skill if variant is None else deepcopy(custom_skill)
            if variant is not None:
                variant(variant_skill)

            target_agent_id = self.ResolveAllyTarget(skill_id, variant_skill)
            if not target_agent_id:
                continue
            if validator is not None and not validator(target_agent_id):
                continue
            return target_agent_id

        return 0

    def ResolvePreferredPartySpikeAllyTarget(
        self,
        skill_id: int,
        custom_skill: CustomSkill | None = None,
        *,
        variants: list[CustomSkillMutator | None] | None = None,
        validator: TargetPredicate | None = None,
        drop_threshold: float = 0.10,
        sample_interval_ms: int = 150,
        window_ms: int | None = None,
        force_sample: bool = False,
    ) -> int:
        from Py4GWCoreLib import Routines

        self.UpdatePartyHealthMonitor(
            sample_interval_ms=sample_interval_ms,
            window_ms=window_ms,
            force=force_sample,
        )

        def spike_validator(agent_id: int) -> bool:
            if not agent_id or not Routines.Checks.Agents.IsAlive(agent_id):
                return False
            if self.GetPartyHealthDelta(agent_id) < drop_threshold:
                return False
            if validator is not None and not validator(agent_id):
                return False
            return True

        return self.ResolvePreferredAllyTarget(
            skill_id,
            custom_skill,
            variants=variants,
            validator=spike_validator,
        )

    def ResolveRankedPartyAllyTarget(
        self,
        skill_id: int,
        custom_skill: CustomSkill | None = None,
        *,
        validator: TargetPredicate | None = None,
        rank_key: Callable[[int], Any] | None = None,
        sample_interval_ms: int = 150,
        window_ms: int | None = None,
        force_sample: bool = False,
    ) -> int:
        from Py4GWCoreLib import Range, Routines

        if custom_skill is None:
            custom_skill = self.GetCustomSkill(skill_id)
        if custom_skill is None:
            return 0

        self.UpdatePartyHealthMonitor(
            sample_interval_ms=sample_interval_ms,
            window_ms=window_ms,
            force=force_sample,
        )

        predicate = self._build_custom_skill_target_predicate(custom_skill=custom_skill)
        ally_array = list(Routines.Targeting.GetAllAlliesArray(Range.Spellcast.value) or [])
        candidates: list[int] = []

        for agent_id in ally_array:
            if not Routines.Checks.Agents.IsAlive(agent_id):
                continue
            if predicate is not None and not predicate(agent_id):
                continue
            if validator is not None and not validator(agent_id):
                continue
            candidates.append(agent_id)

        if not candidates:
            return 0

        if rank_key is None:
            rank_key = lambda agent_id: (
                Routines.Checks.Agents.GetHealth(agent_id),
                -self.GetPartyHealthDelta(agent_id),
            )

        candidates.sort(key=rank_key)
        return candidates[0]

    def _build_custom_skill_target_predicate(
        self,
        base_predicate: TargetPredicate | None = None,
        custom_skill: CustomSkill | None = None,
    ) -> TargetPredicate | None:
        from Py4GWCoreLib import Agent, Routines

        if custom_skill is None:
            return base_predicate

        conditions: CastConditions = custom_skill.Conditions
        checks: list[TargetPredicate] = []

        if base_predicate is not None:
            checks.append(base_predicate)

        if conditions.HasHex:
            checks.append(lambda agent_id: Routines.Checks.Agents.IsHexed(agent_id))
        if conditions.HasEnchantment:
            checks.append(lambda agent_id: Routines.Checks.Agents.IsEnchanted(agent_id))
        if conditions.HasWeaponSpell:
            checks.append(lambda agent_id: Routines.Checks.Agents.IsWeaponSpelled(agent_id))
        if conditions.HasCondition:
            checks.append(lambda agent_id: Routines.Checks.Agents.IsConditioned(agent_id))
        if conditions.IsAttacking:
            checks.append(lambda agent_id: Routines.Checks.Agents.IsAttacking(agent_id))
        if conditions.IsKnockedDown:
            checks.append(lambda agent_id: Routines.Checks.Agents.IsKnockedDown(agent_id))
        if conditions.IsAlive is False:
            checks.append(lambda agent_id: not Routines.Checks.Agents.IsAlive(agent_id))

        if not checks:
            return None

        return lambda agent_id: all(check(agent_id) for check in checks)

    def EvaluatePartyWideThreshold(self, skill_id: int, custom_skill: CustomSkill | None = None) -> bool:
        from HeroAI.targeting import GetAllAlliesArray
        from Py4GWCoreLib import AgentArray, Range, Routines

        if custom_skill is None:
            custom_skill = self.GetCustomSkill(skill_id)
        if custom_skill is None:
            return False

        conditions: CastConditions = custom_skill.Conditions
        if not conditions.IsPartyWide:
            return False

        area = conditions.PartyWideArea or Range.SafeCompass.value
        ally_array = GetAllAlliesArray(area)
        ally_array = AgentArray.Filter.ByCondition(
            ally_array,
            lambda agent_id: Routines.Checks.Agents.IsAlive(agent_id),
        )
        if not ally_array:
            return False

        total_group_life = 0.0
        for agent_id in ally_array:
            total_group_life += Routines.Checks.Agents.GetHealth(agent_id)

        average_group_life = total_group_life / len(ally_array)
        return average_group_life <= conditions.LessLife

    def RestoreEnemyTarget(self, target_agent_id: int):
        if False:
            yield

        from Py4GWCoreLib import Routines
        from Py4GWCoreLib.Agent import Agent
        from Py4GWCoreLib.Player import Player

        if not Agent.IsValid(target_agent_id) or Agent.IsDead(target_agent_id):
            return False

        _, allegiance = Agent.GetAllegiance(target_agent_id)
        if allegiance in ("Ally", "NPC/Minipet"):
            return False

        if Player.GetTargetID() != target_agent_id:
            yield from Routines.Yield.Agents.ChangeTarget(target_agent_id)
            return False

        return True

    def ResetTarget(self) -> None:
        self.current_target_id = 0

    def ResetPartyHealthMonitor(self) -> None:
        self._party_health_monitor.clear()
        self._party_health_monitor_timer.Stop()

    def _get_party_health_sample(self) -> list[int]:
        from Py4GWCoreLib import AgentArray, Range, Routines
        from Py4GWCoreLib.Agent import Agent

        # Routines.Targeting.GetAllAlliesArray() includes pets by merging the
        # filtered spirit/pet array and excluding spawned spirits.
        ally_array = Routines.Targeting.GetAllAlliesArray(Range.SafeCompass.value)
        ally_array = AgentArray.Filter.ByCondition(
            ally_array,
            lambda agent_id: Routines.Checks.Agents.IsAlive(agent_id),
        )
        return list(ally_array or [])

    def UpdatePartyHealthMonitor(
        self,
        *,
        sample_interval_ms: int = 150,
        window_ms: int | None = None,
        force: bool = False,
    ) -> dict[int, dict[str, float]]:
        from Py4GWCoreLib import Routines, Utils

        if window_ms is None:
            window_ms = self._party_health_monitor_window_ms
        window_ms = max(1, int(window_ms))
        self._party_health_monitor_window_ms = window_ms

        self._party_health_monitor_timer.SetThrottleTime(max(1, int(sample_interval_ms)))
        should_sample = force or self._party_health_monitor_timer.IsStopped() or self._party_health_monitor_timer.IsExpired()
        if not should_sample:
            return self._party_health_monitor

        now_ms = int(Utils.GetBaseTimestamp())
        ally_array = self._get_party_health_sample()
        active_agent_ids = set(ally_array)

        for agent_id in list(self._party_health_monitor.keys()):
            if agent_id not in active_agent_ids:
                del self._party_health_monitor[agent_id]

        for agent_id in ally_array:
            current_health = float(Routines.Checks.Agents.GetHealth(agent_id))
            previous_state = self._party_health_monitor.get(agent_id)
            previous_health = current_health if previous_state is None else float(previous_state.get("health", current_health))
            previous_sample_ms = now_ms if previous_state is None else int(previous_state.get("sample_ms", now_ms))
            previous_drop = 0.0 if previous_state is None else float(previous_state.get("drop", 0.0))
            elapsed_ms = max(0, now_ms - previous_sample_ms)
            current_drop = max(0.0, previous_health - current_health)

            if elapsed_ms >= window_ms:
                accumulated_drop = current_drop
            else:
                retention_ratio = max(0.0, float(window_ms - elapsed_ms) / float(window_ms))
                accumulated_drop = (previous_drop * retention_ratio) + current_drop

            self._party_health_monitor[agent_id] = {
                "health": current_health,
                "drop": max(0.0, min(1.0, accumulated_drop)),
                "sample_ms": now_ms,
            }

        self._party_health_monitor_timer.Reset()
        return self._party_health_monitor

    def GetPartyHealthDelta(self, agent_id: int) -> float:
        if not agent_id:
            return 0.0
        return float(self._party_health_monitor.get(agent_id, {}).get("drop", 0.0))

    def GetPartySpikeCandidates(
        self,
        *,
        drop_threshold: float = 0.10,
        sample_interval_ms: int = 150,
        window_ms: int | None = None,
        force_sample: bool = False,
    ) -> list[int]:
        from Py4GWCoreLib import Routines

        self.UpdatePartyHealthMonitor(
            sample_interval_ms=sample_interval_ms,
            window_ms=window_ms,
            force=force_sample,
        )

        candidates = [
            agent_id
            for agent_id, state in self._party_health_monitor.items()
            if float(state.get("drop", 0.0)) >= drop_threshold and Routines.Checks.Agents.IsAlive(agent_id)
        ]
        candidates.sort(
            key=lambda agent_id: (
                -self.GetPartyHealthDelta(agent_id),
                Routines.Checks.Agents.GetHealth(agent_id),
            )
        )
        return candidates

    def IsPartySpikeTarget(
        self,
        agent_id: int,
        *,
        drop_threshold: float = 0.10,
        sample_interval_ms: int = 150,
        window_ms: int | None = None,
        force_sample: bool = False,
    ) -> bool:
        from Py4GWCoreLib import Routines

        if not agent_id or not Routines.Checks.Agents.IsAlive(agent_id):
            return False

        self.UpdatePartyHealthMonitor(
            sample_interval_ms=sample_interval_ms,
            window_ms=window_ms,
            force=force_sample,
        )
        return self.GetPartyHealthDelta(agent_id) >= drop_threshold

    def _is_local_cast_pending(self) -> bool:
        if self._local_cast_timer.IsStopped():
            return False
        if self._local_cast_timer.IsExpired():
            self._local_cast_timer.Stop()
            return False
        return True

    def _mark_local_cast_pending(self, aftercast_delay: int) -> None:
        self._local_cast_timer.SetThrottleTime(max(0, int(aftercast_delay)))
        self._local_cast_timer.Reset()

    def _refresh_target_tracking(self) -> None:
        from Py4GWCoreLib import Routines

        in_aggro = self.IsInAggro()
        if self._was_in_aggro and not in_aggro:
            self.ResetTarget()
            self.ResetPartyHealthMonitor()
        self._was_in_aggro = in_aggro

    def _pick_clustered_target(
        self,
        cluster_radius: float,
        preferred_condition: Callable[[int], bool] | None = None,
        *,
        filter_radius: float | None = None,
    ) -> int:
        """Pick the enemy with the most direct neighbors within
        ``cluster_radius``.

        Candidate pool is enemies within ``filter_radius`` (defaults to
        ``cluster_radius``) of the player. When ``preferred_condition`` is
        provided, candidates are restricted to matches; if none match,
        returns 0 so the caller can drive its own fallback. Ties broken by
        distance to player.

        Suited to AoE-on-cast skills where the effect applies in a single
        radius around the cast target (e.g. Panic, Painful Bond, Cry of
        Frustration, Energy Surge).
        """
        from Py4GWCoreLib import Player, AgentArray, Utils
        from Py4GWCoreLib.Agent import Agent

        if cluster_radius <= 0:
            return 0

        effective_filter_radius = float(filter_radius if filter_radius is not None else cluster_radius)

        player_pos = Player.GetXY()
        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByDistance(enemy_array, player_pos, effective_filter_radius)
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsAlive(agent_id))
        if not enemy_array:
            return 0

        candidates = enemy_array
        if preferred_condition is not None:
            candidates = [agent_id for agent_id in enemy_array if preferred_condition(agent_id)]
            if not candidates:
                return 0

        scored = sorted(
            candidates,
            key=lambda c: (
                -self._count_nearby_enemies(c, cluster_radius),
                Utils.Distance(player_pos, Agent.GetXY(c)),
            ),
        )
        return scored[0]

    def _count_nearby_enemies(self, agent_id: int, cluster_radius: float) -> int:
        """Count alive enemies within ``cluster_radius`` of ``agent_id``,
        excluding ``agent_id`` itself. Returns 0 for invalid inputs.
        """
        from Py4GWCoreLib import AgentArray, Routines
        from Py4GWCoreLib.Agent import Agent

        if not agent_id or cluster_radius <= 0:
            return 0

        target_x, target_y = Agent.GetXY(agent_id)
        nearby = Routines.Agents.GetFilteredEnemyArray(target_x, target_y, cluster_radius)
        nearby = AgentArray.Filter.ByCondition(
            nearby,
            lambda nid: Agent.IsValid(nid) and not Agent.IsDead(nid),
        )
        return max(0, len(nearby) - 1)

    def _resolve_self_agent_id(self) -> int:
        """Resolve the running bot's effective self agent_id for ownership
        comparisons (e.g. ``Agent.GetOwnerID(spirit) == self_agent_id``).

        Tries the API first: shared-memory account broadcast for the
        running email, falling back to ``Player.GetAgentID()``. Then
        refines via observation: if alive nearby spirits all agree on a
        single non-zero ``owner_id``, that owner is us (since spirits
        record the caster's agent_id). This handles environments where
        the API returns an ID that differs from the engine's caster
        identity.

        Caches the resolved value on the instance once observation gives
        a definitive answer. Cache lives for the build's lifetime
        (BuildRegistry rebuilds builds on map change).
        """
        cached = getattr(self, "_resolved_self_agent_id", None)
        if cached:
            return cached

        from Py4GWCoreLib import AgentArray, GLOBAL_CACHE, Player, Range
        from Py4GWCoreLib.Agent import Agent

        account_email = Player.GetAccountEmail() or ""
        self_account = (
            GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email) if account_email else None
        )
        api_id = (
            int(self_account.AgentData.AgentID)
            if self_account is not None
            else Player.GetAgentID()
        )

        spirits = AgentArray.GetSpiritPetArray()
        spirits = AgentArray.Filter.ByDistance(spirits, Player.GetXY(), Range.Compass.value)
        spirits = AgentArray.Filter.ByCondition(
            spirits,
            lambda agent_id: Agent.IsAlive(agent_id),
        )
        owners = {Agent.GetOwnerID(s) for s in spirits}
        owners.discard(0)
        if len(owners) == 1:
            observed = next(iter(owners))
            self._resolved_self_agent_id = observed
            return observed

        return api_id

    def _prefer_melee_nearest_enemy(self, desired_target: int) -> int:
        from Py4GWCoreLib import Agent, Player, Range, Routines, Utils

        if not Routines.Checks.Agents.IsMelee(Player.GetAgentID()):
            return desired_target

        combat_distance = self.GetActiveScanRange()
        nearest_enemy = Routines.Agents.GetNearestEnemy(combat_distance)
        if not (Agent.IsValid(nearest_enemy) and not Agent.IsDead(nearest_enemy)):
            return desired_target

        if not (Agent.IsValid(desired_target) and not Agent.IsDead(desired_target)):
            return nearest_enemy

        player_pos = Player.GetXY()
        nearby_enemies = Routines.Agents.GetFilteredEnemyArray(
            player_pos[0],
            player_pos[1],
            combat_distance,
        )

        contact_enemies = [
            enemy_id
            for enemy_id in nearby_enemies
            if Agent.IsValid(enemy_id)
            and not Agent.IsDead(enemy_id)
            and Utils.Distance(player_pos, Agent.GetXY(enemy_id)) <= Range.Adjacent.value
        ]

        nearest_stable_enemy = 0
        for enemy_id in nearby_enemies:
            if Agent.IsMoving(enemy_id):
                continue
            nearest_stable_enemy = enemy_id
            break

        def _score_target(agent_id: int) -> float:
            if not (Agent.IsValid(agent_id) and not Agent.IsDead(agent_id)):
                return float("-inf")

            distance = Utils.Distance(player_pos, Agent.GetXY(agent_id))
            score = 0.0

            # Melee wants targets that are likely to let us connect and keep
            # swinging, not just the most "tactical" enemy on paper. We give a
            # large bonus to static targets, then a smaller bonus to targets
            # that are already close enough to hit without extra path churn.
            if not Agent.IsMoving(agent_id):
                score += 300.0
            if distance <= Range.Touch.value:
                score += 220.0
            elif distance <= Range.Adjacent.value:
                score += 120.0

            score -= distance * 0.25

            # Keep a light preference for the caller's desired target and for
            # the nearest enemy, but let stability/connectability outweigh
            # tactical desirability when melee would otherwise keep chasing.
            if agent_id == desired_target:
                score += 80.0
            if agent_id == nearest_enemy:
                score += 40.0

            return score

        if contact_enemies:
            # Once melee already has enemies in immediate reach, prefer targets in
            # that contact ring only. This prevents selecting a "better" target
            # behind a front enemy and failing skills because the front line body
            # blocks the path or keeps the character facing the wrong target.
            best_contact_target = max(contact_enemies, key=_score_target)
            return best_contact_target if _score_target(best_contact_target) != float("-inf") else desired_target

        candidates = [desired_target, nearest_enemy, nearest_stable_enemy]
        best_target = max(candidates, key=_score_target)
        return best_target if _score_target(best_target) != float("-inf") else desired_target
    
    def _pick_fallback_target(self, target_type: str) -> int:
        from HeroAI.targeting import GetEnemyAttacking, GetEnemyInjured, TargetClusteredEnemy
        from Py4GWCoreLib.Agent import Agent
        
        combat_distance = self.GetActiveScanRange()
        return_target = 0
        if target_type == "EnemyClustered":
            return_target = TargetClusteredEnemy(combat_distance)
            if not (Agent.IsValid(return_target) and not Agent.IsDead(return_target)):
                return_target = GetEnemyInjured(combat_distance)
        elif target_type == "EnemyHexedOrEnchantedClustered":
            return_target = self._pick_clustered_target(
                combat_distance,
                preferred_condition=lambda agent_id: Agent.IsHexed(agent_id) or Agent.IsEnchanted(agent_id),
            )
            if not (Agent.IsValid(return_target) and not Agent.IsDead(return_target)):
                return_target = GetEnemyInjured(combat_distance)
        elif target_type == "EnemyAttackingClustered":
            return_target = self._pick_clustered_target(
                combat_distance,
                preferred_condition=lambda agent_id: Agent.IsAttacking(agent_id),
            )
            if not (Agent.IsValid(return_target) and not Agent.IsDead(return_target)):
                return_target = GetEnemyInjured(combat_distance)
        elif target_type == "EnemyAttacking":
            return_target = GetEnemyAttacking(combat_distance)
            if not (Agent.IsValid(return_target) and not Agent.IsDead(return_target)):
                return_target = GetEnemyInjured(combat_distance)
                  
        elif target_type == "EnemyInjured":
            return_target = GetEnemyInjured(combat_distance)

        return_target = self._prefer_melee_nearest_enemy(return_target)

        if Agent.IsValid(return_target) and not Agent.IsDead(return_target):
            return return_target 
        return 0

    def _resolve_target(self, target_type: str = "EnemyInjured", show_log: bool = False) -> tuple[bool, bool]:
        from Py4GWCoreLib import Party, Agent, Player, Routines, Range, Utils
        party_target = Party.GetPartyTarget()
        self._debug(f"_acquire_target start current={self.current_target_id} party_target={party_target}", show_log)

        is_melee_player = Routines.Checks.Agents.IsMelee(Player.GetAgentID())
        player_pos = Player.GetXY()

        nearest_contact_enemy = 0
        if is_melee_player:
            nearby_enemies = Routines.Agents.GetFilteredEnemyArray(
                player_pos[0],
                player_pos[1],
                Range.Adjacent.value,
            )
            for enemy_id in nearby_enemies:
                if Agent.IsValid(enemy_id) and not Agent.IsDead(enemy_id):
                    nearest_contact_enemy = enemy_id
                    break

        # Party target is an explicit caller directive and must override every
        # other targeting heuristic. If one exists, stop here and use it.
        if Agent.IsValid(party_target) and not Agent.IsDead(party_target):
            desired_target = party_target
            target_source = "party"
        # Melee gets first claim on its current live target only when no party
        # target is set, so we do not repeatedly swap targets mid-approach as
        # fallback preferences refresh. But once an enemy is already in
        # immediate melee range, prefer that contact target over a farther
        # current target so skills do not keep failing on a body-blocked enemy
        # behind the front line.
        elif is_melee_player and Agent.IsValid(self.current_target_id) and not Agent.IsDead(self.current_target_id):
            current_target_distance = Utils.Distance(player_pos, Agent.GetXY(self.current_target_id))
            if nearest_contact_enemy and current_target_distance > Range.Adjacent.value:
                desired_target = self._prefer_melee_nearest_enemy(nearest_contact_enemy)
                target_source = "contact"
            else:
                desired_target = self.current_target_id
                target_source = "current"
        elif Agent.IsValid(self.current_target_id) and not Agent.IsDead(self.current_target_id):
            desired_target = self.current_target_id
            target_source = "current"
        else:
            desired_target = self._pick_fallback_target(target_type)
            target_source = "fallback"

        if Agent.IsValid(desired_target) and not Agent.IsDead(desired_target):
            target_changed = desired_target != self.current_target_id
            self.current_target_id = desired_target
            if target_changed:
                self._debug(f"Selected new {target_source} target {self.current_target_id}", show_log)
            else:
                self._debug(f"Keeping {target_source} target {self.current_target_id}", show_log)
            return True, target_changed

        self.current_target_id = 0
        self._debug("No valid target acquired", show_log)
        return False, False

    def AcquireTarget(
        self,
        target_type: str = "EnemyInjured",
        wait_ms: int = 100,
        show_debug: bool = False,
    ):
        if False:
            yield

        from Py4GWCoreLib import Player, Routines

        target_acquired, target_changed = self._resolve_target(target_type, show_log=show_debug)
        if not target_acquired:
            self._debug(f"Target acquisition failed, waiting {wait_ms}ms", show_debug)
            yield from Routines.Yield.wait(wait_ms)
            return False

        if target_changed or Player.GetTargetID() != self.current_target_id:
            self._debug(
                f"Settling target desired={self.current_target_id} "
                f"player_target={Player.GetTargetID()} changed={target_changed}",
                show_debug,
            )
            yield from Routines.Yield.Agents.ChangeTarget(self.current_target_id)
            return False

        return True

    def GetWeaponAttackAftercast(self) -> int:
        from Py4GWCoreLib import Agent, Player
        from Py4GWCoreLib.enums import Weapon

        weapon_type, _ = Agent.GetWeaponType(Player.GetAgentID())
        player_living = Agent.GetLivingAgentByID(Player.GetAgentID())
        if player_living is None:
            return 0

        attack_speed = player_living.weapon_attack_speed
        attack_speed_modifier = player_living.attack_speed_modifier if player_living.attack_speed_modifier != 0 else 1.0

        if attack_speed == 0:
            match weapon_type:
                case Weapon.Bow.value:
                    attack_speed = 2.475
                case Weapon.Axe.value:
                    attack_speed = 1.33
                case Weapon.Hammer.value:
                    attack_speed = 1.75
                case Weapon.Daggers.value:
                    attack_speed = 1.33
                case Weapon.Scythe.value:
                    attack_speed = 1.5
                case Weapon.Spear.value:
                    attack_speed = 1.5
                case Weapon.Sword.value:
                    attack_speed = 1.33
                case Weapon.Scepter.value:
                    attack_speed = 1.75
                case Weapon.Scepter2.value:
                    attack_speed = 1.75
                case Weapon.Wand.value:
                    attack_speed = 1.75
                case Weapon.Staff1.value:
                    attack_speed = 1.75
                case Weapon.Staff.value:
                    attack_speed = 1.75
                case Weapon.Staff2.value:
                    attack_speed = 1.75
                case Weapon.Staff3.value:
                    attack_speed = 1.75
                case _:
                    attack_speed = 1.75

        return int((attack_speed / attack_speed_modifier) * 1000)

    def ResetAutoAttack(self) -> None:
        self._auto_attack_time = 0
        self._auto_attack_timer.Stop()

    def _refresh_auto_attack_timing(self) -> None:
        self._auto_attack_time = max(0, int(self.GetWeaponAttackAftercast()))

    def _need_auto_attack_reissue(self) -> bool:
        from Py4GWCoreLib import Agent, Player

        target_id = Player.GetTargetID()
        _, target_allegiance = Agent.GetAllegiance(target_id)
        if target_id == 0 or Agent.IsDead(target_id) or target_allegiance != "Enemy":
            return True

        if self._auto_attack_timer.IsStopped():
            return True

        return self._auto_attack_timer.IsExpired()

    def AutoAttack(self, target_type: str = "EnemyInjured", show_debug: bool = False) -> BuildCoroutine:
        if False:
            yield

        from Py4GWCoreLib import Agent, Player, Routines

        player_id = Player.GetAgentID()
        if not self.CanProcess() or self._is_local_cast_pending() or Agent.IsHoldingItem(player_id):
            return False

        self._refresh_auto_attack_timing()
        if not self._need_auto_attack_reissue():
            return False

        target_acquired, target_changed = self._resolve_target(target_type, show_log=show_debug)
        if not target_acquired:
            return False

        if target_changed or Player.GetTargetID() != self.current_target_id:
            yield from Routines.Yield.Agents.ChangeTarget(self.current_target_id)

        Player.Interact(self.current_target_id, False)
        self._refresh_auto_attack_timing()
        self._auto_attack_timer.SetThrottleTime(max(0, self._auto_attack_time))
        self._auto_attack_timer.Reset()
        return True
    

    def _resolve_extra_condition(self, extra_condition: bool | Callable[[], bool]) -> bool:
        if callable(extra_condition):
            return bool(extra_condition())
        return bool(extra_condition)

    def _is_spirit_skill(self, skill_id: int) -> bool:
        from Py4GWCoreLib.enums import SPIRIT_BUFF_MAP

        return int(skill_id) in set(SPIRIT_BUFF_MAP.values())

    def SpiritBuffExists(self, skill_id: int) -> bool:
        from Py4GWCoreLib import Agent, AgentArray, Player, Range, SpiritModelID
        from Py4GWCoreLib.enums import SPIRIT_BUFF_MAP

        if not self._is_spirit_skill(skill_id):
            return False

        # Allow the skill's metadata to request HP-aware recast: when the spirit's
        # current HP fraction drops below `AllowRecastAtLife`, treat it
        # as absent so the caller can refresh before the spirit naturally dies.
        # 0.0 (default) keeps the pre-change binary alive/dead gate.
        min_hp_fraction = 0.0
        try:
            custom_skill = self.GetCustomSkill(skill_id)
            if custom_skill is not None:
                min_hp_fraction = float(custom_skill.Conditions.AllowRecastAtLife or 0.0)
        except Exception:
            min_hp_fraction = 0.0

        spirit_array = AgentArray.GetSpiritPetArray()
        spirit_array = AgentArray.Filter.ByDistance(spirit_array, Player.GetXY(), Range.Earshot.value)
        spirit_array = AgentArray.Filter.ByCondition(spirit_array, lambda agent_id: Agent.IsAlive(agent_id))

        for spirit_id in spirit_array:
            model_value = Agent.GetPlayerNumber(spirit_id)
            if model_value not in SpiritModelID._value2member_map_:
                continue

            spirit_model_id = SpiritModelID(model_value)
            if SPIRIT_BUFF_MAP.get(spirit_model_id) == skill_id:
                if min_hp_fraction > 0.0 and Agent.GetHealth(spirit_id) < min_hp_fraction:
                    continue
                return True

        return False

    def _get_spirit_cast_wait_ms(self, skill_id: int, aftercast_delay: int) -> int:
        from Py4GWCoreLib import GLOBAL_CACHE

        activation_ms = int(max(0.0, GLOBAL_CACHE.Skill.Data.GetActivation(skill_id)) * 1000)
        intrinsic_aftercast_ms = int(max(0.0, GLOBAL_CACHE.Skill.Data.GetAftercast(skill_id)) * 1000)
        return max(int(aftercast_delay), activation_ms + intrinsic_aftercast_ms + 100)

    def _candidate_overlaps_spirit(self, x: float, y: float, min_distance: float) -> bool:
        from Py4GWCoreLib import Agent, AgentArray

        spirit_array = AgentArray.GetSpiritPetArray()
        spirit_array = AgentArray.Filter.ByDistance(spirit_array, (x, y), min_distance)
        spirit_array = AgentArray.Filter.ByCondition(spirit_array, lambda agent_id: Agent.IsAlive(agent_id))
        spirit_array = AgentArray.Filter.ByCondition(spirit_array, lambda agent_id: Agent.IsSpawned(agent_id))
        return bool(spirit_array)

    def _pick_spirit_stepaway_position(self, distance: float) -> tuple[float, float] | None:
        from Py4GWCoreLib import Player, Range

        player_x, player_y = Player.GetXY()
        directions = [i * (math.pi / 4.0) for i in range(8)]
        random.shuffle(directions)

        for angle in directions:
            candidate_x = player_x + math.cos(angle) * distance
            candidate_y = player_y + math.sin(angle) * distance
            if not self._candidate_overlaps_spirit(candidate_x, candidate_y, Range.Touch.value):
                return candidate_x, candidate_y

        fallback_angle = random.uniform(0.0, math.tau)
        return (
            player_x + math.cos(fallback_angle) * distance,
            player_y + math.sin(fallback_angle) * distance,
        )

    def _pick_spirit_precast_position(self, distance: float) -> tuple[float, float] | None:
        from Py4GWCoreLib import Agent, Player

        player_agent_id = Player.GetAgentID()
        player_x, player_y = Player.GetXY()
        facing = Agent.GetRotationAngle(player_agent_id)

        candidate_angles = [
            facing + math.pi,
            facing + math.pi + (math.pi / 6.0),
            facing + math.pi - (math.pi / 6.0),
            facing + math.pi + (math.pi / 3.0),
            facing + math.pi - (math.pi / 3.0),
        ]

        for angle in candidate_angles:
            candidate_x = player_x + math.cos(angle) * distance
            candidate_y = player_y + math.sin(angle) * distance
            if not self._candidate_overlaps_spirit(candidate_x, candidate_y, distance):
                return candidate_x, candidate_y

        return None

    def _move_for_spirit_cast(self):
        if False:
            yield

        from Py4GWCoreLib import Player, Range, Routines

        destination = self._pick_spirit_precast_position(Range.Touch.value)
        if destination is None:
            return False

        Player.Move(destination[0], destination[1])
        yield from Routines.Yield.wait(300)
        return True

    def _wait_for_spirit_spawn_and_step_away(self, skill_id: int, spawn_timeout_ms: int = 1000):
        if False:
            yield

        from Py4GWCoreLib import Player, Range, Routines

        elapsed_ms = 0
        poll_ms = 100
        while elapsed_ms < max(poll_ms, int(spawn_timeout_ms)):
            if self.SpiritBuffExists(skill_id):
                break
            yield from Routines.Yield.wait(poll_ms)
            elapsed_ms += poll_ms
        else:
            return False

        destination = self._pick_spirit_stepaway_position(Range.Touch.value)
        if destination is None:
            return False

        Player.Move(destination[0], destination[1])
        yield from Routines.Yield.wait(300)
        return True

    def _yield_from_handler(self, handler: BuildHandler | None) -> BuildCoroutine:
        if handler is None:
            yield
            return None

        result = handler()
        if inspect.isgenerator(result):
            return (yield from result)
        return result

    def _process_phase(self, handler: BuildHandler | None, is_in_combat: bool) -> BuildCoroutine:
        # Whiteboard owner self-clear — release my (skill, target) slots on
        # the cast-finish transition so sibling accounts can reuse them
        # immediately. Lives here (not in Tick) because HeroAI's BT path
        # calls ProcessCombat/ProcessOOC directly and bypasses Tick.
        self._whiteboard_owner_self_clear()
        if not self.CanProcess():
            reasons: list[str] = []
            from Py4GWCoreLib import Agent, Player, Routines

            if not Routines.Checks.Map.MapValid():
                reasons.append("map invalid")
            if not Routines.Checks.Map.IsExplorable():
                reasons.append("not explorable")
            if not Routines.Checks.Player.CanAct():
                reasons.append("player cannot act")
            if Agent.IsDead(Player.GetAgentID()):
                reasons.append("player dead")
            if not reasons:
                reasons.append("unknown")
            yield
            return

        self.ResetTickState()
        self._refresh_target_tracking()
        yield from self._yield_from_handler(handler)

        if self.DidTickSucceed():
            return

        fallback = self.ResolveFallback()
        if fallback is not None:
            if is_in_combat:
                yield from fallback.ProcessCombat()
            else:
                yield from fallback.ProcessOOC()
            return

        yield

    def _process_skill_casting_phase(
        self,
        handler: BuildHandler | None,
        is_in_combat: bool | None = None,
    ) -> BuildCoroutine:
        self._whiteboard_owner_self_clear()
        if not self.CanProcess():
            yield
            return

        self.ResetTickState()
        self._refresh_target_tracking()
        handler_result = yield from self._yield_from_handler(handler)

        if self.DidTickSucceed():
            return

        if handler_result is True:
            self.SetTickSuccess()
            return

        fallback = self.ResolveFallback()
        if fallback is not None:
            if is_in_combat is True:
                yield from fallback.ProcessCombat()
            elif is_in_combat is False:
                yield from fallback.ProcessOOC()
            else:
                yield from fallback.ProcessSkillCasting()
            return

        yield

    def _apply_fallback_skill_mask(self, fallback_handler: "BuildMgr | None") -> None:
        if fallback_handler is None:
            return
        fallback_handler.ApplyBlockedSkillIDs(self.GetBlockedSkills())

    def ResetFallback(self) -> None:
        self.current_fallback_name = self.default_fallback_name
        self.current_fallback_handler = self.default_fallback_handler

    def ResolveFallback(self) -> "BuildMgr | None":
        if self.current_fallback_handler is not None:
            self._apply_fallback_skill_mask(self.current_fallback_handler)
            return self.current_fallback_handler
        return None

    def set_fsm(self, fsm) -> None:
        pass

    def set_bot(self, bot) -> None:
        pass

    def set_debug_fn(self, fn: Callable[[], bool]) -> None:
        pass

    def ResetTickState(self) -> None:
        self.tick_state = None

    def SetTickSuccess(self) -> None:
        from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree

        self.tick_state = BehaviorTree.NodeState.SUCCESS

    def SetTickFailure(self) -> None:
        from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree

        self.tick_state = BehaviorTree.NodeState.FAILURE

    def DidTickSucceed(self) -> bool:
        return getattr(self.tick_state, "name", None) == "SUCCESS"

    def _validate_target_for_skill_cast(self, skill_id: int, target_agent_id: int) -> bool:
        from HeroAI.types import Skilltarget, SkillType
        from Py4GWCoreLib import Routines

        if not target_agent_id:
            return True

        custom_skill = self.GetCustomSkill(skill_id)
        if custom_skill is None:
            return True

        target_allegiance = custom_skill.TargetAllegiance
        if target_allegiance == Skilltarget.NonWeaponSpelledAlly.value:
            from HeroAI.targeting import TargetAllyNonWeaponSpelled

            return bool(TargetAllyNonWeaponSpelled())

        if target_allegiance == Skilltarget.AllyCaster.value:
            if (
                not Routines.Checks.Agents.IsCaster(target_agent_id)
                or Routines.Checks.Agents.IsMartial(target_agent_id)
            ):
                return False
        elif target_allegiance == Skilltarget.AllyMartial.value:
            if (
                not Routines.Checks.Agents.IsMartial(target_agent_id)
            ):
                return False
        elif target_allegiance == Skilltarget.AllyMartialMelee.value:
            if (
                not Routines.Checks.Agents.IsMelee(target_agent_id)
            ):
                return False
        elif target_allegiance == Skilltarget.AllyMartialRanged.value:
            if not Routines.Checks.Agents.IsRanged(target_agent_id):
                return False

        if custom_skill.SkillType == SkillType.WeaponSpell.value:
            if custom_skill.Conditions.AllowOverlapWeaponSpell:
                if Routines.Checks.Agents.HasEffect(target_agent_id, skill_id, exact_weapon_spell=True):
                    return False
            elif Routines.Checks.Agents.IsWeaponSpelled(target_agent_id):
                return False

        return True

    #region Whiteboard (cross-hero cast-intent coordination)
    def _is_whiteboard_skill(self, skill_id: int) -> bool:
        """True iff this skill opts into cross-hero whiteboard coordination,
        via either CustomSkill.CoordinatesViaWhiteboard or the shared
        Py4GWCoreLib.Builds.Skills._whiteboard registry.
        """
        if skill_id <= 0:
            return False
        # Lazy import — avoid a circular load of the Builds package during
        # BuildMgr's own module initialization.
        try:
            from Py4GWCoreLib.Builds.Skills._whiteboard import is_registered as _wb_is_registered
            if _wb_is_registered(skill_id):
                return True
        except Exception:
            pass
        try:
            custom = self.GetCustomSkill(skill_id)
            return bool(getattr(custom, "CoordinatesViaWhiteboard", False))
        except Exception:
            return False

    def _whiteboard_is_claimed(self, skill_id: int, target_agent_id: int) -> bool:
        """Read-gate: True if another account in my IsolationGroupID holds an
        unexpired (skill_id, target_agent_id) claim. Failures fall back to
        False so a broken ShMem path never blocks casting.
        """
        if skill_id <= 0 or target_agent_id <= 0:
            return False
        try:
            from Py4GWCoreLib import GLOBAL_CACHE, Player
            email = Player.GetAccountEmail() or ""
            if not email:
                return False
            group_id = GLOBAL_CACHE.ShMem.GetAccountGroupByEmail(email)
            now = Py4GW.Game.get_tick_count64()
            return GLOBAL_CACHE.ShMem.IsIntentClaimed(
                int(skill_id),
                int(target_agent_id),
                int(group_id),
                email,
                int(now),
            )
        except Exception:
            return False

    def _whiteboard_post_intent(self, skill_id: int, target_agent_id: int) -> None:
        """Claim (skill_id, target_agent_id) just before the cast commits."""
        if skill_id <= 0 or target_agent_id <= 0:
            return
        try:
            from Py4GWCoreLib import GLOBAL_CACHE, Player
            from Py4GWCoreLib.GlobalCache.shared_memory_src.Globals import (
                SHMEM_INTENT_DEFAULT_PING_BUDGET_MS,
            )
            email = Player.GetAccountEmail() or ""
            if not email:
                return
            activation_ms = 0
            aftercast_ms = 0
            try:
                activation_ms = int((GLOBAL_CACHE.Skill.Data.GetActivation(skill_id) or 0) * 1000)
            except Exception:
                pass
            try:
                aftercast_ms = int((GLOBAL_CACHE.Skill.Data.GetAftercast(skill_id) or 0) * 1000)
            except Exception:
                pass
            cast_window_ms = max(500, activation_ms + aftercast_ms)
            now = Py4GW.Game.get_tick_count64()
            expires_at = int(now) + cast_window_ms + int(SHMEM_INTENT_DEFAULT_PING_BUDGET_MS)
            GLOBAL_CACHE.ShMem.PostIntent(
                email, int(skill_id), int(target_agent_id), int(expires_at)
            )
            self._wb_posted_this_cast = True
        except Exception:
            pass

    def _whiteboard_owner_self_clear(self) -> None:
        """On the local-cast-pending True->False transition, zero my intent
        slots so sibling accounts can reuse the (skill, target) immediately.
        """
        try:
            pending = self._is_local_cast_pending()
            prev = getattr(self, "_wb_prev_cast_pending", False)
            self._wb_prev_cast_pending = pending
            if not (prev and not pending):
                return
            if not getattr(self, "_wb_posted_this_cast", False):
                return
            from Py4GWCoreLib import GLOBAL_CACHE, Player
            email = Player.GetAccountEmail() or ""
            if email:
                GLOBAL_CACHE.ShMem.ClearIntentsByOwner(email)
            self._wb_posted_this_cast = False
        except Exception:
            pass

    def CanCastSkillID(
        self,
        skill_id: int,
        extra_condition: bool | Callable[[], bool] = True,
    ) -> bool:
        from Py4GWCoreLib import Player, Routines, SkillBar

        if not Routines.Checks.Map.IsExplorable():
            return False
        if self._is_local_cast_pending():
            return False
        if not self._resolve_extra_condition(extra_condition):
            return False
        if not Routines.Checks.Skills.HasEnoughEnergy(Player.GetAgentID(), skill_id):
            return False
        if not Routines.Checks.Skills.IsSkillIDReady(skill_id):
            return False

        slot = SkillBar.GetSlotBySkillID(skill_id)
        if not (1 <= slot <= 8):
            return False
        if not self.IsSharedSkillToggleEnabled(slot):
            return False
        if not Routines.Checks.Skills.HasEnoughAdrenalineBySlot(slot):
            return False
        if self.SpiritBuffExists(skill_id):
            return False

        return True

    def CanCastSkillSlot(
        self,
        slot: int,
        extra_condition: bool | Callable[[], bool] = True,
    ) -> bool:
        from Py4GWCoreLib import Player, Routines, SkillBar

        if not Routines.Checks.Map.IsExplorable():
            return False
        if not (1 <= slot <= 8):
            return False
        if self._is_local_cast_pending():
            return False
        if not self._resolve_extra_condition(extra_condition):
            return False

        skill_id = SkillBar.GetSkillIDBySlot(slot)
        if not skill_id:
            return False
        if not self.IsSharedSkillToggleEnabled(slot):
            return False
        if not Routines.Checks.Skills.HasEnoughEnergy(Player.GetAgentID(), skill_id):
            return False
        if not Routines.Checks.Skills.IsSkillSlotReady(slot):
            return False
        if not Routines.Checks.Skills.HasEnoughAdrenalineBySlot(slot):
            return False
        if self.SpiritBuffExists(skill_id):
            return False

        return True

    def CastSkillID(
        self,
        skill_id: int,
        extra_condition: bool | Callable[[], bool] = True,
        log: bool = False,
        aftercast_delay: int = 1000,
        target_agent_id: int = 0,
    ):
        from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, ConsoleLog, Console, SkillBar
        if False:
            yield

        if not self.CanCastSkillID(skill_id, extra_condition=extra_condition):
            return False
        if not self._validate_target_for_skill_cast(skill_id, target_agent_id):
            return False

        # Interrupt feasibility gate — only for skills classified as
        # SkillNature.Interrupt in HeroAI/custom_skill_src/. Non-interrupts
        # short-circuit on the registry lookup with zero further work.
        # Lazy import keeps BuildMgr independent at module load; HeroAI
        # pushes the gate down via the registry.
        try:
            from HeroAI.interrupt import (
                is_classified_as_interrupt,
                is_interrupt_feasible,
                _get_player_fast_casting_level,
                _PING_HANDLER as _RUPT_PING_HANDLER,
                _queue_outcome,
            )
            if target_agent_id and is_classified_as_interrupt(skill_id):
                from Py4GWCoreLib.Agent import Agent as _RuptAgent
                if not is_interrupt_feasible(
                    target_agent_id=target_agent_id,
                    our_skill_id=skill_id,
                    fast_casting_level=_get_player_fast_casting_level(),
                    ping_ms=int(_RUPT_PING_HANDLER.GetCurrentPing()),
                ):
                    return False
                _queue_outcome(
                    target_agent_id,
                    _RuptAgent.GetCastingSkillID(target_agent_id),
                    skill_id,
                )
        except Exception:
            # Never let a feasibility-helper bug block casting. Legacy
            # behavior (no feasibility gate) is the safe fallback.
            pass

        # Whiteboard read gate — skip if another hero in my isolation group
        # already claimed this (skill_id, target_agent_id). Opt-in per skill.
        if self._is_whiteboard_skill(skill_id) and self._whiteboard_is_claimed(skill_id, target_agent_id):
            return False

        slot = SkillBar.GetSlotBySkillID(skill_id)

        # Whiteboard write — claim (skill_id, target_agent_id) so other heroes
        # in my isolation group skip this combo until my cast resolves.
        if self._is_whiteboard_skill(skill_id):
            self._whiteboard_post_intent(skill_id, target_agent_id)

        GLOBAL_CACHE.SkillBar.UseSkill(slot, target_agent_id=target_agent_id, aftercast_delay=aftercast_delay)
        self._mark_local_cast_pending(aftercast_delay)
        if self._is_spirit_skill(skill_id):
            yield from Routines.Yield.wait(self._get_spirit_cast_wait_ms(skill_id, aftercast_delay))
            yield from self._wait_for_spirit_spawn_and_step_away(skill_id)
        if log:
            ConsoleLog("CastSkillID", f"Cast {GLOBAL_CACHE.Skill.GetName(skill_id)}, slot: {slot}", Console.MessageType.Info, log=log)
        self.SetTickSuccess()

        return True

    def CastSkillIDAndRestoreTarget(
        self,
        skill_id: int,
        target_agent_id: int,
        *,
        extra_condition: bool | Callable[[], bool] = True,
        log: bool = False,
        aftercast_delay: int = 250,
    ):
        from Py4GWCoreLib.Player import Player
        if False:
            yield

        if not target_agent_id:
            return False
        if not self.CanCastSkillID(skill_id, extra_condition=extra_condition):
            return False

        previous_enemy_target = Player.GetTargetID()
        if (yield from self.CastSkillID(
            skill_id=skill_id,
            extra_condition=extra_condition,
            log=log,
            aftercast_delay=aftercast_delay,
            target_agent_id=target_agent_id,
        )):
            yield from self.RestoreEnemyTarget(previous_enemy_target)
            return True

        return False

    def CastSpiritSkillID(
        self,
        skill_id: int,
        extra_condition: bool | Callable[[], bool] = True,
        log: bool = False,
        aftercast_delay: int = 1000,
    ):
        if False:
            yield

        if not self._is_spirit_skill(skill_id):
            return (yield from self.CastSkillID(
                skill_id=skill_id,
                extra_condition=extra_condition,
                log=log,
                aftercast_delay=aftercast_delay,
            ))

        # yield from self._move_for_spirit_cast()
        #
        # Pre-cast positioning disabled. Previously this path ran the line
        # above, which issued Player.Move and interrupted any in-progress
        # cast. When the player had not yet arrived at the destination by
        # the time UseSkill ran, the cast silently failed - leaving the
        # caster stuck in a cast-retry + reposition loop while HeroAI's
        # follow behavior pulled them back. Post-cast step-away inside
        # CastSkillID still runs and keeps the caster from standing inside
        # the new spirit after it has actually spawned.
        #
        # The helpers _move_for_spirit_cast and _pick_spirit_precast_position
        # are intentionally left in place. They do semi-work today (the move
        # happens, the candidate search runs) but are mis-timed: the cast is
        # fired before the player arrives at the destination, so the spirit
        # spawns at an intermediate position or not at all. They can be re-
        # enabled by uncommenting the line above after fixing the timing
        # (arrival poll on Player.Move, widening the candidate search to
        # avoid dead-ends in crowded spirit clusters, and decoupling the
        # move-distance from the overlap radius).
        return (yield from self.CastSkillID(
            skill_id=skill_id,
            extra_condition=extra_condition,
            log=log,
            aftercast_delay=aftercast_delay,
            target_agent_id=0,
        ))

    def CastSkillSlot(
        self,
        slot: int,
        extra_condition: bool | Callable[[], bool] = True,
        log: bool = True,
        aftercast_delay: int = 1000,
        target_agent_id: int = 0,
    ):
        from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, ConsoleLog, Console, SkillBar
        if False:
            yield

        if not self.CanCastSkillSlot(slot, extra_condition=extra_condition):
            return False

        skill_id = SkillBar.GetSkillIDBySlot(slot)
        if not self._validate_target_for_skill_cast(skill_id, target_agent_id):
            return False

        GLOBAL_CACHE.SkillBar.UseSkill(slot, target_agent_id=target_agent_id, aftercast_delay=aftercast_delay)
        self._mark_local_cast_pending(aftercast_delay)
        if self._is_spirit_skill(skill_id):
            yield from Routines.Yield.wait(self._get_spirit_cast_wait_ms(skill_id, aftercast_delay))
            yield from self._wait_for_spirit_spawn_and_step_away(skill_id)
        if log:
            ConsoleLog("CastSkillSlot", f"Cast {GLOBAL_CACHE.Skill.GetName(skill_id)}, slot: {slot}", Console.MessageType.Info, log=log)
        self.SetTickSuccess()

        return True


    def ProcessSkillCasting(self) -> BuildCoroutine:
        if self._local_skill_casting_handler is not None:
            yield from self._process_skill_casting_phase(self._local_skill_casting_handler)
            return

        if self._local_ooc_handler is None and self._local_combat_handler is None:
            raise NotImplementedError

        from Py4GWCoreLib.botting_src.helpers_src.HeroAICombatRange import hero_ai_combat_detected

        if hero_ai_combat_detected():
            yield from self.ProcessCombat()
        else:
            yield from self.ProcessOOC()

    def ProcessOOC(self) -> BuildCoroutine:
        if self._local_ooc_handler is None:
            yield from self.ProcessSkillCasting()
            return
        yield from self._process_phase(self._local_ooc_handler, is_in_combat=False)

    def ProcessCombat(self) -> BuildCoroutine:
        if self._local_combat_handler is None:
            yield from self.ProcessSkillCasting()
            return
        yield from self._process_phase(self._local_combat_handler, is_in_combat=True)

    def Tick(self, is_in_combat: bool):
        # Clear whiteboard intent slots on the cast-finish transition so
        # sibling accounts can reuse the (skill, target) as soon as my
        # local cast window has closed.
        self._whiteboard_owner_self_clear()
        if is_in_combat:
            yield from self.ProcessCombat()
        else:
            yield from self.ProcessOOC()
    
    def LoadSkillBar(self) -> Generator[Any, Any, None]:
        from Py4GWCoreLib import Routines
        """
        Load the skill bar with the build's template code.
        This method can be overridden in child classes if needed.
        """
        yield from Routines.Yield.Skills.LoadSkillbar(self.template_code, log=False)
        
    def _debug(self,message: str, enable: bool = True) -> None:
        from Py4GWCoreLib import ConsoleLog
        import Py4GW
        ConsoleLog(self.build_name, message, Py4GW.Console.MessageType.Info, log=enable)


#region BuildRegistry
class BuildRegistry:
    _cached_build_types: list[type[BuildMgr]] | None = None

    def __init__(self, default_fallback_name: str | None = None, build_init_kwargs: dict[str, Any] | None = None):
        self.default_fallback_name = default_fallback_name
        self.build_init_kwargs = dict(build_init_kwargs or {})
        self._runtime_build_instances: dict[type[BuildMgr], BuildMgr | None] = {}
        self._match_only_build_instances: dict[type[BuildMgr], BuildMgr | None] = {}
        self._cached_runtime_builds: list[BuildMgr] | None = None
        self._cached_match_only_builds: list[BuildMgr] | None = None
        self._cached_runtime_matchable_builds: list[BuildMgr] | None = None
        self._cached_match_only_matchable_builds: list[BuildMgr] | None = None
        self._cached_runtime_fallback_builds: list[BuildMgr] | None = None
        self._cached_match_only_fallback_builds: list[BuildMgr] | None = None

    @classmethod
    def _scan_build_types(cls) -> list[type[BuildMgr]]:
        builds_pkg = importlib.import_module("Py4GWCoreLib.Builds")
        build_types: list[type[BuildMgr]] = []

        seen_module_names: set[str] = set()
        for module_path in Path(builds_pkg.__path__[0]).rglob("*.py"):
            if module_path.name == "__init__.py":
                continue

            relative_path = module_path.relative_to(builds_pkg.__path__[0]).with_suffix("")
            module_name = ".".join((builds_pkg.__name__, *relative_path.parts))
            if module_name in seen_module_names:
                continue
            seen_module_names.add(module_name)

            module = importlib.import_module(module_name)
            for _, value in inspect.getmembers(module, inspect.isclass):
                if value is BuildMgr:
                    continue
                if value.__module__ != module.__name__:
                    continue
                if not issubclass(value, BuildMgr):
                    continue
                build_types.append(value)

        return build_types

    @classmethod
    def GetBuildTypes(cls) -> list[type[BuildMgr]]:
        if cls._cached_build_types is None:
            cls._cached_build_types = cls._scan_build_types()
        return list(cls._cached_build_types)

    @classmethod
    def ClearCache(cls) -> None:
        cls._cached_build_types = None

    def _call_build_ctor(self, build_type: type[BuildMgr], *args: Any, **kwargs: Any) -> BuildMgr | None:
        try:
            ctor = cast(Any, build_type)
            build = ctor(*args, **kwargs)
        except TypeError:
            return None
        return cast(BuildMgr | None, build)

    def _instantiate_build(self, build_type: type[BuildMgr], match_only: bool = False) -> BuildMgr | None:
        cache = self._match_only_build_instances if match_only else self._runtime_build_instances

        if build_type in cache:
            build = cache[build_type]
            if build is not None and "cached_data" in self.build_init_kwargs and hasattr(build, "set_cached_data"):
                build.set_cached_data(self.build_init_kwargs["cached_data"])
            return build

        if match_only:
            build = self._call_build_ctor(build_type, match_only=True, **self.build_init_kwargs)
            if build is None:
                build = self._call_build_ctor(build_type, match_only=True)
            if build is None:
                build = self._call_build_ctor(build_type, **self.build_init_kwargs)
            if build is None:
                build = self._call_build_ctor(build_type)
        else:
            build = self._call_build_ctor(build_type, **self.build_init_kwargs)
            if build is None:
                build = self._call_build_ctor(build_type)

        if build is not None and "cached_data" in self.build_init_kwargs and hasattr(build, "set_cached_data"):
            build.set_cached_data(self.build_init_kwargs["cached_data"])

        cache[build_type] = build
        return build

    def _iter_builds(self, match_only: bool = False) -> list[BuildMgr]:
        cached_builds = self._cached_match_only_builds if match_only else self._cached_runtime_builds
        if cached_builds is not None:
            return list(cached_builds)

        builds: list[BuildMgr] = []
        for build_type in self.GetBuildTypes():
            build = self._instantiate_build(build_type, match_only=match_only)
            if build is not None:
                builds.append(build)

        if match_only:
            self._cached_match_only_builds = builds
            return list(self._cached_match_only_builds)

        self._cached_runtime_builds = builds
        return list(self._cached_runtime_builds)

    def _iter_matchable_builds(self, match_only: bool = False) -> list[BuildMgr]:
        cached_builds = self._cached_match_only_matchable_builds if match_only else self._cached_runtime_matchable_builds
        if cached_builds is not None:
            return list(cached_builds)

        matchable_builds: list[BuildMgr] = []
        for build in self._iter_builds(match_only=match_only):
            if build.is_template_only:
                continue
            if build.is_fallback_candidate:
                continue
            if build.IsFixedBuild:
                continue
            if not build.is_combat_automator_compatible:
                continue
            matchable_builds.append(build)

        if match_only:
            self._cached_match_only_matchable_builds = matchable_builds
            return list(self._cached_match_only_matchable_builds)

        self._cached_runtime_matchable_builds = matchable_builds
        return list(self._cached_runtime_matchable_builds)

    def _iter_fallback_builds(self, match_only: bool = False) -> list[BuildMgr]:
        cached_builds = self._cached_match_only_fallback_builds if match_only else self._cached_runtime_fallback_builds
        if cached_builds is not None:
            return list(cached_builds)

        fallback_builds: list[BuildMgr] = []
        for build in self._iter_builds(match_only=match_only):
            if build.is_fallback_candidate:
                fallback_builds.append(build)

        if match_only:
            self._cached_match_only_fallback_builds = fallback_builds
            return list(self._cached_match_only_fallback_builds)

        self._cached_runtime_fallback_builds = fallback_builds
        return list(self._cached_runtime_fallback_builds)

    def ResolveFallback(self, fallback_name: str | None = None) -> BuildMgr | None:
        requested_name = (fallback_name or self.default_fallback_name or "").strip().casefold()
        fallback_builds = self._iter_fallback_builds(match_only=True)

        if requested_name:
            for build in fallback_builds:
                if build.build_name.casefold() == requested_name or build.__class__.__name__.casefold() == requested_name:
                    return self._instantiate_build(build.__class__)

        if fallback_builds:
            return self._instantiate_build(fallback_builds[0].__class__)

        return None

    def GetBestBuild(
        self,
        current_primary=None,
        current_secondary=None,
        current_skills: list[int] | None = None,
        fallback_name: str | None = None,
    ) -> BuildMgr | None:
        best_build_type: type[BuildMgr] | None = None
        best_score = -1

        for build in self._iter_matchable_builds(match_only=True):
            if build.is_template_only:
                continue
            score = build.ScoreMatch(
                current_primary=current_primary,
                current_secondary=current_secondary,
                current_skills=current_skills,
            )
            if score > best_score:
                best_score = score
                best_build_type = build.__class__

        if best_build_type is not None:
            return self._instantiate_build(best_build_type)

        return self.ResolveFallback(fallback_name=fallback_name)

    def ResolveBuild(
        self,
        current_primary=None,
        current_secondary=None,
        current_skills: list[int] | None = None,
        fallback_name: str | None = None,
    ) -> BuildMgr | None:
        return self.GetBestBuild(
            current_primary=current_primary,
            current_secondary=current_secondary,
            current_skills=current_skills,
            fallback_name=fallback_name,
        )
