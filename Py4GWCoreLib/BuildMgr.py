from __future__ import annotations

from collections.abc import Generator
import importlib
import inspect
from pathlib import Path
from typing import Any, Callable

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
        self._local_skill_casting_handler: Callable[[], Any] | None = None
        self._local_ooc_handler: Callable[[], Any] | None = None
        self._local_combat_handler: Callable[[], Any] | None = None
        self._custom_skill_data_handler = None

        self.minimum_required_match = len(self.required_skills)
        self.tick_state = None
        self.current_target_id = 0
        self._was_in_aggro = False
        self._local_cast_timer = ThrottledTimer(0)
        self._local_cast_timer.Stop()
        
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

    def SetOOCFn(self, handler: Callable[[], Any] | None) -> None:
        self._local_ooc_handler = handler

    def SetCombatFn(self, handler: Callable[[], Any] | None) -> None:
        self._local_combat_handler = handler

    def SetSkillCastingFn(self, handler: Callable[[], Any] | None) -> None:
        self._local_skill_casting_handler = handler

    def CanProcess(self) -> bool:
        from Py4GWCoreLib import Agent, Player, Routines

        return (
            Routines.Checks.Map.MapValid()
            and Routines.Checks.Map.IsExplorable()
            and Routines.Checks.Player.CanAct()
            and not Agent.IsDead(Player.GetAgentID())
        )

    def GetCustomSkill(self, skill_id: int):
        from HeroAI.custom_skill import CustomSkillClass

        if self._custom_skill_data_handler is None:
            self._custom_skill_data_handler = CustomSkillClass()
        return self._custom_skill_data_handler.get_skill(skill_id)

    def GetEquippedSkillSlot(self, skill_id: int) -> int:
        from Py4GWCoreLib.Skillbar import SkillBar

        return int(SkillBar.GetSlotBySkillID(skill_id) or 0)

    def IsSkillEquipped(self, skill_id: int) -> bool:
        return 1 <= self.GetEquippedSkillSlot(skill_id) <= 8

    def GetEquippedCustomSkill(self, skill_id: int):
        if not self.IsSkillEquipped(skill_id):
            return None
        return self.GetCustomSkill(skill_id)

    def ResetTarget(self) -> None:
        self.current_target_id = 0

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

        in_aggro = bool(Routines.Checks.Agents.InAggro())
        if self._was_in_aggro and not in_aggro:
            self.ResetTarget()
        self._was_in_aggro = in_aggro
    
    def _pick_fallback_target(self, target_type: str) -> int:
        from HeroAI.targeting import GetEnemyInjured, TargetClusteredEnemy
        from Py4GWCoreLib import Range
        from Py4GWCoreLib.Agent import Agent
        
        return_target = 0
        if target_type == "EnemyClustered":
            return_target = TargetClusteredEnemy(Range.Earshot.value)
            if not (Agent.IsValid(return_target) and not Agent.IsDead(return_target)):
                return_target = GetEnemyInjured(Range.Earshot.value)
                
        elif target_type == "EnemyInjured":
            return_target = GetEnemyInjured(Range.Earshot.value)
             
        if Agent.IsValid(return_target) and not Agent.IsDead(return_target):
            return return_target 
        return 0

    def _resolve_target(self, target_type: str = "EnemyInjured", show_log: bool = False) -> tuple[bool, bool]:
        from Py4GWCoreLib import Party, Agent
        party_target = Party.GetPartyTarget()
        self._debug(f"_acquire_target start current={self.current_target_id} party_target={party_target}", show_log)

        if Agent.IsValid(party_target) and not Agent.IsDead(party_target):
            desired_target = party_target
            target_source = "party"
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
    

    def _resolve_extra_condition(self, extra_condition: bool | Callable[[], bool]) -> bool:
        if callable(extra_condition):
            return bool(extra_condition())
        return bool(extra_condition)

    def _yield_from_handler(self, handler: Callable[[], Any] | None):
        if handler is None:
            yield
            return

        result = handler()
        if inspect.isgenerator(result):
            yield from result

    def _process_phase(self, handler: Callable[[], Any] | None, is_in_combat: bool):
        if not self.CanProcess():
            yield
            return

        self._refresh_target_tracking()
        yield from self._yield_from_handler(handler)

        fallback = self.ResolveFallback()
        if fallback is not None:
            if is_in_combat:
                yield from fallback.ProcessCombat()
            else:
                yield from fallback.ProcessOOC()
            return

        yield

    def _process_skill_casting_phase(self, handler: Callable[[], Any] | None):
        if not self.CanProcess():
            yield
            return

        self._refresh_target_tracking()
        yield from self._yield_from_handler(handler)

        fallback = self.ResolveFallback()
        if fallback is not None:
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

    def CastSkillID(
        self,
        skill_id: int,
        extra_condition: bool | Callable[[], bool] = True,
        log: bool = False,
        aftercast_delay: int = 1000,
    ):
        from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, ConsoleLog, Console, SkillBar, Skill
        if False:
            yield

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
        if not Routines.Checks.Skills.HasEnoughAdrenalineBySlot(slot):
            return False

        GLOBAL_CACHE.SkillBar.UseSkill(slot, aftercast_delay=aftercast_delay)
        self._mark_local_cast_pending(aftercast_delay)
        if log:
            ConsoleLog("CastSkillID", f"Cast {Skill.GetName(skill_id)}, slot: {slot}", Console.MessageType.Info, log=log)
        self.SetTickSuccess()

        return True

    def CastSkillSlot(
        self,
        slot: int,
        extra_condition: bool | Callable[[], bool] = True,
        log: bool = True,
        aftercast_delay: int = 1000,
    ):
        from Py4GWCoreLib import GLOBAL_CACHE, Player, Routines, ConsoleLog, Console, SkillBar
        if False:
            yield

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
        if not Routines.Checks.Skills.HasEnoughEnergy(Player.GetAgentID(), skill_id):
            return False
        if not Routines.Checks.Skills.IsSkillSlotReady(slot):
            return False
        if not Routines.Checks.Skills.HasEnoughAdrenalineBySlot(slot):
            return False

        GLOBAL_CACHE.SkillBar.UseSkill(slot, aftercast_delay=aftercast_delay)
        self._mark_local_cast_pending(aftercast_delay)
        if log:
            ConsoleLog("CastSkillSlot", f"Cast {GLOBAL_CACHE.Skill.GetName(skill_id)}, slot: {slot}", Console.MessageType.Info, log=log)
        self.SetTickSuccess()

        return True


    def ProcessSkillCasting(self):
        if self._local_skill_casting_handler is not None:
            yield from self._process_skill_casting_phase(self._local_skill_casting_handler)
            return

        if self._local_ooc_handler is None and self._local_combat_handler is None:
            raise NotImplementedError

        from Py4GWCoreLib import Range, Routines

        if Routines.Checks.Agents.InDanger(Range.Earshot):
            yield from self.ProcessCombat()
        else:
            yield from self.ProcessOOC()

    def ProcessOOC(self):
        if self._local_ooc_handler is None:
            yield from self.ProcessSkillCasting()
            return
        yield from self._process_phase(self._local_ooc_handler, is_in_combat=False)

    def ProcessCombat(self):
        if self._local_combat_handler is None:
            yield from self.ProcessSkillCasting()
            return
        yield from self._process_phase(self._local_combat_handler, is_in_combat=True)

    def Tick(self, is_in_combat: bool):
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

    def _instantiate_build(self, build_type: type[BuildMgr]) -> BuildMgr | None:
        try:
            return build_type(**self.build_init_kwargs)
        except TypeError:
            try:
                return build_type()
            except TypeError:
                return None

    def _iter_builds(self) -> list[BuildMgr]:
        builds: list[BuildMgr] = []
        for build_type in self.GetBuildTypes():
            build = self._instantiate_build(build_type)
            if build is not None:
                builds.append(build)
        return builds

    def _iter_matchable_builds(self) -> list[BuildMgr]:
        matchable_builds: list[BuildMgr] = []
        for build in self._iter_builds():
            if build.is_template_only:
                continue
            if build.is_fallback_candidate:
                continue
            if build.IsFixedBuild:
                continue
            if not build.is_combat_automator_compatible:
                continue
            matchable_builds.append(build)
        return matchable_builds

    def _iter_fallback_builds(self) -> list[BuildMgr]:
        fallback_builds: list[BuildMgr] = []
        for build in self._iter_builds():
            if build.is_fallback_candidate:
                fallback_builds.append(build)
        return fallback_builds

    def ResolveFallback(self, fallback_name: str | None = None) -> BuildMgr | None:
        requested_name = (fallback_name or self.default_fallback_name or "").strip().casefold()
        fallback_builds = self._iter_fallback_builds()

        if requested_name:
            for build in fallback_builds:
                if build.build_name.casefold() == requested_name or build.__class__.__name__.casefold() == requested_name:
                    return build

        if fallback_builds:
            return fallback_builds[0]

        return None

    def GetBestBuild(
        self,
        current_primary=None,
        current_secondary=None,
        current_skills: list[int] | None = None,
        fallback_name: str | None = None,
    ) -> BuildMgr | None:
        best_build: BuildMgr | None = None
        best_score = -1

        for build in self._iter_matchable_builds():
            if build.is_template_only:
                continue
            score = build.ScoreMatch(
                current_primary=current_primary,
                current_secondary=current_secondary,
                current_skills=current_skills,
            )
            if score > best_score:
                best_score = score
                best_build = build

        if best_build is not None:
            return best_build

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
