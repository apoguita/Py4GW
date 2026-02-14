from typing import Any, Generator

from Py4GWCoreLib import Agent, Routines
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.botting.botting_manager import BottingManager
from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility


class AutoFollowAgent:
    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AutoFollowAgent, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self.generator: Generator[Any, None, Any] | None = None
            self.is_active: bool = False
            self.target_agent_id: int = 0
            self.follow_distance: float = 300.0  # Stop following when within this distance
            self.update_interval_ms: int = 500  # Update path every 500ms
            self.movement_progress: float = 0
            # UI state
            self.selected_agent_id: int = 0  # Agent ID selected in UI (not yet following)
            self.selected_follow_distance: float = 300.0  # Follow distance selected in UI

    def start(self, agent_id: int, follow_distance: float = 300.0):
        """Start following the specified agent_id."""
        if not Agent.IsValid(agent_id):
            print(f"AutoFollowAgentId: Invalid agent_id {agent_id}")
            return

        self.target_agent_id = agent_id
        self.follow_distance = follow_distance
        self.is_active = True
        self.movement_progress = 0
        self.generator = self.__create_generator()

        if constants.DEBUG:
            print(f"AutoFollowAgentId: Started following agent {agent_id} with distance {follow_distance}")

    def __create_generator(self) -> Generator[None, None, None]:
        """Generator that continuously follows the target agent."""

        # Setup combat behavior utilities
        instance: CustomBehaviorBaseUtility | None = CustomBehaviorLoader().custom_combat_behavior
        if instance is None:
            print("AutoFollowAgentId: No combat behavior instance available")
            return

        # Inject utility skills for movement using configurable list
        config = BottingManager()
        config.inject_enabled_skills(config.get_enabled_automover_skills(), instance)

        if constants.DEBUG:
            print(f"AutoFollowAgentId: Injected utility skills")

        # Main follow loop
        while True:
            # Check if agent is still valid
            if not Agent.IsValid(self.target_agent_id):
                if constants.DEBUG:
                    print(f"AutoFollowAgentId: Agent {self.target_agent_id} is no longer valid, stopping")
                break

            # Check if player is dead
            if Agent.IsDead(Player.GetAgentID()):
                if constants.DEBUG:
                    print("AutoFollowAgentId: Player is dead, stopping")
                break

            # Get positions
            agent_pos = Agent.GetXY(self.target_agent_id)
            player_pos = Player.GetXY()
            distance = Utils.Distance(agent_pos, player_pos)

            # Update progress based on distance
            if distance <= self.follow_distance:
                self.movement_progress = 100.0
            else:
                # Calculate progress inversely proportional to distance
                max_distance = 5000.0  # Assume max tracking distance
                self.movement_progress = max(0, min(100, (1 - (distance - self.follow_distance) / max_distance) * 100))

            if constants.DEBUG:
                print(f"AutoFollowAgentId: Distance to agent: {distance:.1f}, Progress: {self.movement_progress:.1f}%")

            # If within follow distance, just wait
            if distance <= self.follow_distance:
                yield from Routines.Yield.wait(self.update_interval_ms)
                continue

            # Move towards the agent
            path = [player_pos, agent_pos]

            if constants.DEBUG:
                print(f"AutoFollowAgentId: Moving from {player_pos} to {agent_pos}")

            # Create pause function for combat utilities
            custom_pause_fn = lambda: instance.is_executing_utility_skills() == True

            # Follow path to agent with a short timeout to allow frequent updates
            yield from Routines.Yield.Movement.FollowPath(
                path_points=path,
                custom_exit_condition=lambda: (
                    not Agent.IsValid(self.target_agent_id) or
                    Agent.IsDead(Player.GetAgentID()) or
                    Utils.Distance(Agent.GetXY(self.target_agent_id), Player.GetXY()) <= self.follow_distance
                ),
                tolerance=self.follow_distance,
                log=constants.DEBUG,
                timeout=2000,  # Short timeout to allow frequent path updates
                custom_pause_fn=custom_pause_fn
            )

            # Wait before next update
            yield from Routines.Yield.wait(self.update_interval_ms)

        if constants.DEBUG:
            print("AutoFollowAgentId: Follow loop ended")

    def stop(self):
        """Stop following and cleanup."""
        self.generator = None
        self.is_active = False
        self.target_agent_id = 0

        # Clear utility skills
        instance: CustomBehaviorBaseUtility | None = CustomBehaviorLoader().custom_combat_behavior
        if instance is not None:
            instance.clear_additionnal_utility_skills()

        if constants.DEBUG:
            print("AutoFollowAgentId: Stopped following")

    def pause(self):
        """Pause following."""
        self.is_active = False
        if constants.DEBUG:
            print("AutoFollowAgentId: Paused")

    def resume(self):
        """Resume following."""
        self.is_active = True
        if constants.DEBUG:
            print("AutoFollowAgentId: Resumed")

    def is_paused(self) -> bool:
        """Check if following is paused."""
        return self.generator is not None and not self.is_active

    def is_running(self) -> bool:
        """Check if following is currently active."""
        return self.generator is not None

    def get_movement_progress(self) -> float:
        """Get current movement progress as percentage."""
        return self.movement_progress

    def get_target_agent_id(self) -> int:
        """Get the current target agent_id being followed."""
        return self.target_agent_id

    def act(self):
        """Execute one step of following. Called by root.py."""
        if not self.is_active or self.generator is None:
            return

        try:
            next(self.generator)
            if constants.DEBUG:
                print(f"AutoFollowAgentId: Follow step completed")
        except StopIteration:
            if constants.DEBUG:
                print("AutoFollowAgentId: Following completed")
            self.stop()
        except Exception as e:
            print(f"AutoFollowAgentId: Following error: {e}")
            self.stop()

    # Agent selection methods for UI
    def set_selected_agent_id(self, agent_id: int):
        """Set the agent_id to be followed (for UI input)."""
        self.selected_agent_id = agent_id

    def get_selected_agent_id(self) -> int:
        """Get the currently selected agent_id (for UI display)."""
        return self.selected_agent_id

    def set_selected_follow_distance(self, distance: float):
        """Set the follow distance (for UI input)."""
        self.selected_follow_distance = distance

    def get_selected_follow_distance(self) -> float:
        """Get the currently selected follow distance (for UI display)."""
        return self.selected_follow_distance

    def set_agent_from_current_target(self):
        """Set selected agent_id from player's current target."""
        target_id = Player.GetTargetID()
        if Agent.IsValid(target_id):
            self.selected_agent_id = target_id
            return True
        return False

    def set_agent_from_mouse_over(self):
        "deprecated, no property available"
        return False

    def is_selected_agent_valid(self) -> bool:
        """Check if the selected agent_id is valid."""
        return Agent.IsValid(self.selected_agent_id)

    def get_selected_agent_name(self) -> str:
        """Get the name of the selected agent."""
        if self.is_selected_agent_valid():
            return Agent.GetNameByID(self.selected_agent_id)
        return ""

    def get_selected_agent_position(self) -> tuple[float, float]:
        """Get the position of the selected agent."""
        if self.is_selected_agent_valid():
            return Agent.GetXY(self.selected_agent_id)
        return (0.0, 0.0)

    def start_following_selected(self):
        """Start following the currently selected agent with selected distance."""
        if self.is_selected_agent_valid():
            self.start(self.selected_agent_id, self.selected_follow_distance)
            return True
        return False

    def get_target_agent_name(self) -> str:
        """Get the name of the agent currently being followed."""
        if Agent.IsValid(self.target_agent_id):
            return Agent.GetNameByID(self.target_agent_id)
        return ""

    def get_target_agent_position(self) -> tuple[float, float]:
        """Get the position of the agent currently being followed."""
        if Agent.IsValid(self.target_agent_id):
            return Agent.GetXY(self.target_agent_id)
        return (0.0, 0.0)
