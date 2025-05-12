import os
import tempfile
import configparser
import time
import math

from Py4GWCoreLib import *
from Bots.Blessed_helpers import (
    _Mover,
    is_npc_dialog_visible,
    click_dialog_button,
    get_dialog_button_count,
    move_interact_blessing_npc
)

_Mover = _Mover()

# —— INI & Flag Setup ——
FLAG_DIR = os.path.join(tempfile.gettempdir(), "GuildWarsNPCSync")
os.makedirs(FLAG_DIR, exist_ok=True)
INI_PATH = os.path.join(FLAG_DIR, "npc_sync.ini")
SECTION = "NPC_SYNC"

# —— FSM Constants ——
IDLE             = 0
MOVING_NPC       = 1  # walking up to NPC
IN_DIALOG        = 2
CHOICE_DONE      = 3
MOVING_LEADER    = 4  # walking to leader’s broadcast

DIALOG_RESET_TIMEOUT = 2.0

# —— Persistent State ——
last_model      = None
last_choice     = None
last_choice_time = None
state           = IDLE
last_leader_pos = None  # (x, y, timestamp)

# —— Config Helpers ——
def _load_config():
    cfg = configparser.ConfigParser()
    if os.path.exists(INI_PATH):
        cfg.read(INI_PATH)
    if SECTION not in cfg:
        cfg[SECTION] = {}
    return cfg

def _save_config(cfg):
    with open(INI_PATH, 'w') as f:
        cfg.write(f)

def clear_leader_data():
    if os.path.exists(INI_PATH):
        os.remove(INI_PATH)

def find_agent_by_model(model_id: int):
    for ag in AgentArray.GetAgentArray():
        if Agent.GetModelID(ag) == model_id:
            return ag
    return None

# —— Leader target sync ——
def set_leader_target(model_id: int):
    cfg = _load_config()
    cfg[SECTION]["model_id"]   = str(model_id)
    cfg[SECTION]["choice"]     = ""
    cfg[SECTION]["timestamp"]  = str(time.time())
    _save_config(cfg)
    ConsoleLog("NPCSync", f"Leader set model_id={model_id}", Console.MessageType.Info)

def get_leader_data():
    sec = _load_config()[SECTION]
    mid        = int(sec.get("model_id", "0"))
    choice_str = sec.get("choice", "")
    ts         = float(sec.get("timestamp", "0"))
    try:
        choice = int(choice_str) if choice_str else None
    except ValueError:
        choice = None
    return mid, choice, ts

def set_leader_choice(choice: int):
    cfg = _load_config()
    cfg[SECTION]["choice"]    = str(choice)
    cfg[SECTION]["timestamp"] = str(time.time())
    _save_config(cfg)
    ConsoleLog("NPCSync", f"Leader recorded choice={choice}", Console.MessageType.Info)

# —— Leader position sync ——
def set_leader_position(x: float, y: float):
    cfg = _load_config()
    cfg[SECTION]["pos_x"]     = str(x)
    cfg[SECTION]["pos_y"]     = str(y)
    cfg[SECTION]["timestamp"] = str(time.time())
    _save_config(cfg)
    ConsoleLog("NPCSync", f"Leader broadcast position=({x:.1f},{y:.1f})", Console.MessageType.Info)

def get_leader_position():
    sec = _load_config()[SECTION]
    try:
        return (
            float(sec.get("pos_x","")),
            float(sec.get("pos_y","")),
            float(sec.get("timestamp","0"))
        )
    except ValueError:
        return None, None, 0.0

# clear any stale data on load
clear_leader_data()

# —— Helper Functions ——
def reset_sync():
    """Reset all sync state and clear any leader data"""
    global last_model, last_choice, last_choice_time, state, last_leader_pos
    clear_leader_data()
    last_model       = None
    last_choice      = None
    last_choice_time = None
    last_leader_pos  = None
    state            = IDLE
    ConsoleLog("NPCSync", "Sync reset to idle", Console.MessageType.Info)

# —— Lifecycle Hooks ——
def setup():
    clear_leader_data()

def configure():
    setup()

# —— Main Loop ——
def main():
    global last_model, last_choice, last_choice_time, state, last_leader_pos

    # —— 0) Move-to-leader FSM —— 
    lx, ly, lts = get_leader_position()
    if state == IDLE and lx is not None and (last_leader_pos is None or lts > last_leader_pos[2]):
        last_leader_pos = (lx, ly, lts)
        Player.Move(lx, ly)
        ConsoleLog("NPCSync", f"Moving to leader at ({lx:.1f},{ly:.1f})", Console.MessageType.Info)
        state = MOVING_LEADER

    elif state == MOVING_LEADER and last_leader_pos is not None:
        cx, cy = Player.GetXY()
        tx, ty, _ = last_leader_pos
        if math.dist((cx, cy), (tx, ty)) < 50.0:
            ConsoleLog("NPCSync", "Arrived at leader’s spot", Console.MessageType.Info)
            # clear only position flag & return to idle
            clear_leader_data()
            last_leader_pos = None
            state = IDLE

    # —— 1) Existing NPC-sync FSM —— 
    model_id, choice, ts = get_leader_data()
    if not model_id and state != IDLE:
        reset_sync()

    if state == IDLE:
        if model_id and model_id != last_model:
            ag = find_agent_by_model(model_id)
            if ag:
                Player.ChangeTarget(ag)
                last_model = model_id
                state = MOVING_NPC

    elif state == MOVING_NPC:
        ag = find_agent_by_model(model_id)
        if ag and not is_npc_dialog_visible():
            move_interact_blessing_npc(ag, 100.0)
        else:
            state = IN_DIALOG

    elif state == IN_DIALOG:
        if choice and choice != last_choice:
            click_dialog_button(choice)
            last_choice      = choice
            last_choice_time = time.time()
            state            = CHOICE_DONE

    elif state == CHOICE_DONE:
        if is_npc_dialog_visible():
            cfg = _load_config()
            cfg[SECTION]["choice"] = ""
            _save_config(cfg)
            last_choice = None
            state       = IN_DIALOG
        elif last_choice_time and (time.time() - last_choice_time) > DIALOG_RESET_TIMEOUT:
            reset_sync()

    # —— UI Rendering —— 
    PyImGui.begin("Dialog Sync", PyImGui.WindowFlags.AlwaysAutoResize)

    # Runner icon: broadcast position
    if PyImGui.button(IconsFontAwesome5.ICON_RUNNING):
        x, y = Player.GetXY()
        set_leader_position(x, y)
    if PyImGui.is_item_hovered():
        PyImGui.set_tooltip("Broadcast my position - Clients moves to me")

    # Phone icon: set NPC target
    PyImGui.same_line(0.0, -1.0)
    if PyImGui.button(IconsFontAwesome5.ICON_PHONE):
        tid = Player.GetTargetID()
        if tid:
            mid = Agent.GetModelID(tid)
            set_leader_target(mid)
        else:
            ConsoleLog("NPCSync", "No target selected.", Console.MessageType.Warning)
    if PyImGui.is_item_hovered():
        PyImGui.set_tooltip("Target a NPC & Send all client to interact")

    # Sync icon: reset everything
    PyImGui.same_line(0.0, -1.0)
    if PyImGui.button(IconsFontAwesome5.ICON_SYNC):
        reset_sync()
    if PyImGui.is_item_hovered():
        PyImGui.set_tooltip("Reset all broadcasts")

    if is_npc_dialog_visible():
        count = get_dialog_button_count()
        for i in range(1, count + 1):
            if PyImGui.button(f"All Click Button {i}"):
                set_leader_choice(i)

    PyImGui.end()

__all__ = ["main", "configure"]
