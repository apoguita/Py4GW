from enum import Enum, IntEnum

class ValueArg(IntEnum):
    None_ = -1
    Arg1 = 0
    Arg2 = 1
    Fixed = 2

class ModFact:
    def __init__(self, description : str, identifier : int, modifier_value_arg: ValueArg, arg1: tuple[int, ...] = (), arg2: tuple[int, ...] = ()):
        '''
        :param description: The description of the mod fact. This can contain placeholders for formatting.
        :param identifier: The identifier of the mod fact.
        :param modifier_value_arg: The argument type that determines which arg is changing
        :param arg1: The first set of arguments of the fact.
        :param arg2: The second set of arguments of the fact.
        '''
        self.description = description
        self.identifier = identifier
        self.modifier_value_arg = modifier_value_arg
        self.arg1 = arg1
        self.arg2 = arg2

    def get_presentation(self) -> str:
        match self.modifier_value_arg:
            case ValueArg.None_ | ValueArg.Fixed:
                return self.description
            
            case ValueArg.Arg1:
                return self.description.format(*self.arg1)
            
            case ValueArg.Arg2:
                return self.description.format(*self.arg2)
        

class ModFacts(Enum):
    DamagePlusPercent = ModFact("Damage +{0}%", 8760, ValueArg.Arg2, arg2=(10, 15))
    DamageVersusPercent = ModFact("Damage +{0}%", 41544, ValueArg.Arg1, arg1=(10, 20))
    EnergyMinus = ModFact("Energy -{0}", 8376, ValueArg.Fixed, arg2=(5,))
    EnemyType = ModFact("vs. {0}", 32896, ValueArg.Arg1, arg1=(5,))
    
    
    Unknown9522 = ModFact("", 9522, ValueArg.None_)

    
class WeaponMod():
    def __init__(self, name: str, mod_facts: tuple[ModFacts, ...]):
        '''
        :param name: The english name of the weapon mod.
        :param mod_facts: The mod facts associated with this weapon mod. These have to be present in the items modifiers in this exact order.
        '''
        self.name = name
        self.mod_facts = mod_facts
    
    @property
    def description(self) -> str:
        descriptions = [fact.value.get_presentation() for fact in self.mod_facts if fact.value.get_presentation()]
        return "\n".join(descriptions)
        
    
class WeaponMods(Enum):
    Brawn_over_Brains = WeaponMod(
        "\"Brawn over Brains\"",
        (
            ModFacts.DamagePlusPercent,
            ModFacts.Unknown9522,
            ModFacts.EnergyMinus,
        )
    )