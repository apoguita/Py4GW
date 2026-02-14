from ctypes import Array, Structure, addressof, c_int, c_uint, c_float, c_bool, c_wchar, memmove, c_uint64, sizeof

class EnergyStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Current", c_float),
        ("MaxEnergy", c_int),
        ("EnergyRegen", c_float),
        ("EnergyPips", c_int),
        
    ]

    # Inline annotations for IntelliSense
    Current: float
    MaxEnergy: int
    EnergyRegen: float
    EnergyPips: int

    def reset(self) -> None:
        """Reset all fields to zero."""
        self.Current = 0.0
        self.MaxEnergy = 0
        self.EnergyPips = 0
        
    def from_context(self,agent_id: int) -> None: 
        from ...Agent import Agent
        from ...py4gwcorelib_src.Utils import Utils
        
        energy = Agent.GetEnergy(agent_id)
        self.Current = energy if energy > 0 else 1.0
        max_energy = Agent.GetMaxEnergy(agent_id)
        self.MaxEnergy = max_energy if max_energy > 0 else 10
        self.EnergyRegen = Agent.GetEnergyRegen(agent_id)
        self.EnergyPips = Utils.calculate_energy_pips(max_energy, self.EnergyRegen)

