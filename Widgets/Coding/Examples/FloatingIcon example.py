import os

import PyImGui

from Py4GWCoreLib import Py4GW
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.IniManager import IniManager
from dataclasses import dataclass

@dataclass
class FloatingIconVars:
    MODULE_NAME: str = "Floating Icon Example"
    INI_PATH: str = "Widgets/Coding/Examples/FloatingIconExample"
    MAIN_INI_FILENAME: str = "FloatingIconExample.ini"
    FLOATING_INI_FILENAME: str = "FloatingIconExampleFloating.ini"

    MAIN_INI_KEY: str = ""
    FLOATING_INI_KEY: str = ""
    INI_INIT: bool = False
    ICON_PATH: str = os.path.join(Py4GW.Console.get_projects_path(), "python_icon_round.png")


class FloatingButtonExample:
    def __init__(self) -> None:
        self.floating_button = ImGui.FloatingIcon(
            icon_path=FloatingIconVars.ICON_PATH,
            window_id="##floating_icon_example_button",
            window_name="Floating Icon Example Toggle",
            tooltip_visible="Hide window",
            tooltip_hidden="Show window",
            toggle_ini_key=FloatingIconVars.FLOATING_INI_KEY,
            toggle_var_name="show_main_window",
            toggle_default=True,
            draw_callback=self.draw_window,
        )

    def draw_window(self) -> None:
        expanded, open_ = ImGui.BeginWithClose(
            ini_key=FloatingIconVars.MAIN_INI_KEY,
            name=FloatingIconVars.MODULE_NAME,
            p_open=self.floating_button.visible,
            flags=PyImGui.WindowFlags.NoCollapse,
        )
        self.floating_button.sync_begin_with_close(open_)

        if expanded:
            PyImGui.text("This window is controlled by the floating icon.")

        ImGui.End(FloatingIconVars.MAIN_INI_KEY)


FloatingButton: FloatingButtonExample | None = None


def _ensure_ini() -> bool:
    if FloatingIconVars.INI_INIT:
        return True

    FloatingIconVars.MAIN_INI_KEY = IniManager().ensure_key(FloatingIconVars.INI_PATH, FloatingIconVars.MAIN_INI_FILENAME)
    FloatingIconVars.FLOATING_INI_KEY = IniManager().ensure_key(FloatingIconVars.INI_PATH, FloatingIconVars.FLOATING_INI_FILENAME)
    if not FloatingIconVars.MAIN_INI_KEY or not FloatingIconVars.FLOATING_INI_KEY:
        return False

    IniManager().load_once(FloatingIconVars.MAIN_INI_KEY)
    IniManager().load_once(FloatingIconVars.FLOATING_INI_KEY)

    FloatingIconVars.INI_INIT = True
    return True


def _ensure_state() -> FloatingButtonExample:
    global FloatingButton
    if FloatingButton is None:
        FloatingButton = FloatingButtonExample()
        FloatingButton.floating_button.load_visibility()
    return FloatingButton


def main():
    try:
        if not _ensure_ini():
            return

        state = _ensure_state()
        state.floating_button.draw(FloatingIconVars.FLOATING_INI_KEY)
    except Exception as exc:
        Py4GW.Console.Log(FloatingIconVars.MODULE_NAME, f"Error: {exc}", Py4GW.Console.MessageType.Error)
        raise


if __name__ == "__main__":
    main()
