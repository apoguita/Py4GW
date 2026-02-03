# Necessary Imports
import Py4GW        # Miscellaneous functions and classes
import PyImGui     # ImGui wrapper
import PyInventory  # Inventory functions and classes
import PyMerchant   # Merchant functions and classes

# End Necessary Imports

Module_Name = "PyMerchant_DEMO"

# Variables to store input for interactive methods
input_item_model_id = 0
input_quantity = 1
is_material_merchant = False  # Toggle for Material Merchant vs Regular Merchant
price_for_buy = 0
price_for_transact = 0

# Create a Merchant instance
merchant_instance = PyMerchant.PyMerchant()
#initialize item_list for revceiving list of int
item_list = []

item_id = 0
cost = 0
quantity = 1

def draw_trader_window():
    global Module_Name
    global item_list
    global merchant_instance
    global item_id, cost, quantity

    merchant_instance.update()  # Call update to check on quote status

    # Start the ImGui window
    if PyImGui.begin("Trader Functions"):

        item_list = merchant_instance.get_trader_item_list()
        quoted_item_id = merchant_instance.get_quoted_item_id()
        quoted_value = merchant_instance.get_quoted_value()
        is_transaction_complete = merchant_instance.is_transaction_complete()

        PyImGui.text("Merchant Module Demo")
        PyImGui.text(f"Quoted Item ID: {quoted_item_id}")
        PyImGui.text(f"Quoted Value: {quoted_value}")
        PyImGui.text(f"Is transaction Complete: {is_transaction_complete}")
        hovered_item = PyInventory.PyInventory().GetHoveredItemID()
        PyImGui.text(f"Hovered Item ID: {hovered_item}")

        PyImGui.separator()
        item_id = PyImGui.input_int("Item ID", item_id)
        cost = PyImGui.input_int("Cost", quoted_value)
        quantity = 1 #PyImGui.input_int("Quantity", quantity)

        if PyImGui.button("Request Trader Quote"):
            merchant_instance.trader_request_quote(item_id)

        if PyImGui.button("Request Trader Sell Quote"):
            merchant_instance.trader_request_sell_quote(item_id)

        if PyImGui.button("Buy Trader Item"):
            merchant_instance.trader_buy_item(item_id, cost, quantity)

        if PyImGui.button("Sell Trader Item"):
            merchant_instance.trader_sell_item(item_id, cost, quantity)

        PyImGui.text("Items offered by the merchant:")

        if PyImGui.collapsing_header("Item List"):
            for item in item_list:
                PyImGui.text(f"Item ID: {item}")  # Display each item ID
        
        PyImGui.end()

item_id2, cost2, quantity2 = 0, 0, 1
def draw_merchant_window():
    global Module_Name
    global item_list
    global merchant_instance
    global item_id2, cost2, quantity2

    merchant_instance.update()  # Call update to check on quote status

    # Start the ImGui window
    if PyImGui.begin("Merchant Functions"):

        item_list = merchant_instance.get_trader_item_list()
        mechant_item_list = merchant_instance.get_merchant_item_list()
        quoted_item_id = merchant_instance.get_quoted_item_id()
        quoted_value = merchant_instance.get_quoted_value()
        is_transaction_complete = merchant_instance.is_transaction_complete()

        PyImGui.text("Merchant Module Demo")
        PyImGui.text(f"Quoted Item ID: {quoted_item_id}")
        PyImGui.text(f"Quoted Value: {quoted_value}")
        PyImGui.text(f"Is transaction Complete: {is_transaction_complete}")

        PyImGui.separator()
        item_id2 = PyImGui.input_int("Item ID", item_id2)
        cost2 = PyImGui.input_int("Cost", cost2)
        quantity2 = PyImGui.input_int("Quantity", quantity2)

        PyImGui.separator()
        PyImGui.text("Merchant Module Demo")

        if PyImGui.button("Buy Merchant Item"):
            merchant_instance.merchant_buy_item(item_id2, cost2, quantity2)

        if PyImGui.button("Sell Merchant Item"):
            merchant_instance.merchant_sell_item(item_id2, cost2, quantity2)

        PyImGui.separator()
        PyImGui.text("Items offered by the merchant:")

        if PyImGui.collapsing_header("Item List"):
            for item in mechant_item_list:
                PyImGui.text(f"Item ID: {item}")  # Display each item ID

        PyImGui.end()

item_id3, cost3, quantity3 = 0, 0, 1
input_item3, input_quantity3 = 0, 1
crafter_item_list = []
crafter_item_quantities = []

def draw_crafter_window():
    global Module_Name
    global crafter_item_list
    global item_quantities
    global input_item3, input_quantity3
    global item_id3, cost3, quantity3, merchant_instance

    merchant_instance.update()  # Call update to check on quote status

    # Start the ImGui window
    if PyImGui.begin("Crafter Functions"):

        quoted_item_id = merchant_instance.get_quoted_item_id()
        quoted_value = merchant_instance.get_quoted_value()
        is_transaction_complete = merchant_instance.is_transaction_complete()

        PyImGui.text("Crafter Module")
        PyImGui.separator()

        

        # Inputs to add new items
        item_id3 = PyImGui.input_int("Item to buy", item_id3)
        cost3 = PyImGui.input_int("Cost", cost3)

        PyImGui.separator()

        input_item3 = PyImGui.input_int("Item to pay with", input_item3)
        input_quantity3 = PyImGui.input_int("Quantity of (item)", input_quantity3)

        if PyImGui.button("Add Item to List"):
            if input_item3 > 0 and input_quantity3 > 0:
                crafter_item_list.append(input_item3)
                crafter_item_quantities.append(input_quantity3)

        if PyImGui.button("Clear List"):
            crafter_item_list.clear()
            crafter_item_quantities.clear

        PyImGui.separator()

        # Table to show items and quantities
        if PyImGui.begin_table("Item List Table", 2):
            PyImGui.table_setup_column("Item ID")
            PyImGui.table_setup_column("Quantity")
            PyImGui.table_headers_row()

            for item, quantity in zip(crafter_item_list, crafter_item_quantities):
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                PyImGui.text(str(item))
                PyImGui.table_set_column_index(1)
                PyImGui.text(str(quantity))

            PyImGui.end_table()

        PyImGui.separator()

        if PyImGui.button("Execute Crafting"):
            if crafter_item_list and crafter_item_quantities:
                merchant_instance.crafter_buy_item(item_id3, cost3, crafter_item_list, crafter_item_quantities)

        if PyImGui.button("Exchange with collector"):
            merchant_instance.collector_buy_item(item_id3, cost3, crafter_item_list, crafter_item_quantities)

        PyImGui.end()

def main():
    try:
        draw_trader_window()
        draw_merchant_window()
        draw_crafter_window()

    except ImportError as e:
        Py4GW.Console.Log(Module_Name, f"ImportError encountered: {str(e)}")
    except ValueError as e:
        Py4GW.Console.Log(Module_Name, f"ValueError encountered: {str(e)}")
    except Exception as e:
        Py4GW.Console.Log(Module_Name, f"Unexpected error encountered: {str(e)}")

if __name__ == "__main__":
    main()
