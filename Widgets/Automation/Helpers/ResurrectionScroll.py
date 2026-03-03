# ---- REQUIRED BY WIDGET HANDLER (define immediately) ----
def configure():
    pass

def main():
    return

__all__ = ["main", "configure"]

# ---------------------------------------------------------------------------

MODULE_NAME = "Resurrection Scroll"
MODULE_ICON = "Textures/Module_Icons/Resurrection Scroll.png"

_INIT_OK = False
_INIT_ERROR = None

try:
    import Py4GW
    import os

    from Py4GWCoreLib import (
        ConsoleLog,
        Console,
        IniHandler,
        Timer,
        ThrottledTimer,
        GLOBAL_CACHE,
        ModelID,
        Map,
        Player,
        Agent,
        ImGui,
        Routines,
        Range,
    )
    from Py4GWCoreLib import PyImGui, Color

    # -----------------------------------------------------------------------
    # Config / INI
    # -----------------------------------------------------------------------
    _root = Py4GW.Console.get_projects_path()
    _ini_path = os.path.join(_root, "Widgets", "Config", "ResurrectionScroll.ini")
    os.makedirs(os.path.dirname(_ini_path), exist_ok=True)

    _ini = IniHandler(_ini_path)

    _enabled: bool = _ini.read_bool(MODULE_NAME, "enabled", True)

    # -----------------------------------------------------------------------
    # Constants
    # -----------------------------------------------------------------------
    _SCROLL_MODEL_ID = ModelID.Scroll_Of_Resurrection.value   # 26501
    _CHECK_INTERVAL_MS = 1500    # how often we poll for death
    _USE_COOLDOWN_MS   = 8000    # don't re-use within 8 s of last attempt

    # -----------------------------------------------------------------------
    # State
    # -----------------------------------------------------------------------
    _check_timer   = ThrottledTimer(_CHECK_INTERVAL_MS)
    _cooldown_timer = Timer()
    _cooldown_timer.Start()
    _on_cooldown   = False

    _status_text = ""

    # -----------------------------------------------------------------------
    # Logic
    # -----------------------------------------------------------------------
    def _tick():
        global _on_cooldown, _status_text

        if not _enabled:
            _status_text = "Disabled"
            return

        if not _check_timer.IsExpired():
            return
        _check_timer.Reset()

        if not Routines.Checks.Map.MapValid():
            _status_text = "Map invalid"
            return

        if not Map.IsExplorable():
            _status_text = "Not in explorable"
            return

        player_id = Player.GetAgentID()
        if player_id == 0:
            return

        # Can't use items while dead
        if Agent.IsDead(player_id):
            _status_text = "Player is dead"
            return

        # Check if any party member is dead nearby
        dead_ally_id = Routines.Agents.GetDeadAlly(Range.Earshot.value)
        if dead_ally_id == 0:
            _status_text = "All alive"
            _on_cooldown = False
            return

        # A party member is dead — check cooldown
        if _on_cooldown and not _cooldown_timer.HasElapsed(_USE_COOLDOWN_MS):
            _status_text = "Dead party member — waiting cooldown"
            return

        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(_SCROLL_MODEL_ID)
        if item_id == 0:
            _status_text = "Dead party member — no scroll in inventory"
            return

        ConsoleLog(MODULE_NAME, "Party member dead, using Scroll of Resurrection", Console.MessageType.Info)
        GLOBAL_CACHE.Inventory.UseItem(item_id)
        _on_cooldown = True
        _cooldown_timer.Reset()
        _status_text = "Used scroll!"

    # -----------------------------------------------------------------------
    # Config window
    # -----------------------------------------------------------------------
    _config_module = ImGui.WindowModule(
        f"{MODULE_NAME} Config",
        window_name=f"{MODULE_NAME} Config##{MODULE_NAME}",
        window_size=(220, 80),
        window_flags=PyImGui.WindowFlags.AlwaysAutoResize,
    )
    _cx = _ini.read_int(MODULE_NAME + " Config", "x", 100)
    _cy = _ini.read_int(MODULE_NAME + " Config", "y", 100)
    _config_module.window_pos = (_cx, _cy)

    _INIT_OK = True

except Exception as _e:
    _INIT_ERROR = _e


# ---------------------------------------------------------------------------
# Widget entry points
# ---------------------------------------------------------------------------
def configure():
    global _enabled, _config_module, _ini, _status_text
    if not _INIT_OK:
        return

    try:
        if _config_module.first_run:
            PyImGui.set_next_window_size(*_config_module.window_size)
            PyImGui.set_next_window_pos(*_config_module.window_pos)
            _config_module.first_run = False

        if PyImGui.begin(_config_module.window_name, _config_module.window_flags):
            changed, new_val = PyImGui.checkbox("Enable auto-use", _enabled)
            if changed:
                _enabled = new_val
                _ini.write_key(MODULE_NAME, "enabled", str(_enabled))

            PyImGui.spacing()
            PyImGui.text(f"Status: {_status_text}")

            pos = PyImGui.get_window_pos()
            if pos != _config_module.window_pos:
                _config_module.window_pos = (int(pos[0]), int(pos[1]))
                _ini.write_key(MODULE_NAME + " Config", "x", str(int(pos[0])))
                _ini.write_key(MODULE_NAME + " Config", "y", str(int(pos[1])))

        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"configure error: {e}", Py4GW.Console.MessageType.Error)


def tooltip():
    if not _INIT_OK:
        return
    PyImGui.begin_tooltip()
    title_color = Color(255, 200, 100, 255).to_tuple_normalized()
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(MODULE_NAME, title_color)
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.text("Automatically uses a Scroll of Resurrection")
    PyImGui.text("from inventory when the player dies in an")
    PyImGui.text("explorable area.")
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()
    PyImGui.text_colored("Credits:", title_color)
    PyImGui.bullet_text("Developed by Wick Divinus")
    PyImGui.end_tooltip()


def main():
    if not _INIT_OK:
        return
    try:
        _tick()
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"main error: {e}", Py4GW.Console.MessageType.Error)
