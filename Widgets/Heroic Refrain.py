from Py4GWCoreLib import PyImGui, GLOBAL_CACHE, IniHandler, Timer, ThrottledTimer
from HeroAI.cache_data import CacheData
from HeroAI.constants import MAX_NUM_PLAYERS

import os
import sys
import configparser
from Py4GWCoreLib import *
from typing import Set

'''
This widget draws a floating window with every HeroAI player and hero in the party and tracks their HR buff status.
Players/heroes without HR have a clickable blue button to apply HR to them.
'''

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
project_root     = os.path.abspath(os.path.join(script_directory, os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ─── Window Persistence Setup ───────────────────────────────────────────
WINDOW_SECTION = "Heroic Refrain"
ini_window = IniHandler(os.path.join(script_directory, "Config", "Heroic_Refrain_window.ini"))
save_window_timer = Timer()
save_window_timer.Start()

# ─── INI File Setup ─────────────────────────────────────────────────────
BASE_DIR = os.path.join(project_root, "Config")
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
ini_window = IniHandler(os.path.join(script_directory, "Config", "Heroic_Refrain_window.ini"))
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

_run_sequence_called = False

# ─── External API ────────────────────────────────────────────────────────────

def cast_heroic_refrain():
    global cached_data, buff_check_timer, player_data_cache, player_data_timer
    heroic_refrain_skill_id = GLOBAL_CACHE.Skill.GetID("Heroic_Refrain")
    
    # check if player is in explorable area
    if not GLOBAL_CACHE.Map.IsExplorable():
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
        update_player_data_cache()
    
    # update buff data from buff cache every 250ms
    if buff_check_timer.IsExpired():
        buff_check_timer.Reset()
        update_buff_cache()
    
    # render UI using cached data
    render_heroic_refrain_ui()

def update_player_data_cache():
    global player_data_cache, cached_data
    
    # create new cache so we don't overwrite the existing cache
    new_cache = {}
    
    # add player data to cache
    for index in range(MAX_NUM_PLAYERS):
        player_struct = cached_data.HeroAI_vars.all_player_struct[index]
        if player_struct.IsActive:
            try:
                login_number = GLOBAL_CACHE.Party.Players.GetLoginNumberByAgentID(player_struct.PlayerID)
                if login_number > 0:
                    player_name = GLOBAL_CACHE.Party.Players.GetPlayerNameByLoginNumber(login_number)
                    
                    # preserve existing buff status if player was already in cache
                    existing_buff_status = False
                    if index in player_data_cache:
                        existing_buff_status = player_data_cache[index].get('has_heroic_refrain', False)
                    
                    new_cache[index] = {
                        'player_id': player_struct.PlayerID,
                        'player_name': player_name,
                        'login_number': login_number,
                        'has_heroic_refrain': existing_buff_status,
                        'is_hero': False
                    }
            except:
                continue
    
    # add hero
    heroes = GLOBAL_CACHE.Party.GetHeroes()
    for hero_index, hero in enumerate(heroes):
        try:
            # distinguish heroes from players
            cache_key = -(hero_index + 1)  # -1, -2, -3, etc.
            hero_name = hero.hero_id.GetName()
            hero_agent_id = hero.agent_id
            
            # preserve existing buff status if hero was already in cache
            existing_buff_status = False
            if cache_key in player_data_cache:
                existing_buff_status = player_data_cache[cache_key].get('has_heroic_refrain', False)
            
            new_cache[cache_key] = {
                'player_id': hero_agent_id,
                'player_name': hero_name,
                'login_number': 0,
                'has_heroic_refrain': existing_buff_status,
                'is_hero': True,
                'hero_index': hero_index
            }
        except:
            continue
    
    # replace player/hero cache with most recent temp cache
    player_data_cache = new_cache

def update_buff_cache():
    """ update buff information for all cached players """
    global player_data_cache, cached_data
    
    for index, player_data in player_data_cache.items():
        try:
            player_buffs = cached_data.HeroAI_vars.shared_memory_handler.get_agent_buffs(player_data['player_id'])
            player_data['has_heroic_refrain'] = 3431 in player_buffs
        except:
            player_data['has_heroic_refrain'] = False

def render_heroic_refrain_ui():
    """ render UI using cached data """
    global player_data_cache
    
    # separate players and heroes
    players = {}
    heroes = {}
    
    for index, player_data in player_data_cache.items():
        if player_data['is_hero']:
            heroes[index] = player_data
        else:
            players[index] = player_data
    
    # render players first
    if players:
        for index, player_data in players.items():
            player_name = player_data['player_name']
            has_heroic_refrain = player_data['has_heroic_refrain']
            
            if not has_heroic_refrain:
                if PyImGui.button(f"{player_name}##hr_cast_player_{index}"):
                    cast_heroic_refrain_on_player(player_data['player_id'])
            else:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.3, 0.3, 0.3, 1.0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.35, 0.35, 0.35, 1.0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.25, 0.25, 0.25, 1.0))
                PyImGui.button(f"{player_name} ##hr_disabled_player_{index}")
                PyImGui.pop_style_color(3)
    
    # render heroes after players
    if heroes:
        for index, hero_data in heroes.items():
            hero_name = hero_data['player_name']
            has_heroic_refrain = hero_data['has_heroic_refrain']
            
            if not has_heroic_refrain:
                if PyImGui.button(f"{hero_name}##hr_cast_hero_{index}"):
                    cast_heroic_refrain_on_hero(hero_data['player_id'], hero_data['hero_index'])
            else:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, (0.3, 0.3, 0.3, 1.0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.35, 0.35, 0.35, 1.0))
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, (0.25, 0.25, 0.25, 1.0))
                PyImGui.button(f"{hero_name} ##hr_disabled_hero_{index}")
                PyImGui.pop_style_color(3)

def cast_heroic_refrain_on_player(player_id):
    heroic_refrain_skill_id = GLOBAL_CACHE.Skill.GetID("Heroic_Refrain")
    slot_number = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(heroic_refrain_skill_id)
    GLOBAL_CACHE.SkillBar.UseSkill(slot_number, player_id)

def cast_heroic_refrain_on_hero(player_id, hero_index):
    heroic_refrain_skill_id = GLOBAL_CACHE.Skill.GetID("Heroic_Refrain")
    slot_number = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(heroic_refrain_skill_id)
    GLOBAL_CACHE.SkillBar.UseSkill(slot_number, player_id)

def main():
    if not Routines.Checks.Map.MapValid():
        return
    me = Player.GetAgentID()
    on_imgui_render(me)

__all__ = ["main", "configure", "cast_heroic_refrain"]
