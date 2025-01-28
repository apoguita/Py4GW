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

var = 0

#this is the absolute minimum you can do to make a script run.
def main():
    global var
    var += 1
    Py4GW.Console.Log("Barebones Module", f"Cycles Evaluated: {var}",Py4GW.Console.MessageType.Notice)

if __name__ == "__main__":
    main()
