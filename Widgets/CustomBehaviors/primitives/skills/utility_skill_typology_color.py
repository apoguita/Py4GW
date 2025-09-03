from enum import Enum

from Py4GWCoreLib.Py4GWcorelib import Utils

class UtilitySkillTypologyColor:
    COMBAT_COLOR = Utils.ColorToTuple(Utils.RGBToColor(76, 151, 173, 200))
    LOOTING_COLOR = Utils.ColorToTuple(Utils.RGBToColor(229, 226, 70, 200))
    FOLLOWING_COLOR = Utils.ColorToTuple(Utils.RGBToColor(62, 139, 95, 200))
    BOTTING_COLOR = Utils.ColorToTuple(Utils.RGBToColor(131, 90, 146, 200))
    CHESTING_COLOR = Utils.ColorToTuple(Utils.RGBToColor(229, 226, 160, 200))
    DEAMON_COLOR = Utils.ColorToTuple(Utils.RGBToColor(150, 150, 150, 200))