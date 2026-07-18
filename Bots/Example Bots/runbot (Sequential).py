from Py4GWCoreLib import *

MODULE_NAME = "Run to Sardelac Test"

exit_ascalon_path = [(6534.0, 4650.0), (6331, 4394), (5967, 3935), (5591, 3496), (5201, 3067),
    (4813, 2639), (4425, 2212), (3960, 1876), (3417, 1702), (2841, 1654),
    (2266, 1664), (1694, 1731), (1118, 1799), (544, 1850),  (-30, 1844),
    (-230, 1841), (-510,1850),
]

ascalon_to_sardelac_path =  [(17503.0, 11084.0), (16571, 10333), (16068, 9352), (14647, 9480), (13504, 8631),
    (12483, 7617), (11527, 6540), (10393, 5311), (9576, 4320), (8376, 2990), (6943, 1816),
    (5459, 690), (3822, -146), (1770, -682), (51, -495), (-2008, 138), (-3709, 290), (-4835, -53),
    (-4747, -65)
]

#this is the name of the thread, it needs to be tha same name as the procedure that we are going to run 
# on the thread
GOT_TO_SARDEAC_THREAD = "got_to_sardelac"
#this is the name of the thread that will handle the skills, it needs to be tha same name as the procedure 
# that we are going to run on the thread
SKILL_HANDLING_THREAD_NAME = "Process_Skills"
#this is the name of the object that handles threads
thread_manager = MultiThreading(2.0, log_actions=True)
is_script_running = False

def Start_Go_To_Sardelac_and_process_skills_Thread():
    global thread_manager, is_script_running
    is_script_running = True
    thread_manager.stop_all_threads()
    # Add sequential threads
    thread_manager.add_thread(GOT_TO_SARDEAC_THREAD, got_to_sardelac)
    thread_manager.add_thread(SKILL_HANDLING_THREAD_NAME, Process_Skills)
    # Watchdog thread is necessary to async close other running threads
    #the watchdog is an independent thread that will watch over the other threads, 
    # so if they crash or stop, it will stop and clean them
    thread_manager.start_watchdog(GOT_TO_SARDEAC_THREAD)
    
    
def StopAllThreads():
    global thread_manager, is_script_running
    thread_manager.stop_all_threads()
    is_script_running = False


def DrawWindow():
    global is_script_running
    if PyImGui.begin("Sequential Template"):
        PyImGui.text("this script is aimed to be a tutorial with")
        PyImGui.text("indepth commentary, not a full script.")
        PyImGui.text("see the code for more details")
        button_text = "Start script" if not is_script_running else "Stop script"
        if PyImGui.button(button_text):
            if not is_script_running:
                """first we need to start the environment, this will stop all threads and start new ones
                    threads are detached processes that can run separate from the main script, this is useful for
                    running multiple tasks at once, like moving and casting skills at the same time
                    
                    after we start the threads, all code will be deferred to the thread.   
                """
                Start_Go_To_Sardelac_and_process_skills_Thread()
            else:
                pass
                # Stop all threads and clean environment
                StopAllThreads()

    PyImGui.end()   

def travel_to_ascalon_city():
    ascalon_city_map_id = 81
    Routines.Sequential.Map.TravelToOutpost(ascalon_city_map_id, log=True)

def equip_skillbar():
    primary_profession, _ = Agent.GetProfessionNames(Player.GetAgentID())

    skill_templates = {
        "Warrior":      "OQcAQ3lTQ0kAAAAAAAAAAA",
        "Ranger":       "OgcAQ3lTQ0kAAAAAAAAAAA",
        "Monk":         "OwcAQ3lTQ0kAAAAAAAAAAA",
        "Necromancer":  "OAdAQ3lTQ0kAAAAAAAAAAA",
        "Mesmer":       "OQdAQ3lTQ0kAAAAAAAAAAA",
        "Elementalist": "OgdAQ3lTQ0kAAAAAAAAAAA",
        "Assassin":     "OwBAQ3lTQ0kAAAAAAAAAAA",
        "Ritualist":    "OAeAQ3lTQ0kAAAAAAAAAAA",
        "Paragon":      "OQeAQ3lTQ0kAAAAAAAAAAA",
        "Dervish":      "OgeAQ3lTQ0kAAAAAAAAAAA"
    }

    template = skill_templates.get(primary_profession)
    if template:
        ActionQueueManager().AddAction("ACTION",SkillBar.LoadSkillTemplate, template)

    sleep(0.5)

def exit_ascalon_city():
    old_ascalon_map_id = 33
    Routines.Sequential.Movement.FollowPath(exit_ascalon_path, custom_exit_condition=lambda: Map.IsMapLoading())
    Routines.Sequential.Map.WaitforMapLoad(old_ascalon_map_id)   

def follow_path_to_sardelac():
    sardelac_sanitarium_map_id = 39
    Routines.Sequential.Movement.FollowPath(ascalon_to_sardelac_path, custom_exit_condition=lambda: Map.IsMapLoading())
    Routines.Sequential.Map.WaitforMapLoad(sardelac_sanitarium_map_id)
    
def Process_Skills():
    while True:
        #this is where we process all skills and skill behavior, 
        # this is a separate thread that will run in parallel to the main thread
        #we are on an infinite loop, so we need to sleep for a bit to avoid overloading the CPU
        sleep(0.1)
        #our skillbar uses 
        #1.- Skill 1: "Dwarven Stability"
        dwarven_stability = Skill.GetID("Dwarven_Stability")
        #2.- Skill 2: "Dash"
        dash = Skill.GetID("Dash")
        
        #we need to do necessary checks to see if we can use skills
        if not Routines.Checks.Map.MapValid():
            #if the status of the map is not a valis one, we should not use skills
            #we exit the loop and wait for the next iteration
            sleep(0.1)
            continue
        
        if not Map.IsExplorable():
            #if the map is not explorable, we should not use skills
            #we exit the loop and wait for the next iteration
            sleep(0.1)
            continue
        
        #we are on an appropriate map, we can use skills
        #sre we able to cast right now?
        if not Routines.Checks.Skills.CanCast():
            #if we are not able to cast, we should not use skills
            #we exit the loop and wait for the next iteration
            sleep(0.1)
            continue
        
        #dwarven stability, has a duration of 30 seconds and has a cooldown of 30 seconds
        #therefore it will never overlap, so we can use it whenever its available
        #since we know that if its available we dont have the buff
        if Routines.Sequential.Skills.CastSkillID(dwarven_stability,log=True):
            #if we casted the skill, we should wait for the cast and aftercast to finish
            sleep(0.5)
        
        #dash, will nevver overlap, so we can use it whenever its available
        if Routines.Sequential.Skills.CastSkillID(dash, log=True):
            sleep(0.05)
        
        
        
            
def got_to_sardelac():
    #The Thread will start executing here, all code after this point will be run sequentially
    #since its a separate process, you can sleep() or do whatever you want witout blocking the main thread
    
    #1.- We need to Tavel to Ascalon City
    travel_to_ascalon_city()
    #2.- We need to equip the skillbar
    equip_skillbar()
    #3.- We need to exit Ascalon City
    exit_ascalon_city()
    #4.- We need to follow the path to Sardelac
    follow_path_to_sardelac()
    #we arrived to sardelac, theres nothing else to do, we can finish the thread
    #no more code = finish thread


#endregion   
def main():
    global is_script_running, thread_manager
    
    if is_script_running:
        thread_manager.update_all_keepalives()

    DrawWindow()

    if is_script_running:
        if not Agent.IsCasting(Player.GetAgentID()) and not Agent.IsKnockedDown(Player.GetAgentID()):
            ActionQueueManager().ProcessQueue("ACTION")
        else:
            ActionQueueManager().ResetAllQueues()

if __name__ == "__main__":
    main()
