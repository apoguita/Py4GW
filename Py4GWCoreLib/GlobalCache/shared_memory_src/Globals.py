from Py4GWCoreLib.enums_src.GameData_enums import Attribute

SHMEM_MODULE_NAME = "Py4GW - Shared Memory"
SHMEM_SHARED_MEMORY_FILE_NAME = "Py4GW_Shared_Mem"

SHMEM_MAX_PLAYERS = 64
SHMEM_MAX_EMAIL_LEN = 64
SHMEM_MAX_CHAR_LEN = 64
SHMEM_MAX_AVAILABLE_CHARS = 20
SHMEM_MAX_NUMBER_OF_BUFFS = 240
SHMEM_MAX_NUMBER_OF_SKILLS = 8
SHMEM_MAX_NUMBER_OF_ATTRIBUTES = len(Attribute) #5 primary + 3 secondary + 1 from of Profession Mod
SHMEM_MAX_TITLES = 48
SHMEM_MAX_QUESTS = 150

MISSION_BITMAP_ENTRIES = 25 #each entry is a bitmap of a mission flags (32 bits each)
SKILL_BITMAP_ENTRIES = 108 #each entry is a bitmap of a skill flags (32 bits each)

SHMEM_SUBSCRIBE_TIMEOUT_MILLISECONDS = 500 # milliseconds

# Shared memory update throttles (milliseconds)
# Tune these to balance responsiveness vs CPU cost.
SHMEM_HERO_UPDATE_THROTTLE_MS = 50
SHMEM_PET_UPDATE_THROTTLE_MS = 50

# Player account payload tiers
# Fast data (AgentData / AgentPartyData) is updated every callback.
SHMEM_PLAYER_META_UPDATE_THROTTLE_MS = 500      # rank/faction/experience
SHMEM_PLAYER_PROGRESS_UPDATE_THROTTLE_MS = 3000 # titles/questlog/mission
SHMEM_PLAYER_STATIC_UPDATE_THROTTLE_MS = 7500   # unlocked skills/available chars

# AgentData payload tiers
SHMEM_AGENT_FAST_UPDATE_THROTTLE_MS = 100
SHMEM_AGENT_MEDIUM_UPDATE_THROTTLE_MS = 250      # map/skillbar/attributes/buffs
SHMEM_AGENT_SLOW_UPDATE_THROTTLE_MS = 500       # level/profession/weapon metadata

# Hero/Pet wrapper extras (AccountStruct side)
SHMEM_HERO_EXTRA_UPDATE_THROTTLE_MS = 250
SHMEM_PET_EXTRA_UPDATE_THROTTLE_MS = 250

