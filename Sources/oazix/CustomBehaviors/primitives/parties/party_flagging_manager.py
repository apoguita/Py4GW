"""
Singleton manager for party flagging configuration.
Stores all parameters in shared RAM memory for cross-process access.
Manages flag positions for up to 12 party members.
"""

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib import Player
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager

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
        # This method is deprecated - flag positions should be set explicitly via UI
        # Keeping it as a no-op for backward compatibility
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
                my_account.AgentData.Map.MapID == account.AgentData.Map.MapID and
                my_account.AgentData.Map.Region == account.AgentData.Map.Region and
                my_account.AgentData.Map.District == account.AgentData.Map.District
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