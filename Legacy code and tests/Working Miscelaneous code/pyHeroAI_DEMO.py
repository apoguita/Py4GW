from platform import python_implementation
from Py4GWCoreLib import *
import PyHeroAI

module_name = "HeroAI Control Panel"
hero_ai_handler = PyHeroAI.PyHeroAI()

class HeroAIPlayer:
    def __init__(self, player_number):
        self.player_number = player_number
        self.update_attributes()
        self.name = ""

    def update_attributes(self):
        """ Helper function to retrieve and update all attributes. """
        self.follow = hero_ai_handler.GetFollowing(self.player_number)
        self.collision = hero_ai_handler.GetCollision(self.player_number)
        self.looting = hero_ai_handler.GetLooting(self.player_number)
        self.target = hero_ai_handler.GetTargetting(self.player_number)
        self.combat = hero_ai_handler.GetCombat(self.player_number)
        self.skills = [hero_ai_handler.GetSkill(self.player_number, i) for i in range(1, 9)]
        self.is_active = hero_ai_handler.IsActive(self.player_number)
        self.agent_id = hero_ai_handler.GetAgentID(self.player_number)
        self.energy = hero_ai_handler.GetEnergy(self.player_number)
        self.energy_regen = hero_ai_handler.GetEnergyRegen(self.player_number)

    def Update(self):
        """ Updates the instance attributes without reinitializing the object. """
        self.update_attributes()


def DrawPlayerData(player_number):
    global HeroAIPlayers

    player = HeroAIPlayer(player_number)
    player.Update()

    #if not player.is_active and player_number != 0:
        #return
    login_number = Party.Players.GetLoginNumberByAgentID(player.agent_id)
    player_name = Party.Players.GetPlayerNameByLoginNumber(login_number)

    tree_name = player_name
    if player_number == 0:
        tree_name = "Control All"
        PyImGui.set_next_item_open(True)

    if PyImGui.tree_node(tree_name):
        if PyImGui.begin_table("Player" + player.name, 5, PyImGui.TableFlags.NoFlag):
            PyImGui.table_next_row()
            PyImGui.table_next_column()

            follow_buton = ImGui.toggle_button("F", player.follow,30,30)
            ImGui.show_tooltip("Follow")
            PyImGui.table_next_column()
            collision_button = ImGui.toggle_button("C", player.collision,30,30)
            ImGui.show_tooltip("Collision")
            PyImGui.table_next_column()
            looting_button = ImGui.toggle_button("L", player.looting,30,30)
            ImGui.show_tooltip("Loot")
            PyImGui.table_next_column()
            target_button = ImGui.toggle_button("T", player.target,30,30)
            ImGui.show_tooltip("Target")
            PyImGui.table_next_column()
            combat_button = ImGui.toggle_button("X", player.combat,30,30)
            ImGui.show_tooltip("Combat")


            if looting_button != player.looting:
                hero_ai_handler.SetLooting(player.player_number, looting_button)

            if follow_buton != player.follow:
                hero_ai_handler.SetFollowing(player.player_number, follow_buton)

            if collision_button != player.collision:
                hero_ai_handler.SetCollision(player.player_number, collision_button)
                       
            if target_button != player.target:
                hero_ai_handler.SetTargetting(player.player_number, target_button)

            if combat_button != player.combat:
                hero_ai_handler.SetCombat(player.player_number, combat_button)

            PyImGui.end_table()

            PyImGui.separator()

            if PyImGui.begin_table("Skills" + str(player_number), 9, PyImGui.TableFlags.NoFlag):
                PyImGui.table_next_row()
                for i, skill in enumerate(player.skills):
                    PyImGui.table_next_column()
                    skill_button = ImGui.toggle_button(f"{i+1}", skill, 20, 20)
                    ImGui.show_tooltip(f"Skill {i+1}")
                    if skill_button != player.skills[i]:
                        hero_ai_handler.SetSkill(player.player_number, i+1, skill_button)
                PyImGui.end_table()

            PyImGui.separator() 
            PyImGui.text(f"Commands")
            if PyImGui.begin_table("PlayerCommands" + player.name, 5, PyImGui.TableFlags.NoFlag):
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                resign_button = False
                resign_button = ImGui.toggle_button("R", resign_button,30,30)
                ImGui.show_tooltip("Resign")
                PyImGui.table_next_column()
                take_quest_button = False
                take_quest_button = ImGui.toggle_button("Q", take_quest_button,30,30)
                ImGui.show_tooltip("Take Quest")
                PyImGui.table_next_column()
                identify_button = False
                identify_button = ImGui.toggle_button("I", identify_button,30,30)
                ImGui.show_tooltip("Identify Items")
                PyImGui.table_next_column()
                salvage_button = False
                salvage_button = ImGui.toggle_button("S", salvage_button,30,30)
                ImGui.show_tooltip("Salvage First Item")
                PyImGui.table_next_column()
                PyImGui.end_table()

                if resign_button:
                    hero_ai_handler.Resign(player.player_number)

                if take_quest_button:
                    hero_ai_handler.TakeQuest(player.player_number)

                if identify_button:
                    hero_ai_handler.Identify(player.player_number)

                if salvage_button:
                    hero_ai_handler.Salvage(player.player_number)

            PyImGui.tree_pop()


# Example of additional utility function
def DrawWindow():
    global module_name, hero_ai_handler
    try:
        if PyImGui.begin(module_name, PyImGui.WindowFlags.AlwaysAutoResize):
            DrawPlayerData(0)
            if PyImGui.collapsing_header("Party"):
                for i in range(1,9):
                    DrawPlayerData(i)

            PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

# Example of additional utility function
flag_x = 0.0
flag_y = 0.0
player_flag = 0

def DrawFlaggingWindow():
    global module_name, hero_ai_handler
    global flag_x, flag_y, player_flag
    try:
        if PyImGui.begin("Flagging", PyImGui.WindowFlags.AlwaysAutoResize):

            player_x, player_y = Player.GetXY()
            PyImGui.text(f"Player x: {player_x}")
            PyImGui.text(f"Player y: {player_y}")
            PyImGui.separator()
            flag_x = PyImGui.input_float("Flag X", flag_x)
            flag_y = PyImGui.input_float("Flag Y", flag_y)
            player_flag = PyImGui.input_int("Player Flag", player_flag)
            PyImGui.text("0 =  All")

            if PyImGui.button("Flag"):
                hero_ai_handler.FlagAIHero(player_flag, flag_x, flag_y)

            if PyImGui.button("UnFlag"):
                hero_ai_handler.UnFlagAIHero(player_flag)

            PyImGui.end()
    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(module_name, f"Error in DrawFlaggingWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


# main function must exist in every script and is the entry point for your script's execution.
def main():
    global module_name
    try:
        if Map.IsMapReady() and Party.IsPartyLoaded():
            DrawWindow()
            if Map.IsExplorable():
                DrawFlaggingWindow()

    # Handle specific exceptions to provide detailed error messages
    except ImportError as e:
        Py4GW.Console.Log(module_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(module_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(module_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(module_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        # Optional: Code that will run whether an exception occurred or not
        #Py4GW.Console.Log(module_name, "Execution of Main() completed", Py4GW.Console.MessageType.Info)
        # Place any cleanup tasks here
        pass

# This ensures that Main() is called when the script is executed directly.
if __name__ == "__main__":
    main()

