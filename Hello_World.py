from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"

renderer = DXOverlay()

def main():
        try:
            if PyImGui.begin("counter"):
                gold_amount_on_character = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
                gold_amount_on_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()
                
                max_allowed_gold = 1_000_000  # Max storage limit
                available_space = max_allowed_gold - gold_amount_on_storage  # How much can be deposited
                
                PyImGui.text(f"Max Allowed Gold in Storage: {max_allowed_gold}")
                PyImGui.text(f"Gold on Character: {gold_amount_on_character}")
                PyImGui.text(f"Gold in Storage: {gold_amount_on_storage}")
                
                PyImGui.text(f"Available Space in Storage: {available_space}")
                if available_space < 0:
                    PyImGui.text("Storage is full!")
                else:
                    PyImGui.text(f"You can deposit up to {available_space} gold.")
                    
                if PyImGui.button("Deposit Gold"):
                    GLOBAL_CACHE.Inventory.DepositGold(gold_amount_on_character)
                
            PyImGui.end()
            


        except Exception as e:
            Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
            raise


    
if __name__ == "__main__":
    main()
