from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"

counter = 0

def main():
        try:
            if PyImGui.begin("counter"):
                PyImGui.text(f"Items to loot")
                items = LootConfig().GetfilteredLootArray(Range.Earshot.value, multibox_loot= True)
                if items:
                    for item in items:
                        PyImGui.text(f"{item}")
                else:
                    PyImGui.text("No items to loot")
                    
            
                
            PyImGui.end()
            


        except Exception as e:
            Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
            raise


    
if __name__ == "__main__":
    main()
