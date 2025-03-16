from Py4GWCoreLib import *
import time

MODULE_NAME = "tester for everything"

message = "Waiting..."
selected_channel = 0
is_script_running = False  # Controls counting
should_stop = False  # Signals the thread to reset


# Instantiate MultiThreading manager
thread_manager = MultiThreading()


def DrawWindow():
    """ImGui draw function that runs every frame."""
    global message, is_script_running, should_stop
    try:
        flags = PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse | PyImGui.WindowFlags.AlwaysAutoResize
        if PyImGui.begin("Py4GW", flags):
            PyImGui.text("Counter: " + message)  # Display counting message

            if not is_script_running:
                if PyImGui.button("Start"):
                    is_script_running = True
                    should_stop = False  # Allow counting to continue
            else:
                if PyImGui.button("Pause"):
                    is_script_running = False  # Pause the counting

                if PyImGui.button("Stop"):
                    is_script_running = False
                    should_stop = True  # Reset the counter to "Waiting"

        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log("tester", f"Unexpected Error: {str(e)}", Py4GW.Console.MessageType.Error)


def counting_thread():
    """Thread function that manages counting based on ImGui button presses."""
    global message, is_script_running, should_stop

    while True:
        if should_stop:
            message = "Waiting..."
            should_stop = False  # Reset stop flag

        if is_script_running:
            for i in range(1, 4):
                if not is_script_running or should_stop:
                    break  # Stop or pause counting immediately

                message = str(i)  # Update global message
                Py4GW.Console.Log("tester", f"Counter: {i}", Py4GW.Console.MessageType.Info)
                time.sleep(1)  # Sleep for 1000ms (1 second)

            if is_script_running:
                message = "Done!"  # Display "Done!" only if counting wasn't interrupted

        time.sleep(0.1)  # Prevent CPU overuse


# ✅ Start the thread ONCE when the script starts
thread_manager.add_thread("counter", counting_thread)
thread_manager.start_thread("counter")


def main():
    """Runs every frame."""
    DrawWindow()
    thread_manager.update_keepalive("counter")  # Keep thread alive


if __name__ == "__main__":
    main()
