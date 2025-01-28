from Py4GWCoreLib import *

from .constants import (
    GAME_OPTION_MODULE_NAME,
    MAX_NUM_PLAYERS,
    NUMBER_OF_SKILLS
)

from .types import (
    PlayerStruct,
    CandidateStruct,
    MemSkill,
    GameOptionStruct,
    GameStruct,
)
from .globals import HeroAI_vars, HeroAI_windows, Debug_window_vars

def UpdateGameOptions():
    """Update the player list from shared memory."""
    global HeroAI_vars
    try:
        own_party_number = Party.GetOwnPartyNumber()

        if own_party_number == 0:
            for index in range(MAX_NUM_PLAYERS):
                game_option = HeroAI_vars.shared_memory_handler.get_game_option(index)
       
                HeroAI_vars.all_game_option_struct[index].Following = game_option["Following"]
                HeroAI_vars.all_game_option_struct[index].Avoidance = game_option["Avoidance"]
                HeroAI_vars.all_game_option_struct[index].Looting = game_option["Looting"]
                HeroAI_vars.all_game_option_struct[index].Targetting = game_option["Targetting"]
                HeroAI_vars.all_game_option_struct[index].Combat = game_option["Combat"]
                HeroAI_vars.all_game_option_struct[index].WindowVisible = game_option["WindowVisible"]

                for skill_index in range(NUMBER_OF_SKILLS):
                    HeroAI_vars.all_game_option_struct[index].Skills[skill_index].Active = game_option["Skills"][skill_index]
        else:
            game_option = HeroAI_vars.shared_memory_handler.get_game_option(own_party_number)

            HeroAI_vars.all_game_option_struct[own_party_number].Following = game_option["Following"]
            HeroAI_vars.all_game_option_struct[own_party_number].Avoidance = game_option["Avoidance"]
            HeroAI_vars.all_game_option_struct[own_party_number].Looting = game_option["Looting"]
            HeroAI_vars.all_game_option_struct[own_party_number].Targetting = game_option["Targetting"]
            HeroAI_vars.all_game_option_struct[own_party_number].Combat = game_option["Combat"]
            HeroAI_vars.all_game_option_struct[own_party_number].WindowVisible = game_option["WindowVisible"]
            for skill_index in range(NUMBER_OF_SKILLS):
                HeroAI_vars.all_game_option_struct[own_party_number].Skills[
                    skill_index].Active = game_option["Skills"][skill_index]

    except ImportError as e:
        Py4GW.Console.Log(GAME_OPTION_MODULE_NAME, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(GAME_OPTION_MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(GAME_OPTION_MODULE_NAME, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(GAME_OPTION_MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(GAME_OPTION_MODULE_NAME, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(GAME_OPTION_MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(GAME_OPTION_MODULE_NAME, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(GAME_OPTION_MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass
