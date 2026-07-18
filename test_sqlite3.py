"""
DBMgr integration test panel for the Py4GW runtime environment.

This script is frame-safe: main() only draws a control window.
The database test runs only when triggered by the user.
"""

import os
import shutil
import sys
from pathlib import Path

# Py4GW runtime dependency for logging in this test environment.
import Py4GW  # noqa: F401
from Py4GWCoreLib.DBMgr import DBMgr
import PyImGui


MODULE_NAME = "DBMgr Test"
WINDOW_NAME = "DBMgr Integration Test##dbmgr_test"
TEST_NAME = "test_integration_db"
TEST_FILENAME = "test_integration.db"
IMPORT_NAME = "test_import_db"
PLAYERS_TABLE = "players"
LOG_LIMIT = 120
DB_FILE_PATTERNS = ("*.db", "*.db-wal", "*.db-shm", "*.sqlite", "*.sqlite-wal", "*.sqlite-shm", "*.sqlite3")

_status = "Idle"
_last_error = ""
_logs: list[str] = []
_last_run_ok = False

def _log(message: str) -> None:
    """Log to Py4GW and keep a small in-memory history for the test window."""
    global _logs
    Py4GW.Console.Log(MODULE_NAME, message, Py4GW.Console.MessageType.Notice)
    _logs.append(message)
    if len(_logs) > LOG_LIMIT:
        _logs = _logs[-LOG_LIMIT:]


def _set_status(message: str, ok: bool | None = None) -> None:
    """Update the UI status line."""
    global _status, _last_run_ok
    _status = message
    if ok is not None:
        _last_run_ok = ok


def _assert(condition: bool, message: str) -> None:
    """Raise AssertionError with a readable message."""
    if not condition:
        raise AssertionError(message)


def _projects_data_path() -> Path:
    """Return the test artifact root under the projects data directory."""
    return Path(Py4GW.Console.get_projects_path()).resolve() / "data" / "dbmgr_tests"


def _workspace_root() -> Path:
    """Return the repository root for file scanning and cleanup."""
    return Path(os.getcwd()).resolve()


def _data_root() -> Path:
    """Return the DBMgr data root that all managed files should live under."""
    return Path(Py4GW.Console.get_projects_path()).resolve() / "data"


def _backup_folder() -> Path:
    """Return the backup folder used by this integration test."""
    return _projects_data_path() / "backups"


def _export_path() -> Path:
    """Return the export file path used by this integration test."""
    return _projects_data_path() / "test_export.json"


def _db(name: str) -> DBMgr:
    """Return the singleton DBMgr rebound to the requested database."""
    return DBMgr(name)


def _cleanup_test_artifacts() -> None:
    """Remove databases and files created by this test."""
    backup_folder = _backup_folder()
    export_path = _export_path()
    primary = _db("PRIMARY")

    for name in (IMPORT_NAME, TEST_NAME):
        if primary.Has(name):
            primary.Unregister(name, delete_file=True)

    if export_path.exists():
        export_path.unlink()

    if backup_folder.exists():
        shutil.rmtree(str(backup_folder), ignore_errors=True)

    artifacts_root = _projects_data_path()
    if artifacts_root.exists():
        try:
            artifacts_root.rmdir()
        except OSError:
            pass


def _collect_db_files() -> list[Path]:
    """Return all SQLite database files and sidecars under /data only."""
    data_root = _data_root()
    files: set[Path] = set()
    if not data_root.exists():
        return []
    for pattern in DB_FILE_PATTERNS:
        files.update(path.resolve() for path in data_root.rglob(pattern) if path.is_file())
    return sorted(files)


def _collect_backup_dirs() -> list[Path]:
    """Return backup-like directories under /data only."""
    data_root = _data_root()
    if not data_root.exists():
        return []
    return sorted(
        path.resolve()
        for path in data_root.rglob("*")
        if path.is_dir() and "backup" in path.name.lower()
    )


def _log_db_inventory(header: str = "DB Inventory") -> None:
    """Log the current database and backup files present in /data."""
    db_files = _collect_db_files()
    backup_dirs = _collect_backup_dirs()

    _log(f"--- {header} ---")
    _log(f"Data root: {_data_root()}")
    _log(f"DB file count: {len(db_files)}")
    for path in db_files:
        _log(f"DB: {path}")
    _log(f"Backup dir count: {len(backup_dirs)}")
    for path in backup_dirs:
        _log(f"BackupDir: {path}")


def _cleanup_all_db_files() -> None:
    """Delete all SQLite database files and sidecars under /data."""
    deleted = 0
    failed: list[str] = []
    for path in _collect_db_files():
        try:
            path.unlink()
            deleted += 1
        except OSError as exc:
            failed.append(f"{path}: {exc}")

    _log(f"Deleted DB-related files under /data: {deleted}")
    for entry in failed:
        _log(f"Delete failed: {entry}")


def _verify_lifecycle() -> None:
    _log("--- Lifecycle ---")
    primary = _db("PRIMARY")
    path = primary.Register(TEST_NAME, TEST_FILENAME)
    _assert(path.exists(), "Register: database file was not created")
    _assert(primary.Has(TEST_NAME), "Has: test database should be registered")

    db_list = primary.List()
    _assert(TEST_NAME in db_list, "List: test database should appear in catalog")
    _assert("PRIMARY" in db_list, "List: PRIMARY should appear in catalog")
    _log(f"Registered {TEST_NAME} at {path}")


def _verify_schema() -> None:
    _log("--- DDL ---")
    db = _db(TEST_NAME)
    db.CreateTable(
        PLAYERS_TABLE,
        [
            ("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT"),
            ("name", "TEXT", "NOT NULL"),
            ("score", "INTEGER", "DEFAULT 0"),
        ],
    )

    _assert(db.TableExists(PLAYERS_TABLE), "TableExists: players should exist")
    _assert(PLAYERS_TABLE in db.GetTables(), "GetTables: should contain players")

    schema = db.GetSchema(PLAYERS_TABLE)
    _assert(len(schema) == 3, f"GetSchema: expected 3 columns, got {len(schema)}")
    _assert(schema[0]["pk"] == 1, "GetSchema: id should be the primary key")

    columns = db.GetColumns(PLAYERS_TABLE)
    _assert(columns == ["id", "name", "score"], f"GetColumns: unexpected columns {columns}")
    _log("DDL + schema checks passed")


def _seed_players() -> None:
    _log("--- DML ---")
    db = _db(TEST_NAME)

    rowid = db.Insert(PLAYERS_TABLE, ["name", "score"], ["Alice", 100])
    _assert(rowid > 0, f"Insert: expected positive rowid, got {rowid}")
    db.Insert(PLAYERS_TABLE, ["name", "score"], ["Bob", 200])
    db.Insert(PLAYERS_TABLE, ["name", "score"], ["Charlie", 300])

    rows = db.Select(PLAYERS_TABLE)
    _assert(len(rows) == 3, f"Select(*): expected 3 rows, got {len(rows)}")
    _assert(db.Count(PLAYERS_TABLE) == 3, "Count: expected 3 total rows")
    _assert(db.Count(PLAYERS_TABLE, where={"score": 200}) == 1, "Count WHERE: expected 1 row")
    _log("Insert + Select + Count passed")


def _verify_updates_and_merge() -> None:
    _log("--- Update / Delete / Merge ---")
    db = _db(TEST_NAME)

    affected = db.Update(PLAYERS_TABLE, {"score": 150}, where={"name": "Alice"})
    _assert(affected == 1, f"Update: expected 1 affected row, got {affected}")
    alice_updated = db.GetFirstEntry(PLAYERS_TABLE, "name", "Alice")
    if alice_updated is None:
        raise AssertionError("Update verify: Alice should exist")
    _assert(alice_updated["score"] == 150, "Update verify failed")

    deleted = db.Delete(PLAYERS_TABLE, where={"name": "Bob"})
    _assert(deleted == 1, f"Delete: expected 1 row deleted, got {deleted}")
    _assert(db.Count(PLAYERS_TABLE) == 2, "Delete verify: expected 2 rows remaining")

    db.Merge(PLAYERS_TABLE, ["id", "name", "score"], [alice_updated["id"], "Alice", 999])
    alice = db.GetFirstEntry(PLAYERS_TABLE, "name", "Alice")
    if alice is None:
        raise AssertionError("Merge: Alice should exist after update")
    _assert(alice["score"] == 999, f"Merge update: expected 999, got {alice['score']}")
    _assert(db.Count(PLAYERS_TABLE) == 2, "Merge update: expected row count to remain 2")

    db.Merge(PLAYERS_TABLE, ["name", "score"], ["Diana", 400])
    _assert(db.Count(PLAYERS_TABLE) == 3, "Merge insert: expected 3 rows after insert")
    _log("Update + Delete + Merge passed")


def _verify_introspection() -> None:
    _log("--- Introspection ---")
    db = _db(TEST_NAME)

    _assert(db.ColumnExists(PLAYERS_TABLE, "name"), "ColumnExists: name should exist")
    _assert(not db.ColumnExists(PLAYERS_TABLE, "nonexistent"), "ColumnExists: nonexistent should be False")
    _assert(db.EntryExists(PLAYERS_TABLE, "name", "Alice"), "EntryExists: Alice should exist")
    _assert(not db.EntryExists(PLAYERS_TABLE, "name", "Nobody"), "EntryExists: Nobody should not exist")
    _assert(db.EntryCount(PLAYERS_TABLE, "score", 0) == 0, "EntryCount: expected zero rows with score 0")

    entry = db.GetFirstEntry(PLAYERS_TABLE, "name", "Charlie")
    if entry is None:
        raise AssertionError("GetEntry: Charlie should exist")
    _assert(entry["score"] == 300, f"GetEntry: expected Charlie score 300, got {entry['score']}")

    _assert(db.GetFirstEntry(PLAYERS_TABLE, "name", "Nobody") is None, "GetEntry: Nobody should not exist")
    _assert(len(db.GetDistinct(PLAYERS_TABLE, "score")) == 3, "GetDistinct: expected 3 values")
    _assert(db.GetMin(PLAYERS_TABLE, "score") == 300, "GetMin: expected 300")
    _assert(db.GetMax(PLAYERS_TABLE, "score") == 999, "GetMax: expected 999")
    _assert(db.GetColumnType(PLAYERS_TABLE, "name") == "TEXT", "GetColumnType: expected TEXT")
    _log("Introspection helpers passed")


def _verify_transactions() -> None:
    _log("--- Transactions ---")
    db = _db(TEST_NAME)

    db.BeginTransaction()
    db.Insert(PLAYERS_TABLE, ["name", "score"], ["Eve", 500], commit=False)
    db.Insert(PLAYERS_TABLE, ["name", "score"], ["Frank", 600], commit=False)
    db.EndTransaction("COMMIT")
    _assert(db.Count(PLAYERS_TABLE) == 5, "Transaction COMMIT: expected 5 rows")

    db.BeginTransaction()
    db.Insert(PLAYERS_TABLE, ["name", "score"], ["Bad", 0], commit=False)
    db.EndTransaction("ROLLBACK")
    _assert(db.Count(PLAYERS_TABLE) == 5, "Transaction ROLLBACK: row count should remain 5")
    _log("Transaction commit + rollback passed")


def _verify_maintenance() -> None:
    _log("--- Maintenance ---")
    projects_root = _projects_data_path()
    backup_folder = _backup_folder()
    export_path = _export_path()
    primary = _db("PRIMARY")
    db = _db(TEST_NAME)

    projects_root.mkdir(parents=True, exist_ok=True)
    backup_folder.mkdir(parents=True, exist_ok=True)
    backup_path = db.Backup(backup_folder)
    _assert(backup_path.is_dir(), "Backup: backup directory should exist")
    _assert((backup_path / TEST_FILENAME).exists(), "Backup: database file missing from backup")
    _log(f"Backup path on disk: {backup_path}")
    for path in sorted(backup_path.iterdir()):
        _log(f"Backup file: {path}")

    if export_path.exists():
        export_path.unlink()
    db.Export(export_path)
    _assert(export_path.exists(), "Export: JSON export file should exist")
    _log(f"Export path on disk: {export_path}")

    if primary.Has(IMPORT_NAME):
        primary.Unregister(IMPORT_NAME, delete_file=True)
    primary.Register(IMPORT_NAME, "test_import.db")
    import_db_path = _workspace_root() / "data" / "test_import.db"
    _assert(import_db_path.exists(), f"Import DB file missing: {import_db_path}")
    _log(f"Import DB path on disk: {import_db_path}")

    import_db = _db(IMPORT_NAME)
    import_db.Import(export_path)
    _assert(import_db.TableExists(PLAYERS_TABLE), "Import: players table should exist")
    _assert(import_db.Count(PLAYERS_TABLE) == 5, "Import: expected 5 imported rows")

    primary = _db("PRIMARY")
    primary.Unregister(IMPORT_NAME, delete_file=True)
    if export_path.exists():
        export_path.unlink()

    db = _db(TEST_NAME)
    db.Vacuum()
    _log_db_inventory("Post-Maintenance Inventory")
    _log("Backup + Export/Import + Vacuum passed")


def _verify_execute_and_advanced_ddl() -> None:
    _log("--- Execute + Advanced DDL ---")
    db = _db(TEST_NAME)

    result = db.Execute("SELECT COUNT(*) as c FROM players")
    _assert(isinstance(result, list), f"Execute SELECT: expected list, got {type(result)}")
    _assert(result[0]["c"] == 5, f"Execute SELECT: expected count 5, got {result[0]['c']}")

    result = db.Execute("INSERT INTO players (name, score) VALUES (?, ?)", ("Grace", 700))
    _assert(isinstance(result, int), f"Execute INSERT: expected int, got {type(result)}")

    result = db.Execute("CREATE TABLE IF NOT EXISTS temp_test (x INTEGER)")
    _assert(result is None, f"Execute DDL: expected None, got {type(result)}")
    db.DropTable("temp_test")

    db.RenameTable(PLAYERS_TABLE, "contestants")
    _assert(db.TableExists("contestants"), "RenameTable: contestants should exist")
    _assert(not db.TableExists(PLAYERS_TABLE), "RenameTable: players should be gone")

    db.AddColumn("contestants", "active", "INTEGER", "DEFAULT 1")
    _assert(db.ColumnExists("contestants", "active"), "AddColumn: active should exist")

    db.RenameColumn("contestants", "active", "is_active")
    _assert(db.ColumnExists("contestants", "is_active"), "RenameColumn: is_active should exist")
    _assert(not db.ColumnExists("contestants", "active"), "RenameColumn: active should be gone")

    db.DropColumn("contestants", "is_active")
    _assert(not db.ColumnExists("contestants", "is_active"), "DropColumn: is_active should be gone")

    db.RenameTable("contestants", PLAYERS_TABLE)
    _log("Execute + advanced DDL passed")


def _run_full_test() -> None:
    """Run the full DBMgr integration test suite once."""
    global _last_error
    _last_error = ""
    _set_status("Running...", None)
    _logs.clear()

    try:
        _cleanup_test_artifacts()
        _log_db_inventory("Pre-Test Inventory")
        _verify_lifecycle()
        _verify_schema()
        _seed_players()
        _verify_updates_and_merge()
        _verify_introspection()
        _verify_transactions()
        _verify_maintenance()
        _verify_execute_and_advanced_ddl()

        db = _db(TEST_NAME)
        db.DropTable(PLAYERS_TABLE)
        _assert(not db.TableExists(PLAYERS_TABLE), "Cleanup: players table should be dropped")

        _set_status("Passed", True)
        _log_db_inventory("Pre-Final-Cleanup Inventory")
        _log("=== All tests passed ===")
    except Exception as exc:
        _last_error = str(exc)
        _set_status("Failed", False)
        _log(f"FAILED: {exc}")
    finally:
        try:
            _cleanup_test_artifacts()
        except Exception as cleanup_exc:
            _log(f"Cleanup warning: {cleanup_exc}")


def _draw_window() -> None:
    """Draw the frame-safe interactive test window."""
    global _last_error

    if not PyImGui.begin(WINDOW_NAME, True, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.end()
        return

    PyImGui.text("DBMgr integration test")
    PyImGui.text(f"Status: {_status}")
    status_color = (0.2, 1.0, 0.2, 1.0) if _last_run_ok else (1.0, 0.7, 0.2, 1.0)
    if _status == "Failed":
        status_color = (1.0, 0.3, 0.3, 1.0)
    PyImGui.text_colored(f"Result: {'PASS' if _last_run_ok else 'IDLE/FAIL'}", status_color)
    PyImGui.text(f"Projects data: {_projects_data_path()}")
    PyImGui.separator()

    if PyImGui.button("Run Full Test"):
        _run_full_test()
    PyImGui.same_line(0.0, -1.0)
    if PyImGui.button("Cleanup Artifacts"):
        try:
            _cleanup_test_artifacts()
            _set_status("Artifacts cleaned", None)
            _log("Artifacts cleaned")
        except Exception as exc:
            _last_error = str(exc)
            _set_status("Cleanup failed", False)
            _log(f"Cleanup failed: {exc}")
    PyImGui.same_line(0.0, -1.0)
    if PyImGui.button("Scan DB Files"):
        try:
            _log_db_inventory("Manual Inventory")
            _set_status("Scanned DB files", None)
        except Exception as exc:
            _last_error = str(exc)
            _set_status("Scan failed", False)
            _log(f"Scan failed: {exc}")
    PyImGui.same_line(0.0, -1.0)
    if PyImGui.button("Cleanup All .db Files"):
        try:
            _cleanup_all_db_files()
            _set_status("Cleaned all DB files", None)
            _log_db_inventory("Post-Delete Inventory")
        except Exception as exc:
            _last_error = str(exc)
            _set_status("DB cleanup failed", False)
            _log(f"DB cleanup failed: {exc}")

    if _last_error:
        PyImGui.separator()
        PyImGui.text_colored(f"Last error: {_last_error}", (1.0, 0.3, 0.3, 1.0))

    PyImGui.separator()
    PyImGui.text(f"Log entries: {len(_logs)}")
    if PyImGui.begin_child("##dbmgr_test_log", (700.0, 320.0), True):
        for line in _logs[-50:]:
            PyImGui.text(line)
        PyImGui.end_child()

    PyImGui.end()


def main() -> None:
    """Called every frame by the Py4GW runtime."""
    _draw_window()


if __name__ == "__main__":
    main()
