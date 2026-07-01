from Py4GWCoreLib import Color, Map, PyImGui, SkillBar, Timer
from Py4GWCoreLib.Skill import clamp_skill_slot, order_interact_set_hotkey


MODULE_NAME = "Mission Temporary Skill"
MODULE_ICON = "Textures/Module_Icons/Dialogs - Nightfall.png"
MODULE_CATEGORY = "Automation"
MODULE_DESCRIPTION = "Places the offered temporary mission skill into the chosen skillbar slot."
MODULE_TAGS = ["mission", "temporary", "skill", "interaction"]

__widget__ = {
    "enabled": False,
    "category": "Automation",
    "subcategory": "Helpers",
}


VERIFY_INTERVAL_MS = 500
VERIFY_MAX_ATTEMPTS = 12


def _as_int(value, default=0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def _safe_call(func, *args, default=None):
    try:
        if callable(func):
            return func(*args)
    except Exception:
        return default
    return default


class MissionTemporarySkillWidget:
    def __init__(self):
        self.skill_slot = 6
        self.status_message = "Ready."
        self.last_debug = ""
        self.verify_timer = Timer()
        self.verifying_slot = 0
        self.verify_attempts = 0

    def slot_skill_id(self, slot: int) -> int:
        return _as_int(_safe_call(getattr(SkillBar, "GetSkillIDBySlot", None), slot, default=0))

    def take_skill(self) -> bool:
        if not Map.IsMapReady():
            self.status_message = "Map is not ready yet."
            self.last_debug = "map_ready=False"
            return False

        slot = clamp_skill_slot(self.skill_slot)
        slot_index = slot - 1
        if not order_interact_set_hotkey(slot_index):
            self.status_message = f"Could not send placement for slot {slot}."
            self.last_debug = f"native_order_hotkey_failed slot={slot} hotkey={slot_index}"
            return False

        self.verifying_slot = slot
        self.verify_attempts = 0
        self.verify_timer.Reset()
        self.verify_timer.Start()
        self.status_message = f"Placing mission skill in slot {slot}..."
        self.last_debug = f"native_order_hotkey slot={slot} hotkey={slot_index}"
        return True

    def update(self):
        if self.verifying_slot and self.verify_timer.HasElapsed(VERIFY_INTERVAL_MS):
            slot = self.verifying_slot
            self.verify_attempts += 1
            skill_id = self.slot_skill_id(slot)
            if skill_id > 0:
                self.verifying_slot = 0
                self.status_message = f"Mission skill is in slot {slot}."
                self.last_debug = f"verify_slot={slot} skill_id={skill_id} attempts={self.verify_attempts} ok=True"
            elif self.verify_attempts >= VERIFY_MAX_ATTEMPTS:
                self.verifying_slot = 0
                self.status_message = f"Slot {slot} did not receive a mission skill."
                self.last_debug = f"verify_slot={slot} skill_id={skill_id} attempts={self.verify_attempts} ok=False"
            else:
                self.status_message = f"Waiting for slot {slot} to update..."
                self.last_debug = f"verify_slot={slot} skill_id={skill_id} attempts={self.verify_attempts}"
                self.verify_timer.Reset()
                self.verify_timer.Start()
        return None

    def draw(self):
        self.update()

        if not PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
            PyImGui.end()
            return

        self.skill_slot = clamp_skill_slot(PyImGui.input_int("Slot", _as_int(self.skill_slot)))

        PyImGui.separator()
        PyImGui.text(f"Selected slot: {self.skill_slot}")

        if PyImGui.button("Take mission skill"):
            self.take_skill()

        PyImGui.separator()
        status_color = Color(0.65, 0.9, 0.7, 1.0).to_tuple_normalized()
        PyImGui.text_colored(self.status_message, status_color)

        PyImGui.end()


_widget = MissionTemporarySkillWidget()


def Draw_Window():
    _widget.draw()


def main():
    Draw_Window()


if __name__ == "__main__":
    main()
