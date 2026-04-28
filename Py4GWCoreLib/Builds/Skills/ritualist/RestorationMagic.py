from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import Range, Routines
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill
from HeroAI.types import Skilltarget

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["RestorationMagic"]


class RestorationMagic:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    def _has_spirit_in_earshot(self) -> bool:
        return bool(Routines.Agents.GetNearestSpirit(Range.Earshot.value))

    #region B
    def Breath_of_the_Great_Dwarf(self) -> BuildCoroutine:
        if False:
            yield
        return False
    #endregion

    #region L
    def Life(self) -> BuildCoroutine:
        life_id: int = Skill.GetID("Life")

        if not self.build.IsSkillEquipped(life_id):
            return False

        if not (self.build.IsInAggro() or self.build.IsCloseToAggro()):
            return False

        return (yield from self.build.CastSpiritSkillID(
            skill_id=life_id,
            log=False,
            aftercast_delay=250,
        ))
    #endregion

    #region M
    def Mend_Body_and_Soul(
        self,
        *,
        health_threshold: float | None = None,
        cleanse_blind_martial: bool = False,
        cleanse_cripple_melee: bool = False,
    ) -> BuildCoroutine:
        from HeroAI.targeting import GetAllAlliesArray

        mend_body_and_soul_id: int = Skill.GetID("Mend_Body_and_Soul")
        mend_body_and_soul: CustomSkill = self.build.GetCustomSkill(mend_body_and_soul_id)

        if not self.build.IsSkillEquipped(mend_body_and_soul_id):
            return False

        # Cleanse-oriented tiers: MBaS removes one condition per cast only when a
        # spirit is in earshot, so gate the tier on the spirit + profession-specific
        # carriers of the targeted condition.
        if cleanse_blind_martial or cleanse_cripple_melee:
            if not self._has_spirit_in_earshot():
                return False

            if cleanse_blind_martial:
                blind_skill_id: int = Skill.GetID("Blind")
                profession_predicate = lambda aid: Routines.Checks.Agents.IsMartial(aid)
                condition_predicate = lambda aid: Routines.Checks.Agents.HasEffect(aid, blind_skill_id)
            else:
                profession_predicate = lambda aid: Routines.Checks.Agents.IsMelee(aid)
                condition_predicate = lambda aid: Agent.IsCrippled(aid)

            ally_array = GetAllAlliesArray(Range.Spellcast.value) or []
            candidates = [
                agent_id for agent_id in ally_array
                if Agent.IsValid(agent_id)
                and Agent.IsAlive(agent_id)
                and profession_predicate(agent_id)
                and condition_predicate(agent_id)
            ]
            if not candidates:
                return False

            candidates.sort(key=lambda aid: Agent.GetHealth(aid))
            target_agent_id = candidates[0]
        else:
            # HP-threshold tier: caller overrides the metadata's LessLife when it
            # wants a specific tier (emergency, damaged, preventive) rather than
            # the bar-wide default. When None, fall back to metadata (0.70 default).
            threshold: float = (
                health_threshold
                if health_threshold is not None
                else float(mend_body_and_soul.Conditions.LessLife or 0.70)
            )
            threshold = max(0.0, min(1.0, threshold))

            def _resolve_mend_body_and_soul_target() -> int:
                variants: list = [None]
                if self._has_spirit_in_earshot():
                    variants = [
                        lambda custom_skill: setattr(custom_skill.Conditions, "HasCondition", True),
                        None,
                    ]

                return self.build.ResolvePreferredAllyTarget(
                    mend_body_and_soul_id,
                    mend_body_and_soul,
                    variants=variants,
                    validator=lambda aid: Agent.IsAlive(aid) and Agent.GetHealth(aid) < threshold,
                )

            target_agent_id = _resolve_mend_body_and_soul_target()

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            mend_body_and_soul_id,
            target_agent_id,
        ))

    def Mending_Grip(self) -> BuildCoroutine:
        mending_grip_id: int = Skill.GetID("Mending_Grip")
        mending_grip: CustomSkill = self.build.GetCustomSkill(mending_grip_id)
        health_threshold: float = max(0.0, min(1.0, float(mending_grip.Conditions.LessLife or 0.80)))

        def _resolve_mending_grip_target() -> int:
            def _clear_priority_conditions(custom_skill: CustomSkill) -> None:
                custom_skill.Conditions.HasWeaponSpell = False
                custom_skill.Conditions.HasCondition = False

            return self.build.ResolvePreferredAllyTarget(
                mending_grip_id,
                mending_grip,
                variants=[
                    None,
                    _clear_priority_conditions,
                ],
                validator=lambda agent_id: Agent.IsAlive(agent_id) and Agent.GetHealth(agent_id) < health_threshold,
            )

        if not self.build.IsSkillEquipped(mending_grip_id):
            return False

        target_agent_id = _resolve_mending_grip_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            mending_grip_id,
            target_agent_id,
        ))
    #endregion

    #region X
    def Xinraes_Weapon(self) -> BuildCoroutine:
        from HeroAI.targeting import TargetAllyWeaponSpell

        xinraes_weapon_id: int = Skill.GetID("Xinraes_Weapon")

        if not self.build.IsSkillEquipped(xinraes_weapon_id):
            return False

        target_agent_id = TargetAllyWeaponSpell(xinraes_weapon_id, Range.Spellcast.value)
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            xinraes_weapon_id,
            target_agent_id,
        ))
    #endregion

    #region R
    def Recovery(self) -> BuildCoroutine:
        recovery_id: int = Skill.GetID("Recovery")

        if not self.build.IsSkillEquipped(recovery_id):
            return False

        return (yield from self.build.CastSpiritSkillID(
            skill_id=recovery_id,
            log=False,
            aftercast_delay=250,
        ))

    def Recuperation(
        self,
        *,
        min_degen_count: int = 0,
        min_party_damaged_count: int = 0,
    ) -> BuildCoroutine:
        recuperation_id: int = Skill.GetID("Recuperation")

        if not self.build.IsSkillEquipped(recuperation_id):
            return False

        # State gate: only fire during active combat or the approach phase - never
        # during pure downtime.
        if not (self.build.IsInAggro() or self.build.IsCloseToAggro()):
            return False

        # Independent situational gates. Callers that want OR semantics across
        # gates should call Recuperation twice (once per gate) so the "OR" is
        # explicit in the priority chain.
        #   `min_degen_count`         - N allies in Spirit range suffering any
        #                               health-degen source (poison / bleeding /
        #                               burning / degen hex).
        #   `min_party_damaged_count` - N allies in Spirit range below 75% HP.
        # HP-aware recast (spirit at < 20% HP) is enforced by
        # BuildMgr.SpiritBuffExists via the Recuperation custom-skill metadata
        # (Conditions.AllowRecastAtLife = 0.20).
        if min_degen_count > 0:
            if self._count_allies_suffering_degen() < min_degen_count:
                return False

        if min_party_damaged_count > 0:
            if not self._is_party_damaged(
                within_range=Range.Spirit.value,
                min_allies_count=min_party_damaged_count,
                less_health_than_percent=0.75,
            ):
                return False

        return (yield from self.build.CastSpiritSkillID(
            skill_id=recuperation_id,
            log=False,
            aftercast_delay=250,
        ))

    @staticmethod
    def _is_suffering_degen(agent_id: int, burning_skill_id: int) -> bool:
        """Check if an ally has any health-degen condition: poison (-4),
        bleeding (-3), burning (-7), or a degen hex."""
        from Py4GWCoreLib.Effect import Effects
        if Agent.IsPoisoned(agent_id):
            return True
        if Agent.IsBleeding(agent_id):
            return True
        if Agent.IsDegenHexed(agent_id):
            return True
        if Effects.HasEffect(agent_id, burning_skill_id):
            return True
        return False

    def _count_allies_suffering_degen(self) -> int:
        """Count party allies in Spirit range suffering any health-degen source."""
        from Py4GWCoreLib import AgentArray, GLOBAL_CACHE

        ally_ids = AgentArray.GetAllyArray()
        ally_ids = AgentArray.Filter.ByDistance(ally_ids, Player.GetXY(), Range.Spirit.value)
        ally_ids = AgentArray.Filter.ByCondition(ally_ids, lambda aid: Agent.IsAlive(aid))

        burning_skill_id = GLOBAL_CACHE.Skill.GetID("Burning")
        count = 0
        for aid in ally_ids:
            if self._is_suffering_degen(aid, burning_skill_id):
                count += 1
        return count

    @staticmethod
    def _is_party_damaged(
        within_range: float,
        min_allies_count: int,
        less_health_than_percent: float,
    ) -> bool:
        """Return True when at least `min_allies_count` allies within range are
        alive and currently below `less_health_than_percent` HP (0.0-1.0). Short
        -circuits as soon as the threshold is reached."""
        from Py4GWCoreLib import AgentArray

        ally_ids = AgentArray.GetAllyArray()
        ally_ids = AgentArray.Filter.ByDistance(ally_ids, Player.GetXY(), within_range)
        ally_ids = AgentArray.Filter.ByCondition(ally_ids, lambda aid: Agent.IsAlive(aid))

        count = 0
        for aid in ally_ids:
            if Agent.GetHealth(aid) < less_health_than_percent:
                count += 1
                if count >= min_allies_count:
                    return True
        return False
    #endregion

    #region S
    def Spirit_Light(
        self,
        *,
        health_threshold: float | None = None,
    ) -> BuildCoroutine:
        spirit_light_id: int = Skill.GetID("Spirit_Light")
        spirit_light: CustomSkill = self.build.GetCustomSkill(spirit_light_id)
        threshold: float = (
            health_threshold
            if health_threshold is not None
            else float(spirit_light.Conditions.LessLife or 0.60)
        )
        threshold = max(0.0, min(1.0, threshold))

        def _can_safely_cast_spirit_light() -> bool:
            return (
                self._has_spirit_in_earshot()
                or Agent.GetHealth(Player.GetAgentID()) > spirit_light.Conditions.SacrificeHealth
            )

        def _resolve_spirit_light_target() -> int:
            if self._has_spirit_in_earshot():
                return self.build.ResolvePreferredAllyTarget(
                    spirit_light_id,
                    spirit_light,
                    validator=lambda agent_id: Agent.IsAlive(agent_id) and Agent.GetHealth(agent_id) < threshold,
                )

            other_ally_skill = deepcopy(spirit_light)
            other_ally_skill.TargetAllegiance = Skilltarget.OtherAlly.value
            return self.build.ResolvePreferredAllyTarget(
                spirit_light_id,
                other_ally_skill,
                validator=lambda agent_id: (
                    Agent.IsAlive(agent_id)
                    and agent_id != Player.GetAgentID()
                    and Agent.GetHealth(agent_id) < threshold
                ),
            )

        if not self.build.IsSkillEquipped(spirit_light_id):
            return False
        if not _can_safely_cast_spirit_light():
            return False

        target_agent_id = _resolve_spirit_light_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            spirit_light_id,
            target_agent_id,
            extra_condition=_can_safely_cast_spirit_light,
        ))

    def Spirit_Transfer(
        self,
        *,
        health_threshold: float | None = None,
    ) -> BuildCoroutine:
        spirit_transfer_id: int = Skill.GetID("Spirit_Transfer")
        spirit_transfer: CustomSkill = self.build.GetCustomSkill(spirit_transfer_id)
        threshold: float = (
            health_threshold
            if health_threshold is not None
            else float(spirit_transfer.Conditions.LessLife or 0.50)
        )
        threshold = max(0.0, min(1.0, threshold))

        def _resolve_spirit_transfer_target() -> int:
            if not Routines.Agents.GetNearestSpirit(Range.Spellcast.value):
                return 0

            return self.build.ResolvePreferredAllyTarget(
                spirit_transfer_id,
                spirit_transfer,
                validator=lambda agent_id: Agent.IsAlive(agent_id) and Agent.GetHealth(agent_id) < threshold,
            )

        if not self.build.IsSkillEquipped(spirit_transfer_id):
            return False

        target_agent_id = _resolve_spirit_transfer_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            spirit_transfer_id,
            target_agent_id,
        ))
    #endregion

    #region W
    def Wielders_Boon(self) -> BuildCoroutine:
        wielders_boon_id: int = Skill.GetID("Wielders_Boon")
        wielders_boon: CustomSkill = self.build.GetCustomSkill(wielders_boon_id)
        health_threshold: float = max(0.0, min(1.0, float(wielders_boon.Conditions.LessLife or 0.70)))

        def _resolve_wielders_boon_target() -> int:
            return self.build.ResolvePreferredAllyTarget(
                wielders_boon_id,
                wielders_boon,
                variants=[
                    None,
                    lambda custom_skill: setattr(custom_skill.Conditions, "HasWeaponSpell", False),
                ],
                validator=lambda agent_id: Agent.IsAlive(agent_id) and Agent.GetHealth(agent_id) < health_threshold,
            )

        if not self.build.IsSkillEquipped(wielders_boon_id):
            return False

        target_agent_id = _resolve_wielders_boon_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            wielders_boon_id,
            target_agent_id,
        ))
    #endregion
