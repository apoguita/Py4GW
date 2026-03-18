from time import monotonic

from Py4GWCoreLib import BuildMgr, Profession, Routines, GLOBAL_CACHE, Range
from Py4GWCoreLib.Builds.Any.AutoCombat import AutoCombat
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill


class Psychic_Instability(BuildMgr):
	def __init__(self):
		super().__init__(
			name="Psychic Instability",
			required_primary=Profession.Mesmer,
			required_secondary=Profession(0),
			template_code="",
			required_skills=[
				Skill.GetID("Psychic_Instability"),
				Skill.GetID("Cry_of_Frustration"),
				Skill.GetID("Wastrels_Worry"),
			],
			optional_skills=[
				Skill.GetID("Arcane_Conundrum"),
				Skill.GetID("Wastrels_Demise"),
				Skill.GetID("Energy_Surge"),
				Skill.GetID("Mind_Wrack"),
				Skill.GetID("Shatter_Delusions"),
			],
		)

		self.minimum_required_match = 3

		self.SetFallback("AutoCombat", AutoCombat())
		self.SetSkillCastingFn(self._run_local_skill_logic)

		self.psychic_instability = Skill.GetID("Psychic_Instability")
		self.cry_of_frustration = Skill.GetID("Cry_of_Frustration")
		self.wastrels_worry = Skill.GetID("Wastrels_Worry")

		# Both are nearby AoE interrupts.
		self.interrupt_aoe_ranges = {
			self.psychic_instability: Range.Nearby.value,
			self.cry_of_frustration: Range.Nearby.value,
		}

		self.last_pi_target_id = 0
		self.last_pi_cast_time = 0.0
		self.pi_followup_window_seconds = 2.0

	def _has_valid_enemy_target(self) -> bool:
		target_id = Player.GetTargetID()
		if target_id <= 0:
			return False
		return Agent.IsValid(target_id) and not Agent.IsDead(target_id)

	def _get_best_interrupt_cluster_target(self, skill_id: int, min_cast_activation: float = 0.0) -> int:
		aoe_radius = self.interrupt_aoe_ranges.get(skill_id, Range.Nearby.value)
		radius_sq = aoe_radius * aoe_radius

		player_x, player_y = Player.GetXY()
		enemy_ids = Routines.Agents.GetFilteredEnemyArray(player_x, player_y, Range.Spellcast.value)
		if not enemy_ids:
			return 0

		caster_centers: list[int] = []
		for enemy_id in enemy_ids:
			if not Agent.IsValid(enemy_id) or Agent.IsDead(enemy_id):
				continue
			if not Agent.IsCasting(enemy_id):
				continue

			if min_cast_activation > 0.0:
				cast_skill_id = Agent.GetCastingSkillID(enemy_id)
				if cast_skill_id <= 0:
					continue
				if GLOBAL_CACHE.Skill.Data.GetActivation(cast_skill_id) < min_cast_activation:
					continue

			caster_centers.append(enemy_id)

		if not caster_centers:
			return 0

		best_target = 0
		best_hits = -1
		best_player_dist_sq = float("inf")

		for center_id in caster_centers:
			center_x, center_y = Agent.GetXY(center_id)

			hits = 0
			for enemy_id in enemy_ids:
				if not Agent.IsValid(enemy_id) or Agent.IsDead(enemy_id):
					continue
				enemy_x, enemy_y = Agent.GetXY(enemy_id)
				dx = enemy_x - center_x
				dy = enemy_y - center_y
				if (dx * dx) + (dy * dy) <= radius_sq:
					hits += 1

			pdx = center_x - player_x
			pdy = center_y - player_y
			player_dist_sq = (pdx * pdx) + (pdy * pdy)

			if hits > best_hits or (hits == best_hits and player_dist_sq < best_player_dist_sq):
				best_hits = hits
				best_player_dist_sq = player_dist_sq
				best_target = center_id

		return best_target

	def _try_cast_interrupt_cluster_skill(self, skill_id: int, aftercast_delay: int = 200, min_cast_activation: float = 0.0):
		best_target = self._get_best_interrupt_cluster_target(skill_id, min_cast_activation=min_cast_activation)
		if best_target <= 0:
			return False

		if Player.GetTargetID() != best_target:
			yield from Routines.Yield.Agents.ChangeTarget(best_target)
			return True

		casted = (
			yield from self.CastSkillID(
				skill_id,
				extra_condition=lambda target_id=best_target: Player.GetTargetID() == target_id
				and Agent.IsValid(target_id)
				and not Agent.IsDead(target_id)
				and Agent.IsCasting(target_id),
				log=False,
				aftercast_delay=aftercast_delay,
			)
		)

		if casted and skill_id == self.psychic_instability:
			self.last_pi_target_id = best_target
			self.last_pi_cast_time = monotonic()

		return casted

	def _try_cast_wastrels_after_pi_knockdown(self):
		if self.last_pi_target_id <= 0:
			return False

		elapsed = monotonic() - self.last_pi_cast_time
		if elapsed > self.pi_followup_window_seconds:
			self.last_pi_target_id = 0
			return False

		target_id = self.last_pi_target_id
		if not Agent.IsValid(target_id) or Agent.IsDead(target_id):
			self.last_pi_target_id = 0
			return False
		if not Agent.IsKnockedDown(target_id):
			return False

		if Player.GetTargetID() != target_id:
			yield from Routines.Yield.Agents.ChangeTarget(target_id)
			return True

		casted = (
			yield from self.CastSkillID(
				self.wastrels_worry,
				extra_condition=lambda current_target=target_id: Player.GetTargetID() == current_target
				and Agent.IsValid(current_target)
				and not Agent.IsDead(current_target)
				and Agent.IsKnockedDown(current_target),
				log=False,
				aftercast_delay=200,
			)
		)

		if casted:
			self.last_pi_target_id = 0
		return casted

	def _run_local_skill_logic(self):
		if not Routines.Checks.Skills.CanCast():
			yield from Routines.Yield.wait(40)
			return

		# Immediate follow-up: cast Wastrel's Worry right after PI knockdown.
		if (yield from self._try_cast_wastrels_after_pi_knockdown()):
			return

		# Main AoE interrupt on biggest caster cluster.
		if (
			yield from self._try_cast_interrupt_cluster_skill(
				self.psychic_instability,
				aftercast_delay=220,
				min_cast_activation=0.75,
			)
		):
			return

		# Secondary AoE interrupt on biggest caster cluster.
		if (
			yield from self._try_cast_interrupt_cluster_skill(
				self.cry_of_frustration,
				aftercast_delay=200,
				min_cast_activation=0.0,
			)
		):
			return

		if not self._has_valid_enemy_target():
			yield from Routines.Yield.Agents.TargetNearestEnemy(Range.Spellcast.value)
			return
