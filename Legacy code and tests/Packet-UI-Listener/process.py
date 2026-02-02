# The MIT License (MIT)
#
# Copyright (c) 2019-2022 Laurent Dufresne
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from ctypes import (
    Structure,
    POINTER,
    sizeof,
    byref,
)

from contextlib import suppress

import sys
import ctypes
import struct
import functools
import traceback

BOOL        = ctypes.c_long
BYTE        = ctypes.c_byte
CHAR        = ctypes.c_char
DWORD       = ctypes.c_ulong
DWORD64     = ctypes.c_ulonglong
FLOAT       = ctypes.c_float
LONG        = ctypes.c_long
LONGLONG    = ctypes.c_longlong
LPSTR       = ctypes.c_char_p
LPVOID      = ctypes.c_void_p
LPWSTR      = ctypes.c_wchar_p
PVOID       = ctypes.c_void_p
SIZE_T      = ctypes.c_size_t
UINT        = ctypes.c_uint
ULONG       = ctypes.c_ulong
ULONG_PTR   = SIZE_T
ULONGLONG   = ctypes.c_ulonglong
WCHAR       = ctypes.c_wchar
WORD        = ctypes.c_ushort

HANDLE      = ctypes.c_void_p
HMODULE     = HANDLE
NTSTATUS    = LONG

PBOOL       = POINTER(BOOL)
PDWORD      = POINTER(DWORD)
PDWORD64    = POINTER(DWORD64)
PHANDLE     = POINTER(HANDLE)
PULONG      = POINTER(ULONG)

_PYTHON_IS_64_BITS = sys.maxsize > 2 ** 32

# standard access rights
_DELETE                             = 0x00010000
_READ_CONTROL                       = 0x00020000
_WRITE_DAC                          = 0x00040000
_WRITE_OWNER                        = 0x00080000
_SYNCHRONIZE                        = 0x00100000
_STANDARD_RIGHTS_ALL                = 0x001F0000

_PROCESS_TERMINATE                  = 0x0001
_PROCESS_CREATE_THREAD              = 0x0002
_PROCESS_SET_SESSIONID              = 0x0004
_PROCESS_VM_OPERATION               = 0x0008
_PROCESS_VM_READ                    = 0x0010
_PROCESS_VM_WRITE                   = 0x0020
_PROCESS_DUP_HANDLER                = 0x0040
_PROCESS_CREATE_PROCESS             = 0x0080
_PROCESS_SET_QUOTA                  = 0x0100
_PROCESS_SET_INFORMATION            = 0x0200
_PROCESS_QUERY_INFORMATION          = 0x0400
_PROCESS_SUSPEND_RESUME             = 0x0800
_PROCESS_QUERY_LIMITED_INFORMATION  = 0x1000
_PROCESS_SET_LIMITED_INFORMATION    = 0x2000
_PROCESS_ALL_ACCESS = _STANDARD_RIGHTS_ALL | 0xFFFF

_THREAD_TERMINATE                   = 0x0001
_THREAD_SUSPEND_RESUME              = 0x0002
_THREAD_GET_CONTEXT                 = 0x0008
_THREAD_SET_CONTEXT                 = 0x0010
_THREAD_QUERY_INFORMATION           = 0x0040
_THREAD_SET_INFORMATION             = 0x0020
_THREAD_SET_THREAD_TOKEN            = 0x0080
_THREAD_IMPERSONATE                 = 0x0100
_THREAD_DIRECT_IMPERSONATION        = 0x0200
_THREAD_SET_LIMITED_INFORMATION     = 0x0400
_THREAD_QUERY_LIMITED_INFORMATION   = 0x0800
_THREAD_RESUME                      = 0x1000
_THREAD_ALL_ACCESS = _STANDARD_RIGHTS_ALL | 0xFFFF

_TH32CS_SNAPHEAPLIST                = 0x00000001
_TH32CS_SNAPPROCESS                 = 0x00000002
_TH32CS_SNAPTHREAD                  = 0x00000004
_TH32CS_SNAPMODULE                  = 0x00000008
_TH32CS_SNAPMODULE32                = 0x00000010
_TH32CS_SNAPALL                     = 0x000000FF
_TH32CS_INHERIT                     = 0x80000000

_CONTEXT_CONTROL                    = 0x00010001 # SS:SP, CS:IP, FLAGS, BP
_CONTEXT_INTEGER                    = 0x00010002 # AX, BX, CX, DX, SI, DI
_CONTEXT_SEGMENTS                   = 0x00010004 # DS, ES, FS, GS
_CONTEXT_FLOATING_POINT             = 0x00010008 # 387 state
_CONTEXT_DEBUG_REGISTERS            = 0x00010010 # DB 0-3,6,7
_CONTEXT_EXTENDED_REGISTERS         = 0x00010020 # cpu specific extensions
_CONTEXT_FULL = _CONTEXT_CONTROL | _CONTEXT_INTEGER | _CONTEXT_SEGMENTS

_EXCEPTION_DATATYPE_MISALIGNMENT    = 0x80000002
_EXCEPTION_BREAKPOINT               = 0x80000003
_EXCEPTION_SINGLE_STEP              = 0x80000004
_EXCEPTION_ACCESS_VIOLATION         = 0xC0000005
_EXCEPTION_IN_PAGE_ERROR            = 0xC0000006
_EXCEPTION_ILLEGAL_INSTRUCTION      = 0xC000001D
_EXCEPTION_NONCONTINUABLE_EXCEPTION = 0xC0000025
_EXCEPTION_INVALID_DISPOSITION      = 0xC0000026
_EXCEPTION_ARRAY_BOUNDS_EXCEEDED    = 0xC000008C
_EXCEPTION_FLT_DENORMAL_OPERAND     = 0xC000008D
_EXCEPTION_FLT_DIVIDE_BY_ZERO       = 0xC000008E
_EXCEPTION_FLT_INEXACT_RESULT       = 0xC000008F
_EXCEPTION_FLT_INVALID_OPERATION    = 0xC0000090
_EXCEPTION_FLT_OVERFLOW             = 0xC0000091
_EXCEPTION_FLT_STACK_CHECK          = 0xC0000092
_EXCEPTION_FLT_UNDERFLOW            = 0xC0000093
_EXCEPTION_INT_DIVIDE_BY_ZERO       = 0xC0000094
_EXCEPTION_INT_OVERFLOW             = 0xC0000095
_EXCEPTION_PRIV_INSTRUCTION         = 0xC0000096
_EXCEPTION_STACK_OVERFLOW           = 0xC00000FD

_ThreadBasicInformation             = 0
_ThreadTimes                        = 1
_ThreadPriority                     = 2
_ThreadBasePriority                 = 3
_ThreadAffinityMask                 = 4
_ThreadImpersonationToken           = 5
_ThreadDescriptorTableEntry         = 6
_ThreadEnableAlignmentFaultFixup    = 7
_ThreadEventPair                    = 8
_ThreadQuerySetWin32StartAddress    = 9
_ThreadZeroTlsCell                  = 10
_ThreadPerformanceCount             = 11
_ThreadAmILastThread                = 12
_ThreadIdealProcessor               = 13
_ThreadPriorityBoost                = 14
_ThreadSetTlsArrayAddress           = 15
_ThreadIsIoPending                  = 16
_ThreadHideFromDebugger             = 17

_IGNORE                             = 0
_INFINITE                           = 0xFFFFFFFF

_WAIT_OBJECT_0                      = 0x00000000
_WAIT_ABANDONED                     = 0x00000080
_WAIT_TIMEOUT                       = 0x00000102
_WAIT_FAILED                        = 0xFFFFFFFF

_MAX_PATH                           = 260

_EXCEPTION_DEBUG_EVENT              = 1
_CREATE_THREAD_DEBUG_EVENT          = 2
_CREATE_PROCESS_DEBUG_EVENT         = 3
_EXIT_THREAD_DEBUG_EVENT            = 4
_EXIT_PROCESS_DEBUG_EVENT           = 5
_LOAD_DLL_DEBUG_EVENT               = 6
_UNLOAD_DLL_DEBUG_EVENT             = 7
_OUTPUT_DEBUG_STRING_EVENT          = 8
_RIP_EVENT                          = 9

_DBG_CONTINUE                       = 0x00010002
_DBG_EXCEPTION_NOT_HANDLED          = 0x80010001

# Make kernel32 independant of windll which may be unpredictable.
_kernel32 = ctypes.WinDLL('kernel32.dll')
_ntdll    = ctypes.WinDLL('ntdll.dll')

class _MODULEENTRY32(Structure):
    _fields_ = [('dwSize',DWORD),('th32ModuleID',DWORD),('th32ProcessID',DWORD),('GlblcntUsage',DWORD),('ProccntUsage',DWORD),('modBaseAddr',ULONG_PTR),('modBaseSize',DWORD),('hModule',HMODULE),('szModule',CHAR*256),('szExePath',CHAR*_MAX_PATH)]
    def __init__(self):
        self.dwSize = sizeof(self)

class _PROCESSENTRY32(Structure):
    _fields_ = [('dwSize',DWORD),('cntUsage',DWORD),('th32ProcessID',DWORD),('th32DefaultHeapID',ULONG_PTR),('th32ModuleID',DWORD),('cntThreads',DWORD),('th32ParentProcessID',DWORD),('pcPriClassBase',LONG),('dwFlags',DWORD),('szExeFile',CHAR*_MAX_PATH)]
    def __init__(self):
        self.dwSize = sizeof(self)

class _THREADENTRY32(Structure):
    _fields_ = [('dwSize',DWORD),('cntUsage',DWORD),('th32ThreadID',DWORD),('th32OwnerProcessID',DWORD),('tpBasePri',DWORD),('tpDeltaPri',DWORD),('dwFlags',DWORD)]
    def __init__(self):
        self.dwSize = sizeof(self)

class _MEMORY_BASIC_INFORMATION(Structure):
    _pack_   = 4
    _fields_ = [('BaseAddress',PVOID),('AllocationBase',PVOID),('AllocationProtect',DWORD),('RegionSize',SIZE_T),('State',DWORD),('Protect',DWORD),('Type',DWORD)]

class _MEMORY_BASIC_INFORMATION64(Structure):
    _pack_   = 8
    _fields_ = [('BaseAddress',ULONGLONG),('AllocationBase',ULONGLONG),('AllocationProtect',DWORD),('__alignment1',DWORD),('RegionSize',ULONGLONG),('State',DWORD),('Protect',DWORD),('Type',DWORD),('__alignment2',DWORD)]

class _WOW64_FLOATING_SAVE_AREA(Structure):
    _fields_ = [('ControlWord',DWORD),('StatusWord',DWORD),('TagWord',DWORD),('ErrorOffset',DWORD),('ErrorSelector',DWORD),('DataOffset',DWORD),('DataSelector',DWORD),('RegisterArea',BYTE*80),('Spare0',DWORD)]

class _WOW64_CONTEXT(Structure):
    _fields_ = [('ContextFlags',DWORD),('Dr0',DWORD),('Dr1',DWORD),('Dr2',DWORD),('Dr3',DWORD),('Dr6',DWORD),('Dr7',DWORD),('FloatSave',_WOW64_FLOATING_SAVE_AREA),('SegGs',DWORD),('SegFs',DWORD),('SegEs',DWORD),('SegDs',DWORD),('Edi',DWORD),('Esi',DWORD),('Ebx',DWORD),('Edx',DWORD),('Ecx',DWORD),('Eax',DWORD),('Ebp',DWORD),('Eip',DWORD),('SegCs',DWORD),('EFlags',DWORD),('Esp',DWORD),('SegSs',DWORD),('ExtendedRegisters',BYTE*512)]

class _M128A(Structure):
    _fields_ = [('Low',ULONGLONG),('High',LONGLONG)]

class _FLOATING_SAVE_AREA64(Structure):
    _fields_ = [('Header',_M128A*2),('Legacy',_M128A*8),('Xmm0',_M128A),('Xmm1',_M128A),('Xmm2',_M128A),('Xmm3',_M128A),('Xmm4',_M128A),('Xm5',_M128A),('Xmm6',_M128A),('Xmm7',_M128A),('Xmm8',_M128A),('Xmm9',_M128A),('Xmm10',_M128A),('Xmm11',_M128A),('Xmm12',_M128A),('Xmm13',_M128A),('Xmm14',_M128A),('Xmm15',_M128A)]

class _CONTEXT64(Structure):
    _fields_ = [('P1Home',DWORD64),('P2Home',DWORD64),('P3Home',DWORD64),('P4Home',DWORD64),('P5Home',DWORD64),('P6Home',DWORD64),('ContextFlags',DWORD),('MxCsr',DWORD),('SegCs',WORD),('SegDs',WORD),('SegEs',WORD),('SegFs',WORD),('SegGs',WORD),('SegSs',WORD),('EFlags',DWORD),('Dr0',DWORD64),('Dr1',DWORD64),('Dr2',DWORD64),('Dr3',DWORD64),('Dr6',DWORD64),('Dr7',DWORD64),('Rax',DWORD64),('Rcx',DWORD64),('Rdx',DWORD64),('Rbx',DWORD64),('Rsp',DWORD64),('Rbp',DWORD64),('Rsi',DWORD64),('Rdi',DWORD64),('R8',DWORD64),('R9',DWORD64),('R10',DWORD64),('R11',DWORD64),('R12',DWORD64),('R13',DWORD64),('R14',DWORD64),('R15',DWORD64),('Rip',DWORD64),('FltSave',_FLOATING_SAVE_AREA64),('VectorRegister',_M128A*26),('VectorControl',DWORD64),('DebugControl',DWORD64),('LastBranchToRip',DWORD64),('LastBranchFromRip',DWORD64),('LastExceptionToRip',DWORD64),('LastExceptionFromRip',DWORD64)]

class _EXCEPTION_DEBUG_INFO(Structure):
    EXCEPTION_MAXIMUM_PARAMETERS = 15
    _fields_ = [('ExceptionCode',DWORD),('ExceptionFlags',DWORD),('ExceptionRecord',LPVOID),('ExceptionAddress',PVOID),('NumberParameters',DWORD),('ExceptionInformation', ULONG_PTR*15),('dwFirstChance',DWORD)]

class _CREATE_THREAD_DEBUG_INFO(Structure):
    _fields_ = [('hThread',HANDLE),('lpThreadLocalBase',LPVOID),('lpStartAddress',LPVOID)]

class _CREATE_PROCESS_DEBUG_INFO(Structure):
    _fields_ = [('hFile',HANDLE),('hProcess',HANDLE),('hThread',HANDLE),('lpBaseOfImage',LPVOID),('dwDebugInfoFileOffset',DWORD),('nDebugInfoSize',DWORD),('lpThreadLocalBase',LPVOID),('lpStartAddress',LPVOID),('lpImageName',LPVOID),('fUnicode',WORD)]

class _EXIT_THREAD_DEBUG_INFO(Structure):
    _fields_ = [('dwExitCode',DWORD)]

class _EXIT_PROCESS_DEBUG_INFO(Structure):
    _fields_ = [('dwExitCode',DWORD)]

class _LOAD_DLL_DEBUG_INFO(Structure):
    _fields_ = [('hFile',HANDLE),('lpBaseOfDll',LPVOID),('dwDebugInfoFileOffset',DWORD),('nDebugInfoSize',DWORD),('lpImageName',LPVOID),('fUnicode',WORD)]

class _UNLOAD_DLL_DEBUG_INFO(Structure):
    _fields_ = [('lpBaseOfDll',LPVOID)]

class _OUTPUT_DEBUG_STRING_INFO(Structure):
    _fields_ = [('lpDebugStringData',LPSTR),('fUnicode',WORD),('nDebugStringLength',WORD)]

class _RIP_INFO(Structure):
    _fields_ = [('dwError',DWORD),('dwType',DWORD)]

class _Union(ctypes.Union):
    _fields_ = [('Exception',_EXCEPTION_DEBUG_INFO),('CreateThread',_CREATE_THREAD_DEBUG_INFO),('CreateProcessInfo',_CREATE_PROCESS_DEBUG_INFO),('ExitThread',_EXIT_THREAD_DEBUG_INFO),('ExitProcess',_EXIT_PROCESS_DEBUG_INFO),('LoadDll',_LOAD_DLL_DEBUG_INFO),('UnloadDll',_UNLOAD_DLL_DEBUG_INFO),('DebugString',_OUTPUT_DEBUG_STRING_INFO),('RipInfo',_RIP_INFO)]

class _DEBUG_EVENT(Structure):
    _fields_ = [('dwDebugEventCode',DWORD),('dwProcessId',DWORD),('dwThreadId',DWORD),('u',_Union)]

class _CLIENT_ID(Structure):
    _fields_ = [('UniqueProcess',HANDLE),('UniqueThread',HANDLE)]

class _THREAD_BASIC_INFORMATION(Structure):
    _fields_ = [('ExitStatus',DWORD),('TebBaseAddress',LPVOID),('ClientId',_CLIENT_ID),('AffinityMask',ULONG_PTR),('Priority',LONG),('BasePriority',LONG)]

if _PYTHON_IS_64_BITS:
    _CONTEXT = _CONTEXT64
else:
    _CONTEXT = _WOW64_CONTEXT

_CloseHandle                        = _kernel32.CloseHandle
_CloseHandle.argtypes               = [HANDLE]
_CloseHandle.restype                = BOOL
_DuplicateHandle                    = _kernel32.DuplicateHandle
_DuplicateHandle.argtypes           = [HANDLE, HANDLE, HANDLE, PHANDLE, DWORD, BOOL, DWORD]
_DuplicateHandle.restype            = BOOL
_GetLastError                       = _kernel32.GetLastError
_GetLastError.argtypes              = []
_GetLastError.restype               = DWORD
_WaitForSingleObject                = _kernel32.WaitForSingleObject

_OpenProcess                        = _kernel32.OpenProcess
_OpenProcess.argtypes               = [DWORD, BOOL, DWORD]
_OpenProcess.restype                = HANDLE
_TerminateProcess                   = _kernel32.TerminateProcess
_TerminateProcess.argtypes          = [HANDLE, UINT]
_TerminateProcess.restype           = BOOL

_OpenThread                         = _kernel32.OpenThread
_OpenThread.argtypes                = [DWORD, BOOL, DWORD]
_OpenThread.restype                 = HANDLE
_GetThreadId                        = _kernel32.GetThreadId
_GetThreadId.argtypes               = [HANDLE]
_GetThreadId.restype                = DWORD
_ResumeThread                       = _kernel32.ResumeThread
_ResumeThread.argtypes              = [HANDLE]
_ResumeThread.restype               = DWORD
_SuspendThread                      = _kernel32.SuspendThread
_SuspendThread.argtypes             = [HANDLE]
_SuspendThread.restype              = DWORD
_CreateRemoteThread                 = _kernel32.CreateRemoteThread
_CreateRemoteThread.argtypes        = [HANDLE, LPVOID, SIZE_T, LPVOID, LPVOID, DWORD, PDWORD]
_CreateRemoteThread.restype         = HANDLE
_TerminateThread                    = _kernel32.TerminateThread
_TerminateThread.argtypes           = [HANDLE, DWORD]
_TerminateThread.restype            = BOOL
_GetExitCodeThread                  = _kernel32.GetExitCodeThread
_GetExitCodeThread.argtypes         = [HANDLE, PDWORD]
_GetExitCodeThread.restype          = BOOL
_GetExitCodeProcess                 = _kernel32.GetExitCodeProcess
_GetExitCodeProcess.argtypes        = [HANDLE, PDWORD]
_GetExitCodeProcess.restype         = BOOL
_IsWow64Process                     = _kernel32.IsWow64Process
_IsWow64Process.argtypes            = [HANDLE, PBOOL]
_IsWow64Process.restype             = BOOL
_GetThreadContext                   = _kernel32.GetThreadContext
_GetThreadContext.argtypes          = [HANDLE, POINTER(_CONTEXT)]
_GetThreadContext.restype           = BOOL
_SetThreadContext                   = _kernel32.SetThreadContext
_SetThreadContext.argtypes          = [HANDLE, POINTER(_CONTEXT)]
_SetThreadContext.restype           = BOOL
_Wow64GetThreadContext              = _kernel32.Wow64GetThreadContext
_Wow64GetThreadContext.argtypes     = [HANDLE, POINTER(_WOW64_CONTEXT)]
_Wow64GetThreadContext.restype      = BOOL
_Wow64SetThreadContext              = _kernel32.Wow64SetThreadContext
_Wow64SetThreadContext.argtypes     = [HANDLE, POINTER(_WOW64_CONTEXT)]
_Wow64SetThreadContext.restype      = BOOL

_VirtualAllocEx                     = _kernel32.VirtualAllocEx
_VirtualAllocEx.argtypes            = [HANDLE, LPVOID, SIZE_T, DWORD, DWORD]
_VirtualAllocEx.restype             = LPVOID
_VirtualFreeEx                      = _kernel32.VirtualFreeEx
_VirtualFreeEx.argtypes             = [HANDLE, LPVOID, SIZE_T, DWORD]
_VirtualFreeEx.restype              = BOOL
_VirtualProtectEx                   = _kernel32.VirtualProtectEx
_VirtualProtectEx.argtypes          = [HANDLE, LPVOID, SIZE_T, DWORD, PDWORD]
_VirtualProtectEx.restype           = BOOL
_VirtualQueryEx                     = _kernel32.VirtualQueryEx
_VirtualQueryEx.argtypes            = [HANDLE, LPVOID, LPVOID, SIZE_T]
_VirtualQueryEx.restype             = SIZE_T
_ReadProcessMemory                  = _kernel32.ReadProcessMemory
_ReadProcessMemory.argtypes         = [HANDLE, LPVOID, LPVOID, SIZE_T, POINTER(SIZE_T)]
_ReadProcessMemory.restype          = BOOL
_WriteProcessMemory                 = _kernel32.WriteProcessMemory
_WriteProcessMemory.argtypes        = [HANDLE, LPVOID, LPVOID, SIZE_T, POINTER(SIZE_T)]
_FlushInstructionCache              = _kernel32.FlushInstructionCache
_FlushInstructionCache.argtypes     = [HANDLE, LPVOID, SIZE_T]
_FlushInstructionCache.restype      = BOOL

_CreateToolhelp32Snapshot           = _kernel32.CreateToolhelp32Snapshot
_CreateToolhelp32Snapshot.argtypes  = [DWORD, DWORD]
_CreateToolhelp32Snapshot.restype   = HANDLE
_Module32First                      = _kernel32.Module32First
_Module32First.argtypes             = [HANDLE, POINTER(_MODULEENTRY32)]
_Module32First.restype              = BOOL
_Module32Next                       = _kernel32.Module32Next
_Module32Next.argtypes              = [HANDLE, POINTER(_MODULEENTRY32)]
_Module32Next.restype               = BOOL
_Process32First                     = _kernel32.Process32First
_Process32First.argtypes            = [HANDLE, POINTER(_PROCESSENTRY32)]
_Process32First.restype             = BOOL
_Process32Next                      = _kernel32.Process32Next
_Process32Next.argtypes             = [HANDLE, POINTER(_PROCESSENTRY32)]
_Process32Next.restype              = BOOL
_Thread32First                      = _kernel32.Thread32First
_Thread32First.argtypes             = [HANDLE, POINTER(_THREADENTRY32)]
_Thread32First.restype              = BOOL
_Thread32Next                       = _kernel32.Thread32Next
_Thread32Next.argtypes              = [HANDLE, POINTER(_THREADENTRY32)]
_Thread32Next.restype               = BOOL

_DebugSetProcessKillOnExit          = _kernel32.DebugSetProcessKillOnExit
_DebugSetProcessKillOnExit.argtypes = [BOOL]
_DebugSetProcessKillOnExit.restype  = BOOL
_DebugActiveProcess                 = _kernel32.DebugActiveProcess
_DebugActiveProcess.argtypes        = [DWORD]
_DebugActiveProcess.restype         = BOOL
_DebugActiveProcessStop             = _kernel32.DebugActiveProcessStop
_DebugActiveProcessStop.argtypes    = [DWORD]
_DebugActiveProcessStop.restype     = BOOL
_WaitForDebugEvent                  = _kernel32.WaitForDebugEvent
_WaitForDebugEvent.argtypes         = [POINTER(_DEBUG_EVENT), DWORD]
_WaitForDebugEvent.restype          = BOOL
_ContinueDebugEvent                 = _kernel32.ContinueDebugEvent
_ContinueDebugEvent.argtypes        = [DWORD, DWORD, DWORD]
_ContinueDebugEvent.restype         = BOOL

_FormatMessageW                     = _kernel32.FormatMessageW
_FormatMessageW.argtypes            = [DWORD, LPVOID, DWORD, DWORD, LPWSTR, DWORD, LPVOID]
_FormatMessageW.restype             = DWORD
_LoadLibraryA                       = _kernel32.LoadLibraryA
_LoadLibraryA.argtypes              = [LPSTR]
_LoadLibraryA.restype               = HMODULE
_LoadLibraryW                       = _kernel32.LoadLibraryW
_LoadLibraryW.argtypes              = [LPWSTR]
_LoadLibraryW.restype               = HMODULE
_GetProcAddress                     = _kernel32.GetProcAddress
_GetProcAddress.argtypes            = [HMODULE, LPSTR]
_GetProcAddress.restype             = LPVOID
_GetModuleHandleA                   = _kernel32.GetModuleHandleA
_GetModuleHandleA.argtypes          = [LPSTR]
_GetModuleHandleA.restype           = HMODULE
_GetModuleHandleW                   = _kernel32.GetModuleHandleW
_GetModuleHandleW.argtypes          = [LPWSTR]
_GetModuleHandleW.restype           = HMODULE

_NtQueryInformationThread           = _ntdll.NtQueryInformationThread
_NtQueryInformationThread.argtypes  = [HANDLE, DWORD, PVOID, ULONG, PULONG]
_NtQueryInformationThread.restype   = NTSTATUS

def _create_buffer(size):
    """Create a ctypes buffer of a given size."""
    buftype = (CHAR * size)
    return buftype()

def _FormatMessage(error):
    """Format a Win32 error code to the corresponding message. (See MSDN)"""
    size = 256
    while size < 0x10000: # 0x10000 is the constant choosed in C# standard lib.
        buffer = (WCHAR * size)()
        result = _FormatMessageW(0x200 | 0x1000 | 0x2000, None, error, 0, buffer, size, None)
        if result > 0:
            return buffer[:result - 2]
        if _GetLastError() != 0x7A: # ERROR_INSUFFICIENT_BUFFER
            break
    return 'Unknow error'

class Win32Exception(RuntimeError):
    """Exception class for Win32 runtime errors."""
    def __init__(self, error = None, message = None):
        self.error = error or _GetLastError()
        self.msg = message or _FormatMessage(self.error)

    def __str__(self):
        return '%s (0x%08x)' % (self.msg, self.error)

    def __repr__(self):
        return 'Win32Exception(%s)' % str(self)

class ProcessScanner(object):
    """
    Class used to scan remote process's code section.
    """
    def __init__(self, proc, module = None):
        self.proc = proc
        self.module = proc.module(module)
        if not self.module:
            raise RuntimeError("Couldn't find default module")
        # Very hacky but that will do it for now
        self.base = self.module.base
        self.buffer, = proc.read(self.base, '%ds' % self.module.size)

    def find(self, pattern, offset = 0):
        """Returns address of the pattern if found."""
        match = self.buffer.find(pattern)
        if not match:
            raise RuntimeError("Couldn't find the pattern.")
        return self.base + match + offset

    def read(self, *args, **kw):
        return self.proc.read(*args, **kw)

    def __repr__(self):
        return '<Scanner 0x%08x for Process %d>' % (id(self), self.proc.id)

class ProcessModule(object):
    """
    A Win32 process module object.

    Properties:
        - handle
        - pid
        - name
        - base
        - size
        - file
    """
    def __init__(self, handle, process):
        self.handle = handle
        self.pid = process.id

        # make sure all properties are initialized
        self.name = None
        self.base = None
        self.size = None
        self.file = None

    def __eq__(self, other):
        return (self.handle == other.handle) and (self.pid == other.pid)

    def __str__(self):
        return '0x%08x %s' % (self.base, self.name)

    def __repr__(self):
        return '<ProcessModule %s in Process %d>' % (str(self), self.pid)

    @classmethod
    def from_MODULEENTRY32(cls, module, process):
        mod = ProcessModule(module.hModule, process)
        mod.name = module.szModule.decode('ascii').lower()
        mod.base = module.modBaseAddr
        mod.size = module.modBaseSize
        mod.file = module.szExePath.decode('ascii')
        return mod

class ProcessThread(object):
    """
    A Win32 process thread object.

    Properties:
        - id
        - pid
        - handle
        - alive
        - running
    """
    def __init__(self, id, process, handle = None):
        self.id = id
        self.pid = process.id

        self.handle = handle or _OpenThread(_THREAD_ALL_ACCESS, False, id)
        if not self.handle:
            raise Win32Exception()

    def __del__(self):
        _CloseHandle(self.handle)

    def __eq__(self, other):
        return (self.id == other.id)

    def __repr__(self):
        return '<ProcessThread %d in Process %d>' % (self.id, self.pid)

    def kill(self, code = 0):
        """Terminates the Thread with the given exit code."""
        success = _TerminateThread(self.handle, code)
        if not success:
            raise Win32Exception()

    @property
    def alive(self):
        """Checks if the thread is still executing."""
        code = DWORD()
        success = _GetExitCodeThread(self.handle, byref(code))
        if not success:
            raise Win32Exception()
        return (code.value == 259) # STILL_ACTIVE = 259

    def resume(self):
        """Resumes the thread."""
        count = _ResumeThread(self.handle)
        if count == 0xffffffff:
            raise Win32Exception()

    def suspend(self):
        """Suspends the thread."""
        count = _SuspendThread(self.handle)
        if count == 0xffffffff:
            raise Win32Exception()

    def join(self, timeout = _INFINITE):
        """Waits until the thread exit and returns the exit code."""
        reason = _WaitForSingleObject(self.handle, timeout)
        if reason != _WAIT_OBJECT_0:
            raise RuntimeError('Thread has been terminated prematurely.')
        code = DWORD()
        success = _GetExitCodeThread(self.handle, byref(code))
        if not success:
            raise Win32Exception()
        return code.value

    def context32(self, flags = _CONTEXT_FULL):
        """Retrieves the context of the ProcessThread."""
        if _PYTHON_IS_64_BITS:
            context = _WOW64_CONTEXT()
            context.ContextFlags = flags
            if not _Wow64GetThreadContext(self.handle, byref(context)):
                raise Win32Exception()
            return context
        else:
            return self.context(flags)

    def context(self, flags = _CONTEXT_FULL):
        """Retrieves the context of the ProcessThread."""
        context = _CONTEXT()
        context.ContextFlags = flags
        if not _GetThreadContext(self.handle, byref(context)):
            raise Win32Exception()
        return context

    def set_context32(self, context):
        """Sets the context for the ProcessThread."""
        success = _Wow64SetThreadContext(self.handle, byref(context))
        if not success:
            raise Win32Exception()

    def set_context(self, context):
        """Sets the context for the ProcessThread."""
        success = _SetThreadContext(self.handle, byref(context))
        if not success:
            raise Win32Exception()

    @property
    def teb(self):
        """Returns the address of the thread's information/environment block"""
        info = _THREAD_BASIC_INFORMATION()
        ntstatus = _NtQueryInformationThread(self.handle,
            _ThreadBasicInformation, byref(info), sizeof(info), None)
        # Need confirmation, but WinDll default returns type is int and
        # NTSUCCESS are positive signed 32 bytes integers [0 - 0x7fffffff]
        if ntstatus < 0:
            raise Win32Exception()
        return info.TebBaseAddress

class Hook(object):
    """
    Callable object that can contains information about the calling convention
    and the types of his params. Usefull to hook function compiled in C.

    e.g.
    @Hook.stdcall(DWORD)
    def OnSleep(dwMilliseconds):
        print(f'Sleep for {dwMilliseconds} ms')
    OnSleep(25) # prints 'Sleep for 25 ms'

    Note: The function can also be a method.
    e.g.
    class WatchProcess(object):
        def __init__(self, name):
            self.name = name

        @Hook.stdcall(DWORD)
        def OnSleep(self, dwMilliseconds):
            print(f'Process {self.name} Sleep for {dwMilliseconds} ms')

    p1 = WatchProcess('Notepad')
    s1 = p1.OnSleep
    s1(10) # prints 'Process Notepad Sleep for 10 ms'

    p2 = WatchProcess('Vim')
    s2 = p2.OnSleep
    s2(20) # prints 'Process Vim Sleep for 20 ms'
    """
    _stdcall  = 1
    _fastcall = 2
    _thiscall = 3
    _rawcall  = 4

    def __init__(self, callback, callconv, argtypes):
        self.callback = callback
        self.callconv = callconv
        self.argtypes = argtypes

        self.argstr = ''.join(arg._type_ for arg in argtypes)
        self.extargs = []

    def __hash__(self):
        return hash(self.callback)

    def __repr__(self):
        return repr(self.callback)

    def __str__(self):
        return str(self.callback)

    def __get__(self, inst, parent):
        hook = self.clone()
        hook.extargs = [inst]
        return hook

    def __call__(self, *args, **kw):
        try:
            return self.callback(*self.extargs, *args, **kw)
        except:
            print(traceback.format_exc())

    def clone(self):
        return Hook(self.callback, self.callconv, self.argtypes)

    def stdcall(*argtypes):
        def wrapper(function):
            proc = Hook(function, Hook._stdcall, argtypes)
            return proc
        return wrapper

    def fastcall(*argtypes):
        def wrapper(function):
            proc = Hook(function, Hook._fastcall, argtypes)
            return proc
        return wrapper

    def thiscall(*argtypes):
        def wrapper(function):
            proc = Hook(function, Hook._thiscall, argtypes)
            return proc
        return wrapper

    def rawcall(function):
        proc = Hook(function, Hook._rawcall, [])
        return proc

class ProcessHook(object):
    """
    """
    def __init__(self, proc, addr, hook):
        self.proc = proc
        self.addr = addr
        self.hook = hook
        self.inst = proc.read(addr, 's')[0]
        self.enabled = False

    def __del__(self):
        if self.enabled:
            self.disable()

    def __repr__(self):
        return '<ProcessHook %08X in Process %d>' % (self.addr, self.proc.id)

    def enable(self):
        self.enabled = True
        self.proc.write(self.addr, b'\xCC')
        self.proc.flush(self.addr, 1)

    def disable(self):
        self.enabled = False
        self.proc.write(self.addr, self.inst)
        self.proc.flush(self.addr, 1)

class ProcessDebugger(object):
    """
    """
    def __init__(self, proc):
        self.proc = proc
        self.is32bit = self.proc.is32bit();
        _DebugSetProcessKillOnExit(False)

    def __enter__(self):
        self.breakpoints = {};
        self.single_step_breakpoints = {}
        if not _DebugActiveProcess(self.proc.id):
            raise Win32Exception()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        l = len(self.breakpoints.values());
        # First we disable all the hooks which will restore the original
        # instructions.
        for breakpoint in self.breakpoints.values():
            breakpoint.disable()
        self.breakpoints = {}

        # Before stopping to debug the remote process we need to process all
        # debug events, because otherwise we might crash the remote process.
        self.poll(32)
        _DebugActiveProcessStop(self.proc.id)

    def __repr__(self):
        return '<ProcessDebugger for Process %d>' % self.proc.id

    def add_hook(self, addr, hook):
        new_bp = ProcessHook(self.proc, addr, hook)
        if addr in self.breakpoints:
            old_bp = self.breakpoints[addr]
            old_bp.disable()
        self.breakpoints[addr] = new_bp
        new_bp.enable()

    def run(self, **kw):
        frequency = kw.pop('frequency', _INFINITE)
        while self.attached:
            self.poll(frequency)

    def poll(self, timeout = _INFINITE):
        """Poll the next event dispatch it"""
        evt = _DEBUG_EVENT()
        while _WaitForDebugEvent(byref(evt), timeout):
            if evt.dwProcessId != self.proc.id:
                _ContinueDebugEvent(evt.dwProcessId, evt.dwThreadId, _DBG_EXCEPTION_NOT_HANDLED)
                return

            if evt.dwDebugEventCode == _EXIT_PROCESS_DEBUG_EVENT:
                # This mostly avoid exceptions when exiting the Python process,
                # because we can't restore breakpoints in a non-existent process.
                for breakpoint in self.breakpoints.values():
                    breakpoint.disable()
                self.breakpoints = {}
                _ContinueDebugEvent(evt.dwProcessId, evt.dwThreadId, _DBG_CONTINUE)

            if evt.dwDebugEventCode != _EXCEPTION_DEBUG_EVENT:
                _ContinueDebugEvent(evt.dwProcessId, evt.dwThreadId, _DBG_EXCEPTION_NOT_HANDLED)
                return

            continue_status = _DBG_CONTINUE
            try:
                thread = ProcessThread(evt.dwThreadId, self.proc)
                continue_status = self._on_debug_event(thread, evt.u.Exception)
            finally:
                _ContinueDebugEvent(evt.dwProcessId, evt.dwThreadId, continue_status)

    def _on_single_step(self, thread, addr):
        # The single step is done on a int3 which is a single bytes. This mean
        # the address of the hook is the previous instruction. Note that the hook
        # structure may not exist anymore in which case the original instruction
        # should be restored.
        breakpoint_addr = self.single_step_breakpoints.pop(thread.id)
        breakpoint = self.breakpoints.get(breakpoint_addr, None)
        if breakpoint is not None:
            breakpoint.enable()
        return _DBG_CONTINUE

    def _on_breakpoint32(self, thread, proc_hook):
        ctx = thread.context32()

        args = list()
        hook = proc_hook.hook
        conv = hook.callconv

        if conv == Hook._rawcall:
            args.append(ctx)
        else:
            argc = len(hook.argtypes)

            if (argc >= 1) and ((conv == Hook._fastcall) or (conv == Hook._thiscall)):
                args.append(ctx.Ecx)
            if (argc >= 2) and (conv == Hook._fastcall):
                args.append(ctx.Edx)

            argstr = hook.argstr[len(args):]
            argc = argc - len(args)
            stack_args = self.proc.read(ctx.Esp + 4, argstr)
            args.extend(stack_args)

        # What should we do here ??? (We don't want to crash the remote process)
        try:
            hook(*args)
        finally:
            ctx.Eip -= 1
            ctx.EFlags |= 0x100 # TRAP_FLAG
            thread.set_context(ctx)
        return _DBG_CONTINUE

    def _on_breakpoint64(self, thread, breakpoint):
        ctx = thread.context()

        args = list()
        hook = breakpoint.hook
        conv = hook.callconv
        argc = len(hook.argtypes)

        if 1 <= argc:
            args.append(ctx.Rcx)
        if 2 <= argc:
            args.append(ctx.Rdx)
        if 3 <= argc:
            args.append(ctx.R8)
        if 4 <= argc:
            args.append(ctx.R9)

        argstr = hook.argstr[len(args):]
        argc = argc - len(args)
        stack_args = self.proc.read(ctx.Rsp + 8, argstr)
        args.extend(stack_args)

        try:
            hook(*args)
        finally:
            ctx.Rip -= 1
            ctx.EFlags |= 0x100 # TRAP_FLAG
            thread.set_context(ctx)
        return _DBG_CONTINUE

    def _on_breakpoint(self, thread, addr):
        breakpoint = self.breakpoints.get(addr, None)
        if not breakpoint:
            return _DBG_EXCEPTION_NOT_HANDLED
        breakpoint.disable()

        # When single stepping, we don't know whether the next instruction
        # will jump elsewhere in the code. For this reason, we need to save
        # the breakpoint to re-enable it after the single step.
        #
        # - We save one breakpoint per thread, because we can't have more than
        #   one concurrent breakpoint on the same thread. This guarantee the
        #   next debug event is this breakpoint.
        # - We save only the address, because if the breakpoint get deleted in
        #   the mean time, we can detect it and not re-enable it.
        if thread.id in self.single_step_breakpoints:
            raise RuntimeError("It shouldn't be possible to have two breakpoints to restore on the same thread")
        self.single_step_breakpoints[thread.id] = addr

        if self.is32bit:
            return self._on_breakpoint32(thread, breakpoint)
        else:
            return self._on_breakpoint64(thread, breakpoint)

    def _on_debug_event(self, thread, info):
        """This is internal, but if you were to overload it, return the continuation status"""
        code = info.ExceptionCode
        if info.dwFirstChance != 1:
            return _DBG_EXCEPTION_NOT_HANDLED
        addr = info.ExceptionAddress
        if code == _EXCEPTION_SINGLE_STEP:
            ctx = thread.context32()
            return self._on_single_step(thread, addr)
        if code == _EXCEPTION_BREAKPOINT:
            ctx = thread.context32()
            return self._on_breakpoint(thread, addr)
        return _DBG_EXCEPTION_NOT_HANDLED

class Process(object):
    """
    An object to interact with a Win32 remote process.

    Properties:
        - id
        - handle
        - name
        - threads
        - modules
    """
    def __init__(self, pid, right = _PROCESS_ALL_ACCESS):
        self.id = pid
        self.handle = _OpenProcess(right, False, pid)
        if not self.handle:
            raise Win32Exception()

    def __del__(self):
        _CloseHandle(self.handle)

    def __eq__(self, other):
        return (self.id == other.id)

    def __repr__(self):
        return '<Process %d, handle %d at 0x%08x>' % (self.id, self.handle, id(self))

    @property
    def name(self):
        """Returns the name of the process."""
        return self.module().name

    def kill(self, code = 0):
        """Terminates the Process with the given exit code."""
        success = _TerminateProcess(self.handle, code)
        if not success:
            raise Win32Exception()

    def join(self, timeout = _INFINITE):
        """Wait until the Process terminates and Returns exit code"""
        reason = _WaitForSingleObject(self.handle, timeout)
        if reason != _WAIT_OBJECT_0:
            raise RuntimeError('Thread has been terminated prematurely.')
        code = DWORD()
        success = _GetExitCodeProcess(self.handle, byref(code))
        if not success:
            raise Win32Exception()
        return code.value

    def flush(self, addr = None, size = 0):
        """Flush the instruction cache for the process"""
        _FlushInstructionCache(self.handle, addr, size)

    def write(self, addr, *data):
        """Writes in remote process at the given address the data."""
        binary = b''.join(data)
        success = _WriteProcessMemory(self.handle, addr, binary, len(binary), None)
        if not success:
            raise Win32Exception()

    def read(self, addr, format = '<I'):
        """Reads in remote process at given address and return the given format."""
        size = struct.calcsize(format)
        buffer = _create_buffer(size)
        success = _ReadProcessMemory(self.handle, addr, byref(buffer), size, None)
        if not success:
            raise Win32Exception()
        return struct.unpack(format, buffer)

    def mmap(self, size, addr = None):
        """Allocates memory from the unmanaged memory of the process by using the specified number of bytes."""
        right = 0x40 # PAGE_EXECUTE_READWRITE
        flags = 0x1000 | 0x2000 # MEM_COMMIT | MEM_RESERVE
        memory = _VirtualAllocEx(self.handle, addr, size, flags, right)
        if not memory:
            raise Win32Exception()
        return memory

    def unmap(self, addr):
        """Releases memory previously allocated from the unmanaged memory of the process."""
        flags = 0x8000 # MEM_RELEASE
        _VirtualFreeEx(self.handle, addr, 0, flags)

    @property
    def threads(self):
        """Returns the ProcessThread's list of the process."""
        buffer = _THREADENTRY32()
        snap = _CreateToolhelp32Snapshot(_TH32CS_SNAPTHREAD, self.id)
        if not snap:
            raise Win32Exception()

        _threads = list()
        while _Thread32Next(snap, byref(buffer)):
            if buffer.th32OwnerProcessID == self.id:
                _threads.append( ProcessThread(buffer.th32ThreadID, self) )

        _CloseHandle(snap)
        return _threads

    @property
    def modules(self):
        """Returns the ProcessModule's list of the process."""
        buffer = _MODULEENTRY32()
        snapshot = _CreateToolhelp32Snapshot(_TH32CS_SNAPMODULE | _TH32CS_SNAPMODULE32, self.id)
        if not snapshot:
            raise Win32Exception()

        _modules = list()
        while _Module32Next(snapshot , byref(buffer)):
            _modules.append( ProcessModule.from_MODULEENTRY32(buffer, self) )

        _CloseHandle(snapshot)
        return _modules

    def module(self, name = None):
        """Return a ProcessModule's instance of a given module's name."""
        buffer = _MODULEENTRY32()
        snapshot = _CreateToolhelp32Snapshot(_TH32CS_SNAPMODULE | _TH32CS_SNAPMODULE32, self.id)
        if not snapshot:
            raise Win32Exception()

        if name == None:
            rv = _Module32First(snapshot, byref(buffer)) # can this even fail if we were able to open the snapshot ?
            _CloseHandle(snapshot)
            return ProcessModule.from_MODULEENTRY32(buffer, self)

        name = name.encode('ascii')
        while _Module32Next(snapshot, byref(buffer)):
            if buffer.szModule == name:
                _CloseHandle(snapshot)
                return ProcessModule.from_MODULEENTRY32(buffer, self)

        raise RuntimeError('No process module with the given name was found.')

    def page_info(self, addr):
        """Returns (size, access right) about a range of pages in the virtual address space of a process."""
        if not _PYTHON_IS_64_BITS:
            buffer = _MEMORY_BASIC_INFORMATION()
        else:
            buffer = _MEMORY_BASIC_INFORMATION64()
        _VirtualQueryEx(self.handle, addr, byref(buffer), sizeof(buffer))
        return buffer.RegionSize, buffer.Protect

    def spawn_thread(self, entry, param = None):
        """Spawns a thread in a suspended state and returns his ProcessThread."""
        id = DWORD()
        handle = _CreateRemoteThread(self.handle, 0, 0, entry, param, 4, byref(id))
        if not handle:
            raise Win32Exception()
        return ProcessThread(id, self, handle)

    def is32bit(self):
        wow64 = BOOL()
        if not _IsWow64Process(self.handle, byref(wow64)):
            raise Win32Exception()
        return wow64.value == 1

    @classmethod
    def from_name(cls, name):
        """Creates a Process from his name."""
        processes = GetProcesses(name)
        if not len(processes):
            raise RuntimeError('No process with the given name was found.')
        return processes[0]

def GetProcesses(name, right = _PROCESS_ALL_ACCESS):
    """Returns a list of Process that have the give name."""
    name = name.encode('ascii').lower()
    entries = list()

    buffer = _PROCESSENTRY32()
    snapshot = _CreateToolhelp32Snapshot(_TH32CS_SNAPPROCESS, 0)
    if not snapshot:
        raise Win32Exception()

    while _Process32Next(snapshot, byref(buffer)):
        if buffer.szExeFile.lower() == name:
            entries.append( Process(buffer.th32ProcessID, right) )

    _CloseHandle(snapshot)
    return entries
