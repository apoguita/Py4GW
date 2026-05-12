from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib import *

import PyImGui

model= 3093

def main():
    if PyImGui.begin("Hello World"):
        if PyImGui.button("search model"):
             _, current_weapon_name = Agent.GetWeaponType(Player.GetAgentID())
             print(f"Current weapon: {current_weapon_name}")

    
    PyImGui.end()
    


if __name__ == "__main__":
    main()
