from Py4GWCoreLib import *
import random

MODULE_NAME = "Chat Spam"

message_text = ""
channel = "$"

running = False
send_timer = Timer()
# Base delay in milliseconds before sending next message
base_delay = 10000
# Additional random delay in milliseconds added after each send
random_delay = 20000
next_delay = base_delay
send_timer.Start()


def send_chat_if_ready():
    global next_delay
    if running and send_timer.HasElapsed(next_delay):
        if Map.IsMapReady() and not Map.IsMapLoading():
            Player.SendChat(channel, message_text)
            next_delay = base_delay + random.randint(0, random_delay)
            send_timer.Reset()


def main():
    global running, message_text, channel
    try:
        if not Routines.Checks.Map.MapValid():
            send_timer.Reset()
            return 
        
        send_chat_if_ready()

        window_flags = PyImGui.WindowFlags.AlwaysAutoResize
        if PyImGui.begin("Chat Spam", window_flags):
            message_text = PyImGui.input_text("Message", message_text, 120)
            channel = PyImGui.input_text("Channel", channel)
            button_label = "Stop" if running else "Start"
            running = ImGui.toggle_button(button_label, running)
        PyImGui.end()
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


if __name__ == "__main__":
    main()