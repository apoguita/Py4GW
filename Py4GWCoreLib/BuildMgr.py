
from collections.abc import Generator
from typing import Any

#region build
class BuildMgr:
    from Py4GWCoreLib import Profession
    def __init__(
        
        self,
        name: str = "Generic Build",
        required_primary: Profession = Profession(0),
        required_secondary: Profession = Profession(0),
        template_code: str = "AAAAAAAAAAAAAAAA",
        skills: list[int] = []
    ):
        from Py4GWCoreLib import Profession
        self.build_name = name
        self.required_primary: Profession = required_primary
        self.required_secondary: Profession = required_secondary
        self.template_code = template_code
        self.skills = skills
        
    def ValidatePrimary(self, profession: Profession) -> bool:
        return self.required_primary == profession

    def ValidateSecondary(self, profession: Profession) -> bool:
        return self.required_secondary == profession
    
    def ValidateSkills(self) -> Generator[None, None, bool]:
        from Py4GWCoreLib import GLOBAL_CACHE
        from Py4GWCoreLib import Routines
        skills: list[int] = []
        for i in range(8):
            skill = GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(i+1)
            if skill:
                skills.append(skill)

        all_valid = sorted(self.skills) == sorted(skills)

        if not all_valid:
            wait_interval = 1000
        else:
            wait_interval = 0
        yield from Routines.Yield.wait(wait_interval)
        return all_valid


    def ProcessSkillCasting(self):
        """Override this in child classes for casting logic."""
        raise NotImplementedError
    
    def LoadSkillBar(self) -> Generator[Any, Any, None]:
        from Py4GWCoreLib import Routines
        """
        Load the skill bar with the build's template code.
        This method can be overridden in child classes if needed.
        """
        yield from Routines.Yield.Skills.LoadSkillbar(self.template_code, log=False)
    
