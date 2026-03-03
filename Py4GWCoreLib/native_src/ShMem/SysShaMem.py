import Py4GW
from multiprocessing import shared_memory
from ctypes import Structure, c_uint32, c_uint64
import ctypes
from .structs.AgentArraySSM import AgentArraySHMemStruct, AgentArraySHMemWrapper  


class SharedMemoryHeader(Structure):
    _pack_ = 1
    _fields_ = [
        ("version", c_uint32),
        ("total_size", c_uint32),
        ("sequence", c_uint32),
        ("process_id", c_uint32),
        ("window_handle", c_uint64),
    ]

class SystemSharedMemoryManager:
    _instance = None  # Singleton instance
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SystemSharedMemoryManager, cls).__new__(cls)
            cls._instance._initialized = False  # Ensure __init__ runs only once
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.shm_name = Py4GW.Game.get_shared_memory_name()
            self.shm: shared_memory.SharedMemory | None = None
            self.size = ctypes.sizeof(SharedMemoryHeader) + ctypes.sizeof(AgentArraySHMemStruct)
            self.header_struct: SharedMemoryHeader | None = None
            self.agent_array_struct: AgentArraySHMemStruct | None = None
            self.agent_array_wrapper: AgentArraySHMemWrapper | None = None
            self.last_error: str = ""
            self._enabled = False
            self._connect()
            self._initialized = True

    def _connect(self) -> bool:
        current_name = Py4GW.Game.get_shared_memory_name()
        if not current_name:
            self.close()
            self.last_error = "No shared memory name returned by Py4GW.Game."
            return False

        if self.shm is not None and self.shm_name == current_name:
            return True

        self.close()
        self.shm_name = current_name

        try:
            self.shm = shared_memory.SharedMemory(name=self.shm_name, create=False)
            self.last_error = ""
            return True
        except FileNotFoundError:
            self.last_error = f"Shared memory not found: {self.shm_name}"
            self.shm = None
            return False
        except Exception as exc:
            self.last_error = f"Failed to attach shared memory: {exc}"
            self.shm = None
            return False

    def close(self):
        if self.shm is not None:
            self.shm.close()
            self.shm = None

    def reset_data(self):
        self.header_struct = None
        self.agent_array_struct = None
        self.agent_array_wrapper = None

    def get_payload(self):
        self.reset_data()
        if not self._connect():
            return

        header_size = ctypes.sizeof(SharedMemoryHeader)
        header_offset = header_size
        agent_array_size = ctypes.sizeof(AgentArraySHMemStruct)

        if self.shm is None or self.shm.buf is None:
            self.last_error = "Shared memory buffer is not available."
            return

        for _ in range(3):
            header_before = SharedMemoryHeader.from_buffer_copy(self.shm.buf[:header_size])
            if header_before.sequence & 1:
                continue

            payload = AgentArraySHMemStruct.from_buffer_copy(
                self.shm.buf[header_offset:header_offset + agent_array_size]
            )
            header_after = SharedMemoryHeader.from_buffer_copy(self.shm.buf[:header_size])

            if header_before.sequence != header_after.sequence:
                continue

            if header_after.sequence & 1:
                continue

            self.header_struct = header_after
            self.agent_array_struct = payload
            self.agent_array_wrapper = AgentArraySHMemWrapper(payload)
            self.last_error = ""
            return

        self.last_error = "Snapshot changed while reading."
        return

    def enable(self):
        if self._enabled:
            return
        import PyCallback
        PyCallback.PyCallback.Register(
            "SystemSharedMemory.get_payload",
            PyCallback.Phase.PreUpdate,
            self.get_payload,
            priority = 0,
            context=PyCallback.Context.Draw
        )
        self._enabled = True

    def disable(self):
        if not self._enabled:
            self.close()
            self.reset_data()
            return
        import PyCallback
        PyCallback.PyCallback.RemoveByName("SystemSharedMemory.get_payload")
        self._enabled = False
        self.close()
        self.reset_data()

    def get_agent_array_wrapper(self) -> AgentArraySHMemWrapper | None:
        return self.agent_array_wrapper
    
SystemShaMemMgr = SystemSharedMemoryManager()

SystemShaMemMgr.enable()
