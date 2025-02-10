import traceback
import math
from enum import Enum
import time
import inspect
import sys
from dataclasses import dataclass, field

import Py4GW
import PyImGui
import PyMap
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

from .Py4GWcorelib import *
from .Overlay import *

traceback = traceback
math = math
Enum = Enum

Py4Gw = Py4GW
PyImGui = PyImGui
PyMap = PyMap
PyAgent = PyAgent
PyPlayer = PyPlayer
PyParty = PyParty
PyItem = PyItem
PyInventory = PyInventory
PySkill = PySkill
PySkillbar = PySkillbar
PyMerchant = PyMerchant
PyEffects = PyEffects
PyKeystroke = PyKeystroke

class Py4GWLogger:
    def write(self, message):
        if message.strip():  # Avoid logging empty lines
            Py4GW.Console.Log("Py4GW", f"Chat: {message.strip()}", Py4GW.Console.MessageType.Info)

    def flush(self):  
        pass  # Required for sys.stdout but does nothing

# Redirect Python's print output to Py4GW Console
sys.stdout = Py4GWLogger()
sys.stderr = Py4GWLogger()  # Redirect errors as well