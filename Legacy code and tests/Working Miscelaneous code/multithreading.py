from Py4GWCoreLib import *

module_name = "Thread Manager"
manager = None

timer = Timer()
timer.Start()

def example_target():
    """Example function to run in a thread."""
    global timer
    if timer.HasElapsed(1000):
        Py4GW.Console.Log(module_name, "Example thread is running...", Py4GW.Console.MessageType.Info)
        timer.Reset()


def DrawWindow():
    global manager
    try:
        if PyImGui.begin(module_name):
            PyImGui.text("Thread Manager")
            PyImGui.separator()

            if PyImGui.button("Add and Start Example Thread"):
                if manager is None:
                    manager = MultiThreading()
                if "example_thread" not in manager.threads:
                    manager.add_thread("example_thread", example_target)
                manager.start_thread("example_thread")

            if PyImGui.button("Stop Example Thread"):
                if manager is not None and "example_thread" in manager.threads:
                    manager.stop_thread("example_thread")

            if PyImGui.button("Stop All Threads"):
                if manager is not None:
                    manager.stop_all_threads()

            PyImGui.end()
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in DrawWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

# main function must exist in every script and is the entry point for your script's execution.
def main():
    global module_name
    try:
        DrawWindow()

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

