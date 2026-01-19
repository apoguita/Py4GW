from ctypes import Structure
from typing import Optional
from ..internals.gw_array import GW_Array
from ..internals.types import Vec2f, Vec3f, GamePos, CPointer

#region AccountInfo
class AccountInfoStruct(Structure):
    account_name_ptr: Optional[int]
    wins: int
    losses: int
    rating: int
    qualifier_points: int
    rank: int
    tournament_reward_points: int
    
    @property
    def account_name_str(self) -> str | None: ...
   
class MapAgentStruct(Structure):
    cur_energy: float
    max_energy: float
    energy_regen: float
    skill_timestamp: int
    h0010: float
    max_energy2: float
    h0018: float
    h001C: int
    cur_health: float
    max_health: float
    health_regen: float
    h002C: int
    effects: int
    
    @property
    def is_bleeding(self) -> bool: ...
    @property
    def is_conditioned(self) -> bool: ...
    @property
    def is_crippled(self) -> bool: ...
    @property
    def is_dead(self) -> bool: ...
    @property
    def is_deep_wounded(self) -> bool: ...
    @property
    def is_poisoned(self) -> bool: ...
    @property
    def is_enchanted(self) -> bool: ...
    @property
    def is_degen_hexed(self) -> bool: ...
    @property
    def is_hexed(self) -> bool: ...
    @property
    def is_weapon_spelled(self) -> bool: ...
    
class PartyAllyStruct(Structure):
    agent_id: int
    unk : int
    composite_id: int
    
class AttributeStruct(Structure):
    attribute_id: int
    level_base: int
    level: int
    decrement_points: int
    increment_points: int
    
    @property
    def name(self) -> str: ...
    def GetName(self) -> str: ...
    
class PartyAttributeStruct(Structure):
    agent_id: int
    attribute_array: list[AttributeStruct]   # fixed-size array [54]
    
    @property
    def attributes(self) -> list[AttributeStruct]: ...
    
class EffectStruct(Structure):
    skill_id: int
    attribute_level: int
    effect_id: int
    agent_id: int
    duration: float
    timestamp: int

class BuffStruct(Structure):
    skill_id: int
    h0004: int
    buff_id: int
    target_agent_id: int


class AgentEffectsStruct(Structure):
    agent_id: int
    buff_array: GW_Array          # GW_Array<BuffStruct>
    effect_array: GW_Array        # GW_Array<EffectStruct> 
    
    @property
    def buffs(self) -> list[BuffStruct]: ...
    @property
    def effects(self) -> list[EffectStruct]: ...

    
class QuestStruct(Structure):
    quest_id: int
    log_state: int
    location_ptr: Optional[str]
    name_ptr: Optional[int]
    npc_ptr: Optional[int]
    map_from: int
    marker_ptr: GamePos
    h0024: int
    map_to: int
    description_ptr: Optional[int]
    objectives_ptr: Optional[int]
    
    @property
    def is_completed(self) -> bool: ...
    @property
    def is_current_mission_quest(self) -> bool: ...
    @property
    def is_area_primary(self) -> bool: ...
    @property
    def is_primary(self) -> bool: ...
    @property
    def location_str(self) -> str | None: ...
    @property
    def location_encoded_str(self) -> str | None: ...
    @property
    def name_str(self) -> str | None: ...
    @property
    def name_encoded_str(self) -> str | None: ...
    @property
    def npc_str(self) -> str | None: ...
    @property
    def npc_encoded_str(self) -> str | None: ...
    @property
    def description_str(self) -> str | None: ...
    @property
    def description_encoded_str(self) -> str | None: ...
    @property
    def objectives_str(self) -> str | None: ...
    @property
    def objectives_encoded_str(self) -> str | None: ...
    @property
    def marker(self) -> GamePos | None: ...
    
class MissionObjectiveStruct(Structure):
    objective_id: int
    enc_str_ptr: Optional[int]
    type: int
    
    @property
    def enc_str(self) -> str | None: ...
    @property
    def enc_str_encoded_str(self) -> str | None: ...
    

class HeroFlagStruct(Structure):
    hero_id: int
    agent_id: int
    level: int
    hero_behavior: int
    flag_ptr : Vec2f
    h0018: int
    locked_target_id: int
    h0020: int
    @property
    def flag(self) -> Vec2f | None: ...

class HeroInfoStruct(Structure):
    hero_id: int
    agent_id: int
    level: int
    primary: int
    secondary: int
    hero_file_id: int
    model_file_id: int
    h001C: list[int]        # fixed-size array [52]
    name_encoded_str: str
    
    @property
    def name_str(self) -> str | None: ...

class ControlledMinionsStruct(Structure):
    agent_id: int
    minion_count: int   
    

class PartyMemberMoraleInfoStruct(Structure):
    agent_id : int
    agent_id_dupe : int
    unk : list[int]
    morale : int

class PartyMoraleLinkStruct(Structure):
    unk: int
    unk2: int
    party_member_info_ptr: Optional[PartyMemberMoraleInfoStruct]
    
    @property
    def party_member_info(self) -> PartyMemberMoraleInfoStruct | None: ...
    
class PlayerControlledCharacterStruct(Structure):
    field0_0x0: int
    field1_0x4: int
    field2_0x8: int
    field3_0xc: int
    field4_0x10: int
    agent_id: int
    composite_id: int
    field7_0x1c: int
    field8_0x20: int
    field9_0x24: int
    field10_0x28: int
    field11_0x2c: int
    field12_0x30: int
    field13_0x34: int
    field14_0x38: int
    field15_0x3c: int
    field16_0x40: int
    field17_0x44: int
    field18_0x48: int
    field19_0x4c: float
    field20_0x50: float
    field21_0x54: int
    field22_0x58: int
    field23_0x5c: int
    field24_0x60: int
    more_flags: int
    field26_0x68: int
    field27_0x6c: int
    field28_0x70: int
    field29_0x74: int
    field30_0x78: int
    field31_0x7c: int
    field32_0x80: int
    field33_0x84: int
    field34_0x88: int
    field35_0x8c: int
    field36_0x90: int
    field37_0x94: int
    field38_0x98: int
    field39_0x9c: int
    field40_0xa0: int
    field41_0xa4: int
    field42_0xa8: int
    field43_0xac: int
    field44_0xb0: int
    field45_0xb4: int
    field46_0xb8: int
    field47_0xbc: int
    field48_0xc0: int
    field49_0xc4: int
    field50_0xc8: int
    field51_0xcc: int
    field52_0xd0: int
    field53_0xd4: int
    field54_0xd8: int
    field55_0xdc: int
    field56_0xe0: int
    field57_0xe4: int
    field58_0xe8: int
    field59_0xec: int
    field60_0xf0: int
    field61_0xf4: int
    field62_0xf8: int
    field63_0xfc: int
    field64_0x100: int
    field65_0x104: int
    field66_0x108: int
    flags: int
    field68_0x110: int
    field69_0x114: int
    field70_0x118: int
    field71_0x11c: int
    field72_0x120: int
    field73_0x124: int
    field74_0x128: int
    field75_0x12c: int
    field76_0x130: int
    
class ProfessionStateStruct(Structure):
    agent_id: int
    primary : int
    secondary : int
    unlocked_professions : int #bitwise flags
    unk : int
    
    def IsProfessionUnlocked(self, profession_bit: int) -> bool: ...

class SkillbarSkillStruct(Structure):
    adrenaline_a: int
    adrenaline_b: int
    recharge: int
    skill_id: int
    event: int


class SkillbarCastStruct(Structure):
    h0000: int
    skill_id: int
    h0004: int

class SkillbarStruct(Structure):
    agent_id: int
    skills: list[SkillbarSkillStruct]
    disabled: int
    cast_array: GW_Array          # GW_Array<SkillbarCastStruct>
    h00B8: int
    
    @property
    def is_valid(self) -> bool: ...
    
    @property
    def casted_skills(self) -> list[SkillbarCastStruct]: ...
    
    def GetSkillById(self, skill_id: int) -> SkillbarSkillStruct | None: ...
    
    

class DupeSkillStruct(Structure):
    skill_id : int
    count : int
    
class AgentNameInfoStruct(Structure):
    h0000: list[int]        # fixed-size array [13]
    name_enc_ptr: Optional[str]
    @property
    def name_encoded_str(self) -> str | None: ...
    @property
    def name_str(self) -> str | None: ...
    
class MissionMapIconStruct(Structure):
    index: int
    X: float
    Y: float
    h000C: int
    h0010: int
    option: int
    h0018: int
    model_id: int
    h0020: int
    h0024: int

class PetInfoStruct(Structure):
    agent_id: int
    owner_agent_id: int
    pet_name_ptr: Optional[str]
    model_file_id1: int
    model_file_id2: int
    behavior: int
    locked_target_id: int
    
    @property
    def pet_name_encoded_str(self) -> str | None: ...
    @property
    def pet_name_str(self) -> str | None: ...

class NPC_ModelStruct(Structure):
    model_file_id: int
    h0004: int
    scale: int
    sex: int
    npc_flags: int
    primary: int
    h0018: int
    default_level: int
    padding1: int
    padding2: int
    name_enc_ptr: Optional[str]
    model_files_ptr: Optional[int]     # pointer to uint32_t buffer
    files_count: int
    files_capacity: int  
    
    @property
    def is_valid(self) -> bool: ...
    @property
    def is_henchman(self) -> bool: ...
    @property
    def is_hero(self) -> bool: ...
    @property
    def is_spirit(self) -> bool: ...
    @property
    def is_minion(self) -> bool: ...
    @property
    def is_pet(self) -> bool: ...
    @property
    def name_encoded_str(self) -> str | None: ...
    @property
    def name_str(self) -> str | None: ...
    @property
    def model_files(self) -> list[int] | None: ...

    
class PlayerStruct(Structure):
    agent_id: int
    h0004: list[int]                # fixed-size array [3]
    appearance_bitmap: int
    flags: int
    primary: int
    secondary: int
    h0020: int
    name_enc_ptr: Optional[str]
    name_ptr: Optional[str]
    party_leader_player_number: int
    active_title_tier: int
    reforged_or_dhuums_flags: int
    player_number: int
    party_size: int
    h0040_array: GW_Array  # GW_Array<void*>   
    
    @property 
    def is_pvp(self) -> bool: ...
    @property
    def name_enc_encoded_str(self) -> str | None: ...
    @property
    def name_enc_str(self) -> str | None: ...
    @property
    def name_encoded_str(self) -> str | None: ...
    @property
    def name_str(self) -> str | None: ...
    @property
    def h0040_ptrs(self) -> list[int]: ...
    
class TitleStruct(Structure):
    props: int
    current_points: int
    current_title_tier_index: int
    points_needed_current_rank: int
    next_title_tier_index: int
    points_needed_next_rank: int
    max_title_rank: int
    max_title_tier_index: int
    h0020: int
    points_desc_ptr: Optional[str]
    h0028_ptr: Optional[str]
    
    @property
    def is_percentage_based(self) -> bool: ...
    @property
    def has_tiers(self) -> bool: ...
    @property
    def points_desc_encoded_str(self) -> str | None: ...
    @property
    def points_desc_str(self) -> str | None: ...
    @property
    def h0028_encoded_str(self) -> str | None: ...
    @property
    def h0028_str(self) -> str | None: ...
    
class TitleTierStruct(Structure):
    props: int
    tier_number: int
    tier_name_enc_ptr: Optional[str]
    @property
    def tier_name_encoded_str(self) -> str | None: ...
    @property
    def tier_name_str(self) -> str | None: ...
    @property
    def is_percentage_based(self) -> bool: ...
    
#region WorldContextStruct
class WorldContextStruct(Structure):
    account_info_ptr: Optional[CPointer[AccountInfoStruct]]

    message_buff_array: GW_Array
    dialog_buff_array: GW_Array
    merch_items_array: GW_Array
    merch_items2_array: GW_Array

    accumMapInitUnk0: int
    accumMapInitUnk1: int
    accumMapInitOffset: int
    accumMapInitLength: int
    h0054: int
    accumMapInitUnk2: int
    h005C: list[int]                    # fixed-size array [8]

    map_agents_array: GW_Array
    party_allies_array: GW_Array

    all_flag_array: list[float]          # fixed-size array [3]            
    h00A8: int

    party_attributes_array: GW_Array
    
    h00BC: list[int]                    # fixed-size array [255]

    h04B8_array: GW_Array
    h04C8_array: GW_Array
    h04D8: int
    h04DC_array: GW_Array
    h04EC: list[int]                    # fixed-size array [7]

    party_effects_array: GW_Array
    h0518_array: GW_Array

    active_quest_id: int
    quest_log_array: GW_Array
    h053C: list[int]                    # fixed-size array [10]

    mission_objectives_array: GW_Array
    henchmen_agent_ids_array: GW_Array
    hero_flags_array: GW_Array
    hero_info_array: GW_Array
    cartographed_areas_array: GW_Array

    h05B4: list[int]                    # fixed-size array [2]

    controlled_minion_count_array: GW_Array
    missions_completed_array: GW_Array
    missions_bonus_array: GW_Array
    missions_completed_hm_array: GW_Array
    missions_bonus_hm_array: GW_Array
    unlocked_map_array: GW_Array

    h061C: list[int]                    # fixed-size array [2]

    player_morale_ptr: Optional[PartyMemberMoraleInfoStruct]
    h028C: int

    party_morale_array: GW_Array
    h063C: list[int]                    # fixed-size array [16]

    player_number: int
    playerControlledChar_ptr: Optional[PlayerControlledCharacterStruct]

    is_hard_mode_unlocked: int
    h0688: list[int]                    # fixed-size array [2]

    salvage_session_id: int
    h0694: list[int]                    # fixed-size array [5]

    playerTeamToken: int

    pets_array: GW_Array
    party_profession_states_array: GW_Array
    h06CC_array: GW_Array
    h06DC: int
    h06E0_array: GW_Array

    party_skillbar_array: GW_Array
    learnable_character_skills_array: GW_Array
    unlocked_character_skills_array: GW_Array
    duplicated_character_skills_array: GW_Array
    h0730_array: GW_Array

    experience: int
    experience_dupe: int
    current_kurzick: int
    current_kurzick_dupe: int
    total_earned_kurzick: int
    total_earned_kurzick_dupe: int
    current_luxon: int
    current_luxon_dupe: int
    total_earned_luxon: int
    total_earned_luxon_dupe: int
    current_imperial: int
    current_imperial_dupe: int
    total_earned_imperial: int
    total_earned_imperial_dupe: int

    unk_faction4: int
    unk_faction4_dupe: int
    unk_faction5: int
    unk_faction5_dupe: int

    level: int
    level_dupe: int
    morale: int
    morale_dupe: int

    current_balth: int
    current_balth_dupe: int
    total_earned_balth: int
    total_earned_balth_dupe: int

    current_skill_points: int
    current_skill_points_dupe: int
    total_earned_skill_points: int
    total_earned_skill_points_dupe: int

    max_kurzick: int
    max_luxon: int
    max_balth: int
    max_imperial: int

    equipment_status: int

    agent_name_info_array: GW_Array
    h07DC_array: GW_Array
    mission_map_icons_array: GW_Array
    npc_models_array: GW_Array
    players_array: GW_Array
    titles_array: GW_Array
    title_tiers_array: GW_Array
    vanquished_areas_array: GW_Array

    foes_killed: int
    foes_to_kill: int
    
    @property
    def account_info(self) -> AccountInfoStruct | None: ...
    @property
    def message_buff(self) -> list[str] | None: ...
    @property
    def dialog_buff(self) -> list[str] | None: ...
    @property
    def merch_items(self) -> list[int] | None: ...
    @property
    def merch_items2(self) -> list[int] | None: ...
    @property
    def map_agents(self) -> list[MapAgentStruct] | None: ...
    @property
    def party_allies(self) -> list[PartyAllyStruct] | None: ...
    @property
    def party_attributes(self) -> list[PartyAttributeStruct] | None: ...

    def get_attributes_by_agent_id(self, agent_id: int) -> list[AttributeStruct]:...
    
    @property
    def all_flag(self) -> Vec3f | None: ...
    @property
    def h04B8_ptrs(self) -> list[int] | None: ...
    @property
    def h04C8_ptrs(self) -> list[int] | None: ...
    @property
    def h04DC_ptrs(self) -> list[int] | None: ...
    @property
    def party_effects(self) -> list[AgentEffectsStruct] | None: ...
    @property
    def h0518_ptrs(self) -> list[int] | None: ...
    @property
    def quest_log(self) -> list[QuestStruct] | None: ...
    @property
    def mission_objectives(self) -> list[MissionObjectiveStruct] | None: ...
    @property
    def henchmen_agent_ids(self) -> list[int] | None: ...
    @property
    def hero_flags(self) -> list[HeroFlagStruct] | None: ...
    @property
    def hero_info(self) -> list[HeroInfoStruct] | None: ...
    @property
    def cartographed_areas(self) -> list[int] | None: ...
    @property
    def controlled_minions(self) -> list[ControlledMinionsStruct] | None: ...
    @property
    def missions_completed(self) -> list[int] | None: ...
    @property
    def missions_bonus(self) -> list[int] | None: ...
    @property
    def missions_completed_hm(self) -> list[int] | None: ...
    @property
    def missions_bonus_hm(self) -> list[int] | None: ...
    @property
    def unlocked_maps(self) -> list[int] | None: ...
    @property
    def player_morale(self) -> PartyMemberMoraleInfoStruct | None: ...
    @property
    def party_morale(self) -> list[PartyMoraleLinkStruct] | None: ...
    @property
    def player_controlled_character(self) -> PlayerControlledCharacterStruct | None: ...
    @property
    def pets(self) -> list[PetInfoStruct] | None: ...
    @property
    def party_profession_states(self) -> list[ProfessionStateStruct] | None: ...
    @property
    def h06CC_ptrs(self) -> list[int] | None: ...
    @property 
    def h06E0_ptrs(self) -> list[int] | None: ...
    @property
    def party_skillbars(self) -> list[SkillbarStruct] | None: ...
    @property
    def learnable_character_skills(self) -> list[int] | None: ...
    @property
    def unlocked_character_skills(self) -> list[int] | None: ...
    @property
    def duplicated_character_skills(self) -> list[DupeSkillStruct] | None: ...
    @property
    def h0730_ptrs(self) -> list[int] | None: ...
    @property
    def agent_name_info(self) -> list[AgentNameInfoStruct] | None: ...
    @property
    def h07DC_ptrs(self) -> list[int] | None: ...
    @property
    def mission_map_icons(self) -> list[MissionMapIconStruct] | None: ...
    @property
    def npc_models(self) -> list[NPC_ModelStruct] | None: ...
    @property
    def players(self) -> list[PlayerStruct] | None: ...
    @property
    def titles(self) -> list[TitleStruct] | None: ...
    @property
    def title_tiers(self) -> list[TitleTierStruct] | None: ...
    @property
    def vanquished_areas(self) -> list[int] | None: ...
    def GetPlayerById(self, player_id: int) -> PlayerStruct | None:...
# ----------------------------------------------------------------------
# PreGameContext facade
# ----------------------------------------------------------------------
class WorldContext:
    @staticmethod
    def get_ptr() -> int: ...

    @staticmethod
    def enable() -> None: ...

    @staticmethod
    def disable() -> None: ...

    @staticmethod
    def get_context() -> Optional[WorldContextStruct]: ...