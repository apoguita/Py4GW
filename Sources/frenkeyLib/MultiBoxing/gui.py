import ctypes
from typing import Optional
from Py4GW import Console
import PyImGui
from Py4GWCoreLib import ImGui, Overlay
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.GlobalCache.SharedMemory import AccountStruct
from Py4GWCoreLib.ImGui_src.Style import Style
from Py4GWCoreLib.ImGui_src.IconsFontAwesome5 import IconsFontAwesome5
from Py4GWCoreLib.enums_src.GameData_enums import Profession, ProfessionShort
from Py4GWCoreLib.enums_src.IO_enums import Key
from Py4GWCoreLib.py4gwcorelib_src import Utils
from Py4GWCoreLib.py4gwcorelib_src.Color import Color, ColorPalette
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.WidgetManager import get_widget_handler
from Sources.frenkeyLib.MultiBoxing.enum import RenameClientType
from Sources.frenkeyLib.MultiBoxing.messaging import position_clients
from Sources.frenkeyLib.MultiBoxing.region import Region
from Sources.frenkeyLib.MultiBoxing.settings import Settings
from Sources.frenkeyLib.MultiBoxing.window_handling import set_window_active

## Set the MODULE_NAME to the folder
MODULE_NAME = __file__.split("\\")[-2]

class GUI:
    _instance = None
    def __new__(cls, configure_window: ImGui.WindowModule, access_window: ImGui.WindowModule):
        if cls._instance is None:
            cls._instance = super(GUI, cls).__new__(cls)         
            cls._instance.__init__(configure_window, access_window)   
            
        return cls._instance
    
    def __init__(self, configure_window: ImGui.WindowModule, access_window: ImGui.WindowModule):
        self.settings = Settings()
        self.overlay : Overlay = Overlay()
        self.screen_width = self.overlay.GetDisplaySize().x
        
        self.configure_window = configure_window
        self.access_window = access_window
        self.widget_handler = get_widget_handler()
        self.module_info = None
        self.layout_name = ""
        self.layout_index : int = 0
    
    def get_module_info(self, module_name: str):
        if not self.module_info:
            self.module_info = self.widget_handler.get_widget_info(module_name)

        return self.module_info

    def ensure_regions_within_bounds(self, regions: list[Region]):
        for region in regions:
            region.x = max(0, min(region.x, self.settings.screen_size[0] - region.w))
            region.y = max(0, min(region.y, self.settings.screen_size[1] - region.h))
            region.w = min(region.w, self.settings.screen_size[0])
            region.h = min(region.h, self.settings.screen_size[1])

    def draw_row_icon(self, width, height, rows: int = 4, even_color: Optional[Color] = None, odd_color: Optional[Color] = None):
        PyImGui.dummy(width, height)
        
        item_rect_min = PyImGui.get_item_rect_min()
        item_rect_max = PyImGui.get_item_rect_max()
        
        x, y = item_rect_min
        width = item_rect_max[0] - item_rect_min[0]
        height = item_rect_max[1] - item_rect_min[1]
        
        even_color = even_color if even_color else Color(200, 200, 200, 200)
        odd_color = odd_color if odd_color else Color(100, 100, 100, 100)
        
        style = ImGui.get_style()
        
        for i in range(rows):
            # draw every uneven row        
                PyImGui.draw_list_add_rect_filled(
                    x, y + (i * (height / rows)),
                    x + width, y + ((i + 1) * (height / rows)),
                    (even_color if i % 2 == 0 else odd_color).color_int,
                    style.FrameRounding.get_current().value1,
                    PyImGui.DrawFlags.RoundCornersAll
                )

    def draw_column_icon(self, width, height, columns: int = 4, even_color: Optional[Color] = None, odd_color: Optional[Color] = None):
        PyImGui.dummy(width, height)
        
        item_rect_min = PyImGui.get_item_rect_min()
        item_rect_max = PyImGui.get_item_rect_max()
        
        x, y = item_rect_min
        width = item_rect_max[0] - item_rect_min[0]
        height = item_rect_max[1] - item_rect_min[1]
        
        even_color = even_color if even_color else Color(200, 200, 200, 200)
        odd_color = odd_color if odd_color else Color(100, 100, 100, 100)
        
        style = ImGui.get_style()
        
        for i in range(columns):
            # draw every uneven row        
                PyImGui.draw_list_add_rect_filled(
                    x + (i * (width / columns)), y,
                    x + ((i + 1) * (width / columns)), y + height,
                    (even_color if i % 2 == 0 else odd_color).color_int,
                    style.FrameRounding.get_current().value1,
                    PyImGui.DrawFlags.RoundCornersAll
                )

    def draw_configure_window(self):
        module_info = self.get_module_info(MODULE_NAME)
        self.configure_window.open = module_info.configuring if module_info else False

        if self.configure_window.begin(None):
            self.configure_window.window_flags = PyImGui.WindowFlags.NoFlag
            style = ImGui.get_style()
        
            style.CellPadding.push_style_var(5, 0)
            
            regions_width = 300
            header_height = 105
            
            if ImGui.begin_tab_bar("multiboxing_config_tabs"):
                if ImGui.begin_tab_item("Configuration"):
        
                    ImGui.text("Client Renaming", 16, "Bold")
                    ImGui.separator()
                    
                    rename_to = ImGui.combo("Rename To", self.settings.rename_to.value, [e.name.replace("_", " ") for e in RenameClientType])
                    if rename_to != self.settings.rename_to.value:
                        self.settings.rename_to = RenameClientType(rename_to)
                        self.settings.save_settings()

                    append_gw = ImGui.checkbox("Append GW", self.settings.append_gw)
                    if append_gw != self.settings.append_gw:
                        self.settings.append_gw = append_gw
                        self.settings.save_settings()
                        
                    PyImGui.spacing()
                    PyImGui.spacing()
                    
                    ImGui.text("Account Order", 16, "Bold")
                    ImGui.separator()
                    
                    for pos, acc in enumerate(self.settings.accounts_order):
                        if ImGui.begin_child(f"account_order_{acc}", (0, 25), border=False, flags=PyImGui.WindowFlags.NoFlag):
                            if ImGui.icon_button(IconsFontAwesome5.ICON_ARROW_UP, 20, 20):
                                self.settings.move_account(pos, pos - 1)
                            ImGui.show_tooltip("Move account up")
                            
                            PyImGui.same_line(0, 3)
                            if ImGui.icon_button(IconsFontAwesome5.ICON_ARROW_DOWN, 20, 20):
                                self.settings.move_account(pos, pos + 1)
                            ImGui.show_tooltip("Move account down")
                            
                            PyImGui.same_line(0, 10)
                            ImGui.text(acc)
                            
                        ImGui.end_child()
                        
                        
                    
                    ImGui.end_tab_item()
                    
                if ImGui.begin_tab_item("Layout"): 
                    if ImGui.begin_table("layout_table", 2, PyImGui.TableFlags.NoFlag, 0, 0):
                        PyImGui.table_setup_column("left", PyImGui.TableColumnFlags.NoFlag, 0.5)
                        PyImGui.table_setup_column("right", PyImGui.TableColumnFlags.WidthFixed, regions_width)
                        
                        PyImGui.table_next_row()
                        PyImGui.table_next_column()
                        card_background = style.WindowBg.opacify(0.6).to_tuple()
                        
                        def draw_configs():                    
                            style.ChildBg.push_color(card_background)
                            if ImGui.begin_child("configs", (300, header_height), border=True, flags=PyImGui.WindowFlags.NoScrollbar):      

                                snap_to_edges = ImGui.checkbox("Snap to edges", self.settings.snap_to_edges)
                                if snap_to_edges != self.settings.snap_to_edges:
                                    self.settings.snap_to_edges = snap_to_edges
                                    self.settings.save_settings()
                                    
                                hide_widgets_on_slave = ImGui.checkbox("Hide widgets on slave", self.settings.hide_widgets_on_slave)
                                if hide_widgets_on_slave != self.settings.hide_widgets_on_slave:
                                    self.settings.hide_widgets_on_slave = hide_widgets_on_slave
                                    self.settings.save_settings()
                                    
                                show_overview = ImGui.checkbox("Show Overlay", self.settings.show_overview)
                                if show_overview != self.settings.show_overview:
                                    self.settings.show_overview = show_overview
                                    self.settings.save_settings()
                                    
                            style.ChildBg.pop_color()
                            ImGui.end_child() 

                        def draw_screen_size(avail):
                            ImGui.text_centered("Screen Size", avail[0])
                            ImGui.separator()
                                        
                            style.ItemSpacing.push_style_var(0, 0)
                            style.CellPadding.push_style_var(0, 0)
                                
                            if ImGui.begin_table("screen_size_table", 3, PyImGui.TableFlags.NoFlag, avail[0] - 5, 25):
                                PyImGui.table_setup_column("Width", PyImGui.TableColumnFlags.NoFlag, 0.5)
                                PyImGui.table_setup_column("x", PyImGui.TableColumnFlags.WidthFixed, 30)
                                PyImGui.table_setup_column("Height", PyImGui.TableColumnFlags.NoFlag, 0.5)
                                    
                                PyImGui.table_next_row()
                                PyImGui.table_next_column()
                                    
                                PyImGui.push_item_width(PyImGui.get_content_region_avail()[0] - 15)
                                swidth = ImGui.input_int("##width", self.settings.screen_size[0], 800, 10, PyImGui.InputTextFlags.AutoSelectAll)
                                if swidth != self.settings.screen_size[0]:
                                    self.settings.screen_size = (max(800, swidth), self.settings.screen_size[1])
                                    self.settings.screen_size_changed = True
                                        
                                input_active = PyImGui.is_item_active()
                                        
                                PyImGui.pop_item_width()
                                        
                                PyImGui.table_next_column()
                                ImGui.text("x")
                                PyImGui.table_next_column()
                                    
                                PyImGui.push_item_width(PyImGui.get_content_region_avail()[0])
                                sheight = ImGui.input_int("##height", self.settings.screen_size[1], 600, 10, PyImGui.InputTextFlags.AutoSelectAll)
                                if sheight != self.settings.screen_size[1]:
                                    self.settings.screen_size = (self.settings.screen_size[0], max(600, sheight))  
                                    self.settings.screen_size_changed = True        
                                    
                                input_active = input_active or PyImGui.is_item_active()                    
                                    
                                if not input_active and self.settings.screen_size_changed:
                                    self.settings.screen_size_changed = False
                                    self.ensure_regions_within_bounds(self.settings.regions)      
                                        
                                PyImGui.pop_item_width()
                                ImGui.end_table()
                                    
                            style.CellPadding.pop_style_var()
                            style.ItemSpacing.pop_style_var() 
                        
                        def draw_layout_presets():
                            style.ChildBg.push_color(card_background)
                            style.WindowPadding.push_style_var(0, 0)
                            if ImGui.begin_child("layouts", (0, header_height), border=True, flags=PyImGui.WindowFlags.NoScrollbar): 
                                style.ChildBg.pop_color()
                                style.WindowPadding.pop_style_var()
                                
                                if ImGui.begin_child("layouts edit", (PyImGui.get_content_region_avail()[0] / 2, header_height), border=True, flags=PyImGui.WindowFlags.NoScrollbar): 
                                    PyImGui.push_item_width(PyImGui.get_content_region_avail()[0] - 35) 
                                        
                                    self.draw_column_icon(30, 20, 5)      
                                    PyImGui.same_line(0, 5)          
                                    self.settings.layout_import_columns = ImGui.input_text("##Columns##layout_import_columns", self.settings.layout_import_columns, 0)  
                                    ImGui.show_tooltip("Define the column structure using space, comma or semicolon separated integers.\nE.g. '1 2 1' for 3 columns where the middle one is twice as wide as the others.")

                                    self.draw_row_icon(30, 20)      
                                    PyImGui.same_line(0, 5)  
                                    self.settings.layout_import_rows = ImGui.input_text("##Rows##layout_import", self.settings.layout_import_rows, 0)
                                    ImGui.show_tooltip("Define the row structure using space, comma or semicolon separated integers.\nE.g. '1 2 1' for 3 rows where the middle one is twice as high as the others.")
                                    
                                    PyImGui.pop_item_width()
                                    
                                    if ImGui.button("Create Layout", PyImGui.get_content_region_avail()[0] - 5):
                                        try:
                                            ## import from strings like "1,2,1", "1 2 1" "1;1;1;1"
                                            cols = [int(x) for x in self.settings.layout_import_columns.replace(";", ",").replace(" ", ",").split(",") if x.strip().isdigit() and int(x.strip()) > 0] if self.settings.layout_import_columns.strip() else [1]
                                            rows = [int(x) for x in self.settings.layout_import_rows.replace(";", ",").replace(" ", ",").split(",") if x.strip().isdigit() and int(x.strip()) > 0] if self.settings.layout_import_rows.strip() else [1]

                                            if not cols or not rows:
                                                ConsoleLog(MODULE_NAME, "Invalid layout import format. Please provide comma-separated integers for columns and rows.", message_type=1)
                                                return

                                            self.settings.clear_regions()
                                            cell_widths = [self.settings.screen_size[0] // sum(cols) * c for c in cols]
                                            cell_heights = [self.settings.screen_size[1] // sum(rows) * r for r in rows]

                                            y_offset = 0
                                            for rh in cell_heights:
                                                x_offset = 0
                                                for cw in cell_widths:
                                                    region = Region(x_offset, y_offset, cw, rh, name = f"Region {len(self.settings.regions) + 1}")
                                                    self.settings.add_region(region)
                                                    x_offset += cw
                                                y_offset += rh

                                            ConsoleLog(MODULE_NAME, f"Imported layout with {len(self.settings.regions)} regions.")
                                        except Exception as e:
                                            ConsoleLog(MODULE_NAME, f"Error importing layout: {e}", message_type=1)
                                            
                                ImGui.end_child()
                                
                                PyImGui.same_line(0, 0)
                                
                                if ImGui.begin_child("layouts load and save", (0, header_height), border=True, flags=PyImGui.WindowFlags.NoScrollbar):
                                    avail = PyImGui.get_content_region_avail()[0]
                                    
                                    PyImGui.push_item_width(avail - 100)
                                    self.layout_index = self.settings.layouts.index(self.settings.layout) if self.settings.layout and self.settings.layouts else 0
                                    
                                    if self.layout_index > 0 and self.layout_name != self.settings.layout:
                                        self.layout_name = self.settings.layout
                                        
                                    layout_index = ImGui.combo("Selected Layout", min(self.layout_index, len(self.settings.layouts)), self.settings.layouts)
                                    PyImGui.pop_item_width()
                                    if layout_index != self.layout_index:
                                        self.layout_index = layout_index
                                        layout_name = self.settings.layouts[self.layout_index] if self.settings.layouts else self.layout_name

                                        if layout_name != "None":
                                            self.settings.load_layout(layout_name)
                                            
                                            from Sources.frenkeyLib.MultiBoxing.messaging import send_reload_settings
                                            send_reload_settings(self.settings)
                                            
                                            self.layout_name = layout_name
                                            
                                        elif self.layout_name != layout_name:
                                            self.layout_name = "None"
                                            self.settings.layout = "None"
                                            self.settings.save_settings()


                                    PyImGui.push_item_width(avail - 105)
                                    self.layout_name = ImGui.input_text("Layout Name", self.layout_name, 0)
                                    PyImGui.pop_item_width()

                                    if ImGui.button("Save Layout", avail - 5):
                                        self.settings.save_layout(self.layout_name)
                                
                                ImGui.end_child()
                            else:
                                style.WindowPadding.pop_style_var()                    
                                style.ChildBg.pop_color()
                                
                            ImGui.end_child()
                                        
                        def draw_regions_edit():
                            style.ChildBg.push_color(card_background)
                            if ImGui.begin_child("regions", (0, 0), border=True, flags=PyImGui.WindowFlags.NoScrollbar):                                               
                                if ImGui.button("Add Region", PyImGui.get_content_region_avail()[0], 20):
                                    new_region = Region(0, 0, 1920, 1080, name = f"Region {len(self.settings.regions) + 1}")
                                    #center the new region
                                    new_region.x = (self.settings.screen_size[0] - new_region.w) // 2
                                    new_region.y = (self.settings.screen_size[1] - new_region.h) // 2

                                    self.settings.add_region(new_region)
                                    
                                PyImGui.spacing()
                                ImGui.separator()
                                PyImGui.spacing()
                                
                                new_active = self.settings.active_region
                                
                                for region in self.settings.regions:
                                    if region == self.settings.active_region:       
                                        style.ChildBg.push_color(region.color.opacify(0.15).to_tuple())
                                        style.Border.push_color(region.color.to_tuple())
                                        if ImGui.begin_child("active_region_edit", (0, 285), border=True, flags=PyImGui.WindowFlags.NoScrollbar):
                                            style.Border.pop_color()
                                            style.ChildBg.pop_color()
                                            ImGui.text_centered(region.name, PyImGui.get_content_region_avail()[0])
                                            PyImGui.set_cursor_pos(250 - 2, 4)
                                            if ImGui.icon_button(IconsFontAwesome5.ICON_TRASH, 25, 25):
                                                self.settings.remove_region(region)
                                                new_active = None
                                                if self.settings.active_region == region:
                                                    self.settings.active_region = None
                                                ImGui.end_child()
                                                break
                                            
                                            ImGui.show_tooltip("Delete this region")
                                            
                                            ImGui.separator()
                                            
                                            region.name = ImGui.input_text("Name", region.name, 0)
                                            account_names = [acc.AccountEmail for acc in self.settings.accounts]
                                            account_names.insert(0, "None")
                                            
                                            account_index = account_names.index(region.account) if region.account in account_names else 0
                                            new_account = ImGui.combo("Account", account_index, account_names)
                                            if new_account != account_index:
                                                region.account = account_names[new_account]
                                                
                                            region.x = ImGui.input_int("X", region.x, 10, 1, PyImGui.InputTextFlags.AutoSelectAll)
                                            region.y = ImGui.input_int("Y", region.y, 10, 1, PyImGui.InputTextFlags.AutoSelectAll)
                                            region.w = ImGui.input_int("Width", region.w, 10, 1, PyImGui.InputTextFlags.AutoSelectAll)
                                            region.h = ImGui.input_int("Height", region.h, 10, 1, PyImGui.InputTextFlags.AutoSelectAll)           
                                            color = PyImGui.color_edit4("Color", region.color.color_tuple)
                                            if color != region.color.color_tuple:
                                                region.color = Color.from_tuple(color)                   
                                            region.main = ImGui.checkbox("Main Region", region.main)
                                            
                                            if region.main:
                                                for r in self.settings.regions:
                                                    if r != region:
                                                        r.main = False

                                        else:
                                            style.Border.pop_color()
                                            style.ChildBg.pop_color()
                                            
                                        ImGui.end_child()
                                        pass
                                    else:
                                        style.Button.push_color(region.color.rgb_tuple)
                                        style.ButtonTextureBackground.push_color(region.color.rgb_tuple)
                                        style.ButtonHovered.push_color(region.color.saturate(0.2).rgb_tuple)
                                        style.ButtonTextureBackgroundHovered.push_color(region.color.saturate(0.2).rgb_tuple)
                                        style.ButtonActive.push_color(region.color.saturate(0.4).rgb_tuple)
                                        style.ButtonTextureBackgroundActive.push_color(region.color.saturate(0.4).rgb_tuple)
                                        
                                        if ImGui.button(f"{region.name} ({region.w}x{region.h} @ {region.x},{region.y})", PyImGui.get_content_region_avail()[0], 20):
                                            new_active = region
                                                
                                        style.Button.pop_color()
                                        style.ButtonTextureBackground.pop_color()
                                        style.ButtonHovered.pop_color()       
                                        style.ButtonTextureBackgroundHovered.pop_color()                     
                                        style.ButtonActive.pop_color()
                                        style.ButtonTextureBackgroundActive.pop_color()
                                
                                if new_active != self.settings.active_region:
                                    self.settings.active_region = new_active
                                    for r in self.settings.regions:
                                        r.selected = (r == self.settings.active_region)
                                        
                            style.ChildBg.pop_color()
                            ImGui.end_child()
                                                
                        draw_configs()
                        PyImGui.same_line(0, 5)
                        draw_layout_presets()
                        if ImGui.begin_child("region_canvas_container", (0, 0), border=False, flags=PyImGui.WindowFlags.NoScrollbar):
                            self.draw_region_canvas(style, PyImGui.get_content_region_avail(), PyImGui.get_cursor_pos_y())
                        ImGui.end_child()
                        
                        PyImGui.table_next_column()
                        draw_regions_edit()
                        
                        ImGui.end_table()
                        
                    ImGui.end_tab_item()
                    
                ImGui.end_tab_bar()  
            style.CellPadding.pop_style_var()   
            
            
        if self.settings.active_region and PyImGui.is_key_down(Key.Delete.value):
            self.settings.remove_region(self.settings.active_region)
            self.settings.active_region = None

        if not self.configure_window.open and module_info and module_info.configuring:
            self.widget_handler.set_widget_configuring(MODULE_NAME, False)

        self.configure_window.end()
        
    def draw_region_canvas(self, style, win_size, header_bottom):
        ratio = self.settings.screen_size[0] / self.settings.screen_size[1]
            
            # Default drawing area size
        drawing_area_size = [win_size[0], win_size[0] / ratio]

            # Maintain minimum vertical gap below header
        desired_gap = 5
        available_height = win_size[1] - header_bottom - desired_gap

            # If the drawing area is too tall, shrink proportionally (keeping ratio)
        if drawing_area_size[1] > available_height:
            drawing_area_size[1] = available_height
            drawing_area_size[0] = drawing_area_size[1] * ratio

            # Recalculate horizontal centering (center within current window)
        drawing_area_pos_x = PyImGui.get_cursor_pos_x() + max(0, (win_size[0] - drawing_area_size[0]) / 2)

            # Default vertical position (centered vertically)
        drawing_area_pos_y = (win_size[1] - drawing_area_size[1]) / 2

            # Ensure it stays below the header (keep gap)
        drawing_area_pos_y = max(header_bottom + desired_gap, drawing_area_pos_y)

            # Prevent going off the bottom of the window
        bottom_space = win_size[1] - (drawing_area_pos_y + drawing_area_size[1])
        if bottom_space < 0:
            drawing_area_pos_y += bottom_space  # move up to fit fully

            # Prevent it from leaving the top of the window
        drawing_area_pos_y = max(0, drawing_area_pos_y)

        drawing_area_pos = (drawing_area_pos_x, drawing_area_pos_y)

        scale = drawing_area_size[0] / self.settings.screen_size[0]

        
                
            # --- Draw the area ---
        PyImGui.set_cursor_pos(drawing_area_pos[0], drawing_area_pos[1])
        drawing_area_screen_pos = PyImGui.get_cursor_screen_pos()

        if ImGui.is_mouse_in_rect((drawing_area_screen_pos[0], drawing_area_screen_pos[1], drawing_area_size[0], drawing_area_size[1])):
            self.configure_window.window_flags = PyImGui.WindowFlags.NoMove
                        
        if drawing_area_size[0] > 0 and drawing_area_size[1] > 0 and PyImGui.is_rect_visible(drawing_area_size[0], drawing_area_size[1]):
            style.WindowPadding.push_style_var(0, 0)
                
            if PyImGui.begin_child("region_canvas", (drawing_area_size[0], drawing_area_size[1]), False, PyImGui.WindowFlags.NoFlag):
                origin_x, origin_y = PyImGui.get_window_pos()

                io = PyImGui.get_io()
                mx, my = io.mouse_pos_x, io.mouse_pos_y

                canvas_hovered = PyImGui.is_window_hovered()
                        
                left_down = PyImGui.is_mouse_down(0)
                left_clicked = PyImGui.is_mouse_clicked(0)

                for region in self.settings.regions:
                    region.draw(origin_x, origin_y, scale)

                    # --- interaction logic ---
                if canvas_hovered:
                    hovered = None
                    for region in reversed(self.settings.regions):  # topmost first
                        if region.contains(mx - origin_x, my - origin_y, scale):
                            hovered = region
                            break

                        # click handling
                    if left_clicked:                                
                        if hovered:
                                # select
                            self.settings.active_region = hovered
                                    
                            if io.key_ctrl:
                                    #copy region
                                if not self.settings.active_region.resizing:
                                    new_region = Region(self.settings.active_region.x + 20, self.settings.active_region.y + 20, self.settings.active_region.w, self.settings.active_region.h, name = f"{self.settings.active_region.name} Copy", account = self.settings.active_region.account, color = self.settings.active_region.color.copy())
                                    self.settings.add_region(new_region)
                                    self.settings.active_region = new_region
                                    for r in self.settings.regions:
                                        r.selected = (r == new_region)
                                    self.settings.active_region.dragging = True

                            for r in self.settings.regions:
                                r.selected = (r == hovered)
                                # begin drag/resize
                            hovered.resize_direction = hovered.on_resize_zone(mx - origin_x, my - origin_y, scale)
                            
                            if hovered.resize_direction != Region.ResizeDirection.NONE:
                                hovered.resizing = True
                            else:
                                hovered.dragging = True
                        else:
                                # deselect
                            self.settings.active_region = None
                            for r in self.settings.regions:
                                r.selected = False

                        # drag or resize
                    if left_down and self.settings.active_region:
                        dx, dy = PyImGui.get_mouse_drag_delta(0, 0)
                                                    
                        if self.settings.active_region.dragging:
                            self.settings.active_region.x += int(dx * (1/scale))
                            self.settings.active_region.y += int(dy * (1/scale))
                                
                            if self.settings.snap_to_edges:
                                    # Snap to screen edges
                                if abs(self.settings.active_region.x) <= self.settings.edge_snap_distance:
                                    self.settings.active_region.x = 0
                                if abs((self.settings.active_region.x + self.settings.active_region.w) - self.settings.screen_size[0]) <= self.settings.edge_snap_distance:
                                    self.settings.active_region.x = self.settings.screen_size[0] - self.settings.active_region.w
                                if abs(self.settings.active_region.y) <= self.settings.edge_snap_distance:
                                    self.settings.active_region.y = 0
                                if abs((self.settings.active_region.y + self.settings.active_region.h) - self.settings.screen_size[1]) <= self.settings.edge_snap_distance:
                                    self.settings.active_region.y = self.settings.screen_size[1] - self.settings.active_region.h
                                    
                                    # Snap to other regions
                                for r in self.settings.regions:
                                    if r == self.settings.active_region:
                                        continue
                                        
                                        # Snap X axis (left/right)
                                    if abs((self.settings.active_region.x + self.settings.active_region.w) - r.x) <= self.settings.edge_snap_distance:
                                        self.settings.active_region.x = r.x - self.settings.active_region.w
                                    if abs(self.settings.active_region.x - (r.x + r.w)) <= self.settings.edge_snap_distance:
                                        self.settings.active_region.x = r.x + r.w
                                        
                                        # Snap Y axis (top/bottom)
                                    if abs((self.settings.active_region.y + self.settings.active_region.h) - r.y) <= self.settings.edge_snap_distance:
                                        self.settings.active_region.y = r.y - self.settings.active_region.h
                                    if abs(self.settings.active_region.y - (r.y + r.h)) <= self.settings.edge_snap_distance:
                                        self.settings.active_region.y = r.y + r.h
                                

                        elif self.settings.active_region.resizing:
                            # Get drag delta since last reset (not since drag start)
                            dx, dy = PyImGui.get_mouse_drag_delta(0, 0)
                            dx /= scale
                            dy /= scale

                            min_w = 64
                            min_h = 32

                            # Work on local vars first
                            x, y = self.settings.active_region.x, self.settings.active_region.y
                            w, h = self.settings.active_region.w, self.settings.active_region.h

                            match self.settings.active_region.resize_direction:
                                case Region.ResizeDirection.TOP_LEFT:
                                    # Move top-left corner
                                    x += dx
                                    y += dy
                                    w -= dx
                                    h -= dy

                                case Region.ResizeDirection.TOP_RIGHT:
                                    # Move top edge, right stays fixed
                                    y += dy
                                    w += dx
                                    h -= dy

                                case Region.ResizeDirection.BOTTOM_LEFT:
                                    # Move left edge, bottom stays fixed
                                    x += dx
                                    w -= dx
                                    h += dy

                                case Region.ResizeDirection.BOTTOM_RIGHT:
                                    # Bottom-right only changes size
                                    w += dx
                                    h += dy

                            # Enforce min width/height and correct position if clamped
                            if w < min_w:
                                if self.settings.active_region.resize_direction in [Region.ResizeDirection.TOP_LEFT, Region.ResizeDirection.BOTTOM_LEFT]:
                                    x -= (min_w - w)
                                w = min_w

                            if h < min_h:
                                if self.settings.active_region.resize_direction in [Region.ResizeDirection.TOP_LEFT, Region.ResizeDirection.TOP_RIGHT]:
                                    y -= (min_h - h)
                                h = min_h

                            # Apply new values
                            self.settings.active_region.x = int(x)
                            self.settings.active_region.y = int(y)
                            self.settings.active_region.w = int(w)
                            self.settings.active_region.h = int(h)

                            # Reset delta so movement is relative frame-to-frame, not cumulative
                            PyImGui.reset_mouse_drag_delta(0)
                                
                            if self.settings.snap_to_edges:
                                    # Snap to screen edges
                                if abs((self.settings.active_region.x + self.settings.active_region.w) - self.settings.screen_size[0]) <= self.settings.edge_snap_distance:
                                    self.settings.active_region.w = self.settings.screen_size[0] - self.settings.active_region.x
                                if abs((self.settings.active_region.y + self.settings.active_region.h) - self.settings.screen_size[1]) <= self.settings.edge_snap_distance:
                                    self.settings.active_region.h = self.settings.screen_size[1] - self.settings.active_region.y
                                    
                                    # Snap to other regions, if other region is touching, snap to same width/height           
                                for r in self.settings.regions:
                                    if r == self.settings.active_region:
                                        continue
                                        
                                        # Snap width (right edge)
                                    if abs((self.settings.active_region.x + self.settings.active_region.w) - r.x) <= self.settings.edge_snap_distance:
                                        if (self.settings.active_region.y + self.settings.active_region.h > r.y and self.settings.active_region.y < r.y + r.h):
                                            self.settings.active_region.w = r.x - self.settings.active_region.x
                                        
                                        # Snap height (bottom edge)
                                    if abs((self.settings.active_region.y + self.settings.active_region.h) - r.y) <= self.settings.edge_snap_distance:
                                        if (self.settings.active_region.x + self.settings.active_region.w > r.x and self.settings.active_region.x < r.x + r.w):
                                            self.settings.active_region.h = r.y - self.settings.active_region.y
                                        
                                    is_below_at_same_x = (self.settings.active_region.x >= r.x and self.settings.active_region.x <= r.x + r.w) or (self.settings.active_region.x + self.settings.active_region.w >= r.x and self.settings.active_region.x + self.settings.active_region.w <= r.x + r.w)
                                    if is_below_at_same_x and abs((self.settings.active_region.y) - (r.y + r.h)) <= self.settings.edge_snap_distance:
                                        if abs(self.settings.active_region.h - r.h) <= self.settings.edge_snap_distance:
                                            self.settings.active_region.h = r.h
                                            
                                        if abs(self.settings.active_region.w - r.w) <= self.settings.edge_snap_distance:
                                            self.settings.active_region.w = r.w
                                                
                                
                        PyImGui.reset_mouse_drag_delta(0)
                    else:
                        for r in self.settings.regions:
                            r.dragging = False
                            r.resizing = False

            ImGui.end_child()
                
            style.WindowPadding.pop_style_var()
                
            border = Color(168, 168, 168, 150)
            PyImGui.draw_list_add_rect_filled(drawing_area_screen_pos[0], drawing_area_screen_pos[1], drawing_area_screen_pos[0] + drawing_area_size[0], drawing_area_screen_pos[1] + drawing_area_size[1], border.color_int, 0, 0)
                
            border = Color(0, 0, 0, 150)
            border_thickness = 3
            PyImGui.draw_list_add_rect(drawing_area_screen_pos[0] - (border_thickness / 2), drawing_area_screen_pos[1] - (border_thickness / 2), drawing_area_screen_pos[0] + drawing_area_size[0] + (border_thickness / 2), drawing_area_screen_pos[1] + drawing_area_size[1] + (border_thickness / 2), border.color_int, 0, 0, border_thickness)

    def draw_account_button(self, style : Style, account : AccountStruct, size : tuple[float, float] = (0, 0), is_current_account: bool = False, index: int = 0) -> bool:
        profession_colors ={
            Profession.Warrior: ColorPalette.GetColor("gw_warrior"),
            Profession.Ranger: ColorPalette.GetColor("gw_ranger"),
            Profession.Monk: ColorPalette.GetColor("gw_monk"),
            Profession.Necromancer: ColorPalette.GetColor("gw_necromancer"),
            Profession.Mesmer: ColorPalette.GetColor("gw_mesmer"),
            Profession.Elementalist: ColorPalette.GetColor("gw_elementalist"),
            Profession.Assassin: ColorPalette.GetColor("gw_assassin"),
            Profession.Ritualist: ColorPalette.GetColor("gw_ritualist"),
            Profession.Paragon: ColorPalette.GetColor("gw_paragon"),
            Profession.Dervish: ColorPalette.GetColor("gw_dervish"),
        }
        
        cursor_pos = PyImGui.get_cursor_screen_pos()
        profession = Profession(account.AgentData.Profession[0]) if account.AgentData.Profession else Profession._None
        secondary_profession = Profession(account.AgentData.Profession[1]) if account.AgentData.Profession else Profession._None
        
        profession_color = profession_colors.get(profession, ColorPalette.GetColor("gw_disabled"))
        is_hovered = ImGui.is_mouse_in_rect((cursor_pos[0], cursor_pos[1], size[0], size[1]))
        background = profession_color.opacify(0.6).rgb_tuple if is_hovered else profession_color.opacify(0.6).desaturate(0.25).rgb_tuple
        if is_current_account:
            background = profession_color.opacify(0.6).desaturate(0.75).rgb_tuple
            
        border = profession_color.rgb_tuple if is_hovered else profession_color.desaturate(0.25).rgb_tuple
        if is_current_account:
            border = profession_color.desaturate(0.75).rgb_tuple

        style.ChildBg.push_color(background)
        style.Border.push_color(border)

        style.WindowPadding.push_style_var(4, 2)
        if ImGui.begin_child(f"account_btn_{index}", size, border=True, flags=PyImGui.WindowFlags.NoFlag):
            
            profession_text = f"{ProfessionShort(profession).name}" if profession != Profession._None else ""     
            if secondary_profession != Profession._None and secondary_profession != profession:
                profession_text += f"/{ProfessionShort(secondary_profession).name}" 
            
            profession_text = profession_text.strip()
            
            avail = PyImGui.get_content_region_avail()
            
            if profession_text:                
                ImGui.text_centered(profession_text, -1, avail[1] + 6)
                
            level_text = f" {account.AgentData.Level}" if account.AgentData.Level else ""
            
            if level_text:
                PyImGui.same_line(38, 0)
                ImGui.text_centered(level_text, -1, avail[1] + 6)
                
            name_text = f"{account.AgentData.CharacterName}" if account.AgentData.CharacterName else ""
            # name_text = f" frenkey {account.SlotNumber}"
            name_text = name_text if name_text else f"Pending ..."
            if name_text:
                PyImGui.same_line(62, 0)
                ImGui.text_centered(name_text, -1, avail[1] + 6)

        ImGui.end_child()
        style.WindowPadding.pop_style_var()
        
        style.Border.pop_color()
        style.ChildBg.pop_color()
        
        return PyImGui.is_item_clicked(0)

    def draw_access_window(self):
        if not self.settings.show_overview:
            return
        
        window_width = 200               
        style = ImGui.get_style()
        
        style.WindowPadding.push_style_var(4, 2)        
        style.ItemSpacing.push_style_var(5, 2)
        
        header_size = 30
        account_btn_size = (window_width - 7, 20)
        window_height = len(self.settings.accounts) * (account_btn_size[1] + (style.ItemSpacing.value2 or 0) / 2) + header_size
        
        self.access_window.window_pos = (self.screen_width - window_width - 2, 2)
        self.access_window.window_size = (window_width, window_height)
        
        PyImGui.set_next_window_pos(self.screen_width - window_width - 2, 2)
        PyImGui.set_next_window_size(window_width, window_height - (len(self.settings.accounts)))

        if self.access_window.begin(None, PyImGui.WindowFlags(PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.NoResize | PyImGui.WindowFlags.NoMove | PyImGui.WindowFlags.NoSavedSettings)):
            i = 0
            self.screen_width = ImGui.overlay_instance.GetDisplaySize().x
            
            ImGui.text_centered("Accounts", window_width, header_size, font_size=18, font_style="Regular")

            #sort accounts based on their order in settings.accounts_order
            sorted_accounts = []
            for account_email in self.settings.accounts_order:
                account = next((acc for acc in self.settings.accounts if acc.AccountEmail == account_email), None)
                
                if account:
                    sorted_accounts.append(account)
                    
            own_region = next((r for r in self.settings.regions if r.account == self.settings.get_account_mail()), None) if self.settings.regions else None
            
            for account in sorted_accounts:
                i += 1

                is_current_account=account.AccountEmail == self.settings.get_account_mail()
                ctrl_pressed = PyImGui.get_io().key_ctrl
                
                if self.draw_account_button(style=style, account=account, size=account_btn_size, is_current_account=is_current_account, index=i):
                    if not is_current_account:         
                        set_window_active(account, self.settings, ctrl_pressed)
                        
                        if own_region and not ctrl_pressed:
                            ConsoleLog(MODULE_NAME, f"Moving own client to own region {own_region.name}.")
                            ctypes.windll.user32.SetWindowPos(Console.get_gw_window_handle(), -1, own_region.x, own_region.y, own_region.w, own_region.h, 0)
                            # Console.set_window_geometry(own_region.x, own_region.y, own_region.w, own_region.h)
                            # Console.set_borderless(False)
        
            PyImGui.set_cursor_pos(4, 4)
            if ImGui.icon_button(IconsFontAwesome5.ICON_GRIP, 25, 18):
                position_clients(self.settings.get_account_mail(), self.settings.regions, self.settings.accounts)
            
            ImGui.show_tooltip("Position all clients in their assigned regions")
                
        style.ItemSpacing.pop_style_var()
        style.WindowPadding.pop_style_var()
        self.access_window.end()
