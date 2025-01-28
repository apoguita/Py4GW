# Necessary Imports
import Py4GW        #Miscelanious functions and classes
import PyImGui     #ImGui wrapper
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


module_name = "PyAgent DEMO"

input_int_value = 0

def draw_window():
    global module_name
    global input_int_value

    if PyImGui.begin(module_name):

        input_int_value = PyImGui.input_int("Agent ID", input_int_value)
        PyImGui.separator()

        if input_int_value != 0:
            agent_instance = PyAgent.PyAgent(input_int_value)
            PyImGui.text(f"Agent ID: {agent_instance.id}")
            PyImGui.text(f"Position: ({agent_instance.x}, {agent_instance.y}, {agent_instance.z})")
            PyImGui.text(f"Z Plane: {agent_instance.zplane}")
            PyImGui.text(f"Rotation Angle: {agent_instance.rotation_angle}")
            PyImGui.text(f"Rotation Cosine: {agent_instance.rotation_cos}")
            PyImGui.text(f"Rotation Sine: {agent_instance.rotation_sin}")
            PyImGui.text(f"Velocity X: {agent_instance.velocity_x}")
            PyImGui.text(f"Velocity Y: {agent_instance.velocity_y}")
            PyImGui.text(f"Is Living: {'Yes' if agent_instance.is_living else 'No'}")

            if PyImGui.collapsing_header("Attributes"):
                for attribute in agent_instance.attributes:
                    PyImGui.text(f"{attribute.GetName()} - Base Level: {attribute.level_base}, Level: {attribute.level}")

            if PyImGui.collapsing_header("Living Agent Fields"):
                PyImGui.text(f"Level: {agent_instance.living_agent.level}")
                PyImGui.text(f"Allegiance: {agent_instance.living_agent.allegiance.GetName()}")
                PyImGui.text(f"HP: {agent_instance.living_agent.hp}/{agent_instance.living_agent.max_hp} (Regen: {agent_instance.living_agent.hp_regen})")
                PyImGui.separator()
                PyImGui.text(f"Is Player: {'Yes' if agent_instance.living_agent.is_player else 'No'}")
                PyImGui.text(f"Is NPC: {'Yes' if agent_instance.living_agent.is_npc else 'No'}")
                PyImGui.text(f"Is Spawned: {'Yes' if agent_instance.living_agent.is_spawned else 'No'}")

                if PyImGui.collapsing_header("Explorable Exclusive Fields"):
                    PyImGui.text(f"Is Bleeding: {'Yes' if agent_instance.living_agent.is_bleeding else 'No'}")
                    PyImGui.text(f"Is Conditioned: {'Yes' if agent_instance.living_agent.is_conditioned else 'No'}")
                    PyImGui.text(f"Is Crippled: {'Yes' if agent_instance.living_agent.is_crippled else 'No'}")
                    PyImGui.text(f"Is Dead: {'Yes' if agent_instance.living_agent.is_dead else 'No'}")
                    PyImGui.text(f"Is Deep Wounded: {'Yes' if agent_instance.living_agent.is_deep_wounded else 'No'}")
                    PyImGui.text(f"Is Poisoned: {'Yes' if agent_instance.living_agent.is_poisoned else 'No'}")
                    PyImGui.text(f"Is Enchanted: {'Yes' if agent_instance.living_agent.is_enchanted else 'No'}")
                    PyImGui.text(f"Is Degen Hexed: {'Yes' if agent_instance.living_agent.is_degen_hexed else 'No'}")
                    PyImGui.text(f"Is Hexed: {'Yes' if agent_instance.living_agent.is_hexed else 'No'}")
                    PyImGui.text(f"Is Weapon Spelled: {'Yes' if agent_instance.living_agent.is_weapon_spelled else 'No'}")
                    PyImGui.text(f"In Combat Stance: {'Yes' if agent_instance.living_agent.in_combat_stance else 'No'}")
                    PyImGui.text(f"Is Dead (By TypeMap): {'Yes' if agent_instance.living_agent.is_dead_by_typemap else 'No'}")
                    PyImGui.text(f"Is Knocked Down: {'Yes' if agent_instance.living_agent.is_knocked_down else 'No'}")
                    PyImGui.text(f"Is Moving: {'Yes' if agent_instance.living_agent.is_moving else 'No'}")
                    PyImGui.text(f"Is Attacking: {'Yes' if agent_instance.living_agent.is_attacking else 'No'}")
                    PyImGui.text(f"Is Casting: {'Yes' if agent_instance.living_agent.is_casting else 'No'}")
                    PyImGui.text(f"Is Idle: {'Yes' if agent_instance.living_agent.is_idle else 'No'}")
                    PyImGui.text(f"Is Alive: {'Yes' if agent_instance.living_agent.is_alive else 'No'}")
                    PyImGui.text(f"Weapon: {agent_instance.living_agent.weapon_type.GetName()}")
                    PyImGui.separator()

                if PyImGui.collapsing_header("Enemy Exclusive Fields"):
                    PyImGui.text(f"Has Quest: {'Yes' if agent_instance.living_agent.has_quest else 'No'}")
                    PyImGui.text(f"Has Boss Glow: {'Yes' if agent_instance.living_agent.has_boss_glow else 'No'}")
                    PyImGui.separator()

                if PyImGui.collapsing_header("Ally Exclusive Fields"):
                    PyImGui.text(f"Primary: {agent_instance.living_agent.profession.GetName()}")
                    PyImGui.text(f"Secondary: {agent_instance.living_agent.secondary_profession.GetName()}")
                    PyImGui.text(f"Short Name: {agent_instance.living_agent.profession.GetShortName()}/{agent_instance.living_agent.secondary_profession.GetShortName()}")
                    PyImGui.text(f"Can Be Viewed in Party Window: {'Yes' if agent_instance.living_agent.can_be_viewed_in_party_window else 'No'}")

                    if PyImGui.collapsing_header("Henchmen / Hero / Spirit / Pet Fields"):
                        PyImGui.text(f"Owner ID: {agent_instance.living_agent.owner_id}")

                    if PyImGui.collapsing_header("Player Exclusive Fields"):
                        PyImGui.text(f"Login Number: {agent_instance.living_agent.login_number}")
                        PyImGui.text(f"Name: {agent_instance.living_agent.name}")
                        PyImGui.text(f"Player Number: {agent_instance.living_agent.player_number}")
                        PyImGui.text(f"Energy: {agent_instance.living_agent.energy}/{agent_instance.living_agent.max_energy} (Regen: {agent_instance.living_agent.energy_regen})")
                        PyImGui.text(f"Dagger Status: {agent_instance.living_agent.dagger_status}")
                        PyImGui.text(f"Is Hiding Cape: {'Yes' if agent_instance.living_agent.is_hiding_cape else 'No'}")
                        PyImGui.text(f"Is Being Observed: {'Yes' if agent_instance.living_agent.is_being_observed else 'No'}")

                PyImGui.separator()

            PyImGui.text(f"Is Item: {'Yes' if agent_instance.is_item else 'No'}")
            if PyImGui.collapsing_header("Item Agent Fields"):
                PyImGui.text(f"Agent ID: {agent_instance.item_agent.agent_id}")
                PyImGui.text(f"Owner ID: {agent_instance.item_agent.owner_id}")
                PyImGui.text(f"Item ID: {agent_instance.item_agent.item_id}")
                PyImGui.separator()

            PyImGui.text(f"Is Gadget: {'Yes' if agent_instance.is_gadget else 'No'}")
            if PyImGui.collapsing_header("Gadget Agent Fields"):
                PyImGui.text(f"Gadget ID: {agent_instance.gadget_agent.gadget_id}")
                PyImGui.text(f"Extra Type?: {agent_instance.gadget_agent.extra_type}")
                PyImGui.separator()

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
        pass  # Replace with your actual code

# This ensures that main() is called when the script is executed directly.
if __name__ == "__main__":
    main()
