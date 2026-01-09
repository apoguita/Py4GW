import threading
import time
from queue import Queue
import PyInventory
from Py4GWCoreLib import PyImGui as ImGui_Py
from Py4GWCoreLib import Py4GW as Py4GWCoreLib
from Py4GWCoreLib import Routines
from Py4GWCoreLib import *

module_name = "FoW_Bot"

# ---------------------------------------------
# Constants and Global Variables
# ---------------------------------------------

TOA_ID = 138  # Temple of Ages
FOW_ID = 34   # Fissure of Woe

# Thread control and management
bot_running = threading.Event()
threads = {}

# Shared resource lock
resource_lock = threading.Lock()

# Skill IDs and state
skill_ids_initialized = False
skill_ids = {
    "shroud_of_distress": None,
    "shadow_form": None,
    "dwarven_stability": None,
    "whirling_defense": None,
    "heart_of_shadow": None,
    "iau": None,
    "dark_escape": None,
    "mental_block": None,
}

# Global counters
shard_count = 0
wins = 0
fails = 0

# Initialize Py4GW components
party_instance = PyParty.PyParty()
map_instance = PyMap.PyMap()
inventory_instance = Inventory.inventory_instance()
player_instance = PyPlayer.PyPlayer()
skillbar_instance = PySkillbar.Skillbar()

# ---------------------------------------------
# Initialization Functions
# ---------------------------------------------

def assign_skill_ids():
    global skill_ids_initialized, skillbar_instance
    Py4GWCoreLib.Console.Log(module_name, "Starting skill assignment.", Py4GWCoreLib.Console.MessageType.Info)

    expected_skills = {
        "shroud_of_distress": "Shroud of Distress",
        "shadow_form": "Shadow Form",
        "dwarven_stability": "Dwarven Stability",
        "whirling_defense": "Whirling Defense",
        "heart_of_shadow": "Heart of Shadow",
        "iau": "I Am Unstoppable!",
        "dark_escape": "Dark Escape",
        "mental_block": "Mental Block",
    }

    missing_skills = []

    for slot, (skill_key, expected_name) in enumerate(expected_skills.items(), start=1):
        skill = skillbar_instance.GetSkill(slot)
        if skill and skill.id:
            skill_name = skill.id.GetName().replace("_", " ").replace("!", "").strip().lower()
            expected_name_normalized = expected_name.replace("_", " ").replace("!", "").strip().lower()

            if skill_name == expected_name_normalized:
                skill_ids[skill_key] = skill.id.id
            else:
                skill_ids[skill_key] = None
                missing_skills.append((slot, expected_name, skill.id.GetName()))
        else:
            skill_ids[skill_key] = None
            missing_skills.append((slot, expected_name, "None"))

    if missing_skills:
        for slot, expected_name, found_name in missing_skills:
            Py4GWCoreLib.Console.Log(
                module_name,
                f"Slot {slot}: Expected '{expected_name}', but found '{found_name}'.",
                Py4GWCoreLib.Console.MessageType.Warning,
            )
   
    skill_ids_initialized = True
    Py4GWCoreLib.Console.Log(module_name, "Skill assignment complete.", Py4GWCoreLib.Console.MessageType.Info)

def load_fow_skill_template():
    Py4GWCoreLib.Console.Log(module_name, "Loading skill template.", Py4GWCoreLib.Console.MessageType.Info)
    skill_template = "OgcTc5+8Z6ASn5uU4ABimsBKuEA"
    #skillbar_instance.LoadSkillTemplate(skill_template)
    SkillBar.LoadSkillTemplate(skill_template)
    Py4GWCoreLib.Console.Log(
        module_name,
        f"Skill template loaded: {skill_template}",
        Py4GWCoreLib.Console.MessageType.Info,
    )

# ---------------------------------------------
# Core Functions with Shared Lock
# ---------------------------------------------

def CastSkill(skill_id):
    with resource_lock:
        skill_slot = next((slot for slot, sid in enumerate(skill_ids.values(), start=1) if sid == skill_id), None)
        if skill_slot is None:
            Py4GWCoreLib.Console.Log(module_name, f"Skill ID {skill_id} not found.", Py4GWCoreLib.Console.MessageType.Warning)
            return

        #skillbar_instance.UseSkill(skill_slot, -2)  # -2 for self-targeting
        SkillBar.UseSkill(skill_slot)
        aftercast_duration = Py4GWCoreLib.Aftercast.GetAftercast(skill_id)
        threading.Timer(aftercast_duration / 1000, lambda: None).start()

def maintain_effects():
    with resource_lock:
        if not player_instance.HasEffect(skill_ids['shadow_form']):
            CastSkill(skill_ids['shadow_form'])
        if not player_instance.HasEffect(skill_ids['deadly_paradox']):
            CastSkill(skill_ids['deadly_paradox'])

# ---------------------------------------------
# Threaded Functions for Core Tasks
# ---------------------------------------------

def movement(path_points):
    follow_handler = Routines.Movement.FollowPath(path_points)
    while bot_running.is_set():
        if not follow_handler.IsRunning():
            break
        maintain_effects()
        time.sleep(0.2)

def combat():
    while bot_running.is_set():
        target_agent = player_instance.GetNearestEnemy()
        if target_agent and target_agent.is_alive:
            for skill_key in ["whirling_defense", "heart_of_shadow", "iau", "dark_escape", "mental_block"]:
                skill_id = skill_ids.get(skill_key)
                if skill_id:
                    CastSkill(skill_id)
        time.sleep(0.1)

def effects():
    while bot_running.is_set():
        maintain_effects()
        time.sleep(0.3)

def gui():
    while bot_running.is_set():
        draw_window()
        time.sleep(0.05)

# ---------------------------------------------
# Bot Control Functions
# ---------------------------------------------

def start_thread(name, target, *args):
    if name in threads and threads[name].is_alive():
        return
    thread = threading.Thread(target=target, args=args, daemon=True)
    threads[name] = thread
    thread.start()

def stop_all_threads():
    bot_running.clear()
    for thread in threads.values():
        if thread.is_alive():
            thread.join(timeout=2)
    threads.clear()

def start_bot():
    bot_running.set()
    Py4GWCoreLib.Console.Log(module_name, "Bot started.", Py4GWCoreLib.Console.MessageType.Info)
    start_thread("movement", movement, [(-21131, -2390)])
    start_thread("combat", combat)
    start_thread("effects", effects)
    start_thread("gui", gui)

def stop_bot():
    Py4GWCoreLib.Console.Log(module_name, "Stopping bot...", Py4GWCoreLib.Console.MessageType.Info)
    stop_all_threads()

# ---------------------------------------------
# GUI Management
# ---------------------------------------------

def draw_window():
    if ImGui_Py.begin(module_name):
        if ImGui_Py.button("Assign Skillbar"):
            load_fow_skill_template()
        if ImGui_Py.button("Start Bot"):
            start_bot()
        if ImGui_Py.button("Stop Bot"):
            stop_bot()
        ImGui_Py.text(f"Bot Running: {'Yes' if bot_running.is_set() else 'No'}")
        ImGui_Py.text(f"Shards Collected: {shard_count}")
        ImGui_Py.text(f"Wins: {wins}")
        ImGui_Py.text(f"Fails: {fails}")
    ImGui_Py.end()

# ---------------------------------------------
# Main Entry Point
# ---------------------------------------------

def main():
    global skill_ids_initialized
    try:
        if not skill_ids_initialized:
            load_fow_skill_template()
            assign_skill_ids()
            
        draw_window()
    except:
        stop_bot()
