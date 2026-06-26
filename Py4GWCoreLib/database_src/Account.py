from typing import Optional, cast
from .DBMgr import DBMgr

class Account(DBMgr):
    """Project-focused helpers for the Py4GW accounts database."""

    DATABASE_NAME = 'Py4GW_Accounts'
    ACCOUNT_TABLE = 'Account'
    CHARACTER_TABLE = 'Character'
    TEAM_TABLE = 'Team'
    TEAM_NAME_TABLE = 'Team_Name'
    ACCOUNT_KEY_COLUMN = 'ID'
    EMAIL_COLUMN = 'Email'
    CHARACTER_KEY_COLUMN = 'ID'
    CHARACTER_ACCOUNT_KEY_COLUMN = 'AccountID'
    CHARACTER_NAME_COLUMN = 'Name'
    TEAM_KEY_COLUMN = 'ID'
    TEAM_NAME_KEY_COLUMN = 'ID'
    TEAM_NAME_COLUMN = 'Name'
    TEAM_FOREIGN_KEY_COLUMN = 'TeamID'
    TEAM_CHARACTER_KEY_COLUMN = 'CharacterID'

    def __new__(cls) -> 'Account':
        return cast('Account', super().__new__(cls, cls.DATABASE_NAME))

    def __init__(self) -> None:
        super().__init__(self.DATABASE_NAME)

    @staticmethod
    def _normalize_email(email: str) -> str:
        return str(email).strip()

    def GetAccountData(self, email: str, commit: bool = True) -> Optional[dict]:
        """Return the account row for *email*, or ``None`` if missing."""
        return self.GetFirstEntry(self.ACCOUNT_TABLE, self.EMAIL_COLUMN, self._normalize_email(email), commit=commit)

    def GetAccountKey(self, email: str, commit: bool = True) -> Optional[int]:
        """Return the account primary key for *email*, or ``None`` if missing."""
        row = self.GetAccountData(email, commit=commit)
        if row is None:
            return None
        return int(row[self.ACCOUNT_KEY_COLUMN])

    def GetAccountDataByKey(self, account_id: int, commit: bool = True) -> Optional[dict]:
        return self.GetFirstEntry(self.ACCOUNT_TABLE, self.ACCOUNT_KEY_COLUMN, int(account_id), commit=commit)

    def GetAllAccounts(self, commit: bool = True) -> list[dict]:
        return self.Select(self.ACCOUNT_TABLE, order_by=self.ACCOUNT_KEY_COLUMN, commit=commit)

    def CreateAccount(
        self,
        email: str,
        password: str,
        gw_client_path: str,
        extra_args: Optional[str] = None,
        is_password_encrypted: int = 0,
        run_as_admin: int = 0,
        inject_py4gw: int = 1,
        inject_gmod: int = 0,
        gmod_mods: Optional[str] = None,
        startup_script: Optional[str] = None,
        hwnd: Optional[int] = None,
        commit: bool = True,
    ) -> int:
        return self.Insert(
            self.ACCOUNT_TABLE,
            [
                'Email',
                'Password',
                'is_password_encrypted',
                'GW_Client_Path',
                'Extra_Args',
                'run_as_admin',
                'inject_py4gw',
                'inject_gmod',
                'gmod_mods',
                'startup_script',
                'HWND',
            ],
            [
                self._normalize_email(email),
                password,
                int(is_password_encrypted),
                gw_client_path,
                extra_args,
                int(run_as_admin),
                int(inject_py4gw),
                int(inject_gmod),
                gmod_mods,
                startup_script,
                hwnd,
            ],
            commit=commit,
        )

    def SetAccountData(self, email: str, data: dict, commit: bool = True) -> int:
        return self.Update(
            self.ACCOUNT_TABLE,
            data,
            where={self.EMAIL_COLUMN: self._normalize_email(email)},
            commit=commit,
        )

    def SetAccountDataByKey(self, account_id: int, data: dict, commit: bool = True) -> int:
        return self.Update(
            self.ACCOUNT_TABLE,
            data,
            where={self.ACCOUNT_KEY_COLUMN: int(account_id)},
            commit=commit,
        )

    def DeleteAccount(self, email: str, commit: bool = True) -> int:
        return self.Delete(
            self.ACCOUNT_TABLE,
            where={self.EMAIL_COLUMN: self._normalize_email(email)},
            commit=commit,
        )

    def DeleteAccountByKey(self, account_id: int, commit: bool = True) -> int:
        return self.Delete(self.ACCOUNT_TABLE, where={self.ACCOUNT_KEY_COLUMN: int(account_id)}, commit=commit)

    def GetCharacterData(self, character_id: int, commit: bool = True) -> Optional[dict]:
        return self.GetFirstEntry(self.CHARACTER_TABLE, self.CHARACTER_KEY_COLUMN, int(character_id), commit=commit)

    def GetCharacterByName(self, account_id: int, name: str, commit: bool = True) -> Optional[dict]:
        rows = self.Select(
            self.CHARACTER_TABLE,
            where={
                self.CHARACTER_ACCOUNT_KEY_COLUMN: int(account_id),
                self.CHARACTER_NAME_COLUMN: str(name).strip(),
            },
            limit=1,
            commit=commit,
        )
        return rows[0] if rows else None

    def GetCharactersByAccountKey(self, account_id: int, commit: bool = True) -> list[dict]:
        return self.Select(
            self.CHARACTER_TABLE,
            where={self.CHARACTER_ACCOUNT_KEY_COLUMN: int(account_id)},
            order_by=self.CHARACTER_KEY_COLUMN,
            commit=commit,
        )

    def GetCharactersByEmail(self, email: str, commit: bool = True) -> list[dict]:
        account_id = self.GetAccountKey(email, commit=commit)
        if account_id is None:
            return []
        return self.GetCharactersByAccountKey(account_id, commit=commit)

    def CreateCharacter(
        self,
        account_id: int,
        name: str,
        profession: Optional[str] = None,
        level: Optional[int] = None,
        commit: bool = True,
    ) -> int:
        return self.Insert(
            self.CHARACTER_TABLE,
            ['AccountID', 'Name', 'Profession', 'Level'],
            [int(account_id), str(name).strip(), profession, level],
            commit=commit,
        )

    def SetCharacterData(self, character_id: int, data: dict, commit: bool = True) -> int:
        return self.Update(
            self.CHARACTER_TABLE,
            data,
            where={self.CHARACTER_KEY_COLUMN: int(character_id)},
            commit=commit,
        )

    def DeleteCharacter(self, character_id: int, commit: bool = True) -> int:
        return self.Delete(
            self.CHARACTER_TABLE,
            where={self.CHARACTER_KEY_COLUMN: int(character_id)},
            commit=commit,
        )

    def GetTeamNameData(self, team_name_id: int, commit: bool = True) -> Optional[dict]:
        return self.GetFirstEntry(self.TEAM_NAME_TABLE, self.TEAM_NAME_KEY_COLUMN, int(team_name_id), commit=commit)

    def GetTeamNameByName(self, name: str, commit: bool = True) -> Optional[dict]:
        return self.GetFirstEntry(self.TEAM_NAME_TABLE, self.TEAM_NAME_COLUMN, str(name).strip(), commit=commit)

    def GetTeamNameKey(self, name: str, commit: bool = True) -> Optional[int]:
        row = self.GetTeamNameByName(name, commit=commit)
        if row is None:
            return None
        return int(row[self.TEAM_NAME_KEY_COLUMN])

    def GetAllTeamNames(self, commit: bool = True) -> list[dict]:
        return self.Select(self.TEAM_NAME_TABLE, order_by=self.TEAM_NAME_KEY_COLUMN, commit=commit)

    def CreateTeamName(self, name: str, commit: bool = True) -> int:
        return self.Insert(self.TEAM_NAME_TABLE, ['Name'], [str(name).strip()], commit=commit)

    def SetTeamNameData(self, team_name_id: int, data: dict, commit: bool = True) -> int:
        return self.Update(
            self.TEAM_NAME_TABLE,
            data,
            where={self.TEAM_NAME_KEY_COLUMN: int(team_name_id)},
            commit=commit,
        )

    def DeleteTeamName(self, team_name_id: int, commit: bool = True) -> int:
        return self.Delete(
            self.TEAM_NAME_TABLE,
            where={self.TEAM_NAME_KEY_COLUMN: int(team_name_id)},
            commit=commit,
        )

    def GetTeamEntry(self, team_entry_id: int, commit: bool = True) -> Optional[dict]:
        return self.GetFirstEntry(self.TEAM_TABLE, self.TEAM_KEY_COLUMN, int(team_entry_id), commit=commit)

    def GetTeamEntriesByTeamNameKey(self, team_name_id: int, commit: bool = True) -> list[dict]:
        return self.Select(
            self.TEAM_TABLE,
            where={self.TEAM_FOREIGN_KEY_COLUMN: int(team_name_id)},
            order_by=self.TEAM_KEY_COLUMN,
            commit=commit,
        )

    def GetTeamEntriesByTeamName(self, name: str, commit: bool = True) -> list[dict]:
        team_name_id = self.GetTeamNameKey(name, commit=commit)
        if team_name_id is None:
            return []
        return self.GetTeamEntriesByTeamNameKey(team_name_id, commit=commit)

    def GetCharacterTeamEntry(self, character_id: int, commit: bool = True) -> Optional[dict]:
        return self.GetFirstEntry(self.TEAM_TABLE, self.TEAM_CHARACTER_KEY_COLUMN, int(character_id), commit=commit)

    def CreateTeamEntry(self, team_name_id: int, character_id: int, commit: bool = True) -> int:
        return self.Insert(
            self.TEAM_TABLE,
            ['TeamID', 'CharacterID'],
            [int(team_name_id), int(character_id)],
            commit=commit,
        )

    def SetTeamEntryData(self, team_entry_id: int, data: dict, commit: bool = True) -> int:
        return self.Update(
            self.TEAM_TABLE,
            data,
            where={self.TEAM_KEY_COLUMN: int(team_entry_id)},
            commit=commit,
        )

    def SetCharacterTeam(self, character_id: int, team_name_id: int, commit: bool = True) -> int:
        existing = self.GetCharacterTeamEntry(character_id, commit=commit)
        if existing is None:
            return self.CreateTeamEntry(team_name_id, character_id, commit=commit)
        self.SetTeamEntryData(existing[self.TEAM_KEY_COLUMN], {'TeamID': int(team_name_id)}, commit=commit)
        return int(existing[self.TEAM_KEY_COLUMN])

    def DeleteTeamEntry(self, team_entry_id: int, commit: bool = True) -> int:
        return self.Delete(self.TEAM_TABLE, where={self.TEAM_KEY_COLUMN: int(team_entry_id)}, commit=commit)
