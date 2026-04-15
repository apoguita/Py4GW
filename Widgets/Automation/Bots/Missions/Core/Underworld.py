
# ╔══════════════════════════════════════════════════════════════════════════════
# ║  File    : underworld.py
# ║  Purpose : Fully automated Guild Wars Underworld bot.
# ║            Drives all quest sections from Chamber through Dhuum,
# ║            handles entering  and exiting, inventory refill, conset
# ║            management, and multibox party coordination.
# ║            Combat-system integration (CB vs. HeroAI) is swapped via
# ║            the adapter pattern — quest-section code never touches
# ║            the combat system directly.
# ╚══════════════════════════════════════════════════════════════════════════════

# Force a fresh reimport of adapter modules on every script (re)load so that
# edits to adapter files are picked up without restarting the entire Py4GW process.
import sys as _sys
for _mod_key in [k for k in _sys.modules if "sch0l0ka.adapter" in k]:
    del _sys.modules[_mod_key]
del _sys

import enum
import os
import json
import time
from collections import deque
from pathlib import Path
from typing import Any, Generator

import PyImGui
import Py4GW
from Py4GWCoreLib import Botting, Routines, Agent, AgentArray, Player, Utils, AutoPathing, GLOBAL_CACHE, ConsoleLog, Map, Pathing, FlagPreference, Party, IniHandler, Overlay, Item, ItemArray
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.enums_src.Map_enums import name_to_map_id
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Sources.oazix.CustomBehaviors.primitives.behavior_state import BehaviorState

# ╔══════════════════════════════════════════════════════════════════
# ║                     POSSIBLE IMPROVEMENTS                        
# ╠══════════════════════════════════════════════════════════════════
# ║  [X] Kill the Chained Souls when we wait till the quest is done                                                        
# ║  [X] Blacklist Dreamrider to improve Plains speed                                                         
# ║  [X] add Inventory Management                                                          
# ║  [ ] unequip armor at dhuum to sacrifice selected heroes  
# ║  [ ] add Heroai 
# ║  [ ] Take the Dhuum quest earlier   
# ║  [ ] Make pits quest saver and fix 3d navigation                                       
# ║  [X] Reset combat state at the start of each run to prevent stuck                      
# ║      "combat disabled" state after a wipe (e.g. Servants of Grenth)                   
# ║  [ ] Improve pathing around body-blocking Vengeful Aatxe spawn points                 
# ║  [X] Pcons not applied mid-run — only triggered on map load;                           
# ║      ensure UseConset/UsePcons is called after entering the dungeon   
# ║  [ ] Add Questreward for all accounts   
# ║  [ ] Fix runaway at 4H quest   
# ║  [ ] Add Target Priority Management       
# ║                                                                  
# ╚══════════════════════════════════════════════════════════════════


# ── Module identity ──────────────────────────────────────────────────────────
# Model ID 3078 = Dhuum ghost buff NPC (informational reference)
MODULE_NAME = "Underworld"
MODULE_ICON = "Textures/Module_Icons/Underworld.png"
BOT_NAME    = "Underworld"

# ── Persistent configuration (INI file) ──────────────────────────────────────
_ini_file = os.path.join(Py4GW.Console.get_projects_path(), "Widgets", "Config", "UnderworldBot.ini")
_ini = IniHandler(_ini_file)

# ── Consumable definitions ──────────────────────────────────────────────────
# Each entry: (property_name, display_name, category, default_restock_quantity)
# property_name must match a name in UpkeepData (used for Properties.ApplyNow).
_CONS_DEFS: list[tuple[str, str, str, int]] = [
    # Conset
    ("armor_of_salvation",    "Armor of Salvation",    "Conset",     4),
    ("essence_of_celerity",   "Essence of Celerity",   "Conset",     4),
    ("grail_of_might",        "Grail of Might",        "Conset",     4),
    # War
    ("war_supplies",          "War Supplies",           "War",        4),
    # Food / Buff
    ("drake_kabob",           "Drake Kabob",            "Food",       4),
    ("bowl_of_skalefin_soup", "Bowl of Skalefin Soup", "Food",       4),
    ("pahnai_salad",          "Pahnai Salad",           "Food",       4),
    # Sweet
    ("candy_corn",            "Candy Corn",             "Sweet",      4),
    ("candy_apple",           "Candy Apple",            "Sweet",      4),
    ("birthday_cupcake",      "Birthday Cupcake",       "Sweet",      4),
    ("golden_egg",            "Golden Egg",             "Sweet",      4),
    ("slice_of_pumpkin_pie",  "Pumpkin Pie",            "Sweet",      4),
    ("honeycomb",             "Honeycomb",              "Sweet",      4),
]


class ConsSettings:
    """Active flag and Xunlai-restock quantity for every upkeep-able consumable.

    Values are persisted in UnderworldBot.ini under the keys
    ``cons_<property_name>_active`` and ``cons_<property_name>_restock``.
    Changes applied via set_active() / set_restock() also call
    bot.Properties.ApplyNow() so the running upkeep coroutine reacts immediately.
    """

    # Dicts are populated at class-definition time from the INI file.
    _active:  dict[str, bool] = {
        p: bool(_ini.read_bool(BOT_NAME, f"cons_{p}_active", True))
        for p, _, _, _ in _CONS_DEFS
    }
    _restock: dict[str, int] = {
        p: int(_ini.read_int(BOT_NAME, f"cons_{p}_restock", dr))
        for p, _, _, dr in _CONS_DEFS
    }

    @classmethod
    def is_active(cls, prop: str) -> bool:
        return cls._active.get(prop, True)

    @classmethod
    def get_restock(cls, prop: str) -> int:
        return cls._restock.get(prop, 0)

    @classmethod
    def set_active(cls, prop: str, value: bool) -> None:
        cls._active[prop] = value
        cls._save()

    @classmethod
    def set_restock(cls, prop: str, value: int) -> None:
        cls._restock[prop] = max(0, value)
        cls._save()

    @classmethod
    def _save(cls) -> None:
        for prop, _, _, _ in _CONS_DEFS:
            _ini.write_key(BOT_NAME, f"cons_{prop}_active",  str(cls._active.get(prop, True)))
            _ini.write_key(BOT_NAME, f"cons_{prop}_restock", str(cls._restock.get(prop, 0)))


# ── Bot instance ─────────────────────────────────────────────────────────────
# Constructed once at module load; all quest sections share this singleton.
bot = Botting(
    BOT_NAME,
    config_draw_path=True,
    upkeep_auto_inventory_management_active=True,
    # ── Conset ──────────────────────────────────────────────────────────────
    upkeep_armor_of_salvation_active   = ConsSettings._active["armor_of_salvation"],
    upkeep_armor_of_salvation_restock  = ConsSettings._restock["armor_of_salvation"],
    upkeep_essence_of_celerity_active  = ConsSettings._active["essence_of_celerity"],
    upkeep_essence_of_celerity_restock = ConsSettings._restock["essence_of_celerity"],
    upkeep_grail_of_might_active       = ConsSettings._active["grail_of_might"],
    upkeep_grail_of_might_restock      = ConsSettings._restock["grail_of_might"],
    # ── War ─────────────────────────────────────────────────────────────────
    upkeep_war_supplies_active         = ConsSettings._active["war_supplies"],
    upkeep_war_supplies_restock        = ConsSettings._restock["war_supplies"],
    # ── Food / Buff ──────────────────────────────────────────────────────────
    upkeep_drake_kabob_active            = ConsSettings._active["drake_kabob"],
    upkeep_drake_kabob_restock           = ConsSettings._restock["drake_kabob"],
    upkeep_bowl_of_skalefin_soup_active  = ConsSettings._active["bowl_of_skalefin_soup"],
    upkeep_bowl_of_skalefin_soup_restock = ConsSettings._restock["bowl_of_skalefin_soup"],
    upkeep_pahnai_salad_active           = ConsSettings._active["pahnai_salad"],
    upkeep_pahnai_salad_restock          = ConsSettings._restock["pahnai_salad"],
    # ── Sweet ────────────────────────────────────────────────────────────────
    upkeep_candy_corn_active            = ConsSettings._active["candy_corn"],
    upkeep_candy_corn_restock           = ConsSettings._restock["candy_corn"],
    upkeep_candy_apple_active           = ConsSettings._active["candy_apple"],
    upkeep_candy_apple_restock          = ConsSettings._restock["candy_apple"],
    upkeep_birthday_cupcake_active      = ConsSettings._active["birthday_cupcake"],
    upkeep_birthday_cupcake_restock     = ConsSettings._restock["birthday_cupcake"],
    upkeep_golden_egg_active            = ConsSettings._active["golden_egg"],
    upkeep_golden_egg_restock           = ConsSettings._restock["golden_egg"],
    upkeep_slice_of_pumpkin_pie_active  = ConsSettings._active["slice_of_pumpkin_pie"],
    upkeep_slice_of_pumpkin_pie_restock = ConsSettings._restock["slice_of_pumpkin_pie"],
    upkeep_honeycomb_active             = ConsSettings._active["honeycomb"],
    upkeep_honeycomb_restock            = ConsSettings._restock["honeycomb"],
)
bot.Templates.Aggressive()
bot.UI.override_draw_help(lambda: _draw_help())
bot.UI.override_draw_config(lambda: _draw_settings())

# ── Runtime state ─────────────────────────────────────────────────────────────
MAIN_LOOP_HEADER_NAME = ""
_entered_dungeon: bool = False      # set True once map 72 is loaded; watchdog uses this
_dhuum_fight_active: bool = False   # set True from start of Dhuum fight to chest spawn
_run_start_uptime_ms: int = 0       # Map.GetInstanceUptime() value (ms) when the dungeon was entered
_enter_ep: list = ["", 0]           # [entrypoint_name, map_id] — resolved at FSM execution time by Enter_UW
_SKELETON_OF_DHUUM_MODEL_ID: int = 2392
_DRAW_BLOCKED_AREAS_3D = False

_BLOCKED_AREA_SEGMENTS = 48
_BLOCKED_AREA_THICKNESS = 2.5
_BLOCKED_AREA_COLOR = Utils.RGBToColor(255, 40, 40, 170)
_BLOCKED_AREA_RADIUS = 200.0

_pending_wipe_recovery: bool = False   # set by coroutine; consumed by main() before bot.Update()
_pending_wipe_reason:   str  = ""      # human-readable label logged when the restart fires
_planned_resign:        bool = False   # set before an intentional resign so OnPartyWipe is suppressed
_DEBUG_LOG_MAX = 120
_debug_watchdog_log: deque[str] = deque(maxlen=_DEBUG_LOG_MAX)


def _append_debug_watchdog_log(message: str) -> None:
    _debug_watchdog_log.append(f"[{time.strftime('%H:%M:%S')}] {message}")

# ── Quest section completion tracking ────────────────────────────────────────
_QUEST_ORDER: list[str] = [
    "Clear the Chamber",
    "Pass the Mountains",
    "Restore Mountains",
    "Deamon Assassin",
    "Restore Planes",
    "The Four Horsemen",
    "Restore Pools",
    "Terrorweb Queen",
    "Restore Pit",
    "Imprisoned Spirits",
    "Restore Vale",
    "Wrathfull Spirits",
    "Unwanted Guests",
    "Restore Wastes",
    "Servants of Grenth",
    "Dhuum",
]
_quest_completion_times: dict[str, int] = {}   # quest_name → GetInstanceUptime() ms at completion


# ── Quest and NPC enums ───────────────────────────────────────────────────────

class UWQuestID(enum.IntEnum):
    """GW quest IDs for the Underworld quest chain."""
    ClearTheChamber           = 101
    EscortOfSouls             = 108
    UnwantedGuests            = 103
    RestoringGrenthsMonuments = 109
    ImprisonedSpirits         = 105
    TheFourHorsemen           = 106
    WrathfulSpirits           = 110
    ServantsOfGrenth          = 102
    TerrorwebQueen            = 107
    DemonAssassin             = 104
    TheNightmareCometh        = 1129


class UWNpcModelID(enum.IntEnum):
    """Model IDs for Underworld quest-giver NPCs."""
    LostSoul                       = 2425
    ReaperOfTheLabyrinth           = 2399
    ReaperOfTheBonePits            = 2399
    ReaperOfTheChaosPlanes         = 2399
    ReaperOfTheForgottenVale       = 2399
    ReaperOfTheIceWastes           = 2399
    ReaperOfTheSpawningPools       = 2399
    ReaperOfTheTwinSerpentMountains= 2399
    KingFrozenwind                 = 2403


UW_MAP_ID = 72
UW_SCROLL_MODEL_ID = int(ModelID.Passage_Scroll_Uw.value)  # 3746
UW_ENTRYPOINTS: dict[str, tuple[str, int]] = {
    "embark_beach":       ("Embark Beach",       int(name_to_map_id["Embark Beach"])),
    "temple_of_the_ages": ("Temple of the Ages", int(name_to_map_id["Temple of the Ages"])),
    "chantry_of_secrets": ("Chantry of Secrets", int(name_to_map_id["Chantry of Secrets"])),
    "zin_ku_corridor":    ("Zin Ku Corridor",     int(name_to_map_id["Zin Ku Corridor"])),
}
DEFAULT_UW_ENTRYPOINT_KEY = "embark_beach"


# ── Combat adapter (Strategy Pattern) ────────────────────────────────────────
# _get_adapter() returns the right singleton based on BotSettings.BotMode.
# CB mode (default): UWCBAdapter — uses CustomBehaviors shared-memory flags.
# HeroAI mode:       UWHeroAIAdapter — drives native GW flags + HeroAI options.
_cb_adapter_instance = None
_heroai_adapter_instance = None


def _get_adapter():
    global _cb_adapter_instance, _heroai_adapter_instance
    if BotSettings.BotMode == "heroai":
        if _heroai_adapter_instance is None:
            from Sources.sch0l0ka.adapter.uw_heroai_adapter import UWHeroAIAdapter
            _heroai_adapter_instance = UWHeroAIAdapter(BOT_NAME)
        return _heroai_adapter_instance
    if _cb_adapter_instance is None:
        from Sources.sch0l0ka.adapter.uw_cb_adapter import UWCBAdapter
        _cb_adapter_instance = UWCBAdapter(BOT_NAME)
    return _cb_adapter_instance


def _uw_aggressive(b: Botting, **kwargs) -> None:
    """Wrapper around Templates.Aggressive() that undoes the HeroAI/Isolation
    side effects when running in CB mode."""
    b.Templates.Aggressive(**kwargs)
    if BotSettings.BotMode != "heroai":
        b.Properties.Disable("hero_ai")
        b.Multibox.SetAccountIsolation(False)


def _uw_pacifist(b: Botting) -> None:
    """Wrapper around Templates.Pacifist() that undoes the Isolation
    side effect when running in CB mode."""
    b.Templates.Pacifist()
    if BotSettings.BotMode != "heroai":
        b.Multibox.SetAccountIsolation(False)


def _mark_entered_dungeon() -> None:
    global _entered_dungeon, _run_start_uptime_ms
    _entered_dungeon = True
    _run_start_uptime_ms = Map.GetInstanceUptime()


def _set_dhuum_fight_active(value: bool) -> None:
    global _dhuum_fight_active
    _dhuum_fight_active = value


def _record_quest_done(name: str) -> None:
    """Record the completion time (instance uptime ms) for a quest section."""
    if name not in _quest_completion_times:
        _quest_completion_times[name] = Map.GetInstanceUptime()


class InventorySettings:
    """Settings for between-run inventory management."""
    RefillEnabled: bool = bool(_ini.read_bool(BOT_NAME, "inv_refill_enabled", True))
    RestockCons:   bool = bool(_ini.read_bool(BOT_NAME, "inv_restock_cons",   True))

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, "inv_refill_enabled", str(cls.RefillEnabled))
        _ini.write_key(BOT_NAME, "inv_restock_cons",   str(cls.RestockCons))


class DhuumSettings:
    """Which multibox accounts are designated as sacrifice targets in the Dhuum fight."""
    _raw: str = _ini.read_key(BOT_NAME, "dhuum_sacrifice_emails", "")
    SacrificeEmails: set[str] = set(e.strip() for e in _raw.split(";") if e.strip())

    _raw_armor: str = _ini.read_key(BOT_NAME, "dhuum_armor_switch_emails", "")
    ArmorSwitchEmails: set[str] = set(e.strip() for e in _raw_armor.split(";") if e.strip())

    MinSpiritformAccounts: int = int(_ini.read_int(BOT_NAME, "dhuum_min_spiritform", 2))

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, "dhuum_sacrifice_emails", ";".join(sorted(cls.SacrificeEmails)))
        _ini.write_key(BOT_NAME, "dhuum_armor_switch_emails", ";".join(sorted(cls.ArmorSwitchEmails)))
        _ini.write_key(BOT_NAME, "dhuum_min_spiritform", str(cls.MinSpiritformAccounts))

    @classmethod
    def is_sacrifice(cls, email: str) -> bool:
        return email in cls.SacrificeEmails

    @classmethod
    def set_sacrifice(cls, email: str, value: bool) -> None:
        if value:
            cls.SacrificeEmails.add(email)
        else:
            cls.SacrificeEmails.discard(email)
        cls.save()

    @classmethod
    def is_armor_switch(cls, email: str) -> bool:
        return email in cls.ArmorSwitchEmails

    @classmethod
    def set_armor_switch(cls, email: str, value: bool) -> None:
        if value:
            cls.ArmorSwitchEmails.add(email)
        else:
            cls.ArmorSwitchEmails.discard(email)
        cls.save()


class ImprisonedSpiritsSettings:
    """Team assignments for the Imprisoned Spirits quest (left vs. right side)."""
    _raw_left:  str = _ini.read_key(BOT_NAME, "imprisoned_left_emails",  "") or ""
    _raw_right: str = _ini.read_key(BOT_NAME, "imprisoned_right_emails", "") or ""
    LeftTeamEmails:  list[str] = [e.strip() for e in _raw_left.split(";")  if e.strip()]
    RightTeamEmails: list[str] = [e.strip() for e in _raw_right.split(";") if e.strip()]

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, "imprisoned_left_emails",  ";".join(cls.LeftTeamEmails))
        _ini.write_key(BOT_NAME, "imprisoned_right_emails", ";".join(cls.RightTeamEmails))

    @classmethod
    def get_team(cls, email: str) -> str:
        """Returns 'left' or 'right'. Defaults to 'right' if unassigned."""
        if email in cls.LeftTeamEmails:
            return "left"
        return "right"

    @classmethod
    def set_team(cls, email: str, team: str) -> None:
        cls.LeftTeamEmails  = [e for e in cls.LeftTeamEmails  if e != email]
        cls.RightTeamEmails = [e for e in cls.RightTeamEmails if e != email]
        if team == "left":
            cls.LeftTeamEmails.append(email)
        else:
            cls.RightTeamEmails.append(email)
        cls.save()

    @classmethod
    def apply_defaults_if_empty(cls, accounts: list) -> None:
        """If no assignments saved yet, put first 3 on left, rest on right."""
        if cls.LeftTeamEmails or cls.RightTeamEmails:
            return
        emails = [str(a.AccountEmail) for a in accounts]
        cls.LeftTeamEmails  = emails[:3]
        cls.RightTeamEmails = emails[3:]
        cls.save()


class BotSettings:
    """General run settings (repeat, cons, hard mode, combat system choice)."""
    Repeat:    bool = bool(_ini.read_bool(BOT_NAME, "quest_repeat",    False))
    UseCons:   bool = bool(_ini.read_bool(BOT_NAME, "quest_use_cons",  True))
    HardMode:  bool = bool(_ini.read_bool(BOT_NAME, "quest_hardmode",  False))
    BotMode:   str  = str(_ini.read_key(BOT_NAME,  "quest_bot_mode",  "custom_behavior") or "custom_behavior")

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, "quest_repeat",    str(cls.Repeat))
        _ini.write_key(BOT_NAME, "quest_use_cons",  str(cls.UseCons))
        _ini.write_key(BOT_NAME, "quest_hardmode",  str(cls.HardMode))
        _ini.write_key(BOT_NAME, "quest_bot_mode",  str(cls.BotMode))


class EnterSettings:
    """Settings for how the bot travels to and enters the Underworld."""
    EntryPoint: str = str(_ini.read_key(BOT_NAME, "enter_entrypoint", DEFAULT_UW_ENTRYPOINT_KEY) or DEFAULT_UW_ENTRYPOINT_KEY)

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, "enter_entrypoint", str(cls.EntryPoint))



# ── FSM / adapter helpers ─────────────────────────────────────────────────────
# Thin wrappers that delegate to the active adapter so quest-section code
# never needs to know whether CB or HeroAI is in use.

def _toggle_wait_if_aggro(enabled: bool) -> None:
    _get_adapter().toggle_wait_if_aggro(enabled)

def _toggle_wait_for_party(enabled: bool) -> None:
    _get_adapter().toggle_wait_for_party(enabled)

def _toggle_move_to_party_member_if_dead(enabled: bool) -> None:
    _get_adapter().toggle_move_to_party_member_if_dead(enabled)

def _toggle_in_danger_callback(enabled: bool) -> None:
    _get_adapter().toggle_in_danger_callback(enabled)

def _enqueue_section(bot_instance: Botting, attr_name: str, label: str, section_fn):
    bot_instance.States.AddHeader(label)
    bot_instance.States.AddCustomState(
        lambda l=label: _get_adapter().reactivate_for_step(bot_instance, l),
        f"[Setup] {label}",
    )
    section_fn(bot_instance)

def _add_header_with_name(bot_instance: Botting, step_name: str) -> str:
    header_name = f"[H]{step_name}_{bot_instance.config.get_counter('HEADER_COUNTER')}"
    bot_instance.config.FSM.AddYieldRoutineStep(
        name=header_name,
        coroutine_fn=lambda: Routines.Yield.wait(100),
    )
    return header_name

def _restart_main_loop(bot_instance: Botting, reason: str) -> None:
    global _entered_dungeon, _dhuum_fight_active
    _entered_dungeon = False
    _dhuum_fight_active = False
    _quest_completion_times.clear()
    target = MAIN_LOOP_HEADER_NAME
    fsm = bot_instance.config.FSM
    fsm.pause()
    fsm.finished = False  # clear finished flag in case the FSM had reached its last state
    try:
        if target:
            fsm.jump_to_state_by_name(target)
            ConsoleLog(BOT_NAME, f"[WIPE] {reason} – restarting at {target}.", Py4GW.Console.MessageType.Info)
        else:
            ConsoleLog(BOT_NAME, "[WIPE] MAIN_LOOP header missing, restarting from first state.", Py4GW.Console.MessageType.Warning)
            fsm.jump_to_state_by_step_number(0)
    except (ValueError, IndexError):
        # ValueError  – state name not found; IndexError – states list empty
        ConsoleLog(BOT_NAME, f"[WIPE] Header '{target}' not found, restarting from first state.", Py4GW.Console.MessageType.Error)
        try:
            fsm.jump_to_state_by_step_number(0)
        except (ValueError, IndexError):
            ConsoleLog(BOT_NAME, "[WIPE] FSM has no states – cannot restart.", Py4GW.Console.MessageType.Error)
    finally:
        fsm.resume()


def _request_wipe_restart(reason: str) -> None:
    """Request a wipe-recovery restart from inside a managed coroutine.

    Keeps the FSM paused and sets a flag that main() will consume BEFORE
    the next bot.Update() call — guaranteeing the resume never happens from
    inside FSM.update()'s managed-coroutines loop (which would allow
    execute() to run with a potentially stale or None current_state).
    """
    global _pending_wipe_recovery, _pending_wipe_reason
    _pending_wipe_recovery = True
    _pending_wipe_reason   = reason


def _blacklist(bot_instance: Botting, name: str) -> None:
    """Enqueue a state that adds *name* to the EnemyBlacklist."""
    from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist
    bot_instance.States.AddCustomState(
        lambda n=name: EnemyBlacklist().add_name(n),
        f"Blacklist {name.title()}",
    )


def _unblacklist(bot_instance: Botting, name: str) -> None:
    """Enqueue a state that removes *name* from the EnemyBlacklist."""
    from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist
    bot_instance.States.AddCustomState(
        lambda n=name: EnemyBlacklist().remove_name(n),
        f"Unblacklist {name.title()}",
    )


def _enqueue_spread_flags(bot_instance: Botting, flag_points: list[tuple[int, int]]) -> None:
    """Clear flags, auto-assign emails, then set adapter flags for each position.
    Only heroes are flagged (player/party leader is excluded automatically)."""
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().clear_flags(),
        "Clear Flags",
    )
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().auto_assign_flag_emails(),
        "Assign Flag Emails",
    )
    for idx, (flag_x, flag_y) in enumerate(flag_points):
        bot_instance.States.AddCustomState(
            lambda i=idx, x=flag_x, y=flag_y: _get_adapter().set_flag(i, x, y),
            f"Set Flag {idx}",
        )


def _enqueue_imprisoned_spirits_flags(bot_instance: Botting) -> None:
    """Clear flags, then assign left/right team accounts to their respective flag positions.
    The player's own account is excluded (it navigates via the bot FSM directly).
    Left accounts → LEFT_POINTS sequentially; right accounts → RIGHT_POINTS sequentially."""
    LEFT_POINTS  = [(13849, 6602), (13876, 6752), (13985, 6840), (13598, 6779)]
    RIGHT_POINTS = [(12871, 2512), (12640, 2485), (12402, 2472), (12137, 2444), (12150, 2139)]

    def _set_team_flags() -> None:
        my_email     = Player.GetAccountEmail()
        left_emails  = list(ImprisonedSpiritsSettings.LeftTeamEmails)
        right_emails = list(ImprisonedSpiritsSettings.RightTeamEmails)

        # Ensure every connected account is in one of the two lists
        all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData() or []
        known = set(e.lower() for e in left_emails + right_emails)
        for acct in all_accounts:
            email = str(acct.AccountEmail).strip()
            if email and email.lower() not in known:
                right_emails.append(email)
                ImprisonedSpiritsSettings.set_team(email, "right")
                ConsoleLog(BOT_NAME, f"[Imprisoned] Auto-assigned '{email}' to right team.", Py4GW.Console.MessageType.Info)

        assignments: list[tuple[str, int, float, float]] = []
        cb_idx = 0

        # Collect left-team accounts, track overflow
        left_overflow: list[str] = []
        left_pt = 0
        for email in left_emails:
            if email == my_email:
                continue
            if left_pt >= len(LEFT_POINTS):
                left_overflow.append(email)
                continue
            x, y = LEFT_POINTS[left_pt]
            assignments.append((email, cb_idx, float(x), float(y)))
            ConsoleLog(BOT_NAME, f"[Imprisoned] Left  [{cb_idx}] {email} \u2192 ({x},{y})", Py4GW.Console.MessageType.Info)
            cb_idx  += 1
            left_pt += 1

        # Collect right-team accounts, track overflow
        right_overflow: list[str] = []
        right_pt = 0
        for email in right_emails:
            if email == my_email:
                continue
            if right_pt >= len(RIGHT_POINTS):
                right_overflow.append(email)
                continue
            x, y = RIGHT_POINTS[right_pt]
            assignments.append((email, cb_idx, float(x), float(y)))
            ConsoleLog(BOT_NAME, f"[Imprisoned] Right [{cb_idx}] {email} \u2192 ({x},{y})", Py4GW.Console.MessageType.Info)
            cb_idx   += 1
            right_pt += 1

        # Assign overflow from right → remaining left slots
        for email in right_overflow:
            if left_pt >= len(LEFT_POINTS):
                break
            x, y = LEFT_POINTS[left_pt]
            assignments.append((email, cb_idx, float(x), float(y)))
            ConsoleLog(BOT_NAME, f"[Imprisoned] Overflow→Left  [{cb_idx}] {email} \u2192 ({x},{y})", Py4GW.Console.MessageType.Info)
            cb_idx  += 1
            left_pt += 1

        # Assign overflow from left → remaining right slots
        for email in left_overflow:
            if right_pt >= len(RIGHT_POINTS):
                break
            x, y = RIGHT_POINTS[right_pt]
            assignments.append((email, cb_idx, float(x), float(y)))
            ConsoleLog(BOT_NAME, f"[Imprisoned] Overflow→Right [{cb_idx}] {email} \u2192 ({x},{y})", Py4GW.Console.MessageType.Info)
            cb_idx   += 1
            right_pt += 1

        _get_adapter().batch_set_flags(assignments)
        ConsoleLog(BOT_NAME, f"[Imprisoned] Flagged {len(assignments)} account(s) total.", Py4GW.Console.MessageType.Info)

    bot_instance.States.AddCustomState(_set_team_flags, "Set Imprisoned Spirits Team Flags")


def WaitTillQuestDone(bot_instance: Botting) -> None:
    from Py4GWCoreLib.Quest import Quest
    bot_instance.Wait.UntilCondition(
        lambda: not Routines.Checks.Map.MapValid()
        or Map.GetMapID() != UW_MAP_ID
        or ((Quest.GetActiveQuest() > 0) and Quest.IsQuestCompleted(Quest.GetActiveQuest()))
    )


def EnqueueDialogUntilQuestActive(
    bot_instance: Botting,
    dialog_id: int,
    quest_id: int,
    model_id: int = 0,
    step_name: str = "take quest",
    max_retries: int = 4,
    retry_pause_ms: int = 10000,
) -> None:
    """Send a dialog and retry until the active quest matches *quest_id*.

    Use *model_id* to target an NPC by model ID.
    """
    from Py4GWCoreLib.Quest import Quest
    target_quest_id = int(quest_id)

    # Disable ALL movement-issuing CB utility skills on the local instance
    # (following, automover, wait_if_in_aggro, etc.) so this account stays at
    # the NPC during the dialog sequence.  Does NOT touch shared memory.
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().toggle_local_movement(False),
        f"[QuestDialog] Disable local CB movement for quest {target_quest_id}",
    )

    bot_instance.Dialogs.WithModel(model_id, dialog_id, step_name)

    def _coro_ensure_quest_active() -> Generator[Any, Any, None]:
        if target_quest_id <= 0:
            return

        if int(Quest.GetActiveQuest()) == target_quest_id:
            _append_debug_watchdog_log(f"Quest {target_quest_id} accepted on first try.")
            return

        for attempt in range(1, max_retries + 1):
            yield from Routines.Yield.wait(retry_pause_ms)

            if int(Quest.GetActiveQuest()) == target_quest_id:
                _append_debug_watchdog_log(
                    f"Quest {target_quest_id} confirmed before retry {attempt}."
                )
                return

            _append_debug_watchdog_log(
                f"Quest {target_quest_id} not active, retrying dialog ({attempt}/{max_retries})."
            )
            while Agent.IsInCombatStance(Player.GetAgentID()):
                yield from Routines.Yield.wait(5000)
            yield from bot_instance.Dialogs._coro_with_model(model_id, dialog_id)

            if int(Quest.GetActiveQuest()) == target_quest_id:
                _append_debug_watchdog_log(
                    f"Quest {target_quest_id} accepted after retry {attempt}."
                )
                return

        ConsoleLog(
            BOT_NAME,
            f"[QuestDialog] Quest {target_quest_id} was not set after retries.",
            Py4GW.Console.MessageType.Warning,
        )
        _append_debug_watchdog_log(
            f"Quest {target_quest_id} still not active after retries."
        )

    step_idx = bot_instance.config.get_counter("QUEST_DIALOG_RETRY")
    bot_instance.config.FSM.AddYieldRoutineStep(
        name=f"Ensure Quest Active {target_quest_id}_{step_idx}",
        coroutine_fn=_coro_ensure_quest_active,
    )

    # Re-enable all movement utility skills on the local CB instance.
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().toggle_local_movement(True),
        f"[QuestDialog] Re-enable local CB movement after quest {target_quest_id}",
    )


def _coro_hold_horsemen_position() -> Generator[Any, Any, None]:
    """Keep the player at the Four Horsemen wait position every frame.
    Calls Player.Move unconditionally on every frame so that CB movement
    commands (which also fire every frame) cannot override the hold position.
    Exits as soon as the quest is completed, the map is no longer valid,
    the player leaves the UW, or the player is dead (e.g. party wipe).
    This prevents a stale generator from issuing spurious Move commands
    during subsequent quest steps after a wipe recovery.
    """
    from Py4GWCoreLib.Quest import Quest
    _HOLD_X, _HOLD_Y = 11510, -18234
    _MAX_DISTANCE = 80.0
    while True:
        if not Routines.Checks.Map.MapValid():
            return
        if Map.GetMapID() != UW_MAP_ID:
            return
        player_id = Player.GetAgentID()
        if player_id and Agent.IsValid(player_id) and Agent.IsDead(player_id):
            return
        if (Quest.GetActiveQuest() > 0) and Quest.IsQuestCompleted(Quest.GetActiveQuest()):
            # Clear the player's target immediately so the GW client does not
            # try to render a despawning Horsemen agent in AvSelect, which
            # would crash with: !(manualAgentId && !ManagerFindAgent(manualAgentId))
            yield from Routines.Yield.Keybinds.ClearTarget()
            return
        if Utils.Distance(Player.GetXY(), (_HOLD_X, _HOLD_Y)) > _MAX_DISTANCE:
            Player.Move(_HOLD_X, _HOLD_Y)
        yield from Routines.Yield.wait(250)


def _move_with_unstuck(
    bot_instance: Botting,
    target_x: float,
    target_y: float,
    step_name: str = "",
    stuck_threshold: float = 50.0,
    backup_ms: int = 800,
    max_retries: int = 5,
    recalc_interval_ms: int = 500,
    overall_timeout_s: float = 60.0,
) -> None:
    """Move to (target_x, target_y) with continuous path recalculation every recalc_interval_ms.

    Every interval the path is rebuilt from the current player position, hard-avoiding
    all navmesh nodes within 150 units of any blacklisted alive enemy.
    If no avoiding path exists (narrow corridor), falls back to a direct navmesh path.
    Stuck detection: if progress toward the target is less than stuck_threshold per interval
    for max_retries consecutive intervals → /stuck + walk backwards, then try an offset
    intermediate waypoint perpendicular to the target direction.
    overall_timeout_s prevents infinite loops (0 = disabled).
    """
    import math
    import time as _time
    _AVOID_RADIUS = 150.0
    _OFFSET_DISTANCE = 300.0  # perpendicular offset distance after stuck recovery

    def _coro():
        import heapq as _heapq
        from Py4GWCoreLib.Pathing import AutoPathing, AStar, AStarNode, densify_path2d
        from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist

        tolerance = 150.0
        tx, ty = target_x, target_y
        stuck_counter = 0
        _start_time = _time.monotonic()
        _offset_side = 1  # alternates +1 / -1 for perpendicular offset direction

        class _AStarAvoid(AStar):
            """A* that hard-blocks any node within _AVOID_RADIUS of a blacklisted enemy."""
            def __init__(self, navmesh, avoid_pts):
                super().__init__(navmesh)
                self._avoid = avoid_pts

            def _blocked(self, node_id: int) -> bool:
                if not self._avoid:
                    return False
                nx, ny = self.navmesh.get_position(node_id)
                return any(math.hypot(nx - ax, ny - ay) < _AVOID_RADIUS for ax, ay in self._avoid)

            def search(self, start_pos, goal_pos):
                s_id = self.navmesh.find_trapezoid_id_by_coord(start_pos)
                g_id = self.navmesh.find_trapezoid_id_by_coord(goal_pos)
                if s_id is None or g_id is None:
                    return False
                ol: list = []
                _heapq.heappush(ol, AStarNode(s_id, 0, self.heuristic(s_id, g_id)))
                came: dict = {}
                cost: dict = {s_id: 0}
                while ol:
                    cur = _heapq.heappop(ol)
                    if cur.id == g_id:
                        self._reconstruct(came, g_id)
                        self.path.insert(0, start_pos)
                        self.path.append(goal_pos)
                        return True
                    for nb in self.navmesh.get_neighbors(cur.id):
                        if nb != g_id and self._blocked(nb):
                            continue
                        nc = cost[cur.id] + self.heuristic(cur.id, nb)
                        if nb not in cost or nc < cost[nb]:
                            cost[nb] = nc
                            _heapq.heappush(ol, AStarNode(nb, nc, nc + self.heuristic(nb, g_id), cur.id))
                            came[nb] = cur.id
                return False

        def _escape_point(px, py, avoid_pts, navmesh) -> tuple[float, float] | None:
            """Return the closest navmesh-valid point outside all avoid zones, or None."""
            best_dist = float("inf")
            best_pt: tuple[float, float] | None = None
            for ax, ay in avoid_pts:
                d = math.hypot(px - ax, py - ay)
                if d < _AVOID_RADIUS:
                    if d < 1.0:
                        dx, dy = 1.0, 0.0
                    else:
                        dx, dy = (px - ax) / d, (py - ay) / d
                    ex = ax + dx * (_AVOID_RADIUS + 20.0)
                    ey = ay + dy * (_AVOID_RADIUS + 20.0)
                    # Validate escape point lies on navmesh
                    if navmesh is not None and navmesh.find_trapezoid_id_by_coord((ex, ey)) is None:
                        continue
                    escape_d = math.hypot(ex - px, ey - py)
                    if escape_d < best_dist:
                        best_dist = escape_d
                        best_pt = (ex, ey)
            return best_pt

        def _build_path(px, py, avoid_pts):
            """Return a densified move_path for FollowPath.
            If the player is currently inside an avoid zone, a short escape segment
            is prepended so the route leaves the zone first."""
            navmesh = AutoPathing().get_navmesh()
            if navmesh is None:
                return [(tx, ty)]

            escape = _escape_point(px, py, avoid_pts, navmesh) if avoid_pts else None
            start = escape if escape else (px, py)

            for pts in (avoid_pts, []):
                ast = _AStarAvoid(navmesh, pts)
                if ast.search(start, (tx, ty)):
                    raw = ast.get_path()
                    try:
                        smoothed = navmesh.smooth_path_by_los(raw, margin=100, step_dist=200.0) or raw
                    except Exception:
                        smoothed = raw
                    if escape:
                        smoothed = [escape] + smoothed
                    return densify_path2d(smoothed)
                if not avoid_pts:
                    break

            return [(tx, ty)]

        def _perpendicular_offset(px, py) -> tuple[float, float] | None:
            """Compute a point offset perpendicular to the player→target direction.
            Returns None if the point is not on the navmesh."""
            nonlocal _offset_side
            dx, dy = tx - px, ty - py
            dist = math.hypot(dx, dy)
            if dist < 1.0:
                return None
            # Perpendicular unit vector (rotated 90°)
            perp_x = -dy / dist * _offset_side
            perp_y = dx / dist * _offset_side
            # Midpoint between player and target, offset to the side
            mid_x = px + dx * 0.3 + perp_x * _OFFSET_DISTANCE
            mid_y = py + dy * 0.3 + perp_y * _OFFSET_DISTANCE
            _offset_side *= -1  # alternate side next time
            navmesh = AutoPathing().get_navmesh()
            if navmesh is not None and navmesh.find_trapezoid_id_by_coord((mid_x, mid_y)) is None:
                return None
            return (mid_x, mid_y)

        while True:
            # Overall timeout guard
            if overall_timeout_s > 0 and (_time.monotonic() - _start_time) >= overall_timeout_s:
                ConsoleLog(
                    BOT_NAME,
                    f"[Move] Overall timeout ({overall_timeout_s:.0f}s) reached for ({tx:.0f},{ty:.0f}). Aborting.",
                    Py4GW.Console.MessageType.Warning,
                )
                return

            px, py = Player.GetXY()
            if math.hypot(tx - px, ty - py) <= tolerance:
                return

            bl = EnemyBlacklist()
            avoid_pts = [
                Agent.GetXY(eid)
                for eid in AgentArray.GetEnemyArray()
                if bl.is_blacklisted(eid) and Agent.IsAlive(eid)
            ]

            enemy_nearby = any(
                math.hypot(px - ax, py - ay) <= 500.0
                for ax, ay in avoid_pts
            )
            follow_timeout = recalc_interval_ms if enemy_nearby else 0

            move_path = _build_path(px, py, avoid_pts if enemy_nearby else [])

            reached = yield from Routines.Yield.Movement.FollowPath(
                path_points=move_path,
                tolerance=tolerance,
                timeout=follow_timeout,
            )
            if reached:
                return

            npx, npy = Player.GetXY()
            progress = math.hypot(tx - px, ty - py) - math.hypot(tx - npx, ty - npy)

            if progress < stuck_threshold:
                stuck_counter += 1
                if stuck_counter >= max_retries:
                    ConsoleLog(
                        BOT_NAME,
                        f"[Move] Stuck at ({px:.0f},{py:.0f}) → ({tx:.0f},{ty:.0f}). Recovering.",
                        Py4GW.Console.MessageType.Warning,
                    )
                    Player.SendChatCommand("stuck")
                    yield from Routines.Yield.wait(1000)
                    yield from Routines.Yield.Movement.WalkBackwards(backup_ms)
                    yield from Routines.Yield.wait(300)
                    stuck_counter = 0

                    # Try an offset intermediate waypoint to break out of the stuck zone
                    offset_pt = _perpendicular_offset(npx, npy)
                    if offset_pt:
                        ConsoleLog(
                            BOT_NAME,
                            f"[Move] Trying offset waypoint ({offset_pt[0]:.0f},{offset_pt[1]:.0f})",
                            Py4GW.Console.MessageType.Info,
                        )
                        yield from Routines.Yield.Movement.FollowPath(
                            path_points=[offset_pt],
                            tolerance=tolerance,
                            timeout=3000,
                        )
            else:
                stuck_counter = 0

    label = step_name or f"MoveUnstuck_{target_x:.0f}_{target_y:.0f}"
    bot_instance.config.FSM.AddYieldRoutineStep(name=label, coroutine_fn=_coro)


def FocusKeeperOfSouls(bot_instance: Botting):
    KeeperOfSoulsModelID = 2373
    def _focus_logic():
        enemies = [e for e in AgentArray.GetEnemyArray() if Agent.IsAlive(e) and Agent.GetModelID(e) == KeeperOfSoulsModelID]
        
        if not enemies:
            return
        
        player_pos = Player.GetXY()
        closest_enemy = min(enemies, key=lambda e: ((player_pos[0] - Agent.GetXYZ(e)[0])**2 + (player_pos[1] - Agent.GetXYZ(e)[1])**2)**0.5)
        if Agent.IsValid(closest_enemy):
            _get_adapter().set_custom_target(closest_enemy)

    bot_instance.States.AddCustomState(_focus_logic, "Focus Keeper of Souls")


def _draw_blocked_areas_overlay() -> None:
    """Query blacklisted enemy positions and draw circles every frame. Called from main()."""
    if not _DRAW_BLOCKED_AREAS_3D:
        return
    if not Routines.Checks.Map.MapValid():
        return
    if Map.GetMapID() != UW_MAP_ID:
        return
    # Skip during the Dhuum fight — the per-frame INI reads and GetNameByID calls
    # for every enemy in the arena add unnecessary load on the leader client.
    if _dhuum_fight_active:
        return
    try:
        from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist
        _bl = EnemyBlacklist()
        avoid_points = [
            Agent.GetXY(_eid)
            for _eid in AgentArray.GetEnemyArray()
            if _bl.is_blacklisted(_eid) and Agent.IsAlive(_eid)
        ]
        if not avoid_points:
            return
        _overlay = Overlay()
        _overlay.BeginDraw()
        for _ax, _ay in avoid_points:
            _az = _overlay.FindZ(_ax, _ay, 0)
            _overlay.DrawPoly3D(
                _ax,
                _ay,
                _az,
                radius=_BLOCKED_AREA_RADIUS,
                color=_BLOCKED_AREA_COLOR,
                numsegments=_BLOCKED_AREA_SEGMENTS,
                thickness=_BLOCKED_AREA_THICKNESS,
            )
        _overlay.EndDraw()
    except Exception:
        pass





def _coro_skeleton_dhuum_watchdog(bot: Botting):
    """Continuously target the nearest alive Skeleton of Dhuum within spell range
    while pause_on_danger is active."""
    from Py4GWCoreLib.enums import Range
    while True:
        yield from Routines.Yield.wait(250)

        if not bot.config.fsm_running:
            continue
        if not _entered_dungeon:
            continue
        if Map.GetMapID() != UW_MAP_ID:
            continue
        # During the Dhuum fight CB handles all targeting — skip to reduce client load.
        if _dhuum_fight_active:
            continue
        if not bot.config.pause_on_danger_fn():
            continue

        player_pos = Player.GetXY()
        skeletons = [
            e for e in AgentArray.GetEnemyArray()
            if Agent.IsAlive(e)
            and int(Agent.GetModelID(e)) == _SKELETON_OF_DHUUM_MODEL_ID
            and Utils.Distance(player_pos, Agent.GetXY(e)) <= Range.Spellcast.value
        ]
        if not skeletons:
            continue

        nearest = min(skeletons, key=lambda e: Utils.Distance(player_pos, Agent.GetXY(e)))
        # Re-check validity: the agent may have died between loop and ChangeTarget call.
        if Agent.IsValid(nearest):
            _get_adapter().set_custom_target(nearest)


def _coro_dhuum_spirit_form_watchdog(bot: Botting):
    """Monitor all ShMem party members during the Dhuum fight for the Spirit Form buff
    (skill ID 3134 — Spirit_Form_disguise).  While an account has Spirit Form the CB
    flag is moved to the ghost position so follow_flag guides the ghost there.
    When Spirit Form ends (account resurrected via Dhuum Helper dialog) the flag is
    restored to the pre-death position so the account returns to the fight.

    NOTE: No PixelStack is sent — the Dhuum Helper widget handles NPC interaction
    on each follower locally.  A concurrent PixelStack coroutine would conflict with
    the Dhuum Helper's movement commands and cause unreliable dialog delivery."""
    _SPIRIT_FORM_SKILL_ID = 3134
    _SPIRIT_FLAG_X = -16476
    _SPIRIT_FLAG_Y = 17275
    # email -> original flag (x, y) saved when Spirit Form was first detected
    _saved_flag_positions: dict[str, tuple[float, float]] = {}
    _last_sync_log_at: dict[str, float] = {}

    def _read_current_flag_pos(email: str) -> tuple[float, float] | None:
        """Read the current CB flag position for *email* from shared memory."""
        try:
            from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
            mgr = CustomBehaviorParty().party_flagging_manager
            for i in range(12):
                if mgr.get_flag_account_email(i).lower() == email.lower():
                    pos = mgr.get_flag_position(i)
                    if pos != (0.0, 0.0):
                        return pos
                    return None
        except Exception:
            pass
        return None

    while True:
        yield from Routines.Yield.wait(500)

        if not bot.config.fsm_running:
            continue
        if not _dhuum_fight_active:
            # Reset tracker when outside the fight so the next run starts clean.
            _saved_flag_positions.clear()
            _last_sync_log_at.clear()
            continue

        current_map_id = Map.GetMapID()
        if current_map_id != UW_MAP_ID:
            continue

        for account in GLOBAL_CACHE.ShMem.GetAllAccountData() or []:
            if not getattr(account, "IsSlotActive", True):
                continue
            email = str(getattr(account, "AccountEmail", "") or "").strip()
            if not email:
                continue
            # Only process accounts in the same map instance.
            if getattr(account.AgentData.Map, "MapID", 0) != current_map_id:
                continue

            # Check the buff array for Spirit Form (buff ID 3134).
            try:
                has_spirit_form = any(
                    b.SkillId == _SPIRIT_FORM_SKILL_ID
                    for b in account.AgentData.Buffs.Buffs
                    if b.SkillId != 0
                )
            except Exception:
                has_spirit_form = False

            if not has_spirit_form:
                # Spirit Form ended — restore the flag to the saved pre-death position
                # so follow_flag guides the account back to the fight, not the ghost area.
                if email in _saved_flag_positions:
                    ox, oy = _saved_flag_positions.pop(email)
                    try:
                        _get_adapter().update_flag_position_for_email(email, ox, oy)
                        ConsoleLog(
                            BOT_NAME,
                            f"[Dhuum] {email} lost Spirit Form — flag restored to ({ox:.0f}, {oy:.0f}).",
                            Py4GW.Console.MessageType.Info,
                        )
                        _append_debug_watchdog_log(f"Flag restored -> {email} ({ox:.0f}, {oy:.0f})")
                    except Exception:
                        pass
                _last_sync_log_at.pop(email, None)
                continue

            try:
                # First detection: save the current flag position before overriding.
                if email not in _saved_flag_positions:
                    cur = _read_current_flag_pos(email)
                    if cur is not None:
                        _saved_flag_positions[email] = cur
                    ConsoleLog(
                        BOT_NAME,
                        f"[Dhuum] {email} gained Spirit Form — repositioning flag to ghost area.",
                        Py4GW.Console.MessageType.Info,
                    )
                    _append_debug_watchdog_log(
                        f"Spirit Form detected -> {email} saved=({cur[0]:.0f}, {cur[1]:.0f})" if cur else
                        f"Spirit Form detected -> {email} (no saved flag)"
                    )

                # Keep the flag continuously synced while Spirit Form is active.
                # This recovers from intermittent overwrites/races in shared flag memory.
                _get_adapter().update_flag_position_for_email(email, _SPIRIT_FLAG_X, _SPIRIT_FLAG_Y)

                now = time.monotonic()
                if now - _last_sync_log_at.get(email, 0.0) >= 2.0:
                    _append_debug_watchdog_log(
                        f"SpiritForm sync -> {email} flag=({_SPIRIT_FLAG_X:.0f}, {_SPIRIT_FLAG_Y:.0f})"
                    )
                    _last_sync_log_at[email] = now
            except Exception as _e:
                _append_debug_watchdog_log(f"Watchdog error for {email}: {_e}")
                ConsoleLog(
                    BOT_NAME,
                    f"[Dhuum] Spirit Form watchdog error for {email}: {_e}",
                    Py4GW.Console.MessageType.Warning,
                )


# ── Pcon multibox broadcast ─────────────────────────────────────────────────
# Mapping: (ConsSettings key, ModelID value, skill effect name)
# Only entries whose settings_key is active in ConsSettings will be broadcast.
# Honeycomb is excluded — it gives a one-shot morale boost, not an expiring buff.
_PCON_BROADCAST_TABLE: list[tuple[str, int, str]] = [
    ("armor_of_salvation",    ModelID.Armor_Of_Salvation.value,     "Armor_of_Salvation_item_effect"),
    ("essence_of_celerity",   ModelID.Essence_Of_Celerity.value,   "Essence_of_Celerity_item_effect"),
    ("grail_of_might",        ModelID.Grail_Of_Might.value,        "Grail_of_Might_item_effect"),
    ("war_supplies",          ModelID.War_Supplies.value,           "Well_Supplied"),
    ("drake_kabob",           ModelID.Drake_Kabob.value,            "Drake_Skin"),
    ("bowl_of_skalefin_soup", ModelID.Bowl_Of_Skalefin_Soup.value, "Skale_Vigor"),
    ("pahnai_salad",          ModelID.Pahnai_Salad.value,           "Pahnai_Salad_item_effect"),
    ("candy_corn",            ModelID.Candy_Corn.value,             "Candy_Corn_skill"),
    ("candy_apple",           ModelID.Candy_Apple.value,            "Candy_Apple_skill"),
    ("birthday_cupcake",      ModelID.Birthday_Cupcake.value,       "Birthday_Cupcake_skill"),
    ("golden_egg",            ModelID.Golden_Egg.value,             "Golden_Egg_skill"),
    ("slice_of_pumpkin_pie",  ModelID.Slice_Of_Pumpkin_Pie.value,   "Pie_Induced_Ecstasy"),
]


def _broadcast_all_pcons() -> None:
    """Broadcast enabled pcon items to every multibox account (skips sender).

    Only pcons whose ConsSettings key is active are sent.  The UsePcon handler
    on each receiver already guards with AccountHasEffect(), so items are only
    consumed when the buff has actually expired — over-broadcasting is harmless.
    """
    sender = Player.GetAccountEmail()
    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    followers = [a for a in accounts if a.AccountEmail != sender]
    if not followers:
        return

    for settings_key, model_id, effect_name in _PCON_BROADCAST_TABLE:
        if not ConsSettings.is_active(settings_key):
            continue
        skill_id = GLOBAL_CACHE.Skill.GetID(effect_name)
        for account in followers:
            GLOBAL_CACHE.ShMem.SendMessage(
                sender,
                account.AccountEmail,
                SharedCommandType.PCon,
                (float(model_id), float(skill_id), 0.0, 0.0),
            )


def _coro_pcon_upkeep_multibox(bot: Botting):
    """Periodically re-broadcast enabled consumables to multibox followers while
    inside the Underworld.  Broadcasts every 3 minutes; the UsePcon handler on
    each follower guards with AccountHasEffect() so items are only consumed when
    the buff has actually expired.

    Registered via _ensure_managed_coroutines() every frame so it survives
    FSM.restart() which clears the managed_coroutines list."""
    _INTERVAL_MS = 3 * 60 * 1000   # 3 minutes — shorter than the shortest pcon duration
    _TICK_MS     = 1000
    _last_fire_at: float = 0.0

    while True:
        yield from Routines.Yield.wait(_TICK_MS)

        if not bot.config.fsm_running:
            continue
        if not BotSettings.UseCons:
            continue
        if not _entered_dungeon:
            # Reset the timer when outside the dungeon so a fresh window starts
            # at the next dungeon entry.
            _last_fire_at = 0.0
            continue
        if Map.GetMapID() != UW_MAP_ID:
            continue

        now_ms = time.monotonic() * 1000
        if _last_fire_at == 0.0:
            # Arm the timer on the first tick inside the dungeon.  Skip the
            # first interval — the initial broadcast is handled by Clear_the_Chamber.
            _last_fire_at = now_ms
            continue
        if (now_ms - _last_fire_at) < _INTERVAL_MS:
            continue

        _last_fire_at = now_ms
        _broadcast_all_pcons()
        _append_debug_watchdog_log("Pcon upkeep: broadcast sent to all multibox accounts.")


# ── Managed-coroutine registration ──────────────────────────────────────────
# FSM.restart() (triggered by the Start button) calls _cleanup_coroutines()
# which clears ALL managed coroutines.  Botting._start_coroutines() re-adds
# the *built-in* upkeep coroutines every frame, but UW-specific ones are not
# part of that list.  _ensure_managed_coroutines() mirrors that pattern so
# they survive FSM restarts.  AddManagedCoroutine de-duplicates by name, so
# calling this every frame is a cheap no-op once the coroutines are attached.
def _ensure_managed_coroutines(bot_ref: Botting) -> None:
    fsm = bot_ref.config.FSM
    fsm.AddManagedCoroutine("UW_SkeletonDhuumWatchdog",    lambda: _coro_skeleton_dhuum_watchdog(bot_ref))
    fsm.AddManagedCoroutine("UW_DhuumSpiritFormWatchdog",  lambda: _coro_dhuum_spirit_form_watchdog(bot_ref))
    fsm.AddManagedCoroutine("UW_PconUpkeepMultibox",       lambda: _coro_pcon_upkeep_multibox(bot_ref))


def bot_routine(bot: Botting):
    global MAIN_LOOP_HEADER_NAME, _run_start_uptime_ms

    # Set a fallback start time so Duration is never 00:00:00 if _mark_entered_dungeon
    # was not reached (e.g. bot started directly at a later section).
    if _run_start_uptime_ms == 0:
        _run_start_uptime_ms = Map.GetInstanceUptime()

    # ── One-time adapter and coroutine setup ──────────────────────────────────
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    _get_adapter().set_blessing_enabled(True)
    _get_adapter().setup(bot)
    # __reset_botting_behavior (called inside setup via UseCustomBehavior) queues
    # Disable("auto_inventory_management"). Re-enable it immediately after so
    # the upkeep coroutine stays active for the entire run.
    bot.Properties.Enable("auto_inventory_management")

    # NOTE: UW-specific managed coroutines (watchdogs, pcon upkeep) are
    # registered every frame via _ensure_managed_coroutines() in main().
    # Botting._start_coroutines() only re-registers built-in upkeep coroutines
    # after FSM.restart() clears managed_coroutines, so UW-specific ones must
    # be handled separately with the same every-frame de-dupe pattern.

    # Broadcast widget-policy states: disable/enable CB or HeroAI on all accounts.
    _get_adapter().configure_startup_states(bot)
    _uw_aggressive(bot)

    # ── Quest-section state chain ─────────────────────────────────────────────
    # MAIN_LOOP_HEADER_NAME is the FSM jump target used by the wipe handler so
    # a restart skips the one-time setup above and jumps straight to this point.
    MAIN_LOOP_HEADER_NAME = _add_header_with_name(bot, "MAIN_LOOP")

    Enter_UW(bot)
    Clear_the_Chamber(bot)
    _enqueue_section(bot, "PassTheMountains", "Pass the Mountains", Pass_The_Mountains)
    _enqueue_section(bot, "RestoreMountains", "Restore Mountains", Restore_Mountains)
    _enqueue_section(bot, "DeamonAssassin", "Deamon Assassin", Deamon_Assassin)
    _enqueue_section(bot, "RestorePlanes", "Restore Planes", Restore_Planes)
    _enqueue_section(bot, "TheFourHorsemen", "The Four Horsemen", The_Four_Horsemen)
    _enqueue_section(bot, "RestorePools", "Restore Pools", Restore_Pools)
    _enqueue_section(bot, "TerrorwebQueen", "Terrorweb Queen", Terrorweb_Queen)
    _enqueue_section(bot, "RestorePit", "Restore Pit", Restore_Pit)
    _enqueue_section(bot, "ImprisonedSpirits", "Imprisoned Spirits", Imprisoned_Spirits)
    _enqueue_section(bot, "RestoreVale", "Restore Vale", Restore_Vale)
    _enqueue_section(bot, "WrathfullSpirits", "Wrathfull Spirits", Wrathfull_Spirits)
    _enqueue_section(bot, "UnwantedGuests", "Unwanted Guests", Unwanted_Guests)
    _enqueue_section(bot, "RestoreWastes", "Restore Wastes", Restore_Wastes)
    _enqueue_section(bot, "ServantsOfGrenth", "Servants of Grenth", Servants_of_Grenth)
    
    _enqueue_section(bot, "Dhuum", "Dhuum", Dhuum)
    _enqueue_section(bot, "Repeat", "Repeat the whole thing", ResignAndRepeat)
    bot.States.AddHeader("END")




def Enter_UW(bot_instance: Botting):
    from Sources.modular_bot.recipes.step_context import StepContext
    from Sources.modular_bot.recipes.actions_movement import handle_random_travel, handle_wait_map_change, handle_leave_party
    from Sources.modular_bot.recipes.actions_party import handle_summon_all_accounts, handle_invite_all_accounts, handle_set_hard_mode
    from Sources.modular_bot.recipes.actions_interaction import handle_use_item

    def _make_ctx(step: dict) -> StepContext:
        return StepContext(
            bot=bot_instance,
            step=step,
            step_idx=0,
            recipe_name="UW_Enter",
            step_type=step.get("type", ""),
            step_display=step.get("name", ""),
        )

    bot_instance.States.AddHeader("Enter Underworld")

    # After a wipe or resign the leader (and alts) may still be transitioning
    # to the outpost.  Wait until the leader is fully on an outpost before
    # issuing KickAllAccounts so the command reaches accounts that are ready.
    bot_instance.Wait.UntilOnOutpost()
    bot_instance.Wait.ForTime(5000)

    # ── Inventory refill at GH / configured outpost ───────────────────
    bot_instance.Multibox.KickAllAccounts()
    _do_merchant_rules_refill(bot_instance)

    # ── Leave any existing party (multibox-aware) ─────────────────────
    handle_leave_party(_make_ctx({"type": "leave_party", "name": "Leave Party", "multibox": True}))

    # ── Travel to the selected entrypoint (resolved at execution time) ──
    # entrypoint_name / map_id are resolved lazily into _enter_ep so that
    # any change made in the Settings UI before pressing Start is always
    # honoured, even when the FSM was built at module-load with an older value.
    def _resolve_entrypoint() -> None:
        key = EnterSettings.EntryPoint or DEFAULT_UW_ENTRYPOINT_KEY
        name, mid = UW_ENTRYPOINTS.get(key, UW_ENTRYPOINTS[DEFAULT_UW_ENTRYPOINT_KEY])
        _enter_ep[0] = name
        _enter_ep[1] = mid
        ConsoleLog(BOT_NAME, f"[Enter] Entry point resolved: {name} (map {mid})", Py4GW.Console.MessageType.Info)

    def _travel_to_entrypoint() -> None:
        import random
        from Py4GWCoreLib.enums_src.Region_enums import District
        districts = [
            District.EuropeItalian.value,
            District.EuropeSpanish.value,
            District.EuropePolish.value,
            District.EuropeRussian.value,
        ]
        Map.TravelToDistrict(_enter_ep[1], district=random.choice(districts))

    bot_instance.States.AddCustomState(_resolve_entrypoint, "Resolve Entry Point")
    bot_instance.Party.LeaveParty()
    bot_instance.States.AddCustomState(_travel_to_entrypoint, "Travel to Entrypoint")
    bot_instance.Wait.ForTime(500)
    bot_instance.Wait.UntilCondition(
        lambda: Routines.Checks.Map.MapValid() and Map.GetMapID() == _enter_ep[1]
    )
    bot_instance.Wait.ForTime(1000)

    # ── Form party ───────────────────────────────────────────────────
    handle_summon_all_accounts(_make_ctx({"type": "summon_all_accounts", "name": "Summon Alts", "ms": 10000}))

    # Wait until every account has loaded into the entrypoint map (up to 90 s).
    bot_instance.Wait.UntilCondition(
        lambda: all(int(acc.AgentData.Map.MapID) == _enter_ep[1] for acc in GLOBAL_CACHE.ShMem.GetAllAccountData()),
        duration=5000,
    )

    handle_invite_all_accounts(_make_ctx({"type": "invite_all_accounts", "name": "Invite Alts"}))

    # ── Apply hard mode before using scroll ──────────────────────────
    handle_set_hard_mode(_make_ctx({"type": "set_hard_mode", "name": "Set Hard Mode", "enabled": BotSettings.HardMode}))

    # ── Use UW scroll (model 3746) ───────────────────────────────────
    handle_use_item(_make_ctx({"type": "use_item", "name": "Use UW Scroll", "model_id": UW_SCROLL_MODEL_ID}))

    # ── Wait until inside the Underworld ────────────────────────────
    handle_wait_map_change(_make_ctx({"type": "wait_map_change", "name": "Wait For UW", "target_map_id": UW_MAP_ID}))

    bot_instance.States.AddCustomState(_mark_entered_dungeon, "Mark entered dungeon")
    bot_instance.Properties.ApplyNow("pause_on_danger", "active", True)

    


def enable_default_party_behavior(bot_instance: Botting):
    """
    Enable the baseline party behavior toggles used across Underworld missions.
    """
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_following_enabled(True), "Enable Follow")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_combat_enabled(True), "Enable Combat")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_looting_enabled(True), "Enable Looting")


def Clear_the_Chamber(bot_instance: Botting):
    bot_instance.States.AddHeader("Clear the Chamber")
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().reactivate_for_step(bot_instance, "Clear the Chamber"),
        "[Setup] Clear the Chamber",
    )
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_party_leader(Player.GetAccountEmail()), "Set Party Leader")    
    # Configure the enemy blacklist for this quest section.
    _blacklist(bot_instance, "obsidian guardian")
    _blacklist(bot_instance, "vengeful aatxe")
    _blacklist(bot_instance, "chained soul")
    _unblacklist(bot_instance, "wastfull spirit")
    _unblacklist(bot_instance, "obsidian behemoth")
    _unblacklist(bot_instance, "banished dream rider")
    enable_default_party_behavior(bot_instance)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_combat_enabled(False), "Disable Combat")
    EnqueueDialogUntilQuestActive(bot_instance, dialog_id=0x806501, quest_id=UWQuestID.ClearTheChamber, model_id=UWNpcModelID.LostSoul, step_name="Take Clear the Chamber quest")
    bot_instance.Multibox.SendDialogToTarget(0x806501)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_combat_enabled(True), "Enable Combat")
    bot_instance.Move.XY(769, 6564, "Prepare to clear the chamber")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_forced_state(BehaviorState.CLOSE_TO_AGGRO),"Force Close_to_Aggro",)
    bot_instance.Wait.ForTime(5000)

    if BotSettings.UseCons:
        # Conset upkeep is handled by the Botting constructor (upkeep_*_active=True).
        # Broadcast conset + food pcons immediately on dungeon entry so all multibox
        # accounts have their buffs active from the start.
        bot_instance.Multibox.UseConset()
        bot_instance.Multibox.UsePcons()

    bot_instance.States.AddCustomState(lambda: _get_adapter().set_forced_state(None),"Release Close_to_Aggro",)

    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")

    bot_instance.Move.XY(-1505, 6352, "Left")
    bot_instance.Move.XY(-755, 8982, "Mid")
    bot_instance.Move.XY(1259, 10214, "Right")
    bot_instance.Move.XY(-3729, 13414, "Right")
    bot_instance.Move.XY(-5855, 11202, "Clear the Room")
    bot_instance.Move.XY(-5806, 12831, "Go to NPC")
    bot_instance.Wait.ForTime(3000)
    
    bot_instance.Dialogs.WithModel(UWNpcModelID.ReaperOfTheLabyrinth,0x806507, "Take Clear the Chamber reward")
    bot_instance.Multibox.SendDialogToTarget(0x806507)
    EnqueueDialogUntilQuestActive(bot_instance, dialog_id=0x806D01, quest_id=UWQuestID.RestoringGrenthsMonuments, model_id=UWNpcModelID.ReaperOfTheLabyrinth, step_name="Take Restore Monuments quest")
    bot_instance.Wait.ForTime(3000)
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Clear the Chamber"), "Record Clear the Chamber done")

def Pass_The_Mountains(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.Move.XY(-2740, 10133, "Pass the Mountains 0")
    bot_instance.Move.XY(-728,  8910,  "Pass the Mountains 1")
    bot_instance.Move.XY(-1807, 5883,  "Pass the Mountains 2")
    bot_instance.Move.XY(-3486, 1176,  "Pass the Mountains 3")
    bot_instance.Move.XY(536,   1321,  "Pass the Mountains 4")
    bot_instance.Move.XY(3418,  2213,  "Pass the Mountains 5")
    bot_instance.Move.XY(4911,  1425,  "Pass the Mountains 6")
    bot_instance.Move.XY(7938,  616,   "Pass the Mountains 7")
    bot_instance.Move.XY(8001,  -2390, "Pass the Mountains 8")
    bot_instance.Move.XY(8705,  -5293, "Pass the Mountains 9")
    bot_instance.Move.XY(6528,  -7283, "Pass the Mountains 10")
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Pass the Mountains"), "Record Pass the Mountains done")
    
    

def Restore_Mountains(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.Move.XY(4455,  -7967, "Restore the Mountains 1")
    bot_instance.Move.XY(2008,  -10290, "Restore the Mountains 2")
    bot_instance.Move.XY(-542,  -9046, "Restore the Mountains 3")
    bot_instance.Move.XY(-2408, -7698, "Restore the Mountains 4")
    bot_instance.Move.XY(-4233, -5583, "Restore the Mountains 5")
    bot_instance.Move.XY(-6140, -5230, "Restore the Mountains 6")
    bot_instance.Move.XY(-7923, -4567, "Restore the Mountains 7")
    bot_instance.Wait.ForTime(5000)
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Restore Mountains"), "Record Restore Mountains done")

def Deamon_Assassin(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.Move.XY(-8250, -5171, "Go to Deamon Assassin NPC")
    EnqueueDialogUntilQuestActive(bot_instance, 0x806801, int(UWQuestID.DemonAssassin), int(UWNpcModelID.ReaperOfTheTwinSerpentMountains), "take Deamon Assassin quest")
    bot_instance.Move.XY(-3645, -5820, "Deamon Assassin 1")
    WaitTillQuestDone(bot_instance)
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Deamon Assassin"), "Record Deamon Assassin done")

def Restore_Planes(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().add_name("banished dream rider"),
        "Blacklist Banished Dream Rider",
    )
    
    bot_instance.Move.XY(13837, -14736, "Restore Planes 1 left Rider")
    bot_instance.States.AddCustomState(
        lambda: __import__("Py4GWCoreLib.EnemyBlacklist", fromlist=["EnemyBlacklist"]).EnemyBlacklist().remove_name("banished dream rider"),
        "Unblacklist Banished Dream Rider",
    )
    
    Wait_for_Spawns(bot_instance,13790, -15568)
    Wait_for_Spawns(bot_instance,11287, -17921)
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Restore Planes"), "Record Restore Planes done")


def The_Four_Horsemen(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.Move.XY(13473, -12091, "The Four Horseman 1")
    bot_instance.Wait.ForTime(10000)
    THE_FOUR_HORSEMEN_FLAG_POINTS = [
        (13432, -12100),
        (13246, -12440),
        (13072, -12188),
        (13216, -11841),
        (13639, -11866),
        (13745, -12151),
        (13520, -12436),
    ]
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_following_enabled(False), "Disable Following")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_looting_enabled(False), "Disable Looting")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(False), "Disable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_forced_state(BehaviorState.CLOSE_TO_AGGRO),"Force Close_to_Aggro",)
    bot_instance.Move.XY(11371, -17990, "Go to Chaos Planes NPC")
    EnqueueDialogUntilQuestActive(bot_instance, 0x806A01, int(UWQuestID.TheFourHorsemen), int(UWNpcModelID.ReaperOfTheChaosPlanes), "take Foure Horsemen quest")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_forced_state(None),"Release Close_to_Aggro",)

    bot_instance.Wait.ForTime(32000)

    bot_instance.Move.XY(11371, -17990, "Go to Chaos Planes NPC")
    bot_instance.Dialogs.WithModel(UWNpcModelID.ReaperOfTheChaosPlanes,0x8D, "Tp Lab") 
    bot_instance.States.AddCustomState(lambda: _get_adapter().clear_flags(),"Clear Flags")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_following_enabled(True), "Enable Following")
    bot_instance.Move.XY(-5782, 12819, "TP back to Chaos")
    bot_instance.Dialogs.WithModel(UWNpcModelID.ReaperOfTheLabyrinth,0x8B, "Tp back to Chaos") 
    bot_instance.Wait.ForTime(1000)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_following_enabled(True), "Enable Following")
    THE_FOUR_HORSEMEN_FLAG_POINTS_2 = [
        (11510, -18234),
        (11510, -18234),
        (11510, -18234),
        (11510, -18234),
        (11510, -18234),
        (11510, -18234),
        (11510, -18234),
    ]
    _enqueue_spread_flags(bot_instance, THE_FOUR_HORSEMEN_FLAG_POINTS_2)
    bot_instance.States.AddCustomState(
        lambda: bot_instance.Properties.ApplyNow("pause_on_danger", "active", False),
        "Disable PauseOnDanger for Horsemen wait",
    )
    # Disable WaitIfInAggro so CB does not issue competing movement commands
    # (e.g. moving away from or toward enemies) while we must hold position.
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(False), "Disable WaitIfInAggro for Horsemen hold")
    # Disable ALL local CB movement utilities (following, automover, etc.)
    # so nothing overrides the hold position while waiting for the quest.
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().toggle_local_movement(False),
        "Disable local CB movement for Horsemen hold",
    )
    bot_instance.Move.XY(11510, -18234, "Hold position at Horsemen")
    bot_instance.config.FSM.AddYieldRoutineStep(
        name="Hold position at Horsemen",
        coroutine_fn=_coro_hold_horsemen_position,
    )
    WaitTillQuestDone(bot_instance)
    # Clear the player's target before re-enabling aggro scanning so that
    # a stale target (despawning Horsemen agent) cannot crash AvSelect.cpp.
    bot_instance.States.AddCustomState(
        lambda: Player.ChangeTarget(Player.GetAgentID()),
        "Clear stale target after Horsemen",
    )
    # Re-enable local CB movement utilities after the hold.
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().toggle_local_movement(True),
        "Re-enable local CB movement after Horsemen hold",
    )
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Re-enable WaitIfInAggro after Horsemen")
    bot_instance.States.AddCustomState(
        lambda: bot_instance.Properties.ApplyNow("pause_on_danger", "active", True),
        "Re-enable PauseOnDanger after Horsemen",
    )
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().clear_flags(),
        "Clear Flags",
    )
    bot_instance.Wait.ForTime(10000)
    bot_instance.Move.XY(11371, -17990, "Go to Chaos Planes NPC")
    bot_instance.Dialogs.WithModel(UWNpcModelID.ReaperOfTheChaosPlanes,0x806A07, "take questreward")
    bot_instance.Multibox.SendDialogToTarget(0x806A01)
    bot_instance.Wait.ForTime(3000)
    bot_instance.Multibox.SendDialogToTarget(0x806A01)
    
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_following_enabled(True), "Enable Follow")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_looting_enabled(True), "Enable Looting")
    bot_instance.States.AddCustomState(lambda: _record_quest_done("The Four Horsemen"), "Record The Four Horsemen done")

def Restore_Pools(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    _blacklist(bot_instance, "banished dream rider")
    bot_instance.Move.XY(6869, -17771, "Restore Pools 1")
    bot_instance.Move.XY(2867, -19746, "Restore Pools 1")
    bot_instance.Move.XY(1753, -14703, "Restore Pools 1")
    bot_instance.Move.XY(-12703, -10990, "Restore Pools 1")
    bot_instance.Move.XY(-11849, -11986, "Restore Pools 2")
    bot_instance.Move.XY(-5974, -19739, "Restore Pools 3")
    bot_instance.Move.XY(-7217, -19394, "Restore Pools 4")
    bot_instance.Move.XY(-5688, -19471, "Restore Pools 4")
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Restore Pools"), "Record Restore Pools done")

def Terrorweb_Queen(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.Move.XY(-6957, -19478, "To the NPC")
    EnqueueDialogUntilQuestActive(bot_instance, 0x806B01, int(UWQuestID.TerrorwebQueen), int(UWNpcModelID.ReaperOfTheChaosPlanes), "take Terrorweb Queen quest")
    bot_instance.Multibox.SendDialogToTarget(0x806B01)
    bot_instance.Move.XY(-12432, -15874, "Terrorweb Queen 1")
    bot_instance.Move.XY(-6957, -19478, "Back to Chamber")
    bot_instance.Wait.ForTime(3000)
    bot_instance.Dialogs.WithModel(UWNpcModelID.ReaperOfTheSpawningPools,0x806B07, "Back to Chamber")
    bot_instance.Multibox.SendDialogToTarget(0x806B07)
    bot_instance.Wait.ForTime(3000)
    bot_instance.Dialogs.WithModel(UWNpcModelID.ReaperOfTheSpawningPools,0x8B, "Back to Chamber")
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Terrorweb Queen"), "Record Terrorweb Queen done")
    
def Restore_Pit(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.Move.XY(14178, -57, "Restore Pit 1")
    _unblacklist(bot_instance, "banished dream rider")
    bot_instance.Move.XY(15323, 2970, "Restore Pit 2")
    bot_instance.Move.XY(15393, 406, "Restore Pit 3")
    bot_instance.Move.FollowPath([
        (15252, 316),
        (13451, 1123),
        (13181, 1419),
        (13076, 1547),
    ], step_name="Cross the Bridge")
    bot_instance.Move.XY(13216, 1428, "Restore Pit 4")
    bot_instance.Move.XY(13896, 3670, "Restore Pit 5")
    bot_instance.Move.XY(15382, 6581, "Restore Pit 6")
    bot_instance.Move.XY(10620, 2665, "Restore Pit 7")
    bot_instance.Move.XY(8644, 6242, "Restore Pit 8")
    bot_instance.Wait.ForTime(3000)
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Restore Pit"), "Record Restore Pit done")

def Imprisoned_Spirits(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(False), "Disable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_looting_enabled(False), "Disable Looting")
    bot_instance.Move.XY(13212, 4978)
    _enqueue_imprisoned_spirits_flags(bot_instance)
    bot_instance.Move.XY(8692, 6292, "go to NPC")
    bot_instance.Move.XY(8666, 6308, "go to NPC")
    EnqueueDialogUntilQuestActive(bot_instance, 0x806901, int(UWQuestID.ImprisonedSpirits), int(UWNpcModelID.ReaperOfTheBonePits), "take Imprisoned Spirits quest")

    _is_timer: list[float] = [0.0]  # [monotonic start time], captured by closures below
    bot_instance.States.AddCustomState(
        lambda: _is_timer.__setitem__(0, time.monotonic()),
        "Start Imprisoned Spirits Timer",
    )
    bot_instance.Move.XY(13652, 6117)  # Run down towards the left team
    bot_instance.Wait.UntilCondition(
        lambda: time.monotonic() - _is_timer[0] >= 28.0
    )
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().clear_flags(),
        "Clear Flags",
    )
    bot_instance.Move.XY(12593, 1814)
    bot_instance.Wait.ForTime(40000)
    bot_instance.Wait.UntilCondition(
        lambda: time.monotonic() - _is_timer[0] >= 90.0
    )
    _unblacklist(bot_instance, "chained soul")
    bot_instance.Move.XY(10437, 5005)
    WaitTillQuestDone(bot_instance)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_looting_enabled(True), "Enable Looting")
    _blacklist(bot_instance, "chained soul")

    bot_instance.Move.XY(8692, 6292, "go to NPC")
    bot_instance.Dialogs.AtXY(8692, 6292, 0x8D, "Back to Chamber")
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Imprisoned Spirits"), "Record Imprisoned Spirits done")
        

def Restore_Vale(bot_instance: Botting):

    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")

    bot_instance.Dialogs.AtXY(-5806, 12831, 0x806C03, "take quest")
    EnqueueDialogUntilQuestActive(bot_instance, 0x806C01, int(UWQuestID.EscortOfSouls), int(UWNpcModelID.ReaperOfTheLabyrinth), "take Escort of Souls quest")
    bot_instance.Items.UseSummoningStone()
    bot_instance.Move.XY(-8660, 5655, "To the Vale 1")
    bot_instance.Move.XY(-9431, 1659, "To the Vale 2")
    bot_instance.Move.XY(-11123, 2531, "To the Vale 3")
    bot_instance.Move.XY(-11926, 1146 , "To the Vale 4")
    bot_instance.Move.XY(-10691, 98 , "To the Vale 5")
    bot_instance.Move.XY(-15424, 1319 , "To the Vale 6")
    bot_instance.Move.XY(-13246, 5110 , "To the Vale 7")
    bot_instance.Wait.ForTime(3000)
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Restore Vale"), "Record Restore Vale done")

def Wrathfull_Spirits(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.Move.XY(5755, 12769, "go to NPC")
    bot_instance.Dialogs.WithModel(UWNpcModelID.ReaperOfTheForgottenVale,0x806E03, "take quest")
    EnqueueDialogUntilQuestActive(bot_instance, 0x806E01, int(UWQuestID.WrathfulSpirits), int(UWNpcModelID.ReaperOfTheLabyrinth), "take Wrathfull Spirits quest")
    _uw_pacifist(bot_instance)
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(False), "Disable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(False), "Disable WaitIfInAggro")
    _blacklist(bot_instance, "tortured spirit")
    bot_instance.Move.XY(-13422, 973, "Wrathfull Spirits 1")
    _uw_aggressive(bot_instance)
    _unblacklist(bot_instance, "tortured spirit")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar") 
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    _WS_LOOP_STEP = "Wrathfull Spirits loop start"
    bot_instance.States.AddHeader(_WS_LOOP_STEP)

    bot_instance.Move.XY(-13791, 1642, "Wrathfull Spirits 2")
    bot_instance.Move.XY(-12889, 963, "Wrathfull Spirits 3")
    bot_instance.Move.XY(-11445, 1154, "Wrathfull Spirits 4")
    bot_instance.Move.XY(-10554, 1695, "Wrathfull Spirits 5")
    bot_instance.Move.XY(-9481, 963, "Wrathfull Spirits 6")
    bot_instance.Move.XY(-9949, 177, "Wrathfull Spirits 7")
    bot_instance.Move.XY(-11498, -173, "Wrathfull Spirits 8")
    bot_instance.Move.XY(-12677, -205, "Wrathfull Spirits 9")
    bot_instance.Move.XY(-13622, 336, "Wrathfull Spirits 10")
    bot_instance.Move.XY(-12974, 4116, "Wrathfull Spirits 11")
    bot_instance.Move.XY(-14184, 7279, "Wrathfull Spirits 12")
    bot_instance.Move.XY(-15055, 3755, "Wrathfull Spirits 13")
    bot_instance.Move.XY(-13409, 4933, "Wrathfull Spirits 14")
    bot_instance.Move.XY(5755, 12769, "go to NPC")
    bot_instance.Dialogs.WithModel(UWNpcModelID.ReaperOfTheLabyrinth,0x806E07, "Take Reward")
    bot_instance.Dialogs.WithModel(UWNpcModelID.ReaperOfTheLabyrinth,0x8D, "Back to Chamber")
    bot_instance.Wait.ForTime(3000)
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Wrathfull Spirits"), "Record Wrathfull Spirits done")

def Unwanted_Guests(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    #The Quest
    #1st Keeper
    _blacklist(bot_instance, "obsidian behemoth")
    _move_with_unstuck(bot_instance, -2965, 10260, "1st Keeper approach")
    bot_instance.Wait.ForTime(5000)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_following_enabled(False), "Disable Following")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_forced_state(BehaviorState.CLOSE_TO_AGGRO),"Force Close_to_Aggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable wait_for_party")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(False), "Disable MoveToPartyMemberIfDead")

    bot_instance.Move.XY(-5806, 12831, "Go to NPC")
    EnqueueDialogUntilQuestActive(bot_instance, 0x806701, int(UWQuestID.UnwantedGuests), int(UWNpcModelID.ReaperOfTheLabyrinth), "take Unwanted Guests quest")

    bot_instance.States.AddCustomState(lambda: _get_adapter().set_forced_state(None),"Release Close_to_Aggro")
    # Acquire the Keeper target several times to give CB enough frames to lock
    # onto it, then hold position for 20 s while it is being killed.
    FocusKeeperOfSouls(bot_instance)
    bot_instance.Wait.ForTime(500)
    FocusKeeperOfSouls(bot_instance)
    bot_instance.Wait.ForTime(500)
    FocusKeeperOfSouls(bot_instance)
    bot_instance.Wait.ForTime(20000)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_following_enabled(True), "Enable Following")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_forced_state(None),"Release Close_to_Aggro",)
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")

    #2nd Keeper
    bot_instance.Move.XY(-5806, 12831, "Go to NPC")
    bot_instance.Dialogs.WithModel(UWNpcModelID.ReaperOfTheLabyrinth,0x91, "TP Vale")
    _move_with_unstuck(bot_instance, -12953, 750, "2nd Keeper 1")
    _move_with_unstuck(bot_instance, -8371, 4865, "2nd Keeper 2")
    FocusKeeperOfSouls(bot_instance)
    bot_instance.Wait.ForTime(500)
    FocusKeeperOfSouls(bot_instance)
    _move_with_unstuck(bot_instance, -7589, 6801, "2nd Keeper killed")

    #3rd Keeper
    _move_with_unstuck(bot_instance, -4095, 12964, "3rd Keeper approach")
    FocusKeeperOfSouls(bot_instance)
    bot_instance.Wait.ForTime(500)
    FocusKeeperOfSouls(bot_instance)
    _move_with_unstuck(bot_instance, -647, 13356, "3rd Keeper killed")

    #4th Keeper
    _move_with_unstuck(bot_instance, 1098, 12215, "4th Keeper approach")
    FocusKeeperOfSouls(bot_instance)
    bot_instance.Wait.ForTime(500)
    FocusKeeperOfSouls(bot_instance)
    _move_with_unstuck(bot_instance, 3113, 9503, "4th Keeper killed")

    #5th Keeper
    _move_with_unstuck(bot_instance, 1586, 10362, "5th Keeper approach")
    FocusKeeperOfSouls(bot_instance)
    bot_instance.Wait.ForTime(500)
    FocusKeeperOfSouls(bot_instance)
    _move_with_unstuck(bot_instance, 367, 7214, "5th Keeper killed")

    #6th Keeper
    _move_with_unstuck(bot_instance, -3125, 916, "6th Keeper 1")
    _move_with_unstuck(bot_instance, -597, -537, "6th Keeper 1")
    _move_with_unstuck(bot_instance, -344, 2155, "6th Keeper 2")
    FocusKeeperOfSouls(bot_instance)
    bot_instance.Wait.ForTime(500)
    FocusKeeperOfSouls(bot_instance)
    _move_with_unstuck(bot_instance, 1256, 4623, "6th Keeper killed")

    _unblacklist(bot_instance, "obsidian behemoth")
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Unwanted Guests"), "Record Unwanted Guests done")

def Restore_Wastes(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    _uw_aggressive(bot_instance)
    bot_instance.Properties.ApplyNow("pause_on_danger", "active", True)
    bot_instance.Move.XY(3891, 7572, "Restore Wastes 1")
    bot_instance.Move.XY(4106, 16031, "Restore Wastes 2")
    bot_instance.Move.XY(2486, 21723, "Restore Wastes 3")
    bot_instance.Move.XY(-1452, 21202, "Restore Wastes 4")
    bot_instance.Move.XY(542, 18310, "Restore Wastes 5")
    bot_instance.Wait.ForTime(3000)
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Restore Wastes"), "Record Restore Wastes done")

def Servants_of_Grenth(bot_instance: Botting):
    bot_instance.States.AddCustomState(lambda: _toggle_wait_if_aggro(True), "Enable WaitIfInAggro")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    _uw_aggressive(bot_instance)
    bot_instance.Move.XY(2700, 19952, "Servants of Grenth 1")
    SERVANTS_OF_GRENTH_FLAG_POINTS = [
        (2559, 20301),
        (3032, 20148),
        (2813, 20590),
        (2516, 19665),
        (3231, 19472),
        (3691, 19979),
        (2039, 20175),
        ]
    _enqueue_spread_flags(bot_instance, SERVANTS_OF_GRENTH_FLAG_POINTS)
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(False), "Disable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_forced_state(BehaviorState.CLOSE_TO_AGGRO),"Force Close_to_Aggro",)
    bot_instance.Move.XY(554, 18384, "go to NPC")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_following_enabled(False), "Disable Following")
    EnqueueDialogUntilQuestActive(bot_instance, 0x806601, int(UWQuestID.ServantsOfGrenth), int(UWNpcModelID.ReaperOfTheBonePits), "take Servants of Grenth quest")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_forced_state(None),"Release Close_to_Aggro",)
    
    bot_instance.Move.XY(2700, 19952, "Servants of Grenth 2")
    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(True), "Enable MoveToPartyMemberIfDead")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_following_enabled(True), "Enable Following")
    bot_instance.Party.UnflagAllHeroes()
    bot_instance.Party.FlagAllHeroes(3032, 20148)
    bot_instance.Party.UnflagAllHeroes()
    WaitTillQuestDone(bot_instance)
    bot_instance.Party.UnflagAllHeroes()
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().clear_flags(),
        "Clear Flags",
    )
    bot_instance.Wait.ForTime(30000)
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Servants of Grenth"), "Record Servants of Grenth done")


def Dhuum(bot_instance: Botting):
    #Spirit Form BuffId = 3134
    bot_instance.States.AddHeader("Dhuum")
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().toggle_dead_ally_rescue(False),
        "Disable Dead Ally Rescue",
    )

    bot_instance.States.AddCustomState(lambda: _get_adapter().set_forced_state(None),"Release Close_to_Aggro",)

    

    def _flag_sacrifice_accounts() -> None:
        flag_x, flag_y = -15386, 17295
        _get_adapter().clear_flags()

        sacrifice_emails = DhuumSettings.SacrificeEmails
        if not sacrifice_emails:
            ConsoleLog(BOT_NAME, "[Dhuum] No sacrifice accounts configured in Dhuum settings.", Py4GW.Console.MessageType.Warning)
            return

        cb_flagged_emails: list[str] = []
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            email = str(account.AccountEmail)
            if email not in sacrifice_emails:
                continue

            cb_index = len(cb_flagged_emails)
            if cb_index >= 12:
                break

            _get_adapter().set_flag_for_email(email, cb_index, flag_x, flag_y)
            cb_flagged_emails.append(email)

        if not cb_flagged_emails:
            ConsoleLog(BOT_NAME, "[Dhuum] No sacrifice accounts found in shared memory.", Py4GW.Console.MessageType.Warning)
            return

        ConsoleLog(
            BOT_NAME,
            f"[Dhuum] Flagged {len(cb_flagged_emails)} sacrifice account(s): {cb_flagged_emails}",
            Py4GW.Console.MessageType.Info,
        )

    def _flag_survivor_accounts() -> None:
        flag_x, flag_y = -14374, 17261

        my_email = Player.GetAccountEmail()
        sacrifice_emails = DhuumSettings.SacrificeEmails

        # Start after the sacrifice account indices to avoid overwriting them
        all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        sacrifice_offset = sum(
            1 for account in all_accounts
            if str(account.AccountEmail) in sacrifice_emails
        )

        cb_flagged_emails: list[str] = []
        for account in all_accounts:
            email = str(account.AccountEmail)
            if email == my_email or email in sacrifice_emails:
                continue

            cb_index = sacrifice_offset + len(cb_flagged_emails)
            if cb_index >= 12:
                break

            _get_adapter().set_flag_for_email(email, cb_index, flag_x, flag_y)
            cb_flagged_emails.append(email)

        if not cb_flagged_emails:
            ConsoleLog(BOT_NAME, "[Dhuum] No survivor accounts to flag.", Py4GW.Console.MessageType.Info)
            return

        ConsoleLog(
            BOT_NAME,
            f"[Dhuum] Flagged {len(cb_flagged_emails)} survivor account(s): {cb_flagged_emails}",
            Py4GW.Console.MessageType.Info,
        )

    
    _KING_TARGET_X = -11278.0
    _KING_TARGET_Y =  17297.0
    _KING_MODEL_ID =  2403
    _KING_DEST_RADIUS   = 1500.0  # how close the King must be to his destination
    _KING_FOLLOW_RADIUS = 1000.0  # how close we trail behind the King
    _KING_TIMEOUT_S     = 600.0   # 10 min hard-timeout

    def _coro_follow_king_to_destination():
        """Follow model 2403 until it reaches the area around the destination coords."""
        deadline = time.time() + _KING_TIMEOUT_S
        ConsoleLog(BOT_NAME, "[Dhuum] Waiting for the King to walk to position ...", Py4GW.Console.MessageType.Info)
        while time.time() < deadline:
            king_id = next(
                (a for a in AgentArray.GetAgentArray() if Agent.IsValid(a) and int(Agent.GetModelID(a)) == _KING_MODEL_ID),
                None,
            )
            if king_id is None or not Agent.IsValid(king_id):
                yield from Routines.Yield.wait(500)
                continue

            kx, ky = Agent.GetXY(king_id)

            # Stop following once the King has reached his destination
            if Utils.Distance((kx, ky), (_KING_TARGET_X, _KING_TARGET_Y)) <= _KING_DEST_RADIUS:
                ConsoleLog(BOT_NAME, "[Dhuum] King has reached the position.", Py4GW.Console.MessageType.Info)
                return

            # Move towards the King if we are too far away
            px, py = Player.GetXY()
            if Utils.Distance((px, py), (kx, ky)) > _KING_FOLLOW_RADIUS:
                Player.Move(kx, ky)

            yield from Routines.Yield.wait(500)

        ConsoleLog(BOT_NAME, "[Dhuum] Timed out waiting for the King - continuing anyway.", Py4GW.Console.MessageType.Warning)

    bot_instance.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")
    bot_instance.States.AddCustomState(lambda: _toggle_move_to_party_member_if_dead(False), "Disable MoveToPartyMemberIfDead")
    bot_instance.config.FSM.AddYieldRoutineStep(
        name="Follow King to Destination",
        coroutine_fn=_coro_follow_king_to_destination,
    )


    # Switch to sacrifice armor for all accounts with Switch Armor enabled.
    # For each armor slot, build a {char_name: model_id} dict and send via multibox.
    _armor_data = _read_armor_json()
    for _slot_key in ("2", "3", "4", "5", "6"):  # Chest, Legs, Head, Feet, Hands
        _slot_map: dict[str, int] = {}
        for _acct in GLOBAL_CACHE.ShMem.GetAllAccountData():
            _email = str(_acct.AccountEmail)
            if not DhuumSettings.is_armor_switch(_email):
                continue
            _model_id = (_armor_data.get(_email, {}).get("sacrifice") or {}).get(_slot_key, 0)
            if _model_id != 0:
                _slot_map[str(_acct.AgentData.CharacterName)] = _model_id
        if _slot_map:
            bot_instance.Multibox.EquipItemOnAllAccounts(_slot_map)

    bot_instance.Wait.ForTime(1000)  # wait for armor switch to complete before moving
    bot_instance.Move.XY(-11278, 17297, "Wait For the King")
    bot_instance.Wait.UntilCondition(
        lambda: not Routines.Checks.Map.MapValid()
        or Map.GetMapID() != UW_MAP_ID
        or any(
            Agent.IsValid(agent_id)
            and int(Agent.GetModelID(agent_id)) == 2403
            and Utils.Distance(Player.GetXY(), Agent.GetXY(agent_id)) <= 1100
            for agent_id in AgentArray.GetAgentArray()
        )
    )  # Wait until King is within interaction range (exits on wipe/map change)

    bot_instance.Wait.ForTime(10000)
    EnqueueDialogUntilQuestActive(bot_instance, 0x846901, int(UWQuestID.TheNightmareCometh), int(UWNpcModelID.KingFrozenwind), "Take The Nightmare Cometh quest")
    bot_instance.States.AddCustomState(_flag_sacrifice_accounts, "Flag Sacrifice Accounts")
    bot_instance.States.AddCustomState(_flag_survivor_accounts, "Flag Survivor Accounts")
    bot_instance.States.AddCustomState(
        lambda: bot_instance.Multibox.ApplyWidgetPolicy(enable_widgets=("Dhuum Helper",)),
        "Enable Dhuum Helper on all accounts",
    )

    # Hold combat until enough accounts have Spirit Form active so the team
    # does not engage Dhuum before ghosts are in position.
    _SPIRIT_FORM_SKILL_ID_CHECK = 3134
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().set_combat_enabled(False),
        "Disable Combat until Spirit Form ready",
    )
    def _enough_spiritforms() -> bool:
        if not Routines.Checks.Map.MapValid() or Map.GetMapID() != UW_MAP_ID:
            return True  # bail out on wipe / map change
        threshold = DhuumSettings.MinSpiritformAccounts
        count = 0
        for acct in GLOBAL_CACHE.ShMem.GetAllAccountData() or []:
            if getattr(acct.AgentData.Map, "MapID", 0) != UW_MAP_ID:
                continue
            try:
                if any(b.SkillId == _SPIRIT_FORM_SKILL_ID_CHECK
                       for b in acct.AgentData.Buffs.Buffs if b.SkillId != 0):
                    count += 1
            except Exception:
                pass
            if count >= threshold:
                return True
        return False

    
    # Disable the InDanger event callback for the fight — the CB daemon would
    # immediately stomp any fsm.pause() it sets, causing erratic movement.
    bot_instance.States.AddCustomState(lambda: _toggle_in_danger_callback(False), "Disable InDanger callback for Dhuum")
    # Activate the Spirit Form watchdog for the duration of the fight.
    bot_instance.States.AddCustomState(lambda: _set_dhuum_fight_active(True), "Enable Dhuum Spirit Form Watchdog")
    bot_instance.Wait.ForTime(10000)
    bot_instance.Move.XY(-14007, 17287, "Move to Dhuum fight")
    

    def _wait_and_enable_combat():
        # Poll every 250 ms so combat is enabled in the same coroutine frame
        # the condition is first met — no extra state-transition delay.
        while True:
            yield from Routines.Yield.wait(250)
            if _enough_spiritforms():
                _get_adapter().set_combat_enabled(True)
                return

    bot_instance.config.FSM.AddYieldRoutineStep(
        name="Wait for Spirit Forms and enable combat",
        coroutine_fn=_wait_and_enable_combat,
    )
    bot_instance.Wait.UntilCondition(
        lambda: not Routines.Checks.Map.MapValid()
        or Map.GetMapID() != UW_MAP_ID
        or any(
            Agent.IsValid(agent_id)
            and Agent.IsGadget(agent_id)
            and "underworld chest" in (Agent.GetNameByID(agent_id) or "").strip().lower()
            and Utils.Distance((-14381.0, 17283.0), Agent.GetXY(agent_id)) <= 300
            for agent_id in AgentArray.GetAgentArray()
        )
    )  # Wait until UW Chest appears (exits on wipe/map change)


    # Deactivate the Spirit Form watchdog — Dhuum is dead.
    bot_instance.States.AddCustomState(lambda: _set_dhuum_fight_active(False), "Disable Dhuum Spirit Form Watchdog")
    bot_instance.States.AddCustomState(lambda: _toggle_in_danger_callback(True), "Re-enable InDanger callback")
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_combat_enabled(False), "Disable Combat")

    # Switch back to normal armor for all accounts with Switch Armor enabled.
    _armor_data_normal = _read_armor_json()
    for _slot_key in ("2", "3", "4", "5", "6"):  # Chest, Legs, Head, Feet, Hands
        _slot_map_normal: dict[str, int] = {}
        for _acct in GLOBAL_CACHE.ShMem.GetAllAccountData():
            _email = str(_acct.AccountEmail)
            if not DhuumSettings.is_armor_switch(_email):
                continue
            _model_id = (_armor_data_normal.get(_email, {}).get("normal") or {}).get(_slot_key, 0)
            if _model_id != 0:
                _slot_map_normal[str(_acct.AgentData.CharacterName)] = _model_id
        if _slot_map_normal:
            bot_instance.Multibox.EquipItemOnAllAccounts(_slot_map_normal)

    def _loot_underworld_chest():
        chest_id = next(
            (
                agent_id for agent_id in AgentArray.GetAgentArray()
                if Agent.IsValid(agent_id)
                and Agent.IsGadget(agent_id)
                and "underworld chest" in (Agent.GetNameByID(agent_id) or "").strip().lower()
                and Utils.Distance((-14381.0, 17283.0), Agent.GetXY(agent_id)) <= 300
            ),
            None,
        )
        if chest_id is None:
            ConsoleLog(BOT_NAME, "[Dhuum] Underworld Chest not found for looting!", Py4GW.Console.MessageType.Warning)
            return

        my_email = Player.GetAccountEmail()
        current_map_id = Map.GetMapID()
        all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        same_map_accounts = [
            acc for acc in all_accounts
            if acc.AgentData.Map.MapID == current_map_id
        ]

        ConsoleLog(BOT_NAME, f"[Dhuum] Looting chest with {len(same_map_accounts)} account(s)", Py4GW.Console.MessageType.Info)

        for account in same_map_accounts:
            email = str(account.AccountEmail)
            msg_index = GLOBAL_CACHE.ShMem.SendMessage(
                sender_email=my_email,
                receiver_email=email,
                command=SharedCommandType.InteractWithTarget,
                params=(chest_id, 0, 0, 0),
            )
            if msg_index < 0:
                ConsoleLog(BOT_NAME, f"[Dhuum] Failed to send InteractWithTarget to {email}", Py4GW.Console.MessageType.Warning)
            else:
                ConsoleLog(BOT_NAME, f"[Dhuum] Sent InteractWithTarget (chest) to {email}", Py4GW.Console.MessageType.Info)
            yield from Routines.Yield.wait(5000)

    bot_instance.States.AddCustomState(
        lambda: _get_adapter().clear_flags(),
        "Clear Flags",
    )        

    bot_instance.States.AddCustomState(_loot_underworld_chest, "Loot Underworld Chest")

    bot_instance.Wait.ForTime(5000)  # Wait for looting to finish    

    bot_instance.States.AddCustomState(_loot_underworld_chest, "Loot Underworld Chest")

    bot_instance.Wait.ForTime(5000)  # Wait for any stragglers to finish looting
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_looting_enabled(False), "Disable Looting")
    bot_instance.Move.XY(-14324, 17549)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_looting_enabled(True), "Enable Looting")
    bot_instance.Wait.ForTime(5000)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_looting_enabled(False), "Disable Looting")
    bot_instance.Move.XY(-14243, 17017)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_looting_enabled(True), "Enable Looting")
    bot_instance.Wait.ForTime(5000)
    bot_instance.States.AddCustomState(lambda: _get_adapter().set_combat_enabled(True), "Enable Combat")
    bot_instance.States.AddCustomState(
        lambda: _get_adapter().toggle_dead_ally_rescue(True),
        "Enable Dead Ally Rescue",
    )
    bot_instance.States.AddCustomState(lambda: _record_quest_done("Dhuum"), "Record Dhuum done")
    bot_instance.Move.XYAndDialog(-15774, 17302,0x846907, "Talk to Dhuum and complete quest")
    bot_instance.Multibox.SendDialogToTarget(0x846901)
    bot_instance.Wait.ForTime(2000)
    bot_instance.Multibox.SendDialogToTarget(0x846907)
    bot_instance.Wait.ForTime(2000)



def _get_merchant_rules_widget():
    """Get the MerchantRules WIDGET_INSTANCE via the widget handler (same approach as Messaging.py)."""
    try:
        from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler
        widget_handler = get_widget_handler()
        for widget_name in ("MerchantRules", "Merchant Rules"):
            widget_info = widget_handler.get_widget_info(widget_name)
            if not widget_info or not getattr(widget_info, "module", None):
                continue
            instance = getattr(widget_info.module, "WIDGET_INSTANCE", None)
            if instance is not None:
                return instance
    except Exception:
        pass
    return None


def _do_merchant_rules_refill(bot_instance: Botting) -> None:
    """Travel everyone to the Guild Hall, then trigger MerchantRules 'Execute Here'
    on the leader and send MerchantRules EXECUTE to all followers.
    Requires the MerchantRules widget to be enabled and configured on all accounts."""
    if not InventorySettings.RefillEnabled:
        return
    _GH_TRAVEL_TIMEOUT_MS = 60_000
    _EXECUTE_TIMEOUT_MS   = 180_000
    _FOLLOWER_TIMEOUT_MS  = 180_000
    _POLL_MS              = 500

    def _coro_merchant_rules_refill():
        # ── 0. Enable MerchantRules widget on leader + all followers ──
        from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler
        _MR_WIDGET_NAME = "MerchantRules"
        widget_handler = get_widget_handler()
        if not widget_handler.is_widget_enabled(_MR_WIDGET_NAME):
            widget_handler.enable_widget(_MR_WIDGET_NAME)
            Py4GW.Console.Log(BOT_NAME, "Enabled MerchantRules widget on leader.", Py4GW.Console.MessageType.Info)

        sender_email = Player.GetAccountEmail()
        all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData() or []
        followers = [a for a in all_accounts if a.AccountEmail != sender_email]

        for account in followers:
            GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                str(account.AccountEmail),
                SharedCommandType.EnableWidget,
                (0, 0, 0, 0),
                (_MR_WIDGET_NAME, "", "", ""),
            )
        if followers:
            Py4GW.Console.Log(BOT_NAME, f"Sent EnableWidget '{_MR_WIDGET_NAME}' to {len(followers)} follower(s).", Py4GW.Console.MessageType.Info)
            yield from Routines.Yield.wait(1000)

        widget = _get_merchant_rules_widget()
        if widget is None:
            Py4GW.Console.Log(
                BOT_NAME,
                "MerchantRules widget not found after enabling. Skipping inventory refill.",
                Py4GW.Console.MessageType.Warning,
            )
            return

        # ── 1. Travel the leader to the Guild Hall first ──────────────
        if not Map.IsGuildHall():
            Py4GW.Console.Log(BOT_NAME, "Traveling to Guild Hall for MerchantRules.", Py4GW.Console.MessageType.Info)
            Map.TravelGH()
            yield from Routines.Yield.wait(3000)
            elapsed = 0
            while not Map.IsMapReady() and elapsed < _GH_TRAVEL_TIMEOUT_MS:
                yield from Routines.Yield.wait(_POLL_MS)
                elapsed += _POLL_MS

        # ── 2. Tell each follower to travel to their own Guild Hall ──
        if followers:
            Py4GW.Console.Log(BOT_NAME, f"Sending TravelToGuildHall to {len(followers)} follower(s).", Py4GW.Console.MessageType.Info)
            for account in followers:
                target_email = str(account.AccountEmail)
                GLOBAL_CACHE.ShMem.SendMessage(
                    sender_email,
                    target_email,
                    SharedCommandType.TravelToGuildHall,
                    (0, 0, 0, 0),
                )
                yield from Routines.Yield.wait(1500)

        # ── 3. Wait until ALL accounts are on the same map as the leader ─
        leader_map_id = int(Map.GetMapID())
        Py4GW.Console.Log(BOT_NAME, f"Waiting for all accounts to arrive in Guild Hall (map {leader_map_id}).", Py4GW.Console.MessageType.Info)
        elapsed = 0
        all_arrived = False
        while elapsed < _GH_TRAVEL_TIMEOUT_MS:
            all_accounts_fresh = GLOBAL_CACHE.ShMem.GetAllAccountData() or []
            all_arrived = all(
                int(acc.AgentData.Map.MapID) == leader_map_id
                for acc in all_accounts_fresh
            )
            if all_arrived:
                break
            yield from Routines.Yield.wait(_POLL_MS)
            elapsed += _POLL_MS

        if not all_arrived:
            Py4GW.Console.Log(BOT_NAME, "Not all accounts reached the Guild Hall. Continuing anyway.", Py4GW.Console.MessageType.Warning)

        yield from Routines.Yield.wait(2000)

        # ── 4. Execute MerchantRules on the leader (Execute Here) ─────
        Py4GW.Console.Log(BOT_NAME, "Starting MerchantRules Execute Here (leader).", Py4GW.Console.MessageType.Info)
        widget._queue_execute_here()
        yield from Routines.Yield.wait(_POLL_MS)

        elapsed = 0
        while widget.execution_running and elapsed < _EXECUTE_TIMEOUT_MS:
            yield from Routines.Yield.wait(_POLL_MS)
            elapsed += _POLL_MS

        if widget.execution_running:
            Py4GW.Console.Log(BOT_NAME, "MerchantRules leader execution timed out.", Py4GW.Console.MessageType.Warning)
        elif widget.last_error:
            Py4GW.Console.Log(BOT_NAME, f"MerchantRules leader error: {widget.last_error}", Py4GW.Console.MessageType.Warning)
        else:
            Py4GW.Console.Log(BOT_NAME, "MerchantRules leader execution completed.", Py4GW.Console.MessageType.Info)

        # ── 5. Send MerchantRules EXECUTE to all followers ────────────
        if not followers:
            return

        OPCODE_EXECUTE = 3  # MERCHANT_RULES_OPCODE_EXECUTE
        request_id = f"uw_refill_{int(time.monotonic() * 1000)}"
        sent_refs: list[tuple[str, int]] = []

        for account in followers:
            target_email = str(account.AccountEmail)
            msg_idx = GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                target_email,
                SharedCommandType.MerchantRules,
                (float(OPCODE_EXECUTE), 0.0, 0.0, 0.0),
                (request_id, "Execute", "", ""),
            )
            if msg_idx != -1:
                sent_refs.append((target_email, int(msg_idx)))
                Py4GW.Console.Log(
                    BOT_NAME,
                    f"Sent MerchantRules execute to {target_email}.",
                    Py4GW.Console.MessageType.Info,
                )

        if not sent_refs:
            return

        # ── 6. Wait for all follower messages to be consumed ──────────
        from Sources.modular_bot.recipes.combat_engine import outbound_messages_done
        elapsed = 0
        all_done = False
        while elapsed < _FOLLOWER_TIMEOUT_MS:
            all_done = outbound_messages_done(sent_refs, SharedCommandType.MerchantRules)
            if all_done:
                break
            yield from Routines.Yield.wait(_POLL_MS)
            elapsed += _POLL_MS

        if not all_done:
            Py4GW.Console.Log(BOT_NAME, "MerchantRules follower execution timed out on some accounts.", Py4GW.Console.MessageType.Warning)
        else:
            Py4GW.Console.Log(BOT_NAME, "MerchantRules follower execution completed on all accounts.", Py4GW.Console.MessageType.Info)

    bot_instance.Wait.UntilOnOutpost()
    bot_instance.config.FSM.AddYieldRoutineStep(
        name="MerchantRules Inventory Refill",
        coroutine_fn=_coro_merchant_rules_refill,
    )

    # ── Cons restock from Xunlai (after MerchantRules) ──────────────
    if InventorySettings.RestockCons and BotSettings.UseCons:
        _enqueue_cons_restock(bot_instance)


def _enqueue_cons_restock(bot_instance: Botting) -> None:
    """Restock consumables from Xunlai on the leader and broadcast to all followers.
    Called after MerchantRules so everyone is already in the Guild Hall."""
    from Py4GWCoreLib import Inventory

    # Snapshot inactive pcons and their restock quantities at schedule time
    # so we can temporarily zero them out to prevent the built-in restock
    # methods from enabling pcons the user has deactivated.
    _inactive_pcon_qtys: dict[str, int] = {
        p: ConsSettings.get_restock(p)
        for p, _, _, _ in _CONS_DEFS
        if not ConsSettings.is_active(p)
    }

    def _zero_inactive_restock_qty() -> None:
        for prop in _inactive_pcon_qtys:
            if bot_instance.Properties.exists(prop):
                bot_instance.Properties.ApplyNow(prop, "restock_quantity", 0)

    def _restore_inactive_restock_qty() -> None:
        for prop, qty in _inactive_pcon_qtys.items():
            if bot_instance.Properties.exists(prop):
                bot_instance.Properties.ApplyNow(prop, "restock_quantity", qty)

    # Open Xunlai on the leader
    bot_instance.States.AddCustomState(
        lambda: Inventory.OpenXunlaiWindow() if not Inventory.IsStorageOpen() else None,
        "Open Xunlai for Cons Restock",
    )
    bot_instance.Wait.ForTime(1000)

    bot_instance.States.AddCustomState(_zero_inactive_restock_qty, "Zero Inactive Pcon Restock Qty")

    # Restock each consumable on the leader from Xunlai (respects active/qty settings)
    _RESTOCK_METHODS = [
        "BirthdayCupcake", "CandyApple", "Honeycomb", "WarSupplies",
        "EssenceOfCelerity", "GrailOfMight", "ArmorOfSalvation",
        "GoldenEgg", "CandyCorn", "SliceOfPumpkinPie",
        "DrakeKabob", "BowlOfSkalefinSoup", "PahnaiSalad",
    ]
    for method_name in _RESTOCK_METHODS:
        method = getattr(bot_instance.Items.Restock, method_name, None)
        if callable(method):
            method()

    bot_instance.States.AddCustomState(_restore_inactive_restock_qty, "Restore Inactive Pcon Restock Qty")

    # Broadcast restock to all followers (only active pcon quantities)
    conset_qty = max(
        (ConsSettings.get_restock(p) if ConsSettings.is_active(p) else 0)
        for p in ("armor_of_salvation", "essence_of_celerity", "grail_of_might")
    )
    pcon_qty = max(
        (ConsSettings.get_restock(p) if ConsSettings.is_active(p) else 0)
        for p in (
            "birthday_cupcake", "candy_apple", "candy_corn", "golden_egg",
            "slice_of_pumpkin_pie", "honeycomb", "drake_kabob",
            "bowl_of_skalefin_soup", "pahnai_salad", "war_supplies",
        )
    )
    if conset_qty > 0:
        bot_instance.Multibox.RestockConset(conset_qty)
    if pcon_qty > 0:
        bot_instance.Multibox.RestockAllPcons(pcon_qty)
    bot_instance.Wait.ForTime(3000)


def _set_planned_resign() -> None:
    global _planned_resign
    _planned_resign = True


def ResignAndRepeat(bot_instance: Botting):
    bot_instance.States.AddCustomState(_log_successful_run, "Log Successful Run")
    if BotSettings.Repeat:
        bot_instance.States.AddCustomState(_set_planned_resign, "Flag Planned Resign")
        bot_instance.Multibox.ResignParty()
        bot_instance.Wait.ForTime(10000)
        bot_instance.States.AddCustomState(
            lambda: _restart_main_loop(bot_instance, "Successful run"),
            "Restart Main Loop",
        )


def _log_successful_run() -> None:
    """Append a timestamped successful-run entry to the wipe log file."""
    import json as _json
    elapsed_s = max(0, (Map.GetInstanceUptime() - _run_start_uptime_ms) // 1000) if _run_start_uptime_ms else 0
    elapsed_str = f"{elapsed_s // 3600:02d}:{(elapsed_s % 3600) // 60:02d}:{elapsed_s % 60:02d}"
    entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Run completed successfully. Duration: {elapsed_str}\n"
    try:
        with open(_WIPE_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except OSError as exc:
        ConsoleLog(BOT_NAME, f"[Run] Could not write run log: {exc}", Py4GW.Console.MessageType.Warning)
    # Persist per-quest instance uptimes for the avg column.
    if _quest_completion_times:
        for quest_name in _QUEST_ORDER:
            if quest_name in _quest_completion_times:
                elapsed_q = _quest_completion_times[quest_name] // 1000
                _quest_times_log.setdefault(quest_name, []).append(elapsed_q)
        try:
            with open(_QUEST_TIMES_FILE, "w", encoding="utf-8") as f:
                _json.dump(_quest_times_log, f, indent=2)
        except OSError as exc:
            ConsoleLog(BOT_NAME, f"[Run] Could not write quest times log: {exc}", Py4GW.Console.MessageType.Warning)
    ConsoleLog(BOT_NAME, "[Run] Successful run logged.", Py4GW.Console.MessageType.Info)

def Wait_for_Spawns(bot_instance: Botting, x, y):
    _TIMEOUT_S = 20.0

    bot_instance.Move.XY(x, y, "To the Vale")

    def _make_check(label: str):
        """Returns a condition callable that times out after _TIMEOUT_S seconds.
        On timeout: skips the current wait and continues."""
        deadline: float | None = None

        def runtime_check_logic():
            nonlocal deadline
            enemies = [e for e in AgentArray.GetEnemyArray() if Agent.IsAlive(e) and Agent.GetModelID(e) == 2380]

            if not enemies:
                print(f"No Mindblades found - Continuing... ({label})")
                deadline = None  # reset for any future reuse
                return True

            # Start (or keep) the timeout clock
            import time as _time
            now = _time.monotonic()
            if deadline is None:
                deadline = now + _TIMEOUT_S

            if now >= deadline:
                print(f"Mindblades timeout after {_TIMEOUT_S:.0f}s - skipping ({label})")
                deadline = None  # reset so next call restarts the clock
                return True  # unblock the wait and let the bot continue

            print(f"Mindblades ... Waiting. ({label})")
            bot_instance.Move.XY(x, y, "Go Back")
            return False

        return runtime_check_logic

    bot_instance.Wait.UntilCondition(_make_check("1"))
    bot_instance.Wait.ForTime(1000)
    bot_instance.Move.XY(x, y, "1")
    bot_instance.Wait.UntilCondition(_make_check("2"))
    bot_instance.Wait.ForTime(1000)
    bot_instance.Move.XY(x, y, "2")
    bot_instance.Wait.UntilCondition(_make_check("3"))
    bot_instance.Wait.ForTime(1000)
    bot_instance.Move.XY(x, y, "3")
    bot_instance.Wait.UntilCondition(_make_check("4"))


def _draw_help():
    PyImGui.text("Startup widget policy now runs on all active accounts:")

    PyImGui.separator()
    PyImGui.text("Current Status")
    PyImGui.text_wrapped("I'm working on creating a HeroAI version, but there are significant differences.")
    PyImGui.text_wrapped("High risk of getting stuck: 'Unwanted Guests,' 'Dhuum' timing edge cases.")
    PyImGui.text_wrapped("3d pathing in Pits is very rough, may cause getting stuck. Ranged leader works best.")
    PyImGui.text_wrapped("HM is HARDMODE. Never finished a run. Maybe you can?")

    PyImGui.separator()
    PyImGui.text_wrapped("For the Imprisoned Spirits quest, 1 or 2 durable damage dealers are recommended for the left team. You need to figure out which ones.")
    PyImGui.text_wrapped("In the Dhuum battle, 1-2 heroes will die and become ghosts. You can choose which ones.")

    PyImGui.separator()
    PyImGui.text_wrapped("Inventory refill powered by MerchantRules — thanks to Icefox!")


def _draw_inventory_settings() -> None:
    changed = False
    new_val = PyImGui.checkbox("Enable Inventory Refill", InventorySettings.RefillEnabled)
    if new_val != InventorySettings.RefillEnabled:
        InventorySettings.RefillEnabled = new_val
        changed = True
    PyImGui.separator()
    PyImGui.text_wrapped(
        "Travels all accounts to the Guild Hall"
        "Configure buy/sell/deposit rules "
        "in the MerchantRules widget."
    )
    PyImGui.separator()
    PyImGui.begin_disabled(not InventorySettings.RefillEnabled)
    new_val = PyImGui.checkbox("Restock Cons from Xunlai", InventorySettings.RestockCons)
    if new_val != InventorySettings.RestockCons:
        InventorySettings.RestockCons = new_val
        changed = True
    PyImGui.text_wrapped(
        "After MerchantRules finishes: restock consumables from each account's "
        "Xunlai chest based on the Cons tab settings."
    )
    PyImGui.end_disabled()
    if changed:
        InventorySettings.save()


def _draw_imprisoned_spirits_settings() -> None:
    PyImGui.text_wrapped(
        "Assign each multibox account to the Left or Right team for the Imprisoned Spirits quest."
    )
    PyImGui.separator()

    all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    if not all_accounts:
        PyImGui.text("No multibox account data available.")
        return

    ImprisonedSpiritsSettings.apply_defaults_if_empty(all_accounts)

    my_email = Player.GetAccountEmail()

    table_flags = PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersInnerV | PyImGui.TableFlags.BordersOuterH
    if PyImGui.begin_table("##imprisoned_teams", 3, table_flags, 0.0, 0.0):
        PyImGui.table_setup_column("Left",    PyImGui.TableColumnFlags.WidthFixed,   40.0)
        PyImGui.table_setup_column("Right",   PyImGui.TableColumnFlags.WidthFixed,   40.0)
        PyImGui.table_setup_column("Account", PyImGui.TableColumnFlags.WidthStretch, 0.0)
        PyImGui.table_headers_row()

        for account in all_accounts:
            email     = str(account.AccountEmail)
            char_name = str(account.AgentData.CharacterName) or email
            is_self   = email == my_email
            team      = ImprisonedSpiritsSettings.get_team(email)
            team_idx  = 0 if team == "left" else 1

            PyImGui.table_next_row()

            if is_self:
                PyImGui.begin_disabled(True)

            PyImGui.table_next_column()
            new_idx = PyImGui.radio_button(f"##left_{email}", team_idx, 0)

            PyImGui.table_next_column()
            new_idx = PyImGui.radio_button(f"##right_{email}", new_idx, 1)

            PyImGui.table_next_column()
            PyImGui.text(f"{char_name}  (this account)" if is_self else char_name)

            if is_self:
                PyImGui.end_disabled()
            elif new_idx != team_idx:
                ImprisonedSpiritsSettings.set_team(email, "left" if new_idx == 0 else "right")

        PyImGui.end_table()


_ARMOR_JSON_FILE = os.path.join(Py4GW.Console.get_projects_path(), "Widgets", "Config", "EquippedArmor.json")
_ARMOR_SLOT_NAMES = {2: "Chest", 3: "Legs", 4: "Head", 5: "Feet", 6: "Hands"}

_armor_edit_email: str | None = None
_armor_edit_char: str = ""
_armor_edit_normal: dict[str, int] = {}
_armor_edit_sac: dict[str, int] = {}


def _read_armor_json() -> dict:
    try:
        if os.path.exists(_ARMOR_JSON_FILE):
            with open(_ARMOR_JSON_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_armor_json(email: str, normal: dict[str, int], sacrifice: dict[str, int]) -> None:
    try:
        all_armor = _read_armor_json()
        existing = all_armor.get(email, {})
        if not isinstance(existing, dict) or "normal" not in existing:
            existing = {}
        existing["normal"] = normal
        existing["sacrifice"] = sacrifice
        all_armor[email] = existing
        tmp = _ARMOR_JSON_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(all_armor, f, indent=2)
        os.replace(tmp, _ARMOR_JSON_FILE)
    except Exception as e:
        ConsoleLog(BOT_NAME, f"Armor JSON save error: {e}", Py4GW.Console.MessageType.Warning)


def _input_int_val(result: object, current: int) -> int:
    if isinstance(result, tuple) and len(result) > 0:
        return int(result[1]) if len(result) >= 2 else int(result[0])  # type: ignore[return-value]
    if result is None:
        return int(current)
    try:
        return int(result)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return int(current)


def _draw_armor_edit_window() -> None:
    global _armor_edit_email, _armor_edit_char, _armor_edit_normal, _armor_edit_sac
    if _armor_edit_email is None:
        return

    win_flags = PyImGui.WindowFlags.AlwaysAutoResize
    if PyImGui.begin(f"Armor Setup: {_armor_edit_char}##armor_edit", win_flags):
        PyImGui.text_wrapped(f"Account: {_armor_edit_email}")
        PyImGui.text_wrapped("Enter model IDs for normal and sacrifice armor.")
        PyImGui.separator()

        tbl_flags = PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersInnerV | PyImGui.TableFlags.BordersOuterH
        if PyImGui.begin_table("##armor_edit_tbl", 3, tbl_flags, 0.0, 0.0):
            PyImGui.table_setup_column("Slot",      PyImGui.TableColumnFlags.WidthFixed,  80.0)
            PyImGui.table_setup_column("Normal",    PyImGui.TableColumnFlags.WidthFixed, 150.0)
            PyImGui.table_setup_column("Sacrifice", PyImGui.TableColumnFlags.WidthFixed, 150.0)
            PyImGui.table_headers_row()

            for slot in sorted(_ARMOR_SLOT_NAMES):
                slot_str = str(slot)
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text(_ARMOR_SLOT_NAMES[slot])
                PyImGui.table_next_column()
                cur_n = _armor_edit_normal.get(slot_str, 0)
                _armor_edit_normal[slot_str] = _input_int_val(
                    PyImGui.input_int(f"##n{slot}", cur_n, 0, 0, 0), cur_n
                )
                PyImGui.table_next_column()
                cur_s = _armor_edit_sac.get(slot_str, 0)
                _armor_edit_sac[slot_str] = _input_int_val(
                    PyImGui.input_int(f"##s{slot}", cur_s, 0, 0, 0), cur_s
                )

            PyImGui.end_table()

        PyImGui.separator()
        if PyImGui.button("Save##armor_edit"):
            _save_armor_json(_armor_edit_email, dict(_armor_edit_normal), dict(_armor_edit_sac))
            _armor_edit_email = None
        PyImGui.same_line(0.0, 10.0)
        if PyImGui.button("Close##armor_edit"):
            _armor_edit_email = None

    PyImGui.end()


def _draw_dhuum_settings() -> None:
    PyImGui.text_wrapped("Select the multibox accounts to be sacrificed in the Dhuum fight.")
    PyImGui.separator()

    PyImGui.set_next_item_width(100.0)
    new_min = PyImGui.input_int("Min Spiritform accounts", DhuumSettings.MinSpiritformAccounts)
    new_min = max(0, new_min)
    if new_min != DhuumSettings.MinSpiritformAccounts:
        DhuumSettings.MinSpiritformAccounts = new_min
        DhuumSettings.save()
    PyImGui.separator()

    my_email = Player.GetAccountEmail()
    all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()

    if not all_accounts:
        PyImGui.text("No multibox account data available.")
        return

    table_flags = PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersInnerV | PyImGui.TableFlags.BordersOuterH
    if PyImGui.begin_table("##dhuum_settings", 3, table_flags, 0.0, 0.0):
        PyImGui.table_setup_column("Sacrifice",    PyImGui.TableColumnFlags.WidthFixed,   90.0)
        PyImGui.table_setup_column("Switch Armor", PyImGui.TableColumnFlags.WidthFixed,  170.0)
        PyImGui.table_setup_column("Account",      PyImGui.TableColumnFlags.WidthStretch, 0.0)
        PyImGui.table_headers_row()

        for account in all_accounts:
            email     = str(account.AccountEmail)
            char_name = str(account.AgentData.CharacterName) or email
            is_self   = email == my_email

            PyImGui.table_next_row()

            # The executing account cannot sacrifice itself — gray out its row.
            if is_self:
                PyImGui.begin_disabled(True)

            PyImGui.table_next_column()
            cur_sac = DhuumSettings.is_sacrifice(email)
            new_sac = PyImGui.checkbox(f"##sac_{email}", cur_sac)

            PyImGui.table_next_column()
            cur_arm = DhuumSettings.is_armor_switch(email)
            new_arm = PyImGui.checkbox(f"##arm_{email}", cur_arm)
            PyImGui.same_line(0.0, 6.0)
            if PyImGui.button(f"Edit##armedit_{email}"):
                global _armor_edit_email, _armor_edit_char, _armor_edit_normal, _armor_edit_sac
                data = _read_armor_json()
                entry = data.get(email, {})
                _armor_edit_email  = email
                _armor_edit_char   = char_name
                _armor_edit_normal = dict(entry.get("normal", {}))
                _armor_edit_sac    = dict(entry.get("sacrifice", {}))

            PyImGui.table_next_column()
            PyImGui.text(f"{char_name}  (this account)" if is_self else char_name)

            if is_self:
                PyImGui.end_disabled()

            if new_sac != cur_sac:
                DhuumSettings.set_sacrifice(email, new_sac)
            if new_arm != cur_arm:
                DhuumSettings.set_armor_switch(email, new_arm)

        PyImGui.end_table()


def _draw_enter_settings() -> None:
    entrypoint_keys   = list(UW_ENTRYPOINTS.keys())
    entrypoint_labels = [label for label, _ in UW_ENTRYPOINTS.values()]
    current_key = str(EnterSettings.EntryPoint or DEFAULT_UW_ENTRYPOINT_KEY)
    current_idx = entrypoint_keys.index(current_key) if current_key in entrypoint_keys else 0

    PyImGui.text_wrapped("Select the outpost to travel to before using the scroll.")
    PyImGui.separator()
    PyImGui.text("Entry Outpost:")
    new_idx = PyImGui.combo("##uw_entrypoint", current_idx, entrypoint_labels)
    if new_idx != current_idx:
        EnterSettings.EntryPoint = entrypoint_keys[new_idx]
        EnterSettings.save()


def _draw_quest_settings():
    _snapshot = (BotSettings.Repeat, BotSettings.UseCons, BotSettings.HardMode, BotSettings.BotMode)
    BotSettings.Repeat   = PyImGui.checkbox("Resign and Repeat after", BotSettings.Repeat)
    BotSettings.UseCons  = PyImGui.checkbox("Use Cons", BotSettings.UseCons)
    BotSettings.HardMode = PyImGui.checkbox("Hard Mode", BotSettings.HardMode)
    PyImGui.separator()
    PyImGui.text("Bot Mode:")
    mode_idx = 0 if BotSettings.BotMode == "custom_behavior" else 1
    new_mode_idx = PyImGui.radio_button("Custom Behavior##botmode", mode_idx, 0)
    PyImGui.same_line(0, -1)
    new_mode_idx = PyImGui.radio_button("HeroAI (not working)##botmode", new_mode_idx, 1)
    BotSettings.BotMode = "custom_behavior" if new_mode_idx == 0 else "heroai"
    _current = (BotSettings.Repeat, BotSettings.UseCons, BotSettings.HardMode, BotSettings.BotMode)
    if _current != _snapshot:
        BotSettings.save()




bot.SetMainRoutine(bot_routine)

def _draw_debug_settings():
    global _DRAW_BLOCKED_AREAS_3D, _BLOCKED_AREA_RADIUS
    _DRAW_BLOCKED_AREAS_3D = PyImGui.checkbox("Draw Blocked Areas (3D)", _DRAW_BLOCKED_AREAS_3D)
    if _DRAW_BLOCKED_AREAS_3D:
        _BLOCKED_AREA_RADIUS = PyImGui.slider_float("Blocked Area Radius", _BLOCKED_AREA_RADIUS, 50.0, 600.0)

    PyImGui.separator()
    PyImGui.text("Spirit Form (3134) — Active accounts:")
    _SPIRIT_FORM_SKILL_ID = 3134
    _color_has_buff   = Utils.RGBToNormal(100, 255, 100, 255)
    _color_no_buff    = Utils.RGBToNormal(140, 140, 140, 255)
    try:
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData() or []
        current_map_id = Map.GetMapID()
        found_any = False
        for account in accounts:
            if not getattr(account, "IsSlotActive", True):
                continue
            email = str(getattr(account, "AccountEmail", "") or "").strip()
            if not email:
                continue
            in_same_map = getattr(account.AgentData.Map, "MapID", 0) == current_map_id
            has_buff = any(
                b.SkillId == _SPIRIT_FORM_SKILL_ID
                for b in account.AgentData.Buffs.Buffs
                if b.SkillId != 0
            )
            if not has_buff:
                continue
            found_any = True
            # Check if already flagged (in _already_flagged set of the watchdog)
            label = email
            PyImGui.text_colored(f"  {label}", _color_has_buff)
        if not found_any:
            PyImGui.text_colored("  (none)", _color_no_buff)
    except Exception as _e:
        PyImGui.text_colored(f"  Error reading ShMem: {_e}", Utils.RGBToNormal(255, 80, 80, 255))

    PyImGui.separator()
    PyImGui.text("Death Penalty — Party accounts:")
    _color_dp_none   = Utils.RGBToNormal(140, 140, 140, 255)
    _color_dp_low    = Utils.RGBToNormal(255, 220,  60, 255)   # < 15 %
    _color_dp_high   = Utils.RGBToNormal(255,  80,  80, 255)   # >= 15 %
    try:
        _dp_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData() or []
        _dp_found_any = False
        for _dp_acc in _dp_accounts:
            if not getattr(_dp_acc, "IsSlotActive", True):
                continue
            _dp_email = str(getattr(_dp_acc, "AccountEmail", "") or "").strip()
            if not _dp_email:
                continue
            _morale = int(getattr(_dp_acc.AgentData, "Morale", 100) or 100)
            _dp = 100 - _morale
            if _dp <= 0:
                continue
            _dp_found_any = True
            _col = _color_dp_high if _dp >= 15 else _color_dp_low
            PyImGui.text_colored(f"  {_dp_email}  -{_dp}%", _col)
        if not _dp_found_any:
            PyImGui.text_colored("  (no death penalty)", _color_dp_none)
    except Exception as _dp_e:
        PyImGui.text_colored(f"  Error reading ShMem: {_dp_e}", Utils.RGBToNormal(255, 80, 80, 255))

    PyImGui.separator()
    PyImGui.text(f"Watchdog Log (last {_DEBUG_LOG_MAX})")
    if PyImGui.button("Clear##uw_watchdog_log"):
        _debug_watchdog_log.clear()
    if not _debug_watchdog_log:
        PyImGui.text_colored("  (no watchdog entries yet)", _color_no_buff)
    else:
        for entry in list(_debug_watchdog_log)[-20:][::-1]:
            PyImGui.text_wrapped(entry)


def _draw_cons_settings() -> None:
    """Settings tab: per-consumable upkeep toggle and Xunlai restock quantity."""
    PyImGui.text_wrapped(
        "Configure which consumables to upkeep automatically and how many to restock "
        "from the Xunlai chest when the bot visits the guild hall between runs."
    )
    PyImGui.spacing()

    # Group _CONS_DEFS by category, preserving declaration order.
    _seen_cats: list[str] = []
    _by_cat: dict[str, list] = {}
    for _entry in _CONS_DEFS:
        _cat = _entry[2]
        if _cat not in _by_cat:
            _seen_cats.append(_cat)
            _by_cat[_cat] = []
        _by_cat[_cat].append(_entry)

    _tbl_flags = (
        PyImGui.TableFlags.RowBg
        | PyImGui.TableFlags.BordersInnerV
        | PyImGui.TableFlags.BordersOuterH
        | PyImGui.TableFlags.SizingFixedFit
    )

    for _cat in _seen_cats:
        PyImGui.text(_cat)
        PyImGui.separator()
        if PyImGui.begin_table(f"##cons_{_cat}", 3, _tbl_flags, 0.0, 0.0):
            PyImGui.table_setup_column("Active",    PyImGui.TableColumnFlags.WidthFixed,    50.0)
            PyImGui.table_setup_column("Min Stock", PyImGui.TableColumnFlags.WidthFixed,   110.0)
            PyImGui.table_setup_column("Name",      PyImGui.TableColumnFlags.WidthStretch,   0.0)
            PyImGui.table_headers_row()

            for _prop, _dname, _cat2, _def_restock in _by_cat[_cat]:
                _cur_active  = ConsSettings.is_active(_prop)
                _cur_restock = ConsSettings.get_restock(_prop)

                PyImGui.table_next_row()

                # Col 1: active toggle
                PyImGui.table_next_column()
                _new_active = PyImGui.checkbox(f"##ca_{_prop}", _cur_active)
                if _new_active != _cur_active:
                    ConsSettings.set_active(_prop, _new_active)
                    bot.Properties.ApplyNow(_prop, "active", _new_active)

                # Col 2: restock quantity (greyed out when inactive)
                PyImGui.table_next_column()
                PyImGui.begin_disabled(not _cur_active)
                PyImGui.push_item_width(90.0)
                _res         = PyImGui.input_int(f"##cr_{_prop}", _cur_restock, 0, 0, 0)
                _new_restock = _input_int_val(_res, _cur_restock)
                _new_restock = max(0, _new_restock)
                PyImGui.pop_item_width()
                if _new_restock != _cur_restock:
                    ConsSettings.set_restock(_prop, _new_restock)
                    bot.Properties.ApplyNow(_prop, "restock_quantity", _new_restock)
                PyImGui.end_disabled()

                # Col 3: display name
                PyImGui.table_next_column()
                PyImGui.text(_dname)

            PyImGui.end_table()
        PyImGui.spacing()


def _draw_settings():
    if PyImGui.begin_tab_bar("##uw_settings_tabs"):
        if PyImGui.begin_tab_item("General"):
            _draw_quest_settings()
            PyImGui.separator()
            _draw_enter_settings()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Inventory"):
            _draw_inventory_settings()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Cons"):
            _draw_cons_settings()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Imprisoned Spirits"):
            _draw_imprisoned_spirits_settings()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Dhuum"):
            _draw_dhuum_settings()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item("Debug"):
            _draw_debug_settings()
            PyImGui.end_tab_item()
        PyImGui.end_tab_bar()


_WIPE_LOG_FILE = os.path.join(Py4GW.Console.get_projects_path(), "Widgets", "Config", "UnderworldBot_wipes.log")
_QUEST_TIMES_FILE = os.path.join(Py4GW.Console.get_projects_path(), "Widgets", "Config", "UnderworldBot_quest_times.json")

def _load_quest_times_log() -> dict[str, list[int]]:
    """Load per-quest elapsed-second lists from the JSON log, or return empty dict."""
    import json as _json
    try:
        with open(_QUEST_TIMES_FILE, "r", encoding="utf-8") as f:
            data = _json.load(f)
        if isinstance(data, dict):
            return {k: [int(v) for v in vs] for k, vs in data.items() if isinstance(vs, list)}
    except (OSError, ValueError):
        pass
    return {}

_quest_times_log: dict[str, list[int]] = _load_quest_times_log()

def _get_current_header(fsm) -> str:
    """Return the clean name of the nearest preceding [H] header step, or 'unknown'."""
    import re as _re
    try:
        steps = fsm.get_state_names()
        current_idx = fsm.get_current_state_number()
        if current_idx is None or current_idx < 0 or current_idx >= len(steps):
            current_idx = len(steps) - 1
        for i in range(current_idx, -1, -1):
            name = steps[i]
            if name.startswith("[H]"):
                name = _re.sub(r'^\[H\]\s*', '', name)
                name = _re.sub(r'_(?:\[\d+\]|\d+)$', '', name)
                return name
    except Exception:
        pass
    return "unknown"


def _log_wipe_step(fsm) -> None:
    """Append a timestamped wipe entry with the current FSM step name to the wipe log file."""
    step_name = fsm.get_current_step_name()
    header = _get_current_header(fsm)
    # Skip logging when the bot is already past the last quest section (END header).
    # This happens when a resign/map-change after a successful run triggers the wipe
    # callback before the FSM is torn down.
    if header == "END":
        return
    entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Wipe at step: {step_name} [{header}]\n"
    try:
        with open(_WIPE_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except OSError as exc:
        ConsoleLog(BOT_NAME, f"[WIPE] Could not write wipe log: {exc}", Py4GW.Console.MessageType.Warning)
    ConsoleLog(BOT_NAME, f"[WIPE] Logged wipe at step: {step_name} [{header}]", Py4GW.Console.MessageType.Warning)


def OnPartyWipe(bot: "Botting"):
    global _planned_resign
    if _planned_resign:
        _planned_resign = False
        ConsoleLog(BOT_NAME, "[WIPE] Party wipe after planned resign – ignored.", Py4GW.Console.MessageType.Info)
        return
    fsm = bot.config.FSM
    _log_wipe_step(fsm)
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_Underworld", lambda: _on_party_wipe(bot))


def _on_party_wipe(bot: "Botting"):
    ConsoleLog(BOT_NAME, "[WIPE] Party wipe detected!", Py4GW.Console.MessageType.Warning)

    while True:
        yield from Routines.Yield.wait(1000)

        # Check map validity FIRST: during the wipe transport Player.GetAgentID()
        # returns 0, causing Agent.IsDead(0) to return False (invalid agent → not dead).
        # Without this guard the while loop would exit prematurely and resume the FSM
        # mid-transition, leading to a crash.
        if not Routines.Checks.Map.MapValid():
            ConsoleLog(BOT_NAME, "[WIPE] Returned to outpost after wipe, restarting run...", Py4GW.Console.MessageType.Warning)
            yield from Routines.Yield.wait(3000)
            # Do NOT call _restart_main_loop() here — we are inside FSM.update()'s
            # managed-coroutines loop, so calling fsm.resume() would un-pause the FSM
            # mid-loop and allow execute() to run with a potentially stale current_state.
            # Instead, flag main() to do the restart before the next bot.Update().
            _request_wipe_restart("Returned to outpost after wipe")
            return

        player_id = Player.GetAgentID()
        if not Agent.IsValid(player_id):
            # Agent not yet available during map transition — keep waiting.
            continue

        if not Agent.IsDead(player_id):
            ConsoleLog(BOT_NAME, "[WIPE] Player resurrected in instance, resuming...", Py4GW.Console.MessageType.Info)
            _request_wipe_restart("Player resurrected in instance")
            return


def _draw_run_log() -> None:
    """Display the last 10 entries from the wipe/run log file."""
    if PyImGui.button("Clear Log##run_log"):
        try:
            with open(_WIPE_LOG_FILE, "w", encoding="utf-8") as f:
                f.truncate(0)
        except OSError:
            pass
    PyImGui.same_line(0, -1)
    PyImGui.text(_WIPE_LOG_FILE)
    PyImGui.separator()
    try:
        with open(_WIPE_LOG_FILE, "r", encoding="utf-8") as f:
            lines = [l.rstrip("\n") for l in f.readlines() if l.strip()]
        last_10 = lines[-10:] if len(lines) > 10 else lines
        if not last_10:
            PyImGui.text_wrapped("(log is empty)")
        else:
            for line in reversed(last_10):
                PyImGui.text_wrapped(line)
    except FileNotFoundError:
        PyImGui.text_wrapped("(no log file yet — wipes and completed runs will appear here)")
    except OSError as exc:
        PyImGui.text_wrapped(f"Error reading log: {exc}")


def _log_crash(exc: BaseException, tb: str) -> None:
    """Append a timestamped crash entry with the full traceback to the log file."""
    step_name = "unknown"
    header = "unknown"
    try:
        step_name = bot.config.FSM.get_current_step_name()
        header = _get_current_header(bot.config.FSM)
    except Exception:
        pass
    entry = (
        f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] CRASH at step: {step_name} [{header}]\n"
        f"  {type(exc).__name__}: {exc}\n"
    )
    for line in tb.splitlines():
        entry += f"  {line}\n"
    entry += "\n"
    try:
        with open(_WIPE_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except OSError:
        pass  # Nothing we can do if the file itself fails


def _draw_main_additional_ui() -> None:
    """Rendered in the Main tab below the progress bars."""
    _color_done    = Utils.RGBToNormal(100, 255, 100, 255)
    _color_pending = Utils.RGBToNormal(140, 140, 140, 255)
    _color_avg     = Utils.RGBToNormal(255, 210, 80, 255)
    PyImGui.text("Quest Progress")
    if PyImGui.begin_table(
        "##uw_quest_table", 3,
        PyImGui.TableFlags.RowBg
        | PyImGui.TableFlags.BordersOuterH
        | PyImGui.TableFlags.BordersOuterV
        | PyImGui.TableFlags.BordersInnerV,
    ):
        PyImGui.table_setup_column("Quest", PyImGui.TableColumnFlags.WidthStretch)
        PyImGui.table_setup_column("Time",  PyImGui.TableColumnFlags.WidthFixed, 72)
        PyImGui.table_setup_column("Avg",   PyImGui.TableColumnFlags.WidthFixed, 72)
        PyImGui.table_headers_row()
        for quest_name in _QUEST_ORDER:
            PyImGui.table_next_row()
            PyImGui.table_set_column_index(0)
            done = quest_name in _quest_completion_times
            PyImGui.text_colored(quest_name, _color_done if done else _color_pending)
            PyImGui.table_set_column_index(1)
            history = _quest_times_log.get(quest_name, [])
            recent = history[-5:] if history else []
            avg_s = int(sum(recent) / len(recent)) if recent else None
            if done:
                uptime_s = _quest_completion_times[quest_name] // 1000
                h, rem = divmod(uptime_s, 3600)
                m, s = divmod(rem, 60)
                if avg_s is None:
                    time_color = _color_done
                elif uptime_s <= avg_s:
                    time_color = Utils.RGBToNormal(100, 255, 100, 255)
                else:
                    time_color = Utils.RGBToNormal(255, 80, 80, 255)
                PyImGui.text_colored(f"{h:02d}:{m:02d}:{s:02d}", time_color)
            else:
                PyImGui.text_colored("--:--:--", _color_pending)
            PyImGui.table_set_column_index(2)
            if avg_s is not None:
                ah, arem = divmod(avg_s, 3600)
                am, as_ = divmod(arem, 60)
                PyImGui.text_colored(f"{ah:02d}:{am:02d}:{as_:02d}", _color_avg)
            else:
                PyImGui.text_colored("--:--:--", _color_pending)
        PyImGui.end_table()


def main():
    global _pending_wipe_recovery, _pending_wipe_reason
    import traceback as _tb
    try:
        _draw_blocked_areas_overlay()

        _draw_armor_edit_window()
        if bot.config.fsm_running and Routines.Checks.Map.MapValid():
            _get_adapter().sync_runtime()
            # Watchdog: callback sometimes misses wipes — detect return to outpost by map ID
            if _entered_dungeon and Map.GetMapID() == 138:
                ConsoleLog(BOT_NAME, "[WIPE] Watchdog: back in outpost (map 138) without wipe callback — restarting.", Py4GW.Console.MessageType.Warning)
                _restart_main_loop(bot, "Watchdog: returned to map 138")
        # If a wipe-recovery was requested by a managed coroutine, perform the FSM
        # restart here — safely outside FSM.update()'s managed-coroutines loop.
        if _pending_wipe_recovery:
            _pending_wipe_recovery = False
            _restart_main_loop(bot, _pending_wipe_reason)

        # Re-register UW-specific managed coroutines every frame so they
        # survive FSM.restart() which clears the managed_coroutines list.
        if bot.config.fsm_running:
            _ensure_managed_coroutines(bot)

        # Guard: skip game-state logic when the map is not loaded
        # (e.g., character select screen) to prevent reading invalid GW memory.
        # bot_routine() is called by bot.Update() on the first frame and accesses
        # the player's skillbar, which crashes the game if no character is in-game.
        if Routines.Checks.Map.MapValid():
            bot.Update()
        bot.UI.draw_window(
            icon_path=os.path.join(Py4GW.Console.get_projects_path(), MODULE_ICON),
            main_child_dimensions=(350, 570),
            additional_ui=_draw_main_additional_ui,
            extra_tabs=[("Run Log", _draw_run_log)],
        )
    except ValueError as exc:
        # CoreLib bug: FSM.update()'s except-StopIteration handler calls
        # managed_coroutines.remove(routine) without a try/except.  If the
        # routine was already removed from the list (rare edge case triggered
        # by _start_coroutines() or a wipe callback), the remove raises
        # ValueError.  The routine won't be in the next snapshot so the error
        # is self-healing — we just must not let it crash the script.
        if "list.remove" in str(exc):
            ConsoleLog(BOT_NAME,
                       "[WARN] Transient FSM coroutine list error (non-fatal) — bot continues.",
                       Py4GW.Console.MessageType.Warning)
        else:
            _log_crash(exc, _tb.format_exc())
            raise
    except Exception as exc:
        _log_crash(exc, _tb.format_exc())
        raise

if __name__ == "__main__":
    main()