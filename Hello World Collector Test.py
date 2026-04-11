import Py4GW
import PyImGui

from Py4GWCoreLib import GLOBAL_CACHE, Item
from Py4GWCoreLib.UIManager import UIManager


MODULE_NAME = "HelloWorldCollectorTest"


class State:
    def __init__(self):
        self.window_open = True
        self.receive_model_id = 12
        self.request_item_id = 0
        self.cost = 100
        self.material_model_1 = 948
        self.material_qty_1 = 4
        self.material_model_2 = 946
        self.material_qty_2 = 1
        self.last_status = "Idle"


state = State()


def _log(message: str, msg_type=Py4GW.Console.MessageType.Info) -> None:
    Py4GW.Console.Log(MODULE_NAME, message, msg_type)
    state.last_status = message


def _refresh_offered_item_id() -> None:
    offered_items = GLOBAL_CACHE.Trading.Crafter.GetOfferedItems() or []
    state.request_item_id = 0
    for item_id in offered_items:
        if Item.GetModelID(item_id) == state.receive_model_id:
            state.request_item_id = item_id
            break

    if state.request_item_id == 0:
        _log(f"No crafter offer found for model {state.receive_model_id}", Py4GW.Console.MessageType.Warning)
    else:
        _log(f"Resolved request item id {state.request_item_id} from receive model {state.receive_model_id}")


def _resolve_trade_item_ids() -> tuple[list[int], list[int]] | None:
    requested_models = [state.material_model_1, state.material_model_2]
    requested_quantities = [state.material_qty_1, state.material_qty_2]
    trade_item_ids: list[int] = []
    trade_item_quantities: list[int] = []

    for model_id, required_quantity in zip(requested_models, requested_quantities):
        remaining_quantity = int(required_quantity)

        for item_id in GLOBAL_CACHE.Inventory.GetAllInventoryItemIds():
            if item_id == 0:
                continue
            if Item.GetModelID(item_id) != model_id:
                continue

            item_quantity = int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id) or 1)
            if item_quantity <= 0:
                continue

            used_quantity = min(item_quantity, remaining_quantity)
            trade_item_ids.append(item_id)
            trade_item_quantities.append(used_quantity)
            remaining_quantity -= used_quantity

            if remaining_quantity <= 0:
                break

        if remaining_quantity > 0:
            _log(
                f"Could not resolve enough bag item ids for model {model_id} qty {required_quantity}",
                Py4GW.Console.MessageType.Warning,
            )
            return None

    return trade_item_ids, trade_item_quantities


def _send_exchange() -> None:
    if state.request_item_id <= 0:
        _log("Request item id is 0. Resolve it first or enter it manually.", Py4GW.Console.MessageType.Warning)
        return

    trade_payload = _resolve_trade_item_ids()
    if trade_payload is None:
        return

    material_ids, material_qtys = trade_payload

    GLOBAL_CACHE.Trading.Crafter.CraftItem(
        state.request_item_id,
        state.cost,
        material_ids,
        material_qtys,
    )
    _log(
        "Sent Crafter.CraftItem("
        f"item_id={state.request_item_id}, cost={state.cost}, "
        f"item_list={material_ids}, item_quantities={material_qtys})"
    )


def _click_customize_weapon() -> None:
    frame_id = UIManager.GetFrameIDByCustomLabel(frame_label="Merchant.CustomizeWeaponButton")
    if frame_id <= 0:
        _log("Customize weapon button alias was not resolved.", Py4GW.Console.MessageType.Warning)
        return
    if not UIManager.FrameExists(frame_id):
        _log(f"Customize weapon button frame {frame_id} is not visible.", Py4GW.Console.MessageType.Warning)
        return

    UIManager.FrameClick(frame_id)
    _log(f"Clicked Merchant.CustomizeWeaponButton (frame_id={frame_id})")


def draw_window() -> None:
    if not state.window_open:
        return

    if PyImGui.begin("Hello World Collector Test", state.window_open):
        PyImGui.text("Manual crafter request tester")
        PyImGui.separator()

        PyImGui.text_wrapped("Use 'Receive model id' only to resolve the real request item id from the open crafter dialog.")
        state.receive_model_id = PyImGui.input_int("Receive model id", state.receive_model_id)
        state.request_item_id = PyImGui.input_int("Request item id", state.request_item_id)
        state.cost = PyImGui.input_int("Cost", state.cost)
        state.material_model_1 = PyImGui.input_int("Material model 1", state.material_model_1)
        state.material_qty_1 = PyImGui.input_int("Material qty 1", state.material_qty_1)
        state.material_model_2 = PyImGui.input_int("Material model 2", state.material_model_2)
        state.material_qty_2 = PyImGui.input_int("Material qty 2", state.material_qty_2)

        if PyImGui.button("Resolve Request Item ID"):
            _refresh_offered_item_id()

        if PyImGui.button("Send Craft Request"):
            _send_exchange()

        if PyImGui.button("Click Customize Weapon"):
            _click_customize_weapon()

        PyImGui.separator()
        PyImGui.text(f"Transaction complete: {GLOBAL_CACHE.Trading.IsTransactionComplete()}")
        customize_frame_id = UIManager.GetFrameIDByCustomLabel(frame_label="Merchant.CustomizeWeaponButton")
        PyImGui.text(f"Customize button frame id: {customize_frame_id}")
        PyImGui.text(f"Customize button visible: {customize_frame_id > 0 and UIManager.FrameExists(customize_frame_id)}")

        offered_items = GLOBAL_CACHE.Trading.Crafter.GetOfferedItems() or []
        PyImGui.text(f"Crafter offers visible: {len(offered_items)}")
        if PyImGui.collapsing_header("Crafter Offers"):
            for item_id in offered_items:
                model_id = Item.GetModelID(item_id)
                PyImGui.bullet_text(f"item_id={item_id} model_id={model_id}")

        PyImGui.separator()
        PyImGui.text_wrapped(
            "Axe recipe test values:"
            " receive model 12, cost 100, material 1 model 948 qty 4, material 2 model 946 qty 1."
        )
        PyImGui.text_wrapped(
            "Actual request shape:"
            f" Crafter.CraftItem(item_id={state.request_item_id}, cost={state.cost}, "
            "item_list=[resolved bag item ids], item_quantities=[resolved per-stack quantities])"
        )
        PyImGui.text_wrapped(f"Last status: {state.last_status}")

    PyImGui.end()


def main() -> None:
    try:
        draw_window()
    except Exception as exc:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {exc}", Py4GW.Console.MessageType.Error)


if __name__ == "__main__":
    main()
