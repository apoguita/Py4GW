import subprocess
import sys
import ctypes
from ctypes import wintypes

# Dependencies required for the script
DEPENDENCIES = ["pywin32", "psutil"]


def ensure_dependencies():
    """
    Ensure all required dependencies are installed.
    """
    print("Checking dependencies...")
    for package in DEPENDENCIES:
        try:
            __import__(package)
            print(f"Dependency '{package}' is already installed.")
        except ImportError:
            print(f"Dependency '{package}' is missing. Installing...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", package],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                print(f"Dependency '{package}' installed successfully.")
            except subprocess.CalledProcessError:
                print(f"Failed to install dependency '{package}'. Please install it manually.")
                sys.exit(1)
    print("All dependencies are satisfied.\n")


def find_gw_process():
    """
    Find the Guild Wars process by its window class name.
    """
    from win32gui import FindWindow
    from win32process import GetWindowThreadProcessId

    print("Looking for Guild Wars process...")
    window_class_name = "ArenaNet_Dx_Window_Class"
    hwnd = FindWindow(window_class_name, None)
    if hwnd == 0:
        return None, None

    _, pid = GetWindowThreadProcessId(hwnd)
    return hwnd, pid


def open_process(pid):
    """
    Open the Guild Wars process.
    """
    from win32api import OpenProcess
    from win32con import PROCESS_ALL_ACCESS

    return OpenProcess(PROCESS_ALL_ACCESS, False, pid)


def read_process_memory(process_handle, address, size):
    """
    Read memory from the Guild Wars process.
    """
    buffer = ctypes.create_string_buffer(size)
    bytes_read = wintypes.SIZE_T(0)
    success = ctypes.windll.kernel32.ReadProcessMemory(
        ctypes.c_void_p(process_handle),
        ctypes.c_void_p(address),
        buffer,
        size,
        ctypes.byref(bytes_read),
    )
    if not success:
        raise RuntimeError(f"Failed to read memory at address {hex(address)}. Error code: {ctypes.GetLastError()}")
    return buffer.raw


def virtual_query(process_handle, base_address):
    """
    Query memory region information using VirtualQueryEx.
    """
    class MEMORY_BASIC_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BaseAddress", ctypes.c_void_p),
            ("AllocationBase", ctypes.c_void_p),
            ("AllocationProtect", wintypes.DWORD),
            ("RegionSize", ctypes.c_size_t),
            ("State", wintypes.DWORD),
            ("Protect", wintypes.DWORD),
            ("Type", wintypes.DWORD),
        ]

    mbi = MEMORY_BASIC_INFORMATION()
    mbi_size = ctypes.sizeof(mbi)
    result = ctypes.windll.kernel32.VirtualQueryEx(
        ctypes.c_void_p(process_handle),
        ctypes.c_void_p(base_address),
        ctypes.byref(mbi),
        mbi_size,
    )
    if result == 0:
        raise RuntimeError(f"VirtualQueryEx failed at address {hex(base_address)}.")
    return mbi


def get_module_info(process_handle):
    """
    Retrieve base address and size of the Guild Wars executable module.
    """
    class MODULEINFO(ctypes.Structure):
        _fields_ = [
            ("lpBaseOfDll", wintypes.LPVOID),
            ("SizeOfImage", wintypes.DWORD),
            ("EntryPoint", wintypes.LPVOID),
        ]

    psapi = ctypes.WinDLL("psapi")
    module_info = MODULEINFO()
    h_modules = (wintypes.HMODULE * 1024)()
    needed = wintypes.DWORD()

    raw_handle = ctypes.c_void_p(process_handle.handle)

    if not psapi.EnumProcessModules(
        raw_handle,
        ctypes.byref(h_modules),
        ctypes.sizeof(h_modules),
        ctypes.byref(needed),
    ):
        raise RuntimeError(f"Failed to enumerate process modules. Error code: {ctypes.GetLastError()}")

    for module in h_modules[: int(needed.value / ctypes.sizeof(wintypes.HMODULE))]:
        module_name = ctypes.create_string_buffer(256)
        if psapi.GetModuleBaseNameA(raw_handle, module, module_name, ctypes.sizeof(module_name)):
            if b"Gw.exe" in module_name.value:
                if psapi.GetModuleInformation(
                    raw_handle, module, ctypes.byref(module_info), ctypes.sizeof(module_info)
                ):
                    return module_info.lpBaseOfDll, module_info.SizeOfImage

    raise RuntimeError("Guild Wars module not found.")


def scan_for_charname(process_handle, module_base, module_size):
    """
    Scan the memory for the character name offset based on a specific pattern.
    """
    char_name_pattern = b"\x8B\xF8\x6A\x03\x68\x0F\x00\x00\xC0\x8B\xCF\xE8"
    print("Scanning memory for character name offset...")
    current_address = module_base

    while current_address < module_base + module_size:
        mbi = virtual_query(process_handle, current_address)

        if mbi.State == 0x1000 and mbi.Protect in (0x04, 0x40):  # MEM_COMMIT, READ/WRITE/EXEC
            buffer = read_process_memory(process_handle, mbi.BaseAddress, mbi.RegionSize)

            # Search for the pattern
            offset = buffer.find(char_name_pattern)
            if offset != -1:
                match_address = mbi.BaseAddress + offset
                charname_offset_address = match_address - 0x42

                raw_offset = read_process_memory(process_handle, charname_offset_address, 4)
                return int.from_bytes(raw_offset, byteorder="little")

        current_address += mbi.RegionSize

    raise RuntimeError("Pattern not found in memory.")


def get_character_name(process_handle, base_address, charname_offset):
    """
    Retrieve the character name.
    """
    charname_address = base_address + charname_offset
    raw_data = read_process_memory(process_handle, charname_address, 60)  # 60 bytes for wchar[30]
    return raw_data.decode("utf-16", errors="ignore").strip("\x00")


def main():
    print("Initializing Py4GW Injector...")
    ensure_dependencies()

    hwnd, pid = find_gw_process()
    if not hwnd or not pid:
        print("Guild Wars process not found.")
        return

    print(f"Found Guild Wars process. PID: {pid}")
    process_handle = open_process(pid)
    if not process_handle:
        print("Failed to open Guild Wars process.")
        return

    try:
        print("Retrieving Guild Wars module information...")
        base_address, module_size = get_module_info(process_handle)
        print(f"Module Base Address: {hex(base_address)}, Size: {module_size}")

        charname_offset = scan_for_charname(process_handle, base_address, module_size)
        print(f"Character Name Offset: {hex(charname_offset)}")

        char_name = get_character_name(process_handle, base_address, charname_offset)
        print(f"Character Name: {char_name}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        from win32api import CloseHandle
        CloseHandle(process_handle)


if __name__ == "__main__":
    main()
