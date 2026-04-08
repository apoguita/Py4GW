from Py4GWCoreLib import Profession
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Player, Range
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

        if not Routines.Checks.Agents.InAggro():
            return False

        nearby_enemies = Routines.Agents.GetFilteredEnemyArray(
            player_x,
            player_y,
            max_distance=Range.Spellcast.value,
        )
        enemy_count = len(nearby_enemies)

        if self.IsSkillEquipped(Animate_Bone_Horror_ID):
            nearest_corpse = Routines.Agents.GetNearestCorpse(max_distance=Range.Spellcast.value)
            if nearest_corpse and (yield from self.CastSkillID(
                skill_id=Animate_Bone_Horror_ID,
                target_agent_id=nearest_corpse,
                log=False,
                aftercast_delay=250,
            )):
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
