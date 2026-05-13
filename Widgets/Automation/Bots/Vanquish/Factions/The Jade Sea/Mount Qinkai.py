from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Map, Agent, ConsoleLog, Player, Timer, IniManager, SharedCommandType
from Py4GWCoreLib.enums_src.Title_enums import TitleID, TITLE_TIERS
import Py4GW
import PyImGui
import os
import random
import time
BOT_NAME = "VQ Mount Qinkai"
MODULE_NAME = "Mount Qinkai (Vanquish)"
MODULE_ICON = "Textures\\Module_Icons\\Vanquish - Mount Qinkai.png"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Sources", "ApoSource", "textures", "VQ_Helmet.png")
OUTPOST_TO_TRAVEL = 389 # Mount Qinkai outpost
CAVALON= 193 # Cavalon for faction donation
LOAD_RESUME_STABLE_MS = 1500
CONSET_RESTOCK_TARGET = 250
PCON_RESTOCK_TARGET = 250
SUMMONING_STONES_RESTOCK_TARGET = 10

_restock_use_conset = True
_restock_use_pcons = True
_restock_use_summoning_stones = True
_randomize_district = True
_RANDOM_DISTRICTS = [6, 7, 8, 9]
_settings_loaded = False
_SETTINGS_SECTION = "MountQinkaiSettings"
_RANDOMIZE_DISTRICT_KEY = "randomize_district"
_USE_CONSET_KEY = "use_conset"
_USE_PCONS_KEY = "use_pcons"
_USE_SUMMONING_STONES_KEY = "use_summoning_stones"
_CONSET_RESTOCK_TARGET_KEY = "conset_restock_target"
_PCON_RESTOCK_TARGET_KEY = "pcon_restock_target"
_SUMMONING_STONES_RESTOCK_TARGET_KEY = "summoning_stones_restock_target"
_MAX_RESTOCK_TARGET = 999

Vanquish_Path:list[tuple[float, float]] = [
      (-13384.42, -9866.60), #snake yetis  
      (-17490.23, -10193.84), #tendril
      (-13498.94, -4763.97),
      (-11674.48, -4599.29), #wallow patrol
      (-14406.66, -2555.92), #hole
      (-13735.23, -1511.41), #exit hole
      (-10319.44, 2159.07), #cave entrance
      (-7937.16, 3062.79), #wallow patrol
      (-9173.34, 7675.70),
      (-8041.39, 8370.92),
      (-4787.85, 6801.43), #clear
      (-3314.36, 7860.74),
      (-2001.17, 9037.19),
      (-6694.74, 2240.26), #out of cave
      (-9176.05, -13.35),
      (-6789.09, 189.53), #just in case
      (-6890.70, -3249.73), #lower wallows
      (-8307.69, -5465.48),
      (-5021.97, -3830.00),
      (-2310.74, -8512.54),
      (1983.03, -8555.85), #lower oxix
      (6484.80, 1017.07), #wallow patrol
      (6212.15, -8736.39), #beach onis
      (11368.18, -7458.21), #beach patrol
      (14728.93, -9258.35),
      (14774.19, -4493.75),
      (11622.91, -4078.38),
      (13287.39, 296.37),
      (16030.41, 6932.02),
      (11591.91, 7965.41), #water
      (10822.86, 9232.65),
      (7920.46, 5972.42),
      (6274.33, 7410.21), #hill
      (5824.00, 5289.97),
      (4266.50, 5832.48),
      
      (1506.29, 1406.74), #last aptrols
      (1737.57, 1202.17),
      (4450.66, 1146.03), #just in case
      (700.20, -398.73),
      (-273.59, -2516.34),
      (95.02, -3131.64),
      (-1687.58, -3565.68),

      
      
    ]

bot = Botting(BOT_NAME,
              upkeep_honeycomb_active=True,
              upkeep_hero_ai_active=True)

_load_resume_timer = Timer()
_loading_pause_active = False
_session_baselines: dict[str, int] = {}
_session_start_times: dict[str, float] = {}
_EXPANDED_TAB_CHILD_SIZE = (500, 620)
                
def bot_routine(bot: Botting) -> None:
    global Vanquish_Path
    _ensure_settings_loaded(bot)
    #events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    #end events
    
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Properties.Disable("auto_loot")
    bot.States.AddCustomState(lambda: _disable_looting(bot), "Disable Looting")
    bot.States.AddCustomState(lambda: _leave_party_before_start(bot), "Leave Party Before Start")
    bot.States.AddCustomState(lambda: _coro_travel_random_district(bot, OUTPOST_TO_TRAVEL), "Travel to Mount Qinkai")
    bot.Multibox.SummonAllAccounts()
    bot.Wait.ForTime(4000)
    bot.Multibox.InviteAllAccounts()
    
    bot.Party.SetHardMode(True)
    if _restock_use_conset:
        bot.Multibox.RestockConset(CONSET_RESTOCK_TARGET)
    if _restock_use_pcons:
        bot.Multibox.RestockAllPcons(PCON_RESTOCK_TARGET)
    if _restock_use_summoning_stones:
        bot.Multibox.RestockSummoningStones(SUMMONING_STONES_RESTOCK_TARGET)
    bot.Move.XYAndExitMap(-5490, 13672, 200) # Mount Qinkai
    bot.Wait.ForTime(4000)
    
    # Check faction allegiance and get blessing if needed
    current_luxon = Player.GetLuxonData()[0]
    current_kurzick = Player.GetKurzickData()[0]
    
    bot.States.AddCustomState(
        lambda bribe=current_kurzick >= current_luxon: _take_luxon_blessing(bot, bribe),
        "Take Luxon Blessing",
    )
    bot.States.AddHeader("Start Combat") #3
    if _restock_use_conset:
        bot.Multibox.UseConset()
    if _restock_use_pcons:
        bot.Multibox.UsePcons()
    if _restock_use_summoning_stones:
        bot.Multibox.UseSummoningStone()
    bot.States.AddManagedCoroutine("Upkeep Multibox Consumables", lambda: _upkeep_multibox_consumables(bot))
    
    bot.Move.FollowAutoPath(Vanquish_Path, "Kill Route")
    bot.Wait.UntilOutOfCombat()

    bot.Multibox.ResignParty()
    bot.Wait.UntilOnOutpost()
    bot.States.AddCustomState(lambda: _leave_party_before_start(bot), "Leave Party Before Cavalon")
    bot.States.AddCustomState(lambda: _coro_travel_random_district(bot, CAVALON), "Travel to Cavalon")
    bot.Multibox.SummonAllAccounts()
    bot.Wait.ForTime(4000)
    bot.Multibox.DonateFaction()
    bot.Wait.ForTime(30000)
    bot.States.JumpToStepName("[H]VQ Mount Qinkai_1")
    
    
def _leave_party_before_start(bot: "Botting"):
    yield from bot.helpers.Multibox._leave_party_on_all_accounts()
    GLOBAL_CACHE.Party.LeaveParty()
    yield from bot.Wait._coro_for_time(1000)


def _disable_looting(bot: "Botting"):
    bot.Properties.ApplyNow("auto_loot", "active", False)
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        account_email = getattr(account, "AccountEmail", "")
        if not account_email:
            continue
        options = GLOBAL_CACHE.ShMem.GetHeroAIOptionsFromEmail(account_email)
        if options is None:
            continue
        options.Looting = False
        GLOBAL_CACHE.ShMem.SetHeroAIOptionsByEmail(account_email, options)
    yield


def _dispatch_dialog_to_alts_only(dialog_id: int) -> list[tuple[str, int]]:
    sender_email = Player.GetAccountEmail()
    target = Player.GetTargetID()
    if not sender_email or target == 0:
        return []

    refs: list[tuple[str, int]] = []
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        account_email = getattr(account, "AccountEmail", "")
        if not account_email or account_email == sender_email:
            continue
        idx = int(GLOBAL_CACHE.ShMem.SendMessage(
            sender_email,
            account_email,
            SharedCommandType.SendDialogToTarget,
            (target, dialog_id, 0, 0),
        ))
        refs.append((account_email, idx))
    return refs


def _wait_for_alt_dialogs(message_refs: list[tuple[str, int]], timeout_ms: int = 5000):
    pending = {(email, idx) for email, idx in message_refs if idx >= 0}
    elapsed = 0
    while pending and elapsed < timeout_ms:
        completed: list[tuple[str, int]] = []
        for account_email, message_index in pending:
            message = GLOBAL_CACHE.ShMem.GetInbox(message_index)
            if not getattr(message, "Active", False):
                completed.append((account_email, message_index))
        for key in completed:
            pending.discard(key)
        if pending:
            yield from Routines.Yield.wait(250)
            elapsed += 250


def _reset_hero_ai_after_blessing(bot: "Botting") -> None:
    bot.ResetHeroAICombatState(
        active=True,
        following=True,
        avoidance=True,
        looting=False,
        targeting=True,
        combat=True,
        skills=True,
    )


def _send_priest_dialog(bot: "Botting", dialog_id: int):
    target = Player.GetTargetID()
    if target == 0:
        return
    alt_refs = _dispatch_dialog_to_alts_only(dialog_id)
    yield from Routines.Yield.Player.InteractAgent(target)
    yield from bot.Wait._coro_for_time(500)
    Player.SendDialog(dialog_id)
    yield from _wait_for_alt_dialogs(alt_refs)
    yield from bot.Wait._coro_for_time(500)


def _take_luxon_blessing(bot: "Botting", bribe_priest: bool):
    yield from bot.Move._coro_xy_and_interact_npc(-8394, -9801)
    yield from bot.Wait._coro_for_time(500)
    if bribe_priest:
        yield from _send_priest_dialog(bot, 0x84)  # Bribe if Kurzick faction is greater or equal to Luxon.
    yield from _send_priest_dialog(bot, 0x86)      # Get bounty.
    _reset_hero_ai_after_blessing(bot)
    yield from bot.Wait._coro_for_time(500)


def _coro_travel_random_district(bot: Botting, target_map_id: int):
    if _randomize_district:
        district = random.choice(_RANDOM_DISTRICTS)
        ConsoleLog(BOT_NAME, f"Traveling to map {target_map_id} with random EU district {district}")
        Map.TravelToDistrict(target_map_id, district=district)
        yield from Routines.Yield.wait(500)
        yield from bot.Wait._coro_for_map_load(target_map_id=target_map_id)
        return
    yield from bot.Map._coro_travel(target_map_id, "")


def _upkeep_multibox_consumables(bot :"Botting"):
    while True:
        yield from bot.Wait._coro_for_time(15000)
        if not Routines.Checks.Map.MapValid():
            continue
        
        if Routines.Checks.Map.IsOutpost():
            continue
        
        if _restock_use_conset:
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Essence_Of_Celerity.value, 
                                                GLOBAL_CACHE.Skill.GetID("Essence_of_Celerity_item_effect"), 0, 0))  
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Grail_Of_Might.value, 
                                                    GLOBAL_CACHE.Skill.GetID("Grail_of_Might_item_effect"), 0, 0))  
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Armor_Of_Salvation.value, 
                                                    GLOBAL_CACHE.Skill.GetID("Armor_of_Salvation_item_effect"), 0, 0))
        if _restock_use_pcons:
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Birthday_Cupcake.value, 
                                                    GLOBAL_CACHE.Skill.GetID("Birthday_Cupcake_skill"), 0, 0))  
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Golden_Egg.value, 
                                                    GLOBAL_CACHE.Skill.GetID("Golden_Egg_skill"), 0, 0))  
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Candy_Corn.value, 
                                                    GLOBAL_CACHE.Skill.GetID("Candy_Corn_skill"), 0, 0))  
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Candy_Apple.value, 
                                                    GLOBAL_CACHE.Skill.GetID("Candy_Apple_skill"), 0, 0))  
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Slice_Of_Pumpkin_Pie.value, 
                                                    GLOBAL_CACHE.Skill.GetID("Pie_Induced_Ecstasy"), 0, 0))    
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Drake_Kabob.value, 
                                                    GLOBAL_CACHE.Skill.GetID("Drake_Skin"), 0, 0))  
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Bowl_Of_Skalefin_Soup.value, 
                                                    GLOBAL_CACHE.Skill.GetID("Skale_Vigor"), 0, 0))  
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.Pahnai_Salad.value, 
                                                    GLOBAL_CACHE.Skill.GetID("Pahnai_Salad_item_effect"), 0, 0))  
            yield from bot.helpers.Multibox._use_consumable_message((ModelID.War_Supplies.value, 
                                                                    GLOBAL_CACHE.Skill.GetID("Well_Supplied"), 0, 0))
            for i in range(1, 5): 
                GLOBAL_CACHE.Inventory.UseItem(ModelID.Honeycomb.value)
                yield from bot.Wait._coro_for_time(250)
        if _restock_use_summoning_stones:
            yield from bot.helpers.Multibox._use_summoning_stone_message()
            

def _reverse_path():
    global Vanquish_Path
    if Map.IsVanquishCompleted():
        Vanquish_Path = []
        yield 
        return
    
    Vanquish_Path = list(reversed(Vanquish_Path))
    yield
    
def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            # Map invalid → release FSM and exit
            bot.config.FSM.resume()
            return

    # Player revived on same map → jump to recovery step
    bot.States.JumpToStepName("[H]Start Combat_3")
    bot.config.FSM.resume()
    
def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot))


def _runtime_map_ready() -> bool:
    return bool(Routines.Checks.Map.MapValid() and Player.IsPlayerLoaded())


def _should_suspend_for_loading() -> bool:
    global _loading_pause_active

    if not _runtime_map_ready():
        _loading_pause_active = True
        _load_resume_timer.Stop()
        return True

    if _loading_pause_active:
        if _load_resume_timer.IsStopped():
            _load_resume_timer.Start()
        if not _load_resume_timer.HasElapsed(LOAD_RESUME_STABLE_MS):
            return True
        _loading_pause_active = False
        _load_resume_timer.Stop()

    return False


def _ensure_bot_ini(bot: Botting) -> str:
    if not bot.config.ini_key_initialized:
        bot.config.ini_key = IniManager().ensure_key(
            f"BottingClass/bot_{bot.config.bot_name}",
            f"bot_{bot.config.bot_name}.ini",
        )
        bot.config.ini_key_initialized = True
    return bot.config.ini_key


def _load_settings(bot: Botting) -> None:
    global _randomize_district, _restock_use_conset, _restock_use_pcons, _restock_use_summoning_stones
    global CONSET_RESTOCK_TARGET, PCON_RESTOCK_TARGET, SUMMONING_STONES_RESTOCK_TARGET

    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return

    _randomize_district = IniManager().read_bool(
        ini_key, _SETTINGS_SECTION, _RANDOMIZE_DISTRICT_KEY, _randomize_district
    )
    _restock_use_conset = IniManager().read_bool(
        ini_key, _SETTINGS_SECTION, _USE_CONSET_KEY, _restock_use_conset
    )
    _restock_use_pcons = IniManager().read_bool(
        ini_key, _SETTINGS_SECTION, _USE_PCONS_KEY, _restock_use_pcons
    )
    _restock_use_summoning_stones = IniManager().read_bool(
        ini_key, _SETTINGS_SECTION, _USE_SUMMONING_STONES_KEY, _restock_use_summoning_stones
    )
    CONSET_RESTOCK_TARGET = max(0, min(_MAX_RESTOCK_TARGET, int(IniManager().read_int(
        ini_key, _SETTINGS_SECTION, _CONSET_RESTOCK_TARGET_KEY, CONSET_RESTOCK_TARGET
    ))))
    PCON_RESTOCK_TARGET = max(0, min(_MAX_RESTOCK_TARGET, int(IniManager().read_int(
        ini_key, _SETTINGS_SECTION, _PCON_RESTOCK_TARGET_KEY, PCON_RESTOCK_TARGET
    ))))
    SUMMONING_STONES_RESTOCK_TARGET = max(0, min(_MAX_RESTOCK_TARGET, int(IniManager().read_int(
        ini_key, _SETTINGS_SECTION, _SUMMONING_STONES_RESTOCK_TARGET_KEY, SUMMONING_STONES_RESTOCK_TARGET
    ))))


def _ensure_settings_loaded(bot: Botting) -> None:
    global _settings_loaded
    if _settings_loaded:
        return
    _load_settings(bot)
    _settings_loaded = True


def _save_settings(bot: Botting) -> None:
    ini_key = _ensure_bot_ini(bot)
    if not ini_key:
        return

    IniManager().write_key(ini_key, _SETTINGS_SECTION, _RANDOMIZE_DISTRICT_KEY, bool(_randomize_district))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _USE_CONSET_KEY, bool(_restock_use_conset))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _USE_PCONS_KEY, bool(_restock_use_pcons))
    IniManager().write_key(
        ini_key,
        _SETTINGS_SECTION,
        _USE_SUMMONING_STONES_KEY,
        bool(_restock_use_summoning_stones),
    )
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _CONSET_RESTOCK_TARGET_KEY, int(CONSET_RESTOCK_TARGET))
    IniManager().write_key(ini_key, _SETTINGS_SECTION, _PCON_RESTOCK_TARGET_KEY, int(PCON_RESTOCK_TARGET))
    IniManager().write_key(
        ini_key,
        _SETTINGS_SECTION,
        _SUMMONING_STONES_RESTOCK_TARGET_KEY,
        int(SUMMONING_STONES_RESTOCK_TARGET),
    )


def _draw_settings():
    global _restock_use_conset, _restock_use_pcons, _restock_use_summoning_stones
    global CONSET_RESTOCK_TARGET, PCON_RESTOCK_TARGET, SUMMONING_STONES_RESTOCK_TARGET
    global _randomize_district

    _ensure_settings_loaded(bot)

    PyImGui.text("Mount Qinkai Settings")
    PyImGui.separator()
    changed = False

    new_randomize = PyImGui.checkbox("Randomize EU District", _randomize_district)
    if new_randomize != _randomize_district:
        _randomize_district = new_randomize
        changed = True

    PyImGui.separator()
    PyImGui.text("Multibox Consumables")

    new_use_conset = PyImGui.checkbox("Restock & use Conset (Multibox)", _restock_use_conset)
    if new_use_conset != _restock_use_conset:
        _restock_use_conset = new_use_conset
        changed = True

    new_use_pcons = PyImGui.checkbox("Restock & use Pcons (Multibox)", _restock_use_pcons)
    if new_use_pcons != _restock_use_pcons:
        _restock_use_pcons = new_use_pcons
        changed = True

    new_use_summoning = PyImGui.checkbox("Restock & use Summoning Stones (Multibox)", _restock_use_summoning_stones)
    if new_use_summoning != _restock_use_summoning_stones:
        _restock_use_summoning_stones = new_use_summoning
        changed = True

    PyImGui.separator()
    new_conset_target = max(0, min(_MAX_RESTOCK_TARGET, PyImGui.input_int("Conset restock target##mount_qinkai_conset", CONSET_RESTOCK_TARGET)))
    if new_conset_target != CONSET_RESTOCK_TARGET:
        CONSET_RESTOCK_TARGET = new_conset_target
        changed = True

    new_pcon_target = max(0, min(_MAX_RESTOCK_TARGET, PyImGui.input_int("Pcons restock target##mount_qinkai_pcons", PCON_RESTOCK_TARGET)))
    if new_pcon_target != PCON_RESTOCK_TARGET:
        PCON_RESTOCK_TARGET = new_pcon_target
        changed = True

    new_summoning_target = max(0, min(_MAX_RESTOCK_TARGET, PyImGui.input_int("Summoning Stones restock target##mount_qinkai_summoning", SUMMONING_STONES_RESTOCK_TARGET)))
    if new_summoning_target != SUMMONING_STONES_RESTOCK_TARGET:
        SUMMONING_STONES_RESTOCK_TARGET = new_summoning_target
        changed = True

    if changed:
        _save_settings(bot)


def _get_title_track_accounts():
    accounts = list(GLOBAL_CACHE.ShMem.GetAllAccountData())
    if accounts:
        return accounts
    own_email = Player.GetAccountEmail()
    filtered = [account for account in accounts if getattr(account, "AccountEmail", "") == own_email]
    if filtered:
        return filtered
    own_name = Player.GetName()
    filtered = [account for account in accounts if getattr(account.AgentData, "CharacterName", "") == own_name]
    if filtered:
        return filtered
    return accounts[:1] if len(accounts) == 1 else []


def _draw_title_track():
    global _session_baselines, _session_start_times
    title_id = TitleID.Luxon
    title_idx = int(title_id)
    tiers = TITLE_TIERS.get(title_id, [])
    now = time.time()
    accounts = _get_title_track_accounts()
    if not accounts:
        PyImGui.text("No local account statistics available yet.")
        return
    for account in accounts:
        name = account.AgentData.CharacterName
        pts = account.TitlesData.Titles[title_idx].CurrentPoints
        if name not in _session_baselines:
            _session_baselines[name] = pts
            _session_start_times[name] = now
        tier_name = "Unranked"
        tier_rank = 0
        next_required = tiers[0].required if tiers else 0
        for i, tier in enumerate(tiers):
            if pts >= tier.required:
                tier_name = tier.name
                tier_rank = i + 1
                next_required = tiers[i + 1].required if i + 1 < len(tiers) else tier.required
            else:
                next_required = tier.required
                break
        is_maxed = tiers and pts >= tiers[-1].required
        gained = pts - _session_baselines[name]
        elapsed = now - _session_start_times[name]
        pts_hr = int(gained / elapsed * 3600) if elapsed > 0 else 0
        tier_missing = max(next_required - pts, 0)
        next_rank_progress_current = max(pts, 0)
        next_rank_progress_total = max(next_required, 1)

        PyImGui.separator()
        PyImGui.text(f"{name}  [{tier_name} (Rank {tier_rank})]")
        PyImGui.text(f"Total Points: {pts:,}")
        if is_maxed:
            PyImGui.text("Next Rank: Maxed")
            PyImGui.text("Points To Go: 0")
            PyImGui.progress_bar(1.0, -1, 0, "Complete")
            PyImGui.text_colored("Maximum rank achieved. Title complete.", (0.4, 1.0, 0.4, 1.0))
        else:
            PyImGui.text(f"Next Rank: {next_required:,}")
            PyImGui.text(f"Points To Go: {tier_missing:,}")
            frac = min(next_rank_progress_current / next_rank_progress_total, 1.0)
            PyImGui.progress_bar(frac, -1, 0, f"{next_rank_progress_current:,} / {next_rank_progress_total:,}")
        PyImGui.text(f"+{gained:,}  ({pts_hr:,}/hr)")


def _draw_statistics_tab() -> None:
    if PyImGui.begin_child("MountQinkaiStatisticsTabChild", _EXPANDED_TAB_CHILD_SIZE, False):
        PyImGui.text("Luxon Title Statistics")
        _draw_title_track()
    PyImGui.end_child()



bot.SetMainRoutine(bot_routine)
bot.UI.override_draw_config(_draw_settings)

def main():
    _ensure_settings_loaded(bot)
    if not _should_suspend_for_loading():
        bot.Update()
    bot.UI.draw_window(icon_path=TEXTURE, extra_tabs=[("Statistics", _draw_statistics_tab)])

if __name__ == "__main__":
    main()
