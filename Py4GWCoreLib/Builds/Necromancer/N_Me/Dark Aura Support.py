from __future__ import annotations

from Py4GWCoreLib import BuildMgr, Profession, Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib.Builds.Skills import SkillsTemplate
from Py4GWCoreLib.Skill import Skill


DARK_AURA_ID = Skill.GetID("Dark_Aura")
MASOCHISM_ID = Skill.GetID("Masochism")
GREAT_DWARF_WEAPON_ID = Skill.GetID("Great_Dwarf_Weapon")
EVAS_ID = Skill.GetID("Ebon_Vanguard_Assassin_Support")
FOUL_FEAST_ID = Skill.GetID("Foul_Feast")
TECHNOBABBLE_ID = Skill.GetID("Technobabble")
EXPEL_HEXES_ID = Skill.GetID("Expel_Hexes")
PUTRID_EXPLOSION_ID = Skill.GetID("Putrid_Explosion")
SOUL_TAKER_ID = Skill.GetID("Soul_Taker")


class Dark_Aura_Support(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Dark Aura Support",
            required_primary=Profession.Necromancer,
            required_secondary=Profession.Mesmer,
            template_code="OAVCUslEdwW4q4uYCYbpuzXA",
            required_skills=[
                DARK_AURA_ID,
                MASOCHISM_ID,
                GREAT_DWARF_WEAPON_ID,
                EVAS_ID,
                FOUL_FEAST_ID,
                TECHNOBABBLE_ID,
                EXPEL_HEXES_ID,
                PUTRID_EXPLOSION_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            return False

        if self.IsSkillEquipped(MASOCHISM_ID) and (
            yield from self.skills.Necromancer.SoulReaping.Masochism()
        ):
            return True

        if self.IsSkillEquipped(DARK_AURA_ID) and (
            yield from self.skills.Necromancer.DeathMagic.Dark_Aura(
                required_skill_id=SOUL_TAKER_ID,
                other_ally=True,
            )
        ):
            return True

        if self.IsSkillEquipped(FOUL_FEAST_ID) and (
            yield from self.skills.Necromancer.SoulReaping.Foul_Feast()
        ):
            return True

        if self.IsSkillEquipped(EXPEL_HEXES_ID) and (
            yield from self.skills.Mesmer.NoAttribute.Expel_Hexes()
        ):
            return True

        if not self.IsInAggro():
            return False

        if self.IsSkillEquipped(GREAT_DWARF_WEAPON_ID) and (
            yield from self.skills.Any.NoAttribute.Great_Dwarf_Weapon()
        ):
            return True

        if self.IsSkillEquipped(EVAS_ID) and (
            yield from self.skills.Any.PvE.Ebon_Vanguard_Assassin_Support(min_self_energy_pct=0.35)
        ):
            return True

        if self.IsSkillEquipped(TECHNOBABBLE_ID) and (
            yield from self.skills.Any.PvE.Technobabble()
        ):
            return True

        if self.IsSkillEquipped(PUTRID_EXPLOSION_ID) and (
            yield from self.skills.Necromancer.DeathMagic.Putrid_Explosion()
        ):
            return True

        return False
