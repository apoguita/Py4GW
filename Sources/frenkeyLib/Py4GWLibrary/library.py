import os
import traceback
import Py4GW
import PyImGui

from Py4GWCoreLib import ImGui
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.HotkeyManager import HOTKEY_MANAGER, HotKey
from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
from Py4GWCoreLib.ImGui_src.Style import Style
from Py4GWCoreLib.IniManager import IniManager
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.enums_src.IO_enums import Key, ModifierKey
from Py4GWCoreLib.enums_src.Multiboxing_enums import SharedCommandType
from Py4GWCoreLib.py4gwcorelib_src.Color import Color
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import Widget, WidgetHandler
from Sources.frenkeyLib.Py4GWLibrary.enum import SortMode, LayoutMode, ViewMode

class ModuleBrowser:
    CATEGORY_COLUMN_MAX_WIDTH = 150
    SYSTEM_COLOR = Color(255, 0, 0, 255)
    IMAGE_SIZE = 40
    PADDING = 10
    TAG_HEIGHT = 18
    BUTTON_HEIGHT = 24
    
    def __init__(self, ini_key: str, module_name: str, widget_manager : WidgetHandler):
        self.ini_key = ini_key
        self.module_name = module_name
        self.widget_manager = widget_manager
        self.widget_filter = ""
        
        self.view_mode = ViewMode.All
        self.layout_mode = LayoutMode.Minimalistic
        self.sort_mode = SortMode.ByName
        
        self.widgets : list[Widget] = list(self.widget_manager.widgets.values())
        self.filtered_widgets : list[Widget] = []
        self.favorites : list[Widget] = []
                
        self.category : str = ""
        # get unique categories sorted alphabetically
        self.categories : list[str] = sorted(set(widget.category for widget in self.widgets if widget.category))
        
        self.tag : str = ""
        self.tags : list[str] = sorted(set(tag for widget in self.widgets for tag in widget.tags if widget.tags))
        
        self.win_size = (200, 45)
        self.ui_active = False
        self.focus_search = False
        self.popup_opened = False
        
        self.context_menu_widget = None
        self.context_menu_id = ""
        
        self.default_layout = LayoutMode.Minimalistic
        self.show_configure_button = True
        self.show_images = True
        self.show_separator = True
        self.show_category = True
        self.show_tags = True
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
    
    def load_config(self):
        
        try:
            self.default_layout = LayoutMode[IniManager().read_key(key=self.ini_key, section="Configuration", name="default_layout", default=LayoutMode.Compact.name)]
            self.set_layout_mode(self.default_layout)
            
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
    
    def add_to_favorites(self, widget : Widget):
        if widget not in self.favorites:
            self.favorites.append(widget)
            IniManager().set(key=self.ini_key, var_name="favorites", value=",".join(w.folder_script_name for w in self.favorites), section="Favorites")
            IniManager().save_vars(self.ini_key)
            
    def remove_from_favorites(self, widget : Widget):
        if widget in self.favorites:
            self.favorites.remove(widget)
            IniManager().set(key=self.ini_key, var_name="favorites", value=",".join(w.folder_script_name for w in self.favorites), section="Favorites")
            IniManager().save_vars(self.ini_key)
    
    def set_layout_mode(self, mode : LayoutMode):
        self.layout_mode = mode
        match mode:
            case LayoutMode.Library:
                self.win_size = (800, 600)
            case LayoutMode.Compact:
                self.win_size = (300, 80)
            case LayoutMode.Minimalistic:
                self.win_size = (200, 45)
        pass

    def set_search_focus(self):
        match self.layout_mode:
            case LayoutMode.Library:
                self.focus_search = True
                
            case LayoutMode.Compact | LayoutMode.Minimalistic:
                self.set_layout_mode(LayoutMode.Compact)
                self.focus_search = True

    def draw_window(self): 
        win_size = self.win_size
        
        
        match self.layout_mode:
            case LayoutMode.Library:
                self.draw_libary()
            case LayoutMode.Compact:
                self.compact_view()  
            case LayoutMode.Minimalistic:
                self.minimalistic_view()

        if self.first_run:    
            self.win_size = win_size                    
            self.first_run = False
        
    def filter_widgets(self, filter_text: str):        
        self.filtered_widgets.clear()     
        prefiltered = self.widgets.copy()
        
        keywords = [kw.strip().lower() for kw in filter_text.lower().strip().split(";")]
        
        preset_words = [
            "enabled", "active", "on",
            "disabled", "inactive", "off",
            "favorites", "favs", "fav",
            "system", "sys"]
        
        enabled_check = False
        disabled_check = False
        favorites_check = False
        system_check = False
        
        for kw in list(keywords):            
            enabled_check = enabled_check or kw == "enabled" or kw == "active" or kw == "on"
            disabled_check = disabled_check or kw == "disabled" or kw == "inactive" or kw == "off"
            favorites_check = favorites_check or kw == "favorites" or kw == "favs" or kw == "fav"
            system_check = system_check or kw == "system" or kw == "sys"
            
            prefiltered = [w for w in prefiltered if 
                            (not enabled_check or w.enabled) and
                            (not disabled_check or not w.enabled) and
                            (not favorites_check or w in self.favorites) and
                            (not system_check or w.category == "System")]
            
            if kw in preset_words:
                keywords.remove(kw)
            
        
        match self.layout_mode:
            case LayoutMode.Library:
                match self.view_mode:
                    case ViewMode.Favorites:
                        prefiltered = [w for w in prefiltered if w in self.favorites]
                        
                    case ViewMode.Actives:
                        prefiltered = [w for w in self.widgets if w.enabled]
                        
                    case ViewMode.Inactives:
                        prefiltered = [w for w in self.widgets if not w.enabled]
                
                self.filtered_widgets = [w for w in prefiltered if 
                                        (w.category == self.category or not self.category) and 
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

    def draw_toggle_view_mode_button(self):
        match self.layout_mode:
            case LayoutMode.Library:
                if ImGui.icon_button(IconsFontAwesome5.ICON_BARS, 28, 24):
                    self.set_layout_mode(LayoutMode.Compact)
                    
                ImGui.show_tooltip("Switch to Compact View")
                    
            case LayoutMode.Compact:
                if ImGui.icon_button(IconsFontAwesome5.ICON_TH_LIST, 28, 24):
                    self.set_layout_mode(LayoutMode.Library)
                    
                ImGui.show_tooltip("Switch to Library View")
    
    def draw_global_toggles(self, button_width : float, spacing : float):       
        if ImGui.icon_button(IconsFontAwesome5.ICON_RETWEET + "##Reload Widgets", button_width):
            Py4GW.Console.Log("Widget Manager", "Reloading Widgets...", Py4GW.Console.MessageType.Info)
            self.widget_manager.discovered = False
            self.widget_manager.discover()
                
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
    
    def minimalistic_view(self):
        PyImGui.set_next_window_size(self.win_size, PyImGui.ImGuiCond.Always)
        
        if self.focus_search:
            PyImGui.set_next_window_focus()
            
        if ImGui.Begin(ini_key=self.ini_key, name=self.module_name, flags=PyImGui.WindowFlags(PyImGui.WindowFlags.NoResize|PyImGui.WindowFlags.NoTitleBar)):   
            win_size = PyImGui.get_window_size()
            self.win_size = (win_size[0], win_size[1])
            style = ImGui.get_style()
            
            spacing = 5
            width = win_size[0] - style.WindowPadding.value1 * 2
            button_width = self.get_button_width(width, 5, spacing)            
            if ImGui.icon_button(IconsFontAwesome5.ICON_SEARCH + "##FocusSearch", button_width):
                self.set_layout_mode(LayoutMode.Compact)
            
            ImGui.show_tooltip("Search widgets")
            
            PyImGui.same_line(0, spacing)            
            self.draw_global_toggles(button_width, spacing)
                            
        ImGui.End(self.ini_key)
            
    def draw_presets_button(self) -> bool:
        if ImGui.icon_button(IconsFontAwesome5.ICON_FILTER, 28, 24):
            if not self.popup_opened:
                PyImGui.open_popup("PreSets##WidgetBrowser")
                self.popup_opened = True
                Py4GW.Console.Log("Widget Browser", "Opening presets popup", Py4GW.Console.MessageType.Info)
            
        self.popup_opened = PyImGui.begin_popup("PreSets##WidgetBrowser")
        if self.popup_opened:
            if ImGui.menu_item("Show Enabled"):
                self.widget_filter = "enabled; "
                self.focus_search = True
                self.filter_widgets(self.widget_filter)
            
            if ImGui.menu_item("Show Favorites"):
                self.widget_filter = "favorites; "
                self.focus_search = True
                self.filter_widgets(self.widget_filter)
                
            if ImGui.menu_item("Show System"):
                self.widget_filter = "system; "  
                self.focus_search = True
                self.filter_widgets(self.widget_filter)
            
            PyImGui.end_popup()   
                    
        return self.popup_opened
            
    def compact_view(self):
        PyImGui.set_next_window_size(self.win_size, PyImGui.ImGuiCond.Always)
        
        if self.focus_search:
            PyImGui.set_next_window_focus()
            
        if ImGui.Begin(ini_key=self.ini_key, name=self.module_name, flags=PyImGui.WindowFlags.NoResize | PyImGui.WindowFlags.NoTitleBar):   
            window_hovered = PyImGui.is_window_hovered() or PyImGui.is_window_focused()
            win_size = PyImGui.get_window_size()
            self.win_size = (win_size[0], win_size[1])
            style = ImGui.get_style()
            width = win_size[0] - style.WindowPadding.value1 * 2
            
            spacing = 5
            button_width = self.get_button_width(width, 4, spacing)     
            self.draw_global_toggles(button_width, spacing)
            ImGui.separator()
            self.draw_toggle_view_mode_button()   
            PyImGui.same_line(0, spacing)      
            
            search_width = PyImGui.get_content_region_avail()[0] - 30
            PyImGui.push_item_width(search_width)
            changed, self.widget_filter = ImGui.search_field("##WidgetFilter", self.widget_filter)
            if changed:
                self.filter_widgets(self.widget_filter)
            PyImGui.pop_item_width()
            search_active = PyImGui.is_item_active()
            
            if self.focus_search:
                PyImGui.set_keyboard_focus_here(-1)
                self.focus_search = False
            
            PyImGui.same_line(0, spacing)
            
            presets_opened = self.draw_presets_button()      
            window_hovered = PyImGui.is_window_hovered() or PyImGui.is_window_focused() or PyImGui.is_item_hovered() or window_hovered 
            
            
            if not self.draw_suggestions(win_size, style, search_active, window_hovered, presets_opened) and not search_active and not window_hovered and not presets_opened:
                self.widget_filter = ""
                self.filtered_widgets.clear()
                
                if self.default_layout is LayoutMode.Minimalistic:
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

            height = min(200, len(self.filtered_widgets) * 30 + (style.ItemSpacing.value2 or 0) + (style.WindowPadding.value2 or 0) * 2)
            PyImGui.set_next_window_size((win_size[0], height),
                    PyImGui.ImGuiCond.Always
                )
                
            suggestion_hovered = False
            if PyImGui.begin(
                    "##WidgetsList",
                    False,
                    PyImGui.WindowFlags(PyImGui.WindowFlags.NoTitleBar
                    | PyImGui.WindowFlags.NoMove
                    | PyImGui.WindowFlags.NoResize
                    | PyImGui.WindowFlags.NoSavedSettings
                    | PyImGui.WindowFlags.NoFocusOnAppearing
                )):
                suggestion_hovered = PyImGui.is_window_hovered()
                card_width = PyImGui.get_content_region_avail()[0]
                open = True
                    
                for widget in self.filtered_widgets:
                    suggestion_hovered = self.draw_compact_widget_card(widget, card_width) or suggestion_hovered
                    if PyImGui.is_item_clicked(0):
                        self.filter_widgets(self.widget_filter)
                        self.focus_search = True
                        
                        # ---- RIGHT CLICK DETECTION ----
                    if PyImGui.is_item_hovered() and PyImGui.is_mouse_clicked(1):
                        self.context_menu_id = f"WidgetContext##{widget.folder_script_name}"
                        self.context_menu_widget = widget
                        PyImGui.open_popup(self.context_menu_id)
                        
                if self.context_menu_id and self.context_menu_widget:
                    self.card_context_menu(self.context_menu_id, self.context_menu_widget)
                            
                if suggestion_hovered and not self.context_menu_id and not search_active and not self.focus_search and not presets_opened:
                    Py4GW.Console.Log("Widget Browser", "set_window_focus to ##WidgetsList", Py4GW.Console.MessageType.Info)
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
            
        return open
    
    def card_context_menu(self, popup_id: str, widget : Widget):
        
        if PyImGui.begin_popup(popup_id):
            if PyImGui.menu_item("Add to Favorites" if widget not in self.favorites else "Remove from Favorites"):
                if widget not in self.favorites:
                    self.add_to_favorites(widget)
                else:
                    self.remove_from_favorites(widget)
                
            PyImGui.separator()
            
            if PyImGui.menu_item("Enable" if not widget.enabled else "Disable"):
                if not widget.enabled:
                    widget.enable()
                else:
                    widget.disable()
                    
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
    
    def draw_libary(self):
        PyImGui.set_next_window_size(self.win_size, PyImGui.ImGuiCond.Always)
        if ImGui.Begin(ini_key=self.ini_key, name=self.module_name, flags=PyImGui.WindowFlags.MenuBar):    
            io = PyImGui.get_io()
            win_size = PyImGui.get_window_size()
            win_pos = PyImGui.get_window_pos()
            self.win_size = (win_size[0], win_size[1])
            pos_y = 0
            style = ImGui.get_style()
            
            if ImGui.begin_menu_bar():
                pos_y = PyImGui.get_cursor_pos_y()
                if ImGui.begin_menu("Widgets"):
                    if ImGui.menu_item("Reload Widgets"):
                        Py4GW.Console.Log("Widget Manager", "Reloading Widgets...", Py4GW.Console.MessageType.Info)
                        self.widget_manager.discovered = False
                        self.widget_manager.discover()
                    
                    if ImGui.menu_item(f"{("Run" if not self.widget_manager.enable_all else "Pause")} all widgets"):
                        self.widget_manager.enable_all = not self.widget_manager.enable_all
                        IniManager().save_vars(self.ini_key)
                        IniManager().set(key=self.ini_key, var_name="enable_all", value=self.widget_manager.enable_all, section="Configuration")
                    
                    if ImGui.menu_item(f"{("Show" if not self.widget_manager.show_widget_ui else "Hide")} all widget UIs"):
                        show_widget_ui = not self.widget_manager.show_widget_ui
                        self.widget_manager.set_widget_ui_visibility(show_widget_ui)
                        
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
                        
                    ImGui.end_menu()                   
                
                if ImGui.begin_menu("Preferences"):
                    if ImGui.begin_menu("Default Layout Mode"):
                        layout_mode = ImGui.radio_button("Library View", self.default_layout, LayoutMode.Library)
                        if self.default_layout != layout_mode:
                            self.default_layout = LayoutMode.Library
                            self.set_layout_mode(self.default_layout)
                            IniManager().set(key=self.ini_key, var_name="default_layout", value=self.default_layout.name, section="Configuration")
                            IniManager().save_vars(self.ini_key)
                        ImGui.show_tooltip("Open the widget browser in library view by default,\nshowing all details and options for each widget.")
                            
                        layout_mode = ImGui.radio_button("Compact View", self.default_layout, LayoutMode.Compact)
                        if self.default_layout != layout_mode:
                            self.default_layout = LayoutMode.Compact
                            self.set_layout_mode(self.default_layout)
                            IniManager().set(key=self.ini_key, var_name="default_layout", value=self.default_layout.name, section="Configuration")
                            IniManager().save_vars(self.ini_key)
                        ImGui.show_tooltip("Open the widget browser in compact view by default,\nshowing a simplified card for each widget.")
                            
                        layout_mode = ImGui.radio_button("Minimalistic View", self.default_layout, LayoutMode.Minimalistic)
                        if self.default_layout != layout_mode:
                            self.default_layout = LayoutMode.Minimalistic
                            self.set_layout_mode(self.default_layout)
                            IniManager().set(key=self.ini_key, var_name="default_layout", value=self.default_layout.name, section="Configuration")
                            IniManager().save_vars(self.ini_key)
                        ImGui.show_tooltip("Open the widget browser in minimalistic view by default,\nshowing only a search icon which switches to compact view when clicked.\nIf the widget filter is cleared while in compact view, it will switch back to minimalistic view.")
                        
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
                        if key != self.focus_keybind.key or modifiers != self.focus_keybind.modifiers:
                            self.focus_keybind.key = key
                            self.focus_keybind.modifiers = modifiers
                            
                            IniManager().set(self.ini_key, var_name="hotkey", section="Configuration", value=self.focus_keybind.key.name)
                            IniManager().set(self.ini_key, var_name="hotkey_modifiers", section="Configuration", value=self.focus_keybind.modifiers.name)
                            IniManager().save_vars(self.ini_key)
                        
                        ImGui.show_tooltip("Set the hotkey used to focus the search field in the widget browser.\nPressing this hotkey will move the keyboard focus to the search field, allowing you to start typing immediately to filter widgets.")
                        ImGui.separator()
                        
                        if ImGui.menu_item("Clear Keybinds"):
                            self.focus_keybind.key = Key.Unmapped
                            self.focus_keybind.modifiers = ModifierKey.NoneKey
                                                        
                            IniManager().set(self.ini_key, var_name="hotkey", section="Configuration", value="")
                            IniManager().set(self.ini_key, var_name="hotkey_modifiers", section="Configuration", value="")
                            IniManager().save_vars(self.ini_key)
                            
                        ImGui.show_tooltip("Clear all keybinds, resetting them to their default unbound state.")
                            
                        ImGui.end_menu()
                    ImGui.end_menu()
                ImGui.end_menu_bar()
            
            self.draw_toggle_view_mode_button()   
            PyImGui.same_line(0, 5)    
            search_width = PyImGui.get_content_region_avail()[0] - 32
            PyImGui.push_item_width(search_width)
            changed, self.widget_filter = ImGui.search_field("##WidgetFilter", self.widget_filter)
            if self.focus_search:
                PyImGui.set_keyboard_focus_here(-1)
                self.focus_search = False
            PyImGui.pop_item_width()
            if changed:
                self.filter_widgets(self.widget_filter)
            
            PyImGui.same_line(0, 5)
            self.draw_sorting_button()    
            
            ImGui.separator()
            
            if ImGui.begin_table("navigation_view", 2, PyImGui.TableFlags.SizingStretchProp | PyImGui.TableFlags.BordersInnerV):
                max_width = PyImGui.get_content_region_avail()[0]
                                
                PyImGui.table_setup_column("##categories", PyImGui.TableColumnFlags.WidthFixed, min(self.CATEGORY_COLUMN_MAX_WIDTH, max_width * 0.5))
                PyImGui.table_setup_column("##widgets", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_next_row()
                
                PyImGui.table_set_column_index(0)
                if ImGui.begin_child("##category_list", (0, 0)):      
                    if ImGui.selectable("All", self.view_mode is ViewMode.All):
                        self.view_mode = ViewMode.All if not self.view_mode is ViewMode.All else ViewMode.All
                        self.filter_widgets(self.widget_filter)            
                        
                    if ImGui.selectable("Favorites", self.view_mode is ViewMode.Favorites):
                        self.view_mode = ViewMode.Favorites if not self.view_mode is ViewMode.Favorites else ViewMode.All
                        self.filter_widgets(self.widget_filter)
                        
                    if ImGui.selectable("Active", self.view_mode is ViewMode.Actives):
                        self.view_mode = ViewMode.Actives if not self.view_mode is ViewMode.Actives else ViewMode.All
                        self.filter_widgets(self.widget_filter)
                        
                    if ImGui.selectable("Inactive", self.view_mode is ViewMode.Inactives):
                        self.view_mode = ViewMode.Inactives if not self.view_mode is ViewMode.Inactives else ViewMode.All
                        self.filter_widgets(self.widget_filter)
                        
                    ImGui.separator()
                    
                    for category in self.categories:
                        if ImGui.selectable(category, category == self.category):                            
                            self.category = category if category != self.category else ""     
                              
                            if not io.key_ctrl:
                                self.tag = ""
                                                     
                            self.filter_widgets(self.widget_filter)
                    
                    ImGui.separator()
                    style.ScrollbarSize.push_style_var(5)
                    if ImGui.begin_child("##tags", (0, 0)):  
                        for tag in self.tags:
                            if ImGui.selectable(f"{tag}", tag == self.tag):
                                self.tag = tag if tag != self.tag else ""  
                                if not io.key_ctrl:
                                    self.category = ""
                                self.filter_widgets(self.widget_filter)
                                
                    PyImGui.end_child()
                    style.ScrollbarSize.pop_style_var()
                ImGui.end_child()
                
                PyImGui.table_set_column_index(1)
                
                if ImGui.begin_child("##widgets", (0, 0)):  
                    style.DisabledAlpha.push_style_var(0.4)
                    
                    min_card_width = self.card_width if self.fixed_card_width else 250
                    available_width = PyImGui.get_content_region_avail()[0] - (style.ScrollbarSize.value1 if PyImGui.get_scroll_y() == 0 else 0)
                    num_columns = max(1, int(available_width // min_card_width))
                    card_width = 0
                    PyImGui.columns(num_columns, "widget_cards", False)
                    card_height = self.get_card_height()
                            
                    for widget in (self.filtered_widgets):
                        card_width = self.card_width if self.fixed_card_width else PyImGui.get_content_region_avail()[0]
                        
                        self.draw_widget_card(widget, card_width, card_height, widget in self.favorites)
                        if PyImGui.is_item_clicked(0):
                            self.filter_widgets(self.widget_filter)
                                                                        
                        popup_id = f"WidgetContext##{widget.folder_script_name}"
                        # ---- RIGHT CLICK DETECTION ----
                        if PyImGui.is_item_hovered() and PyImGui.is_mouse_clicked(1):
                            PyImGui.open_popup(popup_id)

                        # ---- CONTEXT MENU ----
                        self.card_context_menu(popup_id, widget)
                        
                        PyImGui.next_column()
                                            
                        
                    style.DisabledAlpha.pop_style_var()
                    PyImGui.end_columns()
                    
                ImGui.end_child()
                ImGui.end_table()
                
        ImGui.End(self.ini_key)
        

    def _push_card_style(self, style : Style, enabled : bool):
        style.ChildBg.push_color(self.card_enabled_color.rgb_tuple if enabled else self.card_color.rgb_tuple)
        style.ChildBorderSize.push_style_var(2.0 if enabled else 1.0) 
        style.ChildRounding.push_style_var(self.card_rounding)
        style.Border.push_color(self.card_enabled_color.opacity(0.6).rgb_tuple if enabled else self.card_color.opacity(0.6).rgb_tuple)
        pass

    def _pop_card_style(self, style : Style):
        style.ChildBg.pop_color()
        style.ChildBorderSize.pop_style_var()
        style.ChildRounding.pop_style_var()
        style.Border.pop_color()
        pass

    def _push_tag_style(self, style : Style, color : tuple):
        style.FramePadding.push_style_var(4, 4)
        style.Button.push_color(color)
        style.ButtonHovered.push_color(color)
        style.ButtonActive.push_color(color)
        ImGui.push_font("Regular", 12)

    def _pop_tag_style(self, style : Style):
        style.FramePadding.pop_style_var()
        style.Button.pop_color()
        style.ButtonHovered.pop_color()
        style.ButtonActive.pop_color()
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

    def draw_widget_card(self, widget : Widget, width : float, height: float, is_favorite: bool = False):
        """
        Draws a single widget card.
        Must be called inside a grid / SameLine layout.
        """
        style = ImGui.get_style()
        self._push_card_style(style, widget.enabled)
        
        opened = PyImGui.begin_child(
            f"##widget_card_{widget.folder_script_name}",
            (width, height),
            border=True,
            flags=PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse
        )
        
        if opened and PyImGui.is_rect_visible(width, height):
            available_width = PyImGui.get_content_region_avail()[0]
            
            # --- Top Row: Icon + Title ---
            PyImGui.begin_group()

            # Icon
            if self.show_images:
                ImGui.image(widget.image, (self.IMAGE_SIZE, self.IMAGE_SIZE), border_color=self.category_color.rgb_tuple)
                PyImGui.same_line(0, 5)

            # Title + Category
            PyImGui.begin_group()
            # ImGui.push_font("Regular", 16)
            name = ImGui.trim_text_to_width(text=f"{widget.name}", max_width=width - self.IMAGE_SIZE - self.BUTTON_HEIGHT - self.PADDING * 4 - (15 if is_favorite else 0))
            if is_favorite:
                ImGui.text_colored(f"{IconsFontAwesome5.ICON_STAR} ", self.favorites_color.color_tuple, font_size=10)
                PyImGui.same_line(0, 3)
                
            ImGui.text_colored(name, self.name_color.color_tuple if not widget.enabled else self.name_enabled_color.color_tuple)
            # ImGui.pop_font()
            

            if self.show_separator:
                PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 4)
                PyImGui.separator()
                
            if self.show_category:
                PyImGui.set_cursor_pos_y(PyImGui.get_cursor_pos_y() - 2)
                ImGui.text_colored(f"{widget.category}", self.category_color.color_tuple if widget.category != "System" else self.SYSTEM_COLOR.color_tuple, 12)

            PyImGui.end_group()
                    
            if widget.has_configure_property:
                PyImGui.set_cursor_pos(available_width - 10, 2)
                ImGui.toggle_icon_button(IconsFontAwesome5.ICON_COG, widget.configuring, self.BUTTON_HEIGHT, self.BUTTON_HEIGHT)
            PyImGui.end_group()

            if self.show_tags:
                # --- Tags ---
                self._push_tag_style(style, self.tag_color.rgb_tuple)
                PyImGui.begin_group()
                for i, tag in enumerate(widget.tags):
                    if i > 0:
                        PyImGui.same_line(0, 2)

                    PyImGui.button(tag)
                PyImGui.end_group()
                self._pop_tag_style(style)


        PyImGui.end_child()
        clicked = False
        hovered = False
        self._pop_card_style(style)
        
        if PyImGui.is_item_clicked(0):
            clicked = True
            widget.enable() if not widget.enabled else widget.disable()
            
        if PyImGui.is_item_hovered():
            hovered = True
            if widget.has_tooltip_property:
                try:
                    if widget.tooltip:
                        widget.tooltip()
                except Exception as e:
                    Py4GW.Console.Log("WidgetHandler", f"Error during tooltip of widget {widget.folder_script_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
            else:
                PyImGui.show_tooltip(f"Enable/Disable {widget.name} widget")

        return clicked or hovered
        
    def draw_compact_widget_card(self, widget : Widget, width : float) -> bool:
        """
        Draws a single widget card.
        Must be called inside a grid / SameLine layout.
        """

        style = ImGui.get_style()
        self._push_card_style(style, widget.enabled)
        
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
                ImGui.toggle_icon_button(IconsFontAwesome5.ICON_COG, widget.configuring, self.BUTTON_HEIGHT, self.BUTTON_HEIGHT)

        PyImGui.end_child()
        self._pop_card_style(style)
        clicked = False
        hovered = False
        
        if PyImGui.is_item_clicked(0):
            clicked = True
            widget.enable() if not widget.enabled else widget.disable()
            
        if PyImGui.is_item_hovered():
            hovered = True
            if widget.has_tooltip_property:
                try:
                    if widget.tooltip:
                        widget.tooltip()
                except Exception as e:
                    Py4GW.Console.Log("WidgetHandler", f"Error during tooltip of widget {widget.folder_script_name}: {str(e)}", Py4GW.Console.MessageType.Error)
                    Py4GW.Console.Log("WidgetHandler", f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
            else:
                PyImGui.show_tooltip(f"Enable/Disable {widget.name} widget")

        return clicked or hovered
        