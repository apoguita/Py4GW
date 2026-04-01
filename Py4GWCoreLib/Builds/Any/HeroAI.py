from Py4GWCoreLib import Agent, Map, Player, Profession, Routines
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.BuildMgr import BuildRegistry


class HeroAI_Build(BuildMgr):
    def __init__(self, cached_data=None, standalone_fallback: bool = False, match_only: bool = False):
        super().__init__(
            name="HeroAI",
            template_code="HEROAI",
            is_fallback_candidate=True,
            IsFixedBuild=True,
        )
        self._cached_data = cached_data
        self._standalone_fallback = standalone_fallback
        if match_only:
            self._build_registry = None
            self._contract_map_signature = None
            self._contract_build = None
            return
        self._build_registry = BuildRegistry(
            default_fallback_name=self.build_name,
            build_init_kwargs={"cached_data": cached_data},
        )
        self._contract_signature: tuple[int, ...] | None = None
        self._contract_build: BuildMgr | None = None

    def set_cached_data(self, cached_data):
        self._cached_data = cached_data
        if self._build_registry is not None:
            self._build_registry.build_init_kwargs["cached_data"] = cached_data

    def ApplyBlockedSkillIDs(self, blocked_skill_ids: list[int] | None = None) -> None:
        cached_data = self._get_cached_data()
        combat_handler = getattr(cached_data, "combat_handler", None)
        if combat_handler is not None and hasattr(combat_handler, "ApplyBlockedSkillIDs"):
            combat_handler.ApplyBlockedSkillIDs(blocked_skill_ids)

    def _get_cached_data(self):
        if self._cached_data is None:
            from HeroAI.cache_data import CacheData

            self._cached_data = CacheData()
            if self._build_registry is not None:
                self._build_registry.build_init_kwargs["cached_data"] = self._cached_data
        return self._cached_data

    def _get_contract_signature(self) -> tuple[int, ...]:
        primary_profession, secondary_profession = Agent.GetProfessions(Player.GetAgentID())
        current_skills = tuple(int(skill_id) for skill_id in self._get_current_skills())
        return (
            int(Map.GetMapID()),
            int(Map.GetRegion()[0]),
            int(Map.GetDistrict()),
            int(Map.GetLanguage()[0]),
            int(primary_profession),
            int(secondary_profession),
            *current_skills,
        )

    def _reset_contract(self) -> None:
        self._contract_signature = None
        self._contract_build = None

    def ClearBuildContract(self) -> None:
        self._reset_contract()

    def EnsureBuildContract(self, cached_data=None):
        if cached_data is not None:
            self.set_cached_data(cached_data)
        cached_data = self._get_cached_data()

        if not Map.IsExplorable():
            self._reset_contract()
            return None

        contract_signature = self._get_contract_signature()
        if self._contract_build is not None and self._contract_signature == contract_signature:
            if self._contract_build is self:
                self.set_cached_data(cached_data)
            return self._contract_build

        if self._standalone_fallback:
            self.set_cached_data(cached_data)
            self._contract_signature = contract_signature
            self._contract_build = self
            return self

        if self._build_registry is None:
            self._reset_contract()
            return None

        current_primary_value, current_secondary_value = Agent.GetProfessions(Player.GetAgentID())
        current_primary = Profession(current_primary_value)
        current_secondary = Profession(current_secondary_value)
        current_skills = self._get_current_skills()

        resolved_build = None
        best_score = -1
        for build in self._build_registry._iter_matchable_builds():
            score = build.ScoreMatch(
                current_primary=current_primary,
                current_secondary=current_secondary,
                current_skills=current_skills,
            )
            if score > best_score:
                best_score = score
                resolved_build = build

        if resolved_build is None or best_score <= 0:
            resolved_build = self
        elif isinstance(resolved_build, HeroAI_Build):
            resolved_build = self

        if resolved_build is self:
            self.set_cached_data(cached_data)

        self._contract_signature = contract_signature
        self._contract_build = resolved_build
        return resolved_build

    def GetBuildContract(self):
        return self._contract_build

    def _prepare_combat(self):
        cached_data = self._get_cached_data()

        if not Routines.Checks.Map.MapValid():
            return None

        if not Map.IsExplorable() or Map.IsInCinematic():
            return None

        if not Agent.IsAlive(Player.GetAgentID()) or Agent.IsKnockedDown(Player.GetAgentID()):
            return None

        cached_data.Update()
        cached_data.UpdateCombat()
        return cached_data

    def _get_phase_cached_data(self):
        cached_data = self._get_cached_data()
        if cached_data is None:
            return None
        return self._prepare_combat()

    def _run_contract(self, cached_data, is_in_combat: bool):
        contract_build = self.EnsureBuildContract(cached_data)
        if contract_build is None:
            self.SetTickFailure()
            yield from Routines.Yield.wait(250)
            return

        if contract_build is self:
            if cached_data.combat_handler.HandleCombat(cached_data, ooc=not is_in_combat):
                self.SetTickSuccess()
            else:
                self.SetTickFailure()
            yield
            return

        contract_build.ResetTickState()
        if is_in_combat:
            yield from contract_build.ProcessCombat()
        else:
            yield from contract_build.ProcessOOC()

        self.tick_state = contract_build.tick_state
        if self.tick_state is None:
            self.SetTickFailure()

    def ProcessOOC(self):
        self.ResetTickState()
        cached_data = self._get_phase_cached_data()
        if cached_data is None:
            self.SetTickFailure()
            yield from Routines.Yield.wait(250)
            return

        if cached_data.data.in_aggro:
            self.SetTickFailure()
            yield
            return

        yield from self._run_contract(cached_data, is_in_combat=False)

    def ProcessCombat(self):
        self.ResetTickState()
        cached_data = self._get_phase_cached_data()
        if cached_data is None:
            self.SetTickFailure()
            yield from Routines.Yield.wait(250)
            return

        if not cached_data.data.in_aggro:
            self.SetTickFailure()
            yield
            return

        yield from self._run_contract(cached_data, is_in_combat=True)

    def ProcessSkillCasting(self):
        self.ResetTickState()
        cached_data = self._get_phase_cached_data()
        if cached_data is None:
            self.SetTickFailure()
            yield from Routines.Yield.wait(250)
            return

        if cached_data.data.in_aggro:
            yield from self.ProcessCombat()
        else:
            yield from self.ProcessOOC()


HeroAI = HeroAI_Build
