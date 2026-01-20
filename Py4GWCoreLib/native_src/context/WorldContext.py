import PyPointers
from Py4GW import Game
import math

from ctypes import (
    Structure, POINTER,
    c_uint32, c_float, c_void_p, c_wchar, c_uint8,c_uint16,
    cast
)
from ..internals.helpers import read_wstr, encoded_wstr_to_str
from ..internals.types import Vec2f, Vec3f, GamePos
from ..internals.gw_array import GW_Array, GW_Array_View, GW_Array_Value_View

#region AccountInfo
class AccountInfoStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("account_name_ptr", POINTER(c_wchar)),
        ("wins", c_uint32),
        ("losses", c_uint32),
        ("rating", c_uint32),
        ("qualifier_points", c_uint32),
        ("rank", c_uint32),
        ("tournament_reward_points", c_uint32),
    ]

    @property
    def account_name_str(self) -> str | None:
        return read_wstr(self.account_name_ptr)
 
#region MapAgent   
class MapAgentStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("cur_energy", c_float),        # +h0000
        ("max_energy", c_float),        # +h0004
        ("energy_regen", c_float),      # +h0008
        ("skill_timestamp", c_uint32),  # +h000C
        ("h0010", c_float),             # +h0010
        ("max_energy2", c_float),       # +h0014
        ("h0018", c_float),             # +h0018
        ("h001C", c_uint32),            # +h001C
        ("cur_health", c_float),        # +h0020
        ("max_health", c_float),        # +h0024
        ("health_regen", c_float),      # +h0028
        ("h002C", c_uint32),            # +h002C
        ("effects", c_uint32),          # +h0030
    ]
    
    @property
    def is_bleeding(self) -> bool:
        return (self.effects & 0x0001) != 0
    @property
    def is_conditioned(self) -> bool:
        return (self.effects & 0x0002) != 0
    @property
    def is_crippled(self) -> bool:
        return (self.effects & 0x000A) == 0xA
    @property
    def is_dead(self) -> bool:
        return (self.effects & 0x0010) != 0   
    @property
    def is_deep_wounded(self) -> bool:
        return (self.effects & 0x0020) != 0
    @property
    def is_poisoned(self) -> bool:
        return (self.effects & 0x0040) != 0
    @property
    def is_enchanted(self) -> bool:
        return (self.effects & 0x0080) != 0
    @property
    def is_degen_hexed(self) -> bool:
        return (self.effects & 0x0400) != 0
    @property
    def is_hexed(self) -> bool:
        return (self.effects & 0x0800) != 0
    @property
    def is_weapon_spelled(self) -> bool:
        return (self.effects & 0x8000) != 0
    
#region PartyAlly
class PartyAllyStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),
        ("unk", c_uint32),
        ("composite_id", c_uint32),
    ]

#region Attribute
class AttributeStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("attribute_id", c_uint32),
        ("level_base", c_uint32),
        ("level", c_uint32),
        ("decrement_points", c_uint32),
        ("increment_points", c_uint32),
    ]
    @property
    def name(self) -> str:
        from ...enums_src.GameData_enums import AttributeNames
        return AttributeNames.get(self.attribute_id, "Unknown")
    
    #retro code compatibility
    def GetName(self) -> str:
        return self.name

#region PartyAttribute
class PartyAttributeStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),
        ("attribute_array", AttributeStruct * 54),
    ]     
    
    @property
    def attributes(self) -> list[AttributeStruct]:
        return [self.attribute_array[i] for i in range(54)]
    
    
#region Effect and Buff
class EffectStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("skill_id", c_uint32),
        ("attribute_level", c_uint32),
        ("effect_id", c_uint32),
        ("agent_id", c_uint32),  # non-zero means maintained enchantment - caster id
        ("duration", c_float),
        ("timestamp", c_uint32), #DWORD
    ]
    #DWORD GetTimeElapsed() const;
    #DWORD GetTimeRemaining() const;
       
class BuffStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("skill_id", c_uint32),
        ("h0004", c_uint32),
        ("buff_id", c_uint32),
        ("target_agent_id", c_uint32),
    ]

class AgentEffectsStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),
        ("buff_array", GW_Array),  #Array<Buff>
        ("effect_array", GW_Array),  #Array<Effect>
    ]
    @property
    def buffs(self) -> list[BuffStruct]:
        return GW_Array_Value_View(self.buff_array, BuffStruct).to_list()
    @property
    def effects(self) -> list[EffectStruct]:
        return GW_Array_Value_View(self.effect_array, EffectStruct).to_list()
    
class QuestStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("quest_id", c_uint32),          # +h0000 GW::Constants::QuestID
        ("log_state", c_uint32),         # +h0004
        ("location_ptr", POINTER(c_wchar)), # +h0008
        ("name_ptr", POINTER(c_wchar)),     # +h000C
        ("npc_ptr", POINTER(c_wchar)),      # +h0010
        ("map_from", c_uint32),          # +h0014 GW::Constants::MapID
        ("marker_ptr", GamePos),             # +h0018
        ("h0024", c_uint32),             # +h0024
        ("map_to", c_uint32),            # +h0028 GW::Constants::MapID
        ("description_ptr", POINTER(c_wchar)), # +h002C
        ("objectives_ptr", POINTER(c_wchar)),  # +h0030
    ]
    
    @property
    def is_completed(self) -> bool:
        return (self.log_state & 0x2) != 0
    @property
    def is_current_mission_quest(self) -> bool:
        return (self.log_state & 0x10) != 0
    @property
    def is_area_primary(self) -> bool:
        return (self.log_state & 0x40) != 0  # e.g. "Primary Echovald Forest Quests"
    @property
    def is_primary(self) -> bool:
        return (self.log_state & 0x20) != 0  # e.g. "Primary Quests"
    @property
    def location_str(self) -> str | None:
        return encoded_wstr_to_str(read_wstr(self.location_ptr))
    @property
    def location_encoded_str(self) -> str | None:
        return read_wstr(self.location_ptr)
    @property
    def name_str(self) -> str | None:
        return encoded_wstr_to_str(read_wstr(self.name_ptr))
    @property
    def name_encoded_str(self) -> str | None:
        return read_wstr(self.name_ptr)
    @property
    def npc_str(self) -> str | None:
        return encoded_wstr_to_str(read_wstr(self.npc_ptr))
    @property
    def npc_encoded_str(self) -> str | None:
        return read_wstr(self.npc_ptr)
    @property
    def description_str(self) -> str | None:
        return encoded_wstr_to_str(read_wstr(self.description_ptr))
    @property
    def description_encoded_str(self) -> str | None:
        return read_wstr(self.description_ptr)
    @property
    def objectives_str(self) -> str | None:
        return encoded_wstr_to_str(read_wstr(self.objectives_ptr))
    @property
    def objectives_encoded_str(self) -> str | None:
        return read_wstr(self.objectives_ptr)
    @property
    def marker(self) -> GamePos | None:
        x, y, zplane = self.marker_ptr.x, self.marker_ptr.y, self.marker_ptr.zplane

        if not math.isfinite(x) or not math.isfinite(y) or not math.isfinite(zplane):
            return None

        return GamePos(x, y, zplane)
    
    

class MissionObjectiveStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("objective_id", c_uint32),      # +h0000
        ("enc_str_ptr", POINTER(c_wchar)),   # +h0004
        ("type", c_uint32),              # +h0008
    ]
    
    @property
    def enc_str_encoded_str(self) -> str | None:
        return read_wstr(self.enc_str_ptr)
    @property
    def enc_str(self) -> str | None:
        return encoded_wstr_to_str(read_wstr(self.enc_str_ptr))
  

class HeroFlagStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("hero_id", c_uint32),          # +h0000
        ("agent_id", c_uint32),         # +h0004 AgentID
        ("level", c_uint32),            # +h0008
        ("hero_behavior", c_uint32),    # +h000C HeroBehavior
        ("flag_ptr", Vec2f),                # +h0010
        ("h0018", c_uint32),             # +h0018
        ("locked_target_id", c_uint32),  # +h001C AgentID
        ("h0020", c_uint32),             # +h0020 padding / unknown
    ]
    
    @property
    def flag(self) -> Vec2f | None:
        flag = self.flag_ptr

        if not math.isfinite(flag.x) or not math.isfinite(flag.y):
            return None

        return Vec2f(flag.x, flag.y)

class HeroInfoStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("hero_id", c_uint32),           # +h0000
        ("agent_id", c_uint32),          # +h0004
        ("level", c_uint32),             # +h0008
        ("primary", c_uint32),           # +h000C
        ("secondary", c_uint32),         # +h0010
        ("hero_file_id", c_uint32),      # +h0014
        ("model_file_id", c_uint32),     # +h0018
        ("h001C", c_uint8 * 52),          # +h001C
        ("name_encoded_str", c_wchar * 20),           # +h0050
    ]
    
    @property
    def name_str(self) -> str:
        _name = encoded_wstr_to_str(self.name_encoded_str)
        return _name if _name else ""

  
class ControlledMinionsStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),
        ("minion_count", c_uint32),
    ]
    
class PartyMemberMoraleInfoStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),
        ("agent_id_dupe", c_uint32),
        ("unk", c_uint32 * 4),
        ("morale", c_uint32),
        #// ... unknown size
    ]

class PartyMoraleLinkStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("unk", c_uint32),
        ("unk2", c_uint32),
        ("party_member_info_ptr", POINTER(PartyMemberMoraleInfoStruct)),
    ]
    
    @property
    def party_member_info(self) -> PartyMemberMoraleInfoStruct | None:
        if not self.party_member_info_ptr:
            return None
        return self.party_member_info_ptr.contents
    

class PlayerControlledCharacterStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("field0_0x0", c_uint32),
        ("field1_0x4", c_uint32),
        ("field2_0x8", c_uint32),
        ("field3_0xc", c_uint32),
        ("field4_0x10", c_uint32),
        ("agent_id", c_uint32),
        ("composite_id", c_uint32),
        ("field7_0x1c", c_uint32),
        ("field8_0x20", c_uint32),
        ("field9_0x24", c_uint32),
        ("field10_0x28", c_uint32),
        ("field11_0x2c", c_uint32),
        ("field12_0x30", c_uint32),
        ("field13_0x34", c_uint32),
        ("field14_0x38", c_uint32),
        ("field15_0x3c", c_uint32),
        ("field16_0x40", c_uint32),
        ("field17_0x44", c_uint32),
        ("field18_0x48", c_uint32),
        ("field19_0x4c", c_float),
        ("field20_0x50", c_float),
        ("field21_0x54", c_uint32),
        ("field22_0x58", c_uint32),
        ("field23_0x5c", c_uint32),
        ("field24_0x60", c_uint32),
        ("more_flags", c_uint32),
        ("field26_0x68", c_uint32),
        ("field27_0x6c", c_uint32),
        ("field28_0x70", c_uint32),
        ("field29_0x74", c_uint32),
        ("field30_0x78", c_uint32),
        ("field31_0x7c", c_uint32),
        ("field32_0x80", c_uint32),
        ("field33_0x84", c_uint32),
        ("field34_0x88", c_uint32),
        ("field35_0x8c", c_uint32),
        ("field36_0x90", c_uint32),
        ("field37_0x94", c_uint32),
        ("field38_0x98", c_uint32),
        ("field39_0x9c", c_uint32),
        ("field40_0xa0", c_uint32),
        ("field41_0xa4", c_uint32),
        ("field42_0xa8", c_uint32),
        ("field43_0xac", c_uint32),
        ("field44_0xb0", c_uint32),
        ("field45_0xb4", c_uint32),
        ("field46_0xb8", c_uint32),
        ("field47_0xbc", c_uint32),
        ("field48_0xc0", c_uint32),
        ("field49_0xc4", c_uint32),
        ("field50_0xc8", c_uint32),
        ("field51_0xcc", c_uint32),
        ("field52_0xd0", c_uint32),
        ("field53_0xd4", c_uint32),
        ("field54_0xd8", c_uint32),
        ("field55_0xdc", c_uint32),
        ("field56_0xe0", c_uint32),
        ("field57_0xe4", c_uint32),
        ("field58_0xe8", c_uint32),
        ("field59_0xec", c_uint32),
        ("field60_0xf0", c_uint32),
        ("field61_0xf4", c_uint32),
        ("field62_0xf8", c_uint32),
        ("field63_0xfc", c_uint32),
        ("field64_0x100", c_uint32),
        ("field65_0x104", c_uint32),
        ("field66_0x108", c_uint32),
        ("flags", c_uint32),
        ("field68_0x110", c_uint32),
        ("field69_0x114", c_uint32),
        ("field70_0x118", c_uint32),
        ("field71_0x11c", c_uint32),
        ("field72_0x120", c_uint32),
        ("field73_0x124", c_uint32),
        ("field74_0x128", c_uint32),
        ("field75_0x12c", c_uint32),
        ("field76_0x130", c_uint32),
    ]
    

class ProfessionStateStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),
        ("primary", c_uint32),
        ("secondary", c_uint32),
        ("unlocked_professions", c_uint32), #bitwise flags
        ("unk", c_uint32),
    ]
    
    def IsProfessionUnlocked(self, profession: int) -> bool:    
        return (self.unlocked_professions & (1 << profession)) != 0

class SkillbarSkillStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("adrenaline_a", c_uint32),   # +h0000
        ("adrenaline_b", c_uint32),   # +h0004
        ("recharge", c_uint32),       # +h0008
        ("skill_id", c_uint32),       # +h000C
        ("event", c_uint32),          # +h0010
    ]

class SkillbarCastStruct(Structure): #Array of queued skills on a skillbar
    _pack_ = 1
    _fields_ = [
        ("h0000", c_uint16),           # +h0000
        ("skill_id", c_uint16),        # +h0002 (SkillID is uint16 here)
        ("h0004", c_uint32),           # +h0004
    ]
    
  
class SkillbarStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),            # +h0000
        ("skills", SkillbarSkillStruct * 8),     # +h0004
        ("disabled", c_uint32),            # +h00A4
        ("cast_array", GW_Array),  #SkillbarCastArray           # +h00A8
        ("h00B8", c_uint32),           # +h00B8
    ]
    @property
    def is_valid(self) -> bool:
        return self.agent_id > 0

    def GetSkillById(self, skill_id: int) -> SkillbarSkillStruct | None:
        for skill in self.skills:
            if skill.skill_id == skill_id:
                return skill
        return None
    
    @property
    def casted_skills(self) -> list[SkillbarCastStruct]:
        return GW_Array_Value_View(self.cast_array, SkillbarCastStruct).to_list()
    

class DupeSkillStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("skill_id", c_uint32),
        ("count", c_uint32),
    ]


class AgentNameInfoStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("h0000", c_uint32 * 13),
        ("name_enc_ptr", POINTER(c_wchar)),
    ]
    @property
    def name_encoded_str(self) -> str | None:
        return read_wstr(self.name_enc_ptr)
    @property
    def name_str(self) -> str | None:
        return encoded_wstr_to_str(read_wstr(self.name_enc_ptr))
    
class MissionMapIconStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("index", c_uint32),          # +h0000
        ("X", c_float),               # +h0004
        ("Y", c_float),               # +h0008
        ("h000C", c_uint32),         # +h000C // = 0
        ("h0010", c_uint32),         # +h0010 // = 0
        ("option", c_uint32),        # +h0014 // Affilitation/color. gray = 0, blue, red, yellow, teal, purple, green, gray
        ("h0018", c_uint32),         # +h0018 // = 0
        ("model_id", c_uint32),      # +h001C // Model of the displayed icon in the Minimap
        ("h0020", c_uint32),         # +h0020 // = 0
        ("h0024", c_uint32),         # +h0024 // May concern the name
    ]
    @property 
    def position(self) -> Vec2f:
        return Vec2f(self.X, self.Y)
    
class PetInfoStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),
        ("owner_agent_id", c_uint32),
        ("pet_name_ptr", POINTER(c_wchar)),
        ("model_file_id1", c_uint32),
        ("model_file_id2", c_uint32),
        ("behavior", c_uint32),
        ("locked_target_id", c_uint32),
    ]
    
    @property
    def pet_name_encoded_str(self) -> str | None:
        return read_wstr(self.pet_name_ptr)
    
    @property
    def pet_name_str(self) -> str | None:
        return encoded_wstr_to_str(read_wstr(self.pet_name_ptr))
    
    
class NPC_ModelStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("model_file_id", c_uint32),    # +h0000
        ("h0004", c_uint32),            # +h0004
        ("scale", c_uint32),            # +h0008 // I think, 2 highest order bytes are percent of size, so 0x64000000 is 100
        ("sex", c_uint32),              # +h000C
        ("npc_flags", c_uint32),        # +h0010
        ("primary", c_uint32),          # +h0014
        ("h0018", c_uint32),            # +h0018
        ("default_level", c_uint8),     # +h001C
        ("padding1", c_uint8),          # +h001D
        ("padding2", c_uint16),         # +h001E
        ("name_enc_ptr", POINTER(c_wchar)), # +h0020
        ("model_files_ptr", c_void_p),   # data* +h0024 // ModelFile*
        ("files_count", c_uint32),      # +h0028 // length of ModelFile
        ("files_capacity", c_uint32),   # +h002C // capacity of ModelFile
    ]  
    @property
    def is_valid(self) -> bool:
        return self.model_file_id != 0
    @property
    def is_henchman(self) -> bool:
        return (self.npc_flags & 0x10) != 0
    
    @property
    def is_hero(self) -> bool:
        return (self.npc_flags & 0x20) != 0
    
    @property
    def is_spirit(self) -> bool:
        return (self.npc_flags & 0x4000) != 0
    
    @property
    def is_minion(self) -> bool:
        return (self.npc_flags & 0x100) != 0
    
    @property
    def is_pet(self) -> bool:
        return self.npc_flags == 0xD
    
    @property
    def name_encoded_str(self) -> str | None:
        return read_wstr(self.name_enc_ptr)
    
    @property
    def name_str(self) -> str | None:
        return encoded_wstr_to_str(read_wstr(self.name_enc_ptr))
    
    @property
    def model_files(self) -> list[int]:
        if not self.model_files_ptr or self.files_count == 0:
            return []
        arr = cast(self.model_files_ptr, POINTER(c_uint32))
        return [arr[i] for i in range(self.files_count)]
    


class PlayerStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),                          # +h0000
        ("h0004", c_uint32 * 3),                         # +h0004
        ("appearance_bitmap", c_uint32),                 # +h0010
        ("flags", c_uint32),                             # +h0014 Bitwise field
        ("primary", c_uint32),                           # +h0018
        ("secondary", c_uint32),                         # +h001C
        ("h0020", c_uint32),                             # +h0020
        ("name_enc_ptr", POINTER(c_wchar)),                  # +h0024
        ("name_ptr", POINTER(c_wchar)),                      # +h0028
        ("party_leader_player_number", c_uint32),        # +h002C
        ("active_title_tier", c_uint32),                 # +h0030
        ("reforged_or_dhuums_flags", c_uint32),          # +h0034
        ("player_number", c_uint32),                     # +h0038
        ("party_size", c_uint32),                        # +h003C
        ("h0040_array", GW_Array),                             # +h0040 Array<void*>
    ]
 
    @property 
    def is_pvp(self) -> bool:
        return (self.flags & 0x800) != 0
    @property
    def name_enc_encoded_str(self) -> str | None:
        return read_wstr(self.name_enc_ptr)
    
    @property
    def name_enc_str(self) -> str | None:
        return encoded_wstr_to_str(read_wstr(self.name_ptr))
    
    @property
    def name_encoded_str(self) -> str | None:
        return read_wstr(self.name_ptr)
    
    @property
    def name_str(self) -> str | None:
        return encoded_wstr_to_str(read_wstr(self.name_ptr))
    
    @property
    def h0040_ptrs(self) -> list[int] | None:
        arr = GW_Array_Value_View(self.h0040_array, c_void_p).to_list()
        if not arr:
            return None
        # convert void* -> Python int
        return [int(ptr) for ptr in arr]

class TitleStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("props", c_uint32),                     # +h0000
        ("current_points", c_uint32),            # +h0004
        ("current_title_tier_index", c_uint32),  # +h0008
        ("points_needed_current_rank", c_uint32),# +h000C
        ("next_title_tier_index", c_uint32),     # +h0010
        ("points_needed_next_rank", c_uint32),   # +h0014
        ("max_title_rank", c_uint32),            # +h0018
        ("max_title_tier_index", c_uint32),      # +h001C
        ("h0020", c_uint32),                     # +h0020
        ("points_desc_ptr", POINTER(c_wchar)),       # +h0024 Pretty sure these are ptrs to title hash strings
        ("h0028_ptr", POINTER(c_wchar)),             # +h0028 Pretty sure these are ptrs to title hash strings
    ]
    @property
    def is_percentage_based(self) -> bool:
        return (self.props & 1) != 0
    @property
    def has_tiers(self) -> bool:
        return (self.props & 3) == 2
    @property
    def points_desc_encoded_str(self) -> str | None:
        return read_wstr(self.points_desc_ptr)
    @property
    def points_desc_str(self) -> str | None:
        return encoded_wstr_to_str(read_wstr(self.points_desc_ptr))
    @property
    def h0028_encoded_str(self) -> str | None:
        return read_wstr(self.h0028_ptr)
    @property
    def h0028_str(self) -> str | None:
        return encoded_wstr_to_str(read_wstr(self.h0028_ptr))


class TitleTierStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("props", c_uint32),
        ("tier_number", c_uint32),
        ("tier_name_enc_ptr", POINTER(c_wchar)),
    ]
    @property
    def is_valid(self) -> bool:
        return self.tier_number != 0
    @property
    def tier_name_encoded_str(self) -> str | None:
        return read_wstr(self.tier_name_enc_ptr)
    @property
    def tier_name_str(self) -> str | None:
        return encoded_wstr_to_str(read_wstr(self.tier_name_enc_ptr))
    @property
    def is_percentage_based(self) -> bool:
        return (self.props & 1) != 0

#region WorldContextStruct

# ---------------------------------------------------------------------
# WorldContextStruct
# ---------------------------------------------------------------------

class WorldContextStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("account_info_ptr", POINTER(AccountInfoStruct)),
        ("message_buff_array", GW_Array), #Array<wchar_t>
        ("dialog_buff_array", GW_Array), #Array<wchar_t>
        ("merch_items_array", GW_Array), #Array<ItemID> uint32t
        ("merch_items2_array", GW_Array),  #Array<ItemID> uint32t
        ("accumMapInitUnk0", c_uint32),
        ("accumMapInitUnk1", c_uint32),
        ("accumMapInitOffset", c_uint32),
        ("accumMapInitLength", c_uint32),
        ("h0054", c_uint32),
        ("accumMapInitUnk2", c_uint32),
        ("h005C", c_uint32 * 8),
        ("map_agents_array", GW_Array), #Array<MapAgent>
        ("party_allies_array", GW_Array), #Array<PartyAlly>
        ("all_flag_array", c_float * 3),
        ("h00A8", c_uint32),
        ("party_attributes_array", GW_Array), # Array<PartyAttribute>
        ("h00BC", c_uint32 * 255),
        ("h04B8_array", GW_Array), #Array<void *>
        ("h04C8_array", GW_Array), #Array<void *>
        ("h04D8", c_uint32),
        ("h04DC_array", GW_Array), #Array<void *>
        ("h04EC", c_uint32 * 7),
        ("party_effects_array", GW_Array), #Array<AgentEffects>
        ("h0518_array", GW_Array), #Array<void *>
        ("active_quest_id", c_uint32),
        ("quest_log_array", GW_Array), #Array<Quest>
        ("h053C", c_uint32 * 10),
        ("mission_objectives_array", GW_Array), #Array<MissionObjective>
        ("henchmen_agent_ids_array", GW_Array), #Array<uint32_t>
        ("hero_flags_array", GW_Array), #Array<HeroFlag>
        ("hero_info_array", GW_Array), #Array<HeroInfo>
        ("cartographed_areas_array", GW_Array), #Array<void *>
        ("h05B4", c_uint32 * 2),
        ("controlled_minion_count_array", GW_Array), #Array<ControlledMinions>
        ("missions_completed_array", GW_Array), #Array<uint32_t>
        ("missions_bonus_array", GW_Array), #Array<uint32_t>
        ("missions_completed_hm_array", GW_Array), #Array<uint32_t>
        ("missions_bonus_hm_array", GW_Array), #Array<uint32_t>
        ("unlocked_map_array", GW_Array), #Array<uint32_t>
        ("h061C", c_uint32 * 2),
        ("player_morale_ptr", POINTER(PartyMemberMoraleInfoStruct)),
        ("h028C", c_uint32),
        ("party_morale_array", GW_Array), #Array<PartyMoraleLink>
        ("h063C", c_uint32 * 16),
        ("player_number", c_uint32),
        ("playerControlledChar_ptr", POINTER(PlayerControlledCharacterStruct)),
        ("is_hard_mode_unlocked", c_uint32),
        ("h0688", c_uint32 * 2),
        ("salvage_session_id", c_uint32),
        ("h0694", c_uint32 * 5),
        ("playerTeamToken", c_uint32),
        ("pets_array", GW_Array), #Array<PetInfo>
        ("party_profession_states_array", GW_Array), #Array<ProfessionState>
        ("h06CC_array", GW_Array), #Array<void *>
        ("h06DC", c_uint32),
        ("h06E0_array", GW_Array), #Array<void *>
        ("party_skillbar_array", GW_Array), #Array<Skillbar>
        ("learnable_character_skills_array", GW_Array), #Array<uint32_t> #// populated at skill trainer and when using signet of capture
        ("unlocked_character_skills_array", GW_Array), #Array<uint32_t>
        ("duplicated_character_skills_array", GW_Array), #Array<DupeSkill> // When res signet is bought more than once, its mapped into this array. Used in skill window.
        ("h0730_array", GW_Array), #Array<void *>
        ("experience", c_uint32),
        ("experience_dupe", c_uint32),
        ("current_kurzick", c_uint32),
        ("current_kurzick_dupe", c_uint32),
        ("total_earned_kurzick", c_uint32),
        ("total_earned_kurzick_dupe", c_uint32),
        ("current_luxon", c_uint32),
        ("current_luxon_dupe", c_uint32),
        ("total_earned_luxon", c_uint32),
        ("total_earned_luxon_dupe", c_uint32),
        ("current_imperial", c_uint32),
        ("current_imperial_dupe", c_uint32),
        ("total_earned_imperial", c_uint32),
        ("total_earned_imperial_dupe", c_uint32),
        ("unk_faction4", c_uint32),
        ("unk_faction4_dupe", c_uint32),
        ("unk_faction5", c_uint32),
        ("unk_faction5_dupe", c_uint32),
        ("level", c_uint32),
        ("level_dupe", c_uint32),
        ("morale", c_uint32),
        ("morale_dupe", c_uint32),
        ("current_balth", c_uint32),
        ("current_balth_dupe", c_uint32),
        ("total_earned_balth", c_uint32),
        ("total_earned_balth_dupe", c_uint32),
        ("current_skill_points", c_uint32),
        ("current_skill_points_dupe", c_uint32),
        ("total_earned_skill_points", c_uint32),
        ("total_earned_skill_points_dupe", c_uint32),
        ("max_kurzick", c_uint32),
        ("max_luxon", c_uint32),
        ("max_balth", c_uint32),
        ("max_imperial", c_uint32),
        ("equipment_status", c_uint32),
        ("agent_name_info_array", GW_Array), #Array<AgentNameInfo>
        ("h07DC_array", GW_Array), #Array<void *>
        ("mission_map_icons_array", GW_Array), #Array<MissionMapIcon>
        ("npc_models_array", GW_Array), #Array<NPC_Model>
        ("players_array", GW_Array), #Array<Player>
        ("titles_array", GW_Array), #Array<Title>
        ("title_tiers_array", GW_Array), #Array<TitleTier>
        ("vanquished_areas_array", GW_Array), #Array<uint32_t>
        ("foes_killed", c_uint32),
        ("foes_to_kill", c_uint32),
        #//... couple more arrays after this
    ]
    
#region Properties
    @property
    def account_info(self) -> AccountInfoStruct | None:
        if not self.account_info_ptr:
            return None
        return self.account_info_ptr.contents
    
    @property
    def message_buff(self) -> list[str] | None:
        messages = GW_Array_Value_View(self.message_buff_array, c_wchar).to_list()
        if not messages:
            return None
        return [str(ch) for ch in messages]

    @property
    def dialog_buff(self) -> list[str] | None:
        dialogs = GW_Array_Value_View(self.dialog_buff_array, c_wchar).to_list()
        if not dialogs:
            return None
        return [str(ch) for ch in dialogs]
    
    @property
    def merch_items(self) -> list[int] | None:
        items = GW_Array_Value_View(self.merch_items_array, c_uint32).to_list()
        if not items:
            return None
        return [int(item) for item in items]
    
    @property
    def merch_items2(self) -> list[int] | None:
        items = GW_Array_Value_View(self.merch_items2_array, c_uint32).to_list()
        if not items:
            return None
        return [int(item) for item in items]
    
    @property
    def map_agents(self) -> list[MapAgentStruct] | None:
        agents = GW_Array_Value_View(self.map_agents_array, MapAgentStruct).to_list()
        if not agents:
            return None
        return [agent for agent in agents]
    
    @property
    def party_allies(self) -> list[PartyAllyStruct] | None:
        allies = GW_Array_Value_View(self.party_allies_array, PartyAllyStruct).to_list()
        if not allies:
            return None
        return [ally for ally in allies]
    
    @property
    def party_attributes(self) -> list[PartyAttributeStruct] | None:
        attrs = GW_Array_Value_View(self.party_attributes_array, PartyAttributeStruct).to_list()
        if not attrs:
            return None
        return [attr for attr in attrs]
    
    @staticmethod
    def _is_valid_attribute(attribute: AttributeStruct) -> bool:
        return (
            attribute.level_base > 0 or
            attribute.level > 0 or
            attribute.decrement_points > 0 or
            attribute.increment_points > 0
        )
    
    def get_attributes_by_agent_id(self, agent_id: int) -> list[AttributeStruct]:
        party_attributes = self.party_attributes
        if not party_attributes:
            return []

        for attr in party_attributes:
            if attr.agent_id != agent_id:
                continue

            result: list[AttributeStruct] = []

            for i, attribute in enumerate(attr.attributes):
                if i >= 45:  # soft upper bound
                    break

                if self._is_valid_attribute(attribute):
                    result.append(attribute)

            return result

        return []
    
    def get_party_attributes(self) -> dict[int, list[AttributeStruct]]:
        party_attributes = self.party_attributes
        if not party_attributes:
            return {}

        result: dict[int, list[AttributeStruct]] = {}

        for attr in party_attributes:
            valid_attrs = []

            for i, attribute in enumerate(attr.attributes):
                if i >= 45: # soft upper bound
                    break
                if self._is_valid_attribute(attribute):
                    valid_attrs.append(attribute)

            if valid_attrs:
                result[attr.agent_id] = valid_attrs

        return result


                    
    
    @property
    def all_flag(self) -> Vec3f | None:
        x, y, z = self.all_flag_array

        if not math.isfinite(x) or not math.isfinite(y) or not math.isfinite(z):
            return None

        return Vec3f(x, y, z)

    @property
    def h04B8_ptrs(self) -> list[int] | None:
        ptrs = GW_Array_Value_View(self.h04B8_array, c_void_p).to_list()
        if not ptrs:
            return None
        return [int(ptr) for ptr in ptrs]
    
    @property
    def h04C8_ptrs(self) -> list[int] | None:
        ptrs = GW_Array_Value_View(self.h04C8_array, c_void_p).to_list()
        if not ptrs:
            return None
        return [int(ptr) for ptr in ptrs]
    
    @property
    def h04DC_ptrs(self) -> list[int] | None:
        ptrs = GW_Array_Value_View(self.h04DC_array, c_void_p).to_list()
        if not ptrs:
            return None
        return [int(ptr) for ptr in ptrs]
    
    @property
    def party_effects(self) -> list[AgentEffectsStruct] | None:
        effects = GW_Array_Value_View(self.party_effects_array, AgentEffectsStruct).to_list()
        if not effects:
            return None
        return [effect for effect in effects]
    
    @property
    def h0518_ptrs(self) -> list[int | None] | None:
        ptrs = GW_Array_Value_View(self.h0518_array, c_void_p).to_list()
        if not ptrs:
            return None

        return [int(ptr) if ptr is not None else None for ptr in ptrs]

    @property
    def quest_log(self) -> list[QuestStruct] | None:
        quests = GW_Array_Value_View(self.quest_log_array, QuestStruct).to_list()
        if not quests:
            return None
        return [quest for quest in quests]
    
    @property
    def mission_objectives(self) -> list[MissionObjectiveStruct] | None:
        objectives = GW_Array_Value_View(self.mission_objectives_array, MissionObjectiveStruct).to_list()
        if not objectives:
            return None
        return [obj for obj in objectives]
    
    @property
    def henchmen_agent_ids(self) -> list[int] | None:
        ids = GW_Array_Value_View(self.henchmen_agent_ids_array, c_uint32).to_list()
        if not ids:
            return None
        return [int(id_) for id_ in ids]
    
    @property
    def hero_flags(self) -> list[HeroFlagStruct] | None:
        flags = GW_Array_Value_View(self.hero_flags_array, HeroFlagStruct).to_list()
        if not flags:
            return None
        return [flag for flag in flags]
    
    @property
    def hero_info(self) -> list[HeroInfoStruct] | None:
        infos = GW_Array_Value_View(self.hero_info_array, HeroInfoStruct).to_list()
        if not infos:
            return None
        return [info for info in infos]
    
    @property
    def cartographed_areas(self) -> list[int | None] | None:
        areas = GW_Array_Value_View( self.cartographed_areas_array,c_void_p).to_list()

        if not areas:
            return None

        return [int(a) if a is not None else None for a in areas]
    
    @property
    def controlled_minions(self) -> list[ControlledMinionsStruct] | None:
        minions = GW_Array_Value_View(self.controlled_minion_count_array, ControlledMinionsStruct).to_list()
        if not minions:
            return None
        return [minion for minion in minions]
    
    @property
    def missions_completed(self) -> list[int] | None:
        missions = GW_Array_Value_View(self.missions_completed_array, c_uint32).to_list()
        if not missions:
            return None
        return [int(mission) for mission in missions]
    
    @property
    def missions_bonus(self) -> list[int] | None:
        missions = GW_Array_Value_View(self.missions_bonus_array, c_uint32).to_list()
        if not missions:
            return None
        return [int(mission) for mission in missions]
    
    @property
    def missions_completed_hm(self) -> list[int] | None:
        missions = GW_Array_Value_View(self.missions_completed_hm_array, c_uint32).to_list()
        if not missions:
            return None
        return [int(mission) for mission in missions]
    
    @property
    def missions_bonus_hm(self) -> list[int] | None:
        missions = GW_Array_Value_View(self.missions_bonus_hm_array, c_uint32).to_list()
        if not missions:
            return None
        return [int(mission) for mission in missions]
    
    @property
    def unlocked_maps(self) -> list[int] | None:
        maps = GW_Array_Value_View(self.unlocked_map_array, c_uint32).to_list()
        if not maps:
            return None
        return [int(map_) for map_ in maps]
    
    @property
    def player_morale(self) -> PartyMemberMoraleInfoStruct | None:
        if not self.player_morale_ptr:
            return None
        return self.player_morale_ptr.contents
    
    @property
    def party_morale(self) -> list[PartyMoraleLinkStruct] | None:
        links = GW_Array_Value_View(self.party_morale_array, PartyMoraleLinkStruct).to_list()
        if not links:
            return None
        return [link for link in links]
    
    @property
    def player_controlled_character(self) -> PlayerControlledCharacterStruct | None:
        if not self.playerControlledChar_ptr:
            return None
        return self.playerControlledChar_ptr.contents
    
    @property
    def pets(self) -> list[PetInfoStruct] | None:
        pets = GW_Array_Value_View(self.pets_array, PetInfoStruct).to_list()
        if not pets:
            return None
        return [pet for pet in pets]
    
    @property
    def party_profession_states(self) -> list[ProfessionStateStruct] | None:
        states = GW_Array_Value_View(self.party_profession_states_array, ProfessionStateStruct).to_list()
        if not states:
            return None
        return [state for state in states]
    
    @property
    def h06CC_ptrs(self) -> list[int] | None:
        ptrs = GW_Array_Value_View(self.h06CC_array, c_void_p).to_list()
        if not ptrs:
            return None
        return [int(ptr) for ptr in ptrs]
    
    @property 
    def h06E0_ptrs(self) -> list[int] | None:
        ptrs = GW_Array_Value_View(self.h06E0_array, c_void_p).to_list()
        if not ptrs:
            return None
        return [int(ptr) for ptr in ptrs]
    
    @property
    def party_skillbars(self) -> list[SkillbarStruct] | None:
        skillbars = GW_Array_Value_View(self.party_skillbar_array, SkillbarStruct).to_list()
        if not skillbars:
            return None
        return [skillbar for skillbar in skillbars]
    
    @property
    def learnable_character_skills(self) -> list[int] | None:
        skills = GW_Array_Value_View(self.learnable_character_skills_array, c_uint32).to_list()
        if not skills:
            return None
        return [int(skill) for skill in skills]
    
    @property
    def unlocked_character_skills(self) -> list[int] | None:
        skills = GW_Array_Value_View(self.unlocked_character_skills_array, c_uint32).to_list()
        if not skills:
            return None
        return [int(skill) for skill in skills]
    
    @property
    def duplicated_character_skills(self) -> list[DupeSkillStruct] | None:
        skills = GW_Array_Value_View(self.duplicated_character_skills_array, DupeSkillStruct).to_list()
        if not skills:
            return None
        return [skill for skill in skills]
    
    @property
    def h0730_ptrs(self) -> list[int] | None:
        ptrs = GW_Array_Value_View(self.h0730_array, c_void_p).to_list()
        if not ptrs:
            return None
        return [int(ptr) for ptr in ptrs]
    
    @property
    def agent_name_info(self) -> list[AgentNameInfoStruct] | None:
        infos = GW_Array_Value_View(self.agent_name_info_array, AgentNameInfoStruct).to_list()
        if not infos:
            return None
        return [info for info in infos]
    
    @property
    def h07DC_ptrs(self) -> list[int] | None:
        ptrs = GW_Array_Value_View(self.h07DC_array, c_void_p).to_list()
        if not ptrs:
            return None
        return [int(ptr) for ptr in ptrs]
    
    @property
    def mission_map_icons(self) -> list[MissionMapIconStruct] | None:
        icons = GW_Array_Value_View(self.mission_map_icons_array, MissionMapIconStruct).to_list()
        if not icons:
            return None
        return [icon for icon in icons]

    @property
    def npc_models(self) -> list[NPC_ModelStruct] | None:
        npcs = GW_Array_Value_View(self.npc_models_array, NPC_ModelStruct).to_list()
        if not npcs:
            return None
        return [npc for npc in npcs]
    
    @property
    def players(self) -> list[PlayerStruct] | None:
        players = GW_Array_Value_View(self.players_array, PlayerStruct).to_list()
        if not players:
            return None
        return [player for player in players]
    
    def GetPlayerById(self, player_id: int) -> PlayerStruct | None:
        players = self.players
        if not players:
            return None
        for player in players:
            if player.player_number == player_id:
                return player
        return None
    
    @property
    def titles(self) -> list[TitleStruct] | None:
        titles = GW_Array_Value_View(self.titles_array, TitleStruct).to_list()
        if not titles:
            return None
        return [title for title in titles]
    
    @property
    def title_tiers(self) -> list[TitleTierStruct] | None:
        tiers = GW_Array_Value_View(self.title_tiers_array, TitleTierStruct).to_list()
        if not tiers:
            return None
        return [tier for tier in tiers]
    
    @property
    def vanquished_areas(self) -> list[int] | None:
        areas = GW_Array_Value_View(self.vanquished_areas_array, c_uint32).to_list()
        if not areas:
            return None
        return [int(area) for area in areas]
    
    
#region Facade
class WorldContext:
    _ptr: int = 0
    _cached_ctx: WorldContextStruct | None = None
    _callback_name = "WorldContext.UpdatePtr"

    @staticmethod
    def get_ptr() -> int:
        return WorldContext._ptr

    @staticmethod
    def _update_ptr():
        ptr = PyPointers.PyPointers.GetWorldContextPtr()
        WorldContext._ptr = ptr
        if not ptr:
            WorldContext._cached_ctx = None
            return
        WorldContext._cached_ctx = cast(
            ptr,
            POINTER(WorldContextStruct)
        ).contents

    @staticmethod
    def enable():
        import PyCallback
        PyCallback.PyCallback.Register(
            WorldContext._callback_name,
            PyCallback.Phase.PreUpdate,
            WorldContext._update_ptr,
            priority=4
        )

    @staticmethod
    def disable():
        import PyCallback
        PyCallback.PyCallback.RemoveByName(WorldContext._callback_name)
        WorldContext._ptr = 0
        WorldContext._cached_ctx = None

    @staticmethod
    def get_context() -> WorldContextStruct | None:
        return WorldContext._cached_ctx
        
        
        
WorldContext.enable()