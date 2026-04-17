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
        self.ModelIDFilter: int = 0  # for AllyNPCByModel: model ID to scan for

        # Resource and Health Constraints
        self.LessLife = 0.0
        self.MoreLife = 0.0
        self.LessEnergy = 0.0
        # Hard cap on caster's own energy. 0.0 disables. When > 0, the skill is only
        # eligible while Agent.GetEnergy(player) (a 0.0-1.0 fraction of max) is at or
        # below this value. Use for energy-return interrupts like Power Drain so the
        # cast is skipped when the caster is already near full.
        self.LessSelfEnergyPercentage = 0.0
        self.Overcast = 0.0
        self.Overcast = 0.0
        self.SacrificeHealth = 0.0
        # Fraction of the caster's max HP that this skill sacrifices on cast (e.g. 0.33 for BiP).
        # Used by the post-sacrifice safety floors below to compute hp_after_sacrifice.
        self.SacrificePercent = 0.0
        # Opt-in post-sacrifice safety floors. Both default to 0 (disabled). When set, the caster
        # must remain strictly above BOTH the percent-of-max floor AND the absolute-HP floor after
        # paying the skill's sacrifice, or the cast is refused.
        self.MinHealthAfterSacrificePercent = 0.0
        self.MinHealthAfterSacrificeAbsolute = 0

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