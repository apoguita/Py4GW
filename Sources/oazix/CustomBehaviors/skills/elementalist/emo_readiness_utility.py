from typing import Any, Generator, override

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.parties.shared_lock_manager import ShareLockType
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology


class EmoReadinessUtility(CustomSkillUtilityBase):
    """
    Utility that acquires a lock and keeps it until the team is buffed.
    This prevents the team from moving forward until all protective bonds are applied.
    """
    Name = "emo_readiness"

    def __init__(
            self,
            event_bus: EventBus,
            current_build: list[CustomSkill],
            protective_bond_utility: CustomSkillUtilityBase,
            life_attunement_utility: CustomSkillUtilityBase,
            score_definition: ScoreStaticDefinition = ScoreStaticDefinition(99),
            allowed_states: list[BehaviorState] = [BehaviorState.IDLE, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill(EmoReadinessUtility.Name),
            in_game_build=current_build,
            score_definition=score_definition,
            allowed_states=allowed_states,
            utility_skill_typology=UtilitySkillTypology.BOTTING)

        self.protective_bond_utility: CustomSkillUtilityBase = protective_bond_utility
        self.life_attunement_utility: CustomSkillUtilityBase = life_attunement_utility
        self.lock_key = "emo_readiness_lock"
        
    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        return True

    def _is_team_buffed(self) -> bool:
        """
        Check if the team is fully buffed by checking if both protective_bond_utility
        and life_attunement_utility have no more targets.
        """
        # Check protective_bond_utility
        if hasattr(self.protective_bond_utility, '_get_target'):
            protective_target = self.protective_bond_utility._get_target()
            if protective_target is not None:
                return False  # Still has targets to buff

        # Check life_attunement_utility
        if hasattr(self.life_attunement_utility, '_get_target'):
            life_target = self.life_attunement_utility._get_target()
            if life_target is not None:
                return False  # Still has targets to buff

        # Both utilities have no more targets, team is fully buffed
        return True

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        """
        Evaluate if we should keep the lock.
        Returns score if team is not fully buffed yet.
        Returns None if team is fully buffed (releases lock).
        """
        lock_manager = CustomBehaviorParty().get_shared_lock_manager()

        # Check if team is fully buffed
        if self._is_team_buffed():
            # Team is buffed, release lock if we have it
            if lock_manager.is_any_lock_taken(ShareLockType.ACTIONS):
                lock_manager.release_lock(self.lock_key)
            return None

        # Team is not buffed yet, return score only if we don't have the lock yet
        if not lock_manager.is_any_lock_taken(ShareLockType.ACTIONS):
            return self.score_definition.get_score()

        return None
        
    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        """
        Execute the readiness check.
        Acquires a lock and holds it until the team is buffed.
        """
        lock_manager = CustomBehaviorParty().get_shared_lock_manager()

        # Try to acquire lock
        if lock_manager.try_aquire_lock(self.lock_key, timeout_seconds=30, lock_type=ShareLockType.ACTIONS):
            print(f"EmoReadinessUtility: Lock acquired")
        else:
            # Someone else has the lock, skip
            print(f"EmoReadinessUtility: Failed to acquire lock")
            return BehaviorResult.ACTION_SKIPPED

        # Just wait - the lock will be released in _evaluate when team is buffed
        yield from custom_behavior_helpers.Helpers.wait_for(300)
        return BehaviorResult.ACTION_PERFORMED

    @override
    def get_buff_configuration(self):
        return None

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        import PyImGui
        lock_manager = CustomBehaviorParty().get_shared_lock_manager()
        PyImGui.text(f"Lock taken: {lock_manager.is_any_lock_taken(ShareLockType.ACTIONS)}")
        PyImGui.text(f"Team buffed: {self._is_team_buffed()}")

        # Show individual utility status
        if hasattr(self.protective_bond_utility, '_get_target'):
            protective_target = self.protective_bond_utility._get_target()
            PyImGui.text(f"Protective Bond target: {protective_target}")

        if hasattr(self.life_attunement_utility, '_get_target'):
            life_target = self.life_attunement_utility._get_target()
            PyImGui.text(f"Life Attunement target: {life_target}")

    @override
    def has_persistence(self) -> bool:
        return False

    @override
    def delete_persisted_configuration(self):
        pass

    @override
    def persist_configuration_as_global(self):
        pass

