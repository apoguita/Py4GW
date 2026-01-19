import os

from HeroAI.commands import HeroAICommands
from HeroAI.types import Docked
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.ImGui_src.types import Alignment
from Py4GWCoreLib.py4gwcorelib_src.Console import Console, ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.IniHandler import IniHandler

class Settings:
    class HeroPanelInfo:
        def __init__(self, x: int = 200, y: int = 200, collapsed: bool = False, visible: bool = True):
            self.x: int = x
            self.y: int = y
            self.collapsed: bool = collapsed
            self.open: bool = visible
            
    class CommandHotBar:
        def __init__(self, identifier: str = ""):
            self.identifier: str = identifier
            self.name: str = identifier
            self.commands: dict[int, dict[int, str]] = {0: {0: HeroAICommands().Empty.name}}
            self.position: tuple[int, int] = (0, 0)   
            self.visible: bool = True
            self.button_size: int = 32
            self.docked: Docked = Docked.Freely
            self.alignment: Alignment = Alignment.TopCenter
        
        def to_ini_string(self) -> str:
            #save the position, visible state and combine commands into string into a single row
            ini_string = ""
            ini_string += f"{self.name};"
            ini_string += f"{self.docked.name};"
            ini_string += f"{self.alignment.name};"
            ini_string += f"{self.visible};"
            ini_string += f"{self.button_size};"
            
            #combine commands into rows
            for row in sorted(self.commands.keys()):
                cmd_row = self.commands[row]
                row_str = "|".join(cmd_row.get(col, HeroAICommands().Empty.name) for col in sorted(cmd_row.keys()))
                ini_string += f"{row_str};"
            
            return ini_string
        
        def to_pos_string(self) -> str:
            #save the position, visible state and combine commands into string into a single row
            return f"{self.position[0]},{self.position[1]}"

        @staticmethod
        def from_ini_string(identifier: str, ini_string: str) -> 'Settings.CommandHotBar':
            hotbar = Settings.CommandHotBar()
            hotbar.identifier = identifier
            hotbar.commands = {}
            
            try:
                if ini_string.startswith("True") or ini_string.startswith("False"):
                    ini_string = f"Hotbar;{Docked.Freely.name};{Alignment.TopCenter.name};{ini_string}"
                    
                name, docked_str, aligned_str, visible_str, button_size_str, *command_rows_str = ini_string.split(";")     
                hotbar.name = name                           
                hotbar.docked = Docked[docked_str]
                hotbar.alignment = Alignment[aligned_str]
                hotbar.visible = visible_str.lower() == "true"
                hotbar.button_size = int(button_size_str)

                row = 0
                if command_rows_str:
                    for row_str in command_rows_str:
                        command_names = {col: cmd_name for col, cmd_name in enumerate(row_str.split("|"))}  

                        if any(name for name in command_names.values()):
                            hotbar.commands[row] = command_names
                            row += 1
                
                if len(hotbar.commands) == 0:
                    hotbar.commands = {0: {0: HeroAICommands().Empty.name}}
                else:
                    pass
                    
            except Exception as e:
                ConsoleLog("HeroAI", f"Error parsing CommandHotBar from ini string: {e}")
                
            return hotbar

    _instance = None
    _instance_initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._instance_initialized:
            return
        
        self._instance_initialized = True
        
        base_path = Console.get_projects_path()
        self.ini_path = os.path.join(base_path, "Widgets", "Config", "HeroAI.ini")
        
        self.save_requested = False        
        if not os.path.exists(self.ini_path):
            ConsoleLog("HeroAI", "HeroAI settings file not found. Creating default settings...")
            self.save_requested = True  
        
        self.account_ini_handler : IniHandler | None = None
        self.ini_handler = IniHandler(self.ini_path)
            
        self.Anonymous_PanelNames = False
        self.ShowCommandPanel = True
        self.ShowPartyOverlay = True
        self.ShowPartySearchOverlay = True
        self.ShowCommandPanelOnlyOnLeaderAccount = True
        
        self.ShowPanelOnlyOnLeaderAccount = True
        self.DisableAutomationOnLeaderAccount = False
        
        self.ShowDialogOverlay = True
        self.ShowControlPanelWindow = True
        
        self.CombinePanels = False
        self.ShowLeaderPanel = False
        self.ShowHeroPanels = True
        self.ShowHeroEffects = True
        self.ShowEffectDurations = False
        self.ShowShortEffectDurations = True
        self.ShowHeroUpkeeps = True
        self.MaxEffectRows = 2
        
        self.ShowHeroButtons = True
        self.ShowHeroBars = True
        self.ShowHeroSkills = True
        self.ShowFloatingTargets = True
        self.ShowPartyPanelUI = True
        self.HeroPanelPositions : dict[str, Settings.HeroPanelInfo] = {}
        
        default_hotbar = Settings.CommandHotBar("hotbar_1")
        
        commands = HeroAICommands()
        default_hotbar.commands = {
            0: {
                0: commands.Resign.name,
                1: commands.PixelStack.name,
                2: commands.TakeDialogWithTarget.name,
                3: commands.InteractWithTarget.name,
                4: commands.UnlockChest.name,
                5: commands.CombatPrep.name,
                6: commands.FlagHeroes.name,
                7: commands.UnflagHeroes.name,
            },
            1: {
                0: commands.FormParty.name,
                1: commands.DisbandParty.name,
                2: "Empty",
                3: commands.DonateFaction.name,
                4: commands.PickUpLoot.name,
                5: "Empty",
                6: "Empty",
                7: commands.OpenConsumables.name,
            }
        }
        
        self.CommandHotBars : dict[str, Settings.CommandHotBar] = {
            "hotbar_1": default_hotbar
        }
        
        self.ConfirmFollowPoint = False
        
                
        self.account_email = ""        
        self.account_ini_path = ""    
        self._initialized = False  

        if self.save_requested:
            self.write_settings()  

    def reset(self): 
        self.account_email = ""
        pass 
    
    def ensure_initialized(self) -> bool: 
        account_email = Player.GetAccountEmail()
        
        if not account_email:
            return True
         
        initialized = True if account_email and account_email == self.account_email else False
        
        if not initialized or not self._initialized:
            self.initialize_account_config()
        
        return self._initialized == initialized

    def initialize_account_config(self):
        base_path = Console.get_projects_path()        
        account_email = Player.GetAccountEmail()
        
        if account_email:
            config_dir = os.path.join(base_path, "Widgets", "Config", "Accounts", account_email)
            os.makedirs(config_dir, exist_ok=True)
            self.account_ini_path = os.path.join(config_dir, "HeroAI.ini")
            self.account_ini_handler = IniHandler(self.account_ini_path)            
            self.account_email = account_email
                    
        self._initialized = True if account_email and account_email == self.account_email else False
        
        if self._initialized and account_email and self.account_email == account_email:
            if not os.path.exists(self.account_ini_path):
                self.save_requested = True                
                self.write_settings()
            else:
                self.load_settings()
                
    def save_settings(self):
        self.save_requested = True
    
    def delete_hotbar(self, hotbar_id: str):
        if hotbar_id in self.CommandHotBars:
            del self.CommandHotBars[hotbar_id]
            
            if self.ini_handler is not None:
                self.ini_handler.delete_key("CommandHotBars", hotbar_id)
    
    def write_settings(self):               
        if not self.save_requested:
            return
        
        # ConsoleLog("HeroAI", "Saving HeroAI settings...")
        
        self.ini_handler.write_key("General", "ShowCommandPanel", str(self.ShowCommandPanel))
        self.ini_handler.write_key("General", "ShowCommandPanelOnlyOnLeaderAccount", str(self.ShowCommandPanelOnlyOnLeaderAccount))
        self.ini_handler.write_key("General", "Anonymous_PanelNames", str(self.Anonymous_PanelNames))
        
        self.ini_handler.write_key("General", "ShowPartyOverlay", str(self.ShowPartyOverlay))
        self.ini_handler.write_key("General", "ShowPartySearchOverlay", str(self.ShowPartySearchOverlay))
        
        self.ini_handler.write_key("General", "ShowPanelOnlyOnLeaderAccount", str(self.ShowPanelOnlyOnLeaderAccount))
        self.ini_handler.write_key("General", "DisableAutomationOnLeaderAccount", str(self.DisableAutomationOnLeaderAccount))
        self.ini_handler.write_key("General", "ShowDialogOverlay", str(self.ShowDialogOverlay))
        
        self.ini_handler.write_key("General", "CombinePanels", str(self.CombinePanels))
        self.ini_handler.write_key("General", "ShowHeroPanels", str(self.ShowHeroPanels))
        self.ini_handler.write_key("General", "ShowLeaderPanel", str(self.ShowLeaderPanel))        
        
        self.ini_handler.write_key("General", "ShowHeroEffects", str(self.ShowHeroEffects))
        self.ini_handler.write_key("General", "ShowEffectDurations", str(self.ShowEffectDurations))
        self.ini_handler.write_key("General", "ShowShortEffectDurations", str(self.ShowShortEffectDurations))
        self.ini_handler.write_key("General", "ShowHeroUpkeeps", str(self.ShowHeroUpkeeps))
        self.ini_handler.write_key("General", "MaxEffectRows", str(self.MaxEffectRows))
        
        self.ini_handler.write_key("General", "ShowHeroButtons", str(self.ShowHeroButtons))
        self.ini_handler.write_key("General", "ShowHeroBars", str(self.ShowHeroBars))
        self.ini_handler.write_key("General", "ShowFloatingTargets", str(self.ShowFloatingTargets))
        self.ini_handler.write_key("General", "ShowHeroSkills", str(self.ShowHeroSkills))
        
        self.ini_handler.write_key("General", "ShowPartyPanelUI", str(self.ShowPartyPanelUI))
        self.ini_handler.write_key("General", "ShowControlPanelWindow", str(self.ShowControlPanelWindow))

        self.ini_handler.write_key("General", "ConfirmFollowPoint", str(self.ConfirmFollowPoint))

        for hotbar_id, hotbar in self.CommandHotBars.items():
            self.ini_handler.write_key("CommandHotBars", hotbar_id, hotbar.to_ini_string())
            
        if self.account_ini_handler is not None:
            for hero_email, info in self.HeroPanelPositions.items():
                self.account_ini_handler.write_key("HeroPanelPositions", hero_email, f"{info.x},{info.y},{info.collapsed},{info.open}")
                            
            for hotbar_id, hotbar in self.CommandHotBars.items():
                self.account_ini_handler.write_key("CommandHotBars", hotbar_id, hotbar.to_pos_string())
            
        self.save_requested = False
        
    def load_settings(self):          
        ConsoleLog("HeroAI", "Loading HeroAI settings...")      
        self.ShowCommandPanel = self.ini_handler.read_bool("General", "ShowCommandPanel", True)
        self.ShowCommandPanelOnlyOnLeaderAccount = self.ini_handler.read_bool("General", "ShowCommandPanelOnlyOnLeaderAccount", True)
        self.Anonymous_PanelNames = self.ini_handler.read_bool("General", "Anonymous_PanelNames", False)
        
        self.ShowPartyOverlay = self.ini_handler.read_bool("General", "ShowPartyOverlay", True)
        self.ShowPartySearchOverlay = self.ini_handler.read_bool("General", "ShowPartySearchOverlay", True)
        
        self.ShowPanelOnlyOnLeaderAccount = self.ini_handler.read_bool("General", "ShowPanelOnlyOnLeaderAccount", True)
        self.DisableAutomationOnLeaderAccount = self.ini_handler.read_bool("General", "DisableAutomationOnLeaderAccount", False)
        self.ShowDialogOverlay = self.ini_handler.read_bool("General", "ShowDialogOverlay", True)
        
        self.CombinePanels = self.ini_handler.read_bool("General", "CombinePanels", False)
        self.ShowHeroPanels = self.ini_handler.read_bool("General", "ShowHeroPanels", True)
        self.ShowLeaderPanel = self.ini_handler.read_bool("General", "ShowLeaderPanel", False)
        
        self.ShowHeroEffects = self.ini_handler.read_bool("General", "ShowHeroEffects", True)
        self.ShowEffectDurations = self.ini_handler.read_bool("General", "ShowEffectDurations", True)
        self.ShowShortEffectDurations = self.ini_handler.read_bool("General", "ShowShortEffectDurations", True)
        self.ShowHeroUpkeeps = self.ini_handler.read_bool("General", "ShowHeroUpkeeps", True)
        self.MaxEffectRows = self.ini_handler.read_int("General", "MaxEffectRows", 2)
        
        self.ShowHeroButtons = self.ini_handler.read_bool("General", "ShowHeroButtons", True)
        self.ShowHeroBars = self.ini_handler.read_bool("General", "ShowHeroBars", True)
        self.ShowFloatingTargets = self.ini_handler.read_bool("General", "ShowFloatingTargets", True)
        self.ShowHeroSkills = self.ini_handler.read_bool("General", "ShowHeroSkills", True)
        
        self.ShowPartyPanelUI = self.ini_handler.read_bool("General", "ShowPartyPanelUI", True)
        self.ShowControlPanelWindow = self.ini_handler.read_bool("General", "ShowControlPanelWindow", True)
        
        self.ConfirmFollowPoint = self.ini_handler.read_bool("General", "ConfirmFollowPoint", False)

        self.CommandHotBars.clear()
        self.import_command_hotbars()
        
        self.HeroPanelPositions.clear()        
        self.import_hero_panel_positions(self.account_ini_handler)        
                    
    def import_hero_panel_positions(self, ini_handler: IniHandler | None):
        if ini_handler is None:
            return
        
        items = ini_handler.list_keys("HeroPanelPositions")
        request_save = False

        for key, value in items.items():
            try:
                parts = value.split(",")
                if len(parts) != 4:
                    ConsoleLog("HeroAI", f"Legacy HeroPanelPosition format detected for {key}, upgrading...")
                    x_str, y_str, collapsed_str, visible_str = parts[0] if len(parts) > 0 else "200", parts[1] if len(parts) > 1 else "200", "false", "true"
                else:
                    x_str, y_str, collapsed_str, visible_str = parts
                    
                x = int(x_str)
                y = int(y_str)
                collapsed = collapsed_str.lower() == "true"
                visible = visible_str and visible_str.lower() == "true" 
                request_save = key not in self.HeroPanelPositions or request_save
                self.HeroPanelPositions[key] = Settings.HeroPanelInfo(x, y, collapsed, visible)
                
            except Exception as e:
                ConsoleLog("HeroAI", f"Invalid format for Hero Panel of {key}. Using default.")
                self.HeroPanelPositions[key] = Settings.HeroPanelInfo()
        
        if request_save:
            self.save_requested = True
    
    def import_command_hotbars(self):        
        items = self.ini_handler.list_keys("CommandHotBars")        
        positions = self.account_ini_handler.list_keys("CommandHotBars") if self.account_ini_handler is not None else {}
        
        request_save = False

        for key, value in items.items():
            try:
                hotbar = Settings.CommandHotBar.from_ini_string(key, value)
                self.CommandHotBars[key] = hotbar
                
                if key in positions:
                    x_str, y_str = positions[key].split(",")
                    x = int(x_str)
                    y = int(y_str)
                    hotbar.position = (x, y)                
                
            except Exception as e:
                ConsoleLog("HeroAI", f"Error loading CommandHotBar for {key}: {e}")
        
        if request_save:
            self.save_requested = True  
