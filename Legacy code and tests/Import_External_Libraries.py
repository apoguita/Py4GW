from Py4GWCoreLib import *
import sys
import os
import ctypes
import subprocess

#*******************************************************************************
#*********  Start of manual import of external libraries  ***********************
#*******************************************************************************
# Automatically detect Python installation path

def find_system_python():
    """ Automatically detects the system Python installation path """
    try:
        python_path = subprocess.check_output("where python", shell=True).decode().split("\n")[0].strip()
        if python_path and os.path.exists(python_path):
            return os.path.dirname(python_path)
    except Exception:
        pass

    if sys.prefix and os.path.exists(sys.prefix):
        return sys.prefix

    return None

# Automatically detect Python installation path
system_python_path = find_system_python()

if not system_python_path:
    print("Error: Could not detect system Python!")
    sys.exit(1)

#print("Detected system Python path:", system_python_path)

# Define paths dynamically
site_packages_path = os.path.join(system_python_path, "Lib", "site-packages")
pywin32_system32 = os.path.join(site_packages_path, "pywin32_system32")
win32_path = os.path.join(site_packages_path, "win32")

# Ensure Py4GW has access to the right directories
if site_packages_path not in sys.path:
    sys.path.append(site_packages_path)

if win32_path not in sys.path:
    sys.path.append(win32_path)

if pywin32_system32 not in sys.path:
    sys.path.append(pywin32_system32)

# Manually load `pywintypes` DLL (skipping import)
try:
    ctypes.windll.LoadLibrary(os.path.join(pywin32_system32, "pywintypes313.dll"))
    ctypes.windll.LoadLibrary(os.path.join(pywin32_system32, "pythoncom313.dll"))
    print("Successfully loaded pywintypes DLL manually!")
except Exception as e:
    print(f"Failed to load pywintypes DLL: {e}")

# Now try importing `win32pipe`
try:
    import win32pipe
    import win32file
    print("win32pipe successfully imported!")
except ModuleNotFoundError as e:
    print(f"win32pipe import failed: {e}")
    
#*******************************************************************************
#*********  End of manual import of external libraries  ***********************
#*******************************************************************************

MODULE_NAME = "tester for everything"

def DrawWindow():
    """ImGui draw function that runs every frame."""
    try:
        flags = PyImGui.WindowFlags.NoScrollbar | PyImGui.WindowFlags.NoScrollWithMouse | PyImGui.WindowFlags.AlwaysAutoResize
        if PyImGui.begin("Py4GW", flags):

            if PyImGui.button("print debug"):
                print("sys.path:", sys.path)  
                print("PYTHONPATH:", os.environ.get("PYTHONPATH"))  
                print("PATH:", os.environ.get("PATH"))  
        PyImGui.end()

    except Exception as e:
        Py4GW.Console.Log("tester", f"Unexpected Error: {str(e)}", Py4GW.Console.MessageType.Error)

def main():
    """Runs every frame."""
    DrawWindow()

if __name__ == "__main__":
    main()
