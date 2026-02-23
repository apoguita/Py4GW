import PyImGui
from typing import Literal, Tuple

from Py4GWCoreLib.Builds import KeiranThackerayEOTN
from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          Map, ImGui, ActionQueueManager, Agent, Player, AgentArray)


class BotSettings:
    # Map/Outpost IDs
    EOTN_OUTPOST_ID = 642
    HOM_OUTPOST_ID = 646
    AUSPICIOUS_BEGINNINGS_MAP_ID = 849

    # Gold threshold for deposit
    GOLD_THRESHOLD_DEPOSIT: int = 90000

    # Properties to enable/disable via setting tab
    WAR_SUPPLIES_ENABLED: bool = False

    # Runs counters
    TOTAL_RUNS: int = 0
    SUCCESSFUL_RUNS: int = 0
    FAILED_RUNS: int = 0
    
    # Material purchases
    ECTOS_BOUGHT: int = 0

    # Misc
    DEBUG: bool = False


# ── Combat AI constants ───────────────────────────────────────────────────────
_MIKU_MODEL_ID      = 8433
_SHADOWSONG_ID      = 4264
_SOS_SPIRIT_IDS     = frozenset({4280, 4281, 4282})  # Anger, Hate, Suffering
_AOE_SKILLS         = {1380: 2000, 1372: 2000, 1083: 2000, 830: 2000, 192: 5000}
_MIKU_FAR_DIST      = 1400.0
_MIKU_CLOSE_DIST    = 1100.0
_SPIRIT_FLEE_DIST   = 1600.0
_AOE_SIDESTEP_DIST  = 350.0

# White Mantle Ritualist priority targets (in kill priority order, highest first).
# IDs are base values + 10 adjustment for post-update model IDs.
_PRIORITY_TARGET_MODELS = [
    8301,  # PRIMARY  – Shadowsong / Bloodsong / Pain / Anguish rit
    8299,  # PRIMARY  – Rit/Monk: Preservation, strong heal, hex-remove, spirits
    8303,  # PRIORITY – Weapon of Remedy rit (hard-rez)
    8298,  #            Rit/Paragon spear caster
    8300,  #            SoS rit
    8302,  # 2nd prio – Minion-summoning rit
    8254,  #            Ritualist (additional)
]
_TARGET_SWITCH_INTERVAL = 1.0   # seconds between priority-target checks
_PRIORITY_TARGET_RANGE  = Range.Earshot.value  # only target priority enemies within this distance


def _escape_point(me_x: float, me_y: float, threat_x: float, threat_y: float, dist: float):
    """Return a point 'dist' away from threat, in the direction away from it."""
    import math
    dx = me_x - threat_x
    dy = me_y - threat_y
    length = math.sqrt(dx * dx + dy * dy)
    if length < 1:
        return me_x + dist, me_y
    return me_x + (dx / length) * dist, me_y + (dy / length) * dist


def _perp_point(me_x: float, me_y: float, enemy_x: float, enemy_y: float, dist: float):
    """Return a point 'dist' perpendicular to the line from me to enemy."""
    import math
    dx = enemy_x - me_x
    dy = enemy_y - me_y
    length = math.sqrt(dx * dx + dy * dy)
    if length < 1:
        return me_x + dist, me_y
    return me_x + (dy / length) * dist, me_y + (-dx / length) * dist


def _dist(x1: float, y1: float, x2: float, y2: float) -> float:
    import math
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def _combat_ai_loop(bot: "Botting"):
    """
    Managed coroutine that runs every frame (even when FSM is paused).
    Handles: Miku dead/far, spirit avoidance, AoE dodge, priority targeting.
    """
    import time
    BOT_NAME = "CombatAI_AB"
    AB_MAP = BotSettings.AUSPICIOUS_BEGINNINGS_MAP_ID
    fsm = bot.config.FSM
    pause_reasons: set = set()
    ai_paused_fsm = False   # True only when THIS coroutine issued the pause
    aoe_sidestep_at = 0.0
    aoe_caster_id = 0
    last_target_check = 0.0
    locked_target_id = 0                            # priority target we're locked onto
    locked_priority = len(_PRIORITY_TARGET_MODELS)  # priority index of locked target
    _prev_reasons: set = set()  # used to log changes once, not every frame

    ConsoleLog(BOT_NAME, "CombatAI loop started", Py4GW.Console.MessageType.Info)

    def _set_pause(reason: str):
        nonlocal ai_paused_fsm
        pause_reasons.add(reason)
        if not fsm.is_paused():
            fsm.pause()
            ai_paused_fsm = True

    def _clear_pause(reason: str):
        nonlocal ai_paused_fsm
        pause_reasons.discard(reason)
        # Only resume if WE were the ones who paused — avoids clobbering pause_on_danger
        if not pause_reasons and ai_paused_fsm and fsm.is_paused():
            fsm.resume()
            ai_paused_fsm = False

    while Map.GetMapID() == AB_MAP:
        me_id = Player.GetAgentID()
        if not Agent.IsValid(me_id) or Agent.IsDead(me_id):
            yield
            continue

        me_x, me_y = Agent.GetXY(me_id)
        enemy_array = AgentArray.GetEnemyArray()

        # ── 1. Miku tracking ─────────────────────────────────────────────────
        miku_id = Routines.Agents.GetAgentIDByModelID(_MIKU_MODEL_ID)
        miku_dead = miku_id != 0 and Agent.IsDead(miku_id)
        miku_far = False
        mk_x = mk_y = 0.0
        if miku_id != 0 and not miku_dead:
            mk_x, mk_y = Agent.GetXY(miku_id)
            miku_far = _dist(me_x, me_y, mk_x, mk_y) > _MIKU_FAR_DIST

        if miku_dead:
            _set_pause("miku_dead")
        else:
            _clear_pause("miku_dead")

        if miku_far:
            _set_pause("miku_far")
        else:
            _clear_pause("miku_far")

        # ── 2. Spirit avoidance ───────────────────────────────────────────────
        spirit_id = 0
        sp_x = sp_y = 0.0
        for eid in enemy_array:
            if Agent.IsDead(eid):
                continue
            model = Agent.GetModelID(eid)
            if model == _SHADOWSONG_ID or model in _SOS_SPIRIT_IDS:
                ex, ey = Agent.GetXY(eid)
                if _dist(me_x, me_y, ex, ey) < _SPIRIT_FLEE_DIST:
                    spirit_id = eid
                    sp_x, sp_y = ex, ey
                    break

        if spirit_id != 0:
            _set_pause("spirit")
        else:
            _clear_pause("spirit")

        # ── Debug: log reason changes once per transition ─────────────────────
        if BotSettings.DEBUG and pause_reasons != _prev_reasons:
            added   = pause_reasons - _prev_reasons
            removed = _prev_reasons - pause_reasons
            for r in added:
                ConsoleLog(BOT_NAME, f"PAUSE reason added: {r}", Py4GW.Console.MessageType.Warning)
            for r in removed:
                ConsoleLog(BOT_NAME, f"PAUSE reason cleared: {r}", Py4GW.Console.MessageType.Info)
            _prev_reasons = set(pause_reasons)

        now = time.time()

        # ── 3. Priority target selection (runs every frame, before movement) ──
        if now - last_target_check >= _TARGET_SWITCH_INTERVAL:
            last_target_check = now
            # Validate locked target: drop it if dead or out of range
            if locked_target_id != 0:
                if not Agent.IsValid(locked_target_id) or Agent.IsDead(locked_target_id):
                    locked_target_id = 0
                    locked_priority = len(_PRIORITY_TARGET_MODELS)
                else:
                    lx, ly = Agent.GetXY(locked_target_id)
                    if _dist(me_x, me_y, lx, ly) > _PRIORITY_TARGET_RANGE:
                        locked_target_id = 0
                        locked_priority = len(_PRIORITY_TARGET_MODELS)
            # Scan for a strictly higher-priority target (or any if none locked)
            best_id = 0
            best_priority = len(_PRIORITY_TARGET_MODELS)
            for eid in enemy_array:
                if Agent.IsDead(eid):
                    continue
                ex, ey = Agent.GetXY(eid)
                if _dist(me_x, me_y, ex, ey) > _PRIORITY_TARGET_RANGE:
                    continue
                model = Agent.GetModelID(eid)
                if model in _PRIORITY_TARGET_MODELS:
                    prio = _PRIORITY_TARGET_MODELS.index(model)
                    if prio < best_priority:
                        best_priority = prio
                        best_id = eid
            # Lock onto new target only if strictly higher priority than current lock
            if best_id != 0 and best_priority < locked_priority:
                locked_target_id = best_id
                locked_priority = best_priority
                if BotSettings.DEBUG:
                    ConsoleLog(BOT_NAME,
                               f"Locked priority target: model {_PRIORITY_TARGET_MODELS[locked_priority]} "
                               f"(prio {locked_priority}) agent {locked_target_id}",
                               Py4GW.Console.MessageType.Info)
            # Call the locked target every interval until dead
            if locked_target_id != 0:
                Player.ChangeTarget(locked_target_id)
                bot.Player.CallTarget()

        # ── 4. Act on movement conditions (priority order) ────────────────────
        if miku_dead:
            # Wait for Miku to revive — nothing to do but stay paused
            yield
            continue

        if spirit_id != 0:
            ex_x, ex_y = _escape_point(me_x, me_y, sp_x, sp_y, 600)
            Player.Move(ex_x, ex_y)
            yield from Routines.Yield.wait(200)
            continue

        if miku_far:
            Player.Move(mk_x, mk_y)
            yield from Routines.Yield.wait(200)
            continue

        # ── 5. AoE dodge ─────────────────────────────────────────────────────
        if aoe_caster_id != 0 and now >= aoe_sidestep_at:
            if Agent.IsValid(aoe_caster_id) and not Agent.IsDead(aoe_caster_id):
                tx, ty = Agent.GetXY(aoe_caster_id)
                sx, sy = _perp_point(me_x, me_y, tx, ty, _AOE_SIDESTEP_DIST)
                Player.Move(sx, sy)
                if BotSettings.DEBUG:
                    ConsoleLog(BOT_NAME, f"AoE dodge: stepping to ({sx:.0f}, {sy:.0f})", Py4GW.Console.MessageType.Info)
            aoe_caster_id = 0
        elif aoe_caster_id == 0:
            for eid in enemy_array:
                if Agent.IsDead(eid):
                    continue
                skill = Agent.GetCastingSkillID(eid)
                if skill in _AOE_SKILLS:
                    aoe_sidestep_at = now + _AOE_SKILLS[skill] / 1000.0
                    aoe_caster_id = eid
                    if BotSettings.DEBUG:
                        ConsoleLog(BOT_NAME, f"AoE detected: skill {skill} from agent {eid}, dodging in {_AOE_SKILLS[skill]}ms", Py4GW.Console.MessageType.Warning)
                    break

        yield

    # Cleanup: don't leave the FSM paused when exiting the map
    ConsoleLog(BOT_NAME, "CombatAI loop exiting map — cleaning up", Py4GW.Console.MessageType.Info)
    for reason in list(pause_reasons):
        _clear_pause(reason)


bot = Botting("Auspicious Beginnings",
              custom_build=KeiranThackerayEOTN())
     
def create_bot_routine(bot: Botting) -> None:
    InitializeBot(bot)
    GoToEOTN(bot)
    GetBonusBow(bot)
    QuestLoopEntry(bot)  # Start the quest loop
    
def QuestLoopEntry(bot: Botting) -> None:
    """Main quest loop entry point: checks gold, deposits if needed, then runs quest"""
    CheckAndDepositGold(bot)   # Check gold and deposit if threshold exceeded
    ExitToHOM(bot)             # Exit to HOM (skiped if already in HOM)
    PrepareForQuest(bot)       # Get ready in HOM
    EnterQuest(bot)            # Enter the quest
    RunQuest(bot)              # Run the quest (loops back to CheckAndDepositGold)

def _on_death(bot: "Botting"):
    _increment_runs_counters(bot, "fail")
    bot.Properties.ApplyNow("pause_on_danger", "active", False)
    bot.Properties.ApplyNow("halt_on_death","active", True)
    bot.Properties.ApplyNow("movement_timeout","value", 15000)
    bot.Properties.ApplyNow("auto_combat","active", False)
    yield from Routines.Yield.wait(8000)
    fsm = bot.config.FSM
    fsm.jump_to_state_by_name("[H]Prepare for Quest_5") 
    fsm.resume()                           
    yield  
    
def on_death(bot: "Botting"):
    print ("Player is dead. Run Failed, Restarting...")
    ActionQueueManager().ResetAllQueues()
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnDeath", _on_death(bot))

def _EnableCombat(bot: Botting) -> None:
        bot.OverrideBuild(KeiranThackerayEOTN())
        bot.Templates.Aggressive(enable_imp=False)
 
def _DisableCombat(bot: Botting) -> None:
    bot.Templates.Pacifist()

def InitializeBot(bot: Botting) -> None:
    condition = lambda: on_death(bot)
    bot.Events.OnDeathCallback(condition)

def GoToEOTN(bot: Botting) -> None:
    bot.States.AddHeader("Go to EOTN")

    def _go_to_eotn(bot: Botting):
        current_map = Map.GetMapID()
        should_skip_travel = current_map in [BotSettings.EOTN_OUTPOST_ID, BotSettings.HOM_OUTPOST_ID]
        if should_skip_travel:
            if BotSettings.DEBUG:   
                print(f"[DEBUG] Already in EOTN or HOM, skipping travel")
            return

        Map.Travel(BotSettings.EOTN_OUTPOST_ID)
        yield from Routines.Yield.wait(1000)
        yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.EOTN_OUTPOST_ID) 

    bot.States.AddCustomState(lambda: _go_to_eotn(bot), "GoToEOTN")
      
def GetBonusBow(bot: Botting):
    bot.States.AddHeader("Check for Bonus Bow")

    def _get_bonus_bow(bot: Botting):
        current_map = Map.GetMapID()
        should_skip_bonus_bow = current_map == BotSettings.HOM_OUTPOST_ID
        if should_skip_bonus_bow:
            if BotSettings.DEBUG:   
                print(f"[DEBUG] Already in HOM, skipping bonus bow")
            return

        if not Routines.Checks.Inventory.IsModelInInventoryOrEquipped(ModelID.Bonus_Nevermore_Flatbow.value):
            yield from bot.helpers.Items._spawn_bonus_items()
        yield from Routines.Yield.wait(1000)
        yield from bot.helpers.Items._destroy_bonus_items(exclude_list=[ModelID.Bonus_Nevermore_Flatbow.value])

    bot.States.AddCustomState(lambda: _get_bonus_bow(bot), "GetBonusBow")

def CheckAndDepositGold(bot: Botting) -> None:
    """Check gold on character, deposit if needed"""
    bot.States.AddHeader("Check and Deposit Gold")

    def _check_and_deposit_gold(bot: Botting):
        current_map = Map.GetMapID()
        gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
        gold_in_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()

        if BotSettings.DEBUG:   
            print(f"[DEBUG] CheckAndDepositGold: current_map={current_map}, gold={gold_on_char}, storage={gold_in_storage}")
        
        # Travel to EOTN if character has 90k+ gold
        if gold_on_char > BotSettings.GOLD_THRESHOLD_DEPOSIT:
            # Ensure we're in EOTN outpost
            if current_map != BotSettings.EOTN_OUTPOST_ID:
                if BotSettings.DEBUG:   
                    print(f"[DEBUG] Traveling to EOTN from map {current_map}")

                Map.Travel(BotSettings.EOTN_OUTPOST_ID)
                yield from Routines.Yield.wait(1000)
                yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.EOTN_OUTPOST_ID)
                current_map = BotSettings.EOTN_OUTPOST_ID

            # Deposit gold only if storage hasn't reached 800k
            if gold_in_storage < 800000:
                if BotSettings.DEBUG:   
                    print(f"Depositing {gold_on_char} gold in bank")
                GLOBAL_CACHE.Inventory.DepositGold(gold_on_char)
                yield from Routines.Yield.wait(1000)
            else:
                if BotSettings.DEBUG:   
                    print(f"Storage ({gold_in_storage}) has reached 800k+, keeping gold on character for ecto purchases")
        else:
            if BotSettings.DEBUG:   
                print(f"Gold ({gold_on_char}) below threshold ({BotSettings.GOLD_THRESHOLD_DEPOSIT}), skipping travel and deposit")
        
        # After deposit check, try to buy ectos if in EOTN outpost
        current_map = Map.GetMapID()
        if current_map == BotSettings.EOTN_OUTPOST_ID:
            yield from BuyMaterials(bot)

        if BotSettings.DEBUG:   
            print(f"[DEBUG] After gold check: current_map={current_map}, HOM={BotSettings.HOM_OUTPOST_ID}")

    bot.States.AddCustomState(lambda: _check_and_deposit_gold(bot), "CheckAndDepositGold")

def ExitToHOM(bot: Botting) -> None:
    bot.States.AddHeader("Exit to HOM")

    # Ensure we're in HOM for quest preparation
    def _exit_to_hom(bot: Botting):
        current_map = Map.GetMapID()
        should_exit_to_hom = current_map != BotSettings.HOM_OUTPOST_ID
        should_travel_to_eotn = current_map != BotSettings.EOTN_OUTPOST_ID

        if should_exit_to_hom:
            if BotSettings.DEBUG:   
                print(f"[DEBUG] Not in HOM, need to go there. Currently in map {current_map}")

            if should_travel_to_eotn:
                if BotSettings.DEBUG:   
                    print(f"[DEBUG] Not in EOTN, traveling there first")
                Map.Travel(BotSettings.EOTN_OUTPOST_ID)
                yield from Routines.Yield.wait(1000)
                yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.EOTN_OUTPOST_ID)

            if BotSettings.DEBUG:   
                print(f"[DEBUG] Moving to portal coordinates and exiting to HOM")

            # Use coroutine version to move to portal and exit
            yield from bot.Move._coro_xy_and_exit_map(-4873.00, 5284.00, target_map_id=BotSettings.HOM_OUTPOST_ID)
        else:
            if BotSettings.DEBUG:   
                print(f"[DEBUG] Already in HOM, skipping travel")
        yield

    bot.States.AddCustomState(lambda: _exit_to_hom(bot), "ExitToHOM")

def PrepareForQuest(bot: Botting) -> None:
    """Prepare for quest in HOM: acquire and equip Keiran's Bow"""
    bot.States.AddHeader("Prepare for Quest")
    bot.Wait.ForMapLoad(target_map_id=BotSettings.HOM_OUTPOST_ID)

    def _prepare_for_quest(bot: Botting):
        # Get Keiran's Bow if we don't have it
        if not Routines.Checks.Inventory.IsModelInInventoryOrEquipped(ModelID.Keirans_Bow.value):
            yield from bot.Move._coro_xy_and_dialog(-6583.00, 6672.00, dialog_id=0x0000008A)
        
        # Equip Keiran's Bow if not already equipped
        if not Routines.Checks.Inventory.IsModelEquipped(ModelID.Keirans_Bow.value):
            yield from bot.helpers.Items._equip(ModelID.Keirans_Bow.value)

    bot.States.AddCustomState(lambda: _prepare_for_quest(bot), "PrepareForQuest")

def deposit_gold(bot: Botting):
    gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()

    # Deposit all gold if character has 90k or more
    if gold_on_char >= 90000:
        bot.Map.Travel(target_map_id=642)
        bot.Wait.ForMapLoad(target_map_id=642)
        yield from Routines.Yield.wait(500)
        GLOBAL_CACHE.Inventory.DepositGold(gold_on_char)
        yield from Routines.Yield.wait(500)
        bot.Move.XYAndExitMap(-4873.00, 5284.00, target_map_id=646)
        bot.Wait.ForMapLoad(target_map_id=646)
        yield

def BuyMaterials(bot: Botting):
    """Buy Glob of Ectoplasm if gold conditions are met."""
    # Check gold conditions for buying Glob of Ectoplasm
    gold_in_inventory = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
    gold_in_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()
    
    if gold_in_inventory >= 90000 and gold_in_storage >= 800000:
        # Move to and speak with rare material trader
        yield from bot.Move._coro_xy_and_dialog(-2079.00, 1046.00, dialog_id=0x00000001)
        
        # Buy Glob of Ectoplasm until inventory gold drops below 2k
        for _ in range(100):  # Max 100 Globs of Ectoplasm
            current_gold = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
            if current_gold < 2000:  # Stop buying if gold is below 2k
                if BotSettings.DEBUG:
                    print(f"[DEBUG] Stopping ecto purchases - gold ({current_gold}) below 2k")
                break
            yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Glob_Of_Ectoplasm.value)
            BotSettings.ECTOS_BOUGHT += 1  # Increment ecto counter
            yield from Routines.Yield.wait(100)  # Small delay between purchases

def EnterQuest(bot: Botting) -> None:
    bot.States.AddHeader("Enter Quest")
    bot.Move.XYAndDialog(-6662.00, 6584.00, 0x63F) #enter quest with pool
    bot.Wait.ForMapLoad(target_map_id=BotSettings.AUSPICIOUS_BEGINNINGS_MAP_ID)
    
def RunQuest(bot: Botting) -> None:
    bot.States.AddHeader("Run Quest")
    _EnableCombat(bot)
    bot.States.AddManagedCoroutine("CombatAI_AB", lambda: _combat_ai_loop(bot))
    bot.Move.XY(11864.74, -4899.19)
    
    bot.States.AddCustomState(lambda: _handle_bonus_bow(bot), "HandleBonusBow")
    bot.States.AddCustomState(lambda: _handle_war_supplies(bot, True), "EnableWarSupplies")

    bot.Wait.UntilOnCombat(Range.Spirit)
    
    bot.States.AddCustomState(lambda: _handle_war_supplies(bot, False), "DisableWarSupplies")

    bot.Move.XY(10165.07, -6181.43, step_name="First Spawn")
    #bot.Wait.UntilOutOfCombat()
    bot.Properties.Disable("pause_on_danger")
    path = [(8859.57, -7388.68), (9012.46, -9027.44)]
    bot.Move.FollowAutoPath(path, step_name="To corner")
    bot.Properties.Enable("pause_on_danger")
    #bot.Wait.UntilOutOfCombat()

    bot.Move.XY(4518.81, -9504.34, step_name="To safe spot 0")
    bot.Wait.ForTime(4000)
    bot.Properties.Disable("pause_on_danger")
    bot.Move.XY(2622.71, -9575.04, step_name="To patrol")
    bot.Properties.Enable("pause_on_danger")
    bot.Move.XY(325.22, -11728.24)
    
    bot.Properties.Disable("pause_on_danger")
    bot.Move.XY(-2860.21, -12198.37, step_name="To middle")
    bot.Move.XY(-5109.05, -12717.40, step_name="To patrol 3")
    bot.Move.XY(-6868.76, -12248.82, step_name="To patrol 4")
    bot.Properties.Enable("pause_on_danger")

    bot.Move.XY(-15858.25, -8840.35, step_name="To End of Path")
    bot.Wait.ForMapToChange(target_map_id=BotSettings.HOM_OUTPOST_ID)

    _DisableCombat(bot)

    bot.Wait.ForMapLoad(target_map_id=BotSettings.HOM_OUTPOST_ID)
    
    # Increment success counter at runtime, not setup time
    def _increment_success():
        _increment_runs_counters(bot, "success")
        yield
    
    bot.States.AddCustomState(lambda: _increment_success(), "IncrementSuccessCounter")
    
    # Loop back to check gold and run quest again
    bot.States.JumpToStepName("[H]Check and Deposit Gold_3")

def _handle_bonus_bow(bot: Botting):
    has_bonus_bow = Routines.Checks.Inventory.IsModelInInventory(ModelID.Bonus_Nevermore_Flatbow.value)
    if has_bonus_bow:
        if BotSettings.DEBUG:   
            print(f"[DEBUG] Bonus bow found, equipping")
        yield from bot.helpers.Items._equip(ModelID.Bonus_Nevermore_Flatbow.value)
    else:
        if BotSettings.DEBUG:
            print(f"[DEBUG] Bonus bow not found in inventory or equipped")
    yield

def _handle_war_supplies(bot: Botting, value: bool):
    if BotSettings.WAR_SUPPLIES_ENABLED:
        if BotSettings.DEBUG:   
            print(f"[DEBUG] War supplies { 'enabled' if value else 'disabled' }")
        bot.Properties.ApplyNow("war_supplies", "active", value)
    yield

def _increment_runs_counters(bot: Botting, type: Literal["success", "fail"]):
    """Increment run counters based on run result"""
    BotSettings.TOTAL_RUNS += 1
    if type == "success":
        BotSettings.SUCCESSFUL_RUNS += 1
    elif type == "fail":
        BotSettings.FAILED_RUNS += 1

def _success_rate():
    if BotSettings.TOTAL_RUNS == 0:
        return "0.00%"
    return f"{BotSettings.SUCCESSFUL_RUNS / BotSettings.TOTAL_RUNS * 100:.2f}%"

def _fail_rate():
    if BotSettings.TOTAL_RUNS == 0:
        return "0.00%"
    return f"{BotSettings.FAILED_RUNS / BotSettings.TOTAL_RUNS * 100:.2f}%"

def war_supplies_obtained():
    return 5 * BotSettings.SUCCESSFUL_RUNS # 5 war supplies per run

def gold_obtained():
    return 1000 * BotSettings.SUCCESSFUL_RUNS # 1000 gold per run

def _draw_settings(bot: Botting):
    PyImGui.text("Bot Settings")

    # Gold threshold controls
    gold_threshold = BotSettings.GOLD_THRESHOLD_DEPOSIT
    gold_threshold = PyImGui.input_int("Gold deposit threshold", gold_threshold)

    # War Supplies controls
    use_war_supplies = BotSettings.WAR_SUPPLIES_ENABLED
    use_war_supplies = PyImGui.checkbox("Use War Supplies", use_war_supplies)

    # Debug controls
    debug = BotSettings.DEBUG
    debug = PyImGui.checkbox("Debug", debug)

    BotSettings.WAR_SUPPLIES_ENABLED = use_war_supplies
    BotSettings.GOLD_THRESHOLD_DEPOSIT = gold_threshold
    BotSettings.DEBUG = debug

bot.SetMainRoutine(create_bot_routine)
bot.UI.override_draw_config(lambda: _draw_settings(bot))

def main():
    try:
        projects_path = Py4GW.Console.get_projects_path()
        full_path = projects_path + "\\Sources\\ApoSource\\textures\\"
        main_child_dimensions: Tuple[int, int] = (350, 275)
        
        bot.Update()
        bot.UI.draw_window(icon_path=full_path + "Keiran_art.png")

        if PyImGui.begin(bot.config.bot_name, PyImGui.WindowFlags.AlwaysAutoResize):
            if PyImGui.begin_tab_bar(bot.config.bot_name + "_tabs"):
                if PyImGui.begin_tab_item("Main"):
                    PyImGui.dummy(*main_child_dimensions)

                    PyImGui.separator()

                    ImGui.push_font("Regular", 18)
                    PyImGui.text("Statistics")
                    ImGui.pop_font()
                    
                    if PyImGui.collapsing_header("Runs"):
                        # Total Runs
                        PyImGui.LabelTextV("Total", "%s", [str(BotSettings.TOTAL_RUNS)])    	

                        # Successful Runs
                        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.0, 1.0, 0.0, 1.0))
                        PyImGui.LabelTextV("Successful", "%s", [f"{BotSettings.SUCCESSFUL_RUNS} ({_success_rate()})"])
                        PyImGui.pop_style_color(1)

                        # Failed Runs
                        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 0.0, 0.0, 1.0))
                        PyImGui.LabelTextV("Failed", "%s", [f"{BotSettings.FAILED_RUNS} ({_fail_rate()})"])
                        PyImGui.pop_style_color(1)

                    if PyImGui.collapsing_header("Items/Gold obtained"):
                        PyImGui.LabelTextV("Gold", "%s", [str(gold_obtained())])    	
                        PyImGui.LabelTextV("War Supplies", "%s", [str(war_supplies_obtained())])
                        PyImGui.LabelTextV("Glob of Ectoplasm", "%s", [str(BotSettings.ECTOS_BOUGHT)])    	
                    
                PyImGui.end_tab_item()
            PyImGui.end_tab_bar()
        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log(bot.config.bot_name, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

if __name__ == "__main__":
    main()
