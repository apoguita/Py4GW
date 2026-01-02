import math
from typing import Any, Generator, override
import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Map, Range
from Py4GWCoreLib.Pathing import AutoPathing
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer, Utils, VectorFields
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib.AgentArray import AgentArray
from Widgets.CustomBehaviors.primitives.bus.event_message import EventMessage
from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.parties.party_following_manager import PartyFollowingManager
from Widgets.CustomBehaviors.primitives.scores.comon_score import CommonScore
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology
from Widgets.CustomBehaviors.primitives.bus.event_bus import EventBus
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition

class SpreadDuringCombatUtility(CustomSkillUtilityBase):
    """
    Utility that handles spreading behavior during combat for all players (including leaders).

    Features:
    - Spreads from nearby allies using repulsion forces
    - Spreads from nearby spirits using repulsion forces
    - Spreads from nearby enemies using repulsion forces
    - Attracts toward party leader using attraction forces
    - Works for all players including party leaders
    - Only active during combat (IN_AGGRO state)
    """

    def __init__(
            self,
            event_bus: EventBus,
            current_build: list[CustomSkill]
        ) -> None:

        super().__init__(
            event_bus=event_bus,
            skill=CustomSkill("spread_during_combat"),
            in_game_build=current_build,
            score_definition=ScoreStaticDefinition(CommonScore.FOLLOW.value),
            allowed_states=[BehaviorState.IN_AGGRO],  # Only during combat
            utility_skill_typology=UtilitySkillTypology.FOLLOWING)

        self.throttle_timer = ThrottledTimer(800)
        self.score_definition: ScoreStaticDefinition = ScoreStaticDefinition(CommonScore.FOLLOW.value)
        self.manager: PartyFollowingManager = CustomBehaviorParty().party_following_manager

        # Debug
        self.last_target_pos = None
        self.last_result_vector = None

        # Instance-specific enable flags (not shared across party)
        self.enable_enemy_repulsion = False
        self.enable_leader_attraction = False
        self.enable_allies_repulsion = False

        self.event_bus.subscribe(EventType.MAP_CHANGED, self.area_changed, subscriber_name=self.custom_skill.skill_name)
    
    def area_changed(self, message: EventMessage)-> Generator[Any, Any, Any]:
        if Map.IsExplorable():
            self.enable_enemy_repulsion = False if GLOBAL_CACHE.Agent.IsMelee(GLOBAL_CACHE.Player.GetAgentID()) else True
            self.enable_leader_attraction = True
            self.enable_allies_repulsion = False if GLOBAL_CACHE.Agent.IsMelee(GLOBAL_CACHE.Player.GetAgentID()) else True
        yield
        


    @override
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:

        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        if GLOBAL_CACHE.Party.IsPartyLeader(): return False
        # Only run if this player has a defined flag position (spread around flag)
        if CustomBehaviorParty().party_flagging_manager.is_flag_defined(GLOBAL_CACHE.Player.GetAccountEmail()): return False

        return True

    def _get_party_member_positions(self) -> list[tuple[float, float]]:
        """Get positions of all party members (allies and spirits)"""
        positions = []
        
        # Get ally positions
        for agent_id in AgentArray.GetAllyArray():
            if GLOBAL_CACHE.Agent.IsAlive(agent_id) and GLOBAL_CACHE.Agent.IsValid(agent_id):
                # Exclude self
                if agent_id != GLOBAL_CACHE.Player.GetAgentID():
                    positions.append(GLOBAL_CACHE.Agent.GetXY(agent_id))

        # Get spirit positions
        for agent_id in AgentArray.GetSpiritPetArray():
            if GLOBAL_CACHE.Agent.IsAlive(agent_id) and GLOBAL_CACHE.Agent.IsValid(agent_id):
                positions.append(GLOBAL_CACHE.Agent.GetXY(agent_id))

        return positions

    def _get_enemy_positions(self) -> list[tuple[float, float]]:
        """Get positions of nearby enemies for repulsion"""
        if not self.enable_enemy_repulsion:
            return []

        positions = []
        my_pos = GLOBAL_CACHE.Player.GetXY()
        if my_pos is None:
            return []

        try:
            # Get nearby enemies
            enemy_array = AgentArray.GetEnemyArray()
            for enemy_id in enemy_array:
                if not GLOBAL_CACHE.Agent.IsAlive(enemy_id) or not GLOBAL_CACHE.Agent.IsValid(enemy_id):
                    continue

                enemy_pos = GLOBAL_CACHE.Agent.GetXY(enemy_id)
                if enemy_pos is None:
                    continue

                # Check distance
                distance = Utils.Distance(my_pos, enemy_pos)
                if distance <= self.manager.enemy_repulsion_threshold:
                    positions.append(enemy_pos)

        except Exception as e:
            print(f"SpreadDuringCombatUtility._get_enemy_positions error: {e}")

        return positions

    def _get_party_leader_position(self) -> tuple[float, float] | None:
        """Get the position of the party leader"""
        try:
            leader_agent_id = GLOBAL_CACHE.Party.GetPartyLeaderID()
            if leader_agent_id is None:
                return None

            leader_pos = GLOBAL_CACHE.Agent.GetXY(leader_agent_id)
            return leader_pos
        except Exception as e:
            print(f"SpreadDuringCombatUtility._get_party_leader_position error: {e}")
            return None

    def _calculate_finale_position(self, my_pos: tuple[float, float]) -> tuple[float, float] | None:
        """
        Calculate target position using single VectorFields instance combining:
        1. Repulsion from allies (party members & spirits)
        2. Repulsion from enemies
        3. Attraction to leader
        All forces are combined in one VectorFields calculation.
        """

        party_positions: list[tuple[float, float]] = self._get_party_member_positions() if self.enable_allies_repulsion else []
        enemy_positions: list[tuple[float, float]] = self._get_enemy_positions() if self.enable_enemy_repulsion else []
        leader_pos: tuple[float, float] | None = self._get_party_leader_position() if self.enable_leader_attraction else None

        # Create single VectorFields instance with combined radii
        # Use the largest radius to encompass all force types
        # For attraction, we need a much larger radius to handle long distances
        max_repulsion_radius = max(
            self.manager.allies_repulsion_threshold if self.enable_allies_repulsion else 0,
            self.manager.enemy_repulsion_threshold if self.enable_enemy_repulsion else 0
        )

        # For attraction, use a larger radius to handle long-distance leader attraction
        max_attraction_radius = 1500.0  # Large enough to handle most leader distances

        max_radius = max(max_repulsion_radius, max_attraction_radius)
        if max_radius == 0: return None  # No forces enabled

        vf = VectorFields(
            my_pos,
            custom_repulsion_radius=int(max_repulsion_radius) if max_repulsion_radius > 0 else 100,
            custom_attraction_radius=int(max_attraction_radius)
        )

        # 1. Add allies repulsion positions (with distance check)
        if self.enable_allies_repulsion and party_positions:
            for ally_pos in party_positions:
                distance = Utils.Distance(my_pos, ally_pos)
                if distance < self.manager.allies_repulsion_threshold:
                    vf.add_custom_repulsion_position(ally_pos)

        # 2. Add enemy repulsion positions (with distance check)
        if self.enable_enemy_repulsion and enemy_positions:
            for enemy_pos in enemy_positions:
                distance = Utils.Distance(my_pos, enemy_pos)
                if distance < self.manager.enemy_repulsion_threshold:
                    vf.add_custom_repulsion_position(enemy_pos)

        # 3. Add leader attraction position (with distance check)
        if self.enable_leader_attraction and leader_pos is not None:
            distance_to_leader = Utils.Distance(my_pos, leader_pos)
            print(f"Leader attraction: distance={distance_to_leader:.1f}, threshold={self.manager.leader_attraction_threshold:.1f}")
            # Only attract if beyond threshold to avoid clustering on leader
            if distance_to_leader > self.manager.leader_attraction_threshold:
                vf.add_custom_attraction_position(leader_pos)
                print(f"Added leader attraction position: {leader_pos}")
            else:
                print(f"Leader attraction: distance {distance_to_leader:.1f} <= threshold {self.manager.leader_attraction_threshold:.1f}, no attraction")

        # Compute combined vector from all forces
        combined_vector = vf.compute_combined_vector()
        print(f"Combined vector from VectorFields: ({combined_vector[0]:.2f}, {combined_vector[1]:.2f})")

        # Apply weights by scaling the vector components
        result_vector_x = combined_vector[0]
        result_vector_y = combined_vector[1]

        # Apply movement scaling to the final vector
        # This applies to all movement types (allies, enemies, leader)
        if vector_magnitude := math.sqrt(result_vector_x * result_vector_x + result_vector_y * result_vector_y):
            # Calculate movement scaling based on active forces and distances
            movement_scale = self._calculate_movement_scale(my_pos, party_positions, enemy_positions, leader_pos)

            # Apply scaling to the vector
            result_vector_x *= movement_scale
            result_vector_y *= movement_scale

            # Recalculate magnitude after scaling
            vector_magnitude = math.sqrt(result_vector_x * result_vector_x + result_vector_y * result_vector_y)

            print(f"Applied movement scale: {movement_scale:.2f}")
            print(f"Scaled vector: ({result_vector_x:.2f}, {result_vector_y:.2f}), magnitude={vector_magnitude:.2f}")

        # Store for debug
        self.last_result_vector = (result_vector_x, result_vector_y, vector_magnitude)

        print(f"Final vector: ({result_vector_x:.2f}, {result_vector_y:.2f}), magnitude={vector_magnitude:.2f}")
        print(f"Min threshold: {self.manager.min_move_threshold:.2f}")

        # Only move if vector is significant
        if vector_magnitude < self.manager.min_move_threshold:
            print(f"Vector magnitude {vector_magnitude:.2f} < threshold {self.manager.min_move_threshold:.2f}, not moving")
            return None

        # Limit movement distance to prevent overshooting
        if vector_magnitude > self.manager.max_move_distance:
            scale = self.manager.max_move_distance / vector_magnitude
            result_vector_x *= scale
            result_vector_y *= scale

        # Calculate target position
        target_x = my_pos[0] + result_vector_x
        target_y = my_pos[1] + result_vector_y

        return (target_x, target_y)

    def _calculate_movement_scale(self, my_pos: tuple[float, float],
                                party_positions: list[tuple[float, float]],
                                enemy_positions: list[tuple[float, float]],
                                leader_pos: tuple[float, float] | None) -> float:
        """
        Calculate movement scaling factor based on active forces and distances.
        This applies to all movement types for consistent scaling.
        """
        base_scale = 50.0  # Base movement multiplier

        # Start with base scale
        total_scale = base_scale

        # Scale based on leader distance if leader attraction is active
        if self.enable_leader_attraction and leader_pos is not None:
            distance_to_leader = Utils.Distance(my_pos, leader_pos)
            if distance_to_leader > self.manager.leader_attraction_threshold:
                # Farther from leader = larger steps
                leader_distance_factor = min(distance_to_leader / 200.0, 5.0)
                leader_weight_factor = self.manager.leader_attraction_weight / 100.0
                total_scale *= leader_distance_factor * leader_weight_factor
                print(f"Leader scaling: distance={distance_to_leader:.1f}, distance_factor={leader_distance_factor:.2f}, weight_factor={leader_weight_factor:.2f}")

        # Scale based on ally repulsion if active
        if self.enable_allies_repulsion and party_positions:
            close_allies = sum(1 for ally_pos in party_positions
                             if Utils.Distance(my_pos, ally_pos) < self.manager.allies_repulsion_threshold)
            if close_allies > 0:
                ally_weight_factor = self.manager.allies_repulsion_weight / 100.0
                total_scale *= ally_weight_factor
                print(f"Ally scaling: close_allies={close_allies}, weight_factor={ally_weight_factor:.2f}")

        # Scale based on enemy repulsion if active
        if self.enable_enemy_repulsion and enemy_positions:
            close_enemies = sum(1 for enemy_pos in enemy_positions
                              if Utils.Distance(my_pos, enemy_pos) < self.manager.enemy_repulsion_threshold)
            if close_enemies > 0:
                enemy_weight_factor = self.manager.enemy_repulsion_weight / 100.0
                total_scale *= enemy_weight_factor
                print(f"Enemy scaling: close_enemies={close_enemies}, weight_factor={enemy_weight_factor:.2f}")

        # Ensure minimum scale
        total_scale = max(total_scale, 1.0)

        return total_scale

    def _draw_debug_overlay_2(self, my_pos: tuple[float, float],
                           party_positions: list[tuple[float, float]],
                           enemy_positions: list[tuple[float, float]],
                           leader_pos: tuple[float, float] | None,
                           target_pos: tuple[float, float] | None) -> None:
        """
        Advanced debug overlay showing vector field forces and resultant vector
        """
        if not self.manager.enable_debug_overlay:
            return

        Overlay().BeginDraw()
        my_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        _, _, my_z = GLOBAL_CACHE.Agent.GetXYZ(my_agent_id)

        # Color scheme for different force types
        player_color = Utils.RGBToColor(0, 150, 255, 255)  # Blue
        ally_color = Utils.RGBToColor(255, 100, 0, 255)    # Orange
        enemy_color = Utils.RGBToColor(255, 0, 255, 255)   # Magenta
        leader_color = Utils.RGBToColor(255, 215, 0, 255)  # Gold
        target_color = Utils.RGBToColor(0, 255, 0, 255)    # Green
        vector_color = Utils.RGBToColor(255, 255, 255, 255) # White

        # Draw player position (large blue circle)
        Overlay().DrawPolyFilled3D(my_pos[0], my_pos[1], my_z, 60, Utils.RGBToColor(0, 150, 255, 150), numsegments=16)
        Overlay().DrawPoly3D(my_pos[0], my_pos[1], my_z, 60, player_color, numsegments=16, thickness=4.0)

        # Draw force radius circles
        max_radius = max(
            self.manager.allies_repulsion_threshold if self.enable_allies_repulsion else 0,
            self.manager.enemy_repulsion_threshold if self.enable_enemy_repulsion else 0,
            self.manager.leader_attraction_threshold if self.enable_leader_attraction else 0
        )

        if max_radius > 0:
            Overlay().DrawPoly3D(my_pos[0], my_pos[1], my_z, max_radius, Utils.RGBToColor(128, 128, 128, 100), numsegments=32, thickness=2.0)

        # 1. ALLIES REPULSION FORCES
        if self.enable_allies_repulsion:
            # Draw allies repulsion threshold circle
            Overlay().DrawPoly3D(my_pos[0], my_pos[1], my_z, self.manager.allies_repulsion_threshold, Utils.RGBToColor(255, 100, 0, 80), numsegments=32, thickness=2.0)

            for ally_pos in party_positions:
                distance = Utils.Distance(my_pos, ally_pos)

                # Draw ally position
                Overlay().DrawPolyFilled3D(ally_pos[0], ally_pos[1], my_z, 40, Utils.RGBToColor(255, 100, 0, 150), numsegments=16)

                if distance < self.manager.allies_repulsion_threshold and distance > 0:
                    # Draw repulsion force vector (from ally to player)
                    force_scale = (self.manager.allies_repulsion_threshold - distance) / self.manager.allies_repulsion_threshold
                    force_length = force_scale * 100  # Visual scaling

                    # Calculate repulsion direction (away from ally)
                    dx = (my_pos[0] - ally_pos[0]) / distance if distance > 0 else 0
                    dy = (my_pos[1] - ally_pos[1]) / distance if distance > 0 else 0

                    # Draw force vector
                    end_x = my_pos[0] + dx * force_length
                    end_y = my_pos[1] + dy * force_length
                    Overlay().DrawLine3D(my_pos[0], my_pos[1], my_z, end_x, end_y, my_z, ally_color, thickness=3.0)


        # 2. ENEMY REPULSION FORCES
        if self.enable_enemy_repulsion:
            # Draw enemy repulsion threshold circle
            Overlay().DrawPoly3D(my_pos[0], my_pos[1], my_z, self.manager.enemy_repulsion_threshold, Utils.RGBToColor(255, 0, 255, 80), numsegments=32, thickness=2.0)

            for enemy_pos in enemy_positions:
                distance = Utils.Distance(my_pos, enemy_pos)

                # Draw enemy position
                Overlay().DrawPolyFilled3D(enemy_pos[0], enemy_pos[1], my_z, 45,
                                          Utils.RGBToColor(255, 0, 255, 150), numsegments=16)

                if distance < self.manager.enemy_repulsion_threshold and distance > 0:
                    # Draw repulsion force vector (from enemy to player)
                    force_scale = (self.manager.enemy_repulsion_threshold - distance) / self.manager.enemy_repulsion_threshold
                    force_length = force_scale * 120  # Visual scaling

                    # Calculate repulsion direction (away from enemy)
                    dx = (my_pos[0] - enemy_pos[0]) / distance if distance > 0 else 0
                    dy = (my_pos[1] - enemy_pos[1]) / distance if distance > 0 else 0

                    # Draw force vector
                    end_x = my_pos[0] + dx * force_length
                    end_y = my_pos[1] + dy * force_length

                    Overlay().DrawLine3D(my_pos[0], my_pos[1], my_z, end_x, end_y, my_z, enemy_color, thickness=4.0)

        # 3. LEADER ATTRACTION FORCE
        if self.enable_leader_attraction and leader_pos is not None:
            distance_to_leader = Utils.Distance(my_pos, leader_pos)

            # Draw leader position (large gold circle)
            Overlay().DrawPolyFilled3D(leader_pos[0], leader_pos[1], my_z, 70, Utils.RGBToColor(255, 215, 0, 150), numsegments=16)
            Overlay().DrawPoly3D(leader_pos[0], leader_pos[1], my_z, 70, leader_color, numsegments=16, thickness=4.0)

            # Draw leader attraction threshold circle
            Overlay().DrawPoly3D(leader_pos[0], leader_pos[1], my_z, self.manager.leader_attraction_threshold, Utils.RGBToColor(255, 215, 0, 80), numsegments=32, thickness=2.0)

            if distance_to_leader > self.manager.leader_attraction_threshold:
                # Draw attraction force vector (from player to leader)
                force_scale = (distance_to_leader - self.manager.leader_attraction_threshold) / self.manager.leader_attraction_threshold
                force_scale = min(force_scale, 2.0)  # Cap at 2x
                force_length = force_scale * 100  # Visual scaling

                # Calculate attraction direction (toward leader)
                dx = (leader_pos[0] - my_pos[0]) / distance_to_leader if distance_to_leader > 0 else 0
                dy = (leader_pos[1] - my_pos[1]) / distance_to_leader if distance_to_leader > 0 else 0

                # Draw force vector
                end_x = my_pos[0] + dx * force_length
                end_y = my_pos[1] + dy * force_length

                Overlay().DrawLine3D(my_pos[0], my_pos[1], my_z, end_x, end_y, my_z, leader_color, thickness=4.0)

        # 4. RESULTANT VECTOR AND TARGET
        if target_pos is not None:
            # Draw target position (large green circle)
            Overlay().DrawPolyFilled3D(target_pos[0], target_pos[1], my_z, 55, Utils.RGBToColor(0, 255, 0, 150), numsegments=16)
            Overlay().DrawPoly3D(target_pos[0], target_pos[1], my_z, 55, target_color, numsegments=16, thickness=4.0)

            # Draw resultant vector (thick white arrow from player to target)
            Overlay().DrawLine3D(my_pos[0], my_pos[1], my_z, target_pos[0], target_pos[1], my_z, vector_color, thickness=6.0)

            # Draw movement distance
            move_distance = Utils.Distance(my_pos, target_pos)
            mid_x = (my_pos[0] + target_pos[0]) / 2
            mid_y = (my_pos[1] + target_pos[1]) / 2
            Overlay().DrawText3D(mid_x, mid_y, my_z - 80, f"MOVE: {move_distance:.1f}", vector_color, autoZ=False, centered=True, scale=1.2)

            # Draw target coordinates
            Overlay().DrawText3D(target_pos[0], target_pos[1], my_z - 120, f"Target: ({target_pos[0]:.0f}, {target_pos[1]:.0f})", target_color, autoZ=False, centered=True, scale=0.9)

        Overlay().EndDraw()
   
    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if self.allowed_states is not None and current_state not in self.allowed_states:
            return None

        if GLOBAL_CACHE.Party.IsPartyLeader():
            return None

        if not self.throttle_timer.IsExpired():
            return None

        my_pos = GLOBAL_CACHE.Player.GetXY()

        # Use vector field computation to determine if movement is needed
        # If the vector field produces a significant vector, we need to move
        target_pos = self._calculate_finale_position(my_pos)

        # If we have a valid target position, we need to move
        if target_pos is not None:
            score = self.score_definition.get_score()
            return score

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        try:
            my_pos = GLOBAL_CACHE.Player.GetXY()
            target_pos = self._calculate_finale_position(my_pos)

            self.last_target_pos = target_pos

            if target_pos is not None:
                GLOBAL_CACHE.Player.Move(target_pos[0], target_pos[1])
                self.throttle_timer.Reset()
                yield from custom_behavior_helpers.Helpers.wait_for(1000)
                return BehaviorResult.ACTION_PERFORMED

            yield
            return BehaviorResult.ACTION_SKIPPED

        except Exception as e:
            print(f"SpreadDuringCombatUtility._execute error: {e}")
            yield
            return BehaviorResult.ACTION_SKIPPED

    def draw_overlay(self, current_state: BehaviorState) -> None:
        """
        Draw debug overlay showing spreading behavior visualization.
        This is the public method to be called from GUI.
        """
        # Only draw if enabled and in valid state (IN_AGGRO for spread utility)
        if not self.manager.enable_debug_overlay:
            return

        # Only show overlay when in combat (IN_AGGRO state)
        if current_state != BehaviorState.IN_AGGRO:
            return

        try:
            # Get current positions
            my_pos = GLOBAL_CACHE.Player.GetXY()
            party_positions = self._get_party_member_positions()
            enemy_positions = self._get_enemy_positions()
            leader_pos = self._get_party_leader_position()

            # Draw the overlay
            self._draw_debug_overlay_2(my_pos, party_positions, enemy_positions, leader_pos, self.last_target_pos)
        except Exception as e:
            # Silently fail on debug UI errors
            print(f"SpreadDuringCombatUtility.draw_overlay error: {e}")

    @override
    def customized_debug_ui(self, current_state: BehaviorState) -> None:
        """Comprehensive debug UI for vector field-based spread during combat"""
        self.draw_overlay(current_state)

        if PyImGui.collapsing_header("Vector Field Spread Configuration", PyImGui.TreeNodeFlags.DefaultOpen):

            # === ALLIES REPULSION CONFIGURATION ===
            PyImGui.text_colored("Allies Repulsion Forces:", (1.0, 0.6, 0.0, 1.0))  # Orange

            self.enable_allies_repulsion = PyImGui.checkbox("Enable Allies Repulsion", self.enable_allies_repulsion)
            PyImGui.same_line(0.0, -1.0)
            PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
            if PyImGui.is_item_hovered():
                PyImGui.set_tooltip("Push away from nearby party members and spirits")

            if self.enable_allies_repulsion:
                # Allies repulsion threshold
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, Utils.ColorToTuple(Utils.RGBToColor(255, 100, 0, 100)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, Utils.ColorToTuple(Utils.RGBToColor(255, 100, 0, 150)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, Utils.ColorToTuple(Utils.RGBToColor(255, 100, 0, 180)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrab, Utils.ColorToTuple(Utils.RGBToColor(255, 100, 0, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrabActive, Utils.ColorToTuple(Utils.RGBToColor(255, 100, 0, 255)))

                # Always read fresh value from shared memory to show updates from other instances
                current_threshold = self.manager.allies_repulsion_threshold
                new_threshold = PyImGui.slider_float(
                    "Allies Repulsion Threshold",
                    current_threshold,
                    50.0,
                    400.0
                )
                if new_threshold != current_threshold:
                    self.manager.allies_repulsion_threshold = new_threshold
                PyImGui.pop_style_color(5)
                PyImGui.same_line(0.0, -1.0)
                PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
                if PyImGui.is_item_hovered():
                    PyImGui.set_tooltip("Distance to start repelling from allies")

                # Allies repulsion weight
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, Utils.ColorToTuple(Utils.RGBToColor(255, 100, 0, 100)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, Utils.ColorToTuple(Utils.RGBToColor(255, 100, 0, 150)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, Utils.ColorToTuple(Utils.RGBToColor(255, 100, 0, 180)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrab, Utils.ColorToTuple(Utils.RGBToColor(255, 100, 0, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrabActive, Utils.ColorToTuple(Utils.RGBToColor(255, 100, 0, 255)))

                # Always read fresh value from shared memory to show updates from other instances
                current_weight = self.manager.allies_repulsion_weight
                new_weight = PyImGui.slider_float(
                    "Allies Repulsion Weight",
                    current_weight,
                    10.0,
                    300.0
                )
                if new_weight != current_weight:
                    self.manager.allies_repulsion_weight = new_weight
                PyImGui.pop_style_color(5)
                PyImGui.same_line(0.0, -1.0)
                PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
                if PyImGui.is_item_hovered():
                    PyImGui.set_tooltip("How strongly to push away from allies (higher = more distance)")

            PyImGui.separator()

            # === ENEMY REPULSION CONFIGURATION ===
            PyImGui.text_colored("Enemy Repulsion Forces:", (1.0, 0.0, 1.0, 1.0))  # Magenta

            self.enable_enemy_repulsion = PyImGui.checkbox("Enable Enemy Repulsion", self.enable_enemy_repulsion)
            PyImGui.same_line(0.0, -1.0)
            PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
            if PyImGui.is_item_hovered():
                PyImGui.set_tooltip("Push away from nearby enemies during combat")

            if self.enable_enemy_repulsion:
                # Enemy repulsion threshold
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, Utils.ColorToTuple(Utils.RGBToColor(255, 0, 255, 100)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, Utils.ColorToTuple(Utils.RGBToColor(255, 0, 255, 150)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, Utils.ColorToTuple(Utils.RGBToColor(255, 0, 255, 180)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrab, Utils.ColorToTuple(Utils.RGBToColor(255, 0, 255, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrabActive, Utils.ColorToTuple(Utils.RGBToColor(255, 0, 255, 255)))

                # Always read fresh value from shared memory to show updates from other instances
                current_threshold = self.manager.enemy_repulsion_threshold
                new_threshold = PyImGui.slider_float(
                    "Enemy Repulsion Threshold",
                    current_threshold,
                    50.0,
                    500.0
                )
                if new_threshold != current_threshold:
                    self.manager.enemy_repulsion_threshold = new_threshold
                PyImGui.pop_style_color(5)
                PyImGui.same_line(0.0, -1.0)
                PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
                if PyImGui.is_item_hovered():
                    PyImGui.set_tooltip("Distance to start repelling from enemies")

                # Enemy repulsion weight
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, Utils.ColorToTuple(Utils.RGBToColor(255, 0, 255, 100)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, Utils.ColorToTuple(Utils.RGBToColor(255, 0, 255, 150)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, Utils.ColorToTuple(Utils.RGBToColor(255, 0, 255, 180)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrab, Utils.ColorToTuple(Utils.RGBToColor(255, 0, 255, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrabActive, Utils.ColorToTuple(Utils.RGBToColor(255, 0, 255, 255)))

                # Always read fresh value from shared memory to show updates from other instances
                current_weight = self.manager.enemy_repulsion_weight
                new_weight = PyImGui.slider_float(
                    "Enemy Repulsion Weight",
                    current_weight,
                    10.0,
                    500.0
                )
                if new_weight != current_weight:
                    self.manager.enemy_repulsion_weight = new_weight
                PyImGui.pop_style_color(5)
                PyImGui.same_line(0.0, -1.0)
                PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
                if PyImGui.is_item_hovered():
                    PyImGui.set_tooltip("How strongly to push away from enemies (higher = more distance)")

            PyImGui.separator()

            # === LEADER ATTRACTION CONFIGURATION ===
            PyImGui.text_colored("Leader Attraction Forces:", (1.0, 0.84, 0.0, 1.0))  # Gold

            self.enable_leader_attraction = PyImGui.checkbox("Enable Leader Attraction", self.enable_leader_attraction)
            PyImGui.same_line(0.0, -1.0)
            PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
            if PyImGui.is_item_hovered():
                PyImGui.set_tooltip("Pull toward party leader when too far away")

            if self.enable_leader_attraction:
                # Leader attraction threshold
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, Utils.ColorToTuple(Utils.RGBToColor(255, 215, 0, 100)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, Utils.ColorToTuple(Utils.RGBToColor(255, 215, 0, 150)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, Utils.ColorToTuple(Utils.RGBToColor(255, 215, 0, 180)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrab, Utils.ColorToTuple(Utils.RGBToColor(255, 215, 0, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrabActive, Utils.ColorToTuple(Utils.RGBToColor(255, 215, 0, 255)))

                # Always read fresh value from shared memory to show updates from other instances
                current_threshold = self.manager.leader_attraction_threshold
                new_threshold = PyImGui.slider_float(
                    "Leader Attraction Threshold",
                    current_threshold,
                    50.0,
                    400.0
                )
                if new_threshold != current_threshold:
                    self.manager.leader_attraction_threshold = new_threshold
                PyImGui.pop_style_color(5)
                PyImGui.same_line(0.0, -1.0)
                PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
                if PyImGui.is_item_hovered():
                    PyImGui.set_tooltip("Distance from leader to start attraction (avoid clustering)")

                # Leader attraction weight
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, Utils.ColorToTuple(Utils.RGBToColor(255, 215, 0, 100)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, Utils.ColorToTuple(Utils.RGBToColor(255, 215, 0, 150)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, Utils.ColorToTuple(Utils.RGBToColor(255, 215, 0, 180)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrab, Utils.ColorToTuple(Utils.RGBToColor(255, 215, 0, 255)))
                PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrabActive, Utils.ColorToTuple(Utils.RGBToColor(255, 215, 0, 255)))

                # Always read fresh value from shared memory to show updates from other instances
                current_weight = self.manager.leader_attraction_weight
                new_weight = PyImGui.slider_float(
                    "Leader Attraction Weight",
                    current_weight,
                    10.0,
                    300.0
                )
                if new_weight != current_weight:
                    self.manager.leader_attraction_weight = new_weight
                PyImGui.pop_style_color(5)
                PyImGui.same_line(0.0, -1.0)
                PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
                if PyImGui.is_item_hovered():
                    PyImGui.set_tooltip("How strongly to pull toward leader (higher = stronger attraction)")

            PyImGui.separator()

            # === MOVEMENT PARAMETERS ===
            PyImGui.text_colored("Movement Parameters:", (1.0, 1.0, 1.0, 1.0))  # White

            # Min move threshold
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, Utils.ColorToTuple(Utils.RGBToColor(128, 128, 128, 100)))
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, Utils.ColorToTuple(Utils.RGBToColor(128, 128, 128, 150)))
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, Utils.ColorToTuple(Utils.RGBToColor(128, 128, 128, 180)))
            PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrab, Utils.ColorToTuple(Utils.RGBToColor(128, 128, 128, 255)))
            PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrabActive, Utils.ColorToTuple(Utils.RGBToColor(128, 128, 128, 255)))

            # Always read fresh value from shared memory to show updates from other instances
            current_threshold = self.manager.min_move_threshold
            new_threshold = PyImGui.slider_float(
                "Min Move Threshold",
                current_threshold,
                0.1,
                5.0
            )
            if new_threshold != current_threshold:
                self.manager.min_move_threshold = new_threshold
            PyImGui.pop_style_color(5)
            PyImGui.same_line(0.0, -1.0)
            PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
            if PyImGui.is_item_hovered():
                PyImGui.set_tooltip("Minimum vector magnitude to trigger movement (prevents jitter)")

            # Max move distance
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, Utils.ColorToTuple(Utils.RGBToColor(128, 128, 128, 100)))
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, Utils.ColorToTuple(Utils.RGBToColor(128, 128, 128, 150)))
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, Utils.ColorToTuple(Utils.RGBToColor(128, 128, 128, 180)))
            PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrab, Utils.ColorToTuple(Utils.RGBToColor(128, 128, 128, 255)))
            PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrabActive, Utils.ColorToTuple(Utils.RGBToColor(128, 128, 128, 255)))

            # Always read fresh value from shared memory to show updates from other instances
            current_distance = self.manager.max_move_distance
            new_distance = PyImGui.slider_float(
                "Max Move Distance",
                current_distance,
                50.0,
                500.0
            )
            if new_distance != current_distance:
                self.manager.max_move_distance = new_distance
            PyImGui.pop_style_color(5)
            PyImGui.same_line(0.0, -1.0)
            PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
            if PyImGui.is_item_hovered():
                PyImGui.set_tooltip("Maximum distance to move in one step (prevents overshooting)")

            PyImGui.separator()

            # === DEBUG VISUALIZATION ===
            PyImGui.text_colored("Debug Visualization:", (0.0, 1.0, 1.0, 1.0))  # Cyan

            # Main debug overlay toggle (from manager)
            if hasattr(self.manager, 'enable_debug_overlay'):
                self.manager.enable_debug_overlay = PyImGui.checkbox("Enable Debug Overlay", self.manager.enable_debug_overlay)
                PyImGui.same_line(0.0, -1.0)
                PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
                if PyImGui.is_item_hovered():
                    PyImGui.set_tooltip("Show visual debug overlay in game")

            # Debug overlay version selector
            if PyImGui.button("Use Advanced Debug Overlay"):
                # This could toggle between _draw_debug_overlay and _draw_debug_overlay_2
                pass
            PyImGui.same_line(0.0, -1.0)
            PyImGui.text_colored("(?)", (0.5, 0.5, 0.5, 1.0))
            if PyImGui.is_item_hovered():
                PyImGui.set_tooltip("Switch to advanced vector field visualization")

            PyImGui.separator()

            # === CURRENT STATUS ===
            PyImGui.text_colored("Current Status:", (1.0, 1.0, 0.0, 1.0))  # Yellow

            # Throttle timer
            PyImGui.bullet_text(f"Throttle Timer: {self.throttle_timer.GetTimeRemaining()}ms")

            # Vector field status
            if self.last_result_vector is not None:
                vx, vy, vmag = self.last_result_vector
                PyImGui.text_colored(f"  • Last Vector: ({vx:.2f}, {vy:.2f})", (0.0, 1.0, 0.0, 1.0))
                PyImGui.text_colored(f"  • Vector Magnitude: {vmag:.2f}", (0.0, 1.0, 0.0, 1.0))

                # Movement decision
                will_move = vmag >= self.manager.min_move_threshold
                move_color = (0.0, 1.0, 0.0, 1.0) if will_move else (1.0, 0.0, 0.0, 1.0)
                move_status = "YES" if will_move else "NO (below threshold)"
                PyImGui.text_colored(f"  • Will Move: {move_status}", move_color)

            # Force counts
            try:
                my_pos = GLOBAL_CACHE.Player.GetXY()
                if my_pos is not None:
                    # Count active forces
                    party_positions = self._get_party_member_positions() if self.enable_allies_repulsion else []
                    enemy_positions = self._get_enemy_positions() if self.enable_enemy_repulsion else []
                    leader_pos = self._get_party_leader_position() if self.enable_leader_attraction else None

                    # Allies count
                    active_allies = sum(1 for ally_pos in party_positions
                                      if Utils.Distance(my_pos, ally_pos) < self.manager.allies_repulsion_threshold)
                    PyImGui.text_colored(f"  • Active Ally Forces: {active_allies}/{len(party_positions)}", (1.0, 0.6, 0.0, 1.0))

                    # Enemies count
                    active_enemies = sum(1 for enemy_pos in enemy_positions
                                       if Utils.Distance(my_pos, enemy_pos) < self.manager.enemy_repulsion_threshold)
                    PyImGui.text_colored(f"  • Active Enemy Forces: {active_enemies}/{len(enemy_positions)}", (1.0, 0.0, 1.0, 1.0))

                    # Leader status
                    if leader_pos is not None:
                        leader_distance = Utils.Distance(my_pos, leader_pos)
                        leader_active = leader_distance > self.manager.leader_attraction_threshold
                        leader_color = (1.0, 0.84, 0.0, 1.0) if leader_active else (0.5, 0.5, 0.5, 1.0)
                        leader_status = "ACTIVE" if leader_active else "INACTIVE"
                        PyImGui.text_colored(f"  • Leader Force: {leader_status} (dist: {leader_distance:.1f})", leader_color)
                    else:
                        PyImGui.text_colored("  • Leader Force: NO LEADER", (1.0, 0.0, 0.0, 1.0))

            except Exception as e:
                PyImGui.text_colored(f"  • Status Error: {str(e)}", (1.0, 0.0, 0.0, 1.0))

            PyImGui.separator()

            # === FORCE CONFIGURATION SUMMARY ===
            PyImGui.text_colored("Force Configuration Summary:", (0.8, 0.8, 0.8, 1.0))

            # Calculate max radius for vector field
            max_radius = max(
                self.manager.allies_repulsion_threshold if self.enable_allies_repulsion else 0,
                self.manager.enemy_repulsion_threshold if self.enable_enemy_repulsion else 0,
                self.manager.leader_attraction_threshold if self.enable_leader_attraction else 0
            )
            PyImGui.text_colored(f"  • Vector Field Radius: {max_radius:.1f}", (0.8, 0.8, 0.8, 1.0))

            # Active forces summary
            active_forces = []
            if self.enable_allies_repulsion:
                active_forces.append(f"Allies(R:{self.manager.allies_repulsion_threshold:.0f},W:{self.manager.allies_repulsion_weight:.0f})")
            if self.enable_enemy_repulsion:
                active_forces.append(f"Enemies(R:{self.manager.enemy_repulsion_threshold:.0f},W:{self.manager.enemy_repulsion_weight:.0f})")
            if self.enable_leader_attraction:
                active_forces.append(f"Leader(R:{self.manager.leader_attraction_threshold:.0f},W:{self.manager.leader_attraction_weight:.0f})")

            if active_forces:
                PyImGui.text_colored(f"  • Active Forces: {len(active_forces)}", (0.0, 1.0, 0.0, 1.0))
                for force in active_forces:
                    PyImGui.text_colored(f"    - {force}", (0.7, 0.7, 0.7, 1.0))
            else:
                PyImGui.text_colored("  • Active Forces: NONE", (1.0, 0.0, 0.0, 1.0))
        pass
