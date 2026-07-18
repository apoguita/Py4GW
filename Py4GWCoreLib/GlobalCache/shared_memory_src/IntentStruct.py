from ctypes import Structure, c_wchar, c_uint, c_bool
from .Globals import SHMEM_MAX_EMAIL_LEN


class IntentStruct(Structure):
    """Cross-hero whiteboard lock slot.

    SkillID and TargetAgentID are kept as compatibility names for the
    original skill-target whiteboard. Generic lock callers should treat them
    as KeyID and TargetID scoped by KindID.

    Every slot must have ExpiresAtTick set. Readers treat expired slots as
    empty even before the sweep compacts them.
    """

    _pack_ = 1
    _fields_ = [
        ("OwnerEmail", c_wchar * SHMEM_MAX_EMAIL_LEN),
        ("KindID", c_uint),
        ("LockMode", c_uint),
        ("ReentryPolicy", c_uint),
        ("ClaimStrength", c_uint),
        ("MaxHolders", c_uint),
        ("SkillID", c_uint),
        ("TargetAgentID", c_uint),
        ("IsolationGroupID", c_uint),
        ("PostedAtTick", c_uint),
        ("ExpiresAtTick", c_uint),
        ("Active", c_bool),
    ]

    OwnerEmail: str
    KindID: int
    LockMode: int
    ReentryPolicy: int
    ClaimStrength: int
    MaxHolders: int
    SkillID: int
    TargetAgentID: int
    IsolationGroupID: int
    PostedAtTick: int
    ExpiresAtTick: int
    Active: bool

    def reset(self) -> None:
        """Reset all fields to zero / default values."""
        self.OwnerEmail = ""
        self.KindID = 0
        self.LockMode = 0
        self.ReentryPolicy = 0
        self.ClaimStrength = 0
        self.MaxHolders = 0
        self.SkillID = 0
        self.TargetAgentID = 0
        self.IsolationGroupID = 0
        self.PostedAtTick = 0
        self.ExpiresAtTick = 0
        self.Active = False
