import traceback
import math
from enum import Enum
import time
from time import sleep
import inspect
import sys
from dataclasses import dataclass, field
import os
import subprocess

#*******************************************************************************
#********* Start of manual import of external libraries  ***********************
#*******************************************************************************
def find_system_python():
    try:
        python_path = subprocess.check_output("where python", shell=True).decode().split("\n")[0].strip()
        if python_path and os.path.exists(python_path):
            return os.path.dirname(python_path)
    except Exception:
        pass
    return sys.prefix if sys.prefix and os.path.exists(sys.prefix) else None

system_python_path = find_system_python()
if system_python_path:
    site_packages_path = os.path.join(system_python_path, "Lib", "site-packages")
    if site_packages_path not in sys.path:
        sys.path.append(site_packages_path)
    os.environ["PATH"] = site_packages_path + os.pathsep + os.environ["PATH"]


#*******************************************************************************
#********* End of manual import of external libraries  ***********************
#*******************************************************************************


import Py4GW
import PyScanner
import PyImGui

import PyAgent
import PyPlayer
import PyParty
import PyItem
import PyInventory
import PySkill
import PySkillbar
import PyMerchant
import PyEffects
import PyKeystroke
import PyOverlay
import PyQuest
import PyPathing
import PyUIManager
import PyCamera
import Py2DRenderer
import PyCombatEvents

from .enums import *
from .ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
from .Map import *
from .ImGui import *
from .model_data import *
from .Agent import *
from .Player import *
from .AgentArray import *
from .Party import *
from .Item import *
from .ItemArray import *
from .Inventory import *
from .Skill import *
from .Skillbar import *
from .Effect import *
from .Merchant import *
from .Quest import *
from .Camera import *
from .Scanner import *

from .Py4GWcorelib import *
from .Overlay import *
from .DXOverlay import *
from .UIManager import *
from .Routines import *
from .SkillManager import *
from .GlobalCache import GLOBAL_CACHE
from .Pathing import AutoPathing
from .BuildMgr import BuildMgr
from .Botting import BottingClass as Botting
from .Context import GWContext
from .CombatEvents import CombatEvents
from .IniManager import IniManager

from .py4gwcorelib_src.Profiling import ProfilingRegistry, SimpleProfiler
from .py4gwcorelib_src.WidgetManager import WidgetHandler, Widget

traceback = traceback
math = math
Enum = Enum
time = time
sleep = sleep
inspect = inspect
dataclass = dataclass
field = field

Py4Gw = Py4GW
Py4GW = Py4GW
PyScanner = PyScanner
PyImGui = PyImGui

PyAgent = PyAgent
PyPlayer = PyPlayer
PyParty = PyParty
PyItem = PyItem
PyInventory = PyInventory
PySkill = PySkill
PySkillbar = PySkillbar
PyMerchant = PyMerchant
PyEffects = PyEffects
PyPathing = PyPathing
PyOverlay = PyOverlay
PyQuest = PyQuest
PyUIManager = PyUIManager
PyCamera = PyCamera
Py2DRenderer = Py2DRenderer
PyCombatEvents = PyCombatEvents
GLOBAL_CACHE = GLOBAL_CACHE
AutoPathing = AutoPathing
IconsFontAwesome5 = IconsFontAwesome5
IniManager = IniManager
ProfilingRegistry = ProfilingRegistry
SimpleProfiler = SimpleProfiler
WidgetHandler = WidgetHandler
Widget = Widget



#redirect print output to Py4GW Console
class Py4GWLogger:
    def write(self, message):
        if message.strip():  # Avoid logging empty lines
            Py4GW.Console.Log("print:", f"{message.strip()}", Py4GW.Console.MessageType.Info)

    def flush(self):  
        pass  # Required for sys.stdout but does nothing
    
class Py4GWLoggerError:
    def write(self, message):
        if message.strip():  # Avoid logging empty lines
            Py4GW.Console.Log("print:", f"{message.strip()}", Py4GW.Console.MessageType.Error)

    def flush(self):  
        pass  # Required for sys.stdout but does nothing

# Redirect Python's print output to Py4GW Console
sys.stdout = Py4GWLogger()
sys.stderr = Py4GWLoggerError()