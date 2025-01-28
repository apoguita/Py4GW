# Necessary Imports
import Py4GW        #Miscelanious functions and classes
import PyImGui    #ImGui wrapper
import PyMap        #Map functions and classes
import PyAgent      #Agent functions and classes
import PyPlayer     #Player functions and classes
import PyParty      #Party functions and classes
import PyItem       #Item functions and classes
import PyInventory  #Inventory functions and classes
import PySkill      #Skill functions and classes
import PySkillbar   #Skillbar functions and classes
import PyMerchant   #Merchant functions and classes
import traceback    #traceback to log stack traces
# End Necessary Imports

module_name = "PyItem_DEMO"

# Variables to store input for interactive methods
input_int_value = 0

def DrawWindow():
    global module_name
    global input_int_value

    if PyImGui.begin(module_name):
        # Input Item ID
        input_int_value = PyImGui.input_int("Item ID", input_int_value)
        PyImGui.separator()

        if input_int_value != 0:
            item_instance = PyItem.PyItem(input_int_value)            
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


# main() must exist in every script and is the entry point for your script's execution.
def main():
    try:
        DrawWindow()

    # Handle specific exceptions to provide detailed error messages
    except ImportError as e:
        Py4GW.Console.Log(module_name, f"ImportError encountered: {str(e)}")
    except ValueError as e:
        Py4GW.Console.Log(module_name, f"ValueError encountered: {str(e)}")
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Unexpected error encountered: {str(e)}")
    finally:
        pass  # Replace with your actual code

# This ensures that main() is called when the script is executed directly.
if __name__ == "__main__":
    main()
