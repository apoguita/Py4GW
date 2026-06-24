"""
Settings — Account-Level Key Cache for the Py4GW settings database.

The Settings class maintains in-memory caches for the Widget, Keys (per-account),
and Globals tables. Every get/set/delete operation reads from or writes to cache
rather than hitting the database.

On each throttle period (1000 ms), dirty cache entries are flushed to the database
in a single transaction. This reduces the per-operation open→execute→commit→close
cycle to one DB read on first access (or account change) and one DB write per
throttle tick.

**commit parameter semantics (changed)**:
    For cache-backed operations (current account, globals) the ``commit``
    parameter is accepted but ignored — all writes are staged in cache and
    persisted on the next throttle flush.  For direct-DB fallback paths
    (non-current accounts) ``commit`` is still honoured.

    Return values: methods that return a database row ID may return 0 for
    newly-created entries that have not yet been flushed to disk.

**Account identification**:
    The current account is identified by email (via Player.GetAccountEmail())
    and/or HWND (via Py4GW.Console.get_gw_window_handle()).  Account change
    detection checks both values and invalidates the account cache on mismatch.
"""

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Optional, cast

from .Account import Account
from .DBMgr import DBMgr
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
import Py4GW


class WidgetSettings:
    """Widget-bound convenience wrapper over Settings."""

    def __init__(self, settings_db: 'Settings', widget_key: str, widget_name: Optional[str], description: Optional[str]) -> None:
        self._settings_db = settings_db
        self.widget_key = str(widget_key).strip()
        self.widget_name = widget_name
        self.description = description

    def Ensure(self, commit: bool = True) -> int:
        return self._settings_db.EnsureWidget(self.widget_key, self.widget_name, self.description, commit=commit)

    def EnsureKey(self, section: str, key: str, key_type: str, default: Any, commit: bool = True) -> int:
        self.Ensure(commit=commit)
        existing = self._settings_db.GetCurrentAccountEntry(self.widget_key, section, key, commit=commit)
        if existing is not None:
            return int(existing['ID'])
        return self.SetKey(section, key, key_type, default, commit=commit)

    def EnsureBool(self, section: str, key: str, default: bool = False, commit: bool = True) -> int:
        return self.EnsureKey(section, key, 'bool', default, commit=commit)

    def EnsureInt(self, section: str, key: str, default: int = 0, commit: bool = True) -> int:
        return self.EnsureKey(section, key, 'int', default, commit=commit)

    def EnsureFloat(self, section: str, key: str, default: float = 0.0, commit: bool = True) -> int:
        return self.EnsureKey(section, key, 'float', default, commit=commit)

    def EnsureStr(self, section: str, key: str, default: str = '', commit: bool = True) -> int:
        return self.EnsureKey(section, key, 'str', default, commit=commit)

    def GetKey(self, section: str, key: str, key_type: str, default: Any, commit: bool = True) -> Any:
        return self._settings_db.GetCurrentAccountValue(
            self.widget_key,
            section,
            key,
            key_type,
            default,
            widget_name=self.widget_name,
            description=self.description,
            commit=commit,
        )

    def GetBool(self, section: str, key: str, default: bool = False, commit: bool = True) -> bool:
        return bool(self.GetKey(section, key, 'bool', default, commit=commit))

    def GetInt(self, section: str, key: str, default: int = 0, commit: bool = True) -> int:
        return int(self.GetKey(section, key, 'int', default, commit=commit))

    def GetFloat(self, section: str, key: str, default: float = 0.0, commit: bool = True) -> float:
        return float(self.GetKey(section, key, 'float', default, commit=commit))

    def GetStr(self, section: str, key: str, default: str = '', commit: bool = True) -> str:
        return str(self.GetKey(section, key, 'str', default, commit=commit))

    def SetKey(self, section: str, key: str, key_type: str, value: Any, commit: bool = True) -> int:
        return self._settings_db.SetCurrentAccountValue(
            self.widget_key,
            section,
            key,
            key_type,
            value,
            widget_name=self.widget_name,
            description=self.description,
            commit=commit,
        )

    def SetBool(self, section: str, key: str, value: bool, commit: bool = True) -> int:
        return self.SetKey(section, key, 'bool', value, commit=commit)

    def SetInt(self, section: str, key: str, value: int, commit: bool = True) -> int:
        return self.SetKey(section, key, 'int', value, commit=commit)

    def SetFloat(self, section: str, key: str, value: float, commit: bool = True) -> int:
        return self.SetKey(section, key, 'float', value, commit=commit)

    def SetStr(self, section: str, key: str, value: str, commit: bool = True) -> int:
        return self.SetKey(section, key, 'str', value, commit=commit)

    def DeleteKey(self, section: str, key: str, commit: bool = True) -> int:
        email = self._settings_db._get_current_account_email()
        if not email:
            return 0
        return self._settings_db.DeleteAccountValueByEmail(self.widget_key, email, section, key, commit=commit)

    def GetSection(self, section: str, commit: bool = True) -> list[dict]:
        email = self._settings_db._get_current_account_email()
        if not email:
            return []
        account_id = Account().GetAccountKey(email, commit=commit)
        if account_id is None:
            return []
        return self._settings_db.GetAccountSection(self.widget_key, account_id, section, commit=commit)

    def GetGlobalKey(self, section: str, key: str, key_type: str, default: Any, commit: bool = True) -> Any:
        return self._settings_db.GetGlobalValue(
            self.widget_key,
            section,
            key,
            key_type,
            default,
            widget_name=self.widget_name,
            description=self.description,
            commit=commit,
        )

    def EnsureGlobalKey(self, section: str, key: str, key_type: str, default: Any, commit: bool = True) -> int:
        self.Ensure(commit=commit)
        existing = self._settings_db.GetGlobalEntry(self.widget_key, section, key, commit=commit)
        if existing is not None:
            return int(existing['ID'])
        return self.SetGlobalKey(section, key, key_type, default, commit=commit)

    def EnsureGlobalBool(self, section: str, key: str, default: bool = False, commit: bool = True) -> int:
        return self.EnsureGlobalKey(section, key, 'bool', default, commit=commit)

    def EnsureGlobalInt(self, section: str, key: str, default: int = 0, commit: bool = True) -> int:
        return self.EnsureGlobalKey(section, key, 'int', default, commit=commit)

    def EnsureGlobalFloat(self, section: str, key: str, default: float = 0.0, commit: bool = True) -> int:
        return self.EnsureGlobalKey(section, key, 'float', default, commit=commit)

    def EnsureGlobalStr(self, section: str, key: str, default: str = '', commit: bool = True) -> int:
        return self.EnsureGlobalKey(section, key, 'str', default, commit=commit)

    def GetGlobalBool(self, section: str, key: str, default: bool = False, commit: bool = True) -> bool:
        return bool(self.GetGlobalKey(section, key, 'bool', default, commit=commit))

    def GetGlobalInt(self, section: str, key: str, default: int = 0, commit: bool = True) -> int:
        return int(self.GetGlobalKey(section, key, 'int', default, commit=commit))

    def GetGlobalFloat(self, section: str, key: str, default: float = 0.0, commit: bool = True) -> float:
        return float(self.GetGlobalKey(section, key, 'float', default, commit=commit))

    def GetGlobalStr(self, section: str, key: str, default: str = '', commit: bool = True) -> str:
        return str(self.GetGlobalKey(section, key, 'str', default, commit=commit))

    def SetGlobalKey(self, section: str, key: str, key_type: str, value: Any, commit: bool = True) -> int:
        return self._settings_db.SetGlobalValue(
            self.widget_key,
            section,
            key,
            key_type,
            value,
            widget_name=self.widget_name,
            description=self.description,
            commit=commit,
        )

    def SetGlobalBool(self, section: str, key: str, value: bool, commit: bool = True) -> int:
        return self.SetGlobalKey(section, key, 'bool', value, commit=commit)

    def SetGlobalInt(self, section: str, key: str, value: int, commit: bool = True) -> int:
        return self.SetGlobalKey(section, key, 'int', value, commit=commit)

    def SetGlobalFloat(self, section: str, key: str, value: float, commit: bool = True) -> int:
        return self.SetGlobalKey(section, key, 'float', value, commit=commit)

    def SetGlobalStr(self, section: str, key: str, value: str, commit: bool = True) -> int:
        return self.SetGlobalKey(section, key, 'str', value, commit=commit)

    def DeleteGlobalKey(self, section: str, key: str, commit: bool = True) -> int:
        return self._settings_db.DeleteGlobalValue(self.widget_key, section, key, commit=commit)


@dataclass
class WindowState:
    initialized: bool = False
    x_pos: int = 0
    y_pos: int = 0
    width: int = 0
    height: int = 0
    collapsed: bool = False
    begin_called: bool = False
    begin_returned_true: bool = False


@dataclass
class _CacheEntry:
    """Single cache entry for the account-key or global-key cache."""
    value: str       # serialized value (as stored in DB)
    key_type: str    # 'bool'|'int'|'float'|'str'
    dirty: bool = False
    deleted: bool = False
    db_id: int = 0   # Keys.ID or Globals.ID (0 = not yet in DB)


class Settings(DBMgr):
    """Persistence helpers for the Py4GW settings database.

    Maintains in-memory account-level and global caches.  All get/set/delete
    operations for the current account and global scope hit the cache; the
    database is only touched on the throttle boundary (every 1000 ms) via a
    PyCallback frame callback.

    Public API is unchanged — all method signatures, return types, and the
    WidgetSettings wrapper remain identical.
    """

    DATABASE_NAME = 'Py4GW_Settings'
    WIDGET_TABLE = 'Widget'
    GLOBALS_TABLE = 'Globals'
    KEYS_TABLE = 'Keys'
    FLUSH_THROTTLE_MS = 1000
    GLOBAL_REFRESH_THROTTLE_MS = 3000
    EXTERNAL_STATE_REFRESH_THROTTLE_MS = 10000

    _callback_name = 'Settings.FlushDBCache'
    _settings_instance: Optional['Settings'] = None

    def __new__(cls) -> 'Settings':
        if cls._settings_instance is not None:
            return cls._settings_instance
        instance = cast('Settings', super().__new__(cls, cls.DATABASE_NAME))
        cls._settings_instance = instance
        return instance

    @classmethod
    def Instance(cls) -> 'Settings':
        return cls()

    def __init__(self) -> None:
        super().__init__(self.DATABASE_NAME)
        if getattr(self, '_settings_initialized', False):
            return

        # In-memory window state (unchanged from original)
        self._window_states: dict[str, WindowState] = {}

        # --- Cache dictionaries ---
        self._account_cache: dict[tuple[str, str, str], _CacheEntry] = {}   # (widget_key, section, key) → _CacheEntry
        # (widget_key, section, key) → _CacheEntry
        self._global_cache: dict[tuple[str, str, str], _CacheEntry] = {}
        self._widget_cache: dict[str, int] = {}                              # widget_key → widget_id
        self._widget_id_cache: dict[int, str] = {}
        self._widget_info_cache: dict[str, tuple[str, Optional[str]]] = {}
        self._dirty_account_keys: set[tuple[str, str, str]] = set()
        self._dirty_global_keys: set[tuple[str, str, str]] = set()
        self._widget_cache_loaded: bool = False
        self._global_cache_loaded: bool = False
        self._account_cache_loaded: bool = False

        # --- Widget metadata forwarding ---
        # widget_name/description received from callers; forwarded to EnsureWidget during flush
        self._widget_metadata: dict[str, tuple[Optional[str], Optional[str]]] = {}

        # --- Account identification ---
        self._cached_email: str = ''
        self._cached_hwnd: int = 0
        self._cached_account_id: Optional[int] = None

        # --- Flush machinery ---
        self._flush_timer = ThrottledTimer(self.FLUSH_THROTTLE_MS)
        self._global_refresh_timer = ThrottledTimer(self.GLOBAL_REFRESH_THROTTLE_MS)
        self._external_state_refresh_timer = ThrottledTimer(self.EXTERNAL_STATE_REFRESH_THROTTLE_MS)
        self._flush_failure_count: int = 0       # circuit breaker for persistent errors

        # --- Guarded callback registration (tolerates missing Py4GW runtime) ---
        try:
            self._register_flush_callback()
        except ImportError:
            pass

        self._settings_initialized = True

    # ------------------------------------------------------------------
    # Callback management
    # ------------------------------------------------------------------

    def _register_flush_callback(self) -> None:
        """Register the flush callback on Phase.Data / Context.Update (mirrors IniManager)."""
        import PyCallback

        PyCallback.PyCallback.Register(
            self._callback_name,
            PyCallback.Phase.Data,
            self._flush_callback,
            priority=99,
            context=PyCallback.Context.Update,
        )

    @classmethod
    def enable(cls) -> None:
        """Re-register the flush callback (e.g., after disable())."""
        try:
            cls.Instance()._register_flush_callback()
        except ImportError:
            pass

    @classmethod
    def disable(cls) -> None:
        """Remove the flush callback (for testing/shutdown)."""
        try:
            import PyCallback
            PyCallback.PyCallback.RemoveByName(cls._callback_name)
        except ImportError:
            pass

    def _flush_callback(self, *args, **kwargs) -> None:
        """Frame callback: flush locally, refresh globals frequently, refresh account/widget drift separately."""
        if self._flush_timer.IsExpired():
            if self._has_pending_flush() and self._flush_dirty():
                self._global_refresh_timer.Reset()
                self._external_state_refresh_timer.Reset()
            self._flush_timer.Reset()

        
        if self._global_refresh_timer.IsExpired():
            if not self._has_pending_flush():
                self._refresh_global_cache_from_disk()
            self._global_refresh_timer.Reset()
        

        if self._external_state_refresh_timer.IsExpired():
            #print ("Settings external state refresh triggered.")
            if not self._has_pending_flush():
                self._refresh_external_state_from_disk()
            self._external_state_refresh_timer.Reset()
        

    # ------------------------------------------------------------------
    # Cache population
    # ------------------------------------------------------------------

    def _ensure_cache_populated(self) -> None:
        """Populate caches on first access by running one disk refresh."""
        if self._widget_cache_loaded and self._global_cache_loaded and self._account_cache_loaded:
            return
        self._refresh_cache_from_disk()

    def _resolve_current_account_id(self, email: str, hwnd: int) -> Optional[int]:
        account_id: Optional[int] = None

        if email:
            try:
                account_id = Account().GetAccountKey(email)
            except Exception:
                pass

        if account_id is None and hwnd:
            try:
                rows = Account().Select(Account.ACCOUNT_TABLE, where={'HWND': hwnd}, limit=1)
                if rows:
                    account_id = int(rows[0]['ID'])
            except Exception:
                pass

        return account_id

    def _refresh_account_identity(self) -> bool:
        email = self._get_current_account_email()
        hwnd = self._get_current_account_hwnd()
        previous_account_id = self._cached_account_id

        email_changed = email != self._cached_email
        hwnd_changed = hwnd != self._cached_hwnd
        account_context_changed = email_changed or (hwnd_changed and self._cached_hwnd != 0 and hwnd != 0)
        self._cached_email = email
        self._cached_hwnd = hwnd

        resolved_account_id = self._resolve_current_account_id(email, hwnd)
        account_changed = account_context_changed or resolved_account_id != previous_account_id
        if account_changed:
            self._account_cache.clear()
            self._dirty_account_keys.clear()
            self._account_cache_loaded = False
        self._cached_account_id = resolved_account_id
        return account_changed

    def _build_widget_snapshot(
        self,
        widget_rows: list[dict],
    ) -> tuple[dict[str, int], dict[int, str], dict[str, tuple[str, Optional[str]]]]:
        widget_cache: dict[str, int] = {}
        widget_id_cache: dict[int, str] = {}
        widget_info_cache: dict[str, tuple[str, Optional[str]]] = {}
        for row in widget_rows:
            wk = self._normalize_text(row['Key'] or '')
            if not wk:
                continue
            wid = int(row['ID'])
            widget_cache[wk] = wid
            widget_id_cache[wid] = wk
            widget_info_cache[wk] = (
                self._normalize_text(row['Name'] or wk),
                row['Description'],
            )
        return widget_cache, widget_id_cache, widget_info_cache

    def _refresh_widget_cache_from_disk(self) -> None:
        try:
            start = perf_counter()
            widget_rows = self.Select(self.WIDGET_TABLE)
            widget_cache, widget_id_cache, widget_info_cache = self._build_widget_snapshot(widget_rows)
            self._widget_cache = widget_cache
            self._widget_id_cache = widget_id_cache
            self._widget_info_cache = widget_info_cache
            self._widget_cache_loaded = True
            elapsed_ms = (perf_counter() - start) * 1000
            #print(f'[Settings][refresh_widget_cache] rows={len(widget_rows)} loaded={len(widget_cache)} elapsed_ms={elapsed_ms:.2f}')
        except Exception:
            pass

    def _build_value_snapshot(
        self,
        rows: list[dict],
    ) -> tuple[dict[tuple[str, str, str], _CacheEntry], set[int]]:
        snapshot: dict[tuple[str, str, str], _CacheEntry] = {}
        missing_widget_ids: set[int] = set()
        for row in rows:
            widget_id = int(row['WidgetID'])
            wkey = self._widget_id_cache.get(widget_id)
            if wkey is None:
                missing_widget_ids.add(widget_id)
                continue
            cache_key = (
                wkey,
                self._normalize_text(row['Section'] or ''),
                self._normalize_text(row['Key'] or ''),
            )
            snapshot[cache_key] = _CacheEntry(
                value=row['Value'] or '',
                key_type=row['KeyType'] or 'str',
                dirty=False,
                deleted=False,
                db_id=int(row['ID']),
            )
        return snapshot, missing_widget_ids

    def _merge_global_snapshot(
        self,
        disk_cache: dict[tuple[str, str, str], _CacheEntry],
    ) -> tuple[int, int, int]:
        disk_keys = set(disk_cache)
        cache_keys = set(self._global_cache)
        inserted = 0
        updated = 0
        removed = 0

        for cache_key, disk_entry in disk_cache.items():
            current_entry = self._global_cache.get(cache_key)
            if current_entry is None:
                self._global_cache[cache_key] = disk_entry
                inserted += 1
                continue
            if current_entry.dirty:
                continue
            if (
                current_entry.db_id != disk_entry.db_id
                or current_entry.value != disk_entry.value
                or current_entry.key_type != disk_entry.key_type
                or current_entry.deleted
            ):
                self._global_cache[cache_key] = disk_entry
                updated += 1

        for cache_key in cache_keys - disk_keys:
            current_entry = self._global_cache.get(cache_key)
            if current_entry is not None and not current_entry.dirty:
                del self._global_cache[cache_key]
                removed += 1

        return inserted, updated, removed

    def _refresh_global_cache_from_disk(self) -> None:
        try:
            total_start = perf_counter()
            query_start = perf_counter()
            global_rows = self.Select(self.GLOBALS_TABLE) if self._widget_cache else []
            query_ms = (perf_counter() - query_start) * 1000
            snapshot_start = perf_counter()
            disk_cache, _ = self._build_value_snapshot(global_rows)
            snapshot_ms = (perf_counter() - snapshot_start) * 1000
            merge_start = perf_counter()
            if not self._global_cache_loaded:
                self._global_cache = disk_cache
                inserted = len(disk_cache)
                updated = 0
                removed = 0
            else:
                inserted, updated, removed = self._merge_global_snapshot(disk_cache)
            self._global_cache_loaded = True
            merge_ms = (perf_counter() - merge_start) * 1000
            total_ms = (perf_counter() - total_start) * 1000
            """
            print(
                f'[Settings][refresh_global_cache] rows={len(global_rows)} '
                f'mapped={len(disk_cache)} cache_size={len(self._global_cache)} '
                f'inserted={inserted} updated={updated} removed={removed} '
                f'query_ms={query_ms:.2f} snapshot_ms={snapshot_ms:.2f} merge_ms={merge_ms:.2f} total_ms={total_ms:.2f}'
            )
            """
        except Exception:
            pass

    def _refresh_account_cache_from_disk(self) -> None:
        try:
            total_start = perf_counter()
            account_cache: dict[tuple[str, str, str], _CacheEntry] = {}
            if self._cached_account_id is not None and self._widget_cache:
                query_start = perf_counter()
                keys_rows = self.Select(self.KEYS_TABLE, where={'AccountID': self._cached_account_id})
                query_ms = (perf_counter() - query_start) * 1000
                snapshot_start = perf_counter()
                account_cache, _ = self._build_value_snapshot(keys_rows)
                snapshot_ms = (perf_counter() - snapshot_start) * 1000
            else:
                keys_rows = []
                query_ms = 0.0
                snapshot_ms = 0.0
            self._account_cache = account_cache
            self._account_cache_loaded = True
            total_ms = (perf_counter() - total_start) * 1000
            """
            print(
                f'[Settings][refresh_account_cache] account_id={self._cached_account_id} '
                f'rows={len(keys_rows)} mapped={len(account_cache)} '
                f'query_ms={query_ms:.2f} snapshot_ms={snapshot_ms:.2f} total_ms={total_ms:.2f}'
            )
            """
        except Exception:
            pass

    def _refresh_external_state_from_disk(self) -> None:
        """Refresh account-key rows for the current cached account only."""
        #print(f'[Settings][refresh_external_state] account_id={self._cached_account_id}')
        self._refresh_account_cache_from_disk()

    def _refresh_cache_from_disk(self) -> None:
        """Refresh caches from disk, loading current-account data only when needed."""
        #print(
        #    f'[Settings][refresh_cache] start widget_loaded={self._widget_cache_loaded} '
        #    f'global_loaded={self._global_cache_loaded} account_loaded={self._account_cache_loaded}'
        #)
        account_changed = self._refresh_account_identity()
        #print(f'[Settings][refresh_cache] account_changed={account_changed} account_id={self._cached_account_id}')

        if not self._widget_cache_loaded:
            #print('[Settings][refresh_cache] refreshing widget cache')
            self._refresh_widget_cache_from_disk()
        if not self._global_cache_loaded:
            #print('[Settings][refresh_cache] refreshing global cache')
            self._refresh_global_cache_from_disk()
        if account_changed or not self._account_cache_loaded:
            #print('[Settings][refresh_cache] refreshing account cache')
            self._refresh_account_cache_from_disk()

    def _resolve_widget_key(self, widget_id: int) -> Optional[str]:
        """Reverse-lookup widget_key from widget_id using _widget_cache."""
        return self._widget_id_cache.get(int(widget_id))

    def _resolve_widget_id(self, widget_key: str, commit: bool = False) -> int:
        """Resolve widget_id from widget_key, using cache first, then direct DB."""
        wid = self._widget_cache.get(widget_key)
        if wid is not None:
            return wid
        # Fall back to direct DB (widget-table methods stay direct)
        wid = self.EnsureWidget(widget_key, commit=commit)
        if wid:
            resolved = int(wid)
            self._widget_cache[widget_key] = resolved
            self._widget_id_cache[resolved] = widget_key
        return int(wid) if wid else 0

    # ------------------------------------------------------------------
    # Widget metadata tracking (minimal — forwarded to EnsureWidget at flush)
    # ------------------------------------------------------------------

    def _store_widget_metadata(
        self, widget_key: str, widget_name: Optional[str], description: Optional[str]
    ) -> None:
        """Record widget metadata for forwarding to EnsureWidget during flush."""
        if widget_name is not None or description is not None:
            nwk = self._normalize_text(widget_key)
            normalized_name = self._normalize_text(widget_name) if widget_name is not None else None
            known = self._widget_info_cache.get(nwk)

            if known is not None:
                known_name, known_description = known
                name_matches = normalized_name is None or normalized_name == known_name
                description_matches = description is None or description == known_description
                if name_matches and description_matches:
                    return

            pending = self._widget_metadata.get(nwk)
            if pending is not None:
                pending_name, pending_description = pending
                name_matches = normalized_name is None or normalized_name == pending_name
                description_matches = description is None or description == pending_description
                if name_matches and description_matches:
                    return

            was_idle = not self._has_pending_flush()
            effective_name = normalized_name
            if effective_name is None:
                if pending is not None and pending[0] is not None:
                    effective_name = pending[0]
                elif known is not None:
                    effective_name = known[0]
                else:
                    effective_name = nwk

            effective_description = description
            if effective_description is None:
                if pending is not None:
                    effective_description = pending[1]
                elif known is not None:
                    effective_description = known[1]

            self._widget_metadata[nwk] = (effective_name, effective_description)
            if was_idle:
                self._flush_timer.Reset()

    def _mark_dirty(
        self,
        cache_key: tuple[str, str, str],
        entry: _CacheEntry,
        dirty_keys: set[tuple[str, str, str]],
    ) -> None:
        was_idle = not self._has_pending_flush()
        entry.dirty = True
        dirty_keys.add(cache_key)
        if was_idle:
            self._flush_timer.Reset()

    def _has_pending_flush(self) -> bool:
        """
        if self._widget_metadata:
            print(f"Pending widget metadata: {self._widget_metadata}")
        if self._dirty_account_keys:
            print(f"Pending account keys: {self._dirty_account_keys}")
        if self._dirty_global_keys:
            print(f"Pending global keys: {self._dirty_global_keys}")
        """    
        return bool(self._widget_metadata or self._dirty_account_keys or self._dirty_global_keys)

    # ------------------------------------------------------------------
    # Flush
    # ------------------------------------------------------------------

    def _flush_dirty(self) -> bool:
        """Flush all dirty cache entries in a single transaction.

        Pipeline:
          1. Forward accumulated widget metadata to EnsureWidget.
          2. For each dirty account-cache entry: DELETE/UPDATE/INSERT as needed.
          3. Same for global-cache entries.
          4. Single BeginTransaction/EndTransaction wrapping all operations.

        Uses a local dedup dict for widget_id resolution to avoid redundant
        EnsureWidget calls.  Includes a circuit breaker: 3 consecutive flush
        failures → clear all dirty flags to prevent infinite error loops.
        """
        # Forward widget metadata (before the dirty check — metadata may be the only change)
        # S3: EnsureWidget handles both widget existence and metadata; skip redundant _resolve_widget_id.
        # Circuit breaker: after 3 consecutive failures, clear dirty flags to break error loop
        if self._flush_failure_count >= 3:
            for entry in self._account_cache.values():
                entry.dirty = False
            for entry in self._global_cache.values():
                entry.dirty = False
            self._dirty_account_keys.clear()
            self._dirty_global_keys.clear()
            self._widget_metadata.clear()
            self._flush_failure_count = 0
            self._flush_timer.Reset()
            return False

        # Local dedup dict for widget_id lookups within this flush
        flush_widget_ids: dict[str, int] = {}

        def _get_widget_id(wkey: str) -> int:
            if wkey not in flush_widget_ids:
                flush_widget_ids[wkey] = self._resolve_widget_id(wkey, commit=False)
            return flush_widget_ids[wkey]

        self.BeginTransaction()
        try:
            for widget_key, (name, desc) in list(self._widget_metadata.items()):
                if name is None and desc is None:
                    continue
                wid = self.EnsureWidget(widget_key, name=name, description=desc, commit=False)
                if wid:
                    resolved = int(wid)
                    self._widget_cache[widget_key] = resolved
                    self._widget_id_cache[resolved] = widget_key
                    self._widget_info_cache[widget_key] = (
                        self._normalize_text(name or widget_key),
                        desc,
                    )
                    flush_widget_ids[widget_key] = resolved

            # --- Flush account cache (Keys table) ---
            processed_account_keys: list[tuple[str, str, str]] = []
            for cache_key in list(self._dirty_account_keys):
                entry = self._account_cache.get(cache_key)
                if entry is None:
                    processed_account_keys.append(cache_key)
                    continue

                widget_key, section, key = cache_key

                if entry.deleted:
                    if entry.db_id != 0:
                        self.Delete(self.KEYS_TABLE, where={'ID': entry.db_id}, commit=False)
                    # Optimisation: db_id==0 entries were never persisted — just remove
                    del self._account_cache[cache_key]
                    processed_account_keys.append(cache_key)
                    continue

                widget_id = _get_widget_id(widget_key)

                if entry.db_id != 0:
                    self.Update(
                        self.KEYS_TABLE,
                        {'KeyType': entry.key_type, 'Value': entry.value},
                        where={'ID': entry.db_id},
                        commit=False,
                    )
                else:
                    if self._cached_account_id is None:
                        self._cached_account_id = self._resolve_current_account_id(
                            self._get_current_account_email(),
                            self._get_current_account_hwnd(),
                        )
                    if self._cached_account_id is None:
                        continue
                    new_id = self.Insert(
                        self.KEYS_TABLE,
                        ['WidgetID', 'AccountID', 'Section', 'Key', 'KeyType', 'Value'],
                        [widget_id, self._cached_account_id, section, key, entry.key_type, entry.value],
                        commit=False,
                    )
                    entry.db_id = int(new_id)

                entry.dirty = False
                processed_account_keys.append(cache_key)

            # --- Flush global cache (Globals table) ---
            processed_global_keys: list[tuple[str, str, str]] = []
            for cache_key in list(self._dirty_global_keys):
                entry = self._global_cache.get(cache_key)
                if entry is None:
                    processed_global_keys.append(cache_key)
                    continue

                widget_key, section, key = cache_key

                if entry.deleted:
                    if entry.db_id != 0:
                        self.Delete(self.GLOBALS_TABLE, where={'ID': entry.db_id}, commit=False)
                    del self._global_cache[cache_key]
                    processed_global_keys.append(cache_key)
                    continue

                widget_id = _get_widget_id(widget_key)

                if entry.db_id != 0:
                    self.Update(
                        self.GLOBALS_TABLE,
                        {'KeyType': entry.key_type, 'Value': entry.value},
                        where={'ID': entry.db_id},
                        commit=False,
                    )
                else:
                    new_id = self.Insert(
                        self.GLOBALS_TABLE,
                        ['WidgetID', 'Section', 'Key', 'KeyType', 'Value'],
                        [widget_id, section, key, entry.key_type, entry.value],
                        commit=False,
                    )
                    entry.db_id = int(new_id)

                entry.dirty = False
                processed_global_keys.append(cache_key)

            self.EndTransaction('COMMIT')
            for cache_key in processed_account_keys:
                self._dirty_account_keys.discard(cache_key)
            for cache_key in processed_global_keys:
                self._dirty_global_keys.discard(cache_key)
            self._widget_metadata.clear()
            self._flush_failure_count = 0  # reset on success
            return True

        except Exception:
            self._flush_failure_count += 1
            try:
                self.EndTransaction('ROLLBACK')
            except Exception:
                pass
            raise

    # ------------------------------------------------------------------
    # Account identification helpers
    # ------------------------------------------------------------------

    def _get_current_account_hwnd(self) -> int:
        """Return the current game window handle, or 0 if unavailable."""
        try:
            import Py4GW
            return int(Py4GW.Console.get_gw_window_handle() or 0)
        except Exception:
            return 0

    # ------------------------------------------------------------------
    # Unchanged helpers
    # ------------------------------------------------------------------

    def ForWidget(self, widget_key: str, widget_name: Optional[str] = None, description: Optional[str] = None) -> WidgetSettings:
        return WidgetSettings(self, widget_key, widget_name, description)

    def _get_window_state(self, widget_key: str) -> WindowState:
        normalized_widget_key = self._normalize_text(widget_key)
        state = self._window_states.get(normalized_widget_key)
        if state is None:
            state = WindowState()
            self._window_states[normalized_widget_key] = state
        return state

    def _normalize_text(self, value: str) -> str:
        return str(value).strip()

    def _normalize_cache_key(self, widget_key: str, section: str, key: str) -> tuple[str, str, str, tuple[str, str, str]]:
        normalized_widget_key = self._normalize_text(widget_key)
        normalized_section = self._normalize_text(section)
        normalized_key = self._normalize_text(key)
        return (
            normalized_widget_key,
            normalized_section,
            normalized_key,
            (normalized_widget_key, normalized_section, normalized_key),
        )

    def _normalize_typed_cache_key(
        self,
        widget_key: str,
        section: str,
        key: str,
        key_type: str,
    ) -> tuple[str, str, str, str, tuple[str, str, str]]:
        normalized_widget_key, normalized_section, normalized_key, cache_key = self._normalize_cache_key(
            widget_key,
            section,
            key,
        )
        return (
            normalized_widget_key,
            normalized_section,
            normalized_key,
            self._normalize_key_type(key_type),
            cache_key,
        )

    def SetFlushThrottle(self, milliseconds: int) -> None:
        self._flush_timer.SetThrottleTime(int(milliseconds))
        self._flush_timer.Reset()

    def SetGlobalRefreshThrottle(self, milliseconds: int) -> None:
        self._global_refresh_timer.SetThrottleTime(int(milliseconds))
        self._global_refresh_timer.Reset()

    def SetExternalStateRefreshThrottle(self, milliseconds: int) -> None:
        self._external_state_refresh_timer.SetThrottleTime(int(milliseconds))
        self._external_state_refresh_timer.Reset()

    def GetFlushThrottle(self) -> int:
        return int(self._flush_timer.throttle_time)

    def GetGlobalRefreshThrottle(self) -> int:
        return int(self._global_refresh_timer.throttle_time)

    def GetExternalStateRefreshThrottle(self) -> int:
        return int(self._external_state_refresh_timer.throttle_time)

    def _normalize_key_type(self, key_type: str) -> str:
        normalized = str(key_type).strip().lower()
        if normalized not in {'bool', 'int', 'float', 'str'}:
            raise ValueError(f"Unsupported key type '{key_type}'. Expected one of: bool, int, float, str.")
        return normalized

    def _serialize_value(self, value: Any, key_type: str) -> str:
        normalized = self._normalize_key_type(key_type)
        if normalized == 'bool':
            return '1' if bool(value) else '0'
        if normalized == 'int':
            return str(int(value))
        if normalized == 'float':
            return str(float(value))
        return str(value)

    def _deserialize_value(self, value: str, key_type: str) -> Any:
        normalized = self._normalize_key_type(key_type)
        if normalized == 'bool':
            return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}
        if normalized == 'int':
            return int(value)
        if normalized == 'float':
            return float(value)
        return str(value)

    def _get_current_account_email(self) -> str:
        from ..Player import Player

        return str(Player.GetAccountEmail() or '').strip()

    # ------------------------------------------------------------------
    # Window config (unchanged — transparently benefits from cache)
    # ------------------------------------------------------------------

    def begin_window_config(self, widget_key: str) -> None:
        import PyImGui

        if not widget_key:
            return

        state = self._get_window_state(widget_key)
        state.begin_called = True
        state.begin_returned_true = False

        if state.initialized:
            return

        settings = self.ForWidget(widget_key)
        state.x_pos = settings.GetInt('Window config', 'x', default=0)
        state.y_pos = settings.GetInt('Window config', 'y', default=0)
        state.width = settings.GetInt('Window config', 'width', default=0)
        state.height = settings.GetInt('Window config', 'height', default=0)
        state.collapsed = settings.GetBool('Window config', 'collapsed', default=False)

        PyImGui.set_next_window_pos(state.x_pos, state.y_pos)
        if state.width > 0 and state.height > 0:
            PyImGui.set_next_window_size(state.width, state.height)
        PyImGui.set_next_window_collapsed(state.collapsed, 0)
        state.initialized = True

    def mark_begin_success(self, widget_key: str) -> None:
        if not widget_key:
            return
        self._get_window_state(widget_key).begin_returned_true = True

    def track_window_collapsed(self, widget_key: str, begin_result: bool) -> None:
        if not widget_key:
            return

        state = self._get_window_state(widget_key)
        new_collapsed = not begin_result
        if new_collapsed == state.collapsed:
            return

        state.collapsed = new_collapsed
        self.ForWidget(widget_key).SetBool('Window config', 'collapsed', state.collapsed)

    def end_window_config(self, widget_key: str) -> None:
        import PyImGui

        if not widget_key:
            return

        state = self._get_window_state(widget_key)
        if not state.begin_called or not state.begin_returned_true:
            state.begin_called = False
            state.begin_returned_true = False
            return

        end_pos = PyImGui.get_window_pos()
        end_size = PyImGui.get_window_size()

        new_x = int(end_pos[0])
        new_y = int(end_pos[1])
        new_width = int(end_size[0])
        new_height = int(end_size[1])

        settings = self.ForWidget(widget_key)
        if new_x != state.x_pos:
            state.x_pos = new_x
            settings.SetInt('Window config', 'x', state.x_pos)
        if new_y != state.y_pos:
            state.y_pos = new_y
            settings.SetInt('Window config', 'y', state.y_pos)
        if new_width != state.width:
            state.width = new_width
            settings.SetInt('Window config', 'width', state.width)
        if new_height != state.height:
            state.height = new_height
            settings.SetInt('Window config', 'height', state.height)

        state.begin_called = False
        state.begin_returned_true = False

    # ------------------------------------------------------------------
    # Widget-table methods (unchanged — direct DB, no cache)
    # ------------------------------------------------------------------

    def _get_widget_row(self, widget_key: str, commit: bool = True) -> Optional[dict]:
        return self.GetFirstEntry(self.WIDGET_TABLE, 'Key', self._normalize_text(widget_key), commit=commit)

    def _get_global_row(self, widget_id: int, section: str, key: str, commit: bool = True) -> Optional[dict]:
        rows = self.Select(
            self.GLOBALS_TABLE,
            where={
                'WidgetID': int(widget_id),
                'Section': self._normalize_text(section),
                'Key': self._normalize_text(key),
            },
            limit=1,
            commit=commit,
        )
        return rows[0] if rows else None

    def _get_account_row(self, widget_id: int, account_id: int, section: str, key: str, commit: bool = True) -> Optional[dict]:
        rows = self.Select(
            self.KEYS_TABLE,
            where={
                'WidgetID': int(widget_id),
                'AccountID': int(account_id),
                'Section': self._normalize_text(section),
                'Key': self._normalize_text(key),
            },
            limit=1,
            commit=commit,
        )
        return rows[0] if rows else None

    def RegisterWidget(self, widget_key: str, name: str, description: Optional[str] = None, commit: bool = True) -> int:
        nwk = self._normalize_text(widget_key)
        existing = self._get_widget_row(widget_key, commit=commit)
        if existing is not None:
            wid = int(existing['ID'])
            self._widget_cache[nwk] = wid  # M3: keep widget cache in sync
            self._widget_id_cache[wid] = nwk
            self._widget_info_cache[nwk] = (
                self._normalize_text(existing['Name'] or nwk),
                existing.get('Description'),
            )
            return wid
        wid = self.Insert(
            self.WIDGET_TABLE,
            ['Key', 'Name', 'Description'],
            [nwk, self._normalize_text(name), description],
            commit=commit,
        )
        self._widget_cache[nwk] = int(wid)  # M3: cache newly inserted widget
        self._widget_id_cache[int(wid)] = nwk
        self._widget_info_cache[nwk] = (self._normalize_text(name), description)
        return wid

    def EnsureWidget(self, widget_key: str, name: Optional[str] = None, description: Optional[str] = None, commit: bool = True) -> int:
        nwk = self._normalize_text(widget_key)
        existing = self._get_widget_row(widget_key, commit=commit)
        if existing is not None:
            updates: dict[str, Any] = {}
            if name is not None and self._normalize_text(name) != existing['Name']:
                updates['Name'] = self._normalize_text(name)
            if description is not None and description != existing.get('Description'):
                updates['Description'] = description
            if updates:
                self.Update(self.WIDGET_TABLE, updates, where={'ID': int(existing['ID'])}, commit=commit)
            wid = int(existing['ID'])
            self._widget_cache[nwk] = wid  # M3: keep widget cache in sync
            self._widget_id_cache[wid] = nwk
            resolved_name = self._normalize_text(name) if name is not None else self._normalize_text(existing['Name'] or nwk)
            resolved_description = description if description is not None else existing.get('Description')
            self._widget_info_cache[nwk] = (resolved_name, resolved_description)
            return wid
        return self.RegisterWidget(widget_key, name or nwk, description, commit=commit)

    def GetWidgetData(self, widget_key: str, commit: bool = True) -> Optional[dict]:
        return self._get_widget_row(widget_key, commit=commit)

    def GetWidgetDataByID(self, widget_id: int, commit: bool = True) -> Optional[dict]:
        return self.GetFirstEntry(self.WIDGET_TABLE, 'ID', int(widget_id), commit=commit)

    def GetAllWidgets(self, commit: bool = True) -> list[dict]:
        return self.Select(self.WIDGET_TABLE, order_by='Key', commit=commit)

    def SetWidgetData(self, widget_key: str, data: dict, commit: bool = True) -> int:
        return self.Update(self.WIDGET_TABLE, data, where={'Key': self._normalize_text(widget_key)}, commit=commit)

    def DeleteWidget(self, widget_key: str, commit: bool = True) -> int:
        return self.Delete(self.WIDGET_TABLE, where={'Key': self._normalize_text(widget_key)}, commit=commit)

    # ==================================================================
    # Global-value methods (cache-backed)
    # ==================================================================

    def SetGlobalValue(
        self,
        widget_key: str,
        section: str,
        key: str,
        key_type: str,
        value: Any,
        widget_name: Optional[str] = None,
        description: Optional[str] = None,
        commit: bool = True,
    ) -> int:
        self._ensure_cache_populated()
        self._store_widget_metadata(widget_key, widget_name, description)
        normalized_widget_key, normalized_section, normalized_key, normalized_type, cache_key = self._normalize_typed_cache_key(
            widget_key,
            section,
            key,
            key_type,
        )
        serialized = self._serialize_value(value, normalized_type)

        entry = self._global_cache.get(cache_key)
        if entry is not None:
            if entry.value == serialized and not entry.deleted:
                return entry.db_id
            entry.value = serialized
            entry.key_type = normalized_type
            self._mark_dirty(cache_key, entry, self._dirty_global_keys)
            entry.deleted = False
            return entry.db_id
        else:
            # M1: Check DB before creating db_id=0 to avoid UNIQUE violation on flush
            widget_id = self._resolve_widget_id(normalized_widget_key, commit=commit)
            if widget_id:
                db_row = self._get_global_row(widget_id, normalized_section, normalized_key, commit=commit)
                if db_row is not None:
                    entry = _CacheEntry(
                        value=serialized,
                        key_type=normalized_type,
                        dirty=True,   # value changed — mark dirty
                        deleted=False,
                        db_id=int(db_row['ID']),
                    )
                    self._global_cache[cache_key] = entry
                    self._mark_dirty(cache_key, entry, self._dirty_global_keys)
                    return entry.db_id
            entry = _CacheEntry(value=serialized, key_type=normalized_type, dirty=False, deleted=False, db_id=0)
            self._global_cache[cache_key] = entry
            self._mark_dirty(cache_key, entry, self._dirty_global_keys)
            return 0

    def GetGlobalValue(
        self,
        widget_key: str,
        section: str,
        key: str,
        key_type: str,
        default: Any,
        widget_name: Optional[str] = None,
        description: Optional[str] = None,
        commit: bool = True,
    ) -> Any:
        self._ensure_cache_populated()
        normalized_widget_key, normalized_section, normalized_key, normalized_type, cache_key = self._normalize_typed_cache_key(
            widget_key,
            section,
            key,
            key_type,
        )

        entry = self._global_cache.get(cache_key)
        if entry is None or entry.deleted:
            # M1: Check DB before creating db_id=0 to avoid UNIQUE violation on flush
            widget_id = self._resolve_widget_id(normalized_widget_key, commit=commit)
            if widget_id:
                db_row = self._get_global_row(widget_id, normalized_section, normalized_key, commit=commit)
                if db_row is not None:
                    entry = _CacheEntry(
                        value=db_row['Value'] or '',
                        key_type=db_row['KeyType'] or 'str',
                        dirty=False,
                        deleted=False,
                        db_id=int(db_row['ID']),
                    )
                    self._global_cache[cache_key] = entry
                    return self._deserialize_value(entry.value, entry.key_type)
            serialized = self._serialize_value(default, normalized_type)
            entry = _CacheEntry(value=serialized, key_type=normalized_type, dirty=False, deleted=False, db_id=0)
            self._global_cache[cache_key] = entry
            return default
        return self._deserialize_value(entry.value, entry.key_type)

    def GetGlobalEntry(self, widget_key: str, section: str, key: str, commit: bool = True) -> Optional[dict]:
        self._ensure_cache_populated()
        normalized_widget_key, normalized_section, normalized_key, cache_key = self._normalize_cache_key(widget_key, section, key)
        entry = self._global_cache.get(cache_key)
        if entry is None or entry.deleted:
            # Fallback to direct DB for entries not in cache (e.g. widget not loaded yet)
            widget = self._get_widget_row(widget_key, commit=commit)
            if widget is None:
                return None
            return self._get_global_row(int(widget['ID']), section, key, commit=commit)
        widget_id = self._widget_cache.get(normalized_widget_key, 0)
        return {
            'ID': entry.db_id,
            'WidgetID': widget_id,
            'Section': normalized_section,
            'Key': normalized_key,
            'KeyType': entry.key_type,
            'Value': entry.value,
        }

    def DeleteGlobalValue(self, widget_key: str, section: str, key: str, commit: bool = True) -> int:
        self._ensure_cache_populated()
        normalized_widget_key, normalized_section, normalized_key, cache_key = self._normalize_cache_key(
            widget_key,
            section,
            key,
        )
        entry = self._global_cache.get(cache_key)
        if entry is not None and not entry.deleted:
            if entry.db_id == 0:
                # Never persisted — just remove from cache
                del self._global_cache[cache_key]
            else:
                entry.deleted = True
                self._mark_dirty(cache_key, entry, self._dirty_global_keys)
            return 1
        return 0

    def GetGlobalSection(self, widget_key: str, section: str, commit: bool = True) -> list[dict]:
        self._ensure_cache_populated()
        normalized_widget_key = self._normalize_text(widget_key)
        normalized_section = self._normalize_text(section)

        # M2: Fallback to direct DB if cache is empty (population failed)
        if not self._global_cache_loaded:
            widget = self._get_widget_row(widget_key, commit=commit)
            if widget is None:
                return []
            return self.Select(
                self.GLOBALS_TABLE,
                where={
                    'WidgetID': int(widget['ID']),
                    'Section': normalized_section,
                },
                order_by='Key',
                commit=commit,
            )

        result: list[dict] = []
        for (wk, sec, k), entry in self._global_cache.items():
            if wk == normalized_widget_key and sec == normalized_section and not entry.deleted:
                widget_id = self._widget_cache.get(wk, 0)
                result.append({
                    'ID': entry.db_id,
                    'WidgetID': widget_id,
                    'Section': sec,
                    'Key': k,
                    'KeyType': entry.key_type,
                    'Value': entry.value,
                })
        result.sort(key=lambda r: r['Key'])
        return result

    # ==================================================================
    # Account-value methods (cache-backed for current account, direct DB for others)
    # ==================================================================

    def _is_current_account(self, account_id: int) -> bool:
        """Return True if *account_id* matches the currently cached account."""
        if self._cached_account_id is None:
            return False
        return int(account_id) == self._cached_account_id

    def SetAccountValue(
        self,
        widget_key: str,
        account_id: int,
        section: str,
        key: str,
        key_type: str,
        value: Any,
        widget_name: Optional[str] = None,
        description: Optional[str] = None,
        commit: bool = True,
    ) -> int:
        self._ensure_cache_populated()
        if self._is_current_account(int(account_id)):
            self._store_widget_metadata(widget_key, widget_name, description)
            normalized_widget_key, normalized_section, normalized_key, normalized_type, cache_key = self._normalize_typed_cache_key(
                widget_key,
                section,
                key,
                key_type,
            )
            serialized = self._serialize_value(value, normalized_type)

            entry = self._account_cache.get(cache_key)
            if entry is not None:
                if entry.value == serialized and not entry.deleted:
                    return entry.db_id
                entry.value = serialized
                entry.key_type = normalized_type
                self._mark_dirty(cache_key, entry, self._dirty_account_keys)
                entry.deleted = False
                return entry.db_id
            else:
                entry = _CacheEntry(value=serialized, key_type=normalized_type, dirty=False, deleted=False, db_id=0)
                self._account_cache[cache_key] = entry
                self._mark_dirty(cache_key, entry, self._dirty_account_keys)
                return 0

        # Non-current account — direct DB fallback
        widget_id = self.EnsureWidget(widget_key, widget_name, description, commit=commit)
        normalized_section = self._normalize_text(section)
        normalized_key = self._normalize_text(key)
        normalized_type = self._normalize_key_type(key_type)
        serialized_value = self._serialize_value(value, normalized_type)
        existing = self._get_account_row(widget_id, int(account_id), normalized_section, normalized_key, commit=commit)
        if existing is None:
            return self.Insert(
                self.KEYS_TABLE,
                ['WidgetID', 'AccountID', 'Section', 'Key', 'KeyType', 'Value'],
                [widget_id, int(account_id), normalized_section, normalized_key, normalized_type, serialized_value],
                commit=commit,
            )
        self.Update(
            self.KEYS_TABLE,
            {'KeyType': normalized_type, 'Value': serialized_value},
            where={'ID': int(existing['ID'])},
            commit=commit,
        )
        return int(existing['ID'])

    def SetAccountValueByEmail(
        self,
        widget_key: str,
        email: str,
        section: str,
        key: str,
        key_type: str,
        value: Any,
        widget_name: Optional[str] = None,
        description: Optional[str] = None,
        commit: bool = True,
    ) -> int:
        account_id = Account().GetAccountKey(email, commit=commit)
        if account_id is None:
            raise ValueError(f"Account '{email}' is not registered in Py4GW_Accounts.")
        return self.SetAccountValue(
            widget_key,
            account_id,
            section,
            key,
            key_type,
            value,
            widget_name=widget_name,
            description=description,
            commit=commit,
        )

    def GetAccountValue(
        self,
        widget_key: str,
        account_id: int,
        section: str,
        key: str,
        key_type: str,
        default: Any,
        widget_name: Optional[str] = None,
        description: Optional[str] = None,
        commit: bool = True,
    ) -> Any:
        self._ensure_cache_populated()
        if self._is_current_account(int(account_id)):
            normalized_widget_key, normalized_section, normalized_key, normalized_type, cache_key = self._normalize_typed_cache_key(
                widget_key,
                section,
                key,
                key_type,
            )

            entry = self._account_cache.get(cache_key)
            if entry is None or entry.deleted:
                serialized = self._serialize_value(default, normalized_type)
                entry = _CacheEntry(value=serialized, key_type=normalized_type, dirty=False, deleted=False, db_id=0)
                self._account_cache[cache_key] = entry
                return default
            return self._deserialize_value(entry.value, entry.key_type)

        # Non-current account — direct DB fallback
        widget_id = self.EnsureWidget(widget_key, widget_name, description, commit=commit)
        row = self._get_account_row(widget_id, int(account_id), section, key, commit=commit)
        if row is None:
            # S4: Insert directly instead of delegating to SetAccountValue
            # (avoids redundant EnsureWidget + _get_account_row calls)
            normalized_type = self._normalize_key_type(key_type)
            serialized_value = self._serialize_value(default, normalized_type)
            row_id = self.Insert(
                self.KEYS_TABLE,
                ['WidgetID', 'AccountID', 'Section', 'Key', 'KeyType', 'Value'],
                [widget_id, int(account_id), self._normalize_text(section), self._normalize_text(key), normalized_type, serialized_value],
                commit=commit,
            )
            row = {
                'ID': int(row_id),
                'WidgetID': int(widget_id),
                'AccountID': int(account_id),
                'Section': self._normalize_text(section),
                'Key': self._normalize_text(key),
                'KeyType': normalized_type,
                'Value': serialized_value,
            }
        return self._deserialize_value(row['Value'], row['KeyType'])

    def GetAccountValueByEmail(
        self,
        widget_key: str,
        email: str,
        section: str,
        key: str,
        key_type: str,
        default: Any,
        widget_name: Optional[str] = None,
        description: Optional[str] = None,
        commit: bool = True,
    ) -> Any:
        account_id = Account().GetAccountKey(email, commit=commit)
        if account_id is None:
            raise ValueError(f"Account '{email}' is not registered in Py4GW_Accounts.")
        return self.GetAccountValue(
            widget_key,
            account_id,
            section,
            key,
            key_type,
            default,
            widget_name=widget_name,
            description=description,
            commit=commit,
        )

    # ==================================================================
    # Current-account convenience methods (cache-backed)
    # ==================================================================

    def SetCurrentAccountValue(
        self,
        widget_key: str,
        section: str,
        key: str,
        key_type: str,
        value: Any,
        widget_name: Optional[str] = None,
        description: Optional[str] = None,
        commit: bool = True,
    ) -> int:
        self._ensure_cache_populated()
        if self._cached_account_id is None:
            raise ValueError('Current account email is not available.')
        return self.SetAccountValue(
            widget_key,
            self._cached_account_id,
            section,
            key,
            key_type,
            value,
            widget_name=widget_name,
            description=description,
            commit=commit,
        )

    def GetCurrentAccountValue(
        self,
        widget_key: str,
        section: str,
        key: str,
        key_type: str,
        default: Any,
        widget_name: Optional[str] = None,
        description: Optional[str] = None,
        commit: bool = True,
    ) -> Any:
        self._ensure_cache_populated()
        if self._cached_account_id is None:
            raise ValueError('Current account email is not available.')
        return self.GetAccountValue(
            widget_key,
            self._cached_account_id,
            section,
            key,
            key_type,
            default,
            widget_name=widget_name,
            description=description,
            commit=commit,
        )

    def GetAccountEntry(self, widget_key: str, account_id: int, section: str, key: str, commit: bool = True) -> Optional[dict]:
        self._ensure_cache_populated()
        if self._is_current_account(int(account_id)):
            normalized_widget_key, normalized_section, normalized_key, cache_key = self._normalize_cache_key(
                widget_key,
                section,
                key,
            )
            entry = self._account_cache.get(cache_key)
            if entry is None or entry.deleted:
                return None
            widget_id = self._widget_cache.get(normalized_widget_key, 0)
            return {
                'ID': entry.db_id,
                'WidgetID': widget_id,
                'AccountID': self._cached_account_id or 0,
                'Section': normalized_section,
                'Key': normalized_key,
                'KeyType': entry.key_type,
                'Value': entry.value,
            }

        # Non-current account — direct DB fallback
        widget = self._get_widget_row(widget_key, commit=commit)
        if widget is None:
            return None
        return self._get_account_row(int(widget['ID']), int(account_id), section, key, commit=commit)

    def GetCurrentAccountEntry(self, widget_key: str, section: str, key: str, commit: bool = True) -> Optional[dict]:
        self._ensure_cache_populated()
        if self._cached_account_id is None:
            return None
        return self.GetAccountEntry(widget_key, self._cached_account_id, section, key, commit=commit)

    def DeleteAccountValue(self, widget_key: str, account_id: int, section: str, key: str, commit: bool = True) -> int:
        self._ensure_cache_populated()
        if self._is_current_account(int(account_id)):
            normalized_widget_key, normalized_section, normalized_key, cache_key = self._normalize_cache_key(
                widget_key,
                section,
                key,
            )
            entry = self._account_cache.get(cache_key)
            if entry is not None and not entry.deleted:
                if entry.db_id == 0:
                    # Never persisted — just remove from cache
                    del self._account_cache[cache_key]
                else:
                    entry.deleted = True
                    self._mark_dirty(cache_key, entry, self._dirty_account_keys)
                return 1
            return 0

        # Non-current account — direct DB
        widget = self._get_widget_row(widget_key, commit=commit)
        if widget is None:
            return 0
        return self.Delete(
            self.KEYS_TABLE,
            where={
                'WidgetID': int(widget['ID']),
                'AccountID': int(account_id),
                'Section': self._normalize_text(section),
                'Key': self._normalize_text(key),
            },
            commit=commit,
        )

    def DeleteAccountValueByEmail(self, widget_key: str, email: str, section: str, key: str, commit: bool = True) -> int:
        account_id = Account().GetAccountKey(email, commit=commit)
        if account_id is None:
            return 0
        return self.DeleteAccountValue(widget_key, account_id, section, key, commit=commit)

    def GetAccountSection(self, widget_key: str, account_id: int, section: str, commit: bool = True) -> list[dict]:
        self._ensure_cache_populated()
        if self._is_current_account(int(account_id)):
            normalized_widget_key = self._normalize_text(widget_key)
            normalized_section = self._normalize_text(section)

            # M2: Fallback to direct DB if cache is empty (population failed)
            if not self._account_cache_loaded:
                widget = self._get_widget_row(widget_key, commit=commit)
                if widget is None:
                    return []
                return self.Select(
                    self.KEYS_TABLE,
                    where={
                        'WidgetID': int(widget['ID']),
                        'AccountID': int(account_id),
                        'Section': normalized_section,
                    },
                    order_by='Key',
                    commit=commit,
                )

            result: list[dict] = []
            for (wk, sec, k), entry in self._account_cache.items():
                if wk == normalized_widget_key and sec == normalized_section and not entry.deleted:
                    widget_id = self._widget_cache.get(wk, 0)
                    result.append({
                        'ID': entry.db_id,
                        'WidgetID': widget_id,
                        'AccountID': self._cached_account_id or 0,
                        'Section': sec,
                        'Key': k,
                        'KeyType': entry.key_type,
                        'Value': entry.value,
                    })
            result.sort(key=lambda r: r['Key'])
            return result

        # Non-current account — direct DB
        widget = self._get_widget_row(widget_key, commit=commit)
        if widget is None:
            return []
        return self.Select(
            self.KEYS_TABLE,
            where={
                'WidgetID': int(widget['ID']),
                'AccountID': int(account_id),
                'Section': self._normalize_text(section),
            },
            order_by='Key',
            commit=commit,
        )
