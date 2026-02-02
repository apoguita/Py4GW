import os
import traceback

import Py4GW  # type: ignore
from HeroAI.cache_data import CacheData
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import PyImGui, Color, ImGui
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Timer, Player

script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = Py4GW.Console.get_projects_path()

first_run = True

BASE_DIR = os.path.join(project_root, "Widgets/Config")
INI_WIDGET_WINDOW_PATH = os.path.join(BASE_DIR, "cantha_dialog_sender.ini")
os.makedirs(BASE_DIR, exist_ok=True)

cached_data = CacheData()

# ——— Window Persistence Setup ———
ini_window = IniHandler(INI_WIDGET_WINDOW_PATH)
save_window_timer = Timer()
save_window_timer.Start()

# String consts
MODULE_NAME = "CanthaDialogSender"  # Change this Module name
COLLAPSED = "collapsed"
X_POS = "x"
Y_POS = "y"

# load last‐saved window state (fallback to 100,100 / un-collapsed)
window_x = ini_window.read_int(MODULE_NAME, X_POS, 100)
window_y = ini_window.read_int(MODULE_NAME, Y_POS, 100)
window_collapsed = ini_window.read_bool(MODULE_NAME, COLLAPSED, False)

# Full structured dialog GUI for Guild Wars: Cantha quests
DIALOG_GROUPS = {
    "Choose Secondary Profession": {
        "dialogs": [
            (0x813D0B, "Warrior"),
            (0x813D0F, "Ranger"),
            (0x813D0D, "Monk"),
            (0x813D0C, "Necromancer"),
            (0x813D0E, "Mesmer"),
            (0x813D09, "Elementalist"),
            (0x813D08, "Assassin"),
            (0x813D0A, "Ritualist"),
        ],
        "note": (
            "After entering Linnok Courtyard, send one of these dialogs to Master Togo to choose your "
            "secondary and skip the tutorial quests. Recommended: Assassin for Dash. "
            "Game may crash when sending these; restarting Guild Wars lets you continue as if it worked."
        ),
    },
    "A Formal Introduction": {
        "note": "After selecting your secondary profession and restarting (if crash occurs), take this quest from Master Togo."
    },
    "Minister Cho's Estate Entry": {
        "dialogs": [(0x80000B, "Guardsman Kayao")],
        "note": "Zone back into Shing Jea Monastery and run to the estate. Use /bonus and equip the bow, shield, and summoning stone before entering.",
    },
    "Minister Cho's Estate": {"note": "Mission run with Taya, Lukas, and Aeson. Complete it fully."},
    "Warning the Tengu": {"note": "Quest to complete after Cho’s Estate. Bring Taya, Lukas, and Aeson."},
    "The Threat Grows": {"note": "Another post-Cho’s Estate quest. Use the same party: Taya, Lukas, Aeson."},
    "Journey to the Master": {"note": "Still part of the early quest chain. Use Taya, Lukas, and Aeson."},
    "The Road Less Traveled": {
        "note": (
            "This quest kicks non-Factions characters and heroes. Use cupcakes, apples, and war supplies "
            "to speed run to Seitung Harbor. Or use follower plugin to auto-follow Brother Pe Wan."
        )
    },
    "Zen Daijun Entry": {
        "dialogs": [(0x80000B, "Brother Hanjui")],
        "note": "Run to Zen Daijun from Seitung Harbor. Avoid Afflicted Mesmers. Use party: Taya, Lukas, Kisai, Yuun, Aeson.",
    },
    "Zen Daijun Mission": {
        "note": (
            "Bring Kai Ying, Talon Silverwing, Sister Tai, Su, and Professor Gai. "
            "Be cautious near Afflicted Yijo. Avoid Spirit Rift wipes by flagging heroes out."
        )
    },
    "Travel to Kaineng Docks": {"note": "Talk to First Mate Xiang in Seitung Harbor to sail to Kaineng."},
    "Travel to Kaineng Center": {
        "note": (
            "Run through The Marketplace to Kaineng Center. Take Headmaster Vhang, Lo Sha, Su, Kai Ying, Sister Tai, "
            "Talon Silverwing, and Professor Gai. Flag henchmen on one Afflicted group and run past."
        )
    },
    "Vizunah Square foreign": {
        "dialogs": [(0x800009, "NPC at the entrance of Vizunah Square (Foreign)")],
        "note": (
            "Make sure you have one character in team that has the quest Welcome to Cantha uncompleted in the quest log. "
            "Run from The Marketplace to Vizunah Square foreign Center."
        )
    },
    "Sunspears in Cantha": {
        "note": ("Take this quest from Imperial Guardsman Linro in Kaineng Center to spawn Kormir in Bejunkan Pier.")
    },
    "Kormir in Bejunkan Pier": {
        "dialogs": [(0x84, "Kormir")],
        "note": "Send dialog 0x84 to Kormir to progress the Sunspears quest.",
    },
    "Eternal Forgemaster": {
        "dialogs": [
            (0x07F, 'FOW Armor'),
        ],
        "note": "No need to do all the quests, just make sure the forgemaster",
    },
    "GTOB Professions": {
        "dialogs": [
            (0x0184, 'Warrior'),
            (0x0284, 'Ranger'),
            (0x0384, 'Monk'),
            (0x0484, 'Necromancer'),
            (0x0584, 'Mesmer'),
            (0x0684, 'Elementalist'),
            (0x0784, 'Assassin'),
            (0x0884, 'Ritualist'),
            (0x0984, 'Paragon'),
            (0x0A84, 'Dervish'),
        ],
        "note": "Travel to GTOB. Talk to the professions changer, make sure you have enough gold.",
    },
}


def draw_widget():
    global window_x, window_y, window_collapsed, first_run

    is_window_opened = PyImGui.begin("Cantha Quest Dialogs", PyImGui.WindowFlags.AlwaysAutoResize)
    if is_window_opened:
        group_names = list(DIALOG_GROUPS.keys())
        groups_per_tabbar = 5

        for i in range(0, len(group_names), groups_per_tabbar):
            PyImGui.spacing()
            PyImGui.separator()
            PyImGui.spacing()

            tabbar_id = f"tabbar_{i // groups_per_tabbar}"
            if PyImGui.begin_tab_bar(tabbar_id):
                for group_name in group_names[i : i + groups_per_tabbar]:
                    group_data = DIALOG_GROUPS[group_name]
                    if PyImGui.begin_tab_item(group_name):
                        dialogs = group_data.get("dialogs", [])
                        note = group_data.get("note", "")

                        for dialog_id, label in dialogs:
                            button_label = f"{label} [0x{dialog_id:X}]"
                            if PyImGui.button(button_label):
                                Player.SendDialog(dialog_id)

                        if note:
                            PyImGui.spacing()
                            PyImGui.text_wrapped(f"Note: {note}")
                            PyImGui.spacing()

                        PyImGui.end_tab_item()
                PyImGui.end_tab_bar()
            PyImGui.spacing()
            PyImGui.separator()
            PyImGui.spacing()

    PyImGui.end()


def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("CanthaDialogSender", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("An automation utility for the Guild Wars: Factions (Cantha) campaign.")
    PyImGui.text("This widget provides a structured interface to send quest-specific")
    PyImGui.text("dialog IDs, facilitating mission skips and rapid campaign progression.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Tutorial Skips: Instantly select secondary professions to bypass early quests")
    PyImGui.bullet_text("Mission Automation: Direct dialog triggers for key NPCs like Master Togo and Kormir")
    PyImGui.bullet_text("Speedrun Notes: Integrated tactical advice for missions and zone transitions")
    PyImGui.bullet_text("GTOB Utilities: One-click secondary profession unlocking at Great Temple of Balthazar")
    PyImGui.bullet_text("Categorized Navigation: Sequential tabs covering the journey from Shing Jea to Kaineng")
    PyImGui.bullet_text("Armor Access: Shortcuts for high-end services like the Eternal Forgemaster")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Mark")
    PyImGui.bullet_text("Contributors: Wick-Divinus")

    PyImGui.end_tooltip()


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
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(MODULE_NAME, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass


if __name__ == "__main__":
    main()
