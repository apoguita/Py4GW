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

    @staticmethod
    def get_skill_ids_in_game_build(without_events:bool = True) -> list[tuple[int, int]]:
        '''
        return in-game build of the player as a list of skill_ids.
        this is much more lightweight than get_in_game_build.
        GLOBAL_CACHE.Skill.GetName is very expensive
        '''
        skill_ids:list[tuple[int, int]] = []
        
        for i in range(8):
            skill_data = GLOBAL_CACHE.SkillBar.GetSkillData(i + 1)
            skill_id = skill_data.id.id
            skill_slot = i + 1
            skill_ids.append((skill_id, skill_slot))

        return skill_ids