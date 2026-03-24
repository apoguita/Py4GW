from __future__ import annotations


class EnemyClusterTargetingMixin:
    def _get_enemy_array(self, max_distance: float) -> list[int]:
        from Py4GWCoreLib import Agent, AgentArray, Player, Routines

        player_x, player_y = Player.GetXY()
        enemy_array = Routines.Agents.GetFilteredEnemyArray(player_x, player_y, max_distance)
        return AgentArray.Filter.ByCondition(
            enemy_array,
            lambda agent_id: Agent.IsValid(agent_id) and not Agent.IsDead(agent_id),
        )

    def _get_cluster_score(self, agent_id: int, cluster_radius: float) -> int:
        from Py4GWCoreLib import Agent, AgentArray, Routines

        if not agent_id or cluster_radius <= 0:
            return 0

        target_x, target_y = Agent.GetXY(agent_id)
        nearby_enemies = Routines.Agents.GetFilteredEnemyArray(target_x, target_y, cluster_radius)
        nearby_enemies = AgentArray.Filter.ByCondition(
            nearby_enemies,
            lambda enemy_id: Agent.IsValid(enemy_id) and not Agent.IsDead(enemy_id),
        )
        return max(0, len(nearby_enemies) - 1)

    def _pick_best_target(self, agent_ids: list[int], cluster_radius: float) -> int:
        from Py4GWCoreLib import Agent, Player, Utils

        if not agent_ids:
            return 0

        player_pos = Player.GetXY()
        scored_targets = [
            (
                self._get_cluster_score(agent_id, cluster_radius),
                Utils.Distance(player_pos, Agent.GetXY(agent_id)),
                agent_id,
            )
            for agent_id in agent_ids
        ]
        scored_targets.sort(key=lambda item: (-item[0], item[1]))
        return scored_targets[0][2]