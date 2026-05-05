from typing import List, Tuple, Generator, Any, Optional, Dict
from dataclasses import dataclass
from enum import Enum
import time
import os
from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          AutoPathing, PyImGui, ActionQueueManager, Map, Agent, Player, Item,
                          IconsFontAwesome5, SkillBar, Quest, AgentArray, UIManager, Color)
from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
from Py4GWCoreLib.ImGui_src.ImGuisrc import ImGui
from Py4GWCoreLib.enums_src.Hero_enums import HeroType
from Py4GW import Game

BOT_NAME = "Elite Skills Capture"
MODULE_NAME = BOT_NAME
MODULE_ICON = "Textures\\Module_Icons\\elite_skills_capture.png"
MODULE_CATEGORY = "Helpers"
MODULE_TAGS = ["automation", "skills", "elite", "capture", "botting"]
MODULE_DESCRIPTION = "An advanced automation bot for capturing elite skills from bosses throughout Guild Wars.\n\nFeatures:\n• Automated pathing to elite skill bosses across all campaigns\n• Intelligent boss detection and engagement system\n• Automatic Signet of Capture usage for skill learning\n• Support for all 10 professions with 151+ elite skills\n• Color-coded skill availability (Blue/Available, Green/Captured, Red/Map Locked)\n• Smart map access checking and unlock requirements\n• Progress tracking and capture status monitoring\n• Built-in safety features and stuck detection\n\nCredits:\n• Originally developed by Kendor with help from Wick Divinus and Simfoniya\n• Adapted for Py4GW widget system by Kendor"

TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Widgets", "Automation", "Helpers", "Elite Skills", "elite_skills_capture.png")

def tooltip():
    PyImGui.begin_tooltip()
    
    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Elite Skills Capture", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    
    # Description
    PyImGui.text("An advanced automation bot for capturing elite skills from bosses throughout Guild Wars.")
    PyImGui.spacing()
    
    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Automated pathing to elite skill bosses across all campaigns")
    PyImGui.bullet_text("Automatic Signet of Capture usage for skill learning")
    PyImGui.bullet_text("Support for all 10 professions with 151+ elite skills")
    PyImGui.bullet_text("Color-coded skill availability system")
    PyImGui.bullet_text("Smart map access checking and unlock requirements")
    PyImGui.bullet_text("Progress tracking and capture status monitoring")

    
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()
    
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Originally developed by Kendor with help from Wick Divinus and Simfoniya")
    PyImGui.bullet_text("Adapted for Py4GW widget system by Kendor")
    
    PyImGui.end_tooltip()


# ============================================================================
#region SKILL CHECKING FUNCTIONS
# ============================================================================

def is_skill_unlocked(skill_id: int) -> bool:
    """Check if a skill is already unlocked for the current character."""
    unlocked_skills = Player.GetUnlockedCharacterSkills()
    
    # unlocked_skills is a list of bitmasks, so we need to check the bit for our skill_id
    bits_per_entry = 32
    entry_index = skill_id // bits_per_entry
    bit_position = skill_id % bits_per_entry
    
    if entry_index < len(unlocked_skills):
        skill_mask = unlocked_skills[entry_index]
        return (skill_mask >> bit_position) & 1 == 1
    
    return False

def can_learn_skill(skill_id: int) -> bool:
    """Check if a skill is learnable for the current character across all secondary professions."""
    # Since the character has access to all 9 secondary professions,
    # we should assume all elite skills are learnable unless they're already unlocked
    # This is much safer than trying to check learnable skills which only shows for current secondary
    return True

def can_access_skill_map(skill: 'EliteSkill') -> bool:
    """Check if the required map for skill capture is unlocked."""
    if skill.start_map <= 0:
        return True  # No map requirement
    
    try:
        return Map.IsMapUnlocked(skill.start_map)
    except:
        return True  # Assume unlocked if check fails

def should_skip_skill(skill_id: int) -> Tuple[bool, str]:
    """
    Check if a skill should be skipped during capture.
    Returns (should_skip, reason)
    """
    if is_skill_unlocked(skill_id):
        return True, f"Skill {skill_id} ({GLOBAL_CACHE.Skill.GetName(skill_id)}) already unlocked"
    
    if not can_learn_skill(skill_id):
        return True, f"Skill {skill_id} ({GLOBAL_CACHE.Skill.GetName(skill_id)}) not learnable for this character"
    
    # Find the skill to check map access
    skill = None
    for s in ELITE_SKILLS:
        if s.skill_id == skill_id:
            skill = s
            break
    
    if skill and not can_access_skill_map(skill):
        return True, f"Skill {skill_id} ({GLOBAL_CACHE.Skill.GetName(skill_id)}) map not accessible: {Map.GetMapName(skill.start_map)}"
    
    return False, ""

# ============================================================================
#region ICON HELPER FUNCTIONS
# ============================================================================

def find_py4gw_root(start_path: str) -> Optional[str]:
    """Find Py4GW root directory by looking for characteristic files/dirs."""
    current = os.path.abspath(start_path)
    
    while True:
        # Check for Py4GW characteristics
        py4gw_indicators = [
            "Py4GWCoreLib",
            "Widgets", 
            "Examples",
            "py4gw.exe",
            "Py4GW.py"
        ]
        
        if any(os.path.exists(os.path.join(current, indicator)) for indicator in py4gw_indicators):
            return current
        
        parent = os.path.dirname(current)
        if parent == current:  # Reached root
            break
        current = parent
    
    return None

def find_textures_directory(script_path: str) -> Optional[str]:
    """
    Find the directory containing Textures/Skill_Icons.
    Tries multiple strategies to locate the Py4GW root directory.
    """
    # Strategy 1: Walk up from script location
    result = find_py4gw_root(script_path)
    if result:
        return result
    
    # Strategy 2: Walk up from current working directory
    result = find_py4gw_root(os.getcwd())
    if result:
        return result
    
    # Strategy 3: Check sibling directories of script location
    script_dir = os.path.dirname(os.path.abspath(script_path))
    parent_dir = os.path.dirname(script_dir)
    
    if parent_dir:
        try:
            for sibling in os.listdir(parent_dir):
                if sibling.startswith('.'):
                    continue
                sibling_path = os.path.join(parent_dir, sibling)
                if os.path.isdir(sibling_path):
                    textures_path = os.path.join(sibling_path, "Textures", "Skill_Icons")
                    if os.path.isdir(textures_path):
                        return sibling_path
        except (OSError, PermissionError):
            pass
    
    return None
def _on_party_defeated(bot: Botting, step_name: str):
    """Party wiped: wait for rez, then resume from current position in map."""
    bot.Properties.ApplyNow("pause_on_danger", "active", False)
    bot.ResetHeroAICombatState(active=False, following=False, targeting=False, combat=False)
    ConsoleLog("Defeat", "Party defeated - waiting for resurrection...", log=True)
    
    # Wait for party to be resurrected (either by rez shrine or skills)
    while True:
        yield from Routines.Yield.wait(1000)
        if not Routines.Checks.Map.MapValid():
            continue
        # Check if player is alive
        player_id = Player.GetAgentID()
        if player_id and Agent.IsAlive(player_id):
            break
    
    ConsoleLog("Defeat", "Party resurrected - resuming capture...", log=True)
    fsm = bot.config.FSM
    
    # Resume from the current step without resetting
    fsm.resume()
    
    bot.Templates.Aggressive()
    bot.ResetHeroAICombatState(active=True)
    yield


def _get_mission_header_step(fsm):
    """Return the [H] header state name for the current state (so we restart the mission, not a sub-step)."""
    if not fsm.current_state or not fsm.states:
        return None
    try:
        idx = fsm.states.index(fsm.current_state)
    except ValueError:
        return None
    for i in range(idx, -1, -1):
        if fsm.states[i].name.startswith("[H]"):
            return fsm.states[i].name
    return None


def on_party_defeated(bot: Botting):
    fsm = bot.config.FSM
    current_step = _get_mission_header_step(fsm) or (fsm.current_state.name if fsm.current_state else "")
    ConsoleLog("PartyDefeated", "Party defeated. Returning to outpost and retrying current step...", log=True)
    ActionQueueManager().ResetAllQueues()
    fsm.pause()
    fsm.AddManagedCoroutine("OnPartyDefeated", _on_party_defeated(bot, current_step))

# ============================================================================
#region DATA MODEL - Elite Skills Definitions
# ============================================================================

class EliteSkillType(Enum):
    ELITE_SKILL = "elite_skill"

class Profession(Enum):
    WARRIOR = "Warrior"
    RANGER = "Ranger"
    MONK = "Monk"
    NECROMANCER = "Necromancer"
    MESMER = "Mesmer"
    ELEMENTALIST = "Elementalist"
    ASSASSIN = "Assassin"
    RITUALIST = "Ritualist"
    PARAGON = "Paragon"
    DERVISH = "Dervish"

PROFESSIONS_ORDERED = [
    Profession.WARRIOR,
    Profession.RANGER,
    Profession.MONK,
    Profession.NECROMANCER,
    Profession.MESMER,
    Profession.ELEMENTALIST,
    Profession.ASSASSIN,
    Profession.RITUALIST,
    Profession.PARAGON,
    Profession.DERVISH,
]

# ============================================================================
#region SECONDARY PROFESSION BUILDS
# ============================================================================

# Secondary profession capture builds organized by PRIMARY profession
# Format: PRIMARY_BUILD[your_primary][target_secondary] = template
# Each template should have: EVAS, YMLAD, Signet of Capture, max primary attribute

SECONDARY_BUILDS = {
    Profession.WARRIOR: {
        Profession.WARRIOR:      "OQcSE5OTOMMMHMwODAFFxgi1",        # W 
        Profession.RANGER:       "OQIREZaX0mEAAAAAAAAAYAA",        # W/R
        Profession.MONK:         "OQMREZaX0mEAAAAAAAAAYAA",        # W/Mo
        Profession.NECROMANCER:  "OQQREZaX0mEAAAAAAAAAYAA",        # W/N
        Profession.MESMER:       "OQUREZaX0mEAAAAAAAAAYAA",        # W/Me
        Profession.ELEMENTALIST: "OQYREZaX0mEAAAAAAAAAYAA",        # W/E
        Profession.ASSASSIN:     "OQcSE5OTOMMMHMwODAFFxgi1",        # W/A
        Profession.RITUALIST:    "OQgREZaX0mEAAAAAAAAAYAA",        # W/Rt
        Profession.PARAGON:      "OQkREZaX0mEAAAAAAAAAYAA",        # W/P
        Profession.DERVISH:      "OQoREZaX0mEAAAAAAAAAYAA",        # W/D
    },
    Profession.RANGER: {
        Profession.WARRIOR:      "OgEUUDLe1MHKOA+W4AYA0WAA",       # R/W 
        Profession.RANGER:       "OgUUIELe1MHKWD+W4AYA0WAA",       # R 
        Profession.MONK:         "OgMU4ELe1MHKGl+W4AYA0WAA",       # R/Mo 
        Profession.NECROMANCER:  "OgQUUELe1MHKON+W4AYA0WAA",       # R/N 
        Profession.MESMER:       "OgUUIELe1MHKWD+W4AYA0WAA",       # R/Me
        Profession.ELEMENTALIST: "OgYUoELe1MHKuY+W4AYA0WAA",       # R/E 
        Profession.ASSASSIN:     "OgcUYxrm5vIKmL7bCHAMA0mAAA",     # R/A 
        Profession.RITUALIST:    "OggkYhXXGDijiRd6bEOAgBAtRAA",    # R/Rt
        Profession.PARAGON:      "OgkkYhXaGfKjiRF7bEOAgBAtRAA",    # R/P 
        Profession.DERVISH:      "OgokYhXaGrKjip66bEOAgBAtRAA",    # R/D 
    },
    Profession.MESMER: {
        Profession.WARRIOR:      "OQFUAWBPsaQoAaAXADBEB9A2gDAA",       # Me/W
        Profession.RANGER:       "OQJUAWBPMcQoAaAXADBEB9A2gDAA",   # Me/R
        Profession.MONK:         "OQNEArwj1BhCoBcBMEQE0DYDOAA",       # Me/Mo
        Profession.NECROMANCER:  "OQREArwjdBhCoBcBMEQE0DYDOAA",       # Me/N
        Profession.MESMER:       "OQREArwjdBhCoBcBMEQE0DYDOAA",       # Me
        Profession.ELEMENTALIST: "OQZEArwjhBhCoBcBMEQE0DYDOAA",       # Me/E
        Profession.ASSASSIN:     "OQdUAWBPseQoAaAXADBEB9A2gDAA",       # Me/A
        Profession.RITUALIST:    "OQhkAsC8gJGEKgGwFwQARQPgN4AA",     # Me/Rt
        Profession.PARAGON:      "OQlkAsC8gVGEKgGwFwQARQPgN4AA",     # Me/P
        Profession.DERVISH:      "OQBDArwjRoAaAXADBEB9A2gDAA",     # Me/D
    }, 
    Profession.MONK: {
        Profession.WARRIOR:      "OwEU04nA3qRNgbE3N3ETfQgBADAA",   # Mo/W
        Profession.RANGER:       "OwIU04nAXsRNgbE3N3ETfQg+GDAA",   # Mo/R
        Profession.MONK:         "OwUUMsG/E4SNgbE3N3ETfQgAADAA",   # Mo
        Profession.NECROMANCER:  "OwQUcsG/E4SNgbE3N3ETfQgfCDAA",   # Mo/N
        Profession.MESMER:       "OwUUMsG/E4SNgbE3N3ETfQgAADAA",   # Mo/Me
        Profession.ELEMENTALIST: "OwYUosG/E4SNgbE3N3ETfQgFDDAA",   # Mo/E
        Profession.ASSASSIN:     "OwcU04nA3vRNgbE3N3ETfQguMDAA",   # Mo/A
        Profession.RITUALIST:    "Owgk0wPC0GaUD4GxdzNx0HEYGzAA",   # Mo/Rt
        Profession.PARAGON:      "Owkk0wPC0eaUD4GxdzNx0HEoK2AA",   # Mo/P
        Profession.DERVISH:      "Owok0wPC0uaUD4GxdzNx0HEo41AA",   # Mo/D
    },
    Profession.NECROMANCER: {
        Profession.WARRIOR:      "OAFUQkCbYZQZCuBPCVV7i2kAADAA",    # N/W
        Profession.RANGER:       "OAJUQkCbYcQZCuBPCVV7i2kAADAA",    # N/R
        Profession.MONK:         "OANEQSxG7BlJ4G8IUVtLaTCAMAA",     # N/Mo
        Profession.NECROMANCER:  "OAVEIBJFbMlJ4G8IUVtLaTCAMAA",     # N
        Profession.MESMER:       "OAVEIBJFbMlJ4G8IUVtLaTCAMAA",     # N/Me
        Profession.ELEMENTALIST: "OAZEQSxGnBlJ4G8IUVtLaTCAMAA",     # N/E
        Profession.ASSASSIN:     "OAdUQkCb4fQZCuBPCVV7i2kAADAA",   # N/A
        Profession.RITUALIST:    "OAhkQIFsBHGUmgbwjQV1uoNJAwAA",   # N/Rt
        Profession.PARAGON:      "OAlkQIFsBbGUmgbwjQV1uoNJAwAA",   # N/P
        Profession.DERVISH:      "OApkQIFsBrGUmgbwjQV1uoNJAwAA",   # N/D
    },
    Profession.ELEMENTALIST: {
        Profession.WARRIOR:      "OgFToYGXHaX0msYQYgWAZIAYAAA",    # E/W
        Profession.RANGER:       "OgJToYGjHaX0msYQYgWAZw3YAAA",    # E/R
        Profession.MONK:         "OgNDoMz9Q7i2kFDCD0CIDZEDAA",     # E/Mo
        Profession.NECROMANCER:  "OgRDcjyMT7i2kFDCD0CIDHCDAA",     # E/N
        Profession.MESMER:       "OgVDIjyMT7i2kFDCD0CIDXADAA",     # E/Me
        Profession.ELEMENTALIST: "OgVDIjyMT7i2kFDCD0CIDXADAA",     # E
        Profession.ASSASSIN:     "OgdToYG/HaX0msYQYgWAZwlZAAA",    # E/A
        Profession.RITUALIST:    "OghjowMM4Q7i2kFDCD0CIDfTDAA",    # E/Rt
        Profession.PARAGON:      "OgljowM85Q7i2kFDCD0CIDxYDAA",    # E/P
        Profession.DERVISH:      "OgpjowM86Q7i2kFDCD0CIDiXDAA",    # E/D
    },
    Profession.ASSASSIN: {
        Profession.WARRIOR:      "OwFTUnO/Zyhhh5g5AaX0mMAYAAA",    # A/W
        Profession.RANGER:       "OwJTgnO/Zyhhh5g5AaX0m03YAAA",    # A/R
        Profession.MONK:         "OwNT8mO/Zyhhh5g5AaX0m8uaAAA",    # A/Mo
        Profession.NECROMANCER:  "OwRTcmO/Zyhhh5g5AaX0m8QYAAA",    # A/N
        Profession.MESMER:       "OwVTImO/Zyhhh5g5AaX0m8CYAAA",    # A/Me
        Profession.ELEMENTALIST: "OwZTomO/Zyhhh5g5AaX0msYYAAA",    # A/E
        Profession.ASSASSIN:     "OwBT0Z/8Zyhhh5g5AaX0mkAaAAA",    # A
        Profession.RITUALIST:    "Owhj0xfM4QOMMMHMHQ7i2kfTDAA",    # A/Rt
        Profession.PARAGON:      "Owlj0xf85QOMMMHMHQ7i2kxYDAA",    # A/P
        Profession.DERVISH:      "Owpj0xf86QOMMMHMHQ7i2kiXDAA",    # A/D
    },
    Profession.RITUALIST: {
        Profession.WARRIOR:      "OAGkUFgsITKT18a+NLnnNm5mbAA",    # Rt/W
        Profession.RANGER:       "OAKkgFgsITKT18a+NLnnNm5mbAA",    # Rt/R
        Profession.MONK:         "OAOk8EgsITKT18a+NLnnNm5mbAA",    # Rt/Mo
        Profession.NECROMANCER:  "OASkcEgsITKT18a+NLnnNm5mbAA",    # Rt/N
        Profession.MESMER:       "OAWkIEgsITKT18a+NLnnNm5mbAA",    # Rt/Me
        Profession.ELEMENTALIST: "OAakoEgsITKT18a+NLnnNm5mbAA",    # Rt/E
        Profession.ASSASSIN:     "OAek8FgsITKT18a+NLnnNm5mbAA",    # Rt/A
        Profession.RITUALIST:    "OACjAyiM5MVzr53sce2YmbuBAA",     # Rt
        Profession.PARAGON:      "OAmkAyiMpUGT18a+NLnnNm5mbAA",    # Rt/P
        Profession.DERVISH:      "OAqkAyiMpoGT18a+NLnnNm5mbAA",    # Rt/D
    },
    Profession.PARAGON: {
        Profession.WARRIOR:      "OQGkUFliJjy0uoNJP2OmJ2NWN2AA",   # P/W
        Profession.RANGER:       "OQKkkFliJjy0uoNJP2OmJ2NWN2AA",   # P/R
        Profession.MONK:         "OQOk0EliJjy0uoNJP2OmJ2NWN2AA",   # P/Mo
        Profession.NECROMANCER:  "OQSkcEliJjy0uoNJP2OmJ2NWN2AA",   # P/N
        Profession.MESMER:       "OQWkMEliJjy0uoNJP2OmJ2NWN2AA",   # P/Me
        Profession.ELEMENTALIST: "OQakoEliJjy0uoNJP2OmJ2NWN2AA",   # P/E
        Profession.ASSASSIN:     "OQek8FliJjy0uoNJP2OmJ2NWN2AA",   # P/A
        Profession.RITUALIST:    "OQCjUKmMKT7i2k8Y7YmY3Y1YDAA",   # P/Rt
        Profession.PARAGON:      "OQCjUOmMKT7i2k8Y7YmY3Y1YDAA",   # P
        Profession.DERVISH:      "OQqkUKmMKvG0uoNJP2OmJ2NWN2AA",   # P/D
    },
    Profession.DERVISH: { 
        Profession.WARRIOR:      "OgGkUFp5Kzmk513m4VMJB2+F71AA",   # D/W
        Profession.RANGER:       "OgKkgFp5Kzmk513m4VMJB2+F71AA",   # D/R
        Profession.MONK:         "OgOk0Ep5Kzmk513m4VMJB2+F71AA",   # D/Mo
        Profession.NECROMANCER:  "OgSkcEp5Kzmk513m4VMJB2+F71AA",   # D/N
        Profession.MESMER:       "OgWkIEp5Kzmk513m4VMJB2+F71AA",   # D/Me
        Profession.ELEMENTALIST: "OgakkEp5Kzmk513m4VMJB2+F71AA",   # D/E
        Profession.ASSASSIN:     "Ogek8Fp5Kzmk513m4VMJB2+F71AA",   # D/A
        Profession.RITUALIST:    "OgikIGp5Kzmk513m4VMJB2+F71AA",   # D/Rt
        Profession.PARAGON:      "OgmkUGp5Kzmk513m4VMJB2+F71AA",   # D/P
        Profession.DERVISH:      "OgCjkmrMbSmXfbiXxkEY7XsXDAA",   # D            
    },
}

# Session storage for save/load/restore
_saved_build_template = None
_starting_map_id = None

# ============================================================================
#endregion


@dataclass
class EliteSkill:
    """Represents a single elite skill"""
    id: str
    display_name: str
    skill_id: int
    profession: Profession
    type: EliteSkillType
    step_name: str
    capture_function: str
    start_map: int = 0
    description: str = ""
    icon_filename: Optional[str] = None  # Icon filename in Textures/Skill_Icons/

#region Define all elite skills
ELITE_SKILLS = [
    EliteSkill(
        id="skill_39",
        display_name="Energy Surge",
        skill_id=39,
        profession=Profession.MESMER,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Energy Surge",
        capture_function="EnergySurge",
        start_map=414,
        icon_filename="[39] - Energy Surge.jpg",
        
    ),
    EliteSkill(
        id="skill_1499",
        display_name="Pious Renewal",
        skill_id=1499,
        profession=Profession.DERVISH,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Pious Renewal",
        capture_function="PiousRenewal",
        start_map=493,
        icon_filename="[1499] - Pious Renewal.jpg",
    ),
    EliteSkill(
        id="skill_119",
        display_name="Blood is Power",
        skill_id=119,
        profession=Profession.NECROMANCER,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Blood is Power",
        capture_function="BloodIsPower",
        start_map=393,
        icon_filename="[119] - Blood is Power.jpg",
    ),
    EliteSkill(
        id="skill_1759",
        display_name="Vow of Strength - LOCALS ONLY!!!",
        skill_id=1759,
        profession=Profession.DERVISH,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Vow of Strength Locals",
        capture_function="VowOfStrengthLocals",
        start_map=479,
        icon_filename="[1759] - Vow of Strength.jpg",
    ),
    EliteSkill(
        id="skill_47",
        display_name="Ineptitude",
        skill_id=47,
        profession=Profession.MESMER,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Ineptitude",
        capture_function="Ineptitude",
        start_map=641,
        icon_filename="[47] - Ineptitude.jpg",
    ),
    EliteSkill(
        id="skill_53",
        display_name="Migraine",
        skill_id=53,
        profession=Profession.MESMER,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Migraine",
        capture_function="Migraine",
        start_map=638,
        icon_filename="[53] - Migraine.jpg",
    ), 
    EliteSkill(
        id="skill_1066",
        display_name="Spoil Victor",
        skill_id=1066,
        profession=Profession.NECROMANCER,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Spoil Victor",
        capture_function="SpoilVictor",
        start_map=230,
        icon_filename="[1066] - Spoil Victor.jpg",
    ),
    EliteSkill(
        id="skill_1239",
        display_name="Signet of Spirits",
        skill_id=1239,
        profession=Profession.RITUALIST,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Signet of Spirits",
        capture_function="SignetOfSpirits",
        start_map=388,
        icon_filename="[1239] - Signet of Spirits.jpg",
    ),
    EliteSkill(
        id="skill_121",
        display_name="Spiteful Spirit   ",
        skill_id=121,
        profession=Profession.NECROMANCER,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Spiteful Spirit",
        capture_function="SpitefulSpirit",
        start_map=155,
        icon_filename="[121] - Spiteful Spirit.jpg",
    ),
    EliteSkill(
        id="skill_236",
        display_name="Mist Form",
        skill_id=236,
        profession=Profession.ELEMENTALIST,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Mist Form",
        capture_function="MistForm",
        start_map=155,
        icon_filename="[236] - Mist Form.jpg",
    ),
    EliteSkill(
        id="skill_294",
        display_name="Signet of Judgement",
        skill_id=294,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Signet of Judgement",
        capture_function="SignetOfJudgement",
        start_map=155,
        icon_filename="[294] - Signet of Judgment.jpg",
    ),
    EliteSkill(
        id="skill_33",
        display_name="Illusionary Weaponry",
        skill_id=33,
        profession=Profession.MESMER,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Illusionary Weaponry",
        capture_function="IllusionaryWeaponry",
        start_map=155,
        icon_filename="[33] - Illusionary Weaponry.jpg",
    ),
    EliteSkill(
        id="skill_826",
        display_name="Shadow Form",
        skill_id=826,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Shadow Form",
        capture_function="ShadowForm",
        start_map=284,
        icon_filename="[826] - Shadow Form.jpg",
    ),
    EliteSkill(
        id="skill_826_1",
        display_name="Shadow Form - WoC",
        skill_id=826,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Shadow Form - WoC",
        capture_function="ShadowFormWoC",
        start_map=284,
        icon_filename="[826] - Shadow Form.jpg",
    ),
    EliteSkill(
        id="skill_1198",
        display_name="Broad Head Arrow",
        skill_id=1198,
        profession=Profession.RANGER,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Broad Head Arrow",
        capture_function="BroadHeadArrow",
        start_map=284,
        icon_filename="[1198] - Broad Head Arrow.jpg",
    ),
    EliteSkill(
        id="skill_1240",
        display_name="Soul Twisting",
        skill_id=1240,
        profession=Profession.RITUALIST,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Soul Twisting",
        capture_function="SoulTwisting",
        start_map=298,
        icon_filename="[1240] - Soul Twisting.jpg",
    ),
    EliteSkill(
        id="skill_831",
        display_name="Primal Rage",
        skill_id=831,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Primal Rage",
        capture_function="PrimalRage",
        start_map=298,
        icon_filename="[831] - Primal Rage.jpg",
    ),
    EliteSkill(
        id="1652",
        display_name="Shadow Prison",
        skill_id=1652,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Shadow Prison",
        capture_function="ShadowPrison",
        start_map=398,
        icon_filename="[1652] - Shadow Prison.jpg",
    ), 
    EliteSkill(
        id="928",
        display_name="Shadow Shroud",
        skill_id=928,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Shadow Shroud",
        capture_function="Shadow_Shroud",
        start_map=277,
        icon_filename="[928] - Shadow Shroud.jpg",
    ),
    EliteSkill(
        id="skill_1773",
        display_name="Soldier's Fury",
        skill_id=1773,
        profession=Profession.PARAGON,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Soldier's Fury",
        capture_function="SoldiersFury",
        start_map=438,
        icon_filename="[1773] - Soldier's Fury.jpg",
    ),
    EliteSkill(
        id="skill_218",
        display_name="Obsidian Flesh",
        skill_id=218,
        profession=Profession.ELEMENTALIST,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Obsidian Flesh",
        capture_function="ObsidianFlesh",
        start_map=438,
        icon_filename="[218] - Obsidian Flesh.jpg",
    ),
    EliteSkill(
        id="skill_338",
        display_name="Eviscerate",
        skill_id=338,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Eviscerate",
        capture_function="Eviscerate",
        start_map=124,
        icon_filename="[338] - Eviscerate.jpg",
    ),
    EliteSkill(
        id="skill_465",
        display_name="Greater Conflagration",
        skill_id=465,
        profession=Profession.RANGER,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Greater Conflagration",
        capture_function="GreaterConflagration",
        start_map=124,
        icon_filename="[465] - Greater Conflagration.jpg",
    ),
    EliteSkill(
        id="skill_114",
        display_name="Aura of the Lich",
        skill_id=114,
        profession=Profession.NECROMANCER,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Aura of the Lich",
        capture_function="AuraOfTheLich",
        start_map=124,
        icon_filename="[114] - Aura of the Lich.jpg",
    ),
    EliteSkill(
        id="skill_52",
        display_name="Panic",
        skill_id=52,
        profession=Profession.MESMER,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Panic",
        capture_function="Panic",
        start_map=124,
        icon_filename="[52] - Panic.jpg",
    ),
    EliteSkill(
        id="skill_185",
        display_name="Mind Burn",
        skill_id=185,
        profession=Profession.ELEMENTALIST,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Mind Burn",
        capture_function="MindBurn",
        start_map=124,
        icon_filename="[185] - Mind Burn.jpg",
    ),
    EliteSkill(
        id="skill_1035",
        display_name="Assassin's Promise",
        skill_id=1035,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Assassin's Promise",
        capture_function="AssassinsPromise",
        start_map=640,
        icon_filename="[1035] - Assassin's Promise.jpg",
    ),
    EliteSkill(
        id="skill_268",
        display_name="Unyielding Aura",
        skill_id=268,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Unyielding Aura",
        capture_function="UnyieldingAura",
        start_map=158,
        icon_filename="[268] - Unyielding Aura.jpg",
    ),
    EliteSkill(
        id="skill_365",
        display_name="Victory is Mine",
        skill_id=365,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Victory is Mine",
        capture_function="VictoryIsMine",
        start_map=158,
        icon_filename="[365] - Victory is Mine!.jpg",
    ),
    EliteSkill(
        id="skill_404",
        display_name="Poison Arrow",
        skill_id=404,
        profession=Profession.RANGER,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Poison Arrow",
        capture_function="PoisonArrow",
        start_map=158,
        icon_filename="[404] - Poison Arrow.jpg",
    ),
    EliteSkill(
        id="skill_132",
        display_name="Plague Signet",
        skill_id=132,
        profession=Profession.NECROMANCER,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Plague Signet",
        capture_function="PlagueSignet",
        start_map=158,
        icon_filename="[132] - Plague Signet.jpg",
    ),
    EliteSkill(
        id="skill_227",
        display_name="Glimmering Mark",
        skill_id=227,
        profession=Profession.ELEMENTALIST,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Glimmering Mark",
        capture_function="GlimmeringMark",
        start_map=158,
        icon_filename="[227] - Glimmering Mark.jpg",
    ),
    EliteSkill(
        id="skill_273",
        display_name="Spell Breaker",
        skill_id=273,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Spell Breaker",
        capture_function="SpellBreaker",
        start_map=155,
        icon_filename="[273] - Spell Breaker.jpg",
    ),
    EliteSkill(
        id="skill_82",
        display_name="Mantra of Recall",
        skill_id=82,
        profession=Profession.MESMER,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Mantra of Recall",
        capture_function="MantraOfRecall",
        start_map=155,
        icon_filename="[82] - Mantra of Recall.jpg",
    ),
    EliteSkill(
        id="skill_226",
        display_name="Mind Shock",
        skill_id=226,
        profession=Profession.ELEMENTALIST,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Mind Shock",
        capture_function="MindShock",
        start_map=155,
        icon_filename="[226] - Mind Shock.jpg",
    ),
    EliteSkill(
        id="skill_1517",
        display_name="Vow of Silence",
        skill_id=1517,
        profession=Profession.DERVISH,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Vow of Silence",
        capture_function="VowOfSilence",
        start_map=478,
        icon_filename="[1517] - Vow of Silence.jpg",
    ), 
    EliteSkill(
        id="skill_1686",
        display_name="Glimmer of Light",
        skill_id=1686,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Glimmer of Light",
        capture_function="GlimmerOfLight",
        start_map=421,
        icon_filename="[1686] - Glimmer of Light.jpg",
    ),
    EliteSkill(
        id="skill_1754",
        display_name="Onslaught",
        skill_id=1754,
        profession=Profession.DERVISH,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Onslaught",
        capture_function="Onslaught",
        start_map=643,
        icon_filename="[1754] - Onslaught.jpg",
    ),
    EliteSkill(
        id="skill_1760",
        display_name="Ebon Dust Aura",
        skill_id=1760,
        profession=Profession.DERVISH,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Ebon Dust Aura",
        capture_function="EbonDustAura",
        start_map=414,
        icon_filename="[1760] - Ebon Dust Aura.jpg",
    ),
    EliteSkill(
        id="skill_1518",
        display_name="Avatar of Balthazar",
        skill_id=1518,
        profession=Profession.DERVISH,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Avatar of Balthazar",
        capture_function="AvatarOfBalthazar",
        start_map=387,
        icon_filename="[1518] - Avatar of Balthazar.jpg",
    ),
    EliteSkill(
        id="skill_1522",
        display_name="Avatar of Melandru",
        skill_id=1522,
        profession=Profession.DERVISH,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Avatar of Melandru",
        capture_function="AvatarOfMelandru",
        start_map=477,
        icon_filename="[1522] - Avatar of Melandru.jpg",
    ),
    EliteSkill(
        id="skill_1519",
        display_name="Avatar of Dwayna",
        skill_id=1519,
        profession=Profession.DERVISH,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Avatar of Dwayna",
        capture_function="AvatarOfDwayna",
        start_map=424,
        icon_filename="[1519] - Avatar of Dwayna.jpg",
    ),
    EliteSkill(
        id="skill_1521",
        display_name="Avatar of Lyssa",
        skill_id=1521,
        profession=Profession.DERVISH,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Avatar of Lyssa",
        capture_function="AvatarOfLyssa",
        start_map=554,
        icon_filename="[1521] - Avatar of Lyssa.jpg",
    ),
    EliteSkill(
        id="skill_1520",
        display_name="Avatar of Grenth",
        skill_id=1520,
        profession=Profession.DERVISH,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Avatar of Grenth",
        capture_function="AvatarOfGrenth",
        start_map=426,
        icon_filename="[1520] - Avatar of Grenth.jpg",
    ),
    EliteSkill(
        id="skill_1750",
        display_name="Xinrae's Weapon",
        skill_id=1750,
        profession=Profession.RITUALIST,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Xinrae's Weapon",
        capture_function="XinraesWeapon",
        start_map=496,
        icon_filename="[1750] - Xinrae's Weapon.jpg",
    ),
    EliteSkill(
        id="skill_1596",
        display_name="Incoming!",
        skill_id=1596,
        profession=Profession.PARAGON,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Incoming!",
        capture_function="Incoming",
        start_map=414,
        icon_filename="[1596] - Incoming!.jpg",
    ), 
    EliteSkill(
        id="skill_1769",
        display_name="Focused Anger",
        skill_id=1769,
        profession=Profession.PARAGON,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Focused Anger",
        capture_function="FocusedAnger",
        start_map=427,
        icon_filename="[1769] - Focused Anger.jpg",

    ),
    EliteSkill(
        id="skill_269",
        display_name="Mark of Protection",
        skill_id=269,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Mark of Protection",
        capture_function="MarkOfProtection",
        start_map=38,
        icon_filename="[269] - Mark of Protection.jpg",
    ),
    EliteSkill(
        id="skill_1465",
        display_name="Prepared Shot",
        skill_id=1465,
        profession=Profession.RANGER,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Prepared Shot",
        capture_function="PreparedShot",
        start_map=642,
        icon_filename="[1465] - Prepared Shot.jpg",
    ),
    # Anniversary Skills
    EliteSkill(
        id="skill_3427",
        display_name="Together as One!",
        skill_id=3427,
        profession=Profession.RANGER,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Together as One",
        capture_function="TogetherAsOne",
        start_map=650,
        icon_filename="[3427] - Together as One!.jpg",
    ),
    EliteSkill(
        id="skill_3431",
        display_name="Heroic Refrain",
        skill_id=3431,
        profession=Profession.PARAGON,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Heroic Refrain",
        capture_function="HeroicRefrain",
        start_map=440,
        icon_filename="[3431] - Heroic Refrain.jpg",
    ),
    EliteSkill(
        id="skill_3423",
        display_name="Soul Taker",
        skill_id=3423,
        profession=Profession.NECROMANCER,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Soul Taker",
        capture_function="SoulTaker",
        start_map=35,
        icon_filename="[3423] - Soul Taker.jpg",
    ),
    EliteSkill(
        id="skill_3424",
        display_name="Over The Limit",
        skill_id=3424,
        profession=Profession.ELEMENTALIST,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Over The Limit",
        capture_function="OverTheLimit",
        start_map=35,
        icon_filename="[3424] - Over the Limit.jpg",
    ),
    EliteSkill(
        id="skill_3425",
        display_name="Judgment Strike",
        skill_id=3425,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Judgment Strike",
        capture_function="JudgmentStrike",
        start_map=440,
        icon_filename="[3425] - Judgment Strike.jpg",
    ),
    EliteSkill(
        id="skill_3422",
        display_name="Time Ward",
        skill_id=3422,
        profession=Profession.MESMER,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Time Ward",
        capture_function="TimeWard",
        start_map=650,
        icon_filename="[3422] - Time Ward.jpg",
    ),
    EliteSkill(
        id="skill_3430",
        display_name="Vow of Revolution",
        skill_id=3430,
        profession=Profession.DERVISH,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Vow of Revolution",
        capture_function="VowOfRevolution",
        start_map=440,
        icon_filename="[3430] - Vow of Revolution.jpg",
    ),
    EliteSkill(
        id="skill_3426",
        display_name="Seven Weapon Stance",
        skill_id=3426,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Seven Weapon Stance",
        capture_function="SevenWeaponStance",
        start_map=226,
        icon_filename="[3426] - Seven Weapons Stance.jpg",
    ),
    EliteSkill(
        id="skill_3429",
        display_name="Weapons of Three Forges",
        skill_id=3429,
        profession=Profession.RITUALIST,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Weapons of Three Forges",
        capture_function="WeaponsOfThreeForges",
        start_map=226,
        icon_filename="[3429] - Weapons of Three Forges.jpg",
    ),
    EliteSkill(
        id="skill_3428",
        display_name="Shadow Theft",
        skill_id=3428,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Shadow Theft",
        capture_function="ShadowTheft",
        start_map=226,
        icon_filename="[3428] - Shadow Theft.jpg",
    ), 
    EliteSkill(
        id="skill_1634",
        display_name="Shattering Assault",
        skill_id=1634,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Shattering Assault",
        capture_function="Shattering_Assault",
        start_map=480,
        icon_filename="[1634] - Shattering Assault.jpg",
    ),
    EliteSkill(
        id="skill_1568",
        display_name="Anthem of Guidance",
        skill_id=1568,
        profession=Profession.PARAGON,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Anthem of Guidance",
        capture_function="AnthemofGuidance",
        start_map=403,
        icon_filename="[1568] - Anthem of Guidance.jpg",
    ),
    EliteSkill(
        id="skill_1554",
        display_name="Crippling Anthem",
        skill_id=1554,
        profession=Profession.PARAGON,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Crippling Anthem",
        capture_function="CripplingAnthem",
        start_map=376,
        icon_filename="[1554] - Crippling Anthem.jpg",
    ),
    EliteSkill(
        id="skill_1587",
        display_name="Angelic Bond",
        skill_id=1587,
        profession=Profession.PARAGON,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Angelic Bond",
        capture_function="AngelicBond",
        start_map=434,
        icon_filename="[1587] - Angelic Bond.jpg",
    ),
    EliteSkill(
        id="skill_1553",
        display_name="Anthem of Fury",
        skill_id=1553,
        profession=Profession.PARAGON,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Anthem of Fury",
        capture_function="AnthemofFury",
        start_map=450,
        icon_filename="[1553] - Anthem of Fury.jpg",
    ),
    EliteSkill(
        id="skill_1555",
        display_name="Defensive Anthem",
        skill_id=1555,
        profession=Profession.PARAGON,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Defensive Anthem",
        capture_function="DefensiveAnthem",
        start_map=387,
        icon_filename="[1555] - Defensive Anthem.jpg",
    ),
    EliteSkill(
        id="skill_1599",
        display_name="It's Just a Flesh Wound.",
        skill_id=1599,
        profession=Profession.PARAGON,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]It's Just a Flesh Wound.",
        capture_function="ItsJustaFleshWound",
        start_map=480,
        icon_filename="[1599] - It's Just a Flesh Wound..jpg",
    ),
    EliteSkill(
        id="skill_1782",
        display_name="The Power Is Yours!",
        skill_id=1782,
        profession=Profession.PARAGON,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]The Power Is Yours!",
        capture_function="ThePowerIsYours",
        start_map=440,
        icon_filename="[1782] - The Power Is Yours!.jpg",
    ),
    EliteSkill(
        id="skill_1570",
        display_name="Song of Purification",
        skill_id=1570,
        profession=Profession.PARAGON,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Song of Purification",
        capture_function="SongofPurification",
        start_map=403,
        icon_filename="[1570] - Song of Purification.jpg",
    ),
    EliteSkill(
        id="skill_1771",
        display_name="Song of Restoration",
        skill_id=1771,
        profession=Profession.PARAGON,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Song of Restoration",
        capture_function="Song of Restoration",
        start_map=428,
        icon_filename="[1771] - Song of Restoration.jpg",
    ),
    EliteSkill(
        id="skill_1548",
        display_name="Cruel Spear",
        skill_id=1548,
        profession=Profession.PARAGON,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Cruel Spear",
        capture_function="Cruel Spear",
        start_map=427,
        icon_filename="[1548] - Cruel Spear.jpg",
    ),
    EliteSkill(
        id="skill_1602",
        display_name="Stunning Strike",
        skill_id=1602,
        profession=Profession.PARAGON,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Stunning Strike",
        capture_function="Stunning Strike",
        start_map=469,
        icon_filename="[1602] - Stunning Strike.jpg",
    ),
    EliteSkill(
        id="skill_1588",
        display_name="Cautery Signet",
        skill_id=1588,
        profession=Profession.PARAGON,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Cautery Signet",
        capture_function="Cautery Signet",
        start_map=424,
        icon_filename="[1588] - Cautery Signet.jpg",
    ),
        EliteSkill(
        id="skill_1502",
        display_name="Arcane Zeal",
        skill_id=1502,
        profession=Profession.DERVISH,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Arcane Zeal",
        capture_function="ArcaneZeal",
        start_map=450,
        icon_filename="[1502] - Arcane Zeal.jpg",
    ),
    EliteSkill(
        id="skill_1756",
        display_name="Grenth's Grasp",
        skill_id=1756,
        profession=Profession.DERVISH,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Grenth's Grasp",
        capture_function="GrenthsGrasp",
        start_map=477,
        icon_filename="[1756] - Grenth's Grasp.jpg",
    ),
    EliteSkill(
        id="skill_1767",
        display_name="Reaper's Sweep",
        skill_id=1767,
        profession=Profession.DERVISH,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Reaper's Sweep",
        capture_function="ReapersSweep",
        start_map=421,
        icon_filename="[1767] - Reaper's Sweep.jpg",
    ),
    EliteSkill(
        id="skill_1759_1",
        display_name="Vow of Strength",
        skill_id=1759,
        profession=Profession.DERVISH,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Vow of Strength",
        capture_function="VowofStrength",
        start_map=376,
        icon_filename="[1759] - Vow of Strength.jpg",
    ),
    EliteSkill(
        id="skill_1536",
        display_name="Wounding Strike",
        skill_id=1536,
        profession=Profession.DERVISH,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Wounding Strike",
        capture_function="WoundingStrike",
        start_map=476,
        icon_filename="[1536] - Wounding Strike.jpg",
    ),
    EliteSkill(
        id="skill_1761",
        display_name="Zealous Vow",
        skill_id=1761,
        profession=Profession.DERVISH,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Zealous Vow",
        capture_function="ZealousVow",
        start_map=378,
        icon_filename="[1761] - Zealous Vow.jpg",
    ),
    EliteSkill(
        id="skill_941",
        display_name="Blessed Light",
        skill_id=1768,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Blessed Light",
        capture_function="BlessedLight",
        start_map=193,
        icon_filename="[941] - Blessed Light.jpg",
    ),
    EliteSkill(
        id="skill_867",
        display_name="Healing Light",
        skill_id=867,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Healing Light",
        capture_function="HealingLight",
        start_map=193,
        icon_filename="[867] - Healing Light.jpg",
    ), 
    EliteSkill(
        id="skill_847",
        display_name="Boon Signet",
        skill_id=847,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Boon Signet",
        capture_function="BoonSignet",
        start_map=388,
        icon_filename="[847] - Boon Signet.jpg",
    ),
    EliteSkill(
        id="skill_1393",
        display_name="Healer's Boon",
        skill_id=1393,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Healer's Boon",
        capture_function="HealersBoon",
        start_map=388,
        icon_filename="[1393] - Healer's Boon.jpg",
    ), 
    EliteSkill(
        id="skill_266",
        display_name="Peace and Harmony",
        skill_id=266,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Peace and Harmony",
        capture_function="PeaceAndHarmony",
        start_map=155,
        icon_filename="[266] - Peace and Harmony.jpg",
    ),
    EliteSkill(
        id="skill_942",
        display_name="Withdraw Hexes",
        skill_id=942,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Withdraw Hexes",
        capture_function="WithdrawHexes",
        start_map=389,
        icon_filename="[942] - Withdraw Hexes.jpg",
    ),
    EliteSkill(
        id="skill_1118",
        display_name="Healing Burst",
        skill_id=1118,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Healing Burst",
        capture_function="HealingBurst",
        start_map=130,
        icon_filename="[1118] - Healing Burst.jpg",
    ),
    EliteSkill(
        id="skill_285",
        display_name="Healing Hands",
        skill_id=285,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Healing Hands",
        capture_function="HealingHands",
        start_map=35,
        icon_filename="[285] - Healing Hands.jpg",
    ),
    EliteSkill(
        id="skill_1397",
        display_name="Light of Deliverance",
        skill_id=1397,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Light of Deliverance",
        capture_function="LightOfDeliverance",
        start_map=554,
        icon_filename="[1397] - Light of Deliverance.jpg",
    ),
    EliteSkill(
        id="skill_282",
        display_name="Word of Healing",
        skill_id=282,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Word of Healing",
        capture_function="WordOfHealing",
        start_map=303,
        icon_filename="[282] - Word of Healing.jpg",
    ),
    EliteSkill(
        id="skill_1115",
        display_name="Air of Enchantment",
        skill_id=1115,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Air of Enchantment",
        capture_function="AirofEnchantment",
        start_map=297,
        icon_filename="[1115] - Air of Enchantment.jpg",
    ),
    EliteSkill(
        id="skill_260",
        display_name="Aura of Faith",
        skill_id=260,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Aura of Faith",
        capture_function="AuraofFaith",
        start_map=23,
        icon_filename="[260] - Aura of Faith.jpg",
    ), 
    EliteSkill(
        id="skill_1692",
        display_name="Divert Hexes",
        skill_id=1692,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Divert Hexes",
        capture_function="DivertHexes",
        start_map=480,
        icon_filename="[1692] - Divert Hexes.jpg",
    ),
    EliteSkill(
        id="skill_1123",
        display_name="Life Sheath",
        skill_id=1123,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Life Sheath",
        capture_function="LifeSheath",
        start_map=284,
        icon_filename="[1123] - Life Sheath.jpg",
    ),
    EliteSkill(
        id="skill_261",
        display_name="Shield of Regeneration",
        skill_id=261,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Shield of Regeneration",
        capture_function="ShieldofRegeneration",
        start_map=648,
        icon_filename="[261] - Shield of Regeneration.jpg",
    ),
    EliteSkill(
        id="skill_1687",
        display_name="Zealous Benediction",
        skill_id=1687,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Zealous Benediction",
        capture_function="ZealousBenediction",
        start_map=428,
        icon_filename="[1687] - Zealous Benediction.jpg",
    ),
    EliteSkill(
        id="skill_1688",
        display_name="Defender's Zeal",
        skill_id=1688,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Defender's Zeal",
        capture_function="DefendersZeal",
        start_map=469,
        icon_filename="[1688] - Defender's Zeal.jpg",
    ),
    EliteSkill(
        id="skill_830",
        display_name="Ray of Judgment",
        skill_id=830,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Ray of Judgment",
        capture_function="RayofJudgment",
        start_map=303,
        icon_filename="[830] - Ray of Judgment.jpg",
    ),
    EliteSkill(
        id="skill_1129",
        display_name="Word of Censure",
        skill_id=1129,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Word of Censure",
        capture_function="WordOfCensure",
        start_map=303,
        icon_filename="[1129] - Word of Censure.jpg",
    ),
    EliteSkill(
        id="skill_1126",
        display_name="Empathic Removal",
        skill_id=1126,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Empathic Removal",
        capture_function="EmpathicRemoval",
        start_map=129,
        icon_filename="[1126] - Empathic Removal.jpg",
    ),
    EliteSkill(
        id="skill_298",
        display_name="Martyr",
        skill_id=298,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Martyr",
        capture_function="Martyr",
        start_map=129,
        icon_filename="[298] - Martyr.jpg",
    ),
    EliteSkill(
        id="skill_1690",
        display_name="Signet of Removal",
        skill_id=1690,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Signet of Removal",
        capture_function="SignetofRemoval",
        start_map=427,
        icon_filename="[1690] - Signet of Removal.jpg",
    ),
    EliteSkill(
        id="skill_1395",
        display_name="Balthazar's Pendulum",
        skill_id=1395,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Balthazar's Pendulum",
        capture_function="BalthazarsPendulum",
        start_map=378,
        icon_filename="[1395] - Balthazar's Pendulum.jpg",
    ),
    EliteSkill(
        id="skill_808",
        display_name="Reaper's Mark",
        skill_id=808,
        profession=Profession.NECROMANCER,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Reaper's Mark",
        capture_function="ReapersMark",
        start_map=378,
        icon_filename="[808] - Reaper's Mark.jpg",
    ),
        EliteSkill(
        id="skill_364",
        display_name="Charge!",
        skill_id=364,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Charge!",
        capture_function="Charge",
        start_map=277,
        icon_filename="[364] - Charge!.jpg",
    ),
    EliteSkill(
        id="skill_869",
        display_name="Coward!",
        skill_id=869,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Coward!",
        capture_function="Coward",
        start_map=278,
        icon_filename="[869] - Coward!.jpg",
    ),
    EliteSkill(
        id="skill_1412",
        display_name="You're All Alone!",
        skill_id=1412,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]You're All Alone!",
        capture_function="YoureAllAlone",
        start_map=376,
        icon_filename="[1412] - You're All Alone!.jpg",
    ),
    EliteSkill(
        id="skill_1142",
        display_name="Auspicious Parry",
        skill_id=1142,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Auspicious Parry",
        capture_function="AuspiciousParry",
        start_map=225,
        icon_filename="[1142] - Auspicious Parry.jpg",
    ),
    EliteSkill(
        id="skill_358",
        display_name="Backbreaker",
        skill_id=358,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Backbreaker",
        capture_function="Backbreaker",
        start_map=638,
        icon_filename="[358] - Backbreaker.jpg",
    ),
    EliteSkill(
        id="skill_317",
        display_name="Battle Rage",
        skill_id=317,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Battle Rage",
        capture_function="BattleRage",
        start_map=219,
        icon_filename="[317] - Battle Rage.jpg",
    ),
    EliteSkill(
        id="skill_379",
        display_name="Bull's Charge",
        skill_id=379,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Bull's Charge",
        capture_function="BullsCharge",
        start_map=35,
        icon_filename="[379] - Bull's Charge.jpg",
    ),
    EliteSkill(
        id="skill_1405",
        display_name="Charging Strike",
        skill_id=1405,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Charging Strike",
        capture_function="ChargingStrike",
        start_map=435,
        icon_filename="[1405] - Charging Strike.jpg",
    ),
    EliteSkill(
        id="skill_335",
        display_name="Cleave",
        skill_id=335,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Cleave",
        capture_function="Cleave",
        start_map=289,
        icon_filename="[335] - Cleave.jpg",
    ),
    EliteSkill(
        id="skill_1415",
        display_name="Crippling Slash",
        skill_id=1415,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Crippling Slash",
        capture_function="CripplingSlash",
        start_map=644,
        icon_filename="[1415] - Crippling Slash.jpg",
    ),
    EliteSkill(
        id="skill_1696",
        display_name="Decapitate",
        skill_id=1696,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Decapitate",
        capture_function="Decapitate",
        start_map=424,
        icon_filename="[1696] - Decapitate.jpg",
    ),
    EliteSkill(
        id="skill_318",
        display_name="Defy Pain",
        skill_id=318,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Defy Pain",
        capture_function="DefyPain",
        start_map=24,
        icon_filename="[318] - Defy Pain.jpg",
    ),
    EliteSkill(
        id="skill_355",
        display_name="Devastating Hammer",
        skill_id=355,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Devastating Hammer",
        capture_function="DevastatingHammer",
        start_map=279,
        icon_filename="[355] - Devastating Hammer.jpg",
    ),
    EliteSkill(
        id="skill_907",
        display_name="Dragon Slash",
        skill_id=907,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Dragon Slash",
        capture_function="DragonSlash",
        start_map=273,
        icon_filename="[907] - Dragon Slash.jpg",
    ),
    EliteSkill(
        id="skill_375",
        display_name="Dwarven Battle Stance",
        skill_id=375,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Dwarven Battle Stance",
        capture_function="DwarvenBattleStance",
        start_map=639,
        icon_filename="[375] - Dwarven Battle Stance.jpg",
#    ),
#    EliteSkill(
#        id="skill_354",
#        display_name="Earth Shaker",
#        skill_id=354,
#        profession=Profession.WARRIOR,
#        type=EliteSkillType.ELITE_SKILL,
#        step_name="[H]Earth Shaker",
#        capture_function="EarthShaker",
#        start_map=,
#        icon_filename="[354] - Earth Shaker.jpg",
   ),
   EliteSkill(
       id="skill_993",
       display_name="Enraged Smash",
       skill_id=993,
       profession=Profession.WARRIOR,
       type=EliteSkillType.ELITE_SKILL,
       step_name="[H]Enraged Smash",
       capture_function="EnragedSmash",
       start_map=274,
       icon_filename="[993] - Enraged Smash.jpg",
#    ),
#    EliteSkill(
#        id="skill_389",
#        display_name="Flourish",
#        skill_id=389,
#        profession=Profession.WARRIOR,
#        type=EliteSkillType.ELITE_SKILL,
#        step_name="[H]Flourish",
#        capture_function="Flourish",
#        start_map=,
#        icon_filename="[389] - Flourish.jpg",
    ),
    EliteSkill(
        id="skill_889",
        display_name="Forceful Blow",
        skill_id=889,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Forceful Blow",
        capture_function="ForcefulBlow",
        start_map=272,
        icon_filename="[889] - Forceful Blow.jpg",
    ),
#    EliteSkill(
#        id="skill_372",
#        display_name="Gladiator's Defense",
#        skill_id=372,
#        profession=Profession.WARRIOR,
#        type=EliteSkillType.ELITE_SKILL,
#        step_name="[H]Gladiator's Defense",
#        capture_function="GladiatorsDefense",
#        start_map=,
#        icon_filename="[372] - Gladiator's Defense.jpg",
#    ),
    EliteSkill(
        id="skill_1406",
        display_name="Headbutt",
        skill_id=1406,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Headbutt",
        capture_function="Headbutt",
        start_map=381,
        icon_filename="[1406] - Headbutt.jpg",
    ),
    EliteSkill(
        id="skill_381",
        display_name="Hundred Blades",
        skill_id=381,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Hundred Blades",
        capture_function="HundredBlades",
        start_map=284,
        icon_filename="[381] - Hundred Blades.jpg",
    ),
    EliteSkill(
        id="skill_1694",
        display_name="Magehunter Strike",
        skill_id=1694,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Magehunter Strike",
        capture_function="MagehunterStrike",
        start_map=424,
        icon_filename="[1694] - Magehunter Strike.jpg",
    ),
    EliteSkill(
        id="skill_1697",
        display_name="Magehunter's Smash",
        skill_id=1697,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Magehunter's Smash",
        capture_function="MagehuntersSmash",
        start_map=476,
        icon_filename="[1697] - Magehunter's Smash.jpg",
    ),
    EliteSkill(
        id="skill_892",
        display_name="Quivering Blade",
        skill_id=892,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Quivering Blade",
        capture_function="QuiveringBlade",
        start_map=303,
        icon_filename="[892] - Quivering Blade.jpg",
    ),
    EliteSkill(
        id="skill_1408",
        display_name="Rage of the Ntouka",
        skill_id=1408,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Rage of the Ntouka",
        capture_function="RageoftheNtouka",
        start_map=387,
        icon_filename="[1408] - Rage of the Ntouka.jpg",
    ),
    EliteSkill(
        id="skill_1146",
        display_name="Shove",
        skill_id=1146,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Shove",
        capture_function="Shove",
        start_map=77,
        icon_filename="[1146] - Shove.jpg",
    ),
    EliteSkill(
        id="skill_329",
        display_name="Skull Crack",
        skill_id=329,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Skull Crack",
        capture_function="SkullCrack",
        start_map= 643,
        icon_filename="[329] - Skull Crack.jpg",
    ),
    EliteSkill(
        id="skill_1698",
        display_name="Soldier's Stance",
        skill_id=1698,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Soldier's Stance",
        capture_function="SoldiersStance",
        start_map=545,
        icon_filename="[1698] - Soldier's Stance.jpg",
    ),
    EliteSkill(
        id="skill_1701",
        display_name="Steady Stance",
        skill_id=1701,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Steady Stance",
        capture_function="SteadyStance",
        start_map=407,
        icon_filename="[1701] - Steady Stance.jpg",
    ),
    EliteSkill(
        id="skill_992",
        display_name="Triple Chop",
        skill_id=992,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Triple Chop",
        capture_function="TripleChop",
        start_map=303,
        icon_filename="[992] - Triple Chop.jpg",
    ),
    EliteSkill(
        id="skill_374",
        display_name="Warrior's Endurance",
        skill_id=374,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Warrior's Endurance",
        capture_function="WarriorsEndurance",
        start_map=117,
        icon_filename="[374] - Warrior's Endurance.jpg",
    ),
    EliteSkill(
        id="skill_888",
        display_name="Whirling Axe",
        skill_id=888,
        profession=Profession.WARRIOR,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Whirling Axe",
        capture_function="WhirlingAxe",
        start_map=273,
        icon_filename="[888] - Whirling Axe.jpg",
    ),
    EliteSkill(
        id="skill_270",
        display_name="Life Barrier",
        skill_id=270,
        profession=Profession.MONK,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Life Barrier",
        capture_function="LifeBarrier",
        start_map=24,
        icon_filename="[270] - Life Barrier.jpg",
    ), 
    EliteSkill(
        id="skill_1649",
        display_name="Way of the Assassin",
        skill_id=1649,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Way of the Assassin",
        capture_function="Way_of_theAssassin",
        start_map=424,
        icon_filename="[1649] - Way of the Assassin.jpg",
    ), 
    EliteSkill(
        id="skill_1029",
        display_name="Dark Apostasy",
        skill_id=1029,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Dark Apostasy",
        capture_function="Dark_Apostasy",
        start_map=230,
        icon_filename="[1029] - Dark Apostasy.jpg",
    ), 
    EliteSkill(
        id="skill_1030",
        display_name="Locust's Fury",
        skill_id=1030,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Locust's Fury",
        capture_function="Locusts_Fury",
        start_map=129,
        icon_filename="[1030] - Locust's Fury.jpg",
    ), 
    EliteSkill(
        id="skill_1045",
        display_name="Palm Strike",
        skill_id=1045,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Palm Strike",
        capture_function="Palm_Strike",
        start_map=303,
        icon_filename="[1045] - Palm Strike.jpg",
    ), 
    EliteSkill(
        id="skill_1034",
        display_name="Seeping Wound",
        skill_id=1034,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Seeping Wound",
        capture_function="Seeping_Wound",
        start_map=51,
        icon_filename="[1034] - Seeping Wound.jpg",
    ), 
    EliteSkill(
        id="skill_1042",
        display_name="Flashing Blades",
        skill_id=1042,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Flashing Blades",
        capture_function="Flashing_Blades",
        start_map=220,
        icon_filename="[1042] - Flashing Blades.jpg",
    ),
    EliteSkill(
        id="skill_1640",
        display_name="Fox's Promise",
        skill_id=1640,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Fox's Promise",
        capture_function="Foxs_Promise",
        start_map=396,
        icon_filename="[1640] - Fox's Promise.jpg",
    ), 
    EliteSkill(
        id="skill_1057",
        display_name="Psychic Instability",
        skill_id=1057,
        profession=Profession.MESMER,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Psychic Instability",
        capture_function="Psychic_Instability",
        start_map=277,
        icon_filename="[1057] - Psychic Instability.jpg",
    ), 
    EliteSkill(
        id="skill_771",
        display_name="Aura of Displacement",
        skill_id=771,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Aura of Displacement",
        capture_function="Aura_of_Displacement",
        start_map=77,
        icon_filename="[771] - Aura of Displacement.jpg",
    ), 
    EliteSkill(
        id="skill_570",
        display_name="Mark of Insecurity",
        skill_id=570,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Mark of Insecurity",
        capture_function="Mark_of_Insecurity",
        start_map=559,
        icon_filename="[570] - Mark of Insecurity.jpg",
    ), 
    EliteSkill(
        id="skill_1642",
        display_name="Hidden Caltrops",
        skill_id=1642,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Hidden Caltrops",
        capture_function="Hidden_Caltrops",
        start_map=424,
        icon_filename="[1642] - Hidden Caltrops.jpg",
    ), 
    EliteSkill(
        id="skill_1643",
        display_name="Assault Enchantments",
        skill_id=1643,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Assault Enchantments",
        capture_function="Assault_Enchantments",
        start_map=450,
        icon_filename="[1643] - Assault Enchantments.jpg",
    ), 
    EliteSkill(
        id="skill_1654",
        display_name="Shadow Meld",
        skill_id=1654,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Shadow Meld",
        capture_function="Shadow_Meld",
        start_map=477,
        icon_filename="[1654] - Shadow Meld.jpg",
    ), 
    EliteSkill(
        id="skill_1644",
        display_name="Wastrel's Collapse",
        skill_id=1644,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Wastrel's Collapse",
        capture_function="Wastrel's_Collapse",
        start_map=407,
        icon_filename="[1644] - Wastrel's Collapse.jpg",
    ), 
    EliteSkill(
        id="skill_1635",
        display_name="Golden Skull Strike",
        skill_id=1635,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Golden Skull Strike",
        capture_function="Golden_Skull_Strike",
        start_map=496,
        icon_filename="[1635] - Golden Skull Strike.jpg",
    ), 
    EliteSkill(
        id="skill_988",
        display_name="Temple Strike",
        skill_id=988,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Temple Strike",
        capture_function="Temple_Strike",
        start_map=289,
        icon_filename="[988] - Temple Strike.jpg",
    ), 
    EliteSkill(
        id="skill_781",
        display_name="Moebius Strike",
        skill_id=781,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Moebius Strike",
        capture_function="Moebius_Strike",
        start_map=130,
        icon_filename="[781] - Moebius Strike.jpg",
    ), 
    EliteSkill(
        id="skill_801",
        display_name="Shroud of Silence",
        skill_id=801,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Shroud of Silence",
        capture_function="Shroud_of_Silence",
        start_map=226,
        icon_filename="[801] - Shroud of Silence.jpg",
    ), 
    EliteSkill(
        id="skill_827",
        display_name="Siphon Strength",
        skill_id=827,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Siphon Strength",
        capture_function="Siphon_Strength",
        start_map=288,
        icon_filename="[827] - Siphon Strength.jpg",
    ), 
    EliteSkill(
        id="skill_987",
        display_name="Way of the Empty Palm",
        skill_id=987,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Way of the Empty Palm",
        capture_function="Way_of_the_Empty_Palm",
        start_map=273,
        icon_filename="[987] - Way of the Empty Palm.jpg",
    ),
    EliteSkill(
        id="skill_799",
        display_name="Beguiling Haze",
        skill_id=799,
        profession=Profession.ASSASSIN,
        type=EliteSkillType.ELITE_SKILL,
        step_name="[H]Beguiling Haze",
        capture_function="Beguiling_Haze",
        start_map=287,
        icon_filename="[799] - Beguiling Haze.jpg",
    ),
]

def get_elite_skill_by_id(skill_id: str) -> Optional[EliteSkill]:
    """Get a specific elite skill by its ID"""
    for skill in ELITE_SKILLS:
        if skill.id == skill_id:
            return skill
    return None

    
# ============================================================================
#region BOT CONFIGURATION
# ============================================================================

_script_settings = {
    "use_cupcake": True,
    "use_apple": True,
    "use_candy": True,
    "use_egg": True,
    "use_pies": True,
    "use_war_supplies": True,
}

bot = Botting(BOT_NAME,
              config_draw_path=True,
)

# auto_combat dummy object no longer needed - upkeepers.py now checks for HeroAI instead

# Enable Hero AI combat system
bot.Properties.Enable("hero_ai")
# auto_loot now works properly with Hero AI since upkeepers.py was fixed

# Configure party defeated handler for automatic recovery
bot.Events.OnPartyDefeatedCallback(lambda: on_party_defeated(bot))

# At the top of your file or in an init section
DefaultSkillBar = None

def SaveDefaultSkillBar():
    from Py4GWCoreLib.py4gwcorelib_src.Utils import Utils
    global DefaultSkillBar
    DefaultSkillBar = Utils.GenerateSkillbarTemplate()
    print(f"Saved default skillbar: {DefaultSkillBar}") 
    # use like this    bot.States.AddCustomState(lambda: SaveDefaultSkillBar(), "Save Default Skillbar")
    yield from Routines.Yield.wait(100)

def RestoreSkillBar():
    from Py4GWCoreLib.Skillbar import SkillBar
    global DefaultSkillBar
    if DefaultSkillBar:
        SkillBar.LoadSkillTemplate(DefaultSkillBar)
        print("Restored default skillbar")
    # use like this    bot.States.AddCustomState(lambda: RestoreSkillBar(), "Restore Skill Bar")
    yield from Routines.Yield.wait(100)

def EquipEliteCaptureSkillBar(): 
    global bot

    profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
    if profession == "Dervish":
        yield from Routines.Yield.Skills.LoadSkillbar("OgWiIwsMpBsLaTCAAAAAAAAAA") #done
    elif profession == "Paragon":
        yield from Routines.Yield.Skills.LoadSkillbar("OQWBIMpBsLaTCAAAAAAAAAA")  #done
    elif profession == "Elementalist":
        yield from Routines.Yield.Skills.LoadSkillbar("OgVCwswkGwuoNJAAAAAAAAAA")  #done
    elif profession == "Monk":    
        yield from Routines.Yield.Skills.LoadSkillbar("OwUSIYITaA7i2kAAAAAAAAAA")   #Done
    elif profession == "Warrior":    
        yield from Routines.Yield.Skills.LoadSkillbar("OQUSEZBTaA7i2kAAAAAAAAAA")     #Done      
    elif profession == "Necromancer":
        yield from Routines.Yield.Skills.LoadSkillbar("OAVCIsxkGwuoNJAAAAAAAAAA")  #done
    elif profession == "Mesmer":
        yield from Routines.Yield.Skills.LoadSkillbar("OQBCIMwkGwuoNJAAAAAAAAAA")     #done   
    elif profession == "Ranger":
        yield from Routines.Yield.Skills.LoadSkillbar("OgUSI4LTaA7i2kAAAAAAAAAA")   #done
    elif profession =="Assassin":
        yield from Routines.Yield.Skills.LoadSkillbar("OwViIwjMpBsLaTCAAAAAAAAAA")     #Done 
    elif profession == "Ritualist":
        yield from Routines.Yield.Skills.LoadSkillbar("OAWiIwkMpBsLaTCAAAAAAAAAA")   #done

# ============================================================================
#region BUILD SAVE/LOAD HELPERS
# ============================================================================

def GetPrimaryProfession() -> Profession:
    """Detect player's current primary profession."""
    try:
        prof_name, _ = Agent.GetProfessionNames(Player.GetAgentID())
        for prof in Profession:
            if prof.value == prof_name:
                return prof
    except:
        pass
    return Profession.WARRIOR  # Default fallback

def SaveCurrentBuild():
    """Save player's current skill template."""
    global _saved_build_template
    try:
        _saved_build_template = Utils.GenerateSkillbarTemplate()
        if _saved_build_template:
            ConsoleLog("Build", f"Current build saved: {_saved_build_template[:30]}...", log=True)
        else:
            ConsoleLog("Build", "ERROR: GenerateSkillbarTemplate returned None/empty", log=True)
    except Exception as e:
        ConsoleLog("Build", f"Failed to save build: {e}", log=True)
        import traceback
        ConsoleLog("Build", traceback.format_exc(), log=True)
    yield from Routines.Yield.wait(500)

def LoadSecondaryBuild(profession: Profession):
    """Load build with specific profession as secondary."""
    global _saved_build_template
    
    current_primary = GetPrimaryProfession()
    ConsoleLog("Build", f"Primary: {current_primary.value}, Target: {profession.value}", log=True)
    
    # Look up build for current primary + target secondary
    primary_builds = SECONDARY_BUILDS.get(current_primary)
    
    # Debug: Check what we got
    if primary_builds is None:
        ConsoleLog("Build", f"No entry for {current_primary.value} in SECONDARY_BUILDS", log=True)
        yield
        return
    
    if not isinstance(primary_builds, dict):
        ConsoleLog("Build", f"ERROR: Expected dict for {current_primary.value}, got {type(primary_builds).__name__}", log=True)
        yield
        return
    
    # If target is already primary, load P/P build (e.g., R/R for Ranger)
    # This ensures Signet of Capture is loaded even when no switch needed
    target_secondary = profession if profession == current_primary else profession
    
    template = primary_builds.get(target_secondary)
    if template and len(template) > 10:
        try:
            SkillBar.LoadSkillTemplate(template)
            if profession == current_primary:
                ConsoleLog("Build", f"Loaded {current_primary.value}/{current_primary.value} build with Signet of Capture", log=True)
            else:
                ConsoleLog("Build", f"Loaded {current_primary.value}/{profession.value} build", log=True)
            yield from Routines.Yield.wait(2000)  # Wait for skillbar to load
        except Exception as e:
            ConsoleLog("Build", f"Failed to load build: {e}", log=True)
            yield
    else:
        ConsoleLog("Build", f"No {current_primary.value}/{target_secondary.value} build configured", log=True)
        yield

def RestoreSavedBuild():
    """Restore original build after capture."""
    global _saved_build_template
    if _saved_build_template:
        try:
            ConsoleLog("Build", f"Restoring build: {_saved_build_template[:30]}...", log=True)
            SkillBar.LoadSkillTemplate(_saved_build_template)
            ConsoleLog("Build", "Restored original build", log=True)
            yield from Routines.Yield.wait(2000)
        except Exception as e:
            ConsoleLog("Build", f"Failed to restore build: {e}", log=True)
            import traceback
            ConsoleLog("Build", traceback.format_exc(), log=True)
            yield
    else:
        ConsoleLog("Build", "ERROR: No saved build to restore (_saved_build_template is None/empty)", log=True)
        yield

def RecordStartingMap(map_id: int):
    """Record the starting map for return."""
    global _starting_map_id
    _starting_map_id = map_id
    ConsoleLog("Map", f"Starting map recorded: {map_id}", log=True)

def ReturnToStartingMap():
    """Travel back to recorded starting outpost."""
    global _starting_map_id
    if _starting_map_id:
        try:
            Map.Travel(_starting_map_id)
            ConsoleLog("Map", f"Returning to map {_starting_map_id}", log=True)
            yield from Routines.Yield.wait(3000)
        except Exception as e:
            ConsoleLog("Map", f"Failed to return: {e}", log=True)
            yield
    else:
        ConsoleLog("Map", "No starting map recorded", log=True)
        yield

def HasSignetOfCapture() -> bool:
    """Check if Signet of Capture (skill ID 3) is equipped in the skill bar."""
    try:
        for slot in range(1, 9):
            skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
            if skill_data and skill_data.id == 3:
                return True
        return False
    except:
        return False

def CheckSignetOfCapture():
    """Coroutine to check for Signet of Capture and warn if missing."""
    if not HasSignetOfCapture():
        ConsoleLog("Signet", "WARNING: Signet of Capture not found in skill bar!", log=True)
        ConsoleLog("Signet", "Please equip Signet of Capture before starting capture.", log=True)
        # Could add dialog popup here if needed
    yield

def CheckMapUnlocked(map_id: int, map_name: str = "") -> bool:
    """Check if a map/outpost is unlocked. Returns True if unlocked, False otherwise."""
    try:
        if not Map.IsMapUnlocked(map_id):
            name = map_name if map_name else f"Map {map_id}"
            ConsoleLog("Capture", f"ERROR: {name} is not unlocked! Cannot proceed with capture.", log=True)
            return False
        return True
    except:
        return True  # Assume unlocked if check fails

def IsSignetUnlocked() -> bool:
    """Check if Signet of Capture (skill ID 3) is unlocked on the account."""
    try:
        return GLOBAL_CACHE.SkillBar.IsSkillUnlocked(3) or GLOBAL_CACHE.SkillBar.IsSkillLearnt(3)
    except:
        return False

def BuySignetOfCapture():
    """Travel to Eye of the North and buy Signet of Capture."""
    # Note: Allow buying even if unlocked - players can stack signets
    if IsSignetUnlocked():
        ConsoleLog("Signet", "Signet of Capture already unlocked - buying another...", log=True)
    
    # Record current map before traveling
    starting_map = Map.GetMapID()
    ConsoleLog("Signet", f"Recording starting map: {starting_map}", log=True)
    
    ConsoleLog("Signet", "Buying Signet of Capture from Eye of the North...", log=True)
    
    # Withdraw 1000 gold to ensure we can buy the skill
    ConsoleLog("Signet", "Withdrawing 1000 gold from storage...", log=True)
    yield from Routines.Yield.Items.WithdrawGold(target_gold=1000, deposit_all=True)
    
    # Leave party before traveling (some towns don't support 8-man)
    bot.Party.LeaveParty()
    yield from Routines.Yield.wait(500)
    
    # Travel to Eye of the North (map 642)
    yield from bot.Map._coro_travel(target_map_id=642)
    yield from Routines.Yield.wait(2000)
    
    # Move to Micah (skill trainer at -3551, 2341) and open dialog
    yield from bot.Move._coro_xy_and_dialog(-3551.00, 2341.00, 0x84)
    yield from Routines.Yield.wait(500)
    
    # Buy Signet of Capture (skill ID 3)
    yield from Routines.Yield.Player.BuySkill(3)
    yield from Routines.Yield.wait(500)
    
    ConsoleLog("Signet", "Signet of Capture purchased!", log=True)
    
    # Travel back to starting map
    ConsoleLog("Signet", f"Returning to map {starting_map}...", log=True)
    # Leave party before traveling (some towns don't support 8-man)
    bot.Party.LeaveParty()
    yield from Routines.Yield.wait(500)
    yield from bot.Map._coro_travel(target_map_id=starting_map)
    yield from Routines.Yield.wait(2000)
    ConsoleLog("Signet", "Returned to starting map.", log=True)
    yield

# ============================================================================
#endregion


# ConfigureAggressiveEnv and ConfigurePacifistEnv functions are defined above with proper Hero AI integration

def CheckProofOfTriumph():
    """Check if Proof of Triumph (item ID 38031) is in inventory or storage"""
    global bot
    
    # Check inventory first
    inventory_count = GLOBAL_CACHE.Inventory.GetModelCount(38031)
    if inventory_count > 0:
        ConsoleLog("Proof of Triumph", f"Found {inventory_count} Proof of Triumph in inventory", log=True)
        return True
    
    # Check storage
    storage_count = GLOBAL_CACHE.Inventory.GetModelCountInStorage(38031)
    if storage_count > 0:
        ConsoleLog("Proof of Triumph", f"Found {storage_count} Proof of Triumph in storage", log=True)
        return True
    
    ConsoleLog("Proof of Triumph", "No Proof of Triumph found in inventory or storage", log=True)
    return False

def WithdrawProofOfTriumph():
    """Withdraw Proof of Triumph only if not already in inventory"""
    global bot
    
    if GLOBAL_CACHE.Inventory.GetModelCount(38031) > 0:
        ConsoleLog("Proof of Triumph", "Proof of Triumph already in inventory, skipping withdrawal", log=True)
        return
    
    if GLOBAL_CACHE.Inventory.GetModelCountInStorage(38031) > 0:
        ConsoleLog("Proof of Triumph", "Withdrawing Proof of Triumph from storage", log=True)
        yield from Routines.Yield.Items.WithdrawItems(38031, 1)
    else:
        ConsoleLog("Proof of Triumph", "ERROR: No Proof of Triumph found in storage!", log=True)

def DepositProofOfTriumph():
    """Deposit Proof of Triumph if in inventory"""
    global bot
    
    if GLOBAL_CACHE.Inventory.GetModelCount(38031) > 0:
        ConsoleLog("Proof of Triumph", "Depositing Proof of Triumph to storage", log=True)
        yield from Routines.Yield.Items.DepositItems([38031])
    else:
        ConsoleLog("Proof of Triumph", "No Proof of Triumph in inventory to deposit", log=True)


def AdvancedHeroTeam():
    party_size = Map.GetMaxPartySize()

    # Define skill templates by hero type
    skill_template_map = {
        HeroType.Gwen: "OQhkAsC8gFKzJIHM9MdDBcaG4iB",
        HeroType.Norgu: "OQhkAoC8AGKyJM95gprBZARcxA",
        HeroType.Vekk: "OgVDI8gsS5AnATPmOHgCAZAFBA",
        HeroType.MasterOfWhispers: "OABDUshnSyBVBoBKgbhVVfCWCA",
        HeroType.Olias: "OAhjQoGYIP3hhWVVaO5EeDTqNA",
        HeroType.Ogden: "OwUUMsG/E4SNgbE3N3ETfQgZAMEA",
        HeroType.Razah: "OAWjMMgMJPYTr3jLcCNdmZgeAA",
    }

    hero_list = []
    hero_list.extend([HeroType.Gwen, HeroType.Norgu, HeroType.Vekk, HeroType.MasterOfWhispers, HeroType.Olias, HeroType.Ogden, HeroType.Razah])

    # Add all heroes
    for hero in hero_list:
        GLOBAL_CACHE.Party.Heroes.AddHero(hero.value)
        ConsoleLog("addhero", f"Added Hero: {hero.name}", log=False)

    # Single wait for all heroes to join
    yield from Routines.Yield.wait(1000)

    # Load skillbars by checking which hero is actually at each position
    party_hero_count = GLOBAL_CACHE.Party.GetHeroCount()
    for position in range(1, party_hero_count + 1):
        hero_agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(position)
        if hero_agent_id > 0:
            hero_id = GLOBAL_CACHE.Party.Heroes.GetHeroIDByAgentID(hero_agent_id)
            if hero_id > 0:
                hero = HeroType(hero_id)
                if hero in skill_template_map:
                    skill_template = skill_template_map[hero]
                    GLOBAL_CACHE.SkillBar.LoadHeroSkillTemplate(position, skill_template)
                yield from Routines.Yield.wait(500)

    # Set all heroes to Guard mode
    for position in range(1, party_hero_count + 1):
        hero_agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(position)
        if hero_agent_id > 0:
            GLOBAL_CACHE.Party.Heroes.SetHeroBehavior(hero_agent_id, 1)  # Guard mode
            yield from Routines.Yield.wait(100)
    
    # Activate complete Hero AI combat system to replace old auto_combat
    bot.ResetHeroAICombatState(
        active=True,
        following=True,      # Heroes follow player
        avoidance=True,      # Heroes avoid AoE and danger
        looting=True,        # Heroes help with looting
        targeting=True,      # Heroes auto-target enemies
        combat=True,         # Heroes engage in combat
        skills=True          # Heroes use their skills automatically
    )
    
    ConsoleLog("Hero AI", "Hero AI combat system fully activated", log=True)

def DisableHeroAI():
    """Disable Hero AI combat system"""
    global bot
    bot.ResetHeroAICombatState(
        active=False,
        following=False,
        avoidance=False,
        looting=False,
        targeting=False,
        combat=False,
        skills=False
    )
    ConsoleLog("Hero AI", "Hero AI combat system disabled", log=True)

def ConfigureAggressiveEnv(bot: Botting) -> None:
    bot.Templates.Aggressive()
    bot.Events.OnPartyMemberDeadBehindCallback(lambda: bot.Templates.Routines.OnPartyMemberDeathBehind())

def ConfigurePacifistEnv(bot: Botting) -> None:
    bot.Templates.Pacifist()

def DunkoroHeroTeam():
    party_size = Map.GetMaxPartySize()

    # Define skill templates by hero type
    skill_template_map = {
        HeroType.Gwen: "OQhkAsC8gFKzJIHM9MdDBcaG4iB",
        HeroType.Norgu: "OQhkAoC8AGKyJM95gprBZARcxA",
        HeroType.ZhedShadowhoof: "OgVDI8gsS5AnATPmOHgCAZAFBA",
        HeroType.MasterOfWhispers: "OABDUshnSyBVBoBKgbhVVfCWCA",
        HeroType.Olias: "OAhjQoGYIP3hhWVVaO5EeDTqNA",
        HeroType.Dunkoro: "OwUUMsG/E4SNgbE3N3ETfQgZAMEA",
        HeroType.Razah: "OAWjMMgMJPYTr3jLcCNdmZgeAA",
    }

    hero_list = []
    hero_list.extend([HeroType.Gwen, HeroType.Norgu, HeroType.ZhedShadowhoof, HeroType.MasterOfWhispers, HeroType.Olias, HeroType.Dunkoro, HeroType.Razah])

    # Add all heroes
    for hero in hero_list:
        GLOBAL_CACHE.Party.Heroes.AddHero(hero.value)
        ConsoleLog("addhero", f"Added Hero: {hero.name}", log=False)

    # Single wait for all heroes to join
    yield from Routines.Yield.wait(1000)

    # Load skillbars by checking which hero is actually at each position
    party_hero_count = GLOBAL_CACHE.Party.GetHeroCount()
    for position in range(1, party_hero_count + 1):
        hero_agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(position)
        if hero_agent_id > 0:
            hero_id = GLOBAL_CACHE.Party.Heroes.GetHeroIDByAgentID(hero_agent_id)
            if hero_id > 0:
                hero = HeroType(hero_id)
                if hero in skill_template_map:
                    skill_template = skill_template_map[hero]
                    GLOBAL_CACHE.SkillBar.LoadHeroSkillTemplate(position, skill_template)
                yield from Routines.Yield.wait(500)

    # Set all heroes to Guard mode
    for position in range(1, party_hero_count + 1):
        hero_agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(position)
        if hero_agent_id > 0:
            GLOBAL_CACHE.Party.Heroes.SetHeroBehavior(hero_agent_id, 1)  # Guard mode
            yield from Routines.Yield.wait(100)

# ============================================================================
#region ELITE SKILL CAPTURE FUNCTIONS
# ============================================================================

def get_skill_attribute_offset(skill_id: int) -> int:
    """Get attribute offset for a given skill ID"""
    try:
        attribute = GLOBAL_CACHE.Skill.Attribute.GetAttribute(skill_id)
        return attribute.attribute_id
    except:
        return 1  # Default fallback

def ClickSkillFrame(skill_id: int):
    """Universal skill capture function"""
    skill_capture_grandparent = 2374896298
    skill_capture_offset = [3, 0, 0, 0]
    
    # Get correct attribute offset dynamically
    attribute_offset = get_skill_attribute_offset(skill_id)
    skill_id_offset = [attribute_offset, 1, skill_id, 0]
    
    # Get specific skill frame
    skill_frame = UIManager.GetChildFrameID(
        skill_capture_grandparent, 
        skill_capture_offset + skill_id_offset
    )
    
    ConsoleLog("ClickSkillFrame", f"Looking for skill frame {skill_id} with offset {skill_id_offset}, got frame ID: {skill_frame}", log=True)
    
    if UIManager.FrameExists(skill_frame):
        ConsoleLog("ClickSkillFrame", f"Skill frame {skill_id} exists, clicking it", log=True)
        # Use Game.enqueue like the Factions Character Leveler example
        Game.enqueue(lambda fid=skill_frame: UIManager.TestMouseClickAction(fid, 0, 0))
        yield from Routines.Yield.wait(200)
        
        # Wait 1 second before clicking capture button
        yield from Routines.Yield.wait(1000)
        
        # Click capture button using GetChildFrameID with offset 0
        capture_frame = UIManager.GetChildFrameID(2374896298, [0])
        
        if UIManager.FrameExists(capture_frame):
            ConsoleLog("ClickSkillFrame", f"Capture button exists, clicking it", log=True)
            UIManager.FrameClick(capture_frame)
            yield from Routines.Yield.wait(200)
        else:
            ConsoleLog("ClickSkillFrame", f"ERROR: Capture button (frame 0) not found!", log=True)
    else:
        ConsoleLog("ClickSkillFrame", f"ERROR: Skill frame {skill_id} not found! Check if Signet of Capture UI is open", log=True)

def EnergySurge():
    bot.States.AddHeader("Energy Surge")
    target_prof = Profession.MESMER
    start_map = 414
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Mesmer Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-833, 4980, 419)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-20867.55, -9056.55)
    bot.Move.XY(-19999.87, -4514.18)
    bot.Move.XY(-22300.36, -7250.76)
    bot.Wait.UntilOnCombat()
    bot.Move.XY(-22435, -6718)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(39), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def PiousRenewal():
    bot.States.AddHeader("Pious Renewal")
    target_prof = Profession.DERVISH
    start_map = 493
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Dervish Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(DunkoroHeroTeam, "Dunkoro Hero Team")
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndDialog(-1508.00, 16739.00, 0x81)
    bot.Move.XYAndDialog(-1508.00, 16739.00, 0x84)
    bot.Wait.ForTime(10000)
    bot.Move.XY(-14816, -11739)
    bot.Move.XY(-14924, -9280)
    bot.Move.XY(-14605, -8548)
    bot.Move.XY(-14501, -7181)
    bot.Move.XY(-14219, -5434)
    bot.Move.XY(-12416, -5421)
    bot.Move.XY(-12077, -5155)
    bot.Move.XY(-8853, -4123)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1499), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def BloodIsPower():
    bot.States.AddHeader("Blood is Power")
    target_prof = Profession.NECROMANCER
    start_map = 393
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Necro Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-6066, -1583, 392)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-1695, -374)
    bot.Move.XY(1297, 2931)
    bot.Move.XY(3624, 5284)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(119), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def VowOfStrengthLocals():
    bot.States.AddHeader("Vow of Strength Locals")
    target_prof = Profession.DERVISH
    start_map = 479
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Dervish Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndDialog(22884, 7641, 0x84)
    bot.Wait.ForMapLoad(target_map_id=447)
    bot.Wait.ForTime(100)
    bot.Move.XY(14435, 1664)
    bot.Move.XY(14871, 2611)
    bot.Move.XY(9758.36, -1667.53)
    bot.Wait.UntilOnCombat()
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3) #Signet of Capture
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1759), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def Ineptitude():
    bot.States.AddHeader("Ineptitude")
    target_prof = Profession.MESMER
    start_map = 641
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Mesmer Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(19072, -10584, 572)
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndDialog(18975.00, -7661.00, 0x84)
    bot.Move.XY(13678.05, -7953.19)
    bot.Move.XY(7806.59, -8390.89)
    bot.Move.XY(2419.74, -10806.55)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(47), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def Migraine():
    bot.States.AddHeader("Migraine")
    target_prof = Profession.MESMER
    start_map = 638
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Mesmer Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XY(-9738.66, -21663.27)
    bot.Move.XYAndExitMap(-9605, -19938, 558)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-11074.98, -14619.83)
    bot.Move.XY(-11022.09, -10608.68)
    bot.Move.XY(-10086.13, -6514.95)
    bot.Move.XY(-11156, -2359)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(53), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def SpoilVictor():
    bot.States.AddHeader("Spoil Victor")
    target_prof = Profession.NECROMANCER
    start_map = 230
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Necro Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XY(-4247.07, 3886.89)
    bot.Move.XYAndExitMap(-4663, 4805, 209)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-19692, -6351)
    bot.Move.XY(-23447, -4835)
    bot.Move.XY(-26800.49, -3882.72)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1066), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def SignetOfSpirits():
    bot.States.AddHeader("Signet of Spirits")
    target_prof = Profession.RITUALIST
    start_map = 388
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Ritualist Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-8152, -8703, 210)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(10536, 17699)
    bot.Move.XY(3726, 7910)
    bot.Move.XY(-10086.13, -6514.95)
    bot.Move.XY(6051.00, 4126.00)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1239), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def SpitefulSpirit():
    bot.States.AddHeader("Spiteful Spirit")
    target_prof = Profession.NECROMANCER
    start_map = 155
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Necro Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(7565, -45115, 26)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-18688, 12186)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(121), "Click Skill Frame")
    REAL_CAPTURED_SKILLS = [121]
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(SpitefulSpirit, "[H]Spiteful Spirit")
    yield  
    
def MistForm():
    bot.States.AddHeader("Mist Form")
    target_prof = Profession.ELEMENTALIST
    start_map = 155
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Ele Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(7565, -45115, 26)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-18688, 12186)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(236), "Click Skill Frame")
    REAL_CAPTURED_SKILLS = [236]
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(MistForm, "[H]Mist Form")
    yield

def SignetOfJudgement():
    bot.States.AddHeader("Signet of Judgement")
    target_prof = Profession.MONK
    start_map = 155
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(7565, -45115, 26)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-18688, 12186)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(294), "Click Skill Frame")
    REAL_CAPTURED_SKILLS = [294]
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(SignetOfJudgement, "[H]Signet of Judgement")
    yield

def IllusionaryWeaponry():
    bot.States.AddHeader("Illusionary Weaponry")
    target_prof = Profession.MESMER
    start_map = 155
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Mesmer Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(7565, -45115, 26)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-18688, 12186)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(33), "Click Skill Frame")
    REAL_CAPTURED_SKILLS = [33]
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(IllusionaryWeaponry, "[H]Illusionary Weaponry")
    yield

def ShadowForm():
    bot.States.AddHeader("Shadow Form")
    target_prof = Profession.ASSASSIN
    start_map = 284
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Sin Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XY(11664.37, -18732.13)
    bot.Move.XYAndExitMap(11637, -20480, 256)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(12054, 10092)
    bot.Move.XY(11646.67, 5173.43)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(826), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def ShadowFormWoC():
    bot.States.AddHeader("Shadow Form - WoC")
    target_prof = Profession.ASSASSIN
    start_map = 284
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Sin Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XY(11664.37, -18732.13)
    bot.Move.XYAndExitMap(11637, -20480, 256)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(12054, 10092)
    bot.Move.XY(12438.57, -2243.74)
    bot.Move.XY(12385.90, -5115.57)
    bot.Move.XY(9502.17, -7110.23)
    bot.Move.XY(6698.81, -7094.89)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(826), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield  

def BroadHeadArrow():
    bot.States.AddHeader("Broadhead Arrow")
    target_prof = Profession.RANGER
    start_map = 284
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Ranger Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XY(11664.37, -18732.13)
    bot.Move.XYAndExitMap(11637, -20480, 256)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(12054, 10092)
    bot.Move.XY(12438.57, -2243.74)
    bot.Move.XY(12385.90, -5115.57)
    bot.Move.XY(9502.17, -7110.23)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1198), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def SoulTwisting():
    bot.States.AddHeader("Soul Twisting")
    target_prof = Profession.RITUALIST
    start_map = 298
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Ritualist Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XY(-11511, -4836)
    bot.Move.XYAndExitMap(-14412, -8139, 205)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(18907.74, 13014.72)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1240), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def PrimalRage():
    bot.States.AddHeader("Primal Rage")
    target_prof = Profession.WARRIOR
    start_map = 298
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XY(-11511, -4836)
    bot.Move.XYAndExitMap(-14412, -8139, 205)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(18907.74, 13014.72)
    bot.Move.XY(16910.72, 11775.83)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(831), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def ShadowPrison():
    bot.States.AddHeader("Shadow Prison")
    target_prof = Profession.ASSASSIN
    start_map = 398
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Sin Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-4284, -615, 437)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(18745.25, 10039.62)
    bot.Move.XY(16146.25, 5758.00)
    bot.Move.XY(15450, 1269)
    bot.Move.XY(12274, -1577)
    bot.Move.XY(11634.43, 3894.38)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1652), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def SoldiersFury():
    bot.States.AddHeader("Soldier's Fury")
    target_prof = Profession.PARAGON
    start_map = 438
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Paragon Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-14638, 2927, 437)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-10841.79, 4156.87)
    bot.Wait.ForTime(8000)
    bot.Move.XYAndInteractGadget(-10867.00, 4322.00)
    bot.Wait.ForTime(2000)
    bot.Move.XY(-2487, 8247)
    bot.Move.XY(-1621, 12022)
    bot.Move.XY(-59.74, 15527.17)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1773), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def ObsidianFlesh():
    bot.States.AddHeader("Obsidian Flesh")
    target_prof = Profession.ELEMENTALIST
    start_map = 438
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Ele Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-14638, 2927, 437)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-11118, 3848)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractGadget(-10867.00, 4322.00)
    bot.Wait.ForTime(2000)
    bot.Move.XY(-2675.33, 6765.78)
    bot.Move.XY(-300, 2474)
    bot.Move.XY(5329.65, 5429.12)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(218), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def Eviscerate():
    bot.States.AddHeader("Eviscerate")
    target_prof = Profession.WARRIOR
    start_map = 650
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-27552, 16937, 482)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(12886.46, -15018.20)
    bot.Move.XY(9134.72, -13706.59)
    bot.Move.XY(4565.56, -13479.55)
    bot.Move.XY(2733.14, -15091.32)
    bot.Move.XY(10.51, -15436.22)
    bot.Move.XY(9.80, -17555.21)
    bot.Move.XY(2167.66, -18356.87)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(338), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield    

def GreaterConflagration():
    bot.States.AddHeader("Greater Conflagration")
    target_prof = Profession.RANGER
    start_map = 124
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Ranger Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Map.EnterChallenge(6000, target_map_id=start_map)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(2573, 134)
    bot.Move.XY(3009, -4916)
    bot.Wait.ForTime(7000)
    bot.Move.XY(6322, -8114)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(9299, -9728)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(7827.06, -13540.96)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(465), "Click Skill Frame")
    bot.Wait.ForTime(1000)
    REAL_CAPTURED_SKILLS = [465]
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(GreaterConflagration, "[H]Greater Conflagration")
    yield 

def AuraOfTheLich():
    bot.States.AddHeader("Aura of the Lich")
    target_prof = Profession.NECROMANCER
    start_map = 124
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Necro Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Map.EnterChallenge(6000, target_map_id=start_map)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(2573, 134)
    bot.Move.XY(3009, -4916)
    bot.Wait.ForTime(7000)
    bot.Move.XY(6322, -8114)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(9299, -9728)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(7827.06, -13540.96)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(114), "Click Skill Frame")
    bot.Wait.ForTime(1000)
    REAL_CAPTURED_SKILLS = [114]
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        # Success: Return to outpost normally like other skills
        ConsoleLog("Capture", "Aura of the Lich captured successfully!", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        # Failure: Return to start map and retry
        ConsoleLog("Capture", "Aura of the Lich capture failed, retrying...", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(AuraOfTheLich, "[H]Aura of the Lich")
    yield 

def Panic():
    bot.States.AddHeader("Panic")
    target_prof = Profession.MESMER
    start_map = 124
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Mesmer Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Map.EnterChallenge(6000, target_map_id=start_map)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(2573, 134)
    bot.Move.XY(3009, -4916)
    bot.Wait.ForTime(7000)
    bot.Move.XY(6322, -8114)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(9299, -9728)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(7827.06, -13540.96)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(52), "Click Skill Frame")
    bot.Wait.ForTime(1000)
    REAL_CAPTURED_SKILLS = [52]
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        # Success: Return to outpost normally like other skills
        ConsoleLog("Capture", "Panic captured successfully!", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        # Failure: Return to start map and retry
        ConsoleLog("Capture", "Panic capture failed, retrying...", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(Panic, "[H]Panic")
    yield 

def MindBurn():
    bot.States.AddHeader("Mind Burn")
    target_prof = Profession.ELEMENTALIST
    start_map = 124
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Ele Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Map.EnterChallenge(6000, target_map_id=start_map)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(2573, 134)
    bot.Move.XY(3009, -4916)
    bot.Wait.ForTime(7000)
    bot.Move.XY(6322, -8114)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(9299, -9728)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(7827.06, -13540.96)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(185), "Click Skill Frame")
    bot.Wait.ForTime(1000)
    REAL_CAPTURED_SKILLS = [185]
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        # Success: Return to outpost normally like other skills
        ConsoleLog("Capture", "Mind Burn captured successfully!", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        # Failure: Return to start map and retry
        ConsoleLog("Capture", "Mind Burn capture failed, retrying...", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(MindBurn, "[H]Mind Burn")
    yield 

def AssassinsPromise():
    bot.States.AddHeader("Assassin's Promise")
    target_prof = Profession.ASSASSIN
    start_map = 640
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Sin Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XY(18003.32, 16753.06)
    bot.Move.XYAndExitMap(20243, 16910, 501)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-21519, -7404)
    bot.Move.XY(-19032.91, -10978.03)
    bot.Move.XY(-20351.51, -11994.78)
    bot.Move.XY(-21815.37, -12821.15)
    bot.Move.XY(-23521.56, -11545.54)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1035), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def UnyieldingAura():
    bot.States.AddHeader("Unyielding Aura")
    target_prof = Profession.MONK
    start_map = 158
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-7392, -2618, 95)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-3347.47, 2503.66)
    bot.Move.XY(-4790.01, 2923.01)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(268), "Click Skill Frame")
    REAL_CAPTURED_SKILLS = [268]
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        # Success: Return to outpost normally like other skills
        ConsoleLog("Capture", "Unyielding Aura captured successfully!", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        # Failure: Return to start map and retry
        ConsoleLog("Capture", "Unyielding Aura capture failed, retrying...", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(UnyieldingAura, "[H]Unyielding Aura")
    yield 
    
def VictoryIsMine():
    bot.States.AddHeader("Victory is Mine")
    target_prof = Profession.WARRIOR
    start_map = 158
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-7392, -2618, 95)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-3347.47, 2503.66)
    bot.Move.XY(-4790.01, 2923.01)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(365), "Click Skill Frame")
    REAL_CAPTURED_SKILLS = [365]  
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        # Success: Return to outpost normally like other skills
        ConsoleLog("Capture", "Victory is Mine captured successfully!", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        # Failure: Return to start map and retry
        ConsoleLog("Capture", "Victory is Mine capture failed, retrying...", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(VictoryIsMine, "[H]Victory is Mine")
    yield     

def PoisonArrow():
    bot.States.AddHeader("Poison Arrow")
    target_prof = Profession.RANGER
    start_map = 158
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Ranger Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-7392, -2618, 95)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-3347.47, 2503.66)
    bot.Move.XY(-4790.01, 2923.01)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(404), "Click Skill Frame")
    REAL_CAPTURED_SKILLS = [404]
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        # Success: Return to outpost normally like other skills
        ConsoleLog("Capture", "Poison Arrow captured successfully!", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        # Failure: Return to start map and retry
        ConsoleLog("Capture", "Poison Arrow capture failed, retrying...", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(PoisonArrow, "[H]Poison Arrow")
    yield    

def PlagueSignet():
    bot.States.AddHeader("Plague Signet")
    target_prof = Profession.NECROMANCER
    start_map = 158
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Necro Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-7392, -2618, 95)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-3347.47, 2503.66)
    bot.Move.XY(-4790.01, 2923.01)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(132), "Click Skill Frame")
    REAL_CAPTURED_SKILLS = [132]
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        # Success: Return to outpost normally like other skills
        ConsoleLog("Capture", "Plague Signet captured successfully!", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        # Failure: Return to start map and retry
        ConsoleLog("Capture", "Plague Signet capture failed, retrying...", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(PlagueSignet, "[H]Plague Signet")
    yield  

def GlimmeringMark():
    bot.States.AddHeader("Glimmering Mark")
    target_prof = Profession.ELEMENTALIST
    start_map = 158
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Ele Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-7392, -2618, 95)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-3347.47, 2503.66)
    bot.Move.XY(-4790.01, 2923.01)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(227), "Click Skill Frame")
    REAL_CAPTURED_SKILLS = [227]
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        # Success: Return to outpost normally like other skills
        ConsoleLog("Capture", "Glimmering Mark captured successfully!", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        # Failure: Return to start map and retry
        ConsoleLog("Capture", "Glimmering Mark capture failed, retrying...", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(GlimmeringMark, "[H]Glimmering Mark")
    yield  


def SpellBreaker():
    bot.States.AddHeader("Spell Breaker")
    target_prof = Profession.MONK
    start_map = 155
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(6038, -41402, 91)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(1526.63, -39178.76)
    bot.Move.XY(592.26, -43048.45)
    bot.Move.XY(-2607.90, -44448.80)
    bot.Move.XY(-5678.81, -43418.43)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(273), "Click Skill Frame")
    REAL_CAPTURED_SKILLS = [273]
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        # Success: Return to outpost normally like other skills
        ConsoleLog("Capture", "Spell Breaker captured successfully!", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        # Failure: Return to start map and retry
        ConsoleLog("Capture", "Spell Breaker capture failed, retrying...", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(SpellBreaker, "[H]Spell Breaker")
    yield  

def MantraOfRecall():
    bot.States.AddHeader("Mantra of Recall")
    target_prof = Profession.MESMER
    start_map = 155
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Mesmer Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(6038, -41402, 91)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(1526.63, -39178.76)
    bot.Move.XY(592.26, -43048.45)
    bot.Move.XY(-2607.90, -44448.80)
    bot.Move.XY(-5678.81, -43418.43)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(82), "Click Skill Frame")
    REAL_CAPTURED_SKILLS = [82]
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        # Success: Return to outpost normally like other skills
        ConsoleLog("Capture", "Mantra of Recall captured successfully!", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        # Failure: Return to start map and retry
        ConsoleLog("Capture", "Mantra of Recall capture failed, retrying...", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(MantraOfRecall, "[H]Mantra of Recall")
    yield 

def MindShock():
    bot.States.AddHeader("Mind Shock")
    target_prof = Profession.ELEMENTALIST
    start_map = 155
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Ele Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(6038, -41402, 91)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(1526.63, -39178.76)
    bot.Move.XY(592.26, -43048.45)
    bot.Move.XY(-2607.90, -44448.80)
    bot.Move.XY(-5678.81, -43418.43)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(226), "Click Skill Frame")
    REAL_CAPTURED_SKILLS = [226]
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        # Success: Return to outpost normally like other skills
        ConsoleLog("Capture", "Mind Shock captured successfully!", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        # Failure: Return to start map and retry
        ConsoleLog("Capture", "Mind Shock capture failed, retrying...", log=True)
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(MindShock, "[H]Mind Shock")
    yield   

def VowOfSilence():
    bot.States.AddHeader("Vow of Silence")
    target_prof = Profession.DERVISH
    start_map = 478
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Dervish Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-4817, 5097, 444)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(22749, -5468)
    bot.Move.XY(17736, -5503)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1517), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def GlimmerOfLight():
    bot.States.AddHeader("Glimmer of Light")
    target_prof = Profession.MONK
    start_map = 421
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(26133, 17180, 386)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(3337, -12769)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1686), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def Onslaught():
    bot.States.AddHeader("Onslaught")
    target_prof = Profession.DERVISH
    start_map = 643
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Dervish Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(13591, 19148, 513)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(13883, 2057)
    bot.Move.XY(8414, -1814)
    bot.Move.XY(6336, -2122)
    bot.Move.XY(4268, -4559)
    bot.Wait.UntilOnCombat(range=Range.Nearby)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(2214, -6510)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1754), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def EbonDustAura():
    bot.States.AddHeader("Ebon Dust Aura")
    target_prof = Profession.DERVISH
    start_map = 414
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Dervish Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-820, 5147, 419)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(1457, -14317)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1760), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def AvatarOfBalthazar():
    bot.States.AddHeader("Avatar of Balthazar")
    target_prof = Profession.DERVISH
    start_map = 387
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Dervish Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-225, 4336, 436)
    bot.Move.XYAndExitMap(5342, 7723, 369)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-6895, 9930)
    bot.Move.XY(-3407, 6775)
    bot.Move.XY(-5368, 1542)
    bot.Move.XY(-4033, -1548)
    bot.Move.XY(-5894.94, -3791.20)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1518), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def AvatarOfMelandru():
    bot.States.AddHeader("Avatar of Melandru")
    target_prof = Profession.DERVISH
    start_map = 477
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Dervish Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-15535, -3754, 371)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-10797, -1490)
    bot.Move.XY(-7581, -255)
    bot.Move.XY(-4450, 1156)
    bot.Move.XY(-2573, 1103)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1522), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield    

def AvatarOfDwayna():
    bot.States.AddHeader("Avatar of Dwayna")
    target_prof = Profession.DERVISH
    start_map = 424
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Dervish Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(3805, -4766, 379)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-4402, 17178)
    bot.Move.XY(-4890, 7205)
    bot.Move.XY(-4795, -656)
    bot.Move.XY(-6963, -254)
    bot.Move.XY(-6190, -3157)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1519), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield    

def AvatarOfLyssa():
    bot.States.AddHeader("Avatar of Lyssa")
    target_prof = Profession.DERVISH
    start_map = 554
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Dervish Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-4094, 5856, 373)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-16524, -8868)
    bot.Move.XY(-9692, -7130)
    bot.Move.XY(-3158, -2143)
    bot.Move.XY(-1276, -632)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1521), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield    

def AvatarOfGrenth():
    bot.States.AddHeader("Avatar of Grenth")
    target_prof = Profession.DERVISH
    start_map = 426
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Dervish Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-4431, 5107, 380)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(16110, -13455)
    bot.Move.XY(12158, -9198)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1520), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def XinraesWeapon():
    bot.States.AddHeader("Xinrae's Weapon")
    target_prof = Profession.RITUALIST
    start_map = 496
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Ritualist Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XY(18267, -6197)
    bot.Move.XYAndExitMap(19693, -7411, 466)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-8329, -10361)
    bot.Move.XY(-6013, -5332)
    bot.Move.XY(-2935, -6277)
    bot.Move.XY(142, -9721)
    bot.Move.XY(2824, -10910)
    bot.Move.XY(14222, -3991)
    bot.Move.XY(7129, 169)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1750), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield   

def Incoming():
    bot.States.AddHeader("Incoming!")
    target_prof = Profession.PARAGON
    start_map = 414
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Paragon Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-5134, -5006, 399)
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndDialog(6243.00, 10755.00, 0x81EB01)
    bot.Move.XY(-8550, 10603)
    bot.Move.XY(-10444, 5282)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1596), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield   

def FocusedAnger():
    bot.States.AddHeader("Focused Anger")
    target_prof = Profession.PARAGON
    start_map = 427
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Paragon Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XY(-13625.08, -11257.90)
    bot.Move.XYAndDialog(-13641.00, -10375.00, 0x84)
    bot.Wait.ForMapToChange(377)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-7615, -5029)
    bot.Move.XY(-8597, -2378)
    bot.Move.XY(-7171, 1228)
    bot.Move.XY(-13321, 2245)
    bot.Move.XY(-16798, 1529)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1769), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield  

def MarkOfProtection():
    bot.States.AddHeader("Mark of Protection")
    target_prof = Profession.MONK
    start_map = 38
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-20530, -300, 113)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(11978, -12945)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(269), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield  

def PreparedShot():
    bot.States.AddHeader("Prepared Shot")
    target_prof = Profession.RANGER
    start_map = 642
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Ranger Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(1250, 800, 499)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(6931.01, 5348.25) #Johon the Oxflinger
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(269), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield  

def TogetherAsOne():
    bot.States.AddHeader("Together as One")
    target_prof = Profession.RANGER
    start_map = 650
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Ranger Build")
    ConfigureAggressiveEnv(bot)
    bot.Travel_To_Random_District(target_map_id=start_map) #Longeyes Ledge
    bot.Party.LeaveParty()
    bot.States.AddCustomState(AdvancedHeroTeam, name="Advanced Hero Team")
    bot.Items.Withdraw(38031, 1)
    bot.Move.XYAndExitMap(-21630, 12565, 649) #Exit to Gothmar Wardowns
    bot.Move.XY(-3924.91, -572.00, "Res Shrine 1")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(11385, 2228, "Res Shrine 2")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(19190, -12141, "Res Shrine 3")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XYAndExitMap(23054, -13225, target_map_name="Sacnoth Valley")
    ConfigureAggressiveEnv(bot)
    bot.Items.UseAllConsumables()
    bot.Move.XY(-16333, 16622, "Res Shrine 4")
    bot.Move.XY(-16605, 12608) #wall hugging
    bot.Move.XY(-17653, 8825) #Charr Group
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-17085, 5034) #Charr Group 2
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-13308, 4215) #Charr Group 3
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-13020, 270, "Res Shrine 5")
    bot.Move.XY(-9647, -12780, "Boss")
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(3427), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    bot.Items.Deposit(38031)
    yield

def HeroicRefrain():
    bot.States.AddHeader("Heroic Refrain")
    target_prof = Profession.PARAGON
    start_map = 440
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Paragon Build")
    ConfigureAggressiveEnv(bot)
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(AdvancedHeroTeam, name="Advanced Hero Team")
    bot.Items.Withdraw(38031, 1)
    bot.Move.XYAndExitMap(-5108, -6684, 439)
    bot.Items.UseAllConsumables()
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-7311.32, -4854.25)
    bot.Move.XY(-14444, 3610)
    bot.Move.XY(-13457.71, 9154.56)
    bot.Move.XY(-14566, 9921)
    bot.Move.XY(-15264.96, 10763.86)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(3431), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    bot.Items.Deposit(38031)
    yield

def SoulTaker():
    bot.States.AddHeader("Soul Taker")
    target_prof = Profession.NECROMANCER
    start_map = 35
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Necromancer Build")
    ConfigureAggressiveEnv(bot)
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(AdvancedHeroTeam, name="Advanced Hero Team")
    bot.States.AddCustomState(WithdrawProofOfTriumph, "Withdraw Proof of Triumph")
    bot.Move.XYAndExitMap(3807, -8332, 121)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(8100, -4094)
    bot.Move.XY(15507, -2022)
    bot.Move.XY(20600, 2121)
    bot.Move.XY(23425, 7266)
    bot.Move.XY(23994, 13745)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(3423), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    bot.Items.Deposit(38031)
    yield

def OverTheLimit():
    bot.States.AddHeader("Over The Limit")
    target_prof = Profession.ELEMENTALIST
    start_map = 35
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Elementalist Build")
    ConfigureAggressiveEnv(bot)
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(AdvancedHeroTeam, name="Advanced Hero Team")
    bot.States.AddCustomState(WithdrawProofOfTriumph, "Withdraw Proof of Triumph")
    bot.Move.XYAndExitMap(3807, -8332, 121)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(8100, -4094)
    bot.Move.XY(15507, -2022)
    bot.Move.XY(20600, 2121)
    bot.Move.XY(23425, 7266)
    bot.Move.XY(23994, 13745)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(3424), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    bot.Items.Deposit(38031)
    yield

def JudgmentStrike():
    bot.States.AddHeader("Judgment Strike")
    target_prof = Profession.MONK
    start_map = 440
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    ConfigureAggressiveEnv(bot)
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(AdvancedHeroTeam, name="Advanced Hero Team")
    bot.Items.Withdraw(38031, 1)
    bot.Move.XYAndExitMap(-5108, -6684, 439)
    bot.Items.UseAllConsumables()
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-7311.32, -4854.25)
    bot.Move.XY(-14444, 3610)
    bot.Move.XY(-13457.71, 9154.56)
    bot.Move.XY(-14566, 9921)
    bot.Move.XY(-15264.96, 10763.86)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(3425), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    bot.Items.Deposit(38031)
    yield

def TimeWard():
    bot.States.AddHeader("Time Ward")
    target_prof = Profession.MESMER
    start_map = 650
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Mesmer Build")
    ConfigureAggressiveEnv(bot)
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(AdvancedHeroTeam, name="Advanced Hero Team")
    bot.Items.Withdraw(38031, 1)
    bot.Move.XYAndExitMap(-21630, 12565, 649) #Exit to Gothmar Wardowns
    bot.Move.XY(-4163, -203, "Res Shrine 1")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(11385, 2228, "Res Shrine 2")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(19190, -12141, "Res Shrine 3")
    bot.Wait.UntilOutOfCombat()
    bot.Move.XYAndExitMap(23054, -13225, target_map_name="Sacnoth Valley")
    ConfigureAggressiveEnv(bot)
    bot.Items.UseAllConsumables()
    bot.Move.XY(-16333, 16622, "Res Shrine 4")
    bot.Move.XY(-16605, 12608)
    bot.Move.XY(-17653, 8825)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-17085, 5034)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-13308, 4215)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-13020, 270, "Res Shrine 5")
    bot.Move.XY(-9647, -12780, "Boss")
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(3422), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    bot.Items.Deposit(38031)
    yield

def VowOfRevolution():
    bot.States.AddHeader("Vow of Revolution")
    target_prof = Profession.DERVISH
    start_map = 440
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Dervish Build")
    ConfigureAggressiveEnv(bot)
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(AdvancedHeroTeam, name="Advanced Hero Team")
    bot.Items.Withdraw(38031, 1)
    bot.Move.XYAndExitMap(-5108, -6684, 439)
    bot.Items.UseAllConsumables()
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-7311.32, -4854.25)
    bot.Move.XY(-14444, 3610)
    bot.Move.XY(-13457.71, 9154.56)
    bot.Move.XY(-14566, 9921)
    bot.Move.XY(-15264.96, 10763.86)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(3430), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    bot.Items.Deposit(38031)
    yield

def SevenWeaponStance():
    bot.States.AddHeader("Seven Weapon Stance")
    target_prof = Profession.WARRIOR
    start_map = 226
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Dervish Build")
    ConfigureAggressiveEnv(bot)
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(AdvancedHeroTeam, name="Advanced Hero Team")
    bot.Items.Withdraw(38031, 1)
    bot.Move.XYAndExitMap(-5108, -6684, 439)
    bot.Items.UseAllConsumables()
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-7311.32, -4854.25)
    bot.Move.XY(-14444, 3610)
    bot.Move.XY(-13457.71, 9154.56)
    bot.Move.XY(-14566, 9921)
    bot.Move.XY(-15264.96, 10763.86)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(3426), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    bot.Items.Deposit(38031)
    yield

def WeaponsOfThreeForges():
    bot.States.AddHeader("Weapons of Three Forges")
    target_prof = Profession.RITUALIST
    start_map = 226
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Ritualist Build")
    ConfigureAggressiveEnv(bot)
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(AdvancedHeroTeam, name="Advanced Hero Team")
    bot.Items.Withdraw(38031, 1)
    bot.Move.XYAndExitMap(-9662, 3084, 233)
    bot.Items.UseAllConsumables()
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(16446, 261)
    bot.Move.XY(15194, 299)
    bot.Move.XY(14830, -2177)
    bot.Move.XY(14690, -4412)
    bot.Move.XY(12365, -5527)
    bot.Move.XY(10957, -4475)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(3429), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    bot.Items.Deposit(38031)
    yield

def ShadowTheft():
    bot.States.AddHeader("Shadow Theft")
    target_prof = Profession.ASSASSIN
    start_map = 226
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build")
    ConfigureAggressiveEnv(bot)
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.Party.LeaveParty()
    bot.States.AddCustomState(AdvancedHeroTeam, name="Advanced Hero Team")
    bot.Items.Withdraw(38031, 1)
    bot.Move.XYAndExitMap(-9662, 3084, 233)
    bot.Items.UseAllConsumables()
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(16446, 261)
    bot.Move.XY(15194, 299)
    bot.Move.XY(14830, -2177)
    bot.Move.XY(14690, -4412)
    bot.Move.XY(12365, -5527)
    bot.Move.XY(10957, -4475)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(3428), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    bot.Items.Deposit(38031)
    yield
    
def AnthemofGuidance():
    bot.States.AddHeader("Anthem of Guidance")
    target_prof = Profession.PARAGON
    start_map = 403
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Paragon Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-19999, 20176, 419)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(21678,-15544)
    bot.Move.XY(18450,-15850)
    bot.Move.XY(13733,-14403)
    bot.Move.XY(10751,-15017)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1568), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield  
    
def CripplingAnthem():
    bot.States.AddHeader("Crippling Anthem")
    target_prof = Profession.PARAGON
    start_map = 376
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Paragon Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-13955, 18251, 375)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-11625,16880)
    bot.Move.XY(-6742,14805)    
    bot.Move.XY(-4287,13281)    
    bot.Move.XY(99,11211)   
    bot.Move.XY(1009,9585)    
    bot.Move.XY(182,7959)    
    bot.Move.XY(2359,4706)
    bot.Move.XY(2855,819)      
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1554), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def AngelicBond():
    bot.States.AddHeader("Angelic Bond")
    target_prof = Profession.PARAGON
    start_map = 434
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Paragon Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndDialog(1341.00, -20346.00, 0x81)
    bot.Move.XYAndDialog(1341.00, -20346.00, 0x84)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(1205,-14695)
    bot.Move.XY(2156,-9851)
    bot.Move.XY(3357,-8887)
    bot.Move.XY(1530,-5931)
    bot.Move.XY(1530,-4479)
    bot.Move.XY(2296,-3650)
    bot.Move.XY(2253,-2209)
    bot.Move.XY(1371,-1043)
    bot.Move.XY(1377,289)
    bot.Move.XY(2538,1246)
    bot.Move.XY(1344,2875)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1587), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def AnthemofFury():
    bot.States.AddHeader("Anthem of Fury")
    target_prof = Profession.PARAGON
    start_map = 450
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Paragon Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-7826, 13976, 465)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-2677,-10998)
    bot.Move.XY(-1780,-7409)   
    bot.Move.XY(1456,-7825)   
    bot.Move.XY(5413,-13296)
    bot.Move.XY(4737,-114213)    
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1553), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def DefensiveAnthem():
    bot.States.AddHeader("Defensive Anthem")
    target_prof = Profession.PARAGON
    start_map = 387
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Paragon Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-420, 3921, 436)
    bot.Move.XYAndExitMap(5233, 7646, 369)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-4337,4183)
    bot.Move.XY(-7636,516)
    bot.Move.XY(-8233,-1156)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1555), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield  

def ItsJustaFleshWound():
    bot.States.AddHeader("It's Just a Flesh Wound.")
    target_prof = Profession.PARAGON
    start_map = 480
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Paragon Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-3265, 11584, 446)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-2498,5680)
    bot.Move.XY(-4497,5079)
    bot.Move.XY(-8191,3361)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1599), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def ThePowerIsYours():
    bot.States.AddHeader("The Power Is Yours!")
    target_prof = Profession.PARAGON
    start_map = 440
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Paragon Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(1814, -1774, 439)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-23,7080)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1782), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def SongofPurification():
    bot.States.AddHeader("Song of Purification")
    target_prof = Profession.PARAGON
    start_map = 403
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Paragon Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-18733, 13488, 402)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-16092,7570)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1570), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield
    
def SongofRestoration():
    bot.States.AddHeader("Song of Restoration")
    target_prof = Profession.PARAGON
    start_map = 428
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Paragon Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-2081, 14485, 399)
    bot.Move.XYAndDialog(-4552.00, 15863.00, 0x81)
    bot.Move.XYAndDialog(-4552.00, 15863.00, 0x84)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-10332,-11807)
    bot.Move.XY(-16846,-5635)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1771), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield
    
def CruelSpear():
    bot.States.AddHeader("Cruel Spear")
    target_prof = Profession.PARAGON
    start_map = 427
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Paragon Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(DunkoroHeroTeam, "Dunkoro Hero Team")
    bot.Move.XYAndDialog(-13955.00, -12776.00, 0x81)
    bot.Move.XYAndDialog(-13955.00, -12776.00, 0x84)
    bot.Wait.ForTime(10000)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-9584,-7325)
    bot.Wait.ForTime(30000)
    bot.Move.XYAndDialog(-9803.00, -7381.00, 0x85)
    bot.Move.XY(-4765,-77)
    bot.Move.XY(-3095,-1338)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1548), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def StunningStrike():
    bot.States.AddHeader("Stunning Strike")
    target_prof = Profession.PARAGON
    start_map = 469
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Paragon Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(8150, 18933, 468)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(6162,14210)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1602), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield
    
def CauterySignet():
    bot.States.AddHeader("Cautery Signet")
    target_prof = Profession.PARAGON
    start_map = 424
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Paragon Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(3274, -4412, 379)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-6308,13198)
    bot.Move.XY(-7341,5275)
    bot.Move.XY(-7027,-428)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1588), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield
    
def ArcaneZeal():
    bot.States.AddHeader("Arcane Zeal")
    target_prof = Profession.DERVISH
    start_map = 450
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Dervish Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndDialog(-1052.00, 10003.00, 0x82B801)
    bot.Travel_To_Random_District(target_map_id=559) #Gate of the Nightfallen Lands
    bot.Move.XYAndExitMap(-16114,18564, 465) #Nightfallen lands exit
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-3338,-3747)#remove if from Nightfallen Lands
    bot.Move.XY(-4238,5991)#remove if from Nightfallen Lands
    bot.Move.XY(-6163,11149)
    bot.Move.XY(-10069,10900)
    bot.Move.XY(-12999,13858)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1502), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield
    
def GrenthsGrasp():
    bot.States.AddHeader("Grenth's Grasp")
    target_prof = Profession.DERVISH
    start_map = 477
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Dervish Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-15545, -4092, 371)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-4241,-6589)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1756), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def ReapersSweep():
    bot.States.AddHeader("Reaper's Sweep")
    target_prof = Profession.DERVISH
    start_map = 421
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Dervish Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(22989,14206,373)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(18459,421)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1767), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def VowofStrength():
    bot.States.AddHeader("Vow of Strength")
    target_prof = Profession.DERVISH
    start_map = 376
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Dervish Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-13963,18264,375)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-14487,14623)
    bot.Move.XY(-16605,1454)
    bot.Move.XY(-9719,-11146)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1759), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def WoundingStrike():
    bot.States.AddHeader("Wounding Strike")
    target_prof = Profession.DERVISH
    start_map = 476 
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Dervish Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-4654,-2531,397)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(17786,844)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1536), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def ZealousVow():
    bot.States.AddHeader("Zealous Vow")
    target_prof = Profession.DERVISH
    start_map = 378
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Dervish Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(4856,3125,377)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(15259,14877)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1761), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield
def BlessedLight():
    bot.States.AddHeader("Blessed Light")
    target_prof = Profession.MONK
    start_map = 193
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XY(5672, -4404)
    bot.Move.XYAndExitMap(6809, -7548, 198)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(6044.61, 10084.75)
    bot.Move.XY(10710, 3833) #Healing Light 867
    bot.Move.XY(14782.42, 77.85)
    bot.Move.XY(11879.36, -3854.92)
    bot.Move.XY(16852.28, -8500.27) #Blessed Light 941
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(941), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def HealingLight():
    bot.States.AddHeader("Healing Light")
    target_prof = Profession.MONK
    start_map = 193
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XY(5672, -4404)
    bot.Move.XYAndExitMap(6809, -7548, 198)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(6044.61, 10084.75)
    bot.Move.XY(10710, 3833) #Healing Light 867
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(867), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield   

def BoonSignet():
    bot.States.AddHeader("Boon Signet")
    target_prof = Profession.MONK
    start_map = 388
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XY(-7243.40, -8111.62)
    bot.Move.XYAndExitMap(-8040, -8675, 210)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(12619.55, 21320.75)
    bot.Move.XY(8350.78, 13316.25)
    bot.Move.XY(7732.76, 11883.11)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(847), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield    

def HealersBoon():
    bot.States.AddHeader("Healer's Boon")
    target_prof = Profession.MONK
    start_map = 403
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-18733, 13488, 402)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-16092, 7570)
    bot.Move.XY(-18859.48, -543.13)
    bot.Move.XY(-18043.42, -3146.39)
    bot.Move.XY(-14355.99, -4735.46)
    bot.Move.XY(976.84, -7402.01)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1393), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield   

def PeaceandHarmony():
    bot.States.AddHeader("Peace and Harmony")
    target_prof = Profession.MONK
    start_map = 155
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(5797, -41362, 91)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(6758, -32813)
    bot.Move.XY(5448, -29156)
    bot.Move.XY(1608, -29247)
    bot.Move.XY(4823.32, -22619.05)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(266), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield  

def WithdrawHexes():
    bot.States.AddHeader("Withdraw Hexes")
    target_prof = Profession.MONK
    start_map = 389
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-5840, 14320, 200)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-7252, -2700)
    bot.Move.XY(-8604, 8056)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(942), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield  

def HealingBurst():
    bot.States.AddHeader("Healing Burst")
    target_prof = Profession.MONK
    start_map = 130
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(18153, 1880, 128)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(16632, -2766)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1118), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield  

def HealingHands():
    bot.States.AddHeader("Healing Hands")
    target_prof = Profession.MONK
    start_map = 35
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XY(3695, -9914)
    bot.Move.XYAndExitMap(3772, -8096, 121)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(4435.06, 2104.76)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(285), "Click Skill Frame")
    REAL_CAPTURED_SKILLS = [285]
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(HealingHands, "[H]Healing Hands")
    yield    

def LightofDeliverance():
    bot.States.AddHeader("Light of Deliverance")
    target_prof = Profession.MONK
    start_map = 554
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(5721, -5353, 371)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-3106, 9981)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1397), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 
 
def WordofHealing():
    bot.States.AddHeader("Word of Healing")
    target_prof = Profession.MONK
    start_map = 303
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(16596, 20549, 240)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-5836, -8676)
    bot.Move.XY(-4659, -17086)
    bot.Move.XY(-5177, -19524)
    bot.Move.XYAndExitMap(-5167, -21282, 31)
    bot.Move.XY(-3172.72, 9102.06)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(282), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def AirofEnchantment():
    bot.States.AddHeader("Air of Enchantment")
    target_prof = Profession.MONK
    start_map = 297
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(17214, 10919, 203)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(436, -14129)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1115), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def AuraofFaith():
    bot.States.AddHeader("Aura of Faith")
    target_prof = Profession.MONK
    start_map = 23
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-12507, -23517, 94)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(7408, 15741)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(260), "Click Skill Frame")
    REAL_CAPTURED_SKILLS = [260]
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(AuraofFaith, "[H]Aura of Faith")
    yield 

def DivertHexes():
    bot.States.AddHeader("Divert Hexes")
    target_prof = Profession.MONK
    start_map = 480
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-3104, 11454, 446)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(590.94, 8003.54)
    bot.Move.XY(1281.14, 7621.92)
    bot.Wait.ForTime(6000)
    bot.Interact.WithGadgetAtXY(1144.00, 7795.00)
    bot.Move.XY(8356, 6260)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1692), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield   

def LifeSheath():
    bot.States.AddHeader("Life Sheath")
    target_prof = Profession.MONK
    start_map = 284
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XY(11581, -18462)
    bot.Move.XYAndExitMap(11729, -20248, 256)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(1667, 8179)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1123), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield  

def ShieldOfRegeneration():
    bot.States.AddHeader("Shield of Regeneration")
    target_prof = Profession.MONK
    start_map = 648
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XY(11581, -18462)
    bot.Move.XYAndExitMap(-15205, 13205, 647)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-5878, 4262)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(261), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield      

def ZealousBenediction():
    bot.States.AddHeader("Zealous Benediction")
    target_prof = Profession.MONK
    start_map = 428
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-3, 12656, 399)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-6079, 4930)
    bot.Move.XY(-7671, -3974)
    bot.Move.XY(-8311, -8169)
    bot.Move.XY(2497, -12151)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1687), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def DefendersZeal():
    bot.States.AddHeader("Defender's Zeal")
    target_prof = Profession.MONK
    start_map = 469
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(7784, 18756, 468)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(8744, -3500)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1688), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def RayofJudgment():
    bot.States.AddHeader("Ray of Judgment")
    target_prof = Profession.MONK
    start_map = 303
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(16596, 20549, 240)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-5836, -8676)
    bot.Move.XY(1451.48, -11371.12)
    bot.Move.XY(3837.11, -11483.70)
    bot.Move.XY(6579.26, -15095.15)
    bot.Move.XYAndExitMap(4201, -17019, 241)
    bot.Move.XY(-3172.72, 9102.06)
    bot.Move.XY(9288.86, 11533.50)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(830), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield  

def WordOfCensure():
    bot.States.AddHeader("Word of Censure")
    target_prof = Profession.MONK
    start_map = 303
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(10898, 14691, 239)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(6662, 14738)
    bot.Move.XY(3888, 12848)
    bot.Move.XY(-5294, 12210)
    bot.Move.XY(-7574, 11998)
    bot.Move.XY(-7848, 14735)
    bot.Move.XY(-7357, 19672)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1129), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield  
            
def EmpathicRemoval():
    bot.States.AddHeader("Empathic Removal")
    target_prof = Profession.MONK
    start_map = 129
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-7622, 1811, 201)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-10570, 9687)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1126), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield  

def Martyr():
    bot.States.AddHeader("Martyr")
    target_prof = Profession.MONK
    start_map = 442
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-2263, -4568, 441)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(1187.66, 7907.58)
    bot.Move.XY(-2401.63, 7256.86)
    bot.Move.XY(-3468.55, 7226.10)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(298), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield  

def SignetOfRemoval():
    bot.States.AddHeader("Signet of Removal")
    target_prof = Profession.MONK
    start_map = 427
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-16327, -16374, 384)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(2931, 4745)
    bot.Move.XY(-1370, 647)
    bot.Move.XY(3193.36, -5025.75)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1690), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield     

def BalthazarsPendulum():
    bot.States.AddHeader("Balthazar's Pendulum")
    target_prof = Profession.MONK
    start_map = 378
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(5833, 4322, 377)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-13138.58, 15124.79)
    bot.Move.XY(-10693, 13246)
    bot.Move.XY(-9128, 6575)
    bot.Move.XY(-10995, 4335)
    bot.Move.XY(-12734, 3613)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1395), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield       

def ReapersMark():
    bot.States.AddHeader("Reaper's Mark")
    target_prof = Profession.NECROMANCER
    start_map = 378
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Necromancer Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(5833, 4322, 377)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-13138.58, 15124.79)
    bot.Move.XY(-10693, 13246)
    bot.Move.XY(-9128, 6575)
    bot.Move.XY(-10995, 4335)
    bot.Move.XY(-12734, 3613)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(808), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield
def Charge():
    bot.States.AddHeader("Charge!")
    target_prof = Profession.WARRIOR
    start_map = 277
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(3290,2443,227)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(11281,8015)
    bot.Move.XY(10870,7251)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(364), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def Coward():
    bot.States.AddHeader("Coward!")
    target_prof = Profession.WARRIOR
    start_map = 278
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(16913,-2081,200)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(14346,-7711)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(869), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def YoureAllAlone():
    bot.States.AddHeader("You're All Alone!")
    target_prof = Profession.WARRIOR
    start_map = 376
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-13898,18185,375)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-14670,15191)
    bot.Move.XY(-14442,10506)
    bot.Move.XY(-14987,5964)
    bot.Move.XY(-16592,1214)
    bot.Move.XY(-13983,-447)
    bot.Move.XY(-13735,-3138)
    bot.Move.XY(-12204,-6250)
    bot.Move.XY(-12545,-11272)
    bot.Move.XY(-15243,-11781)
    bot.Move.XY(-18017,-14809)    
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1412), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def AuspiciousParry():
    bot.States.AddHeader("Auspicious Parry")
    target_prof = Profession.WARRIOR
    start_map = 225
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Map.EnterChallenge(6000, target_map_id=start_map)
    ConfigureAggressiveEnv(bot)
    bot.Move.XYAndDialog(-15350.00, -4400.00, 0x84)
    bot.Move.XYAndDialog(-15350.00, -4400.00, 0x85)
    bot.Move.XYAndDialog(-15350.00, -5200.00, 0x84)
    bot.Move.XYAndDialog(-15350.00, -5200.00, 0x85)
    bot.Move.XY(-12912,-4586)
    bot.Move.XY(-9309,-4838)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1142), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def Backbreaker():
    bot.States.AddHeader("Backbreaker")
    target_prof = Profession.WARRIOR
    start_map = 638
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndDialog(-8394.00, -23641.00, 0x834003)
    bot.Move.XYAndDialog(-8394.00, -23641.00, 0x834001)
    bot.Move.XYAndExitMap(-9566,-20185,558)
    bot.Wait.ForTime(10000)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-9510,-19617)
    bot.Move.XY(-7413,-18104)
    bot.Move.XY(-3018,-21929)
    bot.Move.XY(-2640,-22766)
    bot.Move.XY(2412,-22816)
    bot.Move.XY(5803,-22306)
    bot.Move.XY(7927,-22176)
    bot.Move.XY(9963,-23162)
    bot.Move.XY(11318,-23417)
    bot.Move.XY(12061,-24743)
    bot.Move.XY(12083,-25002)
    bot.Move.XY(12139,-25707)
    bot.Move.XYAndExitMap(-9566,-20185,612)
    bot.Wait.ForTime(10000)
    bot.Move.XY(10068,17290)
    bot.Move.XY(12476,16511)
    bot.Move.XY(12550,14251)
    bot.Move.XY(13703,13173)
    bot.Move.XY(14336,12493)
    bot.Move.XY(15603,9255)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(358), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def BattleRage():
    bot.States.AddHeader("Battle Rage")
    target_prof = Profession.WARRIOR
    start_map = 219
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-26066,2719,211)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(17237,-8492)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(317), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def BullsCharge():
    bot.States.AddHeader("Bull's Charge")
    target_prof = Profession.WARRIOR
    start_map = 35
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(3814,-8534,121)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(8603,1382)
    bot.Move.XY(6755,3414)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(379), "Click Skill Frame")
    bot.Wait.ForTime(1000)
    REAL_CAPTURED_SKILLS = [379]
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(BullsCharge, "[H]Bull's Charge")
    yield 

def ChargingStrike():
    bot.States.AddHeader("Charging Strike")
    target_prof = Profession.WARRIOR
    start_map = 435
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(53,8080,419)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-7215,14308)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1405), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def Cleave():
    bot.States.AddHeader("Cleave")
    target_prof = Profession.WARRIOR
    start_map = 289
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-11172,-18231,202)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-1743,-17222)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(335), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def CripplingSlash():
    bot.States.AddHeader("Crippling Slash")
    target_prof = Profession.WARRIOR
    start_map = 644
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(15215,-6445,548)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(10809,-7205)
    bot.Move.XY(8277,-7408)
    bot.Move.XY(3687,-5597)
    bot.Move.XY(276,-4955)
    bot.Move.XY(-1348,-3619)
    bot.Move.XY(-3091,-5772)
    bot.Move.XY(-2462,-10789)
    bot.Move.XY(-1279,-12852)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1415), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def Decapitate():
    bot.States.AddHeader("Decapitate")
    target_prof = Profession.WARRIOR
    start_map = 424
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(4699,4435,384)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-17608,-14656)
    bot.Move.XY(-11839,-12101)
    bot.Move.XY(-5497,-10604)
    bot.Move.XY(-1670,-9530)
    bot.Move.XY(325,-11320)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1696), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def DefyPain():
    bot.States.AddHeader("Defy Pain")
    target_prof = Profession.WARRIOR
    start_map = 24
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-7469,-31762,98)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(13171,13137)
    bot.Move.XY(8538,10771)
    bot.Move.XY(8703,3675)
    bot.Move.XY(3643,2558)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(318), "Click Skill Frame")
    bot.Wait.ForTime(1000)
    REAL_CAPTURED_SKILLS = [318]
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(DefyPain, "[H]Defy Pain")
    yield

def DevastatingHammer():
    bot.States.AddHeader("Devastating Hammer")
    target_prof = Profession.WARRIOR
    start_map = 279
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(8971,-26294,203)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-545,14262)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(355), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def DragonSlash():
    bot.States.AddHeader("Dragon Slash")
    target_prof = Profession.WARRIOR
    start_map = 273
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(3473,7390,247)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(15726,-6563)
    bot.Move.XY(17996,2023)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(907), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def DwarvenBattleStance():
    bot.States.AddHeader("Dwarven Battle Stance")
    target_prof = Profession.WARRIOR
    start_map = 639
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndDialog(-24800.00, 11856.00, 0x833C01)
    bot.Travel_To_Random_District(target_map_id=624)
    bot.Move.XYAndExitMap(19682,19464,604)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-7303,-10429)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(375), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

#def EarthShaker ():
#    bot.States.AddHeader("Earth Shaker")
#    target_prof = Profession.WARRIOR
#    start_map = 
#    
#    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
#    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
#    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
#    bot.Party.LeaveParty()
#    bot.Travel_To_Random_District(target_map_id=start_map)
#    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
#    bot.Move.XY(,)
#    bot.Move.XYAndExitMap(,,)
#    ConfigureAggressiveEnv(bot)
#    bot.Move.XY(,)
#    bot.Wait.UntilOutOfCombat()
#    ConfigurePacifistEnv(bot)
#    bot.SkillBar.UseSkill(3)
#    bot.Wait.ForTime(5000)
#    bot.States.AddCustomState(lambda: ClickSkillFrame(354), "Click Skill Frame")
#    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
#    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
#    yield
#
def EnragedSmash():
    bot.States.AddHeader("Enraged Smash")
    target_prof = Profession.WARRIOR
    start_map = 274
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-12174,8693,232)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-149,18990)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(993), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

#def Flourish():
#    bot.States.AddHeader("Flourish")
#    target_prof = Profession.WARRIOR
#    start_map = 
#    
#    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
#    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
#    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
#    bot.Party.LeaveParty()
#    bot.Travel_To_Random_District(target_map_id=start_map)
#    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
#    bot.Move.XY(,)
#    bot.Move.XYAndExitMap(,,)
#    ConfigureAggressiveEnv(bot)
#    bot.Move.XY(,)
#    bot.Wait.UntilOutOfCombat()
#    ConfigurePacifistEnv(bot)
#    bot.SkillBar.UseSkill(3)
#    bot.Wait.ForTime(5000)
#    bot.States.AddCustomState(lambda: ClickSkillFrame(389), "Click Skill Frame")
#    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
#    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
#    yield
#
def ForcefulBlow():
    bot.States.AddHeader("Forceful Blow")
    target_prof = Profession.WARRIOR
    start_map = 272
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(6229,7476,244)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(10145,-15669)
    bot.Move.XY(3550,-13376)
    bot.Move.XY(-3025,-2655)
    bot.Move.XY(2343,-143)
    bot.Move.XY(4464,-2107)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(889), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

#def GladiatorsDefense():
#    bot.States.AddHeader("Gladiator's Defense")
#    target_prof = Profession.WARRIOR
#    start_map = 
#    
#    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
#    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
#    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
#    bot.Party.LeaveParty()
#    bot.Travel_To_Random_District(target_map_id=start_map)
#    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
#    bot.Move.XY(,)
#    bot.Move.XYAndExitMap(,,)
#    ConfigureAggressiveEnv(bot)
#    bot.Move.XY(,)
#    bot.Wait.UntilOutOfCombat()
#    ConfigurePacifistEnv(bot)
#    bot.SkillBar.UseSkill(3)
#    bot.Wait.ForTime(5000)
#    bot.States.AddCustomState(lambda: ClickSkillFrame(372), "Click Skill Frame")
#    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
#    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
#    yield
#
def Headbutt():
    bot.States.AddHeader("Headbutt")
    target_prof = Profession.WARRIOR
    start_map = 381
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(4547,853,380)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-10606,-13642)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1406), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def HundredBlades():
    bot.States.AddHeader("Hundred Blades")
    target_prof = Profession.WARRIOR
    start_map = 284
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(11716,-20069,256)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-4082,3681)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(381), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def MagehunterStrike():
    bot.States.AddHeader("Magehunter Strike")
    target_prof = Profession.WARRIOR
    start_map = 424
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(3336,-4469,379)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-1995,7148)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1694), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def MagehuntersSmash():
    bot.States.AddHeader("Magehunter's Smash")
    target_prof = Profession.WARRIOR
    start_map = 476
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(4718,-4659,399)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-20058,12400)
    bot.Move.XY(-18445,7220)
    bot.Move.XY(-18572,4688)
    bot.Move.XY(-19413,777)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1697), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield
    
def QuiveringBlade():
    bot.States.AddHeader("Quivering Blade")
    target_prof = Profession.WARRIOR
    start_map = 303
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(11511,15279,239)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(14588,-1653)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(892), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def RageoftheNtouka():
    bot.States.AddHeader("Rage of the Ntouka")
    target_prof = Profession.WARRIOR
    start_map = 387
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-411,3939,436)
    bot.Move.XYAndExitMap(5096,3792,380)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-3911,8256)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1408), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def Shove():
    bot.States.AddHeader("Shove")
    target_prof = Profession.WARRIOR
    start_map = 77
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(10685,-1122,210)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-6166,8228)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1146), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def SkullCrack():
    bot.States.AddHeader("Skull Crack")
    target_prof = Profession.WARRIOR
    start_map = 643
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(13656, 19140, 513)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(14398, 9923)
    bot.Move.XY(14181, 2399)
    bot.Move.XY(12244.49, -2212.59)
    bot.Move.XY(12748, -13018)
    bot.Move.XY(14207, -17051)
    bot.Move.XYAndExitMap(17143, -16898, 548)
    bot.Move.XY(-11059.88, 11532.18)
    bot.Wait.UntilOnCombat() #Wait for Baglorag Grumblesnort
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(329), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield
  
def SoldiersStance():
    bot.States.AddHeader("Soldier's Stance")
    target_prof = Profession.WARRIOR
    start_map = 545
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(1699, 4941, 437)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-4282.58, -13169.55)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractGadget(-4246.00, -12950.00)
    bot.Move.XY(2645, -17001)
    bot.Move.XY(7619, -17555)
    bot.Move.XY(12217, -14581)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1698), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def SteadyStance():
    bot.States.AddHeader("Steady Stance")
    target_prof = Profession.WARRIOR
    start_map = 407
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-4941,702,406)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-3923,-11844)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1701), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def TripleChop():
    bot.States.AddHeader("Triple Chop")
    target_prof = Profession.WARRIOR
    start_map = 303
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(16579,19653,240)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-1680,1957)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(992), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def WarriorsEndurance():
    bot.States.AddHeader("Warrior's Endurance")
    target_prof = Profession.WARRIOR
    start_map = 117
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=117)
    bot.States.AddCustomState(AdvancedHeroTeam, name="Advanced Hero Team") 
    bot.Map.EnterChallenge(delay=1000, target_map_id=117)
    bot.Wait.ForMapToChange(target_map_id=117) # Thirsty River Mission
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-857, 8546) #Sand Giant 1
    bot.Move.XY(-2320, 5881)
    bot.Move.XY(-125.10, 3166.91)
    bot.Move.XY(-50.19, 103.76)
    bot.Move.XY(1417.27, -2503.34)
    bot.Move.XY(4508.23, -3895.00)
    bot.Move.XY(5735.68, -3615.36) #Ugly Bridge
    bot.Move.XY(6548.60, -2597.65)
    bot.Move.XY(6904.65, -1450.62)
    bot.Move.XY(8282.06, -1424.29)
    bot.Move.XYAndInteractNPC(8945.00, -2457.00)
    bot.Wait.ForMapToChange(117) #Cutscene
    bot.Wait.ForTime(1000)
    bot.Move.XY(13091.00, -5283.00) #Goss Aleesh Boss and Priest
    bot.Move.XY(10711.53, -4565.11)
    bot.Wait.ForTime (7000)
    bot.Move.XY(8666.88, -6085.35)
    bot.Move.XY(9782.77, -9098.71)
    bot.Wait.ForTime (11000)
    bot.Move.XY(5899, -6912) #Hessper Sasso and Priest
    bot.Move.XY(6407.00, -11845.00) #Issah Sshay and Priest
    bot.Move.XY(6505.61, -9512.16)
    bot.Wait.ForTime (7000)
    bot.Move.XY(3947.58, -6702.45)
    bot.Move.XY(1570.69, -7218.57)
    bot.Wait.ForTime (11000)
    bot.Move.XY(-1140.90, -7167.44)
    bot.Move.XY(-1782.84, -6591.11) #Custodian Hulgar  and Priest
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(374), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def WhirlingAxe():
    bot.States.AddHeader("Whirling Axe")
    target_prof = Profession.WARRIOR
    start_map = 273
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Warrior Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(3492,7460,247)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(9205,-8560)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(888), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def LifeBarrier():
    bot.States.AddHeader("Life Barrier")
    target_prof = Profession.MONK
    start_map = 24
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Monk Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-7469,-31762,98)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(13171,13137)
    bot.Move.XY(8538,10771)
    bot.Move.XY(8703,3675)
    bot.Move.XY(3643,2558)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(270), "Click Skill Frame")
    bot.Wait.ForTime(1000)
    REAL_CAPTURED_SKILLS = [270]
    found_real_skill = False
    for slot in range(1, 9):
        skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(slot)
        if skill_data and skill_data.id in REAL_CAPTURED_SKILLS:
            found_real_skill = True
            break
    if found_real_skill:
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
        yield
    else:
        bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
        bot.States.AddCustomState(LifeBarrier, "[H]Life Barrier")
    yield  

def Way_of_the_Assassin():
    bot.States.AddHeader("Way of the Assassin")
    target_prof = Profession.ASSASSIN
    start_map = 424
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XY(441, 861)
    bot.Move.XYAndExitMap(3676, -4703, 379)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(11129, 7553)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1649), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield

def Dark_Apostasy():
    bot.States.AddHeader("Dark Apostasy")
    target_prof = Profession.ASSASSIN
    start_map = 230
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-4459, 5455, 209)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-20168, -3708)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1029), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield    

def Locusts_Fury():
    bot.States.AddHeader("Locust's Fury")
    target_prof = Profession.ASSASSIN
    start_map = 129
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-7585, 1955, 201)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-3771, 10839)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1030), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield        

def Palm_Strike():
    bot.States.AddHeader("Palm Strike")
    target_prof = Profession.ASSASSIN
    start_map = 303
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(16512, 20762, 240)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-5661.56, -8976.21)
    bot.Move.XY(-2649.35, -11041.71)
    bot.Move.XY(1566.75, -11356.73)
    bot.Move.XY(3910.05, -11147.77)
    bot.Move.XY(7522.26, -7489.61)
    bot.Move.XY(11203.97, -4819.40)
    bot.Move.XY(6323.50, -5214.16)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1045), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield  

def Seeping_Wound():
    bot.States.AddHeader("Seeping Wound")
    target_prof = Profession.ASSASSIN
    start_map = 51
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(5490, -12398, 31)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-10625, -2757)
    bot.Move.XY(-11491.36, -3626.96)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1034), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield   

def Flashing_Blades():
    bot.States.AddHeader("Flashing Blades")
    target_prof = Profession.ASSASSIN
    start_map = 220
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-14594, -3987, 197)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(8270, -635)
    bot.Move.XY(9518.52, 2496.50)
    bot.Move.XY(9658.32, 895.20)
    bot.Move.XY(9293.15, -141.34)
    bot.Move.XY(9427.46, 795.07)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1042), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield     

def Foxs_Promise():
    bot.States.AddHeader("Fox's Promise")
    target_prof = Profession.ASSASSIN
    start_map = 396
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-1367, 5938, 395)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(6784.16, -14382.22)
    bot.Move.XY(-2183.42, -5759.83)
    bot.Move.XY(-7934.60, -2841.50)
    bot.Move.XY(-9840.09, -2618.33)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1640), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield    

def Psychic_Instability():
    bot.States.AddHeader("Psychic Instability")
    target_prof = Profession.MESMER
    start_map = 277

    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Mesmer Build") 
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(3200, 2499, target_map_id=227)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(4599.85, 3940.26)
    bot.Move.XY(3039.05, 5503.06)
    bot.Move.XY(3187.73, -956.72)
    bot.Move.XY(7629.23, 3.76)
    bot.Move.XY(7716.02, 5614.70)
    bot.Move.XY(4753.20, 7895.67)
    bot.Move.XY(2412.87, 8214.28)
    bot.Move.XY(-3362.41, 5083.70)
    bot.Move.XY(-3286.67, 1236.43) # Chazek Plague Herder
    #bot.Move.XY(-3234.05, -827.53) # Shrouded Oni Shadow Shroud for later
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1057), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")

    yield    

def Shadow_Shroud():
    bot.States.AddHeader("Shadow Shroud")
    target_prof = Profession.ASSASSIN
    start_map = 277

    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build") 
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(3200, 2499, target_map_id=227)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(4599.85, 3940.26)
    bot.Move.XY(3039.05, 5503.06)
    bot.Move.XY(3187.73, -956.72)
    bot.Move.XY(7629.23, 3.76)
    bot.Move.XY(7716.02, 5614.70)
    bot.Move.XY(4753.20, 7895.67)
    bot.Move.XY(2412.87, 8214.28)
    bot.Move.XY(-3362.41, 5083.70)
    bot.Move.XY(-3286.67, 1236.43)
    bot.Move.XY(-3234.05, -827.53) # Shrouded Oni Shadow Shroud 
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(928), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield    

def Shattering_Assault():
    bot.States.AddHeader("Shattering Assault")
    target_prof = Profession.ASSASSIN
    start_map = 480

    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build") 
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XY(-3006.40, 13672.54)
    bot.Move.XYAndExitMap(-3042, 11398, target_map_id=446)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-2385.10, 5693.95)
    bot.Move.XY(-5785.96, 4816.62)
    bot.Move.XY(-9790.39, -6153.40)
    bot.Move.XY(-14231.77, -5938.61)
    bot.Move.XY(-18997.60, -1960.05)
    bot.Move.XYAndExitMap(-19988, -3069, target_map_id=448)
    bot.Move.XY(8516.31, -21069.59)
    bot.Move.XY(5215.24, -21435.55)
    bot.Move.XY(-7342.22, -18174.64)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1634), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield   

def AuraofDisplacement():
    bot.States.AddHeader("Aura of Displacement")
    target_prof = Profession.ASSASSIN
    start_map = 77

    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build") 
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map) #House Zu Heltzer
    bot.States.AddCustomState(AdvancedHeroTeam, name="Advanced Hero Team")
    bot.Move.XY(8196.40, -1113.54)
    bot.Move.XYAndExitMap(10660, -1027, 210) #Ferndale
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-9358.26, 12733.01)
    bot.Move.XY(-1456.50, 19115.00)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(771), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield   

def MarkofInsecurity():
    bot.States.AddHeader("Mark of Insecurity")
    target_prof = Profession.ASSASSIN
    start_map = 559

    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build") 
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map) #Gate of the Nightfallen Lands
    bot.States.AddCustomState(AdvancedHeroTeam, name="Advanced Hero Team")
    bot.Move.XYAndExitMap(-16693, 19103, 465) #Nightfallen Jahai
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-5746, 3318)
    bot.Move.XY(-7538, 825)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(570), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield   

def HiddenCaltrops():
    bot.States.AddHeader("Hidden Caltrops")
    target_prof = Profession.ASSASSIN
    start_map = 424

    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build") 
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map) #Kodorur Crossroads
    bot.States.AddCustomState(AdvancedHeroTeam, name="Advanced Hero Team")
    bot.Move.XYAndExitMap(5018, 5107, 384) #Floodplain of Mahnkelon
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-13221, -11714)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1642), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield   

def AssaultEnchantments():
    bot.States.AddHeader("Assault Enchantments")
    target_prof = Profession.ASSASSIN
    start_map = 450

    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build") 
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map) #Gate of Torment
    bot.States.AddCustomState(AdvancedHeroTeam, name="Advanced Hero Team")
    bot.Move.XYAndExitMap(-7820, 14363, 465) #Floodplain of Mahnkelon
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-2950, -7871)
    bot.Move.XY(4153, -9215)
    bot.Move.XY(17913, -5760)
    bot.Move.XY(20215.48, -6927.39)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1643), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield   

def ShadowMeld():
    bot.States.AddHeader("Shadow Meld")
    target_prof = Profession.ASSASSIN
    start_map = 477

    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build") 
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map) #Nundu Bay
    bot.States.AddCustomState(AdvancedHeroTeam, name="Advanced Hero Team")
    bot.Move.XYAndExitMap(-15570, -3834, 371) #Floodplain of Mahnkelon
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-13815, 3355)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1654), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield   

def WastrelsCollapse():
    bot.States.AddHeader("Wastrel's Collapse")
    target_prof = Profession.ASSASSIN
    start_map = 407

    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build") 
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map) #Yahnur Market
    bot.States.AddCustomState(AdvancedHeroTeam, name="Advanced Hero Team")
    bot.Move.XYAndExitMap(-5262, 635, 406) #Vehtendi Valley
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-6604, -11438)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1644), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield   

def GoldenSkullStrike():
    bot.States.AddHeader("Golden Skull Strike")
    target_prof = Profession.ASSASSIN
    start_map = 496
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XY(18267, -6197)
    bot.Move.XYAndExitMap(19693, -7411, 466)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-8329, -10361)
    bot.Move.XY(-6013, -5332)
    bot.Move.XY(-2935, -6277)
    bot.Move.XY(142, -9721)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(1635), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def Temple_Strike():
    bot.States.AddHeader("Temple Strike")
    target_prof = Profession.ASSASSIN
    start_map = 289
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-14020, -19884, 203)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(9787, 5444)
    bot.Move.XY(7366.23, 4905.62)
    bot.Move.XY(6585.46, 4768.86)
    bot.Move.XY(3505.03, 4318.40)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(988), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def Moebius_Strike():
    bot.States.AddHeader("Moebius Strike")
    target_prof = Profession.ASSASSIN
    start_map = 130
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(18474, 1840, 128)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(9, 10587)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(781), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 


def Shroud_of_Silence():
    bot.States.AddHeader("Shroud of Silence")
    target_prof = Profession.ASSASSIN
    start_map = 226
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-9625, 3076, 233)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(24307.18, 1386.19)
    bot.Move.XY(10995.01, 4251.18)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(801), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def Siphon_Strength():
    bot.States.AddHeader("Siphon Strength")
    target_prof = Profession.ASSASSIN
    start_map = 288
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(-16320, 13637, 199)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(-19877.70, 3994.01)
    bot.Move.XY(-18904.16, 3510.10)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(827), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def Way_of_the_Empty_Palm():
    bot.States.AddHeader("Way of the Empty Palm")
    target_prof = Profession.ASSASSIN
    start_map = 273
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(3473, 7390, 247)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(15726, -6563)
    bot.Move.XY(17996, 2023)
    bot.Move.XY(24723, 8890)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(987), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 

def Beguiling_Haze():
    bot.States.AddHeader("Beguiling Haze")
    target_prof = Profession.ASSASSIN
    start_map = 287
    
    bot.States.AddCustomState(lambda: RecordStartingMap(start_map), "Record Start")
    bot.States.AddCustomState(lambda: SaveCurrentBuild(), "Save Build")
    bot.States.AddCustomState(lambda: LoadSecondaryBuild(target_prof), "Load Assassin Build")
    bot.Party.LeaveParty()
    bot.Travel_To_Random_District(target_map_id=start_map)
    bot.States.AddCustomState(AdvancedHeroTeam, "Advanced Hero Team")
    bot.Move.XYAndExitMap(32538, 10966, 205)
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(10599, -7793)
    bot.Move.XY(11896, -819)
    bot.Move.XY(14938, -266)
    bot.Wait.UntilOutOfCombat()
    ConfigurePacifistEnv(bot)
    bot.SkillBar.UseSkill(3)
    bot.Wait.ForTime(5000)
    bot.States.AddCustomState(lambda: ClickSkillFrame(799), "Click Skill Frame")
    bot.States.AddCustomState(lambda: ReturnToStartingMap(), "Return to Outpost")
    bot.States.AddCustomState(lambda: RestoreSavedBuild(), "Restore Build")
    yield 
# ============================================================================
#region ADVANCED GUI CLASS
# ============================================================================

class EliteSkillsGUI:
    def __init__(self, bot: Botting, base_path: Optional[str] = None):
        self.bot = bot
        
        if base_path is None:
            try:
                script_path = os.path.abspath(__file__)
                base_path = find_textures_directory(script_path)
                
                if base_path is None:
                    base_path = os.path.dirname(os.path.dirname(script_path))
            except NameError:
                base_path = find_textures_directory(os.getcwd())
                if base_path is None:
                    base_path = os.getcwd()
        
        self.base_path = base_path
        
        # UI State
        self.show_window = True
        self.window_size_set = True
        self.current_profession = Profession.MESMER
        self.selected_skill = None
        self.capture_running = False
        self.capture_start_time = None
        self.last_known_state = "Ready"
        
        # Batch capture state
        self.batch_skills = []
        self.current_batch_index = 0

        # Settings state
        self.show_settings = False
        self.settings = {
            "use_cupcake": True,
            "use_apple": True,
            "use_candy": True,
            "use_egg": True,
            "use_pies": True,
            "use_war_supplies": True,
            "use_conset": False,
            "pause_on_danger": True,
            "halt_on_death": False,
            "auto_deposit_gold": True,
        }

        # FSM state tracking (for dynamic state management)
        self._original_state_count = 0
        self._last_original_next = None

    def _set_property_active_now(self, prop_name: str, active: bool) -> None:
        try:
            if hasattr(self.bot, "Properties") and hasattr(self.bot.Properties, "exists") and self.bot.Properties.exists(prop_name):
                self.bot.Properties.ApplyNow(prop_name, "active", active)
        except:
            pass

    def _apply_settings_now(self) -> None:
        global _script_settings
        # Sync GUI settings to module-level storage for ConfigureAggressiveEnv/PacifistEnv
        _script_settings["use_cupcake"] = bool(self.settings.get("use_cupcake", True))
        _script_settings["use_apple"] = bool(self.settings.get("use_apple", True))
        _script_settings["use_candy"] = bool(self.settings.get("use_candy", True))
        _script_settings["use_egg"] = bool(self.settings.get("use_egg", True))
        _script_settings["use_pies"] = bool(self.settings.get("use_pies", True))
        _script_settings["use_war_supplies"] = bool(self.settings.get("use_war_supplies", True))

        self._set_property_active_now("birthday_cupcake", _script_settings["use_cupcake"])
        self._set_property_active_now("candy_apple", _script_settings["use_apple"])
        self._set_property_active_now("candy_corn", _script_settings["use_candy"])
        self._set_property_active_now("golden_egg", _script_settings["use_egg"])
        self._set_property_active_now("slice_of_pumpkin_pie", _script_settings["use_pies"])
        self._set_property_active_now("war_supplies", _script_settings["use_war_supplies"])

        conset_active = bool(self.settings.get("use_conset", False))
        self._set_property_active_now("essence_of_celerity", conset_active)
        self._set_property_active_now("grail_of_might", conset_active)
        self._set_property_active_now("armor_of_salvation", conset_active)

        try:
            if hasattr(self.bot, "config") and hasattr(self.bot.config, "config_properties"):
                if hasattr(self.bot.config.config_properties, "pause_on_danger"):
                    self.bot.config.config_properties.pause_on_danger.set_now("active", bool(self.settings.get("pause_on_danger", True)))
                if hasattr(self.bot.config.config_properties, "halt_on_death"):
                    self.bot.config.config_properties.halt_on_death.set_now("active", bool(self.settings.get("halt_on_death", False)))
        except:
            pass
        
    def get_texture_path(self, skill: EliteSkill):
        """Get the full texture path for a skill's icon"""
        if skill.icon_filename:
            texture_path = os.path.join(self.base_path, "Textures", "Skill_Icons", skill.icon_filename)
            texture_path = os.path.normpath(texture_path)
            
            if os.path.exists(texture_path):
                return texture_path
        
        return None
        
    def get_profession_color(self, profession: Profession):
        """Get pure grey background color"""
        return (0.20, 0.20, 0.20, 0.70)

    def draw_main_window(self):
        """Draw the main GUI window"""
        if not self.show_window:
            return

        if not self.window_size_set:
            PyImGui.set_next_window_size(540, 545)
            self.window_size_set = True

        # Set window background color based on selected profession
        bg_color = self.get_profession_color(self.current_profession)
        PyImGui.push_style_color(PyImGui.ImGuiCol.WindowBg, bg_color)

        if PyImGui.begin("Elite Skills Capper", True, PyImGui.WindowFlags.NoFlag):
            self.draw_header()
            PyImGui.separator()
            self.draw_profession_tabs()
            PyImGui.separator()
            self.draw_skill_selection()
            PyImGui.separator()
            self.draw_controls()
            PyImGui.separator()
            self.draw_status()

        PyImGui.end()
        PyImGui.pop_style_color(1)

        self.draw_settings_window()
    
    def draw_header(self):
        """Draw header with title and settings button"""
        PyImGui.text("Elite Skills Capper")
        if PyImGui.is_item_hovered():
            if PyImGui.begin_tooltip():
                PyImGui.text_colored("Elite Skills Capture Bot", (0.2, 0.8, 0.2, 1.0))
                PyImGui.separator()
                PyImGui.text("Automatically captures elite skills from bosses throughout Guild Wars.")
                PyImGui.text("Travels to required maps, finds bosses, and uses Signet of Capture.")
                PyImGui.separator()
                PyImGui.text_colored("Button Color Guide:", (0.9, 0.9, 0.2, 1.0))
                PyImGui.text_colored("• Blue Start", (0.2, 0.6, 0.8, 1.0))
                PyImGui.text("  - Skill is available and ready to capture")
                PyImGui.text_colored("• Green Start", (0.2, 0.8, 0.2, 1.0))
                PyImGui.text("  - Skill already captured (disabled)")
                PyImGui.text_colored("• Red Start", (0.8, 0.2, 0.2, 1.0))
                PyImGui.text("  - Required map is not unlocked")
                PyImGui.end_tooltip()
        PyImGui.same_line(0, 10)
        
        # Buy Signet button - always visible
        if not IsSignetUnlocked():
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.9, 0.3, 0.1, 1.0))
        if PyImGui.button(IconsFontAwesome5.ICON_SHOPPING_CART + " Buy Signet", 120, 25):
            self.bot.Stop()
            # Remove any dynamic states beyond base count, then add Buy Signet
            fsm = self.bot.config.FSM
            original_count = getattr(self, "_original_state_count", 0)
            if original_count > 0 and len(fsm.states) > original_count:
                del fsm.states[original_count:]
            self.bot.States.AddHeader("Buy Signet of Capture")
            self.bot.States.AddCustomState(lambda: BuySignetOfCapture(), "Buy Signet")
            # Jump directly to Buy Signet state (last state)
            self.bot.StartAtStep("Buy Signet")
        if not IsSignetUnlocked():
            PyImGui.pop_style_color(1)
        PyImGui.same_line(0, 10)
        
        if PyImGui.button(IconsFontAwesome5.ICON_COG + " Settings", 100, 25):
            self.show_settings = not self.show_settings

    def draw_settings_window(self):
        """Draw the settings configuration window"""
        if not self.show_settings:
            return

        if PyImGui.begin("Elite Skills Settings", True, PyImGui.WindowFlags.AlwaysAutoResize):
            PyImGui.text("Consumables")
            PyImGui.separator()

            prev = dict(self.settings)

            self.settings["use_cupcake"] = PyImGui.checkbox("Use Birthday Cupcake", self.settings["use_cupcake"])
            self.settings["use_apple"] = PyImGui.checkbox("Use Golden Apple", self.settings["use_apple"])
            self.settings["use_candy"] = PyImGui.checkbox("Use Candy", self.settings["use_candy"])
            self.settings["use_egg"] = PyImGui.checkbox("Use Egg", self.settings["use_egg"])
            self.settings["use_pies"] = PyImGui.checkbox("Use Pies", self.settings["use_pies"])
            self.settings["use_war_supplies"] = PyImGui.checkbox("Use War Supplies", self.settings["use_war_supplies"])

            PyImGui.separator()
            PyImGui.text("Combat Settings")
            PyImGui.separator()

            self.settings["use_conset"] = PyImGui.checkbox("Use PConSet", self.settings["use_conset"])
            self.settings["pause_on_danger"] = PyImGui.checkbox("Pause on Danger", self.settings["pause_on_danger"])
            self.settings["halt_on_death"] = PyImGui.checkbox("Halt on Death", self.settings["halt_on_death"])

            PyImGui.separator()
            PyImGui.text("Gold Management")
            PyImGui.separator()

            self.settings["auto_deposit_gold"] = PyImGui.checkbox("Auto Deposit Gold", self.settings["auto_deposit_gold"])

            if self.settings != prev:
                self._apply_settings_now()

            PyImGui.separator()
            PyImGui.text("Debug")
            PyImGui.separator()

            try:
                draw_path_active = self.bot.config.config_properties.draw_path.is_active()
                new_draw_path = PyImGui.checkbox("Draw Path", draw_path_active)
                if new_draw_path != draw_path_active:
                    self.bot.config.config_properties.draw_path.set_now("active", new_draw_path)
            except:
                pass

            PyImGui.separator()

            if PyImGui.button("Close", 130, 30):
                self.show_settings = False

            PyImGui.end()

    def draw_profession_tabs(self):
        button_width = 95
        button_height = 24
        spacing = 6

        for i, prof in enumerate(PROFESSIONS_ORDERED):
            if prof == self.current_profession:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.2, 0.6, 0.8, 1.0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.3, 0.7, 0.9, 1.0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.1, 0.5, 0.7, 1.0))

            if PyImGui.button(prof.value, button_width, button_height):
                self.current_profession = prof

            if prof == self.current_profession:
                PyImGui.pop_style_color(3)

            if (i + 1) % 5 == 0 or i == len(PROFESSIONS_ORDERED) - 1:
                pass
            else:
                PyImGui.same_line(0, spacing)
    
    def draw_skill_selection(self):
        """Draw skill selection list with icons"""
        PyImGui.text(f"Select Elite Skill - {self.current_profession.value}")
        PyImGui.separator()

        PyImGui.begin_child("elite_skills_region", (0, 220), True)

        skills = [s for s in ELITE_SKILLS if s.profession == self.current_profession]
        if not skills:
            PyImGui.text("No skills added for this profession yet")
            PyImGui.end_child()
            return

        for skill in sorted(skills, key=lambda s: s.skill_id):
            # Check if skill is already unlocked and if map is accessible
            is_unlocked = is_skill_unlocked(skill.skill_id)
            can_learn = can_learn_skill(skill.skill_id)
            can_access_map = can_access_skill_map(skill)
            
            # Set button color based on skill status
            if is_unlocked:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.2, 0.8, 0.2, 0.5))  # Green - already captured
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.3, 0.9, 0.3, 0.7))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.1, 0.7, 0.1, 0.9))
            elif not can_access_map:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.8, 0.2, 0.2, 0.5))  # Red - map locked
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.9, 0.3, 0.3, 0.7))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.7, 0.1, 0.1, 0.9))
            else:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.2, 0.6, 0.8, 1.0))  # Blue - available
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.3, 0.7, 0.9, 1.0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.1, 0.5, 0.7, 1.0))

            texture_path = self.get_texture_path(skill)

            if texture_path:
                ImGui.image(texture_path, (32, 32))
                # Tooltip on hover - show skill description
                if PyImGui.is_item_hovered():
                    if PyImGui.begin_tooltip():
                        # Skill name
                        ImGui.push_font("Bold", 16)
                        PyImGui.text(skill.display_name)
                        ImGui.pop_font()
                        
                        # Skill status
                        if is_unlocked:
                            PyImGui.text_colored("✓ Already Captured", (0.2, 0.8, 0.2, 1.0))
                        elif not can_access_map:
                            PyImGui.text_colored("✗ Map Locked", (0.8, 0.2, 0.2, 1.0))
                            PyImGui.text(f"Required Map: {Map.GetMapName(skill.start_map)} (ID: {skill.start_map})")
                        else:
                            PyImGui.text_colored("○ Available", (0.2, 0.6, 0.8, 1.0))
                        
                        PyImGui.separator()
                        # Use skill.description if set, else game data
                        desc = skill.description
                        if not desc:
                            try:
                                desc = GLOBAL_CACHE.Skill.GetDescription(skill.skill_id)
                            except:
                                pass
                        if desc:
                            PyImGui.push_text_wrap_pos(350)
                            PyImGui.text_wrapped(desc)
                            PyImGui.pop_text_wrap_pos()
                        else:
                            PyImGui.text_disabled("No description available")
                        PyImGui.end_tooltip()
            else:
                PyImGui.text(" ")

            PyImGui.same_line(0, 10)
            PyImGui.text(skill.display_name)
            PyImGui.same_line(0, 15)

            if self.capture_running:
                PyImGui.begin_disabled(True)
                if PyImGui.button(f"Start##{skill.id}", 110, 30):
                    pass  # Disabled while running
            else:
                if PyImGui.button(f"Start##{skill.id}", 110, 30):
                    self.start_capture_for_skill(skill)
            if self.capture_running:
                PyImGui.end_disabled()
            
            # Add tooltip for button color explanation
            if PyImGui.is_item_hovered():
                if PyImGui.begin_tooltip():
                    if is_unlocked:
                        PyImGui.text_colored("Status: Already Captured", (0.2, 0.8, 0.2, 1.0))
                        PyImGui.text("This skill is already unlocked on your character.")
                    elif not can_access_map:
                        PyImGui.text_colored("Status: Map Locked", (0.8, 0.2, 0.2, 1.0))
                        PyImGui.text(f"Required Map: {Map.GetMapName(skill.start_map)} (ID: {skill.start_map})")
                        PyImGui.text("You need to unlock this outpost to capture this skill.")
                    else:
                        PyImGui.text_colored("Status: Available", (0.2, 0.6, 0.8, 1.0))
                        PyImGui.text("This skill is ready to be captured.")
                    PyImGui.end_tooltip()

            # Pop the 3 style colors we pushed for the button
            PyImGui.pop_style_color(3)

            PyImGui.separator()

        PyImGui.end_child()
    
    def draw_controls(self):
        """Draw control buttons - simplified since selection is no longer needed"""
        
        # Always show Capture All button first (most important feature)
        available_skills = [s for s in ELITE_SKILLS if s.profession == self.current_profession 
                          and not is_skill_unlocked(s.skill_id) 
                          and can_learn_skill(s.skill_id)
                          and can_access_skill_map(s)]
        # Sort by skill_id to match GUI display order
        available_skills = sorted(available_skills, key=lambda s: s.skill_id)
        
        # Available Skills Information Box
        PyImGui.push_style_color(PyImGui.ImGuiCol.ChildBg, (0.1, 0.1, 0.1, 0.8))
        PyImGui.begin_child("available_skills_info", (0, 60), True)
        PyImGui.text(f"Available Skills: {len(available_skills)}")
        PyImGui.text_colored("Ready to capture", (0.2, 0.8, 0.2, 1.0))
        PyImGui.end_child()
        PyImGui.pop_style_color(1)
        
        PyImGui.same_line(0, 10)
        
        PyImGui.same_line(0, 10)
        
        # Show individual skill controls only when a skill is selected
        if not self.selected_skill:
            PyImGui.text("Select a skill from the list above for individual capture")
            return
        
        PyImGui.text(f"Selected: {self.selected_skill.display_name} (ID: {self.selected_skill.skill_id})")
        
        if self.capture_running:
            # Show Stop button while capture is running
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.7, 0.2, 0.2, 1.0))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.8, 0.3, 0.3, 1.0))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.6, 0.1, 0.1, 1.0))
            if PyImGui.button(IconsFontAwesome5.ICON_STOP_CIRCLE + " Stop Capture", 140, 30):
                self.stop_capture()
            PyImGui.pop_style_color(3)
        else:
            # Show Start button when idle
            if PyImGui.button(IconsFontAwesome5.ICON_PLAY_CIRCLE + " Start Capture", 140, 30):
                self._start_capture()
        
            
    def draw_status(self):
        """Draw detailed status information"""
        PyImGui.separator()
        PyImGui.text("Status Information:")
        
        if self.capture_running:
            # Status indicator
            PyImGui.text("Status: " + self._get_capture_status())
            
            # Current skill info
            if self.selected_skill:
                PyImGui.text(f"Skill: {self.selected_skill.display_name} ({self.selected_skill.profession.value})")
            
            # Progress information
            progress_text = self._get_progress_text()
            PyImGui.text(f"Progress: {progress_text}")
            
            # Current location/map
            location_info = self._get_location_info()
            if location_info:
                PyImGui.text(f"Location: {location_info}")
            
            # Elapsed time
            if self.capture_start_time:
                elapsed = time.time() - self.capture_start_time
                minutes, seconds = divmod(int(elapsed), 60)
                PyImGui.text(f"Elapsed: {minutes:02d}:{seconds:02d}")
        else:
            PyImGui.text("Status: Idle")
            PyImGui.text("Progress: Ready to capture")
            if self.selected_skill:
                PyImGui.text(f"Selected: {self.selected_skill.display_name}")
        
        # Bot state information
        current_state = self._get_current_state_info()
        PyImGui.text(f"Current State: {current_state}")
    
    def _get_capture_status(self) -> str:
        """Get current capture status based on bot state"""
        try:
            if not self.capture_running:
                return "Idle"
            
            # Check if bot is in combat - simplified approach
            current_state = self._get_current_state_info()
            if 'combat' in current_state.lower():
                return "In Combat"
            
            # Check if bot is moving/traveling
            current_state = self._get_current_state_info()
            if any(keyword in current_state.lower() for keyword in ['travel', 'move', 'xy']):
                return "Traveling"
            
            # Check if bot is capturing
            if any(keyword in current_state.lower() for keyword in ['capture', 'signet', 'click']):
                return "Capturing Skill"
            
            # Check if bot is waiting
            if any(keyword in current_state.lower() for keyword in ['wait', 'delay']):
                return "Waiting"
            
            return "Active"
        except:
            return "Active"
    
    def _get_progress_text(self) -> str:
        """Get detailed progress information"""
        try:
            current_state = self._get_current_state_info()
            
            # Map common state patterns to user-friendly progress text
            if 'travel' in current_state.lower():
                return "Traveling to destination"
            elif 'move' in current_state.lower():
                return "Moving to capture location"
            elif 'combat' in current_state.lower():
                return "Engaging in combat"
            elif 'capture' in current_state.lower() or 'signet' in current_state.lower():
                return "Capturing elite skill"
            elif 'click' in current_state.lower():
                return "Clicking skill capture interface"
            elif 'wait' in current_state.lower():
                return "Waiting for conditions"
            elif 'party' in current_state.lower():
                return "Managing party"
            elif 'hero' in current_state.lower():
                return "Configuring heroes"
            else:
                return f"Executing: {current_state}"
        except:
            return "Running capture sequence"
    
    def _get_location_info(self) -> str:
        """Get current location/map information"""
        try:
            # Try to get current map ID and name
            if hasattr(Map, 'GetMapID'):
                map_id = Map.GetMapID()
                if hasattr(Map, 'GetMapName'):
                    map_name = Map.GetMapName()
                    return f"{map_name} (ID: {map_id})"
                else:
                    return f"Map ID: {map_id}"
            
            # Fallback to player position if available
            if hasattr(Player, 'GetXY'):
                x, y = Player.GetXY()
                return f"Position: ({int(x)}, {int(y)})"
        except:
            pass
        
        return "Unknown location"
    
    def _get_current_state_info(self) -> str:
        """Get current bot state information"""
        try:
            # Try to get current FSM state
            if hasattr(self.bot, 'config') and hasattr(self.bot.config, 'FSM'):
                fsm = self.bot.config.FSM
                if hasattr(fsm, 'current_state') and fsm.current_state:
                    return fsm.current_state.name or str(fsm.current_state)
            
            # Try to get from bot states using alternative methods
            if hasattr(self.bot, 'States'):
                states = self.bot.States
                # Try multiple possible methods
                for method_name in ['GetCurrentStepName', 'get_current_step', 'current_step', 'get_step']:
                    if hasattr(states, method_name):
                        try:
                            method = getattr(states, method_name)
                            state = method()
                            if state and str(state) != "Unknown":
                                return str(state)
                        except:
                            continue
            
            # Try to get from bot properties
            for method_name in ['GetStatus', 'get_status', 'status']:
                if hasattr(self.bot, method_name):
                    try:
                        method = getattr(self.bot, method_name)
                        status = method()
                        if status:
                            return str(status)
                    except:
                        continue
        except:
            pass
        
        return "Ready"
    
    def start_capture_for_skill(self, skill: EliteSkill):
        """Start the capture process for a specific skill"""
        if self.capture_running:
            return
        
        # Check if skill should be skipped
        should_skip, reason = should_skip_skill(skill.skill_id)
        if should_skip:
            ConsoleLog("SkillCheck", f"SKIPPING: {reason}", log=True)
            print(f"SKIPPING: {reason}")
            return
        
        ConsoleLog("SkillCheck", f"Starting capture for {skill.display_name} (ID: {skill.skill_id})", log=True)
        self.selected_skill = skill
        self._start_capture()
    
    def start_batch_capture(self, skills: List[EliteSkill]):
        """Start batch capture for multiple skills"""
        if self.capture_running:
            return
        
        if not skills:
            ConsoleLog("BatchCapture", "No available skills to capture", log=True)
            return
        
        ConsoleLog("BatchCapture", f"Starting batch capture for {len(skills)} skills", log=True)
        self.batch_skills = skills
        self.current_batch_index = 0
        self._start_next_batch_skill()
    
    def _start_next_batch_skill(self):
        """Start the next skill in the batch"""
        if self.current_batch_index >= len(self.batch_skills):
            ConsoleLog("BatchCapture", "Batch capture completed!", log=True)
            print("Batch capture completed!")
            self.batch_skills = []
            self.current_batch_index = 0
            return
        
        skill = self.batch_skills[self.current_batch_index]
        ConsoleLog("BatchCapture", f"Capturing skill {self.current_batch_index + 1}/{len(self.batch_skills)}: {skill.display_name}", log=True)
        self.selected_skill = skill
        self._start_capture()
    
    def buy_signet_of_capture(self):
        """Buy Signet of Capture from Eye of the North"""
        if self.capture_running:
            ConsoleLog("BuySignet", "Cannot buy signet while capture is running", log=True)
            return
        
        ConsoleLog("BuySignet", "Starting Signet of Capture purchase...", log=True)
        
        # Create a temporary FSM state for buying the signet
        def buy_signet_state():
            yield from BuySignetOfCapture()
        
        # Add the buy state and execute it
        self.bot.States.AddCustomState(buy_signet_state, "Buy Signet of Capture")
        fsm = self.bot.config.FSM
        
        # Get the buy state we just added
        buy_state = fsm.states[-1]
        
        # Execute the buy state
        fsm.current_state = buy_state
        buy_state.reset()
        buy_state.enter()
        self.bot.config.fsm_running = True
    
    def _start_capture(self):
        if not self.selected_skill or self.capture_running:
            return
        
        try:
            self.capture_start_time = time.time()
            self.bot.Stop()
            fsm = self.bot.config.FSM
            original_count = getattr(self, "_original_state_count", 0)

            if original_count <= 0:
                print("FSM base states are not initialized.")
                return

            if len(fsm.states) > original_count:
                fsm.states[original_count - 1].next_state = getattr(self, "_last_original_next", None)
                del fsm.states[original_count:]

            builder_fn = None
            for state in fsm.states:
                if state.name == self.selected_skill.step_name and hasattr(state, 'coroutine_fn'):
                    builder_fn = state.coroutine_fn
                    break

            if not builder_fn:
                print(f"Could not find builder for '{self.selected_skill.display_name}'")
                return

            # Check if starting map is unlocked BEFORE building states
            if self.selected_skill.start_map > 0:
                if not CheckMapUnlocked(self.selected_skill.start_map, self.selected_skill.display_name):
                    ConsoleLog("Capture", f"Cannot start {self.selected_skill.display_name}: Outpost not unlocked", log=True)
                    self.capture_running = False
                    return

            # Check for Signet of Capture - auto-buy if not unlocked (build loading will equip it)
            if not IsSignetUnlocked():
                ConsoleLog("Signet", "Signet not unlocked - will buy from trainer first", log=True)
                # Add buy step as first state before the capture steps
                self.bot.States.AddCustomState(lambda: BuySignetOfCapture(), "Buy Signet of Capture")
                self.bot.Wait.ForTime(1000)

            try:
                gen = builder_fn()
                while True:
                    next(gen)
            except StopIteration:
                pass
            except Exception as e:
                print(f"Error while building steps for {self.selected_skill.display_name}: {e}")
                return

            n_after = len(fsm.states)
            if n_after <= original_count:
                print(f"No execution steps were generated for {self.selected_skill.display_name}")
                return

            print(f"Started: {self.selected_skill.display_name} ({n_after - original_count} steps)")

            fsm.states[original_count - 1].next_state = getattr(self, "_last_original_next", None)
            fsm.states[-1].next_state = None

            first_sub = fsm.states[original_count]
            self.bot.config.fsm_running = True
            fsm.finished = False
            fsm._cleanup_coroutines()
            fsm.current_state = first_sub
            first_sub.reset()
            first_sub.enter()

            print(f"FSM start at: {first_sub.name}")

            self.capture_running = True
            print(f"Started capture for {self.selected_skill.display_name} (ID: {self.selected_skill.skill_id})")
            
            # Check if this is part of a batch capture
            if hasattr(self, 'batch_skills') and self.batch_skills:
                # Start monitoring for completion
                import threading
                def monitor_completion():
                    import time
                    while self.capture_running and self.current_batch_index < len(self.batch_skills):
                        # Check if bot is idle (skill completed)
                        current_state = self._get_current_state_info()
                        if "idle" in current_state.lower() or "ready" in current_state.lower():
                            # Give it a moment to ensure completion
                            time.sleep(1)
                            if "idle" in self._get_current_state_info().lower():
                                skill_name = self.selected_skill.display_name if self.selected_skill else "Unknown"
                                ConsoleLog("BatchCapture", f"Skill {skill_name} completed, moving to next...", log=True)
                                self.current_batch_index += 1
                                if self.current_batch_index < len(self.batch_skills):
                                    self._start_next_batch_skill()
                                else:
                                    ConsoleLog("BatchCapture", "All skills in batch completed!", log=True)
                                    self.batch_skills = []
                                    self.current_batch_index = 0
                                break
                        time.sleep(0.5)  # Check every half second
                
                threading.Thread(target=monitor_completion, daemon=True).start()
            
        except Exception as e:
            print(f"Failed to start capture: {e}")
            self.capture_running = False
    
    def stop_capture(self):
        """Stop the capture process"""
        try:
            self.bot.Stop()
            self.capture_running = False
            self.capture_start_time = None
            
            # Check if this was part of a batch capture
            if hasattr(self, 'batch_skills') and self.batch_skills:
                self.current_batch_index += 1
                # Start next skill in batch after a short delay
                if self.current_batch_index < len(self.batch_skills):
                    ConsoleLog("BatchCapture", f"Moving to next skill in batch...", log=True)
                    # Schedule next skill to start after a delay
                    import threading
                    def start_next():
                        import time
                        time.sleep(2)  # Brief pause between skills
                        self._start_next_batch_skill()
                    threading.Thread(target=start_next, daemon=True).start()
                else:
                    ConsoleLog("BatchCapture", "All skills in batch completed!", log=True)
                    print("Batch capture completed!")
                    self.batch_skills = []
                    self.current_batch_index = 0
            else:
                print("Capture stopped")
        except Exception as e:
            print(f"Error stopping capture: {e}")
# ============================================================================
#region MAIN EXECUTION
# ============================================================================

# Initialize GUI first
gui = EliteSkillsGUI(bot)


# Register all elite skill builders as base FSM states (PvE-bot style)
bot.States.AddCustomState(EnergySurge, "[H]Energy Surge")
bot.States.AddCustomState(PiousRenewal, "[H]Pious Renewal")
bot.States.AddCustomState(BloodIsPower, "[H]Blood is Power")
bot.States.AddCustomState(VowOfStrengthLocals, "[H]Vow of Strength Locals")
bot.States.AddCustomState(Ineptitude, "[H]Ineptitude")
bot.States.AddCustomState(Migraine, "[H]Migraine")
bot.States.AddCustomState(SpoilVictor, "[H]Spoil Victor")
bot.States.AddCustomState(SignetOfSpirits, "[H]Signet of Spirits")
bot.States.AddCustomState(SpitefulSpirit, "[H]Spiteful Spirit")
bot.States.AddCustomState(MistForm, "[H]Mist Form")
bot.States.AddCustomState(SignetOfJudgement, "[H]Signet of Judgement")
bot.States.AddCustomState(IllusionaryWeaponry, "[H]Illusionary Weaponry")
bot.States.AddCustomState(ShadowForm, "[H]Shadow Form")
bot.States.AddCustomState(ShadowFormWoC, "[H]Shadow Form - WoC")
bot.States.AddCustomState(BroadHeadArrow, "[H]Broad Head Arrow")
bot.States.AddCustomState(SoulTwisting, "[H]Soul Twisting")
bot.States.AddCustomState(PrimalRage, "[H]Primal Rage")
bot.States.AddCustomState(ShadowPrison, "[H]Shadow Prison")
bot.States.AddCustomState(SoldiersFury, "[H]Soldier's Fury")
bot.States.AddCustomState(ObsidianFlesh, "[H]Obsidian Flesh")
bot.States.AddCustomState(Eviscerate, "[H]Eviscerate")
bot.States.AddCustomState(GreaterConflagration, "[H]Greater Conflagration")
bot.States.AddCustomState(AuraOfTheLich, "[H]Aura of the Lich")
bot.States.AddCustomState(Panic, "[H]Panic")
bot.States.AddCustomState(MindBurn, "[H]Mind Burn")
bot.States.AddCustomState(AssassinsPromise, "[H]Assassin's Promise")
bot.States.AddCustomState(UnyieldingAura, "[H]Unyielding Aura")
bot.States.AddCustomState(VictoryIsMine, "[H]Victory is Mine")
bot.States.AddCustomState(PoisonArrow, "[H]Poison Arrow")
bot.States.AddCustomState(PlagueSignet, "[H]Plague Signet")
bot.States.AddCustomState(GlimmeringMark, "[H]Glimmering Mark")
bot.States.AddCustomState(SpellBreaker, "[H]Spell Breaker")
bot.States.AddCustomState(MantraOfRecall, "[H]Mantra of Recall")
bot.States.AddCustomState(MindShock, "[H]Mind Shock")
bot.States.AddCustomState(VowOfSilence, "[H]Vow of Silence")
bot.States.AddCustomState(GlimmerOfLight, "[H]Glimmer of Light")
bot.States.AddCustomState(Onslaught, "[H]Onslaught")
bot.States.AddCustomState(EbonDustAura, "[H]Ebon Dust Aura")
bot.States.AddCustomState(AvatarOfBalthazar, "[H]Avatar of Balthazar")
bot.States.AddCustomState(AvatarOfMelandru, "[H]Avatar of Melandru")
bot.States.AddCustomState(AvatarOfDwayna, "[H]Avatar of Dwayna")
bot.States.AddCustomState(AvatarOfLyssa, "[H]Avatar of Lyssa")
bot.States.AddCustomState(AvatarOfGrenth, "[H]Avatar of Grenth")
bot.States.AddCustomState(XinraesWeapon, "[H]Xinrae's Weapon")
bot.States.AddCustomState(Incoming, "[H]Incoming!")
bot.States.AddCustomState(FocusedAnger, "[H]Focused Anger")
bot.States.AddCustomState(MarkOfProtection, "[H]Mark of Protection")
bot.States.AddCustomState(PreparedShot, "[H]Prepared Shot")
bot.States.AddCustomState(TogetherAsOne, "[H]Together as One")
bot.States.AddCustomState(HeroicRefrain, "[H]Heroic Refrain")
bot.States.AddCustomState(SoulTaker, "[H]Soul Taker")
bot.States.AddCustomState(OverTheLimit, "[H]Over The Limit")
bot.States.AddCustomState(JudgmentStrike, "[H]Judgment Strike")
bot.States.AddCustomState(TimeWard, "[H]Time Ward")
bot.States.AddCustomState(VowOfRevolution, "[H]Vow of Revolution")
bot.States.AddCustomState(SevenWeaponStance, "[H]Seven Weapon Stance")
bot.States.AddCustomState(WeaponsOfThreeForges, "[H]Weapons of Three Forges")
bot.States.AddCustomState(ShadowTheft, "[H]Shadow Theft")
bot.States.AddCustomState(AnthemofGuidance, "[H]Anthem of Guidance")
bot.States.AddCustomState(CripplingAnthem, "[H]Crippling Anthem")
bot.States.AddCustomState(AngelicBond, "[H]Angelic Bond")
bot.States.AddCustomState(AnthemofFury, "[H]Anthem of Fury")
bot.States.AddCustomState(DefensiveAnthem, "[H]Defensive Anthem")
bot.States.AddCustomState(ItsJustaFleshWound, "[H]It's Just a Flesh Wound.")
bot.States.AddCustomState(ThePowerIsYours, "[H]The Power Is Yours!")
bot.States.AddCustomState(SongofPurification, "[H]Song of Purification")
bot.States.AddCustomState(SongofRestoration, "[H]Song of Restoration")
bot.States.AddCustomState(CruelSpear, "[H]Cruel Spear")
bot.States.AddCustomState(StunningStrike, "[H]Stunning Strike")
bot.States.AddCustomState(CauterySignet, "[H]Cautery Signet")
bot.States.AddCustomState(ArcaneZeal, "[H]Arcane Zeal")
bot.States.AddCustomState(GrenthsGrasp, "[H]Grenth's Grasp")
bot.States.AddCustomState(ReapersSweep, "[H]Reaper's Sweep")
bot.States.AddCustomState(VowofStrength, "[H]Vow of Strength")
bot.States.AddCustomState(WoundingStrike, "[H]Wounding Strike")
bot.States.AddCustomState(ZealousVow, "[H]Zealous Vow")
bot.States.AddCustomState(BlessedLight, "[H]Blessed Light")
bot.States.AddCustomState(HealingLight, "[H]Healing Light")
bot.States.AddCustomState(BoonSignet, "[H]Boon Signet")
bot.States.AddCustomState(HealersBoon, "[H]Healer's Boon")
bot.States.AddCustomState(PeaceandHarmony, "[H]Peace and Harmony")
bot.States.AddCustomState(WithdrawHexes, "[H]Withdraw Hexes")
bot.States.AddCustomState(HealingBurst, "[H]Healing Burst")
bot.States.AddCustomState(HealingHands, "[H]Healing Hands")
bot.States.AddCustomState(LightofDeliverance, "[H]Light of Deliverance")
bot.States.AddCustomState(WordofHealing, "[H]Word of Healing")
bot.States.AddCustomState(AirofEnchantment, "[H]Air of Enchantment")
bot.States.AddCustomState(AuraofFaith, "[H]Aura of Faith")
bot.States.AddCustomState(DivertHexes, "[H]Divert Hexes")
bot.States.AddCustomState(LifeSheath, "[H]Life Sheath")
bot.States.AddCustomState(ShieldOfRegeneration, "[H]Shield of Regeneration")
bot.States.AddCustomState(ZealousBenediction, "[H]Zealous Benediction")
bot.States.AddCustomState(DefendersZeal, "[H]Defender's Zeal")
bot.States.AddCustomState(RayofJudgment, "[H]Ray of Judgment")
bot.States.AddCustomState(WordOfCensure, "[H]Word of Censure")
bot.States.AddCustomState(EmpathicRemoval, "[H]Empathic Removal")
bot.States.AddCustomState(Martyr, "[H]Martyr")
bot.States.AddCustomState(SignetOfRemoval, "[H]Signet of Removal")
bot.States.AddCustomState(BalthazarsPendulum, "[H]Balthazar's Pendulum")
bot.States.AddCustomState(ReapersMark, "[H]Reaper's Mark")
bot.States.AddCustomState(Charge, "[H]Charge!")
bot.States.AddCustomState(Coward, "[H]Coward!")
bot.States.AddCustomState(YoureAllAlone, "[H]You're All Alone!")
bot.States.AddCustomState(AuspiciousParry, "[H]Auspicious Parry")
bot.States.AddCustomState(Backbreaker, "[H]Backbreaker")
bot.States.AddCustomState(BattleRage, "[H]Battle Rage")
bot.States.AddCustomState(BullsCharge, "[H]Bull's Charge")
bot.States.AddCustomState(ChargingStrike, "[H]Charging Strike")
bot.States.AddCustomState(Cleave, "[H]Cleave")
bot.States.AddCustomState(CripplingSlash, "[H]Crippling Slash")
bot.States.AddCustomState(Decapitate, "[H]Decapitate")
bot.States.AddCustomState(DefyPain, "[H]Defy Pain")
bot.States.AddCustomState(DevastatingHammer, "[H]Devastating Hammer")
bot.States.AddCustomState(DragonSlash, "[H]Dragon Slash")
bot.States.AddCustomState(DwarvenBattleStance, "[H]Dwarven Battle Stance")
#bot.States.AddCustomState(EarthShaker, "[H]Earth Shaker")
bot.States.AddCustomState(EnragedSmash, "[H]Enraged Smash")
#bot.States.AddCustomState(Flourish, "[H]Flourish")
bot.States.AddCustomState(ForcefulBlow, "[H]Forceful Blow")
#bot.States.AddCustomState(GladiatorsDefense, "[H]Gladiator's Defense")
bot.States.AddCustomState(Headbutt, "[H]Headbutt")
bot.States.AddCustomState(HundredBlades, "[H]Hundred Blades")
bot.States.AddCustomState(MagehunterStrike, "[H]Magehunter Strike")
bot.States.AddCustomState(MagehuntersSmash, "[H]Magehunter's Smash")
bot.States.AddCustomState(QuiveringBlade, "[H]Quivering Blade")
bot.States.AddCustomState(RageoftheNtouka, "[H]Rage of the Ntouka")
bot.States.AddCustomState(Shove, "[H]Shove")
bot.States.AddCustomState(SkullCrack, "[H]Skull Crack")
bot.States.AddCustomState(SoldiersStance, "[H]Soldier's Stance")
bot.States.AddCustomState(SteadyStance, "[H]Steady Stance")
bot.States.AddCustomState(TripleChop, "[H]Triple Chop")
bot.States.AddCustomState(WarriorsEndurance, "[H]Warrior's Endurance")
bot.States.AddCustomState(WhirlingAxe, "[H]Whirling Axe")
bot.States.AddCustomState(LifeBarrier, "[H]Life Barrier")
bot.States.AddCustomState(Way_of_the_Assassin, "[H]Way of the Assassin")
bot.States.AddCustomState(Dark_Apostasy, "[H]Dark Apostasy")
bot.States.AddCustomState(Locusts_Fury, "[H]Locust's Fury")
bot.States.AddCustomState(Palm_Strike, "[H]Palm Strike")
bot.States.AddCustomState(Seeping_Wound, "[H]Seeping Wound")
bot.States.AddCustomState(Flashing_Blades, "[H]Flashing Blades")
bot.States.AddCustomState(Foxs_Promise, "[H]Fox's Promise")
bot.States.AddCustomState(Psychic_Instability, "[H]Psychic Instability")
bot.States.AddCustomState(Shadow_Shroud, "[H]Shadow Shroud")
bot.States.AddCustomState(Shattering_Assault, "[H]Shattering Assault")
bot.States.AddCustomState(AuraofDisplacement, "[H]Aura of Displacement")
bot.States.AddCustomState(MarkofInsecurity, "[H]Mark of Insecurity")
bot.States.AddCustomState(HiddenCaltrops, "[H]Hidden Caltrops")
bot.States.AddCustomState(AssaultEnchantments, "[H]Assault Enchantments")
bot.States.AddCustomState(ShadowMeld, "[H]Shadow Meld")
bot.States.AddCustomState(WastrelsCollapse, "[H]Wastrel's Collapse")
bot.States.AddCustomState(GoldenSkullStrike, "[H]Golden Skull Strike")
bot.States.AddCustomState(Temple_Strike, "[H]Temple Strike")
bot.States.AddCustomState(Moebius_Strike, "[H]Moebius Strike")
bot.States.AddCustomState(Shroud_of_Silence, "[H]Shroud of Silence")
bot.States.AddCustomState(Siphon_Strength, "[H]Siphon Strength")
bot.States.AddCustomState(Way_of_the_Empty_Palm, "[H]Way of the Empty Palm")
bot.States.AddCustomState(Beguiling_Haze, "[H]Beguiling Haze")
# Record base builder state count (used to append/remove dynamic sub-steps)
gui._original_state_count = len(bot.config.FSM.states)
gui._last_original_next = bot.config.FSM.states[-1].next_state if bot.config.FSM.states else None

def Draw_Window():
    """Main GUI drawing function"""
    gui.draw_main_window()
    bot.UI.DrawPath()

def main():
    bot.Update()
    Draw_Window()
    
    # Check if capture completed and reset flag
    if gui.capture_running:
        try:
            fsm = bot.config.FSM
            if hasattr(fsm, 'finished') and fsm.finished:
                gui.capture_running = False
                gui.capture_start_time = None
                print(f"Capture completed for {gui.selected_skill.display_name if gui.selected_skill else 'unknown skill'}")
            elif hasattr(fsm, 'current_state') and fsm.current_state is None:
                gui.capture_running = False
                gui.capture_start_time = None
                print(f"Capture completed for {gui.selected_skill.display_name if gui.selected_skill else 'unknown skill'}")
        except:
            pass

if __name__ == "__main__":
    main()

