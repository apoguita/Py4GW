# DBMgr Handover

## What exists

`test_sqlite3.py` — 258-line prototype with a DBMgr class that:
- Manages multiple SQLite databases by alias
- Uses structured helpers (Insert/Update/Delete — no raw SQL in the call)
- Opens/closes connections per operation
- Path resolution via Py4GW.Console.get_projects_path()

## What was discussed

- WAL journal mode for concurrency
- PRIMARY catalog database tracking registered databases
- Short-lived connections (Py4GW can terminate anytime)
- Explicit BeginTransaction/EndTransaction API
- Backup/export/import
- Corruption recovery
- Logging via Py4GW.Console.Log
- Guidance features (Help(), descriptive errors)

## Key design rule

The manager writes the SQL, not the user. Insert/Update/Delete already follow this. Select should too.

## Files to reference

Only `test_sqlite3.py` (the original prototype).
