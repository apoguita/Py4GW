# Blessing_dialog_helper.py
import time
from Py4GWCoreLib import *
from collections import deque, defaultdict

# —— Constants ——————————————————
NPC_DIALOG_HASH    = 3856160816
DEFAULT_OFFSET     = [2, 0, 0, 1]
DIALOG_CHILD_OFFSET = list(DEFAULT_OFFSET)

# —— Core Helpers —————————————————

def is_npc_dialog_visible() -> bool:
    """Return True if the NPC-dialog frame exists and is visible."""
    fid = UIManager.GetFrameIDByHash(NPC_DIALOG_HASH)
    return fid != 0 and UIManager.IsVisible(fid)


def find_dialog_offset() -> None:
    """Auto-detects DIALOG_CHILD_OFFSET for the option-container."""
    global DIALOG_CHILD_OFFSET
    root = UIManager.GetFrameIDByHash(NPC_DIALOG_HASH)
    if root == 0 or not UIManager.IsVisible(root):
        return

    # build parent->children map
    frame_array = UIManager.GetFrameArray()
    children_map = defaultdict(list)
    for fid in frame_array:
        try:
            pid = PyUIManager.UIFrame(fid).parent_id
            children_map[pid].append(fid)
        except:
            pass

    # BFS: pick the container with the most template_type==1 children
    queue = deque([root])
    best = None
    best_count = 0
    while queue:
        cur = queue.popleft()
        kids = children_map.get(cur, [])
        count = sum(
            1 for c in kids
            if UIManager.IsVisible(c)
            and getattr(PyUIManager.UIFrame(c), "template_type", None) == 1
        )
        if count > best_count and count >= 2:
            best_count, best = count, cur
        for c in kids:
            queue.append(c)

    if not best:
        return

    # build index-path from root → best
    path = []
    cur = best
    while cur != root:
        parent = PyUIManager.UIFrame(cur).parent_id
        siblings = children_map[parent]
        path.insert(0, siblings.index(cur))
        cur = parent

    DIALOG_CHILD_OFFSET = path


def get_dialog_button_ids(debug: bool = False) -> list[int]:
    """
    Returns the list of visible, template_type==1 button frame-IDs,
    sorted top→bottom. Pass debug=True to log offset detection.
    """
    # detect offset once
    if DIALOG_CHILD_OFFSET == DEFAULT_OFFSET:
        find_dialog_offset()

    # try the offset first
    ids = UIManager.GetAllChildFrameIDs(NPC_DIALOG_HASH, DIALOG_CHILD_OFFSET)
    valid = [
        fid for fid in ids
        if UIManager.IsVisible(fid)
        and getattr(PyUIManager.UIFrame(fid), "template_type", None) == 1
    ]
    if valid:
        sorted_ids = [fid for fid, _ in UIManager.SortFramesByVerticalPosition(valid)]
        if debug:
            ConsoleLog("DialogHelper", f"Offset IDs → {sorted_ids}", Console.MessageType.Info)
        return sorted_ids

    # fallback BFS over entire tree
    if debug:
        ConsoleLog("DialogHelper", "Falling back to BFS for dialog buttons", Console.MessageType.Info)

    root = UIManager.GetFrameIDByHash(NPC_DIALOG_HASH)
    frame_array = UIManager.GetFrameArray()
    children_map = defaultdict(list)
    for fid in frame_array:
        try:
            pid = PyUIManager.UIFrame(fid).parent_id
            children_map[pid].append(fid)
        except:
            pass

    descendants = []
    queue = deque([root])
    while queue:
        cur = queue.popleft()
        for c in children_map.get(cur, []):
            descendants.append(c)
            queue.append(c)

    valid = [
        fid for fid in descendants
        if UIManager.IsVisible(fid)
        and getattr(PyUIManager.UIFrame(fid), "template_type", None) == 1
    ]
    sorted_ids = [fid for fid, _ in UIManager.SortFramesByVerticalPosition(valid)]
    if debug:
        ConsoleLog("DialogHelper", f"BFS IDs → {sorted_ids}", Console.MessageType.Info)
    return sorted_ids


def click_dialog_button(choice: int, debug: bool = False) -> bool:
    """
    Click the Nth dialog option (1-based). Returns True if dispatched.
    """
    ids = get_dialog_button_ids(debug)
    idx = choice - 1
    if idx < 0 or idx >= len(ids):
        if debug:
            ConsoleLog("DialogHelper", f"Choice #{choice} out of range", Console.MessageType.Warning)
        return False

    target = ids[idx]
    if debug:
        ConsoleLog(
            "DialogHelper",
            f"[{time.time():.2f}] Clicking dialog choice #{choice} → frame {target}",
            Console.MessageType.Info
        )
    UIManager.FrameClick(target)
    return True

def get_dialog_button_count(debug: bool = False) -> int:
    """
    Return the number of visible dialog‐button frames (template_type == 1),
    and log the count if debug=True.
    Log Example: [DialogHelper|Info] Dialog button count 3
    """
    ids = get_dialog_button_ids(debug)
    count = len(ids)

    if debug:
        # Log the count to the console as an info message
        ConsoleLog(
            "DialogHelper",
            f"Dialog button count {count}",
            Console.MessageType.Info
        )

    return count

__all__ = ["is_npc_dialog_visible", "click_dialog_button", "get_dialog_button_count"]
