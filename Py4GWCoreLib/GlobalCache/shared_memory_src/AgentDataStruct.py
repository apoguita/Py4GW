from ctypes import Structure, c_int, c_uint, c_float, c_wchar
from Py4GWCoreLib import ThrottledTimer

from .AttributesStruct import AttributesStruct
from .BuffStruct import BuffStruct
from .SkillbarStruct import SkillbarStruct
from .MapStruct import MapStruct
from .EnergyStruct import EnergyStruct
from .HealthStruct import HealthStruct
from ...native_src.internals.types import Vec2f, Vec3f
from .Globals import (
    SHMEM_MAX_CHAR_LEN,
    SHMEM_AGENT_FAST_UPDATE_THROTTLE_MS,
    SHMEM_AGENT_MEDIUM_UPDATE_THROTTLE_MS,
    SHMEM_AGENT_SLOW_UPDATE_THROTTLE_MS,
)


_agent_medium_timers: dict[int, ThrottledTimer] = {}
_agent_slow_timers: dict[int, ThrottledTimer] = {}


def _get_agent_timer(timer_map: dict[int, ThrottledTimer], key: int, throttle_ms: int) -> ThrottledTimer:
    timer = timer_map.get(key)
    if timer is None:
        timer = ThrottledTimer(throttle_ms)
        timer_map[key] = timer
    elif timer.throttle_time != throttle_ms:
        timer.SetThrottleTime(throttle_ms)
    return timer

class AgentDataStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("CharacterName", c_wchar*SHMEM_MAX_CHAR_LEN),
        
        ("AgentID", c_uint),
        ("UUID", c_uint * 4),  # 128-bit UUID
        ("OwnerAgentID", c_uint),
        ("HeroID", c_uint),
        ("TargetID", c_uint),
        ("ObservingID", c_uint),
        ("PlayerNumber", c_uint),
        ("LoginNumber", c_uint),
        
        ("Map", MapStruct),
        ("Skillbar", SkillbarStruct),
        ("Attributes", AttributesStruct),
        ("Buffs", BuffStruct),
        
        ("Health", HealthStruct),
        ("Energy", EnergyStruct),
        ("Overcast", c_float),
        ("Level", c_uint),
        ("Profession", c_uint * 2),  # Primary and Secondary Profession
        ("Morale", c_uint),
        ("Pos", Vec3f),
        ("ZPlane", c_int),
        ("RotationAngle", c_float),
        ("Velocity", Vec2f),
        
        ("DaggerStatus", c_uint),
        ("WeaponType", c_uint),
        ("WeaponItemType", c_uint),
        ("OffhandItemType", c_uint),
        ("WeaponAttackSpeed", c_float),
        ("AttackSpeedModifier", c_float),
        ("EffectsMask", c_uint),  #mask of active effects
        ("VisualEffectsMask", c_uint),  #mask of active visual effects
        ("TypeMap", c_uint),  #mask of type and subtype flags
        ("ModelState", c_uint),
        ("AnimationSpeed", c_float),
        ("AnimationCode", c_uint),
        ("AnimationID", c_uint),    
    ]
    
    # Type hints for IntelliSense
    CharacterName: str
    
    AgentID: int
    UUID: tuple[int, int, int, int]  # 128-bit UUID as a tuple of four 32-bit integers
    OwnerAgentID: int
    HeroID: int
    TargetID: int
    ObservingID: int
    PlayerNumber: int
    LoginNumber: int
    
    Map: MapStruct
    Skillbar: SkillbarStruct
    Attributes: AttributesStruct
    Buffs: BuffStruct
    
    Health: HealthStruct
    Energy: EnergyStruct
    Overcast: float
    Level: int
    Profession: tuple[int, int]
    Morale: int
    Pos: Vec3f
    ZPlane: int
    RotationAngle: float
    Velocity: Vec2f

    DaggerStatus: int
    WeaponType: int
    WeaponItemType: int
    OffhandItemType: int
    WeaponAttackSpeed: float
    AttackSpeedModifier: float
    EffectsMask: int
    VisualEffectsMask: int
    TypeMap: int
    ModelState: int
    AnimationSpeed: float
    AnimationCode: int
    AnimationID: int
    
    @property
    def Is_Bleeding(self) -> bool:
        return (self.EffectsMask & 0x0001) != 0
    @property
    def Is_Conditioned(self) -> bool:
        return (self.EffectsMask & 0x0002) != 0
    @property
    def Is_Crippled(self) -> bool:
        return (self.EffectsMask & 0x000A) == 0xA
    @property
    def Is_Dead(self) -> bool:
        return (self.EffectsMask & 0x0010) != 0
    @property
    def Is_DeepWounded(self) -> bool:
        return (self.EffectsMask & 0x0020) != 0
    @property
    def Is_Poisoned(self) -> bool:
        return (self.EffectsMask & 0x0040) != 0
    @property
    def Is_Enchanted(self) -> bool:
        return (self.EffectsMask & 0x0080) != 0
    @property
    def Is_DegenHexed(self) -> bool:
        return (self.EffectsMask & 0x0400) != 0
    @property
    def Is_Hexed(self) -> bool:
        return (self.EffectsMask & 0x0800) != 0
    @property
    def Is_WeaponSpelled(self) -> bool:
        return (self.EffectsMask & 0x8000) != 0
    @property
    def Is_InCombatStance(self) -> bool:
        return (self.TypeMap & 0x000001) != 0
    @property
    def Has_Quest(self) -> bool:
        return (self.TypeMap & 0x000002) != 0
    @property
    def Is_DeadByTypeMap(self) -> bool:
        return (self.TypeMap & 0x000008) != 0
    @property
    def Is_Female(self) -> bool:
        return (self.TypeMap & 0x000200) != 0
    @property
    def Has_BossGlow(self) -> bool:
        return (self.TypeMap & 0x000400) != 0
    @property
    def Is_HidingCape(self) -> bool:
        return (self.TypeMap & 0x001000) != 0 
    @property
    def Can_Be_Viewed_In_Party_Window(self) -> bool:
        return (self.TypeMap & 0x20000) != 0
    @property
    def Is_Spawned(self) -> bool:   
        return (self.TypeMap & 0x040000) != 0
    @property
    def Is_Being_Observed(self) -> bool:
        return (self.TypeMap & 0x400000) != 0
    @property
    def Is_Knocked_Down(self) -> bool:
        return (self.ModelState == 1104)
    @property
    def Is_Moving(self) -> bool:
        return (self.ModelState == 12 or self.ModelState == 76 or self.ModelState == 204)
    @property
    def Is_Attacking(self) -> bool:
        return (self.ModelState == 96 or self.ModelState == 1088 or self.ModelState == 1120)
    @property
    def Is_Casting(self) -> bool:
        return (self.ModelState == 65 or self.ModelState == 581)
    @property
    def Is_Idle(self) -> bool:
        return (self.ModelState == 68 or self.ModelState == 64 or self.ModelState == 100)
    @property
    def Is_Alive(self) -> bool:
        return not self.Is_Dead and self.Health.Current > 0.0
    @property 
    def Is_Player(self) -> bool:
        return self.LoginNumber != 0
    @property
    def Is_NPC(self) -> bool:
        return self.LoginNumber == 0  
    
    def reset(self) -> None:
        """Reset all fields to zero or default values."""
        self.Map.reset()
        self.Skillbar.reset()
        self.Attributes.reset()
        self.Buffs.reset()
        
        self.CharacterName = ""
        self.AgentID = 0
        self.OwnerAgentID = 0
        self.HeroID = 0
        self.Health.reset()
        self.Energy.reset()
        self.Profession = (0, 0)
        self.Morale = 0
        
        self.UUID = (0, 0, 0, 0)

        self.TargetID = 0
        self.ObservingID = 0
        self.PlayerNumber = 0

        self.Level = 0

        self.LoginNumber = 0
        self.DaggerStatus = 0
        self.WeaponType = 0
        self.WeaponItemType = 0
        self.OffhandItemType = 0
        self.Overcast = 0.0
        self.WeaponAttackSpeed = 0.0
        self.AttackSpeedModifier = 0.0
        self.EffectsMask = 0
        self.VisualEffectsMask = 0
        self.TypeMap = 0
        self.ModelState = 0
        self.AnimationSpeed = 1.0
        self.AnimationCode = 0
        self.AnimationID = 0
        self.Pos = Vec3f(0.0, 0.0, 0.0)

        self.ZPlane = 0
        self.RotationAngle = 0.0
        self.Velocity = Vec2f(0.0, 0.0)
        
    def from_context(self, agent_id:int, throttle_key: int | None = None):
        from ...Party import Party
        from ...Player import Player
        from ...Agent import Agent
        """Load data from the specified agent ID."""
        if agent_id == 0:
            self.reset()
            return

        timer_key = throttle_key if throttle_key is not None else agent_id
        force_full = (self.AgentID == 0)
        
        
        self.AgentID = Player.GetAgentID() 
        self.OwnerAgentID = 0
        self.HeroID = 0
        self.TargetID = Player.GetTargetID()
        
        self.Health.from_context(agent_id)
        self.Energy.from_context(agent_id)

        self.Pos = Vec3f(*Agent.GetXYZ(agent_id))
        self.ZPlane = Agent.GetZPlane(agent_id)
        self.RotationAngle = Agent.GetRotationAngle(agent_id)
        self.Velocity = Vec2f(*Agent.GetVelocityXY(agent_id))
        
        
        self.EffectsMask = Agent.GetAgentEffects(agent_id)
        
        self.TypeMap = Agent.GetTypeMap(agent_id)
       
        
        fast_timer = _get_agent_timer(_agent_medium_timers, timer_key, SHMEM_AGENT_FAST_UPDATE_THROTTLE_MS)
        if force_full or fast_timer.IsExpired():
            self.Map.from_context()
            self.Skillbar.from_context()
            self.Buffs.from_context(agent_id)
            
            self.Overcast = Agent.GetOvercast(agent_id)
            self.Morale = Player.GetMorale()

            fast_timer.Reset()

        medium_timer = _get_agent_timer(_agent_medium_timers, timer_key, SHMEM_AGENT_MEDIUM_UPDATE_THROTTLE_MS)
        if force_full or medium_timer.IsExpired():
            self.DaggerStatus = Agent.GetDaggerStatus(agent_id)
            self.WeaponAttackSpeed = Agent.GetWeaponAttackSpeed(agent_id)
            self.AttackSpeedModifier = Agent.GetAttackSpeedModifier(agent_id)
            self.VisualEffectsMask = Agent.GetVisualEffects(agent_id)
            self.ModelState = Agent.GetModelState(agent_id)
            self.AnimationSpeed = Agent.GetAnimationSpeed(agent_id)
            self.AnimationCode = Agent.GetAnimationCode(agent_id)
            self.AnimationID = Agent.GetAnimationID(agent_id)
            
            self.ObservingID = Player.GetObservingID()
            
            medium_timer.Reset()

        slow_timer = _get_agent_timer(_agent_slow_timers, timer_key, SHMEM_AGENT_SLOW_UPDATE_THROTTLE_MS)
        if force_full or slow_timer.IsExpired():
            self.CharacterName = Party.Players.GetPlayerNameByLoginNumber(Player.GetLoginNumber())
            self.UUID = Player.GetPlayerUUID()
            self.Attributes.from_context(agent_id)
            self.PlayerNumber = Agent.GetPlayerNumber(agent_id)
            self.LoginNumber = Agent.GetLoginNumber(agent_id)
            
            self.Level = Agent.GetLevel(agent_id)
            self.Profession = Agent.GetProfessionIDs(Player.GetAgentID())
            self.WeaponType = Agent.GetWeaponType(agent_id)[0]
            self.WeaponItemType = Agent.GetWeaponItemType(agent_id)
            self.OffhandItemType = Agent.GetOffhandItemType(agent_id)
            slow_timer.Reset()
