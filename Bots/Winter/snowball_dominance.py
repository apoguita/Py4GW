from Py4GWCoreLib import ConsoleLog, Map, Botting, Range, Utils, Agent, get_texture_for_model, GLOBAL_CACHE, Routines, \
    ActionQueueManager, AgentArray, Player, ModelID
import PyImGui
import random

# --- CONFIGURATION ---
BOT_NAME = "Snowball Dominance"
bot = Botting(BOT_NAME)

# --- GLOBAL VARIABLES ---
oliasInDanger = False
startedAttacking = False
successCounter = 0
failCounter = 0
idx = 0
run_times = []
totalGoldDeposited = 0


class BotSettings:
    STATS_FOR_NERDS: bool = True

    USE_FROSTY_TONICS: bool = True

    GOLD_DEPOSIT_ENABLED: bool = True
    GOLD_THRESHOLD_DEPOSIT: int = 80000  # 80 platinum - deposit when reached

    GOLD_STORAGE_MAX: int = 800000  # 800k - stop depositing when storage full
    BUY_ECTOS_ENABLED: bool = True
    GOLD_KEEP_FOR_ECTOS: int = 2000  # Keep 2k gold for safety

    EOTN_OUTPOST_ID: int = 821  # Eye of the North map ID
    DEBUG: bool = False  # Set to False to disable debug messages

    ECTOS_BOUGHT: int = 0


# Override the help window
bot.UI.override_draw_help(lambda: _draw_help())
bot.UI.override_draw_config(lambda: _draw_settings())  # Disable default config window


# --- MAIN ROUTINE ---
def SnowBallDominance(bot: Botting) -> None:
    InitializeBot(bot)

    if Map.GetMapID() != 821:
        def _state():
            yield from RndTravelState(821, use_districts=8)

        bot.States.AddCustomState(_state, "RndTravel -> EOTN")

    bot.States.AddHeader(BOT_NAME)
    bot.States.RemoveManagedCoroutine("NecroRoutine")
    bot.States.RemoveManagedCoroutine("rangerAttackRoutine")

    def _4state():
        yield from Use_Frosty_Tonics()

    bot.States.AddCustomState(_4state, "Use Frosty Tonics")

    heroes = GLOBAL_CACHE.Party.GetHeroes()
    if len(heroes) > 1:
        bot.Party.LeaveParty()

    for id, hero in enumerate(heroes):
        if hero.hero_id.GetID() != 14:
            bot.Party.LeaveParty()

    bot.Party.AddHero(hero_id=14)

    CheckAndDepositGold(bot)

    # --- QUEST START ---

    rnd_x = random.uniform(-30.0, 30.0)
    rnd_y = random.uniform(-30.0, 30.0)
    bot.Move.XY(-1425.14 + rnd_x, 3464 + rnd_y)
    bot.Dialogs.WithModel(6095, 0x83A601, "Get quest")
    bot.Dialogs.WithModel(6095, 0x84, "Game on")

    bot.Wait.ForMapToChange(793)

    # Hero Flag with Variance
    flag_x = 5144 + random.uniform(-100, 100)
    flag_y = -474 + random.uniform(-100, 100)
    bot.Party.FlagHero(hero_index=1, x=flag_x, y=flag_y)

    bot.States.AddManagedCoroutine("NecroRoutine", lambda: necroRoutine(bot))
    bot.States.AddManagedCoroutine("rangerAttackRoutine", lambda: attackRoutine(bot))

    bot.Wait.ForMapToChange(821)
    bot.Wait.ForMapLoad(821)

    def _3state():
        yield from Use_Frosty_Tonics()

    bot.States.AddCustomState(_3state, "Use Frosty Tonics")

    # --- QUEST TURN IN ---
    rnd_x = random.uniform(-30.0, 30.0)
    rnd_y = random.uniform(-30.0, 30.0)
    bot.Move.XY(-1425.14 + rnd_x, 3464 + rnd_y)
    bot.Dialogs.WithModel(6095, 0x83A607, "Claim Reward")

    CheckAndDepositGold(bot)

    def _state2():
        yield from RndTravelState(821, use_districts=8)

    bot.States.AddCustomState(_state2, "RndDistrictTravel -> EOTN")
    bot.States.JumpToStepName("[H]Snowball Dominance_1")


# --- COMBAT & LOGIC ---
def attackRoutine(bot: "Botting"):
    global startedAttacking, oliasInDanger, successCounter, run_times
    while True:
        if Map.GetMapID() == 793:
            if oliasInDanger and not startedAttacking:
                startedAttacking = True
                target = _find_best_target()
                if target != None:
                    Player.ChangeTarget(target)
                yield from Routines.Yield.wait(7000)
                GLOBAL_CACHE.SkillBar.UseSkill(5)
                yield from Routines.Yield.wait(1000)
                GLOBAL_CACHE.SkillBar.UseSkill(6)
                yield from Routines.Yield.wait(400)
            if startedAttacking:
                enemy_array = AgentArray.GetEnemyArray()
                if len(enemy_array) == 0:
                    # --- SUCCESS BLOCK ---
                    startedAttacking = False
                    oliasInDanger = False
                    successCounter += 1

                    bot.config.FSM.pause()
                    yield from Routines.Yield.wait(3000)
                    yield from RndTravelState(821, use_districts=8)
                    bot.config.FSM.resume()
                    break
                else:
                    skill = GLOBAL_CACHE.SkillBar.GetSkillData(5)
                    healSkill = GLOBAL_CACHE.SkillBar.GetSkillData(8)
                    fortSkill = GLOBAL_CACHE.SkillBar.GetSkillData(7)
                    target = _find_best_target()
                    if target != None:
                        Player.ChangeTarget(target)
                    if fortSkill.recharge == 0 and Agent.GetHealth(GLOBAL_CACHE.Player.GetAgentID()) < 0.80:
                        GLOBAL_CACHE.SkillBar.UseSkill(7)
                        yield from Routines.Yield.wait(1200)
                        continue
                    if healSkill.recharge == 0 and Agent.GetHealth(GLOBAL_CACHE.Player.GetAgentID()) < 0.35:
                        GLOBAL_CACHE.SkillBar.UseSkill(8)
                        yield from Routines.Yield.Movement.FollowPath([(2496.01, -210.70)])
                        yield from Routines.Yield.wait(8000)
                        continue
                    if skill.recharge == 0:
                        GLOBAL_CACHE.SkillBar.UseSkill(5)
                        yield from Routines.Yield.wait(1000)
                        continue
                    else:
                        GLOBAL_CACHE.SkillBar.UseSkill(6)
                        yield from Routines.Yield.wait(800)
        else:
            startedAttacking = False
            oliasInDanger = False
            break
        yield from Routines.Yield.wait(250)


# --- STANDARD FUNCTIONS ---
def _on_death(bot: "Botting"):
    global oliasInDanger, startedAttacking, failCounter
    failCounter += 1
    startedAttacking = False
    oliasInDanger = False
    bot.States.RemoveManagedCoroutine("NecroRoutine")
    bot.States.RemoveManagedCoroutine("rangerAttackRoutine")
    bot.Properties.ApplyNow("pause_on_danger", "active", False)
    bot.Properties.ApplyNow("halt_on_death", "active", True)
    bot.Properties.ApplyNow("movement_timeout", "value", 15000)
    bot.Properties.ApplyNow("auto_combat", "active", False)
    yield from RndTravelState(821, use_districts=8)
    fsm = bot.config.FSM
    fsm.resume()
    yield


def on_death(bot: "Botting"):
    print("Player is dead. Run Failed, Restarting...")
    ActionQueueManager().ResetAllQueues()
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnDeath", _on_death(bot))


def InitializeBot(bot: Botting) -> None:
    condition = lambda: on_death(bot)
    bot.Events.OnDeathCallback(condition)


def necroRoutine(bot: Botting):
    global oliasInDanger
    yield from Routines.Yield.Map.WaitforMapLoad(793, True)
    oliasAgentID = -1
    for id, hero in enumerate(GLOBAL_CACHE.Party.GetHeroes()):
        oliasAgentID = hero.agent_id

    skill4, skill5 = False, False
    while True:
        if Map.GetMapID() == 793:
            if not oliasInDanger:
                skill5 = False
                skill4 = False
            if not Agent.IsDead(oliasAgentID):
                if isAgentInDanger(oliasAgentID) and not oliasInDanger:
                    oliasInDanger = True
                    yield from Routines.Yield.wait(2000)
                    GLOBAL_CACHE.SkillBar.HeroUseSkill(oliasAgentID, 7, 1)
                    yield from Routines.Yield.wait(1200)
                    GLOBAL_CACHE.SkillBar.HeroUseSkill(oliasAgentID, 6, 1)
                    yield from Routines.Yield.wait(1700)
                    continue
                if oliasInDanger and not skill5:
                    skill5 = True
                    GLOBAL_CACHE.SkillBar.HeroUseSkill(oliasAgentID, 5, 1)
                    yield from Routines.Yield.wait(1500)
                    continue
                if oliasInDanger and not skill4:
                    skill4 = True
                    GLOBAL_CACHE.SkillBar.HeroUseSkill(oliasAgentID, 4, 1)
                    yield from Routines.Yield.wait(2300)
                    continue
                if oliasInDanger:
                    GLOBAL_CACHE.SkillBar.HeroUseSkill(oliasAgentID, 1, 1)
                    yield from Routines.Yield.wait(1000)
            else:
                break
        yield from Routines.Yield.wait(250)
        yield


def _find_best_target():
    my_pos = Player.GetXY()
    enemies = [e for e in AgentArray.GetEnemyArray() if
               Agent.IsAlive(e) and Utils.Distance(my_pos, Agent.GetXY(e)) <= 5000]
    if not enemies: return None
    best_target = None
    max_neighbors = -1
    ADJACENT_RANGE = 200
    for e in enemies:
        e_pos = Agent.GetXY(e)
        neighbor_count = 0
        for other in enemies:
            if e != other and Utils.Distance(e_pos, Agent.GetXY(other)) <= ADJACENT_RANGE:
                neighbor_count += 1
        if neighbor_count > max_neighbors:
            max_neighbors = neighbor_count
            best_target = e
        elif neighbor_count == max_neighbors:
            if best_target is None or Utils.Distance(my_pos, e_pos) < Utils.Distance(my_pos, Agent.GetXY(best_target)):
                best_target = e
    return best_target


def isAgentInDanger(agentId, aggro_area=Range.Spellcast, aggressive_only=False):
    enemy_array = AgentArray.GetEnemyArray()
    if len(enemy_array) == 0: return False
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Utils.Distance(Agent.GetXY(agentId),
                                                                                             Agent.GetXY(
                                                                                                 agent_id)) <= aggro_area.value)
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsAlive(agent_id))
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: agentId != agent_id)
    if aggressive_only:
        enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsAggressive(agent_id))
    return len(enemy_array) > 0


def RndTravelState(map_id: int, use_districts: int = 4):
    global idx
    region = [2, 2, 2, 2];
    language = [4, 5, 9, 10]
    if use_districts < 1: use_districts = 1
    if use_districts > len(region): use_districts = len(region)
    tempidx = random.randint(0, use_districts - 1)
    while tempidx == idx:
        tempidx = random.randint(0, use_districts - 1)
    idx = tempidx
    Map.TravelToRegion(map_id, region[idx], 0, language[idx])
    yield from Routines.Yield.wait(8500)


def Use_Frosty_Tonics():
    if BotSettings.USE_FROSTY_TONICS:
        Frost_Tonic_id = GLOBAL_CACHE.Inventory.GetFirstModelID(ModelID.Frosty_Tonic.value)
        Tonic_cooldown_effect = GLOBAL_CACHE.Skill.GetID("Tonic_Tipsiness")
        Tonic_effect = GLOBAL_CACHE.Skill.GetID("Disguised_when_using_non_everlasting_tonics")

        if ((not Routines.Checks.Map.MapValid()) and (Map.IsExplorable())):
            yield

        if Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            yield

        if not GLOBAL_CACHE.Effects.HasEffect(GLOBAL_CACHE.Player.GetAgentID(),
                                              Tonic_cooldown_effect) and Frost_Tonic_id:
            GLOBAL_CACHE.Inventory.UseItem(Frost_Tonic_id)
            yield

    yield


def CheckAndDepositGold(bot: Botting) -> None:
    """Check gold on character, deposit if needed, buy ectos if conditions met"""
    if BotSettings.GOLD_DEPOSIT_ENABLED:
        def _check_and_deposit_gold(bot: Botting):
            current_map = Map.GetMapID()
            gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
            gold_in_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()

            if BotSettings.DEBUG:
                print(f"[GOLD CHECK] Map={current_map}, Gold={gold_on_char}, Storage={gold_in_storage}")

            # Deposit if character has gold above threshold
            if gold_on_char > BotSettings.GOLD_THRESHOLD_DEPOSIT:
                # Ensure we're in EOTN outpost
                if current_map != BotSettings.EOTN_OUTPOST_ID:
                    if BotSettings.DEBUG:
                        print(f"[GOLD] Traveling to EOTN from map {current_map}")
                    Map.Travel(BotSettings.EOTN_OUTPOST_ID)
                    yield from Routines.Yield.Map.WaitforMapLoad(BotSettings.EOTN_OUTPOST_ID)
                    current_map = BotSettings.EOTN_OUTPOST_ID

                # Deposit gold only if storage hasn't reached max
                if gold_in_storage < BotSettings.GOLD_STORAGE_MAX:
                    gold_to_deposit = gold_on_char
                    if BotSettings.DEBUG:
                        print(f"[GOLD] Depositing {gold_to_deposit} gold to storage")

                    GLOBAL_CACHE.Inventory.DepositGold(gold_to_deposit)
                    yield from Routines.Yield.wait(1500)

                    global totalGoldDeposited
                    totalGoldDeposited += gold_to_deposit

                    # Verify deposit
                    new_gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
                    new_gold_in_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()
                    if BotSettings.DEBUG:
                        print(f"[GOLD] After deposit: Character={new_gold_on_char}, Storage={new_gold_in_storage}")
                        print(f"[GOLD] Total deposited this session: {totalGoldDeposited}")
                else:
                    if BotSettings.DEBUG:
                        print(
                            f"[GOLD] Storage full ({gold_in_storage}/{BotSettings.GOLD_STORAGE_MAX}), keeping gold for ectos")
            else:
                if BotSettings.DEBUG:
                    print(
                        f"[GOLD] Below threshold ({gold_on_char}/{BotSettings.GOLD_THRESHOLD_DEPOSIT}), no deposit needed")

            # After deposit check, try to buy ectos if conditions are met
            current_map = Map.GetMapID()
            if current_map == BotSettings.EOTN_OUTPOST_ID:
                yield from BuyMaterials(bot)

            yield

        bot.States.AddCustomState(lambda: _check_and_deposit_gold(bot), "CheckAndDepositGold")


def BuyMaterials(bot: Botting):
    """Buy Glob of Ectoplasm if gold conditions are met"""
    # Check gold conditions for buying Glob of Ectoplasm
    if BotSettings.BUY_ECTOS_ENABLED:
        gold_in_inventory = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
        gold_in_storage = GLOBAL_CACHE.Inventory.GetGoldInStorage()

        # Only buy ectos if we have enough gold on character AND storage is full
        if gold_in_inventory >= BotSettings.GOLD_THRESHOLD_DEPOSIT and gold_in_storage >= BotSettings.GOLD_STORAGE_MAX:
            if BotSettings.DEBUG:
                print(f"[ECTO] Conditions met! Char={gold_in_inventory}, Storage={gold_in_storage}")
                print(f"[ECTO] Moving to Rare Material Trader...")

            # Move to and speak with rare material trader in EOTN
            yield from bot.Move._coro_xy_and_dialog(-2079.00, 1046.00, dialog_id=0x00000001)
            yield from Routines.Yield.wait(500)

            if BotSettings.DEBUG:
                print(
                    f"[ECTO] Starting ecto purchases (will buy until {BotSettings.GOLD_KEEP_FOR_ECTOS} gold remaining)...")

            # Buy ectos until we reach the gold threshold
            ectos_bought_this_session = 0
            for i in range(100):  # Max 100 ectos per session (safety limit)
                # Check current gold BEFORE buying
                current_gold = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()

                # Stop if we don't have enough gold for at least one more ecto
                # Assume max ecto price ~5000 to be safe
                if current_gold < (BotSettings.GOLD_KEEP_FOR_ECTOS + 5000):
                    if BotSettings.DEBUG:
                        print(f"[ECTO] Stopping - gold ({current_gold}) too low for another ecto")
                    break

                try:
                    yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Glob_Of_Ectoplasm.value)
                    ectos_bought_this_session += 1
                    BotSettings.ECTOS_BOUGHT += 1

                    # Check gold AFTER buying
                    new_gold = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
                    if BotSettings.DEBUG:
                        ecto_price = current_gold - new_gold
                        print(
                            f"[ECTO] Bought ecto #{ectos_bought_this_session} for {ecto_price}g (remaining: {new_gold}g)")

                    yield from Routines.Yield.wait(100)
                except Exception as e:
                    if BotSettings.DEBUG:
                        print(f"[ECTO] Error buying ecto: {e}")
                    break

            if BotSettings.DEBUG:
                final_gold = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
                print(f"[ECTO] Session complete: Bought {ectos_bought_this_session} ectos")
                print(f"[ECTO] Total ectos bought (all time): {BotSettings.ECTOS_BOUGHT}")
                print(f"[ECTO] Final gold: {final_gold}")
                print(f"[ECTO] Continuing with quest...")

        else:
            if BotSettings.DEBUG:
                print(
                    f"[ECTO] Conditions not met - Char: {gold_in_inventory}/{BotSettings.GOLD_THRESHOLD_DEPOSIT}, Storage: {gold_in_storage}/{BotSettings.GOLD_STORAGE_MAX}")

        yield


bot.SetMainRoutine(SnowBallDominance)


def _draw_help():
    import PyImGui
    PyImGui.text("Snowball Dominance Farmer")
    PyImGui.separator()
    PyImGui.text_wrapped("This bot automates the repeatable 'Snowball Dominance' quest.")
    PyImGui.text("QUEST REWARDS:")
    PyImGui.bullet_text("500 Gold")
    PyImGui.bullet_text("Wintersday Gifts")
    PyImGui.bullet_text("Tonics")
    PyImGui.separator()
    PyImGui.text("PREREQUISITES:")
    PyImGui.text_wrapped("Must complete: 'The Three Wise Norn' & 'Charr-broiled Plans'.")
    PyImGui.separator()
    PyImGui.text("REQUIREMENTS:")
    PyImGui.bullet_text("Olias (Necromancer) MUST be unlocked.")
    PyImGui.bullet_text("Strategy: Olias with 'Charm Animal' + Polar Bear.")
    PyImGui.bullet_text("Weapon: 20/20 HCT Set recommended.")
    PyImGui.text(f"Instance Time: {Map.GetInstanceUptime()}")


def _draw_settings():
    BotSettings.GOLD_DEPOSIT_ENABLED = PyImGui.checkbox("Deposit Gold at 80k", BotSettings.GOLD_DEPOSIT_ENABLED)
    BotSettings.BUY_ECTOS_ENABLED = PyImGui.checkbox("Buy Ecto When Gold Storage Full", BotSettings.BUY_ECTOS_ENABLED)
    BotSettings.USE_FROSTY_TONICS = PyImGui.checkbox("Use Frosty Tonics", BotSettings.USE_FROSTY_TONICS)
    BotSettings.STATS_FOR_NERDS = PyImGui.checkbox("Show Stats for nerds", BotSettings.STATS_FOR_NERDS)
    BotSettings.DEBUG = PyImGui.checkbox("Enable Debug Logs", BotSettings.DEBUG)


# --- GUI FUNCTIONS ---

def draw_window(bot: Botting):
    global totalGoldDeposited

    if BotSettings.STATS_FOR_NERDS:
        try:
            PyImGui.set_next_window_size(270.0, 360.0)
        except:
            pass

        if PyImGui.begin("Snowball Dominance Stats"):

            # --- CALC STATS ---
            total = successCounter + failCounter
            win_rate = 0.0
            if total > 0:
                win_rate = (successCounter / total) * 100.0

            # Get current gold
            try:
                current_gold = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()
                storage_gold = GLOBAL_CACHE.Inventory.GetGoldInStorage()
            except:
                print("Error retrieving gold amounts")
                current_gold = 0
                storage_gold = 0

            # --- HEADER ---
            PyImGui.text_colored(" Snowball Dominance Pro", (0, 255, 255, 255))
            PyImGui.separator()

            # --- WIN RATE ---
            PyImGui.text("Win Rate:")
            PyImGui.same_line(0.0, -1.0)
            wr_color = (0, 255, 0, 255) if win_rate >= 80 else (255, 255, 0, 255) if win_rate >= 50 else (
            255, 50, 50, 255)
            PyImGui.text_colored(f"{win_rate:.1f}%", wr_color)

            PyImGui.separator()

            # --- STATS TABLE ---
            PyImGui.columns(2, "stats_layout", False)

            # Left Side Labels
            PyImGui.text("Successes")
            PyImGui.text("Fails")
            PyImGui.text("Total Runs")
            PyImGui.text("")  # Spacer
            PyImGui.text("Current Gold")
            PyImGui.text("Storage Gold")
            PyImGui.text("Gold Deposited")
            PyImGui.text("")  # Spacer
            PyImGui.text("Ectos Bought")

            PyImGui.next_column()

            # Right Side Values
            PyImGui.text_colored(str(successCounter), (0, 255, 0, 255))
            PyImGui.text_colored(str(failCounter), (255, 50, 50, 255))
            PyImGui.text(str(total))
            PyImGui.text("")  # Spacer

            # Display current gold with color based on threshold
            gold_color = (255, 150, 0, 255) if current_gold >= BotSettings.GOLD_THRESHOLD_DEPOSIT else (
            255, 215, 0, 255)
            PyImGui.text_colored(f"{current_gold}", gold_color)

            # Display storage gold
            storage_pct = (storage_gold / BotSettings.GOLD_STORAGE_MAX) * 100 if BotSettings.GOLD_STORAGE_MAX > 0 else 0
            storage_color = (255, 100, 100, 255) if storage_pct >= 100 else (150, 255, 150, 255)
            PyImGui.text_colored(f"{storage_gold}", storage_color)

            # Display total deposited gold this session
            PyImGui.text_colored(f"{totalGoldDeposited}", (100, 200, 255, 255))

            PyImGui.text("")  # Spacer

            # Display ectos bought
            PyImGui.text_colored(f"{BotSettings.ECTOS_BOUGHT}", (200, 100, 255, 255))

            PyImGui.columns(1, "reset_layout", False)

            PyImGui.separator()

            # Status messages
            if BotSettings.GOLD_DEPOSIT_ENABLED:
                if current_gold >= BotSettings.GOLD_THRESHOLD_DEPOSIT:
                    PyImGui.text_colored("Will deposit next run!", (255, 200, 0, 255))
                else:
                    gold_remaining = BotSettings.GOLD_THRESHOLD_DEPOSIT - current_gold
                    PyImGui.text(f"{gold_remaining}g until deposit")

            # Storage and ecto status
            if BotSettings.BUY_ECTOS_ENABLED:
                if storage_gold >= BotSettings.GOLD_STORAGE_MAX:
                    if current_gold >= 90000:
                        PyImGui.text_colored("Will buy ectos!", (200, 100, 255, 255))
                    else:
                        PyImGui.text_colored("Storage full", (255, 150, 0, 255))

        PyImGui.end()


def main():
    bot.Update()
    draw_window(bot)
    bot.UI.draw_window()


if __name__ == "__main__":
    main()
