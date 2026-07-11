from __future__ import annotations

from collections.abc import Callable, Sequence
import os

import Py4GW
from typing import Optional, Any
import math
import time


from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Quest import Quest
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.AgentArray import AgentArray
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.enums_src.GameData_enums import Range

from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.enums_src.Player_enums import PlayerStatus
from Py4GWCoreLib.routines_src.behaviourtrees_src.items import BTItems
from Py4GWCoreLib.routines_src.behaviourtrees_src.constants.lists import CONSUMABLE_UPKEEPS as ALL_CONSUMABLE_UPKEEPS

from Sources.ApoSource.ApoBottingLib import wrappers as BT


MODULE_NAME = "Shards of Orr BT"
INI_PATH = "Widgets/Automation/Bots/Missions/Dungeons/Shards of Orr BT"
INI_FILENAME = "Shards_of_Orr_BT.ini"

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


CONSET_UPKEEPS = (
    ESSENCE_OF_CELERITY,
    GRAIL_OF_MIGHT,
    ARMOR_OF_SALVATION,
)

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

_SETTINGS_SECTION = "Settings"
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

L1_PATH_BEFORE_BRIGANT = [
    Vec2f(-11685.5, 10475.5), Vec2f(-10682.6, 9841.2),
    Vec2f(-9670.9, 9744.2), Vec2f(-8661.9, 9975.7),
    Vec2f(-7653.5, 10063.4), Vec2f(-6652.0, 10156.2),
    Vec2f(-5646.1, 10717.7), Vec2f(-4642.3, 11376.3),
    Vec2f(-3640.8, 11984.6), Vec2f(-2634.2, 12702.1),
    Vec2f(-1630.8, 13315.2), Vec2f(-628.5, 14075.6),
    Vec2f(379.8, 14700.8), Vec2f(1384.7, 15324.0),
    Vec2f(2394.5, 15950.3), Vec2f(3409.5, 15710.4),
    Vec2f(4157.9, 14705.9), Vec2f(5089.4, 13698.1),
    Vec2f(6090.8, 13172.6), Vec2f(7091.1, 13482.8),
    Vec2f(8093.3, 13148.6), Vec2f(8503.9, 12143.5),
    Vec2f(7496.9, 11676.0), Vec2f(6494.3, 10739.2),
]

L1_PATH_TO_FIRST_DOOR = [
    Vec2f(9196.0, 11484.4), Vec2f(10196.0, 12469.4),
    Vec2f(11198.7, 13401.8), Vec2f(12201.3, 14284.4),
    Vec2f(13202.8, 15176.3), Vec2f(14207.0, 16116.2),
    Vec2f(15208.8, 16871.6), Vec2f(16213.2, 16417.3),
    Vec2f(16643.4, 15416.6), Vec2f(16994.9, 14410.6),
    Vec2f(17115.6, 13405.6), Vec2f(16689.2, 12400.4),
]

L1_PATH_TO_GADGET = [
    Vec2f(15927.4, 11684.7), Vec2f(16037.8, 10679.9),
    Vec2f(15761.1, 9679.7), Vec2f(15289.5, 8672.6),
    Vec2f(14447.3, 7672.0), Vec2f(14526.2, 6664.2),
    Vec2f(14951.6, 5657.9),
]

L1_PATH_AFTER_DOOR = [
    Vec2f(15364.9, 4858.7), Vec2f(15689.5, 3857.7),
    Vec2f(16026.7, 2857.1), Vec2f(17030.7, 2262.6),
    Vec2f(18035.7, 1888.8), Vec2f(19037.1, 1384.6),
    Vec2f(19679.2, 1009.5), Vec2f(20181.6, 1203.7),
    Vec2f(20400.5, 1300.0),
]

# Level 2 routes / torch mechanics
TORCH_MODEL_IDS = (22341, 22342)
TORCH_BUFF_ID = 2545

L2_BLESSING_NPC = Vec2f(-14076.0, -19457.0)
L2_PATH_TO_TORCH = [
    Vec2f(-14977.9, -16480.2),
    Vec2f(-15985.6, -16838.1),
    Vec2f(-16985.9, -16929.4),
]
L2_TORCH_CHEST = Vec2f(-14709.0, -16548.0)
L2_FIRST_TORCH_DROP_POINT_PATH = [
    Vec2f(-11002.0, -17001.0),
]
L2_RETURN_TO_FIRST_TORCH_PATH = [
    Vec2f(-9259.0, -17322.0),
    Vec2f(-9971.23, -17633.08),
    Vec2f(-11136.85, -17201.66),
]
L2_BRAZIER_PART1 = [
    (-11303.0, -14596.0),
    (-11019.0, -11550.0),
    (-9028.0, -9021.0),
    (-6805.0, -11511.0),
    (-8984.0, -13842.0),
]
L2_CLEANING_PATH = [
    Vec2f(-8836.63, -11471.01),
]
L2_TO_ROOM2_DROP = Vec2f(-11061.1, -7578.5)
L2_RETURN_TO_ROOM2_TORCH_PATH = [
    Vec2f(-10958.2, -4529.5),
    Vec2f(-11690.64, -3802.55),
    Vec2f(-10958.2, -4529.5),
    Vec2f(-11032.11, -5389.71),
    Vec2f(-11090.10, -6890.14),
]
L2_ROOM2_PATH = [
    Vec2f(-8066.1, -4222.4),
    Vec2f(-7058.8, -4191.0),
]

L2_BRAZIER_PART2 = [
    (-3717.0, -4254.0),
    (-8251.0, -3240.0),
    (-8278.0, -1670.0),
]
L2_AFTER_PART2_POSITION = Vec2f(-5009.49, -2542.30)
L2_PATH_TO_LOCK = [
    Vec2f(-11033.4, -6755.6),
    Vec2f(-11318.0, -7767.2),
    Vec2f(-12320.7, -8417.1),
    Vec2f(-13324.0, -8649.0),
    Vec2f(-14326.3, -8773.0),
    Vec2f(-15331.0, -8905.6),
    Vec2f(-16335.1, -9004.5),
]
L2_DUNGEON_LOCK = Vec2f(-18725.0, -9171.0)
L2_EXIT_PATH = [
    Vec2f(-18610.0, -8636.0),
    Vec2f(-19571.61, -8459.0),
]

# Level 3 routes
L3_ENTRY_BLESSING = Vec2f(17544.0, 18810.0)
L3_MAIN_PATH = [
    Vec2f(16111.0, 17556.0), Vec2f(13998.4,18866.7),
    Vec2f(12990.9,19299.5), Vec2f(11988.8,19353.2),
    Vec2f(10986.4,19188.9), Vec2f(9985.7,18719.2),
    Vec2f(9402.1,17715.6), Vec2f(9076.9,17383.4),
    Vec2f(9133.0,16373.0), Vec2f(8496.5,15367.3),
    Vec2f(7978.0,14357.9), Vec2f(7105.7,13350.9),
    Vec2f(6236.1,12349.0), Vec2f(5524.4,11344.1),
    Vec2f(4813.8,10340.7), Vec2f(4095.0,9332.7),
    Vec2f(3091.4,8424.8), Vec2f(2078.2,8286.5),
    Vec2f(1926.0,5848.0), Vec2f(1069.7,8045.3),
    Vec2f(619.8,7044.0), Vec2f(-385.8,6478.3),
    Vec2f(-1123.5,7481.9),
]
L3_BRIGANT_APPROACH = [
    Vec2f(-2964.1,7302.1), Vec2f(-3139.7,7022.7),
    Vec2f(-4152.0,6469.6), Vec2f(-5154.0,5969.0),
    Vec2f(-5837.7,4968.0), Vec2f(-5832.1,3954.0),
    Vec2f(-6838.3,3495.2), Vec2f(-7845.7,4397.5),
    Vec2f(-8049.0,5403.5), Vec2f(-9049.9,5289.2),
    Vec2f(-10051.1,4604.6), Vec2f(-11057.4,4039.1),
    Vec2f(-10381.7,3037.7),
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
L3_BRIGANT_KILL_PATH = [Vec2f(-11878.79,2166.51), Vec2f(-9686.32,2632.0)]
L3_BOSS_DOOR = Vec2f(-9252.32, 6396.40)
L3_FENDI_PATH = [
    Vec2f(-8871.19,6152.95), Vec2f(-9326.33,6862.55),
    Vec2f(-10044.56,7921.78), Vec2f(-8408.54,9475.41),
    Vec2f(-10049.41,11259.31), Vec2f(-11381.15,12387.01),
    Vec2f(-12304.50,13319.24), Vec2f(-14736.33,15054.21),
    Vec2f(-15000.0,16850.0),
]
FENDI_CHEST_POSITION = (-15800.98, 16901.23)
FENDI_CHEST_GADGET_ID = 8934
FENDI_SCAN_RADIUS = 700.0
FENDI_BOSS_MODEL_IDS = {7064, 7065}

initialized = False
ini_key = ""
botting_tree: BottingTree | None = None


def _load_settings() -> None:
    global _settings_loaded
    global _use_hard_mode, _restock_conset, _activate_conset
    global _restock_pcons, _activate_pcons, _use_summoning_stone

    if _settings_loaded:
        return

    _use_hard_mode = _settings_ini.read_bool(_SETTINGS_SECTION, "HardMode", True)
    _restock_conset = _settings_ini.read_bool(_SETTINGS_SECTION, "RestockConset", True)
    _activate_conset = _settings_ini.read_bool(_SETTINGS_SECTION, "ActivateConset", True)
    _restock_pcons = _settings_ini.read_bool(_SETTINGS_SECTION, "RestockPcons", True)
    _activate_pcons = _settings_ini.read_bool(_SETTINGS_SECTION, "ActivatePcons", True)
    _use_summoning_stone = _settings_ini.read_bool(_SETTINGS_SECTION, "UseSummoningStone", True)
    _settings_loaded = True


def _save_settings() -> None:
    _settings_ini.write_key(_SETTINGS_SECTION, "HardMode", str(bool(_use_hard_mode)))
    _settings_ini.write_key(_SETTINGS_SECTION, "RestockConset", str(bool(_restock_conset)))
    _settings_ini.write_key(_SETTINGS_SECTION, "ActivateConset", str(bool(_activate_conset)))
    _settings_ini.write_key(_SETTINGS_SECTION, "RestockPcons", str(bool(_restock_pcons)))
    _settings_ini.write_key(_SETTINGS_SECTION, "ActivatePcons", str(bool(_activate_pcons)))
    _settings_ini.write_key(_SETTINGS_SECTION, "UseSummoningStone", str(bool(_use_summoning_stone)))


def _enabled_consumable_upkeeps() -> tuple[int, ...]:
    enabled: list[int] = []
    if _activate_conset:
        enabled.extend(CONSET_UPKEEPS)
    if _activate_pcons:
        enabled.extend(PCON_UPKEEPS)
    return tuple(dict.fromkeys(int(model_id) for model_id in enabled))


def _configure_runtime_upkeeps() -> None:
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
        consumable_upkeeps=_enabled_consumable_upkeeps(),
        heroai_state_logging=False,
    )


def _draw_settings() -> None:
    import PyImGui
    global _use_hard_mode, _restock_conset, _activate_conset
    global _restock_pcons, _activate_pcons, _use_summoning_stone

    _load_settings()
    PyImGui.text("Shards of Orr Settings")
    PyImGui.separator()

    changed = False
    upkeep_changed = False

    value = PyImGui.checkbox("Hard Mode (HM)", _use_hard_mode)
    if value != _use_hard_mode:
        _use_hard_mode = value
        changed = True

    PyImGui.separator()
    PyImGui.text("Conset")
    value = PyImGui.checkbox("Restock conset from storage", _restock_conset)
    if value != _restock_conset:
        _restock_conset = value
        changed = True
    value = PyImGui.checkbox("Activate / maintain conset", _activate_conset)
    if value != _activate_conset:
        _activate_conset = value
        changed = True
        upkeep_changed = True

    PyImGui.separator()
    PyImGui.text("Personal consumables (pcons)")
    value = PyImGui.checkbox("Restock pcons from storage", _restock_pcons)
    if value != _restock_pcons:
        _restock_pcons = value
        changed = True
    value = PyImGui.checkbox("Activate / maintain pcons", _activate_pcons)
    if value != _activate_pcons:
        _activate_pcons = value
        changed = True
        upkeep_changed = True

    PyImGui.separator()
    value = PyImGui.checkbox("Use summoning stone", _use_summoning_stone)
    if value != _use_summoning_stone:
        _use_summoning_stone = value
        changed = True

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
    def _build(_node: BehaviorTree.Node) -> BehaviorTree:
        items: list[tuple[int, int]] = []
        if _restock_conset:
            items.extend(CONSET_RESTOCK_ITEMS)
        if _restock_pcons:
            items.extend(PCON_RESTOCK_ITEMS)
        if not items:
            return BT.Succeeder("RestockDisabled")
        return BT.RestockItemsFromList(tuple(items), allow_missing=True)

    return BT.Subtree(name="Restock Selected Consumables", subtree_fn=_build)

def _quest_state() -> str:
    quest_ids = {int(quest_id) for quest_id in (Quest.GetQuestLogIds() or [])}
    if LOST_SOULS_QUEST_ID not in quest_ids:
        return "missing"
    if Quest.IsQuestCompleted(LOST_SOULS_QUEST_ID):
        return "complete"
    return "active"


def _quest_state_is(expected: str, name: str) -> BehaviorTree:
    def _check(_node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        return (
            BehaviorTree.NodeState.SUCCESS
            if _quest_state() == expected
            else BehaviorTree.NodeState.FAILURE
        )

    return BehaviorTree(BehaviorTree.ActionNode(name=name, action_fn=_check))


def _map_is(map_id: int, name: str) -> BehaviorTree:
    def _check(_node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        return (
            BehaviorTree.NodeState.SUCCESS
            if int(Map.GetMapID()) == int(map_id)
            else BehaviorTree.NodeState.FAILURE
        )

    return BehaviorTree(BehaviorTree.ActionNode(name=name, action_fn=_check))


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(float(a[0]) - float(b[0]), float(a[1]) - float(b[1]))


def EnsureTorch(name: str) -> BehaviorTree:
    """Ensure that the local player is carrying an active SoO torch."""
    return BT.Selector(
        name=name,
        children=[
            BT.HasLocalEffect(
                effect_id=TORCH_BUFF_ID,
                log=True,
            ),
            BT.Sequence(
                name=f"{name} Pickup",
                children=[
                    BT.PickupGroundItemByModelID(
                        model_ids=TORCH_MODEL_IDS,
                        max_distance=5_000.0,
                        pickup_distance=180.0,
                        timeout_ms=15_000,
                        allow_unassigned=True,
                        interaction_interval_ms=150,
                        aftercast_ms=100,
                        log=True,
                    ),
                    BT.HasLocalEffect(
                        effect_id=TORCH_BUFF_ID,
                        log=True,
                    ),
                ],
            ),
        ],
    )


def BrazierSequence(
    name: str,
    points: list[tuple[float, float]],
) -> BehaviorTree:
    children: list[BehaviorTree | BehaviorTree.Node] = []

    for x, y in points:
        children.extend(
            [
                BT.HasLocalEffect(
                    effect_id=TORCH_BUFF_ID,
                    log=True,
                ),
                BT.MoveAndInteractWithGadget(
                    pos=Vec2f(float(x), float(y)),
                    gadget_id=None,
                    search_distance=300.0,
                    interaction_distance=220.0,
                    interaction_count=2,
                    interaction_interval_ms=100,
                    timeout_ms=15_000,
                    pause_on_combat=False,
                    multi_account=False,
                    include_self=True,
                    log=True,
                ),
                BT.HasLocalEffect(
                    effect_id=TORCH_BUFF_ID,
                    log=True,
                ),
            ]
        )

    return BT.Sequence(
        name=name,
        children=children,
    )

def DropBundleTwice(name: str = "Drop Bundle Twice") -> BehaviorTree:
    return BT.Sequence(
        name=name,
        children=[
            BT.DropBundle(log=True),
            BT.Wait(250),
        ],
    )



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


def PreparePartyAndSupplies() -> BehaviorTree:
    already_ready_in_level_1 = BT.Sequence(
        name="Skip Outpost Preparation - Already In Level 1",
        children=[
            _map_is(SOO_LEVEL_1, "AlreadyInSoOLevel1ForPreparation"),
            _quest_state_is("active", "LostSoulsActiveForPreparation"),
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
            _map_is(SOO_LEVEL_1, "AlreadyInSoOLevel1ForTravel"),
            _quest_state_is("active", "LostSoulsActiveForTravel"),
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
            _map_is(SOO_LEVEL_1, "AlreadyInSoOLevel1ForQuest"),
            _quest_state_is("active", "LostSoulsAlreadyActiveInside"),
            BT.Succeeder("ShandraHandlerAlreadyDone"),
        ],
    )
    active = BT.Sequence(
        name="Lost Souls Already Active",
        children=[_quest_state_is("active", "LostSoulsIsActive"), BT.Succeeder("ContinueWithActiveQuest")],
    )
    completed = BT.Sequence(
        name="Collect And Retake Lost Souls",
        children=[
            _quest_state_is("complete", "LostSoulsIsComplete"),
            BT.MoveAndDialog(SHANDRA_APPROACH, SHANDRA_REWARD_DIALOG, pause_on_combat=False, multi_account=True, log=True),
            BT.WaitForQuestCleared(LOST_SOULS_QUEST_ID, timeout_ms=15_000),
            BT.MoveAndDialog(SHANDRA_APPROACH, SHANDRA_TAKE_DIALOG, pause_on_combat=False, multi_account=True, log=True),
            BT.WaitForActiveQuest(LOST_SOULS_QUEST_ID, timeout_ms=15_000),
        ],
    )
    missing = BT.Sequence(
        name="Take Lost Souls",
        children=[
            _quest_state_is("missing", "LostSoulsIsMissing"),
            BT.MoveAndDialog(SHANDRA_APPROACH, SHANDRA_TAKE_DIALOG, pause_on_combat=False, multi_account=True, log=True),
            BT.WaitForActiveQuest(LOST_SOULS_QUEST_ID, timeout_ms=15_000),
        ],
    )
    return BT.Selector(children=[already_inside, active, completed, missing], name="Handle Shandra Quest")

def EnterShardsOfOrr() -> BehaviorTree:
    already_inside = BT.Sequence(
        name="Skip Dungeon Entry - Already In Level 1",
        children=[
            _map_is(SOO_LEVEL_1, "AlreadyInSoOLevel1ForEntry"),
            _quest_state_is("active", "LostSoulsActiveForEntry"),
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
    return BT.Selector(children=[already_inside, normal_entry], name="Enter Shards of Orr")

def UseAvailableSummon() -> BehaviorTree:
    def _build(_node: BehaviorTree.Node) -> BehaviorTree:
        if not _use_summoning_stone:
            return BT.Succeeder("SummoningStoneDisabled")
        return BT.Selector(
            children=[
                BTItems.UseConsumable(model_id) for model_id in SUMMON_MODEL_IDS
            ] + [BT.Succeeder("NoSummonAvailable")],
            name="Use Available Summon"
        )

    return BT.Subtree(name="Use Summoning Stone Setting", subtree_fn=_build)


def RunLevel1() -> BehaviorTree:
    return BT.Sequence(
        name="Run Shards of Orr Level 1",
        children=[
            BT.AddModelToLootWhitelist(25416),
            BT.MoveAndDialog(
                Vec2f(-11686.0, 10427.0),
                dialog_id=DWARVEN_BLESSING_DIALOG,
                multi_account=True,
                log=True,
            ),
            UseAvailableSummon(),
            BT.VanquishNode(
                L1_PATH_BEFORE_BRIGANT,
                name="Level 1 First Route",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Nearby.value,
            ),
            BT.VanquishNode(
                L1_PATH_TO_FIRST_DOOR,
                name="Level 1 Route To Door",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Nearby.value,
            ),
            BT.Move(Vec2f(15953.0, 11902.0), pause_on_combat=True),
            BT.VanquishNode(
                L1_PATH_TO_GADGET,
                name="Level 1 Route To Door Gadget",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Nearby.value,
            ),
            BT.MoveAndInteractWithGadget(Vec2f(15100.0, 5443.0),
                pause_on_combat=True,
                log=True,
            ),
            BT.VanquishNode(
                L1_PATH_AFTER_DOOR,
                name="Level 1 Route To Level 2",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Nearby.value,
            ),
            BT.WaitForMapLoad(map_id=SOO_LEVEL_2, timeout_ms=60_000),
            BT.WaitUntilOnExplorable(timeout_ms=30_000),
            BT.Wait(2_000),
        ],
    )


def RunLevel2() -> BehaviorTree:
    return BT.Sequence(
        name="Run Shards of Orr Level 2",
        children=[
            BT.MoveAndDialog(
                L2_BLESSING_NPC,
                dialog_id=DWARVEN_BLESSING_DIALOG,
                multi_account=True,
                log=True,
            ),
            UseAvailableSummon(),
            BT.VanquishNode(
                L2_PATH_TO_TORCH,
                name="Level 2 Route To Torch Chest",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Nearby.value,
            ),
            BT.MoveAndInteractWithGadget(
                L2_TORCH_CHEST,
                pause_on_combat=False,
                log=True,
            ),
            EnsureTorch("Pickup First Level 2 Torch"),
            BT.Move(L2_FIRST_TORCH_DROP_POINT_PATH, pause_on_combat=True),
            DropBundleTwice("Drop Torch Before First Combat"),
            BT.VanquishNode(
                L2_RETURN_TO_FIRST_TORCH_PATH,
                name="Clear And Return To First Torch",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Nearby.value,
            ),
            EnsureTorch("Recover First Level 2 Torch"),
            BT.Move(Vec2f(-11030.3, -17474.0), pause_on_combat=False),
            BT.Move(Vec2f(-11303.0, -14596.0), pause_on_combat=False),
            BrazierSequence("Level 2 Brazier Route 1", L2_BRAZIER_PART1),
            DropBundleTwice("Drop Torch For Level 2 Cleaning Route"),
            BT.VanquishNode(
                L2_CLEANING_PATH,
                name="Clear Remaining Level 2 Room 1 Enemies",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Compass.value,
            ),
            EnsureTorch("Pick Up Torch After Level 2 Cleaning"),
            BT.Move(L2_TO_ROOM2_DROP, pause_on_combat=True),
            DropBundleTwice("Drop Torch Before Room 2"),
            BT.VanquishNode(
                L2_RETURN_TO_ROOM2_TORCH_PATH,
                name="Clear Route Back To Room 2 Torch",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Nearby.value,
            ),
            EnsureTorch("Pick Up Level 2 Room 2 Torch"),
            BT.VanquishNode(
                L2_ROOM2_PATH,
                name="Clear Level 2 Room 2",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Nearby.value,
            ),
            DropBundleTwice("Drop Torch At End Of Room 2"),
            BT.VanquishNode([Vec2f(-4245.2, -2101.0)],
                name="Clear Level 2 Room 2",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Nearby.value,
            ),
            EnsureTorch("Pick Up Torch For Second Brazier Route"),
            BrazierSequence("Level 2 Brazier Route 2", L2_BRAZIER_PART2),
            DropBundleTwice("Drop Torch After Second Brazier Route"),
            BT.VanquishNode(
                L2_PATH_TO_LOCK,
                name="Level 2 Route To Dungeon Lock",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Nearby.value,
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
            BT.Wait(2_000),
        ],
    )


def ResolveFendiFight() -> BehaviorTree:
    """Resolve the Fendi encounter with a native stateful BT ActionNode."""
    anchor = (-16022.9, 17889.9)
    state: dict[str, float | None] = {"stable_since": None}

    def _reset() -> None:
        state["stable_since"] = None

    def _tick(_node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        if Map.GetMapID() != SOO_LEVEL_3:
            _reset()
            return BehaviorTree.NodeState.FAILURE

        player_xy = Player.GetXY()
        if not player_xy:
            return BehaviorTree.NodeState.RUNNING

        if _distance(player_xy, anchor) > 750.0:
            Player.Move(*anchor)

        nearest_id = 0
        nearest_distance = float("inf")
        boss_present = False

        for agent_id in AgentArray.GetEnemyArray():
            if not Agent.IsAlive(agent_id):
                continue

            enemy_xy = Agent.GetXY(agent_id)
            if not enemy_xy or _distance(enemy_xy, anchor) > Range.Compass.value:
                continue

            if int(Agent.GetModelID(agent_id)) in FENDI_BOSS_MODEL_IDS:
                boss_present = True

            distance = _distance(enemy_xy, player_xy)
            if distance < nearest_distance:
                nearest_distance = distance
                nearest_id = int(agent_id)

        if nearest_id:
            state["stable_since"] = None
            Player.ChangeTarget(nearest_id)
            Player.Interact(nearest_id, True)
            enemy_xy = Agent.GetXY(nearest_id)
            if enemy_xy and nearest_distance > Range.Earshot.value:
                Player.Move(*enemy_xy)
            return BehaviorTree.NodeState.RUNNING

        if boss_present:
            state["stable_since"] = None
            return BehaviorTree.NodeState.RUNNING

        stable_since = state["stable_since"]
        if stable_since is None:
            state["stable_since"] = time.monotonic()
            Player.Move(*anchor)
            return BehaviorTree.NodeState.RUNNING

        if time.monotonic() - float(stable_since) >= 20.0:
            _reset()
            return BehaviorTree.NodeState.SUCCESS

        Player.Move(*anchor)
        return BehaviorTree.NodeState.RUNNING

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name="Resolve Fendi Fight",
            action_fn=_tick,
        )
    )



def _find_shandra_nearby(max_dist: float = 3000.0) -> int:
    npcs = AgentArray.GetNPCMinipetArray()
    npcs = AgentArray.Filter.ByDistance(npcs, Player.GetXY(), max_dist)
    npcs = AgentArray.Sort.ByDistance(npcs, Player.GetXY())
    for agent_id in npcs:
        try:
            if "shandra" in Agent.GetNameByID(int(agent_id)).lower():
                return int(agent_id)
        except Exception:
            continue
    return 0


def CollectInsideReward() -> BehaviorTree:
    """Collect Shandra's in-dungeon reward with a native BT ActionNode."""
    state: dict[str, Any] = {
        "phase": "find",
        "deadline": 0.0,
        "target": 0,
        "settle_until": 0.0,
    }

    def _reset() -> None:
        state.update(
            phase="find",
            deadline=0.0,
            target=0,
            settle_until=0.0,
        )

    def _tick(_node: BehaviorTree.Node) -> BehaviorTree.NodeState:
        now = time.monotonic()
        phase = str(state["phase"])

        if phase == "find":
            if float(state["deadline"]) <= 0.0:
                state["deadline"] = now + 12.0

            target = _find_shandra_nearby()
            if not target:
                if now >= float(state["deadline"]):
                    _reset()
                    return BehaviorTree.NodeState.FAILURE
                return BehaviorTree.NodeState.RUNNING

            state["target"] = target
            Player.ChangeTarget(target)
            Player.Interact(target, False)
            Player.SendDialog(SHANDRA_REWARD_DIALOG)

            sender = Player.GetAccountEmail()
            for account in GLOBAL_CACHE.ShMem.GetAllAccountData() or []:
                email = str(getattr(account, "AccountEmail", "") or "")
                if email and email != sender:
                    GLOBAL_CACHE.ShMem.SendMessage(
                        sender,
                        email,
                        SharedCommandType.SendDialogToTarget,
                        (
                            float(target),
                            float(SHANDRA_REWARD_DIALOG),
                            0.0,
                            0.0,
                        ),
                    )

            state["phase"] = "settle"
            state["settle_until"] = now + 3.0
            return BehaviorTree.NodeState.RUNNING

        if phase == "settle":
            if now < float(state["settle_until"]):
                return BehaviorTree.NodeState.RUNNING
            _reset()
            return BehaviorTree.NodeState.SUCCESS

        _reset()
        return BehaviorTree.NodeState.FAILURE

    return BehaviorTree(
        BehaviorTree.ActionNode(
            name="Collect Inside Reward",
            action_fn=_tick,
        )
    )



def PrepareNextDungeonRun() -> BehaviorTree:
    reward_collected_inside = BT.Sequence(
        name="Restart After Inside Reward",
        children=[
            _quest_state_is("missing", "LostSoulsMissingAfterInsideReward"),
            BT.LogMessage(message="Reward already collected inside. Retaking Lost Souls.", module_name=MODULE_NAME),
            BT.MoveAndDialog(SHANDRA_APPROACH, SHANDRA_TAKE_DIALOG, pause_on_combat=False, multi_account=True, log=True),
            BT.WaitForActiveQuest(LOST_SOULS_QUEST_ID, timeout_ms=15_000),
            EnterShardsOfOrr(),
        ],
    )

    reward_not_collected_inside = BT.Sequence(
        name="Restart After Outside Reward",
        children=[
            _quest_state_is("complete", "LostSoulsCompleteAfterDungeon"),
            BT.LogMessage(message="Reward still pending. Collecting it in Arbor Bay.", module_name=MODULE_NAME),
            BT.MoveAndDialog(SHANDRA_APPROACH, SHANDRA_REWARD_DIALOG, pause_on_combat=False, multi_account=True, log=True),
            BT.WaitForQuestCleared(LOST_SOULS_QUEST_ID, timeout_ms=15_000),
            EnterShardsOfOrr(),
            BT.MoveAndExitMap(LEVEL1_EXIT_TO_ARBOR, target_map_id=ARBOR_BAY, log=True),
            BT.WaitUntilOnExplorable(timeout_ms=30_000),
            BT.Wait(2_000),
            BT.Move([Vec2f(10218.0, -18864.0), SHANDRA_APPROACH], pause_on_combat=False, log=True),
            BT.MoveAndDialog(SHANDRA_APPROACH, SHANDRA_TAKE_DIALOG, pause_on_combat=False, multi_account=True, log=True),
            BT.WaitForActiveQuest(LOST_SOULS_QUEST_ID, timeout_ms=15_000),
            EnterShardsOfOrr(),
        ],
    )

    return BT.Selector(name="Prepare Next Dungeon Run",children=[reward_collected_inside,reward_not_collected_inside,],
)


def CollectRewardAndPrepareRestart() -> BehaviorTree:
    try_inside_reward = BT.Sequence(
        name="Try Collect Shandra Reward Inside Dungeon",
        children=[
            _quest_state_is("complete", "LostSoulsCompleteInsideDungeon"),
            CollectInsideReward(),
            BT.WaitForQuestCleared(LOST_SOULS_QUEST_ID, timeout_ms=15_000),
        ],
    )

    return BT.Sequence(
        name="Collect Reward And Prepare Restart",
        children=[
            BT.Selector(name="Try Inside Reward", children=[try_inside_reward, BT.Succeeder(name="InsideRewardUnavailable")]),
            BT.LogMessage(message="Waiting for the end-of-dungeon countdown.", module_name=MODULE_NAME),
            BT.WaitForMapLoad(map_id=ARBOR_BAY, timeout_ms=120_000),
            BT.WaitUntilOnExplorable(timeout_ms=30_000),
            BT.Wait(2_000),
            BT.Move(SHANDRA_APPROACH, pause_on_combat=False, log=True),
            PrepareNextDungeonRun(),
            BT.LogMessage(message="Lost Souls active and party back in SoO Level 1.", module_name=MODULE_NAME),
        ],
    )

def RunLevel3() -> BehaviorTree:
    return BT.Sequence(
        name="Run Shards of Orr Level 3",
        children=[
            BT.MoveAndDialog(
                L3_ENTRY_BLESSING,
                dialog_id=DWARVEN_BLESSING_DIALOG,
                multi_account=True,
                log=True,
            ),
            UseAvailableSummon(),
            BT.VanquishNode(
                L3_MAIN_PATH,
                name="Level 3 Main Route",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Nearby.value,
            ),
            BT.VanquishNode(
                L3_BRIGANT_APPROACH,
                name="Level 3 Route Before Torch",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Nearby.value,
            ),
            BT.VanquishNode(
                L3_PATH_TO_TORCH,
                name="Level 3 Route To Torch Chest",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Nearby.value,
            ),
            BT.MoveAndInteractWithGadget(
                L3_TORCH_CHEST, pause_on_combat=False, log=True,
            ),
            EnsureTorch("Pickup Level 3 Torch"),
            BrazierSequence("Level 3 Brazier Route", L3_BRAZIERS),
            DropBundleTwice("Drop Level 3 Torch"),
            BT.VanquishNode(
                L3_BRIGANT_KILL_PATH,
                name="Kill Level 3 Brigant",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Nearby.value,
            ),
            BT.MoveAndInteractWithGadget(
                L3_BOSS_DOOR, pause_on_combat=False, log=True,
            ),
            BT.VanquishNode(
                L3_FENDI_PATH,
                name="Route To Fendi",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Nearby.value,
            ),
            ResolveFendiFight(),
            BT.Move(
                Vec2f(-15821.0, 16834.0),
                pause_on_combat=False,
                log=True,
            ),
            BT.MoveAndInteractWithGadget(
            gadget_id=FENDI_CHEST_GADGET_ID,
            pos=Vec2f(*FENDI_CHEST_POSITION),
            search_distance=700.0,
            interaction_distance=Range.Nearby.value,
            interaction_count=1,
            interaction_interval_ms=500,
            account_settle_ms=5_000,
            timeout_ms=90_000,
            multi_account=True,
            include_self=True,
            log=True,
        ),
            CollectRewardAndPrepareRestart(),
        ],
    )


def get_execution_steps() -> list[tuple[str, Callable[[], BehaviorTree]]]:
    return [
        ("Initialize Bot", InitializeBot),
        ("Prepare Party And Supplies", PreparePartyAndSupplies),
        ("Travel To Shandra", TravelToShandra),
        ("Handle Shandra Quest", HandleShandraQuest),
        ("Enter Shards Of Orr", EnterShardsOfOrr),
        ("Run Level 1", RunLevel1),
        ("Run Level 2", RunLevel2),
        ("Run Level 3", RunLevel3),
    ]


def main() -> None:
    global initialized, ini_key

    if not initialized:
        if not ini_key:
            ini_key = IniManager().ensure_key(INI_PATH, INI_FILENAME)
            if not ini_key:
                return
            IniManager().load_once(ini_key)

        tree = ensure_botting_tree()
        tree.UI.override_draw_config(_draw_settings)
        initialized = True

    tree = ensure_botting_tree()
    tree.tick()
    tree.UI.draw_window()


if __name__ == "__main__":
    main()