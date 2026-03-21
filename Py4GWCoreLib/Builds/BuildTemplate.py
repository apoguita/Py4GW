from Py4GWCoreLib import BuildMgr, GLOBAL_CACHE, Profession
from Py4GWCoreLib.Builds.Any.AutoCombat import AutoCombat


class BuildStatus:
    """
    Optional local state container.

    This is not required by BuildMgr. It is only here to show that builds
    can keep their own tiny state machine when their local logic needs to
    remember what they were doing between ticks.

    Use this for:
    - local phase markers inside the build
    - combo/chain stage tracking
    - simple local modes such as "wait", "prep", "burst"

    Do not confuse this with BuildMgr.tick_state:
    - BuildStatus is your build's own internal state
    - tick_state is the per-tick success/failure signal consumed by HeroAI
    """

    Combat = "combat"
    Wait = "wait"


class PhaseAwareBuildTemplate(BuildMgr):
    """
    Example template for builds that need different logic in:
    - out of combat
    - combat

    Use this pattern when the build needs distinct behavior such as:
    - prebuffing only outside combat
    - different target logic once enemies are nearby
    - maintaining effects outside combat and executing a rotation in combat

    The important thing to understand is that this class does NOT override:
    - ProcessOOC()
    - ProcessCombat()
    - ProcessSkillCasting()

    Instead, it registers local callables with BuildMgr and lets the base
    class provide the shared scaffolding:
    - map/explorable/can-act validation
    - priority target refresh
     - automatic fallback delegation

     This keeps all builds consistent and avoids every build reimplementing
     the same boilerplate.

    Important for build discovery:
    - BuildRegistry may instantiate this class in `match_only` mode
    - `match_only` construction must stay lean and metadata-only
    - runtime-only setup belongs after the early return below
    """

    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Phase Aware Build Template",
            required_primary=Profession(0),
            required_secondary=Profession(0),
            template_code="",
            is_template_only=True,
            required_skills=[
                # Required skills define the build identity.
                # These are the skills that must be present for the build to
                # qualify during build matching.
                #
                # Existing builds are generally treated as "all skills are
                # required", so use this list for the core identity of the bar.
                #
                # Example:
                # GLOBAL_CACHE.Skill.GetID("Skill_Name"),
            ],
            optional_skills=[
                # Optional skills are supported extras.
                # They improve the match score after the build already qualifies.
                #
                # Use this for:
                # - alternate utility slots
                # - variant skills that the build knows how to handle
                # - extra supported bar configurations that should not define
                #   the build identity on their own
            ],
        )

        # Keep the matcher path lean. BuildRegistry uses `match_only=True`
        # when it only needs professions and supported skill ids for scoring.
        # Do not allocate fallback handlers, custom skill data, timers, or
        # other runtime state before this guard.
        if match_only:
            return

        # Everything below is runtime-only state for the selected build handler.
        # Fallback executors handle the rest of the bar after local logic.
        # AutoCombat is the default example, but any executor build can be used.
        self.SetFallback("AutoCombat", AutoCombat())

        # Register the local handlers instead of overriding ProcessOOC /
        # ProcessCombat directly. BuildMgr will call these and then apply the
        # fallback automatically.
        self.SetOOCFn(self._run_local_ooc_logic)
        self.SetCombatFn(self._run_local_combat_logic)

        # Store frequently used skill ids once in the runtime path so the build
        # logic can reference them cheaply and clearly.
        self.skill_ids = {
            # "skill_name": GLOBAL_CACHE.Skill.GetID("Skill_Name"),
        }

        # HeroAI custom skill data can be heavy, so load it only in the runtime
        # path after the `match_only` guard. Keep a local dictionary if your
        # build wants easy named access to the custom skill configuration
        # objects.
        self.custom_skills = {
            name: self.GetCustomSkill(skill_id)
            for name, skill_id in self.skill_ids.items()
        }

        # Example build-local state. Optional.
        self.status = BuildStatus.Wait

    def _run_local_ooc_logic(self):
        """
        Out-of-combat local logic.

        BuildMgr already handled the shared preconditions before this is called:
        - valid map
        - explorable map
        - player can act
        - player is not dead
        - priority target refresh

        This means this method should only focus on actual build decisions.

        Typical OOC responsibilities:
        - upkeep enchantments / stances / forms
        - pet or summon prep
        - target priming before a pull
        - positioning logic if the build owns it locally

        If the build casts through self.CastSkillID(...) or
        self.CastSkillSlot(...), BuildMgr will stamp the per-tick success state
        automatically for HeroAI.

        After this generator finishes, BuildMgr will automatically pass control
        to the configured fallback executor, if one exists.
        """
        yield

    def _run_local_combat_logic(self):
        """
        Combat local logic.

        Use this for the part of the bar that the build wants to own itself.

        Typical combat responsibilities:
        - selecting or validating a target
        - gating a combo / chain
        - deciding when to spend burst skills
        - applying custom HeroAI skill config rules
        - handling custom movement or interactions before executor handoff

        Keep in mind:
        - BuildMgr only auto-reports tick success when a shared cast helper
          actually casts a skill on that tick
        - reads/checks do not report success
        - fallback execution still happens automatically after this handler
        """
        yield


class SinglePhaseBuildTemplate(BuildMgr):
    """
    Example template for builds that do NOT distinguish between OOC and combat.

    Use this when the build wants a single local entry point and the same logic
    should be used regardless of phase.

    This pattern is especially useful for legacy or compact builds where:
    - one generator already owns the whole local decision flow
    - separate OOC/combat handlers would just duplicate code

     Like the phase-aware template, this class does not override the shared
     scaffolding. Instead it registers a single local skill-casting handler and
     lets BuildMgr handle:
     - validation
     - target refresh
     - automatic fallback delegation through ProcessSkillCasting()

    Important for build discovery:
    - BuildRegistry may instantiate this class in `match_only` mode
    - `match_only` construction must stay metadata-only
    - runtime-only setup belongs after the early return below
    """

    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Single Phase Build Template",
            required_primary=Profession(0),
            required_secondary=Profession(0),
            template_code="",
            is_template_only=True,
            required_skills=[
                # Required identity skills for the build matcher.
            ],
            optional_skills=[
                # Extra supported skills that improve match score but do not
                # define the build by themselves.
            ],
        )

        # Build matching only needs the metadata passed to `super().__init__`.
        # Keep expensive runtime setup below this guard so registry scoring
        # stays fast even when many builds are discovered.
        if match_only:
            return

        # Runtime-only execution state starts here.
        self.SetFallback("AutoCombat", AutoCombat())

        # Register one local callable. BuildMgr.ProcessSkillCasting() will call
        # it and then automatically hand off to the fallback executor.
        self.SetSkillCastingFn(self._run_local_skill_logic)

        self.skill_ids = {
            # "skill_name": GLOBAL_CACHE.Skill.GetID("Skill_Name"),
        }
        # Load custom-skill helpers only for the selected runtime build.
        self.custom_skills = {
            name: self.GetCustomSkill(skill_id)
            for name, skill_id in self.skill_ids.items()
        }
        self.status = BuildStatus.Wait

    def _run_local_skill_logic(self):
        """
        Single-phase local logic.

        This is the right place for builds that want one local rotation or one
        unified decision path, without separate OOC/combat methods.

        Typical responsibilities:
        - upkeep checks
        - target maintenance
        - combo gating
        - custom HeroAI skill config checks

        Just like in the phase-aware template:
        - use self.CastSkillID(...) / self.CastSkillSlot(...) for shared cast
          reporting
        - let BuildMgr handle the fallback automatically after this method
          finishes
        """
        return False
