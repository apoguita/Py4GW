
import time
import sys
import os
import ctypes
import subprocess

class ModuleImporter:
    # *******************************************************************************
    # *********  Start of manual import of external libraries  ***********************
    # *******************************************************************************
    # Automatically detect Python installation path

    @staticmethod
    def find_system_python():
        """ Automatically detects the system Python installation path """
        try:
            python_path = subprocess.check_output(
                "where python", shell=True).decode().split("\n")[0].strip()
            if python_path and os.path.exists(python_path):
                return os.path.dirname(python_path)
        except Exception:
            pass

        if sys.prefix and os.path.exists(sys.prefix):
            return sys.prefix

        return None

    @staticmethod
    def prepare_module_import():
        # Automatically detect Python installation path
        system_python_path = ModuleImporter.find_system_python()

        if not system_python_path:
            print("Error: Could not detect system Python!")
            return sys.exit(1)

        # print("Detected system Python path:", system_python_path)

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
            ctypes.windll.LoadLibrary(os.path.join(
                pywin32_system32, "pywintypes313.dll"))
            ctypes.windll.LoadLibrary(os.path.join(
                pywin32_system32, "pythoncom313.dll"))
            return True
        
        except Exception as e:
            # print(f"Failed to load pywintypes DLL: {e}")
            return False
