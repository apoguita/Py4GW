# region Imports

from __future__ import annotations

from collections.abc import Callable
import os
import time

import Py4GW
from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib import GLOBAL_CACHE, IniHandler, Player, SharedCommandType
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.enums_src.Player_enums import PlayerStatus
from Py4GWCoreLib.routines_src.behaviourtrees_src.constants.lists import CONSET_UPKEEPS, CONSUMABLE_UPKEEPS as ALL_CONSUMABLE_UPKEEPS
from Py4GWCoreLib.routines_src.behaviourtrees_src.items import BTItems
from Sources.ApoSource.ApoBottingLib import wrappers as BT
from Widgets.System.Messaging import get_inventory_count, reset_inventory_count


# endregion


# region Script metadata

MODULE_NAME = "Shards of Orr BT"
INI_PATH = "Widgets/Automation/Bots/Missions/Dungeons/Shards of Orr BT"
INI_FILENAME = "Shards_of_Orr_BT.ini"


# endregion


# region Game identifiers

# Maps
VLOXS_FALL = 624
ARBOR_BAY = 485
SOO_LEVEL_1 = 581
SOO_LEVEL_2 = 582
SOO_LEVEL_3 = 583

# Quest / dialogs
LOST_SOULS_QUEST_ID = 0x324
DWARVEN_BLESSING_DIALOG = 0x84
SHANDRA_TAKE_DIALOG = 0x832401
SHANDRA_REWARD_DIALOG = 0x832407

# Consumables
# Conset model IDs.
ESSENCE_OF_CELERITY = 24859
GRAIL_OF_MIGHT = 24860
ARMOR_OF_SALVATION = 24861

# Summoning stones already used by the original SoO script.
SUMMON_MODEL_IDS = (30209, 37810, 31155)

# Standard personal consumables provided by ApoBottingLib.
# The conset IDs are excluded because they have their own settings.
PCON_UPKEEPS = tuple(
    int(model_id)
    for model_id in ALL_CONSUMABLE_UPKEEPS
    if int(model_id) not in CONSET_UPKEEPS
)

CONSET_RESTOCK_ITEMS: tuple[tuple[int, int], ...] = tuple(
    (model_id, 10) for model_id in CONSET_UPKEEPS
)
PCON_RESTOCK_ITEMS: tuple[tuple[int, int], ...] = tuple(
    (model_id, 10) for model_id in PCON_UPKEEPS
)

SUMMON_RESTOCK_ITEMS: tuple[tuple[int, int], ...] = tuple(
    (model_id, 10) for model_id in SUMMON_MODEL_IDS
)

# Final chest drops tracked by the statistics tab.
BDS_MODEL_IDS = tuple(range(1987, 2008))
BDS_MODEL_ID_MIN = BDS_MODEL_IDS[0]
BDS_MODEL_ID_MAX = BDS_MODEL_IDS[-1]
GB_MODEL_ID = 2474

_BDS_ICON_PATH = os.path.join(
    Py4GW.Console.get_projects_path(),
    "Textures", 
    "Module_Icons",
    "BDS.png",
)


# endregion


# region Settings state

_SETTINGS_SECTION = "Settings"
_STATS_SECTION = "Statistics"
_BDS_DROPS_SECTION = "BDS Drops"
_BDS_SNAPSHOT_SECTION = "BDS Snapshot"
_BDS_RUN_SECTION = "BDS Run"
_GB_DROPS_SECTION = "GB Drops"
_GB_SNAPSHOT_SECTION = "GB Snapshot"
_GB_RUN_SECTION = "GB Run"
_CHAR_NAMES_SECTION = "Character Names"

_INVENTORY_QUERY_POLL_MS = 200
_INVENTORY_QUERY_TIMEOUT_MS = 10_000

_settings_path = os.path.join(
    Py4GW.Console.get_projects_path(),
    "Widgets",
    "Config",
    "Shards_of_Orr_BT.ini",
)
os.makedirs(os.path.dirname(_settings_path), exist_ok=True)
_settings_ini = IniHandler(_settings_path)
_settings_loaded = False

_use_hard_mode = True
_restock_conset = True
_activate_conset = True
_restock_pcons = True
_activate_pcons = True
_use_summoning_stone = True
_runtime_consumables_enabled = True

# Persistent statistics.
_statistics_loaded = False
_total_runs = 0
_total_run_time = 0.0
_fastest_run = float("inf")
_slowest_run = 0.0
_l1_total_time = 0.0
_l1_fastest = float("inf")
_l1_slowest = 0.0
_l2_total_time = 0.0
_l2_fastest = float("inf")
_l2_slowest = 0.0
_l3_total_time = 0.0
_l3_fastest = float("inf")
_l3_slowest = 0.0
_bds_drops: dict[str, int] = {}
_gb_drops: dict[str, int] = {}
_char_names: dict[str, str] = {}

# Session-only statistics.
_session_runs = 0
_session_bds: dict[str, int] = {}
_session_gb: dict[str, int] = {}
_scramble_accounts = False

# Active and most recently completed timings.
_t_run_start = 0.0
_t_l2_start = 0.0
_t_l3_start = 0.0
_current_run_time = 0.0
_current_l1_time = 0.0
_current_l2_time = 0.0
_current_l3_time = 0.0


# endregion


# region Routes and coordinates

# Coordinates
VLOXS_EXIT = Vec2f(15505.38, 12460.59)
ARBOR_BLESSING_NPC = Vec2f(16327.00, 11607.00)
SHANDRA_APPROACH = Vec2f(12056.00, -17882.00)

ARBOR_TO_SHANDRA_PATH = [
    Vec2f(13455.43, 10678.00),
    Vec2f(9850.00, 5025.00),
    Vec2f(11207.11, 1872.32),
    Vec2f(10452.02, 178.50),
    Vec2f(10782.86, -3321.00),
    Vec2f(8360.94, -6550.00),
    Vec2f(10382.85, -12342.00),
    Vec2f(10080.30, -13995.00),
    Vec2f(10667.00, -16116.00),
    Vec2f(10747.49, -17546.00),
    Vec2f(11156.00, -17802.00),
]

LEVEL1_EXIT_TO_ARBOR = Vec2f(-15650.0, 8900.0)

SOO_ENTRANCE_PATH = [
    Vec2f(11177.00, -17683.00),
    Vec2f(10218.00, -18864.00),
    Vec2f(9519.00, -19968.00),
    Vec2f(9240.07, -20260.95),
]

L1_PATH = [
    Vec2f(3720.16, 15370.78),
    Vec2f(6740.06, 11039.32),
    Vec2f(15879, 11171),
    Vec2f(16026.25, 16957.26),
    Vec2f(14255.37, 6189.60)
]

L1_PATH_AFTER_DOOR = [
    Vec2f(17442.40, 2577.83),
    Vec2f(20181.6, 1203.7),
    Vec2f(20400.5, 1300.0),
]

# Level 2 routes / torch mechanics
TORCH_MODEL_IDS = (22341, 22342)
TORCH_BUFF_ID = 2545

L2_BLESSING_NPC = Vec2f(-14076.0, -19457.0)


L2_TORCH_CHEST = Vec2f(-14709.0, -16548.0)
L2_FIRST_TORCH_DROP_POINT_PATH = [
    Vec2f(-11002.0, -17001.0),
]
L2_RETURN_TO_FIRST_TORCH_PATH = [
    Vec2f(-9259.0, -17322.0),
    Vec2f(-9971.23, -17633.08),

]
L2_BRAZIER_PART1 = [
    (-11303.00, -14596.00),
    (-11019.00, -11550.00),
    (-9028.00, -9021.00),
    (-6805.00, -11511.00),
    (-8984.00, -13842.00),
]
L2_CLEANING_PATH = [
    Vec2f(-9011.27, -11536.79),
]
L2_TO_ROOM2_DROP = (Vec2f(-10514.69, -9542.61), Vec2f(-11061.1, -7578.5))
L2_RETURN_TO_ROOM2_TORCH_PATH = [
    Vec2f(-10958.2, -4529.5),
    Vec2f(-11690.64, -3802.55),

]
L2_ROOM2_PATH = [
    Vec2f(-8066.1, -4222.4),
    Vec2f(-7058.8, -4191.0),
]

L2_BRAZIER_PART2 = [
    (-3717.00, -4254.00),
    (-8251.00, -3240.00),
    (-8278.0, -1670.0),
]
L2_AFTER_PART2_POSITION = Vec2f(-5009.49, -2542.30)
L2_PATH_TO_LOCK = [Vec2f(-7063, -2017),Vec2f(-16335.1, -9004.5),(-18700.0, -9171.0)
]
L2_DUNGEON_LOCK = Vec2f(-18725.0, -9171.0)
L2_EXIT_PATH = [
    Vec2f(-18610.0, -8636.0),
    Vec2f(-19254, -8256),
]

# Level 3 routes
L3_ENTRY_BLESSING = Vec2f(17544.0, 18810.0)
L3_MAIN_PATH = [
    Vec2f(16325.98, 15981.14),
    Vec2f(14511, 19206),
    Vec2f(8539, 17072),
    Vec2f(3547, 8795),
    Vec2f(4813.8,10340.7)
]

L3_PATH_TO_TORCH = [
    Vec2f(-4723.0,6703.0), Vec2f(-1280.0,7880.0),
    Vec2f(3089.73,8511.0), Vec2f(4963.0,9974.0),
    Vec2f(9918.64,19108.0), Vec2f(14709.0,19526.0),
    Vec2f(16111.0,17556.0),
]
L3_TORCH_CHEST = Vec2f(16111.0, 17556.0)
L3_BRAZIERS = [
    (15692.0,17111.0), (12969.0,19842.0), (8236.0,16950.0),
    (5549.0,9920.0), (-536.0,6109.0), (-3814.0,5599.0),
    (-4959.0,7558.0), (-7532.0,4536.0), (-10984.0,486.0),
    (-12621.0,2948.0),
]
L3_BOSS_DOOR = Vec2f(-9252.32, 6396.40)
L3_FENDI_PATH = [
    Vec2f(-8871.19,6152.95),Vec2f(-9988, 7652), Vec2f(-12712.36, 13502.19),Vec2f(-13893.67, 14349.77),Vec2f(-15606.06, 15287.51),
]
FENDI_CHEST_POSITION = (-15800.98, 16901.23)
FENDI_CHEST_GADGET_ID = 8934

initialized = False
ini_key = ""
botting_tree: BottingTree | None = None

# endregion


# region Run config


def _load_settings() -> None:
    global _settings_loaded
    global _use_hard_mode, _restock_conset, _activate_conset
    global _restock_pcons, _activate_pcons, _use_summoning_stone

    if _settings_loaded:
        _load_statistics()
        return

    _use_hard_mode = _settings_ini.read_bool(_SETTINGS_SECTION, "HardMode", True)
    _restock_conset = _settings_ini.read_bool(_SETTINGS_SECTION, "RestockConset", True)
    _activate_conset = _settings_ini.read_bool(_SETTINGS_SECTION, "ActivateConset", True)
    _restock_pcons = _settings_ini.read_bool(_SETTINGS_SECTION, "RestockPcons", True)
    _activate_pcons = _settings_ini.read_bool(_SETTINGS_SECTION, "ActivatePcons", True)
    _use_summoning_stone = _settings_ini.read_bool(_SETTINGS_SECTION, "UseSummoningStone", True)
    _settings_loaded = True
    _load_statistics()


def _save_settings() -> None:
    _settings_ini.write_key(_SETTINGS_SECTION, "HardMode", str(bool(_use_hard_mode)))
    _settings_ini.write_key(_SETTINGS_SECTION, "RestockConset", str(bool(_restock_conset)))
    _settings_ini.write_key(_SETTINGS_SECTION, "ActivateConset", str(bool(_activate_conset)))
    _settings_ini.write_key(_SETTINGS_SECTION, "RestockPcons", str(bool(_restock_pcons)))
    _settings_ini.write_key(_SETTINGS_SECTION, "ActivatePcons", str(bool(_activate_pcons)))
    _settings_ini.write_key(_SETTINGS_SECTION, "UseSummoningStone", str(bool(_use_summoning_stone)))


def _load_statistics() -> None:
    global _statistics_loaded
    global _total_runs, _total_run_time, _fastest_run, _slowest_run
    global _l1_total_time, _l1_fastest, _l1_slowest
    global _l2_total_time, _l2_fastest, _l2_slowest
    global _l3_total_time, _l3_fastest, _l3_slowest

    if _statistics_loaded:
        return

    section = _STATS_SECTION
    _total_runs = _settings_ini.read_int(section, "total_runs", 0)
    _total_run_time = _settings_ini.read_float(section, "total_run_time", 0.0)

    fastest = _settings_ini.read_float(section, "fastest_run", 0.0)
    _fastest_run = float("inf") if fastest <= 0.0 else fastest
    _slowest_run = _settings_ini.read_float(section, "slowest_run", 0.0)

    _l1_total_time = _settings_ini.read_float(section, "l1_total_time", 0.0)
    fastest = _settings_ini.read_float(section, "l1_fastest", 0.0)
    _l1_fastest = float("inf") if fastest <= 0.0 else fastest
    _l1_slowest = _settings_ini.read_float(section, "l1_slowest", 0.0)

    _l2_total_time = _settings_ini.read_float(section, "l2_total_time", 0.0)
    fastest = _settings_ini.read_float(section, "l2_fastest", 0.0)
    _l2_fastest = float("inf") if fastest <= 0.0 else fastest
    _l2_slowest = _settings_ini.read_float(section, "l2_slowest", 0.0)

    _l3_total_time = _settings_ini.read_float(section, "l3_total_time", 0.0)
    fastest = _settings_ini.read_float(section, "l3_fastest", 0.0)
    _l3_fastest = float("inf") if fastest <= 0.0 else fastest
    _l3_slowest = _settings_ini.read_float(section, "l3_slowest", 0.0)

    for key in _settings_ini.list_keys(_BDS_DROPS_SECTION):
        _bds_drops[key] = _settings_ini.read_int(_BDS_DROPS_SECTION, key, 0)

    for key in _settings_ini.list_keys(_GB_DROPS_SECTION):
        _gb_drops[key] = _settings_ini.read_int(_GB_DROPS_SECTION, key, 0)

    for seed_section in (
        _BDS_SNAPSHOT_SECTION,
        _BDS_RUN_SECTION,
        _GB_SNAPSHOT_SECTION,
        _GB_RUN_SECTION,
    ):
        for key in _settings_ini.list_keys(seed_section):
            _bds_drops.setdefault(key, 0)
            _gb_drops.setdefault(key, 0)

    for key in _settings_ini.list_keys(_CHAR_NAMES_SECTION):
        name = str(
            _settings_ini.read_key(_CHAR_NAMES_SECTION, key, "") or ""
        ).strip()
        if name:
            _char_names[key] = name

    _statistics_loaded = True


def _save_statistics() -> None:
    section = _STATS_SECTION
    _settings_ini.write_key(section, "total_runs", str(_total_runs))
    _settings_ini.write_key(section, "total_run_time", str(_total_run_time))
    _settings_ini.write_key(
        section,
        "fastest_run",
        str(0.0 if _fastest_run == float("inf") else _fastest_run),
    )
    _settings_ini.write_key(section, "slowest_run", str(_slowest_run))

    for floor, total, fastest, slowest in (
        ("l1", _l1_total_time, _l1_fastest, _l1_slowest),
        ("l2", _l2_total_time, _l2_fastest, _l2_slowest),
        ("l3", _l3_total_time, _l3_fastest, _l3_slowest),
    ):
        _settings_ini.write_key(section, f"{floor}_total_time", str(total))
        _settings_ini.write_key(
            section,
            f"{floor}_fastest",
            str(0.0 if fastest == float("inf") else fastest),
        )
        _settings_ini.write_key(section, f"{floor}_slowest", str(slowest))

    for key, total in _bds_drops.items():
        _settings_ini.write_key(_BDS_DROPS_SECTION, key, str(total))

    for key, total in _gb_drops.items():
        _settings_ini.write_key(_GB_DROPS_SECTION, key, str(total))

    for key, name in _char_names.items():
        _settings_ini.write_key(_CHAR_NAMES_SECTION, key, name)


def _enabled_consumable_upkeeps() -> tuple[int, ...]:
    """
    Return the consumables that must be continuously maintained.

    Summoning stones are excluded because they are one-shot items and must not
    be handled by ConsumableService.
    """
    enabled: list[int] = []

    if _activate_conset:
        enabled.extend(CONSET_UPKEEPS)

    if _activate_pcons:
        enabled.extend(PCON_UPKEEPS)

    return tuple(
        dict.fromkeys(
            int(model_id)
            for model_id in enabled
        )
    )


def _configure_runtime_upkeeps(
    *,
    consumables_enabled: bool | None = None,
) -> None:
    global _runtime_consumables_enabled

    if consumables_enabled is not None:
        _runtime_consumables_enabled = bool(consumables_enabled)

    if botting_tree is None:
        return

    botting_tree.Config.ConfigureUpkeep(
        looting_enabled=True,
        resurrection_scroll=True,
        auto_inventory_handler_enabled=True,
        activate_widget_list=(
            "LootManager",
            "Return to outpost on defeat",
        ),
        consumable_upkeeps=(
            _enabled_consumable_upkeeps()
            if _runtime_consumables_enabled
            else ()
        ),
        heroai_state_logging=False,
        enable_party_wipe_recovery=True
    )


def _runtime_consumable_upkeep_node(
    enabled: bool,
) -> BehaviorTree:
    """Enable or suspend conset and pcon upkeep at runtime."""

    def _apply(
        _node: BehaviorTree.Node,
    ) -> BehaviorTree.NodeState:
        if botting_tree is None:
            return BehaviorTree.NodeState.FAILURE

        if _runtime_consumables_enabled != bool(enabled):
            _configure_runtime_upkeeps(
                consumables_enabled=enabled,
            )
            Py4GW.Console.Log(
                MODULE_NAME,
                (
                    "Consumable upkeep resumed for the dungeon run."
                    if enabled
                    else (
                        "Consumable upkeep suspended during the "
                        "end-of-dungeon return sequence."
                    )
                ),
                Py4GW.Console.MessageType.Info,
            )

        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=(
                "Resume Consumable Upkeep"
                if enabled
                else "Suspend Consumable Upkeep"
            ),
            action_fn=_apply,
            aftercast_ms=0,
        )
    )


def _draw_run_config() -> None:
    import PyImGui

    global _use_hard_mode
    global _restock_conset, _activate_conset
    global _restock_pcons, _activate_pcons
    global _use_summoning_stone

    _load_settings()

    PyImGui.text("Shards of Orr Run Config")
    PyImGui.separator()

    changed = False
    upkeep_changed = False

    value = PyImGui.checkbox(
        "Hard Mode (HM)",
        _use_hard_mode,
    )
    if value != _use_hard_mode:
        _use_hard_mode = value
        changed = True

    PyImGui.separator()
    PyImGui.text("Conset")

    value = PyImGui.checkbox(
        "Restock conset from storage",
        _restock_conset,
    )
    if value != _restock_conset:
        _restock_conset = value
        changed = True

    value = PyImGui.checkbox(
        "Activate / maintain conset",
        _activate_conset,
    )
    if value != _activate_conset:
        _activate_conset = value
        changed = True
        upkeep_changed = True

    PyImGui.separator()
    PyImGui.text("Personal consumables")

    value = PyImGui.checkbox(
        "Restock pcons from storage",
        _restock_pcons,
    )
    if value != _restock_pcons:
        _restock_pcons = value
        changed = True

    value = PyImGui.checkbox(
        "Activate / maintain pcons",
        _activate_pcons,
    )
    if value != _activate_pcons:
        _activate_pcons = value
        changed = True
        upkeep_changed = True

    PyImGui.separator()
    PyImGui.text("Summoning stones")

    value = PyImGui.checkbox(
        "Use summoning stones",
        _use_summoning_stone,
    )
    if value != _use_summoning_stone:
        _use_summoning_stone = value
        changed = True
        upkeep_changed = True

    if changed:
        _save_settings()

    if upkeep_changed:
        _configure_runtime_upkeeps()


def _runtime_difficulty_node() -> BehaviorTree:
    return BT.Subtree(
        name="Apply Selected Difficulty",
        subtree_fn=lambda _node: BT.SetHardMode(_use_hard_mode, log=True),
    )


def _runtime_restock_node() -> BehaviorTree:
    def _build(
        _node: BehaviorTree.Node,
    ) -> BehaviorTree:
        items: list[tuple[int, int]] = []

        if _restock_conset:
            items.extend(CONSET_RESTOCK_ITEMS)

        if _restock_pcons:
            items.extend(PCON_RESTOCK_ITEMS)

        if _use_summoning_stone:
            items.extend(SUMMON_RESTOCK_ITEMS)

        if not items:
            return BT.Succeeder(
                "RestockDisabled"
            )

        return BT.RestockItemsFromList(
            tuple(items),
            allow_missing=True,
        )

    return BT.Subtree(
        name="Restock Selected Consumables",
        subtree_fn=_build,
    )


# endregion


# region Statistics


def _account_key(email: str) -> str:
    return str(email).replace("@", "_at_").replace(".", "_")


def _display_email(key: str) -> str:
    return str(key).replace("_at_", "@").replace("_", ".")


def _known_account_keys() -> list[str]:
    return sorted(
        set(_bds_drops)
        | set(_gb_drops)
        | set(_session_bds)
        | set(_session_gb)
    )


def _account_label(key: str) -> str:
    if not _scramble_accounts:
        return _char_names.get(key) or _display_email(key)

    keys = _known_account_keys()
    index = keys.index(key) + 1 if key in keys else 0
    return f"Player {index}"


def _shared_accounts() -> list[object]:
    try:
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData(
            sort_results=False,
            include_isolated=True,
        )
    except TypeError:
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
    except Exception:
        accounts = []

    unique: list[object] = []
    seen: set[str] = set()
    for account in accounts or []:
        email = str(getattr(account, "AccountEmail", "") or "").strip()
        if not email or email in seen:
            continue
        seen.add(email)
        unique.append(account)
    return unique


def _refresh_character_names() -> bool:
    changed = False

    local_email = str(Player.GetAccountEmail() or "").strip()
    local_name = str(Player.GetName() or "").strip()
    if local_email and local_name:
        key = _account_key(local_email)
        if _char_names.get(key) != local_name:
            _char_names[key] = local_name
            changed = True

    for account in _shared_accounts():
        email = str(getattr(account, "AccountEmail", "") or "").strip()
        agent_data = getattr(account, "AgentData", None)
        character_name = str(
            getattr(agent_data, "CharacterName", "") or ""
        ).strip()
        if not email or not character_name:
            continue

        key = _account_key(email)
        if _char_names.get(key) != character_name:
            _char_names[key] = character_name
            changed = True

    return changed


def _statistics_action_node(
    name: str,
    action: Callable[[], None],
) -> BehaviorTree:
    def _run(
        _node: BehaviorTree.Node,
    ) -> BehaviorTree.NodeState:
        try:
            action()
        except Exception as exc:
            Py4GW.Console.Log(
                MODULE_NAME,
                f"[Statistics] {name} failed: {exc}",
                Py4GW.Console.MessageType.Warning,
            )
        return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=name,
            action_fn=_run,
            aftercast_ms=0,
        )
    )


def _mark_run_start_node() -> BehaviorTree:
    def _mark() -> None:
        global _t_run_start, _t_l2_start, _t_l3_start
        global _current_run_time
        global _current_l1_time, _current_l2_time, _current_l3_time

        _t_run_start = time.monotonic()
        _t_l2_start = 0.0
        _t_l3_start = 0.0
        _current_run_time = 0.0
        _current_l1_time = 0.0
        _current_l2_time = 0.0
        _current_l3_time = 0.0

    return _statistics_action_node(
        "Mark Run Start",
        _mark,
    )


def _mark_l2_start_node() -> BehaviorTree:
    def _mark() -> None:
        global _t_l2_start, _current_l1_time

        now = time.monotonic()
        _t_l2_start = now
        _current_l1_time = (
            now - _t_run_start
            if _t_run_start > 0.0
            else 0.0
        )

    return _statistics_action_node(
        "Mark Level 2 Start",
        _mark,
    )


def _mark_l3_start_node() -> BehaviorTree:
    def _mark() -> None:
        global _t_l3_start, _current_l2_time

        now = time.monotonic()
        _t_l3_start = now
        _current_l2_time = (
            now - _t_l2_start
            if _t_l2_start > 0.0
            else 0.0
        )

    return _statistics_action_node(
        "Mark Level 3 Start",
        _mark,
    )


def _record_run_end_node() -> BehaviorTree:
    def _record() -> None:
        global _total_runs, _session_runs
        global _total_run_time, _fastest_run, _slowest_run
        global _l1_total_time, _l1_fastest, _l1_slowest
        global _l2_total_time, _l2_fastest, _l2_slowest
        global _l3_total_time, _l3_fastest, _l3_slowest
        global _current_run_time, _current_l1_time
        global _current_l2_time, _current_l3_time
        global _t_run_start, _t_l2_start, _t_l3_start

        now = time.monotonic()
        timings_valid = (
            _t_run_start > 0.0
            and _t_l2_start > _t_run_start
            and _t_l3_start > _t_l2_start
        )

        if timings_valid:
            run_time = now - _t_run_start
            l1_time = _t_l2_start - _t_run_start
            l2_time = _t_l3_start - _t_l2_start
            l3_time = now - _t_l3_start

            _current_run_time = run_time
            _current_l1_time = l1_time
            _current_l2_time = l2_time
            _current_l3_time = l3_time

            _total_run_time += run_time
            _fastest_run = min(_fastest_run, run_time)
            _slowest_run = max(_slowest_run, run_time)

            _l1_total_time += l1_time
            _l1_fastest = min(_l1_fastest, l1_time)
            _l1_slowest = max(_l1_slowest, l1_time)

            _l2_total_time += l2_time
            _l2_fastest = min(_l2_fastest, l2_time)
            _l2_slowest = max(_l2_slowest, l2_time)

            _l3_total_time += l3_time
            _l3_fastest = min(_l3_fastest, l3_time)
            _l3_slowest = max(_l3_slowest, l3_time)

            Py4GW.Console.Log(
                MODULE_NAME,
                (
                    "[Statistics] Run complete - "
                    f"Total {run_time:.0f}s | "
                    f"L1 {l1_time:.0f}s | "
                    f"L2 {l2_time:.0f}s | "
                    f"L3 {l3_time:.0f}s"
                ),
                Py4GW.Console.MessageType.Success,
            )

        _total_runs += 1
        _session_runs += 1
        _t_run_start = 0.0
        _t_l2_start = 0.0
        _t_l3_start = 0.0
        _save_statistics()

    return _statistics_action_node(
        "Record Successful Run",
        _record,
    )


def _accumulate_drop(
    account_key: str,
    count: int,
    all_time: dict[str, int],
    session: dict[str, int],
) -> None:
    all_time.setdefault(account_key, 0)
    if count <= 0:
        return
    all_time[account_key] += int(count)
    session[account_key] = session.get(account_key, 0) + int(count)


def _inventory_count(
    model_id_min: int,
    model_id_max: int,
) -> int:
    return sum(
        int(GLOBAL_CACHE.Inventory.GetModelCount(model_id))
        for model_id in range(
            int(model_id_min),
            int(model_id_max) + 1,
        )
    )


def _inventory_statistics_node(
    *,
    after_chest: bool,
) -> BehaviorTree:
    node_name = (
        "Record Drops After Final Chest"
        if after_chest
        else "Snapshot Inventories At Dungeon Entry"
    )
    state: dict[str, object] = {
        "started": False,
        "local_email": "",
        "account_keys": [],
        "requests": [],
        "request_index": 0,
        "waiting": False,
        "request_started_at": 0.0,
    }

    def _reset() -> None:
        state["started"] = False
        state["local_email"] = ""
        state["account_keys"] = []
        state["requests"] = []
        state["request_index"] = 0
        state["waiting"] = False
        state["request_started_at"] = 0.0

    def _start() -> None:
        _load_statistics()
        _refresh_character_names()

        local_email = str(Player.GetAccountEmail() or "").strip()
        local_key = _account_key(local_email or "local")
        bds_section = (
            _BDS_RUN_SECTION
            if after_chest
            else _BDS_SNAPSHOT_SECTION
        )
        gb_section = (
            _GB_RUN_SECTION
            if after_chest
            else _GB_SNAPSHOT_SECTION
        )

        bds_count = _inventory_count(
            BDS_MODEL_ID_MIN,
            BDS_MODEL_ID_MAX,
        )
        gb_count = _inventory_count(
            GB_MODEL_ID,
            GB_MODEL_ID,
        )
        _settings_ini.write_key(bds_section, local_key, str(bds_count))
        _settings_ini.write_key(gb_section, local_key, str(gb_count))

        account_keys = [local_key]
        requests: list[dict[str, object]] = []
        for account in _shared_accounts():
            email = str(
                getattr(account, "AccountEmail", "") or ""
            ).strip()
            if not email or email == local_email:
                continue

            key = _account_key(email)
            if key not in account_keys:
                account_keys.append(key)

            requests.extend(
                [
                    {
                        "email": email,
                        "key": key,
                        "model_min": BDS_MODEL_ID_MIN,
                        "model_max": BDS_MODEL_ID_MAX,
                        "section": bds_section,
                        "label": "BDS",
                    },
                    {
                        "email": email,
                        "key": key,
                        "model_min": GB_MODEL_ID,
                        "model_max": GB_MODEL_ID,
                        "section": gb_section,
                        "label": "Glacial Blades",
                    },
                ]
            )

        for key in account_keys:
            _bds_drops.setdefault(key, 0)
            _gb_drops.setdefault(key, 0)

        state["started"] = True
        state["local_email"] = local_email
        state["account_keys"] = account_keys
        state["requests"] = requests

    def _finish() -> None:
        if not after_chest:
            Py4GW.Console.Log(
                MODULE_NAME,
                (
                    "[Statistics] Dungeon-entry inventory snapshot "
                    f"completed for {len(state['account_keys'])} account(s)."
                ),
                Py4GW.Console.MessageType.Info,
            )
            _save_statistics()
            return

        total_bds = 0
        total_gb = 0
        for key in state["account_keys"]:
            account_key = str(key)
            bds_before = _settings_ini.read_int(
                _BDS_SNAPSHOT_SECTION,
                account_key,
                -1,
            )
            bds_after = _settings_ini.read_int(
                _BDS_RUN_SECTION,
                account_key,
                -1,
            )
            bds_delta = (
                max(0, bds_after - bds_before)
                if bds_before >= 0 and bds_after >= 0
                else 0
            )
            _accumulate_drop(
                account_key,
                bds_delta,
                _bds_drops,
                _session_bds,
            )
            total_bds += bds_delta

            gb_before = _settings_ini.read_int(
                _GB_SNAPSHOT_SECTION,
                account_key,
                -1,
            )
            gb_after = _settings_ini.read_int(
                _GB_RUN_SECTION,
                account_key,
                -1,
            )
            gb_delta = (
                max(0, gb_after - gb_before)
                if gb_before >= 0 and gb_after >= 0
                else 0
            )
            _accumulate_drop(
                account_key,
                gb_delta,
                _gb_drops,
                _session_gb,
            )
            total_gb += gb_delta

        _save_statistics()
        Py4GW.Console.Log(
            MODULE_NAME,
            (
                "[Statistics] Final chest recorded - "
                f"BDS {total_bds} | Glacial Blades {total_gb}"
            ),
            Py4GW.Console.MessageType.Success,
        )

    def _tick(
        node: BehaviorTree.Node,
    ) -> BehaviorTree.NodeState:
        try:
            if bool(
                node.blackboard.get(
                    "USER_INTERRUPT_ACTIVE",
                    False,
                )
            ):
                _reset()
                return BehaviorTree.NodeState.FAILURE

            if not bool(state["started"]):
                _start()

            requests = state["requests"]
            while int(state["request_index"]) < len(requests):
                request_index = int(state["request_index"])
                request = requests[request_index]
                email = str(request["email"])
                model_min = int(request["model_min"])
                model_max = int(request["model_max"])

                if not bool(state["waiting"]):
                    reset_inventory_count(
                        email,
                        model_min,
                        model_max,
                    )
                    _settings_ini.write_key(
                        str(request["section"]),
                        str(request["key"]),
                        str(-1),
                    )
                    GLOBAL_CACHE.ShMem.SendMessage(
                        str(state["local_email"]),
                        email,
                        SharedCommandType.InventoryQuery,
                        (
                            float(model_min),
                            float(model_max),
                            0.0,
                            0.0,
                        ),
                        ("report_inventory_count",),
                    )
                    state["waiting"] = True
                    state["request_started_at"] = time.monotonic()
                    return BehaviorTree.NodeState.RUNNING

                count = int(
                    get_inventory_count(
                        email,
                        model_min,
                        model_max,
                    )
                )
                if count >= 0:
                    _settings_ini.write_key(
                        str(request["section"]),
                        str(request["key"]),
                        str(count),
                    )
                    state["request_index"] = request_index + 1
                    state["waiting"] = False
                    continue

                elapsed_ms = (
                    time.monotonic()
                    - float(state["request_started_at"])
                ) * 1000.0
                if elapsed_ms >= _INVENTORY_QUERY_TIMEOUT_MS:
                    Py4GW.Console.Log(
                        MODULE_NAME,
                        (
                            "[Statistics] Inventory query timed out for "
                            f"{request['label']} on "
                            f"{_account_label(str(request['key']))}."
                        ),
                        Py4GW.Console.MessageType.Warning,
                    )
                    state["request_index"] = request_index + 1
                    state["waiting"] = False
                    continue

                return BehaviorTree.NodeState.RUNNING

            _finish()
            _reset()
            return BehaviorTree.NodeState.SUCCESS
        except Exception as exc:
            Py4GW.Console.Log(
                MODULE_NAME,
                f"[Statistics] {node_name} failed: {exc}",
                Py4GW.Console.MessageType.Warning,
            )
            _reset()
            return BehaviorTree.NodeState.SUCCESS

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=node_name,
            action_fn=_tick,
            aftercast_ms=_INVENTORY_QUERY_POLL_MS,
        )
    )


def _draw_statistics() -> None:
    import PyImGui
    from Py4GWCoreLib import Color, ImGui

    global _scramble_accounts

    _load_statistics()
    if _refresh_character_names():
        _save_statistics()

    gold = Color(255, 210, 80, 255).to_tuple_normalized()
    cyan = Color(80, 210, 255, 255).to_tuple_normalized()
    live = Color(100, 180, 255, 255).to_tuple_normalized()

    def _fmt_time(seconds: float) -> str:
        if seconds <= 0.0 or seconds == float("inf"):
            return "--:--"
        minutes, remaining = divmod(int(seconds), 60)
        return f"{minutes:02d}:{remaining:02d}"

    def _avg_time(total: float) -> str:
        return (
            _fmt_time(total / _total_runs)
            if _total_runs > 0
            else "--:--"
        )

    def _runs_per_drop(runs: int, drops: int) -> str:
        return f"{runs / drops:.1f}" if drops > 0 else "-"

    table_flags = (
        PyImGui.TableFlags.Borders
        | PyImGui.TableFlags.RowBg
        | PyImGui.TableFlags.SizingFixedFit
        | PyImGui.TableFlags.NoHostExtendX
    )
    header_color = 26 | (38 << 8) | (51 << 16) | (255 << 24)
    column_width = 72.0
    row_height = 22.0

    def _header_row(labels: tuple[str, ...]) -> None:
        PyImGui.table_next_row(0, row_height)
        PyImGui.table_set_bg_color(2, header_color, -1)
        for index, label in enumerate(labels):
            PyImGui.table_set_column_index(index)
            PyImGui.text(label)

    if os.path.isfile(_BDS_ICON_PATH):
        ImGui.image(_BDS_ICON_PATH, (24, 24))
        PyImGui.same_line(0, 8)
    PyImGui.text_colored("Shards of Orr Statistics", gold)
    PyImGui.separator()
    PyImGui.spacing()

    _scramble_accounts = PyImGui.checkbox(
        "Hide Account Names",
        _scramble_accounts,
    )

    session_bds = sum(_session_bds.values())
    session_gb = sum(_session_gb.values())
    total_bds = sum(_bds_drops.values())
    total_gb = sum(_gb_drops.values())

    PyImGui.text_colored("Session Overview", cyan)
    if PyImGui.begin_table("##soo_bt_session", 3, table_flags):
        for label in ("Runs", "BDS", "GB"):
            PyImGui.table_setup_column(
                label,
                PyImGui.TableColumnFlags.WidthFixed,
                column_width,
            )
        _header_row(("Runs", "BDS", "GB"))
        PyImGui.table_next_row(0, row_height)
        for index, value in enumerate(
            (_session_runs, session_bds, session_gb)
        ):
            PyImGui.table_set_column_index(index)
            PyImGui.text(str(value))
        PyImGui.end_table()

    PyImGui.spacing()
    PyImGui.text_colored("Total Overview", cyan)
    if PyImGui.begin_table("##soo_bt_all_time", 5, table_flags):
        for label in ("Runs", "BDS", "BDS Avg", "GB", "GB Avg"):
            PyImGui.table_setup_column(
                label,
                PyImGui.TableColumnFlags.WidthFixed,
                column_width,
            )
        _header_row(("Runs", "BDS", "BDS Avg", "GB", "GB Avg"))
        values = (
            str(_total_runs),
            str(total_bds),
            _runs_per_drop(_total_runs, total_bds),
            str(total_gb),
            _runs_per_drop(_total_runs, total_gb),
        )
        PyImGui.table_next_row(0, row_height)
        for index, value in enumerate(values):
            PyImGui.table_set_column_index(index)
            PyImGui.text(value)
        PyImGui.end_table()

    PyImGui.spacing()
    PyImGui.text_colored("Run Timings", cyan)
    if PyImGui.begin_table("##soo_bt_timings", 5, table_flags):
        for label in ("Floor", "Current", "Avg", "Best", "Worst"):
            PyImGui.table_setup_column(
                label,
                PyImGui.TableColumnFlags.WidthFixed,
                column_width,
            )
        _header_row(("Floor", "Current", "Avg", "Best", "Worst"))

        now = time.monotonic()
        run_active = _t_run_start > 0.0
        l1_active = run_active and _t_l2_start <= 0.0
        l2_active = _t_l2_start > 0.0 and _t_l3_start <= 0.0
        l3_active = _t_l3_start > 0.0

        timing_rows = (
            (
                "Overall",
                now - _t_run_start if run_active else _current_run_time,
                run_active,
                _total_run_time,
                _fastest_run,
                _slowest_run,
            ),
            (
                "Floor 1",
                now - _t_run_start if l1_active else _current_l1_time,
                l1_active,
                _l1_total_time,
                _l1_fastest,
                _l1_slowest,
            ),
            (
                "Floor 2",
                now - _t_l2_start if l2_active else _current_l2_time,
                l2_active,
                _l2_total_time,
                _l2_fastest,
                _l2_slowest,
            ),
            (
                "Floor 3",
                now - _t_l3_start if l3_active else _current_l3_time,
                l3_active,
                _l3_total_time,
                _l3_fastest,
                _l3_slowest,
            ),
        )

        for label, current, is_live, total, fastest, slowest in timing_rows:
            PyImGui.table_next_row(0, row_height)
            PyImGui.table_set_column_index(0)
            PyImGui.text(label)
            PyImGui.table_set_column_index(1)
            if is_live:
                PyImGui.text_colored(_fmt_time(current), live)
            else:
                PyImGui.text(_fmt_time(current))
            PyImGui.table_set_column_index(2)
            PyImGui.text(_avg_time(total))
            PyImGui.table_set_column_index(3)
            PyImGui.text(_fmt_time(fastest))
            PyImGui.table_set_column_index(4)
            PyImGui.text(_fmt_time(slowest))

        PyImGui.end_table()

    def _draw_drop_table(
        table_id: str,
        title: str,
        session_values: dict[str, int],
        all_time_values: dict[str, int],
    ) -> None:
        PyImGui.spacing()
        PyImGui.text_colored(title, cyan)
        if not PyImGui.begin_table(table_id, 4, table_flags):
            return

        PyImGui.table_setup_column(
            "Account",
            PyImGui.TableColumnFlags.WidthStretch,
        )
        for label in ("Session", "All Time", "Runs/Drop"):
            PyImGui.table_setup_column(
                label,
                PyImGui.TableColumnFlags.WidthFixed,
                column_width,
            )
        _header_row(("Account", "Session", "All Time", "Avg"))

        keys = sorted(set(session_values) | set(all_time_values))
        session_total = 0
        all_time_total = 0
        for key in keys:
            session_count = session_values.get(key, 0)
            all_time_count = all_time_values.get(key, 0)
            session_total += session_count
            all_time_total += all_time_count

            PyImGui.table_next_row(0, row_height)
            PyImGui.table_set_column_index(0)
            PyImGui.text(_account_label(key))
            PyImGui.table_set_column_index(1)
            PyImGui.text(str(session_count))
            PyImGui.table_set_column_index(2)
            PyImGui.text(str(all_time_count))
            PyImGui.table_set_column_index(3)
            PyImGui.text(
                _runs_per_drop(_total_runs, all_time_count)
            )

        PyImGui.table_next_row(0, row_height)
        PyImGui.table_set_column_index(0)
        PyImGui.text_colored("Total", gold)
        PyImGui.table_set_column_index(1)
        PyImGui.text_colored(str(session_total), gold)
        PyImGui.table_set_column_index(2)
        PyImGui.text_colored(str(all_time_total), gold)
        PyImGui.table_set_column_index(3)
        PyImGui.text_colored(
            _runs_per_drop(_total_runs, all_time_total),
            gold,
        )
        PyImGui.end_table()

    _draw_drop_table(
        "##soo_bt_bds_drops",
        "BDS Drops",
        _session_bds,
        _bds_drops,
    )
    _draw_drop_table(
        "##soo_bt_gb_drops",
        "Glacial Blades Drops",
        _session_gb,
        _gb_drops,
    )


# endregion


# region Helpers
def ResilientVanquishNode(
    steps,
    clear_area_radius: float = Range.Spirit.value,
    pause_on_combat: bool | None = None,
    flag_heroes_to_waypoint: bool = False,
    name: str = "VanquishNode",
    max_attempts: int = 3,
) -> BehaviorTree:
    """Relance localement un VanquishNode en cas de FAILURE."""
    attempt_count = max(1, int(max_attempts))
    attempts: list[BehaviorTree] = []

    for attempt_index in range(attempt_count):
        attempt_number = attempt_index + 1

        vanquish = BT.VanquishNode(
            steps,
            clear_area_radius=clear_area_radius,
            pause_on_combat=pause_on_combat,
            flag_heroes_to_waypoint=flag_heroes_to_waypoint,
            name=f"{name} - Attempt {attempt_number}",
        )

        if attempt_number == 1:
            attempts.append(vanquish)
            continue

        attempts.append(
            BT.Sequence(
                name=f"Retry {name} - Attempt {attempt_number}",
                children=[
                    BT.LogMessage(
                        message=(
                            f"{name} failed, probably because movement was "
                            f"blocked. Retrying locally "
                            f"({attempt_number}/{attempt_count})."
                        ),
                        module_name=MODULE_NAME,
                    ),
                    BT.Wait(2_000),
                    vanquish,
                ],
            )
        )

    return BT.Selector(
        name=f"Resilient {name}",
        children=attempts,
    )

def PickupTorch() -> BehaviorTree:
    return BT.PickupGroundItemByModelID(
        model_ids=TORCH_MODEL_IDS,
        max_distance=10_000.0,
        timeout_ms=45_000,
        allow_unassigned=True,
        interaction_interval_ms=1000,
        aftercast_ms=100,
        log=False,
    )


def UseAvailableSummoningStone() -> BehaviorTree:
    """
    Use the first available summoning stone once.

    Summoning stones are handled as one-shot consumables and are therefore
    kept outside the continuous consumable upkeep service.
    """
    if not _use_summoning_stone:
        return BT.Succeeder(
            "SummoningStoneDisabled",
        )

    return BT.Selector(
        name="Use Available Summoning Stone",
        children=[
            BTItems.UseConsumable(
                int(model_id),
            )
            for model_id in SUMMON_MODEL_IDS
        ]
        + [
            BT.Succeeder(
                "NoSummoningStoneAvailable",
            ),
        ],
    )


def BrazierSequence(
    name: str,
    points: list[tuple[float, float]],
) -> BehaviorTree:
    """
    Activate a sequence of SoO braziers.

    The first brazier is activated normally because the torch flame effect is
    not available before that interaction. Every following movement continuously
    monitors the flame and returns to the previous brazier if it disappears.
    """
    if not points:
        return BT.Succeeder(
            f"{name}Empty",
        )

    children: list[
        BehaviorTree | BehaviorTree.Node
    ] = []

    first_x, first_y = points[0]

    children.append(
        BT.MoveAndInteractWithGadget(
            pos=Vec2f(
                float(first_x),
                float(first_y),
            ),
            gadget_id=None,
            search_distance=300.0,
            interaction_distance=220.0,
            interaction_count=2,
            interaction_interval_ms=250,
            timeout_ms=15_000,
            pause_on_combat=False,
            multi_account=False,
            include_self=True,
            log=True,
        )
    )

    for index in range(
        1,
        len(points),
    ):
        previous_brazier = points[
            index - 1
        ]
        next_brazier = points[
            index
        ]

        children.append(
            MoveBetweenBraziersWithFlameRecovery(
            name=f"{name} {index}/{len(points) - 1}",
            previous_brazier=previous_brazier,
            next_brazier=next_brazier,
            effect_id=TORCH_BUFF_ID,
            interaction_distance=220.0,
            interaction_count=2,
            interaction_interval_ms=250,
            effect_apply_timeout_ms=3000,
            timeout_ms=90000,
            max_recoveries=5,
            log=True,)
        )

    return BT.Sequence(
        name=name,
        children=children,
    )

def MoveBetweenBraziersWithFlameRecovery(
    name: str,
    previous_brazier: tuple[float, float],
    next_brazier: tuple[float, float],
    effect_id: int = TORCH_BUFF_ID,
    interaction_distance: float = 220.0,
    interaction_count: int = 2,
    interaction_interval_ms: int = 250,
    effect_apply_timeout_ms: int = 3_000,
    timeout_ms: int = 90_000,
    max_recoveries: int = 5,
    log: bool = True,
) -> BehaviorTree:
    """
    Move between two braziers while continuously monitoring the torch flame.

    Movement is delegated entirely to the regular BT Move node. If the flame
    disappears while moving to the next brazier, that movement subtree is
    reset, the current movement is cancelled once, and a dedicated BT Move
    subtree returns the player to the previous brazier. The torch is then
    relit before the original movement resumes.
    """
    import time

    from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
    from Py4GWCoreLib.Player import Player

    previous_pos = Vec2f(
        float(previous_brazier[0]),
        float(previous_brazier[1]),
    )
    next_pos = Vec2f(
        float(next_brazier[0]),
        float(next_brazier[1]),
    )

    move_to_next = BT.Move(
        next_pos,
        tolerance=float(interaction_distance),
        pause_on_combat=False,
        log=log,
    )
    move_to_previous = BT.Move(
        previous_pos,
        tolerance=float(interaction_distance),
        pause_on_combat=False,
        log=log,
    )
    relight_previous = BT.MoveAndInteractWithGadget(
        pos=previous_pos,
        gadget_id=None,
        search_distance=300.0,
        interaction_distance=float(interaction_distance),
        interaction_count=max(1, int(interaction_count)),
        interaction_interval_ms=max(0, int(interaction_interval_ms)),
        timeout_ms=15_000,
        pause_on_combat=False,
        multi_account=False,
        include_self=True,
        log=log,
    )
    interact_next = BT.MoveAndInteractWithGadget(
        pos=next_pos,
        gadget_id=None,
        search_distance=300.0,
        interaction_distance=float(interaction_distance),
        interaction_count=max(1, int(interaction_count)),
        interaction_interval_ms=max(0, int(interaction_interval_ms)),
        timeout_ms=15_000,
        pause_on_combat=False,
        multi_account=False,
        include_self=True,
        log=log,
    )

    state = {
        "phase": "move_to_next",
        "started_at": 0.0,
        "phase_started_at": 0.0,
        "recovery_count": 0,
    }

    def _trace(
        message: str,
        message_type=Py4GW.Console.MessageType.Info,
    ) -> None:
        if log:
            Py4GW.Console.Log(
                MODULE_NAME,
                f"[{name}] {message}",
                message_type,
            )

    def _has_active_flame() -> bool:
        try:
            return bool(
                GLOBAL_CACHE.Effects.HasEffect(
                    Player.GetAgentID(),
                    int(effect_id),
                )
            )
        except Exception:
            return False

    def _cancel_current_movement() -> None:
        try:
            player_x, player_y = Player.GetXY()
            Player.Move(
                float(player_x),
                float(player_y),
            )
        except Exception:
            pass

    def _reset_tree(tree: BehaviorTree) -> None:
        try:
            tree.reset()
        except Exception:
            try:
                tree.root.reset()
            except Exception:
                pass

    def _tick_tree(
        tree: BehaviorTree,
        node: BehaviorTree.Node,
    ) -> BehaviorTree.NodeState:
        tree.root.blackboard = node.blackboard
        result = tree.root.tick()

        if isinstance(result, BehaviorTree.NodeState):
            return result
        if result is True:
            return BehaviorTree.NodeState.SUCCESS
        if result is False:
            return BehaviorTree.NodeState.FAILURE
        return BehaviorTree.NodeState.RUNNING

    def _reset_all() -> None:
        _reset_tree(move_to_next)
        _reset_tree(move_to_previous)
        _reset_tree(relight_previous)
        _reset_tree(interact_next)

        state["phase"] = "move_to_next"
        state["started_at"] = 0.0
        state["phase_started_at"] = 0.0
        state["recovery_count"] = 0

    def _begin_recovery(now: float) -> BehaviorTree.NodeState:
        state["recovery_count"] += 1

        if state["recovery_count"] > max(1, int(max_recoveries)):
            _trace(
                (
                    "Torch recovery failed after "
                    f"{max(1, int(max_recoveries))} attempt(s)."
                ),
                Py4GW.Console.MessageType.Warning,
            )
            _reset_all()
            return BehaviorTree.NodeState.FAILURE

        _trace(
            (
                "Torch flame extinguished during movement. "
                "Returning to the previous brazier "
                f"(recovery {state['recovery_count']}/"
                f"{max(1, int(max_recoveries))})."
            ),
            Py4GW.Console.MessageType.Warning,
        )

        _reset_tree(move_to_next)
        _reset_tree(move_to_previous)
        _reset_tree(relight_previous)
        _cancel_current_movement()

        state["phase"] = "move_to_previous"
        state["phase_started_at"] = now
        return BehaviorTree.NodeState.RUNNING

    def _move_with_recovery(
        node: BehaviorTree.Node,
    ) -> BehaviorTree.NodeState:
        now = time.monotonic()

        if state["started_at"] <= 0.0:
            state["started_at"] = now
            state["phase_started_at"] = now
            _trace(
                (
                    "Starting monitored BT movement from "
                    f"{previous_brazier} to {next_brazier}."
                )
            )

        elapsed_ms = (
            now - float(state["started_at"])
        ) * 1000.0

        if elapsed_ms >= max(1, int(timeout_ms)):
            _trace(
                "Timed out while moving between braziers.",
                Py4GW.Console.MessageType.Warning,
            )
            _cancel_current_movement()
            _reset_all()
            return BehaviorTree.NodeState.FAILURE

        if bool(
            node.blackboard.get(
                "USER_INTERRUPT_ACTIVE",
                False,
            )
        ):
            _cancel_current_movement()
            _reset_all()
            return BehaviorTree.NodeState.FAILURE

        phase = str(state["phase"])

        if phase == "move_to_next":
            if not _has_active_flame():
                return _begin_recovery(now)

            result = _tick_tree(move_to_next, node)

            if result == BehaviorTree.NodeState.RUNNING:
                return BehaviorTree.NodeState.RUNNING

            if result == BehaviorTree.NodeState.FAILURE:
                _trace(
                    "Movement to the next brazier failed.",
                    Py4GW.Console.MessageType.Warning,
                )
                _reset_all()
                return BehaviorTree.NodeState.FAILURE

            _reset_tree(move_to_next)
            state["phase"] = "interact_next"
            state["phase_started_at"] = now
            _trace(
                "Reached the next brazier with the torch still active."
            )
            return BehaviorTree.NodeState.RUNNING

        if phase == "interact_next":
            if not _has_active_flame():
                return _begin_recovery(now)

            result = _tick_tree(interact_next, node)

            if result == BehaviorTree.NodeState.RUNNING:
                return BehaviorTree.NodeState.RUNNING

            if result == BehaviorTree.NodeState.FAILURE:
                _trace(
                    "Interaction with the next brazier failed.",
                    Py4GW.Console.MessageType.Warning,
                )
                _reset_all()
                return BehaviorTree.NodeState.FAILURE

            _trace(
                "Next brazier interaction completed.",
                Py4GW.Console.MessageType.Success,
            )
            _reset_all()
            return BehaviorTree.NodeState.SUCCESS

        if phase == "move_to_previous":
            result = _tick_tree(move_to_previous, node)

            if result == BehaviorTree.NodeState.RUNNING:
                return BehaviorTree.NodeState.RUNNING

            if result == BehaviorTree.NodeState.FAILURE:
                _trace(
                    "Movement back to the previous brazier failed.",
                    Py4GW.Console.MessageType.Warning,
                )
                _reset_all()
                return BehaviorTree.NodeState.FAILURE

            _reset_tree(move_to_previous)
            state["phase"] = "relight_previous"
            state["phase_started_at"] = now
            _trace(
                "Reached the previous brazier. Relighting the torch."
            )
            return BehaviorTree.NodeState.RUNNING

        if phase == "relight_previous":
            result = _tick_tree(relight_previous, node)

            if result == BehaviorTree.NodeState.RUNNING:
                return BehaviorTree.NodeState.RUNNING

            if result == BehaviorTree.NodeState.FAILURE:
                _trace(
                    "Interaction with the previous brazier failed.",
                    Py4GW.Console.MessageType.Warning,
                )
                _reset_all()
                return BehaviorTree.NodeState.FAILURE

            _reset_tree(relight_previous)
            state["phase"] = "wait_for_relight"
            state["phase_started_at"] = now
            return BehaviorTree.NodeState.RUNNING

        if phase == "wait_for_relight":
            if _has_active_flame():
                _trace(
                    (
                        "Torch relit successfully. "
                        "Resuming movement to the next brazier."
                    ),
                    Py4GW.Console.MessageType.Success,
                )
                _reset_tree(move_to_next)
                _reset_tree(interact_next)
                state["phase"] = "move_to_next"
                state["phase_started_at"] = now
                return BehaviorTree.NodeState.RUNNING

            elapsed_phase_ms = (
                now - float(state["phase_started_at"])
            ) * 1000.0

            if elapsed_phase_ms < max(
                1,
                int(effect_apply_timeout_ms),
            ):
                return BehaviorTree.NodeState.RUNNING

            _trace(
                (
                    "The torch effect did not return after "
                    "the previous brazier interaction. Retrying."
                ),
                Py4GW.Console.MessageType.Warning,
            )

            _reset_tree(relight_previous)
            state["phase"] = "relight_previous"
            state["phase_started_at"] = now
            return BehaviorTree.NodeState.RUNNING

        _reset_all()
        return BehaviorTree.NodeState.FAILURE

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name=name,
            action_fn=_move_with_recovery,
            aftercast_ms=0,
        )
    )


# endregion


# region Bot initialization


def ensure_botting_tree() -> BottingTree:
    global botting_tree

    _load_settings()
    if botting_tree is None:
        botting_tree = BottingTree.Create(
            MODULE_NAME,
            main_routine=get_execution_steps(),
            routine_name="MultiAccountSequence",
            repeat=True,
            multi_account=True,
            isolation_enabled=True,
            configure_fn=lambda tree: tree.Config.ConfigureUpkeep(
                looting_enabled=True,
                resurrection_scroll=True,
                auto_inventory_handler_enabled=True,
                activate_widget_list=(
                    "LootManager",
                    "Return to outpost on defeat",
                ),
                consumable_upkeeps=_enabled_consumable_upkeeps(),
                heroai_state_logging=False,
            ),
        )

    return botting_tree


def InitializeBot() -> BehaviorTree:
    bot = ensure_botting_tree()
    return BT.Sequence(
        name="Initialize Shards of Orr BT",
        children=[
            bot.Config.Aggressive(
                multi_account=True,
                auto_loot=True,
                resurrection_scroll=True,
            ),
            BT.SetPlayerStatus(PlayerStatus.Offline, log=True),
            BT.LogMessage(message="Shards of Orr BT initialized", module_name=MODULE_NAME),
        ],
    )


# endregion


# region Preparation and dungeon entry


def PreparePartyAndSupplies() -> BehaviorTree:
    already_ready_in_level_1 = BT.Sequence(
        name="Skip Outpost Preparation - Already In Level 1",
        children=[
            BT.IsCurrentMap(
    map_id=SOO_LEVEL_1,
    log=True,
),
            BT.IsQuestState(
                quest_id=LOST_SOULS_QUEST_ID,
                state="active",
                log=True,
            ),
            BT.Succeeder("OutpostPreparationAlreadyDone"),
        ],
    )
    normal_preparation = BT.Sequence(
        name="Prepare Party And Supplies From Vlox",
        map_id_or_name=VLOXS_FALL,
        random_travel=True,
        hard_mode=None,
        children=[
            BT.CreateParty(multibox_invite=True, timeout_ms=30_000, log=True),
            BT.AbandonQuest(
    quest_id=LOST_SOULS_QUEST_ID,
    multi_account=True,
    include_self=True,
    timeout_ms=10_000,
    log=True,
),
            _runtime_difficulty_node(),
            _runtime_restock_node(),
            BT.LogMessage(message="Party formed and selected settings applied", module_name=MODULE_NAME),
        ],
    )
    return BT.Selector(children=[already_ready_in_level_1, normal_preparation], name="Prepare Party And Supplies")


def TravelToShandra() -> BehaviorTree:
    skip_if_already_in_level_1 = BT.Sequence(
        name="Skip Travel To Shandra - Already In Level 1",
        children=[
            BT.IsCurrentMap(map_id=SOO_LEVEL_1, log=True),
            BT.IsQuestState(quest_id=LOST_SOULS_QUEST_ID, state="active", log=True),
            BT.Succeeder("TravelToShandraAlreadyDone"),
        ],
    )
    normal_travel = BT.Sequence(
        name="Travel To Shandra From Vlox",
        children=[
            BT.MoveAndExitMap(VLOXS_EXIT, target_map_id=ARBOR_BAY, log=True),
            BT.WaitUntilOnExplorable(timeout_ms=30_000),
            BT.Wait(2_000),
            BT.MoveAndDialog(ARBOR_BLESSING_NPC, dialog_id=DWARVEN_BLESSING_DIALOG, multi_account=True, log=True),
            BT.Wait(3_000),
            BT.Move(ARBOR_TO_SHANDRA_PATH, pause_on_combat=True, log=True),
            BT.WaitUntilOutOfCombat(timeout_ms=60_000),
            BT.Move(SHANDRA_APPROACH, pause_on_combat=False, log=True),
        ],
    )
    return BT.Selector(children=[skip_if_already_in_level_1, normal_travel], name="Travel To Shandra")


def HandleShandraQuest() -> BehaviorTree:
    already_inside = BT.Sequence(
        name="Skip Shandra Handler - Already In Level 1",
        children=[
            BT.IsCurrentMap(map_id=SOO_LEVEL_1, log=True),
            BT.IsQuestState(quest_id=LOST_SOULS_QUEST_ID, state="active", log=True),
            BT.Succeeder("ShandraHandlerAlreadyDone"),
        ],
    )
    active = BT.Sequence(
        name="Lost Souls Already Active",
        children=[BT.IsQuestState(quest_id=LOST_SOULS_QUEST_ID, state="active", log=True), BT.Succeeder("ContinueWithActiveQuest")],
    )
    completed = BT.Sequence(
        name="Collect And Retake Lost Souls",
        children=[
            BT.IsQuestState(quest_id=LOST_SOULS_QUEST_ID, state="complete", log=True),
            BT.MoveAndDialog(SHANDRA_APPROACH, SHANDRA_REWARD_DIALOG, pause_on_combat=False, multi_account=True, log=True),
            BT.WaitForQuestCleared(LOST_SOULS_QUEST_ID, timeout_ms=15_000),
            BT.MoveAndDialog(SHANDRA_APPROACH, SHANDRA_TAKE_DIALOG, pause_on_combat=False, multi_account=True, log=True),
            BT.WaitForActiveQuest(LOST_SOULS_QUEST_ID, timeout_ms=15_000),
        ],
    )
    missing = BT.Sequence(
        name="Take Lost Souls",
        children=[
            BT.IsQuestState(quest_id=LOST_SOULS_QUEST_ID, state="missing", log=True),
            BT.MoveAndDialog(SHANDRA_APPROACH, SHANDRA_TAKE_DIALOG, pause_on_combat=False, multi_account=True, log=True),
            BT.WaitForActiveQuest(LOST_SOULS_QUEST_ID, timeout_ms=15_000),
        ],
    )
    return BT.Selector(children=[already_inside, active, completed, missing], name="Handle Shandra Quest")


def EnterShardsOfOrr(
    enable_consumables_on_entry: bool = True,
) -> BehaviorTree:
    already_inside = BT.Sequence(
        name="Skip Dungeon Entry - Already In Level 1",
        children=[
            BT.IsCurrentMap(map_id=SOO_LEVEL_1, log=True),
            BT.IsQuestState(quest_id=LOST_SOULS_QUEST_ID, state="active", log=True),
            BT.Succeeder("DungeonEntryAlreadyDone"),
        ],
    )
    normal_entry = BT.Sequence(
        name="Enter Shards of Orr From Arbor Bay",
        children=[
            BT.Move(SOO_ENTRANCE_PATH, pause_on_combat=False, log=True),
            BT.WaitForMapLoad(map_id=SOO_LEVEL_1, timeout_ms=60_000),
            BT.WaitUntilOnExplorable(timeout_ms=30_000),
            BT.Wait(2_000),
        ],
    )
    entry = BT.Selector(
        children=[already_inside, normal_entry],
        name="Enter Shards of Orr",
    )

    if not enable_consumables_on_entry:
        return entry

    return BT.Sequence(
        name="Enter Shards of Orr And Resume Consumables",
        children=[
            entry,
            _runtime_consumable_upkeep_node(True),
        ],
    )


# endregion
# region Dungeon level 1


def Level1_Part1() -> BehaviorTree:
    return BT.Sequence(
        name="Run Shards of Orr Level 1",
        children=[
            _mark_run_start_node(),
            _inventory_statistics_node(after_chest=False),
            UseAvailableSummoningStone(),
            BT.AddModelToLootWhitelist(25410),
            BT.MoveAndDialog(
                Vec2f(-11686.0, 10427.0),
                dialog_id=DWARVEN_BLESSING_DIALOG,
                multi_account=True,
                log=True,
            ),
            ResilientVanquishNode(
                L1_PATH,
                name="Level 1 First Route",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
            ),
            
            BT.MoveAndInteractWithGadget(Vec2f(15100.0, 5443.0),
                pause_on_combat=True,
                log=True,
            ),
            
        ],
    )


# endregion
#region Level 1 - part 2
def Level1_Part2() -> BehaviorTree:
    return BT.Sequence(
        name="Run Shards of Orr Level 1 - Part 2",
        children=[
            ResilientVanquishNode(
                L1_PATH_AFTER_DOOR,
                name="Level 1 Route To Level 2",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
            ),
            BT.WaitForMapLoad(map_id=SOO_LEVEL_2, timeout_ms=60_000),
            BT.WaitUntilOnExplorable(timeout_ms=30_000),
            _mark_l2_start_node(),
            BT.Wait(2_000),
        ],
    )
#endregion


# region Level 2 - part 1


def Level2_Part1() -> BehaviorTree:
    return BT.Sequence(
        name="Run Shards of Orr Level 2",
        children=[
            UseAvailableSummoningStone(),
            BT.AddModelToLootWhitelist(25410),
            BT.MoveAndDialog(
                L2_BLESSING_NPC,
                dialog_id=DWARVEN_BLESSING_DIALOG,
                multi_account=True,
                log=True,
            ),
            BT.ClearEnemiesInArea(
                L2_TORCH_CHEST,
                radius=Range.Compass.value,
            ),
            BT.MoveAndInteractWithGadget(
                L2_TORCH_CHEST,
                pause_on_combat=False,
                log=True,
            ),
            PickupTorch(),
            BT.Move(L2_FIRST_TORCH_DROP_POINT_PATH, pause_on_combat=True, log=True),
            BT.DropBundle(log=True),
            ResilientVanquishNode(
                L2_RETURN_TO_FIRST_TORCH_PATH,
                name="Clear And Return To First Torch",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
            ),
            PickupTorch(),
            BT.Move(Vec2f(-9404.44, -17963.49), pause_on_combat=True, log=True),
            BT.Move(Vec2f(-11303.00, -14596.00), pause_on_combat=True, log=True),
            BrazierSequence("Level 2 Brazier Route 1", L2_BRAZIER_PART1),
            BT.DropBundle(log=True),
        ],
    )
#endregion
# region Level 2 - part 2

def Level2_Part2() -> BehaviorTree:
    return BT.Sequence(
        name="Run Shards of Orr Level 2",
        children=[
            BT.ClearEnemiesInArea(
                L2_CLEANING_PATH,radius=Range.Compass.value,
            ),
            PickupTorch(),
            ResilientVanquishNode(L2_TO_ROOM2_DROP,clear_area_radius=Range.Area.value, pause_on_combat=True),
            BT.DropBundle(log=True),
            ResilientVanquishNode(
                L2_RETURN_TO_ROOM2_TORCH_PATH,
                name="Clear Route Back To Room 2 Torch",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
            ),
            PickupTorch(),
            ResilientVanquishNode(
                L2_ROOM2_PATH,
                name="Clear Level 2 Room 2",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
            ),
            BT.DropBundle(log=True),
            ResilientVanquishNode([Vec2f(-4245.2, -2101.0)],
                name="Clear Level 2 Room 2",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
            ),
            PickupTorch(),
            BrazierSequence("Level 2 Brazier Route 2", L2_BRAZIER_PART2),
            BT.DropBundle(log=True),
            BT.ClearEnemiesInArea(Vec2f(-6798.8, -2436.4),allowed_alive_enemies=0,),
            ResilientVanquishNode(
                L2_PATH_TO_LOCK,
                name="Level 2 Route To Dungeon Lock",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
            ),
            BT.MoveAndInteractWithGadget(
                L2_DUNGEON_LOCK,
                pause_on_combat=False,
                log=True,
            ),
            BT.Move(
                L2_EXIT_PATH,
                pause_on_combat=False,
                
                log=True,
            ),
            BT.WaitForMapLoad(map_id=SOO_LEVEL_3, timeout_ms=60_000),
            BT.WaitUntilOnExplorable(timeout_ms=30_000),
            _mark_l3_start_node(),
            BT.Wait(2_000),
        ],
    )


# endregion

# region Level 3 - part 1
def Level3_FirstPath() -> BehaviorTree:
    return BT.Sequence(
        name="Run Shards of Orr Level 3 First Path",
        children=[
            BT.AddModelToLootWhitelist(25410),
            UseAvailableSummoningStone(),
            BT.MoveAndDialog(
                L3_ENTRY_BLESSING,
                dialog_id=DWARVEN_BLESSING_DIALOG,
                multi_account=True,
                log=True,
            ),
            ResilientVanquishNode(
                L3_MAIN_PATH,
                name="Level 3 Main Route",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
            ),
            BT.ClearEnemiesInArea(Vec2f(1025, 6872),radius=Range.Compass.value),
            BT.Move(Vec2f(1025, 6872))
        ],
    )
#endregion

# region Level 3 - part 2
def Level3_BrigantRoom() -> BehaviorTree:
    return BT.Sequence(
        name="Run Shards of Orr Level 3 Second Path",
        children=[
            BT.ClearEnemiesInArea(
                Vec2f(-8577, 4008),
                radius=Range.Compass.value,
            ),
            BT.Move(Vec2f(-8577, 4008))
        ],
    )
#endregion

def Level3_Torch() -> BehaviorTree:
    return BT.Sequence(
        name="Run Shards of Orr Level 3 Third Path",
        children=[
            BT.Move(
                L3_PATH_TO_TORCH,
                flag_heroes_to_waypoint=False,
                pause_on_combat=False
            ),
            BT.MoveAndInteractWithGadget(
                L3_TORCH_CHEST, pause_on_combat=False, log=True,
            ),
            PickupTorch(),
            BrazierSequence("Level 3 Brazier Route", L3_BRAZIERS),
            BT.DropBundle(log=True),
        ],
    )


# region Level 3 - part 3
def Level3_Brigant() -> BehaviorTree:
    return BT.Sequence(
        name="Run Shards of Orr Level 3",
        children=[                      
            BT.ClearEnemiesInArea(
                Vec2f(-9614, 3194),
                radius=Range.Longbow.value,
            ),
            BT.MoveAndInteractWithGadget(
                L3_BOSS_DOOR, pause_on_combat=False, log=True,
            ),
        ],
    )
# endregion

# region Level 3 - boss
def Level3_Fendi() -> BehaviorTree:
    return BT.Sequence(
        name="Run Fendi Boss Fight",
        children=[
            ResilientVanquishNode(
                L3_FENDI_PATH,
                name="Route To Fendi",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
            ),
            BT.WaitForClearEnemiesInArea(
                -15606.06, 15287.51,
                radius=Range.Compass.value,
                allowed_alive_enemies=0,
                interact_interval_ms=750,
                stable_clear_ms=20_000,
                keep_player_near_center=False,
                center_tolerance=750.0,
                log=True,
            ),
            _record_run_end_node(),
    
        ])
#endregion


# region Reward and restart flow


def CollectInsideReward() -> BehaviorTree:
    """
    Collect the Lost Souls reward from Shandra inside the dungeon.

    Shandra is resolved by partial, case-insensitive name matching. The routine
    then interacts with the current target and selects the first automatic
    dialogue option locally and across the multibox party.
    """
    return BT.Sequence(
        name="Collect Inside Reward",
        children=[
            BT.Move(Vec2f(-14873, 17174)),
            BT.MoveAndInteractWithGadget(
            gadget_id=FENDI_CHEST_GADGET_ID,
            pos=Vec2f(*FENDI_CHEST_POSITION),
            search_distance=700.0,
            interaction_distance=Range.Nearby.value,
            interaction_count=2,
            interaction_interval_ms=1000,
            account_settle_ms=3_000,
            timeout_ms=90_000,
            multi_account=True,
            include_self=True,
            log=True,
        ),
            BT.Wait(5_000),
            _inventory_statistics_node(after_chest=True),
            BT.TargetAgentByName(
                agent_name="Shandra",
                log=True,
            ),
            BT.LogMessage(
                message=(
                    "Shandra was found inside the dungeon. "
                    "Attempting to collect the Lost Souls reward "
                    "using automatic dialogue."
                ),
                module_name=MODULE_NAME,
            ),
            BT.InteractTargetAndAutoDialog(
                buttons=0,
                multi_account=True,
                aftercast_ms=500,
                log=True,
            ),
            BT.WaitForQuestCleared(
                LOST_SOULS_QUEST_ID,
                timeout_ms=15_000,
            ),
            BT.LogMessage(
                message=(
                    "The Lost Souls reward was successfully "
                    "collected inside the dungeon."
                ),
                module_name=MODULE_NAME,
            ),
        ],
    )


def PrepareNextDungeonRun() -> BehaviorTree:
    """
    Prepare the next Shards of Orr run after returning to Arbor Bay.

    Two scenarios are supported:

    1. The reward was collected inside the dungeon:
       - Lost Souls is missing;
       - retake the quest in Arbor Bay;
       - enter Shards of Orr.

    2. The reward remains complete:
       - collect the reward from Shandra in Arbor Bay;
       - enter and immediately leave Level 1;
       - retake Lost Souls in Arbor Bay;
       - enter Shards of Orr again for the next run.
    """

    reward_collected_inside = BT.Sequence(
        name="Restart After Inside Reward",
        children=[
            BT.IsQuestState(
                quest_id=LOST_SOULS_QUEST_ID,
                state="missing",
                log=True,
            ),
            BT.LogMessage(
                message=(
                    "The reward was already collected inside "
                    "the dungeon. Retaking Lost Souls."
                ),
                module_name=MODULE_NAME,
            ),
            BT.MoveAndDialog(
                SHANDRA_APPROACH,
                SHANDRA_TAKE_DIALOG,
                pause_on_combat=False,
                multi_account=True,
                log=True,
            ),
            BT.WaitForActiveQuest(
                LOST_SOULS_QUEST_ID,
                timeout_ms=15_000,
            ),
            EnterShardsOfOrr(),
        ],
    )

    reward_not_collected_inside = BT.Sequence(
        name="Restart After Outside Reward",
        children=[
            BT.IsQuestState(
                quest_id=LOST_SOULS_QUEST_ID,
                state="complete",
                log=True,
            ),
            BT.LogMessage(
                message=(
                    "The reward is still pending. "
                    "Collecting it from Shandra in Arbor Bay."
                ),
                module_name=MODULE_NAME,
            ),
            BT.Move(
                SHANDRA_APPROACH,
                pause_on_combat=False,
                log=True,
            ),
            BT.TargetAgentByName(
                agent_name="Shandra",
                log=True,
            ),
            BT.InteractTargetAndAutoDialog(
                buttons=0,
                multi_account=True,
                aftercast_ms=500,
                log=True,
            ),
            BT.WaitForQuestCleared(
                LOST_SOULS_QUEST_ID,
                timeout_ms=15_000,
            ),
            BT.LogMessage(
                message=(
                    "The Lost Souls reward was collected "
                    "successfully in Arbor Bay."
                ),
                module_name=MODULE_NAME,
            ),

            # Enter the dungeon once before retaking the quest,
            # as required by the outside-reward scenario.
            # Consumables stay suspended because the party immediately
            # returns to Arbor Bay without starting the next run.
            EnterShardsOfOrr(
                enable_consumables_on_entry=False,
            ),

            BT.MoveAndExitMap(
                LEVEL1_EXIT_TO_ARBOR,
                target_map_id=ARBOR_BAY,
                log=True,
            ),
            BT.WaitUntilOnExplorable(
                timeout_ms=30_000,
            ),
            BT.Wait(
                2_000,
            ),
            BT.Move(
                [
                    Vec2f(10218.0, -18864.0),
                    SHANDRA_APPROACH,
                ],
                pause_on_combat=False,
                log=True,
            ),
            BT.MoveAndDialog(
                SHANDRA_APPROACH,
                SHANDRA_TAKE_DIALOG,
                pause_on_combat=False,
                multi_account=True,
                log=True,
            ),
            BT.WaitForActiveQuest(
                LOST_SOULS_QUEST_ID,
                timeout_ms=15_000,
            ),
            EnterShardsOfOrr(),
        ],
    )

    return BT.Selector(
        name="Prepare Next Dungeon Run",
        children=[
            reward_collected_inside,
            reward_not_collected_inside,
        ],
    )


def CollectRewardAndPrepareRestart(
    end_countdown_timeout_ms: int = 190_000,
) -> BehaviorTree:
    """
    Attempt to collect the Lost Souls reward from Shandra inside the dungeon,
    then wait for the end-of-dungeon countdown and prepare the next run.

    Two scenarios are supported:

    1. Shandra is available inside the dungeon:
       - collect the reward inside;
       - wait for the automatic return to Arbor Bay;
       - retake Lost Souls;
       - enter Shards of Orr for the next run.

    2. Shandra is unavailable inside the dungeon:
       - log that the reward remains pending;
       - wait for the automatic return to Arbor Bay;
       - collect the reward outside;
       - perform the required dungeon entry/exit sequence;
       - retake Lost Souls;
       - enter Shards of Orr for the next run.
    """

    reward_collected_inside = BT.Sequence(
        name="Collect Shandra Reward Inside Dungeon",
        children=[
            BT.LogMessage(
                message=(
                    "Lost Souls is complete. Looking for "
                    "Shandra inside the dungeon."
                ),
                module_name=MODULE_NAME,
            ),
            CollectInsideReward(),
            BT.WaitForQuestCleared(
                LOST_SOULS_QUEST_ID,
                timeout_ms=15_000,
            ),
            BT.LogMessage(
                message=(
                    "Shandra was found inside the dungeon "
                    "and the Lost Souls reward was collected."
                ),
                module_name=MODULE_NAME,
            ),
        ],
    )

    reward_not_collected_inside = BT.Sequence(
        name="Shandra Unavailable Inside Dungeon",
        children=[
            BT.LogMessage(
                message=(
                    "Shandra was not found inside the dungeon "
                    "or the inside reward could not be collected. "
                    "The reward will be handled in Arbor Bay."
                ),
                module_name=MODULE_NAME,
            ),
            BT.Succeeder(
                "InsideRewardUnavailable",
            ),
        ],
    )

    return BT.Sequence(
        name="Collect Reward And Prepare Restart",
        children=[
            _runtime_consumable_upkeep_node(False),
            BT.Selector(
                name="Resolve Inside Reward",
                children=[
                    reward_collected_inside,
                    reward_not_collected_inside,
                ],
            ),
            BT.LogMessage(
                message=(
                    "Waiting for the end-of-dungeon countdown "
                    "and the return to Arbor Bay."
                ),
                module_name=MODULE_NAME,
            ),
            BT.WaitForMapLoad(
                map_id=ARBOR_BAY,
                timeout_ms=end_countdown_timeout_ms,
            ),
            BT.WaitUntilOnExplorable(
                timeout_ms=30_000,
            ),
            BT.Wait(
                2_000,
            ),
            BT.LogMessage(
                message=(
                    "The party has returned to Arbor Bay. "
                    "Preparing the next dungeon run."
                ),
                module_name=MODULE_NAME,
            ),
            BT.Move(
                SHANDRA_APPROACH,
                pause_on_combat=False,
                log=True,
            ),
            PrepareNextDungeonRun(),
            BT.LogMessage(
                message=(
                    "Lost Souls is active and the party is "
                    "back inside Shards of Orr Level 1."
                ),
                module_name=MODULE_NAME,
            ),
        ],
    )


# endregion


# region Execution


def get_execution_steps() -> list[tuple[str, Callable[[], BehaviorTree]]]:
    return [
        ("Initialize Bot", InitializeBot),
        ("Prepare Party And Supplies", PreparePartyAndSupplies),
        ("Travel To Shandra", TravelToShandra),
        ("Handle Shandra Quest", HandleShandraQuest),
        ("Enter Shards Of Orr", EnterShardsOfOrr),

        ("Level 1 Before door", Level1_Part1),
        ("Level 1 After door", Level1_Part2),

        ("Level 2 After First Brazier Sequence", Level2_Part1),
        ("Level 2 After First Room", Level2_Part2),

        ("Level 3 First Path", Level3_FirstPath),
        ("Level 3 Brigant Room", Level3_BrigantRoom),
        ("Level 3 Torch", Level3_Torch),
        ("Level 3 Brigant", Level3_Brigant),
        ("Level 3 Fendi Boss Fight", Level3_Fendi),

        ("Collect Reward And Prepare Restart", CollectRewardAndPrepareRestart),
    ]


def main() -> None:
    global initialized, ini_key

    if not initialized:
        if not ini_key:
            ini_key = IniManager().ensure_key(INI_PATH, INI_FILENAME)
            if not ini_key:
                return
            IniManager().load_once(ini_key)

        ensure_botting_tree()
        initialized = True

    tree = ensure_botting_tree()
    tree.tick()
    tree.UI.draw_window(
        icon_path=_BDS_ICON_PATH,
        iconwidth=96,
        main_child_dimensions=(420, 380),
        extra_tabs=[
            ("Statistics", _draw_statistics),
            ("Config", _draw_run_config),
        ],
    )


# endregion


if __name__ == "__main__":
    main()
