from Py4GWCoreLib import *
import pathlib
import sys
site_packages_path = r"C:\Users\Apo\AppData\Local\Programs\Python\Python313-32\Lib\site-packages"

if site_packages_path not in sys.path:
    sys.path.append(site_packages_path)
    
from lupa import LuaRuntime

class LuaBridge:
    def __init__(self, script_name='map_id_tester.lua'):
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
        
        #self.lua.globals()['PyItem'] = PyItem
        #self.lua.globals()['PyInventory'] = PyInventory
        #self.lua.globals()['PyAgent'] = PyAgent
        #self.lua.globals()['PyPlayer'] = PyPlayer
        #self.lua.globals()['PyEffects'] = PyEffects
        #self.lua.globals()['PyItemArray'] = ItemArray
        #self.lua.globals()['PyMap'] = PyMap
        #with open(self.LUAcoreLib_dir / 'Map.lua', 'r') as f:
        #        self.map = self.lua.execute(f.read())
                
        #self.lua.globals()['PyMerchant'] = PyMerchant
        #self.lua.globals()['PyParty'] = PyParty
        #self.lua.globals()['PyQuest'] = PyQuest
        #self.lua.globals()['PySkill'] = PySkill
        #self.lua.globals()['PySkillbar'] = PySkillbar
        self.lua.globals()['PyImGui'] = PyImGui
        """
        with open(self.LUAcoreLib_dir / 'ImGui.lua', 'r') as f:
            lua_code = f.read()
            print("[Python] Loading ImGui.lua...")
            self.imgui = self.lua.execute(lua_code)
            print(f"[Python] Loaded ImGui.lua: {self.imgui}")
        """          
        #self.lua.globals()['map'] = self.get_map()  # Make map available to Lua
    
        try:
            # Load Lua scripts
            """
            with open(self.LUAcoreLib_dir / 'Item.lua', 'r') as f:
                self.item = self.lua.execute(f.read())
                
            with open(self.LUAcoreLib_dir / 'AgentArray.lua', 'r') as f:
                self.agent_array = self.lua.execute(f.read())
                
            with open(self.LUAcoreLib_dir / 'Agent.lua', 'r') as f:
                self.agent = self.lua.execute(f.read())
                
            with open(self.LUAcoreLib_dir / 'Effects.lua', 'r') as f:
                self.effects = self.lua.execute(f.read())
                
            with open(self.LUAcoreLib_dir / 'Inventory.lua', 'r') as f:
                self.inventory = self.lua.execute(f.read())
                
            with open(self.LUAcoreLib_dir / 'ItemArray.lua', 'r') as f:
                self.item_array = self.lua.execute(f.read())
            """  
            
            
            """  
            with open(self.LUAcoreLib_dir / 'Merchant.lua', 'r') as f:
                self.merchant = self.lua.execute(f.read())
                
            with open(self.LUAcoreLib_dir / 'Party.lua', 'r') as f:
                self.party = self.lua.execute(f.read())
                
            with open(self.LUAcoreLib_dir / 'Quest.lua', 'r') as f:
                self.quest = self.lua.execute(f.read())
                
            with open(self.LUAcoreLib_dir / 'Skill.lua', 'r') as f:
                self.skill = self.lua.execute(f.read())
                
            with open(self.LUAcoreLib_dir / 'Skillbar.lua', 'r') as f:
                self.skillbar = self.lua.execute(f.read())
            """
                       
            #MapTester
            with open(self.script_dir / self.script_name, 'r') as f:
                self.script_executed = self.lua.execute(f.read())
        except FileNotFoundError as e:
            Py4GW.Console.Log("LUA Bridge", f"File Not Found: {e}", Py4GW.Console.MessageType.Error)
        except Exception as e:
            Py4GW.Console.Log("LUA Bridge", f"Unexpected error while loading Lua scripts: {e}", Py4GW.Console.MessageType.Error)



    def get_item(self):
        return self.item

    def get_agent_array(self):
        return self.agent_array

    def get_agent(self):
        return self.agent

    def get_effects(self):
        return self.effects

    def get_inventory(self):
        return self.inventory

    def get_item_array(self):
        return self.item_array

    def get_map(self):
        return self.map

    def get_merchant(self):
        return self.merchant

    def get_party(self):
        return self.party

    def get_quest(self):
        return self.quest

    def get_skill(self):
        return self.skill

    def get_skillbar(self):
        return self.skillbar

    def execute_lua_script(self):
        return self.script_executed