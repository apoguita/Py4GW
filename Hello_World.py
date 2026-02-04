import PyImGui
from Py4GWCoreLib import AgentArray, Agent

def main():
    if PyImGui.begin("Hello World"):    
        spirit_pet_array = AgentArray.GetSpiritPetArray()
        for agent_id in spirit_pet_array:
            is_spawned = Agent.IsSpawned(agent_id)
            PyImGui.text(f"Spirit Pet Agent ID: {agent_id}")   
            PyImGui.text(f"Is Spawned: {is_spawned}")

    PyImGui.end()

if __name__ == "__main__":
    main()