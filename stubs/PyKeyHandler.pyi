from typing import List

class KeyHandler:
    def __init__(self) -> None:
        pass
    
    def PressKey(self, virtualKeyCode: int) -> None:
        pass
    
    def ReleaseKey(self, virtualKeyCode: int) -> None:
        pass
    
    def PushKey(self, virtualKeyCode: int) -> None:
        pass
    
    def PressKeyCombo(self, keys: List[int]) -> None:
        pass
    
    def ReleaseKeyCombo(self, keys: List[int]) -> None:
        pass
    
    def PushKeyCombo(self, keys: List[int]) -> None:
        pass
