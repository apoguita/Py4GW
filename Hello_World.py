from Py4GWCoreLib.BottingTree import BottingTree
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.py4gwcorelib_src.BehaviorTree import BehaviorTree
from Py4GWCoreLib import *

import PyImGui


def main():
    if PyImGui.begin("Hello World"):
        PyImGui.text("Hello, World!")
        
        if Inventory.IsStorageOpen():
            PyImGui.text("Storage is open.")
        else:
            PyImGui.text("Storage is closed.")
            
        if PyImGui.button("Open Storage"):
            Inventory.OpenXunlaiWindow()
    
    PyImGui.end()
    


if __name__ == "__main__":
    main()
