import Py4GW
from Py4GWCoreLib import PyImGui, UIManager
from Py4GWCoreLib.GWUI import GWUI

from native_ui_test_tabs import rect_tab


MODULE_NAME = "Native UI Test"
LAST_STATUS = "idle"
LAST_TARGET_FRAME_ID = 0
LAST_DIRECT_CHILDREN = []
LAST_DESCENDANTS = []


def _log(message: str) -> None:
    print(f"[{MODULE_NAME}] {message}")


def _target_frame_id() -> int:
    frame_id = int(UIManager.GetFrameIDByLabel(rect_tab.WINDOW_TITLE) or 0)
    if frame_id > 0 and UIManager.FrameExists(frame_id):
        return frame_id
    return 0


def _build_parent_map() -> dict[int, list[int]]:
    parent_map: dict[int, list[int]] = {}
    for frame_id in UIManager.GetFrameArray():
        try:
            if not UIManager.FrameExists(frame_id):
                continue
            parent_id = int(UIManager.GetParentID(frame_id) or 0)
        except Exception:
            continue
        parent_map.setdefault(parent_id, []).append(frame_id)
    return parent_map


def _get_direct_children(frame_id: int) -> list[int]:
    if frame_id <= 0:
        return []
    parent_map = _build_parent_map()
    return sorted(parent_map.get(frame_id, []))


def _get_descendants(frame_id: int) -> list[int]:
    if frame_id <= 0:
        return []
    parent_map = _build_parent_map()
    descendants: list[int] = []
    stack = list(parent_map.get(frame_id, []))
    while stack:
        current = stack.pop()
        descendants.append(current)
        stack.extend(parent_map.get(current, []))
    return descendants


def _frame_summary(frame_id: int) -> str:
    if frame_id <= 0:
        return "frame_id=0"
    try:
        frame = UIManager.GetFrameByID(frame_id)
        child_count = len(_get_direct_children(frame_id))
        return (
            f"frame_id={frame_id} "
            f"parent_id={frame.parent_id} "
            f"child_offset_id={frame.child_offset_id} "
            f"type={frame.type} "
            f"template_type={frame.template_type} "
            f"is_created={frame.is_created} "
            f"is_visible={frame.is_visible} "
            f"child_count={child_count}"
        )
    except Exception as exc:
        return f"frame_id={frame_id} summary_error={exc}"


def _refresh_target() -> None:
    global LAST_STATUS, LAST_TARGET_FRAME_ID, LAST_DIRECT_CHILDREN, LAST_DESCENDANTS
    LAST_TARGET_FRAME_ID = _target_frame_id()
    LAST_DIRECT_CHILDREN = _get_direct_children(LAST_TARGET_FRAME_ID)
    LAST_DESCENDANTS = _get_descendants(LAST_TARGET_FRAME_ID)
    LAST_STATUS = (
        f"target={LAST_TARGET_FRAME_ID} "
        f"direct_children={len(LAST_DIRECT_CHILDREN)} "
        f"descendants={len(LAST_DESCENDANTS)}"
    )
    _log(
        "cleaning refresh "
        f"target={LAST_TARGET_FRAME_ID} "
        f"summary=({_frame_summary(LAST_TARGET_FRAME_ID)}) "
        f"direct_children={LAST_DIRECT_CHILDREN} "
        f"descendants={LAST_DESCENDANTS}"
    )
    for child_id in LAST_DIRECT_CHILDREN[:12]:
        _log(f"cleaning direct child summary {_frame_summary(child_id)}")
    for child_id in LAST_DESCENDANTS[:12]:
        _log(f"cleaning descendant summary {_frame_summary(child_id)}")


def _destroy_direct_children() -> None:
    global LAST_STATUS
    target_frame_id = _target_frame_id()
    if target_frame_id <= 0:
        LAST_STATUS = "no managed clone"
        _log("cleaning destroy direct children aborted: no managed clone")
        return
    children = _get_direct_children(target_frame_id)
    destroyed: list[int] = []
    failed: list[int] = []
    for child_id in children:
        try:
            if GWUI.DestroyUIComponentByFrameId(child_id):
                destroyed.append(child_id)
            else:
                failed.append(child_id)
        except Exception:
            failed.append(child_id)
    LAST_STATUS = (
        f"destroyed direct children: {len(destroyed)} "
        f"failed: {len(failed)}"
    )
    _log(
        "cleaning destroy direct children "
        f"target={target_frame_id} destroyed={destroyed} failed={failed}"
    )
    _refresh_target()


def _destroy_descendants() -> None:
    global LAST_STATUS
    target_frame_id = _target_frame_id()
    if target_frame_id <= 0:
        LAST_STATUS = "no managed clone"
        _log("cleaning destroy descendants aborted: no managed clone")
        return
    descendants = _get_descendants(target_frame_id)
    descendants.reverse()
    destroyed: list[int] = []
    failed: list[int] = []
    for child_id in descendants:
        try:
            if GWUI.DestroyUIComponentByFrameId(child_id):
                destroyed.append(child_id)
            else:
                failed.append(child_id)
        except Exception:
            failed.append(child_id)
    LAST_STATUS = (
        f"destroyed descendants: {len(destroyed)} "
        f"failed: {len(failed)}"
    )
    _log(
        "cleaning destroy descendants "
        f"target={target_frame_id} destroyed={destroyed} failed={failed}"
    )
    _refresh_target()


def _first_direct_child(frame_id: int) -> int:
    children = _get_direct_children(frame_id)
    return children[0] if children else 0


def _clear_direct_child_host() -> None:
    global LAST_STATUS
    target_frame_id = _target_frame_id()
    if target_frame_id <= 0:
        LAST_STATUS = "no managed clone"
        _log("cleaning clear direct child host aborted: no managed clone")
        return
    host_frame_id = _first_direct_child(target_frame_id)
    if host_frame_id <= 0:
        LAST_STATUS = "no direct child host"
        _log(f"cleaning clear direct child host aborted: target={target_frame_id} has no direct child host")
        return
    cleared = bool(GWUI.ClearFrameChildrenRecursiveByFrameId(host_frame_id))
    LAST_STATUS = f"clear direct child host target={host_frame_id} result={cleared}"
    _log(
        "cleaning clear direct child host "
        f"target={target_frame_id} host={host_frame_id} result={cleared}"
    )
    _refresh_target()


def _clear_nested_content_host() -> None:
    global LAST_STATUS
    target_frame_id = _target_frame_id()
    if target_frame_id <= 0:
        LAST_STATUS = "no managed clone"
        _log("cleaning clear nested content host aborted: no managed clone")
        return
    host_frame_id = _first_direct_child(target_frame_id)
    nested_host_id = _first_direct_child(host_frame_id) if host_frame_id > 0 else 0
    if nested_host_id <= 0:
        LAST_STATUS = "no nested content host"
        _log(
            "cleaning clear nested content host aborted: "
            f"target={target_frame_id} host={host_frame_id} nested_host={nested_host_id}"
        )
        return
    cleared = bool(GWUI.ClearFrameChildrenRecursiveByFrameId(nested_host_id))
    LAST_STATUS = f"clear nested content host target={nested_host_id} result={cleared}"
    _log(
        "cleaning clear nested content host "
        f"target={target_frame_id} host={host_frame_id} nested_host={nested_host_id} result={cleared}"
    )
    _refresh_target()


def draw() -> None:
    global LAST_STATUS
    PyImGui.text("Cleaning")
    PyImGui.separator()
    PyImGui.text("Target the managed clone and strip its contents without removing the root.")

    target_frame_id = _target_frame_id()
    direct_children = _get_direct_children(target_frame_id)
    descendants = _get_descendants(target_frame_id)

    if PyImGui.button("Create Window"):
        Py4GW.Game.enqueue(rect_tab._create_window)

    PyImGui.same_line(0.0, -1.0)
    if PyImGui.button("Refresh Target"):
        Py4GW.Game.enqueue(_refresh_target)

    PyImGui.same_line(0.0, -1.0)
    if PyImGui.button("Clear Direct Child Host"):
        Py4GW.Game.enqueue(_clear_direct_child_host)

    PyImGui.same_line(0.0, -1.0)
    if PyImGui.button("Clear Nested Content Host"):
        Py4GW.Game.enqueue(_clear_nested_content_host)

    PyImGui.same_line(0.0, -1.0)
    if PyImGui.button("Destroy Direct Children"):
        Py4GW.Game.enqueue(_destroy_direct_children)

    PyImGui.same_line(0.0, -1.0)
    if PyImGui.button("Destroy All Descendants"):
        Py4GW.Game.enqueue(_destroy_descendants)

    PyImGui.separator()
    PyImGui.text(f"Target Label: {rect_tab.WINDOW_TITLE}")
    PyImGui.text(f"Target Summary: {_frame_summary(target_frame_id)}")
    PyImGui.text(f"Direct Children: {len(direct_children)}")
    if direct_children:
        for child_id in direct_children[:12]:
            PyImGui.text(_frame_summary(child_id))
    PyImGui.text(f"Descendants: {len(descendants)}")
    if descendants:
        for child_id in descendants[:12]:
            PyImGui.text(_frame_summary(child_id))
    PyImGui.separator()
    PyImGui.text(f"Last Status: {LAST_STATUS}")
