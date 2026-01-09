from Py4GWCoreLib import *
import PyImGui

MODULE_NAME = "destroy item"

model_id = 35829
def main():
    global model_id

    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        model_id = PyImGui.input_int("Item Model ID", model_id)
        
        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
        PyImGui.text(f"Found Item ID: {item_id}")

        if Routines.Checks.Inventory.IsModelInInventoryOrEquipped(model_id):
            PyImGui.text("Item is equipped or in inventory.")
        else:
            PyImGui.text("Item is not equipped or in inventory.")
            
        PyImGui.separator()
        
        if Routines.Checks.Inventory.IsModelInInventory(model_id):   
            PyImGui.text("Item is in inventory.")
        else:
            PyImGui.text("Item is not in inventory.")
            
        PyImGui.separator()
        
        if Routines.Checks.Inventory.IsModelEquipped(model_id):
            PyImGui.text("Item is equipped.")
        else:
            PyImGui.text("Item is not equipped.")

    PyImGui.end()


if __name__ == "__main__":
    main()
