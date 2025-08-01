from Py4GWCoreLib import *
import time
import json
from Py4GWCoreLib import ImGui

# If you have a BasicWindow class, import it. Otherwise, define a minimal one here.
try:
    from WindowUtilites import BasicWindow
except ImportError:
    class BasicWindow:
        def __init__(self, window_name="Basic Window", window_size=(350.0, 400.0)):
            self.name = window_name
            self.size = window_size
        def Show(self):
            pass

class ProUnlockWindow(BasicWindow):
    PROFESSION_PRESETS = [
        ("Mesmer", "0x585"),
        ("Necromancer", "0x485"),
        ("Elementalist", "0x685"),
        ("Monk", "0x385"),
        ("Warrior", "0x185"),
        ("Ranger", "0x285"),
        ("Ritualist", "0x885"),
        ("Paragon", "0x985"),
        ("Assassin", "0x785"),
        ("Dervish", "0xA85"),
    ]

    PROFESSION_ICON_MAP = {
        "Warrior": "Textures/Profession_Icons/[1] - Warrior.png",
        "Ranger": "Textures/Profession_Icons/[2] - Ranger.png",
        "Monk": "Textures/Profession_Icons/[3] - Monk.png",
        "Necromancer": "Textures/Profession_Icons/[4] - Necromancer.png",
        "Mesmer": "Textures/Profession_Icons/[5] - Mesmer.png",
        "Elementalist": "Textures/Profession_Icons/[6] - Elementalist.png",
        "Assassin": "Textures/Profession_Icons/[7] - Assassin.png",
        "Ritualist": "Textures/Profession_Icons/[8] - Ritualist.png",
        "Paragon": "Textures/Profession_Icons/[9] - Paragon.png",
        "Dervish": "Textures/Profession_Icons/[10] - Dervish.png",
    }

    def __init__(self):
        super().__init__(window_name="Profession Unlocker", window_size=(400.0, 420.0))
        self.dialog_ids = []
        self.selected_idx = -1
        self.bot_running = False
        self.bot_initialized = False
        self.input_dialog_id = ""
        self.last_action_time = 0
        self.pause_requested = False
        self.save_load_path = ""
        self.cached_character_name = None
        self.requested_name = False
        self.last_agent_id = None
        self.selected_profession_idx = 0

    def get_player_name(self):
        try:
            agent_id = Player.GetAgentID()
            if agent_id != self.last_agent_id:
                self.cached_character_name = None
                self.requested_name = False
                self.last_agent_id = agent_id
            if not self.requested_name:
                Agent.RequestName(agent_id)
                self.requested_name = True
            if Agent.IsNameReady(agent_id):
                self.cached_character_name = Agent.GetName(agent_id)
            return self.cached_character_name if self.cached_character_name else "(loading...)"
        except Exception:
            return "(unknown)"

    def ensure_minimum_gold(self, minimum=4500):
        try:
            gold_inv = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
            gold_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()
            if gold_inv >= minimum:
                return True
            needed = minimum - gold_inv
            if gold_inv + gold_storage < minimum:
                pass
            Inventory.WithdrawGold(needed)  # or try GLOBAL_CACHE.Inventory.WithdrawGold(needed)
            return True
        except Exception as e:
            pass
            return False

    def send_dialog(self, dialog_id):
        # Ensure at least 4500 gold before profession change, but do not abort if not enough
        self.ensure_minimum_gold(4500)
        try:
            if isinstance(dialog_id, str):
                if dialog_id.startswith('0x') or dialog_id.startswith('0X'):
                    value = int(dialog_id, 16)
                else:
                    value = int(dialog_id)
            else:
                value = int(dialog_id)
            Player.SendDialog(value)
            pass
        except Exception as e:
            pass

    def ShowProfessionPresets(self):
        PyImGui.text("Select Profession:")
        profession_names = [name for name, _ in self.PROFESSION_PRESETS]
        self.selected_profession_idx = PyImGui.combo("Profession", self.selected_profession_idx, profession_names)
        if PyImGui.button("Change Profession"):
            _, dialog_id = self.PROFESSION_PRESETS[self.selected_profession_idx]
            self.send_dialog(dialog_id)
        PyImGui.separator()

    def ShowTeleportButton(self):
        if PyImGui.button("Teleport to GToB"):
            try:
                Map.Travel(248)  # Corrected map ID for Great Temple Of Balthazar
                pass
            except Exception as e:
                pass
        PyImGui.separator()

    def ShowMainControls(self):
        profession_name = self.PROFESSION_PRESETS[self.selected_profession_idx][0]
        icon_path = self.PROFESSION_ICON_MAP.get(profession_name)
        window_width = PyImGui.get_window_width()
        window_height = PyImGui.get_window_height()
        # Make the icon even larger, up to 100% of the window size, max 750px
        icon_size = max(64, min(int(min(window_width, window_height) * 1.0), 750))
        if icon_path:
            content_pos = PyImGui.get_cursor_screen_pos()
            x = content_pos[0] + (window_width - icon_size) // 2
            y = content_pos[1] + (window_height - icon_size) // 2
            ImGui.DrawTextureInDrawList((x, y), (icon_size, icon_size), icon_path)
        char_name = self.get_player_name()
        PyImGui.text(f"Current Character: {char_name}")
        PyImGui.separator()
        self.ShowTeleportButton()
        self.ShowProfessionPresets()
        # Start/Pause section removed
        PyImGui.separator()
        # Powered by Py4GW badge at the bottom
        badge_path = "Textures/Game UI/powered_by_py4gw.png"
        badge_width = max(120, min(int(window_width * 0.4), 400))
        badge_height = int(badge_width * (48 / 270))
        x_offset = max((window_width - badge_width) // 2, 0)
        remaining_height = PyImGui.get_window_height() - PyImGui.get_cursor_pos_y() - badge_height - 8
        if remaining_height > 0:
            PyImGui.dummy(0, int(remaining_height))
        PyImGui.set_cursor_pos_x(x_offset)
        ImGui.DrawTexture(badge_path, badge_width, badge_height)

    def get_profession_color(self, profession):
        color = ColorPalette.GetColor("Gray")
        if profession == "Warrior":
            color = ColorPalette.GetColor("GW_Warrior")
        elif profession == "Ranger":
            color = ColorPalette.GetColor("GW_Ranger")
        elif profession == "Monk":
            color = ColorPalette.GetColor("GW_Monk")
        elif profession == "Necromancer":
            color = ColorPalette.GetColor("GW_Necromancer")
        elif profession == "Mesmer":
            color = ColorPalette.GetColor("GW_Mesmer")
        elif profession == "Elementalist":
            color = ColorPalette.GetColor("GW_Elementalist")
        elif profession == "Assassin":
            color = ColorPalette.GetColor("GW_Assassin")
        elif profession == "Ritualist":
            color = ColorPalette.GetColor("GW_Ritualist")
        elif profession == "Paragon":
            color = ColorPalette.GetColor("GW_Paragon")
        elif profession == "Dervish":
            color = ColorPalette.GetColor("GW_Dervish")
        faded_color = Color(color.r, color.g, color.b, 75)  # More subtle alpha
        return color, faded_color

    def Show(self):
        # Make the window resizable (remove AlwaysAutoResize)
        flags = int(PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.NoCollapse)
        profession_name = self.PROFESSION_PRESETS[self.selected_profession_idx][0]
        _, faded_color = self.get_profession_color(profession_name)
        PyImGui.push_style_color(PyImGui.ImGuiCol.WindowBg, faded_color.to_tuple_normalized())
        if PyImGui.begin(self.name, False, flags):
            self.ShowMainControls()
            PyImGui.end()
        PyImGui.pop_style_color(1)


def configure():
    pass

# Main entry for Py4GW
window = ProUnlockWindow()
def main():
    window.Show() 
