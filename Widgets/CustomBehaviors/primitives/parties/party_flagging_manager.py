"""
Singleton manager for party flagging configuration.
Stores all parameters in shared RAM memory for cross-process access.
Manages flag positions for up to 12 party members.
"""

import math
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib import Map, Agent, Player
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager

class PartyFlaggingManager:
    """
    Singleton class to manage party flagging configuration.
    All party members can access and modify these shared settings via RAM.
    Direct property access - always reads/writes from shared memory (no caching).

    Flag data structure:
    - flags[0-11]: Array of 12 flag positions
    - Each flag contains: account_email (or "" for unassigned), position_x, position_y
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PartyFlaggingManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Only initialize once
        if self._initialized:
            return

        self._initialized = True
        self._memory_manager = CustomBehaviorWidgetMemoryManager()

        # Do not auto-initialize flag positions on startup; require explicit UI action
        # self._initialize_default_positions()

    @staticmethod
    def _set_c_wchar_array(arr, value: str):
        """Helper to set a c_wchar array from a Python string"""
        # Clear the array first
        for i in range(len(arr)):
            arr[i] = '\0'
        # Copy the string characters
        for i, ch in enumerate(value):
            if i >= len(arr) - 1:  # Leave room for null terminator
                break
            arr[i] = ch

    @staticmethod
    def _get_c_wchar_array_as_str(arr) -> str:
        """Helper to convert a c_wchar array to a Python string"""
        # Convert to string, stopping at null terminator
        result = []
        for ch in arr:
            if ch == '\0':
                break
            result.append(ch)
        return ''.join(result)

    def _initialize_default_positions(self):
        """Initialize default flag positions on startup if not already set"""

        # Check if we're in game and can get player position
        try:
            # Only initialize if we're the party leader and in an explorable area
            if not Map.IsExplorable():
                return

            if not GLOBAL_CACHE.Party.IsPartyLeader():
                return

            # Check if flags are already assigned (any flag has an email)
            config = self._memory_manager.GetFlaggingConfig()
            has_assignments = False
            for i in range(12):
                email = self._get_c_wchar_array_as_str(config.FlagAccountEmails[i])
                if email:
                    has_assignments = True
                    break

            # If already has assignments, don't override
            if has_assignments:
                return

            # Get leader position and angle
            leader_x, leader_y = Player.GetXY()
            leader_agent_id = Player.GetAgentID()
            leader_angle = Agent.GetRotationAngle(leader_agent_id)

            # Get all party members (excluding leader)
            account_email = Player.GetAccountEmail()
            all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()

            # Filter to same map and party, excluding leader
            party_members = []
            my_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
            if my_account is not None:
                for account in all_accounts:
                    if account.AccountEmail == account_email:
                        continue  # Skip leader
                    # Check if in same map
                    is_in_map = (my_account.MapID == account.MapID and
                               my_account.MapRegion == account.MapRegion and
                               my_account.MapDistrict == account.MapDistrict)
                    if is_in_map:
                        party_members.append(account.AccountEmail)

            # If no party members, nothing to initialize
            if not party_members:
                return

            # Assign flags (flag 1 to first member, flag 2 to second, etc.)
            flag_assignments = {}
            for i, email in enumerate(party_members):
                if i >= 12:  # Max 12 flags
                    break
                flag_assignments[i + 1] = email  # Flag numbers are 1-based

            # Apply formation at current position
            self.assign_formation_preset_1(leader_x, leader_y, leader_angle, flag_assignments)

        except Exception as e:
            # Silently fail if we can't initialize (e.g., not in game yet)
            pass

    # --- Flag Position Access (0-11) ---
    def get_flag_account_email(self, flag_index: int) -> str:
        """Get the account email assigned to a flag position ("" = unassigned)"""
        if flag_index < 0 or flag_index >= 12:
            raise ValueError(f"Flag index must be 0-11, got {flag_index}")
        config = self._memory_manager.GetFlaggingConfig()
        return self._get_c_wchar_array_as_str(config.FlagAccountEmails[flag_index])

    def set_flag_account_email(self, flag_index: int, account_email: str):
        """Set the account email for a flag position ("" = unassigned)"""
        if flag_index < 0 or flag_index >= 12:
            raise ValueError(f"Flag index must be 0-11, got {flag_index}")
        config = self._memory_manager.GetFlaggingConfig()
        self._set_c_wchar_array(config.FlagAccountEmails[flag_index], account_email)
        self._memory_manager.SetFlaggingConfig(config)

    def get_flag_position(self, flag_index: int) -> tuple[float, float]:
        """Get the X, Y position for a flag"""
        if flag_index < 0 or flag_index >= 12:
            raise ValueError(f"Flag index must be 0-11, got {flag_index}")
        config = self._memory_manager.GetFlaggingConfig()
        return (config.FlagPositionsX[flag_index], config.FlagPositionsY[flag_index])

    def set_flag_position(self, flag_index: int, x: float, y: float):
        """Set the X, Y position for a flag"""
        if flag_index < 0 or flag_index >= 12:
            raise ValueError(f"Flag index must be 0-11, got {flag_index}")
        config = self._memory_manager.GetFlaggingConfig()
        config.FlagPositionsX[flag_index] = x
        config.FlagPositionsY[flag_index] = y
        self._memory_manager.SetFlaggingConfig(config)

    def get_flag_data(self, flag_index: int) -> tuple[str, float, float]:
        """Get complete flag data: (account_email, x, y)"""
        if flag_index < 0 or flag_index >= 12:
            raise ValueError(f"Flag index must be 0-11, got {flag_index}")
        config = self._memory_manager.GetFlaggingConfig()
        return (
            self._get_c_wchar_array_as_str(config.FlagAccountEmails[flag_index]),
            config.FlagPositionsX[flag_index],
            config.FlagPositionsY[flag_index]
        )

    def set_flag_data(self, flag_index: int, account_email: str, x: float, y: float):
        """Set complete flag data: account_email, x, y"""
        if flag_index < 0 or flag_index >= 12:
            raise ValueError(f"Flag index must be 0-11, got {flag_index}")
        config = self._memory_manager.GetFlaggingConfig()
        self._set_c_wchar_array(config.FlagAccountEmails[flag_index], account_email)
        config.FlagPositionsX[flag_index] = x
        config.FlagPositionsY[flag_index] = y
        self._memory_manager.SetFlaggingConfig(config)

    # --- Configuration Parameters ---
    @property
    def spacing_radius(self) -> float:
        """Radius for spacing between flag positions"""
        return self._memory_manager.GetFlaggingConfig().SpacingRadius

    @spacing_radius.setter
    def spacing_radius(self, value: float):
        config = self._memory_manager.GetFlaggingConfig()
        config.SpacingRadius = value
        self._memory_manager.SetFlaggingConfig(config)

    @property
    def movement_threshold(self) -> float:
        """How much players can move from their assigned flag before repositioning"""
        return self._memory_manager.GetFlaggingConfig().MovementThreshold

    @movement_threshold.setter
    def movement_threshold(self, value: float):
        config = self._memory_manager.GetFlaggingConfig()
        config.MovementThreshold = value
        self._memory_manager.SetFlaggingConfig(config)

    @property
    def enable_debug_overlay(self) -> bool:
        """Enable debug overlay visualization"""
        return self._memory_manager.GetFlaggingConfig().EnableDebugOverlay

    @enable_debug_overlay.setter
    def enable_debug_overlay(self, value: bool):
        config = self._memory_manager.GetFlaggingConfig()
        config.EnableDebugOverlay = value
        self._memory_manager.SetFlaggingConfig(config)

    # --- Utility Methods ---
    def get_my_flag_index(self, my_account_email: str) -> int | None:
        """Find which flag index is assigned to my account email (returns None if not assigned)"""
        config = self._memory_manager.GetFlaggingConfig()
        for i in range(12):
            email = self._get_c_wchar_array_as_str(config.FlagAccountEmails[i])
            if email == my_account_email:
                return i
        return None

    def are_flags_defined(self) -> bool:
        """Check if any flags are defined (has both email assignment AND valid position)"""
        config = self._memory_manager.GetFlaggingConfig()
        for i in range(12):
            email = self._get_c_wchar_array_as_str(config.FlagAccountEmails[i])
            if email:
                x = config.FlagPositionsX[i]
                y = config.FlagPositionsY[i]
                if x != 0.0 or y != 0.0:
                    return True
        return False


    def auto_assign_emails_if_none_assigned(self) -> bool:
        """
        Auto-assign party members' emails to grid flags (1..12) if none are assigned yet.
        Returns True if an assignment was performed, False otherwise.
        """
        config = self._memory_manager.GetFlaggingConfig()
        # If any email is already assigned, do nothing
        for i in range(12):
            if self._get_c_wchar_array_as_str(config.FlagAccountEmails[i]):
                return False

        # Determine leader and party members in same map
        my_email = Player.GetAccountEmail()
        my_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(my_email)
        if my_account is None:
            return False

        all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        assigned = 0
        for account in all_accounts:
            if account.AccountEmail == my_email:
                continue  # skip leader
            is_in_map = (
                my_account.MapID == account.MapID and
                my_account.MapRegion == account.MapRegion and
                my_account.MapDistrict == account.MapDistrict
            )
            if not is_in_map:
                continue
            if assigned < 12:
                self._set_c_wchar_array(config.FlagAccountEmails[assigned], account.AccountEmail)
                assigned += 1
            else:
                break

        self._memory_manager.SetFlaggingConfig(config)
        return assigned > 0


    def is_flag_defined(self, my_account_email: str) -> bool:
        """
        Check if a flag is defined for this account (has both email assignment AND valid position).
        Returns True only if the flag is assigned AND has a non-zero position.
        """
        config = self._memory_manager.GetFlaggingConfig()
        for i in range(12):
            email = self._get_c_wchar_array_as_str(config.FlagAccountEmails[i])
            if email == my_account_email:
                # Found assignment - check if position is valid (not 0, 0)
                x = config.FlagPositionsX[i]
                y = config.FlagPositionsY[i]
                return x != 0.0 or y != 0.0
        return False

    def clear_flag(self, flag_index: int):
        """Clear a flag assignment"""
        if flag_index < 0 or flag_index >= 12:
            raise ValueError(f"Flag index must be 0-11, got {flag_index}")
        config = self._memory_manager.GetFlaggingConfig()
        self._set_c_wchar_array(config.FlagAccountEmails[flag_index], "")
        config.FlagPositionsX[flag_index] = 0.0
        config.FlagPositionsY[flag_index] = 0.0
        self._memory_manager.SetFlaggingConfig(config)

    def clear_all_flags(self):
        """Clear all flag assignments (both emails and positions)"""
        config = self._memory_manager.GetFlaggingConfig()
        for i in range(12):
            self._set_c_wchar_array(config.FlagAccountEmails[i], "")
            config.FlagPositionsX[i] = 0.0
            config.FlagPositionsY[i] = 0.0
        self._memory_manager.SetFlaggingConfig(config)

    def clear_all_flag_positions(self):
        """Clear all flag positions but keep email assignments (removes flags from map)"""
        config = self._memory_manager.GetFlaggingConfig()
        for i in range(12):
            config.FlagPositionsX[i] = 0.0
            config.FlagPositionsY[i] = 0.0
        self._memory_manager.SetFlaggingConfig(config)

    # --- Formation Assignment Methods ---
    def assign_formation_preset_1(self, leader_x: float, leader_y: float, leader_angle: float, flag_assignments: dict[int, str]) -> None:
        """
        Assign flags in preset formation 1 based on leader position and angle.

        Formation pattern (relative to leader facing direction):
            Perfect 3x4 grid behind leader:
            1  2  3   (closest row)
            4  5  6
            7  8  9
            10 11 12  (furthest row)

        Args:
            leader_x: Leader's X position
            leader_y: Leader's Y position
            leader_angle: Leader's facing angle in radians
            flag_assignments: Dict mapping flag number (1-12) to account email
                             Example: {1: "player1@email.com", 2: "player2@email.com", ...}
        """
        # Get spacing from configuration
        spacing = self.spacing_radius

        # Safety check: if spacing is 0, use default value
        if spacing == 0.0:
            spacing = 100.0
            # Also update the config to fix it permanently
            self.spacing_radius = 100.0

        # Formation offsets relative to leader (in leader's local coordinate system)
        # Format: (forward_offset, right_offset) where forward is leader's facing direction
        # Positive forward = in front of leader, negative = behind
        # Positive right = to leader's right, negative = to leader's left
        # Index corresponds to flag number - 1 (flag 1 = index 0, flag 2 = index 1, etc.)
        formation_offsets = [
            # Flag 1: Row 2, left position
            (-spacing, -spacing),      # behind-left
            # Flag 2: Row 2, center position
            (-spacing, 0),             # behind-center
            # Flag 3: Row 2, right position
            (-spacing, spacing),       # behind-right
            # Flag 4: Row 3, left position
            (-spacing * 2, -spacing),  # further behind-left
            # Flag 5: Row 3, center position
            (-spacing * 2, 0),         # further behind-center
            # Flag 6: Row 3, right position
            (-spacing * 2, spacing),   # further behind-right
            # Flag 7: Row 4, left position
            (-spacing * 3, -spacing),  # even further behind-left
            # Flag 8: Row 4, center position
            (-spacing * 3, 0),         # even further behind-center
            # Flag 9: Row 4, right position
            (-spacing * 3, spacing),   # even further behind-right
            # Flag 10: Row 4, left position
            (-spacing * 4, -spacing),  # furthest behind-left
            # Flag 11: Row 4, center position
            (-spacing * 4, 0),         # furthest behind-center
            # Flag 12: Row 4, right position
            (-spacing * 4, spacing),   # furthest behind-right
        ]

        # Convert leader angle to direction vector
        # In Guild Wars, angle 0 typically points right, increases counter-clockwise
        cos_angle = math.cos(leader_angle)
        sin_angle = math.sin(leader_angle)

        # Assign flags
        config = self._memory_manager.GetFlaggingConfig()

        # Clear all flags first
        for i in range(12):
            self._set_c_wchar_array(config.FlagAccountEmails[i], "")
            config.FlagPositionsX[i] = 0.0
            config.FlagPositionsY[i] = 0.0

        # Assign specified flags
        for flag_number, email in flag_assignments.items():
            if flag_number < 1 or flag_number > 12:
                raise ValueError(f"Flag number must be 1-12, got {flag_number}")

            flag_index = flag_number - 1  # Convert to 0-based index

            # Get formation offset
            forward_offset, right_offset = formation_offsets[flag_index]

            # Transform from local (forward/right) to world coordinates
            # Forward direction: (cos_angle, sin_angle)
            # Right direction: (sin_angle, -cos_angle) [perpendicular to forward, 90° clockwise]
            # Formula: world_pos = leader_pos + forward_offset * forward_vec + right_offset * right_vec
            world_x = leader_x + (forward_offset * cos_angle + right_offset * sin_angle)
            world_y = leader_y + (forward_offset * sin_angle - right_offset * cos_angle)

            # Assign to flag index
            self._set_c_wchar_array(config.FlagAccountEmails[flag_index], email)
            config.FlagPositionsX[flag_index] = world_x
            config.FlagPositionsY[flag_index] = world_y

        self._memory_manager.SetFlaggingConfig(config)

    def update_formation_positions(self, leader_x: float, leader_y: float, leader_angle: float, formation_type: str = "preset_1") -> None:
        """
        Update flag positions while keeping current email assignments.
        Useful for moving the formation without reassigning players.

        Args:
            leader_x: Leader's X position
            leader_y: Leader's Y position
            leader_angle: Leader's facing angle in radians
            formation_type: Type of formation ("preset_1" or custom offsets can be added)
        """
        if formation_type == "preset_2":
            config = self._memory_manager.GetFlaggingConfig()
            for i in range(12):
                email = self._get_c_wchar_array_as_str(config.FlagAccountEmails[i])
                if email:
                    config.FlagPositionsX[i] = leader_x
                    config.FlagPositionsY[i] = leader_y
            self._memory_manager.SetFlaggingConfig(config)
            return
        elif formation_type != "preset_1":
            raise ValueError(f"Unknown formation type: {formation_type}")

        # Get spacing from configuration
        spacing = self.spacing_radius

        # Safety check: if spacing is 0, use default value
        if spacing == 0.0:
            spacing = 100.0
            # Also update the config to fix it permanently
            self.spacing_radius = 100.0

        # Formation offsets relative to leader (forward, right)
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

        config = self._memory_manager.GetFlaggingConfig()

        # Update positions for all assigned flags (without clearing emails)
        for i in range(12):
            email = self._get_c_wchar_array_as_str(config.FlagAccountEmails[i])
            if email:  # Only update if flag is assigned
                # Get formation offset
                forward_offset, right_offset = formation_offsets[i]

                # Transform from local (forward/right) to world coordinates
                world_x = leader_x + (forward_offset * cos_angle + right_offset * sin_angle)
                world_y = leader_y + (forward_offset * sin_angle - right_offset * cos_angle)

                # Update position only
                config.FlagPositionsX[i] = world_x
                config.FlagPositionsY[i] = world_y

        self._memory_manager.SetFlaggingConfig(config)

    def assign_formation_for_current_party(self, formation_type: str = "preset_1") -> tuple[bool, str]:
        """
        Assign formation flags for all party members based on current leader position.
        This is a convenience method for UI usage.

        Args:
            formation_type: Type of formation to use (default: "preset_1")

        Returns:
            tuple[bool, str]: (success, message)
                - success: True if assignment succeeded, False otherwise
                - message: Error message if failed, empty string if succeeded
        """
        # Check if current player is party leader
        if not GLOBAL_CACHE.Party.IsPartyLeader():
            return False, "You must be party leader to set flags"

        # Get leader position and angle
        leader_x, leader_y = Player.GetXY()
        leader_agent_id = Player.GetAgentID()
        leader_angle = Agent.GetRotationAngle(leader_agent_id)

        # Get all party members (excluding leader)
        account_email = Player.GetAccountEmail()
        all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()

        # Filter to same map and party, excluding leader
        party_members = []
        for account in all_accounts:
            if account.AccountEmail == account_email:
                continue  # Skip leader
            # Check if in same map
            my_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
            if my_account is not None:
                is_in_map = (my_account.MapID == account.MapID and
                           my_account.MapRegion == account.MapRegion and
                           my_account.MapDistrict == account.MapDistrict)
                if is_in_map:
                    party_members.append(account.AccountEmail)

        # Assign flags (flag 1 to first member, flag 2 to second, etc.)
        flag_assignments = {}
        for i, email in enumerate(party_members):
            if i >= 12:  # Max 12 flags
                break
            flag_assignments[i + 1] = email  # Flag numbers are 1-based

        # Apply formation
        if formation_type == "preset_1":
            self.assign_formation_preset_1(leader_x, leader_y, leader_angle, flag_assignments)
        else:
            return False, f"Unknown formation type: {formation_type}"

        return True, ""