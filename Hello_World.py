import PyImGui

from Py4GWCoreLib.native_src.context.GuildContext import GuildContext, GHKey
from Py4GWCoreLib.native_src.methods.MapMethods import MapMethods

input_string = ""

def draw_window():
    global input_string
    if PyImGui.begin("HeroAI test"):
        if PyImGui.button("Print Guild Hall Key"):
            guild_ctx = GuildContext.get_context()
            if guild_ctx is None:
                return False
            key = guild_ctx.player_gh_key
            
            print(f"Guild Hall Key: {key.as_string}")
            
        input_string = PyImGui.input_text("Input String", input_string)
        if PyImGui.button("Travel To GH"):
            key = GHKey.from_hex(input_string)
            print (f"Traveling to Guild Hall with Key: {key.as_string}")
            MapMethods.TravelGH(key)
            
        if PyImGui.button("plain Travel To GH"):
            MapMethods.TravelGH()
            
            
            
    PyImGui.end()

def main():
    draw_window()

if __name__ == "__main__":
    main()
