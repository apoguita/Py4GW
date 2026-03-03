from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import GWContext, PyImGui, UIManager
from Py4GWCoreLib import PyItem
import Py4GW

import PyImGui

from native_ui_canvas_test import TEST_LABEL

def _open_devtext_window() -> None:
    try:
        context = GWContext.Char.GetContext()
        if context is None:
            return
        player_flags_before = int(context.player_flags)
        context.player_flags = player_flags_before | 0x8
        UIManager.Keypress(0x25, 0)
        context.player_flags = player_flags_before
    except Exception as exc:
        pass


def _create_text():
    parent_id = UIManager.GetFrameIDByLabel("DevText")
    frame_id = UIManager.CreateTextLabelFrameByFrameId(
            parent_id, 0, 99, "", "Py4GW DevText Window"
        )
    print ("Created text label with frame ID:", frame_id)

def draw_window():
    global item_id, item_name
    if PyImGui.begin("quest data"):
        if PyImGui.button("open devtext window"):
            Py4GW.Game.enqueue(_open_devtext_window)
            
        if PyImGui.button("create text label"):
            Py4GW.Game.enqueue(_create_text)

        PyImGui.end()

def main():
    draw_window()


if __name__ == "__main__":
    main()