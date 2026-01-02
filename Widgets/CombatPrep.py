import ctypes
import json
import math
import os
import time
import traceback

import Py4GW
from HeroAI.cache_data import CacheData
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import CombatPrepSkillsType
from Py4GWCoreLib import IconsFontAwesome5
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import Range
from Py4GWCoreLib import Map
from Py4GWCoreLib import Routines
from Py4GWCoreLib import SharedCommandType
from Py4GWCoreLib import Timer
from Py4GW_widget_manager import get_widget_handler

user32 = ctypes.WinDLL("user32", use_last_error=True)
try:
    script_directory = os.path.dirname(os.path.abspath(__file__))
    in_file = True
except NameError:
    # __file__ is not defined (e.g. running in interactive mode or embedded interpreter)
    script_directory = os.getcwd()
    in_file = False
project_root = os.path.abspath(os.path.join(script_directory, os.pardir))

first_run = True

MODULE_NAME = "CombatPrep"
BASE_DIR = os.path.join(project_root, "Widgets/Config")
FORMATIONS_JSON_PATH = os.path.join(BASE_DIR, "formation_hotkey.json")
INI_WIDGET_WINDOW_PATH = os.path.join(BASE_DIR, "combat_prep_window.ini")
TEXTURES_PATH = os.path.join(BASE_DIR, 'textures/combat_prep')
os.makedirs(BASE_DIR, exist_ok=True)

# String consts
COLLAPSED = "collapsed"
COORDINATES = "coordinates"
DEFAULT = "default"
DISABLE_PARTY_LEADER_TOOL_TIP_TEXT = "Disable Party Leader HeroAI"
DISABLE_PARTY_MEMBERS_TOOL_TIP_TEXT = "Disable Party Members HeroAI"
ENABLE_PARTY_LEADER_TOOL_TIP_TEXT = "Enable Party Leader HeroAI"
ENABLE_PARTY_MEMBERS_TOOL_TIP_TEXT = "Enable Party Members HeroAI"
MODULE_ICON_SIZE = 'module_icon_size'
MODULE_LAYOUT = 'module_layout'
USE_HOTKEYS = 'use_hotkeys'
ROW = "row"
SPIRITS_CAST_COOLDOWN_MS = 4000
SPIRITS_BUTTON_TOOL_TIP_TEXT = "Spirits Prep"
SPIRITS_TOOL_TIP_TEXT = "Enable smart-casting of spirits when party is close enough to an enemy"
SPIRITS_BRAIN_TEXT = IconsFontAwesome5.ICON_BRAIN + "##Spirits"
SPIRITS_BUTTON_ID = "##SpiritsPrepButton"
SHOUTS_CAST_COOLDOWN_MS = 5000
SHOUTS_BUTTON_TOOL_TIP_TEXT = "Shouts Prep"
SHOUTS_TOOL_TIP_TEXT = (
    "Enable smart-casting of shouts when party is close enough to an enemy and within earshot of party leader"
)
SHOUTS_BRAIN_TEXT = IconsFontAwesome5.ICON_BRAIN + "##Shouts"
SHOUTS_BUTTON_ID = "##ShoutsPrepButton"
TOGGLE_PARTY_LEADER_BUTTON_ID = '##TogglePartyLeaderHeroAI'
TOGGLE_PARTY_MEMBERS_BUTTON_ID = '##TogglePartyHeroAI'
TOGGLE_PARTY_MEMBERS_BRAIN_TEXT = IconsFontAwesome5.ICON_BRAIN + "##TogglePartyHeroAI"
TOGGLE_PARTY_MEMBERS_COOLDOWN_MS = 20000
TOGGLE_PARTY_MEMBERS_TOOL_TIP_TEXT = "Enables Auto triggering every 20 seconds to prevent Rits and Paragon from lagging"
TIMESTAMP = "timestamp"
TEXTURE = "texture_path"
VALUE = 'value'
VK = "vk"
WAS_PRESSED = "was_pressed"
X_POS = "x"
Y_POS = "y"

# Flag constants
IS_FLAGGED = "IsFlagged"
FLAG_POSITION_X = "FlagPosX"
FLAG_POSITION_Y = "FlagPosY"
FOLOW_ANGLE = "FollowAngle"

cached_data = CacheData()
widget_handler = get_widget_handler()


# ——— Window Persistence Setup ———
ini_window = IniHandler(INI_WIDGET_WINDOW_PATH)
save_window_timer = Timer()
save_window_timer.Start()

# load last‐saved window state (fallback to 100,100 / un-collapsed)
window_x = ini_window.read_int(MODULE_NAME, X_POS, 100)
window_y = ini_window.read_int(MODULE_NAME, Y_POS, 100)
module_layout = ini_window.read_key(MODULE_NAME, MODULE_LAYOUT, DEFAULT)
module_icon_size = ini_window.read_int(MODULE_NAME, MODULE_ICON_SIZE, 80)
window_collapsed = ini_window.read_bool(MODULE_NAME, COLLAPSED, False)
should_use_hotkeys = ini_window.read_bool(MODULE_NAME, USE_HOTKEYS, False)

# Global Trackers
last_location_spirits_casted = {X_POS: 0.0, Y_POS: 0.0}
last_spirit_cast_time = {TIMESTAMP: 0}
auto_spirit_cast_enabled = {VALUE: True}

last_location_shouts_casted = {X_POS: 0.0, Y_POS: 0.0}
last_shout_cast_time = {TIMESTAMP: 0}
auto_shout_cast_enabled = {VALUE: True}

last_toggle_party_members_hero_ai_follow_time = {TIMESTAMP: 0}
auto_toggle_party_members_hero_ai_follow_enabled = {VALUE: True}


hotkey_state = {WAS_PRESSED: False}


# TODO (mark): add hotkeys for formation data once hotkey support is in Py4GW
# in the meantime use https://github.com/apoguita/Py4GW/pull/153 for use at your own
# risk version with other potentially game breaking changes.
def ensure_formation_json_exists():
    def is_valid_formation_data(data):
        # Ensure top-level keys and per-formation structure are valid
        if not isinstance(data, dict):
            return False
        for name, entry in data.items():  # noqa: name unused
            if not isinstance(entry, dict):
                return False
            if not all(k in entry for k in (VK, COORDINATES, TEXTURE)):
                return False
            if not isinstance(entry[COORDINATES], list):
                return False
        return True

    default_json = {
        "1,2 - Double Backline": {
            VK: 0x31,
            COORDINATES: [[200, -200], [-200, -200], [0, 200], [-200, 450], [200, 450], [-400, 300], [400, 300]],
            TEXTURE: f'{TEXTURES_PATH}/double_backline.png',
        },
        "1 - Single Backline": {
            VK: 0x32,
            COORDINATES: [[0, -250], [-100, 200], [100, 200], [-300, 500], [300, 500], [-350, 300], [350, 300]],
            TEXTURE: f'{TEXTURES_PATH}/single_backline.png',
        },
        "1,2 - Double Backline Triple Row": {
            VK: 0x06,
            COORDINATES: [[-200, -200], [200, -200], [-200, 0], [200, 0], [-200, 300], [0, 300], [200, 300]],
            TEXTURE: f'{TEXTURES_PATH}/double_backline_triple_row.png',
        },
        "Flag Front": {
            VK: 0x05,
            COORDINATES: [[0, 1000], [0, 1000], [0, 1000], [0, 1000], [0, 1000], [0, 1000], [0, 1000], [0, 1000]],
            TEXTURE: f'{TEXTURES_PATH}/flag_front.png',
        },
        "Disband Formation": {
            VK: 0x04,
            COORDINATES: [],
            TEXTURE: f'{TEXTURES_PATH}/disband_formation.png',
        },
    }

    should_overwrite = False

    if os.path.exists(FORMATIONS_JSON_PATH):
        try:
            with open(FORMATIONS_JSON_PATH, "r") as f:
                data = json.load(f)
            if not is_valid_formation_data(data):
                print("[CombatPrep] Invalid format detected, overwriting.")
                should_overwrite = True
        except (json.JSONDecodeError, IOError):
            print("[CombatPrep] JSON error detected, overwriting.")
            should_overwrite = True
    else:
        should_overwrite = True

    if should_overwrite:
        with open(FORMATIONS_JSON_PATH, "w") as f:
            json.dump(default_json, f, indent=4)
            print(f"[CombatPrep] Formation JSON reset at {FORMATIONS_JSON_PATH}")


def is_my_instance_focused():
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return False

    pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

    return pid.value == os.getpid()


def load_formations_from_json():
    ensure_formation_json_exists()
    with open(FORMATIONS_JSON_PATH, "r") as f:
        data = json.load(f)
    return data


def get_key_pressed(vk_code):
    if not should_use_hotkeys or not is_my_instance_focused():
        return None

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


def is_hotkey_pressed_once(vk_code=0x35):
    pressed = get_key_pressed(vk_code)
    if pressed and not hotkey_state[WAS_PRESSED]:
        hotkey_state[WAS_PRESSED] = True
        return True
    elif not pressed:
        hotkey_state[WAS_PRESSED] = False
    return False


class CombatPrep:
    def __init__(self, cached_data, module_icon_size, module_layout):
        self.is_party_leader = GLOBAL_CACHE.Player.GetAgentID() == GLOBAL_CACHE.Party.GetPartyLeaderID()
        self.formations = load_formations_from_json()
        self.cached_data = cached_data
        self.module_icon_size = module_icon_size
        self.module_layout = module_layout

    # helper methods
    def get_party_center(self):
        total_x = 0
        total_y = 0
        count = 0

        for slot in GLOBAL_CACHE.Party.GetPlayers():
            agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(slot.login_number)
            if agent_id:
                agent_x, agent_y = GLOBAL_CACHE.Agent.GetXY(agent_id)
                total_x += agent_x
                total_y += agent_y
                count += 1

        center_x = total_x / count
        center_y = total_y / count

        return center_x, center_y

    def get_party_leader_x_y(self):
        party_leader_id = GLOBAL_CACHE.Party.GetPartyLeaderID()
        return GLOBAL_CACHE.Agent.GetXY(party_leader_id)

    def is_party_leader_hero_ai_status_enabled(self):
        if not self.is_party_leader:
            return False

        # assumes this is party leader account email because they are the only one that has access
        hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(self.cached_data.account_email)
        if hero_ai_options is None:
            return False

        status = True
        for option in [
            hero_ai_options.Following,
            hero_ai_options.Avoidance,
            hero_ai_options.Looting,
            hero_ai_options.Targeting,
            hero_ai_options.Combat,
        ]:
            status = option and status
        return status

    def get_party_leader_texture_path_icon(self):
        texture_path_to_use = (
            f'{TEXTURES_PATH}/enable_pt_leader_hero_ai.png'
            if self.is_party_leader_hero_ai_status_enabled()
            else f'{TEXTURES_PATH}/disable_pt_leader_hero_ai.png'
        )
        return texture_path_to_use

    def is_party_members_hero_ai_status_enabled(self):
        status = True
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        for account in accounts:
            if self.cached_data.account_email != account.AccountEmail:
                hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account.AccountEmail)
                if hero_ai_options is None:
                    continue

                for option in [
                    hero_ai_options.Following,
                    hero_ai_options.Avoidance,
                    hero_ai_options.Looting,
                    hero_ai_options.Targeting,
                    hero_ai_options.Combat,
                ]:
                    status = option and status
        return status

    def get_party_members_texture_path_icon(self):
        texture_path_to_use = (
            f'{TEXTURES_PATH}/enable_pt_hero_ai.png'
            if self.is_party_members_hero_ai_status_enabled()
            else f'{TEXTURES_PATH}/disable_pt_hero_ai.png'
        )
        return texture_path_to_use

    # callback methods
    def cb_set_formation(self, set_formations_relative_to_leader, disband_formation, custom_angle=None):
        party_size = GLOBAL_CACHE.Party.GetPartySize()
        if len(set_formations_relative_to_leader):
            leader_follow_angle = GLOBAL_CACHE.Agent.GetRotationAngle(GLOBAL_CACHE.Party.GetPartyLeaderID())  # in radians
            party_leader_id = GLOBAL_CACHE.Party.GetPartyLeaderID()
            leader_x, leader_y, _ = GLOBAL_CACHE.Agent.GetXYZ(party_leader_id)
            angle_rad = leader_follow_angle - math.pi / 2  # adjust for coordinate system

            if custom_angle:
                angle_rad = custom_angle
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)

            for hero_ai_index in range(1, party_size):
                offset_x, offset_y = set_formations_relative_to_leader[hero_ai_index - 1]

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
                    self.cached_data.HeroAI_vars.shared_memory_handler.set_player_property(
                        hero_ai_index, flag_key, flag_key_value
                    )

                agent_id = GLOBAL_CACHE.Party.Heroes.GetHeroAgentIDByPartyPosition(hero_ai_index)
                if agent_id:
                    GLOBAL_CACHE.Party.Heroes.FlagHero(agent_id, final_x, final_y)

        if disband_formation:
            for hero_ai_index in range(1, party_size):
                for flag_key, flag_key_value in [
                    (IS_FLAGGED, False),
                    (FLAG_POSITION_X, 0),
                    (FLAG_POSITION_Y, 0),
                    (FOLOW_ANGLE, 0),
                ]:
                    self.cached_data.HeroAI_vars.shared_memory_handler.set_player_property(
                        hero_ai_index, flag_key, flag_key_value
                    )
                GLOBAL_CACHE.Party.Heroes.UnflagHero(hero_ai_index)
                GLOBAL_CACHE.Party.Heroes.UnflagAllHeroes()

    def cb_spirits_prep(self, st_button_pressed):
        sender_email = self.cached_data.account_email

        if self.is_party_leader:
            enemy_agent = Routines.Agents.GetNearestEnemy(max_distance=1850)
            party_center_x, party_center_y = self.get_party_center()

            dist_x = party_center_x - last_location_spirits_casted[X_POS]
            dist_y = party_center_y - last_location_spirits_casted[Y_POS]
            distance_squared = dist_x * dist_x + dist_y * dist_y
            distance_threshold_squared = 2300 * 2300
            now = int(time.time() * 1000)
            time_since_last_cast = now - last_spirit_cast_time[TIMESTAMP]

            should_cast = (
                st_button_pressed
                or is_hotkey_pressed_once(0x36)
                or (auto_spirit_cast_enabled[VALUE] and enemy_agent and distance_squared >= distance_threshold_squared)
            ) and time_since_last_cast >= SPIRITS_CAST_COOLDOWN_MS

            if should_cast:
                last_location_spirits_casted[X_POS] = party_center_x
                last_location_spirits_casted[Y_POS] = party_center_y
                last_spirit_cast_time[TIMESTAMP] = now

                accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
                for account in accounts:
                    if sender_email != account.AccountEmail:
                        GLOBAL_CACHE.ShMem.SendMessage(
                            sender_email,
                            account.AccountEmail,
                            SharedCommandType.UseSkillCombatPrep,
                            (CombatPrepSkillsType.SpiritsPrep, 0, 0, 0),
                        )

    def cb_shouts_prep(self, shouts_button_pressed):
        sender_email = self.cached_data.account_email

        if self.is_party_leader:
            enemy_agent = Routines.Agents.GetNearestEnemy(max_distance=1850)
            center_x, center_y = self.get_party_leader_x_y()
            player_x, player_y = GLOBAL_CACHE.Player.GetXY()

            dist_x = center_x - player_x
            dist_y = center_y - player_y
            distance_squared = dist_x * dist_x + dist_y * dist_y
            earshot_radius_squared = Range.Earshot.value * Range.Earshot.value
            is_within_earshot_of_party_leader = distance_squared <= earshot_radius_squared

            dist_x_last = center_x - last_location_shouts_casted[X_POS]
            dist_y_last = center_y - last_location_shouts_casted[Y_POS]
            distance_from_last_cast_squared = dist_x_last * dist_x_last + dist_y_last * dist_y_last
            distance_threshold_squared = 2300 * 2300

            now = int(time.time() * 1000)
            time_since_last_cast = now - last_shout_cast_time[TIMESTAMP]

            should_cast = (
                shouts_button_pressed
                or is_hotkey_pressed_once(0x36)
                or (
                    auto_shout_cast_enabled[VALUE]
                    and enemy_agent
                    and distance_from_last_cast_squared >= distance_threshold_squared
                    and is_within_earshot_of_party_leader
                )
            ) and time_since_last_cast >= SHOUTS_CAST_COOLDOWN_MS

            if should_cast:
                last_location_shouts_casted[X_POS] = center_x
                last_location_shouts_casted[Y_POS] = center_y
                last_shout_cast_time[TIMESTAMP] = now

                accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
                for account in accounts:
                    if sender_email != account.AccountEmail:
                        GLOBAL_CACHE.ShMem.SendMessage(
                            sender_email,
                            account.AccountEmail,
                            SharedCommandType.UseSkillCombatPrep,
                            (CombatPrepSkillsType.ShoutsPrep, 0, 0, 0),
                        )

    def cb_toggle_party_leader_hero_ai(self, toggle_party_leader_hero_ai_button_pressed):
        sender_email = self.cached_data.account_email

        if self.is_party_leader and toggle_party_leader_hero_ai_button_pressed:
            if self.is_party_leader_hero_ai_status_enabled():
                GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    sender_email,
                    SharedCommandType.DisableHeroAI,
                    (0, 0, 0, 0),
                )
            else:
                GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    sender_email,
                    SharedCommandType.EnableHeroAI,
                    (1, 0, 0, 0),
                )

    def cb_toggle_party_members_hero_ai(self, toggle_party_members_hero_ai_button_pressed):
        sender_email = self.cached_data.account_email
        now = int(time.time() * 1000)
        time_since_last_cast = now - last_toggle_party_members_hero_ai_follow_time[TIMESTAMP]
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()

        if (
            auto_toggle_party_members_hero_ai_follow_enabled[VALUE]
            and time_since_last_cast >= TOGGLE_PARTY_MEMBERS_COOLDOWN_MS
            and not self.is_party_members_hero_ai_status_enabled()
        ):
            last_toggle_party_members_hero_ai_follow_time[TIMESTAMP] = now
            for account in accounts:
                if sender_email != account.AccountEmail:
                    GLOBAL_CACHE.ShMem.SendMessage(
                        sender_email,
                        account.AccountEmail,
                        SharedCommandType.EnableHeroAI,
                        (1, 0, 0, 0),
                    )
            return

        if self.is_party_leader and toggle_party_members_hero_ai_button_pressed:
            for account in accounts:
                if sender_email != account.AccountEmail:
                    if self.is_party_members_hero_ai_status_enabled():
                        GLOBAL_CACHE.ShMem.SendMessage(
                            sender_email,
                            account.AccountEmail,
                            SharedCommandType.DisableHeroAI,
                            (0, 0, 0, 0),
                        )
                    else:
                        GLOBAL_CACHE.ShMem.SendMessage(
                            sender_email,
                            account.AccountEmail,
                            SharedCommandType.EnableHeroAI,
                            (1, 0, 0, 0),
                        )

    # UI formats
    def _row_ui(self):
        disband_formation = False
        set_formations_relative_to_leader = []
        icon_size = self.module_icon_size

        if PyImGui.begin_table("CompactRowUI", 9):
            # Setup columns
            for column in range(9):
                PyImGui.table_setup_column(f"Icon_{column}", PyImGui.TableColumnFlags.WidthStretch)

            # --- First row: Formations + control buttons ---
            PyImGui.table_next_row()
            formation_keys = list(self.formations.keys())

            for col_index in range(9):
                PyImGui.table_next_column()

                if col_index < len(formation_keys):
                    # Show formation buttons
                    formation_key = formation_keys[col_index]
                    formation_data = self.formations[formation_key]

                    pressed = ImGui.ImageButton(f"##{formation_key}", formation_data[TEXTURE], icon_size, icon_size)
                    ImGui.show_tooltip(formation_key)

                    hotkey_pressed = get_key_pressed(formation_data[VK]) if formation_data[VK] else False
                    should_set = hotkey_pressed or pressed

                    if should_set:
                        if formation_data[COORDINATES]:
                            set_formations_relative_to_leader = formation_data[COORDINATES]
                        else:
                            disband_formation = True
                else:
                    st_button_pressed = False
                    shouts_button_pressed = False
                    # Remaining slots = static control buttons
                    if col_index == 5:
                        st_button_pressed = ImGui.ImageButton(
                            SPIRITS_BUTTON_ID, f'{TEXTURES_PATH}/st_sos_combo.png', icon_size, icon_size
                        )
                        ImGui.show_tooltip(SPIRITS_BUTTON_TOOL_TIP_TEXT)
                        self.cb_spirits_prep(st_button_pressed)
                    if col_index == 6:
                        shouts_button_pressed = ImGui.ImageButton(
                            SHOUTS_BUTTON_ID, f'{TEXTURES_PATH}/shouts_combo.png', icon_size, icon_size
                        )
                        ImGui.show_tooltip(SHOUTS_BUTTON_TOOL_TIP_TEXT)
                        self.cb_shouts_prep(shouts_button_pressed)
                    elif col_index == 7:
                        toggle_button_pressed = ImGui.ImageButton(
                            TOGGLE_PARTY_LEADER_BUTTON_ID,
                            self.get_party_leader_texture_path_icon(),
                            icon_size,
                            icon_size,
                        )
                        ImGui.show_tooltip(
                            DISABLE_PARTY_LEADER_TOOL_TIP_TEXT
                            if self.is_party_leader_hero_ai_status_enabled()
                            else ENABLE_PARTY_LEADER_TOOL_TIP_TEXT
                        )
                        self.cb_toggle_party_leader_hero_ai(toggle_button_pressed)
                    elif col_index == 8:
                        toggle_button_pressed = ImGui.ImageButton(
                            TOGGLE_PARTY_MEMBERS_BUTTON_ID,
                            self.get_party_members_texture_path_icon(),
                            icon_size,
                            icon_size,
                        )
                        ImGui.show_tooltip(
                            DISABLE_PARTY_MEMBERS_TOOL_TIP_TEXT
                            if self.is_party_members_hero_ai_status_enabled()
                            else ENABLE_PARTY_MEMBERS_TOOL_TIP_TEXT
                        )
                        self.cb_toggle_party_members_hero_ai(toggle_button_pressed)

            # Apply selected formation
            self.cb_set_formation(set_formations_relative_to_leader, disband_formation)

            # --- Second row: toggles aligned by column ---
            PyImGui.table_next_row()
            for col_index in range(9):
                PyImGui.table_next_column()

                if col_index == 5:
                    auto_spirit_cast_enabled[VALUE] = ImGui.toggle_button(
                        SPIRITS_BRAIN_TEXT,
                        auto_spirit_cast_enabled[VALUE],
                        icon_size + icon_size * 0.15,
                        icon_size / 1.75,
                    )
                    ImGui.show_tooltip(SPIRITS_TOOL_TIP_TEXT)
                if col_index == 6:
                    auto_shout_cast_enabled[VALUE] = ImGui.toggle_button(
                        SHOUTS_BRAIN_TEXT,
                        auto_shout_cast_enabled[VALUE],
                        icon_size + icon_size * 0.15,
                        icon_size / 1.75,
                    )
                    ImGui.show_tooltip(SHOUTS_TOOL_TIP_TEXT)
                if col_index == 8:
                    auto_toggle_party_members_hero_ai_follow_enabled[VALUE] = ImGui.toggle_button(
                        TOGGLE_PARTY_MEMBERS_BRAIN_TEXT,
                        auto_toggle_party_members_hero_ai_follow_enabled[VALUE],
                        icon_size + icon_size * 0.15,
                        icon_size / 1.75,
                    )
                    ImGui.show_tooltip(TOGGLE_PARTY_MEMBERS_TOOL_TIP_TEXT)
        PyImGui.end_table()

    def _default_ui(self):
        disband_formation = False
        set_formations_relative_to_leader = []
        icon_size = self.module_icon_size

        PyImGui.text("Formations:")
        PyImGui.separator()

        if PyImGui.begin_table("FormationTable", 3):
            for column in range(3):
                PyImGui.table_setup_column(f"Formation_{column}", PyImGui.TableColumnFlags.WidthStretch)

            col_index = 0
            for formation_key, formation_data in self.formations.items():
                if col_index % 3 == 0:
                    PyImGui.table_next_row()

                PyImGui.table_next_column()

                set_formation_button_pressed = ImGui.ImageButton(
                    f"##{formation_key}", formation_data[TEXTURE], icon_size, icon_size
                )
                ImGui.show_tooltip(formation_key)

                hotkey_pressed = get_key_pressed(formation_data[VK]) if formation_data[VK] else False
                should_set_formation = hotkey_pressed or set_formation_button_pressed

                if should_set_formation:
                    if len(formation_data[COORDINATES]):
                        set_formations_relative_to_leader = formation_data[COORDINATES]
                    else:
                        disband_formation = True

                col_index += 1
            self.cb_set_formation(set_formations_relative_to_leader, disband_formation)
        PyImGui.end_table()

        PyImGui.text("Skill Prep:")
        PyImGui.separator()

        if PyImGui.begin_table("SkillPrepTable", 3):
            for column in range(3):
                PyImGui.table_setup_column(f"SkillUsage_{column}", PyImGui.TableColumnFlags.WidthStretch)

            PyImGui.table_next_row()
            PyImGui.table_next_column()

            # --- Spirits Prep Button ---
            st_button_pressed = ImGui.ImageButton(
                SPIRITS_BUTTON_ID, f'{TEXTURES_PATH}/st_sos_combo.png', icon_size, icon_size
            )
            ImGui.show_tooltip(SPIRITS_BUTTON_TOOL_TIP_TEXT)

            # --- Auto-cast Toggle Below ---
            auto_spirit_cast_enabled[VALUE] = ImGui.toggle_button(
                SPIRITS_BRAIN_TEXT,
                auto_spirit_cast_enabled[VALUE],
                icon_size + icon_size * 0.15,
                icon_size / 1.75,
            )
            ImGui.show_tooltip(SPIRITS_TOOL_TIP_TEXT)
            self.cb_spirits_prep(st_button_pressed)

            PyImGui.table_next_column()

            # --- Shouts Prep Button ---
            shouts_button_pressed = ImGui.ImageButton(
                SHOUTS_BUTTON_ID, f'{TEXTURES_PATH}/shouts_combo.png', icon_size, icon_size
            )
            ImGui.show_tooltip(SHOUTS_BUTTON_TOOL_TIP_TEXT)

            # --- Auto-cast Toggle Below ---
            auto_shout_cast_enabled[VALUE] = ImGui.toggle_button(
                SHOUTS_BRAIN_TEXT,
                auto_shout_cast_enabled[VALUE],
                icon_size + icon_size * 0.15,
                icon_size / 1.75,
            )
            ImGui.show_tooltip(SHOUTS_TOOL_TIP_TEXT)
            self.cb_shouts_prep(shouts_button_pressed)
        PyImGui.end_table()

        PyImGui.text("Control Quick Action:")
        PyImGui.separator()
        if PyImGui.begin_table("OtherSetupTable", 3):
            for column in range(3):
                PyImGui.table_setup_column(f"OtherSetup_{column}", PyImGui.TableColumnFlags.WidthStretch)  # auto-size

            PyImGui.table_next_row()
            # Column 1: Formation Button
            PyImGui.table_next_column()
            toggle_button_pressed_party_leader = ImGui.ImageButton(
                TOGGLE_PARTY_LEADER_BUTTON_ID, self.get_party_leader_texture_path_icon(), icon_size, icon_size
            )
            ImGui.show_tooltip(
                DISABLE_PARTY_LEADER_TOOL_TIP_TEXT
                if self.is_party_leader_hero_ai_status_enabled()
                else ENABLE_PARTY_LEADER_TOOL_TIP_TEXT
            )
            self.cb_toggle_party_leader_hero_ai(toggle_button_pressed_party_leader)

            PyImGui.table_next_column()
            toggle_button_pressed_party_members = ImGui.ImageButton(
                TOGGLE_PARTY_MEMBERS_BUTTON_ID, self.get_party_members_texture_path_icon(), icon_size, icon_size
            )
            ImGui.show_tooltip(
                DISABLE_PARTY_MEMBERS_TOOL_TIP_TEXT
                if self.is_party_members_hero_ai_status_enabled()
                else ENABLE_PARTY_MEMBERS_TOOL_TIP_TEXT
            )
            auto_toggle_party_members_hero_ai_follow_enabled[VALUE] = ImGui.toggle_button(
                TOGGLE_PARTY_MEMBERS_BRAIN_TEXT,
                auto_toggle_party_members_hero_ai_follow_enabled[VALUE],
                icon_size + icon_size * 0.15,
                icon_size / 1.75,
            )
            ImGui.show_tooltip(TOGGLE_PARTY_MEMBERS_TOOL_TIP_TEXT)
            self.cb_toggle_party_members_hero_ai(toggle_button_pressed_party_members)

            # Column 2: Hotkey Input
            PyImGui.table_next_column()

            # Column 3: Save Hotkey Button
            PyImGui.table_next_column()
        PyImGui.end_table()

    # UI methods - UI drawing and functionality marker for calling the callback methods
    def draw_window(self):
        global first_run
        global last_location_spirits_casted
        global time_since_last_cast
        global window_collapsed
        global window_x
        global window_y

        # 1) On first draw, restore last position & collapsed state
        if first_run:
            PyImGui.set_next_window_pos(window_x, window_y)
            PyImGui.set_next_window_collapsed(window_collapsed, 0)
            first_run = False

        is_window_opened = PyImGui.begin("Combat Prep", PyImGui.WindowFlags.AlwaysAutoResize)
        new_collapsed = PyImGui.is_window_collapsed()
        end_pos = PyImGui.get_window_pos()

        if is_window_opened:
            is_hero_ai_enabled = widget_handler.is_widget_enabled("HeroAI")
            if not Map.IsExplorable() or not self.is_party_leader or not is_hero_ai_enabled:
                header_text = "The following prevents you from using CombatPrep:"
                final_text = header_text
                if not Map.IsExplorable():
                    final_text += "\n  - Not in Explorable Area"
                if not self.is_party_leader:
                    final_text += "\n  - Not Currently Party Leader"
                if not is_hero_ai_enabled:
                    final_text += "\n  - HeroAI is not running "
                PyImGui.text(final_text)
                return

            # capture current state
            PyImGui.is_window_collapsed()
            PyImGui.get_window_pos()
            if self.module_layout == ROW:
                self._row_ui()
            else:
                self._default_ui()
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
    global module_icon_size
    global module_layout
    global should_use_hotkeys

    if PyImGui.begin('Combat Prep Configs', PyImGui.WindowFlags.AlwaysAutoResize):
        # --- Icon Size ---
        icon_sizes = ['80', '60', '40']
        current_icon_index = icon_sizes.index(str(module_icon_size))
        new_icon_index = PyImGui.combo('Icon Size', current_icon_index, icon_sizes)
        new_icon_size = int(icon_sizes[new_icon_index])
        if new_icon_size != module_icon_size:
            module_icon_size = new_icon_size
            ini_window.write_key(MODULE_NAME, MODULE_ICON_SIZE, str(module_icon_size))

        # --- Layout ---
        layouts = [DEFAULT, ROW]
        current_layout_index = layouts.index(module_layout)
        new_layout_index = PyImGui.combo('Layout Style', current_layout_index, layouts)
        new_layout = layouts[new_layout_index]
        if new_layout != module_layout:
            module_layout = new_layout
            ini_window.write_key(MODULE_NAME, MODULE_LAYOUT, module_layout)

        # --- Hotkey Usage ---
        previous_should_use_hotkey_value = should_use_hotkeys
        should_use_hotkeys = ImGui.toggle_button('Allow to use pre-set Hotkeys##ShouldUseHotkeys', should_use_hotkeys)
        if should_use_hotkeys != previous_should_use_hotkey_value:
            ini_window.write_key(MODULE_NAME, USE_HOTKEYS, should_use_hotkeys)
    PyImGui.end()


def main():
    global cached_data
    try:
        if not Routines.Checks.Map.MapValid():
            return

        cached_data.Update()
        if Map.IsMapReady() and GLOBAL_CACHE.Party.IsPartyLoaded():
            combat_prep = CombatPrep(cached_data, module_icon_size, module_layout)
            combat_prep.draw_window()

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
