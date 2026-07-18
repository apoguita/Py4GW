import os
import time

import Py4GW
import PyImGui
import PyUIManager
from Py4GWCoreLib import GWContext, Key, UIManager
from Py4GWCoreLib.Scanner import Scanner
from Py4GWCoreLib.GWUI import GWUI


MODULE_NAME = "Native Labeled Frame Test"
WINDOW_NAME = "Native Labeled Frame Test"
DEVTEXT_LABEL = "DevText"
CLONE_LABEL = "PyDevTextClone"
CLONE_PARENT_ID = 9
PLAYER_FLAG_DEBUG_UI = 0x8
DEVTEXT_KEY = 0x25
OPEN_HOTKEY = Key.F6.value
CLONE_HOTKEY = Key.F7.value


def _resolve_base_dir() -> str:
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        try:
            return Py4GW.Game.GetProjectsPath()
        except Exception:
            pass
        try:
            return Py4GW.Console.get_projects_path()
        except Exception:
            return os.getcwd()


BASE_DIR = _resolve_base_dir()
LOG_PATH = os.path.join(BASE_DIR, "native_labeled_frame_test.log")

WINDOW_OPEN = True
DEVTEXT_DIALOG_PROC_CACHED = 0
LAST_STATUS = "idle"
LAST_CREATED_FRAME_ID = 0
LAST_CREATED_VISIBLE = False
LAST_CLONE_SLOT = 0
DEVTEXT_OPEN_PENDING = False
CLONE_PENDING = False
BEFORE_SNAPSHOT: dict[int, dict[str, int | bool]] = {}


def _log(message: str) -> None:
    line = f"[{MODULE_NAME}] {message}"
    print(line)
    try:
        Py4GW.Console.Log(MODULE_NAME, message, Py4GW.Console.MessageType.Info)
    except Exception:
        pass
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {line}\n")
    except Exception:
        pass


def _log_error(message: str) -> None:
    line = f"[{MODULE_NAME}] {message}"
    print(line)
    try:
        Py4GW.Console.Log(MODULE_NAME, message, Py4GW.Console.MessageType.Error)
    except Exception:
        pass
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {line}\n")
    except Exception:
        pass


def _snapshot_frames() -> dict[int, dict[str, int | bool]]:
    snapshot: dict[int, dict[str, int | bool]] = {}
    for frame_id in UIManager.GetFrameArray():
        try:
            frame = PyUIManager.UIFrame(int(frame_id))
        except Exception:
            continue
        snapshot[int(frame_id)] = {
            "parent_id": int(frame.parent_id),
            "child_offset_id": int(frame.child_offset_id),
            "is_created": bool(frame.is_created),
            "is_visible": bool(frame.is_visible),
        }
    return snapshot


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
            _log(
                f"DevText dialog proc resolved xref_index={xref_index} "
                f"use=0x{use_addr:X} addr=0x{proc_addr:X}"
            )
            return DEVTEXT_DIALOG_PROC_CACHED
    _log_error("DevText dialog proc resolution failed")
    return 0


def _resolve_devtext_frame() -> int:
    frame_id = int(UIManager.GetFrameIDByLabel(DEVTEXT_LABEL) or 0)
    if frame_id > 0:
        return frame_id
    try:
        for candidate_id in UIManager.GetFrameArray():
            frame = PyUIManager.UIFrame(int(candidate_id))
            if int(frame.parent_id) != 9:
                continue
            if int(frame.child_offset_id) != 18:
                continue
            if not bool(frame.is_created):
                continue
            if not bool(frame.is_visible):
                continue
            return int(candidate_id)
    except Exception:
        pass
    return 0


def _collect_used_child_slots(parent_frame_id: int) -> set[int]:
    used: set[int] = set()
    for frame_id in UIManager.GetFrameArray():
        try:
            frame = PyUIManager.UIFrame(int(frame_id))
        except Exception:
            continue
        if int(frame.parent_id) == parent_frame_id:
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


def _dispatch_devtext_keypress() -> None:
    global LAST_STATUS
    global DEVTEXT_OPEN_PENDING

    char_ctx = GWContext.Char.GetContext()
    if char_ctx is None:
        LAST_STATUS = "char_context_unavailable"
        _log_error("DevText open failed: CharContext unavailable")
        return

    original_flags = int(char_ctx.player_flags)
    try:
        char_ctx.player_flags = original_flags | PLAYER_FLAG_DEBUG_UI
        UIManager.Keypress(DEVTEXT_KEY, 0)
        LAST_STATUS = "devtext_open_dispatched"
        DEVTEXT_OPEN_PENDING = True
        _log(f"DevText keypress sent key=0x{DEVTEXT_KEY:X} player_flags=0x{original_flags:X}->0x{int(char_ctx.player_flags):X}")
    finally:
        char_ctx.player_flags = original_flags


def _enqueue_open_devtext() -> None:
    global LAST_STATUS
    Py4GW.Game.enqueue(_dispatch_devtext_keypress)
    LAST_STATUS = "devtext_open_enqueued"
    _log("DevText open enqueued")


def _dispatch_clone() -> None:
    global LAST_STATUS
    global BEFORE_SNAPSHOT
    global CLONE_PENDING
    global LAST_CLONE_SLOT

    if _resolve_devtext_frame() <= 0:
        LAST_STATUS = "devtext_unresolved"
        _log_error("Clone aborted: DevText is not open")
        return

    dialog_proc = _resolve_devtext_dialog_proc()
    if dialog_proc <= 0:
        LAST_STATUS = "dialog_proc_unresolved"
        _log_error("Clone aborted: DevText dialog proc unresolved")
        return

    child_slot = _find_available_clone_slot(CLONE_PARENT_ID)
    if child_slot <= 0:
        LAST_STATUS = "clone_slot_unresolved"
        _log_error("Clone aborted: no free child slot")
        return

    BEFORE_SNAPSHOT = _snapshot_frames()
    CLONE_PENDING = True
    LAST_CLONE_SLOT = child_slot
    LAST_STATUS = "clone_dispatched"
    _log(
        f"Clone dispatch parent={CLONE_PARENT_ID} flags=0x0 child_index=0x{child_slot:X} "
        f"callback=0x{dialog_proc:X} label='{CLONE_LABEL}'"
    )

    created = GWUI.CreateLabeledFrameByFrameId(
        CLONE_PARENT_ID,
        0,
        child_slot,
        dialog_proc,
        0,
        CLONE_LABEL,
    )
    _log(f"CreateLabeledFrameByFrameId returned {created}")
    if int(created or 0) <= 0:
        _log_error("CreateLabeledFrameByFrameId returned 0")


def _enqueue_clone() -> None:
    global LAST_STATUS
    Py4GW.Game.enqueue(_dispatch_clone)
    LAST_STATUS = "clone_enqueued"
    _log("Clone enqueued")


def _observe_pending_devtext() -> None:
    global DEVTEXT_OPEN_PENDING
    global LAST_STATUS

    if not DEVTEXT_OPEN_PENDING:
        return

    frame_id = _resolve_devtext_frame()
    if frame_id <= 0:
        return

    DEVTEXT_OPEN_PENDING = False
    LAST_STATUS = f"devtext_opened frame_id={frame_id}"
    _log(f"DevText resolved frame_id={frame_id}")


def _observe_pending_clone() -> None:
    global CLONE_PENDING
    global LAST_CREATED_FRAME_ID
    global LAST_CREATED_VISIBLE
    global LAST_STATUS

    if not CLONE_PENDING:
        return

    after = _snapshot_frames()
    added_ids = sorted(set(after.keys()) - set(BEFORE_SNAPSHOT.keys()))
    if not added_ids:
        return

    added_set = set(added_ids)
    subtree_roots = [
        frame_id for frame_id in added_ids
        if int(after[frame_id]["parent_id"]) not in added_set
    ]

    selected = 0
    for frame_id in subtree_roots:
        if int(after[frame_id]["parent_id"]) == CLONE_PARENT_ID:
            selected = frame_id
            break
    if selected <= 0 and subtree_roots:
        selected = subtree_roots[0]
    if selected <= 0:
        selected = added_ids[0]

    LAST_CREATED_FRAME_ID = selected
    LAST_CREATED_VISIBLE = bool(after.get(selected, {}).get("is_visible", False))
    CLONE_PENDING = False
    LAST_STATUS = f"clone_observed frame_id={selected}"

    _log(f"Added frame ids={added_ids}")
    _log(f"Added subtree roots={subtree_roots}")
    _log(
        f"Selected frame_id={selected} visible={LAST_CREATED_VISIBLE} "
        f"parent_id={after[selected]['parent_id']} child_offset_id={after[selected]['child_offset_id']}"
    )


def _log_runtime_snapshot() -> None:
    devtext_id = _resolve_devtext_frame()
    _log(
        f"Runtime snapshot status={LAST_STATUS} devtext_id={devtext_id} "
        f"clone_id={LAST_CREATED_FRAME_ID} clone_visible={LAST_CREATED_VISIBLE} "
        f"pending_open={DEVTEXT_OPEN_PENDING} pending_clone={CLONE_PENDING}"
    )


def _draw_window() -> None:
    global WINDOW_OPEN

    if not PyImGui.begin(WINDOW_NAME):
        PyImGui.end()
        return

    devtext_id = _resolve_devtext_frame()
    dialog_proc = _resolve_devtext_dialog_proc()

    PyImGui.text("F6 opens DevText. F7 clones it using CreateLabeledFrameByFrameId.")
    PyImGui.separator()
    PyImGui.text(f"Status: {LAST_STATUS}")
    PyImGui.text(f"DevText frame: {devtext_id}")
    PyImGui.text(f"Dialog proc: 0x{dialog_proc:X}" if dialog_proc > 0 else "Dialog proc: unresolved")
    PyImGui.text(f"Clone parent: {CLONE_PARENT_ID}")
    PyImGui.text(f"Last clone slot: 0x{LAST_CLONE_SLOT:X}" if LAST_CLONE_SLOT > 0 else "Last clone slot: unresolved")
    PyImGui.text(
        f"Last created frame: {LAST_CREATED_FRAME_ID} visible={LAST_CREATED_VISIBLE}"
        if LAST_CREATED_FRAME_ID > 0 else
        "Last created frame: none"
    )

    if PyImGui.button("Open DevText##native_labeled_frame_test"):
        _enqueue_open_devtext()

    if PyImGui.button("Clone DevText##native_labeled_frame_test"):
        _enqueue_clone()

    if PyImGui.button("Log Snapshot##native_labeled_frame_test"):
        _log_runtime_snapshot()

    PyImGui.end()


def main() -> None:
    if PyImGui.is_key_pressed(OPEN_HOTKEY):
        _enqueue_open_devtext()
    if PyImGui.is_key_pressed(CLONE_HOTKEY):
        _enqueue_clone()

    _observe_pending_devtext()
    _observe_pending_clone()
    _draw_window()


if __name__ == "__main__":
    main()
