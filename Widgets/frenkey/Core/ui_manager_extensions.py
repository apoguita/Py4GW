
class UIManagerExtensions:
    @staticmethod
    def IsElementVisible(frame_id: int) -> bool:
        """
        Check if a specific frame is open in the UI.

        Args:
            frame_id (int): The ID of the frame to check.

        Returns:
            bool: True if the frame is open, False otherwise.
        """
        return isinstance(frame_id, int) and frame_id > 0
