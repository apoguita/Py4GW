import os
import sqlite3
from pathlib import Path
from typing import Any

import Py4GW

MODULE_NAME = 'DBMgr Test'
PRIMARY_DB_FILENAME = 'sqlite3_test.db'
ANALYTICS_DB_FILENAME = 'sqlite3_analytics.db'
initialized = False


class DBMgr:
    def __init__(self, timeout: float = 5.0):
        """Create a database manager that opens and closes SQLite connections per operation."""
        self.base_directory = Path('.')
        self.timeout = timeout
        self._database_paths: dict[str, Path] = {}
        self.PRIMARY_DB_FILENAME = 'Py4GW_Internals.db'
        self.Initialize()

    def Initialize(self) -> None:
        """Initialize the manager root path and ensure the PRIMARY database is registered."""
        self.base_directory = self._get_db_root_path()
        self.CreateDatabase('PRIMARY', self.PRIMARY_DB_FILENAME)

    def _get_db_root_path(self) -> Path:
        """Return the project root used to resolve relative database paths."""
        if hasattr(Py4GW, 'Console') and hasattr(Py4GW.Console, 'get_projects_path'):
            projects_path = Py4GW.Console.get_projects_path()
            if projects_path:
                return Path(projects_path)
        return Path(os.getcwd()).resolve()
    
    def _get_db_path(self, alias: str) -> Path:
        """Return the filesystem path registered for a database alias."""
        if alias not in self._database_paths:
            raise KeyError(f'Unknown database alias: {alias}')
        return self._database_paths[alias]
    
    def _resolve_path(self, filename: str | Path) -> Path:
        """Resolve a database filename against the manager base directory."""
        path = Path(filename)
        if not path.is_absolute():
            path = self.base_directory / path
        return path.resolve()

    def CreateDatabase(self, alias: str, filename: str | Path) -> Path:
        """Register a database alias and create the SQLite file if it does not already exist."""
        path = self._resolve_path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(path), timeout=self.timeout)
        self._Close(connection)
        self._database_paths[alias] = path
        return path

    def DeleteDatabase(self, alias: str) -> None:
        """Remove a registered database file from disk and unregister its alias."""
        path = self._get_db_path(alias)
        del self._database_paths[alias]
        if path.exists():
            path.unlink()

    def HasDatabase(self, alias: str) -> bool:
        """Return True when the alias is currently registered."""
        return alias in self._database_paths

    def ListDatabases(self) -> dict[str, str]:
        """Return every registered database alias mapped to its resolved path."""
        return {alias: str(path) for alias, path in self._database_paths.items()}

    def Insert(self, alias: str, table: str, fields: list[str], values: list[Any]) -> int:
        """Insert one row into a table using matching field and value lists."""
        self._ValidateFieldValueCount(fields, values, operation='Insert')
        columns_sql = ', '.join(fields)
        placeholders_sql = ', '.join(['?'] * len(values))
        query = f'INSERT INTO {table} ({columns_sql}) VALUES ({placeholders_sql})'
        return self._ExecuteWrite(alias, query, tuple(values), result='lastrowid')

    def Update(
        self,
        alias: str,
        table: str,
        fields: list[str],
        values: list[Any],
        where_fields: list[str],
        where_values: list[Any],
    ) -> int:
        """Update rows in a table using field/value lists plus equality-based WHERE fields."""
        self._ValidateFieldValueCount(fields, values, operation='Update')
        self._ValidateFieldValueCount(where_fields, where_values, operation='Update WHERE')
        set_sql = ', '.join(f'{field} = ?' for field in fields)
        where_sql = self._BuildWhereClause(where_fields)
        query = f'UPDATE {table} SET {set_sql}{where_sql}'
        parameters = tuple(values + where_values)
        return self._ExecuteWrite(alias, query, parameters, result='rowcount')

    def Delete(self, alias: str, table: str, where_fields: list[str], where_values: list[Any]) -> int:
        """Delete rows from a table using equality-based WHERE fields."""
        self._ValidateFieldValueCount(where_fields, where_values, operation='Delete')
        where_sql = self._BuildWhereClause(where_fields)
        query = f'DELETE FROM {table}{where_sql}'
        return self._ExecuteWrite(alias, query, tuple(where_values), result='rowcount')

    def Select(self, alias: str, query: str, parameters: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        """Run a SELECT query and return all rows as dictionaries."""
        rows = self._ExecuteRead(alias, query, parameters)
        return [dict(row) for row in rows]

    def SelectFirst(self, alias: str, query: str, parameters: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        """Run a SELECT query and return the first row as a dictionary, or None."""
        rows = self.Select(alias, query, parameters)
        if not rows:
            return None
        return rows[0]

    def Execute(self, alias: str, query: str, parameters: tuple[Any, ...] = ()) -> None:
        """Execute a raw SQL statement for cases not covered by the structured helpers."""
        self._ExecuteWrite(alias, query, parameters, result='none')

    def _Open(self, alias: str) -> sqlite3.Connection:
        """Open a new SQLite connection for the given alias."""
        path = self._get_db_path(alias)
        connection = sqlite3.connect(str(path), timeout=self.timeout)
        connection.row_factory = sqlite3.Row
        return connection

    def _Close(self, connection: sqlite3.Connection) -> None:
        """Close a SQLite connection opened by this manager."""
        connection.close()

    def _ExecuteRead(self, alias: str, query: str, parameters: tuple[Any, ...]) -> list[sqlite3.Row]:
        """Execute a read query and return the raw SQLite rows."""
        connection = self._Open(alias)
        try:
            cursor = connection.execute(query, parameters)
            return cursor.fetchall()
        finally:
            self._Close(connection)

    def _ExecuteWrite(self, alias: str, query: str, parameters: tuple[Any, ...], result: str) -> int:
        """Execute a write query and return either the last inserted id or affected row count."""
        connection = self._Open(alias)
        try:
            cursor = connection.execute(query, parameters)
            connection.commit()
            if result == 'lastrowid':
                return int(cursor.lastrowid or 0)
            if result == 'rowcount':
                return int(cursor.rowcount)
            return 0
        finally:
            self._Close(connection)

    def _BuildWhereClause(self, where_fields: list[str]) -> str:
        """Build an equality-only WHERE clause from a list of field names."""
        if not where_fields:
            return ''
        return ' WHERE ' + ' AND '.join(f'{field} = ?' for field in where_fields)

    def _ValidateFieldValueCount(self, fields: list[str], values: list[Any], operation: str) -> None:
        """Validate that a structured write operation received aligned field and value lists."""
        if not fields:
            raise ValueError(f'{operation} requires at least one field')
        if len(fields) != len(values):
            raise ValueError(
                f'{operation} field/value count mismatch: {len(fields)} fields, {len(values)} values'
            )



def _has_py4gw_console() -> bool:
    return Py4GW is not None and hasattr(Py4GW, 'Console') and hasattr(Py4GW.Console, 'Log')


def _log(message: str, message_type=None) -> None:
    if not _has_py4gw_console():
        print(f'[{MODULE_NAME}] {message}')
        return
    if message_type is None:
        message_type = Py4GW.Console.MessageType.Notice
    Py4GW.Console.Log(MODULE_NAME, message, message_type)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    global initialized
    if initialized:
        return

    manager = DBMgr()
    primary_path = manager._get_db_path('PRIMARY')
    database_a_path = manager.CreateDatabase('database_a', 'database_a.db')
    database_b_path = manager.CreateDatabase('database_b', 'database_b.db')

    _log(f'Using primary database: {primary_path}')
    _log(f'SQLite engine version: {sqlite3.sqlite_version}')
    _log(f'Registered databases: {manager.ListDatabases()}')

    manager.Execute(
        'PRIMARY',
        '''
        CREATE TABLE IF NOT EXISTS databases (
            name TEXT PRIMARY KEY,
            path TEXT NOT NULL
        )
        ''',
    )

    existing_database_a = manager.SelectFirst(
        'PRIMARY',
        'SELECT name, path FROM databases WHERE name = ?',
        ('database_a',),
    )
    if existing_database_a is None:
        manager.Insert(
            'PRIMARY',
            'databases',
            ['name', 'path'],
            ['database_a', str(database_a_path)],
        )

    existing_database_b = manager.SelectFirst(
        'PRIMARY',
        'SELECT name, path FROM databases WHERE name = ?',
        ('database_b',),
    )
    if existing_database_b is None:
        manager.Insert(
            'PRIMARY',
            'databases',
            ['name', 'path'],
            ['database_b', str(database_b_path)],
        )

    rows = manager.Select(
        'PRIMARY',
        'SELECT name, path FROM databases ORDER BY name',
    )

    _assert(manager.HasDatabase('PRIMARY'), 'PRIMARY alias missing')
    _assert(len(rows) >= 2, 'expected at least two rows in databases table')

    _log('Primary database registry rows:')
    for row in rows:
        _log(str(row))

    success_type = Py4GW.Console.MessageType.Success if _has_py4gw_console() else None
    _log('DBMgr test completed successfully.', success_type)
    initialized = True

if __name__ == '__main__':
    main()
