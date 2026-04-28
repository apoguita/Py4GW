from ctypes import Structure, c_wchar, c_uint, c_bool
from .Globals import SHMEM_MAX_EMAIL_LEN


class IntentStruct(Structure):
    """Cross-hero cast-intent slot posted just before a coordinated cast.

    Heroes in the same IsolationGroupID read these slots to skip
    (SkillID, TargetAgentID) combos another hero already claimed. Slots
    expire three ways: time budget (now >= ExpiresAtTick treated as empty),
    owner self-clear when IsCasting() drops false, and periodic sweep.
    """

    _pack_ = 1
    _fields_ = [
        ("OwnerEmail", c_wchar * SHMEM_MAX_EMAIL_LEN),
        ("SkillID", c_uint),
        ("TargetAgentID", c_uint),
        ("IsolationGroupID", c_uint),
        ("PostedAtTick", c_uint),
        ("ExpiresAtTick", c_uint),
        ("Active", c_bool),
    ]

    OwnerEmail: str
    SkillID: int
    TargetAgentID: int
    IsolationGroupID: int
    PostedAtTick: int
    ExpiresAtTick: int
    Active: bool

    def reset(self) -> None:
        """Reset all fields to zero / default values."""
        self.OwnerEmail = ""
        self.SkillID = 0
        self.TargetAgentID = 0
        self.IsolationGroupID = 0
        self.PostedAtTick = 0
        self.ExpiresAtTick = 0
        self.Active = False
