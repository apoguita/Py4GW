import PyImGui
from typing import Literal, Tuple

from Py4GWCoreLib.Builds import KeiranThackerayEOTN
from Py4GWCoreLib import (GLOBAL_CACHE, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          Map, ImGui, ActionQueueManager, Agent, Player, AgentArray,
                          TitleID, TITLE_TIERS)


class BotSettings:
    # Map/Outpost IDs
    EOTN_OUTPOST_ID = 642
    HOM_OUTPOST_ID = 646
    AUSPICIOUS_BEGINNINGS_MAP_ID = 849

    CUSTOM_BOW_ID = 0 # Change this is you already have a custom bow made for AB. Oppressor Flatbow 35405

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

    # Vanguard title cache (populated at start and after each successful run)
    VANGUARD_SCANNED: bool = False
    VANGUARD_RANK: int = 0
    VANGUARD_TIER_NAME: str = "–"
    VANGUARD_POINTS: int = 0
    VANGUARD_NEXT_REQUIRED: int | None = None

    # Misc
    DEBUG: bool = False


# ── Combat AI constants ───────────────────────────────────────────────────────
_MIKU_MODEL_ID      = 8443
_SHADOWSONG_ID      = 4264
_SOS_SPIRIT_IDS     = frozenset({4280, 4281, 4282})  # Anger, Hate, Suffering
_AOE_SKILLS         = {1380: 2000, 1372: 2000, 1083: 2000, 830: 2000, 192: 5000}
_MIKU_FAR_DIST      = 1000.0
_SPIRIT_FLEE_DIST   = 1700.0
_AOE_SIDESTEP_DIST  = 350.0

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
    _prev_reasons: set = set()  # used to log changes once, not every frame
    auto_combat_suppressed_by_empathy = False

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
        miku_combat = False
        me_combat = False
        mk_x = mk_y = 0.0
        if miku_id != 0 and not miku_dead:
            mk_x, mk_y = Agent.GetXY(miku_id)
            miku_far = _dist(me_x, me_y, mk_x, mk_y) > _MIKU_FAR_DIST
            miku_combat = Agent.IsInCombatStance(miku_id)
            me_combat = Agent.IsInCombatStance(me_id)

        if miku_dead and me_combat:
            nearest_enemy = Routines.Agents.GetNearestEnemy(Range.Earshot.value)
            ne_x, ne_y = Agent.GetXY(nearest_enemy)
            ex_x, ex_y = _escape_point(me_x, me_y, ne_x, ne_y, 1500)
            Player.Move(ex_x, ex_y)
            yield from Routines.Yield.wait(200)
            continue
        elif miku_dead:
            _set_pause("miku_dead")
        else:
            _clear_pause("miku_dead")
        
        if miku_far and not miku_dead and (me_combat or miku_combat):
            mk_x, mk_y = Agent.GetXY(miku_id)
            ex_x, ex_y = _escape_point(me_x, me_y, mk_x, mk_y, -200)
            Player.Move(ex_x, ex_y)
            yield from Routines.Yield.wait(200)

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

        # ── 4. Act on movement conditions (priority order) ────────────────────
        enemy_array_close = Routines.Agents.GetFilteredEnemyArray(me_x, me_y, 250, True)
        enemies_in_range = Routines.Agents.GetFilteredEnemyArray(me_x, me_y, 2000)
        enemies_close_alive = 0
        
        # Player will avoid spirits as long as other enemies exist, once all real enemies are dead and we are healthy engage spirits, makes runs slight faster
        if (spirit_id != 0 and len(enemies_in_range) > 3) or (spirit_id != 0 and Agent.GetHealth(Player.GetAgentID()) < 0.5):
            ex_x, ex_y = _escape_point(me_x, me_y, sp_x, sp_y, 600)
            Player.Move(ex_x, ex_y)
            yield from Routines.Yield.wait(200)
            continue
        # Moves player closer to enemies if Miku has not agroed yet
        if me_combat and not miku_combat:
            nearest_enemy = Routines.Agents.GetNearestEnemy(1200)
            ne_x, ne_y = Agent.GetXY(nearest_enemy)
            ex_x, ex_y = _escape_point(me_x, me_y, ne_x, ne_y, -200)
            Player.Move(ex_x, ex_y)
            yield from Routines.Yield.wait(200)
            continue
        # If two or more enemies are within melee of player, player will kite
        if len(enemy_array_close) > 1:
            nearest_enemy = Routines.Agents.GetNearestEnemy(300)
            ne_x, ne_y = Agent.GetXY(nearest_enemy)
            ex_x, ex_y = _escape_point(me_x, me_y, ne_x, ne_y, 200)
            Player.Move(ex_x, ex_y)
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
    if auto_combat_suppressed_by_empathy:
        bot.Properties.ApplyNow("auto_combat", "active", True)
    for reason in list(pause_reasons):
        _clear_pause(reason)


bot = Botting("Auspicious Beginnings",
              custom_build=KeiranThackerayEOTN())
     
def create_bot_routine(bot: Botting) -> None:
    InitializeBot(bot)
    def _initial_vanguard_scan():
        _update_vanguard_cache()
        yield
    bot.States.AddCustomState(lambda: _initial_vanguard_scan(), "ScanVanguardRank")
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
    yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.HOM_OUTPOST_ID, timeout=30000)
    bot.Properties.ApplyNow("halt_on_death","active", False)
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
        yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.EOTN_OUTPOST_ID, timeout=15000)

    bot.States.AddCustomState(lambda: _go_to_eotn(bot), "GoToEOTN")
      
def GetBonusBow(bot: Botting):
    bot.States.AddHeader("Check for Bonus Bow")

    if BotSettings.CUSTOM_BOW_ID != 0 or Routines.Checks.Inventory.IsModelInInventoryOrEquipped(11730):
        return
    else:
        bot.Map.Travel(194)
        bot.Move.XY(1592.00, -796.00)  # Move to material merchant area
        bot.States.AddCustomState(withdraw_gold, "Withdraw 20k Gold")
        bot.Move.XYAndInteractNPC(1592.00, -796.00)  # Common material merchant
        bot.States.AddCustomState(BuyShortbowMaterials, "Buy Weapoon Materials")
        bot.Wait.ForTime(1500)
        bot.Move.XYAndInteractNPC(-1387.00, -3910.00)  # Weapon crafter in Shing Jea Monastery
        bot.Wait.ForTime(1000)
        exec_fn = lambda: DoCraftShortbow(bot)
        bot.States.AddCustomState(exec_fn, "Craft Weapons")

_SHORTBOW_DATA = {
    "buy":    [(ModelID.Wood_Plank.value, 10), (ModelID.Plant_Fiber.value, 5)],
    "pieces": [(11730, [ModelID.Wood_Plank.value, ModelID.Plant_Fiber.value], [100, 50])],  # Longbow, 10 wood planks
}

def withdraw_gold(target_gold=20000, deposit_all=True):
    gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()

    if gold_on_char > target_gold and deposit_all:
        to_deposit = gold_on_char - target_gold
        GLOBAL_CACHE.Inventory.DepositGold(to_deposit)
        yield from Routines.Yield.wait(250)

    if gold_on_char < target_gold:
        to_withdraw = target_gold - gold_on_char
        GLOBAL_CACHE.Inventory.WithdrawGold(to_withdraw)
        yield from Routines.Yield.wait(250)

def BuyShortbowMaterials():
    for mat, count in _SHORTBOW_DATA["buy"]:
        for _ in range(count):
            yield from Routines.Yield.Merchant.BuyMaterial(mat)

def DoCraftShortbow(bot: Botting):
    for weapon_id, mats, qtys in _SHORTBOW_DATA["pieces"]:
        result = yield from Routines.Yield.Items.CraftItem(weapon_id, 5000, mats, qtys)
        if not result:
            ConsoleLog("DoCraftWeapon", f"Failed to craft weapon ({weapon_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield
        result = yield from Routines.Yield.Items.EquipItem(weapon_id)
        if not result:
            ConsoleLog("DoCraftWeapon", f"Failed to equip weapon ({weapon_id}).", Py4GW.Console.MessageType.Error)
            bot.helpers.Events.on_unmanaged_fail()
            return False
        yield
    return True

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
                yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.EOTN_OUTPOST_ID, timeout=15000)
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
                yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.EOTN_OUTPOST_ID, timeout=15000)

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
    #bot.Wait.ForMapLoad(target_map_id=BotSettings.HOM_OUTPOST_ID)

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
        #bot.Wait.ForMapLoad(target_map_id=642)
        yield from Routines.Yield.wait(500)
        GLOBAL_CACHE.Inventory.DepositGold(gold_on_char)
        yield from Routines.Yield.wait(500)
        bot.Move.XYAndExitMap(-4873.00, 5284.00, target_map_id=646)
        #bot.Wait.ForMapLoad(target_map_id=646)
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
            yield from Routines.Yield.wait(500)  # Small delay between purchases

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

    bot.Properties.Disable("pause_on_danger")
    bot.Move.XY(9724.85, -9671.76)
    bot.Properties.Enable("pause_on_danger")
    bot.Move.XY(8660.40, -8289.95)
    bot.Move.XY(5314.61, -7081.49)
    bot.Move.XY(3258.03, -7818.52)
    bot.Move.XY(2626.34, -10105.07)
    bot.Move.XY(-1015.23, -11944.23)
    bot.Move.XY(-2292.38, -9034.12)
    bot.Move.XY(-4000.69, -10906.09)
    bot.Move.XY(-5762.23, -10164.04)
    bot.Move.XY(-10148.25, -7884.56)
    bot.Move.XY(-13609.29, -8113.12)
    bot.Move.XY(-16070.03, -8736.15)
    #bot.Wait.UntilOutOfCombat()
    #bot.Properties.Disable("pause_on_danger")
    #path = [(8859.57, -7388.68), (9012.46, -9027.44)]
    #bot.Move.FollowAutoPath(path, step_name="To corner")
    #bot.Properties.Enable("pause_on_danger")
    #bot.Wait.UntilOutOfCombat()

    #bot.Move.XY(3113.68, -7008.46)
    #bot.Properties.Disable("pause_on_danger")
    #bot.Move.XY(2622.71, -9575.04, step_name="To patrol")
    #bot.Properties.Enable("pause_on_danger")
    #bot.Move.XY(325.22, -11728.24)
    
    
    #bot.Move.XY(-2860.21, -12198.37, step_name="To middle")
    #bot.Move.XY(-2934.80, -9382.55)
    
    #bot.Move.XY(-5109.05, -12717.40, step_name="To patrol 3")
    #bot.Properties.Disable("pause_on_danger")
    #bot.Move.XY(-6868.76, -12248.82, step_name="To patrol 4")
    #bot.Properties.Enable("pause_on_danger")

    #bot.Move.XY(-15858.25, -8840.35, step_name="To End of Path")
    bot.Wait.ForMapLoad(target_map_id=BotSettings.HOM_OUTPOST_ID)
    
    # Increment success counter at runtime, not setup time
    def _increment_success():
        _increment_runs_counters(bot, "success")
        _update_vanguard_cache()
        yield
    
    bot.States.AddCustomState(lambda: _increment_success(), "IncrementSuccessCounter")
    
    # Loop back to check gold and run quest again
    bot.States.JumpToStepName("[H]Check and Deposit Gold_3")

def _handle_bonus_bow(bot: Botting):
    bonus_bow_id = 11730

    if BotSettings.CUSTOM_BOW_ID != 0:
        bonus_bow_id = BotSettings.CUSTOM_BOW_ID
    has_bonus_bow = Routines.Checks.Inventory.IsModelInInventory(bonus_bow_id)
    if has_bonus_bow:
        if BotSettings.DEBUG:   
            print(f"[DEBUG] Bonus bow found, equipping")
        yield from bot.helpers.Items._equip(bonus_bow_id)
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

def _get_vanguard_rank_info():
    """Returns (rank, tier_name, current_points, next_required) for the Ebon Vanguard title.
    next_required is None if the title is maxed (rank 10)."""
    tiers = TITLE_TIERS.get(TitleID.Ebon_Vanguard, [])
    title = Player.GetTitle(TitleID.Ebon_Vanguard)
    current_points = title.current_points if title is not None else 0

    current_rank = 0
    tier_name = "Unranked"
    for t in tiers:
        if current_points >= t.required:
            current_rank = t.tier
            tier_name = t.name
        else:
            break

    if current_rank >= len(tiers):
        return current_rank, tier_name, current_points, None  # Maxed

    next_required = tiers[current_rank].required
    return current_rank, tier_name, current_points, next_required


def _update_vanguard_cache():
    rank, tier_name, pts, pts_next = _get_vanguard_rank_info()
    BotSettings.VANGUARD_RANK = rank
    BotSettings.VANGUARD_TIER_NAME = tier_name
    BotSettings.VANGUARD_POINTS = pts
    BotSettings.VANGUARD_NEXT_REQUIRED = pts_next
    BotSettings.VANGUARD_SCANNED = True


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

                    if PyImGui.collapsing_header("Vanguard Rank"):
                        if not BotSettings.VANGUARD_SCANNED:
                            PyImGui.text("Not scanned yet...")
                        else:
                            rank = BotSettings.VANGUARD_RANK
                            tier_name = BotSettings.VANGUARD_TIER_NAME
                            pts = BotSettings.VANGUARD_POINTS
                            pts_next = BotSettings.VANGUARD_NEXT_REQUIRED
                            if rank >= 10:
                                PyImGui.LabelTextV("Rank", "%s", [f"10 - {tier_name}"])
                                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 0.84, 0.0, 1.0))
                                PyImGui.LabelTextV("Status", "%s", ["Title Maxed!"])
                                PyImGui.pop_style_color(1)
                            else:
                                rank_label = f"{rank} - {tier_name}" if rank > 0 else "Unranked"
                                PyImGui.LabelTextV("Rank", "%s", [rank_label])
                                if pts_next is not None:
                                    PyImGui.LabelTextV("Points", "%s", [f"{pts:,} / {pts_next:,}"])
                                    PyImGui.LabelTextV("Needed", "%s", [f"{pts_next - pts:,} to next rank"])
                    
                PyImGui.end_tab_item()
            PyImGui.end_tab_bar()
        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log(bot.config.bot_name, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

if __name__ == "__main__":
    main()
