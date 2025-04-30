from Py4GWCoreLib import *

module_name = "PetHelper"

# Behavior Type IntEnum
class BehaviorType(IntEnum):
    Fight = 0
    Guard = 1
    Heel = 2

# Pet class
class PetHelperPet:
    def __init__(self):
        self.data = {}
        self.name = ""

# Player class
class PetHelperPlayer:
    def __init__(self):
        self.own_id = 0
        self.name = ""
        self.target_id = 0

# Config class
class config:
    def __init__(self):
        self.is_map_loading = False         # If Map is Loading
        self.is_map_ready = False           # If Map is Ready
        self.is_party_loaded = False        # If Party is Loaded
        self.is_explorable = False          # If Map is Explorable
        self.map_valid = False              # If Map is Valid

        self.pet_exists = False             # If there is a Player Pet
        self.enemies_in_range = False       # If there is enemies in range (1300.0)
        self.behavior_fight_issued = False  # If Player have issued a Fight order
        self.behavior_fight_acted = False   # If Pet have responded to the Fight order
        self.behavior_guard_issued = False  # If Player have issued a Guard order
        self.behavior_guard_acted = False   # If Pet have responded to the Guard order

        self.game_throttle_time = 100       # Time between Updates
        self.game_throttle_timer = Timer()  # Timer for Time between Updates
        self.game_throttle_timer.Start()    # Starting the Timer for Time between Updates
        self.behavior_timer = Timer()       # Timer for Telling the time between issuing an order and it's responded to

        # Log config
        self.log_fight_issued = True        # Log Player have issued a Fight order
        self.log_guard_issued = True        # Log Player have issued a Guard order
        self.log_map = True
        self.log_heel = True

        # Debug config:
        self.log_all_actions = False        # Log all actions
        self.log_fight_acted = False        # Log Pet have responded to the Fight order
        self.log_guard_acted = False        # Log Pet have responded to the Guard order

# Functions
def configure():
    pass

def PetSetBehavior(behavior):
    global widget_config, player, pet
    
    if behavior == BehaviorType.Fight:
        if pet.data.behavior == BehaviorType.Heel:
            if widget_config.log_heel:
                widget_config.log_heel = False
                Py4GW.Console.Log(module_name, f"Warning Pet is set to Heel", Py4GW.Console.MessageType.Warning)
                Py4GW.Console.Log(module_name, f"{module_name} Temporarily Disabled!", Py4GW.Console.MessageType.Warning)
                Py4GW.Console.Log(module_name, f"Set Pet to Guard to Enable {module_name} again.", Py4GW.Console.MessageType.Warning)
            return

    if behavior == BehaviorType.Fight:
        if pet.data.locked_target_id != player.target_id or pet.data.behavior == BehaviorType.Guard:
            if not widget_config.behavior_fight_issued:
                if not widget_config.behavior_fight_issued: widget_config.behavior_fight_issued = True
                if widget_config.behavior_fight_acted: widget_config.behavior_fight_acted = False
                Party.Pets.SetPetBehavior(BehaviorType.Fight, player.target_id)
                if widget_config.behavior_timer.IsStopped(): widget_config.behavior_timer.Start()
                if widget_config.log_all_actions or widget_config.log_fight_issued:
                    Py4GW.Console.Log(module_name, f"{pet.name} ordered to fight {agent_array.get_name(player.target_id)} ({player.target_id})", Py4GW.Console.MessageType.Info)

    if behavior == BehaviorType.Guard:
        if pet.data.behavior == BehaviorType.Fight:
            if not widget_config.behavior_guard_issued:
                if not widget_config.behavior_guard_issued: widget_config.behavior_guard_issued = True
                if widget_config.behavior_guard_acted: widget_config.behavior_guard_acted = False
                Party.Pets.SetPetBehavior(BehaviorType.Guard, player.own_id)
                if widget_config.behavior_timer.IsStopped(): widget_config.behavior_timer.Start()
                if widget_config.log_all_actions or widget_config.log_guard_issued:
                    Py4GW.Console.Log(module_name, f"{pet.name} ordered to guard {player.name}", Py4GW.Console.MessageType.Info)

def LogPetReactionTime(behavior):
    global widget_config, player, pet

    if behavior == BehaviorType.Fight:
        if pet.data.locked_target_id == player.target_id and pet.data.behavior == BehaviorType.Fight:
            if not widget_config.behavior_fight_acted:
                if not widget_config.behavior_fight_acted: widget_config.behavior_fight_acted = True
                if widget_config.behavior_fight_issued: widget_config.behavior_fight_issued = False
                if not widget_config.behavior_timer.IsStopped(): widget_config.behavior_timer.Stop()
                if widget_config.log_all_actions or widget_config.log_fight_acted:
                    Py4GW.Console.Log(module_name, f"{pet.name} fight {agent_array.get_name(player.target_id)} ({player.target_id}) after ({round(widget_config.behavior_timer.GetElapsedTime(),2)})", Py4GW.Console.MessageType.Info)

    if behavior == BehaviorType.Guard:
        if pet.data.behavior == BehaviorType.Guard:
            if not widget_config.behavior_guard_acted:
                if not widget_config.behavior_guard_acted: widget_config.behavior_guard_acted = True
                if not widget_config.behavior_guard_issued: widget_config.behavior_guard_issued = False
                if not widget_config.behavior_timer.IsStopped(): widget_config.behavior_timer.Stop()
                if widget_config.log_all_actions or widget_config.log_guard_acted:
                    Py4GW.Console.Log(module_name, f"{pet.name} guard {player.name} after ({round(widget_config.behavior_timer.GetElapsedTime(),2)})", Py4GW.Console.MessageType.Info)

def IsEnemyTarget(target_id):
    _, target_aliegance = Agent.GetAllegiance(target_id)
    if (target_aliegance == 'Enemy') and Agent.IsAlive(target_id) and (Agent.GetHealth(target_id) * Agent.GetMaxHealth(target_id) > 1):
        return True
    return False

# Initiation of class's
widget_config = config()
agent_array = RawAgentArray()
pet = PetHelperPet()
player = PetHelperPlayer()

# main Function
def main():
    global widget_config, pet, player
    if widget_config.game_throttle_timer.HasElapsed(widget_config.game_throttle_time):
        widget_config.is_map_loading = Map.IsMapLoading()
        if widget_config.is_map_loading:
            """ Reset variables """
            if pet.name != "": pet.name = ""
            if player.name != "": player.name = ""
            if widget_config.pet_exists: widget_config.pet_exists = False
            if widget_config.enemies_in_range: widget_config.enemies_in_range = False
            if widget_config.behavior_fight_issued: widget_config.behavior_fight_issued = False
            if widget_config.behavior_fight_acted: widget_config.behavior_fight_acted = False
            if widget_config.behavior_guard_issued: widget_config.behavior_guard_issued = False
            if widget_config.behavior_guard_acted: widget_config.behavior_guard_acted = False
            if widget_config.log_map == False: widget_config.log_map = True
            if widget_config.log_heel == False: widget_config.log_heel = True
            return

        widget_config.is_map_ready = Map.IsMapReady()
        widget_config.is_party_loaded = Party.IsPartyLoaded()
        widget_config.is_explorable = Map.IsExplorable()
        widget_config.map_valid = widget_config.is_map_ready and widget_config.is_party_loaded and widget_config.is_explorable

        if widget_config.map_valid:
            player.own_id = Player.GetAgentID()
            if Agent.IsValid(Party.Pets.GetPetID(player.own_id)):
                if widget_config.pet_exists == False: widget_config.pet_exists = True

            else:
                if widget_config.pet_exists == True: widget_config.pet_exists = False
                
            if widget_config.pet_exists:
                if Routines.Agents.GetNearestEnemy(1300.0) > 0: # 1300.0
                    if widget_config.enemies_in_range == False: widget_config.enemies_in_range = True

                else:
                    if widget_config.enemies_in_range == True: widget_config.enemies_in_range = False
                    
        widget_config.game_throttle_timer.Start()

    if widget_config.map_valid and widget_config.pet_exists:
        if widget_config.log_map:
            widget_config.log_map = False
            Py4GW.Console.Log(module_name, f"Is Enabled", Py4GW.Console.MessageType.Success)

        pet.data = Party.Pets.GetPetInfo(player.own_id)
        agent_array.update()
        if pet.name == "": pet.name = agent_array.get_name(pet.data.agent_id).replace("Pet - ", "")

        if player.name == "": player.name = agent_array.get_name(player.own_id)

        if widget_config.enemies_in_range:
            player.target_id = Player.GetTargetID()
            if player.target_id != 0:
                if IsEnemyTarget(player.target_id):
                    PetSetBehavior(BehaviorType.Fight)
                    LogPetReactionTime(BehaviorType.Fight)

            """
            Disabled no need to order to guard if enemies in range
                else:
                    widget_config.behavior_fight_issued = False
                    widget_config.behavior_fight_acted = False
                    PetSetBehavior(BehaviorType.Guard)
                    LogPetReactionTime(BehaviorType.Guard)

            else:
                widget_config.behavior_fight_issued = False
                widget_config.behavior_fight_acted = False
                PetSetBehavior(BehaviorType.Guard)
                LogPetReactionTime(BehaviorType.Guard)
            """

        else:
            if not widget_config.log_heel: widget_config.log_heel = True
            if widget_config.behavior_fight_issued: widget_config.behavior_fight_issued = False
            if widget_config.behavior_fight_acted: widget_config.behavior_fight_acted = False
            PetSetBehavior(BehaviorType.Guard)
            LogPetReactionTime(BehaviorType.Guard)

if __name__ == "__main__":
    main()