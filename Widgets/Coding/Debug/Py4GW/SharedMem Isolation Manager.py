import PyImGui
import traceback

from Py4GWCoreLib import GLOBAL_CACHE, ImGui, Color, Routines, ThrottledTimer
from Py4GWCoreLib.IniManager import IniManager

MODULE_NAME = "Shared Memory Isolation Manager"
MODULE_ICON = "Textures/Module_Icons/Isolation.png"

# --- Module-level state ---
_groups: dict[int, str] = {}
_next_group_id: int = 1
_ini_key: str = ""
_ini_loaded: bool = False
_assignments_applied: bool = False
_ini_reload_timer: ThrottledTimer = ThrottledTimer(2000)
_new_group_name: str = ""
_last_error: str = ""
_show_create_form: bool = False
_context_email: str = ""
_drag_email: str = ""
_drag_source_gid: int = -1
_drag_target_gid: int = -1
_first_draw: bool = True


def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(MODULE_NAME, title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Info
    PyImGui.text_colored("Info:", title_color.to_tuple_normalized())
    PyImGui.text("Lists all active shared-memory accounts, including isolated ones,")
    PyImGui.text("and lets you toggle per-account or per-group isolation in place.")
    PyImGui.spacing()

    # How to use
    PyImGui.text_colored("How to use:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Keep single account isolation in the Ungrouped category")
    PyImGui.bullet_text("Create a group")
    PyImGui.bullet_text("Drag & Drop or right-click a character name to assign a group")
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by: Apo")
    PyImGui.bullet_text("Contributors: Sloppynacho")

    PyImGui.end_tooltip()


def _ensure_ini():
    global _ini_key
    if _ini_key:
        return
    im = IniManager()
    _ini_key = im.ensure_global_key("Py4GW", "IsolationGroups.ini")


def _load_groups(force: bool = False):
    global _groups, _next_group_id, _ini_loaded
    if _ini_loaded and not force:
        if not _ini_reload_timer.IsExpired():
            return
        _ini_reload_timer.Reset()
    _ensure_ini()
    if not _ini_key:
        _ini_loaded = True
        return
    im = IniManager()
    im.reload(_ini_key)
    count = im.read_int(_ini_key, "Groups", "count", 0)
    _next_group_id = max(1, im.read_int(_ini_key, "Groups", "next_id", 1))
    _groups.clear()
    for i in range(count):
        gid = im.read_int(_ini_key, "Groups", f"id_{i}", 0)
        name = str(im.read_key(_ini_key, "Groups", f"name_{i}", "") or "").strip()
        if gid > 0 and name:
            _groups[gid] = name
    if _next_group_id <= max(_groups.keys(), default=0):
        _next_group_id = max(_groups.keys()) + 1
    _ini_loaded = True


def _save_groups():
    _ensure_ini()
    if not _ini_key:
        return
    im = IniManager()
    im.write_key(_ini_key, "Groups", "count", len(_groups))
    im.write_key(_ini_key, "Groups", "next_id", _next_group_id)
    for i, (gid, name) in enumerate(sorted(_groups.items())):
        im.write_key(_ini_key, "Groups", f"id_{i}", gid)
        im.write_key(_ini_key, "Groups", f"name_{i}", name)


def _save_assignment(email: str, group_id: int):
    _ensure_ini()
    if not _ini_key or not email:
        return
    im = IniManager()
    im.write_key(_ini_key, "Assignments", email, group_id)


def _apply_assignments():
    global _assignments_applied
    if _assignments_applied:
        return
    _ensure_ini()
    if not _ini_key:
        _assignments_applied = True
        return
    im = IniManager()
    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData(sort_results=False, include_isolated=True) or []
    for account in accounts:
        email = str(account.AccountEmail or "").strip()
        if not email:
            continue
        stored_gid = im.read_int(_ini_key, "Assignments", email, 0)
        if stored_gid > 0 and stored_gid in _groups:
            GLOBAL_CACHE.ShMem.SetAccountGroupByEmail(email, stored_gid)
        elif stored_gid > 0 and stored_gid not in _groups:
            GLOBAL_CACHE.ShMem.SetAccountGroupByEmail(email, 0)
            im.write_key(_ini_key, "Assignments", email, 0)
    _assignments_applied = True


def _draw_account_row(account, current_gid: int, show_checkbox: bool = True):
    """Draw one account row. show_checkbox=True for ungrouped (legacy isolation), False for grouped."""
    global _context_email, _drag_email, _drag_source_gid, _drag_target_gid
    email = str(account.AccountEmail or "").strip()
    if not email:
        return

    label = account.AgentData.CharacterName or account.AccountName or email

    is_drag_source = (_drag_email == email)

    if show_checkbox:
        # Legacy isolation checkbox — only for ungrouped accounts
        isolated = bool(account.IsIsolated)
        new_isolated = PyImGui.checkbox(f"##iso_{email}", isolated)
        if new_isolated != isolated:
            GLOBAL_CACHE.ShMem.SetAccountIsolationByEmail(email, new_isolated)
        PyImGui.same_line(0, 6)

    prefix = ">> " if is_drag_source else ""
    row_label = f"{prefix}{label}##row_{email}"
    PyImGui.selectable(row_label, is_drag_source, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0))

    # Begin drag when row is held and mouse starts dragging.
    if PyImGui.is_item_active() and PyImGui.is_mouse_dragging(0, 0.0):
        _drag_email = email
        _drag_source_gid = current_gid

    # Hovering this row while dragging marks its group as drop target.
    if _drag_email and _drag_email != email and PyImGui.is_item_hovered():
        _drag_target_gid = current_gid

    # Right-click to open group assignment popup
    if PyImGui.is_item_hovered() and PyImGui.is_mouse_clicked(1):
        _context_email = email
        PyImGui.open_popup("AssignGroupPopup")


def _draw_group_context_menu():
    """Draw the right-click group assignment popup."""
    global _context_email
    if not PyImGui.begin_popup("AssignGroupPopup", PyImGui.WindowFlags.NoFlag):
        return

    if not _context_email:
        PyImGui.end_popup()
        return

    PyImGui.text("Assign Group:")
    PyImGui.separator()

    # Ungrouped option
    if PyImGui.button("Ungrouped##ctx_ungroup"):
        GLOBAL_CACHE.ShMem.SetAccountGroupByEmail(_context_email, 0)
        _save_assignment(_context_email, 0)
        _context_email = ""
        PyImGui.close_current_popup()

    # Each group as an option
    for gid in sorted(_groups.keys()):
        if PyImGui.button(f"{_groups[gid]}##ctx_{gid}"):
            GLOBAL_CACHE.ShMem.SetAccountGroupByEmail(_context_email, gid)
            _save_assignment(_context_email, gid)
            _context_email = ""
            PyImGui.close_current_popup()

    PyImGui.end_popup()


def draw():
    global _new_group_name, _next_group_id, _last_error, _show_create_form
    global _drag_email, _drag_source_gid, _drag_target_gid, _first_draw

    if not Routines.Checks.Map.MapValid():
        return

    try:
        _load_groups()
        _apply_assignments()
    except Exception as e:
        _last_error = traceback.format_exc()

    if _first_draw:
        PyImGui.set_next_window_collapsed(True, 0)
        _first_draw = False

    if ImGui.Begin(MODULE_NAME, MODULE_NAME, flags=PyImGui.WindowFlags.AlwaysAutoResize):
        try:
            if _last_error:
                PyImGui.text_colored(f"Error: {_last_error[:200]}", (1.0, 0.3, 0.3, 1.0))
                PyImGui.separator()

            # Toggle create group form
            if not _show_create_form:
                if PyImGui.button("Create Group"):
                    _show_create_form = True
                    _new_group_name = ""
            else:
                _new_group_name = PyImGui.input_text("##group_name", _new_group_name)
                if PyImGui.button("Confirm") and _new_group_name.strip():
                    _groups[_next_group_id] = _new_group_name.strip()
                    _next_group_id += 1
                    _save_groups()
                    _new_group_name = ""
                    _show_create_form = False
                if PyImGui.button("Cancel"):
                    _show_create_form = False
                    _new_group_name = ""

            PyImGui.separator()

            # Fetch accounts once, skip sort (not needed for this widget)
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData(sort_results=False, include_isolated=True) or []

            if not accounts:
                PyImGui.text("No shared-memory accounts found.")
            elif not _groups:
                PyImGui.text(f"Accounts: {len(accounts)}")
                PyImGui.separator()
                for account in accounts:
                    _draw_account_row(account, 0)
            else:
                # Bucket by group — read IsolationGroupID directly from struct
                grouped: dict[int, list] = {}
                ungrouped: list = []
                for account in accounts:
                    gid = int(account.IsolationGroupID)
                    if gid > 0 and gid in _groups:
                        grouped.setdefault(gid, []).append(account)
                    else:
                        ungrouped.append(account)

                for gid in sorted(_groups.keys()):
                    members = grouped.get(gid, [])
                    group_name = _groups[gid]
                    is_drop_here = (_drag_email != "" and _drag_target_gid == gid)
                    header_label = f"{group_name} ({len(members)})"
                    if is_drop_here:
                        header_label += "  <DROP>"
                    header_label += f"##group_{gid}"
                    header_open = PyImGui.collapsing_header(header_label, PyImGui.TreeNodeFlags.DefaultOpen)
                    if _drag_email and PyImGui.is_item_hovered():
                        _drag_target_gid = gid
                    if header_open:
                        if PyImGui.button(f"Delete Group##del_{gid}"):
                            for acc in members:
                                em = str(acc.AccountEmail or "").strip()
                                if em:
                                    GLOBAL_CACHE.ShMem.SetAccountGroupByEmail(em, 0)
                                    _save_assignment(em, 0)
                            del _groups[gid]
                            _save_groups()
                        else:
                            for acc in members:
                                _draw_account_row(acc, gid, show_checkbox=False)

                ungrouped_drop = (_drag_email != "" and _drag_target_gid == 0)
                ungrouped_label = f"Ungrouped ({len(ungrouped)})"
                if ungrouped_drop:
                    ungrouped_label += "  <DROP>"
                ungrouped_label += "##ungrouped"
                ungrouped_open = PyImGui.collapsing_header(ungrouped_label, PyImGui.TreeNodeFlags.DefaultOpen)
                if _drag_email and PyImGui.is_item_hovered():
                    _drag_target_gid = 0
                if ungrouped_open and ungrouped:
                    for acc in ungrouped:
                        _draw_account_row(acc, 0)

            # Apply drag-drop reorder when mouse is released.
            mouse_down = bool(PyImGui.is_mouse_down(0))
            if (not mouse_down) and _drag_email:
                if _drag_target_gid >= 0 and _drag_target_gid != _drag_source_gid:
                    if _drag_target_gid == 0 or _drag_target_gid in _groups:
                        GLOBAL_CACHE.ShMem.SetAccountGroupByEmail(_drag_email, _drag_target_gid)
                        _save_assignment(_drag_email, _drag_target_gid)
                _drag_email = ""
                _drag_source_gid = -1
                _drag_target_gid = -1

            # Draw the shared context menu (only one popup active at a time)
            _draw_group_context_menu()

        except Exception as e:
            _last_error = traceback.format_exc()
            PyImGui.text_colored(f"Draw error: {_last_error[:200]}", (1.0, 0.3, 0.3, 1.0))

    ImGui.End(MODULE_NAME)


def main():
    pass


if __name__ == "__main__":
    main()
