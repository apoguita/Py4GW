#region KeyHandler
import PyKeystroke
class Keystroke:
    @staticmethod
    def keystroke_instance():
        """
        Purpose: Get the PyScanCodeKeystroke instance for sending keystrokes.
        Returns: PyScanCodeKeystroke
        """
        return PyKeystroke.PyScanCodeKeystroke()


    @staticmethod
    def Press(key):
        """
        Purpose: Simulate a key press event using scan codes.
        Args:
            key (Key): The key to press.
        Returns: None
        """
        Keystroke.keystroke_instance().PressKey(key)

    @staticmethod
    def Release(key):
        """
        Purpose: Simulate a key release event using scan codes.
        Args:
            key (Key): The key to release.
        Returns: None
        """
        Keystroke.keystroke_instance().ReleaseKey(key)

    @staticmethod
    def PressAndRelease(key):
        """
        Purpose: Simulate a key press and release event using scan codes.
        Args:
            key (Key): The key to press and release.
        Returns: None
        """
        Keystroke.keystroke_instance().PushKey(key)

    @staticmethod
    def PressCombo(modifiers: list[int]):
        """
        Purpose: Simulate a key press event for multiple keys using scan codes.
        Args:
            modifiers (list of Key): The list of keys to press.
        Returns: None
        """
        Keystroke.keystroke_instance().PressKeyCombo(modifiers)

    @staticmethod
    def ReleaseCombo(modifiers: list[int]):
        """
        Purpose: Simulate a key release event for multiple keys using scan codes.
        Args:
            modifiers (list of Key): The list of keys to release.
        Returns: None
        """
        Keystroke.keystroke_instance().ReleaseKeyCombo(modifiers)

    @staticmethod
    def PressAndReleaseCombo(modifiers: list[int]):
        """
        Purpose: Simulate a key press and release event for multiple keys using scan codes.
        Args:
            modifiers (list of Key): The list of keys to press and release.
        Returns: None
        """
        Keystroke.keystroke_instance().PushKeyCombo(modifiers)

#endregion
