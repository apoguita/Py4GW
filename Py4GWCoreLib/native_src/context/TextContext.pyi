from ctypes import Structure

class TextFileSlotStruct(Structure):
    _pad0: bytes
    file_hash_ptr: int
    _pad1: int
    lang_id: int    
    start_index: int
    end_index: int
    _pad2: bytes
    
    @property
    def file_hash(self) -> str: ...
    
class LanguageSlotStruct(Structure):
    slot_array_ptr: int
    _h0004: int
    slot_count: int
    
class TextParserStruct(Structure):
    _h0000: bytes
    dec_start_ptr: int
    dec_end_ptr: int
    substitute_1: int
    substitute_2: int
    _cache_header: bytes
    language_slots: list[LanguageSlotStruct]
    _cache_pad: bytes
    entries_per_file: int
    _pad_post_cache: bytes
    h0160: int
    h0164: int
    h0168: int
    _h016C: bytes
    sub_struct_ptr: int
    _h0184: bytes
    language_id: int
    
    def get_file_slot(self, slot_idx: int, language: int = 0) -> TextFileSlotStruct | None: ...
    
class TextParser:

    @staticmethod
    def get_ptr() -> int:...   
    @staticmethod
    def _update_ptr():...
    @staticmethod
    def enable():...
    @staticmethod
    def disable():...
    @staticmethod
    def get_context(): ...