from .database_src import Account, DBMgr, Settings


class Database:
    """Project database namespace."""

    DBMgr = DBMgr
    Account = Account
    Settings = Settings
