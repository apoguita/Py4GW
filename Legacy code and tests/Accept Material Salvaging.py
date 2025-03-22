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
    
    if Map.IsMapLoading():
        widget_config.dialog_accepted = False
        widget_config.material_salvaging_window = False
        return
    
    if not (Map.IsMapReady() and Party.IsPartyLoaded()):
        return
    
    
    if widget_config.game_throttle_timer.HasElapsed(widget_config.game_throttle_time):
        widget_config.game_throttle_timer.Reset()
        salvage_material_window = UIManager.GetChildFrameID(widget_config.parent_hash,widget_config.yes_button_offsets)
    
        frame_exists = UIManager.FrameExists(salvage_material_window)
        
        if not frame_exists:
            widget_config.dialog_accepted = False
            widget_config.material_salvaging_window = False
            return
        
        if widget_config.dialog_accepted:
            return
        
        clickable_frame = UIManager.GetChildFrameID(widget_config.parent_hash,widget_config.yes_button_offsets)
        ActionQueueManager().AddAction("ACTION",UIManager.FrameClick,clickable_frame)
        widget_config.dialog_accepted = True
        

if __name__ == "__main__":
    main()