# ──────────────────────────────────────────────────────────────────────────────
# File: Dialog Sync.py   (no move_interact_blessing_npc fallback)
# ──────────────────────────────────────────────────────────────────────────────

import os
import tempfile
import time
import math
from types import SimpleNamespace

from Py4GW_widget_manager import get_widget_handler
from Py4GWCoreLib import *
from Py4GWCoreLib import (
    GLOBAL_CACHE,
    PyImGui,
    IconsFontAwesome5,
    ConsoleLog,
    Console,
    Routines,
    UIManager,
    SharedCommandType,
    Timer,
    ThrottledTimer,
    IniHandler,
Player
)

from Sources.aC_Scripts.aC_api import (
    is_npc_dialog_visible,
    click_dialog_button,
    get_dialog_button_count,
)

# ──────────────────────────────────────────────────────────────────────────────
# Constants & Paths
# ──────────────────────────────────────────────────────────────────────────────
FLAG_DIR = os.path.join(tempfile.gettempdir(), "GuildWarsNPCSync")
os.makedirs(FLAG_DIR, exist_ok=True)
SECTION = "NPC_SYNC"

WINDOW_INI_PATH   = os.path.join(FLAG_DIR, "npc_sync_window.ini")
ini_window        = IniHandler(WINDOW_INI_PATH)

# ──────────────────────────────────────────────────────────────────────────────
# Throttles & Timers
# ──────────────────────────────────────────────────────────────────────────────
_npc_sync_timer    = ThrottledTimer(1000)   # run FSM at most once per second
save_window_timer  = Timer()
save_window_timer.Start()

# ──────────────────────────────────────────────────────────────────────────────
# Window State (persisted)
# ──────────────────────────────────────────────────────────────────────────────
win_x            = ini_window.read_int(SECTION, "window_x", 100)
win_y            = ini_window.read_int(SECTION, "window_y", 100)
win_collapsed    = ini_window.read_bool(SECTION, "window_collapsed", False)
first_run_window = True

# ──────────────────────────────────────────────────────────────────────────────
# FSM Constants (only used for “Come Here” and “Choice” on followers)
# ──────────────────────────────────────────────────────────────────────────────
IDLE, MOVING_LEADER, IN_DIALOG, CHOICE_DONE = range(4)
DIALOG_RESET_TIMEOUT = 2.0

# ──────────────────────────────────────────────────────────────────────────────
# Shared‐memory “Leader State” (on each follower)
# ──────────────────────────────────────────────────────────────────────────────
leader_target_agent = 0        # NPC agent ID last broadcast by leader
leader_choice       = -1       # Dialog‐button index last broadcast
leader_position     = None     # (x, y, timestamp) last “Come Here” broadcast
leader_position_ts  = 0.0      # timestamp component of leader_position

# ──────────────────────────────────────────────────────────────────────────────
# Per‐follower runtime variables
# ──────────────────────────────────────────────────────────────────────────────
last_choice_time    = None
state               = IDLE
last_leader_pos     = None    # (x, y, timestamp) follower is moving toward
last_processed_lts  = 0.0     # last processed timestamp for position


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def get_email_for_agent(agent_id: int) -> str | None:
    """
    SharedMemory does not expose GetAccountDataFromAgentID, so we iterate
    over GetAllActivePlayers and match PlayerID → agent_id.
    """
    for account in GLOBAL_CACHE.ShMem.GetAllActivePlayers():
        if int(account.PlayerID) == agent_id:
            return account.AccountEmail
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Leader‐side “broadcast” functions
# ──────────────────────────────────────────────────────────────────────────────

def broadcast_target_to_party(agent_id: int):
    """
    Leader calls this to notify all followers: “NPC agent_id is our next target.”
    We put agent_id into Params[0] so that InteractWithTarget can pick it up.
    """
    leader_email = Player.GetAccountEmail()
    if not leader_email:
        return

    for slot in GLOBAL_CACHE.Party.GetPlayers():
        a_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(slot.login_number)
        member_email = get_email_for_agent(a_id)
        if not member_email or member_email == leader_email:
            continue

        GLOBAL_CACHE.ShMem.SendMessage(
            sender_email   = leader_email,
            receiver_email = member_email,
            command        = SharedCommandType.DialogSyncSetTarget,
            params         = (float(agent_id), 0.0, 0.0, 0.0),
        )

    ConsoleLog(
        "DialogSync",
        f"Leader broadcast target agent_id={agent_id}",
        Console.MessageType.Info
    )


def broadcast_choice_to_party(choice_idx: int):
    """
    Leader calls this to notify all followers: “Click dialog button = choice_idx.”
    """
    leader_email = Player.GetAccountEmail()
    if not leader_email:
        return

    for slot in GLOBAL_CACHE.Party.GetPlayers():
        a_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(slot.login_number)
        member_email = get_email_for_agent(a_id)
        if not member_email or member_email == leader_email:
            continue

        GLOBAL_CACHE.ShMem.SendMessage(
            sender_email   = leader_email,
            receiver_email = member_email,
            command        = SharedCommandType.DialogSyncSetChoice,
            params         = (float(choice_idx), 0.0, 0.0, 0.0),
        )

    ConsoleLog(
        "DialogSync",
        f"Leader broadcast choice={choice_idx}",
        Console.MessageType.Info
    )


def broadcast_position_to_party(x: float, y: float):
    """
    Leader calls this to notify all followers: “Move to (x, y).”
    We do not broadcast (0, 0); that is treated as a no‐op.
    """
    if x == 0.0 and y == 0.0:
        return

    leader_email = Player.GetAccountEmail()
    if not leader_email:
        return

    for slot in GLOBAL_CACHE.Party.GetPlayers():
        a_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(slot.login_number)
        member_email = get_email_for_agent(a_id)
        if not member_email or member_email == leader_email:
            continue

        GLOBAL_CACHE.ShMem.SendMessage(
            sender_email   = leader_email,
            receiver_email = member_email,
            command        = SharedCommandType.DialogSyncSetPosition,
            params         = (float(x), float(y), 0.0, 0.0),
        )

    ConsoleLog(
        "DialogSync",
        f"Leader broadcast position=({x:.1f},{y:.1f})",
        Console.MessageType.Info
    )


# ──────────────────────────────────────────────────────────────────────────────
# Reset & Initialize
# ──────────────────────────────────────────────────────────────────────────────

def reset_sync():
    """
    Clear all local “leader_*” state on the follower and return the FSM to IDLE.
    Broadcast only “clear target” to followers. No zero‐choice or zero‐position.
    """
    global leader_target_agent, leader_choice, leader_position, leader_position_ts
    global last_choice_time, state, last_leader_pos, last_processed_lts

    leader_target_agent = 0
    leader_choice       = -1
    leader_position     = None
    leader_position_ts  = 0.0

    last_choice_time    = None
    state               = IDLE
    last_leader_pos     = None
    last_processed_lts  = 0.0

    ConsoleLog("NPCSync", "Sync reset to idle", Console.MessageType.Info)


def setup():
    """
    Called once at startup on each client.
    """
    reset_sync()

# ──────────────────────────────────────────────────────────────────────────────
# Main Logic Loop (called once per frame/tick)
# ──────────────────────────────────────────────────────────────────────────────

def run_logic_if_needed():
    global last_choice_time, state, last_leader_pos, last_processed_lts
    global leader_target_agent, leader_choice, leader_position

    me        = Player.GetAgentID()
    is_leader = (GLOBAL_CACHE.Party.GetPartyLeaderID() == me)

    # ── 1) If I am the leader, skip the follower FSM entirely ──
    if is_leader:
        return

    # ── 2) Followers only: throttle to once per second ──
    if not _npc_sync_timer.IsExpired():
        return

    # ── 3) Validate map for followers ──
    if not Routines.Checks.Map.MapValid():
        return

    # ── 4) Followers: React to “leader_position” (Come Here) ──
    if leader_position is not None:
        lx, ly, lts = leader_position
        if not (lx == 0.0 and ly == 0.0):
            if state == IDLE and lts > last_processed_lts:
                last_leader_pos   = (lx, ly, lts)
                Player.Move(lx, ly)
                time.sleep(0.125)   # let the movement begin
                ConsoleLog("NPCSync", f"Follower moving to leader at ({lx:.1f},{ly:.1f})", Console.MessageType.Info)
                state = MOVING_LEADER
                last_processed_lts = lts

            elif state == MOVING_LEADER and last_leader_pos is not None:
                cx, cy    = Player.GetXY()
                tx, ty, _ = last_leader_pos
                if math.dist((cx, cy), (tx, ty)) < 50.0:
                    ConsoleLog("NPCSync", "Arrived at leader’s spot", Console.MessageType.Info)
                    last_leader_pos = None
                    state           = IDLE

    # ── 5) Followers: Cancel/Reset if leader cleared target and position ──
    if state != IDLE and leader_target_agent == 0 and (leader_position is None or (leader_position[0] == 0.0 and leader_position[1] == 0.0)):
        reset_sync()
        return

    # ── 6) Followers: In‐dialog “wait for leader’s choice” ──
    if state == IN_DIALOG:
        if leader_choice and leader_choice != last_choice:
            click_dialog_button(leader_choice)
            last_choice      = leader_choice
            last_choice_time = time.time()
            state            = CHOICE_DONE

    # ── 7) Followers: After pressing choice, wait for dialog to close ──
    elif state == CHOICE_DONE:
        if is_npc_dialog_visible():
            leader_choice = -1
            last_choice   = None
            state         = IN_DIALOG
        elif last_choice_time and (time.time() - last_choice_time) > DIALOG_RESET_TIMEOUT:
            reset_sync()


# ──────────────────────────────────────────────────────────────────────────────
# UI Rendering (ImGui) – only draw when you are the leader
# ──────────────────────────────────────────────────────────────────────────────

def render_ui():
    global win_x, win_y, win_collapsed, first_run_window
    global leader_target_agent, leader_choice, leader_position

    me        = Player.GetAgentID()
    is_leader = (GLOBAL_CACHE.Party.GetPartyLeaderID() == me)
    if not is_leader:
        return

    # On first run, set window position/collapsed from INI
    if first_run_window:
        PyImGui.set_next_window_pos(win_x, win_y)
        PyImGui.set_next_window_collapsed(win_collapsed, 0)
        first_run_window = False

    PyImGui.begin("Dialog Sync", PyImGui.WindowFlags.AlwaysAutoResize)
    new_collapsed = PyImGui.is_window_collapsed()
    end_pos      = PyImGui.get_window_pos()

    # ── Leader UI: “Come Here” (Running Man) ──
    if PyImGui.button(IconsFontAwesome5.ICON_RUNNING):
        if Routines.Checks.Map.MapValid():
            x, y = Player.GetXY()
            if not (x == 0.0 and y == 0.0):
                leader_position    = (x, y, time.time())
                leader_position_ts = leader_position[2]
                broadcast_position_to_party(x, y)
            else:
                ConsoleLog("NPCSync", "Cannot broadcast position (0,0).", Console.MessageType.Warning)

    PyImGui.same_line(0.0, -1.0)

    # ── Leader UI: “Go Interact” (Phone) ──
    if PyImGui.button(IconsFontAwesome5.ICON_PHONE):
        tid = Player.GetTargetID()
        if tid:
            # 1) Update module‐level variable
            leader_target_agent = tid

            # 2) Broadcast to followers
            broadcast_target_to_party(tid)

            # 3) Also have leader walk+interact via InteractWithTarget coroutine
            fake_msg = SimpleNamespace(
                SenderEmail   = Player.GetAccountEmail(),
                ReceiverEmail = Player.GetAccountEmail(),
                Params        = (str(tid), "0", "0", "0")
            )
            GLOBAL_CACHE.Coroutines.append(InteractWithTarget(-1, fake_msg))

        else:
            ConsoleLog("NPCSync", "No target selected, cannot broadcast NPC.", Console.MessageType.Warning)

    PyImGui.same_line(0.0, -1.0)

    # ── Leader UI: “Reset Sync” (↻) ──
    if PyImGui.button(IconsFontAwesome5.ICON_SYNC):
        reset_sync()
        broadcast_target_to_party(0)   # clear agent‐ID for followers

    # ── Leader UI: “All Click Button i” when in dialog ──
    if is_npc_dialog_visible():
        count = get_dialog_button_count()
        for i in range(1, count + 1):
            if PyImGui.button(f"All Click Button {i}"):
                # Leader clicks locally
                UIManager.ClickDialogButton(i)

                # Record & broadcast to followers
                leader_choice = i
                broadcast_choice_to_party(i)

    PyImGui.end()

    # ── Save window position/collapsed every 15s ──
    if save_window_timer.HasElapsed(15000):
        if (end_pos[0], end_pos[1]) != (win_x, win_y):
            win_x, win_y = int(end_pos[0]), int(end_pos[1])
            ini_window.write_key(SECTION, "window_x", str(win_x))
            ini_window.write_key(SECTION, "window_y", str(win_y))
        if new_collapsed != win_collapsed:
            win_collapsed = new_collapsed
            ini_window.write_key(SECTION, "window_collapsed", str(win_collapsed))
        save_window_timer.Reset()


# ──────────────────────────────────────────────────────────────────────────────
# Entry Points
# ──────────────────────────────────────────────────────────────────────────────

def main():
    # 1) Process incoming messages (e.g. follower: target broadcast → InteractWithTarget)
    ProcessMessages()

    # 2) Run the follower FSM for “Come Here” and “Choice” (leader skips this entirely)
    run_logic_if_needed()

    # 3) Draw leader’s UI (followers see nothing)
    render_ui()


def configure():
    pass


__all__ = ["main", "configure"]
