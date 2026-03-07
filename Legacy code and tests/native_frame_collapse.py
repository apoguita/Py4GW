import ctypes

import Py4GW
import PyImGui
from Py4GWCoreLib import GWContext, UIManager
from Py4GWCoreLib.Scanner import Scanner
from Py4GWCoreLib.native_src.internals.native_function import NativeFunction
from Py4GWCoreLib.native_src.internals.prototypes import NativeFunctionPrototype


MODULE_NAME = "Native Frame Collapse"
WINDOW_OPEN = True
DRAW_OUTLINES = True

DEVTEXT_LABEL = "DevText"
CLONE_LABEL = "PyCollapsedClone"
CLONE_PARENT_ID = 9

ORIGINAL_FRAME_ID = 0
ORIGINAL_FRAME_VISIBLE = False
CLONE_FRAME_ID = 0
CLONE_FRAME_VISIBLE = False

LAST_STATUS = "idle"
LAST_SIZE_STATUS = "idle"
LAST_ADDED_FRAME_IDS: list[int] = []
LAST_ADDED_SUBTREE_ROOTS: list[int] = []
LAST_BEFORE_SNAPSHOT: dict[int, dict[str, object]] = {}

PENDING_CLONE_CREATE = False
PENDING_COLLAPSE_APPLY = False
PENDING_COLLAPSE_OBSERVE = False
LAST_COLLAPSE_BEFORE_RECT = None

LAST_CLONE_SLOT = 0

DEVTEXT_DIALOG_PROC_CACHED = 0
FRAME_ANCHOR_NATIVE_CACHED = None
FRAME_SIZE_NATIVE_CACHED = None

LAST_RESIZE_ANCHOR_PAIR = None
LAST_RESIZE_SIZE_PAIR = None

ORIGINAL_OUTLINE_COLOR = 0xFF00FF00
ORIGINAL_FILL_COLOR = 0x2000FF00
CLONE_OUTLINE_COLOR = 0xFFFFFFFF
CLONE_FILL_COLOR = 0x20FFFFFF


def _snapshot_frames() -> dict[int, dict[str, object]]:
    snapshot: dict[int, dict[str, object]] = {}
    for fid in UIManager.GetFrameArray():
        frame_id = int(fid)
        try:
            frame = UIManager.GetFrameByID(frame_id)
        except Exception:
            continue
        snapshot[frame_id] = {
            "parent_id": int(frame.parent_id),
            "child_offset_id": int(frame.child_offset_id),
            "is_created": bool(frame.is_created),
            "is_visible": bool(frame.is_visible),
            "type": int(frame.type),
            "template_type": int(frame.template_type),
        }
    return snapshot


def _collect_child_ids(parent_id: int) -> list[int]:
    child_ids: list[int] = []
    for fid in UIManager.GetFrameArray():
        frame_id = int(fid)
        try:
            frame = UIManager.GetFrameByID(frame_id)
        except Exception:
            continue
        if int(frame.parent_id) == parent_id:
            child_ids.append(frame_id)
    child_ids.sort()
    return child_ids


def _format_position(frame: object) -> str:
    try:
        pos = getattr(frame, "position")
    except Exception:
        return "<no-position>"

    coords: list[str] = []
    for attr in ("left", "top", "right", "bottom", "x", "y", "x1", "y1"):
        if hasattr(pos, attr):
            try:
                coords.append(f"{attr}={getattr(pos, attr)!r}")
            except Exception:
                pass
    return "{" + ", ".join(coords) + "}" if coords else "<empty-position>"


def _log_frame_layout(frame_id: int, label: str) -> None:
    if frame_id <= 0:
        print(f"[{MODULE_NAME}] {label} frame_id=0")
        return
    try:
        frame = UIManager.GetFrameByID(frame_id)
    except Exception as exc:
        print(f"[{MODULE_NAME}] {label} resolve error: {exc}")
        return

    children = _collect_child_ids(frame_id)
    print(
        f"[{MODULE_NAME}] {label} "
        f"frame_id={frame_id} parent_id={int(frame.parent_id)} "
        f"child_offset_id={int(frame.child_offset_id)} "
        f"type={int(frame.type)} template_type={int(frame.template_type)} "
        f"is_created={bool(frame.is_created)} is_visible={bool(frame.is_visible)} "
        f"child_count={len(children)} position={_format_position(frame)}"
    )


def _find_fanout_parent(frame_id: int) -> int:
    current = frame_id
    while current > 0:
        child_ids = _collect_child_ids(current)
        if len(child_ids) != 1:
            return current
        current = child_ids[0]
    return frame_id


def _find_primary_branch(frame_id: int) -> int:
    fanout_parent = _find_fanout_parent(frame_id)
    child_ids = _collect_child_ids(fanout_parent)
    if not child_ids:
        return 0

    preferred = []
    for child_id in child_ids:
        try:
            frame = UIManager.GetFrameByID(child_id)
        except Exception:
            continue
        if int(frame.child_offset_id) == 0:
            preferred.append(child_id)
    if preferred:
        return preferred[0]
    return child_ids[0]


def _get_primary_rect(frame_id: int) -> tuple[int, int, int, int] | None:
    primary_id = _find_primary_branch(frame_id)
    if primary_id <= 0:
        return None
    try:
        frame = UIManager.GetFrameByID(primary_id)
        pos = frame.position
        return (int(pos.left), int(pos.top), int(pos.right), int(pos.bottom))
    except Exception:
        return None


def _resolve_devtext_dialog_proc() -> int:
    global DEVTEXT_DIALOG_PROC_CACHED

    if DEVTEXT_DIALOG_PROC_CACHED > 0:
        return DEVTEXT_DIALOG_PROC_CACHED

    for xref_index in range(8):
        try:
            use_addr = int(Scanner.FindNthUseOfStringW("DlgDevText", xref_index, 0, 0))
        except Exception:
            use_addr = 0
        if use_addr <= 0:
            continue
        try:
            proc_addr = int(Scanner.ToFunctionStart(use_addr, 0x1200))
        except Exception:
            proc_addr = 0
        if proc_addr > 0:
            DEVTEXT_DIALOG_PROC_CACHED = proc_addr
            print(
                f"[{MODULE_NAME}] DevText dialog proc resolved "
                f"xref_index={xref_index} use=0x{use_addr:X} addr=0x{proc_addr:X}"
            )
            return DEVTEXT_DIALOG_PROC_CACHED

    return 0


def _resolve_native_frame_anchor_wrapper():
    global FRAME_ANCHOR_NATIVE_CACHED

    if FRAME_ANCHOR_NATIVE_CACHED is not None:
        return FRAME_ANCHOR_NATIVE_CACHED

    dialog_addr = _resolve_devtext_dialog_proc()
    if dialog_addr <= 0:
        FRAME_ANCHOR_NATIVE_CACHED = False
        print(f"[{MODULE_NAME}] native anchor wrapper resolve error: no ASLR anchor available")
        return None

    slide = dialog_addr - 0x00864170
    wrapper_addr = slide + 0x006108B0

    try:
        prototype = NativeFunctionPrototype(None, ctypes.c_uint32, ctypes.c_void_p)
        FRAME_ANCHOR_NATIVE_CACHED = NativeFunction.from_address(
            "Ui_SetFrameAnchorPair",
            wrapper_addr,
            prototype,
            report_success=False,
        )
        print(
            f"[{MODULE_NAME}] native anchor wrapper resolved "
            f"anchor=Ui_DevTextDialogProc@0x{dialog_addr:X} slide=0x{slide:X} addr=0x{wrapper_addr:X}"
        )
        return FRAME_ANCHOR_NATIVE_CACHED
    except Exception as exc:
        FRAME_ANCHOR_NATIVE_CACHED = False
        print(f"[{MODULE_NAME}] native anchor wrapper resolve error: {exc}")
        return None


def _resolve_native_frame_size_wrapper():
    global FRAME_SIZE_NATIVE_CACHED

    if FRAME_SIZE_NATIVE_CACHED is not None:
        return FRAME_SIZE_NATIVE_CACHED

    dialog_addr = _resolve_devtext_dialog_proc()
    if dialog_addr <= 0:
        FRAME_SIZE_NATIVE_CACHED = False
        print(f"[{MODULE_NAME}] native size wrapper resolve error: no ASLR anchor available")
        return None

    slide = dialog_addr - 0x00864170
    wrapper_addr = slide + 0x006109F0

    try:
        prototype = NativeFunctionPrototype(None, ctypes.c_uint32, ctypes.c_void_p)
        FRAME_SIZE_NATIVE_CACHED = NativeFunction.from_address(
            "Ui_SetFrameSizeScalars",
            wrapper_addr,
            prototype,
            report_success=False,
        )
        print(
            f"[{MODULE_NAME}] native size wrapper resolved "
            f"anchor=Ui_DevTextDialogProc@0x{dialog_addr:X} slide=0x{slide:X} addr=0x{wrapper_addr:X}"
        )
        return FRAME_SIZE_NATIVE_CACHED
    except Exception as exc:
        FRAME_SIZE_NATIVE_CACHED = False
        print(f"[{MODULE_NAME}] native size wrapper resolve error: {exc}")
        return None


def _open_devtext_window() -> None:
    try:
        context = GWContext.Char.GetContext()
        player_flags_before = int(context.player_flags)
        context.player_flags = player_flags_before | 0x8
        UIManager.Keypress(0x25, 0)
        player_flags_after = int(context.player_flags)
        print(
            f"[{MODULE_NAME}] original DevText keypress sent "
            f"player_flags_before=0x{player_flags_before:X} "
            f"player_flags_after=0x{player_flags_after:X}"
        )
        context.player_flags = player_flags_before
    except Exception as exc:
        print(f"[{MODULE_NAME}] original DevText keypress error: {exc}")


def _resolve_original_devtext() -> int:
    global ORIGINAL_FRAME_ID
    global ORIGINAL_FRAME_VISIBLE

    frame_id = int(UIManager.GetFrameIDByLabel(DEVTEXT_LABEL) or 0)
    if frame_id <= 0:
        print(f"[{MODULE_NAME}] original DevText open dispatch key=0x25")
        _open_devtext_window()
        frame_id = int(UIManager.GetFrameIDByLabel(DEVTEXT_LABEL) or 0)
    else:
        print(f"[{MODULE_NAME}] original DevText already open frame_id={frame_id}")

    if frame_id <= 0:
        print(f"[{MODULE_NAME}] original DevText unresolved")
        ORIGINAL_FRAME_ID = 0
        ORIGINAL_FRAME_VISIBLE = False
        return 0

    ORIGINAL_FRAME_ID = frame_id
    try:
        ORIGINAL_FRAME_VISIBLE = bool(UIManager.GetFrameByID(frame_id).is_visible)
    except Exception:
        ORIGINAL_FRAME_VISIBLE = False

    print(
        f"[{MODULE_NAME}] original DevText frame "
        f"frame_id={ORIGINAL_FRAME_ID} is_visible={ORIGINAL_FRAME_VISIBLE}"
    )
    _log_frame_layout(ORIGINAL_FRAME_ID, "original")
    return ORIGINAL_FRAME_ID


def _collect_used_child_slots(parent_id: int) -> set[int]:
    used: set[int] = set()
    for fid in UIManager.GetFrameArray():
        frame_id = int(fid)
        try:
            frame = UIManager.GetFrameByID(frame_id)
        except Exception:
            continue
        if int(frame.parent_id) == parent_id:
            used.add(int(frame.child_offset_id))
    return used


def _find_available_clone_slot(parent_frame_id: int) -> int:
    if parent_frame_id <= 0:
        return 0
    used = _collect_used_child_slots(parent_frame_id)
    for child_index in range(0x20, 0xFF):
        if child_index not in used:
            return child_index
    return 0


def _select_created_root(
    before: dict[int, dict[str, object]],
    after: dict[int, dict[str, object]],
    owner_frame_id: int,
) -> int:
    before_ids = set(before.keys())
    after_ids = set(after.keys())
    added_ids = sorted(after_ids - before_ids)
    if not added_ids:
        return 0

    added_set = set(added_ids)
    subtree_roots = [
        frame_id
        for frame_id in added_ids
        if int(after[frame_id]["parent_id"]) not in added_set
    ]

    preferred = [fid for fid in subtree_roots if int(after[fid]["parent_id"]) == owner_frame_id]
    if preferred:
        return preferred[0]
    if subtree_roots:
        return subtree_roots[0]
    return added_ids[0]


def _log_frame_diff(
    before: dict[int, dict[str, object]],
    after: dict[int, dict[str, object]],
    owner_frame_id: int,
) -> tuple[int, bool]:
    global LAST_ADDED_FRAME_IDS
    global LAST_ADDED_SUBTREE_ROOTS

    before_ids = set(before.keys())
    after_ids = set(after.keys())
    added_ids = sorted(after_ids - before_ids)
    LAST_ADDED_FRAME_IDS = list(added_ids)

    print(f"[{MODULE_NAME}] frame diff added={len(added_ids)} removed=0")
    for frame_id in added_ids:
        info = after[frame_id]
        print(
            f"[{MODULE_NAME}] added frame_id={frame_id} "
            f"parent_id={info['parent_id']} child_offset_id={info['child_offset_id']} "
            f"is_created={info['is_created']} is_visible={info['is_visible']} "
            f"type={info['type']} template_type={info['template_type']}"
        )

    added_set = set(added_ids)
    subtree_roots = [
        frame_id
        for frame_id in added_ids
        if int(after[frame_id]["parent_id"]) not in added_set
    ]
    LAST_ADDED_SUBTREE_ROOTS = list(subtree_roots)
    if subtree_roots:
        print(f"[{MODULE_NAME}] added subtree roots={subtree_roots}")

    selected = _select_created_root(before, after, owner_frame_id)
    selected_visible = bool(after.get(selected, {}).get("is_visible", False)) if selected > 0 else False
    print(f"[{MODULE_NAME}] selected created frame frame_id={selected} is_visible={selected_visible}")
    return selected, selected_visible


def _dispatch_clone_test() -> None:
    global LAST_STATUS
    global LAST_CLONE_SLOT
    global LAST_BEFORE_SNAPSHOT
    global PENDING_CLONE_CREATE

    if _resolve_original_devtext() <= 0:
        LAST_STATUS = "host_unresolved"
        return

    dialog_proc = _resolve_devtext_dialog_proc()
    if dialog_proc <= 0:
        LAST_STATUS = "dialog_proc_unresolved"
        print(f"[{MODULE_NAME}] clone abort: DevText dialog proc unresolved")
        return

    child_slot = _find_available_clone_slot(CLONE_PARENT_ID)
    if child_slot <= 0:
        LAST_STATUS = "clone_slot_unresolved"
        print(f"[{MODULE_NAME}] clone abort: no free child slot")
        return

    before = _snapshot_frames()
    print(f"[{MODULE_NAME}] before frame_count={len(before)}")

    LAST_CLONE_SLOT = child_slot
    print(
        f"[{MODULE_NAME}] component clone dispatch "
        f"parent={CLONE_PARENT_ID} flags=0x0 child_index=0x{child_slot:X} "
        f"callback=0x{dialog_proc:X} label='{CLONE_LABEL}'"
    )

    LAST_BEFORE_SNAPSHOT = before
    PENDING_CLONE_CREATE = True
    LAST_STATUS = "clone_enqueued"

    def _action() -> None:
        try:
            created = UIManager.CreateUIComponentByFrameId(
                CLONE_PARENT_ID,
                0,
                child_slot,
                dialog_proc,
                "",
                CLONE_LABEL,
            )
            print(f"[{MODULE_NAME}] component clone enqueued returned_frame={created}")
        except Exception as exc:
            print(f"[{MODULE_NAME}] component clone error: {exc}")

    Py4GW.Game.enqueue(_action)
    print(f"[{MODULE_NAME}] component clone enqueued")


def _apply_collapse_to_clone() -> None:
    global LAST_SIZE_STATUS
    global PENDING_COLLAPSE_APPLY
    global PENDING_COLLAPSE_OBSERVE
    global LAST_RESIZE_ANCHOR_PAIR
    global LAST_RESIZE_SIZE_PAIR
    global LAST_COLLAPSE_BEFORE_RECT

    PENDING_COLLAPSE_APPLY = False

    if ORIGINAL_FRAME_ID <= 0 or CLONE_FRAME_ID <= 0:
        LAST_SIZE_STATUS = "collapse_skipped"
        print(f"[{MODULE_NAME}] collapse apply skipped: original/clone unresolved")
        return

    original_rect = _get_primary_rect(ORIGINAL_FRAME_ID)
    clone_rect_before = _get_primary_rect(CLONE_FRAME_ID)
    if not original_rect or not clone_rect_before:
        LAST_SIZE_STATUS = "collapse_rect_unavailable"
        print(f"[{MODULE_NAME}] collapse apply aborted: primary rect unavailable")
        return

    width = abs(original_rect[2] - original_rect[0])
    height = abs(original_rect[3] - original_rect[1])
    print(
        f"[{MODULE_NAME}] collapse before "
        f"original_primary_rect={original_rect} clone_primary_rect={clone_rect_before} "
        f"width={width} height={height}"
    )
    LAST_COLLAPSE_BEFORE_RECT = clone_rect_before

    native_anchor = _resolve_native_frame_anchor_wrapper()
    native_size = _resolve_native_frame_size_wrapper()
    if not native_anchor or not native_size:
        LAST_SIZE_STATUS = "collapse_native_unresolved"
        print(f"[{MODULE_NAME}] collapse apply aborted: native wrappers unresolved")
        return

    try:
        LAST_RESIZE_ANCHOR_PAIR = (ctypes.c_uint32 * 2)(0, 0)
        LAST_RESIZE_SIZE_PAIR = (ctypes.c_uint32 * 2)(int(width), int(height))
        anchor_ptr = ctypes.cast(LAST_RESIZE_ANCHOR_PAIR, ctypes.c_void_p).value
        size_ptr = ctypes.cast(LAST_RESIZE_SIZE_PAIR, ctypes.c_void_p).value

        print(
            f"[{MODULE_NAME}] collapse dispatch "
            f"frame={CLONE_FRAME_ID} current_clone_rect={clone_rect_before} "
            f"anchor=(0, 0) width={width} height={height}"
        )
        native_anchor(CLONE_FRAME_ID, anchor_ptr)
        native_size(CLONE_FRAME_ID, size_ptr)
        LAST_SIZE_STATUS = "collapse_dispatched"
        PENDING_COLLAPSE_OBSERVE = True
        print(f"[{MODULE_NAME}] collapse enqueued")
    except Exception as exc:
        LAST_SIZE_STATUS = "collapse_dispatch_error"
        print(f"[{MODULE_NAME}] collapse error: {exc}")


def _observe_pending_clone_create() -> None:
    global CLONE_FRAME_ID
    global CLONE_FRAME_VISIBLE
    global LAST_STATUS
    global PENDING_CLONE_CREATE
    global LAST_BEFORE_SNAPSHOT
    global PENDING_COLLAPSE_APPLY
    global PENDING_COLLAPSE_OBSERVE

    if not PENDING_CLONE_CREATE:
        if PENDING_COLLAPSE_APPLY:
            _apply_collapse_to_clone()
        elif PENDING_COLLAPSE_OBSERVE:
            clone_rect_after = _get_primary_rect(CLONE_FRAME_ID) if CLONE_FRAME_ID > 0 else None
            before_rect = LAST_COLLAPSE_BEFORE_RECT
            original_rect = _get_primary_rect(ORIGINAL_FRAME_ID) if ORIGINAL_FRAME_ID > 0 else None
            changed_vs_before = clone_rect_after != before_rect if clone_rect_after and before_rect else None
            changed_vs_original = clone_rect_after != original_rect if clone_rect_after and original_rect else None
            if changed_vs_before is True:
                LAST_SIZE_STATUS = "collapse_changed"
            elif changed_vs_before is False:
                LAST_SIZE_STATUS = "collapse_unchanged"
            else:
                LAST_SIZE_STATUS = "collapse_observed"
            PENDING_COLLAPSE_OBSERVE = False
            print(f"[{MODULE_NAME}] collapse after clone_primary_rect={clone_rect_after}")
            if changed_vs_before is True:
                print(f"[{MODULE_NAME}] collapse result: clone primary rect changed vs before")
            elif changed_vs_before is False:
                print(f"[{MODULE_NAME}] collapse result: clone primary rect unchanged vs before")
            if changed_vs_original is True:
                print(f"[{MODULE_NAME}] collapse compare: clone still differs from original")
            elif changed_vs_original is False:
                print(f"[{MODULE_NAME}] collapse compare: clone matches original")
        return

    after = _snapshot_frames()
    selected, selected_visible = _log_frame_diff(LAST_BEFORE_SNAPSHOT, after, CLONE_PARENT_ID)

    if not LAST_ADDED_FRAME_IDS:
        return

    CLONE_FRAME_ID = selected
    CLONE_FRAME_VISIBLE = selected_visible
    LAST_STATUS = "clone_observed"
    PENDING_CLONE_CREATE = False
    LAST_BEFORE_SNAPSHOT = {}
    PENDING_COLLAPSE_APPLY = True

    print(
        f"[{MODULE_NAME}] component clone result "
        f"selected_created={CLONE_FRAME_ID} selected_visible={CLONE_FRAME_VISIBLE} "
        f"added_count={len(LAST_ADDED_FRAME_IDS)}"
    )
    _log_frame_layout(CLONE_FRAME_ID, "clone")


def update_frame_state() -> None:
    global ORIGINAL_FRAME_ID
    global ORIGINAL_FRAME_VISIBLE
    global CLONE_FRAME_ID
    global CLONE_FRAME_VISIBLE

    _observe_pending_clone_create()

    frame_ids = {int(fid) for fid in UIManager.GetFrameArray()}

    if ORIGINAL_FRAME_ID > 0:
        if ORIGINAL_FRAME_ID not in frame_ids:
            ORIGINAL_FRAME_ID = 0
            ORIGINAL_FRAME_VISIBLE = False
            print(f"[{MODULE_NAME}] original DevText frame no longer present")
        else:
            try:
                ORIGINAL_FRAME_VISIBLE = bool(UIManager.GetFrameByID(ORIGINAL_FRAME_ID).is_visible)
            except Exception:
                ORIGINAL_FRAME_ID = 0
                ORIGINAL_FRAME_VISIBLE = False

    if CLONE_FRAME_ID > 0:
        if CLONE_FRAME_ID not in frame_ids:
            CLONE_FRAME_ID = 0
            CLONE_FRAME_VISIBLE = False
            print(f"[{MODULE_NAME}] selected created frame no longer present")
        else:
            try:
                CLONE_FRAME_VISIBLE = bool(UIManager.GetFrameByID(CLONE_FRAME_ID).is_visible)
            except Exception:
                CLONE_FRAME_ID = 0
                CLONE_FRAME_VISIBLE = False


def draw_debug_outlines() -> None:
    update_frame_state()

    if not DRAW_OUTLINES:
        return

    ui = UIManager()
    if ORIGINAL_FRAME_ID > 0 and UIManager.IsFrameCreated(ORIGINAL_FRAME_ID):
        ui.DrawFrame(ORIGINAL_FRAME_ID, ORIGINAL_FILL_COLOR)
        outline = ORIGINAL_OUTLINE_COLOR if ORIGINAL_FRAME_VISIBLE else 0xFFAAAAAA
        ui.DrawFrameOutline(ORIGINAL_FRAME_ID, outline, 4.0)

    if CLONE_FRAME_ID > 0 and UIManager.IsFrameCreated(CLONE_FRAME_ID):
        ui.DrawFrame(CLONE_FRAME_ID, CLONE_FILL_COLOR)
        outline = CLONE_OUTLINE_COLOR if CLONE_FRAME_VISIBLE else 0xFFAAAAAA
        ui.DrawFrameOutline(CLONE_FRAME_ID, outline, 6.0)


def run_collapse_test() -> None:
    def _action() -> None:
        global LAST_STATUS

        print(f"[{MODULE_NAME}] diagnostic begin collapse_test")
        LAST_STATUS = "collapse_test"
        _dispatch_clone_test()
        print(f"[{MODULE_NAME}] diagnostic end")

    Py4GW.Game.enqueue(_action)


def draw_window() -> None:
    global DRAW_OUTLINES

    PyImGui.text("Clone DevText and collapse the cloned window via anchor+size.")

    if PyImGui.button("Run Collapse Test"):
        run_collapse_test()

    DRAW_OUTLINES = PyImGui.checkbox("Draw Outlines", DRAW_OUTLINES)

    PyImGui.text(f"Last status: {LAST_STATUS}")
    PyImGui.text(f"Size Status: {LAST_SIZE_STATUS}")
    PyImGui.text(f"Original DevText: {ORIGINAL_FRAME_ID} visible={ORIGINAL_FRAME_VISIBLE}")
    PyImGui.text(f"Clone Parent: {CLONE_PARENT_ID}")
    PyImGui.text(f"Clone Slot: 0x{LAST_CLONE_SLOT:X}")
    PyImGui.text(f"Created Clone: {CLONE_FRAME_ID} visible={CLONE_FRAME_VISIBLE}")
    PyImGui.text(f"Added Frames: {LAST_ADDED_FRAME_IDS}")
    PyImGui.text(f"Added Roots: {LAST_ADDED_SUBTREE_ROOTS}")


def main() -> None:
    global WINDOW_OPEN
    if not WINDOW_OPEN:
        return

    draw_debug_outlines()

    flags = PyImGui.WindowFlags.AlwaysAutoResize
    WINDOW_OPEN = PyImGui.begin(MODULE_NAME, WINDOW_OPEN, flags)
    if WINDOW_OPEN:
        draw_window()
    PyImGui.end()


if __name__ == "__main__":
    main()
