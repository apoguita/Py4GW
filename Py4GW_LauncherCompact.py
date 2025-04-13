from imgui_bundle import hello_imgui, imgui
import json
import tkinter as tk
from tkinter import filedialog


#region --- patcher ---
import ctypes
import ctypes.wintypes
from ctypes import wintypes
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
from typing import List, Optional

#region --- injector ---
import threading
import time
import win32gui
import win32process
import psutil
import sys
import configparser
import os

class IniHandler:
    def __init__(self, filename: str):
        """
        Initialize the handler with the given INI file.
        """
        self.filename = filename
        self.last_modified = 0
        self.config = configparser.ConfigParser()

    # ----------------------------
    # Core Methods
    # ----------------------------

    def reload(self) -> configparser.ConfigParser:
        """Reload the INI file only if it has changed."""
        current_mtime = os.path.getmtime(self.filename)
        if current_mtime != self.last_modified:
            self.last_modified = current_mtime
            self.config.read(self.filename)
        return self.config

    def save(self, config: configparser.ConfigParser) -> None:
        """
        Save changes to the INI file.
        """
        with open(self.filename, 'w') as configfile:
            config.write(configfile)

    # ----------------------------
    # Read Methods
    # ----------------------------

    def read_key(self, section: str, key: str, default_value: str = "") -> str:
        """
        Read a string value from the INI file.
        """
        config = self.reload()
        try:
            return config.get(section, key)
        except (configparser.NoOptionError, configparser.NoSectionError):
            return default_value

    def read_int(self, section: str, key: str, default_value: int = 0) -> int:
        """
        Read an integer value.
        """
        config = self.reload()
        try:
            return config.getint(section, key)
        except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
            return default_value

    def read_float(self, section: str, key: str, default_value: float = 0.0) -> float:
        """
        Read a float value.
        """
        config = self.reload()
        try:
            return config.getfloat(section, key)
        except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
            return default_value

    def read_bool(self, section: str, key: str, default_value: bool = False) -> bool:
        """
        Read a boolean value.
        """
        config = self.reload()
        try:
            return config.getboolean(section, key)
        except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
            return default_value

    # ----------------------------
    # Write Methods
    # ----------------------------

    def write_key(self, section: str, key: str, value: str) -> None:
        """
        Write or update a key-value pair.
        """
        config = self.reload()
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, key, str(value))
        self.save(config)

    # ----------------------------
    # Delete Methods
    # ----------------------------

    def delete_key(self, section: str, key: str) -> None:
        """
        Delete a specific key.
        """
        config = self.reload()
        if config.has_section(section) and config.has_option(section, key):
            config.remove_option(section, key)
            self.save(config)

    def delete_section(self, section: str) -> None:
        """
        Delete an entire section.
        """
        config = self.reload()
        if config.has_section(section):
            config.remove_section(section)
            self.save(config)


    # ----------------------------
    # Utility Methods
    # ----------------------------

    def list_sections(self) -> list:
        """
        List all sections in the INI file.
        """
        config = self.reload()
        return config.sections()

    def list_keys(self, section: str) -> dict:
        """
        List all keys and values in a section.
        """
        config = self.reload()
        if config.has_section(section):
            return dict(config.items(section))
        return {}

    def has_key(self, section: str, key: str) -> bool:
        """
        Check if a key exists in a section.
        """
        config = self.reload()
        return config.has_section(section) and config.has_option(section, key)

    def clone_section(self, source_section: str, target_section: str) -> None:
        """
        Clone all keys from one section to another.
        """
        config = self.reload()
        if config.has_section(source_section):
            if not config.has_section(target_section):
                config.add_section(target_section)
            for key, value in config.items(source_section):
                config.set(target_section, key, value)
            self.save(config)


current_directory = os.getcwd()
ini_file = "Py4GW.ini"
ini_handler = IniHandler(ini_file)
'''For Future Use'''
mods_directory = os.path.join(current_directory, "Addons", "mods")
os.makedirs(mods_directory, exist_ok=True)  # Create Addons/Mods if it doesn't exist

config_file = ini_handler.read_key("settings","account_config_file","accounts.json")
py4gw_dll_name = ini_handler.read_key("settings","py4gw_dll_name","Py4GW.dll")
blackbox_dll_name = ini_handler.read_key("settings","blackbox_dll_name","GWBlackBOX.dll")
gmod_dll_name = ini_handler.read_key("settings", "gmod_dll_name", "gMod.dll")

log_history = []
log_history.append("Welcome To Py4GW!")

APP_VERSION = "1.0.0"  # Update this with each release as needed

def check_and_handle_version_mismatch(ini_filename: str):
    """
    Check if the stored application version matches the current version.
    If there's a mismatch, clear the Hello ImGui settings file and update the stored version.
    Args:
        ini_filename: The path to the Hello ImGui settings file (e.g., Py4GW_Launcher.ini).
    """
    global ini_handler, log_history

    # Read the stored version from Py4GW.ini
    stored_version = ini_handler.read_key("Py4GW_Launcher", "APP_VERSION", "0.0.0")

    # Compare with the current version
    if stored_version != APP_VERSION:
        log_history.append(f"Version mismatch detected: Stored={stored_version}, Current={APP_VERSION}")
        
        # Clear the Hello ImGui settings file to reset layout settings
        if os.path.exists(ini_filename):
            try:
                os.remove(ini_filename)
                log_history.append(f"Cleared Hello ImGui settings: {ini_filename}")
            except Exception as e:
                log_history.append(f"Error clearing Hello ImGui settings: {str(e)}")
        else:
            log_history.append(f"No Hello ImGui settings file found at {ini_filename}")

        # Update the stored version in Py4GW.ini
        ini_handler.write_key("Py4GW_Launcher", "APP_VERSION", APP_VERSION)
        log_history.append(f"Updated stored version to {APP_VERSION}")
    else:
        log_history.append(f"Version check passed: {APP_VERSION}")

PROCESS_ALL_ACCESS = 0x1F0FFF
VIRTUAL_MEM = 0x1000 | 0x2000  # MEM_COMMIT | MEM_RESERVE
PAGE_READWRITE = 0x04
MEM_RELEASE = 0x8000

PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_QUERY_INFORMATION = 0x0400
MAX_PATH = 260  
TH32CS_SNAPPROCESS = 0x00000002

# Constants
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
HWND_TOP = 0
WM_SETTEXT = 0x000C

# Load libraries
#user32 = ctypes.WinDLL('user32', use_last_error=True)

# Define WNDENUMPROC correctly
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

# Function signatures for User32
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD

user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL

user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL

user32.SetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPCWSTR]
user32.SetWindowTextW.restype = wintypes.BOOL



class PROCESS_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [("Reserved1", ctypes.c_void_p),
                ("PebBaseAddress", ctypes.c_void_p),
                ("Reserved2", ctypes.c_void_p * 2),
                ("UniqueProcessId", ctypes.c_ulong),
                ("Reserved3", ctypes.c_void_p)]

class PEB(ctypes.Structure):
    _fields_ = [("InheritedAddressSpace", ctypes.c_ubyte),
                ("ReadImageFileExecOptions", ctypes.c_ubyte),
                ("BeingDebugged", ctypes.c_ubyte),
                ("BitField", ctypes.c_ubyte),
                ("Mutant", ctypes.c_void_p),
                ("ImageBaseAddress", ctypes.c_void_p)]

class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", ctypes.c_ulong),
                ("cntUsage", ctypes.c_ulong),
                ("th32ProcessID", ctypes.c_ulong),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", ctypes.c_ulong),
                ("cntThreads", ctypes.c_ulong),
                ("th32ParentProcessID", ctypes.c_ulong),
                ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", ctypes.c_ulong),
                ("szExeFile", ctypes.c_char * MAX_PATH)]

CREATE_SUSPENDED = 0x00000004

class STARTUPINFO(ctypes.Structure):
    _fields_ = [("cb", ctypes.c_ulong),
                ("lpReserved", ctypes.c_wchar_p),
                ("lpDesktop", ctypes.c_wchar_p),
                ("lpTitle", ctypes.c_wchar_p),
                ("dwX", ctypes.c_ulong),
                ("dwY", ctypes.c_ulong),
                ("dwXSize", ctypes.c_ulong),
                ("dwYSize", ctypes.c_ulong),
                ("dwXCountChars", ctypes.c_ulong),
                ("dwYCountChars", ctypes.c_ulong),
                ("dwFillAttribute", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("wShowWindow", ctypes.c_ushort),
                ("cbReserved2", ctypes.c_ushort),
                ("lpReserved2", ctypes.c_void_p), 
                ("hStdInput", ctypes.c_void_p),
                ("hStdOutput", ctypes.c_void_p),
                ("hStdError", ctypes.c_void_p)]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", ctypes.c_void_p),
                ("hThread", ctypes.c_void_p),
                ("dwProcessId", ctypes.c_ulong),
                ("dwThreadId", ctypes.c_ulong)]

kernel32 = ctypes.windll.kernel32
ntdll = ctypes.windll.ntdll

class Account:
    def __init__(self, character_name, email, password, gw_client_name, gw_path, extra_args, run_as_admin,
                 inject_py4gw, inject_blackbox, script_path="", enable_client_rename=False, use_character_name=False,
                 custom_client_name="", last_launch_time=None, total_runtime=0.0, current_session_time=0.0,
                 average_runtime=0.0, min_runtime=0.0, max_runtime=0.0, top_left=(0, 0), width=800, height=600,
                 preview_area=False, resize_client=False, inject_gmod=False, gmod_mods=None):
        self.character_name = character_name
        self.email = email
        self.password = password
        self.gw_client_name = gw_client_name
        self.gw_path = gw_path
        self.extra_args = extra_args
        self.run_as_admin = run_as_admin
        self.inject_py4gw = inject_py4gw
        self.inject_blackbox = inject_blackbox
        self.inject_gmod = inject_gmod          # New: Flag for gMod injection
        self.gmod_mods = gmod_mods if gmod_mods is not None else []  # New: List of mod file names
        self.script_path = script_path  # Path to the Python script
        self.enable_client_rename = enable_client_rename  # Whether client renaming is enabled
        self.use_character_name = use_character_name  # Whether to use the character name for renaming
        self.custom_client_name = custom_client_name  # Custom client name for renaming
        self.last_launch_time = last_launch_time  # Timestamp of the last launch
        self.total_runtime = total_runtime  # Total runtime in hours
        self.current_session_time = current_session_time  # Current session runtime in hours
        self.average_runtime = average_runtime  # Average runtime in hours
        self.min_runtime = min_runtime  # Minimum runtime recorded
        self.max_runtime = max_runtime  # Maximum runtime recorded
        self.top_left = top_left  # Top-left position of the window
        self.width = width  # Window width
        self.height = height  # Window height
        self.preview_area = preview_area  # Whether to preview the configured area
        self.resize_client = resize_client  # Whether to enable client resizing

    def to_dict(self):
        return {
            "character_name": self.character_name,
            "email": self.email,
            "password": self.password,
            "gw_client_name": self.gw_client_name,
            "gw_path": self.gw_path,
            "extra_args": self.extra_args,
            "run_as_admin": self.run_as_admin,
            "inject_py4gw": self.inject_py4gw,
            "inject_blackbox": self.inject_blackbox,
            "inject_gmod": self.inject_gmod,
            "gmod_mods": self.gmod_mods,
            "script_path": self.script_path,
            "enable_client_rename": self.enable_client_rename,
            "use_character_name": self.use_character_name,
            "custom_client_name": self.custom_client_name,
            "last_launch_time": self.last_launch_time,
            "total_runtime": self.total_runtime,
            "current_session_time": self.current_session_time,
            "average_runtime": self.average_runtime,
            "min_runtime": self.min_runtime,
            "max_runtime": self.max_runtime,
            "top_left": self.top_left,
            "width": self.width,
            "height": self.height,
            "preview_area": self.preview_area,
            "resize_client": self.resize_client,
        }

    @staticmethod
    def from_dict(data):
        return Account(
            character_name=data["character_name"],
            email=data["email"],
            password=data["password"],
            gw_client_name=data["gw_client_name"],
            gw_path=data["gw_path"],
            extra_args=data["extra_args"],
            run_as_admin=data["run_as_admin"],
            inject_py4gw=data["inject_py4gw"],
            inject_blackbox=data["inject_blackbox"],
            inject_gmod=data.get("inject_gmod", False),
            gmod_mods=data.get("gmod_mods", []),
            script_path=data.get("script_path", ""),  # Default to an empty string if not present
            enable_client_rename=data.get("enable_client_rename", False),
            use_character_name=data.get("use_character_name", False),
            custom_client_name=data.get("custom_client_name", ""),
            last_launch_time=data.get("last_launch_time", None),
            total_runtime=data.get("total_runtime", 0.0),
            current_session_time=data.get("current_session_time", 0.0),
            average_runtime=data.get("average_runtime", 0.0),
            min_runtime=data.get("min_runtime", 0.0),
            max_runtime=data.get("max_runtime", 0.0),
            top_left=tuple(data.get("top_left", (0, 0))),  # Convert to tuple if not present
            width=data.get("width", 800),
            height=data.get("height", 600),
            preview_area=data.get("preview_area", False),
            resize_client=data.get("resize_client", False),
        )

class Team:
    def __init__(self, name):
        self.name = name
        self.accounts = []

    def add_account(self, account):
        """
        Add an account to the team.
        """
        self.accounts.append(account)

    def to_dict(self):
        """
        Convert the team and its accounts to a dictionary.
        """
        return [account.to_dict() for account in self.accounts]

    @staticmethod
    def from_dict(name, accounts_data):
        """
        Create a Team object from a dictionary.
        """
        team = Team(name)
        for account_data in accounts_data:
            team.add_account(Account.from_dict(account_data))
        return team


class TeamManager:
    global log_history
    def __init__(self):
        self.teams = {}

    def add_team(self, team):
        """
        Add a team to the manager.
        """
        self.teams[team.name] = team

    def save_to_json(self, file_path):
        """
        Save all teams and their accounts to a JSON file.
        """
        data = {team_name: team.to_dict() for team_name, team in self.teams.items()}
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)

    def load_from_json(self, file_path):
        """
        Load teams and their accounts from a JSON file.
        Create the file if it does not exist.
        """
        try:
            with open(file_path, "r") as file:
                data = json.load(file)
                self.teams = {team_name: Team.from_dict(team_name, accounts) for team_name, accounts in data.items()}
        except FileNotFoundError:
            # Create the file if it doesn't exist
            with open(file_path, "w") as file:
                json.dump({}, file)
            log_history.append(f"File {file_path} not found. Created an empty file.")
            self.teams = {}
        except json.JSONDecodeError as e:
            log_history.append(f"Error parsing JSON from {file_path}: {e}")
            self.teams = {}


    def get_team(self, team_name):
        """
        Retrieve a team by name.
        """
        return self.teams.get(team_name)

    def get_first_team(self):
        """
        Get the first team in the manager.
        """
        if self.teams:
            return next(iter(self.teams.values()))

    def filter_accounts(self, team_name=None, character_name=None):
        """
        Filter accounts by team and/or character name.
        """
        results = []
        for team in self.teams.values():
            if team_name and team.name != team_name:
                continue
            for account in team.accounts:
                if character_name and account.character_name != character_name:
                    continue
                results.append(account)
        return results

class Patcher:
    global log_history

    def __init__(self):
        pass

    def get_process_module_base(self, process_handle: int) -> Optional[int]:
        pbi = PROCESS_BASIC_INFORMATION()
        return_length = ctypes.c_ulong(0)

        if ntdll.NtQueryInformationProcess(process_handle, 0, ctypes.byref(pbi), ctypes.sizeof(pbi), ctypes.byref(return_length)) != 0:
            return None

        peb_address = pbi.PebBaseAddress
        buffer = ctypes.create_string_buffer(ctypes.sizeof(PEB))

        bytes_read = ctypes.c_size_t()
        if not kernel32.ReadProcessMemory(process_handle, peb_address, buffer, ctypes.sizeof(PEB), ctypes.byref(bytes_read)):
            return None

        peb = PEB.from_buffer(buffer)
        return peb.ImageBaseAddress

    def search_bytes(self, haystack: bytes, needle: bytes) -> int:
        try:
            return haystack.index(needle)
        except ValueError:
            return -1

    def patch(self, pid: int) -> bool:

        process_handle = kernel32.OpenProcess(
            PROCESS_VM_OPERATION | PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_QUERY_INFORMATION, 
            False, 
            pid
        )
        
        if process_handle is None:
            log_history.append(f"Patcher - Could not open process with PID {pid}: {ctypes.GetLastError()}")
            return False

        sig_patch = bytes([0x56, 0x57, 0x68, 0x00, 0x01, 0x00, 0x00, 0x89, 0x85, 0xF4, 0xFE, 0xFF, 0xFF, 0xC7, 0x00, 0x00, 0x00, 0x00, 0x00])
        module_base = self.get_process_module_base(process_handle)
        if module_base is None:
            log_history.append("Patcher - Failed to get module base")
            kernel32.CloseHandle(process_handle)
            return False
        gwdata = ctypes.create_string_buffer(0x48D000)

        bytes_read = ctypes.c_size_t()
        if not kernel32.ReadProcessMemory(process_handle, module_base, gwdata, 0x48D000, ctypes.byref(bytes_read)):
            log_history.append(f"Patcher - Failed to read process memory: {ctypes.GetLastError()}")
            kernel32.CloseHandle(process_handle)
            return False

        idx = self.search_bytes(gwdata.raw, sig_patch)
        if idx == -1:
            log_history.append("Patcher - Failed to find signature")
            kernel32.CloseHandle(process_handle)
            return False

        mcpatch_address = module_base + idx - 0x1A
        payload = bytes([0x31, 0xC0, 0x90, 0xC3])

        bytes_written = ctypes.c_size_t()
        if not kernel32.WriteProcessMemory(process_handle, mcpatch_address, payload, len(payload), ctypes.byref(bytes_written)):
            log_history.append(f"Patcher - Failed to write process memory: {ctypes.GetLastError()}")
            kernel32.CloseHandle(process_handle)
            return False
        
        log_history.append(f"Patcher - Patched at address: {hex(mcpatch_address)}")
        kernel32.CloseHandle(process_handle)
        return True

    def get_hwnd_by_pid(self, pid: int) -> wintypes.HWND:
        """
        Retrieve the HWND (window handle) associated with a given PID.
        """
        hwnd = wintypes.HWND(0)  # Default handle if not found

        # Callback function for EnumWindows
        def callback(handle, extra):
            nonlocal hwnd
            window_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(handle, ctypes.byref(window_pid))
            if window_pid.value == pid and user32.IsWindowVisible(handle):
                hwnd = handle
                return False  # Stop enumeration
            return True  # Continue enumeration

        # Enumerate all windows and find the one matching the PID
        user32.EnumWindows(WNDENUMPROC(callback), 0)
        return hwnd


    def launch_and_patch(self, gw_exe_path: str, account: str, password: str, character: str, extra_args: str, elevated: bool) -> Optional[int]:
        command_line = f'"{gw_exe_path}" -email "{account}" -password "{password}"'
        if character:
            command_line += f' -character "{character}"'
        command_line += f" {extra_args}"

        startup_info = STARTUPINFO()
        startup_info.cb = ctypes.sizeof(startup_info)
        process_info = PROCESS_INFORMATION()

        success = kernel32.CreateProcessW(
            None,  
            command_line,
            None, 
            None,
            False,
            CREATE_SUSPENDED,
            None,
            None,
            ctypes.byref(startup_info),
            ctypes.byref(process_info)
        )

        if not success:
            log_history.append(f"Patcher - Failed to create process: {ctypes.GetLastError()}")
            return None

        pid = process_info.dwProcessId

        if self.patch(pid):
            log_history.append("Patcher - Multiclient patch applied successfully.")
        else:
            log_history.append("Patcher - Failed to apply multiclient patch.")
            kernel32.TerminateProcess(process_info.hProcess, 0)
            kernel32.CloseHandle(process_info.hProcess)
            kernel32.CloseHandle(process_info.hThread)
            return None
        
        if kernel32.ResumeThread(process_info.hThread) == -1:
            log_history.append(f"Python - Failed to resume thread: {ctypes.GetLastError()}")
            kernel32.TerminateProcess(process_info.hProcess, 0)
            kernel32.CloseHandle(process_info.hProcess)
            kernel32.CloseHandle(process_info.hThread)
            return None

        log_history.append("Patcher - Process resumed.")

        kernel32.CloseHandle(process_info.hProcess)
        kernel32.CloseHandle(process_info.hThread)

        return pid

class GWLauncher:
    global log_history, current_directory, py4gw_dll_name, blackbox_dll_name, ini_handler

    def __init__(self):     
        self.active_pids = []
        self.gmod_injection_delay = 0.5  # Delay before gMod injection (configurable)

    def wait_for_gw_window(self, pid, timeout=30):
        """Wait for GW window to be created and fully loaded"""
        log_history.append(f"Waiting for GW window (PID: {pid})")
        start_time = time.time()
        found_windows = []
        
        def enum_windows_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if window_pid == pid:
                        title = win32gui.GetWindowText(hwnd)
                        log_history.append(f"Wait for GW Window - Found window with title: '{title}' for PID: {pid}")
                        # Accept any window from the process initially
                        found_windows.append(hwnd)
                except Exception as e:
                    log_history.append(f"Wait for GW Window - Error in callback: {str(e)}")
            return True

        while time.time() - start_time < timeout:
            try:
                process = psutil.Process(pid)
                if process.status() != psutil.STATUS_RUNNING:
                    log_history.append(f"Wait for GW Window - Process {pid} is not running")
                    return False

                # Clear previous findings
                found_windows.clear()
                win32gui.EnumWindows(enum_windows_callback, None)
                
                if found_windows:
                    log_history.append(f"Wait for GW Window - Found {len(found_windows)} windows for process {pid}")
                    # Return True if we found any window from the process
                    return True
                
            except psutil.NoSuchProcess:
                log_history.append(f"Wait for GW Window - Process {pid} no longer exists")
                return False
            except Exception as e:
                log_history.append(f"Wait for GW Window - Error while waiting for GW window: {str(e)}")
                return False
                
            time.sleep(0.5)
            
            # Add progress indicator every 5 seconds
            elapsed = time.time() - start_time
            if elapsed % 5 < 0.5:
                log_history.append(f"Wait for GW Window - Still waiting... ({int(elapsed)}s)")
                # List all windows for the process
                try:
                    process = psutil.Process(pid)
                    log_history.append(f"Wait for GW Window - Process status: {process.status()}")
                    log_history.append(f"Wait for GW Window - Process command line: {process.cmdline()}")
                except Exception as e:
                    log_history.append(f"Wait for GW Window - Error getting process info: {str(e)}")
        
        log_history.append(f"Wait for GW Window - Timeout waiting for window of process {pid}")
        return False

    def inject_dll(self, pid, dll_path):
        if not dll_path or not os.path.exists(dll_path):
            log_history.append("Inject DLL - Invalid DLL path")
            return False

        log_history.append(f"Inject DLL - Starting DLL injection for PID: {pid}")
        kernel32 = ctypes.windll.kernel32
        process_handle = None
        allocated_memory = None
        thread_handle = None

        try:
            # Get process handle
            process_handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
            if not process_handle:
                log_history.append(f"Inject DLL - Failed to open process. Error: {ctypes.get_last_error()}")
                return False

            # Get LoadLibraryA address
            loadlib_addr = kernel32.GetProcAddress(
                kernel32._handle,
                b"LoadLibraryA"
            )
            if not loadlib_addr:
                log_history.append("Inject DLL - Failed to get LoadLibraryA address")
                return False

            # Prepare DLL path
            dll_path_bytes = dll_path.encode('ascii') + b'\0'
            path_size = len(dll_path_bytes)

            # Allocate memory in target process
            allocated_memory = kernel32.VirtualAllocEx(
                process_handle,
                0,
                path_size,
                VIRTUAL_MEM,
                PAGE_READWRITE
            )
            if not allocated_memory:
                log_history.append("Inject DLL - Failed to allocate memory")
                return False

            # Write DLL path to allocated memory
            written = ctypes.c_size_t(0)
            write_success = kernel32.WriteProcessMemory(
                process_handle,
                allocated_memory,
                dll_path_bytes,
                path_size,
                ctypes.byref(written)
            )
            if not write_success or written.value != path_size:
                log_history.append("Inject DLL - Failed to write to process memory")
                return False

            # Create remote thread
            thread_handle = kernel32.CreateRemoteThread(
                process_handle,
                None,
                0,
                loadlib_addr,
                allocated_memory,
                0,
                None
            )
            if not thread_handle:
                log_history.append("Inject DLL - Failed to create remote thread")
                return False

            # Wait for thread completion
            kernel32.WaitForSingleObject(thread_handle, 5000)  # 5 second timeout

            # Get thread exit code
            exit_code = ctypes.c_ulong(0)
            if kernel32.GetExitCodeThread(thread_handle, ctypes.byref(exit_code)):
                log_history.append(f"Inject DLL - Injection completed with exit code: {exit_code.value}")
                return exit_code.value != 0
            return False

        except Exception as e:
            log_history.append(f"Inject DLL - DLL injection failed with error: {str(e)}")
            return False

        finally:
            # Cleanup
            if thread_handle:
                kernel32.CloseHandle(thread_handle)
            if allocated_memory and process_handle:
                kernel32.VirtualFreeEx(process_handle, allocated_memory, 0, MEM_RELEASE)
            if process_handle:
                kernel32.CloseHandle(process_handle)

    def inject_BlackBox(self, pid, dll_path):
        """Inject GWBlackBoxdll.dll into the process"""
        
        if not os.path.exists(os.path.join(current_directory, "Addons", blackbox_dll_name)):
            log_history.append("GWBlackBox DLL path not valid")
            return False

        log_history.append(f"Injecting BlackBox from: {os.path.join(current_directory, "Addons", blackbox_dll_name)}")
        
        # Store original DLL path
        original_dll_path = os.path.join(current_directory, "Addons", blackbox_dll_name)
        
        try:
            # Use existing inject_dll method
            result = self.inject_dll(pid,original_dll_path)
            log_history.append("GWBlackBox injection " + ("successful" if result else "failed"))
            return result
        finally:
            pass

    def inject_gmod(self, pid):
        gmod_path = os.path.join(current_directory, "Addons", gmod_dll_name)
        if not os.path.exists(gmod_path):
            log_history.append("gMod DLL path not valid")
            return False

        log_history.append(f"Injecting gMod from: {gmod_path}")
        result = self.inject_dll(pid, gmod_path)
        log_history.append("gMod injection " + ("successful" if result else "failed"))
        return result
                
    def is_process_running(self, pid):
        try:
            process = psutil.Process(pid)
            return process.status() == psutil.STATUS_RUNNING
        except psutil.NoSuchProcess:
            return False

    def attempt_dll_injection(self, pid, delay=0, dll_type="Py4GW"):

        if delay > 0:
            log_history.append(f"Waiting {delay} seconds before injecting {dll_type} DLL...")
            time.sleep(delay)
        
        if not self.is_process_running(pid):
            log_history.append(f"Process no longer running, skipping {dll_type} DLL injection")
            return False
       
        
        if dll_type == "Py4GW":
            log_history.append("Attempting Py4GW DLL injection...")
            dll_dir = os.path.join(current_directory, py4gw_dll_name)
            return self.inject_dll(pid,dll_dir)
        elif dll_type == "BlackBox":
            log_history.append("Attempting BlackBox DLL injection...")
            dll_dir = os.path.join(current_directory, "Addons", "GWBlackBOX.dll")
            return self.inject_BlackBox(pid,dll_dir)
        elif dll_type == "gMod":
            log_history.append("Attempting gMod DLL injection...")
            return self.inject_gmod(pid)
        
        log_history.append(f"Skipping {dll_type} DLL injection (not enabled).")
        return False

    def start_injection_thread(self, pid, account: Account):
        def injection_thread():
            try:
                if self.wait_for_gw_window(pid):
                    log_history.append("Injection - GW window found, waiting for initialization...")
                    time.sleep(5)  # delay after window is found

                    if account.inject_blackbox:
                        if self.attempt_dll_injection(pid, delay=0, dll_type="BlackBox"):
                            log_history.append("GWBlackBOX.dll injection successful")
                        else:
                            log_history.append("GWBlackBOX.dll injection failed")

                    custom_dll_delay = 0
                    if account.inject_py4gw:
                        ini_handler.write_key("settings", "autoexec_script", account.script_path)
                        if self.attempt_dll_injection(pid, delay=custom_dll_delay, dll_type="Py4GW"):
                            log_history.append("Py4GW DLL injection successful")
                        else:
                            log_history.append("Py4GW DLL injection failed")
                else:
                    log_history.append("Failed to detect GW window")
            except Exception as e:
                log_history.append(f"Error in injection thread: {str(e)}")

        threading.Thread(target=injection_thread, daemon=True).start()

    def create_modlist_for_gmod(self, account: Account):
        if not account.gw_path:
            log_history.append("Cannot create modlist.txt: gw_path not specified")
            return

        # Get the directory containing Gw.exe
        gw_dir = os.path.dirname(account.gw_path)
        modlist_path = os.path.join(gw_dir, "modlist.txt")

        # Generate list of full paths to .tpf files
        mod_paths = account.gmod_mods  # Already full paths from select_mod_file()

        # Write to modlist.txt (create an empty file if no mods)
        try:
            with open(modlist_path, "w") as f:
                for mod_path in mod_paths:
                    f.write(f"{mod_path}\n")
            log_history.append(f"Updated modlist.txt with {len(mod_paths)} mods at {modlist_path}")
        except Exception as e:
            log_history.append(f"Error updating modlist.txt at {modlist_path}: {str(e)}")

    def start_team_launch_thread(self, team):
        def team_launch_thread():
            log_history.append(f"Launching team: {team.name}")
            for account in team.accounts:
                self.launch_gw(account)

                # Dynamic idle message update
                idle_time = 15  # Seconds
                for remaining in range(idle_time, 0, -1):
                    log_history[-1] = f"Idling... {remaining}s remaining to prevent log-in throttle"
                    time.sleep(1)  # Sleep 1 second and update countdown dynamically

                log_history.append("Idle complete, continuing...")

            log_history.append(f"Finished launching team: {team.name}")

        # Start the thread for launching the team
        threading.Thread(target=team_launch_thread, daemon=True).start()

    def launch_gw(self, account: Account):
        patcher = Patcher()
        try:
            pid = patcher.launch_and_patch(
                account.gw_path,
                account.email,
                account.password,
                account.character_name,
                account.extra_args,
                account.run_as_admin
            )

            if pid is None:
                log_history.append("Launch GW - Failed to launch or patch Guild Wars.")
                return

            log_history.append(f"Launch GW - Launched and patched GW with PID: {pid}")
            self.active_pids.append((account, pid))

            # Create modlist.txt and inject gMod.dll
            if account.inject_gmod:
                self.create_modlist_for_gmod(account)
                if self.attempt_dll_injection(pid, dll_type="gMod"):
                    log_history.append("gMod DLL injection successful")
                    time.sleep(3)  # 3-second delay after gMod, this may need to be adjusted to longer delay.
                else:
                    log_history.append("gMod DLL injection failed")

            if account.inject_py4gw or account.inject_blackbox:
                self.start_injection_thread(pid, account)

            """
            if account.resize_client or account.enable_client_rename:
                log_history.append(f"Launch GW - Waiting for window handle to be created.")

                hwnd = None
                retries = 10  # Maximum number of attempts
                retry_interval = 0.5  # Seconds between retries

                for attempt in range(retries):
                    hwnd = patcher.get_hwnd_by_pid(pid)
                    if hwnd:
                        break  # Exit the loop if hwnd is found
                    time.sleep(retry_interval)  # Wait before retrying

                if not hwnd:
                    log_history.append("Launch GW - Failed to find Guild Wars window after retries.")
                    return

                log_history.append(f"Launch GW - Found window handle: {hwnd}")


                if hwnd and account.enable_client_rename:
                    # Set the new title
                    client_name =  account.character_name if account.use_character_name else account.custom_client_name
                    log_history.append(f"Launch GW - renaming client to: {client_name}")
                    user32.SetWindowTextW(hwnd, client_name)
        
                if hwnd and account_data.resize_client:
                    # Move and resize the window
                    pos_x, pos_y = account_data.top_left
                    width, height = account_data.width, account_data.height
                    user32.MoveWindow(hwnd, account_data.top_left[0], account_data.top_left[1],
                                      account_data.width, account_data.height, True)

                    log_history.append(f"Patcher - Window Renamed: {client_name}, Pos({pos_x}, {pos_y}), Size({width}x{height})")
                else:
                    log_history.append("Patcher - Failed to find Guild Wars window.")

                kernel32.CloseHandle(process_info.hProcess)
                kernel32.CloseHandle(process_info.hThread)
                """
            #threading.Thread(target=self.monitor_game_process, args=(account, pid), daemon=True).start()
        except Exception as e:
            log_history.append(f"Error launching GW: {str(e)}")


# -------------------------------------------------#
# -------------- GUI Functions --------------------#

def create_docking_splits() -> list[hello_imgui.DockingSplit]:
    """
    Define the dockable layout:
    - Bottom: ConsoleDockSpace
    - Left: MainDockSpace
    - Right: AdvDockSpace
    Only active in Advanced View (when is_compact_view is False).
    """
    global is_compact_view, visible_windows
    if is_compact_view:
        visible_windows["AdvDockSpace"] = False
        visible_windows["ConsoleDockSpace"] = False
        visible_windows["MainDockSpace"] = True
        return []  # No splits in Compact View, MainDockSpace takes full space
    else:
        visible_windows["AdvDockSpace"] = True
        visible_windows["ConsoleDockSpace"] = True
        visible_windows["MainDockSpace"] = True
        return [
            # Bottom split for the Console
            hello_imgui.DockingSplit(
                initial_dock_="MainDockSpace",
                new_dock_="ConsoleDockSpace",
                direction_=imgui.Dir.down,
                ratio_=0.20
            ),
            # Right split for the Advanced View
            hello_imgui.DockingSplit(
                initial_dock_="MainDockSpace",
                new_dock_="AdvDockSpace",
                direction_=imgui.Dir.right,
                ratio_=0.70
            )
        ]

def create_dockable_windows() -> list[hello_imgui.DockableWindow]:
    """
    Define the dockable windows:
    - ConsoleDockSpace
    - MainDockSpace
    - AdvDockSpace
    Visibility depends on view mode (Compact hides Console and AdvDockSpace).
    """
    global visible_windows
    dockable_windows = []
    if visible_windows.get("MainDockSpace", True):
        dockable_windows.append(
            hello_imgui.DockableWindow(
                label_="Teams",
                dock_space_name_="MainDockSpace",
                gui_function_=show_team_view,
                can_be_closed_=False,
                is_visible_=True
            )
        )
    if visible_windows.get("AdvDockSpace", True):
        dockable_windows.append(
            hello_imgui.DockableWindow(
                label_="Account Configuration",
                dock_space_name_="AdvDockSpace",
                gui_function_=show_configuration_content,
                can_be_closed_=False,
                is_visible_=True
            )
        )   
    if visible_windows.get("AdvDockSpace", True):
        dockable_windows.append(
            hello_imgui.DockableWindow(
                label_="Launch Configuration",
                dock_space_name_="AdvDockSpace",
                gui_function_=show_account_content,
                can_be_closed_=False,
                is_visible_=True
            )
        )         
    if visible_windows.get("ConsoleDockSpace", True):
        dockable_windows.append(
            hello_imgui.DockableWindow(
                label_="Console",
                dock_space_name_="ConsoleDockSpace",
                gui_function_=show_log_console,
                is_visible_=True
            )
        )
    return dockable_windows

def show_log_console():
    """Content for the Console"""
    imgui.text("Console")
    imgui.separator()

    # Start scrollable child window
    imgui.begin_child(
    str_id="ConsoleDockSpaceWindow",
    size=imgui.ImVec2(0, 0),
    child_flags=int(imgui.ChildFlags_.borders.value),  # Ensure it's an int
    window_flags=int(imgui.WindowFlags_.horizontal_scrollbar.value)  # Ensure window_flags is also an int
)
    

    # Track scroll position
    scroll_y = imgui.get_scroll_y()                      # Current scroll position
    scroll_max_y = imgui.get_scroll_max_y()              # Max scroll position
    is_scrolled_to_bottom = (scroll_y >= scroll_max_y)   # Detect if at the bottom

    # Display log messages
    for i in range(len(log_history)):
        imgui.text(log_history[i])

    # Auto-scroll only if user was at the bottom
    if is_scrolled_to_bottom:
        imgui.set_scroll_here_y(1.0)

    imgui.end_child()



launch_gw = GWLauncher()



def show_team_view():
    """
    Content for the MainDockSpace - Displays all teams and their accounts in a MainDockSpace.
    """
    global team_manager, launch_gw, visible_windows, is_compact_view, last_is_compact_view

    imgui.text("Teams Manager")
    imgui.separator()

    # Display the current view mode
    current_mode = "Compact View" if is_compact_view else "Advanced View"
    imgui.push_style_color(imgui.Col_.text, (0.0, 1.0, 0.0, 1.0))  # Green text
    imgui.text(f"View Mode: {current_mode}")
    imgui.pop_style_color()
    
    # Checkbox to toggle between Compact and Advanced View
    changed, is_compact_view = imgui.checkbox("Toggle View##visibility_toggle", is_compact_view)
    
    if imgui.is_item_hovered():
        if is_compact_view:
            imgui.set_tooltip("Switch to Advanced View to show Console and Configuration panels")
        else:
            imgui.set_tooltip("Switch to Compact View to hide Console and Configuration panels")
    
    # Save to INI if changed
    if changed:
        ini_handler.write_key("Py4GW_Launcher", "is_compact_view", str(is_compact_view))
        log_history.append(f"Saved is_compact_view to [Py4GW_Launcher]: {is_compact_view}")

    imgui.separator()

    # Update visibility and window size only if the view mode changed
    if is_compact_view != last_is_compact_view:
        if is_compact_view:
            hello_imgui.change_window_size((350, 450))
            visible_windows["AdvDockSpace"] = False
            visible_windows["ConsoleDockSpace"] = False
            visible_windows["MainDockSpace"] = True
        else:
            hello_imgui.change_window_size((800, 600))
            visible_windows["AdvDockSpace"] = True
            visible_windows["ConsoleDockSpace"] = True
            visible_windows["MainDockSpace"] = True

        # Log the visibility state only when it changes
        log_history.append(
            f"Visibility toggled: AdvDockSpace={visible_windows['AdvDockSpace']}, "
            f"ConsoleDockSpace={visible_windows['ConsoleDockSpace']}, "
            f"MainDockSpace={visible_windows['MainDockSpace']}"
        )

        # Update the last state
        last_is_compact_view = is_compact_view

    if not team_manager.teams:
        imgui.text("No teams available. Please add teams in the configuration window.")
        return

    for team_name, team in team_manager.teams.items():
        if imgui.tree_node(f"{team_name}##{id(team)}"):
            imgui.spacing()
            
            # Button to launch all accounts in the team sequentially
            if imgui.button(f"Launch {team_name}##{id(team)}"):
                log_history.append(f"Launching all accounts for team: {team_name}")
                launch_gw.start_team_launch_thread(team)  # Use the new threaded function

            imgui.spacing()
            imgui.separator()

            # List all accounts in the team
            for account in team.accounts:
                if imgui.tree_node(f"{account.character_name}##{id(account)}"):
                    imgui.spacing()
                    
                    # Launch individual accounts
                    if imgui.button(f"Launch {account.character_name}##{id(account)}"):
                        log_history.append(f"Launching account: {account.character_name}")
                        launch_gw.launch_gw(account)

                    imgui.tree_pop()

            imgui.tree_pop()



def show_account_content():
    """
    Content for the Main Content Window
    with auto-saving for any modifications.
    """
    global selected_team, team_manager, config_file, launch_gw

    
    # Generate a list of team names
    team_names = [team.name for team in team_manager.teams.values()]

    # Keep track of the currently selected team index
    selected_index = -1  # Default to -1, meaning no selection
    if selected_team:
        selected_index = team_names.index(selected_team.name) if selected_team.name in team_names else -1

    # Combo box for existing teams
    imgui.set_next_item_width(300)
    changed, selected_index = imgui.combo(
        "Select Team", selected_index, team_names
    )

    # Update the selected team if a selection is made
    if changed and selected_index != -1:
        selected_team = team_manager.get_team(team_names[selected_index])
        if selected_team:
            log_history.append(f"Selected team: {selected_team.name}")
    imgui.same_line()

    if not selected_team:
        imgui.text("No team selected. Please select a team from the dropdown.")
        return

    imgui.separator()
    imgui.text(f"Managing Team: {selected_team.name}")
    imgui.separator()

    # Iterate over accounts in the selected team
    for account in selected_team.accounts:
        if imgui.collapsing_header(f"{account.character_name}##{id(account)}"):

            # Launch Account Button
            if imgui.button(f"Launch Account##{id(account)}"):
                launch_gw.launch_gw(account)
                log_history.append(f"Launching account: {account.character_name}")

            # Python Script Path
            imgui.text("Run python script at launch")
            imgui.set_next_item_width(300)
            _, account.script_path = imgui.input_text(f"##{id(account)}", account.script_path, 256)
            imgui.same_line()
            if imgui.button(f"Select Script##{id(account)}"):
                selected_script = select_python_script()
                if selected_script:
                    account.script_path = selected_script
                    team_manager.save_to_json(config_file)  # Auto-save

            """
            # Custom colors for the Client Configuration header
            imgui.push_style_color(imgui.Col_.header, (0.3, 0.4, 0.2, 1.0))  # Greenish header
            imgui.push_style_color(imgui.Col_.header_hovered, (0.35, 0.45, 0.25, 1.0))
            imgui.push_style_color(imgui.Col_.header_active, (0.25, 0.35, 0.15, 1.0))

            if imgui.collapsing_header(f"Client Configuration##{id(account)}"):
                imgui.pop_style_color(3)  # Restore header colors
                imgui.spacing()

                # Set background color for the Client Configuration block
                imgui.push_style_color(imgui.Col_.child_bg, (0.3, 0.4, 0.2, 0.5))  # Greenish background
                if imgui.begin_child(
                    f"ClientConfigBlock##{id(account)}",
                    imgui.ImVec2(0, 150),  # Define size
                    child_flags=0,  # Optional child-specific flags
                    window_flags=imgui.WindowFlags_.no_move,  # Window-specific flags
                    ):

                    #Client Rename Options
                    _, account.enable_client_rename = imgui.checkbox(f"Enable Client Rename##{id(account)}", account.enable_client_rename)
                    team_manager.save_to_json(config_file)  # Auto-save

                    if account.enable_client_rename:
                        _, account.use_character_name = imgui.checkbox(f"Use Character Name##{id(account)}", account.use_character_name)
                        team_manager.save_to_json(config_file)  # Auto-save

                        if not account.use_character_name:
                            imgui.set_next_item_width(300)
                            _, account.custom_client_name = imgui.input_text(f"Custom Client Name##{id(account)}", account.custom_client_name, 128)
                            team_manager.save_to_json(config_file)  # Auto-save

                    imgui.separator()
                    # Resize Client Checkbox
                    _, account.resize_client = imgui.checkbox(f"Resize Client##{id(account)}", account.resize_client)
                    team_manager.save_to_json(config_file)  # Auto-save

                    if account.resize_client:
                        # Preview Area Checkbox
                        _, account.preview_area = imgui.checkbox(f"Preview Area##{id(account)}", account.preview_area)
                        team_manager.save_to_json(config_file)  # Auto-save

                        imgui.text("Top-Left Position")
                        imgui.set_next_item_width(100)
                        changed_x, top_left_x = imgui.input_int(f"X##TopLeft{id(account)}", account.top_left[0])
                        imgui.same_line()
                        imgui.set_next_item_width(100)
                        changed_y, top_left_y = imgui.input_int(f"Y##TopLeft{id(account)}", account.top_left[1])
                        if changed_x or changed_y:
                            account.top_left = (top_left_x, top_left_y)
                            team_manager.save_to_json(config_file)  # Auto-save

                        imgui.spacing()

                        # Width and Height
                        imgui.text("Client Size")
                        imgui.set_next_item_width(100)
                        changed_width, account.width = imgui.input_int(f"Width##{id(account)}", account.width)
                        imgui.same_line()
                        imgui.set_next_item_width(100)
                        changed_height, account.height = imgui.input_int(f"Height##{id(account)}", account.height)
                        if changed_width or changed_height:
                            team_manager.save_to_json(config_file)  # Auto-save

                        imgui.spacing()

                    imgui.end_child()
                imgui.pop_style_color(1)  # Restore background color

            else:
                imgui.pop_style_color(3)  # Restore header colors if not open

            # Account Statistics Collapsible Section
            imgui.push_style_color(imgui.Col_.header, (0.2, 0.35, 0.45, 1.0))  # Custom color for the header
            imgui.push_style_color(imgui.Col_.header_hovered, (0.25, 0.4, 0.5, 1.0))
            imgui.push_style_color(imgui.Col_.header_active, (0.15, 0.3, 0.4, 1.0))

            if imgui.collapsing_header(f"Account Statistics##{id(account)}"):
                imgui.pop_style_color(3)  # Restore the previous header colors
                imgui.spacing()

                # Set background color for the statistics block
                imgui.push_style_color(imgui.Col_.child_bg, (0.2, 0.35, 0.45, 0.5))
                if imgui.begin_child(
                    f"StatsBlock##{id(account)}",
                    imgui.ImVec2(0, 200),  # Define size
                    child_flags=0,  # Optional child-specific flags
                    window_flags=imgui.WindowFlags_.no_move,  # Window-specific flags
                ):
                    if imgui.begin_table(f"##StatsTable{id(account)}", 2, imgui.TableFlags_.borders | imgui.TableFlags_.row_bg):
                        imgui.table_setup_column("Metric", imgui.TableColumnFlags_.width_stretch)
                        imgui.table_setup_column("Value", imgui.TableColumnFlags_.width_stretch)
                        imgui.table_headers_row()

                        stats = {
                            "Last Launch Time": account.last_launch_time or "N/A",
                            "Total Runtime (hours)": f"{account.total_runtime:.2f}",
                            "Session Time (hours)": f"{account.current_session_time:.2f}",
                            "Average Runtime (hours)": f"{account.average_runtime:.2f}",
                            "Min Runtime (hours)": f"{account.min_runtime:.2f}",
                            "Max Runtime (hours)": f"{account.max_runtime:.2f}",
                        }

                        for metric, value in stats.items():
                            imgui.table_next_row()
                            imgui.table_set_column_index(0)
                            imgui.text(metric)
                            imgui.table_set_column_index(1)
                            imgui.text(value)

                        imgui.end_table()

                    imgui.end_child()
                imgui.pop_style_color(1)


            else:
                imgui.pop_style_color(3)  # Restore the previous header colors if not open
            """
            # Save changes after any modification
            team_manager.save_to_json(config_file)



def save_teams_to_json(name):
    global config_file
    imgui.separator()
    if imgui.button("Save##" + str(name)):
        try:
            team_manager.save_to_json(config_file)
            log_history.append("Config saved!")
        except Exception as e:
            log_history.append(f"Error saving teams: {e}")

def select_folder():
    """
    Open a folder selection dialog and return the selected folder path.
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window
    folder_path = filedialog.askdirectory(title="Select Guild Wars Path")
    root.destroy()
    return folder_path

def select_gw_exe():
    """
    Open a file selection dialog to select the 'Gw.exe' file.
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window
    file_path = filedialog.askopenfilename(
        title="Select Guild Wars Executable",
        filetypes=[("Executable Files", "*.exe")],  # Restrict to .exe files
        initialfile="Gw.exe"  # Suggest Gw.exe as the default file
    )
    root.destroy()
    return file_path

def select_dll(name):
    """
    Open a file selection dialog to select the 'DLL' file.
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window
    file_path = filedialog.askopenfilename(
        title="Select DLL",
        filetypes=[("dynamic Libraries", "*.dll")],  # Restrict to .exe files
        initialfile=name  # Suggest Gw.exe as the default file
    )
    root.destroy()
    return file_path

def select_python_script():
    """
    Open a file selection dialog to select the 'DLL' file.
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window
    file_path = filedialog.askopenfilename(
        title="Select Python script",
        filetypes=[("Python Scripts", "*.py")]  # Restrict to .exe files
    )
    root.destroy()
    return file_path

# Function for mod selection
def select_mod_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Mod File",
        filetypes=[("Mod Files", "*.tpf")]
    )
    root.destroy()
    if file_path:
        # Return the full path directly
        log_history.append(f"Selected mod file: {file_path}")
        return file_path
    return None

team_manager = TeamManager()
selected_team = None
entered_team_name = ""
data_loaded = False
show_password = False
new_account_data = {
    "character_name": "",
    "email": "",
    "password": "",
    "gw_client_name": "",
    "gw_path": "",
    "extra_args": "",
    "run_as_admin": False,
    "inject_py4gw": True,
    "inject_blackbox": False,
    "inject_gmod": False,
    "gmod_mods": []
}

# Initialize view mode persistence
is_compact_view = ini_handler.read_bool("Py4GW_Launcher", "is_compact_view", False)
last_is_compact_view = is_compact_view
visible_windows = {
    "AdvDockSpace": True,
    "MainDockSpace": True,
    "ConsoleDockSpace": True,
}
log_history.append(f"Loaded is_compact_view from [Py4GW_Launcher]: {is_compact_view}")

def show_configuration_content():
    global config_file, team_manager, selected_team, entered_team_name, data_loaded, show_password, new_account_data

    # Automatically load data from JSON if not already loaded
    if not data_loaded:
        try:
            team_manager.load_from_json(config_file)
            log_history.append(f"Teams loaded from {config_file}")

            # Attempt to auto-select the first team
            first_team = team_manager.get_first_team()
            if first_team:
                selected_team = first_team
                entered_team_name = first_team.name  # Pre-fill the team name input
                log_history.append(f"Team Configuration: Auto-selected first team: {first_team.name}")
            else:
                log_history.append("No teams found. Please create one.")
        except Exception as e:
            log_history.append(f"Error loading teams: {e}")
        data_loaded = True


    # Title and separator
    imgui.text("Team Management")
    imgui.separator()

    imgui.text("Select or enter a team name:")
    imgui.set_next_item_width(150)  # Standardized field width

    # Generate a list of team names
    team_names = [team.name for team in team_manager.teams.values()]

    # Keep track of the currently selected team index
    selected_index = -1  # Default to -1, meaning no selection
    if selected_team:
        selected_index = team_names.index(selected_team.name) if selected_team.name in team_names else -1

    # Combo box for existing teams
    changed, selected_index = imgui.combo(
        "Existing Teams", selected_index, team_names
    )

    # Update the selected team if a selection is made
    if changed and selected_index != -1:
        selected_team = team_manager.get_team(team_names[selected_index])
        if selected_team:
            entered_team_name = selected_team.name  # Pre-fill the team name field
            log_history.append(f"Selected team from combo box: {selected_team.name}")
    imgui.same_line()
    imgui.set_next_item_width(150)  # Standardized field width
    _, entered_team_name = imgui.input_text("Team Name", entered_team_name, 128)
    imgui.same_line()

    if imgui.button("Select/Create Team"):
        if entered_team_name.strip():
            existing_team = team_manager.get_team(entered_team_name)
            if existing_team:
                selected_team = existing_team
                log_history.append(f"Selected existing team: {entered_team_name}")
            else:
                new_team = Team(entered_team_name)
                team_manager.add_team(new_team)
                selected_team = new_team
                log_history.append(f"Created new team: {entered_team_name}")
        else:
            log_history.append("Please enter a valid team name.")
    imgui.separator()

    if selected_team:
        imgui.text(f"Managing Team: {selected_team.name}")
        imgui.separator()

        # Display existing accounts
        for account in selected_team.accounts:
            if imgui.collapsing_header(f"{account.character_name}##{id(account)}"):
                imgui.spacing()
                imgui.set_next_item_width(300)  # Standardized field width
                _, account.character_name = imgui.input_text(f"Character Name##{id(account)}", account.character_name, 128)
                imgui.spacing()
                imgui.set_next_item_width(300)
                _, account.email = imgui.input_text(f"Email##{id(account)}", account.email, 128)
                imgui.spacing()

        
                password_flags = 0 if show_password else imgui.InputTextFlags_.password.value
                imgui.set_next_item_width(300)

                _, account.password = imgui.input_text(
                    label=f"Password##{id(account)}",                # Label for the input box
                    str=account.password,            # Existing value to display and modify
                    flags=password_flags  # Password flag to obscure text
                )

                imgui.same_line()

                _, show_password = imgui.checkbox(f"Show Password##{id(account)}", show_password)


                imgui.spacing()

                imgui.set_next_item_width(300)
                _, account.gw_client_name = imgui.input_text(f"Rename GW Client##{id(account)}", account.gw_client_name, 128)
                imgui.set_next_item_width(300)
                old_gw_path = account.gw_path
                _, account.gw_path = imgui.input_text(f"GW Path##{id(account)}", account.gw_path, 128)
                # Button for folder selection
                imgui.same_line()
                if imgui.button(f"Select Gw.exe##{id(account)}"):
                    selected_exe = select_gw_exe()
                    if selected_exe:
                        account.gw_path = selected_exe
                        if account.inject_gmod:
                            launch_gw.create_modlist_for_gmod(account)
                # Check if gw_path is in a protected directory
                if account.gw_path:
                    normalized_path = os.path.normpath(account.gw_path).lower()
                    protected_dirs = [
                        os.path.normpath("C:/Program Files (x86)").lower(),
                        os.path.normpath("C:/Program Files").lower()
                    ]
                    is_protected = any(normalized_path.startswith(protected_dir) for protected_dir in protected_dirs)
                    if is_protected:
                        imgui.push_style_color(imgui.Col_.text, (1.0, 0.0, 0.0, 1.0))  # Red text
                        imgui.text_wrapped(
                                "Warning: GW Path is in a protected directory (C:/Program Files (x86) or C:/Program Files). "
                                "The launcher requires admin privileges to create/modify files (e.g., modlist.txt) in this location. "
                                "Use an unprotected directory such as 'C:/Games/Guild Wars', or run the launcher with elevated privileges (as administrator)." 
                            )
                        imgui.pop_style_color()
                # If gw_path changed manually, update modlist.txt
                if old_gw_path != account.gw_path and account.inject_gmod:
                    launch_gw.create_modlist_for_gmod(account)
                imgui.set_next_item_width(300)
                _, account.extra_args = imgui.input_text(f"Extra Args##{id(account)}", account.extra_args, 128)
                _, account.run_as_admin = imgui.checkbox(f"Run as Admin##{id(account)}", account.run_as_admin)
                _, account.inject_py4gw = imgui.checkbox(f"Inject Py4GW##{id(account)}", account.inject_py4gw)
                _, account.inject_blackbox = imgui.checkbox(f"Inject Blackbox##{id(account)}", account.inject_blackbox)

                old_inject_gmod = account.inject_gmod
                _, account.inject_gmod = imgui.checkbox(f"Inject gMod##{id(account)}", account.inject_gmod)
                if old_inject_gmod != account.inject_gmod:
                    if account.inject_gmod:
                        launch_gw.create_modlist_for_gmod(account)
                    else:
                        gw_dir = os.path.dirname(account.gw_path)
                        modlist_path = os.path.join(gw_dir, "modlist.txt")
                        if os.path.exists(modlist_path):
                            try:
                                os.remove(modlist_path)
                                log_history.append(f"Removed modlist.txt at {modlist_path} as gMod injection was disabled")
                            except Exception as e:
                                log_history.append(f"Error removing modlist.txt at {modlist_path}: {str(e)}")

                if account.inject_gmod:
                    imgui.text("gMod Mods:")
                    for i, mod in enumerate(account.gmod_mods):
                        imgui.text(f" - {mod}")
                        imgui.same_line()
                        if imgui.button(f"Remove##{i}_{id(account)}"):
                            account.gmod_mods.pop(i)
                            team_manager.save_to_json(config_file)
                            launch_gw.create_modlist_for_gmod(account)
                    if imgui.button(f"Add Mod##{id(account)}"):
                        mod_file = select_mod_file()
                        if mod_file and mod_file not in account.gmod_mods:
                            account.gmod_mods.append(mod_file)
                            team_manager.save_to_json(config_file)
                            launch_gw.create_modlist_for_gmod(account)

                save_teams_to_json(id(account))
                imgui.same_line()
                if imgui.button(f"Delete Account##{id(account)}"):
                    selected_team.accounts.remove(account)
                    log_history.append(f"Deleted account: {account.character_name}")
                    gw_dir = os.path.dirname(account.gw_path)
                    modlist_path = os.path.join(gw_dir, "modlist.txt")
                    if os.path.exists(modlist_path):
                        try:
                            os.remove(modlist_path)
                            log_history.append(f"Removed modlist.txt at {modlist_path} as account was deleted")
                        except Exception as e:
                            log_history.append(f"Error removing modlist.txt at {modlist_path}: {str(e)}")

        # Collapsible section for new account form
        if imgui.collapsing_header("Add New Account", imgui.TreeNodeFlags_.default_open.value):
            imgui.spacing()
    
            for key in new_account_data.keys():
                if key == "password":  # Special handling for the password field
                    password_flags = 0 if show_password else imgui.InputTextFlags_.password.value
                    imgui.set_next_item_width(300)  # Standardized field width
            
                    # Input field for password
                    _, new_account_data[key] = imgui.input_text(
                    label=f"Password##new_item",  # Label for the input box
                    str=new_account_data[key],    # Existing value to display and modify
                    flags=password_flags  # Password flag to obscure text
                    )

                    # Checkbox for toggling password visibility
                    imgui.same_line()
                    _, show_password = imgui.checkbox("Show Password##new_item", show_password)
                elif key == "gw_path":  # Special handling for the GW Path field
                    imgui.set_next_item_width(300)  # Standardized field width
            
                    # Input field for GW Path
                    _, new_account_data[key] = imgui.input_text(
                        key.replace("_", " ").title() + "##new_item", 
                        new_account_data[key], 
                        128
                    )

                    # Button for folder selection
                    imgui.same_line()
                    if imgui.button(f"Select Gw.exe##new_item"):
                        selected_exe = select_gw_exe()
                        if selected_exe:
                            new_account_data[key] = selected_exe
                    # Check if gw_path is in a protected directory for new account
                    if new_account_data[key]:
                        normalized_path = os.path.normpath(new_account_data[key]).lower()
                        protected_dirs = [
                            os.path.normpath("C:/Program Files (x86)").lower(),
                            os.path.normpath("C:/Program Files").lower()
                        ]
                        is_protected = any(normalized_path.startswith(protected_dir) for protected_dir in protected_dirs)
                        if is_protected:
                            imgui.push_style_color(imgui.Col_.text, (1.0, 0.0, 0.0, 1.0))  # Red text
                            imgui.text_wrapped(
                                "Warning: GW Path is in a protected directory (C:/Program Files (x86) or C:/Program Files). "
                                "The launcher requires admin privileges to create/modify files (e.g., modlist.txt) in this location. "
                                "Use an unprotected directory such as 'C:/Games/Guild Wars', or run the launcher with elevated privileges (as administrator)." 
                            )
                            imgui.pop_style_color()
                elif key == "gmod_mods":
                    _, new_account_data["inject_gmod"] = imgui.checkbox("Inject gMod##new_item", new_account_data["inject_gmod"])
                    if new_account_data["inject_gmod"]:
                        imgui.text("gMod Mods:")
                        for i, mod in enumerate(new_account_data["gmod_mods"]):
                            imgui.text(f" - {mod}")
                            imgui.same_line()
                            if imgui.button(f"Remove##{i}_new"):
                                new_account_data["gmod_mods"].pop(i)
                        if imgui.button("Add Mod##new"):
                            mod_file = select_mod_file()
                            if mod_file and mod_file not in new_account_data["gmod_mods"]:
                                new_account_data["gmod_mods"].append(mod_file)
                elif key == "inject_gmod":
                    continue
                elif isinstance(new_account_data[key], bool):
                    _, new_account_data[key] = imgui.checkbox(key.replace("_", " ").title() + "##new_item", new_account_data[key])
                elif isinstance(new_account_data[key], str):
                    imgui.set_next_item_width(300)  # Standardized field width
                    _, new_account_data[key] = imgui.input_text(key.replace("_", " ").title() + "##new_item", new_account_data[key], 128)

            if imgui.button("Add Account"):
                new_account = Account(**new_account_data)
                selected_team.add_account(new_account)
                log_history.append(f"Added account: {new_account.character_name} to team: {selected_team.name}")
                team_manager.save_to_json(config_file)
                if new_account.inject_gmod:
                    launch_gw.create_modlist_for_gmod(new_account)
                new_account_data["gmod_mods"] = []
            imgui.same_line()
            if imgui.button("Clear Form"):
                for key in new_account_data.keys():
                    if key == "gmod_mods":
                        new_account_data[key] = []
                    elif isinstance(new_account_data[key], str):
                        new_account_data[key] = ""
                    else:
                        new_account_data[key] = False

def set_taskbar_icon(icon_path: str):
    """Set both the taskbar icon and window title bar icon on Windows."""
    try:
        # Step 1: Set the Windows App User Model ID (AppID)
        myappid = "mycompany.myproduct.subproduct.version"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        # Step 2: Get window handle dynamically
        hwnd = ctypes.windll.user32.GetForegroundWindow()  # Get the currently active window
        if hwnd:
            icon_path = os.path.abspath(icon_path)  # Ensure full absolute path
            icon = ctypes.windll.user32.LoadImageW(0, icon_path, 1, 0, 0, 0x00000010)
            ctypes.windll.user32.SendMessageW(hwnd, 0x80, 0, icon)  # Set small icon (title bar)
            ctypes.windll.user32.SendMessageW(hwnd, 0x80, 1, icon)  # Set large icon (taskbar)
            print(f"✅ Window & Taskbar icon set successfully: {icon_path}")
        else:
            print("❌ ERROR: Could not find window handle.")

    except Exception as e:
        print(f"❌ Failed to set taskbar icon: {str(e)}")
        
def main() -> None:
    """Run the Py4GW Launcher application with ImGui."""
    try:
        runner_params = hello_imgui.RunnerParams()
        runner_params.app_window_params.window_title = "Py4GW Launcher"
        runner_params.app_window_params.window_geometry.size = (350, 450) if is_compact_view else (800, 600)
        runner_params.imgui_window_params.default_imgui_window_type = hello_imgui.DefaultImGuiWindowType.provide_full_screen_dock_space
        runner_params.docking_params.docking_splits = create_docking_splits()

        # Explicitly set the ini_filename for Hello ImGui settings
        runner_params.ini_filename = "Py4GW_Launcher.ini"
        log_history.append(f"Using Hello ImGui ini_filename: {runner_params.ini_filename}")

        # Check for version mismatch and handle it before initializing ImGui
        check_and_handle_version_mismatch(runner_params.ini_filename)

        def update_gui():
            global visible_windows
            runner_params.docking_params.dockable_windows = create_dockable_windows()
            runner_params.docking_params.docking_splits = create_docking_splits()

        runner_params.callbacks.show_gui = update_gui
        
        set_taskbar_icon("python_icon.ico")
        
        hello_imgui.run(runner_params)
    except Exception as e:
        log_history.append(f"Application error: {str(e)}")

if __name__ == "__main__":
    main()