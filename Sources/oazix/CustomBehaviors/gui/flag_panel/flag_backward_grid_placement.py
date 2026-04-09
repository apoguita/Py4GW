"""
Flag Backward Grid Placement - Preset 1 formation placement.

This module provides functionality for placing flags in a backward grid formation
relative to the leader's position and facing direction.
"""
import math
from Py4GWCoreLib import Player, Agent
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Sources.oazix.CustomBehaviors.primitives.parties.party_flagging_manager import PartyFlaggingManager


class FlagBackwardGridPlacement:
    """Handles backward grid formation placement (Preset 1)."""
    
    @staticmethod
    def apply_backward_grid_to_flag_manager() -> None:
        """
        Apply backward grid formation to flag manager.

        Formation pattern (relative to leader facing direction):
            Perfect 3x4 grid behind leader:
            1  2* 3   (closest row) - *Leader is at FLAG 2 (behind-center)
            4  5  6
            7  8  9
            10 11 12  (furthest row)

        Clears all flags and assigns all party members (including leader at FLAG 2),
        then updates positions.
        """
        flag_manager = PartyFlaggingManager()

        # Clear all flags first
        flag_manager.clear_all_flags()

        # Assign all party members to flags
        assigned = FlagBackwardGridPlacement._assign_all_party_members(flag_manager)
        # print(f"[FlagBackwardGridPlacement] Assigned {assigned} party members")

        # Get leader position and angle
        leader_x, leader_y = Player.GetXY()
        leader_agent_id = Player.GetAgentID()
        leader_angle = Agent.GetRotationAngle(leader_agent_id)

        # Update positions using backward grid formation
        FlagBackwardGridPlacement._update_backward_grid_positions(
            flag_manager, leader_x, leader_y, leader_angle
        )

    @staticmethod
    def _assign_all_party_members(flag_manager: PartyFlaggingManager) -> int:
        """
        Assign all party members to flags, with leader at FLAG 2 (index 1).

        Args:
            flag_manager: The flag manager instance

        Returns:
            Number of party members assigned
        """
        my_email = Player.GetAccountEmail()
        my_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(my_email)
        if my_account is None:
            return 0

        # Assign leader to FLAG 2 (index 1) - behind-center position
        flag_manager.set_flag_account_email(1, my_email)

        all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        flag_index = 0  # Start from FLAG 1 (index 0)
        for account in all_accounts:
            if account.AccountEmail == my_email:
                continue  # skip leader (already assigned to FLAG 2)
            is_in_map = (
                my_account.AgentData.Map.MapID == account.AgentData.Map.MapID and
                my_account.AgentData.Map.Region == account.AgentData.Map.Region and
                my_account.AgentData.Map.District == account.AgentData.Map.District
            )
            if not is_in_map:
                continue

            # Skip index 1 (FLAG 2) which has the leader
            if flag_index == 1:
                flag_index += 1

            if flag_index < 12:
                flag_manager.set_flag_account_email(flag_index, account.AccountEmail)
                flag_index += 1
            else:
                break

        # Return total number assigned (including leader)
        return flag_index if flag_index > 1 else 1

    @staticmethod
    def _update_backward_grid_positions(
        flag_manager: PartyFlaggingManager,
        leader_x: float,
        leader_y: float,
        leader_angle: float
    ) -> None:
        """
        Update flag positions in backward grid formation.
        
        Args:
            flag_manager: The flag manager instance
            leader_x: Leader's X position
            leader_y: Leader's Y position
            leader_angle: Leader's facing angle in radians
        """
        # Get spacing from configuration
        spacing = flag_manager.spacing_radius
        
        # Safety check: if spacing is 0, use default value
        if spacing == 0.0:
            spacing = 100.0
            flag_manager.spacing_radius = 100.0
        
        # Formation offsets relative to leader (forward, right)
        # Format: (forward_offset, right_offset) where forward is leader's facing direction
        # Positive forward = in front of leader, negative = behind
        # Positive right = to leader's right, negative = to leader's left
        formation_offsets = [
            (-spacing, -spacing),      # Flag 1: behind-left
            (-spacing, 0),             # Flag 2: behind-center
            (-spacing, spacing),       # Flag 3: behind-right
            (-spacing * 2, -spacing),  # Flag 4: further behind-left
            (-spacing * 2, 0),         # Flag 5: further behind-center
            (-spacing * 2, spacing),   # Flag 6: further behind-right
            (-spacing * 3, -spacing),  # Flag 7: even further behind-left
            (-spacing * 3, 0),         # Flag 8: even further behind-center
            (-spacing * 3, spacing),   # Flag 9: even further behind-right
            (-spacing * 4, -spacing),  # Flag 10: furthest behind-left
            (-spacing * 4, 0),         # Flag 11: furthest behind-center
            (-spacing * 4, spacing),   # Flag 12: furthest behind-right
        ]
        
        # Calculate rotation
        cos_angle = math.cos(leader_angle)
        sin_angle = math.sin(leader_angle)
        
        # Update positions for all assigned flags
        updated_count = 0
        for i in range(12):
            email = flag_manager.get_flag_account_email(i)
            if email:  # Only update if flag is assigned
                # Get formation offset
                forward_offset, right_offset = formation_offsets[i]

                # Transform from local (forward/right) to world coordinates
                # Forward direction: (cos_angle, sin_angle)
                # Right direction: (-sin_angle, cos_angle) [perpendicular to forward, 90° counter-clockwise]
                world_x = leader_x + (forward_offset * cos_angle - right_offset * sin_angle)
                world_y = leader_y + (forward_offset * sin_angle + right_offset * cos_angle)

                # Update position
                # print(f"[FlagBackwardGridPlacement] Flag {i}: email={email}, forward={forward_offset:.1f}, right={right_offset:.1f}, pos=({world_x:.1f}, {world_y:.1f})")
                flag_manager.set_flag_position(i, world_x, world_y)
                updated_count += 1
