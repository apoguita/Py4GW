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


def tooltip():
    PyImGui.begin_tooltip()
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(MODULE_NAME, title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.text("Lists all active shared-memory accounts, including isolated ones,")
    PyImGui.text("and lets you toggle per-account isolation in place.")
    PyImGui.text("Right-click a character name to assign a group.")
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


def _draw_account_row(account, show_checkbox: bool = True):
    """Draw one account row. show_checkbox=True for ungrouped (legacy isolation), False for grouped."""
    global _context_email
    email = str(account.AccountEmail or "").strip()
    if not email:
        return

    label = account.AgentData.CharacterName or account.AccountName or email

    if show_checkbox:
        # Legacy isolation checkbox — only for ungrouped accounts
        isolated = bool(account.IsIsolated)
        new_isolated = PyImGui.checkbox(f"{label}##iso_{email}", isolated)
        if new_isolated != isolated:
            GLOBAL_CACHE.ShMem.SetAccountIsolationByEmail(email, new_isolated)
    else:
        # Grouped accounts — just show the name
        PyImGui.text(f"  {label}")

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

    if not Routines.Checks.Map.MapValid():
        return

    try:
        _load_groups()
        _apply_assignments()
    except Exception as e:
        _last_error = traceback.format_exc()

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
                    _draw_account_row(account)
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
                    if PyImGui.collapsing_header(f"{group_name} ({len(members)})##group_{gid}", PyImGui.TreeNodeFlags.DefaultOpen):
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
                                _draw_account_row(acc, show_checkbox=False)

                if ungrouped:
                    if PyImGui.collapsing_header(f"Ungrouped ({len(ungrouped)})##ungrouped", PyImGui.TreeNodeFlags.DefaultOpen):
                        for acc in ungrouped:
                            _draw_account_row(acc)

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
