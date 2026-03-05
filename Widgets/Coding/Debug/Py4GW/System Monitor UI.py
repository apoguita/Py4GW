import importlib.util
from pathlib import Path

import Py4GW.UI as UI
import PyImGui


MODULE_NAME = "System Monitor UI"
MODULE_ICON = "Textures/Module_Icons/Monitor Diagnostic.png"

_ui = UI.UI()
_ui_detail = UI.UI()
_initialized = False

_SOURCE_PATH = Path(__file__).with_name("System Monitor.py")
_spec = importlib.util.spec_from_file_location("_system_monitor_source", _SOURCE_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Failed to load source script: {_SOURCE_PATH}")
_source = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_source)


def _runtime_header(vars_dict: dict) -> dict:
    _source._ensure_loaded()
    _source._auto_refresh_if_needed()

    # Bind config controls to the source data model.
    _source._ui_show_details = bool(vars_dict.get("ui_show_details", _source._ui_show_details))
    _source._ui_show_selected_window = bool(vars_dict.get("ui_show_selected_window", _source._ui_show_selected_window))
    _source._ui_filter_text = str(vars_dict.get("ui_filter_text", _source._ui_filter_text))
    _source._ui_max_rows = int(vars_dict.get("ui_max_rows", _source._ui_max_rows))
    _source._ui_include_draw = bool(vars_dict.get("ui_include_draw", _source._ui_include_draw))
    _source._ui_include_main = bool(vars_dict.get("ui_include_main", _source._ui_include_main))
    _source._ui_include_update = bool(vars_dict.get("ui_include_update", _source._ui_include_update))

    def _consume_button(name: str) -> bool:
        pressed = bool(vars_dict.get(name, False))
        vars_dict[name] = False
        return pressed

    if _consume_button("btn_refresh_live_metrics"):
        _source._catalog.refresh_from_live()
    if _consume_button("btn_reroll_colors"):
        _source._reroll_entry_palette()
    if _consume_button("btn_clear_stats_cache"):
        _source._catalog.clear_usage_stats()
    if _consume_button("btn_print_sample_30"):
        _source._catalog.print_sample(30)

    visible = _source._catalog.filter_text(_source._ui_filter_text)
    selected_phases = set()
    if _source._ui_include_draw:
        selected_phases.add("Draw")
    if _source._ui_include_main:
        selected_phases.add("Main")
    if _source._ui_include_update:
        selected_phases.add("Update")

    usage_rows = _source._catalog.build_usage_groups_by_display(visible, include_phases=selected_phases)
    _source._refresh_entry_color_assignments(usage_rows)
    if _consume_button("btn_log_colors"):
        _source._log_color_pool_and_assignments(usage_rows)

    counts = _source._catalog.summary_counts()
    PyImGui.text(
        f"Items={counts['items']} | Phases={counts['phases']} | Subjects={counts['subjects']} | "
        f"ScriptPaths={counts['script_paths']} | Ops={counts['operations']} | "
        f"Stats={'yes' if _source._catalog.has_usage_stats() else 'no'}"
    )
    PyImGui.text(f"Filtered rows: {len(visible)}")
    PyImGui.text(
        "Grouped by normalized entry (display_token), sorted by included usage total. "
        "Only source avg totals are shown here; percentiles remain in tooltip/details."
    )

    bar_clicked = _source._draw_top_usage_stacked_bar(usage_rows)
    if bar_clicked is not None and bar_clicked != "__others__":
        _source._ui_selected_entry = "" if _source._ui_selected_entry == bar_clicked else bar_clicked

    clicked = _source._draw_usage_groups(usage_rows)
    if clicked is not None:
        _source._ui_selected_entry = "" if _source._ui_selected_entry == clicked else clicked
    if _source._ui_selected_entry and not any(r["display"] == _source._ui_selected_entry for r in usage_rows):
        _source._ui_selected_entry = ""

    return vars_dict


def _seed_vars() -> None:
    _ui.set_var("ui_show_details", _source._ui_show_details)
    _ui.set_var("ui_show_selected_window", True)
    _ui.set_var("ui_filter_text", _source._ui_filter_text)
    _ui.set_var("ui_max_rows", _source._ui_max_rows)
    _ui.set_var("ui_include_draw", _source._ui_include_draw)
    _ui.set_var("ui_include_main", _source._ui_include_main)
    _ui.set_var("ui_include_update", _source._ui_include_update)

    _ui.set_var("btn_refresh_live_metrics", False)
    _ui.set_var("btn_reroll_colors", False)
    _ui.set_var("btn_clear_stats_cache", False)
    _ui.set_var("btn_print_sample_30", False)
    _ui.set_var("btn_log_colors", False)
    _ui_detail.set_var("ui_show_selected_window", True)


def _build_ui() -> None:
    _ui.clear_ui()
    _ui.set_next_window_size(900, 900)
    _ui.begin("Profiler Name Catalog##ui_clone_main", "", 0)

    # Config fields only (same order/intent as original main window).
    _ui.button("Refresh Live Metrics##ui_clone", "btn_refresh_live_metrics")
    _ui.same_line()
    _ui.button("Re-roll Colors##ui_clone", "btn_reroll_colors")
    _ui.same_line()
    _ui.button("Clear Stats Cache##ui_clone", "btn_clear_stats_cache")
    _ui.same_line()
    _ui.button("Print Sample (30)##ui_clone", "btn_print_sample_30")

    _ui.checkbox("Verbose tooltips##ui_clone", "ui_show_details")
    _ui.same_line()
    _ui.checkbox("Details Window##ui_clone", "ui_show_selected_window")
    _ui.input_text("Filter##ui_clone", "ui_filter_text")
    _ui.slider_int("Max Rows##ui_clone", "ui_max_rows", 5, 200)
    _ui.checkbox("Include Draw##ui_clone", "ui_include_draw")
    _ui.same_line()
    _ui.checkbox("Include Main##ui_clone", "ui_include_main")
    _ui.same_line()
    _ui.checkbox("Include Update##ui_clone", "ui_include_update")

    _ui.button("Log Colors##ui_clone", "btn_log_colors")
    _ui.python_callable(_runtime_header)
    _ui.end()


def _runtime_detail(vars_dict: dict) -> dict:
    PyImGui.text("Detail Window Shell")
    PyImGui.separator()
    PyImGui.text(f"selected_entry={_source._ui_selected_entry}")
    if not _source._ui_selected_entry:
        PyImGui.text("No selection yet. Click a row in the main usage table.")
    return vars_dict


def _build_detail_ui() -> None:
    _ui_detail.clear_ui()
    _ui_detail.set_next_window_size(900, 560)
    _ui_detail.begin("Profiler Entry Details##ui_clone_detail", "", 0)
    _ui_detail.python_callable(_runtime_detail)
    _ui_detail.end()


def update() -> None:
    global _initialized
    if not _initialized:
        _seed_vars()
        _build_ui()
        _build_detail_ui()
        _initialized = True


def draw() -> None:
    _ui.render()
    show_details = bool(_ui.vars("ui_show_selected_window"))
    has_selection = bool(_source._ui_selected_entry)
    if show_details and has_selection:
        _ui_detail.render()


def main() -> None:
    return


if __name__ == "__main__":
    main()
