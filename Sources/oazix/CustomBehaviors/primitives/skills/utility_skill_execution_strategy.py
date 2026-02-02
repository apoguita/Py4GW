from enum import Enum

# Create an enumeration
class UtilitySkillExecutionStrategy(Enum):
    EXECUTE_THROUGH_THE_END = 1 
    STOP_EXECUTION_ONCE_SCORE_NOT_HIGHEST = 2