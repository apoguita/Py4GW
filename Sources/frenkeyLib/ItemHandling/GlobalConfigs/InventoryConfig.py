from typing import ClassVar, Self, cast, Self

from Sources.frenkeyLib.ItemHandling.GlobalConfigs.RuleConfig import RuleConfig

class InventoryConfig(RuleConfig):    
    _initialized: bool = False    
    _instances: ClassVar[dict[type[Self], Self]] = {}

    def __new__(cls: type[Self]) -> Self:
        instance = cast(Self | None, cls._instances.get(cls))
        if instance is None:
            instance = cast(Self, super().__new__(cls))
            instance._initialized = False
            cls._instances[cls] = instance
        return instance
    
    def __init__(self: Self) -> None:
        if self._initialized:
            return
        
        self._initialized = True
        super().__init__()
