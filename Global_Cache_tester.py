from Py4GWCoreLib import *

MODULE_NAME = "global cache"


def main():
    global global_cache
    GLOBAL_CACHE._update_cache()
     
    if PyImGui.begin(MODULE_NAME):
        if PyImGui.collapsing_header("Player"):
            PyImGui.text(f"Player ID: {GLOBAL_CACHE.Player.GetAgentID()}")
            PyImGui.text(f"Player Name: {GLOBAL_CACHE.Player.GetName()}")
            PyImGui.text(f"Player Position: {GLOBAL_CACHE.Player.GetXY()}")
            
            if PyImGui.button("move to 100,100"):
                x, y = 100, 100
                GLOBAL_CACHE.Player.Move(x, y)
        if PyImGui.collapsing_header("Map"):
            PyImGui.text(f"Map ID: {GLOBAL_CACHE.Map.GetMapID()}")
            PyImGui.text(f"Map Name: {GLOBAL_CACHE.Map.GetMapName()}")
            if PyImGui.button("travel to 248"):
                map_id = 248
                GLOBAL_CACHE.Map.Travel(map_id)
        
        if PyImGui.collapsing_header("Agent"):
            agent_id = GLOBAL_CACHE.Player.GetTargetID() if GLOBAL_CACHE.Player.GetTargetID() != 0 else GLOBAL_CACHE.Player.GetAgentID()
            PyImGui.text(f"Agent ID: {agent_id}")
            PyImGui.text(f"Agent Name: {GLOBAL_CACHE.Agent.GetName(agent_id)}")
            PyImGui.text(f"Agent Position: {GLOBAL_CACHE.Agent.GetXY(agent_id)}")

        if PyImGui.collapsing_header("Agent Array"):
            agent_array = GLOBAL_CACHE.AgentArray.GetAgentArray()
            for agent_id in agent_array:
                agent_name = GLOBAL_CACHE.Agent.GetName(agent_id)
                agent_position = GLOBAL_CACHE.Agent.GetXY(agent_id)
                PyImGui.text(f"Agent ID: {agent_id}, Name: {agent_name}, Position: {agent_position}")
                
        if PyImGui.collapsing_header("Camera"):
            time_in_the_map = GLOBAL_CACHE.Camera.GetTimeInTheMap()
            PyImGui.text(f"Time in the map: {time_in_the_map}")
            
        if PyImGui.collapsing_header("Effects"):
            buffs = GLOBAL_CACHE.Effects.GetBuffs(GLOBAL_CACHE.Player.GetAgentID())
            effects = GLOBAL_CACHE.Effects.GetEffects(GLOBAL_CACHE.Player.GetAgentID())
            
            for buff in buffs:
                buff_id = buff.buff_id
                skill_id = buff.skill_id
                skill_name = "" #PySkill.Skill(skill_id).id.GetName()
                target_agent_id = buff.target_agent_id
                
                PyImGui.text(f"Buff ID: {buff_id} - {skill_id} - {skill_name} - {target_agent_id}")
                
            PyImGui.separator()
                
            for effect in effects:
                effect_id = effect.effect_id
                skill_id = effect.skill_id
                skill_name = "" #zPySkill.Skill(skill_id).id.GetName()
                duration = effect.duration
                attribute_level = effect.attribute_level
                time_remaining = effect.time_remaining
                
                PyImGui.text(f"Effect ID: {effect_id} - {skill_id} - {skill_name} - {duration} - {attribute_level} - {time_remaining}")

        if PyImGui.collapsing_header("Items"):
            item_array = GLOBAL_CACHE.ItemArray.GetRawItemArray([1,2,3,4])
            for item in item_array:
                item_id = item.item_id
                item_name = GLOBAL_CACHE.Item.GetName(item_id)
                item_quantity = item.quantity
                item_value = item.value
                
                PyImGui.text(f"Item ID: {item_id} - {item_name} - {item_quantity} - {item_value}")
         
    PyImGui.end()
    
    
    
if __name__ == "__main__":
    main()
