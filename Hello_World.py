from Py4GWCoreLib import *
import time
import sys
import os
import ctypes
import subprocess

#*******************************************************************************
#********* Start of manual import of external libraries  ***********************
#*******************************************************************************
def find_system_python():
    try:
        python_path = subprocess.check_output("where python", shell=True).decode().split("\n")[0].strip()
        if python_path and os.path.exists(python_path):
            return os.path.dirname(python_path)
    except Exception:
        pass
    return sys.prefix if sys.prefix and os.path.exists(sys.prefix) else None

system_python_path = find_system_python()
if system_python_path:
    site_packages_path = os.path.join(system_python_path, "Lib", "site-packages")
    if site_packages_path not in sys.path:
        sys.path.append(site_packages_path)
    os.environ["PATH"] = site_packages_path + os.pathsep + os.environ["PATH"]

import glfw
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer
#*******************************************************************************
#********* End of manual import of external libraries  ***********************
#*******************************************************************************

class OverlayApp:
    def __init__(self):
        self.initialized = False
        self.window = None
        self.renderer = None
        self.overlay_hwnd = None

    def startup(self, x, y, w, h):
        glfw.init()
        glfw.window_hint(glfw.FLOATING, True)
        glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, True)
        glfw.window_hint(glfw.DECORATED, False)

        # Initialize the window at the current game dimensions
        self.window = glfw.create_window(w, h, "Overlay", None, None)
        glfw.set_window_pos(self.window, x, y)
        glfw.make_context_current(self.window)

        # 1. Get Overlay HWND
        self.overlay_hwnd = glfw.get_win32_window(self.window)
        
        # 2. Use Game HWND to "Anchor" the overlay
        # This makes the game the owner, so the overlay stays on top of it.
        game_hwnd = Py4GW.Console.get_gw_window_handle()
        ctypes.windll.user32.SetWindowLongW(self.overlay_hwnd, -8, game_hwnd) # -8 is GWL_HWNDPARENT (Owner)

        # 3. Make Click-Through
        style = ctypes.windll.user32.GetWindowLongW(self.overlay_hwnd, -20)
        ctypes.windll.user32.SetWindowLongW(self.overlay_hwnd, -20, style | 0x80000 | 0x20)

        imgui.create_context()
        self.renderer = GlfwRenderer(self.window)
        self.initialized = True

app = OverlayApp()

def main():
    # 1. Get Game Data from Py4GW
    try:
        # These are the coordinates for the game's actual rendering area
        x, y, w, h = Py4GW.Console.get_client_rect()
    except:
        return 

    # 2. Startup/Initialization
    if not app.initialized:
        app.startup(x, y, w, h)

    if glfw.window_should_close(app.window):
        return

    # 3. Sync Overlay to Game Window
    # This keeps the overlay window perfectly mapped to the game's client area
    ctypes.windll.user32.MoveWindow(app.overlay_hwnd, x, y, w, h, True)
    
    # 4. ONE SINGLE TICK
    glfw.poll_events()
    if not app.renderer:
        return
    app.renderer.process_inputs()
    
    imgui.new_frame()
    
    # User Drawing Code
    if imgui.begin("External Overlay"):
        imgui.text(f"Synced to Game HWND: {Py4GW.Console.get_gw_window_handle()}")
        imgui.text(f"Position: {x}, {y} | Size: {w}x{h}")
    imgui.end()

    imgui.render()
    
    from OpenGL import GL as gl
    gl.glClearColor(0, 0, 0, 0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    
    app.renderer.render(imgui.get_draw_data())
    glfw.swap_buffers(app.window)

if __name__ == "__main__":
    main()