from Py4GWCoreLib import Profession
from Py4GWCoreLib import Routines
from Py4GWCoreLib.enums_src.GameData_enums import Profession as ProfessionEnum
from Py4GWCoreLib import Range
from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Effect import Effects
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Infuse_Health_ID = Skill.GetID("Infuse_Health")
Spirit_Bond_ID = Skill.GetID("Spirit_Bond")
Life_Attunement_ID = Skill.GetID("Life_Attunement")
Protective_Bond_ID = Skill.GetID("Protective_Bond")
Ether_Renewal_ID = Skill.GetID("Ether_Renewal")
Aura_of_Restoration_ID = Skill.GetID("Aura_of_Restoration")

Life_Bond_ID = Skill.GetID("Life_Bond")
Great_Dwarf_Weapon_ID = Skill.GetID("Great_Dwarf_Weapon")
Reversal_of_Fortune_ID = Skill.GetID("Reversal_of_Fortune")
Shield_of_Absorption_ID = Skill.GetID("Shield_of_Absorption")
Protective_Spirit_ID = Skill.GetID("Protective_Spirit")
Vigorous_Spirit_ID = Skill.GetID("Vigorous_Spirit")
Draw_Conditions_ID = Skill.GetID("Draw_Conditions")


class Ether_Renewal_Bonder(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Ether Renewal Bonder",
            required_primary=Profession.Elementalist,
            required_secondary=Profession.Monk,
            template_code="",
            required_skills=[
                Life_Attunement_ID,
                Protective_Bond_ID,
                Ether_Renewal_ID,
                Aura_of_Restoration_ID,
            ],
            optional_skills=[
                Infuse_Health_ID,
                Spirit_Bond_ID,
                Life_Bond_ID,
                Great_Dwarf_Weapon_ID,
                Reversal_of_Fortune_ID,
                Shield_of_Absorption_ID,
                Protective_Spirit_ID,
                Vigorous_Spirit_ID,
                Draw_Conditions_ID,
            ],
        )

        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)

    def _has_maintained_buff(self, target_agent_id: int, skill_id: int) -> bool:
        """
        Check if the player is maintaining skill_id on target_agent_id.
        Maintained enchantments live in the caster's (player's) buff list,
        so we filter by both skill_id and target_agent_id.
        """
        buff_list = Effects.GetBuffs(Player.GetAgentID())
        return any(b.skill_id == skill_id and b.target_agent_id == target_agent_id for b in buff_list)

    def _self_enchantment_upkeep(self, skill_id: int) -> BuildCoroutine:
        player_agent_id = Player.GetAgentID()
        not_has_enchantment = lambda: not self._has_maintained_buff(player_agent_id, skill_id)

        if not self.IsSkillEquipped(skill_id):
            return False
        if not not_has_enchantment():
            return False

        return (yield from self.CastSkillID(
            skill_id=skill_id,
            target_agent_id=player_agent_id,
            extra_condition=not_has_enchantment,
            log=False,
            aftercast_delay=250,
        ))

    def _is_necro_rit(self, agent_id: int) -> bool:
        """Returns True only for exact N/Rit (Necromancer primary, Ritualist secondary)."""
        primary, secondary = Agent.GetProfessions(agent_id)
        return primary == ProfessionEnum.Necromancer.value and secondary == ProfessionEnum.Ritualist.value

    def _life_attunement_upkeep(self) -> BuildCoroutine:
        """
        Keep Life Attunement on self and on party members with N or Rt profession.
        """
        if not self.IsSkillEquipped(Life_Attunement_ID):
            return False

        # Self first.
        if (yield from self._self_enchantment_upkeep(Life_Attunement_ID)):
            return True

        # Then N/Rit party members without the buff.
        player_agent_id = Player.GetAgentID()
        ally_array = list(Routines.Targeting.GetAllAlliesArray(Range.Spellcast.value) or [])
        for ally_agent_id in ally_array:
            if ally_agent_id == player_agent_id:
                continue
            if not Routines.Party.IsPartyMember(ally_agent_id):
                continue
            if not self._is_necro_rit(ally_agent_id):
                continue
            if self._has_maintained_buff(ally_agent_id, Life_Attunement_ID):
                continue

            missing_la = lambda aid=ally_agent_id: not self._has_maintained_buff(aid, Life_Attunement_ID)
            if (yield from self.CastSkillIDAndRestoreTarget(
                skill_id=Life_Attunement_ID,
                target_agent_id=ally_agent_id,
                extra_condition=missing_la,
                log=False,
                aftercast_delay=250,
            )):
                return True

        return False

    _BOND_SKILL_IDS = (Life_Attunement_ID, Protective_Bond_ID, Life_Bond_ID)

    def _drop_all_bonds(self) -> bool:
        """
        Drop every active bond maintained enchantment when energy is critically low (< 5).
        Returns True if at least one buff was dropped.
        """
        player_agent_id = Player.GetAgentID()
        actual_energy = Agent.GetEnergy(player_agent_id) * Agent.GetMaxEnergy(player_agent_id)
        if actual_energy >= 5:
            return False

        buff_list = Effects.GetBuffs(player_agent_id)
        dropped_any = False
        for buff in buff_list:
            if buff.skill_id in Ether_Renewal_Bonder._BOND_SKILL_IDS:
                Effects.DropBuff(buff.buff_id)
                dropped_any = True

        return dropped_any

    _MAX_BONDS = 10

    def _can_cast_more_bonds(self) -> bool:
        """Return True when the number of active maintained bonds is below the allowed maximum."""
        buff_list = Effects.GetBuffs(Player.GetAgentID())
        active = sum(1 for b in buff_list if b.skill_id in Ether_Renewal_Bonder._BOND_SKILL_IDS)
        return active < Ether_Renewal_Bonder._MAX_BONDS

    def _bond_party_upkeep(self, skill_id: int) -> BuildCoroutine:
        """
        Maintain a maintained enchantment (bond) on all party teammates (excluding self).
        """
        if not self.IsSkillEquipped(skill_id):
            return False

        player_agent_id = Player.GetAgentID()
        ally_array = list(Routines.Targeting.GetAllAlliesArray(Range.Spellcast.value) or [])

        for ally_agent_id in ally_array:
            if ally_agent_id == player_agent_id:
                continue
            if not Routines.Party.IsPartyMember(ally_agent_id):
                continue
            if self._has_maintained_buff(ally_agent_id, skill_id):
                continue

            missing_bond = lambda aid=ally_agent_id, sid=skill_id: not self._has_maintained_buff(aid, sid)
            if (yield from self.CastSkillIDAndRestoreTarget(
                skill_id=skill_id,
                target_agent_id=ally_agent_id,
                extra_condition=missing_bond,
                log=False,
                aftercast_delay=250,
            )):
                return True

        return False

    def _infuse_health_support(self) -> BuildCoroutine:
        """
        Cast Infuse Health on the lowest-HP party member below 70% health.
        """
        if not self.IsSkillEquipped(Infuse_Health_ID):
            return False

        player_agent_id = Player.GetAgentID()
        ally_array = list(Routines.Targeting.GetAllAlliesArray(Range.Spellcast.value) or [])
        candidates = [
            aid for aid in ally_array
            if aid != player_agent_id
            and Routines.Party.IsPartyMember(aid)
            and Agent.IsAlive(aid)
            and Agent.GetHealth(aid) < 0.70
        ]
        if not candidates:
            return False

        target_agent_id = min(candidates, key=lambda aid: Agent.GetHealth(aid))
        return (yield from self.CastSkillIDAndRestoreTarget(
            skill_id=Infuse_Health_ID,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    def _energy_recovery(self) -> BuildCoroutine:
        """
        Energy recovery mode: spam Spirit Bond and Reversal of Fortune on self
        to trigger Ether Renewal's energy gain.

        Activates when energy drops below 70% AND either:
        - not in aggro, or
        - all party members are at full health.
        """
        player_agent_id = Player.GetAgentID()

        energy_low = Agent.GetEnergy(player_agent_id) < 0.70
        health_low = Agent.GetHealth(player_agent_id) < 0.60
        if not energy_low and not health_low:
            return False

        if self.IsInAggro():
            ally_array = list(Routines.Targeting.GetAllAlliesArray(Range.Spellcast.value) or [])
            all_full = all(
                Agent.GetHealth(aid) >= 1.0
                for aid in ally_array
                if Routines.Party.IsPartyMember(aid) and aid != player_agent_id
            )
            if not all_full:
                return False

        # Prioritize missing buffs first, then spam regardless of buff status.
        for skill_id in (Spirit_Bond_ID, Reversal_of_Fortune_ID):
            if not self.IsSkillEquipped(skill_id):
                continue
            if not Routines.Checks.Effects.HasBuff(player_agent_id, skill_id):
                if (yield from self.CastSkillID(
                    skill_id=skill_id,
                    target_agent_id=player_agent_id,
                    log=False,
                    aftercast_delay=250,
                )):
                    return True

        for skill_id in (Spirit_Bond_ID, Reversal_of_Fortune_ID):
            if not self.IsSkillEquipped(skill_id):
                continue
            if (yield from self.CastSkillID(
                skill_id=skill_id,
                target_agent_id=player_agent_id,
                log=False,
                aftercast_delay=250,
            )):
                return True

        return False

    def _cast_on_damaged_allies(self, skill_id: int, health_threshold: float) -> BuildCoroutine:
        """
        Cast skill on the lowest-HP party member below health_threshold
        who doesn't already have the buff. Combat only.
        """
        if not self.IsSkillEquipped(skill_id):
            return False
        if not self.IsInAggro():
            return False

        player_agent_id = Player.GetAgentID()
        ally_array = list(Routines.Targeting.GetAllAlliesArray(Range.Spellcast.value) or [])
        candidates = [
            aid for aid in ally_array
            if Routines.Party.IsPartyMember(aid)
            and Agent.IsAlive(aid)
            and Agent.GetHealth(aid) < health_threshold
            and not Routines.Checks.Effects.HasBuff(aid, skill_id)
        ]
        if not candidates:
            return False

        target_agent_id = min(candidates, key=lambda aid: Agent.GetHealth(aid))
        return (yield from self.CastSkillIDAndRestoreTarget(
            skill_id=skill_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    def _run_local_skill_logic(self) -> BuildCoroutine:
        if not Routines.Checks.Skills.CanCast():
            return False

        # Emergency: drop all bonds when energy is critically low (< 5 mana).
        if self._drop_all_bonds():
            return True

        # Hard priority: always reapply Ether Renewal first when missing.
        if (yield from self.skills.Elementalist.EnergyStorage.Ether_Renewal()):
            return True

        # All further spells require Ether Renewal to be active.
        if not Routines.Checks.Effects.HasBuff(Player.GetAgentID(), Ether_Renewal_ID):
            return False

        # Second highest priority: heal any party member below 70% HP.
        if (yield from self._infuse_health_support()):
            return True

        # Shield of Absorption on allies below 70% HP (combat only).
        if (yield from self._cast_on_damaged_allies(Shield_of_Absorption_ID, 0.70)):
            return True

        # Spirit Bond and Reversal of Fortune on allies below 90% HP (combat only).
        if (yield from self._cast_on_damaged_allies(Spirit_Bond_ID, 0.90)):
            return True

        if (yield from self._cast_on_damaged_allies(Reversal_of_Fortune_ID, 0.90)):
            return True

        # Keep Aura of Restoration up in and out of combat.
        if (yield from self.skills.Elementalist.EnergyStorage.Aura_of_Restoration()):
            return True

        # Bond upkeep: only cast when energy regen > -10 pips.
        if self._can_cast_more_bonds():
            if (yield from self._life_attunement_upkeep()):
                return True

            if (yield from self._self_enchantment_upkeep(Protective_Bond_ID)):
                return True

            if (yield from self._bond_party_upkeep(Protective_Bond_ID)):
                return True

            if (yield from self._bond_party_upkeep(Life_Bond_ID)):
                return True

        if (yield from self._energy_recovery()):
            return True

        if not self.IsInAggro():
            return False

        self.UpdatePartyHealthMonitor(sample_interval_ms=150)

        if self.IsSkillEquipped(Draw_Conditions_ID) and (yield from self.skills.Monk.ProtectionPrayers.Draw_Conditions()):
            return True

        if self.IsSkillEquipped(Great_Dwarf_Weapon_ID) and (yield from self.skills.Any.NoAttribute.Great_Dwarf_Weapon()):
            return True

        if self.IsSkillEquipped(Protective_Spirit_ID) and (yield from self.skills.Monk.ProtectionPrayers.Protective_Spirit()):
            return True

        if self.IsSkillEquipped(Vigorous_Spirit_ID) and (yield from self.skills.Monk.HealingPrayers.Vigorous_Spirit()):
            return True

        return False
