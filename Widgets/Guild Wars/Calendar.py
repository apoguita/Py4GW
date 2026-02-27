from __future__ import annotations
from typing import List, Tuple, Optional
from datetime import date, timedelta
import ast
import os


import PyImGui
from Py4GWCoreLib import *
from Py4GWCoreLib.enums import YEARS, MONTHS, EVENTS, PVE_WEEKLY_BONUSES, PVP_WEEKLY_BONUSES, NICHOLAS_CYCLE
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import Widget, WidgetHandler, get_widget_handler


REFERENCE_WEEK = date(2013, 5, 13)  # First Monday after update
ROTATION_START = REFERENCE_WEEK  # baseline for modulo rotation
MODULE_NAME = "Calendar"

def get_weekly_bonuses(day: date) -> tuple[dict, dict]:
    """Return (PvE_bonus, PvP_bonus) active for the given date."""
    # Normalize to Monday of this week
    monday = day - timedelta(days=day.weekday())  # Monday start
    if monday < ROTATION_START:
        return PVE_WEEKLY_BONUSES[0], PVP_WEEKLY_BONUSES[0]

    weeks = (monday - ROTATION_START).days // 7

    pve_index = weeks % len(PVE_WEEKLY_BONUSES)
    pvp_index = weeks % len(PVP_WEEKLY_BONUSES)

    return PVE_WEEKLY_BONUSES[pve_index], PVP_WEEKLY_BONUSES[pvp_index]


from datetime import date, timedelta

def expand_cycle_if_needed(day: date) -> None:
    """Expand NICHOLAS_CYCLE in place if 'day' is outside its current range."""
    global NICHOLAS_CYCLE

    if not NICHOLAS_CYCLE:
        return

    num_weeks = len(NICHOLAS_CYCLE)
    shift_days = num_weeks * 7

    first_week = NICHOLAS_CYCLE[0]["week"]
    last_week = NICHOLAS_CYCLE[-1]["week"]

    # If the date is before the first known week → prepend one cycle
    while day < first_week:
        shifted = []
        for entry in NICHOLAS_CYCLE:
            new_entry = entry.copy()
            new_entry["week"] = entry["week"] - timedelta(days=shift_days)
            shifted.append(new_entry)
        NICHOLAS_CYCLE = shifted + NICHOLAS_CYCLE
        first_week = NICHOLAS_CYCLE[0]["week"]

    # If the date is after the last known week → append one cycle
    while day > last_week:
        shifted = []
        for entry in NICHOLAS_CYCLE:
            new_entry = entry.copy()
            new_entry["week"] = entry["week"] + timedelta(days=shift_days)
            shifted.append(new_entry)
        NICHOLAS_CYCLE = NICHOLAS_CYCLE + shifted
        last_week = NICHOLAS_CYCLE[-1]["week"]


def get_nicholas_for_day(day: date) -> dict | None:
    """Return Nicholas dict for any given date, expanding cycle on demand."""
    if not NICHOLAS_CYCLE:
        return None

    # Normalize to Monday
    monday = day - timedelta(days=day.weekday())

    # Ensure dataset covers the requested Monday
    expand_cycle_if_needed(monday)

    # Now find the exact Monday in the dataset
    for entry in NICHOLAS_CYCLE:
        if entry["week"] == monday:
            return entry

    return None






def get_event_for_day(day: date) -> dict | None:
    """Return event dict if 'day' falls within an event's range."""
    for name, info in EVENTS.items():
        start_month, start_day = info["start_date"]
        start = date(day.year, start_month, start_day)
        end = start + timedelta(days=info["duration_days"])
        if start <= day < end:
            return {"name": name, **info}
    return None



class Calendar:
    def __init__(self, current: date | None = None):
        # Default to today if nothing passed
        self.current = current or date.today()

    # -------------------------
    # Basics
    # -------------------------
    def get_current_date(self) -> Tuple[int, int, int]:
        return self.current.year, self.current.month, self.current.day

    def to_string(self) -> str:
        return self.current.strftime("%B %d, %Y")

    def get_year(self) -> str:
        return str(self.current.year)

    def get_month(self) -> str:
        return str(self.current.month)

    def get_month_name(self) -> str:
        return MONTHS[self.current.month - 1][0]

    def get_month_short_name(self) -> str:
        return MONTHS[self.current.month - 1][1]

    def get_month_year(self) -> str:
        return f"{self.get_month_name()} - {self.current.year}"

    def get_short_month_year(self) -> str:
        return f"{self.get_month_short_name()} - {self.current.year}"

    def get_day(self) -> str:
        return str(self.current.day)

    def get_day_of_week(self) -> str:
        return self.current.strftime("%A")

    def get_week_of_month(self) -> int:
        first_day = self.current.replace(day=1)
        adjusted_dom = self.current.day + first_day.weekday()
        return int((adjusted_dom - 1) / 7) + 1
    
    # -------------------------
    # Navigation
    # -------------------------
    def set_date(self, year: int, month: int, day: int):
        self.current = date(year, month, day)

    def reset_date(self):
        self.current = date.today()

    def next_day(self):
        self.current += timedelta(days=1)

    def previous_day(self):
        self.current -= timedelta(days=1)

    def next_month(self):
        year, month = self.current.year, self.current.month
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1
        self.current = self.current.replace(year=year, month=month, day=1)

    def previous_month(self):
        year, month = self.current.year, self.current.month
        if month == 1:
            year, month = year - 1, 12
        else:
            month -= 1
        self.current = self.current.replace(year=year, month=month, day=1)

    def next_year(self):
        self.current = self.current.replace(year=self.current.year + 1)

    def previous_year(self):
        self.current = self.current.replace(year=self.current.year - 1)
        
    # -------------------------
    # Grid Helpers
    # -------------------------
    def month_grid(self):
        """Return a 2D list representing the current month (weeks × days)."""
        import calendar
        cal = calendar.Calendar(firstweekday=0)  # Sunday=6
        return [
            [d if d.month == self.current.month else None
             for d in week]
            for week in cal.monthdatescalendar(self.current.year, self.current.month)
        ]
        
    # -------------------------
    # Conversions
    # -------------------------
    def iso_format(self) -> str:
        return self.current.isoformat()

    def us_format(self) -> str:
        return self.current.strftime("%m/%d/%Y")

    def eu_format(self) -> str:
        return self.current.strftime("%d/%m/%Y")

    def short_label(self) -> str:
        return self.current.strftime("%d %b %Y")

    def long_label(self) -> str:
        return self.current.strftime("%A, %B %d, %Y")
    
    # -------------------------
    # Utilities
    # -------------------------
    def is_today(self) -> bool:
        return self.current == date.today()

    def is_weekend(self) -> bool:
        return self.current.weekday() >= 5  # 5=Saturday, 6=Sunday

    def days_until(self, other: "Calendar") -> int:
        return (other.current - self.current).days

    # -------------------------
    # Events Integration
    # -------------------------
    def get_events_for_day(self, events_dict: dict) -> Optional[dict]:
        """events_dict format: {year: {month: {day: {"event": str, "link": str}}}}"""
        return (
            events_dict
            .get(self.current.year, {})
            .get(self.current.month, {})
            .get(self.current.day)
        )

    def highlighted(self, events_dict: dict) -> bool:
        return self.get_events_for_day(events_dict) is not None

    # -------------------------
    # Representation & Comparison
    # -------------------------
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Calendar):
            return self.current == other.current
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Calendar):
            return self.current < other.current
        return NotImplemented

    def __repr__(self) -> str:
        return f"Calendar(current={self.current})"

    def __str__(self) -> str:
        return self.to_string()

def toggle_button(label: str, v: bool, width=0, height =0, button_color:Color=Color(0, 0,0,255), hover_color:Color=Color(0, 0,0,255), active_color:Color=Color(0, 0,0,255)) -> bool:
    """
    Purpose: Create a toggle button that changes its state and color based on the current state.
    Args:
        label (str): The label of the button.
        v (bool): The current toggle state (True for on, False for off).
    Returns: bool: The new state of the button after being clicked.
    """
    clicked = False
    
    black = Color(0, 0, 0, 255)
    if button_color == black:
        button_color = Color.from_tuple(ImGui.style.get_color(PyImGui.ImGuiCol.Button))
        
    if hover_color == black:
        hover_color = Color.from_tuple(ImGui.style.get_color(PyImGui.ImGuiCol.ButtonHovered))
        
    if active_color == black:
        active_color = Color.from_tuple(ImGui.style.get_color(PyImGui.ImGuiCol.ButtonActive))

    if v:
        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, active_color.to_tuple_normalized())  # On color
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, hover_color.to_tuple_normalized())  # Hover color
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, active_color.to_tuple_normalized())
        if width != 0 and height != 0:
            clicked = PyImGui.button(label, width, height)
        else:
            clicked = PyImGui.button(label)
        PyImGui.pop_style_color(3)
    else:
        if width != 0 and height != 0:
            clicked = PyImGui.button(label, width, height)
        else:
            clicked = PyImGui.button(label)

    if clicked:
        v = not v

    return v


class ToggleButton:
    def __init__(self, label: str, toggled: bool = False, width: int = 30, height: int = 30):
        self.label = label
        self.toggled = toggled
        self.width = width
        self.height = height

    def is_toggled(self) -> bool:
        self.toggled = toggle_button(self.label, self.toggled, width=self.width, height=self.height)
        return self.toggled
    
    def set_toggled(self, state: bool) -> None:
        self.toggled = state
        
        
class Button:
    def __init__(self, label: str, width: int = 30, height: int = 30):
        self.label = label
        self.width = width
        self.height = height

    def draw(self, width: int | None = None, height: int | None = None) -> bool:
        w = width if width is not None else self.width
        h = height if height is not None else self.height
        return PyImGui.button(self.label, w, h)
      
calendar = Calendar()

class ButtonLayout:
    def __init__(self):
        self.button_width = 30
        self.button_height = 30
        self.period_caption = "MONTH - YEAR"

        self.button_day = ToggleButton(f"{IconsFontAwesome5.ICON_CALENDAR_DAY}", toggled=True,
                                       width=self.button_width, height=self.button_height)
        self.button_trimester = ToggleButton(f"{IconsFontAwesome5.ICON_CALENDAR_WEEK}", toggled=False,
                                             width=self.button_width, height=self.button_height)
        self.button_year = ToggleButton(f"{IconsFontAwesome5.ICON_CALENDAR_DAYS}", toggled=False,
                                        width=self.button_width, height=self.button_height)

        self.button_prev = Button(f"{IconsFontAwesome5.ICON_CHEVRON_LEFT}", width=self.button_width, height=self.button_height)
        self.button_next = Button(f"{IconsFontAwesome5.ICON_CHEVRON_RIGHT}", width=self.button_width, height=self.button_height)
        self.button_period = Button(self.period_caption, width=0, height=self.button_height)
        

    def get_active_scope(self) -> str:
        if self.button_day.toggled:
            return "month"
        if self.button_trimester.toggled:
            return "trimester"
        if self.button_year.toggled:
            return "year"
        return "month"

    def update_period_caption(self):
        scope = self.get_active_scope()
        if scope == "month":
            self.period_caption = calendar.get_short_month_year()
        elif scope == "trimester":
            q = (calendar.current.month - 1) // 3 + 1
            self.period_caption = f"Q{q} - {calendar.current.year}"
        elif scope == "year":
            self.period_caption = str(calendar.current.year)
        self.button_period.label = self.period_caption

    def draw(self):
        # Scope toggles
        if self.button_day.is_toggled():
            self.button_trimester.set_toggled(False)
            self.button_year.set_toggled(False)
        ImGui.show_tooltip("Month")
        PyImGui.same_line(0, -1)

        if self.button_trimester.is_toggled():
            self.button_day.set_toggled(False)
            self.button_year.set_toggled(False)
        ImGui.show_tooltip("Trimester")
        PyImGui.same_line(0, -1)

        if self.button_year.is_toggled():
            self.button_day.set_toggled(False)
            self.button_trimester.set_toggled(False)
        ImGui.show_tooltip("Year")
        PyImGui.same_line(0, -1)

        # Prev button
        if self.button_prev.draw():
            scope = self.get_active_scope()
            if scope == "month":
                calendar.previous_month()
            elif scope == "trimester":
                for _ in range(3):
                    calendar.previous_month()
            elif scope == "year":
                calendar.previous_year()

        PyImGui.same_line(0, -1)

        # Period caption
        self.update_period_caption()
        min_width = 100
        PyImGui.push_item_width(min_width)
        if self.button_period.draw(width=min_width):
            Py4GW.Console.Log("Calendar", "Period button clicked.", Py4GW.Console.MessageType.Info)
        PyImGui.pop_item_width()
        ImGui.show_tooltip("Select period")

        PyImGui.same_line(0, -1)
        
        # Next button
        if self.button_next.draw():
            scope = self.get_active_scope()
            if scope == "month":
                calendar.next_month()
            elif scope == "trimester":
                for _ in range(3):
                    calendar.next_month()
            elif scope == "year":
                calendar.next_year()
        

button_layout = ButtonLayout()
calendar = Calendar()
widget_handler: WidgetHandler = get_widget_handler()
calendar_window_open = True
owned_nicholas_farm_widget_id: Optional[str] = None



def draw_month(cal: Calendar, width: int = 300, height: int = 265):
    """Draw a single month inside a child so formatting stays intact."""
    child_id = f"month_{cal.current.month}_{cal.current.year}"
    if PyImGui.begin_child(child_id, (width, height), True, PyImGui.WindowFlags.NoFlag):
        # Caption
        PyImGui.text_colored(cal.get_month_year(), ColorPalette.GetColor("yellow").to_tuple_normalized())

        headers = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        if PyImGui.begin_table(f"calendar_table_{child_id}", 7, PyImGui.TableFlags.Borders):
            for h in headers:
                PyImGui.table_setup_column(h)
            PyImGui.table_headers_row()

            grid = cal.month_grid()
            for week in grid:
                PyImGui.table_next_row()
                for day in week:
                    PyImGui.table_next_column()
                    if day is None or day.month != cal.current.month:
                        PyImGui.text("")
                    else:
                        # Event check
                        event = get_event_for_day(day)
                        pve_bonus, pvp_bonus = get_weekly_bonuses(day)
                        nicholas = get_nicholas_for_day(day)
                        colors = event["colors"] if event else None

                        if event and colors:
                            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, tuple(c/255 for c in colors["button"]))
                            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, tuple(c/255 for c in colors["button_hover"]))
                            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, tuple(c/255 for c in colors["button_active"]))

                        if PyImGui.button(str(day.day), 30, 30):
                            calendar.set_date(day.year, day.month, day.day)   # 👈 this makes clicked date active

                            Py4GW.Console.Log("Calendar", f"Clicked raw day: {day}", Py4GW.Console.MessageType.Info)
                            Py4GW.Console.Log("Calendar", f"Global calendar set to: {calendar.current}", Py4GW.Console.MessageType.Info)



                        if event and colors:
                            PyImGui.pop_style_color(3)

                        if PyImGui.is_item_hovered():
                            if PyImGui.begin_tooltip():
                                PyImGui.text(f"{day.strftime('%A, %B %d, %Y')}")
                                if event and colors:
                                    PyImGui.text_colored(f"Event: {event['name']}", tuple(c/255 for c in colors["button_active"]))
                                if pve_bonus:
                                    PyImGui.text(f"PvE Weekly Bonus: {pve_bonus['name']}")
                                if pvp_bonus:
                                    PyImGui.text(f"PvP Weekly Bonus: {pvp_bonus['name']}")
                                if nicholas:  # << NEW tooltip info
                                    PyImGui.separator()
                                    PyImGui.text_colored("Nicholas the Traveler", (200/255, 155/255, 0, 1))
                                    PyImGui.text(f"Item: {nicholas['item']}")
                                else:
                                    PyImGui.text("Nicholas the Traveler: Not visiting this week.")
                                PyImGui.end_tooltip()

            PyImGui.end_table()
    PyImGui.end_child()

def _normalize_model_id(model: object) -> Optional[int]:
    """Convert model values (int or enum-like) into a comparable integer ID."""
    if isinstance(model, int):
        return model

    value = getattr(model, "value", None)
    if isinstance(value, int):
        return value

    try:
        return int(model)  # type: ignore[arg-type]
    except Exception:
        return None


def _extract_model_id_from_script(script_path: str) -> Optional[int]:
    """
    Read MODEL_ID_TO_FARM from a script without importing/executing it.
    Supports:
    - MODEL_ID_TO_FARM = 446
    - MODEL_ID_TO_FARM = ModelID.Shriveled_Eye
    """
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=script_path)
    except Exception:
        return None

    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue

        if not any(isinstance(t, ast.Name) and t.id == "MODEL_ID_TO_FARM" for t in targets):
            continue

        value_node = node.value
        if value_node is None:
            return None

        if isinstance(value_node, ast.Constant) and isinstance(value_node.value, int):
            return value_node.value

        if (
            isinstance(value_node, ast.Attribute)
            and isinstance(value_node.value, ast.Name)
            and value_node.value.id == "ModelID"
        ):
            enum_member = getattr(ModelID, value_node.attr, None)
            return _normalize_model_id(enum_member)

        return None

    return None


def get_script_path_for_model(model: int) -> Optional[str]:
    """
    Resolve the script filename for a given model ID.
    Returns the full path if found, otherwise None.
    """
    widgets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    bots_path = os.path.join(
        widgets_path,
        "Automation",
        "Bots",
        "Farmers",
        "Trophies",
        "Nicholas the Traveler",
    )

    model_id = _normalize_model_id(model)
    if model_id is None:
        return None

    try:
        for file in os.listdir(bots_path):
            if not file.endswith(".py"):
                continue

            full_path = os.path.join(bots_path, file)

            # Backward-compatible: legacy "<model>-Name.py" naming.
            if file.startswith(f"{model_id}-"):
                return full_path

            # Preferred: read MODEL_ID_TO_FARM from script content.
            file_model_id = _extract_model_id_from_script(full_path)
            if file_model_id == model_id:
                return full_path
    except Exception as e:
        Py4GW.Console.Log(
            "script loader",
            f"Error scanning for model {model_id}: {str(e)}",
            Py4GW.Console.MessageType.Error,
        )

    return None


def _normalize_script_path(path: str) -> str:
    return os.path.normcase(os.path.abspath(path))


def _get_widget_enabled_var_name(widget: Widget) -> str:
    return f"{widget.name}__enabled"


def _save_widget_enabled_state(widget: Widget) -> bool:
    manager_ini_key = widget_handler.MANAGER_INI_KEY
    if not manager_ini_key:
        Py4GW.Console.Log(
            MODULE_NAME,
            f"Widget Manager INI key is unavailable while updating '{widget.plain_name}'.",
            Py4GW.Console.MessageType.Warning,
        )
        return False

    IniManager().set(
        key=manager_ini_key,
        section=f"Widget:{widget.name}",
        var_name=_get_widget_enabled_var_name(widget),
        value=widget.enabled,
    )
    IniManager().save_vars(manager_ini_key)
    return True


def _set_widget_enabled(widget: Widget, enabled: bool) -> bool:
    try:
        if enabled:
            widget.enable()
        else:
            widget.disable()
    except Exception as e:
        Py4GW.Console.Log(
            MODULE_NAME,
            f"Failed to {'enable' if enabled else 'disable'} '{widget.plain_name}': {e}",
            Py4GW.Console.MessageType.Error,
        )
        return False

    state_saved = _save_widget_enabled_state(widget)
    return bool(widget.enabled) == bool(enabled) and state_saved


def _resolve_widget_for_script(script_path: str) -> Optional[Widget]:
    normalized_script_path = _normalize_script_path(script_path)

    for widget in widget_handler.widgets.values():
        if _normalize_script_path(widget.script_path) == normalized_script_path:
            return widget

    return None


def _disable_owned_farm(reason: str) -> bool:
    global owned_nicholas_farm_widget_id

    if not owned_nicholas_farm_widget_id:
        return False

    widget = widget_handler.get_widget_info(owned_nicholas_farm_widget_id)
    if widget is None:
        Py4GW.Console.Log(
            MODULE_NAME,
            f"Owned farm '{owned_nicholas_farm_widget_id}' is no longer registered; clearing ownership.",
            Py4GW.Console.MessageType.Warning,
        )
        owned_nicholas_farm_widget_id = None
        return False

    if widget.enabled:
        Py4GW.Console.Log(
            MODULE_NAME,
            f"Disabling owned farm '{widget.plain_name}' ({reason}).",
            Py4GW.Console.MessageType.Info,
        )
        if not _set_widget_enabled(widget, False):
            Py4GW.Console.Log(
                MODULE_NAME,
                f"Widget Manager state did not fully update while disabling owned farm '{widget.plain_name}'.",
                Py4GW.Console.MessageType.Warning,
            )
    else:
        _save_widget_enabled_state(widget)
        Py4GW.Console.Log(
            MODULE_NAME,
            f"Owned farm '{widget.plain_name}' was already disabled ({reason}); clearing ownership.",
            Py4GW.Console.MessageType.Info,
        )

    owned_nicholas_farm_widget_id = None
    return True


def _request_farm_enable(script_path: str, item_name: str) -> None:
    global owned_nicholas_farm_widget_id

    widget = _resolve_widget_for_script(script_path)
    if widget is None:
        Py4GW.Console.Log(
            MODULE_NAME,
            f"Unable to map farm script to a Widget Manager entry: {script_path}",
            Py4GW.Console.MessageType.Warning,
        )
        return

    Py4GW.Console.Log(
        MODULE_NAME,
        f"Requesting Widget Manager enable for Nicholas farm '{widget.plain_name}' ({item_name}).",
        Py4GW.Console.MessageType.Info,
    )

    if owned_nicholas_farm_widget_id and owned_nicholas_farm_widget_id != widget.name:
        _disable_owned_farm(f"switching to '{widget.plain_name}'")

    if widget.enabled:
        if not _save_widget_enabled_state(widget):
            Py4GW.Console.Log(
                MODULE_NAME,
                f"Widget Manager state did not fully update while syncing enabled farm '{widget.plain_name}'.",
                Py4GW.Console.MessageType.Warning,
            )
        if owned_nicholas_farm_widget_id == widget.name:
            Py4GW.Console.Log(
                MODULE_NAME,
                f"Nicholas farm '{widget.plain_name}' is already enabled and still owned by Calendar.",
                Py4GW.Console.MessageType.Info,
            )
        else:
            owned_nicholas_farm_widget_id = None
            Py4GW.Console.Log(
                MODULE_NAME,
                f"Nicholas farm '{widget.plain_name}' was already enabled; Calendar will not claim ownership.",
                Py4GW.Console.MessageType.Info,
            )
        return

    if _set_widget_enabled(widget, True):
        owned_nicholas_farm_widget_id = widget.name
        Py4GW.Console.Log(
            MODULE_NAME,
            f"Enabled Nicholas farm '{widget.plain_name}' via Widget Manager; Calendar now owns this enablement.",
            Py4GW.Console.MessageType.Info,
        )
    else:
        owned_nicholas_farm_widget_id = None
        Py4GW.Console.Log(
            MODULE_NAME,
            f"Widget Manager failed to enable Nicholas farm '{widget.plain_name}'.",
            Py4GW.Console.MessageType.Warning,
        )


def _disable_calendar_widget(reason: str) -> None:
    calendar_widget = widget_handler.get_widget_info(MODULE_NAME)
    if calendar_widget is None:
        Py4GW.Console.Log(
            MODULE_NAME,
            f"Calendar widget entry was not found while handling '{reason}'.",
            Py4GW.Console.MessageType.Warning,
        )
        _disable_owned_farm(reason)
        return

    Py4GW.Console.Log(
        MODULE_NAME,
        f"Disabling Calendar widget ({reason}).",
        Py4GW.Console.MessageType.Info,
    )
    _set_widget_enabled(calendar_widget, False)


def on_enable():
    global calendar_window_open
    calendar_window_open = True


def on_disable():
    _disable_owned_farm("Calendar disabled or unloaded")

def DrawDayCard():
    selected_day = calendar.current   # 👈 use current calendar date, not today
    current_event = get_event_for_day(selected_day)
    pve_bonus, pvp_bonus = get_weekly_bonuses(selected_day)
    nicholas = get_nicholas_for_day(selected_day)

    # Show the selected date (defaults to today)
    PyImGui.text_colored(f"{calendar.get_day_of_week()}, {selected_day.strftime('%B %d, %Y')}",  ColorPalette.GetColor("yellow").to_tuple_normalized())
    PyImGui.text_colored(f"PvE Bonus:",  ColorPalette.GetColor("gw_gold").to_tuple_normalized())
    PyImGui.same_line(0, -1)
    PyImGui.text(f"{pve_bonus['name']}")
    PyImGui.text_colored(f"PvP Bonus:",  ColorPalette.GetColor("gw_gold").to_tuple_normalized())
    PyImGui.same_line(0, -1)
    PyImGui.text(f"{pvp_bonus['name']}")
    
    if nicholas:
        table_flags = PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersOuterH
        if PyImGui.begin_table("Nictable", 2, table_flags):
            iconwidth = 96
            child_width = 300
            child_height = 275
            PyImGui.table_setup_column("Icon", PyImGui.TableColumnFlags.WidthFixed, iconwidth)
            PyImGui.table_setup_column("titles", PyImGui.TableColumnFlags.WidthFixed, child_width - iconwidth)
            PyImGui.table_next_row()
            PyImGui.table_set_column_index(0)
            ImGui.DrawTexture(get_texture_for_model(nicholas["model_id"]), iconwidth, iconwidth)
            PyImGui.table_set_column_index(1)
            if PyImGui.begin_table("Nick Info", 1, PyImGui.TableFlags.NoFlag):
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                ImGui.push_font("Regular", 20)
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ColorPalette.GetColor("yellow").to_tuple_normalized())
                PyImGui.text(f"Nicholas the Traveler")
                PyImGui.pop_style_color(1)
                ImGui.pop_font()
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0)
                PyImGui.text(f"Item: {nicholas['item']}")
                PyImGui.text(f"Location: {nicholas['location']}")
                PyImGui.text(f"Region: {nicholas['region']}")
                PyImGui.text(f"Campaign: {nicholas['campaign']}")
                if nicholas["map_url"]:
                    if PyImGui.button("View Map"):
                        import webbrowser
                        webbrowser.open(nicholas["map_url"])
                    ImGui.show_tooltip("Open map in browser")
                    farm_script = get_script_path_for_model(nicholas["model_id"])
                    if farm_script:
                        PyImGui.same_line(0, -1)
                        if PyImGui.button("Load Farm"):
                            _request_farm_enable(farm_script, nicholas["item"])
                        ImGui.show_tooltip(f"Load farm script for {nicholas['item']}")

                    
                             
                PyImGui.end_table()
            PyImGui.end_table()

    else:
        PyImGui.text(f"No Nicholas data to show for {selected_day}")

    if current_event:
        colors = current_event["colors"]

        # Draw the button with event name
        PyImGui.text(f"Current Event: {current_event['name']}")
        if "dropped_items" in current_event and current_event["dropped_items"]:
            PyImGui.separator()
            PyImGui.text_colored("Event Drops", (0.8, 0.8, 0.2, 1))  # yellowish

            #Prevents crashes of Imgui if the  table is to small
            item_amount = max(len(current_event["dropped_items"]), 1)
            if PyImGui.is_rect_visible(0, 20):
                if PyImGui.begin_table("event_drops_table", item_amount, PyImGui.TableFlags.NoFlag):
                    for _ in range(item_amount):
                        PyImGui.table_setup_column("Item", PyImGui.TableColumnFlags.WidthFixed, 48)
                        
                    PyImGui.table_next_row()
                    PyImGui.table_next_column()

                    for _, item in enumerate(current_event["dropped_items"]):
                        ImGui.DrawTexture(get_texture_for_model(item), 48, 48)                        
                        ImGui.show_tooltip(str(item.name))                        
                        PyImGui.table_next_column()
                        
                    PyImGui.end_table()

            PyImGui.separator()
    else:
        # No event: just draw a text label
        PyImGui.text("Current Event: - No Event Active")



def DrawWindow() -> bool:
    global button_layout, calendar, calendar_window_open
    window_flags = PyImGui.WindowFlags.AlwaysAutoResize

    is_window_opened, calendar_window_open = PyImGui.begin_with_close("Calendar", calendar_window_open, window_flags)

    if calendar_window_open and is_window_opened:
        button_layout.draw()
        PyImGui.separator()

        scope = button_layout.get_active_scope()

        if scope == "month":
            draw_month(calendar)

        elif scope == "trimester":
            q = (calendar.current.month - 1) // 3
            start_month = q * 3 + 1
            for i in range(3):
                month_cal = Calendar(date(calendar.current.year, start_month + i, 1))
                draw_month(month_cal)
                if i < 2:
                    PyImGui.same_line(0,-1)

        elif scope == "year":
            for i in range(12):
                month_cal = Calendar(date(calendar.current.year, i + 1, 1))
                draw_month(month_cal)
                if (i + 1) % 4 != 0:  # 4 per row
                    PyImGui.same_line(0,-1)

    PyImGui.end()
    return calendar_window_open

def DrawDayWindow():
    if PyImGui.begin("Event Details", PyImGui.WindowFlags.AlwaysAutoResize):
        DrawDayCard()
    PyImGui.end()


def tooltip():
    ImGui.begin_tooltip()
    title_color = ColorPalette.GetColor("yellow")
    ImGui.push_font("Regular", 24)
    PyImGui.text_colored("Calendar", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.separator()

    # Description
    PyImGui.text("This widget provides a calendar interface that highlights")
    PyImGui.text("in-game events, weekly bonuses, and Nicholas the Traveler's schedule.")
    PyImGui.text("Users can navigate through months, trimesters, and years to plan their")
    PyImGui.text("in-game activities accordingly.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("View monthly calendars with highlighted in-game events.")
    PyImGui.bullet_text("See weekly PvE and PvP bonuses.")
    PyImGui.bullet_text("See Seasonal Events and their details.")
    PyImGui.bullet_text("Check Nicholas the Traveler's weekly item and location.")
    PyImGui.bullet_text("Navigate by month, trimester, or year.")
    PyImGui.bullet_text("Load farm scripts for Nicholas's items directly.")
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")

    ImGui.end_tooltip()

def main():
    try:
        if not DrawWindow():
            _disable_calendar_widget("main window closed")
            return
        DrawDayWindow()
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

if __name__ == "__main__":
    main()
