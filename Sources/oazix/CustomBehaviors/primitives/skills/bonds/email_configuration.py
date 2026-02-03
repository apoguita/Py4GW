from dataclasses import dataclass


@dataclass
class EmailConfiguration:
    def __init__(self, account_email: str, is_activated: bool):
        self.account_email: str = account_email
        self.is_activated: bool = is_activated
