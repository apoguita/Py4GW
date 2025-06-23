import ctypes
import json
import math
import os
import traceback

import Py4GW
from HeroAI.cache_data import CacheData
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import CombatPrepSkillsType
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import Routines
from Py4GWCoreLib import SharedCommandType
from Py4GWCoreLib import Timer

user32 = ctypes.WinDLL("user32", use_last_error=True)
script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_directory, os.pardir))

first_run = True

BASE_DIR = os.path.join(project_root, "Widgets/Config")
FORMATIONS_JSON_PATH = os.path.join(BASE_DIR, "formation_hotkey.json")
INI_WIDGET_WINDOW_PATH = os.path.join(BASE_DIR, "combat_prep_window.ini")
os.makedirs(BASE_DIR, exist_ok=True)

# String consts
HOTKEY = "hotkey"
MODULE_NAME = "CombatPrep"
COLLAPSED = "collapsed"
COORDINATES = "coordinates"
VK = "vk"
X_POS = "x"
Y_POS = "y"

# Flag constants
IS_FLAGGED = "IsFlagged"
FLAG_POSITION_X = "FlagPosX"
FLAG_POSITION_Y = "FlagPosY"
FOLOW_ANGLE = "FollowAngle"

cached_data = CacheData()

# ——— Window Persistence Setup ———
ini_window = IniHandler(INI_WIDGET_WINDOW_PATH)
save_window_timer = Timer()
save_window_timer.Start()

# load last‐saved window state (fallback to 100,100 / un-collapsed)
window_x = ini_window.read_int(MODULE_NAME, X_POS, 100)
window_y = ini_window.read_int(MODULE_NAME, Y_POS, 100)
window_collapsed = ini_window.read_bool(MODULE_NAME, COLLAPSED, False)


# TODO (mark): add hotkeys for formation data once hotkey support is in Py4GW
# in the meantime use https://github.com/apoguita/Py4GW/pull/153 for use at your own
# risk version with other potentially game breaking changes.
def ensure_formation_json_exists():
    if not os.path.exists(FORMATIONS_JSON_PATH):
        default_json = {
            "Flag Front": {
                HOTKEY: None,
                VK: None,
                COORDINATES: [
                    [0, 1000],
                    [0, 1000],
                    [0, 1000],
                    [0, 1000],
                    [0, 1000],
                    [0, 1000],
                    [0, 1000],
                ],
            },
            "1,2 - Double Backline": {
                HOTKEY: None,
                VK: None,
                COORDINATES: [
                    [200, -200],
                    [-200, -200],
                    [0, 200],
                    [-200, 450],
                    [200, 450],
                    [-400, 300],
                    [400, 300],
                ],
            },
            "1 - Single Backline": {
                HOTKEY: None,
                VK: None,
                COORDINATES: [
                    [0, -250],
                    [-100, 200],
                    [100, 200],
                    [-300, 500],
                    [300, 500],
                    [-350, 300],
                    [350, 300],
                ],
            },
            "1,2 - Double Backline Triple Row": {
                HOTKEY: None,
                VK: None,
                COORDINATES: [
                    [-200, -200],
                    [200, -200],
                    [-200, 0],
                    [200, 0],
                    [-200, 300],
                    [0, 300],
                    [200, 300],
                ],
            },
            "Disband Formation": {
                HOTKEY: None,
                VK: None,
                COORDINATES: [],
            },
        }
        with open(FORMATIONS_JSON_PATH, "w") as f:
            print(FORMATIONS_JSON_PATH)
            json.dump(default_json, f)  # empty dict initially


def save_formation_hotkey(
    formation_name: str, hotkey: str, vk: int, coordinates: list[tuple[int, int]]
):
    ensure_formation_json_exists()
    with open(FORMATIONS_JSON_PATH, "r") as f:
        data = json.load(f)

    # Save or update the formation
    data[formation_name] = {
        HOTKEY: hotkey,
        VK: vk,
        COORDINATES: coordinates,  # JSON supports list of lists directly
    }

    with open(FORMATIONS_JSON_PATH, "w") as f:
        json.dump(data, f, indent=4)


def load_formations_from_json():
    ensure_formation_json_exists()
    with open(FORMATIONS_JSON_PATH, "r") as f:
        data = json.load(f)
    return data


def get_key_pressed(vk_code):
    value = user32.GetAsyncKeyState(vk_code) & 0x8000
    is_value_not_zero = value != 0
    if is_value_not_zero:
        return vk_to_char(vk_code)
    return None


def char_to_vk(char: str) -> int:
    if len(char) != 1:
        pass
    vk = user32.VkKeyScanW(ord(char))
    if vk == -1:
        pass
    return vk & 0xFF  # The low byte is the VK code


def vk_to_char(vk_code):
    return chr(user32.MapVirtualKeyW(vk_code, 2))


hotkey_state = {"was_pressed": False}


def is_hotkey_pressed_once(vk_code=0x35):
    pressed = get_key_pressed(vk_code)
    if pressed and not hotkey_state["was_pressed"]:
        hotkey_state["was_pressed"] = True
        return True
    elif not pressed:
        hotkey_state["was_pressed"] = False
    return False


formation_hotkey_values = {}
# At the top-level (e.g., global scope or init function)
if not formation_hotkey_values:  # Only load once
    formations = load_formations_from_json()
    for formation_key, formation_data in formations.items():
        formation_hotkey_values[formation_key] = formation_data.get(HOTKEY, "") or ""

skills_prep_hotkey_values = {}


def draw_combat_prep_window(cached_data):
    global formation_hotkey_values, window_x, window_y, window_collapsed, first_run

    # 1) On first draw, restore last position & collapsed state
    if first_run:
        PyImGui.set_next_window_pos(window_x, window_y)
        PyImGui.set_next_window_collapsed(window_collapsed, 0)
        first_run = False

    is_window_opened = PyImGui.begin(
        "Combat Prep", PyImGui.WindowFlags.AlwaysAutoResize
    )
    new_collapsed = PyImGui.is_window_collapsed()
    end_pos = PyImGui.get_window_pos()

    if is_window_opened:
        is_party_leader = (
            GLOBAL_CACHE.Player.GetAgentID() == GLOBAL_CACHE.Party.GetPartyLeaderID()
        )
        if not GLOBAL_CACHE.Map.IsExplorable() or not is_party_leader:
            PyImGui.text("Need to be party Leader and in Explorable Area")
            return

        # capture current state
        PyImGui.is_window_collapsed()
        PyImGui.get_window_pos()

        party_size = cached_data.data.party_size
        disband_formation = False

        PyImGui.text("Formations:")
        PyImGui.separator()
        set_formations_relative_to_leader = []
        formations = load_formations_from_json()

        if PyImGui.begin_table("FormationTable", 3):
            # Setup column widths BEFORE starting the table rows
            PyImGui.table_setup_column(
                "Formation", PyImGui.TableColumnFlags.WidthStretch
            )  # auto-size
            PyImGui.table_setup_column(
                "Hotkey", PyImGui.TableColumnFlags.WidthFixed, 30.0
            )  # fixed 30px
            PyImGui.table_setup_column(
                "Save", PyImGui.TableColumnFlags.WidthStretch
            )  # auto-size
            for formation_key, formation_data in formations.items():
                if formation_data[HOTKEY]:
                    hotkey_pressed = get_key_pressed(formation_data[VK])
                else:
                    hotkey_pressed = False

                PyImGui.table_next_row()

                # Column 1: Formation Button
                PyImGui.table_next_column()
                button_pressed = PyImGui.button(formation_key)
                should_set_formation = hotkey_pressed or button_pressed

                # Column 2: Hotkey Input
                # Get and display editable input buffer
                PyImGui.table_next_column()
                current_value = formation_hotkey_values[formation_key] or ""
                PyImGui.set_next_item_width(30)
                raw_value = PyImGui.input_text(
                    f"##HotkeyInput_{formation_key}", current_value, 4
                )

                updated_value = raw_value.strip()[:1] if raw_value else ""
                # Store it persistently
                formation_hotkey_values[formation_key] = updated_value

                # Column 3: Save Hotkey Button
                PyImGui.table_next_column()
                if PyImGui.button(f"Save Hotkey##{formation_key}"):
                    input_value = updated_value.lower()
                    if len(input_value) == 1:
                        # Normalize to lowercase
                        input_value = input_value.lower()
                        vk_value = char_to_vk(input_value)
                        if input_value and vk_value:
                            save_formation_hotkey(
                                formation_key,
                                input_value,
                                vk_value,
                                formation_data[COORDINATES],
                            )
                        else:
                            save_formation_hotkey(
                                formation_key, None, None, formation_data[COORDINATES]
                            )
                    else:
                        print(
                            "[ERROR] Only a single character keyboard keys can be used for a Hotkey"
                        )

                if should_set_formation:
                    if len(formation_data[COORDINATES]):
                        set_formations_relative_to_leader = formation_data[COORDINATES]
                    else:
                        disband_formation = True
        PyImGui.end_table()

        if len(set_formations_relative_to_leader):
            leader_follow_angle = (
                cached_data.data.party_leader_rotation_angle
            )  # in radians
            leader_x, leader_y, _ = GLOBAL_CACHE.Agent.GetXYZ(
                GLOBAL_CACHE.Party.GetPartyLeaderID()
            )
            angle_rad = (
                leader_follow_angle - math.pi / 2
            )  # adjust for coordinate system

            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)

            for hero_ai_index in range(1, party_size):
                offset_x, offset_y = set_formations_relative_to_leader[
                    hero_ai_index - 1
                ]

                # Rotate offset
                rotated_x = offset_x * cos_a - offset_y * sin_a
                rotated_y = offset_x * sin_a + offset_y * cos_a

                # Apply rotated offset to leader's position
                final_x = leader_x + rotated_x
                final_y = leader_y + rotated_y

                for flag_key, flag_key_value in [
                    (IS_FLAGGED, True),
                    (FLAG_POSITION_X, final_x),
                    (FLAG_POSITION_Y, final_y),
                    (FOLOW_ANGLE, leader_follow_angle),
                ]:
                    cached_data.HeroAI_vars.shared_memory_handler.set_player_property(
                        hero_ai_index, flag_key, flag_key_value
                    )

        if disband_formation:
            for hero_ai_index in range(1, party_size):
                for flag_key, flag_key_value in [
                    (IS_FLAGGED, False),
                    (FLAG_POSITION_X, 0),
                    (FLAG_POSITION_Y, 0),
                    (FOLOW_ANGLE, 0),
                ]:
                    cached_data.HeroAI_vars.shared_memory_handler.set_player_property(
                        hero_ai_index, flag_key, flag_key_value
                    )
                GLOBAL_CACHE.Party.Heroes.UnflagHero(hero_ai_index)
                GLOBAL_CACHE.Party.Heroes.UnflagAllHeroes()

        PyImGui.text("Skill Prep:")
        PyImGui.separator()

        if PyImGui.begin_table("SkillPrepTable", 3):
            # Setup column widths BEFORE starting the table rows
            PyImGui.table_setup_column(
                "SkillUsage", PyImGui.TableColumnFlags.WidthStretch
            )  # auto-size
            PyImGui.table_setup_column(
                "Hotkey", PyImGui.TableColumnFlags.WidthFixed, 30.0
            )  # fixed 30px
            PyImGui.table_setup_column(
                "Save", PyImGui.TableColumnFlags.WidthStretch
            )  # auto-size

            PyImGui.table_next_row()
            # Column 1: Formation Button
            PyImGui.table_next_column()
            st_button_pressed = PyImGui.button("Spirits Prep")

            # Column 2: Hotkey Input
            # Get and display editable input buffer
            PyImGui.table_next_column()

            # Column 3: Save Hotkey Button
            PyImGui.table_next_column()

            sender_email = cached_data.account_email

            if is_party_leader:
                # Only party leader is allowed to have access to hotkey
                if st_button_pressed or is_hotkey_pressed_once(0x35):
                    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
                    for account in accounts:
                        if sender_email != account.AccountEmail:
                            GLOBAL_CACHE.ShMem.SendMessage(
                                sender_email,
                                account.AccountEmail,
                                SharedCommandType.UseSkill,
                                (CombatPrepSkillsType.SpiritsPrep, 0, 0, 0),
                            )
        PyImGui.end_table()

        PyImGui.text("Control Quick Action:")
        PyImGui.separator()
        if PyImGui.begin_table("OtherSetupTable", 3):
            # Setup column widths BEFORE starting the table rows
            PyImGui.table_setup_column(
                "OtherSetup", PyImGui.TableColumnFlags.WidthStretch
            )  # auto-size
            PyImGui.table_setup_column(
                "Hotkey", PyImGui.TableColumnFlags.WidthFixed, 30.0
            )  # fixed 30px
            PyImGui.table_setup_column(
                "Save", PyImGui.TableColumnFlags.WidthStretch
            )  # auto-size

            PyImGui.table_next_row()
            # Column 1: Formation Button
            PyImGui.table_next_column()
            disable_party_leader_hero_ai = PyImGui.button("Disable Party Leader HeroAI")

            # Column 2: Hotkey Input
            # Get and display editable input buffer
            PyImGui.table_next_column()

            # Column 3: Save Hotkey Button
            PyImGui.table_next_column()

            sender_email = cached_data.account_email

            if is_party_leader and disable_party_leader_hero_ai:
                GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    sender_email,
                    SharedCommandType.DisableHeroAI,
                    (0, 0, 0, 0),
                )
        PyImGui.end_table()
    PyImGui.end()

    if save_window_timer.HasElapsed(1000):
        # Position changed?
        if (end_pos[0], end_pos[1]) != (window_x, window_y):
            window_x, window_y = int(end_pos[0]), int(end_pos[1])
            ini_window.write_key(MODULE_NAME, X_POS, str(window_x))
            ini_window.write_key(MODULE_NAME, Y_POS, str(window_y))
        # Collapsed state changed?
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
            draw_combat_prep_window(cached_data)

    except ImportError as e:
        Py4GW.Console.Log(
            MODULE_NAME,
            f"ImportError encountered: {str(e)}",
            Py4GW.Console.MessageType.Error,
        )
        Py4GW.Console.Log(
            MODULE_NAME,
            f"Stack trace: {traceback.format_exc()}",
            Py4GW.Console.MessageType.Error,
        )
    except ValueError as e:
        Py4GW.Console.Log(
            MODULE_NAME,
            f"ValueError encountered: {str(e)}",
            Py4GW.Console.MessageType.Error,
        )
        Py4GW.Console.Log(
            MODULE_NAME,
            f"Stack trace: {traceback.format_exc()}",
            Py4GW.Console.MessageType.Error,
        )
    except TypeError as e:
        Py4GW.Console.Log(
            MODULE_NAME,
            f"TypeError encountered: {str(e)}",
            Py4GW.Console.MessageType.Error,
        )
        Py4GW.Console.Log(
            MODULE_NAME,
            f"Stack trace: {traceback.format_exc()}",
            Py4GW.Console.MessageType.Error,
        )
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(
            MODULE_NAME,
            f"Unexpected error encountered: {str(e)}",
            Py4GW.Console.MessageType.Error,
        )
        Py4GW.Console.Log(
            MODULE_NAME,
            f"Stack trace: {traceback.format_exc()}",
            Py4GW.Console.MessageType.Error,
        )
    finally:
        pass


if __name__ == "__main__":
    main()
