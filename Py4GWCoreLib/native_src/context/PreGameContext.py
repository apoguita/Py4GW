import PyPointers
from ctypes import Structure, c_uint32, c_int32, c_float, c_void_p, sizeof, cast, POINTER, c_wchar
from ..internals.types import Vec2f
from ..internals.gw_array import GW_Array, GW_BaseArray, GW_Array_View, GW_Array_Value_View
from ..internals.helpers import read_wstr, encoded_wstr_to_str


class LoginCharacter(Structure):
    _pack_ = 1
    _fields_ = [
        # ── Header (0x00–0x07) ──
        ("appearance_packed", c_uint32),     # 0x00 packed bitfield (8 appearance fields via CharDataAppearanceUnpack)
        ("pvp_flag", c_uint32),              # 0x04 PvP character flag; zeroed for non-PvP chars
        # ── Guild GUID (0x08–0x17) ──
        ("guild_guid_0", c_uint32),          # 0x08 Guild GUID[0]
        ("guild_guid_1", c_uint32),          # 0x0C Guild GUID[1]
        ("guild_guid_2", c_uint32),          # 0x10 Guild GUID[2]
        ("guild_guid_3", c_uint32),          # 0x14 Guild GUID[3]
        # ── Items TArray (0x18–0x23) ──
        ("items_data", c_void_p),            # 0x18 TArray<Item> data pointer (freed in OnNotifyClear)
        ("items_capacity", c_uint32),        # 0x1C TArray capacity
        ("items_count", c_uint32),           # 0x20 TArray count
        # ── Padding (0x24–0x27) ──
        ("items_param", c_uint32),           # 0x24 likely TArray m_param or dead padding
        # ── Core Data (0x28–0x2F) ──
        ("level", c_uint32),                 # 0x28
        ("current_map_id", c_uint32),        # 0x2C
        # ── Profession & Flags (0x30–0x4B) ──
        ("field_0x30", c_uint32),            # 0x30 UNRESOLVED (possibly experience/time_played)
        ("primary_profession", c_uint32),    # 0x34 unpacked profession for fast access
        ("profession_enum", c_uint32),        # 0x38 ECharProfession enum
        ("field_0x3C", c_uint32),            # 0x3C likely is_pvp_character flag
        ("field_0x40", c_uint32),            # 0x40 UNRESOLVED (flag)
        ("field_0x44", c_uint32),            # 0x44 UNRESOLVED (flag)
        ("field_0x48", c_uint32),            # 0x48 UNRESOLVED (flag)
        # ── Model & Name (0x4C–0x77) ──
        ("char_model_ptr", c_void_p),        # 0x4C CCharModel* (refcounted, freed on clear)
        ("character_name_enc", c_wchar * 20),# 0x50 inline wchar_t[20], confirmed via i32.store16
    ]

    @property
    def guild_guid(self) -> bytes:
        import struct
        return struct.pack('<IIII', self.guild_guid_0, self.guild_guid_1, self.guild_guid_2, self.guild_guid_3)

    @property
    def character_name(self) -> str | None:
        return encoded_wstr_to_str(self.character_name_enc)


class PreGameContextStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("frame_id", c_uint32),
        ("scene_type", c_uint32),
        ("scene_controller_iface", c_uint32),
        ("camera_pitch_frequency", c_float),
        ("camera_pitch_current", c_float),
        ("camera_pitch_target", c_float),
        ("camera_pitch_velocity", c_float),
        ("RESERVED_0x1C", c_uint32 * 12),
        ("camera_mode", c_uint32),
        ("RESERVED_0x50", c_uint32 * 5),
        ("RESERVED_0x64", c_uint32),
        ("camera_limits_frequency", c_float),
        ("camera_limits_min_current", c_float),
        ("camera_limits_max_current", c_float),
        ("camera_limits_min_target", c_float),
        ("camera_limits_max_target", c_float),
        ("camera_limits_min_velocity", c_float),
        ("camera_limits_max_velocity", c_float),
        ("scroll_offset_frequency", c_float),
        ("scroll_offset_current", c_float),
        ("scroll_offset_target", c_float),
        ("scroll_offset_velocity", c_float),
        ("scroll_speed_frequency", c_float),
        ("scroll_speed_current", c_float),
        ("scroll_speed_target", c_float),
        ("scroll_speed_velocity", c_float),
        ("camera_height", c_float),
        ("camera_height_min", c_float),
        ("camera_height_max", c_float),
        ("camera_rotation_frequency", c_float),
        ("camera_rotation_current", c_float),
        ("camera_rotation_target", c_float),
        ("camera_rotation_velocity", c_float),
        ("RESERVED_0xC0", c_uint32 * 4),
        # ── TAIL (0xD0–0xFF) — DO NOT CHANGE ──
        ("max_characters", c_uint32),
        ("chosen_character_index", c_int32),
        ("preview_character_index", c_int32),
        ("pending_character_index", c_int32),
        ("chars_array", GW_BaseArray),
        ("char_creation_flag", c_int32),
        ("create_slot_index", c_int32),
        ("sentinel_guard", c_uint32),
        ("self_link", c_void_p),
        ("list_head", c_uint32),
    ]
    
    @property
    def chars_list(self) -> list[LoginCharacter]:
        # GW_BaseArray (0x0C) is compatible with GW_Array_Value_View — both have
        # m_buffer at +0x00 and m_size at +0x08
        return GW_Array_Value_View(self.chars_array, LoginCharacter).to_list()

# Struct size assertions — verified against WASM ground truth (0x100 total, 0x78 LoginCharacter stride)
assert sizeof(LoginCharacter) == 0x78, f"LoginCharacter size mismatch: {sizeof(LoginCharacter)} != 0x78"
assert sizeof(PreGameContextStruct) == 0x100, f"PreGameContextStruct size mismatch: {sizeof(PreGameContextStruct)} != 0x100"

class PreGameContext:
    _ptr: int = 0
    _cached_ctx: PreGameContextStruct | None = None
    _callback_name = "PreGameContext.UpdatePtr"

    @staticmethod
    def get_ptr() -> int:
        return PreGameContext._ptr

    @staticmethod
    def _update_ptr():
        from ...native_src.ShMem.SysShaMem import SystemShaMemMgr
        if (SSM := SystemShaMemMgr.get_pointers_struct()) is None:
            return
        ptr = SSM.PreGameContext
        #ptr = PyPointers.PyPointers.GetPreGameContextPtr()
        PreGameContext._ptr = ptr
        if not ptr:
            PreGameContext._cached_ctx = None
            return
        PreGameContext._cached_ctx = cast(
            ptr,
            POINTER(PreGameContextStruct)
        ).contents

    @staticmethod
    def enable():
        import PyCallback
        PyCallback.PyCallback.Register(
            PreGameContext._callback_name,
            PyCallback.Phase.PreUpdate,
            PreGameContext._update_ptr,
            priority=99,
            context=PyCallback.Context.Draw
        )

    @staticmethod
    def disable():
        import PyCallback
        PyCallback.PyCallback.RemoveByName(PreGameContext._callback_name)
        PreGameContext._ptr = 0
        PreGameContext._cached_ctx = None

    @staticmethod
    def get_context() -> PreGameContextStruct | None:
        return PreGameContext._cached_ctx
    
PreGameContext.enable()