import os
import sys
import configparser
from typing import Set

from Py4GWCoreLib import *
from Bots.aC_Scripts.aC_api import has_any_blessing, BlessingRunner, FLAG_DIR

# ─── Paths & Configuration ─────────────────────────────────────────────────
script_directory = os.getcwd()
project_root     = Py4GW.Console.get_projects_path()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

BASE_DIR  = os.path.join(project_root, "Widgets", "Config")
INI_PATH  = os.path.join(BASE_DIR, "Blessed_Config.ini")
os.makedirs(BASE_DIR, exist_ok=True)

WINDOW_SECTION = "Get Blessed"
win_ini_path   = os.path.join(script_directory, "Widgets", "Config", "GetBlessed_window.ini")

# ─── INI Read/Write ────────────────────────────────────────────────────────
def _read_ini() -> configparser.ConfigParser:
    cp = configparser.ConfigParser()
    cp.read(INI_PATH)
    return cp

def read_run_flag() -> bool:
    return _read_ini().get("BlessingRun", "Enabled", fallback="false").strip().lower() == "true"

def write_run_flag(val: bool):
    cp = _read_ini()
    if not cp.has_section("BlessingRun"):
        cp.add_section("BlessingRun")
    cp.set("BlessingRun", "Enabled", str(val))
    with open(INI_PATH, "w") as f:
        cp.write(f)

# ─── UI Settings ───────────────────────────────────────────────────────────
cfg            = _read_ini()
LEADER_UI      = cfg.getboolean("Settings",   "LeaderUI",    fallback=True)
PER_CLIENT_UI  = cfg.getboolean("Settings",   "PerClientUI", fallback=False)
AUTO_RUN_ALL   = cfg.getboolean("BlessingRun","AutoRunAll",  fallback=True)

# ─── Window Persistence ─────────────────────────────────────────────────────
ini_handler = IniHandler(win_ini_path)
save_timer  = Timer(); save_timer.Start()
win_x       = ini_handler.read_int(WINDOW_SECTION, "x", 100)
win_y       = ini_handler.read_int(WINDOW_SECTION, "y", 100)
win_coll    = ini_handler.read_bool(WINDOW_SECTION, "collapsed", False)
first_run   = True

# ─── Runner & State ────────────────────────────────────────────────────────
_runner     = BlessingRunner()
_running    = False
_last_flag  = False
_consumed   = False
i_am_blessed = False

# ─── Caches & Timers ───────────────────────────────────────────────────────
_sync_timer         = ThrottledTimer(2000)   # 1s
_flag_timer         = ThrottledTimer(1500)    # 0.5s
_logic_scan_timer   = ThrottledTimer(2200)   # 1.2s

_last_dir_mtime     = 0
_cached_blessed_ids = set()

_last_party_hash    = None
_cached_slots       = []

_party_cache_timer  = ThrottledTimer(5200)
_party_cache_lines  = []

# ─── Flag Directory Scan ───────────────────────────────────────────────────
def _scan_flag_files():
    global _cached_blessed_ids, _last_dir_mtime
    try:
        mtime = os.stat(FLAG_DIR).st_mtime
    except OSError:
        return
    if mtime == _last_dir_mtime:
        return
    _last_dir_mtime = mtime
    new_set = set()
    for entry in os.scandir(FLAG_DIR):
        if entry.name.endswith(".flag"):
            try:
                new_set.add(int(entry.name[:-5]))
            except ValueError:
                pass
    _cached_blessed_ids = new_set

# ─── Party Cache Update ────────────────────────────────────────────────────
def _update_party_cache():
    global _cached_slots, _last_party_hash
    slots = Party.GetPlayers()
    current_hash = tuple(s.login_number for s in slots)
    if current_hash == _last_party_hash:
        return
    _last_party_hash = current_hash
    _cached_slots    = list(slots)

# ─── Main Logic Tick ───────────────────────────────────────────────────────
def _blessing_logic_tick(me: int):
    global _running, _last_flag, _consumed, i_am_blessed

    if _sync_timer.IsExpired():
        _sync_timer.Reset()
        my_id   = me
        my_file = os.path.join(FLAG_DIR, f"{my_id}.flag")
        has_b   = has_any_blessing(my_id)

        # gained blessing
        if not i_am_blessed and has_b:
            i_am_blessed = True
            if not os.path.exists(my_file):
                open(my_file, "w").close()
                ConsoleLog("Blessing", f"[{my_id}] created flag file", Console.MessageType.Info)
        # lost blessing
        elif i_am_blessed and not has_b:
            i_am_blessed = False
            if os.path.exists(my_file):
                os.remove(my_file)
                ConsoleLog("Blessing", f"[{my_id}] removed flag file", Console.MessageType.Info)

    if _flag_timer.IsExpired():
        _flag_timer.Reset()
        flag = read_run_flag()
        if flag != _last_flag:
            _consumed  = False
            _last_flag = flag
        if flag and not _running and not _consumed:
            _runner.start()
            _running   = True
            _consumed  = True

    if _running:
        done, _ = _runner.update()
        if done:
            if AUTO_RUN_ALL and Party.GetPartyLeaderID() == me:
                write_run_flag(False)
            _running = False

    if _logic_scan_timer.IsExpired():
        _logic_scan_timer.Reset()

# ─── UI Rendering ─────────────────────────────────────────────────────────
def on_imgui_render(me: int):
    global first_run, win_x, win_y, win_coll, _running
    global first_run, win_x, win_y, win_coll

    # Only draw when leader UI or per-client UI is enabled
    leader_id = None
    try:
        leader_id = GLOBAL_CACHE.Party.GetPartyLeaderID()
    except IndexError:
        pass
    if not ((LEADER_UI and leader_id == me) or PER_CLIENT_UI):
        return

    # Begin window
    PyImGui.begin("Get Blessed", PyImGui.WindowFlags.AlwaysAutoResize)

    if first_run:
        PyImGui.set_next_window_pos(win_x, win_y)
        PyImGui.set_next_window_collapsed(win_coll, 0)
        first_run = False

    # If collapsed, bail out early
    if PyImGui.is_window_collapsed():
        PyImGui.end()
        return

    win_coll = PyImGui.is_window_collapsed()
    pos      = PyImGui.get_window_pos()

    PyImGui.text("Party Blessing Status:")
    PyImGui.separator()

    # Update party cache lines once per interval
    if _party_cache_timer.IsExpired():
        _party_cache_timer.Reset()
        _party_cache_lines.clear()
        for slot in _cached_slots:
            ln = slot.login_number
            ag = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(ln)
            nm = GLOBAL_CACHE.Party.Players.GetPlayerNameByLoginNumber(ln)
            icon = IconsFontAwesome5.ICON_PRAYING_HANDS if ag in _cached_blessed_ids else IconsFontAwesome5.ICON_HANDS
            _party_cache_lines.append(f"{icon} {nm}")

    for line in _party_cache_lines:
        PyImGui.text(line)

    PyImGui.separator()

    if not _running and PyImGui.button("Get Party Blessed"):
        if AUTO_RUN_ALL and (GLOBAL_CACHE.Party.GetPartyLeaderID() == me):
            write_run_flag(True)
        _runner.start()
        _running = True

    if _running:
        PyImGui.text("Running blessing sequence")

    PyImGui.end()

    # Persist window state once per second
    if save_timer.HasElapsed(1000):
        save_timer.Reset()
        new_x, new_y = pos
        if (new_x, new_y) != (win_x, win_y):
            win_x, win_y = int(new_x), int(new_y)
            ini_handler.write_key(WINDOW_SECTION, "x", str(win_x))
            ini_handler.write_key(WINDOW_SECTION, "y", str(win_y))
        if win_coll != ini_handler.read_bool(WINDOW_SECTION, "collapsed", False):
            ini_handler.write_key(WINDOW_SECTION, "collapsed", str(win_coll))

# ─── Entrypoints ──────────────────────────────────────────────────────────
def setup():
    pass

def configure():
    setup()
    
def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Blessed", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("An automated blessing management utility designed to ensure")
    PyImGui.text("your party maintains essential combat buffs. It synchronizes")
    PyImGui.text("blessing sequences across multiboxed accounts.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Auto-Blessing: Automatically triggers sequences to refresh party buffs")
    PyImGui.bullet_text("Party Leader Sync: Optional 'Auto Run All' mode for leader-driven automation")
    PyImGui.bullet_text("Sequence Runner: Utilizes a dedicated 'BlessingRunner' for reliable casting")
    PyImGui.bullet_text("State Monitoring: Real-time tracking of active blessing status for all members")
    PyImGui.bullet_text("Persistence: Remembers window position and collapsed state via INI config")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by aC")

    PyImGui.end_tooltip()

def Get_Blessed():
    """External API trigger."""
    me = Player.GetAgentID()
    if AUTO_RUN_ALL and GLOBAL_CACHE.Party.GetPartyLeaderID() == me:
        write_run_flag(True)
    _runner.start()
    global _running
    _running = True

def main():
    if not Routines.Checks.Map.MapValid():
        return
    me = Player.GetAgentID()
    _scan_flag_files()
    _update_party_cache()
    _blessing_logic_tick(me)
    on_imgui_render(me)