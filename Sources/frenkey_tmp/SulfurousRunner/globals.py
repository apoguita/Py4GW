from typing import Generator
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
from .waypoint import Waypoint3D, Waypoints


class Global:
    __instance = None
    __initalized = False
    
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Global, cls).__new__(cls)
        return cls.__instance
    
    def __init__(self):
        if self.__initalized:
            return
        
        self.__initalized = True
        
        self.paths: dict[int, list[Waypoint3D]] = {}
        self.closest_waypoint = 0
        
        self.current_path_generator : Generator | None = None        
        self.waypoints: Waypoints = Waypoints()
    