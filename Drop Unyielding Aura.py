from Py4GWCoreLib import *
module_name = "Get Bounty"

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





def configure():
    pass

def main():
    global widget_config
    pass
    if widget_config.game_throttle_timer.HasElapsed(widget_config.game_throttle_time):
        widget_config.is_map_loading = Map.IsMapLoading()
        if widget_config.is_map_loading:
            return
        
        widget_config.is_map_ready = Map.IsMapReady()
        widget_config.is_party_loaded = Party.IsPartyLoaded()
        widget_config.is_explorable = Map.IsExplorable()
        widget_config.map_valid = widget_config.is_map_ready and widget_config.is_party_loaded and widget_config.is_explorable
        
        if widget_config.map_valid:
            player_id = Player.GetAgentID()
            unyielding_aura = Skill.GetID("Unyielding Aura")
            widget_config.buff_exists = Effects.EffectExists(player_id, data['effect_id']) or Effects.BuffExists(player_id, data['effect_id'])
        widget_config.game_throttle_timer.Start()
        
    if widget_config.map_valid and widget_config.bounty_window_exists and not widget_config.bounty_taken:
        clickable_frame = UIManager.GetParentID(widget_config.frame_id)
        UIManager.FrameClick(frame_id = clickable_frame)
        #print(f"Clicked on Bounty on frame_id: {clickable_frame}")
        widget_config.bounty_taken = True

        

if __name__ == "__main__":
    main()

