from Py4GWCoreLib import BuildMgr, Profession, Range, Routines
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


# Required
SIGNET_OF_LOST_SOULS_ID = Skill.GetID("Signet_of_Lost_Souls")
SPIRIT_BOND_ID = Skill.GetID("Spirit_Bond")
PROTECTIVE_SPIRIT_ID = Skill.GetID("Protective_Spirit")
REVERSE_HEX_ID = Skill.GetID("Reverse_Hex")

# Optional
MARTYR_ID = Skill.GetID("Martyr")
REVERSAL_OF_FORTUNE_ID = Skill.GetID("Reversal_of_Fortune")
SHIELD_OF_ABSORPTION_ID = Skill.GetID("Shield_of_Absorption")

# Caster-energy ceiling for the Signet of Lost Souls energy engine: only fire
# while own energy is strictly below 60%.
SIGNET_ENERGY_CEILING = 0.60

# Minimum number of conditioned allies (excluding self) required before Martyr
# pulls every nearby party member's conditions onto the caster.
MARTYR_CONDITION_ALLY_THRESHOLD = 3


class Necro_Prot(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Necro Prot",
            required_primary=Profession.Necromancer,
            required_secondary=Profession.Monk,
            template_code="OANCY5vjKpqKAmJQt7qWseA",
            required_skills=[
                SIGNET_OF_LOST_SOULS_ID,
                SPIRIT_BOND_ID,
                PROTECTIVE_SPIRIT_ID,
                REVERSE_HEX_ID,
            ],
            optional_skills=[
                MARTYR_ID,
                REVERSAL_OF_FORTUNE_ID,
                SHIELD_OF_ABSORPTION_ID,
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

        # Sample party health at 150 ms so the reactive prots (Spirit Bond /
        # Shield of Absorption / Protective Spirit) see spikes promptly; the
        # prot helpers read GetPartyHealthDelta off this monitor.
        self.UpdatePartyHealthMonitor(sample_interval_ms=150)

        # Priority 1: Martyr — pull all conditions onto the caster when at least
        # three nearby allies are conditioned (local build logic).
        if self.IsSkillEquipped(MARTYR_ID) and (yield from self._martyr()):
            return True

        # Signet of Lost Souls as the energy/HP engine: fire only while the
        # caster's own energy is below 60% and a foe under 50% HP is in
        # spellcast range (the foe gate lives inside the helper).
        if (yield from self.skills.Necromancer.SoulReaping.Signet_of_Lost_Souls(
            max_self_energy_pct=SIGNET_ENERGY_CEILING,
        )):
            return True

        # Reactive protection. Every helper below gates on aggro and resolves
        # its own party-ally target (lowest-HP / most-spiked first). Protective
        # Spirit additionally prebuffs melee allies the moment combat is
        # imminent (close to aggro) so the opening spike is already capped.
        if (yield from self.skills.Monk.ProtectionPrayers.Spirit_Bond()):
            return True

        if (yield from self.skills.Monk.ProtectionPrayers.Protective_Spirit(prebuff_melee_precombat=True)):
            return True

        if self.IsSkillEquipped(SHIELD_OF_ABSORPTION_ID) and (
            yield from self.skills.Monk.ProtectionPrayers.Shield_of_Absorption()
        ):
            return True

        if (yield from self.skills.Monk.ProtectionPrayers.Reverse_Hex()):
            return True

        if self.IsSkillEquipped(REVERSAL_OF_FORTUNE_ID) and (
            yield from self.skills.Monk.ProtectionPrayers.Reversal_of_Fortune()
        ):
            return True

        return False

    def _martyr(self):
        """Martyr at top priority: cleanse the party once at least three other
        allies carry a condition.

        Counts conditioned allies (excluding the caster) within spellcast range.
        When the threshold is met, Martyr is cast targeting the most endangered
        (lowest-HP) conditioned ally; the skill still pulls the conditions off
        every nearby party member onto the caster.
        """
        if not self.IsInAggro():
            return False

        player_pos = Player.GetXY()
        allies = Routines.Agents.GetFilteredAllyArray(
            player_pos[0],
            player_pos[1],
            Range.Spellcast.value,
            other_ally=True,
        )
        conditioned = [
            ally_id
            for ally_id in (allies or [])
            if Agent.IsAlive(ally_id) and Agent.IsConditioned(ally_id)
        ]
        if len(conditioned) < MARTYR_CONDITION_ALLY_THRESHOLD:
            return False

        target_agent_id = min(conditioned, key=lambda ally_id: Agent.GetHealth(ally_id))

        return (yield from self.CastSkillIDAndRestoreTarget(
            skill_id=MARTYR_ID,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
