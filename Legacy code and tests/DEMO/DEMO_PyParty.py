# Impor# Necessary Imports
import Py4GW        #Miscelanious functions and classes
import PyImGui     #ImGui wrapper
import PyParty      #Party functions and classes

# End Necessary Imports

module_name = "PyParty_DEMO"

# Create an instance of PyParty
party_instance = PyParty.PyParty()

# Variables to store input for interactive methods
hero_id_input = 0
henchman_id_input = 0
player_id_input = 0
x_pos_input = 0.0
y_pos_input = 0.0
hard_mode_flag = False

def draw_window():
    global module_name
    global party_instance
    global hero_id_input, henchman_id_input, player_id_input, x_pos_input, y_pos_input, hard_mode_flag

    party_instance.GetContext()  # Get the party context
    
    if PyImGui.begin(module_name):
        # Check if party is ticked
        PyImGui.text(f"Is All Party Ticked? {'Yes' if party_instance.tick.IsTicked() else 'No'}")
        if PyImGui.button("Toggle Party Tick"):
            party_instance.tick.ToggleTicked()
        if PyImGui.button("Set Tick Is a Toggle?"):
            party_instance.tick.SetTickToggle(True)
        PyImGui.separator()
        
        if PyImGui.collapsing_header("Party Info", PyImGui.TreeNodeFlags.DefaultOpen):
            
            # Party ID
            PyImGui.text(f"Party ID: {party_instance.party_id}")
            PyImGui.text(f"Party Size: {party_instance.party_size}")
            PyImGui.text(f"Player Count: {party_instance.party_player_count}")
            PyImGui.text(f"Hero Count: {party_instance.party_hero_count}")
            PyImGui.text(f"Henchman Count: {party_instance.party_henchman_count}")
            
            PyImGui.text(f"Is Party Defeated?: {'Yes' if party_instance.is_party_defeated else 'No'}")
            PyImGui.text(f"Is Party Loaded?: {'Yes' if party_instance.is_party_loaded else 'No'}")
            PyImGui.text(f"Is Party Leader?: {'Yes' if party_instance.is_party_leader else 'No'}")
            
            PyImGui.text(f"Is In Hard Mode: {'Yes' if party_instance.is_in_hard_mode else 'No'}")
            PyImGui.text(f"Is Hard Mode Unlocked?: {'Yes' if party_instance.is_hard_mode_unlocked else 'No'}")
            PyImGui.separator()

            # Interactive Method: Set Hard Mode
            if PyImGui.button("Set Hard Mode"):
                party_instance.SetHardMode(True)

            PyImGui.separator()

            # Players in the party
            if PyImGui.collapsing_header("Players"):

                # Interactive Method: Kick Player
                player_id_input = PyImGui.input_int("Player ID to Kick", player_id_input)

                if PyImGui.button("Invite Player"):
                    party_instance.InvitePlayer(player_id_input)

                if PyImGui.button("Kick Player"):
                    party_instance.KickPlayer(player_id_input)
                PyImGui.separator()
                
                for player in party_instance.players:
                    PyImGui.text(f"Player ID: {player.player_id}")
                    agent_id = party_instance.GetAgentByPlayerID(player.player_id)
                    PyImGui.text(f"Agent ID: {agent_id}")
                    PyImGui.text(f"Called Target ID: {player.called_target_id}")
                    PyImGui.text(f"Is Connected? {'Yes' if player.is_connected else 'No'}")
                    PyImGui.text(f"Is Ticked? {'Yes' if player.is_ticked else 'No'}")
                    PyImGui.separator()

            # Heroes in the party
            if PyImGui.collapsing_header("Heroes"):

                # Interactive Method: Add Hero
                hero_id_input = PyImGui.input_int("Hero ID to Add", hero_id_input)

                if PyImGui.button("Add Hero"):
                    party_instance.AddHero(hero_id_input)

                if PyImGui.button("Kick Hero"):
                    party_instance.KickHero(hero_id_input)

                if PyImGui.button("Kick All Heroes"):
                    party_instance.KickAllHeroes()

                PyImGui.separator()

                # Interactive Method: Flag Hero
                x_pos_input = PyImGui.input_float("Hero X Position", x_pos_input)
                y_pos_input = PyImGui.input_float("Hero Y Position", y_pos_input)

                if PyImGui.button("Flag Hero"):
                    party_instance.FlagHero(hero_id_input, x_pos_input, y_pos_input)

                if PyImGui.button("Set Hero Behavior Fight"):
                    party_instance.SetHeroBehavior(hero_id_input, 0)

                if PyImGui.button("Set Hero Behavior Guard"):
                    party_instance.SetHeroBehavior(hero_id_input, 1)

                if PyImGui.button("Set Hero Behavior Avoid"):
                    party_instance.SetHeroBehavior(hero_id_input, )

                if PyImGui.button("Cast Hero Skill"):
                    target_agent_id =27
                    skill_number = 2
                    hero_number = 1
                    party_instance.HeroUseSkill(target_agent_id, skill_number, hero_number)

                PyImGui.separator()
                
                for hero in party_instance.heroes:
                    PyImGui.text(f"Agent ID: {hero.agent_id}")
                    PyImGui.text(f"Owner Player ID: {hero.owner_player_id}")
                    PyImGui.text(f"Hero ID: {hero.hero_id.GetId()}")
                    PyImGui.text(f"Hero Name: {hero.hero_id.GetName()}")
                    PyImGui.text(f"Hero Primary: {hero.primary.GetName()}")
                    PyImGui.text(f"Hero Secondary: {hero.secondary.GetName()}")
                    PyImGui.text(f"Level: {hero.level}")
                    PyImGui.separator()
                    
                PyImGui.separator()

            # Henchmen in the party
            if PyImGui.collapsing_header("Henchmen"):

                # Interactive Method: Add Henchman
                henchman_id_input = PyImGui.input_int("Henchman ID", henchman_id_input)

                if PyImGui.button("Add Henchman"):
                    party_instance.AddHenchman(henchman_id_input)
                PyImGui.separator()

                if PyImGui.button("Kick Henchman"):
                    party_instance.KickHenchman(henchman_id_input)
                PyImGui.separator()
                
                for henchman in party_instance.henchmen:
                    PyImGui.text(f"Agent ID: {henchman.agent_id}")
                    PyImGui.text(f"Profession: {henchman.profession.GetName()}")
                    PyImGui.text(f"Level: {henchman.level}")
                    PyImGui.separator()

        PyImGui.end()


# main() must exist in every script and is the entry point for your script's execution.
def main():
    try:
        draw_window()

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
