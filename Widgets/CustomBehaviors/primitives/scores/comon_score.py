from enum import Enum, auto

class CommonScore(Enum):
    FOLLOW                          = 01.000
    FOLLOW_FLAG                     = 01.001
    LOOT                            = 01.100
    AUTO_ATTACK                     = 09.900
    GENERIC_SKILL_HERO_AI           = 09.910
    LOWER_COMBAT                    = 10.000 # combat_skill cannot be lower than 10
    FOLLOW_FLAG_REQUIRED            = 99.001
    BOTTING                         = 99.500
    DEAMON                          = 99.600
