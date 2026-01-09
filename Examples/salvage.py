from Py4GWCoreLib import *


start_salvage = False
salvage_started = False
salvage_timer = Timer()
salvage_finished = False

inventory = PyInventory.PyInventory() 

def DrawWindow():
    global start_salvage, salvage_started,salvage_finished , inventory, salvage_timer

    if PyImGui.begin("Hello World!"):
        if PyImGui.button(f"salvage"):
            start_salvage = True

        if PyImGui.button(f"continue salvage"):
            inventory.ContinueSalvage()

        if PyImGui.button(f"finish salvage"):
            inventory.FinishSalvage()
            salvage_finished = True
            salvage_started = False
            start_salvage = False

        if start_salvage and not salvage_started:
            salvage_kit_id = Inventory.GetFirstSalvageKit()
            if salvage_kit_id == 0:
                Py4GW.Console.Log("SalvageFirst", "No salvage kit found.")
                return False

            # Find the first salvageable item based on the rarity filter
            salvage_item_id = Inventory.GetFirstSalvageableItem()
            if salvage_item_id == 0:
                Py4GW.Console.Log("SalvageFirst", "No salvageable item found.")
                return False

            # Use the Salvage Kit to salvage the item
            inventory = PyInventory.PyInventory()
            inventory.StartSalvage(salvage_kit_id, salvage_item_id)
            salvage_started = True
            salvage_finished = False
            salvage_timer.Start()

            inventory.ContinueSalvage()

            inventory.FinishSalvage()
            salvage_finished = True
            salvage_started = False
            start_salvage = False



        
    PyImGui.end()


def main():
        DrawWindow()

if __name__ == "__main__":
    main()

