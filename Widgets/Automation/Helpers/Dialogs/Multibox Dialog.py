import ctypes
import os
import traceback
from enum import IntEnum

import Py4GW  # type: ignore
from HeroAI.cache_data import CacheData
from Py4GWCoreLib import GLOBAL_CACHE, PyUIManager, UIManager, IconsFontAwesome5
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import PyImGui, Color, ImGui
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Timer, Player
from Py4GWCoreLib.Overlay import Overlay
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType

script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = Py4GW.Console.get_projects_path()

first_run = True

BASE_DIR = os.path.join(project_root, "Widgets/Config")
INI_WIDGET_WINDOW_PATH = os.path.join(BASE_DIR, "nightfall_dialog_sender.ini")
os.makedirs(BASE_DIR, exist_ok=True)

cached_data = CacheData()

# ——— Window Persistence Setup ———
ini_window = IniHandler(INI_WIDGET_WINDOW_PATH)
save_window_timer = Timer()
save_window_timer.Start()

# String consts
MODULE_NAME = "Dialog Sender (Multibox)"  # Change this Module name
MODULE_ICON = "Textures\\Module_Icons\\Dialogs - Nightfall.png"
COLLAPSED = "collapsed"
X_POS = "x"
Y_POS = "y"

# load last‐saved window state (fallback to 100,100 / un-collapsed)
window_x = ini_window.read_int(MODULE_NAME, X_POS, 100)
window_y = ini_window.read_int(MODULE_NAME, Y_POS, 100)
window_collapsed = ini_window.read_bool(MODULE_NAME, COLLAPSED, False)

default_dialog_string: str = "0x84"

dialog_open : bool = False
frame_coords : list[tuple[int, tuple[int, int, int, int]]] = []
dialog_coords : tuple[int, int, int, int] = (0, 0, 0, 0)
overlay = Overlay()

# Load user32.dll
user32 = ctypes.windll.user32

# Virtual-key code for left mouse button
VK_LBUTTON = 0x01

def is_left_pressed() -> bool:
    return bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)

_left_was_pressed = False

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


class WhichKey(IntEnum):
    CTRL = 1
    SHIFT = 2


which_key: int = 2
to_hex : str = "?"
dialog_int : int = 0
gray_color = Color(150, 150, 150, 255)


def draw_dialog_overlay():
    global frame_coords, dialog_open, dialog_coords, gray_color, \
        to_hex, dialog_int, \
        which_key

    account_email = Player.GetAccountEmail()
    own_data = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(account_email)
    if own_data is None:
        # print("no cache data")
        return

    dialog_open = UIManager.IsNPCDialogVisible()
    frame_coords = UIManager.GetDialogButtonFrames() if dialog_open else []

    if not frame_coords or not dialog_open:
        # print("no dialog data")
        return

    pyimgui_io = PyImGui.get_io()
    mouse_pos = (pyimgui_io.mouse_pos_x, pyimgui_io.mouse_pos_y)

    sorted_frames = sorted(frame_coords, key=lambda x: (x[1][1], x[1][0]))  # Sort by Y, then X

    # print("dialog open")
    for i, (frame_id, frame) in enumerate(sorted_frames):
        if ImGui.is_mouse_in_rect((frame[0], frame[1], frame[2] - frame[0], frame[3] - frame[1]), mouse_pos):

            frame_obj = PyUIManager.UIFrame(frame_id)
            if frame_obj is not None:
                dialog_int = frame_obj.field105_0x1c4
                to_hex = f"0x{dialog_int:X}"

                set_dialog_id(to_hex)


            ctrl, str_ctrl = get_modifier_state(pyimgui_io, which_key)

            if is_left_mouse_clicked():
                if ctrl:

                    # hero ai does this...
                    # accounts = [acc for acc in GLOBAL_CACHE.ShMem.GetAllAccountData() if acc.AccountEmail != account_email]
                    # print(f"sending dialog {i + 1}")
                    # commands.send_dialog(accounts, i + 1)

                    # this is the field in toolbox:
                    # PyUIManager.UIFrame(frame_id).field105_0x1c4
                    send_dialog_for_all(to_hex, dialog_int, include_sender = False)

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

        else:
            # print("no dialog")
            pass

    pass


# todo expose setting to not clash with hero ai and gw1 call target ideal of using ctrl or remove feature from hero ai to be more modular
def get_modifier_state(pyimgui_io, which_key):
    ctrl = False
    str_ctrl = "shift"
    if WhichKey.CTRL.value == which_key:
        ctrl = pyimgui_io.key_ctrl
        str_ctrl = "ctrl"
    else:
        ctrl = pyimgui_io.key_shift
    return ctrl, str_ctrl


# Allow the user to override the dialog id manually if they so choose as well as display current dialog id and button to send
def draw_widget():
    global window_x, window_y, window_collapsed, first_run
    global default_dialog_string

    if not PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.end()
        return

    default_dialog_string = ImGui.input_text("Dialog Id", default_dialog_string, 0)

    if PyImGui.button(f"{IconsFontAwesome5.ICON_CROSSHAIRS} Send Dialog"):
        send_dialog()

    PyImGui.end()


# Module tooltip, not the dialog tooltip
def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(MODULE_NAME, title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("An automation utility for sending dialogs when multiboxing based on the open dialogs.")
    PyImGui.spacing()

    PyImGui.end_tooltip()


# @staticmethod
def set_dialog_id(dialog_string: str):
    global default_dialog_string
    default_dialog_string = dialog_string


def send_dialog():
    global default_dialog_string
    try:
        dialog_id: int = int(default_dialog_string, 0)
        send_dialog_for_all(default_dialog_string, dialog_id)
    except Exception as e:
        print(f"Well sending {default_dialog_string} failed {e}")
        default_dialog_string = "0x84"


# @staticmethod
def send_dialog_for_all(dialog_string: str, dialog_id: int, include_sender: bool = True):
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

            # TODO distance check first to avoid the wobble of death

            print(f"Ordering {account.AccountEmail} to send dialog {dialog_id} ({dialog_string}) to target: {target}")
            GLOBAL_CACHE.ShMem.SendMessage(
                sender_email, account.AccountEmail, SharedCommandType.SendDialogToTarget,
                (target, dialog_id, 0, 0)
            )


def main():
    global cached_data
    try:
        if not Routines.Checks.Map.MapValid():
            return

        draw_widget()

        draw_dialog_overlay()

    except ImportError as e:
        Py4GW.Console.Log(MODULE_NAME, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(MODULE_NAME, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(MODULE_NAME, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(MODULE_NAME, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass


if __name__ == "__main__":
    main()
