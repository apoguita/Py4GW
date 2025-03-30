from Py4GWCoreLib import *

MODULE_NAME = "Sequential Coding Template"


MAIN_THREAD_NAME = "RunBotSequentialLogic"
SKILL_HANDLING_THREAD_NAME = "SkillHandler"
thread_manager = MultiThreading(2.0, log_actions=True)
is_script_running = False

def StartSequentialEnviroment():
    global thread_manager, is_script_running
    is_script_running = True
    thread_manager.stop_all_threads()
    # Add sequential threads
    thread_manager.add_thread(MAIN_THREAD_NAME, RunBotSequentialLogic)
    thread_manager.add_thread(SKILL_HANDLING_THREAD_NAME, SkillHandler)
    # Watchdog thread is necessary to async close other running threads
    thread_manager.start_watchdog(MAIN_THREAD_NAME)
    
    
def StopSequentialEnviroment():
    global thread_manager, is_script_running
    thread_manager.stop_all_threads()
    is_script_running = False


def DrawWindow():
    global is_script_running
    if PyImGui.begin("Sequential Template"):
        PyImGui.text("This Script will set up the sequential envitoment and start the bot")
        button_text = "Start script" if not is_script_running else "Stop script"
        if PyImGui.button(button_text):
            if not is_script_running:
                # set up necessary threads
                print ("Starting sequential environment")
                StartSequentialEnviroment()
            else:
                # Stop all threads and clean environment
                StopSequentialEnviroment()

    PyImGui.end()   


def SkillHandler():
    """Thread function to handle skill casting based on conditions."""
    global is_script_running
    seconds_running = 0
    while is_script_running:
        print (f"Casting skills for {seconds_running} seconds")
        seconds_running += 1
        sleep(1)
    


def RunBotSequentialLogic():
    """Thread function that manages counting based on ImGui button presses."""
    global is_script_running
    seconds_running = 0
    while is_script_running:
        print (f"Running logic for {seconds_running} seconds")
        seconds_running += 1
        sleep(1)

            
            
#endregion   
def main():
    global is_script_running, thread_manager
    
    if is_script_running:
        thread_manager.update_all_keepalives()

    DrawWindow()


if __name__ == "__main__":
    main()
