from Py4GWCoreLib import *
import json

MODULE_NAME = "Character Inventory Logger"
file_name = "inventory_data.json"

class ItemDataHandler:
    def write_item_data(self, item_data):
        try:
            with open("item_data.json", "w") as file:
                json.dump(item_data, file)
            ConsoleLog(MODULE_NAME, "Item data written successfully.",Py4GW.Console.MessageType.Info)
        except Exception as e:
            Py4GW.Console.Log(MODULE_NAME, f"Error writing item data: {e}", Py4GW.Console.MessageType.Error)
            
    def ConstructItemData(self, item_id):
        item_data = {
            "account_email": Player.GetAccountEmail(),
            "character_name": Agent.GetName(Player.GetAgentID()),
            "model_id": Item.GetModelID(item_id),
            "item_name": Item.GetName(item_id),
            "quantity": Item.Properties.GetQuantity(item_id)
            
        }
        return item_data


# ========== GUI ==========

def DrawWindow():
    try:
        if PyImGui.begin(MODULE_NAME):
            if PyImGui.button("Set Character Data"):
                pass

        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Window error: {e}", Py4GW.Console.MessageType.Error)


# ========== Main Loop ==========

def main():
    DrawWindow()

if __name__ == "__main__":
    main()
