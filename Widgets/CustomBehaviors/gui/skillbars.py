from Py4GWCoreLib import IconsFontAwesome5, PyImGui
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader, MatchResult
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager

shared_data = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()

@staticmethod
def render():
    
    PyImGui.text(f"All skillbars : ")
    results: list[MatchResult] | None = CustomBehaviorLoader().get_all_custom_behavior_candidates()
    if results is not None:
        for i, result in enumerate(results):
            PyImGui.text(f"{i}: {result.instance.__class__.__name__} ({result.matching_count} matches /{result.build_size} (total_build_size) => {result.matching_result} score | => {result.is_matched_with_current_build})")
