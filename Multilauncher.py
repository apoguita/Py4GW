import win32gui
import win32con
import win32api
import win32process
import json
from dataclasses import dataclass, asdict
from typing import List, Optional
import os
import subprocess
import win32event
import ctypes
import logging
from datetime import datetime
import time
import psutil
from ctypes import wintypes
import threading
from Patcher import Patcher
import sys
# Add these constants
PROCESS_ALL_ACCESS = 0x1F0FFF
VIRTUAL_MEM = 0x1000 | 0x2000  # MEM_COMMIT | MEM_RESERVE
PAGE_READWRITE = 0x04
MEM_RELEASE = 0x8000

@dataclass
class Account:
    character: str = ""
    email: str = ""
    gwpath: str = ""
    password: str = ""
    extraargs: str = ""
    elevated: bool = False
    title: str = ""
    active: bool = False
    state: str = "Inactive"

class DebugWindow:
    def __init__(self, parent_hwnd):
        # Register window class for debug window
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self.debug_wnd_proc
        wc.lpszClassName = "GWDebugWindow"
        wc.hbrBackground = win32gui.GetStockObject(win32con.WHITE_BRUSH)
        win32gui.RegisterClass(wc)
        
        # Create debug window
        self.hwnd = win32gui.CreateWindow(
            wc.lpszClassName,
            "Debug Log",
            win32con.WS_OVERLAPPEDWINDOW | win32con.WS_VISIBLE,
            100, 100, 600, 400,
            parent_hwnd, 0, 0, None
        )
        
        # Create edit control for log display
        self.edit_hwnd = win32gui.CreateWindow(
            "EDIT", "",
            win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.WS_VSCROLL |
            win32con.ES_MULTILINE | win32con.ES_AUTOVSCROLL | win32con.ES_READONLY,
            0, 0, 600, 400,
            self.hwnd, 0, 0, None
        )
        
        self.log_messages = []

    def debug_wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_SIZE:
            width = win32api.LOWORD(lparam)
            height = win32api.HIWORD(lparam)
            win32gui.MoveWindow(self.edit_hwnd, 0, 0, width, height, True)
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        # Single line break between entries
        log_entry = f"\r\n[{timestamp}] {message}\r\n"
        self.log_messages.append(log_entry)
        
        # Join all messages with explicit line breaks
        full_log = "".join(self.log_messages)
        
        # Set text and force update
        win32gui.SendMessage(self.edit_hwnd, win32con.WM_SETTEXT, 0, full_log)
        
        # Force scroll to bottom
        length = win32gui.SendMessage(self.edit_hwnd, win32con.WM_GETTEXTLENGTH, 0, 0)
        win32gui.SendMessage(self.edit_hwnd, win32con.EM_SETSEL, length, length)
        win32gui.SendMessage(self.edit_hwnd, win32con.EM_LINESCROLL, 0, 0xffff)
        win32gui.SendMessage(self.edit_hwnd, win32con.EM_SCROLLCARET, 0, 0)

class GWLauncher:
    def __init__(self):
        # Set up file paths first
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle (compiled executable)
            self.app_directory = os.path.dirname(sys.executable)
        else:
            # If the application is run from a Python interpreter
            self.app_directory = os.path.dirname(os.path.abspath(__file__))
        
        self.accounts_file = os.path.join(self.app_directory, "accounts.json")
        
        # Add menu IDs
        self.ID_LAUNCH = 1001
        self.ID_ADD = 1002
        self.ID_EDIT = 1003
        self.ID_DELETE = 1004
        self.ID_SELECT_DLL = 1005
        self.ID_TOGGLE_DLL = 1006
        self.ID_SELECT_TOOLBOX = 1007  # New ID for toolbox selection
        self.ID_TOGGLE_TOOLBOX = 1008  # New ID for toolbox toggle
        
        # Track which account was right-clicked
        self.selected_account: Optional[Account] = None
        
        # Initialize accounts list
        self.accounts: List[Account] = []
        
        # Add DLL settings
        self.dll_path = self.load_dll_path()
        self.dll_enabled = self.load_dll_enabled()
        
        # Add Toolbox settings
        self.toolbox_path = self.load_toolbox_path()
        self.toolbox_enabled = self.load_toolbox_enabled()
        
        self.active_pids = []
        
        # Register main window class
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self.wnd_proc
        wc.lpszClassName = "GWLauncherClass"
        wc.hbrBackground = win32gui.GetStockObject(win32con.WHITE_BRUSH)
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW
        
        try:
            win32gui.UnregisterClass("GWLauncherClass", None)
        except:
            pass
        
        win32gui.RegisterClass(wc)
        
        # Create main window
        style = win32con.WS_OVERLAPPEDWINDOW | win32con.WS_CLIPCHILDREN
        self.hwnd = win32gui.CreateWindow(
            wc.lpszClassName,
            "GW Launcher",
            style,
            win32con.CW_USEDEFAULT,
            win32con.CW_USEDEFAULT,
            500, 600,
            0, 0,
            0, None
        )
        
        # Create debug window BEFORE any logging attempts
        self.debug_window = DebugWindow(self.hwnd)
        
        # Now we can start logging
        self.debug_window.log("GWLauncher initialized")
        self.debug_window.log(f"Application directory: {self.app_directory}")
        self.debug_window.log(f"Accounts file location: {self.accounts_file}")
        
        # Load accounts after debug window is created
        self.load_accounts()
        
        # Show main window
        win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
        win32gui.UpdateWindow(self.hwnd)

    def wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
            
        elif msg == win32con.WM_ERASEBKGND:
            return 1  # Prevent background erasing
            
        elif msg == win32con.WM_PAINT:
            self.paint()
            return 0
            
        elif msg == win32con.WM_LBUTTONDOWN:
            x = win32api.LOWORD(lparam)
            y = win32api.HIWORD(lparam)
            self.handle_click(x, y)
            return 0
            
        elif msg == win32con.WM_RBUTTONUP:
            x = win32api.LOWORD(lparam)
            y = win32api.HIWORD(lparam)
            self.show_context_menu(x, y)
            return 0
            
        elif msg == win32con.WM_COMMAND:
            self.handle_command(wparam)
            return 0
            
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def paint(self):
        hdc, ps = win32gui.BeginPaint(self.hwnd)
        rect = win32gui.GetClientRect(self.hwnd)
        
        try:
            memdc = win32gui.CreateCompatibleDC(hdc)
            bitmap = win32gui.CreateCompatibleBitmap(hdc, rect[2], rect[3])
            old_bitmap = win32gui.SelectObject(memdc, bitmap)
            
            try:
                # Store original text color and background mode
                old_text_color = win32gui.GetTextColor(memdc)
                old_bk_mode = win32gui.GetBkMode(memdc)
                
                # Clear background to black
                black_brush = win32gui.CreateSolidBrush(win32api.RGB(0, 0, 0))
                win32gui.FillRect(memdc, rect, black_brush)
                win32gui.DeleteObject(black_brush)
                
                # Draw accounts list with buttons
                y = 10
                for account in self.accounts:
                    # Set text color to white for better contrast on black background
                    win32gui.SetTextColor(memdc, win32api.RGB(255, 255, 255))
                    win32gui.SetBkMode(memdc, win32con.TRANSPARENT)
                    
                    # Account text
                    text = f"{account.title or account.character} - {account.state}"
                    win32gui.DrawText(
                        memdc, text, -1,
                        (10, y, rect[2]-305, y+25),
                        win32con.DT_LEFT | win32con.DT_VCENTER | win32con.DT_SINGLELINE | win32con.DT_END_ELLIPSIS
                    )
                    
                    # Draw buttons
                    button_width = 80
                    button_spacing = 10
                    button_x = rect[2] - (button_width * 3 + button_spacing * 2) - 10
                    
                    # Launch button - Green
                    green_brush = win32gui.CreateSolidBrush(0x00008000)  # RGB(0, 128, 0) - Green
                    old_brush = win32gui.SelectObject(memdc, green_brush)
                    win32gui.Rectangle(memdc, button_x, y, button_x + button_width, y + 25)
                    win32gui.SelectObject(memdc, old_brush)
                    win32gui.DeleteObject(green_brush)
                    
                    # Set text color to white for Launch button
                    win32gui.SetTextColor(memdc, 0x00FFFFFF)
                    win32gui.DrawText(memdc, "Launch", -1,
                        (button_x, y, button_x + button_width, y + 25),
                        win32con.DT_CENTER | win32con.DT_VCENTER | win32con.DT_SINGLELINE
                    )
                    
                    # Edit button - Purple
                    button_x += button_width + button_spacing
                    purple_brush = win32gui.CreateSolidBrush(win32api.RGB(128, 0, 128))  # Purple
                    old_brush = win32gui.SelectObject(memdc, purple_brush)
                    win32gui.Rectangle(memdc, button_x, y, button_x + button_width, y + 25)
                    win32gui.SelectObject(memdc, old_brush)
                    win32gui.DeleteObject(purple_brush)
                    
                    # White text for Edit button
                    win32gui.SetTextColor(memdc, 0x00FFFFFF)
                    win32gui.DrawText(memdc, "Edit", -1,
                        (button_x, y, button_x + button_width, y + 25),
                        win32con.DT_CENTER | win32con.DT_VCENTER | win32con.DT_SINGLELINE
                    )
                    
                    # Delete button - Red
                    button_x += button_width + button_spacing
                    red_brush = win32gui.CreateSolidBrush(0x000000FF)  # RGB(255, 0, 0) - Red
                    old_brush = win32gui.SelectObject(memdc, red_brush)
                    win32gui.Rectangle(memdc, button_x, y, button_x + button_width, y + 25)
                    win32gui.SelectObject(memdc, old_brush)
                    win32gui.DeleteObject(red_brush)
                    
                    # White text for Delete button
                    win32gui.SetBkMode(memdc, win32con.TRANSPARENT)
                    win32gui.SetTextColor(memdc, 0x00FFFFFF)
                    
                    win32gui.DrawText(memdc, "Delete", -1,
                        (button_x, y, button_x + button_width, y + 25),
                        win32con.DT_CENTER | win32con.DT_VCENTER | win32con.DT_SINGLELINE
                    )
                    
                    # Restore original text color and background mode
                    win32gui.SetTextColor(memdc, old_text_color)
                    win32gui.SetBkMode(memdc, old_bk_mode)
                    
                    y += 35
                
                # Draw bottom buttons
                bottom_y = rect[3] - 40
                button_width = 120
                
                # Add Account button - Light Green
                light_green_brush = win32gui.CreateSolidBrush(win32api.RGB(144, 238, 144))
                old_brush = win32gui.SelectObject(memdc, light_green_brush)
                win32gui.Rectangle(memdc, 10, bottom_y, 10 + button_width, bottom_y + 30)
                win32gui.SelectObject(memdc, old_brush)
                win32gui.DeleteObject(light_green_brush)
                
                # Set text properties for Add Account button
                old_bk_mode = win32gui.SetBkMode(memdc, win32con.TRANSPARENT)
                win32gui.SetTextColor(memdc, win32api.RGB(0, 0, 0))
                
                win32gui.DrawText(memdc, "Add Account", -1,
                    (10, bottom_y, 10 + button_width, bottom_y + 30),
                    win32con.DT_CENTER | win32con.DT_VCENTER | win32con.DT_SINGLELINE
                )
                
                # DLL Options button - Dark Blue
                dark_blue_brush = win32gui.CreateSolidBrush(win32api.RGB(0, 0, 139))  # Dark blue color
                old_brush = win32gui.SelectObject(memdc, dark_blue_brush)
                win32gui.Rectangle(memdc, 140, bottom_y, 140 + button_width, bottom_y + 30)
                win32gui.SelectObject(memdc, old_brush)
                win32gui.DeleteObject(dark_blue_brush)
                
                # Set text properties for DLL Options button (white text)
                win32gui.SetTextColor(memdc, win32api.RGB(255, 255, 255))
                win32gui.SetBkMode(memdc, win32con.TRANSPARENT)
                
                win32gui.DrawText(memdc, "DLL Options", -1,
                    (140, bottom_y, 140 + button_width, bottom_y + 30),
                    win32con.DT_CENTER | win32con.DT_VCENTER | win32con.DT_SINGLELINE
                )
                
                # Copy from memory DC to window DC
                win32gui.BitBlt(
                    hdc, 0, 0, rect[2], rect[3],
                    memdc, 0, 0,
                    win32con.SRCCOPY
                )
            finally:
                win32gui.SelectObject(memdc, old_bitmap)
                win32gui.DeleteObject(bitmap)
                win32gui.DeleteDC(memdc)
        finally:
            win32gui.EndPaint(self.hwnd, ps)

    def load_accounts(self):
        self.debug_window.log("Starting account load process...")
        self.debug_window.log(f"Loading from: {self.accounts_file}")
        
        try:
            if os.path.exists(self.accounts_file):
                with open(self.accounts_file, "r", encoding='utf-8') as f:
                    file_content = f.read()
                    self.debug_window.log(f"File content length: {len(file_content)} bytes")
                    if not file_content.strip():
                        self.debug_window.log("accounts.json is empty")
                        self.accounts = []
                        return
                    
                    accounts_data = json.loads(file_content)
                    self.debug_window.log(f"Parsed JSON data: {accounts_data}")
                    
                    self.accounts = []
                    for acc_data in accounts_data:
                        acc = Account(
                            character=acc_data.get('character', ''),
                            email=acc_data.get('email', ''),
                            gwpath=acc_data.get('gwpath', ''),
                            password=acc_data.get('password', ''),
                            extraargs=acc_data.get('extraargs', ''),
                            elevated=acc_data.get('elevated', False),
                            title=acc_data.get('title', ''),
                        )
                        self.accounts.append(acc)
                    
                    self.debug_window.log(f"Successfully loaded {len(self.accounts)} accounts")
            else:
                self.debug_window.log("accounts.json does not exist")
                self.accounts = []
        except FileNotFoundError:
            self.debug_window.log("FileNotFoundError while loading accounts.json")
            self.accounts = []
        except json.JSONDecodeError as e:
            self.debug_window.log(f"JSON decode error: {str(e)}")
            if os.path.exists(self.accounts_file):
                backup_path = f"{self.accounts_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(self.accounts_file, backup_path)
                self.debug_window.log(f"Corrupted file backed up to {backup_path}")
            self.accounts = []
        except Exception as e:
            self.debug_window.log(f"Unexpected error loading accounts: {str(e)}")
            self.accounts = []

    def save_accounts(self):
        self.debug_window.log("Starting account save process...")
        self.debug_window.log(f"Saving to: {self.accounts_file}")
        
        try:
            # Ensure the directory exists
            directory = os.path.dirname(self.accounts_file)
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.debug_window.log(f"Created directory: {directory}")

            # Create backup of existing file if it exists
            if os.path.exists(self.accounts_file):
                backup_path = f"{self.accounts_file}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.replace(self.accounts_file, backup_path)
                self.debug_window.log(f"Created backup at: {backup_path}")

            # Convert accounts to dictionary format
            accounts_data = []
            for account in self.accounts:
                acc_dict = {
                    'character': account.character,
                    'email': account.email,
                    'gwpath': account.gwpath,
                    'password': account.password,
                    'extraargs': account.extraargs,
                    'elevated': account.elevated,
                    'title': account.title,
                }
                accounts_data.append(acc_dict)
            
            self.debug_window.log(f"Preparing to save {len(accounts_data)} accounts")
            
            # Save to file with pretty printing
            with open(self.accounts_file, "w", encoding='utf-8') as f:
                json.dump(accounts_data, f, indent=4, ensure_ascii=False)
            
            self.debug_window.log("Accounts saved successfully")
            
            # Verify the save
            if os.path.exists(self.accounts_file):
                file_size = os.path.getsize(self.accounts_file)
                self.debug_window.log(f"Verified: File exists and is {file_size} bytes")
                
                # Try to read it back to verify integrity
                with open(self.accounts_file, "r", encoding='utf-8') as f:
                    verify_data = json.load(f)
                    self.debug_window.log(f"Verified: File contains {len(verify_data)} accounts")
            else:
                self.debug_window.log("Warning: File does not exist after save!")

        except Exception as e:
            self.debug_window.log(f"Error saving accounts: {str(e)}")
            if 'backup_path' in locals():
                try:
                    os.replace(backup_path, self.accounts_file)
                    self.debug_window.log("Restored backup after save failure")
                except Exception as restore_error:
                    self.debug_window.log(f"Failed to restore backup: {str(restore_error)}")
            raise

    def inject_dll(self, pid):
        if not self.dll_path or not os.path.exists(self.dll_path):
            self.debug_window.log("Invalid DLL path")
            return False

        self.debug_window.log(f"Starting DLL injection for PID: {pid}")
        kernel32 = ctypes.windll.kernel32
        process_handle = None
        allocated_memory = None
        thread_handle = None

        try:
            # Get process handle
            process_handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
            if not process_handle:
                self.debug_window.log(f"Failed to open process. Error: {ctypes.get_last_error()}")
                return False

            # Get LoadLibraryA address
            loadlib_addr = kernel32.GetProcAddress(
                kernel32._handle,
                b"LoadLibraryA"
            )
            if not loadlib_addr:
                self.debug_window.log("Failed to get LoadLibraryA address")
                return False

            # Prepare DLL path
            dll_path_bytes = self.dll_path.encode('ascii') + b'\0'
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
                self.debug_window.log("Failed to allocate memory")
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
                self.debug_window.log("Failed to write to process memory")
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
                self.debug_window.log("Failed to create remote thread")
                return False

            # Wait for thread completion
            kernel32.WaitForSingleObject(thread_handle, 5000)  # 5 second timeout

            # Get thread exit code
            exit_code = ctypes.c_ulong(0)
            if kernel32.GetExitCodeThread(thread_handle, ctypes.byref(exit_code)):
                self.debug_window.log(f"Injection completed with exit code: {exit_code.value}")
                return exit_code.value != 0
            return False

        except Exception as e:
            self.debug_window.log(f"DLL injection failed with error: {str(e)}")
            return False

        finally:
            # Cleanup
            if thread_handle:
                kernel32.CloseHandle(thread_handle)
            if allocated_memory and process_handle:
                kernel32.VirtualFreeEx(process_handle, allocated_memory, 0, MEM_RELEASE)
            if process_handle:
                kernel32.CloseHandle(process_handle)

    def inject_toolbox(self, pid):
        """Inject GWToolboxdll.dll into the process"""
        
        if not self.toolbox_path or not os.path.exists(self.toolbox_path):
            self.debug_window.log("GWToolbox DLL path not valid")
            return False

        self.debug_window.log(f"Injecting BlackBox from: {self.toolbox_path}")
        
        # Store original DLL path
        original_dll_path = self.dll_path
        
        try:
            # Temporarily set dll_path to toolbox path
            self.dll_path = self.toolbox_path
            # Use existing inject_dll method
            result = self.inject_dll(pid)
            self.debug_window.log("GWToolbox injection " + ("successful" if result else "failed"))
            return result
        finally:
            # Restore original DLL path
            self.dll_path = original_dll_path

    def wait_for_gw_window(self, pid, timeout=30):
        """Wait for GW window to be created and fully loaded"""
        self.debug_window.log(f"Waiting for GW window (PID: {pid})")
        start_time = time.time()
        found_windows = []
        
        def enum_windows_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                    if window_pid == pid:
                        title = win32gui.GetWindowText(hwnd)
                        self.debug_window.log(f"Found window with title: '{title}' for PID: {pid}")
                        # Accept any window from the process initially
                        found_windows.append(hwnd)
                except Exception as e:
                    self.debug_window.log(f"Error in callback: {str(e)}")
            return True

        while time.time() - start_time < timeout:
            try:
                process = psutil.Process(pid)
                if process.status() != psutil.STATUS_RUNNING:
                    self.debug_window.log(f"Process {pid} is not running")
                    return False

                # Clear previous findings
                found_windows.clear()
                win32gui.EnumWindows(enum_windows_callback, None)
                
                if found_windows:
                    self.debug_window.log(f"Found {len(found_windows)} windows for process {pid}")
                    # Return True if we found any window from the process
                    return True
                
            except psutil.NoSuchProcess:
                self.debug_window.log(f"Process {pid} no longer exists")
                return False
            except Exception as e:
                self.debug_window.log(f"Error while waiting for GW window: {str(e)}")
                return False
                
            time.sleep(0.5)
            
            # Add progress indicator every 5 seconds
            elapsed = time.time() - start_time
            if elapsed % 5 < 0.5:
                self.debug_window.log(f"Still waiting... ({int(elapsed)}s)")
                # List all windows for the process
                try:
                    process = psutil.Process(pid)
                    self.debug_window.log(f"Process status: {process.status()}")
                    self.debug_window.log(f"Process command line: {process.cmdline()}")
                except Exception as e:
                    self.debug_window.log(f"Error getting process info: {str(e)}")
        
        self.debug_window.log(f"Timeout waiting for window of process {pid}")
        return False

    def is_process_running(self, pid):
        try:
            process = psutil.Process(pid)
            return process.status() == psutil.STATUS_RUNNING
        except psutil.NoSuchProcess:
            return False

    def attempt_dll_injection(self, pid, delay=0, dll_type="custom"):

        if delay > 0:
            self.debug_window.log(f"Waiting {delay} seconds before injecting {dll_type} DLL...")
            time.sleep(delay)
        
        if not self.is_process_running(pid):
            self.debug_window.log(f"Process no longer running, skipping {dll_type} DLL injection")
            return False

        if dll_type == "toolbox" and self.toolbox_enabled:
            self.debug_window.log("Attempting GWToolboxdll.dll injection...")
            return self.inject_toolbox(pid)
        elif dll_type == "custom" and self.dll_enabled:
            self.debug_window.log("Attempting configured DLL injection...")
            return self.inject_dll(pid)

        self.debug_window.log(f"Skipping {dll_type} DLL injection (not enabled).")
        return False

    def start_injection_thread(self, pid):
            def injection_thread():
                try:
                    if self.wait_for_gw_window(pid):
                        self.debug_window.log("GW window found, waiting for initialization...")
                        time.sleep(5)

                        if self.toolbox_enabled:
                            if self.attempt_dll_injection(pid, dll_type="toolbox"):
                                self.debug_window.log("GWToolboxdll.dll injection successful")
                            else:
                                self.debug_window.log("GWToolboxdll.dll injection failed")

                        custom_dll_delay = 30 if self.toolbox_enabled else 0 
                        
                        if self.dll_enabled:
                            if self.attempt_dll_injection(pid, delay=custom_dll_delay, dll_type="custom"):
                                self.debug_window.log("Custom DLL injection successful")
                            else:
                                self.debug_window.log("Custom DLL injection failed")
                    else:
                        self.debug_window.log("Failed to detect GW window")
                except Exception as e:
                    self.debug_window.log(f"Error in injection thread: {str(e)}")

            threading.Thread(target=injection_thread, daemon=True).start()
            
    def update_account_state(self, account, state):
        account.state = state
        win32gui.InvalidateRect(self.hwnd, None, True)     
  
    def launch_gw(self, account: Account):
        patcher = Patcher()
        try:
            pid = patcher.launch_and_patch(
                account.gwpath,
                account.email,
                account.password,
                account.character,
                account.extraargs,
                account.elevated
            )

            if pid is None:
                self.debug_window.log("Failed to launch or patch Guild Wars.")
                self.update_account_state(account, "Launch Failed")
                return

            self.debug_window.log(f"Launched and patched GW with PID: {pid}")
            self.active_pids.append((account, pid))
            
            if self.dll_enabled or self.toolbox_enabled:
                self.start_injection_thread(pid)

            self.update_account_state(account, "Active")
            threading.Thread(target=self.monitor_game_process, args=(account, pid), daemon=True).start()
        except Exception as e:
            self.debug_window.log(f"Error launching GW: {str(e)}")
            self.update_account_state(account, "Launch Failed")

    def monitor_game_process(self, account, pid):
        while self.is_process_running(pid): 
            time.sleep(1)  

        self.debug_window.log(f"Game with PID {pid} (account: {account.character}) has closed.")
        self.update_account_state(account, "Inactive")

        for acc, p in self.active_pids:
            if acc == account and p == pid:
                self.active_pids.remove((acc, p))
                break        
            
    def run(self):
        while True:
            try:
                msg = win32gui.PeekMessage(None, 0, 0, win32con.PM_REMOVE)
                if msg[1] == win32con.WM_QUIT:
                    break
                win32gui.TranslateMessage(msg[1])
                win32gui.DispatchMessage(msg[1])
            except:
                win32gui.PumpWaitingMessages()

    def handle_click(self, x, y):
        rect = win32gui.GetClientRect(self.hwnd)
        width = rect[2]
        
        # Check if click is on bottom buttons
        bottom_y = rect[3] - 40
        if bottom_y <= y <= bottom_y + 30:
            if 10 <= x <= 130:  # Add Account button
                self.debug_window.log("Add Account button clicked")
                self.show_account_dialog()
                return
            elif 140 <= x <= 260:  # DLL Options button
                self.debug_window.log("DLL Options button clicked")
                self.show_dll_options()
                return
        
        # Check if click is on account buttons
        account_idx = (y - 10) // 35
        if 0 <= account_idx < len(self.accounts):
            button_width = 80
            button_spacing = 10
            button_x = width - (button_width * 3 + button_spacing * 2) - 10
            
            if button_x <= x <= button_x + button_width:  # Launch button
                self.debug_window.log(f"Launch button clicked for account {account_idx}")
                self.launch_gw(self.accounts[account_idx])
            elif button_x + button_width + button_spacing <= x <= button_x + button_width * 2 + button_spacing:  # Edit button
                self.debug_window.log(f"Edit button clicked for account {account_idx}")
                self.show_account_dialog(self.accounts[account_idx])
            elif button_x + button_width * 2 + button_spacing * 2 <= x <= button_x + button_width * 3 + button_spacing * 2:  # Delete button
                self.debug_window.log(f"Delete button clicked for account {account_idx}")
                self.accounts.remove(self.accounts[account_idx])
                self.save_accounts()
                win32gui.InvalidateRect(self.hwnd, None, True)

    def show_context_menu(self, x, y):
        # Find clicked account
        account_idx = y // 25
        self.selected_account = self.accounts[account_idx] if 0 <= account_idx < len(self.accounts) else None
        
        # Create popup menu
        menu = win32gui.CreatePopupMenu()
        
        if self.selected_account:
            win32gui.AppendMenu(menu, win32con.MF_STRING, self.ID_LAUNCH, "Launch")
            win32gui.AppendMenu(menu, win32con.MF_STRING, self.ID_EDIT, "Edit")
            win32gui.AppendMenu(menu, win32con.MF_STRING, self.ID_DELETE, "Delete")
            win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
        
        win32gui.AppendMenu(menu, win32con.MF_STRING, self.ID_ADD, "Add Account")
        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
        
        # DLL options submenu
        dll_menu = win32gui.CreatePopupMenu()
        win32gui.AppendMenu(dll_menu, win32con.MF_STRING, self.ID_SELECT_DLL, "Select DLL")
        # Add checkmark if DLL injection is enabled
        flags = win32con.MF_STRING | (win32con.MF_CHECKED if self.dll_enabled else win32con.MF_UNCHECKED)
        win32gui.AppendMenu(dll_menu, flags, self.ID_TOGGLE_DLL, "Enable DLL Injection")
        
        win32gui.AppendMenu(menu, win32con.MF_POPUP | win32con.MF_STRING, dll_menu, "DLL Options")
        
        # Convert client coordinates to screen coordinates
        pt = win32gui.ClientToScreen(self.hwnd, (x, y))
        win32gui.TrackPopupMenu(
            menu,
            win32con.TPM_LEFTALIGN | win32con.TPM_RIGHTBUTTON,
            pt[0], pt[1], 0, self.hwnd, None
        )
        win32gui.DestroyMenu(menu)

    def handle_command(self, wparam):
        command = win32api.LOWORD(wparam)
        
        if command == self.ID_LAUNCH and self.selected_account:
            # Check for both DLLs if enabled
            dll_check_needed = False
            if self.dll_enabled and not self.dll_path:
                dll_check_needed = True
            if self.toolbox_enabled and not self.toolbox_path:
                dll_check_needed = True
                
            if dll_check_needed:
                result = ctypes.windll.user32.MessageBoxW(
                    self.hwnd,
                    "One or more DLLs are enabled but not selected. Would you like to select them now?",
                    "DLL Selection",
                    win32con.MB_YESNO | win32con.MB_ICONQUESTION
                )
                if result == win32con.IDYES:
                    self.show_dll_options()
                    return
            
            self.launch_gw(self.selected_account)
            
        elif command == self.ID_ADD:
            self.show_account_dialog()
            
        elif command == self.ID_EDIT and self.selected_account:
            self.show_account_dialog(self.selected_account)
            
        elif command == self.ID_DELETE and self.selected_account:
            self.accounts.remove(self.selected_account)
            self.save_accounts()
            win32gui.InvalidateRect(self.hwnd, None, True)
            
        elif command == self.ID_SELECT_DLL:
            self.select_dll()
            
        elif command == self.ID_TOGGLE_DLL:
            self.dll_enabled = not self.dll_enabled
            self.save_settings()
            self.debug_window.log(f"DLL injection {'enabled' if self.dll_enabled else 'disabled'}")
        
        elif command == self.ID_SELECT_TOOLBOX:
            self.select_toolbox()
            
        elif command == self.ID_TOGGLE_TOOLBOX:
            self.toolbox_enabled = not self.toolbox_enabled
            self.save_settings()
            self.debug_window.log(f"GWToolbox injection {'enabled' if self.toolbox_enabled else 'disabled'}")

    def show_account_dialog(self, account: Optional[Account] = None):
        self.debug_window.log("Opening account dialog...")
        
        # Dialog dimensions and constants
        DIALOG_WIDTH = 500
        INITIAL_HEIGHT = 450  # Initial height, will be adjusted later
        SPACING = 45
        LABEL_WIDTH = 120
        EDIT_WIDTH = 300
        BTN_WIDTH = 90
        BTN_HEIGHT = 30
        BTN_SPACING = 20
        BOTTOM_MARGIN = 50
        RIGHT_MARGIN = 30
        
        # Create dialog window
        dialog_class = "GWAccountDialog"
        
        # First try to unregister the class if it exists
        try:
            win32gui.UnregisterClass(dialog_class, None)
        except:
            pass
        
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self.dialog_proc
        wc.lpszClassName = dialog_class
        wc.hbrBackground = win32gui.GetStockObject(win32con.WHITE_BRUSH)
        
        try:
            win32gui.RegisterClass(wc)
        except Exception as e:
            self.debug_window.log(f"Error registering dialog class: {str(e)}")
            return
        
        # Center dialog
        screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        x = (screen_width - DIALOG_WIDTH) // 2
        y = (screen_height - INITIAL_HEIGHT) // 2
        
        # Create dialog window with initial height
        style = win32con.WS_POPUP | win32con.WS_CAPTION | win32con.WS_SYSMENU
        self.dialog_hwnd = win32gui.CreateWindow(
            dialog_class,
            "Add Account" if not account else "Edit Account",
            style,
            x, y, DIALOG_WIDTH, INITIAL_HEIGHT,
            self.hwnd, 0, 0, None
        )
        
        # Store editing state
        self.editing_account = account
        
        # Create controls
        self.controls = {}
        y_pos = 30  # Initial y position
        
        # Labels and text inputs
        fields = [
            ("character", "Character Name:"),
            ("email", "Email:"),
            ("password", "Password:"),
            ("title", "Display Title (optional):")
        ]
        
        for field_id, label in fields:
            # Label
            win32gui.CreateWindow(
                "STATIC", label,
                win32con.WS_CHILD | win32con.WS_VISIBLE,
                30, y_pos, LABEL_WIDTH, 20,
                self.dialog_hwnd, 0, 0, None
            )
            
            # Text input
            style = win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.WS_BORDER
            if field_id == "password":
                style |= win32con.ES_PASSWORD
            
            edit_hwnd = win32gui.CreateWindow(
                "EDIT", "",
                style,
                LABEL_WIDTH + 40, y_pos, EDIT_WIDTH, 22,
                self.dialog_hwnd, 0, 0, None
            )
            
            self.controls[field_id] = edit_hwnd
            if account:
                win32gui.SetWindowText(edit_hwnd, getattr(account, field_id))
            
            y_pos += SPACING
        
        # GW Path selection
        win32gui.CreateWindow(
            "STATIC", "Guild Wars Path:",
            win32con.WS_CHILD | win32con.WS_VISIBLE,
            30, y_pos, LABEL_WIDTH, 20,
            self.dialog_hwnd, 0, 0, None
        )
        
        self.controls["gwpath"] = win32gui.CreateWindow(
            "EDIT", account.gwpath if account else "",
            win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.WS_BORDER,
            LABEL_WIDTH + 40, y_pos, EDIT_WIDTH - 80, 22,
            self.dialog_hwnd, 0, 0, None
        )
        
        # Browse button
        self.browse_btn = win32gui.CreateWindow(
            "BUTTON", "Browse",
            win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.BS_PUSHBUTTON,
            LABEL_WIDTH + 40 + EDIT_WIDTH - 70, y_pos, 70, 22,
            self.dialog_hwnd, 1001, 0, None
        )
        
        y_pos += SPACING
        
        # Extra args
        win32gui.CreateWindow(
            "STATIC", "Extra Arguments:",
            win32con.WS_CHILD | win32con.WS_VISIBLE,
            30, y_pos, LABEL_WIDTH, 20,
            self.dialog_hwnd, 0, 0, None
        )
        
        self.controls["extraargs"] = win32gui.CreateWindow(
            "EDIT", account.extraargs if account else "",
            win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.WS_BORDER,
            LABEL_WIDTH + 40, y_pos, EDIT_WIDTH, 22,
            self.dialog_hwnd, 0, 0, None
        )
        
        y_pos += SPACING
        
        # Elevated checkbox
        self.controls["elevated"] = win32gui.CreateWindow(
            "BUTTON", "Run as Administrator",
            win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.BS_AUTOCHECKBOX,
            30, y_pos, 200, 20,
            self.dialog_hwnd, 0, 0, None
        )
        
        if account and account.elevated:
            win32gui.SendMessage(self.controls["elevated"], win32con.BM_SETCHECK, 1, 0)
        
        # Calculate final positions
        button_y = y_pos + SPACING
        final_height = button_y + BTN_HEIGHT + BOTTOM_MARGIN
        
        # Resize dialog to fit all controls
        win32gui.SetWindowPos(
            self.dialog_hwnd, None,
            x, y, DIALOG_WIDTH, final_height,
            win32con.SWP_NOZORDER | win32con.SWP_NOMOVE
        )
        
        # Create OK/Cancel buttons
        self.ok_btn = win32gui.CreateWindow(
            "BUTTON", "OK",
            win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.BS_PUSHBUTTON,
            DIALOG_WIDTH - (BTN_WIDTH * 2 + BTN_SPACING + RIGHT_MARGIN), button_y,
            BTN_WIDTH, BTN_HEIGHT,
            self.dialog_hwnd, 1002, 0, None
        )
        
        self.cancel_btn = win32gui.CreateWindow(
            "BUTTON", "Cancel",
            win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.BS_PUSHBUTTON,
            DIALOG_WIDTH - (BTN_WIDTH + RIGHT_MARGIN), button_y,
            BTN_WIDTH, BTN_HEIGHT,
            self.dialog_hwnd, 1003, 0, None
        )
        
        self.debug_window.log("Account dialog created and shown")
        # Show dialog
        win32gui.ShowWindow(self.dialog_hwnd, win32con.SW_SHOW)

    def dialog_proc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_COMMAND:
            id = win32api.LOWORD(wparam)
            
            if id == 1001:  # Browse button
                flags = win32con.OFN_FILEMUSTEXIST | win32con.OFN_PATHMUSTEXIST
                filter = "Executable files (*.exe)\0*.exe\0All files (*.*)\0*.*\0"
                
                try:
                    filename = win32gui.GetOpenFileNameW(
                        Filter=filter,
                        Title="Select Guild Wars Client",
                        Flags=flags
                    )[0]
                    win32gui.SetWindowText(self.controls["gwpath"], filename)
                except:
                    pass
                    
            elif id == 1002:  # OK button
                self.save_dialog_data()
                win32gui.DestroyWindow(hwnd)
                
            elif id == 1003:  # Cancel button
                win32gui.DestroyWindow(hwnd)
                
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def save_dialog_data(self):
        self.debug_window.log("Starting to save dialog data...")
        
        # Get values from controls
        data = {}
        for field, hwnd in self.controls.items():
            if field == "elevated":
                data[field] = bool(win32gui.SendMessage(hwnd, win32con.BM_GETCHECK, 0, 0))
            else:
                data[field] = win32gui.GetWindowText(hwnd)
        
        self.debug_window.log(f"Collected dialog data: {data}")
        
        # Validate required fields
        required_fields = ["character", "email", "password", "gwpath"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            message = "Please fill in the following required fields:\n" + "\n".join(missing_fields)
            self.debug_window.log(f"Validation failed - missing fields: {missing_fields}")
            ctypes.windll.user32.MessageBoxW(
                self.dialog_hwnd,
                message,
                "Missing Information",
                win32con.MB_OK | win32con.MB_ICONWARNING
            )
            return
        
        # Validate GW path exists
        if not os.path.exists(data["gwpath"]):
            self.debug_window.log(f"Invalid GW path: {data['gwpath']}")
            ctypes.windll.user32.MessageBoxW(
                self.dialog_hwnd,
                "The specified Guild Wars path does not exist.",
                "Invalid Path",
                win32con.MB_OK | win32con.MB_ICONWARNING
            )
            return

        if self.editing_account:
            self.debug_window.log("Updating existing account")
            # Update existing account
            for key, value in data.items():
                setattr(self.editing_account, key, value)
        else:
            self.debug_window.log("Creating new account")
            # Create new account
            new_account = Account(**data)
            self.accounts.append(new_account)
        
        try:
            self.save_accounts()
            self.debug_window.log("Account saved successfully")
            win32gui.InvalidateRect(self.hwnd, None, True)
            win32gui.DestroyWindow(self.dialog_hwnd)
        except Exception as e:
            self.debug_window.log(f"Error while saving: {str(e)}")
            ctypes.windll.user32.MessageBoxW(
                self.dialog_hwnd,
                f"Error saving accounts: {str(e)}",
                "Save Error",
                win32con.MB_OK | win32con.MB_ICONERROR
            )

    def load_dll_path(self):
        """Load DLL path from settings file"""
        settings_file = os.path.join(self.app_directory, "settings.json")
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    return settings.get('dll_path', '')
            return ''
        except Exception as e:
            return ''

    def save_dll_path(self, path):
        """Save DLL path to settings file"""
        settings_file = os.path.join(self.app_directory, "settings.json")
        try:
            # Load existing settings if file exists
            settings = {}
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
            
            # Update DLL path
            settings['dll_path'] = path
            
            # Save all settings back to file
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            
            self.debug_window.log(f"Saved DLL path: {path}")
            return True
        except Exception as e:
            self.debug_window.log(f"Error saving DLL path: {str(e)}")
            return False

    def select_dll(self):
        """Open file dialog to select DLL"""
        try:
            flags = win32con.OFN_FILEMUSTEXIST | win32con.OFN_PATHMUSTEXIST
            filter_str = "DLL files (*.dll)\0*.dll\0All files (*.*)\0*.*\0"
            
            filename = win32gui.GetOpenFileNameW(
                Filter=filter_str,
                Title="Select Injection DLL",
                Flags=flags
            )[0]
            
            if filename:
                self.dll_path = filename
                if self.save_dll_path(filename):
                    self.debug_window.log(f"Selected and saved new DLL: {filename}")
                    return True
                else:
                    self.debug_window.log("Failed to save DLL path")
            return False
        except Exception as e:
            self.debug_window.log(f"Error selecting DLL: {str(e)}")
            return False

    def load_dll_enabled(self):
        """Load DLL enabled setting from settings file"""
        settings_file = os.path.join(self.app_directory, "settings.json")
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    return settings.get('dll_enabled', False)
            return False
        except Exception as e:
            return False

    def load_settings(self):
        """Load all settings from file"""
        settings_file = os.path.join(self.app_directory, "settings.json")
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.debug_window.log(f"Error loading settings: {str(e)}")
            return {}

    def load_toolbox_path(self):
        """Load Toolbox path from settings file"""
        settings = self.load_settings()
        return settings.get('toolbox_path', '')

    def load_toolbox_enabled(self):
        """Load Toolbox enabled setting from settings file"""
        settings = self.load_settings()
        return settings.get('toolbox_enabled', False)

    def save_settings(self):
        """Save all settings to file"""
        settings_file = os.path.join(self.app_directory, "settings.json")
        try:
            settings = {
                'dll_path': self.dll_path,
                'dll_enabled': self.dll_enabled,
                'toolbox_path': self.toolbox_path,
                'toolbox_enabled': self.toolbox_enabled
            }
            
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            
            self.debug_window.log("Settings saved successfully")
        except Exception as e:
            self.debug_window.log(f"Error saving settings: {str(e)}")

    def select_toolbox(self):
        """Open file dialog to select GWToolbox DLL"""
        try:
            flags = win32con.OFN_FILEMUSTEXIST | win32con.OFN_PATHMUSTEXIST
            filter_str = "DLL files (*.dll)\0*.dll\0All files (*.*)\0*.*\0"
            
            filename = win32gui.GetOpenFileNameW(
                Filter=filter_str,
                Title="Select GWToolbox DLL",
                Flags=flags
            )[0]
            
            if filename:
                self.toolbox_path = filename
                self.save_settings()
                self.debug_window.log(f"Selected and saved new Toolbox DLL: {filename}")
                return True
            return False
        except Exception as e:
            self.debug_window.log(f"Error selecting Toolbox DLL: {str(e)}")
            return False

    def show_dll_options(self):
        menu = win32gui.CreatePopupMenu()
        
        # Custom DLL options
        win32gui.AppendMenu(menu, win32con.MF_STRING, self.ID_SELECT_DLL, "Select Custom DLL")
        flags = win32con.MF_STRING | (win32con.MF_CHECKED if self.dll_enabled else win32con.MF_UNCHECKED)
        win32gui.AppendMenu(menu, flags, self.ID_TOGGLE_DLL, "Enable Custom DLL")
        
        # Add separator
        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
        
        # Toolbox options
        win32gui.AppendMenu(menu, win32con.MF_STRING, self.ID_SELECT_TOOLBOX, "Select GWToolbox DLL")
        flags = win32con.MF_STRING | (win32con.MF_CHECKED if self.toolbox_enabled else win32con.MF_UNCHECKED)
        win32gui.AppendMenu(menu, flags, self.ID_TOGGLE_TOOLBOX, "Enable GWToolbox")
        
        rect = win32gui.GetClientRect(self.hwnd)
        pt = win32gui.ClientToScreen(self.hwnd, (115, rect[3] - 30))
        
        win32gui.TrackPopupMenu(
            menu,
            win32con.TPM_LEFTALIGN | win32con.TPM_RIGHTBUTTON,
            pt[0], pt[1], 0, self.hwnd, None
        )
        win32gui.DestroyMenu(menu)

if __name__ == "__main__":
    launcher = GWLauncher()
    launcher.run()