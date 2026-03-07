import PyImGui
from Py4GWCoreLib import GLOBAL_CACHE, Agent, Player, Party
from Py4GWCoreLib.GlobalCache.shared_memory_src.AccountStruct import AccountStruct
import Py4GW

ShMem = GLOBAL_CACHE.ShMem

original_account_name = ""
original_email = ""
original_character_name = ""

converted_account_name = ""
converted_email = ""
converted_character_name = ""

def main():
    global original_account_name, original_email, original_character_name
    global converted_account_name, converted_email, converted_character_name
    living = Agent.GetLivingAgentByID(Player.GetAgentID())
    if living is None:
        return
        
    if PyImGui.begin("acocutn data tester"):
        PyImGui.text(f"data from context:")
        
        original_account_name = Player.GetAccountName()
        original_email = Player.GetAccountEmail()
        original_character_name = Party.Players.GetPlayerNameByLoginNumber(Player.GetLoginNumber())
        PyImGui.text(f"Account Name: {original_account_name}")
        PyImGui.text(f"Account email: {original_email}")
        PyImGui.text(f"character name: {original_character_name}")
        
        PyImGui.separator()
        
        PyImGui.text(f"data from shared memory:")
        account: AccountStruct | None = ShMem.GetAccountDataFromEmail(Player.GetAccountEmail())
        if account is None:
            PyImGui.text(f"Couldnt Locate email in shared memory {Player.GetAccountEmail()}")
        else:
            converted_account_name = account.AccountName
            converted_email = account.AccountEmail
            converted_character_name = account.AgentData.CharacterName
            PyImGui.text(f"Account Name: {converted_account_name}")
            PyImGui.text(f"Account Email: {converted_email}")
            PyImGui.text(f"Character Name: {converted_character_name}")
            
        if (original_account_name == converted_account_name):
            PyImGui.text("Account Name matches")
        else:
            PyImGui.text("Account Name does not match")
            
        if (original_email == converted_email):
            PyImGui.text("Account Email matches")
        else:
            PyImGui.text("Account Email does not match")
            
        if (original_character_name == converted_character_name):
            PyImGui.text("Character Name matches")
        else:
            PyImGui.text("Character Name does not match")
        


            
        

    PyImGui.end()

if __name__ == "__main__":
    main()