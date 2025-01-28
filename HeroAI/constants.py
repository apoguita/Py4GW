"""This file contains the constants and globals used by the HeroAI module."""
from Py4GWCoreLib import *

TRUE = 1
FALSE = 0
"""module constant"""
MODULE_NAME = "HeroAI"
SMM_MODULE_NAME = "HeroAI - Shared Memory Manager"
CANDIDATES_MODULE_NAME = "HeroAI - Candidates"
GAME_OPTION_MODULE_NAME = "HeroAI - Game Option"
PLAYERS_MODULE_NAME = "HeroAI - Players"
WINDOWS_MODULE_NAME = "HeroAI - Window - "

"""shared memory constants"""
MAX_NUM_PLAYERS = 8
NUMBER_OF_SKILLS = 8
MAX_NUMBER_OF_BUFFS = 240
SHARED_MEMORY_FILE_NAME = "HeroAI_Mem"
LOCK_MUTEX_TIMEOUT = 1 #SECONDS
SUBSCRIBE_TIMEOUT_SECONDS = 250 # milliseconds

class Range(Enum):
    Touch = 144.0
    Adjacent = 166.0
    Nearby = 252.0
    Area = 322.0
    Earshot = 1012.0
    Spellcast = 1248.0
    Spirit = 2500.0
    SafeCompass = 4800.0 #made up distance to make easy checks
    Compass = 5000.0

""" HELPER CONSTANTS """
MELEE_RANGE_VALUE = Range.Spellcast.value
RANGED_RANGE_VALUE = Range.Spellcast.value
FOLLOW_DISTANCE_ON_COMBAT = Range.Spellcast.value
FOLLOW_DISTANCE_OUT_OF_COMBAT = Range.Area.value

STAY_ALERT_TIME = 3000  # milliseconds

BLOOD_IS_POWER = 119  # skill id
BLOOD_RITUAL = 157  # skill id