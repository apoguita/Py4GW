import traceback
import math
from enum import Enum
import time
from time import sleep
import inspect
import sys
from dataclasses import dataclass, field

import Py4GW
import PyImGui
import PyMap
import PyMissionMap
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

from .enums import *
from .IconsFontAwesome5 import *
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

from .Py4GWcorelib import *
from .Overlay import *
from .DXOverlay import *
from .UIManager import *
from .Routines import *
from .SkillManager import *
from .GlobalCache import GLOBAL_CACHE
from .Pathing import AutoPathing

traceback = traceback
math = math
Enum = Enum

Py4Gw = Py4GW
PyImGui = PyImGui
PyMap = PyMap
PyMissionMap = PyMissionMap
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
PyPathing = PyPathing
PyUIManager = PyUIManager
PyCamera = PyCamera
Py2DRenderer = Py2DRenderer
GLOBAL_CACHE = GLOBAL_CACHE
AutoPathing = AutoPathing

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