from ctypes import Array, Structure, addressof, c_int, c_uint, c_float, c_bool, c_wchar, memmove, c_uint64, sizeof

from .AttributesStruct import AttributesStruct
from .BuffStruct import BuffStruct
from .SkillbarStruct import SkillbarStruct
from .MapStruct import MapStruct
from .EnergyStruct import EnergyStruct
from .HealthStruct import HealthStruct
from ...native_src.internals.types import Vec2f, Vec3f
from .Globals import (
    SHMEM_MAX_CHAR_LEN,
)

class AgentDataStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("Map", MapStruct),
        ("Skillbar", SkillbarStruct),
        ("Attributes", AttributesStruct),
        ("Buffs", BuffStruct),
        
        ("CharacterName", c_wchar*SHMEM_MAX_CHAR_LEN),
        ("AgentID", c_uint),
        ("OwnerAgentID", c_uint),
        ("HeroID", c_uint),
        ("Health", HealthStruct),
        
        
        ("Level", c_uint),
        ("Profession", c_uint * 2),  # Primary and Secondary Profession
        ("Morale", c_uint),
        
        
        ("UUID", c_uint * 4),  # 128-bit UUID
        
        
        ("TargetID", c_uint),
        ("ObservingID", c_uint),
        ("PlayerNumber", c_uint),
        
        
        ("Energy", c_float),
        ("MaxEnergy", c_float),
        ("EnergyPips", c_int),

        ("LoginNumber", c_uint),
        ("DaggerStatus", c_uint),
        ("WeaponType", c_uint),
        ("WeaponItemType", c_uint),
        ("OffhandItemType", c_uint),
        ("Overcast", c_float),
        ("WeaponAttackSpeed", c_float),
        ("AttackSpeedModifier", c_float),
        ("EffectsMask", c_uint),  #mask of active effects
        ("VisualEffectsMask", c_uint),  #mask of active visual effects
        ("TypeMap", c_uint),  #mask of type and subtype flags
        ("ModelState", c_uint),
        ("AnimationSpeed", c_float),
        ("AnimationCode", c_uint),
        ("AnimationID", c_uint),
        ("XYZ", c_float * 3),
        ("ZPlane", c_int),
        ("RotationAngle", c_float),
        ("VelocityVector", c_float * 2),  
        ("Velocity", Vec2f),
        
    ]
    
    # Type hints for IntelliSense
    Map: MapStruct
    Skillbar: SkillbarStruct
    Attributes: AttributesStruct
    Buffs: BuffStruct
    
    
    CharacterName: str
    AgentID: int
    OwnerAgentID: int
    HeroID: int
    Health: HealthStruct
    Level: int
    Profession: tuple[int, int]
    Morale: int
    
    
    UUID: list[int]
    
    TargetID: int
    ObservingID: int
    PlayerNumber: int
    
    
    Energy: float
    MaxEnergy: float
    EnergyPips: int

    LoginNumber: int
    DaggerStatus: int
    WeaponType: int
    WeaponItemType: int
    OffhandItemType: int
    Overcast: float
    WeaponAttackSpeed: float
    AttackSpeedModifier: float
    EffectsMask: int
    VisualEffectsMask: int
    TypeMap: int
    ModelState: int
    AnimationSpeed: float
    AnimationCode: int
    AnimationID: int
    XYZ: list[float]
    ZPlane: int
    RotationAngle: float
    VelocityVector: list[float]
    Velocity: Vec2f

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
        self.Profession = (0, 0)
        self.Morale = 0
        
        
        for i in range(4):
            self.UUID[i] = 0


        self.TargetID = 0
        self.ObservingID = 0
        self.PlayerNumber = 0
        
        
        self.Level = 0
        self.Energy = 0.0
        self.MaxEnergy = 0.0
        self.EnergyPips = 0
        
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
        for i in range(3):
            self.XYZ[i] = 0.0
        self.ZPlane = 0
        self.RotationAngle = 0.0
        for i in range(2):
            self.VelocityVector[i] = 0.0  
        self.Velocity = Vec2f(0.0, 0.0)