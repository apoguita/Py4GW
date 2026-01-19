import PyImGui

from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib import ChatChannel, UIManager
from Py4GWCoreLib.native_src.methods.PlayerMethods import PlayerMethods


input_string = ""

def draw_window():
    global input_string
    if PyImGui.begin("player test"): 
        PyImGui.text(f"Active Title ID: {Player.GetActiveTitleID()}")
        instance_time = Agent.GetInstanceFrames(Player.GetAgentID())
        PyImGui.text(f"Instance Time: {instance_time} frames")
        fps_limit = UIManager.GetFPSLimit() 
        fps_limit = max(fps_limit, 30)  # Prevent division by zero
        PyImGui.text(f"FPS Limit: {fps_limit}")
        instance_time_ms = instance_time / fps_limit * 1000
        PyImGui.text(f"Instance Time: {instance_time_ms:.2f} ms")
        
        if PyImGui.button("send chat"):
            Player.SendChat("#", "Hello from Py4GW!")
            
        if PyImGui.button("send chat trough method"):
            PlayerMethods.SendChat('#', "Hello from Py4GW Method!")
         
        input_string = PyImGui.input_text("whisper character name", input_string)    
        
        if PyImGui.button("send whisper"):
            Player.SendWhisper(input_string, "Hello from Py4GW whisper!")
            
        if PyImGui.button("send whisper trough method"):
            PlayerMethods.SendWhisper(input_string, "Hello from Py4GW Method whisper!")
            
        if PyImGui.button("send chat command"):
            Player.SendChatCommand("dance")
            
        if PyImGui.button("send chat command trough method"):
            PlayerMethods.SendChatCommand("dance")
            
        if PyImGui.button("send fake chat"):
            Player.SendFakeChat(ChatChannel.CHANNEL_EMOTE, "Hello from Py4GW fake chat!")
            
        if PyImGui.button("send fake chat trough method"):
            PlayerMethods.SendFakeChat(ChatChannel.CHANNEL_EMOTE.value, "Hello from Py4GW Method fake chat!")


    PyImGui.end()

def main():
    draw_window()

if __name__ == "__main__":
    main()
