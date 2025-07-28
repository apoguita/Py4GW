import ctypes
import ctypes.wintypes
import os
import traceback
import threading
import atexit
import sys
import json

import Py4GW  # type: ignore
from HeroAI.cache_data import CacheData
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Effects
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Timer
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import Item
from Py4GWCoreLib import ItemArray
from Py4GWCoreLib import ModelID
from Py4GWCoreLib import Bags

# Your existing setup
script_directory = os.getcwd()
project_root = os.path.abspath(os.path.join(script_directory, os.pardir))

first_run = True
BASE_DIR = os.path.join(project_root, "Widgets/Config")
INI_WIDGET_WINDOW_PATH = os.path.join(BASE_DIR, "AlcoholProc.ini")
ALCOHOL_PROCS_JSON_PATH = os.path.join(BASE_DIR, "alcohol_procs.json")
os.makedirs(BASE_DIR, exist_ok=True)

cached_data = CacheData()

ini_window = IniHandler(INI_WIDGET_WINDOW_PATH)
save_window_timer = Timer()
save_window_timer.Start()

MODULE_NAME = "AlcoholProc"
COLLAPSED = "collapsed"
X_POS = "x"
Y_POS = "y"
VK = 'VK'
CALLBACK = 'callback'

window_x = ini_window.read_int(MODULE_NAME, X_POS, 100)
window_y = ini_window.read_int(MODULE_NAME, Y_POS, 100)
window_collapsed = ini_window.read_bool(MODULE_NAME, COLLAPSED, False)

# Windows constants
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# LowLevelKeyboardProc function prototype
LowLevelKeyboardProc = ctypes.WINFUNCTYPE(
    ctypes.c_int,
    ctypes.c_int,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM,
)

ALCOHOL_SKILLS_TO_DETECT = [
    "Drunken_Master",
    "Dwarven_Stability",
    "Feel_No_Pain",
]

ALCOHOL_MODEL_IDS = [
    ModelID.Bottle_Of_Rice_Wine,
    ModelID.Bottle_Of_Vabbian_Wine,
    ModelID.Dwarven_Ale,
    ModelID.Eggnog,
    ModelID.Hard_Apple_Cider,
    ModelID.Hunters_Ale,
    ModelID.Shamrock_Ale,
    ModelID.Vial_Of_Absinthe,
    ModelID.Witchs_Brew,
]


if sys.maxsize > 2**32:
    ULONG_PTR = ctypes.c_uint64
else:
    ULONG_PTR = ctypes.c_ulong


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", ctypes.wintypes.DWORD),
        ("scanCode", ctypes.wintypes.DWORD),
        ("flags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


hook_handle = None
hook_thread = None
hook_proc = None
should_suppress_key = False  # Controlled by your widget toggle
suppressed_key_callbacks = {}


def use_alcohol():
    for bag in range(Bags.Backpack, Bags.Bag2 + 1):
        items = ItemArray.GetItemArray(ItemArray.CreateBagList(bag))
        for item in items:
            if Item.GetModelID(item) in [model.value for model in ALCOHOL_MODEL_IDS]:
                GLOBAL_CACHE.Inventory.UseItem(item)
                return True
    return False


def load_alcohol_keybinds_from_json():
    with open(ALCOHOL_PROCS_JSON_PATH, "r") as f:
        data = json.load(f)

    suppressed_key_callbacks.clear()

    for skill_name in ALCOHOL_SKILLS_TO_DETECT:
        skill_id = GLOBAL_CACHE.Skill.GetID(skill_name)
        slot_number = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id)

        slot_number = str(slot_number)
        if slot_number in data:
            vk = char_to_vk(data[slot_number])
            if vk is not None:

                def cast_after_consuming_alcohol(sid):
                    if not Effects.GetAlcoholLevel() and should_suppress_key:
                        use_alcohol()
                    Routines.Yield.Skills.CastSkillID(sid, aftercast_delay=100)

                suppressed_key_callbacks[int(vk)] = lambda sid=skill_id: cast_after_consuming_alcohol(sid)

    return data


def is_my_instance_focused():
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return False

    pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value == os.getpid()


def vk_to_char(vk_code):
    return chr(user32.MapVirtualKeyW(vk_code, 2))


def char_to_vk(char: str) -> int:
    if len(char) != 1:
        pass
    vk = user32.VkKeyScanW(ord(char))
    if vk == -1:
        pass
    return vk & 0xFF  # The low byte is the VK code


@LowLevelKeyboardProc
def keyboard_hook(nCode, wParam, lParam):
    if nCode == 0 and wParam == WM_KEYDOWN:
        kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
        if kb.vkCode in suppressed_key_callbacks and should_suppress_key and is_my_instance_focused():
            Py4GW.Console.Log(
                MODULE_NAME, f"Suppressed {vk_to_char(kb.vkCode).upper()} key press", Py4GW.Console.MessageType.Debug
            )

            # Trigger callback if registered
            callback = suppressed_key_callbacks.get(kb.vkCode)
            if callback:
                callback()

            return 1  # Block key
    return user32.CallNextHookEx(hook_handle, nCode, wParam, lParam)


def install_hook():
    global hook_handle, hook_proc
    hook_proc = keyboard_hook
    hook_handle = user32.SetWindowsHookExW(
        WH_KEYBOARD_LL,
        hook_proc,
        kernel32.GetModuleHandleW(None),
        0,
    )
    if not hook_handle:
        raise ctypes.WinError(ctypes.get_last_error())


def uninstall_hook():
    global hook_handle
    if hook_handle:
        user32.UnhookWindowsHookEx(hook_handle)
        hook_handle = None


atexit.register(uninstall_hook)


def hook_message_loop():
    msg = ctypes.wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))


def start_hook_thread():
    global hook_thread
    install_hook()
    hook_thread = threading.Thread(target=hook_message_loop, daemon=True)
    hook_thread.start()


# Start hook thread on module import or at first use
start_hook_thread()


def draw_widget():
    global window_x, window_y, window_collapsed, first_run, should_suppress_key

    if first_run:
        PyImGui.set_next_window_pos(window_x, window_y)
        PyImGui.set_next_window_collapsed(window_collapsed, 0)
        first_run = False

    is_window_opened = PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize)
    new_collapsed = PyImGui.is_window_collapsed()
    end_pos = PyImGui.get_window_pos()

    if is_window_opened:
        # Toggle suppression via your UI
        should_suppress_key = ImGui.toggle_button('Start Alcohol Support##StartAlcoholSupport', should_suppress_key)

        keybinds = load_alcohol_keybinds_from_json()
        if keybinds and PyImGui.begin_table(
            "Alcohol Proccer", 2, PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg
        ):
            for skill_name in ALCOHOL_SKILLS_TO_DETECT:

                skill_id = GLOBAL_CACHE.Skill.GetID(skill_name)
                slot_number = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id)

                if skill_id and slot_number:
                    # Skill icon column
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()
                    prefix = ""
                    if "Widgets" in str(script_directory):
                        prefix = "..\\"

                    texture_file = prefix + GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(skill_id)
                    ImGui.DrawTexture(texture_file, 44, 44)

                    # Keybind column
                    PyImGui.table_next_column()
                    keybind_value = (
                        keybinds.get(str(slot_number)).upper() if keybinds.get(str(slot_number)) else "[Unbound]"
                    )
                    PyImGui.text(keybind_value)

            PyImGui.end_table()
        else:
            PyImGui.text("No keybinds loaded.")
    PyImGui.end()

    # Save window state every second
    if save_window_timer.HasElapsed(1000):
        if (end_pos[0], end_pos[1]) != (window_x, window_y):
            window_x, window_y = int(end_pos[0]), int(end_pos[1])
            ini_window.write_key(MODULE_NAME, X_POS, str(window_x))
            ini_window.write_key(MODULE_NAME, Y_POS, str(window_y))

        if new_collapsed != window_collapsed:
            window_collapsed = new_collapsed
            ini_window.write_key(MODULE_NAME, COLLAPSED, str(window_collapsed))

        save_window_timer.Reset()


def configure():
    pass


def main():
    global cached_data
    try:
        if not Routines.Checks.Map.MapValid():
            return

        cached_data.Update()
        if cached_data.data.is_map_ready and cached_data.data.is_party_loaded:
            draw_widget()

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
        Py4GW.Console.Log(MODULE_NAME, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass


if __name__ == "__main__":
    main()
