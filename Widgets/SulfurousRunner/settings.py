from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.IniHandler import IniHandler

class Settings:
    __instance = None
    __initalized = False
    
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Settings, cls).__new__(cls)
        return cls.__instance
    
    def __init__(self):
        if self.__initalized:
            return
        
        self.__initalized = True
        
        self.ini_handler : IniHandler = IniHandler("Widgets\\Config\\Sulfurous Runner.ini")
        self.draw_flags: bool = True
        self.draw_paths: bool = True
        
        self.use_flag_collision: bool = True
        self.use_path_collision: bool = True
        
        self.path_color: Color = Color(200, 200, 200, 100)
        self.flag_color: Color = Color(0, 204, 156, 100)
        self.load()
        
    
    def load(self):
        self.draw_flags = self.ini_handler.read_bool("Settings", "draw_flags", True)
        self.draw_paths = self.ini_handler.read_bool("Settings", "draw_paths", True)
        
        self.use_flag_collision = self.ini_handler.read_bool("Settings", "use_flag_collision", True)
        self.use_path_collision = self.ini_handler.read_bool("Settings", "use_path_collision", True)
        
        path_color = self.ini_handler.read_key("Settings", "path_color", str((200, 200, 200, 100)))
        path_color_tuple = tuple(int(c) for c in path_color.strip("()").split(","))
        self.path_color = Color(*path_color_tuple)
        
        flag_color = self.ini_handler.read_key("Settings", "flag_color", str((0, 204, 156, 100)))
        flag_color_tuple = tuple(int(c) for c in flag_color.strip("()").split(","))
        self.flag_color = Color(*flag_color_tuple)        
        
    def save(self):
        self.ini_handler.write_key("Settings", "draw_flags", str(self.draw_flags))
        self.ini_handler.write_key("Settings", "draw_paths", str(self.draw_paths))
        
        self.ini_handler.write_key("Settings", "use_flag_collision", str(self.use_flag_collision))
        self.ini_handler.write_key("Settings", "use_path_collision", str(self.use_path_collision))
        
        self.ini_handler.write_key("Settings", "path_color", str(self.path_color.rgb_tuple))
        self.ini_handler.write_key("Settings", "flag_color", str(self.flag_color.rgb_tuple))
        
    