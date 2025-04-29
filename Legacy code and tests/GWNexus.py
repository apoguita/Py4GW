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
shared_memory_area = shared_memory.SharedMemory(name="GW_NEXUS_SMA", create=True, size=_size_)
# Cast the buffer to our structure
GAME_DATA = SharedMemoryArea.from_buffer(shared_memory_area.buf)

#trottled timers to handle data synchronization
game_query_timer =  ThrottledTimer(75) #75ms throttle

def main():
    global game_query_timer, GAME_DATA
    
    if game_query_timer.IsExpired():
        game_query_timer.Reset()
        
        #update Player data
        GAME_DATA.player_data.agent_id = Player.GetAgentID()
        x,y,z = Agent.GetXYZ(Player.GetAgentID())
        GAME_DATA.player_data.pos_x = x
        GAME_DATA.player_data.pos_y = y
        GAME_DATA.player_data.pos_z = z
        GAME_DATA.player_data.rotation_angle = Agent.GetRotationAngle(Player.GetAgentID())
        GAME_DATA.player_data.agent_name = Player.GetName()
        prim_prof, second_prof = Agent.GetProfessionIDs(Player.GetAgentID())
        GAME_DATA.player_data.primary_profession = prim_prof
        GAME_DATA.player_data.secondary_profession = second_prof
        GAME_DATA.player_data.level = Agent.GetLevel(Player.GetAgentID())
        GAME_DATA.player_data.health = Agent.GetHealth(Player.GetAgentID())
        GAME_DATA.player_data.energy = Agent.GetEnergy(Player.GetAgentID())
        GAME_DATA.player_data.max_health = Agent.GetMaxHealth(Player.GetAgentID())
        GAME_DATA.player_data.max_energy = Agent.GetMaxEnergy(Player.GetAgentID())
        #update Agent data
        if GAME_DATA.agent_data.request_for_data:
            GAME_DATA.agent_data.request_for_data = False
            agent_id = GAME_DATA.agent_data.request_agent_id
            GAME_DATA.agent_data.agent_id = agent_id
            x,y,z = Agent.GetXYZ(agent_id)
            GAME_DATA.agent_data.pos_x = x
            GAME_DATA.agent_data.pos_y = y
            GAME_DATA.agent_data.pos_z = z
            GAME_DATA.agent_data.rotation_angle = Agent.GetRotationAngle(agent_id)
            prim_prof, second_prof = Agent.GetProfessionIDs(agent_id)
            GAME_DATA.agent_data.primary_profession = prim_prof
            GAME_DATA.agent_data.secondary_profession = second_prof
            GAME_DATA.agent_data.level = Agent.GetLevel(agent_id)
            GAME_DATA.agent_data.health = Agent.GetHealth(agent_id)
            GAME_DATA.agent_data.energy = Agent.GetEnergy(agent_id)
            GAME_DATA.agent_data.max_health = Agent.GetMaxHealth(agent_id)
            GAME_DATA.agent_data.max_energy = Agent.GetMaxEnergy(agent_id)
            GAME_DATA.agent_data.data_ready = True
        
        #update Agent arrays
        ally_array = AgentArray.GetAllyArray()
        enemy_array = AgentArray.GetEnemyArray()
        neutral_array = AgentArray.GetNeutralArray()
        spirit_pet_array = AgentArray.GetSpiritPetArray()
        minion_array = AgentArray.GetMinionArray()
        npc_minipet_array = AgentArray.GetNPCMinipetArray()
        item_array = AgentArray.GetItemArray()
        gadget_array = AgentArray.GetGadgetArray()
        
        def fill_array(target, source):
            max_len = len(target)
            for i in range(max_len):
                if i < len(source):
                    target[i] = source[i]
                else:
                    target[i] = 0  # or -1 if you want "invalid agent"
        
        fill_array(GAME_DATA.agent_array.ally_array, ally_array)
        fill_array(GAME_DATA.agent_array.enemy_array, enemy_array)
        fill_array(GAME_DATA.agent_array.neutral_array, neutral_array)
        fill_array(GAME_DATA.agent_array.spirit_pet_array, spirit_pet_array)
        fill_array(GAME_DATA.agent_array.minion_array, minion_array)
        fill_array(GAME_DATA.agent_array.npc_minipet_array, npc_minipet_array)
        fill_array(GAME_DATA.agent_array.item_array, item_array)
        fill_array(GAME_DATA.agent_array.gadget_array, gadget_array)
    
if __name__ == "__main__":
    main()
