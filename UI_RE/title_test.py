"""
Title test — uses custom proc during msg 0x09 (FrameCreate lifecycle).
"""
import PyImGui
import PyUIManager
import Py4GW

from Py4GWCoreLib import UIManager
from Py4GWCoreLib.GWUI import GWUI

window_id = 0

def main():
    global window_id

    if not PyImGui.begin("Title Test"):
        return

    if PyImGui.button("Create Window") and window_id == 0:
        window_id = int(PyUIManager.UIManager.create_titled_container_window(
            100, 100, 400, 300,
            title="Py4GW Test",
            parent_frame_id=9,
            child_index=0,
            frame_flags=0x20,
            anchor_flags=0x6,
            subclass_flags=0x59,
        ) or 0)
        label = UIManager.GetFrameLabel(window_id)
        print(f"[CREATE] id={window_id} label='{label}'")

    PyImGui.same_line(0.0, 8.0)
    PyImGui.text(f"id={window_id}")

    if PyImGui.button("Snapshot") and window_id != 0:
        label = UIManager.GetFrameLabel(window_id)
        title_text = UIManager.GetFrameTitleText(window_id)
        print(f"[SNAP] id={window_id} label='{label}' title_text='{title_text}'")

    PyImGui.same_line(0.0, 8.0)
    if PyImGui.button("Destroy") and window_id != 0:
        GWUI.DestroyUIComponentByFrameId(window_id)
        window_id = 0

    PyImGui.end()

if __name__ == "__main__":
    main()
