class BottingTreeBlackboardMixin:
    _LOG_LAST_MESSAGE_KEY = 'last_log_message'
    _LOG_LAST_MESSAGE_DATA_KEY = 'last_log_message_data'
    _LOG_HISTORY_KEY = 'blackboard_log_history'

    @property
    def blackboard(self) -> dict:
        return self.tree.blackboard

    def GetBlackboardValue(self, key: str, default=None):
        return self.blackboard.get(key, default)

    def SetBlackboardValue(self, key: str, value) -> None:
        self.blackboard[key] = value

    def ClearBlackboardValue(self, key: str) -> None:
        self.blackboard.pop(key, None)

    def HasBlackboardValue(self, key: str) -> bool:
        return key in self.blackboard

    def GetLastBlackboardLogMessage(self) -> str:
        value = self.blackboard.get(self._LOG_LAST_MESSAGE_KEY, '')
        return value if isinstance(value, str) else ''

    def GetLastBlackboardLogData(self) -> dict:
        value = self.blackboard.get(self._LOG_LAST_MESSAGE_DATA_KEY, {})
        return value if isinstance(value, dict) else {}

    def GetBlackboardLogHistory(self) -> list[str]:
        value = self.blackboard.get(self._LOG_HISTORY_KEY, [])
        if not isinstance(value, list):
            return []
        return [entry for entry in value if isinstance(entry, str)]

    def ClearBlackboardLog(self) -> None:
        self.blackboard.pop(self._LOG_LAST_MESSAGE_KEY, None)
        self.blackboard.pop(self._LOG_LAST_MESSAGE_DATA_KEY, None)

    def ClearBlackboardLogHistory(self) -> None:
        self.blackboard.pop(self._LOG_HISTORY_KEY, None)
