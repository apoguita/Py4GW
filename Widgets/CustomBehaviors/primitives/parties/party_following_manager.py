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
    def combat_follow_distance(self) -> float:
        return self._memory_manager.GetFollowingConfig().CombatFollowDistance

    @combat_follow_distance.setter
    def combat_follow_distance(self, value: float):
        config = self._memory_manager.GetFollowingConfig()
        config.CombatFollowDistance = value
        self._memory_manager.SetFollowingConfig(config)

    @property
    def combat_spread_threshold(self) -> float:
        return self._memory_manager.GetFollowingConfig().CombatSpreadThreshold

    @combat_spread_threshold.setter
    def combat_spread_threshold(self, value: float):
        config = self._memory_manager.GetFollowingConfig()
        config.CombatSpreadThreshold = value
        self._memory_manager.SetFollowingConfig(config)

    @property
    def combat_repulsion_weight(self) -> float:
        return self._memory_manager.GetFollowingConfig().CombatRepulsionWeight

    @combat_repulsion_weight.setter
    def combat_repulsion_weight(self, value: float):
        config = self._memory_manager.GetFollowingConfig()
        config.CombatRepulsionWeight = value
        self._memory_manager.SetFollowingConfig(config)

    @property
    def noncombat_follow_distance(self) -> float:
        return self._memory_manager.GetFollowingConfig().NoncombatFollowDistance

    @noncombat_follow_distance.setter
    def noncombat_follow_distance(self, value: float):
        config = self._memory_manager.GetFollowingConfig()
        config.NoncombatFollowDistance = value
        self._memory_manager.SetFollowingConfig(config)

    @property
    def noncombat_spread_threshold(self) -> float:
        return self._memory_manager.GetFollowingConfig().NoncombatSpreadThreshold

    @noncombat_spread_threshold.setter
    def noncombat_spread_threshold(self, value: float):
        config = self._memory_manager.GetFollowingConfig()
        config.NoncombatSpreadThreshold = value
        self._memory_manager.SetFollowingConfig(config)

    @property
    def noncombat_repulsion_weight(self) -> float:
        return self._memory_manager.GetFollowingConfig().NoncombatRepulsionWeight

    @noncombat_repulsion_weight.setter
    def noncombat_repulsion_weight(self, value: float):
        config = self._memory_manager.GetFollowingConfig()
        config.NoncombatRepulsionWeight = value
        self._memory_manager.SetFollowingConfig(config)

    @property
    def follow_distance_tolerance(self) -> float:
        return self._memory_manager.GetFollowingConfig().FollowDistanceTolerance

    @follow_distance_tolerance.setter
    def follow_distance_tolerance(self, value: float):
        config = self._memory_manager.GetFollowingConfig()
        config.FollowDistanceTolerance = value
        self._memory_manager.SetFollowingConfig(config)

    @property
    def max_move_distance(self) -> float:
        return self._memory_manager.GetFollowingConfig().MaxMoveDistance

    @max_move_distance.setter
    def max_move_distance(self, value: float):
        config = self._memory_manager.GetFollowingConfig()
        config.MaxMoveDistance = value
        self._memory_manager.SetFollowingConfig(config)

    @property
    def min_move_threshold(self) -> float:
        return self._memory_manager.GetFollowingConfig().MinMoveThreshold

    @min_move_threshold.setter
    def min_move_threshold(self, value: float):
        config = self._memory_manager.GetFollowingConfig()
        config.MinMoveThreshold = value
        self._memory_manager.SetFollowingConfig(config)

    @property
    def enable_debug_overlay(self) -> bool:
        return self._memory_manager.GetFollowingConfig().EnableDebugOverlay

    @enable_debug_overlay.setter
    def enable_debug_overlay(self, value: bool):
        config = self._memory_manager.GetFollowingConfig()
        config.EnableDebugOverlay = value
        self._memory_manager.SetFollowingConfig(config)

    def apply_preset_tight_combat(self):
        """Apply tight combat formation preset"""
        self.combat_follow_distance = 100.0
        self.combat_spread_threshold = 120.0
        self.combat_repulsion_weight = 120.0
        self.noncombat_follow_distance = 150.0
        self.noncombat_spread_threshold = 80.0
        self.noncombat_repulsion_weight = 120.0

    def apply_preset_balanced(self):
        """Apply balanced formation preset (default)"""
        self.combat_follow_distance = 150.0
        self.combat_spread_threshold = 150.0
        self.combat_repulsion_weight = 150.0
        self.noncombat_follow_distance = 200.0
        self.noncombat_spread_threshold = 100.0
        self.noncombat_repulsion_weight = 150.0

    def apply_preset_loose_formation(self):
        """Apply loose formation preset"""
        self.combat_follow_distance = 200.0
        self.combat_spread_threshold = 180.0
        self.combat_repulsion_weight = 180.0
        self.noncombat_follow_distance = 300.0
        self.noncombat_spread_threshold = 120.0
        self.noncombat_repulsion_weight = 180.0

