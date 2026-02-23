from Py4GWCoreLib import Botting, Routines, GLOBAL_CACHE, ModelID, Agent, Player, ConsoleLog
from Py4GWCoreLib.enums_src.Title_enums import TitleID, TITLE_TIERS
import Py4GW
import os
import time

BOT_NAME = "Asura title farm by Wick Divinus"
TEXTURE = os.path.join(Py4GW.Console.get_projects_path(), "Bots", "Vanquish", "VQ_Helmet.png")
RATASUM = 640

bot = Botting(BOT_NAME,
              upkeep_honeycomb_active=True)

def Routine(bot: Botting) -> None:
    PrepareForCombat(bot)
    Fight(bot)

def PrepareForCombat(bot: Botting) -> None:
    bot.States.AddHeader("Enable Combat Mode")
    bot.Templates.Multibox_Aggressive()
    bot.Templates.Routines.PrepareForFarm(map_id_to_travel=RATASUM)
    bot.Party.SetHardMode(True)

def Fight(bot: Botting) -> None:
    #events
    condition = lambda: OnPartyWipe(bot)
    bot.Events.OnPartyWipeCallback(condition)
    #end events
    bot.States.AddHeader("Start Combat")
    bot.Move.XY(-6062, -2688,"Exit Outpost")
    bot.Wait.ForMapLoad(target_map_name="Magus Stones")
    bot.Multibox.UseAllConsumables()
    bot.States.AddManagedCoroutine("Upkeep Multibox Consumables", lambda: _upkeep_multibox_consumables(bot))
    bot.Move.XY(14778.00, 13178.00)
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(14778.00, 13178.00)
    bot.Multibox.SendDialogToTarget(0x84)
    bot.Wait.ForTime(5000)
    bot.Move.XY(16722, 11774, "Moving")
    bot.Move.XY(17383, 8685, "Moving")
    bot.Move.XY(18162, 6670, "First Spider Group")
    bot.Move.XY(18447, 4537, "Second Spider Group")
    bot.Move.XY(18331, 2108, "Spider Pop")
    bot.Move.XY(17526, 143, "Spider Pop 2")
    bot.Move.XY(17205, -1355, "Third Spider Group")
    bot.Move.XY(17366, -5132, "Krait Group")
    bot.Move.XY(18111, -8030, "Krait Group")
    bot.Move.XY(18409, -8474, "Taking Blessing")
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(18409, -8474)
    bot.Multibox.SendDialogToTarget(0x84)
    bot.Wait.ForTime(10000)
    bot.Move.XY(18613, -11799, "Froggy Group")
    bot.Move.XY(17154, -15669, "Krait Patrol")
    bot.Move.XY(14250, -16744, "Second Patrol")
    bot.Move.XY(12186, -14139, "Krait Patrol")
    bot.Move.XY(12540, -13440, "Krait Patrol")
    bot.Move.XY(13234, -9948, "Krait Group")
    bot.Move.XY(8875, -9065, "Krait Group")
    bot.Move.XY(4671, -8699, "Krait Patrol")
    bot.Move.XY(1534, -5493, "Krait Group")
    bot.Move.XY(1052, -7074, "Moving")
    bot.Move.XY(-1029, -8724, "Spider Group")
    bot.Move.XY(-3439, -10339, "Krait Group")
    bot.Move.XY(-3024, -12586, "Spider Cave")
    bot.Move.XY(-2797, -13645, "Spider Cave")
    bot.Move.XY(-3393, -15633, "Spider Cave")
    bot.Move.XY(-4635, -16643, "Spider Pop")
    bot.Move.XY(-7814, -17796, "Spider Group")
    bot.Move.XY(-10109, -17520, "Taking Blessing")
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-10109, -17520)
    bot.Multibox.SendDialogToTarget(0x84)
    bot.Wait.ForTime(10000)
    bot.Move.XY(-9111, -17237, "Moving")
    bot.Move.XY(-10963, -15506, "Ranger Boss Group")
    bot.Move.XY(-12885, -14651, "Froggy Group")
    bot.Move.XY(-13975, -17857, "Corner Spiders")
    bot.Move.XY(-11912, -10641, "Froggy Group")
    bot.Move.XY(-8760, -9933, "Krait Boss Warrior")
    bot.Move.XY(-14030, -9780, "Froggy Coing Group")
    bot.Move.XY(-12368, -7330, "Froggy Group")
    bot.Move.XY(-16527, -8175, "Froggy Patrol")
    bot.Move.XY(-17391, -5984, "Froggy Group")
    bot.Move.XY(-15704, -3996, "Froggy Patrol")
    bot.Move.XY(-16609, -2607, "Moving")
    bot.Move.XY(-15476, 186, "Moving")
    bot.Move.XY(-16480, 2522, "Krait Group")
    bot.Move.XY(-17090, 5252, "Krait Group")
    bot.Move.XY(-19292, 8994, "Taking Blessing")
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-19292, 8994)
    bot.Multibox.SendDialogToTarget(0x84)
    bot.Wait.ForTime(10000)
    bot.Move.XY(-18640, 8724, "Moving")
    bot.Move.XY(-18484, 12021, "Krait Patrol")
    bot.Move.XY(-17180, 13093, "Krait Patrol")
    bot.Move.XY(-15072, 14075, "Froggy Group")
    bot.Move.XY(-11888, 15628, "Froggy Group")
    bot.Move.XY(-12043, 18463, "Froggy Boss Warrior")
    bot.Move.XY(-8876, 17415, "Froggy Group")
    bot.Move.XY(-5778, 19838, "Froggy Group")
    bot.Move.XY(-10970, 16860, "Moving Back")
    bot.Move.XY(-9301, 15054, "Moving")
    bot.Move.XY(-5379, 16642, "Krait Group")
    bot.Move.XY(-4430, 17268, "Krait Group")
    bot.Move.XY(-2974, 14197, "Krait Group")
    bot.Move.XY(-5228, 12475, "Boss Patrol")
    bot.Move.XY(-3468, 10837, "Lonely Patrol")
    bot.Move.XY(-2037, 10758, "Taking Blessing")
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-2037, 10758)
    bot.Multibox.SendDialogToTarget(0x84)
    bot.Wait.ForTime(10000)
    bot.Move.XY(-3804, 8017, "Krait Group")
    bot.Move.XY(-1346, 12360, "Moving")
    bot.Move.XY(874, 14367, "Moving")
    bot.Move.XY(3572, 13698, "Krait Group Standing")
    bot.Move.XY(5899, 14205, "Moving")
    bot.Move.XY(7407, 11867, "Krait Group")
    bot.Move.XY(9541, 9027, "Rider")
    bot.Move.XY(12639, 7537, "Rider Group")
    bot.Move.XY(9064, 7312, "Rider")
    bot.Move.XY(7986, 4365, "Krait group")
    bot.Move.XY(6341, 3029, "Krait Group")
    bot.Move.XY(7097, 92, "Krait Group")
    bot.Move.XY(4893, 445, "Taking Blessing")
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(4893, 445)
    bot.Multibox.SendDialogToTarget(0x84)
    bot.Wait.ForTime(10000)
    bot.Move.XY(8943, -985, "Krait Boss")
    bot.Move.XY(10949, -2056, "Krait Patrol")
    bot.Move.XY(13780, -5667, "Rider Patrol")
    bot.Move.XY(12444, -793, "Moving Back")
    bot.Move.XY(8193, -841, "Moving Back")
    bot.Move.XY(3284, -1599, "Krait Group")
    bot.Move.XY(-76, -1498, "Krait Group")
    bot.Move.XY(578, 719, "Krait Group")
    bot.Move.XY(316, 2489, "Krait Group")
    bot.Move.XY(-1018, -1235, "Moving Back")
    bot.Move.XY(-3195, -1538, "Krait Patrol")
    bot.Move.XY(-6322, -2565, "Krait Group")
    bot.Move.XY(-9231, -2629, "Taking Blessing")
    bot.Wait.ForTime(5000)
    bot.Move.XYAndInteractNPC(-9231, -2629)
    bot.Multibox.SendDialogToTarget(0x84)
    bot.Wait.ForTime(10000)
    bot.Move.XY(-11414, 4055, "Leftovers Krait")
    bot.Move.XY(-6907, 8461, "Moving")
    bot.Move.XY(-8689, 11227, "Leftovers Krait and Rider")
    bot.Multibox.ResignParty()
    bot.Wait.UntilOnOutpost()
    bot.Wait.ForTime(5000)
    bot.States.JumpToStepName("[H]Enable Combat Mode_1")


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
            
def _on_party_wipe(bot: "Botting"):
    while Agent.IsDead(Player.GetAgentID()):
        yield from bot.Wait._coro_for_time(1000)
        if not Routines.Checks.Map.MapValid():
            # Map invalid → release FSM and exit
            bot.config.FSM.resume()
            return

    # Player revived on same map → jump to recovery step
    bot.States.JumpToStepName("[H]Start Combat_2")
    bot.config.FSM.resume()
    
def OnPartyWipe(bot: "Botting"):
    ConsoleLog("on_party_wipe", "event triggered")
    fsm = bot.config.FSM
    fsm.pause()
    fsm.AddManagedCoroutine("OnWipe_OPD", lambda: _on_party_wipe(bot)) 

bot.SetMainRoutine(Routine)

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
    title_idx = int(TitleID.Asuran)
    tiers = TITLE_TIERS.get(TitleID.Asuran, [])
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
