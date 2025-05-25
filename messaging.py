from Py4GWCoreLib import *
from ctypes import Structure, c_int, c_float, c_bool, c_char, c_wchar, c_ubyte, c_uint, c_ushort
MODULE_NAME = "tester for everything"

MAX_NUMBER_OF_BUFFS = 240

class AccountData(Structure):
    _fields_ = [
        ("AccountEmail", c_wchar*64),
        ("AcocuntName", c_wchar*20),
        ("CharacterName", c_wchar*20),
        ("MapID", c_int),
        ("MapRegion", c_int),
        ("MapDistrict", c_int),
        ("PlayerID", c_int),
        ("PlayerHP", c_float),
        ("PlayerMaxHP", c_float),
        ("PlayerHealthRegen", c_float),
        ("PlayerEnergy", c_float),
        ("PlayerMaxEnergy", c_float),
        ("PlayerEnergyRegen", c_float),
        ("PlayerPosX", c_float),
        ("PlayerPosY", c_float),
        ("PlayerPosZ", c_float),
        ("PlayerTargetID", c_int),
        ("PlayerBuffs", c_int * MAX_NUMBER_OF_BUFFS),  # Buff IDs


        
        
        
        
        
        
        
        
        
        
        ("LastUpdated", c_int),
    ]

width, height = 0,0
def main():
    global width, height
    
    if PyImGui.begin("timer test"):
        if PyImGui.button("get Client Size"):
            io = PyImGui.get_io()
            print(f"Client Size: {io.display_size_x}, {io.display_size_y}")   
    PyImGui.end()
    
if __name__ == "__main__":
    main()
