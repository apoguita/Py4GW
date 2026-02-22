from typing import List, Optional
from ..internals.types import CPointer
from ..internals.gw_array import GW_Array
from ..internals.gw_list import GW_TList, GW_TLink
from ..internals.types import Vec2f, Vec3f, GamePos
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

class DyeInfoStruct():
    dye_tint: int
    dye1: int
    dye2: int
    dye3: int
    dye4: int
    
    def snapshot(self) -> DyeInfo: ...
    
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
    
class ItemDataStruct():
    model_file_id: int
    type: int  # enum stored as uint32_t
    dye: DyeInfoStruct
    value: int
    interaction: int
    
    def snapshot(self) -> "ItemDataStruct": ...
    
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


class EquipmentItemsUnionStruct():
    items : list[ItemDataStruct]
    weapon : ItemDataStruct
    offhand : ItemDataStruct
    chest : ItemDataStruct
    legs : ItemDataStruct
    head : ItemDataStruct
    feet : ItemDataStruct
    hands : ItemDataStruct
    costume_body : ItemDataStruct
    costume_head : ItemDataStruct
    
    def snapshot(self) -> "EquipmentItemsUnion": ...
    
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

class EquipmentItemIDsUnionStruct():
    item_ids: list[int]
    item_id_weapon: int
    item_id_offhand: int
    item_id_chest: int
    item_id_legs: int
    item_id_head: int
    item_id_feet: int
    item_id_hands: int
    item_id_costume_body: int
    item_id_costume_head: int
    
    def snapshot(self) -> "EquipmentItemIDsUnion": ...
 
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
   
class EquipmentStruct():
    vtable : int
    h0004 : int
    h0008 : int
    h000C : int
    left_hand_ptr : Optional[CPointer[ItemDataStruct]]
    right_hand_ptr : Optional[CPointer[ItemDataStruct]]
    h0018 : int
    shield_ptr : Optional[CPointer[ItemDataStruct]]
    left_hand_map : int
    right_hand_map : int
    head_map : int
    shield_map : int
    items_union : EquipmentItemsUnion
    ids_union : EquipmentItemIDsUnion
    
    def snapshot(self) -> "Equipment": ...

    @property 
    def left_hand(self) -> Optional[ItemDataStruct]:...
    
    @property
    def right_hand(self) -> Optional[ItemDataStruct]:...
    
    @property
    def shield(self) -> Optional[ItemDataStruct]:...

# ---------------------------------------------------------------------
# ----------------------- TagInfo -------------------------------------
# ---------------------------------------------------------------------
@dataclass(slots=True)
class TagInfo:
    guild_id: int
    primary: int
    secondary: int
    level: int

class TagInfoStruct ():
    guild_id: int
    primary: int
    secondary: int
    level: int
    # ... (possible more fields)
    def snapshot(self) -> "TagInfo": ...

# ---------------------------------------------------------------------
# ------------------ VisibleEffect ------------------------------------
# ---------------------------------------------------------------------

@dataclass(slots=True)
class VisibleEffect:
    unk: int
    id: int
    has_ended: int
    
class VisibleEffectStruct ():
    unk : int
    id : int  # Constants::EffectID
    has_ended : int
    
    def snapshot(self) -> "VisibleEffect": ...
    
# ---------------------------------------------------------------------
# ------------------ AgentLiving --------------------------------------
# ---------------------------------------------------------------------
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

    equipment: Optional[EquipmentStruct]
    tags: Optional[TagInfoStruct]
    visible_effects: List[VisibleEffectStruct]
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
    equipment_ptr_ptr : Optional[CPointer[CPointer[EquipmentStruct]]]  # Equipment**
    h0100 : int
    h0104 : int  # New variable added here
    tags_ptr : Optional[TagInfoStruct]  # TagInfo
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
    visible_effects_list : GW_TList  # TList<VisibleEffect>
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

    @property
    def equipment(self) -> Optional[EquipmentStruct]:...
    
    @property
    def tags(self) ->  Optional[TagInfoStruct]:...
    
    @property
    def visible_effects(self) -> List[VisibleEffectStruct]:...
    @property
    def is_bleeding(self) -> bool:...
    @property
    def is_conditioned(self) -> bool:...
    @property
    def is_crippled(self) -> bool:...
    @property
    def is_dead(self) -> bool:...
    @property
    def is_deep_wounded(self) -> bool:...
    @property
    def is_poisoned(self) -> bool:...
    @property
    def is_enchanted(self) -> bool:...
    @property
    def is_degen_hexed(self) -> bool:...
    @property
    def is_hexed(self) -> bool:...
    @property
    def is_weapon_spelled(self) -> bool:...
    @property
    def is_in_combat_stance(self) -> bool:...
    @property
    def has_quest(self) -> bool:...
    @property
    def is_dead_by_type_map(self) -> bool:...
    @property
    def is_female(self) -> bool:...
    @property
    def has_boss_glow(self) -> bool:...
    @property
    def is_hiding_cape(self) -> bool:...
    
    @property
    def can_be_viewed_in_party_window(self) -> bool:...
    
    @property
    def is_spawned(self) -> bool:  ...
    @property
    def is_being_observed(self) -> bool:...
    
    @property
    def is_knocked_down(self) -> bool:...
    @property
    def is_moving(self) -> bool:...
    
    @property
    def is_attacking(self) -> bool:...
    @property
    def is_casting(self) -> bool:...
    
    @property
    def is_idle(self) -> bool:...
    
    @property
    def is_alive(self) -> bool:...
    @property 
    def is_player(self) -> bool:...
    @property
    def is_npc(self) -> bool:...
    
    def snapshot_living(self) -> AgentLiving: ...
    
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
    owner: int
    item_id: int
    h00CC: int
    extra_type: int
    
    def snapshot_item(self) -> AgentItem:...
    
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
    h00C4: int
    h00C8: int
    extra_type: int
    gadget_id: int
    h00D4: list[int]
    
    def snapshot_gadget(self) -> AgentGadget: ...

    
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
    
    _item_agent: Optional["AgentItem"]
    _gadget_agent: Optional["AgentGadget"]
    _living_agent: Optional["AgentLiving"]
    
    def GetAsAgentItem(self) -> Optional["AgentItem"]:
        return self._item_agent

    def GetAsAgentGadget(self) -> Optional["AgentGadget"]:
        return self._gadget_agent

    def GetAsAgentLiving(self) -> Optional["AgentLiving"]:
        return self._living_agent
       
    
class AgentStruct():
    vtable_ptr: CPointer[int]
    h0004: int
    h0008: int
    h000C: list[int]
    timer: int  # Agent Instance Timer (in Frames)
    timer2: int
    link_link: GW_TLink  # TLink<Agent>
    link2_link: GW_TLink  # TLink<Agent>
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

    @property
    def vtable(self) -> int:...
      
    @property 
    def is_item_type(self) -> bool:...
    
    @property
    def is_gadget_type(self) -> bool:...
    
    @property
    def is_living_type(self) -> bool:...
    
    def snapshot(self) -> "AgentStruct": ...
    
    def GetAsAgentItem(self) -> Optional[AgentItemStruct]:...

    def GetAsAgentGadget(self) -> Optional[AgentGadgetStruct]:...

    def GetAsAgentLiving(self) -> Optional[AgentLivingStruct]:...
    

    
class AgentArrayStruct():
    agent_array: GW_Array
    @property
    def raw_agents(self) -> list[AgentStruct | None]:...

    def _ensure_fields(self):...
        
    def _ensure_cache_up_to_date(self):...   
    def _iter_valid_agents(self):...
    def _build_allegiance_cache(self):...
    
    def GetAgentByID(self, agent_id: int) -> Optional[AgentStruct]:...
    
    def GetAgentArray(self) -> list[int]:...
    def GetAllyArray(self) -> list[int]:...
    def GetNeutralArray(self) -> list[int]:...
    def GetEnemyArray(self) -> list[int]:...
    def GetSpiritPetArray(self) -> list[int]:...
    def GetMinionArray(self) -> list[int]:...
    def GetNPCMinipetArray(self) -> list[int]:...
    def GetItemAgentArray(self) -> list[int]:...
    def GetOwnedItemAgentArray(self) -> list[int]:...
    def GetGadgetAgentArray(self) -> list[int]:...
    def GetDeadAllyArray(self) -> list[int]:...
    def GetDeadEnemyArray(self) -> list[int]:...


class AgentArray:
    @staticmethod
    def get_ptr() -> int:...  
    @staticmethod
    def _update_ptr():...
    @staticmethod
    def enable():...

    @staticmethod
    def disable():...

    @staticmethod
    def get_context() -> AgentArrayStruct | None:...
        
        