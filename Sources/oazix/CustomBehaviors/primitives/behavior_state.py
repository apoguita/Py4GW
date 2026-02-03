from enum import Enum

# Create an enumeration
class BehaviorState(Enum):
    IN_AGGRO = 1

    FAR_FROM_AGGRO = 5
    CLOSE_TO_AGGRO = 6

    IDLE = 10
