from Py4GWCoreLib import *
module_name = "Return to Outpost"

class config:
    def __init__(self):
        self.is_map_loading = False
        self.is_map_ready = False
        self.is_party_loaded = False
        self.is_explorable = False
        self.bounty_window_exists = False
        self.frame_id = 0
        self.frame_hash = 3856160816
        self.bounty_taken = False
        self.bounty_taken_timer = Timer()
        self.bounty_taken_timer.Start()
        self.map_valid = False
        
        self.game_throttle_time = 500
        self.game_throttle_timer = Timer()
        self.game_throttle_timer.Start()

widget_config = config()





def configure():
    pass

def main():
    global widget_config
    return
    
    if widget_config.game_throttle_timer.HasElapsed(widget_config.game_throttle_time):
        widget_config.is_map_loading = Map.IsMapLoading()
        if widget_config.is_map_loading:
            widget_config.bounty_taken = False
            widget_config.bounty_window_exists = False
            return
        
        widget_config.is_map_ready = Map.IsMapReady()
        widget_config.is_party_loaded = Party.IsPartyLoaded()
        widget_config.is_explorable = Map.IsExplorable()
        widget_config.map_valid = widget_config.is_map_ready and widget_config.is_party_loaded and widget_config.is_explorable
        
        if widget_config.map_valid:
            widget_config.frame_id = UIManager.GetFrameIDByHash(widget_config.frame_hash)
            if widget_config.frame_id != 0:
                widget_config.bounty_window_exists = UIManager.FrameExists(widget_config.frame_id)
            else:
                widget_config.bounty_window_exists = False
        widget_config.game_throttle_timer.Start()
        
        if widget_config.map_valid and widget_config.bounty_window_exists and not widget_config.bounty_taken:
            frame_id = UIManager.GetFrameIDByCustomLabel(frame_label = "NPC Bounty Dialog.Option1.Icon") or 0
            clickable_frame = UIManager.GetParentID(frame_id)
            if UIManager.FrameExists(clickable_frame):
                UIManager.FrameClick(frame_id = clickable_frame)
            widget_config.bounty_taken = True
            
    if widget_config.bounty_taken and widget_config.bounty_taken_timer.HasElapsed(5000):
        widget_config.bounty_taken = False
        widget_config.bounty_taken_timer.Reset()

        

if __name__ == "__main__":
    main()

