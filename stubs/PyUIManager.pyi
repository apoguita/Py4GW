from typing import List, Tuple, Callable
from enum import IntEnum

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



class UIInteractionCallback:
    def __init__(self) -> None:
        """Initialize the callback (empty constructor, defined in bindings)."""
        pass

    def get_address(self) -> int:
        """Retrieve the function pointer address (stubbed in bindings)."""
        ...


    
    
class FramePosition:
    def __init__(self) -> None: ...
    
    top: int
    left: int
    bottom: int
    right: int
    content_top: int
    content_left: int
    content_bottom: int
    content_right: int
    unknown: float
    scale_factor: float
    viewport_width: float
    viewport_height: float
    screen_top: float
    screen_left: float
    screen_bottom: float
    screen_right: float
    top_on_screen: int
    left_on_screen: int
    bottom_on_screen: int
    right_on_screen: int
    width_on_screen: int
    height_on_screen: int
    viewport_scale_x: float
    viewport_scale_y: float
    
class FrameRelation:
    def __init__(self) -> None: ...
    
    parent_id: int
    field67_0x124: int
    field68_0x128: int
    frame_hash_id: int
    siblings: List[int]

class UIFrame:
    def __init__(self, frame_id: int) -> None: ...
    
    frame_id: int
    parent_id: int
    frame_hash: int
    visibility_flags: int
    type: int
    template_type: int
    position: FramePosition
    relation: FrameRelation
    frame_callbacks: List[UIInteractionCallback]
    child_offset_id : int
    is_visible: bool
    is_created: bool
    
    # All extra fields
    field1_0x0: int
    field2_0x4: int
    frame_layout: int
    field3_0xc: int
    field4_0x10: int
    field5_0x14: int
    field7_0x1c: int
    field10_0x28: int
    field11_0x2c: int
    field12_0x30: int
    field13_0x34: int
    field14_0x38: int
    field15_0x3c: int
    field16_0x40: int
    field17_0x44: int
    field18_0x48: int
    field19_0x4c: int
    field20_0x50: int
    field21_0x54: int
    field22_0x58: int
    field23_0x5c: int
    field24_0x60: int
    field25_0x64: int
    field26_0x68: int
    field27_0x6c: int
    field28_0x70: int
    field29_0x74: int
    field30_0x78: int
    field31_0x7c: List[int]
    field32_0x8c: int
    field33_0x90: int
    field34_0x94: int
    field35_0x98: int
    field36_0x9c: int
    field40_0xb8: int
    field41_0xbc: int
    field42_0xc0: int
    field43_0xc4: int
    field44_0xc8: int
    field45_0xcc: int
    field63_0x114: int
    field64_0x118: int
    field65_0x11c: int
    field73_0x13c: int
    field74_0x140: int
    field75_0x144: int
    field76_0x148: int
    field77_0x14c: int
    field78_0x150: int
    field79_0x154: int
    field80_0x158: int
    field81_0x15c: int
    field82_0x160: int
    field83_0x164: int
    field84_0x168: int
    field85_0x16c: int
    field86_0x170: int
    field87_0x174: int
    field88_0x178: int
    field89_0x17c: int
    field90_0x180: int
    field91_0x184: int
    field92_0x188: int
    field93_0x18c: int
    field94_0x190: int
    field95_0x194: int
    field96_0x198: int
    field97_0x19c: int
    field98_0x1a0: int
    field100_0x1a8: int

    def get_context(self) -> None: ...
    
class UIManager:
    #def __init__(self) -> None: ... 
    @staticmethod
    def get_frame_id_by_label(label: str) -> int: ...
    @staticmethod
    def get_frame_id_by_hash(hash: int) -> int: ...
    @staticmethod
    def get_hash_by_label(label: str) -> int: ...
    @staticmethod
    def get_frame_hierarchy() -> List[Tuple[int, int, int, int]]: ...
    @staticmethod
    def get_frame_coords_by_hash(frame_hash: int) -> List[Tuple[int, int]]: ...
    @staticmethod
    def button_click(frame_id: int) -> None: ...
    @staticmethod
    def get_root_frame_id() -> int: ...
    @staticmethod
    def is_world_map_showing() -> bool: ...
    @staticmethod
    def set_preference (preference: int, value: int) -> None: ...
    @staticmethod
    def get_frame_limit() -> int: ...
    @staticmethod
    def set_frame_limit(limit: int) -> None: ...
    @staticmethod
    def get_frame_array() -> List[int]: ...
    @staticmethod
    def get_child_frame_id(parent_hash: int, child_offsets: List[int]) -> int: ...