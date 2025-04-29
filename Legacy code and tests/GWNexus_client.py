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
    
class SharedAgentArray(Structure):
    _pack_ = 1
    _fields_ = [
        ("ally_array", c_int * 64),
        ("enemy_array", c_int * 64),
        ("neutral_array", c_int * 64),
        ("spirit_pet_array", c_int * 64),
        ("minion_array", c_int * 64),
        ("npc_minipet_array", c_int * 64),
        ("item_array", c_int * 64),
        ("gadget_array", c_int * 64),
    ]
    
class SharedAgentData(Structure):
    _pack_ = 1
    _fields_ = [
        ("request_for_data", c_bool),
        ("request_agent_id", c_int),
        ("data_ready", c_bool),
        
        ("agent_id", c_int),
        ("pos_x", c_float),
        ("pos_y", c_float),
        ("pos_z", c_float),
        ("rotation_angle", c_float),
        ("profession", c_int),
        ("level", c_int),
        ("health", c_float),
        ("energy", c_float),
        ("max_health", c_float),
        ("max_energy", c_float),
    ]
    
class SharedMemoryArea(Structure):
    _pack_ = 1
    _fields_ = [
        ("player_data", SharedPlayerData),
        ("agent_array", SharedAgentArray),
        ("agent_data", SharedAgentData),
    ]
    
    
_size_ = ctypes.sizeof(SharedMemoryArea)
# Create shared memory
existing_shm = shared_memory.SharedMemory(name="GW_NEXUS_SMA")
# Map buffer to structure
GAME_DATA = SharedMemoryArea.from_buffer(existing_shm.buf)

#trottled timers to handle data synchronization
game_query_timer =  ThrottledTimer(75) #75ms throttle

def main():
    global game_query_timer, GAME_DATA
    
    if PyImGui.begin("Nexus CLient"):
        # Display player data
        PyImGui.text("Player Data")
        PyImGui.text(f"Agent ID: {GAME_DATA.player_data.agent_id}")
        PyImGui.text(f"Position: ({GAME_DATA.player_data.pos_x}, {GAME_DATA.player_data.pos_y}, {GAME_DATA.player_data.pos_z})")
        PyImGui.text(f"Rotation Angle: {GAME_DATA.player_data.rotation_angle}")
        PyImGui.text(f"Primary Profession: {GAME_DATA.player_data.primary_profession}")
        PyImGui.text(f"Secondary Profession: {GAME_DATA.player_data.secondary_profession}")
        PyImGui.text(f"Level: {GAME_DATA.player_data.level}")
        PyImGui.text(f"Health: {GAME_DATA.player_data.health}/{GAME_DATA.player_data.max_health}")
        PyImGui.text(f"Energy: {GAME_DATA.player_data.energy}/{GAME_DATA.player_data.max_energy}")
    PyImGui.end()
    
    
    
if __name__ == "__main__":
    main()
