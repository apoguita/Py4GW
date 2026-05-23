from dataclasses import dataclass

from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import Range
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import HexRemovalPriority, SkillsTemplate
from HeroAI.targeting import GetAllAlliesArray
from HeroAI.types import Skilltarget


Healing_Burst_ID = Skill.GetID("Healing_Burst")
Dwaynas_Kiss_ID = Skill.GetID("Dwaynas_Kiss")
Seed_of_Life_ID = Skill.GetID("Seed_of_Life")
Draw_Conditions_ID = Skill.GetID("Draw_Conditions")
Vigorous_Spirit_ID = Skill.GetID("Vigorous_Spirit")
Remove_Hex_ID = Skill.GetID("Remove_Hex")
Cure_Hex_ID = Skill.GetID("Cure_Hex")


@dataclass(slots=True)
class _RequiredSupportSnapshot:
    healing_burst_needed: bool = False
    dwaynas_kiss_needed: bool = False
    seed_of_life_needed: bool = False
    draw_conditions_needed: bool = False

    @property
    def any_required_support_needed(self) -> bool:
        return (
            self.healing_burst_needed
            or self.dwaynas_kiss_needed
            or self.seed_of_life_needed
            or self.draw_conditions_needed
        )


class Healing_Burst(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Healing Burst",
            required_primary=Profession.Monk,
            template_code="OwUUMoG/CoSeRbE5g3EAAAAAAAAA",
            required_skills=[
                Healing_Burst_ID,
                Dwaynas_Kiss_ID,
                Seed_of_Life_ID,
                Draw_Conditions_ID,
            ],
            optional_skills=[
                Vigorous_Spirit_ID,
                Remove_Hex_ID,
                Cure_Hex_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _get_required_support_snapshot(self) -> _RequiredSupportSnapshot:
        healing_burst = self.GetEquippedCustomSkill(Healing_Burst_ID)
        dwaynas_kiss = self.GetEquippedCustomSkill(Dwaynas_Kiss_ID)
        seed_of_life = self.GetEquippedCustomSkill(Seed_of_Life_ID)
        draw_conditions = self.GetEquippedCustomSkill(Draw_Conditions_ID)

        required_skills = [
            skill
            for skill in (healing_burst, dwaynas_kiss, seed_of_life, draw_conditions)
            if skill is not None
        ]
        snapshot = _RequiredSupportSnapshot()
        if not required_skills:
            return snapshot

        player_id = Player.GetAgentID()
        party_area = max(
            (
                int(skill.Conditions.PartyWideArea)
                for skill in required_skills
                if skill.Conditions.IsPartyWide and skill.Conditions.PartyWideArea
            ),
            default=Range.SafeCompass.value,
        )
        ally_array = list(GetAllAlliesArray(party_area) or [])
        if not ally_array:
            return snapshot

        healing_burst_threshold = (
            float(healing_burst.Conditions.LessLife)
            if healing_burst is not None and healing_burst.Conditions.LessLife > 0
            else 0.0
        )
        dwaynas_kiss_threshold = (
            float(dwaynas_kiss.Conditions.LessLife)
            if dwaynas_kiss is not None and dwaynas_kiss.Conditions.LessLife > 0
            else 0.0
        )
        seed_of_life_threshold = (
            float(seed_of_life.Conditions.LessLife)
            if seed_of_life is not None and seed_of_life.Conditions.LessLife > 0
            else 0.0
        )
        max_any_ally_heal_threshold = healing_burst_threshold
        max_other_ally_heal_threshold = max(dwaynas_kiss_threshold, seed_of_life_threshold)
        needs_seed_party_average = bool(
            seed_of_life is not None
            and seed_of_life.Conditions.IsPartyWide
            and seed_of_life_threshold > 0
        )

        alive_count = 0
        total_health = 0.0

        for agent_id in ally_array:
            if not Routines.Checks.Agents.IsAlive(agent_id):
                continue

            health = float(Routines.Checks.Agents.GetHealth(agent_id))
            is_other_ally = agent_id != player_id

            alive_count += 1
            total_health += health

            if not snapshot.healing_burst_needed and max_any_ally_heal_threshold > 0:
                if health <= max_any_ally_heal_threshold:
                    snapshot.healing_burst_needed = True

            if is_other_ally and max_other_ally_heal_threshold > 0 and health <= max_other_ally_heal_threshold:
                if not snapshot.dwaynas_kiss_needed and dwaynas_kiss_threshold > 0 and health <= dwaynas_kiss_threshold:
                    snapshot.dwaynas_kiss_needed = True

                if not snapshot.seed_of_life_needed and seed_of_life_threshold > 0 and health <= seed_of_life_threshold:
                    snapshot.seed_of_life_needed = True

            if (
                is_other_ally
                and not snapshot.draw_conditions_needed
                and draw_conditions is not None
                and draw_conditions.Conditions.HasCondition
            ):
                if Routines.Checks.Agents.IsConditioned(agent_id):
                    snapshot.draw_conditions_needed = True

            if (
                snapshot.healing_burst_needed
                and snapshot.dwaynas_kiss_needed
                and snapshot.draw_conditions_needed
                and (not needs_seed_party_average or snapshot.seed_of_life_needed is False)
            ):
                if not needs_seed_party_average:
                    return snapshot

        if (
            needs_seed_party_average
            and alive_count > 0
        ):
            average_group_life = total_health / alive_count
            snapshot.seed_of_life_needed = (
                snapshot.seed_of_life_needed
                and average_group_life <= seed_of_life.Conditions.LessLife if seed_of_life is not None else False
            )

        return snapshot

    def _run_local_skill_logic(self):
        if not Routines.Checks.Skills.CanCast():
            return False

        support_snapshot = self._get_required_support_snapshot()
        if not support_snapshot.any_required_support_needed:
            return False

        player_energy_pct = float(Agent.GetEnergy(Player.GetAgentID()))

        if support_snapshot.healing_burst_needed and (yield from self.skills.Monk.HealingPrayers.Healing_Burst()):
            return True

        if (yield from self.skills.Monk.NoAttribute.Remove_Hex(min_priority=HexRemovalPriority.HIGH)):
            return True

        if (yield from self.skills.Monk.HealingPrayers.Cure_Hex(min_priority=HexRemovalPriority.HIGH)):
            return True

        if support_snapshot.dwaynas_kiss_needed and (yield from self.skills.Monk.HealingPrayers.Dwaynas_Kiss()):
            return True

        if support_snapshot.seed_of_life_needed and (yield from self.skills.Monk.NoAttribute.Seed_of_Life()):
            return True

        if player_energy_pct >= 0.50 and (yield from self.skills.Monk.NoAttribute.Remove_Hex(min_priority=HexRemovalPriority.MEDIUM)):
            return True

        if player_energy_pct >= 0.50 and (yield from self.skills.Monk.HealingPrayers.Cure_Hex(min_priority=HexRemovalPriority.MEDIUM)):
            return True

        if support_snapshot.draw_conditions_needed and (yield from self.skills.Monk.ProtectionPrayers.Draw_Conditions()):
            return True

        if player_energy_pct >= 0.70 and (yield from self.skills.Monk.NoAttribute.Remove_Hex()):
            return True

        if player_energy_pct >= 0.70 and (yield from self.skills.Monk.HealingPrayers.Cure_Hex()):
            return True

        if not (self.IsInAggro()):
            return False

        if self.IsSkillEquipped(Vigorous_Spirit_ID) and (yield from self.skills.Monk.HealingPrayers.Vigorous_Spirit()):
            return True

        return False
