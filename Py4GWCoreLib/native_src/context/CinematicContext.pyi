
class CinematicStruct():
    h0000: int
    h0004: int

#region facade
class Cinematic:
    @staticmethod
    def get_ptr() -> int:...    
    @staticmethod
    def _update_ptr():...
    @staticmethod
    def enable():...
    @staticmethod
    def disable():...
    @staticmethod
    def get_context() -> CinematicStruct | None:...
        
        