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
    unyielding_aura = Skill.GetID("Unyielding_Aura")
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
            widget_config.buff_exists = Effects.EffectExists(player_id, unyielding_aura) or Effects.BuffExists(player_id, unyielding_aura)
        widget_config.game_throttle_timer.Start()
        
    if widget_config.map_valid and  widget_config.buff_exists:
        buff_id = Effects.GetBuffID(unyielding_aura)
        ActionQueueManager().AddAction("ACTION", Effects.DropBuff, buff_id)
        Effects.DropBuff(buff_id)

        

if __name__ == "__main__":
    main()
    ActionQueueManager().ProcessQueue('ACTION')

