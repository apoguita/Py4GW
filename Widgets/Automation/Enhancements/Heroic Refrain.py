from Py4GWCoreLib import PyImGui, GLOBAL_CACHE, IniHandler, Timer, ThrottledTimer
from HeroAI.cache_data import CacheData
from HeroAI.constants import MAX_NUM_PLAYERS

import os
import sys
import configparser
from Py4GWCoreLib import *
from typing import Set

from Py4GWCoreLib.GlobalCache.SharedMemory import AccountStruct

'''
This widget draws a floating window with every HeroAI player and hero in the party and tracks their HR buff status.
Players/heroes without HR have a clickable blue button to apply HR to them.
'''

MODULE_NAME = "Heroic Refrain Manager"
MODULE_ICON = "Textures\\Skill_Icons\\[3431] - Heroic Refrain.jpg"

# global cached data singleton
cached_data = CacheData()

# timer used to check buffs every 250ms instead of every frame
buff_check_timer = ThrottledTimer(250)  

# cache player data so we don't grab it every frame
player_data_cache = {}

# check for player data every 500ms
player_data_timer = ThrottledTimer(500)

# ─── Import the game's API ────────────────────────────────────────────────
from Py4GWCoreLib import Player, Party, PyImGui, IniHandler, Timer

# ─── Make sure "heroic_refrain" is on the import path ──────────────────
script_directory = os.path.dirname(os.path.abspath(__file__))
project_root     = Py4GW.Console.get_projects_path()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ─── Window Persistence Setup ───────────────────────────────────────────
WINDOW_SECTION = "Heroic Refrain"
ini_window = IniHandler(os.path.join(project_root, "Widgets", "Config", "Heroic_Refrain_window.ini"))
save_window_timer = Timer()
save_window_timer.Start()

# ─── INI File Setup ─────────────────────────────────────────────────────
BASE_DIR = os.path.join(project_root, "Widgets", "Config")
INI_PATH = os.path.join(BASE_DIR, "Heroic_Refrain_Config.ini")
os.makedirs(BASE_DIR, exist_ok=True)

def _read_ini() -> configparser.ConfigParser:
    cp = configparser.ConfigParser()
    cp.read(INI_PATH)
    return cp

def read_run_flag() -> bool:
    return _read_ini().getboolean("HeroicRefrain", "Enabled", fallback=False)

def write_run_flag(val: bool):
    cp = _read_ini()
    if not cp.has_section("HeroicRefrain"):
        cp.add_section("HeroicRefrain")
    cp.set("HeroicRefrain", "Enabled", str(val))
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(INI_PATH, "w") as f:
        cp.write(f)

# ─── UI Configuration ──────────────────────────────────────────────────
cfg            = _read_ini()
LEADER_UI      = cfg.getboolean("Settings",   "LeaderUI",    fallback=True)
PER_CLIENT_UI  = cfg.getboolean("Settings",   "PerClientUI", fallback=False)
AUTO_RUN_ALL   = cfg.getboolean("HeroicRefrain","AutoRunAll",  fallback=True)

# ─── Window Persistence Setup ───────────────────────────────────────────
WINDOW_SECTION = "Heroic Refrain"
ini_window = IniHandler(os.path.join(project_root, "Widgets", "Config", "Heroic_Refrain_window.ini"))
save_window_timer = Timer()
save_window_timer.Start()

# load last-saved window state (fallbacks)
win_x = ini_window.read_int(WINDOW_SECTION, "x", 100)
win_y = ini_window.read_int(WINDOW_SECTION, "y", 100)
win_collapsed = ini_window.read_bool(WINDOW_SECTION, "collapsed", False)
first_run_window = True
slot_number = 0

# ─── Frame‐by‐frame UI logic ────────────────────────────────────────────
def on_imgui_render(me: int):
    global _running, _last_flag, _consumed
    global first_run_window, win_x, win_y, win_collapsed, slot_number

    # Show the widget only if HR is equipped
    heroic_refrain_skill_id = GLOBAL_CACHE.Skill.GetID("Heroic_Refrain")
    try:
        slot_number = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(heroic_refrain_skill_id)
    except IndexError:
        pass
    if not slot_number:
        return

    # Restore window position & collapsed state on first run
    if first_run_window:
        PyImGui.set_next_window_pos(win_x, win_y)
        PyImGui.set_next_window_collapsed(win_collapsed, 0)
        first_run_window = False

    # (E) draw
    PyImGui.begin("Heroic Refrain", PyImGui.WindowFlags.AlwaysAutoResize)
    # capture current state
    new_collapsed = PyImGui.is_window_collapsed()
    end_pos = PyImGui.get_window_pos()

    PyImGui.text("Click to cast HR")
    PyImGui.separator()

    cast_heroic_refrain()

    PyImGui.end()

    # ─── Persist window state once per second ────────────────────────────
    if save_window_timer.HasElapsed(1000):
        if (end_pos[0], end_pos[1]) != (win_x, win_y):
            win_x, win_y = int(end_pos[0]), int(end_pos[1])
            ini_window.write_key(WINDOW_SECTION, "x", str(win_x))
            ini_window.write_key(WINDOW_SECTION, "y", str(win_y))
        if new_collapsed != win_collapsed:
            win_collapsed = new_collapsed
            ini_window.write_key(WINDOW_SECTION, "collapsed", str(win_collapsed))
        save_window_timer.Reset()

# ─── Widget Manager Hooks ───────────────────────────────────────────────
def setup():
    pass

def configure():
    setup()
    
def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Heroic Refrain Manager", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("A specialized buff management widget for the Paragon 'Heroic Refrain' skill.")
    PyImGui.text("It monitors the status of this essential attribute-boosting shout across")
    PyImGui.text("all players and heroes in the multiboxed party.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Buff Tracking: Real-time visual monitoring of HR status for every party member")
    PyImGui.bullet_text("One-Click Application: Interactive buttons to instantly apply HR to those without it")
    PyImGui.bullet_text("Hero & Player Support: Differentiates between account players and AI heroes for casting")
    PyImGui.bullet_text("Shared Memory Sync: Leverages AccountData to track status across multiple clients")
    PyImGui.bullet_text("Optimized Performance: Throttled timers for buff checking and data caching to save CPU")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by SikroK")
    PyImGui.bullet_text("Contributors: Mnemonicide, Apo, frenkey")

    PyImGui.end_tooltip()

_run_sequence_called = False

# ─── External API ────────────────────────────────────────────────────────────

def cast_heroic_refrain():
    global cached_data, buff_check_timer, player_data_cache, player_data_timer
    heroic_refrain_skill_id = GLOBAL_CACHE.Skill.GetID("Heroic_Refrain")
    
    # check if player is in explorable area
    if not Map.IsExplorable():
        PyImGui.text("Enter explorable area")
        return
    
    # check if HR is on skill bar
    slot_number = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(heroic_refrain_skill_id)
    if not slot_number:
        PyImGui.text("Heroic Refrain not found")
        return
    
    # update player data from player cache every 500ms
    if player_data_timer.IsExpired():
        player_data_timer.Reset()
    
    # update buff data from buff cache every 250ms
    if buff_check_timer.IsExpired():
        buff_check_timer.Reset()
        update_buff_cache()
    
    # render UI using cached data
    render_heroic_refrain_ui()

def update_buff_cache():
    """ update buff information for all cached players """
    global player_data_cache, cached_data
    
    for index, player_data in player_data_cache.items():
        try:
            account = GLOBAL_CACHE.ShMem.GetAccountDataFromPartyNumber(index)
            player_data['has_heroic_refrain'] = any(buff.SkillId == 3431 and buff.Remaining > 0 for buff in account.AgentData.Buffs.Buffs) if account else False
        except:
            player_data['has_heroic_refrain'] = False

def render_heroic_refrain_ui():
    """ render UI using cached data """
    global player_data_cache
    
    # Get all valid accounts once
    accounts = [
        account
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData()
        if account is not None
    ]

    # Extract heroes for each valid account
    acc_heroes = [
        hero
        for account in accounts
        for hero in GLOBAL_CACHE.ShMem.GetHeroesFromPlayers(account.AgentData.AgentID)
        if hero is not None
    ]
    
    # render players first
    for data in [accounts, acc_heroes]:
        for account in data:
            has_heroic_refrain = any(buff.SkillId == 3431 and buff.Remaining > 0 for buff in account.AgentData.Buffs.Buffs) if account else False 
            
            if not has_heroic_refrain:
                if PyImGui.button(f"{account.AgentData.CharacterName}##hr_cast_{account.AgentData.AgentID}"):
                    if account.IsHero:
                        cast_heroic_refrain_on_hero(account.AgentData.AgentID)
                    else:
                        cast_heroic_refrain_on_player(account.AgentData.AgentID)
            else:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.3, 0.3, 0.3, 1.0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.35, 0.35, 0.35, 1.0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.25, 0.25, 0.25, 1.0))
                PyImGui.button(f"{account.AgentData.CharacterName} ##hr_disabled_{account.AgentData.AgentID}")
                PyImGui.pop_style_color(3)
                

def cast_heroic_refrain_on_player(player_id):
    heroic_refrain_skill_id = GLOBAL_CACHE.Skill.GetID("Heroic_Refrain")
    slot_number = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(heroic_refrain_skill_id)
    GLOBAL_CACHE.SkillBar.UseSkill(slot_number, player_id)

def cast_heroic_refrain_on_hero(player_id):
    heroic_refrain_skill_id = GLOBAL_CACHE.Skill.GetID("Heroic_Refrain")
    slot_number = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(heroic_refrain_skill_id)
    GLOBAL_CACHE.SkillBar.UseSkill(slot_number, player_id)

def main():
    if not Routines.Checks.Map.MapValid():
        return
    me = Player.GetAgentID()
    on_imgui_render(me)

__all__ = ["main", "configure", "cast_heroic_refrain"]