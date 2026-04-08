from Py4GWCoreLib import Profession
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Agent, Player, Range
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build


Aura_of_Restoration_ID = Skill.GetID("Aura_of_Restoration")
Fire_Storm_ID = Skill.GetID("Fire_Storm")
Flare_ID = Skill.GetID("Flare")
Ether_Feast_ID = Skill.GetID("Ether_Feast")
Resurrection_Signet_ID = Skill.GetID("Resurrection_Signet")


class Pre_Searing_ele(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Pre-Searing ele",
            required_primary=Profession.Elementalist,
            required_secondary=Profession.Mesmer,
            template_code="",
            required_skills=[
                Aura_of_Restoration_ID,
                Fire_Storm_ID,
                Flare_ID,
                Ether_Feast_ID,
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

        if self.IsSkillEquipped(Ether_Feast_ID):
            should_cast_ether_feast = Agent.GetHealth(player_agent_id) < 0.65
            if should_cast_ether_feast and (yield from self.CastSkillID(
                skill_id=Ether_Feast_ID,
                log=False,
                aftercast_delay=250,
            )):
                return True

        if not Routines.Checks.Agents.InAggro():
            return False

        if self.IsSkillEquipped(Fire_Storm_ID) and (yield from self.CastSkillID(
            skill_id=Fire_Storm_ID,
            log=False,
            aftercast_delay=250,
        )):
            return True

        if self.IsSkillEquipped(Flare_ID) and (yield from self.CastSkillID(
            skill_id=Flare_ID,
            log=False,
            aftercast_delay=250,
        )):
            return True

        if (yield from self.AutoAttack()):
            return True

        return False
