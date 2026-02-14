from ctypes import Structure, c_uint
#region Factions 
class FactionUnitStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Current", c_uint),
        ("TotalEarned", c_uint),
        ("Max", c_uint),
    ]

    # Inline annotations for IntelliSense
    Current: int
    TotalEarned: int
    Max: int

    def reset(self) -> None:
        """Reset all fields to zero."""
        self.Current = 0
        self.TotalEarned = 0
        self.Max = 0
    
class FactionStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Kurzick", FactionUnitStruct),
        ("Luxon", FactionUnitStruct),
        ("Imperial", FactionUnitStruct),
        ("Balthazar", FactionUnitStruct),
    ]

    # Inline annotations for IntelliSense
    Kurzick: FactionUnitStruct
    Luxon: FactionUnitStruct
    Imperial: FactionUnitStruct
    Balthazar: FactionUnitStruct

    def reset(self) -> None:
        """Reset all fields to zero."""
        self.Kurzick.reset()
        self.Luxon.reset()
        self.Imperial.reset()
        self.Balthazar.reset()
        
    def from_context (self):
        from ...Player import Player
        kurzick_data = Player.GetKurzickData()
        self.Kurzick.Current = kurzick_data[0]
        self.Kurzick.TotalEarned = kurzick_data[1]
        self.Kurzick.Max = kurzick_data[2]
        
        luxon_data = Player.GetLuxonData()
        self.Luxon.Current = luxon_data[0]
        self.Luxon.TotalEarned = luxon_data[1]
        self.Luxon.Max = luxon_data[2]
        
        imperial_data = Player.GetImperialData()
        self.Imperial.Current = imperial_data[0]
        self.Imperial.TotalEarned = imperial_data[1]
        self.Imperial.Max = imperial_data[2]
        
        balthazar_data = Player.GetBalthazarData()
        self.Balthazar.Current = balthazar_data[0]
        self.Balthazar.TotalEarned = balthazar_data[1]
        self.Balthazar.Max = balthazar_data[2]