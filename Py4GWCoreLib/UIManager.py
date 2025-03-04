import ctypes
import PyUIManager

CALLBACK_FUNC_TYPE = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)


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
    def GetFrameArray():
        """
        Get the frame array.

        :return: list: The frame array.
        """
        return PyUIManager.UIManager.get_frame_array()
    
    @staticmethod
    def ButtonClick(frame_id):
        """
        Click a button on the UI.

        :param frame_id: The ID of the button.
        """
        PyUIManager.UIManager.button_click(frame_id)
    
    @staticmethod
    def GetRootFrameID():
        """
        Get the root frame ID.

        :return: int: The root frame ID.
        """
        return PyUIManager.UIManager.get_root_frame_id()
    
    @staticmethod
    def IsWorldMapShowing():
        """
        Check if the world map is showing.

        :return: bool: True if the world map is showing, False otherwise.
        """
        return PyUIManager.UIManager.is_world_map_showing()
    
    @staticmethod
    def SetPreference(preference, value):
        """
        Set a preference value.

        :param preference: The preference to set.
        :param value: The value to set.
        """
        PyUIManager.UIManager.set_preference(preference, value)
        
    @staticmethod
    def GetFPSLimit():
        """
        Get the frame limit.

        :return: int: The frame limit.
        """
        return PyUIManager.UIManager.get_frame_limit()
    
    @staticmethod
    def SetFPSLimit(limit):
        """
        Set the frame limit.

        :param limit: The frame limit.
        """
        PyUIManager.UIManager.set_frame_limit(limit)
        
    @staticmethod
    def ExecuteCallback(callback: PyUIManager.UIInteractionCallback, message_id: int, wParam=None, lParam=None):
        """
        Execute a UI interaction callback function.

        :param callback: The callback object.
        :param message_id: The UIMessage ID to send.
        :param wParam: Optional parameter, defaults to None.
        :param lParam: Optional parameter, defaults to None.
        """
        if not callback:
            raise ValueError("Callback is None")

        address = callback.get_address()
        if not address:
            raise ValueError(f"Invalid callback function pointer: {hex(address)}")

        func = CALLBACK_FUNC_TYPE(address)

        func(
            ctypes.c_uint32(message_id),  # Convert int to uint32 when calling
            ctypes.c_void_p(wParam) if wParam is not None else None,
            ctypes.c_void_p(lParam) if lParam is not None else None
        )
    