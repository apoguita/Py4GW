from Py4GWCoreLib import *
import ctypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
window_module = ImGui.WindowModule('Skillbar+', window_name = 'Skillbar+', window_pos = (1200, 400), window_flags = PyImGui.WindowFlags.AlwaysAutoResize)

class SkillBarPlus:
    ini = IniHandler(os.path.join(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")), "Widgets/Config/Skillbar +.ini"))
    
    class SkillsPlus:
        overlay        = PyOverlay.Overlay()
        coords         = []
        font_size      = 40
        draw_bg        = True
        bg_default     = Utils.RGBToColor(0, 0, 0, 150)
        bg_near        = Utils.RGBToColor(0, 255, 0, 50)
        near_threshold = 3

        def Clear(self):
            self.coords = []

        def GetCoords(self):
            for i in range(8):
                frame_id = UIManager.GetFrameIDByCustomLabel(frame_label = f'Skillbar.Skill{i + 1}')
                coords = UIManager.GetFrameCoords(frame_id)
                while coords[0] == 0:
                    frame_id = UIManager.GetFrameIDByCustomLabel(frame_label = f'Skillbar.Skill{i + 1}')
                    coords = UIManager.GetFrameCoords(frame_id)
                self.coords.append(coords)

        def DrawText(self, caption, text, x, y, w, h):
            PyImGui.set_next_window_pos(x, y)
            PyImGui.set_next_window_size(w, h)
            
            flags=(PyImGui.WindowFlags.NoCollapse        | 
                   PyImGui.WindowFlags.NoTitleBar        |
                   PyImGui.WindowFlags.NoScrollbar       |
                   PyImGui.WindowFlags.NoScrollWithMouse |
                   PyImGui.WindowFlags.NoBackground      |
                   PyImGui.WindowFlags.NoMouseInputs     |
                   PyImGui.WindowFlags.AlwaysAutoResize) 
            
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding, 0)
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowBorderSize, 0)
            PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 0, 0)
            
            if PyImGui.begin(caption, flags):
                PyImGui.text(text)
            PyImGui.end()

            PyImGui.pop_style_var(3)

        def DrawBackground(self, coords, color):
            left, top, right, bottom = coords
            self.overlay.DrawQuadFilled(PyOverlay.Point2D(left,top),
                                        PyOverlay.Point2D(right,top),
                                        PyOverlay.Point2D(right,bottom),
                                        PyOverlay.Point2D(left,bottom),
                                        color)

        def Draw(self):
            self.overlay.BeginDraw()

            for i in range(8):
                recharge = GLOBAL_CACHE.SkillBar.GetSkillData(i+1).get_recharge/1000
                recharge = math.floor(recharge) if recharge > 1 else round(recharge,1)
                if 1000 > recharge > 0:
                    left, top, right, bottom = self.coords[i]

                    if self.draw_bg:
                        color = self.bg_default if recharge > (self.near_threshold - 1) else self.bg_near
                        self.DrawBackground(self.coords[i], color)

                    width = right - left
                    height = bottom - top

                    ImGui.push_font("Regular", self.font_size)
                    
                    text_width, text_height = PyImGui.calc_text_size(str(recharge))
                    text_width = text_width
                    text_height = text_height*.75

                    self.DrawText(f'skill{i}', str(recharge), left + (width - text_width)/2, top + (height - text_height)/2, text_width, text_height)

                    ImGui.pop_font()

            self.overlay.EndDraw()

        def Config(self):
            if PyImGui.collapsing_header(f'Skillbar'):
                self.font_size = PyImGui.slider_int('Font Size##Skillbar',  self.font_size,  10, 100)
                self.draw_bg = PyImGui.checkbox('Draw Background Colors', self.draw_bg)
                if self.draw_bg:
                    self.bg_default = Utils.TupleToColor(PyImGui.color_edit4('Default', Utils.ColorToTuple(self.bg_default)))
                    self.bg_near = Utils.TupleToColor(PyImGui.color_edit4('Nearly Recharged', Utils.ColorToTuple(self.bg_near)))
                    self.near_threshold = PyImGui.input_int('Almost Recharged Threshold (s)', self.near_threshold)

    class EffectsPlus:
        font_size = 20
        bg_color  = Utils.RGBToColor(0, 0, 0, 150)

        def DrawText(self, caption, text, x, y, w, h):
            PyImGui.set_next_window_pos(x, y)
            PyImGui.set_next_window_size(w, h)
            
            flags=(PyImGui.WindowFlags.NoCollapse        | 
                   PyImGui.WindowFlags.NoTitleBar        |
                   PyImGui.WindowFlags.NoScrollbar       |
                   PyImGui.WindowFlags.NoScrollWithMouse |
                   PyImGui.WindowFlags.AlwaysAutoResize) 
            
            PyImGui.push_style_color(PyImGui.ImGuiCol.WindowBg, Utils.ColorToTuple(self.bg_color))
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowRounding, 0)
            PyImGui.push_style_var(ImGui.ImGuiStyleVar.WindowBorderSize, 0)
            PyImGui.push_style_var2(ImGui.ImGuiStyleVar.WindowPadding, 2, 2)
            
            if PyImGui.begin(caption, flags):
                PyImGui.text(text)
            PyImGui.end()

            PyImGui.pop_style_color(1)
            PyImGui.pop_style_var(3)
            
            return result

        def Draw(self):
            for effect in GLOBAL_CACHE.Effects.GetEffects(GLOBAL_CACHE.Player.GetAgentID()):
                frame_id = UIManager.GetChildFrameID(1726357791, [effect.skill_id + 4])
                frame_coords = UIManager.GetFrameCoords(frame_id)
                while frame_coords[0] == 0:
                    frame_coords = UIManager.GetFrameCoords(frame_id)

                time_remaining = effect.time_remaining
                if effect.time_remaining > 30*60*1000: continue
                time_remaining = str(round(time_remaining/1000))

                _, _, right, bottom = frame_coords

                ImGui.push_font("Regular", self.font_size)
                
                text_width, text_height = PyImGui.calc_text_size(time_remaining)
                text_width = text_width + 4
                text_height = text_height*.75 + 4

                self.DrawText(f'effect{effect.skill_id}', time_remaining, right - text_width, bottom - text_height, text_width, text_height)

                ImGui.pop_font()

        def Config(self):
            if PyImGui.collapsing_header(f'Effects'):
                self.font_size = PyImGui.slider_int('Font Size##Effects',  self.font_size,  5, 50)
                self.bg_color = Utils.TupleToColor(PyImGui.color_edit4('Background', Utils.ColorToTuple(self.bg_color)))

    class AutoCast:
        action_queue = ActionQueueManager()
        enable_click = True
        slots = [False]*8
        cast_timer = Timer()
        cast_timer.Start()
        click_timer = Timer()
        click_timer.Start()

        def CanQueue(self, slot):
            return self.cast_timer.HasElapsed(150) and Routines.Checks.Skills.IsSkillSlotReady(slot) and Routines.Checks.Skills.CanCast()

        def Cast(self):
            for i in range(8):
                if self.slots[i] and self.CanQueue(i + 1):
                    self.cast_timer.Reset()
                    self.action_queue.AddAction('ACTION',SkillBar.UseSkill, i + 1)

        def Config(self):
            if PyImGui.collapsing_header(f'Auto Cast'):
                self.enable_click = PyImGui.checkbox('Enable alt + right click on a skillbar skill to toggle autocasting.', self.enable_click)

                icon_size = 48
                offset = icon_size + 24

                for i in range(8):
                    if not Map.IsMapReady(): return
                    if self.slots[i]:
                        PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        (0, 0.70, 0, 1))
                        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0, 0.85, 0, 1))
                        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  (0, 0.90, 0, 1))
                    else:
                        PyImGui.push_style_color(PyImGui.ImGuiCol.Button,        (0.2, 0.2, 0.2, 1))
                        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, (0.3, 0.3, 0.3, 1))
                        PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,  (0.4, 0.4, 0.4, 1))

                    texture_path = GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(SkillBar.GetSkillIDBySlot(i + 1))
                    if texture_path:
                        if ImGui.ImageButton(f'##slot_{i}', texture_path, icon_size, icon_size):
                            self.slots[i] = not self.slots[i]
                        PyImGui.same_line(offset,-1)
                        offset += icon_size + 14

                    PyImGui.pop_style_color(3)

    skills = SkillsPlus()
    effects = EffectsPlus()
    auto = AutoCast()

    def LoadConfig(self):
        self.skills.font_size      = self.ini.read_int('skills', 'font', 40)
        self.skills.draw_bg        = self.ini.read_bool('skills', 'draw_bg', True)
        self.skills.bg_default     = self.ini.read_int('skills', 'color_default', Utils.RGBToColor(0, 0, 0, 150))
        self.skills.bg_near        = self.ini.read_int('skills', 'color_near', Utils.RGBToColor(0, 255, 0, 50))
        self.skills.near_threshold = self.ini.read_int('skills', 'threshold',3)

        self.effects.font_size     = self.ini.read_int('effects', 'font', 20)
        self.effects.bg_color      = self.ini.read_int('effects', 'color', Utils.RGBToColor(0, 0, 0, 150))

        self.auto.enable_click   = self.ini.read_bool('auto', 'enable_click', True)

    def SaveConfig(self):
        self.ini.write_key('skills', 'font', str(self.skills.font_size))
        self.ini.write_key('skills', 'draw_bg', str(self.skills.draw_bg))
        self.ini.write_key('skills', 'color_default', str(self.skills.bg_default))
        self.ini.write_key('skills', 'color_near', str(self.skills.bg_near))
        self.ini.write_key('skills', 'threshold', str(self.skills.near_threshold))

        self.ini.write_key('effects', 'font', str(self.effects.font_size))
        self.ini.write_key('effects', 'color', str(self.effects.bg_color))

        self.ini.write_key('auto', 'enable_click', str(self.auto.enable_click))

    def DrawConfig(self):
        self.skills.Config()
        self.effects.Config()
        self.auto.Config()

sbp = SkillBarPlus()
sbp.LoadConfig()

def IsKeyPressed(vk_code):
    value = user32.GetAsyncKeyState(vk_code) & 0x8000
    is_value_not_zero = value != 0
    if is_value_not_zero:
        return True
    return False

def configure():
    global window_module, sbp

    if not Map.IsMapReady() or not Party.IsPartyLoaded(): return
    
    if window_module.first_run:    
        PyImGui.set_next_window_pos(window_module.window_pos[0], window_module.window_pos[1])
        window_module.first_run = False

    try:
        if PyImGui.begin(window_module.window_name, window_module.window_flags):
            PyImGui.push_style_color(PyImGui.ImGuiCol.Header,           (.2,.2,.2,1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderHovered,    (.3,.3,.3,1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.HeaderActive,     (.4,.4,.4,1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBg,          (0.2, 0.2, 0.2, 1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgHovered,   (0.3, 0.3, 0.3, 1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.FrameBgActive,    (0.4, 0.4, 0.4, 1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrab,       (0.0, 0.0, 0.0, 1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.SliderGrabActive, (0.0, 0.0, 0.0, 1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.Button,           (0.2, 0.2, 0.2, 1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered,    (0.3, 0.3, 0.3, 1))
            PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive,     (0.4, 0.4, 0.4, 1))

            sbp.DrawConfig()

            PyImGui.pop_style_color(11)
        PyImGui.end()

        sbp.SaveConfig()

    except Exception as e:
        current_function = inspect.currentframe().f_code.co_name # type: ignore
        Py4GW.Console.Log('BOT', f'Error in {current_function}: {str(e)}', Py4GW.Console.MessageType.Error)
        raise

def main():
    global sbp
    try:
        if Map.IsMapLoading():
            sbp.skills.Clear()
            sbp.auto.slots = [False]*8

        if Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and not UIManager.IsWorldMapShowing():
            if not sbp.skills.coords:
                sbp.skills.GetCoords()
            sbp.skills.Draw()
            sbp.effects.Draw()
            sbp.auto.Cast()
            sbp.auto.action_queue.ProcessAll()

            if PyImGui.get_io().key_alt and IsKeyPressed(2) and sbp.auto.enable_click and sbp.auto.click_timer.HasElapsed(200):
                skill_id = SkillBar.GetHoveredSkillID()
                if skill_id:
                    slot = SkillBar.GetSlotBySkillID(skill_id)
                    sbp.auto.slots[slot - 1] = not sbp.auto.slots[slot - 1]
                    sbp.auto.click_timer.Reset()

    except ImportError as e:
        Py4GW.Console.Log('Compass+', f'ImportError encountered: {str(e)}', Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log('Compass+', f'Stack trace: {traceback.format_exc()}', Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log('Compass+', f'ValueError encountered: {str(e)}', Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log('Compass+', f'Stack trace: {traceback.format_exc()}', Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log('Compass+', f'TypeError encountered: {str(e)}', Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log('Compass+', f'Stack trace: {traceback.format_exc()}', Py4GW.Console.MessageType.Error)
    except Exception as e:
        Py4GW.Console.Log('Compass+', f'Unexpected error encountered: {str(e)}', Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log('Compass+', f'Stack trace: {traceback.format_exc()}', Py4GW.Console.MessageType.Error)
    finally:
        pass

if __name__ == '__main__':
    main()