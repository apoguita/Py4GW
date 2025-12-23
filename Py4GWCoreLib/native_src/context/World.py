import PyPlayer
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

#region processed
class AccountInfo(Structure):
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
    
class MapAgent(Structure):
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
    
class PartyAlly(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),
        ("unk", c_uint32),
        ("composite_id", c_uint32),
    ]

class Attribute(Structure):
    _pack_ = 1
    _fields_ = [
        ("attribute_id", c_uint32),
        ("level_base", c_uint32),
        ("level", c_uint32),
        ("decrement_points", c_uint32),
        ("increment_points", c_uint32),
    ]

class PartyAttribute(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),
        ("attribute_array", Attribute * 54),
    ]     
    
    @property
    def attributes(self) -> list[Attribute]:
        return [self.attribute_array[i] for i in range(54)]
    
class Effect(Structure):
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
       
class Buff(Structure):
    _pack_ = 1
    _fields_ = [
        ("skill_id", c_uint32),
        ("h0004", c_uint32),
        ("buff_id", c_uint32),
        ("target_agent_id", c_uint32),
    ]

class AgentEffects(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),
        ("buff_array", GW_Array),  #Array<Buff>
        ("effect_array", GW_Array),  #Array<Effect>
    ]
    @property
    def buffs(self) -> list[Buff]:
        return GW_Array_Value_View(self.buff_array, Buff).to_list()
    @property
    def effects(self) -> list[Effect]:
        return GW_Array_Value_View(self.effect_array, Effect).to_list()
    
class Quest(Structure):
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
    
    

class MissionObjective(Structure):
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
    

#region not_processed
# ---------------------------------------------------------------------
# Simple structs
# ---------------------------------------------------------------------



class ControlledMinions(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),
        ("minion_count", c_uint32),
    ]


class DupeSkill(Structure):
    _pack_ = 1
    _fields_ = [
        ("skill_id", c_uint32),
        ("count", c_uint32),
    ]


class ProfessionState(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),
        ("primary", c_uint32),
        ("secondary", c_uint32),
        ("unlocked_professions", c_uint32), #bitwise flags
        ("unk", c_uint32),
    ]
"""
inline bool IsProfessionUnlocked(GW::Constants::Profession profession) const {
    return (unlocked_professions & (1 << (uint32_t)profession)) != 0;
}"""



class PartyMemberMoraleInfo(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),
        ("agent_id_dupe", c_uint32),
        ("unk", c_uint32 * 4),
        ("morale", c_uint32),
        #// ... unknown size
    ]


class PartyMoraleLink(Structure):
    _pack_ = 1
    _fields_ = [
        ("unk", c_uint32),
        ("unk2", c_uint32),
        ("party_member_info", POINTER(PartyMemberMoraleInfo)),
    ]


class PetInfo(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),
        ("owner_agent_id", c_uint32),
        ("pet_name", POINTER(c_wchar)),
        ("model_file_id1", c_uint32),
        ("model_file_id2", c_uint32),
        ("behavior", c_uint32),
        ("locked_target_id", c_uint32),
    ]


class PlayerControlledCharacter(Structure):
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
        ("field19_0x4c", c_uint32),
        ("field20_0x50", c_uint32),
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
    
# ---------------------------------------------------------------------
# ADDED Misc structs
# ---------------------------------------------------------------------


class HeroFlag(Structure):
    _pack_ = 1
    _fields_ = [
        ("hero_id", c_uint32),          # +h0000
        ("agent_id", c_uint32),         # +h0004 AgentID
        ("level", c_uint32),            # +h0008
        ("hero_behavior", c_uint32),    # +h000C HeroBehavior
        ("flag", Vec2f),                # +h0010
        ("h0018", c_uint32),             # +h0018
        ("locked_target_id", c_uint32),  # +h001C AgentID
        ("h0020", c_uint32),             # +h0020 padding / unknown
    ]


class HeroInfo(Structure):
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
        ("name", c_wchar * 20),           # +h0050
    ]
    
# ---------------------------------------------------------------------
# Skill  (size = 0xA4 / 164 bytes)
# ---------------------------------------------------------------------

class Skill(Structure):
    _pack_ = 1
    _fields_ = [
        ("skill_id", c_uint32),                 # +h0000
        ("h0004", c_uint32),                    # +h0004
        ("campaign", c_uint32),                 # +h0008
        ("type", c_uint32),                     # +h000C
        ("special", c_uint32),                  # +h0010
        ("combo_req", c_uint32),                # +h0014
        ("effect1", c_uint32),                  # +h0018
        ("condition", c_uint32),                # +h001C
        ("effect2", c_uint32),                  # +h0020
        ("weapon_req", c_uint32),               # +h0024
        ("profession", c_uint8),                # +h0028
        ("attribute", c_uint8),                 # +h0029
        ("title", c_uint16),                    # +h002A
        ("skill_id_pvp", c_uint32),              # +h002C
        ("combo", c_uint8),                     # +h0030
        ("target", c_uint8),                    # +h0031
        ("h0032", c_uint8),                     # +h0032
        ("skill_equip_type", c_uint8),           # +h0033
        ("overcast", c_uint8),                  # +h0034 // only if special flag has 0x000001 set
        ("energy_cost", c_uint8),               # +h0035
        ("health_cost", c_uint8),               # +h0036
        ("h0037", c_uint8),                     # +h0037
        ("adrenaline", c_uint32),               # +h0038
        ("activation", c_float),                # +h003C
        ("aftercast", c_float),                 # +h0040
        ("duration0", c_uint32),                # +h0044
        ("duration15", c_uint32),               # +h0048
        ("recharge", c_uint32),                 # +h004C
        ("h0050", c_uint16 * 4),                # +h0050
        ("skill_arguments", c_uint32),           # +h0058 // 1 - duration set, 2 - scale set, 4 - bonus scale set (3 would mean duration and scale is set/used by the skill)
        ("scale0", c_uint32),                   # +h005C
        ("scale15", c_uint32),                  # +h0060
        ("bonusScale0", c_uint32),              # +h0064
        ("bonusScale15", c_uint32),             # +h0068
        ("aoe_range", c_float),                 # +h006C
        ("const_effect", c_float),              # +h0070
        ("caster_overhead_animation_id", c_uint32), # +h0074 //2077 == max == no animation
        ("caster_body_animation_id", c_uint32),     # +h0078
        ("target_body_animation_id", c_uint32),     # +h007C
        ("target_overhead_animation_id", c_uint32), # +h0080
        ("projectile_animation_1_id", c_uint32),    # +h0084
        ("projectile_animation_2_id", c_uint32),    # +h0088
        ("icon_file_id", c_uint32),                  # +h008C
        ("icon_file_id_2", c_uint32),                # +h0090
        ("icon_file_id_hi_res", c_uint32),           # +h0094
        ("name", c_uint32),                           # +h0098
        ("concise", c_uint32),                        # +h009C
        ("description", c_uint32),                    # +h00A0
    ]


"""        uint8_t GetEnergyCost() const {
            switch (energy_cost) {
            case 11: return 15;
            case 12: return 25;
            default: return energy_cost;
            }
        }

        [[nodiscard]] bool IsTouchRange() const { return (special & 0x2) != 0; }
        [[nodiscard]] bool IsElite() const { return (special & 0x4) != 0; }
        [[nodiscard]] bool IsHalfRange() const { return (special & 0x8) != 0; }
        [[nodiscard]] bool IsPvP() const { return (special & 0x400000) != 0; }
        [[nodiscard]] bool IsPvE() const { return (special & 0x80000) != 0; }
        [[nodiscard]] bool IsPlayable() const { return (special & 0x2000000) == 0; }

        // NB: Guild Wars uses the skill array to build mods for weapons, so stuff like runes are skills too, and use stacking/non-stacking flags
        [[nodiscard]] bool IsStacking() const { return (special & 0x10000) != 0; }
        [[nodiscard]] bool IsNonStacking() const { return (special & 0x20000) != 0; }
        [[nodiscard]] bool IsUnused() const;
    };
    static_assert(sizeof(Skill) == 0xa4, "struct Skill has incorrect size");"""

# ---------------------------------------------------------------------
# SkillbarSkill (size = 0x14 / 20 bytes)
# ---------------------------------------------------------------------

class SkillbarSkill(Structure):
    _pack_ = 1
    _fields_ = [
        ("adrenaline_a", c_uint32),   # +h0000
        ("adrenaline_b", c_uint32),   # +h0004
        ("recharge", c_uint32),       # +h0008
        ("skill_id", c_uint32),       # +h000C
        ("event", c_uint32),          # +h0010
    ]


# ---------------------------------------------------------------------
# SkillbarCast (size = 0x08 / 8 bytes)
# ---------------------------------------------------------------------

class SkillbarCast(Structure): #Array of queued skills on a skillbar
    _pack_ = 1
    _fields_ = [
        ("h0000", c_uint16),           # +h0000
        ("skill_id", c_uint16),        # +h0002 (SkillID is uint16 here)
        ("h0004", c_uint32),           # +h0004
    ]


# ---------------------------------------------------------------------
# Skillbar (size = 0xBC / 188 bytes)
# ---------------------------------------------------------------------

class Skillbar(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),            # +h0000
        ("skills", SkillbarSkill * 8),     # +h0004
        ("disabled", c_uint32),            # +h00A4
        ("h00A8", c_uint32 * 2),           # +h00A8
        ("casting", c_uint32),             # +h00B0
        ("h00B4", c_uint32 * 2),           # +h00B4
    ]
    #bool IsValid() const { return agent_id > 0; }
    
class AgentInfo(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32 * 13),
        ("name_enc", POINTER(c_wchar)),
    ]
    
class MissionMapIcon(Structure):
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
    
  
class NPC(Structure):
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
        ("name_enc", POINTER(c_wchar)), # +h0020
        ("model_files", POINTER(c_uint32)), # +h0024
        ("files_count", c_uint32),      # +h0028 // length of ModelFile
        ("files_capacity", c_uint32),   # +h002C // capacity of ModelFile
    ]  

    """inline bool IsHenchman() { return (npc_flags & 0x10) != 0; }
    inline bool IsHero() { return (npc_flags & 0x20) != 0; }
    inline bool IsSpirit() { return (npc_flags & 0x4000) != 0; }
    inline bool IsMinion() { return (npc_flags & 0x100) != 0; }
    inline bool IsPet() { return (npc_flags & 0xD) != 0; }"""

class Player(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_uint32),                          # +h0000
        ("h0004", c_uint32 * 3),                         # +h0004
        ("appearance_bitmap", c_uint32),                 # +h0010
        ("flags", c_uint32),                             # +h0014 Bitwise field
        ("primary", c_uint32),                           # +h0018
        ("secondary", c_uint32),                         # +h001C
        ("h0020", c_uint32),                             # +h0020
        ("name_enc", POINTER(c_wchar)),                  # +h0024
        ("name", POINTER(c_wchar)),                      # +h0028
        ("party_leader_player_number", c_uint32),        # +h002C
        ("active_title_tier", c_uint32),                 # +h0030
        ("reforged_or_dhuums_flags", c_uint32),          # +h0034
        ("player_number", c_uint32),                     # +h0038
        ("party_size", c_uint32),                        # +h003C
        ("h0040_array", GW_Array),                             # +h0040 Array<void*>
    ]
 
    """  inline bool IsPvP() {
        return (flags & 0x800) != 0;
    }"""

class Title(Structure):
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
        ("points_desc", POINTER(c_wchar)),       # +h0024 Pretty sure these are ptrs to title hash strings
        ("h0028", POINTER(c_wchar)),             # +h0028 Pretty sure these are ptrs to title hash strings
    ]


    """inline bool is_percentage_based() { return (props & 1) != 0; };
    inline bool has_tiers() { return (props & 3) == 2; };"""

class TitleTier(Structure):
    _pack_ = 1
    _fields_ = [
        ("props", c_uint32),
        ("tier_number", c_uint32),
        ("tier_name_enc", POINTER(c_wchar)),
    ]

    """inline bool is_percentage_based() { return (props & 1) != 0; };"""


# ---------------------------------------------------------------------
# WorldContextStruct
# ---------------------------------------------------------------------

class WorldContextStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("account_info_ptr", POINTER(AccountInfo)),
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
        ("player_morale_info", POINTER(PartyMemberMoraleInfo)),
        ("h028C", c_uint32),
        ("party_morale_related", GW_Array), #Array<PartyMoraleLink>
        ("h063C", c_uint32 * 16),
        ("player_number", c_uint32),
        ("playerControlledChar", POINTER(PlayerControlledCharacter)),
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
        ("skillbar_array", GW_Array), #Array<Skillbar>
        ("learnable_character_skills_array", GW_Array), #Array<uint32_t>
        ("unlocked_character_skills_array", GW_Array), #Array<uint32_t>
        ("duplicated_character_skills_array", GW_Array), #Array<DupeSkill>
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
        ("agent_infos_array", GW_Array), #Array<AgentInfo>
        ("h07DC_array", GW_Array), #Array<void *>
        ("mission_map_icons_array", GW_Array), #Array<MissionMapIcon>
        ("npcs_array", GW_Array), #Array<NPC>
        ("players_array", GW_Array), #Array<Player>
        ("titles_array", GW_Array), #Array<Title>
        ("title_tiers_array", GW_Array), #Array<TitleTier>
        ("vanquished_areas_array", GW_Array), #Array<uint32_t>
        ("foes_killed", c_uint32),
        ("foes_to_kill", c_uint32),
        #//... couple more arrays after this
    ]
    
    @property
    def account_info(self) -> AccountInfo | None:
        if not self.account_info_ptr:
            return None
        return self.account_info_ptr.contents
    
    @property
    def message_buff(self) -> list[str] | None:
        messages = GW_Array_View(self.message_buff_array, c_wchar).to_list()
        if not messages:
            return None
        return [str(ch) for ch in messages]

    @property
    def dialog_buff(self) -> list[str] | None:
        dialogs = GW_Array_View(self.dialog_buff_array, c_wchar).to_list()
        if not dialogs:
            return None
        return [str(ch) for ch in dialogs]
    
    @property
    def merch_items(self) -> list[int] | None:
        items = GW_Array_View(self.merch_items_array, c_uint32).to_list()
        if not items:
            return None
        return [int(item) for item in items]
    
    @property
    def merch_items2(self) -> list[int] | None:
        items = GW_Array_View(self.merch_items2_array, c_uint32).to_list()
        if not items:
            return None
        return [int(item) for item in items]
    
    @property
    def map_agents(self) -> list[MapAgent] | None:
        agents = GW_Array_Value_View(self.map_agents_array, MapAgent).to_list()
        if not agents:
            return None
        return [agent for agent in agents]
    
    @property
    def party_allies(self) -> list[PartyAlly] | None:
        allies = GW_Array_Value_View(self.party_allies_array, PartyAlly).to_list()
        if not allies:
            return None
        return [ally for ally in allies]
    
    @property
    def party_attributes(self) -> list[PartyAttribute] | None:
        attrs = GW_Array_Value_View(self.party_attributes_array, PartyAttribute).to_list()
        if not attrs:
            return None
        return [attr for attr in attrs]
    
    @property
    def all_flag(self) -> Vec3f | None:
        x, y, z = self.all_flag_array

        if not math.isfinite(x) or not math.isfinite(y) or not math.isfinite(z):
            return None

        return Vec3f(x, y, z)

    @property
    def h04B8_ptrs(self) -> list[int] | None:
        ptrs = GW_Array_View(self.h04B8_array, c_void_p).to_list()
        if not ptrs:
            return None
        return [int(ptr) for ptr in ptrs]
    
    @property
    def h04C8_ptrs(self) -> list[int] | None:
        ptrs = GW_Array_View(self.h04C8_array, c_void_p).to_list()
        if not ptrs:
            return None
        return [int(ptr) for ptr in ptrs]
    
    @property
    def h04DC_ptrs(self) -> list[int] | None:
        ptrs = GW_Array_View(self.h04DC_array, c_void_p).to_list()
        if not ptrs:
            return None
        return [int(ptr) for ptr in ptrs]
    
    @property
    def party_effects(self) -> list[AgentEffects] | None:
        effects = GW_Array_Value_View(self.party_effects_array, AgentEffects).to_list()
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
    def quest_log(self) -> list[Quest] | None:
        quests = GW_Array_Value_View(self.quest_log_array, Quest).to_list()
        if not quests:
            return None
        return [quest for quest in quests]
    
    @property
    def mission_objectives(self) -> list[MissionObjective] | None:
        objectives = GW_Array_Value_View(self.mission_objectives_array, MissionObjective).to_list()
        if not objectives:
            return None
        return [obj for obj in objectives]

class WorldContext:
    _ptr: int = 0
    _callback_name = "WorldContext.UpdateWorldContextPtr"

    @staticmethod
    def get_ptr() -> int:
        return WorldContext._ptr

    @staticmethod
    def _update_ptr():
        WorldContext._ptr = PyPlayer.PyPlayer().GetWorldContextPtr()

    @staticmethod
    def enable():
        Game.register_callback(
            WorldContext._callback_name,
            WorldContext._update_ptr
        )

    @staticmethod
    def disable():
        Game.remove_callback(WorldContext._callback_name)
        WorldContext._ptr = 0

    @staticmethod
    def get_context() -> WorldContextStruct | None:
        ptr = WorldContext._ptr
        if not ptr:
            return None
        return cast(
            ptr,
            POINTER(WorldContextStruct)
        ).contents
        
WorldContext.enable()