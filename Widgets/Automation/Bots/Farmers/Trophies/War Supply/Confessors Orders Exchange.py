import PyImGui
from typing import List, Tuple
from Py4GWCoreLib import *

MODULE_NAME = "Confessor's Orders Exchange"
MODULE_ICON = "Textures\\Module_Icons\\Item Eater.png"

_CONFESSORS_ORDERS_MODEL_ID = 35123
_WAR_SUPPLY_MODEL_ID        = 35121
_EXCHANGE_RATE              = 3     # 3 Confessor's Orders → 1 War Supply
_TRANSACTION_TIMEOUT_MS     = 5000


def _get_order_stacks() -> List[Tuple[int, int]]:
    """Return all (item_id, quantity) pairs for Confessor's Orders across all inventory bags."""
    stacks: List[Tuple[int, int]] = []
    for bag_id in (1, 2, 3, 4):
        try:
            bag = PyInventory.Bag(bag_id, f"Bag_{bag_id}")
            for bag_item in bag.GetItems():
                if int(getattr(bag_item, "model_id", 0) or 0) == _CONFESSORS_ORDERS_MODEL_ID:
                    item_id = int(getattr(bag_item, "item_id", 0) or 0)
                    qty     = int(getattr(bag_item, "quantity", 0) or 0)
                    if item_id > 0 and qty > 0:
                        stacks.append((item_id, qty))
        except Exception:
            ConsoleLog(MODULE_NAME, f"Stack scan failed on bag {bag_id}.", Py4GW.Console.MessageType.Warning)
    return stacks


def _build_turn_in(stacks: List[Tuple[int, int]], needed: int) -> Tuple[List[int], List[int]]:
    """Build give_ids / give_qtys to satisfy 'needed' items, drawing across stacks as required.
    Returns empty lists if the total across all stacks is insufficient."""
    give_ids:  List[int] = []
    give_qtys: List[int] = []
    remaining = needed

    for item_id, qty in stacks:
        if remaining <= 0:
            break
        take = min(qty, remaining)
        if take > 0:
            give_ids.append(item_id)
            give_qtys.append(take)
            remaining -= take

    if remaining > 0:
        return [], []
    return give_ids, give_qtys


def _find_war_supply_item_id() -> int:
    """Find the item_id of War Supply in the collector's current offer list."""
    offered = GLOBAL_CACHE.Trading.Collector.GetOfferedItems() or []
    for item_id in offered:
        if Item.GetModelID(item_id) == _WAR_SUPPLY_MODEL_ID:
            return item_id
    return 0


def _exchange_orders():
    war_supply_item_id = _find_war_supply_item_id()
    if war_supply_item_id == 0:
        ConsoleLog(MODULE_NAME,
                   "War Supply not found in collector offers — make sure the collector dialog is open.",
                   Py4GW.Console.MessageType.Warning)
        return

    stacks = _get_order_stacks()
    total  = sum(qty for _, qty in stacks)
    ConsoleLog(MODULE_NAME,
               f"Starting exchange: {total} Confessor's Orders → {total // _EXCHANGE_RATE} War Supplies.",
               Py4GW.Console.MessageType.Info)

    while True:
        stacks = _get_order_stacks()
        give_ids, give_qtys = _build_turn_in(stacks, _EXCHANGE_RATE)

        if not give_ids:
            break   # not enough orders remaining across all stacks

        GLOBAL_CACHE.Trading.Collector.ExchangeItem(
            war_supply_item_id, 0,
            give_ids, give_qtys
        )

        # Wait for server to confirm the transaction
        elapsed = 0
        while not GLOBAL_CACHE.Trading.IsTransactionComplete() and elapsed < _TRANSACTION_TIMEOUT_MS:
            yield from Routines.Yield.wait(100)
            elapsed += 100

        yield from Routines.Yield.wait(200)   # brief settle between exchanges

    ConsoleLog(MODULE_NAME, "Exchange complete.", Py4GW.Console.MessageType.Info)


def main():
    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        stacks    = _get_order_stacks()
        total     = sum(qty for _, qty in stacks)
        exchanges = total // _EXCHANGE_RATE

        PyImGui.text(f"Confessor's Orders : {total}")
        PyImGui.text(f"War Supplies yield : {exchanges}")
        PyImGui.separator()

        if exchanges > 0:
            if PyImGui.button("Exchange All"):
                GLOBAL_CACHE.Coroutines.append(_exchange_orders())
        else:
            PyImGui.text("(need at least 3 orders)")

    PyImGui.end()


if __name__ == "__main__":
    main()
