from enum import Enum, IntEnum
import os

from Py4GWCoreLib.ImGui import ImGui
from Py4GWCoreLib.Py4GWcorelib import ConsoleLog
from Py4GWCoreLib.enums import Profession

core_texture_path = __file__.replace("texture_map.py", "textures/")

class TextureState(IntEnum):
    Normal = 0
    Hovered = 1
    Active = 2
    Disabled = 3
    
class MapTexture():
    def __init__(self, texture : str, texture_size : tuple[float, float], size: tuple[float, float], normal:tuple[float, float] = (0, 0), hovered : tuple[float, float] | None = None, active : tuple[float, float] | None = None, disabled : tuple[float, float] | None = None):        
        self.size = size
        self.width = size[0]
        self.height = size[1]
        
        self.texture = texture        
        self.texture_size = texture_size
        
        self.normal_offset : tuple[float, float, float, float] = (normal[0] / texture_size[0], normal[1] / texture_size[1], (normal[0] + size[0]) / texture_size[0], (normal[1] + size[1]) / texture_size[1])
        self.hovered_offset : tuple[float, float, float, float] = (hovered[0] / texture_size[0], hovered[1] / texture_size[1], (hovered[0] + size[0]) / texture_size[0], (hovered[1] + size[1]) / texture_size[1]) if hovered else (0, 0, 1, 1)
        self.active_offset : tuple[float, float, float, float] =  (active[0] / texture_size[0], active[1] / texture_size[1], (active[0] + size[0]) / texture_size[0], (active[1] + size[1]) / texture_size[1]) if active else (0, 0, 1, 1)
        self.disabled_offset : tuple[float, float, float, float] = (disabled[0] / texture_size[0], disabled[1] / texture_size[1], (disabled[0] + size[0]) / texture_size[0], (disabled[1] + size[1]) / texture_size[1]) if disabled else (0, 0, 1, 1)
    
    def get_uv(self, state: TextureState) -> tuple[float, float, float, float]:
        if state == TextureState.Normal:
            return self.normal_offset
        elif state == TextureState.Hovered:
            return self.hovered_offset
        elif state == TextureState.Active:
            return self.active_offset
        elif state == TextureState.Disabled:
            return self.disabled_offset
    
    def draw(self, size : tuple[float, float], state: TextureState = TextureState.Normal, tint = (255, 255, 255, 255), border_color = (255, 255, 255, 0)):        
        uv = self.get_uv(state)        
        ImGui.DrawTextureExtended(self.texture, size, (uv[0], uv[1]), (uv[2], uv[3]), tint, border_color)

class CoreTextures(Enum):
    PROFESSION_ICON_SQUARE = "profession_icon_square_{}.png"
    PROFESSION_ICON_SQUARE_HOVERED = "profession_icon_square_{}_hovered.png"
    
    Down_Arrows = MapTexture(
        texture = os.path.join(core_texture_path, "GW.EXE_0x38C59CC8.png"),
        texture_size = (128, 64),
        size = (32, 32),
        normal=(0, 0),
        hovered=(32, 0),
        active=(64, 0),
        disabled=(96, 0),
    )
    Up_Arrows = MapTexture(
        texture = os.path.join(core_texture_path, "GW.EXE_0x38C59CC8.png"),
        texture_size = (128, 64),
        size = (32, 32),
        normal=(0, 32),
        hovered=(32, 32),
        active=(64, 32),
        disabled=(96, 32),
    )

    @staticmethod
    def get_profession_texture(profession: Profession, hovered: bool = False) -> str:

        if hovered:
            return os.path.join(core_texture_path, CoreTextures.PROFESSION_ICON_SQUARE_HOVERED.value.format(profession.name.lower()))

        return CoreTextures.PROFESSION_ICON_SQUARE.value.format(profession.name.lower())

    Assassin = os.path.join(core_texture_path, PROFESSION_ICON_SQUARE.format(
        Profession.Assassin.name.lower()))
    Assassin_Hovered = os.path.join(
        core_texture_path, PROFESSION_ICON_SQUARE_HOVERED.format(Profession.Assassin.name.lower()))
    Elementalist = os.path.join(core_texture_path, PROFESSION_ICON_SQUARE.format(
        Profession.Elementalist.name.lower()))
    Elementalist_Hovered = os.path.join(
        core_texture_path, PROFESSION_ICON_SQUARE_HOVERED.format(Profession.Elementalist.name.lower()))
    Mesmer = os.path.join(core_texture_path, PROFESSION_ICON_SQUARE.format(
        Profession.Mesmer.name.lower()))
    Mesmer_Hovered = os.path.join(
        core_texture_path, PROFESSION_ICON_SQUARE_HOVERED.format(Profession.Mesmer.name.lower()))
    Monk = os.path.join(core_texture_path, PROFESSION_ICON_SQUARE.format(
        Profession.Monk.name.lower()))
    Monk_Hovered = os.path.join(
        core_texture_path, PROFESSION_ICON_SQUARE_HOVERED.format(Profession.Monk.name.lower()))
    Necromancer = os.path.join(core_texture_path, PROFESSION_ICON_SQUARE.format(
        Profession.Necromancer.name.lower()))
    Necromancer_Hovered = os.path.join(
        core_texture_path, PROFESSION_ICON_SQUARE_HOVERED.format(Profession.Necromancer.name.lower()))
    Ranger = os.path.join(core_texture_path, PROFESSION_ICON_SQUARE.format(
        Profession.Ranger.name.lower()))
    Ranger_Hovered = os.path.join(
        core_texture_path, PROFESSION_ICON_SQUARE_HOVERED.format(Profession.Ranger.name.lower()))
    Ritualist = os.path.join(core_texture_path, PROFESSION_ICON_SQUARE.format(
        Profession.Ritualist.name.lower()))
    Ritualist_Hovered = os.path.join(
        core_texture_path, PROFESSION_ICON_SQUARE_HOVERED.format(Profession.Ritualist.name.lower()))
    Paragon = os.path.join(core_texture_path, PROFESSION_ICON_SQUARE.format(
        Profession.Paragon.name.lower()))
    Paragon_Hovered = os.path.join(
        core_texture_path, PROFESSION_ICON_SQUARE_HOVERED.format(Profession.Paragon.name.lower()))
    Dervish = os.path.join(core_texture_path, PROFESSION_ICON_SQUARE.format(
        Profession.Dervish.name.lower()))
    Dervish_Hovered = os.path.join(
        core_texture_path, PROFESSION_ICON_SQUARE_HOVERED.format(Profession.Dervish.name.lower()))
    Warrior = os.path.join(core_texture_path, PROFESSION_ICON_SQUARE.format(
        Profession.Warrior.name.lower()))
    Warrior_Hovered = os.path.join(
        core_texture_path, PROFESSION_ICON_SQUARE_HOVERED.format(Profession.Warrior.name.lower()))
    UI_Checkmark = os.path.join(core_texture_path, "ui_checkmark.png")
    UI_Checkmark_Hovered = os.path.join(core_texture_path, "ui_checkmark_hovered.png")
    Cancel = os.path.join(core_texture_path, "cancel.png")
    Cog = os.path.join(core_texture_path, "cog.png")
    UI_Cancel = os.path.join(core_texture_path, "ui_cancel.png")
    UI_Cancel_Hovered = os.path.join(core_texture_path, "ui_cancel_hovered.png")
    UI_Reward_Bag = os.path.join(core_texture_path, "ui_reward_bag.png")
    UI_Reward_Bag_Hovered = os.path.join(core_texture_path, "ui_reward_bag_hovered.png")
    UI_Backpack = os.path.join(core_texture_path, "ui_backpack.png")
    UI_Destroy = os.path.join(core_texture_path, "ui_destroy.png")
    UI_Show_Always = os.path.join(core_texture_path, "ui_show_always.png")
    UI_Show_Always_Hovered = os.path.join(core_texture_path, "ui_show_always_hovered.png")
    UI_Show_Explorable = os.path.join(core_texture_path, "ui_show_explorable.png")
    UI_Show_Explorable_Hovered = os.path.join(core_texture_path, "ui_show_explorable_hovered.png")
    UI_Show_Never = os.path.join(core_texture_path, "ui_show_never.png")
    UI_Show_Never_Hovered = os.path.join(core_texture_path, "ui_show_never_hovered.png")
    UI_Show_PvP = os.path.join(core_texture_path, "ui_show_pvp.png")
    UI_Show_PvP_Hovered = os.path.join(core_texture_path, "ui_show_pvp_hovered.png")
    UI_Inventory_Slot = os.path.join(core_texture_path, "ui_inventory_slot_background_ex.png")
    UI_Platinum = os.path.join(core_texture_path, "ui_platinum.png")
    UI_Gold = os.path.join(core_texture_path, "ui_gold.png")
        
    UI_Help_Icon = os.path.join(core_texture_path, "ui_help_icon.png")
    UI_Help_Icon_Hovered = os.path.join(core_texture_path, "ui_help_icon_hovered.png")
    UI_Help_Icon_Active = os.path.join(core_texture_path, "ui_help_icon_active.png")
