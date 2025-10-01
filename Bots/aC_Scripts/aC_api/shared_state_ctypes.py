# shared_state_ctypes.py
# ---------------------------------------------------------------
import os
import time
import ctypes
from enum import IntEnum
from multiprocessing import shared_memory

# —── flock shim for cross-platform locking ──—
try:
    import fcntl
    def _acquire_lock(fd):
        fcntl.flock(fd, fcntl.LOCK_EX)
    def _release_lock(fd):
        fcntl.flock(fd, fcntl.LOCK_UN)
except ImportError:
    # Windows fallback: lock via mkdir loop
    def _acquire_lock(lock):
        path, fd = lock
        while True:
            try:
                os.mkdir(path)
                break
            except FileExistsError:
                time.sleep(0.01)

    def _release_lock(lock):
        path, fd = lock
        try:
            os.rmdir(path)
        except OSError:
            pass

# —── Constants & Enums ──—
MAX_CLIENTS = 8
STALE_THRESHOLD = 60.0  # seconds

class SyncState(IntEnum):
    IDLE       = 0
    MOVING     = 1
    IN_DIALOG  = 2
    DONE       = 3

# —── Shared struct layout ──—
class SharedData(ctypes.Structure):
    _fields_ = [
        ("model_id",   ctypes.c_int32),
        ("choice",     ctypes.c_int32),    # -1 = None
        ("timestamp",  ctypes.c_double),
        ("pos_x",      ctypes.c_double),
        ("pos_y",      ctypes.c_double),

        ("state",      ctypes.c_int32 * MAX_CLIENTS),
        ("last_ts",    ctypes.c_double  * MAX_CLIENTS),
        ("confirmed",  ctypes.c_uint8   * MAX_CLIENTS),
        ("active_mask",ctypes.c_uint8),

        ("_pad",       ctypes.c_uint8 * 43),
    ]

# —── Manager singleton ──—
class SharedState:
    _instance = None
    _SHM_SIZE = ctypes.sizeof(SharedData)

    def __new__(cls, name: str = "mywidgets_sync", *, lock_dir: str = ""):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init(name, lock_dir)
        return cls._instance

    def _init(self, name: str, lock_dir: str):
        # 1) Attach or create shared memory safely
        try:
            # try to attach existing
            self.shm = shared_memory.SharedMemory(name=name)
            first_init = False
        except FileNotFoundError:
            # not found: create new
            try:
                self.shm = shared_memory.SharedMemory(
                    name=name, create=True, size=self._SHM_SIZE
                )
                first_init = True
            except FileExistsError:
                # race: someone else created it in between
                self.shm = shared_memory.SharedMemory(name=name)
                first_init = False

        # 2) Map to ctypes
        self.data = SharedData.from_buffer(self.shm.buf)

        # 3) If attaching to a stale segment, clear it
        if not first_init:
            now = time.time()
            if (now - self.data.timestamp) > STALE_THRESHOLD:
                self._clear_all()

        # 4) Set up a cross-platform lock
        tmp = lock_dir or os.getenv("TMPDIR", os.getenv("TEMP", "/tmp"))
        lock_path = os.path.join(tmp, f"{name}.lockdir")
        open(lock_path + ".fd", "a").close()
        self._lock = (lock_path, open(lock_path + ".fd", "r+"))

        # 5) If brand new, initialize defaults
        if first_init:
            self._clear_all()

    def _clear_all(self):
        d = self.data
        d.model_id    = 0
        d.choice      = -1
        d.timestamp   = time.time()
        d.pos_x       = 0.0
        d.pos_y       = 0.0
        d.active_mask = 0
        for i in range(MAX_CLIENTS):
            d.state[i]     = SyncState.IDLE
            d.last_ts[i]   = 0.0
            d.confirmed[i] = 0

    ### ─── Global getters/setters ───
    def get_model_id(self) -> int:
        return int(self.data.model_id)

    def set_model_id(self, mid: int):
        _acquire_lock(self._lock)
        try:
            self.data.model_id  = mid
            self.data.choice    = -1
            self.data.timestamp = time.time()
        finally:
            _release_lock(self._lock)

    def get_choice(self) -> int | None:
        c = self.data.choice
        return None if c < 0 else int(c)

    def set_choice(self, choice: int):
        _acquire_lock(self._lock)
        try:
            self.data.choice    = choice
            self.data.timestamp = time.time()
        finally:
            _release_lock(self._lock)

    def get_timestamp(self) -> float:
        return float(self.data.timestamp)

    def set_position(self, x: float, y: float):
        _acquire_lock(self._lock)
        try:
            self.data.pos_x     = x
            self.data.pos_y     = y
            self.data.timestamp = time.time()
        finally:
            _release_lock(self._lock)

    def get_position(self) -> tuple[float,float,float]:
        return (
            float(self.data.pos_x),
            float(self.data.pos_y),
            float(self.data.timestamp),
        )

    ### ─── Per-client state ───
    def set_client_state(self, agent_idx: int, state: int):
        if not (0 <= agent_idx < MAX_CLIENTS):
            raise IndexError
        _acquire_lock(self._lock)
        try:
            self.data.state[agent_idx]   = state
            self.data.last_ts[agent_idx] = time.time()
        finally:
            _release_lock(self._lock)

    def get_client_state(self, agent_idx: int) -> tuple[int,float]:
        if not (0 <= agent_idx < MAX_CLIENTS):
            raise IndexError
        return (
            int(self.data.state[agent_idx]),
            float(self.data.last_ts[agent_idx])
        )

    def confirm_client(self, agent_idx: int, yes: bool=True):
        if not (0 <= agent_idx < MAX_CLIENTS):
            raise IndexError
        _acquire_lock(self._lock)
        try:
            self.data.confirmed[agent_idx] = 1 if yes else 0
        finally:
            _release_lock(self._lock)

    def is_client_confirmed(self, agent_idx: int) -> bool:
        if not (0 <= agent_idx < MAX_CLIENTS):
            raise IndexError
        return bool(self.data.confirmed[agent_idx])

    def set_active_clients(self, mask: int):
        _acquire_lock(self._lock)
        try:
            self.data.active_mask = mask
        finally:
            _release_lock(self._lock)

    def get_active_clients(self) -> int:
        return int(self.data.active_mask)

    ### ─── Helpers ───
    def tick(self):
        """
        Every 3 s, clear any slot whose last_ts is older than 30 s.
        """
        now = time.time()
        for i in range(MAX_CLIENTS):
            if now - self.data.last_ts[i] > 30.0:
                self.data.state[i]     = SyncState.IDLE
                self.data.confirmed[i] = 0

    def close(self):
        try:
            self.shm.close()
            self._lock[1].close()
        except Exception:
            pass
