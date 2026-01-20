import PyImGui

import PyCallback
from enum import IntEnum

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


def main():
    draw_window()

if __name__ == "__main__":
    main()
