import atexit
import ctypes
import ctypes.wintypes
import json
import os
import sys
import threading
import traceback

import Py4GW  # type: ignore
from HeroAI.cache_data import CacheData
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Bags
from Py4GWCoreLib import Effects
from Py4GWCoreLib import IconsFontAwesome5
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import Item
from Py4GWCoreLib import ItemArray
from Py4GWCoreLib import ModelID
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Timer


def find_project_root(current_path: str, anchor_dir: str = "Py4GW") -> str:
    """
    Walks up the directory tree from `current_path` until it finds `anchor_dir`.
    """
    while current_path and os.path.basename(current_path) != anchor_dir:
        new_path = os.path.dirname(current_path)
        if new_path == current_path:  # Reached filesystem root
            raise RuntimeError(f"Could not find project root '{anchor_dir}' from '{current_path}'")
        current_path = new_path
    return current_path


try:
    script_path = os.path.abspath(__file__)
except NameError:
    script_path = os.path.abspath(os.getcwd())  # Fallback for interactive mode

project_root = find_project_root(script_path, anchor_dir="Py4GW")
first_run = True

BASE_DIR = os.path.join(project_root, "Bots/marks_coding_corner")
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
    ModelID.Eggnog,
    ModelID.Dwarven_Ale,
    ModelID.Hard_Apple_Cider,
    ModelID.Hunters_Ale,
    ModelID.Bottle_Of_Juniberry_Gin,
    ModelID.Shamrock_Ale,
    ModelID.Bottle_Of_Vabbian_Wine,
    ModelID.Vial_Of_Absinthe,
    ModelID.Witchs_Brew,
    ModelID.Zehtukas_Jug,
    ModelID.Aged_Dwarven_Ale,
    ModelID.Aged_Hunters_Ale,
    ModelID.Bottle_Of_Grog,
    ModelID.Flask_Of_Firewater,
    ModelID.Keg_Of_Aged_Hunters_Ale,
    ModelID.Krytan_Brandy,
    ModelID.Spiked_Eggnog,
    ModelID.Battle_Isle_Iced_Tea,
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
should_suppress_key = True  # Controlled by your widget toggle
suppressed_key_callbacks = {}


def ensure_alcohol_json_exists():
    def is_valid_data(data):
        if not isinstance(data, dict):
            return False
        return True

    default_json = {"1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", "8": "8"}

    should_overwrite = False

    if os.path.exists(ALCOHOL_PROCS_JSON_PATH):
        try:
            with open(ALCOHOL_PROCS_JSON_PATH, "r") as f:
                data = json.load(f)
            if not is_valid_data(data):
                print("[AlcoholProc] Invalid format detected, overwriting.")
                should_overwrite = True
        except (json.JSONDecodeError, IOError):
            print("[AlcoholProc] JSON error detected, overwriting.")
            should_overwrite = True
    else:
        should_overwrite = True

    if should_overwrite:
        with open(ALCOHOL_PROCS_JSON_PATH, "w") as f:
            json.dump(default_json, f, indent=4)
            print(f"[AlcoholProc] Formation JSON reset at {ALCOHOL_PROCS_JSON_PATH}")


def use_alcohol():
    for bag in range(Bags.Backpack, Bags.Bag2 + 1):
        items = ItemArray.GetItemArray(ItemArray.CreateBagList(bag))
        for item in items:
            if Item.GetModelID(item) in {model.value for model in ALCOHOL_MODEL_IDS}:
                GLOBAL_CACHE.Inventory.UseItem(item)
                return True
    return False


def load_alcohol_keybinds_from_json():
    ensure_alcohol_json_exists()
    with open(ALCOHOL_PROCS_JSON_PATH, "r") as f:
        data = json.load(f)

    suppressed_key_callbacks.clear()

    for skill_name in ALCOHOL_SKILLS_TO_DETECT:
        skill_id = GLOBAL_CACHE.Skill.GetID(skill_name)
        slot_number = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id)

        str_slot_number = str(slot_number)
        if str_slot_number in data:
            vk = char_to_vk(data[str_slot_number])
            if vk is not None:

                def cast_after_consuming_alcohol(sid):
                    if (
                        not Effects.GetAlcoholLevel()
                        and cached_data.combat_handler.IsReadyToCast(slot_number)
                        and should_suppress_key
                    ):
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
        if (
            is_my_instance_focused()
            and not GLOBAL_CACHE.Player.IsTyping()
            and kb.vkCode in suppressed_key_callbacks
            and should_suppress_key
        ):
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
    global window_x
    global window_y
    global window_collapsed
    global first_run
    global should_suppress_key
    global in_file

    if first_run:
        PyImGui.set_next_window_pos(window_x, window_y)
        PyImGui.set_next_window_collapsed(window_collapsed, 0)
        first_run = False

    is_window_opened = PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize)
    new_collapsed = PyImGui.is_window_collapsed()
    end_pos = PyImGui.get_window_pos()

    if is_window_opened:
        # Toggle suppression via your UI
        should_suppress_key = ImGui.toggle_button(
            f'Alcohol Support is {"ON" if should_suppress_key else "OFF"}##StartAlcoholSupport', should_suppress_key
        )

        keybinds = load_alcohol_keybinds_from_json()
        if keybinds and PyImGui.begin_table("Alcohol Injector", 2):
            PyImGui.table_setup_column("Icon", PyImGui.TableColumnFlags.WidthFixed, 50)
            PyImGui.table_setup_column("Keybind", PyImGui.TableColumnFlags.WidthStretch)
            for skill_name in ALCOHOL_SKILLS_TO_DETECT:

                skill_id = GLOBAL_CACHE.Skill.GetID(skill_name)
                slot_number = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(skill_id)

                if skill_id and slot_number:
                    # Skill icon column
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()

                    texture_file = os.path.join(project_root, GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(skill_id))
                    ImGui.DrawTexture(texture_file, 44, 44)

                    # Keybind column
                    PyImGui.table_next_column()
                    keybind_value = (
                        keybinds.get(str(slot_number)).upper() if keybinds.get(str(slot_number)) else "[Unbound]"
                    )
                    PyImGui.text(f"Keybind:\n\n[{keybind_value}]")

            PyImGui.end_table()
        else:
            PyImGui.text("No keybinds loaded.")

        if PyImGui.begin_table("Help Text", 1):
            PyImGui.table_setup_column("Text", PyImGui.TableColumnFlags.WidthFixed, 120)
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            PyImGui.text_wrapped(IconsFontAwesome5.ICON_HANDS_HELPING + " Keybinds Help")
            ImGui.show_tooltip(
                f"Update your current skill keybinds in '{BASE_DIR}\\alcohol_procs.json' - by default it uses 1-8 keys"
            )
            PyImGui.end_table()
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
        if Routines.Checks.Map.IsMapReady() and Routines.Checks.Party.IsPartyLoaded():
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
    # Sample JSON to add to your alcohol_procs.json
    # {
    #     "1": "q",
    #     "2": "w",
    #     "3": "e",
    #     "4": "r",
    #     "5": "a",
    #     "6": "s",
    #     "7": "d",
    #     "8": "f"
    # }
    main()
