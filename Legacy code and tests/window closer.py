from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"
window_open = True
visible = True

def main():
    global window_open, visible
    
    if window_open:
        visible, window_open = PyImGui.begin_with_close(f"close window tester", window_open, PyImGui.WindowFlags.NoFlag)

        if visible:
            PyImGui.text("This is a test window with a close button")
            PyImGui.text(f"Window open: {window_open}")
            PyImGui.text(f"Window visible: {visible}")
            PyImGui.end()
        else:
            PyImGui.end()

if __name__ == "__main__":
    main()
