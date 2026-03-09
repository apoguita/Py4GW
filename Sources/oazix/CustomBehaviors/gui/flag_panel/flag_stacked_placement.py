"""
Flag Stacked Placement - Preset 2 formation placement.

This module provides functionality for placing all flags stacked at the leader's position.
"""
from Py4GWCoreLib import Player
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Sources.oazix.CustomBehaviors.primitives.parties.party_flagging_manager import PartyFlaggingManager


class FlagStackedPlacement:
    """Handles stacked formation placement (Preset 2)."""

    @staticmethod
    def apply_stacked_to_flag_manager() -> None:
        """
        Apply stacked formation to flag manager.

        All flags are placed at the leader's current position.
        Clears all flags and assigns all party members.
        """
        flag_manager = PartyFlaggingManager()

        # Clear all flags first
        flag_manager.clear_all_flags()

        # Assign all party members to flags
        assigned = FlagStackedPlacement._assign_all_party_members(flag_manager)
        # print(f"[FlagStackedPlacement] Assigned {assigned} party members")

        # Get leader position
        leader_x, leader_y = Player.GetXY()

        # Update all assigned flags to leader's position
        for i in range(12):
            email = flag_manager.get_flag_account_email(i)
            if email:  # Only update if flag is assigned
                flag_manager.set_flag_position(i, leader_x, leader_y)
                # print(f"[FlagStackedPlacement] Flag {i}: email={email}, pos=({leader_x:.1f}, {leader_y:.1f})")

    @staticmethod
    def _assign_all_party_members(flag_manager: PartyFlaggingManager) -> int:
        """
        Assign all party members (excluding leader) to flags.

        Args:
            flag_manager: The flag manager instance

        Returns:
            Number of party members assigned
        """
        my_email = Player.GetAccountEmail()
        my_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(my_email)
        if my_account is None:
            return 0

        all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        assigned = 0
        for account in all_accounts:
            if account.AccountEmail == my_email:
                continue  # skip leader
            is_in_map = (
                my_account.AgentData.Map.MapID == account.AgentData.Map.MapID and
                my_account.AgentData.Map.Region == account.AgentData.Map.Region and
                my_account.AgentData.Map.District == account.AgentData.Map.District
            )
            if not is_in_map:
                continue
            if assigned < 12:
                flag_manager.set_flag_account_email(assigned, account.AccountEmail)
                assigned += 1
            else:
                break

        return assigned
