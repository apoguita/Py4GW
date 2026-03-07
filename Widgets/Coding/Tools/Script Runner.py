import os

import Py4GW
import PyImGui

from Py4GWCoreLib import Color, ImGui
from Py4GWCoreLib.IniManager import IniManager


MODULE_NAME = "Script Runner"
MODULE_ICON = "Textures/Module_Icons/Template.png"
OPTIONAL = True

__widget__ = {
    "name": "Script Runner",
    "enabled": False,
    "category": "Coding",
    "subcategory": "Tools",
    "icon": "ICON_PLAY",
    "quickdock": False,
    "hidden": False,
}

INI_KEY = ""
INI_PATH = "Widgets/ScriptRunner"
INI_FILENAME = "ScriptRunner.ini"

WINDOW_OPEN = True
STATUS_TEXT = "idle"
PROJECTS_PATH = ""

SCRIPT_PATH_INPUT = ""
LOG_PATH_INPUT = ""
DELAY_MS_INPUT = 350
LOG_TAIL_LINE_COUNT = 20


def _log(message: str, level: int = None) -> None:
    if level is None:
        level = Py4GW.Console.MessageType.Info
    print(f"[{MODULE_NAME}] {message}")
    try:
        Py4GW.Console.Log(MODULE_NAME, message, level)
    except Exception:
        pass


def _default_script_path() -> str:
    base = PROJECTS_PATH or os.getcwd()
    return os.path.join(base, "native_labeled_frame_test.py")


def _default_log_path() -> str:
    base = PROJECTS_PATH or os.getcwd()
    return os.path.join(base, "native_labeled_frame_test.log")


def _add_config_vars() -> None:
    IniManager().add_str(INI_KEY, "script_path", "ScriptRunner", "script_path", _default_script_path())
    IniManager().add_str(INI_KEY, "log_path", "ScriptRunner", "log_path", _default_log_path())
    IniManager().add_int(INI_KEY, "delay_ms", "ScriptRunner", "delay_ms", DELAY_MS_INPUT)
    IniManager().add_int(INI_KEY, "log_tail_count", "ScriptRunner", "log_tail_count", LOG_TAIL_LINE_COUNT)


def _load_config() -> None:
    global SCRIPT_PATH_INPUT
    global LOG_PATH_INPUT
    global DELAY_MS_INPUT
    global LOG_TAIL_LINE_COUNT

    SCRIPT_PATH_INPUT = str(IniManager().get(INI_KEY, "script_path", _default_script_path()) or _default_script_path())
    LOG_PATH_INPUT = str(IniManager().get(INI_KEY, "log_path", _default_log_path()) or _default_log_path())
    DELAY_MS_INPUT = int(IniManager().get(INI_KEY, "delay_ms", DELAY_MS_INPUT) or DELAY_MS_INPUT)
    LOG_TAIL_LINE_COUNT = int(IniManager().get(INI_KEY, "log_tail_count", LOG_TAIL_LINE_COUNT) or LOG_TAIL_LINE_COUNT)


def _save_config() -> None:
    IniManager().set(INI_KEY, "script_path", SCRIPT_PATH_INPUT)
    IniManager().set(INI_KEY, "log_path", LOG_PATH_INPUT)
    IniManager().set(INI_KEY, "delay_ms", DELAY_MS_INPUT)
    IniManager().set(INI_KEY, "log_tail_count", LOG_TAIL_LINE_COUNT)


def _set_status(message: str) -> None:
    global STATUS_TEXT
    STATUS_TEXT = message
    _log(message)


def _safe_status() -> str:
    try:
        return str(Py4GW.Console.status())
    except Exception as exc:
        return f"status_error: {exc}"


def _normalize_existing_path(path: str) -> str:
    raw = str(path or "").strip().strip('"')
    if not raw:
        return ""
    if os.path.isabs(raw):
        return raw
    return os.path.join(PROJECTS_PATH or os.getcwd(), raw)


def _load_only() -> None:
    path = _normalize_existing_path(SCRIPT_PATH_INPUT)
    if not path or not os.path.exists(path):
        _set_status(f"script_missing: {path}")
        return
    Py4GW.Console.load(path)
    _set_status(f"loaded: {path}")


def _run_only() -> None:
    Py4GW.Console.run()
    _set_status(f"run_requested status={_safe_status()}")


def _stop_only() -> None:
    Py4GW.Console.stop()
    _set_status(f"stop_requested status={_safe_status()}")


def _defer_reload_run() -> None:
    path = _normalize_existing_path(SCRIPT_PATH_INPUT)
    if not path or not os.path.exists(path):
        _set_status(f"script_missing: {path}")
        return
    Py4GW.Console.defer_stop_load_and_run(path, max(0, int(DELAY_MS_INPUT)))
    _set_status(f"reload_run_enqueued delay_ms={DELAY_MS_INPUT}")


def _run_native_test_preset() -> None:
    global SCRIPT_PATH_INPUT
    global LOG_PATH_INPUT

    SCRIPT_PATH_INPUT = _default_script_path()
    LOG_PATH_INPUT = _default_log_path()
    _save_config()
    _defer_reload_run()


def _read_log_tail() -> list[str]:
    path = _normalize_existing_path(LOG_PATH_INPUT)
    if not path or not os.path.exists(path):
        return [f"<log missing> {path}"]
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.readlines()
        tail_count = max(1, int(LOG_TAIL_LINE_COUNT))
        return [line.rstrip("\r\n") for line in lines[-tail_count:]]
    except Exception as exc:
        return [f"<log read error> {exc}"]


def configure() -> None:
    global SCRIPT_PATH_INPUT
    global LOG_PATH_INPUT
    global DELAY_MS_INPUT
    global LOG_TAIL_LINE_COUNT

    if not PyImGui.begin(f"{MODULE_NAME} Config"):
        PyImGui.end()
        return

    PyImGui.text("Control Py4GW console script loading for rapid iteration.")
    SCRIPT_PATH_INPUT = PyImGui.input_text("Script Path", SCRIPT_PATH_INPUT, 512)
    LOG_PATH_INPUT = PyImGui.input_text("Log Path", LOG_PATH_INPUT, 512)
    DELAY_MS_INPUT = PyImGui.input_int("Reload Delay (ms)", DELAY_MS_INPUT)
    LOG_TAIL_LINE_COUNT = PyImGui.input_int("Log Tail Lines", LOG_TAIL_LINE_COUNT)

    if PyImGui.button("Save Config##script_runner"):
        _save_config()
        _set_status("config_saved")

    PyImGui.end()


def tooltip() -> None:
    PyImGui.begin_tooltip()
    title_color = Color(255, 200, 100, 255)
    PyImGui.text_colored(MODULE_NAME, title_color.to_tuple_normalized())
    PyImGui.separator()
    PyImGui.text("Loads, runs, stops, and reloads Py4GW scripts.")
    PyImGui.bullet_text("Fast reload loop for test scripts.")
    PyImGui.bullet_text("Preset for native_labeled_frame_test.py.")
    PyImGui.bullet_text("Built-in log tail viewer.")
    PyImGui.end_tooltip()


def draw_widget() -> None:
    global SCRIPT_PATH_INPUT
    global LOG_PATH_INPUT
    global DELAY_MS_INPUT
    global LOG_TAIL_LINE_COUNT

    if not ImGui.Begin(INI_KEY, MODULE_NAME, flags=PyImGui.WindowFlags.AlwaysAutoResize):
        ImGui.End(INI_KEY)
        return

    script_path = _normalize_existing_path(SCRIPT_PATH_INPUT)
    log_path = _normalize_existing_path(LOG_PATH_INPUT)

    PyImGui.text(f"Console Status: {_safe_status()}")
    PyImGui.text(f"Widget Status: {STATUS_TEXT}")
    PyImGui.separator()

    new_script = PyImGui.input_text("Script Path##script_runner", SCRIPT_PATH_INPUT, 512)
    if new_script != SCRIPT_PATH_INPUT:
        SCRIPT_PATH_INPUT = new_script
        _save_config()

    new_log = PyImGui.input_text("Log Path##script_runner", LOG_PATH_INPUT, 512)
    if new_log != LOG_PATH_INPUT:
        LOG_PATH_INPUT = new_log
        _save_config()

    new_delay = PyImGui.input_int("Reload Delay (ms)##script_runner", DELAY_MS_INPUT)
    if new_delay != DELAY_MS_INPUT:
        DELAY_MS_INPUT = max(0, int(new_delay))
        _save_config()

    new_tail_count = PyImGui.input_int("Log Tail Lines##script_runner", LOG_TAIL_LINE_COUNT)
    if new_tail_count != LOG_TAIL_LINE_COUNT:
        LOG_TAIL_LINE_COUNT = max(1, int(new_tail_count))
        _save_config()

    PyImGui.text(f"Resolved Script: {script_path}")
    PyImGui.text(f"Resolved Log: {log_path}")

    if PyImGui.button("Load##script_runner"):
        _load_only()
    if PyImGui.button("Run##script_runner"):
        _run_only()
    if PyImGui.button("Stop##script_runner"):
        _stop_only()
    if PyImGui.button("Reload + Run##script_runner"):
        _defer_reload_run()
    if PyImGui.button("Native Test Preset##script_runner"):
        _run_native_test_preset()

    PyImGui.separator()
    PyImGui.text("Native UI test hotkeys after load:")
    PyImGui.bullet_text("F6 opens DevText")
    PyImGui.bullet_text("F7 clones with CreateLabeledFrameByFrameId")

    PyImGui.separator()
    PyImGui.text("Log Tail")
    for line in _read_log_tail():
        PyImGui.text_wrapped(line)

    ImGui.End(INI_KEY)


initialized = False


def main() -> None:
    global initialized
    global INI_KEY
    global PROJECTS_PATH

    if initialized:
        draw_widget()
        return

    try:
        PROJECTS_PATH = Py4GW.Game.GetProjectsPath()
    except Exception:
        try:
            PROJECTS_PATH = Py4GW.Console.get_projects_path()
        except Exception:
            PROJECTS_PATH = os.getcwd()

    if not INI_KEY:
        INI_KEY = IniManager().ensure_key(INI_PATH, INI_FILENAME)
        if not INI_KEY:
            return
        _add_config_vars()
        IniManager().load_once(INI_KEY)
        _load_config()

    initialized = True
    draw_widget()


if __name__ == "__main__":
    main()
