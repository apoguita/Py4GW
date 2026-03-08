"""
Singleton manager for party following configuration.
Stores all parameters in shared RAM memory for cross-process access.
"""

from Py4GWCoreLib import Agent
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Sources.oazix.CustomBehaviors.primitives.following_behavior_priority import FollowingBehaviorPriority
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager

class PartyFollowingManager:
    """
    Singleton class to manage party following configuration.
    All party members can access and modify these shared settings via RAM.
    Direct property access - always reads/writes from shared memory (no caching).
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PartyFollowingManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Only initialize once

        if self._initialized:
            return

        self._initialized = True
        self._memory_manager = CustomBehaviorWidgetMemoryManager()

    @property
    def follow_distance(self) -> float:
        return self._memory_manager.GetFollowingConfig().FollowDistance

    @follow_distance.setter
    def follow_distance(self, value: float):
        config = self._memory_manager.GetFollowingConfig()
        config.FollowDistance = value
        self._memory_manager.SetFollowingConfig(config)

    # Enemy repulsion configuration
    @property
    def enemy_repulsion_threshold(self) -> float:
        return self._memory_manager.GetFollowingConfig().EnemyRepulsionThreshold

    @enemy_repulsion_threshold.setter
    def enemy_repulsion_threshold(self, value: float):
        config = self._memory_manager.GetFollowingConfig()
        config.EnemyRepulsionThreshold = value
        self._memory_manager.SetFollowingConfig(config)

    @property
    def enemy_repulsion_weight(self) -> float:
        return self._memory_manager.GetFollowingConfig().EnemyRepulsionWeight

    @enemy_repulsion_weight.setter
    def enemy_repulsion_weight(self, value: float):
        config = self._memory_manager.GetFollowingConfig()
        config.EnemyRepulsionWeight = value
        self._memory_manager.SetFollowingConfig(config)

    # Leader attraction configuration
    @property
    def leader_attraction_threshold(self) -> float:
        return self._memory_manager.GetFollowingConfig().LeaderAttractionThreshold

    @leader_attraction_threshold.setter
    def leader_attraction_threshold(self, value: float):
        config = self._memory_manager.GetFollowingConfig()
        config.LeaderAttractionThreshold = value
        self._memory_manager.SetFollowingConfig(config)

    @property
    def leader_attraction_weight(self) -> float:
        return self._memory_manager.GetFollowingConfig().LeaderAttractionWeight

    @leader_attraction_weight.setter
    def leader_attraction_weight(self, value: float):
        config = self._memory_manager.GetFollowingConfig()
        config.LeaderAttractionWeight = value
        self._memory_manager.SetFollowingConfig(config)

    # Allies repulsion configuration
    @property
    def allies_repulsion_threshold(self) -> float:
        return self._memory_manager.GetFollowingConfig().AlliesRepulsionThreshold

    @allies_repulsion_threshold.setter
    def allies_repulsion_threshold(self, value: float):
        config = self._memory_manager.GetFollowingConfig()
        config.AlliesRepulsionThreshold = value
        self._memory_manager.SetFollowingConfig(config)

    @property
    def allies_repulsion_weight(self) -> float:
        return self._memory_manager.GetFollowingConfig().AlliesRepulsionWeight

    @allies_repulsion_weight.setter
    def allies_repulsion_weight(self, value: float):
        config = self._memory_manager.GetFollowingConfig()
        config.AlliesRepulsionWeight = value
        self._memory_manager.SetFollowingConfig(config)

    @property
    def enable_debug_overlay(self) -> bool:
        return self._memory_manager.GetFollowingConfig().EnableDebugOverlay

    @enable_debug_overlay.setter
    def enable_debug_overlay(self, value: bool):
        config = self._memory_manager.GetFollowingConfig()
        config.EnableDebugOverlay = value
        self._memory_manager.SetFollowingConfig(config)

    # Movement parameters configuration
    @property
    def min_move_threshold(self) -> float:
        return self._memory_manager.GetFollowingConfig().MinMoveThreshold

    @min_move_threshold.setter
    def min_move_threshold(self, value: float):
        config = self._memory_manager.GetFollowingConfig()
        config.MinMoveThreshold = value
        self._memory_manager.SetFollowingConfig(config)

    @property
    def max_move_distance(self) -> float:
        return self._memory_manager.GetFollowingConfig().MaxMoveDistance

    @max_move_distance.setter
    def max_move_distance(self, value: float):
        config = self._memory_manager.GetFollowingConfig()
        config.MaxMoveDistance = value
        self._memory_manager.SetFollowingConfig(config)

    # Party following behavior mode
    @property
    def party_following_behavior(self) -> FollowingBehaviorPriority | None:
        """Get the party following behavior mode from shared memory"""
        value = self._memory_manager.GetFollowingConfig().PartyFollowingBehavior
        if value == 0:
            return None
        try:
            return FollowingBehaviorPriority(value)
        except ValueError:
            return None

    @party_following_behavior.setter
    def party_following_behavior(self, value: FollowingBehaviorPriority | None):
        """Set the party following behavior mode in shared memory"""
        config = self._memory_manager.GetFollowingConfig()
        config.PartyFollowingBehavior = value.value if value is not None else 0
        self._memory_manager.SetFollowingConfig(config)

    def set_party_following_behavior_state(self, state: FollowingBehaviorPriority):

        # Set the behavior state enum
        self.party_following_behavior = state

        # # Apply preset configuration to all registered accounts
        # config = self._memory_manager.GetFollowingConfig()
        # GLOBAL_CACHE.ShMem.GetAllAccountData()

        # for idx in range(12):  # MAX_FLAG_POSITIONS
        #     email = self._get_c_wchar_array_as_str(config.AccountEmails[idx])

        #     # Skip empty slots
        #     if not email or email.strip() == "":
        #         continue

        #     # Apply preset based on behavior state
        #     if state == FollowingBehaviorPriority.PRIORITIZE_ATTRACT_TO_LEADER:
        #         # Preset: Only leader attraction active (like flagging mode)
        #         config.IsRepulsionAlliesActive[idx] = False
        #         config.IsAttractionLeaderActive[idx] = True
        #         config.IsRepulsionEnemiesActive[idx] = False

        #     elif state == FollowingBehaviorPriority.PRIORITIZE_REPULSE_FROM_ALLIES:
        #         # Preset: Allies repulsion + light leader attraction
        #         config.IsRepulsionAlliesActive[idx] = True
        #         config.IsAttractionLeaderActive[idx] = True
        #         config.IsRepulsionEnemiesActive[idx] = False

        #     elif state == FollowingBehaviorPriority.PRIORITIZE_VECTOR_FIELD or state == FollowingBehaviorPriority.LOW_PRIORITY_VECTOR_FIELD:
        #         # All forces enabled - keep current settings (don't change)
        #         pass

        #     elif state == FollowingBehaviorPriority.NONE:
        #         # No following behavior - disable all forces
        #         config.IsRepulsionAlliesActive[idx] = False
        #         config.IsAttractionLeaderActive[idx] = False
        #         config.IsRepulsionEnemiesActive[idx] = False

        # Save the updated configuration
        # self._memory_manager.SetFollowingConfig(config)

    # Per-account force activation methods
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

    def _get_account_index(self, account_email: str) -> int | None:
        """Find the index of an account email in the shared memory array"""
        config = self._memory_manager.GetFollowingConfig()
        for i in range(12):  # MAX_FLAG_POSITIONS
            stored_email = self._get_c_wchar_array_as_str(config.AccountEmails[i])
            if stored_email == account_email:
                return i
        return None

    def _get_or_create_account_index(self, account_email: str) -> int | None:
        """Get existing account index or create a new one"""
        # First try to find existing
        idx = self._get_account_index(account_email)
        if idx is not None:
            return idx

        # Find empty slot
        config = self._memory_manager.GetFollowingConfig()
        for i in range(12):  # MAX_FLAG_POSITIONS
            stored_email = self._get_c_wchar_array_as_str(config.AccountEmails[i])
            if stored_email == "" or stored_email[0] == '\0' if stored_email else True:
                # Found empty slot, assign it
                self._set_c_wchar_array(config.AccountEmails[i], account_email)
                self._memory_manager.SetFollowingConfig(config)
                return i

        return None  # No empty slots

    def get_is_repulsion_allies_active(self, account_email: str) -> bool:
        """Get whether allies repulsion is active for a specific account"""
        idx = self._get_account_index(account_email)
        if idx is None:
            return False  # Default if account not found
        config = self._memory_manager.GetFollowingConfig()
        return config.IsRepulsionAlliesActive[idx]

    def set_is_repulsion_allies_active(self, account_email: str, value: bool):
        """Set whether allies repulsion is active for a specific account"""
        idx = self._get_or_create_account_index(account_email)
        if idx is None:
            return  # Could not create slot
        config = self._memory_manager.GetFollowingConfig()
        config.IsRepulsionAlliesActive[idx] = value
        self._memory_manager.SetFollowingConfig(config)

    def get_is_attraction_leader_active(self, account_email: str) -> bool:
        """Get whether leader attraction is active for a specific account"""
        idx = self._get_account_index(account_email)
        if idx is None:
            return True  # Default if account not found
        config = self._memory_manager.GetFollowingConfig()
        return config.IsAttractionLeaderActive[idx]

    def set_is_attraction_leader_active(self, account_email: str, value: bool):
        """Set whether leader attraction is active for a specific account"""
        idx = self._get_or_create_account_index(account_email)
        if idx is None:
            return  # Could not create slot
        config = self._memory_manager.GetFollowingConfig()
        config.IsAttractionLeaderActive[idx] = value
        self._memory_manager.SetFollowingConfig(config)

    def get_is_repulsion_enemies_active(self, account_email: str) -> bool:
        """Get whether enemies repulsion is active for a specific account"""
        idx = self._get_account_index(account_email)
        if idx is None:
            return False  # Default if account not found
        config = self._memory_manager.GetFollowingConfig()
        return config.IsRepulsionEnemiesActive[idx]

    def set_is_repulsion_enemies_active(self, account_email: str, value: bool):
        """Set whether enemies repulsion is active for a specific account"""
        idx = self._get_or_create_account_index(account_email)
        if idx is None:
            return  # Could not create slot
        config = self._memory_manager.GetFollowingConfig()
        config.IsRepulsionEnemiesActive[idx] = value
        self._memory_manager.SetFollowingConfig(config)

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

    def get_account_email(self, index: int) -> str:
        """Get the account email at a specific index"""
        config = self._memory_manager.GetFollowingConfig()
        return self._get_c_wchar_array_as_str(config.AccountEmails[index])

    def get_is_repulsion_allies_active_by_index(self, index: int) -> bool:
        """Get whether allies repulsion is active for a specific account index"""
        config = self._memory_manager.GetFollowingConfig()
        return config.IsRepulsionAlliesActive[index]

    def get_is_attraction_leader_active_by_index(self, index: int) -> bool:
        """Get whether leader attraction is active for a specific account index"""
        config = self._memory_manager.GetFollowingConfig()
        return config.IsAttractionLeaderActive[index]

    def get_is_repulsion_enemies_active_by_index(self, index: int) -> bool:
        """Get whether enemies repulsion is active for a specific account index"""
        config = self._memory_manager.GetFollowingConfig()
        return config.IsRepulsionEnemiesActive[index]

    def initialize_account_forces(self, account_email: str):
        """
        Initialize force activation flags for an account based on martial/caster status.
        This should be called when an account first uses spread_during_combat_utility.

        Args:
            account_email: The account email to initialize
            is_martial: True if the character is martial, False if caster
        """
        # Check if already initialized
        idx = self._get_account_index(account_email)
        if idx is not None:
            return  # Already initialized   

        # Create new entry with defaults based on martial/caster
        # Note: _get_or_create_account_index will add the email to the array if needed
        idx = self._get_or_create_account_index(account_email)
        if idx is None:
            return  # Could not create slot

        # Get fresh config after _get_or_create_account_index may have modified it
        config = self._memory_manager.GetFollowingConfig()

        config.IsRepulsionAlliesActive[idx] = False
        config.IsAttractionLeaderActive[idx] = False
        config.IsRepulsionEnemiesActive[idx] = False

        self._memory_manager.SetFollowingConfig(config)

    def set_account_forces(self, account_email: str, is_repulsion_allies_active: bool, is_attraction_leader_active: bool, is_repulsion_enemies_active: bool):
        idx = self._get_account_index(account_email)
        if idx is None:
            return  # Not found
        
        config = self._memory_manager.GetFollowingConfig()
        config.IsRepulsionAlliesActive[idx] = is_repulsion_allies_active
        config.IsAttractionLeaderActive[idx] = is_attraction_leader_active
        config.IsRepulsionEnemiesActive[idx] = is_repulsion_enemies_active
        self._memory_manager.SetFollowingConfig(config)

    def scatter_party(self):
        config = self._memory_manager.GetFollowingConfig()

        for idx in range(12):
            email = self._get_c_wchar_array_as_str(config.AccountEmails[idx])

            config.IsAttractionLeaderActive[idx] = False
            config.IsRepulsionEnemiesActive[idx] = False

            account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(email)
            if account is None:
                config.IsRepulsionAlliesActive[idx] = True
            else:
                # let's check if the agent is melee.
                is_melee = Agent.IsMelee(account.AgentData.AgentID)
                if is_melee:
                    config.IsRepulsionAlliesActive[idx] = False
                else:
                    config.IsRepulsionAlliesActive[idx] = True

    def close_to_leader(self):
        config = self._memory_manager.GetFollowingConfig()

        for idx in range(12):
            email = self._get_c_wchar_array_as_str(config.AccountEmails[idx])
            config.IsRepulsionAlliesActive[idx] = False
            config.IsAttractionLeaderActive[idx] = True
            config.IsRepulsionEnemiesActive[idx] = False

        self._memory_manager.SetFollowingConfig(config)

    def reset_all_forces(self):
        """Reset all force activation settings to defaults (all False)."""
        config = self._memory_manager.GetFollowingConfig()

        for idx in range(12):
            config.IsRepulsionAlliesActive[idx] = False
            config.IsAttractionLeaderActive[idx] = False
            config.IsRepulsionEnemiesActive[idx] = False

        self._memory_manager.SetFollowingConfig(config)
