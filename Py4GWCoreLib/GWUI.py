import ctypes
from typing import Optional

import Py4GW
import PyUIManager

from .native_src.methods.PlayerMethods import (
    CtlFrameListCreateItem_Func,
    FrameNewSubclass_Func,
)
from .Scanner import Scanner


class GWUI:
    """High-level Guild Wars UI creation and management.

    Provides convenience wrappers around PyUIManager bindings and
    native-function bridges. All native calls are enqueued on the
    game thread via Game.enqueue().
    """

    @staticmethod
    def CreateWindow(
        x: float,
        y: float,
        width: float,
        height: float,
        title: str = "",
    ) -> int:
        """Create a standalone native window from top-left content bounds in pixel space."""
        return int(
            PyUIManager.UIManager.CreateNativeWindow(
                float(x),
                float(y),
                float(width),
                float(height),
                str(title),
            )
            or 0
        )

    # ==========================================================================
    # Window Contents — Frame List + Text Items (2026-06-04)
    # ==========================================================================
    # Architecture: CContainerFrame → FrameList (child 0, type 0xAEA) → TextLabels
    # The frame list (CCtlFrameList::OnFrameMsgSize) handles vertical stacking.
    #
    # Two API layers:
    #   1. High-level — C++ bindings (create_scrollable_text_window, etc.)
    #   2. Low-level — NativeFunction bridges (CtlFrameListCreateItem_Func, etc.)
    #
    # TextLabelFrame_Callback = GWCA-resolved CtlTextProc @ EXE 0x00610c40

    # ── High-Level Convenience (C++ Bindings) ────────────────────────────

    @staticmethod
    def CreateScrollableContent(
        window_id: int,
        child_index: int = 0,
        flags: int = 0x20000,
    ) -> int:
        """Create a scrollable frame list as a child of the container window.

        Uses GWCA's CreateScrollableFrame to create a scrollable wrapper
        (CtlViewProc) containing a frame list (type 0xAEA) + scrollbars.
        """
        return int(
            PyUIManager.UIManager.create_scrollable_content_by_frame_id(
                window_id,
                child_index,
                flags,
            )
            or 0
        )

    @staticmethod
    def AddTextItem(
        frame_list_id: int,
        text: str,
        insert_index: int = 0,
        item_flags: int = 0,
    ) -> int:
        """Add a text label item to a frame list via CtlFrameListCreateItem.

        The C++ binding encodes plain text into GW's literal format
        and calls the native CtlFrameListCreateItem (msg 0x57).

        Items are auto-stacked by the frame list's layout engine.
        For manual positioning, use the low-level API with style 0x2000.
        """
        return int(
            PyUIManager.UIManager.add_text_item_to_frame_list_by_frame_id(
                frame_list_id,
                str(text),
                insert_index,
                item_flags,
            )
            or 0
        )

    @staticmethod
    def CreateScrollableWindow(
        x: float,
        y: float,
        width: float,
        height: float,
        title: str,
        items: list[str],
    ) -> int:
        """One-step: create a titled container window with scrollable text items.

        Combines CreateWindow + CreateScrollableContent + AddTextItem × N.
        Returns the window frame ID.
        """
        return int(
            PyUIManager.UIManager.create_scrollable_text_window(
                float(x),
                float(y),
                float(width),
                float(height),
                str(title),
                [str(item) for item in items],
            )
            or 0
        )

    # ── Tier 1 UI Controls: Create Functions (2026-06-04) ──────────────

    @staticmethod
    def create_dropdown(
        parent_frame_id: int,
        component_flags: int = 0x300,
        child_index: int = 0,
        component_label: str = "",
    ) -> int:
        """Create a native dropdown (combo box) frame.

        Post-create: use UIManager's add_option_by_frame_id to populate items,
        and select_option_by_frame_id / get_dropdown_value_by_frame_id to interact.
        """
        return int(
            PyUIManager.UIManager.create_dropdown_frame_by_frame_id(
                parent_frame_id,
                component_flags,
                child_index,
                str(component_label),
            )
            or 0
        )

    @staticmethod
    def create_slider(
        parent_frame_id: int,
        component_flags: int = 0,
        child_index: int = 0,
        component_label: str = "",
    ) -> int:
        """Create a native slider frame.

        Post-create: use set_slider_range_by_frame_id and
        set_slider_value_by_frame_id to configure.
        """
        return int(
            PyUIManager.UIManager.create_slider_frame_by_frame_id(
                parent_frame_id,
                component_flags,
                child_index,
                str(component_label),
            )
            or 0
        )

    @staticmethod
    def create_editable_text(
        parent_frame_id: int,
        component_flags: int = 0,
        child_index: int = 0,
        component_label: str = "",
    ) -> int:
        """Create a native editable text (edit box) frame.

        Post-create: use set_editable_text_max_length_by_frame_id and
        set_editable_text_readonly_by_frame_id to configure.
        """
        return int(
            PyUIManager.UIManager.create_editable_text_frame_by_frame_id(
                parent_frame_id,
                component_flags,
                child_index,
                str(component_label),
            )
            or 0
        )

    @staticmethod
    def create_progress_bar(
        parent_frame_id: int,
        component_flags: int = 0x300,
        child_index: int = 0,
        component_label: str = "",
    ) -> int:
        """Create a native progress bar frame.

        Post-create: use set_progress_bar_max_by_frame_id and
        set_progress_bar_style_by_frame_id to configure.
        """
        return int(
            PyUIManager.UIManager.create_progress_bar_by_frame_id(
                parent_frame_id,
                component_flags,
                child_index,
                str(component_label),
            )
            or 0
        )

    @staticmethod
    def create_tabs(
        parent_frame_id: int,
        component_flags: int = 0x40000,
        child_index: int = 0,
        component_label: str = "",
    ) -> int:
        """Create a native tabs (page) frame.

        Post-create: use add_tab_by_frame_id to populate tabs.
        """
        return int(
            PyUIManager.UIManager.create_tabs_frame_by_frame_id(
                parent_frame_id,
                component_flags,
                child_index,
                str(component_label),
            )
            or 0
        )

    # ── Low-Level NativeFunction Bridges ─────────────────────────────────

    @staticmethod
    def _encode_text_literal(plain_text: str) -> ctypes.Array:
        """Encode plain text into a GW encoded-text-literal wchar_t buffer.

        Format: <0x0108><0x0107><escaped_text><0x0001>
        Compatible with CtlTextProc::OnCreate text resolution.
        """
        escaped = plain_text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
        encoded_str = chr(0x0108) + chr(0x0107) + escaped + chr(0x0001)
        return ctypes.create_unicode_buffer(encoded_str)

    @staticmethod
    def _resolve_text_label_callback() -> int:
        """Resolve the TextLabelFrame_Callback (CtlTextProc) address."""
        addr = Scanner.FindAssertion(
            "CtlText.cpp",
            "FrameTestStyles(hdr.frameId, CTLTEXT_STYLE_MODEL)",
            0, 0,
        )
        if addr:
            return Scanner.ToFunctionStart(addr, 0xFFF)
        return 0

    @staticmethod
    def CtlFrameListCreateItem(
        frame_list_id: int,
        flags: int,
        insert_index: int,
        item_proc: int,
        encoded_text_addr: int,
    ) -> int:
        """Low-level: call CtlFrameListCreateItem (EXE 0x00612900) directly.

        Sends msg 0x57 to the frame list. Returns the new item's frame ID.
        Must be called from the game thread (use Game.enqueue wrapper).
        """
        return int(
            CtlFrameListCreateItem_Func.directCall(
                ctypes.c_uint32(frame_list_id),
                ctypes.c_uint32(flags),
                ctypes.c_uint32(insert_index),
                ctypes.c_uint32(item_proc),
                ctypes.c_uint32(encoded_text_addr),
            )
            or 0
        )

    @staticmethod
    def FrameNewSubclass(
        frame_id: int,
        subclass_proc: int,
        msg_id: int,
    ) -> int:
        """Low-level: call FrameNewSubclass (EXE 0x0062f150) directly.

        Registers a subclass proc on a frame for a given msg ID.
        Returns the subclass handle. Must be called from the game thread.
        """
        return int(
            FrameNewSubclass_Func.directCall(
                ctypes.c_uint32(frame_id),
                ctypes.c_uint32(subclass_proc),
                ctypes.c_uint32(msg_id),
            )
            or 0
        )
