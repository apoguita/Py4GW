from typing import Optional
from ctypes import Structure
from ..internals.types import Vec2f
from ..internals.gw_array import GW_BaseArray

class LoginCharacter(Structure):
    # ── Header (0x00–0x07) ──
    appearance_packed: int      # 0x00 packed bitfield (8 appearance fields)
    pvp_flag: int               # 0x04 PvP character flag
    # ── Guild GUID (0x08–0x17) ──
    guild_guid_0: int           # 0x08
    guild_guid_1: int           # 0x0C
    guild_guid_2: int           # 0x10
    guild_guid_3: int           # 0x14
    # ── Items TArray (0x18–0x23) ──
    items_data: int             # 0x18 data pointer
    items_capacity: int         # 0x1C
    items_count: int            # 0x20
    # ── Padding (0x24–0x27) ──
    items_param: int            # 0x24
    # ── Core Data (0x28–0x2F) ──
    level: int                  # 0x28
    current_map_id: int         # 0x2C
    # ── Profession & Flags (0x30–0x4B) ──
    field_0x30: int             # 0x30 UNRESOLVED
    primary_profession: int     # 0x34
    profession_enum: int         # 0x38 ECharProfession
    field_0x3C: int             # 0x3C
    field_0x40: int             # 0x40 UNRESOLVED
    field_0x44: int             # 0x44 UNRESOLVED
    field_0x48: int             # 0x48 UNRESOLVED
    # ── Model & Name (0x4C–0x77) ──
    char_model_ptr: int         # 0x4C CCharModel*
    character_name_enc: str     # 0x50 inline wchar_t[20]

    @property
    def guild_guid(self) -> bytes: ...

    @property
    def character_name(self) -> str | None: ...

class PreGameContextStruct(Structure):
    frame_id: int
    scene_type: int
    scene_controller_iface: int
    camera_pitch_frequency: float
    camera_pitch_current: float
    camera_pitch_target: float
    camera_pitch_velocity: float
    RESERVED_0x1C: list[int]     # 12 dwords (48 bytes)
    camera_mode: int
    RESERVED_0x50: list[int]     # 5 dwords (20 bytes)
    RESERVED_0x64: int
    camera_limits_frequency: float
    camera_limits_min_current: float
    camera_limits_max_current: float
    camera_limits_min_target: float
    camera_limits_max_target: float
    camera_limits_min_velocity: float
    camera_limits_max_velocity: float
    scroll_offset_frequency: float
    scroll_offset_current: float
    scroll_offset_target: float
    scroll_offset_velocity: float
    scroll_speed_frequency: float
    scroll_speed_current: float
    scroll_speed_target: float
    scroll_speed_velocity: float
    camera_height: float
    camera_height_min: float
    camera_height_max: float
    camera_rotation_frequency: float
    camera_rotation_current: float
    camera_rotation_target: float
    camera_rotation_velocity: float
    RESERVED_0xC0: list[int]     # 4 dwords (16 bytes)
    # ── TAIL (0xD0–0xFF) ──
    max_characters: int
    chosen_character_index: int
    preview_character_index: int
    pending_character_index: int
    chars_array: GW_BaseArray
    char_creation_flag: int
    create_slot_index: int
    sentinel_guard: int
    self_link: int
    list_head: int
    
    @property
    def chars_list(self) -> list[LoginCharacter]: ...
    
# ----------------------------------------------------------------------
# PreGameContext facade
# ----------------------------------------------------------------------
class PreGameContext:
    @staticmethod
    def get_ptr() -> int: ...

    @staticmethod
    def enable() -> None: ...

    @staticmethod
    def disable() -> None: ...

    @staticmethod
    def get_context() -> Optional[PreGameContextStruct]: ...