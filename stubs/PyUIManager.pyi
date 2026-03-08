from typing import List, Tuple, Sequence, Any

class UIInteractionCallback:
    def __init__(self) -> None:
        """Initialize the callback (empty constructor, defined in bindings)."""
        pass

    callback_address: int
    uictl_context: int
    h0008: int

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
    frame_layout: int
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
    field24a_0x64: int
    field24b_0x68: int
    field25_0x6c: int
    field26_0x70: int
    field27_0x74: int
    field28_0x78: int
    field29_0x7c: int
    field30_0x80: int
    field31_0x84: list[int]
    field32_0x94: int
    field33_0x98: int
    field34_0x9c: int
    field35_0xa0: int
    field36_0xa4: int
    
    field40_0xc0: int
    field41_0xc4: int
    field42_0xc8: int
    field43_0xcc: int
    field44_0xd0: int
    field45_0xd4: int

    field63_0x11c: int
    field64_0x120: int
    field65_0x124: int

    field73_0x144: int
    field74_0x148: int
    field75_0x14c: int
    field76_0x150: int
    field77_0x154: int
    field78_0x158: int
    field79_0x15c: int
    field80_0x160: int
    field81_0x164: int
    field82_0x168: int
    field83_0x16c: int
    field84_0x170: int
    field85_0x174: int
    field86_0x178: int
    field87_0x17c: int
    field88_0x180: int
    field89_0x184: int
    field90_0x188: int

    field92_0x190: int
    field93_0x194: int
    field94_0x198: int
    field95_0x19c: int
    field96_0x1a0: int
    field97_0x1a4: int
    field98_0x1a8: int

    field100_0x1b0: int
    field101_0x1b4: int
    field102_0x1b8: int
    field103_0x1bc: int
    field104_0x1c0: int
    field105_0x1c4: int

    def get_context(self) -> None: ...
    
class UIManager:
    #def __init__(self) -> None: ... 
    @staticmethod
    def get_frame_logs() -> List[Tuple[int, int, str]]: ...
    @staticmethod
    def clear_frame_logs() -> None: ...
    @staticmethod
    def get_ui_message_logs() -> List[Tuple[int, int, bool, bool, int, list[int], list[int]]]: ...
    @staticmethod
    def clear_ui_message_logs() -> None: ...
    @staticmethod
    def get_text_language() -> int: ...
    @staticmethod
    def get_frame_id_by_label(label: str) -> int: ...
    @staticmethod
    def get_frame_id_by_hash(hash: int) -> int: ...
    @staticmethod
    def get_child_frame_by_frame_id(parent_frame_id: int, child_offset: int) -> int: ...
    @staticmethod
    def get_child_frame_path_by_frame_id(parent_frame_id: int, child_offsets: List[int]) -> int: ...
    @staticmethod
    def get_parent_frame_id(frame_id: int) -> int: ...
    @staticmethod
    def get_frame_context(frame_id: int) -> int: ...
    @staticmethod
    def get_first_child_frame_id(parent_frame_id: int) -> int: ...
    @staticmethod
    def get_last_child_frame_id(parent_frame_id: int) -> int: ...
    @staticmethod
    def get_next_child_frame_id(frame_id: int) -> int: ...
    @staticmethod
    def get_prev_child_frame_id(frame_id: int) -> int: ...
    @staticmethod
    def get_item_frame_id(parent_frame_id: int, index: int) -> int: ...
    @staticmethod
    def get_tab_frame_id(parent_frame_id: int, index: int) -> int: ...
    @staticmethod
    def get_hash_by_label(label: str) -> int: ...
    @staticmethod
    def get_frame_hierarchy() -> List[Tuple[int, int, int, int]]: ...
    @staticmethod
    def get_frame_coords_by_hash(frame_hash: int) -> List[Tuple[int, int]]: ...
    @staticmethod
    def SendUIMessage(
        msgid: int,
        values: list[int],
        skip_hooks: bool = False
    ) -> bool: ...
    
    @staticmethod
    def SendUIMessageRaw(
        msgid: int,
        wparam: int,
        lparam: int,
        skip_hooks: bool = False
    ) -> bool: ...
    
    @staticmethod
    def SendFrameUIMessage(
        frame_id: int,
        message_id: int,
        wparam: int,
        lparam: int = 0
    ) -> bool: ...

    @staticmethod
    def SendFrameUIMessageWString(
        frame_id: int,
        message_id: int,
        text: str
    ) -> bool: ...

    @staticmethod
    def create_ui_component_by_frame_id(
        parent_frame_id: int,
        component_flags: int,
        child_index: int,
        event_callback: int,
        name_enc: str = ...,
        component_label: str = ...
    ) -> int: ...

    @staticmethod
    def create_ui_component_raw_by_frame_id(
        parent_frame_id: int,
        component_flags: int,
        child_index: int,
        event_callback: int,
        wparam: int = ...,
        component_label: str = ...
    ) -> int: ...

    @staticmethod
    def create_labeled_frame_by_frame_id(
        parent_frame_id: int,
        frame_flags: int,
        child_index: int,
        frame_callback: int,
        create_param: int,
        frame_label: str = ...
    ) -> int: ...

    @staticmethod
    def create_window_by_frame_id(
        parent_frame_id: int,
        child_index: int,
        frame_callback: int,
        x: float,
        y: float,
        width: float,
        height: float,
        frame_flags: int = ...,
        create_param: int = ...,
        frame_label: str = ...,
        anchor_flags: int = ...
    ) -> int: ...

    @staticmethod
    def find_available_child_slot(
        parent_frame_id: int,
        start_index: int = ...,
        end_index: int = ...
    ) -> int: ...

    @staticmethod
    def resolve_devtext_dialog_proc() -> int: ...

    @staticmethod
    def ensure_devtext_source() -> Tuple[int, bool]: ...

    @staticmethod
    def open_devtext_window() -> int: ...

    @staticmethod
    def get_devtext_frame_id() -> int: ...

    @staticmethod
    def restore_devtext_source(opened_temporarily: bool) -> None: ...

    @staticmethod
    def resolve_observed_content_host_by_frame_id(root_frame_id: int) -> int: ...

    @staticmethod
    def clear_frame_children_recursive_by_frame_id(frame_id: int) -> bool: ...

    @staticmethod
    def clear_window_contents_by_frame_id(root_frame_id: int) -> bool: ...

    @staticmethod
    def create_window(
        x: float,
        y: float,
        width: float,
        height: float,
        frame_label: str = ...,
        parent_frame_id: int = ...,
        child_index: int = ...,
        frame_flags: int = ...,
        create_param: int = ...,
        frame_callback: int = ...,
        anchor_flags: int = ...,
        ensure_devtext_source: bool = ...
    ) -> int: ...

    @staticmethod
    def create_empty_window(
        x: float,
        y: float,
        width: float,
        height: float,
        frame_label: str = ...,
        parent_frame_id: int = ...,
        child_index: int = ...,
        frame_flags: int = ...,
        create_param: int = ...,
        frame_callback: int = ...,
        anchor_flags: int = ...,
        ensure_devtext_source: bool = ...
    ) -> int: ...

    @staticmethod
    def set_frame_controller_anchor_margins_by_frame_id_ex(
        frame_id: int,
        x: float,
        y: float,
        width: float,
        height: float,
        flags: int = ...
    ) -> bool: ...

    @staticmethod
    def choose_anchor_flags_for_desired_rect(
        x: float,
        y: float,
        width: float,
        height: float,
        parent_width: float,
        parent_height: float,
        disable_center: bool = ...
    ) -> int: ...

    @staticmethod
    def collapse_window_by_frame_id(frame_id: int) -> bool: ...

    @staticmethod
    def set_frame_visible_by_frame_id(frame_id: int, is_visible: bool) -> bool: ...

    @staticmethod
    def set_frame_disabled_by_frame_id(frame_id: int, is_disabled: bool) -> bool: ...

    @staticmethod
    def set_frame_title_by_frame_id(frame_id: int, title: str) -> bool: ...

    @staticmethod
    def get_frame_label_by_frame_id(frame_id: int) -> str: ...

    @staticmethod
    def get_text_label_encoded_by_frame_id(frame_id: int) -> str: ...

    @staticmethod
    def get_text_label_encoded_bytes_by_frame_id(frame_id: int) -> bytes: ...

    @staticmethod
    def get_text_label_decoded_by_frame_id(frame_id: int) -> str: ...

    @staticmethod
    def set_label_by_frame_id(frame_id: int, label: str) -> bool: ...

    @staticmethod
    def set_text_label_by_frame_id(frame_id: int, label: str) -> bool: ...

    @staticmethod
    def set_text_label_bytes_by_frame_id(frame_id: int, label_bytes: bytes) -> bool: ...

    @staticmethod
    def append_text_label_encoded_suffix_by_frame_id(frame_id: int, encoded_suffix: str) -> bool: ...

    @staticmethod
    def append_text_label_plain_suffix_by_frame_id(frame_id: int, plain_text: str) -> bool: ...

    @staticmethod
    def set_multiline_label_by_frame_id(frame_id: int, label: str) -> bool: ...

    @staticmethod
    def set_text_label_font_by_frame_id(frame_id: int, font_id: int) -> bool: ...

    @staticmethod
    def set_read_only_by_frame_id(frame_id: int, is_read_only: bool) -> bool: ...

    @staticmethod
    def is_read_only_by_frame_id(frame_id: int) -> bool: ...

    @staticmethod
    def restore_window_rect_by_frame_id(
        frame_id: int,
        x: float,
        y: float,
        width: float,
        height: float,
        flags: int = ...,
        use_auto_flags: bool = ...,
        disable_center: bool = ...
    ) -> bool: ...

    @staticmethod
    def set_frame_margins_by_frame_id(frame_id: int, flags: int, x: float, y: float, width: float, height: float) -> bool: ...

    @staticmethod
    def set_next_created_window_title(title: str) -> bool: ...

    @staticmethod
    def clear_next_created_window_title() -> None: ...

    @staticmethod
    def has_next_created_window_title() -> bool: ...

    @staticmethod
    def is_window_title_hook_installed() -> bool: ...

    @staticmethod
    def get_last_applied_window_title_frame_id() -> int: ...

    @staticmethod
    def get_last_applied_window_title() -> str: ...

    @staticmethod
    def destroy_ui_component_by_frame_id(frame_id: int) -> bool: ...

    @staticmethod
    def add_frame_ui_interaction_callback_by_frame_id(
        frame_id: int,
        event_callback: int,
        wparam: int = ...
    ) -> bool: ...

    @staticmethod
    def trigger_frame_redraw_by_frame_id(frame_id: int) -> bool: ...

    @staticmethod
    def draw_on_compass(session_id: int, points: List[Tuple[int, int]]) -> bool: ...

    @staticmethod
    def load_settings(data: List[int]) -> None: ...

    @staticmethod
    def get_settings() -> List[int]: ...

    @staticmethod
    def get_current_tooltip_address() -> int: ...

    @staticmethod
    def create_button_frame_by_frame_id(
        parent_frame_id: int,
        component_flags: int,
        child_index: int = ...,
        name_enc: str = ...,
        component_label: str = ...
    ) -> int: ...

    @staticmethod
    def create_checkbox_frame_by_frame_id(
        parent_frame_id: int,
        component_flags: int,
        child_index: int = ...,
        name_enc: str = ...,
        component_label: str = ...
    ) -> int: ...

    @staticmethod
    def create_scrollable_frame_by_frame_id(
        parent_frame_id: int,
        component_flags: int,
        child_index: int = ...,
        page_context: int = ...,
        component_label: str = ...
    ) -> int: ...

    @staticmethod
    def create_text_label_frame_by_frame_id(
        parent_frame_id: int,
        component_flags: int,
        child_index: int = ...,
        name_enc: str = ...,
        component_label: str = ...
    ) -> int: ...

    @staticmethod
    def create_text_label_frame_with_plain_text_by_frame_id(
        parent_frame_id: int,
        component_flags: int,
        child_index: int = ...,
        plain_text: str = ...,
        component_label: str = ...
    ) -> int: ...

    @staticmethod
    def create_text_label_frame_from_template_by_frame_id(
        parent_frame_id: int,
        component_flags: int,
        child_index: int,
        template_frame_id: int,
        plain_text: str = ...,
        component_label: str = ...
    ) -> int: ...

    @staticmethod
    def get_text_label_create_payload_diagnostics_by_template_frame_id(
        template_frame_id: int,
        plain_text: str = ...
    ) -> dict: ...

    # CreateUIComponent callback binding is intentionally disabled for now.
    # @staticmethod
    # def register_create_ui_component_callback(callback, altitude: int = ...) -> int: ...

    # @staticmethod
    # def remove_create_ui_component_callback(handle: int) -> bool: ...

    @staticmethod
    def button_click(frame_id: int) -> None: ...
    @staticmethod
    def button_double_click(frame_id: int) -> None: ...
    @staticmethod
    def test_mouse_action(frame_id: int, current_state: int, wparam_value:int, lparam:int) -> None: ...
    @staticmethod
    def test_mouse_click_action(frame_id: int, current_state: int, wparam_value:int, lparam:int) -> None: ...
    @staticmethod
    def get_root_frame_id() -> int: ...
    @staticmethod
    def is_world_map_showing() -> bool: ...
    @staticmethod
    def is_ui_drawn() -> bool: ...
    @staticmethod
    def async_decode_str(enc_str: str) -> str: ...
    @staticmethod
    def is_valid_enc_str(enc_str: str) -> bool: ...
    @staticmethod
    def is_valid_enc_bytes(enc_bytes: bytes) -> bool: ...
    @staticmethod
    def uint32_to_enc_str(value: int) -> str: ...
    @staticmethod
    def enc_str_to_uint32(enc_str: str) -> int: ...
    @staticmethod
    def set_open_links(toggle: bool) -> None: ...
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
    def get_key_mappings() -> List[int]: ...
    @staticmethod
    def set_key_mappings(mappings: List[int]) -> None: ...
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
