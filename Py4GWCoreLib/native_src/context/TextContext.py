"""TextParser context — game string subsystem accessed via GameContext+0x18.

Pointer chain (from GWCA + Ghidra RE):
    GameContext       = PyPointers.GetGameContextPtr()
    TextParser        = *(GameContext + 0x18)

TextParser contains an inline TextCache region starting at +0x30.
Within that region, per-language file slot arrays describe which dat
files hold string entries for each language.

TextParser layout (0x1D4 bytes, from GWCA TextParser.h + RE):
    +0x000: h0000[8]             (32 bytes, unknown)
    +0x020: dec_start            (wchar_t*)
    +0x024: dec_end              (wchar_t*)
    +0x028: substitute_1
    +0x02C: substitute_2
    +0x030: inline TextCache start
        +0x064: language_slots[11]   (LanguageSlotStruct * 11)
        +0x148: entries_per_file     (1024)
    +0x160: h0160
    +0x180: sub_struct_ptr
    +0x1D0: language_id          (GW::Constants::Language)

File slot array entries (TextFileSlotStruct, 0x24 bytes each):
    +0x08: file_hash_ptr     (ptr to wchar16 hash for dat lookup)
    +0x10: lang_id
    +0x14: start_index
    +0x18: end_index
"""

import ctypes
from ctypes import Structure, POINTER, c_uint32, c_uint8, cast

import PyPointers

from .GameContext import GameContextStruct


# ─── Structures ───────────────────────────────────────────────────────────

class TextFileSlotStruct(Structure):
    """Single file slot describing a dat string file (0x24 bytes)."""
    _pack_ = 1
    _fields_ = [
        ("_pad0", c_uint8 * 8),         # +0x00
        ("file_hash_ptr", c_uint32),     # +0x08  ptr to wchar16 hash string
        ("_pad1", c_uint32),             # +0x0C
        ("lang_id", c_uint32),           # +0x10
        ("start_index", c_uint32),       # +0x14
        ("end_index", c_uint32),         # +0x18
        ("_pad2", c_uint8 * 8),          # +0x1C
    ]

    @property
    def file_hash(self) -> str:
        """Read the null-terminated wchar16 hash string from the pointer."""
        ptr = self.file_hash_ptr
        if not ptr:
            return ""
        chars: list[str] = []
        while True:
            v = ctypes.c_uint16.from_address(ptr).value
            if v == 0:
                break
            chars.append(chr(v))
            ptr += 2
        return ''.join(chars)


class LanguageSlotStruct(Structure):
    """Per-language file slot metadata (0x0C bytes)."""
    _pack_ = 1
    _fields_ = [
        ("slot_array_ptr", c_uint32),    # +0x00  ptr to TextFileSlotStruct[]
        ("_h0004", c_uint32),            # +0x04
        ("slot_count", c_uint32),        # +0x08
    ]


_MAX_LANGUAGES = 11


class TextParserStruct(Structure):
    """TextParser from GWCA + inline TextCache (0x1D4 bytes total)."""
    _pack_ = 1
    _fields_ = [
        # TextParser header (from GWCA)
        ("_h0000", c_uint32 * 8),                               # +0x000  (32 bytes)
        ("dec_start_ptr", c_uint32),                             # +0x020
        ("dec_end_ptr", c_uint32),                               # +0x024
        ("substitute_1", c_uint32),                              # +0x028
        ("substitute_2", c_uint32),                              # +0x02C

        # Inline TextCache region
        ("_cache_header", c_uint8 * 0x34),                       # +0x030  (52 bytes, hash map etc.)
        ("language_slots", LanguageSlotStruct * _MAX_LANGUAGES),  # +0x064  (132 bytes)
        ("_cache_pad", c_uint8 * 0x60),                          # +0x0E8  (96 bytes)
        ("entries_per_file", c_uint32),                          # +0x148

        # Post-cache TextParser fields (from GWCA)
        ("_pad_post_cache", c_uint8 * 0x14),                     # +0x14C  (20 bytes)
        ("h0160", c_uint32),                                     # +0x160
        ("h0164", c_uint32),                                     # +0x164
        ("h0168", c_uint32),                                     # +0x168
        ("_h016C", c_uint32 * 5),                                # +0x16C  (20 bytes)
        ("sub_struct_ptr", c_uint32),                            # +0x180
        ("_h0184", c_uint32 * 19),                               # +0x184  (76 bytes)
        ("language_id", c_uint32),                               # +0x1D0
    ]

    def get_file_slot(self, slot_idx: int, language: int = 0) -> TextFileSlotStruct | None:
        """Read a file slot struct for the given language and slot index."""
        if language >= _MAX_LANGUAGES:
            return None
        lang_slot = self.language_slots[language]
        if slot_idx >= lang_slot.slot_count or not lang_slot.slot_array_ptr:
            return None
        addr = lang_slot.slot_array_ptr + slot_idx * ctypes.sizeof(TextFileSlotStruct)
        return TextFileSlotStruct.from_address(addr)


# ─── Facade ───────────────────────────────────────────────────────────────

class TextParser:
    """Cached accessor for the game's TextParser context."""

    _ptr: int = 0
    _cached_ctx: TextParserStruct | None = None
    _callback_name = "TextParser.UpdatePtr"
    _string_table_triggered: bool = False

    @staticmethod
    def get_ptr() -> int:
        return TextParser._ptr

    @staticmethod
    def _update_ptr():
        gc = PyPointers.PyPointers.GetGameContextPtr()
        if not gc:
            TextParser._ptr = 0
            TextParser._cached_ctx = None
            return
        gc_struct = cast(gc, POINTER(GameContextStruct)).contents
        tp_ptr = gc_struct.text_parser
        if not tp_ptr:
            TextParser._ptr = 0
            TextParser._cached_ctx = None
            return
        TextParser._ptr = tp_ptr
        TextParser._cached_ctx = cast(tp_ptr, POINTER(TextParserStruct)).contents

        if not TextParser._string_table_triggered:
            TextParser._string_table_triggered = True
            from ..internals.string_table import _do_load_string_table
            _do_load_string_table(TextParser._cached_ctx.language_id)

    @staticmethod
    def enable():
        import PyCallback
        PyCallback.PyCallback.Register(
            TextParser._callback_name,
            PyCallback.Phase.PreUpdate,
            TextParser._update_ptr,
            priority=99,
            context=PyCallback.Context.Draw,
        )

    @staticmethod
    def disable():
        import PyCallback
        PyCallback.PyCallback.RemoveByName(TextParser._callback_name)
        TextParser._ptr = 0
        TextParser._cached_ctx = None

    @staticmethod
    def get_context() -> TextParserStruct | None:
        return TextParser._cached_ctx


TextParser.enable()
