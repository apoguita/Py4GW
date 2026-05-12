from dataclasses import dataclass

from Py4GWCoreLib import Profession
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import HexRemovalPriority, SkillsTemplate

Symbolic_Celerity_ID = Skill.GetID("Symbolic_Celerity")
Keystone_Signet_ID = Skill.GetID("Keystone_Signet")
Unnatural_Signet_ID = Skill.GetID("Unnatural_Signet")
Signet_of_Clumsiness_ID = Skill.GetID("Signet_of_Clumsiness")
Smite_Hex_ID = Skill.GetID("Smite_Hex")
Hex_Eater_Signet_ID = Skill.GetID("Hex_Eater_Signet")
Castigation_Signet_ID = Skill.GetID("Castigation_Signet")
Bane_Signet_ID = Skill.GetID("Bane_Signet")
Breath_of_the_Great_Dwarf_ID = Skill.GetID("Breath_of_the_Great_Dwarf")


@dataclass(slots=True)
class _KeystoneBarSnapshot:
    has_symbolic_celerity: bool = False
    has_keystone_signet: bool = False
    enemy_in_spellcast: bool = False
    attacking_enemy_in_spellcast: bool = False

    @property
    def symbolic_celerity_needed(self) -> bool:
        return not self.has_symbolic_celerity

    @property
    def keystone_signet_needed(self) -> bool:
        return self.has_symbolic_celerity and not self.has_keystone_signet


class KeystoneSignet(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Keystone Signet",
            required_primary=Profession.Mesmer,
            template_code="OQITEZJZVSpYHEqQsGAAAAAAAAA",
            required_skills=[
                Symbolic_Celerity_ID,
                Keystone_Signet_ID,
                Unnatural_Signet_ID,
                Signet_of_Clumsiness_ID,
            ],
            optional_skills=[
                Smite_Hex_ID,
                Hex_Eater_Signet_ID,
                Castigation_Signet_ID,
                Bane_Signet_ID,
                Breath_of_the_Great_Dwarf_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _get_bar_snapshot(self) -> _KeystoneBarSnapshot:
        player_id = Player.GetAgentID()
        snapshot = _KeystoneBarSnapshot(
            has_symbolic_celerity=Routines.Checks.Effects.HasBuff(player_id, Symbolic_Celerity_ID),
            has_keystone_signet=Routines.Checks.Effects.HasBuff(player_id, Keystone_Signet_ID),
        )

        if not self.IsInAggro():
            return snapshot

        snapshot.enemy_in_spellcast = bool(Routines.Agents.GetNearestEnemy(Range.Spellcast.value))
        snapshot.attacking_enemy_in_spellcast = bool(Routines.Targeting.GetEnemyAttacking(Range.Spellcast.value))
        return snapshot

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            return False

        snapshot = self._get_bar_snapshot()
        player_energy_pct = float(Agent.GetEnergy(Player.GetAgentID()))

        if (yield from self.skills.Monk.SmitingPrayers.Smite_Hex(min_priority=HexRemovalPriority.HIGH)):
            return True

        if snapshot.symbolic_celerity_needed and (yield from self.skills.Mesmer.FastCasting.Symbolic_Celerity()):
            return True

        if self.IsSkillEquipped(Hex_Eater_Signet_ID):
            if (yield from self.skills.Mesmer.InspirationMagic.Hex_Eater_Signet()):
                return True

        if self.IsSkillEquipped(Breath_of_the_Great_Dwarf_ID) and (yield from self.skills.Any.NoAttribute.Breath_of_the_Great_Dwarf()):
            return True

        if not self.IsInAggro():
            return False

        if snapshot.keystone_signet_needed and (yield from self.skills.Mesmer.FastCasting.Keystone_Signet()):
            return True

        if player_energy_pct >= 0.50 and (yield from self.skills.Monk.SmitingPrayers.Smite_Hex(min_priority=HexRemovalPriority.MEDIUM)):
            return True

        if snapshot.enemy_in_spellcast and (yield from self.skills.Mesmer.DominationMagic.Unnatural_Signet()):
            return True

        if snapshot.attacking_enemy_in_spellcast and (yield from self.skills.Mesmer.IllusionMagic.Signet_of_Clumsiness()):
            return True

        if self.IsSkillEquipped(Castigation_Signet_ID) and snapshot.attacking_enemy_in_spellcast and (yield from self.skills.Monk.SmitingPrayers.Castigation_Signet()):
            return True

        if self.IsSkillEquipped(Bane_Signet_ID) and snapshot.attacking_enemy_in_spellcast and (yield from self.skills.Monk.SmitingPrayers.Bane_Signet()):
            return True

        if player_energy_pct >= 0.70 and (yield from self.skills.Monk.SmitingPrayers.Smite_Hex()):
            return True

        return False
