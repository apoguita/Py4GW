from Py4GWCoreLib import *
from collections import deque, defaultdict

# —— Constants ——
NPC_DIALOG_HASH    = 3856160816
DEFAULT_OFFSET     = [2, 0, 0, 1]
# will be updated at runtime if detection succeeds
DIALOG_CHILD_OFFSET = list(DEFAULT_OFFSET)

# —— Helpers ——
def is_npc_dialog_visible() -> bool:
    """Return True if the NPC-dialog frame exists and is visible."""
    fid = UIManager.GetFrameIDByHash(NPC_DIALOG_HASH)
    return fid != 0 and UIManager.IsVisible(fid)


def find_dialog_offset(debug: bool = False) -> None:
    """
    Auto-detect the child-offset path from the NPC_DIALOG_HASH root
    to the container whose direct children are the dialog options
    (identified by template_type == 1). Updates DIALOG_CHILD_OFFSET.
    """
    global DIALOG_CHILD_OFFSET
    root = UIManager.GetFrameIDByHash(NPC_DIALOG_HASH)
    if root == 0 or not UIManager.IsVisible(root):
        if debug:
            ConsoleLog("DialogTester", "Dialog not visible; cannot detect offset.", Console.MessageType.Warning)
        return

    # build parent->children map
    frame_array = UIManager.GetFrameArray()
    children_map: dict[int, list[int]] = defaultdict(list)
    for fid in frame_array:
        try:
            pid = PyUIManager.UIFrame(fid).parent_id
            children_map[pid].append(fid)
        except Exception:
            continue

    # BFS to find best container: most template_type==1 children
    queue = deque([root])
    best_container = None
    best_count = 0
    while queue:
        curr = queue.popleft()
        kids = children_map.get(curr, [])
        # count visible children with template_type == 1
        count = 0
        for c in kids:
            if not UIManager.IsVisible(c):
                continue
            try:
                if PyUIManager.UIFrame(c).template_type == 1:
                    count += 1
            except Exception:
                continue
        if count > best_count and count >= 2:
            best_count = count
            best_container = curr
        # continue BFS
        for c in kids:
            queue.append(c)

    if best_container is None:
        if debug:
            ConsoleLog("DialogTester", "No button container found; using default offset.", Console.MessageType.Warning)
        DIALOG_CHILD_OFFSET = list(DEFAULT_OFFSET)
        return

    # build path from root to best_container
    path: list[int] = []
    curr = best_container
    while curr != root:
        pid = PyUIManager.UIFrame(curr).parent_id
        siblings = children_map.get(pid, [])
        idx = siblings.index(curr)
        path.insert(0, idx)
        curr = pid

    DIALOG_CHILD_OFFSET = path
    if debug:
        ConsoleLog("DialogTester", f"Detected offset path: {path}", Console.MessageType.Info)


def get_dialog_button_ids(debug: bool = False) -> list[int]:
    """
    Try to get dialog choices via the standard child-offset.
    If that returns nothing, fall back to BFS over all descendants.
    In both cases, filter to visible frames with template_type==1 and sort top-to-bottom.
    """
    # primary: use built-in offset chain
    primary = UIManager.GetAllChildFrameIDs(NPC_DIALOG_HASH, DIALOG_CHILD_OFFSET)
    if primary:
        if debug:
            ConsoleLog("DialogTester", f"Primary offset IDs → {primary}", Console.MessageType.Info)
        visible_primary = []
        for fid in primary:
            if UIManager.IsVisible(fid):
                try:
                    if PyUIManager.UIFrame(fid).template_type == 1:
                        visible_primary.append(fid)
                except Exception:
                    continue
        sorted_primary = [fid for fid, _ in UIManager.SortFramesByVerticalPosition(visible_primary)]
        if sorted_primary:
            if debug:
                ConsoleLog("DialogTester", f"Using offset-filtered choices → {sorted_primary}", Console.MessageType.Info)
            return sorted_primary

    # fallback: BFS over entire frame array
    if debug:
        ConsoleLog("DialogTester", "Primary offset returned no choices; falling back to BFS.", Console.MessageType.Info)
    root = UIManager.GetFrameIDByHash(NPC_DIALOG_HASH)
    if root == 0:
        return []
    frame_array = UIManager.GetFrameArray()
    children_map = defaultdict(list)
    for fid in frame_array:
        try:
            pid = PyUIManager.UIFrame(fid).parent_id
        except Exception:
            continue
        children_map[pid].append(fid)
    descendants = []
    queue = deque([root])
    while queue:
        cur = queue.popleft()
        for child in children_map.get(cur, []):
            descendants.append(child)
            queue.append(child)
    # filter BFS candidates
    visible = []
    for fid in descendants:
        if not UIManager.IsVisible(fid):
            continue
        try:
            if PyUIManager.UIFrame(fid).template_type == 1:
                visible.append(fid)
        except Exception:
            continue
    sorted_pairs = UIManager.SortFramesByVerticalPosition(visible)
    sorted_ids = [fid for fid, _ in sorted_pairs]
    if debug:
        ConsoleLog("DialogTester", f"BFS-based filtered choices → {sorted_ids}", Console.MessageType.Info)
    return sorted_ids


def click_dialog_button(choice: int, debug: bool = False) -> bool:
    """
    Clicks the given dialog choice by index (1-based).
    Performs an immediate FrameClick plus queuing it on the ACTION queue.
    Returns True if dispatched.
    """
    if not is_npc_dialog_visible():
        if debug:
            ConsoleLog("DialogTester", "Dialog not visible; cannot click.", Console.MessageType.Warning)
        return False

    ids = get_dialog_button_ids(debug)
    idx = choice - 1
    if idx < 0 or idx >= len(ids):
        if debug:
            ConsoleLog("DialogTester", f"Choice #{choice} out of range (found {len(ids)}).", Console.MessageType.Warning)
        return False

    target = ids[idx]
    # immediate plus queued click
    UIManager.FrameClick(target)
    ActionQueueManager().AddAction("ACTION", UIManager.FrameClick, target)

    if debug:
        ConsoleLog("DialogTester", f"Clicked & queued frame {target} (choice #{choice})", Console.MessageType.Info)
    return True

# —— ImGui window ——
window = ImGui.WindowModule(
    "Dialog Tester",
    window_name="Dialog Tester",
    window_size=(360, 240),
    window_flags=PyImGui.WindowFlags.AlwaysAutoResize
)

def on_ui():
    window.begin()
    PyImGui.text("NPC Dialog Tester")
    PyImGui.separator()

    # Debug info
    vis = is_npc_dialog_visible()
    ids = get_dialog_button_ids(debug=True)
    # gather template types for each choice
    types = []
    for fid in ids:
        try:
            types.append(PyUIManager.UIFrame(fid).template_type)
        except Exception:
            types.append(None)

    PyImGui.text(f"Dialog Visible : {vis}")
    PyImGui.text(f"Choices Found  : {len(ids)} → {ids}")
    PyImGui.text(f"Template Types: {types}")
    PyImGui.separator()

    # Dynamic choice buttons
    for i, fid in enumerate(ids, start=1):
        label = f"Click Choice {i}"
        if PyImGui.button(label):
            if not click_dialog_button(i, debug=True):
                ConsoleLog("DialogTester", f"Failed to click choice {i}", Console.MessageType.Error)
        if (i % 3) != 0:
            PyImGui.separator()

    window.end()

def main():
    on_ui()
