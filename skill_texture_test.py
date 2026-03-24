import PyImGui
import PySkill

from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.Item import Item
from Py4GWCoreLib.ItemArray import ItemArray

MODULE_NAME = "Skill Texture Test"
SKILL_ID = 330 #2235
ICON_SIZE = 256.0


def _make_texture_key(file_id: int) -> str:
    return f"gwdat://{int(file_id)}" if int(file_id or 0) > 0 else ""


def _get_skill_file_id(skill, *names: str) -> int:
    for name in names:
        value = getattr(skill, name, 0)
        if value:
            return int(value)
    return 0


def _draw_texture_row(label: str, file_id: int, texture_key: str, extra_text: str = ""):
    PyImGui.text(label)
    PyImGui.text(f"File ID: {int(file_id or 0)}")
    if extra_text:
        PyImGui.text(extra_text)
    if texture_key:
        ImGui.DrawTexture(texture_key, ICON_SIZE, ICON_SIZE)
        PyImGui.text(texture_key)
    else:
        PyImGui.text("No file id resolved")
    PyImGui.separator()


def _get_skill_texture_keys() -> list[tuple[str, int, str]]:
    skill = PySkill.Skill(SKILL_ID)
    skill.GetContext()
    sources = [
        ("Skill Icon", _get_skill_file_id(skill, "icon_file_id")),
        ("Skill Icon Hi Res", _get_skill_file_id(skill, "icon_file2_id", "icon_file_id_2")),
    ]
    return [(label, file_id, _make_texture_key(file_id)) for label, file_id in sources]


def _get_first_inventory_item_texture_key() -> tuple[int, int, str]:
    bags = ItemArray.CreateBagList(1, 2, 3, 4)
    item_ids = ItemArray.GetItemArray(bags)
    if not item_ids:
        return 0, 0, ""

    item_id = int(item_ids[0] or 0)
    file_id = int(Item.GetModelFileID(item_id) or 0) if item_id > 0 else 0
    texture_key = _make_texture_key(file_id)
    return item_id, file_id, texture_key


def main():
    skill_textures = _get_skill_texture_keys()
    item_id, item_file_id, item_texture_key = _get_first_inventory_item_texture_key()

    if PyImGui.begin(MODULE_NAME):
        PyImGui.text(f"Skill ID: {SKILL_ID}")
        PyImGui.separator()

        for label, file_id, texture_key in skill_textures:
            _draw_texture_row(label, file_id, texture_key)

        _draw_texture_row(
            "First Inventory Item",
            item_file_id,
            item_texture_key,
            extra_text=f"Item ID: {item_id}",
        )

    PyImGui.end()


if __name__ == "__main__":
    main()
