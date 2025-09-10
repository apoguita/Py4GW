from Py4GWCoreLib import *
import PyMap, PyImGui

MODULE_NAME = "destroy item"

model_id = 0
def main():
    global model_id

    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        model_id = PyImGui.input_int("Item Model ID", model_id)
        
        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)
        PyImGui.text(f"Found Item ID: {item_id}")
        
        if PyImGui.button("Destroy Item"):
            GLOBAL_CACHE.Inventory.DestroyItem(item_id)
            
    PyImGui.end()


if __name__ == "__main__":
    main()
