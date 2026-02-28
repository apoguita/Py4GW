from Py4GWCoreLib import Timer
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Agent
from Py4GWCoreLib import UIManager
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Color
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import PetBehavior
from Py4GWCoreLib import Keystroke
from Py4GWCoreLib import Key
from Py4GWCoreLib import Map, Player
import PyImGui

MODULE_NAME = "Pet Helper"
MODULE_ICON = "Textures\\Module_Icons\\Pet Helper.png"

class frame_coords:
    def __init__(self, left,top,right,bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

class Global_Vars:
    def __init__(self):
        self.title_frame_parent_hash = 3332025202
        self.title_frame_offsets = [0,0,0,8,1]
        self.title_frame_id = 0
        self.title_frame_coords = frame_coords(0,0,0,0)
        self.title_frame_visible = False
        
        self.widget_active = True
        self.pet_window = False
        self.pet_window_timer = Timer()
        self.pet_window_delay = 3000
        self.throttle_timer = ThrottledTimer(500)
        self.update_target_throttle_timer = ThrottledTimer(1000)
        self.checks_timer = ThrottledTimer(500)
        self.non_enemy_target_grace_timer = Timer()
        self.non_enemy_target_grace_ms = 750
        
        self.pet_id = 0
        self.pet_target_id = 0
        self.pet_bahavior = 2
        self.owner_target_id = 0
        self.owner_has_non_enemy_target = False

    def _validate_enemy_target(self, agent_id):
        if agent_id == 0 or not Agent.IsValid(agent_id):
            return 0

        _, allegiance = Agent.GetAllegiance(agent_id)
        if allegiance != "Enemy":
            return 0

        # Keep a minimal death sanity check; dead reporting is not always consistent.
        if Agent.GetHealth(agent_id) == 0.0 or Agent.IsDead(agent_id):
            return 0

        return agent_id

    def update(self):
        
        self.player_agent_id = Player.GetAgentID()
        self.pet_id = GLOBAL_CACHE.Party.Pets.GetPetID(self.player_agent_id)

        if not Agent.IsValid(self.pet_id):
            return

        self.title_frame_id =  UIManager.GetChildFrameID(self.title_frame_parent_hash, self.title_frame_offsets)
        if self.title_frame_id == 0:
            self.title_frame_visible = False
            return
        
        self.title_frame_coords.left, self.title_frame_coords.top, self.title_frame_coords.right, self.title_frame_coords.bottom = UIManager.GetFrameCoords(self.title_frame_id)
        self.title_frame_visible = UIManager.FrameExists(self.title_frame_id)
        
        if self.pet_id != 0:
            pet_info = GLOBAL_CACHE.Party.Pets.GetPetInfo(self.player_agent_id)
            self.pet_target_id = pet_info.locked_target_id
            self.pet_bahavior = pet_info.behavior

        raw_owner_target_id = Player.GetTargetID()
        self.owner_has_non_enemy_target = False
        self.owner_target_id = 0

        if raw_owner_target_id != 0 and Agent.IsValid(raw_owner_target_id):
            _, allegiance = Agent.GetAllegiance(raw_owner_target_id)
            if allegiance != "Enemy":
                self.owner_has_non_enemy_target = True
                if self.non_enemy_target_grace_timer.IsRunning():
                    self.non_enemy_target_grace_timer.Stop()
                self.non_enemy_target_grace_timer.Start()
            else:
                self.owner_target_id = self._validate_enemy_target(raw_owner_target_id)
                if self.owner_target_id != 0 and self.non_enemy_target_grace_timer.IsRunning():
                    self.non_enemy_target_grace_timer.Stop()

global_vars = Global_Vars()

def DrawWindow():
    global global_vars
    caption = "Helper ON" if global_vars.widget_active else "Helper OFF"
    caption_color = Color(0, 255, 0, 255) if global_vars.widget_active and global_vars.pet_bahavior != PetBehavior.Heel else Color(243, 230, 0, 255) if global_vars.widget_active and global_vars.pet_bahavior == PetBehavior.Heel else Color(255, 0, 0, 255)
    if ImGui.floating_button(caption=caption, x=global_vars.title_frame_coords.left+75, y=global_vars.title_frame_coords.top+3, width=90, height=30, color=caption_color):
        global_vars.widget_active = not global_vars.widget_active
    

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Pet Helper", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("An automation utility for Ranger pets that synchronizes")
    PyImGui.text("pet behaviors with the player or party leader's actions.")
    PyImGui.text("Ensures pets are always engaging the correct tactical targets.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Auto-Targeting: Automatically commands pets to attack the party's current target")
    PyImGui.bullet_text("Behavior Sync: Switches pet states between 'Guard' and 'Fight' dynamically")
    PyImGui.bullet_text("UI Integration: Monitors the game's internal Pet Window for real-time status")
    PyImGui.bullet_text("Throttled Execution: Prevents command spamming through smart update timers")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Zilvereyes")
    PyImGui.bullet_text("Contributors: Apo")

    PyImGui.end_tooltip()
    
def draw():
    global global_vars
    map_valid = Routines.Checks.Map.MapValid()
    map_explorable = Map.IsExplorable()


    if not map_valid or not map_explorable:
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


    if not map_valid or not map_explorable:
        return
    
    if not global_vars.widget_active:
        return

    if not global_vars.pet_window:
        if global_vars.pet_window_timer.IsStopped():
            global_vars.pet_window_timer.Start()
        if global_vars.pet_window_timer.HasElapsed(global_vars.pet_window_delay):
            global_vars.pet_window = True
            Keystroke.PressAndRelease(Key.Apostrophe.value)
            
    if not global_vars.checks_timer.IsExpired():
        return
    
    global_vars.checks_timer.Reset()

    if not Routines.Checks.Agents.InDanger():
        return

    if not global_vars.update_target_throttle_timer.IsExpired():
        return

    # Player is targeting self/ally/NPC while using another skill; do not override pet state.
    if global_vars.owner_has_non_enemy_target:
        return

    # Keep pet target aligned to the player's current enemy target.
    if global_vars.owner_target_id != 0 and global_vars.owner_target_id != global_vars.pet_target_id and (global_vars.pet_bahavior == PetBehavior.Guard or global_vars.pet_bahavior == PetBehavior.Fight):
        GLOBAL_CACHE.Party.Pets.SetPetBehavior(PetBehavior.Fight, global_vars.owner_target_id)
        #ActionQueueManager().AddAction("ACTION", Party.Pets.SetPetBehavior, PetBehavior.Fight, global_vars.owner_target_id)
        global_vars.update_target_throttle_timer.Reset()
    elif global_vars.owner_target_id == 0 and global_vars.pet_bahavior == PetBehavior.Fight:
        if global_vars.non_enemy_target_grace_timer.IsRunning() and not global_vars.non_enemy_target_grace_timer.HasElapsed(global_vars.non_enemy_target_grace_ms):
            return
        if global_vars.non_enemy_target_grace_timer.IsRunning():
            global_vars.non_enemy_target_grace_timer.Stop()
        GLOBAL_CACHE.Party.Pets.SetPetBehavior(PetBehavior.Guard, global_vars.player_agent_id)
        #ActionQueueManager().AddAction("ACTION", Party.Pets.SetPetBehavior, PetBehavior.Guard, global_vars.player_agent_id)
        global_vars.update_target_throttle_timer.Reset()


if __name__ == "__main__":
    draw()
