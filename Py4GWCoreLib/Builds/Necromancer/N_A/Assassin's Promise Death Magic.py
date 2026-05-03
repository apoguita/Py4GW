from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate

# Required
Putrid_Bile_ID = Skill.GetID("Putrid_Bile")
Assassins_Promise_ID = Skill.GetID("Assassins_Promise")
Putrid_Explosion_ID = Skill.GetID("Putrid_Explosion")

# Optional
Rising_Bile_ID = Skill.GetID("Rising_Bile")
Masochism_ID = Skill.GetID("Masochism")
Ebon_Battle_Standard_of_Honor_ID = Skill.GetID("Ebon_Battle_Standard_of_Honor")
Ebon_Vanguard_Assassin_Support_ID = Skill.GetID("Ebon_Vanguard_Assassin_Support")
You_Move_Like_a_Dwarf_ID = Skill.GetID("You_Move_Like_a_Dwarf")
Finish_Him_ID = Skill.GetID("Finish_Him")
Technobabble_ID = Skill.GetID("Technobabble")
Great_Dwarf_Weapon_ID = Skill.GetID("Great_Dwarf_Weapon")


class Assassins_Promise_Death_Magic(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Assassin's Promise Death Magic",
            required_primary=Profession.Necromancer,
            required_secondary=Profession.Assassin,
            template_code="OAdDQsNHTKgLQfBAAAAAAAAAAA",
            required_skills=[
                Putrid_Bile_ID,
                Assassins_Promise_ID,
                Putrid_Explosion_ID,
            ],
            optional_skills=[
                Rising_Bile_ID,
                Masochism_ID,
                Ebon_Battle_Standard_of_Honor_ID,
                Ebon_Vanguard_Assassin_Support_ID,
                You_Move_Like_a_Dwarf_ID,
                Finish_Him_ID,
                Technobabble_ID,
                Great_Dwarf_Weapon_ID,
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

        # Pre-buff: Masochism — only fires close-to-aggro and in-aggro per
        # the skill module's own gate. Top priority so the energy regen is
        # up before the burst rotation begins.
        if self.IsSkillEquipped(Masochism_ID) and (yield from self.skills.Necromancer.SoulReaping.Masochism()):
            return True

        # Combat opener: Rising Bile — 20-second hex, longest timer first
        # for maximum per-second damage on detonation.
        if self.IsSkillEquipped(Rising_Bile_ID) and (yield from self.skills.Necromancer.DeathMagic.Rising_Bile()):
            return True

        # Drop the +20% damage ward early so all subsequent damage benefits.
        if self.IsSkillEquipped(Ebon_Battle_Standard_of_Honor_ID) and (yield from self.skills.Any.NoAttribute.Ebon_Battle_Standard_of_Honor()):
            return True

        # Anchor the focus target with Assassin's Promise — the kill on this
        # foe recharges all skills and refunds energy.
        if (yield from self.skills.Assassin.DeadlyArts.Assassins_Promise()):
            return True

        # Single-target spike on the AP focus via summoned EVA.
        if self.IsSkillEquipped(Ebon_Vanguard_Assassin_Support_ID) and (yield from self.skills.Any.PvE.Ebon_Vanguard_Assassin_Support()):
            return True

        # Pile Putrid Bile on the AP target so it detonates on the kill.
        if (yield from self.skills.Necromancer.DeathMagic.Putrid_Bile()):
            return True

        # Knockdown the AP focus to slow its damage output / cast progress.
        if self.IsSkillEquipped(You_Move_Like_a_Dwarf_ID) and (yield from self.skills.Any.NoAttribute.You_Move_Like_a_Dwarf()):
            return True

        # Apply Cracked Armor + Deep Wound when a target dips below 50% HP.
        if self.IsSkillEquipped(Finish_Him_ID) and (yield from self.skills.Any.NoAttribute.Finish_Him()):
            return True

        # Interrupt + daze a casting enemy.
        if self.IsSkillEquipped(Technobabble_ID) and (yield from self.skills.Any.PvE.Technobabble()):
            return True

        # Cleanup: exploit any corpse the AP kill chain left behind.
        if (yield from self.skills.Necromancer.DeathMagic.Putrid_Explosion()):
            return True

        # Opportunistic ally support — buff a martial ally with GDW.
        if self.IsSkillEquipped(Great_Dwarf_Weapon_ID) and (yield from self.skills.Any.NoAttribute.Great_Dwarf_Weapon()):
            return True

        return False
