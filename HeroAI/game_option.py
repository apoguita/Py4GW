import Py4GW
import traceback
from Py4GWCoreLib import GLOBAL_CACHE

from .constants import GAME_OPTION_MODULE_NAME, MAX_NUM_PLAYERS, NUMBER_OF_SKILLS
from .cache_data import CacheData

def UpdateGameOptions(cache_data:CacheData):
    """Update the player list from shared memory."""
    global GAME_OPTION_MODULE_NAME, MAX_NUM_PLAYERS, NUMBER_OF_SKILLS
    try:
        own_party_number = cache_data.data.own_party_number

        if own_party_number == 0:
            accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
            if accounts is None:
                Py4GW.Console.Log(GAME_OPTION_MODULE_NAME, "No accounts found in shared memory.", Py4GW.Console.MessageType.Warning)
                return
            
            for account in accounts:
                hero_ai_data = GLOBAL_CACHE.ShMem.GetHeroAIOptions(account.AccountEmail)
                if hero_ai_data is None:
                    continue
       
                cache_data.HeroAI_vars.all_game_option_struct[account.PartyPosition].Following = hero_ai_data.Following
                cache_data.HeroAI_vars.all_game_option_struct[account.PartyPosition].Avoidance = hero_ai_data.Avoidance
                cache_data.HeroAI_vars.all_game_option_struct[account.PartyPosition].Looting = hero_ai_data.Looting
                cache_data.HeroAI_vars.all_game_option_struct[account.PartyPosition].Targeting = hero_ai_data.Targeting
                cache_data.HeroAI_vars.all_game_option_struct[account.PartyPosition].Combat = hero_ai_data.Combat
                cache_data.HeroAI_vars.all_game_option_struct[account.PartyPosition].WindowVisible = True
                for skill_index in range(NUMBER_OF_SKILLS):
                    cache_data.HeroAI_vars.all_game_option_struct[account.PartyPosition].Skills[skill_index].Active = hero_ai_data.Skills[skill_index]

        else:
            hero_ai_data = GLOBAL_CACHE.ShMem.GetHeroAIOptions(cache_data.account_email)
            if hero_ai_data is None:
                return

            cache_data.HeroAI_vars.all_game_option_struct[own_party_number].Following = hero_ai_data.Following
            cache_data.HeroAI_vars.all_game_option_struct[own_party_number].Avoidance = hero_ai_data.Avoidance
            cache_data.HeroAI_vars.all_game_option_struct[own_party_number].Looting = hero_ai_data.Looting
            cache_data.HeroAI_vars.all_game_option_struct[own_party_number].Targeting = hero_ai_data.Targeting
            cache_data.HeroAI_vars.all_game_option_struct[own_party_number].Combat = hero_ai_data.Combat
            cache_data.HeroAI_vars.all_game_option_struct[own_party_number].WindowVisible = True
            for skill_index in range(NUMBER_OF_SKILLS):
                cache_data.HeroAI_vars.all_game_option_struct[own_party_number].Skills[
                    skill_index].Active = hero_ai_data.Skills[skill_index]

    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(GAME_OPTION_MODULE_NAME, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(GAME_OPTION_MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass
