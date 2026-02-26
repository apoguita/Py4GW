from Py4GWCoreLib import ImGui, PyImGui, Timer
from .constants import MODULE_NAME, MAX_NUM_PLAYERS, NUMBER_OF_SKILLS
from .types import PlayerStruct, CandidateStruct

class HeroAI_varsClass:
    global MAX_NUM_PLAYERS, NUMBER_OF_SKILLS
    def __init__(self):
        self.all_candidate_struct = [CandidateStruct() for _ in range(MAX_NUM_PLAYERS)]
        self.submit_candidate_struct = CandidateStruct()
        self.all_player_struct = [PlayerStruct() for _ in range(MAX_NUM_PLAYERS)]
        

class HeroAI_Window_varsClass:
    global MODULE_NAME
    def __init__(self):
        self.main_window = ImGui.WindowModule(MODULE_NAME, "HeroAI - Follower", window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
        self.control_window = ImGui.WindowModule(MODULE_NAME, "HeroAI", window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
        self.tools_window = ImGui.WindowModule(MODULE_NAME, "Multibox Tools", window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
        self.follow_formations_window = ImGui.WindowModule(MODULE_NAME, "Follow Formations", window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)

class DebugWindowClass:
    global MODULE_NAME
    def __init__(self, name):
        self.name = name
        self.visible = False
        self.window = ImGui.WindowModule(MODULE_NAME, name, window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)


class DebugWindowListClass:
    def __init__(self):
        self.main_window = DebugWindowClass("Debug Menu")
        self.candidate_window = DebugWindowClass("Candidates Debug")


""" Helper Variables """

oldAngle = 0.0  # used for angle change

#hero_formation = [ 0.0, 45.0, -45.0, 90.0, -90.0, 135.0, -135.0, 180.0 ] # position on the grid of heroes
hero_formation = [ 0.0, 45.0, -45.0, 90.0, -90.0, 135.0, -135.0, 180.0 , -180.0, 225.0, -225.0, 270.0] # position on the grid of heroes

overlay_explorable_initialized = False
show_area_rings = True
show_hero_follow_grid = True
show_distance_on_followers = True
show_broadcast_follow_positions = True
show_broadcast_follow_threshold_rings = True

capture_flag_all = False
capture_hero_flag = False
capture_hero_index = 0
capture_mouse_timer = Timer()

option_show_floating_targets = True
