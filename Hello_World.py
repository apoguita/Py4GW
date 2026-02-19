import PyImGui
from glm import c_uint32
from Py4GWCoreLib import AgentArray, Agent, Player, Party
import Py4GW

def main():
    living = Agent.GetLivingAgentByID(Player.GetAgentID())
    if living is None:
        return
        
    if PyImGui.begin("living data"):    
        PyImGui.text(f"Player Agent ID: {Player.GetAgentID()}")
        PyImGui.text(f"login number: {Player.GetLoginNumber()}")
        PyImGui.text(f"tick count: {Py4GW.Game.get_tick_count64()}")
        
        PyImGui.separator()
        
        for hero_data in Party.GetHeroes():
            PyImGui.text(f"Agent ID: {hero_data.agent_id}")
            PyImGui.text(f"Owner Player ID: {hero_data.owner_player_id}")
            PyImGui.text(f"Hero ID: {hero_data.hero_id.GetID()}")
            aid = Party.Players.GetAgentIDByLoginNumber(hero_data.owner_player_id)
            PyImGui.text(f"Agent ID from Party: {aid}")
            PyImGui.separator()
            
            
            
        

    PyImGui.end()

if __name__ == "__main__":
    main()