import os
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple
import random, time, math
import inspect
import PyInventory
from Py4GWCoreLib import *
import Py4GW
from Py4GWCoreLib import (
    Agent,
    Botting,
    ConsoleLog,
    Effects,
    GLOBAL_CACHE,
    Map,
    Player,
    Range,
    Routines,
    SharedCommandType,
    AgentArray,
    IniHandler,
)
from Py4GWCoreLib.botting_src.helpers import BottingHelpers
from Py4GW_widget_manager import get_widget_handler
from Sources.oazix.CustomBehaviors.primitives.botting.botting_helpers import BottingHelpers
from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Py4GWCoreLib.routines_src.Yield import Utils
from Py4GWCoreLib.routines_src.Yield import Yield

# ==================== CONFIGURATION ====================
BOT_NAME = "BDS bot"
MODULE_ALIASES = [
    "Shards of Orr",
    "SOO",
]

# Widgets you want to force-manage at startup.
# Edit these lists to choose which widgets to enable/disable.
WIDGETS_TO_ENABLE: tuple[str, ...] = (
    "LootManager",
    "CustomBehaviors",
    "ResurrectionScroll",
    "Return to outpost on defeat",
)
WIDGETS_TO_DISABLE: tuple[str, ...] = ()
_ALT_ONLY_DISABLE_WIDGETS: tuple[str, ...] = (os.path.splitext(os.path.basename(__file__))[0],)
_SCRIPT_DIR = os.path.dirname(__file__)

# Difficulty selection (default: HM)
_DIFFICULTY_SECTION = "BDS"
_DIFFICULTY_VAR = "use_hard_mode"
_use_hard_mode: bool = True
_difficulty_loaded: bool = False

# District randomizer (default: enabled)
_DISTRICT_SECTION = "BDS"
_DISTRICT_VAR = "randomize_district"
_randomize_district: bool = True
_district_loaded: bool = False

# ==================== BDS STATISTICS ====================
BDS_MODEL_IDS = list(range(1987, 2008))  # all BDS variants (domination â†’ channeling)

_bds_ini_path = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "BDS", "bds_settings.ini")
os.makedirs(os.path.dirname(_bds_ini_path), exist_ok=True)
_bds_ini = IniHandler(_bds_ini_path)

# In-memory session stats (leader only, reset on reload)
_session_bds_found: int = 0
_session_runs: int = 0
_bds_pre_snapshot: dict[int, int] = {}  # model_id -> count before chest open

_BDS_ICON_PATH = os.path.join(_SCRIPT_DIR, "BDS.png")

# ==================== MERCHANT SETTINGS ====================
_MERCHANT_SECTION = "BDS Merchant"
_ALT_SALVAGE_SECTION = "BDS Alt Salvage Kits"
_FIXED_ID_KITS_TARGET = 3
_FIXED_SALVAGE_KITS_TARGET = 10
_ALT_SALVAGE_TRIGGER_THRESHOLD = 2
_ALT_SALVAGE_POLL_TIMEOUT_MS = 200
_ALT_SALVAGE_POLL_MAX_TOTAL_MS = 10_000
_merchant_enabled: bool = False
_merchant_id_kits_target: int = 2
_merchant_salvage_kits_target: int = 5
_merchant_id_kits_target: int = _FIXED_ID_KITS_TARGET
_merchant_salvage_kits_target: int = _FIXED_SALVAGE_KITS_TARGET
_merchant_store_consumable_materials: bool = False
_merchant_sell_materials: bool = False
_merchant_sell_rare_mats: bool = False
_merchant_buy_ectos: bool = False
_merchant_ecto_threshold: int = 800_000
_merchant_alt_wait_ms: int = 90_000
_DEFAULT_ALT_SETTLE_WAIT_MS = 2000
_MAX_ALT_SETTLE_WAIT_MS = 5000
_merchant_alt_wait_ms: int = _DEFAULT_ALT_SETTLE_WAIT_MS
_POST_RETURN_TO_ARBOR_SETTLE_MS = 4000
_POST_WIDGET_REENABLE_SETTLE_MS = 2500
_merchant_loaded: bool = False

# ==================== BOT SETUP ====================
TEXTURE = _BDS_ICON_PATH

# Map IDs
Vloxs_Fall = 624
Arbor_Bay = 485
SoO_lvl1 = 581
SoO_lvl2 = 582
SoO_lvl3 = 583
Great_Temple_of_Balthazar = 248
EyeOfTheNorth = 642

# Quest IDs
LOST_SOULS_QUEST_ID = 0x324  # Lost Souls - abandon when in Vloxs Fall

# Dialog IDs
DWARVEN_BLESSING_DIALOG = 0x84
SHANDRA_TAKE_DIALOGS = 0x832401
SHANDRA_QUEST_REWARD_DIALOG = 0x832407

# Coordinates
FENDI_CHEST_POSITION = (-15800.98,16901.23)
SHANDRA_POSITION = (14067.01, -17253.24)

# ==================== GLOBAL VARIABLES ====================
bot = Botting(
    bot_name=BOT_NAME,
    upkeep_auto_combat_active=False,
    upkeep_auto_loot_active=True,
    upkeep_morale_active=True,
    upkeep_auto_inventory_management_active=True,
)

# ==================== CORE ROUTINE ====================
def farm_bds_routine(bot: Botting) -> None:
    
    # ===== INITIAL CONFIGURATION =====
    bot.Templates.Routines.UseCustomBehaviors(
        on_player_critical_death=BottingHelpers.botting_unrecoverable_issue,
        on_party_death=BottingHelpers.botting_unrecoverable_issue,
        on_player_critical_stuck=BottingHelpers.botting_unrecoverable_issue)
    # Register wipe callback
    bot.Events.OnPartyWipeCallback(lambda: OnPartyWipe(bot))
    

    
    # ===== START OF BOT =====
    bot.States.AddHeader("Startup - Widget Setup")
    bot.Properties.Enable("pause_on_danger")
    bot.States.AddCustomState(apply_widget_policy_step, "Apply widget policy")
    bot.States.AddCustomState(lambda: _gh_merchant_setup(leave_party=True), "GH Merchant Setup")
    bot.Templates.Aggressive()
    bot.Multibox.AbandonQuest(LOST_SOULS_QUEST_ID)
    bot.States.AddHeader("Startup - Party Setup")
    bot.Events.OnPartyMemberBehindCallback(lambda: bot.Templates.Routines.OnPartyMemberBehind())
    bot.Events.OnPartyMemberInDangerCallback(lambda: bot.Templates.Routines.OnPartyMemberInDanger())
    bot.Events.OnPartyMemberDeadBehindCallback(lambda: bot.Templates.Routines.OnPartyMemberDeathBehind())
    bot.Multibox.KickAllAccounts()
    bot.States.AddCustomState(lambda: _coro_travel_random_district(Vloxs_Fall), "Travel to Vlox's Falls")
    bot.Multibox.SummonAllAccounts()
    bot.Wait.ForTime(4000)
    bot.Multibox.InviteAllAccounts()
    bot.States.AddCustomState(_reenable_merchant_widgets, "Re-enable widgets (all in Vlox's Falls)")
    bot.Multibox.RestockAllPcons()
    bot.Multibox.RestockConset()
    bot.Multibox.RestockResurrectionScroll(250)


    
    # ===== START OF LOOP =====
    bot.States.AddHeader("Run Loop")
    _load_difficulty_setting()
    bot.Party.SetHardMode(_use_hard_mode)
    # Enable properties
    bot.Properties.Enable('auto_combat')
    bot.States.AddCustomState(_step_anchor, "Reset farm")  # anchor for secure return on wipe    
    # ===== GO TO DUNGEON =====
    bot.States.AddHeader("Go to Dungeon")
    bot.Move.XYAndExitMap(15505.38, 12460.59, target_map_id=Arbor_Bay)
    bot.Wait.UntilOnExplorable()
    bot.Wait.ForTime(2000)
    
    # First blessing in Arbor Bay
    bot.Move.XYAndInteractNPC(16327, 11607)
    bot.Wait.ForTime(4000)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(4000)
    bot.Multibox.UseAllConsumables()

    IS_REPATHING = False
    # Path to Shandra
    path = [
    (13455.43, 10678.00),
    (9850.00, 5025.00),
    (11207.11, 1872.32),
    #(11256.59, 1742.31),
    (10452.02, 178.50),
    #(10870.85, -3558.11),
    #(11736.00, 70.00),
    (10782.86, -3321.00),
    (8360.94, -6550.00),
    (10382.85, -12342.00),
    (10080.30, -13995.00),
    (10667.00, -16116.00),
    (10747.49, -17546.00),
    (11156.00, -17802.00),
]
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path)
    bot.Wait.UntilOutOfCombat()
    
    # ===== LOOP RESTART POINT =====
    bot.States.AddCustomState(loop_marker, "LOOP_RESTART_POINT")
    
    bot.States.AddCustomState(lambda: bot.Move.XY(12056.00,-17882), "Go to Shandra")
    # Take Shandra' quest
    bot.Move.XYAndInteractNPC((12056.00,-17882)[0], (12056.00,-17882)[1])
    bot.Multibox.SendDialogToTarget(SHANDRA_TAKE_DIALOGS)
    bot.Wait.ForTime(4000)
    
    # Enter the dungeon
    bot.Move.XY(11177, -17683)
    bot.Move.XY(10218, -18864)
    bot.Move.XY(9519, -19968)
    bot.Move.XY(9240.07, -20260.95)


    # Wait for change to Level 1
    bot.States.AddCustomState(lambda: wait_for_map_change(SoO_lvl1, 60), "Wait for Level 1")
    bot.Wait.ForTime(2000)
    

    # =========================
    #           Level 1
    # =========================
    bot.States.AddHeader("Level 1 - Entry and Blessing")
    
    # First blessing Level 1
    bot.States.AddCustomState(lambda: S_BlacklistModels(TORCH_MODEL_IDS), "Blacklist torchs")
    bot.Multibox.UseAllConsumables()
    bot.Move.XY(-11686, 10427)
    bot.Move.XYAndInteractNPC(-11686, 10427)
    bot.Wait.ForTime(2000)    
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)    

    
    # Use consumables
    bot.States.AddCustomState(UseSummons, "Use Summons")
    bot.Templates.Aggressive()

    path_before_bridgant = [
        (-11685.5,10475.5),
        (-10682.6,9841.2),
        (-9670.9,9744.2),
        (-8661.9,9975.7),
        (-7653.5,10063.4),
        (-6652.0,10156.2),
        (-5646.1,10717.7),
        (-4642.3,11376.3),
        (-3640.8,11984.6),
        (-2634.2,12702.1),
        (-1630.8,13315.2),
        (-628.5,14075.6),
        (379.8,14700.8),
        (1384.7,15324.0),
        (2394.5,15950.3),
        (3409.5,15710.4),
        (4157.9,14705.9),
        (5089.4,13698.1),
        (6090.8,13172.6),
        (7091.1,13482.8),
        (8093.3,13148.6),
        (8503.9,12143.5),
        (7496.9,11676.0),
        (6494.3,10739.2)]
    bot.Templates.Aggressive()
    bot.Wait.UntilOutOfCombat()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_before_bridgant)

    bot.States.AddHeader("Level 1 - Secure Return Checkpoint 1")
    bot.States.AddCustomState(_step_anchor, "Secure return - L1")  # anchor for secure return on wipe

    path_before_door= [
        (9196.0,11484.4),
        (10196.0,12469.4),
        (11198.7,13401.8),
        (12201.3,14284.4),
        (13202.8,15176.3),
        (14207.0,16116.2),
        (15208.8,16871.6),
        (16213.2,16417.3),
        (16643.4,15416.6),
        (16994.9,14410.6),
        (17115.6,13405.6),
        (16689.2,12400.4),
        ]
    bot.Templates.Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_before_door)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(15953, 11902)
    bot.States.AddHeader("Level 1 - Secure Return Checkpoint 2")
    bot.States.AddCustomState(_step_anchor, "Secure return 1 - L1")  # anchor for secure return on wipe    
    
    path_before_door2 = [    
        (15927.4,11684.7),
        (16037.8,10679.9),
        (15761.1,9679.7),
        (15289.5,8672.6),
        (14447.3,7672.0),
        (14526.2,6664.2),
        (14951.6,5657.9),
    ]

    bot.Templates.Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_before_door2)
    bot.Wait.UntilOutOfCombat()
    # Door gadget
    bot.Move.XY(15100, 5443)
    bot.States.AddCustomState(bot.Move.XYAndInteractGadget(15100.00, 5443),"Interact")

    # Path after door
    path_after_door = [
        (15364.9,4858.7),
        (15689.5,3857.7),
        (16026.7,2857.1),
        (17030.7,2262.6),
        (18035.7,1888.8),
        (19037.1,1384.6),
        (19679.2,1009.5),
        (20181.6,1203.7),
        (20400.5,1300),


    ]
    bot.Templates.Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_after_door)
    bot.Wait.UntilOutOfCombat()

    # Wait for change to Level 2
    bot.States.AddCustomState(lambda: wait_for_map_change(SoO_lvl2, 60), "Wait for Level 2")
    bot.Wait.ForTime(2000)

    # =========================
    #          Level 2
    # =========================
    bot.States.AddHeader("Level 2 - Entry and Blessing")
    # --- Entry + Blessing ---
    bot.Move.XY(-14076, -19457)
    bot.Wait.UntilOutOfCombat()
    bot.Move.XY(-14076, -19457)
    bot.Move.XYAndInteractNPC(-14076, -19457)
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(2000)
    bot.States.AddHeader("Level 2 - Secure Return Checkpoint")
    bot.States.AddCustomState(_step_anchor, "Secure return - L2")  # anchor for secure return on wipe
 
    # Use consumables
    bot.States.AddCustomState(UseSummons, "Use Summons")
    bot.Multibox.UseAllConsumables()
    bot.Templates.Aggressive()
    # --- Path to torch area (atomisÃ©) ---
    path_before_torch = [
        (-14977.9,-16480.2),
        (-15985.6,-16838.1),
        (-16985.9,-16929.4),
    ]
    bot.Templates.Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_before_torch)
    bot.Wait.UntilOutOfCombat()

    # --- Torch chest + pickup ---
    bot.States.AddCustomState(bot.Move.XYAndInteractGadget(-14709, -16548), "Open Torch Chest")

    bot.States.AddCustomState(pickup_torch, "Pickup Torch")
    # --- Move to brazier sequence 1 (avec drop bundle) ---
    bot.Move.XY(-11002, -17001)
    bot.States.AddCustomState(lambda: drop_bundle_safe(2, 250), "Drop bundle")



    bot.Move.XY(-9259, -17322)
    bot.Move.XY(-9971.23, -17633.08)
    bot.Move.XY(-11136.85, -17201.66)
    bot.States.AddCustomState(pickup_torch, "Pickup Torch")

    bot.Move.XY(-11030.3,-17474.0)
    bot.Move.XY(-11303, -14596)

    # --- Brazier sequence 1 ---
    bot.States.AddHeader("Level 2 - Brazier Route 1")
    run_brazier_sequence([(float(x), float(y)) for x, y in BDS_L2_PART1])
    bot.States.AddHeader("Level 2 - Clear Remaining Enemies")
    bot.States.AddCustomState(_log_cleaning_room, "Making sure no enemys are left")
    bot.States.AddCustomState(lambda: drop_bundle_safe(2, 250), "Drop bundle")
    bot.Move.FollowAutoPath(BDS_L2_CLEANING)
    bot.States.AddCustomState(pickup_torch, "Pickup Torch")

    bot.States.AddHeader("Level 2 - Move to Next Room")
    bot.Move.XY(-11061.1,-7578.5)
    bot.States.AddCustomState(lambda: drop_bundle_safe(2, 250), "Drop bundle")
    
    bot.Move.XY(-10958.2,-4529.5)
    bot.Move.XY(-11690.64, -3802.55)
    bot.Move.XY(-10958.2,-4529.5)
    bot.Move.XY(-11032.11, -5389.71)
    bot.Move.XY(-11090.10, -6890.14)
    bot.States.AddCustomState(pickup_torch, "Pickup Torch")

    path_room2 = [
    (-11013.7,-6381.7),
    (-11081.9,-5378.8),
    (-10071.6,-4396.5),
    (-9069.4,-4301.1),
    (-8066.1,-4222.4),
    (-7058.8,-4191.0)]
    bot.Templates.Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_room2)
    bot.Wait.UntilOutOfCombat()



    bot.States.AddCustomState(lambda: drop_bundle_safe(2, 250), "Drop bundle")
    bot.Move.XY(-4245.2,-2101)
    bot.States.AddCustomState(pickup_torch, "Pickup Torch")


    # --- Brazier sequence 2 ---
    bot.States.AddHeader("Level 2 - Brazier Route 2")

    run_brazier_sequence([(float(x), float(y)) for x, y in BDS_L2_PART2])

    bot.States.AddCustomState(lambda: drop_bundle_safe(2, 250), "Drop bundle")
    bot.Move.XY(-6798.8, -2436.4)

    bot.States.AddHeader("Level 2 - Move to Dungeon Lock")
    path_after_second_room = [
    (-9069.4,-4301.1),
    (-10071.6,-4396.5),
    (-11106.6,-4747.1),
    (-10970.9,-5754.5),
    (-11033.4,-6755.6),
    (-11318.0,-7767.2),
    (-12320.7,-8417.1),
    (-13324.0,-8649.0),
    (-14326.3,-8773.0),
    (-15331.0,-8905.6),
    (-16335.1,-9004.5),
        

    ]
    bot.Templates.Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_after_second_room)
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("Level 2 - Open Door")
    bot.Move.XY(-18725, -9171)
    bot.States.AddCustomState(bot.Move.XYAndInteractGadget(-18725, -9171), "Open Door")
    bot.Move.XY(-18610, -8636)
    bot.Move.XY(-19571.61, -8459.00)
    bot.States.AddCustomState(lambda: wait_for_map_change(SoO_lvl3, 60), "Wait for Level 3")
    bot.Wait.ForTime(2000)

    # =========================
    #           Level 3
    # =========================
    bot.States.AddHeader("Level 3 - Entry and Blessing")
    bot.Properties.Enable("pause_on_danger")
    # --- Blessing ---
    bot.Move.XY(17544, 18810)
    bot.Move.XYAndInteractNPC(17544, 18810)
    bot.Wait.ForTime(2000)    
    bot.Multibox.SendDialogToTarget(DWARVEN_BLESSING_DIALOG)
    bot.Wait.ForTime(2000) 
    bot.States.AddHeader("Level 3 - Secure Return Checkpoint")
    bot.States.AddCustomState(_step_anchor, "Secure return 1 - L3")
    # Use consumables

    bot.States.AddCustomState(UseSummons, "Use Summons")
    bot.Multibox.UseAllConsumables()
    bot.Templates.Aggressive()

    bot.States.AddHeader("Level 3 - Clear Main Path")
    path_before_flag = [
        (17544.5,18530.2),
        (17231.2,17523.3),
        (16811.3,16513.4),
        (15803.0,17071.6),
        (15004.8,18075.5),
        (13998.4,18866.7),
        (12990.9,19299.5),
        (11988.8,19353.2),
        (10986.4,19188.9),
        (9985.7,18719.2),
        (9402.1,17715.6),
        (9076.9,17383.4),
        (9133.0,16373.0),
        (8496.5,15367.3),
        (7978.0,14357.9),
        (7105.7,13350.9),
        (6236.1,12349.0),
        (5524.4,11344.1),
        (4813.8,10340.7),
        (4095.0,9332.7),
        (3091.4,8424.8),
        (2078.2,8286.5),
        (1926,5848),
        (1069.7,8045.3),
        (619.8,7044.0),
        (-385.8,6478.3),
        (-1123.5,7481.9)]
    bot.Templates.Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_before_flag)
    bot.Wait.UntilOutOfCombat()

    bot.States.AddCustomState(_reset_l3_boss_route_flag, "Reset L3 boss route flag") #ICI CE TROUVE LE SHRINE DONC SI JE MEURT APRES JE REVIENS ICI DONC MAIS SI JE MEURT AU BOSS C4EST ICI QUE JE REVIS
        
    path2=[(-2964.1,7302.1),
        (-3139.7,7022.7),
        (-4152.0,6469.6),
        (-5154.0,5969.0),
        (-5837.7,4968.0),
        (-5832.1,3954.0),
        (-6838.3,3495.2),
        (-7845.7,4397.5),
        (-8049.0,5403.5),
        (-9049.9,5289.2),
        (-10051.1,4604.6),
        (-11057.4,4039.1),
        (-10381.7,3037.7),
    ]
    bot.Templates.Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path2)
    bot.Wait.UntilOutOfCombat()

    bot.States.AddHeader("Level 3 - Path to Torch")
    path_to_take_torch = [
        (-4723.00, 6703.00),
        (-1280.00, 7880.00),
        (3089.73, 8511.00),
        (4963.00, 9974.00),
        (9918.64, 19108.00),
        (14709.00, 19526.00),
        (16111.00, 17556.00),
    ]

    bot.Templates.Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_to_take_torch)
    bot.Wait.UntilOutOfCombat()

    bot.States.AddCustomState(bot.Move.XYAndInteractGadget(16111.00, 17556), "Open Torch Chest")
    bot.States.AddCustomState(pickup_torch, "Pickup Torch")

    # --- Brazier sequence ---
    bot.States.AddHeader("Level 3 - Brazier Route")
    bot.States.AddCustomState(lambda: _toggle_wait_for_party(False), "Disable WaitIfPartyMemberTooFar")    
    run_brazier_sequence([(float(x), float(y)) for x, y in BDS_L3])
    bot.States.AddCustomState(lambda: drop_bundle_safe(2, 250), "Drop bundle")
    bot.States.AddCustomState(lambda: _toggle_wait_for_party(True), "Enable WaitIfPartyMemberTooFar")   
    bot.States.AddHeader("Level 3 - Kill Brigant")
    bot.Move.XY(-11878.79, 2166.51)
    bot.Move.XY(-9686.32, 2632)
    bot.States.AddCustomState(_set_l3_boss_route_flag, "Set L3 boss route flag")
    bot.States.AddHeader("Level 3 - Boss Checkpoint")
    bot.States.AddCustomState(_step_anchor, "Secure return boss - L3")
    bot.States.AddHeader("Level 3 - Open Boss Door")
    bot.Move.XY(-9252.32, 6396.40)
    bot.States.AddCustomState(bot.Move.XYAndInteractGadget(-9252.32, 6396.40), "Open Door")

    bot.States.AddHeader("Level 3 - Path to Fendi")
    # --- Boss path ---
    path_bds = [
        (-8871.19, 6152.95),
        (-9326.33, 6862.55),
        (-10044.56, 7921.78),
        (-8408.54, 9475.41),
        (-10049.41, 11259.31),
        (-11381.15, 12387.01),
        (-12304.50, 13319.24),
        (-14736.33, 15054.21),
        (-15162.24, 15579.30),
    ]

    bot.Templates.Aggressive()
    if not IS_REPATHING:
        bot.Move.FollowAutoPath(path_bds)
    bot.States.AddCustomState(resolve_fendi_fight, "Resolve Fendi Fight")
    bot.States.AddHeader("Final Chest")
        # ===== OPEN FINAL CHEST =====
    bot.Move.XY(-15800.98,16901.23)
    bot.States.AddCustomState(_snapshot_bds_before_chest, "BDS Pre-Chest Snapshot")
    bot.Move.XY(-15800.98,16901.23) 
    bot.States.AddCustomState(open_fendi_chest, "Open Chest (All Accounts)")
    bot.States.AddCustomState(_record_bds_after_loot, "Record BDS Stats After Loot")
    bot.States.AddHeader("Quest Turn-In and Reset")
    bot.States.AddCustomState(lambda: Search_and_talk_with_Shandra(bot), "Find Shandra and talk")
    bot.Wait.ForTime(5000)
    bot.Multibox.SendDialogToTarget(SHANDRA_QUEST_REWARD_DIALOG)
    bot.Wait.ForTime(4000)
    bot.States.AddCustomState(_verify_reward_taken_from_quest_log, "Verify reward from quest log")

    
    # ===== NEXT RUN =====
    bot.Wait.ForMapToChange(target_map_name="Arbor Bay")
    bot.States.AddCustomState(_gh_merchant_setup_if_inventory_full, "GH Merchant if inventory full")
    bot.States.AddCustomState(_gh_merchant_setup_for_alt_salvage_threshold, "GH Merchant if alt salvage kits are low")
    bot.States.AddCustomState(lambda: _post_return_flow(bot), "Post-return quest handling")
    
    # ===== LOOP =====
    bot.States.JumpToStepName("LOOP_RESTART_POINT")
# ==================== CUSTOM HELPERS ====================


# --- Merchant Setup and Inventory Helpers ---

def _load_merchant_settings() -> None:
    global _merchant_enabled, _merchant_id_kits_target, _merchant_salvage_kits_target, _merchant_store_consumable_materials, _merchant_sell_materials, _merchant_sell_rare_mats, _merchant_buy_ectos, _merchant_ecto_threshold, _merchant_alt_wait_ms, _merchant_loaded
    if _merchant_loaded:
        return
    _merchant_enabled = _bds_ini.read_bool(_MERCHANT_SECTION, "enabled", False)
    _merchant_id_kits_target = _bds_ini.read_int(_MERCHANT_SECTION, "id_kits_target", _FIXED_ID_KITS_TARGET)
    _merchant_salvage_kits_target = _bds_ini.read_int(_MERCHANT_SECTION, "salvage_kits_target", _FIXED_SALVAGE_KITS_TARGET)
    _merchant_store_consumable_materials = _bds_ini.read_bool(_MERCHANT_SECTION, "store_consumable_materials", False)
    _merchant_sell_materials = _bds_ini.read_bool(_MERCHANT_SECTION, "sell_materials", False)
    _merchant_sell_rare_mats = _bds_ini.read_bool(_MERCHANT_SECTION, "sell_rare_mats", False)
    _merchant_buy_ectos = _bds_ini.read_bool(_MERCHANT_SECTION, "buy_ectos", False)
    _merchant_ecto_threshold = _bds_ini.read_int(_MERCHANT_SECTION, "ecto_threshold", 800_000)
    _merchant_alt_wait_ms = max(0, min(_MAX_ALT_SETTLE_WAIT_MS, _bds_ini.read_int(_MERCHANT_SECTION, "alt_wait_ms", _DEFAULT_ALT_SETTLE_WAIT_MS)))
    _merchant_loaded = True


def _save_merchant_settings() -> None:
    _bds_ini.write_key(_MERCHANT_SECTION, "enabled", str(_merchant_enabled))
    _bds_ini.write_key(_MERCHANT_SECTION, "id_kits_target", str(_merchant_id_kits_target))
    _bds_ini.write_key(_MERCHANT_SECTION, "salvage_kits_target", str(_merchant_salvage_kits_target))
    _bds_ini.write_key(_MERCHANT_SECTION, "store_consumable_materials", str(_merchant_store_consumable_materials))
    _bds_ini.write_key(_MERCHANT_SECTION, "sell_materials", str(_merchant_sell_materials))
    _bds_ini.write_key(_MERCHANT_SECTION, "sell_rare_mats", str(_merchant_sell_rare_mats))
    _bds_ini.write_key(_MERCHANT_SECTION, "buy_ectos", str(_merchant_buy_ectos))
    _bds_ini.write_key(_MERCHANT_SECTION, "ecto_threshold", str(_merchant_ecto_threshold))
    _bds_ini.write_key(_MERCHANT_SECTION, "alt_wait_ms", str(_merchant_alt_wait_ms))


def _find_npc_xy_by_name(name_fragment: str, max_dist: float = 15000.0):
    """Find the nearest NPC whose display name contains name_fragment."""
    npcs = AgentArray.GetNPCMinipetArray()
    npcs = AgentArray.Filter.ByDistance(npcs, Player.GetXY(), max_dist)
    for npc_id in npcs:
        npc_name = Agent.GetNameByID(int(npc_id))
        if name_fragment.lower() in npc_name.lower():
            return Agent.GetXY(int(npc_id))
    return None


def _count_model_in_inventory(model_id: int) -> int:
    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    count = 0
    for item_id in item_array:
        if int(GLOBAL_CACHE.Item.GetModelID(item_id)) == int(model_id):
            count += max(1, int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)))
    return count


def _account_key(email: str) -> str:
    return email.replace("@", "_at_").replace(".", "_")


def _write_local_salvage_kit_count() -> None:
    from Py4GWCoreLib.enums_src.Model_enums import ModelID as _ModelID

    email = Player.GetAccountEmail()
    salvage_count = int(GLOBAL_CACHE.Inventory.GetModelCount(_ModelID.Salvage_Kit.value))
    _bds_ini.write_key(_ALT_SALVAGE_SECTION, _account_key(email), str(salvage_count))


def _request_alt_salvage_kit_counts() -> Generator:
    my_email = Player.GetAccountEmail()
    alt_accounts = [acc for acc in GLOBAL_CACHE.ShMem.GetAllAccountData() if acc.AccountEmail != my_email]
    for acc in alt_accounts:
        _bds_ini.write_key(_ALT_SALVAGE_SECTION, _account_key(acc.AccountEmail), str(-1))

    pending_accounts = alt_accounts
    max_attempts = max(1, _ALT_SALVAGE_POLL_MAX_TOTAL_MS // max(1, _ALT_SALVAGE_POLL_TIMEOUT_MS))
    for _attempt in range(max_attempts):
        if not pending_accounts:
            break

        for acc in pending_accounts:
            GLOBAL_CACHE.ShMem.SendMessage(
                my_email,
                acc.AccountEmail,
                SharedCommandType.MerchantItems,
                (0, 0, 0, 0),
                ("report_salvage_kits", _bds_ini_path, _ALT_SALVAGE_SECTION, _account_key(acc.AccountEmail)),
            )

        yield from Routines.Yield.wait(_ALT_SALVAGE_POLL_TIMEOUT_MS)
        pending_accounts = [
            acc for acc in pending_accounts
            if _bds_ini.read_int(_ALT_SALVAGE_SECTION, _account_key(acc.AccountEmail), -1) < 0
        ]

    if pending_accounts:
        pending_names = [acc.AgentData.CharacterName or acc.AccountEmail for acc in pending_accounts]
        ConsoleLog(
            BOT_NAME,
            f"[Merchant] No salvage count reply after {max_attempts} attempts ({_ALT_SALVAGE_POLL_MAX_TOTAL_MS} ms max) from: {', '.join(pending_names)}. Skipping them this check.",
            Py4GW.Console.MessageType.Warning,
        )


def _alts_need_salvage_restock() -> tuple[bool, list[str], list[str]]:
    my_email = Player.GetAccountEmail()
    ini_reader = IniHandler(_bds_ini_path)
    low_accounts: list[str] = []
    unknown_accounts: list[str] = []
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if acc.AccountEmail == my_email:
            continue
        count = ini_reader.read_int(_ALT_SALVAGE_SECTION, _account_key(acc.AccountEmail), -1)
        char_name = acc.AgentData.CharacterName or acc.AccountEmail
        if count < 0:
            unknown_accounts.append(char_name)
            continue
        if count < _ALT_SALVAGE_TRIGGER_THRESHOLD:
            low_accounts.append(f"{char_name} ({count})")
    return len(low_accounts) > 0, low_accounts, unknown_accounts


def _coro_sell_rare_mats_at_trader(x: float, y: float, model_ids: set[int]) -> Generator:
    """Sell rare material items (by model ID) to the trader at (x, y), one unit at a time.
    Bypasses SellMaterialsAtTrader which skips IsRareMaterial items."""
    yield from Routines.Yield.Movement.FollowPath([(x, y)])
    yield from Routines.Yield.wait(100)
    yield from Routines.Yield.Agents.InteractWithAgentXY(x, y)
    yield from Routines.Yield.wait(1000)

    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    sold_total = 0
    for item_id in item_array:
        if int(GLOBAL_CACHE.Item.GetModelID(item_id)) not in model_ids:
            continue
        stack_qty = int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))
        while stack_qty > 0:
            quoted = yield from Routines.Yield.Merchant._wait_for_quote(
                GLOBAL_CACHE.Trading.Trader.RequestSellQuote, item_id,
                timeout_ms=750, step_ms=10)
            if quoted <= 0:
                break
            GLOBAL_CACHE.Trading.Trader.SellItem(item_id, quoted)
            new_qty = yield from Routines.Yield.Merchant._wait_for_stack_quantity_drop(
                item_id, stack_qty, timeout_ms=750, step_ms=10)
            if new_qty >= stack_qty:
                break
            sold_total += stack_qty - new_qty
            stack_qty = new_qty
    ConsoleLog(BOT_NAME, f"[Merchant] Sold {sold_total} rare material unit(s) at trader")


def _get_leftover_material_item_ids(batch_size: int = 10) -> list[int]:
    """Return item IDs of common (non-rare) material stacks with quantity < batch_size."""
    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    leftovers: list[int] = []
    for item_id in item_array:
        if not GLOBAL_CACHE.Item.Type.IsMaterial(item_id):
            continue
        if GLOBAL_CACHE.Item.Type.IsRareMaterial(item_id):
            continue
        qty = int(GLOBAL_CACHE.Item.Properties.GetQuantity(item_id))
        if 0 < qty < batch_size:
            leftovers.append(int(item_id))
    return leftovers


def _disable_widgets_on_alts_only(widget_names: tuple[str, ...]) -> Generator:
    if not widget_names:
        yield
        return

    my_email = Player.GetAccountEmail()
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        account_email = str(getattr(account, "AccountEmail", "") or "")
        if not account_email or account_email == my_email:
            continue
        for widget_name in widget_names:
            GLOBAL_CACHE.ShMem.SendMessage(
                my_email,
                account_email,
                SharedCommandType.DisableWidget,
                (0, 0, 0, 0),
                (widget_name, "", "", ""),
            )
    yield from Routines.Yield.wait(500)
def _get_material_item_ids_by_models(selected_models: set[int]) -> list[int]:
    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    result: list[int] = []
    for item_id in item_array:
        if not GLOBAL_CACHE.Item.Type.IsMaterial(item_id):
            continue
        if GLOBAL_CACHE.Item.Type.IsRareMaterial(item_id):
            continue
        model_id = int(GLOBAL_CACHE.Item.GetModelID(item_id))
        if model_id in selected_models:
            result.append(int(item_id))
    return result


def _coro_deposit_crafting_materials_to_storage(selected_models: set[int]) -> Generator:
    if not selected_models:
        yield
        return
    if not GLOBAL_CACHE.Inventory.IsStorageOpen():
        GLOBAL_CACHE.Inventory.OpenXunlaiWindow()
        yield from Routines.Yield.wait(1000)
    if not GLOBAL_CACHE.Inventory.IsStorageOpen():
        ConsoleLog(BOT_NAME, "[Merchant] Storage not open; skipping crafting material deposit", Py4GW.Console.MessageType.Warning)
        yield
        return

    item_ids = _get_material_item_ids_by_models(selected_models)
    if not item_ids:
        ConsoleLog(BOT_NAME, "[Merchant] No crafting materials to deposit")
        yield
        return

    for item_id in item_ids:
        GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
        yield from Routines.Yield.wait(40)

    ConsoleLog(BOT_NAME, f"[Merchant] Deposited {len(item_ids)} crafting material stack(s) to storage")
    yield


_SCROLL_MODEL_IDS = {5594, 5595, 5611, 5853, 5975, 5976, 21233}
_SCROLL_MODEL_FILTER = "5594,5595,5611,5853,5975,5976,21233"


def _coro_sell_scrolls(mx: float, my: float) -> Generator:
    """Sell XP/insight scrolls to the GH merchant."""
    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    sell_ids = [int(item_id) for item_id in item_array
                if int(GLOBAL_CACHE.Item.GetModelID(item_id)) in _SCROLL_MODEL_IDS]
    if not sell_ids:
        ConsoleLog(BOT_NAME, "[Merchant] No scrolls to sell in bags 1-4")
        storage_hits = [(mid, GLOBAL_CACHE.Inventory.GetModelCountInStorage(mid))
                        for mid in _SCROLL_MODEL_IDS]
        storage_hits = [(mid, cnt) for mid, cnt in storage_hits if cnt > 0]
        if storage_hits:
            ConsoleLog(BOT_NAME, f"[Merchant] WARNING: scrolls found in STORAGE (InventoryPlus deposited them): {storage_hits}")
        yield
        return
    for item_id in sell_ids:
        val = GLOBAL_CACHE.Item.Properties.GetValue(item_id)
        qty = GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)
        mid = GLOBAL_CACHE.Item.GetModelID(item_id)
        ConsoleLog(BOT_NAME, f"[Merchant] Scroll queued: item_id={item_id} model={mid} qty={qty} value={val}")
    yield from bot.Move._coro_xy_and_interact_npc(mx, my, "GH Merchant (scrolls)")
    yield from Routines.Yield.wait(1200)
    ConsoleLog(BOT_NAME, f"[Merchant] Selling {len(sell_ids)} scroll(s) at merchant")
    yield from Routines.Yield.Merchant.SellItems(sell_ids, log=True)
    yield from Routines.Yield.wait(300)


def _coro_sell_nonsalvageable_golds(mx: float, my: float) -> Generator:
    """Sell all identified, non-salvageable gold items (e.g. anniversary weapons) to the GH merchant."""
    bag_list = GLOBAL_CACHE.ItemArray.CreateBagList(1, 2, 3, 4)
    item_array = GLOBAL_CACHE.ItemArray.GetItemArray(bag_list)
    sell_ids = []
    for item_id in item_array:
        _, rarity = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
        if rarity != "Gold":
            continue
        if not GLOBAL_CACHE.Item.Usage.IsIdentified(item_id):
            continue
        if GLOBAL_CACHE.Item.Usage.IsSalvageable(item_id):
            continue
        sell_ids.append(int(item_id))
    if not sell_ids:
        ConsoleLog(BOT_NAME, "[Merchant] No non-salvageable gold items to sell")
        yield
        return
    yield from bot.Move._coro_xy_and_interact_npc(mx, my, "GH Merchant (non-salvageable golds)")
    yield from Routines.Yield.wait(1200)
    ConsoleLog(BOT_NAME, f"[Merchant] Selling {len(sell_ids)} non-salvageable gold item(s) at merchant")
    yield from Routines.Yield.Merchant.SellItems(sell_ids, log=True)
    yield from Routines.Yield.wait(300)


_MERCHANT_MANAGED_WIDGETS = ("InventoryPlus", "CustomBehaviors")
_PRETRAVEL_DISABLE_WIDGETS = ("InventoryPlus",)  # disable before GH travel so deposit cycle doesn't run on GH entry


def _disable_merchant_widgets() -> Generator:
    """Disable InventoryPlus and CustomBehaviors on leader + all alts during GH merchant ops."""
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler as _get_wh
    ConsoleLog(BOT_NAME, "[Merchant] Disabling managed widgets on all accounts")
    wh = _get_wh()
    for name in _MERCHANT_MANAGED_WIDGETS:
        wh.disable_widget(name)
    _my_email = Player.GetAccountEmail()
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if acc.AccountEmail != _my_email:
            for name in _MERCHANT_MANAGED_WIDGETS:
                GLOBAL_CACHE.ShMem.SendMessage(
                    _my_email, acc.AccountEmail,
                    SharedCommandType.DisableWidget, (0, 0, 0, 0), (name, "", "", ""),
                )
    ConsoleLog(BOT_NAME, f"[Merchant] Disabled {_MERCHANT_MANAGED_WIDGETS} on all accounts")
    yield

SHANDRA_TAKE_DIALOGS = 0x832401
SHANDRA_QUEST_REWARD_DIALOG = 0x832407
SHANDRA_QUEST_ID = 0x324

def _move_to(x: float, y: float, tolerance: float = 180.0, max_tries: int = 60):
    Player.Move(x, y)

    for _ in range(max_tries):
        px, py = Player.GetXY()
        dist = Utils.Distance((px, py), (x, y))

        if dist <= tolerance:
            return True

        yield from Routines.Yield.wait(100)

    return False


def _wait_for_map(map_name: str, max_tries: int = 120):
    for _ in range(max_tries):
        if Map.GetMapName() == map_name:
            return True
        yield from Routines.Yield.wait(500)
    return False

def _verify_reward_taken_from_quest_log() -> Generator:
    global SHANDRA_REWARD_PENDING

    quest_ids = Quest.GetQuestLogIds()

    if SHANDRA_QUEST_ID not in quest_ids:
        SHANDRA_REWARD_PENDING = True
        ConsoleLog(BOT_NAME, "[FLAG] Reward confirmed: quest no longer in quest log", log=True)
    else:
        SHANDRA_REWARD_PENDING = False
        ConsoleLog(BOT_NAME, "[FLAG] Reward NOT confirmed: quest still present in quest log", log=True)

    yield

# --- Quest Recovery and Guild Hall Flow ---

def Search_and_talk_with_Shandra(bot: Botting):
    npc_name = "Crewmember Shandra"

    ConsoleLog(BOT_NAME, "[Shandra] Start quest take", log=True)

    for attempt in range(1, 21):
        ConsoleLog(BOT_NAME, f"[Shandra] Search {npc_name} attempt {attempt}/20", log=True)

        agent_id = find_nearest_npc_by_name(npc_name, 2000.0)

        if agent_id:
            ConsoleLog(BOT_NAME, f"[Shandra] Found {npc_name} agent_id={agent_id}", log=True)

            x, y = Agent.GetXY(agent_id)
            ConsoleLog(BOT_NAME, f"[Shandra] Move to ({x}, {y})", log=True)

            for i in range(150):
                if i % 10 == 0:
                    Player.Move(x, y)

                px, py = Player.GetXY()
                dist = Utils.Distance((px, py), (x, y))

                if dist < 150:
                    ConsoleLog(BOT_NAME, "[Shandra] Arrived near Shandra", log=True)
                    break

                yield from Routines.Yield.wait(100)
            else:
                ConsoleLog(BOT_NAME, "[Shandra] Could not reach Shandra", log=True)
                yield
                return

            Player.ChangeTarget(agent_id)
            yield from Routines.Yield.wait(500)

            current_target = Player.GetTargetID()
            ConsoleLog(BOT_NAME, f"[Shandra] Current target = {current_target}", log=True)

            Player.Interact(agent_id)
            yield from Routines.Yield.wait(800)

            Player.ChangeTarget(agent_id)
            yield from Routines.Yield.wait(500)

            Player.Interact(agent_id)
            yield from Routines.Yield.wait(800)

            ConsoleLog(BOT_NAME, "[Shandra] Quest/Reward taken", log=True)
            yield
            return

        yield from Routines.Yield.wait(500)

def find_nearest_npc_by_name(name_fragment: str, max_dist: float = 2000.0) -> int:
    """Find nearest NPC whose name contains name_fragment."""
    player_pos = Player.GetXY()

    npcs = AgentArray.GetNPCMinipetArray()
    npcs = AgentArray.Filter.ByDistance(npcs, player_pos, max_dist)
    npcs = AgentArray.Sort.ByDistance(npcs, player_pos)

    for npc_id in npcs:
        npc_id = int(npc_id)

        try:
            npc_name = Agent.GetNameByID(npc_id)
        except Exception:
            continue

        if name_fragment.lower() in npc_name.lower():
            return npc_id

    return 0

def _interact_with_Shandra(bot: Botting, dialog_id: int, tolerance: float = 220.0):
    npc_name = "Crewmember Shandra"

    agent_id = find_nearest_npc_by_name(npc_name, 2000.0)
    if not agent_id:
        ConsoleLog(BOT_NAME, f"[Shandra] {npc_name} not found nearby", log=True)
        return False

    x, y = Agent.GetXY(agent_id)
    ConsoleLog(BOT_NAME, f"[Shandra] Found {npc_name} at ({x}, {y}) agent_id={agent_id}", log=True)

    ok = yield from _move_to(x, y, tolerance=tolerance)
    if not ok:
        ConsoleLog(BOT_NAME, "[Shandra] Impossible to approach Shandra", log=True)
        return False

    Player.ChangeTarget(agent_id)
    yield from Routines.Yield.wait(800)
    Player.Interact(agent_id)
    yield from Routines.Yield.wait(800)
    Player.SendDialog(dialog_id)
    yield from Routines.Yield.wait(1500)

    return True

def _recover_reward_and_retake_quest(bot: Botting) -> Generator:
    global SHANDRA_REWARD_PENDING

    ConsoleLog(BOT_NAME, "[RECOVERY] Late reward flow -> start", log=True)

    # 1) Reward Shandra in Sparkfly
    if Map.GetMapName() != "Arbor Bay":
        ConsoleLog(BOT_NAME, f"[RECOVERY] Mauvaise map pour reward: {Map.GetMapName()}", log=True)
        yield
        return

    ok = yield from _interact_with_Shandra(bot, SHANDRA_QUEST_REWARD_DIALOG)
    if not ok:
        ConsoleLog(BOT_NAME, "[RECOVERY] Reward Shandra failed", log=True)
        yield
        return


    # 2) Go to dungeon entrance
    for x, y in [
        (11177.00, -17683.00),(10218.00, -18864.00),(9519.00, -19968.00)]:
        ok = yield from _move_to(x, y)
        if not ok:
            ConsoleLog(BOT_NAME, f"[RECOVERY] Failed move to ({x}, {y})", log=True)
            yield
            return

    Player.Move(9240.07, -20260.95)
    yield from Routines.Yield.wait(1000)

    ok = yield from _wait_for_map("Shards of Oor (level 1)")
    if not ok:
        ConsoleLog(BOT_NAME, "[RECOVERY] Impossible to enter to Shards of Oor (level 1)", log=True)
        yield
        return

    ConsoleLog(BOT_NAME, "[RECOVERY] Entered Shards of Oor (level 1)", log=True)

    # 3) Exit dungeon
    ok = yield from _move_to(-15650.00, 8900.00)
    if not ok:
        ConsoleLog(BOT_NAME, "[RECOVERY] Failed move to dungeon exit", log=True)
        yield
        return

    yield from Routines.Yield.wait(1000)

    ok = yield from _wait_for_map("Arbor Bay")
    if not ok:
        ConsoleLog(BOT_NAME, "[RECOVERY] Impossible to comeback to Arbor Bay", log=True)
        yield
        return

    ConsoleLog(BOT_NAME, "[RECOVERY] Back to Arbor Bay", log=True)



    # 4) Retake quest from Shandra
    ok = yield from _interact_with_Shandra(bot, SHANDRA_TAKE_DIALOGS)
    if not ok:
        ConsoleLog(BOT_NAME, "[RECOVERY] Retake quest failed", log=True)
        yield
        return

    ConsoleLog(BOT_NAME, "[RECOVERY] Late reward flow -> done", log=True)



    bot.States.JumpToStepName("LOOP_RESTART_POINT")
    yield

SHANDRA_REWARD_PENDING = False
L3_BOSS_ROUTE_UNLOCKED = False

def _reset_l3_boss_route_flag() -> Generator:
    global L3_BOSS_ROUTE_UNLOCKED
    L3_BOSS_ROUTE_UNLOCKED = False
    ConsoleLog(BOT_NAME, "[L3] Boss route unlocked = False")
    yield


def _set_l3_boss_route_flag() -> Generator:
    global L3_BOSS_ROUTE_UNLOCKED
    L3_BOSS_ROUTE_UNLOCKED = True
    ConsoleLog(BOT_NAME, "[L3] Boss route unlocked = True")
    yield

def _post_return_flow(bot: Botting) -> Generator:
    global SHANDRA_REWARD_PENDING

    ConsoleLog(BOT_NAME, f"[POST-RETURN] Flag value = {SHANDRA_REWARD_PENDING}", log=True)

    if not SHANDRA_REWARD_PENDING:
        ConsoleLog(BOT_NAME, "[POST-RETURN] Reward NOT taken -> recovery flow", log=True)
        yield from _recover_reward_and_retake_quest(bot)
        yield
        return

    ConsoleLog(BOT_NAME, "[POST-RETURN] Reward taken -> continue", log=True)
    yield



def _disable_inventoryplus_pretravel() -> Generator:
    """Disable InventoryPlus on leader + alts BEFORE GH travel, so InventoryPlus cannot
    run its auto-deposit cycle when accounts enter GH (which would send scrolls to storage)."""
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler as _get_wh
    ConsoleLog(BOT_NAME, "[Merchant] Pre-travel: disabling InventoryPlus on all accounts")
    wh = _get_wh()
    for name in _PRETRAVEL_DISABLE_WIDGETS:
        wh.disable_widget(name)
    _my_email = Player.GetAccountEmail()
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if acc.AccountEmail != _my_email:
            for name in _PRETRAVEL_DISABLE_WIDGETS:
                GLOBAL_CACHE.ShMem.SendMessage(
                    _my_email, acc.AccountEmail,
                    SharedCommandType.DisableWidget, (0, 0, 0, 0), (name, "", "", ""),
                )
    ConsoleLog(BOT_NAME, "[Merchant] Pre-travel: InventoryPlus disabled â€” waiting 1.5s for alts to process")
    yield from Routines.Yield.wait(1500)


def _reenable_merchant_widgets() -> Generator:
    """Re-enable InventoryPlus and CustomBehaviors on leader + all alts after GH merchant ops.
    Called once all accounts are back in Vlox's Falls, ready to enter the dungeon."""
    from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler as _get_wh
    ConsoleLog(BOT_NAME, "[Merchant] Re-enabling managed widgets on all accounts")
    wh = _get_wh()
    for name in _MERCHANT_MANAGED_WIDGETS:
        wh.enable_widget(name)
    _my_email = Player.GetAccountEmail()
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if acc.AccountEmail != _my_email:
            for name in _MERCHANT_MANAGED_WIDGETS:
                GLOBAL_CACHE.ShMem.SendMessage(
                    _my_email, acc.AccountEmail,
                    SharedCommandType.EnableWidget, (0, 0, 0, 0), (name, "", "", ""),
                )
    ConsoleLog(BOT_NAME, f"[Merchant] Re-enabled {_MERCHANT_MANAGED_WIDGETS} on all accounts")
    # Give widget loops time to initialize before party commands (summon/invite).
    yield from Routines.Yield.wait(_POST_WIDGET_REENABLE_SETTLE_MS)
    yield


def _gh_merchant_setup(leave_party: bool = True) -> Generator:
    """Travel to Guild Hall (all accounts via SharedMemory), restock kits, sell materials,
    sell leftover stacks and optionally buy ectos. Mirrors the FoW modular bot pattern."""
    from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
    from Sources.oazix.CustomBehaviors.primitives.parties.party_command_contants import PartyCommandConstants
    from Py4GWCoreLib.enums_src.Model_enums import ModelID as _ModelID

    _load_merchant_settings()
    if not _merchant_enabled:
        yield
        return

    # â”€â”€ Step 0 (startup only): Leave current party on all accounts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if leave_party:
        ConsoleLog(BOT_NAME, "[Merchant] Leaving party on all accounts before GH travel")
        _my_email = Player.GetAccountEmail()
        for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
            if acc.AccountEmail != _my_email:
                GLOBAL_CACHE.ShMem.SendMessage(_my_email, acc.AccountEmail, SharedCommandType.LeaveParty, (0, 0, 0, 0), ("", "", "", ""))
        GLOBAL_CACHE.Party.LeaveParty()
        yield from Routines.Yield.wait(2000)

    # â”€â”€ Pre-travel: Disable InventoryPlus BEFORE GH entry so its auto-deposit cycle
    #    cannot send scrolls (or other items) to storage when accounts enter GH. â”€â”€
    yield from _disable_inventoryplus_pretravel()

    # â”€â”€ Step 1: Send ALL accounts to their own Guild Hall (FoW pattern) â”€â”€â”€â”€â”€â”€â”€
    ConsoleLog(BOT_NAME, "[Merchant] Waiting for CustomBehaviorParty to be ready")
    _cb_deadline = time.time() + 30
    while not CustomBehaviorParty().is_ready_for_action() and time.time() < _cb_deadline:
        yield from Routines.Yield.wait(100)

    ConsoleLog(BOT_NAME, "[Merchant] Scheduling GH travel for all accounts")
    _ok = bool(CustomBehaviorParty().schedule_action(PartyCommandConstants.travel_gh))
    if not _ok:
        ConsoleLog(BOT_NAME, "[Merchant] CB schedule failed â€” falling back to local TravelGH")
        if not Map.IsGuildHall():
            Map.TravelGH()

    # Wait for all accounts to arrive at their GH
    _cb_deadline = time.time() + 60
    while not CustomBehaviorParty().is_ready_for_action() and time.time() < _cb_deadline:
        yield from Routines.Yield.wait(200)

    # Ensure leader is in GH
    _gh_deadline = time.time() + 30
    while not Map.IsGuildHall() and time.time() < _gh_deadline:
        yield from Routines.Yield.wait(500)

    if not Map.IsGuildHall():
        ConsoleLog(BOT_NAME, "[Merchant] Failed to reach Guild Hall â€” skipping merchant step")
        yield
        return

    yield from Routines.Yield.wait(3000)  # wait for NPCs to finish loading

    # â”€â”€ Disable CustomBehavior and InventoryPlus on all accounts during merchant ops â”€â”€
    yield from _disable_merchant_widgets()

    # â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _my_email = Player.GetAccountEmail()

    def _dispatch_to_alts(command, params, extra_data=("", "", "", "")) -> list[tuple[str, int]]:
        refs: list[tuple[str, int]] = []
        for _acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
            if _acc.AccountEmail != _my_email:
                msg_index = int(
                    GLOBAL_CACHE.ShMem.SendMessage(_my_email, _acc.AccountEmail, command, params, extra_data)
                )
                refs.append((_acc.AccountEmail, msg_index))
        return refs

    def _wait_for_alt_dispatch_completion(
        stage_name: str,
        message_refs: list[tuple[str, int]],
        command,
        timeout_ms: int = 30_000,
    ):
        if not message_refs:
            return
        pending: dict[tuple[str, int], None] = {
            (acc_email, msg_index): None
            for acc_email, msg_index in message_refs
            if int(msg_index) >= 0
        }
        if not pending:
            return
        deadline = time.monotonic() + (max(0, int(timeout_ms)) / 1000.0)
        while pending and time.monotonic() < deadline:
            completed: list[tuple[str, int]] = []
            for acc_email, msg_index in list(pending.keys()):
                message = GLOBAL_CACHE.ShMem.GetInbox(msg_index)
                is_same_message = (
                    bool(getattr(message, "Active", False))
                    and str(getattr(message, "ReceiverEmail", "") or "") == acc_email
                    and str(getattr(message, "SenderEmail", "") or "") == _my_email
                    and int(getattr(message, "Command", -1)) == int(command)
                )
                if not is_same_message:
                    completed.append((acc_email, msg_index))
            for key in completed:
                pending.pop(key, None)
            if pending:
                yield from Routines.Yield.wait(50)
        if pending:
            pending_accounts = ", ".join(sorted({email for email, _ in pending}))
            ConsoleLog(
                BOT_NAME,
                f"[Merchant] {stage_name}: timeout waiting for alt completion after {timeout_ms} ms. Pending: {pending_accounts}",
                Py4GW.Console.MessageType.Warning,
            )

    # â”€â”€ Step 2: Find NPC coordinates â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _RARE_MAT_MODELS = {935, 936}  # Diamond=935, Onyx Gemstone=936
    _RARE_MAT_FILTER  = "935,936"  # encoded for ShMem dispatch
    _CRAFTING_MAT_MODELS = {
        int(_ModelID.Pile_Of_Glittering_Dust.value),
        int(_ModelID.Bone.value),
        int(_ModelID.Iron_Ingot.value),
        int(_ModelID.Feather.value),
        int(_ModelID.Plant_Fiber.value),
    }
    _CRAFTING_MAT_FILTER = ",".join(str(mid) for mid in sorted(_CRAFTING_MAT_MODELS))

    merchant_xy   = _find_npc_xy_by_name("Merchant")
    mat_xy        = _find_npc_xy_by_name("Material Trader") if _merchant_sell_materials else None
    rare_xy       = _find_npc_xy_by_name("Rare") if (_merchant_buy_ectos or _merchant_sell_rare_mats) else None

    # â”€â”€ Step 2.5: Store consumable crafting mats before trader sales (leader + alts)
    if _merchant_store_consumable_materials:
        ConsoleLog(BOT_NAME, "[Merchant] Depositing consumable crafting materials to storage on all accounts")
        deposit_refs = _dispatch_to_alts(
            SharedCommandType.MerchantMaterials,
            (0, 0, 0, 0),
            ("deposit", _CRAFTING_MAT_FILTER, "", "0"),
        )
        yield from _coro_deposit_crafting_materials_to_storage(_CRAFTING_MAT_MODELS)
        yield from _wait_for_alt_dispatch_completion("deposit_materials", deposit_refs, SharedCommandType.MerchantMaterials)

    # â”€â”€ Step 3: Sell materials at trader (leader + alts) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if _merchant_sell_materials:
        if mat_xy:
            tmx, tmy = mat_xy
            ConsoleLog(BOT_NAME, f"[Merchant] Dispatching sell_materials to alts, trader at ({tmx:.0f}, {tmy:.0f})")
            sell_mat_refs = _dispatch_to_alts(
                SharedCommandType.MerchantMaterials,
                (tmx, tmy, 0, 0),
                ("sell", "", "", ""),
            )
            ConsoleLog(BOT_NAME, "[Merchant] Selling materials at trader (leader)")
            yield from Routines.Yield.Merchant.SellMaterialsAtTrader(tmx, tmy)
            yield from _wait_for_alt_dispatch_completion("sell_materials", sell_mat_refs, SharedCommandType.MerchantMaterials)
        else:
            ConsoleLog(BOT_NAME, "[Merchant] No Material Trader NPC found")

        # â”€â”€ Step 4: Sell leftover stacks < 10 to regular merchant (leader + alts)
        if merchant_xy:
            mx, my = merchant_xy
            ConsoleLog(BOT_NAME, "[Merchant] Dispatching sell_merchant_leftovers to alts")
            leftover_refs = _dispatch_to_alts(
                SharedCommandType.MerchantMaterials,
                (mx, my, 0, 0),
                ("sell_merchant_leftovers", "", "10", ""),
            )
            leftover_ids = _get_leftover_material_item_ids()
            if leftover_ids:
                ConsoleLog(BOT_NAME, f"[Merchant] Selling {len(leftover_ids)} leftover stacks (leader)")
                yield from bot.Move._coro_xy_and_interact_npc(mx, my, "GH Merchant (leftovers)")
                yield from Routines.Yield.wait(1200)
                yield from Routines.Yield.Merchant.SellItems(leftover_ids, log=True)
                yield from Routines.Yield.wait(300)
            yield from _wait_for_alt_dispatch_completion(
                "sell_merchant_leftovers",
                leftover_refs,
                SharedCommandType.MerchantMaterials,
            )

    # â”€â”€ Step 5: Sell non-salvageable gold items (anniversary weapons) to merchant â”€
    if merchant_xy:
        mx, my = merchant_xy
        ConsoleLog(BOT_NAME, "[Merchant] Dispatching sell_nonsalvageable_golds to alts")
        sell_gold_refs = _dispatch_to_alts(
            SharedCommandType.MerchantMaterials,
            (mx, my, 0, 0),
            ("sell_nonsalvageable_golds", "", "", ""),
        )
        yield from _coro_sell_nonsalvageable_golds(mx, my)
        yield from _wait_for_alt_dispatch_completion(
            "sell_nonsalvageable_golds",
            sell_gold_refs,
            SharedCommandType.MerchantMaterials,
        )

    # â”€â”€ Step 6: Sell XP/insight scrolls to merchant (leader + alts) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if merchant_xy:
        mx, my = merchant_xy
        ConsoleLog(BOT_NAME, "[Merchant] Dispatching sell_scrolls to alts")
        sell_scroll_refs = _dispatch_to_alts(
            SharedCommandType.MerchantMaterials,
            (mx, my, 0, 0),
            ("sell_scrolls", _SCROLL_MODEL_FILTER, "", ""),
        )
        yield from _coro_sell_scrolls(mx, my)
        yield from _wait_for_alt_dispatch_completion("sell_scrolls", sell_scroll_refs, SharedCommandType.MerchantMaterials)

    # â”€â”€ Step 7: Restock kits (leader + alts) â€” after all selling to maximise free space
    if merchant_xy:
        mx, my = merchant_xy
        ConsoleLog(BOT_NAME, f"[Merchant] Merchant at ({mx:.0f}, {my:.0f}) â€” dispatching kits to alts")
        kit_refs = _dispatch_to_alts(
            SharedCommandType.MerchantItems,
            (mx, my, _merchant_id_kits_target, _merchant_salvage_kits_target),
        )
        yield from bot.Move._coro_xy_and_interact_npc(mx, my, "GH Merchant")
        yield from Routines.Yield.wait(1200)
        id_kits     = _count_model_in_inventory(_ModelID.Identification_Kit.value)
        sup_id_kits = _count_model_in_inventory(_ModelID.Superior_Identification_Kit.value)
        salvage_kits = _count_model_in_inventory(_ModelID.Salvage_Kit.value)
        id_to_buy      = max(0, _merchant_id_kits_target     - (id_kits + sup_id_kits))
        salvage_to_buy = max(0, _merchant_salvage_kits_target - salvage_kits)
        ConsoleLog(BOT_NAME, f"[Merchant] Buying {id_to_buy} ID kits, {salvage_to_buy} salvage kits")
        yield from Routines.Yield.Merchant.BuyIDKits(id_to_buy, log=True)
        yield from Routines.Yield.Merchant.BuySalvageKits(salvage_to_buy, log=True)
        yield from _wait_for_alt_dispatch_completion("restock_kits", kit_refs, SharedCommandType.MerchantItems)
        yield from Routines.Yield.wait(300)
    else:
        ConsoleLog(BOT_NAME, "[Merchant] No Merchant NPC found â€” skipping kit purchase")

    # â”€â”€ Step 6: Sell Diamonds & Onyx to Rare Material Trader (leader + alts) â”€â”€
    if _merchant_sell_rare_mats:
        if rare_xy:
            rx, ry = rare_xy
            ConsoleLog(BOT_NAME, "[Merchant] Dispatching sell_rare_mats (Diamond/Onyx) to alts")
            rare_sell_refs = _dispatch_to_alts(
                SharedCommandType.MerchantMaterials,
                (rx, ry, 0, 0),
                ("sell_rare_mats", _RARE_MAT_FILTER, "", ""),
            )
            ConsoleLog(BOT_NAME, "[Merchant] Selling Diamond/Onyx at Rare Material Trader (leader)")
            yield from _coro_sell_rare_mats_at_trader(rx, ry, _RARE_MAT_MODELS)
            yield from _wait_for_alt_dispatch_completion(
                "sell_rare_mats",
                rare_sell_refs,
                SharedCommandType.MerchantMaterials,
            )
        else:
            ConsoleLog(BOT_NAME, "[Merchant] No Rare Material Trader found â€” skipping rare mat sell")

    # â”€â”€ Step 7: Buy ectos from storage excess (leader + alts independently)
    # Storage is PER-ACCOUNT in GW â€” each account checks its own storage independently.
    # Always dispatch to alts so each alt can buy if ITS OWN storage exceeds threshold.
    if _merchant_buy_ectos and rare_xy:
        rx, ry = rare_xy
        ConsoleLog(BOT_NAME, f"[Merchant] Dispatching buy_ectoplasm to all alts (threshold={_merchant_ecto_threshold:,})")
        buy_ecto_refs = _dispatch_to_alts(
            SharedCommandType.MerchantMaterials,
            (rx, ry, _merchant_ecto_threshold, _merchant_ecto_threshold),
            ("buy_ectoplasm", "1", "0", ""),  # use_storage_gold=True; each alt checks own storage
        )
        # Leader buys from its own storage independently
        leader_storage = int(GLOBAL_CACHE.Inventory.GetGoldInStorage())
        if leader_storage > _merchant_ecto_threshold:
            ConsoleLog(BOT_NAME, f"[Merchant] Leader buying ectos (storage={leader_storage:,}, threshold={_merchant_ecto_threshold:,})")
            yield from Routines.Yield.Merchant.BuyEctoplasm(
                rx, ry,
                use_storage_gold=True,
                start_threshold=_merchant_ecto_threshold,
                stop_threshold=_merchant_ecto_threshold,
            )
        else:
            ConsoleLog(BOT_NAME, f"[Merchant] Leader storage ({leader_storage:,}) at/below threshold â€” skipping leader ecto buy")
        yield from _wait_for_alt_dispatch_completion("buy_ectoplasm", buy_ecto_refs, SharedCommandType.MerchantMaterials)
    elif _merchant_buy_ectos:
        ConsoleLog(BOT_NAME, "[Merchant] Ecto buy skipped â€” no Rare Material Trader found")

    # â”€â”€ Step 8: Wait for alts to finish their queued actions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if _merchant_alt_wait_ms > 0:
        ConsoleLog(BOT_NAME, f"[Merchant] Final settle wait {_merchant_alt_wait_ms}ms")
        yield from Routines.Yield.wait(_merchant_alt_wait_ms)

    # â”€â”€ Step 9: Return to Vlox's Fall â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    ConsoleLog(BOT_NAME, "[Merchant] Returning to Vlox's Fall")
    yield from _coro_travel_random_district(Vloxs_Fall)
    ConsoleLog(BOT_NAME, "[Merchant] Guild Hall merchant run complete")
    yield

def _resign_all_to_outpost_before_merchant() -> Generator:
    ConsoleLog(BOT_NAME, "[Merchant] Resigning all accounts before Guild Hall merchant routine")
    start_map_id = int(Map.GetMapID())
    my_email = Player.GetAccountEmail()
    for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if acc.AccountEmail != my_email:
            GLOBAL_CACHE.ShMem.SendMessage(my_email, acc.AccountEmail, SharedCommandType.Resign, (0, 0, 0, 0), ("", "", "", ""))
    Player.SendChatCommand("resign")
    yield from Routines.Yield.wait(500)

    map_change_deadline = time.time() + 45.0
    while time.time() < map_change_deadline:
        if int(Map.GetMapID()) != start_map_id:
            break
        yield from Routines.Yield.wait(250)

    yield from bot.Wait._coro_until_on_outpost()


def _return_to_arbor_bay_after_merchant() -> Generator:
    if int(Map.GetMapID()) == Arbor_Bay:
        yield from Routines.Yield.wait(_POST_RETURN_TO_ARBOR_SETTLE_MS)
        yield
        return
    if int(Map.GetMapID()) != Vloxs_Fall:
        yield from _coro_travel_random_district(Vloxs_Fall)
    yield from bot.Wait._coro_until_on_outpost()
    yield from bot.Move._coro_xy_and_exit_map(15505.38, 12460.59, target_map_id=Arbor_Bay, step_name="Return to Arbor Bay")
    yield from Routines.Yield.wait(_POST_RETURN_TO_ARBOR_SETTLE_MS)


def _rebuild_party_after_merchant() -> Generator:
    from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
    from Sources.oazix.CustomBehaviors.primitives.parties.party_command_contants import PartyCommandConstants

    ConsoleLog(BOT_NAME, "[Merchant] Rebuilding party after GH restock (CustomBehaviorParty)")

    _cb_deadline = time.time() + 15.0
    while not CustomBehaviorParty().is_ready_for_action() and time.time() < _cb_deadline:
        yield from Routines.Yield.wait(100)

    if not CustomBehaviorParty().is_ready_for_action():
        ConsoleLog(BOT_NAME, "[Merchant] Party behavior not ready for summon", Py4GW.Console.MessageType.Warning)
        yield
        return

    _ok = bool(CustomBehaviorParty().schedule_action(PartyCommandConstants.summon_all_to_current_map))
    if not _ok:
        ConsoleLog(BOT_NAME, "[Merchant] Failed to schedule summon_all_to_current_map", Py4GW.Console.MessageType.Warning)
        yield
        return

    # Let summon travel/actions settle before invite.
    _cb_deadline = time.time() + 25.0
    while not CustomBehaviorParty().is_ready_for_action() and time.time() < _cb_deadline:
        yield from Routines.Yield.wait(200)
    yield from Routines.Yield.wait(1200)

    _cb_deadline = time.time() + 15.0
    while not CustomBehaviorParty().is_ready_for_action() and time.time() < _cb_deadline:
        yield from Routines.Yield.wait(100)

    if not CustomBehaviorParty().is_ready_for_action():
        ConsoleLog(BOT_NAME, "[Merchant] Party behavior not ready for invite", Py4GW.Console.MessageType.Warning)
        yield
        return

    _ok = bool(CustomBehaviorParty().schedule_action(PartyCommandConstants.invite_all_to_leader_party))
    if not _ok:
        ConsoleLog(BOT_NAME, "[Merchant] Failed to schedule invite_all_to_leader_party", Py4GW.Console.MessageType.Warning)
        yield
        return

    _cb_deadline = time.time() + 20.0
    while not CustomBehaviorParty().is_ready_for_action() and time.time() < _cb_deadline:
        yield from Routines.Yield.wait(200)


def _gh_merchant_setup_for_alt_salvage_threshold() -> Generator:
    _write_local_salvage_kit_count()
    yield from _request_alt_salvage_kit_counts()
    needs_restock, low_accounts, unknown_accounts = _alts_need_salvage_restock()
    if unknown_accounts:
        ConsoleLog(
            BOT_NAME,
            f"[Merchant] Alt salvage count unknown this pass: {', '.join(unknown_accounts)}",
            Py4GW.Console.MessageType.Warning,
        )
    if not needs_restock:
        yield
        return

    ConsoleLog(
        BOT_NAME,
        f"[Merchant] Alt salvage trigger hit: {', '.join(low_accounts)}. Running Guild Hall merchant routine.",
    )
    yield from _resign_all_to_outpost_before_merchant()
    yield from _gh_merchant_setup(leave_party=True)
    yield from _reenable_merchant_widgets()
    yield from _return_to_arbor_bay_after_merchant()
    yield from _rebuild_party_after_merchant()


def _gh_merchant_setup_if_inventory_full() -> Generator:
    """After quest reward: if only 1 free inventory slot remains, resign to outpost then run the full GH merchant routine."""
    free_slots = int(GLOBAL_CACHE.Inventory.GetFreeSlotCount())
    if free_slots > 1:
        yield
        return
    ConsoleLog(BOT_NAME, f"[Merchant] Inventory nearly full ({free_slots} free slot) â€” resigning to outpost then triggering GH merchant run")

    yield from _resign_all_to_outpost_before_merchant()
    yield from _gh_merchant_setup(leave_party=True)
    yield from _reenable_merchant_widgets()
    yield from _return_to_arbor_bay_after_merchant()
    yield from _rebuild_party_after_merchant()


def _snapshot_bds_before_chest() -> Generator:
    global _bds_pre_snapshot
    _bds_pre_snapshot = {}
    for model_id in BDS_MODEL_IDS:
        count = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
        if count > 0:
            _bds_pre_snapshot[model_id] = count
    total_pre = sum(_bds_pre_snapshot.values())
    ConsoleLog(BOT_NAME, f"[BDS Stats] Pre-chest snapshot: {total_pre} BDS in inventory")
    yield


def _record_bds_after_loot() -> Generator:
    global _session_bds_found, _session_runs
    new_count = 0

    for model_id in BDS_MODEL_IDS:
        post_count = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
        pre_count = _bds_pre_snapshot.get(model_id, 0)
        if post_count > pre_count:
            new_count += post_count - pre_count
    _session_bds_found += new_count
    _session_runs += 1

    rate = f"{(_session_bds_found / _session_runs):.2f}/run" if _session_runs > 0 else "-"
    if new_count > 0:
        ConsoleLog(BOT_NAME, f"[BDS Stats] +{new_count} BDS this run! Session: {_session_bds_found} in {_session_runs} runs ({rate})")
    else:
        ConsoleLog(BOT_NAME, f"[BDS Stats] No BDS this run. Session: {_session_bds_found} in {_session_runs} runs ({rate})")
    yield


# --- Statistics and Run Tracking ---

def _draw_bds_stats() -> None:
    import PyImGui
    from Py4GWCoreLib import ImGui, Color

    gold = Color(255, 210, 80, 255).to_tuple_normalized()

    _bds_icon_exists = os.path.isfile(_BDS_ICON_PATH)
    if _bds_icon_exists:
        ImGui.image(_BDS_ICON_PATH, (24, 24))
        PyImGui.same_line(0, 8)
    PyImGui.text_colored("BDS Statistics (this session)", gold)
    rate = f"{(_session_bds_found / _session_runs):.2f}/run" if _session_runs > 0 else "-"
    PyImGui.text(f"BDS dropped: {_session_bds_found}   |   Runs: {_session_runs}   |   Rate: {rate}")




# ==================== AUTO SHRINE + STEP REGISTRY ====================

# Move step registry (per map)
_STEP_BY_NAME: Dict[str, int] = {}  # name -> global index
_STEP_META: List[Dict[str, Any]] = []  # {idx,name,map_id,x,y}

# â€œLearned shrinesâ€ per map (from rez positions)
_SHRINES: Dict[int, List[Tuple[float, float]]] = {}

_LAST_STEP_NAME: Optional[str] = None
_LAST_STEP_IDX: int = -1

# Tune these
SHRINE_MERGE_DIST = 450.0   # merge learned shrines within this radius
RESUME_SEARCH_DIST = 1200.0 # max dist to find a nearby move step at rez

# --- Pathing, Shrines, and Step Registry ---

def S_BlacklistModel(model_id: int):
    """Custom FSM step: add a MODEL ID to loot blacklist (script-only)."""
    from Py4GWCoreLib.Routines import Routines
    from Py4GWCoreLib.py4gwcorelib_src.Lootconfig_src import LootConfig

    def _gen():
        loot = LootConfig()
        loot.AddToBlacklist(model_id)     # <- MODEL blacklist
        yield from Routines.Yield.wait(100)
        yield
    return _gen()


def S_BlacklistModels(model_ids) -> Generator:
    from Py4GWCoreLib.Routines import Routines
    from Py4GWCoreLib.py4gwcorelib_src.Lootconfig_src import LootConfig

    def _gen():
        loot = LootConfig()
        for model_id in model_ids:
            loot.AddToBlacklist(int(model_id))
        yield from Routines.Yield.wait(100)
        yield

    return _gen()

def drop_bundle_safe(times: int = 2, delay_ms: int = 250) -> Generator:
    for _ in range(times):
        yield from Routines.Yield.Keybinds.DropBundle()
        yield from Routines.Yield.wait(delay_ms)
    yield

def _toggle_wait_for_party(enabled: bool) -> None:
    _set_custom_utility_enabled(
        enabled,
        skill_names=("wait_if_party_member_too_far",),
        class_names=("WaitIfPartyMemberTooFarUtility",),
    )


def _set_custom_utility_enabled(
    enabled: bool,
    *,
    skill_names: tuple[str, ...] = (),
    class_names: tuple[str, ...] = (),
) -> bool:
    behavior = _get_custom_behavior(initialize_if_needed=True)
    if behavior is None:
        return False

    for utility in behavior.get_skills_final_list():
        utility_skill_name = getattr(getattr(utility, "custom_skill", None), "skill_name", None)
        utility_class_name = utility.__class__.__name__

        if utility_skill_name in skill_names or utility_class_name in class_names:
            utility.is_enabled = enabled
            return True

    return False


def _get_custom_behavior(initialize_if_needed: bool = True):
    loader = CustomBehaviorLoader()
    behavior = loader.custom_combat_behavior

    if behavior is None and initialize_if_needed:
        loader.initialize_custom_behavior_candidate()
        behavior = loader.custom_combat_behavior

    return behavior

def TrackCurrentStep(bot: "Botting") -> None:
    """Update last step name + idx (best-effort)."""
    global _LAST_STEP_NAME, _LAST_STEP_IDX

    cur = getattr(bot.config.FSM, "current_step_name", None)
    if not cur:
        cur = getattr(bot.States, "CurrentStepName", None)

    if isinstance(cur, str) and cur and cur != _LAST_STEP_NAME:
        _LAST_STEP_NAME = cur
        _LAST_STEP_IDX = _STEP_BY_NAME.get(cur, _LAST_STEP_IDX)
        ConsoleLog("STEP", f"ðŸ‘€ {cur} (idx={_LAST_STEP_IDX})")

def _dist(ax: float, ay: float, bx: float, by: float) -> float:
    return math.hypot(ax - bx, ay - by)


BDS_L2_PART1 = [
    (-11303, -14596),  # allumage torche (premier brasier)
    (-11019, -11550),
    (-9028,  -9021),
    (-6805,  -11511),
    (-8984,  -13842),
]


BDS_L2_PART2 = [
    (-3717, -4254),
    (-8251, -3240),
    (-8278, -1670),
]
BDS_L2_CLEANING = [
    (-7506.89, -12236.26),
    (-7435.12, -10649.25),
    (-9013.61, -9772.06),
    (-10324.58, -10434.43),
    (-10371.20, -12510.16),
    (-8836.63, -11471.01),
]
BDS_L3 = [
    (15692, 17111),
    (12969, 19842),
    (8236,  16950),
    (5549,  9920),
    (-536,  6109),
    (-3814, 5599),
    (-4959, 7558),
    (-7532, 4536),
    (-10984, 486),
    (-12621, 2948),
]

# --- Torch, Brazier, and Boss Helpers ---

def command_type_routine_in_message_is_active(account_email, shared_command_type):
    """Checks if a multibox command is active for an account"""
    index, message = GLOBAL_CACHE.ShMem.PreviewNextMessage(account_email)
    if index == -1 or message is None:
        return False
    if message.Command != shared_command_type:
        return False
    return True


def debug_item_signature(max_dist: float = 2500.0) -> Generator:
    agents = AgentArray.GetItemArray()
    agents = AgentArray.Filter.ByDistance(agents, Player.GetXY(), max_dist)
    agents = AgentArray.Sort.ByDistance(agents, Player.GetXY())

    ConsoleLog(BOT_NAME, f"[DBG] items_near={len(agents)}")

    for i, a in enumerate(agents[:10]):
        it = Agent.GetItemAgentByID(int(a))
        if not it:
            continue
        ConsoleLog(
            BOT_NAME,
            f"[DBG] #{i} agent_id={a} item_id={it.item_id} extra_type={it.extra_type} h00CC={hex(int(it.h00CC))}"
        )
        yield from Routines.Yield.wait(100)

    yield

INTERACTABLE_TYPES = {0x200, 0x400}  # coffres / portes / brasiers (comme ton AutoIt)


try:
    from Py4GWCoreLib import Item
except Exception:
    Item = None

TORCH_MODEL_IDS = {22341, 22342}
PICKUP_DIST = 180.0
MOVE_TIMEOUT_MS = 9000



def pickup_torch(max_scan_dist: float = 5000, attempts: int = 40) -> Generator:
    inv = PyInventory.PyInventory()
    me = int(Player.GetAgentID())

    ConsoleLog("TORCH", "Scanning for Torch")

    for _ in range(attempts):
        arr = AgentArray.GetItemArray()
        arr = AgentArray.Filter.ByDistance(arr, Player.GetXY(), max_scan_dist)
        arr = AgentArray.Sort.ByDistance(arr, Player.GetXY())

        target_agent: int = 0
        ground_item_id: int = 0
        owner: int = -1

        for a in arr:
            aid = int(a)
            it = Agent.GetItemAgentByID(aid)
            if not it:
                continue

            try:
                owner = int(it.owner)
                if owner not in (0, me):
                    continue
            except Exception:
                owner = -1  # si owner illisible, on tente quand mÃªme

            try:
                gid = int(Agent.GetItemAgentItemID(aid))
            except Exception:
                continue

            mid: Optional[int] = None
            if Item is not None:
                try:
                    m = Item.GetModelID(gid)
                    mid = int(m) if isinstance(m, int) else None
                except Exception:
                    mid = None

            if mid in TORCH_MODEL_IDS:
                target_agent = aid
                ground_item_id = gid
                break

        if not target_agent:
            yield from Routines.Yield.wait(150)
            continue

        tx, ty = Agent.GetXY(target_agent)

        # Approche
        try:
            Player.Move(tx, ty)
        except Exception:
            pass

        start = time.time() * 1000
        while True:
            px, py = Player.GetXY()
            if _dist(px, py, tx, ty) <= PICKUP_DIST:
                break
            if (time.time() * 1000) - start > MOVE_TIMEOUT_MS:
                ConsoleLog("TORCH", "cant reach -> retry")
                target_agent = 0
                break
            yield from Routines.Yield.wait(100)

        if not target_agent:
            continue

        # stop-move pour Ã©viter annulation
        try:
            px, py = Player.GetXY()
            Player.Move(px, py)
        except Exception:
            pass
        yield from Routines.Yield.wait(80)

        # Ciblage
        Player.ChangeTarget(target_agent)
        yield from Routines.Yield.wait(120)

        ConsoleLog("TORCH", f"pickup try agent={target_agent} ground_item_id={ground_item_id} owner={owner}")

        # Essais : agent_id puis ground_item_id (compat multi-build)
        for _try in range(2):
            try:
                inv.PickUpItem(target_agent, True)
            except Exception:
                pass
            yield from Routines.Yield.wait(250)

            try:
                inv.PickUpItem(ground_item_id, True)
            except Exception:
                pass
            yield from Routines.Yield.wait(250)

            # fallback interact
            try:
                Player.Interact(target_agent, False)
            except Exception:
                pass
            yield from Routines.Yield.wait(450)

            # check disparition (ramassÃ©)
            try:
                still_there = bool(Agent.GetItemAgentByID(target_agent))
            except Exception:
                still_there = False

            if not still_there:
                ConsoleLog("TORCH", "Torch picked up")
                yield
                return

        ConsoleLog("TORCH", "Torch pickup attempt failed -> retry")
        yield from Routines.Yield.wait(200)

    ConsoleLog("TORCH", "Torch pickup failed")
    yield




def nearest_from_array(arr: List[int], max_dist: float) -> int:
    arr = AgentArray.Filter.ByDistance(arr, Player.GetXY(), max_dist)
    arr = AgentArray.Sort.ByDistance(arr, Player.GetXY())
    return int(arr[0]) if len(arr) > 0 else 0


BRAZIER_INTERACT_ATTEMPTS = 4
TORCH_BUFF_ID = 2545
BRAZIER_MAX_RETRIES = 3
BRAZIER_ARRIVE_DIST = 200.0
BRAZIER_MOVE_POLL_MS = 150
BRAZIER_MOVE_TIMEOUT_S = 30.0

def _interact_brazier(label: str, result: list, max_dist: float = 220.0, attempts: int = BRAZIER_INTERACT_ATTEMPTS) -> Generator:
    """Find the nearest gadget and interact with it. Logs once with the label and gadget id.
    Sets result[0] = True if a gadget was found and interacted with."""
    result[0] = False
    logged = False
    for attempt in range(attempts):
        gadgets = AgentArray.GetGadgetArray()
        gad_id = nearest_from_array(gadgets, max_dist)
        if not gad_id:
            yield from Routines.Yield.wait(300)
            continue

        if not logged:
            ConsoleLog(BOT_NAME, f"[BRAZIER] {label} (gadget id: {gad_id})")
            logged = True
            result[0] = True

        Player.ChangeTarget(gad_id)
        yield from Routines.Yield.wait(150)
        Player.Interact(gad_id, False)
        yield from Routines.Yield.wait(400)

    if not logged:
        ConsoleLog(BOT_NAME, f"[BRAZIER] {label} - no gadget found within {max_dist}")
    yield


def _move_to_xy_gen(
    x: float,
    y: float,
    result: Optional[list] = None,
    check_abort: Optional[Callable[[], bool]] = None,
) -> Generator:
    """Move to (x, y), yielding until arrival, timeout, or check_abort() returns True.
    If result is provided, sets result[0] to 'arrived', 'timeout', or 'aborted'."""
    if result is not None:
        result[0] = "arrived"
    deadline = time.time() + BRAZIER_MOVE_TIMEOUT_S
    while True:
        if check_abort is not None and check_abort():
            if result is not None:
                result[0] = "aborted"
            break
        px, py = Player.GetXY()
        if _dist(px, py, x, y) <= BRAZIER_ARRIVE_DIST:
            break
        if time.time() > deadline:
            if result is not None:
                result[0] = "timeout"
            ConsoleLog(BOT_NAME, f"[BRAZIER] Move timeout")
            break
        Player.Move(x, y)
        yield from Routines.Yield.wait(BRAZIER_MOVE_POLL_MS)


def _brazier_sequence_gen(points: list[tuple[float, float]], interact_dist: float = 200.0) -> Generator:
    """Walk through brazier waypoints, checking the torch buff (2545) after each one.
    If the buff has expired before the next brazier can be lit, go back to the
    previous brazier, re-interact to refresh the torch, then retry."""
    total = len(points)
    idx = 0
    interact_ok = [False]
    move_result = ["arrived"]
    while idx < total:
        x, y = points[idx]
        label = f"Brazier {idx + 1}/{total}"
        need_buff_check = idx > 0

        def _buff_expired():
            return not Effects.HasEffect(Player.GetAgentID(), TORCH_BUFF_ID)

        for retry in range(BRAZIER_MAX_RETRIES):
            if retry:
                ConsoleLog(BOT_NAME, f"[BRAZIER] Retry {retry} for {label}")

            move_result[0] = "arrived"
            check_abort = _buff_expired if need_buff_check else None
            yield from _move_to_xy_gen(x, y, move_result, check_abort)

            if move_result[0] == "aborted":
                ConsoleLog(BOT_NAME, f"[BRAZIER] Buff expired during move, returning to previous brazier ({idx}/{total})")
                prev_x, prev_y = points[idx - 1]
                yield from _move_to_xy_gen(prev_x, prev_y)
                yield from Routines.Yield.wait(250)
                yield from _interact_brazier(f"Re-lighting brazier {idx}/{total}", interact_ok, interact_dist)
                yield from Routines.Yield.wait(500)
                continue

            yield from Routines.Yield.wait(250)
            yield from _interact_brazier(label, interact_ok, interact_dist)
            yield from Routines.Yield.wait(500)

            if not interact_ok[0]:
                ConsoleLog(BOT_NAME, f"[BRAZIER] {label} - could not interact")
                if idx > 0:
                    prev_x, prev_y = points[idx - 1]
                    ConsoleLog(BOT_NAME, f"[BRAZIER] Returning to previous brazier ({idx}/{total}) to re-light torch")
                    yield from _move_to_xy_gen(prev_x, prev_y)
                    yield from Routines.Yield.wait(250)
                    yield from _interact_brazier(f"Re-lighting brazier {idx}/{total}", interact_ok, interact_dist)
                    yield from Routines.Yield.wait(500)
                continue
            if idx == 0:
                ConsoleLog(BOT_NAME, f"[BRAZIER] {label} lit (start)")
                break
            my_id = Player.GetAgentID()
            if Effects.HasEffect(my_id, TORCH_BUFF_ID):
                ConsoleLog(BOT_NAME, f"[BRAZIER] {label} lit")
                break
            prev_x, prev_y = points[idx - 1]
            ConsoleLog(BOT_NAME, f"[BRAZIER] Buff expired, returning to previous brazier ({idx}/{total}) to re-light torch")
            yield from _move_to_xy_gen(prev_x, prev_y)
            yield from Routines.Yield.wait(250)
            yield from _interact_brazier(f"Re-lighting brazier {idx}/{total}", interact_ok, interact_dist)
            yield from Routines.Yield.wait(500)
        else:
            ConsoleLog(BOT_NAME, f"[BRAZIER] {label} failed after {BRAZIER_MAX_RETRIES} retries")

        idx += 1

    ConsoleLog(BOT_NAME, f"[BRAZIER] Sequence complete ({total} braziers)")
    yield


def _log_cleaning_room() -> Generator:
    """Log message when L2 - Cleaning header state is reached."""
    ConsoleLog(BOT_NAME, "Clearing room level 2")
    yield


def run_brazier_sequence(points: list[tuple[float, float]], interact_dist: float = 200.0) -> None:
    bot.States.AddCustomState(
        lambda p=points, d=interact_dist: _brazier_sequence_gen(p, d),
        "Brazier sequence"
    )


FENDI_GADGET_ID = 8934
FENDI_SCAN_RADIUS = 700.0  # un peu plus large que 500 pour Ãªtre safe

def _target_fendi_chest_agent_id() -> int:
    """Retourne l'agent_id du coffre de Fendi (filtrÃ© par gadget_id)."""
    gadgets = AgentArray.GetGadgetArray()
    gadgets = AgentArray.Filter.ByDistance(gadgets, FENDI_CHEST_POSITION, FENDI_SCAN_RADIUS)
    gadgets = AgentArray.Sort.ByDistance(gadgets, FENDI_CHEST_POSITION)

    best = 0
    for a in gadgets:
        aid = int(a)
        g = Agent.GetGadgetAgentByID(aid)
        if not g:
            continue

        # g.gadget_id est la signature la plus fiable ici
        try:
            if int(g.gadget_id) == int(FENDI_GADGET_ID):
                best = aid
                break
        except Exception:
            continue

    return best



def debug_nearby_gadgets(max_print: int = 10) -> Generator:
    """Debug rapide si jamais tu veux vÃ©rifier les candidats autour du point."""
    gadgets = AgentArray.GetGadgetArray()
    gadgets = AgentArray.Filter.ByDistance(gadgets, FENDI_CHEST_POSITION, FENDI_SCAN_RADIUS)
    gadgets = AgentArray.Sort.ByDistance(gadgets, FENDI_CHEST_POSITION)

    ConsoleLog(BOT_NAME, f"[FENDI] gadgets_near={len(gadgets)}")
    for i, a in enumerate(gadgets[:max_print]):
        aid = int(a)
        g = Agent.GetGadgetAgentByID(aid)
        if not g:
            continue
        try:
            ConsoleLog(BOT_NAME, f"[FENDI] #{i} aid={aid} gadget_id={int(g.gadget_id)} extra_type={int(g.extra_type)}")
        except Exception:
            ConsoleLog(BOT_NAME, f"[FENDI] #{i} aid={aid} (no fields)")
        yield from Routines.Yield.wait(100)
    yield

def TargetNearestNPC():
    npc_array = AgentArray.GetNPCMinipetArray()
    npc_array = AgentArray.Filter.ByDistance(npc_array,Player.GetXY(), 200)
    npc_array = AgentArray.Sort.ByDistance(npc_array, Player.GetXY())
    if len(npc_array) > 0:
        Player.ChangeTarget(npc_array[0])

CHEST_OPEN_ATTEMPTS = 3  # number of interact attempts per account

def open_fendi_chest():
    """Multibox coordination for opening the final chest"""
    ConsoleLog(BOT_NAME, "Opening final chest with multibox...")

    target = _target_fendi_chest_agent_id()
    if target == 0:
        ConsoleLog(BOT_NAME, "No Fendi chest found (gadget_id filter)!")
        return

    sender_email = Player.GetAccountEmail()
    accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()

    Player.ChangeTarget(target)
    yield from Routines.Yield.wait(150)

    # --- LEADER: interact multiple times to ensure chest opens ---
    for attempt in range(CHEST_OPEN_ATTEMPTS):
        ConsoleLog(BOT_NAME, f"Leader opening chest (attempt {attempt + 1}/{CHEST_OPEN_ATTEMPTS})")
        Player.Interact(target, False)
        yield from Routines.Yield.wait(500)

    # Wait for the leader to finish
    while command_type_routine_in_message_is_active(sender_email, SharedCommandType.InteractWithTarget):
        yield from Routines.Yield.wait(250)
    while command_type_routine_in_message_is_active(sender_email, SharedCommandType.PickUpLoot):
        yield from Routines.Yield.wait(1000)
    yield from Routines.Yield.wait(5000)

    # Command opening for all members with multiple attempts
    for account in accounts:
        if not account.AccountEmail or sender_email == account.AccountEmail:
            continue
        ConsoleLog(BOT_NAME, f"Ordering {account.AccountEmail} to open chest")

        for attempt in range(CHEST_OPEN_ATTEMPTS):
            ConsoleLog(BOT_NAME, f"{account.AccountEmail} attempt {attempt + 1}/{CHEST_OPEN_ATTEMPTS}")
            GLOBAL_CACHE.ShMem.SendMessage(
                sender_email,
                account.AccountEmail,
                SharedCommandType.InteractWithTarget,
                (target, 0, 0, 0),
            )
            yield from Routines.Yield.wait(1000)

        while command_type_routine_in_message_is_active(account.AccountEmail, SharedCommandType.InteractWithTarget):
            yield from Routines.Yield.wait(1000)
        while command_type_routine_in_message_is_active(account.AccountEmail, SharedCommandType.PickUpLoot):
            yield from Routines.Yield.wait(1000)
        yield from Routines.Yield.wait(5000)

    ConsoleLog(BOT_NAME, "ALL accounts opened chest!")
    yield


def resolve_fendi_fight() -> Generator:
    """
    Hold near Fendi's position, kill all enemies in compass range,
    and require 20s stable verification with neither Fendi Nin
    nor Soul of Fendi present before finishing.
    """
    boss_model_ids = {7064, 7065} #Fendi Nin and Soul of Fendi
    anchor_x, anchor_y = (-16022.9, 17889.9)
    compass_sq = Range.Compass.value ** 2
    anchor_soft_radius_sq = 750.0 ** 2
    stable_verify_ms = 0

    while stable_verify_ms < 20000:
        if Map.GetMapID() != SoO_lvl3:
            break
        if not Routines.Checks.Map.MapValid():
            yield from Routines.Yield.wait(500)
            continue

        player_pos = Player.GetXY()
        if not player_pos:
            yield from Routines.Yield.wait(500)
            continue

        dx_a = anchor_x - player_pos[0]
        dy_a = anchor_y - player_pos[1]
        if (dx_a * dx_a + dy_a * dy_a) > anchor_soft_radius_sq:
            Player.Move(anchor_x, anchor_y)

        nearest_id = 0
        nearest_dist_sq = float("inf")
        boss_present = False

        for agent_id in AgentArray.GetEnemyArray():
            if not Agent.IsAlive(agent_id):
                continue
            enemy_pos = Agent.GetXY(agent_id)
            if not enemy_pos:
                continue
            ax = enemy_pos[0] - anchor_x
            ay = enemy_pos[1] - anchor_y
            if (ax * ax + ay * ay) > compass_sq:
                continue
            if Agent.GetModelID(agent_id) in boss_model_ids:
                boss_present = True
            px = enemy_pos[0] - player_pos[0]
            py = enemy_pos[1] - player_pos[1]
            dist_sq = px * px + py * py
            if dist_sq < nearest_dist_sq:
                nearest_dist_sq = dist_sq
                nearest_id = agent_id

        if nearest_id:
            stable_verify_ms = 0
            Player.ChangeTarget(nearest_id)
            Player.Interact(nearest_id, True)
            target_pos = Agent.GetXY(nearest_id)
            if target_pos:
                dx = target_pos[0] - player_pos[0]
                dy = target_pos[1] - player_pos[1]
                if (dx * dx + dy * dy) > (Range.Earshot.value ** 2):
                    Player.Move(target_pos[0], target_pos[1])
        else:
            if not boss_present:
                stable_verify_ms += 500
            else:
                stable_verify_ms = 0
            Player.Move(anchor_x, anchor_y)

        yield from Routines.Yield.wait(500)

    ConsoleLog(BOT_NAME, "Fendi is dead -- area clear for 20s. Goodluck on chest ^.^")
    yield


# --- Wipe Recovery and Step Anchors ---

def wait_for_map_change(target_map_id, timeout_seconds=60):
    """Wait for map change with timeout"""
    ConsoleLog(BOT_NAME, f"Waiting for map change to {target_map_id}...")
    timeout = time.time() + timeout_seconds
    while True:
        current_map = Map.GetMapID()
        if current_map == target_map_id:
            ConsoleLog(BOT_NAME, f"Map change detected! Now in map {target_map_id}")
            yield
            return
        if time.time() > timeout:
            ConsoleLog(BOT_NAME, f"Timeout waiting for map {target_map_id}")
            yield
            return
        yield from Routines.Yield.wait(500)


def _on_party_wipe(bot: "Botting"):
    global L3_BOSS_ROUTE_UNLOCKED
    # Wait until we are alive again
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            bot.config.FSM.resume()
            return

    ConsoleLog("Res Check", "We ressed retrying!")
    yield from bot.Wait._coro_for_time(3000)

    # Map-safe anchors (YOU said you replaced jumps by headers)
    # These should be the JUMPABLE step names (anchors), not just visual headers.
    SHRINES_BY_MAP = {
        SoO_lvl1: [
            ("Secure return - L1", 8503.9,12143.5),
            ("Secure return 1 - L1", 15953.0, 11902.0)
        ],
        SoO_lvl2: [
            ("Secure return - L2", -14076.0, -19457.0)
        ],
        SoO_lvl3: [
            ("Secure return 1 - L3", 17544.0, 18810.0),
            ("Secure return boss - L3", -9686.32, 2632)
        ],
    }

    def pick_nearest_anchor(map_id: int, px: float, py: float) -> str:
        candidates = SHRINES_BY_MAP.get(map_id)
        if not candidates:
            return "Reset farm"  # generic fallback anchor

        best_name = candidates[0][0]
        best_d2 = float("inf")
        for name, sx, sy in candidates:
            d2 = (px - sx) ** 2 + (py - sy) ** 2
            if d2 < best_d2:
                best_d2 = d2
                best_name = name
        return best_name

    player_x, player_y = Player.GetXY()
    map_id = int(Map.GetMapID())

    bot.config.FSM.pause()

    # Not in dungeon maps -> resign and go to generic secure return
    if map_id not in (SoO_lvl1, SoO_lvl2, SoO_lvl3):
        bot.Multibox.ResignParty()
        yield from bot.Wait._coro_for_time(10000)
        bot.config.FSM.jump_to_state_by_name("Reset farm")
        bot.config.FSM.resume()
        return

    # Full party defeated -> let widget handle return
    if GLOBAL_CACHE.Party.IsPartyDefeated():
        yield from bot.Wait._coro_for_time(10000)
        bot.config.FSM.jump_to_state_by_name("Reset farm")
        bot.config.FSM.resume()
        return

    if map_id == SoO_lvl3:
        if L3_BOSS_ROUTE_UNLOCKED:
            chosen = "Secure return boss - L3"
        else:
            chosen = "Secure return 1 - L3"
    else:
        chosen = pick_nearest_anchor(map_id, float(player_x), float(player_y))                          

    ConsoleLog("Res Check", f"â†© wipe-route -> {chosen} (map={map_id}, pos=({player_x:.0f},{player_y:.0f}))")
    bot.config.FSM.jump_to_state_by_name(chosen)

    bot.config.FSM.resume()
    return


def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))

def S_Path(name: str, points: list[tuple[float, float]], map_id: Optional[int] = None) -> None:
    bot.States.AddHeader(name)

    # âœ… Step "ancre" jumpable
    bot.States.AddCustomState(_step_anchor, name)

    n = len(points)
    for i, (x, y) in enumerate(points, start=1):
        bot.Move.XY(float(x), float(y), step_name=f"{name} - {i}/{n}")

def UseSummons():
    """
    Uses:
    - Summons (model ID 30209)
    - Legionnary Summoning Crystal (model ID 37810)
    """

    summons = [
        ("Summons", 30209),
        ("Legionnary Crystal", 37810),
    ]

    for name, model_id in summons:
        ConsoleLog("UseSummons", f"Searching for {name}...", log=True)

        item_id = GLOBAL_CACHE.Inventory.GetFirstModelID(model_id)

        if item_id:
            ConsoleLog("UseSummons", f"{name} found (item_id: {item_id}), using...", log=True)
            GLOBAL_CACHE.Inventory.UseItem(item_id)
            yield from Routines.Yield.wait(1000)
            ConsoleLog("UseSummons", f"{name} used!", log=True)
        else:
            ConsoleLog("UseSummons", f"{name} not found in inventory", log=True)

    yield

_RANDOM_DISTRICTS = [
    6,  # EuropeItalian
    7,  # EuropeSpanish
    8,  # EuropePolish
    9,  # EuropeRussian
]

def _coro_travel_random_district(target_map_id: int) -> Generator:
    if _randomize_district:
        district = random.choice(_RANDOM_DISTRICTS)
        ConsoleLog(BOT_NAME, f"Traveling to map {target_map_id} with random district {district}")
        Map.TravelToDistrict(target_map_id, district=district)
        yield from Routines.Yield.wait(500)
        yield from bot.Wait._coro_for_map_load(target_map_id=target_map_id)
    else:
        yield from bot.Map._coro_travel(target_map_id, "")

def _step_anchor() -> Generator:
    yield

def loop_marker():
    """Empty marker for loop restart point"""
    ConsoleLog(BOT_NAME, "Starting new dungeon run...")
    yield

def apply_widget_policy_step() -> Generator:
    bot.Multibox.ApplyWidgetPolicy(
        enable_widgets=WIDGETS_TO_ENABLE,
        disable_widgets=WIDGETS_TO_DISABLE,
        apply_local=True,
    )
    yield from _disable_widgets_on_alts_only(_ALT_ONLY_DISABLE_WIDGETS)
    yield

# --- Settings and Bot UI Helpers ---

def _load_difficulty_setting() -> None:
    global _use_hard_mode, _difficulty_loaded
    if _difficulty_loaded:
        return

    if not bot.config.ini_key_initialized:
        bot.config.ini_key = IniManager().ensure_key(
            f"BottingClass/bot_{bot.config.bot_name}",
            f"bot_{bot.config.bot_name}.ini",
        )
        if bot.config.ini_key:
            IniManager().load_once(bot.config.ini_key)
        bot.config.ini_key_initialized = True

    if not bot.config.ini_key:
        return

    _use_hard_mode = bool(
        IniManager().get(
            key=bot.config.ini_key,
            section=_DIFFICULTY_SECTION,
            var_name=_DIFFICULTY_VAR,
            default=True,
        )
    )
    _difficulty_loaded = True

def _save_difficulty_setting() -> None:
    if not bot.config.ini_key:
        return
    IniManager().set(
        key=bot.config.ini_key,
        section=_DIFFICULTY_SECTION,
        var_name=_DIFFICULTY_VAR,
        value=_use_hard_mode,
    )

def _draw_difficulty_setting() -> None:
    import PyImGui
    global _use_hard_mode

    _load_difficulty_setting()
    new_hard_mode = PyImGui.checkbox("Hard Mode (HM)", _use_hard_mode)
    if new_hard_mode != _use_hard_mode:
        _use_hard_mode = new_hard_mode
        _save_difficulty_setting()

def _load_district_setting() -> None:
    global _randomize_district, _district_loaded
    if _district_loaded:
        return

    if not bot.config.ini_key_initialized:
        bot.config.ini_key = IniManager().ensure_key(
            f"BottingClass/bot_{bot.config.bot_name}",
            f"bot_{bot.config.bot_name}.ini",
        )
        if bot.config.ini_key:
            IniManager().load_once(bot.config.ini_key)
        bot.config.ini_key_initialized = True

    if not bot.config.ini_key:
        return

    _randomize_district = bool(
        IniManager().get(
            key=bot.config.ini_key,
            section=_DISTRICT_SECTION,
            var_name=_DISTRICT_VAR,
            default=True,
        )
    )
    _district_loaded = True

def _save_district_setting() -> None:
    if not bot.config.ini_key:
        return
    IniManager().set(
        key=bot.config.ini_key,
        section=_DISTRICT_SECTION,
        var_name=_DISTRICT_VAR,
        value=_randomize_district,
    )

def _draw_district_setting() -> None:
    import PyImGui
    global _randomize_district

    _load_district_setting()
    new_val = PyImGui.checkbox("Randomize EU District", _randomize_district)
    if new_val != _randomize_district:
        _randomize_district = new_val
        _save_district_setting()

def _draw_merchant_settings() -> None:
    import PyImGui
    global _merchant_enabled, _merchant_id_kits_target, _merchant_salvage_kits_target, _merchant_store_consumable_materials, _merchant_sell_materials, _merchant_sell_rare_mats, _merchant_buy_ectos, _merchant_ecto_threshold, _merchant_alt_wait_ms

    _load_merchant_settings()

    PyImGui.separator()
    PyImGui.text("Merchant (Guild Hall) â€” runs once on startup")
    PyImGui.separator()

    new_enabled = PyImGui.checkbox("Restock kits / sell materials on startup", _merchant_enabled)
    if new_enabled != _merchant_enabled:
        _merchant_enabled = new_enabled
        _save_merchant_settings()

    if _merchant_enabled:
        PyImGui.push_item_width(100)
        new_id = PyImGui.input_int("ID Kits target##bds_id", _merchant_id_kits_target)
        if new_id != _merchant_id_kits_target:
            _merchant_id_kits_target = max(0, new_id)
            _save_merchant_settings()

        new_sal = PyImGui.input_int("Salvage Kits target##bds_sal", _merchant_salvage_kits_target)
        if new_sal != _merchant_salvage_kits_target:
            _merchant_salvage_kits_target = max(0, new_sal)
            _save_merchant_settings()
        PyImGui.pop_item_width()

        new_sell = PyImGui.checkbox("Sell common materials##bds_sell", _merchant_sell_materials)
        if new_sell != _merchant_sell_materials:
            _merchant_sell_materials = new_sell
            _save_merchant_settings()

        new_store = PyImGui.checkbox(
            "Store consumable materials (Dust/Iron/Feather/Bone/Fiber)##bds_store_cons_mats",
            _merchant_store_consumable_materials,
        )
        if new_store != _merchant_store_consumable_materials:
            _merchant_store_consumable_materials = new_store
            _save_merchant_settings()

        new_rare = PyImGui.checkbox("Sell Diamond & Onyx to Rare Material Trader##bds_rare_mats", _merchant_sell_rare_mats)
        if new_rare != _merchant_sell_rare_mats:
            _merchant_sell_rare_mats = new_rare
            _save_merchant_settings()

        new_ectos = PyImGui.checkbox("Buy Glob of Ectoplasm when storage over threshold##bds_ectos", _merchant_buy_ectos)
        if new_ectos != _merchant_buy_ectos:
            _merchant_buy_ectos = new_ectos
            _save_merchant_settings()

        if _merchant_buy_ectos:
            new_thresh = PyImGui.input_int("Storage threshold (gold)##bds_ecto_thresh", _merchant_ecto_threshold)
            if new_thresh != _merchant_ecto_threshold:
                _merchant_ecto_threshold = max(0, new_thresh)
                _save_merchant_settings()

        PyImGui.push_item_width(100)
        new_wait = PyImGui.input_int("Alt settle wait (ms)##bds_alt_wait", _merchant_alt_wait_ms)
        if new_wait != _merchant_alt_wait_ms:
            _merchant_alt_wait_ms = max(0, min(_MAX_ALT_SETTLE_WAIT_MS, new_wait))
            _save_merchant_settings()
        PyImGui.pop_item_width()
        PyImGui.same_line(0, 6)
        PyImGui.text("(time given to alts to reach NPCs and finish)")


def _draw_bds_settings() -> None:
    import PyImGui
    PyImGui.text("BDS Settings")
    PyImGui.separator()
    _draw_difficulty_setting()
    _draw_district_setting()
    _draw_merchant_settings()

# ==================== INITIALIZATION ====================

bot.SetMainRoutine(farm_bds_routine)
bot.UI.override_draw_config(_draw_bds_settings)


# ==================== UI AND ENTRYPOINT ====================

def _draw_bds_window_with_stats_tab() -> None:
    import PyImGui
    from Py4GWCoreLib import ImGui, IniManager, Routines

    main_child_dimensions = (500, 350)
    iconwidth = 96

    if not bot.config.ini_key_initialized:
        bot.config.ini_key = IniManager().ensure_key(
            f"BottingClass/bot_{bot.config.bot_name}",
            f"bot_{bot.config.bot_name}.ini",
        )
        IniManager().load_once(bot.config.ini_key)
        bot.config.ini_key_initialized = True
        _load_difficulty_setting()

    if not bot.config.ini_key:
        return

    if ImGui.Begin(
        ini_key=bot.config.ini_key,
        name=bot.config.bot_name,
        p_open=True,
        flags=PyImGui.WindowFlags.AlwaysAutoResize,
    ):
        if PyImGui.begin_tab_bar(bot.config.bot_name + "_tabs"):
            if PyImGui.begin_tab_item("Main"):
                if PyImGui.begin_child(f"{bot.config.bot_name} - Main", main_child_dimensions, True, PyImGui.WindowFlags.NoFlag):
                    bot.UI._draw_main_child(main_child_dimensions, TEXTURE, iconwidth)
                    PyImGui.end_child()
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Navigation"):
                PyImGui.text("Jump to step (filtered by step index):")
                bot.UI._draw_fsm_jump_button()
                PyImGui.separator()
                bot.UI.draw_fsm_tree_selector_ranged(child_size=main_child_dimensions)
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Settings"):
                bot.UI._draw_settings_child()
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Help"):
                bot.UI._draw_help_child()
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Debug"):
                bot.UI.draw_debug_window()
                PyImGui.end_tab_item()

            if PyImGui.begin_tab_item("Statistics"):
                _draw_bds_stats()
                PyImGui.end_tab_item()

            PyImGui.end_tab_bar()

    ImGui.End(bot.config.ini_key)

    if Routines.Checks.Map.MapValid():
        bot.UI.DrawPath(
            bot.config.config_properties.follow_path_color.get("value"),
            bot.config.config_properties.use_occlusion.is_active(),
            bot.config.config_properties.snap_to_ground_segments.get("value"),
            bot.config.config_properties.floor_offset.get("value"),
        )

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Bone Dragon Staff Farmer bot", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("multi-account bot to farm Bone Dragon Staff")
    PyImGui.spacing()
    PyImGui.bullet_text("Requirements:")
    PyImGui.bullet_text("- Any number of accounts, but for best performance, 8 well-geared accounts is recommended")
    PyImGui.bullet_text("- Custom Behavior widget enabled on all accounts")
    PyImGui.bullet_text("- Launch the script on the party leader only")
    PyImGui.bullet_text("Designed for Normal Mode (NM) and Hard Mode (HM), check bot settings for more details.")
    
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Oo SKY oO")
    PyImGui.bullet_text("Contributors: Wick-Divinus, Sloppynacho, XLeek, Yodz, Le Z")
    PyImGui.end_tooltip()

def main():
    bot.Update()
    draw_window_sig = inspect.signature(bot.UI.draw_window)
    if "extra_tabs" in draw_window_sig.parameters:
        bot.UI.draw_window(
            icon_path=TEXTURE,
            main_child_dimensions=(500, 350),
            extra_tabs=[("Statistics", _draw_bds_stats)],
        )
    else:
        _draw_bds_window_with_stats_tab()


if __name__ == "__main__":
    main()
