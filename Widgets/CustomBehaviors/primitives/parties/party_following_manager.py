"""
Singleton manager for party following configuration.
Stores all parameters in shared RAM memory for cross-process access.
"""

from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager

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




