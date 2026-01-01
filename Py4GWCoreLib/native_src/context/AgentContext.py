
from Py4GW import Game
from ctypes import Structure, c_uint32, c_float, sizeof, cast, POINTER, c_wchar, c_uint8, c_uint16, c_void_p
from ctypes import Union
import ctypes
from ..context.AccAgentContext import AccAgentContext, AccAgentContextStruct
from ..internals.types import Vec2f, Vec3f, GamePos
from ..internals.gw_array import GW_Array, GW_Array_Value_View, GW_Array_View
from ..internals.gw_list import GW_TList, GW_TList_View, GW_TLink
from typing import List, Optional, Dict
from ..internals.helpers import read_wstr, encoded_wstr_to_str
from ..internals.native_symbol import NativeSymbol
from ...Scanner import Scanner, ScannerSection



class DyeInfoStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("dye_tint", c_uint8),        # 0x00
        ("dye1", c_uint8, 4),         # 0x01 low nibble
        ("dye2", c_uint8, 4),         # 0x01 high nibble
        ("dye3", c_uint8, 4),         # 0x02 low nibble
        ("dye4", c_uint8, 4),         # 0x02 high nibble
    ]

class ItemDataStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("model_file_id", c_uint32),     # 0x00
        ("type", c_uint32),              # 0x04 - enum stored as uint32_t
        ("dye", DyeInfoStruct),                # 0x08
        ("value", c_uint32),             # 0x0B / actually 0x0C aligned
        ("interaction", c_uint32),       # 0x10
    ]

class EquipmentItemsUnion(Union):
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

class EquipmentItemIDsUnion(Union):
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
        ("items_union", EquipmentItemsUnion),

        # ---- 0x00B4 .. 0x00D7 ----
        ("ids_union", EquipmentItemIDsUnion),
    ]
    @property 
    def left_hand(self) -> Optional[ItemDataStruct]:
        """Return the left hand item data if available."""
        if self.left_hand_ptr:
            return self.left_hand_ptr.contents
        return None
    
    @property
    def right_hand(self) -> Optional[ItemDataStruct]:
        """Return the right hand item data if available."""
        if self.right_hand_ptr:
            return self.right_hand_ptr.contents
        return None
    
    @property
    def shield(self) -> Optional[ItemDataStruct]:
        """Return the shield item data if available."""
        if self.shield_ptr:
            return self.shield_ptr.contents
        return None



class TagInfoStruct (Structure):
    _pack_ = 1
    _fields_ = [
        ("guild_id", c_uint16),    # +0x0000
        ("primary", c_uint8),      # +0x0002
        ("secondary", c_uint8),    # +0x0003
        ("level", c_uint16),       # +0x0004
        # ... (possible more fields)
    ]


class VisibleEffectStruct (Structure):
    _pack_ = 1
    _fields_ = [
        ("unk", c_uint32), #enchantment = 1, weapon spell = 9
        ("id", c_uint32),  # Constants::EffectID
        ("has_ended", c_uint32), #effect no longer active, effect ending animation plays.
    ]


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
    
class AgentItemStruct(AgentStruct):
    _pack_ = 1
    _fields_ = [
        ("owner", c_uint32),        # +0x00C4 AgentID
        ("item_id", c_uint32),      # +0x00C8 ItemID
        ("h00CC", c_uint32),        # +0x00CC
        ("extra_type", c_uint32),   # +0x00D0
    ]

class AgentGadgetStruct(AgentStruct):
    _pack_ = 1
    _fields_ = [
        ("h00C4", c_uint32),        # +0x00C4
        ("h00C8", c_uint32),        # +0x00C8
        ("extra_type", c_uint32),   # +0x00CC
        ("gadget_id", c_uint32),    # +0x00D0
        ("h00D4", c_uint32 * 4),    # +0x00D4
    ]
    
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
    @property
    def equipment(self) -> Optional[EquipmentStruct]:
        """Return the Equipment of the AgentLiving if available."""
        if self.equipment_ptr_ptr and self.equipment_ptr_ptr.contents:
            return self.equipment_ptr_ptr.contents.contents
        return None
    
    @property
    def tags(self) ->  Optional[TagInfoStruct]:
        """Return the TagInfo of the AgentLiving if available."""
        if self.tags_ptr:
            return self.tags_ptr.contents
        return None
    
    @property
    def visible_effects(self) -> List[VisibleEffectStruct]:
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
 
   
class AgentArrayStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_array", GW_Array),        # +0x00C4 Array<Agent*>
    ]
    def _ensure_fields(self):
        if not hasattr(self, "_allegiance_cache"):
            self._allegiance_cache = None
        if not hasattr(self, "_last_instance_timer"):
            self._last_instance_timer = 0
        if not hasattr(self, "raw_agent_list"):
            self.raw_agent_list = []
        
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
    
    def _ensure_cache_up_to_date(self):
        """
        Uses instance_timer to detect map changes, same logic as GWCA.
        Refreshes only when needed.
        """
        self._ensure_fields()
        
        acc_agent_ctx = AccAgentContext.get_context()
        if not acc_agent_ctx:
            return
        instance_timer = acc_agent_ctx.instance_timer

        if self._last_instance_timer == instance_timer:
            # cache still valid
            return

        self._last_instance_timer = instance_timer
        self._build_allegiance_cache()
        
    def _iter_valid_agents(self):
        for agent in self.raw_agents:
            if not agent:
                continue
            if agent.agent_id != 0:
                yield agent

    def _build_allegiance_cache(self):
        """Populate ALL allegiance/type lists in a single traversal."""

        self._allegiance_cache = {
            "ally": [],#-
            "neutral": [], #-
            "enemy": [], #-
            "spirit_pet": [],#-
            "minion": [], #-
            "npc_minipet": [], #-
            "living": [],#-
            "item": [], #-
            "owned_item": [], # -
            "gadget": [], #-
            "dead_ally": [],
            "dead_enemy": [],
            "all": [], #-
        }
        
        self.raw_agent_list = []

        acc_agent_ctx = AccAgentContext.get_context()
        if not acc_agent_ctx:
            self._allegiance_cache = {}
            return
        
        valid_agents_ids = acc_agent_ctx.valid_agents_ids
        if not valid_agents_ids:
            self._allegiance_cache = {}
            return 

        # Single iteration — uses movement-valid agents only
        for agent in self._iter_valid_agents():
            if agent.agent_id not in valid_agents_ids:
                continue
            
            self.raw_agent_list.append(agent)
            
            aid = agent.agent_id
            self._allegiance_cache["all"].append(aid)
            
            if agent.is_gadget_type:
                self._allegiance_cache["gadget"].append(aid)
                continue
            
            if agent.is_item_type:
                item:AgentItemStruct| None = agent.GetAsAgentItem()
                if item is None:
                    continue

                if item and item.owner!= 0:
                    self._allegiance_cache["owned_item"].append(aid)
                
                self._allegiance_cache["item"].append(aid)
                continue
            
            # ---------- LIVING types ----------
            if not agent.is_living_type:
                continue

            living = agent.GetAsAgentLiving()
            if not living:
                continue
            
            self._allegiance_cache["living"].append(aid)

            """ 1: "ally",
                2: "neutral",
                3: "enemy",
                4: "spirit_pet",
                5: "minion",
                6: "npc_minipet","""

                   
            match living.allegiance:
                case 1:
                    self._allegiance_cache["ally"].append(aid)
                    if living.is_dead:
                        self._allegiance_cache["dead_ally"].append(aid)
                case 2:
                    self._allegiance_cache["neutral"].append(aid)
                case 3:
                    self._allegiance_cache["enemy"].append(aid)
                    if living.is_dead:
                        self._allegiance_cache["dead_enemy"].append(aid)
                case 4:
                    self._allegiance_cache["spirit_pet"].append(aid)
                case 5:
                    self._allegiance_cache["minion"].append(aid)
                case 6:
                    self._allegiance_cache["npc_minipet"].append(aid)

    
    def GetAgentByID(self, agent_id: int) -> Optional[AgentStruct]:
        """Retrieve an Agent by its AgentID."""
        self._ensure_cache_up_to_date()
        for agent in self.raw_agent_list:
            if agent.agent_id == agent_id:
                return agent
        return None
    
    def GetLivingAgents(self) -> list[AgentStruct]:
        """Retrieve all living Agents (players, NPCs, monsters)."""
        self._ensure_cache_up_to_date()
        living_agents: list[AgentStruct] = []
        for agent in self.raw_agent_list:
            if agent and agent.is_living_type:
                living_agents.append(agent)
        return living_agents
    
    def GetItemAgents(self) -> list[AgentStruct]:
        """Retrieve all item Agents."""
        self._ensure_cache_up_to_date()
        item_agents: list[AgentStruct] = []
        for agent in self.raw_agent_list:
            if agent and agent.is_item_type:
                item_agents.append(agent)
        return item_agents
    
    def GetGadgetAgents(self) -> list[AgentStruct]:
        """Retrieve all gadget Agents."""
        self._ensure_cache_up_to_date()
        gadget_agents: list[AgentStruct] = []
        for agent in self.raw_agent_list:
            if agent and agent.is_gadget_type:
                gadget_agents.append(agent)
        return gadget_agents
    
    def GetAgentArray(self) -> list[int]:
        """Retrieve the raw agent array as a list of AgentIDs."""
        self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("all", [])
    
    def GetLivingAgentArray(self) -> list[int]:
        """Retrieve the living agent array as a list of AgentIDs."""
        self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("living", [])
    
    def GetItemAgentArray(self) -> list[int]:
        """Retrieve the item agent array as a list of AgentIDs."""
        self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("item", [])
    
    def GetOwnedItemAgentArray(self) -> list[int]:
        """Retrieve the owned item agent array as a list of AgentIDs."""
        self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("owned_item", [])
    
    def GetGadgetAgentArray(self) -> list[int]:
        """Retrieve the gadget agent array as a list of AgentIDs."""
        self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("gadget", [])
    

    def GetAllyArray(self) -> list[int]:
        """Retrieve the ally agent array as a list of AgentIDs."""
        self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("ally", [])
    
    def GetNeutralArray(self) -> list[int]:
        """Retrieve the neutral agent array as a list of AgentIDs."""
        self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("neutral", [])
    
    def GetEnemyArray(self) -> list[int]:
        """Retrieve the enemy agent array as a list of AgentIDs."""
        self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("enemy", [])
    
    def GetSpiritPetArray(self) -> list[int]:
        """Retrieve the spirit/pet agent array as a list of AgentIDs."""
        self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("spirit_pet", [])
    
    def GetMinionArray(self) -> list[int]:
        """Retrieve the minion agent array as a list of AgentIDs."""
        self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("minion", [])
    
    def GetNPCMinipetArray(self) -> list[int]:
        """Retrieve the NPC/minipet agent array as a list of AgentIDs."""
        self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("npc_minipet", [])
    
    def GetDeadAllyArray(self) -> list[int]:
        """Retrieve the dead ally agent array as a list of AgentIDs."""
        self._ensure_cache_up_to_date()
        if not self._allegiance_cache:
            return []
        return self._allegiance_cache.get("dead_ally", [])
    
    def GetDeadEnemyArray(self) -> list[int]:
        """Retrieve the dead enemy agent array as a list of AgentIDs."""
        self._ensure_cache_up_to_date()
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
    _callback_name = "AgentArray.UpdateAgentArrayPtr"

    @staticmethod
    def get_ptr() -> int:
        return AgentArray._ptr    
    @staticmethod
    def _update_ptr():
        AgentArray._ptr = AgentArray_GetPtr.read_ptr()

    @staticmethod
    def enable():
        Game.register_callback(
            AgentArray._callback_name,
            AgentArray._update_ptr
        )

    @staticmethod
    def disable():
        Game.remove_callback(AgentArray._callback_name)
        AgentArray._ptr = 0
        AgentArray._cached_ptr = 0
        AgentArray._cached_ctx = None

    @staticmethod
    def get_context() -> AgentArrayStruct | None:
        ptr = AgentArray._ptr
        if not ptr:
            # context lost → drop cache
            AgentArray._cached_ctx = None
            AgentArray._cached_ptr = 0
            return None

        # pointer changed? (map load, zone change, etc.)
        if ptr != AgentArray._cached_ptr:
            AgentArray._cached_ptr = ptr
            AgentArray._cached_ctx = cast(
                ptr,
                POINTER(AgentArrayStruct)
            ).contents

        return AgentArray._cached_ctx
        
        
AgentArray.enable()
