from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Timer
from Py4GWCoreLib import Map, Player, Color, ImGui
import PyImGui
module_name = "Drop Unyielding Aura"

MODULE_NAME = "Drop Unyielding Aura"
MODULE_ICON = "Textures\\Skill_Icons\\[268] - Unyielding Aura.jpg"

class config:
    def __init__(self):
        self.is_map_loading = False
        self.is_map_ready = False
        self.is_party_loaded = False
        self.is_explorable = False
        self.buff_exists = False
        self.map_valid = False
        
        self.game_throttle_time = 100
        self.game_throttle_timer = Timer()
        self.game_throttle_timer.Start()

widget_config = config()



def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Drop Unyielding Aura", title_color.to_tuple_normalized())
    ImGui.pop_font()
    
    PyImGui.spacing()
    PyImGui.separator()
    
    # Description
    PyImGui.text("Automatically drops the Unyielding Aura buff when mantained.")
    
    PyImGui.spacing()
    PyImGui.separator()
    
    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Monitors your buffs and removes Unyielding Aura in explorable maps.")
    
    PyImGui.spacing()
    PyImGui.separator()
    
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")
    
    PyImGui.end_tooltip()

def main():
    global widget_config
    unyielding_aura = GLOBAL_CACHE.Skill.GetID("Unyielding_Aura")
    if widget_config.game_throttle_timer.HasElapsed(widget_config.game_throttle_time):
        widget_config.is_map_loading = Map.IsMapLoading()
        if widget_config.is_map_loading:
            return
        
        widget_config.is_map_ready = Map.IsMapReady()
        widget_config.is_party_loaded = GLOBAL_CACHE.Party.IsPartyLoaded()
        widget_config.is_explorable = Map.IsExplorable()
        widget_config.map_valid = widget_config.is_map_ready and widget_config.is_party_loaded and widget_config.is_explorable
        
        if widget_config.map_valid:
            player_id = Player.GetAgentID()
            widget_config.buff_exists = GLOBAL_CACHE.Effects.EffectExists(player_id, unyielding_aura) or GLOBAL_CACHE.Effects.BuffExists(player_id, unyielding_aura)
        widget_config.game_throttle_timer.Start()
        
    if widget_config.map_valid and  widget_config.buff_exists:
        buff_id = GLOBAL_CACHE.Effects.GetBuffID(unyielding_aura)
        GLOBAL_CACHE.Effects.DropBuff(buff_id)

        

if __name__ == "__main__":
    main()

