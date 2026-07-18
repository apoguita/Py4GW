import Py4GW
from Py4GWCoreLib import *
import heapq

MODULE_NAME = "chat spammer"

dialog = 0x8E

throttle_time = 90000  # 90 seconds in milliseconds

chat_timer = ThrottledTimer(throttle_time)
spam_chat = False
message = "WTB Lockpicks 80=100k x10"

def main():
    global dialog, chat_timer, spam_chat, message, throttle_time
    try:

        if PyImGui.begin("Dialog Sender", PyImGui.WindowFlags.AlwaysAutoResize): 
            
            message = PyImGui.input_text("Message", message)
            prev_throttle_time = throttle_time
            throttle_time = PyImGui.input_int("Throttle time (ms)", throttle_time)
            if throttle_time != prev_throttle_time:
                chat_timer.SetThrottleTime(throttle_time)

            spam_chat = ImGui.toggle_button("Spam chat", spam_chat)
            
            elapsed_time = FormatTime(chat_timer.GetTimeElapsed(),"mm::ss::ms")
            PyImGui.text(f"Chat timer: {elapsed_time}")
            
            
            
            if spam_chat and chat_timer.IsExpired():
                chat_timer.Reset()
                Player.SendChat('$', message)
        PyImGui.end()


    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


    
if __name__ == "__main__":
    main()