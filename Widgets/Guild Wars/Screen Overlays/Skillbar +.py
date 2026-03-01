from Py4GWCoreLib import *
import ctypes
import PyImGui

MODULE_NAME = "Skillbar +"
MODULE_ICON = "Textures/Module_Icons/SkillBar+.png"

user32 = ctypes.WinDLL("user32", use_last_error=True)
window_module = ImGui.WindowModule('Skillbar+', window_name = 'Skillbar+', window_flags = PyImGui.WindowFlags.AlwaysAutoResize)

class SkillBarPlus:
    ini = IniHandler(os.path.join(Py4GW.Console.get_projects_path(), "Widgets/Config/Skillbar +.ini"))
    
    class SkillsPlus:
        overlay         = PyOverlay.Overlay()
        coords          = []
        font_size       = 40
        draw_bg         = True
        bg_default      = Utils.RGBToColor(0, 255, 0, 50)
        bg_near         = Utils.RGBToColor(255, 0, 0, 150)
        near_threshold  = 5
        draw_duration   = True
        duration_font   = 16
        duration_bg     = Utils.RGBToColor(0, 0, 0, 255)
        duration_bar    = Utils.RGBToColor(100, 100, 100, 255)
        duration_offset = 0
        duration_bar_height = 20
        skill_height = 100

        def Clear(self):
            self.coords = []

        def GetSkillFrames(self):
            for i in range(8):
                frame_id = UIManager.GetChildFrameID(641635682, [i])
                if not UIManager.FrameExists(frame_id): 
                    continue
                coords = UIManager.GetFrameCoords(frame_id)
                self.coords.append(coords)

            if len(self.coords) < 8:
                self.coords = []

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
            
        def DrawDurationBar(self, id, coords, duration, remaining):
            ImGui.push_font("Regular", self.duration_font)

            percentage = remaining/duration
            remaining = math.floor(remaining) if remaining > 1 else round(remaining,1)
                
            text_width, text_height = PyImGui.calc_text_size(str(remaining))

            left, top, right, bottom = coords
            self.skill_height = bottom - top
            top += self.duration_offset
            bottom = top + int(text_height*.75 + 4)
            self.duration_bar_height = bottom - top
            self.overlay.DrawQuadFilled(PyOverlay.Point2D(left,top),
                                        PyOverlay.Point2D(right,top),
                                        PyOverlay.Point2D(right,bottom + 2),
                                        PyOverlay.Point2D(left,bottom + 2),
                                        self.duration_bg)
            
            bar_length = int(((right - 1) - (left + 1))*percentage)
            self.overlay.DrawQuadFilled(PyOverlay.Point2D(left + 1,top + 1),
                                        PyOverlay.Point2D(left + bar_length,top + 1),
                                        PyOverlay.Point2D(left + bar_length,bottom + 1),
                                        PyOverlay.Point2D(left + 1,bottom + 1),
                                        self.duration_bar)
            
            width = right - left
            height = bottom - top
            text_width = text_width + 4
            text_height = text_height*.75 + 4

            self.DrawText(id, str(remaining), left + (width - text_width)/2, 3 + top + (height - text_height)/2, text_width, text_height)

            ImGui.pop_font()

        def Draw(self):
            self.overlay.BeginDraw()

            if not self.coords: return

            for i in range(8):
                if self.draw_bg or self.draw_duration:
                    skill_id = GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(i+1)
                    duration = 0
                    remaining = 0
                    for effect in GLOBAL_CACHE.Effects.GetEffects(Player.GetAgentID()):
                        if effect.skill_id == skill_id:
                            duration = effect.duration
                            remaining = effect.time_remaining/1000
                            break

                    if remaining and remaining < 50000:
                        if self.draw_bg:
                            color = self.bg_near
                            if remaining > self.near_threshold + 1:
                                color = self.bg_default
                            elif remaining > self.near_threshold:
                                bg_color = tuple(int(c * 255) for c in Utils.ColorToTuple(self.bg_default))
                                near_color = tuple(int(c * 255) for c in Utils.ColorToTuple(self.bg_near))
                                amount = 1 - (remaining - self.near_threshold)
                                color = Color(*bg_color).shift(Color(*near_color), amount).to_color()


                            self.DrawBackground(self.coords[i], color)

                        if self.draw_duration:
                            self.DrawDurationBar(f'duration{i}', self.coords[i], duration, remaining)

                recharge = GLOBAL_CACHE.SkillBar.GetSkillData(i+1).get_recharge/1000
                recharge = math.floor(recharge) if recharge > 1 else round(recharge,1)
                if 1000 > recharge > 0:
                    left, top, right, bottom = self.coords[i]

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
                    self.bg_default = Utils.TupleToColor(PyImGui.color_edit4('Under Skill Effect', Utils.ColorToTuple(self.bg_default)))
                    self.bg_near = Utils.TupleToColor(PyImGui.color_edit4('Skill Effect Nearly Expired', Utils.ColorToTuple(self.bg_near)))
                    self.near_threshold = PyImGui.input_int('Nearly Expired Threshold (s)', self.near_threshold)

                self.draw_duration = PyImGui.checkbox('Draw Effect Durations on Skillbar', self.draw_duration)
                if self.draw_duration:
                    self.duration_font   = PyImGui.slider_int('Font Size##EffectDuration',  self.duration_font,  4, 30)
                    self.duration_bg     = Utils.TupleToColor(PyImGui.color_edit4('Duration Bar Background', Utils.ColorToTuple(self.duration_bg)))
                    self.duration_bar    = Utils.TupleToColor(PyImGui.color_edit4('Duration Bar Foreground', Utils.ColorToTuple(self.duration_bar)))
                    self.duration_offset = PyImGui.slider_int('Duration Bar Y Offset',  self.duration_offset,  -self.duration_bar_height - 1, self.skill_height)

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

        def Draw(self):
            active = []

            for effect in GLOBAL_CACHE.Effects.GetEffects(Player.GetAgentID()):
                frame_id = UIManager.GetChildFrameID(1726357791, [effect.skill_id + 4])
                if not UIManager.FrameExists(frame_id): 
                    continue

                time_remaining = effect.time_remaining/1000
                if time_remaining > 30*60:
                    continue
                time_remaining = math.floor(time_remaining) if time_remaining > 1 else round(time_remaining,1)

                active.append((effect.skill_id, frame_id, time_remaining))

            unique_ids = set([act[0] for act in active])

            for skill_id in unique_ids:
                filtered = [act for act in active if act[0] == skill_id]
                newest = max(filtered, key=lambda act: act[2])
                effect, frame_id, time_remaining = newest

                _, _, right, bottom = UIManager.GetFrameCoords(frame_id)

                ImGui.push_font("Regular", self.font_size)
                time_remaining = str(time_remaining)
                text_width, text_height = PyImGui.calc_text_size(time_remaining)
                text_width = text_width + 4
                text_height = text_height*.75 + 4

                self.DrawText(f'effect{skill_id}', time_remaining, right - text_width, bottom - text_height, text_width, text_height)

                ImGui.pop_font()

        def Config(self):
            if PyImGui.collapsing_header(f'Effects'):
                self.font_size = PyImGui.slider_int('Font Size##Effects',  self.font_size,  5, 50)
                self.bg_color = Utils.TupleToColor(PyImGui.color_edit4('Background', Utils.ColorToTuple(self.bg_color)))

    class AutoCast:
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
                    player_id = Player.GetAgentID()
                    skill_id = GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(i + 1)
                    if (Routines.Checks.Skills.HasEnoughEnergy(player_id, skill_id)     and 
                        Routines.Checks.Skills.HasEnoughAdrenaline(player_id, skill_id) and 
                        Routines.Checks.Skills.HasEnoughLife(player_id, skill_id)):
                        self.cast_timer.Reset()
                        GLOBAL_CACHE.SkillBar.UseSkill(i + 1)

        def Config(self):
            if PyImGui.collapsing_header(f'Auto Cast'):
                self.enable_click = PyImGui.checkbox('Enable alt + right click on a skillbar skill to toggle autocasting.', self.enable_click)

                icon_size = 36
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
        self.skills.font_size       = self.ini.read_int('skills', 'font', 40)
        self.skills.draw_bg         = self.ini.read_bool('skills', 'draw_bg', True)
        self.skills.bg_default      = self.ini.read_int('skills', 'color_default', Utils.RGBToColor(0, 255, 0, 50))
        self.skills.bg_near         = self.ini.read_int('skills', 'color_near', Utils.RGBToColor(255, 0, 0, 150))
        self.skills.near_threshold  = self.ini.read_int('skills', 'threshold',3)
        self.skills.draw_duration   = self.ini.read_bool('skills', 'draw_duration', False)
        self.skills.duration_font   = self.ini.read_int('skills', 'duration_font', 16)
        self.skills.duration_bg     = self.ini.read_int('skills', 'duration_bg', Utils.RGBToColor(0, 0, 0, 255))
        self.skills.duration_bar    = self.ini.read_int('skills', 'duration_bar', Utils.RGBToColor(100, 100, 100, 255))
        self.skills.duration_offset = self.ini.read_int('skills', 'duration_offset', 0)

        self.effects.font_size      = self.ini.read_int('effects', 'font', 20)
        self.effects.bg_color       = self.ini.read_int('effects', 'color', Utils.RGBToColor(0, 0, 0, 150))

        self.auto.enable_click      = self.ini.read_bool('auto', 'enable_click', False)

    def SaveConfig(self):
        self.ini.write_key('skills', 'font', str(self.skills.font_size))
        self.ini.write_key('skills', 'draw_bg', str(self.skills.draw_bg))
        self.ini.write_key('skills', 'color_default', str(self.skills.bg_default))
        self.ini.write_key('skills', 'color_near', str(self.skills.bg_near))
        self.ini.write_key('skills', 'threshold', str(self.skills.near_threshold))
        self.ini.write_key('skills', 'draw_duration', str(self.skills.draw_duration))
        self.ini.write_key('skills', 'duration_font', str(self.skills.duration_font))
        self.ini.write_key('skills', 'duration_bg', str(self.skills.duration_bg))
        self.ini.write_key('skills', 'duration_bar', str(self.skills.duration_bar))
        self.ini.write_key('skills', 'duration_offset', str(self.skills.duration_offset))

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

    if not Map.IsMapReady() or not Party.IsPartyLoaded() or Map.IsInCinematic(): return
    
    if window_module.first_run:
        x = sbp.ini.read_int('pos', 'x', 500)
        y = sbp.ini.read_int('pos', 'y', 300)
        PyImGui.set_next_window_pos(x, y)
        window_module.first_run = False

    pos = (-1, -1)
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

            pos = PyImGui.get_window_pos()
        PyImGui.end()

        if pos != (-1, -1):
            sbp.ini.write_key('pos', 'x', str(int(pos[0])))
            sbp.ini.write_key('pos', 'y', str(int(pos[1])))
        sbp.SaveConfig()

    except Exception as e:
        current_function = inspect.currentframe().f_code.co_name # type: ignore
        Py4GW.Console.Log('BOT', f'Error in {current_function}: {str(e)}', Py4GW.Console.MessageType.Error)
        raise
    
def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Skillbar +", title_color.to_tuple_normalized())
    ImGui.pop_font()
    
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()
    
    # Description
    PyImGui.text("Enhances the Guild Wars skillbar with additional features.")
    
    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()
    
    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Displays skill recharge timers directly on the skillbar.")
    PyImGui.bullet_text("Shows effect durations above the skillbar.")
    PyImGui.bullet_text("Auto-cast skills with customizable toggles.")
    
    PyImGui.spacing()
    PyImGui.separator()
    
    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by jtmele1")
    
    PyImGui.end_tooltip()

def main():
    global sbp
    try:
        if Map.IsMapLoading():
            sbp.skills.Clear()
            sbp.auto.slots = [False]*8

        if Map.IsMapReady() and Map.IsExplorable() and Party.IsPartyLoaded() and not Map.IsInCinematic() and not UIManager.IsWorldMapShowing():
            if not sbp.skills.coords:
                sbp.skills.GetSkillFrames()
            sbp.skills.Draw()
            sbp.effects.Draw()
            sbp.auto.Cast()

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