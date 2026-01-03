from __future__ import annotations
from typing import List, Tuple, Generator, Any
import os
from Py4GW import Console
import PyImGui
from Py4GWCoreLib import Key, Keystroke, Map, CHAR_MAP
from AccountData import MODULE_NAME
from Py4GWCoreLib import (GLOBAL_CACHE, Agent, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          AutoPathing, ImGui, ActionQueueManager,)
LAST_CHARACTER_NAME: str = ""
LAST_PRIMARY_PROF: str = ""
LAST_CAMPAIGN: str = "Nightfall"

bot = Botting("Chahbek Village ZM")
 
def create_bot_routine(bot: Botting) -> None:
    global LAST_CHARACTER_NAME, LAST_PRIMARY_PROF, LAST_CAMPAIGN
    # capture early while still in game
    LAST_CHARACTER_NAME = GLOBAL_CACHE.Player.GetName() or LAST_CHARACTER_NAME
    try:
        p, _ = Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
        if p:
            LAST_PRIMARY_PROF = p
    except Exception:
        pass

    SkipTutorialDialog(bot)                    # Skip opening tutorial
    TakeZM(bot)                                #Take ZM
    TravelToChabbek(bot)                       # Go to chabbek village
    Meeting_First_Spear_Jahdugar(bot)          # Meeting First Spear Jahdugar
    ConfigureFirstBattle(bot)                  # Configure first battle setup
    EnterChahbekMission(bot)                   # Enter Chahbek mission
    TakeReward(bot)                            # Take Reward 
    UnlockXunlai(bot)                          # Unlock Storage
    DepositReward(bot)
    DepositGold(bot)                           # Deposit Copper Z coins

    bot.States.AddHeader("Reroll: Logout > Delete > Recreate")
    bot.States.AddCustomState(LogoutAndDeleteState, "Logout/Delete/Recreate same name")
    bot.States.AddHeader("Loop: restart routine")
    bot.States.AddCustomState(ScheduleNextRun, "Schedule next run")

# ---------------------------------------------------------------------------
# Bot Routine Functions (in order of execution)
# ---------------------------------------------------------------------------
def ConfigureAggressiveEnv(bot: Botting) -> None:
    bot.Templates.Aggressive()
    bot.Items.SpawnBonusItems()
       
def PrepareForBattle(bot: Botting, Hero_List = [6], Henchman_List = [1,2]) -> None:
    ConfigureAggressiveEnv(bot)
    bot.Party.LeaveParty()
    bot.Party.AddHeroList(Hero_List)
    bot.Party.AddHenchmanList(Henchman_List)

def SkipTutorialDialog(bot: Botting) -> None:
    bot.States.AddHeader("Skip Tutorial")
    bot.Dialogs.AtXY(10289, 6405, 0x82A501)  
    bot.Map.TravelGH()
    bot.Map.LeaveGH()
    bot.Wait.ForMapToChange(target_map_id=544)

def TakeZM(bot: Botting):
    bot.States.AddHeader("Take ZM")
    def _state():
        yield from RndTravelState(796, use_districts=8)
    bot.States.AddCustomState(_state, "RndTravel -> Codex Arena")
    def _state2():
        yield from RndTravelState(248, use_districts=8)
    bot.States.AddCustomState(_state2, "RndTravel -> Great Temple of Balthazar")
    bot.Move.XYAndDialog(-5065.00, -5211.00, 0x83D201)

def TravelToChabbek(bot: Botting) -> None:
    bot.States.AddHeader("To Chahbek Village")
    def _state():
        yield from RndTravelState(544, use_districts=8)
    bot.States.AddCustomState(_state, "RndTravel -> Chahbek")
    
def Meeting_First_Spear_Jahdugar(bot: Botting):
    bot.States.AddHeader("Meeting First Spear Jahdugar")
    bot.Move.XYAndDialog(3482, -5167, 0x82A507)
    bot.Move.XYAndDialog(3482, -5167, 0x83A801)

def Equip_Weapon():
        global bot
        profession, _ = Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
        if profession == "Dervish":
            bot.Items.Equip(15591)  # starter scythe
        elif profession == "Paragon":
            bot.Items.Equip(15593) #Starter Spear
            #bot.Items.Equip(6514) #Bonus Shield
        elif profession == "Elementalist":
            #bot.Items.Equip(6508) #Luminescent Scepter
            bot.Items.Equip(2742) #Starter Elemental Rod
            #bot.Wait.ForTime(1000)
            #bot.Items.Equip(6514)
        elif profession == "Mesmer":
            #bot.Items.Equip(6508) #Luminescent Scepter
            bot.Items.Equip(2652) #Starter Cane
            #bot.Wait.ForTime(1000)
            #bot.Items.Equip(6514)
        elif profession == "Necromancer":
            #bot.Items.Equip(6515) #Soul Shrieker   
            bot.Items.Equip(2694) #Starter Truncheon
        elif profession == "Ranger":
            #bot.Items.Equip(5831) #Nevermore Flatbow 
            bot.Items.Equip(477) #Starter Bow
        elif profession == "Warrior":
            bot.Items.Equip(2982) #Starter Sword  
            #bot.Items.Equip(6514) #Bonus Shield  
        elif profession == "Monk":
            #bot.Items.Equip(6508) #Luminescent Scepter 
            bot.Items.Equip(2787) #Starter Holy Rod
            #bot.Wait.ForTime(1000)
            #bot.Items.Equip(6514)  

def ConfigureFirstBattle(bot: Botting):
    bot.States.AddHeader("Battle Setup")
    bot.Wait.ForTime(1000)
    Equip_Weapon()
    PrepareForBattle(bot, Hero_List=[6], Henchman_List=[1,2])

def EnterChahbekMission(bot: Botting):
    bot.States.AddHeader("Chahbek Village")
    bot.Dialogs.AtXY(3485, -5246, 0x81)
    bot.Dialogs.AtXY(3485, -5246, 0x84)
    bot.Wait.ForTime(2000)
    bot.Wait.UntilOnExplorable()
    bot.Move.XY(2240, -3535)
    bot.Move.XY(227, -5658)
    bot.Move.XY(-1144, -4378)
    bot.Move.XY(-2058, -3494)
    bot.Move.XY(-4725, -1830)
    bot.Interact.WithGadgetAtXY(-4725, -1830) #Oil 1
    bot.Wait.ForTime(2000)
    bot.Party.FlagAllHeroes(-1422.47, 1810.77)
    bot.Move.XY(-1725, -2551)
    bot.Wait.ForTime(1500)
    bot.Interact.WithGadgetAtXY(-1725, -2550) #Cata load
    bot.Wait.ForTime(1500)
    bot.Interact.WithGadgetAtXY(-1725, -2550) #Cata fire
    bot.Move.XY(-4725, -1830) #Back to Oil
    bot.Interact.WithGadgetAtXY(-4725, -1830) #Oil 2
    bot.Move.XY(-1731, -4138)
    bot.Interact.WithGadgetAtXY(-1731, -4138) #Cata 2 load
    bot.Wait.ForTime(2000)
    bot.Interact.WithGadgetAtXY(-1731, -4138) #Cata 2 fire
    #bot.Move.XY(-2331, -419)
    bot.Wait.ForTime(10000)
    bot.Party.UnflagAllHeroes()
    bot.Move.XY(-276.01, -1219.04)
    #bot.Move.XY(-1685, 1459)
    bot.Move.XY(-2895, -6247)
    bot.Move.XY(-3938, -6315) #Boss
    bot.Wait.ForMapToChange(target_map_id=456)

def TakeReward(bot: Botting):
    bot.States.AddHeader("Take Reward")
    def _state():
        # 7=EU, 8=EU+INT, 11=ALL (incl. Asia)
        yield from RndTravelState(248, use_districts=8)
    bot.States.AddCustomState(_state, "RndTravel -> Great Temple of Balthazar")
    bot.Move.XY(-5159.01, -5548.32)
    bot.Dialogs.WithModel(1192,0x83D207)

def UnlockXunlai(bot : Botting) :
    bot.States.AddHeader("Unlock Xunlai Storage")
    path_to_xunlai = [(-5540.40, -5733.11),(-7050.04, -6392.59),]
    bot.Move.FollowPath(path_to_xunlai) #UNLOCK_XUNLAI_STORAGE_MATERIAL_PANEL
    bot.Dialogs.WithModel(221, 0x84)
    bot.Dialogs.WithModel(221, 0x86)

def DepositReward(bot : Botting) :
    bot.States.AddHeader("Deposit Reward")
    bot.Items.AutoDepositItems() #deposit copper Z coins to bank model 31202 for config something after

def DepositGold(bot : Botting) :
    bot.States.AddHeader("Deposit Gold")
    bot.Items.AutoDepositGold() #deposit gold to bank

#region Helpers

# ---------------------------------------------------------------------------
#  REROLL (Logout -> Delete -> Create same name)
# ---------------------------------------------------------------------------

def _resolve_character_name():
    global LAST_CHARACTER_NAME

    # 1) In game
    login_number = GLOBAL_CACHE.Party.Players.GetLoginNumberByAgentID(GLOBAL_CACHE.Player.GetAgentID())
    name = GLOBAL_CACHE.Party.Players.GetPlayerNameByLoginNumber(login_number)
    if name:
        LAST_CHARACTER_NAME = name
        yield from Routines.Yield.wait(100)
        return name
    
    print (f"name (beginning) = {LAST_CHARACTER_NAME}")

    # 2) Character selection screen
    try:
        if GLOBAL_CACHE.Player.InCharacterSelectScreen():
            pregame = GLOBAL_CACHE.Player.GetPreGameContext()
            if pregame and hasattr(pregame, "chars") and hasattr(pregame, "index_1"):
                idx = int(pregame.chosen_character_index)
                if 0 <= idx < len(pregame.chars):
                    name = str(pregame.chars[idx])
                    if name:
                        LAST_CHARACTER_NAME = name
                        yield from Routines.Yield.wait(100)
                        return name
    except Exception:
        pass

    print (f"name (beginning) = {LAST_CHARACTER_NAME}")
    #add this to make it a generator
    yield from Routines.Yield.wait(100)
    # 3) Last known name
    return LAST_CHARACTER_NAME

def _has(obj, name: str) -> bool:
    try:
        return hasattr(obj, name) and callable(getattr(obj, name))
    except Exception:
        return False

def _pregame_character_list() -> list[str]:
    """Best-effort: returns the list of characters seen in selection screen."""
    try:
        pregame = GLOBAL_CACHE.Player.GetPreGameContext()
        if pregame and hasattr(pregame, "chars"):
            return [str(x) for x in list(getattr(pregame, "chars"))]
    except Exception:
        pass
    return []

def type_text_keystroke(text: str, delay_ms: int = 50):
    """
    Type text using individual keystrokes instead of clipboard.
    This avoids clipboard conflicts when running multiple instances in parallel.
    """
    yield from Routines.Yield.wait(1000)
    for char in text:
        if char in CHAR_MAP:
            key, needs_shift = CHAR_MAP[char]
            if needs_shift:
                Keystroke.Press(Key.LShift.value)
                yield from Routines.Yield.wait(50)
            Keystroke.PressAndRelease(key.value)
            yield from Routines.Yield.wait(delay_ms)
            if needs_shift:
                Keystroke.Release(Key.LShift.value)
                yield from Routines.Yield.wait(50)
        else:
            # Skip unmapped characters
            ConsoleLog("TextInput", f"Skipping unmapped character: '{char}'", Console.MessageType.Warning)

def custom_delete_character(character_name: str, timeout_ms: int = 45000):
    """
    Custom character deletion that uses keystrokes instead of clipboard.
    This prevents conflicts when running multiple instances in parallel.
    """
    from Py4GWCoreLib.routines_src.Yield import Yield

    # Click delete character button
    try:
        WindowFrames = getattr(Yield, "WindowFrames", None)
        if WindowFrames and hasattr(WindowFrames, "DeleteCharacterButton"):
            WindowFrames.DeleteCharacterButton.FrameClick()
            yield from Routines.Yield.wait(2000)

            # Type character name using keystrokes instead of clipboard
            yield from type_text_keystroke(character_name)

            yield from Routines.Yield.wait(2000)

            # Click final delete button
            if hasattr(WindowFrames, "FinalDeleteCharacterButton"):
                WindowFrames.FinalDeleteCharacterButton.FrameClick()
                yield from Routines.Yield.wait(5000)

            return True
    except Exception as e:
        ConsoleLog("CustomDelete", f"Error in custom delete: {e}", Console.MessageType.Error)
        return False

def custom_create_character(character_name: str, campaign_name: str, profession_name: str, timeout_ms: int = 60000):
    """
    Custom character creation that uses keystrokes instead of clipboard.
    This prevents conflicts when running multiple instances in parallel.
    """
    from Py4GWCoreLib.routines_src.Yield import Yield

    try:
        WindowFrames = getattr(Yield, "WindowFrames", None)
        if not WindowFrames:
            return False

        # Navigate through character creation screens
        # Select body (default)
        if hasattr(WindowFrames, "CreateCharacterNextButtonGeneric"):
            WindowFrames.CreateCharacterNextButtonGeneric.FrameClick()
            yield from Routines.Yield.wait(3000)

            # Enter name using keystrokes instead of clipboard
            yield from type_text_keystroke(character_name)
            yield from Routines.Yield.wait(2000)

            # Click final create button
            if hasattr(WindowFrames, "FinalCreateCharacterButton"):
                WindowFrames.FinalCreateCharacterButton.FrameClick()
                yield from Routines.Yield.wait(1000)

            return True
    except Exception as e:
        ConsoleLog("CustomCreate", f"Error in custom create: {e}", Console.MessageType.Error)
        return False

def LogoutAndDeleteState():
    """State final: logout -> delete -> recreate -> restart routine"""

    ConsoleLog("Reroll", "Start: Logout > Delete > Recreate", Console.MessageType.Info)

    # ------------------------------------------------------------
    # 1) Resolve character name
    # ------------------------------------------------------------
    char_name = yield from _resolve_character_name()
    if not char_name:
        ConsoleLog("Reroll", "Unable to resolve character name. Abort.", Console.MessageType.Error)
        return

    primary_prof, _ = Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
    if not primary_prof:
        primary_prof = LAST_PRIMARY_PROF or "Warrior"
    campaign_name = "Nightfall"

    RC = getattr(getattr(Routines, "Yield", None), "RerollCharacter", None)
    if not RC:
        ConsoleLog("Reroll", "RerollCharacter API not found.", Console.MessageType.Error)
        return

    ConsoleLog(
        "Reroll",
        f"Target='{char_name}' prof='{primary_prof}' camp='{campaign_name}'",
        Console.MessageType.Info
    )

    # ------------------------------------------------------------
    # 2) LOGOUT
    # ------------------------------------------------------------
    GLOBAL_CACHE.Player.LogoutToCharacterSelect()
    yield from Routines.Yield.wait(7000)

    # ------------------------------------------------------------
    # 3) Delete character (using custom keystroke-based method to avoid clipboard conflicts)
    # ------------------------------------------------------------
    success = yield from custom_delete_character(char_name)
    if not success:
        ConsoleLog("Reroll", "Custom character deletion failed, falling back to framework method", Console.MessageType.Warning)
        try:
            yield from RC.DeleteCharacter(
                character_name_to_delete=char_name,
                timeout_ms=45000,
                log=True
            )
        except TypeError:
            yield from RC.DeleteCharacter(
                character_name=char_name,
                timeout_ms=45000,
                log=True
            )

    yield from Routines.Yield.wait(7000)

    # ------------------------------------------------------------
    # 4) Decide name immediately (no long wait)
    # ------------------------------------------------------------
    try:
        names = [c.player_name for c in GLOBAL_CACHE.Player.GetLoginCharacters()]
    except Exception:
        names = []

    if char_name in names:
        final_name = _generate_fallback_name(char_name)
        ConsoleLog(
            "Reroll",
            f"Original name still locked. Using generated name '{final_name}'.",
            Console.MessageType.Warning
        )
    else:
        final_name = char_name

    # ------------------------------------------------------------
    # 5) Create character (using custom keystroke-based method to avoid clipboard conflicts)
    # ------------------------------------------------------------
    success = yield from custom_create_character(final_name, campaign_name, primary_prof)
    if not success:
        ConsoleLog("Reroll", "Custom character creation failed, falling back to framework method", Console.MessageType.Warning)
        yield from RC.CreateCharacter(
            character_name=final_name,
            campaign_name=campaign_name,
            profession_name=primary_prof,
            timeout_ms=60000,
            log=True
        )

    yield from Routines.Yield.wait(7000)

    # ------------------------------------------------------------
    # 6) Select character (si dispo)
    # ------------------------------------------------------------
    ConsoleLog("Reroll", "Reroll finished. Restarting routine.", Console.MessageType.Success)

    yield from Routines.Yield.wait(3000)

    ActionQueueManager().ResetAllQueues()
    bot.SetMainRoutine(create_bot_routine)
    return

import random

def _generate_fallback_name(current_name: str) -> str:
    """
    Generates a valid Guild Wars name without numbers.
    Cleans, removes any existing suffix and replaces it.
    NEVER stacks suffixes.
    """

    suffixes = [
        "A", "B", "C", "D", "E",
        "F", "K", "H", "I", "J",
    ]

    # ------------------------------------------------------------
    # 1) Strict cleanup: letters + spaces only
    # ------------------------------------------------------------
    cleaned = "".join(
        ch for ch in (current_name or "")
        if ch.isalpha() or ch == " "
    )
    cleaned = " ".join(cleaned.split())  # normalize spaces

    if not cleaned:
        return "Fallback A"

    parts = cleaned.split()

    # ------------------------------------------------------------
    # 2) Current suffix detection (if exists)
    # ------------------------------------------------------------
    current_suffix = None
    if parts and parts[-1] in suffixes:
        current_suffix = parts[-1]

    # ------------------------------------------------------------
    # 3) Remove ALL known suffixes at the end
    # ------------------------------------------------------------
    while parts and parts[-1] in suffixes:
        parts.pop()

    base_name = " ".join(parts).strip()
    if not base_name:
        base_name = "Fallback"

    # ------------------------------------------------------------
    # 4) Suffix choice (rotation)
    # ------------------------------------------------------------
    if current_suffix in suffixes:
        idx = suffixes.index(current_suffix)
        suffix = suffixes[(idx + 1) % len(suffixes)]
    else:
        suffix = suffixes[0]  # A

    return f"{base_name} {suffix}"

REGION_EU = 4
REGION_NA = 1
REGION_INT = 0

LANG_EN = 0
LANG_FR = 1
LANG_DE = 2
LANG_IT = 3
LANG_PL = 4
LANG_RU = 5

EU_LANGS = [LANG_EN, LANG_FR, LANG_DE, LANG_IT, LANG_PL, LANG_RU]

def pick_random_region_language(allow_international=True):
    regions = [REGION_EU, REGION_NA]
    if allow_international:
        regions.append(REGION_INT)

    region = random.choice(regions)

    # NA = English only (according to your needs)
    if region == REGION_NA:
        return region, LANG_EN

    # INT = "no default language"
    if region == REGION_INT:
        return region, 0  # or None if your API accepts it (often not)

    # EU = random among EU langs
    return region, random.choice(EU_LANGS)

def withdraw_gold(target_gold=50, deposit_all=True):
    gold_on_char = GLOBAL_CACHE.Inventory.GetGoldOnCharacter()

    if gold_on_char > target_gold and deposit_all:
        to_deposit = gold_on_char - target_gold
        GLOBAL_CACHE.Inventory.DepositGold(to_deposit)
        yield from Routines.Yield.wait(250)

    if gold_on_char < target_gold:
        to_withdraw = target_gold - gold_on_char
        GLOBAL_CACHE.Inventory.WithdrawGold(to_withdraw)
        yield from Routines.Yield.wait(250)

def TravelToRegion(map_id: int, server_region: int, district_number: int = 0, language: int = 0):
    """
    Travel to a map by its ID and region/language (direct MapInstance call).
    """
    Map.TravelToRegion(map_id, server_region, district_number, language)

def RndTravelState(map_id: int, use_districts: int = 4):
    region   = [2, 2, 2, 2] 
    language = [4, 5, 9, 10]
    if use_districts < 1:
        use_districts = 1
    if use_districts > len(region):
        use_districts = len(region)
    idx = random.randint(0, use_districts - 1)
    reg = region[idx]
    lang = language[idx]
    ConsoleLog("RndTravel", f"MoveMap(map_id={map_id}, region={reg}, district=0, language={lang})", Console.MessageType.Info)
    # Direct low-level call (equivalent to MoveMap/Map_MoveMap)
    Map.TravelToRegion(map_id, reg, 0, lang)
    # Wait for loading (equivalent to Map_WaitMapLoading)
    yield from Routines.Yield.wait(6500)
    yield from Routines.Yield.wait(1000)
selected_step = 0
filter_header_steps = True

iconwidth = 96

def _draw_texture():
    global iconwidth
    level = Agent.GetLevel(GLOBAL_CACHE.Player.GetAgentID())

    path = os.path.join(Py4GW.Console.get_projects_path(),"Bots", "Leveling", "Nightfall","Nightfall_leveler-art.png")
    size = (float(iconwidth), float(iconwidth))
    tint = (255, 255, 255, 255)
    border_col = (0, 0, 0, 0)  # <- ints, not normalized floats

    if level <= 3:
        ImGui.DrawTextureExtended(texture_path=path, size=size,
                                  uv0=(0.0, 0.0),   uv1=(0.25, 1.0),
                                  tint=tint, border_color=border_col)
    elif level <= 5:
        ImGui.DrawTextureExtended(texture_path=path, size=size,
                                  uv0=(0.25, 0.0), uv1=(0.5, 1.0),
                                  tint=tint, border_color=border_col)
    elif level <= 9:
        ImGui.DrawTextureExtended(texture_path=path, size=size,
                                  uv0=(0.5, 0.0),  uv1=(0.75, 1.0),
                                  tint=tint, border_color=border_col)
    else:
        ImGui.DrawTextureExtended(texture_path=path, size=size,
                                  uv0=(0.75, 0.0), uv1=(1.0, 1.0),
                                  tint=tint, border_color=border_col)
        
def _draw_settings(bot: Botting):
    import PyImGui
    PyImGui.text("Bot Settings")
    use_birthday_cupcake = bot.Properties.Get("birthday_cupcake", "active")
    bc_restock_qty = bot.Properties.Get("birthday_cupcake", "restock_quantity")

    use_honeycomb = bot.Properties.Get("honeycomb", "active")
    hc_restock_qty = bot.Properties.Get("honeycomb", "restock_quantity")

    use_birthday_cupcake = PyImGui.checkbox("Use Birthday Cupcake", use_birthday_cupcake)
    bc_restock_qty = PyImGui.input_int("Birthday Cupcake Restock Quantity", bc_restock_qty)

    use_honeycomb = PyImGui.checkbox("Use Honeycomb", use_honeycomb)
    hc_restock_qty = PyImGui.input_int("Honeycomb Restock Quantity", hc_restock_qty)

    # War Supplies controls
    use_war_supplies = bot.Properties.Get("war_supplies", "active")
    ws_restock_qty = bot.Properties.Get("war_supplies", "restock_quantity")

    use_war_supplies = PyImGui.checkbox("Use War Supplies", use_war_supplies)
    ws_restock_qty = PyImGui.input_int("War Supplies Restock Quantity", ws_restock_qty)

    bot.Properties.ApplyNow("war_supplies", "active", use_war_supplies)
    bot.Properties.ApplyNow("war_supplies", "restock_quantity", ws_restock_qty)
    bot.Properties.ApplyNow("birthday_cupcake", "active", use_birthday_cupcake)
    bot.Properties.ApplyNow("birthday_cupcake", "restock_quantity", bc_restock_qty)
    bot.Properties.ApplyNow("honeycomb", "active", use_honeycomb)
    bot.Properties.ApplyNow("honeycomb", "restock_quantity", hc_restock_qty)
bot.UI.override_draw_texture(_draw_texture)
bot.UI.override_draw_config(lambda: _draw_settings(bot))

# --- UI / Settings drawing ---------------------------------------------------
bot.UI.override_draw_texture(_draw_texture)
bot.UI.override_draw_config(lambda: _draw_settings(bot))

# ---------------------------------------------------------------------------
#  MAIN SCRIPT LOOP
# ---------------------------------------------------------------------------

def main():
    bot.Update()
    bot.UI.draw_window()

if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
#  LOOP CONTROLLER: schedules a new run after reroll
# ---------------------------------------------------------------------------

def ScheduleNextRun():
    """State: waits to be in game, then re-adds the entire routine (infinite loop)."""
    # If we just rerolled, we might be in character selection screen for a few seconds.
    for _ in range(200):  # ~20s max
        if not GLOBAL_CACHE.Player.InCharacterSelectScreen():
            # we're either loading or in game
            break
        yield from Routines.Yield.wait(100)

    # Small stability pause
    yield from Routines.Yield.wait(1000)

    # Re-stack all the steps again
    create_bot_routine(bot)

bot.SetMainRoutine(create_bot_routine)
