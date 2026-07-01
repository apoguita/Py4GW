import PyInventory
import PyImGui
import PyItem

from Py4GWCoreLib import *

MODULE_NAME = "Stack Dropper"
MODULE_ICON = "Textures/Module_Icons/Template.png"

INI_KEY = ""
INI_PATH = "Widgets/StackDropper"
INI_FILENAME = "StackDropper.ini"

# State
target_model_id = 0
hovered_model_id = 0
hovered_quantity = 0
auto_max_drop = False
dialog_was_open = False  # track dialog state to only fire once per open

# Auto-drop state
stack_size = 250       # how many units count as one "stack" to drop per pile
stacks_to_drop = 1     # how many such piles to drop
is_dropping = False
drop_model_id = 0
drop_stack_size = 0    # stack size locked in when the run started
drop_start_units = 0   # total units of the model at run start
drop_stop_at_units = 0 # stop once live units reach this
drop_pending = []      # item_ids still to drop one pile from, planned at start
drop_last_units = -1
drop_stall_ticks = 0
drop_status = ""

INVENTORY_BAGS = [Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2]

MAX_BTN_HASH = 4008686776
DROP_BTN_HASH = 4014954629

MAX_STACK_QTY = 250  # GW caps a single slot at 250, so a pile can't exceed this
DROP_TICK_MS = 100
MAX_STALL_TICKS = 15  # confirm phase: abort after this many ticks without inventory change (1.5s)

drop_timer = ThrottledTimer(DROP_TICK_MS)


def _get_item_model_id(item) -> int:
    if hasattr(item, "model_id"):
        return int(item.model_id)
    return int(GLOBAL_CACHE.Item.GetModelID(int(item.item_id)))


def _get_item_quantity(item, default: int = 1) -> int:
    if hasattr(item, "quantity"):
        return int(item.quantity)
    try:
        return int(GLOBAL_CACHE.Item.Properties.GetQuantity(int(item.item_id)))
    except Exception:
        return default


def _update_hovered_item():
    global hovered_model_id, hovered_quantity
    try:
        hovered_item_id = int(GLOBAL_CACHE.Inventory.GetHoveredItemID())
    except Exception:
        return
    if hovered_item_id <= 0:
        return
    try:
        item = PyItem.PyItem(hovered_item_id)
        hovered_model_id = int(item.model_id)
        hovered_quantity = int(item.quantity)
    except Exception:
        hovered_model_id = 0
        hovered_quantity = 0


def _get_model_item_slots(model_id):
    """Return [(item_id, quantity), ...] for every inventory slot holding the model."""
    slots = []
    for bag_enum in INVENTORY_BAGS:
        try:
            bag = PyInventory.Bag(bag_enum.value, bag_enum.name)
            items = bag.GetItems()
        except Exception:
            continue
        for item in items:
            if not item or int(item.item_id) == 0:
                continue
            if _get_item_model_id(item) != model_id:
                continue
            qty = _get_item_quantity(item)
            if qty > 0:
                slots.append((int(item.item_id), qty))
    return slots


def _count_total_units(model_id):
    return sum(qty for _, qty in _get_model_item_slots(model_id))


def _count_available_piles(model_id, size):
    """How many whole piles of `size` can be formed, counting per slot (a slot can
    only contribute floor(qty / size) since each drop comes from a single slot)."""
    if size <= 0:
        return 0
    return sum(qty // size for _, qty in _get_model_item_slots(model_id))


def _start_auto_drop():
    global is_dropping, drop_model_id, drop_stack_size, drop_pending
    global drop_start_units, drop_stop_at_units, drop_last_units, drop_stall_ticks, drop_status

    if not Map.IsExplorable():
        drop_status = "Can only drop in explorable areas"
        return

    size = max(1, min(MAX_STACK_QTY, stack_size))
    slots = _get_model_item_slots(target_model_id)
    total = sum(qty for _, qty in slots)

    # Plan every drop up front from a snapshot, fullest slots first; the fast
    # tick can't rely on the live count, it lags behind the issued drops.
    pending = []
    for item_id, qty in sorted(slots, key=lambda s: s[1], reverse=True):
        while qty >= size and len(pending) < stacks_to_drop:
            pending.append(item_id)
            qty -= size

    if not pending:
        drop_status = f"No full stacks of {size} to drop"
        return

    drop_model_id = target_model_id
    drop_stack_size = size
    drop_start_units = total
    drop_stop_at_units = total - len(pending) * size
    drop_pending = pending
    drop_last_units = -1
    drop_stall_ticks = 0
    drop_status = ""
    is_dropping = True
    drop_timer.Reset()


def _process_auto_drop():
    """Issue one planned pile per tick, then wait for the inventory to confirm."""
    global is_dropping, drop_pending, drop_last_units, drop_stall_ticks, drop_status

    if not is_dropping:
        return
    if not drop_timer.IsExpired():
        return
    drop_timer.Reset()

    # Issue phase: one pre-planned pile per tick.
    if drop_pending:
        item_id = drop_pending.pop(0)
        GLOBAL_CACHE.Inventory.DropItem(item_id, drop_stack_size)
        return

    # Confirm phase: all drops issued, wait for the live count to catch up.
    current = _count_total_units(drop_model_id)
    if current <= drop_stop_at_units:
        is_dropping = False
        dropped = drop_start_units - current
        drop_status = f"Done - dropped {dropped} ({dropped // drop_stack_size} x {drop_stack_size})"
        return

    # Abort if drops stop registering (e.g. dropping not allowed here)
    if current == drop_last_units:
        drop_stall_ticks += 1
        if drop_stall_ticks >= MAX_STALL_TICKS:
            is_dropping = False
            dropped = drop_start_units - current
            drop_status = f"Aborted - {dropped} dropped, rest not registering"
    else:
        drop_stall_ticks = 0
        drop_last_units = current


def _auto_confirm_drop_dialog():
    """Fire once when dialog appears, then wait for it to close before firing again."""
    global dialog_was_open

    max_frame_id = UIManager.GetFrameIDByHash(MAX_BTN_HASH)
    drop_frame_id = UIManager.GetFrameIDByHash(DROP_BTN_HASH)
    dialog_open = (
        max_frame_id != 0
        and drop_frame_id != 0
        and UIManager.FrameExists(max_frame_id)
        and UIManager.FrameExists(drop_frame_id)
    )

    if dialog_open and not dialog_was_open:
        # Dialog just appeared — click Max then Drop once
        GLOBAL_CACHE._ActionQueueManager.AddAction('ACTION', UIManager.FrameClick, max_frame_id)
        GLOBAL_CACHE._ActionQueueManager.AddAction('ACTION', UIManager.FrameClick, drop_frame_id)

    dialog_was_open = dialog_open


def draw_widget():
    global INI_KEY, target_model_id, auto_max_drop, stack_size, stacks_to_drop, is_dropping, drop_status

    if ImGui.Begin(INI_KEY, MODULE_NAME, flags=PyImGui.WindowFlags.AlwaysAutoResize):

        # --- Hovered item picker ---
        if hovered_model_id > 0:
            PyImGui.text(f"Hovered: Model {hovered_model_id}  (Qty: {hovered_quantity})")
            PyImGui.same_line(0, 10)
            if PyImGui.button("Use"):
                target_model_id = hovered_model_id
        else:
            PyImGui.text("Hover an inventory item to detect it")

        PyImGui.separator()

        # --- Model ID input ---
        PyImGui.text("Target Model ID:")
        target_model_id = PyImGui.input_int("##model_id", target_model_id)

        if target_model_id > 0:
            # --- Stack size (units per pile) ---
            PyImGui.text("Stack size (qty per drop):")
            stack_size = max(1, min(MAX_STACK_QTY, PyImGui.input_int("##stack_size", stack_size)))

            # --- Stacks to drop ---
            PyImGui.text("Stacks to drop:")
            stacks_to_drop = max(1, PyImGui.input_int("##stacks_to_drop", stacks_to_drop))

            total_units = _count_total_units(target_model_id)
            available = _count_available_piles(target_model_id, stack_size)
            PyImGui.text(f"Available: {total_units} units = {available} stack(s) of {stack_size}")

            if is_dropping:
                dropped = max(0, drop_start_units - total_units)
                target = drop_start_units - drop_stop_at_units
                PyImGui.text(f"Dropping... {dropped}/{target} units")
                if PyImGui.button("Stop"):
                    is_dropping = False
                    drop_pending.clear()
                    drop_status = "Stopped by user"
            else:
                if PyImGui.button(f"Drop {min(stacks_to_drop, available)} stack(s) of {stack_size}"):
                    _start_auto_drop()

            if drop_status:
                PyImGui.text(drop_status)

        PyImGui.separator()

        # --- Auto Max Drop toggle ---
        auto_max_drop = PyImGui.checkbox("Auto Max Drop", auto_max_drop)
        PyImGui.text("Drag items out of inventory.")
        PyImGui.text("Dialog auto-confirms with Max qty.")

    ImGui.End(INI_KEY)

    _update_hovered_item()

    _process_auto_drop()

    if auto_max_drop:
        _auto_confirm_drop_dialog()


def draw():
    global initialized
    if initialized:
        draw_widget()


def main():
    global INI_KEY, initialized
    if initialized:
        return

    if not Routines.Checks.Map.MapValid():
        return

    if not INI_KEY:
        INI_KEY = IniManager().ensure_key(INI_PATH, INI_FILENAME)
        if not INI_KEY:
            return
        IniManager().load_once(INI_KEY)
        initialized = True


initialized = False
if __name__ == "__main__":
    main()
