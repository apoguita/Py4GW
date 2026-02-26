
import pathlib
import sys
import os
import json
import time

import Py4GW
from Py4GWCoreLib import ImGui, Map, PyImGui, Routines, Color, Style, ThemeTextures, Utils
from Py4GWCoreLib.Py4GWcorelib import ThrottledTimer
from Py4GWCoreLib.UIManager import UIManager
from Sources.oazix.CustomBehaviors.PathLocator import PathLocator
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.fps_monitor import FPSMonitor
from Sources.oazix.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Sources.oazix.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Sources.oazix.CustomBehaviors.primitives.widget_monitor import WidgetMonitor

# Iterate through all modules in sys.modules (already imported modules)
# Iterate over all imported modules and reload them
for module_name in list(sys.modules.keys()):
    if module_name not in ("sys", "importlib", "cache_data"):
        try:
            if "behavior" in module_name.lower():
                # Py4GW.Console.Log("CustomBehaviors", f"Reloading module: {module_name}")
                del sys.modules[module_name]
                # importlib.reload(module_name)
                pass
        except Exception as e:
            Py4GW.Console.Log("CustomBehaviors", f"Error reloading module {module_name}: {e}")

from Sources.oazix.CustomBehaviors.daemon import daemon
from Sources.oazix.CustomBehaviors.primitives import constants
from Sources.oazix.CustomBehaviors.primitives.fps_monitor import FPSMonitor
from Sources.oazix.CustomBehaviors.primitives.widget_monitor import WidgetMonitor
from Sources.oazix.CustomBehaviors.gui.current_build import render as current_build_render
from Sources.oazix.CustomBehaviors.gui.party import render as party
from Sources.oazix.CustomBehaviors.gui.debug_skillbars import render as debug_skilbars
from Sources.oazix.CustomBehaviors.gui.debug_execution import render as debug_execution
from Sources.oazix.CustomBehaviors.gui.debug_sharedlocks import render as debug_sharedlocks
from Sources.oazix.CustomBehaviors.gui.debug_eventbus import render as debug_eventbus
from Sources.oazix.CustomBehaviors.gui.debug_eval_profiler import render as debug_eval_profiler
from Sources.oazix.CustomBehaviors.gui.auto_mover import render as auto_mover
from Sources.oazix.CustomBehaviors.gui.teambuild import render as teambuild
from Sources.oazix.CustomBehaviors.gui.botting import render as botting

party_forced_state_combo = 0
current_path = pathlib.Path.cwd()
monitor = FPSMonitor(history=300)
widget_monitor = WidgetMonitor()
# print(f"current_path is : {current_path}")
widget_window_size:tuple[float, float] = (0,0)
widget_window_pos:tuple[float, float] = (0,0)
widget_window_initialized = False

WIDGET_TITLE = "Custom behaviors - Multiboxing over utility-ai algorithm."
ui_state_path = "Py4GW/custom_behaviors_widget_ui.json"
handle_icon_path = PathLocator.get_custom_behaviors_root_directory() + "\\gui\\textures\\all.png"

hover_handle_mode = True
hover_pin_open = False
hover_is_visible = True
hover_hide_delay_s = 0.35
hover_hide_deadline = 0.0
hover_handle_initialized = False
saved_handle_pos = None
saved_window_pos = None
saved_window_size = None
layout_dirty = False
layout_save_timer = ThrottledTimer(750)


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _load_ui_state():
    global saved_handle_pos, saved_window_pos, saved_window_size, hover_pin_open, hover_handle_mode
    try:
        if not os.path.exists(ui_state_path):
            return
        with open(ui_state_path, mode="r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data.get("handle_pos"), list) and len(data["handle_pos"]) == 2:
            saved_handle_pos = (_safe_float(data["handle_pos"][0]), _safe_float(data["handle_pos"][1]))
        if isinstance(data.get("window_pos"), list) and len(data["window_pos"]) == 2:
            saved_window_pos = (_safe_float(data["window_pos"][0]), _safe_float(data["window_pos"][1]))
        if isinstance(data.get("window_size"), list) and len(data["window_size"]) == 2:
            saved_window_size = (_safe_float(data["window_size"][0]), _safe_float(data["window_size"][1]))
        hover_pin_open = bool(data.get("pin_open", hover_pin_open))
        hover_handle_mode = bool(data.get("hover_handle_mode", hover_handle_mode))
    except Exception:
        pass


def _save_ui_state():
    try:
        os.makedirs(os.path.dirname(ui_state_path), exist_ok=True)
        with open(ui_state_path, mode="w", encoding="utf-8") as f:
            json.dump({
                "handle_pos": [saved_handle_pos[0], saved_handle_pos[1]] if saved_handle_pos else None,
                "window_pos": [saved_window_pos[0], saved_window_pos[1]] if saved_window_pos else None,
                "window_size": [saved_window_size[0], saved_window_size[1]] if saved_window_size else None,
                "pin_open": hover_pin_open,
                "hover_handle_mode": hover_handle_mode,
            }, f, indent=2)
    except Exception:
        pass


def _set_saved_pair(name: str, value: tuple[float, float]):
    global saved_handle_pos, saved_window_pos, saved_window_size, layout_dirty
    if value is None:
        return
    x, y = _safe_float(value[0]), _safe_float(value[1])

    target = None
    if name == "handle":
        target = saved_handle_pos
    elif name == "window_pos":
        target = saved_window_pos
    elif name == "window_size":
        target = saved_window_size

    if target is not None:
        if abs(target[0] - x) < 0.5 and abs(target[1] - y) < 0.5:
            return

    if name == "handle":
        saved_handle_pos = (x, y)
    elif name == "window_pos":
        saved_window_pos = (x, y)
    elif name == "window_size":
        saved_window_size = (x, y)

    layout_dirty = True


def _flush_ui_state_if_dirty():
    global layout_dirty
    if not layout_dirty:
        return
    if not layout_save_timer.IsExpired():
        return
    layout_save_timer.Reset()
    _save_ui_state()
    layout_dirty = False


def _mouse_in_current_window_rect():
    try:
        io = PyImGui.get_io()
        mx = _safe_float(getattr(io, "mouse_pos_x", -1.0), -1.0)
        my = _safe_float(getattr(io, "mouse_pos_y", -1.0), -1.0)
        wx, wy = PyImGui.get_window_pos()
        ww, wh = PyImGui.get_window_size()
        return (mx >= wx) and (mx <= (wx + ww)) and (my >= wy) and (my <= (wy + wh))
    except Exception:
        return False


def _get_display_size():
    io = PyImGui.get_io()
    w = _safe_float(getattr(io, "display_size_x", 1920.0), 1920.0)
    h = _safe_float(getattr(io, "display_size_y", 1080.0), 1080.0)
    return max(320.0, w), max(240.0, h)


def _clamp_pos(x, y, w, h, margin=4.0):
    disp_w, disp_h = _get_display_size()
    max_x = max(margin, disp_w - w - margin)
    max_y = max(margin, disp_h - h - margin)
    return min(max(float(x), margin), max_x), min(max(float(y), margin), max_y)


def _clamp_size(w, h, min_w=420.0, min_h=280.0, margin=20.0):
    disp_w, disp_h = _get_display_size()
    max_w = max(min_w, disp_w - margin)
    max_h = max(min_h, disp_h - margin)
    return min(max(float(w), min_w), max_w), min(max(float(h), min_h), max_h)


def _draw_hover_handle() -> bool:
    global hover_pin_open, hover_handle_initialized

    display_w, _ = _get_display_size()

    btn_w = 48.0
    btn_h = 48.0
    win_w = btn_w + 4.0
    win_h = btn_h + 4.0
    default_x = max(8.0, (display_w * 0.5) - (btn_w * 0.5))
    default_y = 4.0

    if saved_handle_pos is None:
        _set_saved_pair("handle", (default_x, default_y))

    x, y = saved_handle_pos if saved_handle_pos is not None else (default_x, default_y)
    x, y = _clamp_pos(x, y, btn_w, btn_h)
    _set_saved_pair("handle", (x, y))
    button_rect = (x, y, btn_w, btn_h)

    PyImGui.set_next_window_pos(x, y)
    PyImGui.set_next_window_size(win_w, win_h)
    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 0.0, 0.0)
    flags = (
        PyImGui.WindowFlags.NoTitleBar |
        PyImGui.WindowFlags.NoResize |
        PyImGui.WindowFlags.NoMove |
        PyImGui.WindowFlags.NoScrollbar |
        PyImGui.WindowFlags.NoScrollWithMouse |
        PyImGui.WindowFlags.NoCollapse |
        PyImGui.WindowFlags.NoBackground
    )

    hovered = False
    if PyImGui.begin("CustomBehaviorsHandle##CustomBehaviorsHandle", flags):
        hover_handle_initialized = True
        is_hover = ImGui.is_mouse_in_rect(button_rect)
        try:
            match(ImGui.get_style().Theme):
                case Style.StyleTheme.Guild_Wars:
                    ThemeTextures.Button_Background.value.get_texture().draw_in_drawlist(
                        button_rect[:2], button_rect[2:],
                        tint=(255, 255, 255, 255) if is_hover else (200, 200, 200, 255),
                    )
                    ThemeTextures.Button_Frame.value.get_texture().draw_in_drawlist(
                        button_rect[:2], button_rect[2:],
                        tint=(255, 255, 255, 255) if is_hover else (200, 200, 200, 255),
                    )
                case _:
                    PyImGui.draw_list_add_rect_filled(
                        button_rect[0] + 1, button_rect[1] + 1,
                        button_rect[0] + button_rect[2] - 1, button_rect[1] + button_rect[3] - 1,
                        Utils.RGBToColor(51, 76, 102, 255) if is_hover else Utils.RGBToColor(26, 38, 51, 255),
                        4, 0
                    )
                    PyImGui.draw_list_add_rect(
                        button_rect[0] + 1, button_rect[1] + 1,
                        button_rect[0] + button_rect[2] - 1, button_rect[1] + button_rect[3] - 1,
                        Utils.RGBToColor(204, 204, 212, 50), 4, 0, 1
                    )
        except Exception:
            pass

        frame_col = Utils.RGBToColor(76, 235, 89, 255) if hover_pin_open else Utils.RGBToColor(242, 71, 56, 255)
        PyImGui.draw_list_add_rect(
            button_rect[0] + 1, button_rect[1] + 1,
            button_rect[0] + button_rect[2] - 1, button_rect[1] + button_rect[3] - 1,
            frame_col, 4, 0, 3
        )

        icon_rect = (button_rect[0] + 8, button_rect[1] + 6, 32, 32)
        if os.path.exists(handle_icon_path):
            ImGui.DrawTextureInDrawList(icon_rect[:2], icon_rect[2:], handle_icon_path, tint=(255, 255, 255, 255) if is_hover else (210, 210, 210, 255))

        if PyImGui.invisible_button("##CustomBehaviorsHandleBtn", button_rect[2], button_rect[3]):
            hover_pin_open = not hover_pin_open
        elif PyImGui.is_item_active():
            delta = PyImGui.get_mouse_drag_delta(0, 0.0)
            PyImGui.reset_mouse_drag_delta(0)
            nx, ny = _clamp_pos(x + delta[0], y + delta[1], btn_w, btn_h)
            _set_saved_pair("handle", (nx, ny))

        if PyImGui.is_item_hovered():
            tip = "Custom Behaviors (click to pin)" if not hover_pin_open else "Custom Behaviors (click to unpin)"
            ImGui.show_tooltip(tip)

        hovered = ImGui.is_mouse_in_rect(button_rect)
    PyImGui.end()
    PyImGui.pop_style_var(1)
    return hovered


_load_ui_state()

def gui():
    # PyImGui.set_next_window_size(260, 650)
    # PyImGui.set_next_window_size(460, 800)

    global party_forced_state_combo, monitor, widget_window_size, widget_window_pos, widget_window_initialized
    
    # window_module:ImGui.WindowModule = ImGui.WindowModule("Custom behaviors", window_name="Custom behaviors - Multiboxing over utility-ai algorithm.", window_size=(0, 600), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)

    if not widget_window_initialized:
        if saved_window_pos is not None:
            sw, sh = saved_window_size if saved_window_size is not None else (640.0, 420.0)
            sw, sh = _clamp_size(sw, sh)
            px, py = _clamp_pos(saved_window_pos[0], saved_window_pos[1], sw, sh)
            PyImGui.set_next_window_pos(px, py)
        if saved_window_size is not None:
            sw, sh = _clamp_size(saved_window_size[0], saved_window_size[1])
            PyImGui.set_next_window_size(sw, sh)

    hovered = False
    if PyImGui.begin(WIDGET_TITLE, PyImGui.WindowFlags.NoFlag):
        widget_window_initialized = True
        widget_window_size = PyImGui.get_window_size()
        widget_window_pos = PyImGui.get_window_pos()
        _set_saved_pair("window_pos", widget_window_pos)
        _set_saved_pair("window_size", widget_window_size)
        hovered = _mouse_in_current_window_rect() or PyImGui.is_window_hovered()

        PyImGui.begin_tab_bar("tabs")
        if PyImGui.begin_tab_item("party"):
            party()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("player"):
            current_build_render()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("waypoint builder / auto_mover"):
            auto_mover()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("teambuild"):
            teambuild()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("botting"):
            botting()
            PyImGui.end_tab_item()

        if PyImGui.begin_tab_item("debug"):
                
                PyImGui.text(f"{monitor.fps_stats()[1]}")
                PyImGui.text(f"{monitor.frame_stats()[1]}")
                constants.DEBUG = PyImGui.checkbox("with debugging logs", constants.DEBUG)
                
                PyImGui.begin_tab_bar("debug_tab_bar")
                
                if PyImGui.begin_tab_item("debug_execution"):
                    debug_execution()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("debug_sharedlock"):
                    debug_sharedlocks()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("debug_eventbus"):
                    debug_eventbus()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("debug_loader"):
                    PyImGui.text(f"History (newest on top) : ")
                    debug_skilbars()
                    PyImGui.end_tab_item()

                if PyImGui.begin_tab_item("debug_profiler"):
                    debug_eval_profiler()
                    PyImGui.end_tab_item()

                PyImGui.end_tab_bar()

        PyImGui.end_tab_bar()
    PyImGui.end()
    return hovered

previous_map_status = False
map_change_throttler = ThrottledTimer(1_500)

def main():
    global previous_map_status, monitor, widget_window_size, widget_window_pos, hover_is_visible, hover_hide_deadline

    monitor.tick()
    widget_monitor.act()

    if Routines.Checks.Map.MapValid() and previous_map_status == False:
        map_change_throttler.Reset()
        if constants.DEBUG: print("map changed detected - we will throttle.")

    previous_map_status = Routines.Checks.Map.MapValid()
    
    if not Routines.Checks.Map.MapValid():
        return
    
    if not map_change_throttler.IsExpired():
        if constants.DEBUG: print("map changed - throttling.")

    if map_change_throttler.IsExpired():
        show_ui = not UIManager.IsWorldMapShowing() and not Map.IsInCinematic() and not Map.Pregame.InCharacterSelectScreen() and Py4GW.Console.is_window_active()
        if show_ui:
            now = time.time()
            handle_hovered = False
            main_hovered = False

            if hover_handle_mode:
                handle_hovered = _draw_hover_handle()
                if handle_hovered:
                    hover_is_visible = True
                    hover_hide_deadline = now + hover_hide_delay_s
                if hover_pin_open:
                    hover_is_visible = True

                if hover_is_visible or hover_pin_open:
                    main_hovered = bool(gui())
            else:
                hover_is_visible = True
                main_hovered = bool(gui())

            if hover_handle_mode:
                if main_hovered:
                    hover_is_visible = True
                    hover_hide_deadline = now + hover_hide_delay_s
                if not hover_pin_open and not handle_hovered and not main_hovered and now >= hover_hide_deadline:
                    hover_is_visible = False

            _flush_ui_state_if_dirty()

        daemon()

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Custom Behaviors: Utility AI", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("A specialized combat engine that utilizes Utility AI (Scoring)")
    PyImGui.text("logic rather than fixed trees. This system evaluates the current")
    PyImGui.text("game state to choose the most mathematically optimal action.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Utility Scoring: Dynamically weights skills and behaviors based on priority")
    PyImGui.bullet_text("Advanced Party Sync: Real-time coordination via Shared Memory (SMM)")
    PyImGui.bullet_text("Behavior Injection: Modular system for custom skill and party routines")
    PyImGui.bullet_text("Diagnostic Suite: Integrated FPS monitoring and Skillbar debugging")
    PyImGui.bullet_text("Automated Handling: Built-in NPC interaction and loot management")
    PyImGui.bullet_text("Event Bus Architecture: Decoupled communication for reactive combat states")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Oazix")

    PyImGui.end_tooltip()

__all__ = ["main"]
