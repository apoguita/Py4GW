from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"

#region globals
outpost_coordinate_list = [(8180, -27084), (4790, -27870)]
explorable_coordinate_list = [(2928,-24873), (2724,-22040), (-371,-20086), (-3294,-18164), (-5267,-14941), (-5297,-11045), (-1969,-12627), (1165,-14245), (4565,-15956)]

            
message = "Waiting..."
selected_channel = 0
is_script_running = False  # Controls counting

# Instantiate MultiThreading manager
thread_manager = MultiThreading()
action_queue = ActionQueueNode(100)
#endregion

def DrawWindow():
    """ImGui draw function that runs every frame."""
    global is_script_running
    try:
        flags = PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse | PyImGui.WindowFlags.AlwaysAutoResize
        if PyImGui.begin("Py4GW", flags):
            PyImGui.text("This is a boreal bot coded sequentially")
            
            button_text = "Start script" if not is_script_running else "Stop script"
            if PyImGui.button(button_text):
                is_script_running = not is_script_running 
             

        PyImGui.end()

    except Exception as e:
        print(f"Error in DrawWindow: {str(e)}")

#region HelperFunctions

def MapValidityCheck():
    if Map.IsMapLoading():
        return False
    if not Map.IsMapReady():
        return False
    if not Party.IsPartyLoaded():
        return False
    return True

def LoadSkillBar():
    global action_queue
    primary_profession, secondary_profession = Agent.GetProfessionNames(Player.GetAgentID())

    if primary_profession == "Warrior":
        action_queue.add_action(SkillBar.LoadSkillTemplate, "OQcAQ3lTQ0kAAAAAAAAAAA")
    elif primary_profession == "Ranger":
        action_queue.add_action(SkillBar.LoadSkillTemplate, "OgcAQ3lTQ0kAAAAAAAAAAA")
    elif primary_profession == "Monk":
        action_queue.add_action(SkillBar.LoadSkillTemplate, "OwcAQ3lTQ0kAAAAAAAAAAA")
    elif primary_profession == "Necromancer":
        action_queue.add_action(SkillBar.LoadSkillTemplate, "OAdAQ3lTQ0kAAAAAAAAAAA")
    elif primary_profession == "Mesmer":
        action_queue.add_action(SkillBar.LoadSkillTemplate, "OQdAQ3lTQ0kAAAAAAAAAAA")
    elif primary_profession == "Elementalist":
        action_queue.add_action(SkillBar.LoadSkillTemplate, "OgdAQ3lTQ0kAAAAAAAAAAA")
    elif primary_profession == "Assassin":
        action_queue.add_action(SkillBar.LoadSkillTemplate, "OwBAQ3lTQ0kAAAAAAAAAAA")
    elif primary_profession == "Ritualist":
        action_queue.add_action(SkillBar.LoadSkillTemplate, "OAeAQ3lTQ0kAAAAAAAAAAA")
    elif primary_profession == "Paragon":
        action_queue.add_action(SkillBar.LoadSkillTemplate, "OQeAQ3lTQ0kAAAAAAAAAAA")
    elif primary_profession == "Dervish":
        action_queue.add_action(SkillBar.LoadSkillTemplate, "OgeAQ3lTQ0kAAAAAAAAAAA")
        
def IsSkillBarLoaded():
    primary_profession, secondary_profession = Agent.GetProfessionNames(Player.GetAgentID())
    if primary_profession != "Assassin" and secondary_profession != "Assassin":
        frame = inspect.currentframe()
        current_function = frame.f_code.co_name if frame else "Unknown"
        Py4GW.Console.Log("Boreal Bot", f"{current_function} - This bot requires A/Any or Any/A to work, halting.", Py4GW.Console.MessageType.Error)
        return False
    return True

def follow_path(path_handler, movement_object, action_queue, custom_exit_condition=None):  
        movement_object.reset()
        if custom_exit_condition is None:
            custom_exit_condition = lambda: False
        while not (path_handler.is_finished() and movement_object.has_arrived()):
            if custom_exit_condition():
                break
            #this routine performs the follow, it uses the same movement objects as the asynch method
            movement_object.update(action_queue=action_queue)
            if movement_object.is_following():
                sleep(0.5)
                continue
                   
            point_to_follow = path_handler.advance()
            if point_to_follow is not None:
                movement_object.move_to_waypoint(point_to_follow[0], point_to_follow[1])
                sleep(0.5)
                
def IsChestFound(max_distance=2500) -> bool:
    return Routines.Targeting.GetNearestChest(max_distance) != 0
        


#endregion

#region Sequential Code

def SequentialCodeThread():
    """Thread function that manages counting based on ImGui button presses."""
    global MAIN_THREAD_NAME, is_script_running, action_queue

    while True:
        if thread_manager.should_stop(MAIN_THREAD_NAME):
            print("Thread detected inactivity, shutting down.")
            break  
        
        if not is_script_running:
            time.sleep(0.1)
            continue

        boreal_station = 675
        #correct map?
        if Map.GetMapID() != boreal_station:
            print ("Traveling to boreal station")
            action_queue.add_action(Map.Travel, boreal_station) #Map.Travel(boreal_station)
            sleep(1)
            waititng_for_map_load = True
            while waititng_for_map_load:
                if Map.IsMapReady() and Party.IsPartyLoaded() and Map.GetMapID() == boreal_station:
                    waititng_for_map_load = False
                    break
                sleep(1)
                
        print ("We are in boreal station, continue...")
        print ("Loading skillbar")
        LoadSkillBar()
        sleep(0.5)
        if not IsSkillBarLoaded():
            is_script_running = False
            continue
        print ("Skillbar loaded")
        if Inventory.GetFreeSlotCount() < 1 :
            print ("Inventory full")
            is_script_running = False
            continue
        
        if Inventory.GetModelCount(22751) < 1:
            print ("No more Lockpicks")
            is_script_running = False
            continue
            
        print ("all checks passed, starting routine")
        
        outpost_path = Routines.Movement.PathHandler(outpost_coordinate_list)
        explorable_path = Routines.Movement.PathHandler(explorable_coordinate_list)
        movement_object = Routines.Movement.FollowXY()
        
        print ("moving to explorable")
        
        follow_path(outpost_path, movement_object, action_queue)
        
        waititng_for_map_load = True
        while waititng_for_map_load:
            if Map.IsMapReady() and Party.IsPartyLoaded() and Map.GetMapID() == 499: #499 = Ice cliff chasms
                waititng_for_map_load = False
                break
            sleep(1)
        
        print ("We are in Ice cliff chasms, continue...")
        
        follow_path(explorable_path, movement_object, action_queue,custom_exit_condition=lambda: IsChestFound(max_distance=2500))

        if not IsChestFound(max_distance=2500):
            print ("No chest found") 
            #is_script_running = False
            continue #we restart the loop
        
        print ("Chest found")
        chest_id = Routines.Targeting.GetNearestChest(max_distance=2500)
        chest_x, chest_y = Agent.GetXY(chest_id)
        found_chest_coord_list = [(chest_x, chest_y)]
        chest_path = Routines.Movement.PathHandler(found_chest_coord_list)
        follow_path(chest_path, movement_object, action_queue)
        sleep(0.5)
        action_queue.add_action(Player.Interact, chest_id, False)
        
        sleep(1)
        action_queue.add_action(Player.SendDialog,2) #open chest
        sleep(1)
        nearest_item = Routines.Targeting.GetNearestItem(max_distance=300)
        action_queue.add_action(Player.Interact, nearest_item, False)
        sleep(1)
        
        #is_script_running = False #we stop the script
        #print ("Script finished")
        #break
            
#endregion   

#region globals_threading
MAIN_THREAD_NAME = "SequentialCodeThread"
thread_manager.add_thread(MAIN_THREAD_NAME, SequentialCodeThread)
thread_manager.start_thread(MAIN_THREAD_NAME)
#endregion

def main():
    global MAIN_THREAD_NAME, action_queue
    thread_manager.update_keepalive(MAIN_THREAD_NAME)
    
    DrawWindow()
    
    if action_queue.action_queue_timer.HasElapsed(action_queue.action_queue_time):
        action_queue.execute_next()


if __name__ == "__main__":
    main()
