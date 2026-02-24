from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Agent, Player, ConsoleLog
from Py4GWCoreLib.Map import Map
from Py4GWCoreLib.enums_src.Title_enums import TitleID, TITLE_TIERS
import Py4GW
import os
import time
BOT_NAME = "Norn title farm by Wick Divinus"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Vanquish", "VQ_Helmet.png")
OLAFSTEAD = 645
VARAJAR_FELLS = 553

Norn_Path: list[tuple[float, float]] = [
    (-2484.73, 118.55),
    (-3059.12, -419.00),
    (-3301.01, -2008.23),
    (-2034, -4512),
    (-5278, -5771),
    (-5456, -7921),
    (-8793, -5837),
    (-14092, -9662),
    (-17260, -7906),
    (-21964, -12877),
    (-22275, -12462),
    (-21671, -2163),
    (-19592, 772),
    (-13795, -751),
    (-17012, -5376),
    (-12071, -4274),
    (-8351, -2633),
    (-4362, -1610),
    (-4316, 4033),
    (-8809, 5639),
    (-14916, 2475),
    (-11282, 5466),
    (-16051, 6492),
    (-16934, 11145),
    (-19378, 14555),
    (-22751, 14163),
    (-15932, 9386),
    (-13777, 8097),
    (-4729, 15385),
    (-2290, 14879),
    (-1810, 4679),
    (-6911, 5240),
    (-15471, 6384),
    (-411, 5874),
    (2859, 3982),
    (4909, -4259),
    (7514, -6587),
    (3800, -6182),
    (7755, -11467),
    (15403, -4243),
    (21597, -6798),
    (24522, -6532),
    (22883, -4248),
    (18606, -1894),
    (14969, -4048),
    (13599, -7339),
    (10056, -4967),
    (10147, -1630),
    (8963, 4043),
    (9339.46, 3859.12),
    (15576, 7156),
    (22838, 7914),
    (22961, 12757),
    (18067, 8766),
    (13311, 11917),
    (13714, 14520),
    (11126, 10443),
    (5575, 4696),
    (-503, 9182),
    (1582, 15275),
    (7857, 10409)
]

bot = Botting(BOT_NAME,
              upkeep_honeycomb_active=True)
                
def bot_routine(bot: Botting) -> None:
    global Norn_Path
    #events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    #end events
    
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=OLAFSTEAD)
    
    bot.Party.SetHardMode(True)
    auto_path_list = [(-328.0, 1240.0), (-1500.0, 1250.0)]
    bot.Move.FollowPath(auto_path_list)
    bot.Wait.ForMapLoad(target_map_id=553)
    bot.States.AddHeader("Start Combat")
    bot.Multibox.UseAllConsumables()
    bot.States.AddManagedCoroutine("Upkeep Multibox Consumables", lambda: _upkeep_multibox_consumables(bot))
    bot.States.AddManagedCoroutine("Anti-Stuck Watchdog", lambda: _anti_stuck_watchdog(bot))
    
    # Initial path to first blessing
    bot.Move.XY(-2484.73, 118.55, "Start")
    bot.Move.XY(-3059.12, -419.00, "Move to bridge")
    bot.Move.XY(-3301.01, -2008.23, "Move to shrine")
    bot.Move.XY(-2034, -4512, "Move to blessing 1")
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-1892.00, -4505.00)
    bot.Multibox.SendDialogToTarget(0x84) #Get Blessing 1
    bot.Wait.ForTime(5000)
    
    # Path to blessing 2
    bot.Move.XY(-5278, -5771, "Aggro: Berzerker")
    bot.Move.XY(-5456, -7921, "Aggro: Berzerker")
    bot.Move.XY(-8793, -5837, "Aggro: Berzerker")
    bot.Move.XY(-14092, -9662, "Aggro: Vaettir and Berzerker")
    bot.Move.XY(-17260, -7906, "Aggro: Vaettir and Berzerker")
    bot.Move.XY(-21964, -12877, "Aggro: Jotun")
    bot.Move.XY(-25341.00, -11957.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-25341.00, -11957.00) 
    bot.Multibox.SendDialogToTarget(0x84) # Edda Blessing 2
    bot.Wait.ForTime(10000)
    
    # Path to blessing 3
    bot.Move.XY(-22275, -12462, "Move to area 2")
    bot.Move.XY(-21671, -2163, "Aggro: Berzerker")
    bot.Move.XY(-19592, 772, "Aggro: Berzerker")
    bot.Move.XY(-13795, -751, "Aggro: Berzerker")
    bot.Move.XY(-17012, -5376, "Aggro: Berzerker")
    bot.Move.XY(-10606.23, -1625.26)
    bot.Move.XY(-12158.00, -4277.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-12158.00, -4277.00)
    bot.Multibox.SendDialogToTarget(0x84) #Blessing 3
    bot.Wait.ForTime(10000)
    
    # Path to blessing 4
    bot.Move.XY(-12071, -4274, "Aggro: Berzerker")
    bot.Move.XY(-8351, -2633, "Move to regroup")
    bot.Move.XY(-4362, -1610, "Aggro: Lake")
    bot.Move.XY(-4316, 4033, "Aggro: Lake")
    bot.Move.XY(-8809, 5639, "Aggro: Lake")
    bot.Move.XY(-14916, 2475)
    bot.Move.XY(-11204.00, 5479.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-11204.00, 5479.00)
    bot.Multibox.SendDialogToTarget(0x84) #Blessing 4
    bot.Wait.ForTime(10000)
    
    # Path to blessing 5
    bot.Move.XY(-11282, 5466, "Aggro: Elemental")
    bot.Move.XY(-16051, 6492, "Aggro: Elemental")
    bot.Move.XY(-16934, 11145, "Aggro: Elemental")
    bot.Move.XY(-19378, 14555)
    bot.Move.XY(-22889.00, 14165.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-22889.00, 14165.00)
    bot.Multibox.SendDialogToTarget(0x84) #Blessing 5
    bot.Wait.ForTime(10000)
    
    # Path to blessing 6
    bot.Move.XY(-22751, 14163, "Aggro: Elemental")
    bot.Move.XY(-15932, 9386, "Move to camp")
    bot.Move.XY(-13777, 8097, "Aggro: Lake")
    bot.Move.XY(-2217.00, 14914.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-2217.00, 14914.00)
    bot.Multibox.SendDialogToTarget(0x84) #Blessing 6
    bot.Wait.ForTime(10000)
    
    # Continue route
    # bot.Move.XY(-2290, 14879, "Aggro: Modnir")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(-1810, 4679, "Move to boss")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(-6911, 5240, "Aggro: Boss")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(-15471, 6384, "Move to regroup")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(-411, 5874, "Aggro: Modniir")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(2859, 3982, "Aggro: Ice Imp")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(4909, -4259, "Aggro: Ice Imp")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(7514, -6587, "Aggro: Berserker")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(3800, -6182, "Aggro: Berserker")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(7755, -11467, "Aggro: Elementals and Griffins")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(15403, -4243, "Aggro: Elementals and Griffins")
    # bot.Wait.UntilOutOfCombat()
    
    # # Path to blessing 7
    # bot.Move.XY(21597, -6798)
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(-2217.00, 14914.00)
    # bot.Wait.ForTime(5000)
    # bot.Move.XYAndInteractNPC(-2217.00, 14914.00)
    # bot.Multibox.SendDialogToTarget(0x84) #Blessing 7
    # bot.Wait.ForTime(10000)
    
    # bot.Move.XY(24522, -6532, "Aggro: Unknown")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(22883, -4248, "Aggro: Unknown")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(18606, -1894, "Aggro: Unknown")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(14969, -4048, "Aggro: Unknown")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(13599, -7339, "Aggro: Ice Imp")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(10056, -4967, "Aggro: Ice Imp")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(10147, -1630, "Aggro: Ice Imp")
    # bot.Wait.UntilOutOfCombat()
    
    # # Path to blessing 8
    # bot.Move.XY(8963, 4043, "Take blessing 8")
    # bot.Wait.ForTime(5000)
    # bot.Move.XYAndInteractNPC(8963, 4043)
    # bot.Multibox.SendDialogToTarget(0x84) #Blessing 8
    # bot.Wait.ForTime(10000)
    
    # bot.Move.XY(9339.46, 3859.12, "Aggro: Unknown")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(15576, 7156, "Aggro: Berserker")
    # bot.Wait.UntilOutOfCombat()
    
    # # Path to blessing 9
    # bot.Move.XY(22838, 7914, "Take blessing 9")
    # bot.Wait.ForTime(5000)
    # bot.Move.XYAndInteractNPC(22838, 7914)
    # bot.Multibox.SendDialogToTarget(0x84) #Blessing 9
    # bot.Wait.ForTime(10000)
    
    # # Final route section
    # bot.Move.XY(22961, 12757, "Move to shrine")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(18067, 8766, "Aggro: Modniir and Elemental")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(13311, 11917, "Aggro: Area")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(13714, 14520, "Aggro: Modniir and Elemental")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(11126, 10443, "Aggro: Modniir and Elemental")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(5575, 4696, "Aggro: Modniir and Elemental")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(-503, 9182, "Aggro: Modniir and Elemental 2")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(1582, 15275, "Aggro: Modniir and Elemental 2")
    # bot.Wait.UntilOutOfCombat()
    # bot.Move.XY(7857, 10409, "Aggro: Modniir and Elemental 2")
    # bot.Wait.UntilOutOfCombat()
    
    bot.Multibox.ResignParty()
    bot.Wait.UntilOnOutpost()
    
    bot.Wait.ForTime(5000)
    bot.States.JumpToStepName("[H]Norn title farm by Wick Divinus_1")
    
EXPLORABLE_TIMEOUT_SECONDS = 3 * 3600  # 3 hours

def _anti_stuck_resign(bot: "Botting"):
    """Called when the timeout fires: resign, wait for outpost, then restart."""
    yield from bot.helpers.Multibox._resignParty()
    while True:
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            continue
        if Routines.Checks.Map.IsOutpost():
            break
    bot.States.JumpToStepName("[H]Norn title farm by Wick Divinus_1")
    bot.config.FSM.resume()
    yield


def _anti_stuck_watchdog(bot: "Botting"):
    """Resign the party if stuck in explorable for more than 3 hours."""
    explorable_entry_time = None
    while True:
        yield from bot.Wait._coro_for_time(60000)  # check every minute
        if not Routines.Checks.Map.MapValid():
            explorable_entry_time = None
            continue
        if Routines.Checks.Map.IsOutpost():
            explorable_entry_time = None
            continue
        # We are in explorable
        if explorable_entry_time is None:
            explorable_entry_time = time.time()
            continue
        elapsed = time.time() - explorable_entry_time
        if elapsed >= EXPLORABLE_TIMEOUT_SECONDS:
            ConsoleLog(BOT_NAME, f"Anti-stuck: {elapsed/3600:.1f}h in explorable — resigning party.", Py4GW.Console.MessageType.Warning)
            explorable_entry_time = None
            bot.config.FSM.pause()
            bot.config.FSM.AddManagedCoroutine("AntiStuck_Resign", lambda: _anti_stuck_resign(bot))


def _upkeep_multibox_consumables(bot: "Botting"):
    while True:
        yield from bot.Wait._coro_for_time(15000)
        if not Routines.Checks.Map.MapValid():
            continue
        
        if Routines.Checks.Map.IsOutpost():
            continue
        
        yield from bot.helpers.Multibox._use_consumable_message((ModelID.Essence_Of_Celerity.value, 
                                            GLOBAL_CACHE.Skill.GetID("Essence_of_Celerity_item_effect"), 0, 0))  
        yield from bot.helpers.Multibox._use_consumable_message((ModelID.Grail_Of_Might.value, 
                                                GLOBAL_CACHE.Skill.GetID("Grail_of_Might_item_effect"), 0, 0))  
        yield from bot.helpers.Multibox._use_consumable_message((ModelID.Armor_Of_Salvation.value, 
                                                GLOBAL_CACHE.Skill.GetID("Armor_of_Salvation_item_effect"), 0, 0))
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
            
def _nearest_path_index(path: list, x: float, y: float) -> int:
    best, best_dist = 0, float('inf')
    for i, (px, py) in enumerate(path):
        d = (px - x) ** 2 + (py - y) ** 2
        if d < best_dist:
            best_dist, best = d, i
    return best


def _all_accounts_alive() -> bool:
    current_map = Map.GetMapID()
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        if account.AgentData.Map.MapID != current_map:
            continue  # skip accounts not in the same explorable (other maps, outpost, etc.)
        if account.AgentData.Health.Current <= 0:
            return False
    return True


def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(Player.GetAgentID()) or not _all_accounts_alive():
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            bot.config.FSM.resume()
            return

    # All accounts revived — resume route from nearest path point
    pos = Player.GetXY()
    if pos:
        nearest_idx = _nearest_path_index(Norn_Path, pos[0], pos[1])
        for (wx, wy) in Norn_Path[nearest_idx:]:
            if not Routines.Checks.Map.MapValid():
                break
            yield from bot.Move._coro_xy(wx, wy)

    bot.States.JumpToStepName("[H]Start Combat_3")
    bot.config.FSM.resume()
    
def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot)) 

bot.SetMainRoutine(bot_routine)

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Asura Title Farm", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Multi Account, farm Asura title in Magus Stones")
    PyImGui.spacing()
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Wick Divinus")
    PyImGui.end_tooltip()

_session_baselines: dict[str, int] = {}
_session_start_times: dict[str, float] = {}

def _draw_title_track():
    global _session_baselines, _session_start_times
    import PyImGui
    title_idx = int(TitleID.Norn)
    tiers = TITLE_TIERS.get(TitleID.Norn, [])
    now = time.time()
    for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
        name = account.AgentData.CharacterName
        pts = account.TitlesData.Titles[title_idx].CurrentPoints
        if name not in _session_baselines:
            _session_baselines[name] = pts
            _session_start_times[name] = now
        tier_name = "Unranked"
        prev_required = 0
        next_required = tiers[0].required if tiers else 0
        for i, tier in enumerate(tiers):
            if pts >= tier.required:
                tier_name = tier.name
                prev_required = tier.required
                next_required = tiers[i + 1].required if i + 1 < len(tiers) else tier.required
            else:
                next_required = tier.required
                break
        gained = pts - _session_baselines[name]
        elapsed = now - _session_start_times[name]
        pts_hr = int(gained / elapsed * 3600) if elapsed > 0 else 0
        PyImGui.separator()
        PyImGui.text(f"{name}  [{tier_name}]")
        PyImGui.text(f"Points: {pts:,} / {next_required:,}")
        if next_required > prev_required:
            frac = min((pts - prev_required) / (next_required - prev_required), 1.0)
            PyImGui.progress_bar(frac, -1, 0, f"{pts - prev_required:,} / {next_required - prev_required:,}")
        PyImGui.text(f"+{gained:,}  ({pts_hr:,}/hr)")

REFORGED_TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Sources", "Wick Divinus bots", "Reforged_Icon.png")
def main():
    bot.Update()
    bot.UI.draw_window(icon_path=REFORGED_TEXTURE, additional_ui=_draw_title_track)

if __name__ == "__main__":
    main()
