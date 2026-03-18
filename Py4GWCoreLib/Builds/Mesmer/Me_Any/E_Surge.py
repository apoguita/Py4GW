from Py4GWCoreLib import BuildMgr, Profession, Routines, GLOBAL_CACHE, Range
from Py4GWCoreLib.Builds.Any.AutoCombat import AutoCombat
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill


class E_Surge(BuildMgr):
	def __init__(self):
		super().__init__(
			name="Energy Surge Mesmer",
			required_primary=Profession.Mesmer,
			required_secondary=Profession(0),
			template_code="",
			required_skills=[
				Skill.GetID("Energy_Surge"),
				Skill.GetID("Cry_of_Frustration"),
			],
			optional_skills=[
				Skill.GetID("Arcane_Echo"),
				Skill.GetID("Energy_Burn"),
				Skill.GetID("Air_of_Superiority"),
				Skill.GetID("Flesh_of_My_Flesh"),
				Skill.GetID("Overload"),
				Skill.GetID("Unnatural_Signet"),
				Skill.GetID("Shatter_Hex"),
				Skill.GetID("Shatter_Delusions"),
				Skill.GetID("Shatter_Enchantment"),
				Skill.GetID("Cry_of_Pain"),
				Skill.GetID("Spiritual_Pain"),
				Skill.GetID("Chaos_Storm"),
				Skill.GetID("Mind_Wrack"),
				Skill.GetID("Empathy"),
			],
		)

		self.minimum_required_match = 4

		self.SetFallback("AutoCombat", AutoCombat())
		self.SetSkillCastingFn(self._run_local_skill_logic)

		# Core PvX-style package without Auspicious Incantation.
		self.air_of_superiority = Skill.GetID("Air_of_Superiority")
		self.arcane_echo = Skill.GetID("Arcane_Echo")
		self.energy_surge = Skill.GetID("Energy_Surge")
		self.energy_burn = Skill.GetID("Energy_Burn")
		self.cry_of_frustration = Skill.GetID("Cry_of_Frustration")
		self.flesh_of_my_flesh = Skill.GetID("Flesh_of_My_Flesh")

		# Common optional slot picks.
		self.overload = Skill.GetID("Overload")
		self.unnatural_signet = Skill.GetID("Unnatural_Signet")
		self.shatter_hex = Skill.GetID("Shatter_Hex")
		self.cry_of_pain = Skill.GetID("Cry_of_Pain")
		self.spiritual_pain = Skill.GetID("Spiritual_Pain")
		self.chaos_storm = Skill.GetID("Chaos_Storm")

		# AoE radii mapped from wiki wording:
		# Adjacent -> Range.Adjacent, Nearby -> Range.Nearby, In the area -> Range.Area.
		self.aoe_skill_ranges = {
			self.energy_surge: Range.Nearby.value,
			self.cry_of_frustration: Range.Nearby.value,
			self.unnatural_signet: Range.Adjacent.value,
			self.chaos_storm: Range.Area.value,
			self.cry_of_pain: Range.Nearby.value,
		}
		self.interrupt_skills = {
			self.cry_of_frustration,
			self.cry_of_pain,
		}

	def _has_valid_target(self) -> bool:
		target_id = Player.GetTargetID()
		if target_id <= 0:
			return False
		if not Agent.IsValid(target_id) or Agent.IsDead(target_id):
			return False
		return True

	def _get_dead_player_targets(self) -> list[int]:
		player_x, player_y = Player.GetXY()
		dead_targets: list[tuple[float, int]] = []

		for party_player in GLOBAL_CACHE.Party.GetPlayers():
			agent_id = int(GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(party_player.login_number) or 0)
			if agent_id <= 0:
				continue
			if not Agent.IsValid(agent_id) or not Agent.IsDead(agent_id):
				continue

			tx, ty = Agent.GetXY(agent_id)
			dx = tx - player_x
			dy = ty - player_y
			dead_targets.append(((dx * dx) + (dy * dy), agent_id))

		dead_targets.sort(key=lambda item: item[0])
		return [agent_id for _, agent_id in dead_targets]

	def _get_best_aoe_target(self, aoe_radius: float) -> int:
		player_x, player_y = Player.GetXY()
		enemy_ids = Routines.Agents.GetFilteredEnemyArray(player_x, player_y, Range.Spellcast.value)
		if not enemy_ids:
			return 0

		radius_sq = aoe_radius * aoe_radius
		best_target = 0
		best_hits = -1
		best_player_dist_sq = float("inf")

		for center_id in enemy_ids:
			if not Agent.IsValid(center_id) or Agent.IsDead(center_id):
				continue

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

	def _try_cast_aoe_skill(self, skill_id: int, aftercast_delay: int = 200):
		aoe_radius = self.aoe_skill_ranges.get(skill_id, Range.Nearby.value)
		best_target = self._get_best_aoe_target(aoe_radius)
		if best_target <= 0:
			return False

		if Player.GetTargetID() != best_target:
			yield from Routines.Yield.Agents.ChangeTarget(best_target)
			return True

		return (
			yield from self.CastSkillID(
				skill_id,
				extra_condition=lambda target_id=best_target: Player.GetTargetID() == target_id
				and Agent.IsValid(target_id)
				and not Agent.IsDead(target_id),
				log=False,
				aftercast_delay=aftercast_delay,
			)
		)

	def _get_best_interrupt_aoe_target(self, skill_id: int) -> int:
		aoe_radius = self.aoe_skill_ranges.get(skill_id, Range.Nearby.value)
		radius_sq = aoe_radius * aoe_radius

		player_x, player_y = Player.GetXY()
		enemy_ids = Routines.Agents.GetFilteredEnemyArray(player_x, player_y, Range.Spellcast.value)
		if not enemy_ids:
			return 0

		casting_targets = [
			agent_id
			for agent_id in enemy_ids
			if Agent.IsValid(agent_id) and not Agent.IsDead(agent_id) and Agent.IsCasting(agent_id)
		]
		if not casting_targets:
			return 0

		best_target = 0
		best_hits = -1
		best_player_dist_sq = float("inf")

		for center_id in casting_targets:
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

	def _try_cast_interrupt_aoe_skill(self, skill_id: int, aftercast_delay: int = 200):
		best_target = self._get_best_interrupt_aoe_target(skill_id)
		if best_target <= 0:
			return False

		if Player.GetTargetID() != best_target:
			yield from Routines.Yield.Agents.ChangeTarget(best_target)
			return True

		return (
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

	def _has_hexed_ally(self) -> bool:
		player_id = Player.GetAgentID()
		if Agent.IsHexed(player_id):
			return True

		player_x, player_y = Player.GetXY()
		for ally_id in Routines.Agents.GetFilteredAllyArray(player_x, player_y, Range.Spellcast.value, other_ally=True):
			if Agent.IsHexed(ally_id):
				return True
		return False

	def _get_best_hexed_enemy_aoe_target(self, aoe_radius: float) -> int:
		player_x, player_y = Player.GetXY()
		enemy_ids = Routines.Agents.GetFilteredEnemyArray(player_x, player_y, Range.Spellcast.value)
		if not enemy_ids:
			return 0

		hexed_centers = [
			agent_id
			for agent_id in enemy_ids
			if Agent.IsValid(agent_id) and not Agent.IsDead(agent_id) and Agent.IsHexed(agent_id)
		]
		if not hexed_centers:
			return 0

		radius_sq = aoe_radius * aoe_radius
		best_target = 0
		best_hits = -1
		best_player_dist_sq = float("inf")

		for center_id in hexed_centers:
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

	def _try_cast_shatter_hex_for_hexed_allies(self):
		if not self._has_hexed_ally():
			return False

		aoe_radius = self.aoe_skill_ranges.get(self.shatter_hex, Range.Nearby.value)
		best_target = self._get_best_hexed_enemy_aoe_target(aoe_radius)
		if best_target <= 0:
			return False

		if Player.GetTargetID() != best_target:
			yield from Routines.Yield.Agents.ChangeTarget(best_target)
			return True

		return (
			yield from self.CastSkillID(
				self.shatter_hex,
				extra_condition=lambda target_id=best_target: self._has_hexed_ally()
				and Player.GetTargetID() == target_id
				and Agent.IsValid(target_id)
				and not Agent.IsDead(target_id)
				and Agent.IsHexed(target_id),
				log=False,
				aftercast_delay=200,
			)
		)

	def _run_local_skill_logic(self):
		player_id = Player.GetAgentID()

		if not Routines.Checks.Skills.CanCast():
			yield from Routines.Yield.wait(40)
			return

		for dead_player_id in self._get_dead_player_targets():
			if Player.GetTargetID() != dead_player_id:
				yield from Routines.Yield.Agents.ChangeTarget(dead_player_id)
				return

			if (
				yield from self.CastSkillID(
					self.flesh_of_my_flesh,
					extra_condition=lambda target_id=dead_player_id: Player.GetTargetID() == target_id
					and Agent.IsValid(target_id)
					and Agent.IsDead(target_id),
					log=False,
					aftercast_delay=450,
				)
			):
				return

		if not self._has_valid_target():
			yield from Routines.Yield.Agents.TargetNearestEnemy(Range.Spellcast.value)
			return

		# Keep PvE title upkeep alive when present.
		if not Routines.Checks.Effects.HasBuff(player_id, self.air_of_superiority):
			if (
				yield from self.CastSkillID(
					self.air_of_superiority,
					extra_condition=lambda: not Routines.Checks.Effects.HasBuff(player_id, self.air_of_superiority),
					log=False,
					aftercast_delay=250,
				)
			):
				return

		# Burst package: Arcane Echo -> Energy Surge.
		if (
			yield from self.CastSkillID(
				self.arcane_echo,
				extra_condition=True,
				log=False,
				aftercast_delay=250,
			)
		):
			return

		if (yield from self._try_cast_aoe_skill(self.energy_surge, aftercast_delay=250)):
			return

		if (
			yield from self.CastSkillID(
				self.energy_burn,
				extra_condition=True,
				log=False,
				aftercast_delay=200,
			)
		):
			return

		if (yield from self._try_cast_interrupt_aoe_skill(self.cry_of_frustration, aftercast_delay=200)):
			return

		if (yield from self._try_cast_shatter_hex_for_hexed_allies()):
			return

		if (yield from self._try_cast_aoe_skill(self.chaos_storm, aftercast_delay=250)):
			return

		# Flexible optional finishers if present on the bar.
		for skill_id in (
			self.overload,
			self.unnatural_signet,
			self.cry_of_pain,
			self.spiritual_pain,
		):
			if skill_id in self.interrupt_skills:
				if (yield from self._try_cast_interrupt_aoe_skill(skill_id, aftercast_delay=200)):
					return
				continue

			if skill_id in self.aoe_skill_ranges:
				if (yield from self._try_cast_aoe_skill(skill_id, aftercast_delay=200)):
					return
				continue

			if (
				yield from self.CastSkillID(
					skill_id,
					extra_condition=True,
					log=False,
					aftercast_delay=200,
				)
			):
				return
