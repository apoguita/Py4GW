
from Py4GWCoreLib import *
from LUACoreLib.lua_bridge import LuaBridge

lua_bridge = LuaBridge('hello_world.lua')
lua_script = lua_bridge.execute_lua_script()

def main():
    global lua_script
    try:
        if lua_script:
            lua_script.render()
        else:
            raise Exception("Script render failed: No instance available.")
        
    except Exception as e:
        Py4GW.Console.Log("LUA Engine", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

if __name__ == "__main__":
    main()
