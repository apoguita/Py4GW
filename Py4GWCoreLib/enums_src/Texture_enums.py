import os.path
import Py4GW
import PySkill

from Py4GWCoreLib.enums_src.Model_enums import ModelID

FILE_NOT_FOUND_TEXTURE_PATH = os.path.join(Py4GW.Console.get_projects_path(), "Textures\\0-File_Not_found.png")
ITEM_MODEL_TEXTURE_PATH = "Textures\\Items"
SKILL_TEXTURE_PATH = "Textures\\Skills"


def get_texture_for_item(model_id: int | ModelID) -> str:
    basepath = os.path.join(Py4GW.Console.get_projects_path(), ITEM_MODEL_TEXTURE_PATH)

    if isinstance(model_id, int):
        try:
            model_id = ModelID(model_id)
        except ValueError:
            return FILE_NOT_FOUND_TEXTURE_PATH

    path = os.path.join(basepath, str(model_id.value).zfill(5) + "-" + model_id.name + ".png")
    if not os.path.isfile(path):
        return FILE_NOT_FOUND_TEXTURE_PATH

    return path

def get_formatted_skill_name(skill: PySkill.SkillID) -> str:
    skill_name = skill.GetName()
    for i in ['_kurzick', '_luxon']:
        skill_name = skill_name.replace(i, '')
    if skill.id == 2808:
        skill_name = "Enraged_Smash_Pvp"
    return skill_name


def get_texture_for_skill(skill_id: int | PySkill.SkillID) -> str:
    basepath = os.path.join(Py4GW.Console.get_projects_path(), SKILL_TEXTURE_PATH)

    if isinstance(skill_id, int):
        try:
            skill_id = PySkill.SkillID(skill_id)
        except ValueError:
            return FILE_NOT_FOUND_TEXTURE_PATH

    path = os.path.join(basepath, str(skill_id.id).zfill(4) + "-" + get_formatted_skill_name(skill_id) + ".jpg")

    if not os.path.isfile(path):
        return FILE_NOT_FOUND_TEXTURE_PATH

    return path

# region ProfessionTextures
ProfessionTextureMap = {
    1: "[1] - Warrior.png",
    2: "[2] - Ranger.png",
    3: "[3] - Monk.png",
    4: "[4] - Necromancer.png",
    5: "[5] - Mesmer.png",
    6: "[6] - Elementalist.png",
    7: "[7] - Assassin.png",
    8: "[8] - Ritualist.png",
    9: "[9] - Paragon.png",
    10: "[10] - Dervish.png",
}
