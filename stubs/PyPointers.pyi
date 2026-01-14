# PyPointers.pyi

class PyPointers:
    """
    Static accessors for internal Guild Wars context pointers.
    All methods return uintptr_t values as Python ints.
    """

    @staticmethod
    def GetMissionMapContextPtr() -> int:
        """
        Returns uintptr_t pointer to MissionMapContext.
        """
        ...

    @staticmethod
    def GetWorldMapContextPtr() -> int:
        """
        Returns uintptr_t pointer to WorldMapContext.
        """
        ...

    @staticmethod
    def GetGameplayContextPtr() -> int:
        """
        Returns uintptr_t pointer to GameplayContext.
        """
        ...

    @staticmethod
    def GetMapContextPtr() -> int:
        """
        Returns uintptr_t pointer to MapContext.
        """
        ...
    @staticmethod
    def GetAreaInfoPtr() -> int:
        """
        Returns uintptr_t pointer to AreaInfo.
        """
        ...