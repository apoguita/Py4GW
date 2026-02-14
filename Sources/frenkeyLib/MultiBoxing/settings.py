import ctypes
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.GlobalCache.SharedMemory import AccountStruct
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.py4gwcorelib_src.Console import Console, ConsoleLog
from Sources.frenkeyLib.MultiBoxing.enum import RenameClientType
from Sources.frenkeyLib.MultiBoxing.messaging import position_clients
from Sources.frenkeyLib.MultiBoxing.region import Region

MODULE_NAME = __file__.split("\\")[-2]

class Settings:
    _instance = None
    _initialized = False
        
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Settings, cls).__new__(cls)
        return cls._instance
    
    def __init__(self): 
        # guard: only initialize once
        if self.__class__._initialized:
            return
        
        self.__class__._initialized = True
               
        screen_size = self.get_screen_size()
        
        self.sub_regions : list[Region] = []  # Placeholder for sub-regions
        
        self.regions : list[Region] = []
        self.active_region : Region | None = None
        self.move_slave_to_main : bool = True
        self.move_on_focus : bool = False
        
        self.show_overview : bool = True
        
        self.screen_size : tuple[int, int] = screen_size
        self.screen_size_changed : bool = False
        
        self.custom_names : dict[str, str] = {}  # account email -> custom name
        self.rename_to : RenameClientType = RenameClientType.Character
        self.append_gw : bool = True
        
        self.hide_widgets_on_slave : bool = True
        
        self.snap_to_edges : bool = True
        self.edge_snap_distance : int = 15
        
        self.columns : int = 1
        self.rows : int = 1
        self.layout_import_rows : str = "1 1 1"
        self.layout_import_columns : str = "1 1 1"
        
        self.layout : str = "None"  # Current layout name
        self.layouts : list[str] = ["None"]  # List of layout names
        
        self.account : str = ""
        self.accounts : list[AccountStruct] = []  # List of account objects
        self.accounts_order : list[str] = []  # List of (account index, account email) tuples
        

    @property
    def main_region(self) -> Region | None:
        main = next((r for r in self.regions if r.main), None) if self.regions else None
        
        return main
    
    def set_accounts(self, accounts: list[AccountStruct]):
        self.accounts = accounts
        
        for acc in accounts:
            if not acc.AccountEmail:
                continue
            
            if acc.AccountEmail not in self.accounts_order:
                self.accounts_order.append(acc.AccountEmail)
                    
    def move_account(self, from_index: int, to_index: int):
        if from_index < 0 or from_index >= len(self.accounts_order):
            return
        if to_index < 0 or to_index >= len(self.accounts_order):
            return

        # Move the account
        account = self.accounts_order.pop(from_index)
        self.accounts_order.insert(to_index, account)

        # Save new order
        self.save_settings()

    def get_account_mail(self) -> str:
        from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE

        if not self.account:
            self.account = Player.GetAccountEmail()
            
        return self.account

    def get_screen_size(self) -> tuple[int, int]:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        return screen_width, screen_height
    
    def add_region(self, region: Region):
        self.regions.append(region)
    
    def remove_region(self, region: Region):
        if region in self.regions:
            self.regions.remove(region)
            
    def clear_regions(self):
        self.regions.clear()
        
    def save_settings(self):
        folder_path = Console.get_projects_path() + "\\Widgets\\Config\\MultiBoxing"
        try:
            import os
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                
            import json
            settings_data = {
                "rename_to": self.rename_to.name,
                "append_gw": self.append_gw,
                "hide_widgets_on_slave": self.hide_widgets_on_slave,
                "snap_to_edges": self.snap_to_edges,
                "edge_snap_distance": self.edge_snap_distance,
                "layout": self.layout,
                "accounts_order": self.accounts_order,
                "show_overview": self.show_overview
            }
            
            with open(f"{folder_path}\\settings.json", "w") as f:
                json.dump(settings_data, f, indent=4)
                
            ConsoleLog(MODULE_NAME, f"Settings saved to {folder_path}\\settings.json")
            
        except Exception as e:
            ConsoleLog(MODULE_NAME, f"Error saving settings: {e}", Console.MessageType.Error)
        
    def load_settings(self):
        folder_path = Console.get_projects_path() + "\\Widgets\\Config\\MultiBoxing"
        try:
            import os
            file_path = f"{folder_path}\\settings.json"
            if not os.path.exists(file_path):
                ConsoleLog(MODULE_NAME, f"Settings file does not exist at {file_path}, using defaults.", Console.MessageType.Warning)
                return
            
            import json
            with open(file_path, "r") as f:
                settings_data = json.load(f)
                
                rename_to_str = settings_data.get("rename_to", "Character")
                self.rename_to = RenameClientType[rename_to_str] if rename_to_str in RenameClientType.__members__ else RenameClientType.Character
                self.append_gw = settings_data.get("append_gw", True)
                self.hide_widgets_on_slave = settings_data.get("hide_widgets_on_slave", True)
                self.snap_to_edges = settings_data.get("snap_to_edges", True)
                self.edge_snap_distance = settings_data.get("edge_snap_distance", 15)
                self.layout = settings_data.get("layout", "None")      
                self.accounts_order = settings_data.get("accounts_order", [])      
                self.show_overview = settings_data.get("show_overview", True)
            ConsoleLog(MODULE_NAME, f"Settings loaded from {file_path}")
                
        except Exception as e:
            ConsoleLog(MODULE_NAME, f"Error loading settings: {e}", Console.MessageType.Error)

    def save_layout(self, name: str):
        if not name:
            ConsoleLog(MODULE_NAME, "Layout name is empty, cannot save layout.", Console.MessageType.Warning)
            return
        
        try:
            import os
            folder_path = Console.get_projects_path() + "\\Widgets\\Config\\MultiBoxing\\Layouts"

            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            json_data = {
                "regions": [region.to_dict() for region in self.regions]
            }
            
            with open(f"{folder_path}\\{name}.json", "w") as f:
                import json
                json.dump(json_data, f, indent=4)
                
            ConsoleLog(MODULE_NAME, f"Layout '{name}' saved successfully.")
            
            if not name in self.layouts:
                self.layouts.append(name)  # Add to layouts list if not already present
                
        except Exception as e:
            ConsoleLog(MODULE_NAME, f"Error saving layout '{name}': {e}", Console.MessageType.Error)
    
    def load_layout(self, name: str):
        if not name or name == "None":
            ConsoleLog(MODULE_NAME, "Layout name is empty or 'None', cannot load layout.", Console.MessageType.Warning)
            return
        
        try:
            import os
            folder_path = Console.get_projects_path() + "\\Widgets\\Config\\MultiBoxing\\Layouts"
            file_path = f"{folder_path}\\{name}.json"

            if not os.path.exists(file_path):
                ConsoleLog(MODULE_NAME, f"Layout file '{file_path}' does not exist.", Console.MessageType.Warning)
                return

            with open(file_path, "r") as f:
                import json
                data = json.load(f)
                
                self.clear_regions()
                
                for i, region_data in enumerate(data.get("regions", [])):
                    region = Region.from_dict(region_data, number=i+1)
                    self.add_region(region)                
                
                if name != self.layout:                      
                    self.layout = name
                    self.save_settings()
                    
                ConsoleLog(MODULE_NAME, f"Layout '{name}' loaded successfully with {len(self.regions)} regions.")
                position_clients(self.get_account_mail(), self.regions, self.accounts)      
                
        except Exception as e:
            ConsoleLog(MODULE_NAME, f"Error loading layout '{name}': {e}", Console.MessageType.Error)
        
    def load_layouts(self):
        
        import os
        folder_path = Console.get_projects_path() + "\\Widgets\\Config\\MultiBoxing\\Layouts"
        self.layouts = ["None"]  # Reset to default
        
        if not os.path.exists(folder_path):
            return

        for file in os.listdir(folder_path):
            if file.endswith(".json"):
                self.layouts.append(file[:-5])  # Remove .json extension
                ConsoleLog(MODULE_NAME, f"Adding layout: '{file[:-5]}'")        