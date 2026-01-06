"""This file contains the constants and globals used by the HeroAI module."""
from Py4GWCoreLib import Range, GLOBAL_CACHE

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
MAX_NUM_PLAYERS = 12
NUMBER_OF_SKILLS = 8
MAX_NUMBER_OF_BUFFS = 240
SHARED_MEMORY_FILE_NAME = "HeroAI_Mem"
LOCK_MUTEX_TIMEOUT = 1 #SECONDS
SUBSCRIBE_TIMEOUT_SECONDS = 500 # milliseconds

""" HELPER CONSTANTS """
MELEE_RANGE_VALUE = Range.Spellcast.value
RANGED_RANGE_VALUE = Range.Spellcast.value
FOLLOW_DISTANCE_ON_COMBAT = Range.Spellcast.value
FOLLOW_DISTANCE_OUT_OF_COMBAT = Range.Area.value

STAY_ALERT_TIME = 750  # milliseconds

BLOOD_IS_POWER = GLOBAL_CACHE.Skill.GetID("Blood_is_Power")
BLOOD_RITUAL = GLOBAL_CACHE.Skill.GetID("Blood_Ritual")  # skill id

PARTY_WINDOW_HASH = 3332025202
PARTY_WINDOW_FRAME_OUTPOST_OFFSETS = [1]
PARTY_WINDOW_FRAME_EXPLORABLE_OFFSETS = [0]
SKILLBAR_WINDOW_HASH = 641635682

""" AI CONSTANTS """