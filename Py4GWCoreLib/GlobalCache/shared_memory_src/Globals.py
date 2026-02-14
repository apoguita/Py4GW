from Py4GWCoreLib.enums_src.GameData_enums import Attribute

SHMEM_MODULE_NAME = "Py4GW - Shared Memory"
SHMEM_SHARED_MEMORY_FILE_NAME = "Py4GW_Shared_Mem"

SHMEM_MAX_PLAYERS = 64
SHMEM_MAX_EMAIL_LEN = 64
SHMEM_MAX_CHAR_LEN = 30
SHMEM_MAX_AVAILABLE_CHARS = 20
SHMEM_MAX_NUMBER_OF_BUFFS = 240
SHMEM_MAX_NUMBER_OF_SKILLS = 8
SHMEM_MAX_NUMBER_OF_ATTRIBUTES = len(Attribute) #5 primary + 3 secondary + 1 from of Profession Mod
SHMEM_MAX_TITLES = 48
SHMEM_MAX_QUESTS = 150

MISSION_BITMAP_ENTRIES = 25 #each entry is a bitmap of a mission flags (32 bits each)
SKILL_BITMAP_ENTRIES = 108 #each entry is a bitmap of a skill flags (32 bits each)
