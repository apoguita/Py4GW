from enum import Enum
from enum import IntEnum


#region ImguiFonts
class ImguiFonts(IntEnum):
    Regular_14 = 0
    Regular_22 = 1
    Regular_30 = 2
    Regular_46 = 3
    Regular_62 = 4
    Regular_124 = 5
    Bold_14 = 6
    Bold_22 = 7
    Bold_30 = 8
    Bold_46 = 9
    Bold_62 = 10
    Bold_124 = 11
    Italic_14 = 12
    Italic_22 = 13
    Italic_30 = 14
    Italic_46 = 15
    Italic_62 = 16
    Italic_124 = 17
    BoldItalic_14 = 18
    BoldItalic_22 = 19
    BoldItalic_30 = 20
    BoldItalic_46 = 21
    BoldItalic_62 = 22
    BoldItalic_124 = 23


#endregion
# region ChatChannel
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
    CHANNEL_UNKNOWN = -1


# endregion

# region UIManager
class UIMessage(IntEnum):
    kNone                       = 0x0
    kResize                     = 0x8
    kInitFrame                  = 0x9
    kDestroyFrame               = 0xB
    kKeyDown                    = 0x20  # wparam = UIPacket::kKeyAction*
    kSetFocus                   = 0x21
    kKeyUp                      = 0x22  # wparam = UIPacket::kKeyAction*
    kMouseClick                 = 0x24  # wparam = UIPacket::kMouseClick*
    kMouseCoordsClick           = 0x26
    kMouseUp                    = 0x28  # wparam = UIPacket::kMouseClick*
    kMouseClick2                = 0x31  # wparam = UIPacket::kMouseAction*
    kMouseAction                = 0x32  # wparam = UIPacket::kMouseAction*
    kSetLayout                  = 0x37
    kMeasureContent             = 0x38
    kRefreshContent             = 0x3B

    kRerenderAgentModel         = 0x10000007 # 0x10000007, wparam = uint32_t agent_id
    kAgentDestroy               = 0x10000008 # 0x10000008, wparam = uint32_t agent_id
    kUpdateAgentEffects         = 0x10000009
    kAgentSpeechBubble          = 0x10000017
    kShowAgentNameTag           = 0x10000019 # 0x10000019, wparam = AgentNameTagInfo*
    kHideAgentNameTag           = 0x1000001A 
    kSetAgentNameTagAttribs     = 0x1000001B #  0x1000001B, wparam = AgentNameTagInfo*
    kSetAgentProfession         = 0x1000001D #  0x1000001D, wparam = UIPacket::kSetAgentProfession*
    kChangeTarget               = 0x10000020 # 0x10000020, wparam = UIPacket::kChangeTarget*
    kAgentSkillActivatedInstantly = 0x10000025 # kAgentSkillPacket
    kAgentSkillCancelled        = 0x10000026 # kAgentSkillPacket
    kAgentStartCasting          = 0x10000027  # wparam = { uint32_t agent_id, uint32_t skill_id }
    kShowMapEntryMessage        = 0x10000029 # 0x10000029, wparam = { wchar_t* title, wchar_t* subtitle }
    kSetCurrentPlayerData       = 0x1000002A # 0x1000002A, fired after setting the worldcontext player name
    kPostProcessingEffect       = 0x10000034 # 0x10000034, Triggered when drunk. wparam = UIPacket::kPostProcessingEffect
    kHeroAgentAdded             = 0x10000038 # 0x10000038, hero assigned to agent/inventory/ai mode
    kHeroDataAdded              = 0x10000039 # 0x10000039, hero info received from server (name, level etc)
    kShowXunlaiChest            = 0x10000040 # 0x10000040
    kMinionCountUpdated         = 0x10000046 # 0x10000046
    kMoraleChange               = 0x10000047 # 0x10000047, wparam = {agent id, morale percent }
    #= 0x10000048 unknown enter challenge related message
    kLoginStateChanged          = 0x10000050 # 0x10000050, wparam = {bool is_logged_in, bool unk }
    kEffectAdd                  = 0x10000055 # 0x10000055, wparam = {agent_id, GW::Effect*}
    kEffectRenew                = 0x10000056 # 0x10000056, wparam = GW::Effect*
    kEffectRemove               = 0x10000057 # 0x10000057, wparam = effect id
    kSkillActivated             = 0x1000005b # 0x1000005b, wparam ={ uint32_t agent_id , uint32_t skill_id }
    kUpdateSkillbar             = 0x1000005E # 0x1000005E, wparam ={ uint32_t agent_id , ... }
    kUpdateSkillsAvailable      = 0x1000005f # 0x1000005f, Triggered on a skill unlock, profession change or map load
    kPlayerTitleChanged         = 0x10000064 # 0x10000064, wparam = { uint32_t player_id, uint32_t title_id }
    kTitleProgressUpdated       = 0x10000065 # 0x10000065, wparam = title_id
    kExperienceGained           = 0x10000066 # 0x10000066, wparam = experience amount
    kWriteToChatLog             = 0x1000007F # 0x1000007F, wparam = UIPacket::kWriteToChatLog*
    kWriteToChatLogWithSender   = 0x10000080 # 0x10000080, wparam = UIPacket::kWriteToChatLogWithSender*
    kAllyOrGuildMessage         = 0x10000081 # 0x10000081, wparam = UIPacket::kAllyOrGuildMessage*
    kPlayerChatMessage          = 0x10000082 # 0x10000082, wparam = UIPacket::kPlayerChatMessage*
    kFloatingWindowMoved        = 0x10000084 # 0x10000084, wparam = frame_id
    kFriendUpdated              = 0x1000008B # 0x1000008B, wparam = { GW::Friend*, ... }
    kMapLoaded                  = 0x1000008C # 0x1000008C
    kOpenWhisper                = 0x10000092 # 0x10000092, wparam = wchar* name
    kLoadMapContext             = 0x10000098 # 0x10000098, wparam = UIPacket::kLoadMapContext
    kLogout                     = 0x1000009D # 0x1000009D, wparam = { bool unknown, bool character_select }
    kCompassDraw                = 0x1000009E # 0x1000009E, wparam = UIPacket::kCompassDraw*
    kOnScreenMessage            = 0x100000A2 # 0x100000A2, wparam = wchar_** encoded_string
    kDialogButton               = 0x100000A3 # 0x100000A3, wparam = DialogButtonInfo*
    kDialogBody                 = 0x100000A6 # 0x100000A6, wparam = DialogBodyInfo*
    kTargetNPCPartyMember       = 0x100000B3 # 0x100000B3, wparam = { uint32_t unk, uint32_t agent_id }
    kTargetPlayerPartyMember    = 0x100000B4 # 0x100000B4, wparam = { uint32_t unk, uint32_t player_number }
    kVendorWindow               = 0x100000B5 # 0x100000B5, wparam = UIPacket::kVendorWindow
    kVendorItems                = 0x100000B9 # 0x100000B9, wparam = UIPacket::kVendorItems
    kVendorTransComplete        = 0x100000BB # 0x100000BB, wparam = *TransactionType
    kVendorQuote                = 0x100000BD # 0x100000BD, wparam = UIPacket::kVendorQuote
    kStartMapLoad               = 0x100000C2 # 0x100000C2, wparam = { uint32_t map_id, ...}
    kWorldMapUpdated            = 0x100000C7 # 0x100000C7, Triggered when an area in the world map has been discovered/updated
    kGuildMemberUpdated         = 0x100000DA # 0x100000DA, wparam = { GuildPlayer::name_ptr }
    kShowHint                   = 0x100000E1 # 0x100000E1, wparam = { uint32_t icon_type, wchar_t* message_enc }
    kWeaponSetSwapComplete      = 0x100000E9 # 0x100000E9, wparam = UIPacket::kWeaponSwap*
    kWeaponSetSwapCancel        = 0x100000EA # 0x100000EA
    kWeaponSetUpdated           = 0x100000EB # 0x100000EB
    kUpdateGoldCharacter        = 0x100000EC # 0x100000EC, wparam = { uint32_t unk, uint32_t gold_character }
    kUpdateGoldStorage          = 0x100000ED # 0x100000ED, wparam = { uint32_t unk, uint32_t gold_storage }
    kInventorySlotUpdated       = 0x100000EE # 0x100000EE, Triggered when an item is moved into a slot
    kEquipmentSlotUpdated       = 0x100000EF # 0x100000EF, Triggered when an item is moved into a slot
    kInventorySlotCleared       = 0x100000F1 # 0x100000F1, Triggered when an item has been removed from a slot
    kEquipmentSlotCleared       = 0x100000F2 # 0x100000F2, Triggered when an item has been removed from a slot
    kPvPWindowContent           = 0x100000FA # 0x100000FA
    kPreStartSalvage            = 0x10000102 # 0x10000102, { uint32_t item_id, uint32_t kit_id }
    kTomeSkillSelection         = 0x10000103 # 0x10000103, wparam = UIPacket::kTomeSkillSelection*
    kTradePlayerUpdated         = 0x10000105 # 0x10000105, wparam = GW::TraderPlayer*
    kItemUpdated                = 0x10000106 # 0x10000106, wparam = UIPacket::kItemUpdated*
    kMapChange                  = 0x10000111 # 0x10000111, wparam = map id
    kCalledTargetChange         = 0x10000115 # 0x10000115, wparam = { player_number, target_id }
    kErrorMessage               = 0x10000119 # 0x10000119, wparam = { int error_index, wchar_t* error_encoded_string }
    kPartyHardModeChanged       = 0x1000011A # 0x1000011A, wparam = { int is_hard_mode }
    kPartyAddHenchman           = 0x1000011B # 0x1000011B
    kPartyRemoveHenchman        = 0x1000011C # 0x1000011C
    kPartyAddHero               = 0x1000011E # 0x1000011E
    kPartyRemoveHero            = 0x1000011F # 0x1000011F
    kPartyAddPlayer             = 0x10000124 # 0x10000124
    kPartyRemovePlayer          = 0x10000126 # 0x10000126
    kDisableEnterMissionBtn     = 0x1000012A # 0x1000012A, wparam = boolean (1 = disabled, 0 = enabled)
    kShowCancelEnterMissionBtn  = 0x1000012D # 0x1000012D
    kPartyDefeated              = 0x1000012F # 0x1000012F
    #kEnterChallengeRelated      = 0x10000130
    kPartySearchInviteReceived  = 0x10000137 # 0x10000137, wparam = UIPacket::kPartySearchInviteReceived*
    kPartySearchInviteSent      = 0x10000139 # 0x10000139
    kPartyShowConfirmDialog     = 0x1000013A # 0x1000013A, wparam = UIPacket::kPartyShowConfirmDialog
    kPreferenceEnumChanged      = 0x10000140 # 0x10000140, wparam = UiPacket::kPreferenceEnumChanged
    kPreferenceFlagChanged      = 0x10000141 # 0x10000141, wparam = UiPacket::kPreferenceFlagChanged
    kPreferenceValueChanged     = 0x10000142 # 0x10000142, wparam = UiPacket::kPreferenceValueChanged
    kUIPositionChanged          = 0x10000143 # 0x10000143, wparam = UIPacket::kUIPositionChanged
    kPreBuildLoginScene         = 0x10000144 # 0x10000144, Called with no args right before login scene is drawn
    kQuestAdded                 = 0x1000014E # 0x1000014E, wparam = { quest_id, ... }
    kQuestDetailsChanged        = 0x1000014F # 0x1000014F, wparam = { quest_id, ... }
    kQuestRemoved               = 0x10000150 # 0x10000150, wparam = { quest_id, ... }
    kClientActiveQuestChanged   = 0x10000151 # 0x10000151, wparam = { quest_id, ... }. Triggered when the game requests the current quest to change
    kServerActiveQuestChanged   = 0x10000153 # 0x10000153, wparam = UIPacket::kServerActiveQuestChanged*. Triggered when the server requests the current quest to change
    kUnknownQuestRelated        = 0x10000154 # 0x10000154
    kDungeonComplete            = 0x10000156 # 0x10000156
    kMissionComplete            = 0x10000157 # 0x10000157
    kVanquishComplete           = 0x10000159 # 0x10000159
    kObjectiveAdd               = 0x1000015A # 0x1000015A, wparam = UIPacket::kObjectiveAdd*
    kObjectiveComplete          = 0x1000015B # 0x1000015B, wparam = UIPacket::kObjectiveComplete*
    kObjectiveUpdated           = 0x1000015C # 0x1000015C, wparam = UIPacket::kObjectiveUpdated*
    kTradeSessionStart          = 0x10000165 # 0x10000165, wparam = { trade_state, player_number }
    kTradeSessionUpdated        = 0x1000016b # 0x1000016b, no args
    kTriggerLogoutPrompt        = 0x1000016E # 0x1000016E, no args
    kToggleOptionsWindow        = 0x1000016F # 0x1000016F, no args
    kRedrawItem                 = 0x10000174 # 0x10000174, wparam = uint32_t item_id
    kCheckUIState               = 0x10000175 # 0x10000175
    kCloseSettings              = 0x10000176 # 0x10000176
    kChangeSettingsTab          = 0x10000177 # 0x10000177, wparam = uint32_t is_interface_tab
    kDestroyUIPositionOverlay   = 0x10000179 # 0x10000179
    kEnableUIPositionOverlay    = 0x1000017a # 0x1000017a, wparam = uint32_t enable
      
    kGuildHall                  = 0x1000017F # was 0x1000017C, wparam = gh key (uint32_t[4])
    kLeaveGuildHall             = 0x10000181 # was 0x1000017E
    kTravel                     = 0x10000182 # was 0x1000017F
    kOpenWikiUrl                = 0x10000183 # was 0x10000180, wparam = char* url
    kAppendMessageToChat        = 0x10000191 # was 0x1000018E, wparam = wchar_t* message
    kHideHeroPanel              = 0x1000019F # was 0x1000019C, wparam = hero_id
    kShowHeroPanel              = 0x100001A0 # was 0x1000019D, wparam = hero_id
    kGetInventoryAgentId        = 0x100001A4 # was 0x100001A1, wparam = 0, lparam = uint32_t* agent_id_out. Used to fetch which agent is selected
    kEquipItem                  = 0x100001A5 # was 0x100001A2, wparam = { item_id, agent_id }
    kMoveItem                   = 0x100001A6 # was 0x100001A3, wparam = { item_id, to_bag, to_slot, bool prompt }
    kInitiateTrade              = 0x100001A8 # was 0x100001A5
    kInventoryAgentChanged      = 0x100001B8 # was 0x100001B5, Triggered when inventory needs updating due to agent change; no args
    kOpenTemplate               = 0x100001C1 # was 0x100001BE, wparam = GW::UI::ChatTemplate*

    kCancelEnterMission         = 0x30000001  
    kSendEnterMission           = 0x30000002  # wparam = uint32_t arena_id
    kSendLoadSkillbar           = 0x30000003  # wparam = UIPacket::kSendLoadSkillbar*
    kSendPingWeaponSet          = 0x30000004  # wparam = UIPacket::kSendPingWeaponSet*
    kSendMoveItem               = 0x30000005  # wparam = UIPacket::kSendMoveItem*
    kSendMerchantRequestQuote   = 0x30000006  # wparam = UIPacket::kSendMerchantRequestQuote*
    kSendMerchantTransactItem   = 0x30000007  # wparam = UIPacket::kSendMerchantTransactItem*
    kSendUseItem                = 0x30000008  # wparam = UIPacket::kSendUseItem*
    kSendSetActiveQuest         = 0x30000009  # wparam = uint32_t quest_id
    kSendAbandonQuest           = 0x3000000A  # wparam = uint32_t quest_id
    kSendChangeTarget           = 0x3000000B  # wparam = UIPacket::kSendChangeTarget*
    kSendMoveToWorldPoint       = 0x3000000C  # wparam = GW::GamePos*  # Clicking on the ground in the 3D world to move there
    kSendInteractNPC            = 0x3000000D  # wparam = UIPacket::kInteractAgent*
    kSendInteractGadget         = 0x3000000E  # wparam = UIPacket::kInteractAgent*
    kSendInteractItem           = 0x3000000F  # wparam = UIPacket::kInteractAgent*
    kSendInteractEnemy          = 0x30000010  # wparam = UIPacket::kInteractAgent*
    kSendInteractPlayer         = 0x30000011  # wparam = uint32_t agent_id  # NB: calling target is a separate packet
    kSendCallTarget             = 0x30000013  # wparam = { uint32_t call_type, uint32_t agent_id }
    kSendAgentDialog            = 0x30000014  # wparam = uint32_t agent_id
    kSendGadgetDialog           = 0x30000015  # wparam = uint32_t agent_id
    kSendDialog                 = 0x30000016  # wparam = dialog_id  # Internal use

    kStartWhisper               = 0x30000017  # wparam = UIPacket::kStartWhisper*
    kGetSenderColor             = 0x30000018  # wparam = UIPacket::kGetColor*
    kGetMessageColor            = 0x30000019  # wparam = UIPacket::kGetColor*
    kSendChatMessage            = 0x3000001B  # wparam = UIPacket::kSendChatMessage*
    kLogChatMessage             = 0x3000001D  # wparam = UIPacket::kLogChatMessage*
    kRecvWhisper                = 0x3000001E  # wparam = UIPacket::kRecvWhisper*
    kPrintChatMessage           = 0x3000001F  # wparam = UIPacket::kPrintChatMessage*
    kSendWorldAction            = 0x30000020  # wparam = UIPacket::kSendWorldAction*
    kSetRendererValue           = 0x30000021  # wparam = UIPacket::kSetRendererValue
    kIdentifyItem               = 0x30000022  # wparam = UIPacket::kIdentifyItem



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

class BoolPreference(IntEnum):
    _False = 0
    _True = 1

class InterfaceSize(IntEnum):
    Small = 4294967295  # -1 as uint32_t
    Normal =  0
    Large = 1
    Larger = 2

class AntiAliasing(IntEnum):
    _None = 0
    _2X = 1
    _4X = 3
    _8X = 4
    
class TerrainQuality(IntEnum):
    Low = 1
    Medium = 2
    High = 3

class Reflections(IntEnum):
    _None = 0
    TerrainAndSky = 1
    Default = 2 
    All = 3
    
class TextureQuality(IntEnum):
    High = 0
    Medium = 1
    Low = 2

class ShadowQuality(IntEnum):
    Off = 0
    Low = 1
    Medium = 2
    High = 3
    Ultra = 4
    
class ShaderQuality(IntEnum):
    Low = 1
    Medium = 2
    High = 3
    
class FrameLimiter(IntEnum):
    _None = 0
    _30 = 1
    _60 = 2
    MonitorRefreshRate = 3


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
    BackgroundVolume = 24  # Range: 0–100
    DialogVolume = 25  # Range: 0–100
    EffectsVolume = 26  # Range: 0–100
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
    GamepadInputGuide = 0xE

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

    WaitForVSync = 0x41 #65
    DoubleTapForwardToRunBackwardsToFlip = 0x42   # 66

    DoNotCloseWindowsOnEscape = 0x45
    ShowMinimapOnWorldMap = 0x46
    OptimizeForStereo = 0x4E # 78

    UseHighResolutionTexturesInOutposts = 0x52 # 82
    EnhancedDrawDistance = 0x54 # 84
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
    WindowID_DistrictList = 0xA
    WindowID_PerformanceMonitor = 0xB
    WindowID_EffectsMonitor = 0xC
    WindowID_Hints = 0xD
    #0xE?
    WindowID_MissionProgress = 0xF #0xE
    WindowID_MissionStatusAndScoreDisplay = 0xF
    WindowID_Notifications = 0x12
    WindowID_Skillbar = 0x16
    WindowID_SkillMonitor = 0x17
    WindowID_UpkeepMonitor = 0x19
    WindowID_SkillWarmup = 0x1A
    #WindowID_Menu = 0x1A
    WindowID_EnergyBar = 0x1E
    WindowID_ExperienceBar = 0x1F
    WindowID_HealthBar = 0x20
    WindowID_TargetDisplay = 0x21
    WindowID_Task_Tracker = 0x23
    WindowID_TradeButton = 0x24
    WindowID_WeaponBar = 0x25

    WindowID_Hero1 = 0x36
    WindowID_Hero2 = 0x37
    WindowID_Hero3 = 0x38
    WindowID_Hero = 0x39

    WindowID_SkillsAndAttributes = 0x3B #0x38
    WindowID_Friends = 0x3D #0x3A
    WindowID_Guild = 0x3E #0x3B
    WindowID_Help = 0x40 #0x3D
    WindowID_Inventory = 0x41 #0x3E
    #WindowID_VaultBox = 0x3B #0x3F # Deprecated
    WindowID_InventoryBags = 0x43 #old 0x40
    WindowID_MissionMap = 0x45
    WindowID_Observe = 0x47
    WindowID_Options = 0x45
    WindowID_PartyWindow = 0x4B #0x48  # state flag ignored, position is valid
    WindowID_PartySearch = 0x4C #0x49
    WindowID_QuestLog = 0x52 #0x4F
    #WindowID_Merchant = 0x5F #0x5C # Deprecated
    WindowID_Hero4 = 0x61 #0x5E
    WindowID_Hero5 = 0x62 #0x5F
    WindowID_Hero6 = 0x63 #0x60
    WindowID_Hero7 = 0x64 #0x61

    WindowID_Count = 0x69  # Used for bounds checking

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
    ControlAction_ChatReply = 0xBE
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

class InGameClockMode(IntEnum):
    Off = 0
    LocalTime = 1
    ServerTime = 2