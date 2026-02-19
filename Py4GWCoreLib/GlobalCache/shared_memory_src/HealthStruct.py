from ctypes import  Structure,  c_int,  c_float

class HealthStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Current", c_float),
        ("Max", c_float),
        ("Regen", c_float),
        ("Pips", c_int),
    ]

    # Inline annotations for IntelliSense
    Current: float
    Max: float
    Regen: float
    Pips: int

    def reset(self) -> None:
        """Reset all fields to zero."""
        self.Current = 0.0
        self.Max = 0.0
        self.Regen = 0.0
        self.Pips = 0
        
    def from_context(self, agent_id: int) -> None:
        from ...Agent import Agent
        from ...py4gwcorelib_src.Utils import Utils
        
        self.Current = Agent.GetHealth(agent_id)
        self.Max = Agent.GetMaxHealth(agent_id)
        self.Regen = Agent.GetHealthRegen(agent_id)
        self.Pips = Utils.calculate_health_pips(self.Max, self.Regen)

    