# Necessary Imports
import Py4GW        #Miscelanious functions and classes
import PyImGui     #ImGui wrapper
import PyAgent      #Agent functions and classes
import PyPlayer     #Player functions and classes

# End Necessary Imports

module_name = "PyPlayer DEMO"

checkbox_state = False
input_int_value = 0
selected_agents = {}
text_input = "dance"
x_val = 0.0
y_val = 0.0
interact_agent_id = 0
call_target = False


def draw_agent_window(module_name, input_int_value):
    if PyImGui.begin(module_name):
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
                
                if PyImGui.collapsing_header("Explorable exclusive Fields"):  
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
                    PyImGui.text(f"Is Knocked Down: {'Yes' if agent_instance.living_agent.is_knocked_down else 'No'}")
                    PyImGui.text(f"Is Moving: {'Yes' if agent_instance.living_agent.is_moving else 'No'}")
                    PyImGui.text(f"Is Attacking: {'Yes' if agent_instance.living_agent.is_attacking else 'No'}")
                    PyImGui.text(f"Is Casting: {'Yes' if agent_instance.living_agent.is_casting else 'No'}")
                    PyImGui.text(f"Is Idle: {'Yes' if agent_instance.living_agent.is_idle else 'No'}")
                    PyImGui.text(f"Is Alive: {'Yes' if agent_instance.living_agent.is_alive else 'No'}")
                    PyImGui.text(f"Weapon: {agent_instance.living_agent.weapon_type.GetName()}")
                    PyImGui.separator()
                    
                    if PyImGui.collapsing_header("Enemy exclusive Fields"): 
                        PyImGui.text(f"Has Quest: {'Yes' if agent_instance.living_agent.has_quest else 'No'}")
                        PyImGui.text(f"Has Boss Glow: {'Yes' if agent_instance.living_agent.has_boss_glow else 'No'}")
                        PyImGui.separator()
                    
                    if PyImGui.collapsing_header("Ally exclusive Fields"): 
                        PyImGui.text(f"Primary: {agent_instance.living_agent.profession.GetName()}")
                        PyImGui.text(f"Secondary: {agent_instance.living_agent.secondary_profession.GetName()}")
                        PyImGui.text(f"Short Name: {agent_instance.living_agent.profession.GetShortName()}/{agent_instance.living_agent.secondary_profession.GetShortName()}")
                        PyImGui.text(f"Can Be Viewed in Party Window: {'Yes' if agent_instance.living_agent.can_be_viewed_in_party_window else 'No'}")
                        if PyImGui.collapsing_header("Henchmen / Hero / Spirit / Pet Fields"): 
                            PyImGui.text(f"Owner ID: {agent_instance.living_agent.owner_id}") 
                        if PyImGui.collapsing_header("Player Exclusive Fields"): 
                            PyImGui.text(f"Login Number: {agent_instance.living_agent.login_number}")
                            PyImGui.text(f"Player Number: {agent_instance.living_agent.player_number}")
                            PyImGui.text(f"Name: {agent_instance.living_agent.name}")
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


def draw_window():
    global module_name, checkbox_state, selected_agents, text_input, x_val, y_val
    global interact_agent_id, call_target
    
    if PyImGui.begin(module_name):
        
        player_instance = PyPlayer.PyPlayer()
        PyImGui.text(f"Agent ID: {player_instance.id}")
        checkbox_state = PyImGui.checkbox("Show Player Agent Data", checkbox_state)
        if checkbox_state:
            draw_agent_window("Player Agent Data", player_instance.id)
        
        PyImGui.separator()
        if PyImGui.collapsing_header("Methods"):
            PyImGui.separator()
            if PyImGui.collapsing_header("SendChatCommand"):
                
                if PyImGui.collapsing_header("SendChatCommand Info"):
                    PyImGui.text("It will send a /command to chat")
                    PyImGui.text("works for in-game and toolbox commands")
                    PyImGui.text("some commands will work only with the window on focus")
                PyImGui.separator()
                PyImGui.text("/")
                PyImGui.same_line(0.0, -1.0)
                text_input = PyImGui.input_text("Enter Text", text_input)
                if PyImGui.button("Send"):
                    player_instance.SendChatCommand(text_input)
            PyImGui.separator()
                
            if PyImGui.collapsing_header("Move"):     
                x_val = PyImGui.input_float(":x", x_val)
                y_val = PyImGui.input_float(":y", y_val)
                if PyImGui.button("Go"):
                    Py4GW.Console.Log(module_name, f"Moving to ({x_val}, {y_val})")
                    player_instance.Move(x_val, y_val)
            PyImGui.separator()
            
            if PyImGui.collapsing_header("InteractAgent"):   
                if PyImGui.collapsing_header("InteractAgent Info"):
                    PyImGui.text("used for everything in game")
                    PyImGui.text("follow an ally, attacking an enemy, picking up loot, etc")
                PyImGui.separator()
                interact_agent_id = PyImGui.input_int("AgentID", interact_agent_id)
                call_target = PyImGui.checkbox("Call Target", call_target)
                if PyImGui.button("Interact"):
                    player_instance.InteractAgent(interact_agent_id, call_target)
            PyImGui.separator()


        PyImGui.separator()
        if PyImGui.collapsing_header("Agent Arrays"):
            for array_name, agent_array in {
                "Allies": player_instance.GetAllyArray(),
                "Neutrals": player_instance.GetNeutralArray(),
                "Enemies": player_instance.GetEnemyArray(),
                "Spirit Pets": player_instance.GetSpiritPetArray(),
                "Minions": player_instance.GetMinionArray(),
                "NPC Minipets": player_instance.GetNPCMinipetArray(),
                "Items": player_instance.GetItemArray(),
                "Gadgets": player_instance.GetGadgetArray(),
                "All Agents": player_instance.GetAgentArray()
            }.items():
                
                if PyImGui.collapsing_header(array_name):
                    for agent_id in agent_array:
                        checkbox_label = f"Agent {agent_id}"
                        if checkbox_label not in selected_agents:
                            selected_agents[checkbox_label] = False
                        selected_agents[checkbox_label] = PyImGui.checkbox(checkbox_label, selected_agents[checkbox_label])
                        if selected_agents[checkbox_label]:
                            draw_agent_window(f"Agent {agent_id}", agent_id)
        
        PyImGui.end()

# main() must exist in every script and is the entry point for your plugin's execution.
def main():
    try:
        draw_window()      

    # Handle specific exceptions to provide detailed error messages
    except ImportError as e:
        Py4GW.Console.Log(module_name, f"ImportError encountered: {str(e)}")
    except ValueError as e:
        Py4GW.Console.Log(module_name, f"ValueError encountered: {str(e)}")
    except Exception as e:
        # Catch-all for any other exceptions
        Py4GW.Console.Log(module_name, f"Unexpected error encountered: {str(e)}")
    finally:
        # Optional: Code that will run whether an exception occurred or not
        pass  # Replace with your actual code

# This ensures that main() is called when the script is executed directly.
if __name__ == "__main__":
    main()
