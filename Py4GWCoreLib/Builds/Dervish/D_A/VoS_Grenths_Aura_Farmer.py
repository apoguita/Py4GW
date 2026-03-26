from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import Agent
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Player
from Py4GWCoreLib import Profession
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib.Skill import Skill


Sand_Shards_ID = Skill.GetID("Sand_Shards")
Vow_of_Strength_ID = Skill.GetID("Vow_of_Strength")
Grenths_Aura_ID = Skill.GetID("Grenths_Aura")
Mystic_Regeneration_ID = Skill.GetID("Mystic_Regeneration")
Mirage_Cloak_ID = Skill.GetID("Mirage_Cloak")
Deaths_Charge_ID = Skill.GetID("Deaths_Charge")
I_Am_Unstoppable_ID = Skill.GetID("I_Am_Unstoppable")
Ebon_Battle_Standard_of_Honor_ID = Skill.GetID("Ebon_Battle_Standard_of_Honor")


class VoS_Grenths_Aura_Farmer(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="VoS Grenth's Aura Farmer",
            required_primary=Profession.Dervish,
            required_secondary=Profession.Assassin,
            template_code="OgejoqrMLSmXfbdfsXcX4O0k5iA",
            required_skills=[
                Sand_Shards_ID,
                Vow_of_Strength_ID,
                Grenths_Aura_ID,
                Mystic_Regeneration_ID,
                Mirage_Cloak_ID,
                Deaths_Charge_ID,
                I_Am_Unstoppable_ID,
                Ebon_Battle_Standard_of_Honor_ID,
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetBlockedSkills([
            Sand_Shards_ID,
            Vow_of_Strength_ID,
            Grenths_Aura_ID,
            Mirage_Cloak_ID,
            Deaths_Charge_ID,
            Ebon_Battle_Standard_of_Honor_ID,
            I_Am_Unstoppable_ID,
        ])
        self.SetSkillCastingFn(self._run_local_skill_logic)

    def _get_enemy_array(self, distance: float = Range.Spellcast.value) -> list[int]:
        player_x, player_y = Player.GetXY()
        return list(Routines.Agents.GetFilteredEnemyArray(player_x, player_y, distance) or [])

    def _count_enemies_near_agent(self, center_agent_id: int, enemy_array: list[int], radius: float = Range.Area.value) -> int:
        if not center_agent_id:
            return 0

        center_x, center_y = Agent.GetXY(center_agent_id)
        radius_sq = radius * radius
        count = 0
        for agent_id in enemy_array:
            enemy_x, enemy_y = Agent.GetXY(agent_id)
            dx = enemy_x - center_x
            dy = enemy_y - center_y
            if dx * dx + dy * dy <= radius_sq:
                count += 1
        return count

    def _count_enemies_near_player(self, enemy_array: list[int], radius: float = Range.Area.value) -> int:
        player_x, player_y = Player.GetXY()
        radius_sq = radius * radius
        count = 0
        for agent_id in enemy_array:
            enemy_x, enemy_y = Agent.GetXY(agent_id)
            dx = enemy_x - player_x
            dy = enemy_y - player_y
            if dx * dx + dy * dy <= radius_sq:
                count += 1
        return count

    def _get_best_deaths_charge_target(self, enemy_array: list[int]) -> int:
        player_x, player_y = Player.GetXY()
        best_target = 0
        best_cluster = 0

        for agent_id in enemy_array:
            enemy_x, enemy_y = Agent.GetXY(agent_id)
            dx = enemy_x - player_x
            dy = enemy_y - player_y
            if dx * dx + dy * dy <= Range.Adjacent.value * Range.Adjacent.value:
                continue

            cluster_count = self._count_enemies_near_agent(agent_id, enemy_array, Range.Nearby.value)
            if cluster_count > best_cluster:
                best_cluster = cluster_count
                best_target = agent_id

        if best_cluster >= 3:
            return best_target
        return 0

    def _run_local_skill_logic(self):
        player_agent_id = Player.GetAgentID()
        in_combat = Routines.Checks.Agents.InAggro()
        enemy_array = self._get_enemy_array()
        nearby_enemy_count = self._count_enemies_near_player(enemy_array, Range.Area.value)
        player_hp = Agent.GetHealth(player_agent_id)

        has_sand_shards = Routines.Checks.Effects.HasBuff(player_agent_id, Sand_Shards_ID)
        has_vow_of_strength = Routines.Checks.Effects.HasBuff(player_agent_id, Vow_of_Strength_ID)
        has_mystic_regeneration = Routines.Checks.Effects.HasBuff(player_agent_id, Mystic_Regeneration_ID)
        has_mirage_cloak = Routines.Checks.Effects.HasBuff(player_agent_id, Mirage_Cloak_ID)
        has_grenths_aura = Routines.Checks.Effects.HasBuff(player_agent_id, Grenths_Aura_ID)
        has_i_au = Routines.Checks.Effects.HasBuff(player_agent_id, I_Am_Unstoppable_ID)
        has_battle_standard = Routines.Checks.Effects.HasBuff(player_agent_id, Ebon_Battle_Standard_of_Honor_ID)
        mirage_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_agent_id, Mirage_Cloak_ID) if has_mirage_cloak else 0

        if not in_combat and not has_vow_of_strength:
            if (yield from self.CastSkillID(Vow_of_Strength_ID, aftercast_delay=250)):
                return

        if not in_combat and not has_mystic_regeneration:
            if (yield from self.CastSkillID(Mystic_Regeneration_ID, aftercast_delay=250)):
                return

        if in_combat:
            deaths_charge_target = self._get_best_deaths_charge_target(enemy_array)
            if deaths_charge_target and self.CanCastSkillID(Deaths_Charge_ID):
                if (yield from self.CastSkillIDAndRestoreTarget(
                    Deaths_Charge_ID,
                    deaths_charge_target,
                    aftercast_delay=350,
                )):
                    return

            if nearby_enemy_count >= 3 and not has_battle_standard:
                if (yield from self.CastSpiritSkillID(Ebon_Battle_Standard_of_Honor_ID, aftercast_delay=250)):
                    return

            if not has_i_au:
                if (yield from self.CastSkillID(I_Am_Unstoppable_ID, aftercast_delay=150)):
                    return

            if not has_vow_of_strength:
                if (yield from self.CastSkillID(Vow_of_Strength_ID, aftercast_delay=250)):
                    return

            if (not has_mirage_cloak) or mirage_remaining <= 1500:
                if (yield from self.CastSkillID(Mirage_Cloak_ID, aftercast_delay=250)):
                    return

        if (not has_grenths_aura) and in_combat and nearby_enemy_count >= 3 and player_hp <= 0.85:
            if (yield from self.CastSkillID(Grenths_Aura_ID, aftercast_delay=250)):
                return

        if not has_sand_shards:
            if (yield from self.CastSkillID(Sand_Shards_ID, aftercast_delay=250)):
                return

        if not has_grenths_aura:
            if (yield from self.CastSkillID(Grenths_Aura_ID, aftercast_delay=250)):
                return

        return False
