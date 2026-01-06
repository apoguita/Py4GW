from Py4GWCoreLib import *

from typing import Optional
from enum import IntEnum


module_name = "Mod Handler"
window_module = ImGui.WindowModule("Item Compare", window_name="Item Compare", window_size=(300, 300))

class ModType(IntEnum):
    Inscription = 0
    Metadata = 1
    
class ApplyTarget(IntEnum):
    Weapon = 0
    MartialWeapon = 1
    SpellCastingWeapon = 2
    Offhand = 3
    
class ModifierValue(IntEnum):
    Arg1 = 0
    Arg2 = 1
    Arg = 2
    
      


class ModifierInfo:
    def __init__(self, identifier: int, name: str,
                 arg: type | None = None,
                 arg1: type | None = None,
                 arg2: type | None = None,
                 representation=lambda *a: "",
                 # vital metadata
                 mod_type: ModType = ModType.Inscription,
                 apply_targets: list[ApplyTarget] | None = None,
                 min_value: dict[int, int] | None = None,
                 max_value: dict[int, int] | None = None,
                 modifier_value_arg: Optional[ModifierValue] = None):
        self.identifier = identifier
        self.name = name
        self.arg = arg
        self.arg1 = arg1
        self.arg2 = arg2
        self.representation = representation

        # metadata
        self.mod_type = mod_type
        self.apply_targets: list[ApplyTarget] = apply_targets or []
        self.min_value = min_value or {}
        self.max_value = max_value or {}
        self.modifier_value_arg = modifier_value_arg

    def _resolve(self, kind, value):
        if kind and isinstance(kind, type) and issubclass(kind, IntEnum):
            try:
                return kind(value).name
            except ValueError:
                return str(value)
        return value

    def get_main_value(self, arg, arg1, arg2) -> int | None:
        """Return whichever argument is the 'main source' for progression."""
        if self.modifier_value_arg == ModifierValue.Arg1:
            return arg1
        elif self.modifier_value_arg == ModifierValue.Arg2:
            return arg2
        elif self.modifier_value_arg == ModifierValue.Arg:
            return arg
        return None

    def get_min(self, mod_id: Optional[int] = None) -> int | None:
        """Return min value (per modifier id if provided)."""
        if mod_id is not None:
            return self.min_value.get(mod_id)
        return next(iter(self.min_value.values()), None)

    def get_max(self, mod_id: Optional[int] = None) -> int | None:
        """Return max value (per modifier id if provided)."""
        if mod_id is not None:
            return self.max_value.get(mod_id)
        return next(iter(self.max_value.values()), None)

    def format(self, arg, arg1, arg2) -> str:
        """Format description using resolved arguments."""
        return self.representation(
            self._resolve(self.arg, arg),
            self._resolve(self.arg1, arg1),
            self._resolve(self.arg2, arg2),
        )

_MODIFIER_MAP: dict[int, ModifierInfo] = {}

#region metadata
# 8760: Damage +X%
_MODIFIER_MAP[8760] = ModifierInfo(
    8760,
    name="Damage",
    arg2=int,
    mod_type=ModType.Metadata,
    min_value={8760: 10},
    max_value={8760: 20},
    modifier_value_arg=ModifierValue.Arg2,
    representation=lambda arg, arg1, arg2: f"Damage +{arg2}%"
)

# 9032: Health +X
_MODIFIER_MAP[9032] = ModifierInfo(
    9032,
    name="Health",
    arg1=int,
    mod_type=ModType.Metadata,
    min_value={9032: 15},
    max_value={9032: 50},
    modifier_value_arg=ModifierValue.Arg1,
    representation=lambda arg, arg1, arg2: f"Health +{arg1}"
)

_MODIFIER_MAP[8392] = ModifierInfo(
    8392,
    name="Energy regeneration",
    arg2=int,
    mod_type=ModType.Metadata,
    min_value={8392: 1},
    max_value={8392: 1},
    modifier_value_arg=ModifierValue.Arg2,
    representation=lambda arg, arg1, arg2: f"Energy regeneration -{arg2}"
)

#region combat enhancing
# 8824: Damage +X% (while Health is above Y%)
_MODIFIER_MAP[8216] = ModifierInfo(
    8824,
    name= "\"Strength and Honor\"",
    mod_type=ModType.Inscription,
    apply_targets=[ApplyTarget.Weapon],
    arg1=int,
    arg2=int,
    modifier_value_arg=ModifierValue.Arg2,
    min_value={8824: 10, 9032: 15},  # Damage at 10 minimum
    max_value={8824: 15, 9032: 10},  # Damage capped at 15 maximum
    representation=lambda arg, arg1, arg2: (f"Damage +{arg2}% (while Health is above {arg1}%)")
)

# 8808: Damage +X% (while Enchanted)
_MODIFIER_MAP[8808] = ModifierInfo(
    8808,
    name="\"Guided by Fate\"",
    mod_type=ModType.Inscription,
    apply_targets=[ApplyTarget.Weapon],
    arg2=int,
    modifier_value_arg=ModifierValue.Arg2,
    min_value={8808: 10},
    max_value={8808: 15},
    representation=lambda arg, arg1, arg2: f"Damage +{arg2}% (while Enchanted)"
)

# 8872: Damage +X% (while in a stance)
_MODIFIER_MAP[8872] = ModifierInfo(
    8872,
    name='"Dance With Death"',
    mod_type=ModType.Inscription,
    apply_targets=[ApplyTarget.Weapon],
    arg2=int,
    modifier_value_arg=ModifierValue.Arg2,
    min_value={8872: 10},
    max_value={8872: 15},
    representation=lambda arg, arg1, arg2: f"Damage +{arg2}% (while in a stance)"
)

# 8792: Damage +X% (vs. Hexed foes)
_MODIFIER_MAP[8792] = ModifierInfo(
    8792,
    name= "\"Too Much Information\"",
    mod_type=ModType.Inscription,
    apply_targets=[ApplyTarget.Weapon],
    arg2=int,
    modifier_value_arg=ModifierValue.Arg2,
    min_value={8792: 10},
    max_value={8792: 15},
    representation=lambda arg, arg1, arg2: f"Damage +{arg2}% (vs. Hexed foes)"
)

# 8216: Armor -X (while attacking)
_MODIFIER_MAP[8216] = ModifierInfo(
    8216,
    name="\"To the Pain!\"",
    mod_type=ModType.Inscription,
    apply_targets=[ApplyTarget.Weapon],
    arg2=int,
    min_value={8216: 10, 8760: 14},   # Armor fixed at 10, Damage restricted to 14+
    max_value={8216: 10, 8760: 15},   # Damage restricted to 15
    representation=lambda arg, arg1, arg2: (
        f"{_MODIFIER_MAP[8760].format(None, None, arg2)}\n"
        f"Armor -{arg2} (while attacking)"
    ),
)

_MODIFIER_MAP[8376] = ModifierInfo(
    8376,
    name= "\"Brawn over Brains\"",
    mod_type=ModType.Inscription,
    apply_targets=[ApplyTarget.Weapon],
    arg2=int,
    min_value={8376: 5, 8760: 14},   # Energy fixed at 5, Damage restricted to 14+
    max_value={8376: 5, 8760: 15},   # Damage restricted to 15
    representation=lambda arg, arg1, arg2: (
        f"{_MODIFIER_MAP[8760].format(None, None, arg2)}\n"
        f"Energy -{arg2}"
    ),
)

_MODIFIER_MAP[8840] = ModifierInfo(
    8840,
    name="\"Vengeance is Mine\"",
    mod_type=ModType.Inscription,
    apply_targets=[ApplyTarget.Weapon],
    arg1=int,
    arg2=int,
    modifier_value_arg=ModifierValue.Arg2,
    min_value={8840: 10, 9032: 50},  # Damage at 10 minimum
    max_value={8840: 20, 9032: 50},  # Damage capped at 20 maximum
    representation=lambda arg, arg1, arg2: (
        f"Damage +{arg2}% (while Health is below {arg1}%)"
    )
)

_MODIFIER_MAP[8856] = ModifierInfo(
    8856,
    name="\"Don't Fear the Reaper\"",
    mod_type=ModType.Inscription,
    apply_targets=[ApplyTarget.Weapon],
    arg2=int,
    modifier_value_arg=ModifierValue.Arg2,
    min_value={8856: 10},
    max_value={8856: 20},
    representation=lambda arg, arg1, arg2: f"Damage +{arg2}% (while Hexed)"
)

_MODIFIER_MAP[8920] = ModifierInfo(
    8920,
    name="\"I have the power!\"",
    mod_type=ModType.Inscription,
    apply_targets=[ApplyTarget.MartialWeapon],
    arg2=int,
    modifier_value_arg=ModifierValue.Arg2,
    min_value={8920: 5},
    max_value={8920: 5},
    representation=lambda arg, arg1, arg2: f"Energy +{arg2}"
)

_MODIFIER_MAP[8968] = ModifierInfo(
    8968,
    name="\"Hale and Hearty\"",
    mod_type=ModType.Inscription,
    apply_targets=[ApplyTarget.SpellCastingWeapon],
    arg1=int,
    arg2=int,
    modifier_value_arg=ModifierValue.Arg2,
    min_value={8968: 1, 9032: 50},  # Energy at 1 minimum
    max_value={8968: 5, 9032: 50},  # Energy capped at 5 maximum
    representation=lambda arg, arg1, arg2: (
        f"Energy +{arg2}% (while Health is above {arg1}%)"
    )
)

_MODIFIER_MAP[8952] = ModifierInfo(
    8952,
    name="\"Have faith\"",
    mod_type=ModType.Inscription,
    apply_targets=[ApplyTarget.SpellCastingWeapon],
    arg2=int,
    modifier_value_arg=ModifierValue.Arg2,
    min_value={8952: 1},
    max_value={8952: 5},
    representation=lambda arg, arg1, arg2: f"Energy +{arg2} (while Enchanted)"
)

_MODIFIER_MAP[8984] = ModifierInfo(
    8984,
    name="\"Don't call it a comeback!\"",
    mod_type=ModType.Inscription,
    apply_targets=[ApplyTarget.SpellCastingWeapon],
    arg1=int,
    arg2=int,
    modifier_value_arg=ModifierValue.Arg2,
    min_value={8984: 2, 9032: 50},  # Energy at 1 minimum
    max_value={8984: 7, 9032: 50},  # Energy capped at 5 maximum
    representation=lambda arg, arg1, arg2: (
        f"Energy +{arg2}% (while Health is below {arg1}%)"
    )
)

_MODIFIER_MAP[9000] = ModifierInfo(
    9000,
    name="\"I am Sorrow.\"",
    mod_type=ModType.Inscription,
    apply_targets=[ApplyTarget.SpellCastingWeapon],
    arg2=int,
    modifier_value_arg=ModifierValue.Arg2,
    min_value={9000: 2},
    max_value={9000: 7},
    representation=lambda arg, arg1, arg2: f"Energy +{arg2} (while Hexed)"
)

_MODIFIER_MAP[25288] = ModifierInfo(
    25288,
    name="\"Seize the Day\"",
    arg1=int,
    mod_type=ModType.Inscription,
    apply_targets=[ApplyTarget.SpellCastingWeapon],
    min_value={8920: 10},
    max_value={8920: 15},
    modifier_value_arg=ModifierValue.Arg2,
    representation=lambda arg, arg1, arg2: (
        f"{_MODIFIER_MAP[8920].format(None, None, arg2)}\n"
        f"{_MODIFIER_MAP[8392].format(None, None, arg2)}"
    ),
)

_MODIFIER_MAP[8712] = ModifierInfo(
    8712,
    name="\"Don't Think Twice\"",
    arg1=int,
    mod_type=ModType.Inscription,
    apply_targets=[ApplyTarget.Weapon],
    min_value={8712: 5},
    max_value={8712: 10},
    modifier_value_arg=ModifierValue.Arg1,
    representation=lambda arg, arg1, arg2: (
        f"Halves casting time of spells (Chance: {arg1}%)"
    ),
)

_MODIFIER_MAP[10248] = ModifierInfo(
    10248,
    name= "\"Aptitude not Attitude\"",
    arg1=int,
    mod_type=ModType.Inscription,
    apply_targets=[ApplyTarget.SpellCastingWeapon],
    min_value={10248: 10},
    max_value={10248: 20},
    modifier_value_arg=ModifierValue.Arg1,
    representation=lambda arg, arg1, arg2: (
        f"Halves casting time on spells of item's attribute (Chance: {arg1}%)"
    ),
)

#region off-hand
_MODIFIER_MAP[41240] = ModifierInfo(
    41240,
    name="\"Not the Face!\"",
    arg1=DamageType,
    arg2=int,
    mod_type=ModType.Inscription,
    apply_targets=[ApplyTarget.Offhand],
    min_value={41240: 5},
    max_value={41240: 10},
    modifier_value_arg=ModifierValue.Arg2,
    representation=lambda arg, arg1, arg2: f"Armor +{arg2} (vs. {arg1} damage)"
)
add_modifier(ModifierInfo(
    identifier=41240,
     
    name="\"Not the Face!\"", 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Attribute", 
    arg1_eval_fn=lambda attribute_id: GetDamageType(attribute_id), 
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"Armor +{arg2} (vs. {arg1} damage)"
))



add_modifier(ModifierInfo(
    identifier=8312,
     
    name='Inscription: "Luck of the Draw"', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Attribute", 
    arg1_eval_fn=lambda value: Value(value), 
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"Recieved physical damage -{arg2} (Chance: {arg1}%)"
))

add_modifier(ModifierInfo(
    identifier=8328,
     
    name='Inscription: "Sheltered by faith"', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="INVALID", 
    arg1_eval_fn=None, 
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"Recieved physical damage -{arg2} (while Enchanted)"
))

add_modifier(ModifierInfo(
    identifier=8344,
     
    name='Inscription: "Nothing to Fear"', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="INVALID", 
    arg1_eval_fn=None, 
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"Recieved physical damage -{arg2} (while Hexed)"
))

add_modifier(ModifierInfo(
    identifier=8360,
     
    name='Inscription: "Run For Your Life!"', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="INVALID", 
    arg1_eval_fn=None, 
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"Recieved physical damage -{arg2} (while in a Stance)"
))


add_modifier(ModifierInfo(
    identifier=8408,
     
    name='Inscription: "Life is Pain" / Superior Rune',  
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=None,
    arg2="INVALID",
    arg2_eval_fn=lambda value: Value(value), 
    representation=lambda arg, arg1, arg2: f"Health +/-{arg2}"
))

add_modifier(ModifierInfo(
    identifier=8424,
     
    name='Vampiric', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=lambda value: Value(value), 
    arg2="INVALID",
    arg2_eval_fn=None,
    representation=lambda arg, arg1, arg2: f"Health regeneration -{arg2}"
))

add_modifier(ModifierInfo(
    identifier=8456,
     
    name='Armor', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=lambda value: Value(value), 
    arg2="INVALID",
    arg2_eval_fn=None,
    representation=lambda arg, arg1, arg2: f"Armor +{arg2}"
))


add_modifier(ModifierInfo(
    identifier=8488,
     
    name='Warding',
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="INVALID", 
    arg1_eval_fn=lambda value: Value(value), 
    arg2="Armor",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"Armor +{arg2} (vs. elemental damage)"
))

add_modifier(ModifierInfo(
    identifier=8536,
     
    name='Shelter',
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="INVALID", 
    arg1_eval_fn=lambda value: Value(value), 
    arg2="Armor",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"Armor +{arg2} (vs. physical damage)"
))

add_modifier(ModifierInfo(
    identifier=8568,
     
    name='Inscription: "Might makes Right"', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="INVALID", 
    arg1_eval_fn=lambda value: Value(value),
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"Armor +{arg2} (while attacking)"
))

add_modifier(ModifierInfo(
    identifier=8584,
     
    name='Inscription: "Knowing is Half the Battle."', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="INVALID", 
    arg1_eval_fn=lambda value: Value(value),
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"Armor +{arg2} (while casting)"
))

add_modifier(ModifierInfo(
    identifier=8600,
     
    name='Inscription: "Faith is My Shield"', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="INVALID", 
    arg1_eval_fn=lambda value: Value(value),
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"Armor +{arg2} (while Enchanted)"
))


add_modifier(ModifierInfo(
    identifier=8616,
     
    name='Inscription: "Hail to the King"', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Above", 
    arg1_eval_fn=lambda value: Value(value), 
    arg2="Damage",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"Armor +{arg2} (while Health is above {arg1}%)"
))

add_modifier(ModifierInfo(
    identifier=8632,
     
    name='Inscription: "Down But Not Out"', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Below", 
    arg1_eval_fn=lambda value: Value(value), 
    arg2="Damage",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"Armor +{arg2} (while Health is below {arg1}%)"
))

add_modifier(ModifierInfo(
    identifier=8648,
     
    name='Inscription: "Be Just and Fear Not"', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="INVALID", 
    arg1_eval_fn=lambda value: Value(value),
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"Armor +{arg2} (while Hexed)"
))







add_modifier(ModifierInfo(
    identifier=8888,
     
    name='Of Enchanting', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="INVALID", 
    arg1_eval_fn=None, 
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"Enchantments last {arg2}% longer"
))



add_modifier(ModifierInfo(
    identifier=9064,
     
    name='Devotion', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=lambda value: Value(value), 
    arg2="INVALID",
    arg2_eval_fn=None,
    representation=lambda arg, arg1, arg2: f"Health +{arg1} (while Enchanted)"
))

add_modifier(ModifierInfo(
    identifier=9080,
     
    name='Health while Hexed"', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=lambda value: Value(value), 
    arg2="INVALID",
    arg2_eval_fn=None,
    representation=lambda arg, arg1, arg2: f"Health +{arg1} (while Hexed)"
))

add_modifier(ModifierInfo(
    identifier=9096,
     
    name='Health wile in a stance"', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="INVALID", 
    arg1_eval_fn=lambda value: Value(value),
    arg2="Value",
    arg2_eval_fn=None,
    representation=lambda arg, arg1, arg2: f"Health +{arg1} (while in a stance)"
))

add_modifier(ModifierInfo(
    identifier=9112,
     
    name='Halves skill recharge of [Attribute] spells', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=lambda value: Value(value), 
    arg2="INVALID",
    arg2_eval_fn=lambda attribute_id: GetAttributeName(attribute_id),
    representation=lambda arg, arg1, arg2: f"Halves skill recharge of {arg2} spells (Chance: {arg1}%)"
))



add_modifier(ModifierInfo(
    identifier=9144,
     
    name='Furious', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=None,
    arg2="INVALID",
    arg2_eval_fn=lambda value: Value(value), 
    representation=lambda arg, arg1, arg2: f"Double adrenaline gain (Chance: {arg2}%)"
))

add_modifier(ModifierInfo(
    identifier=9208,
     
    name='Sundering', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=lambda value: Value(value), 
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"Armor penetration +{arg2}% (Chance: {arg1}%)"
))

add_modifier(ModifierInfo(
    identifier=9224,
     
    name='Unknown 9224', 
    arg="Value", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=None, 
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"{arg} , {arg1} , {arg2}"
))

add_modifier(ModifierInfo(
    identifier=9240,
     
    name="Mastery", 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Attribute", 
    arg1_eval_fn=lambda attribute_id: GetAttributeName(attribute_id), 
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"{arg1} +1 ({arg2} chance while using skills)"
))

add_modifier(ModifierInfo(
    identifier=9320,
     
    name='lengthens_condition', 
    arg="INVALID", 
    arg_eval_fn=lambda value: Value(value),
    arg1="INVALID", 
    arg1_eval_fn=lambda value: Value(value),
    arg2="Ailment",
    arg2_eval_fn=lambda damage_type_id: GetAilment(damage_type_id), 
    representation=lambda arg, arg1, arg2: f"Lenghtens {arg2} duration on foes by 33%"
))

add_modifier(ModifierInfo(
    identifier=9336,
     
    name='reduces_condition', 
    arg="INVALID", 
    arg_eval_fn=lambda value: Value(value),
    arg1="Ailment", 
    arg1_eval_fn=None,
    arg2="INVALID",
    arg2_eval_fn= lambda damage_type_id: GetAilment(damage_type_id),
    representation=lambda arg, arg1, arg2: f"Reduces {arg2} duration on you by 20% (Stacking)"
))

add_modifier(ModifierInfo(
    identifier=9400,
     
    name="Damage Type", 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Type", 
    arg1_eval_fn=lambda damage_type_id: GetDamageType(damage_type_id), 
    arg2="INVALID",
    arg2_eval_fn=None,
    representation=lambda arg, arg1, arg2: f"{arg1} Dmg: "
))

add_modifier(ModifierInfo(
    identifier=9496,
     
    name='Zealous', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=None,
    arg2="INVALID",
    arg2_eval_fn=lambda value: Value(value), 
    representation=lambda arg, arg1, arg2: f"Energy gain on hit: {arg2}"
))

add_modifier(ModifierInfo(
    identifier=9512,
     
    name='Vampiric', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=lambda value: Value(value), 
    arg2="INVALID",
    arg2_eval_fn=None,
    representation=lambda arg, arg1, arg2: f"Life Draining: {arg1}"
))

add_modifier(ModifierInfo(
    identifier=9520,
     
    name='Unknown 9520', 
    arg="Value", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=None, 
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"{arg} , {arg1} , {arg2}"
))

add_modifier(ModifierInfo(
    identifier=9522,
     
    name='Unknown 9522', 
    arg="Value", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=None, 
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"{arg} , {arg1} , {arg2}"
))

add_modifier(ModifierInfo(
    identifier=9720,
     
    name='Inscription: "Show me the money!"', 
    arg="INVALID", 
    arg_eval_fn=lambda value: Value(value),
    arg1="INVALID", 
    arg1_eval_fn=lambda value: Value(value),
    arg2="INVALID",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"Improved sale value ({arg} , {arg1} , {arg2})"
))

add_modifier(ModifierInfo(
    identifier=9736,
     
    name='Inscription: "Measure for Measure"', 
    arg="INVALID", 
    arg_eval_fn=lambda value: Value(value),
    arg1="INVALID", 
    arg1_eval_fn=lambda value: Value(value),
    arg2="INVALID",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"Highly salvageable ({arg} , {arg1} , {arg2})"
))

add_modifier(ModifierInfo(
    identifier=9752,
     
    name='Unknown 9752', 
    arg="Value", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=None, 
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"{arg} , {arg1} , {arg2}"
))

add_modifier(ModifierInfo(
    identifier=9800,
     
    name='Unknown 9800', 
    arg="Value", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=None, 
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"{arg} , {arg1} , {arg2}"
))

add_modifier(ModifierInfo(
    identifier=9880,
     
    name='Unknown 9880', 
    arg="Value", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=None, 
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"{arg} , {arg1} , {arg2}"
))

add_modifier(ModifierInfo(
    identifier=10136,
     
    name="Requires", 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Attribute", 
    arg1_eval_fn=lambda attribute_id: GetAttributeName(attribute_id), 
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"(Requires {arg2} {arg1})"
))



add_modifier(ModifierInfo(
    identifier=10280,
     
    name='Halves skill recharge of [Attribute] spells', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=lambda value: Value(value), 
    arg2="INVALID",
    arg2_eval_fn=None,
    representation=lambda arg, arg1, arg2: f"Halves skill recharge of [Attribute] spells (Chance: {arg1}%)"
))

add_modifier(ModifierInfo(
    identifier=10296,
     
    name='Inscription: "Master of My Domain"',  
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=lambda value: Value(value), 
    arg2="INVALID",
    arg2_eval_fn=None,
    representation=lambda arg, arg1, arg2: f"[Attribute] +1 (Chance: {arg1}%)"
))

add_modifier(ModifierInfo(
    identifier=10328,
     
    name='reduces_condition', 
    arg="INVALID", 
    arg_eval_fn=lambda value: Value(value),
    arg1="Ailment", 
    arg1_eval_fn=lambda damage_type_id: GetReducedAilment(damage_type_id),
    arg2="INVALID",
    arg2_eval_fn= lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"Reduces {arg1} duration on you by 20% (Stacking)"
))


add_modifier(ModifierInfo(
    identifier=26568,
     
    name='Energy', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Above", 
    arg1_eval_fn=lambda value: Value(value), 
    arg2="Damage",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"Energy +{arg1}"
))

add_modifier(ModifierInfo(
    identifier=32784,
     
    name="Requires", 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Attribute", 
    arg1_eval_fn=lambda attribute_id: GetAttributeName(attribute_id), 
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"(Requires {arg2} {arg1})"
))


add_modifier(ModifierInfo(
    identifier=32880,
     
    name='Unknown 32880', 
    arg="Value", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=None, 
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"{arg} , {arg1} , {arg2}"
))

add_modifier(ModifierInfo(
    identifier=32896,
     
    name='Unknown 32896', 
    arg="Value", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=None, 
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"{arg} , {arg1} , {arg2}"
))


add_modifier(ModifierInfo(
    identifier=41544,
     
    name='Deathbane', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="INVALID", 
    arg1_eval_fn=lambda value: Value(value),
    arg2="Value",
    arg2_eval_fn=None,
    representation=lambda arg, arg1, arg2: f"Dmg +{arg1}% (vs. undead)"
))

add_modifier(ModifierInfo(
    identifier=42288,
     
    name='Unknown 42288', 
    arg="Value", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=None, 
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"{arg} , {arg1} , {arg2}"
))

add_modifier(ModifierInfo(
    identifier=42290,
     
    name='Inscription Name', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=None,
    arg2="INVALID",
    arg2_eval_fn=lambda attribute_id: GetInscription(attribute_id),
    representation=lambda arg, arg1, arg2: f"Inscription: {arg2}"
))

add_modifier(ModifierInfo(
    identifier=42920,
     
    name="Damage range", 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Max", 
    arg1_eval_fn=lambda value: Value(value), 
    arg2="Min",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"{arg2}-{arg1}"
))

add_modifier(ModifierInfo(
    identifier=42936,
     
    name='Shield Armor', 
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=lambda value: Value(value), 
    arg2="INVALID",
    arg2_eval_fn=None,
    representation=lambda arg, arg1, arg2: f"Armor: {arg1}"
))

add_modifier(ModifierInfo(
    identifier=49152,
     
    name="Unknown 49152 InventoryItemtype?", 
    arg="Value", 
    arg_eval_fn=lambda value: Value(value), 
    arg1="Value", 
    arg1_eval_fn=lambda value: Value(value), 
    arg2="Value",
    arg2_eval_fn=lambda value: Value(value),
    representation=lambda arg, arg1, arg2: f"{arg} , {arg1} , {arg2}"
))

add_modifier(ModifierInfo(
    identifier=9128,
     
    name='Inscription: "Let the Memory Live Again" / "Serenity Now"',
    arg="INVALID", 
    arg_eval_fn=None, 
    arg1="Value", 
    arg1_eval_fn=lambda value: Value(value), 
    arg2="INVALID",
    arg2_eval_fn=None,
    representation=lambda arg, arg1, arg2: f"Halves skill recharge of spells (Chance: {arg1}%)"
))

input_item1 = 0
input_item2 = 0
item1_id = 0
item2_id = 0
hovered_item = 0

def ShowOffhandItemdescription():
    try:
        global item1_id, item2_id, hovered_item
        global modifiers, window_module

        if window_module.first_run:
            PyImGui.set_next_window_size(window_module.window_size[0], window_module.window_size[1])     
            PyImGui.set_next_window_pos(window_module.window_pos[0], window_module.window_pos[1])
            window_module.first_run = False

        if PyImGui.begin(f"Offhand Item Description", window_module.window_flags):

            hovered_item = Inventory.GetHoveredItemID()
            PyImGui.text(f"Hovered Item: {hovered_item}")
            PyImGui.separator()

            bags_to_check = ItemArray.CreateBagList(1,2,3,4)
            item_array = ItemArray.GetItemArray(bags_to_check)

            item1_id = item_array[0] if item_array else None

            if not item1_id:
                PyImGui.text("No item selected for description.")
                PyImGui.end()
                return

            PyImGui.separator()

            
            item1_type_id, item1_type_name = Item.GetItemType(item1_id)
            PyImGui.text(f"Item 1 ID: {item1_id}")
            PyImGui.text(f"Type: {item1_type_id} - {item1_type_name}")


            modifiers1 = Item.Customization.Modifiers.GetModifiers(item1_id)
            if not modifiers1:
                PyImGui.text("No modifiers found.")
                PyImGui.end()
                return

            for modifier in modifiers1:
                identifier = modifier.GetIdentifier()
                mod_data = find_modifier(identifier)
                if not mod_data:
                    continue

                #check if the name of the modifier doesnt start weith "Unknown"
                if not mod_data.name.startswith("Unknown"):
                    arg, arg1, arg2 = modifier.GetArg(), modifier.GetArg1(), modifier.GetArg2()
                    arg_eval = mod_data.arg_eval_fn(arg) if mod_data.arg_eval_fn else arg
                    arg1_eval = mod_data.arg1_eval_fn(arg1) if mod_data.arg1_eval_fn else arg1
                    arg2_eval = mod_data.arg2_eval_fn(arg2) if mod_data.arg2_eval_fn else arg2

                    if mod_data.name.startswith("Inscription"):
                        PyImGui.text(f"{mod_data.name}")
                    PyImGui.text(f"{mod_data.representation(arg_eval, arg1_eval, arg2_eval)}")

            # Close window
            PyImGui.end()
    except Exception as e:
        # Log and handle the exception
        Py4GW.Console.Log(module_name, f"Error in ShowItemComparisonWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

def ShowItemdescription():
    try:
        global item1_id, item2_id, hovered_item
        global modifiers, window_module

        if window_module.first_run:
            PyImGui.set_next_window_size(window_module.window_size[0], window_module.window_size[1])     
            PyImGui.set_next_window_pos(window_module.window_pos[0], window_module.window_pos[1])
            window_module.first_run = False

        if PyImGui.begin(f"Item Description", window_module.window_flags):

            hovered_item = Inventory.GetHoveredItemID()
            PyImGui.text(f"Hovered Item: {hovered_item}")
            PyImGui.separator()

            bags_to_check = ItemArray.CreateBagList(1,2,3,4)
            item_array = ItemArray.GetItemArray(bags_to_check)

            item1_id = item_array[0] if item_array else None

            if not item1_id:
                PyImGui.text("No item selected for description.")
                PyImGui.end()
                return

            PyImGui.separator()

            
            item1_type_id, item1_type_name = Item.GetItemType(item1_id)
            PyImGui.text(f"Item 1 ID: {item1_id}")
            PyImGui.text(f"Type: {item1_type_id} - {item1_type_name}")


            modifiers1 = Item.Customization.Modifiers.GetModifiers(item1_id)
            if not modifiers1:
                PyImGui.text("No modifiers found.")
                PyImGui.end()
                return

            damage_type = find_modifier(9400)
            damage_range = find_modifier(42920)
            requires = find_modifier(10136)

            if not damage_type or not damage_range or not requires:
                PyImGui.text("Missing critical modifiers.")
                PyImGui.end()
                return


            result = Item.Customization.Modifiers.GetModifierValues(item1_id, 9400)

            if not result or result == (None, None, None):
                PyImGui.text("Damage type values could not be retrieved.")
                PyImGui.end()
                return
            arg, arg1, arg2 = result

            arg_eval = damage_type.arg_eval_fn(arg) if damage_type.arg_eval_fn else arg
            arg1_eval = damage_type.arg1_eval_fn(arg1) if damage_type.arg1_eval_fn else arg1
            arg2_eval = damage_type.arg2_eval_fn(arg2) if damage_type.arg2_eval_fn else arg2

            first_line = f"{damage_type.representation(arg_eval, arg1_eval, arg2_eval)}"
            
            result = Item.Customization.Modifiers.GetModifierValues(item1_id, 42920)

            if not result or result == (None, None, None):
                PyImGui.text("Damage Range values not be retrieved.")
                PyImGui.end()
                return
            arg, arg1, arg2 = result

            arg_eval = damage_range.arg_eval_fn(arg) if damage_range.arg_eval_fn else arg
            arg1_eval = damage_range.arg1_eval_fn(arg1) if damage_range.arg1_eval_fn else arg1
            arg2_eval = damage_range.arg2_eval_fn(arg2) if damage_range.arg2_eval_fn else arg2

            first_line += f"{damage_range.representation(arg_eval, arg1_eval, arg2_eval)}"
       
            result = Item.Customization.Modifiers.GetModifierValues(item1_id, 10136)

            if not result or result == (None, None, None):
                PyImGui.text("Requirement values could not be retrieved.")
                PyImGui.end()
                return
            arg, arg1, arg2 = result

            arg_eval = requires.arg_eval_fn(arg) if requires.arg_eval_fn else arg
            arg1_eval = requires.arg1_eval_fn(arg1) if requires.arg1_eval_fn else arg1
            arg2_eval = requires.arg2_eval_fn(arg2) if requires.arg2_eval_fn else arg2

            first_line += f" {requires.representation(arg_eval, arg1_eval, arg2_eval)}"

            PyImGui.text(f"{first_line}")

            for modifier in modifiers1:
                identifier = modifier.GetIdentifier()
                mod_data = find_modifier(identifier)
                if not mod_data:
                    continue

                if identifier == 9400 or identifier == 42920 or identifier == 10136:
                    continue

                #check if the name of the modifier doesnt start weith "Unknown"
                if not mod_data.name.startswith("Unknown"):
                    arg, arg1, arg2 = modifier.GetArg(), modifier.GetArg1(), modifier.GetArg2()
                    arg_eval = mod_data.arg_eval_fn(arg) if mod_data.arg_eval_fn else arg
                    arg1_eval = mod_data.arg1_eval_fn(arg1) if mod_data.arg1_eval_fn else arg1
                    arg2_eval = mod_data.arg2_eval_fn(arg2) if mod_data.arg2_eval_fn else arg2

                    if mod_data.name.startswith("Inscription"):
                        PyImGui.text(f"{mod_data.name}")
                    PyImGui.text(f"{mod_data.representation(arg_eval, arg1_eval, arg2_eval)}")

            # Close window
            PyImGui.end()
    except Exception as e:
        # Log and handle the exception
        Py4GW.Console.Log(module_name, f"Error in ShowItemComparisonWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

"""
identifier = 0
def ShowModifierDecoderWindow():
    try:
        global window_module, identifier

        if window_module.first_run:
            PyImGui.set_next_window_size(window_module.window_size[0], window_module.window_size[1])
            PyImGui.set_next_window_pos(0, 0)
            window_module.first_run = False

        if PyImGui.begin("Modifier Decoder", window_module.window_flags):
            PyImGui.text("Enter Modifier Identifier:")
            identifier = PyImGui.input_int("Identifier", identifier)

            if identifier is not None:
                modifier_info = decode_modifier(identifier)
                PyImGui.text(f"Decoded Modifier:")
                PyImGui.text(f"Name: {modifier_info.name}")
                PyImGui.text(f"Arg: {modifier_info.arg}")
                PyImGui.text(f"Arg1: {modifier_info.arg1}")
                PyImGui.text(f"Arg2: {modifier_info.arg2}")
            else:
                PyImGui.text("Invalid Identifier.")

            PyImGui.end()
    except Exception as e:
        Py4GW.Console.Log(module_name, f"Error in ShowModifierDecoderWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise
    
    """
    
def ShowItemComparisonWindow():
    try:
        global item1_id, item2_id, hovered_item
        global item_show, input_item1, input_item2
        global modifiers, window_module

        if window_module.first_run:
            PyImGui.set_next_window_size(window_module.window_size[0], window_module.window_size[1])     
            PyImGui.set_next_window_pos(window_module.window_pos[0], window_module.window_pos[1])
            window_module.first_run = False

        if PyImGui.begin(f"Compare Items", window_module.window_flags):

            hovered_item = Inventory.GetHoveredItemID()
            PyImGui.text(f"Hovered Item: {hovered_item}")
            PyImGui.separator()

            bags_to_check = ItemArray.CreateBagList(1,2,3,4)
            item_array = ItemArray.GetItemArray(bags_to_check)

            input_item1 = item_array[0]
            input_item2 = item_array[1]
            # Input fields for item IDs
            #input_item1 = PyImGui.input_int("Item 1 ID", input_item1)
            #input_item2 = PyImGui.input_int("Item 2 ID", input_item2)


            #if PyImGui.button("Compare Items"):
            item1_id = input_item1
            item2_id = input_item2

            PyImGui.separator()

            headers = ["Property", "Item 1", "Item 2"]
            
            # Common Item Info
            item1_type_id, item1_type_name = Item.GetItemType(item1_id)
            item2_type_id, item2_type_name = Item.GetItemType(item2_id)
            
            data = [
                ("Item Type:", f"{item1_type_id} - {item1_type_name}", f"{item2_type_id} - {item2_type_name}"),
                ("Model Id:", Item.GetModelID(item1_id), Item.GetModelID(item2_id)),
                ("Slot:", Item.GetSlot(item1_id), Item.GetSlot(item2_id)),
                ("AgentId:", Item.GetAgentID(item1_id), Item.GetAgentID(item2_id)),
                ("AgentItemID:", Item.GetAgentItemID(item1_id), Item.GetAgentItemID(item2_id)),
            ]
            ImGui.table("Item comparison common info", headers, data)

            # Modifier comparison
            if PyImGui.collapsing_header("Modifiers"):
                # Retrieve modifiers for both items
                modifiers1 = Item.Customization.Modifiers.GetModifiers(item1_id)
                modifiers2 = Item.Customization.Modifiers.GetModifiers(item2_id)

                # Gather all unique identifiers for comparison
                all_identifiers = {mod.GetIdentifier() for mod in modifiers1}.union({mod.GetIdentifier() for mod in modifiers2})

                # Iterate over all unique identifiers
                for identifier in all_identifiers:
                    mod1 = next((mod for mod in modifiers1 if mod.GetIdentifier() == identifier), None)
                    mod2 = next((mod for mod in modifiers2 if mod.GetIdentifier() == identifier), None)

                    # Extract data or use an empty string for missing modifiers
                    identifier1 = mod1.GetIdentifier() if mod1 else " "
                    identifier2 = mod2.GetIdentifier() if mod2 else " "
    
                    item1_arg = mod1.GetArg() if mod1 else " "
                    item2_arg = mod2.GetArg() if mod2 else " "
    
                    item1_arg1 = mod1.GetArg1() if mod1 else " "
                    item2_arg1 = mod2.GetArg1() if mod2 else " "
    
                    item1_arg2 = mod1.GetArg2() if mod1 else " "
                    item2_arg2 = mod2.GetArg2() if mod2 else " "

                    # Lookup modifier data if available and process with eval functions
                    ident = identifier1 if mod1 else identifier2
                    if isinstance(ident, int):
                        mod_data = find_modifier(ident)
                    else:
                        mod_data = None
    
                    header_1, header_2 = "Item 1", "Item 2"
                    arg_name, arg1_name, arg2_name = "", "", ""

                    representation_1 , representation_2 = "", ""

                    if mod_data:
                        header_1 = mod_data.name + "(1)"
                        header_2 = mod_data.name + "(2)"
                        arg_name = mod_data.arg
                        arg1_name = mod_data.arg1
                        arg2_name = mod_data.arg2

                        # Evaluate each arg if functions are provided

                        item1_arg = mod_data.arg_eval_fn(item1_arg) if mod_data.arg_eval_fn else item1_arg
                        item2_arg = mod_data.arg_eval_fn(item2_arg) if mod_data.arg_eval_fn else item2_arg

                        item1_arg1 = mod_data.arg1_eval_fn(item1_arg1) if mod_data.arg1_eval_fn else item1_arg1
                        item2_arg1 = mod_data.arg1_eval_fn(item2_arg1) if mod_data.arg1_eval_fn else item2_arg1
                        item1_arg2 = mod_data.arg2_eval_fn(item1_arg2) if mod_data.arg2_eval_fn else item1_arg2
                        item2_arg2 = mod_data.arg2_eval_fn(item2_arg2) if mod_data.arg2_eval_fn else item2_arg2

                        # Generate representation strings     
                        representation_1 = mod_data.representation(item1_arg, item1_arg1, item1_arg2) if mod1 else " "
                        representation_2 = mod_data.representation(item2_arg, item2_arg1, item2_arg2) if mod2 else " "
                    else:
                        arg_name = arg1_name = arg2_name = " "

                    if mod_data:
                        headers = ["Value", header_1, header_2]
                        data = [
                            (f"Item Type:", f"{item1_type_id} - {item1_type_name}", f"{item2_type_id} - {item2_type_name}"),
                            ("Representation:", representation_1, representation_2)
                        ]
                    else:
                        headers = ["Value", header_1, header_2]
                        data = [
                            (f"Identifier:", identifier1, identifier2),
                            (f"Item Type:", f"{item1_type_id} - {item1_type_name}", f"{item2_type_id} - {item2_type_name}"),
                        ]

                        # Conditionally add each item based on `arg_name`, `arg1_name`, and `arg2_name`
                        if arg_name != "INVALID":
                            data.append((f"Arg: {arg_name}", item1_arg, item2_arg))
                        if arg1_name != "INVALID":
                            data.append((f"Arg1: {arg1_name}", item1_arg1, item2_arg1))
                        if arg2_name != "INVALID":
                            data.append((f"Arg2: {arg2_name}", item1_arg2, item2_arg2))

                    # Highlighting logic
                    if mod_data:
                        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.0, 1.0, 1.0, 1.0))  # Blue for found mod
                    elif identifier1 == identifier2 and item1_arg == item2_arg and item1_arg1 == item2_arg1 and item1_arg2 == item2_arg2:
                        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (0.0, 1.0, 0.0, 1.0))  # Green for identical mods
                    else:
                        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, (1.0, 0.0, 0.0, 1.0))  # Red for different mods

                    ImGui.table(f"Item Modifiers Comparison {identifier}", headers, data)
                    PyImGui.pop_style_color(1)

            # Close window
            PyImGui.end()
    except Exception as e:
        # Log and handle the exception
        Py4GW.Console.Log(module_name, f"Error in ShowItemComparisonWindow: {str(e)}", Py4GW.Console.MessageType.Error)
        raise



# main function must exist in every script and is the entry point for your script's execution.
def main():
    global module_name
    try:
        ShowItemComparisonWindow()
        ShowItemdescription()
        ShowOffhandItemdescription()

    # Handle specific exceptions to provide detailed error messages
    except ImportError as e:
        Py4GW.Console.Log(module_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(module_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(module_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(module_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        # Optional: Code that will run whether an exception occurred or not
        #Py4GW.Console.Log(module_name, "Execution of Main() completed", Py4GW.Console.MessageType.Info)
        # Place any cleanup tasks here
        pass

# This ensures that Main() is called when the script is executed directly.
if __name__ == "__main__":
    main()


#region processed
