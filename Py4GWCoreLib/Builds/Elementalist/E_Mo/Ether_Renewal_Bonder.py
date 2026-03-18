from collections.abc import Generator
from typing import Any

from Py4GWCoreLib import BuildMgr, Profession, Routines, GLOBAL_CACHE
from Py4GWCoreLib.Builds.Any.AutoCombat import AutoCombat
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill


class Ether_Renewal_Bonder(BuildMgr):
	def __init__(self):
		super().__init__(
			name="Ether Renewal Bonder",
			required_primary=Profession.Elementalist,
			required_secondary=Profession.Monk,
			# PvX bar has two optional slots, so we keep template loading disabled here.
			template_code="",
			required_skills=[
				Skill.GetID("Infuse_Health"),
				Skill.GetID("Spirit_Bond"),
				Skill.GetID("Life_Attunement"),
				Skill.GetID("Protective_Bond"),
				Skill.GetID("Ether_Renewal"),
				Skill.GetID("Aura_of_Restoration"),
			],
			optional_skills=[
				Skill.GetID("Burning_Speed"),
				Skill.GetID("Great_Dwarf_Weapon"),
				Skill.GetID("Reversal_of_Fortune"),
				Skill.GetID("Shield_of_Absorption"),
				Skill.GetID("Aegis"),
				Skill.GetID("Protective_Spirit"),
				Skill.GetID("Vigorous_Spirit"),
				Skill.GetID("Healing_Breeze"),
				Skill.GetID("Draw_Conditions"),
			],
		)
		self.minimum_required_match = 5

		self.SetFallback("AutoCombat", AutoCombat())
		self.SetSkillCastingFn(self._run_local_skill_logic)

		self.infuse_health = Skill.GetID("Infuse_Health")
		self.spirit_bond = Skill.GetID("Spirit_Bond")
		self.life_attunement = Skill.GetID("Life_Attunement")
		self.protective_bond = Skill.GetID("Protective_Bond")
		self.protective_bond_buff_id = 263
		self.ether_renewal = Skill.GetID("Ether_Renewal")
		self.aura_of_restoration = Skill.GetID("Aura_of_Restoration")
		self.burning_speed = Skill.GetID("Burning_Speed")
		self.infuse_health_threshold = 0.70
		self.spirit_bond_health_threshold = 0.90
		self.low_mana_drop_threshold = 0.10
		self.protective_bond_energy_threshold = 0.80
		self.burning_speed_energy_threshold = 0.75

	def _get_party_member_ids(self, player_id: int) -> list[int]:
		member_ids: list[int] = [player_id]

		for player in GLOBAL_CACHE.Party.GetPlayers():
			agent_id = int(GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number) or 0)
			if agent_id > 0 and agent_id not in member_ids:
				member_ids.append(agent_id)

		for hero in GLOBAL_CACHE.Party.GetHeroes():
			agent_id = int(getattr(hero, "agent_id", 0) or 0)
			if agent_id > 0 and agent_id not in member_ids:
				member_ids.append(agent_id)

		for henchman in GLOBAL_CACHE.Party.GetHenchmen():
			agent_id = int(getattr(henchman, "agent_id", 0) or 0)
			if agent_id > 0 and agent_id not in member_ids:
				member_ids.append(agent_id)

		return member_ids

	def _has_shared_memory_buff(self, agent_id: int, buff_id: int) -> bool:
		if agent_id <= 0 or buff_id <= 0:
			return False

		# Shared memory is authoritative for ally buff state.
		for account in GLOBAL_CACHE.ShMem.GetAllAccountData():
			if not account.IsSlotActive:
				continue
			if int(account.AgentPartyData.PartyID) != int(GLOBAL_CACHE.Party.GetPartyID()):
				continue
			if int(account.AgentData.AgentID) != int(agent_id):
				continue

			for buff in account.AgentData.Buffs.Buffs:
				if int(getattr(buff, "SkillId", 0) or 0) == int(buff_id):
					return True
			return False

		# Fallback for local agent when no shared-memory slot is available.
		return Routines.Checks.Effects.HasBuff(agent_id, buff_id)

	def _ensure_stationary_for_cast(self, player_id: int) -> Generator[Any, Any, bool]:
		# Do not force a pre-cast stop. Only pin position during the real cast animation,
		# so follow can resume immediately after the spell has finished casting.
		max_lock_ms = 500
		elapsed_ms = 0
		while Agent.IsCasting(player_id) and elapsed_ms < max_lock_ms:
			px, py = Player.GetXY()
			Player.Move(px, py)
			yield from Routines.Yield.wait(40)
			elapsed_ms += 40
		return True

	def _try_cast_skill(self, player_id: int, skill_id: int, extra_condition, aftercast_delay: int = 250) -> Generator[Any, Any, bool]:
		casted = (
			yield from self.CastSkillID(
				skill_id=skill_id,
				extra_condition=extra_condition,
				log=False,
				aftercast_delay=aftercast_delay,
			)
		)
		if casted:
			yield from self._ensure_stationary_for_cast(player_id)
		return casted

	def _get_spirit_bond_targets(self, player_id: int) -> list[int]:
		candidates: list[tuple[float, int]] = []
		for ally_id in self._get_party_member_ids(player_id):
			if not Agent.IsValid(ally_id) or Agent.IsDead(ally_id):
				continue
			if self._has_shared_memory_buff(ally_id, self.spirit_bond):
				continue

			health_ratio = float(Agent.GetHealth(ally_id))
			if health_ratio <= 0.0 or health_ratio >= self.spirit_bond_health_threshold:
				continue
			candidates.append((health_ratio, ally_id))

		candidates.sort(key=lambda item: item[0])
		return [ally_id for _, ally_id in candidates]

	def _get_infuse_targets(self, player_id: int) -> list[int]:
		candidates: list[tuple[float, int]] = []
		for ally_id in self._get_party_member_ids(player_id):
			if ally_id == player_id:
				continue
			if not Agent.IsValid(ally_id) or Agent.IsDead(ally_id):
				continue

			health_ratio = float(Agent.GetHealth(ally_id))
			if health_ratio <= 0.0 or health_ratio >= self.infuse_health_threshold:
				continue
			candidates.append((health_ratio, ally_id))

		candidates.sort(key=lambda item: item[0])
		return [ally_id for _, ally_id in candidates]

	def _drop_own_protective_bonds(self, player_id: int) -> bool:
		buffs = GLOBAL_CACHE.Effects.GetBuffs(player_id)
		any_dropped = False
		for buff in buffs:
			skill_id = int(getattr(buff, "skill_id", 0) or 0)
			if skill_id != int(self.protective_bond):
				continue

			buff_id = int(getattr(buff, "buff_id", 0) or 0)
			if buff_id <= 0:
				continue

			GLOBAL_CACHE.Effects.DropBuff(buff_id)
			any_dropped = True

		return any_dropped

	def _run_local_skill_logic(self):
		player_id = Player.GetAgentID()
		player_energy_ratio = Agent.GetEnergy(player_id)

		if (
			not Routines.Checks.Effects.HasBuff(player_id, self.ether_renewal)
			and (player_energy_ratio <= 0.0 or player_energy_ratio < self.low_mana_drop_threshold)
		):
			if self._drop_own_protective_bonds(player_id):
				yield from Routines.Yield.wait(100)
				return

		if not Routines.Checks.Skills.CanCast():
			# Do not issue movement overrides here; just wait for next tick.
			yield from Routines.Yield.wait(40)
			return

		# Absolute priority: while Ether Renewal is down, do not cast anything else.
		if not Routines.Checks.Effects.HasBuff(player_id, self.ether_renewal):
			yield from self._try_cast_skill(
				player_id=player_id,
				skill_id=self.ether_renewal,
				extra_condition=lambda: not Routines.Checks.Effects.HasBuff(player_id, self.ether_renewal),
			)
			return

		for ally_id in self._get_infuse_targets(player_id):
			if Player.GetTargetID() != ally_id:
				yield from Routines.Yield.Agents.ChangeTarget(ally_id)
				return

			if (
				yield from self._try_cast_skill(
					player_id=player_id,
					skill_id=self.infuse_health,
					extra_condition=lambda current_target=ally_id: Routines.Checks.Effects.HasBuff(player_id, self.ether_renewal)
					and Player.GetTargetID() == current_target
					and Agent.GetHealth(current_target) < self.infuse_health_threshold,
				)
			):
				return

		for ally_id in self._get_spirit_bond_targets(player_id):
			if Player.GetTargetID() != ally_id:
				yield from Routines.Yield.Agents.ChangeTarget(ally_id)
				return

			if (
				yield from self._try_cast_skill(
					player_id=player_id,
					skill_id=self.spirit_bond,
					extra_condition=lambda current_target=ally_id: Routines.Checks.Effects.HasBuff(player_id, self.ether_renewal)
					and Player.GetTargetID() == current_target
					and Agent.GetHealth(current_target) < self.spirit_bond_health_threshold
					and not self._has_shared_memory_buff(current_target, self.spirit_bond),
				)
			):
				return

		if not Routines.Checks.Effects.HasBuff(player_id, self.aura_of_restoration):
			if (
				yield from self._try_cast_skill(
					player_id=player_id,
					skill_id=self.aura_of_restoration,
					extra_condition=lambda: not Routines.Checks.Effects.HasBuff(player_id, self.aura_of_restoration),
				)
			):
				return

		if player_energy_ratio < self.burning_speed_energy_threshold:
			if (
				yield from self._try_cast_skill(
					player_id=player_id,
					skill_id=self.burning_speed,
					extra_condition=lambda: Routines.Checks.Effects.HasBuff(player_id, self.ether_renewal)
					and Agent.GetEnergy(player_id) < self.burning_speed_energy_threshold,
				)
			):
				return

		if not Routines.Checks.Effects.HasBuff(player_id, self.life_attunement):
			if Player.GetTargetID() != player_id:
				yield from Routines.Yield.Agents.ChangeTarget(player_id)
				return

			if (
				yield from self._try_cast_skill(
					player_id=player_id,
					skill_id=self.life_attunement,
					extra_condition=lambda: Player.GetTargetID() == player_id
					and not Routines.Checks.Effects.HasBuff(player_id, self.life_attunement),
				)
			):
				return

		if player_energy_ratio >= self.protective_bond_energy_threshold:
			if not self._has_shared_memory_buff(player_id, self.protective_bond_buff_id):
				if Player.GetTargetID() != player_id:
					yield from Routines.Yield.Agents.ChangeTarget(player_id)
					return

				if (
					yield from self._try_cast_skill(
						player_id=player_id,
						skill_id=self.protective_bond,
						extra_condition=lambda: Routines.Checks.Effects.HasBuff(player_id, self.ether_renewal)
						and Agent.GetEnergy(player_id) >= self.protective_bond_energy_threshold
						and Player.GetTargetID() == player_id
						and not self._has_shared_memory_buff(player_id, self.protective_bond_buff_id),
					)
				):
					return

			for ally_id in self._get_party_member_ids(player_id):
				if ally_id == player_id:
					continue
				if not Agent.IsValid(ally_id) or Agent.IsDead(ally_id):
					continue
				if self._has_shared_memory_buff(ally_id, self.protective_bond_buff_id):
					continue

				if Player.GetTargetID() != ally_id:
					yield from Routines.Yield.Agents.ChangeTarget(ally_id)
					return

				if (
					yield from self._try_cast_skill(
						player_id=player_id,
						skill_id=self.protective_bond,
						extra_condition=lambda current_target=ally_id: Routines.Checks.Effects.HasBuff(player_id, self.ether_renewal)
						and Agent.GetEnergy(player_id) >= self.protective_bond_energy_threshold
						and Player.GetTargetID() == current_target
						and not self._has_shared_memory_buff(current_target, self.protective_bond_buff_id),
					)
				):
					return
