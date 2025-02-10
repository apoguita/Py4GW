
from Py4GWCoreLib import *

import ctypes
from ctypes import wintypes


# Constants and Structures
ULONG_PTR = ctypes.c_uint32
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
MAPVK_VK_TO_VSC = 0

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ULONG_PTR)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD),
                ("ki", KEYBDINPUT)]


def send_scan_code(virtual_key_code, is_key_up=False):
    # Map virtual key to scan code
    scan_code = ctypes.windll.user32.MapVirtualKeyW(virtual_key_code, MAPVK_VK_TO_VSC)

    # Configure the input structure
    input = INPUT()
    input.type = INPUT_KEYBOARD
    input.ki = KEYBDINPUT(wVk=0,  # Use scan code mode
                          wScan=scan_code,
                          dwFlags=KEYEVENTF_KEYUP if is_key_up else 0,
                          time=0,
                          dwExtraInfo=0)

    # Send the input
    ctypes.windll.user32.SendInput(1, ctypes.byref(input), ctypes.sizeof(input))


def attach_thread_to_game(window_handle):
    target_thread_id = ctypes.windll.user32.GetWindowThreadProcessId(window_handle, None)
    current_thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
    ctypes.windll.user32.AttachThreadInput(current_thread_id, target_thread_id, True)

def bring_window_to_foreground(window_handle):
    ctypes.windll.user32.SetForegroundWindow(window_handle)


def DrawWindow():
    client_window_handle = Py4GW.Console.get_gw_window_handle()  # Obtain the game window handle
    attach_thread_to_game(client_window_handle)  # Attach threads
    bring_window_to_foreground(client_window_handle)  # Ensure input focus

    if PyImGui.begin("Key Handler"):
        PyImGui.text("Simulate Key Press")
        
        # Simulate pressing and releasing the 'W' key
        if PyImGui.button("Press W Key"):
            send_scan_code(Key.W.value, is_key_up=False)
        
        if PyImGui.button("Release W Key"):
            send_scan_code(Key.W.value, is_key_up=True)

    PyImGui.end()


walk_timer = Timer()    
walk_timer.Start()
def main():
    global walk_timer
    if walk_timer.GetElapsedTime() < 1000:
        Keystroke.Press(Key.W.value)
    else:
        Keystroke.Release(Key.W.value)

    if walk_timer.GetElapsedTime() > 2000:
        walk_timer.Reset()

    DrawWindow()


if __name__ == "__main__":
    main()
