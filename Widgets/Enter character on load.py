from Py4GWCoreLib import Timer
from Py4GWCoreLib import UIManager
from Py4GWCoreLib import Keystroke
from Py4GWCoreLib import Key
from Py4GWCoreLib import IniManager
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib.Context import GWContext

module_name = "Enter character on load"

play_button_hash = 184818986
loading_in_character_screen = True

start_timer = Timer()
start_timer.Start()

INI_KEY = ""
INI_INIT = False


def _ensure_ini() -> bool:
    global INI_KEY, INI_INIT
    if INI_INIT:
        return True

    INI_KEY = IniManager().ensure_global_key(
        "Widgets/EnterCharacterOnLoad",
        "EnterCharacterOnLoad.ini"
    )

    if not INI_KEY:
        ConsoleLog(module_name, "INI global key creation FAILED (INI_KEY empty).")
        return False

    # FORCE: ensure node has at least 1 var, then save once (this stages writes)
    IniManager().add_bool(INI_KEY, "init", "Window config", "init", default=True)
    IniManager().load_once(INI_KEY)
    IniManager().set(INI_KEY, "init", True)
    IniManager().save_vars(INI_KEY)

    ConsoleLog(module_name, f"INI global key OK: {INI_KEY}")
    INI_INIT = True
    return True


def main():
    global loading_in_character_screen, start_timer, play_button_hash

    _ensure_ini()

    if start_timer.IsStopped():
        return

    if (pregame_ctx := GWContext.PreGame.GetContext()) is None:
        return

    if start_timer.HasElapsed(1000) and loading_in_character_screen:
        frame_id = UIManager.GetFrameIDByHash(play_button_hash)
        if UIManager.FrameExists(frame_id):
            ConsoleLog(module_name, "Entering Game.")
            Keystroke.PressAndRelease(Key.Enter.value)

        loading_in_character_screen = False
        start_timer.Stop()

    if start_timer.HasElapsed(1500):
        loading_in_character_screen = False
        start_timer.Stop()


def configure():
    pass


if __name__ == "__main__":
    main()
