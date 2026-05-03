MODULE_NAME = "Active Dialog Viewer"
MODULE_ICON = "Textures/Module_Icons/Script Runner.png"

import ctypes
import os
import traceback
from enum import IntEnum

import Py4GW
import PyDialog
import PyImGui
from Py4GWCoreLib import Player
from HeroAI.cache_data import CacheData
from Py4GWCoreLib import GLOBAL_CACHE, PyUIManager, UIManager, IconsFontAwesome5
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import Color, ImGui
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Timer
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType

_dialog_was_active = False

# Multibox Dialog variables
script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = Py4GW.Console.get_projects_path()

BASE_DIR = os.path.join(project_root, "Widgets/Config")
INI_WIDGET_WINDOW_PATH = os.path.join(BASE_DIR, "active_dialog_viewer_multibox.ini")
os.makedirs(BASE_DIR, exist_ok=True)

# Window persistence setup
ini_window = IniHandler(INI_WIDGET_WINDOW_PATH)
save_window_timer = Timer()
save_window_timer.Start()

# Multibox Dialog constants
default_dialog_string: str = "0x84"
dialog_open : bool = False
frame_coords : list[tuple[int, tuple[int, int, int, int]]] = []
dialog_coords : tuple[int, int, int, int] = (0, 0, 0, 0)
overlay = Overlay()

# Load user32.dll
user32 = ctypes.windll.user32
VK_LBUTTON = 0x01

_left_was_pressed = False

class WhichKey(IntEnum):
    CTRL = 1
    SHIFT = 2

which_key: int = 2
to_hex : str = "?"
dialog_int : int = 0
gray_color = Color(150, 150, 150, 255)

# Window state
window_x = ini_window.read_int(MODULE_NAME, "x", 100)
window_y = ini_window.read_int(MODULE_NAME, "y", 100)
window_collapsed = ini_window.read_bool(MODULE_NAME, "collapsed", False)


def configure():
    pass


def tooltip():
    PyImGui.begin_tooltip()
    PyImGui.text(MODULE_NAME)
    PyImGui.separator()
    PyImGui.text_wrapped("Displays the current active Guild Wars dialog, the tracked context dialog, and the currently visible dialog buttons.")
    PyImGui.separator()
    PyImGui.text_wrapped("Multibox: Shift+Click on dialog buttons to send to all accounts.")
    PyImGui.end_tooltip()


def _draw_active_dialog() -> None:
    active = PyDialog.PyDialog.get_active_dialog()

    PyImGui.text(f"Dialog active: {PyDialog.PyDialog.is_dialog_active()}")
    PyImGui.text(f"Last selected dialog id: 0x{PyDialog.PyDialog.get_last_selected_dialog_id():X}")
    PyImGui.separator()

    PyImGui.text("Active dialog")
    PyImGui.text(f"dialog_id: 0x{active.dialog_id:X} ({active.dialog_id})")
    PyImGui.text(f"context_dialog_id: 0x{active.context_dialog_id:X} ({active.context_dialog_id})")
    PyImGui.text(f"agent_id: {active.agent_id}")
    PyImGui.text(f"dialog_id_authoritative: {active.dialog_id_authoritative}")
    PyImGui.separator()
    PyImGui.text("Message")
    if active.message:
        PyImGui.text_wrapped(active.message)
    else:
        PyImGui.text("<empty>")


def _draw_buttons() -> None:
    buttons = PyDialog.PyDialog.get_active_dialog_buttons()
    visible_buttons = [button for button in buttons if getattr(button, "dialog_id", 0) != 0]

    PyImGui.separator()
    PyImGui.text(f"Buttons: {len(visible_buttons)}")

    if not visible_buttons:
        PyImGui.text("<no dialog buttons>")
        return

    for index, button in enumerate(visible_buttons):
        PyImGui.separator()
        PyImGui.text(f"Button #{index}")
        PyImGui.text(f"dialog_id: 0x{button.dialog_id:X} ({button.dialog_id})")
        PyImGui.text(f"button_icon: {button.button_icon}")
        PyImGui.text(f"decode_pending: {button.message_decode_pending}")
        if PyImGui.button(f"{IconsFontAwesome5.ICON_RSS} Send##dialog_button_{index}"):
            Player.SendAutomaticDialog(index)
        PyImGui.same_line(0, -1)
        if PyImGui.button(f"{IconsFontAwesome5.ICON_CROSSHAIRS} Send Dialog to All##dialog_button_{index}"):
            active = PyDialog.PyDialog.get_active_dialog()
            Player.ChangeTarget(active.agent_id)
            _send_dialog_for_all(f"0x{button.dialog_id:X}", button.dialog_id, True)
        label = button.message_decoded or button.message
        if label:
            PyImGui.text_wrapped(label)
        else:
            PyImGui.text("<empty>")


def _draw_multibox_controls() -> None:
    """Draw multibox dialog controls"""
    global default_dialog_string
    
    PyImGui.separator()
    PyImGui.text("Multibox Controls")
    PyImGui.separator()
    
    default_dialog_string = ImGui.input_text("Dialog Id", default_dialog_string, 0)
    
    if PyImGui.button(f"{IconsFontAwesome5.ICON_CROSSHAIRS} Send Dialog to All"):
        _send_dialog()
    
    PyImGui.text_wrapped("Ctrl+Shift+Click on dialog buttons to send to all accounts")


# Multibox helper functions
def is_left_pressed() -> bool:
    return bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)


def is_left_mouse_clicked() -> bool:
    """
    Returns True exactly once per full click (press → release).
    False at all other times.
    """
    global _left_was_pressed

    # Is button physically down now?
    pressed = bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)

    # Detect release event (was pressed, now not pressed)
    clicked = _left_was_pressed and not pressed

    # Update state for next call
    _left_was_pressed = pressed

    return clicked


def _draw_dialog_overlay():
    """Draw overlay for multibox dialog interaction"""
    global frame_coords, dialog_open, dialog_coords, gray_color, to_hex, dialog_int, which_key

    account_email = Player.GetAccountEmail()
    own_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
    if own_data is None:
        return

    dialog_open = UIManager.IsNPCDialogVisible()
    frame_coords = UIManager.GetDialogButtonFrames() if dialog_open else []

    if not frame_coords or not dialog_open:
        return

    pyimgui_io = PyImGui.get_io()
    mouse_pos = (pyimgui_io.mouse_pos_x, pyimgui_io.mouse_pos_y)

    sorted_frames = sorted(frame_coords, key=lambda x: (x[1][1], x[1][0]))  # Sort by Y, then X

    for i, (frame_id, frame) in enumerate(sorted_frames):
        if ImGui.is_mouse_in_rect((frame[0], frame[1], frame[2] - frame[0], frame[3] - frame[1]), mouse_pos):
            frame_obj = PyUIManager.UIFrame(frame_id)
            if frame_obj is not None:
                dialog_int = frame_obj.field105_0x1c4
                to_hex = f"0x{dialog_int:X}"
                _set_dialog_id(to_hex)

            ctrl, str_ctrl = _get_modifier_state(pyimgui_io, which_key)
            if is_left_mouse_clicked():
                if ctrl:

                    # hero ai does this...
                    # accounts = [acc for acc in GLOBAL_CACHE.ShMem.GetAllAccountData() if acc.AccountEmail != account_email]
                    # print(f"sending dialog {i + 1}")
                    # commands.send_dialog(accounts, i + 1)

                    # this is the field in toolbox:
                    # PyUIManager.UIFrame(frame_id).field105_0x1c4
                    _send_dialog_for_all(to_hex, dialog_int, include_sender = False)

                    return
                else:
                    #todo if debug
                    print(f"clicked without {str_ctrl}")
            else:

                if ctrl:
                    # to show that you have the right key sleted
                    ImGui.begin_tooltip()
                    ImGui.text_colored(f"({str_ctrl}) + Click to send dialog {to_hex} ({dialog_int}) on all accounts.", gray_color.color_tuple, 12)
                    ImGui.end_tooltip()
                else:
                    ImGui.begin_tooltip()
                    ImGui.text_colored(f"{str_ctrl} + Click to send dialog {to_hex} ({dialog_int}) on all accounts.", gray_color.color_tuple, 12)
                    ImGui.end_tooltip()


def _get_modifier_state(pyimgui_io, which_key):
    ctrl = False
    str_ctrl = "Shift"
    if WhichKey.CTRL.value == which_key:
        ctrl = pyimgui_io.key_ctrl
        str_ctrl = "Ctrl"
    else:
        ctrl = pyimgui_io.key_shift
    return ctrl, str_ctrl


def _set_dialog_id(dialog_string: str):
    """Set the dialog ID for multibox operations"""
    global default_dialog_string
    default_dialog_string = dialog_string


def _send_dialog():
    """Send dialog to all accounts"""
    global default_dialog_string
    try:
        dialog_id: int = int(default_dialog_string, 0)
        _send_dialog_for_all(default_dialog_string, dialog_id)
    except Exception as e:
        print(f"Sending {default_dialog_string} failed: {e}")
        default_dialog_string = "0x84"


def _send_dialog_for_all(dialog_string: str, dialog_id: int, include_sender: bool = True):
    """Send dialog command to all accounts"""
    print(f"Starting sending {dialog_string} as {dialog_id}")
    target = Player.GetTargetID()
    if target == 0:
        print("No target to interact with.")
    else:
        sender_email = Player.GetAccountEmail()
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        for account in accounts:
            if not include_sender and sender_email == account.AccountEmail:
                continue

            print(f"Ordering {account.AccountEmail} to send dialog {dialog_id} ({dialog_string}) to target: {target}")
            GLOBAL_CACHE.ShMem.SendMessage(
                sender_email, account.AccountEmail, SharedCommandType.SendDialogToTarget,
                (target, dialog_id, 0, 0)
            )


def main():
    global _dialog_was_active
    try:
        dialog_active = PyDialog.PyDialog.is_dialog_active()
        if _dialog_was_active and not dialog_active:
            PyDialog.PyDialog.clear_cache()
        _dialog_was_active = dialog_active

        if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
            if PyImGui.begin_tab_bar("top_level_tabs"):
                if ImGui.begin_tab_item("Default"):
                    _draw_active_dialog()
                    _draw_buttons()
                    ImGui.end_tab_item()
                if ImGui.begin_tab_item("Actions"):
                    _draw_multibox_controls()
                    ImGui.end_tab_item()
            PyImGui.end_tab_bar()
        PyImGui.end()
        
        # Draw multibox overlay
        _draw_dialog_overlay()
        
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {e}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, traceback.format_exc(), Py4GW.Console.MessageType.Error)


if __name__ == "__main__":
    main()
