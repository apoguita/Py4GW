from enum import Enum

class DisabilityPriority(Enum):
    '''
    When multiple disabilities are detected, 2 algorithms are possible : 
    - if we can only remove 1 disability, the highest priority one is selected.
    - if we can remove multiple disabilities, we could try to sum them :
        example : 
            1x Very_High > 2x High > 4x Normal
            3x High > 1x Very_High
            3x Normal > 1x High
            ect
    
    '''
    VERY_HIGH = 14
    HIGH = 5
    NORMAL = 2
