from Py4GWCoreLib import *

from ctypes import Structure, c_int, c_float, c_bool, c_char
from multiprocessing import shared_memory

MODULE_NAME = "GLOBAL LOOT CONFIGURATION"

class LootConfigData(Structure):
    _pack_ = 1
    _fields_ = [
        ("loot_whites", c_bool),
        ("loot_blues", c_bool),
        ("loot_purples", c_bool),
        ("loot_golds", c_bool),
        ("loot_greens", c_bool),
        ("whitelist", c_int * 512),
        ("blacklist", c_int * 512),
    ]
    
    
    
def main():
    try:
        pass
    except Exception as e:
        ConsoleLog(MODULE_NAME, f"Error in main loop: {e}", Console.MessageType.Error)
        ConsoleLog(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Console.MessageType.Error)

if __name__ == "__main__":
    main()
