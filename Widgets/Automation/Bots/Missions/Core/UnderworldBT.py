
# ╔══════════════════════════════════════════════════════════════════════════════
# ║  File    : UnderworldBT.py
# ║  Purpose : BehaviorTree port of the Underworld bot.
# ║            BehaviorTree planner, parallel services, stats UI.
# ╚══════════════════════════════════════════════════════════════════════════════

import enum
import json
import math
import os
import time
from collections import deque

import Py4GW
import PyImGui
from Py4GWCoreLib import Agent, GLOBAL_CACHE, ConsoleLog, IniHandler, Map, Player, Range, Routines, Utils
from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.enums_src.Map_enums import name_to_map_id
from Py4GWCoreLib.native_src.internals.types import Vec2f

# ── Module identity ───────────────────────────────────────────────────────────
MODULE_NAME = 'UnderworldBT'
MODULE_ICON = 'Textures/Module_Icons/Underworld.png'
BOT_NAME    = 'UnderworldBT'

# ── Persistent configuration ──────────────────────────────────────────────────
_ini_file = os.path.join(Py4GW.Console.get_projects_path(), 'Widgets', 'Config', 'UnderworldBT.ini')
_ini = IniHandler(_ini_file)


# ╔══════════════════════════════════════════════════════════════════════════════
# ║  SETTINGS
# ╚══════════════════════════════════════════════════════════════════════════════

def _read_emails_set(key: str) -> set[str]:
    return {e.strip() for e in _ini.read_key(BOT_NAME, key, '').split(';') if e.strip()}

def _read_emails_list(key: str) -> list[str]:
    return [e.strip() for e in (_ini.read_key(BOT_NAME, key, '') or '').split(';') if e.strip()]


# ── General / Run ─────────────────────────────────────────────────────────────
class BotSettings:
    """General run settings (repeat, cons, hard mode)."""
    Repeat:   bool = bool(_ini.read_bool(BOT_NAME, 'quest_repeat',   False))
    UseCons:  bool = bool(_ini.read_bool(BOT_NAME, 'quest_use_cons', True))
    HardMode: bool = bool(_ini.read_bool(BOT_NAME, 'quest_hardmode', False))

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, 'quest_repeat',   str(cls.Repeat))
        _ini.write_key(BOT_NAME, 'quest_use_cons', str(cls.UseCons))
        _ini.write_key(BOT_NAME, 'quest_hardmode', str(cls.HardMode))



# ── Entry point ───────────────────────────────────────────────────────────────
UW_MAP_ID = 72


class UWBlacklistName:
    """Display names for HeroAI EnemyBlacklist (name-based — requires stable TextParser)."""
    BanishedDreamRider     = 'Banished Dream Rider'
    ObsidianBehemoth       = 'Obsidian Behemoth'
    SpiritOfNaturesRenewal = "Nature's Renewal"
    ChainedSoul            = 'Chained Soul'
    ObsidianGuardian       = 'Obsidian Guardian'
    TorturedSpirit         = 'Tortured Spirit'  # covers Friendly + alt variants (same display name)
    VengefulAatxe          = 'Vengeful Aatxe'


# Model IDs kept ONLY for BehemothGuard agent-detection logic (not for blacklisting).
UW_BEHEMOTH_GUARD_MODEL_IDS: frozenset[int] = frozenset({2369, 2938})

UW_BEHEMOTH_GUARD_NAMES: tuple[str, ...] = (
    UWBlacklistName.ObsidianBehemoth,
    UWBlacklistName.SpiritOfNaturesRenewal,
)

UW_TORTURED_SPIRIT_NAMES: tuple[str, ...] = (
    UWBlacklistName.TorturedSpirit,
)

# Spectral Mindblade spawn wait in Restore Planes (not blacklisted)
_UW_SPECTRAL_MINDBLADE_MODEL_ID = 2380
UW_SCROLL_MODEL_ID = 3746  # ModelID.Passage_Scroll_Uw
_SCROLL_TRADER_NAME = 'Scroll Trader'
_SCROLL_TRADER_MODEL_ID = 207      # Guild Hall Scroll Trader
_SCROLL_TRADER_APPROACH_DIST = 220.0  # stop short of NPC collision (Adjacent ~= 166)
_SCROLL_TRADER_MOVE_TOLERANCE = 200.0
DEFAULT_UW_ENTRYPOINT_KEY = 'embark_beach'
UW_ENTRYPOINTS: dict[str, tuple[str, int]] = {
    'embark_beach':       ('Embark Beach',       int(name_to_map_id['Embark Beach'])),
    'temple_of_the_ages': ('Temple of the Ages', int(name_to_map_id['Temple of the Ages'])),
    'chantry_of_secrets': ('Chantry of Secrets', int(name_to_map_id['Chantry of Secrets'])),
    'zin_ku_corridor':    ('Zin Ku Corridor',     int(name_to_map_id['Zin Ku Corridor'])),
}

# Underworld enemies ordered from highest to lowest party-call priority (UnderworldV2 + tracker).
# Omitted on purpose: Chained Soul, Tortured Spirit, Spirit of Nature's Renewal (bot blacklists),
# Dire/Hearty Black Widow (trash).
UW_TARGET_PRIORITY: list[str] = [
    # Quest / high-value targets
    'Keeper of Souls',
    'Skeleton of Dhuum',
    'Terrorweb Queen',
    'Ghozer Dhuum',
    'Kazhad Dhuum',
    'Madruk Dhuum',
    'Thul Za Dhuum',
    'Wailing Lord',
    'Terrorweb Dryder',
    'Mindblade Spectre',
    'Banished Dream Rider',
    'Dead Collector',
    'Dead Thresher',
    # Nightmare / Aatxe packs
    'Grasping Darkness',
    'Charged Blackness',
    'Coldfire Night',
    'Stalking Night',
    'Dying Nightmare',
    'Bladed Aatxe',
    'Vengeful Aatxe',
    # General UW mobs
    'Smite Crawler',
    'Bone Horror',
    'Obsidian Guardian',
    # Dhuum fight (Dhuum Helper still handles CB; low priority fallback)
    'Champion of Dhuum',
    'Slayer',
    'Minion of Dhuum',
    'Dhuum',
    # Behemoth last — usually blacklisted until BehemothGuard engages
    'Obsidian Behemoth',
]
_UW_PRIORITY_TARGET_RANGE = Range.Earshot.value + 100.0
_UW_PRIORITY_TARGET_COOLDOWN_MS = 2000.0
_UW_PRIORITY_TARGET_SCAN_INTERVAL_MS = 500.0

class EnterSettings:
    """Entry outpost used before activating the UW scroll."""
    EntryPoint: str = str(
        _ini.read_key(BOT_NAME, 'enter_entrypoint', DEFAULT_UW_ENTRYPOINT_KEY)
        or DEFAULT_UW_ENTRYPOINT_KEY
    )

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, 'enter_entrypoint', str(cls.EntryPoint))


# ── Inventory refill ──────────────────────────────────────────────────────────
class InventorySettings:
    """Between-run inventory management (MerchantRules + Xunlai restock)."""
    RefillEnabled: bool = bool(_ini.read_bool(BOT_NAME, 'inv_refill_enabled', True))
    RestockCons:   bool = bool(_ini.read_bool(BOT_NAME, 'inv_restock_cons',   True))
    BuyUWScrolls:  bool = bool(_ini.read_bool(BOT_NAME, 'inv_buy_uw_scrolls', False))
    UWScrollMin:   int = max(0, int(_ini.read_int(BOT_NAME, 'inv_uw_scroll_min', 1) or 1))
    UWScrollMax:   int = max(
        UWScrollMin,
        max(0, int(_ini.read_int(BOT_NAME, 'inv_uw_scroll_max', 2) or 2)),
    )

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, 'inv_refill_enabled', str(cls.RefillEnabled))
        _ini.write_key(BOT_NAME, 'inv_restock_cons',   str(cls.RestockCons))
        _ini.write_key(BOT_NAME, 'inv_buy_uw_scrolls', str(cls.BuyUWScrolls))
        _ini.write_key(BOT_NAME, 'inv_uw_scroll_min',  str(max(0, int(cls.UWScrollMin))))
        _ini.write_key(BOT_NAME, 'inv_uw_scroll_max',  str(max(0, int(cls.UWScrollMax))))


# ── Consumables ───────────────────────────────────────────────────────────────
# Each entry: (ini_key, display_name, category, default_restock_quantity)
_CONS_DEFS: list[tuple[str, str, str, int]] = [
    # Conset
    ('armor_of_salvation',    'Armor of Salvation',    'Conset', 4),
    ('essence_of_celerity',   'Essence of Celerity',   'Conset', 4),
    ('grail_of_might',        'Grail of Might',        'Conset', 4),
    # War
    ('war_supplies',          'War Supplies',           'War',   4),
    # Food
    ('drake_kabob',           'Drake Kabob',            'Food',  4),
    ('bowl_of_skalefin_soup', 'Bowl of Skalefin Soup', 'Food',  4),
    ('pahnai_salad',          'Pahnai Salad',           'Food',  4),
    # Sweet
    ('candy_corn',            'Candy Corn',             'Sweet', 4),
    ('candy_apple',           'Candy Apple',            'Sweet', 4),
    ('birthday_cupcake',      'Birthday Cupcake',       'Sweet', 4),
    ('golden_egg',            'Golden Egg',             'Sweet', 4),
    ('slice_of_pumpkin_pie',  'Pumpkin Pie',            'Sweet', 4),
    ('honeycomb',             'Honeycomb',              'Sweet', 4),
]

class ConsSettings:
    """Active flag and Xunlai-restock quantity for every upkeep-able consumable."""
    _active:  dict[str, bool] = {
        p: bool(_ini.read_bool(BOT_NAME, f'cons_{p}_active', True))
        for p, _, _, _ in _CONS_DEFS
    }
    _restock: dict[str, int] = {
        p: int(_ini.read_int(BOT_NAME, f'cons_{p}_restock', dr))
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
            _ini.write_key(BOT_NAME, f'cons_{prop}_active',  str(cls._active.get(prop, True)))
            _ini.write_key(BOT_NAME, f'cons_{prop}_restock', str(cls._restock.get(prop, 0)))


# ── Dhuum fight ───────────────────────────────────────────────────────────────
_KING_FROZENWIND_MODEL_ID = 2403
_KING_FROZENWIND_DEST_X      = -11278.0   # where the King stops walking
_KING_FROZENWIND_DEST_Y      =  17297.0
_KING_FROZENWIND_DEST_RADIUS = 1500.0     # how close he must be to count as "arrived"
_KING_FROZENWIND_FOLLOW_RADIUS = 1000.0   # max distance before we move to keep up
_KING_FROZENWIND_TIMEOUT_S   = 600.0      # 10-min hard timeout

class DhuumSettings:
    """Sacrifice account assignments for the Dhuum fight."""
    SacrificeEmails:       set[str] = _read_emails_set('dhuum_sacrifice_emails')
    MinSpiritformAccounts: int      = int(_ini.read_int(BOT_NAME, 'dhuum_min_spiritform', 2))

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, 'dhuum_sacrifice_emails', ';'.join(sorted(cls.SacrificeEmails)))
        _ini.write_key(BOT_NAME, 'dhuum_min_spiritform',   str(cls.MinSpiritformAccounts))

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

# ── Imprisoned Spirits teams ──────────────────────────────────────────────────
class ImprisonedSpiritsSettings:
    """Left / right team assignments for the Imprisoned Spirits quest."""
    LeftTeamEmails:  list[str] = _read_emails_list('imprisoned_left_emails')
    RightTeamEmails: list[str] = _read_emails_list('imprisoned_right_emails')

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, 'imprisoned_left_emails',  ';'.join(cls.LeftTeamEmails))
        _ini.write_key(BOT_NAME, 'imprisoned_right_emails', ';'.join(cls.RightTeamEmails))

    @classmethod
    def get_team(cls, email: str) -> str:
        return 'left' if email in cls.LeftTeamEmails else 'right'

    @classmethod
    def set_team(cls, email: str, team: str) -> None:
        cls.LeftTeamEmails  = [e for e in cls.LeftTeamEmails  if e != email]
        cls.RightTeamEmails = [e for e in cls.RightTeamEmails if e != email]
        if team == 'left':
            cls.LeftTeamEmails.append(email)
        else:
            cls.RightTeamEmails.append(email)
        cls.save()

    @classmethod
    def apply_defaults_if_empty(cls, accounts: list) -> None:
        if cls.LeftTeamEmails or cls.RightTeamEmails:
            return
        emails = [str(a.AccountEmail) for a in accounts]
        cls.LeftTeamEmails  = emails[:3]
        cls.RightTeamEmails = emails[3:]
        cls.save()


# ╔══════════════════════════════════════════════════════════════════════════════
# ║  RUNTIME STATE
# ╚══════════════════════════════════════════════════════════════════════════════

_QUEST_ORDER: list[str] = [
    'Enter Underworld',
    'Clear the Chamber',
    'Pass the Mountains',
    'Restore Mountains',
    'Deamon Assassin',
    'Restore Planes',
    'The Four Horsemen',
    'Restore Pools',
    'Terrorweb Queen',
    'Restore Pit',
    'Imprisoned Spirits',
    'Restore Vale',
    'Wrathfull Spirits',
    'Unwanted Guests',
    'Restore Wastes',
    'Servants of Grenth',
    'Dhuum',
    'Loot Chest',
]



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


# Explorable UW quest steps (derived from planner order; excludes entry + loot).
_UW_EXPLORABLE_STEPS: frozenset[str] = frozenset(
    q for q in _QUEST_ORDER if q not in ('Enter Underworld', 'Loot Chest')
)


_quest_completion_times: dict[str, int] = {}
_DEBUG_LOG_MAX = 120
_debug_watchdog_log: deque[str] = deque(maxlen=_DEBUG_LOG_MAX)
_SPIRIT_FORM_SKILL_ID = 3134

# ── Log files ─────────────────────────────────────────────────────────────────
_WIPE_LOG_FILE    = os.path.join(Py4GW.Console.get_projects_path(), 'Widgets', 'Config', 'UnderworldBT_wipes.log')
_QUEST_TIMES_FILE = os.path.join(Py4GW.Console.get_projects_path(), 'Widgets', 'Config', 'UnderworldBT_quest_times.json')
_WIPE_COUNTS_FILE = os.path.join(Py4GW.Console.get_projects_path(), 'Widgets', 'Config', 'UnderworldBT_wipe_counts.json')


def _load_quest_times_log() -> dict[str, list[int]]:
    try:
        with open(_QUEST_TIMES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {k: [int(v) for v in vs] for k, vs in data.items() if isinstance(vs, list)}
    except (OSError, ValueError):
        pass
    return {}


_quest_times_log: dict[str, list[int]] = _load_quest_times_log()


def _load_wipe_counts() -> dict[str, int]:
    try:
        with open(_WIPE_COUNTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {k: int(v) for k, v in data.items() if isinstance(v, (int, float))}
    except (OSError, ValueError):
        pass
    return {}


def _save_wipe_counts() -> None:
    try:
        os.makedirs(os.path.dirname(_WIPE_COUNTS_FILE), exist_ok=True)
        with open(_WIPE_COUNTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(_wipe_counts_log, f, indent=2)
    except OSError:
        pass


_wipe_counts_log: dict[str, int] = _load_wipe_counts()

# ── Step timer ────────────────────────────────────────────────────────────────
# Timer starts when 'Clear the Chamber' begins.  Each step's recorded value is
# the cumulative elapsed seconds from that moment until the step completed.
# 'Enter Underworld' is intentionally excluded from timing.
_RUN_START_QUEST  = 'Clear the Chamber'
_TIMED_QUESTS: frozenset[str] = frozenset(_QUEST_ORDER[1:])  # all except 'Enter Underworld'
_timing_state: dict = {
    'run_start_ms': None,   # monotonic ms when Clear the Chamber started
    'last_step':    '',     # previous current_step_name value
}


def _save_quest_times_log() -> None:
    try:
        os.makedirs(os.path.dirname(_QUEST_TIMES_FILE), exist_ok=True)
        with open(_QUEST_TIMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(_quest_times_log, f, indent=2)
    except OSError:
        pass


def _append_run_log(message: str) -> None:
    """Append a timestamped line to the run log file (shown in the Run Log tab)."""
    try:
        os.makedirs(os.path.dirname(_WIPE_LOG_FILE), exist_ok=True)
        ts = time.strftime('%Y-%m-%d %H:%M:%S')
        with open(_WIPE_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f'[{ts}] {message}\n')
    except OSError:
        pass



# ╔══════════════════════════════════════════════════════════════════════════════
# ║  HELPERS
# ╚══════════════════════════════════════════════════════════════════════════════

def _input_int_val(result: object, current: int) -> int:
    if isinstance(result, tuple) and len(result) > 0:
        return int(result[1]) if len(result) >= 2 else int(result[0])  # type: ignore[return-value]
    if result is None:
        return int(current)
    try:
        return int(result)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return int(current)


# ╔══════════════════════════════════════════════════════════════════════════════
# ║  DRAW FUNCTIONS
# ╚══════════════════════════════════════════════════════════════════════════════

def _draw_help() -> None:
    PyImGui.text('Startup widget policy now runs on all active accounts:')

    PyImGui.separator()
    PyImGui.text('Current Status')
    PyImGui.text_wrapped("I'm working on creating a HeroAI version, but there are significant differences.")
    PyImGui.text_wrapped("High risk of getting stuck: 'Unwanted Guests,' 'Dhuum' timing edge cases.")
    PyImGui.text_wrapped('3d pathing in Pits is very rough, may cause getting stuck. Ranged leader works best.')
    PyImGui.text_wrapped('HM is HARDMODE. Never finished a run. Maybe you can?')

    PyImGui.separator()
    PyImGui.text_wrapped(
        'For the Imprisoned Spirits quest, 1 or 2 durable damage dealers are recommended for the left team. '
        'You need to figure out which ones.'
    )
    PyImGui.text_wrapped('In the Dhuum battle, 1-2 heroes will die and become ghosts. You can choose which ones.')

    PyImGui.separator()
    PyImGui.text_wrapped('Inventory refill powered by MerchantRules — thanks to Icefox!')


def _draw_quest_settings() -> None:
    _snapshot = (BotSettings.Repeat, BotSettings.UseCons, BotSettings.HardMode)
    BotSettings.Repeat   = PyImGui.checkbox('Resign and Repeat after', BotSettings.Repeat)
    BotSettings.UseCons  = PyImGui.checkbox('Use Cons', BotSettings.UseCons)
    BotSettings.HardMode = PyImGui.checkbox('Hard Mode', BotSettings.HardMode)
    PyImGui.separator()
    PyImGui.text('Bot Mode: HeroAI')
    if (BotSettings.Repeat, BotSettings.UseCons, BotSettings.HardMode) != _snapshot:
        BotSettings.save()



def _draw_enter_settings() -> None:
    entrypoint_keys   = list(UW_ENTRYPOINTS.keys())
    entrypoint_labels = [label for label, _ in UW_ENTRYPOINTS.values()]
    current_key = str(EnterSettings.EntryPoint or DEFAULT_UW_ENTRYPOINT_KEY)
    current_idx = entrypoint_keys.index(current_key) if current_key in entrypoint_keys else 0

    PyImGui.text_wrapped('Select the outpost to travel to before using the scroll.')
    PyImGui.separator()
    PyImGui.text('Entry Outpost:')
    new_idx = PyImGui.combo('##uw_entrypoint', current_idx, entrypoint_labels)
    if new_idx != current_idx:
        EnterSettings.EntryPoint = entrypoint_keys[new_idx]
        EnterSettings.save()


def _draw_inventory_settings() -> None:
    changed = False
    new_val = PyImGui.checkbox('Enable Inventory Refill', InventorySettings.RefillEnabled)
    if new_val != InventorySettings.RefillEnabled:
        InventorySettings.RefillEnabled = new_val
        changed = True
    PyImGui.separator()
    PyImGui.text_wrapped(
        'Travels all accounts to the Guild Hall. '
        'Configure buy/sell/deposit rules in the MerchantRules widget.'
    )
    PyImGui.separator()
    PyImGui.begin_disabled(not InventorySettings.RefillEnabled)
    new_val = PyImGui.checkbox('Restock Cons from Xunlai', InventorySettings.RestockCons)
    if new_val != InventorySettings.RestockCons:
        InventorySettings.RestockCons = new_val
        changed = True
    PyImGui.text_wrapped(
        "After MerchantRules finishes: restock consumables from each account's "
        'Xunlai chest based on the Cons tab settings.'
    )
    PyImGui.end_disabled()
    PyImGui.separator()
    new_val = PyImGui.checkbox('Buy UW scrolls at Scroll Trader (Guild Hall)', InventorySettings.BuyUWScrolls)
    if new_val != InventorySettings.BuyUWScrolls:
        InventorySettings.BuyUWScrolls = new_val
        changed = True
    PyImGui.begin_disabled(not InventorySettings.BuyUWScrolls)
    _uw_scroll_input_w = 56.0
    PyImGui.text('Min')
    PyImGui.same_line(0, 4)
    PyImGui.push_item_width(_uw_scroll_input_w)
    new_min = max(0, _input_int_val(PyImGui.input_int('##uw_scroll_min', InventorySettings.UWScrollMin, 0, 0, 0), InventorySettings.UWScrollMin))
    PyImGui.pop_item_width()
    PyImGui.same_line(0, 12)
    PyImGui.text('Max')
    PyImGui.same_line(0, 4)
    PyImGui.push_item_width(_uw_scroll_input_w)
    new_max = max(0, _input_int_val(PyImGui.input_int('##uw_scroll_max', InventorySettings.UWScrollMax, 0, 0, 0), InventorySettings.UWScrollMax))
    PyImGui.pop_item_width()
    current_uw_scrolls = int(GLOBAL_CACHE.Inventory.GetModelCount(int(UW_SCROLL_MODEL_ID)) or 0)
    PyImGui.same_line(0, 12)
    _scroll_now_label = f'Now: {current_uw_scrolls}'
    if current_uw_scrolls < new_min:
        PyImGui.text_colored(_scroll_now_label, Utils.RGBToNormal(255, 80, 80, 255))
    elif current_uw_scrolls >= new_max:
        PyImGui.text_colored(_scroll_now_label, Utils.RGBToNormal(100, 255, 100, 255))
    else:
        PyImGui.text_colored(_scroll_now_label, Utils.RGBToNormal(200, 200, 200, 255))
    if new_max < new_min:
        new_max = new_min
    if new_min != InventorySettings.UWScrollMin:
        InventorySettings.UWScrollMin = new_min
        changed = True
    if new_max != InventorySettings.UWScrollMax:
        InventorySettings.UWScrollMax = new_max
        changed = True
    PyImGui.end_disabled()
    if changed:
        InventorySettings.save()


def _draw_cons_settings() -> None:
    PyImGui.text_wrapped(
        'Configure which consumables to upkeep automatically and how many to restock '
        'from the Xunlai chest when the bot visits the guild hall between runs. '
        'During a run, checked items are kept up in explorable areas by a single background '
        'ConsumableUpkeep service (round-robin per item; requires *Use Cons* on the Run tab).'
    )
    PyImGui.spacing()

    _seen_cats: list[str] = []
    _by_cat: dict[str, list] = {}
    for entry in _CONS_DEFS:
        cat = entry[2]
        if cat not in _by_cat:
            _seen_cats.append(cat)
            _by_cat[cat] = []
        _by_cat[cat].append(entry)

    tbl_flags = (
        PyImGui.TableFlags.RowBg
        | PyImGui.TableFlags.BordersInnerV
        | PyImGui.TableFlags.BordersOuterH
        | PyImGui.TableFlags.SizingFixedFit
    )

    for cat in _seen_cats:
        PyImGui.text(cat)
        PyImGui.separator()
        if PyImGui.begin_table(f'##cons_{cat}', 3, tbl_flags, 0.0, 0.0):
            PyImGui.table_setup_column('Active',    PyImGui.TableColumnFlags.WidthFixed,   50.0)
            PyImGui.table_setup_column('Min Stock', PyImGui.TableColumnFlags.WidthFixed,  110.0)
            PyImGui.table_setup_column('Name',      PyImGui.TableColumnFlags.WidthStretch,  0.0)
            PyImGui.table_headers_row()

            for prop, dname, _, _ in _by_cat[cat]:
                cur_active  = ConsSettings.is_active(prop)
                cur_restock = ConsSettings.get_restock(prop)

                PyImGui.table_next_row()

                PyImGui.table_next_column()
                new_active = PyImGui.checkbox(f'##ca_{prop}', cur_active)
                if new_active != cur_active:
                    ConsSettings.set_active(prop, new_active)

                PyImGui.table_next_column()
                PyImGui.begin_disabled(not cur_active)
                PyImGui.push_item_width(90.0)
                new_restock = max(0, _input_int_val(PyImGui.input_int(f'##cr_{prop}', cur_restock, 0, 0, 0), cur_restock))
                PyImGui.pop_item_width()
                if new_restock != cur_restock:
                    ConsSettings.set_restock(prop, new_restock)
                PyImGui.end_disabled()

                PyImGui.table_next_column()
                PyImGui.text(dname)

        PyImGui.end_table()
        PyImGui.spacing()


def _draw_dhuum_settings() -> None:
    PyImGui.text_wrapped('Select the multibox accounts to be sacrificed in the Dhuum fight.')
    PyImGui.separator()

    PyImGui.set_next_item_width(100.0)
    new_min = max(0, _input_int_val(
        PyImGui.input_int('Min Spiritform accounts', DhuumSettings.MinSpiritformAccounts, 0, 0, 0),
        DhuumSettings.MinSpiritformAccounts,
    ))
    if new_min != DhuumSettings.MinSpiritformAccounts:
        DhuumSettings.MinSpiritformAccounts = new_min
        DhuumSettings.save()
    PyImGui.separator()

    if not Routines.Checks.Map.MapValid():
        PyImGui.text('Waiting for map to load...')
        return

    my_email     = Player.GetAccountEmail()
    all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    if not all_accounts:
        PyImGui.text('No multibox account data available.')
        return

    table_flags = PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersInnerV | PyImGui.TableFlags.BordersOuterH
    if PyImGui.begin_table('##dhuum_settings', 2, table_flags, 0.0, 0.0):
        PyImGui.table_setup_column('Sacrifice', PyImGui.TableColumnFlags.WidthFixed,   90.0)
        PyImGui.table_setup_column('Account',   PyImGui.TableColumnFlags.WidthStretch, 0.0)
        PyImGui.table_headers_row()

        for account in all_accounts:
            email     = str(account.AccountEmail)
            char_name = str(account.AgentData.CharacterName) or email
            is_self   = email == my_email

            PyImGui.table_next_row()
            if is_self:
                PyImGui.begin_disabled(True)

            PyImGui.table_next_column()
            cur_sac = DhuumSettings.is_sacrifice(email)
            new_sac = PyImGui.checkbox(f'##sac_{email}', cur_sac)

            PyImGui.table_next_column()
            PyImGui.text(f'{char_name}  (this account)' if is_self else char_name)

            if is_self:
                PyImGui.end_disabled()
            if new_sac != cur_sac:
                DhuumSettings.set_sacrifice(email, new_sac)

        PyImGui.end_table()


def _draw_imprisoned_spirits_settings() -> None:
    PyImGui.text_wrapped(
        'Assign each multibox account to the Left or Right team for the Imprisoned Spirits quest.'
    )
    PyImGui.separator()

    if not Routines.Checks.Map.MapValid():
        PyImGui.text('Waiting for map to load...')
        return

    all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    if not all_accounts:
        PyImGui.text('No multibox account data available.')
        return

    ImprisonedSpiritsSettings.apply_defaults_if_empty(all_accounts)
    my_email = Player.GetAccountEmail()

    table_flags = PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersInnerV | PyImGui.TableFlags.BordersOuterH
    if PyImGui.begin_table('##imprisoned_teams', 3, table_flags, 0.0, 0.0):
        PyImGui.table_setup_column('Left',    PyImGui.TableColumnFlags.WidthFixed,   40.0)
        PyImGui.table_setup_column('Right',   PyImGui.TableColumnFlags.WidthFixed,   40.0)
        PyImGui.table_setup_column('Account', PyImGui.TableColumnFlags.WidthStretch, 0.0)
        PyImGui.table_headers_row()

        for account in all_accounts:
            email     = str(account.AccountEmail)
            char_name = str(account.AgentData.CharacterName) or email
            is_self   = email == my_email
            team_idx  = 0 if ImprisonedSpiritsSettings.get_team(email) == 'left' else 1

            PyImGui.table_next_row()
            if is_self:
                PyImGui.begin_disabled(True)

            PyImGui.table_next_column()
            new_idx = PyImGui.radio_button(f'##left_{email}',  team_idx, 0)
            PyImGui.table_next_column()
            new_idx = PyImGui.radio_button(f'##right_{email}', new_idx,  1)
            PyImGui.table_next_column()
            PyImGui.text(f'{char_name}  (this account)' if is_self else char_name)

            if is_self:
                PyImGui.end_disabled()
            elif new_idx != team_idx:
                ImprisonedSpiritsSettings.set_team(email, 'left' if new_idx == 0 else 'right')

        PyImGui.end_table()


def _account_has_spirit_form(account) -> bool:
    try:
        return any(
            int(b.SkillId) == _SPIRIT_FORM_SKILL_ID
            for b in account.AgentData.Buffs.Buffs
            if int(getattr(b, 'SkillId', 0) or 0) != 0
        )
    except Exception:
        return False


def _account_death_penalty_pct(account) -> int:
    try:
        morale = int(getattr(account.AgentData, 'Morale', 100) or 100)
    except Exception:
        morale = 100
    return max(0, 100 - morale)


def _draw_debug_settings() -> None:
    if not Routines.Checks.Map.MapValid():
        PyImGui.separator()
        PyImGui.text('Waiting for map to load...')
        return

    _color_ok   = Utils.RGBToNormal(100, 255, 100, 255)
    _color_grey = Utils.RGBToNormal(140, 140, 140, 255)
    _color_warn = Utils.RGBToNormal(255,  80,  80, 255)
    _color_low  = Utils.RGBToNormal(255, 220,  60, 255)

    PyImGui.separator()
    PyImGui.text(f'Account status (Spirit Form = skill {_SPIRIT_FORM_SKILL_ID})')
    PyImGui.spacing()

    my_email = str(Player.GetAccountEmail() or '').strip()
    try:
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData() or []
    except Exception as e:
        PyImGui.text_colored(f'Error reading account data: {e}', _color_warn)
        accounts = []

    if not accounts:
        PyImGui.text_colored('No multibox account data available.', _color_grey)
    else:
        table_flags = PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersInnerV | PyImGui.TableFlags.BordersOuterH
        if PyImGui.begin_table('##uw_debug_accounts', 3, table_flags, 0.0, 0.0):
            PyImGui.table_setup_column('Character',   PyImGui.TableColumnFlags.WidthStretch, 0.0)
            PyImGui.table_setup_column('Spirit Form', PyImGui.TableColumnFlags.WidthFixed,   90.0)
            PyImGui.table_setup_column('Death Pen.',  PyImGui.TableColumnFlags.WidthFixed,   90.0)
            PyImGui.table_headers_row()

            for account in accounts:
                if not getattr(account, 'IsSlotActive', True):
                    continue
                email = str(getattr(account, 'AccountEmail', '') or '').strip()
                if not email:
                    continue

                char_name = str(getattr(account.AgentData, 'CharacterName', '') or '').strip() or email
                has_spirit = _account_has_spirit_form(account)
                dp_pct = _account_death_penalty_pct(account)
                is_self = email == my_email

                PyImGui.table_next_row()
                PyImGui.table_next_column()
                label = f'{char_name}  (this account)' if is_self else char_name
                if email != char_name and not is_self:
                    PyImGui.text(label)
                    PyImGui.text_colored(f'  {email}', _color_grey)
                else:
                    PyImGui.text(label)

                PyImGui.table_next_column()
                if has_spirit:
                    PyImGui.text_colored('Yes', _color_ok)
                else:
                    PyImGui.text_colored('No', _color_grey)

                PyImGui.table_next_column()
                if dp_pct <= 0:
                    PyImGui.text_colored('No', _color_grey)
                else:
                    dp_col = _color_warn if dp_pct >= 15 else _color_low
                    PyImGui.text_colored(f'-{dp_pct}%', dp_col)

        PyImGui.end_table()

    PyImGui.separator()
    PyImGui.text(f'Watchdog Log (last {_DEBUG_LOG_MAX})')
    if PyImGui.button('Clear##uw_watchdog_log'):
        _debug_watchdog_log.clear()
    if not _debug_watchdog_log:
        PyImGui.text_colored('  (no watchdog entries yet)', _color_grey)
    else:
        for entry in list(_debug_watchdog_log)[-20:][::-1]:
            PyImGui.text_wrapped(entry)


def _draw_settings() -> None:
    if PyImGui.begin_tab_bar('##uw_settings_tabs'):
        if PyImGui.begin_tab_item('General'):
            _draw_quest_settings()
            PyImGui.separator()
            _draw_enter_settings()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item('Inventory'):
            _draw_inventory_settings()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item('Cons'):
            _draw_cons_settings()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item('Imprisoned Spirits'):
            _draw_imprisoned_spirits_settings()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item('Dhuum'):
            _draw_dhuum_settings()
            PyImGui.end_tab_item()
        if PyImGui.begin_tab_item('Debug'):
            _draw_debug_settings()
            PyImGui.end_tab_item()
        PyImGui.end_tab_bar()


def _draw_run_log() -> None:
    if PyImGui.button('Clear Log##run_log'):
        try:
            with open(_WIPE_LOG_FILE, 'w', encoding='utf-8') as f:
                f.truncate(0)
        except OSError:
            pass
    PyImGui.same_line(0, -1)
    PyImGui.text(_WIPE_LOG_FILE)
    PyImGui.separator()
    try:
        with open(_WIPE_LOG_FILE, 'r', encoding='utf-8') as f:
            lines = [ln.rstrip('\n') for ln in f.readlines() if ln.strip()]
        last_10 = lines[-10:] if len(lines) > 10 else lines
        if not last_10:
            PyImGui.text_wrapped('(log is empty)')
        else:
            for line in reversed(last_10):
                PyImGui.text_wrapped(line)
    except FileNotFoundError:
        PyImGui.text_wrapped('(no log file yet — wipes and completed runs will appear here)')
    except OSError as exc:
        PyImGui.text_wrapped(f'Error reading log: {exc}')


def _fmt_s(total_s: int) -> str:
    h, rem = divmod(total_s, 3600)
    m, s   = divmod(rem, 60)
    return f'{h:02d}:{m:02d}:{s:02d}'


def _draw_main_additional_ui() -> None:
    _color_done    = Utils.RGBToNormal(100, 255, 100, 255)
    _color_pending = Utils.RGBToNormal(140, 140, 140, 255)
    _color_avg     = Utils.RGBToNormal(255, 210,  80, 255)
    _color_slow    = Utils.RGBToNormal(255,  80,  80, 255)

    PyImGui.text('Quest Progress')
    if PyImGui.begin_table(
        '##uw_quest_table', 5,
        PyImGui.TableFlags.RowBg
        | PyImGui.TableFlags.BordersOuterH
        | PyImGui.TableFlags.BordersOuterV
        | PyImGui.TableFlags.BordersInnerV,
    ):
        PyImGui.table_setup_column('Quest',  PyImGui.TableColumnFlags.WidthStretch)
        PyImGui.table_setup_column('Time',   PyImGui.TableColumnFlags.WidthFixed, 62)
        PyImGui.table_setup_column('Avg5',   PyImGui.TableColumnFlags.WidthFixed, 62)
        PyImGui.table_setup_column('AvgAll', PyImGui.TableColumnFlags.WidthFixed, 62)
        PyImGui.table_setup_column('SR%',    PyImGui.TableColumnFlags.WidthFixed, 42)
        PyImGui.table_headers_row()

        enter_uw_done = _timing_state['run_start_ms'] is not None

        for quest_name in _QUEST_ORDER:
            PyImGui.table_next_row()

            if quest_name == 'Enter Underworld':
                done = enter_uw_done
            else:
                done = quest_name in _quest_completion_times
            history = _quest_times_log.get(quest_name, [])
            recent5 = history[-5:] if history else []
            avg5_s  = int(sum(recent5) / len(recent5)) if recent5 else None
            avgall_s = int(sum(history)  / len(history))  if history else None

            # col 0 – Quest name
            PyImGui.table_set_column_index(0)
            PyImGui.text_colored(quest_name, _color_done if done else _color_pending)

            # col 1 – Time (this run, cumulative from Clear the Chamber)
            # 'Enter Underworld' has no completion time — it marks run start only.
            PyImGui.table_set_column_index(1)
            completion_ms = _quest_completion_times.get(quest_name)
            if done and completion_ms is not None:
                run_s = completion_ms // 1000
                cmp   = avg5_s if avg5_s is not None else avgall_s
                col   = (_color_done if cmp is None or run_s <= cmp else _color_slow)
                PyImGui.text_colored(_fmt_s(run_s), col)
            elif done:
                PyImGui.text_colored('✓', _color_done)
            else:
                PyImGui.text_colored('--:--:--', _color_pending)

            # col 2 – Avg last 5 runs
            PyImGui.table_set_column_index(2)
            if avg5_s is not None:
                PyImGui.text_colored(_fmt_s(avg5_s), _color_avg)
            else:
                PyImGui.text_colored('--:--:--', _color_pending)

            # col 3 – Avg all runs
            PyImGui.table_set_column_index(3)
            if avgall_s is not None:
                PyImGui.text_colored(_fmt_s(avgall_s), _color_avg)
            else:
                PyImGui.text_colored('--:--:--', _color_pending)

            # col 4 – Success rate (completions / (completions + wipes at this step))
            PyImGui.table_set_column_index(4)
            completions  = len(history)
            wipes        = _wipe_counts_log.get(quest_name, 0)
            attempts     = completions + wipes
            if attempts > 0:
                sr_pct = completions / attempts * 100.0
                if sr_pct >= 90.0:
                    sr_col = _color_done
                elif sr_pct >= 70.0:
                    sr_col = _color_avg
                else:
                    sr_col = _color_slow
                PyImGui.text_colored(f'{sr_pct:.0f}%', sr_col)
            else:
                PyImGui.text_colored('--', _color_pending)

        PyImGui.end_table()


# ╔══════════════════════════════════════════════════════════════════════════════
# ║  BOT + MAIN
# ╚══════════════════════════════════════════════════════════════════════════════

bot = BottingTree.Create(bot_name=BOT_NAME, multi_account=True, auto_loot=True, isolation_enabled=False)
# Reset the EnemyBlacklist on startup: clear any leftover entries from a previous
# crashed or incomplete run so HeroAI starts with a clean state.
try:
    from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist as _EBL_Init

    _bl_init = _EBL_Init()
    _bl_init._write(set())        # clear legacy model-ID entries
    _bl_init._write_names(set())  # clear leftover name entries
except Exception:
    pass
bot.UI.override_draw_help(lambda: _draw_help())
bot.UI.override_draw_config(lambda: _draw_settings())

# ── BehaviorTree import ──────────────────────────────────────────────────────
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree as _BT

# ── Shared BT helpers ────────────────────────────────────────────────────────

_BEHEMOTH_ENGAGE_RADIUS = 500.0

# Toggled by _behemoth_guard_start / _stop nodes; read every tick by the service.
_behemoth_guard_active: bool = False


def _build_behemoth_guard_service() -> _BT:
    """Parallel service: monitors Obsidian Behemoths while _behemoth_guard_active is True.

    No Routines.BT equivalent — dynamic EnemyBlacklist service.

    - Only runs its check every 500 ms to stay lightweight.
    - Uses Agent.GetModelID for enemy identification (model IDs are reliable without TextParser).
    - When a live behemoth enters range: removes its names from the blacklist so HeroAI fights.
    - When no more live behemoths within range: re-adds names to blacklist.
    - When the guard is deactivated (end of step): ensures the blacklist entry is restored.
    """
    state: dict = {'fighting': False, 'last_check_ms': 0}

    def _tick(node: _BT.Node) -> _BT.NodeState:
        global _behemoth_guard_active

        if not _behemoth_guard_active:
            if state['fighting']:
                _blacklist_names(UW_BEHEMOTH_GUARD_NAMES)
                state['fighting'] = False
            return _BT.NodeState.RUNNING

        now = int(Utils.GetBaseTimestamp())
        if now - state['last_check_ms'] < 500:
            return _BT.NodeState.RUNNING
        state['last_check_ms'] = now

        from Py4GWCoreLib import AgentArray as _AA
        px, py = Player.GetXY()
        nearby = False
        for aid in _AA.GetEnemyArray():
            if not Agent.IsAlive(aid):
                continue
            try:
                if int(Agent.GetModelID(aid)) not in UW_BEHEMOTH_GUARD_MODEL_IDS:
                    continue
                dist = Utils.Distance((px, py), Agent.GetXY(aid))
            except Exception:
                continue
            if dist <= _BEHEMOTH_ENGAGE_RADIUS:
                nearby = True
                break

        if nearby and not state['fighting']:
            _unblacklist_names(UW_BEHEMOTH_GUARD_NAMES)
            ConsoleLog(BOT_NAME, '[BehemothGuard] Enemy in range — blacklist OFF, engaging.', Py4GW.Console.MessageType.Info)
            state['fighting'] = True
        elif not nearby and state['fighting']:
            _blacklist_names(UW_BEHEMOTH_GUARD_NAMES)
            ConsoleLog(BOT_NAME, '[BehemothGuard] Fight done — blacklist ON, resuming.', Py4GW.Console.MessageType.Info)
            state['fighting'] = False

        return _BT.NodeState.RUNNING

    return _BT(_BT.ActionNode(name='BehemothGuardService', action_fn=_tick, aftercast_ms=0))
def _update_blacklist_names(
    *,
    add: tuple[str, ...] | list[str] = (),
    remove: tuple[str, ...] | list[str] = (),
    clear: bool = False,
) -> None:
    """Apply name-based blacklist changes with a single INI write.

    EnemyBlacklist.add_name/remove_name each write the INI individually.
    This helper batches all changes into one read-modify-write cycle.
    Pass clear=True to wipe all existing names before applying adds.
    """
    from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist as _EBL

    bl = _EBL()
    names: set[str] = set() if clear else set(bl.get_all_names())
    for name in remove:
        names.discard(name.strip().lower())
    for name in add:
        n = name.strip().lower()
        if n:
            names.add(n)
    bl._write_names(names)


def _blacklist_names(names: tuple[str, ...] | list[str]) -> None:
    _update_blacklist_names(add=names)


def _unblacklist_names(names: tuple[str, ...] | list[str]) -> None:
    _update_blacklist_names(remove=names)


def _blacklist_name(name: str) -> None:
    _update_blacklist_names(add=(name,))


def _unblacklist_name(name: str) -> None:
    _update_blacklist_names(remove=(name,))


def _is_agent_blacklisted(agent_id: int) -> bool:
    from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist as _EBL

    if not agent_id:
        return False
    try:
        return _EBL().is_blacklisted(int(agent_id))
    except Exception:
        return False


def _behemoth_guard_start() -> _BT:
    """Enable the BehemothGuard service and blacklist Obsidian Behemoth + Spirit of Nature's Renewal."""
    def _tick(node: _BT.Node) -> _BT.NodeState:
        global _behemoth_guard_active
        _blacklist_names(UW_BEHEMOTH_GUARD_NAMES)
        _behemoth_guard_active = True
        ConsoleLog(BOT_NAME, '[BehemothGuard] Started — Behemoth + Spirit blacklisted.', Py4GW.Console.MessageType.Info)
        return _BT.NodeState.SUCCESS
    return _BT(_BT.ActionNode(name='BehemothGuardStart', action_fn=_tick))
def _behemoth_guard_stop() -> _BT:
    """Disable the BehemothGuard service and immediately remove all guarded names from the blacklist."""
    def _tick(node: _BT.Node) -> _BT.NodeState:
        global _behemoth_guard_active
        _behemoth_guard_active = False
        _unblacklist_names(UW_BEHEMOTH_GUARD_NAMES)
        ConsoleLog(BOT_NAME, '[BehemothGuard] Stopped and blacklist cleared.', Py4GW.Console.MessageType.Info)
        return _BT.NodeState.SUCCESS
    return _BT(_BT.ActionNode(name='BehemothGuardStop', action_fn=_tick))
def _wait_out_of_combat(timeout_ms: int = 120_000) -> _BT:
    """RUNNING while COMBAT_ACTIVE is True in the blackboard; SUCCESS when combat ends or timeout."""
    def _tick(node: _BT.Node) -> _BT.NodeState:
        if node.blackboard.get('COMBAT_ACTIVE', False):
            return _BT.NodeState.RUNNING
        return _BT.NodeState.SUCCESS

    return _BT(_BT.WaitUntilNode(
        name='WaitOutOfCombat',
        condition_fn=_tick,
        throttle_interval_ms=250,
        timeout_ms=timeout_ms,
    ))


def _dialog_until_quest_active(
    x: float,
    y: float,
    dialog_id: int,
    quest_id: int,
    label: str = '',
    max_retries: int = 5,
    confirm_wait_ms: int = 2_000,
    retry_wait_ms: int = 3_000,
) -> _BT:
    """
    Move to (x, y), send dialog_id, then verify quest_id appears in the quest log.
    If not, retry up to max_retries times (wait_out_of_combat before each attempt).
    Always returns SUCCESS so the planner can continue even if all retries fail.
    """
    BT = Routines.BT
    _tag          = label or f'Quest{quest_id}'
    _retry_count  = [0]

    def _quest_in_log() -> bool:
        from Py4GWCoreLib import Quest as _Quest
        try:
            return any(int(q) == quest_id for q in (_Quest.GetQuestLogIds() or []))
        except Exception:
            return False

    def _single_dialog_attempt(attempt_label: str) -> _BT:
        return BT.Composite.Sequence(
            _wait_out_of_combat(timeout_ms=30_000),
            BT.Movement.Move(x=x, y=y),
            BT.Agents.MoveTargetInteractAndDialog(x=x, y=y, dialog_id=dialog_id),
            name=attempt_label,
        )

    def _check_or_retry(node: _BT.Node) -> _BT:
        if _quest_in_log():
            ConsoleLog(
                BOT_NAME,
                f'[{_tag}] Quest {quest_id} confirmed active.',
                Py4GW.Console.MessageType.Info,
            )
            return _BT(_BT.ActionNode(name=f'{_tag}QuestOK', action_fn=lambda n: _BT.NodeState.SUCCESS))

        if _retry_count[0] >= max_retries:
            ConsoleLog(
                BOT_NAME,
                f'[{_tag}] Quest {quest_id} not in log after {max_retries} retries — continuing.',
                Py4GW.Console.MessageType.Warning,
            )
            return _BT(_BT.ActionNode(name=f'{_tag}QuestGiveUp', action_fn=lambda n: _BT.NodeState.SUCCESS))

        _retry_count[0] += 1
        ConsoleLog(
            BOT_NAME,
            f'[{_tag}] Quest {quest_id} not in log — retry {_retry_count[0]}/{max_retries}.',
            Py4GW.Console.MessageType.Warning,
        )
        return BT.Composite.Sequence(
            BT.Player.Wait(duration_ms=retry_wait_ms),
            _single_dialog_attempt(f'{_tag}Retry{_retry_count[0]}'),
            BT.Player.Wait(duration_ms=confirm_wait_ms),
            _BT(_BT.SubtreeNode(name=f'{_tag}RetryCheck{_retry_count[0]}', subtree_fn=_check_or_retry)),
            name=f'{_tag}RetrySeq{_retry_count[0]}',
        )

    return BT.Composite.Sequence(
        _single_dialog_attempt(f'{_tag}FirstAttempt'),
        BT.Player.Wait(duration_ms=confirm_wait_ms),
        _BT(_BT.SubtreeNode(name=f'{_tag}QuestCheck', subtree_fn=_check_or_retry)),
        name=f'{_tag}DialogUntilQuestActive',
    )


def _wait_quest_completed(
    hold_x: float | None = None,
    hold_y: float | None = None,
    hold_radius: float = 500.0,
    move_throttle_ms: int = 2_000,
    timeout_ms: int = 0,
) -> _BT:
    """Wait until the active quest is completed.

    If hold_x/hold_y are given, the player is nudged back to that position
    whenever they drift more than hold_radius units away and are not in combat.
    """
    from Py4GWCoreLib.Quest import Quest

    state: dict = {'last_move_ms': None}

    def _condition(node: _BT.Node) -> _BT.NodeState:
        active = int(Quest.GetActiveQuest())
        if active > 0 and bool(Quest.IsQuestCompleted(active)):
            return _BT.NodeState.SUCCESS

        if hold_x is not None and hold_y is not None:
            px, py = Player.GetXY()
            dist = Utils.Distance((px, py), (hold_x, hold_y))
            if (
                dist > hold_radius
                and not node.blackboard.get('COMBAT_ACTIVE', False)
                and not node.blackboard.get('PAUSE_MOVEMENT', False)
            ):
                now = int(Utils.GetBaseTimestamp())
                last = state['last_move_ms']
                if last is None or now - last >= move_throttle_ms:
                    Player.Move(hold_x, hold_y)
                    state['last_move_ms'] = now

        return _BT.NodeState.RUNNING

    return _BT(_BT.WaitUntilNode(
        name='WaitQuestCompleted',
        condition_fn=_condition,
        throttle_interval_ms=500,
        timeout_ms=timeout_ms,
    ))
def _blacklist_add_dream_rider() -> None:
    _blacklist_name(UWBlacklistName.BanishedDreamRider)
def _clear_follower_flags() -> _BT:
    """No Routines.BT equivalent — HeroAI multibox follower flags (not BT.Party.FlagHero)."""

    def _tick(node: _BT.Node) -> _BT.NodeState:
        for _, options in GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False):
            if int(_.AgentPartyData.PartyPosition) == 0:
                continue
            options.IsFlagged       = False
            options.FlagPos.x       = 0.0
            options.FlagPos.y       = 0.0
            options.FlagFacingAngle = 0.0
        return _BT.NodeState.SUCCESS

    return _BT(_BT.ActionNode(name='ClearFollowerFlags', action_fn=_tick))
_DHUUM_SAC_FLAG_X  = -15386.0
_DHUUM_SAC_FLAG_Y  =  17295.0
_DHUUM_SURV_FLAG_X = -14374.0
_DHUUM_SURV_FLAG_Y =  17261.0


def _flag_dhuum_accounts() -> _BT:
    """Single-pass flag assignment for Dhuum.

    No Routines.BT equivalent — HeroAI multibox follower flags (not BT.Party.FlagHero).

    - Clears all follower flags first.
    - Sacrifice accounts (DhuumSettings.SacrificeEmails) → (_DHUUM_SAC_FLAG_X/Y).
    - All other followers (non-leader, non-sacrifice) → (_DHUUM_SURV_FLAG_X/Y).
    - The leader (bot runner, party position 0) is never flagged.
    """
    def _tick(node: _BT.Node) -> _BT.NodeState:
        sacrifice_emails = {e.strip().lower() for e in DhuumSettings.SacrificeEmails}
        my_email = (Player.GetAccountEmail() or '').strip().lower()

        sac_flagged:  list[str] = []
        surv_flagged: list[str] = []

        for account, options in GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False):
            email = str(account.AccountEmail or '').strip().lower()

            # Always clear first
            options.IsFlagged       = False
            options.FlagPos.x       = 0.0
            options.FlagPos.y       = 0.0
            options.FlagFacingAngle = 0.0

            if email == my_email:
                continue  # leader runs the bot — never flagged

            if email in sacrifice_emails:
                options.IsFlagged = True
                options.FlagPos.x = _DHUUM_SAC_FLAG_X
                options.FlagPos.y = _DHUUM_SAC_FLAG_Y
                sac_flagged.append(email)
            else:
                options.IsFlagged = True
                options.FlagPos.x = _DHUUM_SURV_FLAG_X
                options.FlagPos.y = _DHUUM_SURV_FLAG_Y
                surv_flagged.append(email)

        if not sacrifice_emails:
            ConsoleLog(BOT_NAME, '[Dhuum] No sacrifice accounts configured — all flagged as survivors.', Py4GW.Console.MessageType.Warning)
        ConsoleLog(BOT_NAME, f'[Dhuum] Sacrifice flags ({len(sac_flagged)}): {sac_flagged}', Py4GW.Console.MessageType.Info)
        ConsoleLog(BOT_NAME, f'[Dhuum] Survivor  flags ({len(surv_flagged)}): {surv_flagged}', Py4GW.Console.MessageType.Info)
        return _BT.NodeState.SUCCESS

    return _BT(_BT.ActionNode(name='FlagDhuumAccounts', action_fn=_tick))
def _disable_heroai_combat_all() -> _BT:
    """Set Combat = False on every active HeroAI account (all party slots).

    No Routines.BT equivalent — HeroAI Combat toggle via SharedMemory options.
    """
    def _tick(node: _BT.Node) -> _BT.NodeState:
        for _, options in GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False):
            options.Combat = False
        ConsoleLog(BOT_NAME, '[Dhuum] HeroAI combat disabled for all accounts.', Py4GW.Console.MessageType.Info)
        return _BT.NodeState.SUCCESS

    return _BT(_BT.ActionNode(name='DisableHeroAICombatAll', action_fn=_tick))
def _enable_heroai_combat_all() -> _BT:
    """Set Combat = True on every active HeroAI account (all party slots).

    No Routines.BT equivalent — HeroAI Combat toggle via SharedMemory options.
    """
    def _tick(node: _BT.Node) -> _BT.NodeState:
        for _, options in GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False):
            options.Combat = True
        ConsoleLog(BOT_NAME, '[Dhuum] HeroAI combat enabled for all accounts.', Py4GW.Console.MessageType.Info)
        return _BT.NodeState.SUCCESS

    return _BT(_BT.ActionNode(name='EnableHeroAICombatAll', action_fn=_tick))
_UW_CHEST_NAME     = 'underworld chest'
_UW_CHEST_POS      = (-14381.0, 17283.0)
_UW_CHEST_RADIUS   = 300.0


def _wait_for_uw_chest() -> _BT:
    """RUNNING until the Underworld Chest gadget appears near its spawn point.

    Only bails out with SUCCESS when:
      - the map is confirmed invalid (left UW / party wipe kicked everyone out), or
      - the chest gadget is found within _UW_CHEST_RADIUS, or
      - the safety timeout fires (25 min — Dhuum fight far exceeds this only if bugged).

    API errors are treated as RUNNING (keep waiting), never as SUCCESS.
    This prevents a transient exception (e.g. while the leader is dead) from
    prematurely exiting the wait and triggering LootChest mid-fight.
    """
    import time as _time

    _TIMEOUT_S = 3600.0  # 60 minutes — only fires if something is catastrophically broken
    state: dict = {'deadline': None}

    def _tick(node: _BT.Node) -> _BT.NodeState:
        # ── Map validity check — exception → keep waiting (RUNNING) ──────────
        try:
            map_valid = Routines.Checks.Map.MapValid()
        except Exception:
            return _BT.NodeState.RUNNING  # can't determine → stay safe
        if not map_valid:
            ConsoleLog(BOT_NAME, '[Dhuum] WaitForUWChest: map no longer valid — exiting.', Py4GW.Console.MessageType.Warning)
            state['deadline'] = None
            return _BT.NodeState.SUCCESS

        try:
            map_id = int(Map.GetMapID() or 0)
        except Exception:
            return _BT.NodeState.RUNNING  # can't determine → stay safe
        if map_id != UW_MAP_ID:
            ConsoleLog(BOT_NAME, f'[Dhuum] WaitForUWChest: map changed ({map_id}) — exiting.', Py4GW.Console.MessageType.Warning)
            state['deadline'] = None
            return _BT.NodeState.SUCCESS

        # ── Safety timeout (last resort only) ────────────────────────────────
        now = _time.monotonic()
        if state['deadline'] is None:
            state['deadline'] = now + _TIMEOUT_S
        elif now >= state['deadline']:
            ConsoleLog(BOT_NAME, '[Dhuum] WaitForUWChest: safety timeout fired — something is broken.', Py4GW.Console.MessageType.Error)
            state['deadline'] = None
            return _BT.NodeState.SUCCESS

        # ── Scan for chest gadget ─────────────────────────────────────────────
        try:
            from Py4GWCoreLib import AgentArray as _AA
            agents = list(_AA.GetAgentArray() or [])
        except Exception:
            return _BT.NodeState.RUNNING

        for agent_id in agents:
            try:
                if not Agent.IsValid(agent_id):
                    continue
                if not Agent.IsGadget(agent_id):
                    continue
                pos = Agent.GetXY(agent_id)
                if not pos:
                    continue
                if Utils.Distance(_UW_CHEST_POS, pos) <= _UW_CHEST_RADIUS:
                    ConsoleLog(BOT_NAME, '[Dhuum] Underworld Chest appeared — Dhuum done.', Py4GW.Console.MessageType.Info)
                    state['deadline'] = None
                    return _BT.NodeState.SUCCESS
            except Exception:
                continue

        return _BT.NodeState.RUNNING

    return _BT(_BT.ActionNode(name='WaitForUWChest', action_fn=_tick))
def _wait_for_spirit_forms() -> _BT:
    """RUNNING until MinSpiritformAccounts party members in UW have Spirit Form (buff 3134).

    Bails out immediately (SUCCESS) on map change / wipe so the planner can recover.
    """
    def _tick(node: _BT.Node) -> _BT.NodeState:
        if not Routines.Checks.Map.MapValid() or int(Map.GetMapID() or 0) != UW_MAP_ID:
            return _BT.NodeState.SUCCESS  # bail on wipe / map change
        threshold = int(DhuumSettings.MinSpiritformAccounts)
        count = 0
        for acct in GLOBAL_CACHE.ShMem.GetAllAccountData() or []:
            if getattr(acct.AgentData.Map, 'MapID', 0) != UW_MAP_ID:
                continue
            try:
                if any(b.SkillId == _SPIRIT_FORM_BUFF_ID for b in acct.AgentData.Buffs.Buffs if b.SkillId != 0):
                    count += 1
            except Exception:
                pass
            if count >= threshold:
                ConsoleLog(BOT_NAME, f'[Dhuum] {count}/{threshold} Spirit Form(s) active — enabling combat.', Py4GW.Console.MessageType.Info)
                return _BT.NodeState.SUCCESS
        return _BT.NodeState.RUNNING

    return _BT(_BT.ActionNode(name='WaitForSpiritForms', action_fn=_tick))
def _enable_dhuum_helper_on_all_accounts() -> _BT:
    """Enable the 'Dhuum Helper' widget locally and send EnableWidget to every other account.

    No Routines.BT equivalent — WidgetManager + EnableWidget multibox messages.
    """
    def _tick(node: _BT.Node) -> _BT.NodeState:
        from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler
        from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType

        widget_name = 'Dhuum Helper'
        handler = get_widget_handler()
        if not handler.is_widget_enabled(widget_name):
            handler.enable_widget(widget_name)

        sender_email = Player.GetAccountEmail()
        for account in GLOBAL_CACHE.ShMem.GetAllActiveSlotsData():
            acc_email = str(getattr(account, 'AccountEmail', '') or '').strip().lower()
            if not acc_email or acc_email == (sender_email or '').lower():
                continue
            GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                acc_email,
                SharedCommandType.EnableWidget,
                (0, 0, 0, 0),
                (widget_name, '', '', ''),
            )
        ConsoleLog(BOT_NAME, '[Dhuum] Dhuum Helper enabled on all accounts.', Py4GW.Console.MessageType.Info)
        return _BT.NodeState.SUCCESS

    return _BT(_BT.ActionNode(name='EnableDhuumHelperAllAccounts', action_fn=_tick))
def _follow_king_frozenwind() -> _BT:
    """RUNNING while following King Frozenwind to his destination.

    Mirrors _coro_follow_king_to_destination from legacy Underworld.py:
    - Locate the King by model ID 2403 each tick.
    - Nudge the player toward the King if distance > _KING_FROZENWIND_FOLLOW_RADIUS.
    - Return SUCCESS once the King reaches _KING_FROZENWIND_DEST_X/Y ± DEST_RADIUS.
    - Return SUCCESS on timeout so the sequence continues regardless.
    """
    import time as _t

    state: dict = {'deadline': None}

    def _tick(node: _BT.Node) -> _BT.NodeState:
        from Py4GWCoreLib import AgentArray as _AA

        if state['deadline'] is None:
            state['deadline'] = _t.time() + _KING_FROZENWIND_TIMEOUT_S
            ConsoleLog(BOT_NAME, '[Dhuum] Following King Frozenwind to his position …', Py4GW.Console.MessageType.Info)

        if _t.time() >= state['deadline']:
            ConsoleLog(BOT_NAME, '[Dhuum] King follow timed out — continuing.', Py4GW.Console.MessageType.Warning)
            state['deadline'] = None
            return _BT.NodeState.SUCCESS

        king_id = next(
            (a for a in _AA.GetAgentArray() if Agent.IsValid(a) and int(Agent.GetModelID(a)) == _KING_FROZENWIND_MODEL_ID),
            None,
        )
        if king_id is None:
            return _BT.NodeState.RUNNING

        kx, ky = Agent.GetXY(king_id)
        if Utils.Distance((kx, ky), (_KING_FROZENWIND_DEST_X, _KING_FROZENWIND_DEST_Y)) <= _KING_FROZENWIND_DEST_RADIUS:
            ConsoleLog(BOT_NAME, '[Dhuum] King has reached his position.', Py4GW.Console.MessageType.Info)
            state['deadline'] = None
            return _BT.NodeState.SUCCESS

        px, py = Player.GetXY()
        if Utils.Distance((px, py), (kx, ky)) > _KING_FROZENWIND_FOLLOW_RADIUS:
            Player.Move(kx, ky)

        return _BT.NodeState.RUNNING

    return _BT(_BT.WaitUntilNode(
        name='FollowKingFrozenwind',
        condition_fn=_tick,
        throttle_interval_ms=500,
        timeout_ms=int(_KING_FROZENWIND_TIMEOUT_S * 1000) + 5000,
    ))
def _purge_all_enemy_blacklist_names() -> None:
    """Drop every name-based blacklist entry (resets all bot-managed blacklist state)."""
    _update_blacklist_names(clear=True)


def _purge_blacklist_names_action(_node: _BT.Node) -> _BT.NodeState:
    _purge_all_enemy_blacklist_names()
    return _BT.NodeState.SUCCESS


def _unblacklist_chained_soul(node: _BT.Node) -> _BT.NodeState:
    _unblacklist_name(UWBlacklistName.ChainedSoul)
    return _BT.NodeState.SUCCESS


def _blacklist_chained_soul(node: _BT.Node) -> _BT.NodeState:
    _blacklist_name(UWBlacklistName.ChainedSoul)
    return _BT.NodeState.SUCCESS


def _blacklist_tortured_spirits(_node: _BT.Node) -> _BT.NodeState:
    _blacklist_names(UW_TORTURED_SPIRIT_NAMES)
    return _BT.NodeState.SUCCESS


def _unblacklist_tortured_spirits(_node: _BT.Node) -> _BT.NodeState:
    _unblacklist_names(UW_TORTURED_SPIRIT_NAMES)
    return _BT.NodeState.SUCCESS


def _blacklist_obsidian_guardian(_node: _BT.Node) -> _BT.NodeState:
    _blacklist_name(UWBlacklistName.ObsidianGuardian)
    return _BT.NodeState.SUCCESS


def _blacklist_vengeful_aatxe(_node: _BT.Node) -> _BT.NodeState:
    _blacklist_name(UWBlacklistName.VengefulAatxe)
    return _BT.NodeState.SUCCESS


def _unblacklist_vengeful_aatxe(_node: _BT.Node) -> _BT.NodeState:
    _unblacklist_name(UWBlacklistName.VengefulAatxe)
    return _BT.NodeState.SUCCESS


def _unblacklist_dream_rider(_node: _BT.Node) -> _BT.NodeState:
    _unblacklist_name(UWBlacklistName.BanishedDreamRider)
    return _BT.NodeState.SUCCESS


def _prepare_unwanted_guests_blacklist(_node: _BT.Node) -> _BT.NodeState:
    _update_blacklist_names(
        add=(UWBlacklistName.VengefulAatxe,),
        remove=UW_TORTURED_SPIRIT_NAMES,
    )
    return _BT.NodeState.SUCCESS


def _clear_bot_blacklist_names() -> None:
    _purge_all_enemy_blacklist_names()
def _party_call_or_change_target(agent_id: int) -> None:
    """Match HeroAI UI: party leader uses Call Target (Ctrl+Space); others only change local target.

    No Routines.BT equivalent — HeroAI CallTarget + Player.ChangeTarget.
    """
    from Py4GWCoreLib.Agent import Agent as _Agent

    if not agent_id or not _Agent.IsValid(agent_id):
        return
    try:
        from HeroAI.call_target import CallTarget
    except Exception:
        CallTarget = None  # type: ignore[misc, assignment]

    try:
        leader_id = int(GLOBAL_CACHE.Party.GetPartyLeaderID() or 0)
    except Exception:
        leader_id = 0
    local_id = int(Player.GetAgentID() or 0)

    if CallTarget is not None and leader_id and local_id == leader_id:
        if CallTarget(int(agent_id), interact=False):
            return
    Player.ChangeTarget(int(agent_id))

# ── Entry / scroll ───────────────────────────────────────────────────────────

def _force_local_skills_on() -> _BT:
    """Force all HeroAI skill slots for this account to True in SharedMemory.

    No Routines.BT equivalent — per-slot HeroAI Skills[] flags in SharedMemory.

    RestoreHeroAIOptions only sets Combat/Following/Avoidance/Targeting.
    Per-slot Skills[i] flags persist from the HeroAI widget (Shift+Click
    disables a slot). If any slot is False, Headless HeroAI silently skips
    that slot even when Combat is active. Call this once at the start of
    each explorable step.
    """
    state: dict = {'done': False}

    def _tick(node: _BT.Node) -> _BT.NodeState:
        if state['done']:
            return _BT.NodeState.SUCCESS
        account_email = Player.GetAccountEmail()
        if not account_email:
            return _BT.NodeState.RUNNING
        try:
            options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account_email)
        except Exception:
            options = None
        if options is None:
            return _BT.NodeState.RUNNING
        try:
            for slot in range(len(options.Skills)):
                options.Skills[slot] = True
            GLOBAL_CACHE.ShMem.SetHeroAIOptionsByEmail(account_email, options)
        except Exception:
            return _BT.NodeState.RUNNING
        ConsoleLog(BOT_NAME, '[Bot] ForceLocalSkillsOn: all skill slots enabled.', Py4GW.Console.MessageType.Info)
        state['done'] = True
        return _BT.NodeState.SUCCESS

    return _BT(_BT.ActionNode(name='ForceLocalSkillsOn', action_fn=_tick))


_REQUIRED_WIDGETS: tuple[str, ...] = ('HeroAI', 'Dhuum Helper')


def _enable_required_widgets_on_all_accounts(node: object) -> object:
    """Enable HeroAI and Dhuum Helper locally and on every other account.

    No Routines.BT equivalent — WidgetManager + EnableWidget multibox messages.
    """
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler
    from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
    from Py4GWCoreLib.Player import Player as _Player

    handler = get_widget_handler()
    for widget_name in _REQUIRED_WIDGETS:
        if not handler.is_widget_enabled(widget_name):
            handler.enable_widget(widget_name)

    sender_email = _Player.GetAccountEmail()
    for account in GLOBAL_CACHE.ShMem.GetAllActiveSlotsData():
        acc_email = str(getattr(account, 'AccountEmail', '') or '').strip().lower()
        if not acc_email or acc_email == sender_email.lower():
            continue
        for widget_name in _REQUIRED_WIDGETS:
            GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                acc_email,
                SharedCommandType.EnableWidget,
                (0, 0, 0, 0),
                (widget_name, '', '', ''),
            )
    return _BT.NodeState.SUCCESS


def _uw_scroll_count_local() -> int:
    return int(GLOBAL_CACHE.Inventory.GetModelCount(int(UW_SCROLL_MODEL_ID)) or 0)


def _leader_needs_uw_scroll_buy() -> bool:
    if not InventorySettings.BuyUWScrolls or not Map.IsGuildHall():
        return False
    return _uw_scroll_count_local() < max(0, int(InventorySettings.UWScrollMin))


def _resolve_scroll_trader() -> tuple[float, float, int] | None:
    """Locate Scroll Trader (model 207) in the Guild Hall NPC arrays."""
    from Py4GWCoreLib import AgentArray as _AA

    seen: set[int] = set()
    for source in (_AA.GetNPCMinipetArray(), _AA.GetAgentArray(), _AA.GetNeutralArray()):
        for agent_id in source or []:
            aid = int(agent_id)
            if aid in seen:
                continue
            seen.add(aid)
            if not Agent.IsValid(aid):
                continue
            try:
                if int(Agent.GetModelID(aid)) == _SCROLL_TRADER_MODEL_ID:
                    pos = Agent.GetXY(aid)
                    if pos:
                        return float(pos[0]), float(pos[1]), aid
            except Exception:
                continue
    return None


def _scroll_trader_approach_xy(trader_x: float, trader_y: float) -> tuple[float, float]:
    """Stand on the player side of the trader, not on the NPC's blocked tile."""
    player_pos = Player.GetXY()
    if not player_pos:
        return trader_x, trader_y

    px, py = float(player_pos[0]), float(player_pos[1])
    dx = px - trader_x
    dy = py - trader_y
    dist = math.hypot(dx, dy)
    if dist < 1.0:
        return trader_x + _SCROLL_TRADER_APPROACH_DIST, trader_y

    scale = _SCROLL_TRADER_APPROACH_DIST / dist
    return trader_x + dx * scale, trader_y + dy * scale


def _scroll_trader_stock_ready(_node: _BT.Node) -> _BT.NodeState:
    """Scroll Trader stock is exposed via Trading.Trader, not Trading.Merchant."""
    for candidate in GLOBAL_CACHE.Trading.Trader.GetOfferedItems() or []:
        if int(GLOBAL_CACHE.Item.GetModelID(candidate) or 0) == int(UW_SCROLL_MODEL_ID):
            return _BT.NodeState.SUCCESS
    return _BT.NodeState.RUNNING


def _build_buy_uw_scrolls_tree(node: _BT.Node) -> _BT:
    """Guild Hall Scroll Trader restock for the leader when below min scrolls."""
    BT = Routines.BT

    if not _leader_needs_uw_scroll_buy():
        return _BT(_BT.ActionNode(name='SkipBuyUWScrolls', action_fn=lambda _node: _BT.NodeState.SUCCESS))

    _trader_state: dict = {'trader_xy': None, 'trader_agent_id': 0, 'wait_start_ms': None}

    def _wait_for_scroll_trader(_node: _BT.Node) -> _BT.NodeState:
        if not Map.IsGuildHall():
            return _BT.NodeState.SUCCESS

        resolved = _resolve_scroll_trader()
        if resolved:
            _trader_state['trader_xy'] = (resolved[0], resolved[1])
            _trader_state['trader_agent_id'] = int(resolved[2])
            ConsoleLog(
                BOT_NAME,
                f'[EnterUW] BuyUWScrolls: found {_SCROLL_TRADER_NAME} '
                f'(model {int(Agent.GetModelID(resolved[2]))}) '
                f'agent_id={resolved[2]} at ({resolved[0]:.0f}, {resolved[1]:.0f}).',
                Py4GW.Console.MessageType.Info,
            )
            return _BT.NodeState.SUCCESS

        now_ms = int(Utils.GetBaseTimestamp())
        if _trader_state['wait_start_ms'] is None:
            _trader_state['wait_start_ms'] = now_ms
            ConsoleLog(
                BOT_NAME,
                f'[EnterUW] BuyUWScrolls: waiting for {_SCROLL_TRADER_NAME} …',
                Py4GW.Console.MessageType.Info,
            )

        if now_ms - int(_trader_state['wait_start_ms']) >= 30_000:
            scrolls = _uw_scroll_count_local()
            min_req = max(0, int(InventorySettings.UWScrollMin))
            if scrolls >= min_req:
                ConsoleLog(
                    BOT_NAME,
                    f'[EnterUW] BuyUWScrolls: {_SCROLL_TRADER_NAME} not found — have {scrolls} scroll(s) (min {min_req}), skipping buy.',
                    Py4GW.Console.MessageType.Warning,
                )
            else:
                ConsoleLog(
                    BOT_NAME,
                    f'[EnterUW] BuyUWScrolls: {_SCROLL_TRADER_NAME} not found — only {scrolls} scroll(s) (need {min_req}); continuing without buy.',
                    Py4GW.Console.MessageType.Warning,
                )
            return _BT.NodeState.SUCCESS

        return _BT.NodeState.RUNNING

    def _build_buy_sequence(_node: _BT.Node) -> _BT:
        trader_xy = _trader_state.get('trader_xy')
        trader_agent_id = int(_trader_state.get('trader_agent_id') or 0)
        if not trader_xy:
            return _BT(_BT.ActionNode(name='SkipBuyUWScrollsNoTrader', action_fn=lambda n: _BT.NodeState.SUCCESS))

        target_max = max(0, int(InventorySettings.UWScrollMax))
        buy_qty = max(0, target_max - _uw_scroll_count_local())
        if buy_qty <= 0:
            return _BT(_BT.ActionNode(name='SkipBuyUWScrollsAtMax', action_fn=lambda n: _BT.NodeState.SUCCESS))

        trader_x, trader_y = float(trader_xy[0]), float(trader_xy[1])
        approach_x, approach_y = _scroll_trader_approach_xy(trader_x, trader_y)
        ConsoleLog(
            BOT_NAME,
            f'[EnterUW] BuyUWScrolls: buying {buy_qty} scroll(s) for leader (target max={target_max}); '
            f'approach=({approach_x:.0f}, {approach_y:.0f}) trader=({trader_x:.0f}, {trader_y:.0f}) '
            f'agent_id={trader_agent_id}.',
            Py4GW.Console.MessageType.Info,
        )
        if trader_agent_id > 0:
            target_trader = BT.Player.ChangeTarget(trader_agent_id, log=True)
        else:
            target_trader = BT.Agents.TargetAgentByModelID(_SCROLL_TRADER_MODEL_ID, log=True)
        return BT.Composite.Sequence(
            BT.Movement.Move(
                x=approach_x,
                y=approach_y,
                tolerance=_SCROLL_TRADER_MOVE_TOLERANCE,
                timeout_ms=30_000,
                pause_on_combat=False,
                log=False,
            ),
            target_trader,
            BT.Player.InteractTarget(log=True),
            BT.Player.Wait(2000, log=False),
            _BT(_BT.WaitUntilNode(
                name='WaitScrollTraderStock',
                condition_fn=_scroll_trader_stock_ready,
                throttle_interval_ms=100,
                timeout_ms=8000,
            )),
            BT.Items.BuyMaterials(
                int(UW_SCROLL_MODEL_ID),
                batches=buy_qty,
                rare_trader=True,
                log=True,
                aftercast_ms=250,
            ),
            name='BuyUWScrollsSequence',
        )

    return BT.Composite.Sequence(
        _BT(_BT.WaitUntilNode(
            name='WaitForScrollTrader',
            condition_fn=_wait_for_scroll_trader,
            throttle_interval_ms=500,
            timeout_ms=35_000,
        )),
        _BT(_BT.SubtreeNode(
            name='BuyUWScrollsSequence',
            subtree_fn=_build_buy_sequence,
        )),
        name='BuyUWScrolls',
    )


def _resolve_uw_entry_map_id() -> int:
    key = EnterSettings.EntryPoint or DEFAULT_UW_ENTRYPOINT_KEY
    return int(UW_ENTRYPOINTS.get(key, UW_ENTRYPOINTS[DEFAULT_UW_ENTRYPOINT_KEY])[1])


# ── Quest trees (chronological) ──────────────────────────────────────────────

# Missing ApoBT wrappers (no equivalent exists in ApoBottingLib yet):
#
#   1. ApoBT.SummonAllAccounts — using RoutinesBT.Multibox.SummonAllAccounts directly.
#   2. ApoBT.UseItemByModelID  — using a raw _BT.ActionNode + GLOBAL_CACHE.Inventory.UseItem.
#   3. ApoBT.EnableWidgets     — using a raw _BT.ActionNode + WidgetManager + ShMem.SendMessage.

def _enter_underworld_tree() -> _BT:
    """
    Step 1: Gather all accounts at Guild Hall, travel to entry point, create party, then enter UW.

    Sequence:
      0. bot.Config.Pacifist(multi_account=True) — HeroAI off, isolation off, multibox on.
      1. LeaveParty → TravelGH → SummonAllAccounts → Wait — all accounts meet at GH.
      2. BuyUWScrolls (skipped when stock is sufficient).
      3. Travel to configured entry outpost.
      4. CreateParty(multibox_invite=True) — LeaveParty + SummonAllAccounts + InviteAllAccounts.
      5. EnableRequiredWidgets; set hard/normal mode.
      6. BlacklistChainedSoul; use UW scroll.
    """
    from Sources.ApoSource.ApoBottingLib import wrappers as ApoBT
    from Py4GWCoreLib.routines_src.BehaviourTrees import BT as RoutinesBT
    BT = Routines.BT

    def _use_local_uw_scroll(_node: _BT.Node) -> _BT.NodeState:
        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(UW_SCROLL_MODEL_ID)
        if item_id == 0:
            ConsoleLog(BOT_NAME, '[EnterUW] UseUWScroll: no scroll found in inventory!', Py4GW.Console.MessageType.Warning)
            return _BT.NodeState.FAILURE
        GLOBAL_CACHE.Inventory.UseItem(item_id)
        ConsoleLog(BOT_NAME, '[EnterUW] UseUWScroll: scroll used.', Py4GW.Console.MessageType.Info)
        return _BT.NodeState.SUCCESS

    return BT.Composite.Sequence(
        bot.Config.Pacifist(multi_account=True),
        ApoBT.LeaveParty(),
        ApoBT.TravelGH(),
        RoutinesBT.Multibox.SummonAllAccounts(timeout_ms=15_000, poll_interval_ms=100, log=True),
        ApoBT.Wait(duration_ms=1000, log=True),
        _BT(_BT.SubtreeNode(name='BuyUWScrolls', subtree_fn=_build_buy_uw_scrolls_tree)),
        ApoBT.Travel(target_map_id=_resolve_uw_entry_map_id(), log=True),
        ApoBT.CreateParty(multibox_invite=True, timeout_ms=15_000, poll_interval_ms=100, aftercast_ms=250, log=True),
        _BT(_BT.ActionNode(name='EnableRequiredWidgets', action_fn=_enable_required_widgets_on_all_accounts, aftercast_ms=500)),
        ApoBT.SetHardMode(hard_mode=BotSettings.HardMode, log=True),
        _BT(_BT.ActionNode(name='BlacklistChainedSoul', action_fn=_blacklist_chained_soul)),
        _BT(_BT.ActionNode(name='UseUWScroll', action_fn=_use_local_uw_scroll, aftercast_ms=500)),
        name='EnterUnderworld',
    )


def _clear_the_chamber_tree() -> _BT:
    """
    Step 2: Clear the Chamber quest.

    Sequence:
      1.  Move to Lost Soul (2425) at (345, 7167) → interact → take quest (dialog 0x806501).
      2.  Move to combat start position (769, 6564).
      3.  Walk the chamber clearing path.
      4.  Move to Reaper of the Labyrinth (2399) at (-5806, 12831) → collect reward (0x806507).
      5.  Take Restore Monuments quest from same Reaper (0x806D01).
    """
    BT = Routines.BT

    return BT.Composite.Sequence(
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True),
        _force_local_skills_on(),
        # Take quest from Lost Soul
        BT.Agents.MoveTargetInteractAndAutomaticDialog(
            x=345, y=7167,
            button_number=0,
        ),
        # Move to combat staging area
        BT.Movement.Move(x=769, y=6564),
        # Clear the chamber — walk the full path
        BT.Movement.Move(x=-1547, y=6038),
        BT.Movement.Move(x=-664,  y=8912),
        BT.Movement.Move(x=1307,  y=10135),
        BT.Movement.Move(x=1110,  y=12567),
        BT.Movement.Move(x=-290,  y=13342),
        BT.Movement.Move(x=-3945, y=13308),
        BT.Movement.Move(x=-4699, y=11793),
        BT.Movement.Move(x=-5963, y=11827),
        BT.Movement.Move(x=-5834, y=12812),
        # Collect reward from Reaper of the Labyrinth
        BT.Agents.MoveTargetInteractAndAutomaticDialog(
            x=-5834, y=12812,
            button_number=0,
        ),
        # Take Restore Monuments quest from same Reaper (with quest-active retry)
        _dialog_until_quest_active(
            x=-5834, y=12812,
            dialog_id=0x806D01,
            quest_id=int(UWQuestID.RestoringGrenthsMonuments),
            label='RestoreMonuments',
        ),
        name='ClearTheChamber',
    )












def _pass_the_mountains_tree() -> _BT:
    BT = Routines.BT
    return BT.Composite.Sequence(
        _behemoth_guard_start(),
        BT.Movement.Move(x=-5834, y=12812),
        BT.Movement.Move(x=-3533, y=10728),
        BT.Movement.Move(x=-1450, y=10356),
        BT.Movement.Move(x=-1384, y=6402),
        BT.Movement.Move(x=-3295, y=2620),
        BT.Movement.Move(x=-83,   y=2593),
        BT.Movement.Move(x=2969,  y=2806),
        BT.Movement.Move(x=5317,  y=590),
        BT.Movement.Move(x=8648,  y=-1533),
        BT.Movement.Move(x=8688,  y=-5315),
        BT.Movement.Move(x=7547,  y=-7611),
        _behemoth_guard_stop(),
        name='PassTheMountains',
    )


def _restore_mountains_tree() -> _BT:
    BT = Routines.BT
    return BT.Composite.Sequence(
        _behemoth_guard_start(),
        BT.Movement.Move(x=3009,  y=-7876),
        BT.Movement.Move(x=1018,  y=-9456),
        BT.Movement.Move(x=-2419, y=-7770),
        BT.Movement.Move(x=-5391, y=-4426),
        _behemoth_guard_stop(),
        BT.Movement.Move(x=-8337, y=-5342),
        name='RestoreMountains',
    )




def _deamon_assassin_tree() -> _BT:
    BT = Routines.BT

    return BT.Composite.Sequence(
        _dialog_until_quest_active(
            x=-8260.00, y=-5238.00,
            dialog_id=0x806801,
            quest_id=int(UWQuestID.DemonAssassin),
            label='DeamonAssassin',
        ),
        _behemoth_guard_start(),
        BT.Movement.Move(x=-3560, y=-5899),
        _wait_quest_completed(),
        _behemoth_guard_stop(),
        name='DeamonAssassin',
    )


def _restore_planes_tree() -> _BT:
    from Py4GWCoreLib import AgentArray, Agent

    def _blacklist_add(node: _BT.Node) -> _BT.NodeState:
        _blacklist_name(UWBlacklistName.BanishedDreamRider)
        return _BT.NodeState.SUCCESS

    def _blacklist_remove(node: _BT.Node) -> _BT.NodeState:
        _unblacklist_name(UWBlacklistName.BanishedDreamRider)
        return _BT.NodeState.SUCCESS

    def _wait_mindblade_spawn(
        x: float, y: float,
        clean_window_ms: int = 6_000,
        move_throttle_ms: int = 500,
    ) -> _BT:
        state: dict = {
            'clean_since_ms': None,
            'last_move_ms':   None,
        }

        def _check(node: _BT.Node) -> _BT.NodeState:
            now = int(Utils.GetBaseTimestamp())

            # Match legacy Underworld.Wait_for_Spawns: model 2380, not name decoding.
            # GetNameByID on many enemies can stress native code and has been observed to destabilize the client.
            found_mindblade = False
            try:
                raw = AgentArray.GetEnemyArray()
                for aid in list(raw or []):
                    try:
                        eid = int(aid)
                    except (TypeError, ValueError):
                        continue
                    if not Agent.IsValid(eid):
                        continue
                    if not Agent.IsAlive(eid):
                        continue
                    try:
                        if int(Agent.GetModelID(eid)) != _UW_SPECTRAL_MINDBLADE_MODEL_ID:
                            continue
                    except Exception:
                        continue
                    found_mindblade = True
                    break
            except Exception:
                found_mindblade = False

            # Always nudge player back to position when not in combat, regardless of Mindblade state.
            in_combat = bool(node.blackboard.get('COMBAT_ACTIVE', False))
            if not in_combat and not node.blackboard.get('PAUSE_MOVEMENT', False):
                last_move = state['last_move_ms']
                if last_move is None or now - last_move >= move_throttle_ms:
                    try:
                        Player.Move(x, y)
                    except Exception:
                        pass
                    state['last_move_ms'] = now

            if found_mindblade:
                state['clean_since_ms'] = None
                return _BT.NodeState.RUNNING

            # No Mindblade visible — start / continue clean window
            if state['clean_since_ms'] is None:
                state['clean_since_ms'] = now

            elapsed = now - state['clean_since_ms']
            if elapsed >= clean_window_ms:
                ConsoleLog(BOT_NAME, f'[RestorePlanes] WaitMindbladeSpawn: {clean_window_ms}ms clean — done.', Py4GW.Console.MessageType.Info)
                return _BT.NodeState.SUCCESS
            return _BT.NodeState.RUNNING

        return _BT(_BT.WaitUntilNode(
            name='WaitMindbladeSpawn',
            condition_fn=_check,
            throttle_interval_ms=500,
            timeout_ms=600_000,
        ))

    def _set_local_looting(enabled: bool, label: str) -> _BT.NodeState:
        """Toggle looting on this account only (BottingTree headless + local HeroAI option)."""
        loot_on = bool(enabled)
        bot.looting_enabled = loot_on
        bot.blackboard['looting_enabled'] = loot_on
        bot.headless_heroai.SetLootingEnabled(loot_on)

        account_email = Player.GetAccountEmail()
        if account_email:
            try:
                options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account_email)
                if options is not None:
                    options.Looting = bool(enabled)
                    GLOBAL_CACHE.ShMem.SetHeroAIOptionsByEmail(account_email, options)
            except Exception:
                pass

        ConsoleLog(
            BOT_NAME,
            f'[RestorePlanes] {label}: local looting={"on" if enabled else "off"}.',
            Py4GW.Console.MessageType.Info,
        )
        return _BT.NodeState.SUCCESS

    def _loot_off(_node: _BT.Node) -> _BT.NodeState:
        return _set_local_looting(False, 'DisableLootMindbladeWait')

    def _loot_on(_node: _BT.Node) -> _BT.NodeState:
        return _set_local_looting(True, 'EnableLootMindbladeWait')

    BT = Routines.BT
    return BT.Composite.Sequence(
        _BT(_BT.ActionNode(name='PurgeBlacklistNames', action_fn=_purge_blacklist_names_action)),
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True),
        _force_local_skills_on(),
        _BT(_BT.ActionNode(name='BlacklistChainedSoul', action_fn=_blacklist_chained_soul)),
        _BT(_BT.ActionNode(name='BlacklistDreamRider', action_fn=_blacklist_add)),
        _behemoth_guard_start(),
        BT.Movement.Move(x=-3560,  y=-5899),
        BT.Movement.Move(x=-2658,  y=-8620),
        BT.Movement.Move(x=1177,   y=-9402),
        BT.Movement.Move(x=6883,   y=-7797),
        BT.Movement.Move(x=9550,   y=-9787),
        BT.Movement.Move(x=11687,  y=-7969),
        BT.Movement.Move(x=12775,  y=-9787),
        BT.Movement.Move(x=11329,  y=-11618),
        BT.Movement.Move(x=13147,  y=-12587),
        BT.Movement.Move(x=13704,  y=-16024),
        _BT(_BT.ActionNode(name='UnblacklistDreamRider', action_fn=_blacklist_remove)),
        _behemoth_guard_stop(),
        _wait_out_of_combat(),
        BT.Player.Wait(duration_ms=10_000),
        _BT(_BT.ActionNode(name='DisableLootMindbladeWait', action_fn=_loot_off)),
        _wait_mindblade_spawn(x=13704, y=-16024),
        BT.Movement.Move(x=11037, y=-17988),
        _wait_mindblade_spawn(x=11345, y=-17852),
        _BT(_BT.ActionNode(name='EnableLootMindbladeWait', action_fn=_loot_on)),
        name='RestorePlanes',
    )








def _four_horsemen_tree() -> _BT:
    BT = Routines.BT

    def _set_follower_flags(x: float, y: float) -> _BT:
        # No Routines.BT equivalent — HeroAI multibox follower flags.
        def _tick(node: _BT.Node) -> _BT.NodeState:
            from Py4GWCoreLib import Agent as _Agent
            facing_angle = _Agent.GetRotationAngle(GLOBAL_CACHE.Party.GetPartyLeaderID())
            pairs = GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False)
            for account, options in pairs:
                party_pos = int(account.AgentPartyData.PartyPosition)
                if party_pos == 0:
                    continue
                options.IsFlagged       = True
                options.FlagPos.x       = float(x)
                options.FlagPos.y       = float(y)
                options.FlagFacingAngle = facing_angle
            return _BT.NodeState.SUCCESS

        return _BT(_BT.ActionNode(name='SetFollowerFlags', action_fn=_tick))

    return BT.Composite.Sequence(
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True),
        _force_local_skills_on(),
        BT.Movement.Move(13600, -11956),
        _set_follower_flags(13600, -11956),
        _dialog_until_quest_active(
            x=11337, y=-17962,
            dialog_id=0x806A01,
            quest_id=int(UWQuestID.TheFourHorsemen),
            label='TheFourHorsemen',
        ),
        BT.Player.Wait(duration_ms=30_000 if BotSettings.HardMode else 40_000),
        BT.Agents.MoveTargetInteractAndDialog(
            x=11337, y=-17962,
            dialog_id=0x8D,
        ),
        _clear_follower_flags(),
        BT.Movement.Move(x=-5782, y=12819),
        BT.Agents.MoveTargetInteractAndDialog(
            x=-5782, y=12819,
            dialog_id=0x8B,
        ),
        BT.Movement.Move(11524,-18292),
        _set_follower_flags(x=11524, y=-18292),
        _wait_quest_completed(hold_x=11524, hold_y=-18292, hold_radius=500.0),
        _clear_follower_flags(),
        _BT(_BT.ActionNode(
            name='BlacklistDreamRider',
            action_fn=lambda node: (
                _blacklist_add_dream_rider()
                or _BT.NodeState.SUCCESS
            ),
        )),
        name='TheFourHorsemen',
    )





def _restore_pools_tree() -> _BT:
    BT = Routines.BT
    return BT.Composite.Sequence(
        BT.Movement.Move(x=8263,   y=-19952),
        BT.Movement.Move(x=4203,   y=-19965),
        BT.Movement.Move(x=2106,   y=-19249),
        BT.Movement.Move(x=660,    y=-14710),
        BT.Movement.Move(x=-4290,  y=-15002),
        BT.Movement.Move(x=-8828,  y=-12415),
        BT.Movement.Move(x=-12000, y=-13901),
        BT.Movement.Move(x=-13592, y=-16701),
        BT.Movement.Move(x=-9916,  y=-17417),
        BT.Movement.Move(x=-9452,  y=-20098),
        BT.Movement.Move(x=-5736,  y=-20005),
        BT.Movement.Move(x=-5736,  y=-18904),
        BT.Movement.Move(x=-7156,  y=-18930),
        BT.Movement.Move(x=-7050,  y=-19448),
        name='RestorePools',
    )


def _terrorweb_queen_tree() -> _BT:
    BT = Routines.BT

    return BT.Composite.Sequence(
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True),
        _force_local_skills_on(),
        _BT(_BT.ActionNode(name='PurgeBlacklistNames', action_fn=_purge_blacklist_names_action)),
        _BT(_BT.ActionNode(name='BlacklistChainedSoul', action_fn=_blacklist_chained_soul)),
        _BT(_BT.ActionNode(name='BlacklistDreamRider', action_fn=lambda node: (_blacklist_add_dream_rider() or _BT.NodeState.SUCCESS))),
        _BT(_BT.ActionNode(name='BlacklistObsidianGuardian', action_fn=_blacklist_obsidian_guardian)),
        _dialog_until_quest_active(
            x=-6957, y=-19478,
            dialog_id=0x806B01,
            quest_id=int(UWQuestID.TerrorwebQueen),
            label='TerrorwebQueen',
        ),
        BT.Movement.Move(x=-12432, y=-15874),
        _wait_quest_completed(hold_x=-12432, hold_y=-15874, timeout_ms=300_000),
        BT.Movement.Move(x=-6957, y=-19478),
        BT.Agents.MoveTargetInteractAndDialog(
            x=-6957, y=-19478,
            dialog_id=0x8B,
        ),
        name='TerrorwebQueen',
    )


def _restore_pit_tree() -> _BT:
    BT = Routines.BT

    return BT.Composite.Sequence(
        _BT(_BT.ActionNode(name='PurgeBlacklistNames', action_fn=_purge_blacklist_names_action)),
        _BT(_BT.ActionNode(name='BlacklistChainedSoul', action_fn=_blacklist_chained_soul)),
        _BT(_BT.ActionNode(name='BlacklistDreamRider', action_fn=lambda node: (_blacklist_add_dream_rider() or _BT.NodeState.SUCCESS))),
        BT.Movement.Move(x=13672,  y=-16754),
        BT.Movement.Move(x=13390,  y=-10020),
        BT.Movement.Move(x=11416,  y=-2473),
        BT.Movement.Move(x=10105,  y=15),
        BT.Movement.Move(x=14086,  y=-283),
        BT.Movement.Move(x=14584,  y=2935),
        BT.Movement.Move(x=15612,  y=646),
        BT.Movement.MoveDirect(path_points=[Vec2f(12776, 1541)]),
        BT.Movement.Move(x=14086,  y=4129),
        BT.Movement.Move(x=12345,  y=4345),
        BT.Movement.Move(x=15247,  y=5506),
        BT.Movement.Move(x=11432,  y=7347),
        BT.Movement.Move(x=10868,  y=2387),
        BT.Movement.Move(x=9309,   y=7164),
        BT.Movement.Move(x=8729,   y=6435),
        name='RestorePit',
    )


def _imprisoned_spirits_tree() -> _BT:
    BT = Routines.BT

    LEFT_POINTS  = [(13849, 6602), (13876, 6752), (13985, 6840), (13598, 6779), (13845, 6489), (13845, 6489)]
    RIGHT_POINTS = [(12871, 2512), (12640, 2485), (12402, 2472), (12137, 2444), (12150, 2139), (12239, 2324)]

    _is_start_ms: list[int | None] = [None]

    def _start_timer(node: _BT.Node) -> _BT.NodeState:
        # Same clock as BehaviorTree wait nodes (GetBaseTimestamp ms).
        _is_start_ms[0] = int(Utils.GetBaseTimestamp())
        return _BT.NodeState.SUCCESS

    def _wait_is_elapsed_ms(target_ms: int) -> _BT.NodeState:
        start = _is_start_ms[0]
        if start is None:
            ConsoleLog(BOT_NAME, '[IS] Timer wait: start time missing (StartISTimer not run?).', Py4GW.Console.MessageType.Warning)
            return _BT.NodeState.FAILURE
        if int(Utils.GetBaseTimestamp()) - int(start) >= int(target_ms):
            return _BT.NodeState.SUCCESS
        return _BT.NodeState.RUNNING

    # No Routines.BT equivalent — HeroAI multibox follower flags.
    def _flag_teams(node: _BT.Node) -> _BT.NodeState:
        from Py4GWCoreLib import Agent as _Agent
        facing_angle = _Agent.GetRotationAngle(GLOBAL_CACHE.Party.GetPartyLeaderID())
        pairs = GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False)

        left_idx  = 0
        right_idx = 0

        for account, options in pairs:
            party_pos = int(account.AgentPartyData.PartyPosition)
            if party_pos == 0:
                continue

            email = str(account.AccountEmail or '').strip().lower()
            settings = ImprisonedSpiritsSettings

            if email in [e.strip().lower() for e in settings.LeftTeamEmails]:
                if left_idx < len(LEFT_POINTS):
                    px, py = LEFT_POINTS[left_idx]
                    left_idx += 1
                else:
                    continue
            else:
                if right_idx < len(RIGHT_POINTS):
                    px, py = RIGHT_POINTS[right_idx]
                    right_idx += 1
                else:
                    continue

            options.IsFlagged       = True
            options.FlagPos.x       = float(px)
            options.FlagPos.y       = float(py)
            options.FlagFacingAngle = facing_angle

        return _BT.NodeState.SUCCESS

    return BT.Composite.Sequence(
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True),
        _force_local_skills_on(),
        _BT(_BT.ActionNode(name='UnblacklistDreamRider', action_fn=_unblacklist_dream_rider)),
        BT.Movement.Move(x=13010, y=4452),
        _BT(_BT.ActionNode(name='FlagTeams', action_fn=_flag_teams)),
        _dialog_until_quest_active(
            x=8679, y=6235,
            dialog_id=0x806901,
            quest_id=int(UWQuestID.ImprisonedSpirits),
            label='ImprisonedSpirits',
        ),
        _BT(_BT.ActionNode(name='StartISTimer', action_fn=_start_timer)),
        BT.Movement.Move(x=13924, y=6914),
        _BT(_BT.WaitNode(
            name='WaitISTimer38s',
            check_fn=lambda: _wait_is_elapsed_ms(38_000),
            timeout_ms=240_000,
        )),
        _clear_follower_flags(),
        BT.Movement.Move(x=12497, y=2022),
        _BT(_BT.WaitNode(
            name='WaitISTimer90s',
            check_fn=lambda: _wait_is_elapsed_ms(90_000),
            timeout_ms=360_000,
        )),
        _BT(_BT.ActionNode(
            name='UnblacklistChainedSoul',
            action_fn=_unblacklist_chained_soul,
        )),
        BT.Movement.Move(x=10437, y=5005),
        _wait_quest_completed(),
        _BT(_BT.ActionNode(
            name='BlacklistChainedSoul',
            action_fn=_blacklist_chained_soul,
        )),
        BT.Agents.MoveTargetInteractAndDialog(
            x=8692, y=6292,
            dialog_id=0x8D,
        ),
        name='ImprisonedSpirits',
    )

def _restore_vale_tree() -> _BT:
    BT = Routines.BT
    _r = 2000.0

    return BT.Composite.Sequence(
        BT.Agents.MoveTargetInteractAndDialog(
            x=-5806, y=12831,
            dialog_id=0x806C01,
        ),
        BT.Movement.MoveAndKill(Vec2f(-8660, 5655), clear_area_radius=_r),
        BT.Movement.MoveAndKill(Vec2f(-9431, 1659), clear_area_radius=_r),
        BT.Movement.MoveAndKill(Vec2f(-11123, 2531), clear_area_radius=_r),
        BT.Movement.MoveAndKill(Vec2f(-11926, 1146), clear_area_radius=_r),
        BT.Movement.MoveAndKill(Vec2f(-10691, 98), clear_area_radius=_r),
        BT.Movement.MoveAndKill(Vec2f(-15424, 1319), clear_area_radius=_r),
        BT.Movement.MoveAndKill(Vec2f(-13246, 5110), clear_area_radius=_r),
        name='RestoreVale',
    )


def _wrathfull_spirits_tree() -> _BT:
    BT = Routines.BT

    _kr = 2000.0

    return BT.Composite.Sequence(
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True),
        _force_local_skills_on(),
        _BT(_BT.ActionNode(name='PurgeBlacklistNames', action_fn=_purge_blacklist_names_action)),
        _BT(_BT.ActionNode(name='BlacklistChainedSoul', action_fn=_blacklist_chained_soul)),
        _BT(_BT.ActionNode(name='BlacklistTorturedSpirits', action_fn=_blacklist_tortured_spirits)),
        _dialog_until_quest_active(
            x=-13217, y=5167,
            dialog_id=0x806E01,
            quest_id=int(UWQuestID.WrathfulSpirits),
            label='WrathfulSpirits',
        ),
        BT.Movement.Move(x=-13422, y=973),
        _BT(_BT.ActionNode(name='UnblacklistTorturedSpirits', action_fn=_unblacklist_tortured_spirits)),
        BT.Movement.MoveAndKill(Vec2f(-13791, 1642), clear_area_radius=_kr),
        BT.Movement.MoveAndKill(Vec2f(-12889, 963), clear_area_radius=_kr),
        BT.Movement.MoveAndKill(Vec2f(-11445, 1154), clear_area_radius=_kr),
        BT.Movement.MoveAndKill(Vec2f(-10554, 1695), clear_area_radius=_kr),
        BT.Movement.MoveAndKill(Vec2f(-9481, 963), clear_area_radius=_kr),
        BT.Movement.MoveAndKill(Vec2f(-9949, 177), clear_area_radius=_kr),
        BT.Movement.MoveAndKill(Vec2f(-11498, -173), clear_area_radius=_kr),
        BT.Movement.MoveAndKill(Vec2f(-12677, -205), clear_area_radius=_kr),
        BT.Movement.MoveAndKill(Vec2f(-13622, 336), clear_area_radius=_kr),
        BT.Movement.MoveAndKill(Vec2f(-12974, 4116), clear_area_radius=_kr),
        BT.Movement.MoveAndKill(Vec2f(-14184, 7279), clear_area_radius=_kr),
        BT.Movement.MoveAndKill(Vec2f(-15055, 3755), clear_area_radius=_kr),
        BT.Movement.MoveAndKill(Vec2f(-13409, 4933), clear_area_radius=_kr),
        BT.Movement.MoveAndKill(Vec2f(-13217, 5167), clear_area_radius=_kr),
        BT.Agents.MoveTargetInteractAndAutomaticDialog(
            x=-13217, y=5167,
            button_number=0,
        ),
        BT.Agents.MoveTargetInteractAndDialog(
            x=-13217, y=5167,
            dialog_id=0x8D,
        ),
        name='WrathfullSpirits',
    )


def _unwanted_guests_tree() -> _BT:
    BT = Routines.BT
    _fx, _fy = -2816.0, 10036.0

    def _set_follower_flags_at_hold(node: _BT.Node) -> _BT.NodeState:
        from Py4GWCoreLib import Agent as _Agent
        facing_angle = _Agent.GetRotationAngle(GLOBAL_CACHE.Party.GetPartyLeaderID())
        for account, options in GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False):
            if int(account.AgentPartyData.PartyPosition) == 0:
                continue
            options.IsFlagged       = True
            options.FlagPos.x       = _fx
            options.FlagPos.y       = _fy
            options.FlagFacingAngle = facing_angle
        return _BT.NodeState.SUCCESS

    return BT.Composite.Sequence(
        _BT(_BT.ActionNode(name='PrepareUnwantedGuestsBlacklist', action_fn=_prepare_unwanted_guests_blacklist)),
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True),
        _force_local_skills_on(),
        BT.Movement.Move(x=_fx, y=_fy),
        _BT(_BT.ActionNode(name='SetFollowerFlagsUnwantedGuests', action_fn=_set_follower_flags_at_hold)),
        BT.Movement.Move(x=-5850, y=12818),
        _dialog_until_quest_active(
            x=-5850, y=12818,
            dialog_id=0x806701,
            quest_id=int(UWQuestID.UnwantedGuests),
            label='UnwantedGuests',
        ),
        BT.Movement.Move(x=_fx, y=_fy),
        BT.Movement.Move(x=-5850, y=12818),
        _clear_follower_flags(),
        BT.Agents.MoveTargetInteractAndDialog(
            x=-5850, y=12818,
            dialog_id=0x91,
        ),
        BT.Movement.Move(x=-13858, y=2415,   tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=-13739, y=1320,   tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=-11888, y=929,    tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=-9298,  y=2067,   tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=-7608,  y=6704,   tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=-5221,  y=8946,   tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=-6283,  y=10271,  tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=-3735,  y=13311,  tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=-202,   y=13337,  tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=1199,   y=10543,  tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=1344,   y=10008,  tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=2864,   y=10169,  tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=494,    y=9625,   tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=-109,   y=8929,   tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=290,    y=7281,   tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=-1799,  y=5914,   tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=-3158,  y=3426,   tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=-3676,  y=946,    tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=-2546,  y=-438,   tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=-1068,  y=-753,   tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=316,    y=131,    tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=95,     y=1787,   tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=-355,   y=2135,   tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=87,     y=3672,   tolerance=400, timeout_ms=60_000),
        BT.Movement.Move(x=1539,   y=4708,   tolerance=400, timeout_ms=60_000),
        name='UnwantedGuests',
    )


def _restore_wastes_tree() -> _BT:
    BT = Routines.BT
    _kr = 2000.0
    return BT.Composite.Sequence(
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True),
        _force_local_skills_on(),
        _BT(_BT.ActionNode(name='UnblacklistVengefulAatxe', action_fn=_unblacklist_vengeful_aatxe)),
        BT.Movement.Move(x=8138, y=16929),
        BT.Movement.Move(x=6210, y=19120),
        BT.Movement.MoveAndKill(Vec2f(6320, 21167), clear_area_radius=_kr),
        BT.Movement.MoveAndKill(Vec2f(4282, 15902), clear_area_radius=_kr),
        BT.Movement.MoveAndKill(Vec2f(2617, 16810), clear_area_radius=_kr),
        BT.Movement.MoveAndKill(Vec2f(2702, 21583), clear_area_radius=_kr),
        BT.Movement.MoveAndKill(Vec2f(511, 21473), clear_area_radius=_kr),
        BT.Movement.MoveAndKill(Vec2f(537, 18407), clear_area_radius=_kr),
        name='RestoreWastes',
    )


def _servants_of_grenth_tree() -> _BT:
    BT = Routines.BT
    _points: list[tuple[float, float]] = [
        (2559, 20301),
        (3032, 20148),
        (2813, 20590),
        (2516, 19665),
        (3231, 19472),
        (3691, 19979),
        (2039, 20175),
    ]

    def _set_spread_flags(node: _BT.Node) -> _BT.NodeState:
        from Py4GWCoreLib import Agent as _Agent

        facing_angle = _Agent.GetRotationAngle(GLOBAL_CACHE.Party.GetPartyLeaderID())
        pairs = GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False)
        for account, options in pairs:
            party_pos = int(account.AgentPartyData.PartyPosition)
            # PartyPosition 0 is local leader; followers are 1..7.
            if party_pos <= 0:
                continue
            idx = party_pos - 1
            if idx < 0 or idx >= len(_points):
                continue
            px, py = _points[idx]
            options.IsFlagged = True
            options.FlagPos.x = float(px)
            options.FlagPos.y = float(py)
            options.FlagFacingAngle = facing_angle
        return _BT.NodeState.SUCCESS

    return BT.Composite.Sequence(
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True),
        _force_local_skills_on(),
        BT.Movement.Move(x=2700, y=19952),
        _BT(_BT.ActionNode(name='SetServantsOfGrenthFlags', action_fn=_set_spread_flags)),
        BT.Movement.Move(x=554, y=18384),
        _dialog_until_quest_active(
            x=554, y=18384,
            dialog_id=0x806601,
            quest_id=int(UWQuestID.ServantsOfGrenth),
            label='ServantsOfGrenth',
        ),
        BT.Movement.Move(x=2700, y=19952),
        _wait_quest_completed(),
        _clear_follower_flags(),
        name='ServantsOfGrenth',
    )








_SPIRIT_FORM_BUFF_ID = 3134










def _dhuum_tree() -> _BT:
    """
    Dhuum / The Nightmare Cometh.

    Part 1: King Frozenwind (2403) dialog button 0, move to (-12093, 17282),
            disable HeroAI combat, flag accounts, enable Dhuum Helper.
    """
    BT = Routines.BT
    return BT.Composite.Sequence(
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True),
        _force_local_skills_on(),
        _follow_king_frozenwind(),
        BT.Agents.MoveTargetInteractAndAutomaticDialogByModelID(
            _KING_FROZENWIND_MODEL_ID,
            button_number=0,
            log=True,
        ),
        BT.Movement.Move(x=-12093, y=17282),
        _disable_heroai_combat_all(),
        _flag_dhuum_accounts(),
        _enable_dhuum_helper_on_all_accounts(),
        BT.Player.Wait(10000),
        BT.Movement.Move(-15373, 17298, pause_on_combat=False),
        _wait_for_spirit_forms(),
        _enable_heroai_combat_all(),
        _wait_for_uw_chest(),
        name='Dhuum',
    )


def _get_local_party_slot_index() -> int:
    """Return the 0-based party-slot index of the local player, or 0 on any error."""
    try:
        slot = GLOBAL_CACHE.Party.GetOwnPartyNumber()
        return max(0, int(slot))
    except Exception:
        return 0


def _loot_chest_tree() -> _BT:
    """Leader moves to the chest, then sends InteractWithTarget to every account
    in the same map one by one with a 4-second gap between each — including itself.
    Afterwards all accounts interact with King Frozenwind (button 0) twice, then
    resign if BotSettings.Repeat is enabled.

    This mirrors the pattern in the legacy Underworld.py and works regardless of
    whether followers are running UnderworldBT independently: every HeroAI /
    BottingTree instance processes SharedCommandType.InteractWithTarget.
    """
    BT = Routines.BT
    from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType as _SCT
    from Py4GWCoreLib import AgentArray as _AA

    def _find_king_id() -> int:
        for agent_id in (_AA.GetAgentArray() or []):
            if not Agent.IsValid(agent_id):
                continue
            try:
                if int(Agent.GetModelID(agent_id)) == _KING_FROZENWIND_MODEL_ID:
                    return int(agent_id)
            except Exception:
                pass
        return 0

    king_id = _find_king_id()
    if king_id:
        ConsoleLog(BOT_NAME, f'[LootChest] King Frozenwind found (id={king_id}).', Py4GW.Console.MessageType.Info)
    else:
        ConsoleLog(BOT_NAME, '[LootChest] King Frozenwind not found — dialog commands will be skipped gracefully.', Py4GW.Console.MessageType.Warning)

    king_params = (float(king_id), 0.0, 0.0, 0.0)

    _state: dict = {
        'chest_id':    None,   # gadget agent ID, resolved on first tick
        'accounts':    None,   # list of AccountData for same-map accounts
        'index':       0,      # next account to send to
        'next_ms':     None,   # earliest timestamp (ms) for next send
    }

    def _find_chest_id() -> int | None:
        from Py4GWCoreLib import AgentArray as _AA
        for agent_id in _AA.GetAgentArray():
            if not Agent.IsValid(agent_id):
                continue
            if not Agent.IsGadget(agent_id):
                continue
            if Utils.Distance(_UW_CHEST_POS, Agent.GetXY(agent_id)) <= _UW_CHEST_RADIUS:
                return agent_id
        return None

    def _tick(node: _BT.Node) -> _BT.NodeState:
        # ── First tick: resolve chest and account list ────────────────────────
        if _state['chest_id'] is None:
            chest_id = _find_chest_id()
            if chest_id is None:
                ConsoleLog(BOT_NAME, '[LootChest] Chest not found — skipping loot.', Py4GW.Console.MessageType.Warning)
                return _BT.NodeState.SUCCESS
            _state['chest_id'] = chest_id

            current_map_id = int(Map.GetMapID() or 0)
            _state['accounts'] = [
                acc for acc in (GLOBAL_CACHE.ShMem.GetAllAccountData() or [])
                if int(getattr(acc.AgentData.Map, 'MapID', 0) or 0) == current_map_id
            ]
            _state['index']   = 0
            _state['next_ms'] = int(Utils.GetBaseTimestamp())
            ConsoleLog(BOT_NAME, f'[LootChest] Found chest id={chest_id}, looting {len(_state["accounts"])} account(s).', Py4GW.Console.MessageType.Info)

        # ── All accounts sent ─────────────────────────────────────────────────
        accounts = _state['accounts']
        if _state['index'] >= len(accounts):
            return _BT.NodeState.SUCCESS

        # ── Wait for slot gap ─────────────────────────────────────────────────
        if int(Utils.GetBaseTimestamp()) < _state['next_ms']:
            return _BT.NodeState.RUNNING

        # ── Send to next account (BT.Shared.SendCommand — same transport as SendMessage) ──
        acc   = accounts[_state['index']]
        email = str(getattr(acc, 'AccountEmail', '') or '')
        send_tree = BT.Shared.SendCommand(
            _SCT.InteractWithTarget,
            params=(float(_state['chest_id']), 0.0, 0.0, 0.0),
            recipients=[email],
            include_self=True,
            log=False,
        )
        send_tree.blackboard = node.blackboard
        send_result = send_tree.tick()
        if send_result == _BT.NodeState.FAILURE:
            ConsoleLog(BOT_NAME, f'[LootChest] InteractWithTarget failed for {email}.', Py4GW.Console.MessageType.Warning)
        else:
            ConsoleLog(BOT_NAME, f'[LootChest] Sent InteractWithTarget to {email}.', Py4GW.Console.MessageType.Info)
        _state['index']  += 1
        _state['next_ms'] = int(Utils.GetBaseTimestamp()) + 4_000
        return _BT.NodeState.RUNNING

    return BT.Composite.Sequence(
        BT.Movement.Move(x=_UW_CHEST_POS[0], y=_UW_CHEST_POS[1], tolerance=400),
        _BT(_BT.WaitUntilNode(
            name='LootChestSequential',
            condition_fn=_tick,
            throttle_interval_ms=100,
            timeout_ms=300_000,
        )),
        BT.Player.Wait(duration_ms=15_000),
        BT.Shared.SendAndWait(
            _SCT.TakeDialogWithTarget,
            params=king_params,
            include_self=True,
            timeout_ms=30_000,
            log=True,
        ),
        BT.Player.Wait(duration_ms=5_000),
        BT.Shared.SendAndWait(
            _SCT.TakeDialogWithTarget,
            params=king_params,
            include_self=True,
            timeout_ms=30_000,
            log=True,
        ),
        BT.Player.Wait(duration_ms=5_000),
        _BT(_BT.SubtreeNode(
            name='ResignIfRepeat',
            subtree_fn=lambda node: (
                BT.Composite.Sequence(
                    BT.Shared.ResignAllAccounts(timeout_ms=15_000, log=True),
                    BT.Player.Resign(log=True),
                    _BT(_BT.WaitUntilNode(
                        name='WaitUntilOutpost',
                        condition_fn=lambda n: (
                            _BT.NodeState.SUCCESS
                            if (Map.IsMapReady() and not Map.IsExplorable())
                            else _BT.NodeState.RUNNING
                        ),
                        timeout_ms=120_000,
                    )),
                    _BT(_BT.ActionNode(
                        name='RestartToEnterUW',
                        action_fn=lambda n: (
                            n.blackboard.__setitem__('restart_step_name_request', 'Enter Underworld')
                            or _BT.NodeState.SUCCESS
                        ),
                    )),
                    name='ResignAndRestart',
                )
                if BotSettings.Repeat
                else _BT(_BT.ActionNode(name='SkipResign', action_fn=lambda n: _BT.NodeState.SUCCESS))
            ),
        )),
        name='LootChest',
    )








# Names temporarily added by the bot to EnemyBlacklist during specific quest steps.
# Must be cleared on wipe recovery to avoid leaving stale name entries across runs,
# which would cause GetNameByID to be called on dying/despawning agents → TextParser crash.




# How many consecutive ticks IsPartyWiped() must be True before recovery activates.
# Kept high to avoid false positives from brief death windows in combat.
_WIPE_CONFIRM_TICKS = 60  # ~3 seconds at 20 fps


# ── Services ─────────────────────────────────────────────────────────────────

def _build_step_timer_service():
    """Service: watches blackboard step transitions and records cumulative elapsed time.

    On each step transition X → Y:
    - If Y == 'Enter Underworld': new run starting → clear this-run display times.
    - If Y == 'Clear the Chamber': start the cumulative run timer.
    - If X is a timed quest and the timer is running: record X's elapsed time,
      append to _quest_times_log, and flush to JSON.
    """
    def _tick(node) -> '_BT.NodeState':
        current_step = str(node.blackboard.get('current_step_name', '') or '')
        last_step    = _timing_state['last_step']

        if current_step == last_step:
            return _BT.NodeState.RUNNING

        now_ms = int(time.monotonic() * 1000)

        if current_step == 'Enter Underworld':
            _quest_completion_times.clear()
            _timing_state['run_start_ms'] = None

        if current_step == _RUN_START_QUEST:
            _timing_state['run_start_ms'] = now_ms

        run_start = _timing_state['run_start_ms']
        if last_step and last_step in _TIMED_QUESTS and run_start is not None:
            elapsed_ms = now_ms - run_start
            _quest_completion_times[last_step] = elapsed_ms
            _quest_times_log.setdefault(last_step, []).append(elapsed_ms // 1000)
            _save_quest_times_log()
            if last_step == 'Loot Chest':
                total_s = elapsed_ms // 1000
                _append_run_log(f'Run completed in {_fmt_s(total_s)}')

        _timing_state['last_step'] = current_step
        return _BT.NodeState.RUNNING

    return _BT(_BT.ActionNode(name='StepTimerService', action_fn=_tick))

def _build_uw_wipe_recovery_tree() -> _BT:
    """No Routines.BT equivalent — Party.ReturnToOutpost for wipe recovery."""

    import time as _t
    _state: dict = {
        'active': False,
        'wipe_ticks': 0,
        'last_return_ms': 0.0,
    }

    def _tick(node: _BT.Node) -> _BT.NodeState:
        from Py4GWCoreLib.Map import Map as _Map
        from Py4GWCoreLib.Routines import Routines as _R

        now = _t.monotonic() * 1000.0
        map_ready     = _Map.IsMapReady()
        in_explorable = map_ready and _Map.IsExplorable()
        in_outpost    = map_ready and _Map.IsOutpost()

        current_step = str(node.blackboard.get('current_step_name', '') or '')
        in_uw_step   = current_step in _UW_EXPLORABLE_STEPS

        # Signal A: in a UW quest step but already in outpost = kicked out after wipe.
        #           Unambiguous – activate immediately, no debounce needed.
        kicked_to_outpost = in_uw_step and in_outpost

        # Signal B: all party members dead while still inside the explorable.
        #           Requires _WIPE_CONFIRM_TICKS consecutive True ticks to filter
        #           brief death windows (e.g. one member dies and is instantly rezzed).
        #           IsPartyDefeated() is intentionally excluded: it fires unreliably
        #           during combat and causes false ReturnToOutpost() calls.
        all_dead_in_uw = in_explorable and in_uw_step and _R.Checks.Party.IsPartyWiped()

        is_wiped = kicked_to_outpost or all_dead_in_uw

        if not _state['active']:
            if not is_wiped:
                _state['wipe_ticks'] = 0
                node.blackboard['party_wipe_recovery_active'] = False
                return _BT.NodeState.RUNNING

            _state['wipe_ticks'] += 1
            if not kicked_to_outpost and _state['wipe_ticks'] < _WIPE_CONFIRM_TICKS:
                return _BT.NodeState.RUNNING

            _state['active'] = True
            _state['wipe_ticks'] = 0
            _state['last_return_ms'] = 0.0
            node.blackboard['party_wipe_recovery_active'] = True
            step_at_wipe = str(node.blackboard.get('current_step_name', '') or 'unknown')
            _append_run_log(f'Party wiped at step: {step_at_wipe}')
            if step_at_wipe and step_at_wipe != 'unknown':
                _wipe_counts_log[step_at_wipe] = _wipe_counts_log.get(step_at_wipe, 0) + 1
                _save_wipe_counts()
            _clear_bot_blacklist_names()
            return _BT.NodeState.RUNNING

        node.blackboard['party_wipe_recovery_active'] = True

        if in_outpost and GLOBAL_CACHE.Party.IsPartyLoaded():
            node.blackboard['restart_step_name_request'] = 'Enter Underworld'
            _state['active'] = False
            _state['wipe_ticks'] = 0
            _state['last_return_ms'] = 0.0
            node.blackboard['party_wipe_recovery_active'] = False
            return _BT.NodeState.SUCCESS

        if now - float(_state['last_return_ms']) >= 1000.0:
            GLOBAL_CACHE.Party.ReturnToOutpost()
            _state['last_return_ms'] = now

        return _BT.NodeState.RUNNING

    return _BT(_BT.ActionNode(name='PartyWipeRecoveryService', action_fn=_tick, aftercast_ms=0))




def _skip_background_upkeep(blackboard: dict) -> bool:
    """True when parallel upkeep should not fight planner movement (loot interrupt, wipe, load)."""
    if blackboard.get('PAUSE_MOVEMENT', False):
        return True
    if blackboard.get('party_wipe_recovery_active', False):
        return True
    if str(blackboard.get('current_step_name', '') or '') == 'Enter Underworld':
        return True
    try:
        if Map.IsMapLoading() or not Map.IsMapReady():
            return True
    except Exception:
        pass
    return False




def _build_uw_priority_model_map() -> dict[int, int]:
    """Map model_id -> priority index without runtime GetNameByID."""
    from Py4GWCoreLib.model_data import ModelData

    name_prio = {name.strip().lower(): idx for idx, name in enumerate(UW_TARGET_PRIORITY)}
    model_map: dict[int, int] = {}
    for model_id, data in ModelData.items():
        model_name = str(data.get('name', '') or '').strip().lower()
        prio = name_prio.get(model_name)
        if prio is None:
            continue
        mid = int(model_id)
        if mid not in model_map or prio < model_map[mid]:
            model_map[mid] = prio
    return model_map


def _build_priority_target_service() -> _BT:
    """Background service: call the highest-priority UW enemy in range as party target.

    Port of UnderworldV2 ``BuildPriorityTargetService`` / ``CallPriorityTarget``.
    Uses HeroAI ``CallTarget`` on the party leader via ``_party_call_or_change_target``.
    Matches enemies by model ID only (no GetNameByID — TextParser crash on dying agents).
    """
    priority_by_model = _build_uw_priority_model_map()
    sentinel_priority = len(UW_TARGET_PRIORITY)
    range_sq = float(_UW_PRIORITY_TARGET_RANGE) * float(_UW_PRIORITY_TARGET_RANGE)
    state: dict = {'last_call_ms': 0.0, 'last_scan_ms': 0.0}

    def _agent_priority_from_model(model_id: int) -> int:
        return priority_by_model.get(int(model_id), -1)

    def _blacklist_names_snapshot() -> frozenset[str]:
        try:
            from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist as _EBL

            return frozenset(_EBL().get_all_names())
        except Exception:
            return frozenset()

    def _tick(node: _BT.Node) -> _BT.NodeState:
        from Py4GWCoreLib.AgentArray import AgentArray as _AgentArray

        now_ms = time.monotonic() * 1000.0
        if (now_ms - state['last_scan_ms']) < _UW_PRIORITY_TARGET_SCAN_INTERVAL_MS:
            return _BT.NodeState.RUNNING
        state['last_scan_ms'] = now_ms

        if _skip_background_upkeep(node.blackboard):
            return _BT.NodeState.RUNNING
        try:
            if not Map.IsExplorable() or int(Map.GetMapID()) != int(UW_MAP_ID):
                return _BT.NodeState.RUNNING
        except Exception:
            return _BT.NodeState.RUNNING

        try:
            leader_id = int(GLOBAL_CACHE.Party.GetPartyLeaderID() or 0)
            local_id = int(Player.GetAgentID() or 0)
        except Exception:
            leader_id = 0
            local_id = 0
        if leader_id > 0 and local_id > 0 and local_id != leader_id:
            return _BT.NodeState.RUNNING

        player_pos = Player.GetXY()
        if not player_pos:
            return _BT.NodeState.RUNNING

        blacklist_names = _blacklist_names_snapshot()
        px, py = float(player_pos[0]), float(player_pos[1])
        best_agent_id = 0
        best_priority = sentinel_priority
        best_model_id = 0
        try:
            enemy_ids = list(_AgentArray.GetEnemyArray() or [])
        except Exception:
            return _BT.NodeState.RUNNING

        for raw_agent_id in enemy_ids:
            try:
                agent_id = int(raw_agent_id)
                if not Agent.IsAlive(agent_id):
                    continue
                model_id = int(Agent.GetModelID(agent_id))
                try:
                    agent_name = (Agent.GetNameByID(agent_id) or '').strip().lower()
                except Exception:
                    agent_name = ''
                if agent_name and agent_name in blacklist_names:
                    continue
                prio = _agent_priority_from_model(model_id)
                if prio == -1 or prio >= best_priority:
                    continue
                ax, ay = Agent.GetXY(agent_id)
                dx, dy = px - float(ax), py - float(ay)
            except Exception:
                continue
            if dx * dx + dy * dy > range_sq:
                continue
            best_priority = prio
            best_agent_id = agent_id
            best_model_id = model_id

        if best_agent_id == 0:
            return _BT.NodeState.RUNNING
        try:
            current_target_id = int(Player.GetTargetID() or 0)
        except Exception:
            current_target_id = 0

        if current_target_id != 0:
            current_prio = sentinel_priority
            try:
                current_model_id = int(Agent.GetModelID(current_target_id))
                current_target_name = (Agent.GetNameByID(current_target_id) or '').strip().lower()
                if not (current_target_name and current_target_name in blacklist_names):
                    current_prio = _agent_priority_from_model(current_model_id)
                    if current_prio == -1:
                        current_prio = sentinel_priority
            except Exception:
                pass
            if best_priority >= current_prio and (now_ms - state['last_call_ms']) < _UW_PRIORITY_TARGET_COOLDOWN_MS:
                return _BT.NodeState.RUNNING

        if (now_ms - state['last_call_ms']) < _UW_PRIORITY_TARGET_COOLDOWN_MS:
            return _BT.NodeState.RUNNING

        try:
            if not Agent.IsValid(best_agent_id) or not Agent.IsAlive(best_agent_id):
                return _BT.NodeState.RUNNING
            best_name_final = (Agent.GetNameByID(best_agent_id) or '').strip().lower()
            if best_name_final and best_name_final in blacklist_names:
                return _BT.NodeState.RUNNING
        except Exception:
            return _BT.NodeState.RUNNING

        _party_call_or_change_target(int(best_agent_id))
        state['last_call_ms'] = now_ms
        return _BT.NodeState.RUNNING

    return _BT(
        _BT.RepeaterForeverNode(
            child=_BT.ActionNode(name='PriorityTargetServiceTick', action_fn=_tick),
            name='PriorityTargetService',
        )
    )


def _build_consolidated_consumable_upkeep_service() -> _BT:
    """Single background service that round-robins the per-item ConsumableService trees.

    Many parallel ConsumableService branches (one per con) all ticked alongside HeroAI +
    planner; each can issue ``UseItem`` and hit effect scans. That competes with movement
    and ``WaitNode`` timing and showed up as frequent *Planner tree failed*.  Here only
    **one** consumable subtree runs per frame, in rotation over active items.
    """
    _inners: dict[str, _BT] = {}

    def _inner_for(prop: str) -> _BT:
        if prop not in _inners:
            preset = Routines.BT.Upkeepers.CONSUMABLE_UPKEEP_PRESETS.get(prop, {})
            model_id = int(preset.get('model_id', 0))
            _inners[prop] = Routines.BT.Upkeepers.ConsumableService(model_id)
        return _inners[prop]

    def _tick(node: _BT.Node) -> _BT.NodeState:
        if not BotSettings.UseCons:
            return _BT.NodeState.RUNNING
        if _skip_background_upkeep(node.blackboard):
            return _BT.NodeState.RUNNING
        active = [p for p, _, _, _ in _CONS_DEFS if ConsSettings.is_active(p)]
        if not active:
            return _BT.NodeState.RUNNING

        rr = int(node.blackboard.setdefault('uw_cons_upkeep_rr', 0) or 0)
        prop = active[rr % len(active)]
        node.blackboard['uw_cons_upkeep_rr'] = rr + 1

        inner = _inner_for(prop)
        inner.blackboard = node.blackboard
        return inner.tick()

    return _BT(_BT.ActionNode(name='ConsumableUpkeepConsolidated', action_fn=_tick, aftercast_ms=0))


# ── Bot registration ─────────────────────────────────────────────────────────

bot.SetNamedPlannerSteps([
    ('Enter Underworld',    _enter_underworld_tree),
    ('Clear the Chamber',   _clear_the_chamber_tree),
    ('Pass the Mountains',  _pass_the_mountains_tree),
    ('Restore Mountains',   _restore_mountains_tree),
    ('Deamon Assassin',     _deamon_assassin_tree),
    ('Restore Planes',      _restore_planes_tree),
    ('The Four Horsemen',   _four_horsemen_tree),
    ('Restore Pools',       _restore_pools_tree),
    ('Terrorweb Queen',     _terrorweb_queen_tree),
    ('Restore Pit',         _restore_pit_tree),
    ('Imprisoned Spirits',  _imprisoned_spirits_tree),
    ('Restore Vale',        _restore_vale_tree),
    ('Wrathfull Spirits',   _wrathfull_spirits_tree),
    ('Unwanted Guests',     _unwanted_guests_tree),
    ('Restore Wastes',      _restore_wastes_tree),
    ('Servants of Grenth',  _servants_of_grenth_tree),
    ('Dhuum',               _dhuum_tree),
    ('Loot Chest',          _loot_chest_tree),
])

# Party wipe: ``BottingTree.Create`` leaves ``_service_steps`` empty — register UW recovery explicitly
# (always restart from 'Enter Underworld', not the failed step).
_wipe_svc = 'PartyWipeRecoveryService'
_wipe_i = next((_i for _i, (_n, _) in enumerate(bot._service_steps) if _n == _wipe_svc), None)
if _wipe_i is None:
    bot.AddServiceTree(_wipe_svc, _build_uw_wipe_recovery_tree)
else:
    bot._service_steps[_wipe_i] = (_wipe_svc, _build_uw_wipe_recovery_tree)
    bot._service_trees[_wipe_i] = (_wipe_svc, bot._coerce_runtime_tree(_build_uw_wipe_recovery_tree))
    bot._rebuild_root_tree()

bot.AddServiceTree('StepTimer',               _build_step_timer_service)
bot.AddServiceTree('PriorityTargetService',   _build_priority_target_service)
bot.AddServiceTree('ConsumableUpkeep', _build_consolidated_consumable_upkeep_service)
bot.AddServiceTree('BehemothGuard', _build_behemoth_guard_service)

# ── COMBAT_ACTIVE tightening ───────────────────────────────────────────────
# The SharedMemory InAggro field can scan up to Spellcast range (~5000 units)
# when any party member is in aggro AND the leader was recently in aggro
# (stay-alert window = 750 ms).  In Underworld, followers are always fighting,
# so this feedback loop keeps COMBAT_ACTIVE=True even when the leader is far
# from every enemy, which freezes BT.Movement.Move (pause_on_combat=True).
#
# Fix: monkey-patch _tick_planner so that, just before the planner tree ticks
# and its Move nodes read COMBAT_ACTIVE, we replace any True value from the
# Replaces the planner's broad SharedMemory scan with a live radius scan (≈ Earshot).
# HeroAI's own combat logic is untouched; only the planner pause is affected.
_PAUSE_ON_DANGER_RANGE: float = 1020.0

_orig_tick_planner = bot._tick_planner


def _in_aggro_excluding_blacklist() -> bool:
    """Live radius scan that ignores blacklisted enemies (name-based)."""
    from Py4GWCoreLib.AgentArray import AgentArray
    from Py4GWCoreLib.Agent import Agent
    from Py4GWCoreLib.Player import Player as _Player
    from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist

    bl_names = frozenset(EnemyBlacklist().get_all_names())
    player_id = _Player.GetAgentID()
    player_pos = _Player.GetXY()
    if not player_pos:
        return False

    enemy_array = AgentArray.GetEnemyArray()
    if not enemy_array:
        return False

    px, py = player_pos
    radius_sq = _PAUSE_ON_DANGER_RANGE * _PAUSE_ON_DANGER_RANGE
    for agent_id in enemy_array:
        if agent_id == player_id:
            continue
        if not Agent.IsAlive(agent_id):
            continue
        try:
            name = (Agent.GetNameByID(agent_id) or '').strip().lower()
            if name and name in bl_names:
                continue
        except Exception:
            pass
        pos = Agent.GetXY(agent_id)
        if not pos:
            continue
        dx, dy = px - pos[0], py - pos[1]
        if dx * dx + dy * dy <= radius_sq:
            return True
    return False


def _tight_combat_active_planner_tick(node):  # type: ignore[override]
    bb = node.blackboard
    if str(bb.get('current_step_name', '') or '') != 'Enter Underworld':
        try:
            map_ok = Map.IsMapReady() and not Map.IsMapLoading()
        except Exception:
            map_ok = False
        if map_ok and bb.get('COMBAT_ACTIVE', False):
            bb['COMBAT_ACTIVE'] = _in_aggro_excluding_blacklist()
    return _orig_tick_planner(node)


bot._tick_planner = _tight_combat_active_planner_tick  # type: ignore[method-assign]

_map_stable_frames: int = 0
_MAP_STABLE_THRESHOLD: int = 10


def main() -> None:
    global _map_stable_frames

    if not Map.IsMapDataLoaded():
        _map_stable_frames = 0
        return

    _map_stable_frames += 1
    if _map_stable_frames < _MAP_STABLE_THRESHOLD:
        return

    if Routines.Checks.Map.MapValid():
        bot.tick()

    bot.UI.draw_window(
        icon_path=os.path.join(Py4GW.Console.get_projects_path(), MODULE_ICON),
        main_child_dimensions=(550, 570),
        additional_ui=_draw_main_additional_ui,
        extra_tabs=[('Run Log', _draw_run_log)],
    )


if __name__ == '__main__':
    main()
