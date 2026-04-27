from Py4GWCoreLib import Profession
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Agent, Party, Player, Range
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build


Troll_Unguent_ID = Skill.GetID("Troll_Unguent")
Ignite_Arrows_ID = Skill.GetID("Ignite_Arrows")
Frenzy_ID = Skill.GetID("Frenzy")
Comfort_Animal_ID = Skill.GetID("Comfort_Animal")
Charm_animal_ID = Skill.GetID("Charm_Animal")
Resurrection_Signet_ID = Skill.GetID("Resurrection_Signet")
Read_the_Wind_ID = Skill.GetID("Read_the_Wind")


class Pre_Searing_Ignite(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="Pre-Searing ignite",
            required_primary=Profession.Ranger,
            required_secondary=Profession.Warrior,
            template_code="OgEUYlrh5cG++1aFAAAA0WAA",
            required_skills=[
                Troll_Unguent_ID,
                Resurrection_Signet_ID,
                Comfort_Animal_ID,
                Charm_animal_ID
            ],
            optional_skills=[Frenzy_ID, Read_the_Wind_ID, Ignite_Arrows_ID],
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

        if self.IsSkillEquipped(Comfort_Animal_ID):
            pet_id = Party.Pets.GetPetID(player_agent_id)
            if pet_id and (not Agent.IsAlive(pet_id) or Agent.GetHealth(pet_id) < 0.01):
                if (yield from self.CastSkillID(
                    skill_id=Comfort_Animal_ID,
                    log=False,
                    aftercast_delay=250,
                )):
                    return True

        if self.IsSkillEquipped(Troll_Unguent_ID):
            should_cast_troll = (
                Agent.GetHealth(player_agent_id) < 0.99
                and not Routines.Checks.Agents.HasEffect(player_agent_id, Troll_Unguent_ID)
                and not Routines.Checks.Agents.HasEffect(player_agent_id, Frenzy_ID)
            )
            if should_cast_troll and (yield from self.CastSkillID(
                skill_id=Troll_Unguent_ID,
                log=False,
                aftercast_delay=250,
            )):
                return True

        if not self.IsInAggro():
            return False

        if self.IsSkillEquipped(Ignite_Arrows_ID):
            should_cast_ignite = not Routines.Checks.Agents.HasEffect(player_agent_id, Ignite_Arrows_ID)
            if should_cast_ignite and (yield from self.CastSkillID(
                skill_id=Ignite_Arrows_ID,
                log=False,
                aftercast_delay=250,
            )):
                return True
        elif self.IsSkillEquipped(Read_the_Wind_ID):
            # Preparations do not stack. If Ignite Arrows is not equipped,
            # keep Read the Wind up as the default preparation.
            should_cast_read_the_wind = not Routines.Checks.Agents.HasEffect(player_agent_id, Read_the_Wind_ID)
            if should_cast_read_the_wind and (yield from self.CastSkillID(
                skill_id=Read_the_Wind_ID,
                log=False,
                aftercast_delay=250,
            )):
                return True

        if self.IsSkillEquipped(Frenzy_ID):
            should_cast_frenzy = (
                Agent.GetHealth(player_agent_id) > 0.95
                and not Routines.Checks.Agents.HasEffect(player_agent_id, Frenzy_ID)
            )
            if should_cast_frenzy and (yield from self.CastSkillID(
                skill_id=Frenzy_ID,
                log=False,
                aftercast_delay=250,
            )):
                return True

        if (yield from self.AutoAttack(target_type="EnemyClustered")):
            return True

        return False
