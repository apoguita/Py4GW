import PyImGui


class BottingTreeDebuggingMixin:
    def GetDebugConsoleLastMessage(self) -> str:
        return self.GetLastBlackboardLogMessage()

    def GetDebugConsoleLastMessageData(self) -> dict:
        return self.GetLastBlackboardLogData()

    def GetDebugConsoleHistory(self) -> list[str]:
        return self.GetBlackboardLogHistory()

    def ClearDebugConsole(self) -> None:
        self.ClearBlackboardLog()
        self.ClearBlackboardLogHistory()

    def CopyDebugConsoleToClipboard(self) -> None:
        PyImGui.set_clipboard_text('\n'.join(self.GetDebugConsoleHistory()))

    def DrawDebugConsole(
        self,
        child_id: str | None = None,
        height: float = 200.0,
        reverse_order: bool = True,
        show_controls: bool = True,
    ) -> None:
        if show_controls:
            if PyImGui.button('Clear UI Log'):
                self.ClearDebugConsole()
            PyImGui.same_line(0, -1)
            if PyImGui.button('Copy UI Log'):
                self.CopyDebugConsoleToClipboard()

        log_history = self.GetDebugConsoleHistory()
        child_name = child_id or f'BottingTreeDebugConsole##{id(self)}'
        if PyImGui.begin_child(child_name, (0, height), True, PyImGui.WindowFlags.HorizontalScrollbar):
            entries = log_history[::-1] if reverse_order else log_history
            for entry in entries:
                PyImGui.text_wrapped(entry)
        PyImGui.end_child()
