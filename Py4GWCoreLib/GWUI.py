import PyUIManager


class GWUI:
    @staticmethod
    def CreateWindow(
        x: float,
        y: float,
        width: float,
        height: float,
        title: str = "",
    ) -> int:
        """Create a standalone native window from top-left content bounds in pixel space."""
        return int(
            PyUIManager.UIManager.CreateNativeWindow(
                float(x),
                float(y),
                float(width),
                float(height),
                str(title),
            )
            or 0
        )
