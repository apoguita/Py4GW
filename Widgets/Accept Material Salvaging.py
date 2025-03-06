from Py4GWCoreLib import *
module_name = "Return to Outpost"

class config:
    def __init__(self):
        self.is_map_loading = False
        self.is_map_ready = False
        self.is_party_loaded = False
        self.material_salvaging_window = False
        self.frame_id = 0
        self.dialog_accepted = False
        self.map_valid = False
        self.parent_hash = 140452905
        self.child_offsets = [6,98]
        self.yes_button_offsets = [6,98,6]
        self.frame_label = "Salvage Materials Dialog"
        
        self.game_throttle_time = 100
        self.game_throttle_timer = Timer()
        self.game_throttle_timer.Start()

widget_config = config()





def configure():
    pass

def main():
    global widget_config
    
    if widget_config.game_throttle_timer.HasElapsed(widget_config.game_throttle_time):
        widget_config.is_map_loading = Map.IsMapLoading()
        if widget_config.is_map_loading:
            widget_config.dialog_accepted = False
            widget_config.material_salvaging_window = False
            return
        
        widget_config.is_map_ready = Map.IsMapReady()
        widget_config.is_party_loaded = Party.IsPartyLoaded()
        widget_config.map_valid = widget_config.is_map_ready and widget_config.is_party_loaded
        
        if widget_config.map_valid:
            widget_config.frame_id = UIManager.GetChildFrameID(parent_hash = widget_config.parent_hash, child_offsets = widget_config.child_offsets)
            if widget_config.frame_id != 0:
                widget_config.material_salvaging_window = UIManager.FrameExists(widget_config.frame_id)
                if not widget_config.material_salvaging_window:
                    widget_config.dialog_accepted = False
                    
            else:
                widget_config.dialog_accepted = False
                widget_config.material_salvaging_window = False
                return
        widget_config.game_throttle_timer.Start()
        
    if widget_config.map_valid and widget_config.material_salvaging_window and not widget_config.dialog_accepted:
        clickable_frame = UIManager.GetChildFrameID(parent_hash = widget_config.parent_hash, child_offsets = widget_config.yes_button_offsets)
        UIManager.FrameClick(frame_id = clickable_frame)
        #print(f"Clicked on Bounty on frame_id: {clickable_frame}")
        widget_config.dialog_accepted = True
        #draw_color:int = Utils.RGBToColor(0, 255, 0, 125)
        #UIManager().DrawFrame(widget_config.frame_id,draw_color)
        

if __name__ == "__main__":
    main()

