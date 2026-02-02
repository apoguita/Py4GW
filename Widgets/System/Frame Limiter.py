from Py4GWCoreLib import Routines, EnumPreference, FrameLimiter, ThrottledTimer, UIManager, Color, ColorPalette, ImGui
import PyImGui

update_timer = ThrottledTimer(1000)  # 1 second timer
OPTIONAL = False

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Frame Limiter", title_color.to_tuple_normalized())
    ImGui.pop_font()
    red = ColorPalette.GetColor("red")
    PyImGui.text_colored("This is a system Widget, deactivating it will cause issues.", red.to_tuple_normalized())
    PyImGui.separator()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.text("Ensures frame limiter is set to 60 FPS or lower")
    PyImGui.text("Automatically adjusts frame limiter if set above 60 FPS")
    PyImGui.text("Maintains compatibility with certain features")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")

    PyImGui.end_tooltip()


def main():
    global update_timer
    if not Routines.Checks.Map.MapValid():
        return
    
    if update_timer.IsExpired():
        update_timer.Reset()
        frame_limit = UIManager.GetEnumPreference(EnumPreference.FrameLimiter.value)
        if FrameLimiter._None.value < frame_limit > FrameLimiter._60.value:
            UIManager.SetEnumPreference(EnumPreference.FrameLimiter, FrameLimiter._60.value)

if __name__ == "__main__":
    main()
