from Py4GWCoreLib import GLOBAL_CACHE
from Sources.oazix.CustomBehaviors.primitives.skills.custom_skill import CustomSkill

class CustomBehaviorSkillbarManagement():

    def __init__(self):
        pass

    @staticmethod
    def get_in_game_build() -> dict[int, "CustomSkill"]:
        """
        return in-game build of the player as a dictionary.
        list length can vary.
        can be per skill_id as this is only used in town.
        """
        ordered_skills_by_skill_id: dict[int, "CustomSkill"] = {}
        for i in range(8):
            skill_id = GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(i + 1)
            if skill_id == 0: continue
            skill_name =  GLOBAL_CACHE.Skill.GetName(skill_id)
            custom_skill = CustomSkill(skill_name)
            ordered_skills_by_skill_id[skill_id] = custom_skill

        return ordered_skills_by_skill_id