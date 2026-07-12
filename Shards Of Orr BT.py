from __future__ import annotations

from collections.abc import Callable
import os, Py4GW
from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib.enums_src.GameData_enums import Range
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.native_src.internals.types import Vec2f
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib.enums_src.Player_enums import PlayerStatus
from Py4GWCoreLib.routines_src.behaviourtrees_src.constants.lists import CONSET_UPKEEPS, CONSUMABLE_UPKEEPS as ALL_CONSUMABLE_UPKEEPS
from Py4GWCoreLib.routines_src.behaviourtrees_src.items import BTItems
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

L1_PATH = [
    Vec2f(3720.16, 15370.78),
    Vec2f(6740.06, 11039.32),
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

L2_PATH_TO_TORCH = [
    Vec2f(-16985.9, -16929.4),
]
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
L2_PATH_TO_LOCK = [
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
    Vec2f(16325.98, 15981.14),
    Vec2f(13998.4,18866.7),
    Vec2f(8496.5,15367.3),
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
L3_BRIGANT_KILL_PATH = [Vec2f(-11878.79,2166.51), Vec2f(-9252.32, 6396.40), Vec2f(-9686.32,2632.0)]
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

    global _use_hard_mode
    global _restock_conset, _activate_conset
    global _restock_pcons, _activate_pcons
    global _use_summoning_stone

    _load_settings()

    PyImGui.text("Shards of Orr Settings")
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


def BrazierSequence(
    name: str,
    points: list[tuple[float, float]],
) -> BehaviorTree:
    children: list[BehaviorTree | BehaviorTree.Node] = []

    for x, y in points:
        children.append(
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
            )
        )

    return BT.Sequence(
        name=name,
        children=children,
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

def EnterShardsOfOrr() -> BehaviorTree:
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
    return BT.Selector(children=[already_inside, normal_entry], name="Enter Shards of Orr")

def RunLevel1() -> BehaviorTree:
    return BT.Sequence(
        name="Run Shards of Orr Level 1",
        children=[
            UseAvailableSummoningStone(),
            BT.AddModelToLootWhitelist(25410),
            BT.MoveAndDialog(
                Vec2f(-11686.0, 10427.0),
                dialog_id=DWARVEN_BLESSING_DIALOG,
                multi_account=True,
                log=True,
            ),
            BT.VanquishNode(
                L1_PATH,
                name="Level 1 First Route",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
            ),
            
            BT.MoveAndInteractWithGadget(Vec2f(15100.0, 5443.0),
                pause_on_combat=True,
                log=True,
            ),
            BT.VanquishNode(
                L1_PATH_AFTER_DOOR,
                name="Level 1 Route To Level 2",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
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
            UseAvailableSummoningStone(),
            BT.AddModelToLootWhitelist(25410),
            BT.MoveAndDialog(
                L2_BLESSING_NPC,
                dialog_id=DWARVEN_BLESSING_DIALOG,
                multi_account=True,
                log=True,
            ),
            BT.VanquishNode(
                L2_PATH_TO_TORCH,
                name="Level 2 Route To Torch Chest",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
            ),
            BT.MoveAndInteractWithGadget(
                L2_TORCH_CHEST,
                pause_on_combat=False,
                log=True,
            ),
            BT.PickupGroundItemByModelID(model_ids=TORCH_MODEL_IDS,max_distance=10_000.0,timeout_ms=45_000,allow_unassigned=True,interaction_interval_ms=5000,aftercast_ms=100,log=True,),
            BT.Move(L2_FIRST_TORCH_DROP_POINT_PATH, pause_on_combat=True),
            BT.DropBundle(log=True),
            BT.VanquishNode(
                L2_RETURN_TO_FIRST_TORCH_PATH,
                name="Clear And Return To First Torch",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
            ),
            BT.PickupGroundItemByModelID(model_ids=TORCH_MODEL_IDS,max_distance=10_000.0,timeout_ms=45_000,allow_unassigned=True,interaction_interval_ms=5000,aftercast_ms=100,log=True,),
            BT.Move(Vec2f(-9404.44, -17963.49), pause_on_combat=True),
            BT.Move(Vec2f(-11303.00, -14596.00), pause_on_combat=True),
            BrazierSequence("Level 2 Brazier Route 1", L2_BRAZIER_PART1),
            BT.DropBundle(log=True),
            BT.VanquishNode(
                L2_CLEANING_PATH,
                name="Clear Remaining Level 2 Room 1 Enemies",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Compass.value,
            ),
            BT.PickupGroundItemByModelID(model_ids=TORCH_MODEL_IDS,max_distance=10_000.0,timeout_ms=45_000,allow_unassigned=True,interaction_interval_ms=5000,aftercast_ms=100,log=True,),
            BT.VanquishNode(L2_TO_ROOM2_DROP,clear_area_radius=Range.Area.value, pause_on_combat=True),
            BT.DropBundle(log=True),
            BT.VanquishNode(
                L2_RETURN_TO_ROOM2_TORCH_PATH,
                name="Clear Route Back To Room 2 Torch",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
            ),
            BT.PickupGroundItemByModelID(model_ids=TORCH_MODEL_IDS,max_distance=10_000.0,timeout_ms=45_000,allow_unassigned=True,interaction_interval_ms=5000,aftercast_ms=100,log=True,),
            BT.VanquishNode(
                L2_ROOM2_PATH,
                name="Clear Level 2 Room 2",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
            ),
            BT.DropBundle(log=True),
            BT.VanquishNode([Vec2f(-4245.2, -2101.0)],
                name="Clear Level 2 Room 2",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
            ),
            BT.PickupGroundItemByModelID(model_ids=TORCH_MODEL_IDS,max_distance=10_000.0,timeout_ms=45_000,allow_unassigned=True,interaction_interval_ms=5000,aftercast_ms=100,log=True,),
            BrazierSequence("Level 2 Brazier Route 2", L2_BRAZIER_PART2),
            BT.DropBundle(log=True),
            BT.VanquishNode(
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
            BT.Wait(2_000),
        ],
    )


def CollectInsideReward() -> BehaviorTree:
    return BT.Sequence(
        name="Collect Inside Reward",
        children=[
            BT.TargetAgentByName(
                agent_name="Shandra",
                log=True,
            ),
            BT.InteractTargetAndSendDialog(
                dialog_id=SHANDRA_REWARD_DIALOG,
                multi_account=True,
                log=True,
            ),
        ],
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

def PrepareNextDungeonRun() -> BehaviorTree:
    reward_collected_inside = BT.Sequence(
        name="Restart After Inside Reward",
        children=[
            BT.IsQuestState(quest_id=LOST_SOULS_QUEST_ID, state="missing", log=True),
            BT.LogMessage(message="Reward already collected inside. Retaking Lost Souls.", module_name=MODULE_NAME),
            BT.MoveAndDialog(SHANDRA_APPROACH, SHANDRA_TAKE_DIALOG, pause_on_combat=False, multi_account=True, log=True),
            BT.WaitForActiveQuest(LOST_SOULS_QUEST_ID, timeout_ms=15_000),
            EnterShardsOfOrr(),
        ],
    )

    reward_not_collected_inside = BT.Sequence(
        name="Restart After Outside Reward",
        children=[
            BT.IsQuestState(quest_id=LOST_SOULS_QUEST_ID, state="complete", log=True),
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
            BT.IsQuestState(
                quest_id=LOST_SOULS_QUEST_ID,
                state="complete",
                log=True,
            ),
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

def RunLevel3() -> BehaviorTree:
    return BT.Sequence(
        name="Run Shards of Orr Level 3",
        children=[
            UseAvailableSummoningStone(),
            BT.MoveAndDialog(
                L3_ENTRY_BLESSING,
                dialog_id=DWARVEN_BLESSING_DIALOG,
                multi_account=True,
                log=True,
            ),
            BT.VanquishNode(
                L3_MAIN_PATH,
                name="Level 3 Main Route",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
            ),
            BT.VanquishNode(
                L3_BRIGANT_APPROACH,
                name="Level 3 Route Before Torch",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
            ),
            BT.VanquishNode(
                L3_PATH_TO_TORCH,
                name="Level 3 Route To Torch Chest",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
            ),
            BT.MoveAndInteractWithGadget(
                L3_TORCH_CHEST, pause_on_combat=False, log=True,
            ),
            BT.PickupGroundItemByModelID(model_ids=TORCH_MODEL_IDS,max_distance=10_000.0,timeout_ms=45_000,allow_unassigned=True,interaction_interval_ms=5000,aftercast_ms=100,log=True,),            BrazierSequence("Level 3 Brazier Route", L3_BRAZIERS),
            BT.DropBundle(log=True),
            BT.VanquishNode(
                L3_BRIGANT_KILL_PATH,
                name="Kill Level 3 Brigant",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
            ),
            BT.MoveAndInteractWithGadget(
                L3_BOSS_DOOR, pause_on_combat=False, log=True,
            ),
            BT.VanquishNode(
                L3_FENDI_PATH,
                name="Route To Fendi",
                flag_heroes_to_waypoint=False,
                clear_area_radius=Range.Spellcast.value,
            ),
            BT.WaitForClearEnemiesInArea(
                x=-16022.9,
                y=17889.9,
                radius=Range.Compass.value,
                allowed_alive_enemies=0,
                interact_interval_ms=750,
                stable_clear_ms=20_000,
                keep_player_near_center=True,
                center_tolerance=750.0,
                log=True,
            ),
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
            interaction_count=3,
            interaction_interval_ms=2000,
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