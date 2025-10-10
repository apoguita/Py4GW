from typing import List, Tuple, Callable

class UIInteractionCallback:
    def __init__(self) -> None:
        """Initialize the callback (empty constructor, defined in bindings)."""
        pass

    def get_address(self) -> int:
        """Retrieve the function pointer address (stubbed in bindings)."""
        ...


    
    
class FramePosition:
    def __init__(self) -> None: ...
    
    top: int
    left: int
    bottom: int
    right: int
    content_top: int
    content_left: int
    content_bottom: int
    content_right: int
    unknown: float
    scale_factor: float
    viewport_width: float
    viewport_height: float
    screen_top: float
    screen_left: float
    screen_bottom: float
    screen_right: float
    top_on_screen: int
    left_on_screen: int
    bottom_on_screen: int
    right_on_screen: int
    width_on_screen: int
    height_on_screen: int
    viewport_scale_x: float
    viewport_scale_y: float
    
class FrameRelation:
    def __init__(self) -> None: ...
    
    parent_id: int
    field67_0x124: int
    field68_0x128: int
    frame_hash_id: int
    siblings: List[int]

class UIFrame:
    def __init__(self, frame_id: int) -> None: ...
    
    frame_id: int
    parent_id: int
    frame_hash: int
    visibility_flags: int
    type: int
    template_type: int
    position: FramePosition
    relation: FrameRelation
    frame_callbacks: List[UIInteractionCallback]
    child_offset_id : int
    is_visible: bool
    is_created: bool
    
    # All extra fields
    field1_0x0: int
    field2_0x4: int
    frame_layout: int
    field3_0xc: int
    field4_0x10: int
    field5_0x14: int
    field7_0x1c: int
    field10_0x28: int
    field11_0x2c: int
    field12_0x30: int
    field13_0x34: int
    field14_0x38: int
    field15_0x3c: int
    field16_0x40: int
    field17_0x44: int
    field18_0x48: int
    field19_0x4c: int
    field20_0x50: int
    field21_0x54: int
    field22_0x58: int
    field23_0x5c: int
    field24_0x60: int
    field25_0x64: int
    field26_0x68: int
    field27_0x6c: int
    field28_0x70: int
    field29_0x74: int
    field30_0x78: int
    field31_0x7c: List[int]
    field32_0x8c: int
    field33_0x90: int
    field34_0x94: int
    field35_0x98: int
    field36_0x9c: int
    field40_0xb8: int
    field41_0xbc: int
    field42_0xc0: int
    field43_0xc4: int
    field44_0xc8: int
    field45_0xcc: int
    field63_0x114: int
    field64_0x118: int
    field65_0x11c: int
    field73_0x13c: int
    field74_0x140: int
    field75_0x144: int
    field76_0x148: int
    field77_0x14c: int
    field78_0x150: int
    field79_0x154: int
    field80_0x158: int
    field81_0x15c: int
    field82_0x160: int
    field83_0x164: int
    field84_0x168: int
    field85_0x16c: int
    field86_0x170: int
    field87_0x174: int
    field88_0x178: int
    field89_0x17c: int
    field90_0x180: int
    field91_0x184: int
    field92_0x188: int
    field93_0x18c: int
    field94_0x190: int
    field95_0x194: int
    field96_0x198: int
    field97_0x19c: int
    field98_0x1a0: int
    field100_0x1a8: int

    def get_context(self) -> None: ...
    
class UIManager:
    #def __init__(self) -> None: ... 
    @staticmethod
    def get_frame_id_by_label(label: str) -> int: ...
    @staticmethod
    def get_frame_id_by_hash(hash: int) -> int: ...
    @staticmethod
    def get_hash_by_label(label: str) -> int: ...
    @staticmethod
    def get_frame_hierarchy() -> List[Tuple[int, int, int, int]]: ...
    @staticmethod
    def get_frame_coords_by_hash(frame_hash: int) -> List[Tuple[int, int]]: ...
    @staticmethod
    def button_click(frame_id: int) -> None: ...
    @staticmethod
    def test_mouse_action(frame_id: int, current_state: int, wparam_value:int, lparam:int) -> None: ...
    @staticmethod
    def test_mouse_click_action(frame_id: int, current_state: int, wparam_value:int, lparam:int) -> None: ...
    @staticmethod
    def get_root_frame_id() -> int: ...
    @staticmethod
    def is_world_map_showing() -> bool: ...
    @staticmethod
    def get_frame_limit() -> int: ...
    @staticmethod
    def set_frame_limit(limit: int) -> None: ...
    @staticmethod
    def get_frame_array() -> List[int]: ...
    @staticmethod
    def get_child_frame_id(parent_hash: int, child_offsets: List[int]) -> int: ...
    @staticmethod
    def get_preference_options(pref: int) -> List[int]: ...
    @staticmethod
    def get_enum_preference(pref: int) -> int: ...
    @staticmethod
    def get_int_preference(pref: int) -> int: ...
    @staticmethod
    def get_string_preference(pref: int) -> str: ...
    @staticmethod
    def get_bool_preference(pref: int) -> bool: ...
    @staticmethod
    def set_enum_preference(pref: int, value: int) -> None: ...
    @staticmethod
    def set_int_preference(pref: int, value: int) -> None: ...
    @staticmethod
    def set_string_preference(pref: int, value: str) -> None: ...
    @staticmethod
    def set_bool_preference(pref: int, value: bool) -> None: ...
    @staticmethod
    def key_down(key: int, frame_id: int) -> None: ...
    @staticmethod   
    def key_up(key: int, frame_id: int) -> None: ...
    @staticmethod   
    def key_press(key: int, frame_id: int) -> None: ...
    @staticmethod
    def get_window_position(window_id: int) -> list[int]: ...
    @staticmethod
    def is_window_visible(window_id: int) -> bool: ...
    @staticmethod
    def set_window_visible(window_id: int, is_visible: bool) -> None: ...
    @staticmethod
    def set_window_position(window_id: int, position: list[int]) -> None: ...
    @staticmethod
    def is_shift_screenshot() -> bool: ...