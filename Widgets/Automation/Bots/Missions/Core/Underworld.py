
# ╔══════════════════════════════════════════════════════════════════════════════
# ║  File    : UnderworldBT.py
# ║  Purpose : BehaviorTree port of the Underworld bot.
# ║            BehaviorTree planner, parallel services, stats UI.
# ╚══════════════════════════════════════════════════════════════════════════════

import enum
import math
import os
import time

import Py4GW
import PyImGui
from Py4GWCoreLib import Agent, GLOBAL_CACHE, ConsoleLog, Map, Player, Range, Routines, Utils
from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.enums_src.Map_enums import name_to_map_id
from Py4GWCoreLib.native_src.internals.types import Vec2f

# ── Module identity ───────────────────────────────────────────────────────────
MODULE_ICON = 'Textures/Module_Icons/Underworld.png'
BOT_NAME    = 'UnderworldBT'

# ── Persistent configuration ──────────────────────────────────────────────────
# Persistence goes through the shared IniManager: account-scoped config files under
# <projects>/Settings/<email>/..., replacing the hand-rolled IniHandler path. The
# adapter below keeps the old read/write surface but resolves the IniManager key
# lazily, so module import never fails when the account isn't ready yet (the key is
# empty until login; reads return defaults and writes are dropped until then).
_INI_PATH     = 'Widgets/Automation/Bots/Missions/Core'
_INI_FILENAME = 'UnderworldBT.ini'


class _IniAdapter:
    def __init__(self, path: str, filename: str) -> None:
        self._path = path
        self._filename = filename
        self._key = ''

    def key(self) -> str:
        if not self._key:
            self._key = IniManager().ensure_key(self._path, self._filename)
        return self._key

    def read_key(self, section: str, name: str, default: str = '') -> str:
        k = self.key()
        return IniManager().read_key(k, section, name, default) if k else default

    def read_int(self, section: str, name: str, default: int = 0) -> int:
        k = self.key()
        return IniManager().read_int(k, section, name, default) if k else default

    def read_float(self, section: str, name: str, default: float = 0.0) -> float:
        k = self.key()
        return IniManager().read_float(k, section, name, default) if k else default

    def read_bool(self, section: str, name: str, default: bool = False) -> bool:
        k = self.key()
        return IniManager().read_bool(k, section, name, default) if k else default

    def write_key(self, section: str, name: str, value) -> None:
        k = self.key()
        if k:
            IniManager().write_key(k, section, name, value)

    def delete_section(self, section: str) -> None:
        k = self.key()
        if k:
            IniManager().delete_section(k, section)


_ini = _IniAdapter(_INI_PATH, _INI_FILENAME)


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
    Repeat:   bool = False
    UseCons:  bool = True
    HardMode: bool = False

    @classmethod
    def load(cls) -> None:
        cls.Repeat   = bool(_ini.read_bool(BOT_NAME, 'quest_repeat',   False))
        cls.UseCons  = bool(_ini.read_bool(BOT_NAME, 'quest_use_cons', True))
        cls.HardMode = bool(_ini.read_bool(BOT_NAME, 'quest_hardmode', False))

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
    SpiritOfNaturesRenewal = "Spirit of Nature's Renewal"
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

# Every enemy name the bot itself ever blacklists. Used to clear ONLY the bot's own
# entries instead of wiping the whole list, so manually-added blacklist entries (from
# the HeroAI blacklist UI) survive bot startup, step purges, and wipe recovery.
UW_BOT_BLACKLIST_NAMES: tuple[str, ...] = (
    UWBlacklistName.ChainedSoul,
    UWBlacklistName.TorturedSpirit,
    UWBlacklistName.ObsidianGuardian,
    UWBlacklistName.VengefulAatxe,
    UWBlacklistName.BanishedDreamRider,
    UWBlacklistName.ObsidianBehemoth,
    UWBlacklistName.SpiritOfNaturesRenewal,
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

# Underworld enemy encoded names (GW string-table form). Encoded names are
# language-independent AND stable across game updates (model/player numbers can in
# theory shift), so targeting/priority is keyed on these. Matched at runtime against
# Agent.GetEncNameStrByID(agent_id, literal=False). Sourced from the Enemy Tracker
# data for The Underworld (map 72).
#
# NOTE: Skeleton of Dhuum and Dhuum Servant are intentionally absent. They have no
# stable base encoded name — every spawn gets a unique per-instance name
# (\x8102\x5C.. / \x8102\x5D..), so they cannot be matched reliably by encoded name
# and are therefore dropped from priority. Terrorweb Dryder keeps its base name, but
# instances using a per-spawn name are likewise not matched.
class UWEncName(str, enum.Enum):
    KEEPER_OF_SOULS           = r'\\x12AD\\xF69B\\xBD35\\x7A5E'
    TERRORWEB_QUEEN           = r'\\x17DF\\xAC9D\\xE33B\\x63DE'
    WAILING_LORD              = r'\\x12AF\\x8B85\\x9E38\\x7FED'
    TERRORWEB_DRYDER          = r'\\x12AC\\x9F81\\xBFE4\\x3216'
    MINDBLADE_SPECTRE         = r'\\x12BB\\xA3DC\\x0BDD'
    BANISHED_DREAM_RIDER      = r'\\x12B0\\xA053\\x8415\\x6F58'
    DEAD_COLLECTOR            = r'\\x12BC\\x98DC\\xFDF0\\x1FD0'
    DEAD_THRESHER             = r'\\x12BD\\xB160\\xA954\\x4D4C'
    GRASPING_DARKNESS         = r'\\x12C5\\xD142\\xFA22\\x1E49'
    CHARGED_BLACKNESS         = r'\\x12C4\\xA887\\x7302'
    COLDFIRE_NIGHT            = r'\\x12BE\\xB04F\\xE727\\x218F'
    STALKING_NIGHT            = r'\\x12C0\\xCE4F\\xC177\\x75FE'
    DYING_NIGHTMARE           = r'\\x12BF\\xF224\\xEA77\\x4E7D'
    BLADED_AATXE              = r'\\x12C2\\x968C\\xB2A0\\x1035'
    SMITE_CRAWLER             = r'\\x12BA\\xD696\\x4774'
    BONE_HORROR               = r'\\x1230\\x9354\\x94B4\\x654F'
    OBSIDIAN_GUARDIAN         = r'\\x12A8\\xE724\\xC399\\x1FB5'
    SLAYER                    = r'\\x17C1\\xF036\\x8EDD\\x575E'
    OBSIDIAN_BEHEMOTH         = r'\\x12A7\\xF511\\xCDD1\\x22D3'


# Underworld enemies ordered from highest to lowest party-call priority (UnderworldV2 + tracker).
# Omitted on purpose: Chained Soul, Tortured Spirit, Spirit of Nature's Renewal,
# Vengeful Aatxe (all bot-blacklisted — a party call would override the per-account
# blacklist filter and make every account attack them), Dire/Hearty Black Widow (trash).
# Also omitted: Skeleton of Dhuum and Dhuum Servant — no stable encoded name (see
# UWEncName note). The dedicated Dhuum handling drives that fight regardless.
UW_TARGET_PRIORITY: list[UWEncName] = [
    # Quest / high-value targets
    UWEncName.KEEPER_OF_SOULS,
    UWEncName.TERRORWEB_QUEEN,
    UWEncName.WAILING_LORD,
    UWEncName.TERRORWEB_DRYDER,
    UWEncName.MINDBLADE_SPECTRE,
    UWEncName.BANISHED_DREAM_RIDER,
    UWEncName.DEAD_COLLECTOR,
    UWEncName.DEAD_THRESHER,
    # Nightmare / Aatxe packs
    UWEncName.GRASPING_DARKNESS,
    UWEncName.CHARGED_BLACKNESS,
    UWEncName.COLDFIRE_NIGHT,
    UWEncName.STALKING_NIGHT,
    UWEncName.DYING_NIGHTMARE,
    UWEncName.BLADED_AATXE,
    # General UW mobs
    UWEncName.SMITE_CRAWLER,
    UWEncName.BONE_HORROR,
    UWEncName.OBSIDIAN_GUARDIAN,
    # Dhuum fight (low-priority fallback)
    UWEncName.SLAYER,
    # Behemoth last — usually blacklisted until BehemothGuard engages
    UWEncName.OBSIDIAN_BEHEMOTH,
]
_UW_PRIORITY_TARGET_RANGE = Range.Earshot.value + 100.0
_UW_PRIORITY_TARGET_COOLDOWN_MS = 2000.0
_UW_PRIORITY_TARGET_SCAN_INTERVAL_MS = 500.0

class EnterSettings:
    """Entry outpost used before activating the UW scroll."""
    EntryPoint: str = DEFAULT_UW_ENTRYPOINT_KEY

    @classmethod
    def load(cls) -> None:
        cls.EntryPoint = str(
            _ini.read_key(BOT_NAME, 'enter_entrypoint', DEFAULT_UW_ENTRYPOINT_KEY)
            or DEFAULT_UW_ENTRYPOINT_KEY
        )

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, 'enter_entrypoint', str(cls.EntryPoint))


# ── Inventory refill ──────────────────────────────────────────────────────────
class InventorySettings:
    """Between-run inventory management (Guild Hall UW scroll purchasing)."""
    BuyUWScrolls:  bool = False
    UWScrollMin:   int = 1
    UWScrollMax:   int = 2
    BuySalvageKits:   bool = True
    SalvageKitTarget: int = 4
    BuyIDKits:        bool = True
    IDKitTarget:      int = 2

    @classmethod
    def load(cls) -> None:
        cls.BuyUWScrolls = bool(_ini.read_bool(BOT_NAME, 'inv_buy_uw_scrolls', False))
        cls.UWScrollMin  = max(0, int(_ini.read_int(BOT_NAME, 'inv_uw_scroll_min', 1) or 1))
        cls.UWScrollMax  = max(
            cls.UWScrollMin,
            max(0, int(_ini.read_int(BOT_NAME, 'inv_uw_scroll_max', 2) or 2)),
        )
        cls.BuySalvageKits   = bool(_ini.read_bool(BOT_NAME, 'inv_buy_salvage_kits', True))
        cls.SalvageKitTarget = max(0, int(_ini.read_int(BOT_NAME, 'inv_salvage_kit_target', 4) or 4))
        cls.BuyIDKits        = bool(_ini.read_bool(BOT_NAME, 'inv_buy_id_kits', True))
        cls.IDKitTarget      = max(0, int(_ini.read_int(BOT_NAME, 'inv_id_kit_target', 2) or 2))

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, 'inv_buy_uw_scrolls', str(cls.BuyUWScrolls))
        _ini.write_key(BOT_NAME, 'inv_uw_scroll_min',  str(max(0, int(cls.UWScrollMin))))
        _ini.write_key(BOT_NAME, 'inv_uw_scroll_max',  str(max(0, int(cls.UWScrollMax))))
        _ini.write_key(BOT_NAME, 'inv_buy_salvage_kits',   str(cls.BuySalvageKits))
        _ini.write_key(BOT_NAME, 'inv_salvage_kit_target', str(max(0, int(cls.SalvageKitTarget))))
        _ini.write_key(BOT_NAME, 'inv_buy_id_kits',   str(cls.BuyIDKits))
        _ini.write_key(BOT_NAME, 'inv_id_kit_target', str(max(0, int(cls.IDKitTarget))))


# ── Consumables ───────────────────────────────────────────────────────────────
# Upkeep is toggled per category. Each category maps to a core-library consumable
# mode (see botting_consumables.consumable_specs), so the actual item set stays in
# sync with the library — "all pcons that exist", not a hand-maintained subset.
#   Cons  → conset trio (Armor of Salvation, Essence of Celerity, Grail of Might)
#   Pcons → every pcon the library knows (war supplies, food, and sweets)
_CONS_CATEGORY_MODES: dict[str, str] = {
    'Cons':  'conset',
    'Pcons': 'pcons',
}
_CONS_CATEGORIES: list[str] = list(_CONS_CATEGORY_MODES.keys())

class ConsSettings:
    """Per-category upkeep toggles and multibox Xunlai-restock quantities."""
    _active:  dict[str, bool] = {cat: True for cat in _CONS_CATEGORIES}
    # Multibox Xunlai restock (broadcast after the Guild Hall merchant). Uses the
    # shared RestockAllPcons / RestockConset commands with a single quantity each.
    RestockPcons:     bool = False
    PconRestockQty:   int  = 20
    ConsetRestockQty: int  = 10

    @classmethod
    def load(cls) -> None:
        cls._active = {
            cat: bool(_ini.read_bool(BOT_NAME, f'cons_cat_{cat.lower()}_active', True))
            for cat in _CONS_CATEGORIES
        }
        cls.RestockPcons     = bool(_ini.read_bool(BOT_NAME, 'cons_restock_pcons', False))
        cls.PconRestockQty   = max(0, int(_ini.read_int(BOT_NAME, 'cons_pcon_restock_qty', 20) or 20))
        cls.ConsetRestockQty = max(0, int(_ini.read_int(BOT_NAME, 'cons_conset_restock_qty', 10) or 10))

    @classmethod
    def is_category_active(cls, category: str) -> bool:
        return cls._active.get(category, True)

    @classmethod
    def set_category_active(cls, category: str, value: bool) -> None:
        cls._active[category] = value
        cls._save()

    @classmethod
    def _save(cls) -> None:
        for cat in _CONS_CATEGORIES:
            _ini.write_key(BOT_NAME, f'cons_cat_{cat.lower()}_active', str(cls._active.get(cat, True)))
        _ini.write_key(BOT_NAME, 'cons_restock_pcons',     str(cls.RestockPcons))
        _ini.write_key(BOT_NAME, 'cons_pcon_restock_qty',  str(max(0, int(cls.PconRestockQty))))
        _ini.write_key(BOT_NAME, 'cons_conset_restock_qty', str(max(0, int(cls.ConsetRestockQty))))


# ── Dhuum fight ───────────────────────────────────────────────────────────────
_KING_FROZENWIND_MODEL_ID = 2403
_KING_FROZENWIND_DEST_X      = -11278.0   # where the King stops walking
_KING_FROZENWIND_DEST_Y      =  17297.0
_KING_FROZENWIND_DEST_RADIUS = 1500.0     # how close he must be to count as "arrived"
_KING_FROZENWIND_FOLLOW_RADIUS = 1000.0   # max distance before we move to keep up
_KING_FROZENWIND_TIMEOUT_S   = 600.0      # 10-min hard timeout

class DhuumSettings:
    """Sacrifice account assignments for the Dhuum fight."""
    SacrificeEmails:       set[str] = set()
    MinSpiritformAccounts: int      = 2

    @classmethod
    def load(cls) -> None:
        cls.SacrificeEmails       = _read_emails_set('dhuum_sacrifice_emails')
        cls.MinSpiritformAccounts = int(_ini.read_int(BOT_NAME, 'dhuum_min_spiritform', 2))

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
    LeftTeamEmails:  list[str] = []
    RightTeamEmails: list[str] = []

    @classmethod
    def load(cls) -> None:
        cls.LeftTeamEmails  = _read_emails_list('imprisoned_left_emails')
        cls.RightTeamEmails = _read_emails_list('imprisoned_right_emails')

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


# Deferred load: settings classes hold safe defaults at import time and only pull
# persisted values once the IniManager key resolves (i.e. the account is ready).
# main() calls this once the key is available.
_settings_loaded = False


def _load_all_settings() -> None:
    BotSettings.load()
    EnterSettings.load()
    InventorySettings.load()
    ConsSettings.load()
    DhuumSettings.load()
    ImprisonedSpiritsSettings.load()
    _load_quest_times_log()
    _load_wipe_counts()


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

# Steps during which the dead-member rescue is allowed (Clear the Chamber through
# Servants of Grenth, inclusive). Disabled everywhere else (entry, Dhuum, loot)
# where backtracking to a corpse would do more harm than good.
_DEAD_RESCUE_STEPS: frozenset[str] = frozenset(
    _QUEST_ORDER[_QUEST_ORDER.index('Clear the Chamber'):_QUEST_ORDER.index('Servants of Grenth') + 1]
)


_quest_completion_times: dict[str, int] = {}
_SPIRIT_FORM_SKILL_ID = 3134

# ── Statistics (persisted via IniManager in dedicated sections) ───────────────
# quest_times: per-quest history of completed run times (seconds), serialized as a
# ';'-joined list per quest under [QuestTimes]. wipe_counts: per-quest wipe tally
# under [WipeCounts]. Both share the UnderworldBT.ini with the settings but in
# their own sections, and load lazily once the account-scoped ini key resolves.
_STATS_QUEST_TIMES_SECTION = 'QuestTimes'
_STATS_WIPE_COUNTS_SECTION = 'WipeCounts'

_quest_times_log: dict[str, list[int]] = {}
_wipe_counts_log: dict[str, int] = {}


def _load_quest_times_log() -> None:
    global _quest_times_log
    result: dict[str, list[int]] = {}
    for quest in _QUEST_ORDER:
        raw = _ini.read_key(_STATS_QUEST_TIMES_SECTION, quest, '')
        if not raw:
            continue
        times = [int(v) for v in raw.split(';') if v.strip().lstrip('-').isdigit()]
        if times:
            result[quest] = times
    _quest_times_log = result


def _load_wipe_counts() -> None:
    global _wipe_counts_log
    result: dict[str, int] = {}
    for quest in _QUEST_ORDER:
        count = _ini.read_int(_STATS_WIPE_COUNTS_SECTION, quest, 0)
        if count > 0:
            result[quest] = count
    _wipe_counts_log = result


def _save_wipe_counts() -> None:
    for quest, count in _wipe_counts_log.items():
        _ini.write_key(_STATS_WIPE_COUNTS_SECTION, quest, str(int(count)))

# ── Step timer ────────────────────────────────────────────────────────────────
# Timer starts when 'Clear the Chamber' begins.  Each step's recorded value is
# the cumulative elapsed seconds from that moment until the step completed.
# 'Enter Underworld' is intentionally excluded from timing.
_RUN_START_QUEST  = 'Clear the Chamber'
_TIMED_QUESTS: frozenset[str] = frozenset(_QUEST_ORDER[1:])  # all except 'Enter Underworld'
_timing_state: dict = {
    'run_start_ms':     None,  # instance-timer ms when Clear the Chamber started
    'last_step':        '',    # previous current_step_name value
    'last_instance_ms': 0,     # last instance-timer reading taken inside the UW explorable
}


def _save_quest_times_log() -> None:
    for quest, times in _quest_times_log.items():
        _ini.write_key(_STATS_QUEST_TIMES_SECTION, quest, ';'.join(str(int(t)) for t in times))


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
# ║  UI · DRAW FUNCTIONS  (settings tabs, main-window widgets)
# ╚══════════════════════════════════════════════════════════════════════════════

def _draw_help() -> None:
    _c_title = Utils.RGBToNormal(120, 200, 255, 255)
    _c_head  = Utils.RGBToNormal(255, 215, 100, 255)
    _c_warn  = Utils.RGBToNormal(255, 120, 120, 255)
    _c_grey  = Utils.RGBToNormal(170, 170, 170, 255)

    # ── Overview ──────────────────────────────────────────────────────────────
    PyImGui.text_colored('Underworld Multibox Bot', _c_title)
    PyImGui.text_wrapped(
        'Runs the full Underworld clear with a multibox party. Start the script on the '
        'party leader only — every other account is driven through shared memory + HeroAI. '
        'Configure the per-quest settings in the tabs above before starting a run.'
    )
    PyImGui.spacing()
    PyImGui.text_colored('Quick start', _c_head)
    PyImGui.bullet_text('Run the leader; followers join automatically.')
    PyImGui.bullet_text('Use a RANGED leader. It works best (smoother pathing, fewer snags).')
    PyImGui.bullet_text("Set the teams in 'Imprisoned Spirits' and the sacrifices in 'Dhuum'.")
    PyImGui.bullet_text("Toggle Cons / Hard Mode / Repeat on the Run tab.")

    PyImGui.separator()

    # ── Imprisoned Spirits tab ────────────────────────────────────────────────
    PyImGui.text_colored('Imprisoned Spirits tab', _c_head)
    PyImGui.text_wrapped(
        'This quest needs the party split in two so spirits spawning on both sides are '
        'intercepted. Each account is assigned to a Left or Right team here.'
    )
    PyImGui.bullet_text('Left / Right radio buttons: pick the team for each follower account.')
    PyImGui.bullet_text('During the quest, Left accounts are flagged to the left staging spot,')
    PyImGui.text_wrapped('   Right accounts to the right one, they hold those lanes automatically.')
    PyImGui.bullet_text('Your own (leader) row is greyed out, it runs the bot and is not flagged.')
    PyImGui.bullet_text('Default if never set: first 3 accounts go Left, the rest go Right.')
    PyImGui.text_colored(
        'You need to find out which builds hold it.', _c_grey,
    )

    PyImGui.separator()

    # ── Dhuum tab ─────────────────────────────────────────────────────────────
    PyImGui.text_colored('Dhuum tab', _c_head)
    PyImGui.text_wrapped(
        'In the Dhuum fight some accounts are deliberately killed so they take on '
        'I sacrifice all but ST '
        'who is frontlane and how many spirits the bot waits for. (2-3 should be enough)'
    )
    PyImGui.bullet_text('Sacrifice checkboxes: which follower accounts get sent to the death')
    PyImGui.text_wrapped('   spot to die and become spirits. Everyone else is flagged as a survivor.')
    PyImGui.bullet_text('Your own (leader) row is disabled — the leader is never sacrificed.')
    PyImGui.bullet_text('Min Spiritform accounts: the bot holds combat until at least this many')
    PyImGui.text_wrapped('   party members in UW actually have Spirit Form, then resumes the fight.')

    PyImGui.separator()

    # ── Known issues ──────────────────────────────────────────────────────────
    PyImGui.text_colored('Status & known issues', _c_head)
    PyImGui.bullet_text("Medium risk of getting stuck on 'Unwanted Guests' and Dhuum timing edge cases.")
    PyImGui.bullet_text("Low risk of leaving dead mates behind.")
    PyImGui.text_colored('Hard Mode has never been fully cleared. Maybe you can?', _c_warn)
    PyImGui.separator()


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
    _scroll_input_w = 56.0

    def _draw_scroll_min_max_row(
        min_input_id: str,
        max_input_id: str,
        current_min: int,
        current_max: int,
        model_id: int,
    ) -> tuple[int, int]:
        PyImGui.text('Min')
        PyImGui.same_line(0, 4)
        PyImGui.push_item_width(_scroll_input_w)
        new_min = max(0, _input_int_val(PyImGui.input_int(min_input_id, current_min, 0, 0, 0), current_min))
        PyImGui.pop_item_width()
        PyImGui.same_line(0, 12)
        PyImGui.text('Max')
        PyImGui.same_line(0, 4)
        PyImGui.push_item_width(_scroll_input_w)
        new_max = max(0, _input_int_val(PyImGui.input_int(max_input_id, current_max, 0, 0, 0), current_max))
        PyImGui.pop_item_width()

        current_count = int(GLOBAL_CACHE.Inventory.GetModelCount(int(model_id)) or 0)
        PyImGui.same_line(0, 12)
        now_label = f'Now: {current_count}'
        if current_count < new_min:
            PyImGui.text_colored(now_label, Utils.RGBToNormal(255, 80, 80, 255))
        elif current_count >= new_max:
            PyImGui.text_colored(now_label, Utils.RGBToNormal(100, 255, 100, 255))
        else:
            PyImGui.text_colored(now_label, Utils.RGBToNormal(200, 200, 200, 255))

        if new_max < new_min:
            new_max = new_min
        return new_min, new_max

    new_val = PyImGui.checkbox('Buy UW scrolls at Scroll Trader (Guild Hall)', InventorySettings.BuyUWScrolls)
    if new_val != InventorySettings.BuyUWScrolls:
        InventorySettings.BuyUWScrolls = new_val
        changed = True
    PyImGui.begin_disabled(not InventorySettings.BuyUWScrolls)
    new_min, new_max = _draw_scroll_min_max_row(
        '##uw_scroll_min',
        '##uw_scroll_max',
        InventorySettings.UWScrollMin,
        InventorySettings.UWScrollMax,
        UW_SCROLL_MODEL_ID,
    )
    if new_min != InventorySettings.UWScrollMin:
        InventorySettings.UWScrollMin = new_min
        changed = True
    if new_max != InventorySettings.UWScrollMax:
        InventorySettings.UWScrollMax = new_max
        changed = True
    PyImGui.end_disabled()

    PyImGui.separator()
    new_buy_kits = PyImGui.checkbox('Buy Salvage Kits at Merchant (Guild Hall)', InventorySettings.BuySalvageKits)
    if new_buy_kits != InventorySettings.BuySalvageKits:
        InventorySettings.BuySalvageKits = new_buy_kits
        changed = True
    PyImGui.begin_disabled(not InventorySettings.BuySalvageKits)
    PyImGui.text('Target per account')
    PyImGui.same_line(0, 4)
    PyImGui.push_item_width(_scroll_input_w)
    new_kit_target = max(0, _input_int_val(
        PyImGui.input_int('##uw_salvage_kit_target', InventorySettings.SalvageKitTarget, 0, 0, 0),
        InventorySettings.SalvageKitTarget,
    ))
    PyImGui.pop_item_width()
    if new_kit_target != InventorySettings.SalvageKitTarget:
        InventorySettings.SalvageKitTarget = new_kit_target
        changed = True
    PyImGui.end_disabled()

    new_buy_id = PyImGui.checkbox('Buy Superior ID Kits at Merchant (Guild Hall)', InventorySettings.BuyIDKits)
    if new_buy_id != InventorySettings.BuyIDKits:
        InventorySettings.BuyIDKits = new_buy_id
        changed = True
    PyImGui.begin_disabled(not InventorySettings.BuyIDKits)
    PyImGui.text('Target per account')
    PyImGui.same_line(0, 4)
    PyImGui.push_item_width(_scroll_input_w)
    new_id_target = max(0, _input_int_val(
        PyImGui.input_int('##uw_id_kit_target', InventorySettings.IDKitTarget, 0, 0, 0),
        InventorySettings.IDKitTarget,
    ))
    PyImGui.pop_item_width()
    if new_id_target != InventorySettings.IDKitTarget:
        InventorySettings.IDKitTarget = new_id_target
        changed = True
    PyImGui.end_disabled()

    if changed:
        InventorySettings.save()


def _draw_cons_settings() -> None:

    new_restock = PyImGui.checkbox(
        'Restock pcons/conset from Xunlai (all accounts)', ConsSettings.RestockPcons
    )
    _cons_changed = new_restock != ConsSettings.RestockPcons
    if _cons_changed:
        ConsSettings.RestockPcons = new_restock

    PyImGui.begin_disabled(not ConsSettings.RestockPcons)
    PyImGui.push_item_width(70.0)
    new_pcon_qty = max(0, _input_int_val(
        PyImGui.input_int('Pcon qty##cons_pcon_qty', ConsSettings.PconRestockQty, 0, 0, 0),
        ConsSettings.PconRestockQty,
    ))
    PyImGui.same_line(0, 16)
    new_conset_qty = max(0, _input_int_val(
        PyImGui.input_int('Conset qty##cons_conset_qty', ConsSettings.ConsetRestockQty, 0, 0, 0),
        ConsSettings.ConsetRestockQty,
    ))
    PyImGui.pop_item_width()
    PyImGui.end_disabled()
    if new_pcon_qty != ConsSettings.PconRestockQty:
        ConsSettings.PconRestockQty = new_pcon_qty
        _cons_changed = True
    if new_conset_qty != ConsSettings.ConsetRestockQty:
        ConsSettings.ConsetRestockQty = new_conset_qty
        _cons_changed = True
    if _cons_changed:
        ConsSettings._save()
    PyImGui.separator()
    PyImGui.spacing()

    PyImGui.text('Upkeep categories')
    PyImGui.separator()
    for cat in _CONS_CATEGORIES:
        cur_active = ConsSettings.is_category_active(cat)
        new_active = PyImGui.checkbox(f'{cat}##cons_cat_{cat}', cur_active)
        if new_active != cur_active:
            ConsSettings.set_category_active(cat, new_active)


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


def _reset_stats() -> None:
    # Reset every statistic shown in the Quest Progress table: this-run times
    # (Time), the per-quest history feeding Avg5/AvgAll, and the wipe counts
    # feeding SR% (cleared together so SR% returns to '--' instead of a misleading
    # 0%). Also reset the live run timer state so 'Enter Underworld' goes back to
    # pending, and drop the persisted stat sections from the ini.
    _quest_completion_times.clear()
    _quest_times_log.clear()
    _wipe_counts_log.clear()
    _timing_state['run_start_ms'] = None
    _timing_state['last_step'] = ''
    _ini.delete_section(_STATS_QUEST_TIMES_SECTION)
    _ini.delete_section(_STATS_WIPE_COUNTS_SECTION)


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
    PyImGui.same_line(0, -1)
    if PyImGui.button('Reset Times##uw_stats'):
        _reset_stats()
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
# ║  BOT INSTANCE + MAIN-WINDOW SETUP  (create bot, wire UI overrides)
# ╚══════════════════════════════════════════════════════════════════════════════

bot = BottingTree.Create(bot_name=BOT_NAME, multi_account=True, auto_loot=True, isolation_enabled=False)
# Reset the EnemyBlacklist on startup: drop only the bot's OWN leftover name entries
# from a previous crashed or incomplete run. Manually-added entries (model IDs and any
# user names from the HeroAI blacklist UI) are preserved.
try:
    from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist as _EBL_Init

    _bl_init = _EBL_Init()
    _bot_bl_names = {n.strip().lower() for n in UW_BOT_BLACKLIST_NAMES}
    _bl_init._write_names({n for n in _bl_init.get_all_names() if n not in _bot_bl_names})
except Exception:
    pass
bot.UI.override_draw_help(lambda: _draw_help())
bot.UI.override_draw_config(lambda: _draw_settings())

# Declutter the Main tab: suppress the verbose status boolean block
# (Started/Paused/Headless HeroAI/Looting/... ). The framework renders that
# block exclusively through ``_colored_bool``, so neutralizing it on this bot's
# UI instance hides those rows without touching the shared framework or any
# other bot. The header (Current step / HeroAI / Planner) and the control
# buttons above it remain untouched.
bot.UI._colored_bool = lambda label, value: None  # type: ignore[method-assign]

# Hide the built-in "Navigation" tab from the Main window. The framework
# hard-codes that tab inside ``_draw_managed_window`` with no per-bot toggle, so
# we wrap the draw call and make ``begin_tab_item`` report the Navigation tab as
# collapsed (returns False) only while this bot renders its window. Every other
# tab/label passes through unchanged, and the original ``begin_tab_item`` is
# restored immediately, so no other widget or bot is affected.
_bt_orig_draw_managed_window = bot.UI._draw_managed_window


def _draw_managed_window_without_navigation() -> None:
    _real_begin_tab_item = PyImGui.begin_tab_item

    def _filtered_begin_tab_item(label, *args, **kwargs):
        if label == 'Navigation':
            return False
        return _real_begin_tab_item(label, *args, **kwargs)

    PyImGui.begin_tab_item = _filtered_begin_tab_item
    try:
        _bt_orig_draw_managed_window()
    finally:
        PyImGui.begin_tab_item = _real_begin_tab_item


bot.UI._draw_managed_window = _draw_managed_window_without_navigation  # type: ignore[method-assign]

# ── BehaviorTree import ──────────────────────────────────────────────────────
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree as _BT


# ╔══════════════════════════════════════════════════════════════════════════════
# ║  BEHAVIOR TREE · SHARED HELPERS & ACTIONS
# ║  (reusable BT nodes: blacklist, flags, combat toggles, waits, targeting —
# ║   building blocks consumed by the quest trees further below)
# ╚══════════════════════════════════════════════════════════════════════════════

_BEHEMOTH_ENGAGE_RADIUS = 500.0

# Toggled by _behemoth_guard_start / _stop nodes; read every tick by the service.
_behemoth_guard_active: bool = False
_soulkeeper_call_active: bool = False


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


def _kill_route_until_quest_completed(
    waypoints: list[tuple[Vec2f, float]],
    quest_id: int,
    label: str = '',
    max_passes: int = 3,
    confirm_wait_ms: int = 2_000,
) -> _BT:
    """Walk a MoveAndKill route, then verify quest_id is completed.

    If the quest is not completed (e.g. enemies were missed on the way),
    the whole route is walked again, up to max_passes additional times.
    Already-cleared waypoints simply pass through, so only missed enemies
    get engaged on later passes.

    Always returns SUCCESS so the planner can continue to the turn-in dialog
    even if the quest never registers as completed.
    """
    BT = Routines.BT
    _tag         = label or f'Quest{quest_id}'
    _pass_count  = [0]

    def _quest_completed() -> bool:
        from Py4GWCoreLib import Quest as _Quest
        try:
            return bool(_Quest.IsQuestCompleted(quest_id))
        except Exception:
            return False

    def _walk_route(attempt_label: str) -> _BT:
        return BT.Composite.Sequence(
            *[BT.Movement.MoveAndKill(pos, clear_area_radius=radius) for pos, radius in waypoints],
            name=attempt_label,
        )

    def _check_or_repeat(node: _BT.Node) -> _BT:
        if _quest_completed():
            ConsoleLog(
                BOT_NAME,
                f'[{_tag}] Quest {quest_id} completed.',
                Py4GW.Console.MessageType.Info,
            )
            return _BT(_BT.ActionNode(name=f'{_tag}QuestDone', action_fn=lambda n: _BT.NodeState.SUCCESS))

        if _pass_count[0] >= max_passes:
            ConsoleLog(
                BOT_NAME,
                f'[{_tag}] Quest {quest_id} not completed after {max_passes} extra passes — continuing.',
                Py4GW.Console.MessageType.Warning,
            )
            return _BT(_BT.ActionNode(name=f'{_tag}QuestGiveUp', action_fn=lambda n: _BT.NodeState.SUCCESS))

        _pass_count[0] += 1
        ConsoleLog(
            BOT_NAME,
            f'[{_tag}] Quest {quest_id} not completed — re-walking route, pass {_pass_count[0]}/{max_passes}.',
            Py4GW.Console.MessageType.Warning,
        )
        return BT.Composite.Sequence(
            _walk_route(f'{_tag}RepeatPass{_pass_count[0]}'),
            BT.Player.Wait(duration_ms=confirm_wait_ms),
            _BT(_BT.SubtreeNode(name=f'{_tag}RepeatCheck{_pass_count[0]}', subtree_fn=_check_or_repeat)),
            name=f'{_tag}RepeatSeq{_pass_count[0]}',
        )

    return BT.Composite.Sequence(
        _walk_route(f'{_tag}FirstPass'),
        BT.Player.Wait(duration_ms=confirm_wait_ms),
        _BT(_BT.SubtreeNode(name=f'{_tag}QuestCheck', subtree_fn=_check_or_repeat)),
        name=f'{_tag}KillRouteUntilQuestCompleted',
    )


def _blacklist_add_dream_rider() -> None:
    _blacklist_name(UWBlacklistName.BanishedDreamRider)
def _clear_follower_flags() -> _BT:
    """No Routines.BT equivalent — HeroAI multibox follower flags (not BT.Party.FlagHero)."""

    def _tick(node: _BT.Node) -> _BT.NodeState:
        for account, _ in GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False):
            if int(account.AgentPartyData.PartyPosition) == 0:
                continue
            email = str(account.AccountEmail or '').strip().lower()
            if not email:
                continue
            GLOBAL_CACHE.ShMem.SetHeroAIPropertyByEmail(email, 'IsFlagged',       False)
            GLOBAL_CACHE.ShMem.SetHeroAIPropertyByEmail(email, 'FlagPos',         Vec2f(0.0, 0.0))
            GLOBAL_CACHE.ShMem.SetHeroAIPropertyByEmail(email, 'FlagFacingAngle', 0.0)
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

        for account, _ in GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False):
            email = str(account.AccountEmail or '').strip().lower()
            if not email:
                continue

            # Always clear first
            GLOBAL_CACHE.ShMem.SetHeroAIPropertyByEmail(email, 'IsFlagged',       False)
            GLOBAL_CACHE.ShMem.SetHeroAIPropertyByEmail(email, 'FlagPos',         Vec2f(0.0, 0.0))
            GLOBAL_CACHE.ShMem.SetHeroAIPropertyByEmail(email, 'FlagFacingAngle', 0.0)

            if email == my_email:
                continue  # leader runs the bot — never flagged

            if email in sacrifice_emails:
                GLOBAL_CACHE.ShMem.SetHeroAIPropertyByEmail(email, 'IsFlagged', True)
                GLOBAL_CACHE.ShMem.SetHeroAIPropertyByEmail(email, 'FlagPos',   Vec2f(_DHUUM_SAC_FLAG_X,  _DHUUM_SAC_FLAG_Y))
                sac_flagged.append(email)
            else:
                GLOBAL_CACHE.ShMem.SetHeroAIPropertyByEmail(email, 'IsFlagged', True)
                GLOBAL_CACHE.ShMem.SetHeroAIPropertyByEmail(email, 'FlagPos',   Vec2f(_DHUUM_SURV_FLAG_X, _DHUUM_SURV_FLAG_Y))
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
        updated = 0
        for account, _ in GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False):
            email = str(getattr(account, 'AccountEmail', '') or '').strip().lower()
            if not email:
                continue
            GLOBAL_CACHE.ShMem.SetHeroAIPropertyByEmail(email, 'Combat', False)
            updated += 1
        ConsoleLog(BOT_NAME, f'[Dhuum] HeroAI combat disabled for {updated} account(s).', Py4GW.Console.MessageType.Info)
        return _BT.NodeState.SUCCESS

    return _BT(_BT.ActionNode(name='DisableHeroAICombatAll', action_fn=_tick))
def _enable_heroai_combat_all() -> _BT:
    """Set Combat = True on every active HeroAI account (all party slots).

    No Routines.BT equivalent — HeroAI Combat toggle via SharedMemory options.
    """
    def _tick(node: _BT.Node) -> _BT.NodeState:
        updated = 0
        for account, _ in GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False):
            email = str(getattr(account, 'AccountEmail', '') or '').strip().lower()
            if not email:
                continue
            GLOBAL_CACHE.ShMem.SetHeroAIPropertyByEmail(email, 'Combat', True)
            updated += 1
        ConsoleLog(BOT_NAME, f'[Dhuum] HeroAI combat enabled for {updated} account(s).', Py4GW.Console.MessageType.Info)
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
                if any(b.SkillId == _SPIRIT_FORM_SKILL_ID for b in acct.AgentData.Buffs.Buffs if b.SkillId != 0):
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
def _purge_bot_blacklist_names() -> None:
    """Remove only the bot's own name entries, preserving manually-added blacklist entries."""
    _update_blacklist_names(remove=UW_BOT_BLACKLIST_NAMES)


def _purge_blacklist_names_action(_node: _BT.Node) -> _BT.NodeState:
    _purge_bot_blacklist_names()
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
    _purge_bot_blacklist_names()
def _party_call_or_change_target(agent_id: int) -> None:
    """Match HeroAI UI: party leader uses Call Target (Ctrl+Space); others only change local target.

    No Routines.BT equivalent — HeroAI CallTarget + Player.ChangeTarget.
    """
    from Py4GWCoreLib.Agent import Agent as _Agent
    from Py4GWCoreLib.enums_src.GameData_enums import Allegiance as _Allegiance

    if not agent_id or not _Agent.IsValid(agent_id):
        return

    def _is_enemy_living_target(target_id: int) -> bool:
        """Allow party-call only for valid, living enemy agents."""
        try:
            if not _Agent.IsValid(target_id):
                return False
            if not _Agent.IsLiving(target_id):
                return False
            if not _Agent.IsAlive(target_id):
                return False
            allegiance_value, _ = _Agent.GetAllegiance(target_id)
            return int(allegiance_value) == int(_Allegiance.Enemy)
        except Exception:
            return False

    if not _is_enemy_living_target(int(agent_id)):
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
        # Leader: only ever issue Call Target. Do NOT fall through to
        # ChangeTarget when CallTarget rejects the agent (invalid/dead/
        # despawned) — calling ChangeTarget on an agent that no longer exists
        # crashes the client (AvSelect.cpp assertion) during fast despawns such
        # as the Dhuum fight (dying Minions/Champions of Dhuum).
        CallTarget(int(agent_id), interact=False)
        return
    # Non-leader (or CallTarget unavailable): re-validate immediately before
    # ChangeTarget to minimize the despawn race that triggers the assertion.
    if _Agent.IsValid(agent_id):
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


_REQUIRED_WIDGETS: tuple[str, ...] = ('Dhuum Helper',)


def _enable_required_widgets_on_all_accounts(node: object) -> object:
    """Enable the required widgets (Dhuum Helper) locally and on every other account.

    HeroAI is intentionally not auto-enabled here — it must already be running on
    every account for the bot to control the followers.

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


# ╔══════════════════════════════════════════════════════════════════════════════
# ║  QUEST FLOW · STEP TREES (chronological)
# ║  (one tree per planner step, in run order; registered in BOT REGISTRATION
# ║   at the bottom of the file)
# ╚══════════════════════════════════════════════════════════════════════════════

# Missing ApoBT wrappers (no equivalent exists in ApoBottingLib yet):
#
#   1. ApoBT.SummonAllAccounts — using RoutinesBT.Multibox.SummonAllAccounts directly.
#   2. ApoBT.UseItemByModelID  — using a raw _BT.ActionNode + GLOBAL_CACHE.Inventory.UseItem.
#   3. ApoBT.EnableWidgets     — using a raw _BT.ActionNode + WidgetManager + ShMem.SendMessage.

# Guild Hall merchant restock (multibox). The Guild Hall "Merchant" NPC is model
# id 196; it is located at runtime via an NPC-array scan so no fixed coordinates
# are required.
_GH_MERCHANT_MODEL_ID = 196
# Robust merchant lookup (same strategy as the Merchant Rules widget): match the
# language-independent encoded name first, then the localized "[Merchant]" name,
# then fall back to the model id. Search within compass range of the leader.
_GH_MERCHANT_NAME_QUERY = '[Merchant]'
_GH_MERCHANT_SEARCH_MAX_DIST = float(Range.Compass.value)
# Default Salvage-Kit top-up target per account at the Guild Hall merchant. The
# live value is configurable via InventorySettings.SalvageKitTarget (Inventory tab);
# this constant only documents the original/default quantity.
_SALVAGE_KIT_RESTOCK_TARGET = 4
# Max time to wait for every account to arrive in the Guild Hall before starting
# the restock anyway (safety net so Enter Underworld never stalls).
_SALVAGE_RESTOCK_GATHER_TIMEOUT_MS = 20000
# Max time to wait for every account's merchant round-trip to finish.
_SALVAGE_RESTOCK_WAIT_TIMEOUT_MS = 120000


def _build_restock_salvage_kits_tree() -> _BT:
    """Multibox Salvage-Kit restock as a single pure-BT ActionNode.

    Once every multibox account has arrived in the Guild Hall, locate the Guild
    Hall Merchant (model 196) and broadcast a ``MerchantItems`` shared command to
    every account (leader included). Each account walks to the merchant and tops
    its Salvage Kits up to ``InventorySettings.SalvageKitTarget`` and its Superior
    Identification Kits up to ``InventorySettings.IDKitTarget`` via the standard
    Messaging handler (a kit is skipped when its toggle is off; the whole step is
    skipped when both are off). This node only sends the command and polls the outbound
    refs for completion — all movement/buying is performed by the shared-memory
    command infrastructure (same pattern as the LootChest step). Always returns
    SUCCESS so Enter Underworld never stalls.
    """
    from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType as _SCT
    from Py4GWCoreLib import AgentArray as _AA
    from Py4GWCoreLib.modular.selectors import resolve_agent_xy_from_step as _resolve_agent_xy_from_step

    salvage_target = max(0, int(InventorySettings.SalvageKitTarget)) if InventorySettings.BuySalvageKits else 0
    id_target      = max(0, int(InventorySettings.IDKitTarget))      if InventorySettings.BuyIDKits      else 0
    state: dict = {
        'phase':              'wait_gathered',  # wait_gathered → send → waiting → done
        'gather_deadline_ms': 0,
        'refs':               [],               # list of (email, message_index)
        'deadline_ms':        0,
    }

    def _all_accounts_in_guild_hall() -> bool:
        if not Map.IsGuildHall():
            return False
        gh_map_id = int(Map.GetMapID() or 0)
        if gh_map_id <= 0:
            return False
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData() or []
        if not accounts:
            return False
        return all(
            int(getattr(acc.AgentData.Map, 'MapID', 0) or 0) == gh_map_id
            for acc in accounts
        )

    def _find_merchant_xy() -> "tuple[float, float] | None":
        # Primary: resolve the merchant the same way the Merchant Rules widget does
        # — encoded-name match first (language-independent), then the localized
        # "[Merchant]" name, then the model id — scoped to NPCs within compass
        # range of the leader. This is far more reliable than a bare model scan.
        for idx, step in enumerate((
            {'npc': 'MERCHANT'},
            {'target': _GH_MERCHANT_NAME_QUERY},
            {'model_id': _GH_MERCHANT_MODEL_ID},
        )):
            try:
                coords = _resolve_agent_xy_from_step(
                    step,
                    recipe_name=BOT_NAME,
                    step_idx=idx,
                    agent_kind='npc',
                    default_max_dist=_GH_MERCHANT_SEARCH_MAX_DIST,
                    log_failures=False,
                )
            except Exception:
                coords = None
            if coords is not None:
                return float(coords[0]), float(coords[1])

        # Fallback: original model-id scan across the NPC / agent / neutral arrays
        # in case the merchant is missing from the NPC minipet array.
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
                    if int(Agent.GetModelID(aid)) == _GH_MERCHANT_MODEL_ID:
                        pos = Agent.GetXY(aid)
                        if pos:
                            return float(pos[0]), float(pos[1])
                except Exception:
                    continue
        return None

    def _tick(node: _BT.Node) -> _BT.NodeState:
        if not InventorySettings.BuySalvageKits and not InventorySettings.BuyIDKits:
            return _BT.NodeState.SUCCESS

        now = int(Utils.GetBaseTimestamp())
        my_email = str(Player.GetAccountEmail() or '')

        if state['phase'] == 'wait_gathered':
            if state['gather_deadline_ms'] == 0:
                state['gather_deadline_ms'] = now + _SALVAGE_RESTOCK_GATHER_TIMEOUT_MS
            if _all_accounts_in_guild_hall():
                state['phase'] = 'send'
                return _BT.NodeState.RUNNING
            if now >= state['gather_deadline_ms']:
                ConsoleLog(
                    BOT_NAME,
                    '[EnterUW] RestockSalvageKits: not all accounts reached the Guild Hall '
                    'before timeout — restocking available accounts anyway.',
                    Py4GW.Console.MessageType.Warning,
                )
                state['phase'] = 'send'
                return _BT.NodeState.RUNNING
            return _BT.NodeState.RUNNING

        if state['phase'] == 'send':
            merchant = _find_merchant_xy()
            if merchant is None:
                ConsoleLog(
                    BOT_NAME,
                    '[EnterUW] RestockSalvageKits: Guild Hall merchant (model 196) not found — '
                    'skipping kit restock.',
                    Py4GW.Console.MessageType.Warning,
                )
                ConsoleLog(BOT_NAME, 'Restock Kits: merchant not found, skipped.', Py4GW.Console.MessageType.Info)
                state['phase'] = 'done'
                return _BT.NodeState.SUCCESS

            mx, my = merchant
            refs: list[tuple[str, int]] = []
            for acc in GLOBAL_CACHE.ShMem.GetAllAccountData() or []:
                email = str(getattr(acc, 'AccountEmail', '') or '')
                if not email:
                    continue
                message_index = int(
                    GLOBAL_CACHE.ShMem.SendMessage(
                        my_email,
                        email,
                        _SCT.MerchantItems,
                        (float(mx), float(my), float(id_target), float(salvage_target)),
                    )
                )
                refs.append((email, message_index))

            state['refs']        = refs
            state['deadline_ms'] = now + _SALVAGE_RESTOCK_WAIT_TIMEOUT_MS
            state['phase']       = 'waiting'
            _kit_parts = []
            if id_target > 0:
                _kit_parts.append(f'{id_target} ID kit(s)')
            if salvage_target > 0:
                _kit_parts.append(f'{salvage_target} salvage kit(s)')
            _kit_desc = ' + '.join(_kit_parts) if _kit_parts else 'nothing'
            ConsoleLog(BOT_NAME, f'Restock Kits: topping up to {_kit_desc} on {len(refs)} account(s)…', Py4GW.Console.MessageType.Info)
            if not refs:
                state['phase'] = 'done'
                return _BT.NodeState.SUCCESS
            return _BT.NodeState.RUNNING

        if state['phase'] == 'waiting':
            still_pending: list[tuple[str, int]] = []
            for email, message_index in state['refs']:
                if int(message_index) < 0:
                    continue
                message = GLOBAL_CACHE.ShMem.GetInbox(int(message_index))
                is_same_message = (
                    bool(getattr(message, 'Active', False))
                    and str(getattr(message, 'ReceiverEmail', '') or '') == email
                    and str(getattr(message, 'SenderEmail', '') or '') == my_email
                    and int(getattr(message, 'Command', -1)) == int(_SCT.MerchantItems)
                )
                if is_same_message:
                    still_pending.append((email, message_index))
            state['refs'] = still_pending

            if not still_pending:
                ConsoleLog(BOT_NAME, 'Restock Kits: done.', Py4GW.Console.MessageType.Info)
                state['phase'] = 'done'
                return _BT.NodeState.SUCCESS
            if now >= state['deadline_ms']:
                ConsoleLog(
                    BOT_NAME,
                    f'[EnterUW] RestockSalvageKits: timeout after {_SALVAGE_RESTOCK_WAIT_TIMEOUT_MS} ms, '
                    f'{len(still_pending)} account(s) did not confirm.',
                    Py4GW.Console.MessageType.Warning,
                )
                ConsoleLog(BOT_NAME, 'Restock Kits: timed out waiting for some accounts.', Py4GW.Console.MessageType.Warning)
                state['phase'] = 'done'
                return _BT.NodeState.SUCCESS
            return _BT.NodeState.RUNNING

        return _BT.NodeState.SUCCESS

    return _BT(_BT.ActionNode(name='RestockSalvageKits', action_fn=_tick))


_PCON_RESTOCK_WAIT_TIMEOUT_MS = 60000


def _build_restock_pcons_tree() -> _BT:
    """Multibox pcon/conset restock from each account's Xunlai storage.

    Runs right after the Guild Hall merchant step. When ``ConsSettings.RestockPcons``
    is on, broadcasts ``RestockAllPcons`` and ``RestockConset`` to every account
    (leader included). Each account withdraws from its own Xunlai up to the configured
    quantities (``PconRestockQty`` / ``ConsetRestockQty``) — no movement is required,
    so this is fast. This node only sends the commands and polls the outbound refs for
    completion; the actual withdrawing is handled by the shared-memory command
    infrastructure. Always returns SUCCESS so Enter Underworld never stalls, and is a
    no-op when the toggle is off or both quantities are 0.
    """
    from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType as _SCT

    state: dict = {
        'phase':       'send',   # send → waiting → done
        'refs':        [],       # list of (email, message_index, command)
        'deadline_ms': 0,
    }

    def _tick(node: _BT.Node) -> _BT.NodeState:
        if not ConsSettings.RestockPcons:
            return _BT.NodeState.SUCCESS

        now = int(Utils.GetBaseTimestamp())
        my_email = str(Player.GetAccountEmail() or '')

        if state['phase'] == 'send':
            pcon_qty   = max(0, int(ConsSettings.PconRestockQty))
            conset_qty = max(0, int(ConsSettings.ConsetRestockQty))
            if pcon_qty <= 0 and conset_qty <= 0:
                state['phase'] = 'done'
                return _BT.NodeState.SUCCESS

            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData() or []
            refs: list[tuple[str, int, int]] = []
            for acc in accounts:
                email = str(getattr(acc, 'AccountEmail', '') or '')
                if not email:
                    continue
                if pcon_qty > 0:
                    mi = int(GLOBAL_CACHE.ShMem.SendMessage(
                        my_email, email, _SCT.RestockAllPcons, (pcon_qty, 0, 0, 0)))
                    refs.append((email, mi, int(_SCT.RestockAllPcons)))
                if conset_qty > 0:
                    mi = int(GLOBAL_CACHE.ShMem.SendMessage(
                        my_email, email, _SCT.RestockConset, (conset_qty, 0, 0, 0)))
                    refs.append((email, mi, int(_SCT.RestockConset)))

            state['refs']        = refs
            state['deadline_ms'] = now + _PCON_RESTOCK_WAIT_TIMEOUT_MS
            state['phase']       = 'waiting'
            _parts = []
            if pcon_qty > 0:
                _parts.append(f'{pcon_qty} pcon(s)')
            if conset_qty > 0:
                _parts.append(f'{conset_qty} conset')
            ConsoleLog(BOT_NAME, f'Restock Pcons: topping up {" + ".join(_parts)} on {len(accounts)} account(s)…', Py4GW.Console.MessageType.Info)
            if not refs:
                state['phase'] = 'done'
                return _BT.NodeState.SUCCESS
            return _BT.NodeState.RUNNING

        if state['phase'] == 'waiting':
            still_pending: list[tuple[str, int, int]] = []
            for email, message_index, command in state['refs']:
                if int(message_index) < 0:
                    continue
                message = GLOBAL_CACHE.ShMem.GetInbox(int(message_index))
                is_same_message = (
                    bool(getattr(message, 'Active', False))
                    and str(getattr(message, 'ReceiverEmail', '') or '') == email
                    and str(getattr(message, 'SenderEmail', '') or '') == my_email
                    and int(getattr(message, 'Command', -1)) == int(command)
                )
                if is_same_message:
                    still_pending.append((email, message_index, command))
            state['refs'] = still_pending

            if not still_pending:
                ConsoleLog(BOT_NAME, 'Restock Pcons: done.', Py4GW.Console.MessageType.Info)
                state['phase'] = 'done'
                return _BT.NodeState.SUCCESS
            if now >= state['deadline_ms']:
                ConsoleLog(
                    BOT_NAME,
                    f'[EnterUW] RestockPcons: timeout after {_PCON_RESTOCK_WAIT_TIMEOUT_MS} ms, '
                    f'{len(still_pending)} message(s) did not confirm.',
                    Py4GW.Console.MessageType.Warning,
                )
                ConsoleLog(BOT_NAME, 'Restock Pcons: timed out waiting for some accounts.', Py4GW.Console.MessageType.Warning)
                state['phase'] = 'done'
                return _BT.NodeState.SUCCESS
            return _BT.NodeState.RUNNING

        return _BT.NodeState.SUCCESS

    return _BT(_BT.ActionNode(name='RestockPcons', action_fn=_tick))


def _build_summon_stone_tree() -> _BT:
    """Reusable building block: tell the FOLLOWER accounts to use a summoning stone.

    Dispatches ``SharedCommandType.UseSummoningStone`` via ``BT.Shared.SendCommand``
    to the same-map follower accounts. The leader (this account) is only used as a
    fallback when there are no same-map followers (e.g. solo). The shared-command
    handler itself guards the use (skips on Summoning Sickness or an already-active
    party summon), so each follower only summons when it actually can — and it picks
    whatever summoning stone that account carries (Ghastly/32557 included).

    This is NOT wired anywhere automatically. Hook it into a quest tree where a
    summon is wanted, e.g. inside a Sequence:

        _BT(_BT.SubtreeNode(name='SummonStone', subtree_fn=lambda _n: _build_summon_stone_tree())),

    Returns SUCCESS immediately after dispatch, so it can never stall the planner.
    """
    BT = Routines.BT
    from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType as _SCT

    def _dispatch(node: _BT.Node) -> _BT:
        my_email = str(Player.GetAccountEmail() or '')
        try:
            current_map_id = int(Map.GetMapID() or 0)
        except Exception:
            current_map_id = 0

        followers: list[str] = []
        for acc in (GLOBAL_CACHE.ShMem.GetAllAccountData() or []):
            email = str(getattr(acc, 'AccountEmail', '') or '')
            if not email or email == my_email:
                continue
            try:
                acc_map_id = int(getattr(acc.AgentData.Map, 'MapID', 0) or 0)
            except Exception:
                acc_map_id = 0
            if acc_map_id != current_map_id:
                continue
            followers.append(email)

        if followers:
            recipients = followers
            include_self = False
            target_desc = f'{len(recipients)} follower account(s)'
        else:
            # No same-map followers → fall back to the leader so a solo run still summons.
            recipients = [my_email] if my_email else []
            include_self = True
            target_desc = 'leader (no followers)'

        ConsoleLog(BOT_NAME, f'Summon Stone: requesting summon on {target_desc}.', Py4GW.Console.MessageType.Info)
        return BT.Shared.SendCommand(
            _SCT.UseSummoningStone,
            recipients=recipients,
            include_self=include_self,
            log=True,
        )

    return _BT(_BT.SubtreeNode(name='SummonStone', subtree_fn=_dispatch))


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
        ApoBT.LeaveParty(),
        ApoBT.TravelGH(),
        RoutinesBT.Multibox.SummonAllAccounts(timeout_ms=15_000, poll_interval_ms=100, log=True),
        ApoBT.Wait(duration_ms=1000, log=True),
        _BT(_BT.SubtreeNode(name='RestockSalvageKits', subtree_fn=lambda _node: _build_restock_salvage_kits_tree())),
        _BT(_BT.SubtreeNode(name='RestockPcons', subtree_fn=lambda _node: _build_restock_pcons_tree())),
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
      5.  Take Restore Monuments quest from same Reaper (buttons [2, 0]).
    """
    from Sources.ApoSource.ApoBottingLib import wrappers as ApoBT
    BT = Routines.BT

    return BT.Composite.Sequence(
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True, resurrection_scroll=True),
        _force_local_skills_on(),
        # Take quest from Lost Soul
        ApoBT.MoveAndAutoDialog(pos=(345, 7167), buttons=0, multi_account=True),
        # Followers use their summoning stone (handler self-guards eligibility).
        _BT(_BT.SubtreeNode(name='SummonStone', subtree_fn=lambda _n: _build_summon_stone_tree())),
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
        BT.Player.Wait(duration_ms=10000),
        # Collect reward from Reaper of the Labyrinth
        ApoBT.MoveAndAutoDialog(pos=(-5834, 12812), buttons=0, multi_account=True),
        # Take Restore Monuments quest from same Reaper
        ApoBT.MoveAndAutoDialog(pos=(-5834, 12812), buttons=[2, 0], multi_account=True),
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
        fallback_timeout_ms: int = 240_000,
    ) -> _BT:
        state: dict = {
            'clean_since_ms': None,
            'last_move_ms':   None,
            'started_ms':     None,
        }

        def _check(node: _BT.Node) -> _BT.NodeState:
            now = int(Utils.GetBaseTimestamp())
            if state['started_ms'] is None:
                state['started_ms'] = now

            elapsed_since_start = now - int(state['started_ms'])
            if elapsed_since_start >= int(fallback_timeout_ms):
                ConsoleLog(
                    BOT_NAME,
                    f'[RestorePlanes] WaitMindbladeSpawn fallback after {fallback_timeout_ms}ms — continuing.',
                    Py4GW.Console.MessageType.Warning,
                )
                return _BT.NodeState.SUCCESS

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
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True, resurrection_scroll=True),
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
        BT.Movement.Move(x=11037, y=-17988, pause_on_combat=False),
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
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True, resurrection_scroll=True),
        _force_local_skills_on(),
        # Followers use their summoning stone (handler self-guards eligibility).
        _BT(_BT.SubtreeNode(name='SummonStone', subtree_fn=lambda _n: _build_summon_stone_tree())),
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
        BT.Movement.Move(x=-5736,  y=-18904, pause_on_combat=False),
        BT.Movement.Move(x=-7156,  y=-18930, pause_on_combat=False),
        BT.Movement.Move(x=-7050,  y=-19448, pause_on_combat=False),
        name='RestorePools',
    )


def _terrorweb_queen_tree() -> _BT:
    BT = Routines.BT

    return BT.Composite.Sequence(
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True, resurrection_scroll=True),
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
        # Followers use their summoning stone (handler self-guards eligibility).
        _BT(_BT.SubtreeNode(name='SummonStone', subtree_fn=lambda _n: _build_summon_stone_tree())),
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
        facing_angle  = _Agent.GetRotationAngle(GLOBAL_CACHE.Party.GetPartyLeaderID())
        left_emails   = {e.strip().lower() for e in ImprisonedSpiritsSettings.LeftTeamEmails}
        pairs         = GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False)

        left_idx  = 0
        right_idx = 0

        for account, _ in pairs:
            party_pos = int(account.AgentPartyData.PartyPosition)
            if party_pos == 0:
                continue

            email = str(account.AccountEmail or '').strip().lower()
            if not email:
                continue

            if email in left_emails:
                # Clamp to last point if more accounts than positions.
                px, py = LEFT_POINTS[min(left_idx, len(LEFT_POINTS) - 1)]
                left_idx += 1
            else:
                px, py = RIGHT_POINTS[min(right_idx, len(RIGHT_POINTS) - 1)]
                right_idx += 1

            # Use SetHeroAIPropertyByEmail for reliable shared-memory writes
            # (avoids potential ctypes sub-struct copy pitfall with FlagPos.x = ...).
            GLOBAL_CACHE.ShMem.SetHeroAIPropertyByEmail(email, 'IsFlagged',       True)
            GLOBAL_CACHE.ShMem.SetHeroAIPropertyByEmail(email, 'FlagPos',         Vec2f(float(px), float(py)))
            GLOBAL_CACHE.ShMem.SetHeroAIPropertyByEmail(email, 'FlagFacingAngle', float(facing_angle))
            ConsoleLog(BOT_NAME, f'[IS] Flagged {email} → ({px}, {py})', Py4GW.Console.MessageType.Info)

        return _BT.NodeState.SUCCESS

    return BT.Composite.Sequence(
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True, resurrection_scroll=True),
        _force_local_skills_on(),
        _BT(_BT.ActionNode(name='UnblacklistDreamRider', action_fn=_unblacklist_dream_rider)),
        BT.Movement.Move(x=13010, y=4452),
        # Followers use their summoning stone (handler self-guards eligibility).
        _BT(_BT.SubtreeNode(name='SummonStone', subtree_fn=lambda _n: _build_summon_stone_tree())),
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
        # Followers use their summoning stone (handler self-guards eligibility).
        _BT(_BT.SubtreeNode(name='SummonStone', subtree_fn=lambda _n: _build_summon_stone_tree())),
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
    _kr2 = 1200.0

    return BT.Composite.Sequence(
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True, resurrection_scroll=True),
        _force_local_skills_on(),
        _BT(_BT.ActionNode(name='PurgeBlacklistNames', action_fn=_purge_blacklist_names_action)),
        _BT(_BT.ActionNode(name='BlacklistChainedSoul', action_fn=_blacklist_chained_soul)),
        _BT(_BT.ActionNode(name='BlacklistTorturedSpirits', action_fn=_blacklist_tortured_spirits)),
        BT.Player.Wait(duration_ms=10_000),
        _dialog_until_quest_active(
            x=-13217, y=5167,
            dialog_id=0x806E01,
            quest_id=int(UWQuestID.WrathfulSpirits),
            label='WrathfulSpirits',
        ),
        BT.Movement.Move(x=-13422, y=973),
        _BT(_BT.ActionNode(name='UnblacklistTorturedSpirits', action_fn=_unblacklist_tortured_spirits)),
        _kill_route_until_quest_completed(
            waypoints=[
                (Vec2f(-13791, 1642), _kr),
                (Vec2f(-12889, 963),  _kr),
                (Vec2f(-11445, 1154), _kr),
                (Vec2f(-10554, 1695), _kr),
                (Vec2f(-9481, 963),   _kr),
                (Vec2f(-9949, 177),   _kr),
                (Vec2f(-11498, -173), _kr),
                (Vec2f(-12677, -205), _kr),
                (Vec2f(-13622, 336),  _kr),
                (Vec2f(-12974, 4116), _kr),
                (Vec2f(-14184, 7279), _kr2),
                (Vec2f(-15055, 3755), _kr2),
                (Vec2f(-13409, 4933), _kr),
                (Vec2f(-13217, 5167), _kr2),
            ],
            quest_id=int(UWQuestID.WrathfulSpirits),
            label='WrathfulSpirits',
        ),
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

    def _set_soulkeeper_call_active(enabled: bool) -> _BT:
        def _tick(_node: _BT.Node) -> _BT.NodeState:
            global _soulkeeper_call_active
            _soulkeeper_call_active = bool(enabled)
            return _BT.NodeState.SUCCESS

        return _BT(_BT.ActionNode(name=f"{'Enable' if enabled else 'Disable'}SoulkeeperCall", action_fn=_tick))

    def _set_follower_flags_at_hold(node: _BT.Node) -> _BT.NodeState:
        from Py4GWCoreLib import Agent as _Agent
        facing_angle = _Agent.GetRotationAngle(GLOBAL_CACHE.Party.GetPartyLeaderID())
        for account, _ in GLOBAL_CACHE.ShMem.GetAllActiveAccountHeroAIPairs(sort_results=False):
            if int(account.AgentPartyData.PartyPosition) == 0:
                continue
            email = str(account.AccountEmail or '').strip().lower()
            if not email:
                continue
            GLOBAL_CACHE.ShMem.SetHeroAIPropertyByEmail(email, 'IsFlagged',       True)
            GLOBAL_CACHE.ShMem.SetHeroAIPropertyByEmail(email, 'FlagPos',         Vec2f(float(_fx), float(_fy)))
            GLOBAL_CACHE.ShMem.SetHeroAIPropertyByEmail(email, 'FlagFacingAngle', float(facing_angle))
        return _BT.NodeState.SUCCESS

    return BT.Composite.Sequence(
        _BT(_BT.ActionNode(name='PrepareUnwantedGuestsBlacklist', action_fn=_prepare_unwanted_guests_blacklist)),
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True, resurrection_scroll=True),
        _force_local_skills_on(),
        BT.Movement.Move(x=_fx, y=_fy),
        _BT(_BT.ActionNode(name='SetFollowerFlagsUnwantedGuests', action_fn=_set_follower_flags_at_hold)),
        _set_soulkeeper_call_active(True),
        BT.Movement.Move(x=-5850, y=12818),
        _dialog_until_quest_active(
            x=-5850, y=12818,
            dialog_id=0x806701,
            quest_id=int(UWQuestID.UnwantedGuests),
            label='UnwantedGuests',
        ),
        BT.Movement.Move(x=_fx, y=_fy),
        _set_soulkeeper_call_active(False),
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
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True, resurrection_scroll=True),
        _force_local_skills_on(),
        _BT(_BT.ActionNode(name='UnblacklistVengefulAatxe', action_fn=_unblacklist_vengeful_aatxe)),
        # Followers use their summoning stone (handler self-guards eligibility).
        _BT(_BT.SubtreeNode(name='SummonStone', subtree_fn=lambda _n: _build_summon_stone_tree())),
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
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True, resurrection_scroll=True),
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








def _dhuum_tree() -> _BT:
    """
    Dhuum / The Nightmare Cometh.

    Part 1: King Frozenwind (2403) dialog button 0, move to (-12093, 17282),
            disable HeroAI combat, flag accounts, enable Dhuum Helper.
    """
    BT = Routines.BT
    return BT.Composite.Sequence(
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True, resurrection_scroll=True),
        _force_local_skills_on(),
        _follow_king_frozenwind(),
        BT.Player.Wait(10000),
        BT.Agents.MoveTargetInteractAndAutomaticDialogByModelID(
            _KING_FROZENWIND_MODEL_ID,
            button_number=0,
            log=True,
        ),
        BT.Movement.Move(x=-12093, y=17282),
        # Followers use their summoning stone (handler self-guards eligibility).
        _BT(_BT.SubtreeNode(name='SummonStone', subtree_fn=lambda _n: _build_summon_stone_tree())),
        _disable_heroai_combat_all(),
        _flag_dhuum_accounts(),
        _enable_dhuum_helper_on_all_accounts(),
        BT.Player.Wait(10000),
        BT.Movement.Move(-13799,17274, pause_on_combat=False),
        _wait_for_spirit_forms(),
        _force_local_skills_on(),
        BT.Movement.Move(-14440,17383, pause_on_combat=False),
        _enable_heroai_combat_all(),
        _wait_for_uw_chest(),
        name='Dhuum',
    )


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
        # Interacting with the chest only makes the reward drop on the ground
        # (assigned per account); nothing collects it on its own. PickUpLoot is a
        # self-contained per-account routine, so broadcasting it (include_self)
        # makes the leader and every follower walk over and grab their own drops
        # before the King dialog / resign below moves anyone off the loot.
        BT.Shared.SendAndWait(
            _SCT.PickUpLoot,
            include_self=True,
            timeout_ms=90_000,
            log=True,
        ),
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


# ╔══════════════════════════════════════════════════════════════════════════════
# ║  PARALLEL SERVICES
# ║  (background trees that run every tick alongside the quest flow: step timer,
# ║   consumable upkeep, guard/priority-target monitors)
# ╚══════════════════════════════════════════════════════════════════════════════

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

        # Quest/run times are measured against the in-game instance timer (same
        # clock as the Instance Timer widget) instead of wall/monotonic time.
        # The instance timer starts at 0 on entering UW, so sample it every tick
        # while we are inside the UW explorable and keep the last valid reading;
        # this also keeps the final 'Loot Chest' time correct if the step change
        # is only detected after the party has left the instance.
        inst_ms = int(Map.GetInstanceUptime())
        if inst_ms > 0 and Map.IsExplorable():
            _timing_state['last_instance_ms'] = inst_ms

        if current_step == last_step:
            return _BT.NodeState.RUNNING

        now_ms = int(_timing_state['last_instance_ms'])

        # Record the just-completed step's cumulative time BEFORE applying any
        # run reset for the new step. The 'Loot Chest' → 'Enter Underworld'
        # transition (repeat mode) would otherwise clear run_start_ms first and
        # silently drop the Loot Chest stat and the run-success console line.
        run_start = _timing_state['run_start_ms']
        if last_step and last_step in _TIMED_QUESTS and run_start is not None:
            elapsed_ms = now_ms - run_start
            if elapsed_ms >= 0:
                _quest_completion_times[last_step] = elapsed_ms
                _quest_times_log.setdefault(last_step, []).append(elapsed_ms // 1000)
                _save_quest_times_log()
                if last_step == 'Loot Chest':
                    total_s = elapsed_ms // 1000
                    ConsoleLog(BOT_NAME, f'Run SUCCESS completed in {_fmt_s(total_s)}', Py4GW.Console.MessageType.Success)

        if current_step == 'Enter Underworld':
            _quest_completion_times.clear()
            _timing_state['run_start_ms'] = None

        if current_step == _RUN_START_QUEST:
            _timing_state['run_start_ms'] = now_ms

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
            ConsoleLog(BOT_NAME, f'Party wiped at step: {step_at_wipe}', Py4GW.Console.MessageType.Warning)
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




def _build_priority_target_service() -> _BT:
    """Background service: call the highest-priority UW enemy in range as party target.

    Port of UnderworldV2 ``BuildPriorityTargetService`` / ``CallPriorityTarget``.
    Uses HeroAI ``CallTarget`` on the party leader via ``_party_call_or_change_target``.
    Priority lookup is keyed on the encoded name (Agent.GetEncNameStrByID), which is
    language-independent and stable across game updates; it also avoids TextParser
    (unlike GetNameByID). GetNameByID is only used for the (name-based) blacklist
    filter, and only for agents that already match a priority encoded name.
    """
    priority_map: dict[str, int] = {enc.value: idx for idx, enc in enumerate(UW_TARGET_PRIORITY)}
    sentinel_priority = len(UW_TARGET_PRIORITY)
    range_sq = float(_UW_PRIORITY_TARGET_RANGE) * float(_UW_PRIORITY_TARGET_RANGE)
    state: dict = {'last_call_ms': 0.0, 'last_scan_ms': 0.0}

    def _agent_priority(enc_name: str) -> int:
        return priority_map.get(enc_name, -1) if enc_name else -1

    def _agent_enc(agent_id: int) -> str:
        try:
            return Agent.GetEncNameStrByID(agent_id, literal=False) or ''
        except Exception:
            return ''

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
        try:
            enemy_ids = list(_AgentArray.GetEnemyArray() or [])
        except Exception:
            return _BT.NodeState.RUNNING

        for raw_agent_id in enemy_ids:
            try:
                agent_id = int(raw_agent_id)
                if not Agent.IsAlive(agent_id):
                    continue
                prio = _agent_priority(_agent_enc(agent_id))
                if prio == -1 or prio >= best_priority:
                    continue
                # Only matched-priority agents reach the (name-based) blacklist filter.
                try:
                    agent_name = (Agent.GetNameByID(agent_id) or '').strip().lower()
                except Exception:
                    agent_name = ''
                if agent_name and agent_name in blacklist_names:
                    continue
                ax, ay = Agent.GetXY(agent_id)
                dx, dy = px - float(ax), py - float(ay)
            except Exception:
                continue
            if dx * dx + dy * dy > range_sq:
                continue
            best_priority = prio
            best_agent_id = agent_id

        if best_agent_id == 0:
            return _BT.NodeState.RUNNING
        try:
            current_target_id = int(Player.GetTargetID() or 0)
        except Exception:
            current_target_id = 0

        if current_target_id != 0:
            current_prio = sentinel_priority
            try:
                current_prio = _agent_priority(_agent_enc(current_target_id))
                if current_prio == -1:
                    current_prio = sentinel_priority
                else:
                    current_target_name = (Agent.GetNameByID(current_target_id) or '').strip().lower()
                    if current_target_name and current_target_name in blacklist_names:
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


def _build_soulkeeper_call_service() -> _BT:
    """Call Keeper of Souls while the Unwanted Guests quest pickup window is active."""
    target_name = 'keeper of souls'
    range_sq = 3000.0 * 3000.0
    scan_interval_ms = 500.0
    call_cooldown_ms = 1500.0
    state: dict = {'last_call_ms': 0.0, 'last_scan_ms': 0.0}

    def _tick(node: _BT.Node) -> _BT.NodeState:
        from Py4GWCoreLib.AgentArray import AgentArray as _AgentArray

        if not _soulkeeper_call_active:
            return _BT.NodeState.RUNNING
        if _skip_background_upkeep(node.blackboard):
            return _BT.NodeState.RUNNING

        now_ms = time.monotonic() * 1000.0
        if (now_ms - state['last_scan_ms']) < scan_interval_ms:
            return _BT.NodeState.RUNNING
        state['last_scan_ms'] = now_ms

        try:
            if not Map.IsExplorable() or int(Map.GetMapID()) != int(UW_MAP_ID):
                return _BT.NodeState.RUNNING
            leader_id = int(GLOBAL_CACHE.Party.GetPartyLeaderID() or 0)
            local_id = int(Player.GetAgentID() or 0)
        except Exception:
            return _BT.NodeState.RUNNING
        if leader_id > 0 and local_id > 0 and local_id != leader_id:
            return _BT.NodeState.RUNNING

        player_pos = Player.GetXY()
        if not player_pos:
            return _BT.NodeState.RUNNING
        px, py = float(player_pos[0]), float(player_pos[1])
        best_agent_id = 0
        best_dist_sq = range_sq

        try:
            enemy_ids = list(_AgentArray.GetEnemyArray() or [])
        except Exception:
            return _BT.NodeState.RUNNING
        for raw_agent_id in enemy_ids:
            try:
                agent_id = int(raw_agent_id)
                if not Agent.IsValid(agent_id) or not Agent.IsAlive(agent_id):
                    continue
                agent_name = (Agent.GetNameByID(agent_id) or '').strip().lower()
                if agent_name != target_name:
                    continue
                ax, ay = Agent.GetXY(agent_id)
                dx = px - float(ax)
                dy = py - float(ay)
                dist_sq = dx * dx + dy * dy
            except Exception:
                continue
            if dist_sq <= best_dist_sq:
                best_dist_sq = dist_sq
                best_agent_id = agent_id

        if best_agent_id and (now_ms - state['last_call_ms']) >= call_cooldown_ms:
            _party_call_or_change_target(best_agent_id)
            state['last_call_ms'] = now_ms
        return _BT.NodeState.RUNNING

    return _BT(
        _BT.RepeaterForeverNode(
            child=_BT.ActionNode(name='SoulkeeperCallServiceTick', action_fn=_tick),
            name='SoulkeeperCallService',
        )
    )


def _build_consolidated_consumable_upkeep_service() -> _BT:
    """Background consumable upkeep: one ConsumableService per item under a ParallelNode.

    The item set per category comes straight from the core library's canonical
    consumable lists (``consumable_specs``), so every pcon the library knows is
    covered — no hand-maintained subset. ConsumableService self-throttles
    (``check_interval_ms``) and only acts when its effect is missing, so ticking
    every item in parallel does not spam ``UseItem`` or effect scans. Each child is
    guarded by the global Use-Cons toggle, its category toggle, and the planner's
    background-upkeep skip flag. ConsumableService returns RUNNING in steady state,
    so the ParallelNode stays RUNNING and never resets its children.
    """
    from Py4GWCoreLib.routines_src.behaviourtrees_src.botting_consumables import consumable_specs

    def _make_child(category: str, model_id: int, effect_name: str) -> _BT.Node:
        inner = Routines.BT.Upkeepers.ConsumableService(model_id, effect_name)

        def _tick(node: _BT.Node) -> _BT.NodeState:
            if not BotSettings.UseCons:
                return _BT.NodeState.RUNNING
            if _skip_background_upkeep(node.blackboard):
                return _BT.NodeState.RUNNING
            if not ConsSettings.is_category_active(category):
                return _BT.NodeState.RUNNING
            inner.blackboard = node.blackboard
            return inner.tick()

        return _BT.ActionNode(name=f'ConsumableUpkeep_{category}_{model_id}', action_fn=_tick, aftercast_ms=0)

    children: list[_BT.Node] = []
    for category, mode in _CONS_CATEGORY_MODES.items():
        for model_id, effect_name in consumable_specs(mode):
            children.append(_make_child(category, int(model_id), str(effect_name)))

    return _BT(_BT.ParallelNode(children=children, name='ConsumableUpkeepParallel'))


# Dead-member rescue tuning. When a party member dies and is left behind, the
# leader backtracks to the corpse and holds there until the party rezzes them.
_UW_RESCUE_ARRIVE_RANGE       = float(Range.Spellcast.value)  # close enough for the party to rez
_UW_RESCUE_MOVE_TOLERANCE     = float(Range.Spellcast.value)
_UW_RESCUE_ARRIVAL_WAIT_MS    = 25_000.0   # max hold at the corpse before giving up this attempt
_UW_RESCUE_OVERALL_TIMEOUT_MS = 60_000.0   # absolute cap on a single rescue attempt (anti-stall)
_UW_RESCUE_SCAN_INTERVAL_MS   = 400.0      # idle detection throttle (full-rate once active)
# Private pause key for the rescue Move: it must keep walking while the planner's
# own Move nodes are paused via PAUSE_MOVEMENT, so it reads a flag we never set.
_UW_RESCUE_MOVE_PAUSE_KEY     = 'UW_RESCUE_NEVER_PAUSE'


def _build_dead_member_recovery_service() -> _BT:
    """Background service: walk the leader back to a dead party member left behind
    and hold there until the party revives them.

    Port of the legacy ``BottingClass._on_party_member_death_behind`` coroutine to
    the BottingTree model. Leader-only. While a rescue is active it sets
    ``uw_dead_recovery_active`` on the blackboard; the planner-tick override reads
    that flag and forces ``PAUSE_MOVEMENT`` so the quest waypoints don't fight the
    backtrack. The rescue itself drives a private ``Move`` subtree that uses its own
    (never-set) pause key, so it keeps walking while the planner is paused.

    Trigger:  a dead member is farther than Earshot behind the leader.
    Hold:     while in danger or HeroAI looting, stay put (HeroAI handles it) but
              keep the planner paused so we don't abandon the corpse.
    Release:  no dead members remain (everyone alive), arrival-wait elapsed, the
              overall timeout fired, or the party wiped — anti-stall safeguards so a
              permanently-unrezzable corpse can never freeze the run.
    """
    state: dict = {
        'active':       False,
        'target_id':    0,
        'move_tree':    None,
        'arrived_ms':   None,
        'started_ms':   0.0,
        'last_scan_ms': 0.0,
    }

    def _release(node: _BT.Node) -> None:
        state['active'] = False
        state['target_id'] = 0
        state['move_tree'] = None
        state['arrived_ms'] = None
        node.blackboard['uw_dead_recovery_active'] = False

    def _tick(node: _BT.Node) -> _BT.NodeState:
        bb = node.blackboard

        # Tailored guards (intentionally NOT _skip_background_upkeep: that checks
        # PAUSE_MOVEMENT, which the planner override sets True *because* we are
        # active — using it here would instantly release the rescue).
        if bb.get('party_wipe_recovery_active', False):
            _release(node)
            return _BT.NodeState.RUNNING
        # Only rescue during the explorable quest steps Clear the Chamber …
        # Servants of Grenth; disabled at entry, during Dhuum, and at Loot Chest.
        if str(bb.get('current_step_name', '') or '') not in _DEAD_RESCUE_STEPS:
            _release(node)
            return _BT.NodeState.RUNNING
        try:
            if Map.IsMapLoading() or not Map.IsMapReady():
                _release(node)
                return _BT.NodeState.RUNNING
            if not Map.IsExplorable() or int(Map.GetMapID()) != int(UW_MAP_ID):
                _release(node)
                return _BT.NodeState.RUNNING
        except Exception:
            _release(node)
            return _BT.NodeState.RUNNING

        if Routines.Checks.Party.IsPartyWiped() or GLOBAL_CACHE.Party.IsPartyDefeated():
            _release(node)
            return _BT.NodeState.RUNNING

        # Leader-only: only the account driving planner movement should backtrack.
        try:
            leader_id = int(GLOBAL_CACHE.Party.GetPartyLeaderID() or 0)
            local_id = int(Player.GetAgentID() or 0)
        except Exception:
            leader_id = local_id = 0
        if leader_id > 0 and local_id > 0 and local_id != leader_id:
            _release(node)
            return _BT.NodeState.RUNNING

        now_ms = time.monotonic() * 1000.0
        # Throttle detection while idle; once a rescue is active we tick the Move
        # every frame so movement progresses smoothly.
        if not state['active'] and (now_ms - state['last_scan_ms']) < _UW_RESCUE_SCAN_INTERVAL_MS:
            return _BT.NodeState.RUNNING
        state['last_scan_ms'] = now_ms

        dead_id = int(Routines.Party.GetDeadPartyMemberID() or 0)
        if dead_id == 0 or not Agent.IsValid(dead_id):
            # Everyone alive again → resume normal planner movement.
            _release(node)
            return _BT.NodeState.RUNNING

        if not state['active']:
            # Only trigger once the dead member is meaningfully *behind* us; if the
            # party can rez in place no backtrack is needed.
            if not Routines.Checks.Party.IsDeadPartyMemberBehind():
                bb['uw_dead_recovery_active'] = False
                return _BT.NodeState.RUNNING
            state['active'] = True
            state['started_ms'] = now_ms
            state['arrived_ms'] = None
            state['target_id'] = 0
            state['move_tree'] = None
            ConsoleLog(BOT_NAME, 'Dead party member behind — walking back to revive.', Py4GW.Console.MessageType.Info)

        bb['uw_dead_recovery_active'] = True

        # Absolute safety cap so a permanently-unrezzable corpse can't stall the run.
        if (now_ms - state['started_ms']) >= _UW_RESCUE_OVERALL_TIMEOUT_MS:
            ConsoleLog(BOT_NAME, 'Dead-member rescue timed out — resuming run.', Py4GW.Console.MessageType.Info)
            _release(node)
            return _BT.NodeState.RUNNING

        player_pos = Player.GetXY()
        dead_pos = Agent.GetXY(dead_id)
        if not player_pos or not dead_pos:
            return _BT.NodeState.RUNNING

        if Utils.Distance(player_pos, dead_pos) <= _UW_RESCUE_ARRIVE_RANGE:
            # At the corpse: hold and let the party rez. Give up after a while so a
            # corpse that never gets rezzed doesn't pin us here forever.
            state['move_tree'] = None
            if state['arrived_ms'] is None:
                state['arrived_ms'] = now_ms
            elif (now_ms - state['arrived_ms']) >= _UW_RESCUE_ARRIVAL_WAIT_MS:
                ConsoleLog(BOT_NAME, 'Could not revive dead member in time — resuming run.', Py4GW.Console.MessageType.Info)
                _release(node)
            return _BT.NodeState.RUNNING

        # En route. While fighting or looting, hold position (HeroAI handles it) and
        # keep the planner paused so we don't abandon the corpse.
        if Routines.Checks.Agents.InDanger() or bb.get('LOOTING_ACTIVE', False):
            state['move_tree'] = None
            return _BT.NodeState.RUNNING

        if state['move_tree'] is None or state['target_id'] != dead_id:
            state['target_id'] = dead_id
            state['move_tree'] = Routines.BT.Movement.Move(
                x=float(dead_pos[0]),
                y=float(dead_pos[1]),
                tolerance=_UW_RESCUE_MOVE_TOLERANCE,
                pause_on_combat=False,
                pause_flag_key=_UW_RESCUE_MOVE_PAUSE_KEY,
            )
        move_tree = state['move_tree']
        move_tree.blackboard = bb
        result = move_tree.tick()
        if result == _BT.NodeState.SUCCESS or result == _BT.NodeState.FAILURE:
            state['move_tree'] = None  # rebuild / re-evaluate next tick
        return _BT.NodeState.RUNNING

    return _BT(
        _BT.RepeaterForeverNode(
            child=_BT.ActionNode(name='DeadMemberRecoveryTick', action_fn=_tick),
            name='DeadMemberRecoveryService',
        )
    )


# ╔══════════════════════════════════════════════════════════════════════════════
# ║  BOT REGISTRATION
# ║  (bind the step trees + services to the planner, then expose the module entry)
# ╚══════════════════════════════════════════════════════════════════════════════

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
bot.AddServiceTree('SoulkeeperCallService',   _build_soulkeeper_call_service)
bot.AddServiceTree('ConsumableUpkeep', _build_consolidated_consumable_upkeep_service)
bot.AddServiceTree('BehemothGuard', _build_behemoth_guard_service)
bot.AddServiceTree('DeadMemberRecovery', _build_dead_member_recovery_service)

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
    # Dead-member rescue owns movement while active: pause the planner's own Move
    # nodes (they read PAUSE_MOVEMENT) so the quest waypoints don't fight the
    # backtrack to the corpse driven by _build_dead_member_recovery_service. The
    # rescue Move uses a separate, never-set pause key so it keeps walking.
    if bb.get('uw_dead_recovery_active', False):
        bb['PAUSE_MOVEMENT'] = True
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
    global _map_stable_frames, _settings_loaded

    # Pull persisted settings once the account-scoped IniManager key resolves.
    if not _settings_loaded and _ini.key():
        _load_all_settings()
        _settings_loaded = True

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
        main_child_dimensions=(550, 680),
        additional_ui=_draw_main_additional_ui,
    )


if __name__ == '__main__':
    main()
