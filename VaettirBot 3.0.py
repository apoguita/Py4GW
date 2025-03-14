from Py4GWCoreLib import *
import time
from time import sleep

MODULE_NAME = "VaettirBot 3.0"


#region globals
class BOTVARIABLES:
    def __init__(self):
        self.is_script_running = False
        self.log_to_console = True # Controls whether to print to console
        self.action_queue = ActionQueueNode(100)
        self.merchant_queue = ActionQueueNode(350)
        
bot_variables = BOTVARIABLES()

# Instantiate MultiThreading manager
thread_manager = MultiThreading()

def DrawWindow():
    """ImGui draw function that runs every frame."""
    global bot_variables
    
    flags = PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse | PyImGui.WindowFlags.AlwaysAutoResize
    if PyImGui.begin("Py4GW", flags):
        PyImGui.text("This is a template for sequential coding.")
        
        button_text = "Start script" if not bot_variables.is_script_running else "Stop script"
        if PyImGui.button(button_text):
            bot_variables.is_script_running = not bot_variables.is_script_running                

    PyImGui.end()

    

#region Sequential coding
def SequentialCodeThread():
    """Thread function that manages counting based on ImGui button presses."""
    global MAIN_THREAD_NAME, bot_variables

    while True:
        if thread_manager.should_stop(MAIN_THREAD_NAME):
            ConsoleLog(MODULE_NAME,"thread stopping.",log= bot_variables.log_to_console)
            break  

        if not bot_variables.is_script_running:
            sleep(1)
            continue
        
        #Your code goes here
        longeyes_ledge = 650 #Longeyes Ledge
        Routines.Sequential.Map.TravelToOutpost(longeyes_ledge, bot_variables.action_queue, bot_variables.log_to_console)
        
        
        

        time.sleep(0.1)
#endregion

#region Watchdog
def watchdog_fn():
    """Daemon thread that monitors all active threads and shuts down unresponsive ones."""
    global MAIN_THREAD_NAME

    while True:
        active_threads = list(thread_manager.threads.keys())

        #Check for timeouts and stop unresponsive threads
        for name in active_threads:
            if name != "watchdog" and thread_manager.should_stop(name):  # Don't stop itself
                ConsoleLog(f"Watchdog",f"Thread: {name}' timed out. Stopping it.",Console.MessageType.Notice,log=True)
                thread_manager.stop_thread(name)

        #If the main thread itself has timed out, shut everything down
        if MAIN_THREAD_NAME not in thread_manager.threads or thread_manager.should_stop(MAIN_THREAD_NAME):
            
            print("[Watchdog] Main thread has timed out. Stopping all threads.")
            thread_manager.stop_all_threads()
            break  # Watchdog exits naturally, no `join()` needed

        time.sleep(1)  #Adjust checking interval as needed


#endregion

MAIN_THREAD_NAME = "SequentialCodeThread"
thread_manager.add_thread(MAIN_THREAD_NAME, SequentialCodeThread)
thread_manager.start_thread(MAIN_THREAD_NAME)

thread_manager.add_thread("watchdog", watchdog_fn)
thread_manager.start_thread("watchdog")


def main():
    global MAIN_THREAD_NAME
    try:
        thread_manager.update_keepalive(MAIN_THREAD_NAME)

        DrawWindow()
        
        if bot_variables.action_queue.action_queue_timer.HasElapsed(bot_variables.action_queue.action_queue_time):
            bot_variables.action_queue.execute_next()
            
    except Exception as e:
        ConsoleLog(MODULE_NAME,f"Error: {str(e)}",Py4GW.Console.MessageType.Error,log=True)

if __name__ == "__main__":
    main()