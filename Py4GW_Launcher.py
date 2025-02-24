from imgui_bundle import hello_imgui, imgui
import json
import tkinter as tk
from tkinter import filedialog
import ctypes
import ctypes.wintypes
from ctypes import wintypes
import threading
import time
import win32gui
import win32process
import psutil
import sys
import configparser
import os
import tempfile
import shutil
from typing import Optional

# Windows API libraries for process and window manipulation
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Global variables for application state
error_message = ""
show_error_popup = False
success_message = ""
team_filter = ""
current_page = 0
items_per_page = 5
log_history = []


# Extracts and copies embedded DLLs to the launcher's directory if running as a frozen executable
def get_embedded_dll_path(dll_name, subdir=None):
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
        dll_src = os.path.join(
            base_path, dll_name if not subdir else os.path.join(subdir, dll_name)
        )
        launcher_dir = os.path.dirname(sys.executable)
        dll_dest = os.path.join(launcher_dir, dll_name)
        if not os.path.exists(dll_dest):
            shutil.copy2(dll_src, dll_dest)
            log_history.append(f"Copied {dll_name} to {launcher_dir}")
        return dll_dest
    return os.path.join(
        os.getcwd(), dll_name if not subdir else os.path.join(subdir, dll_name)
    )


# Logs application messages to a file, clearing the in-memory log after writing
def log_to_file():
    with open(os.path.join(os.getcwd(), "Py4GW.log"), "a") as f:
        for entry in log_history[:]:
            f.write(f"{entry}\n")
    log_history.clear()


class IniHandler:
    """Handles reading, writing, and managing INI configuration files."""

    def __init__(self, filename: str = "Py4GW.ini"):
        base_path = os.getcwd()
        self.filename = os.path.join(base_path, filename)
        self.last_modified = 0
        self.config = configparser.ConfigParser()
        if not os.path.exists(self.filename):
            self.config["settings"] = {
                "account_config_file": "accounts.json",
                "py4gw_dll_name": "Py4GW.dll",
                "blackbox_dll_name": "GWBlackBOX.dll",
            }
            with open(self.filename, "w") as configfile:
                self.config.write(configfile)
            log_history.append(f"Created default INI file: {self.filename}")
            log_to_file()

    def reload(self) -> configparser.ConfigParser:
        """Reload the INI file if it has been modified."""
        current_mtime = os.path.getmtime(self.filename)
        if current_mtime != self.last_modified:
            self.last_modified = current_mtime
            self.config.read(self.filename)
        return self.config

    def save(self, config: configparser.ConfigParser) -> None:
        """Save changes to the INI file."""
        with open(self.filename, "w") as configfile:
            config.write(configfile)

    def read_key(self, section: str, key: str, default_value: str = "") -> str:
        """Read a string value from the INI file, returning a default if not found."""
        config = self.reload()
        try:
            return config.get(section, key)
        except (configparser.NoOptionError, configparser.NoSectionError):
            return default_value

    def write_key(self, section: str, key: str, value: str) -> None:
        """Write or update a key-value pair in the INI file."""
        config = self.reload()
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, key, str(value))
        self.save(config)


class TeamManager:
    """Manages multiple teams of Guild Wars accounts, handling persistence to JSON."""

    def __init__(self):
        self.teams = {}

    def add_team(self, team):
        """Add a team to the manager."""
        self.teams[team.name] = team

    def save_to_json(self, base_path: str, file_path: str):
        """Save all teams and their accounts to a JSON file in the specified path."""
        config_file_path = os.path.join(base_path, file_path)
        data = {team_name: team.to_dict() for team_name, team in self.teams.items()}
        os.makedirs(os.path.dirname(config_file_path), exist_ok=True)
        with open(config_file_path, "w") as file:
            json.dump(data, file, indent=4)
        log_history.append(f"Saved teams to {config_file_path}")
        log_to_file()

    def load_from_json(self, base_path: str, file_path: str):
        """Load teams and their accounts from a JSON file, creating an empty file if it doesn’t exist."""
        config_file_path = os.path.join(base_path, file_path)
        if os.path.exists(config_file_path):
            try:
                with open(config_file_path, "r") as file:
                    data = json.load(file)
                    self.teams = {
                        team_name: Team.from_dict(team_name, accounts)
                        for team_name, accounts in data.items()
                    }
                    log_history.append(f"Loaded teams from {config_file_path}")
            except json.JSONDecodeError as e:
                log_history.append(f"Error parsing JSON from {config_file_path}: {e}")
                self.teams = {}
        else:
            log_history.append(
                f"No accounts.json found at {config_file_path}, starting fresh"
            )
            self.teams = {}
        log_to_file()

    def get_team(self, team_name):
        """Retrieve a team by name, returning None if not found."""
        return self.teams.get(team_name)

    def get_first_team(self):
        """Get the first team in the manager, or None if no teams exist."""
        return next(iter(self.teams.values())) if self.teams else None


current_directory = os.getcwd()
ini_file = "Py4GW.ini"
config_file = "accounts.json"
py4gw_dll_name = get_embedded_dll_path("Py4GW.dll")
blackbox_dll_name = get_embedded_dll_path("GWBlackBOX.dll", "Addons")
gmod_dll_name = get_embedded_dll_path("gMod.dll", "Addons")
log_history.append("Welcome To Py4GW!")
log_to_file()

# Windows API constants for process and memory management
PROCESS_ALL_ACCESS = 0x1F0FFF
VIRTUAL_MEM = 0x1000 | 0x2000
PAGE_READWRITE = 0x04
MEM_RELEASE = 0x8000
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_QUERY_INFORMATION = 0x0400
MAX_PATH = 260
TH32CS_SNAPPROCESS = 0x00000002
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
HWND_TOP = 0
WM_SETTEXT = 0x000C
CREATE_SUSPENDED = 0x00000004
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

# Set up Windows API function signatures
user32.GetWindowThreadProcessId.argtypes = [
    wintypes.HWND,
    ctypes.POINTER(wintypes.DWORD),
]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL
user32.SetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPCWSTR]
user32.SetWindowTextW.restype = wintypes.BOOL


class PROCESS_BASIC_INFORMATION(ctypes.Structure):
    """Structure for basic process information."""

    _fields_ = [
        ("Reserved1", ctypes.c_void_p),
        ("PebBaseAddress", ctypes.c_void_p),
        ("Reserved2", ctypes.c_void_p * 2),
        ("UniqueProcessId", ctypes.c_ulong),
        ("Reserved3", ctypes.c_void_p),
    ]


class PEB(ctypes.Structure):
    """Structure for Process Environment Block (PEB) data."""

    _fields_ = [
        ("InheritedAddressSpace", ctypes.c_ubyte),
        ("ReadImageFileExecOptions", ctypes.c_ubyte),
        ("BeingDebugged", ctypes.c_ubyte),
        ("BitField", ctypes.c_ubyte),
        ("Mutant", ctypes.c_void_p),
        ("ImageBaseAddress", ctypes.c_void_p),
    ]


class PROCESSENTRY32(ctypes.Structure):
    """Structure for process entry information in a snapshot."""

    _fields_ = [
        ("dwSize", ctypes.c_ulong),
        ("cntUsage", ctypes.c_ulong),
        ("th32ProcessID", ctypes.c_ulong),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", ctypes.c_ulong),
        ("cntThreads", ctypes.c_ulong),
        ("th32ParentProcessID", ctypes.c_ulong),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", ctypes.c_ulong),
        ("szExeFile", ctypes.c_char * MAX_PATH),
    ]


class STARTUPINFO(ctypes.Structure):
    """Structure for startup information of a process."""

    _fields_ = [
        ("cb", ctypes.c_ulong),
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
        ("hStdError", ctypes.c_void_p),
    ]


class PROCESS_INFORMATION(ctypes.Structure):
    """Structure for process information after creation."""

    _fields_ = [
        ("hProcess", ctypes.c_void_p),
        ("hThread", ctypes.c_void_p),
        ("dwProcessId", ctypes.c_ulong),
        ("dwThreadId", ctypes.c_ulong),
    ]


ntdll = ctypes.windll.ntdll


class Account:
    """Represents a Guild Wars account with configuration options and change tracking."""

    def __init__(
        self,
        character_name,
        email,
        password,
        gw_client_name,
        gw_path,
        extra_args,
        run_as_admin,
        inject_py4gw,
        inject_blackbox,
        script_path="",
        enable_client_rename=False,
        use_character_name=False,
        custom_client_name="",
        last_launch_time=None,
        total_runtime=0.0,
        current_session_time=0.0,
        average_runtime=0.0,
        min_runtime=0.0,
        max_runtime=0.0,
        top_left=(0, 0),
        width=800,
        height=600,
        preview_area=False,
        resize_client=False,
        gmod_enabled=False,
        mod_list=None,
    ):
        self.character_name = character_name
        self.email = email
        self.password = password
        self.gw_client_name = gw_client_name
        self.gw_path = gw_path
        self.extra_args = extra_args
        self.run_as_admin = run_as_admin
        self.inject_py4gw = inject_py4gw
        self.inject_blackbox = inject_blackbox
        self.script_path = script_path
        self.enable_client_rename = enable_client_rename
        self.use_character_name = use_character_name
        self.custom_client_name = custom_client_name
        self.last_launch_time = last_launch_time
        self.total_runtime = total_runtime
        self.current_session_time = current_session_time
        self.average_runtime = average_runtime
        self.min_runtime = min_runtime
        self.max_runtime = max_runtime
        self.top_left = top_left
        self.width = width
        self.height = height
        self.preview_area = preview_area
        self.resize_client = resize_client
        self.gmod_enabled = gmod_enabled
        self.mod_list = mod_list if mod_list is not None else []
        self.ini_handler = IniHandler()
        self.has_changes = False  # Tracks whether the account has unsaved changes

    def mark_changed(self):
        """Mark this account as having unsaved changes."""
        self.has_changes = True

    def clear_changes(self):
        """Clear the changes flag after saving."""
        self.has_changes = False

    def to_dict(self):
        """Convert account data to a dictionary for JSON serialization."""
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
            "gmod_enabled": self.gmod_enabled,
            "mod_list": self.mod_list,
        }

    @staticmethod
    def from_dict(data):
        """Create an Account object from a dictionary, initializing with no changes."""
        account = Account(
            **{
                k: v
                for k, v in data.items()
                if k in Account.__init__.__code__.co_varnames
            }
        )
        account.has_changes = False
        return account


class Team:
    """Represents a group of Guild Wars accounts for coordinated launches."""

    def __init__(self, name):
        self.name = name
        self.accounts = []

    def add_account(self, account):
        """Add an account to the team."""
        self.accounts.append(account)

    def to_dict(self):
        """Convert team accounts to a list of dictionaries for JSON serialization."""
        return [account.to_dict() for account in self.accounts]

    @staticmethod
    def from_dict(name, accounts_data):
        """Create a Team object from a dictionary of account data."""
        team = Team(name)
        for account_data in accounts_data:
            team.add_account(Account.from_dict(account_data))
        return team


# Initialize TeamManager globally after its class definition
team_manager = TeamManager()

class Patcher:
    """Handles patching Guild Wars processes to enable multiclient support."""

    def __init__(self):
        pass

    def get_process_module_base(self, process_handle: int) -> Optional[int]:
        """Retrieve the base address of the Guild Wars module in the process."""
        pbi = PROCESS_BASIC_INFORMATION()
        return_length = ctypes.c_ulong(0)
        if (
            ntdll.NtQueryInformationProcess(
                process_handle,
                0,
                ctypes.byref(pbi),
                ctypes.sizeof(pbi),
                ctypes.byref(return_length),
            )
            != 0
        ):
            return None
        peb_address = pbi.PebBaseAddress
        buffer = ctypes.create_string_buffer(ctypes.sizeof(PEB))
        bytes_read = ctypes.c_size_t()
        if not kernel32.ReadProcessMemory(
            process_handle,
            peb_address,
            buffer,
            ctypes.sizeof(PEB),
            ctypes.byref(bytes_read),
        ):
            return None
        peb = PEB.from_buffer(buffer)
        return peb.ImageBaseAddress

    def search_bytes(self, haystack: bytes, needle: bytes) -> int:
        """Search for a byte pattern in a byte array, returning the index or -1 if not found."""
        try:
            return haystack.index(needle)
        except ValueError:
            return -1

    def patch(self, pid: int) -> bool:
        """Apply a multiclient patch to the Guild Wars process with the given PID."""
        process_handle = kernel32.OpenProcess(
            PROCESS_VM_OPERATION
            | PROCESS_VM_READ
            | PROCESS_VM_WRITE
            | PROCESS_QUERY_INFORMATION,
            False,
            pid,
        )
        if not process_handle:
            log_history.append(
                f"Patcher - Could not open process with PID {pid}: {ctypes.GetLastError()}"
            )
            return False
        sig_patch = bytes(
            [
                0x56,
                0x57,
                0x68,
                0x00,
                0x01,
                0x00,
                0x00,
                0x89,
                0x85,
                0xF4,
                0xFE,
                0xFF,
                0xFF,
                0xC7,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
            ]
        )
        module_base = self.get_process_module_base(process_handle)
        if module_base is None:
            kernel32.CloseHandle(process_handle)
            return False
        gwdata = ctypes.create_string_buffer(0x48D000)
        bytes_read = ctypes.c_size_t()
        if not kernel32.ReadProcessMemory(
            process_handle, module_base, gwdata, 0x48D000, ctypes.byref(bytes_read)
        ):
            kernel32.CloseHandle(process_handle)
            return False
        idx = self.search_bytes(gwdata.raw, sig_patch)
        if idx == -1:
            kernel32.CloseHandle(process_handle)
            return False
        mcpatch_address = module_base + idx - 0x1A
        payload = bytes([0x31, 0xC0, 0x90, 0xC3])
        bytes_written = ctypes.c_size_t()
        if not kernel32.WriteProcessMemory(
            process_handle,
            mcpatch_address,
            payload,
            len(payload),
            ctypes.byref(bytes_written),
        ):
            kernel32.CloseHandle(process_handle)
            return False
        log_history.append(f"Patcher - Patched at address: {hex(mcpatch_address)}")
        kernel32.CloseHandle(process_handle)
        return True

    def launch_and_patch(
        self,
        gw_exe_path: str,
        account: str,
        password: str,
        character: str,
        extra_args: str,
        elevated: bool,
    ) -> Optional[int]:
        """Launch Guild Wars with account details, apply the multiclient patch, and return the process ID."""
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
            ctypes.byref(process_info),
        )
        if not success:
            log_history.append(
                f"Patcher - Failed to create process: {ctypes.GetLastError()}"
            )
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
            log_history.append(
                f"Patcher - Failed to resume thread: {ctypes.GetLastError()}"
            )
            kernel32.TerminateProcess(process_info.hProcess, 0)
            kernel32.CloseHandle(process_info.hProcess)
            kernel32.CloseHandle(process_info.hThread)
            return None
        log_history.append("Patcher - Process resumed.")
        kernel32.CloseHandle(process_info.hProcess)
        kernel32.CloseHandle(process_info.hThread)
        return pid


class GWLauncher:
    """Manages launching Guild Wars processes and injecting DLLs for enhancements."""

    def __init__(self):
        self.active_pids = []

    def wait_for_gw_window(self, pid, timeout=30):
        """Wait for the Guild Wars window to appear, returning True if found within the timeout."""
        log_history.append(f"Waiting for GW window (PID: {pid})")
        start_time = time.time()
        found_windows = []

        def enum_windows_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if window_pid == pid:
                        title = win32gui.GetWindowText(hwnd)
                        log_history.append(
                            f"Wait for GW Window - Found window: '{title}' (PID: {pid})"
                        )
                        found_windows.append(hwnd)
                except Exception as e:
                    log_history.append(f"Wait for GW Window - Callback error: {str(e)}")
            return True

        while time.time() - start_time < timeout:
            try:
                process = psutil.Process(pid)
                if process.status() != psutil.STATUS_RUNNING:
                    log_history.append(
                        f"Wait for GW Window - Process {pid} not running"
                    )
                    return False
                found_windows.clear()
                win32gui.EnumWindows(enum_windows_callback, None)
                if found_windows:
                    log_history.append(
                        f"Wait for GW Window - Found {len(found_windows)} windows for PID {pid}"
                    )
                    return True
            except psutil.NoSuchProcess:
                log_history.append(
                    f"Wait for GW Window - Process {pid} no longer exists"
                )
                return False
            except Exception as e:
                log_history.append(f"Wait for GW Window - Error: {str(e)}")
                return False
            time.sleep(0.5)
        log_history.append(
            f"Wait for GW Window - Timeout after {timeout}s for PID {pid}"
        )
        return False

    def inject_dll(self, pid, dll_path):
        """Inject a DLL into the specified Guild Wars process."""
        if not dll_path or not os.path.exists(dll_path):
            log_history.append(f"Inject DLL - Invalid path: {dll_path}")
            return False
        log_history.append(
            f"Inject DLL - Starting injection for PID {pid} with {dll_path}"
        )
        process_handle = None
        allocated_memory = None
        thread_handle = None
        try:
            process_handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
            if not process_handle:
                log_history.append(
                    f"Inject DLL - Failed to open process {pid}: Error {ctypes.get_last_error()}"
                )
                return False
            kernel32_handle = kernel32.GetModuleHandleA(b"kernel32.dll")
            if not kernel32_handle:
                log_history.append("Inject DLL - Failed to get kernel32.dll handle")
                return False
            loadlib_addr = kernel32.GetProcAddress(kernel32_handle, b"LoadLibraryA")
            if not loadlib_addr:
                log_history.append("Inject DLL - Failed to get LoadLibraryA address")
                return False
            dll_path_bytes = dll_path.encode("ascii") + b"\0"
            path_size = len(dll_path_bytes)
            allocated_memory = kernel32.VirtualAllocEx(
                process_handle, 0, path_size, VIRTUAL_MEM, PAGE_READWRITE
            )
            if not allocated_memory:
                log_history.append("Inject DLL - Failed to allocate memory")
                return False
            written = ctypes.c_size_t(0)
            if not kernel32.WriteProcessMemory(
                process_handle,
                allocated_memory,
                dll_path_bytes,
                path_size,
                ctypes.byref(written),
            ):
                log_history.append("Inject DLL - Failed to write to process memory")
                return False
            thread_handle = kernel32.CreateRemoteThread(
                process_handle, None, 0, loadlib_addr, allocated_memory, 0, None
            )
            if not thread_handle:
                log_history.append("Inject DLL - Failed to create remote thread")
                return False
            kernel32.WaitForSingleObject(thread_handle, 5000)
            exit_code = ctypes.c_ulong(0)
            kernel32.GetExitCodeThread(thread_handle, ctypes.byref(exit_code))
            log_history.append(
                f"Inject DLL - Completed with exit code: {exit_code.value}"
            )
            return exit_code.value != 0
        except Exception as e:
            log_history.append(f"Inject DLL - Exception: {str(e)}")
            return False
        finally:
            if thread_handle:
                kernel32.CloseHandle(thread_handle)
            if allocated_memory and process_handle:
                kernel32.VirtualFreeEx(process_handle, allocated_memory, 0, MEM_RELEASE)
            if process_handle:
                kernel32.CloseHandle(process_handle)

    def inject_BlackBox(self, pid, dll_path):
        """Inject the GWBlackBox.dll into the specified process."""
        if not os.path.exists(dll_path):
            log_history.append(f"Inject BlackBox - Invalid path: {dll_path}")
            return False
        log_history.append(f"Injecting BlackBox from: {dll_path}")
        result = self.inject_dll(pid, dll_path)
        log_history.append(
            f"GWBlackBox injection {'successful' if result else 'failed'}"
        )
        return result

    def is_process_running(self, pid):
        """Check if a process with the given PID is still running."""
        try:
            process = psutil.Process(pid)
            return process.status() == psutil.STATUS_RUNNING
        except psutil.NoSuchProcess:
            return False

    def attempt_dll_injection(self, pid, delay=0, dll_type="Py4GW"):
        """Attempt to inject a specified DLL into the process after a delay if needed."""
        if delay > 0:
            log_history.append(f"Waiting {delay}s before injecting {dll_type} DLL...")
            time.sleep(delay)
        if not self.is_process_running(pid):
            log_history.append(
                f"Process {pid} not running, skipping {dll_type} injection"
            )
            return False
        if dll_type == "gMod":
            log_history.append("Attempting gMod DLL injection...")
            return self.inject_dll(pid, gmod_dll_name)
        elif dll_type == "Py4GW":
            log_history.append("Attempting Py4GW DLL injection...")
            return self.inject_dll(pid, py4gw_dll_name)
        elif dll_type == "BlackBox":
            log_history.append("Attempting BlackBox DLL injection...")
            return self.inject_BlackBox(pid, blackbox_dll_name)
        log_history.append(f"Skipping {dll_type} DLL injection (not enabled)")
        return False

    def start_injection_thread(self, pid, account: Account):
        """Start a background thread to handle DLL injection for the given account and process."""

        def injection_thread():
            if self.wait_for_gw_window(pid):
                log_history.append("Injection - GW window found, waiting 2s...")
                time.sleep(2)
                if account.gmod_enabled:
                    self.attempt_dll_injection(pid, dll_type="gMod")
                custom_dll_delay = 2 if account.gmod_enabled else 0
                if account.inject_blackbox:
                    self.attempt_dll_injection(
                        pid, delay=custom_dll_delay, dll_type="BlackBox"
                    )
                if account.inject_py4gw:
                    account.ini_handler.write_key(
                        "settings", "autoexec_script", account.script_path
                    )
                    self.attempt_dll_injection(
                        pid, delay=custom_dll_delay, dll_type="Py4GW"
                    )
            else:
                log_history.append("Injection - Failed to detect GW window")

        threading.Thread(target=injection_thread, daemon=True).start()

    def start_team_launch_thread(self, team):
        """Launch all accounts in a team sequentially in a separate thread to prevent login throttling."""

        def team_launch_thread():
            log_history.append(f"Launching team: {team.name}")
            for account in team.accounts:
                self.launch_gw(account)
                idle_time = 10
                for remaining in range(idle_time, 0, -1):
                    log_history[-1] = (
                        f"Idling... {remaining}s to prevent login throttle"
                    )
                    time.sleep(1)
                log_history.append("Idle complete, continuing...")
            log_history.append(f"Finished launching team: {team.name}")

        threading.Thread(target=team_launch_thread, daemon=True).start()

    def launch_gw(self, account: Account):
        """Launch Guild Wars for the given account, apply patches, and inject DLLs if enabled."""
        patcher = Patcher()
        try:
            pid = patcher.launch_and_patch(
                account.gw_path,
                account.email,
                account.password,
                account.character_name,
                account.extra_args,
                account.run_as_admin,
            )
            if pid is None:
                log_history.append(
                    f"Failed to launch Guild Wars for {account.character_name}. Check path and credentials."
                )
                return
            log_history.append(
                f"Launched and patched GW with PID: {pid} for {account.character_name}"
            )
            self.active_pids.append((account, pid))

            # Handle gMod DLL copy to game directory
            gw_dir = os.path.dirname(os.path.normpath(account.gw_path))
            d3d9_path = os.path.join(gw_dir, "d3d9.dll")
            d3d9_bak_path = os.path.join(gw_dir, "d3d9.dll.bak")
            if account.gmod_enabled:
                if os.path.exists(d3d9_path):
                    shutil.move(d3d9_path, d3d9_bak_path)
                    log_history.append(f"Renamed existing {d3d9_path} to {d3d9_bak_path}")
                shutil.copy2(gmod_dll_name, d3d9_path)
                log_history.append(f"Copied {gmod_dll_name} to {d3d9_path}")

            if account.inject_py4gw or account.inject_blackbox or account.gmod_enabled:
                self.start_injection_thread(pid, account)
            log_history.append(f"Successfully launched {account.character_name}")
        except Exception as e:
            log_history.append(
                f"Error launching GW for {account.character_name}: {str(e)}"
            )


launch_gw = GWLauncher()


def create_docking_splits() -> list[hello_imgui.DockingSplit]:
    """Define the docking layout for the application windows."""
    return [
        hello_imgui.DockingSplit(
            initial_dock_="MainDockSpace",
            new_dock_="LogConsole",
            direction_=imgui.Dir.down,
            ratio_=0.25,
        ),
        hello_imgui.DockingSplit(
            initial_dock_="MainDockSpace",
            new_dock_="TreeView",
            direction_=imgui.Dir.left,
            ratio_=0.40,  # Adjusted ratio to 40%
        ),
    ]


def create_dockable_windows() -> list[hello_imgui.DockableWindow]:
    """Define the dockable windows for the application interface."""
    return [
        hello_imgui.DockableWindow(
            label_="Log Console",
            dock_space_name_="LogConsole",
            gui_function_=show_log_console,
            can_be_closed_=False  # Disable close button
        ),
        hello_imgui.DockableWindow(
            label_="Teams",
            dock_space_name_="TreeView",
            gui_function_=show_tree_view,
            can_be_closed_=False  # Disable close button
        ),
        hello_imgui.DockableWindow(
            label_="Account Configuration",
            dock_space_name_="MainDockSpace",
            gui_function_=show_configuration_content,
            can_be_closed_=False  # Disable close button
        ),
    ]


def show_log_console():
    """Display a scrollable log of application events, auto-scrolling to the bottom if at the end."""
    imgui.text("Log Console")
    imgui.separator()
    imgui.begin_child(
        "LogConsoleWindow",
        imgui.ImVec2(0, 0),
        child_flags=int(imgui.ChildFlags_.borders.value),
        window_flags=int(imgui.WindowFlags_.horizontal_scrollbar.value),
    )
    scroll_y = imgui.get_scroll_y()
    scroll_max_y = imgui.get_scroll_max_y()
    is_scrolled_to_bottom = scroll_y >= scroll_max_y
    for i in range(len(log_history)):
        imgui.text(log_history[i])
    if is_scrolled_to_bottom:
        imgui.set_scroll_here_y(1.0)
    imgui.end_child()


def show_tree_view():
    """Display a hierarchical view of teams and accounts with filtering, pagination, and launch script configuration."""
    global team_manager, launch_gw, team_filter, current_page, items_per_page
    imgui.text("Teams Manager")
    imgui.separator()
    imgui.text("Filter teams below:")
    imgui.set_next_item_width(200)
    _, team_filter = imgui.input_text(
        "Filter Teams", team_filter, flags=imgui.InputTextFlags_.enter_returns_true
    )
    if imgui.is_item_hovered():
        imgui.set_tooltip("Type to filter teams by name.")
    filtered_teams = {
        name: team
        for name, team in team_manager.teams.items()
        if team_filter.lower() in name.lower()
    }
    team_list = list(filtered_teams.items())
    start_idx = current_page * items_per_page
    end_idx = min(start_idx + items_per_page, len(team_list))
    for team_name, team in team_list[start_idx:end_idx]:
        if team_manager.get_first_team() and team_name == team_manager.get_first_team().name:
            # Always expand the first team
            imgui.set_next_item_open(True)  # Force expansion
            if imgui.tree_node(f"{team_name}##{id(team)}"):
                imgui.push_style_color(imgui.Col_.button, (0.2, 0.6, 0.2, 1.0))
                if imgui.button(f"Launch {team_name}##{id(team)}"):
                    launch_gw.start_team_launch_thread(team)
                imgui.pop_style_color()
                imgui.separator()
                for account in team.accounts:
                    if imgui.tree_node(f"{account.character_name}##{id(account)}"):
                        imgui.push_style_color(imgui.Col_.button, (0.2, 0.6, 0.2, 1.0))
                        if imgui.button(f"Launch {account.character_name}##{id(account)}"):
                            launch_gw.launch_gw(account)
                        imgui.pop_style_color()
                        # Add script configuration for launching with Python script
                        imgui.text("Run Python script at launch")
                        imgui.set_next_item_width(300)
                        changed, account.script_path = imgui.input_text(
                            f"Script Path##{id(account)}_script", account.script_path
                        )
                        imgui.same_line()
                        if imgui.button(f"Select Script##{id(account)}_select"):
                            selected_script = select_python_script()
                            if selected_script:
                                account.script_path = selected_script
                                team_manager.save_to_json(os.getcwd(), config_file)
                        if imgui.is_item_hovered():
                            imgui.set_tooltip(
                                "Select a Python script (e.g., .py) to run at launch."
                            )
                        if changed and imgui.is_item_deactivated_after_edit():
                            team_manager.save_to_json(os.getcwd(), config_file)
                        imgui.tree_pop()
                imgui.tree_pop()
        else:
            if len(team.accounts) > 5 and not imgui.is_item_expanded():
                imgui.set_next_item_open(False)
            if imgui.tree_node(f"{team_name}##{id(team)}"):
                imgui.push_style_color(imgui.Col_.button, (0.2, 0.6, 0.2, 1.0))
                if imgui.button(f"Launch {team_name}##{id(team)}"):
                    launch_gw.start_team_launch_thread(team)
                imgui.pop_style_color()
                imgui.separator()
                for account in team.accounts:
                    if imgui.tree_node(f"{account.character_name}##{id(account)}"):
                        imgui.push_style_color(imgui.Col_.button, (0.2, 0.6, 0.2, 1.0))
                        if imgui.button(f"Launch {account.character_name}##{id(account)}"):
                            launch_gw.launch_gw(account)
                        imgui.pop_style_color()
                        # Add script configuration for launching with Python script
                        imgui.text("Run Python script at launch")
                        imgui.set_next_item_width(300)
                        changed, account.script_path = imgui.input_text(
                            f"Script Path##{id(account)}_script", account.script_path
                        )
                        imgui.same_line()
                        if imgui.button(f"Select Script##{id(account)}_select"):
                            selected_script = select_python_script()
                            if selected_script:
                                account.script_path = selected_script
                                team_manager.save_to_json(os.getcwd(), config_file)
                        if imgui.is_item_hovered():
                            imgui.set_tooltip(
                                "Select a Python script (e.g., .py) to run at launch."
                            )
                        if changed and imgui.is_item_deactivated_after_edit():
                            team_manager.save_to_json(os.getcwd(), config_file)
                        imgui.tree_pop()
                imgui.tree_pop()
    if not team_manager.teams:
        imgui.text("No teams available. Add teams in the Account Configuration window.")


def show_configuration_content():
    """Manage teams and configure account details with dynamic UI and change tracking for the Save button."""
    global config_file, team_manager, selected_team, entered_team_name, data_loaded, show_password, new_account_data
    # Set focus on this window to make it the default tab on startup
    imgui.set_next_window_focus()
    
    if not data_loaded:
        try:
            team_manager.load_from_json(os.getcwd(), config_file)
            first_team = team_manager.get_first_team()
            if first_team:
                selected_team = first_team
                entered_team_name = first_team.name
                log_history.append(
                    f"Team Configuration: Auto-selected first team: {first_team.name}"
                )
            else:
                log_history.append("No teams found. Please create one.")
        except Exception as e:
            log_history.append(f"Error loading teams: {e}")
        data_loaded = True
        log_to_file()
    imgui.text("Team Management")
    imgui.separator()
    imgui.push_style_var(imgui.StyleVar_.frame_padding, (4, 4))
    imgui.text("Step 1: Select or Create a Team")
    imgui.pop_style_var()
    imgui.push_style_color(imgui.Col_.text, (0.8, 0.8, 0.8, 1.0))
    imgui.text_wrapped(
        "Select an existing team from the dropdown, or enter a new name and click 'Create Team'."
    )
    imgui.pop_style_color()
    team_names = [team.name for team in team_manager.teams.values()]
    selected_index = (
        team_names.index(selected_team.name)
        if selected_team and selected_team.name in team_names
        else -1
    )
    imgui.text("Select Existing Team:")
    imgui.set_next_item_width(200)
    changed, selected_index = imgui.combo("Existing Teams", selected_index, team_names)
    if changed and selected_index != -1:
        selected_team = team_manager.get_team(team_names[selected_index])
        entered_team_name = selected_team.name
        log_history.append(f"Selected team: {selected_team.name}")
        log_to_file()
    imgui.text("Or Create New Team:")
    imgui.set_next_item_width(200)
    _, entered_team_name = imgui.input_text(
        "Team Name", entered_team_name, flags=imgui.InputTextFlags_.enter_returns_true
    )
    if imgui.is_item_hovered():
        imgui.set_tooltip("Enter a unique name and press Enter or click 'Create Team'.")
    imgui.same_line()
    imgui.push_style_color(imgui.Col_.button, (0.2, 0.6, 0.2, 1.0))
    if imgui.button("Create Team") or (
        imgui.is_item_active() and imgui.is_key_pressed(imgui.Key.enter)
    ):
        if entered_team_name.strip():
            if entered_team_name in team_manager.teams:
                log_history.append(
                    f"Team '{entered_team_name}' already exists. Select it or use a different name."
                )
            else:
                new_team = Team(entered_team_name)
                team_manager.add_team(new_team)
                selected_team = new_team
                log_history.append(f"Created new team: {entered_team_name}")
            log_to_file()
        else:
            log_history.append("Team name cannot be empty.")
            log_to_file()
    imgui.pop_style_color()
    imgui.separator()
    if selected_team:
        imgui.text(f"Selected Team: {selected_team.name}")
        imgui.separator()
        # Determine if "Add New Account" should be expanded or collapsed
        default_open_flag = (
            imgui.TreeNodeFlags_.default_open.value
            if not selected_team.accounts
            else 0
        )
        if imgui.collapsing_header(
            "Add New Account", default_open_flag
        ):
            imgui.push_style_var(imgui.StyleVar_.frame_padding, (4, 4))
            imgui.text("Step 2: Add Account Details")
            imgui.pop_style_var()
            imgui.push_style_color(imgui.Col_.text, (0.8, 0.8, 0.8, 1.0))
            imgui.text_wrapped(
                "Fill in all required fields (*) and click 'Add Account'."
            )
            imgui.pop_style_color()
            required_fields = ["character_name", "email", "password", "gw_path"]
            imgui.push_style_color(imgui.Col_.text, (1.0, 0.5, 0.5, 1.0))
            imgui.set_next_item_width(300)
            _, new_account_data["character_name"] = imgui.input_text(
                "Character Name *", new_account_data["character_name"]
            )
            imgui.pop_style_color()
            if imgui.is_item_hovered():
                imgui.set_tooltip("Enter the in-game character name (required).")
            imgui.set_next_item_width(300)
            _, new_account_data["email"] = imgui.input_text(
                "Email *", new_account_data["email"]
            )
            if imgui.is_item_hovered():
                imgui.set_tooltip("Guild Wars account email (required).")
            imgui.set_next_item_width(300)
            password_flags = (
                0 if show_password else imgui.InputTextFlags_.password.value
            )
            _, new_account_data["password"] = imgui.input_text(
                "Password *", new_account_data["password"], flags=password_flags
            )
            imgui.same_line()
            _, show_password = imgui.checkbox("Show", show_password)
            imgui.push_style_color(imgui.Col_.text, (1.0, 0.5, 0.5, 1.0))
            imgui.set_next_item_width(300)
            _, new_account_data["gw_path"] = imgui.input_text(
                "Guild Wars Path *", new_account_data["gw_path"]
            )
            imgui.pop_style_color()
            imgui.same_line()
            if imgui.button("Browse"):
                selected_exe = select_gw_exe()
                if selected_exe:
                    new_account_data["gw_path"] = selected_exe
            if imgui.is_item_hovered():
                imgui.set_tooltip("Path to Gw.exe (required).")
            imgui.set_next_item_width(300)
            _, new_account_data["gw_client_name"] = imgui.input_text(
                "GW Client Name", new_account_data["gw_client_name"]
            )
            if imgui.is_item_hovered():
                imgui.set_tooltip("Optional name for renaming the GW client.")
            imgui.set_next_item_width(300)
            _, new_account_data["extra_args"] = imgui.input_text(
                "Extra Arguments", new_account_data["extra_args"]
            )
            if imgui.is_item_hovered():
                imgui.set_tooltip(
                    "Additional command-line arguments for Guild Wars (optional)."
                )
            _, new_account_data["run_as_admin"] = imgui.checkbox(
                "Run As Admin", new_account_data["run_as_admin"]
            )
            if imgui.is_item_hovered():
                imgui.set_tooltip("Run Guild Wars with administrative privileges.")
            _, new_account_data["inject_py4gw"] = imgui.checkbox(
                "Inject Py4GW", new_account_data["inject_py4gw"]
            )
            _, new_account_data["inject_blackbox"] = imgui.checkbox(
                "Inject Blackbox", new_account_data["inject_blackbox"]
            )
            if imgui.is_item_hovered():
                imgui.set_tooltip(
                    "Inject the Blackbox DLL for additional functionality."
                )
            _, new_account_data["gmod_enabled"] = imgui.checkbox(
                "Inject gMod", new_account_data["gmod_enabled"]
            )
            if imgui.is_item_hovered():
                imgui.set_tooltip(
                    "Inject the gMod DLL to enable mod support (requires modlist.txt)."
                )
            imgui.separator()
            imgui.push_style_color(imgui.Col_.button, (0.2, 0.6, 0.2, 1.0))
            if imgui.button("Add Account"):
                missing = [
                    k.replace("_", " ").title()
                    for k in required_fields
                    if not new_account_data[k].strip()
                ]
                if missing:
                    log_history.append(f"Missing required fields: {', '.join(missing)}")
                elif not os.path.exists(new_account_data["gw_path"]):
                    log_history.append(
                        "Invalid Guild Wars path. Please select a valid Gw.exe file."
                    )
                else:
                    new_account = Account(**new_account_data)
                    selected_team.add_account(new_account)
                    team_manager.save_to_json(os.getcwd(), config_file)
                    log_history.append(f"Added account: {new_account.character_name}")
                    for key in new_account_data:
                        new_account_data[key] = (
                            "" if isinstance(new_account_data[key], str) else False
                        )
                log_to_file()
            imgui.pop_style_color()
            imgui.same_line()
            if imgui.button("Clear Form"):
                for key in new_account_data:
                    new_account_data[key] = (
                        "" if isinstance(new_account_data[key], str) else False
                    )
                log_history.append("Cleared account form")
                log_to_file()

        # Existing Accounts - Display and manage existing accounts with collapsible sections and change tracking
        imgui.begin_child(
            "ExistingAccounts",
            imgui.ImVec2(0, 0),
            child_flags=int(imgui.ChildFlags_.borders.value),
        )
        imgui.text("Existing Accounts")
        for i, account in enumerate(selected_team.accounts):
            if imgui.collapsing_header(
                f"{account.character_name or 'Unnamed Account'}##{id(account)}"
            ):
                changed = False

                # Character Name
                imgui.set_next_item_width(300)
                char_changed, account.character_name = imgui.input_text(
                    f"Character Name##{id(account)}_char", account.character_name
                )
                if char_changed and imgui.is_item_deactivated_after_edit():
                    team_manager.save_to_json(os.getcwd(), config_file)
                    log_history.append(
                        f"Updated character name for {account.character_name}"
                    )
                    changed = True
                if imgui.is_item_hovered():
                    imgui.set_tooltip("Enter the in-game character name.")

                # Email
                imgui.set_next_item_width(300)
                email_changed, account.email = imgui.input_text(
                    f"Email##{id(account)}_email", account.email
                )
                if email_changed and imgui.is_item_deactivated_after_edit():
                    team_manager.save_to_json(os.getcwd(), config_file)
                    log_history.append(f"Updated email for {account.character_name}")
                    changed = True
                if imgui.is_item_hovered():
                    imgui.set_tooltip("Guild Wars account email.")

                # Password
                password_flags = (
                    0 if show_password else imgui.InputTextFlags_.password.value
                )
                imgui.set_next_item_width(300)
                pwd_changed, account.password = imgui.input_text(
                    f"Password##{id(account)}_pwd",
                    account.password,
                    flags=password_flags,
                )
                if pwd_changed and imgui.is_item_deactivated_after_edit():
                    team_manager.save_to_json(os.getcwd(), config_file)
                    log_history.append(f"Updated password for {account.character_name}")
                    changed = True
                imgui.same_line()
                _, show_password = imgui.checkbox(
                    f"Show##{id(account)}_show", show_password
                )

                # Guild Wars Path
                imgui.set_next_item_width(300)
                path_changed, account.gw_path = imgui.input_text(
                    f"Guild Wars Path##{id(account)}_path", account.gw_path
                )
                if path_changed and imgui.is_item_deactivated_after_edit():
                    team_manager.save_to_json(os.getcwd(), config_file)
                    changed = True
                imgui.same_line()
                if imgui.button(f"Browse##{id(account)}_browse"):
                    selected_exe = select_gw_exe()
                    if selected_exe:
                        account.gw_path = selected_exe
                        team_manager.save_to_json(os.getcwd(), config_file)
                        changed = True
                if imgui.is_item_hovered():
                    imgui.set_tooltip("Path to Gw.exe (required).")

                # Checkboxes (Reordered to put "Run As Admin" first with color on the checkbox label)
                if account.run_as_admin:
                    imgui.push_style_color(imgui.Col_.text, (1.0, 0.0, 0.0, 1.0))  # Bright red when selected
                else:
                    imgui.push_style_color(imgui.Col_.text, (1.0, 0.5, 0.5, 1.0))  # Light red when unselected
                admin_changed, account.run_as_admin = imgui.checkbox(
                    "Run As Admin##{id(account)}_admin", account.run_as_admin
                )
                imgui.pop_style_color()
                if admin_changed:
                    team_manager.save_to_json(os.getcwd(), config_file)
                    changed = True
                if imgui.is_item_hovered():
                    imgui.set_tooltip("Run Guild Wars with administrative privileges.")

                py4gw_changed, account.inject_py4gw = imgui.checkbox(
                    f"Inject Py4GW##{id(account)}_py4gw", account.inject_py4gw
                )
                if py4gw_changed:
                    team_manager.save_to_json(os.getcwd(), config_file)
                    changed = True

                bb_changed, account.inject_blackbox = imgui.checkbox(
                    f"Inject Blackbox##{id(account)}_bb", account.inject_blackbox
                )
                if bb_changed:
                    team_manager.save_to_json(os.getcwd(), config_file)
                    changed = True
                if imgui.is_item_hovered():
                    imgui.set_tooltip(
                        "Inject the Blackbox DLL for additional functionality."
                    )

                gmod_changed, account.gmod_enabled = imgui.checkbox(
                    f"Inject gMod##{id(account)}_gmod", account.gmod_enabled
                )
                if gmod_changed:
                    team_manager.save_to_json(os.getcwd(), config_file)
                    changed = True
                    if not account.gmod_enabled:
                        # Mark for cleanup on save instead of immediate removal
                        account.mark_changed()

                # Mods
                if imgui.button(f"Add Mod##{id(account)}_addmod"):
                    root = tk.Tk()
                    root.withdraw()
                    mod_file = filedialog.askopenfilename(
                        title="Select .tpf Mod", filetypes=[("TPF Files", "*.tpf")]
                    )
                    root.destroy()
                    if mod_file and mod_file not in account.mod_list:
                        account.mod_list.append(mod_file)
                        team_manager.save_to_json(os.getcwd(), config_file)
                        changed = True
                for j, mod in enumerate(account.mod_list[:]):
                    imgui.text(f" - {mod}")
                    imgui.same_line()
                    if imgui.button(f"Remove##{id(account)}_{j}_remove"):
                        account.mod_list.pop(j)
                        team_manager.save_to_json(os.getcwd(), config_file)
                        changed = True
                imgui.separator()

                # Update has_changes in the Account object if any change occurred
                if changed:
                    account.mark_changed()

                # Save and Delete Buttons
                imgui.push_style_color(
                    imgui.Col_.button,
                    (
                        (0.5, 0.5, 0.5, 1.0)
                        if not account.has_changes
                        else (0.2, 0.6, 0.2, 1.0)
                    ),
                )
                if imgui.button(f"Save##{id(account)}_save") and account.has_changes:
                    if not account.gw_path:
                        log_history.append(
                            f"No GW path specified for {account.character_name}."
                        )
                    elif not os.path.exists(account.gw_path):
                        log_history.append(
                            f"GW path does not exist for {account.character_name}: {account.gw_path}"
                        )
                    else:
                        gw_dir = os.path.dirname(os.path.normpath(account.gw_path))
                        modlist_path = os.path.join(gw_dir, "modlist.txt")
                        os.makedirs(os.path.dirname(modlist_path), exist_ok=True)
                        with open(modlist_path, "w") as f:
                            f.write(
                                "\n".join(account.mod_list) if account.mod_list else ""
                            )
                        log_history.append(f"Wrote modlist.txt to {modlist_path}")
                        # Clean up d3d9.dll if gMod is disabled
                        d3d9_path = os.path.join(gw_dir, "d3d9.dll")
                        if not account.gmod_enabled and os.path.exists(d3d9_path):
                            try:
                                os.remove(d3d9_path)
                                log_history.append(
                                    f"Removed {d3d9_path} as gMod is disabled"
                                )
                            except Exception as e:
                                log_history.append(
                                    f"Failed to remove {d3d9_path}: {str(e)}"
                                )
                        team_manager.save_to_json(os.getcwd(), config_file)
                        log_history.append(f"Saved account: {account.character_name}")
                        account.clear_changes()
                imgui.pop_style_color()
                imgui.same_line()
                imgui.push_style_color(imgui.Col_.button, (0.6, 0.2, 0.2, 1.0))
                if imgui.button(f"Delete##{id(account)}_delete"):
                    selected_team.accounts.pop(i)
                    team_manager.save_to_json(os.getcwd(), config_file)
                    log_history.append(f"Deleted account: {account.character_name}")
                imgui.pop_style_color()

        imgui.end_child()


def select_folder():
    """Open a dialog to select a folder path for Guild Wars installation."""
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Select Guild Wars Path")
    root.destroy()
    return folder_path


def select_gw_exe():
    """Open a dialog to select the Guild Wars executable (Gw.exe)."""
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Guild Wars Executable",
        filetypes=[("Executable Files", "*.exe")],
        initialfile="Gw.exe",
    )
    root.destroy()
    return file_path


def select_dll(name):
    """Open a dialog to select a DLL file."""
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select DLL", filetypes=[("Dynamic Libraries", "*.dll")], initialfile=name
    )
    root.destroy()
    return file_path


def select_python_script():
    """Open a dialog to select a Python script file."""
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Python Script", filetypes=[("Python Scripts", "*.py")]
    )
    root.destroy()
    return file_path


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
    "gmod_enabled": False,
}


def main():
    """Run the Py4GW Launcher application with a docking-based ImGui interface."""
    try:
        runner_params = hello_imgui.RunnerParams()
        runner_params.app_window_params.window_title = "Py4GW Launcher v1.0"
        runner_params.app_window_params.window_geometry.size = (1280, 720)
        runner_params.imgui_window_params.default_imgui_window_type = (
            hello_imgui.DefaultImGuiWindowType.provide_full_screen_dock_space
        )
        runner_params.docking_params.docking_splits = create_docking_splits()
        runner_params.docking_params.dockable_windows = create_dockable_windows()
        hello_imgui.run(runner_params)
    except Exception as e:
        log_history.append(f"Application error: {str(e)}")
        log_to_file()
        raise


if __name__ == "__main__":
    main()