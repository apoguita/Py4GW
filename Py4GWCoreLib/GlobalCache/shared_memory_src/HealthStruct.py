from ctypes import Array, Structure, addressof, c_int, c_uint, c_float, c_bool, c_wchar, memmove, c_uint64, sizeof


class HealthStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Current", c_float),
        ("MaxHealth", c_float),
        ("HealthRegen", c_float),
        ("HealthPips", c_int),
    ]

    # Inline annotations for IntelliSense
    Current: float
    MaxHealth: float
    HealthRegen: float
    HealthPips: int

    def reset(self) -> None:
        """Reset all fields to zero."""
        self.Current = 0.0
        self.MaxHealth = 0.0
        self.HealthRegen = 0.0
        self.HealthPips = 0
        
    def from_context(self, agent_id: int) -> None:
        from ...Agent import Agent
        from ...py4gwcorelib_src.Utils import Utils
        
        self.Current = Agent.GetHealth(agent_id)
        self.MaxHealth = Agent.GetMaxHealth(agent_id)
        self.HealthRegen = Agent.GetHealthRegen(agent_id)
        self.HealthPips = Utils.calculate_health_pips(self.MaxHealth, self.HealthRegen)

    