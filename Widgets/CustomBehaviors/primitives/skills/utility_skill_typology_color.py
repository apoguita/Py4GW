from enum import Enum

from Py4GWCoreLib.Py4GWcorelib import Utils
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology

class UtilitySkillTypologyColor:
    COMBAT_COLOR = Utils.ColorToTuple(Utils.RGBToColor(76, 151, 173, 200))
    LOOTING_COLOR = Utils.ColorToTuple(Utils.RGBToColor(229, 226, 70, 200))
    FOLLOWING_COLOR = Utils.ColorToTuple(Utils.RGBToColor(62, 139, 95, 200))
    BOTTING_COLOR = Utils.ColorToTuple(Utils.RGBToColor(131, 90, 146, 200))
    CHESTING_COLOR = Utils.ColorToTuple(Utils.RGBToColor(229, 226, 160, 200))
    DAEMON_COLOR = Utils.ColorToTuple(Utils.RGBToColor(150, 150, 150, 200))
    BLESSING_COLOR = Utils.ColorToTuple(Utils.RGBToColor(255, 143, 62, 200))
    INVENTORY_COLOR = Utils.ColorToTuple(Utils.RGBToColor(30, 143, 62, 200))
    FLAG_COLOR = Utils.ColorToTuple(Utils.RGBToColor(147, 217, 32, 250))

    @staticmethod
    def get_color_from_typology(utility_skill_typology:UtilitySkillTypology) -> tuple[float, float, float, float]:
        if utility_skill_typology.value == UtilitySkillTypology.BOTTING.value:
            return UtilitySkillTypologyColor.BOTTING_COLOR
        if utility_skill_typology == UtilitySkillTypology.CHESTING:
            return UtilitySkillTypologyColor.CHESTING_COLOR
        if utility_skill_typology == UtilitySkillTypology.COMBAT:
            return UtilitySkillTypologyColor.COMBAT_COLOR
        if utility_skill_typology == UtilitySkillTypology.DAEMON:
            return UtilitySkillTypologyColor.DAEMON_COLOR
        if utility_skill_typology == UtilitySkillTypology.FOLLOWING:
            return UtilitySkillTypologyColor.FOLLOWING_COLOR
        if utility_skill_typology == UtilitySkillTypology.LOOTING:
            return UtilitySkillTypologyColor.LOOTING_COLOR
        if utility_skill_typology == UtilitySkillTypology.BLESSING:
            return UtilitySkillTypologyColor.BLESSING_COLOR
        if utility_skill_typology == UtilitySkillTypology.INVENTORY:
            return UtilitySkillTypologyColor.INVENTORY_COLOR
        
        print(f"Unknown typology {utility_skill_typology}")
        return Utils.ColorToTuple(Utils.RGBToColor(255, 2, 255, 200))