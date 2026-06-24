"""
DBMgr — Py4GW SQL-free Database Manager.

A self-managed SQLite database class that generates all SQL internally.
Users never write SQL — they only provide database names, table names,
column definitions, and values.

Architecture:
    DBMgr('name') — opens database by alias. Path resolved from PRIMARY catalog.
    All operations are open → execute → commit → close (unless in transaction).
    Bootstrap runs once per process: creates PRIMARY, runs setup scripts, self-registers.

Usage:
    db = DBMgr('myapp')
    db.CreateTable('players', [('id', 'INTEGER', 'PRIMARY KEY'), ('name', 'TEXT', 'NOT NULL')])
    db.Insert('players', ['id', 'name'], [1, 'Apo'])
    rows = db.Select('players', where={'name': 'Apo'})
"""

import json
import os
import re
import shutil
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union


MODULE_NAME = "DBMgr"
_PRIMARY_ALIAS = "PRIMARY"
_PRIMARY_DB_FILENAME = "Py4GW_Internals.db"
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_PRIMARY_SETUP_RE = re.compile(r"^\d+_")

# ---------------------------------------------------------------------------
# Module-level helpers (no Py4GW dependency at import time)
# ---------------------------------------------------------------------------


def _get_projects_path() -> Path:
    """Resolve the base path for database storage.

    Tries Py4GW.Console.get_projects_path() first.
    Falls back to os.getcwd() if Py4GW is not available.
    """
    try:
        import Py4GW

        if hasattr(Py4GW, "Console") and hasattr(Py4GW.Console, "get_projects_path"):
            path = Py4GW.Console.get_projects_path()
            if path:
                return Path(path).resolve()
    except Exception:
        pass
    return Path(os.getcwd()).resolve()


def _get_data_path() -> Path:
    """Resolve the default storage root for DBMgr-managed files."""
    return (_get_projects_path() / "data").resolve()


# ---------------------------------------------------------------------------
# DBMgr
# ---------------------------------------------------------------------------


class DBMgr:
    """Central authority for all SQLite database creation, access, and maintenance.

    Position-based: each instance is bound to ONE database, looked up by name
    from the PRIMARY catalog. All operations generate SQL internally — the user
    never writes raw SQL (except via the ``Execute()`` failsafe).

    Construction:
        db = DBMgr('myapp')    # opens database registered under 'myapp'

    Lifecycle:
        db.Register('myapp', 'myapp.db')    # register a new database
        db.Unregister('myapp')              # remove from catalog
        db.List()                           # {name: path, ...}
        db.Has('myapp')                     # True/False
    """

    # -----------------------------------------------------------------------
    # Class-level bootstrap state
    # -----------------------------------------------------------------------

    _bootstrapped: bool = False
    _instance: Optional["DBMgr"] = None
    _projects_path: Optional[Path] = None
    _data_path: Optional[Path] = None
    _primary_path: Optional[Path] = None
    _primary_catalog_ensured: bool = False
    _catalog_consistent: bool = False
    _read_connections: dict[str, sqlite3.Connection] = {}
    _ensured_database_paths: set[str] = set()

    def __new__(cls, name: str) -> "DBMgr":
        """Return the single process-wide DBMgr instance."""
        cls._bootstrap_once()
        cls._validate_identifier(name)
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def _require_projects_path(cls) -> Path:
        """Return the bootstrapped projects path or raise if unavailable."""
        if cls._projects_path is None:
            raise RuntimeError("DBMgr bootstrap did not initialize the projects path.")
        return cls._projects_path

    @classmethod
    def _require_data_path(cls) -> Path:
        """Return the bootstrapped DBMgr data path or raise if unavailable."""
        if cls._data_path is None:
            raise RuntimeError("DBMgr bootstrap did not initialize the DBMgr data path.")
        return cls._data_path

    @classmethod
    def _require_primary_path(cls) -> Path:
        """Return the bootstrapped PRIMARY database path or raise if unavailable."""
        if cls._primary_path is None:
            raise RuntimeError("DBMgr bootstrap did not initialize the PRIMARY database path.")
        cls._ensure_primary_catalog()
        return cls._primary_path

    @classmethod
    def _invalidate_catalog_cache(cls) -> None:
        """Clear process-local catalog/bootstrap verification flags."""
        cls._primary_catalog_ensured = False
        cls._catalog_consistent = False

    @classmethod
    def _register_primary_catalog_entry(cls) -> None:
        """Ensure PRIMARY is present in its own catalog."""
        pc = sqlite3.connect(str(cls._require_primary_path_raw()))
        try:
            pc.row_factory = sqlite3.Row
            cls._apply_pragmas(pc)
            pc.execute(
                "INSERT OR IGNORE INTO databases (name, path) VALUES (?, ?)",
                (_PRIMARY_ALIAS, str(cls._require_primary_path_raw())),
            )
            pc.commit()
        finally:
            pc.close()

    @classmethod
    def _require_primary_path_raw(cls) -> Path:
        """Return PRIMARY path without triggering catalog repair recursion."""
        if cls._primary_path is None:
            raise RuntimeError("DBMgr bootstrap did not initialize the PRIMARY database path.")
        return cls._primary_path

    @classmethod
    def _get_setup_scripts_for_database(cls, name: str, db_path: Path) -> list[Path]:
        """Return setup scripts that should initialize a specific database."""
        setup_dir = cls._require_data_path() / "db_setup"
        if not setup_dir.is_dir():
            return []

        if name == _PRIMARY_ALIAS:
            return sorted(
                path for path in setup_dir.glob("*.sql")
                if _PRIMARY_SETUP_RE.match(path.stem) or path.stem.lower() in {"primary", "primary_setup"}
            )

        aliases = {name.lower(), db_path.stem.lower()}
        return sorted(path for path in setup_dir.glob("*.sql") if path.stem.lower() in aliases)

    @classmethod
    def _discover_setup_databases(cls) -> list[tuple[str, Path]]:
        """Discover non-PRIMARY databases defined by setup scripts."""
        setup_dir = cls._require_data_path() / "db_setup"
        if not setup_dir.is_dir():
            return []

        discovered: list[tuple[str, Path]] = []
        for path in sorted(setup_dir.glob("*.sql")):
            stem = path.stem
            if _PRIMARY_SETUP_RE.match(stem) or stem.lower() in {"primary", "primary_setup"}:
                continue
            if not _IDENTIFIER_RE.match(stem):
                continue
            discovered.append((stem, cls._require_data_path() / f"{stem}.db"))
        return discovered

    @classmethod
    def _initialize_database_from_setup(cls, name: str, db_path: Path) -> None:
        """Create a database file and populate it from matching setup scripts."""
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        try:
            conn.row_factory = sqlite3.Row
            cls._apply_pragmas(conn)
        finally:
            conn.close()

        for sql_file in cls._get_setup_scripts_for_database(name, db_path):
            script = sql_file.read_text(encoding="utf-8")
            if not script.strip():
                continue
            sc = sqlite3.connect(str(db_path))
            try:
                sc.row_factory = sqlite3.Row
                cls._apply_pragmas(sc)
                sc.executescript(script)
                sc.commit()
            finally:
                sc.close()

    @classmethod
    def _ensure_database_present(cls, name: str, db_path: Path) -> None:
        """Ensure a registered database file exists, rebuilding from setup when missing."""
        db_key = str(db_path.resolve())
        if db_key in cls._ensured_database_paths:
            return
        if db_path.exists():
            cls._ensured_database_paths.add(db_key)
            return
        cls._initialize_database_from_setup(name, db_path)
        cls._ensured_database_paths.add(db_key)

    @classmethod
    def _register_database_catalog_entry(cls, name: str, db_path: Path) -> None:
        """Ensure a database alias is present in PRIMARY."""
        cat = sqlite3.connect(str(cls._require_primary_path_raw()))
        try:
            cat.row_factory = sqlite3.Row
            cls._apply_pragmas(cat)
            cat.execute(
                "INSERT OR IGNORE INTO databases (name, path) VALUES (?, ?)",
                (name, str(db_path.resolve())),
            )
            cat.commit()
        finally:
            cat.close()

    @classmethod
    def _sync_setup_databases(cls) -> None:
        """Ensure setup-defined databases are created and registered."""
        for name, db_path in cls._discover_setup_databases():
            cls._ensure_database_present(name, db_path)
            cls._register_database_catalog_entry(name, db_path)

    @classmethod
    def _ensure_catalog_consistency(cls) -> None:
        """Ensure PRIMARY is valid and all setup-defined databases are present."""
        if cls._catalog_consistent:
            return
        cls._ensure_primary_catalog()
        cls._sync_setup_databases()
        cls._catalog_consistent = True

    @classmethod
    def _ensure_primary_catalog(cls) -> None:
        """Ensure the PRIMARY database file and catalog table exist via setup scripts."""
        if cls._primary_catalog_ensured:
            return
        if cls._data_path is None or cls._primary_path is None:
            raise RuntimeError("DBMgr bootstrap paths are not initialized.")

        cls._data_path.mkdir(parents=True, exist_ok=True)
        cls._primary_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(cls._primary_path))
        try:
            conn.row_factory = sqlite3.Row
            cls._apply_pragmas(conn)
            row = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name = 'databases' LIMIT 1"
            ).fetchone()
        finally:
            conn.close()

        if row is None:
            cls._initialize_database_from_setup(_PRIMARY_ALIAS, cls._primary_path)
            cls._register_primary_catalog_entry()
        cls._primary_catalog_ensured = True

    # -----------------------------------------------------------------------
    # Bootstrap (Phase 2)
    # -----------------------------------------------------------------------

    @classmethod
    def _bootstrap_once(cls) -> None:
        """Ensure the PRIMARY catalog database exists and is self-registered.

        Runs exactly once per process. Creates the PRIMARY database file,
        executes all ``.sql`` scripts from ``data/db_setup/`` in alphabetical
        order, and registers PRIMARY in its own catalog.

        Idempotent: safe to call multiple times — only the first call has effect.
        """
        cls._projects_path = _get_projects_path()
        cls._data_path = _get_data_path()
        cls._primary_path = cls._data_path / _PRIMARY_DB_FILENAME
        cls._ensure_catalog_consistency()

        cls._bootstrapped = True

    # -----------------------------------------------------------------------
    # Logging (static — deferred Py4GW import)
    # -----------------------------------------------------------------------

    @staticmethod
    def _log(message: str, severity: str = "Info") -> None:
        """Log a message through Py4GW.Console.Log with print() fallback.

        Args:
            message: The message text.
            severity: One of 'Error', 'Warning', 'Notice', 'Info', 'Debug'.
        """
        try:
            import Py4GW

            msg_type = getattr(Py4GW.Console.MessageType, severity, Py4GW.Console.MessageType.Notice)
            Py4GW.Console.Log(MODULE_NAME, message, msg_type)
        except Exception:
            print(f"[{MODULE_NAME}] [{severity}] {message}")

    # -----------------------------------------------------------------------
    # Constructor (Phase 7)
    # -----------------------------------------------------------------------

    def __init__(self, name: str) -> None:
        """Create a DBMgr bound to a specific database.

        Args:
            name: Alias of the database to open. Must be registered in the
                  PRIMARY catalog (or be 'PRIMARY' itself).

        Raises:
            ValueError: If *name* is not a valid identifier or not found
                        in the PRIMARY catalog.
        """
        DBMgr._bootstrap_once()
        self._validate_identifier(name)

        if not hasattr(self, "_tx_conn"):
            self._tx_conn: Optional[sqlite3.Connection] = None

        current_name = getattr(self, "_name", None)
        if current_name == name:
            return

        if self._tx_conn is not None:
            raise RuntimeError(
                f"Cannot switch DBMgr binding from '{self._name}' to '{name}' while a transaction is active."
            )

        self._name = name
        self._db_path = self._resolve_db_path(name)

    # -----------------------------------------------------------------------
    # Path resolution helpers
    # -----------------------------------------------------------------------

    def _resolve_db_path(self, name: str) -> Path:
        """Look up a database name in the PRIMARY catalog and return its path.

        Args:
            name: Database alias to resolve.

        Returns:
            Absolute Path to the database file.

        Raises:
            ValueError: If *name* is not found in the PRIMARY catalog.
        """
        DBMgr._ensure_catalog_consistency()
        if name == _PRIMARY_ALIAS:
            return DBMgr._require_primary_path()

        conn = sqlite3.connect(str(DBMgr._require_primary_path()))
        try:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT path FROM databases WHERE name = ?", (name,)).fetchone()
            if row is None:
                raise ValueError(
                    f"Database '{name}' not found in catalog. "
                    f"Register it first with Register('{name}', 'filename.db'). "
                    f"Use List() to see registered databases."
                )
            db_path = Path(row["path"])
            DBMgr._ensure_database_present(name, db_path)
            return db_path
        finally:
            conn.close()

    # -----------------------------------------------------------------------
    # Validation helpers (Phase 6)
    # -----------------------------------------------------------------------

    @staticmethod
    def _validate_identifier(identifier: str) -> None:
        """Validate that *identifier* is a safe SQL identifier.

        Allowed pattern: ``^[A-Za-z_][A-Za-z0-9_]*$``

        Args:
            identifier: The string to validate.

        Raises:
            ValueError: If the identifier does not match the allowed pattern.
        """
        if not isinstance(identifier, str) or not _IDENTIFIER_RE.match(identifier):
            raise ValueError(
                f"Invalid identifier: '{identifier}'. "
                f"Must match pattern: ^[A-Za-z_][A-Za-z0-9_]*$ "
                f"(start with letter or underscore, then letters/digits/underscores)."
            )

    @staticmethod
    def _validate_order_dir(order_dir: str) -> None:
        """Validate that *order_dir* is 'ASC' or 'DESC'.

        Args:
            order_dir: Sort direction string.

        Raises:
            ValueError: If *order_dir* is not 'ASC' or 'DESC'.
        """
        if order_dir.upper() not in ("ASC", "DESC"):
            raise ValueError(f"order_dir must be 'ASC' or 'DESC', got '{order_dir}'.")

    def _ensure_tx(self) -> None:
        """Check that a transaction is active; raise RuntimeError if not."""
        if self._tx_conn is None:
            raise RuntimeError(
                f"No active transaction on '{self._name}'. "
                f"Call BeginTransaction() first, then use commit=False."
            )

    def _require_tx_conn(self) -> sqlite3.Connection:
        """Return the active transaction connection or raise if none exists."""
        self._ensure_tx()
        if self._tx_conn is None:
            raise RuntimeError(f"No active transaction on '{self._name}'.")
        return self._tx_conn

    # -----------------------------------------------------------------------
    # SQL fragment builders (Phase 6)
    # -----------------------------------------------------------------------

    def _build_where(self, where: Optional[dict]) -> tuple:
        """Build a ``WHERE col = ? AND col = ?`` clause from a dict.

        Args:
            where: ``{column_name: value, ...}`` dict.  None or empty
                   produces an empty clause.

        Returns:
            ``(clause_string, params_tuple)``.  *clause_string* is empty
            when *where* is None/empty.
        """
        if not where:
            return "", ()
        for key in where:
            self._validate_identifier(key)
        clauses = [f"{k} = ?" for k in where]
        return " WHERE " + " AND ".join(clauses), tuple(where.values())

    def _build_set(self, data: dict) -> tuple:
        """Build a ``SET col = ?, col = ?`` fragment from a dict.

        Args:
            data: ``{column_name: value, ...}`` dict.

        Returns:
            ``(set_string, params_tuple)``.

        Raises:
            ValueError: If *data* is empty.
        """
        if not data:
            raise ValueError("SET data cannot be empty.")
        for key in data:
            self._validate_identifier(key)
        parts = [f"{k} = ?" for k in data]
        return ", ".join(parts), tuple(data.values())

    def _build_columns(self, columns: Optional[list]) -> str:
        """Build a column-list string for SELECT.

        Args:
            columns: List of column names or None.

        Returns:
            ``'*'`` if *columns* is None or empty, otherwise a comma-separated
            list of validated column names.
        """
        if not columns:
            return "*"
        for col in columns:
            self._validate_identifier(col)
        return ", ".join(columns)

    # -----------------------------------------------------------------------
    # PRAGMAs (Phase 3)
    # -----------------------------------------------------------------------

    @staticmethod
    def _apply_pragmas(conn: sqlite3.Connection) -> None:
        """Apply the six required PRAGMAs to a connection.

        Order: WAL, foreign_keys, busy_timeout, synchronous, cache_size, temp_store.
        """
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = -8000")
        conn.execute("PRAGMA temp_store = MEMORY")

    # -----------------------------------------------------------------------
    # Connection management (Phase 3)
    # -----------------------------------------------------------------------

    def _open_connection(self) -> sqlite3.Connection:
        """Open a new SQLite connection to the bound database.

        Applies all PRAGMAs and sets ``row_factory = sqlite3.Row``.
        Detects corruption and triggers the 3-step recovery chain on failure.

        Returns:
            A configured ``sqlite3.Connection``.

        Raises:
            sqlite3.DatabaseError: If the database is corrupt and recovery fails.
        """
        DBMgr._ensure_catalog_consistency()
        DBMgr._ensure_database_present(self._name, self._db_path)
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        try:
            self._apply_pragmas(conn)
        except sqlite3.DatabaseError as e:
            msg = str(e).lower()
            if "malformed" in msg or "file is not a database" in msg:
                conn.close()
                self._recover_from_corruption()
                # Reconnect to the recovered database
                conn = sqlite3.connect(str(self._db_path))
                conn.row_factory = sqlite3.Row
                self._apply_pragmas(conn)
            else:
                conn.close()
                raise
        return conn

    def _open_read_connection(self) -> sqlite3.Connection:
        """Return a pooled read connection for the bound database."""
        DBMgr._ensure_catalog_consistency()
        DBMgr._ensure_database_present(self._name, self._db_path)
        db_key = str(self._db_path.resolve())
        conn = DBMgr._read_connections.get(db_key)
        if conn is not None:
            return conn

        conn = sqlite3.connect(str(self._db_path), isolation_level=None)
        conn.row_factory = sqlite3.Row
        try:
            self._apply_pragmas(conn)
            conn.execute("PRAGMA query_only = ON")
        except sqlite3.DatabaseError as e:
            msg = str(e).lower()
            if "malformed" in msg or "file is not a database" in msg:
                conn.close()
                self._recover_from_corruption()
                conn = sqlite3.connect(str(self._db_path), isolation_level=None)
                conn.row_factory = sqlite3.Row
                self._apply_pragmas(conn)
                conn.execute("PRAGMA query_only = ON")
            else:
                conn.close()
                raise
        DBMgr._read_connections[db_key] = conn
        return conn

    @classmethod
    def _close_read_connection(cls, db_key: str) -> None:
        """Close one pooled read connection, ignoring any errors."""
        conn = cls._read_connections.pop(db_key, None)
        if conn is None:
            return
        try:
            conn.close()
        except Exception:
            pass

    @staticmethod
    def _close_connection(conn: sqlite3.Connection) -> None:
        """Close a SQLite connection, ignoring any errors."""
        try:
            conn.close()
        except Exception:
            pass

    # -----------------------------------------------------------------------
    # Corruption recovery chain (Phase 4)
    # -----------------------------------------------------------------------

    def _recover_from_corruption(self) -> None:
        """3-step corruption recovery chain.

        Step 0: Rename corrupt .db/.wal/.shm to timestamped ``.corrupt_*`` files.
        Step 1: Attempt to restore from the most recent backup directory.
        Step 2: Create a clean replacement and re-run setup scripts.
        Step 3: Raise ``sqlite3.DatabaseError`` if all steps fail.
        """

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_path = Path(self._db_path)
        corrupt_suffix = f".corrupt_{timestamp}.db"
        corrupt_db = db_path.parent / (db_path.stem + corrupt_suffix)

        # Step 0: Rename corrupt files
        for ext in ("", "-wal", "-shm"):
            src = Path(str(db_path) + ext)
            dst = Path(str(corrupt_db) + ext)
            if src.exists():
                try:
                    src.rename(dst)
                except OSError:
                    pass

        # Step 1: Restore from most recent backup
        parent = db_path.parent
        backup_dirs = sorted(
            [d for d in parent.iterdir() if d.is_dir() and "_backup_" in d.name],
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )
        for backup_dir in backup_dirs:
            backup_db = backup_dir / db_path.name
            if backup_db.exists():
                try:
                    shutil.copy2(str(backup_db), str(db_path))
                    # Copy WAL/SHM if present
                    for ext in ("-wal", "-shm"):
                        backup_ext = backup_dir / (db_path.name + ext)
                        if backup_ext.exists():
                            shutil.copy2(str(backup_ext), str(db_path) + ext)
                    DBMgr._log(
                        f"Database '{self._name}' recovered from backup: {backup_dir.name}",
                        "Warning",
                    )
                    return
                except OSError:
                    continue

        # Step 2: Recreate from setup scripts
        self._log(
            f"Database '{self._name}' is corrupt and no backup was found. "
            f"Creating a clean replacement.",
            "Warning",
        )
        DBMgr._initialize_database_from_setup(self._name, db_path)
        if self._name == _PRIMARY_ALIAS:
            DBMgr._register_primary_catalog_entry()

        self._log(
            f"Database '{self._name}' was recovered (clean replacement created).",
            "Warning",
        )

    # -----------------------------------------------------------------------
    # Central executor (Phase 5)
    # -----------------------------------------------------------------------

    def _execute(
        self,
        sql: str,
        params: Optional[tuple] = None,
        commit: bool = True,
        fetch: bool = False,
    ) -> Any:
        """Central SQL executor — the single entry point for all SQL execution.

        Args:
            sql: SQL statement to execute (with ``?`` placeholders).
            params: Tuple of bind parameters.
            commit:
                If ``True``: auto-rollback any orphan transaction, open a fresh
                connection, execute, commit, close. Uses lock-retry with backoff.
                If ``False``: use the held transaction connection. Raises
                ``RuntimeError`` if no transaction is active.
            fetch:
                If ``True``: execute, fetch all rows, return ``list[dict]``.
                If ``False``: return ``cursor.lastrowid`` (for INSERT) or
                ``cursor.rowcount`` (for UPDATE/DELETE).

        Returns:
            ``list[dict]`` when ``fetch=True``, ``int`` otherwise.
        """
        if params is None:
            params = ()

        # Auto-rollback orphan transactions
        if commit and self._tx_conn is not None:
            DBMgr._log(
                f"Orphaned transaction on '{self._name}' auto-rolled back.",
                "Warning",
            )
            try:
                self._tx_conn.execute("ROLLBACK")
            except Exception:
                pass
            DBMgr._close_connection(self._require_tx_conn())
            self._tx_conn = None

        # Determine connection strategy
        if not commit:
            conn = self._require_tx_conn()
            do_close = False
        else:
            conn = self._open_connection()
            do_close = True

        try:
            cursor = conn.execute(sql, params)

            if fetch:
                result = [dict(row) for row in cursor.fetchall()]
            else:
                result = cursor.lastrowid or cursor.rowcount

            if do_close:
                conn.commit()

            return result

        except sqlite3.OperationalError as e:
            if do_close and "locked" in str(e).lower():
                DBMgr._close_connection(conn)
                return self._retry_on_lock(sql, params, fetch)
            raise

        except sqlite3.DatabaseError as e:
            msg = str(e).lower()
            if do_close and ("malformed" in msg or "file is not a database" in msg):
                DBMgr._close_connection(conn)
                self._recover_from_corruption()
                retry_conn = self._open_connection()
                try:
                    retry_cursor = retry_conn.execute(sql, params)
                    if fetch:
                        return [dict(row) for row in retry_cursor.fetchall()]
                    retry_conn.commit()
                    return retry_cursor.lastrowid or retry_cursor.rowcount
                finally:
                    DBMgr._close_connection(retry_conn)
            raise

        finally:
            if do_close:
                DBMgr._close_connection(conn)

    def _retry_on_lock(self, sql: str, params: tuple, fetch: bool) -> Any:
        """Retry a write operation on 'database is locked' errors with backoff.

        3 attempts total with 0.1s / 0.5s delays.
        """
        delays = [0.1, 0.5]
        last_error = None
        for attempt, delay in enumerate(delays):
            try:
                conn = self._open_connection()
                try:
                    cursor = conn.execute(sql, params)
                    if fetch:
                        result = [dict(row) for row in cursor.fetchall()]
                    else:
                        result = cursor.lastrowid or cursor.rowcount
                    conn.commit()
                    return result
                finally:
                    DBMgr._close_connection(conn)
            except sqlite3.OperationalError as e:
                if "locked" not in str(e).lower():
                    raise
                last_error = e
                time.sleep(delay)

        # Final attempt
        try:
            conn = self._open_connection()
            try:
                cursor = conn.execute(sql, params)
                if fetch:
                    result = [dict(row) for row in cursor.fetchall()]
                else:
                    result = cursor.lastrowid or cursor.rowcount
                conn.commit()
                return result
            finally:
                DBMgr._close_connection(conn)
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                raise sqlite3.OperationalError(
                    f"Database '{self._name}' is locked after 3 retries."
                ) from e
            raise

    # =======================================================================
    # PUBLIC API — Lifecycle (Phase 8)
    # =======================================================================

    def Register(self, name: str, filename: Union[str, Path]) -> Path:
        """Register a new database under *name* in the PRIMARY catalog.

        Creates the database file on disk and applies PRAGMAs.

        Args:
            name: Unique alias for the database. Must match the identifier pattern.
            filename: Relative path under the DBMgr data directory or absolute path
                that still resolves under the DBMgr data directory.

        Returns:
            Resolved ``Path`` of the created database file.

        Raises:
            ValueError: If *name* is already registered, is 'PRIMARY', or is an
                        invalid identifier. Also if the path escapes the base
                        directory.
        """
        DBMgr._ensure_catalog_consistency()
        self._validate_identifier(name)
        if name == _PRIMARY_ALIAS:
            raise ValueError(f"'{_PRIMARY_ALIAS}' is reserved.")
        if self.Has(name):
            raise ValueError(
                f"Database '{name}' is already registered. "
                f"Use Unregister('{name}') to remove it first."
            )

        path = Path(filename)
        if not path.is_absolute():
            path = (DBMgr._require_data_path() / path).resolve()
        else:
            path = path.resolve()

        # Path traversal guard
        try:
            path.relative_to(DBMgr._require_data_path())
        except ValueError:
            raise ValueError(
                f"Database path '{path}' escapes the DBMgr data directory "
                f"'{DBMgr._require_data_path()}'."
            )

        # Create and initialize the database file
        DBMgr._initialize_database_from_setup(name, path)
        DBMgr._ensured_database_paths.add(str(path.resolve()))

        # Register in PRIMARY catalog
        cat = sqlite3.connect(str(DBMgr._require_primary_path()))
        try:
            cat.row_factory = sqlite3.Row
            cat.execute(
                "INSERT INTO databases (name, path) VALUES (?, ?)",
                (name, str(path)),
            )
            cat.commit()
        finally:
            cat.close()

        DBMgr._catalog_consistent = True
        DBMgr._log(f"Database '{name}' registered at {path}.", "Info")
        return path

    def Unregister(self, name: str, delete_file: bool = False) -> bool:
        """Remove a database from the PRIMARY catalog and optionally delete files.

        Args:
            name: Alias of the database to unregister. 'PRIMARY' cannot be removed.
            delete_file: If ``True``, permanently delete ``.db``, ``-wal``, and
                         ``-shm`` files from disk.

        Returns:
            ``True`` on success.

        Raises:
            ValueError: If *name* is 'PRIMARY' or not registered.
        """
        DBMgr._ensure_catalog_consistency()
        self._validate_identifier(name)
        if name == _PRIMARY_ALIAS:
            raise ValueError("Cannot unregister the PRIMARY catalog database.")
        if not self.Has(name):
            raise ValueError(f"Database '{name}' is not registered.")

        # If the database being unregistered is THIS instance's db, auto-rollback any tx
        if name == self._name and self._tx_conn is not None:
            DBMgr._log(
                f"Active transaction on '{self._name}' auto-rolled back before unregister.",
                "Warning",
            )
            try:
                self._tx_conn.execute("ROLLBACK")
            except Exception:
                pass
            DBMgr._close_connection(self._require_tx_conn())
            self._tx_conn = None

        # Get path from catalog before deleting the row
        cat = sqlite3.connect(str(DBMgr._require_primary_path()))
        try:
            cat.row_factory = sqlite3.Row
            row = cat.execute("SELECT path FROM databases WHERE name = ?", (name,)).fetchone()
            db_path = Path(row["path"]) if row else None
            cat.execute("DELETE FROM databases WHERE name = ?", (name,))
            cat.commit()
        finally:
            cat.close()

        # Delete files if requested
        if delete_file and db_path is not None:
            DBMgr._ensured_database_paths.discard(str(db_path.resolve()))
            for p in [db_path, Path(str(db_path) + "-wal"), Path(str(db_path) + "-shm")]:
                if p.exists():
                    try:
                        p.unlink()
                    except OSError:
                        pass
            DBMgr._log(f"Database '{name}' and associated files deleted.", "Warning")
        else:
            DBMgr._log(f"Database '{name}' unregistered (files preserved).", "Info")

        DBMgr._catalog_consistent = True
        return True

    def List(self) -> dict:
        """List all databases registered in the PRIMARY catalog.

        Returns:
            ``{name: path, ...}`` dictionary of all registered databases.
        """
        DBMgr._ensure_catalog_consistency()
        cat = sqlite3.connect(str(DBMgr._require_primary_path()))
        try:
            cat.row_factory = sqlite3.Row
            rows = cat.execute("SELECT name, path FROM databases").fetchall()
            return {row["name"]: row["path"] for row in rows}
        finally:
            cat.close()

    def Has(self, name: str) -> bool:
        """Check whether a database name is registered in the PRIMARY catalog.

        Args:
            name: Database alias to look up.

        Returns:
            ``True`` if *name* exists in the catalog.
        """
        DBMgr._ensure_catalog_consistency()
        if name == _PRIMARY_ALIAS:
            return True
        cat = sqlite3.connect(str(DBMgr._require_primary_path()))
        try:
            cat.row_factory = sqlite3.Row
            row = cat.execute("SELECT 1 FROM databases WHERE name = ?", (name,)).fetchone()
            return row is not None
        finally:
            cat.close()

    # =======================================================================
    # PUBLIC API — DDL (Phase 9)
    # =======================================================================

    def CreateTable(
        self,
        table: str,
        columns_def: list,
        if_not_exists: bool = True,
        commit: bool = True,
    ) -> None:
        """Create a table in the bound database.

        Args:
            table: Table name (validated against identifier pattern).
            columns_def: List of ``(name, type, constraints?)`` tuples.
                Example: ``[('id', 'INTEGER', 'PRIMARY KEY AUTOINCREMENT'),
                ('name', 'TEXT', 'NOT NULL')]``.
            if_not_exists: If ``True`` (default), adds ``IF NOT EXISTS`` to the
                CREATE statement for idempotency.
            commit: If ``True`` (default), auto-commits. Set ``False`` inside a
                transaction.

        Raises:
            ValueError: If *table* is invalid or *columns_def* is empty.
        """
        self._validate_identifier(table)
        if not columns_def:
            raise ValueError("columns_def must be a non-empty list of (name, type[, constraints]) tuples.")

        col_parts = []
        for col in columns_def:
            name, col_type = col[0], col[1]
            self._validate_identifier(name)
            constraints = col[2] if len(col) > 2 and col[2] else ""
            part = f"{name} {col_type}"
            if constraints:
                part += f" {constraints}"
            col_parts.append(part)

        if_not = "IF NOT EXISTS " if if_not_exists else ""
        sql = f"CREATE TABLE {if_not}{table} ({', '.join(col_parts)})"
        self._execute(sql, commit=commit)

    def DropTable(self, table: str, if_exists: bool = True, commit: bool = True) -> None:
        """Drop a table from the bound database.

        Args:
            table: Table name.
            if_exists: If ``True`` (default), adds ``IF EXISTS`` to prevent
                errors when the table does not exist.
            commit: If ``True`` (default), auto-commits. Set ``False`` inside a
                transaction.
        """
        self._validate_identifier(table)
        if_ex = "IF EXISTS " if if_exists else ""
        sql = f"DROP TABLE {if_ex}{table}"
        self._execute(sql, commit=commit)

    def RenameTable(self, old_name: str, new_name: str, commit: bool = True) -> None:
        """Rename a table in the bound database.

        Args:
            old_name: Current table name.
            new_name: New table name.
            commit: If ``True`` (default), auto-commits. Set ``False`` inside a
                transaction.
        """
        self._validate_identifier(old_name)
        self._validate_identifier(new_name)
        sql = f"ALTER TABLE {old_name} RENAME TO {new_name}"
        self._execute(sql, commit=commit)

    def AddColumn(
        self,
        table: str,
        name: str,
        col_type: str,
        constraints: Optional[str] = None,
        commit: bool = True,
    ) -> None:
        """Add a column to an existing table.

        Args:
            table: Table name.
            name: New column name.
            col_type: SQL type (e.g. 'TEXT', 'INTEGER').
            constraints: Optional constraint string (e.g. 'NOT NULL DEFAULT 0').
            commit: If ``True`` (default), auto-commits. Set ``False`` inside a
                transaction.
        """
        self._validate_identifier(table)
        self._validate_identifier(name)
        part = f"{name} {col_type}"
        if constraints:
            part += f" {constraints}"
        sql = f"ALTER TABLE {table} ADD COLUMN {part}"
        self._execute(sql, commit=commit)

    def DropColumn(self, table: str, name: str, commit: bool = True) -> None:
        """Drop a column from a table.

        NOTE: Requires SQLite 3.35.0+ (2021-03-12).

        Args:
            table: Table name.
            name: Column name to drop.
            commit: If ``True`` (default), auto-commits. Set ``False`` inside a
                transaction.
        """
        self._validate_identifier(table)
        self._validate_identifier(name)
        sql = f"ALTER TABLE {table} DROP COLUMN {name}"
        self._execute(sql, commit=commit)

    def RenameColumn(self, table: str, old_name: str, new_name: str, commit: bool = True) -> None:
        """Rename a column in a table.

        NOTE: Requires SQLite 3.25.0+ (2018-09-15).

        Args:
            table: Table name.
            old_name: Current column name.
            new_name: New column name.
            commit: If ``True`` (default), auto-commits. Set ``False`` inside a
                transaction.
        """
        self._validate_identifier(table)
        self._validate_identifier(old_name)
        self._validate_identifier(new_name)
        sql = f"ALTER TABLE {table} RENAME COLUMN {old_name} TO {new_name}"
        self._execute(sql, commit=commit)

    # =======================================================================
    # PUBLIC API — DML (Phase 10)
    # =======================================================================

    def Insert(
        self,
        table: str,
        fields: list,
        values: list,
        commit: bool = True,
    ) -> int:
        """Insert one row into a table.

        Args:
            table: Table name.
            fields: List of column names.
            values: List of values (same length as *fields*).
            commit: If ``True`` (default), auto-commits. Set ``False`` inside a
                transaction.

        Returns:
            The ``rowid`` of the inserted row.
        """
        self._validate_identifier(table)
        for f in fields:
            self._validate_identifier(f)
        if len(fields) != len(values):
            raise ValueError(
                f"Insert field/value count mismatch: "
                f"{len(fields)} fields vs {len(values)} values."
            )
        if not fields:
            raise ValueError("Insert requires at least one field.")

        cols = ", ".join(fields)
        places = ", ".join(["?"] * len(values))
        sql = f"INSERT INTO {table} ({cols}) VALUES ({places})"
        return self._execute(sql, tuple(values), commit=commit, fetch=False)

    def Update(
        self,
        table: str,
        data: dict,
        where: Optional[dict] = None,
        commit: bool = True,
    ) -> int:
        """Update rows in a table matching a WHERE clause.

        Args:
            table: Table name.
            data: ``{column: new_value, ...}`` dict of columns to set.
            where: ``{column: value, ...}`` dict of equality conditions.
                   ``None`` or empty updates ALL rows (use with caution).
            commit: If ``True`` (default), auto-commits.

        Returns:
            Number of rows affected.
        """
        self._validate_identifier(table)
        set_sql, set_params = self._build_set(data)
        where_sql, where_params = self._build_where(where)
        sql = f"UPDATE {table} SET {set_sql}{where_sql}"
        params = set_params + where_params
        return self._execute(sql, params, commit=commit, fetch=False)

    def Delete(
        self,
        table: str,
        where: Optional[dict] = None,
        commit: bool = True,
    ) -> int:
        """Delete rows from a table matching a WHERE clause.

        Args:
            table: Table name.
            where: ``{column: value, ...}`` dict of equality conditions.
                   ``None`` or empty deletes ALL rows (use with caution).
            commit: If ``True`` (default), auto-commits.

        Returns:
            Number of rows deleted.
        """
        self._validate_identifier(table)
        where_sql, where_params = self._build_where(where)
        sql = f"DELETE FROM {table}{where_sql}"
        return self._execute(sql, where_params or (), commit=commit, fetch=False)

    def Select(
        self,
        table: str,
        columns: Optional[list] = None,
        where: Optional[dict] = None,
        order_by: Optional[str] = None,
        order_dir: str = "ASC",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        commit: bool = True,
    ) -> list:
        """Select rows from a table.

        Args:
            table: Table name.
            columns: List of column names to return. ``None`` or ``[]`` → ``SELECT *``.
            where: ``{column: value, ...}`` dict of equality AND conditions.
            order_by: Column name to sort by.
            order_dir: ``'ASC'`` (default) or ``'DESC'``.
            limit: Maximum number of rows to return.
            offset: Number of rows to skip before returning results.
            commit: If ``True`` (default), auto-commits. Set ``False`` inside a
                transaction.

        Returns:
            ``list[dict]`` of matching rows.
        """
        self._validate_identifier(table)
        cols = self._build_columns(columns)
        where_sql, where_params = self._build_where(where)

        sql = f"SELECT {cols} FROM {table}{where_sql}"

        extra_params = []
        if order_by:
            self._validate_identifier(order_by)
            self._validate_order_dir(order_dir)
            sql += f" ORDER BY {order_by} {order_dir.upper()}"
        if limit is not None:
            sql += " LIMIT ?"
            extra_params.append(limit)
        if offset is not None:
            sql += " OFFSET ?"
            extra_params.append(offset)

        params = where_params + tuple(extra_params)
        if not commit:
            return self._execute(sql, params, commit=False, fetch=True)
        return self._execute_select(sql, params)

    def _execute_select(self, sql: str, params: Optional[tuple] = None) -> list[dict]:
        """Execute a standalone SELECT without committing the connection."""
        if params is None:
            params = ()

        if self._tx_conn is not None:
            DBMgr._log(
                f"Orphaned transaction on '{self._name}' auto-rolled back.",
                "Warning",
            )
            try:
                self._tx_conn.execute("ROLLBACK")
            except Exception:
                pass
            DBMgr._close_connection(self._require_tx_conn())
            self._tx_conn = None

        db_key = str(self._db_path.resolve())
        conn = self._open_read_connection()
        try:
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                DBMgr._close_read_connection(db_key)
                return self._retry_select_on_lock(sql, params)
            raise
        except sqlite3.DatabaseError as e:
            msg = str(e).lower()
            if "malformed" in msg or "file is not a database" in msg:
                DBMgr._close_read_connection(db_key)
                self._recover_from_corruption()
                retry_conn = self._open_read_connection()
                try:
                    retry_cursor = retry_conn.execute(sql, params)
                    return [dict(row) for row in retry_cursor.fetchall()]
                finally:
                    pass
            DBMgr._close_read_connection(db_key)
            raise

    def _retry_select_on_lock(self, sql: str, params: tuple) -> list[dict]:
        """Retry a standalone SELECT on lock errors with backoff."""
        delays = [0.1, 0.5]
        db_key = str(self._db_path.resolve())
        for delay in delays:
            try:
                conn = self._open_read_connection()
                cursor = conn.execute(sql, params)
                return [dict(row) for row in cursor.fetchall()]
            except sqlite3.OperationalError as e:
                if "locked" not in str(e).lower():
                    raise
                DBMgr._close_read_connection(db_key)
                time.sleep(delay)

        try:
            conn = self._open_read_connection()
            cursor = conn.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                DBMgr._close_read_connection(db_key)
                raise sqlite3.OperationalError(
                    f"Database '{self._name}' is locked after 3 retries."
                ) from e
            raise

    def Count(self, table: str, where: Optional[dict] = None, commit: bool = True) -> int:
        """Count rows in a table, optionally filtered by a WHERE clause.

        Args:
            table: Table name.
            where: ``{column: value, ...}`` dict of equality conditions.
            commit: If ``True`` (default), auto-commits. Set ``False`` inside a
                transaction.

        Returns:
            Row count as ``int`` (``0`` for empty tables).
        """
        self._validate_identifier(table)
        where_sql, where_params = self._build_where(where)
        sql = f"SELECT COUNT(*) FROM {table}{where_sql}"
        result = self._execute(sql, where_params or (), commit=commit, fetch=True)
        return result[0]["COUNT(*)"] if result else 0

    def Merge(
        self,
        table: str,
        fields: list,
        values: list,
        commit: bool = True,
    ) -> int:
        """Insert a row, or update it if a conflict on the PRIMARY KEY occurs.

        Automatically detects the PRIMARY KEY column(s) from the table schema.

        Args:
            table: Table name.
            fields: List of column names (same shape as ``Insert``).
            values: List of values (same length as *fields*).
            commit: If ``True`` (default), auto-commits.

        Returns:
            The ``rowid`` of the inserted or updated row.
        """
        self._validate_identifier(table)
        for f in fields:
            self._validate_identifier(f)
        if len(fields) != len(values):
            raise ValueError(
                f"Merge field/value count mismatch: "
                f"{len(fields)} fields vs {len(values)} values."
            )
        if not fields:
            raise ValueError("Merge requires at least one field.")

        # Auto-detect PK column(s)
        schema = self.GetSchema(table, commit=commit)
        pk_columns = [s["name"] for s in schema if s["pk"]]
        if not pk_columns:
            # No PK defined — fall back to simple INSERT
            cols = ", ".join(fields)
            places = ", ".join(["?"] * len(values))
            sql = f"INSERT INTO {table} ({cols}) VALUES ({places})"
            return self._execute(sql, tuple(values), commit=commit, fetch=False)

        # Build UPSERT
        cols = ", ".join(fields)
        places = ", ".join(["?"] * len(values))
        pk_list = ", ".join(pk_columns)

        # UPDATE SET for non-PK columns
        non_pk_fields = [f for f in fields if f not in pk_columns]
        if non_pk_fields:
            update_parts = ", ".join(f"{f} = excluded.{f}" for f in non_pk_fields)
            sql = (
                f"INSERT INTO {table} ({cols}) VALUES ({places}) "
                f"ON CONFLICT({pk_list}) DO UPDATE SET {update_parts}"
            )
        else:
            # All columns are PK — conflict means nothing to update
            sql = (
                f"INSERT OR IGNORE INTO {table} ({cols}) VALUES ({places})"
            )

        return self._execute(sql, tuple(values), commit=commit, fetch=False)

    # =======================================================================
    # PUBLIC API — Introspection (Phase 11)
    # =======================================================================

    def GetTables(self, commit: bool = True) -> list:
        """Return a list of all table names in the bound database.

        Returns:
            ``list[str]`` — excludes internal ``sqlite_*`` tables.
        """
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        result = self._execute(sql, commit=commit, fetch=True)
        return [r["name"] for r in result]

    def TableExists(self, table: str, commit: bool = True) -> bool:
        """Check if a table exists in the bound database.

        Args:
            table: Table name.

        Returns:
            ``True`` if the table exists.
        """
        self._validate_identifier(table)
        sql = "SELECT 1 FROM sqlite_master WHERE type='table' AND name = ? LIMIT 1"
        result = self._execute(sql, (table,), commit=commit, fetch=True)
        return len(result) > 0

    def GetSchema(self, table: str, commit: bool = True) -> list:
        """Return the schema of a table.

        Args:
            table: Table name.

        Returns:
            ``list[dict]`` with keys: ``cid``, ``name``, ``type``, ``notnull``,
            ``dflt_value``, ``pk``.
        """
        self._validate_identifier(table)
        sql = f"PRAGMA table_info({table})"
        return self._execute(sql, commit=commit, fetch=True)

    def GetColumns(self, table: str, commit: bool = True) -> list:
        """Return a list of column names for a table.

        Args:
            table: Table name.

        Returns:
            ``list[str]`` of column names in schema order.
        """
        schema = self.GetSchema(table, commit=commit)
        return [s["name"] for s in schema]

    def ColumnExists(self, table: str, column: str, commit: bool = True) -> bool:
        """Check if a column exists in a table.

        Args:
            table: Table name.
            column: Column name.

        Returns:
            ``True`` if the column exists.
        """
        self._validate_identifier(column)
        return column in self.GetColumns(table, commit=commit)

    def GetColumnType(self, table: str, column: str, commit: bool = True) -> Optional[str]:
        """Return the declared type of a column.

        Args:
            table: Table name.
            column: Column name.

        Returns:
            Type string (e.g. ``'TEXT'``, ``'INTEGER'``) or ``None`` if the
            column does not exist.
        """
        schema = self.GetSchema(table, commit=commit)
        for s in schema:
            if s["name"] == column:
                return s["type"]
        return None

    def EntryExists(self, table: str, column: str, value: Any, commit: bool = True) -> bool:
        """Check if any row has *value* in *column*.

        Args:
            table: Table name.
            column: Column name to search.
            value: Value to match.

        Returns:
            ``True`` if at least one matching row exists.
        """
        self._validate_identifier(table)
        self._validate_identifier(column)
        sql = f"SELECT 1 FROM {table} WHERE [{column}] = ? LIMIT 1"
        result = self._execute(sql, (value,), commit=commit, fetch=True)
        return len(result) > 0

    def EntryCount(self, table: str, column: str, value: Any, commit: bool = True) -> int:
        """Count rows where *column* equals *value*.

        Args:
            table: Table name.
            column: Column name.
            value: Value to match.

        Returns:
            Number of matching rows.
        """
        self._validate_identifier(table)
        self._validate_identifier(column)
        sql = f"SELECT COUNT(*) FROM {table} WHERE [{column}] = ?"
        result = self._execute(sql, (value,), commit=commit, fetch=True)
        return result[0]["COUNT(*)"] if result else 0

    def GetFirstEntry(self, table: str, column: str, value: Any, commit: bool = True) -> Optional[dict]:
        """Return the first row where *column* equals *value*.

        Args:
            table: Table name.
            column: Column name.
            value: Value to match.

        Returns:
            ``dict`` of the first matching row, or ``None`` if no match.
        """
        self._validate_identifier(table)
        self._validate_identifier(column)
        sql = f"SELECT * FROM {table} WHERE [{column}] = ? LIMIT 1"
        result = self._execute(sql, (value,), commit=commit, fetch=True)
        return result[0] if result else None

    def GetDistinct(self, table: str, column: str, commit: bool = True) -> list:
        """Return all distinct values of a column.

        Args:
            table: Table name.
            column: Column name.

        Returns:
            ``list`` of unique values in the column.
        """
        self._validate_identifier(table)
        self._validate_identifier(column)
        sql = f"SELECT DISTINCT [{column}] FROM {table}"
        result = self._execute(sql, commit=commit, fetch=True)
        return [r[column] for r in result]

    def GetMin(self, table: str, column: str, commit: bool = True) -> Any:
        """Return the minimum value of a column.

        Args:
            table: Table name.
            column: Column name.

        Returns:
            The minimum value, or ``None`` if the table is empty.
        """
        self._validate_identifier(table)
        self._validate_identifier(column)
        sql = f"SELECT MIN([{column}]) as mv FROM {table}"
        result = self._execute(sql, commit=commit, fetch=True)
        return result[0]["mv"] if result else None

    def GetMax(self, table: str, column: str, commit: bool = True) -> Any:
        """Return the maximum value of a column.

        Args:
            table: Table name.
            column: Column name.

        Returns:
            The maximum value, or ``None`` if the table is empty.
        """
        self._validate_identifier(table)
        self._validate_identifier(column)
        sql = f"SELECT MAX([{column}]) as mv FROM {table}"
        result = self._execute(sql, commit=commit, fetch=True)
        return result[0]["mv"] if result else None

    # =======================================================================
    # PUBLIC API — Transactions (Phase 12)
    # =======================================================================

    def BeginTransaction(self) -> None:
        """Begin an explicit transaction on the bound database.

        Opens and holds a connection. Subsequent ``commit=False`` calls use
        this connection without auto-committing.

        If an orphaned transaction already exists, it is auto-rolled back
        with a warning before the new transaction begins.

        Uses ``BEGIN IMMEDIATE`` to prevent busy-waiting on write locks.
        """
        # Auto-rollback orphan
        if self._tx_conn is not None:
            DBMgr._log(
                f"Orphaned transaction on '{self._name}' auto-rolled back before new transaction.",
                "Warning",
            )
            try:
                self._tx_conn.execute("ROLLBACK")
            except Exception:
                pass
            DBMgr._close_connection(self._require_tx_conn())
            self._tx_conn = None

        conn = self._open_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
        except Exception:
            DBMgr._close_connection(conn)
            raise

        self._tx_conn = conn

    def EndTransaction(self, action: str) -> None:
        """End the active transaction: COMMIT or ROLLBACK.

        Args:
            action: ``'COMMIT'`` to save changes, ``'ROLLBACK'`` to discard them.

        Raises:
            ValueError: If *action* is not ``'COMMIT'`` or ``'ROLLBACK'``.
            RuntimeError: If no active transaction exists.
        """
        if action not in ("COMMIT", "ROLLBACK"):
            raise ValueError(
                f"Invalid action '{action}'. Use 'COMMIT' or 'ROLLBACK'."
            )
        if self._tx_conn is None:
            raise RuntimeError(
                f"No active transaction on '{self._name}'. "
                f"Call BeginTransaction() first."
            )

        try:
            tx_conn = self._require_tx_conn()
            tx_conn.execute(action)
            if action == "ROLLBACK":
                DBMgr._log(f"Transaction rolled back on '{self._name}'.", "Warning")
        finally:
            DBMgr._close_connection(self._require_tx_conn())
            self._tx_conn = None

    # =======================================================================
    # PUBLIC API — Maintenance (Phase 13)
    # =======================================================================

    def Backup(self, target_folder: Union[str, Path]) -> Path:
        """Copy the database and its WAL/SHM files to a timestamped backup directory.

        Args:
            target_folder: Parent directory for the backup. A subdirectory
                ``{name}_backup_YYYYMMDD_HHMMSS/`` is created inside it.

        Returns:
            Path to the backup directory.

        Raises:
            RuntimeError: If a transaction is active on this database.
        """
        if self._tx_conn is not None:
            raise RuntimeError(
                f"Cannot backup '{self._name}' while a transaction is active. "
                f"End the transaction first."
            )

        target_folder = Path(target_folder)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = target_folder / f"{self._name}_backup_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        db_path = Path(self._db_path)

        # Copy .db
        if db_path.exists():
            shutil.copy2(str(db_path), str(backup_dir / db_path.name))

        # Copy -wal
        wal_path = Path(str(db_path) + "-wal")
        if wal_path.exists():
            shutil.copy2(str(wal_path), str(backup_dir / wal_path.name))

        # Copy -shm
        shm_path = Path(str(db_path) + "-shm")
        if shm_path.exists():
            shutil.copy2(str(shm_path), str(backup_dir / shm_path.name))

        DBMgr._log(f"Backup of '{self._name}' created at {backup_dir}.", "Info")
        return backup_dir

    def Export(self, target_path: Union[str, Path]) -> None:
        """Export all tables in the bound database to a JSON file.

        The JSON structure is:
        ``{"database": "<name>", "exported_at": "<iso_datetime>", "tables": {"table_name": [rows...]}}``

        Args:
            target_path: Path where the JSON file will be written.

        Raises:
            FileExistsError: If *target_path* already exists.
            RuntimeError: If a transaction is active.
        """
        if self._tx_conn is not None:
            raise RuntimeError(
                f"Cannot export '{self._name}' while a transaction is active."
            )

        target_path = Path(target_path).resolve()
        if target_path.exists():
            raise FileExistsError(
                f"Export target '{target_path}' already exists. "
                f"Delete it first or choose a different path."
            )

        tables = {}
        for table_name in self.GetTables():
            rows = self._execute(
                f"SELECT * FROM [{table_name}]",
                commit=True,
                fetch=True,
            )
            tables[table_name] = rows

        export_data = {
            "database": self._name,
            "exported_at": datetime.now().isoformat(),
            "tables": tables,
        }

        with open(str(target_path), "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

        DBMgr._log(f"Database '{self._name}' exported to {target_path}.", "Info")

    def Import(self, source_path: Union[str, Path]) -> None:
        """Import tables from a JSON file into the bound database.

        All tables are imported in a single transaction. Tables are created
        automatically if they do not exist (all columns default to ``TEXT`` type).
        Existing tables have rows appended.

        Args:
            source_path: Path to a JSON file previously created by ``Export()``.

        Raises:
            FileNotFoundError: If *source_path* does not exist.
            ValueError: If the JSON structure is invalid.
        """
        source_path = Path(source_path).resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Import source not found: '{source_path}'.")

        with open(str(source_path), "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Malformed JSON in '{source_path}': {e}") from e

        if "tables" not in data or not isinstance(data["tables"], dict):
            raise ValueError(
                "Import JSON must contain a 'tables' key with a dictionary "
                "of table name → rows."
            )

        self.BeginTransaction()
        try:
            for table_name, rows in data["tables"].items():
                self._validate_identifier(table_name)
                if not rows:
                    continue

                # Infer columns from first row
                columns = list(rows[0].keys())

                # Create table if it doesn't exist
                if not self.TableExists(table_name, commit=False):
                    col_defs = [(c, "TEXT") for c in columns]
                    self.CreateTable(table_name, col_defs, commit=False)

                # Insert rows
                for row in rows:
                    fields = list(row.keys())
                    vals = [row.get(c) for c in fields]
                    self.Insert(table_name, fields, vals, commit=False)

            self.EndTransaction("COMMIT")
        except Exception:
            try:
                self.EndTransaction("ROLLBACK")
            except Exception:
                pass
            raise

        DBMgr._log(f"Import from {source_path} into '{self._name}' completed.", "Info")

    def Vacuum(self) -> None:
        """Rebuild the bound database file, reclaiming unused space.

        Raises:
            RuntimeError: If a transaction is active.
        """
        if self._tx_conn is not None:
            raise RuntimeError(
                f"Cannot vacuum '{self._name}' while a transaction is active."
            )

        conn = self._open_connection()
        try:
            conn.execute("VACUUM")
        finally:
            DBMgr._close_connection(conn)

        DBMgr._log(f"Vacuum completed on '{self._name}'.", "Info")

    # =======================================================================
    # PUBLIC API — Execute failsafe (Phase 14)
    # =======================================================================

    def Execute(self, sql: str, params: Optional[tuple] = None, commit: bool = True) -> Any:
        """Execute a raw SQL statement — the failsafe escape hatch.

        Auto-detects the statement type and returns the appropriate result:
        - ``SELECT`` / ``PRAGMA`` / ``WITH`` / ``EXPLAIN`` → ``list[dict]``
        - ``INSERT`` / ``UPDATE`` / ``DELETE`` / ``REPLACE`` → ``int``
        - DDL (``CREATE``, ``ALTER``, ``DROP``, etc.) → ``None``

        Args:
            sql: Raw SQL string with ``?`` placeholders.
            params: Tuple of bind parameters.
            commit: If ``True`` (default), auto-commits.

        Returns:
            ``list[dict]``, ``int``, or ``None`` depending on statement type.
        """
        stmt_type = sql.strip().split(None, 1)[0].upper() if sql.strip() else ""

        if stmt_type in ("SELECT", "PRAGMA", "WITH", "EXPLAIN"):
            return self._execute(sql, params, commit=commit, fetch=True)

        if stmt_type in ("INSERT", "UPDATE", "DELETE", "REPLACE"):
            return self._execute(sql, params, commit=commit, fetch=False)

        # DDL — execute without expecting a return value
        self._execute(sql, params, commit=commit, fetch=False)
        return None
