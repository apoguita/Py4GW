from __future__ import annotations

import time
from ctypes import Structure, c_uint, c_wchar
from typing import Generator

# Constants for the shared lock table
MAX_LOCKS = 64
MAX_LOCK_KEY_LEN = 64
LOCK_TTL_SECONDS = 30

class SharedLockEntry:
    def __init__(self, key: str, acquired_at_seconds: int, ttl_seconds: int = LOCK_TTL_SECONDS):
        self.key: str = key
        self.acquired_at_seconds: int = acquired_at_seconds
        self.ttl_seconds: int = ttl_seconds

    @property
    def expires_at_seconds(self) -> int:
        return self.acquired_at_seconds + self.ttl_seconds

    def is_expired(self, now_seconds: int | None = None) -> bool:
        now_s = int(time.time()) if now_seconds is None else now_seconds
        return now_s > self.expires_at_seconds


class SharedLockEntryStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Key", c_wchar * MAX_LOCK_KEY_LEN),
        ("AcquiredAt", c_uint),
    ]


class SharedLockManager:
    def __init__(self, get_struct_callable):
        self._get_struct_callable = get_struct_callable

    def __get_struct(self):
        return self._get_struct_callable()

    def __dedupe_locks(self):
        mem = self.__get_struct()
        now_s = int(time.time())
        first_seen: dict[str, int] = {}
        for i in range(MAX_LOCKS):
            key = mem.LockEntries[i].Key
            ts = mem.LockEntries[i].AcquiredAt
            if key == "" or ts == 0:
                continue
            # evict expired
            entry = SharedLockEntry(key, ts)
            if entry.is_expired(now_s):
                mem.LockEntries[i].Key = ""
                mem.LockEntries[i].AcquiredAt = 0
                continue
            if key not in first_seen:
                first_seen[key] = i
            else:
                # keep the oldest entry (smallest timestamp); clear newer
                prev_idx = first_seen[key]
                if mem.LockEntries[prev_idx].AcquiredAt <= ts:
                    mem.LockEntries[i].Key = ""
                    mem.LockEntries[i].AcquiredAt = 0
                else:
                    mem.LockEntries[prev_idx].Key = ""
                    mem.LockEntries[prev_idx].AcquiredAt = 0
                    first_seen[key] = i

    def __find_lock_index(self, key: str) -> int | None:
        self.__dedupe_locks()
        mem = self.__get_struct()
        now_s = int(time.time())
        for i in range(MAX_LOCKS):
            if mem.LockEntries[i].Key != "" and mem.LockEntries[i].AcquiredAt != 0:
                entry = SharedLockEntry(mem.LockEntries[i].Key, mem.LockEntries[i].AcquiredAt)
                if entry.is_expired(now_s):
                    mem.LockEntries[i].Key = ""
                    mem.LockEntries[i].AcquiredAt = 0
                elif mem.LockEntries[i].Key == key:
                    return i
            elif mem.LockEntries[i].Key == key:
                return i
        return None

    def __find_empty_lock_slot(self) -> int | None:
        self.__dedupe_locks()
        mem = self.__get_struct()
        now_s = int(time.time())
        for i in range(MAX_LOCKS):
            if mem.LockEntries[i].Key != "" and mem.LockEntries[i].AcquiredAt != 0:
                entry = SharedLockEntry(mem.LockEntries[i].Key, mem.LockEntries[i].AcquiredAt)
                if entry.is_expired(now_s):
                    mem.LockEntries[i].Key = ""
                    mem.LockEntries[i].AcquiredAt = 0
            if mem.LockEntries[i].Key == "":
                return i
        return None

    def try_aquire_lock(self, key: str) -> bool:
        if key is None or key == "":
            return False
        self.__dedupe_locks()
        if self.__find_lock_index(key) is not None:
            return False
        idx = self.__find_empty_lock_slot()
        if idx is None:
            return False
        mem = self.__get_struct()
        mem.LockEntries[idx].Key = key
        mem.LockEntries[idx].AcquiredAt = int(time.time())
        # final dedupe to collapse any rare duplicates due to races
        self.__dedupe_locks()
        # We successfully acquired the lock, return True
        return True

    def release_lock(self, key: str) -> None:
        if key is None or key == "":
            return
        mem = self.__get_struct()
        idx = self.__find_lock_index(key)
        if idx is not None:
            mem.LockEntries[idx].Key = ""
            mem.LockEntries[idx].AcquiredAt = 0

    def wait_aquire_lock(self, key: str, timeout_seconds: int = 20) -> Generator[None, None, bool]:
        if timeout_seconds is None or timeout_seconds < 0:
            timeout_seconds = 20
        start_time_s = time.time()
        while not self.try_aquire_lock(key):
            if (time.time() - start_time_s) >= timeout_seconds:
                return False
            yield
        return True

    def get_current_locks(self) -> list[SharedLockEntry]:
        self.__dedupe_locks()
        mem = self.__get_struct()
        now_s = int(time.time())
        result: list[SharedLockEntry] = []
        for i in range(MAX_LOCKS):
            if mem.LockEntries[i].Key != "" and mem.LockEntries[i].AcquiredAt != 0:
                entry = SharedLockEntry(mem.LockEntries[i].Key, mem.LockEntries[i].AcquiredAt)
                if not entry.is_expired(now_s):
                    result.append(entry)
        return result

