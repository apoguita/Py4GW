from Py4GWCoreLib import *

from ctypes import Structure, c_int, c_float, c_bool, c_char
from multiprocessing import shared_memory

MODULE_NAME = "GW NEXUS"

class SharedPlayerData(Structure):
    _pack_ = 1
    _fields_ = [
        ("agent_id", c_int),
        ("pos_x", c_float),
        ("pos_y", c_float),
        ("pos_z", c_float),
        ("rotation_angle", c_float),
        ("primary_profession", c_int),
        ("secondary_profession", c_int),
        ("level", c_int),
        ("health", c_float),
        ("energy", c_float),
        ("max_health", c_float),
        ("max_energy", c_float),   
    ]
    
    
    
def main():
    try:
        pass
    except Exception as e:
        ConsoleLog(MODULE_NAME, f"Error in main loop: {e}", Console.MessageType.Error)
        ConsoleLog(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Console.MessageType.Error)

if __name__ == "__main__":
    main()
