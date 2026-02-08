import PyImGui

import PyCallback
from enum import IntEnum
from Py4GWCoreLib import ImGui, Color

# Matches: using CallbackId = uint64_t
class Phase(IntEnum):
    PreUpdate = 0
    Data = 1
    Update = 2
def draw_window():
    callback_list = PyCallback.PyCallback.GetCallbackInfo()

    # phase -> list[(id, name, phase, priority, order)]
    phases: dict[int, list[tuple]] = {
        Phase.PreUpdate: [],
        Phase.Data: [],
        Phase.Update: [],
    }

    # segment
    for cb in callback_list:
        cb_id, cb_name, cb_phase, cb_priority, cb_order = cb
        phases.setdefault(cb_phase, []).append(cb)

    # order inside each phase
    for phase in phases:
        phases[phase].sort(key=lambda c: (c[3], c[4]))  # priority, order

    phase_names = {
        Phase.PreUpdate: "PreUpdate",
        Phase.Data: "Data",
        Phase.Update: "Update",
    }

    if PyImGui.begin("Callback Debug"):
        for phase, name in phase_names.items():
            callbacks = phases.get(phase, [])
            if not callbacks:
                PyImGui.text(f"No callbacks in phase: {name}")
                continue

            if PyImGui.collapsing_header(f"{name} ({len(callbacks)})"):
                for cb_id, cb_name, cb_phase, cb_priority, cb_order in callbacks:
                    PyImGui.text(
                        f"[{cb_priority:02}] #{cb_order:03}  {cb_name}  (id={cb_id})"
                    )

        PyImGui.end()
        
def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Frame Callback Monitor", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("A low-level debugging utility for monitoring the Py4GW engine.")
    PyImGui.text("It visualizes the internal execution order of scripts and engine")
    PyImGui.text("callbacks across the different update phases of the game frame.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Phase Tracking: Categorizes callbacks into PreUpdate, Data, and Update phases")
    PyImGui.bullet_text("Priority Visualization: Displays execution order based on priority and ID")
    PyImGui.bullet_text("Real-time Metrics: Shows the number of active callbacks per phase")
    PyImGui.bullet_text("Deep Inspection: Identifies specific scripts by name to find performance bottlenecks")
    PyImGui.bullet_text("UI Organization: Uses collapsing headers to keep the debug view manageable")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")


    PyImGui.end_tooltip()


def main():
    draw_window()

if __name__ == "__main__":
    main()
