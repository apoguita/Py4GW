from Py4GWCoreLib import UIManager, EnumPreference, FrameLimiter, ThrottledTimer
import PyImGui

update_timer = ThrottledTimer(1000)  # 1 second timer

def configure():
    PyImGui.begin("Frame Limiter Configurator")
    PyImGui.text("This tool ensures the frame limiter is set to 60 FPS or lower.")
    PyImGui.text("If the frame limiter is set above 60 FPS, it will be automatically adjusted.")
    PyImGui.text("This is necessary to maintain compatibility with certain features.")
    PyImGui.end()


def main():
    global update_timer
    
    if update_timer.IsExpired():
        update_timer.Reset()
        frame_limit = UIManager.GetEnumPreference(EnumPreference.FrameLimiter.value)
        if frame_limit > FrameLimiter._60.value:
            UIManager.SetEnumPreference(EnumPreference.FrameLimiter, FrameLimiter._60.value)
        


if __name__ == "__main__":
    main()
