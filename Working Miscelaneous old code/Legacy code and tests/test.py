# Necessary Imports
import Py4GW        #Miscelanious functions and classes
import ImGui_Py     #ImGui wrapper
import PyMap        #Map functions and classes
import PyAgent      #Agent functions and classes
import PyPlayer     #Player functions and classes
import PyParty      #Party functions and classes
import PyItem       #Item functions and classes
import PyInventory  #Inventory functions and classes
import PySkill      #Skill functions and classes
import PySkillbar   #Skillbar functions and classes
import PyMerchant   #Merchant functions and classes
import traceback    #traceback to log stack traces
# End Necessary Imports

#this module tests the persistence of variables in the environment
#it will increment a global variable each time it is called
module_name = "Functionality Test Module"

var = 0

def main():
    try:
        global var
        global module_name
        var += 1
        Py4GW.Console.Log(module_name, f"Cycles Evaluated: {var}",Py4GW.Console.MessageType.Notice)

    # Handle specific exceptions to provide detailed error messages
    except ImportError as e:
        Py4GW.Console.Log(module_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(module_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(module_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(module_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        # Optional: Code that will run whether an exception occurred or not
        #Py4GW.Console.Log(module_name, "Execution of Main() completed", Py4GW.Console.MessageType.Info)
        # Place any cleanup tasks here
        pass


if __name__ == "__main__":
    main()
