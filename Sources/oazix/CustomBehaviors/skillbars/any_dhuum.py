"""AnyDhuum_UtilitySkillBar — Dhuum phase skill behavior for the Underworld bot.

This module is the *skillbar orchestrator only*. It wires up individual
per-skill utility classes and declares detection / requirement rules for
the framework. All cast logic and domain helpers live in:

  Sources/oazix/CustomBehaviors/specifics/underworld/
    dhuum_helpers.py           — chest detection, Spirit Form queries, morale lookup
    reaper_mode_tracker.py     — reaper event scanning, Dhuum's Rest / Ghostly Fury mode
    spiritual_healing_utility.py
    reversal_of_death_utility.py
    dhuums_rest_utility.py
    ghostly_fury_utility.py

Four utilities are active during the Dhuum soul-splitting (rez) phase:

  - SpiritualHealingUtility   score 90  — heal weakest ally below 70 % HP
  - ReversalOfDeathUtility    score 94  — rez soul-split ally with highest death penalty
  - DhuumsRestUtility         score 97  — mirror Reaper's Dhuum's Rest cast
  - GhostlyFuryUtility        score 97  — mirror Reaper's Ghostly Fury cast

PendingConditionUtility is a stub for Encase Skeletal (cast conditions TBD).
"""
from typing import Any, Generator, override

from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.skills.bonds.custom_buff_multiple_target import CustomBuffMultipleTarget
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.specifics.underworld.dhuum_helpers import resolve_skill_id
from Sources.oazix.CustomBehaviors.specifics.underworld.dhuums_rest_utility import DhuumsRestUtility
from Sources.oazix.CustomBehaviors.specifics.underworld.ghostly_fury_utility import GhostlyFuryUtility
from Sources.oazix.CustomBehaviors.specifics.underworld.reversal_of_death_utility import ReversalOfDeathUtility
from Sources.oazix.CustomBehaviors.specifics.underworld.spiritual_healing_utility import SpiritualHealingUtility

#OQBDAqwDSPwQwRwSwTwAAAAAAA


# ─── Placeholder utility ─────────────────────────────────────────────────────

class PendingConditionUtility(CustomSkillUtilityBase):
    """Placeholder for skills that are registered in the build but have no cast logic yet.

    Currently wraps Encase Skeletal, which appears on the Dhuum skillbar but whose
    exact usage conditions have not been implemented. The utility will never fire
    and serves only as a registered stub so the skill is tracked by the framework.
    """

    def __init__(self, event_bus: EventBus, skill: CustomSkill, current_build: list[CustomSkill]):
        super().__init__(
            event_bus=event_bus,
            skill=skill,
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(50),
            mana_required_to_cast=0,
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
        )

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        if False:
            yield None
        return BehaviorResult.ACTION_SKIPPED

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        pass

    @override
    def get_buff_configuration(self) -> CustomBuffMultipleTarget | None:
        return None

    @override
    def has_persistence(self) -> bool:
        return False

    @override
    def delete_persisted_configuration(self):
        pass

    @override
    def persist_configuration_as_global(self):
        pass

    @override
    def persist_configuration_for_account(self):
        pass


# ─── Main skillbar behavior ──────────────────────────────────────────────────

class AnyDhuum_UtilitySkillBar(CustomBehaviorBaseUtility):
    """Skillbar behavior profile for the Dhuum rez phase.

    Wires up all individual UtilityBase instances and exposes the active skill list
    to the framework via custom_skills_in_behavior and skills_required_in_behavior.

    Profile detection is tolerant: any single known Dhuum-phase skill found in the
    in-game skillbar is sufficient to select this profile
    (see count_matches_between_custom_behavior_and_in_game_build).
    The primary detection marker is Curse of Dhuum (skills_required_in_behavior).
    """

    _DHUUM_MARKER_CANDIDATES = (
        "Curse_of_Dhuum",
        "Curse of Dhuum",
    )

    _PREPARED_SKILL_CANDIDATES: dict[str, tuple[str, ...]] = {
        "DhuumsRest": ("Dhuum's Rest", "Dhuum_s_Rest", "Dhuums_Rest"),
        "SpiritualHealing": ("Spiritual Healing", "Spiritual_Healing"),
        "ReversalOfDeath": ("Reversal of Death", "Reversal_of_Death"),
        "GhostlyFury": ("Ghostly Fury", "Ghostly_Fury"),
    }

    def __init__(self):
        super().__init__()
        in_game_build = list(self.skillbar_management.get_in_game_build().values())

        self.spiritual_healing_utility: CustomSkillUtilityBase = SpiritualHealingUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
        )
        self.reversal_of_death_utility = ReversalOfDeathUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
        )
        self.dhuums_rest_utility: CustomSkillUtilityBase = DhuumsRestUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
        )
        self.ghostly_fury_utility: CustomSkillUtilityBase = GhostlyFuryUtility(
            event_bus=self.event_bus,
            current_build=in_game_build,
        )
        # Encase Skeletal: cast conditions not yet implemented — not instantiated.
        # self.encase_skeletal_utility = PendingConditionUtility(...)

    @override
    def count_matches_between_custom_behavior_and_in_game_build(self) -> int:
        """Return 1 if at least one Dhuum-phase skill is present in the in-game skillbar.

        A single match is sufficient because this is a highly specialised profile:
        if any Dhuum skill is on the bar, the full behavior suite should be loaded.
        Returns 0 when no known skill is detected (profile should not be selected).
        """
        in_game_ids = set(self.skillbar_management.get_in_game_build().keys())

        detection_candidates: list[tuple[str, ...]] = [
            self._DHUUM_MARKER_CANDIDATES,
            *self._PREPARED_SKILL_CANDIDATES.values(),
        ]

        for candidate_names in detection_candidates:
            skill_id = resolve_skill_id(*candidate_names)
            if skill_id > 0 and skill_id in in_game_ids:
                return 1

        return 0

    @property
    @override
    def custom_skills_in_behavior(self) -> list[CustomSkillUtilityBase]:
        """Return the ordered list of active skill utilities for the Dhuum phase.

        Evaluation order and scores:
          spiritual_healing  (score 90) — heal weak allies below 70% HP
          dhuums_rest        (score 97) — mirror reaper Dhuum's Rest cast
          reversal_of_death  (score 94) — rez soul-split ally with highest death penalty
          ghostly_fury       (score 97) — mirror reaper Ghostly Fury cast
        """
        return [
            self.spiritual_healing_utility,
            self.dhuums_rest_utility,
            self.reversal_of_death_utility,
            self.ghostly_fury_utility,
        ]

    @property
    @override
    def skills_required_in_behavior(self) -> list[CustomSkill]:
        """Return the skill(s) whose presence in-bar confirms this behavior profile.

        Curse of Dhuum is the most reliable Dhuum-phase marker: it is only placed on
        the skillbar of accounts assigned to the rez role in the party composition.
        """
        return [CustomSkill("Curse_of_Dhuum")]
