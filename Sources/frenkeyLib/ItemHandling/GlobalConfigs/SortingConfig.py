from typing import ClassVar, Self, cast

from Py4GWCoreLib.Item import Bag


class BagSorting:
    def __init__(self, bag_id: Bag):
        self.bag_id = bag_id
    
class SortingConfig():
    _initialized: bool = False    
    _instance : ClassVar[Self | None] = None

    def __new__(cls: type[Self]) -> Self:
        instance = cast(Self | None, cls._instance)
        if instance is None:
            instance = cast(Self, super().__new__(cls))
            instance._initialized = False
            cls._instance = instance
        return instance
            
    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        
        self.BagSortings : list[BagSorting] = []