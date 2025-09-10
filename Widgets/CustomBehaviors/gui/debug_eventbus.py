import os
from collections import deque
from datetime import datetime
from Py4GWCoreLib import IconsFontAwesome5, ImGui, PyImGui
from Widgets.CustomBehaviors.primitives.bus.event_bus import EVENT_BUS
from Widgets.CustomBehaviors.primitives.bus.event_message import EventMessage
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
from Widgets.CustomBehaviors.primitives.parties.shared_lock_manager import SharedLockHistory, SharedLockManager
from Widgets.CustomBehaviors.primitives.skills.utility_skill_execution_history import UtilitySkillExecutionHistory

shared_data = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_directory, os.pardir))
py4gw_root_directory = project_root + f"\\..\\..\\"

@staticmethod
def render():
    
    PyImGui.text(f"History (newest on top) : ")
    if PyImGui.begin_child("x", size=(400, 600),border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):

        results:list[EventMessage] = EVENT_BUS.get_message_history(limit=30)

        # simple table with skill picture and name
        if PyImGui.begin_table("history_eventbus", 2, int(PyImGui.TableFlags.SizingStretchProp)):
            PyImGui.table_setup_column("Icon")
            PyImGui.table_setup_column("Name")
            for result in reversed(results):
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                texture_file = project_root + f"\\gui\\textures\\event.png"
                ImGui.DrawTexture(texture_file, 30, 30)
                PyImGui.table_next_column()
                time_emitted_at = datetime.fromtimestamp(result.timestamp or 0)
                time_emitted_at_formatted = f"{time_emitted_at:%H:%M:%S}:{int(time_emitted_at.microsecond/1000):03d}"
                PyImGui.text(f"started_at: {time_emitted_at_formatted}")
                PyImGui.text(f"type: {result.type}")
                PyImGui.separator()
            PyImGui.end_table()
           


        PyImGui.end_child()
