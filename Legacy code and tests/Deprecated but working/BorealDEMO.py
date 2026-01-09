# Necessary Imports
import Py4GW        #Miscelanious functions and classes
import PyImGui     #ImGui wrapper
import PyMap        #Map functions and classes
import PyAgent      #Agent functions and classes
import PyPlayer     #Player functions and classes

import PySkill      #Skill functions and classes
import PySkillbar   #Skillbar functions and classes

import traceback    #traceback to log stack traces
# End Necessary Imports
import Py4GWcorelib as CoreLib
import time

#first and last element should be placeholder for allowing pathing functions to reverse direction
outpost_coordinate_list = [(8180, -27084), (4790, -27870)]
explorable_coordinate_list = [(2928,-24873), (2724,-22040), (-371,-20086), (-3294,-18164), (-5267,-14941), (-5297,-11045), (-1969,-12627), (1165,-14245), (4565,-15956)]

class BotVariables:
    def __init__(self):
        self.bot_name = "Boreal Chest Run Demo"
        self.first_run = True
        self.state = "explorable_check"
        self.logic_active = False
        self.timer = Py4GW.Timer()
        self.move_to = CoreLib.Player.Routines.Movement.FollowXY()
        self.outpost_pathing = CoreLib.Player.Routines.Movement.PathHandler(outpost_coordinate_list)
        self.explorable_pathing = CoreLib.Player.Routines.Movement.PathHandler(explorable_coordinate_list)


bot_vars = BotVariables()
def DrawTextWithTitle(title, text_content, lines_visible=10):
    """
    Function to display a title and multi-line text in a scrollable and configurable area.
    Width is based on the main window's width with a margin.
    Height is based on the number of lines_visible.
    """
    margin = 20
    max_lines = 10
    line_padding = 4  # Add a bit of padding for readability

    # Display the title first
    PyImGui.text(title)

    # Get the current window size and adjust for margin to calculate content width
    window_width = PyImGui.get_window_size()[0]
    content_width = window_width - margin
    text_block = text_content + "\n" + Py4GW.Console.GetCredits()

    # Split the text content into lines by newline
    lines = text_block.split("\n")
    total_lines = len(lines)

    # Limit total lines to max_lines if provided
    if max_lines is not None:
        total_lines = min(total_lines, max_lines)

    # Get the line height from ImGui
    line_height = PyImGui.get_text_line_height()
    if line_height == 0:
        line_height = 10  # Set default line height if it's not valid

    # Add padding between lines and calculate content height based on visible lines
    content_height = (lines_visible * line_height) + ((lines_visible - 1) * line_padding)

    # Set up the scrollable child window with dynamic width and height
    if PyImGui.begin_child(f"ScrollableTextArea_{title}", size=(content_width, content_height), border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):

        # Get the scrolling position and window size for visibility checks
        scroll_y = PyImGui.get_scroll_y()
        scroll_max_y = PyImGui.get_scroll_max_y()
        window_size_y = PyImGui.get_window_size()[1]
        window_pos_y = PyImGui.get_cursor_pos_y()

        # Display each line only if it's visible based on scroll position
        for index, line in enumerate(lines):
            # Calculate the Y position of the line based on index
            line_start_y = window_pos_y + (index * (line_height + line_padding))

            # Calculate visibility boundaries
            line_end_y = line_start_y + line_height

            # Skip rendering if the line is above or below the visible area
            if line_end_y < scroll_y or line_start_y > scroll_y + window_size_y:
                continue

            # Render the line if it's within the visible scroll area
            PyImGui.text_wrapped(line)
            PyImGui.spacing()  # Add spacing between lines for better readability

        # End the scrollable child window
        PyImGui.end_child()



# Example of additional utility function
def DrawWindow():
    global bot_vars
    try:
        description = "This is a Tech demo showcasing basic Py4GW functionality and routines. \nits aimed as a technical showcase and a proof of work more than a full bot. \nrefer to the code to see funtionality \nthis bot leverages Toolbox functionality, you need to have some options activated \nAutomatically return to outpost on defeat \nAuto use lockpicks when interacting with locked chests"


        #width, height = 400, 500
        #PyImGui.set_next_window_size(width, height)

        if PyImGui.begin(bot_vars.bot_name):
            PyImGui.text("Boreal Chest Run Demo")
            PyImGui.separator()

            DrawTextWithTitle("ATTENTION", description)

            # Retrieve map type, map name, and free inventory slots
            map_name = CoreLib.Map.GetMapName()  # Get the map name (e.g., Boreal Station)
            free_slots = CoreLib.Inventory.GetFreeSlotCount()  # Get the number of free slots in inventory
            lockpick_count = CoreLib.Inventory.GetModelCount(22751)  # Get the number of lockpicks in inventory

            headers = ["Info", "Value"]
            data = [("Map Name", map_name),
                    ("Free Inventory Slots", free_slots),
                    ("Lockpicks", lockpick_count)]

            CoreLib.ImGui.table("Map Info Table",headers,data)

            is_moving_to_waypoint = bot_vars.move_to.GetIsFollowing()
            has_arrived_to_waypoint = bot_vars.move_to.GetHasArrived()
            elapsed_time = bot_vars.move_to.GetElapsedTime()
            distance_to_waypoint = bot_vars.move_to.GetDistanceToWaypoint()
            waypoint = bot_vars.move_to.GetWaypoint()

            headers = ["FollowXY var", "Value"]
            data = [("Is Moving to Waypoint", is_moving_to_waypoint),
                    ("Has Arrived?", has_arrived_to_waypoint),
                    ("Elapsed Time", elapsed_time),
                    ("Distance to Waypoint", distance_to_waypoint),
                    ("Waypoint", f"X: {waypoint[0]} Y: {waypoint[1]}")]

            CoreLib.ImGui.table("FollowXY Info Table",headers,data)


            bot_state = bot_vars.state
            map_instance = PyMap.PyMap()
            instance_time = map_instance.instance_time
            elapsed_time = bot_vars.timer.get_elapsed_time()

            # Convert instance_time from milliseconds to HH:mm:ss
            instance_time_seconds = instance_time / 1000  # Convert to seconds
            formatted_time = time.strftime('%H:%M:%S', time.gmtime(instance_time_seconds))

            headers = ["Info"]
            data = [f"Current state: {bot_state}",
                    f"Elapsed time: {elapsed_time}",
                    f"Instance Time: {formatted_time} - [{instance_time}]"]

            CoreLib.ImGui.table("Timers Info Table",headers,data)


            if PyImGui.collapsing_header("Buffs And Effects"):
                # Effects table
                effects_list = CoreLib.Buffs.GetEffects(CoreLib.Player.GetAgentID())
                if effects_list:
                    effects_headers = ["Effect ID", "Skill ID", "Skill Name", "Duration", "Attr. Level", "Time Remaining"]
                    effects_data = [(effect.effect_id, effect.skill_id, PySkill.Skill(effect.skill_id).id.GetName(), 
                                     effect.duration, effect.attribute_level, effect.time_remaining) for effect in effects_list]
                    CoreLib.ImGui.table("Effect Info Table", effects_headers, effects_data)

                # Buffs table
                buffs_list = CoreLib.Buffs.GetBuffs(CoreLib.Player.GetAgentID())
                if buffs_list:
                    buffs_headers = ["Buff ID", "Skill ID", "Target Agent"]
                    buffs_data = [(buff.buff_id, buff.skill_id, buff.target_agent_id) for buff in buffs_list]
                    CoreLib.ImGui.table("Buff Info Table", buffs_headers, buffs_data)


             
            # Toggle button for starting/stopping the demo
            bot_vars.logic_active = CoreLib.ImGui.toggle_button("Stop DEMO" if bot_vars.logic_active else "Start DEMO", bot_vars.logic_active)
            if not bot_vars.logic_active:
                bot_vars.state = "explorable_first_check"

            PyImGui.end()

    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(bot_vars.bot_name, f"Error in PerformTask: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def FirstRun():
    global bot_vars
    try:
        
        if bot_vars.state == "explorable_first_check":
            if CoreLib.Map.IsExplorable():
                #Is Explorable, we should start in an Outpost
                #/resign and wait for a bit
                #this bot assumes return to outpost on defeat from toolbox

                Py4GW.Console.Log(bot_vars.bot_name, "Why Are we in Explorable? we should be in an Outpost", Py4GW.Console.MessageType.Notice)
                CoreLib.Player.SendChatCommand("resign")
                
                bot_vars.timer.start()
                bot_vars.state = "resign_wait"
            else:
                Py4GW.Console.Log(bot_vars.bot_name, "Explorable check passed?", Py4GW.Console.MessageType.Notice)
                bot_vars.state = "outpost_check"

        if bot_vars.state == "resign_wait":
            if bot_vars.timer.has_elapsed(1000):
                #Waited 1 seconds, lets see if we are in an outpost
                #1 second is chosen for being as responsive as possible without spamming
                if not CoreLib.Map.IsOutpost():
                    #not in Outpost Wait another second
                    bot_vars.timer.reset()
                else:
                    bot_vars.timer.stop()
                    bot_vars.state = "outpost_check"

        if bot_vars.state == "outpost_wait":
            if bot_vars.timer.has_elapsed(2000):
                if not CoreLib.Map.IsOutpost():
                    #in Outpost Wait another second
                    bot_vars.timer.reset()
                else:
                    bot_vars.timer.stop()
                    bot_vars.state = "outpost_check"

        if bot_vars.state == "outpost_check":
            if CoreLib.Map.IsOutpost():
                if CoreLib.Map.GetMapID() != 675: #Boreal Station
                   #We are in an outpost, but not the right one
                   CoreLib.Map.Travel(675)
                   bot_vars.timer.start()
                   bot_vars.state = "outpost_wait"
                   Py4GW.Console.Log(bot_vars.bot_name, "Not in the correct Outpost, Traveling", Py4GW.Console.MessageType.Notice)
                else:
                    #We are in the right outpost
                    Py4GW.Console.Log(bot_vars.bot_name, "Correct Outpost, sanity check wait", Py4GW.Console.MessageType.Notice)
                    bot_vars.timer.start()
                    bot_vars.state = "sanity_wait"
            else:
                #We are not in an outpost, lets wait a bit
                bot_vars.timer.start()
                bot_vars.state = "outpost_wait"

        if bot_vars.state == "sanity_wait":
            if bot_vars.timer.has_elapsed(1000):

                #Loading Approprieate skillbar
                player = PyPlayer.PyPlayer()
                agent_instance = PyAgent.PyAgent(player.id)
                agent_living = agent_instance.living_agent
                skillbar_instance = PySkillbar.Skillbar()

                Py4GW.Console.Log(bot_vars.bot_name, "Loading Appropriate skillbar.", Py4GW.Console.MessageType.Notice)

                if agent_living.profession.GetName() == "Warrior":
                    skillbar_instance.LoadSkillTemplate("OQcAQ3lTQ0kAAAAAAAAAAA")
                elif agent_living.profession.GetName() == "Ranger":
                    skillbar_instance.LoadSkillTemplate("OgcAQ3lTQ0kAAAAAAAAAAA")
                elif agent_living.profession.GetName() == "Monk":
                    skillbar_instance.LoadSkillTemplate("OwcAQ3lTQ0kAAAAAAAAAAA")
                elif agent_living.profession.GetName() == "Necromancer":
                    skillbar_instance.LoadSkillTemplate("OAdAQ3lTQ0kAAAAAAAAAAA")
                elif agent_living.profession.GetName() == "Mesmer":
                    skillbar_instance.LoadSkillTemplate("OQdAQ3lTQ0kAAAAAAAAAAA")
                elif agent_living.profession.GetName() == "Elementalist":
                    skillbar_instance.LoadSkillTemplate("OgdAQ3lTQ0kAAAAAAAAAAA")
                elif agent_living.profession.GetName() == "Assassin":
                    skillbar_instance.LoadSkillTemplate("OwBAQ3lTQ0kAAAAAAAAAAA")
                elif agent_living.profession.GetName() == "Ritualist":
                    skillbar_instance.LoadSkillTemplate("OAeAQ3lTQ0kAAAAAAAAAAA")
                elif agent_living.profession.GetName() == "Paragon":
                    skillbar_instance.LoadSkillTemplate("OQeAQ3lTQ0kAAAAAAAAAAA")
                elif agent_living.profession.GetName() == "Dervish":
                    skillbar_instance.LoadSkillTemplate("OgeAQ3lTQ0kAAAAAAAAAAA")
                if agent_living.profession.GetName() != "Assassin" and agent_living.secondary_profession.GetName() != "Assassin":
                    Py4GW.Console.Log(bot_vars.bot_name, "This bot requires A/Any or Any/A to work, halting.", Py4GW.Console.MessageType.Error)
                    bot_vars.state = "end"


                free_slots = CoreLib.Inventory.GetFreeSlotCount()  # Get the number of free slots in inventory
                lockpick_count = CoreLib.Inventory.GetModelCount(22751)  # Get the number of lockpicks in inventory
                bot_vars.state = "start_from_outpost"

                if free_slots == 0:
                    Py4GW.Console.Log(bot_vars.bot_name, "Not enough Inventory Space", Py4GW.Console.MessageType.Notice)
                    bot_vars.state = "end"
                else:
                    Py4GW.Console.Log(bot_vars.bot_name, "Inventory space checked", Py4GW.Console.MessageType.Notice)

                if lockpick_count == 0:
                    Py4GW.Console.Log(bot_vars.bot_name, "No Lockpicks remaining", Py4GW.Console.MessageType.Notice)
                    bot_vars.state = "end"
                else:
                    Py4GW.Console.Log(bot_vars.bot_name, "Enough Lockpicks for run", Py4GW.Console.MessageType.Notice)


        if bot_vars.state == "start_from_outpost":
            bot_vars.first_run= False
                    
        if bot_vars.state == "end":
            bot_vars.logic_active = False
            bot_vars.first_run = True
            bot_vars.state = "explorable_first_check"

            Py4GW.Console.Log(bot_vars.bot_name, "Routines Halted", Py4GW.Console.MessageType.Error)


    except Exception as e:
        # Log and re-raise exception to ensure the main script can handle it
        Py4GW.Console.Log(bot_vars.bot_name, f"Error in FirstRun: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


def HandleOutpostMovementLogic():
    global bot_vars
    try:
        if bot_vars.state == "start_from_outpost":
            # Move to the first coordinate if not already following
            if not bot_vars.move_to.GetIsFollowing() and not bot_vars.outpost_pathing.is_finished():
                x, y = bot_vars.outpost_pathing.get_current_point_and_advance() # Get the next point in the list
                bot_vars.move_to.Move(x, y) # Move the player to the point requested
                bot_vars.state = "outpost_moving_to_waypoint"
                Py4GW.Console.Log(bot_vars.bot_name, f"Moving to ({x}:{y})", Py4GW.Console.MessageType.Notice)


        if bot_vars.state == "outpost_moving_to_waypoint":
            is_moving_to_waypoint = bot_vars.move_to.GetIsFollowing()
            has_arrived_to_waypoint = bot_vars.move_to.GetHasArrived()
            elapsed_time = bot_vars.move_to.GetElapsedTime()


            if has_arrived_to_waypoint:
                if bot_vars.outpost_pathing.is_finished(): 
                    # All waypoints have been reached
                    Py4GW.Console.Log(bot_vars.bot_name, "All waypoints reached!", Py4GW.Console.Message)
                    bot_vars.state = "outpost_end_routine"

                if bot_vars.state == "outpost_moving_to_waypoint":
                    # Move to the next coordinate if there are more
                    Py4GW.Console.Log(bot_vars.bot_name, f"Waypoint reached in ({elapsed_time}) ms.", Py4GW.Console.MessageType.Notice)
                    if not bot_vars.outpost_pathing.is_finished():
                        x, y = bot_vars.outpost_pathing.get_current_point_and_advance() # Get the next point in the list
                        bot_vars.move_to.Move(x, y) # Move the player to the point requested
                        Py4GW.Console.Log(bot_vars.bot_name, f"Moving to ({x}:{y})", Py4GW.Console.MessageType.Notice)
              
                    
               
        
    except Exception as e:
        print(f"Error during PerformLogic: {e}")

def HandleExplorableMovementLogic():
    global bot_vars
    try:
        
        if bot_vars.state == "outpost_end_routine":
            bot_vars.timer.reset()
            bot_vars.state = "explorable_check"

        if bot_vars.state == "explorable_check":
            if bot_vars.timer.has_elapsed(2000):
                bot_vars.timer.stop()
                bot_vars.state = "explorable_movement_start"

        if bot_vars.state == "explorable_movement_start":
            # Move to the first coordinate if not already following
            if not bot_vars.move_to.GetIsFollowing() and not bot_vars.explorable_pathing.is_finished():
                x, y = bot_vars.explorable_pathing.get_current_point_and_advance() # Get the next point in the list
                bot_vars.move_to.Move(x, y) # Move the player to the point requested
                bot_vars.state = "explorable_moving_to_waypoint"
                Py4GW.Console.Log(bot_vars.bot_name, f"Moving to ({x}:{y})", Py4GW.Console.MessageType.Notice)

        if bot_vars.state == "explorable_moving_to_waypoint" and bot_vars.explorable_pathing.get_position() >=3: #we skip some steps because portal name is a gadget aswell as the chest
            chest_agent = CoreLib.Agent.GetNearestGadget()
            if chest_agent != None:
                Py4GW.Console.Log(bot_vars.bot_name, f"Chest found Adjusting Follow Target to ({chest_agent.x}:{chest_agent.y})", Py4GW.Console.MessageType.Notice)
                bot_vars.move_to.SetWaypoint(chest_agent.x, chest_agent.y)
                bot_vars.state = "explorable_moving_to_chest"

        if bot_vars.state == "explorable_moving_to_waypoint":
            is_moving_to_waypoint = bot_vars.move_to.GetIsFollowing()
            has_arrived_to_waypoint = bot_vars.move_to.GetHasArrived()
            elapsed_time = bot_vars.move_to.GetElapsedTime()


            if has_arrived_to_waypoint:
                if bot_vars.state == "explorable_moving_to_waypoint":
                    Py4GW.Console.Log(bot_vars.bot_name, f"Waypoint reached in ({elapsed_time}) ms.", Py4GW.Console.MessageType.Notice)
                    if not bot_vars.explorable_pathing.is_finished():
                        x, y = bot_vars.explorable_pathing.get_current_point_and_advance() # Get the next point in the list
                        bot_vars.move_to.Move(x, y) # Move the player to the point requested
                        Py4GW.Console.Log(bot_vars.bot_name, f"Moving to ({x}:{y})", Py4GW.Console.MessageType.Notice)
                    else:
                        Py4GW.Console.Log(bot_vars.bot_name, "All waypoints reached!", Py4GW.Console.Message)
                        bot_vars.state = "all_routines_end"
                

        if bot_vars.state == "explorable_moving_to_chest":
            is_moving_to_waypoint = bot_vars.move_to.GetIsFollowing()
            has_arrived_to_waypoint = bot_vars.move_to.GetHasArrived()
            elapsed_time = bot_vars.move_to.GetElapsedTime()

            if has_arrived_to_waypoint:
                # Move to the next coordinate if there are more
                Py4GW.Console.Log(bot_vars.bot_name, f"Chest reached in ({elapsed_time}) ms.", Py4GW.Console.MessageType.Notice)
                #Open Chest
                chest_agent = CoreLib.Agent.GetNearestGadget()      
                if chest_agent != None:
                    CoreLib.Player.Interact(chest_agent.id)
                    bot_vars.timer.reset()
                    bot_vars.state = "explorable_interact_wait"

        if bot_vars.state == "explorable_interact_wait":
            if bot_vars.timer.has_elapsed(1000):
                item_agent = CoreLib.Agent.GetNearestItem()
                if item_agent != None:
                    CoreLib.Player.Interact(item_agent.id)
                    bot_vars.timer.reset()
                    bot_vars.state = "looting_wait"

        if bot_vars.state == "looting_wait":
            item_agent = CoreLib.Agent.GetNearestItem()
            if item_agent == None:
                bot_vars.state = "all_routines_end"

        if bot_vars.state == "all_routines_end":
            bot_vars.first_run = True
            bot_vars.state = "explorable_first_check"
            bot_vars.outpost_pathing.reset_path()
            bot_vars.explorable_pathing.reset_path()

            Py4GW.Console.Log(bot_vars.bot_name, f"All routines ended", Py4GW.Console.MessageType.Notice)
            Py4GW.Console.Log(bot_vars.bot_name, "Environment Reset", Py4GW.Console.MessageType.Error)
        
    except Exception as e:
        print(f"Error during PerformLogic: {e}")



def PerformLogic():
    global bot_vars
    try:

        # Check if we're in an outpost
        if CoreLib.Map.IsOutpost():
            HandleOutpostMovementLogic()
         
        if CoreLib.Map.IsExplorable():
            if bot_vars.state == "outpost_moving_to_waypoint": #something went wrong, this message should not be here
                bot_vars.state = "outpost_end_routine" #thios bot doesnt need that check, passing

            HandleExplorableMovementLogic()

    except Exception as e:
        print(f"Error during PerformLogic: {e}")


# main function must exist in every script and is the entry point for your script's execution.
def main():
    global bot_vars
    try:
        

        bot_vars.move_to.Update() #this has to be global

        if CoreLib.Map.IsMapReady():
            DrawWindow()
            if bot_vars.logic_active:
                if bot_vars.first_run:
                    FirstRun()
                else:
                    PerformLogic()


    # Handle specific exceptions to provide detailed error messages
    except ImportError as e:
        Py4GW.Console.Log(bot_vars.bot_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_vars.bot_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(bot_vars.bot_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_vars.bot_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(bot_vars.bot_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_vars.bot_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(bot_vars.bot_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_vars.bot_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        # Optional: Code that will run whether an exception occurred or not
        #Py4GW.Console.Log(module_name, "Execution of Main() completed", Py4GW.Console.MessageType.Info)
        # Place any cleanup tasks here
        pass

# This ensures that Main() is called when the script is executed directly.
if __name__ == "__main__":
    main()
