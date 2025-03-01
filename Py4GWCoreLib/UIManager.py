import PyUIManager

class UIManager:
    @staticmethod
    def GetFrameIDByLabel(label):
        """
        Get the frame ID by its label.

        :param label: The label of the frame.
        :return: int: The frame ID, or -1 if not found.
        """
        return PyUIManager.UIManager.get_frame_id_by_label(label)
    
    @staticmethod
    def GetFrameIDByHash(hash):
        """
        Get the frame ID by its hash value.

        :param hash: The hash value of the frame.
        :return: int: The frame ID, or -1 if not found.
        """
        return PyUIManager.UIManager.get_frame_id_by_hash(hash)
    
    @staticmethod
    def GetHashByLabel(label):
        """
        Get the hash value of a frame by its label.

        :param label: The label of the frame.
        :return: int: The hash value of the frame, or -1 if not found.
        """
        return PyUIManager.UIManager.get_hash_by_label(label)
    
    @staticmethod
    def GetFrameHierarchy():
        """
        Get the frame hierarchy as a dictionary.

        :return: dict: The frame hierarchy.
        """
        return PyUIManager.UIManager.get_frame_hierarchy()
    
    @staticmethod
    def GetFrameCoordsByHash(hash):
        """
        Get the coordinates of a frame by its hash value.

        :param hash: The hash value of the frame.
        :return: tuple: The (x, y),(x1,y1) coordinates of the frame, or None if not found.
        """
        return PyUIManager.UIManager.get_frame_coords_by_hash(hash)
    
    @staticmethod
    def GetFrame(frame_id):
        """
        Get the frame by its ID.

        :param frame_id: The ID of the frame.
        :return: UIFrame: The frame object, or None if not found.
        """
        return PyUIManager.UIManager().get_frame(frame_id)
    
    