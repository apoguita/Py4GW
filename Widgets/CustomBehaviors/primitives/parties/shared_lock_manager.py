from __future__ import annotations

import time
from collections import deque
from ctypes import Structure, c_uint, c_wchar
from typing import Generator
from Py4GWCoreLib import Player

# Constants for the shared lock table
MAX_LOCKS = 64
MAX_LOCK_KEY_LEN = 64
MAX_SENDER_EMAIL_LEN = 64
MAX_LOCK_HISTORY = 30
LOCK_TTL_SECONDS = 30

class SharedLockEntry:
    def __init__(self, key: str, acquired_at_seconds: int, sender_email: str, ttl_seconds: int = LOCK_TTL_SECONDS):

        self.key: str = key
        self.acquired_at_seconds: int = acquired_at_seconds
        self.ttl_seconds: int = ttl_seconds
        self.sender_email: str = sender_email

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
        ("ReleasedAt", c_uint),
        ("TTLSeconds", c_uint),
        ("SenderEmail", c_wchar * MAX_SENDER_EMAIL_LEN),
    ]

class SharedLockHistoryStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Key", c_wchar * MAX_LOCK_KEY_LEN),
        ("SenderEmail", c_wchar * MAX_SENDER_EMAIL_LEN),
        ("AcquiredAt", c_uint),
        ("ReleasedAt", c_uint),
    ]

class SharedLockHistory:
    def __init__(self, key: str, sender_email: str, acquired_at_seconds: int | None = None, released_at_seconds: int | None = None):
        self.key: str = key
        self.sender_email: str = sender_email
        self.acquired_at: int | None = int(time.time()) if acquired_at_seconds is None else acquired_at_seconds
        self.released_at: int | None = released_at_seconds

class SharedLockManager:
    def __init__(self, get_struct_callable):
        self._get_struct_callable = get_struct_callable
        # keep a small rolling history of lock events (newest at the end)

    def get_lock_history(self) -> deque[SharedLockHistory]: 
        # Prefer shared memory ring buffer so history is visible across runtimes
        try:
            mem = self.__get_struct()
            if hasattr(mem, "LockHistoryEntries") and hasattr(mem, "LockHistoryIdx"):
                result: deque[SharedLockHistory] = deque[SharedLockHistory](maxlen=MAX_LOCK_HISTORY)
                start_idx = getattr(mem, "LockHistoryIdx", 0)
                for i in range(MAX_LOCK_HISTORY):
                    idx = (start_idx - 1 - i) % MAX_LOCK_HISTORY
                    sh = mem.LockHistoryEntries[idx]
                    key = sh.Key
                    acquired_at = int(sh.AcquiredAt)
                    released_at = int(sh.ReleasedAt)
                    sender = sh.SenderEmail
                    if key == "" and acquired_at == 0 and released_at == 0:
                        continue
                    result.append(
                        SharedLockHistory(
                            key,
                            sender,
                            acquired_at_seconds=(acquired_at if acquired_at != 0 else None),
                            released_at_seconds=(released_at if released_at != 0 else None),
                        )
                    )
                return result
        except Exception:
            pass
        # Always return an empty deque if shared memory isn't available
        return deque[SharedLockHistory]()

    def __get_struct(self):
        return self._get_struct_callable()

    def __update_history_on_release(self, key: str, acquired_at: int, sender_email: str, released_at: int) -> None:
        """Update shared-memory history for a released/expired lock."""
        try:
            mem = self.__get_struct()
            if hasattr(mem, "LockHistoryEntries"):
                self.__update_shared_history_on_release(mem, key, acquired_at, sender_email, released_at)
        except Exception:
            pass

    def __release_and_clear_slot(self, mem, slot_index: int, released_at: int) -> None:
        """Mark a slot as released, update history, and clear key/acquired time.

        SenderEmail is intentionally preserved for auditing.
        """
        try:
            self.__update_history_on_release(
                mem.LockEntries[slot_index].Key,
                mem.LockEntries[slot_index].AcquiredAt,
                mem.LockEntries[slot_index].SenderEmail,
                released_at,
            )
            self.__update_shared_history_on_release(
                mem,
                mem.LockEntries[slot_index].Key,
                mem.LockEntries[slot_index].AcquiredAt,
                mem.LockEntries[slot_index].SenderEmail,
                released_at,
            )
        except Exception:
            pass

        try:
            if hasattr(mem.LockEntries[slot_index], "ReleasedAt"):
                mem.LockEntries[slot_index].ReleasedAt = released_at
        except Exception:
            pass

        mem.LockEntries[slot_index].Key = ""
        mem.LockEntries[slot_index].AcquiredAt = 0
        if hasattr(mem.LockEntries[slot_index], "TTLSeconds"):
            mem.LockEntries[slot_index].TTLSeconds = 0

    def __dedupe_locks(self):
        """
        Normalize the shared lock table by:
        1) Evicting expired entries
        2) Deduplicating so only the oldest entry per key remains
        """
        mem = self.__get_struct()
        now_s = int(time.time())
        first_seen_by_key: dict[str, int] = {}

        for slot_index in range(MAX_LOCKS):
            key = mem.LockEntries[slot_index].Key
            acquired_at = mem.LockEntries[slot_index].AcquiredAt

            if key == "" or acquired_at == 0:
                continue

            # 1) Evict expired entries
            ttl_seconds = getattr(mem.LockEntries[slot_index], 'TTLSeconds', LOCK_TTL_SECONDS)
            if SharedLockEntry(key, acquired_at, sender_email=mem.LockEntries[slot_index].SenderEmail, ttl_seconds=ttl_seconds).is_expired(now_s):
                self.__release_and_clear_slot(mem, slot_index, int(time.time()))
                continue

            # 2) Deduplicate: keep oldest per key
            previous_slot = first_seen_by_key.get(key)
            if previous_slot is None:
                first_seen_by_key[key] = slot_index
                continue

            previous_acquired_at = mem.LockEntries[previous_slot].AcquiredAt
            if previous_acquired_at <= acquired_at:
                # current is newer; remove current
                self.__release_and_clear_slot(mem, slot_index, int(time.time()))
            else:
                # previous is newer; remove previous and remember current
                self.__release_and_clear_slot(mem, previous_slot, int(time.time()))
                first_seen_by_key[key] = slot_index

    def __find_lock_index(self, key: str) -> int | None:
        self.__dedupe_locks()
        mem = self.__get_struct()
        now_s = int(time.time())
        for i in range(MAX_LOCKS):
            if mem.LockEntries[i].Key != "" and mem.LockEntries[i].AcquiredAt != 0:
                ttl_seconds = getattr(mem.LockEntries[i], 'TTLSeconds', LOCK_TTL_SECONDS)
                entry = SharedLockEntry(mem.LockEntries[i].Key, mem.LockEntries[i].AcquiredAt, sender_email=mem.LockEntries[i].SenderEmail, ttl_seconds=ttl_seconds)
                if entry.is_expired(now_s):
                    released_at_now = int(time.time())
                    mem.LockEntries[i].Key = ""
                    # update history before clearing acquired time
                    self.__update_history_on_release(entry.key, mem.LockEntries[i].AcquiredAt, mem.LockEntries[i].SenderEmail, released_at_now)
                    mem.LockEntries[i].AcquiredAt = 0
                    if hasattr(mem.LockEntries[i], "ReleasedAt"):
                        mem.LockEntries[i].ReleasedAt = released_at_now
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
                ttl_seconds = getattr(mem.LockEntries[i], 'TTLSeconds', LOCK_TTL_SECONDS)
                entry = SharedLockEntry(mem.LockEntries[i].Key, mem.LockEntries[i].AcquiredAt, sender_email=mem.LockEntries[i].SenderEmail, ttl_seconds=ttl_seconds)
                if entry.is_expired(now_s):
                    mem.LockEntries[i].Key = ""
                    mem.LockEntries[i].AcquiredAt = 0
                    if hasattr(mem.LockEntries[i], "TTLSeconds"):
                        mem.LockEntries[i].TTLSeconds = 0
            if mem.LockEntries[i].Key == "":
                return i
        return None

    def try_aquire_lock(self, key: str, timeout_seconds: int = LOCK_TTL_SECONDS) -> bool:
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
        mem.LockEntries[idx].ReleasedAt = 0
        mem.LockEntries[idx].TTLSeconds = timeout_seconds
        mem.LockEntries[idx].SenderEmail = f"{Player.GetAccountEmail()} | {Player.GetName()}"
        # final dedupe to collapse any rare duplicates due to races
        self.__dedupe_locks()
        # record history in shared memory ring
        self.__append_shared_history(
            self.__get_struct(),
            key,
            mem.LockEntries[idx].SenderEmail,
            mem.LockEntries[idx].AcquiredAt,
            0,
        )
        # We successfully acquired the lock, return True
        return True

    def release_lock(self, key: str) -> None:
        if key is None or key == "":
            return
        mem = self.__get_struct()
        idx = self.__find_lock_index(key)
        if idx is not None:
            # capture state before clearing
            acquired_at_before = mem.LockEntries[idx].AcquiredAt
            sender_before = mem.LockEntries[idx].SenderEmail
            released_at_now = int(time.time())
            mem.LockEntries[idx].Key = ""
            mem.LockEntries[idx].AcquiredAt = 0
            mem.LockEntries[idx].ReleasedAt = released_at_now
            if hasattr(mem.LockEntries[idx], "TTLSeconds"):
                mem.LockEntries[idx].TTLSeconds = 0
            # update existing history row instead of appending
            self.__update_history_on_release(key, acquired_at_before, sender_before, released_at_now)
            self.__update_shared_history_on_release(mem, key, acquired_at_before, sender_before, released_at_now)
            mem.LockEntries[idx].SenderEmail = ""

    # ---------- Shared history ring buffer helpers ----------
    def __append_shared_history(self, mem, key: str, sender_email: str, acquired_at: int, released_at: int) -> None:
        try:
            idx = getattr(mem, "LockHistoryIdx", 0) % MAX_LOCK_HISTORY
            mem.LockHistoryEntries[idx].Key = key
            mem.LockHistoryEntries[idx].SenderEmail = sender_email
            mem.LockHistoryEntries[idx].AcquiredAt = acquired_at
            mem.LockHistoryEntries[idx].ReleasedAt = released_at
            mem.LockHistoryIdx = (idx + 1) % MAX_LOCK_HISTORY
        except Exception:
            pass

    def __update_shared_history_on_release(self, mem, key: str, acquired_at: int, sender_email: str, released_at: int) -> None:
        try:
            # search newest to oldest in ring
            for i in range(MAX_LOCK_HISTORY):
                idx = (getattr(mem, "LockHistoryIdx", 0) - 1 - i) % MAX_LOCK_HISTORY
                if mem.LockHistoryEntries[idx].Key == key and mem.LockHistoryEntries[idx].AcquiredAt == acquired_at:
                    mem.LockHistoryEntries[idx].ReleasedAt = released_at
                    if mem.LockHistoryEntries[idx].SenderEmail == "":
                        mem.LockHistoryEntries[idx].SenderEmail = sender_email
                    return
            # if not found (e.g., history rolled over), append a new one
            self.__append_shared_history(mem, key, sender_email, acquired_at, released_at)
        except Exception:
            pass

    def is_lock_taken(self, key: str) -> bool:
        if key is None or key == "":
            return False
        self.__dedupe_locks()
        mem = self.__get_struct()
        now_s = int(time.time())
        for i in range(MAX_LOCKS):
            if mem.LockEntries[i].Key == key and mem.LockEntries[i].AcquiredAt != 0:
                ttl_seconds = getattr(mem.LockEntries[i], 'TTLSeconds', LOCK_TTL_SECONDS)
                entry = SharedLockEntry(mem.LockEntries[i].Key, mem.LockEntries[i].AcquiredAt, sender_email=mem.LockEntries[i].SenderEmail, ttl_seconds=ttl_seconds)
                if entry.is_expired(now_s):
                    mem.LockEntries[i].Key = ""
                    mem.LockEntries[i].AcquiredAt = 0
                    mem.LockEntries[i].ReleasedAt = int(time.time())
                    mem.LockEntries[i].SenderEmail = ""
                    if hasattr(mem.LockEntries[i], "TTLSeconds"):
                        mem.LockEntries[i].TTLSeconds = 0
                    return False
                return True
        return False

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
                ttl_seconds = getattr(mem.LockEntries[i], 'TTLSeconds', LOCK_TTL_SECONDS)
                entry = SharedLockEntry(
                    mem.LockEntries[i].Key,
                    mem.LockEntries[i].AcquiredAt,
                    mem.LockEntries[i].SenderEmail,
                    ttl_seconds=ttl_seconds,
                )
                if not entry.is_expired(now_s):
                    result.append(entry)
        return result

    def is_any_lock_taken(self) -> bool:
        """Check if any lock is currently active (not expired)."""
        self.__dedupe_locks()
        mem = self.__get_struct()
        now_s = int(time.time())
        for i in range(MAX_LOCKS):
            if mem.LockEntries[i].Key != "" and mem.LockEntries[i].AcquiredAt != 0:
                ttl_seconds = getattr(mem.LockEntries[i], 'TTLSeconds', LOCK_TTL_SECONDS)
                entry = SharedLockEntry(
                    mem.LockEntries[i].Key,
                    mem.LockEntries[i].AcquiredAt,
                    mem.LockEntries[i].SenderEmail,
                    ttl_seconds=ttl_seconds,
                )
                if not entry.is_expired(now_s):
                    return True
        return False

