import PyImGui

from Py4GWCoreLib import ImGui
from Py4GWCoreLib.Item import Item

ICON_SIZE = 256.0

class ItemTexture:
    @staticmethod
    def _make_texture_key(file_id: int) -> str:
        return f"gwdat://{int(file_id)}" if int(file_id or 0) > 0 else ""
    
    @staticmethod
    def _get_item_texture(item_id : int) -> tuple[int, int, str]:
        file_id = int(Item.GetModelFileID(item_id) or 0) if item_id > 0 else 0
        texture_key = ItemTexture._make_texture_key(file_id)
        return item_id, file_id, texture_key
    
    @staticmethod
    def _draw_ui_texture():
        file_id = int(0xD84CFDA9)
        texture_key = ItemTexture._make_texture_key(file_id)
        ImGui.DrawTexture(texture_key, ICON_SIZE, ICON_SIZE)
        
    @staticmethod
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