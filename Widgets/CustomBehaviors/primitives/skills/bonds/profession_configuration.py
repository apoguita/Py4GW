from dataclasses import dataclass
from Py4GWCoreLib.enums import Profession, Range

@dataclass
class ProfessionConfiguration:
    def __init__(self, bond_target_profession: Profession, is_activated: bool):
        self.bond_target_profession: Profession = bond_target_profession
        self.is_activated: bool = is_activated
