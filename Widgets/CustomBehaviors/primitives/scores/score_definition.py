from abc import ABC, abstractmethod
from typing import Callable, Generic, TypeVar, override

class ScoreDefinition(ABC):
    
    @abstractmethod
    def score_definition_debug_ui(self) -> str:
        pass