from enum import IntEnum


class PlayerStatus(IntEnum):
    Offline = 0
    Online = 1
    DoNotDisturb = 2
    DND = 2
    Away = 3

    @classmethod
    def from_value(cls, status):
        if isinstance(status, cls):
            return status
        if isinstance(status, str):
            normalized = status.strip().lower().replace(" ", "_").replace("-", "_")
            if normalized == "offline":
                return cls.Offline
            if normalized == "online":
                return cls.Online
            if normalized in ("do_not_disturb", "donotdisturb", "dnd"):
                return cls.DoNotDisturb
            if normalized == "away":
                return cls.Away
            return None
        try:
            return cls(int(status))
        except Exception:
            return None

    @property
    def display_name(self) -> str:
        if self == PlayerStatus.DoNotDisturb:
            return "do_not_disturb"
        return self.name.lower()
