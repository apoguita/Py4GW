import os
from collections import deque
from datetime import datetime
from Py4GWCoreLib import IconsFontAwesome5, ImGui, PyImGui
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
from Widgets.CustomBehaviors.primitives.parties.shared_lock_manager import SharedLockManager
from Widgets.CustomBehaviors.primitives.skills.utility_skill_execution_history import UtilitySkillExecutionHistory

shared_data = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_directory, os.pardir))
py4gw_root_directory = project_root + f"\\..\\..\\"

@staticmethod
def render():
    
    PyImGui.text(f"Current user : {GLOBAL_CACHE.Player.GetAccountEmail()} | {GLOBAL_CACHE.Player.GetName()}")
    PyImGui.text(f"History (newest on top) : ")
    if PyImGui.begin_child("x", size=(400, 600),border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):

        shared_lock_manager:SharedLockManager = CustomBehaviorParty().get_shared_lock_manager()
        if shared_lock_manager is None: return
        results:deque[SharedLockHistory] = shared_lock_manager.get_lock_history()

        # simple table with skill picture and name
        if PyImGui.begin_table("history_sharedlocks", 2, int(PyImGui.TableFlags.SizingStretchProp)):
            PyImGui.table_setup_column("Icon")
            PyImGui.table_setup_column("Name")
            for result in results:

                PyImGui.table_next_row()
                PyImGui.table_next_column()
                texture_file = project_root + f"\\gui\\textures\\lock_released.png"
                
                if result.released_at is None:
                    texture_file = project_root + f"\\gui\\textures\\lock_taken.png"

                ImGui.DrawTexture(texture_file, 30, 30)
                PyImGui.table_next_column()

                PyImGui.text(f"{result.key} | ")
                PyImGui.same_line(0.0, 0.0)
                time_started_at = datetime.fromtimestamp(result.acquired_at or 0)
                time_started_at_formatted = f"{time_started_at:%H:%M:%S}:{int(time_started_at.microsecond/1000):03d}"
                PyImGui.text(f"started_at: {time_started_at_formatted}")

                if result.released_at is not None:
                    time_released_at = datetime.fromtimestamp(result.released_at or 0)
                    time_released_at_formatted = f"{time_released_at:%H:%M:%S}:{int(time_released_at.microsecond/1000):03d}"
                    PyImGui.same_line(0.0, 0.0)
                    PyImGui.text(f"| released_at: {time_released_at_formatted}")
                
                PyImGui.text(f"sender_email: {result.sender_email}")
                PyImGui.separator()
            PyImGui.end_table()
           


        PyImGui.end_child()
