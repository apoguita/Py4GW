import Py4GW
import PyUIManager
from Py4GWCoreLib import GWContext, PyImGui, UIManager
from Py4GWCoreLib.Scanner import Scanner
from Py4GWCoreLib.native_src.internals.native_function import NativeFunction
from Py4GWCoreLib.native_src.internals.prototypes import NativeFunctionPrototype
import ctypes


MODULE_NAME = "Native UI Test"
WINDOW_OPEN = True
DRAW_OUTLINES = True
DEVTEXT_LABEL = "DevText"

HOST_FRAME_ID = 0
HOST_VISIBLE = False
ORIGINAL_FRAME_ID = 0
ORIGINAL_FRAME_VISIBLE = False
CREATED_FRAME_ID = 0
CREATED_FRAME_VISIBLE = False

LAST_ADDED_FRAME_IDS: list[int] = []
LAST_REMOVED_FRAME_IDS: list[int] = []
LAST_ADDED_SUBTREE_ROOTS: list[int] = []
LAST_TEST_STATUS = "idle"

LAST_CLONE_PARENT = 9
LAST_CLONE_SLOT = 0
LAST_CLONE_LABEL = "PyDevTextClone"

PENDING_CLONE_CREATE = False
PENDING_BEFORE_SNAPSHOT: dict[int, dict[str, object]] = {}
PENDING_SIZE_APPLY = False
PENDING_SIZE_OBSERVE = False
PENDING_NEXT_CLONE_STAGE = False
LAST_SIZE_STATUS = "idle"
CURRENT_SIZE_PHASE = ""
# The call-combination matrix is complete:
# - anchor_only: no effect
# - notify_only: no effect
# - size_only: no effect
# - size_plus_notify: no effect
# - anchor_plus_size: operative
# The anchor sweep is also complete: the tested anchor presets all collapsed the
# clone. The remaining variable is the size-pair encoding, so keep one fixed
# nonzero-x anchor and sweep size pairs only.
SIZE_TEST_PHASES = (
    "size_500_500",
    "size_452_500",
    "size_500_100",
    "size_452_100",
    "size_452_1",
)
PENDING_SIZE_SEQUENCE: list[str] = []
LAST_SIZE_BEFORE_RECT = None

DEVTEXT_DIALOG_PROC_CACHED = 0
CREATE_COMPONENT_ADDR_CACHED = 0
FRAME_SIZE_NATIVE_CACHED = None
FRAME_ANCHOR_NATIVE_CACHED = None
FRAME_NOTIFY_NATIVE_CACHED = None

LAST_RESIZE_ANCHOR_PAIR = None
LAST_RESIZE_SIZE_PAIR = None

ORIGINAL_OUTLINE_COLOR = 0xFF00FF00
ORIGINAL_FILL_COLOR = 0x3000FF00
CREATED_OUTLINE_COLOR = 0xFFFFFFFF
CREATED_FILL_COLOR = 0x30FFFFFF


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


def _resolve_create_component_addr() -> int:
    global CREATE_COMPONENT_ADDR_CACHED

    if CREATE_COMPONENT_ADDR_CACHED > 0:
        return CREATE_COMPONENT_ADDR_CACHED

    try:
        use_addr = int(Scanner.Find(b"\x33\xD2\x89\x45\x08\xB9\xC8\x01\x00\x00", "xxxxxxxxxx", 0, 0))
    except Exception:
        use_addr = 0
    if use_addr <= 0:
        return 0

    try:
        func_addr = int(Scanner.ToFunctionStart(use_addr, 0xFF))
    except Exception:
        func_addr = 0
    if func_addr <= 0:
        return 0

    CREATE_COMPONENT_ADDR_CACHED = func_addr
    print(f"[{MODULE_NAME}] CreateUIComponent resolved use=0x{use_addr:X} addr=0x{func_addr:X}")
    return CREATE_COMPONENT_ADDR_CACHED


def _resolve_native_frame_size_wrapper():
    global FRAME_SIZE_NATIVE_CACHED

    if FRAME_SIZE_NATIVE_CACHED is not None:
        return FRAME_SIZE_NATIVE_CACHED

    # Prefer the DevText dialog proc as the ASLR anchor in this branch because it
    # is already resolved successfully for every clone test. Fall back to the
    # CreateUIComponent constructor signature if needed.
    slide = 0
    anchor_name = ""
    anchor_addr = 0

    dialog_addr = _resolve_devtext_dialog_proc()
    if dialog_addr > 0:
        # Static address from Ghidra for Ui_DevTextDialogProc.
        slide = dialog_addr - 0x00864170
        anchor_name = "Ui_DevTextDialogProc"
        anchor_addr = dialog_addr
    else:
        create_addr = _resolve_create_component_addr()
        if create_addr > 0:
            # Static address from Ghidra for Ui_CreateLabeledFrame /
            # CreateUIComponent in this build.
            slide = create_addr - 0x0060D2D0
            anchor_name = "Ui_CreateLabeledFrame"
            anchor_addr = create_addr
        else:
            FRAME_SIZE_NATIVE_CACHED = False
            print(f"[{MODULE_NAME}] native size wrapper resolve error: no ASLR anchor available")
            return None

    # Static address from Ghidra for Ui_SetFrameSizeScalars.
    size_addr = slide + 0x006109F0

    try:
        prototype = NativeFunctionPrototype(
            None,
            ctypes.c_uint32,
            ctypes.c_void_p,
        )
        FRAME_SIZE_NATIVE_CACHED = NativeFunction.from_address(
            "Ui_SetFrameSizeScalars",
            size_addr,
            prototype,
            report_success=False,
        )
        print(
            f"[{MODULE_NAME}] native size wrapper resolved "
            f"anchor={anchor_name}@0x{anchor_addr:X} slide=0x{slide:X} addr=0x{size_addr:X}"
        )
        return FRAME_SIZE_NATIVE_CACHED
    except Exception as exc:
        FRAME_SIZE_NATIVE_CACHED = False
        print(f"[{MODULE_NAME}] native size wrapper resolve error: {exc}")
        return None


def _resolve_native_frame_anchor_wrapper():
    global FRAME_ANCHOR_NATIVE_CACHED

    if FRAME_ANCHOR_NATIVE_CACHED is not None:
        return FRAME_ANCHOR_NATIVE_CACHED

    slide = 0
    anchor_name = ""
    anchor_addr = 0

    dialog_addr = _resolve_devtext_dialog_proc()
    if dialog_addr > 0:
        slide = dialog_addr - 0x00864170
        anchor_name = "Ui_DevTextDialogProc"
        anchor_addr = dialog_addr
    else:
        create_addr = _resolve_create_component_addr()
        if create_addr > 0:
            slide = create_addr - 0x0060D2D0
            anchor_name = "Ui_CreateLabeledFrame"
            anchor_addr = create_addr
        else:
            FRAME_ANCHOR_NATIVE_CACHED = False
            print(f"[{MODULE_NAME}] native anchor wrapper resolve error: no ASLR anchor available")
            return None

    anchor_wrapper_addr = slide + 0x006108B0

    try:
        prototype = NativeFunctionPrototype(
            None,
            ctypes.c_uint32,
            ctypes.c_void_p,
        )
        FRAME_ANCHOR_NATIVE_CACHED = NativeFunction.from_address(
            "Ui_SetFrameAnchorPair",
            anchor_wrapper_addr,
            prototype,
            report_success=False,
        )
        print(
            f"[{MODULE_NAME}] native anchor wrapper resolved "
            f"anchor={anchor_name}@0x{anchor_addr:X} slide=0x{slide:X} addr=0x{anchor_wrapper_addr:X}"
        )
        return FRAME_ANCHOR_NATIVE_CACHED
    except Exception as exc:
        FRAME_ANCHOR_NATIVE_CACHED = False
        print(f"[{MODULE_NAME}] native anchor wrapper resolve error: {exc}")
        return None


def _resolve_native_frame_notify_wrapper():
    global FRAME_NOTIFY_NATIVE_CACHED

    if FRAME_NOTIFY_NATIVE_CACHED is not None:
        return FRAME_NOTIFY_NATIVE_CACHED

    slide = 0
    anchor_name = ""
    anchor_addr = 0

    dialog_addr = _resolve_devtext_dialog_proc()
    if dialog_addr > 0:
        slide = dialog_addr - 0x00864170
        anchor_name = "Ui_DevTextDialogProc"
        anchor_addr = dialog_addr
    else:
        create_addr = _resolve_create_component_addr()
        if create_addr > 0:
            slide = create_addr - 0x0060D2D0
            anchor_name = "Ui_CreateLabeledFrame"
            anchor_addr = create_addr
        else:
            FRAME_NOTIFY_NATIVE_CACHED = False
            print(f"[{MODULE_NAME}] native notify wrapper resolve error: no ASLR anchor available")
            return None

    notify_wrapper_addr = slide + 0x00610D00

    try:
        prototype = NativeFunctionPrototype(
            None,
            ctypes.c_uint32,
            ctypes.c_uint32,
        )
        FRAME_NOTIFY_NATIVE_CACHED = NativeFunction.from_address(
            "Ui_ToggleFrameState0x200AndNotify",
            notify_wrapper_addr,
            prototype,
            report_success=False,
        )
        print(
            f"[{MODULE_NAME}] native notify wrapper resolved "
            f"anchor={anchor_name}@0x{anchor_addr:X} slide=0x{slide:X} addr=0x{notify_wrapper_addr:X}"
        )
        return FRAME_NOTIFY_NATIVE_CACHED
    except Exception as exc:
        FRAME_NOTIFY_NATIVE_CACHED = False
        print(f"[{MODULE_NAME}] native notify wrapper resolve error: {exc}")
        return None


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


def _is_descendant_of(frame_id: int, ancestor_id: int) -> bool:
    if frame_id <= 0 or ancestor_id <= 0 or frame_id == ancestor_id:
        return False

    current = frame_id
    visited: set[int] = set()
    frame_ids = {int(fid) for fid in UIManager.GetFrameArray()}

    while current > 0 and current not in visited and current in frame_ids:
        visited.add(current)
        try:
            frame = UIManager.GetFrameByID(current)
        except Exception:
            return False
        parent_id = int(frame.parent_id)
        if parent_id == ancestor_id:
            return True
        current = parent_id
    return False


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


def _get_child_rect_by_offset(frame_id: int, child_offset: int) -> tuple[int, int, int, int] | None:
    fanout_parent = _find_fanout_parent(frame_id)
    child_ids = _collect_child_ids(fanout_parent)
    for child_id in child_ids:
        try:
            frame = UIManager.GetFrameByID(child_id)
        except Exception:
            continue
        if int(frame.child_offset_id) != child_offset:
            continue
        pos = frame.position
        return (int(pos.left), int(pos.top), int(pos.right), int(pos.bottom))
    return None


def _resolve_ui_size_method(*names: str):
    for name in names:
        method = getattr(PyUIManager.UIManager, name, None)
        if callable(method):
            return method, name
        wrapper = getattr(UIManager, name, None)
        if callable(wrapper):
            return wrapper, f"UIManager.{name}"
    return None, ""


def _apply_clone_size_from_original() -> None:
    global LAST_SIZE_STATUS
    global PENDING_SIZE_APPLY
    global PENDING_SIZE_OBSERVE
    global LAST_RESIZE_ANCHOR_PAIR
    global LAST_RESIZE_SIZE_PAIR
    global CURRENT_SIZE_PHASE
    global LAST_SIZE_BEFORE_RECT
    global PENDING_SIZE_SEQUENCE

    PENDING_SIZE_APPLY = False

    if ORIGINAL_FRAME_ID <= 0 or CREATED_FRAME_ID <= 0:
        LAST_SIZE_STATUS = "size_skipped"
        print(f"[{MODULE_NAME}] size apply skipped: original/clone unresolved")
        return

    original_rect = _get_primary_rect(ORIGINAL_FRAME_ID)
    clone_rect_before = _get_primary_rect(CREATED_FRAME_ID)
    if not original_rect:
        LAST_SIZE_STATUS = "size_no_original_rect"
        print(f"[{MODULE_NAME}] size apply aborted: original primary rect unavailable")
        return
    if not clone_rect_before:
        LAST_SIZE_STATUS = "size_no_clone_rect"
        print(f"[{MODULE_NAME}] size apply aborted: clone primary rect unavailable")
        return

    width = abs(original_rect[2] - original_rect[0])
    height = abs(original_rect[3] - original_rect[1])
    print(
        f"[{MODULE_NAME}] size apply before "
        f"original_primary_rect={original_rect} clone_primary_rect={clone_rect_before} "
        f"width={width} height={height}"
    )
    LAST_SIZE_BEFORE_RECT = clone_rect_before

    if not PENDING_SIZE_SEQUENCE:
        LAST_SIZE_STATUS = "size_no_pending_phase"
        print(f"[{MODULE_NAME}] size apply skipped: no pending phase")
        return

    phase = PENDING_SIZE_SEQUENCE[0]

    native_anchor = _resolve_native_frame_anchor_wrapper()
    if not native_anchor:
        LAST_SIZE_STATUS = "size_anchor_unresolved"
        print(f"[{MODULE_NAME}] size apply aborted: native anchor wrapper unresolved")
        return

    native_size = _resolve_native_frame_size_wrapper()
    if not native_size:
        LAST_SIZE_STATUS = "size_method_unresolved"
        print(f"[{MODULE_NAME}] size apply aborted: native size wrapper unresolved")
        return

    _dispatch_size_phase(
        phase,
        original_rect,
        clone_rect_before,
        native_anchor,
        native_size,
        None,
    )


def _dispatch_size_phase(
    phase: str,
    original_rect: tuple[int, int, int, int],
    clone_rect_before: tuple[int, int, int, int],
    native_anchor,
    native_size,
    native_notify,
) -> None:
    global LAST_SIZE_STATUS
    global PENDING_SIZE_OBSERVE
    global LAST_RESIZE_SIZE_PAIR
    global CURRENT_SIZE_PHASE

    original_width = abs(original_rect[2] - original_rect[0])
    original_top = int(original_rect[1])
    aux_rect = _get_child_rect_by_offset(ORIGINAL_FRAME_ID, 3)
    aux_left = int(aux_rect[0]) if aux_rect else 456
    aux_top = int(aux_rect[1]) if aux_rect else original_top

    anchor_x = aux_left
    anchor_y = aux_top

    if phase == "size_500_500":
        target_width = 500
        target_height = 500
    elif phase == "size_452_500":
        target_width = original_width
        target_height = 500
    elif phase == "size_500_100":
        target_width = 500
        target_height = 100
    elif phase == "size_452_100":
        target_width = original_width
        target_height = 100
    elif phase == "size_452_1":
        target_width = original_width
        target_height = 1
    else:
        raise ValueError(f"Unknown size test phase: {phase}")

    try:
        LAST_RESIZE_ANCHOR_PAIR = (ctypes.c_uint32 * 2)(anchor_x, anchor_y)
        LAST_RESIZE_SIZE_PAIR = (ctypes.c_uint32 * 2)(int(target_width), int(target_height))
        anchor_ptr = ctypes.cast(LAST_RESIZE_ANCHOR_PAIR, ctypes.c_void_p).value
        size_ptr = ctypes.cast(LAST_RESIZE_SIZE_PAIR, ctypes.c_void_p).value

        print(
            f"[{MODULE_NAME}] size {phase} dispatch "
            f"frame={CREATED_FRAME_ID} "
            f"current_clone_rect={clone_rect_before} "
            f"anchor=({anchor_x}, {anchor_y}) "
            f"width={target_width} height={target_height}"
        )
        native_anchor(CREATED_FRAME_ID, anchor_ptr)
        native_size(CREATED_FRAME_ID, size_ptr)
        CURRENT_SIZE_PHASE = phase
        LAST_SIZE_STATUS = f"size_{phase}_dispatched"
        PENDING_SIZE_OBSERVE = True
        print(f"[{MODULE_NAME}] size {phase} enqueued")
    except Exception as exc:
        LAST_SIZE_STATUS = f"size_{phase}_dispatch_error"
        CURRENT_SIZE_PHASE = ""
        print(f"[{MODULE_NAME}] size {phase} error: {exc}")


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


def _resolve_host_frame() -> int:
    global HOST_FRAME_ID
    global HOST_VISIBLE
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
        print(
            f"[{MODULE_NAME}] host resolve failed: "
            f"label='{DEVTEXT_LABEL}' not found"
        )
        HOST_FRAME_ID = 0
        HOST_VISIBLE = False
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

    current = ORIGINAL_FRAME_ID
    for depth in range(1, 4):
        child_ids = _collect_child_ids(current)
        if len(child_ids) != 1:
            break
        current = child_ids[0]
        _log_frame_layout(current, f"original chain[{depth}]")

    fanout_children = _collect_child_ids(current)
    print(
        f"[{MODULE_NAME}] original fanout_parent={current} "
        f"children={fanout_children[:8]} total_children={len(fanout_children)}"
    )
    for idx, child_id in enumerate(fanout_children[:6]):
        _log_frame_layout(child_id, f"original child[{child_id}]")

    HOST_FRAME_ID = current
    HOST_VISIBLE = True
    return HOST_FRAME_ID


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


def _find_available_component_slot(parent_frame_id: int) -> int:
    if parent_frame_id <= 0:
        return 0
    used = _collect_used_child_slots(parent_frame_id)
    for child_index in range(0xFE, 0, -1):
        if child_index not in used:
            return child_index
    return 0


def _encode_component_label(label: str) -> str:
    return "\u0108\u0107" + label + "\u0001"


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

    visible_added = [fid for fid in added_ids if bool(after[fid]["is_visible"])]
    if visible_added:
        return visible_added[0]
    return added_ids[0]


def _log_frame_diff(
    before: dict[int, dict[str, object]],
    after: dict[int, dict[str, object]],
    owner_frame_id: int,
) -> tuple[int, bool]:
    global LAST_ADDED_FRAME_IDS
    global LAST_REMOVED_FRAME_IDS

    before_ids = set(before.keys())
    after_ids = set(after.keys())
    added_ids = sorted(after_ids - before_ids)
    removed_ids = sorted(before_ids - after_ids)
    LAST_ADDED_FRAME_IDS = list(added_ids)
    LAST_REMOVED_FRAME_IDS = list(removed_ids)

    print(f"[{MODULE_NAME}] frame diff added={len(added_ids)} removed={len(removed_ids)}")
    if not added_ids and not removed_ids:
        print(f"[{MODULE_NAME}] frame diff no changes detected")

    for frame_id in added_ids:
        info = after[frame_id]
        print(
            f"[{MODULE_NAME}] added frame_id={frame_id} "
            f"parent_id={info['parent_id']} child_offset_id={info['child_offset_id']} "
            f"is_created={info['is_created']} is_visible={info['is_visible']} "
            f"type={info['type']} template_type={info['template_type']}"
        )

    for frame_id in removed_ids:
        info = before[frame_id]
        print(
            f"[{MODULE_NAME}] removed frame_id={frame_id} "
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
    if subtree_roots:
        print(f"[{MODULE_NAME}] added subtree roots={subtree_roots}")

    selected = _select_created_root(before, after, owner_frame_id)
    selected_visible = bool(after.get(selected, {}).get("is_visible", False)) if selected > 0 else False
    print(f"[{MODULE_NAME}] selected created frame frame_id={selected} is_visible={selected_visible}")
    return selected, selected_visible


def _find_available_clone_slot(parent_frame_id: int) -> int:
    if parent_frame_id <= 0:
        return 0
    used = _collect_used_child_slots(parent_frame_id)
    for child_index in range(0x20, 0xFF):
        if child_index not in used:
            return child_index
    return 0


def _dispatch_clone_test() -> None:
    global LAST_TEST_STATUS
    global LAST_CLONE_PARENT
    global LAST_CLONE_SLOT
    global PENDING_BEFORE_SNAPSHOT
    global PENDING_CLONE_CREATE

    if _resolve_host_frame() <= 0:
        LAST_TEST_STATUS = "clone_host_unresolved"
        print(f"[{MODULE_NAME}] clone abort: original DevText unresolved")
        return

    dialog_proc = _resolve_devtext_dialog_proc()
    if dialog_proc <= 0:
        LAST_TEST_STATUS = "dialog_proc_unresolved"
        print(f"[{MODULE_NAME}] clone abort: DevText dialog proc unresolved")
        return

    clone_parent = 9
    child_slot = _find_available_clone_slot(clone_parent)
    if child_slot <= 0:
        LAST_TEST_STATUS = "clone_slot_unresolved"
        print(f"[{MODULE_NAME}] clone abort: no free child slot")
        return

    before = _snapshot_frames()
    print(f"[{MODULE_NAME}] before frame_count={len(before)}")

    LAST_CLONE_PARENT = clone_parent
    LAST_CLONE_SLOT = child_slot
    print(
        f"[{MODULE_NAME}] component clone dispatch "
        f"parent={clone_parent} flags=0x0 child_index=0x{child_slot:X} "
        f"callback=0x{dialog_proc:X} label='{LAST_CLONE_LABEL}'"
    )

    PENDING_BEFORE_SNAPSHOT = before
    PENDING_CLONE_CREATE = True
    LAST_TEST_STATUS = "clone_enqueued"

    def _action() -> None:
        try:
            created = UIManager.CreateUIComponentByFrameId(
                clone_parent,
                0,
                child_slot,
                dialog_proc,
                "",
                LAST_CLONE_LABEL,
            )
            print(f"[{MODULE_NAME}] component clone enqueued returned_frame={created}")
        except Exception as exc:
            print(f"[{MODULE_NAME}] component clone error: {exc}")

    Py4GW.Game.enqueue(_action)
    print(f"[{MODULE_NAME}] component clone enqueued")


def _observe_pending_clone_create() -> None:
    global CREATED_FRAME_ID
    global CREATED_FRAME_VISIBLE
    global LAST_TEST_STATUS
    global LAST_SIZE_STATUS
    global CURRENT_SIZE_PHASE
    global PENDING_CLONE_CREATE
    global PENDING_BEFORE_SNAPSHOT
    global LAST_ADDED_SUBTREE_ROOTS
    global PENDING_SIZE_APPLY
    global PENDING_SIZE_OBSERVE
    global PENDING_NEXT_CLONE_STAGE
    global PENDING_SIZE_SEQUENCE

    if not PENDING_CLONE_CREATE:
        if PENDING_SIZE_APPLY:
            _apply_clone_size_from_original()
        elif PENDING_SIZE_OBSERVE:
            clone_rect_after = _get_primary_rect(CREATED_FRAME_ID) if CREATED_FRAME_ID > 0 else None
            before_rect = LAST_SIZE_BEFORE_RECT
            original_rect = _get_primary_rect(ORIGINAL_FRAME_ID) if ORIGINAL_FRAME_ID > 0 else None
            changed_vs_before = clone_rect_after != before_rect if clone_rect_after and before_rect else None
            changed_vs_original = clone_rect_after != original_rect if clone_rect_after and original_rect else None
            if changed_vs_before is True:
                LAST_SIZE_STATUS = f"size_{CURRENT_SIZE_PHASE}_changed"
            elif changed_vs_before is False:
                LAST_SIZE_STATUS = f"size_{CURRENT_SIZE_PHASE}_unchanged"
            else:
                LAST_SIZE_STATUS = f"size_{CURRENT_SIZE_PHASE}_observed"
            PENDING_SIZE_OBSERVE = False
            print(
                f"[{MODULE_NAME}] size {CURRENT_SIZE_PHASE} after "
                f"clone_primary_rect={clone_rect_after}"
            )
            if changed_vs_before is True:
                print(f"[{MODULE_NAME}] size {CURRENT_SIZE_PHASE} result: clone primary rect changed vs before")
            elif changed_vs_before is False:
                print(f"[{MODULE_NAME}] size {CURRENT_SIZE_PHASE} result: clone primary rect unchanged vs before")
            if changed_vs_original is True:
                print(f"[{MODULE_NAME}] size {CURRENT_SIZE_PHASE} compare: clone still differs from original")
            elif changed_vs_original is False:
                print(f"[{MODULE_NAME}] size {CURRENT_SIZE_PHASE} compare: clone matches original")
            if PENDING_SIZE_SEQUENCE:
                completed = PENDING_SIZE_SEQUENCE.pop(0)
                print(f"[{MODULE_NAME}] size phase complete: {completed}")
            if PENDING_SIZE_SEQUENCE:
                if CREATED_FRAME_ID > 0:
                    try:
                        UIManager.DestroyUIComponentByFrameId(CREATED_FRAME_ID)
                    except Exception as exc:
                        print(f"[{MODULE_NAME}] destroy clone error frame={CREATED_FRAME_ID}: {exc}")
                    else:
                        print(f"[{MODULE_NAME}] destroy clone dispatched frame={CREATED_FRAME_ID}")
                CREATED_FRAME_ID = 0
                CREATED_FRAME_VISIBLE = False
                PENDING_NEXT_CLONE_STAGE = True
            else:
                CURRENT_SIZE_PHASE = ""
                LAST_SIZE_STATUS = "size_sweep_complete"
        elif PENDING_NEXT_CLONE_STAGE:
            PENDING_NEXT_CLONE_STAGE = False
            print(
                f"[{MODULE_NAME}] advancing to next size phase "
                f"next={PENDING_SIZE_SEQUENCE[0] if PENDING_SIZE_SEQUENCE else '<none>'}"
            )
            _dispatch_clone_test()
        return

    after = _snapshot_frames()
    selected, selected_visible = _log_frame_diff(PENDING_BEFORE_SNAPSHOT, after, LAST_CLONE_PARENT)

    if not LAST_ADDED_FRAME_IDS and not LAST_REMOVED_FRAME_IDS:
        return

    CREATED_FRAME_ID = selected
    CREATED_FRAME_VISIBLE = selected_visible
    added_set = set(LAST_ADDED_FRAME_IDS)
    LAST_ADDED_SUBTREE_ROOTS = [
        fid
        for fid in LAST_ADDED_FRAME_IDS
        if int(after.get(fid, {}).get("parent_id", -1)) not in added_set
    ]

    LAST_TEST_STATUS = "clone_observed"
    PENDING_CLONE_CREATE = False
    PENDING_BEFORE_SNAPSHOT = {}
    PENDING_SIZE_APPLY = True

    print(
        f"[{MODULE_NAME}] component clone result "
        f"selected_created={CREATED_FRAME_ID} selected_visible={CREATED_FRAME_VISIBLE} "
        f"added_count={len(LAST_ADDED_FRAME_IDS)}"
    )
    _log_frame_layout(CREATED_FRAME_ID, "clone")
    current = CREATED_FRAME_ID
    for depth in range(1, 4):
        child_ids = _collect_child_ids(current)
        if len(child_ids) != 1:
            break
        current = child_ids[0]
        _log_frame_layout(current, f"clone chain[{depth}]")

def run_clone_test() -> None:
    def _action() -> None:
        global LAST_TEST_STATUS
        global PENDING_SIZE_SEQUENCE
        global PENDING_NEXT_CLONE_STAGE
        global PENDING_SIZE_APPLY
        global PENDING_SIZE_OBSERVE

        print(f"[{MODULE_NAME}] diagnostic begin clone_test")
        LAST_TEST_STATUS = "clone_test"
        PENDING_SIZE_SEQUENCE = list(SIZE_TEST_PHASES)
        PENDING_NEXT_CLONE_STAGE = False
        PENDING_SIZE_APPLY = False
        PENDING_SIZE_OBSERVE = False
        _dispatch_clone_test()
        print(f"[{MODULE_NAME}] diagnostic end")

    Py4GW.Game.enqueue(_action)


def update_frame_anchors() -> None:
    global HOST_FRAME_ID
    global HOST_VISIBLE
    global ORIGINAL_FRAME_ID
    global ORIGINAL_FRAME_VISIBLE
    global CREATED_FRAME_ID
    global CREATED_FRAME_VISIBLE

    _observe_pending_clone_create()

    if ORIGINAL_FRAME_ID > 0:
        frame_ids = {int(fid) for fid in UIManager.GetFrameArray()}
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

    if HOST_FRAME_ID > 0:
        frame_ids = {int(fid) for fid in UIManager.GetFrameArray()}
        if HOST_FRAME_ID not in frame_ids:
            HOST_FRAME_ID = 0
            HOST_VISIBLE = False
            print(f"[{MODULE_NAME}] host frame no longer present")
        else:
            try:
                HOST_VISIBLE = bool(UIManager.GetFrameByID(HOST_FRAME_ID).is_visible)
            except Exception:
                HOST_FRAME_ID = 0
                HOST_VISIBLE = False

    if CREATED_FRAME_ID <= 0:
        return

    frame_ids = {int(fid) for fid in UIManager.GetFrameArray()}
    if CREATED_FRAME_ID not in frame_ids:
        CREATED_FRAME_ID = 0
        CREATED_FRAME_VISIBLE = False
        print(f"[{MODULE_NAME}] selected created frame no longer present")
        return

    try:
        CREATED_FRAME_VISIBLE = bool(UIManager.GetFrameByID(CREATED_FRAME_ID).is_visible)
    except Exception:
        CREATED_FRAME_ID = 0
        CREATED_FRAME_VISIBLE = False


def draw_debug_outlines() -> None:
    update_frame_anchors()

    if not DRAW_OUTLINES:
        return

    ui = UIManager()
    if ORIGINAL_FRAME_ID > 0 and UIManager.IsFrameCreated(ORIGINAL_FRAME_ID):
        ui.DrawFrame(ORIGINAL_FRAME_ID, ORIGINAL_FILL_COLOR)
        outline = ORIGINAL_OUTLINE_COLOR if ORIGINAL_FRAME_VISIBLE else 0xFFAAAAAA
        ui.DrawFrameOutline(ORIGINAL_FRAME_ID, outline, 4.0)

    if CREATED_FRAME_ID > 0 and UIManager.IsFrameCreated(CREATED_FRAME_ID):
        ui.DrawFrame(CREATED_FRAME_ID, CREATED_FILL_COLOR)
        outline = CREATED_OUTLINE_COLOR if CREATED_FRAME_VISIBLE else 0xFFAAAAAA
        ui.DrawFrameOutline(CREATED_FRAME_ID, outline, 6.0)


def draw_window() -> None:
    global DRAW_OUTLINES

    PyImGui.text("Clone DevText and run the anchor+size sweep automatically.")

    if PyImGui.button("Run Clone Test"):
        run_clone_test()

    DRAW_OUTLINES = PyImGui.checkbox("Draw Outlines", DRAW_OUTLINES)

    PyImGui.text(f"Last status: {LAST_TEST_STATUS}")
    PyImGui.text(f"Host Label: {DEVTEXT_LABEL}")
    PyImGui.text(f"Original DevText: {ORIGINAL_FRAME_ID} visible={ORIGINAL_FRAME_VISIBLE}")
    PyImGui.text(f"Clone Parent: {LAST_CLONE_PARENT}")
    PyImGui.text(f"Clone Slot: 0x{LAST_CLONE_SLOT:X}")
    PyImGui.text(f"Created Clone: {CREATED_FRAME_ID} visible={CREATED_FRAME_VISIBLE}")
    PyImGui.text(f"Size Status: {LAST_SIZE_STATUS}")
    PyImGui.text(f"Active Size Phase: {CURRENT_SIZE_PHASE}")
    PyImGui.text(f"Pending Size Phases: {PENDING_SIZE_SEQUENCE}")
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
