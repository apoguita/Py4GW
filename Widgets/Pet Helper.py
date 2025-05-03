from Py4GWCoreLib import *

module_name = "PetHelper"

class frame_coords:
    def __init__(self, left,top,right,bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

class Global_Vars:
    def __init__(self):
        self.title_frame = None
        self.title_frame_hash = 3282622945
        self.title_frame_id = 0
        self.title_frame_coords = frame_coords(0,0,0,0)
        self.title_frame_visible = False
        
        self.widget_active = True
        self.throttle_timer = ThrottledTimer(100)
        self.update_target_throttle_timer = ThrottledTimer(1000)
        
        self.pet_id = 0
        self.party_target_id = 0
        
    def update(self):
        self.title_frame_id = UIManager.GetFrameIDByHash(self.title_frame_hash)
        if self.title_frame_id == 0:
            self.title_frame_visible = False
            return
        
        self.title_frame_coords.left, self.title_frame_coords.top, self.title_frame_coords.right, self.title_frame_coords.bottom = UIManager.GetFrameCoords(self.title_frame_id)
        self.title_frame_visible = UIManager.FrameExists(self.title_frame_id)
        
        self.player_agent_id = Player.GetAgentID()
        self.pet_id = Party.Pets.GetPetID(self.player_agent_id)
        if self.pet_id != 0:
            self.pet_target_id = Party.Pets.GetPetInfo(self.player_agent_id).locked_target_id
            
        if Agent.IsDead(global_vars.pet_target_id):
            self.pet_target_id = 0
            
        self.party_target_id = Routines.Agents.GetPartyTargetID()
        _, alliegance = Agent.GetAllegiance(self.party_target_id)
        if not (alliegance == "Enemy"):
            self.party_target_id = 0
            
        if Agent.IsDead(self.party_target_id):
            self.party_target_id = 0
        
        self.owner_target_id = Player.GetTargetID()
        _, alliegance = Agent.GetAllegiance(self.owner_target_id)
        if not (alliegance == "Enemy"):
            self.owner_target_id = 0
        
        if Agent.IsDead(self.owner_target_id):
            self.owner_target_id = 0

        
global_vars = Global_Vars()

def DrawWindow():
    global global_vars
    caption = "Helper ON" if global_vars.widget_active else "Helper OFF"
    caption_color = Color(0, 255, 0,255).to_tuple() if global_vars.widget_active else Color(255, 0, 0,255).to_tuple()
    if ImGui.floating_button(caption, global_vars.title_frame_coords.left+75, global_vars.title_frame_coords.top+3,100,30,caption_color):
        global_vars.widget_active = not global_vars.widget_active

def configure():
    pass

def main():
    global global_vars

    if not Routines.Checks.Map.MapValid() and not Map.IsExplorable():
        return
    
    if not global_vars.throttle_timer.IsExpired():
        return
    
    global_vars.update()
    
    if global_vars.pet_id == 0:
        return 
    
    if global_vars.title_frame_visible:
        DrawWindow()
        
    if not global_vars.widget_active:
        return
        
    if not Routines.Checks.Agents.InDanger():
        return
    
    if not global_vars.update_target_throttle_timer.IsExpired():
        return
    
    # Set Party Target to Pet
    if global_vars.party_target_id != 0 and global_vars.party_target_id != global_vars.pet_target_id:
        ActionQueueManager().AddAction("ACTION", Party.Pets.SetPetBehavior,PetBehavior.Fight, global_vars.party_target_id)
        global_vars.update_target_throttle_timer.Reset()
    elif global_vars.owner_target_id != 0 and global_vars.owner_target_id != global_vars.pet_target_id:
        ActionQueueManager().AddAction("ACTION", Party.Pets.SetPetBehavior,PetBehavior.Fight, global_vars.owner_target_id)
        global_vars.update_target_throttle_timer.Reset()
    
    
    ActionQueueManager().ProcessQueue("ACTION")
    

if __name__ == "__main__":
    main()