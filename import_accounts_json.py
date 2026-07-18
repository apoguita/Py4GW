"""
Import accounts.json into the Py4GW_Accounts database.

This script is frame-safe: main() only draws a control window.
The import runs only when explicitly triggered by the user.
"""

import json
from pathlib import Path
from typing import Any

import Py4GW
import PyImGui

from Py4GWCoreLib import Database, Map, Player
from Py4GWCoreLib.enums_src.GameData_enums import Profession, Profession_Names


MODULE_NAME = 'Accounts JSON Importer'
WINDOW_NAME = 'Accounts JSON Importer##accounts_json_importer'
DEFAULT_SOURCE = Path('accounts.json')
LOG_LIMIT = 120

_status = 'Idle'
_last_error = ''
_logs: list[str] = []
_last_run_ok = False


def _log(message: str) -> None:
    global _logs
    Py4GW.Console.Log(MODULE_NAME, message, Py4GW.Console.MessageType.Notice)
    _logs.append(message)
    if len(_logs) > LOG_LIMIT:
        _logs = _logs[-LOG_LIMIT:]


def _set_status(message: str, ok: bool | None = None) -> None:
    global _status, _last_run_ok
    _status = message
    if ok is not None:
        _last_run_ok = ok


def _normalize_text(value: Any) -> str:
    return str(value or '').strip()


def _normalize_optional_text(value: Any) -> str | None:
    text = _normalize_text(value)
    return text or None


def _normalize_bool(value: Any) -> int:
    return int(bool(value))


def _normalize_gmod_mods(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        return json.dumps(value)
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return json.dumps(value)


def _profession_name_from_id(profession_id: int) -> str | None:
    try:
        profession = Profession(int(profession_id))
        name = Profession_Names.get(profession)
        if not name or name == 'None':
            return None
        return str(name)
    except Exception:
        return None


def _ensure_team_name(accounts_db: Database.Account, team_name: str, commit: bool) -> int:
    existing = accounts_db.GetTeamNameKey(team_name, commit=commit)
    if existing is not None:
        return existing
    return accounts_db.CreateTeamName(team_name, commit=commit)


def _ensure_account(accounts_db: Database.Account, entry: dict[str, Any], commit: bool) -> int:
    email = _normalize_text(entry.get('email'))
    if not email:
        raise ValueError('Account entry is missing email.')

    existing_id = accounts_db.GetAccountKey(email, commit=commit)
    account_data = {
        'Password': _normalize_text(entry.get('password')),
        'GW_Client_Path': _normalize_text(entry.get('gw_path')),
        'Extra_Args': _normalize_optional_text(entry.get('extra_args')),
        'run_as_admin': _normalize_bool(entry.get('run_as_admin')),
        'inject_py4gw': _normalize_bool(entry.get('inject_py4gw', True)),
        'inject_gmod': _normalize_bool(entry.get('inject_gmod', False)),
        'gmod_mods': _normalize_gmod_mods(entry.get('gmod_mods')),
        'startup_script': _normalize_optional_text(entry.get('script_path')),
    }

    if existing_id is None:
        return accounts_db.CreateAccount(
            email=email,
            password=account_data['Password'],
            gw_client_path=account_data['GW_Client_Path'],
            extra_args=account_data['Extra_Args'],
            run_as_admin=account_data['run_as_admin'],
            inject_py4gw=account_data['inject_py4gw'],
            inject_gmod=account_data['inject_gmod'],
            gmod_mods=account_data['gmod_mods'],
            startup_script=account_data['startup_script'],
            commit=commit,
        )

    accounts_db.SetAccountDataByKey(existing_id, account_data, commit=commit)
    return existing_id


def _ensure_character(accounts_db: Database.Account, account_id: int, entry: dict[str, Any], commit: bool) -> int:
    character_name = _normalize_text(entry.get('character_name'))
    if not character_name:
        raise ValueError(f'Account {account_id} entry is missing character_name.')

    existing = accounts_db.GetCharacterByName(account_id, character_name, commit=commit)
    if existing is not None:
        return int(existing['ID'])

    return accounts_db.CreateCharacter(account_id, character_name, commit=commit)


def sync_available_characters_for_current_account() -> dict[str, int]:
    account_email = _normalize_text(Player.GetAccountEmail())
    if not account_email:
        raise ValueError('Current account email is not available.')

    account_id = Database.Account().GetAccountKey(account_email)
    if account_id is None:
        raise ValueError(f"Current account '{account_email}' is not registered in Py4GW_Accounts.")

    available_characters = Map.Pregame.GetAvailableCharacterList()
    if not available_characters:
        raise ValueError('No available characters were found for the current client.')

    accounts_db = Database.Account()
    created = 0
    updated = 0

    accounts_db.BeginTransaction()
    try:
        for char in available_characters:
            character_name = _normalize_text(getattr(char, 'player_name', ''))
            if not character_name:
                continue

            profession_name = _profession_name_from_id(int(getattr(char, 'primary', 0) or 0))
            level = int(getattr(char, 'level', 0) or 0)

            existing = accounts_db.GetCharacterByName(account_id, character_name, commit=False)
            if existing is None:
                accounts_db.CreateCharacter(
                    account_id,
                    character_name,
                    profession=profession_name,
                    level=level,
                    commit=False,
                )
                created += 1
                continue

            updates: dict[str, Any] = {}
            if profession_name and existing.get('Profession') != profession_name:
                updates['Profession'] = profession_name
            if int(existing.get('Level') or 0) != level:
                updates['Level'] = level
            if updates:
                accounts_db.SetCharacterData(int(existing['ID']), updates, commit=False)
                updated += 1

        accounts_db.EndTransaction('COMMIT')
    except Exception:
        accounts_db.EndTransaction('ROLLBACK')
        raise

    return {
        'account_id': int(account_id),
        'character_count': len(available_characters),
        'created': created,
        'updated': updated,
    }


def import_accounts_json(source: Path) -> dict[str, int]:
    payload = json.loads(source.read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError('accounts.json must contain an object of team names to account lists.')

    accounts_db = Database.Account()
    imported_entries = 0
    imported_characters = 0
    imported_teams = 0

    accounts_db.BeginTransaction()
    try:
        for team_name, entries in payload.items():
            normalized_team_name = _normalize_text(team_name)
            if not normalized_team_name:
                continue
            if not isinstance(entries, list):
                raise ValueError(f"Team '{team_name}' must contain a list of account entries.")

            team_name_id = _ensure_team_name(accounts_db, normalized_team_name, commit=False)
            imported_teams += 1

            for entry in entries:
                if not isinstance(entry, dict):
                    raise ValueError(f"Team '{team_name}' contains a non-object entry.")

                account_id = _ensure_account(accounts_db, entry, commit=False)
                character_id = _ensure_character(accounts_db, account_id, entry, commit=False)
                accounts_db.SetCharacterTeam(character_id, team_name_id, commit=False)

                imported_entries += 1
                imported_characters += 1

        accounts_db.EndTransaction('COMMIT')
    except Exception:
        accounts_db.EndTransaction('ROLLBACK')
        raise

    return {
        'teams_processed': imported_teams,
        'entries_processed': imported_entries,
        'characters_processed': imported_characters,
    }


def _run_import() -> None:
    global _last_error
    _last_error = ''
    _set_status('Running...', None)

    try:
        result = import_accounts_json(DEFAULT_SOURCE)
        _set_status('Passed', True)
        _log(
            f"Imported {result['entries_processed']} entries, "
            f"{result['characters_processed']} characters across "
            f"{result['teams_processed']} teams from {DEFAULT_SOURCE}."
        )
    except Exception as exc:
        _last_error = str(exc)
        _set_status('Failed', False)
        _log(f'FAILED: {exc}')


def _run_available_character_sync() -> None:
    global _last_error
    _last_error = ''
    _set_status('Running...', None)

    try:
        result = sync_available_characters_for_current_account()
        _set_status('Passed', True)
        _log(
            f"Synced {result['character_count']} available characters for account "
            f"{result['account_id']}: created {result['created']}, updated {result['updated']}."
        )
    except Exception as exc:
        _last_error = str(exc)
        _set_status('Failed', False)
        _log(f'FAILED: {exc}')


def _draw_window() -> None:
    global _last_error

    if not PyImGui.begin(WINDOW_NAME, True, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.end()
        return

    PyImGui.text('Import accounts.json into Py4GW_Accounts')
    PyImGui.text(f'Status: {_status}')
    status_color = (0.2, 1.0, 0.2, 1.0) if _last_run_ok else (1.0, 0.7, 0.2, 1.0)
    if _status == 'Failed':
        status_color = (1.0, 0.3, 0.3, 1.0)
    PyImGui.text_colored(f"Result: {'PASS' if _last_run_ok else 'IDLE/FAIL'}", status_color)
    PyImGui.text(f'Source: {DEFAULT_SOURCE.resolve()}')
    PyImGui.separator()

    if PyImGui.button('Run Import'):
        _run_import()
    PyImGui.same_line(0.0, -1.0)
    if PyImGui.button('Sync Available Characters'):
        _run_available_character_sync()

    if _last_error:
        PyImGui.separator()
        PyImGui.text_colored(f'Last error: {_last_error}', (1.0, 0.3, 0.3, 1.0))

    PyImGui.separator()
    PyImGui.text(f'Log entries: {len(_logs)}')
    if PyImGui.begin_child('##accounts_json_importer_log', (720.0, 320.0), True):
        for line in _logs[-50:]:
            PyImGui.text(line)
        PyImGui.end_child()

    PyImGui.end()


def main() -> None:
    """Called every frame by the Py4GW runtime."""
    _draw_window()


if __name__ == '__main__':
    _run_import()
