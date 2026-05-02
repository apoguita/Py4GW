import time
import PyInventory

MODULE_NAME = "SalvageSessionInfoTest"

# Change this before running the script:
# Valid options: "materials", "prefix", "suffix", "inscription"
TARGET_OPTION = "suffix"

# Safety: this script only changes the selected salvage option.
# It does NOT click Salvage and does NOT accept/confirm anything.
AUTO_SELECT_ONCE = True

_last_print_time = 0.0
_selection_attempted_for = None


def _print_session(label, session):
    print(
        f"[{MODULE_NAME}] {label}: "
        f"active={session.get('active')} "
        f"item_id={session.get('item_id')} "
        f"kit_id={session.get('kit_id')} "
        f"available={session.get('available_option_names')} "
        f"chosen={session.get('chosen_option')} "
        f"option_item_ids={session.get('option_item_ids')}"
    )


def main():
    global _last_print_time, _selection_attempted_for

    now = time.time()
    if now - _last_print_time < 2.0:
        return

    _last_print_time = now

    try:
        inv = PyInventory.PyInventory()

        if not hasattr(inv, "GetSalvageSessionInfo"):
            print(f"[{MODULE_NAME}] ERROR: GetSalvageSessionInfo does not exist on PyInventory.")
            return

        if not hasattr(inv, "SelectSalvageSessionOption"):
            print(f"[{MODULE_NAME}] ERROR: SelectSalvageSessionOption does not exist on PyInventory.")
            return

        session = inv.GetSalvageSessionInfo()
        _print_session("before", session)

        if not session.get("active"):
            print(f"[{MODULE_NAME}] Waiting for a salvage popup...")
            _selection_attempted_for = None
            return

        item_id = session.get("item_id", 0)
        selection_key = (item_id, TARGET_OPTION)

        if not AUTO_SELECT_ONCE:
            print(f"[{MODULE_NAME}] AUTO_SELECT_ONCE is disabled. No selection attempted.")
            return

        if _selection_attempted_for == selection_key:
            print(f"[{MODULE_NAME}] Already attempted {TARGET_OPTION!r} for item_id={item_id}.")
            return

        available_options = session.get("available_options", {})
        if not available_options.get(TARGET_OPTION, False):
            print(f"[{MODULE_NAME}] Target option {TARGET_OPTION!r} is not available for this item.")
            _selection_attempted_for = selection_key
            return

        if session.get("chosen_option") == TARGET_OPTION:
            print(f"[{MODULE_NAME}] Target option {TARGET_OPTION!r} is already selected.")
            _selection_attempted_for = selection_key
            return

        ok = inv.SelectSalvageSessionOption(TARGET_OPTION)
        print(f"[{MODULE_NAME}] SelectSalvageSessionOption({TARGET_OPTION!r}) returned: {ok}")

        after = inv.GetSalvageSessionInfo()
        _print_session("after", after)

        _selection_attempted_for = selection_key

    except Exception as e:
        print(f"[{MODULE_NAME}] ERROR: {type(e).__name__}: {e}")