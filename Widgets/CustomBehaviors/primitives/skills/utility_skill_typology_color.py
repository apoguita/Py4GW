from enum import Enum

from Py4GWCoreLib.Py4GWcorelib import Utils
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class UtilitySkillTypologyColor:
    COMBAT_COLOR = Utils.ColorToTuple(Utils.RGBToColor(76, 151, 173, 200))
    LOOTING_COLOR = Utils.ColorToTuple(Utils.RGBToColor(229, 226, 70, 200))
    FOLLOWING_COLOR = Utils.ColorToTuple(Utils.RGBToColor(62, 139, 95, 200))
    BOTTING_COLOR = Utils.ColorToTuple(Utils.RGBToColor(131, 90, 146, 200))
    CHESTING_COLOR = Utils.ColorToTuple(Utils.RGBToColor(229, 226, 160, 200))
    DEAMON_COLOR = Utils.ColorToTuple(Utils.RGBToColor(150, 150, 150, 200))

    @staticmethod
    def get_color_from_typology(utility_skill_typology:UtilitySkillTypology) -> tuple[float, float, float, float]:
        if utility_skill_typology == UtilitySkillTypology.BOTTING:
            return UtilitySkillTypologyColor.BOTTING_COLOR
        if utility_skill_typology == UtilitySkillTypology.CHESTING:
            return UtilitySkillTypologyColor.CHESTING_COLOR
        if utility_skill_typology == UtilitySkillTypology.COMBAT:
            return UtilitySkillTypologyColor.COMBAT_COLOR
        if utility_skill_typology == UtilitySkillTypology.DEAMON:
            return UtilitySkillTypologyColor.DEAMON_COLOR
        if utility_skill_typology == UtilitySkillTypology.FOLLOWING:
            return UtilitySkillTypologyColor.FOLLOWING_COLOR
        if utility_skill_typology == UtilitySkillTypology.LOOTING:
            return UtilitySkillTypologyColor.LOOTING_COLOR
            
        return Utils.ColorToTuple(Utils.RGBToColor(255, 255, 255, 200))