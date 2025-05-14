from Py4GWCoreLib import *
import os

module_name = "Survival Title Helper"

script_directory = os.path.dirname(os.path.abspath(__file__))
root_directory = os.path.normpath(os.path.join(script_directory, ".."))
ini_file_location = os.path.join(root_directory, "Widgets/Config/Survival Title Helper.ini")

ini_handler = IniHandler(ini_file_location)
sync_timer = Timer()
sync_timer.Start()
sync_interval = 1000

class Global_Vars:
    def __init__(self):
        self.lvl1_10_threshold = 50           # lvl 1 - 10 threshold
        self.lvl11_20_threshold = 120         # lvl 11 - 20 threshold
        self.current_threhold = 50            # currrent treshold
        self.default_max_health_table = {
            1: 100,
            2: 120,
            3: 140,
            4: 160,
            5: 180,
            6: 200,
            7: 220,
            8: 240,
            9: 260,
            10: 280,
            11: 300,
            12: 320,
            13: 340,
            14: 360,
            15: 380,
            16: 400,
            17: 420,
            18: 440,
            19: 460,
            20: 480,    # Maybe this should be set to 550 +50 health rune, but pre-searing it's 480 (510 with health rune)
        }
        self.players_max_health_table:dict[int, float] = {}
        self.party_leader_name:dict[int, str] = {}
        self.is_party_leader = False
        self.reform_party = False
        self.party_names:dict[int, str] = {}
        self.last_outpost = 0

        self.low_life = False
        self.low_life_agent = 0
        self.log_low_health = True

        self.game_time = 100                  # Time between Updates
        self.game_timer = Timer()             # Timer for Time between Updates
        self.game_timer.Start()               # Starting the Timer for Time between Updates

        self.travel_time = 4000               # Time between Updates
        self.travel_timer = Timer()           # Timer for Time between Updates
        self.travel_timer.Start()             # Starting the Timer for Time between Updates

    def reset_vars(self):
        if self.low_life:
            self.low_life = False
        if self.low_life_agent != 0:
            self.low_life_agent = 0
        if len(self.players_max_health_table) > 0:
            self.players_max_health_table = {}
        if self.log_low_health == False:
            self.log_low_health = True


global_vars = Global_Vars()

def update_max_health():
    global global_vars
    players = Party.GetPlayers()
    for player in players:
        agent_id = Party.Players.GetAgentIDByLoginNumber(player.login_number)
        agent_max_health = Agent.GetMaxHealth(agent_id)
        current_health = Agent.GetHealth(agent_id)

        if 0.0 < current_health <= 1 and agent_max_health > 0.0:
            if global_vars.players_max_health_table.get(agent_id, Player.GetAgentID()) != agent_max_health:
                global_vars.players_max_health_table[agent_id] = agent_max_health

def update_party_names():
    global global_vars
    players = Party.GetPlayers()
    for player in players:
        agent_id = Party.Players.GetAgentIDByLoginNumber(player.login_number)
        name = agent_array.get_name(agent_id)
        if name != "":
            if agent_id == Party.GetPartyLeaderID():
                if global_vars.party_leader_name.get(agent_id, Player.GetAgentID()) != name:
                    global_vars.party_leader_name[agent_id] = name
                    #Py4GW.Console.Log(module_name, f"Set Party Leader: {name}", Py4GW.Console.MessageType.Info)
            else:
                if global_vars.party_names.get(agent_id, Player.GetAgentID()) != name:
                    global_vars.party_names[agent_id] = name
                    #Py4GW.Console.Log(module_name, f"Added Player: {name} to Party", Py4GW.Console.MessageType.Info)

def get_max_health(agent_id:int):
    global global_vars
    level = Agent.GetLevel(agent_id)
    default = global_vars.default_max_health_table.get(level, 1)
    max_health = global_vars.players_max_health_table.get(agent_id, default)
    return max_health

def get_threshold(agent_id:int):
    global global_vars
    level = Agent.GetLevel(agent_id)
    if 1 <= level <= 10:
        global_vars.current_threhold = global_vars.lvl1_10_threshold

    elif 11 <= level <= 20:
        global_vars.current_threhold = global_vars.lvl11_20_threshold
    
    health_treshold = 1 / (get_max_health(agent_id) / global_vars.current_threhold)
    return health_treshold


def reformparty():
    global global_vars
    if not len(Party.GetPlayers()) > 1:
        for agent_id in global_vars.party_names:
            name = global_vars.party_names.get(agent_id, "")
            ActionQueueManager().AddAction("ACTION", Party.Players.InvitePlayer, name)
#            Party.Players.InvitePlayer(name)
        global_vars.reform_party = False

def acceptparty():
    global global_vars
    party_leader_name = ""
    if not len(Party.GetPlayers()) > 1:
        for agent_id in global_vars.party_leader_name:
            party_leader_name = global_vars.party_leader_name.get(agent_id, "")
            ActionQueueManager().AddAction("ACTION", Party.Players.InvitePlayer, party_leader_name)
#            Party.Players.InvitePlayer(name)
            global_vars.reform_party = False

class Config:
    global ini_handler, module_name, sync_timer, sync_interval, global_vars
    def __init__(self):
        """Read configuration values from INI file"""
        self.lvl1_10 = ini_handler.read_int(module_name, "lvl1_10", global_vars.lvl1_10_threshold)
        if global_vars.lvl1_10_threshold != self.lvl1_10:
            global_vars.lvl1_10_threshold = self.lvl1_10
        self.lvl11_20 = ini_handler.read_int(module_name, "lvl11_20", global_vars.lvl11_20_threshold)
        if global_vars.lvl11_20_threshold != self.lvl11_20:
            global_vars.lvl11_20_threshold = self.lvl11_20

    def save(self):
        """Save the current configuration to the INI file."""
        if sync_timer.HasElapsed(sync_interval):
            ini_handler.write_key(module_name, "lvl1_10", str(self.lvl1_10))
            ini_handler.write_key(module_name, "lvl11_20", str(self.lvl11_20))
            sync_timer.Start()

widget_config = Config()

agent_array = RawAgentArray()

config_module = ImGui.WindowModule(f"{module_name} Config", window_name=f"{module_name} Config##{module_name}", window_size=(100, 100), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
window_x = ini_handler.read_int(module_name + " Config", "config_x", 100)
window_y = ini_handler.read_int(module_name + " Config", "config_y", 100)

config_module.window_pos = (window_x, window_y)

def configure():
    global widget_config, config_module, ini_handler, global_vars
    try:
        if not Routines.Checks.Map.MapValid():
            global_vars.reset_vars()
            return
        
        if config_module.first_run:
            PyImGui.set_next_window_size(config_module.window_size[0], config_module.window_size[1])
            PyImGui.set_next_window_pos(config_module.window_pos[0], config_module.window_pos[1])
            config_module.first_run = False

        end_pos = config_module.window_pos
        if PyImGui.begin(config_module.window_name, config_module.window_flags):
    #        new_collapsed = PyImGui.is_window_collapsed()
            PyImGui.text_wrapped(f"         {module_name}:")
            PyImGui.text_wrapped("if any of your player party members")
            PyImGui.text_wrapped("          goes below threshold:")
            if 1 <= Agent.GetLevel(Player.GetAgentID()) <= 10:
                PyImGui.text_colored(f"lvl: 1-10 = {global_vars.lvl1_10_threshold}", (0.143, 0.724, 0.017, 1.000))
            else:
                PyImGui.text_wrapped(f"lvl: 1-10 = {global_vars.lvl1_10_threshold}")
            PyImGui.same_line(100, -1.0)
            PyImGui.text_wrapped("or")
            PyImGui.same_line(120, -1.0)
            if 11 <= Agent.GetLevel(Player.GetAgentID()) <= 20:
                PyImGui.text_colored(f"lvl: 11-20 = {global_vars.lvl11_20_threshold}", (0.143, 0.724, 0.017, 1.000))
            else:
                PyImGui.text_wrapped(f"lvl: 11-20 = {global_vars.lvl11_20_threshold}")

            PyImGui.text_wrapped("    it'll Map Travel to last Outpost,")
            PyImGui.text_wrapped("    you can set the threshold below.")
            PyImGui.text_wrapped("                 If in a Party,")
            PyImGui.text_wrapped("  It'll also reform your player party")
            PyImGui.text_wrapped("            once in the Outpost")
            PyImGui.text_wrapped("    Current character lvl threshold")
            PyImGui.text_wrapped("        is highlighted with")
            PyImGui.same_line(157, -1.0)
            PyImGui.text_colored("green", (0.143, 0.724, 0.017, 1.000))
            if 1 <= Agent.GetLevel(Player.GetAgentID()) <= 10:
                PyImGui.text_colored("                  Level 1 - 10:", (0.143, 0.724, 0.017, 1.000))
            else:
                PyImGui.text_wrapped("                  Level 1 - 10:")
            widget_config.lvl1_10 = PyImGui.slider_int("", widget_config.lvl1_10, 0, 330)
            PyImGui.text_wrapped("                       0 - 330")
            if global_vars.lvl1_10_threshold != widget_config.lvl1_10:
                global_vars.lvl1_10_threshold = widget_config.lvl1_10
            if 11 <= Agent.GetLevel(Player.GetAgentID()) <= 20:
                PyImGui.text_colored("                  Level 11 - 20:", (0.143, 0.724, 0.017, 1.000))
            else:
                PyImGui.text_wrapped("                  Level 11 - 20:")
            widget_config.lvl11_20 = PyImGui.slider_int("", widget_config.lvl11_20, 0, 550)
            PyImGui.text_wrapped("                       0 - 550")
            if global_vars.lvl11_20_threshold != widget_config.lvl11_20:
                global_vars.lvl11_20_threshold = widget_config.lvl11_20

            widget_config.save()
            end_pos = PyImGui.get_window_pos()

        PyImGui.end()

        if end_pos[0] != config_module.window_pos[0] or end_pos[1] != config_module.window_pos[1]:
            config_module.window_pos = (int(end_pos[0]), int(end_pos[1]))
            ini_handler.write_key(module_name + " Config", "config_x", str(int(end_pos[0])))
            ini_handler.write_key(module_name + " Config", "config_y", str(int(end_pos[1])))

    except ImportError as e:
        Py4GW.Console.Log(module_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(module_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(module_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass
    

# main Function
def main():
    global global_vars
    try:
        if not Routines.Checks.Map.MapValid():
            global_vars.reset_vars()
            return
        
        elif Map.IsOutpost():
            agent_array.update()
            if global_vars.last_outpost != Map.GetMapID():
                global_vars.last_outpost = Map.GetMapID()
                #Py4GW.Console.Log(module_name, f"Last Outpost: {Map.GetMapName(global_vars.last_outpost)}({Map.GetMapID()})", Py4GW.Console.MessageType.Info)
            #reform party
            if global_vars.reform_party:
                if global_vars.is_party_leader:
                    reformparty()
                else:
                    acceptparty()
            ActionQueueManager().ProcessQueue("ACTION")
            return

        elif Map.IsExplorable():
            agent_array.update()
            if global_vars.game_timer.HasElapsed(global_vars.game_time):
                if Party.IsPartyLeader() and not global_vars.is_party_leader:
                    global_vars.is_party_leader = True
                update_max_health()
                update_party_names()
                if global_vars.low_life:
                    global_vars.low_life = False
                players = Party.GetPlayers()
                for player in players:
                    agent_id = Party.Players.GetAgentIDByLoginNumber(player.login_number)
                    if 0.0 < Agent.GetHealth(agent_id) < 1.0:
                        health = Agent.GetHealth(agent_id)
                        max_health = get_max_health(agent_id)
                        if health <= get_threshold(agent_id):
                            if global_vars.log_low_health:
                                global_vars.log_low_health = False
                                Py4GW.Console.Log(module_name, f"Player: {agent_array.get_name(agent_id)} ({agent_id}) have low health: {round(health * max_health)}", Py4GW.Console.MessageType.Info)
                            global_vars.low_life = True
                            global_vars.low_life_agent = agent_id

                if global_vars.low_life:
                    if global_vars.travel_timer.HasElapsed(global_vars.travel_time):
                        if len(Party.GetPlayers()) > 1:
                            global_vars.reform_party = True
                        ActionQueueManager().AddAction("ACTION", Map.Travel, global_vars.last_outpost)
#                        Map.Travel(global_vars.last_outpost)
                        ActionQueueManager().AddAction("ACTION", Keystroke.PressAndRelease, Key.Y.value)
                        ActionQueueManager().AddAction("ACTION", Keystroke.PressAndRelease, Key.Y.value)
#                        Keystroke.PressAndRelease(Key.Y.value)
                        Py4GW.Console.Log(module_name, f"Traveling to: {Map.GetMapName(global_vars.last_outpost)}({global_vars.last_outpost})", Py4GW.Console.MessageType.Info)
                        global_vars.low_life = False
                        global_vars.travel_timer.Start()

                global_vars.game_timer.Start()
            ActionQueueManager().ProcessQueue("ACTION")
            return

    except ImportError as e:
        Py4GW.Console.Log(module_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(module_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(module_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass

if __name__ == "__main__":
    main()