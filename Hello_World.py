import PyImGui
from glm import c_uint32
from Py4GWCoreLib import AgentArray, Agent, Player

def main():
    living = Agent.GetLivingAgentByID(Player.GetAgentID())
    if living is None:
        return
        
    if PyImGui.begin("living data"):    
        PyImGui.text(f"Agent ID: {living.agent_id}")
        PyImGui.text(f"owner: {living.owner}")
        PyImGui.text(f"h00C8: {living.h00C8}")
        PyImGui.text(f"h00CC: {living.h00CC}")
        PyImGui.text(f"h00D0: {living.h00D0}")
        PyImGui.text(f"h00D4: {living.h00D4[0]}, {living.h00D4[1]}, {living.h00D4[2]}")
        PyImGui.text(f"animation_type: {living.animation_type}")
        PyImGui.text(f"h00E4: {living.h00E4[0]}, {living.h00E4[1]}")
        PyImGui.text(f"weapon_attack_speed: {living.weapon_attack_speed}")
        PyImGui.text(f"attack_speed_modifier: {living.attack_speed_modifier}")
        PyImGui.text(f"player_number: {living.player_number}")
        PyImGui.text(f"agent_model_type: {living.agent_model_type}")
        PyImGui.text(f"transmog_npc_id: {living.transmog_npc_id}")
        PyImGui.text(f"h0100: {living.h0100}")
        PyImGui.text(f"h0104: {living.h0104}")  # New
        PyImGui.text(f"h010C: {living.h010C}")  # New
        PyImGui.text(f"primary profession: {living.primary}")
        PyImGui.text(f"secondary profession: {living.secondary}")
        PyImGui.text(f"level: {living.level}")
        PyImGui.text(f"team_id: {living.team_id}")
        PyImGui.text(f"h0112: {living.h0112[0]}, {living.h0112[1]}")
        PyImGui.text(f"h0114: {living.h0114}")
        PyImGui.text(f"energy_regen: {living.energy_regen}")
        PyImGui.text(f"h011C: {living.h011C}")
        PyImGui.text(f"energy: {living.energy}")
        PyImGui.text(f"max_energy: {living.max_energy}")
        PyImGui.text(f"h0128: {living.h0128}") #overcast
        PyImGui.text(f"hp_pips: {living.hp_pips}")
        PyImGui.text(f"h0130: {living.h0130}")
        PyImGui.text(f"hp: {living.hp}")
        PyImGui.text(f"max_hp: {living.max_hp}")
        PyImGui.text(f"effects: {living.effects}")
        PyImGui.text(f"h0140: {living.h0140}")
        PyImGui.text(f"hex: {living.hex}")
        for i in range(19):
            PyImGui.text(f"h0145[{i}]: {living.h0145[i]}")
            
        PyImGui.text(f"model_state: {living.model_state}")
        PyImGui.text(f"type_map: {living.type_map}")
        PyImGui.text(f"h0160: {living.h0160[0]}, {living.h0160[1]}, {living.h0160[2]}, {living.h0160[3]}")
        PyImGui.text(f"in_spirit_range: {living.in_spirit_range}")
        PyImGui.text(f"visible_effects_list: {living.visible_effects_list}")
        PyImGui.text(f"h0180: {living.h0180}")
        PyImGui.text(f"login_number: {living.login_number}")
        PyImGui.text(f"animation_speed: {living.animation_speed}")
        PyImGui.text(f"animation_code: {living.animation_code}")
        PyImGui.text(f"animation_id: {living.animation_id}")
        for i in range(32):
            PyImGui.text(f"h0194[{i}]: {living.h0194[i]}")
        PyImGui.text(f"dagger_status: {living.dagger_status}")
        PyImGui.text(f"allegiance: {living.allegiance}")
        PyImGui.text(f"weapon_type: {living.weapon_type}")
        PyImGui.text(f"skill: {living.skill}")
        PyImGui.text(f"h01BA: {living.h01BA}")
        PyImGui.text(f"weapon_item_type: {living.weapon_item_type}")
        PyImGui.text(f"offhand_item_type: {living.offhand_item_type}")
        PyImGui.text(f"weapon_item_id: {living.weapon_item_id}")
        PyImGui.text(f"offhand_item_id: {living.offhand_item_id}")

    PyImGui.end()

if __name__ == "__main__":
    main()