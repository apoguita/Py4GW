from __future__ import annotations

from typing import TYPE_CHECKING

from Py4GWCoreLib.BuildMgr import BuildCoroutine
from Py4GWCoreLib.Skill import Skill

if TYPE_CHECKING:
    from HeroAI.custom_skill_src.skill_types import CustomSkill
    from Py4GWCoreLib.BuildMgr import BuildMgr


class InspirationMagic:
    def __init__(self, build: BuildMgr) -> None:
        self.build: BuildMgr = build

    def Hex_Eater_Signet(self) -> BuildCoroutine:
        hex_eater_signet_id: int = Skill.GetID("Hex_Eater_Signet")

        if not self.build.IsSkillEquipped(hex_eater_signet_id):
            return False

        hex_eater_signet: CustomSkill = self.build.GetCustomSkill(hex_eater_signet_id)
        target_agent_id = self.build.ResolveAllyTarget(
            hex_eater_signet_id,
            hex_eater_signet,
        )
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            hex_eater_signet_id,
            target_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    def Drain_Enchantment(
        self,
        *,
        energy_threshold_pct: float = 0.80,
        energy_threshold_abs: float | None = None,
    ) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, AgentArray, Player, Range, Routines, Utils

        drain_enchantment_id: int = Skill.GetID("Drain_Enchantment")

        if not self.build.IsSkillEquipped(drain_enchantment_id):
            return False

        # Drain Enchantment refunds energy and health on a successful strip,
        # so gate on the player's current energy the same way Power_Drain
        # does. Absolute threshold (when set) wins over the percentage.
        player_id = Player.GetAgentID()
        if energy_threshold_abs is not None:
            current_energy_abs = Agent.GetEnergy(player_id) * Agent.GetMaxEnergy(player_id)
            if current_energy_abs > energy_threshold_abs:
                return False
        elif Agent.GetEnergy(player_id) > energy_threshold_pct:
            return False

        player_pos = Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(
            player_pos[0], player_pos[1], Range.Spellcast.value
        )
        enchanted_enemies = AgentArray.Filter.ByCondition(
            enemy_array,
            lambda agent_id: (
                Agent.IsValid(agent_id)
                and not Agent.IsDead(agent_id)
                and Agent.IsEnchanted(agent_id)
            ),
        )
        if not enchanted_enemies:
            return False

        # Rank lowest-HP enchanted enemy first, break ties by proximity so a
        # close, low-HP strip wins over a far one with the same HP.
        target_agent_id = min(
            enchanted_enemies,
            key=lambda agent_id: (
                Agent.GetHealth(agent_id),
                Utils.Distance(player_pos, Agent.GetXY(agent_id)),
            ),
        )

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=drain_enchantment_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))

    def Power_Drain(
        self,
        *,
        energy_threshold_pct: float = 0.70,
        energy_threshold_abs: float | None = None,
    ) -> BuildCoroutine:
        from Py4GWCoreLib import Agent, Player, Range, Routines

        power_drain_id: int = Skill.GetID("Power_Drain")

        if not self.build.IsSkillEquipped(power_drain_id):
            return False

        # Power Drain exists to refill energy. Skip when the player does not
        # need it. Absolute threshold (when set) wins over the percentage
        # threshold so critical-tier call sites can express a flat floor.
        player_id = Player.GetAgentID()
        if energy_threshold_abs is not None:
            current_energy_abs = Agent.GetEnergy(player_id) * Agent.GetMaxEnergy(player_id)
            if current_energy_abs > energy_threshold_abs:
                return False
        elif Agent.GetEnergy(player_id) > energy_threshold_pct:
            return False

        target_agent_id: int = Routines.Targeting.GetEnemyCastingSpellOrChant(Range.Spellcast.value)
        if not target_agent_id:
            return False

        return (yield from self.build.CastSkillIDAndRestoreTarget(
            skill_id=power_drain_id,
            target_agent_id=target_agent_id,
            log=False,
            aftercast_delay=250,
        ))
