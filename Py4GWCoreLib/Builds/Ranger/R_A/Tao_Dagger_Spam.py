from Py4GWCoreLib import Profession
from Py4GWCoreLib import BuildMgr
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Agent, Party, Player
from Py4GWCoreLib.Skill import Skill
from Py4GWCoreLib.Builds.Any.HeroAI import HeroAI_Build
from Py4GWCoreLib.Builds.Skills import SkillsTemplate


Jagged_Strike_ID = Skill.GetID("Jagged_Strike")
Fox_Fangs_ID = Skill.GetID("Fox_Fangs")
Death_Blossom_ID = Skill.GetID("Death_Blossom")
Together_as_one_ID = Skill.GetID("Together_as_one")
Breath_of_the_Great_Dwarf_ID = Skill.GetID("Breath_of_the_Great_Dwarf")
Air_of_Superiority_ID = Skill.GetID("Air_of_Superiority")
Comfort_Animal_ID = Skill.GetID("Comfort_Animal")
I_Am_the_Strongest_ID = Skill.GetID("I_Am_the_Strongest")
Lightning_Reflexes_ID = Skill.GetID("Lightning_Reflexes")


class Tao_Dagger_Spam(BuildMgr):
    def __init__(self, match_only: bool = False):
        super().__init__(
            name="TaO Dagger Spam",
            required_primary=Profession.Ranger,
            required_secondary=Profession.Assassin,
            template_code="OgcTYr72Xyhhh5gZsGAAAAAAAAA",
            required_skills=[
                Jagged_Strike_ID,
                Fox_Fangs_ID,
                Death_Blossom_ID,
                Together_as_one_ID,
            ],
            optional_skills=[
                Breath_of_the_Great_Dwarf_ID,
                Comfort_Animal_ID,
                I_Am_the_Strongest_ID,
                Lightning_Reflexes_ID,
                Air_of_Superiority_ID
            ],
        )
        if match_only:
            return

        self.SetFallback("HeroAI", HeroAI_Build(standalone_fallback=True))
        self.SetSkillCastingFn(self._run_local_skill_logic)
        self.skills: SkillsTemplate = SkillsTemplate(self)
        self.dagger_target_type = "EnemyNearest"

    def _run_local_skill_logic(self):
        def _should_cast_comfort_animal() -> bool:
            pet_id = Party.Pets.GetPetID(Player.GetAgentID())
            if not pet_id:
                return False
            if not Agent.IsAlive(pet_id):
                return True
            return Agent.GetHealth(pet_id) < 0.30

        if not Routines.Checks.Skills.CanCast():
            return False

        if self.IsSkillEquipped(I_Am_the_Strongest_ID) and (yield from self.CastSkillID(
            skill_id=I_Am_the_Strongest_ID,
            log=False,
            aftercast_delay=250,
        )):
            return

        if self.IsSkillEquipped(Comfort_Animal_ID) and _should_cast_comfort_animal() and (yield from self.CastSkillID(
            skill_id=Comfort_Animal_ID,
            extra_condition=_should_cast_comfort_animal,
            log=False,
            aftercast_delay=250,
        )):
            return

        if self.IsSkillEquipped(Breath_of_the_Great_Dwarf_ID) and (yield from self.skills.Any.NoAttribute.Breath_of_the_Great_Dwarf()):
            return True
            
        if self.IsSkillEquipped(Air_of_Superiority_ID) and (yield from self.skills.Any.PvE.Air_of_Superiority()):
            return

        if not Routines.Checks.Agents.InAggro():
            return False

        if self.IsSkillEquipped(Lightning_Reflexes_ID) and (yield from self.CastSkillID(
            skill_id=Lightning_Reflexes_ID,
            log=False,
            aftercast_delay=250,
        )):
            return

        if (yield from self.skills.Ranger.Expertise.Together_as_One()):
            return True

        if (yield from self.skills.Assassin.DaggerMastery.Death_Blossom()):
            return True
        if (yield from self.skills.Assassin.DaggerMastery.Fox_Fangs()):
            return True
        if (yield from self.skills.Assassin.DaggerMastery.Jagged_Strike()):
            return True

        return False
