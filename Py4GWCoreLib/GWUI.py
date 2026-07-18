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

    @staticmethod
    def DestroyWindow(window_id: int) -> bool:
        """Destroy a window + everything in it SAFELY. Scrubs the native hover/focus input globals
        first so a control that is the current hover/focus target is not left dangling after it's
        freed — that dangling pointer is the 'crash on closing the window' use-after-free. ALWAYS use
        this (not a raw destroy) to close a window that hosts checkbox/edit/slider/progress/etc."""
        try:
            return bool(PyUIManager.UIManager.destroy_window_safely_by_frame_id(int(window_id)))
        except Exception:
            return False

    @staticmethod
    def ClearInputTargets() -> None:
        """Scrub the native hover/focus target globals (no-hover, no-focus). Call before freeing any
        frame that might currently be hovered/focused."""
        try:
            PyUIManager.UIManager.clear_ui_input_targets()
        except Exception:
            pass

    @staticmethod
    def CreatePanel(window_id: int, width: float = 0.0, height: float = 0.0, child_index: int = 0) -> int:
        """Create an owned CONTENT PANEL inside a window and return its id. Parent controls to the PANEL,
        not the window — the game never hosts controls on the window chrome, and doing so is what makes
        them crash on close. Returns the panel frame id (or 0)."""
        try:
            return int(PyUIManager.UIManager.create_content_panel_by_frame_id(
                int(window_id), float(width), float(height), int(child_index)) or 0)
        except Exception:
            return 0

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

    # ── Native Buttons (CONFIRMED WORKING in-client 2026-06-30) ─────────
    # A real, textured, clickable GW button = a STYLED button (IUi::UiCtlBtnProc) item in a
    # NO-STRETCH scrollable frame list. The list sizes items to their content; the item gets
    # the 0x40000 paint bit + the shared button image list (msg 0x05); clicks are read from the
    # engine's own pushed state (msg 0x59). Full RE: docs/RE/native_button_pipeline.md.
    #
    # Usage:
    #     win   = GWUI.CreateWindow(x, y, w, h, "Title")
    #     blist = GWUI.CreateButtonList(win)
    #     btn   = GWUI.CreateButton(blist, "Click Me")
    #     ... every frame ...
    #     if GWUI.IsButtonClicked(btn):
    #         do_something()

    _button_prev_pushed: dict = {}

    @staticmethod
    def CreateButtonList(window_id: int, child_index: int = 0) -> int:
        """Create a scrollable frame list that lays buttons out at their own size (no stretch).
        Add buttons to the returned list id with CreateButton()."""
        list_id = int(
            PyUIManager.UIManager.create_scrollable_content_by_frame_id(window_id, child_index, 0x20000) or 0
        )
        if list_id:
            try:
                PyUIManager.UIManager.set_frame_list_no_stretch_by_frame_id(list_id)
            except Exception:
                pass
        return list_id

    @staticmethod
    def CreateButton(button_list_id: int, caption: str, insert_index: int = 0) -> int:
        """Add a real styled GW button (textured, clickable) to a list created with
        CreateButtonList(). Returns the button frame id (use it with IsButtonClicked)."""
        return int(
            PyUIManager.UIManager.add_control_item_by_frame_id(
                button_list_id, "styled_button", str(caption), insert_index, 0
            )
            or 0
        )

    @staticmethod
    def IsButtonPushed(button_id: int) -> bool:
        """True while the button is currently held down (native pushed state, msg 0x59)."""
        try:
            return bool(PyUIManager.UIManager.is_button_pushed_by_frame_id(button_id))
        except Exception:
            return False

    @staticmethod
    def IsButtonClicked(button_id: int) -> bool:
        """True exactly once per click (rising edge of the native pushed state).
        Call every frame; the previous state is tracked internally."""
        cur = GWUI.IsButtonPushed(button_id)
        prev = GWUI._button_prev_pushed.get(button_id, False)
        GWUI._button_prev_pushed[button_id] = cur
        return cur and not prev

    @staticmethod
    def CreateCheckbox(window_id: int, label: str, child_index: int = 1, checked: bool = False) -> int:
        """Add a REAL GW checkbox (native box art, self-sizing) as a DIRECT CHILD of a window
        created with CreateWindow(). Give each checkbox on the same window a UNIQUE child_index
        (1, 2, 3, ...) so they lay out instead of overlapping. Returns the checkbox frame id
        (use it with IsChecked / SetChecked)."""
        return int(
            PyUIManager.UIManager.create_checkbox_child_by_frame_id(
                window_id, str(label), int(child_index), bool(checked)
            )
            or 0
        )

    @staticmethod
    def IsChecked(checkbox_id: int) -> bool:
        """True while the checkbox is ticked (native checked bit, msg 0x58). User clicks
        auto-toggle it, so poll this each frame to read the current state."""
        try:
            return bool(PyUIManager.UIManager.is_checkbox_checked_by_frame_id(checkbox_id))
        except Exception:
            return False

    @staticmethod
    def SetChecked(checkbox_id: int, checked: bool) -> bool:
        """Set the checkbox ticked state programmatically (native msg 0x57)."""
        try:
            return bool(
                PyUIManager.UIManager.set_checkbox_checked_by_frame_id(checkbox_id, bool(checked))
            )
        except Exception:
            return False

    # Radio group = a SELECTABLE frame list; single-selection gives free mutual exclusion.
    # Option codes are kept per-list so callers work in stable 0-based INDICES.
    _radio_codes: dict = {}
    # Per-list next child code for hyperlink rows (kept nonzero + unique so clicks are pollable).
    _hyperlink_next: dict = {}

    @staticmethod
    def CreateRadioGroup(window_id: int, options: list[str], default_index: int = -1, child_index: int = 0) -> int:
        """Create a radio-button group (mutually-exclusive single selection) inside window_id.
        Renders as a selectable scrollable list with one text row per option; clicking a row
        selects it and auto-clears the others (native single-selection). Optionally pre-selects
        default_index. Returns the list id — read it with GetRadioSelection(), set it with
        SetRadioSelection()."""
        list_id = int(
            PyUIManager.UIManager.create_selectable_scrollable_content_by_frame_id(window_id, child_index, 0x20000) or 0
        )
        if not list_id:
            return 0
        # (Ghidra-verified) Rows MUST be CtlTextSelectable (same proc as hyperlinks), NOT flat buttons.
        # When the list highlights the selected row it sends child msg 0x57 with a null out-ptr:
        # CtlTextSelectable's 0x57 SETS the per-row selected flag + redraws (visible highlight) and is
        # null-safe; CtlBtnProc's 0x57 only CLEARS its checked bit (row never highlights); CtlTextProc's
        # 0x57 writes through the null (crash). Select by the create-time child KEY = insert_index (i+1),
        # NOT the AddItem return (that is the frame-id). insert_index 0 is reserved (== "no selection").
        codes = []
        for i, opt in enumerate(options):
            idx = i + 1
            try:
                PyUIManager.UIManager.add_clickable_text_button_to_selectable_list(list_id, str(opt), idx, 0)
            except Exception:
                pass
            codes.append(idx)
        GWUI._radio_codes[list_id] = codes
        if 0 <= default_index < len(codes):
            try:
                PyUIManager.UIManager.set_frame_list_selection_by_frame_id(list_id, codes[default_index])
            except Exception:
                pass
        return list_id

    @staticmethod
    def GetRadioSelection(list_id: int) -> int:
        """Return the selected option INDEX (0-based), or -1 if nothing is selected. Poll each frame."""
        code = int(PyUIManager.UIManager.get_frame_list_selection_by_frame_id(list_id) or 0)
        if not code:
            return -1
        codes = GWUI._radio_codes.get(list_id, [])
        return codes.index(code) if code in codes else -1

    @staticmethod
    def SetRadioSelection(list_id: int, index: int) -> bool:
        """Programmatically select option INDEX (default/restore). Returns True on success."""
        codes = GWUI._radio_codes.get(list_id, [])
        if not (0 <= index < len(codes)) or not codes[index]:
            return False
        try:
            return bool(PyUIManager.UIManager.set_frame_list_selection_by_frame_id(list_id, codes[index]))
        except Exception:
            return False

    # ── Clickable text button (hyperlink-style, CtlTextBtnProc) ──────────
    # Text buttons surface a click ONLY as parent-notify 8, which ONLY a SELECTABLE list consumes
    # into a pollable selection. So: make a selectable list, add buttons, poll the selection.
    #   win  = GWUI.CreateWindow(x, y, w, h, "Title")
    #   hl   = GWUI.CreateHyperlinkList(win)
    #   btn  = GWUI.CreateHyperlink(hl, "Click Me")
    #   ... every frame ...
    #   if GWUI.GetClickedHyperlink(hl):   # nonzero == a row was clicked
    #       do_something()

    @staticmethod
    def CreateHyperlinkList(window_id: int, child_index: int = 0) -> int:
        """Create a SELECTABLE scrollable frame list to hold clickable text buttons. Only a
        selectable list turns a text button's notify-8 click into a pollable selection."""
        return int(
            PyUIManager.UIManager.create_selectable_scrollable_content_by_frame_id(
                window_id, child_index, 0x20000
            )
            or 0
        )

    @staticmethod
    def CreateHyperlink(hyperlink_list_id: int, caption: str, insert_index: int = 0) -> int:
        """Add a clickable text button (cyan hyperlink look) to a list from CreateHyperlinkList().
        Returns the item frame id; read clicks with GetClickedHyperlink(list_id).

        Each row is auto-assigned a UNIQUE NONZERO child code. The selectable list keys rows by
        their create-time child code (== insert_index); if every row shares 0 (the old default)
        the rows are indistinguishable AND a click reads back as 0 == "no selection", so clicks
        were never detected. An explicit nonzero insert_index is honored; otherwise codes run 1,2,3…"""
        code = int(insert_index)
        if code <= 0:
            code = GWUI._hyperlink_next.get(hyperlink_list_id, 0) + 1
        GWUI._hyperlink_next[hyperlink_list_id] = max(code, GWUI._hyperlink_next.get(hyperlink_list_id, 0))
        return int(
            PyUIManager.UIManager.add_clickable_text_button_to_selectable_list(
                hyperlink_list_id, str(caption), code, 0
            )
            or 0
        )

    @staticmethod
    def GetClickedHyperlink(hyperlink_list_id: int) -> int:
        """Return the child code of the currently-selected/clicked text button (0 if none).
        Poll each frame; nonzero identifies the clicked row (msg 0x67)."""
        return int(
            PyUIManager.UIManager.get_frame_list_selection_by_frame_id(hyperlink_list_id) or 0
        )

    @staticmethod
    def SetHyperlinkColor(text_button_id: int, color_abgr: int) -> bool:
        """Override the baked cyan NORMAL color (msg 0x5b). color is 0xAABBGGRR (ABGR)."""
        try:
            return bool(
                PyUIManager.UIManager.set_text_button_color_by_frame_id(
                    text_button_id, int(color_abgr) & 0xFFFFFFFF
                )
            )
        except Exception:
            return False

    @staticmethod
    def SetHyperlinkHoverColor(text_button_id: int, color_abgr: int) -> bool:
        """Override the baked HOVER color (msg 0x5d). color is 0xAABBGGRR (ABGR)."""
        try:
            return bool(
                PyUIManager.UIManager.set_text_button_hover_color_by_frame_id(
                    text_button_id, int(color_abgr) & 0xFFFFFFFF
                )
            )
        except Exception:
            return False

    @staticmethod
    def SetHyperlinkText(text_button_id: int, caption: str) -> bool:
        """Replace the caption (msg 0x5f, raw wide string)."""
        try:
            return bool(
                PyUIManager.UIManager.set_text_button_text_by_frame_id(text_button_id, str(caption))
            )
        except Exception:
            return False

    # ── Native Edit Box (edit / text input) ─────────────────────────────
    # A REAL editable text box is a DIRECT CHILD of a window (NOT a frame-list item): the
    # CCtlEdit value context is only installed by the outer proc (0x008852e0) on the
    # CreateUIComponent child path, and CtlEditProc has no self-size so an explicit size is
    # required. The caret material must be warm (it is, in any in-game session with a chat box).
    #
    # Usage:
    #     win  = GWUI.CreateWindow(x, y, w, h, "Title")
    #     edit = GWUI.CreateEditBox(win, "Name")
    #     GWUI.SetEditBoxText(edit, "hello")
    #     text = GWUI.GetEditBoxText(edit)

    @staticmethod
    def CreateEditBox(window_id: int, label: str = "EditBox", child_index: int = 0,
                      component_flags: int = 0x892e000, width: float = 200.0, height: float = 20.0) -> int:
        """Create a real editable text box as a direct child of window_id. Returns the edit
        frame id. Only creates in-game (caret materials must be warm)."""
        try:
            if not PyUIManager.UIManager.is_edit_caret_material_ready():
                # Cold (login/char-select): creation still warms it via a guarded msg 0x05,
                # but prefer creating once in-game where a chat box already warmed it.
                pass
            # NOTE: GW frame ids are 0-based — id 0 is a VALID handle. Do NOT collapse it with `or 0`.
            # The native creator returns 0xFFFFFFFF (4294967295) on failure; everything else is a real id.
            rid = PyUIManager.UIManager.create_edit_box_child_by_frame_id(
                window_id, str(label), child_index, component_flags, float(width), float(height)
            )
            rid = int(rid)
            return -1 if rid == 0xFFFFFFFF else rid
        except Exception:
            return -1

    @staticmethod
    def SetEditBoxText(edit_id: int, text: str) -> bool:
        """Set the edit box text (auto-encoded, msg 0x5E)."""
        try:
            return bool(PyUIManager.UIManager.set_edit_box_text_by_frame_id(edit_id, str(text)))
        except Exception:
            return False

    @staticmethod
    def SetEditBoxMaxLength(edit_id: int, max_length: int) -> bool:
        """Set the max input length (msg 0x5A)."""
        try:
            return bool(PyUIManager.UIManager.set_edit_box_max_length_by_frame_id(edit_id, int(max_length)))
        except Exception:
            return False

    @staticmethod
    def GetEditBoxText(edit_id: int) -> str:
        """Read the current edit box text (msg 0x57 via the existing GetValue path)."""
        try:
            return str(PyUIManager.UIManager.get_editable_text_value_by_frame_id(edit_id) or "")
        except Exception:
            return ""

    # ── Native progress bar (CtlProgress @ EXE 0x008812e0) ───────────────
    # The default create_progress_bar path (GW::ProgressBar::Create) registers the rate-arrow
    # LOADER as its callback and crashes; this path registers the CORRECT proc and sizes the
    # bar explicitly (the proc self-sizes height only, so width must be given).
    #
    # Usage:
    #     win = GWUI.CreateWindow(x, y, w, h, "Title")
    #     bar = GWUI.CreateProgressBar(win, x=10, y=30, width=200)
    #     ... every frame ...
    #     GWUI.SetProgressBarPercent(bar, pct)   # 0..100

    @staticmethod
    def CreateProgressBar(window_id: int, x: float = 10.0, y: float = 10.0,
                          width: float = 160.0, height: float = 0.0) -> int:
        """Create a real native GW progress bar (CtlProgress) as a positioned child of a window.
        Renders a filled bar (primary-bar paint bit is set for you); drive it each frame with
        SetProgressBarPercent() or SetProgressBarValue(). Returns the progress-bar frame id."""
        return int(
            PyUIManager.UIManager.create_progress_bar_child_by_frame_id(
                window_id, float(x), float(y), float(width), float(height), 0, 0x300
            )
            or 0
        )

    @staticmethod
    def SetProgressBarPercent(progress_id: int, percent: int) -> bool:
        """Set the fill as a percentage 0..100 (base FrameWithValue SetPercent, msg 0x5B)."""
        try:
            pct = int(max(0, min(100, percent)))
            return bool(PyUIManager.UIManager.set_progress_bar_percent_by_frame_id(progress_id, pct))
        except Exception:
            return False

    @staticmethod
    def SetProgressBarValue(progress_id: int, value: int) -> bool:
        """Set the fill by absolute value relative to max (default max is 100; msg 0x58)."""
        try:
            return bool(PyUIManager.UIManager.set_progress_bar_value_by_frame_id(progress_id, int(value)))
        except Exception:
            return False

    @staticmethod
    def SetProgressBarMax(progress_id: int, value: int) -> bool:
        """Set the maximum value the bar fills to (msg 0x5A)."""
        try:
            return bool(PyUIManager.UIManager.set_progress_bar_max_by_frame_id(progress_id, int(value)))
        except Exception:
            return False

    # ── Tabs (CtlPage) — 2026-06-30 ──────────────────────────────────────
    # Usage:
    #     win  = GWUI.CreateWindow(...)
    #     tabs = GWUI.CreateTabs(win)
    #     GWUI.AddTab(tabs, "General", 0)     # first tab auto-selects
    #     GWUI.AddTab(tabs, "Combat",  1)
    #     GWUI.AddTab(tabs, "Debug",   2)
    #     ...
    #     idx = GWUI.GetActiveTab(tabs)       # poll each frame; changes on user click
    _tabs_prev_active: dict = {}

    @staticmethod
    def CreateTabs(window_id: int, child_index: int = 0) -> int:
        """Create a TABS container (styled CtlPage) as a DIRECT child of the window — the game's own
        textured-tabs path: the styled UiCtlPageProc (0x00885590) is the PRIMARY proc, so its msg-0x5e
        config makes AddTab build TEXTURED tab buttons (the base-proc list-item path rendered generic).
        NOTE: the container renders 0x0 until at least one tab is added (AddTab)."""
        return int(
            PyUIManager.UIManager.create_tabs_frame_by_frame_id(window_id, 0x40000, child_index) or 0
        )

    @staticmethod
    def AddTab(tabs_id: int, caption: str, index: int, body_text: str = "") -> int:
        """Add a tab (button + body) to a CtlPage created with CreateTabs().
        index must be >= 0 and unique. Returns the tab BODY frame id. First tab auto-selects."""
        return int(
            PyUIManager.UIManager.add_tab_to_page_by_frame_id(
                tabs_id, str(caption), int(index), 0, str(body_text)
            )
            or 0
        )

    @staticmethod
    def SelectTab(tabs_id: int, index: int) -> bool:
        """Programmatically select the active tab by index (native msg 0x5d)."""
        try:
            return bool(PyUIManager.UIManager.tab_set_active_by_frame_id(tabs_id, int(index)))
        except Exception:
            return False

    @staticmethod
    def GetActiveTab(tabs_id: int) -> int:
        """Active tab index (native msg 0x59). Returns 0xffffffff (-1) until the first tab exists.
        Poll every frame; the value changes when the user clicks a tab button (handled in-engine)."""
        try:
            return int(PyUIManager.UIManager.tab_get_active_by_frame_id(tabs_id))
        except Exception:
            return 0xFFFFFFFF

    @staticmethod
    def GetTabBodyFrame(tabs_id: int, index: int) -> int:
        """Body frame id for the given tab index (native msg 0x5a)."""
        try:
            return int(PyUIManager.UIManager.tab_get_body_frame_by_frame_id(tabs_id, int(index)) or 0)
        except Exception:
            return 0

    @staticmethod
    def IsTabChanged(tabs_id: int) -> bool:
        """True once when the active tab index changes (user click or SelectTab). Call each frame."""
        cur = GWUI.GetActiveTab(tabs_id)
        prev = GWUI._tabs_prev_active.get(tabs_id, 0xFFFFFFFF)
        GWUI._tabs_prev_active[tabs_id] = cur
        return cur != prev

    @staticmethod
    def CreateSlider(
        window_id: int,
        min_value: int = 0,
        max_value: int = 100,
        initial_value: int = 0,
        width: float = 150.0,
        height: float = 18.0,
        child_index: int = 0,
    ) -> int:
        """Create a real textured GW slider (two-layer CtlSliderProc + UiCtlSliderProc) as a direct
        child of a managed window (use CreateWindow(), NOT a button/scrollable list). Range, value and
        size are set in the crash-safe order. Returns the slider frame id (use it with GetSliderValue).
        NOTE: sliders cannot be placed in a frame list — the single-proc item path crashes on click."""
        return int(
            PyUIManager.UIManager.create_slider_control_by_frame_id(
                window_id,
                int(min_value),
                int(max_value),
                int(initial_value),
                float(width),
                float(height),
                int(child_index),
            )
            or 0
        )

    @staticmethod
    def GetSliderValue(slider_id: int) -> int:
        """Current slider value (native engine state, msg 0x58). Reflects user drags — poll each frame."""
        try:
            return int(PyUIManager.UIManager.get_slider_value_by_frame_id(slider_id) or 0)
        except Exception:
            return 0

    @staticmethod
    def SetSliderValue(slider_id: int, value: int) -> bool:
        """Programmatically move the slider (msg 0x57). Value MUST be within the range set at creation
        (the engine asserts min<=value<=max), so clamp before calling."""
        try:
            return bool(PyUIManager.UIManager.set_slider_value_by_frame_id(slider_id, int(value)))
        except Exception:
            return False

    @staticmethod
    def DestroySlider(slider_id: int) -> bool:
        """Tear down a slider — use THIS, not a bare destroy. The slider registers an auto-scroll
        native CTimer on a groove click that the normal destroy path never releases; this sends a
        synthetic mouse-up first to free it (otherwise the leaked repeating timer crashes the client
        after some fiddling). Call BEFORE destroying the slider's parent window."""
        try:
            return bool(PyUIManager.UIManager.destroy_slider_control_by_frame_id(slider_id))
        except Exception:
            return False



    # ── Native Group Header (collapsible section) ──────────────────────────
    # A real GW group header = the CGroupHeaderFrame proc (EXE 0x0087ddc0) created as an
    # item in a PLAIN scrollable frame list. The engine self-builds a CheckOpen checkbox +
    # a caption child and lays them out via the L"UiCtlGroupHeader" template, so you must
    # NOT size/position it. Open/closed state is the engine's own (msg 0x56).
    #
    # Usage:
    #     win = GWUI.CreateWindow(x, y, w, h, "Title")
    #     lst = PyUIManager.UIManager.create_scrollable_content_by_frame_id(win, 0, 0x20000)
    #     hdr = GWUI.CreateGroupHeader(lst, "Section")
    #     ... every frame ...
    #     if not GWUI.IsGroupHeaderOpen(hdr):
    #         # section collapsed by the user
    @staticmethod
    def CreateGroupHeader(frame_list_id: int, header_text: str, insert_index: int = 0, item_flags: int = 0) -> int:
        """Add a native collapsible GROUP HEADER (checkbox + caption) row to a scrollable
        frame list. The engine builds and positions the children itself — do not size or
        position it. Poll IsGroupHeaderOpen() to detect collapse. Returns the header frame id."""
        return int(
            PyUIManager.UIManager.add_group_header_item_to_frame_list_by_frame_id(
                int(frame_list_id), str(header_text), int(insert_index), int(item_flags)
            )
            or 0
        )

    @staticmethod
    def IsGroupHeaderOpen(header_id: int) -> bool:
        """True if the group header section is expanded (native state, msg 0x56)."""
        try:
            return bool(PyUIManager.UIManager.group_header_get_is_open_by_frame_id(int(header_id)))
        except Exception:
            return False

    @staticmethod
    def SetGroupHeaderOpen(header_id: int, is_open: bool) -> None:
        """Expand/collapse the group header section (msg 0x58)."""
        try:
            PyUIManager.UIManager.group_header_set_is_open_by_frame_id(int(header_id), bool(is_open))
        except Exception:
            pass

    @staticmethod
    def SetGroupHeaderText(header_id: int, header_text: str) -> None:
        """Change the group header caption (msg 0x59)."""
        try:
            PyUIManager.UIManager.group_header_set_text_by_frame_id(int(header_id), str(header_text))
        except Exception:
            pass

    # ── App-side collapsible SECTIONS (the engine provides NO native grouping) ──
    # (Ghidra-verified) A group header only toggles its OWN checkbox glyph — it never touches sibling
    # rows. To build a real collapsible section: create the header, create its member rows with known
    # insert_index CODES, register them here, then call UpdateGroupSections() every frame. It hides/
    # shows members (msg 0x67) whenever the header's open state flips, and the list reflows.
    # The frame list MUST be a 0x20000 (no-0x2000) list or it won't reflow.
    _group_sections: dict = {}   # header_id -> {"list": int, "members": list[int], "last": bool | None}

    @staticmethod
    def RegisterGroupSection(header_id: int, frame_list_id: int, member_codes: list) -> None:
        """Tie a group header to the item CODES (their insert_index) that collapse with it. Call once
        after creating the header and its rows; then poll UpdateGroupSections() each frame."""
        GWUI._group_sections[int(header_id)] = {
            "list": int(frame_list_id),
            "members": [int(c) for c in member_codes],
            "last": None,
        }

    @staticmethod
    def UpdateGroupSections() -> None:
        """Call EVERY frame. When a registered group header's open/closed state changes, show or hide
        its member items (msg 0x67) so the section actually collapses/expands and the list reflows."""
        for hid, sec in list(GWUI._group_sections.items()):
            # skip/drop sections whose header frame was freed (window closed) — messaging it would crash
            try:
                if not PyUIManager.UIManager.frame_exists_by_frame_id(int(hid)):
                    GWUI._group_sections.pop(hid, None)
                    continue
            except Exception:
                pass
            try:
                cur = GWUI.IsGroupHeaderOpen(hid)
            except Exception:
                continue
            if cur != sec["last"]:
                for code in sec["members"]:
                    try:
                        PyUIManager.UIManager.ctl_frame_list_show_item_by_frame_id(sec["list"], int(code), bool(cur))
                    except Exception:
                        pass
                sec["last"] = cur

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
