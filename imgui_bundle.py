from Py4GWCoreLib import *
import ctypes
import glfw
from imgui_bundle import imgui
from imgui_bundle.python_backends.glfw_backend import GlfwRenderer
from OpenGL import GL as gl

# Constants
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
# SWP flags to move window without affecting Z-order or Focus
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

class OverlayApp:
    def __init__(self):
        self.initialized = False
        self.window = None
        self.renderer = None
        self.overlay_hwnd = None
        self.is_interactive = False

    def set_interaction(self, enable: bool):
        if not self.overlay_hwnd:
            return
        
        # Get current flags
        style = ctypes.windll.user32.GetWindowLongW(self.overlay_hwnd, GWL_EXSTYLE)
        
        if enable:
            # REMOVE Transparent flag to allow clicks
            new_style = style & ~WS_EX_TRANSPARENT
        else:
            # ADD Transparent flag to pass clicks through to game
            new_style = style | WS_EX_TRANSPARENT
            
        if style != new_style:
            ctypes.windll.user32.SetWindowLongW(self.overlay_hwnd, GWL_EXSTYLE, new_style)
            self.is_interactive = enable

    def startup(self, x, y, w, h):
        if not glfw.init():
            return

        glfw.window_hint(glfw.FLOATING, True)
        glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, True)
        glfw.window_hint(glfw.DECORATED, False)
        glfw.window_hint(glfw.FOCUS_ON_SHOW, False)

        self.window = glfw.create_window(w, h, "Py4GW_Overlay", None, None)
        if not self.window:
            return

        glfw.set_window_pos(self.window, x, y)
        glfw.make_context_current(self.window)
        glfw.swap_interval(0) # Disable vsync for embedded frames

        self.overlay_hwnd = glfw.get_win32_window(self.window)
        
        # Set Owner to Game HWND
        game_hwnd = Py4GW.Console.get_gw_window_handle()
        ctypes.windll.user32.SetWindowLongW(self.overlay_hwnd, -8, game_hwnd) 

        # Initial State: Layered + Transparent (Click-through)
        style = ctypes.windll.user32.GetWindowLongW(self.overlay_hwnd, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(self.overlay_hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)

        imgui.create_context()
        self.renderer = GlfwRenderer(self.window)
        self.initialized = True

    def shutdown(self):
        """Call this to properly remove the window from the screen."""
        if self.initialized:
            if self.window:
                glfw.destroy_window(self.window)
            glfw.terminate()
            self.initialized = False

app = OverlayApp()

def main():
    # If the script is being signaled to stop by your environment, 
    # we MUST call app.shutdown(). 
    # Check if Py4GW is still 'running' or if the user pressed a 'stop' key.
    
    try:
        x, y, w, h = Py4GW.Console.get_window_rect()
    except:
        app.shutdown()
        return 

    if not app.initialized:
        app.startup(x, y, w, h)

    if glfw.window_should_close(app.window):
        app.shutdown()
        return

    # Sync position using SetWindowPos (faster and supports NOACTIVATE)
    ctypes.windll.user32.SetWindowPos(app.overlay_hwnd, 0, x, y, w, h, SWP_NOACTIVATE | SWP_SHOWWINDOW)
    
    glfw.poll_events()
    
    app.renderer.process_inputs()

    # Determine if ImGui needs the mouse
    io = imgui.get_io()
    # Logic: If mouse is over a window, enable interaction. Otherwise, click-through.
    needs_input = io.want_capture_mouse or io.want_capture_keyboard
    app.set_interaction(needs_input)

    imgui.new_frame()
    
    # Simple UI for testing
    imgui.set_next_window_size((300, 150), imgui.Cond_.first_use_ever)
    if imgui.begin("Overlay Control"):
        imgui.text(f"Mouse Over UI: {io.want_capture_mouse}")
        imgui.text(f"Interactive: {app.is_interactive}")
        imgui.text(f"mouse_pos: {io.mouse_pos.x}, {io.mouse_pos.y}")
        if imgui.button("Close Overlay"):
             app.shutdown()
    imgui.end()

    imgui.render()
    
    gl.glClearColor(0, 0, 0, 0)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)
    
    app.renderer.render(imgui.get_draw_data())
    glfw.swap_buffers(app.window)

# In some embedded envs, the script ending doesn't trigger a delete.
# Ensure cleanup if the script is terminated.
import atexit
atexit.register(app.shutdown)

if __name__ == "__main__":
    main()