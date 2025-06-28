import Py4GW
from Py4GWCoreLib import *

MODULE_NAME = "Inventory +"
INVENTORY_FRAME_HASH = 291586130
XUNLAI_VAULT_FRAME_HASH = 2315448754
AUTO_HANDLER = AutoInventoryHandler()
    
class WidgetUI:
    #region Frame
    class Frame:
        def __init__(self, frame_id):
            self.frame_id = frame_id
            if self.frame_id == 0:
                self.left = 0
                self.top = 0
                self.right = 0
                self.bottom = 0
                self.height = 0
                self.width = 0
            else:
                self.update_coords()
                
        def set_frame_id(self, frame_id):
            self.frame_id = frame_id
            if self.frame_id == 0:
                self.left = 0
                self.top = 0
                self.right = 0
                self.bottom = 0
                self.height = 0
                self.width = 0
            else:
                self.update_coords()
                
        def update_coords(self):
            self.left, self.top, self.right, self.bottom = UIManager.GetFrameCoords(self.frame_id) 
            self.height = self.bottom - self.top
            self.width = self.right - self.left   
            
        def draw_frame(self, color=Color(255, 255, 255, 255)):
            if self.frame_id == 0:
                return
            UIManager().DrawFrame(self.frame_id, color.to_color())
            
        def draw_frame_outline(self, color=Color(255, 255, 255, 255)):
            if self.frame_id == 0:
                return
            UIManager().DrawFrameOutline(self.frame_id, color.to_color())

    #endregion
    #region Colorize globals
    class Colorizeglobals:
        def __init__(self):
            self.colorize_whites = False
            self.colorize_blues = True
            self.colorize_purples = True
            self.colorize_golds = True
            self.colorize_greens = True
            self.white_color = Color(255, 255, 255, 255)
            self.blue_color = Color(0, 170, 255, 255)
            self.purple_color = Color(110, 65, 200, 255)
            self.gold_color = Color(225, 150, 0, 255)
            self.green_color = Color(25, 200, 0, 255)
            self.disabled_color = Color(26, 26, 26, 255)
    
    #endregion
    #region TabIcon  
    class TabIcon:
        def __init__(self, 
                     icon_name = "Unknown",
                     icon = IconsFontAwesome5.ICON_QUESTION_CIRCLE,
                     icon_color = Color(255, 255, 255, 255),
                     icon_tooltip = "Unknown",
                     rainbow_color = False):
            self.icon_name = icon_name
            self.icon = icon
            self.icon_color = icon_color
            self.icon_tooltip = icon_tooltip 
            self._color_tick = 0
            self.rainbow_color = rainbow_color
            
        def advance_rainbow_color(self):
            if not self.rainbow_color:
                return
            self._color_tick += 1
            # Use sine waves offset from each other to create a rainbow pulse
            r = int((math.sin(self._color_tick * 0.05) * 0.5 + 0.5) * 255)  # Red wave
            g = int((math.sin(self._color_tick * 0.05 + 2.0) * 0.5 + 0.5) * 255)  # Green wave
            b = int((math.sin(self._color_tick * 0.05 + 4.0) * 0.5 + 0.5) * 255)  # Blue wave
            self.icon_color = Color(r, g, b, 255)
     
    #endregion
    #region InitUI       
    def __init__(self, inventory_frame_id=0, id_checkboxes=None, salvage_checkboxes=None):
        self.id_checkboxes:Dict[int, bool] = id_checkboxes if id_checkboxes is not None else {}
        self.salvage_checkboxes:Dict[int, bool] = salvage_checkboxes if salvage_checkboxes is not None else {}
        self.inventory_frame_id = inventory_frame_id
        self.inventory_frame = self.Frame(0)
        self.tab_icons: List["WidgetUI.TabIcon"] = []
        self.initialize_tab_icons()
        self.selected_tab_icon_index = 0
        
        self.colorize_globals = self.Colorizeglobals()
        
        self.widget_active = True
        
        
    def set_inventory_frame_id(self, inventory_frame_id):
        self.inventory_frame_id = inventory_frame_id
        self.inventory_frame.set_frame_id(inventory_frame_id)
        
    def initialize_tab_icons(self):
        # Initialize tab icons here if needed
        self.tab_icons.append(self.TabIcon(icon_name="##ColorizeTab",
                            icon=IconsFontAwesome5.ICON_PALETTE,
                            icon_color=Color(255, 0, 0, 255),
                            icon_tooltip="Inventory+",
                            rainbow_color=True))
        self.tab_icons.append(self.TabIcon(icon_name="##AutoHandlerTab",
                            icon=IconsFontAwesome5.ICON_STOPWATCH,
                            icon_tooltip="AutoHandler"))
        self.tab_icons.append(self.TabIcon(icon_name="##IDTab",
                            icon=IconsFontAwesome5.ICON_QUESTION_CIRCLE,
                            icon_tooltip="Mass ID"))
        self.tab_icons.append(self.TabIcon(icon_name="##SalvageTab",
                            icon=IconsFontAwesome5.ICON_RECYCLE,
                            icon_tooltip="Mass Salvage"))
        self.tab_icons.append(self.TabIcon(icon_name="##XunlaiVaultTab",
                            icon=IconsFontAwesome5.ICON_BOX_OPEN,
                            icon_tooltip="Xunlai Vault"))
        self.tab_icons.append(self.TabIcon(icon_name="##TradeTab",
                            icon=IconsFontAwesome5.ICON_BALANCE_SCALE,
                            icon_tooltip="Trade"))
    
    #endregion
    #region FloatingCheckbox
    def floating_checkbox(self, name, state,  x, y, width = 18, height = 18 , color: Color = Color(255, 255, 255, 255)):
        # Set the position and size of the floating button
        PyImGui.set_next_window_pos(x, y)
        PyImGui.set_next_window_size(width, height)
        

        flags=( PyImGui.WindowFlags.NoCollapse | 
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.AlwaysAutoResize  ) 
        
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding,0.0,0.0)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 3, 5)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Border, color.to_tuple_normalized())
        
        result = state
        
        white = ColorPalette.GetColor("White")
        
        if PyImGui.begin(f"##invisible_window{name}", flags):
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg, (0.2, 0.3, 0.4, 0.1))  # Normal state color
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered, (0.3, 0.4, 0.5, 0.1))  # Hovered state
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive, (0.4, 0.5, 0.6, 0.1))  # Checked state
            PyImGui.push_style_color(PyImGui.ImGuiCol.CheckMark, color.shift(white, 0.5).to_tuple_normalized())  # Checkmark color

            result = PyImGui.checkbox(f"##floating_checkbox{name}", state)
            PyImGui.pop_style_color(4)
        PyImGui.end()
        PyImGui.pop_style_var(3)
        PyImGui.pop_style_color(1)
        return result
    
    #region FloatingButtons
    def floating_button(self, caption, name, x, y, width = 18, height = 18 , color: Color = Color(255, 255, 255, 255)):
        PyImGui.set_next_window_pos(x, y)
        PyImGui.set_next_window_size(width, height)

        flags = (
            PyImGui.WindowFlags.NoCollapse |
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.AlwaysAutoResize
        )

        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, -1, -0)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, color.to_tuple_normalized())
        result = False
        if PyImGui.begin(f"{caption}##invisible_buttonwindow{name}", flags):
            result = PyImGui.button(f"{caption}##floating_button{name}", width=width, height=height)

            
        PyImGui.end()
        PyImGui.pop_style_color(1)
        PyImGui.pop_style_var(2)

        return result
    
    #endregion
    #region GameButton
    def floating_game_button(self, caption, name, tooltip,  x, y, width = 18, height = 18 , color: Color = Color(255, 0, 0, 255)):
        PyImGui.set_next_window_pos(x, y)
        PyImGui.set_next_window_size(width, height)

        flags = (
            PyImGui.WindowFlags.NoCollapse |
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.AlwaysAutoResize
        )

        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 0, 0)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding, 0.0)
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0, 0)
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.ItemInnerSpacing, 0, 0)
        

        result = False
        if PyImGui.begin(f"{caption}##invisible_buttonwindow{name}", flags):
            col_normal = color.to_tuple_normalized()
            col_hovered = color.desaturate(0.50).to_tuple_normalized()
            col_active = color.desaturate(0.75).to_tuple_normalized()

            PyImGui.push_style_color(PyImGui.ImGuiCol.Button, col_normal)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, col_hovered)
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, col_active)

            result = PyImGui.button(caption)

            PyImGui.pop_style_color(3)
            ImGui.show_tooltip(tooltip)

        PyImGui.end()
        PyImGui.pop_style_var(4)  # 4 vars were pushed

        return result
    
    def game_button(self, caption, name, tooltip, width = 18, height = 18 , color: Color = Color(255, 0, 0, 255)):
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 0, 0)
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding, 0.0)
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0, 0)
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.ItemInnerSpacing, 0, 0)

        result = False

        #color.set_a(255)
        col_normal = color.to_tuple_normalized()

        col_hovered = color.desaturate(0.50).to_tuple_normalized()
        col_active = color.desaturate(0.75).to_tuple_normalized()

        PyImGui.push_style_color(PyImGui.ImGuiCol.Button, col_normal)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, col_hovered)
        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, col_active)

        result = PyImGui.button(caption + name, width, height)

        PyImGui.pop_style_color(3)
        ImGui.show_tooltip(tooltip)

        PyImGui.pop_style_var(4)  # 4 vars were pushed

        return result
    
    def game_toggle_button(self, name, tooltip, state, width=18, height=18, color: Color = Color(255, 0, 0, 255)):
        if state:
            caption = IconsFontAwesome5.ICON_CHECK_CIRCLE
            clicked = self.game_button(caption, name, tooltip, width, height, color)
        else:
            caption = IconsFontAwesome5.ICON_CIRCLE
            _color = Color(color.r, color.g, color.b, 125)
            clicked = self.game_button(caption, name, tooltip, width, height, _color)
        return clicked
        
    
    #endregion
    #region WidgetToggleButton
    def draw_widget_toggle_button(self):
        x = self.inventory_frame.right - 43
        y = self.inventory_frame.top + 2
        color = Color(0, 255, 0, 255) if self.widget_active else Color(255, 0, 0, 255)
        tooltip = "Inventory + Active" if self.widget_active else "Inventory + Inactive"
        if self.floating_game_button("O", "InvPlus", tooltip,x, y, width=13, height=13, color=color):
            self.widget_active = not self.widget_active
            message = "Active" if self.widget_active else "Inactive"
            Py4GW.Console.Log(MODULE_NAME, f"Inventory + widget is now {message}.", Py4GW.Console.MessageType.Info)
      
    #endregion
    #region DrawButtonStrip      
    def draw_button_strip(self):
        x = self.inventory_frame.left -29
        y = self.inventory_frame.top
        width = 35
        height = self.inventory_frame.height -5
        
        PyImGui.set_next_window_pos(x, y)
        PyImGui.set_next_window_size(width, height)

        flags = (
            PyImGui.WindowFlags.NoCollapse |
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.AlwaysAutoResize
        )
        
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 5, 5)
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0, 0)
        
        if PyImGui.begin("Inventory + Tabs", flags):
            # Draw the tab icons
            for index, icon in enumerate(self.tab_icons):
                icon.advance_rainbow_color()
                toggle_status = False
                if self.selected_tab_icon_index == index:
                    toggle_status = True

                if icon.rainbow_color:
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, icon.icon_color.to_tuple_normalized())

                toggle_status =  ImGui.toggle_button(icon.icon + icon.icon_name, toggle_status, width=25, height=25)
                if icon.rainbow_color:
                    PyImGui.pop_style_color(1)
                if toggle_status:
                    self.selected_tab_icon_index = self.tab_icons.index(icon)
                ImGui.show_tooltip(icon.icon_tooltip)

        PyImGui.end()
        PyImGui.pop_style_var(2)
        
    #endregion
    #region ColorizeStrip

    def draw_colorize_bottom_strip(self):
        x = self.inventory_frame.left +5
        y = self.inventory_frame.bottom
        width = self.inventory_frame.width
        height = 30
        
        PyImGui.set_next_window_pos(x, y)
        PyImGui.set_next_window_size(0, height)

        flags = (
            PyImGui.WindowFlags.NoCollapse |
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.AlwaysAutoResize
        )
        
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 5, 5)
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0, 0)
        
        if PyImGui.begin("ColorizeButtons", flags):
            
            state = self.colorize_globals.colorize_whites
            color = self.colorize_globals.white_color
            if self.game_toggle_button("##ColorizeWhiteButton","Color Whites",state, width=20, height=20, color=color):
                self.colorize_globals.colorize_whites = not self.colorize_globals.colorize_whites
                Py4GW.Console.Log(MODULE_NAME, f"Colorize Whites is now {'enabled' if self.colorize_globals.colorize_whites else 'disabled'}.", Py4GW.Console.MessageType.Info)
            PyImGui.same_line(0,3)  
            state = self.colorize_globals.colorize_blues
            color = self.colorize_globals.blue_color
            if self.game_toggle_button("##ColorizeBlueButton","Color Blues",state, width=20, height=20, color=color):
                self.colorize_globals.colorize_blues = not self.colorize_globals.colorize_blues
                Py4GW.Console.Log(MODULE_NAME, f"Colorize Blues is now {'enabled' if self.colorize_globals.colorize_blues else 'disabled'}.", Py4GW.Console.MessageType.Info)
            PyImGui.same_line(0,3)     
            state = self.colorize_globals.colorize_purples
            color = self.colorize_globals.purple_color
            if self.game_toggle_button("##ColorizePurpleButton","Color Purples",state, width=20, height=20, color=color):
                self.colorize_globals.colorize_purples = not self.colorize_globals.colorize_purples
                Py4GW.Console.Log(MODULE_NAME, f"Colorize Purples is now {'enabled' if self.colorize_globals.colorize_purples else 'disabled'}.", Py4GW.Console.MessageType.Info)
            PyImGui.same_line(0,3)     
            state = self.colorize_globals.colorize_golds
            color = self.colorize_globals.gold_color
            if self.game_toggle_button("##ColorizeGoldButton","Color Golds",state, width=20, height=20, color=color):
                self.colorize_globals.colorize_golds = not self.colorize_globals.colorize_golds
                Py4GW.Console.Log(MODULE_NAME, f"Colorize Golds is now {'enabled' if self.colorize_globals.colorize_golds else 'disabled'}.", Py4GW.Console.MessageType.Info)
            PyImGui.same_line(0,3)     
            state = self.colorize_globals.colorize_greens
            color = self.colorize_globals.green_color
            if self.game_toggle_button("##ColorizeGreenButton","Color Greens",state, width=20, height=20, color=color):
                self.colorize_globals.colorize_greens = not self.colorize_globals.colorize_greens
                Py4GW.Console.Log(MODULE_NAME, f"Colorize Greens is now {'enabled' if self.colorize_globals.colorize_greens else 'disabled'}.", Py4GW.Console.MessageType.Info)
            

        PyImGui.end()
        PyImGui.pop_style_var(2)
    
    #endregion
    #region DrawIDBottomStrip
    def draw_id_bottom_strip(self):
        def _tick_checkboxes(rarity:str, tick_state:bool):
            for bag_id in range(Bags.Backpack, Bags.Bag2 + 1):
                bag_to_check = ItemArray.CreateBagList(bag_id)
                item_array = ItemArray.GetItemArray(bag_to_check)

                for item_id in item_array:
                    if Item.Usage.IsIdentified(item_id) or Item.Usage.IsIDKit(item_id):
                        continue
                    # Ensure checkbox state exists (if it was removed earlier)
                    if item_id not in self.id_checkboxes:
                        self.id_checkboxes[item_id] = False

                    # Apply state based on selected filter
                    if rarity == "All":
                        self.id_checkboxes[item_id] = tick_state
                    elif rarity == "White" and Item.Rarity.IsWhite(item_id):
                        self.id_checkboxes[item_id] = tick_state
                    elif rarity == "Blue" and Item.Rarity.IsBlue(item_id):
                        self.id_checkboxes[item_id] = tick_state
                    elif rarity == "Purple" and Item.Rarity.IsPurple(item_id):
                        self.id_checkboxes[item_id] = tick_state
                    elif rarity == "Gold" and Item.Rarity.IsGold(item_id):
                        self.id_checkboxes[item_id] = tick_state
                    elif rarity == "Green" and Item.Rarity.IsGreen(item_id):
                        self.id_checkboxes[item_id] = tick_state
                        
            # Remove checkbox states that are set to False
            for item_id in list(self.id_checkboxes):
                if not self.id_checkboxes[item_id]:
                    del self.id_checkboxes[item_id]
            
        
        
        x = self.inventory_frame.left +5
        y = self.inventory_frame.bottom
        width = self.inventory_frame.width
        height = 57
        
        PyImGui.set_next_window_pos(x, y)
        PyImGui.set_next_window_size(0, height)

        window_flags = (
            PyImGui.WindowFlags.NoCollapse |
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.AlwaysAutoResize
        )
        
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 5, 5)
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0, 0)
        
        table_flags = (
            PyImGui.TableFlags.BordersInnerV |
            PyImGui.TableFlags.NoPadOuterX
        )
        
        if PyImGui.begin("IDButtonsWindow", window_flags):
            if PyImGui.begin_table("IDButtonsTable", 2, table_flags):
                PyImGui.table_setup_column("Buttons", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("MainButton", PyImGui.TableColumnFlags.WidthFixed, 40)

                PyImGui.table_next_row()
                PyImGui.table_next_column()
                
                if self.game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##IDAllButton","Select All", width=20, height=20, color=self.colorize_globals.disabled_color):
                    _tick_checkboxes("All", True)
                        
                        
                PyImGui.same_line(0,3)
                PyImGui.text("|")
                PyImGui.same_line(0,3)
                
                if self.game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##IDWhitesButton","Select All Whites", width=20, height=20, color=self.colorize_globals.white_color):
                    print(self.colorize_globals.white_color.__repr__())
                    _tick_checkboxes("White", True)
                            
                PyImGui.same_line(0,3)
                if self.game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##IDBluesButton","Select All Blues", width=20, height=20, color=self.colorize_globals.blue_color):
                    print(self.colorize_globals.blue_color.__repr__())
                    _tick_checkboxes("Blue", True)
                            
                PyImGui.same_line(0,3)
                if self.game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##IDPurplesButton","Select All Purples", width=20, height=20, color=self.colorize_globals.purple_color):
                    print(self.colorize_globals.purple_color.__repr__())
                    _tick_checkboxes("Purple", True)
                            
                PyImGui.same_line(0,3)
                if self.game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##IDGoldsButton","Select All Golds", width=20, height=20, color=self.colorize_globals.gold_color):
                    print(self.colorize_globals.gold_color.__repr__())
                    _tick_checkboxes("Gold", True)
                            
                PyImGui.same_line(0,3)
                if self.game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##IDGreensButton","Select All Greens", width=20, height=20, color=self.colorize_globals.green_color):
                    print(self.colorize_globals.green_color.__repr__())
                    _tick_checkboxes("Green", True)           
                            
                #next row of buttons
                if self.game_button(IconsFontAwesome5.ICON_SQUARE,"##IDClearAllButton","Clear All", width=20, height=20, color=self.colorize_globals.disabled_color):
                    print(self.colorize_globals.white_color.__repr__())
                    _tick_checkboxes("All", False) 
                            
                PyImGui.same_line(0,3)
                PyImGui.text("|")
                PyImGui.same_line(0,3)
                
                if self.game_button(IconsFontAwesome5.ICON_SQUARE,"##IDClearWhitesButton","Clear Whites", width=20, height=20, color=self.colorize_globals.white_color):
                    print(self.colorize_globals.white_color.__repr__())
                    _tick_checkboxes("White", False)
                    
                PyImGui.same_line(0,3)
                if self.game_button(IconsFontAwesome5.ICON_SQUARE,"##IDClearBluesButton","Clear Blues", width=20, height=20, color=self.colorize_globals.blue_color):
                    print(self.colorize_globals.blue_color.__repr__())
                    _tick_checkboxes("Blue", False)
                    
                PyImGui.same_line(0,3)
                if self.game_button(IconsFontAwesome5.ICON_SQUARE,"##IDClearPurplesButton","Clear Purples", width=20, height=20, color=self.colorize_globals.purple_color):
                    print(self.colorize_globals.purple_color.__repr__())
                    _tick_checkboxes("Purple", False)
                    
                PyImGui.same_line(0,3)
                if self.game_button(IconsFontAwesome5.ICON_SQUARE,"##IDClearGoldsButton","Clear Golds", width=20, height=20, color=self.colorize_globals.gold_color):
                    print(self.colorize_globals.gold_color.__repr__())
                    _tick_checkboxes("Gold", False)
                PyImGui.same_line(0,3)
                
                if self.game_button(IconsFontAwesome5.ICON_SQUARE,"##IDClearGreensButton","Clear Greens", width=20, height=20, color=self.colorize_globals.green_color):
                    print(self.colorize_globals.green_color.__repr__())
                    _tick_checkboxes("Green", False)
                    
            PyImGui.table_next_column()
            texture_file = ItemModelTextureMap[ModelID.Superior_Identification_Kit.value]
            if ImGui.ImageButton("##text_unique_name", texture_file, 45, 45):
                GLOBAL_CACHE.Coroutines.append(IdentifyCheckedItems(self.id_checkboxes))
            ImGui.show_tooltip("Identify selected items.")    

            PyImGui.end_table()
                        
        PyImGui.end()
        PyImGui.pop_style_var(2)
    
    
    #endregion
    
    #region DrawSalvBottomStrip
    def draw_salvage_bottom_strip(self):
        def _tick_checkboxes(rarity:str, tick_state:bool):
            for bag_id in range(Bags.Backpack, Bags.Bag2 + 1):
                bag_to_check = ItemArray.CreateBagList(bag_id)
                item_array = ItemArray.GetItemArray(bag_to_check)

                for item_id in item_array:
                    if not Item.Usage.IsSalvageable(item_id):
                        continue
                    
                    if Item.Usage.IsSalvageKit(item_id):
                        continue
                    
                    if not (Item.Rarity.IsWhite(item_id) or Item.Usage.IsIdentified(item_id)):
                        continue
                    
                    # Ensure checkbox state exists (if it was removed earlier)
                    if item_id not in self.salvage_checkboxes:
                        self.salvage_checkboxes[item_id] = False

                    # Apply state based on selected filter
                    if rarity == "All":
                        self.salvage_checkboxes[item_id] = tick_state
                    elif rarity == "White" and Item.Rarity.IsWhite(item_id):
                        self.salvage_checkboxes[item_id] = tick_state
                    elif rarity == "Blue" and Item.Rarity.IsBlue(item_id):
                        self.salvage_checkboxes[item_id] = tick_state
                    elif rarity == "Purple" and Item.Rarity.IsPurple(item_id):
                        self.salvage_checkboxes[item_id] = tick_state
                    elif rarity == "Gold" and Item.Rarity.IsGold(item_id):
                        self.salvage_checkboxes[item_id] = tick_state
                    elif rarity == "Green" and Item.Rarity.IsGreen(item_id):
                        self.salvage_checkboxes[item_id] = tick_state
                        
            # Remove checkbox states that are set to False
            for item_id in list(self.salvage_checkboxes):
                if not self.salvage_checkboxes[item_id]:
                    del self.salvage_checkboxes[item_id]
            
        
        
        x = self.inventory_frame.left +5
        y = self.inventory_frame.bottom
        width = self.inventory_frame.width
        height = 57
        
        PyImGui.set_next_window_pos(x, y)
        PyImGui.set_next_window_size(0, height)

        window_flags = (
            PyImGui.WindowFlags.NoCollapse |
            PyImGui.WindowFlags.NoTitleBar |
            PyImGui.WindowFlags.NoScrollbar |
            PyImGui.WindowFlags.NoScrollWithMouse |
            PyImGui.WindowFlags.AlwaysAutoResize
        )
        
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 5, 5)
        PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0, 0)
        
        table_flags = (
            PyImGui.TableFlags.BordersInnerV |
            PyImGui.TableFlags.NoPadOuterX
        )
        
        if PyImGui.begin("SalvageButtonsWindow", window_flags):
            if PyImGui.begin_table("SalvageButtonsTable", 2, table_flags):
                PyImGui.table_setup_column("Buttons", PyImGui.TableColumnFlags.WidthStretch)
                PyImGui.table_setup_column("MainButton", PyImGui.TableColumnFlags.WidthFixed, 40)

                PyImGui.table_next_row()
                PyImGui.table_next_column()
                
                if self.game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##SalvageAllButton","Select All", width=20, height=20, color=self.colorize_globals.disabled_color):
                    _tick_checkboxes("All", True)
                        
                        
                PyImGui.same_line(0,3)
                PyImGui.text("|")
                PyImGui.same_line(0,3)
                
                if self.game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##SalvageWhitesButton","Select All Whites", width=20, height=20, color=self.colorize_globals.white_color):
                    print(self.colorize_globals.white_color.__repr__())
                    _tick_checkboxes("White", True)
                            
                PyImGui.same_line(0,3)
                if self.game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##SalvageBluesButton","Select All Blues", width=20, height=20, color=self.colorize_globals.blue_color):
                    print(self.colorize_globals.blue_color.__repr__())
                    _tick_checkboxes("Blue", True)
                            
                PyImGui.same_line(0,3)
                if self.game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##SalvagePurplesButton","Select All Purples", width=20, height=20, color=self.colorize_globals.purple_color):
                    print(self.colorize_globals.purple_color.__repr__())
                    _tick_checkboxes("Purple", True)
                            
                PyImGui.same_line(0,3)
                if self.game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##SalvageGoldsButton","Select All Golds", width=20, height=20, color=self.colorize_globals.gold_color):
                    print(self.colorize_globals.gold_color.__repr__())
                    _tick_checkboxes("Gold", True)
                            
                PyImGui.same_line(0,3)
                if self.game_button(IconsFontAwesome5.ICON_CHECK_SQUARE,"##SalvageGreensButton","Select All Greens", width=20, height=20, color=self.colorize_globals.green_color):
                    print(self.colorize_globals.green_color.__repr__())
                    _tick_checkboxes("Green", True)           
                            
                #next row of buttons
                if self.game_button(IconsFontAwesome5.ICON_SQUARE,"##SalvageClearAllButton","Clear All", width=20, height=20, color=self.colorize_globals.disabled_color):
                    print(self.colorize_globals.white_color.__repr__())
                    _tick_checkboxes("All", False) 
                            
                PyImGui.same_line(0,3)
                PyImGui.text("|")
                PyImGui.same_line(0,3)
                
                if self.game_button(IconsFontAwesome5.ICON_SQUARE,"##SalvageClearWhitesButton","Clear Whites", width=20, height=20, color=self.colorize_globals.white_color):
                    print(self.colorize_globals.white_color.__repr__())
                    _tick_checkboxes("White", False)
                    
                PyImGui.same_line(0,3)
                if self.game_button(IconsFontAwesome5.ICON_SQUARE,"##SalvageClearBluesButton","Clear Blues", width=20, height=20, color=self.colorize_globals.blue_color):
                    print(self.colorize_globals.blue_color.__repr__())
                    _tick_checkboxes("Blue", False)
                    
                PyImGui.same_line(0,3)
                if self.game_button(IconsFontAwesome5.ICON_SQUARE,"##SalvageClearPurplesButton","Clear Purples", width=20, height=20, color=self.colorize_globals.purple_color):
                    print(self.colorize_globals.purple_color.__repr__())
                    _tick_checkboxes("Purple", False)
                    
                PyImGui.same_line(0,3)
                if self.game_button(IconsFontAwesome5.ICON_SQUARE,"##SalvageClearGoldsButton","Clear Golds", width=20, height=20, color=self.colorize_globals.gold_color):
                    print(self.colorize_globals.gold_color.__repr__())
                    _tick_checkboxes("Gold", False)
                PyImGui.same_line(0,3)
                
                if self.game_button(IconsFontAwesome5.ICON_SQUARE,"##SalvageClearGreensButton","Clear Greens", width=20, height=20, color=self.colorize_globals.green_color):
                    print(self.colorize_globals.green_color.__repr__())
                    _tick_checkboxes("Green", False)
                    
            PyImGui.table_next_column()
            texture_file = ItemModelTextureMap[ModelID.Salvage_Kit.value]
            if ImGui.ImageButton("##text_unique_name", texture_file, 45, 45):
                GLOBAL_CACHE.Coroutines.append(SalvageCheckedItems(self.salvage_checkboxes))
            ImGui.show_tooltip("Salvage selected items.")    

            PyImGui.end_table()
                        
        PyImGui.end()
        PyImGui.pop_style_var(2)
    
    
    #endregion
    
    
    #region ColorizeItems
    
    def _can_draw_item(self, rarity:str):
        if rarity == "White":
            return self.colorize_globals.colorize_whites
        elif rarity == "Blue":
            return self.colorize_globals.colorize_blues
        elif rarity == "Green":
            return self.colorize_globals.colorize_greens
        elif rarity == "Purple":
            return self.colorize_globals.colorize_purples
        elif rarity == "Gold":
            return self.colorize_globals.colorize_golds
        else:
            return False
    
    def _get_parent_hash(self):
        return INVENTORY_FRAME_HASH
    
    def _get_offsets(self, bag_id:int, slot:int):
        return [0,0,0,bag_id-1,slot+2]
    
    def _get_frame_color(self, rarity:str):
        rarity_colors = {
            "White": self.colorize_globals.white_color,
            "Blue": self.colorize_globals.blue_color,
            "Green": self.colorize_globals.green_color,
            "Purple": self.colorize_globals.purple_color,
            "Gold": self.colorize_globals.gold_color,
            "Disabled": self.colorize_globals.disabled_color
        }
        color =  rarity_colors.get(rarity, Color(255, 255, 255, 255))
        _color = Color(color.r, color.g, color.b, color.a)
        if rarity != "Disabled":
            _color.a = 25
        else:
            _color.a = 200
        return _color.to_color()
        
    def _get_frame_outline_color(self, rarity:str):
        rarity_colors = {
            "White": self.colorize_globals.white_color,
            "Blue": self.colorize_globals.blue_color,
            "Green": self.colorize_globals.green_color,
            "Purple": self.colorize_globals.purple_color,
            "Gold": self.colorize_globals.gold_color,
            "Disabled": self.colorize_globals.disabled_color
        }
        color =  rarity_colors.get(rarity, Color(255, 255, 255, 255))
        _color = Color(color.r, color.g, color.b, color.a)
        if rarity != "Disabled":
            _color.a = 125
        else:
            _color.a = 255
        return _color.to_color()
    
    def _get_checkbox_color(self, rarity:str):
        rarity_colors = {
            "White": self.colorize_globals.white_color,
            "Blue": self.colorize_globals.blue_color,
            "Green": self.colorize_globals.green_color,
            "Purple": self.colorize_globals.purple_color,
            "Gold": self.colorize_globals.gold_color,
            "Disabled": self.colorize_globals.disabled_color
        }
        color = rarity_colors.get(rarity, Color(255, 255, 255, 255))
        _color = Color(color.r, color.g, color.b, color.a)
        return _color
        
    #endregion
    #region ColorizeItems
    def colorize_items(self):
        for bag_id in range(Bags.Backpack, Bags.Bag2+1):
            bag_to_check = ItemArray.CreateBagList(bag_id)
            item_array = ItemArray.GetItemArray(bag_to_check)
            
            for item_id in item_array:
                _,rarity = Item.Rarity.GetRarity(item_id)
                slot = Item.GetSlot(item_id)
                if not self._can_draw_item(rarity):
                    continue
                frame_id = UIManager.GetChildFrameID(self._get_parent_hash(),self._get_offsets(bag_id, slot))
                is_visible = UIManager.FrameExists(frame_id)
                if not is_visible:
                    continue
                UIManager().DrawFrame(frame_id, self._get_frame_color(rarity))
                UIManager().DrawFrameOutline(frame_id, self._get_frame_outline_color(rarity))
         
    #endregion
    #region ColorizeVaultItems
    def colorize_vault_items(self):
        def _get_parent_hash():
            return XUNLAI_VAULT_FRAME_HASH
        
        def _get_offsets(bag_id:int, slot:int):        
            return [0,bag_id-8,slot+2]
        
        if not Inventory.IsStorageOpen():
            return
        
        for bag_id in range(Bags.Storage1, Bags.Storage14+1):
            bag_to_check = ItemArray.CreateBagList(bag_id)
            item_array = ItemArray.GetItemArray(bag_to_check)
            
            for item_id in item_array:
                _,rarity = Item.Rarity.GetRarity(item_id)
                slot = Item.GetSlot(item_id)

                if not self._can_draw_item(rarity):
                        continue
                
                frame_id = UIManager.GetChildFrameID(_get_parent_hash(), _get_offsets(bag_id, slot))
                is_visible = UIManager.FrameExists(frame_id)
                if not is_visible:
                    continue
                UIManager().DrawFrame(frame_id, self._get_frame_color(rarity))
                UIManager().DrawFrameOutline(frame_id, self._get_frame_outline_color(rarity))

    #region ColorizeIDMasks       
    def colorize_id_masks(self):
        for bag_id in range(Bags.Backpack, Bags.Bag2+1):
            bag_to_check = ItemArray.CreateBagList(bag_id)
            item_array = ItemArray.GetItemArray(bag_to_check)
            
            for item_id in item_array:
                _,rarity = Item.Rarity.GetRarity(item_id)
                slot = Item.GetSlot(item_id)

                frame_id = UIManager.GetChildFrameID(self._get_parent_hash(), self._get_offsets(bag_id, slot))
                is_visible = UIManager.FrameExists(frame_id)
                if not is_visible:
                    continue
                
                frame_color = self._get_frame_color(rarity)
                frame_outline_color = self._get_frame_outline_color(rarity)
                
                if Item.Usage.IsIdentified(item_id) and not Item.Usage.IsIDKit(item_id):
                    frame_color = self._get_frame_color("Disabled")
                    frame_outline_color = self._get_frame_outline_color("Disabled")
                
                UIManager().DrawFrame(frame_id, frame_color)
                UIManager().DrawFrameOutline(frame_id, frame_outline_color)
                
                #--------------- Checkboxes ---------------
                if not Item.Usage.IsIdentified(item_id) and not Item.Usage.IsIDKit(item_id):
                    if item_id not in self.id_checkboxes:
                        self.id_checkboxes[item_id] = False
                    
                    left,top, right, bottom = UIManager.GetFrameCoords(frame_id)
                    self.id_checkboxes[item_id] = self.floating_checkbox(
                        f"{item_id}", 
                        self.id_checkboxes[item_id], 
                        right -25, 
                        bottom-25,
                        width=25,
                        height=25,
                        color = self._get_checkbox_color(rarity)
                    )
                            
                # Remove checkbox states that are set to False
                for item_id in list(self.id_checkboxes):
                    if not self.id_checkboxes[item_id]:
                        del self.id_checkboxes[item_id]
         
    #endregion
    #region ColorizeSalvageMasks       
    def colorize_salvage_masks(self):
        for bag_id in range(Bags.Backpack, Bags.Bag2+1):
            bag_to_check = ItemArray.CreateBagList(bag_id)
            item_array = ItemArray.GetItemArray(bag_to_check)
            
            for item_id in item_array:
                _,rarity = Item.Rarity.GetRarity(item_id)
                slot = Item.GetSlot(item_id)

                frame_id = UIManager.GetChildFrameID(self._get_parent_hash(), self._get_offsets(bag_id, slot))
                is_visible = UIManager.FrameExists(frame_id)
                if not is_visible:
                    continue
                
                frame_color = self._get_frame_color(rarity)
                frame_outline_color = self._get_frame_outline_color(rarity)
                
                is_white =  rarity == "White"
                is_identified = Item.Usage.IsIdentified(item_id)
                is_salvageable = Item.Usage.IsSalvageable(item_id)
                is_salvage_kit = Item.Usage.IsLesserKit(item_id)
                
                if not (((is_white and is_salvageable) or (is_identified and is_salvageable)) or is_salvage_kit):
                    frame_color = self._get_frame_color("Disabled")
                    frame_outline_color = self._get_frame_outline_color("Disabled")
                
                UIManager().DrawFrame(frame_id, frame_color)
                UIManager().DrawFrameOutline(frame_id, frame_outline_color) 
                
                #--------------- Checkboxes ---------------
                if (((is_white and is_salvageable) or (is_identified and is_salvageable)) and not is_salvage_kit):
                    if item_id not in self.salvage_checkboxes:
                        self.salvage_checkboxes[item_id] = False
                    
                    left,top, right, bottom = UIManager.GetFrameCoords(frame_id)
                    self.salvage_checkboxes[item_id] = self.floating_checkbox(
                        f"{item_id}", 
                        self.salvage_checkboxes[item_id], 
                        right -25, 
                        bottom-25,
                        width=25,
                        height=25,
                        color = self._get_checkbox_color(rarity)
                    )
                            
                # Remove checkbox states that are set to False
                for item_id in list(self.salvage_checkboxes):
                    if not self.salvage_checkboxes[item_id]:
                        del self.salvage_checkboxes[item_id]

    #region DrawDepositButtons
    def draw_deposit_buttons(self):
        for bag_id in range(Bags.Backpack, Bags.Bag2+1):
            bag_to_check = ItemArray.CreateBagList(bag_id)
            item_array = ItemArray.GetItemArray(bag_to_check)
            
            for item_id in item_array:
                _,rarity = Item.Rarity.GetRarity(item_id)
                slot = Item.GetSlot(item_id)

                frame_id = UIManager.GetChildFrameID(self._get_parent_hash(),self._get_offsets(bag_id, slot))
                is_visible = UIManager.FrameExists(frame_id)
                if not is_visible:
                    continue
                
                left,top, right, bottom = UIManager.GetFrameCoords(frame_id)
                if self.floating_button(caption=IconsFontAwesome5.ICON_CARET_SQUARE_RIGHT,
                                        name=f"DepositButton{item_id}",
                                        x=right-25, 
                                        y=bottom-25, 
                                        width=25, 
                                        height=25, 
                                        color=self._get_checkbox_color(rarity)):
                    GLOBAL_CACHE.Inventory.DepositItemToStorage(item_id)
                    
            
                    
    def draw_withdraw_buttons(self):
        def _get_parent_hash():
            return XUNLAI_VAULT_FRAME_HASH
        
        def _get_offsets(bag_id:int, slot:int):        
            return [0,bag_id-8,slot+2]
        
        for bag_id in range(Bags.Storage1, Bags.Storage14+1):
            bag_to_check = ItemArray.CreateBagList(bag_id)
            item_array = ItemArray.GetItemArray(bag_to_check)
            
            for item_id in item_array:
                _,rarity = Item.Rarity.GetRarity(item_id)
                slot = Item.GetSlot(item_id)

                frame_id = UIManager.GetChildFrameID(_get_parent_hash(),_get_offsets(bag_id, slot))
                is_visible = UIManager.FrameExists(frame_id)
                if not is_visible:
                    continue
                
                left,top, right, bottom = UIManager.GetFrameCoords(frame_id)
                if self.floating_button(caption=IconsFontAwesome5.ICON_CARET_SQUARE_LEFT,
                                        name=f"WithdrawButton{item_id}",
                                        x=right-25, 
                                        y=bottom-25, 
                                        width=25, 
                                        height=25, 
                                        color=self._get_checkbox_color(rarity)):
                    GLOBAL_CACHE.Inventory.WithdrawItemFromStorage(item_id)
                
         
    #endregion
                


    def draw_colorize_options(self):
        selected_tab = self.tab_icons[self.selected_tab_icon_index]
        if selected_tab.icon_name == "##ColorizeTab":
            self.draw_colorize_bottom_strip()
            self.colorize_items()
            self.colorize_vault_items()
        elif selected_tab.icon_name == "##AutoHandlerTab":
            self.DrawAutoHandler()
            self.show_model_id_dialog_popup()
        elif selected_tab.icon_name == "##IDTab":
            self.draw_id_bottom_strip()
            self.colorize_id_masks()
        elif selected_tab.icon_name == "##SalvageTab":
            self.draw_salvage_bottom_strip()
            self.colorize_salvage_masks()
        elif selected_tab.icon_name == "##XunlaiVaultTab":
            if not Inventory.IsStorageOpen():
                Inventory.OpenXunlaiWindow()
            self.colorize_items()
            self.colorize_vault_items()
            self.draw_deposit_buttons()
            self.draw_withdraw_buttons()
        elif selected_tab.icon_name == "##TradeTab":
            pass
   
   
    #region AtuoHandler

    def show_model_id_dialog_popup(self):
        if AUTO_HANDLER.show_dialog_popup:
            PyImGui.open_popup("ModelID Lookup")
            AUTO_HANDLER.show_dialog_popup = False  # trigger only once

        if PyImGui.begin_popup_modal("ModelID Lookup", True,PyImGui.WindowFlags.AlwaysAutoResize):
            PyImGui.text("ModelID Lookup")
            PyImGui.separator()

            # Input + filter mode
            AUTO_HANDLER.model_id_search = PyImGui.input_text("Search", AUTO_HANDLER.model_id_search)
            search_lower = AUTO_HANDLER.model_id_search.strip().lower()

            AUTO_HANDLER.model_id_search_mode = PyImGui.radio_button("Contains", AUTO_HANDLER.model_id_search_mode, 0)
            PyImGui.same_line(0, -1)
            AUTO_HANDLER.model_id_search_mode = PyImGui.radio_button("Starts With", AUTO_HANDLER.model_id_search_mode, 1)

            # Build reverse lookup: model_id → name
            model_id_to_name = {member.value: name for name, member in ModelID.__members__.items()}

            PyImGui.separator()

            if PyImGui.begin_table("ModelIDTable", 2):
                PyImGui.table_setup_column("All Models", PyImGui.TableColumnFlags.WidthFixed)
                PyImGui.table_setup_column("Blacklisted Models", PyImGui.TableColumnFlags.WidthStretch)
            
                PyImGui.table_headers_row()
                PyImGui.table_next_column()
                # LEFT: All Models
                if PyImGui.begin_child("ModelIDList", (295, 375), True, PyImGui.WindowFlags.NoFlag):
                    sorted_model_ids = sorted(
                        [(name, member.value) for name, member in ModelID.__members__.items()],
                        key=lambda x: x[0].lower()
                    )
                    for name, model_id in sorted_model_ids:
                        name_lower = name.lower()
                        if search_lower:
                            if AUTO_HANDLER.model_id_search_mode == 0 and search_lower not in name_lower:
                                continue
                            if AUTO_HANDLER.model_id_search_mode == 1 and not name_lower.startswith(search_lower):
                                continue

                        label = f"{name} ({model_id})"
                        if PyImGui.selectable(label, False, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0)):
                            if model_id not in AUTO_HANDLER.salvage_blacklist:
                                AUTO_HANDLER.salvage_blacklist.append(model_id)
                PyImGui.end_child()

                # RIGHT: Blacklist
                PyImGui.table_next_column()
                if PyImGui.begin_child("BlacklistModelIDList", (295, 375), True, PyImGui.WindowFlags.NoFlag):
                    # Create list of (name, model_id) and sort by name
                    sorted_blacklist = sorted(
                        [(model_id_to_name.get(model_id, "Unknown"), model_id)
                        for model_id in AUTO_HANDLER.salvage_blacklist],
                        key=lambda x: x[0].lower()
                    )

                    for name, model_id in sorted_blacklist:
                        label = f"{name} ({model_id})"
                        if PyImGui.selectable(label, False, PyImGui.SelectableFlags.NoFlag, (0.0, 0.0)):
                            AUTO_HANDLER.salvage_blacklist.remove(model_id)
                PyImGui.end_child()



                PyImGui.end_table()

            if PyImGui.button("Close"):
                PyImGui.close_current_popup()

            PyImGui.end_popup_modal()

    def DrawAutoHandler(self):
        global global_vars
        
        content_frame = UIManager.GetChildFrameID(self._get_parent_hash(), [0])
        left, top, right, bottom = UIManager.GetFrameCoords(content_frame)
        y_offset = 2
        x_offset = 0
        height = bottom - top + y_offset
        width = right - left + x_offset
        if width < 100:
            width = 100
        if height < 100:
            height = 100
            
        UIManager().DrawFrame(content_frame, Utils.RGBToColor(0, 0, 0, 255))
        
        #flags= ImGui.PushTransparentWindow()
        
        flags = ( PyImGui.WindowFlags.NoCollapse | 
                PyImGui.WindowFlags.NoTitleBar |
                PyImGui.WindowFlags.NoResize
        )
        PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding,0.0)
        
        PyImGui.set_next_window_pos(left, top)
        PyImGui.set_next_window_size(width, height)
        
        if PyImGui.begin("Embedded AutoHandler",True, flags):
            if AUTO_HANDLER.module_active:
                active_button = IconsFontAwesome5.ICON_TOGGLE_ON
                active_tooltip = "AutoHandler is active"
            else:
                active_button = IconsFontAwesome5.ICON_TOGGLE_OFF
                active_tooltip = "AutoHandler is inactive"
                
            AUTO_HANDLER.module_active = ImGui.toggle_button(active_button + "##AutoHandlerActive", AUTO_HANDLER.module_active)
            ImGui.show_tooltip(active_tooltip)
            
            PyImGui.same_line(0,-1)
            PyImGui.text("|")
            PyImGui.same_line(0,-1)
            
            if PyImGui.button(IconsFontAwesome5.ICON_SAVE + "##autosalvsave"):
                AUTO_HANDLER.save_to_ini()
                ConsoleLog(MODULE_NAME, "Settings saved to Auto Inv.ini", Py4GW.Console.MessageType.Success)
            ImGui.show_tooltip("Save Settings")
            PyImGui.same_line(0,-1)
            if PyImGui.button(IconsFontAwesome5.ICON_SYNC + "##autosalvreload"):
                AUTO_HANDLER.load_from_ini(AUTO_HANDLER.ini)
                AUTO_HANDLER.lookup_throttle.SetThrottleTime(AUTO_HANDLER._LOOKUP_TIME)
                AUTO_HANDLER.lookup_throttle.Reset()
                ConsoleLog(MODULE_NAME, "Settings reloaded from Auto Inv.ini", Py4GW.Console.MessageType.Success)
            ImGui.show_tooltip("Reload Settings")
            
            PyImGui.separator()
            
            PyImGui.text("Lookup Time (ms):")
            PyImGui.same_line(0,-1)
            
            PyImGui.push_item_width(150)
            AUTO_HANDLER._LOOKUP_TIME = PyImGui.input_int("##lookup_time",  AUTO_HANDLER._LOOKUP_TIME)
            PyImGui.pop_item_width()
            ImGui.show_tooltip("Changes will take effect after the next lookup.")
            
            if not GLOBAL_CACHE.Map.IsExplorable():
                PyImGui.text("Auto Lookup only runs in explorable.")
            else:
                remaining = AUTO_HANDLER.lookup_throttle.GetTimeRemaining() / 1000  # convert ms to seconds
                PyImGui.text(f"Next Lookup in: {remaining:.1f} s")
            
            PyImGui.separator()
            
            if PyImGui.begin_tab_bar("AutoID&SalvageTabs"):
                if PyImGui.begin_tab_item("Identification"):
                    state = AUTO_HANDLER.id_whites
                    color = self.colorize_globals.white_color
                    if self.game_toggle_button("##autoIDWhite","Identify White Items",state, width=20, height=20, color=color):
                        AUTO_HANDLER.id_whites = not AUTO_HANDLER.id_whites
                    PyImGui.same_line(0,3)
                    state = AUTO_HANDLER.id_blues
                    color = self.colorize_globals.blue_color
                    if self.game_toggle_button("##autoIDBlue","Identify Blue Items",state, width=20, height=20, color=color):
                        AUTO_HANDLER.id_blues = not AUTO_HANDLER.id_blues
                        
                    PyImGui.same_line(0,3)
                    state = AUTO_HANDLER.id_purples
                    color = self.colorize_globals.purple_color
                    if self.game_toggle_button("##autoIDPurple","Identify Purple Items",state, width=20, height=20, color=color):
                        AUTO_HANDLER.id_purples = not AUTO_HANDLER.id_purples
                    PyImGui.same_line(0,3)
                    state = AUTO_HANDLER.id_golds
                    color = self.colorize_globals.gold_color
                    if self.game_toggle_button("##autoIDGold","Identify Gold Items",state, width=20, height=20, color=color):
                        AUTO_HANDLER.id_golds = not AUTO_HANDLER.id_golds
                        
                    PyImGui.end_tab_item()
                if PyImGui.begin_tab_item("Salvage"):
                    state = AUTO_HANDLER.salvage_whites
                    color = self.colorize_globals.white_color
                    if self.game_toggle_button("##autoSalvageWhite","Salvage White Items",state, width=20, height=20, color=color):
                        AUTO_HANDLER.salvage_whites = not AUTO_HANDLER.salvage_whites
                    
                    PyImGui.same_line(0,3)
                    state = AUTO_HANDLER.salvage_blues
                    color = self.colorize_globals.blue_color
                    if self.game_toggle_button("##autoSalvageBlue","Salvage Blue Items",state, width=20, height=20, color=color):
                        AUTO_HANDLER.salvage_blues = not AUTO_HANDLER.salvage_blues
                        
                    PyImGui.same_line(0,3)
                    state = AUTO_HANDLER.salvage_purples
                    color = self.colorize_globals.purple_color
                    if self.game_toggle_button("##autoSalvagePurple","Salvage Purple Items",state, width=20, height=20, color=color):
                        AUTO_HANDLER.salvage_purples = not AUTO_HANDLER.salvage_purples
                        
                    PyImGui.same_line(0,3)
                    state = AUTO_HANDLER.salvage_golds
                    color = self.colorize_globals.gold_color
                    if self.game_toggle_button("##autoSalvageGold","Salvage Gold Items",state, width=20, height=20, color=color):
                        AUTO_HANDLER.salvage_golds = not AUTO_HANDLER.salvage_golds

                    PyImGui.separator()
                    
                    if PyImGui.collapsing_header("Ignore Items"):
                        PyImGui.text(f"{len(AUTO_HANDLER.salvage_blacklist)} Blacklisted ModelIDs")

                        if PyImGui.button("Manage Ignore List"):
                            AUTO_HANDLER.show_dialog_popup = True

                            
                    PyImGui.end_tab_item()
                if PyImGui.begin_tab_item("Deposit"):
                    AUTO_HANDLER.deposit_materials = ImGui.toggle_button( IconsFontAwesome5.ICON_HAMMER + "##depositmaterials", AUTO_HANDLER.deposit_materials)
                    ImGui.show_tooltip("Deposit Materials")
                    PyImGui.same_line(0,3)
                    AUTO_HANDLER.deposit_trophies = ImGui.toggle_button(IconsFontAwesome5.ICON_TROPHY + "##deposittrophies", AUTO_HANDLER.deposit_trophies)
                    ImGui.show_tooltip("Deposit Trophies")
                    PyImGui.same_line(0,3)
                    AUTO_HANDLER.deposit_event_items = ImGui.toggle_button(IconsFontAwesome5.ICON_HAT_WIZARD + "##depositeventitems", AUTO_HANDLER.deposit_event_items)
                    ImGui.show_tooltip("Deposit Event Items")
                    
                    PyImGui.same_line(0,3)
                    state = AUTO_HANDLER.deposit_blues
                    color = self.colorize_globals.blue_color
                    
                    if self.game_toggle_button("##depositBlue","Deposit Blue Items",state, width=20, height=20, color=color):
                        AUTO_HANDLER.deposit_blues = not AUTO_HANDLER.deposit_blues
                    PyImGui.same_line(0,3)
                    state = AUTO_HANDLER.deposit_purples
                    color = self.colorize_globals.purple_color
                    if self.game_toggle_button("##depositPurple","Deposit Purple Items",state, width=20, height=20, color=color):
                        AUTO_HANDLER.deposit_purples = not AUTO_HANDLER.deposit_purples
                    PyImGui.same_line(0,3)
                    state = AUTO_HANDLER.deposit_golds
                    color = self.colorize_globals.gold_color
                    if self.game_toggle_button("##depositGold","Deposit Gold Items",state, width=20, height=20, color=color):
                        AUTO_HANDLER.deposit_golds = not AUTO_HANDLER.deposit_golds
                    PyImGui.same_line(0,3)
                    state = AUTO_HANDLER.deposit_greens
                    color = self.colorize_globals.green_color
                    if self.game_toggle_button("##depositGreen","Deposit Green Items",state, width=20, height=20, color=color):
                        AUTO_HANDLER.deposit_greens = not AUTO_HANDLER.deposit_greens
                    
                    PyImGui.separator()
                    PyImGui.text("Keep Gold:")
                    PyImGui.same_line(0,-1)
                    AUTO_HANDLER.keep_gold = PyImGui.input_int("##keep_gold", AUTO_HANDLER.keep_gold, 1, 1000, PyImGui.InputTextFlags.NoFlag)
                    ImGui.show_tooltip("Keep Gold in inventory, deposit the rest")
                    
                    PyImGui.end_tab_item()
                PyImGui.end_tab_bar()
        PyImGui.end() 
        PyImGui.pop_style_var(1)

    
#region IdentifyCheckedItems         
 
def IdentifyCheckedItems(id_checkboxes: Dict[int, bool]):
    identified_items = 0
    for item_id, checked in list(id_checkboxes.items()):
        if checked:
            first_id_kit = Inventory.GetFirstIDKit()
            if first_id_kit == 0:
                Py4GW.Console.Log(MODULE_NAME, "No ID Kit found in inventory.", Py4GW.Console.MessageType.Warning)
                return
            
            item_instance = PyItem.PyItem(item_id)
            if item_instance.is_identified:
                id_checkboxes[item_id] = False
                continue
            
            ActionQueueManager().AddAction("ACTION", Inventory.IdentifyItem,item_id, first_id_kit)
            identified_items += 1
            while True:
                yield from Routines.Yield.wait(50)
                item_instance.GetContext()
                if item_instance.is_identified:
                    break
            id_checkboxes[item_id] = False
        yield from Routines.Yield.wait(50)
        
    ConsoleLog(MODULE_NAME, f"Identified {identified_items} items.", Py4GW.Console.MessageType.Info)


#region IdentifyCheckedItems         
def SalvageCheckedItems(salvage_checkboxes: Dict[int, bool]):
    salvaged_items = 0
    items_to_salvage = list(salvage_checkboxes.items())

    for item_id, checked in items_to_salvage:
        while checked:
            first_salv_kit = Inventory.GetFirstSalvageKit(use_lesser=True)
            if first_salv_kit == 0:
                Py4GW.Console.Log(MODULE_NAME, "No Salvage Kit found in inventory.", Py4GW.Console.MessageType.Warning)
                return

            quantity = Item.Properties.GetQuantity(item_id)
            if quantity == 0:
                salvage_checkboxes[item_id] = False
                break

            is_purple = Item.Rarity.IsPurple(item_id)
            is_gold = Item.Rarity.IsGold(item_id)
            require_materials_confirmation = is_purple or is_gold
            wait_for_consumption = quantity == 1

            ActionQueueManager().AddAction("ACTION", Inventory.SalvageItem, item_id, first_salv_kit)

            if require_materials_confirmation:
                yield from Routines.Yield.Items._wait_for_salvage_materials_window()
                ActionQueueManager().AddAction("ACTION", Inventory.AcceptSalvageMaterialsWindow)
                yield from Routines.Yield.wait(50)

            if wait_for_consumption:
                while True:
                    bag_list = ItemArray.CreateBagList(Bags.Backpack, Bags.BeltPouch, Bags.Bag1, Bags.Bag2)
                    item_array = ItemArray.GetItemArray(bag_list)
                    if item_id not in item_array:
                        salvage_checkboxes[item_id] = False
                        salvaged_items += 1
                        break
                    yield from Routines.Yield.wait(50)
            else:
                item_instance = PyItem.PyItem(item_id)
                while True:
                    yield from Routines.Yield.wait(50)
                    item_instance.GetContext()
                    if item_instance.quantity < quantity:
                        salvaged_items += 1
                        break

            yield from Routines.Yield.wait(50)
            # Refresh status for the next iteration
            checked = salvage_checkboxes.get(item_id, False)

    ConsoleLog(MODULE_NAME, f"Salvaged {salvaged_items} items.", Py4GW.Console.MessageType.Info)

             
class Globals:     
    def __init__(self, ui_handler: WidgetUI):
        self.ui_handler = ui_handler
        self.inventory_frame_hash = INVENTORY_FRAME_HASH
        self.inventory_frame_id = 0
        self.inventory_frame_exists = False
        self.inventory_check_throttle_timer = ThrottledTimer(100)
        self.widget_active = True
        
    def update (self):
        if not Routines.Checks.Map.MapValid():
            self.inventory_frame_exists = False
            self.inventory_frame_id = 0
            AUTO_HANDLER.lookup_throttle.Reset()
            AUTO_HANDLER.outpost_handled = False
            return False
        
        if not AUTO_HANDLER.initialized:
            AUTO_HANDLER.load_from_ini(AUTO_HANDLER.ini)
            AUTO_HANDLER.lookup_throttle.SetThrottleTime(AUTO_HANDLER._LOOKUP_TIME)
            AUTO_HANDLER.lookup_throttle.Reset()
            AUTO_HANDLER.initialized = True
            ConsoleLog(MODULE_NAME, "Auto Widget Options initialized", Py4GW.Console.MessageType.Success)
            
        if not GLOBAL_CACHE.Map.IsExplorable():
            AUTO_HANDLER.lookup_throttle.Stop()
            AUTO_HANDLER.status = "Idle"
            if not AUTO_HANDLER.outpost_handled and AUTO_HANDLER.module_active:
                GLOBAL_CACHE.Coroutines.append(AUTO_HANDLER.IDSalvageDepositItems())
                AUTO_HANDLER.outpost_handled = True
        else:      
            if AUTO_HANDLER.lookup_throttle.IsStopped():
                AUTO_HANDLER.lookup_throttle.Start()
                AUTO_HANDLER.status = "Idle"
                
        if AUTO_HANDLER.lookup_throttle.IsExpired():
            AUTO_HANDLER.lookup_throttle.SetThrottleTime(AUTO_HANDLER._LOOKUP_TIME)
            AUTO_HANDLER.lookup_throttle.Stop()
            if AUTO_HANDLER.status == "Idle" and AUTO_HANDLER.module_active:
                GLOBAL_CACHE.Coroutines.append(AUTO_HANDLER.IDAndSalvageItems())
            AUTO_HANDLER.lookup_throttle.Start()       
        
        if not UIManager.IsWindowVisible(WindowID.WindowID_InventoryBags):
            self.inventory_frame_exists = False
            self.inventory_frame_id = 0
            return False
        
        if not self.inventory_check_throttle_timer.IsExpired():
            return True
        
        self.inventory_frame_id = UIManager.GetFrameIDByHash(self.inventory_frame_hash)
        self.inventory_frame_exists = UIManager.FrameExists(self.inventory_frame_id)
        
        if self.inventory_frame_exists:
            self.ui_handler.set_inventory_frame_id(self.inventory_frame_id)
            self.widget_active = self.ui_handler.widget_active
        
        return self.inventory_frame_exists  
            

    

class WidgetConfig:
    def __init__(self):
        self.id_checkboxes: Dict[int, bool] = {}
        self.salvage_checkboxes: Dict[int, bool] = {}
        self.UI = WidgetUI(inventory_frame_id=0,
                           id_checkboxes=self.id_checkboxes,
                           salvage_checkboxes=self.salvage_checkboxes)
        self.globals = Globals(self.UI)


widget_config = WidgetConfig()

def configure():
    pass


def main():
    global widget_config
    try:
        if not widget_config.globals.update(): return

        widget_config.UI.draw_widget_toggle_button()
        
        if not widget_config.globals.widget_active: return  
        
        widget_config.UI.draw_button_strip()
        widget_config.UI.draw_colorize_options()
        
        
        
        
        


    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise


    
if __name__ == "__main__":
    main()
