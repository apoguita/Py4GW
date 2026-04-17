from Py4GWCoreLib import IconsFontAwesome5, PyImGui, Color
from Sources.oazix.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader, MatchResult
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager

@staticmethod
def render():

    shared_data = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()

    # Header with styling
    PyImGui.text_colored("All Skillbars:", Color(100, 200, 255, 255).to_tuple_normalized())
    PyImGui.separator()

    results: list[MatchResult] | None = CustomBehaviorLoader().get_all_custom_behavior_candidates()
    if results is not None and len(results) > 0:
        PyImGui.text(f"Found {len(results)} skillbar(s)")
        PyImGui.separator()
        for i, result in enumerate(results):
            # Determine colors based on match status
            is_matched = result.is_matched_with_current_build

            # Background color for the row
            if is_matched:
                bg_color = Color(30, 80, 40, 180)  # Green tint for matched
                text_color = Color(120, 255, 120, 255)  # Bright green
                icon = IconsFontAwesome5.ICON_CHECK_CIRCLE
            else:
                bg_color = Color(60, 60, 70, 120)  # Neutral gray for unmatched
                text_color = Color(180, 180, 190, 255)  # Muted white
                icon = IconsFontAwesome5.ICON_CIRCLE

            # Format the label with icon
            class_name = result.instance.__class__.__name__
            label = f"{icon} [{i}] {class_name}##skillbar_{i}"

            # Draw background colored button (as a visual indicator)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, bg_color.to_tuple_normalized())
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, bg_color.shift(Color(255, 255, 255), 0.15).to_tuple_normalized())
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, bg_color.shift(Color(255, 255, 255), 0.25).to_tuple_normalized())
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, text_color.to_tuple_normalized())

            PyImGui.button(label, width=0, height=0)

            PyImGui.pop_style_color(4)

            # Details on same line
            PyImGui.same_line(0, 5)

            # Required skills match ratio
            required_ratio = f"{result.matching_count}/{result.build_size}"
            required_color = Color(100, 255, 100, 255) if result.matching_count == result.build_size else Color(255, 150, 80, 255)
            PyImGui.text_colored("Req: ", Color(150, 150, 150, 255).to_tuple_normalized())
            PyImGui.same_line(0, 5)
            PyImGui.text_colored(required_ratio, required_color.to_tuple_normalized())

            # Custom skills match ratio
            PyImGui.same_line(0, 5)
            PyImGui.text_colored(" | Custom: ", Color(150, 150, 150, 255).to_tuple_normalized())
            PyImGui.same_line(0, 5)
            custom_ratio = f"{result.custom_skills_matching_count}/{result.custom_skills_count}"
            custom_color = Color(120, 200, 255, 255) if result.custom_skills_matching_count > 0 else Color(100, 100, 100, 255)
            PyImGui.text_colored(custom_ratio, custom_color.to_tuple_normalized())
