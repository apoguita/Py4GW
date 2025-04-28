from Py4GWCoreLib import *

module_name = "PetHelper"

class config:
    def __init__(self):
        self.is_map_loading = False         # If Map is Loading
        self.is_map_ready = False           # If Map is Ready
        self.is_party_loaded = False        # If Party is Loaded
        self.is_explorable = False          # If Map is Explorable
        self.map_valid = False              # If Map is Valid

        self.pet_exists = False             # If there is a Player Pet
        self.enemies_in_range = False       # If there is enemies in range (1248.0)
        self.behavior_fight_issued = False  # If Player have issued a Fight order
        self.behavior_fight_acted = False   # If Pet have responded to the Fight order
        self.behavior_guard_issued = False  # If Player have issued a Guard order
        self.behavior_guard_acted = True    # If Pet have responded to the Guard order

        self.game_throttle_time = 1000      # Time between Updates
        self.game_throttle_timer = Timer()  # Timer for Time between Updates
        self.game_throttle_timer.Start()    # Starting the Timer for Time between Updates
        self.behavior_timer = Timer()       # Timer for Telling the time between issuing an order and it's responded to

        # Debug options:
        self.log_all_actions = False        # Log all actions
        self.log_fight_issued = False       # Log Player have issued a Fight order
        self.log_fight_acted = False        # Log Pet have responded to the Fight order
        self.log_guard_issued = False       # Log Player have issued a Guard order
        self.log_guard_acted = False        # Log Pet have responded to the Guard order

widget_config = config()

def configure():
    pass

class BehaviorType(IntEnum):
    Fight = 0
    Guard = 1
    Avoid = 2

class PetHelperPet:
    def __init__(self):
        self.data = {}

pet = PetHelperPet()

class PetHelperPlayer:
    def __init__(self):
        self.own_id = 0
        self.target_id = 0

player = PetHelperPlayer()

def PetSetBehavior(behavior):
    global widget_config, player, pet

    if behavior == BehaviorType.Fight:
        if pet.data.locked_target_id != player.target_id or pet.data.behavior == BehaviorType.Guard:
            if not widget_config.behavior_fight_issued:
                widget_config.behavior_fight_issued = True
                widget_config.behavior_fight_acted = False
                Party.Pets.SetPetBehavior(BehaviorType.Fight, player.target_id)
                if widget_config.behavior_timer.IsStopped():
                    widget_config.behavior_timer.Start()
                if widget_config.log_all_actions or widget_config.log_fight_issued:
                    Py4GW.Console.Log(module_name, f"Pet ordered to fight ({player.target_id})", Py4GW.Console.MessageType.Info)

    if behavior == BehaviorType.Guard:
        if pet.data.behavior == BehaviorType.Fight:
            if not widget_config.behavior_guard_issued:
                widget_config.behavior_guard_issued = True
                widget_config.behavior_guard_acted = False
                Party.Pets.SetPetBehavior(BehaviorType.Guard, 0)
                if widget_config.behavior_timer.IsStopped():
                    widget_config.behavior_timer.Start()
                if widget_config.log_all_actions or widget_config.log_guard_issued:
                    Py4GW.Console.Log(module_name, f"Pet ordered to guard player", Py4GW.Console.MessageType.Info)

def LogPetReactionTime(behavior):
    global widget_config, player, pet

    if behavior == BehaviorType.Fight:
        if pet.data.locked_target_id == player.target_id and pet.data.behavior == BehaviorType.Fight:
            if not widget_config.behavior_fight_acted:
                widget_config.behavior_fight_acted = True
                widget_config.behavior_fight_issued = False
                if not widget_config.behavior_timer.IsStopped():
                    widget_config.behavior_timer.Stop()
                if widget_config.log_all_actions or widget_config.log_fight_acted:
                    Py4GW.Console.Log(module_name, f"Pet fight ({player.target_id}) after ({round(widget_config.behavior_timer.GetElapsedTime(),2)})", Py4GW.Console.MessageType.Info)

    if behavior == BehaviorType.Guard:
        if pet.data.behavior == BehaviorType.Guard:
            if not widget_config.behavior_guard_acted:
                widget_config.behavior_guard_acted = True
                widget_config.behavior_guard_issued = False
                if not widget_config.behavior_timer.IsStopped():
                    widget_config.behavior_timer.Stop()
                if widget_config.log_all_actions or widget_config.log_guard_acted:
                    Py4GW.Console.Log(module_name, f"Pet guard player after ({round(widget_config.behavior_timer.GetElapsedTime(),2)})", Py4GW.Console.MessageType.Info)

def IsEnemyTarget(target_id):
    _, target_aliegance = Agent.GetAllegiance(target_id)
    if (target_aliegance != 'Enemy') or Agent.IsDead(target_id):
        return False
    return True

def main():
    global widget_config, pet, player
    if widget_config.game_throttle_timer.HasElapsed(widget_config.game_throttle_time):
        widget_config.is_map_loading = Map.IsMapLoading()
        if widget_config.is_map_loading:
            return

        widget_config.is_map_ready = Map.IsMapReady()
        widget_config.is_party_loaded = Party.IsPartyLoaded()
        widget_config.is_explorable = Map.IsExplorable()
        widget_config.map_valid = widget_config.is_map_ready and widget_config.is_party_loaded and widget_config.is_explorable

        if widget_config.map_valid:
            player.own_id = Player.GetAgentID()
            if Party.Pets.GetPetID(player.own_id) != 0:
                if widget_config.pet_exists == False:
                    widget_config.pet_exists = True
            else:
                if widget_config.pet_exists == True:
                    widget_config.pet_exists = False
                
            if widget_config.pet_exists:
                if Routines.Agents.GetNearestEnemy(Range.Spellcast.value) > 0: # 1248.0
                    if widget_config.enemies_in_range == False:
                        widget_config.enemies_in_range = True
                else:
                    if widget_config.enemies_in_range == True:
                        widget_config.enemies_in_range = False
                    
        widget_config.game_throttle_timer.Start()

    if widget_config.map_valid and widget_config.pet_exists:
        pet.data = Party.Pets.GetPetInfo(player.own_id)
        if widget_config.enemies_in_range:
            player.target_id = Player.GetTargetID()
            if player.target_id != 0:
                if IsEnemyTarget(player.target_id):
                    PetSetBehavior(BehaviorType.Fight)
                    LogPetReactionTime(BehaviorType.Fight)

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

        else:
            widget_config.behavior_fight_issued = False
            widget_config.behavior_fight_acted = False
            PetSetBehavior(BehaviorType.Guard)
            LogPetReactionTime(BehaviorType.Guard)

if __name__ == "__main__":
    main()