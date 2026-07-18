"""
Native button creation using the CtlBtnProc (engine-level) FrameProc.

Background:
    The existing GWCA CreateButtonFrame path uses IUi::UiCtlBtnProc which depends
    on s_btnCheckImageList (a global HFrameImageList created at startup).
    This crashes when creating buttons after game startup.

Solution: CtlBtnProc (Path B — Flat Engine Button)
    CtlBtnProc is the bare-metal engine button FrameProc with ZERO external
    dependencies. It paints flat-color rectangles (no GW styling) and accepts
    text via the CtlBtnSetTextLiteral message (msg 0x5E).

    This is the exact same path the IME candidate window uses for its prev/next
    page buttons — proven working.

    Prior to this project, CtlBtnProc buttons rendered as thin strips because
    no dimensions were set after creation.  The fix: call FrameSetSize after
    FrameCreate to give the button visible dimensions.

    Click support requires FrameNewSubclass on the PARENT window with the
    dialog subclass type (0x0aed) to add OnFrameNotify dispatch.  This is
    implemented as a separate step — see create_flat_button_with_click().

Architecture:
    Python wrapper → NativeFunction (via Game.enqueue) → FrameCreate
      → passes CtlBtnProc callback instead of IUi::UiCtlBtnProc
      → after creation, calls CtlBtnSetTextLiteral(frameId, label)
      → calls FrameSetSize(frameId, width, height) to fix thin strip
      → optionally: FrameNewSubclass(parentId, dialogType, 0) for clicks

Functions resolved via FindAssertion (FrApi.cpp string-anchoring) survive
EXE rebuilds.

EXE Build: 06-14-2026 (verified against loaded Gw.exe(Symbols))
"""

import ctypes
from typing import Optional

from ...Scanner import Scanner, ScannerSection
from ..internals.prototypes import Prototypes
from ..internals.native_function import NativeFunction
from Py4GW import Game


# ============================================================================
# Coord2f — 8-byte struct {float x; float y} used by FrameSetSize/FrameSetPosition
# ============================================================================

class Coord2f(ctypes.Structure):
    """Matches the native Coord2f type: {float x; float y}, 8 bytes total."""
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
    ]


# ============================================================================
# Helper: Robust multi-pattern resolution with fallback
# ============================================================================

def _resolve_ctlbtn_proc() -> int:
    """
    Find CtlBtnProc address using multiple fallback patterns.
    Returns the function address or 0.

    Strategy (ordered):
      1. Primary 26-byte unique prologue (EXE 05-30: 0x0060f4f0, Symbols: 0x005f1180)
      2. Short stack-frame prologue (9 bytes, SUB ESP,0x30 + PUSH sequence)
      3. Jump-table max-message pattern (CMP EAX,0x5E; JA) + ToFunctionStart
    """
    # Pattern 1: Full 26-byte unique prologue (verified in 05-30 and Symbols builds)
    addr = Scanner.Find(
        b"\x55\x8B\xEC\x83\xEC\x30\x53\x8B\x5D\x08\x56\x57"
        b"\x8B\x7D\x0C\x8B\x43\x04\x8B\x53\x08\x48\x83\xF8\x5E",
        "xxxxxxxxxxxxxxxxxxxxxxxxxx",
        0, ScannerSection.TEXT,
    )
    if addr:
        print(f"[ButtonMethods] CtlBtnProc resolved via primary pattern @ 0x{addr:08X}")
        return addr

    # Pattern 2: Short stack-frame prologue (SUB ESP,0x30 + register saves)
    addr = Scanner.Find(
        b"\x83\xEC\x30\x53\x8B\x5D\x08\x56\x57",
        "xxxxxxxxx",
        0, ScannerSection.TEXT,
    )
    if addr:
        candidate = Scanner.ToFunctionStart(addr + 0x10, 0x80)
        if candidate:
            print(f"[ButtonMethods] CtlBtnProc resolved via short-prologue fallback @ 0x{candidate:08X}")
            return candidate

    # Pattern 3: Max-message dispatch (CMP EAX,0x5E; JA) — unique to CtlBtnProc
    addr = Scanner.Find(
        b"\x48\x83\xF8\x5E\x0F\x87",
        "xxxxxx",
        0, ScannerSection.TEXT,
    )
    if addr:
        candidate = Scanner.ToFunctionStart(addr, 0x100)
        if candidate:
            print(f"[ButtonMethods] CtlBtnProc resolved via max-msg fallback @ 0x{candidate:08X}")
            return candidate

    print("[ButtonMethods] ERROR: All CtlBtnProc patterns failed — EXE build mismatch?")
    return 0


# ============================================================================
# Native Function Registrations
# ============================================================================

_ctlbtn_addr = _resolve_ctlbtn_proc()

# CtlBtnProc — address-only NativeFunction (no prototype, no enqueue — 
# its address is passed as a callback parameter to FrameCreate).
_ctlb = NativeFunction.__new__(NativeFunction)
_ctlb.name = "CtlBtnProc_Callback"
_ctlb.pattern = b""
_ctlb.mask = ""
_ctlb.offset = 0
_ctlb.section = ScannerSection.TEXT
_ctlb.prototype = None
_ctlb.use_near_call = False
_ctlb.near_call_offset = 0
_ctlb.report_success = False
if _ctlbtn_addr:
    _ctlb.func_ptr = _ctlbtn_addr
    _ctlb.initialized = True
else:
    _ctlb.func_ptr = None
    _ctlb.initialized = False
CtlBtnProc_Callback = _ctlb

# FrameCreate (aka CreateUIComponent_Func in GWCA) — the frame allocation function.
# GWCA pattern at +0x27 inside FUN_0062bfc0; ToFunctionStart resolves to entry.
# Prototype: uint32 __cdecl FrameCreate(uint32 parent, uint32 flags, uint32 child_idx,
#                                        void* callback, void* param, void* label_utf16)
_create_component_addr = Scanner.Find(
    b"\x33\xd2\x89\x45\x08\xb9\xc8\x01\x00\x00",
    "xxxxxxxxxx",
    0,
    ScannerSection.TEXT,
)
_create_component_addr = Scanner.ToFunctionStart(_create_component_addr)

FrameCreate_Func = NativeFunction.from_address(
    name="FrameCreate_Func",
    address=_create_component_addr,
    prototype=Prototypes["U32_U32_U32_U32_U32_U32"],
)

# CtlBtnSetTextLiteral — sends msg 0x5E to set button text after creation.
# Pattern at +0x4E inside; ToFunctionStart resolves to function entry.
# Prototype: void __cdecl CtlBtnSetTextLiteral(uint32 frameId, wchar_t* text)
_set_text_addr = Scanner.Find(
    b"\x6A\x00\x53\x6A\x5E\x57\xE8",
    "xxxxxxx",
    0,
    ScannerSection.TEXT,
)
_set_text_addr = Scanner.ToFunctionStart(_set_text_addr)

CtlBtnSetTextLiteral_Func = NativeFunction.from_address(
    name="CtlBtnSetTextLiteral_Func",
    address=_set_text_addr,
    prototype=Prototypes["Void_U32_WCharP"],
)


# ============================================================================
# FrameSetSize — FrApi.cpp line 0x880, EXE 0x0062f9a0
# Resolved via FindAssertion (survives EXE rebuilds).
# Prototype: void __cdecl FrameSetSize(uint32 frameId, Coord2f* size)
# ============================================================================

def _resolve_frameset_size() -> int:
    """Resolve FrameSetSize via FindAssertion on FrApi.cpp anchor."""
    addr = Scanner.FindAssertion("FrApi.cpp", "frameId", 0x880, 0)
    if addr:
        fn_start = Scanner.ToFunctionStart(addr, 0x100)
        if fn_start:
            print(f"[ButtonMethods] FrameSetSize resolved @ 0x{fn_start:08X}")
            return fn_start

    # Fallback: byte pattern from known EXE build 06-14
    # PUSH DWORD [EBP+0xC]; MOV ECX, [EBP+0x8]; CALL FrApi_body
    addr = Scanner.Find(
        b"\xFF\x75\x0C\x8B\x4D\x08\xE8",
        "xxxxxxx",
        0, ScannerSection.TEXT,
    )
    if addr:
        fn_start = Scanner.FunctionFromNearCall(addr + 2, True)  # CALL target
        if fn_start:
            print(f"[ButtonMethods] FrameSetSize resolved via byte-pattern fallback @ 0x{fn_start:08X}")
            return fn_start

    print("[ButtonMethods] ERROR: FrameSetSize resolution failed")
    return 0

_frame_set_size_addr = _resolve_frameset_size()

FrameSetSize_Func = NativeFunction.from_address(
    name="FrameSetSize_Func",
    address=_frame_set_size_addr,
    prototype=Prototypes["Void_U32_VoidP"],
)


# ============================================================================
# FrameSetPosition — FrApi.cpp line 0x85c, EXE 0x0062f7f0
# Resolved via FindAssertion (survives EXE rebuilds).
# Prototype: void __cdecl FrameSetPosition(uint32 frameId, Coord2f* pos)
# ============================================================================

def _resolve_frameset_position() -> int:
    """Resolve FrameSetPosition via FindAssertion on FrApi.cpp anchor."""
    addr = Scanner.FindAssertion("FrApi.cpp", "frameId", 0x85c, 0)
    if addr:
        fn_start = Scanner.ToFunctionStart(addr, 0x100)
        if fn_start:
            print(f"[ButtonMethods] FrameSetPosition resolved @ 0x{fn_start:08X}")
            return fn_start

    # Fallback: byte pattern from known EXE build 06-14
    addr = Scanner.Find(
        b"\xFF\x75\x0C\x8B\x4D\x08\xE8",
        "xxxxxxx",
        0, ScannerSection.TEXT,
    )
    if addr:
        fn_start = Scanner.FunctionFromNearCall(addr + 2, True)
        if fn_start:
            print(f"[ButtonMethods] FrameSetPosition resolved via byte-pattern fallback @ 0x{fn_start:08X}")
            return fn_start

    print("[ButtonMethods] ERROR: FrameSetPosition resolution failed")
    return 0

_frame_set_pos_addr = _resolve_frameset_position()

FrameSetPosition_Func = NativeFunction.from_address(
    name="FrameSetPosition_Func",
    address=_frame_set_pos_addr,
    prototype=Prototypes["Void_U32_VoidP"],
)


# ============================================================================
# FrameMouseEnable — FrApi.cpp line 0x540
# Resolved via FindAssertion on FrApi.cpp anchor.
# Prototype: void __cdecl FrameMouseEnable(uint32 frameId, uint32 enable, uint32 unk)
# ============================================================================

def _resolve_frame_mouse_enable() -> int:
    """Resolve FrameMouseEnable via FindAssertion on FrApi.cpp anchor."""
    addr = Scanner.FindAssertion("FrApi.cpp", "frameId", 0x540, 0)
    if addr:
        fn_start = Scanner.ToFunctionStart(addr, 0x100)
        if fn_start:
            print(f"[ButtonMethods] FrameMouseEnable resolved @ 0x{fn_start:08X}")
            return fn_start

    # Fallback: byte pattern from known EXE build 06-14
    addr = Scanner.Find(
        b"\x8D\x88\x94\x00\x00\x00\xFF\x75\x10\xFF\x75\x0C",
        "xxx???xxxxxx",
        0, ScannerSection.TEXT,
    )
    if addr:
        fn_start = Scanner.ToFunctionStart(addr, 0x100)
        if fn_start:
            print(f"[ButtonMethods] FrameMouseEnable resolved via byte-pattern fallback @ 0x{fn_start:08X}")
            return fn_start

    print("[ButtonMethods] WARNING: FrameMouseEnable resolution failed (non-critical)")
    return 0

_frame_mouse_enable_addr = _resolve_frame_mouse_enable()

FrameMouseEnable_Func = NativeFunction.from_address(
    name="FrameMouseEnable_Func",
    address=_frame_mouse_enable_addr,
    prototype=Prototypes["Void_U32_U32_U32_U32"],
)


# ============================================================================
# FrameNewSubclass — reusable from PlayerMethods or resolved locally
# ============================================================================

def _resolve_frame_new_subclass() -> int:
    """Resolve FrameNewSubclass via FindAssertion on FrApi.cpp, line 0x467."""
    addr = Scanner.FindAssertion("FrApi.cpp", "frameId", 0x467, 0)
    if addr:
        fn_start = Scanner.ToFunctionStart(addr, 0x100)
        if fn_start:
            print(f"[ButtonMethods] FrameNewSubclass resolved @ 0x{fn_start:08X}")
            return fn_start

    # Fallback: byte pattern from known EXE build
    addr = Scanner.Find(
        b"\x8D\xB8\xA8\x00\x00\x00\x8B\xCF",
        "xxxxxxxx",
        -0x2D, ScannerSection.TEXT,
    )
    if addr:
        print(f"[ButtonMethods] FrameNewSubclass resolved via byte-pattern fallback @ 0x{addr:08X}")
        return addr

    print("[ButtonMethods] WARNING: FrameNewSubclass resolution failed")
    return 0

_frame_new_subclass_addr = _resolve_frame_new_subclass()

FrameNewSubclass_Func = NativeFunction.from_address(
    name="FrameNewSubclass_Func",
    address=_frame_new_subclass_addr,
    prototype=Prototypes["U32_U32_U32_U32"],
)


# ============================================================================
# Public API
# ============================================================================

# Dialog subclass type address for FrameNewSubclass.
# In WASM this is &DAT_ram_00000aed = function table index 0x0aed.
# In x86 EXE, the equivalent type address needs to be resolved.
# Currently using DlgMsgProc function pointer as Approach B fallback.
# Set to 0 to disable click support (Approach C).
#
# TODO: Find the EXE data address for the dialog subclass type.
#       DialogShow calls FrameNewSubclass(frameId, &DAT_ram_00000aed, flags).
#       Extract the immediate value from the EXE instruction stream.
DIALOG_SUBCLASS_TYPE_ADDR: int = 0x00851180  # Ui_CompositeRootControlProc (CRProc)
# Resolved 2026-06-19: DialogShow @ EXE 0x004dc1b0 →
#   Ui_AttachCurrentHandlerSlot(frame, 0x851180, pvVar5)
# WARNING: GWUI.CreateWindow ALREADY attaches CRProc via FrameNewSubclass.
# Calling FrameNewSubclass again with this address DOUBLE-SUBCLASSES → CRASH.
# Only use if creating a BARE frame WITHOUT GWUI.CreateWindow.


class ButtonMethods:
    """
    Create native GW buttons using the CtlBtnProc (engine-level) FrameProc.

    All calls are automatically enqueued to the game thread via NativeFunction.
    EXE build: 06-14-2026.

    Path B — Flat Engine Button:
        1. FrameCreate(parent, flags, childIdx, CtlBtnProc, userData, label)
        2. FrameSetSize(buttonId, width, height)          ← fixes thin strip
        3. CtlBtnSetTextLiteral(buttonId, text)           ← sets caption
        4. [Optional] FrameNewSubclass(parent, dialogType, 0) ← enables clicks
        5. FrameMouseEnable(buttonId, 1, 0)
        6. FrameSetPosition(buttonId, x, y)
    """

    # ── Low-level NativeFunction wrappers (all Game.enqueue'd) ──────────

    @staticmethod
    def frame_set_size(
        frame_id: int,
        width: float,
        height: float,
    ) -> None:
        """Set a frame's dimensions via native FrameSetSize."""
        def _action():
            if not FrameSetSize_Func.is_valid():
                print("[ButtonMethods] FrameSetSize_Func not resolved")
                return
            coord = Coord2f(width, height)
            FrameSetSize_Func.directCall(
                ctypes.c_uint32(frame_id),
                ctypes.cast(ctypes.byref(coord), ctypes.c_void_p),
            )
        Game.enqueue(_action)

    @staticmethod
    def frame_set_position(
        frame_id: int,
        x: float,
        y: float,
    ) -> None:
        """Set a frame's position via native FrameSetPosition."""
        def _action():
            if not FrameSetPosition_Func.is_valid():
                print("[ButtonMethods] FrameSetPosition_Func not resolved")
                return
            coord = Coord2f(x, y)
            FrameSetPosition_Func.directCall(
                ctypes.c_uint32(frame_id),
                ctypes.cast(ctypes.byref(coord), ctypes.c_void_p),
            )
        Game.enqueue(_action)

    @staticmethod
    def frame_mouse_enable(
        frame_id: int,
        enable: bool = True,
    ) -> None:
        """Enable/disable mouse input on a frame via native FrameMouseEnable."""
        def _action():
            if not FrameMouseEnable_Func.is_valid():
                print("[ButtonMethods] FrameMouseEnable_Func not resolved")
                return
            FrameMouseEnable_Func.directCall(
                ctypes.c_uint32(frame_id),
                ctypes.c_uint32(1 if enable else 0),
                ctypes.c_uint32(0),
                ctypes.c_uint32(0),
            )
        Game.enqueue(_action)

    @staticmethod
    def frame_new_subclass(
        frame_id: int,
        subclass_proc: int,
        msg_id: int = 0,
    ) -> None:
        """
        Register a subclass handler on a frame for OnFrameNotify dispatch.

        This is the CRITICAL missing piece for click support:
          - Button click → ICtlBtn::Click → FrameMsgNotifyParent(7 or 8)
          - Parent must have OnFrameNotify handler (added via dialog subclass)

        Args:
            frame_id:      Parent frame that should receive click notifications.
            subclass_proc: Handler function pointer or type address.
                           For dialog subclass, this should be &DAT_ram_00000aed
                           in WASM (or its EXE data-address equivalent).
            msg_id:        Message filter (0 = all messages).
        """
        def _action():
            if not FrameNewSubclass_Func.is_valid():
                print("[ButtonMethods] FrameNewSubclass_Func not resolved")
                return
            if not subclass_proc:
                print("[ButtonMethods] FrameNewSubclass skipped — no subclass_proc")
                return
            FrameNewSubclass_Func.directCall(
                ctypes.c_uint32(frame_id),
                ctypes.c_uint32(subclass_proc),
                ctypes.c_uint32(msg_id),
            )
        Game.enqueue(_action)

    # ── Convenience: Flat Button Creation ────────────────────────────────

    @staticmethod
    def create_flat_button_with_click(
        parent_frame_id: int,
        component_flags: int = 0x40000,   # IME-style: creates with flat background
        child_index: int = 0,
        label_text: str = "",
        width: float = 100.0,
        height: float = 24.0,
        pos_x: float = 10.0,
        pos_y: float = 10.0,
        enable_click: bool = False,
    ) -> None:
        """
        Create a flat engine button with proper dimensions and optional click support.

        This is the COMPLETE Path B implementation from the button-rendering-pipeline
        consensus.  It chains:
          1. FrameCreate with CtlBtnProc callback
          2. FrameSetSize to fix the "thin strip" rendering issue
          3. CtlBtnSetTextLiteral for the button caption
          4. FrameSetPosition for placement
          5. FrameMouseEnable for mouse input
          6. [Optional] FrameNewSubclass on parent for OnFrameNotify → click support

        Args:
            parent_frame_id:  Frame ID of the parent to attach to.
            component_flags:  Creation flags. Default 0x40000 (IME-style, flat bg).
            child_index:      Child ordering index.
            label_text:       Button caption text.
            width:            Button width in pixels (default 100).
            height:           Button height in pixels (default 24).
            pos_x:            X position within parent.
            pos_y:            Y position within parent.
            enable_click:     If True, calls FrameNewSubclass on the parent with
                              the dialog subclass type to enable OnFrameNotify
                              dispatch for button click notifications.
                              NOTE: Requires DIALOG_SUBCLASS_TYPE_ADDR to be set
                              to a valid type address (currently 0 = disabled).

        Note:
            This is fire-and-forget — all calls are enqueued to the game thread.
            The button's frame ID is NOT returned synchronously.
            Use UIManager.GetChildFrameIDs(parent_frame_id) to find the button
            after creation.

        EXE build: 06-14-2026.
        """
        def _action():
            if not CtlBtnProc_Callback.is_valid():
                raise RuntimeError("CtlBtnProc_Callback not resolved")

            cb_addr = CtlBtnProc_Callback.func_ptr
            label_buf = ctypes.create_unicode_buffer(label_text) if label_text else None
            label_ptr = ctypes.cast(label_buf, ctypes.c_void_p).value if label_buf else 0

            # Step 1: Create the button frame via FrameCreate with CtlBtnProc
            frame_id = FrameCreate_Func.directCall(
                ctypes.c_uint32(parent_frame_id),
                ctypes.c_uint32(component_flags),
                ctypes.c_uint32(child_index),
                ctypes.c_uint32(cb_addr),
                ctypes.c_uint32(0),      # user_param = NULL
                ctypes.c_uint32(label_ptr),
            )

            if not frame_id:
                print("[ButtonMethods] FrameCreate returned 0 — button creation failed")
                return

            print(f"[ButtonMethods] Flat button created with frame_id={frame_id}")

            # Step 2: Fix the thin strip — set dimensions
            if FrameSetSize_Func.is_valid() and width > 0 and height > 0:
                coord = Coord2f(width, height)
                FrameSetSize_Func.directCall(
                    ctypes.c_uint32(frame_id),
                    ctypes.cast(ctypes.byref(coord), ctypes.c_void_p),
                )

            # Step 3: Set caption text (after creation)
            if label_text and CtlBtnSetTextLiteral_Func.is_valid():
                CtlBtnSetTextLiteral_Func.directCall(
                    ctypes.c_uint32(frame_id),
                    label_buf,
                )

            # Step 4: Set position
            if FrameSetPosition_Func.is_valid():
                coord = Coord2f(pos_x, pos_y)
                FrameSetPosition_Func.directCall(
                    ctypes.c_uint32(frame_id),
                    ctypes.cast(ctypes.byref(coord), ctypes.c_void_p),
                )

            # Step 5: Enable mouse input
            if FrameMouseEnable_Func.is_valid():
                FrameMouseEnable_Func.directCall(
                    ctypes.c_uint32(frame_id),
                    ctypes.c_uint32(1),
                    ctypes.c_uint32(0),
                    ctypes.c_uint32(0),
                )

            # Step 6: [Optional] Add OnFrameNotify to parent for click support
            if enable_click and DIALOG_SUBCLASS_TYPE_ADDR:
                if FrameNewSubclass_Func.is_valid():
                    FrameNewSubclass_Func.directCall(
                        ctypes.c_uint32(parent_frame_id),
                        ctypes.c_uint32(DIALOG_SUBCLASS_TYPE_ADDR),
                        ctypes.c_uint32(0),
                    )
                    print(f"[ButtonMethods] FrameNewSubclass called on parent {parent_frame_id} — click support enabled")

        Game.enqueue(_action)

    # ── Legacy API (preserved for backward compatibility) ───────────────

    @staticmethod
    def create_native_button(
        parent_frame_id: int,
        component_flags: int = 0x40000,
        child_index: int = 0,
        label_text: str = "",
    ) -> None:
        """
        Create a native GW button inside a parent frame using CtlBtnProc.

        Legacy wrapper — calls create_flat_button_with_click with default sizing
        and click=False for backward compatibility.

        EXE build: 06-14-2026.
        """
        ButtonMethods.create_flat_button_with_click(
            parent_frame_id=parent_frame_id,
            component_flags=component_flags,
            child_index=child_index,
            label_text=label_text,
            enable_click=False,
        )

    @staticmethod
    def create_native_button_sync(
        parent_frame_id: int,
        component_flags: int = 0x40000,
        child_index: int = 0,
        label_text: str = "",
    ) -> Optional[int]:
        """
        Synchronous version — ONLY call from game thread context.

        Returns the new button's frame ID, or 0 on failure.
        This calls directCall WITHOUT Game.enqueue, so it MUST run on
        the game thread. Use from rendercallback/gameloop hooks only.

        EXE build: 06-14-2026.
        """
        if not CtlBtnProc_Callback.is_valid():
            return None

        cb_addr = CtlBtnProc_Callback.func_ptr
        label_buf = ctypes.create_unicode_buffer(label_text) if label_text else None
        label_ptr = ctypes.cast(label_buf, ctypes.c_void_p).value if label_buf else 0

        frame_id = FrameCreate_Func.directCall(
            ctypes.c_uint32(parent_frame_id),
            ctypes.c_uint32(component_flags),
            ctypes.c_uint32(child_index),
            ctypes.c_uint32(cb_addr),
            ctypes.c_uint32(0),
            ctypes.c_uint32(label_ptr),
        )

        if frame_id and label_text:
            CtlBtnSetTextLiteral_Func.directCall(
                ctypes.c_uint32(frame_id),
                label_buf,
            )

        return frame_id
