import PyUIManager
from typing import Optional


class GWUI:
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
    def SetFrameTitleByFrameId(frame_id: int, title: str) -> bool:
        return bool(PyUIManager.UIManager.set_frame_title_by_frame_id(frame_id, str(title or "")))

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
        return GWUI.SetFrameRect(
            frame_id,
            x,
            y,
            width,
            height,
            flags,
            disable_center,
        )

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
    ) -> int:
        root_frame_id = GWUI.CreateWindow(
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
        return root_frame_id
