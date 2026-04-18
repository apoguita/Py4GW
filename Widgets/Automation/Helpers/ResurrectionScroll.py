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
        Party,
        SkillBar,
        Skill,
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
    _skip_if_res_available: bool = _ini.read_bool(MODULE_NAME, "skip_if_res_available", False)

    # -----------------------------------------------------------------------
    # Constants
    # -----------------------------------------------------------------------
    _SCROLL_MODEL_ID = ModelID.Scroll_Of_Resurrection.value   # 26501
    _CHECK_INTERVAL_MS = 1500    # how often we poll for death
    _USE_COOLDOWN_MS   = 8000    # don't re-use within 8 s of last attempt

    # Known resurrection skills: id -> lowercase name
    _RES_SKILLS = {
        2:    "resurrection signet",
        52:   "rebirth",
        58:   "restore life",
        247:  "resurrection chant",
        509:  "we shall return!",
        878:  "flesh of my flesh",
        894:  "death pact signet",
        1180: "lively was naomei",
        1264: "sunspear rebirth signet",
        1778: "signet of return",
    }
    _RES_SKILL_IDS   = set(_RES_SKILLS.keys())
    _RES_SKILL_NAMES = set(_RES_SKILLS.values())
    # -----------------------------------------------------------------------
    _check_timer   = ThrottledTimer(_CHECK_INTERVAL_MS)
    _cooldown_timer = Timer()
    _cooldown_timer.Start()
    _on_cooldown   = False

    _status_text = ""

    # Cache: list of (agent_id, name, skill_name) for party members with res skills
    _res_cache = []        # type: list[tuple[int, str, str]]
    _cache_built = False
    _last_was_explorable = False
    _explorable_entry_timer = Timer()
    _CACHE_DELAY_MS = 8000  # wait 8 seconds after map ready before scanning skillbars

    # -----------------------------------------------------------------------
    # Logic
    # -----------------------------------------------------------------------
    def _build_res_cache():
        """Scan all party player skillbars once (via shared memory) and cache who has a res skill."""
        global _res_cache, _cache_built
        _res_cache = []

        # Check local player
        player_id = Player.GetAgentID()
        if player_id != 0:
            try:
                player_skills = SkillBar.GetSkillbar()  # list[int]
                player_name = Agent.GetNameByID(player_id) or "Player"

                if not player_skills:
                    ConsoleLog(MODULE_NAME, f"[Cache] {player_name}: skillbar empty (not loaded yet?)", Console.MessageType.Warning, log=False)
                    return  # skillbar not loaded yet — retry next tick

                skill_info = [(sid, Skill.GetNameFromWiki(sid)) for sid in player_skills]
                ConsoleLog(MODULE_NAME, f"[Cache] {player_name} skills: {skill_info}", Console.MessageType.Info, log=False)

                for skill_id in player_skills:
                    skill_name = Skill.GetNameFromWiki(skill_id)
                    if skill_id in _RES_SKILL_IDS or skill_name.lower() in _RES_SKILL_NAMES:
                        _res_cache.append((player_id, player_name, skill_name))
                        ConsoleLog(MODULE_NAME, f"[Cache] {player_name} has res skill '{skill_name}' (id {skill_id})", Console.MessageType.Info, log=False)
                        break
            except Exception as e:
                ConsoleLog(MODULE_NAME, f"[Cache] Error reading local skillbar: {e}", Console.MessageType.Error)
                return  # retry next tick

        # Check other accounts via shared memory
        try:
            all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            my_agent_id = player_id
            for acc in all_accounts:
                acc_agent_id = acc.AgentData.AgentID
                if acc_agent_id == 0 or acc_agent_id == my_agent_id:
                    continue
                char_name = acc.AgentData.CharacterName or acc.AccountEmail or "Account"

                acc_skill_ids = [int(s.Id) for s in acc.AgentData.Skillbar.Skills if int(s.Id) != 0]
                if not acc_skill_ids:
                    ConsoleLog(MODULE_NAME, f"[Cache] {char_name}: shared memory skillbar empty (not synced yet?)", Console.MessageType.Warning, log=False)
                    return  # shared memory skillbar not synced yet — retry next tick

                acc_skill_info = [(sid, Skill.GetNameFromWiki(sid)) for sid in acc_skill_ids]
                ConsoleLog(MODULE_NAME, f"[Cache] {char_name} skills: {acc_skill_info}", Console.MessageType.Info, log=False)

                for sid in acc_skill_ids:
                    skill_name = Skill.GetNameFromWiki(sid)
                    if sid in _RES_SKILL_IDS or skill_name.lower() in _RES_SKILL_NAMES:
                        _res_cache.append((acc_agent_id, char_name, skill_name))
                        ConsoleLog(MODULE_NAME, f"[Cache] {char_name} has res skill '{skill_name}' (id {sid})", Console.MessageType.Info, log=False)
                        break
        except Exception as e:
            ConsoleLog(MODULE_NAME, f"[Cache] Error reading shared memory: {e}", Console.MessageType.Error)
            return  # retry next tick

        if not _res_cache:
            ConsoleLog(MODULE_NAME, "[Cache] No party members have a res skill equipped", Console.MessageType.Info)
        else:
            ConsoleLog(MODULE_NAME, f"[Cache] {len(_res_cache)} party member(s) with res skills cached", Console.MessageType.Info)

        _cache_built = True

    def _alive_party_member_has_res_skill():
        """Check if any cached res-skill holder is currently alive."""
        for agent_id, name, skill_name in _res_cache:
            if agent_id == 0:
                continue
            try:
                if Agent.IsValid(agent_id) and not Agent.IsDead(agent_id):
                    return True
            except Exception:
                pass
        return False

    def _tick():
        global _on_cooldown, _status_text, _cache_built, _last_was_explorable

        if not _enabled:
            _status_text = "Disabled"
            return

        if not _check_timer.IsExpired():
            return
        _check_timer.Reset()

        if not Routines.Checks.Map.MapValid():
            _status_text = "Map invalid"
            _cache_built = False
            _last_was_explorable = False
            return

        is_explorable = Map.IsExplorable()

        # Invalidate cache when leaving explorable
        if not is_explorable:
            _status_text = "Not in explorable"
            _cache_built = False
            _last_was_explorable = False
            return

        # Build cache once on explorable entry (only needed when skip feature is on)
        if _skip_if_res_available and not _cache_built and is_explorable:
            if Routines.Checks.Map.IsMapReady() and Routines.Checks.Party.IsPartyLoaded():
                if not _last_was_explorable:
                    # First tick in explorable — start the delay timer
                    _explorable_entry_timer.Reset()
                    _last_was_explorable = True
                    _status_text = "Waiting for skillbars to load..."
                    return
                if not _explorable_entry_timer.HasElapsed(_CACHE_DELAY_MS):
                    _status_text = "Waiting for skillbars to load..."
                    return
                _build_res_cache()

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

        # Skip scroll if an alive player/hero has a res skill
        if _skip_if_res_available and _alive_party_member_has_res_skill():
            _status_text = "Dead party member — res skill available"
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
    global _enabled, _skip_if_res_available, _config_module, _ini, _status_text, _cache_built
    if not _INIT_OK:
        return

    try:
        if _config_module.first_run:
            PyImGui.set_next_window_size(*_config_module.window_size)
            PyImGui.set_next_window_pos(*_config_module.window_pos)
            _config_module.first_run = False

        if PyImGui.begin(_config_module.window_name, _config_module.window_flags):
            new_enabled = PyImGui.checkbox("Enable auto-use", _enabled)
            if new_enabled != _enabled:
                _enabled = new_enabled
                _ini.write_key(MODULE_NAME, "enabled", str(_enabled))

            new_skip = PyImGui.checkbox("Skip if res skill available", _skip_if_res_available)
            if new_skip != _skip_if_res_available:
                _skip_if_res_available = new_skip
                _ini.write_key(MODULE_NAME, "skip_if_res_available", str(_skip_if_res_available))

            PyImGui.spacing()
            PyImGui.text(f"Status: {_status_text}")

            # Show cached res-skill holders
            if _res_cache:
                PyImGui.spacing()
                PyImGui.text("Res skill holders:")
                for agent_id, name, skill_name in _res_cache:
                    alive = ""
                    try:
                        alive = "alive" if Agent.IsValid(agent_id) and not Agent.IsDead(agent_id) else "dead"
                    except Exception:
                        alive = "?"
                    PyImGui.bullet_text(f"{name}: {skill_name} ({alive})")

            PyImGui.spacing()
            if PyImGui.button("Rebuild cache"):
                _cache_built = False

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
