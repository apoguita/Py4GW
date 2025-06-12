from enum import Enum, IntEnum

class SharedCommandType(IntEnum):
    NoCommand = 0
    TravelToMap = 1
    InviteToParty = 2
    InteractWithTarget = 3
    TakeDialogWithTarget = 4
    GetBlessing = 5
    OpenChest = 6
    PickUpLoot = 7
    UseSkill = 8
    Resign = 9
    PixelStack = 10
    PCon = 11
    IdentifyItems = 12
    SalvageItems = 13
    MerchantItems = 14
    MerchantMaterials = 15
    LootEx = 16 #privately Handled Command, by Frenkey

#region mouse
class MouseButton(IntEnum):
    Left = 0
    Right = 1
    Middle = 2

#region Key
class Key(Enum):
    # Letters
    A = 0x41
    B = 0x42
    C = 0x43
    D = 0x44
    E = 0x45
    F = 0x46
    G = 0x47
    H = 0x48
    I = 0x49
    J = 0x4A
    K = 0x4B
    L = 0x4C
    M = 0x4D
    N = 0x4E
    O = 0x4F
    P = 0x50
    Q = 0x51
    R = 0x52
    S = 0x53
    T = 0x54
    U = 0x55
    V = 0x56
    W = 0x57
    X = 0x58
    Y = 0x59
    Z = 0x5A

    # Numbers (Top row, not numpad)
    Zero = 0x30
    One = 0x31
    Two = 0x32
    Three = 0x33
    Four = 0x34
    Five = 0x35
    Six = 0x36
    Seven = 0x37
    Eight = 0x38
    Nine = 0x39

    # Function keys
    F1 = 0x70
    F2 = 0x71
    F3 = 0x72
    F4 = 0x73
    F5 = 0x74
    F6 = 0x75
    F7 = 0x76
    F8 = 0x77
    F9 = 0x78
    F10 = 0x79
    F11 = 0x7A
    F12 = 0x7B

    # Control keys
    Shift = 0x10
    Ctrl = 0x11
    Alt = 0x12
    Enter = 0x0D
    Escape = 0x1B
    Space = 0x20
    Tab = 0x09
    Backspace = 0x08
    Delete = 0x2E
    Insert = 0x2D
    Home = 0x24
    End = 0x23
    PageUp = 0x21
    PageDown = 0x22

    # Arrow keys
    LeftArrow = 0x25
    UpArrow = 0x26
    RightArrow = 0x27
    DownArrow = 0x28

    # Numpad keys
    Numpad0 = 0x60
    Numpad1 = 0x61
    Numpad2 = 0x62
    Numpad3 = 0x63
    Numpad4 = 0x64
    Numpad5 = 0x65
    Numpad6 = 0x66
    Numpad7 = 0x67
    Numpad8 = 0x68
    Numpad9 = 0x69
    NumpadMultiply = 0x6A
    NumpadAdd = 0x6B
    NumpadSubtract = 0x6D
    NumpadDecimal = 0x6E
    NumpadDivide = 0x6F

    # Miscellaneous
    CapsLock = 0x14
    PrintScreen = 0x2C
    ScrollLock = 0x91
    Pause = 0x13

    # Special characters (US standard keyboard) (Danish standard keyboard) (English standard keyboard)
    Semicolon = 0xBA       # ;                   # æ                        # ;
    Equal = 0xBB           # =                   # ´                        # =
    Comma = 0xBC           # ,                   # ,                        # ,
    Minus = 0xBD           # -                   # +                        # -
    Period = 0xBE          # .                   # .                        # .
    Slash = 0xBF           # /                   # -                        # /
    Backtick = 0xC0        # `                   # ½                        # `
    LeftBracket = 0xDB     # [                   # å                        # [
    Backslash = 0xDC       # \                   # '                        # #
    RightBracket = 0xDD    # ]                   # ¨                        # ]
    Apostrophe = 0xDE      # '                   # ø                        # '

#region Console
class Console:
    class MessageType:
        Info = 0
        Warning = 1
        Error = 2
        Debug = 3
        Success = 4
        Performance = 5
        Notice = 6
        
#endregion
#region Range  
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

#endregion
#region ServerRegion
class ServerRegion(IntEnum):
    International = -2
    America = 0
    Korea = 1
    Europe = 2
    China = 3
    Japan = 4
    Unknown = 255

#endregion
#region ServerRegionName
ServerRegionName = {
    ServerRegion.International.value: "International",
    ServerRegion.America.value: "America",
    ServerRegion.Korea.value: "Korea",
    ServerRegion.Europe.value: "Europe",
    ServerRegion.China.value: "Traditional Chinese",
    ServerRegion.Japan.value: "Japanese",
}
       
#endregion
#region ServerLanguage
class ServerLanguage(IntEnum):
    English = 0
    Korean = 1
    French = 2
    German = 3
    Italian = 4
    Spanish = 5
    TraditionalChinese = 6
    Japanese = 8
    Polish = 9
    Russian = 10
    BorkBorkBork = 17
    Unknown = 255

#endregion
#region ServerLanguageName
ServerLanguageName = {
    ServerLanguage.English.value: "English",
    ServerLanguage.Korean.value: "Korean",
    ServerLanguage.French.value: "French",
    ServerLanguage.German.value: "German",
    ServerLanguage.Italian.value: "Italian",
    ServerLanguage.Spanish.value: "Spanish",
    ServerLanguage.TraditionalChinese.value: "Traditional Chinese",
    ServerLanguage.Japanese.value: "Japanese",
    ServerLanguage.Polish.value: "Polish",
    ServerLanguage.Russian.value: "Russian",
    ServerLanguage.BorkBorkBork.value: "Bork Bork Bork",
    ServerLanguage.Unknown.value: "Unknown",
}

#endregion

#region District
class District(IntEnum):
    Current = 0
    International = 1
    American = 2
    EuropeEnglish = 3
    EuropeFrench = 4
    EuropeGerman = 5
    EuropeItalian = 6
    EuropeSpanish = 7
    EuropePolish = 8
    EuropeRussian = 9
    AsiaKorean = 10
    AsiaChinese = 11
    AsiaJapanese = 12
    Unknown = 255

#endregion
#region Language
class Language(IntEnum):
    English = 0
    Korean = 1
    French = 2
    German = 3
    Italian = 4
    Spanish = 5
    TraditionalChinese = 6
    Japanese = 8
    Polish = 9
    Russian = 10
    BorkBorkBork = 17
    Unknown = 255

#endregion
#region District

#region ampaign
class Campaign(IntEnum):
    Core = 0
    Prophecies = 1
    Factions = 2
    Nightfall = 3
    EyeOfTheNorth = 4
    BonusMissionPack = 5
    Undefined = 6

#endregion
#region RegionType
class RegionType(IntEnum):
    AllianceBattle = 0
    Arena = 1
    ExplorableZone = 2
    GuildBattleArea = 3
    GuildHall = 4
    MissionOutpost = 5
    CooperativeMission = 6
    CompetitiveMission = 7
    EliteMission = 8
    Challenge = 9
    Outpost = 10
    ZaishenBattle = 11
    HeroesAscent = 12
    City = 13
    MissionArea = 14
    HeroBattleOutpost = 15
    HeroBattleArea = 16
    EotnMission = 17
    Dungeon = 18
    Marketplace = 19
    Unknown = 20
    DevRegion = 21

#endregion
#region Continent
class Continent(IntEnum):
    Kryta = 0
    DevContinent = 1
    Cantha = 2
    BattleIsles = 3
    Elona = 4
    RealmOfTorment = 5
    Undefined = 6

#endregion
#region Rarity
class Rarity(IntEnum):
    White = 0
    Blue = 1
    Purple = 2
    Gold = 3
    Green = 4

# SalvageAllType
class SalvageAllType(IntEnum):
    None_ = 0
    White = 1
    BlueAndLower = 2
    PurpleAndLower = 3
    GoldAndLower = 4

# IdentifyAllType
class IdentifyAllType(IntEnum):
    None_ = 0
    All = 1
    Blue = 2
    Purple = 3
    Gold = 4
    
#endregion
#region bags 
class Bags(IntEnum):
    NoBag = 0
    Backpack = 1
    BeltPouch = 2
    Bag1 = 3
    Bag2 = 4
    EquipmentPack = 5
    MaterialStorage = 6
    UnclaimedItems = 7
    Storage1 = 8
    Storage2 = 9
    Storage3 = 10
    Storage4 = 11
    Storage5 = 12
    Storage6 = 13
    Storage7 = 14
    Storage8 = 15
    Storage9 = 16
    Storage10 = 17
    Storage11 = 18
    Storage12 = 19
    Storage13 = 20
    Storage14 = 21
    EquippedItems = 22



#endregion
#region ItemType
class ItemType(IntEnum):
    Salvage = 0
    Axe = 2
    Bag = 3
    Boots = 4
    Bow = 5
    Bundle = 6
    Chestpiece = 7
    Rune_Mod = 8
    Usable =9
    Dye = 10
    Materials_Zcoins = 11
    Offhand = 12
    Gloves = 13
    Hammer = 15
    Headpiece = 16
    CC_Shards = 17
    Key = 18
    Leggings = 19
    Gold_Coin = 20
    Quest_Item = 21
    Wand = 22
    Shield = 24
    Staff = 26
    Sword = 27
    Kit = 29
    Trophy = 30
    Scroll = 31
    Daggers = 32
    Present = 33
    Minipet = 34
    Scythe = 35
    Spear = 36
    Weapon = 37
    MartialWeapon = 38
    OffhandOrShield = 39
    EquippableItem = 40
    SpellcastingWeapon = 41
    Storybook = 43
    Costume = 44
    Costume_Headpiece = 45
    Unknown = 255

#endregion
#region DyeColor
class DyeColor(IntEnum):
    NoColor = 0
    Blue = 2
    Green = 3
    Purple = 4
    Red = 5
    Yellow = 6
    Brown = 7
    Orange = 8
    Silver = 9
    Black = 10
    Gray = 11
    White = 12
    Pink = 13

#endregion
#region Profession
class Profession(IntEnum):
    _None = 0  
    Warrior = 1
    Ranger = 2
    Monk = 3
    Necromancer = 4
    Mesmer = 5
    Elementalist = 6
    Assassin = 7
    Ritualist = 8
    Paragon = 9
    Dervish = 10
    
class ProfessionShort(IntEnum):
    _ = 0  
    W = 1
    R = 2
    Mo = 3
    N = 4
    Me = 5
    E = 6
    A = 7
    Rt = 8
    P = 9
    D = 10

#endregion
#region Allegiance
class Allegiance(IntEnum):
    Unknown = 0
    Ally = 1  # 0x1 = ally/non-attackable
    Neutral = 2  # 0x2 = neutral
    Enemy = 3  # 0x3 = enemy
    SpiritPet = 4  # 0x4 = spirit/pet
    Minion = 5  # 0x5 = minion
    NpcMinipet = 6  # 0x6 = npc/minipet
    
# AllieganceDonation
class FactionAllegiance(IntEnum):
    Kurzick = 0
    Luxon = 1
    
#endregion
#region Mod structs
class Ailment(IntEnum):
    Bleeding = 222
    Blind = 223
    Crippled = 225
    Deep_Wound = 226
    Disease = 227
    Poison = 228
    Dazed = 229
    Weakness = 230
    
class Reduced_Ailment(IntEnum):
    Bleeding = 0
    Blind = 1
    Crippled = 3
    Deep_Wound = 4
    Disease = 5
    Poison = 6
    Dazed = 7
    Weakness = 8
    
#DamageType
class DamageType(IntEnum):
    Blunt = 0
    Piercing = 1
    Slashing = 2
    Cold = 3
    Lightning = 4
    Fire = 5
    Chaos = 6
    Dark = 7
    Holy = 8
    unknown_9 = 9
    unknown_10 = 10
    Earth = 11
    unknown_12 = 12
    unknown_13 = 13
    unknown_14 = 14
    unknown_15 = 15

#WeaponType
class Weapon(IntEnum):
    Unknown = 0
    Bow = 1
    Axe = 2
    Hammer = 3
    Daggers = 4
    Scythe = 5
    Spear = 6
    Sword = 7
    Scepter = 8
    Scepter2 = 9
    Wand = 10
    Staff1 = 11
    Staff = 12
    Staff2 = 13
    Staff3 = 14
    Unknown1 = 15
    Unknown2 = 16
    Unknown3 = 17
    Unknown4 = 18
    Unknown5 = 19
    Unknown6 = 20
    Unknown7 = 21
    Unknown8 = 22
    Unknown9 = 23
    Unknown10 = 24

# Attribute
class Attribute(IntEnum):
    FastCasting = 0
    IllusionMagic = 1
    DominationMagic = 2
    InspirationMagic = 3
    BloodMagic = 4
    DeathMagic = 5
    SoulReaping = 6
    Curses = 7
    AirMagic = 8
    EarthMagic = 9
    FireMagic = 10
    WaterMagic = 11
    EnergyStorage = 12
    HealingPrayers = 13
    SmitingPrayers = 14
    ProtectionPrayers = 15
    DivineFavor = 16
    Strength = 17
    AxeMastery = 18
    HammerMastery = 19
    Swordsmanship = 20
    Tactics = 21
    BeastMastery = 22
    Expertise = 23
    WildernessSurvival = 24
    Marksmanship = 25
    Unknown1 = 26
    Unknown2 = 27
    Unknown3 = 28
    DaggerMastery = 29
    DeadlyArts = 30
    ShadowArts = 31
    Communing = 32
    RestorationMagic = 33
    ChannelingMagic = 34
    CriticalStrikes = 35
    SpawningPower = 36
    SpearMastery = 37
    Command = 38
    Motivation = 39
    Leadership = 40
    ScytheMastery = 41
    WindPrayers = 42
    EarthPrayers = 43
    Mysticism = 44
    None_ = 45  # Avoiding reserved keyword "None"
    
#Inscription
class Inscription(IntEnum):
    Fear_Cuts_Deeper = 0
    I_Can_See_Clearly_Now = 1
    Swift_as_the_Wind = 3
    Strenght_of_Body = 4
    Cast_Out_the_Unclean = 5
    Pure_of_Heart = 6
    Soundness_of_Mind = 7
    Only_the_Strong_Survive = 8

    Not_the_Face = 134
    Leaf_on_the_Wind = 136
    Like_a_Rolling_Stone = 138
    Riders_on_the_Storm = 140
    Sleep_Now_in_the_Fire = 142
    Trough_Thick_and_Thin = 144
    The_Riddle_of_Steel = 146


#endregion
#region PetBehavior
class PetBehavior(IntEnum):
    Fight = 0
    Guard = 1
    Heel = 2

#endregion
#region HeroType
class HeroType(IntEnum):
    None_ = 0  # Avoiding reserved keyword "None"
    Norgu = 1
    Goren = 2
    Tahlkora = 3
    MasterOfWhispers = 4
    AcolyteJin = 5
    Koss = 6
    Dunkoro = 7
    AcolyteSousuke = 8
    Melonni = 9
    ZhedShadowhoof = 10
    GeneralMorgahn = 11
    MagridTheSly = 12
    Zenmai = 13
    Olias = 14
    Razah = 15
    MOX = 16
    KeiranThackeray = 17
    Jora = 18
    PyreFierceshot = 19
    Anton = 20
    Livia = 21
    Hayda = 22
    Kahmu = 23
    Gwen = 24
    Xandra = 25
    Vekk = 26
    Ogden = 27
    MercenaryHero1 = 28
    MercenaryHero2 = 29
    MercenaryHero3 = 30
    MercenaryHero4 = 31
    MercenaryHero5 = 32
    MercenaryHero6 = 33
    MercenaryHero7 = 34
    MercenaryHero8 = 35
    Miku = 36
    ZeiRi = 37
  
#endregion
#region ChatChannel  
class ChatChannel(IntEnum):
    CHANNEL_ALLIANCE = 0
    CHANNEL_ALLIES = 1  # Coop with two groups for instance.
    CHANNEL_GWCA1 = 2
    CHANNEL_ALL = 3
    CHANNEL_GWCA2 = 4
    CHANNEL_MODERATOR = 5
    CHANNEL_EMOTE = 6
    CHANNEL_WARNING = 7  # Shows in the middle of the screen and does not parse <c> tags
    CHANNEL_GWCA3 = 8
    CHANNEL_GUILD = 9
    CHANNEL_GLOBAL = 10
    CHANNEL_GROUP = 11
    CHANNEL_TRADE = 12
    CHANNEL_ADVISORY = 13
    CHANNEL_WHISPER = 14
    CHANNEL_COUNT = 15

    # Non-standard channels, but useful.
    CHANNEL_COMMAND = 16
    CHANNEL_UNKNOW = -1

#endregion
#region UIManager

class UIMessage(IntEnum):
    kNone = 0x0
    kInitFrame = 0x9
    kDestroyFrame = 0xb
    kKeyDown = 0x1e  # wparam = UIPacket::kKeyAction*
    kKeyUp = 0x20  # wparam = UIPacket::kKeyAction*
    kMouseClick = 0x22  # wparam = UIPacket::kMouseClick*
    kMouseClick2 = 0x2e  # wparam = UIPacket::kMouseAction*
    kMouseAction = 0x2f  # wparam = UIPacket::kMouseAction*
    kUpdateAgentEffects = 0x10000009
    kRerenderAgentModel = 0x10000007  # wparam = uint32_t agent_id
    kShowAgentNameTag = 0x10000019  # wparam = AgentNameTagInfo*
    kHideAgentNameTag = 0x1000001A
    kSetAgentNameTagAttribs = 0x1000001B  # wparam = AgentNameTagInfo*
    kChangeTarget = 0x10000020  # wparam = ChangeTargetUIMsg*
    kAgentStartCasting = 0x10000027  # wparam = { uint32_t agent_id, uint32_t skill_id }
    kShowMapEntryMessage = 0x10000029  # wparam = { wchar_t* title, wchar_t* subtitle }
    kSetCurrentPlayerData = 0x1000002A
    kPostProcessingEffect = 0x10000034  # wparam = UIPacket::kPostProcessingEffect
    kHeroAgentAdded = 0x10000038
    kHeroDataAdded = 0x10000039
    kShowXunlaiChest = 0x10000040
    kMinionCountUpdated = 0x10000046
    kMoraleChange = 0x10000047  # wparam = {agent id, morale percent }
    kLoginStateChanged = 0x10000050  # wparam = {bool is_logged_in, bool unk }
    kEffectAdd = 0x10000055  # wparam = {agent_id, GW::Effect*}
    kEffectRenew = 0x10000056  # wparam = GW::Effect*
    kEffectRemove = 0x10000057  # wparam = effect id
    kUpdateSkillbar = 0x1000005E  # wparam = { uint32_t agent_id , ... }
    kSkillActivated = 0x1000005B  # wparam = { uint32_t agent_id , uint32_t skill_id }
    kTitleProgressUpdated = 0x10000065  # wparam = title_id
    kExperienceGained = 0x10000066  # wparam = experience amount
    kWriteToChatLog = 0x1000007E  # wparam = UIPacket::kWriteToChatLog*
    kWriteToChatLogWithSender = 0x1000007F  # wparam = UIPacket::kWriteToChatLogWithSender*
    kPlayerChatMessage = 0x10000081  # wparam = UIPacket::kPlayerChatMessage*
    kFriendUpdated = 0x10000089  # wparam = { GW::Friend*, ... }
    kMapLoaded = 0x1000008A
    kOpenWhisper = 0x10000090  # wparam = wchar* name
    kLogout = 0x1000009B  # wparam = { bool unknown, bool character_select }
    kCompassDraw = 0x1000009C  # wparam = UIPacket::kCompassDraw*
    kOnScreenMessage = 0x100000A0  # wparam = wchar_** encoded_string
    kDialogBody = 0x100000A4  # wparam = DialogBodyInfo*
    kDialogButton = 0x100000A1  # wparam = DialogButtonInfo*
    kTargetNPCPartyMember = 0x100000B1  # wparam = { uint32_t unk, uint32_t agent_id }
    kTargetPlayerPartyMember = 0x100000B2  # wparam = { uint32_t unk, uint32_t player_number }
    kInitMerchantList = 0x100000B3  # wparam = { uint32_t merchant_tab_type, uint32_t unk, uint32_t merchant_agent_id, uint32_t is_pending }
    kQuotedItemPrice = 0x100000BB  # wparam = { uint32_t item_id, uint32_t price }
    kStartMapLoad = 0x100000C0  # wparam = { uint32_t map_id, ... }
    kWorldMapUpdated = 0x100000C5
    kGuildMemberUpdated = 0x100000D8  # wparam = { GuildPlayer::name_ptr }
    kShowHint = 0x100000DF  # wparam = { uint32_t icon_type, wchar_t* message_enc }
    kUpdateGoldCharacter = 0x100000EA  # wparam = { uint32_t unk, uint32_t gold_character }
    kUpdateGoldStorage = 0x100000EB  # wparam = { uint32_t unk, uint32_t gold_storage }
    kInventorySlotUpdated = 0x100000EC  # Triggered when an item is moved into a slot
    kEquipmentSlotUpdated = 0x100000ED  # Triggered when an item is moved into a slot
    kInventorySlotCleared = 0x100000EF  # Triggered when an item is removed from a slot
    kEquipmentSlotCleared = 0x100000F0  # Triggered when an item is removed from a slot
    kPvPWindowContent = 0x100000F8
    kPreStartSalvage = 0x10000100  # { uint32_t item_id, uint32_t kit_id }
    kTradePlayerUpdated = 0x10000103  # wparam = GW::TraderPlayer*
    kItemUpdated = 0x10000104  # wparam = UIPacket::kItemUpdated*
    kMapChange = 0x1000010F  # wparam = map id
    kCalledTargetChange = 0x10000113  # wparam = { player_number, target_id }
    kErrorMessage = 0x10000117  # wparam = { int error_index, wchar_t* error_encoded_string }
    kSendEnterMission = 0x30000002  # wparam = uint32_t arena_id
    kSendLoadSkillbar = 0x30000003  # wparam = UIPacket::kSendLoadSkillbar*
    kSendPingWeaponSet = 0x30000004  # wparam = UIPacket::kSendPingWeaponSet*
    kSendMoveItem = 0x30000005  # wparam = UIPacket::kSendMoveItem*
    kSendMerchantRequestQuote = 0x30000006  # wparam = UIPacket::kSendMerchantRequestQuote*
    kSendMerchantTransactItem = 0x30000007  # wparam = UIPacket::kSendMerchantTransactItem*
    kSendUseItem = 0x30000008  # wparam = UIPacket::kSendUseItem*
    kSendSetActiveQuest = 0x30000009  # wparam = uint32_t quest_id
    kSendAbandonQuest = 0x3000000A  # wparam = uint32_t quest_id
    kSendChangeTarget = 0x3000000B  # wparam = UIPacket::kSendChangeTarget*
    kSendMoveToWorldPoint = 0x3000000C  # wparam = GW::GamePos*  # Clicking on the ground in the 3D world to move there
    kSendInteractNPC = 0x3000000D  # wparam = UIPacket::kInteractAgent*
    kSendInteractGadget = 0x3000000E  # wparam = UIPacket::kInteractAgent*
    kSendInteractItem = 0x3000000F  # wparam = UIPacket::kInteractAgent*
    kSendInteractEnemy = 0x30000010  # wparam = UIPacket::kInteractAgent*
    kSendInteractPlayer = 0x30000011  # wparam = uint32_t agent_id  # NB: calling target is a separate packet
    kSendCallTarget = 0x30000013  # wparam = { uint32_t call_type, uint32_t agent_id }  # Also used to broadcast morale, death penalty, "I'm following X", etc
    kSendAgentDialog = 0x30000014  # wparam = uint32_t agent_id  # e.g., switching tabs on a merchant window, choosing a response to an NPC dialog
    kSendGadgetDialog = 0x30000015  # wparam = uint32_t agent_id  # e.g., opening locked chest with a key
    kSendDialog = 0x30000016  # wparam = dialog_id  # Internal use

    kStartWhisper = 0x30000017  # wparam = UIPacket::kStartWhisper*
    kGetSenderColor = 0x30000018  # wparam = UIPacket::kGetColor*  # Get chat sender color depending on the channel, output object passed by reference
    kGetMessageColor = 0x30000019  # wparam = UIPacket::kGetColor*  # Get chat message color depending on the channel, output object passed by reference
    kSendChatMessage = 0x3000001B  # wparam = UIPacket::kSendChatMessage*
    kLogChatMessage = 0x3000001D  # wparam = UIPacket::kLogChatMessage*  # Triggered when a message wants to be added to the persistent chat log
    kRecvWhisper = 0x3000001E  # wparam = UIPacket::kRecvWhisper*
    kPrintChatMessage = 0x3000001F  # wparam = UIPacket::kPrintChatMessage*  # Triggered when a message wants to be added to the in-game chat window
    kSendWorldAction = 0x30000020  # wparam = UIPacket::kSendWorldAction*

class EnumPreference(IntEnum):
    CharSortOrder = 0
    AntiAliasing = 1  # multi sampling
    Reflections = 2
    ShaderQuality = 3
    ShadowQuality = 4
    TerrainQuality = 5
    InterfaceSize = 6
    FrameLimiter = 7
    Count = 8  # Not meant for use as a real value; represents size
    
class StringPreference(IntEnum):
    Unk1 = 0
    Unk2 = 1
    LastCharacterName = 2
    Count = 3  # Internal use only
    
class NumberPreference(IntEnum):
    AutoTournPartySort = 0
    ChatState = 1  # 1 == showing chat window, 0 == hidden
    ChatTab = 2
    DistrictLastVisitedLanguage = 3
    DistrictLastVisitedLanguage2 = 4
    DistrictLastVisitedNonInternationalLanguage = 5
    DistrictLastVisitedNonInternationalLanguage2 = 6
    DamageTextSize = 7  # Range: 0–100
    FullscreenGamma = 8  # Range: 0–100
    InventoryBag = 9
    TextLanguage = 10
    AudioLanguage = 11
    ChatFilterLevel = 12
    RefreshRate = 13
    ScreenSizeX = 14
    ScreenSizeY = 15
    SkillListFilterRarity = 16
    SkillListSortMethod = 17
    SkillListViewMode = 18
    SoundQuality = 19  # Range: 0–100
    StorageBagPage = 20
    Territory = 21
    TextureQuality = 22  # TextureLod
    UseBestTextureFiltering = 23
    EffectsVolume = 24  # Range: 0–100
    DialogVolume = 25  # Range: 0–100
    BackgroundVolume = 26  # Range: 0–100
    MusicVolume = 27  # Range: 0–100
    UIVolume = 28  # Range: 0–100
    Vote = 29
    WindowPosX = 30
    WindowPosY = 31
    WindowSizeX = 32
    WindowSizeY = 33
    SealedSeed = 34  # Codex Arena
    SealedCount = 35  # Codex Arena
    FieldOfView = 36  # Range: 0–100
    CameraRotationSpeed = 37  # Range: 0–100
    ScreenBorderless = 38  # 0x1 = Borderless, 0x2 = Fullscreen Windowed
    MasterVolume = 39  # Range: 0–100
    ClockMode = 40
    Count = 41  # Internal use

class FlagPreference(IntEnum):
    # Boolean preferences
    ChannelAlliance = 0x4
    ChannelEmotes = 0x6
    ChannelGuild = 0x7
    ChannelLocal = 0x8
    ChannelGroup = 0x9
    ChannelTrade = 0xA

    ShowTextInSkillFloaters = 0x11
    ShowKRGBRatingsInGame = 0x12

    AutoHideUIOnLoginScreen = 0x14
    DoubleClickToInteract = 0x15
    InvertMouseControlOfCamera = 0x16
    DisableMouseWalking = 0x17
    AutoCameraInObserveMode = 0x18
    AutoHideUIInObserveMode = 0x19

    RememberAccountName = 0x2D
    IsWindowed = 0x2E

    ShowSpendAttributesButton = 0x31  # Shows button next to EXP bar
    ConciseSkillDescriptions = 0x32
    DoNotShowSkillTipsOnEffectMonitor = 0x33
    DoNotShowSkillTipsOnSkillBars = 0x34

    MuteWhenGuildWarsIsInBackground = 0x37

    AutoTargetFoes = 0x39
    AutoTargetNPCs = 0x3A
    AlwaysShowNearbyNamesPvP = 0x3B
    FadeDistantNameTags = 0x3C

    DoNotCloseWindowsOnEscape = 0x45
    ShowMinimapOnWorldMap = 0x46

    WaitForVSync = 0x54
    WhispersFromFriendsEtcOnly = 0x55
    ShowChatTimestamps = 0x56
    ShowCollapsedBags = 0x57
    ItemRarityBorder = 0x58
    AlwaysShowAllyNames = 0x59
    AlwaysShowFoeNames = 0x5A

    LockCompassRotation = 0x5C

    Count = 0x5D  # For internal size check

class WindowID(IntEnum):
    WindowID_Dialogue1 = 0x0
    WindowID_Dialogue2 = 0x1
    WindowID_MissionGoals = 0x2
    WindowID_DropBundle = 0x3
    WindowID_Chat = 0x4
    WindowID_InGameClock = 0x6
    WindowID_Compass = 0x7
    WindowID_DamageMonitor = 0x8
    WindowID_PerformanceMonitor = 0xB
    WindowID_EffectsMonitor = 0xC
    WindowID_Hints = 0xD
    WindowID_MissionProgress = 0xE
    WindowID_MissionStatusAndScoreDisplay = 0xF
    WindowID_Notifications = 0x11
    WindowID_Skillbar = 0x14
    WindowID_SkillMonitor = 0x15
    WindowID_UpkeepMonitor = 0x17
    WindowID_SkillWarmup = 0x18
    WindowID_Menu = 0x1A
    WindowID_EnergyBar = 0x1C
    WindowID_ExperienceBar = 0x1D
    WindowID_HealthBar = 0x1E
    WindowID_TargetDisplay = 0x1F
    WindowID_TradeButton = 0x21
    WindowID_WeaponBar = 0x22

    WindowID_Hero1 = 0x33
    WindowID_Hero2 = 0x34
    WindowID_Hero3 = 0x35
    WindowID_Hero = 0x36

    WindowID_SkillsAndAttributes = 0x38
    WindowID_Friends = 0x3A
    WindowID_Guild = 0x3B
    WindowID_Help = 0x3D
    WindowID_Inventory = 0x3E
    WindowID_VaultBox = 0x3F
    WindowID_InventoryBags = 0x40
    WindowID_MissionMap = 0x42
    WindowID_Observe = 0x44
    WindowID_Options = 0x45
    WindowID_PartyWindow = 0x48  # state flag ignored, position is valid
    WindowID_PartySearch = 0x49
    WindowID_QuestLog = 0x4F
    WindowID_Merchant = 0x5C
    WindowID_Hero4 = 0x5E
    WindowID_Hero5 = 0x5F
    WindowID_Hero6 = 0x60
    WindowID_Hero7 = 0x61

    WindowID_Count = 0x66  # Used for bounds checking


class ControlAction(IntEnum):
    ControlAction_None = 0x00
    ControlAction_Screenshot = 0xAE

    # Panels
    ControlAction_CloseAllPanels = 0x85
    ControlAction_ToggleInventoryWindow = 0x8B
    ControlAction_OpenScoreChart = 0xBD
    ControlAction_OpenTemplateManager = 0xD3
    ControlAction_OpenSaveEquipmentTemplate = 0xD4
    ControlAction_OpenSaveSkillTemplate = 0xD5
    ControlAction_OpenParty = 0xBF
    ControlAction_OpenGuild = 0xBA
    ControlAction_OpenFriends = 0xB9
    ControlAction_ToggleAllBags = 0xB8
    ControlAction_OpenMissionMap = 0xB6
    ControlAction_OpenBag2 = 0xB5
    ControlAction_OpenBag1 = 0xB4
    ControlAction_OpenBelt = 0xB3
    ControlAction_OpenBackpack = 0xB2
    ControlAction_OpenSkillsAndAttributes = 0x8F
    ControlAction_OpenQuestLog = 0x8E
    ControlAction_OpenWorldMap = 0x8C
    ControlAction_OpenHero = 0x8A
    # Weapon sets
    ControlAction_CycleEquipment = 0x86
    ControlAction_ActivateWeaponSet1 = 0x81
    ControlAction_ActivateWeaponSet2 = 0x82
    ControlAction_ActivateWeaponSet3 = 0x83
    ControlAction_ActivateWeaponSet4 = 0x84

    ControlAction_DropItem = 0xCD  # drops bundle item >> flags, ashes, etc
    # Chat
    ControlAction_CharReply = 0xBE
    ControlAction_OpenChat = 0xA1
    ControlAction_OpenAlliance = 0x88

    ControlAction_ReverseCamera = 0x90
    ControlAction_StrafeLeft = 0x91
    ControlAction_StrafeRight = 0x92
    ControlAction_TurnLeft = 0xA2
    ControlAction_TurnRight = 0xA3
    ControlAction_MoveBackward = 0xAC
    ControlAction_MoveForward = 0xAD
    ControlAction_CancelAction = 0xAF
    ControlAction_Interact = 0x80
    ControlAction_ReverseDirection = 0xB1
    ControlAction_Autorun = 0xB7
    ControlAction_Follow = 0xCC
    # Targeting
    ControlAction_TargetPartyMember1 = 0x96
    ControlAction_TargetPartyMember2 = 0x97
    ControlAction_TargetPartyMember3 = 0x98
    ControlAction_TargetPartyMember4 = 0x99
    ControlAction_TargetPartyMember5 = 0x9A
    ControlAction_TargetPartyMember6 = 0x9B
    ControlAction_TargetPartyMember7 = 0x9C
    ControlAction_TargetPartyMember8 = 0x9D
    ControlAction_TargetPartyMember9 = 0xC6
    ControlAction_TargetPartyMember10 = 0xC7
    ControlAction_TargetPartyMember11 = 0xC8
    ControlAction_TargetPartyMember12 = 0xC9

    ControlAction_TargetNearestItem = 0xC3
    ControlAction_TargetNextItem = 0xC4
    ControlAction_TargetPreviousItem = 0xC5
    ControlAction_TargetPartyMemberNext = 0xCA
    ControlAction_TargetPartyMemberPrevious = 0xCB
    ControlAction_TargetAllyNearest = 0xBC
    ControlAction_ClearTarget = 0xE3
    ControlAction_TargetSelf = 0xA0  # also overlaps with 0x96
    ControlAction_TargetPriorityTarget = 0x9F
    ControlAction_TargetNearestEnemy = 0x93
    ControlAction_TargetNextEnemy = 0x95
    ControlAction_TargetPreviousEnemy = 0x9E

    ControlAction_ShowOthers = 0x89
    ControlAction_ShowTargets = 0x94

    ControlAction_CameraZoomIn = 0xCE
    ControlAction_CameraZoomOut = 0xCF
    # Party / Hero commands
    ControlAction_ClearPartyCommands = 0xDB
    ControlAction_CommandParty = 0xD6
    ControlAction_CommandHero1 = 0xD7
    ControlAction_CommandHero2 = 0xD8
    ControlAction_CommandHero3 = 0xD9
    ControlAction_CommandHero4 = 0x102
    ControlAction_CommandHero5 = 0x103
    ControlAction_CommandHero6 = 0x104
    ControlAction_CommandHero7 = 0x105

    ControlAction_OpenHero1PetCommander = 0xE0
    ControlAction_OpenHero2PetCommander = 0xE1
    ControlAction_OpenHero3PetCommander = 0xE2
    ControlAction_OpenHero4PetCommander = 0xFE
    ControlAction_OpenHero5PetCommander = 0xFF
    ControlAction_OpenHero6PetCommander = 0x100
    ControlAction_OpenHero7PetCommander = 0x101

    ControlAction_OpenHeroCommander1 = 0xDC
    ControlAction_OpenHeroCommander2 = 0xDD
    ControlAction_OpenHeroCommander3 = 0xDE
    ControlAction_OpenHeroCommander4 = 0x126
    ControlAction_OpenHeroCommander5 = 0x127
    ControlAction_OpenHeroCommander6 = 0x128
    ControlAction_OpenHeroCommander7 = 0x129
    
    ControlAction_Hero1Skill1 = 0xE5
    ControlAction_Hero1Skill2 = 0xE6
    ControlAction_Hero1Skill3 = 0xE7
    ControlAction_Hero1Skill4 = 0xE8
    ControlAction_Hero1Skill5 = 0xE9
    ControlAction_Hero1Skill6 = 0xEA
    ControlAction_Hero1Skill7 = 0xEB
    ControlAction_Hero1Skill8 = 0xEC

    ControlAction_Hero2Skill1 = 0xED
    ControlAction_Hero2Skill2 = 0xEE
    ControlAction_Hero2Skill3 = 0xEF
    ControlAction_Hero2Skill4 = 0xF0
    ControlAction_Hero2Skill5 = 0xF1
    ControlAction_Hero2Skill6 = 0xF2
    ControlAction_Hero2Skill7 = 0xF3
    ControlAction_Hero2Skill8 = 0xF4

    ControlAction_Hero3Skill1 = 0xF5
    ControlAction_Hero3Skill2 = 0xF6
    ControlAction_Hero3Skill3 = 0xF7
    ControlAction_Hero3Skill4 = 0xF8
    ControlAction_Hero3Skill5 = 0xF9
    ControlAction_Hero3Skill6 = 0xFA
    ControlAction_Hero3Skill7 = 0xFB
    ControlAction_Hero3Skill8 = 0xFC

    ControlAction_Hero4Skill1 = 0x106
    ControlAction_Hero4Skill2 = 0x107
    ControlAction_Hero4Skill3 = 0x108
    ControlAction_Hero4Skill4 = 0x109
    ControlAction_Hero4Skill5 = 0x10A
    ControlAction_Hero4Skill6 = 0x10B
    ControlAction_Hero4Skill7 = 0x10C
    ControlAction_Hero4Skill8 = 0x10D

    ControlAction_Hero5Skill1 = 0x10E
    ControlAction_Hero5Skill2 = 0x10F
    ControlAction_Hero5Skill3 = 0x110
    ControlAction_Hero5Skill4 = 0x111
    ControlAction_Hero5Skill5 = 0x112
    ControlAction_Hero5Skill6 = 0x113
    ControlAction_Hero5Skill7 = 0x114
    ControlAction_Hero5Skill8 = 0x115

    ControlAction_Hero6Skill1 = 0x116
    ControlAction_Hero6Skill2 = 0x117
    ControlAction_Hero6Skill3 = 0x118
    ControlAction_Hero6Skill4 = 0x119
    ControlAction_Hero6Skill5 = 0x11A
    ControlAction_Hero6Skill6 = 0x11B
    ControlAction_Hero6Skill7 = 0x11C
    ControlAction_Hero6Skill8 = 0x11D

    ControlAction_Hero7Skill1 = 0x11E
    ControlAction_Hero7Skill2 = 0x11F
    ControlAction_Hero7Skill3 = 0x120
    ControlAction_Hero7Skill4 = 0x121
    ControlAction_Hero7Skill5 = 0x122
    ControlAction_Hero7Skill6 = 0x123
    ControlAction_Hero7Skill7 = 0x124
    ControlAction_Hero7Skill8 = 0x125
    # Skills
    ControlAction_UseSkill1 = 0xA4
    ControlAction_UseSkill2 = 0xA5
    ControlAction_UseSkill3 = 0xA6
    ControlAction_UseSkill4 = 0xA7
    ControlAction_UseSkill5 = 0xA8
    ControlAction_UseSkill6 = 0xA9
    ControlAction_UseSkill7 = 0xAA
    ControlAction_UseSkill8 = 0xAB
    
#end region
#region Titles
class TitleID(IntEnum):
    Hero = 0
    TyrianCarto = 1
    CanthanCarto = 2
    Gladiator = 3
    Champion = 4
    Kurzick = 5
    Luxon = 6
    Drunkard = 7
    Deprecated_SkillHunter = 8  # Pre hard mode update version
    Survivor = 9
    KoaBD = 10
    Deprecated_TreasureHunter = 11  # Old title, non-account bound
    Deprecated_Wisdom = 12  # Old title, non-account bound
    ProtectorTyria = 13
    ProtectorCantha = 14
    Lucky = 15
    Unlucky = 16
    Sunspear = 17
    ElonianCarto = 18
    ProtectorElona = 19
    Lightbringer = 20
    LDoA = 21
    Commander = 22
    Gamer = 23
    SkillHunterTyria = 24
    VanquisherTyria = 25
    SkillHunterCantha = 26
    VanquisherCantha = 27
    SkillHunterElona = 28
    VanquisherElona = 29
    LegendaryCarto = 30
    LegendaryGuardian = 31
    LegendarySkillHunter = 32
    LegendaryVanquisher = 33
    Sweets = 34
    GuardianTyria = 35
    GuardianCantha = 36
    GuardianElona = 37
    Asuran = 38
    Deldrimor = 39
    Vanguard = 40
    Norn = 41
    MasterOfTheNorth = 42
    Party = 43
    Zaishen = 44
    TreasureHunter = 45
    Wisdom = 46
    Codex = 47
    None_ = 0xff  # Use 'None_' to avoid using the reserved keyword 'None'

TITLE_NAME = {
    TitleID.Hero: "Hero",
    TitleID.TyrianCarto: "Tyrian Cartographer",
    TitleID.CanthanCarto: "Canthan Cartographer",
    TitleID.Gladiator: "Gladiator",
    TitleID.Champion: "Champion",
    TitleID.Kurzick: "Kurzick",
    TitleID.Luxon: "Luxon",
    TitleID.Drunkard: "Drunkard",
    TitleID.Deprecated_SkillHunter: "Skill Hunter",  # Pre hard mode update version
    TitleID.Survivor: "Survivor",
    TitleID.KoaBD: "Kind Of A Big Deal",
    TitleID.Deprecated_TreasureHunter: "Treasure Hunter",  # Old title, non-account bound
    TitleID.Deprecated_Wisdom: "Wisdom",  # Old title, non-account bound
    TitleID.ProtectorTyria: "Protector of Tyria",
    TitleID.ProtectorCantha: "Protector of Cantha",
    TitleID.Lucky: "Lucky",
    TitleID.Unlucky: "Unlucky",
    TitleID.Sunspear: "Sunspear",
    TitleID.ElonianCarto: "Elonian Cartographer",
    TitleID.ProtectorElona: "Protector of Elona",
    TitleID.Lightbringer: "Lightbringer",
    TitleID.LDoA: "Legendary Defender of Ascalon",
    TitleID.Commander: "Commander",
    TitleID.Gamer: "Gamer",
    TitleID.SkillHunterTyria: "Tyrian Skill Hunter",
    TitleID.VanquisherTyria: "Tyrian Vanquisher",
    TitleID.SkillHunterCantha: "Canthan Skill Hunter",
    TitleID.VanquisherCantha: "Canthan Vanquisher",
    TitleID.SkillHunterElona: "Elonian Skill Hunter",
    TitleID.VanquisherElona: "Elonian Vanquisher",
    TitleID.LegendaryCarto: "Legendary Cartographer",
    TitleID.LegendaryGuardian: "Legendary Guardian",
    TitleID.LegendarySkillHunter: "Legendary Skill Hunter",
    TitleID.LegendaryVanquisher: "Legendary Vanquisher",
    TitleID.Sweets: "Sweet Tooth",
    TitleID.GuardianTyria: "Tyrian Guardian",
    TitleID.GuardianCantha: "Canthan Guardian",
    TitleID.GuardianElona: "Elonian Guardian",
    TitleID.Asuran: "Asuran",
    TitleID.Deldrimor: "Deldrimor",
    TitleID.Vanguard: "Vanguard",
    TitleID.Norn: "Norn",
    TitleID.MasterOfTheNorth: "Master of the North",
    TitleID.Party: "Party Animal",
    TitleID.Zaishen: "Zaishen",
    TitleID.TreasureHunter: "Treasure Hunter",
    TitleID.Wisdom: "Wisdom",
    TitleID.Codex: "Codex",
    TitleID.None_: "None",  # Use 'None_' to avoid Python reserved keyword
}

#endregion
#region Outpost Names

outposts = {
    4: "Guild Hall - Warrior's Isle",
    5: "Guild Hall - Hunter's Isle",
    6: "Guild Hall - Wizard's Isle",
    10: "Bloodstone Fen outpost",
    11: "The Wilds outpost",
    12: "Aurora Glade outpost",
    14: "Gates of Kryta outpost",
    15: "D'Alessio Seaboard outpost",
    16: "Divinity Coast outpost",
    19: "Sanctum Cay outpost",
    20: "Droknar's Forge",
    21: "The Frost Gate outpost",
    22: "Ice Caves of Sorrow outpost",
    23: "Thunderhead Keep outpost",
    24: "Iron Mines of Moladune outpost",
    25: "Borlis Pass outpost",
    28: "The Great Northern Wall outpost",
    29: "Fort Ranik outpost",
    30: "Ruins of Surmia outpost",
    32: "Nolani Academy outpost",
    35: "Ember Light Camp",
    36: "Grendich Courthouse",
    37: "Glint' Challenge",
    38: "Augury Rock outpost",
    39: "Sardelac Sanitarium",
    40: "Piken Square",
    49: "Henge of Denravi",
    51: "Senjis Corner",
    52: "Guild Hall - Burning Isle",
    55: "Lions Arch",
    57: "Bergen Hot Springs",
    65: "D'Alessio Arena",
    73: "Riverside Province outpost",
    75: "The Hall of Heroes Arena",
    76: "Broken Tower Arena",
    77: "House zu Heltzer",
    78: "The Courtyard Arena",
    79: "Unholy Temples Area",
    80: "Burial Mounds Arena",
    81: "Ascalon City",
    82: "Tomb of the Primeval Kings",
    83: "The Vault Arena",
    84: "The Underworld Arena",
    85: "Ascalon Arena outpost",
    86: "Sacred Temples Arena",
    109: "The Amnoon Oasis",
    116: "Dunes of Despair outpost",
    117: "Thirsty River outpost",
    118: "Elona Reach outpost",
    119: "Augury Rock outpost",
    120: "The Dragon's Lair outpost",
    122: "Ring of Fire outpost",
    123: "Abaddon's Mouth outpost",
    124: "Hell's Precipice outpost",
    126: "Golden Gates",
    129: "Lutgardis Conservatory",
    130: "Vasburg Armory",
    131: "Serenity Temple",
    132: "Ice Tooth Cave",
    133: "Beacons Perch",
    134: "Yaks Bend",
    135: "Frontier Gate",
    136: "Beetletun",
    137: "Fishermens Haven",
    138: "Temple of the Ages",
    139: "Ventaris Refuge",
    140: "Druids Overlook",
    141: "Maguuma Stade",
    142: "Quarrel Falls",
    150: "Ascalon Academy PvP battle",
    152: "Heroes Audience",
    153: "Seekers Passage",
    154: "Destinys Gorge",
    155: "Camp Rankor",
    156: "The Granite Citadel",
    157: "Marhans Grotto",
    158: "Port Sledge",
    159: "Copperhammer Mines",
    163: "Pre-Searing: The Barradin Estate",
    164: "Pre-Searing: Ashford Abbey",
    165: "Pre-Searing: Foibles Fair",
    166: "Pre-Searing: Fort Ranik",
    176: "Guild Hall - Frozen Isle",
    177: "Guild Hall - Nomad's Isle",
    178: "Guild Hall - Druid's Isle",
    179: "Guild Hall - Isle of the Dead",
    180: "Fort Koga",
    181: "Shiverpeak Arena outpost",
    182: "Amnoon Arena",
    183: "Deldrimor Arena",
    184: "The Crag",
    188: "Random Arenas outpost",
    189: "Team Arenas outpost",
    193: "Cavalon",
    194: "Kaineng Center",
    204: "Unwaking Waters - Kurzick",
    206: "Deldrimor War Camp",
    208: "Heroes' Crypt",
    213: "Zen Daijun outpost",
    214: "Minister Chos Estate outpost",
    215: "Vizunah Square",
    216: "Nahpui Quarter outpost",
    217: "Tahnnakai Temple outpost",
    218: "Arborstone outpost",
    219: "Boreas Seabed outpost",
    220: "Sunjiang District outpost",
    221: "Fort Aspenwood",
    222: "The Eternal Grove outpost",
    223: "The Jade Quarry",
    224: "Gyala Hatchery outpost",
    225: "Raisu Palace outpost",
    226: "Imperial Sanctum outpost",
    228: "Grenz Frontier",
    230: "Amatz Basin outpost",
    234: "The Aurios Mines outpost",
    242: "Shing Jea Monastery",
    243: "Shing Jea Arena outpost",
    248: "Great Temple of Balthazar",
    249: "Tsumei Village",
    250: "Seitung Harbor",
    251: "Ran Musu Gardens",
    253: "Dwayna Vs Grenth outpost",
    266: "Urgoz's Warren outpost",
    272: "Altrumm Ruins outpost",
    273: "Zos Shivros Channel outpost",
    274: "Dragons Throat outpost",
    275: "Guild Hall - Isle of Weeping Stone",
    276: "Guild Hall - Isle of Jade",
    277: "Harvest Temple",
    278: "Breaker Hollow",
    279: "Leviathan Pits",
    281: "Zaishen Challenge outpost",
    282: "Zaishen Elite outpost",
    283: "Maatu Keep",
    284: "Zin Ku Corridor",
    286: "Brauer Academy",
    287: "Durheim Archives",
    288: "Bai Paasu Reach",
    289: "Seafarer's Rest",
    291: "Vizunah Square Local Quarter",
    292: "Vizunah Square Foreign Quarter",
    293: "Fort Aspenwood - Luxon",
    294: "Fort Aspenwood - Kurzick",
    295: "The Jade Quarry - Luxon",
    296: "The Jade Quarry - Kurzick",
    297: "Unwaking Waters Luxon",
    298: "Unwaking Waters Kurzick",
    300: "Etnaran Keys",
    303: "The Marketplace",
    307: "The Deep outpost",
    308: "Ascalon Arena",
    309: "Annihilation",
    310: "Kill Count Training",
    311: "Annihilation",
    312: "Obelisk Annihilation Training",
    314: "Shiverpeak Arena",
    318: "D'Alessio Arena",
    319: "Amnoon Arena",
    320: "Fort Koga",
    321: "Heroes' Crypt",
    322: "Shiverpeak Arena",
    328: "Saltspray Beach - Luxon",
    329: "Saltspray Beach - Kurzick",
    330: "Heroes Ascent outpost",
    331: "Grenz Frontier - Luxon",
    332: "Grenz Frontier - Kurzick",
    333: "The Ancestral Lands - Luxon",
    334: "The Ancestral Lands - Kurzick",
    335: "Etnaran Keys - Luxon",
    336: "Etnaran Keys - Kurzick",
    337: "Kaanai Canyon - Luxon",
    338: "Kaanai Canyon - Kurzick",
    339: "D'Alessio Arena",
    340: "Amnoon Arena",
    341: "Fort Koga",
    342: "Heroes' Crypt",
    343: "Shiverpeak Arena",
    348: "Tanglewood Copse",
    349: "Saint Anjeka's Shrine",
    350: "Eredon Terrace",
    352: "Brawler's Pit",
    353: "Petrified Arena",
    354: "Seabed Arena",
    359: "Guild Hall - Imperial Isle",
    360: "Guild Hall - Isle of Meditation",
    368: "Dragon Arena outpost",
    376: "Camp Hojanu",
    378: "Wehhan Terraces",
    381: "Yohlon Haven",
    387: "Sunspear Sanctuary",
    388: "Aspenwood Gate - Kurzick",
    389: "Aspenwood Gate - Luxon",
    390: "Jade Flats Kurzick",
    391: "Jade Flats Luxon",
    393: "Chantry of Secrets",
    396: "Mihanu Township",
    398: "Basalt Grotto",
    403: "Honur Hill",
    407: "Yahnur Market",
    414: "The Kodash Bazaar",
    421: "Venta Cemetery outpost",
    424: "Kodonur Crossroads outpost",
    425: "Rilohn Refuge outpost",
    426: "Pogahn Passage outpost",
    427: "Moddok Crevice outpost",
    428: "Tihark Orchard outpost",
    431: "Sunspear Great Hall",
    433: "Dzagonur Bastion outpost",
    434: "Dasha Vestibule outpost",
    435: "Grand Court of Sebelkeh outpost",
    438: "Bone Palace",
    440: "The Mouth of Torment",
    442: "Lair of the Forgotten",
    445: "The Ebony Citadel of Mallyx",
    449: "Kamadan Jewel of Istan",
    450: "Gate of Torment",
    457: "Beknur Harbor",
    467: "Rollerbeetle Racing outpost",
    469: "Gate of Fear",
    473: "Gate of Secrets",
    476: "Jennurs Horde outpost",
    477: "Nundu Bay outpost",
    478: "Gate of Desolation outpost",
    479: "Champions Dawn",
    480: "Ruins of Morah outpost",
    487: "Beknur Harbor",
    489: "Kodlonu Hamlet",
    491: "Jokanur Diggings outpost",
    492: "Blacktide Den outpost",
    493: "Consulate Docks outpost",
    494: "Gate of Pain outpost",
    495: "Gate of Madness outpost",
    496: "Abaddons Gate outpost",
    497: "Sunspear Arena outpost",
    502: "The Astralarium",
    504: "Churranu Island Arena",
    529: "Guild Hall - Uncharted Isle",
    530: "Guild Hall - Isle of Wurms",
    536: "Sunspear Arena",
    537: "Guild Hall - Corrupted Isle",
    538: "Guild Hall - Isle of Solitude",
    544: "Chahbek Village outpost",
    545: "Remains of Sahlahja outpost",
    549: "Hero Battles outpost",
    554: "Dajkah Inlet outpost",
    555: "The Shadow Nexus outpost",
    559: "Gate of the Nightfallen Lands",
    624: "Vlox's Falls",
    638: "Gadd's Encampment",
    639: "Umbral Grotto",
    640: "Rata Sum",
    641: "Tarnished Haven",
    642: "Eye of the North outpost",
    643: "Sifhalla",
    644: "Gunnar's Hold",
    645: "Olafstead",
    648: "Doomlore Shrine",
    650: "Longeyes Ledge",
    652: "Central Transfer Chamber",
    675: "Boreal Station",
    721: "Costume Brawl outpost",
    795: "Zaishen Menagerie outpost",
    796: "Codex Arena outpost",
    808: "Lions Arch - Halloween",
    809: "Lions Arch - Wintersday",
    810: "Lions Arch - Canthan New Year",
    811: "Ascalon City - Wintersday",
    812: "Droknars Forge - Halloween",
    813: "Droknars Forge - Wintersday",
    814: "Tomb of the Primeval Kings - Halloween",
    815: "Shing Jea Monastery - Dragon Festival",
    816: "Shing Jea Monastery - Canthan New Year",
    817: "Kaineng Center",
    818: "Kamadan Jewel of Istan - Halloween",
    819: "Kamadan Jewel of Istan - Wintersday",
    820: "Kamadan Jewel of Istan - Canthan New Year",
    821: "Eye of the North outpost - Wintersday",
    857: "Embark Beach",
 }

outpost_name_to_id = {name: id for id, name in outposts.items()}

#endregion
#region Explorable Names
explorables = {
    7: "Warrior's Isle",
    8: "Hunter's Isle",
    9: "Wizard's Isle",
    13: "Diessa Lowlands",
    17: "Talmark Wilderness",
    18: "The Black Curtain",
    26: "Talus Chute",
    27: "Griffon's Mouth",
    31: "Xaquang Skyway",
    33: "Old Ascalon",
    34: "The Fissure of Woe",
    41: "Sage Lands",
    42: "Mamnoon Lagoon",
    43: "Silverwood",
    44: "Ettin's Back",
    45: "Reed Bog",
    46: "The Falls",
    47: "Dry Top",
    48: "Tangle Root",
    53: "Tears of the Fallen",
    54: "Scoundrel's Rise",
    56: "Cursed Lands",
    58: "North Kryta Province",
    59: "Nebo Terrace",
    60: "Majesty's Rest",
    61: "Twin Serpent Lakes",
    62: "Watchtower Coast",
    63: "Stingray Strand",
    64: "Kessex Peak",
    67: "Burning Isle",
    68: "Frozen Isle",
    69: "Nomad's Isle",
    70: "Druid's Isle",
    71: "Isle of the Dead (guild hall)",
    72: "The Underworld",
    87: "Icedome",
    88: "Iron Horse Mine",
    89: "Anvil Rock",
    90: "Lornar's Pass",
    91: "Snake Dance",
    92: "Tasca's Demise",
    93: "Spearhead Peak",
    94: "Ice Floe",
    95: "Witman's Folly",
    96: "Mineral Springs",
    97: "Dreadnought's Drift",
    98: "Frozen Forest",
    99: "Traveler's Vale",
    100: "Deldrimor Bowl",
    101: "Regent Valley",
    102: "The Breach",
    103: "Ascalon Foothills",
    104: "Pockmark Flats",
    105: "Dragon's Gullet",
    106: "Flame Temple Corridor",
    107: "Eastern Frontier",
    108: "The Scar",
    110: "Diviner's Ascent",
    111: "Vulture Drifts",
    112: "The Arid Sea",
    113: "Prophet's Path",
    114: "Salt Flats",
    115: "Skyward Reach",
    121: "Perdition Rock",
    127: "Scarred Earth",
    128: "The Eternal Grove (explorable area)",
    144: "Gyala Hatchery (explorable area)",
    145: "The Catacombs",
    146: "Lakeside County",
    147: "The Northlands",
    148: "Ascalon City (pre-Searing)",
    149: "Ascalon Academy",
    151: "Ascalon Academy",
    160: "Green Hills County",
    161: "Wizard's Folly",
    162: "Regent Valley (pre-Searing)",
    167: "Burning Isle",
    168: "Druid's Isle",
    170: "Frozen Isle",
    171: "Warrior's Isle",
    172: "Hunter's Isle",
    173: "Wizard's Isle",
    174: "Nomad's Isle",
    175: "Isle of the Dead",
    190: "Sorrow's Furnace",
    191: "Grenth's Footprint",
    195: "Drazach Thicket",
    196: "Jaya Bluffs",
    197: "Shenzun Tunnels",
    198: "Archipelagos",
    199: "Maishang Hills",
    200: "Mount Qinkai",
    201: "Melandru's Hope",
    202: "Rhea's Crater",
    203: "Silent Surf",
    205: "Morostav Trail",
    209: "Mourning Veil Falls",
    210: "Ferndale",
    211: "Pongmei Valley",
    212: "Monastery Overlook",
    227: "Unwaking Waters (explorable area)",
    232: "Shadow's Passage",
    233: "Raisu Palace (explorable area)",
    235: "Panjiang Peninsula",
    236: "Kinya Province",
    237: "Haiju Lagoon",
    238: "Sunqua Vale",
    239: "Wajjun Bazaar",
    240: "Bukdek Byway",
    241: "The Undercity",
    244: "Arborstone (explorable area)",
    245: "Minister Cho's Estate (explorable area)",
    246: "Zen Daijun (explorable area)",
    247: "Boreas Seabed (explorable area)",
    252: "Linnok Courtyard",
    256: "Sunjiang District (explorable area)",
    265: "Nahpui Quarter (explorable area)",
    269: "Tahnnakai Temple (explorable area)",
    280: "Isle of the Nameless",
    285: "Monastery Overlook",
    290: "Bejunkan Pier",
    301: "Raisu Pavilion",
    302: "Kaineng Docks",
    313: "Saoshang Trail",
    344: "The Hall of Heroes",
    345: "The Courtyard",
    346: "Scarred Earth",
    347: "The Underworld (explorable area)",
    351: "Divine Path",
    361: "Isle of Weeping Stone",
    362: "Isle of Jade",
    363: "Imperial Isle",
    364: "Isle of Meditation",
    369: "Jahai Bluffs",
    371: "Marga Coast",
    373: "Sunward Marches",
    375: "Barbarous Shore",
    377: "Badhok Caverns",
    379: "Dejarin Estate",
    380: "Arkjok Ward",
    382: "Gandara, the Moon Fortress",
    384: "The Floodplain of Mahnkelon",
    385: "Lion's Arch (Sunspears in Kryta)",
    386: "Turai's Procession",
    392: "Yatendi Canyons",
    394: "Garden of Seborhin",
    395: "Holdings of Chokhin",
    397: "Vehjin Mines",
    399: "Forum Highlands",
    400: "Kaineng Center (Sunspears in Cantha)",
    402: "Resplendent Makuun",
    404: "Wilderness of Bahdza",
    406: "Vehtendi Valley",
    413: "The Hidden City of Ahdashim",
    415: "Lion's Gate",
    419: "The Mirror of Lyss",
    420: "Secure the Refuge",
    422: "Bad Tide Rising#NPCs - Kamadan, Jewel of Istan (explorable area)",
    423: "The Tribunal",
    429: "Consulate",
    430: "Plains of Jarin",
    432: "Cliffs of Dohjok",
    436: "Command Post",
    437: "Joko's Domain",
    439: "The Ruptured Heart",
    441: "The Shattered Ravines",
    443: "Poisoned Outcrops",
    444: "The Sulfurous Wastes",
    446: "The Alkali Pan",
    447: "A Land of Heroes",
    448: "Crystal Overlook",
    455: "Nightfallen Garden",
    456: "Churrhir Fields",
    461: "The Underworld",
    462: "Heart of Abaddon",
    463: "The Underworld",
    465: "Nightfallen Jahai",
    466: "Depths of Madness",
    468: "Domain of Fear",
    470: "Domain of Pain",
    471: "Bloodstone Fen (explorable area)",
    472: "Domain of Secrets",
    474: "Domain of Anguish",
    481: "Fahranur, The First City",
    482: "Bjora Marches",
    483: "Zehlon Reach",
    484: "Lahtenda Bog",
    485: "Arbor Bay",
    486: "Issnur Isles",
    488: "Mehtani Keys",
    490: "Island of Shehkah",
    499: "Ice Cliff Chasms",
    500: "Bokka Amphitheatre",
    501: "Riven Earth",
    503: "Throne of Secrets",
    505: "Shing Jea Monastery (mission)",
    506: "Haiju Lagoon (mission)",
    507: "Jaya Bluffs (mission)",
    508: "Seitung Harbor (mission)",
    509: "Tsumei Village (mission)",
    510: "Seitung Harbor (mission 2)",
    511: "Tsumei Village (mission 2)",
    513: "Drakkar Lake",
    531: "Uncharted Isle",
    532: "Isle of Wurms",
    539: "Corrupted Isle",
    540: "Isle of Solitude",
    543: "Sun Docks",
    546: "Jaga Moraine",
    547: "Bombardment",
    548: "Norrhart Domains",
    550: "The Beachhead",
    551: "The Crossing",
    552: "Desert Sands",
    553: "Varajar Fells",
    558: "Sparkfly Swamp",
    560: "Cathedral of Flames (level 1)",
    561: "The Troubled Keeper",
    566: "Verdant Cascades",
    567: "Cathedral of Flames (level 2)",
    568: "Cathedral of Flames (level 3)",
    569: "Magus Stones",
    570: "Catacombs of Kathandrax (level 1)",
    571: "Catacombs of Kathandrax (level 2)",
    572: "Alcazia Tangle",
    573: "Rragar's Menagerie (level 1)",
    574: "Rragar's Menagerie (level 2)",
    575: "Rragar's Menagerie (level 3)",
    576: "Ooza Pit",
    577: "Slaver's Exile",
    578: "Oola's Lab (level 1)",
    579: "Oola's Lab (level 2)",
    580: "Oola's Lab (level 3)",
    581: "Shards of Oor (level 1)",
    582: "Shards of Oor (level 2)",
    583: "Shards of Oor (level 3)",
    584: "Arachni's Haunt",
    585: "Arachni's Haunt",
    593: "Fetid River",
    596: "Forgotten Shrines",
    598: "Antechamber",
    604: "Vloxen Excavations (level 1)",
    605: "Vloxen Excavations (level 2)",
    606: "Vloxen Excavations (level 3)",
    607: "Heart of the Shiverpeaks (level 1)",
    608: "Heart of the Shiverpeaks (level 2)",
    609: "Heart of the Shiverpeaks (level 3)",
    612: "Bloodstone Caves (level 1)",
    613: "Bloodstone Caves (level 2)",
    614: "Bloodstone Caves (level 3)",
    615: "Bogroot Growths (level 1)",
    616: "Bogroot Growths (level 2)",
    617: "Raven's Point (level 1)",
    618: "Raven's Point (level 2)",
    619: "Raven's Point (level 3)",
    620: "Slaver's Exile (level 1)",
    621: "Slaver's Exile (level 2)",
    622: "Slaver's Exile (level 3)",
    623: "Slaver's Exile (level 4)",
    625: "Battledepths",
    628: "Sepulchre of Dragrimmar (level 1)",
    629: "Sepulchre of Dragrimmar (level 2)",
    630: "Frostmaw's Burrows (level 1)",
    631: "Frostmaw's Burrows (level 2)",
    632: "Frostmaw's Burrows (level 3)",
    633: "Frostmaw's Burrows (level 4)",
    634: "Frostmaw's Burrows (level 5)",
    635: "Darkrime Delves (level 1)",
    636: "Darkrime Delves (level 2)",
    637: "Darkrime Delves (level 3)",
    646: "Hall of Monuments",
    647: "Dalada Uplands",
    649: "Grothmar Wardowns",
    651: "Sacnoth Valley",
    653: "Curse of the Nornbear",
    654: "Blood Washes Blood",
    655: "A Gate Too Far (level 1)",
    656: "A Gate Too Far (level 2)",
    657: "A Gate Too Far (level 3)",
    658: "The Elusive Golemancer (level 1)",
    659: "The Elusive Golemancer (level 2)",
    660: "The Elusive Golemancer (level 3)",
    661: "Finding the Bloodstone (level 1)",
    662: "Finding the Bloodstone (level 2)",
    663: "Finding the Bloodstone (level 3)",
    664: "Genius Operated Living Enchanted Manifestation",
    665: "Against the Charr",
    666: "Warband of Brothers (level 1)",
    667: "Warband of Brothers (level 2)",
    668: "Warband of Brothers (level 3)",
    669: "Assault on the Stronghold",
    670: "Destruction's Depths (level 1)",
    671: "Destruction's Depths (level 2)",
    672: "Destruction's Depths (level 3)",
    673: "A Time for Heroes",
    674: "Warband Training",
    676: "Catacombs of Kathandrax",
    678: "Attack of the Nornbear",
    686: "Polymock Coliseum",
    687: "Polymock Glacier",
    688: "Polymock Crossing",
    690: "Cold as Ice",
    691: "Beneath Lion's Arch",
    692: "Tunnels Below Cantha",
    693: "Caverns Below Kamadan",
    695: "Service: In Defense of the Eye",
    696: "Mano a Norn-o",
    697: "Service: Practice, Dummy",
    698: "Hero Tutorial",
    700: "The Norn Fighting Tournament",
    701: "Secret Lair of the Snowmen",
    702: "Norn Brawling Championship",
    703: "Kilroy's Punchout Training",
    704: "Fronis Irontoe's Lair",
    705: "The Justiciar's End",
    707: "The Great Norn Alemoot",
    708: "Varajar Fells",
    710: "Epilogue",
    711: "Insidious Remnants",
    717: "Attack on Jalis's Camp",
    722: "Whitefury Rapids",
    723: "Kysten Shore",
    724: "Deepway Ruins",
    725: "Plikkup Works",
    726: "Kilroy's Punchout Tournament",
    727: "Special Ops: Flame Temple Corridor",
    728: "Special Ops: Dragon's Gullet",
    729: "Special Ops: Grendich Courthouse",
    770: "The Tengu Accords",
    771: "The Battle of Jahai",
    772: "The Flight North",
    773: "The Rise of the White Mantle",
    781: "Secret Lair of the Snowmen",
    782: "Secret Lair of the Snowmen",
    783: "Droknar's Forge (explorable area)",
    788: "Deactivating R.O.X.#NPCs",
    789: "Deactivating P.O.X.",
    790: "Deactivating N.O.X.",
    791: "Secret Underground Lair",
    792: "Golem Tutorial Simulation",
    793: "Snowball Dominance",
    794: "Zaishen Menagerie Grounds",
    806: "The Underworld (Something Wicked This Way Comes)",
    807: "The Underworld (Don't Fear the Reapers)",
    837: "Talmark Wilderness (War in Kryta)",
    838: "Trial of Zinn",
    839: "Divinity Coast (explorable area)",
    840: "Lion's Arch Keep",
    841: "D'Alessio Seaboard (explorable area)",
    842: "The Battle for Lion's Arch (explorable area)",
    843: "Riverside Province (explorable area)",
    844: "Lion's Arch (War in Kryta)",
    845: "The Mausoleum",
    846: "Rise",
    847: "Shadows in the Jungle",
    848: "A Vengeance of Blades",
    849: "Auspicious Beginnings",
    854: "Olafstead (explorable area)",
    855: "The Great Snowball Fight of the Gods (Operation: Crush Spirits)",
    856: "The Great Snowball Fight of the Gods (Fighting in a Winter Wonderland)",
    860: "What Waits in Shadow#NPCs - Dragon's Throat (explorable area)",
    861: "A Chance Encounter#NPCs - Kaineng Center (Winds of Change)",
    862: "Tracking the Corruption#NPCs - The Marketplace (explorable area)",
    863: "Cantha Courier Crisis#NPCs - Bukdek Byway (Winds of Change)",
    864: "A Treaty's a Treaty#NPCs - Tsumei Village (Winds of Change)",
    865: "Deadly Cargo#NPCs - Seitung Harbor (explorable area)",
    866: "The Rescue Attempt#NPCs - Tahnnakai Temple (Winds of Change)",
    867: "Violence in the Streets#NPCs - Wajjun Bazaar (Winds of Change)",
    868: "Scarred Psyche",
    869: "Calling All Thugs#NPCs - Shadow's Passage (Winds of Change)",
    870: "Finding Jinnai#NPCs - Altrumm Ruins",
    871: "Raid on Shing Jea Monastery#NPCs - Shing Jea Monastery",
    872: "Raid on Kaineng Center#NPCs - Kaineng Center (Winds of Change)",
    873: "Ministry of Oppression#NPCs - Wajjun Bazaar (Winds of Change)",
    874: "The Final Confrontation#NPCs - The Final Confrontation",
    875: "Lakeside County: 1070 AE",
    876: "Ashford Catacombs: 1070 AE",
}

explorable_name_to_id = {name: id for id, name in explorables.items()}

#endregion
#region ItemModels
class ModelID(IntEnum):
    Umbral_Shell = 98765432111
    Vampiric_Fang = 987654789
    Water_Djinn_Essence = 78965412365 
    Ancient_Kappa_Shell = 123654789691    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value 
    Animal_Hide = 1236547896911    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Ashen_Wurm_Husk = 123654789692    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Bleached_Shell = 123654789693    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Blood_Drinker_Pelt = 123654789694    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Bonesnap_Shell = 123654789696    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Branch_Of_Juni_Berries = 123654789695    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Bull_Trainer_Giant_Jawbone = 123654789697    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Dark_Claw = 1236547891    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Dark_Flame_Fang = 12365478911    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Dregde_Manifesto = 12365478914    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Fibrous_Mandragor_Root = 12365478917    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Fledglin_Skree_Wing = 12365478918    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Frozen_Remnant = 12365478919    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Frozen_Shell = 123654789191    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Gargantuan_Jawbone = 123654789192    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Ghostly_Remains = 123654789193    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Gold_Crimson_Skull_Coin = 123654789194    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Igneous_Spider_leg = 123654789195    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Kuskale_Claw = 123654789198    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Leather_Belt = 123456677        # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Mandragor_Carapace = 123654789181        # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Plauge_Idol = 123654789185    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Rinkhal_Talon = 123654789186    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Searing_Ribcage = 123654789187    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Searing_Burrower_Jaw = 123654789189    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Silver_Crimson_Skull_Coin = 211111356    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Smoking_Remains = 8787899465    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Spiny_Seed = 74966338    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Stolen_Supplies = 66665481    # Dummy modelid's to insure no LootManager Crash - will be changed to correct value
    Shadowy_Remnants = 441
    Ivory_Troll_Tusk = 445
    Lavastrider_Appendage = 27058
    Blessing_Of_War = 37843
    Diamond_Djinn_Essence = 19186
    Elder_Kappa_Shell = 837
    Enchanted_Vine = 834
    Diessa_Chalice = 24353
    Dregde_Charm = 27064
    Kappa_Shell = 839   
    Naga_Hide = 832
    Oni_Claw = 817
    Oni_Taloon = 831    
    Copper_Chrimson_Skull_Coin = 806
    Aatxe_Mini = 22765
    Abnormal_Seed = 442
    Abominable_Tonic = 30646
    Abomination_Mini = 32519
    Abyssal_Mini = 30610
    Abyssal_Tonic = 30624
    Aged_Dwarven_Ale = 24593
    Aged_Hunters_Ale = 31145
    Alpine_Seed = 497
    Amber_Chunk = 6532
    Amber_Summon = 30961
    Amphibian_Tongue = 27036
    Amulet_Of_The_Mists = 6069
    Ancient_Armor_Remnant = 19190
    Ancient_Artifact = 19182
    Ancient_Elonian_Key = 15556
    Ancient_Eye = 464
    Arachnis_Scythe = 26993
    Archaic_Kappa_Shell = 850
    Armbrace_Of_Truth = 21127
    Armor_Of_Salvation = 24860
    Artic_Summon = 30962
    Ascalonian_Key = 5966
    Assassin_Elitetome = 21786
    Assassin_Tome = 21796
    Asura_Mini = 22189
    Augmented_Flesh = 826
    Autmatonic_Tonic = 30634
    Automaton_Summon = 30846
    Axe_Grip = 905
    Axe_Haft = 893
    Azure_Crest = 844
    Azure_Remains = 496
    Bag = 35
    Baked_Husk = 433
    Battle_Commendation = 17081
    Battle_Isle_Iced_Tea = 36682
    Bds_Air = 1995
    Bds_Blood = 1992
    Bds_Channeling = 2007
    Bds_Communing = 2004
    Bds_Curses = 1993
    Bds_Death = 1994
    Bds_Divine = 2000
    Bds_Domination = 1987
    Bds_Earth = 1996
    Bds_Energy_Storage = 1997
    Bds_Fast_Casting = 1988
    Bds_Fire = 1998
    Bds_Healing = 2001
    Bds_Illusion = 1989
    Bds_Inspiration = 1990
    Bds_Protection = 2002
    Bds_Restoration = 2006
    Bds_Smiting = 2003
    Bds_Soul_Reaping = 1991
    Bds_Spawning = 2005
    Bds_Water = 1999
    Beetle_Egg = 27066
    Beetle_Juice_Tonic = 22192
    Behemoth_Hide = 1675
    Behemoth_Jaw = 465
    Belt_Pouch = 34
    Berserker_Horn = 27046
    Scroll_Of_Berserkers_Insight = 5595
    Birthday_Cupcake = 22269
    Birthday_Present = 37798
    Bison_Championship_Token = 27563
    Black_Beast_Of_Aaaaarrrrrrggghhh_Mini = 30611
    Black_Moa_Chick_Mini = 25499
    Black_Pearl = 841
    Bleached_Carapace = 449
    Blob_Of_Ooze = 27067
    Blue_Rock_Candy = 31151
    Bog_Skale_Fin = 443
    Bogroots_Boss_Key = 2593
    Bolt_Of_Cloth = 925
    Bolt_Of_Damask = 927
    Bolt_Of_Linen = 926
    Bolt_Of_Silk = 928
    Bone = 921
    Bone_Charm = 811
    Bone_Dragon_Mini = 13783
    Book_Of_Secrets = 19197
    Boreal_Tonic = 30638
    Bottle_Of_Grog = 30855
    Bottle_Of_Juniberry_Gin = 19172
    Bottle_Of_Rice_Wine = 15477
    Bottle_Of_Vabbian_Wine = 19173
    Bottle_Rocket = 21809
    Bow_Grip = 906
    Bow_String = 894
    Bowl_Of_Skalefin_Soup = 17061
    Brass_Knuckles = 24897
    Brood_Claws = 27982
    Brown_Rabbit_Mini = 31158
    Burning_Titan_Mini = 13793
    Burol_Ironfists_Commendation = 29018
    Candy_Apple = 28431
    Candy_Corn = 28432
    Candysmith_Marley_Mini = 34397
    Canthan_Key = 6540
    Captured_Skeleton = 32559
    Cave_Spider_Mini = 30622
    Cc_Air = 1768
    Cc_Blood = 1065
    Cc_Channeling = 1885
    Cc_Communing = 1881
    Cc_Curses = 1066
    Cc_Death = 1067
    Cc_Divine = 1773
    Cc_Domination = 1055
    Cc_Earth = 1769
    Cc_Energy_Storage = 1770
    Cc_Fast_Casting = 1058
    Cc_Fire = 1771
    Cc_Healing = 1870
    Cc_Illusion = 1060
    Cc_Inspiration = 1064
    Cc_Protection = 1879
    Cc_Restoration = 1884
    Cc_Shard = 556
    Cc_Smiting = 1880
    Cc_Soul_Reaping = 1752
    Cc_Spawning = 1883
    Cc_Water = 1772
    Celestial_Dog_Mini = 29423
    Celestial_Dragon_Mini = 29417
    Celestial_Essence = 855
    Celestial_Horse_Mini = 29419
    Celestial_Monkey_Mini = 29421
    Celestial_Ox_Mini = 29414
    Celestial_Pig_Mini = 29412
    Celestial_Rabbit_Mini = 29416
    Celestial_Rat_Mini = 29413
    Celestial_Rooster_Mini = 29422
    Celestial_Sheep_Mini = 29420
    Celestial_Sigil = 2571
    Celestial_Snake_Mini = 29418
    Celestial_Summon = 34176
    Celestial_Tiger_Mini = 29415
    Ceratadon_Mini = 28416
    Cerebral_Tonic = 30626
    Ceremonial_Daggers = 15166
    Champagne_Popper = 21810
    Champions_Zaishen_Strongbox = 36665
    Charr_Battle_Plan_Decoder = 27341
    Charr_Carving = 423
    Charr_Shaman_Mini = 13784
    Chitin_Fragment = 954
    Chitinous_Summon = 30959
    Chocolate_Bunny = 22644
    Chromatic_Scale = 27069
    Chunk_Of_Drake_Flesh = 19185
    Cloth_Of_The_Brotherhood = 27322
    Cloudtouched_Simian_Mini = 30621
    Cobalt_Scabara_Mini = 34393
    Cobalt_Talon = 1609
    Coffer_Of_Whispers = 21228
    Confessor_Dorian_Mini = 35132
    Confessor_Isaiah_Mini = 35131
    Confessors_Orders = 35123
    Copper_Shilling = 1577
    Copper_Zaishen_Coin = 31202
    Corrosive_Spider_Leg = 518
    Cottontail_Tonic = 31142
    Crate_Of_Fireworks = 29436
    Creme_Brulee = 15528
    Curved_Mintaur_Horn = 495
    Dagger_Handle = 6331
    Dagger_Tang = 6323
    Dagnar_Stonepate_Mini = 32527
    Dark_Remains = 522
    Darkstone_Key = 5963
    Decayed_Orr_Emblem = 504
    Deep_Jade_Key = 6539
    Deldrimor_Armor_Remnant = 27321
    Deldrimor_Talisman = 30693
    Deldrimor_Steel_Ingot = 950
    Delicious_Cake = 36681
    Demonic_Fang = 473
    Demonic_Key = 19174
    Demonic_Relic = 1580
    Demonic_Remains = 476
    Demonic_Summon = 30963
    Demrikovs_Judgement = 36670
    Dervish_Elitetome = 21793
    Dervish_Tome = 21803
    Desert_Griffon_Mini = 32521
    Dessicated_Hydra_Claw = 454
    Destroyer_Core = 27033
    Destroyer_Of_Flesh_Mini = 22250
    Dhuum_Mini = 32822
    Disco_Ball = 29543
    Diamond = 935
    Dragon_Mask = 15481
    Dragon_Root = 819
    Drake_Kabob = 17060
    Dredge_Brute_Mini = 32517
    Dredge_Incisor = 818
    Droknars_Key = 26724
    Dryder_Web = 27070
    Dull_Carapace = 425
    Dune_Burrower_Jaw = 447
    Dusty_Insect_Carapace = 1588
    Dwarven_Ale = 5585
    Ebon_Spider_Leg = 463
    Ecclesiate_Xun_Rao_Mini = 30225
    Eggnog = 6375
    El_Abominable_Tonic = 30647
    El_Abyssal_Tonic = 30625
    El_Acolyte_Jin_Tonic = 36428
    El_Acolyte_Sousuke_Tonic = 36429
    El_Anton_Tonic = 36447
    El_Automatonic_Tonic = 30635
    El_Avatar_Of_Balthazar_Tonic = 36658
    El_Balthazars_Champion_Tonic = 36661
    El_Boreal_Tonic = 30639
    El_Cerebral_Tonic = 30627
    El_Cottontail_Tonic = 31143
    El_Crate_Of_Fireworks = 31147
    El_Destroyer_Tonic = 36457
    El_Dunkoro_Tonic = 36426
    El_Flame_Sentinel_Tonic = 36664
    El_Gelatinous_Tonic = 30641
    El_Ghostly_Hero_Tonic = 36660
    El_Ghostly_Priest_Tonic = 36663
    El_Goren_Tonic = 36434
    El_Guild_Lord_Tonic = 36652
    El_Gwen_Tonic = 36442
    El_Hayda_Tonic = 36448
    El_Henchman_Tonic = 32850
    El_Jora_Tonic = 36455
    El_Kahmu_Tonic = 36444
    El_Keiran_Thackeray_Tonic = 36450
    El_Koss_Tonic = 36425
    El_Kuunavang_Tonic = 36461
    El_Livia_Tonic = 36449
    El_Macabre_Tonic = 30629
    El_Magrid_The_Sly_Tonic = 36432
    El_Margonite_Tonic = 36456
    El_Master_Of_Whispers_Tonic = 36433
    El_Melonni_Tonic = 36427
    El_Miku_Tonic = 36451
    El_Mischievious_Tonic = 31021
    El_Morgahn_Tonic = 36436
    El_Mox_Tonic = 36452
    El_Norgu_Tonic = 36435
    El_Ogden_Stonehealer_Tonic = 36440
    El_Olias_Tonic = 36438
    El_Phantasmal_Tonic = 30643
    El_Priest_Of_Balthazar_Tonic = 36659
    El_Prince_Rurik_Tonic = 36455
    El_Pyre_Fiercehot_Tonic = 36446
    El_Queen_Salma_Tonic = 36458
    El_Razah_Tonic = 36437
    El_Reindeer_Tonic = 34156
    El_Searing_Tonic = 30633
    El_Shiro_Tonic = 36453
    El_Sinister_Automatonic_Tonic = 30827
    El_Skeletonic_Tonic = 30637
    El_Slightly_Mad_King_Tonic = 36460
    El_Tahlkora_Tonic = 36430
    El_Transmogrifier_Tonic = 23242
    El_Trapdoor_Tonic = 30631
    El_Unseen_Tonic = 31173
    El_Vekk_Tonic = 36441
    El_Xandra_Tonic = 36443
    El_Yuletide_Tonic = 29241
    El_Zenmai_Tonic = 36439
    El_Zhed_Shadowhoof_Tonic = 36431
    Elemental_Sword = 2267
    Elementalist_Elitetome = 21789
    Elementalist_Tome = 21799
    Elf_Mini = 22756
    Elixir_Of_Valor = 21227
    Elonian_Key = 5960
    Elonian_Leather_Square = 943
    Enchanted_Lodestone = 431
    Encrusted_Lodestone = 451
    Encrypted_Charr_Battle_Plans = 27976
    Enslavement_Stone = 532
    Envoy_Scythe = 36677
    Equipment_Requisition = 5817
    Essence_Of_Celerity = 24859
    Evennia_Mini = 35128
    Everlasting_Mobstopper = 32558
    Expert_Salvage_Kit = 2991
    Eye_Of_Janthir_Mini = 32529
    Feather = 933
    Feathered_Avicara_Scalp = 498
    Feathered_Caromi_Scalp = 444
    Feathered_Crest = 835
    Feathered_Scalp = 836
    Festival_Prize = 15478
    Fetid_Carapace = 479
    Fiery_Crest = 508
    Fire_Drake_Mini = 34390
    Fire_Imp_Mini = 22764
    Flame_Djinn_Mini = 32528
    Flame_Of_Balthazar = 2514
    Flask_Of_Firewater = 2513
    Flesh_Reaver_Morsel = 27062
    Flowstone_Elemental_Mini = 32525
    Focus_Core = 15551
    Forbidden_Key = 6534
    Forest_Minotaur_Horn = 440
    Forest_Minotaur_Mini = 30615
    Forgotten_Seal = 459
    Forgotten_Trinket_Box = 825
    Fossilized_Summon = 30965
    Four_Leaf_Clover = 22191
    Freezie_Mini = 30612
    Frigid_Heart = 494
    Frigid_Mandragor_Husk = 27042
    Froggy_Air = 1963
    Froggy_Blood = 1960
    Froggy_Channeling = 1975
    Froggy_Communing = 1972
    Froggy_Curses = 1961
    Froggy_Death = 1962
    Froggy_Divine = 1968
    Froggy_Domination = 1953
    Froggy_Earth = 1964
    Froggy_Energy_Storage = 1965
    Froggy_Fast_Casting = 1956
    Froggy_Fire = 1966
    Froggy_Healing = 1969
    Froggy_Illusion = 1957
    Froggy_Inspiration = 1958
    Froggy_Protection = 1970
    Froggy_Restoration = 1974
    Froggy_Smiting = 1971
    Froggy_Soul_Reaping = 1959
    Froggy_Spawning = 1973
    Froggy_Water = 1967
    Frosted_Griffon_Wing = 493
    Frostfire_Fang = 489
    Frosty_Summon = 31023
    Frosty_Tonic = 30648
    Frozen_Wurm_Husk = 27048
    Fruitcake = 21492
    Fungal_Root = 27061
    Fungal_Wallow_Mini = 13782
    Fur_Square = 941
    Gargoyle_Skull = 426
    Gelatinous_Summon = 30964
    Gelatinous_Tonic = 30640
    Geode = 1681
    Ghastly_Summon = 32557
    Ghost_In_The_Box = 6368
    Ghostly_Priest_Mini = 36650
    Giant_Tusk = 1590
    Gift_Of_The_Huntsman = 31149
    Gift_Of_The_Traveller = 31148
    Glacial_Stone = 27047
    Gladiators_Zaishen_Strongbox = 36667
    Glob_Of_Ectoplasm = 930
    Glob_Of_Frozen_Ectoplasm = 21509
    Gloom_Seed = 523
    Glowing_Heart = 439
    Gold_Coins = 2511
    Gold_Doubloon = 1578
    Gold_Zaishen_Coin = 31203
    Golden_Egg = 22752
    Golden_Flame_Of_Balthazar = 22188
    Golden_Lantern = 4195
    Golden_Rin_Relic = 24354
    Golem_Runestone = 27065
    Grail_Of_Might = 24861
    Granite_Slab = 955
    Grawl_Mini = 22822
    Grawl_Necklace = 432
    Gray_Giant_Mini = 17053
    Green_Rock_Candy = 31152
    Gruesome_Ribcage = 482
    Gruesome_Sternum = 475
    Guardian_Moss = 849
    Guild_Lord_Mini = 36648
    Gwen_Doll_Mini = 31157
    Gwen_Mini = 22753
    Hammer_Grip = 907
    Hammer_Haft = 895
    Hard_Apple_Cider = 28435
    Hardened_Hump = 435
    Harpy_Ranger_Mini = 22761
    Heavy_Equipment_Pack = 31224
    Heket_Tongue = 19199
    Heket_Warrior_Mini = 22760
    Heleynes_Insight = 36676
    Scroll_Of_Heros_Insight = 5594
    Heros_Handbook = 26899
    Heros_Zaishen_Strongbox = 36666
    Herring_Mini_Black_Moa_Chick_Incubator = 26502
    High_Priest_Zhang_Mini = 36649
    Honeycomb = 26784
    Huge_Jawbone = 492
    Hunk_Of_Fresh_Meat = 15583
    Hunters_Ale = 910
    Scroll_Of_Hunters_Insight = 5976
    Hunting_Minotaur_Horn = 1682
    Hydra_Mini = 13787
    Iboga_Petal = 19183
    Icy_Hump = 490
    Icy_Lodestone = 424
    Identification_Kit = 2989
    Igneous_Hump = 510
    Igneous_Spider_Leg = 505
    Igneous_Summoning_Stone = 30847
    Immolated_Djinn_Essence = 1620
    Imperial_Commendation = 6068
    Imperial_Dragons_Tear = 30205
    Imperial_Guard_Lockbox = 30212
    Imperial_Guard_Requisition_Order = 29108
    Imperial_Guard_Summon = 30210
    Incubus_Wing = 27034
    Inscribed_Secret = 19196
    Inscribed_Shard = 1587
    Inscriptions_All = 15542
    Inscriptions_Focus_Items = 19123
    Inscriptions_Focus_Shield = 15541
    Inscriptions_General = 17059
    Inscriptions_Martial = 15540
    Inscriptions_Spellcasting = 19122
    Insect_Appendage = 1597
    Insect_Carapace = 1617
    Intricate_Grawl_Necklace = 499
    Iridescant_Griffon_Wing = 453
    Iron_Ingot = 948
    Irukandji_Mini = 30613
    Istani_Key = 15557
    Jade_Armor_Mini = 13788
    Jade_Bracelet = 809
    Jade_Mandible = 457
    Jade_Orb = 15940
    Jadeite_Shard = 6533
    Jadeite_Summon = 30966
    Jar_Of_Honey = 31150
    Jora_Mini = 32524
    Jotun_Pelt = 27045
    Juggernaut_Mini = 22762
    Jungle_Skale_Fin = 70
    Jungle_Troll_Mini = 13794
    Jungle_Troll_Tusk = 471
    Juvenile_Termite_Leg = 1598
    Kappa_Hatchling_Shell = 838
    Keen_Oni_Claw = 817
    Keen_Oni_Talon = 847
    Keg_Of_Aged_Hunters_Ale = 31146
    Keirans_Bow = 35829
    Kilhn_Testibries_Crest = 2115
    Kilhn_Testibries_Cuisse = 2113
    Kilhn_Testibries_Greaves = 2114
    Kilhn_Testibries_Pauldron = 2116
    King_Adelbern_Mini = 34399
    Kirin_Horn = 846
    Kirin_Mini = 13789
    Koss_Mini = 22758
    Kournan_Coin = 19195
    Kournan_Key = 15559
    Kournan_Pendant = 1582
    Krait_Neoss_Mini = 32520
    Krait_Skin = 27729
    Kraken_Eye = 843
    Krytan_Brandy = 35124
    Krytan_Key = 5964
    Krytan_Lokum = 35125
    Kurzick_Bauble = 604
    Kurzick_Key = 6535
    Kuunavang_Mini = 12389
    Kveldulf_Mini = 32522
    Large_Equipment_Pack = 31223
    Leather_Square = 942
    Leathery_Claw = 484
    Legionnaire_Summoning_Crystal = 37810
    Lich_Mini = 22755
    Light_Equipment_Pack = 31222
    Livia_Mini = 35129
    Lockpick = 22751
    Losaru_Mane = 448
    Lump_Of_Charcoal = 922
    Lunar_Fortune_2007_Pig = 29424
    Lunar_Fortune_2008_Rat = 29425
    Lunar_Fortune_2009_Ox = 29426
    Lunar_Fortune_2010_Tiger = 29427
    Lunar_Fortune_2011_Rabbit = 29428
    Lunar_Fortune_2012_Dragon = 29429
    Lunar_Fortune_2013_Snake = 29430
    Lunar_Fortune_2014_Horse = 29431
    Lunar_Fortune_2015_Sheep = 29432
    Lunar_Fortune_2016_Monkey = 29433
    Lunar_Fortune_2017_Rooster = 29434
    Lunar_Fortune_2018_Dog = 29435
    Lunar_Token = 21833
    Luxon_Key = 6538
    Luxon_Pendant = 810
    Luxon_Totem = 6048
    Macabre_Tonic =30628
    Mad_King_Thorn_Mini = 30614
    Mad_Kings_Guard_Mini = 32555
    Maguuma_Key = 5965
    Maguuma_Mane = 466
    Mahgo_Claw = 513
    Mallyx_Mini = 21229
    Mandragor_Husk = 1668
    Mandragor_Imp_Mini = 22759
    Mandragor_Root = 1686
    Mandragor_Root_Cake = 19170
    Mandragor_Swamproot = 1671
    Mantid_Pincer = 815
    Mantid_Ungula = 27054
    Mantis_Pincer = 829
    Map_Piece_Bl = 24631
    Map_Piece_Br = 24632
    Map_Piece_Tl = 24629
    Map_Piece_Tr = 24630
    Margonite_Gemstone = 21128
    Margonite_Key = 15560
    Margonite_Mask = 1581
    Massive_Jawbone = 452
    Master_Dungeon_Guide = 26603
    Master_Dungeon_Guide_Hard_Mode = 26897
    Medal_Of_Honor = 35122
    Merchant_Summon = 21154
    Mergoyle_Skull = 436
    Mesmer_Elitetome = 21787
    Mesmer_Tome = 21797
    Miners_Key = 5961
    Minister_Reiko_Mini = 30224
    Ministerial_Commendation = 36985
    Ministerial_Decree = 29109
    Minitreats_Of_Purity = 30208
    Minotaur_Horn = 455
    Minutely_Mad_King_Tonic = 37772
    Mischievious_Tonic = 31020
    Mischievous_Summon = 31022
    Modnir_Mane = 27043
    Molten_Claw = 503
    Molten_Eye = 506
    Molten_Heart = 514
    Monastery_Credit = 5819
    Monk_Elitetome = 21790
    Monk_Tome = 21800
    Monumental_Tapestry = 27583
    Monstrous_Claw = 923
    Monstrous_Eye = 931
    Monstrous_Fang = 932
    Moon_Shell = 1009
    Mossy_Mandible = 469
    Mountain_Root = 27049
    Mountain_Troll_Tusk = 500
    Mox_Mini = 34400
    Mummy_Wrapping = 1583
    Mursaat_Mini = 30616
    Mursaat_Token = 462
    Mysterious_Armor_Piece = 19192
    Mysterious_Summon = 31155
    Mysterious_Tonic = 31141
    Mystical_Summon = 30960
    Naga_Pelt = 833
    Naga_Raincaller_Mini = 15515
    Naga_Skin = 848
    Necrid_Horseman_Mini = 13786
    Necromancer_Elitetome = 21788
    Necromancer_Tome = 21798
    Nian_Mini = 32526
    Night_Falls = 28479
    Nornbear_Mini = 32519
    Oath_Of_Purity = 30206
    Obsidian_Burrower_Jaw = 472
    Obsidian_Key = 5971
    Obsidian_Shard = 945
    Oni_Mini = 15516
    Onyx_Gemstone = 936
    Oola_Mini = 34396
    Ooze_Mini = 30618
    Ophil_Nahualli_Mini = 34392
    Ornate_Grawl_Necklace = 487
    Pahnai_Salad = 17062
    Palawa_Joko_Mini = 22757
    Panda_Mini = 15517
    Paper_Wrapped_Parcel = 34212
    Paragon_Elitetome = 21795
    Paragon_Tome = 21805
    Party_Beacon = 36683
    Passage_Scroll_Deep = 22279
    Passage_Scroll_Fow = 22280
    Passage_Scroll_Urgoz = 3256
    Passage_Scroll_Uw = 3746
    Patch_Of_Simian_Fur = 27038
    Peppermint_Cc = 6370
    Perfect_Salvage_Kit = 25881
    Phantasmal_Tonic = 30642
    Phantom_Key = 5882
    Phantom_Residue = 474
    Pig_Mini = 21806
    Pile_Of_Elemental_Dust = 27050
    Pile_Of_Glittering_Dust = 929
    Plant_Fiber = 934
    Polar_Bear_Mini = 21439
    Polymock_Aloe_Seed = 24355
    Polymock_Earth_Elemental = 24357
    Polymock_Fire_Elemental = 24358
    Polymock_Fire_Imp = 24359
    Polymock_Gaki = 24360
    Polymock_Gargoyle = 24361
    Polymock_Ice_Elemental = 24365
    Polymock_Ice_Imp = 24366
    Polymock_Kappa = 24367
    Polymock_Mergoyle = 24369
    Polymock_Mirage_Iboga = 24363
    Polymock_Mursaat_Elementalist = 24370
    Polymock_Naga_Shaman = 24372
    Polymock_Ruby_Djinn = 24371
    Polymock_Skale = 24373
    Polymock_Stone_Rain = 24374
    Polymock_Wind_Rider = 24356
    Powerstone_Of_Courage = 24862
    Primeval_Armor_Remnant = 19193
    Prince_Rurik_Mini = 13790
    Princess_Salma_Mini = 35130
    Proof_Of_Legend = 37841
    Pulsating_Growth = 824
    Pumpkin_Cookie = 28433
    Putrid_Cyst = 827
    Quetzal_Crest = 27039
    Quetzal_Sly_Mini = 32523
    Rainbow_Cc = 21489
    Scroll_Of_Rampagers_Insight = 5975
    Ranger_Elitetome = 21792
    Ranger_Tome = 21802
    Raptor_Mini = 30619
    Rawhide_Belt = 483
    Red_Bean_Cake = 15479
    Red_Gift_Bag = 21811
    Red_Iris_Flower = 2994
    Red_Rock_Candy = 31153
    Refined_Jelly = 19039
    Rift_Warden_Mini = 36651
    Ritualist_Elitetome = 21794
    Ritualist_Tome = 21804
    Roaring_Ether_Claw = 1629
    Roaring_Ether_Mini = 30620
    Roll_Of_Parchment = 951
    Roll_Of_Vellum = 952
    Rot_Wallow_Tusk = 842
    Royal_Gift = 35120
    Ruby = 937
    Ruby_Djinn_Essence = 19187
    Rune_Of_Holding = 2988
    Sack_Of_Random_Junk = 34213
    Salvage_Kit = 2992
    Sandblasted_Lodestone = 1584
    Sapphire =  938
    Sapphire_Djinn_Essence = 19188
    Saurian_Bone = 27035
    Scale = 953
    Scar_Behemoth_Jaw = 478
    Scorched_Lodestone = 486
    Scorched_Seed = 485
    Scourge_Manta_Mini = 34394
    Scroll_Of_Adventurers_Insight = 5853
    Scroll_Of_Resurrection = 26501
    Scroll_Of_The_Lightbringer = 21233
    Scythe_Grip = 15553
    Scythe_Snathe = 15543
    Seal_Of_The_Dragon_Empire = 30211
    Searing_Tonic = 30632
    Seer_Mini = 34386
    Sentient_Lodestone = 1619
    Sentient_Root = 1600
    Sentient_Seed = 1601
    Sentient_Spore = 19198
    Sentient_Vine = 27041
    Shadowy_Crest = 520
    Shadowy_Husk = 526
    Shadowy_Remnant = 441
    Shamrock_Ale = 22190
    Shard_Wolf_Mini = 34389
    Shield_Handle = 15554
    Shing_Jea_Key = 6537
    Shining_Blade_Ration = 35127
    Shining_Blade_Summon = 35126
    Shiro_Mini = 13791
    Shiroken_Assassin_Mini = 22195
    Shiverpeak_Key = 5962
    Shiverpeak_Mane = 488
    Shriveled_Eye = 446
    Siege_Devourer = 34387
    Siege_Turtle_Mini = 13795
    Silver_Bullion_Coin = 1579
    Silver_Zaishen_Coin = 31204
    Singed_Gargoyle_Skull = 480
    Sinister_Automatonic_Tonic = 4730
    Skale_Claw = 1604
    Skale_Fang = 27055
    Skale_Fin = 19184
    Skale_Fin_PreSearing = 429
    Skale_Tooth = 1603
    Skeletal_Limb = 430
    Skeleton_Bone = 1605
    Skeletonic_Tonic = 30636
    Skelk_Claw = 27040
    Skelk_Fang = 27060
    Skree_Wing = 1610
    Skull_Juju = 814
    Slayers_Insight_Scroll = 5611
    Slice_Of_Pumpkin_Pie = 28436
    Small_Equipment_Pack = 31221
    Smite_Crawler_Mini = 32556
    Snowman_Summoner = 6376
    Soul_Stone = 852
    Sparkler = 21813
    Spear_Grip = 15555
    Spearhead = 15544
    Spider_Leg = 422
    Spiked_Crest = 434
    Spiked_Eggnog = 6366
    Spiritwood_Plank = 956
    Spooky_Tonic = 37771
    Squash_Serum = 6369
    Staff_Head = 896
    Staff_Wrapping = 908
    Star_Of_Transference = 25896
    Steel_Ingot = 949
    Steel_Key = 5967
    Stolen_Provisions = 851
    Stolen_Sunspear_Armor = 19191
    Stone_Carving = 820
    Stone_Claw = 27057
    Stone_Grawl_Necklace = 27053
    Stone_Horn = 816
    Stone_Summit_Badge = 502
    Stone_Summit_Emblem = 27044
    Stoneroot_Key = 6536
    Stormy_Eye = 477
    Strategists_Zaishen_Strongbox = 36668
    Stygian_Gemstone = 21129
    Sugary_Blue_Drink = 21812
    Summit_Giant_Herder = 34391
    Superior_Identification_Kit = 5899
    Superior_Salvage_Kit = 5900
    Superior_Charr_Carving = 27052
    Sword_Hilt = 897
    Sword_Pommel = 909
    Tangled_Seed = 468
    Tanned_Hide_Square = 940
    Tempered_Glass_Vial = 939
    Temple_Guardian_Mini = 13792
    Tengu_Summon = 30209
    Terrorweb_Dryder_Mini = 32518
    Thorn_Wolf_Mini = 22766
    Thorny_Carapace = 467
    Titan_Gemstone = 21130
    Topaz_Crest = 450
    Torivos_Rage = 36680
    Torment_Gemstone = 21131
    Totem_Axe = 15064
    Trick_Or_Treat_Bag = 28434
    Trade_Contract = 17082
    Transmogrifier_Tonic = 15837
    Trapdoor_Tonic = 30630
    Truffle = 813
    Umbral_Eye = 519
    Umbral_Skeletal_Limb = 525
    Unctuous_Remains = 511
    Undead_Bone = 27974
    Unnatural_Seed = 428
    Unseen_Tonic = 31172
    Vabbian_Key = 15558
    Vaettir_Essence = 27071
    Varesh_Ossa_Mini = 21069
    Venerable_Mantid_Pincer = 854
    Ventari_Mini = 34395
    Vermin_Hide = 853
    Vetauras_Harbinger = 36678
    Vial_Of_Absinthe = 6367
    Vial_Of_Dye = 146
    Vial_Of_Ink = 944
    Victory_Token = 18345
    Vizu_Mini = 22196
    Wand = 15552
    War_Supplies = 35121
    Warden_Horn = 822
    Warrior_Elitetome = 21791
    Warrior_Tome = 21801
    Water_Djinn_Mini = 22754
    Wayfarer_Mark = 37765
    Weaver_Leg = 27037
    Whiptail_Devourer_Mini = 13785
    White_Mantle_Badge = 461
    White_Mantle_Emblem = 460
    White_Rabbit_Mini = 30623
    Wind_Rider_Mini = 22763
    Wintergreen_Axe = 15835
    Wintergreen_Bow = 15836
    Wintergreen_Cc = 21488
    Wintergreen_Daggers = 15838
    Wintergreen_Hammer = 15839
    Wintergreen_Scythe = 15877
    Wintergreen_Shield = 15878
    Wintergreen_Spear = 15971
    Wintergreen_Staff =16128
    Wintergreen_Sword = 16130
    Wintergreen_Wand = 15840
    Wintersday_Gift = 21491
    Witchs_Brew = 6049
    Wood_Plank = 946
    Word_Of_Madness_Mini = 32516
    World_Famous_Racing_Beetle_Mini = 37792
    Worn_Belt = 427
    Yakkington_Mini = 32515
    Yuletide_Tonic = 21490
    Zaishen_Key = 28571
    Zaishen_Summon = 31156
    Zaishen_Tonic = 31144
    Zehtukas_Great_Horn = 15845
    Zehtukas_Jug = 19171
    Zhed_Shadowhoof_Mini = 22197
    Zhos_Journal = 25866
    Zhu_Hanuku_Mini = 34398
    
    
#region AgentModels
class SpiritModelID(IntEnum):
    #SPIRIT_MODEL
    #RANGER
    BRAMBLES = 4239
    CONFLAGRATION = 4237
    ENERGIZING_WIND = 2885
    EQUINOX = 4236
    EDGE_OF_EXTINCTION = 2876
    FAMINE = 4238
    FAVORABLE_WINDS = 2883
    FERTILE_SEASON = 2878
    FROZEN_SOIL = 2882
    GREATER_CONFLAGRATION = 2877
    INFURIATING_HEAT = 5715
    LACERATE = 4232
    MUDDY_TERRAIN = 2888
    NATURES_RENEWAL = 2887
    PESTILENCE = 4234
    PREDATORY_SEASON = 2881
    PRIMAL_ECHOES = 2880
    QUICKENING_ZEPHYR = 2886
    QUICKSAND = 5718
    ROARING_WINDS = 5717
    SYMBIOSIS = 2879
    TOXICITY = 5716
    TRANQUILITY = 4235
    WINTER = 2874
    WINNOWING = 2875
    
    #RITUALIST
    AGONY = 5854
    ANGUISH = 5720
    ANGER = 4229
    BLOODSONG = 4227
    DESTRUCTION = 4215
    DISENCHANTMENT = 4225
    DISPLACEMENT = 4217
    DISSONANCE = 4221
    EARTHBIND = 4222
    EMPOWERMENT = 5721
    HATE = 4230
    LIFE = 4218
    PAIN = 4214
    PRESERVATION = 4219
    RECOVERY = 5719
    RECUPERATION = 4220
    REJUVENATION = 5853
    RESTORATION = 4226
    SHADOWSONG = 4213
    SHELTER = 4223
    SOOTHING = 4216
    SUFFERING = 4231
    UNION = 4224
    WANDERLUST = 4228

    #OTHER
    VAMPIRISM = 5723
    WINDS = 2884

#region Menagerie
#PET_MODEL
class PetModelID(IntEnum):
    #charmable animals
    MELANDRUS_STALKER_WILD = 1345
    RAINBOW_PHOENIX_WILD = 2990
    RAVEN_WILD = 5820
    WOLF_WILD = 1387
    WOLF_ELDER_WILD = 1388
    
    
    ALBINO_RAT = 561
    ALBINO_RAT_12_ELDER = 562
    ALBINO_RAT_12_PLAYFUL = 563
    ALBINO_RAT_12_AGGRESSIVE = 564
    ALBINO_RAT_15_ELDER = 565
    ALBINO_RAT_15_PLAYFUL = 566
    ALBINO_RAT_15_AGGRESSIVE = 567
    ALBINO_RAT_15_HEARTY = 568
    ALBINO_RAT_15_DIRE = 569
    ALBINO_RAT_20_ELDER = 570
    ALBINO_RAT_20_PLAYFUL = 571
    ALBINO_RAT_20_AGGRESSIVE = 572
    ALBINO_RAT_20_HEARTY = 573
    ALBINO_RAT_20_DIRE = 574
    BLACK_BEAR = 575
    BLACK_BEAR_12_ELDER = 576
    BLACK_BEAR_12_PLAYFUL = 577
    BLACK_BEAR_12_AGGRESSIVE = 578
    BLACK_BEAR_15_ELDER = 579
    BLACK_BEAR_15_PLAYFUL = 580
    BLACK_BEAR_15_AGGRESSIVE = 581
    BLACK_BEAR_15_HEARTY = 582
    BLACK_BEAR_15_DIRE = 583
    BLACK_BEAR_20_ELDER = 584
    BLACK_BEAR_20_PLAYFUL = 585
    BLACK_BEAR_20_AGGRESSIVE = 586
    BLACK_BEAR_20_HEARTY = 587
    BLACK_BEAR_20_DIRE = 588
    BLACK_MOA = 589
    BLACK_MOA_12_ELDER = 590
    BLACK_MOA_12_PLAYFUL = 591
    BLACK_MOA_12_AGGRESSIVE = 592
    BLACK_MOA_15_ELDER = 593
    BLACK_MOA_15_PLAYFUL = 594
    BLACK_MOA_15_AGGRESSIVE = 595
    BLACK_MOA_15_HEARTY = 596
    BLACK_MOA_15_DIRE = 597
    BLACK_MOA_20_ELDER = 598
    BLACK_MOA_20_PLAYFUL = 599
    BLACK_MOA_20_AGGRESSIVE = 600
    BLACK_MOA_20_HEARTY = 601
    BLACK_MOA_20_DIRE = 602
    BLACK_WIDOW = 603
    BLACK_WIDOW_12_ELDER = 604
    BLACK_WIDOW_12_PLAYFUL = 605
    BLACK_WIDOW_12_AGGRESSIVE = 606
    BLACK_WIDOW_15_ELDER = 607
    BLACK_WIDOW_15_PLAYFUL = 608
    BLACK_WIDOW_15_AGGRESSIVE = 609
    BLACK_WIDOW_15_HEARTY = 610
    BLACK_WIDOW_15_DIRE = 611
    BLACK_WIDOW_20_ELDER = 612
    BLACK_WIDOW_20_PLAYFUL = 613
    BLACK_WIDOW_20_AGGRESSIVE = 614
    BLACK_WIDOW_20_HEARTY = 615
    BLACK_WIDOW_20_DIRE = 616
    BLACK_WOLF = 617
    BLACK_WOLF_12_ELDER = 618
    BLACK_WOLF_12_PLAYFUL = 619
    BLACK_WOLF_12_AGGRESSIVE = 620
    BLACK_WOLF_15_ELDER = 621
    BLACK_WOLF_15_PLAYFUL = 622
    BLACK_WOLF_15_AGGRESSIVE = 623
    BLACK_WOLF_15_HEARTY = 624
    BLACK_WOLF_15_DIRE = 625
    BLACK_WOLF_20_ELDER = 626
    BLACK_WOLF_20_PLAYFUL = 627
    BLACK_WOLF_20_AGGRESSIVE = 628
    BLACK_WOLF_20_HEARTY = 629
    BLACK_WOLF_20_DIRE = 630
    CRANE = 631
    CRANE_12_ELDER = 632
    CRANE_12_PLAYFUL = 633
    CRANE_12_AGGRESSIVE = 634
    CRANE_15_ELDER = 635
    CRANE_15_PLAYFUL = 636
    CRANE_15_AGGRESSIVE = 637
    CRANE_15_HEARTY = 638
    CRANE_15_DIRE = 639
    CRANE_20_ELDER = 640
    CRANE_20_PLAYFUL = 641
    CRANE_20_AGGRESSIVE = 642
    CRANE_20_HEARTY = 643
    CRANE_20_DIRE = 644
    CROCODILE = 645
    CROCODILE_12_ELDER = 646
    CROCODILE_12_PLAYFUL = 647
    CROCODILE_12_AGGRESSIVE = 648
    CROCODILE_15_ELDER = 649
    CROCODILE_15_PLAYFUL = 650
    CROCODILE_15_AGGRESSIVE = 651
    CROCODILE_15_HEARTY = 652
    CROCODILE_15_DIRE = 653
    CROCODILE_20_ELDER = 654
    CROCODILE_20_PLAYFUL = 655
    CROCODILE_20_AGGRESSIVE = 656
    CROCODILE_20_HEARTY = 657
    CROCODILE_20_DIRE = 658
    DUNE_LIZARD = 659
    DUNE_LIZARD_12_ELDER = 660
    DUNE_LIZARD_12_PLAYFUL = 661
    DUNE_LIZARD_12_AGGRESSIVE = 662
    DUNE_LIZARD_15_ELDER = 663
    DUNE_LIZARD_15_PLAYFUL = 664
    DUNE_LIZARD_15_AGGRESSIVE = 665
    DUNE_LIZARD_15_HEARTY = 666
    DUNE_LIZARD_15_DIRE = 667
    DUNE_LIZARD_20_ELDER = 668
    DUNE_LIZARD_20_PLAYFUL = 669
    DUNE_LIZARD_20_AGGRESSIVE = 670
    DUNE_LIZARD_20_HEARTY = 671
    DUNE_LIZARD_20_DIRE = 672
    FLAMINGO = 673
    FLAMINGO_12_ELDER = 674
    FLAMINGO_12_PLAYFUL = 675
    FLAMINGO_12_AGGRESSIVE = 676
    FLAMINGO_15_ELDER = 677
    FLAMINGO_15_PLAYFUL = 678
    FLAMINGO_15_AGGRESSIVE = 679
    FLAMINGO_15_HEARTY = 680
    FLAMINGO_15_DIRE = 681
    FLAMINGO_20_ELDER = 682
    FLAMINGO_20_PLAYFUL = 683
    FLAMINGO_20_AGGRESSIVE = 684
    FLAMINGO_20_HEARTY = 685
    FLAMINGO_20_DIRE = 686
    HYENA = 687
    HYENA_12_ELDER = 688
    HYENA_12_PLAYFUL = 689
    HYENA_12_AGGRESSIVE = 690
    HYENA_15_ELDER = 691
    HYENA_15_PLAYFUL = 692
    HYENA_15_AGGRESSIVE = 693
    HYENA_15_HEARTY = 694
    HYENA_15_DIRE = 695
    HYENA_20_ELDER = 696
    HYENA_20_PLAYFUL = 697
    HYENA_20_AGGRESSIVE = 698
    HYENA_20_HEARTY = 699
    HYENA_20_DIRE = 700
    IGUANA = 701
    IGUANA_12_ELDER = 702
    IGUANA_12_PLAYFUL = 703
    IGUANA_12_AGGRESSIVE = 704
    IGUANA_15_ELDER = 705
    IGUANA_15_PLAYFUL = 706
    IGUANA_15_AGGRESSIVE = 707
    IGUANA_15_HEARTY = 708
    IGUANA_15_DIRE = 709
    IGUANA_20_ELDER = 710
    IGUANA_20_PLAYFUL = 711
    IGUANA_20_AGGRESSIVE = 712
    IGUANA_20_HEARTY = 713
    IGUANA_20_DIRE = 714
    JAHAI_RAT = 715
    JAHAI_RAT_12_ELDER = 716
    JAHAI_RAT_12_PLAYFUL = 717
    JAHAI_RAT_12_AGGRESSIVE = 718
    JAHAI_RAT_15_ELDER = 719
    JAHAI_RAT_15_PLAYFUL = 720
    JAHAI_RAT_15_AGGRESSIVE = 721
    JAHAI_RAT_15_HEARTY = 722
    JAHAI_RAT_15_DIRE = 723
    JAHAI_RAT_20_ELDER = 724
    JAHAI_RAT_20_PLAYFUL = 725
    JAHAI_RAT_20_AGGRESSIVE = 726
    JAHAI_RAT_20_HEARTY = 727
    JAHAI_RAT_20_DIRE = 728
    JINGLE_BEAR = 729
    JINGLE_BEAR_12_ELDER = 730
    JINGLE_BEAR_12_PLAYFUL = 731
    JINGLE_BEAR_12_AGGRESSIVE = 732
    JINGLE_BEAR_15_ELDER = 733
    JINGLE_BEAR_15_PLAYFUL = 734
    JINGLE_BEAR_15_AGGRESSIVE = 735
    JINGLE_BEAR_15_HEARTY = 736
    JINGLE_BEAR_15_DIRE = 737
    JINGLE_BEAR_20_ELDER = 738
    JINGLE_BEAR_20_PLAYFUL = 739
    JINGLE_BEAR_20_AGGRESSIVE = 740
    JINGLE_BEAR_20_HEARTY = 741
    JINGLE_BEAR_20_DIRE = 742
    
    LION = 757
    LION_12_ELDER = 758
    LION_12_PLAYFUL = 759
    LION_12_AGGRESSIVE = 760
    LION_15_ELDER = 761
    LION_15_PLAYFUL = 762
    LION_15_AGGRESSIVE = 763
    LION_15_HEARTY = 764
    LION_15_DIRE = 765
    LION_20_ELDER = 766
    LION_20_PLAYFUL = 767
    LION_20_AGGRESSIVE = 768
    LION_20_HEARTY = 769
    LION_20_DIRE = 770
    LIONESS = 771
    LIONESS_12_ELDER = 772
    LIONESS_12_PLAYFUL = 773
    LIONESS_12_AGGRESSIVE = 774
    LIONESS_15_ELDER = 775
    LIONESS_15_PLAYFUL = 776
    LIONESS_15_AGGRESSIVE = 777
    LIONESS_15_HEARTY = 778
    LIONESS_15_DIRE = 779
    LIONESS_20_ELDER = 780
    LIONESS_20_PLAYFUL = 781
    LIONESS_20_AGGRESSIVE = 782
    LIONESS_20_HEARTY = 783
    LIONESS_20_DIRE = 784
    LURKER = 785
    LURKER_12_ELDER = 786
    LURKER_12_PLAYFUL = 787
    LURKER_12_AGGRESSIVE = 788
    LURKER_15_ELDER = 789
    LURKER_15_PLAYFUL = 790
    LURKER_15_AGGRESSIVE = 791
    LURKER_15_HEARTY = 792
    LURKER_15_DIRE = 793
    LURKER_20_ELDER = 794
    LURKER_20_PLAYFUL = 795
    LURKER_20_AGGRESSIVE = 796
    LURKER_20_HEARTY = 797
    LURKER_20_DIRE = 798
    LYNX = 799
    LYNX_12_ELDER = 800
    LYNX_12_PLAYFUL = 801
    LYNX_12_AGGRESSIVE = 802
    LYNX_15_ELDER = 803
    LYNX_15_PLAYFUL = 804
    LYNX_15_AGGRESSIVE = 805
    LYNX_15_HEARTY = 806
    LYNX_15_DIRE = 807
    LYNX_20_ELDER = 808
    LYNX_20_PLAYFUL = 809
    LYNX_20_AGGRESSIVE = 810
    LYNX_20_HEARTY = 811
    LYNX_20_DIRE = 812
    MELANDRUS_STALKER = 813
    MELANDRUS_STALKER_12_ELDER = 814
    MELANDRUS_STALKER_12_PLAYFUL = 815
    MELANDRUS_STALKER_12_AGGRESSIVE = 816
    MELANDRUS_STALKER_15_ELDER = 817
    MELANDRUS_STALKER_15_PLAYFUL = 818
    MELANDRUS_STALKER_15_AGGRESSIVE = 819
    MELANDRUS_STALKER_15_HEARTY = 820
    MELANDRUS_STALKER_15_DIRE = 821
    MELANDRUS_STALKER_20_ELDER = 822
    MELANDRUS_STALKER_20_PLAYFUL = 823
    MELANDRUS_STALKER_20_AGGRESSIVE = 824
    MELANDRUS_STALKER_20_HEARTY = 825
    MELANDRUS_STALKER_20_DIRE = 826
    MOA_BIRD = 827
    MOA_BIRD_12_ELDER = 828
    MOA_BIRD_12_PLAYFUL = 829
    MOA_BIRD_12_AGGRESSIVE = 830
    MOA_BIRD_15_ELDER = 831
    MOA_BIRD_15_PLAYFUL = 832
    MOA_BIRD_15_AGGRESSIVE = 833
    MOA_BIRD_15_HEARTY = 834
    MOA_BIRD_15_DIRE = 835
    MOA_BIRD_20_ELDER = 836
    MOA_BIRD_20_PLAYFUL = 837
    MOA_BIRD_20_AGGRESSIVE = 838
    MOA_BIRD_20_HEARTY = 839
    MOA_BIRD_20_DIRE = 840
    MOSS_SPIDER = 841
    MOSS_SPIDER_12_ELDER = 842
    MOSS_SPIDER_12_PLAYFUL = 843
    MOSS_SPIDER_12_AGGRESSIVE = 844
    MOSS_SPIDER_15_ELDER = 845
    MOSS_SPIDER_15_PLAYFUL = 846
    MOSS_SPIDER_15_AGGRESSIVE = 847
    MOSS_SPIDER_15_HEARTY = 848
    MOSS_SPIDER_15_DIRE = 849
    MOSS_SPIDER_20_ELDER = 850
    MOSS_SPIDER_20_PLAYFUL = 851
    MOSS_SPIDER_20_AGGRESSIVE = 852
    MOSS_SPIDER_20_HEARTY = 853
    MOSS_SPIDER_20_DIRE = 854
    MOUNTAIN_EAGLE = 855
    MOUNTAIN_EAGLE_12_ELDER = 856
    MOUNTAIN_EAGLE_12_PLAYFUL = 857
    MOUNTAIN_EAGLE_12_AGGRESSIVE = 858
    MOUNTAIN_EAGLE_15_ELDER = 859
    MOUNTAIN_EAGLE_15_PLAYFUL = 860
    MOUNTAIN_EAGLE_15_AGGRESSIVE = 861
    MOUNTAIN_EAGLE_15_HEARTY = 862
    MOUNTAIN_EAGLE_15_DIRE = 863
    MOUNTAIN_EAGLE_20_ELDER = 864
    MOUNTAIN_EAGLE_20_PLAYFUL = 865
    MOUNTAIN_EAGLE_20_AGGRESSIVE = 866
    MOUNTAIN_EAGLE_20_HEARTY = 867
    MOUNTAIN_EAGLE_20_DIRE = 868
    PANDA = 869
    PANDA_12_ELDER = 870
    PANDA_12_PLAYFUL = 871
    PANDA_12_AGGRESSIVE = 872
    PANDA_15_ELDER = 873
    PANDA_15_PLAYFUL = 874
    PANDA_15_AGGRESSIVE = 875
    PANDA_15_HEARTY = 876
    PANDA_15_DIRE = 877
    PANDA_20_ELDER = 878
    PANDA_20_PLAYFUL = 879
    PANDA_20_AGGRESSIVE = 880
    PANDA_20_HEARTY = 881
    PANDA_20_DIRE = 882
    PHOENIX = 883
    PHOENIX_12_ELDER = 884
    PHOENIX_12_PLAYFUL = 885
    PHOENIX_12_AGGRESSIVE = 886
    PHOENIX_15_ELDER = 887
    PHOENIX_15_PLAYFUL = 888
    PHOENIX_15_AGGRESSIVE = 889
    PHOENIX_15_HEARTY = 890
    PHOENIX_15_DIRE = 891
    PHOENIX_20_ELDER = 892
    PHOENIX_20_PLAYFUL = 893
    PHOENIX_20_AGGRESSIVE = 894
    PHOENIX_20_HEARTY = 895
    PHOENIX_20_DIRE = 896
    
    POLAR_BEAR = 911
    POLAR_BEAR_12_ELDER = 912
    POLAR_BEAR_12_PLAYFUL = 913
    POLAR_BEAR_12_AGGRESSIVE = 914
    POLAR_BEAR_15_ELDER = 915
    POLAR_BEAR_15_PLAYFUL = 916
    POLAR_BEAR_15_AGGRESSIVE = 917
    POLAR_BEAR_15_HEARTY = 918
    POLAR_BEAR_15_DIRE = 919
    POLAR_BEAR_20_ELDER = 920
    POLAR_BEAR_20_PLAYFUL = 921
    POLAR_BEAR_20_AGGRESSIVE = 922
    POLAR_BEAR_20_HEARTY = 923
    POLAR_BEAR_20_DIRE = 924
    
    RACING_BEETLE = 939
    RACING_BEETLE_12_ELDER = 940
    RACING_BEETLE_12_PLAYFUL = 941
    RACING_BEETLE_12_AGGRESSIVE = 942
    RACING_BEETLE_15_ELDER = 943
    RACING_BEETLE_15_PLAYFUL = 944
    RACING_BEETLE_15_AGGRESSIVE = 945
    RACING_BEETLE_15_HEARTY = 946
    RACING_BEETLE_15_DIRE = 947
    RACING_BEETLE_20_ELDER = 948
    RACING_BEETLE_20_PLAYFUL = 949
    RACING_BEETLE_20_AGGRESSIVE = 950
    RACING_BEETLE_20_HEARTY = 951
    RACING_BEETLE_20_DIRE = 952
    RAINBOW_PHOENIX = 953
    RAINBOW_PHOENIX_12_ELDER = 954
    RAINBOW_PHOENIX_12_PLAYFUL = 955
    RAINBOW_PHOENIX_12_AGGRESSIVE = 956
    RAINBOW_PHOENIX_15_ELDER = 957
    RAINBOW_PHOENIX_15_PLAYFUL = 958
    RAINBOW_PHOENIX_15_AGGRESSIVE = 959
    RAINBOW_PHOENIX_15_HEARTY = 960
    RAINBOW_PHOENIX_15_DIRE = 961
    RAINBOW_PHOENIX_20_ELDER = 962
    RAINBOW_PHOENIX_20_PLAYFUL = 963
    RAINBOW_PHOENIX_20_AGGRESSIVE = 964
    RAINBOW_PHOENIX_20_HEARTY = 965
    RAINBOW_PHOENIX_20_DIRE = 966
    RAVEN = 967
    RAVEN_12_ELDER = 968
    RAVEN_12_PLAYFUL = 969
    RAVEN_12_AGGRESSIVE = 970
    RAVEN_15_ELDER = 971
    RAVEN_15_PLAYFUL = 972
    RAVEN_15_AGGRESSIVE = 973
    RAVEN_15_HEARTY = 974
    RAVEN_15_DIRE = 975
    RAVEN_20_ELDER = 976
    RAVEN_20_PLAYFUL = 977
    RAVEN_20_AGGRESSIVE = 978
    RAVEN_20_HEARTY = 979
    RAVEN_20_DIRE = 980
    
    REEF_LURKER = 995
    REEF_LURKER_12_ELDER = 996
    REEF_LURKER_12_PLAYFUL = 997
    REEF_LURKER_12_AGGRESSIVE = 998
    REEF_LURKER_15_ELDER = 999
    REEF_LURKER_15_PLAYFUL = 1000
    REEF_LURKER_15_AGGRESSIVE = 1001
    REEF_LURKER_15_HEARTY = 1002
    REEF_LURKER_15_DIRE = 1003
    REEF_LURKER_20_ELDER = 1004
    REEF_LURKER_20_PLAYFUL = 1005
    REEF_LURKER_20_AGGRESSIVE = 1006
    REEF_LURKER_20_HEARTY = 1007
    REEF_LURKER_20_DIRE = 1008

    TIGER = 1023
    TIGER_12_ELDER = 1024
    TIGER_12_PLAYFUL = 1025
    TIGER_12_AGGRESSIVE = 1026
    TIGER_15_ELDER = 1027
    TIGER_15_PLAYFUL = 1028
    TIGER_15_AGGRESSIVE = 1029
    TIGER_15_HEARTY = 1030
    TIGER_15_DIRE = 1031
    TIGER_20_ELDER = 1032
    TIGER_20_PLAYFUL = 1033
    TIGER_20_AGGRESSIVE = 1034
    TIGER_20_HEARTY = 1035
    TIGER_20_DIRE = 1036
    WARTHOG = 1037
    WARTHOG_12_ELDER = 1038
    WARTHOG_12_PLAYFUL = 1039
    WARTHOG_12_AGGRESSIVE = 1040
    WARTHOG_15_ELDER = 1041
    WARTHOG_15_PLAYFUL = 1042
    WARTHOG_15_AGGRESSIVE = 1043
    WARTHOG_15_HEARTY = 1044
    WARTHOG_15_DIRE = 1045
    WARTHOG_20_ELDER = 1046
    WARTHOG_20_PLAYFUL = 1047
    WARTHOG_20_AGGRESSIVE = 1048
    WARTHOG_20_HEARTY = 1049
    WARTHOG_20_DIRE = 1050
    WHITE_CRAB = 1051
    WHITE_CRAB_12_ELDER = 1052
    WHITE_CRAB_12_PLAYFUL = 1053
    WHITE_CRAB_12_AGGRESSIVE = 1054
    WHITE_CRAB_15_ELDER = 1055
    WHITE_CRAB_15_PLAYFUL = 1056
    WHITE_CRAB_15_AGGRESSIVE = 1057
    WHITE_CRAB_15_HEARTY = 1058
    WHITE_CRAB_15_DIRE = 1059
    WHITE_CRAB_20_ELDER = 1060
    WHITE_CRAB_20_PLAYFUL = 1061
    WHITE_CRAB_20_AGGRESSIVE = 1062
    WHITE_CRAB_20_HEARTY = 1063
    WHITE_CRAB_20_DIRE = 1064
    WHITE_JINGLE_MOA = 1065
    WHITE_JINGLE_MOA_12_ELDER = 1066
    WHITE_JINGLE_MOA_12_PLAYFUL = 1067
    WHITE_JINGLE_MOA_12_AGGRESSIVE = 1068
    WHITE_JINGLE_MOA_15_ELDER = 1069
    WHITE_JINGLE_MOA_15_PLAYFUL = 1070
    WHITE_JINGLE_MOA_15_AGGRESSIVE = 1071
    WHITE_JINGLE_MOA_15_HEARTY = 1072
    WHITE_JINGLE_MOA_15_DIRE = 1073
    WHITE_JINGLE_MOA_20_ELDER = 1074
    WHITE_JINGLE_MOA_20_PLAYFUL = 1075
    WHITE_JINGLE_MOA_20_AGGRESSIVE = 1076
    WHITE_JINGLE_MOA_20_HEARTY = 1077
    WHITE_JINGLE_MOA_20_DIRE = 1078
    WHITE_MOA = 1079
    WHITE_MOA_12_ELDER = 1080
    WHITE_MOA_12_PLAYFUL = 1081
    WHITE_MOA_12_AGGRESSIVE = 1082
    WHITE_MOA_15_ELDER = 1083
    WHITE_MOA_15_PLAYFUL = 1084
    WHITE_MOA_15_AGGRESSIVE = 1085
    WHITE_MOA_15_HEARTY = 1086
    WHITE_MOA_15_DIRE = 1087
    WHITE_MOA_20_ELDER = 1088
    WHITE_MOA_20_PLAYFUL = 1089
    WHITE_MOA_20_AGGRESSIVE = 1090
    WHITE_MOA_20_HEARTY = 1091
    WHITE_MOA_20_DIRE = 1092
    WHITE_TIGER = 1093
    WHITE_TIGER_12_ELDER = 1094
    WHITE_TIGER_12_PLAYFUL = 1095
    WHITE_TIGER_12_AGGRESSIVE = 1096
    WHITE_TIGER_15_ELDER = 1097
    WHITE_TIGER_15_PLAYFUL = 1098
    WHITE_TIGER_15_AGGRESSIVE = 1099
    WHITE_TIGER_15_HEARTY = 1100
    WHITE_TIGER_15_DIRE = 1101
    WHITE_TIGER_20_ELDER = 1102
    WHITE_TIGER_20_PLAYFUL = 1103
    WHITE_TIGER_20_AGGRESSIVE = 1104
    WHITE_TIGER_20_HEARTY = 1105
    WHITE_TIGER_20_DIRE = 1106
    WHITE_WOLF = 1107
    WHITE_WOLF_12_ELDER = 1108
    WHITE_WOLF_12_PLAYFUL = 1109
    WHITE_WOLF_12_AGGRESSIVE = 1110
    WHITE_WOLF_15_ELDER = 1111
    WHITE_WOLF_15_PLAYFUL = 1112
    WHITE_WOLF_15_AGGRESSIVE = 1113
    WHITE_WOLF_15_HEARTY = 1114
    WHITE_WOLF_15_DIRE = 1115
    WHITE_WOLF_20_ELDER = 1116
    WHITE_WOLF_20_PLAYFUL = 1117
    WHITE_WOLF_20_AGGRESSIVE = 1118
    WHITE_WOLF_20_HEARTY = 1119
    WHITE_WOLF_20_DIRE = 1120
    WOLF = 1121
    WOLF_12_ELDER = 1122
    WOLF_12_PLAYFUL = 1123
    WOLF_12_AGGRESSIVE = 1124
    WOLF_15_ELDER = 1125
    WOLF_15_PLAYFUL = 1126
    WOLF_15_AGGRESSIVE = 1127
    WOLF_15_HEARTY = 1128
    WOLF_15_DIRE = 1129
    WOLF_20_ELDER = 1130
    WOLF_20_PLAYFUL = 1131
    WOLF_20_AGGRESSIVE = 1132
    WOLF_20_HEARTY = 1133
    WOLF_20_DIRE = 1134
    HOUND = 1135
    HOUND_12_ELDER = 1136
    HOUND_12_PLAYFUL = 1137
    HOUND_12_AGGRESSIVE = 1138
    HOUND_15_ELDER = 1139
    HOUND_15_PLAYFUL = 1140
    HOUND_15_AGGRESSIVE = 1141
    HOUND_15_HEARTY = 1142
    HOUND_15_DIRE = 1143
    HOUND_20_ELDER = 1144
    HOUND_20_PLAYFUL = 1145
    HOUND_20_AGGRESSIVE = 1146
    HOUND_20_HEARTY = 1147
    HOUND_20_DIRE = 1148
    


#region SkillTextures

SkillTextureMap = {
    1: '[1] - Healing Signet.jpg',
    2: '[2] - Resurrection Signet.jpg',
    3: '[3] - Signet of Capture.jpg',
    5: '[5] - Power Block.jpg',
    6: '[6] - Mantra of Earth.jpg',
    7: '[7] - Mantra of Flame.jpg',
    8: '[8] - Mantra of Frost.jpg',
    9: '[9] - Mantra of Lightning.jpg',
    10: '[10] - Hex Breaker.jpg',
    11: '[11] - Distortion.jpg',
    13: '[13] - Mantra of Recovery.jpg',
    14: '[14] - Mantra of Persistence.jpg',
    15: '[15] - Mantra of Inscriptions.jpg',
    16: '[16] - Mantra of Concentration.jpg',
    17: '[17] - Mantra of Resolve.jpg',
    18: '[18] - Mantra of Signets.jpg',
    19: '[19] - Fragility.jpg',
    21: '[21] - Inspired Enchantment.jpg',
    22: '[22] - Inspired Hex.jpg',
    23: '[23] - Power Spike.jpg',
    24: '[24] - Power Leak.jpg',
    25: '[25] - Power Drain.jpg',
    26: '[26] - Empathy.jpg',
    27: '[27] - Shatter Delusions.jpg',
    28: '[28] - Backfire.jpg',
    29: '[29] - Blackout.jpg',
    30: '[30] - Diversion.jpg',
    31: '[31] - Conjure Phantasm.jpg',
    32: '[32] - Illusion of Weakness.jpg',
    33: '[33] - Illusionary Weaponry.jpg',
    34: '[34] - Sympathetic Visage.jpg',
    35: '[35] - Ignorance.jpg',
    36: '[36] - Arcane Conundrum.jpg',
    37: '[37] - Illusion of Haste.jpg',
    38: '[38] - Channeling.jpg',
    39: '[39] - Energy Surge.jpg',
    40: '[40] - Ether Feast.jpg',
    41: '[41] - Ether Lord.jpg',
    42: '[42] - Energy Burn.jpg',
    43: '[43] - Clumsiness.jpg',
    44: '[44] - Phantom Pain.jpg',
    45: '[45] - Ethereal Burden.jpg',
    46: '[46] - Guilt.jpg',
    47: '[47] - Ineptitude.jpg',
    48: '[48] - Spirit of Failure.jpg',
    49: '[49] - Mind Wrack.jpg',
    50: "[50] - Wastrel's Worry.jpg",
    51: '[51] - Shame.jpg',
    52: '[52] - Panic.jpg',
    53: '[53] - Migraine.jpg',
    54: '[54] - Crippling Anguish.jpg',
    55: '[55] - Fevered Dreams.jpg',
    56: '[56] - Soothing Images.jpg',
    57: '[57] - Cry of Frustration.jpg',
    58: '[58] - Signet of Midnight.jpg',
    59: '[59] - Signet of Weariness.jpg',
    61: '[61] - Leech Signet.jpg',
    62: '[62] - Signet of Humility.jpg',
    63: '[63] - Keystone Signet.jpg',
    65: '[65] - Arcane Mimicry.jpg',
    66: '[66] - Spirit Shackles.jpg',
    67: '[67] - Shatter Hex.jpg',
    68: '[68] - Drain Enchantment.jpg',
    69: '[69] - Shatter Enchantment.jpg',
    72: '[72] - Elemental Resistance.jpg',
    73: '[73] - Physical Resistance.jpg',
    74: '[74] - Echo.jpg',
    75: '[75] - Arcane Echo.jpg',
    76: '[76] - Imagined Burden.jpg',
    77: '[77] - Chaos Storm.jpg',
    78: '[78] - Epidemic.jpg',
    79: '[79] - Energy Drain.jpg',
    80: '[80] - Energy Tap.jpg',
    81: '[81] - Arcane Thievery.jpg',
    82: '[82] - Mantra of Recall.jpg',
    83: '[83] - Animate Bone Horror.jpg',
    84: '[84] - Animate Bone Fiend.jpg',
    85: '[85] - Animate Bone Minions.jpg',
    86: "[86] - Grenth's Balance.jpg",
    87: "[87] - Verata's Gaze.jpg",
    88: "[88] - Verata's Aura.jpg",
    89: '[89] - Deathly Chill.jpg',
    90: "[90] - Verata's Sacrifice.jpg",
    91: '[91] - Well of Power.jpg',
    92: '[92] - Well of Blood.jpg',
    93: '[93] - Well of Suffering.jpg',
    94: '[94] - Well of the Profane.jpg',
    95: '[95] - Putrid Explosion.jpg',
    96: '[96] - Soul Feast.jpg',
    97: '[97] - Necrotic Traversal.jpg',
    98: '[98] - Consume Corpse.jpg',
    99: '[99] - Parasitic Bond.jpg',
    100: '[100] - Soul Barbs.jpg',
    101: '[101] - Barbs.jpg',
    102: '[102] - Shadow Strike.jpg',
    103: '[103] - Price of Failure.jpg',
    104: '[104] - Death Nova.jpg',
    105: '[105] - Deathly Swarm.jpg',
    106: '[106] - Rotting Flesh.jpg',
    107: '[107] - Virulence.jpg',
    108: '[108] - Suffering.jpg',
    109: '[109] - Life Siphon.jpg',
    110: '[110] - Unholy Feast.jpg',
    111: '[111] - Awaken the Blood.jpg',
    112: '[112] - Desecrate Enchantments.jpg',
    113: '[113] - Tainted Flesh.jpg',
    114: '[114] - Aura of the Lich.jpg',
    115: '[115] - Blood Renewal.jpg',
    116: '[116] - Dark Aura.jpg',
    117: '[117] - Enfeeble.jpg',
    118: '[118] - Enfeebling Blood.jpg',
    119: '[119] - Blood is Power.jpg',
    120: '[120] - Blood of the Master.jpg',
    121: '[121] - Spiteful Spirit.jpg',
    122: '[122] - Malign Intervention.jpg',
    123: '[123] - Insidious Parasite.jpg',
    124: '[124] - Spinal Shivers.jpg',
    125: '[125] - Wither.jpg',
    126: '[126] - Life Transfer.jpg',
    127: '[127] - Mark of Subversion.jpg',
    128: '[128] - Soul Leech.jpg',
    129: '[129] - Defile Flesh.jpg',
    130: '[130] - Demonic Flesh.jpg',
    131: '[131] - Barbed Signet.jpg',
    132: '[132] - Plague Signet.jpg',
    133: '[133] - Dark Pact.jpg',
    134: '[134] - Order of Pain.jpg',
    135: '[135] - Faintheartedness.jpg',
    136: '[136] - Shadow of Fear.jpg',
    137: '[137] - Rigor Mortis.jpg',
    138: '[138] - Dark Bond.jpg',
    139: '[139] - Infuse Condition.jpg',
    140: '[140] - Malaise.jpg',
    141: '[141] - Rend Enchantments.jpg',
    142: '[142] - Lingering Curse.jpg',
    143: '[143] - Strip Enchantment.jpg',
    144: '[144] - Chilblains.jpg',
    145: '[145] - Signet of Agony.jpg',
    146: '[146] - Offering of Blood.jpg',
    147: '[147] - Dark Fury.jpg',
    148: '[148] - Order of the Vampire.jpg',
    149: '[149] - Plague Sending.jpg',
    150: '[150] - Mark of Pain.jpg',
    151: '[151] - Feast of Corruption.jpg',
    152: '[152] - Taste of Death.jpg',
    153: '[153] - Vampiric Gaze.jpg',
    154: '[154] - Plague Touch.jpg',
    155: '[155] - Vile Touch.jpg',
    156: '[156] - Vampiric Touch.jpg',
    157: '[157] - Blood Ritual.jpg',
    158: '[158] - Touch of Agony.jpg',
    159: '[159] - Weaken Armor.jpg',
    160: '[160] - Windborne Speed.jpg',
    162: '[162] - Gale.jpg',
    163: '[163] - Whirlwind.jpg',
    164: '[164] - Elemental Attunement.jpg',
    165: '[165] - Armor of Earth.jpg',
    166: '[166] - Kinetic Armor.jpg',
    167: '[167] - Eruption.jpg',
    168: '[168] - Magnetic Aura.jpg',
    169: '[169] - Earth Attunement.jpg',
    170: '[170] - Earthquake.jpg',
    171: '[171] - Stoning.jpg',
    172: '[172] - Stone Daggers.jpg',
    173: '[173] - Grasping Earth.jpg',
    174: '[174] - Aftershock.jpg',
    175: '[175] - Ward Against Elements.jpg',
    176: '[176] - Ward Against Melee.jpg',
    177: '[177] - Ward Against Foes.jpg',
    178: '[178] - Ether Prodigy.jpg',
    179: '[179] - Incendiary Bonds.jpg',
    180: '[180] - Aura of Restoration.jpg',
    181: '[181] - Ether Renewal.jpg',
    182: '[182] - Conjure Flame.jpg',
    183: '[183] - Inferno.jpg',
    184: '[184] - Fire Attunement.jpg',
    185: '[185] - Mind Burn.jpg',
    186: '[186] - Fireball.jpg',
    187: '[187] - Meteor.jpg',
    188: '[188] - Flame Burst.jpg',
    189: "[189] - Rodgort's Invocation.jpg",
    190: '[190] - Mark of Rodgort.jpg',
    191: '[191] - Immolate.jpg',
    192: '[192] - Meteor Shower.jpg',
    193: '[193] - Phoenix.jpg',
    194: '[194] - Flare.jpg',
    195: '[195] - Lava Font.jpg',
    196: '[196] - Searing Heat.jpg',
    197: '[197] - Fire Storm.jpg',
    198: '[198] - Glyph of Elemental Power.jpg',
    199: '[199] - Glyph of Energy.jpg',
    200: '[200] - Glyph of Lesser Energy.jpg',
    201: '[201] - Glyph of Concentration.jpg',
    202: '[202] - Glyph of Sacrifice.jpg',
    203: '[203] - Glyph of Renewal.jpg',
    204: '[204] - Rust.jpg',
    205: '[205] - Lightning Surge.jpg',
    206: '[206] - Armor of Frost.jpg',
    207: '[207] - Conjure Frost.jpg',
    208: '[208] - Water Attunement.jpg',
    209: '[209] - Mind Freeze.jpg',
    210: '[210] - Ice Prison.jpg',
    211: '[211] - Ice Spikes.jpg',
    212: '[212] - Frozen Burst.jpg',
    213: '[213] - Shard Storm.jpg',
    214: '[214] - Ice Spear.jpg',
    215: '[215] - Maelstrom.jpg',
    216: '[216] - Iron Mist.jpg',
    217: '[217] - Crystal Wave.jpg',
    218: '[218] - Obsidian Flesh.jpg',
    219: '[219] - Obsidian Flame.jpg',
    220: '[220] - Blinding Flash.jpg',
    221: '[221] - Conjure Lightning.jpg',
    222: '[222] - Lightning Strike.jpg',
    223: '[223] - Chain Lightning.jpg',
    224: '[224] - Enervating Charge.jpg',
    225: '[225] - Air Attunement.jpg',
    226: '[226] - Mind Shock.jpg',
    227: '[227] - Glimmering Mark.jpg',
    228: '[228] - Thunderclap.jpg',
    229: '[229] - Lightning Orb.jpg',
    230: '[230] - Lightning Javelin.jpg',
    231: '[231] - Shock.jpg',
    232: '[232] - Lightning Touch.jpg',
    233: '[233] - Swirling Aura.jpg',
    234: '[234] - Deep Freeze.jpg',
    235: '[235] - Blurred Vision.jpg',
    236: '[236] - Mist Form.jpg',
    237: '[237] - Water Trident.jpg',
    238: '[238] - Armor of Mist.jpg',
    239: '[239] - Ward Against Harm.jpg',
    240: '[240] - Smite.jpg',
    241: '[241] - Life Bond.jpg',
    242: "[242] - Balthazar's Spirit.jpg",
    243: '[243] - Strength of Honor.jpg',
    244: '[244] - Life Attunement.jpg',
    245: '[245] - Protective Spirit.jpg',
    246: '[246] - Divine Intervention.jpg',
    247: '[247] - Symbol of Wrath.jpg',
    248: '[248] - Retribution.jpg',
    249: '[249] - Holy Wrath.jpg',
    250: '[250] - Essence Bond.jpg',
    251: '[251] - Scourge Healing.jpg',
    252: '[252] - Banish.jpg',
    253: '[253] - Scourge Sacrifice.jpg',
    254: '[254] - Vigorous Spirit.jpg',
    255: '[255] - Watchful Spirit.jpg',
    256: '[256] - Blessed Aura.jpg',
    257: '[257] - Aegis.jpg',
    258: '[258] - Guardian.jpg',
    259: '[259] - Shield of Deflection.jpg',
    260: '[260] - Aura of Faith.jpg',
    261: '[261] - Shield of Regeneration.jpg',
    262: '[262] - Shield of Judgment.jpg',
    263: '[263] - Protective Bond.jpg',
    264: '[264] - Pacifism.jpg',
    265: '[265] - Amity.jpg',
    266: '[266] - Peace and Harmony.jpg',
    267: "[267] - Judge's Insight.jpg",
    268: '[268] - Unyielding Aura.jpg',
    269: '[269] - Mark of Protection.jpg',
    270: '[270] - Life Barrier.jpg',
    271: "[271] - Zealot's Fire.jpg",
    272: "[272] - Balthazar's Aura.jpg",
    273: '[273] - Spell Breaker.jpg',
    274: '[274] - Healing Seed.jpg',
    275: '[275] - Mend Condition.jpg',
    276: '[276] - Restore Condition.jpg',
    277: '[277] - Mend Ailment.jpg',
    278: '[278] - Purge Conditions.jpg',
    279: '[279] - Divine Healing.jpg',
    280: '[280] - Heal Area.jpg',
    281: '[281] - Orison of Healing.jpg',
    282: '[282] - Word of Healing.jpg',
    283: "[283] - Dwayna's Kiss.jpg",
    284: '[284] - Divine Boon.jpg',
    285: '[285] - Healing Hands.jpg',
    286: '[286] - Heal Other.jpg',
    287: '[287] - Heal Party.jpg',
    288: '[288] - Healing Breeze.jpg',
    289: '[289] - Vital Blessing.jpg',
    290: '[290] - Mending.jpg',
    291: '[291] - Live Vicariously.jpg',
    292: '[292] - Infuse Health.jpg',
    293: '[293] - Signet of Devotion.jpg',
    294: '[294] - Signet of Judgment.jpg',
    295: '[295] - Purge Signet.jpg',
    296: '[296] - Bane Signet.jpg',
    297: '[297] - Blessed Signet.jpg',
    298: '[298] - Martyr.jpg',
    299: '[299] - Shielding Hands.jpg',
    300: '[300] - Contemplation of Purity.jpg',
    301: '[301] - Remove Hex.jpg',
    302: '[302] - Smite Hex.jpg',
    303: '[303] - Convert Hexes.jpg',
    304: '[304] - Light of Dwayna.jpg',
    305: '[305] - Resurrect.jpg',
    306: '[306] - Rebirth.jpg',
    307: '[307] - Reversal of Fortune.jpg',
    308: '[308] - Succor.jpg',
    309: '[309] - Holy Veil.jpg',
    310: '[310] - Divine Spirit.jpg',
    311: '[311] - Draw Conditions.jpg',
    312: '[312] - Holy Strike.jpg',
    313: '[313] - Healing Touch.jpg',
    314: '[314] - Restore Life.jpg',
    315: '[315] - Vengeance.jpg',
    316: '[316] - To the Limit!.jpg',
    317: '[317] - Battle Rage.jpg',
    318: '[318] - Defy Pain.jpg',
    319: '[319] - Rush.jpg',
    320: '[320] - Hamstring.jpg',
    321: '[321] - Wild Blow.jpg',
    322: '[322] - Power Attack.jpg',
    323: '[323] - Desperation Blow.jpg',
    324: '[324] - Thrill of Victory.jpg',
    325: '[325] - Distracting Blow.jpg',
    326: "[326] - Protector's Strike.jpg",
    327: "[327] - Griffon's Sweep.jpg",
    328: '[328] - Pure Strike.jpg',
    329: '[329] - Skull Crack.jpg',
    330: '[330] - Cyclone Axe.jpg',
    331: '[331] - Hammer Bash.jpg',
    332: "[332] - Bull's Strike.jpg",
    333: '[333] - I Will Avenge You!.jpg',
    334: '[334] - Axe Rake.jpg',
    335: '[335] - Cleave.jpg',
    336: "[336] - Executioner's Strike.jpg",
    337: '[337] - Dismember.jpg',
    338: '[338] - Eviscerate.jpg',
    339: '[339] - Penetrating Blow.jpg',
    340: '[340] - Disrupting Chop.jpg',
    341: '[341] - Swift Chop.jpg',
    342: '[342] - Axe Twist.jpg',
    343: '[343] - For Great Justice!.jpg',
    344: '[344] - Flurry.jpg',
    345: '[345] - Defensive Stance.jpg',
    346: '[346] - Frenzy.jpg',
    347: '[347] - Endure Pain.jpg',
    348: '[348] - Watch Yourself!.jpg',
    349: '[349] - Sprint.jpg',
    350: '[350] - Belly Smash.jpg',
    351: '[351] - Mighty Blow.jpg',
    352: '[352] - Crushing Blow.jpg',
    353: '[353] - Crude Swing.jpg',
    354: '[354] - Earth Shaker.jpg',
    355: '[355] - Devastating Hammer.jpg',
    356: '[356] - Irresistible Blow.jpg',
    357: '[357] - Counter Blow.jpg',
    358: '[358] - Backbreaker.jpg',
    359: '[359] - Heavy Blow.jpg',
    360: '[360] - Staggering Blow.jpg',
    361: '[361] - Dolyak Signet.jpg',
    362: "[362] - Warrior's Cunning.jpg",
    363: '[363] - Shield Bash.jpg',
    364: '[364] - Charge!.jpg',
    365: '[365] - Victory Is Mine!.jpg',
    366: '[366] - Fear Me!.jpg',
    367: '[367] - Shields Up!.jpg',
    368: '[368] - I Will Survive!.jpg',
    370: '[370] - Berserker Stance.jpg',
    371: '[371] - Balanced Stance.jpg',
    372: "[372] - Gladiator's Defense.jpg",
    373: '[373] - Deflect Arrows.jpg',
    374: "[374] - Warrior's Endurance.jpg",
    375: '[375] - Dwarven Battle Stance.jpg',
    376: '[376] - Disciplined Stance.jpg',
    377: '[377] - Wary Stance.jpg',
    378: '[378] - Shield Stance.jpg',
    379: "[379] - Bull's Charge.jpg",
    380: "[380] - Bonetti's Defense.jpg",
    381: '[381] - Hundred Blades.jpg',
    382: '[382] - Sever Artery.jpg',
    383: '[383] - Galrath Slash.jpg',
    384: '[384] - Gash.jpg',
    385: '[385] - Final Thrust.jpg',
    386: '[386] - Seeking Blade.jpg',
    387: '[387] - Riposte.jpg',
    388: '[388] - Deadly Riposte.jpg',
    389: '[389] - Flourish.jpg',
    390: '[390] - Savage Slash.jpg',
    391: "[391] - Hunter's Shot.jpg",
    392: '[392] - Pin Down.jpg',
    393: '[393] - Crippling Shot.jpg',
    394: '[394] - Power Shot.jpg',
    395: '[395] - Barrage.jpg',
    396: '[396] - Dual Shot.jpg',
    397: '[397] - Quick Shot.jpg',
    398: '[398] - Penetrating Attack.jpg',
    399: '[399] - Distracting Shot.jpg',
    400: '[400] - Precision Shot.jpg',
    402: '[402] - Determined Shot.jpg',
    403: '[403] - Called Shot.jpg',
    404: '[404] - Poison Arrow.jpg',
    405: '[405] - Oath Shot.jpg',
    406: '[406] - Debilitating Shot.jpg',
    407: '[407] - Point Blank Shot.jpg',
    408: '[408] - Concussion Shot.jpg',
    409: '[409] - Punishing Shot.jpg',
    411: '[411] - Charm Animal.jpg',
    412: '[412] - Call of Protection.jpg',
    415: '[415] - Call of Haste.jpg',
    422: '[422] - Revive Animal.jpg',
    423: '[423] - Symbiotic Bond.jpg',
    424: '[424] - Throw Dirt.jpg',
    425: '[425] - Dodge.jpg',
    426: '[426] - Savage Shot.jpg',
    427: '[427] - Antidote Signet.jpg',
    428: '[428] - Incendiary Arrows.jpg',
    429: "[429] - Melandru's Arrows.jpg",
    430: "[430] - Marksman's Wager.jpg",
    431: '[431] - Ignite Arrows.jpg',
    432: '[432] - Read the Wind.jpg',
    433: '[433] - Kindle Arrows.jpg',
    434: '[434] - Choking Gas.jpg',
    435: '[435] - Apply Poison.jpg',
    436: '[436] - Comfort Animal.jpg',
    437: '[437] - Bestial Pounce.jpg',
    438: '[438] - Maiming Strike.jpg',
    439: '[439] - Feral Lunge.jpg',
    440: '[440] - Scavenger Strike.jpg',
    441: "[441] - Melandru's Assault.jpg",
    442: '[442] - Ferocious Strike.jpg',
    443: "[443] - Predator's Pounce.jpg",
    444: '[444] - Brutal Strike.jpg',
    445: '[445] - Disrupting Lunge.jpg',
    446: '[446] - Troll Unguent.jpg',
    447: "[447] - Otyugh's Cry.jpg",
    448: '[448] - Escape.jpg',
    449: '[449] - Practiced Stance.jpg',
    450: '[450] - Whirling Defense.jpg',
    451: "[451] - Melandru's Resilience.jpg",
    452: "[452] - Dryder's Defenses.jpg",
    453: '[453] - Lightning Reflexes.jpg',
    454: "[454] - Tiger's Fury.jpg",
    455: '[455] - Storm Chaser.jpg',
    456: "[456] - Serpent's Quickness.jpg",
    457: '[457] - Dust Trap.jpg',
    458: '[458] - Barbed Trap.jpg',
    459: '[459] - Flame Trap.jpg',
    460: '[460] - Healing Spring.jpg',
    461: '[461] - Spike Trap.jpg',
    462: '[462] - Winter.jpg',
    463: '[463] - Winnowing.jpg',
    464: '[464] - Edge of Extinction.jpg',
    465: '[465] - Greater Conflagration.jpg',
    466: '[466] - Conflagration.jpg',
    467: '[467] - Fertile Season.jpg',
    468: '[468] - Symbiosis.jpg',
    469: '[469] - Primal Echoes.jpg',
    470: '[470] - Predatory Season.jpg',
    471: '[471] - Frozen Soil.jpg',
    472: '[472] - Favorable Winds.jpg',
    474: '[474] - Energizing Wind.jpg',
    475: '[475] - Quickening Zephyr.jpg',
    476: "[476] - Nature's Renewal.jpg",
    477: '[477] - Muddy Terrain.jpg',
    570: '[570] - Mark of Insecurity.jpg',
    571: '[571] - Disrupting Dagger.jpg',
    572: '[572] - Deadly Paradox.jpg',
    763: '[763] - Jaundiced Gaze.jpg',
    764: '[764] - Wail of Doom.jpg',
    766: '[766] - Gaze of Contempt.jpg',
    769: "[769] - Viper's Defense.jpg",
    770: '[770] - Return.jpg',
    771: '[771] - Aura of Displacement.jpg',
    772: '[772] - Generous Was Tsungrai.jpg',
    773: '[773] - Mighty Was Vorizun.jpg',
    775: '[775] - Death Blossom.jpg',
    776: '[776] - Twisting Fangs.jpg',
    777: '[777] - Horns of the Ox.jpg',
    778: '[778] - Falling Spider.jpg',
    779: '[779] - Black Lotus Strike.jpg',
    780: '[780] - Fox Fangs.jpg',
    781: '[781] - Moebius Strike.jpg',
    782: '[782] - Jagged Strike.jpg',
    783: '[783] - Unsuspecting Strike.jpg',
    784: '[784] - Entangling Asp.jpg',
    785: '[785] - Mark of Death.jpg',
    786: '[786] - Iron Palm.jpg',
    787: '[787] - Resilient Weapon.jpg',
    788: '[788] - Blind Was Mingson.jpg',
    789: '[789] - Grasping Was Kuurong.jpg',
    790: '[790] - Vengeful Was Khanhei.jpg',
    791: '[791] - Flesh of My Flesh.jpg',
    792: '[792] - Splinter Weapon.jpg',
    793: '[793] - Weapon of Warding.jpg',
    794: '[794] - Wailing Weapon.jpg',
    795: '[795] - Nightmare Weapon.jpg',
    799: '[799] - Beguiling Haze.jpg',
    800: '[800] - Enduring Toxin.jpg',
    801: '[801] - Shroud of Silence.jpg',
    802: '[802] - Expose Defenses.jpg',
    803: '[803] - Power Leech.jpg',
    804: '[804] - Arcane Languor.jpg',
    805: '[805] - Animate Vampiric Horror.jpg',
    806: "[806] - Cultist's Fervor.jpg",
    808: "[808] - Reaper's Mark.jpg",
    809: '[809] - Shatterstone.jpg',
    810: "[810] - Protector's Defense.jpg",
    811: '[811] - Run as One.jpg',
    812: '[812] - Defiant Was Xinrae.jpg',
    813: "[813] - Lyssa's Aura.jpg",
    814: '[814] - Shadow Refuge.jpg',
    815: '[815] - Scorpion Wire.jpg',
    816: '[816] - Mirrored Stance.jpg',
    817: '[817] - Discord.jpg',
    818: '[818] - Well of Weariness.jpg',
    819: '[819] - Vampiric Spirit.jpg',
    820: '[820] - Depravity.jpg',
    821: '[821] - Icy Veins.jpg',
    822: '[822] - Weaken Knees.jpg',
    823: '[823] - Burning Speed.jpg',
    824: '[824] - Lava Arrows.jpg',
    825: '[825] - Bed of Coals.jpg',
    826: '[826] - Shadow Form.jpg',
    827: '[827] - Siphon Strength.jpg',
    828: '[828] - Vile Miasma.jpg',
    830: '[830] - Ray of Judgment.jpg',
    831: '[831] - Primal Rage.jpg',
    832: '[832] - Animate Flesh Golem.jpg',
    834: '[834] - Reckless Haste.jpg',
    835: '[835] - Blood Bond.jpg',
    836: '[836] - Ride the Lightning.jpg',
    837: '[837] - Energy Boon.jpg',
    838: "[838] - Dwayna's Sorrow.jpg",
    839: '[839] - Retreat!.jpg',
    840: '[840] - Poisoned Heart.jpg',
    841: '[841] - Fetid Ground.jpg',
    842: '[842] - Arc Lightning.jpg',
    843: '[843] - Gust.jpg',
    844: '[844] - Churning Earth.jpg',
    845: '[845] - Liquid Flame.jpg',
    846: '[846] - Steam.jpg',
    847: '[847] - Boon Signet.jpg',
    848: '[848] - Reverse Hex.jpg',
    849: '[849] - Lacerating Chop.jpg',
    850: '[850] - Fierce Blow.jpg',
    851: '[851] - Sun and Moon Slash.jpg',
    852: '[852] - Splinter Shot.jpg',
    853: "[853] - Melandru's Shot.jpg",
    854: '[854] - Snare.jpg',
    858: '[858] - Dancing Daggers.jpg',
    859: '[859] - Conjure Nightmare.jpg',
    860: '[860] - Signet of Disruption.jpg',
    862: '[862] - Ravenous Gaze.jpg',
    863: '[863] - Order of Apostasy.jpg',
    864: '[864] - Oppressive Gaze.jpg',
    865: '[865] - Lightning Hammer.jpg',
    866: '[866] - Vapor Blade.jpg',
    867: '[867] - Healing Light.jpg',
    869: '[869] - Coward!.jpg',
    870: '[870] - Pestilence.jpg',
    871: '[871] - Shadowsong.jpg',
    876: '[876] - Signet of Shadows.jpg',
    877: "[877] - Lyssa's Balance.jpg",
    878: '[878] - Visions of Regret.jpg',
    879: '[879] - Illusion of Pain.jpg',
    880: '[880] - Stolen Speed.jpg',
    881: '[881] - Ether Signet.jpg',
    882: '[882] - Signet of Disenchantment.jpg',
    883: '[883] - Vocal Minority.jpg',
    884: '[884] - Searing Flames.jpg',
    885: '[885] - Shield Guardian.jpg',
    886: '[886] - Restful Breeze.jpg',
    887: '[887] - Signet of Rejuvenation.jpg',
    888: '[888] - Whirling Axe.jpg',
    889: '[889] - Forceful Blow.jpg',
    891: '[891] - None Shall Pass!.jpg',
    892: '[892] - Quivering Blade.jpg',
    893: '[893] - Seeking Arrows.jpg',
    898: '[898] - Overload.jpg',
    899: '[899] - Images of Remorse.jpg',
    900: '[900] - Shared Burden.jpg',
    901: '[901] - Soul Bind.jpg',
    902: '[902] - Blood of the Aggressor.jpg',
    903: '[903] - Icy Prism.jpg',
    904: '[904] - Furious Axe.jpg',
    905: '[905] - Auspicious Blow.jpg',
    906: '[906] - On Your Knees!.jpg',
    907: '[907] - Dragon Slash.jpg',
    908: "[908] - Marauder's Shot.jpg",
    909: '[909] - Focused Shot.jpg',
    910: '[910] - Spirit Rift.jpg',
    911: '[911] - Union.jpg',
    913: '[913] - Tranquil Was Tanasen.jpg',
    914: '[914] - Consume Soul.jpg',
    915: '[915] - Spirit Light.jpg',
    916: '[916] - Lamentation.jpg',
    917: '[917] - Rupture Soul.jpg',
    918: '[918] - Spirit to Flesh.jpg',
    919: '[919] - Spirit Burn.jpg',
    920: '[920] - Destruction.jpg',
    921: '[921] - Dissonance.jpg',
    923: '[923] - Disenchantment.jpg',
    925: '[925] - Recall.jpg',
    926: '[926] - Sharpen Daggers.jpg',
    927: '[927] - Shameful Fear.jpg',
    928: '[928] - Shadow Shroud.jpg',
    929: '[929] - Shadow of Haste.jpg',
    930: '[930] - Auspicious Incantation.jpg',
    931: '[931] - Power Return.jpg',
    932: '[932] - Complicate.jpg',
    933: '[933] - Shatter Storm.jpg',
    934: '[934] - Unnatural Signet.jpg',
    935: '[935] - Rising Bile.jpg',
    936: '[936] - Envenom Enchantments.jpg',
    937: '[937] - Shockwave.jpg',
    938: '[938] - Ward of Stability.jpg',
    939: '[939] - Icy Shackles.jpg',
    941: '[941] - Blessed Light.jpg',
    942: '[942] - Withdraw Hexes.jpg',
    943: '[943] - Extinguish.jpg',
    944: '[944] - Signet of Strength.jpg',
    946: "[946] - Trapper's Focus.jpg",
    947: '[947] - Brambles.jpg',
    948: '[948] - Desperate Strike.jpg',
    949: '[949] - Way of the Fox.jpg',
    950: '[950] - Shadowy Burden.jpg',
    951: '[951] - Siphon Speed.jpg',
    952: "[952] - Death's Charge.jpg",
    953: '[953] - Power Flux.jpg',
    954: '[954] - Expel Hexes.jpg',
    955: '[955] - Rip Enchantment.jpg',
    957: '[957] - Spell Shield.jpg',
    958: '[958] - Healing Whisper.jpg',
    959: '[959] - Ethereal Light.jpg',
    960: '[960] - Release Enchantments.jpg',
    961: '[961] - Lacerate.jpg',
    962: '[962] - Spirit Transfer.jpg',
    963: '[963] - Restoration.jpg',
    964: '[964] - Vengeful Weapon.jpg',
    973: '[973] - Blinding Powder.jpg',
    974: '[974] - Mantis Touch.jpg',
    975: '[975] - Exhausting Assault.jpg',
    976: '[976] - Repeating Strike.jpg',
    977: '[977] - Way of the Lotus.jpg',
    978: '[978] - Mark of Instability.jpg',
    979: '[979] - Mistrust.jpg',
    980: '[980] - Feast of Souls.jpg',
    981: '[981] - Recuperation.jpg',
    982: '[982] - Shelter.jpg',
    983: '[983] - Weapon of Shadow.jpg',
    985: '[985] - Caltrops.jpg',
    986: '[986] - Nine Tail Strike.jpg',
    987: '[987] - Way of the Empty Palm.jpg',
    988: '[988] - Temple Strike.jpg',
    989: '[989] - Golden Phoenix Strike.jpg',
    990: '[990] - Expunge Enchantments.jpg',
    991: '[991] - Deny Hexes.jpg',
    992: '[992] - Triple Chop.jpg',
    993: '[993] - Enraged Smash.jpg',
    994: '[994] - Renewing Smash.jpg',
    995: '[995] - Tiger Stance.jpg',
    996: '[996] - Standing Slash.jpg',
    997: '[997] - Famine.jpg',
    1014: "[1014] - Let's Get 'Em!.jpg",
    1018: '[1018] - Critical Eye.jpg',
    1019: '[1019] - Critical Strike.jpg',
    1020: '[1020] - Blades of Steel.jpg',
    1021: '[1021] - Jungle Strike.jpg',
    1022: '[1022] - Wild Strike.jpg',
    1023: '[1023] - Leaping Mantis Sting.jpg',
    1024: '[1024] - Black Mantis Thrust.jpg',
    1025: '[1025] - Disrupting Stab.jpg',
    1026: '[1026] - Golden Lotus Strike.jpg',
    1027: '[1027] - Critical Defenses.jpg',
    1028: '[1028] - Way of Perfection.jpg',
    1029: '[1029] - Dark Apostasy.jpg',
    1030: "[1030] - Locust's Fury.jpg",
    1031: '[1031] - Shroud of Distress.jpg',
    1032: '[1032] - Heart of Shadow.jpg',
    1033: '[1033] - Impale.jpg',
    1034: '[1034] - Seeping Wound.jpg',
    1035: "[1035] - Assassin's Promise.jpg",
    1036: '[1036] - Signet of Malice.jpg',
    1037: '[1037] - Dark Escape.jpg',
    1038: '[1038] - Crippling Dagger.jpg',
    1040: '[1040] - Spirit Walk.jpg',
    1041: '[1041] - Unseen Fury.jpg',
    1042: '[1042] - Flashing Blades.jpg',
    1043: '[1043] - Dash.jpg',
    1044: '[1044] - Dark Prison.jpg',
    1045: '[1045] - Palm Strike.jpg',
    1048: '[1048] - Revealed Enchantment.jpg',
    1049: '[1049] - Revealed Hex.jpg',
    1052: '[1052] - Accumulated Pain.jpg',
    1053: '[1053] - Psychic Distraction.jpg',
    1054: "[1054] - Ancestor's Visage.jpg",
    1055: '[1055] - Recurring Insecurity.jpg',
    1056: "[1056] - Kitah's Burden.jpg",
    1057: '[1057] - Psychic Instability.jpg',
    1059: '[1059] - Hex Eater Signet.jpg',
    1061: '[1061] - Feedback.jpg',
    1062: '[1062] - Arcane Larceny.jpg',
    1066: '[1066] - Spoil Victor.jpg',
    1067: '[1067] - Lifebane Strike.jpg',
    1068: '[1068] - Bitter Chill.jpg',
    1069: '[1069] - Taste of Pain.jpg',
    1070: '[1070] - Defile Enchantments.jpg',
    1071: '[1071] - Shivers of Dread.jpg',
    1075: '[1075] - Vampiric Swarm.jpg',
    1076: '[1076] - Blood Drinker.jpg',
    1077: '[1077] - Vampiric Bite.jpg',
    1078: "[1078] - Wallow's Bite.jpg",
    1079: '[1079] - Enfeebling Touch.jpg',
    1081: "[1081] - Teinai's Wind.jpg",
    1082: '[1082] - Shock Arrow.jpg',
    1083: '[1083] - Unsteady Ground.jpg',
    1084: '[1084] - Sliver Armor.jpg',
    1085: '[1085] - Ash Blast.jpg',
    1086: "[1086] - Dragon's Stomp.jpg",
    1088: '[1088] - Second Wind.jpg',
    1090: '[1090] - Smoldering Embers.jpg',
    1091: '[1091] - Double Dragon.jpg',
    1093: "[1093] - Teinai's Heat.jpg",
    1094: '[1094] - Breath of Fire.jpg',
    1095: '[1095] - Star Burst.jpg',
    1096: '[1096] - Glyph of Essence.jpg',
    1097: "[1097] - Teinai's Prison.jpg",
    1098: '[1098] - Mirror of Ice.jpg',
    1099: "[1099] - Teinai's Crystals.jpg",
    1113: "[1113] - Kirin's Wrath.jpg",
    1114: '[1114] - Spirit Bond.jpg',
    1115: '[1115] - Air of Enchantment.jpg',
    1117: "[1117] - Heaven's Delight.jpg",
    1118: '[1118] - Healing Burst.jpg',
    1119: "[1119] - Karei's Healing Circle.jpg",
    1120: "[1120] - Jamei's Gaze.jpg",
    1121: '[1121] - Gift of Health.jpg',
    1123: '[1123] - Life Sheath.jpg',
    1126: '[1126] - Empathic Removal.jpg',
    1128: '[1128] - Resurrection Chant.jpg',
    1129: '[1129] - Word of Censure.jpg',
    1130: '[1130] - Spear of Light.jpg',
    1131: '[1131] - Stonesoul Strike.jpg',
    1133: '[1133] - Drunken Blow.jpg',
    1134: "[1134] - Leviathan's Sweep.jpg",
    1135: '[1135] - Jaizhenju Strike.jpg',
    1136: '[1136] - Penetrating Chop.jpg',
    1137: '[1137] - Yeti Smash.jpg',
    1140: '[1140] - Storm of Swords.jpg',
    1141: '[1141] - You Will Die!.jpg',
    1142: '[1142] - Auspicious Parry.jpg',
    1144: '[1144] - Silverwing Slash.jpg',
    1146: '[1146] - Shove.jpg',
    1191: '[1191] - Sundering Attack.jpg',
    1192: "[1192] - Zojun's Shot.jpg",
    1194: '[1194] - Predatory Bond.jpg',
    1195: '[1195] - Heal as One.jpg',
    1196: "[1196] - Zojun's Haste.jpg",
    1197: '[1197] - Needling Shot.jpg',
    1198: '[1198] - Broad Head Arrow.jpg',
    1199: '[1199] - Glass Arrows.jpg',
    1200: "[1200] - Archer's Signet.jpg",
    1201: '[1201] - Savage Pounce.jpg',
    1202: '[1202] - Enraged Lunge.jpg',
    1203: '[1203] - Bestial Mauling.jpg',
    1205: '[1205] - Poisonous Bite.jpg',
    1206: '[1206] - Pounce.jpg',
    1209: '[1209] - Bestial Fury.jpg',
    1211: "[1211] - Viper's Nest.jpg",
    1212: '[1212] - Equinox.jpg',
    1213: '[1213] - Tranquility.jpg',
    1215: '[1215] - Clamor of Souls.jpg',
    1217: '[1217] - Ritual Lord.jpg',
    1218: '[1218] - Cruel Was Daoshen.jpg',
    1219: '[1219] - Protective Was Kaolai.jpg',
    1220: '[1220] - Attuned Was Songkai.jpg',
    1221: '[1221] - Resilient Was Xiko.jpg',
    1222: '[1222] - Lively Was Naomei.jpg',
    1223: '[1223] - Anguished Was Lingwah.jpg',
    1224: '[1224] - Draw Spirit.jpg',
    1225: '[1225] - Channeled Strike.jpg',
    1226: '[1226] - Spirit Boon Strike.jpg',
    1227: '[1227] - Essence Strike.jpg',
    1228: '[1228] - Spirit Siphon.jpg',
    1229: '[1229] - Explosive Growth.jpg',
    1230: '[1230] - Boon of Creation.jpg',
    1231: '[1231] - Spirit Channeling.jpg',
    1232: '[1232] - Armor of Unfeeling.jpg',
    1233: '[1233] - Soothing Memories.jpg',
    1234: '[1234] - Mend Body and Soul.jpg',
    1235: '[1235] - Dulled Weapon.jpg',
    1236: '[1236] - Binding Chains.jpg',
    1237: '[1237] - Painful Bond.jpg',
    1238: '[1238] - Signet of Creation.jpg',
    1239: '[1239] - Signet of Spirits.jpg',
    1240: '[1240] - Soul Twisting.jpg',
    1244: '[1244] - Ghostly Haste.jpg',
    1245: '[1245] - Gaze from Beyond.jpg',
    1246: "[1246] - Ancestors' Rage.jpg",
    1247: '[1247] - Pain.jpg',
    1249: '[1249] - Displacement.jpg',
    1250: '[1250] - Preservation.jpg',
    1251: '[1251] - Life.jpg',
    1252: '[1252] - Earthbind.jpg',
    1253: '[1253] - Bloodsong.jpg',
    1255: '[1255] - Wanderlust.jpg',
    1257: '[1257] - Spirit Light Weapon.jpg',
    1258: '[1258] - Brutal Weapon.jpg',
    1259: '[1259] - Guided Weapon.jpg',
    1260: '[1260] - Meekness.jpg',
    1261: '[1261] - Frigid Armor.jpg',
    1262: '[1262] - Healing Ring.jpg',
    1263: '[1263] - Renew Life.jpg',
    1264: '[1264] - Doom.jpg',
    1265: "[1265] - Wielder's Boon.jpg",
    1266: '[1266] - Soothing.jpg',
    1267: '[1267] - Vital Weapon.jpg',
    1268: '[1268] - Weapon of Quickening.jpg',
    1269: '[1269] - Signet of Rage.jpg',
    1333: '[1333] - Extend Conditions.jpg',
    1334: '[1334] - Hypochondria.jpg',
    1335: "[1335] - Wastrel's Demise.jpg",
    1336: '[1336] - Spiritual Pain.jpg',
    1337: '[1337] - Drain Delusions.jpg',
    1338: '[1338] - Persistence of Memory.jpg',
    1339: '[1339] - Symbols of Inspiration.jpg',
    1340: '[1340] - Symbolic Celerity.jpg',
    1341: '[1341] - Frustration.jpg',
    1342: '[1342] - Tease.jpg',
    1343: '[1343] - Ether Phantom.jpg',
    1344: '[1344] - Web of Disruption.jpg',
    1345: "[1345] - Enchanter's Conundrum.jpg",
    1346: '[1346] - Signet of Illusions.jpg',
    1347: '[1347] - Discharge Enchantment.jpg',
    1348: '[1348] - Hex Eater Vortex.jpg',
    1349: '[1349] - Mirror of Disenchantment.jpg',
    1350: '[1350] - Simple Thievery.jpg',
    1351: '[1351] - Animate Shambling Horror.jpg',
    1352: '[1352] - Order of Undeath.jpg',
    1353: '[1353] - Putrid Flesh.jpg',
    1354: '[1354] - Feast for the Dead.jpg',
    1355: '[1355] - Jagged Bones.jpg',
    1356: '[1356] - Contagion.jpg',
    1358: '[1358] - Ulcerous Lungs.jpg',
    1359: '[1359] - Pain of Disenchantment.jpg',
    1360: '[1360] - Mark of Fury.jpg',
    1362: '[1362] - Corrupt Enchantment.jpg',
    1363: '[1363] - Signet of Sorrow.jpg',
    1364: '[1364] - Signet of Suffering.jpg',
    1365: '[1365] - Signet of Lost Souls.jpg',
    1366: '[1366] - Well of Darkness.jpg',
    1367: '[1367] - Blinding Surge.jpg',
    1368: '[1368] - Chilling Winds.jpg',
    1369: '[1369] - Lightning Bolt.jpg',
    1370: "[1370] - Storm Djinn's Haste.jpg",
    1371: '[1371] - Stone Striker.jpg',
    1372: '[1372] - Sandstorm.jpg',
    1373: '[1373] - Stone Sheath.jpg',
    1374: '[1374] - Ebon Hawk.jpg',
    1375: '[1375] - Stoneflesh Aura.jpg',
    1376: '[1376] - Glyph of Restoration.jpg',
    1377: '[1377] - Ether Prism.jpg',
    1378: '[1378] - Master of Magic.jpg',
    1379: '[1379] - Glowing Gaze.jpg',
    1380: '[1380] - Savannah Heat.jpg',
    1381: "[1381] - Flame Djinn's Haste.jpg",
    1382: '[1382] - Freezing Gust.jpg',
    1390: "[1390] - Judge's Intervention.jpg",
    1391: '[1391] - Supportive Spirit.jpg',
    1392: '[1392] - Watchful Healing.jpg',
    1393: "[1393] - Healer's Boon.jpg",
    1394: "[1394] - Healer's Covenant.jpg",
    1395: "[1395] - Balthazar's Pendulum.jpg",
    1396: '[1396] - Words of Comfort.jpg',
    1397: '[1397] - Light of Deliverance.jpg',
    1398: '[1398] - Scourge Enchantment.jpg',
    1399: '[1399] - Shield of Absorption.jpg',
    1400: '[1400] - Reversal of Damage.jpg',
    1401: '[1401] - Mending Touch.jpg',
    1402: '[1402] - Critical Chop.jpg',
    1403: '[1403] - Agonizing Chop.jpg',
    1404: '[1404] - Flail.jpg',
    1405: '[1405] - Charging Strike.jpg',
    1406: '[1406] - Headbutt.jpg',
    1407: "[1407] - Lion's Comfort.jpg",
    1408: '[1408] - Rage of the Ntouka.jpg',
    1409: '[1409] - Mokele Smash.jpg',
    1410: '[1410] - Overbearing Smash.jpg',
    1411: '[1411] - Signet of Stamina.jpg',
    1412: "[1412] - You're All Alone!.jpg",
    1413: '[1413] - Burst of Aggression.jpg',
    1414: '[1414] - Enraging Charge.jpg',
    1415: '[1415] - Crippling Slash.jpg',
    1416: '[1416] - Barbarous Slice.jpg',
    1465: '[1465] - Prepared Shot.jpg',
    1466: '[1466] - Burning Arrow.jpg',
    1467: '[1467] - Arcing Shot.jpg',
    1468: '[1468] - Strike as One.jpg',
    1469: '[1469] - Crossfire.jpg',
    1470: '[1470] - Barbed Arrows.jpg',
    1471: "[1471] - Scavenger's Focus.jpg",
    1472: '[1472] - Toxicity.jpg',
    1473: '[1473] - Quicksand.jpg',
    1474: "[1474] - Storm's Embrace.jpg",
    1475: "[1475] - Trapper's Speed.jpg",
    1476: '[1476] - Tripwire.jpg',
    1478: '[1478] - Renewing Surge.jpg',
    1479: '[1479] - Offering of Spirit.jpg',
    1480: "[1480] - Spirit's Gift.jpg",
    1481: '[1481] - Death Pact Signet.jpg',
    1482: '[1482] - Reclaim Essence.jpg',
    1483: '[1483] - Banishing Strike.jpg',
    1484: '[1484] - Mystic Sweep.jpg',
    1485: "[1485] - Eremite's Attack.jpg",
    1486: '[1486] - Reap Impurities.jpg',
    1487: '[1487] - Twin Moon Sweep.jpg',
    1488: '[1488] - Victorious Sweep.jpg',
    1489: '[1489] - Irresistible Sweep.jpg',
    1490: '[1490] - Pious Assault.jpg',
    1491: '[1491] - Mystic Twister.jpg',
    1493: "[1493] - Grenth's Fingers.jpg",
    1495: '[1495] - Aura of Thorns.jpg',
    1496: "[1496] - Balthazar's Rage.jpg",
    1497: '[1497] - Dust Cloak.jpg',
    1498: '[1498] - Staggering Force.jpg',
    1499: '[1499] - Pious Renewal.jpg',
    1500: '[1500] - Mirage Cloak.jpg',
    1502: '[1502] - Arcane Zeal.jpg',
    1503: '[1503] - Mystic Vigor.jpg',
    1504: '[1504] - Watchful Intervention.jpg',
    1505: '[1505] - Vow of Piety.jpg',
    1506: '[1506] - Vital Boon.jpg',
    1507: '[1507] - Heart of Holy Flame.jpg',
    1508: '[1508] - Extend Enchantments.jpg',
    1509: '[1509] - Faithful Intervention.jpg',
    1510: '[1510] - Sand Shards.jpg',
    1512: "[1512] - Lyssa's Haste.jpg",
    1513: '[1513] - Guiding Hands.jpg',
    1514: '[1514] - Fleeting Stability.jpg',
    1515: '[1515] - Armor of Sanctity.jpg',
    1516: '[1516] - Mystic Regeneration.jpg',
    1517: '[1517] - Vow of Silence.jpg',
    1518: '[1518] - Avatar of Balthazar.jpg',
    1519: '[1519] - Avatar of Dwayna.jpg',
    1520: '[1520] - Avatar of Grenth.jpg',
    1521: '[1521] - Avatar of Lyssa.jpg',
    1522: '[1522] - Avatar of Melandru.jpg',
    1523: '[1523] - Meditation.jpg',
    1524: "[1524] - Eremite's Zeal.jpg",
    1525: '[1525] - Natural Healing.jpg',
    1526: '[1526] - Imbue Health.jpg',
    1527: '[1527] - Mystic Healing.jpg',
    1528: "[1528] - Dwayna's Touch.jpg",
    1529: '[1529] - Pious Restoration.jpg',
    1530: '[1530] - Signet of Pious Light.jpg',
    1531: '[1531] - Intimidating Aura.jpg',
    1532: '[1532] - Mystic Sandstorm.jpg',
    1533: '[1533] - Winds of Disenchantment.jpg',
    1534: '[1534] - Rending Touch.jpg',
    1535: '[1535] - Crippling Sweep.jpg',
    1536: '[1536] - Wounding Strike.jpg',
    1537: '[1537] - Wearying Strike.jpg',
    1538: "[1538] - Lyssa's Assault.jpg",
    1539: '[1539] - Chilling Victory.jpg',
    1540: '[1540] - Conviction.jpg',
    1541: '[1541] - Enchanted Haste.jpg',
    1542: '[1542] - Pious Concentration.jpg',
    1543: '[1543] - Pious Haste.jpg',
    1544: '[1544] - Whirling Charge.jpg',
    1545: '[1545] - Test of Faith.jpg',
    1546: '[1546] - Blazing Spear.jpg',
    1547: '[1547] - Mighty Throw.jpg',
    1548: '[1548] - Cruel Spear.jpg',
    1549: "[1549] - Harrier's Toss.jpg",
    1550: '[1550] - Unblockable Throw.jpg',
    1551: '[1551] - Spear of Lightning.jpg',
    1552: '[1552] - Wearying Spear.jpg',
    1553: '[1553] - Anthem of Fury.jpg',
    1554: '[1554] - Crippling Anthem.jpg',
    1555: '[1555] - Defensive Anthem.jpg',
    1556: '[1556] - Godspeed.jpg',
    1557: '[1557] - Anthem of Flame.jpg',
    1558: '[1558] - Go for the Eyes!.jpg',
    1559: '[1559] - Anthem of Envy.jpg',
    1560: '[1560] - Song of Power.jpg',
    1561: '[1561] - Zealous Anthem.jpg',
    1562: '[1562] - Aria of Zeal.jpg',
    1563: '[1563] - Lyric of Zeal.jpg',
    1564: '[1564] - Ballad of Restoration.jpg',
    1565: '[1565] - Chorus of Restoration.jpg',
    1566: '[1566] - Aria of Restoration.jpg',
    1567: '[1567] - Song of Concentration.jpg',
    1568: '[1568] - Anthem of Guidance.jpg',
    1569: '[1569] - Energizing Chorus.jpg',
    1570: '[1570] - Song of Purification.jpg',
    1571: '[1571] - Hexbreaker Aria.jpg',
    1572: '[1572] - Brace Yourself!.jpg',
    1573: '[1573] - Awe.jpg',
    1574: '[1574] - Enduring Harmony.jpg',
    1575: '[1575] - Blazing Finale.jpg',
    1576: '[1576] - Burning Refrain.jpg',
    1577: '[1577] - Finale of Restoration.jpg',
    1578: '[1578] - Mending Refrain.jpg',
    1579: '[1579] - Purifying Finale.jpg',
    1580: '[1580] - Bladeturn Refrain.jpg',
    1581: '[1581] - Glowing Signet.jpg',
    1583: "[1583] - Leader's Zeal.jpg",
    1584: "[1584] - Leader's Comfort.jpg",
    1585: '[1585] - Signet of Synergy.jpg',
    1586: '[1586] - Angelic Protection.jpg',
    1587: '[1587] - Angelic Bond.jpg',
    1588: '[1588] - Cautery Signet.jpg',
    1589: '[1589] - Stand Your Ground!.jpg',
    1590: '[1590] - Lead the Way!.jpg',
    1591: '[1591] - Make Haste!.jpg',
    1592: '[1592] - We Shall Return!.jpg',
    1593: '[1593] - Never Give Up!.jpg',
    1594: '[1594] - Help Me!.jpg',
    1595: '[1595] - Fall Back!.jpg',
    1596: '[1596] - Incoming!.jpg',
    1597: "[1597] - They're on Fire!.jpg",
    1598: '[1598] - Never Surrender!.jpg',
    1599: "[1599] - It's Just a Flesh Wound..jpg",
    1600: '[1600] - Barbed Spear.jpg',
    1601: '[1601] - Vicious Attack.jpg',
    1602: '[1602] - Stunning Strike.jpg',
    1603: '[1603] - Merciless Spear.jpg',
    1604: '[1604] - Disrupting Throw.jpg',
    1605: '[1605] - Wild Throw.jpg',
    1633: '[1633] - Malicious Strike.jpg',
    1634: '[1634] - Shattering Assault.jpg',
    1635: '[1635] - Golden Skull Strike.jpg',
    1636: '[1636] - Black Spider Strike.jpg',
    1637: '[1637] - Golden Fox Strike.jpg',
    1638: '[1638] - Deadly Haste.jpg',
    1639: "[1639] - Assassin's Remedy.jpg",
    1640: "[1640] - Fox's Promise.jpg",
    1641: '[1641] - Feigned Neutrality.jpg',
    1642: '[1642] - Hidden Caltrops.jpg',
    1643: '[1643] - Assault Enchantments.jpg',
    1644: "[1644] - Wastrel's Collapse.jpg",
    1645: '[1645] - Lift Enchantment.jpg',
    1646: '[1646] - Augury of Death.jpg',
    1647: '[1647] - Signet of Toxic Shock.jpg',
    1648: '[1648] - Signet of Twilight.jpg',
    1649: '[1649] - Way of the Assassin.jpg',
    1650: '[1650] - Shadow Walk.jpg',
    1651: "[1651] - Death's Retreat.jpg",
    1652: '[1652] - Shadow Prison.jpg',
    1653: '[1653] - Swap.jpg',
    1654: '[1654] - Shadow Meld.jpg',
    1655: '[1655] - Price of Pride.jpg',
    1656: '[1656] - Air of Disenchantment.jpg',
    1657: '[1657] - Signet of Clumsiness.jpg',
    1658: '[1658] - Symbolic Posture.jpg',
    1659: '[1659] - Toxic Chill.jpg',
    1660: '[1660] - Well of Silence.jpg',
    1661: '[1661] - Glowstone.jpg',
    1662: '[1662] - Mind Blast.jpg',
    1663: '[1663] - Elemental Flame.jpg',
    1664: '[1664] - Invoke Lightning.jpg',
    1683: '[1683] - Pensive Guardian.jpg',
    1684: "[1684] - Scribe's Insight.jpg",
    1685: '[1685] - Holy Haste.jpg',
    1686: '[1686] - Glimmer of Light.jpg',
    1687: '[1687] - Zealous Benediction.jpg',
    1688: "[1688] - Defender's Zeal.jpg",
    1689: '[1689] - Signet of Mystic Wrath.jpg',
    1690: '[1690] - Signet of Removal.jpg',
    1691: '[1691] - Dismiss Condition.jpg',
    1692: '[1692] - Divert Hexes.jpg',
    1693: '[1693] - Counterattack.jpg',
    1694: '[1694] - Magehunter Strike.jpg',
    1695: "[1695] - Soldier's Strike.jpg",
    1696: '[1696] - Decapitate.jpg',
    1697: "[1697] - Magehunter's Smash.jpg",
    1698: "[1698] - Soldier's Stance.jpg",
    1699: "[1699] - Soldier's Defense.jpg",
    1700: '[1700] - Frenzied Defense.jpg',
    1701: '[1701] - Steady Stance.jpg',
    1702: '[1702] - Steelfang Slash.jpg',
    1719: '[1719] - Screaming Shot.jpg',
    1720: '[1720] - Keen Arrow.jpg',
    1721: '[1721] - Rampage as One.jpg',
    1722: '[1722] - Forked Arrow.jpg',
    1723: '[1723] - Disrupting Accuracy.jpg',
    1724: "[1724] - Expert's Dexterity.jpg",
    1725: '[1725] - Roaring Winds.jpg',
    1726: '[1726] - Magebane Shot.jpg',
    1727: '[1727] - Natural Stride.jpg',
    1728: "[1728] - Heket's Rampage.jpg",
    1729: '[1729] - Smoke Trap.jpg',
    1730: '[1730] - Infuriating Heat.jpg',
    1731: '[1731] - Vocal Was Sogolon.jpg',
    1732: '[1732] - Destructive Was Glaive.jpg',
    1733: "[1733] - Wielder's Strike.jpg",
    1734: '[1734] - Gaze of Fury.jpg',
    1736: "[1736] - Spirit's Strength.jpg",
    1737: "[1737] - Wielder's Zeal.jpg",
    1738: '[1738] - Sight Beyond Sight.jpg',
    1739: '[1739] - Renewing Memories.jpg',
    1740: "[1740] - Wielder's Remedy.jpg",
    1741: '[1741] - Ghostmirror Light.jpg',
    1742: '[1742] - Signet of Ghostly Might.jpg',
    1743: '[1743] - Signet of Binding.jpg',
    1744: "[1744] - Caretaker's Charge.jpg",
    1745: '[1745] - Anguish.jpg',
    1747: '[1747] - Empowerment.jpg',
    1748: '[1748] - Recovery.jpg',
    1749: '[1749] - Weapon of Fury.jpg',
    1750: "[1750] - Xinrae's Weapon.jpg",
    1751: "[1751] - Warmonger's Weapon.jpg",
    1752: '[1752] - Weapon of Remedy.jpg',
    1753: '[1753] - Rending Sweep.jpg',
    1754: '[1754] - Onslaught.jpg',
    1755: '[1755] - Mystic Corruption.jpg',
    1756: "[1756] - Grenth's Grasp.jpg",
    1757: '[1757] - Veil of Thorns.jpg',
    1758: "[1758] - Harrier's Grasp.jpg",
    1759: '[1759] - Vow of Strength.jpg',
    1760: '[1760] - Ebon Dust Aura.jpg',
    1761: '[1761] - Zealous Vow.jpg',
    1762: '[1762] - Heart of Fury.jpg',
    1763: '[1763] - Zealous Renewal.jpg',
    1764: "[1764] - Attacker's Insight.jpg",
    1765: '[1765] - Rending Aura.jpg',
    1766: '[1766] - Featherfoot Grace.jpg',
    1767: "[1767] - Reaper's Sweep.jpg",
    1768: "[1768] - Harrier's Haste.jpg",
    1769: '[1769] - Focused Anger.jpg',
    1770: '[1770] - Natural Temper.jpg',
    1771: '[1771] - Song of Restoration.jpg',
    1772: '[1772] - Lyric of Purification.jpg',
    1773: "[1773] - Soldier's Fury.jpg",
    1774: '[1774] - Aggressive Refrain.jpg',
    1775: '[1775] - Energizing Finale.jpg',
    1776: '[1776] - Signet of Aggression.jpg',
    1777: '[1777] - Remedy Signet.jpg',
    1778: '[1778] - Signet of Return.jpg',
    1779: '[1779] - Make Your Time!.jpg',
    1780: "[1780] - Can't Touch This!.jpg",
    1781: '[1781] - Find Their Weakness!.jpg',
    1782: '[1782] - The Power Is Yours!.jpg',
    1783: "[1783] - Slayer's Spear.jpg",
    1784: '[1784] - Swift Javelin.jpg',
    1814: "[1814] - Lightbringer's Gaze.jpg",
    1815: '[1815] - Lightbringer Signet.jpg',
    1816: '[1816] - Sunspear Rebirth Signet.jpg',
    1948: '[1948] - Shadow Sanctuary.jpg',
    1949: '[1949] - Ether Nightmare.jpg',
    1950: '[1950] - Signet of Corruption.jpg',
    1951: '[1951] - Elemental Lord.jpg',
    1952: '[1952] - Selfless Spirit.jpg',
    1953: '[1953] - Triple Shot.jpg',
    1954: '[1954] - Save Yourselves!.jpg',
    1955: '[1955] - Aura of Holy Might.jpg',
    1957: '[1957] - Spear of Fury.jpg',
    1986: '[1986] - Vampiric Assault.jpg',
    1987: '[1987] - Lotus Strike.jpg',
    1988: '[1988] - Golden Fang Strike.jpg',
    1990: '[1990] - Falling Lotus Strike.jpg',
    1991: "[1991] - Sadist's Signet.jpg",
    1992: '[1992] - Signet of Distraction.jpg',
    1993: '[1993] - Signet of Recall.jpg',
    1994: '[1994] - Power Lock.jpg',
    1995: '[1995] - Waste Not, Want Not.jpg',
    1996: '[1996] - Sum of All Fears.jpg',
    1997: '[1997] - Withering Aura.jpg',
    1998: '[1998] - Cacophony.jpg',
    1999: "[1999] - Winter's Embrace.jpg",
    2000: '[2000] - Earthen Shackles.jpg',
    2001: '[2001] - Ward of Weakness.jpg',
    2002: '[2002] - Glyph of Swiftness.jpg',
    2003: '[2003] - Cure Hex.jpg',
    2004: '[2004] - Smite Condition.jpg',
    2005: "[2005] - Smiter's Boon.jpg",
    2006: '[2006] - Castigation Signet.jpg',
    2007: '[2007] - Purifying Veil.jpg',
    2008: '[2008] - Pulverizing Smash.jpg',
    2009: '[2009] - Keen Chop.jpg',
    2010: '[2010] - Knee Cutter.jpg',
    2011: '[2011] - Grapple.jpg',
    2012: '[2012] - Radiant Scythe.jpg',
    2013: "[2013] - Grenth's Aura.jpg",
    2014: '[2014] - Signet of Pious Restraint.jpg',
    2015: "[2015] - Farmer's Scythe.jpg",
    2016: '[2016] - Energetic Was Lee Sa.jpg',
    2017: '[2017] - Anthem of Weariness.jpg',
    2018: '[2018] - Anthem of Disruption.jpg',
    2051: '[2051] - Summon Spirits.jpg',
    2052: '[2052] - Shadow Fang.jpg',
    2053: '[2053] - Calculated Risk.jpg',
    2054: '[2054] - Shrinking Armor.jpg',
    2055: '[2055] - Aneurysm.jpg',
    2056: '[2056] - Wandering Eye.jpg',
    2057: '[2057] - Foul Feast.jpg',
    2058: '[2058] - Putrid Bile.jpg',
    2059: '[2059] - Shell Shock.jpg',
    2060: '[2060] - Glyph of Immolation.jpg',
    2061: '[2061] - Patient Spirit.jpg',
    2062: '[2062] - Healing Ribbon.jpg',
    2063: '[2063] - Aura of Stability.jpg',
    2064: '[2064] - Spotless Mind.jpg',
    2065: '[2065] - Spotless Soul.jpg',
    2066: '[2066] - Disarm.jpg',
    2067: '[2067] - I Meant to Do That!.jpg',
    2068: '[2068] - Rapid Fire.jpg',
    2069: "[2069] - Sloth Hunter's Shot.jpg",
    2070: '[2070] - Aura Slicer.jpg',
    2071: '[2071] - Zealous Sweep.jpg',
    2072: '[2072] - Pure Was Li Ming.jpg',
    2073: '[2073] - Weapon of Aggression.jpg',
    2074: '[2074] - Chest Thumper.jpg',
    2075: '[2075] - Hasty Refrain.jpg',
    2091: '[2091] - Shadow Sanctuary.jpg',
    2092: '[2092] - Ether Nightmare.jpg',
    2093: '[2093] - Signet of Corruption.jpg',
    2094: '[2094] - Elemental Lord.jpg',
    2095: '[2095] - Selfless Spirit.jpg',
    2096: '[2096] - Triple Shot.jpg',
    2097: '[2097] - Save Yourselves!.jpg',
    2098: '[2098] - Aura of Holy Might.jpg',
    2099: '[2099] - Spear of Fury.jpg',
    2100: '[2100] - Summon Spirits.jpg',
    2101: '[2101] - Critical Agility.jpg',
    2102: '[2102] - Cry of Pain.jpg',
    2103: '[2103] - Necrosis.jpg',
    2104: '[2104] - Intensity.jpg',
    2105: '[2105] - Seed of Life.jpg',
    2107: '[2107] - Whirlwind Attack.jpg',
    2108: '[2108] - Never Rampage Alone.jpg',
    2109: '[2109] - Eternal Aura.jpg',
    2110: '[2110] - Vampirism.jpg',
    2112: "[2112] - There's Nothing to Fear!.jpg",
    2116: '[2116] - Sneak Attack.jpg',
    2135: '[2135] - Trampling Ox.jpg',
    2136: '[2136] - Smoke Powder Defense.jpg',
    2137: '[2137] - Confusing Images.jpg',
    2138: "[2138] - Hexer's Vigor.jpg",
    2139: '[2139] - Masochism.jpg',
    2140: '[2140] - Piercing Trap.jpg',
    2141: '[2141] - Companionship.jpg',
    2142: '[2142] - Feral Aggression.jpg',
    2143: '[2143] - Disrupting Shot.jpg',
    2144: '[2144] - Volley.jpg',
    2145: '[2145] - Expert Focus.jpg',
    2146: '[2146] - Pious Fury.jpg',
    2147: '[2147] - Crippling Victory.jpg',
    2148: '[2148] - Sundering Weapon.jpg',
    2149: '[2149] - Weapon of Renewal.jpg',
    2150: '[2150] - Maiming Spear.jpg',
    2186: '[2186] - Signet of Deadly Corruption.jpg',
    2187: '[2187] - Way of the Master.jpg',
    2188: '[2188] - Defile Defenses.jpg',
    2189: "[2189] - Angorodon's Gaze.jpg",
    2190: '[2190] - Magnetic Surge.jpg',
    2191: '[2191] - Slippery Ground.jpg',
    2192: '[2192] - Glowing Ice.jpg',
    2193: '[2193] - Energy Blast.jpg',
    2194: '[2194] - Distracting Strike.jpg',
    2195: '[2195] - Symbolic Strike.jpg',
    2196: "[2196] - Soldier's Speed.jpg",
    2197: '[2197] - Body Blow.jpg',
    2198: '[2198] - Body Shot.jpg',
    2199: '[2199] - Poison Tip Signet.jpg',
    2200: '[2200] - Signet of Mystic Speed.jpg',
    2201: '[2201] - Shield of Force.jpg',
    2202: '[2202] - Mending Grip.jpg',
    2203: '[2203] - Spiritleech Aura.jpg',
    2204: '[2204] - Rejuvenation.jpg',
    2205: '[2205] - Agony.jpg',
    2206: '[2206] - Ghostly Weapon.jpg',
    2207: '[2207] - Inspirational Speech.jpg',
    2208: '[2208] - Burning Shield.jpg',
    2209: '[2209] - Holy Spear.jpg',
    2210: '[2210] - Spear Swipe.jpg',
    2211: "[2211] - Alkar's Alchemical Acid.jpg",
    2212: '[2212] - Light of Deldrimor.jpg',
    2213: '[2213] - Ear Bite.jpg',
    2214: '[2214] - Low Blow.jpg',
    2215: '[2215] - Brawling Headbutt.jpg',
    2216: "[2216] - Don't Trip!.jpg",
    2217: "[2217] - By Ural's Hammer!.jpg",
    2218: '[2218] - Drunken Master.jpg',
    2219: '[2219] - Great Dwarf Weapon.jpg',
    2220: '[2220] - Great Dwarf Armor.jpg',
    2221: '[2221] - Breath of the Great Dwarf.jpg',
    2222: '[2222] - Snow Storm.jpg',
    2223: '[2223] - Black Powder Mine.jpg',
    2224: '[2224] - Summon Mursaat.jpg',
    2225: '[2225] - Summon Ruby Djinn.jpg',
    2226: '[2226] - Summon Ice Imp.jpg',
    2227: '[2227] - Summon Naga Shaman.jpg',
    2228: '[2228] - Deft Strike.jpg',
    2229: '[2229] - Signet of Infection.jpg',
    2230: '[2230] - Tryptophan Signet.jpg',
    2231: '[2231] - Ebon Battle Standard of Courage.jpg',
    2232: '[2232] - Ebon Battle Standard of Wisdom.jpg',
    2233: '[2233] - Ebon Battle Standard of Honor.jpg',
    2234: '[2234] - Ebon Vanguard Sniper Support.jpg',
    2235: '[2235] - Ebon Vanguard Assassin Support.jpg',
    2236: '[2236] - Well of Ruin.jpg',
    2237: '[2237] - Atrophy.jpg',
    2238: '[2238] - Spear of Redemption.jpg',
    2353: '[2353] - Finish Him!.jpg',
    2354: '[2354] - Dodge This!.jpg',
    2355: '[2355] - I Am the Strongest!.jpg',
    2356: '[2356] - I Am Unstoppable!.jpg',
    2357: '[2357] - A Touch of Guile.jpg',
    2358: '[2358] - You Move Like a Dwarf!.jpg',
    2359: '[2359] - You Are All Weaklings!.jpg',
    2360: '[2360] - Feel No Pain.jpg',
    2361: '[2361] - Club of a Thousand Bears.jpg',
    2374: '[2374] - Ursan Blessing.jpg',
    2379: '[2379] - Volfen Blessing.jpg',
    2384: '[2384] - Raven Blessing.jpg',
    2411: '[2411] - Mindbender.jpg',
    2412: '[2412] - Smooth Criminal.jpg',
    2413: '[2413] - Technobabble.jpg',
    2414: '[2414] - Radiation Field.jpg',
    2415: '[2415] - Asuran Scan.jpg',
    2416: '[2416] - Air of Superiority.jpg',
    2417: '[2417] - Mental Block.jpg',
    2418: '[2418] - Pain Inverter.jpg',
    2420: '[2420] - Ebon Escape.jpg',
    2421: '[2421] - Weakness Trap.jpg',
    2422: '[2422] - Winds.jpg',
    2423: '[2423] - Dwarven Stability.jpg',
    2657: '[2657] - Call of Haste (PvP).jpg',
    2683: "[2683] - Castigation Signet (Saul D'Alessio).jpg",
    2684: "[2684] - Unnatural Signet (Saul D'Alessio).jpg",
    2734: '[2734] - Mind Wrack (PvP).jpg',
    2803: '[2803] - Mind Freeze (PvP).jpg',
    2804: '[2804] - Mind Shock (PvP).jpg',
    2805: '[2805] - Mist Form (PvP).jpg',
    2806: '[2806] - Ward Against Harm (PvP).jpg',
    2807: '[2807] - Ride the Lightning (PvP).jpg',
    2808: '[2808] - Enraged Smash (PvP).jpg',
    2809: '[2809] - Obsidian Flame (PvP).jpg',
    2857: '[2857] - Aegis (PvP).jpg',
    2858: '[2858] - Watch Yourself! (PvP).jpg',
    2859: '[2859] - Enfeeble (PvP).jpg',
    2860: '[2860] - Ether Renewal (PvP).jpg',
    2861: '[2861] - Penetrating Attack (PvP).jpg',
    2862: '[2862] - Shadow Form (PvP).jpg',
    2863: '[2863] - Discord (PvP).jpg',
    2864: '[2864] - Sundering Attack (PvP).jpg',
    2866: '[2866] - Flesh of My Flesh (PvP).jpg',
    2867: "[2867] - Ancestors' Rage (PvP).jpg",
    2868: '[2868] - Splinter Weapon (PvP).jpg',
    2869: "[2869] - Assassin's Remedy (PvP).jpg",
    2871: '[2871] - Light of Deliverance (PvP).jpg',
    2872: '[2872] - Death Pact Signet (PvP).jpg',
    2875: "[2875] - Harrier's Toss (PvP).jpg",
    2876: '[2876] - Defensive Anthem (PvP).jpg',
    2877: '[2877] - Ballad of Restoration (PvP).jpg',
    2878: '[2878] - Song of Restoration (PvP).jpg',
    2879: '[2879] - Incoming! (PvP).jpg',
    2880: '[2880] - Never Surrender! (PvP).jpg',
    2883: '[2883] - For Great Justice! (PvP).jpg',
    2884: '[2884] - Mystic Regeneration (PvP).jpg',
    2885: '[2885] - Enfeebling Blood (PvP).jpg',
    2887: '[2887] - Signet of Judgment (PvP).jpg',
    2891: '[2891] - Unyielding Aura (PvP).jpg',
    2892: '[2892] - Spirit Bond (PvP).jpg',
    2893: '[2893] - Weapon of Warding (PvP).jpg',
    2895: "[2895] - Smiter's Boon (PvP).jpg",
    2925: "[2925] - Sloth Hunter's Shot (PvP).jpg",
    2959: "[2959] - Expert's Dexterity (PvP).jpg",
    2965: '[2965] - Signet of Spirits (PvP).jpg',
    2966: '[2966] - Signet of Ghostly Might (PvP).jpg',
    2969: '[2969] - Read the Wind (PvP).jpg',
    2998: '[2998] - Fragility (PvP).jpg',
    2999: '[2999] - Strength of Honor (PvP).jpg',
    3002: "[3002] - Warrior's Endurance (PvP).jpg",
    3003: '[3003] - Armor of Unfeeling (PvP).jpg',
    3005: '[3005] - Union (PvP).jpg',
    3006: '[3006] - Shadowsong (PvP).jpg',
    3007: '[3007] - Pain (PvP).jpg',
    3008: '[3008] - Destruction (PvP).jpg',
    3009: '[3009] - Soothing (PvP).jpg',
    3010: '[3010] - Displacement (PvP).jpg',
    3011: '[3011] - Preservation (PvP).jpg',
    3012: '[3012] - Life (PvP).jpg',
    3013: '[3013] - Recuperation (PvP).jpg',
    3014: '[3014] - Dissonance (PvP).jpg',
    3015: '[3015] - Earthbind (PvP).jpg',
    3016: '[3016] - Shelter (PvP).jpg',
    3017: '[3017] - Disenchantment (PvP).jpg',
    3018: '[3018] - Restoration (PvP).jpg',
    3019: '[3019] - Bloodsong (PvP).jpg',
    3020: '[3020] - Wanderlust (PvP).jpg',
    3021: '[3021] - Savannah Heat (PvP).jpg',
    3022: '[3022] - Gaze of Fury (PvP).jpg',
    3023: '[3023] - Anguish (PvP).jpg',
    3024: '[3024] - Empowerment (PvP).jpg',
    3025: '[3025] - Recovery (PvP).jpg',
    3026: '[3026] - Go for the Eyes! (PvP).jpg',
    3027: '[3027] - Brace Yourself! (PvP).jpg',
    3028: '[3028] - Blazing Finale (PvP).jpg',
    3029: '[3029] - Bladeturn Refrain (PvP).jpg',
    3030: '[3030] - Signet of Return (PvP).jpg',
    3031: "[3031] - Can't Touch This! (PvP).jpg",
    3032: '[3032] - Stand Your Ground! (PvP).jpg',
    3033: '[3033] - We Shall Return! (PvP).jpg',
    3034: '[3034] - Find Their Weakness! (PvP).jpg',
    3035: '[3035] - Never Give Up! (PvP).jpg',
    3036: '[3036] - Help Me! (PvP).jpg',
    3037: '[3037] - Fall Back! (PvP).jpg',
    3038: '[3038] - Agony (PvP).jpg',
    3039: '[3039] - Rejuvenation (PvP).jpg',
    3040: '[3040] - Anthem of Disruption (PvP).jpg',
    3045: '[3045] - Comfort Animal (PvP).jpg',
    3047: "[3047] - Melandru's Assault (PvP).jpg",
    3048: '[3048] - Shroud of Distress (PvP).jpg',
    3049: '[3049] - Unseen Fury (PvP).jpg',
    3050: '[3050] - Predatory Bond (PvP).jpg',
    3051: '[3051] - Enraged Lunge (PvP).jpg',
    3053: '[3053] - Signet of Deadly Corruption (PvP).jpg',
    3054: '[3054] - Masochism (PvP).jpg',
    3058: '[3058] - Unholy Feast (PvP).jpg',
    3059: '[3059] - Signet of Agony (PvP).jpg',
    3060: '[3060] - Escape (PvP).jpg',
    3061: '[3061] - Death Blossom (PvP).jpg',
    3062: '[3062] - Finale of Restoration (PvP).jpg',
    3063: '[3063] - Mantra of Resolve (PvP).jpg',
    3068: '[3068] - Charm Animal (Codex).jpg',
    3141: '[3141] - Lightning Reflexes (PvP).jpg',
    3143: '[3143] - Renewing Smash (PvP).jpg',
    3144: '[3144] - Heal as One (PvP).jpg',
    3145: '[3145] - Glass Arrows (PvP).jpg',
    3147: '[3147] - Keen Arrow (PvP).jpg',
    3148: '[3148] - Anthem of Envy (PvP).jpg',
    3149: '[3149] - Mending Refrain (PvP).jpg',
    3151: '[3151] - Empathy (PvP).jpg',
    3152: '[3152] - Crippling Anguish (PvP).jpg',
    3156: "[3156] - Soldier's Stance (PvP).jpg",
    3157: '[3157] - Destructive Was Glaive (PvP).jpg',
    3179: '[3179] - Mantra of Signets (PvP).jpg',
    3180: '[3180] - Shatter Delusions (PvP).jpg',
    3181: '[3181] - Illusionary Weaponry (PvP).jpg',
    3183: '[3183] - Migraine (PvP).jpg',
    3184: '[3184] - Accumulated Pain (PvP).jpg',
    3185: '[3185] - Psychic Instability (PvP).jpg',
    3186: '[3186] - Shared Burden (PvP).jpg',
    3187: '[3187] - Stolen Speed (PvP).jpg',
    3188: '[3188] - Unnatural Signet (PvP).jpg',
    3189: '[3189] - Spiritual Pain (PvP).jpg',
    3190: '[3190] - Frustration (PvP).jpg',
    3191: '[3191] - Mistrust (PvP).jpg',
    3192: "[3192] - Enchanter's Conundrum (PvP).jpg",
    3193: '[3193] - Signet of Clumsiness (PvP).jpg',
    3194: '[3194] - Mirror of Disenchantment (PvP).jpg',
    3195: '[3195] - Wandering Eye (PvP).jpg',
    3196: '[3196] - Calculated Risk (PvP).jpg',
    3204: '[3204] - Defy Pain (PvP).jpg',
    3232: '[3232] - Heal Party (PvP).jpg',
    3233: '[3233] - Spoil Victor (PvP).jpg',
    3234: '[3234] - Visions of Regret (PvP).jpg',
    3251: '[3251] - Fox Fangs (PvP).jpg',
    3252: '[3252] - Wild Strike (PvP).jpg',
    3263: '[3263] - Banishing Strike (PvP).jpg',
    3264: '[3264] - Twin Moon Sweep (PvP).jpg',
    3265: '[3265] - Irresistible Sweep (PvP).jpg',
    3266: '[3266] - Pious Assault (PvP).jpg',
    3269: '[3269] - Guiding Hands (PvP).jpg',
    3270: '[3270] - Avatar of Dwayna (PvP).jpg',
    3271: '[3271] - Avatar of Melandru (PvP).jpg',
    3272: '[3272] - Mystic Healing (PvP).jpg',
    3273: '[3273] - Signet of Pious Restraint (PvP).jpg',
    3289: '[3289] - Fevered Dreams (PvP).jpg',
    3346: '[3346] - Aura of Thorns (PvP).jpg',
    3347: '[3347] - Dust Cloak (PvP).jpg',
    3348: "[3348] - Lyssa's Haste (PvP).jpg",
    3365: '[3365] - Onslaught (PvP).jpg',
    3366: '[3366] - Heart of Fury (PvP).jpg',
    3367: '[3367] - Wounding Strike (PvP).jpg',
    3368: '[3368] - Pious Fury (PvP).jpg',
    3373: '[3373] - Illusion of Haste (PvP).jpg',
    3374: '[3374] - Illusion of Pain (PvP).jpg',
    3375: '[3375] - Aura of Restoration (PvP).jpg',
    3386: '[3386] - Web of Disruption (PvP).jpg',
    3396: '[3396] - Lightning Hammer (PvP).jpg',
    3397: '[3397] - Elemental Flame (PvP).jpg',
    3398: '[3398] - Slippery Ground (PvP).jpg',
    3422: '[3422] - Time Ward.jpg',
    3423: '[3423] - Soul Taker.jpg',
    3424: '[3424] - Over the Limit.jpg',
    3425: '[3425] - Judgment Strike.jpg',
    3426: '[3426] - Seven Weapons Stance.jpg',
    3427: '[3427] - Together as One!.jpg',
    3428: '[3428] - Shadow Theft.jpg',
    3429: '[3429] - Weapons of Three Forges.jpg',
    3430: '[3430] - Vow of Revolution.jpg',
    3431: '[3431] - Heroic Refrain.jpg',
}


#endregion


