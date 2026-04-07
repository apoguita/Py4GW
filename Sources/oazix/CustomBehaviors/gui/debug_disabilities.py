import PyImGui

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Sources.oazix.CustomBehaviors.primitives.parties.party_disability_manager import PartyDisabilityManager
from Sources.oazix.CustomBehaviors.primitives.skillbars.disabilities.disability_priority import DisabilityPriority


def get_priority_color(priority: DisabilityPriority) -> Color:
    """Get color based on disability priority level"""
    if priority == DisabilityPriority.VERY_HIGH:
        return Color(255, 80, 80, 255)  # Bright red
    elif priority == DisabilityPriority.HIGH:
        return Color(255, 165, 0, 255)  # Orange
    elif priority == DisabilityPriority.NORMAL:
        return Color(100, 180, 255, 255)  # Light blue
    else:
        return Color(150, 150, 150, 255)  # Gray fallback


def create_colored_button(label: str, color: Color, width=0, height=0):
    """Create a colored button with hover and active states and black text"""
    # Create slightly darker colors for hover and active states
    hovered_color = Color(
        max(0, color.r - 30),
        max(0, color.g - 30),
        max(0, color.b - 30),
        color.a
    )
    active_color = Color(
        max(0, color.r - 50),
        max(0, color.g - 50),
        max(0, color.b - 50),
        color.a
    )

    # Black text color
    black_color = Color(0, 0, 0, 255)

    # Push button colors and text color
    PyImGui.push_style_color(PyImGui.ImGuiCol.Button, color.to_tuple_normalized())
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, hovered_color.to_tuple_normalized())
    PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, active_color.to_tuple_normalized())
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, black_color.to_tuple_normalized())

    # Create button
    clicked = PyImGui.button(label, width, height)

    # Pop colors (4 colors: button, hovered, active, text)
    PyImGui.pop_style_color(4)

    return clicked


@staticmethod
def render():

    # Get disability priorities manager and debug data
    disability_prio = PartyDisabilityManager()
    static_data_by_skillbar_name, live_data_by_agent_id = disability_prio.get_debug_data()

    # Aggregate all hex priorities from all party members
    all_hex_priorities = []
    for skillbar_name, static_data in static_data_by_skillbar_name.items():
        for hex_prio in static_data.hex_priorities:
            all_hex_priorities.append((static_data.account_email, skillbar_name, hex_prio))

    # Aggregate all condition priorities from all party members
    all_condition_priorities = []
    for skillbar_name, static_data in static_data_by_skillbar_name.items():
        for cond_prio in static_data.condition_priorities:
            all_condition_priorities.append((static_data.account_email, skillbar_name, cond_prio))

    # Render Hexes section
    PyImGui.text("Hex Priorities:")
    PyImGui.spacing()

    # Sort by priority value (highest first)
    all_hex_priorities.sort(key=lambda x: x[2].priority.value, reverse=True)

    if not all_hex_priorities:
        PyImGui.text("  No hex priorities configured")
    else:
        for idx, (email, skillbar_name, hex_prio) in enumerate(all_hex_priorities):
            skill_name = hex_prio.hex.skill_name
            priority_name = hex_prio.priority.name
            priority_value = hex_prio.priority.value
            priority_color = get_priority_color(hex_prio.priority)
            skill_id = hex_prio.hex_skill_id

            # Gray color for skill name button
            gray_color = Color(120, 120, 120, 255)

            # Skill name button in gray
            skill_button_label = f"{skill_name } | ({skillbar_name})##hex_skill_{idx}"
            create_colored_button(skill_button_label, gray_color, 0, 22)

            # Tooltip for skill
            if PyImGui.is_item_hovered():
                PyImGui.begin_tooltip()
                PyImGui.text(f"Hex: {skill_name}")
                PyImGui.text(f"Skillbar: {skillbar_name}")
                PyImGui.text(f"Account: {email}")
                PyImGui.end_tooltip()

            # Priority button in color, right next to skill button
            PyImGui.same_line(0, 3)
            priority_button_label = f"{priority_name} | ({priority_value})##hex_prio_{idx}"
            create_colored_button(priority_button_label, priority_color, 0, 22)

            # Tooltip for priority
            if PyImGui.is_item_hovered():
                PyImGui.begin_tooltip()
                PyImGui.text(f"Priority: {priority_name}")
                PyImGui.text(f"Value: {priority_value}")
                PyImGui.end_tooltip()

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Render Conditions section
    PyImGui.text("Condition Priorities:")
    PyImGui.spacing()

    # Sort by priority value (highest first)
    all_condition_priorities.sort(key=lambda x: x[2].priority.value, reverse=True)

    if not all_condition_priorities:
        PyImGui.text("  No condition priorities configured")
    else:
        for idx, (email, skillbar_name, cond_prio) in enumerate(all_condition_priorities):
            skill_name = cond_prio.condition.skill_name
            priority_name = cond_prio.priority.name
            priority_value = cond_prio.priority.value
            priority_color = get_priority_color(cond_prio.priority)

            # Gray color for skill name button
            gray_color = Color(120, 120, 120, 255)

            # Skill name button in gray
            skill_button_label = f"{skill_name} | ({skillbar_name})##cond_skill_{idx}"
            create_colored_button(skill_button_label, gray_color, 0, 22)

            # Tooltip for skill
            if PyImGui.is_item_hovered():
                PyImGui.begin_tooltip()
                PyImGui.text(f"Condition: {skill_name}")
                PyImGui.text(f"Skillbar: {skillbar_name}")
                PyImGui.text(f"Account: {email}")
                PyImGui.end_tooltip()

            # Priority button in color, right next to skill button
            PyImGui.same_line(0, 3)
            priority_button_label = f"{priority_name} ({priority_value})##cond_prio_{idx}"
            create_colored_button(priority_button_label, priority_color, 0, 22)

            # Tooltip for priority
            if PyImGui.is_item_hovered():
                PyImGui.begin_tooltip()
                PyImGui.text(f"Priority: {priority_name}")
                PyImGui.text(f"Value: {priority_value}")
                PyImGui.end_tooltip()

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Live data section
    PyImGui.text("Live Data:")
    PyImGui.spacing()

    if not live_data_by_agent_id:
        PyImGui.text("  No live data available")
    else:
        # Begin table with 6 columns
        if PyImGui.begin_table("live_data_table", 7, PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg):
            # Setup columns
            PyImGui.table_setup_column("Agent ID", PyImGui.TableColumnFlags.WidthFixed, 80)
            PyImGui.table_setup_column("Account", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column("Skillbar", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column("Hexes", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column("Hex Score", PyImGui.TableColumnFlags.WidthFixed, 100)
            PyImGui.table_setup_column("Conditions", PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_setup_column("Condition Score", PyImGui.TableColumnFlags.WidthFixed, 120)
            PyImGui.table_headers_row()

            # Populate rows
            for agent_id, live_data in live_data_by_agent_id.items():
                PyImGui.table_next_row()

                # Agent ID column
                PyImGui.table_set_column_index(0)
                PyImGui.text(str(agent_id))

                # Account column
                PyImGui.table_set_column_index(1)
                account = GLOBAL_CACHE.ShMem.GetAccountDataFromEmail(live_data.account_email)
                character_name = account.AgentData.CharacterName if account.AgentData.CharacterName else "Unknown"
                PyImGui.text(f"{character_name}")
                PyImGui.same_line(0, 5)
                PyImGui.text(live_data.account_email) 
                PyImGui.table_set_column_index(2)
                PyImGui.text(live_data.skillbar_name)

                # Hexes column
                PyImGui.table_set_column_index(3)
                if live_data.hex_priorities:
                    hex_names = ", ".join([f"{hp.hex.skill_name} ({hp.priority.name})" for hp in live_data.hex_priorities])
                    PyImGui.text(hex_names)
                else:
                    PyImGui.text("-")

                # Hex Score column
                PyImGui.table_set_column_index(4)
                hex_score_color = Color(255, 80, 80, 255) if live_data.hex_score > 0 else Color(150, 150, 150, 255)
                PyImGui.text_colored(str(live_data.hex_score), hex_score_color.to_tuple_normalized())

                # Conditions column
                PyImGui.table_set_column_index(5)
                if live_data.condition_priorities:
                    cond_names = ", ".join([f"{cp.condition.skill_name} ({cp.priority.name})" for cp in live_data.condition_priorities])
                    PyImGui.text(cond_names)
                else:
                    PyImGui.text("-")

                # Condition Score column
                PyImGui.table_set_column_index(6)
                cond_score_color = Color(255, 165, 0, 255) if live_data.condition_score > 0 else Color(150, 150, 150, 255)
                PyImGui.text_colored(str(live_data.condition_score), cond_score_color.to_tuple_normalized())

            PyImGui.end_table()

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()