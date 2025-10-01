from Py4GWCoreLib import *
import PyAgent
import os
import datetime
import time

module_name = "Farmer Hamnet Bot"

# Create log file with timestamp in current directory
log_filename = f"farmer_hamnet_bot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_filepath = log_filename

# Bot Configuration
class BotConfig:
    def __init__(self):
        self.target_town_id = 165  # Foible's Fair
        self.target_town_name = "Foible's Fair"
        self.target_explorable_id = 161  # Wizard's Folly
        self.target_explorable_name = "Wizard's Folly"
        self.exit_coordinates = (350, 7700)  # Exit point coordinates
        self.has_loaded = False  # Track if map has loaded
        self.after_loading_counter = 0.0
        self.run_count = 0  # Track number of farming runs completed

bot_config = BotConfig()

# Bot State
class BotState:
    def __init__(self):
        self.is_running = False
        self.current_step = "idle"
        self.movement_handler = Routines.Movement.FollowXY(tolerance=100)
        self.loading_start_time = 0.0  # Track when we start waiting for map loading (0.0 means not loading)
        self.travel_initiated = False  # Track if travel has been initiated to avoid spam
        self.combat_started = False  # Track if combat has started to avoid spam
        self.travel_start_time = 0.0  # Track when travel started (initialized to 0.0)

bot_state = BotState()

def write_to_log_file(level, message):
    """Write message to log file with timestamp"""
    try:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        with open(log_filepath, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception:
        pass  # Don't break the bot if logging fails

def log_info(message):
    """Log info messages to both console and file"""
    Py4GW.Console.Log(module_name, message, Py4GW.Console.MessageType.Info)
    write_to_log_file("INFO", message)

def log_success(message):
    """Log success messages to both console and file"""
    Py4GW.Console.Log(module_name, message, Py4GW.Console.MessageType.Success)
    write_to_log_file("SUCCESS", message)

def log_error(message):
    """Log error messages to both console and file"""
    Py4GW.Console.Log(module_name, message, Py4GW.Console.MessageType.Error)
    write_to_log_file("ERROR", message)

def is_in_town():
    """Check if we're in Foible's Fair"""
    try:
        current_map = Map.GetMapID()
        is_outpost = Map.IsOutpost()
        return current_map == bot_config.target_town_id and is_outpost
    except Exception:
        return False

def is_in_explorable():
    """Check if we're in an explorable area"""
    try:
        return Map.IsExplorable() and Map.IsMapReady()
    except Exception:
        return False

def is_in_wizards_folly():
    """Check if we're in Wizard's Folly (map ID 161)"""
    try:
        current_map = Map.GetMapID()
        return current_map == bot_config.target_explorable_id
    except Exception:
        return False
    
def find_item_by_name(item_name):
    bag_list = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)
    item_array = ItemArray.GetItemArray(bag_list)
    for item_id in item_array:
        agent_id = Item.GetAgentID(item_id)           
        current_name = Item.GetName(agent_id)
        if current_name == item_name:
            return item_id
    return 0

def PopImp():
    summoning_stone = ModelID.Igneous_Summoning_Stone.value
    stone_id = Item.GetItemIdFromModelID(summoning_stone)
    imp_effect_id = 2886
    has_effect = Effects.HasEffect(Player.GetAgentID(), imp_effect_id)

    imp_model_id = 513
    others = Party.GetOthers()
    cast_imp = True

    for other in others:
        if Agent.GetModelID(other) == imp_model_id:
            if not Agent.IsDead(other):
                cast_imp = False
            break

    if stone_id and not has_effect and cast_imp:
        Inventory.UseItem(stone_id)

def HasEnoughAdrenaline(skill_slot):
        skill_id = SkillBar.GetSkillIDBySlot(skill_slot)

        return SkillBar.GetSkillData(skill_slot).adrenaline_a >= Skill.Data.GetAdrenaline(skill_id)

def combat_phase():
    """Handle combat in Wizard's Folly - target enemies 15 and 16"""
    try:
        # Wait 5 seconds for map to fully load
        delta = time.time() - bot_config.after_loading_counter
        if not bot_config.has_loaded:
            bot_config.after_loading_counter = time.time()
            bot_config.has_loaded = True
            return None
        elif not bot_state.combat_started and delta < 5:
            return None
        if not bot_state.combat_started and delta >= 5:
            log_info("Combat phase started")
            bot_state.combat_started = True
            PopImp()

        # Get player position
        player_pos = Player.GetXY()
        
        target_enemies = []
        
        # Check if enemies 15 and 16 are valid and alive
        for agent_id in [15, 16]:
            if AgentArray.IsAgentIDValid(agent_id) and not Agent.IsDead(agent_id):
                target_enemies.append(agent_id)
                
        if not target_enemies:
            # Both enemies are dead - run complete
            bot_config.run_count += 1
            log_success(f"Run #{bot_config.run_count} completed")
            
            # Reset flags for next run
            bot_state.combat_started = False
            bot_config.has_loaded = False
            bot_config.after_loading_counter = 0.0
            bot_state.travel_initiated = False
            bot_state.current_step = "travel_to_town"
            return True
        
        # Select the first available target
        closest_enemy = target_enemies[0]
        
        if not closest_enemy:
            return None
        
        # Set target
        Player.ChangeTarget(closest_enemy)

        # Check if current target is dead before attacking
        if Agent.IsDead(closest_enemy):
            return None

        # Auto-attack
        if not Agent.IsAttacking(Player.GetAgentID()):
            Player.Interact(closest_enemy, False)
        
        # Use skills if available
        if HasEnoughAdrenaline(1) and Routines.Checks.Skills.CanCast():
            SkillBar.UseSkill(1, closest_enemy)

        if HasEnoughAdrenaline(2) and Routines.Checks.Skills.CanCast():
            SkillBar.UseSkill(2, closest_enemy)

        # Use skill 3 if within range
        enemy_pos = Agent.GetXY(closest_enemy)
        distance = ((player_pos[0] - enemy_pos[0]) ** 2 + (player_pos[1] - enemy_pos[1]) ** 2) ** 0.5
        if distance <= 900 and Routines.Checks.Skills.IsSkillSlotReady(3) and Routines.Checks.Skills.CanCast():
            SkillBar.UseSkill(3, closest_enemy)
        
        return None
        
    except Exception as e:
        log_error(f"Combat error: {str(e)}")
        bot_state.combat_started = False
        return False

def travel_to_town():
    """Travel to Foible's Fair"""
    try:
        current_map = Map.GetMapID()
        
        if current_map != bot_config.target_town_id:
            if not bot_state.travel_initiated:
                log_info(f"Traveling to {bot_config.target_town_name}")
                Map.Travel(bot_config.target_town_id)
                bot_state.travel_initiated = True
                bot_state.travel_start_time = time.time()
            else:
                # Check for timeout
                if hasattr(bot_state, 'travel_start_time'):
                    elapsed = time.time() - bot_state.travel_start_time
                    if elapsed > 15:
                        log_error(f"Travel timeout - retrying")
                        bot_state.travel_initiated = False
                        delattr(bot_state, 'travel_start_time')
                        return True
                else:
                    bot_state.travel_initiated = False
        else:
            bot_state.travel_initiated = False
            if hasattr(bot_state, 'travel_start_time'):
                delattr(bot_state, 'travel_start_time')
        return True
    except Exception as e:
        log_error(f"Travel error: {str(e)}")
        bot_state.travel_initiated = False
        if hasattr(bot_state, 'travel_start_time'):
            delattr(bot_state, 'travel_start_time')
        return False

def walk_to_exit():
    """Walk to the exit coordinates"""
    try:
        if is_in_explorable():
            log_success("Reached explorable area")
            return True
        
        if not bot_state.movement_handler.is_following():
            log_info("Moving to exit")
            bot_state.movement_handler.move_to_waypoint(
                bot_config.exit_coordinates[0],
                bot_config.exit_coordinates[1],
                tolerance=100
            )
        else:
            bot_state.movement_handler.update(log_actions=False)
            
            if bot_state.movement_handler.has_arrived():
                pass  # Wait for zone transition silently
        
        return None
        
    except Exception as e:
        log_error(f"Walk error: {str(e)}")
        return False

def reset_bot_state():
    """Reset all bot state variables to initial values"""
    bot_state.is_running = False
    bot_state.current_step = "idle"
    bot_state.loading_start_time = 0.0
    bot_state.travel_initiated = False
    bot_state.combat_started = False
    if hasattr(bot_state, 'travel_start_time'):
        delattr(bot_state, 'travel_start_time')
    bot_config.has_loaded = False
    bot_config.after_loading_counter = 0.0
    bot_state.movement_handler = Routines.Movement.FollowXY(tolerance=100)

def start_bot():
    """Start the bot"""
    if not bot_state.is_running:
        reset_bot_state()
        bot_config.run_count = 0
        log_info("Bot started")
        bot_state.is_running = True
        bot_state.current_step = "travel_to_town"

def stop_bot():
    """Stop the bot"""
    if bot_state.is_running:
        log_info("Bot stopped")
        reset_bot_state()

def PerformTask():
    """Main bot logic"""
    if not bot_state.is_running:
        return "Bot is idle"
    
    try:
        # Step 1: Travel to town
        if bot_state.current_step == "travel_to_town":
            if is_in_town():
                if bot_state.travel_initiated:
                    log_success("Arrived at town")
                bot_state.travel_initiated = False
                bot_state.current_step = "walk_to_exit"
            else:
                if not travel_to_town():
                    log_error("Travel failed")
                    stop_bot()
                    return "Travel failed"
                    
        # Step 2: Walk to exit
        elif bot_state.current_step == "walk_to_exit":
            if is_in_town():
                result = walk_to_exit()
                if result is True:
                    log_success("Reached explorable area")
                    stop_bot()
                    return "Success"
                elif result is False:
                    log_error("Exit walk failed")
                    stop_bot()
                    return "Walk failed"
            else:
                bot_state.current_step = "combat"
                
        # Step 3: Combat
        elif bot_state.current_step == "combat":
            current_map = Map.GetMapID()
            
            # Handle map loading
            if current_map == 0:
                if bot_state.loading_start_time == 0.0:
                    bot_state.loading_start_time = time.time()
                    log_info("Map loading...")
                    return f"Running - {bot_state.current_step} (loading)"
                else:
                    elapsed = time.time() - bot_state.loading_start_time
                    if elapsed >= 10.0:
                        bot_state.loading_start_time = 0.0
                        new_map = Map.GetMapID()
                        if new_map == bot_config.target_explorable_id:
                            log_success("Map loaded")
                        elif new_map == 0:
                            bot_state.loading_start_time = time.time()
                            return f"Running - {bot_state.current_step} (still loading)"
                        else:
                            log_error(f"Wrong map: {new_map}")
                            bot_state.current_step = "travel_to_town"
                            return f"Running - {bot_state.current_step}"
                    else:
                        return f"Running - {bot_state.current_step} (loading {elapsed:.1f}s)"
            
            if current_map != 0:
                bot_state.loading_start_time = 0.0
            
            if current_map != 0:
                if is_in_wizards_folly():
                    result = combat_phase()
                    if result is True:
                        return "Combat completed"
                    elif result is False:
                        log_error("Combat failed")
                        stop_bot()
                        return "Combat error"
                else:
                    log_error(f"Wrong area: map {current_map}")
                    bot_state.current_step = "travel_to_town"
        
        return f"Running - {bot_state.current_step}"
        
    except Exception as e:
        log_error(f"Bot error: {str(e)}")
        stop_bot()
        return "Error"

def main():
    """Main function - entry point for the script"""
    try:
        # Create ImGui window for bot control
        if ImGui.gw_window.begin(name="Simple Farming Bot",
                                pos=(100, 100),
                                size=(300, 250),
                                collapsed=False):
            
            # Bot Title
            PyImGui.text("Simple Farming Bot")
            PyImGui.separator()
            
            # Target Info
            PyImGui.text(f"Target: {bot_config.target_town_name}")
            PyImGui.text(f"Exit Point: {bot_config.exit_coordinates}")
            PyImGui.text(f"Runs Completed: {bot_config.run_count}")
            
            PyImGui.separator()
            
            # Control Buttons
            PyImGui.text("Controls:")
            PyImGui.spacing()
            
            # Start Button
            start_color = Color(0, 150, 0, 255).to_tuple() if not bot_state.is_running else Color(100, 100, 100, 255).to_tuple()
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, start_color)
            if PyImGui.button("START", 100, 30):
                start_bot()
            PyImGui.pop_style_color(1)
            
            PyImGui.same_line(110.0, 10.0)
            
            # Stop Button
            stop_color = Color(150, 0, 0, 255).to_tuple() if bot_state.is_running else Color(100, 100, 100, 255).to_tuple()
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, stop_color)
            if PyImGui.button("STOP", 100, 30):
                stop_bot()
            PyImGui.pop_style_color(1)
            
            PyImGui.separator()
            
            # Status Display
            PyImGui.text("Status:")
            status_color = Color(0, 255, 0, 255).to_tuple() if bot_state.is_running else Color(255, 255, 255, 255).to_tuple()
            PyImGui.text_colored(f"{'RUNNING' if bot_state.is_running else 'IDLE'}", status_color)
            PyImGui.text(f"Step: {bot_state.current_step}")
            
            PyImGui.separator()
            
        ImGui.gw_window.end("Simple Farming Bot")
        
        # Run bot logic
        if bot_state.is_running:
            PerformTask()
            
    except Exception as e:
        log_error(f"Main error: {str(e)}")

# Entry point
if __name__ == "__main__":
    main()
