from Py4GWCoreLib import Profession
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Agent, AgentArray, Player, Range, GLOBAL_CACHE
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build


Aura_of_Restoration_ID = Skill.GetID("Aura_of_Restoration")
Fire_Storm_ID = Skill.GetID("Fire_Storm")
Flare_ID = Skill.GetID("Flare")
Deathly_Swarm_ID = Skill.GetID("Deathly_Swarm")
Animate_Bone_Horror_ID = Skill.GetID("Animate_Bone_Horror")
Resurrection_Signet_ID = Skill.GetID("Resurrection_Signet")


class Pre_Searing_Necro(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Pre-Searing Necro",
            required_primary=Profession.Necromancer,
            required_secondary=Profession.Elementalist,
            template_code="",
            required_skills=[
                Aura_of_Restoration_ID,
                Fire_Storm_ID,
                Flare_ID,
                Deathly_Swarm_ID,
                Animate_Bone_Horror_ID,
                Resurrection_Signet_ID,
            ],
            optional_skills=[],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)

    @staticmethod
    def _get_nearest_exploitable_corpse(max_distance=Range.Spellcast.value):
        def _allowed_allegiance(agent_id: int) -> bool:
            _, allegiance = Agent.GetAllegiance(agent_id)
            return allegiance in ("Ally", "Neutral", "Enemy", "NPC/Minipet")

        corpse_array = AgentArray.GetAgentArray()
        corpse_array = AgentArray.Filter.ByDistance(corpse_array, Player.GetXY(), max_distance)
        corpse_array = AgentArray.Filter.ByCondition(
            corpse_array,
            lambda agent_id: (
                Agent.IsDead(agent_id)
                and not Agent.HasBossGlow(agent_id)
                and not Agent.IsSpirit(agent_id)
                and not Agent.IsSpawned(agent_id)
                and not Agent.IsMinion(agent_id)
                and not Routines.Agents.IsExploitableCorpseModelBlocked(Agent.GetModelID(agent_id))
            ),
        )
        corpse_array = AgentArray.Filter.ByCondition(corpse_array, _allowed_allegiance)
        corpse_array = AgentArray.Sort.ByDistance(corpse_array, Player.GetXY())
        return corpse_array[0] if corpse_array else 0

    def _mark_corpse_model_if_cast_failed(
        self,
        corpse_agent_id: int,
        skill_id: int,
        wait_ms: int = 900,
    ):
        if False:
            yield

        model_id = int(Agent.GetModelID(corpse_agent_id) or 0)
        saw_cast_start = False
        remaining_ms = wait_ms
        while remaining_ms > 0:
            step_ms = min(50, remaining_ms)
            yield from Routines.Yield.wait(step_ms)
            remaining_ms -= step_ms
            if Agent.IsCasting(Player.GetAgentID()) or (GLOBAL_CACHE.SkillBar.GetCasting() or 0):
                saw_cast_start = True

        if saw_cast_start:
            return False

        return Routines.Agents.MarkExploitableCorpseCastFailed(
            agent_id=corpse_agent_id,
            model_id=model_id,
            skill_id=skill_id,
            reason="cast_never_started",
        )

    def _run_local_skill_logic(self):
        player_agent_id = Player.GetAgentID()
        player_x, player_y = Player.GetXY()

        if not Routines.Checks.Skills.CanCast():
            return False

        if self.IsSkillEquipped(Resurrection_Signet_ID):
            dead_ally_id = Routines.Agents.GetDeadAlly(max_distance=Range.Spellcast.value)
            if dead_ally_id and (yield from self.CastSkillID(
                skill_id=Resurrection_Signet_ID,
                target_agent_id=dead_ally_id,
                log=False,
                aftercast_delay=250,
            )):
                return True

        if self.IsSkillEquipped(Aura_of_Restoration_ID):
            should_cast_aura = not Routines.Checks.Agents.HasEffect(player_agent_id, Aura_of_Restoration_ID)
            if should_cast_aura and (yield from self.CastSkillID(
                skill_id=Aura_of_Restoration_ID,
                log=False,
                aftercast_delay=250,
            )):
                return True

        if not self.IsInAggro():
            return False

        nearby_enemies = Routines.Agents.GetFilteredEnemyArray(
            player_x,
            player_y,
            max_distance=Range.Spellcast.value,
        )
        enemy_count = len(nearby_enemies)

        if self.IsSkillEquipped(Animate_Bone_Horror_ID):
            nearest_exploitable_corpse = self._get_nearest_exploitable_corpse(max_distance=Range.Spellcast.value)
            if nearest_exploitable_corpse and (yield from self.CastSkillID(
                skill_id=Animate_Bone_Horror_ID,
                target_agent_id=nearest_exploitable_corpse,
                log=False,
                aftercast_delay=250,
            )):
                yield from self._mark_corpse_model_if_cast_failed(
                    nearest_exploitable_corpse,
                    Animate_Bone_Horror_ID,
                    wait_ms=1200,
                )
                return True

        if self.IsSkillEquipped(Fire_Storm_ID):
            clustered_enemy_id = Routines.Targeting.TargetClusteredEnemy(area=Range.Spellcast.value)
            if clustered_enemy_id and enemy_count >= 3 and (yield from self.CastSkillID(
                skill_id=Fire_Storm_ID,
                target_agent_id=clustered_enemy_id,
                log=False,
                aftercast_delay=250,
            )):
                return True

        if self.IsSkillEquipped(Deathly_Swarm_ID):
            nearest_enemy_id = Routines.Agents.GetNearestEnemy(max_distance=Range.Spellcast.value)
            if nearest_enemy_id and enemy_count >= 2 and (yield from self.CastSkillID(
                skill_id=Deathly_Swarm_ID,
                target_agent_id=nearest_enemy_id,
                log=False,
                aftercast_delay=250,
            )):
                return True

        if self.IsSkillEquipped(Flare_ID):
            nearest_enemy_id = Routines.Agents.GetNearestEnemy(max_distance=Range.Spellcast.value)
            if nearest_enemy_id and (yield from self.CastSkillID(
                skill_id=Flare_ID,
                target_agent_id=nearest_enemy_id,
                log=False,
                aftercast_delay=250,
            )):
                return True

        if (yield from self.AutoAttack()):
            return True

        return False
