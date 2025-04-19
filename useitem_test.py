from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"
timer = Timer()
timer.Start()

def useitem(model_id):
    item = Item.GetItemIdFromModelID(model_id)
    Inventory.UseItem(item)

def main():
    global timer
    if PyImGui.begin("timer test"):
        if PyImGui.button("use Item"):
            useitem(30847)
            
        
    PyImGui.end()
    
if __name__ == "__main__":
    main()
