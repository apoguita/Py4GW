import math
from typing import Any, Generator, override
import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Agent, Range, Player
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer, Utils
from Py4GWCoreLib.Overlay import Overlay
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.parties.party_following_manager import PartyFollowingManager
from Widgets.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Widgets.CustomBehaviors.primitives.scores.score_per_status_definition import ScorePerStatusDefinition
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus

class FollowPartyLeaderOnlyUtility(CustomSkillUtilityBase):
    """
    Utility that makes party members follow the party leader at a configured distance.
    This utility only handles following behavior - no spreading.
    
    Features:
    - Follows party leader at configured distance based on combat state
    - Different follow distances for combat vs non-combat
    - Party leaders are automatically excluded
    - Simple distance-based following without spreading forces
    """

    def __init__(
            self,
            event_bus: EventBus,
            current_build: list[CustomSkill]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("follow_party_leader_only"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.FOLLOW.value),
            allowed_states=[BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
            utility_skill_typology=UtilitySkillTypology.FOLLOWING)

        self.throttle_timer = ThrottledTimer(600)
        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.FOLLOW.value)

        # Use singleton manager for all configuration
        self.manager = PartyFollowingManager()

        # Note: follow_distance is now managed by shared memory via self.manager.follow_distance

        # Hard-coded movement parameters (removed from shared memory)
        self.follow_distance_tolerance = 50.0  # Tolerance for follow distance
        self.min_move_threshold = 0.5  # Minimum vector magnitude to trigger movement
        self.max_move_distance = 250.0  # Maximum distance to move in one step

        # Debug
        self.last_target_pos = None
        self.last_state = None

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        if custom_behavior_helpers.CustomBehaviorHelperParty.is_party_leader(): return False
        return True

    def _get_party_leader_position(self) -> tuple[float, float] | None:
        """Get position of party leader (first player in party)"""
        try:
            leader_agent_id = custom_behavior_helpers.CustomBehaviorHelperParty.get_party_leader_id()
            if leader_agent_id is None:
                return None
            
            if not Agent.IsAlive(leader_agent_id):
                return None
            
            pos = Agent.GetXY(leader_agent_id)
            if pos is None or len(pos) != 2:
                return None
            
            return pos
        except Exception as e:
            print(f"FollowPartyLeaderOnlyUtility._get_party_leader_position error: {e}")
            return None
    
    def _am_i_party_leader(self) -> bool:
        return custom_behavior_helpers.CustomBehaviorHelperParty.is_party_leader()

    def _get_follow_distance_for_state(self, state: BehaviorState) -> float:
        """Get follow distance from shared memory"""
        return self.manager.follow_distance

    def _calculate_follow_position(self, my_pos: tuple[float, float],
                                   leader_pos: tuple[float, float],
                                   state: BehaviorState) -> tuple[float, float] | None:
        """
        Calculate target position to follow leader at configured distance.
        Simple distance-based following without spreading forces.
        """
        
        # Get follow distance for current state
        follow_distance = self._get_follow_distance_for_state(state)
        
        # Calculate distance to leader
        dx = leader_pos[0] - my_pos[0]
        dy = leader_pos[1] - my_pos[1]
        distance_to_leader = math.sqrt(dx * dx + dy * dy)
        
        # Calculate how much we need to move toward/away from leader
        distance_error = distance_to_leader - follow_distance
        
        # Check if we're within tolerance
        if abs(distance_error) <= self.follow_distance_tolerance:
            return None
        
        # Only move if we're too far from leader (not too close)
        if distance_error <= 0:
            return None
        
        # Calculate direction toward leader
        if distance_to_leader > 0:
            norm_dx = dx / distance_to_leader
            norm_dy = dy / distance_to_leader
            
            # Move toward leader, but limit movement distance
            move_amount = min(distance_error, self.max_move_distance)
            
            # Calculate target position
            target_x = my_pos[0] + norm_dx * move_amount
            target_y = my_pos[1] + norm_dy * move_amount
            
            return (target_x, target_y)
        
        return None

    def _draw_debug_overlay(self, my_pos: tuple[float, float],
                           leader_pos: tuple[float, float] | None,
                           target_pos: tuple[float, float] | None,
                           state: BehaviorState) -> None:
        """Draw debug overlay showing leader and target"""
        if not self.manager.enable_debug_overlay:
            return

        follow_distance = self._get_follow_distance_for_state(state)

        Overlay().BeginDraw()
        my_agent_id = Player.GetAgentID()
        _, _, my_z = Agent.GetXYZ(my_agent_id)

        # Determine state color for visual feedback
        if state == BehaviorState.IN_AGGRO:
            state_color = Utils.RGBToColor(255, 0, 0, 255)  # Red for combat
        else:
            state_color = Utils.RGBToColor(0, 255, 0, 255)  # Green for non-combat

        # Draw my position (blue circle)
        Overlay().DrawPoly3D(my_pos[0], my_pos[1], my_z, 50,
                            Utils.RGBToColor(0, 100, 255, 200), numsegments=16, thickness=3.0)

        # Draw leader position and follow distance circle
        if leader_pos is not None:
            # Draw leader (gold circle)
            Overlay().DrawPolyFilled3D(leader_pos[0], leader_pos[1], my_z, 60,
                                      Utils.RGBToColor(255, 215, 0, 200), numsegments=16)
            Overlay().DrawText3D(leader_pos[0], leader_pos[1], my_z - 150,
                               "LEADER", Utils.RGBToColor(255, 215, 0, 255),
                               autoZ=False, centered=True, scale=1.2)

            # Draw follow distance circle around leader (gold transparent)
            Overlay().DrawPoly3D(leader_pos[0], leader_pos[1], my_z, follow_distance,
                                Utils.RGBToColor(255, 215, 0, 80), numsegments=32, thickness=2.0)

            # Debug: Show current follow distance setting
            Overlay().DrawText3D(leader_pos[0], leader_pos[1], my_z - 200,
                               f"Follow Distance: {follow_distance:.0f}",
                               Utils.RGBToColor(255, 215, 0, 255),
                               autoZ=False, centered=True, scale=0.9)

            # Draw line from me to leader with distance
            Overlay().DrawLine3D(my_pos[0], my_pos[1], my_z,
                                leader_pos[0], leader_pos[1], my_z,
                                Utils.RGBToColor(255, 215, 0, 150), thickness=2.0)

            # Draw current distance to leader
            current_distance = Utils.Distance(my_pos, leader_pos)
            mid_x = (my_pos[0] + leader_pos[0]) / 2
            mid_y = (my_pos[1] + leader_pos[1]) / 2
            Overlay().DrawText3D(mid_x, mid_y, my_z - 50,
                               f"{current_distance:.0f}",
                               Utils.RGBToColor(255, 215, 0, 255),
                               autoZ=False, centered=True, scale=1.0)

        # Draw target position (green circle and arrow)
        if target_pos is not None:
            Overlay().DrawPolyFilled3D(target_pos[0], target_pos[1], my_z, 50,
                                      Utils.RGBToColor(0, 255, 0, 200), numsegments=16)

            # Draw arrow from current to target
            Overlay().DrawLine3D(my_pos[0], my_pos[1], my_z,
                                target_pos[0], target_pos[1], my_z,
                                Utils.RGBToColor(0, 255, 0, 255), thickness=4.0)

            # Draw distance text
            move_distance = Utils.Distance(my_pos, target_pos)
            Overlay().DrawText3D(target_pos[0], target_pos[1], my_z - 100,
                               f"MOVE: {move_distance:.0f}",
                               Utils.RGBToColor(0, 255, 0, 255),
                               autoZ=False, centered=True, scale=1.2)

        # Draw state and active parameters
        state_name = state.name if hasattr(state, 'name') else str(state)
        state_text = f"FOLLOW ONLY - STATE: {state_name}"
        Overlay().DrawText3D(my_pos[0], my_pos[1], my_z - 200,
                           state_text, state_color,
                           autoZ=False, centered=True, scale=1.0)

        # Active parameters
        params_text = f"Follow Distance: {follow_distance:.0f}"
        Overlay().DrawText3D(my_pos[0], my_pos[1], my_z - 250,
                           params_text, state_color,
                           autoZ=False, centered=True, scale=0.9)

        Overlay().EndDraw()

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if self.allowed_states is not None and current_state not in self.allowed_states:
            return None

        if not self.throttle_timer.IsExpired():
            return None

        my_pos = Player.GetXY()
        if my_pos is None or len(my_pos) != 2:
            return None

        # Leaders don't follow
        if self._am_i_party_leader():
            return None
        
        # Check if we need to move
        leader_pos = self._get_party_leader_position()
        if leader_pos is None:
            return None
        
        # Get follow distance for current state
        follow_distance = self._get_follow_distance_for_state(current_state)
        
        # Calculate distance to leader
        dx = leader_pos[0] - my_pos[0]
        dy = leader_pos[1] - my_pos[1]
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Check if we need to adjust position for following
        outside_tolerance = abs(distance - follow_distance) > self.follow_distance_tolerance
        too_far = distance > follow_distance  # Only move if too far, not too close
        
        if outside_tolerance and too_far:
            return self.score_definition.get_score()
        
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        
        try:
            self.last_state = state
            
            my_pos = Player.GetXY()
            if my_pos is None or len(my_pos) != 2:
                yield
                return BehaviorResult.ACTION_SKIPPED
            
            # If I'm the leader, don't follow
            if self._am_i_party_leader():
                yield
                return BehaviorResult.ACTION_SKIPPED
            
            leader_pos = self._get_party_leader_position()
            if leader_pos is None:
                yield
                return BehaviorResult.ACTION_SKIPPED
            
            # Calculate target position (follow only)
            target_pos = self._calculate_follow_position(my_pos, leader_pos, state)
            
            # Store for debug UI
            self.last_target_pos = target_pos
            
            # Move if we have a valid target
            if target_pos is not None:
                Player.Move(target_pos[0], target_pos[1])
                self.throttle_timer.Reset()
                yield from custom_behavior_helpers.Helpers.wait_for(1000)
                return BehaviorResult.ACTION_PERFORMED
            
            yield
            return BehaviorResult.ACTION_SKIPPED
            
        except Exception as e:
            print(f"FollowPartyLeaderOnlyUtility._execute error: {e}")
            yield
            return BehaviorResult.ACTION_SKIPPED

    def draw_overlay(self, current_state: BehaviorState) -> None:
        """
        Draw debug overlay showing following behavior visualization.
        This is the public method to be called from GUI.
        """
        # Only draw if enabled and in valid state (CLOSE_TO_AGGRO or FAR_FROM_AGGRO for follow utility)
        if not self.manager.enable_debug_overlay:
            return

        # Only show overlay when in following states (not during active combat)
        if current_state not in [BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]:
            return

        try:
            # Get current positions
            my_pos = Player.GetXY()
            if my_pos is None or len(my_pos) != 2:
                return

            leader_pos = self._get_party_leader_position()

            # Get current state (use last_state if available, otherwise use current_state)
            state = self.last_state if self.last_state is not None else current_state

            # Draw the overlay
            self._draw_debug_overlay(my_pos, leader_pos, self.last_target_pos, state)
        except Exception as e:
            # Silently fail on debug UI errors
            print(f"FollowPartyLeaderOnlyUtility.draw_overlay error: {e}")

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        """Draw debug overlay and status info"""

        if PyImGui.collapsing_header("Follow Leader Only Status", PyImGui.TreeNodeFlags.DefaultOpen):

            PyImGui.text_colored("Configuration is in Party UI -> [EXPLORABLE] Following settings", (1.0, 1.0, 0.0, 1.0))
            PyImGui.separator()

            if self._am_i_party_leader():
                PyImGui.text_colored("You are the party leader", (1.0, 0.84, 0.0, 1.0))  # Gold
                PyImGui.text("Leaders don't follow anyone")
                PyImGui.separator()
            else:
                # Configuration for followers
                PyImGui.text_colored("Configuration:", (1.0, 1.0, 1.0, 1.0))

                # Follow distance slider
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, Utils.ColorToTuple(Utils.RGBToColor(255, 215, 0, 100)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, Utils.ColorToTuple(Utils.RGBToColor(255, 215, 0, 150)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, Utils.ColorToTuple(Utils.RGBToColor(255, 215, 0, 180)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrab, Utils.ColorToTuple(Utils.RGBToColor(255, 215, 0, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrabActive, Utils.ColorToTuple(Utils.RGBToColor(255, 215, 0, 255)))

                self.manager.follow_distance = PyImGui.slider_float(
                    "Follow Distance",
                    self.manager.follow_distance,
                    50.0,
                    300.0
                )
                PyImGui.pop_style_color(5)
                PyImGui.same_line(0.0, -1.0)
                PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
                if PyImGui.is_item_hovered():
                    PyImGui.set_tooltip("Distance to maintain from party leader")

                PyImGui.separator()

            # Status
            PyImGui.text("Status:")
            PyImGui.bullet_text(f"Throttle Timer: {self.throttle_timer.GetTimeRemaining()}ms")

            if self.last_state is not None:
                state_name = self.last_state.name if hasattr(self.last_state, 'name') else str(self.last_state)

                # Color state based on combat/non-combat
                if self.last_state == BehaviorState.IN_AGGRO:
                    state_color = (1.0, 0.0, 0.0, 1.0)  # Red for combat
                else:
                    state_color = (0.0, 1.0, 0.0, 1.0)  # Green for non-combat

                PyImGui.text_colored(f"  • Current State: {state_name}", state_color)

                follow_dist = self._get_follow_distance_for_state(self.last_state)
                PyImGui.text_colored(f"  • Follow Distance: {follow_dist:.1f}", (1.0, 0.84, 0.0, 1.0))  # Gold

            if not self._am_i_party_leader():
                leader_pos = self._get_party_leader_position()
                if leader_pos:
                    my_pos = Player.GetXY()
                    if my_pos and len(my_pos) == 2:
                        dx = leader_pos[0] - my_pos[0]
                        dy = leader_pos[1] - my_pos[1]
                        distance = math.sqrt(dx * dx + dy * dy)
                        PyImGui.text_colored(f"  • Distance to Leader: {distance:.1f}", (1.0, 0.84, 0.0, 1.0))  # Gold
