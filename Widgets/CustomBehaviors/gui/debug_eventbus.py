import os
from collections import deque
from datetime import datetime
from Py4GWCoreLib import IconsFontAwesome5, ImGui, PyImGui

from Widgets.CustomBehaviors.primitives.bus.event_message import EventMessage
from Widgets.CustomBehaviors.primitives.bus.event_type import EventType
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
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

    # Create tabs for different views
    if PyImGui.begin_tab_bar("EventBusDebugTabs"):

        # Tab 1: Event History
        if PyImGui.begin_tab_item("Event History"):
            render_event_history()
            PyImGui.end_tab_item()

        # Tab 2: Subscribers
        if PyImGui.begin_tab_item("Subscribers"):
            render_subscribers()
            PyImGui.end_tab_item()

        PyImGui.end_tab_bar()


def render_event_history():
    """Render the event history tab."""
    PyImGui.text(f"History (newest on top) : ")
    if PyImGui.begin_child("event_history_child", size=(400, 600), border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):

        results: list[EventMessage] = []

        if CustomBehaviorLoader().custom_combat_behavior is not None:
            results = CustomBehaviorLoader().custom_combat_behavior.event_bus.get_message_history(limit=30)

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


def render_subscribers():
    """Render the subscribers tab showing all event types and their subscribers."""
    PyImGui.text("Event Type Subscribers:")

    if PyImGui.begin_child("subscribers_child", size=(600, 600), border=True, flags=PyImGui.WindowFlags.HorizontalScrollbar):

        combat_behavior = CustomBehaviorLoader().custom_combat_behavior
        if combat_behavior is None:
            PyImGui.text("No custom combat behavior loaded")
            PyImGui.end_child()
            return

        event_bus = combat_behavior.event_bus

        # Get all utilities to map subscriber names to their skill icons
        utilities_map = {}
        try:
            utilities = combat_behavior.get_skills_final_list()
            for utility in utilities:
                # Map class name to utility instance
                class_name = utility.__class__.__name__
                utilities_map[class_name] = utility
                # Also try mapping by skill name
                utilities_map[utility.custom_skill.skill_name] = utility
        except Exception as e:
            pass  # Continue without icons if utilities can't be loaded

        # Get all event types that have subscribers
        event_types: list[EventType] = event_bus.get_all_event_types()

        if not event_types:
            PyImGui.text("No event types with subscribers")
            PyImGui.end_child()
            return

        # Create a table with event types and their subscribers
        if PyImGui.begin_table("subscribers_table", 3, int(PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchProp)):
            PyImGui.table_setup_column("Event Type", PyImGui.TableColumnFlags.WidthFixed, 200)
            PyImGui.table_setup_column("Count", PyImGui.TableColumnFlags.WidthFixed, 60)
            PyImGui.table_setup_column("Subscribers", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_headers_row()

            # Sort event types by name for consistent display
            sorted_event_types = sorted(event_types, key=lambda et: et.name)

            for event_type in sorted_event_types:
                subscribers: list[str] = event_bus.get_subscribers_for_event(event_type)

                PyImGui.table_next_row()

                # Column 1: Event Type Name
                PyImGui.table_next_column()
                PyImGui.text(event_type.name)

                # Column 2: Subscriber Count
                PyImGui.table_next_column()
                PyImGui.text(str(len(subscribers)))

                # Column 3: All Subscribers with Icons in same cell
                PyImGui.table_next_column()
                if not subscribers:
                    PyImGui.text_disabled("(no subscribers)")
                else:
                    # Display all subscribers in the same cell
                    for idx, subscriber in enumerate(subscribers):
                        # Try to find matching utility and display icon
                        utility = utilities_map.get(subscriber)
                        if utility is not None:
                            texture_file = utility.custom_skill.get_texture(py4gw_root_directory, project_root)
                            ImGui.DrawTexture(texture_file, 30, 30)
                            PyImGui.same_line(0, 5)

                        PyImGui.text(subscriber)

                        # Add spacing between subscribers (except for the last one)
                        if idx < len(subscribers) - 1:
                            PyImGui.spacing()

            PyImGui.end_table()

        PyImGui.end_child()
