import PyUIManager
from typing import Optional


class GWUI:
    _LIVE_CREATE_ENCODED_TEXT_FN = None
    _LIVE_SET_FRAME_TEXT_FN = None
    _STATIC_UI_DEVTEXT_DIALOG_PROC = 0x00864170
    _STATIC_UI_SET_FRAME_TEXT = 0x00610B00
    _DEVTEXT_USE_SCAN_AHEAD = 0x40

    #region LowLevel
    @staticmethod
    def CreateUIComponentByFrameId(
        parent_frame_id: int,
        component_flags: int,
        child_index: int,
        event_callback: int,
        name_enc: str = "",
        component_label: str = "",
    ) -> int:
        return PyUIManager.UIManager.create_ui_component_by_frame_id(
            parent_frame_id,
            component_flags,
            child_index,
            event_callback,
            name_enc,
            component_label,
        )

    @staticmethod
    def CreateUIComponentRawByFrameId(
        parent_frame_id: int,
        component_flags: int,
        child_index: int,
        event_callback: int,
        wparam: int = 0,
        component_label: str = "",
    ) -> int:
        return PyUIManager.UIManager.create_ui_component_raw_by_frame_id(
            parent_frame_id,
            component_flags,
            child_index,
            event_callback,
            wparam,
            component_label,
        )

    @staticmethod
    def CreateLabeledFrameByFrameId(
        parent_frame_id: int,
        frame_flags: int,
        child_index: int,
        frame_callback: int,
        create_param: int,
        frame_label: str = "",
    ) -> int:
        return PyUIManager.UIManager.create_labeled_frame_by_frame_id(
            parent_frame_id,
            frame_flags,
            child_index,
            frame_callback,
            create_param,
            frame_label,
        )

    @staticmethod
    def FindAvailableChildSlot(
        parent_frame_id: int,
        start_index: int = 0x20,
        end_index: int = 0xFE,
    ) -> int:
        return int(
            PyUIManager.UIManager.find_available_child_slot(
                parent_frame_id,
                start_index,
                end_index,
            )
            or 0
        )

    @staticmethod
    def DestroyUIComponentByFrameId(frame_id: int) -> bool:
        return bool(PyUIManager.UIManager.destroy_ui_component_by_frame_id(frame_id))

    @staticmethod
    def TriggerFrameRedrawByFrameId(frame_id: int) -> bool:
        return bool(PyUIManager.UIManager.trigger_frame_redraw_by_frame_id(frame_id))

    @staticmethod
    def GetFrameInteractionCallbacksByFrameId(frame_id: int) -> list[tuple[int, int]]:
        from Py4GWCoreLib import UIManager

        callbacks: list[tuple[int, int]] = []
        if frame_id <= 0:
            return callbacks
        try:
            frame = UIManager.GetFrameByID(frame_id)
        except Exception:
            return callbacks

        for callback in getattr(frame, "frame_callbacks", []):
            callback_address = int(getattr(callback, "callback_address", 0) or 0)
            callback_h0008 = int(getattr(callback, "h0008", 0) or 0)
            if callback_address > 0:
                callbacks.append((callback_address, callback_h0008))
        return callbacks

    @staticmethod
    def AddFrameUIInteractionCallbackByFrameId(
        frame_id: int,
        event_callback: int,
        wparam: int = 0,
    ) -> bool:
        return bool(
            PyUIManager.UIManager.add_frame_ui_interaction_callback_by_frame_id(
                frame_id,
                event_callback,
                wparam,
            )
        )

    @staticmethod
    def AddFrameUIInteractionCallbacksByFrameId(
        frame_id: int,
        callbacks: list[tuple[int, int]],
        start_index: int = 0,
    ) -> int:
        if frame_id <= 0:
            return 0

        added = 0
        for callback_address, callback_h0008 in callbacks[max(0, int(start_index)):]:
            if callback_address <= 0:
                continue
            if GWUI.AddFrameUIInteractionCallbackByFrameId(
                frame_id,
                callback_address,
                callback_h0008,
            ):
                added += 1
        return added

    @staticmethod
    def CreateUIComponentFromSourceFrameByFrameId(
        parent_frame_id: int,
        source_frame_id: int,
        component_flags: int,
        child_index: int,
        component_label: str = "",
        reattach_remaining_callbacks: bool = True,
        trigger_redraw: bool = True,
    ) -> int:
        callbacks = GWUI.GetFrameInteractionCallbacksByFrameId(source_frame_id)
        if parent_frame_id <= 0 or not callbacks:
            return 0

        primary_callback, primary_h0008 = callbacks[0]
        created_frame_id = int(
            GWUI.CreateUIComponentRawByFrameId(
                parent_frame_id,
                component_flags,
                child_index,
                primary_callback,
                primary_h0008,
                component_label,
            )
            or 0
        )
        if created_frame_id <= 0:
            return 0

        if reattach_remaining_callbacks and len(callbacks) > 1:
            GWUI.AddFrameUIInteractionCallbacksByFrameId(
                created_frame_id,
                callbacks,
                start_index=1,
            )

        if trigger_redraw:
            GWUI.TriggerFrameRedrawByFrameId(created_frame_id)

        return created_frame_id

    #region WindowState
    @staticmethod
    def HideWindowByLabel(frame_label: str) -> bool:
        from Py4GWCoreLib import UIManager

        frame_id = int(UIManager.GetFrameIDByLabel(frame_label) or 0)
        if frame_id <= 0 or not UIManager.FrameExists(frame_id):
            return False
        return GWUI.DestroyUIComponentByFrameId(frame_id)

    @staticmethod
    def CollapseWindowByFrameId(frame_id: int) -> bool:
        return bool(PyUIManager.UIManager.collapse_window_by_frame_id(frame_id))

    @staticmethod
    def SetFrameVisibleByFrameId(frame_id: int, is_visible: bool) -> bool:
        return bool(PyUIManager.UIManager.set_frame_visible_by_frame_id(frame_id, is_visible))

    @staticmethod
    def SetFrameDisabledByFrameId(frame_id: int, is_disabled: bool) -> bool:
        return bool(PyUIManager.UIManager.set_frame_disabled_by_frame_id(frame_id, is_disabled))

    @staticmethod
    def RestoreWindowRectByFrameId(
        frame_id: int,
        x: float,
        y: float,
        width: float,
        height: float,
        flags: int = 0,
        use_auto_flags: bool = True,
        disable_center: bool = True,
    ) -> bool:
        return bool(
            PyUIManager.UIManager.restore_window_rect_by_frame_id(
                frame_id,
                x,
                y,
                width,
                height,
                flags,
                use_auto_flags,
                disable_center,
            )
        )

    @staticmethod
    def SetFrameMarginsByFrameId(
        frame_id: int,
        flags: int,
        x: float,
        y: float,
        width: float,
        height: float,
    ) -> bool:
        return bool(
            PyUIManager.UIManager.set_frame_margins_by_frame_id(
                frame_id,
                flags,
                x,
                y,
                width,
                height,
            )
        )

    @staticmethod
    def ToggleWindowByLabel(
        frame_label: str,
        x: float,
        y: float,
        width: float,
        height: float,
        parent_frame_id: int = 9,
        child_index: int = 0,
        frame_flags: int = 0,
        create_param: int = 0,
        frame_callback: int = 0,
        anchor_flags: int = 0x6,
        ensure_devtext_source: bool = True,
    ) -> int:
        from Py4GWCoreLib import UIManager

        frame_id = int(UIManager.GetFrameIDByLabel(frame_label) or 0)
        if frame_id > 0 and UIManager.FrameExists(frame_id):
            GWUI.DestroyUIComponentByFrameId(frame_id)
            return 0
        return GWUI.CreateWindow(
            x,
            y,
            width,
            height,
            frame_label,
            parent_frame_id,
            child_index,
            frame_flags,
            create_param,
            frame_callback,
            anchor_flags,
            ensure_devtext_source,
        )

    #region FrameText
    @staticmethod
    def SetWindowTitle(frame_id: int, title: str) -> bool:
        from Py4GW import Game

        frame_id = int(frame_id or 0)
        title = str(title or "")
        if frame_id <= 0 or not title:
            return False

        if bool(PyUIManager.UIManager.set_frame_title_by_frame_id(frame_id, title)):
            return True

        create_text_fn = GWUI._get_live_create_encoded_text_fn()
        set_frame_text_fn = GWUI._get_live_set_frame_text_fn()
        if not (create_text_fn and set_frame_text_fn):
            return False

        def _invoke() -> None:
            encoded_text_ptr = int(create_text_fn.directCall(8, 7, title, 0) or 0)
            if encoded_text_ptr <= 0:
                return
            set_frame_text_fn.directCall(frame_id, encoded_text_ptr)
            GWUI.TriggerFrameRedrawByFrameId(frame_id)

        Game.enqueue(_invoke)
        return True

    @staticmethod
    def SetFrameTitleByFrameId(frame_id: int, title: str) -> bool:
        return GWUI.SetWindowTitle(frame_id, title)

    @staticmethod
    def GetFrameLabelByFrameId(frame_id: int) -> str:
        return str(PyUIManager.UIManager.get_frame_label_by_frame_id(frame_id) or "")

    @staticmethod
    def GetTextLabelEncodedByFrameId(frame_id: int) -> str:
        return str(PyUIManager.UIManager.get_text_label_encoded_by_frame_id(frame_id) or "")

    @staticmethod
    def GetTextLabelEncodedBytesByFrameId(frame_id: int) -> bytes:
        return bytes(PyUIManager.UIManager.get_text_label_encoded_bytes_by_frame_id(frame_id) or b"")

    @staticmethod
    def GetTextLabelDecodedByFrameId(frame_id: int) -> str:
        return str(PyUIManager.UIManager.get_text_label_decoded_by_frame_id(frame_id) or "")

    @staticmethod
    def SetLabelByFrameId(frame_id: int, label: str) -> bool:
        return bool(PyUIManager.UIManager.set_label_by_frame_id(frame_id, str(label or "")))

    @staticmethod
    def SetTextLabelByFrameId(frame_id: int, label: str) -> bool:
        return bool(PyUIManager.UIManager.set_text_label_by_frame_id(frame_id, str(label or "")))

    @staticmethod
    def SetTextLabelBytesByFrameId(frame_id: int, label_bytes: bytes) -> bool:
        return bool(PyUIManager.UIManager.set_text_label_bytes_by_frame_id(frame_id, bytes(label_bytes or b"")))

    @staticmethod
    def AppendTextLabelEncodedSuffixByFrameId(frame_id: int, encoded_suffix: str) -> bool:
        return bool(
            PyUIManager.UIManager.append_text_label_encoded_suffix_by_frame_id(
                frame_id,
                str(encoded_suffix or ""),
            )
        )

    @staticmethod
    def AppendTextLabelPlainSuffixByFrameId(frame_id: int, plain_text: str) -> bool:
        return bool(
            PyUIManager.UIManager.append_text_label_plain_suffix_by_frame_id(
                frame_id,
                str(plain_text or ""),
            )
        )

    @staticmethod
    def _read_u8(address: int) -> int:
        import ctypes

        return int(ctypes.c_ubyte.from_address(address).value)

    @staticmethod
    def _read_i32(address: int) -> int:
        import ctypes

        return int(ctypes.c_int32.from_address(address).value)

    @staticmethod
    def _resolve_relative_call_target(call_addr: int) -> int:
        if call_addr <= 0:
            return 0
        try:
            if GWUI._read_u8(call_addr) != 0xE8:
                return 0
            rel = GWUI._read_i32(call_addr + 1)
            return int(call_addr + 5 + rel)
        except (ValueError, OSError):
            return 0

    @staticmethod
    def _get_live_create_encoded_text_fn():
        from Py4GWCoreLib.native_src.internals.native_function import NativeFunction, ScannerSection
        from Py4GWCoreLib.native_src.internals.prototypes import NativeFunctionPrototype
        import ctypes

        if GWUI._LIVE_CREATE_ENCODED_TEXT_FN is not None:
            return GWUI._LIVE_CREATE_ENCODED_TEXT_FN if GWUI._LIVE_CREATE_ENCODED_TEXT_FN.is_valid() else None

        create_proto = NativeFunctionPrototype(
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_wchar_p,
            ctypes.c_uint32,
        )
        GWUI._LIVE_CREATE_ENCODED_TEXT_FN = NativeFunction(
            name="Ui_CreateEncodedText",
            pattern=(
                b"\x55\x8B\xEC\x51\x56\x57\xE8\x00\x00\x00\x00\x8B\x48\x18"
                b"\xE8\x00\x00\x00\x00\x8B\xF8"
            ),
            mask="xxxxxxx????xxxx????xx",
            offset=0,
            section=ScannerSection.TEXT,
            prototype=create_proto,
            use_near_call=False,
            report_success=False,
        )
        return GWUI._LIVE_CREATE_ENCODED_TEXT_FN if GWUI._LIVE_CREATE_ENCODED_TEXT_FN.is_valid() else None

    @staticmethod
    def _get_live_set_frame_text_fn():
        from Py4GWCoreLib import Scanner
        from Py4GWCoreLib.native_src.internals.native_function import NativeFunction
        from Py4GWCoreLib.native_src.internals.prototypes import Prototypes

        if GWUI._LIVE_SET_FRAME_TEXT_FN is not None:
            return GWUI._LIVE_SET_FRAME_TEXT_FN if GWUI._LIVE_SET_FRAME_TEXT_FN.is_valid() else None

        create_text_fn = GWUI._get_live_create_encoded_text_fn()
        if not create_text_fn:
            return None

        try:
            use_addr = int(Scanner.FindNthUseOfStringW("DlgDevText", 0, 0, 0) or 0)
        except Exception:
            use_addr = 0
        if use_addr <= 0:
            return None

        try:
            proc_addr = int(Scanner.ToFunctionStart(use_addr, 0x1200) or 0)
        except Exception:
            proc_addr = 0
        if proc_addr <= 0:
            return None

        runtime_slide = int(proc_addr - GWUI._STATIC_UI_DEVTEXT_DIALOG_PROC)
        expected_called = int(GWUI._STATIC_UI_SET_FRAME_TEXT + runtime_slide + 0x30)
        create_addr = int(create_text_fn.get_address() or 0)

        seen_create = False
        for addr in range(use_addr, use_addr + GWUI._DEVTEXT_USE_SCAN_AHEAD):
            target = GWUI._resolve_relative_call_target(addr)
            if target <= 0:
                continue
            if target == create_addr:
                seen_create = True
                continue
            if seen_create and target == expected_called:
                GWUI._LIVE_SET_FRAME_TEXT_FN = NativeFunction.from_address(
                    "Ui_SetFrameText_Live",
                    target,
                    Prototypes["Void_U32_U32"],
                    report_success=False,
                )
                return GWUI._LIVE_SET_FRAME_TEXT_FN

        for addr in range(use_addr, use_addr + GWUI._DEVTEXT_USE_SCAN_AHEAD):
            target = GWUI._resolve_relative_call_target(addr)
            if target == expected_called:
                GWUI._LIVE_SET_FRAME_TEXT_FN = NativeFunction.from_address(
                    "Ui_SetFrameText_Live",
                    target,
                    Prototypes["Void_U32_U32"],
                    report_success=False,
                )
                return GWUI._LIVE_SET_FRAME_TEXT_FN
        return None

    @staticmethod
    def SetMultilineLabelByFrameId(frame_id: int, label: str) -> bool:
        return bool(PyUIManager.UIManager.set_multiline_label_by_frame_id(frame_id, str(label or "")))

    @staticmethod
    def SetTextLabelFontByFrameId(frame_id: int, font_id: int) -> bool:
        return bool(PyUIManager.UIManager.set_text_label_font_by_frame_id(frame_id, int(font_id)))

    @staticmethod
    def SetReadOnlyByFrameId(frame_id: int, is_read_only: bool) -> bool:
        return bool(PyUIManager.UIManager.set_read_only_by_frame_id(frame_id, is_read_only))

    @staticmethod
    def IsReadOnlyByFrameId(frame_id: int) -> bool:
        return bool(PyUIManager.UIManager.is_read_only_by_frame_id(frame_id))

    #region WindowTitleHooks
    @staticmethod
    def SetNextCreatedWindowTitle(title: str) -> bool:
        return bool(PyUIManager.UIManager.set_next_created_window_title(str(title or "")))

    @staticmethod
    def ClearNextCreatedWindowTitle() -> None:
        PyUIManager.UIManager.clear_next_created_window_title()

    @staticmethod
    def HasNextCreatedWindowTitle() -> bool:
        return bool(PyUIManager.UIManager.has_next_created_window_title())

    @staticmethod
    def IsWindowTitleHookInstalled() -> bool:
        return bool(PyUIManager.UIManager.is_window_title_hook_installed())

    @staticmethod
    def GetLastAppliedWindowTitleFrameId() -> int:
        return int(PyUIManager.UIManager.get_last_applied_window_title_frame_id() or 0)

    @staticmethod
    def GetLastAppliedWindowTitle() -> str:
        return str(PyUIManager.UIManager.get_last_applied_window_title() or "")

    #region Factory
    @staticmethod
    def CreateButtonFrameByFrameId(
        parent_frame_id: int,
        component_flags: int,
        child_index: int = 0,
        name_enc: str = "",
        component_label: str = "",
    ) -> int:
        return int(
            PyUIManager.UIManager.create_button_frame_by_frame_id(
                parent_frame_id,
                component_flags,
                child_index,
                name_enc,
                component_label,
            )
            or 0
        )

    @staticmethod
    def CreateCheckboxFrameByFrameId(
        parent_frame_id: int,
        component_flags: int,
        child_index: int = 0,
        name_enc: str = "",
        component_label: str = "",
    ) -> int:
        return int(
            PyUIManager.UIManager.create_checkbox_frame_by_frame_id(
                parent_frame_id,
                component_flags,
                child_index,
                name_enc,
                component_label,
            )
            or 0
        )

    @staticmethod
    def CreateScrollableFrameByFrameId(
        parent_frame_id: int,
        component_flags: int,
        child_index: int = 0,
        page_context: int = 0,
        component_label: str = "",
    ) -> int:
        return int(
            PyUIManager.UIManager.create_scrollable_frame_by_frame_id(
                parent_frame_id,
                component_flags,
                child_index,
                page_context,
                component_label,
            )
            or 0
        )

    @staticmethod
    def CreateTextLabelFrameByFrameId(
        parent_frame_id: int,
        component_flags: int,
        child_index: int = 0,
        name_enc: str = "",
        component_label: str = "",
    ) -> int:
        return int(
            PyUIManager.UIManager.create_text_label_frame_by_frame_id(
                parent_frame_id,
                component_flags,
                child_index,
                name_enc,
                component_label,
            )
            or 0
        )

    @staticmethod
    def CreateTextLabelFrameWithPlainTextByFrameId(
        parent_frame_id: int,
        component_flags: int,
        child_index: int = 0,
        plain_text: str = "",
        component_label: str = "",
    ) -> int:
        return int(
            PyUIManager.UIManager.create_text_label_frame_with_plain_text_by_frame_id(
                parent_frame_id,
                component_flags,
                child_index,
                plain_text,
                component_label,
            )
            or 0
        )

    @staticmethod
    def CreateTextLabelFrameFromTemplateByFrameId(
        parent_frame_id: int,
        component_flags: int,
        child_index: int,
        template_frame_id: int,
        plain_text: str = "",
        component_label: str = "",
    ) -> int:
        return int(
            PyUIManager.UIManager.create_text_label_frame_from_template_by_frame_id(
                parent_frame_id,
                component_flags,
                child_index,
                template_frame_id,
                plain_text,
                component_label,
            )
            or 0
        )

    @staticmethod
    def GetTextLabelCreatePayloadDiagnosticsByTemplateFrameId(
        template_frame_id: int,
        plain_text: str = "",
    ) -> dict:
        return dict(
            PyUIManager.UIManager.get_text_label_create_payload_diagnostics_by_template_frame_id(
                template_frame_id,
                plain_text,
            )
            or {}
        )

    @staticmethod
    def GetTextLabelLiteralCreatePayloadDiagnostics(
        plain_text: str = "",
    ) -> dict:
        return dict(
            PyUIManager.UIManager.get_text_label_literal_create_payload_diagnostics(
                plain_text,
            )
            or {}
        )

    # CreateUIComponent callback binding is intentionally disabled for now.
    # The runtime path was destabilizing validation runs and should only be
    # restored when callback-specific work is resumed.
    #
    # @staticmethod
    # def RegisterCreateUIComponentCallback(callback, altitude: int = -0x8000) -> int:
    #     return int(PyUIManager.UIManager.register_create_ui_component_callback(callback, altitude) or 0)
    #
    # @staticmethod
    # def RemoveCreateUIComponentCallback(handle: int) -> bool:
    #     return bool(PyUIManager.UIManager.remove_create_ui_component_callback(handle))

    #region DevText
    @staticmethod
    def GetDevTextFrameID() -> int:
        from Py4GWCoreLib import UIManager

        frame_id = int(PyUIManager.UIManager.get_devtext_frame_id() or 0)
        if frame_id > 0:
            return frame_id
        frame_id = int(UIManager.GetFrameIDByLabel("DevText") or 0)
        if frame_id <= 0:
            return 0
        try:
            frame = UIManager.GetFrameByID(frame_id)
            if bool(frame.is_created):
                return frame_id
        except Exception:
            pass
        return 0

    @staticmethod
    def ResolveDevTextDialogProc() -> int:
        return int(PyUIManager.UIManager.resolve_devtext_dialog_proc() or 0)

    @staticmethod
    def OpenDevTextWindow(timeout_ms: int = 750, poll_interval_ms: int = 25) -> int:
        import time
        from Py4GW import Game
        from Py4GWCoreLib import GWContext

        frame_id = GWUI.GetDevTextFrameID()
        if frame_id > 0:
            return frame_id

        def _dispatch_open_devtext() -> None:
            char_ctx = GWContext.Char.GetContext()
            if char_ctx is None:
                return
            original_flags = int(char_ctx.player_flags)
            try:
                char_ctx.player_flags = original_flags | 0x8
                PyUIManager.UIManager.key_press(0x25, 0)
            finally:
                char_ctx.player_flags = original_flags

        Game.enqueue(_dispatch_open_devtext)

        deadline = time.monotonic() + max(0.0, float(timeout_ms) / 1000.0)
        poll_seconds = max(0.005, float(poll_interval_ms) / 1000.0)
        while time.monotonic() <= deadline:
            frame_id = GWUI.GetDevTextFrameID()
            if frame_id > 0:
                return frame_id
            time.sleep(poll_seconds)
        return 0

    @staticmethod
    def EnsureDevTextSource() -> tuple[int, bool]:
        frame_id = GWUI.GetDevTextFrameID()
        if frame_id > 0:
            return frame_id, False
        frame_id = GWUI.OpenDevTextWindow()
        return frame_id, frame_id > 0

    @staticmethod
    def ResolveObservedContentHostByFrameId(root_frame_id: int) -> int:
        return int(PyUIManager.UIManager.resolve_observed_content_host_by_frame_id(root_frame_id) or 0)

    @staticmethod
    def ResolveWindowContentFrameByFrameId(root_frame_id: int) -> int:
        from Py4GWCoreLib import UIManager

        root_frame_id = int(root_frame_id or 0)
        if root_frame_id <= 0:
            return 0
        return int(UIManager.GetChildFrameByFrameId(root_frame_id, 0) or 0)

    @staticmethod
    def ResolveWindowScrollableFrameByFrameId(root_frame_id: int) -> int:
        from Py4GWCoreLib import UIManager

        content_frame_id = GWUI.ResolveWindowContentFrameByFrameId(root_frame_id)
        if content_frame_id <= 0:
            return 0
        return int(UIManager.GetChildFrameByFrameId(content_frame_id, 0) or 0)

    @staticmethod
    def ResolveEmptyWindowClearBoundaryByFrameId(
        root_frame_id: int,
        timeout_ms: int = 250,
        poll_interval_ms: int = 10,
    ) -> int:
        import time
        from Py4GWCoreLib import UIManager

        if root_frame_id <= 0:
            return 0
        deadline = time.monotonic() + max(0.0, float(timeout_ms) / 1000.0)
        poll_seconds = max(0.005, float(poll_interval_ms) / 1000.0)
        while time.monotonic() <= deadline:
            level0 = int(UIManager.GetChildFrameByFrameId(root_frame_id, 0) or 0)
            if level0 > 0:
                level1 = int(UIManager.GetChildFrameByFrameId(level0, 0) or 0)
                if level1 > 0:
                    return level1
            time.sleep(poll_seconds)
        return 0

    @staticmethod
    def ClearFrameChildrenRecursiveByFrameId(frame_id: int) -> bool:
        return bool(PyUIManager.UIManager.clear_frame_children_recursive_by_frame_id(frame_id))

    @staticmethod
    def ClearWindowContentsByFrameId(root_frame_id: int) -> bool:
        clear_boundary = GWUI.ResolveEmptyWindowClearBoundaryByFrameId(root_frame_id)
        if clear_boundary <= 0:
            return False
        result = GWUI.ClearFrameChildrenRecursiveByFrameId(clear_boundary)
        if result:
            GWUI.TriggerFrameRedrawByFrameId(root_frame_id)
        return result

    @staticmethod
    def ClearWindowLeafContentsByFrameId(root_frame_id: int) -> bool:
        scrollable_frame_id = GWUI.ResolveWindowScrollableFrameByFrameId(root_frame_id)
        if scrollable_frame_id <= 0:
            return False
        result = GWUI.ClearFrameChildrenRecursiveByFrameId(scrollable_frame_id)
        if result:
            GWUI.TriggerFrameRedrawByFrameId(root_frame_id)
        return result

    #region Interaction
    @staticmethod
    def FrameClick(frame_id: int) -> None:
        from Py4GWCoreLib import UIManager
        UIManager.FrameClick(frame_id)

    @staticmethod
    def TestMouseAction(
        frame_id: int,
        current_state: int,
        wparam_value: int,
        lparam_value: int = 0,
    ) -> None:
        from Py4GWCoreLib import UIManager
        UIManager.TestMouseAction(frame_id, current_state, wparam_value, lparam_value)

        
    @staticmethod
    def TestMouseClickAction(
        frame_id: int,
        current_state: int,
        wparam_value: int,
        lparam_value: int = 0,
    ) -> None:
        from Py4GWCoreLib import UIManager
        UIManager.TestMouseClickAction(frame_id, current_state, wparam_value, lparam_value)
        
    #region Rects
    @staticmethod
    def SetFrameControllerAnchorMarginsByFrameIdEx(
        frame_id: int,
        x: float,
        y: float,
        width: float,
        height: float,
        flags: int = 0x6,
    ) -> bool:
        return bool(
            PyUIManager.UIManager.set_frame_controller_anchor_margins_by_frame_id_ex(
                frame_id,
                x,
                y,
                width,
                height,
                flags,
            )
        )

    @staticmethod
    def QueueFrameControllerUpdateByFrameId(frame_id: int) -> bool:
        return bool(PyUIManager.UIManager.queue_frame_controller_update_by_frame_id(frame_id))

    @staticmethod
    def ProcessFrameControllerUpdateByFrameId(frame_id: int) -> bool:
        return bool(PyUIManager.UIManager.process_frame_controller_update_by_frame_id(frame_id))

    @staticmethod
    def FlushFrameControllerUpdateByFrameId(frame_id: int) -> bool:
        queued = GWUI.QueueFrameControllerUpdateByFrameId(frame_id)
        processed = GWUI.ProcessFrameControllerUpdateByFrameId(frame_id)
        return bool(queued and processed)

    @staticmethod
    def ChooseAnchorFlagsForDesiredRect(
        x: float,
        y: float,
        width: float,
        height: float,
        parent_width: float,
        parent_height: float,
        disable_center: bool = False,
    ) -> int:
        return int(
            PyUIManager.UIManager.choose_anchor_flags_for_desired_rect(
                x,
                y,
                width,
                height,
                parent_width,
                parent_height,
                disable_center,
            )
            or 0
        )

    @staticmethod
    def SetFrameRect(
        frame_id: int,
        x: float,
        y: float,
        width: float,
        height: float,
        flags: Optional[int] = 0x6,
        disable_center: bool = False,
    ) -> bool:
        from Py4GWCoreLib import UIManager

        resolved_flags = flags
        if resolved_flags is None:
            parent_id = UIManager.GetParentID(frame_id)
            if parent_id <= 0:
                resolved_flags = 0x6
            else:
                left, top, right, bottom = UIManager.GetFrameCoords(parent_id)
                parent_width = abs(float(right - left))
                parent_height = abs(float(bottom - top))
                resolved_flags = GWUI.ChooseAnchorFlagsForDesiredRect(
                    float(x),
                    float(y),
                    float(width),
                    float(height),
                    parent_width,
                    parent_height,
                    disable_center,
                )
        return GWUI.SetFrameControllerAnchorMarginsByFrameIdEx(
            frame_id,
            float(x),
            float(y),
            float(width),
            float(height),
            int(resolved_flags),
        )

    @staticmethod
    def ApplyRect(
        frame_id: int,
        x: float,
        y: float,
        width: float,
        height: float,
        flags: Optional[int] = 0x6,
        disable_center: bool = False,
    ) -> bool:
        applied = GWUI.SetFrameRect(
            frame_id,
            x,
            y,
            width,
            height,
            flags,
            disable_center,
        )
        if not applied:
            return False
        GWUI.FlushFrameControllerUpdateByFrameId(frame_id)
        return True

    @staticmethod
    def ResizeRect(
        frame_id: int,
        width: float,
        height: float,
        x: Optional[float] = None,
        y: Optional[float] = None,
        flags: Optional[int] = 0x6,
        disable_center: bool = False,
    ) -> bool:
        from Py4GWCoreLib import UIManager

        if x is None or y is None:
            left, top, _, _ = UIManager.GetFrameCoords(frame_id)
            if x is None:
                x = float(left)
            if y is None:
                y = float(top)
        return GWUI.ApplyRect(
            frame_id,
            float(x),
            float(y),
            width,
            height,
            flags,
            disable_center,
        )

    @staticmethod
    def SetFrameSize(
        frame_id: int,
        width: float,
        height: float,
        flags: Optional[int] = 0x6,
        disable_center: bool = False,
    ) -> bool:
        return GWUI.ResizeRect(
            frame_id,
            float(width),
            float(height),
            None,
            None,
            flags,
            disable_center,
        )

    @staticmethod
    def MoveRect(
        frame_id: int,
        x: float,
        y: float,
        width: Optional[float] = None,
        height: Optional[float] = None,
        flags: Optional[int] = 0x6,
        disable_center: bool = False,
    ) -> bool:
        from Py4GWCoreLib import UIManager

        if width is None or height is None:
            left, top, right, bottom = UIManager.GetFrameCoords(frame_id)
            if width is None:
                width = abs(float(right - left))
            if height is None:
                height = abs(float(bottom - top))
        return GWUI.ApplyRect(
            frame_id,
            x,
            y,
            float(width),
            float(height),
            flags,
            disable_center,
        )

    @staticmethod
    def SetFramePosition(
        frame_id: int,
        x: float,
        y: float,
        flags: Optional[int] = 0x6,
        disable_center: bool = False,
    ) -> bool:
        return GWUI.MoveRect(
            frame_id,
            float(x),
            float(y),
            flags=flags,
            disable_center=disable_center,
        )

    #region Windows
    @staticmethod
    def CloneWindow(
        parent_frame_id: int,
        frame_callback: int,
        frame_flags: int = 0,
        child_index: int = 0,
        create_param: int = 0,
        frame_label: str = "",
    ) -> int:
        resolved_child_index = child_index if child_index > 0 else GWUI.FindAvailableChildSlot(parent_frame_id)
        if resolved_child_index <= 0:
            return 0
        return GWUI.CreateLabeledFrameByFrameId(
            parent_frame_id,
            frame_flags,
            resolved_child_index,
            frame_callback,
            create_param,
            frame_label,
        )

    @staticmethod
    def CreateWindowClone(
        x: float,
        y: float,
        width: float,
        height: float,
        frame_label: str = "",
        parent_frame_id: int = 9,
        child_index: int = 0,
        frame_flags: int = 0,
        create_param: int = 0,
        frame_callback: int = 0,
        anchor_flags: int = 0x6,
        ensure_devtext_source: bool = True,
    ) -> int:
        return int(
            PyUIManager.UIManager.create_window(
                x,
                y,
                width,
                height,
                frame_label,
                parent_frame_id,
                child_index,
                frame_flags,
                create_param,
                frame_callback,
                anchor_flags,
                ensure_devtext_source,
            )
            or 0
        )

    @staticmethod
    def CreateWindow(
        x: float,
        y: float,
        width: float,
        height: float,
        frame_label: str = "",
        parent_frame_id: int = 9,
        child_index: int = 0,
        frame_flags: int = 0,
        create_param: int = 0,
        frame_callback: int = 0,
        anchor_flags: int = 0x6,
        ensure_devtext_source: bool = True,
        window_title: str = "",
    ) -> int:
        root_frame_id = GWUI.CreateWindowClone(
            x,
            y,
            width,
            height,
            frame_label,
            parent_frame_id,
            child_index,
            frame_flags,
            create_param,
            frame_callback,
            anchor_flags,
            ensure_devtext_source,
        )
        if root_frame_id <= 0:
            return 0
        GWUI.ClearWindowContentsByFrameId(root_frame_id)
        if str(window_title or ""):
            GWUI.SetWindowTitle(root_frame_id, str(window_title))
        return root_frame_id

    @staticmethod
    def CreateEmptyWindow(
        x: float,
        y: float,
        width: float,
        height: float,
        frame_label: str = "",
        parent_frame_id: int = 9,
        child_index: int = 0,
        frame_flags: int = 0,
        create_param: int = 0,
        frame_callback: int = 0,
        anchor_flags: int = 0x6,
        ensure_devtext_source: bool = True,
        window_title: str = "",
    ) -> int:
        return GWUI.CreateWindow(
            x,
            y,
            width,
            height,
            frame_label,
            parent_frame_id,
            child_index,
            frame_flags,
            create_param,
            frame_callback,
            anchor_flags,
            ensure_devtext_source,
            window_title,
        )

    @staticmethod
    def CreateNativeWindow(
        x: float,
        y: float,
        width: float,
        height: float,
        frame_label: str = "",
        parent_frame_id: int = 9,
        child_index: int = 0,
        frame_flags: int = 0,
        create_param: int = 0,
        frame_callback: int = 0,
        anchor_flags: int = 0x6,
        ensure_devtext_source: bool = True,
        window_title: str = "",
    ) -> int:
        return GWUI.CreateWindow(
            x,
            y,
            width,
            height,
            frame_label,
            parent_frame_id,
            child_index,
            frame_flags,
            create_param,
            frame_callback,
            anchor_flags,
            ensure_devtext_source,
            window_title,
        )

    @staticmethod
    def SetNativeWindowTitleByFrameId(frame_id: int, title: str) -> bool:
        return GWUI.SetWindowTitle(frame_id, title)

    @staticmethod
    def CreateTextLabel(
        parent_frame_id: int,
        plain_text: str,
        component_label: str = "",
        child_index: int = 0,
        component_flags: int = 0x300,
    ) -> int:
        resolved_child_index = int(child_index or 0)
        if resolved_child_index <= 0:
            resolved_child_index = GWUI.FindAvailableChildSlot(parent_frame_id, 0x20, 0xFE)
        if parent_frame_id <= 0 or resolved_child_index <= 0:
            return 0
        frame_id = GWUI.CreateTextLabelFrameWithPlainTextByFrameId(
            parent_frame_id,
            component_flags,
            resolved_child_index,
            plain_text,
            component_label,
        )
        if frame_id > 0:
            GWUI.FlushFrameControllerUpdateByFrameId(frame_id)
            GWUI.FlushFrameControllerUpdateByFrameId(parent_frame_id)
        return frame_id

    @staticmethod
    def CreateScrollable(
        parent_frame_id: int,
        component_label: str = "",
        child_index: int = 0,
        component_flags: int = 0x20000,
        page_context: int = 0,
        x: Optional[float] = None,
        y: Optional[float] = None,
        width: Optional[float] = None,
        height: Optional[float] = None,
        anchor_flags: Optional[int] = 0x6,
        disable_center: bool = False,
    ) -> int:
        from Py4GWCoreLib import UIManager

        resolved_child_index = int(child_index or 0)
        if resolved_child_index <= 0:
            resolved_child_index = GWUI.FindAvailableChildSlot(parent_frame_id, 0x20, 0xFE)
        if parent_frame_id <= 0 or resolved_child_index <= 0:
            return 0
        frame_id = GWUI.CreateScrollableFrameByFrameId(
            parent_frame_id,
            int(component_flags),
            resolved_child_index,
            int(page_context),
            component_label,
        )
        if frame_id <= 0:
            return 0

        if x is None or y is None or width is None or height is None:
            parent_left, parent_top, parent_right, parent_bottom = UIManager.GetFrameCoords(parent_frame_id)
            parent_width = abs(float(parent_right - parent_left))
            parent_height = abs(float(parent_bottom - parent_top))
            if x is None:
                x = 0.0
            if y is None:
                y = 0.0
            if width is None:
                width = parent_width
            if height is None:
                height = parent_height

        GWUI.ApplyRect(
            frame_id,
            float(x),
            float(y),
            float(width),
            float(height),
            flags=anchor_flags,
            disable_center=disable_center,
        )
        GWUI.FlushFrameControllerUpdateByFrameId(frame_id)
        page_frame_id = int(UIManager.GetChildFrameByFrameId(frame_id, 0) or 0)
        if page_frame_id > 0:
            GWUI.FlushFrameControllerUpdateByFrameId(page_frame_id)
        GWUI.TriggerFrameRedrawByFrameId(frame_id)
        GWUI.TriggerFrameRedrawByFrameId(parent_frame_id)
        return frame_id

    @staticmethod
    def CreateNativeTextLabelByFrameId(
        parent_frame_id: int,
        plain_text: str,
        component_label: str = "",
        child_index: int = 0,
        component_flags: int = 0x300,
    ) -> int:
        return GWUI.CreateTextLabel(
            parent_frame_id,
            plain_text,
            component_label,
            child_index,
            component_flags,
        )

    class Frame:
        def __init__(self, frame_id: int):
            self.frame_id = int(frame_id or 0)

        def __int__(self) -> int:
            return self.frame_id

        def exists(self) -> bool:
            return self.frame_id > 0

        def redraw(self) -> bool:
            return GWUI.TriggerFrameRedrawByFrameId(self.frame_id)

        def destroy(self) -> bool:
            return GWUI.DestroyUIComponentByFrameId(self.frame_id)

        def set_visible(self, is_visible: bool) -> bool:
            return GWUI.SetFrameVisibleByFrameId(self.frame_id, is_visible)

        def set_disabled(self, is_disabled: bool) -> bool:
            return GWUI.SetFrameDisabledByFrameId(self.frame_id, is_disabled)

        def set_position(self, x: float, y: float, flags: Optional[int] = 0x6, disable_center: bool = False) -> bool:
            return GWUI.SetFramePosition(self.frame_id, x, y, flags, disable_center)

        def set_size(self, width: float, height: float, flags: Optional[int] = 0x6, disable_center: bool = False) -> bool:
            return GWUI.SetFrameSize(self.frame_id, width, height, flags, disable_center)

        def apply_rect(
            self,
            x: float,
            y: float,
            width: float,
            height: float,
            flags: Optional[int] = 0x6,
            disable_center: bool = False,
        ) -> bool:
            return GWUI.ApplyRect(self.frame_id, x, y, width, height, flags, disable_center)

        def get_label(self) -> str:
            return GWUI.GetFrameLabelByFrameId(self.frame_id)

    class Button(Frame):
        def get_label(self) -> str:
            return str(PyUIManager.UIManager.get_button_label_by_frame_id(self.frame_id) or "")

        def set_label(self, enc_label: str) -> bool:
            return bool(PyUIManager.UIManager.set_button_label_by_frame_id(self.frame_id, str(enc_label or "")))

        def click(self) -> None:
            PyUIManager.UIManager.button_click(self.frame_id)

        def double_click(self) -> None:
            PyUIManager.UIManager.button_double_click(self.frame_id)

        def mouse_action(self, action: int) -> bool:
            return bool(PyUIManager.UIManager.button_mouse_action_by_frame_id(self.frame_id, int(action)))

    class Checkbox(Button):
        def is_checked(self) -> bool:
            return bool(PyUIManager.UIManager.is_checkbox_checked_by_frame_id(self.frame_id))

        def set_checked(self, checked: bool) -> bool:
            return bool(PyUIManager.UIManager.set_checkbox_checked_by_frame_id(self.frame_id, checked))

        def get_value(self) -> int:
            return int(PyUIManager.UIManager.get_checkbox_value_by_frame_id(self.frame_id) or 0)

        def set_value(self, value: int) -> bool:
            return bool(PyUIManager.UIManager.set_checkbox_value_by_frame_id(self.frame_id, int(value)))

    class Tabs(Frame):
        def add_tab(
            self,
            tab_name_enc: str,
            flags: int,
            child_index: int,
            callback: int = 0,
            wparam: int = 0,
        ) -> "GWUI.Frame":
            return GWUI.Frame(
                PyUIManager.UIManager.add_tab_by_frame_id(
                    self.frame_id,
                    str(tab_name_enc or ""),
                    int(flags),
                    int(child_index),
                    int(callback),
                    int(wparam),
                )
                or 0
            )

        def disable_tab(self, tab_id: int) -> bool:
            return bool(PyUIManager.UIManager.disable_tab_by_frame_id(self.frame_id, int(tab_id)))

        def enable_tab(self, tab_id: int) -> bool:
            return bool(PyUIManager.UIManager.enable_tab_by_frame_id(self.frame_id, int(tab_id)))

        def remove_tab(self, tab_id: int) -> bool:
            return bool(PyUIManager.UIManager.remove_tab_by_frame_id(self.frame_id, int(tab_id)))

        def get_current_tab_index(self) -> int:
            return int(PyUIManager.UIManager.get_current_tab_index_by_frame_id(self.frame_id) or 0)

        def get_tab_frame_id(self, tab_id: int) -> int:
            return int(PyUIManager.UIManager.get_tab_frame_id_by_frame_id(self.frame_id, int(tab_id)) or 0)

        def get_is_tab_enabled(self, tab_id: int) -> int:
            return int(PyUIManager.UIManager.get_is_tab_enabled_by_frame_id(self.frame_id, int(tab_id)) or 0)

        def get_tab_by_label(self, label: str) -> "GWUI.Frame":
            return GWUI.Frame(PyUIManager.UIManager.get_tab_by_label_by_frame_id(self.frame_id, str(label or "")) or 0)

        def get_current_tab(self) -> "GWUI.Frame":
            return GWUI.Frame(PyUIManager.UIManager.get_current_tab_by_frame_id(self.frame_id) or 0)

        def choose_tab_by_frame_id(self, tab_frame_id: int) -> bool:
            return bool(PyUIManager.UIManager.choose_tab_by_tab_frame_id(self.frame_id, int(tab_frame_id)))

        def choose_tab_by_index(self, tab_index: int) -> bool:
            return bool(PyUIManager.UIManager.choose_tab_by_index_by_frame_id(self.frame_id, int(tab_index)))

        def get_tab_button(self, tab_frame_id: int) -> "GWUI.Button":
            return GWUI.Button(PyUIManager.UIManager.get_tab_button_by_frame_id(self.frame_id, int(tab_frame_id)) or 0)

    class EditableText(Frame):
        def get_value(self) -> str:
            return str(PyUIManager.UIManager.get_editable_text_value_by_frame_id(self.frame_id) or "")

        def set_value(self, value: str) -> bool:
            return bool(PyUIManager.UIManager.set_editable_text_value_by_frame_id(self.frame_id, str(value or "")))

        def set_max_length(self, max_length: int) -> bool:
            return bool(PyUIManager.UIManager.set_editable_text_max_length_by_frame_id(self.frame_id, int(max_length)))

        def is_read_only(self) -> bool:
            return bool(PyUIManager.UIManager.is_editable_text_read_only_by_frame_id(self.frame_id))

        def set_read_only(self, read_only: bool) -> bool:
            return bool(PyUIManager.UIManager.set_editable_text_read_only_by_frame_id(self.frame_id, read_only))

    class ProgressBar(Button):
        def get_value(self) -> int:
            return int(PyUIManager.UIManager.get_progress_bar_value_by_frame_id(self.frame_id) or 0)

        def set_value(self, value: int) -> bool:
            return bool(PyUIManager.UIManager.set_progress_bar_value_by_frame_id(self.frame_id, int(value)))

        def set_max(self, value: int) -> bool:
            return bool(PyUIManager.UIManager.set_progress_bar_max_by_frame_id(self.frame_id, int(value)))

        def set_color_id(self, color_id: int) -> bool:
            return bool(PyUIManager.UIManager.set_progress_bar_color_id_by_frame_id(self.frame_id, int(color_id)))

        def set_style(self, style: int) -> bool:
            return bool(PyUIManager.UIManager.set_progress_bar_style_by_frame_id(self.frame_id, int(style)))

    class Dropdown(Frame):
        def get_options(self) -> list[int]:
            return [int(v) for v in (PyUIManager.UIManager.get_dropdown_options_by_frame_id(self.frame_id) or [])]

        def select_option(self, value: int) -> bool:
            return bool(PyUIManager.UIManager.select_dropdown_option_by_frame_id(self.frame_id, int(value)))

        def select_index(self, index: int) -> bool:
            return bool(PyUIManager.UIManager.select_dropdown_index_by_frame_id(self.frame_id, int(index)))

        def add_option(self, label_enc: str, value: int) -> bool:
            return bool(PyUIManager.UIManager.add_dropdown_option_by_frame_id(self.frame_id, str(label_enc or ""), int(value)))

        def get_count(self) -> int:
            return int(PyUIManager.UIManager.get_dropdown_count_by_frame_id(self.frame_id) or 0)

        def get_option_value(self, index: int) -> int:
            return int(PyUIManager.UIManager.get_dropdown_option_value_by_frame_id(self.frame_id, int(index)) or 0)

        def get_option_index(self, value: int) -> int:
            return int(PyUIManager.UIManager.get_dropdown_option_index_by_frame_id(self.frame_id, int(value)) or 0)

        def get_selected_index(self) -> int:
            return int(PyUIManager.UIManager.get_dropdown_selected_index_by_frame_id(self.frame_id) or 0)

        def has_value_mapping(self) -> bool:
            return bool(PyUIManager.UIManager.dropdown_has_value_mapping_by_frame_id(self.frame_id))

        def get_value(self) -> int:
            return int(PyUIManager.UIManager.get_dropdown_value_by_frame_id(self.frame_id) or 0)

        def set_value(self, value: int) -> bool:
            return bool(PyUIManager.UIManager.set_dropdown_value_by_frame_id(self.frame_id, int(value)))

    class Slider(Frame):
        def get_value(self) -> int:
            return int(PyUIManager.UIManager.get_slider_value_by_frame_id(self.frame_id) or 0)

        def set_value(self, value: int) -> bool:
            return bool(PyUIManager.UIManager.set_slider_value_by_frame_id(self.frame_id, int(value)))

    class TextLabel(Frame):
        def get_encoded(self) -> str:
            return GWUI.GetTextLabelEncodedByFrameId(self.frame_id)

        def get_decoded(self) -> str:
            return GWUI.GetTextLabelDecodedByFrameId(self.frame_id)

        def set_text(self, label: str) -> bool:
            return GWUI.SetTextLabelByFrameId(self.frame_id, label)

        def set_multiline_text(self, label: str) -> bool:
            return GWUI.SetMultilineLabelByFrameId(self.frame_id, label)

        def set_font(self, font_id: int) -> bool:
            return GWUI.SetTextLabelFontByFrameId(self.frame_id, font_id)

    class Scrollable(Frame):
        def get_page_frame_id(self) -> int:
            from Py4GWCoreLib import UIManager

            page_frame_id = int(UIManager.GetChildFrameByFrameId(self.frame_id, 0) or 0)
            if page_frame_id > 0:
                return page_frame_id
            return int(PyUIManager.UIManager.get_scrollable_page_by_frame_id(self.frame_id) or 0)

        def get_page(self) -> "GWUI.Frame":
            return GWUI.Frame(self.get_page_frame_id())

        def set_page(self, page_context: int) -> "GWUI.Frame":
            return GWUI.Frame(PyUIManager.UIManager.set_scrollable_page_by_frame_id(self.frame_id, int(page_context)) or 0)

        def get_items(self) -> list[int]:
            return [int(v) for v in (PyUIManager.UIManager.get_scrollable_items_by_frame_id(self.frame_id) or [])]

        def get_count(self) -> int:
            return int(PyUIManager.UIManager.get_scrollable_count_by_frame_id(self.frame_id) or 0)

        def clear_items(self) -> bool:
            return bool(PyUIManager.UIManager.clear_scrollable_items_by_frame_id(self.frame_id))

        def remove_item(self, child_index: int) -> bool:
            return bool(PyUIManager.UIManager.remove_scrollable_item_by_frame_id(self.frame_id, int(child_index)))

        def add_item(self, flags: int, child_index: int, callback: int = 0) -> bool:
            return bool(
                PyUIManager.UIManager.add_scrollable_item_by_frame_id(
                    self.frame_id,
                    int(flags),
                    int(child_index),
                    int(callback),
                )
            )

        def get_selected_value(self) -> int:
            return int(PyUIManager.UIManager.get_scrollable_selected_value_by_frame_id(self.frame_id) or 0)

        def get_sort_handler(self) -> int:
            return int(PyUIManager.UIManager.get_scrollable_sort_handler_by_frame_id(self.frame_id) or 0)

        def set_sort_handler(self, handler: int) -> bool:
            return bool(PyUIManager.UIManager.set_scrollable_sort_handler_by_frame_id(self.frame_id, int(handler)))

        def create_text_label(
            self,
            plain_text: str,
            component_label: str = "",
            child_index: int = 0,
            component_flags: int = 0x300,
        ) -> "GWUI.TextLabel":
            parent_id = self.get_page_frame_id() or self.frame_id
            frame_id = GWUI.CreateTextLabel(
                parent_id,
                plain_text,
                component_label=component_label,
                child_index=child_index,
                component_flags=component_flags,
            )
            return GWUI.TextLabel(frame_id)

    class Window(Frame):
        def set_title(self, title: str) -> bool:
            return GWUI.SetWindowTitle(self.frame_id, title)

        def get_content_frame_id(self) -> int:
            return GWUI.ResolveWindowContentFrameByFrameId(self.frame_id)

        def get_content(self) -> "GWUI.Frame":
            return GWUI.Frame(self.get_content_frame_id())

        def get_scrollable_frame_id(self) -> int:
            return GWUI.ResolveWindowScrollableFrameByFrameId(self.frame_id)

        def get_scrollable(self) -> "GWUI.Scrollable":
            return GWUI.Scrollable(self.get_scrollable_frame_id())

        def create_scrollable(
            self,
            component_label: str = "",
            child_index: int = 0,
            component_flags: int = 0x20000,
            page_context: int = 0,
            x: Optional[float] = None,
            y: Optional[float] = None,
            width: Optional[float] = None,
            height: Optional[float] = None,
            anchor_flags: Optional[int] = 0x6,
            disable_center: bool = False,
        ) -> "GWUI.Scrollable":
            frame_id = GWUI.CreateScrollable(
                self.get_content_frame_id(),
                component_label=component_label,
                child_index=child_index,
                component_flags=component_flags,
                page_context=page_context,
                x=x,
                y=y,
                width=width,
                height=height,
                anchor_flags=anchor_flags,
                disable_center=disable_center,
            )
            return GWUI.Scrollable(frame_id)

        def create_text_label(
            self,
            plain_text: str,
            component_label: str = "",
            child_index: int = 0,
            component_flags: int = 0x300,
        ) -> "GWUI.TextLabel":
            frame_id = GWUI.CreateTextLabel(
                self.get_content_frame_id(),
                plain_text,
                component_label=component_label,
                child_index=child_index,
                component_flags=component_flags,
            )
            return GWUI.TextLabel(frame_id)

    @staticmethod
    def WrapFrame(frame_id: int) -> "GWUI.Frame":
        return GWUI.Frame(frame_id)

    @staticmethod
    def WrapWindow(frame_id: int) -> "GWUI.Window":
        return GWUI.Window(frame_id)

    @staticmethod
    def WrapScrollable(frame_id: int) -> "GWUI.Scrollable":
        return GWUI.Scrollable(frame_id)

    @staticmethod
    def WrapTextLabel(frame_id: int) -> "GWUI.TextLabel":
        return GWUI.TextLabel(frame_id)
