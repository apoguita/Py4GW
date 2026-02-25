from typing import Any, Generator, override

import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Player
from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager, ThrottledTimer, Utils
from Py4GWCoreLib.Overlay import Overlay
from Sources.oazix.CustomBehaviors.primitives.bus.event_message import EventMessage
from Sources.oazix.CustomBehaviors.primitives.bus.event_type import EventType
from Sources.oazix.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Sources.oazix.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.parties.party_flagging_manager import PartyFlaggingManager
from Sources.oazix.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Sources.oazix.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology
from Sources.oazix.CustomBehaviors.primitives.bus.event_bus import EventBus
from Sources.oazix.CustomBehaviors.PersistenceLocator import PersistenceLocator

class FollowFlagUtilityNew(CustomSkillUtilityBase):
    """
    Utility that follows assigned flag positions from shared memory.

    Uses PartyFlaggingManager to access flag assignments:
    - Each player is assigned to a flag index (0-10)
    - Flag positions are stored in shared memory
    - Players move to their assigned flag position
    """

    def __init__(
            self,
            event_bus: EventBus,
            current_build: list[CustomSkill],
            allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("follow_flag_new"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.FOLLOW_FLAG.value),
            allowed_states=allowed_states,
            utility_skill_typology=UtilitySkillTypology.FOLLOWING)

        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.FOLLOW_FLAG.value)
        self.throttle_timer = ThrottledTimer(1000)

        # Use singleton manager for all configuration
        self.manager =  CustomBehaviorParty().party_flagging_manager

        # Load thresholds from persistence or use defaults
        persistence = PersistenceLocator().flagging
        self.follow_flag_threshold: float = persistence.read_follow_flag_threshold() or 260.0
        self.follow_flag_required_threshold: float = persistence.read_follow_flag_required_threshold() or 400.0

        self.event_bus.subscribe(EventType.MAP_CHANGED, self.area_changed, subscriber_name=self.custom_skill.skill_name)
        
    def area_changed(self, message: EventMessage) -> Generator[Any, Any, Any]:
        self.throttle_timer.Reset()
        self.manager.clear_all_flag_positions()
        yield

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        if custom_behavior_helpers.CustomBehaviorHelperParty.is_party_leader(): return False
        return True

    def _get_my_assigned_flag_position(self) -> tuple[float, float] | None:
        """Get the flag position assigned to this player from shared memory"""
        try:
            # Use account email as stable identifier (agent ID changes across maps)
            my_email = Player.GetAccountEmail()
            if not my_email:
                return None

            # Find which flag index is assigned to me
            flag_index = self.manager.get_my_flag_index(my_email)
            if flag_index is None:
                return None

            # Get the position for that flag
            x, y = self.manager.get_flag_position(flag_index)

            # Check if position is valid (not 0, 0)
            if x == 0.0 and y == 0.0:
                return None

            return (x, y)
        except Exception as e:
            print(f"FollowFlagUtilityNew._get_my_assigned_flag_position error: {e}")
            return None

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if self.allowed_states is not None and current_state not in self.allowed_states:
            return None

        # Get my assigned flag position from shared memory
        flag_pos = self._get_my_assigned_flag_position()
        if flag_pos is None:
            return None

        my_pos = Player.GetXY()
        if my_pos is None:
            return None

        # Calculate distance from assigned flag
        distance_from_flag = Utils.Distance(flag_pos, my_pos)

        # If very close to flag, don't move
        if distance_from_flag < 10:
            return None

        # If far from flag, high priority (use required threshold)
        if distance_from_flag > self.follow_flag_required_threshold:
            return CommonScore.FOLLOW_FLAG_REQUIRED.value

        # If outside threshold, normal priority (use normal threshold)
        if distance_from_flag > self.follow_flag_threshold:
            return CommonScore.FOLLOW_FLAG.value

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        if not self.throttle_timer.IsExpired():
            yield
            return BehaviorResult.ACTION_SKIPPED

        # Get my assigned flag position from shared memory
        flag_pos = self._get_my_assigned_flag_position()
        if flag_pos is None:
            yield
            return BehaviorResult.ACTION_SKIPPED

        # Move to assigned flag position
        print(f"Moving to flag position: {flag_pos}")

        # Cancel any current action (like auto-attacking) before moving
        # from Py4GWCoreLib.Routines import Routines
        # yield from Routines.Yield.Keybinds.CancelAction()
        # yield from custom_behavior_helpers.Helpers.wait_for(10)

        # Clear target and reset action queue
        # yield from Routines.Yield.Keybinds.ClearTarget()
        # ActionQueueManager().ResetQueue("ACTION")

        # Reset movement pointer then issue actual movement command
        # This is necessary after canceling actions to "wake up" the movement system
        Player.Move(0, 0)
        Player.Move(flag_pos[0], flag_pos[1])

        self.throttle_timer.Reset()

        yield from custom_behavior_helpers.Helpers.wait_for(1500)
        return BehaviorResult.ACTION_PERFORMED
    
    def save_thresholds_to_flagging(self) -> None:
        """Save threshold values to flagging persistence (global only)."""
        persistence = PersistenceLocator().flagging
        persistence.write_follow_flag_threshold(self.follow_flag_threshold)
        persistence.write_follow_flag_required_threshold(self.follow_flag_required_threshold)

    @override
    def has_persistence(self) -> bool:
        return True

    @override
    def persist_configuration_for_account(self):
        """Save thresholds to flagging.ini (global storage)."""
        self.save_thresholds_to_flagging()
        print("Follow flag thresholds saved to global storage")

    @override
    def persist_configuration_as_global(self):
        """Save thresholds to flagging.ini (global storage)."""
        self.save_thresholds_to_flagging()
        print("Follow flag thresholds saved to global storage")

    @override
    def delete_persisted_configuration(self):
        """Delete persisted threshold values and reset to defaults."""
        persistence = PersistenceLocator().flagging
        persistence.delete_follow_flag_thresholds()
        self.follow_flag_threshold = 260.0
        self.follow_flag_required_threshold = 400.0
        print("Follow flag thresholds deleted and reset to defaults (260.0 / 400.0)")

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        # if flag affected
        PyImGui.bullet_text(f"flag affected : {CustomBehaviorParty().party_flagging_manager.is_flag_defined(Player.GetAccountEmail())}")
        flag_index = CustomBehaviorParty().party_flagging_manager.get_my_flag_index(Player.GetAccountEmail())

        if flag_index is not None:
            PyImGui.bullet_text(f"flag index : {flag_index}")
            PyImGui.bullet_text(f"flag position : {CustomBehaviorParty().party_flagging_manager.get_flag_position(flag_index)}")
        else:
            PyImGui.bullet_text(f"flag index : None")

        PyImGui.separator()
        PyImGui.text("Thresholds:")

        # Normal threshold slider
        new_value = PyImGui.slider_float(
            "Normal Threshold##follow_flag_threshold",
            self.follow_flag_threshold,
            10.0,
            1000.0
        )
        if new_value != self.follow_flag_threshold:
            self.follow_flag_threshold = new_value
            self.save_thresholds_to_flagging()

        # Required threshold slider
        new_value = PyImGui.slider_float(
            "Required Threshold##follow_flag_required_threshold",
            self.follow_flag_required_threshold,
            10.0,
            1000.0
        )
        if new_value != self.follow_flag_required_threshold:
            self.follow_flag_required_threshold = new_value
            self.save_thresholds_to_flagging()

        # Show current distance if flag is assigned
        if flag_index is not None:
            flag_pos = self._get_my_assigned_flag_position()
            if flag_pos is not None:
                my_pos = Player.GetXY()
                if my_pos is not None:
                    distance = Utils.Distance(flag_pos, my_pos)
                    PyImGui.bullet_text(f"Current distance: {distance:.0f}")
        
    def draw_overlay(self, current_state: BehaviorState) -> None:
        """
        Draw debug overlay showing all flag positions as circles.
        This is the public method to be called from GUI.
        """
        # Only draw if enabled
        if not self.manager.enable_debug_overlay:
            return

        try:
            # Get my position for Z coordinate
            my_pos = Player.GetXY()
            if my_pos is None or len(my_pos) != 2:
                return

            my_agent_id = Player.GetAgentID()
            if my_agent_id is None:
                return

            _, _, my_z = Agent.GetXYZ(my_agent_id)

            # Get my account email to highlight my assigned flag
            my_email = Player.GetAccountEmail()
            if not my_email:
                return

            Overlay().BeginDraw()

            # Draw all 12 flag positions
            for flag_index in range(12):
                account_email, flag_x, flag_y = self.manager.get_flag_data(flag_index)

                # Skip unassigned flags (email == "") or invalid positions
                if not account_email or (flag_x == 0.0 and flag_y == 0.0):
                    continue

                # Determine color based on whether this is my flag
                if account_email == my_email:
                    # My flag - bright green
                    circle_color = Utils.RGBToColor(0, 255, 0, 200)
                    fill_color = Utils.RGBToColor(0, 255, 0, 100)
                    text_color = Utils.RGBToColor(0, 255, 0, 255)
                else:
                    # Other player's flag - cyan
                    circle_color = Utils.RGBToColor(0, 200, 255, 200)
                    fill_color = Utils.RGBToColor(0, 200, 255, 80)
                    text_color = Utils.RGBToColor(0, 200, 255, 255)

                # Draw filled circle for flag position
                Overlay().DrawPolyFilled3D(flag_x, flag_y, my_z, 16,
                                          fill_color, numsegments=16)

                # Draw circle outline
                Overlay().DrawPoly3D(flag_x, flag_y, my_z, 16,
                                    circle_color, numsegments=16, thickness=3.0)

                # Draw flag number (closer to ground at flag position)
                flag_z = Overlay().FindZ(flag_x, flag_y)
                Overlay().DrawText3D(flag_x, flag_y, flag_z - 25,
                                   f"Flag {flag_index + 1}",
                                   text_color,
                                   autoZ=False, centered=True, scale=1.0)

                # If this is my flag, draw a line from me to it
                if account_email == my_email:
                    Overlay().DrawLine3D(my_pos[0], my_pos[1], my_z,
                                        flag_x, flag_y, my_z,
                                        Utils.RGBToColor(0, 255, 0, 150), thickness=2.0)

                    # Draw distance to my flag
                    distance = Utils.Distance(my_pos, (flag_x, flag_y))
                    mid_x = (my_pos[0] + flag_x) / 2
                    mid_y = (my_pos[1] + flag_y) / 2
                    Overlay().DrawText3D(mid_x, mid_y, my_z - 25,
                                       f"{distance:.0f}",
                                       Utils.RGBToColor(0, 255, 0, 255),
                                       autoZ=False, centered=True, scale=1.0)

            # Intentionally omit drawing player's blue circle in flag overlay

        except Exception as e:
            # Silently fail on debug UI errors
            print(f"FollowFlagUtilityNew.draw_overlay error: {e}")
            raise e
        finally:
            Overlay().EndDraw()