import Py4GW

from Py4GWCoreLib import Timer
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import RawAgentArray
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import UIManager
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Color
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import PetBehavior
from Py4GWCoreLib import Keystroke
from Py4GWCoreLib import Key


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
        self.title_frame_parent_hash = 3332025202
        self.title_frame_offsets = [0,0,0,8,1]
        self.title_frame_id = 0
        self.title_frame_coords = frame_coords(0,0,0,0)
        self.title_frame_visible = False
        
        self.widget_active = True
        self.log_action = False
        self.pet_window = False
        self.pet_window_timer = Timer()
        self.pet_window_delay = 3000
        self.wipe_log = True
        self.throttle_timer = ThrottledTimer(100)
        self.update_target_throttle_timer = ThrottledTimer(1000)
        
        self.pet_id = 0
        self.pet_target_id = 0
        self.pet_bahavior = 2
        self.party_target_id = 0
        self.owner_target_id = 0

        self.agent_array = RawAgentArray()
        self.pet_name = ""
        self.player_name = ""
        self.party_target_name = ""
        self.owner_target_name = ""

    def wipe(self):
        players = GLOBAL_CACHE.Party.GetPlayers()
        players_dead = {player: False for player in players}
        wipe = False
        all_dead = True
        if GLOBAL_CACHE.Agent.GetHealth(GLOBAL_CACHE.Player.GetAgentID()) == 1.0 or GLOBAL_CACHE.Agent.IsAlive(GLOBAL_CACHE.Player.GetAgentID()):
            if not self.wipe_log:
                self.wipe_log = True

        if len(players) >= 1:
            for player in players:
                player_agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
                if GLOBAL_CACHE.Agent.GetHealth(player_agent_id) < 0.001 or GLOBAL_CACHE.Agent.IsDead(player_agent_id):
                    players_dead[player] = True

            for player in players_dead:
                if players_dead[player] == False:
                    all_dead = False

            if all_dead and self.wipe_log and self.log_action:
                self.wipe_log = False
                Py4GW.Console.Log(module_name, f"Wipe: Set Pet to Guard", Py4GW.Console.MessageType.Info)

            if all_dead:
                wipe = True
        return wipe

    def update(self):
        self.player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        self.pet_id = GLOBAL_CACHE.Party.Pets.GetPetID(self.player_agent_id)

        if not GLOBAL_CACHE.Agent.IsValid(self.pet_id):
            return

        self.title_frame_id =  UIManager.GetChildFrameID(self.title_frame_parent_hash, self.title_frame_offsets)
        if self.title_frame_id == 0:
            self.title_frame_visible = False
            return
        
        self.title_frame_coords.left, self.title_frame_coords.top, self.title_frame_coords.right, self.title_frame_coords.bottom = UIManager.GetFrameCoords(self.title_frame_id)
        self.title_frame_visible = UIManager.FrameExists(self.title_frame_id)
        
        if self.pet_id != 0:
            self.pet_target_id = GLOBAL_CACHE.Party.Pets.GetPetInfo(self.player_agent_id).locked_target_id
            self.pet_bahavior = GLOBAL_CACHE.Party.Pets.GetPetInfo(self.player_agent_id).behavior
            
        if GLOBAL_CACHE.Agent.IsDead(global_vars.pet_target_id):
            self.pet_target_id = 0
            
        self.party_target_id = Routines.Agents.GetPartyTargetID()
        _, alliegance = GLOBAL_CACHE.Agent.GetAllegiance(self.party_target_id)
        if not (alliegance == "Enemy"):
            self.party_target_id = 0
            
        if GLOBAL_CACHE.Agent.GetHealth(self.party_target_id) < 1.0:
            if GLOBAL_CACHE.Agent.GetHealth(self.party_target_id) == 0.0: # The client doesn't always reconise if a agent is dead, hence this check
                self.party_target_id = 0

        if GLOBAL_CACHE.Agent.IsDead(self.party_target_id):
            self.party_target_id = 0
        
        self.owner_target_id = GLOBAL_CACHE.Player.GetTargetID()
        _, alliegance = GLOBAL_CACHE.Agent.GetAllegiance(self.owner_target_id)
        if not (alliegance == "Enemy"):
            self.owner_target_id = 0

        if GLOBAL_CACHE.Agent.GetHealth(self.owner_target_id) < 1.0:
            if GLOBAL_CACHE.Agent.GetHealth(self.owner_target_id) == 0.0: # The client doesn't always reconise if a agent is dead, hence this check
                self.owner_target_id = 0

        if GLOBAL_CACHE.Agent.IsDead(self.owner_target_id):
            self.owner_target_id = 0

        if self.wipe():
            self.party_target_id = 0
            self.owner_target_id = 0

        self.agent_array.update()
        if self.pet_name == "":
            #self.pet_name = self.agent_array.get_name(self.pet_id).replace("Pet - ", "")
            self.pet_name = GLOBAL_CACHE.Agent.GetName(self.pet_id).replace("Pet - ", "")
        if self.player_name == "":
            #self.player_name = self.agent_array.get_name(self.player_agent_id)
            self.player_name = GLOBAL_CACHE.Agent.GetName(self.player_agent_id)
        #self.party_target_name = self.agent_array.get_name(self.party_target_id)
        self.party_target_name = GLOBAL_CACHE.Agent.GetName(self.party_target_id)
        #self.owner_target_name = self.agent_array.get_name(self.owner_target_id)
        self.owner_target_name = GLOBAL_CACHE.Agent.GetName(self.owner_target_id)

global_vars = Global_Vars()

def DrawWindow():
    global global_vars
    caption = "Helper ON" if global_vars.widget_active else "Helper OFF"
    caption_color = Color(0, 255, 0, 255) if global_vars.widget_active and global_vars.pet_bahavior != PetBehavior.Heel else Color(243, 230, 0, 255) if global_vars.widget_active and global_vars.pet_bahavior == PetBehavior.Heel else Color(255, 0, 0, 255)
    log_caption_color = Color(0, 255, 0, 255) if global_vars.log_action else Color(255, 0, 0, 255)
    if ImGui.floating_button(caption=caption, x=global_vars.title_frame_coords.left+75, y=global_vars.title_frame_coords.top+3, width=90, height=30, color=caption_color):
        global_vars.widget_active = not global_vars.widget_active
    if ImGui.floating_button(caption="Log", x=global_vars.title_frame_coords.left+135, y=global_vars.title_frame_coords.top+3, width=50, height=30, color= log_caption_color):
        global_vars.log_action = not global_vars.log_action
    

def configure():
    pass

def main():
    global global_vars

    if not Routines.Checks.Map.MapValid() or not GLOBAL_CACHE.Map.IsExplorable():
        if global_vars.pet_name != "":
            global_vars.pet_name = ""
        if global_vars.player_name != "":
            global_vars.player_name = ""
        if global_vars.pet_window_timer.IsRunning():
            global_vars.pet_window_timer.Stop()
        if global_vars.pet_window:
            global_vars.pet_window = False
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

    if not global_vars.pet_window:
        if global_vars.pet_window_timer.IsStopped():
            global_vars.pet_window_timer.Start()
        if global_vars.pet_window_timer.HasElapsed(global_vars.pet_window_delay):
            global_vars.pet_window = True
            Keystroke.PressAndRelease(Key.Apostrophe.value)
            if global_vars.log_action:
                Py4GW.Console.Log(module_name, f"Opening Pet Window", Py4GW.Console.MessageType.Info)

    if not Routines.Checks.Agents.InDanger():
        return

    if not global_vars.update_target_throttle_timer.IsExpired():
        return

    # Set Party Target to Pet
    if global_vars.party_target_id != 0 and global_vars.party_target_id != global_vars.pet_target_id and (global_vars.pet_bahavior == PetBehavior.Guard or global_vars.pet_bahavior == PetBehavior.Fight):
        
        GLOBAL_CACHE.Party.Pets.SetPetBehavior(PetBehavior.Fight, global_vars.party_target_id)
        #ActionQueueManager().AddAction("ACTION", GLOBAL_CACHE.Party.Pets.SetPetBehavior, PetBehavior.Fight, global_vars.party_target_id)
        if global_vars.log_action:
            Py4GW.Console.Log(module_name, f"{global_vars.pet_name} Fight {global_vars.party_target_name} ({global_vars.party_target_id})", Py4GW.Console.MessageType.Info)
        global_vars.update_target_throttle_timer.Reset()
    elif global_vars.owner_target_id != 0 and global_vars.owner_target_id != global_vars.pet_target_id and (global_vars.pet_bahavior == PetBehavior.Guard or global_vars.pet_bahavior == PetBehavior.Fight):
        GLOBAL_CACHE.Party.Pets.SetPetBehavior(PetBehavior.Fight, global_vars.owner_target_id)
        #ActionQueueManager().AddAction("ACTION", Party.Pets.SetPetBehavior, PetBehavior.Fight, global_vars.owner_target_id)
        if global_vars.log_action:
            Py4GW.Console.Log(module_name, f"{global_vars.pet_name} Fight {global_vars.owner_target_name} ({global_vars.owner_target_id})", Py4GW.Console.MessageType.Info)
        global_vars.update_target_throttle_timer.Reset()
    elif global_vars.party_target_id == 0 and global_vars.owner_target_id == 0 and global_vars.pet_bahavior == PetBehavior.Fight:
        GLOBAL_CACHE.Party.Pets.SetPetBehavior(PetBehavior.Guard, global_vars.player_agent_id)
        #ActionQueueManager().AddAction("ACTION", Party.Pets.SetPetBehavior, PetBehavior.Guard, global_vars.player_agent_id)
        if global_vars.log_action:
            Py4GW.Console.Log(module_name, f"{global_vars.pet_name} Guard {global_vars.player_name}", Py4GW.Console.MessageType.Info)
        global_vars.update_target_throttle_timer.Reset()


if __name__ == "__main__":
    main()