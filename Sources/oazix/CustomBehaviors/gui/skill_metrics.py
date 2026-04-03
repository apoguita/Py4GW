from collections import deque
import os

from Py4GWCoreLib import PyImGui, GLOBAL_CACHE
from Py4GWCoreLib.ImGui import ImGui
from Sources.oazix.CustomBehaviors.PathLocator import PathLocator
from Sources.oazix.CustomBehaviors.primitives.helpers.utility_skill_metrics import (
    UtilitySkillMetrics,
    UtilitySkillMetricsSample,
)


_WINDOW_PRESETS = [10, 30, 60, 120, 300, 600]


def _compute_skill_metrics(history: deque[UtilitySkillMetricsSample]):
    """Compute aggregated metrics per skill from history.

    Returns:
        List of tuples: (skill_name, skill_id, action_skipped_count, action_performed_count, success_rate)
    """
    skill_data: dict[int, dict[str, int]] = {}  # skill_id -> metrics

    for sample in history:
        skill_id = sample.skill_id
        if skill_id not in skill_data:
            skill_data[skill_id] = {"skipped": 0, "performed": 0}

        if sample.action_type == "skipped":
            skill_data[skill_id]["skipped"] += 1
        elif sample.action_type == "performed":
            skill_data[skill_id]["performed"] += 1

    # Build result rows with success rate
    rows = []
    for skill_id, data in skill_data.items():
        skill_name = GLOBAL_CACHE.Skill.GetName(skill_id)
        skipped = data["skipped"]
        performed = data["performed"]
        total_executions = skipped + performed
        success_rate = (performed / total_executions * 100) if total_executions > 0 else 0.0
        rows.append((skill_name, skill_id, skipped, performed, success_rate))

    # Sort by total executions (most used first)
    rows.sort(key=lambda r: r[2] + r[3], reverse=True)
    return rows

def _get_skill_texture(skill_id: int) -> str:
    """Get skill texture path with fallback."""
    if skill_id > 0:
        texture_path = PathLocator.get_project_root_directory() + "\\" + GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(skill_id)
        if os.path.exists(texture_path):
            return texture_path
    return PathLocator.get_texture_fallback()

def render():
    TABLE_FLAGS = int(PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchProp)
    SORTABLE_TABLE_FLAGS = int(PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.SizingStretchProp | PyImGui.TableFlags.Sortable)

    metrics = UtilitySkillMetrics()
    metrics.enabled = PyImGui.checkbox("Enable utility skill metrics##metrics_enabled", metrics.enabled)

    PyImGui.same_line(0, -1)
    if PyImGui.button("Clear##metrics_clear"):
        metrics.clear()

    # Reset when entering combat checkbox
    metrics.should_reset_when_entering_combat = PyImGui.checkbox(
        "Reset when entering combat",
        metrics.should_reset_when_entering_combat
    )
    if PyImGui.is_item_hovered():
        PyImGui.set_tooltip("Automatically clear metrics when transitioning from FAR_FROM_AGGRO to IN_AGGRO or CLOSE_TO_AGGRO")

    history = metrics.history
    n = len(history)

    PyImGui.text(f"Total history entries: {n}")
    PyImGui.same_line(0, -1)

    if n == 0:
        PyImGui.text("No data collected yet.")
        return

    PyImGui.separator()

    # Compute aggregated metrics
    skill_rows = _compute_skill_metrics(history)

    # Display summary table with icon column
    if PyImGui.begin_table("##utility_skill_metrics_table", 4, SORTABLE_TABLE_FLAGS):
        PyImGui.table_setup_column("Icon", PyImGui.TableColumnFlags.WidthFixed, 20)
        PyImGui.table_setup_column("Skill Name", PyImGui.TableColumnFlags.WidthStretch | PyImGui.TableColumnFlags.DefaultSort)
        PyImGui.table_setup_column("Skipped", PyImGui.TableColumnFlags.WidthFixed, 60)
        PyImGui.table_setup_column("Performed", PyImGui.TableColumnFlags.WidthFixed, 70)
        PyImGui.table_headers_row()

        # Handle sorting
        sort_specs = PyImGui.table_get_sort_specs()
        if sort_specs is not None and sort_specs.Specs is not None:
            col_idx = sort_specs.Specs.ColumnIndex
            reverse = sort_specs.Specs.SortDirection == PyImGui.SortDirection.Descending

            if col_idx == 1:  # Skill Name
                skill_rows.sort(key=lambda r: r[0], reverse=reverse)
            elif col_idx == 2:  # Skipped
                skill_rows.sort(key=lambda r: r[2], reverse=reverse)
            elif col_idx == 3:  # Performed
                skill_rows.sort(key=lambda r: r[3], reverse=reverse)
            elif col_idx == 4:  # Success %
                skill_rows.sort(key=lambda r: r[4], reverse=reverse)

        for skill_name, skill_id, skipped, performed, success_rate in skill_rows:
            PyImGui.table_next_row()

            # Icon column
            PyImGui.table_next_column()
            texture_path = _get_skill_texture(skill_id)
            ImGui.DrawTexture(texture_path, 32, 32)

            # Skill name column
            PyImGui.table_next_column()
            PyImGui.text(skill_name)

            # Skipped column
            PyImGui.table_next_column()
            PyImGui.text(str(skipped))

            # Performed column
            PyImGui.table_next_column()
            PyImGui.text(str(performed))

        PyImGui.end_table()


debug_utility_skill_metrics = render

