
from ctypes import Structure, c_uint32, c_float, cast, POINTER, c_uint8, c_uint16, c_void_p
from ctypes import Union
import ctypes
from ..context.AccAgentContext import AccAgentContext
from ..context.MapContext import MapContext
from ..context.CharContext import CharContext
from ..context.InstanceInfoContext import InstanceInfo
from ..context.WorldContext import WorldContext
from ..internals.types import Vec2f, Vec3f, GamePos
from ..internals.gw_array import GW_Array, GW_Array_Value_View
from ..internals.gw_list import GW_TList, GW_TList_View, GW_TLink
from typing import List, Optional
from ..internals.native_symbol import NativeSymbol
from ...Scanner import ScannerSection
from dataclasses import dataclass

# ---------------------------------------------------------------------
# ------------------ DyeInfo ------------------------------------------
# ---------------------------------------------------------------------
@dataclass(slots=True)
class DyeInfo:
    dye_tint: int
    dye1: int
    dye2: int
    dye3: int
    dye4: int

class DyeInfoStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("dye_tint", c_uint8),        # 0x00
        ("dye1", c_uint8, 4),         # 0x01 low nibble
        ("dye2", c_uint8, 4),         # 0x01 high nibble
        ("dye3", c_uint8, 4),         # 0x02 low nibble
        ("dye4", c_uint8, 4),         # 0x02 high nibble
    ]
    def snapshot(self) -> DyeInfo:
        return DyeInfo(
            dye_tint=int(self.dye_tint),
            dye1=int(self.dye1),
            dye2=int(self.dye2),
            dye3=int(self.dye3),
            dye4=int(self.dye4),
        )

# ---------------------------------------------------------------------
# ------------------ ItemData -----------------------------------------
# ---------------------------------------------------------------------

@dataclass(slots=True)
class ItemData:
    model_file_id: int
    type: int
    dye: DyeInfo
    value: int
    interaction: int
    
class ItemDataStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("model_file_id", c_uint32),     # 0x00
        ("type", c_uint32),              # 0x04 - enum stored as uint32_t
        ("dye", DyeInfoStruct),                # 0x08
        ("value", c_uint32),             # 0x0B / actually 0x0C aligned
        ("interaction", c_uint32),       # 0x10
    ]
    
    def snapshot(self) -> ItemData:
        return ItemData(
            model_file_id=int(self.model_file_id),
            type=int(self.type),
            dye=self.dye.snapshot(),   # nested snapshot
            value=int(self.value),
            interaction=int(self.interaction),
        )

# ---------------------------------------------------------------------
# ------------------ EquipmentItemsUnion ------------------------------
# ---------------------------------------------------------------------
@dataclass(slots=True)
class EquipmentItemsUnion:
    items: tuple[ItemData, ItemData, ItemData, ItemData, ItemData,
                 ItemData, ItemData, ItemData, ItemData]
    weapon: ItemData
    offhand: ItemData
    chest: ItemData
    legs: ItemData
    head: ItemData
    feet: ItemData
    hands: ItemData
    costume_body: ItemData
    costume_head: ItemData


class EquipmentItemsUnionStruct(Union):
    _pack_ = 1
    _fields_ = [
        ("items", ItemDataStruct * 9),
        ("weapon", ItemDataStruct),            # 0x0024
        ("offhand", ItemDataStruct),           # 0x0034
        ("chest", ItemDataStruct),             # 0x0044
        ("legs", ItemDataStruct),              # 0x0054
        ("head", ItemDataStruct),              # 0x0064
        ("feet", ItemDataStruct),              # 0x0074
        ("hands", ItemDataStruct),             # 0x0084
        ("costume_body", ItemDataStruct),      # 0x0094
        ("costume_head", ItemDataStruct),      # 0x00A4
    ]
    
    def snapshot(self) -> EquipmentItemsUnion:
        items = (
            self.items[0].snapshot(),
            self.items[1].snapshot(),
            self.items[2].snapshot(),
            self.items[3].snapshot(),
            self.items[4].snapshot(),
            self.items[5].snapshot(),
            self.items[6].snapshot(),
            self.items[7].snapshot(),
            self.items[8].snapshot(),
        )

        return EquipmentItemsUnion(
            items=tuple(items),
            weapon=self.weapon.snapshot(),
            offhand=self.offhand.snapshot(),
            chest=self.chest.snapshot(),
            legs=self.legs.snapshot(),
            head=self.head.snapshot(),
            feet=self.feet.snapshot(),
            hands=self.hands.snapshot(),
            costume_body=self.costume_body.snapshot(),
            costume_head=self.costume_head.snapshot(),
        )

# ---------------------------------------------------------------------
# ------------------ EquipmentItemIDsUnion ----------------------------
# ---------------------------------------------------------------------
@dataclass(slots=True)
class EquipmentItemIDsUnion:
    item_ids: tuple[int, int, int, int, int, int, int, int, int]
    item_id_weapon: int
    item_id_offhand: int
    item_id_chest: int
    item_id_legs: int
    item_id_head: int
    item_id_feet: int
    item_id_hands: int
    item_id_costume_body: int
    item_id_costume_head: int
    
class EquipmentItemIDsUnionStruct(Union):
    _pack_ = 1
    _fields_ = [
        ("item_ids", c_uint32 * 9),
        ("item_id_weapon", c_uint32),          # 0x00B4
        ("item_id_offhand", c_uint32),         # 0x00B8
        ("item_id_chest", c_uint32),           # 0x00BC
        ("item_id_legs", c_uint32),            # 0x00C0
        ("item_id_head", c_uint32),            # 0x00C4
        ("item_id_feet", c_uint32),            # 0x00C8
        ("item_id_hands", c_uint32),           # 0x00CC
        ("item_id_costume_body", c_uint32),    # 0x00D0
        ("item_id_costume_head", c_uint32),    # 0x00D4
    ]
    
    def snapshot(self) -> EquipmentItemIDsUnion:
        item_ids = (
            int(self.item_ids[0]),
            int(self.item_ids[1]),
            int(self.item_ids[2]),
            int(self.item_ids[3]),
            int(self.item_ids[4]),
            int(self.item_ids[5]),
            int(self.item_ids[6]),
            int(self.item_ids[7]),
            int(self.item_ids[8]),
        )

        return EquipmentItemIDsUnion(
            item_ids=item_ids,
            item_id_weapon=int(self.item_id_weapon),
            item_id_offhand=int(self.item_id_offhand),
            item_id_chest=int(self.item_id_chest),
            item_id_legs=int(self.item_id_legs),
            item_id_head=int(self.item_id_head),
            item_id_feet=int(self.item_id_feet),
            item_id_hands=int(self.item_id_hands),
            item_id_costume_body=int(self.item_id_costume_body),
            item_id_costume_head=int(self.item_id_costume_head),
        )
        
# ---------------------------------------------------------------------
# ----------------------- Equipment -----------------------------------
# ---------------------------------------------------------------------

@dataclass(slots=True)
class Equipment:
    vtable: int
    h0004: int
    h0008: int
    h000C: int
    h0018: int
    left_hand_map: int
    right_hand_map: int
    head_map: int
    shield_map: int
    items_union: EquipmentItemsUnion
    ids_union: EquipmentItemIDsUnion
    
    #accessors
    left_hand: Optional[ItemData]
    right_hand: Optional[ItemData]
    shield:Optional[ItemData]

class EquipmentStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("vtable", c_void_p),               # 0x0000
        ("h0004", c_uint32),                # 0x0004 Ptr PlayerModelFile?
        ("h0008", c_uint32),                # 0x0008
        ("h000C", c_uint32),                # 0x000C
        ("left_hand_ptr", POINTER(ItemDataStruct)),   # 0x0010 Ptr Bow, Hammer, Focus, Daggers, Scythe
        ("right_hand_ptr", POINTER(ItemDataStruct)),  # 0x0014 Ptr Sword, Spear, Staff, Daggers, Axe, Zepter, Bundle
        ("h0018", c_uint32),                # 0x0018
        ("shield_ptr", POINTER(ItemDataStruct)),  # 0x001C Ptr Shield
        ("left_hand_map", c_uint8),         # 0x0020 Weapon1     None = 9, Bow = 0, Hammer = 0, Focus = 1, Daggers = 0, Scythe = 0
        ("right_hand_map", c_uint8),        # 0x0021 Weapon2     None = 9, Sword = 0, Spear = 0, Staff = 0, Daggers = 0, Axe = 0, Zepter = 0, Bundle
        ("head_map", c_uint8),              # 0x0022
        ("shield_map", c_uint8),            # 0x0023

        # ---- 0x0024 .. 0x00B3 ----
        ("items_union", EquipmentItemsUnionStruct),

        # ---- 0x00B4 .. 0x00D7 ----
        ("ids_union", EquipmentItemIDsUnionStruct),
    ]
    
    # ---------- SAFE ACCESSORS ----------
    @property
    def left_hand(self) -> Optional[ItemDataStruct]:
        # example mapping logic – adapt to your map values
        idx = self.left_hand_map
        if 0 <= idx < 9:
            return self.items_union.items[idx]
        return None

    
    @property
    def right_hand(self) -> Optional[ItemDataStruct]:
        """Return the right hand item data if available."""
        idx = self.right_hand_map
        if 0 <= idx < 9:
            return self.items_union.items[idx]
        return None
    
    @property
    def shield(self) -> Optional[ItemDataStruct]:
        """Return the shield item data if available."""
        idx = self.shield_map
        if 0 <= idx < 9:
            return self.items_union.items[idx]
        
    # ---------- SNAPSHOT ----------
    def snapshot(self) -> Equipment:
        return Equipment(
            vtable=int(self.vtable) if self.vtable else 0,
            h0004=int(self.h0004),
            h0008=int(self.h0008),
            h000C=int(self.h000C),
            h0018=int(self.h0018),
            left_hand_map=int(self.left_hand_map),
            right_hand_map=int(self.right_hand_map),
            head_map=int(self.head_map),
            shield_map=int(self.shield_map),

            items_union=self.items_union.snapshot(),
            ids_union=self.ids_union.snapshot(),
            
            left_hand=self.left_hand.snapshot() if self.left_hand else None,
            right_hand=self.right_hand.snapshot() if self.right_hand else None,
            shield=self.shield.snapshot() if self.shield else None,

        )

# ---------------------------------------------------------------------
# ----------------------- TagInfo -------------------------------------
# ---------------------------------------------------------------------
@dataclass(slots=True)
class TagInfo:
    guild_id: int
    primary: int
    secondary: int
    level: int

class TagInfoStruct (Structure):
    _pack_ = 1
    _fields_ = [
        ("guild_id", c_uint16),    # +0x0000
        ("primary", c_uint8),      # +0x0002
        ("secondary", c_uint8),    # +0x0003
        ("level", c_uint16),       # +0x0004
        # ... (possible more fields)
    ]
    def snapshot(self) -> TagInfo:
        return TagInfo(
            guild_id=int(self.guild_id),
            primary=int(self.primary),
            secondary=int(self.secondary),
            level=int(self.level),
        )

# ---------------------------------------------------------------------
# ------------------ VisibleEffect ------------------------------------
# ---------------------------------------------------------------------

@dataclass(slots=True)
class VisibleEffect:
    unk: int
    id: int
    has_ended: int


class VisibleEffectStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("unk", c_uint32),        # enchantment = 1, weapon spell = 9
        ("id", c_uint32),         # Constants::EffectID
        ("has_ended", c_uint32),  # effect no longer active
    ]

    def snapshot(self) -> VisibleEffect:
        return VisibleEffect(
            unk=int(self.unk),
            id=int(self.id),
            has_ended=int(self.has_ended),
        )
        
    
# ---------------------------------------------------------------------
# ------------------------ Agent --------------------------------------
# --------------------------------------------------------------------- 
@dataclass(slots=True) 
class AgentNative():
    h0004: int
    h0008: int
    h000C: list[int]
    timer: int  # Agent Instance Timer (in Frames)
    timer2: int
    agent_id: int
    z: float  # Z coord in float
    width1: float  # Width of the model's box
    height1: float  # Height of the model's box
    width2: float  # Width of the model's box (same as 1)
    height2: float  # Height of the model's box (same as 1)
    width3: float  # Width of the model's box (same as 1)
    height3: float  # Height of the model's box (same as 1)
    rotation_angle: float  # Rotation in radians from East (-pi to pi)
    rotation_cos: float  # Cosine of rotation
    rotation_sin: float  # Sine of rotation
    name_properties: int  # Bitmap basically telling what the agent is
    ground: int
    h0060: int
    terrain_normal: Vec3f
    h0070: list[int]
    pos : GamePos
    h0080: list[int]
    name_tag_x: float
    name_tag_y: float
    name_tag_z: float
    visual_effects: int
    h0092: int
    h0094: list[int]
    type: int  # Key field to determine the type of agent
    velocity: Vec2f
    h00A8: int
    rotation_cos2: float
    rotation_sin2: float
    h00B4: list[int]

    vtable: int
      
    is_item_type : bool 
    is_gadget_type : bool
    is_living_type : bool
    
    _item_agent: Optional["AgentItem"] = None
    _gadget_agent: Optional["AgentGadget"] = None
    _living_agent: Optional["AgentLiving"] = None
    
    def GetAsAgentItem(self) -> Optional["AgentItem"]:
        return self._item_agent

    def GetAsAgentGadget(self) -> Optional["AgentGadget"]:
        return self._gadget_agent

    def GetAsAgentLiving(self) -> Optional["AgentLiving"]:
        return self._living_agent
    


class AgentStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("vtable_ptr", POINTER(c_uint32)),      # 0x0000
        ("h0004", c_uint32),               # 0x0004
        ("h0008", c_uint32),               # 0x0008
        ("h000C", c_uint32 * 2),           # 0x000C
        ("timer", c_uint32),               # 0x0014 Agent Instance Timer (in Frames)
        ("timer2", c_uint32),              # 0x0018
        ("link_link", GW_TLink),                # 0x001C TLink<Agent>
        ("link2_link", GW_TLink),               # 0x0024 TLink<Agent>
        ("agent_id", c_uint32),            # 0x002C
        ("z", c_float),                    # 0x0030 Z coord in float
        ("width1", c_float),               # 0x0034 Width of the model's box
        ("height1", c_float),              # 0x0038 Height of the model's box34
        ("width2", c_float),               # 0x003C Width of the model's box (same as 1)
        ("height2", c_float),              # 0x0040 Height of the model's box (same as 1)
        ("width3", c_float),               # 0x0044 Width of the model's box (same as 1)
        ("height3", c_float),              # 0x0048 Height of the model's box (same as 1)
        ("rotation_angle", c_float),       # 0x004C Rotation in radians from East (-pi to pi)
        ("rotation_cos", c_float),         # 0x0050 Cosine of rotation
        ("rotation_sin", c_float),         # 0x0054 Sine of rotation
        ("name_properties", c_uint32),     # 0x0058 Bitmap basically telling what the agent is
        ("ground", c_uint32),              # 0x005C
        ("h0060", c_uint32),               # 0x0060
        ("terrain_normal", Vec3f),         # 0x0064
        ("h0070", c_uint8 * 4),            # 0x0070
        
        ("pos", GamePos),                # 0x0074 GamePos view

        ("h0080", c_uint8 * 4),            # 0x0080
        ("name_tag_x", c_float),           # 0x0084
        ("name_tag_y", c_float),           # 0x0088
        ("name_tag_z", c_float),           # 0x008C
        ("visual_effects", c_uint16),      # 0x0090
        ("h0092", c_uint16),               # 0x0092
        ("h0094", c_uint32 * 2),           # 0x0094
        ("type", c_uint32),                # 0x009C  <-- KEY FIELD

        ("velocity", Vec2f),               # 0x00A0
        ("h00A8", c_uint32),               # 0x00A8
        ("rotation_cos2", c_float),        # 0x00AC
        ("rotation_sin2", c_float),        # 0x00B0
        ("h00B4", c_uint32 * 4),           # 0x00B4
    ]
    
    @property
    def vtable(self) -> int:
        """Return the vtable pointer of the Agent."""
        if getattr(self, "_is_snapshot", False):
            return 0
        if not self.vtable_ptr:
            return 0
        return ctypes.addressof(self.vtable_ptr.contents)

      
    @property 
    def is_item_type(self) -> bool:
        """Return True if this Agent is an Item."""
        return (self.type & 0x400) != 0
    
    @property
    def is_gadget_type(self) -> bool:
        """Return True if this Agent is a Gadget."""
        return (self.type & 0x200) != 0
    
    @property
    def is_living_type(self) -> bool:
        """Return True if this Agent is a Living being (Player, NPC, Monster)."""
        return (self.type & 0xDB) != 0

    def snapshot(self) -> AgentNative:
        item_snapshot: Optional[AgentItem] = None
        if self.is_item_type:
            item = self.GetAsAgentItem()
            if item:
                item_snapshot = item.snapshot_item()
                
        gadget_snapshot: Optional[AgentGadget] = None
        if self.is_gadget_type:
            gadget = self.GetAsAgentGadget()
            if gadget:
                gadget_snapshot = gadget.snapshot_gadget()
                
        living_snapshot: Optional[AgentLiving] = None
        if self.is_living_type:
            living = self.GetAsAgentLiving()
            if living:
                living_snapshot = living.snapshot_living()
        
        return AgentNative(
            h0004=int(self.h0004),
            h0008=int(self.h0008),
            h000C=[int(x) for x in self.h000C],
            timer=int(self.timer),
            timer2=int(self.timer2),
            agent_id=int(self.agent_id),
            z=float(self.z),
            width1=float(self.width1),
            height1=float(self.height1),
            width2=float(self.width2),
            height2=float(self.height2),
            width3=float(self.width3),
            height3=float(self.height3),
            rotation_angle=float(self.rotation_angle),
            rotation_cos=float(self.rotation_cos),
            rotation_sin=float(self.rotation_sin),
            name_properties=int(self.name_properties),
            ground=int(self.ground),
            h0060=int(self.h0060),
            terrain_normal=Vec3f(
                float(self.terrain_normal.x),
                float(self.terrain_normal.y),
                float(self.terrain_normal.z),
            ),
            h0070=[int(x) for x in self.h0070],
            pos=self.pos,
            h0080=[int(x) for x in self.h0080],
            name_tag_x=float(self.name_tag_x),
            name_tag_y=float(self.name_tag_y),
            name_tag_z=float(self.name_tag_z),
            visual_effects=int(self.visual_effects),
            h0092=int(self.h0092),
            h0094=[int(x) for x in self.h0094],
            type=int(self.type),
            velocity=Vec2f(
                float(self.velocity.x),
                float(self.velocity.y),
            ),
            h00A8=int(self.h00A8),
            rotation_cos2=float(self.rotation_cos2),
            rotation_sin2=float(self.rotation_sin2),
            h00B4=[int(x) for x in self.h00B4],
            vtable=self.vtable,
            is_item_type=self.is_item_type,
            is_gadget_type=self.is_gadget_type,
            is_living_type=self.is_living_type,
        
            _item_agent=item_snapshot,
            _gadget_agent=gadget_snapshot,
            _living_agent=living_snapshot,
        )
        
    # ---------------------------------------------------------
    # ---  reinterpret this Agent as its derived type       ---
    # ---  identical semantics to C++ static_cast<T*>(this) ---
    # ---------------------------------------------------------
    
    def GetAsAgentItem(self) -> Optional["AgentItemStruct"]:
        if self.is_item_type:
            return ctypes.cast(ctypes.pointer(self), ctypes.POINTER(AgentItemStruct)).contents
        return None

    def GetAsAgentGadget(self) -> Optional["AgentGadgetStruct"]:
        if self.is_gadget_type:
            return ctypes.cast(ctypes.pointer(self), ctypes.POINTER(AgentGadgetStruct)).contents
        return None

    def GetAsAgentLiving(self) -> Optional["AgentLivingStruct"]:
        if self.is_living_type:
            return ctypes.cast(ctypes.pointer(self), ctypes.POINTER(AgentLivingStruct)).contents
        return None
    
# ---------------------------------------------------------------------
# ------------------ AgentLiving --------------------------------------
# ---------------------------------------------------------------------
@dataclass(slots=True)
class AgentLiving:
    owner : int
    h00C8 : int
    h00CC : int
    h00D0 : int
    h00D4 : list[int]
    animation_type : float
    h00E4 : list[int]
    weapon_attack_speed : float  # The base attack speed in float of last attacks weapon. 1.33 = axe, sWORD, daggers etc.
    attack_speed_modifier : float  # Attack speed modifier of the last attack. 0.67 = 33% increase (1-.33)
    player_number : int  # player number / modelnumber
    agent_model_type : int  # Player = 0x3000, NPC = 0x2000
    transmog_npc_id : int  # Actually, it's 0x20000000 | npc_id, It's not defined for npc, minipet, etc...
    h0100 : int
    h0104 : int  # New variable added here
    h010C : int
    primary : int  # Primary profession 0-10 (None,W,R,Mo
    secondary : int # Secondary profession 0-10 (None,W,R,Mo,N,Me,E,A,Rt,P,D)
    level : int
    team_id : int # 0=None, 1=Blue, 2=Red, 3=Yellow
    h0112 : list[int]
    h0114 : int
    energy_regen : float
    h011C : int
    energy : float
    max_energy : int
    h0128 : int
    hp_pips : float
    h0130 : int
    hp : float
    max_hp : int
    effects : int #Bitmap for effects to display when targetted. DOES include hexes
    h0140 : int
    hex : int # Bitmap for the hex effect when targetted (apparently obsolete!) (
    h0145 : list[int]
    model_state : int
    type_map : int #Odd variable! 0x08 = dead, 0xC00 = boss, 0x40000 = spirit, 0x400000 = player
    h0160 : list[int]
    in_spirit_range : int #Tells if agent is within spirit range of you. Doesn't work anymore?
    h0180 : int
    login_number : int #Unique number in instance that only works for players
    animation_speed : float #Speed of the current animation
    animation_code : int #related to animations
    animation_id : int   #Id of the current animation
    h0194 : list[int]
    dagger_status : int            #0x1 = used lead attack, 0x2
    allegiance : int               #Constants::Allegiance; 0x1 = ally/non-attackable, 0x2 = neutral, 0x3 = enemy, 0x4 = spirit/pet, 0x5 = minion, 0x6 = npc/minipet
    weapon_type : int             #1=bow, 2=axe, 3=hammer, 4=daggers, 5=scythe, 6=spear, 7=sWORD, 10=wand, 12=staff, 14=staff
    skill : int                   #0 = not using a skill. Anything else is the Id of
    h01BA : int
    weapon_item_type : int
    offhand_item_type : int
    weapon_item_id : int
    offhand_item_id : int

    equipment: Optional[Equipment]
    tags: Optional[TagInfo]
    visible_effects: List[VisibleEffect]
    is_bleeding: bool
    is_conditioned: bool
    is_crippled: bool
    is_dead: bool
    is_deep_wounded: bool
    is_poisoned: bool
    is_enchanted: bool
    is_degen_hexed: bool
    is_hexed: bool
    is_weapon_spelled: bool
    is_in_combat_stance: bool
    has_quest: bool
    is_dead_by_type_map: bool
    is_female: bool
    has_boss_glow: bool
    is_hiding_cape: bool
    can_be_viewed_in_party_window: bool
    is_spawned: bool
    is_being_observed: bool
    
    is_knocked_down: bool
    is_moving: bool
    
    is_attacking: bool
    is_casting: bool
    is_idle: bool
    is_alive: bool
    is_player: bool
    is_npc: bool

class AgentLivingStruct(AgentStruct):
    _pack_ = 1
    _fields_ = [
        # Derived from Agent struct fields up to +0x00B8
        ("owner", c_uint32),
        ("h00C8", c_uint32),
        ("h00CC", c_uint32),
        ("h00D0", c_uint32),
        ("h00D4", c_uint32 * 3),
        ("animation_type", c_float),
        ("h00E4", c_uint32 * 2),
        ("weapon_attack_speed", c_float), #The base attack speed in float of last attacks weapon. 1.33 = axe, sWORD, daggers etc.
        ("attack_speed_modifier", c_float), #Attack speed modifier of the last attack. 0.67 = 33% increase (1-.33)
        ("player_number", c_uint16), #player number / modelnumber
        ("agent_model_type", c_uint16), #Player = 0x3000, NPC = 0x2000
        ("transmog_npc_id", c_uint32), #Actually, it's 0x20000000 | npc_id, It's not defined for npc, minipet, etc...
        ("equipment_ptr_ptr", POINTER(POINTER(EquipmentStruct))),  # Equipment**
        ("h0100", c_uint32),
        ("h0104", c_uint32),  # New variable added here
        ("tags_ptr", POINTER(TagInfoStruct)),  # TagInfo
        ("h010C", c_uint16),
        ("primary", c_uint8),  # Primary profession 0-10 (None,W,R,Mo,N,Me,E,A,Rt,P,D)
        ("secondary", c_uint8), # Secondary profession 0-10 (None,W,R,Mo,N,Me,E,A,Rt,P,D)
        ("level", c_uint8),
        ("team_id", c_uint8), # 0=None, 1=Blue, 2=Red, 3=Yellow
        ("h0112", c_uint8 * 2),
        ("h0114", c_uint32),
        ("energy_regen", c_float),
        ("h011C", c_uint32),
        ("energy", c_float),
        ("max_energy", c_uint32),
        ("h0128", c_uint32), #overcast
        ("hp_pips", c_float),
        ("h0130", c_uint32),
        ("hp", c_float),
        ("max_hp", c_uint32),
        ("effects", c_uint32), #Bitmap for effects to display when targetted. DOES include hexes
        ("h0140", c_uint32),
        ("hex", c_uint8), # Bitmap for the hex effect when targetted (apparently obsolete!) (yes)
        ("h0145", c_uint8 * 19),
        ("model_state", c_uint32),
        ("type_map", c_uint32), #Odd variable! 0x08 = dead, 0xC00 = boss, 0x40000 = spirit, 0x400000 = player
        ("h0160", c_uint32 * 4),
        ("in_spirit_range", c_uint32), #Tells if agent is within spirit range of you. Doesn't work anymore?
        ("visible_effects_list", GW_TList), #TList<VisibleEffect>
        ("h0180", c_uint32),
        ("login_number", c_uint32), #Unique number in instance that only works for players
        ("animation_speed", c_float), #Speed of the current animation
        ("animation_code", c_uint32), #related to animations
        ("animation_id", c_uint32),   #Id of the current animation
        ("h0194", c_uint8 * 32),
        ("dagger_status", c_uint8),            #0x1 = used lead attack, 0x2 = used offhand attack, 0x3 = used dual attack
        ("allegiance", c_uint8),               #Constants::Allegiance; 0x1 = ally/non-attackable, 0x2 = neutral, 0x3 = enemy, 0x4 = spirit/pet, 0x5 = minion, 0x6 = npc/minipet
        ("weapon_type", c_uint16),             #1=bow, 2=axe, 3=hammer, 4=daggers, 5=scythe, 6=spear, 7=sWORD, 10=wand, 12=staff, 14=staff
        ("skill", c_uint16),                   #0 = not using a skill. Anything else is the Id of that skill
        ("h01BA", c_uint16),
        ("weapon_item_type", c_uint8),
        ("offhand_item_type", c_uint8),
        ("weapon_item_id", c_uint16),
        ("offhand_item_id", c_uint16),
    ]
    
    # ---- snapshot-safe properties ----
    @property
    def equipment(self) -> Optional["EquipmentStruct"]:
        if getattr(self, "_is_snapshot", False):
            return getattr(self, "_equipment_snapshot", None)
        if self.equipment_ptr_ptr and self.equipment_ptr_ptr.contents:
            return self.equipment_ptr_ptr.contents.contents
        return None
    
    @property
    def tags(self) -> Optional["TagInfoStruct"]:
        if getattr(self, "_is_snapshot", False):
            return getattr(self, "_tags_snapshot", None)
        if self.tags_ptr:
            return self.tags_ptr.contents
        return None

    @property
    def visible_effects(self) -> List["VisibleEffectStruct"]:
        if getattr(self, "_is_snapshot", False):
            return getattr(self, "_visible_effects_snapshot", [])
        return GW_TList_View(self.visible_effects_list, VisibleEffectStruct).to_list()

    @property
    def is_bleeding(self) -> bool:
        """Return True if the agent is bleeding."""
        return (self.effects & 0x0001) != 0
    @property
    def is_conditioned(self) -> bool:
        """Return True if the agent is conditioned."""
        return (self.effects & 0x0002) != 0
    @property
    def is_crippled(self) -> bool:
        """Return True if the agent is crippled."""
        return (self.effects & 0x000A) == 0xA
    @property
    def is_dead(self) -> bool:
        """Return True if the agent is dead."""
        return (self.effects & 0x0010) != 0
    @property
    def is_deep_wounded(self) -> bool:
        """Return True if the agent is deep wounded."""
        return (self.effects & 0x0020) != 0
    @property
    def is_poisoned(self) -> bool:
        """Return True if the agent is poisoned."""
        return (self.effects & 0x0040) != 0
    @property
    def is_enchanted(self) -> bool:
        """Return True if the agent is enchanted."""
        return (self.effects & 0x0080) != 0
    @property
    def is_degen_hexed(self) -> bool:
        """Return True if the agent is degen hexed."""
        return (self.effects & 0x0400) != 0
    @property
    def is_hexed(self) -> bool:
        """Return True if the agent is hexed."""
        return (self.effects & 0x0800) != 0
    @property
    def is_weapon_spelled(self) -> bool:
        """Return True if the agent is weapon spelled."""
        return (self.effects & 0x8000) != 0
    @property
    def is_in_combat_stance(self) -> bool:
        """Return True if the agent is in combat stance."""
        return (self.type_map & 0x000001) != 0
    @property
    def has_quest(self) -> bool:
        """Return True if the agent has a quest."""
        return (self.type_map & 0x000002) != 0
    @property
    def is_dead_by_type_map(self) -> bool:
        """Return True if the agent is dead by type map."""
        return (self.type_map & 0x000008) != 0
    @property
    def is_female(self) -> bool:
        """Return True if the agent is female."""
        return (self.type_map & 0x000200) != 0
    @property
    def has_boss_glow(self) -> bool:
        """Return True if the agent has boss glow."""
        return (self.type_map & 0x000400) != 0
    @property
    def is_hiding_cape(self) -> bool:
        """Return True if the agent is hiding cape."""
        return (self.type_map & 0x001000) != 0
    
    @property
    def can_be_viewed_in_party_window(self) -> bool:
        """Return True if the agent can be viewed in party window."""
        return (self.type_map & 0x20000) != 0
    
    @property
    def is_spawned(self) -> bool:   
        """Return True if the agent is spawned."""
        return (self.type_map & 0x040000) != 0
    @property
    def is_being_observed(self) -> bool:
        """Return True if the agent is being observed."""
        return (self.type_map & 0x400000) != 0
    
    @property
    def is_knocked_down(self) -> bool:
        """Return True if the agent is knocked down."""
        return (self.model_state == 1104)
    @property
    def is_moving(self) -> bool:
        """Return True if the agent is moving."""
        return (self.model_state == 12 or self.model_state == 76 or self.model_state == 204)
    
    @property
    def is_attacking(self) -> bool:
        """Return True if the agent is attacking."""
        return (self.model_state == 96 or self.model_state == 1088 or self.model_state == 1120)
    @property
    def is_casting(self) -> bool:
        """Return True if the agent is casting."""
        return (self.model_state == 65 or self.model_state == 581)
    
    @property
    def is_idle(self) -> bool:
        """Return True if the agent is idle."""
        return (self.model_state == 68 or self.model_state == 64 or self.model_state == 100)
    
    @property
    def is_alive(self) -> bool:
        """Return True if the agent is alive."""
        return not self.is_dead and self.hp > 0.0
    @property 
    def is_player(self) -> bool:
        """Return True if the agent is a player."""
        return self.login_number != 0
    
    @property
    def is_npc(self) -> bool:
        """Return True if the agent is an NPC."""
        return self.login_number == 0  

    def snapshot_living(self) -> AgentLiving:

        return AgentLiving(
            owner=int(self.owner),
            h00C8=int(self.h00C8),
            h00CC=int(self.h00CC),
            h00D0=int(self.h00D0),
            h00D4=[int(self.h00D4[i]) for i in range(3)],
            animation_type=float(self.animation_type),
            h00E4=[int(self.h00E4[i]) for i in range(2)],
            weapon_attack_speed=float(self.weapon_attack_speed),
            attack_speed_modifier=float(self.attack_speed_modifier),
            player_number=int(self.player_number),
            agent_model_type=int(self.agent_model_type),
            transmog_npc_id=int(self.transmog_npc_id),
            h0100=int(self.h0100),
            h0104=int(self.h0104),
            h010C=int(self.h010C),
            primary=int(self.primary),
            secondary=int(self.secondary),
            level=int(self.level),
            team_id=int(self.team_id),
            h0112=[int(self.h0112[i]) for i in range(2)],
            h0114=int(self.h0114),
            energy_regen=float(self.energy_regen),
            h011C=int(self.h011C),
            energy=float(self.energy),
            max_energy=int(self.max_energy),
            h0128=int(self.h0128),
            hp_pips=float(self.hp_pips),
            h0130=int(self.h0130),
            hp=float(self.hp),
            max_hp=int(self.max_hp),
            effects=int(self.effects),
            h0140=int(self.h0140),
            hex=int(self.hex),
            h0145=[int(self.h0145[i]) for i in range(19)],
            model_state=int(self.model_state),
            type_map=int(self.type_map),
            h0160=[int(self.h0160[i]) for i in range(4)],
            in_spirit_range=int(self.in_spirit_range),
            h0180=int(self.h0180),
            login_number=int(self.login_number),
            animation_speed=float(self.animation_speed),
            animation_code=int(self.animation_code),
            animation_id=int(self.animation_id),
            h0194=[int(self.h0194[i]) for i in range(32)],
            dagger_status=int(self.dagger_status),
            allegiance=int(self.allegiance),
            weapon_type=int(self.weapon_type),
            skill=int(self.skill),
            h01BA=int(self.h01BA),
            weapon_item_type=int(self.weapon_item_type),
            offhand_item_type=int(self.offhand_item_type),
            weapon_item_id=int(self.weapon_item_id),
            offhand_item_id=int(self.offhand_item_id),
            equipment= self.equipment.snapshot() if self.equipment else None,   
            tags= self.tags.snapshot() if self.tags else None,
            visible_effects= [ve.snapshot() for ve in self.visible_effects] if self.visible_effects else [],
            is_bleeding=self.is_bleeding,
            is_conditioned=self.is_conditioned,
            is_crippled=self.is_crippled,
            is_dead=self.is_dead,
            is_deep_wounded=self.is_deep_wounded,
            is_poisoned=self.is_poisoned,
            is_enchanted=self.is_enchanted,
            is_degen_hexed=self.is_degen_hexed,
            is_hexed=self.is_hexed,
            is_weapon_spelled=self.is_weapon_spelled,
            is_in_combat_stance=self.is_in_combat_stance,
            has_quest=self.has_quest,
            is_dead_by_type_map=self.is_dead_by_type_map,
            is_female=self.is_female,
            has_boss_glow=self.has_boss_glow,
            is_hiding_cape=self.is_hiding_cape,
            can_be_viewed_in_party_window=self.can_be_viewed_in_party_window,
            is_spawned=self.is_spawned,
            is_being_observed=self.is_being_observed,
            is_knocked_down=self.is_knocked_down,
            is_moving=self.is_moving,
            is_attacking=self.is_attacking,
            is_casting=self.is_casting,
            is_idle=self.is_idle,
            is_alive=self.is_alive,
            is_player=self.is_player,
            is_npc=self.is_npc,
        )

# ---------------------------------------------------------------------
# ------------------ AgentItem ----------------------------------------
# ---------------------------------------------------------------------

@dataclass(slots=True)
class AgentItem:
    owner: int
    item_id: int
    h00CC: int
    extra_type: int

class AgentItemStruct(AgentStruct):
    _pack_ = 1
    _fields_ = [
        ("owner", c_uint32),        # +0x00C4 AgentID
        ("item_id", c_uint32),      # +0x00C8 ItemID
        ("h00CC", c_uint32),        # +0x00CC
        ("extra_type", c_uint32),   # +0x00D0
    ]

    def snapshot_item(self) -> AgentItem:
        return AgentItem(
            owner=int(self.owner),
            item_id=int(self.item_id),
            h00CC=int(self.h00CC),
            extra_type=int(self.extra_type),
        )

# ---------------------------------------------------------------------
# ------------------ AgentGadget --------------------------------------
# ---------------------------------------------------------------------

@dataclass(slots=True)
class AgentGadget:
    h00C4: int
    h00C8: int
    extra_type: int
    gadget_id: int
    h00D4: tuple[int, int, int, int]


class AgentGadgetStruct(AgentStruct):
    _pack_ = 1
    _fields_ = [
        ("h00C4", c_uint32),        # +0x00C4
        ("h00C8", c_uint32),        # +0x00C8
        ("extra_type", c_uint32),   # +0x00CC
        ("gadget_id", c_uint32),    # +0x00D0
        ("h00D4", c_uint32 * 4),    # +0x00D4
    ]

    def snapshot_gadget(self) -> AgentGadget:
        return AgentGadget(
            h00C4=int(self.h00C4),
            h00C8=int(self.h00C8),
            extra_type=int(self.extra_type),
            gadget_id=int(self.gadget_id),
            h00D4=(
                int(self.h00D4[0]),
                int(self.h00D4[1]),
                int(self.h00D4[2]),
                int(self.h00D4[3]),
            ),
        )
        

 
   
class AgentArrayStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_array", GW_Array),        # +0x00C4 Array<Agent*>
    ]
    def _ensure_fields(self):
        if not hasattr(self, "_allegiance_cache"):
            self._allegiance_cache = None
        if not hasattr(self, "_agent_by_id"):
            self._agent_by_id = {}
        if not hasattr(self, "_last_instance_timer"):
            self._last_instance_timer = 0
        if not hasattr(self, "frame_counter"):
            self.frame_counter = 0
        if not hasattr(self, "frame_throttle"):
            self.frame_throttle = 2

        
    @property
    def raw_agents(self) -> list[AgentStruct | None]:
        """
        Mirror C++: Array<Agent*> agent_array;

        - Uses GW_Array_Value_View with elem_type = POINTER(Agent)
        - Keeps None where the engine has a NULL Agent*
        """
        arr = self.agent_array
        if not arr.m_buffer or arr.m_size == 0:
            return []

        # Array<Agent*> → value type is POINTER(Agent)
        ptrs = GW_Array_Value_View(arr, POINTER(AgentStruct)).to_list()
        if not ptrs:
            return []

        out: list[AgentStruct | None] = []
        for ptr in ptrs:
            # NULL pointer → bool(ptr) is False
            if not ptr:
                out.append(None)
                continue
            try:
                out.append(ptr.contents)
            except ValueError:
                # extra safety: if ctypes still complains, treat as None
                out.append(None)

        return out
    
    def _drop_cache(self) -> None:
        self._allegiance_cache = None
        self._agent_by_id = {}
        self._last_instance_timer = 0
    
    def _ensure_cache_up_to_date(self):
        """
        Uses instance_timer to detect map changes, same logic as GWCA.
        Refreshes only when needed.
        """
        self._ensure_fields()
        
        # ---- validity checks ----
        map_ctx = MapContext.get_context()
        char_ctx = CharContext.get_context()
        instance_info_ctx = InstanceInfo.get_context()
        world_ctx = WorldContext.get_context()
        acc_agent_ctx = AccAgentContext.get_context()


        if not (map_ctx and char_ctx and instance_info_ctx and world_ctx and acc_agent_ctx):
            self._drop_cache()
            return
        
        instance_type = instance_info_ctx.instance_type
        if instance_type not in (0, 1):  # explorable, story, pvp
            self._drop_cache()
            return
        
        if (char_ctx.player_number is None):
            self._drop_cache()
            return
        
        #per frame cache, not throttling
        #self.frame_counter += 3
        #if self.frame_counter < self.frame_throttle:
        #    return
        #self.frame_counter = 0
        
        self._build_allegiance_cache()
        
    def _iter_valid_agents(self):
        for agent in self.raw_agents:
            if not agent:
                continue
            if agent.agent_id != 0:
                yield agent
                
    

    def _build_allegiance_cache(self):
        """Populate ALL allegiance/type lists in a single traversal."""
        self._ensure_fields()
        
        acc_agent_ctx = AccAgentContext.get_context()
        if not acc_agent_ctx:
            self._drop_cache()
            return

        valid_agents_ids = acc_agent_ctx.valid_agents_ids
        if not valid_agents_ids:
            self._drop_cache()
            return

        cache = {
            "ally": [],
            "neutral": [],
            "enemy": [],
            "spirit_pet": [],
            "minion": [],
            "npc_minipet": [],
            "living": [],
            "item": [],
            "owned_item": [],
            "gadget": [],
            "dead_ally": [],
            "dead_enemy": [],
            "all": [],
        }
        
        agent_by_id: dict[int, "AgentStruct"] = {}
        
        # Single iteration — uses movement-valid agents only
        for agent in self._iter_valid_agents():
            if agent.agent_id not in valid_agents_ids:
                continue
            
            # ---- CRITICAL: snapshot NOW (Python-owned) ----
            aid = agent.agent_id
            if aid == 0:
                continue
            
            cache["all"].append(aid)
            agent_by_id[aid] = agent
            
            if agent.is_gadget_type:
                cache["gadget"].append(aid)
                continue
            
            if agent.is_item_type:
                item:AgentItemStruct| None = agent.GetAsAgentItem()
                if item is None:
                    continue

                if item and item.owner!= 0:
                    cache["owned_item"].append(aid)
                
                cache["item"].append(aid)
                continue
            
            # ---------- LIVING types ----------
            if not agent.is_living_type:
                continue

            living = agent.GetAsAgentLiving()
            if not living:
                continue
            
            cache["living"].append(aid)

            """ 1: "ally",
                2: "neutral",
                3: "enemy",
                4: "spirit_pet",
                5: "minion",
                6: "npc_minipet","""
                   
            match living.allegiance:
                case 1:
                    cache["ally"].append(aid)
                    if living.is_dead:
                        cache["dead_ally"].append(aid)
                case 2:
                    cache["neutral"].append(aid)
                case 3:
                    cache["enemy"].append(aid)
                    if living.is_dead:
                        cache["dead_enemy"].append(aid)
                case 4:
                    cache["spirit_pet"].append(aid)
                case 5:
                    cache["minion"].append(aid)
                case 6:
                    cache["npc_minipet"].append(aid)
            
        self._allegiance_cache = cache
        self._agent_by_id = agent_by_id


    
    # ------------------------------------------------------------
    # O(1) lookup (uses the snapshot dictionary built per frame)
    # ------------------------------------------------------------
    def GetAgentByID(self, agent_id: int) -> Optional["AgentStruct"]:
        self._ensure_fields()
        
        map_ctx = MapContext.get_context()
        char_ctx = CharContext.get_context()
        instance_info_ctx = InstanceInfo.get_context()
        world_ctx = WorldContext.get_context()
        acc_agent_ctx = AccAgentContext.get_context()

        if not (map_ctx and char_ctx and instance_info_ctx and world_ctx and acc_agent_ctx):
            self._drop_cache()
            return None
        
        instance_type = instance_info_ctx.instance_type
        if instance_type not in (0, 1):  # explorable, story, pvp
            self._drop_cache()
            return None
        
        agent =  self._agent_by_id.get(agent_id)
        return agent


    
    #AgentArray
    def GetAgentArray(self) -> list[int]:
        """Retrieve the raw agent array as a list of AgentIDs."""
        #self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("all", [])
    
    #AllyArray
    def GetAllyArray(self) -> list[int]:
        """Retrieve the ally agent array as a list of AgentIDs."""
        #self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("ally", [])
    
    #neutral
    def GetNeutralArray(self) -> list[int]:
        """Retrieve the neutral agent array as a list of AgentIDs."""
        #self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("neutral", [])
    
    #enemy
    def GetEnemyArray(self) -> list[int]:
        """Retrieve the enemy agent array as a list of AgentIDs."""
        #self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("enemy", [])
    
    #spirit_pet
    def GetSpiritPetArray(self) -> list[int]:
        """Retrieve the spirit/pet agent array as a list of AgentIDs."""
        #self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("spirit_pet", [])
    
    #minion
    
    def GetMinionArray(self) -> list[int]:
        """Retrieve the minion agent array as a list of AgentIDs."""
        #self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("minion", [])
    
    #npc-minipet
    def GetNPCMinipetArray(self) -> list[int]:
        """Retrieve the NPC/minipet agent array as a list of AgentIDs."""
        #self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("npc_minipet", [])
    
    
    #item
    def GetItemAgentArray(self) -> list[int]:
        """Retrieve the item agent array as a list of AgentIDs."""
        #self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("item", [])
    
    #owned item
    def GetOwnedItemAgentArray(self) -> list[int]:
        """Retrieve the owned item agent array as a list of AgentIDs."""
        #self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("owned_item", [])
    
    #gadget
    def GetGadgetAgentArray(self) -> list[int]:
        """Retrieve the gadget agent array as a list of AgentIDs."""
        #self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("gadget", [])
    

    #dead ally/enemy
    def GetDeadAllyArray(self) -> list[int]:
        """Retrieve the dead ally agent array as a list of AgentIDs."""
        #self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("dead_ally", [])
    

    def GetDeadEnemyArray(self) -> list[int]:
        """Retrieve the dead enemy agent array as a list of AgentIDs."""
        #self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("dead_enemy", [])
    

    
    
    
AgentArray_GetPtr = NativeSymbol(
    name="GetInstanceInfoPtr",
    pattern=b"\x8b\x0c\x90\x85\xc9\x74\x19",
    mask="xxxxxxx",
    offset=-0x4,  
    section=ScannerSection.TEXT
)

#region facade
class AgentArray:
    _ptr: int = 0
    _cached_ptr: int = 0
    _cached_ctx: AgentArrayStruct | None = None
    _callback_name_ptr = "AgentArray.UpdatePtr"
    _callback_name_cache = "AgentArray.UpdateCache"

    @staticmethod
    def get_ptr() -> int:
        return AgentArray._ptr    
    @staticmethod
    def _update_ptr():
        ptr = AgentArray_GetPtr.read_ptr()
        AgentArray._ptr = ptr
        if not ptr:
            AgentArray._cached_ctx = None
            return
        AgentArray._cached_ctx = cast(
            ptr,
            POINTER(AgentArrayStruct)
        ).contents

    @staticmethod
    def _update_cache():
        ctx = AgentArray.get_context()
        if not ctx:
            return
        ctx._ensure_cache_up_to_date()

    @staticmethod
    def enable():
        import PyCallback
        PyCallback.PyCallback.Register(
            AgentArray._callback_name_ptr,
            PyCallback.Phase.PreUpdate,
            AgentArray._update_ptr,
            priority=6,
            context=PyCallback.Context.Draw
        )

        PyCallback.PyCallback.Register(
            AgentArray._callback_name_cache,
            PyCallback.Phase.Data,
            AgentArray._update_cache,
            priority=0,
            context=PyCallback.Context.Draw
        )  


    @staticmethod
    def disable():
        import PyCallback
        PyCallback.PyCallback.RemoveByName(AgentArray._callback_name_ptr)
        PyCallback.PyCallback.RemoveByName(AgentArray._callback_name_cache)
        AgentArray._ptr = 0
        AgentArray._cached_ctx = None

    @staticmethod
    def get_context() -> AgentArrayStruct | None:
        return AgentArray._cached_ctx
    
          
AgentArray.enable()

