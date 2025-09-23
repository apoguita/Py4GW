from typing import TypeAlias, Optional
from ..Overlay import Overlay
import PyImGui
from .Textures import ThemeTextures, TextureState
from .types import StyleTheme

class WindowModule:
        _windows : dict[str, 'WindowModule'] = {}
        
        def __init__(self, module_name="", window_name="", window_size=(100,100), window_pos=(0,0), window_flags=PyImGui.WindowFlags.NoFlag, collapse= False, can_close=False, forced_theme: Optional[StyleTheme] = None):
            self.module_name = module_name
            
            self.window_name = window_name if window_name else module_name
            self.window_size = window_size
            self.collapse = collapse
            
            if window_pos == (0,0):
                overlay = Overlay()
                screen_width, screen_height = overlay.GetDisplaySize().x, overlay.GetDisplaySize().y
                #set position to the middle of the screen
                self.window_pos = (screen_width / 2 - window_size[0] / 2, screen_height / 2 - window_size[1] / 2)
            else:
                self.window_pos = window_pos
            self.window_flags = window_flags
            
            self.can_close = can_close
            self.can_resize = (int(self.window_flags) & int(PyImGui.WindowFlags.NoResize)) == 0 and (int(self.window_flags) & int(PyImGui.WindowFlags.AlwaysAutoResize)) == 0

            self.end_pos = window_pos  # Initialize end_pos to window_pos
            self.first_run = True
            
            #internal variables
            self.window_display_name = self.window_name.split("##")[0]
            self.window_name_size : tuple[float, float] = PyImGui.calc_text_size(self.window_display_name)
            
            self.open = True
            self.theme : StyleTheme | None = forced_theme
            
            self.__decorated_window_min_size = (self.window_name_size[0] + 40, 32.0) # Internal use only
            self.__decorators_left = window_pos[0] - 15 # Internal use only
            self.__decorators_top = window_pos[1] - (26) # Internal use only
            
            self.__decorators_right = self.__decorators_left + window_size[0] + 30 # Internal use only
            self.__decorators_bottom = self.__decorators_top + window_size[1] + 14 + (26) # Internal use only
            
            self.__decorators_width = self.__decorators_right - self.__decorators_left # Internal use only
            self.__decorators_height = self.__decorators_bottom - self.__decorators_top # Internal use only
            
            self.__close_button_rect = (self.__decorators_right - 29, self.__decorators_top + 9, 11, 11) # Internal use only
            self.__title_bar_rect = (self.__decorators_left + 5, self.__decorators_top + 2, self.__decorators_width - 10, 26) # Internal use only
            
            self.__resize = False # Internal use only
            self.__set_focus = False # Internal use only

            self.__dragging = False # Internal use only
            self.__drag_started = False # Internal use only
            #endregion

            #debug variables
            self.collapsed_status = True
            self.tracking_position = self.window_pos
            
            WindowModule._windows[self.window_name] = self
            
        def get_theme(self) -> StyleTheme:
            from .ImGuisrc import ImGui
            """
            Returns the current theme of the ImGui module.
            """

            theme = self.theme if self.theme else ImGui.get_style().Theme

            return theme
             

        def initialize(self):
            if not self.module_name:
                return
            
            if self.first_run:
                PyImGui.set_next_window_size(self.window_size[0], self.window_size[1])     
                PyImGui.set_next_window_pos(self.window_pos[0], self.window_pos[1])
                PyImGui.set_next_window_collapsed(self.collapse, 0)
                self.first_run = False                

        def begin(self, p_open: Optional[bool] = None, flags: PyImGui.WindowFlags = PyImGui.WindowFlags.NoFlag) -> bool:   
            from .ImGuisrc import ImGui         
            self.__current_theme = self.get_theme()
            #push_theme = self.__current_theme != ImGui.get_style().Theme
            #if push_theme:
            #    ImGui.push_theme(self.__current_theme)
                                  
            if p_open is not None:
                self.open = p_open
                
            if flags != PyImGui.WindowFlags.NoFlag:
                self.window_flags = flags
        
            is_expanded = not self.collapse
            is_first_run = self.first_run
            
            self.can_resize = (int(self.window_flags) & int(PyImGui.WindowFlags.NoResize)) == 0 and (int(self.window_flags) & int(PyImGui.WindowFlags.AlwaysAutoResize)) == 0
            
            if self.first_run:
                self.initialize()
                
            match (self.__current_theme):
                case StyleTheme.Guild_Wars:
                    has_always_auto_resize = (int(self.window_flags) & int(PyImGui.WindowFlags.AlwaysAutoResize)) != 0
                    
                    # PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 10, 10)
                    internal_flags = int(PyImGui.WindowFlags.NoTitleBar | PyImGui.WindowFlags.NoBackground) | int(self.window_flags)
                    self.__dragging = PyImGui.is_mouse_dragging(0, -1) and self.__dragging and self.__drag_started
                    if not PyImGui.is_mouse_dragging(0, -1) and not PyImGui.is_mouse_down(0):
                        self.__drag_started = False
                                
                    if self.open and is_expanded: 
                        if not is_first_run:
                            if self.__resize or self.window_size[0] < self.__decorated_window_min_size[0] or self.window_size[1] < self.__decorated_window_min_size[1]:
                                if not has_always_auto_resize:
                                    self.window_size = (max(self.__decorated_window_min_size[0], self.window_size[0]), max(self.__decorated_window_min_size[1], self.window_size[1]))
                                    PyImGui.set_next_window_size((self.window_size[0], self.window_size[1]), PyImGui.ImGuiCond.Always)            
                                self.__resize = False
                        
                    # push_style_color(PyImGui.ImGuiCol.WindowBg, (0, 0, 0, 0.85))
                        
                    if not is_expanded:
                        # Remove PyImGui.WindowFlags.MenuBar and PyImGui.WindowFlags.AlwaysAutoResize from internal_flags when not expanded
                        internal_flags &= ~int(PyImGui.WindowFlags.MenuBar)
                        internal_flags &= ~int(PyImGui.WindowFlags.AlwaysAutoResize)
                        internal_flags |= int(PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse| PyImGui.WindowFlags.NoResize| PyImGui.WindowFlags.NoMouseInputs)
                        
                    if self.__set_focus:
                        internal_flags &= ~int(PyImGui.WindowFlags.AlwaysAutoResize)
                        
                    _, open = PyImGui.begin_with_close(name = self.window_name, p_open=self.open, flags=internal_flags)

                    # pop_style_color(1)
                                            
                    self.open = open               
                                    
                    if self.__set_focus and not self.__dragging and not self.__drag_started:
                        PyImGui.set_window_focus(self.window_name)
                        self.__set_focus = False
                    
                    if self.__dragging:
                        PyImGui.set_window_focus(self.window_name)
                        PyImGui.set_window_focus(f"{self.window_name}##titlebar_fake")

                    if self.open:
                        self.__draw_decorations()

                    # PyImGui.pop_style_var(1)
                    
                    if has_always_auto_resize:                    
                        cursor = PyImGui.get_cursor_pos()
                        PyImGui.dummy(int(self.window_name_size[0] + 20), 0)
                        PyImGui.set_cursor_pos(cursor[0], cursor[1])
                                    
                case _:  
                    if self.can_close:              
                        expanded, self.open = PyImGui.begin_with_close(name = self.window_name, p_open=self.open, flags=self.window_flags)
                        self.collapse = not expanded
                    else:
                        self.collapse = not PyImGui.begin(self.window_name, self.window_flags)
                        self.open = True

            if is_expanded and not self.collapse and self.open and not self.__dragging:
                self.window_size = PyImGui.get_window_size()
                          
            #if push_theme:
            #    pop_theme()

            return self.open
        

        def process_window(self):
            self.collapsed_status = PyImGui.is_window_collapsed()
            self.end_pos = PyImGui.get_window_pos()

        def end(self):
            PyImGui.end()
            
        def __draw_decorations(self): 
            from .ImGuisrc import ImGui   
            from ..py4gwcorelib_src.Utils import Utils              
            has_title_bar = (int(self.window_flags) & int(PyImGui.WindowFlags.NoTitleBar)) == 0
            
            if not self.collapse and self.open:
                window_pos = PyImGui.get_window_pos()
                window_size = PyImGui.get_window_size()            
                                                    
                self.__decorators_left = window_pos[0] - 15
                self.__decorators_top = window_pos[1] - (26 if has_title_bar else 5)
                
                self.__decorators_right = self.__decorators_left + window_size[0] + 30
                self.__decorators_bottom = self.__decorators_top + window_size[1] + 14 + (26 if has_title_bar else 5)
                
                self.__decorators_width = self.__decorators_right - self.__decorators_left
                self.__decorators_height = self.__decorators_bottom - self.__decorators_top
                self.__close_button_rect = (self.__decorators_right - 29, self.__decorators_top + 9, 11, 11)

                PyImGui.push_clip_rect(self.__decorators_left, self.__decorators_top, self.__decorators_width, self.__decorators_height, False)   
                state = TextureState.Normal
                                
                if ImGui.is_mouse_in_rect(self.__close_button_rect) and ((int(self.window_flags) & int(PyImGui.WindowFlags.NoMouseInputs)) == 0):
                    if PyImGui.is_mouse_down(0):
                        state = TextureState.Active
                    else:
                        state = TextureState.Hovered
                                        
                # Draw the background
                has_background = not self.window_flags or ((int(self.window_flags) & int(PyImGui.WindowFlags.NoBackground)) == 0)                
                if has_background:
                    ThemeTextures.Empty_Pixel.value.draw_in_drawlist(
                        x=self.__decorators_left + 15,
                        y=self.__decorators_top + 5,
                        size=(self.__decorators_width - 30, self.__decorators_height - 15),
                        tint=(0,0,0,215)
                    )

                if self.can_resize:
                    ThemeTextures.Window_Frame_Bottom.value.get_texture().draw_in_drawlist(
                        x=self.__decorators_left + 5,
                        y=self.__decorators_bottom - 57,
                        size=(self.__decorators_width - 10, 60)
                    )
                else:
                    ThemeTextures.Window_Frame_Bottom_No_Resize.value.get_texture().draw_in_drawlist(
                        x=self.__decorators_left + 5,
                        y=self.__decorators_bottom - 57,
                        size=(self.__decorators_width - 10, 60)
                    )

                ThemeTextures.Window_Frame_Center.value.get_texture().draw_in_drawlist(
                    x=self.__decorators_left + 5,
                    y=self.__decorators_top + (26 if has_title_bar else 11) + 35,
                    size=(self.__decorators_width - 10, self.__decorators_height - 35 - 60)
                )
                
                
                if has_title_bar:      
                    ThemeTextures.Window_Frame_Top.value.get_texture().draw_in_drawlist(
                        x=self.__decorators_left + 5,
                        y=self.__decorators_top + 26,
                        size=(self.__decorators_width - 10, 35)
                    )

                    ThemeTextures.Title_Bar.value.get_texture().draw_in_drawlist(
                        x=self.__decorators_left + 5,
                        y=self.__decorators_top,
                        size=(self.__decorators_width - 10, 26)
                    )
                
                    if self.can_close:
                        ThemeTextures.Empty_Pixel.value.draw_in_drawlist(
                            x=self.__close_button_rect[0] - 1,
                            y=self.__close_button_rect[1] - 1,
                            size=(self.__close_button_rect[2] + 2, self.__close_button_rect[3] + 2),
                            tint=(0,0,0,255)
                        )

                        ThemeTextures.Close_Button.value.get_texture().draw_in_drawlist(
                            x=self.__close_button_rect[0],
                            y=self.__close_button_rect[1],
                            size=self.__close_button_rect[2:],
                            state=state
                        )
                        
                    self.__title_bar_rect = (self.__decorators_left + 10, self.__decorators_top + 2, self.__decorators_width - 10, 26)
                  
                    # Draw the title text
                    PyImGui.push_clip_rect(
                        self.__title_bar_rect[0] + 15,
                        self.__title_bar_rect[1] + 7,
                        self.__title_bar_rect[2] - 15 - 29,
                        self.__title_bar_rect[3] - 7,
                        False
                    )
                    PyImGui.draw_list_add_text(self.__title_bar_rect[0] + 15, self.__title_bar_rect[1] + 7, Utils.RGBToColor(255,255,255,255), self.window_display_name)
                    PyImGui.pop_clip_rect()
                    
                    self.__draw_title_bar_fake(self.__title_bar_rect)
                else:
                    ThemeTextures.Window_Frame_Top_NoTitleBar.value.get_texture().draw_in_drawlist(
                        x=self.__decorators_left + 5,
                        y=self.__decorators_top,
                        size=(self.__decorators_width - 10, 50)
                    )

            else:
                window_pos = PyImGui.get_window_pos()
                
                self.__decorators_left = window_pos[0] - 15
                self.__decorators_top = window_pos[1] - (26)

                self.__decorators_right = self.__decorators_left + self.__decorated_window_min_size[0] + 30
                self.__decorators_bottom = window_pos[1]

                self.__decorators_width = self.__decorators_right - self.__decorators_left
                self.__decorators_height = self.__decorators_bottom - self.__decorators_top
                self.__close_button_rect = (self.__decorators_right - 29, self.__decorators_top + 9, 11, 11)

                PyImGui.set_window_size(1, 1, PyImGui.ImGuiCond.Always)
    
                state = TextureState.Normal

                if ImGui.is_mouse_in_rect(self.__close_button_rect): 
                    if PyImGui.is_mouse_down(0):         
                        state = TextureState.Active
                    else:
                        state = TextureState.Hovered

                PyImGui.push_clip_rect(self.__decorators_left, self.__decorators_top + 5, self.__decorators_width, self.__decorators_height , False)
                ThemeTextures.Empty_Pixel.value.draw_in_drawlist(
                    x=self.__decorators_left + 15,
                    y=self.__decorators_top,
                    size=(self.__decorators_width - 30, 14),
                    tint=(0,0,0,215)
                )
                
                # PyImGui.push_clip_rect(self.__decorators_left, self.__decorators_top, self.__decorators_width - 15, self.__decorators_height + 30, False)   
                ThemeTextures.Window_Frame_Bottom_No_Resize.value.get_texture().draw_in_drawlist(
                    x=self.__decorators_left + 2,
                    y=self.__decorators_top - 12 + 8,
                    size=(self.__decorators_width - 5 , 40)
                )

                PyImGui.push_clip_rect(self.__decorators_left, self.__decorators_top, self.__decorators_width, self.__decorators_height + 30, False)

                if has_title_bar:
                    ThemeTextures.Title_Bar.value.get_texture().draw_in_drawlist(
                        x=self.__decorators_left + 5,
                        y=self.__decorators_top,
                        size=(self.__decorators_width - 10, 26)
                    )

                    if self.can_close:
                        ThemeTextures.Empty_Pixel.value.draw_in_drawlist(
                            x=self.__close_button_rect[0] - 1,
                            y=self.__close_button_rect[1] - 1,
                            size=(self.__close_button_rect[2] + 2, self.__close_button_rect[3] + 2),
                            tint=(0,0,0,255)
                        )

                        ThemeTextures.Close_Button.value.get_texture().draw_in_drawlist(
                            x=self.__close_button_rect[0],
                            y=self.__close_button_rect[1],
                            size=(self.__close_button_rect[2:]),
                            state=state
                        )

                    self.__title_bar_rect = (self.__decorators_left + 10, self.__decorators_top + 2, self.__decorators_width - 10, 26)
                 
                    PyImGui.push_clip_rect(
                        self.__title_bar_rect[0] + 15,
                        self.__title_bar_rect[1] + 7,
                        self.__title_bar_rect[2] - 15 - 29,
                        self.__title_bar_rect[3] - 7,
                        False
                    )
                    PyImGui.draw_list_add_text(self.__title_bar_rect[0] + 15, self.__title_bar_rect[1] + 7, Utils.RGBToColor(255,255,255,255), self.window_display_name)
                    PyImGui.pop_clip_rect()

                    self.__draw_title_bar_fake(self.__title_bar_rect)
                else:
                    ThemeTextures.Window_Frame_Top_NoTitleBar.value.get_texture().draw_in_drawlist(
                        x=self.__decorators_left + 5,
                        y=self.__decorators_top + 11,
                        size=(self.__decorators_width - 10, 50)
                    )

            PyImGui.pop_clip_rect()
            
        def __draw_title_bar_fake(self, __title_bar_rect):  
            from .ImGuisrc import ImGui          
            can_interact = (int(self.window_flags) & int(PyImGui.WindowFlags.NoMouseInputs)) == 0
            
            PyImGui.set_next_window_pos(__title_bar_rect[0], __title_bar_rect[1])
            PyImGui.set_next_window_size(__title_bar_rect[2], __title_bar_rect[3])

            flags = (
                    PyImGui.WindowFlags.NoCollapse |
                    PyImGui.WindowFlags.NoTitleBar |
                    PyImGui.WindowFlags.NoScrollbar |
                    PyImGui.WindowFlags.NoScrollWithMouse |
                    PyImGui.WindowFlags.AlwaysAutoResize 
                    | PyImGui.WindowFlags.NoBackground
                )
            PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, -1, -0)
            ImGui.push_style_color(PyImGui.ImGuiCol.WindowBg, (0, 1, 0, 0.0))  # Fully transparent
            PyImGui.begin(f"{self.window_name}##titlebar_fake", flags)
            PyImGui.invisible_button("##titlebar_dragging_area_1", __title_bar_rect[2] - (30 if self.can_close else 0), __title_bar_rect[3])
            self.__dragging = (PyImGui.is_item_active() or self.__dragging) and can_interact
                        
            if PyImGui.is_item_focused():
                self.__set_focus = True
                
            PyImGui.set_cursor_screen_pos(self.__close_button_rect[0] + self.__close_button_rect[2], self.__close_button_rect[1] + self.__close_button_rect[3])
            PyImGui.invisible_button("##titlebar_dragging_area_2", 15, __title_bar_rect[3])
            self.__dragging = (PyImGui.is_item_active() or self.__dragging) and can_interact
                    
            if PyImGui.is_item_focused():
                self.__set_focus = True
                
            # Handle Double Click to Expand/Collapse
            if PyImGui.is_mouse_double_clicked(0) and self.__set_focus:
                can_collapse = (int(self.window_flags) & int(PyImGui.WindowFlags.NoCollapse)) == 0                
                if can_collapse and can_interact:
                    self.collapse = not self.collapse

                    if not self.collapse:
                        self.__resize = True

            if self.can_close:
                PyImGui.set_cursor_screen_pos(self.__close_button_rect[0], self.__close_button_rect[1])
                if PyImGui.invisible_button(f"##Close", self.__close_button_rect[2] + 1, self.__close_button_rect[3] + 1) and can_interact:
                    self.open = False
                    self.__set_focus = False
                    
                    
            PyImGui.end()
            ImGui.pop_style_color(1)
            PyImGui.pop_style_var(1)
                                
            # Handle dragging
            if self.__dragging:   
                can_drag = (int(self.window_flags) & int(PyImGui.WindowFlags.NoMove)) == 0
        
                if can_drag:
                    if self.__drag_started:                    
                        delta = PyImGui.get_mouse_drag_delta(0, 0.0)
                        new_window_pos = (__title_bar_rect[0] + 5 + delta[0], __title_bar_rect[1] + __title_bar_rect[3] - 2 + delta[1])
                        PyImGui.reset_mouse_drag_delta(0)
                        PyImGui.set_window_pos(new_window_pos[0], new_window_pos[1], PyImGui.ImGuiCond.Always)
                    else:
                        self.__drag_started = True
                else:
                    self.__dragging = False
                    self.__drag_started = False
         