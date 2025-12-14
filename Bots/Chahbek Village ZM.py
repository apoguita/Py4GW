from __future__ import annotations
from typing import List, Tuple, Generator, Any
import os
from Py4GW import Console
import PyImGui
from Py4GWCoreLib import Key, Keystroke, Map
from AccountData import MODULE_NAME
from Py4GWCoreLib import (GLOBAL_CACHE, Inventory, Routines, Range, Py4GW, ConsoleLog, ModelID, Botting,
                          AutoPathing, ImGui, ActionQueueManager,)
LAST_CHARACTER_NAME: str = ""
LAST_PRIMARY_PROF: str = ""
LAST_CAMPAIGN: str = "Nightfall"

bot = Botting("Chahbek Village ZM",
              upkeep_birthday_cupcake_restock=10,
              upkeep_honeycomb_restock=20,
              upkeep_war_supplies_restock=2,
              upkeep_auto_inventory_management_active=False,
              upkeep_auto_combat_active=False,
              upkeep_auto_loot_active=True)
 
def create_bot_routine(bot: Botting) -> None:
    global LAST_CHARACTER_NAME, LAST_PRIMARY_PROF, LAST_CAMPAIGN
    # capture tôt tant qu'on est bien en jeu
    LAST_CHARACTER_NAME = GLOBAL_CACHE.Player.GetName() or LAST_CHARACTER_NAME
    try:
        p, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
        if p:
            LAST_PRIMARY_PROF = p
    except Exception:
        pass

    SkipTutorialDialog(bot)                    # Skip opening tutorial
    UnlockGtob(bot)
    TakeZM(bot)                                #Take ZM
    TravelToChabbek(bot)                       # Go to chabbek village
    ConfigureFirstBattle(bot)                  # Configure first battle setup
    Meeting_First_Spear_Jahdugar(bot)          # Meeting First Spear Jahdugar
    EnterChahbekMission(bot)                   # Enter Chahbek mission
    TravelToGtob(bot)                         # Travel to EB
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
    bot.Wait.ForTime(500)
    bot.Map.LeaveGH()
    bot.Wait.ForTime(5000)

def UnlockGtob(bot: Botting):
    bot.States.AddHeader("To Gtob")
    bot.Map.Travel(target_map_id=796)
    bot.Map.Travel(target_map_id=248)

def TakeZM(bot: Botting):
    bot.States.AddHeader("Take ZM")
    bot.Move.XYAndDialog(-5065.00, -5211.00, 0x83D201)

def TravelToChabbek(bot: Botting) -> None:
    bot.States.AddHeader("To Chahbek Village")
    def _state():
        # 7=EU, 8=EU+INT, 11=ALL (incl. Asia)
        yield from RndTravelState(544, use_districts=8)
    bot.States.AddCustomState(_state, "RndTravel -> Chahbek")
    
def Meeting_First_Spear_Jahdugar(bot: Botting):
    bot.States.AddHeader("Meeting First Spear Jahdugar")
    bot.Move.XYAndDialog(3482, -5167, 0x82A507)
    bot.Move.XYAndDialog(3482, -5167, 0x83A801)

def Equip_Weapon():
        global bot
        profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
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
    ConfigureAggressiveEnv(bot)
    bot.Move.XY(2240, -3535)
    bot.Move.XY(227, -5658)
    bot.Move.XY(-1144, -4378)
    bot.Move.XY(-2058, -3494)
    bot.Move.XY(-4725, -1830)
    bot.Interact.WithGadgetAtXY(-4725, -1830) #Oil 1
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
    bot.Move.XY(-2331, -419)
    bot.Move.XY(-1685, 1459)
    bot.Move.XY(-2895, -6247)
    bot.Move.XY(-3938, -6315) #Boss
    bot.Wait.ForMapToChange(target_map_id=456)

def TravelToGtob(bot: Botting) -> None:
    bot.States.AddHeader("To GTOB")

    def _state():
        # 7=EU, 8=EU+INT, 11=ALL (incl. Asia)
        yield from RndTravelState(248, use_districts=8)

    bot.States.AddCustomState(_state, "RndTravel -> Great Temple of Balthazar")

def TakeReward(bot: Botting):
    bot.States.AddHeader("Take Reward")
    bot.Move.XYAndDialog(-5019.00, -5496.00, 0x83D207)

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

    # 1) En jeu
    login_number = GLOBAL_CACHE.Party.Players.GetLoginNumberByAgentID(GLOBAL_CACHE.Player.GetAgentID())
    name = GLOBAL_CACHE.Party.Players.GetPlayerNameByLoginNumber(login_number)
    if name:
        LAST_CHARACTER_NAME = name
        yield
        return name
    
    print (f"name (beginning) = {LAST_CHARACTER_NAME}")

    # 2) Écran de sélection
    try:
        if GLOBAL_CACHE.Player.InCharacterSelectScreen():
            pregame = GLOBAL_CACHE.Player.GetPreGameContext()
            if pregame and hasattr(pregame, "chars") and hasattr(pregame, "index_1"):
                idx = int(pregame.index_1)
                if 0 <= idx < len(pregame.chars):
                    name = str(pregame.chars[idx])
                    if name:
                        LAST_CHARACTER_NAME = name
                        yield
                        return name
    except Exception:
        pass

    print (f"name (beginning) = {LAST_CHARACTER_NAME}")
    #add this to make it a generator
    yield 
    # 3) Dernier nom connu
    return LAST_CHARACTER_NAME


def _has(obj, name: str) -> bool:
    try:
        return hasattr(obj, name) and callable(getattr(obj, name))
    except Exception:
        return False

def _pregame_character_list() -> list[str]:
    """Best-effort: retourne la liste des persos vus en écran de sélection."""
    try:
        pregame = GLOBAL_CACHE.Player.GetPreGameContext()
        if pregame and hasattr(pregame, "chars"):
            return [str(x) for x in list(getattr(pregame, "chars"))]
    except Exception:
        pass
    return []

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

    primary_prof, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
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
    # 2) LOGOUT — MÉTHODE OFFICIELLE ET STABLE
    # ------------------------------------------------------------
    GLOBAL_CACHE.Player.LogoutToCharacterSelect()
    yield from Routines.Yield.wait(5000)

    # ------------------------------------------------------------
    # 3) Delete character
    # ------------------------------------------------------------
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

    yield from Routines.Yield.wait(3000)

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
    # 5) Create character
    # ------------------------------------------------------------
    yield from RC.CreateCharacter(
        character_name=final_name,
        campaign_name=campaign_name,
        profession_name=primary_prof,
        timeout_ms=60000,
        log=True
    )

    yield from Routines.Yield.wait(4000)

    # ------------------------------------------------------------
    # 6) Select character (si dispo)
    # ------------------------------------------------------------
    if hasattr(RC, "SelectCharacter"):
        try:
            yield from RC.SelectCharacter(character_name=final_name, timeout_ms=45000, log=True)
        except TypeError:
            yield from RC.SelectCharacter(character_name_to_select=final_name, timeout_ms=45000, log=True)

    # ------------------------------------------------------------
    # 7) Restart routine SAFELY
    # ------------------------------------------------------------
    ConsoleLog("Reroll", "Reroll finished. Restarting routine.", Console.MessageType.Success)

    yield from Routines.Yield.wait(1000)

    ActionQueueManager().ResetAllQueues()
    bot.SetMainRoutine(create_bot_routine)
    return

import random

def _generate_fallback_name(current_name: str) -> str:
    """
    Génère un nom Guild Wars valide sans chiffres.
    Nettoie, supprime tout suffixe existant et le remplace.
    Ne stack JAMAIS les suffixes.
    """

    suffixes = [
        "Alt", "Tmp", "New", "Bis", "Prime",
        "Echo", "Nova", "Void", "Flux", "Core",
    ]

    # ------------------------------------------------------------
    # 1) Nettoyage strict : lettres + espaces uniquement
    # ------------------------------------------------------------
    cleaned = "".join(
        ch for ch in (current_name or "")
        if ch.isalpha() or ch == " "
    )
    cleaned = " ".join(cleaned.split())  # normalise espaces

    if not cleaned:
        return "Fallback Alt"

    parts = cleaned.split()

    # ------------------------------------------------------------
    # 2) Détection du suffixe actuel (s'il existe)
    # ------------------------------------------------------------
    current_suffix = None
    if parts and parts[-1] in suffixes:
        current_suffix = parts[-1]

    # ------------------------------------------------------------
    # 3) Suppression de TOUS les suffixes connus à la fin
    # ------------------------------------------------------------
    while parts and parts[-1] in suffixes:
        parts.pop()

    base_name = " ".join(parts).strip()
    if not base_name:
        base_name = "Fallback"

    # ------------------------------------------------------------
    # 4) Choix du suffixe (rotation)
    # ------------------------------------------------------------
    if current_suffix in suffixes:
        idx = suffixes.index(current_suffix)
        suffix = suffixes[(idx + 1) % len(suffixes)]
    else:
        suffix = suffixes[0]  # Alt

    return f"{base_name} {suffix}"




# Exemple de mapping (à adapter à TES IDs réels)
REGION_EU = 4
REGION_NA = 1
REGION_INT = 0

# Exemple de langues EU (IDs à adapter à ta lib)
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

    # NA = English only (selon ton besoin)
    if region == REGION_NA:
        return region, LANG_EN

    # INT = “pas de langue par défaut”
    if region == REGION_INT:
        return region, 0  # ou None si ton API l’accepte (souvent non)

    # EU = random among EU langs
    return region, random.choice(EU_LANGS)


def withdraw_gold(target_gold=5000, deposit_all=True):
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
    Map.map_instance().Travel(map_id, server_region, district_number, language)

def RndTravelState(map_id: int, use_districts: int = 8):
    """
    Travel aléatoire style AutoIt.
    use_districts:
      7 = EU seulement
      8 = EU + International
      11 = EU + International + Asie
    """

    # Ordre: eu-en, eu-fr, eu-ge, eu-it, eu-sp, eu-po, eu-ru, int, asia-ko, asia-ch, asia-ja
    region   = [2, 2, 2, 2, 2, 2, 2, -2, 1, 3, 4]
    language = [0, 2, 3, 4, 5, 9, 10, 0, 0, 0, 0]

    if use_districts < 1:
        use_districts = 1
    if use_districts > len(region):
        use_districts = len(region)

    idx = random.randint(0, use_districts - 1)

    reg = region[idx]
    lang = language[idx]

    ConsoleLog("RndTravel", f"MoveMap(map_id={map_id}, region={reg}, district=0, language={lang})", Console.MessageType.Info)

    # Appel bas niveau direct (équivalent du MoveMap/Map_MoveMap)
    Map.map_instance().Travel(map_id, reg, 0, lang)

    # Attendre le chargement (équivalent Map_WaitMapLoading)
    yield from Routines.Yield.wait(6500)
    yield from Routines.Yield.wait(1000)

selected_step = 0
filter_header_steps = True

iconwidth = 96

def _draw_texture():
    global iconwidth
    level = GLOBAL_CACHE.Agent.GetLevel(GLOBAL_CACHE.Player.GetAgentID())

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
#  BOUCLE PRINCIPALE DU SCRIPT
# ---------------------------------------------------------------------------

def main():
    bot.Update()
    bot.UI.draw_window()


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
#  LOOP CONTROLLER: planifie un nouveau run après le reroll
# ---------------------------------------------------------------------------

def ScheduleNextRun():
    """State: attend d'être en jeu, puis re-ajoute toute la routine (boucle infinie)."""
    # Si on vient de reroll, on peut être en écran de sélection quelques secondes.
    for _ in range(200):  # ~20s max
        if not GLOBAL_CACHE.Player.InCharacterSelectScreen():
            # on est soit en chargement, soit en jeu
            break
        yield from Routines.Yield.wait(100)

    # Petite pause de stabilité
    yield from Routines.Yield.wait(1000)

    # On re-empile une nouvelle fois tous les steps
    create_bot_routine(bot)

bot.SetMainRoutine(create_bot_routine)
