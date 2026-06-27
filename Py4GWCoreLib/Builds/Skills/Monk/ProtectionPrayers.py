from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr

__all__ = ["ProtectionPrayers"]


class ProtectionPrayers:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    def _resolve_precombat_melee_prebuff_target(self, skill_id: int, custom_skill: CustomSkill) -> int:
        """Pre-combat prebuff target for a self/ally enchantment.

        Picks a melee-weapon ally in spellcast range that does not already carry
        this enchantment, so frontliners are protected the moment combat starts
        rather than reactively after the first hits land. Lowest-HP first as a
        stable tiebreak.
        """
        return self.build.ResolveRankedPartyAllyTarget(
            skill_id,
            custom_skill,
            validator=lambda agent_id: (
                Agent.IsMelee(agent_id)
                and not Routines.Checks.Effects.HasBuff(agent_id, skill_id)
            ),
            rank_key=lambda agent_id: Agent.GetHealth(agent_id),
        )

    def _count_conditions(self, agent_id: int) -> int:
        """Number of distinct conditions on an agent.

        Mirrors the Contagion build's detection: the four bitfield-exposed
        conditions plus the remaining condition effect ids, read via
        Routines.Checks.Agents.HasEffect so party-member conditions published as
        shared-memory buffs are counted too.
        """
        detected: set[str] = set()
        for name, has_flag in (
            ("bleeding", Agent.IsBleeding),
            ("crippled", Agent.IsCrippled),
            ("deep_wound", Agent.IsDeepWounded),
            ("poison", Agent.IsPoisoned),
        ):
            if has_flag(agent_id):
                detected.add(name)
        for name, skill_name in (
            ("burning", "Burning"),
            ("disease", "Disease"),
            ("blind", "Blind"),
            ("dazed", "Dazed"),
            ("weakness", "Weakness"),
            ("cracked_armor", "Cracked_Armor"),
            ("bleeding", "Bleeding"),
            ("poison", "Poison"),
            ("crippled", "Crippled"),
            ("deep_wound", "Deep_Wound"),
        ):
            if name in detected:
                continue
            condition_id = Skill.GetID(skill_name)
            if condition_id and Routines.Checks.Agents.HasEffect(agent_id, condition_id):
                detected.add(name)
        return len(detected)

    #region A
    def Aura_of_Faith(self) -> BuildCoroutine:
        aura_of_faith_id: int = Skill.GetID("Aura_of_Faith")
        aura_of_faith: CustomSkill = self.build.GetCustomSkill(aura_of_faith_id)
        sample_interval_ms = 500
        focused_drop_threshold = 0.10
        health_threshold: float = max(0.0, min(1.0, float(aura_of_faith.Conditions.LessLife or 0.75)))

        def _resolve_aura_of_faith_target() -> int:
            return self.build.ResolveRankedPartyAllyTarget(
                aura_of_faith_id,
                aura_of_faith,
                validator=lambda agent_id: (
                    Agent.GetHealth(agent_id) < health_threshold
                    and not Routines.Checks.Effects.HasBuff(agent_id, aura_of_faith_id)
                    and self.build.GetPartyHealthDelta(agent_id) >= focused_drop_threshold
                ),
                rank_key=lambda agent_id: (
                    -self.build.GetPartyHealthDelta(agent_id),
                    Agent.GetHealth(agent_id),
                ),
                sample_interval_ms=sample_interval_ms,
            )

        if not self.build.IsSkillEquipped(aura_of_faith_id):
            return False
        if not self.build.IsInAggro():
            return False

        target_agent_id = _resolve_aura_of_faith_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            aura_of_faith_id,
            target_agent_id,
        ))
    #endregion

    #region D
    def Draw_Conditions(self) -> BuildCoroutine:
        draw_conditions_id: int = Skill.GetID("Draw_Conditions")
        draw_conditions: CustomSkill = self.build.GetCustomSkill(draw_conditions_id)

        def _resolve_draw_conditions_target() -> int:
            return self.build.ResolveAllyTarget(
                draw_conditions_id,
                draw_conditions,
            )

        if not self.build.IsSkillEquipped(draw_conditions_id):
            return False

        target_agent_id = _resolve_draw_conditions_target()
        return (yield from self.build.CastSkillIDAndRestoreTarget(
            draw_conditions_id,
            target_agent_id,
        ))

    def Divert_Hexes(self, *, min_hexes: int = 2) -> BuildCoroutine:
        from Py4GWCoreLib.GlobalCache.HexRemovalPriority import get_hex_skill_ids_on_agent

        divert_hexes_id: int = Skill.GetID("Divert_Hexes")
        divert_hexes: CustomSkill = self.build.GetCustomSkill(divert_hexes_id)

        def _hex_count(agent_id: int) -> int:
            return len(get_hex_skill_ids_on_agent(agent_id) or [])

        def _resolve_divert_hexes_target() -> int:
            return self.build.ResolveRankedPartyAllyTarget(
                divert_hexes_id,
                divert_hexes,
                validator=lambda agent_id: _hex_count(agent_id) >= min_hexes,
                rank_key=lambda agent_id: (
                    -_hex_count(agent_id),
                    Agent.GetHealth(agent_id),
                ),
            )

        if not self.build.IsSkillEquipped(divert_hexes_id):
            return False
        if not self.build.IsInAggro():
            return False

        target_agent_id = _resolve_divert_hexes_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            divert_hexes_id,
            target_agent_id,
        ))
    #endregion

    #region L
    def Life_Sheath(self, *, min_conditions: int = 2) -> BuildCoroutine:
        life_sheath_id: int = Skill.GetID("Life_Sheath")
        life_sheath: CustomSkill = self.build.GetCustomSkill(life_sheath_id)

        def _resolve_life_sheath_target() -> int:
            return self.build.ResolveRankedPartyAllyTarget(
                life_sheath_id,
                life_sheath,
                validator=lambda agent_id: (
                    self._count_conditions(agent_id) >= min_conditions
                    and not Routines.Checks.Effects.HasBuff(agent_id, life_sheath_id)
                ),
                rank_key=lambda agent_id: (
                    -self._count_conditions(agent_id),
                    Agent.GetHealth(agent_id),
                ),
            )

        if not self.build.IsSkillEquipped(life_sheath_id):
            return False
        if not self.build.IsInAggro():
            return False

        target_agent_id = _resolve_life_sheath_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            life_sheath_id,
            target_agent_id,
        ))
    #endregion

    #region P
    def Protective_Spirit(self, *, prebuff_melee_precombat: bool = False) -> BuildCoroutine:
        protective_spirit_id: int = Skill.GetID("Protective_Spirit")
        protective_spirit: CustomSkill = self.build.GetCustomSkill(protective_spirit_id)
        sample_interval_ms = 500
        focused_drop_threshold = 0.10
        health_threshold: float = max(0.0, min(1.0, float(protective_spirit.Conditions.LessLife or 0.80)))

        def _resolve_protective_spirit_target() -> int:
            return self.build.ResolveRankedPartyAllyTarget(
                protective_spirit_id,
                protective_spirit,
                validator=lambda agent_id: (
                    Agent.GetHealth(agent_id) < health_threshold
                    and not Routines.Checks.Effects.HasBuff(agent_id, protective_spirit_id)
                    and self.build.GetPartyHealthDelta(agent_id) >= focused_drop_threshold
                ),
                rank_key=lambda agent_id: (
                    -self.build.GetPartyHealthDelta(agent_id),
                    Agent.GetHealth(agent_id),
                ),
                sample_interval_ms=sample_interval_ms,
            )

        if not self.build.IsSkillEquipped(protective_spirit_id):
            return False

        if self.build.IsInAggro():
            target_agent_id = _resolve_protective_spirit_target()
        elif prebuff_melee_precombat and self.build.IsCloseToAggro():
            # Just before combat: prebuff melee allies so the first spike is
            # already capped instead of reacting to it.
            target_agent_id = self._resolve_precombat_melee_prebuff_target(
                protective_spirit_id, protective_spirit,
            )
        else:
            return False

        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            protective_spirit_id,
            target_agent_id,
        ))
    #endregion

    def Reversal_of_Fortune(self) -> BuildCoroutine:
        reversal_of_fortune_id: int = Skill.GetID("Reversal_of_Fortune")
        reversal_of_fortune: CustomSkill = self.build.GetCustomSkill(reversal_of_fortune_id)
        sample_interval_ms = 500
        focused_drop_threshold = 0.05
        health_threshold: float = max(0.0, min(1.0, float(reversal_of_fortune.Conditions.LessLife or 0.85)))

        def _resolve_reversal_of_fortune_target() -> int:
            def _priority(agent_id: int) -> tuple[int, int, float, float]:
                role_rank = 2
                if Agent.IsMelee(agent_id):
                    role_rank = 0
                elif Agent.IsCaster(agent_id):
                    role_rank = 1

                return (
                    0 if self.build.GetPartyHealthDelta(agent_id) >= focused_drop_threshold else 1,
                    role_rank,
                    Agent.GetHealth(agent_id),
                    -self.build.GetPartyHealthDelta(agent_id),
                )

            return self.build.ResolveRankedPartyAllyTarget(
                reversal_of_fortune_id,
                reversal_of_fortune,
                validator=lambda agent_id: (
                    Agent.GetHealth(agent_id) < health_threshold
                    and not Routines.Checks.Effects.HasBuff(agent_id, reversal_of_fortune_id)
                ),
                rank_key=_priority,
                sample_interval_ms=sample_interval_ms,
            )

        if not self.build.IsSkillEquipped(reversal_of_fortune_id):
            return False
        if not self.build.IsInAggro():
            return False

        target_agent_id = _resolve_reversal_of_fortune_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            reversal_of_fortune_id,
            target_agent_id,
        ))

    def Reverse_Hex(self) -> BuildCoroutine:
        reverse_hex_id: int = Skill.GetID("Reverse_Hex")
        reverse_hex: CustomSkill = self.build.GetCustomSkill(reverse_hex_id)
        sample_interval_ms = 500
        # Reverse Hex removes one hex and reduces the target's next incoming
        # damage (no heal, no per-hex scaling). It is pure hex removal, so it
        # fires on any hexed ally regardless of current health.

        def _resolve_reverse_hex_target() -> int:
            return self.build.ResolveRankedPartyAllyTarget(
                reverse_hex_id,
                reverse_hex,
                validator=lambda agent_id: Routines.Checks.Agents.IsHexed(agent_id),
                rank_key=lambda agent_id: (
                    Agent.GetHealth(agent_id),
                    -self.build.GetPartyHealthDelta(agent_id),
                ),
                sample_interval_ms=sample_interval_ms,
            )

        if not self.build.IsSkillEquipped(reverse_hex_id):
            return False
        if not self.build.IsInAggro():
            return False

        target_agent_id = _resolve_reverse_hex_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            reverse_hex_id,
            target_agent_id,
        ))
    #endregion

    #region S
    def Shield_of_Absorption(self) -> BuildCoroutine:
        shield_of_absorption_id: int = Skill.GetID("Shield_of_Absorption")
        shield_of_absorption: CustomSkill = self.build.GetCustomSkill(shield_of_absorption_id)
        sample_interval_ms = 500
        focused_drop_threshold = 0.10
        health_threshold: float = max(0.0, min(1.0, float(shield_of_absorption.Conditions.LessLife or 0.60)))

        def _resolve_shield_of_absorption_target() -> int:
            return self.build.ResolveRankedPartyAllyTarget(
                shield_of_absorption_id,
                shield_of_absorption,
                validator=lambda agent_id: (
                    Agent.GetHealth(agent_id) < health_threshold
                    and not Routines.Checks.Effects.HasBuff(agent_id, shield_of_absorption_id)
                    and self.build.GetPartyHealthDelta(agent_id) >= focused_drop_threshold
                ),
                rank_key=lambda agent_id: (
                    -self.build.GetPartyHealthDelta(agent_id),
                    Agent.GetHealth(agent_id),
                ),
                sample_interval_ms=sample_interval_ms,
            )

        if not self.build.IsSkillEquipped(shield_of_absorption_id):
            return False
        if not self.build.IsInAggro():
            return False

        target_agent_id = _resolve_shield_of_absorption_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            shield_of_absorption_id,
            target_agent_id,
        ))

    def Spirit_Bond(self) -> BuildCoroutine:
        spirit_bond_id: int = Skill.GetID("Spirit_Bond")
        spirit_bond: CustomSkill = self.build.GetCustomSkill(spirit_bond_id)
        sample_interval_ms = 500
        focused_drop_threshold = 0.10
        health_threshold: float = max(0.0, min(1.0, float(spirit_bond.Conditions.LessLife or 0.70)))

        def _resolve_spirit_bond_target() -> int:
            return self.build.ResolveRankedPartyAllyTarget(
                spirit_bond_id,
                spirit_bond,
                validator=lambda agent_id: (
                    Agent.GetHealth(agent_id) < health_threshold
                    and not Routines.Checks.Effects.HasBuff(agent_id, spirit_bond_id)
                    and self.build.GetPartyHealthDelta(agent_id) >= focused_drop_threshold
                ),
                rank_key=lambda agent_id: (
                    -self.build.GetPartyHealthDelta(agent_id),
                    Agent.GetHealth(agent_id),
                ),
                sample_interval_ms=sample_interval_ms,
            )

        if not self.build.IsSkillEquipped(spirit_bond_id):
            return False
        if not self.build.IsInAggro():
            return False

        target_agent_id = _resolve_spirit_bond_target()
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            spirit_bond_id,
            target_agent_id,
        ))
    #endregion
