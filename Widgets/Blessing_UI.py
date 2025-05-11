# Blessing_UI.py
import os
import sys
import tempfile
import configparser
from typing import Set

# ─── Import the game’s API ────────────────────────────────────────────────
from Py4GWCoreLib import Player, Party, PyImGui

# ─── Make sure “Blessed_helpers” is on the import path ──────────────────
script_directory = os.path.dirname(os.path.abspath(__file__))
project_root     = os.path.abspath(os.path.join(script_directory, os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ─── Now import your facade package ──────────────────────────────────────
from Bots.Blessed_helpers import has_any_blessing, BlessingRunner, FLAG_DIR

# ─── INI File Setup ─────────────────────────────────────────────────────
BASE_DIR = os.path.join(project_root, "Config")
INI_PATH = os.path.join(BASE_DIR, "Blessed_Config.ini")
os.makedirs(BASE_DIR, exist_ok=True)

def _read_ini() -> configparser.ConfigParser:
    cp = configparser.ConfigParser()
    cp.read(INI_PATH)
    return cp

def read_run_flag() -> bool:
    return _read_ini().getboolean("BlessingRun", "Enabled", fallback=False)

def write_run_flag(val: bool):
    cp = _read_ini()
    if not cp.has_section("BlessingRun"):
        cp.add_section("BlessingRun")
    cp.set("BlessingRun", "Enabled", str(val))
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(INI_PATH, "w") as f:
        cp.write(f)

# ─── UI Configuration ──────────────────────────────────────────────────
cfg            = _read_ini()
LEADER_UI      = cfg.getboolean("Settings",   "LeaderUI",    fallback=True)
PER_CLIENT_UI  = cfg.getboolean("Settings",   "PerClientUI", fallback=False)
AUTO_RUN_ALL   = cfg.getboolean("BlessingRun","AutoRunAll",  fallback=True)

# ─── FSM runner + shared-flag state ────────────────────────────────────
_runner    = BlessingRunner()
_running   = False
_last_flag = False
_consumed  = False

# ─── Frame‐by‐frame UI logic ────────────────────────────────────────────
def on_imgui_render(me: int):
    global _running, _last_flag, _consumed

    # (A) sync per‐client flag files
    my_id   = Player.GetAgentID()
    my_file = os.path.join(FLAG_DIR, f"{my_id}.flag")
    if has_any_blessing(my_id):
        if not os.path.exists(my_file):
            open(my_file, "w").close()
    else:
        if os.path.exists(my_file):
            os.remove(my_file)

    # (B) shared run‐flag coordination
    flag = read_run_flag()
    if flag != _last_flag:
        _consumed  = False
        _last_flag = flag

    if flag and not _running and not _consumed:
        _runner.start()
        _running, _consumed = True, True

    if _running:
        done, _ = _runner.update()
        if done:
            if AUTO_RUN_ALL and Party.GetPartyLeaderID() == me:
                write_run_flag(False)
            _running = False

    # (C) only show UI if leader or per‐client mode
    slots    = Party.GetPlayers()
    if not slots:
        return
    is_leader = (Party.GetPartyLeaderID() == me)
    if not (LEADER_UI and is_leader) and not PER_CLIENT_UI:
        return

    # (D) collect who’s blessed
    blessed_ids: Set[int] = set()
    for fn in os.listdir(FLAG_DIR):
        if fn.endswith(".flag"):
            try:
                blessed_ids.add(int(fn[:-5]))
            except ValueError:
                pass

    # (E) draw
    PyImGui.begin("Blessing Controller")
    PyImGui.text("Party Blessing Status:")
    PyImGui.separator()

    for slot in slots:
        ln = slot.login_number
        ag = Party.Players.GetAgentIDByLoginNumber(ln)
        nm = Party.Players.GetPlayerNameByLoginNumber(ln)
        role = "Leader" if ag == Party.GetPartyLeaderID() else "Ai Hero"
        mark = "Blessed" if ag in blessed_ids else "Unholy"
        PyImGui.text(f"[{ln}] {nm} ({role}) [{mark}]")

    PyImGui.separator()
    if not _running and PyImGui.button("Run Blessing Sequence"):
        if AUTO_RUN_ALL and is_leader:
            write_run_flag(True)
            _runner.start()
            _running = True
        elif not AUTO_RUN_ALL:
            _runner.start()
            _running = True

    if _running:
        PyImGui.text("Running blessing sequence…")

    PyImGui.end()

# ─── Widget Manager Hooks ───────────────────────────────────────────────
def setup():
    # any one-time initialization you need can go here
    pass

def configure():
    setup()

_run_sequence_called = False

# ─── External API ────────────────────────────────────────────────────────────
def Get_Blessed():
    """
    External API: Called from outside scripts (e.g., bots, automation tools)
    to start the blessing sequence exactly as if the UI button had been clicked.
    """
    from Py4GWCoreLib import Player, Party

    me = Player.GetAgentID()
    is_leader = (Party.GetPartyLeaderID() == me)

    # Mirror the AUTO_RUN_ALL + leader logic
    if AUTO_RUN_ALL and is_leader:
        write_run_flag(True)

    # Start the background blessing runner
    _runner.start()

    # Let the UI know we’re running
    global _running
    _running = True

def main():
    me = Player.GetAgentID()
    on_imgui_render(me)

__all__ = ["main", "configure", "Get_Blessed"]
