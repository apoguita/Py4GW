
# ╔══════════════════════════════════════════════════════════════════════════════
# ║  File    : UnderworldBT.py
# ║  Purpose : BehaviorTree port of the Underworld bot.
# ║            UI only — bot logic not yet ported.
# ╚══════════════════════════════════════════════════════════════════════════════

import json
import os
import time
from collections import deque

import Py4GW
import PyImGui
from Py4GWCoreLib import GLOBAL_CACHE, ConsoleLog, IniHandler, Map, Player, Routines, Utils
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
UW_SCROLL_MODEL_ID = 3746  # ModelID.Passage_Scroll_Uw
DEFAULT_UW_ENTRYPOINT_KEY = 'embark_beach'
UW_ENTRYPOINTS: dict[str, tuple[str, int]] = {
    'embark_beach':       ('Embark Beach',       int(name_to_map_id['Embark Beach'])),
    'temple_of_the_ages': ('Temple of the Ages', int(name_to_map_id['Temple of the Ages'])),
    'chantry_of_secrets': ('Chantry of Secrets', int(name_to_map_id['Chantry of Secrets'])),
    'zin_ku_corridor':    ('Zin Ku Corridor',     int(name_to_map_id['Zin Ku Corridor'])),
}

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

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, 'inv_refill_enabled', str(cls.RefillEnabled))
        _ini.write_key(BOT_NAME, 'inv_restock_cons',   str(cls.RestockCons))


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
class DhuumSettings:
    """Sacrifice / armor-switch account assignments for the Dhuum fight."""
    SacrificeEmails:       set[str] = _read_emails_set('dhuum_sacrifice_emails')
    ArmorSwitchEmails:     set[str] = _read_emails_set('dhuum_armor_switch_emails')
    MinSpiritformAccounts: int      = int(_ini.read_int(BOT_NAME, 'dhuum_min_spiritform', 2))

    @classmethod
    def save(cls) -> None:
        _ini.write_key(BOT_NAME, 'dhuum_sacrifice_emails',    ';'.join(sorted(cls.SacrificeEmails)))
        _ini.write_key(BOT_NAME, 'dhuum_armor_switch_emails', ';'.join(sorted(cls.ArmorSwitchEmails)))
        _ini.write_key(BOT_NAME, 'dhuum_min_spiritform',      str(cls.MinSpiritformAccounts))

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
]

_quest_completion_times: dict[str, int] = {}
_DEBUG_LOG_MAX = 120
_debug_watchdog_log: deque[str] = deque(maxlen=_DEBUG_LOG_MAX)

# ── Log files ─────────────────────────────────────────────────────────────────
_WIPE_LOG_FILE    = os.path.join(Py4GW.Console.get_projects_path(), 'Widgets', 'Config', 'UnderworldBT_wipes.log')
_QUEST_TIMES_FILE = os.path.join(Py4GW.Console.get_projects_path(), 'Widgets', 'Config', 'UnderworldBT_quest_times.json')


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

# ── Armor edit popup state ────────────────────────────────────────────────────
_ARMOR_JSON_FILE  = os.path.join(Py4GW.Console.get_projects_path(), 'Widgets', 'Config', 'EquippedArmor.json')
_ARMOR_SLOT_NAMES = {2: 'Chest', 3: 'Legs', 4: 'Head', 5: 'Feet', 6: 'Hands'}

_armor_edit_email:  str | None       = None
_armor_edit_char:   str              = ''
_armor_edit_normal: dict[str, int]   = {}
_armor_edit_sac:    dict[str, int]   = {}


# ╔══════════════════════════════════════════════════════════════════════════════
# ║  HELPERS
# ╚══════════════════════════════════════════════════════════════════════════════

def _read_armor_json() -> dict:
    try:
        if os.path.exists(_ARMOR_JSON_FILE):
            with open(_ARMOR_JSON_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_armor_json(email: str, normal: dict[str, int], sacrifice: dict[str, int]) -> None:
    try:
        all_armor = _read_armor_json()
        existing  = all_armor.get(email, {})
        if not isinstance(existing, dict) or 'normal' not in existing:
            existing = {}
        existing['normal']    = normal
        existing['sacrifice'] = sacrifice
        all_armor[email] = existing
        tmp = _ARMOR_JSON_FILE + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(all_armor, f, indent=2)
        os.replace(tmp, _ARMOR_JSON_FILE)
    except Exception as e:
        ConsoleLog(BOT_NAME, f'Armor JSON save error: {e}', Py4GW.Console.MessageType.Warning)


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
    if changed:
        InventorySettings.save()


def _draw_cons_settings() -> None:
    PyImGui.text_wrapped(
        'Configure which consumables to upkeep automatically and how many to restock '
        'from the Xunlai chest when the bot visits the guild hall between runs.'
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
    new_min = max(0, PyImGui.input_int('Min Spiritform accounts', DhuumSettings.MinSpiritformAccounts))
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
    if PyImGui.begin_table('##dhuum_settings', 3, table_flags, 0.0, 0.0):
        PyImGui.table_setup_column('Sacrifice',    PyImGui.TableColumnFlags.WidthFixed,   90.0)
        PyImGui.table_setup_column('Switch Armor', PyImGui.TableColumnFlags.WidthFixed,  170.0)
        PyImGui.table_setup_column('Account',      PyImGui.TableColumnFlags.WidthStretch, 0.0)
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
            cur_arm = DhuumSettings.is_armor_switch(email)
            new_arm = PyImGui.checkbox(f'##arm_{email}', cur_arm)
            PyImGui.same_line(0.0, 6.0)
            if PyImGui.button(f'Edit##armedit_{email}'):
                global _armor_edit_email, _armor_edit_char, _armor_edit_normal, _armor_edit_sac
                data = _read_armor_json()
                entry = data.get(email, {})
                _armor_edit_email  = email
                _armor_edit_char   = char_name
                _armor_edit_normal = dict(entry.get('normal', {}))
                _armor_edit_sac    = dict(entry.get('sacrifice', {}))

            PyImGui.table_next_column()
            PyImGui.text(f'{char_name}  (this account)' if is_self else char_name)

            if is_self:
                PyImGui.end_disabled()
            if new_sac != cur_sac:
                DhuumSettings.set_sacrifice(email, new_sac)
            if new_arm != cur_arm:
                DhuumSettings.set_armor_switch(email, new_arm)

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
    PyImGui.text('Spirit Form (3134) — Active accounts:')
    try:
        accounts       = GLOBAL_CACHE.ShMem.GetAllAccountData() or []
        current_map_id = Map.GetMapID()
        found_any      = False
        for account in accounts:
            if not getattr(account, 'IsSlotActive', True):
                continue
            email = str(getattr(account, 'AccountEmail', '') or '').strip()
            if not email:
                continue
            has_buff = any(
                b.SkillId == 3134
                for b in account.AgentData.Buffs.Buffs
                if b.SkillId != 0
            )
            if not has_buff:
                continue
            found_any = True
            PyImGui.text_colored(f'  {email}', _color_ok)
        if not found_any:
            PyImGui.text_colored('  (none)', _color_grey)
    except Exception as e:
        PyImGui.text_colored(f'  Error: {e}', _color_warn)

    PyImGui.separator()
    PyImGui.text('Death Penalty — Party accounts:')
    try:
        found_any = False
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData() or []:
            if not getattr(account, 'IsSlotActive', True):
                continue
            email = str(getattr(account, 'AccountEmail', '') or '').strip()
            if not email:
                continue
            dp = 100 - int(getattr(account.AgentData, 'Morale', 100) or 100)
            if dp <= 0:
                continue
            found_any = True
            PyImGui.text_colored(f'  {email}  -{dp}%', _color_warn if dp >= 15 else _color_low)
        if not found_any:
            PyImGui.text_colored('  (no death penalty)', _color_grey)
    except Exception as e:
        PyImGui.text_colored(f'  Error: {e}', _color_warn)

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


def _draw_armor_edit_window() -> None:
    global _armor_edit_email, _armor_edit_char, _armor_edit_normal, _armor_edit_sac
    if _armor_edit_email is None:
        return

    if PyImGui.begin(f'Armor Setup: {_armor_edit_char}##armor_edit', PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.text_wrapped(f'Account: {_armor_edit_email}')
        PyImGui.text_wrapped('Enter model IDs for normal and sacrifice armor.')
        PyImGui.separator()

        tbl_flags = PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersInnerV | PyImGui.TableFlags.BordersOuterH
        if PyImGui.begin_table('##armor_edit_tbl', 3, tbl_flags, 0.0, 0.0):
            PyImGui.table_setup_column('Slot',      PyImGui.TableColumnFlags.WidthFixed,  80.0)
            PyImGui.table_setup_column('Normal',    PyImGui.TableColumnFlags.WidthFixed, 150.0)
            PyImGui.table_setup_column('Sacrifice', PyImGui.TableColumnFlags.WidthFixed, 150.0)
            PyImGui.table_headers_row()

            for slot in sorted(_ARMOR_SLOT_NAMES):
                slot_str = str(slot)
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text(_ARMOR_SLOT_NAMES[slot])
                PyImGui.table_next_column()
                cur_n = _armor_edit_normal.get(slot_str, 0)
                _armor_edit_normal[slot_str] = _input_int_val(
                    PyImGui.input_int(f'##n{slot}', cur_n, 0, 0, 0), cur_n
                )
                PyImGui.table_next_column()
                cur_s = _armor_edit_sac.get(slot_str, 0)
                _armor_edit_sac[slot_str] = _input_int_val(
                    PyImGui.input_int(f'##s{slot}', cur_s, 0, 0, 0), cur_s
                )
            PyImGui.end_table()

        PyImGui.separator()
        if PyImGui.button('Save##armor_edit'):
            _save_armor_json(_armor_edit_email, dict(_armor_edit_normal), dict(_armor_edit_sac))
            _armor_edit_email = None
        PyImGui.same_line(0.0, 10.0)
        if PyImGui.button('Close##armor_edit'):
            _armor_edit_email = None

    PyImGui.end()


def _draw_main_additional_ui() -> None:
    _color_done    = Utils.RGBToNormal(100, 255, 100, 255)
    _color_pending = Utils.RGBToNormal(140, 140, 140, 255)
    _color_avg     = Utils.RGBToNormal(255, 210,  80, 255)

    PyImGui.text('Quest Progress')
    if PyImGui.begin_table(
        '##uw_quest_table', 3,
        PyImGui.TableFlags.RowBg
        | PyImGui.TableFlags.BordersOuterH
        | PyImGui.TableFlags.BordersOuterV
        | PyImGui.TableFlags.BordersInnerV,
    ):
        PyImGui.table_setup_column('Quest', PyImGui.TableColumnFlags.WidthStretch)
        PyImGui.table_setup_column('Time',  PyImGui.TableColumnFlags.WidthFixed, 72)
        PyImGui.table_setup_column('Avg',   PyImGui.TableColumnFlags.WidthFixed, 72)
        PyImGui.table_headers_row()

        for quest_name in _QUEST_ORDER:
            PyImGui.table_next_row()
            done    = quest_name in _quest_completion_times
            history = _quest_times_log.get(quest_name, [])
            recent  = history[-5:] if history else []
            avg_s   = int(sum(recent) / len(recent)) if recent else None

            PyImGui.table_set_column_index(0)
            PyImGui.text_colored(quest_name, _color_done if done else _color_pending)

            PyImGui.table_set_column_index(1)
            if done:
                uptime_s = _quest_completion_times[quest_name] // 1000
                h, rem = divmod(uptime_s, 3600)
                m, s   = divmod(rem, 60)
                col = _color_done if avg_s is None else (
                    Utils.RGBToNormal(100, 255, 100, 255) if uptime_s <= avg_s
                    else Utils.RGBToNormal(255, 80, 80, 255)
                )
                PyImGui.text_colored(f'{h:02d}:{m:02d}:{s:02d}', col)
            else:
                PyImGui.text_colored('--:--:--', _color_pending)

            PyImGui.table_set_column_index(2)
            if avg_s is not None:
                ah, arem = divmod(avg_s, 3600)
                am, as_  = divmod(arem, 60)
                PyImGui.text_colored(f'{ah:02d}:{am:02d}:{as_:02d}', _color_avg)
            else:
                PyImGui.text_colored('--:--:--', _color_pending)

        PyImGui.end_table()


# ╔══════════════════════════════════════════════════════════════════════════════
# ║  BOT + MAIN
# ╚══════════════════════════════════════════════════════════════════════════════

bot = BottingTree.Create(bot_name=BOT_NAME, isolation_enabled=False)
bot.UI.override_draw_help(lambda: _draw_help())
bot.UI.override_draw_config(lambda: _draw_settings())

# ── Planner steps ──────────────────────────────────────────────────────────────
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree as _BT

def _placeholder(name: str) -> _BT:
    return _BT(_BT.ActionNode(name=name, action_fn=lambda node: _BT.NodeState.RUNNING))


def _force_local_skills_on() -> _BT:
    """Force all HeroAI skill slots for this account to True in SharedMemory.

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
    """Enable HeroAI and Dhuum Helper locally and on every other account."""
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


def _enter_underworld_tree() -> _BT:
    """
    Step 1: Leave party (all coordinated accounts) and travel to Guild Hall,
    matching HeroAI "Leave & Travel to GH", then invite.

    Sequence:
      1. For every account in scope (same as HeroAI hotbar): LeaveParty then
         TravelToGuildHall via shared commands.
      2. Wait until every account in SharedMemory is on the same GH map.
      3. Invite all accounts that are in the same map and not yet in the party.
      4. Wait until every account has joined the leader's party.
      5. Enable required follower widgets (HeroAI, Dhuum Helper); remaining
         steps continue to entry point and UW.
    """
    BT = Routines.BT

    def _leave_party_and_travel_gh_like_heroai(node: _BT.Node) -> _BT.NodeState:
        """Mirror HeroAI hotbar: Leave Party then TravelToGuildHall per account."""
        try:
            from HeroAI.commands import HeroAICommands
            from HeroAI.utils import SameMapOrPartyAsAccount
        except Exception as exc:
            ConsoleLog(BOT_NAME, f'[EnterUW] LeavePartyAndTravelGH: HeroAI import failed ({exc}).', Py4GW.Console.MessageType.Error)
            return _BT.NodeState.FAILURE

        from Py4GWCoreLib import Party

        my_email = str(Player.GetAccountEmail() or '').strip()
        if not my_email:
            ConsoleLog(BOT_NAME, '[EnterUW] LeavePartyAndTravelGH: no sender email.', Py4GW.Console.MessageType.Warning)
            return _BT.NodeState.FAILURE

        all_acct = GLOBAL_CACHE.ShMem.GetAllAccountData(include_isolated=True) or []
        if Map.IsExplorable():
            party_id = int(Party.GetPartyID() or 0)
            accounts = [
                a for a in all_acct
                if SameMapOrPartyAsAccount(a)
                and (party_id <= 0 or int(getattr(getattr(a, 'AgentPartyData', None), 'PartyID', 0) or 0) == party_id)
            ]
        else:
            accounts = [a for a in all_acct if SameMapOrPartyAsAccount(a)]

        if not accounts:
            ConsoleLog(BOT_NAME, '[EnterUW] LeavePartyAndTravelGH: no accounts in scope (same map / party).', Py4GW.Console.MessageType.Warning)
            return _BT.NodeState.FAILURE

        try:
            HeroAICommands().LeavePartyAndTravelGH(accounts)
        except Exception as exc:
            ConsoleLog(BOT_NAME, f'[EnterUW] LeavePartyAndTravelGH: failed ({exc}).', Py4GW.Console.MessageType.Error)
            return _BT.NodeState.FAILURE

        emails = [str(getattr(a, 'AccountEmail', '') or '') for a in accounts]
        ConsoleLog(BOT_NAME, f'[EnterUW] LeavePartyAndTravelGH: dispatched to {len(emails)} account(s): {emails}', Py4GW.Console.MessageType.Info)
        return _BT.NodeState.SUCCESS

    def _wait_all_in_gh(node: _BT.Node) -> _BT.NodeState:
        # WaitUntilNode treats bool-False as immediate FAILURE, so we must
        # return NodeState.RUNNING to keep polling while accounts are still traveling.
        if not Map.IsMapReady() or not Map.IsGuildHall():
            return _BT.NodeState.RUNNING
        local_map_id = int(Map.GetMapID() or 0)
        my_email = str(Player.GetAccountEmail() or '')
        missing = []
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
            email = str(getattr(account, 'AccountEmail', '') or '')
            if not email or email == my_email:
                continue
            map_obj = getattr(getattr(account, 'AgentData', None), 'Map', None)
            acc_map_id = int(getattr(account, 'MapID', 0) or getattr(map_obj, 'MapID', 0) or 0)
            if acc_map_id != local_map_id:
                missing.append(email)
        if missing:
            return _BT.NodeState.RUNNING
        ConsoleLog(BOT_NAME, '[EnterUW] WaitAllInGH: all accounts arrived in Guild Hall.', Py4GW.Console.MessageType.Info)
        return _BT.NodeState.SUCCESS

    def _dispatch_invites(node: _BT.Node) -> _BT.NodeState:
        try:
            from HeroAI.commands import HeroAICommands
        except Exception as exc:
            ConsoleLog(BOT_NAME, f'[EnterUW] InviteAll: failed to load HeroAICommands ({exc})', Py4GW.Console.MessageType.Error)
            return _BT.NodeState.FAILURE
        my_email = str(Player.GetAccountEmail() or '')
        all_accounts = GLOBAL_CACHE.ShMem.GetAllAccountData() or []
        targets = [a for a in all_accounts if str(getattr(a, 'AccountEmail', '') or '') != my_email]
        if not targets:
            ConsoleLog(BOT_NAME, '[EnterUW] InviteAll: no follower accounts found.', Py4GW.Console.MessageType.Warning)
            return _BT.NodeState.SUCCESS
        try:
            HeroAICommands().FormParty(targets)
        except Exception as exc:
            ConsoleLog(BOT_NAME, f'[EnterUW] InviteAll: FormParty failed ({exc})', Py4GW.Console.MessageType.Error)
            return _BT.NodeState.FAILURE
        ConsoleLog(BOT_NAME, f'[EnterUW] InviteAll: dispatched FormParty to {len(targets)} account(s).', Py4GW.Console.MessageType.Info)
        return _BT.NodeState.SUCCESS

    party_sync_state: dict = {}

    def _all_in_party() -> _BT.NodeState:
        from Py4GWCoreLib import Party
        leader_map_id   = int(Map.GetMapID() or 0)
        leader_district = int(Map.GetDistrict() or 0)
        leader_party_id = int(Party.GetPartyID() or 0)
        if leader_party_id <= 0:
            return _BT.NodeState.RUNNING
        my_email = str(Player.GetAccountEmail() or '')
        pending = []
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData() or []:
            if str(getattr(account, 'AccountEmail', '') or '') == my_email:
                continue
            try:
                acc_map      = int(account.AgentData.Map.MapID)
                acc_district = int(account.AgentData.Map.District)
                acc_party_id = int(account.AgentPartyData.PartyID)
            except Exception:
                return _BT.NodeState.RUNNING
            if acc_map != leader_map_id or acc_district != leader_district:
                continue
            if acc_party_id != leader_party_id:
                pending.append(str(getattr(account, 'AccountEmail', '') or ''))
        if not pending:
            ConsoleLog(BOT_NAME, f'[EnterUW] All accounts in party (id={leader_party_id}).', Py4GW.Console.MessageType.Info)
            return _BT.NodeState.SUCCESS
        return _BT.NodeState.RUNNING

    def _wait_all_on_leader_map(node: _BT.Node) -> _BT.NodeState:
        if not Map.IsMapReady():
            return _BT.NodeState.RUNNING
        local_map_id = int(Map.GetMapID() or 0)
        my_email = str(Player.GetAccountEmail() or '')
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData(include_isolated=True):
            email = str(getattr(account, 'AccountEmail', '') or '')
            if not email or email == my_email:
                continue
            map_obj = getattr(getattr(account, 'AgentData', None), 'Map', None)
            acc_map_id = int(getattr(account, 'MapID', 0) or getattr(map_obj, 'MapID', 0) or 0)
            if acc_map_id != local_map_id:
                return _BT.NodeState.RUNNING
        ConsoleLog(BOT_NAME, f'[EnterUW] WaitAllAtEntryPoint: all accounts arrived (map={local_map_id}).', Py4GW.Console.MessageType.Info)
        return _BT.NodeState.SUCCESS

    def _use_uw_scroll() -> _BT.NodeState:
        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(UW_SCROLL_MODEL_ID)
        if item_id == 0:
            ConsoleLog(BOT_NAME, '[EnterUW] UseUWScroll: no scroll found in inventory!', Py4GW.Console.MessageType.Warning)
            return _BT.NodeState.FAILURE
        GLOBAL_CACHE.Inventory.UseItem(item_id)
        ConsoleLog(BOT_NAME, '[EnterUW] UseUWScroll: scroll used.', Py4GW.Console.MessageType.Info)
        return _BT.NodeState.SUCCESS

    def _wait_all_in_uw(node: _BT.Node) -> _BT.NodeState:
        if not Map.IsMapReady():
            return _BT.NodeState.RUNNING
        if int(Map.GetMapID() or 0) != UW_MAP_ID:
            return _BT.NodeState.RUNNING
        my_email = str(Player.GetAccountEmail() or '')
        for account in GLOBAL_CACHE.ShMem.GetAllAccountData(include_isolated=True):
            email = str(getattr(account, 'AccountEmail', '') or '')
            if not email or email == my_email:
                continue
            map_obj = getattr(getattr(account, 'AgentData', None), 'Map', None)
            acc_map_id = int(getattr(account, 'MapID', 0) or getattr(map_obj, 'MapID', 0) or 0)
            if acc_map_id != UW_MAP_ID:
                return _BT.NodeState.RUNNING
        ConsoleLog(BOT_NAME, '[EnterUW] WaitForUW: all accounts in Underworld.', Py4GW.Console.MessageType.Info)
        return _BT.NodeState.SUCCESS

    def _log(name: str) -> _BT:
        return _BT(_BT.ActionNode(
            name=f'Log_{name}',
            action_fn=lambda node, n=name: (
                ConsoleLog(BOT_NAME, f'[EnterUW] Starting: {n}', Py4GW.Console.MessageType.Info)
                or _BT.NodeState.SUCCESS
            ),
        ))

    return BT.Composite.Sequence(
        _log('LeavePartyAndTravelGH'),
        _BT(_BT.ActionNode(
            name='LeavePartyAndTravelGH',
            action_fn=_leave_party_and_travel_gh_like_heroai,
            aftercast_ms=750,
        )),
        _log('WaitAllInGuildHall'),
        _BT(_BT.WaitUntilNode(
            name='WaitAllInGuildHall',
            condition_fn=_wait_all_in_gh,
            throttle_interval_ms=1000,
            timeout_ms=120_000,
        )),
        _log('InviteAllAccounts'),
        _BT(_BT.ActionNode(
            name='DispatchPartyInvites',
            action_fn=_dispatch_invites,
            aftercast_ms=750,
        )),
        _log('WaitAllInParty'),
        _BT(_BT.WaitNode(
            name='WaitAllAccountsInParty',
            check_fn=_all_in_party,
            timeout_ms=30_000,
        )),
        _BT(_BT.ActionNode(
            name='EnableRequiredWidgets',
            action_fn=_enable_required_widgets_on_all_accounts,
            aftercast_ms=500,
        )),
        _log('TravelToEntryPoint'),
        _BT(_BT.SubtreeNode(
            name='TravelToEntryPoint',
            subtree_fn=lambda node: BT.Map.TravelToOutpost(
                outpost_id=UW_ENTRYPOINTS.get(
                    EnterSettings.EntryPoint or DEFAULT_UW_ENTRYPOINT_KEY,
                    UW_ENTRYPOINTS[DEFAULT_UW_ENTRYPOINT_KEY],
                )[1],
                timeout=30_000,
            ),
        )),
        _log('WaitAllAtEntryPoint'),
        _BT(_BT.WaitUntilNode(
            name='WaitAllAtEntryPoint',
            condition_fn=_wait_all_on_leader_map,
            throttle_interval_ms=1000,
            timeout_ms=120_000,
        )),
        _log('UseUWScroll'),
        _BT(_BT.ActionNode(
            name='UseUWScroll',
            action_fn=_use_uw_scroll,
            aftercast_ms=500,
        )),
        _log('WaitForUW'),
        _BT(_BT.WaitUntilNode(
            name='WaitForUW',
            condition_fn=_wait_all_in_uw,
            throttle_interval_ms=1000,
            timeout_ms=120_000,
        )),
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
        # Take Restore Monuments quest from same Reaper
                BT.Agents.MoveTargetInteractAndDialog(
            x=-5834, y=12812,
            dialog_id=0x806D01,
        ),
        name='ClearTheChamber',
    )


def _pass_the_mountains_tree() -> _BT:
    BT = Routines.BT
    return BT.Composite.Sequence(
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
        name='PassTheMountains',
    )


def _restore_mountains_tree() -> _BT:
    BT = Routines.BT
    return BT.Composite.Sequence(
        BT.Movement.Move(x=3009,  y=-7876),
        BT.Movement.Move(x=1018,  y=-9456),
        BT.Movement.Move(x=-2419, y=-7770),
        BT.Movement.Move(x=-5391, y=-4426),
        BT.Movement.Move(x=-8337, y=-5342),
        name='RestoreMountains',
    )


def _deamon_assassin_tree() -> _BT:
    BT = Routines.BT

    def _no_slayer_alive(node: _BT.Node) -> _BT.NodeState:
        from Py4GWCoreLib import AgentArray, Agent
        for agent_id in AgentArray.GetEnemyArray():
            if not Agent.IsAlive(agent_id):
                continue
            name = str(Agent.GetNameByID(agent_id) or '').lower()
            if 'slayer' in name:
                return _BT.NodeState.RUNNING
        return _BT.NodeState.SUCCESS

    return BT.Composite.Sequence(
        BT.Agents.MoveTargetInteractAndDialog(
            x=-8337, y=-5342,
            dialog_id=0x806801,
        ),
        BT.Movement.Move(x=-3560, y=-5899),
        _wait_quest_completed(),
        name='DeamonAssassin',
    )


def _restore_planes_tree() -> _BT:
    from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist
    from Py4GWCoreLib import AgentArray, Agent

    def _blacklist_add(node: _BT.Node) -> _BT.NodeState:
        EnemyBlacklist().add_name('banished dream rider')
        return _BT.NodeState.SUCCESS

    def _blacklist_remove(node: _BT.Node) -> _BT.NodeState:
        EnemyBlacklist().remove_name('banished dream rider')
        return _BT.NodeState.SUCCESS

    def _wait_mindblade_spawn(
        x: float, y: float,
        clean_window_ms: int = 6_000,
        move_throttle_ms: int = 2_000,
    ) -> _BT:
        state: dict = {
            'clean_since_ms': None,
            'last_move_ms':   None,
        }

        def _check(node: _BT.Node) -> _BT.NodeState:
            now = int(Utils.GetBaseTimestamp())

            # Check for alive Mindblade enemies
            found_mindblade = any(
                'mindblade' in str(Agent.GetNameByID(aid) or '').lower()
                for aid in AgentArray.GetEnemyArray()
                if Agent.IsAlive(aid)
            )

            if found_mindblade:
                state['clean_since_ms'] = None
                return _BT.NodeState.RUNNING

            # No Mindblade visible — start / continue clean window
            if state['clean_since_ms'] is None:
                state['clean_since_ms'] = now

            in_combat = bool(node.blackboard.get('COMBAT_ACTIVE', False))
            if not in_combat:
                last_move = state['last_move_ms']
                if last_move is None or now - last_move >= move_throttle_ms:
                    Player.Move(x, y)
                    state['last_move_ms'] = now

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

    BT = Routines.BT
    return BT.Composite.Sequence(
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True),
        _force_local_skills_on(),
        _BT(_BT.ActionNode(name='BlacklistDreamRider', action_fn=_blacklist_add)),
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
        BT.Player.Wait(duration_ms=10_000),
        _wait_mindblade_spawn(x=13704, y=-16024),
        BT.Movement.Move(x=11037, y=-17988),
        _wait_mindblade_spawn(x=11037, y=-17988),
        name='RestorePlanes',
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
            if dist > hold_radius and not node.blackboard.get('COMBAT_ACTIVE', False):
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
    from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist
    EnemyBlacklist().add_name('banished dream rider')


def _clear_follower_flags() -> _BT:
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


def _four_horsemen_tree() -> _BT:
    BT = Routines.BT

    def _set_follower_flags(x: float, y: float) -> _BT:
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
        BT.Movement.Move(x=13598, y=-11526),
        _set_follower_flags(x=13598, y=-11526),
        BT.Agents.MoveTargetInteractAndDialog(
            x=11337, y=-17962,
            dialog_id=0x806A01,
        ),
        BT.Player.Wait(duration_ms=32_000),
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
    from Py4GWCoreLib import AgentArray, Agent

    def _blacklist_add(node: _BT.Node) -> _BT.NodeState:
        from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist
        EnemyBlacklist().add_name('obsidian guardian')
        return _BT.NodeState.SUCCESS

    def _queen_dead(node: _BT.Node) -> _BT.NodeState:
        for aid in AgentArray.GetEnemyArray():
            if not Agent.IsAlive(aid):
                continue
            if 'terrorweb queen' in str(Agent.GetNameByID(aid) or '').lower():
                return _BT.NodeState.RUNNING
        return _BT.NodeState.SUCCESS

    return BT.Composite.Sequence(
        bot.Config.MultiboxAggressiveTree(auto_loot=True, pause_on_danger=True),
        _force_local_skills_on(),
        _BT(_BT.ActionNode(name='BlacklistObsidianBehemoth', action_fn=_blacklist_add)),
        BT.Agents.MoveTargetInteractAndDialog(
            x=-6957, y=-19478,
            dialog_id=0x806B01,
        ),
        BT.Movement.Move(x=-12432, y=-15874),
        _BT(_BT.WaitUntilNode(
            name='WaitTerrorwebQueenDead',
            condition_fn=_queen_dead,
            throttle_interval_ms=1000,
            timeout_ms=300_000,
        )),
        BT.Movement.Move(x=-6957, y=-19478),
        BT.Agents.MoveTargetInteractAndDialog(
            x=-6957, y=-19478,
            dialog_id=0x8B,
        ),
        name='TerrorwebQueen',
    )


def _restore_pit_tree() -> _BT:
    BT = Routines.BT

    def _blacklist_add(node: _BT.Node) -> _BT.NodeState:
        from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist
        EnemyBlacklist().add_name('chained soul')
        return _BT.NodeState.SUCCESS

    return BT.Composite.Sequence(
        _BT(_BT.ActionNode(name='BlacklistChainedSoul', action_fn=_blacklist_add)),
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


def _unblacklist_chained_soul(node: _BT.Node) -> _BT.NodeState:
    from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist
    EnemyBlacklist().remove_name('chained soul')
    return _BT.NodeState.SUCCESS


def _blacklist_chained_soul(node: _BT.Node) -> _BT.NodeState:
    from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist
    EnemyBlacklist().add_name('chained soul')
    return _BT.NodeState.SUCCESS


def _imprisoned_spirits_tree() -> _BT:
    import time as _time
    BT = Routines.BT

    LEFT_POINTS  = [(13849, 6602), (13876, 6752), (13985, 6840), (13598, 6779), (13845, 6489)]
    RIGHT_POINTS = [(12871, 2512), (12640, 2485), (12402, 2472), (12137, 2444), (12150, 2139), (12239, 2324)]

    _is_timer: list[float] = [0.0]

    def _start_timer(node: _BT.Node) -> _BT.NodeState:
        _is_timer[0] = _time.monotonic()
        return _BT.NodeState.SUCCESS

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
        BT.Movement.Move(x=13010, y=4452),
        _BT(_BT.ActionNode(name='FlagTeams', action_fn=_flag_teams)),
        BT.Agents.MoveTargetInteractAndDialog(
            x=8679, y=6235,
            dialog_id=0x806901,
        ),
        _BT(_BT.ActionNode(name='StartISTimer', action_fn=_start_timer)),
        BT.Movement.Move(x=13924, y=6914),
        _BT(_BT.WaitUntilNode(
            name='WaitISTimer38s',
            condition_fn=lambda: _time.monotonic() - _is_timer[0] >= 38.0,
            timeout_ms=120_000,
        )),
        _clear_follower_flags(),
        BT.Movement.Move(x=12497, y=2022),
        _BT(_BT.WaitUntilNode(
            name='WaitISTimer90s',
            condition_fn=lambda: _time.monotonic() - _is_timer[0] >= 90.0,
            timeout_ms=180_000,
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


# How many consecutive ticks IsPartyWiped() must be True before recovery activates.
# Kept high to avoid false positives from brief death windows in combat.
_WIPE_CONFIRM_TICKS = 60  # ~3 seconds at 20 fps

# During these steps the bot must always be in an explorable area.
# If the map is ready but NOT explorable while in one of these steps → wipe.
_UW_EXPLORABLE_STEPS: frozenset[str] = frozenset({
    'Clear the Chamber', 'Pass the Mountains', 'Restore Mountains',
    'Deamon Assassin', 'Restore Planes', 'The Four Horsemen',
    'Restore Pools', 'Terrorweb Queen', 'Restore Pit',
    'Imprisoned Spirits', 'Restore Vale', 'Wrathfull Spirits',
    'Unwanted Guests', 'Restore Wastes', 'Servants of Grenth', 'Dhuum',
})


def _build_uw_wipe_recovery_tree() -> _BT:
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
    ('Restore Vale',        lambda: _placeholder('Restore Vale')),
    ('Wrathfull Spirits',   lambda: _placeholder('Wrathfull Spirits')),
    ('Unwanted Guests',     lambda: _placeholder('Unwanted Guests')),
    ('Restore Wastes',      lambda: _placeholder('Restore Wastes')),
    ('Servants of Grenth',  lambda: _placeholder('Servants of Grenth')),
    ('Dhuum',               lambda: _placeholder('Dhuum')),
])

# Replace the default wipe recovery (which restarts from the current step)
# with one that always restarts from 'Enter Underworld'.
_wipe_svc = 'PartyWipeRecoveryService'
for _i, (_svc_name, _) in enumerate(bot._service_steps):
    if _svc_name == _wipe_svc:
        bot._service_steps[_i] = (_wipe_svc, _build_uw_wipe_recovery_tree)
        bot._service_trees[_i] = (_wipe_svc, bot._coerce_runtime_tree(_build_uw_wipe_recovery_tree))
        bot._rebuild_root_tree()
        break

# ── COMBAT_ACTIVE tightening ───────────────────────────────────────────────
# The SharedMemory InAggro field can scan up to Spellcast range (~5000 units)
# when any party member is in aggro AND the leader was recently in aggro
# (stay-alert window = 750 ms).  In Underworld, followers are always fighting,
# so this feedback loop keeps COMBAT_ACTIVE=True even when the leader is far
# from every enemy, which freezes BT.Movement.Move (pause_on_combat=True).
#
# Fix: monkey-patch _tick_planner so that, just before the planner tree ticks
# and its Move nodes read COMBAT_ACTIVE, we replace any True value from the
# large-range SharedMemory scan with a live radius scan (default ≈ Earshot).
# HeroAI's own combat logic is untouched; only the planner pause is affected.
_PAUSE_ON_DANGER_RANGE_DEFAULT: float = 1020.0
_PAUSE_ON_DANGER_RANGE_PASS_MOUNTAINS: float = 400.0

_orig_tick_planner = bot._tick_planner


def _in_aggro_excluding_blacklist(aggro_area: float = 1020.0) -> bool:
    """Live radius scan that ignores blacklisted enemies."""
    from Py4GWCoreLib.AgentArray import AgentArray
    from Py4GWCoreLib.Agent import Agent
    from Py4GWCoreLib.Player import Player as _Player
    from Py4GWCoreLib.EnemyBlacklist import EnemyBlacklist

    bl = EnemyBlacklist()
    player_id = _Player.GetAgentID()
    player_pos = _Player.GetXY()
    if not player_pos:
        return False

    enemy_array = AgentArray.GetEnemyArray()
    if not enemy_array:
        return False

    px, py = player_pos
    radius_sq = aggro_area * aggro_area
    for agent_id in enemy_array:
        if agent_id == player_id:
            continue
        if not Agent.IsAlive(agent_id):
            continue
        if bl.is_blacklisted(agent_id):
            continue
        pos = Agent.GetXY(agent_id)
        if not pos:
            continue
        dx, dy = px - pos[0], py - pos[1]
        if dx * dx + dy * dy <= radius_sq:
            return True
    return False


def _planner_pause_on_danger_range(bb: dict) -> float:
    step = str(bb.get('current_step_name', '') or '')
    if step == 'Pass the Mountains':
        return _PAUSE_ON_DANGER_RANGE_PASS_MOUNTAINS
    return _PAUSE_ON_DANGER_RANGE_DEFAULT


def _tight_combat_active_planner_tick(node):  # type: ignore[override]
    bb = node.blackboard
    if bb.get('COMBAT_ACTIVE', False):
        r = _planner_pause_on_danger_range(bb)
        bb['COMBAT_ACTIVE'] = _in_aggro_excluding_blacklist(r)
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

    _draw_armor_edit_window()

    if Routines.Checks.Map.MapValid():
        bot.tick()

    bot.UI.draw_window(
        icon_path=os.path.join(Py4GW.Console.get_projects_path(), MODULE_ICON),
        main_child_dimensions=(350, 570),
        additional_ui=_draw_main_additional_ui,
        extra_tabs=[('Run Log', _draw_run_log)],
    )


if __name__ == '__main__':
    main()
