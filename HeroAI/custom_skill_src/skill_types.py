from Py4GWCoreLib import Range

from ..types import SkillNature
from ..types import Skilltarget
from ..types import SkillType

class CastConditions:
    def __init__(self):
        # Conditions
        self.IsAlive = True
        self.HasCondition = False
        self.HasBleeding = False
        self.HasBlindness = False
        self.HasBurning = False
        self.HasCrackedArmor = False
        self.HasCrippled = False
        self.HasDazed = False
        self.HasDeepWound = False
        self.HasDisease = False
        self.HasPoison = False
        self.HasWeakness = False

        # Special Conditions
        self.HasWeaponSpell = False
        self.WeaponSpellList = []
        self.HasEnchantment = False
        self.EnchantmentList = []
        self.HasDervishEnchantment = False
        self.HasHex = False
        self.HexList = []
        self.HasChant = False
        self.ChantList = []
        self.IsCasting = False
        self.CastingSkillList = []
        self.IsKnockedDown = False
        self.IsMoving = False
        self.IsAttacking = False
        self.IsHoldingItem = False
        self.RequiresSpiritInEarshot = False
        self.SharedEffects = []

        # Targeting Rules
        self.TargetingStrict = True
        self.SelfFirst = False

        # Resource and Health Constraints
        self.LessLife = 0.0
        self.MoreLife = 0.0
        self.LessEnergy = 0.0
        self.Overcast = 0.0
        self.Overcast = 0.0
        self.SacrificeHealth = 0.0

        # Usage Flags
        self.IsPartyWide = False
        self.PartyWideArea = 0
        self.UniqueProperty = False
        self.IsOutOfCombat = False

        # combat field checks
        self.EnemiesInRange = 0
        self.EnemiesInRangeArea = Range.Area.value

        self.AlliesInRange = 0
        self.AlliesInRangeArea = Range.Area.value

        self.SpiritsInRange = 0
        self.SpiritsInRangeArea = Range.Area.value

        self.MinionsInRange = 0
        self.MinionsInRangeArea = Range.Area.value
            
class CustomSkill:
    def __init__(self):
        self.SkillID = 0
        self.SkillType = SkillType.Skill.value
        self.TargetAllegiance = Skilltarget.Enemy.value
        self.Nature = SkillNature.Offensive.value
        self.Conditions = CastConditions()