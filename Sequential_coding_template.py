from Py4GWCoreLib import *
import time
from time import sleep

MODULE_NAME = "tester for everything"

message = "Waiting..."
selected_channel = 0
is_script_running = False  # Controls counting

# Instantiate MultiThreading manager
thread_manager = MultiThreading()

def DrawWindow():
    """ImGui draw function that runs every frame."""
    global is_script_running
    try:
        flags = PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse | PyImGui.WindowFlags.AlwaysAutoResize
        if PyImGui.begin("Py4GW", flags):
            PyImGui.text("This is a template for sequential coding.")
            
            button_text = "Start script" if not is_script_running else "Stop script"
            if PyImGui.button(button_text):
                is_script_running = not is_script_running                

        PyImGui.end()

    except Exception as e:
        print(f"Error in DrawWindow: {str(e)}")


def SequentialCodeThread():
    """Thread function that manages counting based on ImGui button presses."""
    global MAIN_THREAD_NAME, is_script_running

    seconds_running = 0
    while True:
        if thread_manager.should_stop(MAIN_THREAD_NAME):
            print("Thread detected inactivity, shutting down.")
            break  

        #your sequential block of code starts here
        if is_script_running:
            print(f"Script is running for {seconds_running} seconds.")
            seconds_running += 1
            sleep(1)

        time.sleep(0.1)

MAIN_THREAD_NAME = "SequentialCodeThread"
thread_manager.add_thread(MAIN_THREAD_NAME, SequentialCodeThread)
thread_manager.start_thread(MAIN_THREAD_NAME)


def main():
    global MAIN_THREAD_NAME
    thread_manager.update_keepalive(MAIN_THREAD_NAME)

    DrawWindow()
    


if __name__ == "__main__":
    main()
