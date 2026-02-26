import Py4GW
import PyImGui
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler, WidgetHandler, Widget
from Py4GWCoreLib import UIManager, Map, Style, ThemeTextures, Utils
import os
import time

module_name = "Widget Manager"
      
#region UI
from Sources.oazix.CustomBehaviors import start_drop_viewer

def draw_window():
    global INI_KEY
    
    # Auto-run drop viewer
    start_drop_viewer.draw_window()
    
    if ImGui.Begin(INI_KEY,MODULE_NAME, flags=PyImGui.WindowFlags.AlwaysAutoResize):
        
        val = bool(IniManager().get(key= INI_KEY, var_name="enable_all", default=False, section="Configuration"))
        new_val = PyImGui.checkbox("Enable All Widgets", val)
        if new_val != val:
            IniManager().set(key=INI_KEY, var_name="enable_all", value=new_val, section="Configuration")
            IniManager().save_vars(INI_KEY)

    ImGui.End(INI_KEY)

def configure():
    pass
    
#region Main
# ------------------------------------------------------------
# Config
# ------------------------------------------------------------
widget_manager = get_widget_handler()

MODULE_NAME = "Widget Template"

INI_KEY = ""
INI_PATH = "Widgets/WidgetManager"
INI_FILENAME = "WidgetManager.ini"
HANDLE_SECTION = "WidgetManagerHandle"
WINDOW_SECTION = "WidgetManagerWindow"
HANDLE_ICON_PATH = os.path.join("Widgets", "Assets", "WidgetManager", "cog.jpg")

wm_handle_x = 40.0
wm_handle_y = 40.0
wm_handle_pin = False
wm_hover_mode = True
wm_handle_visible = True
wm_hide_delay_s = 0.35
wm_hide_deadline = 0.0
wm_layout_last_save = 0.0
wm_layout_save_interval_s = 0.7
wm_window_initialized = False

def _add_config_vars():
    global INI_KEY
    IniManager().add_bool(key=INI_KEY, var_name="enable_all", section="Configuration", name="enable_all", default=True)
    IniManager().add_float(key=INI_KEY, var_name="wm_handle_x", section=HANDLE_SECTION, name="x", default=40.0)
    IniManager().add_float(key=INI_KEY, var_name="wm_handle_y", section=HANDLE_SECTION, name="y", default=40.0)
    IniManager().add_bool(key=INI_KEY, var_name="wm_handle_pin", section=HANDLE_SECTION, name="pin", default=False)
    IniManager().add_bool(key=INI_KEY, var_name="wm_hover_mode", section=HANDLE_SECTION, name="hover_mode", default=True)
    IniManager().add_float(key=INI_KEY, var_name="wm_window_x", section=WINDOW_SECTION, name="x", default=100.0)
    IniManager().add_float(key=INI_KEY, var_name="wm_window_y", section=WINDOW_SECTION, name="y", default=100.0)
    IniManager().add_float(key=INI_KEY, var_name="wm_window_w", section=WINDOW_SECTION, name="w", default=520.0)
    IniManager().add_float(key=INI_KEY, var_name="wm_window_h", section=WINDOW_SECTION, name="h", default=380.0)
    
    for cv in widget_manager.config_vars:
        # Match the suffix to determine the 'name' inside the INI file
        ini_key_name = "enabled" if cv.var_name.endswith("__enabled") else "optional"

        IniManager().add_bool(
            key=INI_KEY,
            section=cv.section,
            var_name=cv.var_name,
            name=ini_key_name,
            default=False
        )

def _mouse_in_window_rect() -> bool:
    try:
        io = PyImGui.get_io()
        mx = float(getattr(io, "mouse_pos_x", -1.0))
        my = float(getattr(io, "mouse_pos_y", -1.0))
        wx, wy = PyImGui.get_window_pos()
        ww, wh = PyImGui.get_window_size()
        return (mx >= wx) and (mx <= (wx + ww)) and (my >= wy) and (my <= (wy + wh))
    except Exception:
        return False

def _get_display_size():
    io = PyImGui.get_io()
    w = float(getattr(io, "display_size_x", 1920.0) or 1920.0)
    h = float(getattr(io, "display_size_y", 1080.0) or 1080.0)
    return max(320.0, w), max(240.0, h)

def _clamp_pos(x, y, w, h, margin=4.0):
    sw, sh = _get_display_size()
    max_x = max(margin, sw - w - margin)
    max_y = max(margin, sh - h - margin)
    return min(max(float(x), margin), max_x), min(max(float(y), margin), max_y)

def _clamp_size(w, h, min_w=360.0, min_h=240.0, margin=20.0):
    sw, sh = _get_display_size()
    max_w = max(min_w, sw - margin)
    max_h = max(min_h, sh - margin)
    return min(max(float(w), min_w), max_w), min(max(float(h), min_h), max_h)

def _draw_themed_button(button_rect):
    hovered = ImGui.is_mouse_in_rect(button_rect)
    try:
        match(ImGui.get_style().Theme):
            case Style.StyleTheme.Guild_Wars:
                ThemeTextures.Button_Background.value.get_texture().draw_in_drawlist(
                    button_rect[:2], button_rect[2:],
                    tint=(255, 255, 255, 255) if hovered else (200, 200, 200, 255),
                )
                ThemeTextures.Button_Frame.value.get_texture().draw_in_drawlist(
                    button_rect[:2], button_rect[2:],
                    tint=(255, 255, 255, 255) if hovered else (200, 200, 200, 255),
                )
            case _:
                PyImGui.draw_list_add_rect_filled(
                    button_rect[0] + 1, button_rect[1] + 1,
                    button_rect[0] + button_rect[2] - 1, button_rect[1] + button_rect[3] - 1,
                    Utils.RGBToColor(51, 76, 102, 255) if hovered else Utils.RGBToColor(26, 38, 51, 255),
                    4, 0
                )
                PyImGui.draw_list_add_rect(
                    button_rect[0] + 1, button_rect[1] + 1,
                    button_rect[0] + button_rect[2] - 1, button_rect[1] + button_rect[3] - 1,
                    Utils.RGBToColor(204, 204, 212, 50), 4, 0, 1
                )
    except Exception:
        pass

def _draw_widget_manager_handle() -> bool:
    global wm_handle_x, wm_handle_y, wm_handle_pin

    btn_w, btn_h = 48.0, 48.0
    wm_handle_x, wm_handle_y = _clamp_pos(wm_handle_x, wm_handle_y, btn_w, btn_h)
    button_rect = (wm_handle_x, wm_handle_y, btn_w, btn_h)

    PyImGui.set_next_window_pos(wm_handle_x, wm_handle_y)
    PyImGui.set_next_window_size(btn_w + 4.0, btn_h + 4.0)
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
    if PyImGui.begin("##WidgetManagerHandle", flags):
        _draw_themed_button(button_rect)

        frame_col = Utils.RGBToColor(76, 235, 89, 255) if wm_handle_pin else Utils.RGBToColor(242, 71, 56, 255)
        PyImGui.draw_list_add_rect(
            button_rect[0] + 1, button_rect[1] + 1,
            button_rect[0] + button_rect[2] - 1, button_rect[1] + button_rect[3] - 1,
            frame_col, 4, 0, 3
        )

        is_hover = ImGui.is_mouse_in_rect(button_rect)
        icon_rect = (button_rect[0] + 8, button_rect[1] + 6, 32, 32)
        if os.path.exists(HANDLE_ICON_PATH):
            ImGui.DrawTextureInDrawList(
                icon_rect[:2], icon_rect[2:], HANDLE_ICON_PATH,
                tint=(255, 255, 255, 255) if is_hover else (210, 210, 210, 255),
            )

        if PyImGui.invisible_button("##WidgetManagerHandleBtn", btn_w, btn_h):
            wm_handle_pin = not wm_handle_pin
        elif PyImGui.is_item_active():
            delta = PyImGui.get_mouse_drag_delta(0, 0.0)
            PyImGui.reset_mouse_drag_delta(0)
            wm_handle_x += delta[0]
            wm_handle_y += delta[1]
            wm_handle_x, wm_handle_y = _clamp_pos(wm_handle_x, wm_handle_y, btn_w, btn_h)

        hovered = ImGui.is_mouse_in_rect(button_rect)
        if PyImGui.is_item_hovered():
            tip = "Widget Manager (click to pin)" if not wm_handle_pin else "Widget Manager (click to unpin)"
            ImGui.show_tooltip(tip)

    PyImGui.end()
    PyImGui.pop_style_var(1)
    return hovered
        
def update():
    #return #deprecated in place of callbacks
    if widget_manager.enable_all:
        widget_manager.execute_enabled_widgets_update()
    
def draw():
    return #deprecated in place of callbacks
    if widget_manager.enable_all:
        widget_manager.execute_enabled_widgets_draw()     
        
widget_manager_initialized = False
widget_manager_initializing = False

def main():
    global INI_KEY, widget_manager_initialized, widget_manager_initializing
    global wm_handle_x, wm_handle_y, wm_handle_pin, wm_hover_mode
    global wm_handle_visible, wm_hide_deadline, wm_layout_last_save, wm_window_initialized

    if not INI_KEY:
        if not os.path.exists(INI_PATH):
            os.makedirs(INI_PATH, exist_ok=True)

        INI_KEY = IniManager().ensure_global_key(
            INI_PATH,
            INI_FILENAME
        )
        
        if not INI_KEY: return
        
        widget_manager.MANAGER_INI_KEY = INI_KEY
        
        widget_manager.discover()
        _add_config_vars()
        IniManager().load_once(INI_KEY)

        # FIX 1: Explicitly load the global manager state into the handler
        widget_manager.enable_all = bool(IniManager().get(key=INI_KEY, var_name="enable_all", default=False, section="Configuration"))
        wm_handle_x = float(IniManager().getFloat(key=INI_KEY, var_name="wm_handle_x", default=40.0, section=HANDLE_SECTION))
        wm_handle_y = float(IniManager().getFloat(key=INI_KEY, var_name="wm_handle_y", default=40.0, section=HANDLE_SECTION))
        wm_handle_pin = bool(IniManager().getBool(key=INI_KEY, var_name="wm_handle_pin", default=False, section=HANDLE_SECTION))
        wm_hover_mode = bool(IniManager().getBool(key=INI_KEY, var_name="wm_hover_mode", default=True, section=HANDLE_SECTION))
        wm_window_initialized = False
        widget_manager._apply_ini_configuration()
            
    show_ui = not UIManager.IsWorldMapShowing() and not Map.IsInCinematic() and not Map.Pregame.InCharacterSelectScreen()

    handle_hovered = False
    main_hovered = False
    now = time.time()

    if INI_KEY and show_ui:
        if wm_hover_mode:
            handle_hovered = _draw_widget_manager_handle()
            if handle_hovered:
                wm_handle_visible = True
                wm_hide_deadline = now + wm_hide_delay_s
            if wm_handle_pin:
                wm_handle_visible = True
        else:
            wm_handle_visible = True

        if wm_handle_visible or wm_handle_pin or not wm_hover_mode:
            if not wm_window_initialized:
                wx = float(IniManager().getFloat(key=INI_KEY, var_name="wm_window_x", default=100.0, section=WINDOW_SECTION))
                wy = float(IniManager().getFloat(key=INI_KEY, var_name="wm_window_y", default=100.0, section=WINDOW_SECTION))
                ww = float(IniManager().getFloat(key=INI_KEY, var_name="wm_window_w", default=520.0, section=WINDOW_SECTION))
                wh = float(IniManager().getFloat(key=INI_KEY, var_name="wm_window_h", default=380.0, section=WINDOW_SECTION))
                ww, wh = _clamp_size(ww, wh)
                wx, wy = _clamp_pos(wx, wy, ww, wh)
                PyImGui.set_next_window_pos(wx, wy)
                PyImGui.set_next_window_size(ww, wh)
            if ImGui.Begin(ini_key=INI_KEY, name="Widget Manager", flags=PyImGui.WindowFlags.NoFlag):
                wm_window_initialized = True
                widget_manager.draw_ui(INI_KEY)
                main_hovered = _mouse_in_window_rect() or PyImGui.is_window_hovered()
                try:
                    wpos = PyImGui.get_window_pos()
                    wsize = PyImGui.get_window_size()
                    IniManager().set(INI_KEY, "wm_window_x", float(wpos[0]), WINDOW_SECTION)
                    IniManager().set(INI_KEY, "wm_window_y", float(wpos[1]), WINDOW_SECTION)
                    IniManager().set(INI_KEY, "wm_window_w", float(wsize[0]), WINDOW_SECTION)
                    IniManager().set(INI_KEY, "wm_window_h", float(wsize[1]), WINDOW_SECTION)
                except Exception:
                    pass
            ImGui.End(INI_KEY)

        if wm_hover_mode:
            if main_hovered:
                wm_handle_visible = True
                wm_hide_deadline = now + wm_hide_delay_s
            if not wm_handle_pin and not handle_hovered and not main_hovered and now >= wm_hide_deadline:
                wm_handle_visible = False

        # Persist handle state and mode.
        IniManager().set(INI_KEY, "wm_handle_x", float(wm_handle_x), HANDLE_SECTION)
        IniManager().set(INI_KEY, "wm_handle_y", float(wm_handle_y), HANDLE_SECTION)
        IniManager().set(INI_KEY, "wm_handle_pin", bool(wm_handle_pin), HANDLE_SECTION)
        IniManager().set(INI_KEY, "wm_hover_mode", bool(wm_hover_mode), HANDLE_SECTION)
        if now - wm_layout_last_save >= wm_layout_save_interval_s:
            IniManager().save_vars(INI_KEY)
            wm_layout_last_save = now
    
    if widget_manager.enable_all:
        #deprecated in place of callbacks
        #widget_manager.execute_enabled_widgets_main()
        widget_manager.execute_configuring_widgets()


if __name__ == "__main__":
    main()
