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
    @staticmethod
    def GetGameContextPtr() -> int:
        """
        Returns uintptr_t pointer to GameContext.
        """
        ...
    @staticmethod
    def GetPreGameContextPtr() -> int:
        """
        Returns uintptr_t pointer to PreGameContext.
        """
        ...
    @staticmethod
    def GetWorldContextPtr() -> int:
        """
        Returns uintptr_t pointer to WorldContext.
        """
        ...
    @staticmethod
    def GetCharContextPtr() -> int:
        """
        Returns uintptr_t pointer to CharContext.
        """
        ...
    @staticmethod
    def GetAgentContextPtr() -> int:
        """
        Returns uintptr_t pointer to AgentContext.
        """
        ...
    @staticmethod
    def GetCinematicPtr() -> int:
        """
        Returns uintptr_t pointer to Cinematic.
        """
        ...
    @staticmethod
    def GetGuildContextPtr() -> int:
        """
        Returns uintptr_t pointer to GuildContext.
        """
        ...