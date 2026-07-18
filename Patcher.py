import ctypes
import ctypes.wintypes
from typing import List, Optional

PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_QUERY_INFORMATION = 0x0400
MAX_PATH = 260  
TH32CS_SNAPPROCESS = 0x00000002

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

class Patcher:
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
            print(f"Could not open process with PID {pid}: {ctypes.GetLastError()}")
            return False

        sig_patch = bytes([0x56, 0x57, 0x68, 0x00, 0x01, 0x00, 0x00, 0x89, 0x85, 0xF4, 0xFE, 0xFF, 0xFF, 0xC7, 0x00, 0x00, 0x00, 0x00, 0x00])
        module_base = self.get_process_module_base(process_handle)
        if module_base is None:
            print("Failed to get module base")
            kernel32.CloseHandle(process_handle)
            return False
        gwdata = ctypes.create_string_buffer(0x48D000)

        bytes_read = ctypes.c_size_t()
        if not kernel32.ReadProcessMemory(process_handle, module_base, gwdata, 0x48D000, ctypes.byref(bytes_read)):
            print(f"Failed to read process memory: {ctypes.GetLastError()}")
            kernel32.CloseHandle(process_handle)
            return False

        idx = self.search_bytes(gwdata.raw, sig_patch)
        if idx == -1:
            print("Failed to find signature")
            kernel32.CloseHandle(process_handle)
            return False

        mcpatch_address = module_base + idx - 0x1A
        payload = bytes([0x31, 0xC0, 0x90, 0xC3])

        bytes_written = ctypes.c_size_t()
        if not kernel32.WriteProcessMemory(process_handle, mcpatch_address, payload, len(payload), ctypes.byref(bytes_written)):
            print(f"Failed to write process memory: {ctypes.GetLastError()}")
            kernel32.CloseHandle(process_handle)
            return False
        
        print(f"Patched at address: {hex(mcpatch_address)}")
        kernel32.CloseHandle(process_handle)
        return True

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
            print(f"Failed to create process: {ctypes.GetLastError()}")
            return None

        pid = process_info.dwProcessId

        if self.patch(pid):
            print("Multiclient patch applied successfully.")
        else:
            print("Failed to apply multiclient patch.")
            kernel32.TerminateProcess(process_info.hProcess, 0)
            kernel32.CloseHandle(process_info.hProcess)
            kernel32.CloseHandle(process_info.hThread)
            return None
        
        if kernel32.ResumeThread(process_info.hThread) == -1:
            print(f"Failed to resume thread: {ctypes.GetLastError()}")
            kernel32.TerminateProcess(process_info.hProcess, 0)
            kernel32.CloseHandle(process_info.hProcess)
            kernel32.CloseHandle(process_info.hThread)
            return None

        print("Process resumed.")

        kernel32.CloseHandle(process_info.hProcess)
        kernel32.CloseHandle(process_info.hThread)

        return pid