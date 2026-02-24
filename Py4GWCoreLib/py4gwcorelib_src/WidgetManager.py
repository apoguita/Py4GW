from enum import IntEnum
from typing import Callable
from types import ModuleType
import traceback
import Py4GW
import PyImGui
from Py4GWCoreLib.HotkeyManager import HOTKEY_MANAGER, HotKey
from Py4GWCoreLib.ImGui_src.Style import Style
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.enums_src.IO_enums import Key, ModifierKey
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
import importlib.util
import os
import sys
import PyImGui
import PyCallback
from dataclasses import dataclass, field
from types import ModuleType
from typing import Callable, Optional

from Py4GWCoreLib.py4gwcorelib_src.Color import Color

_profiling_registry = None

def _get_profiling():
    global _profiling_registry
    if _profiling_registry is None:
        from Py4GWCoreLib.py4gwcorelib_src.Profiling import ProfilingRegistry
        _profiling_registry = ProfilingRegistry()
    return _profiling_registry

#region Py4GW Library
class LayoutMode(IntEnum):
    Library = 0
    Compact = 1
    Minimalistic = 2
    SingleButton = 3
    
    LastView = 100
    
class SortMode(IntEnum):
    ByName = 0
    ByCategory = 1
    ByStatus = 2
    
class ViewMode(IntEnum):
    All = 0
    Favorites = 1
    Actives = 2
    Inactives = 3
    
class WidgetTreeNode:
    def __init__(
        self,
        name: str = "",
        depth: int = 0,
        parent: "WidgetTreeNode | None" = None,
    ):
        self.name: str = name
        self.depth: int = depth
        self.parent: WidgetTreeNode | None = parent

        # full path (stable, precomputed)
        if parent and parent.path:
            self.path: str = f"{parent.path}/{name}"
        elif parent:
            self.path: str = name
        else:
            self.path: str = ""

        # hierarchy
        self.children: dict[str, WidgetTreeNode] = {}
        self.widgets: list[str] = []

    def get_child(self, name: str) -> "WidgetTreeNode":
        if name not in self.children:
            self.children[name] = WidgetTreeNode(
                name=name,
                depth=self.depth + 1,
                parent=self
            )
        return self.children[name]
                    
class Py4GWLibrary:
    CATEGORY_COLUMN_MAX_WIDTH = 200
    SYSTEM_COLOR = Color(255, 0, 0, 255)
    TEXT_TINTED = Color(128, 128, 128, 255)
    IMAGE_SIZE = 40
    PADDING = 10
    TAG_HEIGHT = 18
    BUTTON_HEIGHT = 24
    CONFIRMATION_MODAL_ID = "This is a critical widget!##ConfirmDisableSystemWidget"
    
    def __init__(self, ini_key: str, module_name: str, widget_manager : "WidgetHandler"):
        self.ini_key = ini_key
        self.module_name = module_name
        self.widget_manager = widget_manager
        self.widget_filter = ""
        
        self.view_mode = ViewMode.All
        self.layout_mode = LayoutMode.Library
        self.previous_mode = self.layout_mode
        self.sort_mode = SortMode.ByName
        
        self.filtered_widgets : list[Widget] = []
        self.favorites : list[Widget] = []
                
        self.category : str = ""
        # get unique categories sorted alphabetically
        self.categories : list[str] = sorted(set(widget.category for widget in self.widget_manager.widgets.values() if widget.category))
        
        self.path : str = ""
        self.tag : str = ""
        self.tags : list[str] = sorted(set(tag for widget in self.widget_manager.widgets.values() for tag in widget.tags if widget.tags))
        
        self._pending_disable_widget : "Widget | None" = None
        self._request_disable_popup = False 
        
        self.win_size : Optional[tuple[float, float]] = None
        self.previous_size : Optional[tuple[float, float]] = None
        self.ui_active = False
        
        self.queue_filter_widgets = False
        self.focus_search = False
        self.popup_opened = False
        
        self.context_menu_widget = None
        self.context_menu_id = ""
        
        self.active_card_style_pushed = False
        
        self.startup_layout = LayoutMode.LastView
        self.show_configure_button = True
        self.show_images = True
        self.show_separator = True
        self.show_category = True
        self.show_tags = True
        self.single_filter = True
        self.fixed_card_width = False
        self.card_width = 300
        
        self.card_enabled_color = Color(90, 255, 90, 30)
        self.card_color = Color(200, 200, 200, 20)
        self.favorites_color = Color(255, 215, 0, 255)
        self.tag_color = Color(38, 51, 59, 255)
        self.category_color = Color(150, 150, 150, 255)
        self.name_color = Color(255, 255, 255, 255)
        self.name_enabled_color = Color(150, 255, 150, 255)
        self.card_rounding = 4.0
        self.max_suggestions = 10
        self.single_button_size = 48
        self.jump_to_minimalistic = True
        
        self.focus_keybind : HotKey = HOTKEY_MANAGER.register_hotkey(
            key=Key.Unmapped,
            modifiers=ModifierKey.NoneKey,
            callback=self.set_search_focus,
            identifier="Py4GWLibrary_focus_search",
            name="Focus Search",
        )
            
        self.load_config()
        self.filter_widgets("")
        self.first_run = True
        self.folder_tree = self.build_widget_tree(self.widget_manager.widgets)
    
    def load_config(self):
        
        try:
            self.max_suggestions = IniManager().read_int(key=self.ini_key, section="Configuration", name="max_suggestions", default=10)
            self.single_button_size = IniManager().read_int(key=self.ini_key, section="Configuration", name="single_button_size", default=48)
            
            self.jump_to_minimalistic = IniManager().read_bool(key=self.ini_key, section="Configuration", name="jump_to_minimalistic", default=False)
            self.single_filter = IniManager().read_bool(key=self.ini_key, section="Configuration", name="single_filter", default=True)
            self.startup_layout = LayoutMode[IniManager().read_key(key=self.ini_key, section="Configuration", name="startup_layout", default=LayoutMode.LastView.name)]
            
            x = IniManager().read_float(key=self.ini_key, section="Configuration", name="library_width", default=900)
            y = IniManager().read_float(key=self.ini_key, section="Configuration", name="library_height", default=600)
            self.previous_size = (x, y)
            
            layout = LayoutMode[IniManager().read_key(key=self.ini_key, section="Configuration", name="layout", default=LayoutMode.Library.name)] if self.startup_layout is LayoutMode.LastView else self.startup_layout
            self.set_layout_mode(layout)
            
            self.show_configure_button = IniManager().read_bool(key=self.ini_key, section="Card Configuration", name="show_configure_button", default=True)
            self.show_images = IniManager().read_bool(key=self.ini_key, section="Card Configuration", name="show_images", default=True)
            self.show_separator = IniManager().read_bool(key=self.ini_key, section="Card Configuration", name="show_separator", default=True)
            self.show_category = IniManager().read_bool(key=self.ini_key, section="Card Configuration", name="show_category", default=True)
            self.show_tags = IniManager().read_bool(key=self.ini_key, section="Card Configuration", name="show_tags", default=True)
            self.fixed_card_width = IniManager().read_bool(key=self.ini_key, section="Card Configuration", name="fixed_card_width", default=False)
            self.card_width = IniManager().read_float(key=self.ini_key, section="Card Configuration", name="card_width", default=300)            
            
            self.card_enabled_color = Color.from_rgba_string(IniManager().read_key(key=self.ini_key, section="Card Configuration", name="card_enabled_color", default="90, 255, 90, 30"))
            self.card_color = Color.from_rgba_string(IniManager().read_key(key=self.ini_key, section="Card Configuration", name="card_color", default="200, 200, 200, 20"))
            self.favorites_color = Color.from_rgba_string(IniManager().read_key(key=self.ini_key, section="Card Configuration", name="favorites_color", default="255, 215, 0, 255"))
            self.tag_color = Color.from_rgba_string(IniManager().read_key(key=self.ini_key, section="Card Configuration", name="tag_color", default="38, 51, 59, 255"))
            self.category_color = Color.from_rgba_string(IniManager().read_key(key=self.ini_key, section="Card Configuration", name="category_color", default="150, 150, 150, 255"))
            self.name_color = Color.from_rgba_string(IniManager().read_key(key=self.ini_key, section="Card Configuration", name="name_color", default="255, 255, 255, 255"))
            self.name_enabled_color = Color.from_rgba_string(IniManager().read_key(key=self.ini_key, section="Card Configuration", name="name_enabled_color", default="150, 255, 150, 255"))
            self.card_rounding = IniManager().read_float(key=self.ini_key, section="Card Configuration", name="card_rounding", default=4.0)
            
            self.favorites.clear()            
            favs = IniManager().read_key(key=self.ini_key, section="Favorites", name="favorites", default="").split(",")
            for fav in favs:
                widget = self.widget_manager.widgets.get(fav)
                
                if widget:
                    self.favorites.append(widget)
                    
            hotkeykey = IniManager().read_key(self.ini_key, section="Configuration", name="hotkey", default="Unmapped")
            modifiers = IniManager().read_key(self.ini_key, section="Configuration", name="hotkey_modifiers", default="NoneKey")
            register_hotkey = False
            
            try:
                self.focus_keybind.key = Key[hotkeykey]
                register_hotkey = True
                
            except KeyError:
                pass
                
            try:
                self.focus_keybind.modifiers = ModifierKey[modifiers]
                register_hotkey = register_hotkey and True
                
            except KeyError:
                pass
                
                           
        
        except Exception as e:
            Py4GW.Console.Log("Widget Browser", f"Error loading config: {e}", Py4GW.Console.MessageType.Error)
            
        pass    
    
    def build_widget_tree(self, widgets: dict[str, "Widget"]) -> WidgetTreeNode:
        root = WidgetTreeNode(name="", depth=0, parent=None)

        for _, widget in widgets.items():
            node = root

            if widget.widget_path:
                for part in widget.widget_path.split("/"):
                    node = node.get_child(part)

        return root

    def add_to_favorites(self, widget : "Widget"):
        if widget not in self.favorites:
            self.favorites.append(widget)
            IniManager().set(key=self.ini_key, var_name="favorites", value=",".join(w.folder_script_name for w in self.favorites), section="Favorites")
            IniManager().save_vars(self.ini_key)
            
    def remove_from_favorites(self, widget : "Widget"):
        if widget in self.favorites:
            self.favorites.remove(widget)
            IniManager().set(key=self.ini_key, var_name="favorites", value=",".join(w.folder_script_name for w in self.favorites), section="Favorites")
            IniManager().save_vars(self.ini_key)
    
    def set_layout_mode(self, mode : LayoutMode):
        match mode:
            case LayoutMode.Library:                
                self.win_size = self.previous_size or (900, 600)
            case LayoutMode.Compact:
                self.focus_search = True
                self.win_size = (300, 80)
            case LayoutMode.Minimalistic:
                self.win_size = (200, 45)
            case LayoutMode.SingleButton:
                self.win_size = (self.single_button_size, self.single_button_size)
                self.previous_mode = self.layout_mode
                
        self.layout_mode = mode
        IniManager().set(key=self.ini_key, section="Configuration", var_name="layout", value=mode.name)
        self.queue_filter_widgets = True
        pass

    def set_search_focus(self):
        match self.layout_mode:
            case LayoutMode.SingleButton:
                self.set_layout_mode(LayoutMode.Library if self.previous_mode is LayoutMode.Library else LayoutMode.Compact)
                self.focus_search = True
                
            case LayoutMode.Library:
                self.focus_search = True
                
            case LayoutMode.Compact | LayoutMode.Minimalistic:
                self.focus_search = True
                self.set_layout_mode(LayoutMode.Compact)

    def draw_search_tooltip(self):
        if PyImGui.is_item_hovered():
            PyImGui.begin_tooltip()
            ImGui.text("Search widgets by name, folder, category or tags. Use ';' to separate multiple keywords.")            
            ImGui.text("Special keywords:")
            ImGui.bullet_text("#enabled / #active / #on - Show only enabled widgets")
            ImGui.bullet_text("#disabled / #inactive / #off - Show only disabled widgets")
            ImGui.bullet_text("#favorites / #favs / #fav - Show only favorite widgets")
            ImGui.bullet_text("#system / #sys - Show only widgets in the 'System' category")
            
            PyImGui.separator()
            
            ImGui.text_colored("Press " + self.focus_keybind.format_hotkey() + " to focus.", self.TEXT_TINTED.color_tuple)
            PyImGui.end_tooltip()



    def draw_window(self): 
        win_size = self.win_size
        
        if self.queue_filter_widgets:
            self.filter_widgets(self.widget_filter)
            self.queue_filter_widgets = False
        
        match self.layout_mode:
            case LayoutMode.Library:
                self.draw_libary_view()
            case LayoutMode.Compact:
                self.draw_compact_view()  
            case LayoutMode.Minimalistic:
                self.draw_minimalistic_view()
            case LayoutMode.SingleButton:
                self.draw_one_button_view()

        if self.first_run:    
            self.win_size = win_size                    
            self.first_run = False
            
    def filter_widgets(self, filter_text: str):        
        self.filtered_widgets.clear()     
        prefiltered = list(self.widget_manager.widgets.values()).copy()
        
        keywords = [kw.strip().lower() for kw in filter_text.lower().strip().split(";")]
        
        preset_words : dict[str, list[str]]= {
            "enabled": ["#enabled", "#active", "#on"],
            "disabled": ["#disabled", "#inactive", "#off"],
            "favorites": ["#favorites", "#favs", "#fav"],
            "system": ["#system", "#sys"]
        }
        
        enabled_check = False
        disabled_check = False
        favorites_check = False
        system_check = False
        
        for kw in list(keywords):            
            enabled_check = enabled_check or any(kw == preset_kw for preset_kw in preset_words["enabled"])
            disabled_check = disabled_check or any(kw == preset_kw for preset_kw in preset_words["disabled"])
            favorites_check = favorites_check or any(kw == preset_kw for preset_kw in preset_words["favorites"])
            system_check = system_check or any(kw == preset_kw for preset_kw in preset_words["system"])
            
            prefiltered = [w for w in prefiltered if 
                            (not enabled_check or w.enabled) and
                            (not disabled_check or not w.enabled) and
                            (not favorites_check or w in self.favorites) and
                            (not system_check or w.category == "System")]
            
            for preset, preset_keywords in preset_words.items():
                if kw in preset_keywords:
                    keywords.remove(kw)
            
        
        match self.layout_mode:
            case LayoutMode.Library:
                match self.view_mode:
                    case ViewMode.Favorites:
                        prefiltered = [w for w in prefiltered if w in self.favorites]
                        
                    case ViewMode.Actives:
                        prefiltered = [w for w in list(self.widget_manager.widgets.values()) if w.enabled]
                        
                    case ViewMode.Inactives:
                        prefiltered = [w for w in list(self.widget_manager.widgets.values()) if not w.enabled]
                
                self.filtered_widgets = [w for w in prefiltered if 
                                        (w.category == self.category or not self.category) and 
                                        (self.path in w.widget_path or not self.path) and 
                                        (self.tag in w.tags or not self.tag) and 
                                        all(kw in w.plain_name.lower() or kw in w.folder.lower() for kw in keywords if keywords and kw)]
                
                match self.sort_mode:
                    case SortMode.ByName:
                        self.filtered_widgets.sort(key=lambda w: w.name.lower())
                    case SortMode.ByCategory:
                        self.filtered_widgets.sort(key=lambda w: (w.category.lower() if w.category else "", w.name.lower()))
                    case SortMode.ByStatus:
                        self.filtered_widgets.sort(key=lambda w: (not w.enabled, w.name.lower()))
            case LayoutMode.Compact:
                # check if all keywords are in name or folder
                self.filtered_widgets = [w for w in prefiltered if all(kw in w.plain_name.lower() or kw in w.folder.lower() for kw in keywords if keywords and kw)]

    def draw_toggle_view_mode_button(self) -> bool:
        clicked = False
        hovered = False
        
        match self.layout_mode:
            case LayoutMode.Library:
                if ImGui.icon_button(IconsFontAwesome5.ICON_BARS, 28, 24):
                    self.set_layout_mode(LayoutMode.Compact)
                    clicked = True
                
                hovered = PyImGui.is_item_hovered()
                ImGui.show_tooltip("Switch to Compact View")
                    
            case LayoutMode.Compact:
                if ImGui.icon_button(IconsFontAwesome5.ICON_TH_LIST, 28, 24):
                    self.set_layout_mode(LayoutMode.Library)
                    clicked = True
                    
                hovered = PyImGui.is_item_hovered()
                ImGui.show_tooltip("Switch to Library View")
                
        return clicked or hovered
    
    def draw_global_toggles(self, button_width : float, spacing : float, search : bool = False): 
        if ImGui.button("##one_button_layout", width=button_width):
            if self.layout_mode != LayoutMode.SingleButton:
                self.set_layout_mode(LayoutMode.SingleButton)
        
        item_min, _, item_size = ImGui.get_item_rect()
        image_size = item_size[1] - 4
        pos_x = item_min[0] + ((item_size[0] - image_size) / 2)
        pos_y = item_min[1] + ((item_size[1] - image_size) / 2)
        ImGui.DrawTextureInDrawList((pos_x, pos_y), (image_size, image_size), "python_icon_round_20px.png")
        ImGui.show_tooltip("Switch to Single Button View")        
        
        PyImGui.same_line(0, spacing)
        
        if search:
            if ImGui.icon_button(IconsFontAwesome5.ICON_SEARCH + "##FocusSearch", button_width):
                self.set_layout_mode(LayoutMode.Compact)
            
            ImGui.show_tooltip("Search widgets")
            
            PyImGui.same_line(0, spacing)      
        
        if ImGui.icon_button(IconsFontAwesome5.ICON_RETWEET + "##Reload Widgets", button_width):
            self.widget_manager.discovered = False
            self.widget_manager.discover()
            self.queue_filter_widgets = True
                
        ImGui.show_tooltip("Reload all widgets")
        PyImGui.same_line(0, spacing)
        
        new_enable_all = ImGui.toggle_icon_button(
            (IconsFontAwesome5.ICON_TOGGLE_ON if self.widget_manager.enable_all else IconsFontAwesome5.ICON_TOGGLE_OFF) + "##widget_disable",
            self.widget_manager.enable_all,
            button_width
        )

        if new_enable_all != self.widget_manager.enable_all:
            self.widget_manager.enable_all = new_enable_all
            IniManager().set(key= self.ini_key, var_name="enable_all", value=new_enable_all, section="Configuration")
            IniManager().save_vars(self.ini_key)


        ImGui.show_tooltip(f"{("Run" if not self.widget_manager.enable_all else "Pause")} all widgets")
        
        PyImGui.same_line(0, spacing)
        show_widget_ui = ImGui.toggle_icon_button((IconsFontAwesome5.ICON_EYE if self.widget_manager.show_widget_ui else IconsFontAwesome5.ICON_EYE_SLASH) + "##Show Widget UIs", self.widget_manager.show_widget_ui, button_width)
        if show_widget_ui != self.widget_manager.show_widget_ui:
            self.widget_manager.set_widget_ui_visibility(show_widget_ui)
        ImGui.show_tooltip(f"{("Show" if not self.widget_manager.show_widget_ui else "Hide")} all widget UIs")
        
        PyImGui.same_line(0, spacing)
        pause_non_env = ImGui.toggle_icon_button((IconsFontAwesome5.ICON_PAUSE if self.widget_manager.pause_optional_widgets else IconsFontAwesome5.ICON_PLAY) + "##Pause Non-Env Widgets", not self.widget_manager.pause_optional_widgets, button_width)
        if pause_non_env != (not self.widget_manager.pause_optional_widgets):
            if not self.widget_manager.pause_optional_widgets:
                self.widget_manager.pause_widgets()
            else:
                self.widget_manager.resume_widgets()
                
            own_email = Player.GetAccountEmail()
            for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
                if acc.AccountEmail == own_email:
                    continue
                
                GLOBAL_CACHE.ShMem.SendMessage(own_email, acc.AccountEmail, SharedCommandType.PauseWidgets if self.widget_manager.pause_optional_widgets else SharedCommandType.ResumeWidgets)
            
        ImGui.show_tooltip(f"{("Pause" if not self.widget_manager.pause_optional_widgets else "Resume")} all optional widgets")
    
    def get_button_width(self, width, num_buttons, spacing) -> float:        
        button_width = (width - spacing * (num_buttons - 1)) / num_buttons
        return button_width
    
    def draw_minimalistic_view(self):
        if self.win_size:
            PyImGui.set_next_window_size(self.win_size, PyImGui.ImGuiCond.Always)
        
        if self.focus_search:
            PyImGui.set_next_window_focus()
            
        if ImGui.Begin(ini_key=self.ini_key, name=self.module_name, flags=PyImGui.WindowFlags(PyImGui.WindowFlags.NoResize|PyImGui.WindowFlags.NoTitleBar|PyImGui.WindowFlags.NoScrollbar|PyImGui.WindowFlags.NoScrollWithMouse)):   
            win_size = PyImGui.get_window_size()
            self.win_size = (win_size[0], win_size[1])
            ImGui.set_window_within_displayport(*self.win_size)
            style = ImGui.get_style()
            
            spacing = 5
            width = win_size[0] - style.WindowPadding.value1 * 2
            button_width = self.get_button_width(width, 6, spacing)        
            self.draw_global_toggles(button_width, spacing, search=True)
                            
        ImGui.End(self.ini_key)
            
    def draw_presets_button(self) -> bool:
        clicked = False
        if ImGui.icon_button(IconsFontAwesome5.ICON_FILTER, 28, 24):
            clicked = True
            
            if not self.popup_opened:
                PyImGui.open_popup("PreSets##WidgetBrowser")
                self.popup_opened = True
        ImGui.show_tooltip("Filter presets")
        
        self.popup_opened = PyImGui.begin_popup("PreSets##WidgetBrowser")
        if self.popup_opened:
            if ImGui.menu_item("Show Enabled"):
                self.widget_filter = "enabled; "
                self.focus_search = True
                self.queue_filter_widgets = True
                
            if ImGui.menu_item("Show Disabled"):
                self.widget_filter = "disabled; "
                self.focus_search = True
                self.queue_filter_widgets = True
            
            if ImGui.menu_item("Show Favorites"):
                self.widget_filter = "favorites; "
                self.focus_search = True
                self.queue_filter_widgets = True
                
            if ImGui.menu_item("Show System"):
                self.widget_filter = "system; "  
                self.focus_search = True
                self.queue_filter_widgets = True
            
            PyImGui.end_popup()   
                    
        return self.popup_opened or clicked
            
    def draw_compact_view(self):
        if self.win_size:
            PyImGui.set_next_window_size(self.win_size, PyImGui.ImGuiCond.Always)
        
        if self.focus_search:
            PyImGui.set_next_window_focus()
            
        if ImGui.Begin(ini_key=self.ini_key, name=self.module_name, flags=PyImGui.WindowFlags.NoResize | PyImGui.WindowFlags.NoTitleBar):   
            window_hovered = PyImGui.is_window_hovered()
            win_size = PyImGui.get_window_size()
            self.win_size = (win_size[0], win_size[1])
            ImGui.set_window_within_displayport(*self.win_size)
            
            style = ImGui.get_style()
            width = win_size[0] - style.WindowPadding.value1 * 2
            
            spacing = 5
            button_width = self.get_button_width(width, 5, spacing)     
            self.draw_global_toggles(button_width, spacing)
            ImGui.separator()
            toggle_interacted = self.draw_toggle_view_mode_button()   
            PyImGui.same_line(0, spacing)      
            
            search_width = PyImGui.get_content_region_avail()[0] - 30
            PyImGui.push_item_width(search_width)
            changed, self.widget_filter = ImGui.search_field("##WidgetFilter", self.widget_filter)
            if changed:
                if self.single_filter:
                    self.tag = ""
                    self.category = ""
                    self.path = ""
                    
                self.queue_filter_widgets = True
            PyImGui.pop_item_width()
            search_active = PyImGui.is_item_active() or PyImGui.is_item_focused() or self.focus_search
            
            if self.focus_search:
                PyImGui.set_keyboard_focus_here(-1)
                self.focus_search = False
            
            self.draw_search_tooltip()
            PyImGui.same_line(0, spacing)
            
            presets_opened = self.draw_presets_button()      
            window_hovered = PyImGui.is_window_hovered() or PyImGui.is_item_hovered() or window_hovered 
            suggestions_opened = self.draw_suggestions(win_size, style, search_active, window_hovered, presets_opened)
            
            if not presets_opened and not suggestions_opened and not window_hovered and not PyImGui.is_window_appearing():
                clicked_outside = PyImGui.is_mouse_down(0) and not PyImGui.is_any_item_hovered()
                if not toggle_interacted and (clicked_outside or not search_active):
                    if self.jump_to_minimalistic and self.layout_mode is LayoutMode.Compact:
                        self.set_layout_mode(LayoutMode.Minimalistic)
                            
        ImGui.End(self.ini_key)

    def draw_suggestions(self, win_size, style : Style, search_active, window_hovered, presets_opened) -> bool:
        open = False
        
        if self.filtered_widgets and self.widget_filter:
            win_pos = PyImGui.get_window_pos()
                
            PyImGui.set_next_window_pos(
                    (win_pos[0], win_pos[1] + win_size[1] - style.WindowBorderSize.value1),
                    PyImGui.ImGuiCond.Always
                )

            height = min(self.max_suggestions, len(self.filtered_widgets)) * 30 + (style.ItemSpacing.value2 or 0) + (style.WindowPadding.value2 or 0) * 2
            PyImGui.set_next_window_size((win_size[0], height),
                    PyImGui.ImGuiCond.Always
                )
                
            suggestion_hovered = False
            
            if PyImGui.begin("##WidgetsList", False, PyImGui.WindowFlags(PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.NoMove | PyImGui.WindowFlags.NoResize | PyImGui.WindowFlags.NoSavedSettings | PyImGui.WindowFlags.NoFocusOnAppearing )):
                suggestion_hovered = PyImGui.is_window_hovered()
                card_width = PyImGui.get_content_region_avail()[0]
                open = True
                
                self._push_card_style(style, enabled=False)
                
                first_visible = False
                last_visible = False
                for widget in self.filtered_widgets:
                    if first_visible and last_visible:
                        ImGui.dummy(card_width, 30)
                        continue
                    
                    clicked, hovered = self.draw_compact_widget_card(widget, card_width, style) or suggestion_hovered
                    suggestion_hovered = suggestion_hovered or hovered or clicked
                    if clicked:
                        self.queue_filter_widgets = True
                        self.focus_search = True
                        
                        # ---- RIGHT CLICK DETECTION ----
                    if hovered and PyImGui.is_mouse_clicked(1):
                        self.context_menu_id = f"WidgetContext##{widget.folder_script_name}"
                        self.context_menu_widget = widget
                        PyImGui.open_popup(self.context_menu_id)
                        
                        
                if self.active_card_style_pushed:
                    self._pop_card_style(style)
                
                self._pop_card_style(style)
                
                if self.context_menu_id and self.context_menu_widget:
                    self.card_context_menu(self.context_menu_id, self.context_menu_widget)
                            
                if suggestion_hovered and not (self.context_menu_id or self.context_menu_widget) and not search_active and not self.focus_search and not presets_opened:
                    PyImGui.set_window_focus("##WidgetsList")
                
            if (
                    not PyImGui.is_window_focused()
                    and not search_active
                    and not window_hovered
                    and not suggestion_hovered
                    and not self.context_menu_id
                    and not PyImGui.is_any_item_active()
                ):
                open = False
                    
            ImGui.end()
            
        if self._request_disable_popup:
            PyImGui.open_popup(self.CONFIRMATION_MODAL_ID)
            self._request_disable_popup = False
            
        self.draw_confirmation_modal()
            
        return open
    
    def card_context_menu(self, popup_id: str, widget : "Widget"):   
                     
        if PyImGui.begin_popup(popup_id):
            if PyImGui.menu_item("Add to Favorites" if widget not in self.favorites else "Remove from Favorites"):
                if widget not in self.favorites:
                    self.add_to_favorites(widget)
                else:
                    self.remove_from_favorites(widget)
                
            PyImGui.separator()
                        
            if PyImGui.menu_item("Enable" if not widget.enabled else "Disable"):
                if not widget.enabled:
                    self.widget_manager.enable_widget(widget.plain_name)
                else:
                    if widget.category == "System":
                        self._pending_disable_widget = widget
                        self._request_disable_popup = True
                    else:
                        self.widget_manager.disable_widget(widget.plain_name)
                    
            PyImGui.separator()

            if widget.has_configure_property:
                if PyImGui.menu_item((f"Close " if widget.configuring else "") + "Configure"):
                    widget.set_configuring(not widget.configuring)

                PyImGui.separator()

            if PyImGui.menu_item("Open Widget Folder"):
                os.startfile(os.path.join(Py4GW.Console.get_projects_path(), "Widgets", widget.folder))

            if PyImGui.menu_item("Open Widget File"):
                os.startfile(os.path.join(Py4GW.Console.get_projects_path(), "Widgets", widget.folder_script_name))

            PyImGui.end_popup()
        else:
            self.context_menu_id = ""
            self.context_menu_widget = None
        
    def draw_sorting_button(self):
        if ImGui.icon_button(IconsFontAwesome5.ICON_SORT_AMOUNT_DOWN, 28, 24):
            PyImGui.open_popup("SortingPopup##WidgetBrowser")
        ImGui.show_tooltip("Sorting options")
        
        if PyImGui.begin_popup("SortingPopup##WidgetBrowser"):
            sort_mode = ImGui.radio_button("Sort by Name", self.sort_mode, SortMode.ByName)
            if self.sort_mode != sort_mode:
                self.sort_mode = SortMode.ByName
                self.filtered_widgets.sort(key=lambda w: w.name.lower())
                
            sort_mode = ImGui.radio_button("Sort by Category", self.sort_mode, SortMode.ByCategory)
            if self.sort_mode != sort_mode:
                self.sort_mode = SortMode.ByCategory
                self.filtered_widgets.sort(key=lambda w: (w.category.lower() if w.category else "", w.name.lower()))
                
            sort_mode = ImGui.radio_button("Sort by Status", self.sort_mode, SortMode.ByStatus)
            if self.sort_mode != sort_mode:
                self.sort_mode = SortMode.ByStatus
                self.filtered_widgets.sort(key=lambda w: (not w.enabled, w.name.lower()))
                
            PyImGui.end_popup()    
    
    def is_same_color(self, color1 : tuple[float, float, float, float], color2 : tuple[float, float, float, float]) -> bool:
        threshold = 0.01
        return all(abs(c1 - c2) < threshold for c1, c2 in zip(color1, color2))
    
    def draw_tree(self, node: WidgetTreeNode, style : Style = ImGui.get_style()):
        selected = self.path == node.path
                        
        if not node.children:
            node_open = ImGui.selectable(label=f"{node.name}##{node.depth}", selected=selected)
        else:
            if selected:
                x, y = PyImGui.get_cursor_screen_pos()
                width = PyImGui.get_content_region_avail()[0]
                height = 14
                
                PyImGui.draw_list_add_rect_filled(
                    x, y, x + width, y + height, style.Header.color_int, 0, 0)
                
            node_open = ImGui.tree_node(label=f"{node.name}##{node.depth}")
        
        if selected:
            style.Header.pop_color()
        
        if PyImGui.is_item_clicked(0):
            self.path = node.path if self.path != node.path else ""
            
            if self.single_filter:
                self.tag = ""
                self.category = ""
                self.widget_filter = ""
            
            self.queue_filter_widgets = True
        
        if node_open and node.children:                
            for child in node.children.values():
                self.draw_tree(child, style)
            
            ImGui.tree_pop()
                    
    def draw_libary_view(self):
        if self.win_size:
            PyImGui.set_next_window_size(self.win_size, PyImGui.ImGuiCond.Always)
        window_open = ImGui.Begin(ini_key=self.ini_key, name=self.module_name, flags=PyImGui.WindowFlags.MenuBar)
        
        if window_open:            
            win_size = PyImGui.get_window_size()
            win_pos = PyImGui.get_window_pos()
            self.win_size = (win_size[0], win_size[1])
            collapsed = PyImGui.is_window_collapsed()
            io = PyImGui.get_io()
            mouse_pos = (io.mouse_pos_x, io.mouse_pos_y)
    
            if self.previous_size != self.win_size and self.layout_mode is LayoutMode.Library and not collapsed:
                self.previous_size = self.win_size
                IniManager().set(key=self.ini_key, section="Configuration", var_name="library_width", value=self.win_size[0])
                IniManager().set(key=self.ini_key, section="Configuration", var_name="library_height", value=self.win_size[1])
                IniManager().save_vars(self.ini_key)
                
            ImGui.set_window_within_displayport(*self.win_size, PyImGui.ImGuiCond.Once)            
            style = ImGui.get_style()
            
            PyImGui.push_clip_rect(*win_pos, self.win_size[0], self.win_size[1], False)
            ImGui.DrawTextureInDrawList((win_pos[0] + 4, win_pos[1] + 2), (20, 20), "python_icon_round_20px.png")
            if ImGui.is_mouse_in_rect((win_pos[0] + 4, win_pos[1] + 2, 20, 20)):
                PyImGui.begin_tooltip()
                PyImGui.text(f"Collapse to a single button showing only the Python icon.\nOpening the full library view when clicked." )
                PyImGui.end_tooltip()
            
            close_rect = (win_pos[0] + win_size[0] - 21, win_pos[1] + 2, 16, 16)
            minimize_rect = (win_pos[0] + 4 + win_size[0] - 50, win_pos[1] + 2, 24, 20)
            cursor_pos = PyImGui.get_cursor_screen_pos()
            PyImGui.set_cursor_screen_pos(minimize_rect[0], minimize_rect[1])
                
            fontawesome_font_size = int(int(PyImGui.get_text_line_height()) * 0.8)
            ImGui.push_font("Regular", fontawesome_font_size)
            style.Button.push_color_direct((0, 0, 0, 0))
            
            if PyImGui.button(IconsFontAwesome5.ICON_MINUS + "##MinimizeLibraryView", minimize_rect[2], minimize_rect[3]):
                self.set_layout_mode(LayoutMode.Minimalistic)
            style.Button.pop_color_direct()
            ImGui.pop_font()
            ImGui.show_tooltip("Switch to Minimalistic View")
            
            if ImGui.is_mouse_in_rect(close_rect):
                PyImGui.begin_tooltip()
                PyImGui.text("Switch to One Button View")
                PyImGui.end_tooltip()
            
            PyImGui.set_cursor_screen_pos(cursor_pos[0], cursor_pos[1])
            PyImGui.pop_clip_rect()
            
            if ImGui.begin_menu_bar():
                if ImGui.begin_menu("Widgets"):
                    if ImGui.menu_item("Reload Widgets"):
                        self.widget_manager.discovered = False
                        self.widget_manager.discover()
                        self.queue_filter_widgets = True
                    ImGui.show_tooltip("Reload all widgets")
                    
                    if ImGui.menu_item(f"{("Run" if not self.widget_manager.enable_all else "Pause")} all widgets"):
                        self.widget_manager.enable_all = not self.widget_manager.enable_all
                        IniManager().save_vars(self.ini_key)
                        IniManager().set(key=self.ini_key, var_name="enable_all", value=self.widget_manager.enable_all, section="Configuration")
                    ImGui.show_tooltip(f"{("Run" if not self.widget_manager.enable_all else "Pause")} all widgets")
                    
                    if ImGui.menu_item(f"{("Show" if not self.widget_manager.show_widget_ui else "Hide")} all widget UIs"):
                        show_widget_ui = not self.widget_manager.show_widget_ui
                        self.widget_manager.set_widget_ui_visibility(show_widget_ui)
                    ImGui.show_tooltip(f"{("Show" if not self.widget_manager.show_widget_ui else "Hide")} all widget UIs by setting the alpha of imgui to 0 or 1")
                        
                    if ImGui.menu_item(f"{("Pause" if not self.widget_manager.pause_optional_widgets else "Resume")} all optional widgets"):
                        pause_non_env = not self.widget_manager.pause_optional_widgets
                        if not self.widget_manager.pause_optional_widgets:
                            self.widget_manager.pause_widgets()
                        else:
                            self.widget_manager.resume_widgets()
                            
                        own_email = Player.GetAccountEmail()
                        for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
                            if acc.AccountEmail == own_email:
                                continue
                            
                            GLOBAL_CACHE.ShMem.SendMessage(own_email, acc.AccountEmail, SharedCommandType.PauseWidgets if pause_non_env else SharedCommandType.ResumeWidgets)
                    ImGui.show_tooltip(f"{("Pause" if not self.widget_manager.pause_optional_widgets else "Resume")} all optional/non system widgets")
                    
                    ImGui.end_menu()                   
                
                if ImGui.begin_menu("Preferences"):
                    if ImGui.begin_menu("Layout"):                        
                        if ImGui.begin_menu("Startup View Mode"):
                            layout_mode = ImGui.radio_button("Last View", self.startup_layout, LayoutMode.LastView)
                            if self.startup_layout != layout_mode:
                                self.startup_layout = LayoutMode.LastView                                
                                IniManager().set(key=self.ini_key, var_name="startup_layout", value=self.startup_layout.name, section="Configuration")
                                IniManager().save_vars(self.ini_key)                                
                            ImGui.show_tooltip("Open the widget browser in the same view mode as when it was last closed.")
                                                        
                            layout_mode = ImGui.radio_button("Library View", self.startup_layout, LayoutMode.Library)
                            if self.startup_layout != layout_mode:
                                self.startup_layout = LayoutMode.Library
                                self.set_layout_mode(self.startup_layout)
                                IniManager().set(key=self.ini_key, var_name="startup_layout", value=self.startup_layout.name, section="Configuration")
                                IniManager().save_vars(self.ini_key)
                            ImGui.show_tooltip("Open the widget browser in library view by default,\nshowing all details and options for each widget.")
                                
                            layout_mode = ImGui.radio_button("Compact View", self.startup_layout, LayoutMode.Compact)
                            if self.startup_layout != layout_mode:
                                self.startup_layout = LayoutMode.Compact
                                self.set_layout_mode(self.startup_layout)
                                IniManager().set(key=self.ini_key, var_name="startup_layout", value=self.startup_layout.name, section="Configuration")
                                IniManager().save_vars(self.ini_key)
                            ImGui.show_tooltip("Open the widget browser in compact view by default,\nshowing a simplified card for each widget.")
                                
                            layout_mode = ImGui.radio_button("Minimalistic View", self.startup_layout, LayoutMode.Minimalistic)
                            if self.startup_layout != layout_mode:
                                self.startup_layout = LayoutMode.Minimalistic
                                self.set_layout_mode(self.startup_layout)
                                IniManager().set(key=self.ini_key, var_name="startup_layout", value=self.startup_layout.name, section="Configuration")
                                IniManager().save_vars(self.ini_key)
                            ImGui.show_tooltip("Open the widget browser in minimalistic view by default,\nshowing only a search icon which switches to compact view when clicked.\nIf the widget filter is cleared while in compact view, it will switch back to minimalistic view.")
                            
                            ImGui.end_menu()
                        
                        jump_to_minimalistic = ImGui.checkbox("Jump to Minimalistic View", self.jump_to_minimalistic)
                        if jump_to_minimalistic != self.jump_to_minimalistic:
                            self.jump_to_minimalistic = jump_to_minimalistic
                            IniManager().set(key=self.ini_key, var_name="jump_to_minimalistic", value=self.jump_to_minimalistic, section="Configuration")
                            IniManager().save_vars(self.ini_key)
                        ImGui.show_tooltip("Automatically switch to Minimalistic View after clearing the search field while in Compact View.\nIf the widget filter is cleared while in compact view, it will switch back to minimalistic view.")
                        
                        PyImGui.push_item_width(100)
                        max_suggestions = ImGui.slider_int("Max Suggestions", self.max_suggestions, 1, 50)
                        if max_suggestions != self.max_suggestions:
                            self.max_suggestions = max_suggestions
                            IniManager().set(key=self.ini_key, var_name="max_suggestions", value=self.max_suggestions, section="Configuration")
                            IniManager().save_vars(self.ini_key)
                        PyImGui.pop_item_width()
                        ImGui.show_tooltip("Set the maximum number of search suggestions to display in the search dropdown in compact view.")
                        
                        PyImGui.push_item_width(100)
                        single_button_size = ImGui.slider_int("Single Button Size", self.single_button_size, 20, 128)
                        if single_button_size != self.single_button_size:
                            self.single_button_size = single_button_size
                            IniManager().set(key=self.ini_key, var_name="single_button_size", value=self.single_button_size, section="Configuration")
                            IniManager().save_vars(self.ini_key)
                        PyImGui.pop_item_width()
                        ImGui.show_tooltip("Set the maximum number of search suggestions to display in the search dropdown in compact view.")
                        ImGui.end_menu()
                    
                    if ImGui.begin_menu("Widget Cards"):
                        if ImGui.begin_menu("Layout"):                            
                            show_configure = ImGui.checkbox("Show Configure Button", self.show_configure_button)
                            if show_configure != self.show_configure_button:
                                self.show_configure_button = show_configure
                                IniManager().set(key=self.ini_key, var_name="show_configure_button", value=self.show_configure_button, section="Configuration")
                                IniManager().save_vars(self.ini_key)
                            ImGui.show_tooltip("Show or hide the configure button on each widget card.")
                            
                            show_images = ImGui.checkbox("Show Widget Images", self.show_images)
                            if show_images != self.show_images:
                                self.show_images = show_images
                                IniManager().set(key=self.ini_key, var_name="show_images", value=self.show_images, section="Configuration")
                                IniManager().save_vars(self.ini_key)
                            ImGui.show_tooltip("Show or hide the images on each widget card.")
                            
                            show_separator = ImGui.checkbox("Show Separator", self.show_separator)
                            if show_separator != self.show_separator:
                                self.show_separator = show_separator
                                IniManager().set(key=self.ini_key, var_name="show_separator", value=self.show_separator, section="Configuration")
                                IniManager().save_vars(self.ini_key)
                            
                            show_category = ImGui.checkbox("Show Widget Category", self.show_category)
                            if show_category != self.show_category:
                                self.show_category = show_category
                                IniManager().set(key=self.ini_key, var_name="show_category", value=self.show_category, section="Configuration")
                                IniManager().save_vars(self.ini_key)
                            ImGui.show_tooltip("Show or hide the category text on each widget card.")
                            
                            show_tags = ImGui.checkbox("Show Widget Tags", self.show_tags)
                            if show_tags != self.show_tags:
                                self.show_tags = show_tags
                                IniManager().set(key=self.ini_key, var_name="show_tags", value=self.show_tags, section="Configuration")
                                IniManager().save_vars(self.ini_key)
                            ImGui.show_tooltip("Show or hide the tags on each widget card.")
                            
                            fixed_width = ImGui.checkbox("Fixed Card Width", self.fixed_card_width)
                            if fixed_width != self.fixed_card_width:
                                self.fixed_card_width = fixed_width
                                IniManager().set(key=self.ini_key, var_name="fixed_card_width", value=self.fixed_card_width, section="Configuration")
                                IniManager().save_vars(self.ini_key)
                            ImGui.show_tooltip("Enable or disable fixed card width.\nIf enabled, all widget cards will have the same width defined by 'Card Width'.\nIf disabled, card width will be determined automatically based on the available space and number of columns.")
                            
                            if self.fixed_card_width:
                                card_width = ImGui.slider_float("Card Width", self.card_width, 100, 600)
                                if card_width != self.card_width:
                                    self.card_width = card_width
                                    IniManager().set(key=self.ini_key, var_name="card_width", value=self.card_width, section="Configuration")
                                    IniManager().save_vars(self.ini_key)
                                ImGui.show_tooltip(f"Set the width of each widget card when fixed card width is enabled.\nCard width {self.card_width}px.")
                            
                            ImGui.end_menu()
                        
                        if ImGui.begin_menu("Styling"):
                            
                            card_rounding = ImGui.slider_float("Card Rounding", self.card_rounding, 0, 20)
                            if card_rounding != self.card_rounding:
                                self.card_rounding = card_rounding
                                IniManager().set(key=self.ini_key, var_name="card_rounding", value=self.card_rounding, section="Configuration")
                                IniManager().save_vars(self.ini_key)
                            ImGui.show_tooltip("Set the rounding of the widget cards.\nThis controls how rounded the corners of the widget cards are, with 0 being sharp corners and higher values being more rounded.")
                            
                            card_color = ImGui.color_edit4("Card", self.card_color.color_tuple)
                            if not self.is_same_color(card_color, self.card_color.color_tuple):
                                self.card_color = Color.from_tuple(card_color)
                                IniManager().set(key=self.ini_key, var_name="card_color", value=self.card_color.to_rgba_string(), section="Configuration")
                                IniManager().save_vars(self.ini_key)
                            ImGui.show_tooltip("Set the background color of the widget cards.\nThis color is used for inactive widgets or when 'Show Enabled State' is disabled.")
                            
                            card_enabled_color = ImGui.color_edit4("Card (Enabled)", self.card_enabled_color.color_tuple)
                            if not self.is_same_color(card_enabled_color, self.card_enabled_color.color_tuple):
                                self.card_enabled_color = Color.from_tuple(card_enabled_color)
                                IniManager().set(key=self.ini_key, var_name="card_enabled_color", value=self.card_enabled_color.to_rgba_string(), section="Configuration")
                                IniManager().save_vars(self.ini_key)
                            ImGui.show_tooltip("Set the background color of enabled widget cards.\nThis color is used for active widgets when 'Show Enabled State' is enabled.")
                            
                            name_color = ImGui.color_edit4("Name", self.name_color.color_tuple)
                            if not self.is_same_color(name_color, self.name_color.color_tuple):
                                self.name_color = Color.from_tuple(name_color)
                                IniManager().set(key=self.ini_key, var_name="name_color", value=self.name_color.to_rgba_string(), section="Configuration")
                                IniManager().save_vars(self.ini_key)
                            ImGui.show_tooltip("Set the color used for widget names.\nThis color is used for the text of the widget names displayed on each widget card.")
                            
                            name_enabled_color = PyImGui.color_edit4("Name (Enabled)", self.name_enabled_color.color_tuple)
                            if not self.is_same_color(name_enabled_color, self.name_enabled_color.color_tuple):
                                self.name_enabled_color = Color.from_tuple(name_enabled_color)
                                IniManager().set(key=self.ini_key, var_name="name_enabled_color", value=self.name_enabled_color.to_rgba_string(), section="Configuration")
                                IniManager().save_vars(self.ini_key)
                            ImGui.show_tooltip("Set the color used for enabled widget names.\nThis color is used for the text of the widget names displayed on each widget card when the widget is enabled.")
                            
                            favorites_color = ImGui.color_edit4("Favorites", self.favorites_color.color_tuple)
                            if not self.is_same_color(favorites_color, self.favorites_color.color_tuple):
                                self.favorites_color = Color.from_tuple(favorites_color)
                                IniManager().set(key=self.ini_key, var_name="favorites_color", value=self.favorites_color.to_rgba_string(), section="Configuration")
                                IniManager().save_vars(self.ini_key)    
                            ImGui.show_tooltip("Set the color used to indicate favorite widgets.\nThis color is used for the star icon on each widget card.")
                            
                            tag_color = ImGui.color_edit4("Tags", self.tag_color.color_tuple)
                            if not self.is_same_color(tag_color, self.tag_color.color_tuple):
                                self.tag_color = Color.from_tuple(tag_color)
                                IniManager().set(key=self.ini_key, var_name="tag_color", value=self.tag_color.to_rgba_string(), section="Configuration")
                                IniManager().save_vars(self.ini_key)
                            ImGui.show_tooltip("Set the color used for widget tags.\nThis color is used for the text of the tags displayed on each widget card.")
                            
                            category_color = ImGui.color_edit4("Category", self.category_color.color_tuple)
                            if not self.is_same_color(category_color, self.category_color.color_tuple):
                                self.category_color = Color.from_tuple(category_color)
                                IniManager().set(key=self.ini_key, var_name="category_color", value=self.category_color.to_rgba_string(), section="Configuration")
                                IniManager().save_vars(self.ini_key)
                            ImGui.show_tooltip("Set the color used for widget categories.\nThis color is used for the text of the category displayed on each widget card.")
                            ImGui.end_menu()                        
                        
                        ImGui.end_menu()                        
                    
                    if ImGui.begin_menu("Keybinds"):
                        key, modifiers, changed = ImGui.keybinding("Focus Search##WidgetBrowser", key=self.focus_keybind.key, modifiers=self.focus_keybind.modifiers)                    
                        if changed:
                            self.focus_keybind.key = key
                            self.focus_keybind.modifiers = modifiers
                            
                            IniManager().set(self.ini_key, var_name="hotkey", section="Configuration", value=self.focus_keybind.key.name)
                            IniManager().set(self.ini_key, var_name="hotkey_modifiers", section="Configuration", value=self.focus_keybind.modifiers.name)
                            IniManager().save_vars(self.ini_key)
                        
                        ImGui.show_tooltip("Set the hotkey used to focus the search field in the widget browser.\nPressing this hotkey will move the keyboard focus to the search field, allowing you to start typing immediately to filter widgets.\nWorks only ingame due to limitations with our Hotkey system.")
                        
                        PyImGui.same_line(0, 0)
                        ImGui.dummy(200, 0)
                        
                        ImGui.separator()
                                                    
                        ImGui.show_tooltip("Clear all keybinds, resetting them to their default unbound state.")
                        ImGui.end_menu()
                            
                    if ImGui.begin_menu("Behavior"):
                        single_filter = ImGui.checkbox("Single Filter Mode", self.single_filter)
                        if single_filter != self.single_filter:
                            self.single_filter = single_filter
                            IniManager().set(key=self.ini_key, var_name="single_filter", value=self.single_filter, section="Configuration")
                            IniManager().save_vars(self.ini_key)
                        ImGui.show_tooltip("Enable or disable single filter mode.\nWhen enabled, selecting a category, tag, path or editing the search field will clear any existing filters in the other fields.\nThis ensures that only one filter is applied at a time.")                        
                        ImGui.end_menu()
                        
                    ImGui.end_menu()
                ImGui.end_menu_bar()
            
            _ = self.draw_toggle_view_mode_button()   
            PyImGui.same_line(0, 5)    
            search_width = PyImGui.get_content_region_avail()[0] - 32
            PyImGui.push_item_width(search_width)
            changed, self.widget_filter = ImGui.search_field("##WidgetFilter", self.widget_filter)
            if self.focus_search:
                PyImGui.set_keyboard_focus_here(-1)
                self.focus_search = False
            
            self.draw_search_tooltip()
            PyImGui.pop_item_width()
            if changed:
                if self.single_filter:
                    self.tag = ""
                    self.category = ""
                    self.path = ""
                    
                self.queue_filter_widgets = True
            
            PyImGui.same_line(0, 5)
            self.draw_sorting_button()
            ImGui.separator()
            
            if ImGui.begin_table("navigation_view2", 2, PyImGui.TableFlags.SizingStretchProp | PyImGui.TableFlags.Resizable | PyImGui.TableFlags.BordersInnerV):
                max_width = PyImGui.get_content_region_avail()[0]
                                
                PyImGui.table_setup_column("##categories", PyImGui.TableColumnFlags.WidthFixed, 200)
                PyImGui.table_setup_column("##widgets", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_next_row()
                
                PyImGui.table_set_column_index(0)
                if ImGui.begin_child("##category_list", (0, 0)):      
                    if ImGui.selectable("All", self.view_mode is ViewMode.All):
                        self.view_mode = ViewMode.All if not self.view_mode is ViewMode.All else ViewMode.All
                        if self.single_filter:
                            self.tag = ""
                            self.category = ""
                            self.widget_filter = ""
                            self.path = ""
                            
                        self.queue_filter_widgets = True      
                        
                    if ImGui.selectable("Favorites", self.view_mode is ViewMode.Favorites):
                        self.view_mode = ViewMode.Favorites if not self.view_mode is ViewMode.Favorites else ViewMode.All
                        if self.single_filter:
                            self.tag = ""
                            self.category = ""
                            self.widget_filter = ""
                            self.path = ""
                        self.queue_filter_widgets = True
                        
                    if ImGui.selectable("Active", self.view_mode is ViewMode.Actives):
                        self.view_mode = ViewMode.Actives if not self.view_mode is ViewMode.Actives else ViewMode.All
                        if self.single_filter:
                            self.tag = ""
                            self.category = ""
                            self.widget_filter = ""
                            self.path = ""
                        self.queue_filter_widgets = True
                        
                    if ImGui.selectable("Inactive", self.view_mode is ViewMode.Inactives):
                        self.view_mode = ViewMode.Inactives if not self.view_mode is ViewMode.Inactives else ViewMode.All
                        if self.single_filter:
                            self.tag = ""
                            self.category = ""
                            self.widget_filter = ""
                            self.path = ""
                        self.queue_filter_widgets = True
                        
                    ImGui.separator()
                    style.ScrollbarSize.push_style_var_direct(5)
                    
                    if ImGui.begin_child("##tags", (0, 0), flags=PyImGui.WindowFlags.HorizontalScrollbar):  
                        ##Create tree of selectables self.folder_tree, indent based on depth
                        for node in self.folder_tree.children.values():
                            self.draw_tree(node)
                            
                    ImGui.end_child()
                    style.ScrollbarSize.pop_style_var_direct()
                ImGui.end_child()
                
                PyImGui.table_set_column_index(1)
                
                if ImGui.begin_child("##widgets", (0, 0)):  
                    style.DisabledAlpha.push_style_var_direct(0.4)
                    
                    min_card_width = self.card_width if self.fixed_card_width else 250
                    available_width = PyImGui.get_content_region_avail()[0] - (style.ScrollbarSize.value1 if PyImGui.get_scroll_y() == 0 else 0)
                    num_columns = max(1, int(available_width // min_card_width))
                    card_width = 0
                    PyImGui.columns(num_columns, "widget_cards", False)
                    card_height = self.get_card_height()
                    
                    first_visible = False
                    last_visible = False
                    
                    self._push_card_style(style, enabled=False)
                    for widget in (self.filtered_widgets):
                        card_width = self.card_width if self.fixed_card_width else PyImGui.get_content_region_avail()[0]
                        if first_visible and last_visible:
                            ImGui.dummy(card_width, card_height)
                            PyImGui.next_column()
                            continue
                        
                        is_visible = PyImGui.is_rect_visible(card_width, card_height)                        
                        if is_visible:
                            first_visible = True
                            
                            clicked, hovered = self.draw_widget_card(widget, card_width, card_height, widget in self.favorites, mouse_pos, style)
                            if clicked:
                                self.queue_filter_widgets = True
                                                                            
                            # ---- RIGHT CLICK DETECTION ----
                            if hovered and PyImGui.is_mouse_clicked(1):
                                self.context_menu_id = f"WidgetContext##{widget.folder_script_name}"
                                self.context_menu_widget = widget
                                PyImGui.open_popup(self.context_menu_id)
                        
                        else:
                            if first_visible:
                                last_visible = True
                            
                            ImGui.dummy(card_width, card_height)
                            
                        PyImGui.next_column()
                        
                    if self.active_card_style_pushed:
                        self._pop_card_style(style)
                    
                    self._pop_card_style(style)
                        
                    style.DisabledAlpha.pop_style_var_direct()
                    PyImGui.end_columns()
                    
                    if self.context_menu_id and self.context_menu_widget:
                        self.card_context_menu(self.context_menu_id, self.context_menu_widget)
                ImGui.end_child()
                ImGui.end_table()
                                
        if PyImGui.is_window_collapsed() or not window_open:
            self.set_layout_mode(LayoutMode.SingleButton)   

        
        ImGui.End(self.ini_key)
        
        if self._request_disable_popup:
            PyImGui.open_popup(self.CONFIRMATION_MODAL_ID)
            self._request_disable_popup = False
            
        self.draw_confirmation_modal()

    def draw_confirmation_modal(self):
        io = PyImGui.get_io()
        center_x = (io.display_size_x / 2) - 250
        center_y = (io.display_size_y / 2) - 100

        PyImGui.set_next_window_pos(
            (center_x, center_y),
            PyImGui.ImGuiCond.Always,
        )

        PyImGui.set_next_window_size(
            (500, 175),
            PyImGui.ImGuiCond.Always,
        )

        if PyImGui.begin_popup_modal(
            self.CONFIRMATION_MODAL_ID,
            True,
            PyImGui.WindowFlags.NoMove | PyImGui.WindowFlags.NoResize | PyImGui.WindowFlags.NoTitleBar
            | PyImGui.WindowFlags.NoSavedSettings
        ):
            widget = self._pending_disable_widget

            if widget:
                ImGui.text_colored(
                    "Warning - This widget is required for core functionality!",
                    (1.0, 0.2, 0.2, 1.0),
                    font_size=16
                )
                PyImGui.separator()

                ImGui.text_wrapped(
                    f"The widget '{widget.name}' is a SYSTEM widget.\n\n"
                    "Disabling it may break core functionality.\n\n"
                    "Are you sure you want to continue?"
                )

                PyImGui.spacing()
                PyImGui.separator()
                PyImGui.spacing()

                PyImGui.columns(2, "confirmation_buttons", False)
                
                # ---- BUTTONS ----
                if ImGui.button("Cancel", -1, 0):
                    self._pending_disable_widget = None
                    PyImGui.close_current_popup()

                PyImGui.next_column()
                if ImGui.button("Disable", -1, 0):
                    self.widget_manager.disable_widget(widget.plain_name)
                    self._pending_disable_widget = None
                    PyImGui.close_current_popup()
                PyImGui.end_columns()
                
            PyImGui.end_popup()

    def _push_card_style(self, style : Style, enabled : bool):
        self.active_card_style_pushed = enabled
            
        style.ChildBg.push_color_direct(self.card_enabled_color.rgb_tuple if enabled else self.card_color.rgb_tuple)
        style.ChildBorderSize.push_style_var_direct(2.0 if enabled else 1.0) 
        style.ChildRounding.push_style_var_direct(self.card_rounding)
        style.Border.push_color_direct(self.card_enabled_color.opacify(0.6).rgb_tuple if enabled else self.card_color.opacify(0.6).rgb_tuple)
        pass

    def _pop_card_style(self, style : Style):
        self.active_card_style_pushed = False
        style.ChildBg.pop_color_direct()
        style.ChildBorderSize.pop_style_var_direct()
        style.ChildRounding.pop_style_var_direct()
        style.Border.pop_color_direct()
        pass

    def _push_tag_style(self, style : Style, color : tuple):        
        style.FramePadding.push_style_var_direct(4, 4)
        style.Button.push_color_direct(color)
        style.ButtonHovered.push_color_direct(color)
        style.ButtonActive.push_color_direct(color)
        ImGui.push_font("Regular", 12)

    def _pop_tag_style(self, style : Style):
        style.FramePadding.pop_style_var_direct()
        style.Button.pop_color_direct()
        style.ButtonHovered.pop_color_direct()
        style.ButtonActive.pop_color_direct()        
        ImGui.pop_font()
    
    def get_card_height(self):
        height = 20
        
        if self.show_images:
            height += self.IMAGE_SIZE
        else:
            height += 11
            if self.show_separator:
                height += 3
                
            if self.show_category:
                height += 15
        
        if self.show_tags:
            height += 25
        
        return height

    def draw_widget_card(self, widget : "Widget", width : float, height: float, is_favorite: bool, mouse_pos: tuple, style : Style) -> tuple[bool, bool]:
        """
        Draws a single widget card.
        Must be called inside a grid / SameLine layout.
        """
    
        rect_visible = PyImGui.is_rect_visible(width, height)
        clicked = False
        hovered = False
        cog_hovered = False
        
        if rect_visible:
            enabled = widget.enabled
            
            if enabled:
                if not self.active_card_style_pushed:
                    self._push_card_style(style, enabled)
            else:
                if self.active_card_style_pushed:
                    self._pop_card_style(style)
        
            
            cx, cy = PyImGui.get_cursor_screen_pos()
            opened = PyImGui.begin_child(
                f"##widget_card_{widget.folder_script_name}",
                (width, height),
                border=True,
                flags=PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse
            )
            
            if  opened:
                available_width = PyImGui.get_content_region_avail()[0]
                
                # --- Top Row: Icon + Title ---
                PyImGui.begin_group()

                # Icon
                if self.show_images:
                    ImGui.image(widget.image, (self.IMAGE_SIZE, self.IMAGE_SIZE), border_color=self.category_color.rgb_tuple)
                    PyImGui.same_line(0, 5)

                # Title + Category
                PyImGui.begin_group()
                # name = widget.name
                name = ImGui.trim_text_to_width(text=f"{widget.name}", max_width=width - self.IMAGE_SIZE - (self.BUTTON_HEIGHT if widget.has_configure_property and self.show_configure_button else 0) - self.PADDING * 4 - (15 if is_favorite else 0))
                if is_favorite:
                    ImGui.text_colored(f"{IconsFontAwesome5.ICON_STAR} ", self.favorites_color.color_tuple, font_size=10)
                    PyImGui.same_line(0, 3)
                    
                ImGui.text_colored(name, self.name_color.color_tuple if not widget.enabled else self.name_enabled_color.color_tuple)

                if self.show_separator:
                    PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 4)
                    PyImGui.separator()
                    
                if self.show_category:
                    PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 2)
                    ImGui.text_colored(f"{widget.category}", self.category_color.color_tuple if widget.category != "System" else self.SYSTEM_COLOR.color_tuple, 12)

                PyImGui.end_group()
                        
                if widget.has_configure_property and self.show_configure_button:
                    PyImGui.set_cursor_pos(available_width - 10, 2)
                    configuring = ImGui.toggle_icon_button(IconsFontAwesome5.ICON_COG, widget.configuring, self.BUTTON_HEIGHT, self.BUTTON_HEIGHT)
                    if configuring != widget.configuring:
                        widget.set_configuring(configuring)
                    
                    cog_hovered = PyImGui.is_item_hovered()
                    if cog_hovered:
                        ImGui.begin_tooltip()
                        ImGui.text("Configure Widget")
                        ImGui.end_tooltip()
                    
                    
                        
                PyImGui.end_group()

                if self.show_tags:
                    # --- Tags ---
                    self._push_tag_style(style, self.tag_color.rgb_tuple)
                    
                    for i in range(1, len(widget.tags)):
                        if i > 1:
                            PyImGui.same_line(0, 2)
                        
                        PyImGui.button(widget.tags[i])
                        
                    self._pop_tag_style(style)


            PyImGui.end_child()
                    
            if ImGui.is_mouse_in_rect((cx, cy, cx + width, cy + height), mouse_pos):
                if PyImGui.is_item_clicked(0):
                    clicked = True
                    
                    if not widget.enabled:
                        self.widget_manager.enable_widget(widget.plain_name)
                    else:                        
                        if widget.category == "System":
                            self._pending_disable_widget = widget
                            self._request_disable_popup = True
                        else:
                            self.widget_manager.disable_widget(widget.plain_name)
                        
                if not cog_hovered and PyImGui.is_item_hovered():
                        hovered = True
                        self._pop_card_style(style)
                        
                        if widget.has_tooltip_property:
                            if widget.tooltip:
                                
                                try:
                                    widget.tooltip()                                
                                except Exception as e:
                                    Py4GW.Console.Log("WidgetHandler", f"Error during tooltip of widget {widget.folder_script_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                                    Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
                                
                        else:
                            PyImGui.show_tooltip(f"Enable/Disable {widget.name} widget")
                            
                        self._push_card_style(style, enabled)
        else:
            ImGui.dummy(width, height)
            
        return clicked, (hovered or cog_hovered)
        
    def draw_compact_widget_card(self, widget : "Widget", width : float, style : Style) -> tuple[bool, bool]:
        """
        Draws a single widget card.
        Must be called inside a grid / SameLine layout.
        """
        
        rect_visible = PyImGui.is_rect_visible(width, 30)
        clicked = False
        hovered = False
        cog_hovered = False

        if rect_visible:
            enabled = widget.enabled
            
            if enabled:
                if not self.active_card_style_pushed:
                    self._push_card_style(style, enabled)
            else:
                if self.active_card_style_pushed:
                    self._pop_card_style(style)
        
            opened = PyImGui.begin_child(
                f"##widget_card_{widget.folder_script_name}",
                (width, 30),
                border=True,
                flags=PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse
            )
            
            if opened and PyImGui.is_rect_visible(width, 30):
                available_width = PyImGui.get_content_region_avail()[0]

                ImGui.push_font("Regular", 15)
                name = ImGui.trim_text_to_width(text=widget.name, max_width=available_width - 20)
                ImGui.text_colored(name, self.name_color.color_tuple if not widget.enabled else self.name_enabled_color.color_tuple, 15)
                ImGui.pop_font()
                                
                if widget.has_configure_property:
                    PyImGui.set_cursor_pos(available_width - 10, 2)
                    configuring = ImGui.toggle_icon_button(IconsFontAwesome5.ICON_COG, widget.configuring, self.BUTTON_HEIGHT, self.BUTTON_HEIGHT)
                    if configuring != widget.configuring:
                        widget.set_configuring(configuring)
                        
                    cog_hovered = PyImGui.is_item_hovered()

            PyImGui.end_child()
            
            if PyImGui.is_item_clicked(0):
                clicked = True
                if not widget.enabled:
                    self.widget_manager.enable_widget(widget.plain_name)
                else:
                    if widget.category == "System":
                        self._pending_disable_widget = widget
                        self._request_disable_popup = True
                    else:
                        self.widget_manager.disable_widget(widget.plain_name)
                
            if not cog_hovered and PyImGui.is_item_hovered():
                hovered = True
                self._pop_card_style(style)
                
                if widget.has_tooltip_property:
                    try:
                        if widget.tooltip:
                            self._pop_card_style(style)                        
                            
                            widget.tooltip()
                            
                    except Exception as e:
                        Py4GW.Console.Log("WidgetHandler", f"Error during tooltip of widget {widget.folder_script_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                        Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
                else:
                    PyImGui.show_tooltip(f"Enable/Disable {widget.name} widget")
                    
                self._push_card_style(style, enabled)
        else:
            ImGui.dummy(width, 30)
            
        return clicked, (hovered or cog_hovered)     

    def draw_one_button_view(self): 
        if self.win_size:       
            PyImGui.set_next_window_size(self.win_size, PyImGui.ImGuiCond.Always)
            
        PyImGui.set_next_window_collapsed(False, PyImGui.ImGuiCond.Always)
        style = ImGui.get_style()
        
        padding = self.single_button_size * 0.05
        style.WindowPadding.push_style_var_direct(padding, padding)
        win_open = ImGui.Begin(ini_key=self.ini_key, name=self.module_name, flags=PyImGui.WindowFlags(PyImGui.WindowFlags.NoResize|
                                                                                                      PyImGui.WindowFlags.NoCollapse|
                                                                                                      PyImGui.WindowFlags.NoTitleBar|
                                                                                                      PyImGui.WindowFlags.NoScrollbar|
                                                                                                      PyImGui.WindowFlags.NoScrollWithMouse))   
        style.WindowPadding.pop_style_var_direct()
        
        if win_open:
            win_size = PyImGui.get_window_size()
            self.win_size = (win_size[0], win_size[1])
            ImGui.set_window_within_displayport(*self.win_size)
            win_pos = PyImGui.get_window_pos()
            win_center = (win_pos[0] + self.win_size[0] / 2, win_pos[1] + self.win_size[1] / 2)
            radius = (min(self.win_size) - (padding * 2)) / 2
            io = PyImGui.get_io()
            mouse_pos = (io.mouse_pos_x, io.mouse_pos_y)
            in_radius = (mouse_pos[0] - win_center[0]) ** 2 + (mouse_pos[1] - win_center[1]) ** 2 < radius ** 2
            win_hovered = PyImGui.is_window_hovered() and in_radius
            
            button_size = PyImGui.get_content_region_avail()[0] * (1 if win_hovered else 0.8)
            
            if not win_hovered:
                PyImGui.set_cursor_pos((self.win_size[0] - button_size) / 2, (self.win_size[1] - button_size) / 2)
            
            cx, cy = PyImGui.get_cursor_pos()
            ImGui.image("python_icon_round.png", (button_size, button_size))              
            PyImGui.set_cursor_pos(cx, cy)
            ImGui.dummy(button_size, button_size)
            if in_radius:       
                if PyImGui.is_item_clicked(0):
                    self.set_layout_mode(self.previous_mode)
                
                ImGui.show_tooltip(f"Open Widget Manager")
                
        ImGui.End(self.ini_key)
#endregion

#region widget
@dataclass
class Widget:
    """
    Widget data class with callback extraction in __post_init__
    """
    # Core identity (passed to __init__)
    folder_script_name: str       # "folder/script_name"
    plain_name: str = ""          # script without extension
    widget_path: str = ""         # folder relative path (no script)
    script_path: str = ""         # script full path
    
    #callback data
    update_callback_id: int = 0
    draw_callback_id: int = 0   
    main_callback_id: int = 0
    
    #Extra_execution data
    has_update_property: bool = False
    has_draw_property: bool = False
    has_main_property: bool = False
    has_configure_property: bool = False
    has_tooltip_property: bool = False
    
    # INI configuration (passed to __init__)
    ini_key: str = ""             # "" or valid key
    ini_path: str = ""            # "Widgets/folder"
    ini_filename: str = ""        # "script_name.ini"
        
    # Extracted callbacks (will be populated in __post_init__)
    main: Optional[Callable] = field(default=None, init=False)
    configure: Optional[Callable] = field(default=None, init=False)
    update: Optional[Callable] = field(default=None, init=False)
    draw: Optional[Callable] = field(default=None, init=False)
    tooltip: Optional[Callable] = field(default=None, init=False)
    minimal: Optional[Callable] = field(default=None, init=False)
    
    on_enable: Optional[Callable] = field(default=None, init=False)
    on_disable: Optional[Callable] = field(default=None, init=False)
    
    module: Optional[ModuleType] = field(default=None, init=False, repr=False)
    __enabled: bool = field(default=False, init=False,)
    __configuring: bool = field(default=False, init=False)
    
    # Optional properties to be displayed in widget manager ui
    name : str = field(default="", init=False, repr=False)
    image : str = field(default="", init=False, repr=False)
    tags : list[str] = field(default_factory=list, init=False)
    category : str = field(default="", init=False)    
    
    @property
    def enabled(self) -> bool:
        """Check if the widget is enabled"""
        return self.__enabled
    
    @property
    def configuring(self) -> bool:
        """Check if the widget is in configuring state"""
        return self.__configuring
    
    def load_module(self) -> bool:
        """Load the module if not already loaded"""
        if self.module is not None:
            return True  # Already loaded
        
        if not os.path.isfile(self.script_path):
            Py4GW.Console.Log("WidgetManager", f"Widget script not found: {self.script_path}", Py4GW.Console.MessageType.Error)
            return False
        
        unique_name = f"py4gw_widget_{self.folder_script_name.replace('/', '_').replace('.', '_')}"
        
        spec = importlib.util.spec_from_file_location(unique_name, self.script_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Invalid module spec: {self.script_path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[unique_name] = module
        
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            del sys.modules[unique_name]
            self.disable()
            Py4GW.Console.Log("WidgetManager", f"Failed to load widget module '{self.folder_script_name}': {e}", Py4GW.Console.MessageType.Error)
            return False
        
        self.module = module
        
        if self.module:                
            # --- capability flags (what exists in the widget module) ---
            self.has_main_property      = callable(getattr(self.module, "main", None))
            self.has_configure_property = callable(getattr(self.module, "configure", None))
            self.has_update_property    = callable(getattr(self.module, "update", None))
            self.has_draw_property      = callable(getattr(self.module, "draw", None))
            self.has_tooltip_property   = callable(getattr(self.module, "tooltip", None))
            
            # Extract main callback
            self.main = getattr(self.module, "main", None) if self.has_main_property else None
            self.configure = getattr(self.module, "configure", None) if self.has_configure_property else None
            self.update = getattr(self.module, "update", None) if self.has_update_property else None
            self.draw = getattr(self.module, "draw", None) if self.has_draw_property else None
            self.tooltip = getattr(self.module, "tooltip", None) if self.has_tooltip_property else None
            self.minimal = getattr(self.module, "minimal", None) if callable(getattr(self.module, "minimal", None)) else None
            self.on_enable = getattr(self.module, "on_enable", None) if callable(getattr(self.module, "on_enable", None)) else None
            self.on_disable = getattr(self.module, "on_disable", None) if callable(getattr(self.module, "on_disable", None)) else None
            self.optional = getattr(self.module, 'OPTIONAL', True) if hasattr(self.module, 'OPTIONAL') else True
            
            self.name = getattr(self.module, 'MODULE_NAME', "") if hasattr(self.module, 'MODULE_NAME') else self.cleaned_name()
            self.category = getattr(self.module, 'MODULE_CATEGORY', "") if hasattr(self.module, 'MODULE_CATEGORY') else (self.widget_path.split('/')[0] if self.widget_path else "") #get first folder after Widgets 
            self.tags = getattr(self.module, 'MODULE_TAGS', []) if hasattr(self.module, 'MODULE_TAGS') else [folder for folder in self.widget_path.split('/') if folder]
            self.image = getattr(self.module, 'MODULE_ICON', "") if hasattr(self.module, 'MODULE_ICON') else "Textures\\missing_texture.png"
            
            self.RegisterCallbacks()
            self.PauseCallbacks()  # Start paused until explicitly enabled
            
        return True
    
    def set_configuring(self, state: bool):
        """Set configuring state"""
        self.__configuring = state
        
    def enable_configuring(self):
        """Enable configuring state"""
        self.set_configuring(True)
        
    def disable_configuring(self):  
        """Disable configuring state"""
        self.set_configuring(False)
        
    def PauseCallbacks(self):
        """Pause callbacks by id if they exist"""
        self.RegisterCallbacks()  # Ensure callbacks are registered before trying to pause
        if self.update_callback_id:
            PyCallback.PyCallback.PauseById(self.update_callback_id)
        if self.draw_callback_id:
            PyCallback.PyCallback.PauseById(self.draw_callback_id)
        if self.main_callback_id:
            PyCallback.PyCallback.PauseById(self.main_callback_id)
            
    def ResumeCallbacks(self):
        """Resume callbacks by id if they exist"""
        self.RegisterCallbacks()  # Ensure callbacks are registered before trying to resume
        if self.update_callback_id:
            PyCallback.PyCallback.ResumeById(self.update_callback_id)
        if self.draw_callback_id:
            PyCallback.PyCallback.ResumeById(self.draw_callback_id)
        if self.main_callback_id:
            PyCallback.PyCallback.ResumeById(self.main_callback_id)
            
    def RegisterCallbacks(self):
        """Register callbacks if they exist in the module"""
        def wrap_profiler(key: str, fn: Callable):
            # We return a NEW function (lambda) that the C++ Callback system 
            # will store and execute every frame.
            def callback_wrapper():
                profiling = _get_profiling()
                if profiling.enabled:
                    # Executes fn() inside the profiling scope
                    return profiling.runcall_scope("widgets", f"{self.folder_script_name}:{key}", fn)
                else:
                    # Executes fn() normally
                    return fn()
            
            return callback_wrapper
       
        if self.module is None:
            return
        
        # 1. Update Callback (Logic Loop)
        if self.has_update_property and self.update is not None and self.update_callback_id == 0:
            self.update_callback_id = PyCallback.PyCallback.Register(
                self.folder_script_name,
                PyCallback.Phase.Update,
                wrap_profiler("update", self.update), # Pass the wrapper
                priority=99,
                context=PyCallback.Context.Update
            )
            
        # 2. Draw Callback (Visual Loop)
        if self.has_draw_property and self.draw is not None and self.draw_callback_id == 0:
            self.draw_callback_id = PyCallback.PyCallback.Register(
                self.folder_script_name,
                PyCallback.Phase.Update,
                wrap_profiler("draw", self.draw), # Pass the wrapper
                priority=99,
                context=PyCallback.Context.Draw
            )
            
        # 3. Main Callback (System Loop)
        if self.has_main_property and self.main is not None and self.main_callback_id == 0:
            self.main_callback_id = PyCallback.PyCallback.Register(
                self.folder_script_name,
                PyCallback.Phase.Update,
                wrap_profiler("main", self.main), # Pass the wrapper
                priority=99,
                context=PyCallback.Context.Main
            )
        
    def disable(self):
        """Disable the widget"""
        self.PauseCallbacks()
        if self.__enabled:
            if self.module is not None:
                try:
                    if self.on_disable:
                        self.on_disable()
                    
                except Exception as e:
                    Py4GW.Console.Log("WidgetManager", f"Error during on_disable of widget {self.folder_script_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    Py4GW.Console.Log("WidgetManager", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
                
            self.__enabled = False
        
    def enable(self):
        """Enable the widget"""
        
        #ensure callback
        self.ResumeCallbacks()

        if self.enabled and self.module is not None: 
            return  # Already enabled
        
        # enable widget only if module loads successfully
        self.__enabled = self.load_module()
        
        if self.enabled:
            try:
                if self.on_enable:
                    self.on_enable()
                
            except Exception as e:
                Py4GW.Console.Log("WidgetManager", f"Error during on_enable of widget {self.folder_script_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                Py4GW.Console.Log("WidgetManager", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
        
    def cleaned_name(self):
        """Cleanup the widget name for display"""
        ## if name starts with [0-9]-, remove that part for module cleanup and replace all _ with " "
        import re
        cleaned_name = re.sub(r'^\d+-', '', self.plain_name)
        cleaned_name = cleaned_name.replace("_", " ")
        return cleaned_name.strip()
                    
    def __post_init__(self):
        """Extract callbacks from module after initialization"""      
        
        # --- capability flags (what exists in the widget module) ---
        self.has_main_property      = False
        self.has_configure_property = False
        self.has_update_property    = False
        self.has_draw_property      = False
        self.has_tooltip_property   = False
        
        # Extract main callback
        self.main : Optional[Callable] = None
        self.configure : Optional[Callable] = None
        self.update : Optional[Callable] = None
        self.draw : Optional[Callable] = None
        self.tooltip : Optional[Callable] = None
        self.minimal : Optional[Callable] = None
        self.on_enable : Optional[Callable] = None
        self.on_disable : Optional[Callable] = None
        self.optional = True  
        
        self.load_module()
        
            
    @property
    def folder(self) -> str:
        """Extract folder path from name"""
        if '/' in self.folder_script_name:
            return self.folder_script_name.rsplit('/', 1)[0]
        return ""
    
    @property  
    def script_name(self) -> str:
        """Extract script name from name"""
        if '/' in self.folder_script_name:
            return self.folder_script_name.rsplit('/', 1)[1]
        return self.folder_script_name
    
    @property
    def can_save(self) -> bool:
        """Check if widget can save (has INI key)"""
        return bool(self.ini_key)
    
    @property
    def needs_ini_key(self) -> bool:
        """Check if widget needs INI key resolved"""
        # FIXED: Your logic was inverted
        return not self.ini_key and bool(self.ini_path) and bool(self.ini_filename)
    
    @property
    def is_global(self) -> bool:
        """Check if widget is global (works without account)"""
        return bool(getattr(self.module, 'GLOBAL', False))
    
    def __getitem__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")
    
    def __setitem__(self, key, value):
        if key in self.__dict__:
            self.__dict__[key] = value
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")
#endregion

class WidgetConfigVars:
    def __init__(self, widget_id: str, section: str, var_name: str):
        self.widget_id = widget_id
        self.section = section
        self.var_name = var_name
            
         
#region widget handler
class WidgetHandler:
    _instance = None
    _widgets_folder = "Widgets"
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, widgets_path=None):
        # Singleton guard
        if hasattr(self, "_initialized"):
            return
            
        # Path resolution
        if widgets_path:
            self.widgets_path = os.path.abspath(widgets_path)
        else:
            base_dir = Py4GW.Console.get_projects_path()
            self.widgets_path = os.path.join(base_dir, self._widgets_folder)
            
        self.MANAGER_INI_KEY:str = ""
        self.MANAGER_INI_PATH = "Widgets/WidgetManager"
        self.MANAGER_INI_FILENAME = "WidgetManager.ini"
        self.MANAGER_VARS_ADDED = False
        
        # Core state
        self.widgets: dict[str, Widget] = {}
        self.show_ui = True
        self.pause_optionals = False
        self.run_once = False
        self.enable_all = True
        
        self.discovered = False
        self.widget_initialized = False
        self._initialized = True
        self.config_vars: list[WidgetConfigVars] = []
        
        
        
    # Properties
    @property
    def pause_optional_widgets(self):
        return self.pause_optionals
    
    @property
    def show_widget_ui(self):
        return self.show_ui
    
    #region internal helpers
    def _log_error(self, message: str):
        Py4GW.Console.Log("WidgetManager", message, Py4GW.Console.MessageType.Error)
        
    def _log_success(self, message: str):
        Py4GW.Console.Log("WidgetManager", message, Py4GW.Console.MessageType.Info)
        
    def _get_config_var(self, widget_name: str, var_name: str) -> Optional[WidgetConfigVars]:
        for cv in self.config_vars:
            if cv.widget_id == widget_name and cv.var_name == var_name:
                return cv
        return None
    
    def _widget_var(self, widget_id: str, suffix: str) -> str:
        """Returns the unique variable name for IniManager lookup"""
        return f"{widget_id}__{suffix}"
    
    def _get_widget_by_plain_name(self, plain_name: str) -> Optional[Widget]:
        for widget in self.widgets.values():
            if widget.plain_name == plain_name:
                return widget
        return None
        
    def _set_widget_state(self, INI_KEY, name: str, state: bool):
        widget = self._get_widget_by_plain_name(name)
        if not widget:
            Py4GW.Console.Log("WidgetHandler", f"Widget '{name}' not found", Py4GW.Console.MessageType.Warning)
            return
        
        if state:
            widget.enable()
        else:
            widget.disable()
        
        widget_id = widget.folder_script_name  # full id: "folder/file.py"
        v_enabled = self._widget_var(widget_id, "enabled")  # "folder/file.py__enabled"

        cv = self._get_config_var(widget_id, v_enabled)

        if cv:
            # Correct order: key, section, var_name, value
            IniManager().set(key=INI_KEY, section=cv.section, var_name=cv.var_name, value=state)
            IniManager().save_vars(INI_KEY)
    #endregion        

        
    # --------------------------------------------
    # region discovery
           
    def discover(self):
        if self.discovered:
            return
        
        """Phase 0: Unload currently enabled widgets"""
        for widget in self.widgets.values():
            if widget.enabled:
                widget.disable()
                                
        """Phase 1: Discover widgets without INI configuration"""
        self.widgets.clear()
        
        try:
            self._scan_widget_folders()
            self.discovered = True
        except Exception as e:
            self._log_error(f"Discovery failed: {e}")
            raise
    
    
    def _scan_widget_folders(self):
        """Find .widget folders and load .py files throughout the entire tree"""
        if not os.path.isdir(self.widgets_path):
            raise FileNotFoundError(f"Widgets folder missing: {self.widgets_path}")
        
        for current_dir, dirs, files in os.walk(self.widgets_path):
            # Check if this specific folder is marked as a widget container
            if ".widget" in files:
                for py_file in [f for f in files if f.endswith(".py")]:
                    self._load_widget_module(current_dir, py_file)

    def _load_widget_module(self, folder: str, filename: str):
        """Load a widget module without INI configuration"""
        # Create widget ID
        rel_folder = os.path.relpath(folder, self.widgets_path)
        widget_id = f"{rel_folder}/{filename}" if rel_folder != "." else filename

        plain = os.path.splitext(filename)[0]
        widget_path = "" if rel_folder == "." else rel_folder.replace("\\", "/")

                
        if widget_id in self.widgets:
            return
        
        script_path = os.path.join(folder, filename)
        
        try:
            # 1. Create Widget with EMPTY INI data
            widget = Widget(
                folder_script_name=widget_id,
                plain_name=plain,
                widget_path=widget_path,
                script_path=script_path,
                ini_key="",           # Empty - will be set later
                ini_path="",          # Empty - will be set later  
                ini_filename="",      # Empty - will be set later                
            )
            
            # 3. Register
            self.widgets[widget_id] = widget
            
            #4. Ini handling (SECTION PER WIDGET)
            self.config_vars.append(WidgetConfigVars(
                widget_id=widget_id,
                section=f"Widget:{widget_id}",
                var_name=f"{widget_id}__enabled"
            ))
            self.config_vars.append(WidgetConfigVars(
                widget_id=widget_id,
                section=f"Widget:{widget_id}",
                var_name=f"{widget_id}__optional"
            ))                    

            cv = self._get_config_var(widget.folder_script_name, self._widget_var(widget.folder_script_name, "enabled"))
            
            enabled = bool(IniManager().get(key=self.MANAGER_INI_KEY, section=cv.section, var_name=cv.var_name, default=False)) if cv else False
            if enabled:
                widget.enable()
                
            #keep logging minimal
            #self._log_success(f"Discovered: {widget_id}")
            
        except Exception as e:
            self._log_error(f"Failed to discover {widget_id}: {e}")
                            
                
    def _apply_ini_configuration(self):
        """Apply saved enabled states and enforce System widget activation"""
        for wid, w in self.widgets.items():
            vname = self._widget_var(wid, "enabled")
            section = f"Widget:{wid}"
            
            # 1. Read the current state from IniManager (which just loaded from disk)
            enabled = bool(IniManager().get(key=self.MANAGER_INI_KEY, section=section, var_name=vname, default=False))
            
            # 2. THE FORCE: Check if this is a System widget section
            is_system = "Widget:System" in section
            
            if is_system:
                # If it's system but the disk/ini said False, we override it right now
                if not enabled:
                    # Py4GW.Console.Log("WidgetManager", f"Forcing System Widget: {wid}", Py4GW.Console.MessageType.Info)
                    enabled = True
                    # Update IniManager memory so it stays synced
                    IniManager().set(key=self.MANAGER_INI_KEY, section=section, var_name=vname, value=True)
                    # Note: No need to save_vars here unless you want to fix the file immediately; 
                    # the next global save will persist this.
                    self._log_success(f"Enforcing System Widget Enabled: {wid}")
            
            # 3. Final Activation
            if enabled:
                w.enable()
                
    #endregion
    
    #region UI       
    def draw_node(self, INI_KEY: str, node: dict, depth: int = 0):
        style = ImGui.get_style()
        widget_manager = self 

        for key, value in sorted(node.items()):
            # Leaf: render widgets table
            if key == "__widgets__":
                table_id = f"WidgetsTable##tree_depth_{depth}"
                PyImGui.set_next_item_width(-1)  # take full available width

                flags = (
                    PyImGui.TableFlags.Borders |
                    PyImGui.TableFlags.SizingStretchProp |
                    PyImGui.TableFlags.NoSavedSettings
                )

                if ImGui.begin_table(table_id, 2, flags):
                    PyImGui.table_setup_column("Widget", PyImGui.TableColumnFlags.WidthStretch, 1.0)
                    PyImGui.table_setup_column("Cfg", PyImGui.TableColumnFlags.WidthFixed, 40.0)
                    #PyImGui.table_headers_row()

                    for widget_id in value:
                        widget = widget_manager.widgets.get(widget_id)
                        if not widget:
                            continue

                        PyImGui.table_next_row()
                        PyImGui.table_set_column_index(0)

                        display_name = widget.plain_name

                        label = f"{display_name}##{widget_id}"
                        
                        v_enabled = self._widget_var(widget_id, "enabled")
                        # Define the section once to ensure consistency
                        section_name = f"Widget:{widget_id}"

                        # FIXED: Added the section parameter to the get call
                        val = bool(IniManager().get(INI_KEY, v_enabled, False, section=section_name))
                        new_enabled = ImGui.checkbox(label, val)
                        if PyImGui.is_item_hovered():
                            if widget.has_tooltip_property:
                                try:
                                    if widget.tooltip:
                                        widget.tooltip()
                                except Exception as e:
                                    Py4GW.Console.Log("WidgetHandler", f"Error during tooltip of widget {widget_id}: {str(e)}", Py4GW.Console.MessageType.Error)
                                    Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
                            else:
                                PyImGui.show_tooltip(f"Enable/Disable {display_name} widget")

                        if new_enabled != val:
                            # Using consistent section name
                            if new_enabled:
                                widget.enable()
                            else:
                                widget.disable()
                                
                            IniManager().set(key=INI_KEY, var_name=v_enabled, value=widget.enabled, section=section_name)
                            IniManager().save_vars(INI_KEY)

                        PyImGui.table_set_column_index(1)
                        
                        if widget.has_configure_property:
                            configuring = ImGui.toggle_icon_button(
                                IconsFontAwesome5.ICON_COG + f"##Configure{widget_id}",
                                widget.configuring
                            )
                            if configuring != widget.configuring:
                                widget.set_configuring(configuring)
                                
                            if PyImGui.is_item_hovered():
                                PyImGui.show_tooltip("Configure Widget")
                        else:
                            PyImGui.table_set_column_index(1)
                            PyImGui.text_disabled(IconsFontAwesome5.ICON_COG)
                            if PyImGui.is_item_hovered():
                                PyImGui.show_tooltip("No config available")

                    ImGui.end_table()
                continue

            # Folder nodes
            if depth == 0:
                # IMPORTANT: also make header id stable+unique
                open_ = ImGui.collapsing_header(f"{key}##FolderHeader_{key}")
            else:
                if style.Theme not in ImGui.Textured_Themes:
                    style.TextTreeNode.push_color((255, 200, 100, 255))

                open_ = ImGui.tree_node(f"{key}##Tree_{depth}_{key}")

                if style.Theme not in ImGui.Textured_Themes:
                    style.TextTreeNode.pop_color()

            if open_:
                self.draw_node(INI_KEY, value, depth + 1)
                if depth > 0:
                    ImGui.tree_pop()
                    
    def PauseAllWidgets(self):
        for widget in self.widgets.values():
            if widget.enabled:
                widget.disable()
                
    def ResumeAllWidgets(self):
        for widget in self.widgets.values():
            if not widget.enabled:
                widget.enable()
            
    def draw_ui(self, INI_KEY: str):
        if ImGui.icon_button(IconsFontAwesome5.ICON_RETWEET + "##Reload Widgets", 40):
            Py4GW.Console.Log("Widget Manager", "Reloading Widgets...", Py4GW.Console.MessageType.Info)
            
            
            self.widget_initialized = False
            self.discovered = False
            self.discover()
            self.widget_initialized = True    
                
        ImGui.show_tooltip("Reload all widgets")
        PyImGui.same_line(0, 5)
        
        e_all = bool(IniManager().get(key=INI_KEY, var_name="enable_all", default=True, section="Configuration"))
        new_enable_all = ImGui.toggle_icon_button(
            (IconsFontAwesome5.ICON_TOGGLE_ON if e_all else IconsFontAwesome5.ICON_TOGGLE_OFF) + "##widget_disable",
            e_all,
            40
        )

        if new_enable_all != e_all:
            IniManager().set(key= INI_KEY, var_name="enable_all", value=new_enable_all, section="Configuration")
            IniManager().save_vars(INI_KEY)
            if new_enable_all:
                self.ResumeAllWidgets()
            else:
                self.PauseAllWidgets()    
            

        self.enable_all = new_enable_all


        ImGui.show_tooltip(f"{("Run" if not self.enable_all else "Pause")} all widgets")
        
        PyImGui.same_line(0, 5)
        show_widget_ui = ImGui.toggle_icon_button((IconsFontAwesome5.ICON_EYE if self.show_widget_ui else IconsFontAwesome5.ICON_EYE_SLASH) + "##Show Widget UIs", self.show_widget_ui, 40)
        if show_widget_ui != self.show_widget_ui:
            self.set_widget_ui_visibility(show_widget_ui)
        ImGui.show_tooltip(f"{("Show" if not self.show_widget_ui else "Hide")} all widget UIs")
        
        PyImGui.same_line(0, 5)
        pause_non_env = ImGui.toggle_icon_button((IconsFontAwesome5.ICON_PAUSE if self.pause_optional_widgets else IconsFontAwesome5.ICON_PLAY) + "##Pause Non-Env Widgets", not self.pause_optional_widgets, 40)
        if pause_non_env != (not self.pause_optional_widgets):
            if not self.pause_optional_widgets:
                self.pause_widgets()
            else:
                self.resume_widgets()
                
            own_email = Player.GetAccountEmail()
            for acc in GLOBAL_CACHE.ShMem.GetAllAccountData():
                if acc.AccountEmail == own_email:
                    continue
                
                GLOBAL_CACHE.ShMem.SendMessage(own_email, acc.AccountEmail, SharedCommandType.PauseWidgets if self.pause_optional_widgets else SharedCommandType.ResumeWidgets)
            
        ImGui.show_tooltip(f"{("Pause" if not self.pause_optional_widgets else "Resume")} all optional widgets")
        ImGui.separator()
        
        # ------------------------------------------------------------
        # Folder-based Widgets (TREE UI)
        # ------------------------------------------------------------
        tree: dict = {}

        for widget_id, widget in self.widgets.items():
            folder = widget.widget_path  # "A/B/C" or ""
            node = tree

            if folder:
                for part in folder.split("/"):
                    node = node.setdefault(part, {})

            node.setdefault("__widgets__", []).append(widget_id)
            
        self.draw_node(INI_KEY, tree)
    #endregion
        
    def execute_enabled_widgets_update(self):
        profiling = _get_profiling()
        profiling_enabled = profiling.enabled
        pause_optional = self.pause_optional_widgets

        for widget_name, widget_info in self.widgets.items():
            if not widget_info.enabled:
                continue

            if pause_optional and widget_info.optional:
                continue

            if widget_info.update is not None:
                try:
                    if profiling_enabled:
                        profiling.runcall_scope("widgets", f"{widget_name}:update", widget_info.update)
                    else:
                        widget_info.update()
                except Exception as e:
                    Py4GW.Console.Log("WidgetHandler", f"Error executing widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

    def execute_enabled_widgets_draw(self):
        profiling = _get_profiling()
        profiling_enabled = profiling.enabled
        style = ImGui.Selected_Style.pyimgui_style
        alpha = style.Alpha
        ui_enabled = self.show_widget_ui
        pause_optional = self.pause_optional_widgets

        if not ui_enabled:
            style.Alpha = 0.0
            style.Push()

        for widget_name, widget_info in self.widgets.items():
            if not widget_info.enabled:
                continue

            if widget_info.minimal is not None:
                try:
                    if profiling_enabled:
                        profiling.runcall_scope("widgets", f"{widget_name}:minimal", widget_info.minimal)
                    else:
                        widget_info.minimal()
                except Exception as e:
                    Py4GW.Console.Log("WidgetHandler", f"Error executing minimal of widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

            if pause_optional and widget_info.optional:
                continue

            if widget_info.draw is not None:
                try:
                    if profiling_enabled:
                        profiling.runcall_scope("widgets", f"{widget_name}:draw", widget_info.draw)
                    else:
                        widget_info.draw()
                except Exception as e:
                    Py4GW.Console.Log("WidgetHandler", f"Error executing widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

        if not ui_enabled:
            style.Alpha = alpha
            style.Push()

    def execute_enabled_widgets_main(self):
        profiling = _get_profiling()
        profiling_enabled = profiling.enabled
        style = ImGui.Selected_Style.pyimgui_style
        alpha = style.Alpha
        ui_enabled = self.show_widget_ui
        pause_optional = self.pause_optional_widgets

        if not ui_enabled:
            style.Alpha = 0.0
            style.Push()

        for widget_name, widget_info in self.widgets.items():
            if not widget_info.enabled:
                continue

            if widget_info.minimal is not None:
                try:
                    if profiling_enabled:
                        profiling.runcall_scope("widgets", f"{widget_name}:minimal", widget_info.minimal)
                    else:
                        widget_info.minimal()
                except Exception as e:
                    Py4GW.Console.Log("WidgetHandler", f"Error executing minimal of widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

            if pause_optional and widget_info.optional:
                continue

            if widget_info.main is not None:
                try:
                    if profiling_enabled:
                        profiling.runcall_scope("widgets", f"{widget_name}:main", widget_info.main)
                    else:
                        widget_info.main()
                except Exception as e:
                    Py4GW.Console.Log("WidgetHandler", f"Error executing widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)

        if not ui_enabled:
            style.Alpha = alpha
            style.Push()
        
    def execute_configuring_widgets(self):
        for widget_name, widget_info in self.widgets.items():
            if not widget_info.configuring:
                continue
            try:
                if widget_info.configure:
                    widget_info.configure()
                    
            except Exception as e:
                Py4GW.Console.Log("WidgetHandler", f"Error executing widget {widget_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
      
      
    #region  Public API
    def set_widget_ui_visibility(self, visible: bool):
        self.show_ui = visible
        
    def pause_widgets(self):
        self.pause_optionals = True
        
    def resume_widgets(self):
        self.pause_optionals = False
    
    def is_widget_enabled(self, name: str) -> bool:
        widget = self._get_widget_by_plain_name(name)
        return bool(widget and widget.enabled)

    def list_enabled_widgets(self) -> list[str]:
        return [name for name, info in self.widgets.items() if info.enabled]
    
    def enable_widget(self, name: str):
        self._set_widget_state(self.MANAGER_INI_KEY,name, True)

    def disable_widget(self, name: str):
        self._set_widget_state(self.MANAGER_INI_KEY,name, False)
        
    def set_widget_configuring(self, name: str, value: bool = True):
        widget = self._get_widget_by_plain_name(name)
        if not widget:
            Py4GW.Console.Log("WidgetHandler", f"Widget '{name}' not found", Py4GW.Console.MessageType.Warning)
            return
        widget.set_configuring(value)
        
    def get_widget_info(self, name: str) -> Widget | None:
        # 1) direct full id lookup
        w = self.widgets.get(name, None)
        if w:
            return w

        # 2) fallback to plain_name lookup
        return self._get_widget_by_plain_name(name)
    #endregion
#endregion

_widget_handler = WidgetHandler()

def get_widget_handler() -> WidgetHandler:
    return _widget_handler