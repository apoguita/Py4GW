import time

import PyInventory
from Py4GWCoreLib.Inventory import Inventory


MODULE_NAME = "SalvageStartValidation"

# Leave as 0 to auto-pick the first salvage kit/salvageable item from bags 1-4.
# For the Arcane Scepter case, set these to the exact kit/item IDs from Merchant Rules logs.
KIT_ID = 0
ITEM_ID = 0

# Safety: this only starts salvage and observes the popup/session.
# It does NOT choose an option, click Salvage, or accept/confirm anything.
AUTO_START_ONCE = True
POLL_SECONDS = 5.0
PRINT_INTERVAL_SECONDS = 0.5

_started = False
_done = False
_start_time = 0.0
_last_print_time = 0.0
_kit_id = 0
_item_id = 0


def _resolve_ids():
    kit_id = int(KIT_ID or 0)
    item_id = int(ITEM_ID or 0)

    if kit_id <= 0:
        kit_id = int(Inventory.GetFirstSalvageKit(use_lesser=False) or 0)
    if item_id <= 0:
        item_id = int(Inventory.GetFirstSalvageableItem() or 0)

    return kit_id, item_id


def _print_status(label, status):
    print(
        f"[{MODULE_NAME}] {label}: "
        f"kit_id={status.get('kit_id')} "
        f"item_id={status.get('item_id')} "
        f"kit_exists={status.get('kit_exists')} "
        f"item_exists={status.get('item_exists')} "
        f"kit_is_salvage_kit={status.get('kit_is_salvage_kit')} "
        f"item_is_salvageable={status.get('item_is_salvageable')} "
        f"kit_can_interact={status.get('kit_can_interact')} "
        f"item_can_interact={status.get('item_can_interact')} "
        f"safeitem_precheck={status.get('safeitem_precheck')} "
        f"salvage_start_func_ready={status.get('salvage_start_func_ready')} "
        f"failure_reason={status.get('failure_reason')}"
    )


def _print_session(label, session):
    print(
        f"[{MODULE_NAME}] {label}: "
        f"active={session.get('active')} "
        f"item_id={session.get('item_id')} "
        f"kit_id={session.get('kit_id')} "
        f"available={session.get('available_option_names')} "
        f"chosen={session.get('chosen_option')}"
    )


def main():
    global _started, _done, _start_time, _last_print_time, _kit_id, _item_id

    if _done:
        return

    now = time.time()
    if now - _last_print_time < PRINT_INTERVAL_SECONDS:
        return
    _last_print_time = now

    try:
        inv = PyInventory.PyInventory()

        if not hasattr(inv, "GetSalvageStartStatus"):
            print(f"[{MODULE_NAME}] ERROR: GetSalvageStartStatus does not exist on PyInventory.")
            return
        if not hasattr(inv, "StartSalvage"):
            print(f"[{MODULE_NAME}] ERROR: StartSalvage does not exist on PyInventory.")
            return
        if not hasattr(inv, "GetSalvageSessionInfo"):
            print(f"[{MODULE_NAME}] ERROR: GetSalvageSessionInfo does not exist on PyInventory.")
            return

        if not _started:
            _kit_id, _item_id = _resolve_ids()
            print(f"[{MODULE_NAME}] selected_ids: kit_id={_kit_id} item_id={_item_id}")
            if _kit_id <= 0 or _item_id <= 0:
                print(f"[{MODULE_NAME}] ERROR: missing valid kit/item IDs.")
                _started = True
                _done = True
                return

            status = inv.GetSalvageStartStatus(_kit_id, _item_id)
            _print_status("status_before_start", status)

            if not bool(status.get("salvage_start_func_ready", False)):
                print(f"[{MODULE_NAME}] RESULT: FAIL salvage_start_func_ready is False")
                _started = True
                _done = True
                return

            if not AUTO_START_ONCE:
                print(f"[{MODULE_NAME}] AUTO_START_ONCE is disabled. No StartSalvage call made.")
                _started = True
                _done = True
                return

            started = bool(inv.StartSalvage(_kit_id, _item_id))
            print(f"[{MODULE_NAME}] StartSalvage({_kit_id}, {_item_id}) returned: {started}")
            _started = True
            _start_time = now

        session = inv.GetSalvageSessionInfo()
        _print_session("session_after_start", session)

        if bool(session.get("active", False)):
            matches_item = int(session.get("item_id", 0) or 0) == int(_item_id)
            print(f"[{MODULE_NAME}] RESULT: PASS session_active=True matches_item={matches_item}")
            _done = True
            return

        elapsed = now - _start_time
        if elapsed >= POLL_SECONDS:
            print(f"[{MODULE_NAME}] RESULT: FAIL no active salvage session after {elapsed:.1f}s")
            _done = True
        else:
            print(f"[{MODULE_NAME}] waiting_for_session elapsed={elapsed:.1f}s")

    except Exception as exc:
        print(f"[{MODULE_NAME}] ERROR: {type(exc).__name__}: {exc}")
        _done = True
