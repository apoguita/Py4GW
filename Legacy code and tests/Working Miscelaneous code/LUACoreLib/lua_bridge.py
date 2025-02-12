from Py4GWCoreLib import *
import pathlib
import sys
site_packages_path = r"C:\Users\Apo\AppData\Local\Programs\Python\Python313-32\Lib\site-packages"

if site_packages_path not in sys.path:
    sys.path.append(site_packages_path)
    
from lupa import LuaRuntime

class LuaBridge:
    def __init__(self, script_name='test_script.lua'):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.script_executed = None
        self.LUAcoreLib_dir = pathlib.Path(__file__).resolve().parent
        self.script_dir = pathlib.Path(__file__).resolve().parent.parent / "lua_scripts"
        self.script_name = script_name
        self._setup_lua_environment()
        
        

    def _setup_lua_environment(self):

        # Ensure LUAcoreLib_dir is correctly set
        lua_lib_dir = str(self.LUAcoreLib_dir).replace("\\", "/")

        # Construct new Lua paths
        lua_package_path = f"{lua_lib_dir}/?.lua;{lua_lib_dir}/?/init.lua;./?.lua;./?/init.lua"
        lua_package_cpath = f"{lua_lib_dir}/?.dll;./?.dll"

        # Modify package.path and package.cpath in Lua
        self.lua.globals()['Py4GW'] = Py4GW
        self.lua.execute(f"""
        package.path = "{lua_package_path}"; 
        package.cpath = "{lua_package_cpath}";

        -- Override print function to redirect output to Py4GW console
        function print(...)
            local args = {{...}}
            local output = ""
            for i, v in ipairs(args) do
                output = output .. tostring(v) .. " "
            end
            Py4GW.Console.Log("LuaBridge", output, Py4GW.Console.MessageType.Info)
        end

        print("[LUA Bridge] Updated package.path: " .. package.path)
        print("[LUA Bridge] Updated package.cpath: " .. package.cpath)
        """)
        
        self.lua.globals()['Agent'] = Agent
        self.lua.globals()['AgentArray'] = AgentArray
        self.lua.globals()['Effects'] = Effects
        self.lua.globals()['Enums'] = enums
        self.lua.globals()['PyImGui'] = PyImGui
        self.lua.globals()['ImGui'] = ImGui
        self.lua.globals()['Inventory'] = Inventory
        self.lua.globals()['Item'] = Item
        self.lua.globals()['ItemArray'] = ItemArray
        self.lua.globals()['Map'] = Map
        self.lua.globals()['Merchant'] = Merchant
        self.lua.globals()['Party'] = Party
        self.lua.globals()['Player'] = Player
        self.lua.globals()['Quest'] = Quest
        self.lua.globals()['Skill'] = Skill
        self.lua.globals()['Skillbar'] = Skillbar

        try:
            # Load Lua script
            #MapTester
            with open(self.script_dir / self.script_name, 'r') as f:
                self.script_executed = self.lua.execute(f.read())
        except FileNotFoundError as e:
            Py4GW.Console.Log("LUA Bridge", f"File Not Found: {e}", Py4GW.Console.MessageType.Error)
        except Exception as e:
            Py4GW.Console.Log("LUA Bridge", f"Unexpected error while loading Lua scripts: {e}", Py4GW.Console.MessageType.Error)

    def execute_lua_script(self):
        return self.script_executed