import json
import math
import os
import traceback

import Py4GW

from HeroAI.cache_data import CacheData
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import CombatPrepSkillsType
from Py4GWCoreLib import Party
from Py4GWCoreLib import Player
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import Routines
from Py4GWCoreLib import SharedCommandType


script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_directory, os.pardir))

BASE_DIR = os.path.join(project_root, "Widgets/Config")
FORMATIONS_JSON_PATH = os.path.join(BASE_DIR, "formation_hotkey.json")
MODULE_NAME = "CombatPrep"

os.makedirs(BASE_DIR, exist_ok=True)
cached_data = CacheData()


# TODO (mark): add hotkeys for formation data once hotkey support is in Py4GW
# in the meantime use https://github.com/apoguita/Py4GW/pull/153 for use at your own
# risk version with other potentially game breaking changes.
def ensure_formation_json_exists():
    if not os.path.exists(FORMATIONS_JSON_PATH):
        default_json = {
            "Flag Front": {
                "hotkey": None,
                "vk": None,
                "coordinates": [
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
                "hotkey": None,
                "vk": None,
                "coordinates": [
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
                "hotkey": None,
                "vk": None,
                "coordinates": [
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
                "hotkey": None,
                "vk": None,
                "coordinates": [
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
                "hotkey": None,
                "vk": None,
                "coordinates": [],
            },
        }
        with open(FORMATIONS_JSON_PATH, "w") as f:
            print(FORMATIONS_JSON_PATH)
            json.dump(default_json, f)  # empty dict initially


def load_formations_from_json():
    ensure_formation_json_exists()
    with open(FORMATIONS_JSON_PATH, "r") as f:
        data = json.load(f)
    return data


def draw_combat_prep_window(cached_data):
    if PyImGui.begin("Combat Prep", PyImGui.WindowFlags.AlwaysAutoResize):
        # Currently hardcode to key 5
        me = Player.GetAgentID()
        is_party_leader = Party.GetPartyLeaderID() == me
        if not GLOBAL_CACHE.Map.IsExplorable() or not is_party_leader:
            PyImGui.text("Need to be party Leader and in Explorable Area")
            return

        # capture current state
        PyImGui.is_window_collapsed()
        PyImGui.get_window_pos()

        party_size = cached_data.data.party_size
        disband_formation = False
        COORDINATES = "coordinates"

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
                PyImGui.table_next_row()

                # Column 1: Formation Button
                PyImGui.table_next_column()
                button_pressed = PyImGui.button(formation_key)
                should_set_formation = button_pressed

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

                cached_data.HeroAI_vars.shared_memory_handler.set_player_property(
                    hero_ai_index, "IsFlagged", True
                )
                cached_data.HeroAI_vars.shared_memory_handler.set_player_property(
                    hero_ai_index, "FlagPosX", final_x
                )
                cached_data.HeroAI_vars.shared_memory_handler.set_player_property(
                    hero_ai_index, "FlagPosY", final_y
                )
                cached_data.HeroAI_vars.shared_memory_handler.set_player_property(
                    hero_ai_index, "FollowAngle", leader_follow_angle
                )

        if disband_formation:
            for i in range(1, party_size):
                cached_data.HeroAI_vars.shared_memory_handler.set_player_property(
                    i, "IsFlagged", False
                )
                cached_data.HeroAI_vars.shared_memory_handler.set_player_property(
                    i, "FlagPosX", 0.0
                )
                cached_data.HeroAI_vars.shared_memory_handler.set_player_property(
                    i, "FlagPosY", 0.0
                )
                cached_data.HeroAI_vars.shared_memory_handler.set_player_property(
                    i, "FollowAngle", 0.0
                )
            GLOBAL_CACHE.Party.Heroes.UnflagHero(i)
            GLOBAL_CACHE.Party.Heroes.UnflagAllHeroes()

        PyImGui.text("Skill Prep:")
        PyImGui.separator()

        if PyImGui.begin_table("SkillPrepTable", 3):
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

            PyImGui.table_next_row()
            # Column 1: Formation Button
            PyImGui.table_next_column()
            st_button_pressed = PyImGui.button("Spirits Prep")

            sender_email = cached_data.account_email

            # Only party leader is allowed to have access to hotkey
            if is_party_leader:
                if st_button_pressed:
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
    PyImGui.end()


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
