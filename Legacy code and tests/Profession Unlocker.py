from Py4GWCoreLib import *
import time
import json

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

    def __init__(self):
        super().__init__(window_name="Profession Unlocker", window_size=(400.0, 420.0))
        self.dialog_ids = []
        self.selected_idx = -1
        self.status_log = []
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

    def log(self, msg):
        self.status_log.append(msg)
        if len(self.status_log) > 10:
            self.status_log = self.status_log[-10:]

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
                self.log(f"Warning: Not enough gold. Need {minimum}, have {gold_inv} in inventory and {gold_storage} in storage. The NPC will notify you in-game.")
                return False
            self.log(f"Withdrawing {needed} gold from storage.")
            Inventory.WithdrawGold(needed)  # or try GLOBAL_CACHE.Inventory.WithdrawGold(needed)
            return True
        except Exception as e:
            self.log(f"Error checking/withdrawing gold: {e}")
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
            self.log(f"Sent dialog ID: {dialog_id}")
        except Exception as e:
            self.log(f"Error sending dialog {dialog_id}: {e}")

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
                Map.Travel(82)
                self.log("Teleported to Great Temple of Balthazar (GToB)")
            except Exception as e:
                self.log(f"Error teleporting: {e}")
        PyImGui.separator()

    def ShowMainControls(self):
        char_name = self.get_player_name()
        PyImGui.text(f"Current Character: {char_name}")
        PyImGui.separator()
        self.ShowTeleportButton()
        self.ShowProfessionPresets()
        # Start/Pause section removed
        PyImGui.separator()
        # Status Log
        PyImGui.text("Status Log:")
        for line in self.status_log:
            PyImGui.text(line)

    def Show(self):
        if PyImGui.begin(self.name, False, int(PyImGui.WindowFlags.AlwaysAutoResize)):
            PyImGui.begin_child("Main Content", self.size, False, int(PyImGui.WindowFlags.AlwaysAutoResize))
            self.ShowMainControls()
            PyImGui.end_child()
            PyImGui.end()
        # Remove bot_running logic since Start/Pause is gone

def configure():
    pass

# Main entry for Py4GW
window = ProUnlockWindow()
def main():
    window.Show() 