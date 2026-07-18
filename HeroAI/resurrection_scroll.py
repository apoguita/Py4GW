import Py4GW
import PyImGui

from HeroAI.settings import Settings
from Py4GWCoreLib import Agent
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import Map
from Py4GWCoreLib import ModelID
from Py4GWCoreLib import Player
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines
from Py4GWCoreLib import SharedCommandType
from Py4GWCoreLib import Skill
from Py4GWCoreLib import SkillBar
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import Timer
from Py4GWCoreLib.GlobalCache.SharedMemory import AccountStruct
from Py4GWCoreLib.GlobalCache.WhiteboardLocks import claim_resurrection_target
from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
from Py4GWCoreLib.py4gwcorelib_src.Console import Console
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog

MODULE_NAME = "HeroAI Resurrection Scroll"

_SCROLL_MODEL_ID = ModelID.Scroll_Of_Resurrection.value
_CHECK_INTERVAL_MS = 1500
_USE_COOLDOWN_MS = 8000
_AFTERCAST_MS = 500
_CACHE_DELAY_MS = 8000

_RES_SKILLS = {
    2: "resurrection signet",
    52: "rebirth",
    58: "restore life",
    247: "resurrection chant",
    509: "we shall return!",
    878: "flesh of my flesh",
    894: "death pact signet",
    1180: "lively was naomei",
    1264: "sunspear rebirth signet",
    1778: "signet of return",
}
_RES_SKILL_IDS = set(_RES_SKILLS.keys())
_RES_SKILL_NAMES = set(_RES_SKILLS.values())

_settings = Settings()
_check_timer = ThrottledTimer(_CHECK_INTERVAL_MS)
_cooldown_timer = Timer()
_cooldown_timer.Start()
_aftercast_timer = Timer()
_aftercast_timer.Start()
_explorable_entry_timer = Timer()

_status_text = ""
_res_cache: list[tuple[int, str, str]] = []
_cache_built = False
_last_was_explorable = False
_on_cooldown = False


def _get_same_party_accounts() -> list[AccountStruct]:
    self_email = str(Player.GetAccountEmail() or "").strip()
    self_account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(self_email) if self_email else None
    party_id = int(getattr(getattr(self_account, "AgentPartyData", None), "PartyID", 0) or 0)

    accounts = []
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if party_id and int(getattr(getattr(account, "AgentPartyData", None), "PartyID", 0) or 0) != party_id:
            continue
        accounts.append(account)

    return sorted(
        accounts,
        key=lambda account: (
            int(getattr(getattr(account, "AgentPartyData", None), "PartyPosition", 9999) or 9999),
            str(getattr(account, "AccountEmail", "") or ""),
        ),
    )


def _build_res_cache() -> None:
    global _res_cache, _cache_built
    _res_cache = []

    player_id = Player.GetAgentID()
    if player_id != 0:
        try:
            player_skills = SkillBar.GetSkillbar()
            player_name = Agent.GetNameByID(player_id) or "Player"
            if not player_skills:
                ConsoleLog(MODULE_NAME, f"[Cache] {player_name}: skillbar empty (not loaded yet?)", Console.MessageType.Warning, log=False)
                return

            for skill_id in player_skills:
                skill_name = Skill.GetNameFromWiki(skill_id)
                if skill_id in _RES_SKILL_IDS or skill_name.lower() in _RES_SKILL_NAMES:
                    _res_cache.append((player_id, player_name, skill_name))
                    break
        except Exception as exc:
            ConsoleLog(MODULE_NAME, f"[Cache] Error reading local skillbar: {exc}", Console.MessageType.Error)
            return

    try:
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            account_agent_data = getattr(account, "AgentData", None)
            account_agent_id = int(getattr(account_agent_data, "AgentID", 0) or 0)
            if account_agent_id == 0 or account_agent_id == player_id:
                continue

            char_name = getattr(account_agent_data, "CharacterName", "") or getattr(account, "AccountEmail", "") or "Account"
            skillbar = getattr(account_agent_data, "Skillbar", None)
            skills = getattr(skillbar, "Skills", []) if skillbar is not None else []
            account_skill_ids = [int(skill.Id) for skill in skills if int(skill.Id) != 0]
            if not account_skill_ids:
                ConsoleLog(MODULE_NAME, f"[Cache] {char_name}: shared memory skillbar empty (not synced yet?)", Console.MessageType.Warning, log=False)
                return

            for skill_id in account_skill_ids:
                skill_name = Skill.GetNameFromWiki(skill_id)
                if skill_id in _RES_SKILL_IDS or skill_name.lower() in _RES_SKILL_NAMES:
                    _res_cache.append((account_agent_id, char_name, skill_name))
                    break
    except Exception as exc:
        ConsoleLog(MODULE_NAME, f"[Cache] Error reading shared memory: {exc}", Console.MessageType.Error)
        return

    if not _res_cache:
        ConsoleLog(MODULE_NAME, "[Cache] No party members have a res skill equipped", Console.MessageType.Info)
    else:
        ConsoleLog(MODULE_NAME, f"[Cache] {len(_res_cache)} party member(s) with res skills cached", Console.MessageType.Info)

    _cache_built = True


def rebuild_cache() -> None:
    global _cache_built
    _cache_built = False


def _alive_party_member_has_res_skill() -> bool:
    for agent_id, _, _ in _res_cache:
        if agent_id == 0:
            continue
        try:
            if Agent.IsValid(agent_id) and not Agent.IsDead(agent_id):
                return True
        except Exception:
            pass
    return False


def _consume_toggle_messages() -> None:
    account_email = str(Player.GetAccountEmail() or "").strip()
    if not account_email:
        return

    latest_enabled: bool | None = None
    for message_index, message in GLOBAL_CACHE.ShMem.GetAllMessages():
        if message is None or not getattr(message, "Active", False):
            continue
        if str(getattr(message, "ReceiverEmail", "") or "").strip() != account_email:
            continue
        if int(getattr(message, "Command", SharedCommandType.NoCommand)) != int(SharedCommandType.SetResurrectionScroll):
            continue

        latest_enabled = bool(int(getattr(message, "Params", (1, 0, 0, 0))[0] or 0))
        GLOBAL_CACHE.ShMem.MarkMessageAsFinished(account_email, message_index)

    if latest_enabled is not None:
        _settings.set_account_resurrection_scroll_enabled(latest_enabled, account_email)
        ConsoleLog(
            "HeroAI",
            f"Resurrection Scroll {'enabled' if latest_enabled else 'disabled'} for {account_email}",
            Py4GW.Console.MessageType.Info,
        )


def is_enabled(account_email: str | None = None) -> bool:
    return _settings.get_account_resurrection_scroll_enabled(account_email)


def are_all_party_accounts_enabled() -> bool:
    accounts = _get_same_party_accounts()
    if not accounts:
        return is_enabled()
    return all(is_enabled(account.AccountEmail) for account in accounts)


def toggle_all_accounts() -> bool:
    sender_email = str(Player.GetAccountEmail() or "").strip()
    if not sender_email:
        return False

    accounts = _get_same_party_accounts()
    if not accounts:
        return False

    new_enabled = not all(is_enabled(account.AccountEmail) for account in accounts)
    for account in accounts:
        GLOBAL_CACHE.ShMem.SendMessage(
            sender_email,
            account.AccountEmail,
            SharedCommandType.SetResurrectionScroll,
            (1 if new_enabled else 0, 0, 0, 0),
        )

    ConsoleLog(
        "HeroAI",
        f"Resurrection Scroll {'enabled' if new_enabled else 'disabled'} for all accounts",
        Py4GW.Console.MessageType.Info,
    )
    return new_enabled


def tick() -> None:
    global _on_cooldown, _status_text, _cache_built, _last_was_explorable

    _settings.ensure_initialized()
    _consume_toggle_messages()

    if not is_enabled():
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

    if not Map.IsExplorable():
        _status_text = "Not in explorable"
        _cache_built = False
        _last_was_explorable = False
        return

    skip_if_res_available = _settings.get_account_resurrection_scroll_skip_if_res_available()
    if skip_if_res_available and not _cache_built:
        if Routines.Checks.Map.IsMapReady() and Routines.Checks.Party.IsPartyLoaded():
            if not _last_was_explorable:
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

    if Agent.IsDead(player_id):
        _status_text = "Player is dead"
        return

    dead_ally_id = claim_resurrection_target(
        Routines.Agents.GetDeadAllyArray(Range.Earshot.value),
        skill_id=0,
        aftercast_delay=_USE_COOLDOWN_MS,
    )
    if dead_ally_id == 0:
        if Routines.Agents.GetDeadAlly(Range.Earshot.value) != 0:
            _status_text = "Dead party member locked by another account"
        else:
            _status_text = "All alive"
        _on_cooldown = False
        return

    if skip_if_res_available and _alive_party_member_has_res_skill():
        _status_text = "Dead party member - res skill available"
        return

    if not _aftercast_timer.HasElapsed(_AFTERCAST_MS):
        _status_text = "Dead party member - waiting aftercast"
        return

    if _on_cooldown and not _cooldown_timer.HasElapsed(_USE_COOLDOWN_MS):
        _status_text = "Dead party member - waiting cooldown"
        return

    item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(_SCROLL_MODEL_ID)
    if item_id == 0:
        _status_text = "Dead party member - no scroll in inventory"
        return

    Player.ChangeTarget(dead_ally_id)
    ConsoleLog(MODULE_NAME, f"Party member dead, using Scroll of Resurrection on {dead_ally_id}", Console.MessageType.Info)
    GLOBAL_CACHE.Inventory.UseItem(item_id)
    _aftercast_timer.Reset()
    _on_cooldown = True
    _cooldown_timer.Reset()
    _status_text = "Used scroll!"


def draw_settings() -> None:
    _settings.ensure_initialized()

    if ImGui.begin_child("##ResurrectionScrollSettingsChild", (0, 0)):
        PyImGui.text("Party Members")
        PyImGui.separator()

        accounts = _get_same_party_accounts()
        if not accounts:
            PyImGui.text_disabled("No same-party accounts found.")
        else:
            for account in accounts:
                account_email = str(account.AccountEmail or "")
                account_name = str(getattr(getattr(account, "AgentData", None), "CharacterName", "") or account_email)

                enabled = _settings.get_account_resurrection_scroll_enabled(account_email)
                new_enabled = PyImGui.checkbox(f"Enable##res_scroll_enabled_{account_email}", enabled)
                if new_enabled != enabled:
                    _settings.set_account_resurrection_scroll_enabled(new_enabled, account_email)

                PyImGui.same_line(0, 8)
                PyImGui.text(account_name)

                skip = _settings.get_account_resurrection_scroll_skip_if_res_available(account_email)
                new_skip = PyImGui.checkbox(f"Skip if res skill available##res_scroll_skip_{account_email}", skip)
                if new_skip != skip:
                    _settings.set_account_resurrection_scroll_skip_if_res_available(new_skip, account_email)

        PyImGui.spacing()
        PyImGui.separator()
        PyImGui.text(f"Local status: {_status_text}")

        if _res_cache:
            PyImGui.spacing()
            PyImGui.text("Local cached res skill holders:")
            for agent_id, name, skill_name in _res_cache:
                alive = "?"
                try:
                    alive = "alive" if Agent.IsValid(agent_id) and not Agent.IsDead(agent_id) else "dead"
                except Exception:
                    pass
                PyImGui.bullet_text(f"{name}: {skill_name} ({alive})")

        PyImGui.spacing()
        if PyImGui.button(f"{IconsFontAwesome5.ICON_SCROLL} Rebuild local cache"):
            rebuild_cache()

    ImGui.end_child()
