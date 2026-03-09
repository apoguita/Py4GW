from enum import Enum

class FollowingBehaviorPriority(Enum):
    HIGH_PRIORITY = 1
    HIGH_PRIORITY_WITH_THROTTLE = 2
    LOW_PRIORITY = 3
    NONE = 10