from Py4GWCoreLib import BuildMgr, Profession, Routines, GLOBAL_CACHE
from Py4GWCoreLib.Builds.Any.AutoCombat import AutoCombat
from Py4GWCoreLib.Agent import Agent
from Py4GWCoreLib.Player import Player
from Py4GWCoreLib.Skill import Skill


class Dark_Aura_Support(BuildMgr):
	def __init__(self):
		super().__init__(
			name="Dark Aura Support",
			required_primary=Profession.Necromancer,
			required_secondary=Profession(0),
			template_code="",
			required_skills=[
				Skill.GetID("Dark_Aura"),
				Skill.GetID("Masochism"),
			],
			optional_skills=[
				Skill.GetID("Soul_Taker"),
				Skill.GetID("Great_Dwarf_Weapon"),
				Skill.GetID("Putrid_Explosion"),
				Skill.GetID("Ebon_Escape"),
			],
		)

		self.minimum_required_match = 2

		self.SetFallback("AutoCombat", AutoCombat())
		self.SetSkillCastingFn(self._run_local_skill_logic)

		self.dark_aura = Skill.GetID("Dark_Aura")
		self.masochism = Skill.GetID("Masochism")
		self.soul_taker = Skill.GetID("Soul_Taker")

	def _get_party_member_ids(self, player_id: int) -> list[int]:
		member_ids: list[int] = [player_id]

		for party_player in GLOBAL_CACHE.Party.GetPlayers():
			agent_id = int(GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(party_player.login_number) or 0)
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

	def _has_shared_memory_buff(self, agent_id: int, buff_skill_id: int) -> bool:
		if agent_id <= 0 or buff_skill_id <= 0:
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
				if int(getattr(buff, "SkillId", 0) or 0) == int(buff_skill_id):
					return True
			return False

		return Routines.Checks.Effects.HasBuff(agent_id, buff_skill_id)

	def _is_team_necromancer(self, agent_id: int) -> bool:
		primary, secondary = Agent.GetProfessionIDs(agent_id)
		necro_id = int(Profession.Necromancer)
		return int(primary) == necro_id or int(secondary) == necro_id

	def _get_dark_aura_targets(self, player_id: int) -> list[int]:
		player_x, player_y = Player.GetXY()
		candidates: list[tuple[float, int]] = []

		for ally_id in self._get_party_member_ids(player_id):
			if not Agent.IsValid(ally_id) or Agent.IsDead(ally_id):
				continue
			if not self._is_team_necromancer(ally_id):
				continue
			if not self._has_shared_memory_buff(ally_id, self.soul_taker):
				continue
			if self._has_shared_memory_buff(ally_id, self.dark_aura):
				continue

			ally_x, ally_y = Agent.GetXY(ally_id)
			dx = ally_x - player_x
			dy = ally_y - player_y
			candidates.append(((dx * dx) + (dy * dy), ally_id))

		candidates.sort(key=lambda item: item[0])
		return [ally_id for _, ally_id in candidates]

	def _run_local_skill_logic(self):
		player_id = Player.GetAgentID()

		if not Routines.Checks.Skills.CanCast():
			yield from Routines.Yield.wait(40)
			return

		# Maintain Masochism on self.
		if not Routines.Checks.Effects.HasBuff(player_id, self.masochism):
			if (
				yield from self.CastSkillID(
					self.masochism,
					extra_condition=lambda: not Routines.Checks.Effects.HasBuff(player_id, self.masochism),
					log=False,
					aftercast_delay=200,
				)
			):
				return

		# Dark Aura only on team necromancers that currently have Soul Taker.
		for ally_id in self._get_dark_aura_targets(player_id):
			if Player.GetTargetID() != ally_id:
				yield from Routines.Yield.Agents.ChangeTarget(ally_id)
				return

			if (
				yield from self.CastSkillID(
					self.dark_aura,
					extra_condition=lambda current_target=ally_id: Player.GetTargetID() == current_target
					and Agent.IsValid(current_target)
					and not Agent.IsDead(current_target)
					and self._is_team_necromancer(current_target)
					and self._has_shared_memory_buff(current_target, self.soul_taker)
					and not self._has_shared_memory_buff(current_target, self.dark_aura),
					log=False,
					aftercast_delay=250,
				)
			):
				return
