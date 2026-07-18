from Py4GWCoreLib import *
from Py4GWCoreLib.UIManager import UIManager
from  PyUIManager import UIFrame


MODULE_NAME = "Native UI Canvas Test"
WINDOW_NAME = "Native UI Canvas Test"

TEST_LABEL = "PyCanvasLabel"
TEST_FLAGS_INPUT = "0x0"
TEST_PAGE_CONTEXT_INPUT = "0"
TARGET_LABEL_INPUT = ""
TARGET_CHILD_INDEX_INPUT = ""
TARGET_PARENT_INPUT = ""
TEST_CALLBACK_INPUT = "0"

DEVTEXT_ROOT_ID = 0
DEVTEXT_PARENT_ID = 0
LAST_CREATED_FRAME_ID = 0
CREATED_FRAME_IDS = []
HOST_CANDIDATES = []
HOST_CANDIDATE_INDEX = 0
WATCH_FRAME_ID = 0
WATCH_EXPECTED_PARENT_ID = 0
WATCH_LOGGED_NONZERO = False
LAST_STATUS = "Idle"
DRAW_OUTLINES = True
DEVTEXT_OPEN_PENDING = False
AUTO_REDRAW_AFTER_CREATE = True


def _log(message: str) -> None:
    print(f"[{MODULE_NAME}] {message}")


def _snapshot_frames() -> dict[int, dict]:
    snapshot = {}
    for frame_id in UIManager.GetFrameArray():
        try:
            frame = UIFrame(frame_id)
            snapshot[frame_id] = {
                "parent_id": frame.parent_id,
                "child_offset_id": frame.child_offset_id,
                "is_created": frame.is_created,
                "is_visible": frame.is_visible,
                "type": frame.type,
                "template_type": frame.template_type,
            }
        except Exception:
            continue
    return snapshot


def _collect_child_ids(parent_id: int) -> list[int]:
    child_ids = []
    for frame_id in UIManager.GetFrameArray():
        try:
            frame = UIFrame(frame_id)
            if frame.parent_id == parent_id:
                child_ids.append(frame_id)
        except Exception:
            continue
    child_ids.sort()
    return child_ids


def _find_child_by_offset(parent_id: int, child_offset_id: int) -> int:
    for frame_id in UIManager.GetFrameArray():
        try:
            frame = UIFrame(frame_id)
            if frame.parent_id == parent_id and frame.child_offset_id == child_offset_id:
                return frame_id
        except Exception:
            continue
    return 0


def _describe_child_offsets(parent_id: int, limit: int = 16) -> str:
    offsets = []
    for child_id in _collect_child_ids(parent_id):
        try:
            child = UIFrame(child_id)
            offsets.append(f"0x{child.child_offset_id:X}->{child_id}")
        except Exception:
            continue
    if not offsets:
        return "none"
    if len(offsets) > limit:
        return ", ".join(offsets[:limit]) + f", ... total={len(offsets)}"
    return ", ".join(offsets)


def _find_canvas_parent(frame_id: int) -> int:
    current = frame_id
    visited = set()
    best_fan_out = 0
    last_valid = frame_id

    while current and current not in visited:
        visited.add(current)
        child_ids = _collect_child_ids(current)
        if not child_ids:
            break

        # DevText uses a primary child_offset_id=0 spine with extra siblings
        # hanging off intermediate nodes. The visible insertion point is not
        # the first fan-out node; it is the deepest fan-out container along
        # that main spine.
        if len(child_ids) > 1:
            best_fan_out = current

        next_main = _find_child_by_offset(current, 0)
        if not next_main:
            if len(child_ids) == 1:
                next_main = child_ids[0]
            else:
                break

        last_valid = current
        current = next_main

    if best_fan_out:
        return best_fan_out
    return last_valid


def _resolve_existing_devtext() -> int:
    frame_id = UIManager.GetFrameIDByLabel("DevText")
    if frame_id:
        return frame_id
    try:
        for candidate_id in UIManager.GetFrameArray():
            try:
                frame = UIFrame(candidate_id)
            except Exception:
                continue
            if frame.parent_id != 9:
                continue
            if frame.child_offset_id != 18:
                continue
            if not frame.is_created:
                continue
            if not frame.is_visible:
                continue
            return candidate_id
    except Exception:
        pass
    return 0


def _dispatch_devtext_keypress() -> bool:
    global DEVTEXT_OPEN_PENDING
    global LAST_STATUS

    try:
        context = GWContext.Char.GetContext()
        player_flags_before = int(context.player_flags)
        context.player_flags = player_flags_before | 0x8
        UIManager.Keypress(0x25, 0)
        player_flags_after = int(context.player_flags)
        context.player_flags = player_flags_before
        DEVTEXT_OPEN_PENDING = True
        LAST_STATUS = "DevText keypress dispatched"
        _log(
            "DevText keypress sent "
            f"player_flags_before=0x{player_flags_before:X} "
            f"player_flags_after=0x{player_flags_after:X}"
        )
        return True
    except Exception as exc:
        LAST_STATUS = "DevText keypress failed"
        _log(f"DevText keypress error: {exc}")
        return False


def _dispatch_devtext_refresh_cycle() -> bool:
    global DEVTEXT_OPEN_PENDING
    global LAST_STATUS

    try:
        context = GWContext.Char.GetContext()
        player_flags_before = int(context.player_flags)
        context.player_flags = player_flags_before | 0x8
        UIManager.Keypress(0x25, 0)
        UIManager.Keypress(0x25, 0)
        player_flags_after = int(context.player_flags)
        context.player_flags = player_flags_before
        DEVTEXT_OPEN_PENDING = True
        LAST_STATUS = "DevText refresh dispatched"
        _log(
            "DevText refresh sent "
            f"player_flags_before=0x{player_flags_before:X} "
            f"player_flags_after=0x{player_flags_after:X}"
        )
        return True
    except Exception as exc:
        LAST_STATUS = "DevText refresh failed"
        _log(f"DevText refresh error: {exc}")
        return False


def _open_devtext_button_action() -> None:
    global LAST_STATUS

    Py4GW.Game.enqueue(_dispatch_devtext_keypress)
    LAST_STATUS = "DevText keypress enqueued"
    _log(LAST_STATUS)


def _enqueue_action(callback, label: str) -> None:
    global LAST_STATUS

    Py4GW.Game.enqueue(callback)
    LAST_STATUS = f"{label} enqueued"
    _log(LAST_STATUS)


def _resolve_devtext_canvas() -> int:
    global DEVTEXT_ROOT_ID
    global DEVTEXT_PARENT_ID

    DEVTEXT_ROOT_ID = _resolve_existing_devtext()
    if not DEVTEXT_ROOT_ID:
        DEVTEXT_PARENT_ID = 0
        return 0

    DEVTEXT_PARENT_ID = _find_canvas_parent(DEVTEXT_ROOT_ID)
    _log(f"DevText root={DEVTEXT_ROOT_ID} canvas_parent={DEVTEXT_PARENT_ID}")
    return DEVTEXT_PARENT_ID


def _resolve_target_parent() -> int:
    global LAST_STATUS

    target_label = TARGET_LABEL_INPUT.strip()
    if target_label:
        frame_id = UIManager.GetFrameIDByLabel(target_label)
        if not frame_id:
            LAST_STATUS = f"Label parent not found: {target_label}"
            _log(LAST_STATUS)
            return 0
        try:
            resolved_id = frame_id
            child_path = _parse_child_path(TARGET_CHILD_INDEX_INPUT)
            for depth, child_index in enumerate(child_path):
                child_id = _find_child_by_offset(resolved_id, child_index)
                if not child_id:
                    path_text = ",".join(f"0x{part:X}" for part in child_path[: depth + 1])
                    LAST_STATUS = (
                        f"Label child not found: {target_label}[{path_text}]"
                    )
                    _log(LAST_STATUS)
                    _log(
                        f"Available children under frame={resolved_id}: "
                        f"{_describe_child_offsets(resolved_id)}"
                    )
                    return 0
                resolved_id = child_id

            frame = UIFrame(resolved_id)
            if child_path:
                path_text = ",".join(f"0x{part:X}" for part in child_path)
                LAST_STATUS = (
                    f"Using label child {target_label}[{path_text}]={resolved_id}"
                )
            else:
                LAST_STATUS = f"Using label parent {target_label}={resolved_id}"
            _log(
                f"Label parent={target_label} frame={resolved_id} "
                f"visible={frame.is_visible} created={frame.is_created} "
                f"{_describe_frame_rect(resolved_id)}"
            )
            return resolved_id
        except Exception as exc:
            LAST_STATUS = f"Label parent invalid: {exc}"
            _log(LAST_STATUS)
            return 0

    override = _parse_int(TARGET_PARENT_INPUT, -1)
    if override >= 0:
        try:
            frame = UIFrame(override)
            LAST_STATUS = f"Using manual parent {override}"
            _log(
                f"Manual parent={override} visible={frame.is_visible} "
                f"created={frame.is_created} {_describe_frame_rect(override)}"
            )
            return override
        except Exception as exc:
            LAST_STATUS = f"Manual parent invalid: {exc}"
            _log(LAST_STATUS)
            return 0

    return _resolve_devtext_canvas()


def _tick_pending_devtext_open() -> None:
    global DEVTEXT_OPEN_PENDING
    global DEVTEXT_ROOT_ID
    global DEVTEXT_PARENT_ID
    global LAST_STATUS

    if not DEVTEXT_OPEN_PENDING:
        return

    frame_id = _resolve_existing_devtext()
    if not frame_id:
        return

    DEVTEXT_OPEN_PENDING = False
    DEVTEXT_ROOT_ID = frame_id
    DEVTEXT_PARENT_ID = _find_canvas_parent(frame_id)
    LAST_STATUS = f"DevText open resolved frame_id={frame_id}"
    _log(f"{LAST_STATUS} canvas_parent={DEVTEXT_PARENT_ID}")
    _dump_frame_subtree(frame_id)
    _refresh_host_candidates()


def _dump_devtext_tree() -> None:
    global DEVTEXT_PARENT_ID
    global LAST_STATUS

    frame_id = _resolve_existing_devtext()
    if not frame_id:
        LAST_STATUS = "DevText not open"
        _log(LAST_STATUS)
        return

    DEVTEXT_PARENT_ID = _find_canvas_parent(frame_id)
    LAST_STATUS = f"Dumped DevText subtree root={frame_id}"
    _dump_frame_subtree(frame_id)


def _parse_int(value: str, default: int = 0) -> int:
    try:
        return int(value.strip(), 0)
    except Exception:
        return default


def _parse_child_path(value: str) -> list[int]:
    text = value.strip()
    if not text:
        return []
    parts = [part.strip() for part in text.split(",")]
    path = []
    for part in parts:
        if not part:
            continue
        try:
            path.append(int(part, 0))
        except Exception:
            return []
    return path


def _next_free_child_slot(parent_id: int, start: int = 0xFE) -> int:
    child_ids = _collect_child_ids(parent_id)
    used = set()
    zero_slot_children = 0
    for child_id in child_ids:
        try:
            child = UIFrame(child_id)
            used.add(child.child_offset_id)
            if child.child_offset_id == 0:
                zero_slot_children += 1
        except Exception:
            continue

    # Some live container nodes (DevText is one) lay out only the slot-0
    # sibling chain. Synthetic high slots create valid frames but they never
    # receive bounds, so force new children onto the slot the container
    # already uses.
    if child_ids and zero_slot_children and zero_slot_children >= (len(child_ids) - 1):
        return 0

    for slot in range(start, 0, -1):
        if slot not in used:
            return slot
    return -1


def _diff_new_frames(before: dict[int, dict], after: dict[int, dict]) -> list[int]:
    added = sorted(set(after.keys()) - set(before.keys()))
    for frame_id in added:
        info = after[frame_id]
        _log(
            "added "
            f"frame_id={frame_id} parent_id={info['parent_id']} "
            f"child_offset_id={info['child_offset_id']} "
            f"is_created={info['is_created']} is_visible={info['is_visible']} "
            f"type={info['type']} template_type={info['template_type']} "
            f"{_describe_frame_rect(frame_id)}"
        )
    return added


def _record_created_frame(frame_id: int) -> None:
    global LAST_CREATED_FRAME_ID
    LAST_CREATED_FRAME_ID = frame_id
    if frame_id and frame_id not in CREATED_FRAME_IDS:
        CREATED_FRAME_IDS.append(frame_id)


def _watch_created_frame(frame_id: int, expected_parent_id: int) -> None:
    global WATCH_FRAME_ID
    global WATCH_EXPECTED_PARENT_ID
    global WATCH_LOGGED_NONZERO

    WATCH_FRAME_ID = frame_id
    WATCH_EXPECTED_PARENT_ID = expected_parent_id
    WATCH_LOGGED_NONZERO = False


def _describe_frame_rect(frame_id: int) -> str:
    try:
        frame = UIFrame(frame_id)
        pos = frame.position
        return (
            f"screen=({pos.left_on_screen},{pos.top_on_screen})-"
            f"({pos.right_on_screen},{pos.bottom_on_screen}) "
            f"size={pos.width_on_screen}x{pos.height_on_screen}"
        )
    except Exception as exc:
        return f"rect_error={exc}"


def _post_create_frame_actions(frame_id: int, parent_id: int, context_label: str) -> None:
    if not frame_id:
        return

    _log(f"{context_label} rect frame={frame_id} {_describe_frame_rect(frame_id)}")
    _watch_created_frame(frame_id, parent_id)

    if AUTO_REDRAW_AFTER_CREATE:
        parent_redraw = UIManager.TriggerFrameRedrawByFrameId(parent_id)
        frame_redraw = UIManager.TriggerFrameRedrawByFrameId(frame_id)
        _log(
            f"{context_label} redraw parent={parent_id} result={parent_redraw} "
            f"frame={frame_id} result={frame_redraw}"
        )


def _collect_subtree_nodes(root_id: int, max_depth: int = 6, max_nodes: int = 256) -> list[tuple[int, int]]:
    if not root_id:
        return []

    stack = [(root_id, 0)]
    visited = set()
    result = []

    while stack and len(result) < max_nodes:
        frame_id, depth = stack.pop()
        if frame_id in visited:
            continue
        visited.add(frame_id)
        result.append((frame_id, depth))

        if depth >= max_depth:
            continue

        for child_id in reversed(_collect_child_ids(frame_id)):
            stack.append((child_id, depth + 1))

    return result


def _tick_created_frame_watch() -> None:
    global WATCH_FRAME_ID
    global WATCH_EXPECTED_PARENT_ID
    global WATCH_LOGGED_NONZERO

    if not WATCH_FRAME_ID:
        return

    try:
        frame = UIFrame(WATCH_FRAME_ID)
        pos = frame.position
        has_nonzero = pos.width_on_screen > 0 and pos.height_on_screen > 0
        if not has_nonzero:
            return
        if WATCH_LOGGED_NONZERO:
            return

        WATCH_LOGGED_NONZERO = True
        _log(
            f"Watched frame became visible frame={WATCH_FRAME_ID} "
            f"parent={frame.parent_id} expected_parent={WATCH_EXPECTED_PARENT_ID} "
            f"{_describe_frame_rect(WATCH_FRAME_ID)}"
        )
    except Exception:
        return


def _refresh_host_candidates() -> list[int]:
    global HOST_CANDIDATES
    global HOST_CANDIDATE_INDEX
    global LAST_STATUS

    root_id = _resolve_existing_devtext()
    if not root_id:
        HOST_CANDIDATES = []
        HOST_CANDIDATE_INDEX = 0
        LAST_STATUS = "DevText not open"
        _log(LAST_STATUS)
        return HOST_CANDIDATES

    scored = []
    for frame_id, depth in _collect_subtree_nodes(root_id):
        if frame_id == root_id:
            continue
        try:
            frame = UIFrame(frame_id)
            pos = frame.position
        except Exception:
            continue

        if not frame.is_created or not frame.is_visible:
            continue
        if pos.width_on_screen <= 0 or pos.height_on_screen <= 0:
            continue

        child_count = len(_collect_child_ids(frame_id))
        score = 0
        if frame.template_type:
            score += 40
        if frame.type:
            score += 15
        if 1 <= depth <= 4:
            score += 20 - (depth * 2)
        if child_count == 0:
            score += 12
        elif child_count <= 3:
            score += 24
        elif child_count <= 8:
            score += 16
        elif child_count <= 16:
            score += 6
        else:
            score -= min(child_count, 40)
        if pos.height_on_screen <= 160:
            score += 14
        if pos.width_on_screen <= 700:
            score += 8

        scored.append((score, frame_id, depth, child_count))

    scored.sort(key=lambda item: (-item[0], item[2], item[3], item[1]))
    HOST_CANDIDATES = [frame_id for _, frame_id, _, _ in scored]
    HOST_CANDIDATE_INDEX = 0

    LAST_STATUS = f"Host candidates refreshed count={len(HOST_CANDIDATES)}"
    _log(LAST_STATUS)
    for score, frame_id, depth, child_count in scored[:8]:
        try:
            frame = UIFrame(frame_id)
            _log(
                f"candidate frame={frame_id} score={score} depth={depth} "
                f"children={child_count} slot=0x{frame.child_offset_id:X} "
                f"type={frame.type} template={frame.template_type} "
                f"{_describe_frame_rect(frame_id)}"
            )
        except Exception:
            continue

    return HOST_CANDIDATES


def _dump_frame_subtree(root_id: int, max_depth: int = 5, max_nodes: int = 48) -> None:
    if not root_id:
        _log("Frame subtree dump skipped: root_id=0")
        return

    stack = [(root_id, 0)]
    visited = set()
    emitted = 0

    _log(
        f"Frame subtree dump root={root_id} "
        f"selected_parent={DEVTEXT_PARENT_ID} max_depth={max_depth} max_nodes={max_nodes}"
    )

    while stack and emitted < max_nodes:
        frame_id, depth = stack.pop()
        if frame_id in visited:
            continue
        visited.add(frame_id)

        try:
            frame = UIFrame(frame_id)
        except Exception as exc:
            _log(f"{'  ' * depth}- frame={frame_id} read_error={exc}")
            continue

        marker = ""
        if frame_id == root_id:
            marker += " [root]"
        if frame_id == DEVTEXT_PARENT_ID:
            marker += " [selected]"

        child_ids = _collect_child_ids(frame_id)
        rect = _describe_frame_rect(frame_id)
        _log(
            f"{'  ' * depth}- frame={frame_id}{marker} "
            f"parent={frame.parent_id} slot=0x{frame.child_offset_id:X} "
            f"visible={frame.is_visible} created={frame.is_created} "
            f"type={frame.type} template={frame.template_type} "
            f"children={len(child_ids)} {rect}"
        )
        emitted += 1

        if depth >= max_depth:
            continue

        for child_id in reversed(child_ids):
            stack.append((child_id, depth + 1))

    if stack:
        _log(f"Frame subtree dump truncated after {emitted} nodes")


def _create_text_label_for_parent(parent_id: int, context_label: str = "CreateTextLabel") -> int:
    global LAST_STATUS

    if not parent_id:
        return 0

    flags = _parse_int(TEST_FLAGS_INPUT, 0)
    child_index = _next_free_child_slot(parent_id)
    if child_index < 0:
        LAST_STATUS = "No free child slot"
        _log(LAST_STATUS)
        return 0

    before = _snapshot_frames()
    frame_id = UIManager.CreateTextLabelFrameByFrameId(
        parent_id, flags, child_index, "", TEST_LABEL
    )
    after = _snapshot_frames()

    added = _diff_new_frames(before, after)
    _record_created_frame(frame_id)
    LAST_STATUS = (
        f"{context_label} parent={parent_id} slot=0x{child_index:X} "
        f"frame={frame_id} added={len(added)}"
    )
    _log(LAST_STATUS)
    if frame_id:
        _post_create_frame_actions(frame_id, parent_id, context_label)
        if (
            not TARGET_LABEL_INPUT.strip()
            and not TARGET_PARENT_INPUT.strip()
            and DEVTEXT_ROOT_ID
            and parent_id == DEVTEXT_PARENT_ID
        ):
            Py4GW.Game.enqueue(_dispatch_devtext_refresh_cycle)
            _log("DevText refresh enqueued")
    return frame_id


def _create_text_label() -> None:
    parent_id = _resolve_target_parent()
    _create_text_label_for_parent(parent_id, "CreateTextLabel")


def _probe_next_host() -> None:
    global HOST_CANDIDATE_INDEX
    global LAST_STATUS

    if not HOST_CANDIDATES or HOST_CANDIDATE_INDEX >= len(HOST_CANDIDATES):
        _refresh_host_candidates()
        if not HOST_CANDIDATES:
            return

    candidate_id = HOST_CANDIDATES[HOST_CANDIDATE_INDEX]
    HOST_CANDIDATE_INDEX += 1

    try:
        frame = UIFrame(candidate_id)
        _log(
            f"Probing host frame={candidate_id} "
            f"index={HOST_CANDIDATE_INDEX}/{len(HOST_CANDIDATES)} "
            f"children={len(_collect_child_ids(candidate_id))} "
            f"slot=0x{frame.child_offset_id:X} "
            f"type={frame.type} template={frame.template_type} "
            f"{_describe_frame_rect(candidate_id)}"
        )
    except Exception as exc:
        LAST_STATUS = f"Probe host read error: {exc}"
        _log(LAST_STATUS)
        return

    frame_id = _create_text_label_for_parent(candidate_id, f"ProbeTextLabel[{candidate_id}]")
    if frame_id:
        _log(
            f"Probe result host={candidate_id} created={frame_id} "
            f"{_describe_frame_rect(frame_id)}"
        )


def _create_scrollable() -> None:
    global LAST_STATUS

    parent_id = _resolve_target_parent()
    if not parent_id:
        return

    flags = _parse_int(TEST_FLAGS_INPUT, 0)
    page_context = _parse_int(TEST_PAGE_CONTEXT_INPUT, 0)
    child_index = _next_free_child_slot(parent_id)
    if child_index < 0:
        LAST_STATUS = "No free child slot"
        _log(LAST_STATUS)
        return

    before = _snapshot_frames()
    frame_id = UIManager.CreateScrollableFrameByFrameId(
        parent_id, flags, child_index, page_context, TEST_LABEL
    )
    after = _snapshot_frames()

    added = _diff_new_frames(before, after)
    _record_created_frame(frame_id)
    LAST_STATUS = (
        f"CreateScrollable parent={parent_id} slot=0x{child_index:X} "
        f"page_ctx={page_context} frame={frame_id} added={len(added)}"
    )
    _log(LAST_STATUS)
    if frame_id:
        _post_create_frame_actions(frame_id, parent_id, "CreateScrollable")


def _create_button() -> None:
    global LAST_STATUS

    parent_id = _resolve_target_parent()
    if not parent_id:
        return

    flags = _parse_int(TEST_FLAGS_INPUT, 0)
    child_index = _next_free_child_slot(parent_id)
    if child_index < 0:
        LAST_STATUS = "No free child slot"
        _log(LAST_STATUS)
        return

    before = _snapshot_frames()
    frame_id = UIManager.CreateButtonFrameByFrameId(
        parent_id, flags, child_index, "", TEST_LABEL
    )
    after = _snapshot_frames()

    added = _diff_new_frames(before, after)
    _record_created_frame(frame_id)
    LAST_STATUS = (
        f"CreateButton parent={parent_id} slot=0x{child_index:X} "
        f"frame={frame_id} added={len(added)}"
    )
    _log(LAST_STATUS)
    if frame_id:
        _post_create_frame_actions(frame_id, parent_id, "CreateButton")


def _create_checkbox() -> None:
    global LAST_STATUS

    parent_id = _resolve_target_parent()
    if not parent_id:
        return

    flags = _parse_int(TEST_FLAGS_INPUT, 0)
    child_index = _next_free_child_slot(parent_id)
    if child_index < 0:
        LAST_STATUS = "No free child slot"
        _log(LAST_STATUS)
        return

    before = _snapshot_frames()
    frame_id = UIManager.CreateCheckboxFrameByFrameId(
        parent_id, flags, child_index, "", TEST_LABEL
    )
    after = _snapshot_frames()

    added = _diff_new_frames(before, after)
    _record_created_frame(frame_id)
    LAST_STATUS = (
        f"CreateCheckbox parent={parent_id} slot=0x{child_index:X} "
        f"frame={frame_id} added={len(added)}"
    )
    _log(LAST_STATUS)
    if frame_id:
        _post_create_frame_actions(frame_id, parent_id, "CreateCheckbox")


def _trigger_redraw_target() -> None:
    global LAST_STATUS

    parent_id = _resolve_target_parent()
    if not parent_id:
        return

    result = UIManager.TriggerFrameRedrawByFrameId(parent_id)
    LAST_STATUS = f"TriggerRedraw parent={parent_id} result={result}"
    _log(LAST_STATUS)
    _log(f"TriggerRedraw rect parent={parent_id} {_describe_frame_rect(parent_id)}")


def _trigger_redraw_last_created() -> None:
    global LAST_STATUS

    if not LAST_CREATED_FRAME_ID:
        LAST_STATUS = "No last created frame"
        _log(LAST_STATUS)
        return

    result = UIManager.TriggerFrameRedrawByFrameId(LAST_CREATED_FRAME_ID)
    LAST_STATUS = f"TriggerRedraw frame={LAST_CREATED_FRAME_ID} result={result}"
    _log(LAST_STATUS)
    _log(
        f"TriggerRedraw rect frame={LAST_CREATED_FRAME_ID} "
        f"{_describe_frame_rect(LAST_CREATED_FRAME_ID)}"
    )


def _add_callback_target() -> None:
    global LAST_STATUS

    parent_id = _resolve_target_parent()
    if not parent_id:
        return

    callback_ptr = _parse_int(TEST_CALLBACK_INPUT, 0)
    if not callback_ptr:
        LAST_STATUS = "Callback pointer is 0"
        _log(LAST_STATUS)
        return

    result = GWUI.AddFrameUIInteractionCallbackByFrameId(parent_id, callback_ptr, 0)
    LAST_STATUS = (
        f"AddCallback frame={parent_id} callback=0x{callback_ptr:X} result={result}"
    )
    _log(LAST_STATUS)


def _add_callback_last_created() -> None:
    global LAST_STATUS

    if not LAST_CREATED_FRAME_ID:
        LAST_STATUS = "No last created frame"
        _log(LAST_STATUS)
        return

    callback_ptr = _parse_int(TEST_CALLBACK_INPUT, 0)
    if not callback_ptr:
        LAST_STATUS = "Callback pointer is 0"
        _log(LAST_STATUS)
        return

    result = GWUI.AddFrameUIInteractionCallbackByFrameId(
        LAST_CREATED_FRAME_ID, callback_ptr, 0
    )
    LAST_STATUS = (
        f"AddCallback frame={LAST_CREATED_FRAME_ID} callback=0x{callback_ptr:X} "
        f"result={result}"
    )
    _log(LAST_STATUS)


def _destroy_last_created() -> None:
    global LAST_STATUS
    global LAST_CREATED_FRAME_ID

    if not LAST_CREATED_FRAME_ID:
        LAST_STATUS = "No created frame to destroy"
        _log(LAST_STATUS)
        return

    target = LAST_CREATED_FRAME_ID
    try:
        UIManager.DestroyUIComponentByFrameId(target)
        LAST_STATUS = f"Destroy dispatched frame={target}"
        _log(LAST_STATUS)
    except Exception as exc:
        LAST_STATUS = f"Destroy error frame={target}: {exc}"
        _log(LAST_STATUS)

    LAST_CREATED_FRAME_ID = 0


def _clear_tracked() -> None:
    global LAST_STATUS
    global LAST_CREATED_FRAME_ID

    for frame_id in list(CREATED_FRAME_IDS):
        try:
            UIManager.DestroyUIComponentByFrameId(frame_id)
            _log(f"Destroy dispatched frame={frame_id}")
        except Exception as exc:
            _log(f"Destroy error frame={frame_id}: {exc}")
    CREATED_FRAME_IDS.clear()
    LAST_CREATED_FRAME_ID = 0
    LAST_STATUS = "Cleared tracked created frames"


def _draw_created_outlines() -> None:
    if not DRAW_OUTLINES:
        return

    drawer = UIManager()

    for frame_id in CREATED_FRAME_IDS:
        if not frame_id:
            continue
        try:
            frame = UIFrame(frame_id)
            if not frame.is_visible:
                continue
            # Draw every created frame in green. Keep the last-created frame
            # green as well, but make it brighter/thicker instead of switching
            # to a different color.
            if frame_id == LAST_CREATED_FRAME_ID:
                drawer.DrawFrame(frame_id, 0x6000FF00)
                drawer.DrawFrameOutline(frame_id, 0xFF00FF00, 4)
            else:
                drawer.DrawFrame(frame_id, 0x3000FF00)
                drawer.DrawFrameOutline(frame_id, 0xC000FF00, 2)
        except Exception:
            continue


def main():
    global TEST_LABEL
    global TEST_FLAGS_INPUT
    global TEST_PAGE_CONTEXT_INPUT
    global TARGET_LABEL_INPUT
    global TARGET_CHILD_INDEX_INPUT
    global TARGET_PARENT_INPUT
    global TEST_CALLBACK_INPUT
    global DRAW_OUTLINES
    global LAST_STATUS
    global AUTO_REDRAW_AFTER_CREATE

    _tick_pending_devtext_open()
    _tick_created_frame_watch()
    _draw_created_outlines()

    PyImGui.set_next_window_size(520, 340)
    if PyImGui.begin(WINDOW_NAME):
        PyImGui.text("Create bound UI elements inside DevText.")
        DRAW_OUTLINES = PyImGui.checkbox("Draw Outlines", DRAW_OUTLINES)
        TEST_LABEL = PyImGui.input_text("Label", TEST_LABEL)
        TEST_FLAGS_INPUT = PyImGui.input_text("Flags", TEST_FLAGS_INPUT)
        TEST_PAGE_CONTEXT_INPUT = PyImGui.input_text("Page Context", TEST_PAGE_CONTEXT_INPUT)
        TEST_CALLBACK_INPUT = PyImGui.input_text("Callback Ptr", TEST_CALLBACK_INPUT)
        TARGET_LABEL_INPUT = PyImGui.input_text("Parent Label", TARGET_LABEL_INPUT)
        TARGET_CHILD_INDEX_INPUT = PyImGui.input_text("Label Child Index", TARGET_CHILD_INDEX_INPUT)
        TARGET_PARENT_INPUT = PyImGui.input_text("Parent Override", TARGET_PARENT_INPUT)
        AUTO_REDRAW_AFTER_CREATE = PyImGui.checkbox(
            "Auto Redraw After Create", AUTO_REDRAW_AFTER_CREATE
        )

        if PyImGui.button("Open DevText"):
            _open_devtext_button_action()
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Create Text Label"):
            _enqueue_action(_create_text_label, "CreateTextLabel")
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Create Scrollable"):
            _enqueue_action(_create_scrollable, "CreateScrollable")

        if PyImGui.button("Create Button"):
            _enqueue_action(_create_button, "CreateButton")
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Create Checkbox"):
            _enqueue_action(_create_checkbox, "CreateCheckbox")

        if PyImGui.button("Redraw Target"):
            _enqueue_action(_trigger_redraw_target, "TriggerRedrawTarget")
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Redraw Last"):
            _enqueue_action(_trigger_redraw_last_created, "TriggerRedrawLast")
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Add Callback Target"):
            _enqueue_action(_add_callback_target, "AddCallbackTarget")
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Add Callback Last"):
            _enqueue_action(_add_callback_last_created, "AddCallbackLast")

        if PyImGui.button("Destroy Last Created"):
            _enqueue_action(_destroy_last_created, "DestroyLastCreated")
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Clear Tracked"):
            _enqueue_action(_clear_tracked, "ClearTracked")
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Dump DevText Tree"):
            _enqueue_action(_dump_devtext_tree, "DumpDevTextTree")
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Refresh Hosts"):
            _enqueue_action(_refresh_host_candidates, "RefreshHosts")
        PyImGui.same_line(0.0, -1.0)
        if PyImGui.button("Probe Next Host"):
            _enqueue_action(_probe_next_host, "ProbeNextHost")

        PyImGui.separator()
        PyImGui.text(f"DevText Root: {DEVTEXT_ROOT_ID}")
        PyImGui.text(f"Canvas Parent: {DEVTEXT_PARENT_ID}")
        PyImGui.text(
            f"Host Probe: {HOST_CANDIDATE_INDEX}/{len(HOST_CANDIDATES)}"
        )
        PyImGui.text(f"Last Created: {LAST_CREATED_FRAME_ID}")
        PyImGui.text(f"Tracked Frames: {CREATED_FRAME_IDS}")
        PyImGui.text(f"Status: {LAST_STATUS}")

    PyImGui.end()


if __name__ == "__main__":
    main()
