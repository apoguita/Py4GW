from Py4GWCoreLib import ImGui, PyImGui, Timer
from .constants import MODULE_NAME, MAX_NUM_PLAYERS, NUMBER_OF_SKILLS
from .types import PlayerStruct, CandidateStruct, GameOptionStruct
from .shared_memory_manager import SharedMemoryManager

class HeroAI_varsClass:
    global MAX_NUM_PLAYERS, NUMBER_OF_SKILLS
    def __init__(self):
        self.shared_memory_handler = SharedMemoryManager()
        self.all_candidate_struct = [CandidateStruct() for _ in range(MAX_NUM_PLAYERS)]
        self.submit_candidate_struct = CandidateStruct()
        self.all_player_struct = [PlayerStruct() for _ in range(MAX_NUM_PLAYERS)]
        self.submit_player_struct = PlayerStruct()
        self.all_game_option_struct = [GameOptionStruct() for _ in range(MAX_NUM_PLAYERS)]
        self.global_control_game_struct = GameOptionStruct()
        self.submit_game_option_struct = GameOptionStruct()
        self.global_control_game_struct.Following = True
        self.global_control_game_struct.Avoidance = True
        self.global_control_game_struct.Looting = True
        self.global_control_game_struct.Targeting = True
        self.global_control_game_struct.Combat = True
        self.global_control_game_struct.WindowVisible = True
        
        for i in range(NUMBER_OF_SKILLS):
            self.global_control_game_struct.Skills[i].Active = True


class HeroAI_Window_varsClass:
    global MODULE_NAME
    def __init__(self):
        self.main_window = ImGui.WindowModule(MODULE_NAME, "HeroAI", window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
        self.control_window = ImGui.WindowModule(MODULE_NAME, "HeroAI - Control Panel", window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
        self.tools_window = ImGui.WindowModule(MODULE_NAME, "Multibox Tools", window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)

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

capture_flag_all = False
capture_hero_flag = False
capture_hero_index = 0
capture_mouse_timer = Timer()

option_show_floating_targets = True
