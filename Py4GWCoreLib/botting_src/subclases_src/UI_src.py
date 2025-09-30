#region STATES
from typing import TYPE_CHECKING, Callable, Optional, Tuple
from Py4GWCoreLib import Color
from Py4GWCoreLib import Routines
import PyImGui

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass
    
    
    
#region UI
class _UI:
    def __init__(self, parent: "BottingClass"):
        self.parent:BottingClass = parent
        self._parent:BottingClass = parent
        self._config = parent.config
        self._helpers = parent.helpers
        self.draw_texture_fn: Optional[Callable[[], None]] = None
        self.draw_config_fn: Optional[Callable[[], None]] = None
        self.draw_help_fn: Optional[Callable[[], None]] = None

        self._FSM_SELECTED_NAME_ORIG: str | None = None   # selection persists across frames
        self._FSM_FILTER_START: int = 0
        self._FSM_FILTER_END: int = 0

    def CancelSkillRewardWindow(self):
        self._helpers.UI.cancel_skill_reward_window()

    def _draw_path(self, color:Color=Color(255, 255, 0, 255), use_occlusion: bool = False, snap_to_ground_segments: int = 1, floor_offset: float = 0) -> None:
        from ...DXOverlay import DXOverlay
        path = self._config.path_to_draw

        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            z1 = DXOverlay.FindZ(x1, y1)
            z2 = DXOverlay.FindZ(x2, y2)
            DXOverlay().DrawLine3D(x1, y1, z1, x2, y2, z2, color.to_color(), use_occlusion, snap_to_ground_segments, floor_offset)


    def DrawPath(self, color:Color=Color(255, 255, 0, 255), use_occlusion: bool = False, snap_to_ground_segments: int = 1, floor_offset: float = 0) -> None:
        if self._config.config_properties.draw_path.is_active() and Routines.Checks.Map.MapValid():
            self._draw_path(color, use_occlusion, snap_to_ground_segments, floor_offset)

    def SendChatMessage(self, channel: str, message: str):
        self._helpers.UI.send_chat_message(channel, message)

    def PrintMessageToConsole(self, source: str, message: str):
        self._helpers.UI.print_message_to_console(source, message)

    def _find_current_header_step(self):
        import re

        steps = self._config.FSM.get_state_names()
        total_steps = len(steps)

        # Raw current index as reported by the FSM (may be None or out-of-bounds at "end")
        raw_current = self._config.FSM.get_current_state_number()

        # Normalize and detect "finished"
        if total_steps == 0:
            # No steps at all
            current_idx = -1
            finished = True
            step_name = None
            search_from = -1
        else:
            if raw_current is None:
                finished = True
                current_idx = total_steps - 1           # clamp to last valid index for display
            elif raw_current < 0:
                finished = False
                current_idx = 0                         # clamp up
            elif raw_current >= total_steps:
                finished = True
                current_idx = total_steps - 1           # clamp down
            else:
                finished = False
                current_idx = raw_current

            step_name = None if finished else self._config.FSM.get_state_name_by_number(current_idx)
            search_from = current_idx if current_idx >= 0 else -1

        # Find nearest preceding [H] header up to the display index (or last if empty/finished)
        header_for_current = None
        current_header_step = -1
        if total_steps > 0 and search_from >= 0:
            for i in range(search_from, -1, -1):
                name = steps[i]
                if name.startswith("[H]"):
                    # strip "[H]" and trailing index suffixes "_[n]" or "_n"
                    name_clean = re.sub(r'^\[H\]\s*', '', name)
                    name_clean = re.sub(r'_(?:\[\d+\]|\d+)$', '', name_clean)
                    header_for_current = name_clean
                    current_header_step = i
                    break

        return current_header_step, header_for_current, current_idx, total_steps, step_name, finished


    def _draw_texture(self, texture_path:str, size:Tuple[float,float]=(96.0,96.0), tint:Color=Color(255,255,255,255), border_col:Color=Color(0,0,0,0)):
        from ...ImGui import ImGui
        from ...enums import get_texture_for_model
        if self.draw_texture_fn is not None:
            self.draw_texture_fn()
            return

        if not texture_path:
            texture_path = get_texture_for_model(0)
        
        ImGui.DrawTextureExtended(texture_path=texture_path, size=size,
                                uv0=(0.0, 0.0),   uv1=(1.0, 1.0),
                                tint=tint.to_tuple(), border_color=border_col.to_tuple())
        
    def override_draw_texture(self, draw_fn: Optional[Callable[[], None]] = None) -> None:
        """
        Override the texture drawing function.
        If draw_fn is None, resets to default drawing behavior.
        """
        self.draw_texture_fn = draw_fn
        
    def override_draw_config(self, draw_fn: Optional[Callable[[], None]] = None) -> None:
        """
        Override the config drawing function.
        If draw_fn is None, resets to default drawing behavior.
        """
        self.draw_config_fn = draw_fn
        
    def override_draw_help(self, draw_fn: Optional[Callable[[], None]] = None) -> None:
        """
        Override the help drawing function.
        If draw_fn is None, resets to default drawing behavior.
        """
        self.draw_help_fn = draw_fn
        
    def _draw_fsm_jump_button(self) -> None:
        if self._FSM_SELECTED_NAME_ORIG:
            sel_num = self._config.FSM.get_state_number_by_name(self._FSM_SELECTED_NAME_ORIG)
            sel_str = f"{sel_num-1}" if isinstance(sel_num, int) else "N/A"
            PyImGui.text(f"Selected: {self._FSM_SELECTED_NAME_ORIG}  (#{sel_str})")
        else:
            PyImGui.text("Selected: (none)")

        if PyImGui.button("Jump to Selected") and self._FSM_SELECTED_NAME_ORIG:
            self._config.fsm_running = True
            self._config.FSM.reset()
            self._config.FSM.jump_to_state_by_name(self._FSM_SELECTED_NAME_ORIG)

            
    def _draw_step_range_inputs(self):
        steps = self._config.FSM.get_state_names()
        if not steps:
            self._FSM_FILTER_START = 0
            self._FSM_FILTER_END = 0
            PyImGui.text("No steps.")
            return

        last_index = len(steps) - 1
        if self._FSM_FILTER_END == 0 and last_index > 0:
            self._FSM_FILTER_END = last_index

        self._FSM_FILTER_START = PyImGui.input_int("Start Step", self._FSM_FILTER_START)
        self._FSM_FILTER_END   = PyImGui.input_int("End Step",   self._FSM_FILTER_END)

        self._FSM_FILTER_START = max(0, min(self._FSM_FILTER_START, last_index))
        self._FSM_FILTER_END   = max(0, min(self._FSM_FILTER_END,   last_index))
        if self._FSM_FILTER_START > self._FSM_FILTER_END:
            self._FSM_FILTER_START, self._FSM_FILTER_END = self._FSM_FILTER_END, self._FSM_FILTER_START

        PyImGui.same_line(0,-1)
        if PyImGui.button("Reset Range"):
            self._FSM_FILTER_START = 0
            self._FSM_FILTER_END   = last_index

        PyImGui.text(f"Showing steps [{self._FSM_FILTER_START} … {self._FSM_FILTER_END}] of 0…{last_index}")



    def _get_fsm_sections(self):
        """
        -> List[dict] with:
        header_idx:int, header_name_orig:str, header_name_clean:str,
        children: List[Tuple[int, str]]  # (step_index, original_name)
        Groups steps under the nearest preceding [H] header.
        """
        def _clean_header(name: str) -> str:
            import re
            if name.startswith("[H]"):
                name = re.sub(r'^\[H\]\s*', '', name)
                name = re.sub(r'_(?:\[\d+\]|\d+)$', '', name)
            return name

        steps = self._config.FSM.get_state_names()
        sections = []
        current = None

        for i, name in enumerate(steps):
            if name.startswith("[H]"):
                if current is not None:
                    sections.append(current)
                current = {
                    "header_idx": i,
                    "header_name_orig": name,
                    "header_name_clean": _clean_header(name),
                    "children": []
                }
            else:
                if current is None:
                    current = {
                        "header_idx": -1,
                        "header_name_orig": "[H] (No Header)",
                        "header_name_clean": "(No Header)",
                        "children": []
                    }
                current["children"].append((i, name))

        if current is not None:
            sections.append(current)
        return sections
    
    def draw_fsm_tree_selector_ranged(self, child_size: Tuple[float, float]=(350, 250)) -> str | None:
        """
        Scrollable child window with a header-grouped tree,
        filtered to only show steps in [_FSM_FILTER_START, _FSM_FILTER_END].
        Returns selected ORIGINAL name or None.
        """

        # filter inputs
        self._draw_step_range_inputs()
        PyImGui.separator()

        sections = self._get_fsm_sections()
        NOFLAG = PyImGui.SelectableFlags.NoFlag
        SIZE: Tuple[float, float] = (0.0, 0.0)

        PyImGui.begin_child("fsm_tree_ranged_child", child_size, True, 0)

        any_drawn = False
        for sec in sections:
            # header/children within range?
            header_in_range = (sec["header_idx"] >= 0 and self._FSM_FILTER_START <= sec["header_idx"] <= self._FSM_FILTER_END)
            children_in_range = [(idx, nm) for (idx, nm) in sec["children"] if self._FSM_FILTER_START <= idx <= self._FSM_FILTER_END]

            if not header_in_range and not children_in_range:
                continue

            any_drawn = True
            header_idx_label = sec["header_idx"] if sec["header_idx"] >= 0 else "—"
            parent_label = f"[{header_idx_label}] {sec['header_name_clean']}##hdr_{header_idx_label}"

            if PyImGui.tree_node(parent_label):
                # header selectable
                header_label = f"(Header) {sec['header_name_clean']}##sel_hdr_{header_idx_label}"
                is_header_sel = (self._FSM_SELECTED_NAME_ORIG == sec["header_name_orig"])
                if PyImGui.selectable(header_label, is_header_sel, NOFLAG, SIZE):
                    self._FSM_SELECTED_NAME_ORIG = sec["header_name_orig"]

                # children (in range)
                for idx, name_orig in children_in_range:
                    label = f"[{idx}] {name_orig}##sel_step_{idx}"
                    is_sel = (self._FSM_SELECTED_NAME_ORIG == name_orig)
                    if PyImGui.selectable(label, is_sel, NOFLAG, SIZE):
                        self._FSM_SELECTED_NAME_ORIG = name_orig

                PyImGui.tree_pop()

        if not any_drawn:
            PyImGui.text("No steps in selected range.")

        PyImGui.end_child()
        return self._FSM_SELECTED_NAME_ORIG

    def _draw_main_child (self, main_child_dimensions: Tuple[int, int]  = (350, 275), 
                            icon_path:str = "",
                            iconwidth: int = 96) -> None:
        from ...ImGui import ImGui
        from ...ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
        from ...Py4GWcorelib import ConsoleLog, Console
        from ...GlobalCache import GLOBAL_CACHE
        
        current_header_step, header_for_current , current_step, total_steps, step_name, finished = self._find_current_header_step()
        if PyImGui.begin_table("bot_header_table", 2, PyImGui.TableFlags.RowBg | PyImGui.TableFlags.BordersOuterH):
            PyImGui.table_setup_column("Icon", PyImGui.TableColumnFlags.WidthFixed, iconwidth)
            PyImGui.table_setup_column("titles", PyImGui.TableColumnFlags.WidthFixed, main_child_dimensions[0] - iconwidth)
            PyImGui.table_next_row()
            PyImGui.table_set_column_index(0)
            self._draw_texture(texture_path=icon_path, size=(iconwidth, iconwidth))
            PyImGui.table_set_column_index(1)
            
            PyImGui.dummy(0,3)
            ImGui.push_font("Regular", 22)
            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, Color(255, 255, 0, 255).to_tuple_normalized())
            PyImGui.text(f"{self._config.bot_name}")
            PyImGui.pop_style_color(1)
            ImGui.pop_font()
    
            ImGui.push_font("Bold", 18)
            PyImGui.text(f"[{max(current_header_step, 0)}] {header_for_current or 'Not started'}")
            ImGui.pop_font()
            if total_steps <= 0:
                PyImGui.text("Step: —/— - (No steps)")
            else:
                # When finished we show the last index and mark it as Finished
                if finished:
                    PyImGui.text(f"Step: {total_steps-1}/{total_steps-1} - (Finished)")
                else:
                    PyImGui.text(f"Step: {current_step}/{max(total_steps-1, 0)} - {step_name or '(…?)'}")

            # Status line
            if not self._config.fsm_running and finished:
                self._config.state_description = "Finished"
            PyImGui.text(f"Status: {self._config.state_description}")

            PyImGui.end_table()

        
        # --- Single toggle button: Play ↔ Stop ---
        icon = IconsFontAwesome5.ICON_STOP_CIRCLE if self._config.fsm_running else IconsFontAwesome5.ICON_PLAY_CIRCLE
        legend = "  Stop" if self._config.fsm_running else "  Start"
        if PyImGui.button(icon + legend + "##BotToggle"):
            if self._config.fsm_running:
                # Stop
                self._config.fsm_running = False
                ConsoleLog(self._config.bot_name, "Script stopped", Console.MessageType.Info)
                self._config.state_description = "Idle"
                self._config.FSM.stop()
                GLOBAL_CACHE.Coroutines.clear()
            else:
                # Start
                self._config.fsm_running = True
                ConsoleLog(self._config.bot_name, "Script started", Console.MessageType.Info)
                self._config.state_description = "Running"
                self._config.FSM.restart()


            
        if total_steps > 1:
            fraction = (total_steps - 1) and (current_step / float(total_steps - 1)) or 0.0
        else:
            fraction = 1.0 if finished and total_steps == 1 else 0.0
        if finished and total_steps > 0:
            fraction = 1.0
        fraction = max(0.0, min(1.0, fraction))

            
        PyImGui.text("Overall Progress")
        PyImGui.push_item_width(main_child_dimensions[0] - 10)
        PyImGui.progress_bar(fraction, (main_child_dimensions[0] - 10), 0, f"{fraction * 100:.2f}%")
        PyImGui.pop_item_width()
        
        PyImGui.separator()
        PyImGui.text("Step Progress")
        PyImGui.push_item_width(main_child_dimensions[0] - 10)
        PyImGui.progress_bar(self._config.state_percentage, (main_child_dimensions[0] - 10), 0, f"{self._config.state_percentage * 100:.2f}%")
        PyImGui.pop_item_width()

    def _draw_settings_child(self):
        if self.draw_config_fn:
            self.draw_config_fn()
            return 
        
        PyImGui.text("Bot Settings")
        PyImGui.separator()
        PyImGui.text("override this function to provide custom settings")
        PyImGui.text("use bot.Override_settings to set a custom settings function")
        PyImGui.separator()

    def _draw_help_child(self):
        if self.draw_help_fn:
            self.draw_help_fn()
            return
        
        PyImGui.text("Bot Help")
        PyImGui.separator()
        PyImGui.text("override this function to provide custom help info")
        PyImGui.text("use bot.Override_help to set a custom help function")
        PyImGui.separator()
        
    def draw_configure_window(self):
        from ...ImGui import ImGui
        from ...ImGui_src.IconsFontAwesome5 import IconsFontAwesome5

        if PyImGui.begin("Bot Configuration", PyImGui.WindowFlags.AlwaysAutoResize):
            self._draw_settings_child()    
            PyImGui.end()  
    
    def draw_debug_window(self):
        if PyImGui.collapsing_header("Map Navigation"):
            self._config.config_properties.draw_path.set_now("active",PyImGui.checkbox("Draw Path", self._config.config_properties.draw_path.is_active()))
            self._config.config_properties.use_occlusion.set_now("active",PyImGui.checkbox("Use Occlusion", self._config.config_properties.use_occlusion.is_active()))
            self._config.config_properties.snap_to_ground_segments.set_now("value", PyImGui.slider_int("Snap to Ground Segments", self._config.config_properties.snap_to_ground_segments.get("value"), 1, 32))
            self._config.config_properties.floor_offset.set_now("value", PyImGui.slider_float("Floor Offset", self._config.config_properties.floor_offset.get("value"), -10.0, 50.0))

        if PyImGui.collapsing_header("Properties"):
            def debug_text(prop_name:str, key:str):
                from ...Py4GWcorelib import Utils
                value = self._parent.Properties.Get(prop_name, key)
                if isinstance(value, bool):
                    color = Utils.TrueFalseColor(value)
                else:
                    color = (255, 255, 255, 255)
                PyImGui.text_colored(f"{prop_name} - {key}: {value}", color)

            debug_text("log_actions", "active")
            debug_text("halt_on_death", "active")
            debug_text("pause_on_danger", "active")
            PyImGui.text("InDanger(PauseOnDangerFn eval):")
            PyImGui.same_line(0,-1)
            parent = self._parent
            if parent.config.pause_on_danger_fn():
                PyImGui.text_colored(f"{parent.config.pause_on_danger_fn()}", (0, 255, 0, 255))
            else:
                PyImGui.text_colored(f"{parent.config.pause_on_danger_fn()}", (255, 0, 0, 255))

            debug_text("movement_timeout", "value")
            debug_text("movement_tolerance", "value")
            debug_text("draw_path", "active")
            debug_text("use_occlusion", "active")
            debug_text("snap_to_ground", "active")
            debug_text("snap_to_ground_segments", "value")
            debug_text("floor_offset", "value")
            debug_text("follow_path_color", "value")
            PyImGui.separator()
            debug_text("follow_path_succeeded", "value")
            debug_text("dialog_at_succeeded", "value")
            PyImGui.separator()
            debug_text("auto_combat", "active")
            debug_text("hero_ai", "active")
            debug_text("auto_loot", "active")
            debug_text("auto_inventory_management", "active")

        
        if PyImGui.collapsing_header("UpkeepData"):
            def render_upkeep_data(parent):
                # ---- your exact accessor, unchanged ----
                def debug_text(prop_name: str, key: str):
                    from ...Py4GWcorelib import Utils
                    value = self._parent.Properties.Get(prop_name, key)
                    if isinstance(value, bool):
                        color = Utils.TrueFalseColor(value)
                    else:
                        color = (255, 255, 255, 255)
                    PyImGui.text_colored(f"{prop_name} - {key}: {value}", color)

                # Most items: ("active", "restock_quantity")
                DEFAULT_KEYS = ("active", "restock_quantity")

                # Compact spec: either "prop" (uses DEFAULT_KEYS) or ("prop", (<custom keys>))
                ITEMS = [
                    ("alcohol", ("active", "target_drunk_level", "disable_visual")),
                    "armor_of_salvation",
                    ("auto_combat", ("active",)),
                    ("auto_inventory_management", ("active",)),
                    ("auto_loot", ("active",)),
                    "birthday_cupcake",
                    "blue_rock_candy",
                    "bowl_of_skalefin_soup",
                    "candy_apple",
                    "candy_corn",
                    ("city_speed", ("active",)),
                    "drake_kabob",
                    "essence_of_celerity",
                    "four_leaf_clover",
                    "golden_egg",
                    "grail_of_might",
                    "green_rock_candy",
                    ("hero_ai", ("active",)),
                    "honeycomb",
                    ("imp", ("active",)),
                    ("morale", ("active", "target_morale")),
                    "pahnai_salad",
                    "red_rock_candy",
                    "slice_of_pumpkin_pie",
                    "war_supplies",
                    "identify_kits",
                    "salvage_kits",
                ]

                if not PyImGui.collapsing_header("UpkeepData"):
                    return

                for item in ITEMS:
                    if isinstance(item, str):
                        prop, keys = item, DEFAULT_KEYS
                    else:
                        prop, keys = item

                    if PyImGui.tree_node(prop):
                        PyImGui.push_id(prop)  # avoid ID collisions for the same key labels
                        for key in keys:
                            debug_text(prop, key)
                        PyImGui.pop_id()
                        PyImGui.tree_pop()

            render_upkeep_data(self)

        if PyImGui.collapsing_header("Build"):
            def render_build_data(parent):
                build_handler = parent.config.build_handler

                def debug_text(prop_name: str, value: object):
                    from ...Py4GWcorelib import Utils
                    if isinstance(value, bool):
                        color = Utils.TrueFalseColor(value)
                    elif isinstance(value, (int, float)):
                        color = (200, 200, 255, 255)  # numbers: bluish
                    elif isinstance(value, str):
                        color = (200, 255, 200, 255)  # strings: greenish
                    else:
                        color = (255, 255, 255, 255)  # default white
                    PyImGui.text_colored(f"{prop_name}: {value}", color)

                # Walk over instance attributes
                for key, value in build_handler.__dict__.items():
                    if PyImGui.tree_node(key):
                        PyImGui.push_id(key)
                        debug_text(key, value)
                        PyImGui.pop_id()
                        PyImGui.tree_pop()

            render_build_data(self.parent)

        
        
    def draw_window(
        self, 
        main_child_dimensions: Tuple[int, int] = (350, 275),
        icon_path: str = "",
        iconwidth: int = 96,
        addtional_ui: Optional[Callable[[], None]] = None
    ):

        if PyImGui.begin(self._config.bot_name, PyImGui.WindowFlags.AlwaysAutoResize):
            if PyImGui.begin_tab_bar(self._config.bot_name + "_tabs"):
                if PyImGui.begin_tab_item("Main"):
                    if PyImGui.begin_child(f"{self._config.bot_name} - Main", main_child_dimensions, True, PyImGui.WindowFlags.NoFlag):
                        self._draw_main_child(main_child_dimensions, icon_path, iconwidth)
                        if addtional_ui:
                            PyImGui.separator()
                            addtional_ui()
                        PyImGui.end_child()
                    PyImGui.end_tab_item()
                
                if PyImGui.begin_tab_item("Navigation"):        
                    PyImGui.text("Jump to step (filtered by step index):")
                    self._draw_fsm_jump_button()
                    PyImGui.separator()
                    selected_name = self.draw_fsm_tree_selector_ranged(child_size=main_child_dimensions)
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("Settings"):
                    self._draw_settings_child()
                    PyImGui.end_tab_item()
                    
                if PyImGui.begin_tab_item("Help"):
                    self._draw_help_child()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("Debug"):
                    
                    self.draw_debug_window()
                    PyImGui.end_tab_item()
                    
                PyImGui.end_tab_bar()

        PyImGui.end()
        self.parent.UI.DrawPath(
            self._config.config_properties.follow_path_color.get("value"), 
            self._config.config_properties.use_occlusion.is_active(), 
            self._config.config_properties.snap_to_ground_segments.get("value"), 
            self._config.config_properties.floor_offset.get("value"))
