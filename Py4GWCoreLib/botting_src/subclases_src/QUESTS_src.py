# botting_src/subclases_src/QUESTS_src.py
#region STATES
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass  # only for typing

from Py4GWCoreLib import ActionQueueManager, ConsoleLog, Py4GW, PyQuest
#endregion

#region QUESTS
class _QUESTS:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers

        # keep one instance (not per call)
        _q = PyQuest.PyQuest()
        _aqm = ActionQueueManager()

        # expose grouped subfeatures like MERCHANTS.Restock
        self.Get = _QUESTS._GET(parent, _q)
        self.Action = _QUESTS._ACTIONS(parent, _q, _aqm)
        self.Wait = _QUESTS._WAIT(parent, _q)

    def GetActive(self) -> int:
        return self.Get.Active()

    def InLog(self, quest_id: int) -> bool:
        return self.Get.InLog(quest_id)

    def RequestInfo(self, quest_id: int, update_markers: bool = False) -> None:
        self.Action.RequestInfo(quest_id, update_markers)

    def SetActive(self, quest_id: int) -> None:
        self.Action.SetActive(quest_id)

    def Abandon(self, quest_id: int) -> None:
        self.Action.Abandon(quest_id)

    def WaitActive(self, quest_id: int, timeout_ms: int = 1500, step_ms: int = 100) -> bool:
        return self.Wait.Active(quest_id, timeout_ms, step_ms)

    def WaitNotActive(self, quest_id: int, timeout_ms: int = 1500, step_ms: int = 100) -> bool:
        return self.Wait.NotActive(quest_id, timeout_ms, step_ms)

    class _GET:
        def __init__(self, parent: "BottingClass", q: PyQuest.PyQuest):
            self.parent = parent
            self._q = q

        def Active(self) -> int:
            try:
                return self._q.get_active_quest_id()
            except Exception:
                return -1

        def InLog(self, quest_id: int) -> bool:
            try:
                return any(q.quest_id == quest_id for q in self._q.get_quest_log())
            except Exception:
                return False

    class _ACTIONS:
        def __init__(self, parent: "BottingClass", q: PyQuest.PyQuest, aqm: ActionQueueManager):
            self.parent = parent
            self._q = q
            self._aqm = aqm

        def RequestInfo(self, quest_id: int, update_markers: bool = False) -> None:
            # PyQuest expects update_markers (plural)
            self._aqm.AddAction("ACTION", self._q.request_quest_info, quest_id, update_markers)

        def SetActive(self, quest_id: int) -> None:
            self._aqm.AddAction("ACTION", self._q.set_active_quest_id, quest_id)

        def Abandon(self, quest_id: int) -> None:
            self._aqm.AddAction("ACTION", self._q.abandon_quest_id, quest_id)

    class _WAIT:
        def __init__(self, parent: "BottingClass", q: PyQuest.PyQuest):
            self.parent = parent
            self._q = q

        def _get_active(self) -> int:
            try:
                return self._q.get_active_quest_id()
            except Exception:
                return -1

        def Active(self, quest_id: int, timeout_ms: int = 1500, step_ms: int = 100) -> bool:
            waited = 0
            while waited < timeout_ms:
                if self._get_active() == quest_id:
                    return True
                self.parent.Wait.ForTime(step_ms)
                waited += step_ms
            ConsoleLog(
                "Quests",
                f"WaitActive timeout (wanted {quest_id}, active {self._get_active()})",
                Py4GW.Console.MessageType.Warning,
            )
            return False

        def NotActive(self, quest_id: int, timeout_ms: int = 1500, step_ms: int = 100) -> bool:
            waited = 0
            while waited < timeout_ms:
                if self._get_active() != quest_id:
                    return True
                self.parent.Wait.ForTime(step_ms)
                waited += step_ms
            ConsoleLog(
                "Quests",
                f"WaitNotActive timeout (still active {self._get_active()})",
                Py4GW.Console.MessageType.Warning,
            )
            return False
#endregion
