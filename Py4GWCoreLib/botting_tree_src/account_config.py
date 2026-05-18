from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Mapping


class BottingTreeAccountMode(str, Enum):
    SINGLE_ACCOUNT = 'single_account'
    MULTI_ACCOUNT = 'multi_account'

    @classmethod
    def coerce(cls, value: 'BottingTreeAccountMode | str | None') -> 'BottingTreeAccountMode':
        if isinstance(value, cls):
            return value
        normalized = str(value or cls.SINGLE_ACCOUNT.value).strip().lower()
        if normalized in {'single', 'single_account', 'single-player', 'single_player', 'solo'}:
            return cls.SINGLE_ACCOUNT
        if normalized in {'multi', 'multi_account', 'multi-account', 'multibox'}:
            return cls.MULTI_ACCOUNT
        raise ValueError(f'Unsupported botting-tree account mode: {value!r}')


@dataclass(slots=True)
class BottingTreeAccountConfig:
    mode: BottingTreeAccountMode = BottingTreeAccountMode.SINGLE_ACCOUNT
    isolation_enabled: bool | None = None
    sync_party_isolation: bool = True
    account_role: str = 'local'
    leader_account_email: str = ''
    controlled_account_emails: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.mode = BottingTreeAccountMode.coerce(self.mode)
        self.account_role = str(self.account_role or 'local').strip().lower() or 'local'
        self.leader_account_email = str(self.leader_account_email or '').strip()
        self.controlled_account_emails = tuple(
            str(email or '').strip()
            for email in self.controlled_account_emails
            if str(email or '').strip()
        )
        self.metadata = dict(self.metadata or {})

    @classmethod
    def coerce(
        cls,
        value: 'BottingTreeAccountConfig | Mapping[str, object] | BottingTreeAccountMode | str | None',
        *,
        multi_account: bool = False,
        isolation_enabled: bool | None = None,
        account_mode: BottingTreeAccountMode | str | None = None,
    ) -> 'BottingTreeAccountConfig':
        resolved_account_mode = account_mode if account_mode is not None else (
            BottingTreeAccountMode.MULTI_ACCOUNT if multi_account else BottingTreeAccountMode.SINGLE_ACCOUNT
        )
        if isinstance(value, cls):
            config = cls(
                mode=value.mode,
                isolation_enabled=value.isolation_enabled,
                sync_party_isolation=value.sync_party_isolation,
                account_role=value.account_role,
                leader_account_email=value.leader_account_email,
                controlled_account_emails=value.controlled_account_emails,
                metadata=value.metadata,
            )
        elif isinstance(value, Mapping):
            config = cls(
                mode=value.get('mode', value.get('account_mode', resolved_account_mode)),
                isolation_enabled=value.get('isolation_enabled', isolation_enabled),
                sync_party_isolation=bool(value.get('sync_party_isolation', True)),
                account_role=str(value.get('account_role', 'local') or 'local'),
                leader_account_email=str(value.get('leader_account_email', '') or ''),
                controlled_account_emails=tuple(value.get('controlled_account_emails', ()) or ()),
                metadata=dict(value.get('metadata', {}) or {}),
            )
        elif value is None:
            config = cls(
                mode=BottingTreeAccountMode.coerce(resolved_account_mode),
                isolation_enabled=isolation_enabled,
            )
        else:
            config = cls(
                mode=BottingTreeAccountMode.coerce(value),
                isolation_enabled=isolation_enabled,
            )

        config.mode = BottingTreeAccountMode.coerce(resolved_account_mode)
        if isolation_enabled is not None:
            config.isolation_enabled = bool(isolation_enabled)
        return config

    def resolve_isolation_enabled(self) -> bool:
        if self.isolation_enabled is not None:
            return bool(self.isolation_enabled)
        return self.mode == BottingTreeAccountMode.SINGLE_ACCOUNT

    def as_blackboard_state(self) -> dict[str, object]:
        mode = BottingTreeAccountMode.coerce(self.mode)
        return {
            'multi_account': mode == BottingTreeAccountMode.MULTI_ACCOUNT,
            'account_mode': mode.value,
            'account_mode_is_single': mode == BottingTreeAccountMode.SINGLE_ACCOUNT,
            'account_mode_is_multi': mode == BottingTreeAccountMode.MULTI_ACCOUNT,
            'account_role': self.account_role,
            'leader_account_email': self.leader_account_email,
            'controlled_account_emails': list(self.controlled_account_emails),
            'sync_party_isolation': bool(self.sync_party_isolation),
            'account_isolation_enabled': self.resolve_isolation_enabled(),
        }
