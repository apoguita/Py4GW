from __future__ import annotations

from Py4GWCoreLib import BuildMgr, Profession

from .any import AnySkills
from .warrior import WarriorSkills
from .ranger import RangerSkills
from .Monk import MonkSkills
from .necromancer import NecromancerSkills
from .mesmer import MesmerSkills
from .elementalist import ElementalistSkills
from .assassin import AssassinSkills
from .ritualist import RitualistSkills
from .paragon import ParagonSkills
from .dervish import DervishSkills


class SkillsTemplate(BuildMgr):
    """
    Root scaffold for shared build-skill modules.

    Each profession group exposes one object per attribute, including
    a NoAttribute bucket for profession-specific untyped skills.
    """

    def __init__(self, owner: BuildMgr | None = None, match_only: bool = False):
        super().__init__(
            name="Skills",
            required_primary=Profession._None,
            template_code="",
            is_template_only=True,
            required_skills=[],
            optional_skills=[],
        )

        if match_only:
            return

        self.owner: BuildMgr = owner if owner is not None else self
        self.Any: AnySkills = AnySkills(self.owner)
        self.Warrior: WarriorSkills = WarriorSkills(self.owner)
        self.Ranger: RangerSkills = RangerSkills(self.owner)
        self.Monk: MonkSkills = MonkSkills(self.owner)
        self.Necromancer: NecromancerSkills = NecromancerSkills(self.owner)
        self.Mesmer: MesmerSkills = MesmerSkills(self.owner)
        self.Elementalist: ElementalistSkills = ElementalistSkills(self.owner)
        self.Assassin: AssassinSkills = AssassinSkills(self.owner)
        self.Ritualist: RitualistSkills = RitualistSkills(self.owner)
        self.Paragon: ParagonSkills = ParagonSkills(self.owner)
        self.Dervish: DervishSkills = DervishSkills(self.owner)
