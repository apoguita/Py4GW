import math
from typing import Any, Generator, override
import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Routines, Range
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer, Utils, VectorFields
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib.AgentArray import AgentArray
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.parties.party_following_manager import PartyFollowingManager
from Widgets.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Widgets.CustomBehaviors.primitives.scores.score_per_status_definition import ScorePerStatusDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus

class FollowPartyLeaderNewUtility(CustomSkillUtilityBase):
    """
    Utility that follows party leader with configurable spread behavior.
    
    Two modes:
    - IN_AGGRO: Tight formation with spreading (avoid clustering during combat)
    - CLOSE_TO_AGGRO/FAR_FROM_AGGRO: Loose formation (follow at distance)
    
    Features:
    - Follows party leader at configured distance
    - Spreads from nearby allies using repulsion forces
    - Different parameters for combat vs non-combat
    - Party leaders are automatically excluded
    """

    def __init__(
            self,
            event_bus: EventBus,
            current_build: list[CustomSkill]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("follow_party_leader_new"),
            in_game_build=current_build,
            score_definition= ScorePerStatusDefinition(lambda state: CommonScore.FOLLOW_FLAG_REQUIRED.value if state == BehaviorState.IN_AGGRO else CommonScore.FOLLOW.value),
            allowed_states=[BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO],
            utility_skill_typology=UtilitySkillTypology.FOLLOWING)

        self.throttle_timer = ThrottledTimer(800)
        self.score_definition : ScorePerStatusDefinition = ScorePerStatusDefinition(lambda state: CommonScore.FOLLOW_FLAG_REQUIRED.value if state == BehaviorState.IN_AGGRO else CommonScore.FOLLOW.value)

        # Use singleton manager for all configuration
        self.manager = PartyFollowingManager()

        # Hard-coded movement parameters (removed from shared memory)
        self.follow_distance_tolerance = 50.0  # Tolerance for follow distance
        self.min_move_threshold = 0.5  # Minimum vector magnitude to trigger movement
        self.max_move_distance = 250.0  # Maximum distance to move in one step

        # Debug
        self.last_target_pos = None
        self.last_result_vector = None
        self.last_state = None

    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        # Don't follow leader if this player has a defined flag position (should follow flag instead)
        if CustomBehaviorParty().party_flagging_manager.is_flag_defined(GLOBAL_CACHE.Player.GetAccountEmail()): return False
        return True

    def _get_party_leader_position(self) -> tuple[float, float] | None:
        """Get position of party leader (first player in party)"""
        try:
            leader_agent_id = GLOBAL_CACHE.Party.GetPartyLeaderID()
            if leader_agent_id is None:
                return None
            
            if not GLOBAL_CACHE.Agent.IsAlive(leader_agent_id):
                return None
            
            pos = GLOBAL_CACHE.Agent.GetXY(leader_agent_id)
            if pos is None or len(pos) != 2:
                return None
            
            return pos
        except Exception as e:
            print(f"FollowPartyLeaderNewUtility._get_party_leader_position error: {e}")
            return None
    
    def _am_i_party_leader(self) -> bool:
        return GLOBAL_CACHE.Party.IsPartyLeader()

    def _get_party_member_positions(self) -> list[tuple[float, float]]:
        
        positions = []
        for agent_id in AgentArray.GetAllyArray():
            if GLOBAL_CACHE.Agent.IsAlive(agent_id) and GLOBAL_CACHE.Agent.IsValid(agent_id):
                positions.append(GLOBAL_CACHE.Agent.GetXY(agent_id))

        for agent_id in AgentArray.GetSpiritPetArray():
            if GLOBAL_CACHE.Agent.IsAlive(agent_id) and GLOBAL_CACHE.Agent.IsValid(agent_id):
                positions.append(GLOBAL_CACHE.Agent.GetXY(agent_id))

        return positions

    def _get_parameters_for_state(self, state: BehaviorState) -> tuple[float, float, float]:
        """Get parameters based on current state"""
        if state == BehaviorState.IN_AGGRO:
            return (self.manager.combat_follow_distance,
                    self.manager.combat_spread_threshold,
                    self.manager.combat_repulsion_weight)
        else:
            return (self.manager.noncombat_follow_distance,
                    self.manager.noncombat_spread_threshold,
                    self.manager.noncombat_repulsion_weight)

    def _calculate_follow_spread_position(self, my_pos: tuple[float, float],
                                          leader_pos: tuple[float, float],
                                          party_positions: list[tuple[float, float]],
                                          state: BehaviorState) -> tuple[float, float] | None:
        """
        Calculate target position using VectorFields:
        1. Stays at follow_distance from leader (attraction/repulsion)
        2. Spreads from nearby allies (repulsion)
        """

        # Get parameters for current state
        follow_distance, spread_threshold, repulsion_weight = self._get_parameters_for_state(state)

        # Step 1: Calculate leader following vector manually (for better control)
        dx = leader_pos[0] - my_pos[0]
        dy = leader_pos[1] - my_pos[1]
        distance_to_leader = math.sqrt(dx * dx + dy * dy)

        # Calculate how much we need to move toward/away from leader
        distance_error = distance_to_leader - follow_distance

        # Define "far" threshold - if farther than this, move directly toward leader
        far_threshold = follow_distance * 2.0  # 2x the follow distance

        # Initialize result vector with leader following component
        if abs(distance_error) > self.follow_distance_tolerance:
            # Need to adjust distance to leader
            if distance_to_leader > 0:
                # Direction toward leader
                norm_dx = dx / distance_to_leader
                norm_dy = dy / distance_to_leader

                # Only move if we're TOO FAR from leader (not too close)
                # If we're inside the follow distance, don't force movement away
                if distance_error > 0:  # Too far from leader
                    if distance_to_leader > far_threshold:
                        # Very far from leader - move directly toward them (no damping)
                        # Move the full distance error (clamped by max_move_distance later)
                        move_amount = distance_error
                    else:
                        # Close enough - use damping to prevent overshooting
                        move_amount = distance_error * 0.8  # Move 80% of the error

                    result_vector_x = norm_dx * move_amount
                    result_vector_y = norm_dy * move_amount
                else:
                    # Too close to leader - don't force movement away, let spreading handle it
                    result_vector_x = 0.0
                    result_vector_y = 0.0
            else:
                result_vector_x = 0.0
                result_vector_y = 0.0
        else:
            # Within tolerance, no leader adjustment needed
            result_vector_x = 0.0
            result_vector_y = 0.0

        # Step 2: Add spreading forces using VectorFields (only if not too far from leader)
        if distance_to_leader <= far_threshold and len(party_positions) > 0:
            vf = VectorFields(my_pos, custom_repulsion_radius=int(spread_threshold))

            # Add repulsion from nearby allies
            for ally_pos in party_positions:
                vf.add_custom_repulsion_position(ally_pos)

            # Compute spreading vector
            spread_vector = vf.compute_combined_vector()

            # Add spreading component (scaled by repulsion weight)
            result_vector_x += spread_vector[0] * repulsion_weight
            result_vector_y += spread_vector[1] * repulsion_weight
        # If too far from leader, ignore spreading - just catch up!

        # Step 3: Calculate final magnitude
        vector_magnitude = math.sqrt(result_vector_x * result_vector_x + result_vector_y * result_vector_y)

        # Store for debug
        self.last_result_vector = (result_vector_x, result_vector_y, vector_magnitude)

        # Only move if vector is significant
        if vector_magnitude < self.min_move_threshold:
            return None

        # Limit movement distance to prevent overshooting
        # BUT: If in FAR MODE, don't clamp - move the full distance!
        far_threshold = follow_distance * 2.0
        is_far = distance_to_leader > far_threshold

        if not is_far and vector_magnitude > self.max_move_distance:
            # Only clamp when NOT in far mode
            scale = self.max_move_distance / vector_magnitude
            result_vector_x *= scale
            result_vector_y *= scale
        # When in far mode, don't clamp - move the full distance in one go!

        # Calculate target position
        target_x = my_pos[0] + result_vector_x
        target_y = my_pos[1] + result_vector_y

        return (target_x, target_y)

    def _draw_debug_overlay(self, my_pos: tuple[float, float],
                           leader_pos: tuple[float, float] | None,
                           party_positions: list[tuple[float, float]],
                           target_pos: tuple[float, float] | None,
                           state: BehaviorState) -> None:
        """Draw debug overlay showing leader, allies, and target"""
        if not self.manager.enable_debug_overlay:
            return

        # Get parameters for current state
        follow_distance, spread_threshold, repulsion_weight = self._get_parameters_for_state(state)

        Overlay().BeginDraw()
        my_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        _, _, my_z = GLOBAL_CACHE.Agent.GetXYZ(my_agent_id)

        # Determine state color for visual feedback
        if state == BehaviorState.IN_AGGRO:
            state_color = Utils.RGBToColor(255, 0, 0, 255)  # Red for combat
            circle_color = Utils.RGBToColor(255, 0, 0, 80)  # Red transparent
        else:
            state_color = Utils.RGBToColor(0, 255, 0, 255)  # Green for non-combat
            circle_color = Utils.RGBToColor(0, 255, 0, 80)  # Green transparent

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

        # Draw spread threshold circle around me (state-colored)
        Overlay().DrawPoly3D(my_pos[0], my_pos[1], my_z, spread_threshold,
                            circle_color, numsegments=32, thickness=3.0)

        # Draw party members (red circles) and repulsion lines
        for ally_pos in party_positions:
            Overlay().DrawPolyFilled3D(ally_pos[0], ally_pos[1], my_z, 40,
                                      Utils.RGBToColor(255, 0, 0, 150), numsegments=16)

            distance = Utils.Distance(my_pos, ally_pos)
            if distance < spread_threshold:
                # Draw repulsion line (orange) with distance
                Overlay().DrawLine3D(my_pos[0], my_pos[1], my_z,
                                    ally_pos[0], ally_pos[1], my_z,
                                    Utils.RGBToColor(255, 100, 0, 200), thickness=3.0)

                # Draw distance to ally
                mid_x = (my_pos[0] + ally_pos[0]) / 2
                mid_y = (my_pos[1] + ally_pos[1]) / 2
                Overlay().DrawText3D(mid_x, mid_y, my_z - 50,
                                   f"{distance:.0f}",
                                   Utils.RGBToColor(255, 100, 0, 255),
                                   autoZ=False, centered=True, scale=0.8)

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

        # Draw state and active parameters (top of screen)
        state_name = state.name if hasattr(state, 'name') else str(state)

        # Check if in "far mode"
        far_threshold = follow_distance * 2.0
        is_far = False
        if leader_pos is not None:
            current_distance = Utils.Distance(my_pos, leader_pos)
            is_far = current_distance > far_threshold

        # Main state indicator
        state_text = f"STATE: {state_name}"
        if is_far:
            state_text += " [FAR - CATCHING UP]"
        Overlay().DrawText3D(my_pos[0], my_pos[1], my_z - 200,
                           state_text,
                           state_color,
                           autoZ=False, centered=True, scale=1.0)

        # Active parameters
        params_text = f"Follow: {follow_distance:.0f} | Spread: {spread_threshold:.0f} | Weight: {repulsion_weight:.0f}"
        if is_far:
            params_text += " | SPREADING DISABLED"
        Overlay().DrawText3D(my_pos[0], my_pos[1], my_z - 250,
                           params_text,
                           state_color,
                           autoZ=False, centered=True, scale=0.9)

        # Vector info
        if self.last_result_vector is not None:
            vx, vy, vmag = self.last_result_vector
            info_text = f"Vector: ({vx:.1f}, {vy:.1f}) | Mag: {vmag:.1f}"
            Overlay().DrawText3D(my_pos[0], my_pos[1], my_z - 300,
                               info_text, Utils.RGBToColor(255, 255, 255, 255),
                               autoZ=False, centered=True, scale=0.8)

        Overlay().EndDraw()

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if self.allowed_states is not None and current_state not in self.allowed_states:
            return None

        if not self.throttle_timer.IsExpired():
            return None

        my_pos = GLOBAL_CACHE.Player.GetXY()
        if my_pos is None or len(my_pos) != 2:
            return None

        # Leaders don't follow
        if self._am_i_party_leader():
            return None
        
        # Check if we need to move
        leader_pos = self._get_party_leader_position()
        if leader_pos is None:
            return None
        
        # Get parameters for current state
        follow_distance, spread_threshold, _ = self._get_parameters_for_state(current_state)
        
        # Calculate distance to leader
        dx = leader_pos[0] - my_pos[0]
        dy = leader_pos[1] - my_pos[1]
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Check if we need to adjust position (either for following or spreading)
        party_positions = self._get_party_member_positions()
        
        # Need to move if: outside follow tolerance OR clustered with allies
        outside_tolerance = abs(distance - follow_distance) > self.manager.follow_distance_tolerance
        
        is_clustered = False
        for ally_pos in party_positions:
            ally_distance = Utils.Distance(my_pos, ally_pos)
            if ally_distance < spread_threshold:
                is_clustered = True
                break
        
        if outside_tolerance or is_clustered:
            return self.score_definition.get_score(current_state)
        
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        
        try:
            self.last_state = state
            
            my_pos = GLOBAL_CACHE.Player.GetXY()
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
            
            party_positions = self._get_party_member_positions()
            if party_positions is None:
                party_positions = []
            
            # Calculate target position (follow + spread)
            target_pos = self._calculate_follow_spread_position(my_pos, leader_pos, party_positions, state)
            
            # Store for debug UI
            self.last_target_pos = target_pos
            
            # Move if we have a valid target
            if target_pos is not None:
                GLOBAL_CACHE.Player.Move(target_pos[0], target_pos[1])
                self.throttle_timer.Reset()
                yield from custom_behavior_helpers.Helpers.wait_for(1000)
                return BehaviorResult.ACTION_PERFORMED
            
            yield
            return BehaviorResult.ACTION_SKIPPED
            
        except Exception as e:
            print(f"FollowPartyLeaderNewUtility._execute error: {e}")
            yield
            return BehaviorResult.ACTION_SKIPPED

    def draw_overlay(self, current_state: BehaviorState) -> None:
        """
        Draw debug overlay showing following behavior visualization.
        This is the public method to be called from GUI.
        """
        # Only draw if enabled
        if not self.manager.enable_debug_overlay:
            return

        try:
            # Get current positions
            my_pos = GLOBAL_CACHE.Player.GetXY()
            if my_pos is None or len(my_pos) != 2:
                return

            leader_pos = self._get_party_leader_position()

            party_positions = self._get_party_member_positions()
            if party_positions is None:
                party_positions = []

            # Get current state (use last_state if available, otherwise use current_state)
            state = self.last_state if self.last_state is not None else current_state

            # Draw the overlay
            self._draw_debug_overlay(my_pos, leader_pos, party_positions, self.last_target_pos, state)
        except Exception as e:
            # Silently fail on debug UI errors
            print(f"FollowPartyLeaderNewUtility.draw_overlay error: {e}")

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        """Draw debug overlay and status info"""

        if PyImGui.collapsing_header("Follow Leader (New) Status", PyImGui.TreeNodeFlags.DefaultOpen):

            PyImGui.text_colored("Configuration is in Party UI -> [EXPLORABLE] Following settings", (1.0, 1.0, 0.0, 1.0))
            PyImGui.separator()

            if self._am_i_party_leader():
                PyImGui.text_colored("You are the party leader", (1.0, 0.84, 0.0, 1.0))  # Gold
                PyImGui.text("Leaders don't follow anyone")
                PyImGui.separator()

            # Overlay color legend
            PyImGui.text_colored("Overlay Colors:", (1.0, 1.0, 1.0, 1.0))
            PyImGui.text_colored("  • My Position", (0.0, 0.39, 1.0, 1.0))  # Blue (0, 100, 255)
            PyImGui.text_colored("  • Leader Position", (1.0, 0.84, 0.0, 1.0))  # Gold (255, 215, 0)
            PyImGui.text_colored("  • Party Members", (1.0, 0.0, 0.0, 1.0))  # Red (255, 0, 0)
            PyImGui.text_colored("  • Target Position", (0.0, 1.0, 0.0, 1.0))  # Green (0, 255, 0)
            PyImGui.text_colored("  • Repulsion Lines", (1.0, 0.39, 0.0, 1.0))  # Orange (255, 100, 0)
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

                follow_dist, spread_thresh, repul_weight = self._get_parameters_for_state(self.last_state)
                PyImGui.text_colored(f"  • Follow Distance: {follow_dist:.1f}", (1.0, 0.84, 0.0, 1.0))  # Gold
                PyImGui.text_colored(f"  • Spread Threshold: {spread_thresh:.1f}", state_color)
                PyImGui.text_colored(f"  • Repulsion Weight: {repul_weight:.1f}", (1.0, 0.39, 0.0, 1.0))  # Orange

            if not self._am_i_party_leader():
                leader_pos = self._get_party_leader_position()
                if leader_pos:
                    my_pos = GLOBAL_CACHE.Player.GetXY()
                    if my_pos and len(my_pos) == 2:
                        dx = leader_pos[0] - my_pos[0]
                        dy = leader_pos[1] - my_pos[1]
                        distance = math.sqrt(dx * dx + dy * dy)
                        PyImGui.text_colored(f"  • Distance to Leader: {distance:.1f}", (1.0, 0.84, 0.0, 1.0))  # Gold

            if self.last_result_vector is not None:
                vx, vy, vmag = self.last_result_vector
                PyImGui.text_colored(f"  • Last Vector: ({vx:.1f}, {vy:.1f})", (0.0, 1.0, 0.0, 1.0))  # Green
                PyImGui.text_colored(f"  • Vector Magnitude: {vmag:.1f}", (0.0, 1.0, 0.0, 1.0))  # Green

            party_count = len(self._get_party_member_positions())
            PyImGui.text_colored(f"  • Party Members: {party_count}", (1.0, 0.0, 0.0, 1.0))  # Red

