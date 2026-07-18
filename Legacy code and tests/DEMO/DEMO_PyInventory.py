# Necessary Imports
import Py4GW        #Miscelanious functions and classes
import PyImGui      #ImGui wrapper
import PyItem       #Item functions and classes
import PyInventory  #Inventory functions and classes

# End Necessary Imports

from enum import Enum

# Define the Bag enum in Python if not already done
class Bag(Enum):
    NoBag = 0
    Backpack = 1
    Belt_Pouch = 2
    Bag_1 = 3
    Bag_2 = 4
    Equipment_Pack = 5
    Material_Storage = 6
    Unclaimed_Items = 7
    Storage_1 = 8
    Storage_2 = 9
    Storage_3 = 10
    Storage_4 = 11
    Storage_5 = 12
    Storage_6 = 13
    Storage_7 = 14
    Storage_8 = 15
    Storage_9 = 16
    Storage_10 = 17
    Storage_11 = 18
    Storage_12 = 19
    Storage_13 = 20
    Storage_14 = 21
    Equipped_Items = 22
    Max = 23

Module_Name = "PyInventory DEMO"
checkbox_state = {}
input_pick = 0
pick_call = False
input_drop = 0
input_qty = 1
input_equip_item_id = 0
input_equip_agent_id = 0
input_use_item_id = 0
input_gold_deposit = 0
input_gold_drop = 0
input_gold_withdraw = 0
input_destroy_item_id = 0
input_identify_kit_id = 0
input_identify_item_id = 0
salv_kit_id = 0
salv_item_id = 0


def draw_item_window(ItemID):
    if PyImGui.begin(f"Item: {ItemID}"):

        if ItemID != 0:
            item_instance = PyItem.Item(ItemID)            
            PyImGui.text(f"Item ID: {item_instance.item_id}")
            PyImGui.text(f"Agent ID: {item_instance.agent_id}")
            PyImGui.text(f"Modifiers Count: {len(item_instance.modifiers)}")
            
            if len(item_instance.modifiers) == 0:
                PyImGui.text("No Modifiers")
            else:
                for idx, modifier in enumerate(item_instance.modifiers):
                    PyImGui.text(f"Modifier {idx + 1}:")
                    PyImGui.text(f"  {modifier.ToString()}")
                    PyImGui.separator()

            PyImGui.text(f"Is Customized: {'Yes' if item_instance.is_customized else 'No'}")
            PyImGui.text(f"Item Type: {item_instance.item_type.GetName()}")
            PyImGui.text(f"Dye Info: {item_instance.dye_info.ToString()}")
            PyImGui.text(f"Value: {item_instance.value}")
            PyImGui.text(f"Interaction: {item_instance.interaction}")
            PyImGui.text(f"Model ID: {item_instance.model_id}")
            PyImGui.text(f"Item Formula: {item_instance.item_formula}")
            PyImGui.text(f"Is Material Salvageable: {item_instance.is_material_salvageable}")
            PyImGui.text(f"Quantity: {item_instance.quantity}")
            PyImGui.text(f"Equipped: {item_instance.equipped}")
            PyImGui.text(f"Profession: {item_instance.profession}")
            PyImGui.text(f"Slot: {item_instance.slot}")
            PyImGui.text(f"Is Stackable: {'Yes' if item_instance.is_stackable else 'No'}")
            PyImGui.text(f"Is Inscribable: {'Yes' if item_instance.is_inscribable else 'No'}")
            PyImGui.text(f"Is Material: {'Yes' if item_instance.is_material else 'No'}")
            PyImGui.text(f"Is ZCoin: {'Yes' if item_instance.is_zcoin else 'No'}")
            PyImGui.text(f"Rarity: {item_instance.rarity.name}")
            PyImGui.text(f"Uses: {item_instance.uses}")
            PyImGui.text(f"Is ID Kit: {'Yes' if item_instance.is_id_kit else 'No'}")
            PyImGui.text(f"Is Salvage Kit: {'Yes' if item_instance.is_salvage_kit else 'No'}")
            PyImGui.text(f"Is Tome: {'Yes' if item_instance.is_tome else 'No'}")
            PyImGui.text(f"Is Lesser Kit: {'Yes' if item_instance.is_lesser_kit else 'No'}")
            PyImGui.text(f"Is Expert Salvage Kit: {'Yes' if item_instance.is_expert_salvage_kit else 'No'}")
            PyImGui.text(f"Is Perfect Salvage Kit: {'Yes' if item_instance.is_perfect_salvage_kit else 'No'}")
            PyImGui.text(f"Is Weapon: {'Yes' if item_instance.is_weapon else 'No'}")
            PyImGui.text(f"Is Armor: {'Yes' if item_instance.is_armor else 'No'}")
            PyImGui.text(f"Is Salvageable: {'Yes' if item_instance.is_salvageable else 'No'}")
            PyImGui.text(f"Is Inventory Item: {'Yes' if item_instance.is_inventory_item else 'No'}")
            PyImGui.text(f"Is Storage Item: {'Yes' if item_instance.is_storage_item else 'No'}")
            PyImGui.text(f"Is Rare Material: {'Yes' if item_instance.is_rare_material else 'No'}")
            PyImGui.text(f"Is Offered In Trade: {'Yes' if item_instance.is_offered_in_trade else 'No'}")
            PyImGui.text(f"Is Sparkly: {'Yes' if item_instance.is_sparkly else 'No'}")
            PyImGui.text(f"Is Identified: {'Yes' if item_instance.is_identified else 'No'}")
            PyImGui.text(f"Is Prefix Upgradable: {'Yes' if item_instance.is_prefix_upgradable else 'No'}")
            PyImGui.text(f"Is Suffix Upgradable: {'Yes' if item_instance.is_suffix_upgradable else 'No'}")
            PyImGui.text(f"Is Stackable: {'Yes' if item_instance.is_stackable else 'No'}")
            PyImGui.text(f"Is Usable: {'Yes' if item_instance.is_usable else 'No'}")
            PyImGui.text(f"Is Tradable: {'Yes' if item_instance.is_tradable else 'No'}")
            PyImGui.text(f"Is Inscription: {'Yes' if item_instance.is_inscription else 'No'}")
            PyImGui.text(f"Is Rarity Blue: {'Yes' if item_instance.is_rarity_blue else 'No'}")
            PyImGui.text(f"Is Rarity Purple: {'Yes' if item_instance.is_rarity_purple else 'No'}")
            PyImGui.text(f"Is Rarity Green: {'Yes' if item_instance.is_rarity_green else 'No'}")
            PyImGui.text(f"Is Rarity Gold: {'Yes' if item_instance.is_rarity_gold else 'No'}")

        PyImGui.end()

# Define grouped bags for easier organization
inventory_bags = [Bag.Backpack, Bag.Belt_Pouch, Bag.Bag_1, Bag.Bag_2, Bag.Equipment_Pack]
vault_bags = [Bag.Material_Storage, Bag.Storage_1, Bag.Storage_2, Bag.Storage_3, Bag.Storage_4, 
              Bag.Storage_5, Bag.Storage_6, Bag.Storage_7, Bag.Storage_8, Bag.Storage_9, 
              Bag.Storage_10, Bag.Storage_11, Bag.Storage_12, Bag.Storage_13, Bag.Storage_14]
unclaimed_items = [Bag.Unclaimed_Items]
equipped_items = [Bag.Equipped_Items]

def display_bags(group_name, bags):
    """Helper function to display items in a group of bags"""
    if PyImGui.collapsing_header(f"{group_name}"):
        for bag_enum in bags:
            bag_instance = PyInventory.Bag(bag_enum.value, bag_enum.name)
            if PyImGui.collapsing_header(f"{bag_enum.name}"):
                PyImGui.text(f"BagID: {bag_instance.id}")
                PyImGui.text(f"Bag Name: {bag_instance.name}")
                PyImGui.text(f"Container Item: {bag_instance.container_item}")
                PyImGui.text(f"items_count: {bag_instance.items_count} (Static from GW)")
                PyImGui.text(f"Item Count {bag_instance.GetItemCount()} (Dynamic from Vector)")
                PyImGui.text(f"IsInventoryBag: {'Yes' if bag_instance.is_inventory_bag else 'No'}")
                PyImGui.text(f"IsStorageBag: {'Yes' if bag_instance.is_storage_bag else 'No'}")
                PyImGui.text(f"IsMaterialStorage: {'Yes' if bag_instance.is_material_storage else 'No'}")

                if PyImGui.collapsing_header(f"Items for {bag_enum.name}"):
                    for i, item in enumerate(bag_instance.GetItems()):
                        # Initialize checkbox state if not set
                        if item.item_id not in checkbox_state:
                            checkbox_state[item.item_id] = False

                        # Checkbox to control window visibility
                        checkbox_state[item.item_id] = PyImGui.checkbox(f"Show Item {item.item_id}", checkbox_state[item.item_id])

                        # Draw the item window if the checkbox is checked
                        if checkbox_state[item.item_id]:
                            draw_item_window(item.item_id)

                PyImGui.separator()
            PyImGui.separator()
    PyImGui.separator()

def draw_window():
    global Module_Name
    global input_pick, pick_call, input_drop, input_qty, input_equip_item_id, input_equip_agent_id
    global input_use_item_id, input_gold_deposit, input_gold_drop, input_gold_withdraw, input_destroy_item_id
    global input_identify_kit_id, input_identify_item_id, salv_kit_id, salv_item_id

    inventory = PyInventory.PyInventory()
    if PyImGui.begin(Module_Name):
        if PyImGui.collapsing_header("Methods"):
            if PyImGui.button("OpenXunlaiWindow"):
                inventory.OpenXunlaiWindow()
                
            PyImGui.separator()
        
            input_pick = PyImGui.input_int("Pick ItemID", input_pick)
            pick_call = PyImGui.checkbox("Call Target",pick_call)
            if PyImGui.button("Pickup Item"):
                inventory.PickUpItem(input_pick,pick_call)
                
            PyImGui.separator()
            PyImGui.text("Drop quantity is bugged from toolbox")
            input_drop = PyImGui.input_int("Drop ItemID", input_drop)
            input_qty = PyImGui.input_int("Quantity",input_qty)
            if PyImGui.button("Drop Item"):
                inventory.DropItem(input_drop,input_qty)
                
            PyImGui.separator()
            
            # Test EquipItem
            PyImGui.separator()
            input_equip_item_id = PyImGui.input_int("Equip ItemID", input_equip_item_id)
            input_equip_agent_id = PyImGui.input_int("Equip AgentID", input_equip_agent_id)
            if PyImGui.button("Equip Item"):
                inventory.EquipItem(input_equip_item_id, input_equip_agent_id)

            # Test UseItem
            PyImGui.separator()
            input_use_item_id = PyImGui.input_int("Use ItemID", input_use_item_id)
            if PyImGui.button("Use Item"):
                inventory.UseItem(input_use_item_id)

            # Test DestroyItem
            PyImGui.separator()
            input_destroy_item_id = PyImGui.input_int("Destroy ItemID", input_destroy_item_id)
            if PyImGui.button("Destroy Item"):
                inventory.DestroyItem(input_destroy_item_id)

            # Test IdentifyItem
            PyImGui.separator()
            input_identify_kit_id = PyImGui.input_int("ID Kit ItemID", input_identify_kit_id)
            input_identify_item_id = PyImGui.input_int("Item to Identify ID", input_identify_item_id)
            if PyImGui.button("Identify Item"):
                inventory.IdentifyItem(input_identify_kit_id, input_identify_item_id)

            # Test Gold Manipulation
            PyImGui.separator()
            input_gold_deposit = PyImGui.input_int("Deposit Gold amount", input_gold_deposit)
            if PyImGui.button("Deposit Gold"):
                inventory.DepositGold(input_gold_deposit)

            input_gold_drop = PyImGui.input_int("Drop Gold amount", input_gold_drop)
            if PyImGui.button("Drop Gold"):
                inventory.DropGold(input_gold_drop)
                
            input_gold_withdraw = PyImGui.input_int("Withdraw Gold amount", input_gold_withdraw)
            if PyImGui.button("Withdraw Gold"):
                inventory.WithdrawGold(input_gold_withdraw)

            # Test Salvage methods
            PyImGui.separator()
            salv_kit_id = PyImGui.input_int("Salvage Kit ID", salv_kit_id)
            salv_item_id = PyImGui.input_int("Item to Salvage ID", salv_item_id)
            PyImGui.text(f"Is Salvaging: {'Yes' if inventory.IsSalvaging() else 'No'}")
            PyImGui.text(f"Is Salvaging Transaction Done: {'Yes' if inventory.IsSalvageTransactionDone() else 'No'}")
            if PyImGui.button("Start Salvage"):
                inventory.StartSalvage(salv_kit_id, salv_item_id)
            #if PyImGui.button("Finish Salvage"):
            #    inventory.FinishSalvage()
              
            if inventory.IsSalvaging() and inventory.IsSalvageTransactionDone():
                inventory.FinishSalvage()

            PyImGui.separator()
        
        # Display Inventory Bags (1 to 5)
        display_bags("Inventory Bags", inventory_bags)

        # Display Unclaimed Items
        display_bags("Unclaimed Items", unclaimed_items)

        # Display Vault Bags (6, 8 to 14)
        display_bags("Vault", vault_bags)

        # Display Equipped Items (22)
        display_bags("Equipped Items", equipped_items)

    PyImGui.end()

# main() must exist in every script and is the entry point for your plugin's execution.
def main():
    try:
        draw_window()

    # Handle specific exceptions to provide detailed error messages
    except ImportError as e:
        Py4GW.Console.Log("YourModule", f"ImportError encountered: {str(e)}")
    except ValueError as e:
        Py4GW.Console.Log("YourModule", f"ValueError encountered: {str(e)}")
    except Exception as e:
        Py4GW.Console.Log("YourModule", f"Unexpected error encountered: {str(e)}")
    finally:
        # Optional: Code that will run whether an exception occurred or not
        pass  # Replace with your actual code

# This ensures that main() is called when the script is executed directly.
if __name__ == "__main__":
    main()
