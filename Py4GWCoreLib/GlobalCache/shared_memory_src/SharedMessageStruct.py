from ctypes import Array, Structure, addressof, c_int, c_uint, c_float, c_bool, c_wchar, memmove, c_uint64, sizeof
from .Globals import (
    SHMEM_MAX_EMAIL_LEN,
    SHMEM_MAX_CHAR_LEN,
)

class SharedMessageStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("SenderEmail", c_wchar * SHMEM_MAX_EMAIL_LEN),
        ("ReceiverEmail", c_wchar * SHMEM_MAX_EMAIL_LEN),
        ("Command", c_uint),
        ("Params", c_float * 4),
        ("ExtraData", (c_wchar * SHMEM_MAX_CHAR_LEN) * 4),
        ("Active", c_bool), 
        ("Running", c_bool),
        ("Timestamp", c_uint), 
    ]
    
    # Type hints for IntelliSense
    SenderEmail: str
    ReceiverEmail: str
    Command: int
    Params: Array[c_float]
    ExtraData: Array
    Active: bool
    Running: bool
    Timestamp: int
    
    def reset(self) -> None:
        """Reset all fields to zero or default values."""
        self.SenderEmail = ""
        self.ReceiverEmail = ""
        self.Command = 0
        for i in range(4):
            self.Params[i] = 0.0
            for j in range(SHMEM_MAX_CHAR_LEN):
                self.ExtraData[i][j] = '\0'
        self.Active = False
        self.Running = False
        self.Timestamp = 0