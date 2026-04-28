import time
from ctypes import Structure, c_wchar, sizeof
from multiprocessing import shared_memory
from typing import Optional

from Py4GWCoreLib import GLOBAL_CACHE, Routines, ThrottledTimer, Utils
from Py4GWCoreLib.Player import Player


MAX_TEAM_VIEWER_SLOTS = 12
MAX_EMAIL_LEN = 64
MAX_TEMPLATE_LEN = 128

_SHM_NAME = "HeroAITeamViewerMemory"
_PUBLISH_INTERVAL_MS = 1000
_WARMUP_SECONDS = 3.0


class HeroAITeamViewerStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("AccountEmails", (c_wchar * MAX_EMAIL_LEN) * MAX_TEAM_VIEWER_SLOTS),
        ("Templates", (c_wchar * MAX_TEMPLATE_LEN) * MAX_TEAM_VIEWER_SLOTS),
    ]


class HeroAITeamViewerMemory:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HeroAITeamViewerMemory, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._size = sizeof(HeroAITeamViewerStruct)
        try:
            self._shm = shared_memory.SharedMemory(name=_SHM_NAME)
        except FileNotFoundError:
            self._shm = shared_memory.SharedMemory(name=_SHM_NAME, create=True, size=self._size)
            self._clear_all()

    def _struct(self) -> HeroAITeamViewerStruct:
        return HeroAITeamViewerStruct.from_buffer(self._shm.buf)

    @staticmethod
    def _read_wchar_array(arr) -> str:
        chars: list[str] = []
        for ch in arr:
            if ch == "\0":
                break
            chars.append(ch)
        return "".join(chars)

    @staticmethod
    def _write_wchar_array(arr, value: str) -> None:
        max_len = len(arr)
        for i in range(max_len):
            arr[i] = "\0"
        if not value:
            return
        for i, ch in enumerate(value):
            if i >= max_len - 1:
                break
            arr[i] = ch

    def _clear_all(self) -> None:
        mem = self._struct()
        for i in range(MAX_TEAM_VIEWER_SLOTS):
            mem.AccountEmails[i][0] = "\0"
            mem.Templates[i][0] = "\0"

    def GetTemplateForEmail(self, email: str) -> Optional[str]:
        if not email:
            return None
        mem = self._struct()
        for i in range(MAX_TEAM_VIEWER_SLOTS):
            slot_email = self._read_wchar_array(mem.AccountEmails[i])
            if slot_email == email:
                template = self._read_wchar_array(mem.Templates[i])
                return template if template else None
        return None

    def SetTemplateForEmail(self, email: str, template: str) -> None:
        if not email:
            return
        mem = self._struct()
        for i in range(MAX_TEAM_VIEWER_SLOTS):
            slot_email = self._read_wchar_array(mem.AccountEmails[i])
            if slot_email == email:
                self._write_wchar_array(mem.Templates[i], template)
                return
        for i in range(MAX_TEAM_VIEWER_SLOTS):
            slot_email = self._read_wchar_array(mem.AccountEmails[i])
            if not slot_email:
                self._write_wchar_array(mem.AccountEmails[i], email)
                self._write_wchar_array(mem.Templates[i], template)
                return

    def ClearSlotForEmail(self, email: str) -> None:
        if not email:
            return
        mem = self._struct()
        for i in range(MAX_TEAM_VIEWER_SLOTS):
            slot_email = self._read_wchar_array(mem.AccountEmails[i])
            if slot_email == email:
                self._write_wchar_array(mem.AccountEmails[i], "")
                self._write_wchar_array(mem.Templates[i], "")
                return

    def GetAllEmails(self) -> list[str]:
        mem = self._struct()
        result: list[str] = []
        for i in range(MAX_TEAM_VIEWER_SLOTS):
            slot_email = self._read_wchar_array(mem.AccountEmails[i])
            if slot_email:
                result.append(slot_email)
        return result


_publish_throttler = ThrottledTimer(_PUBLISH_INTERVAL_MS)
_map_valid_since: Optional[float] = None


def tick() -> None:
    global _map_valid_since

    if not _publish_throttler.IsExpired():
        return

    try:
        map_valid = Routines.Checks.Map.MapValid()
    except Exception:
        _map_valid_since = None
        return

    if not map_valid:
        _map_valid_since = None
        return

    now = time.monotonic()
    if _map_valid_since is None:
        _map_valid_since = now
        return
    if (now - _map_valid_since) < _WARMUP_SECONDS:
        return

    try:
        agent_id = Player.GetAgentID()
        if not agent_id:
            return
    except Exception:
        return

    _publish_throttler.Reset()

    try:
        email = Player.GetAccountEmail()
        if not email:
            return
        template = Utils.GenerateSkillbarTemplate()
        if not template:
            return

        mem = HeroAITeamViewerMemory()
        mem.SetTemplateForEmail(email, template)
    except Exception:
        pass


def get_template_for_email(email: str) -> Optional[str]:
    try:
        return HeroAITeamViewerMemory().GetTemplateForEmail(email)
    except Exception:
        return None
