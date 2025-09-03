import os
import pathlib
import re
import sys
from Py4GWCoreLib import IconsFontAwesome5, ImGui, Player, PyImGui
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Py4GWcorelib import Color, Utils
from Widgets.CustomBehaviors.primitives.skillbars.custom_behavior_base_utility import CustomBehaviorBaseUtility
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_shared_memory import CustomBehaviorWidgetMemoryManager
from Widgets.CustomBehaviors.primitives.skills.bonds.per_type.custom_buff_target import BuffConfigurationPerProfession
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase
from Widgets.CustomBehaviors.primitives.constants import DEBUG
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology import UtilitySkillTypology
from Widgets.CustomBehaviors.primitives.skills.utility_skill_typology_color import UtilitySkillTypologyColor

shared_data = CustomBehaviorWidgetMemoryManager().GetCustomBehaviorWidgetData()
WITH_DETAIL = False

@staticmethod
def render():
    global WITH_DETAIL

    current_build:CustomBehaviorBaseUtility | None = CustomBehaviorLoader().custom_combat_behavior
    if current_build is None:
        PyImGui.text(f"Current build is None.")
        if PyImGui.button(f"{IconsFontAwesome5.ICON_SYNC} Search build again"):
            CustomBehaviorLoader().refresh_custom_behavior_candidate()
        return

    if DEBUG:
        # PyImGui.same_line(0, 10)
        PyImGui.text(f"HasLoaded : {CustomBehaviorLoader()._has_loaded}")
        # PyImGui.same_line(0, 10)
        PyImGui.text(f"Selected template : {CustomBehaviorLoader().custom_combat_behavior.__class__.__name__}")
        if CustomBehaviorLoader().custom_combat_behavior is not None:
            PyImGui.text(f"Account state:{CustomBehaviorLoader().custom_combat_behavior.get_state()}")
            PyImGui.text(f"Final state:{CustomBehaviorLoader().custom_combat_behavior.get_final_state()}")
    

        if CustomBehaviorLoader().custom_combat_behavior.get_is_enabled():
            if PyImGui.button(f"{IconsFontAwesome5.ICON_TIMES} Disable"):
                CustomBehaviorLoader().custom_combat_behavior.disable()
        else:
            if PyImGui.button(f"{IconsFontAwesome5.ICON_CHECK} Enable"):
                CustomBehaviorLoader().custom_combat_behavior.enable()
        pass
    
    # if current_build is not None and type(current_build).mro()[1].__name__ != CustomBehaviorBaseUtility.__name__:
    #     PyImGui.separator()
    #     PyImGui.text(f"Generic skills : ")
    #     generic_behavior_build:list[CustomSkill] = current_build.get_generic_behavior_build()
    #     if generic_behavior_build is not None:
    #         for skill in generic_behavior_build:
    #             PyImGui.text(f"bbb {skill.skill_name}")

    # print(type(current_build))
    # print(CustomBehaviorBaseUtility)
    # print(type(current_build).mro()[1].__name__)  # Should be CustomBehaviorBaseUtility
    # print(id(CustomBehaviorBaseUtility))
    # print('CustomBehaviorBaseUtility' in type(current_build).mro()[0].__name__)
    # and isinstance(current_build, CustomBehaviorBaseUtility)
    # print(type(current_build).mro()[1].__name__ == CustomBehaviorBaseUtility.__name__)

    if current_build is not None and type(current_build).mro()[1].__name__ == CustomBehaviorBaseUtility.__name__:
        PyImGui.separator()
        # PyImGui.text(f"Generic skills - Utility system : ")
        instance: CustomBehaviorBaseUtility = current_build 
        # utilities: list[CustomSkillUtilityBase] = instance.get_skills_final_list()

        # for utility in utilities:
        #     PyImGui.text(f"{utility.custom_skill.skill_name} {utility.additive_score_weight}")

        PyImGui.text(f"Utility system : ")
        PyImGui.same_line(0, -1)
        WITH_DETAIL = PyImGui.checkbox("with detail", WITH_DETAIL)

        scores: list[tuple[CustomSkillUtilityBase, float | None]] = instance.get_all_scores()
        if PyImGui.begin_table("skill", 2, int(PyImGui.TableFlags.SizingStretchProp)):
            PyImGui.table_setup_column("A")
            PyImGui.table_setup_column("B")
            # PyImGui.table_headers_row()

        for score in scores:
            
            def label_generic_utility(utility: CustomSkillUtilityBase) -> str:
                if utility.__class__.__name__ == "HeroAiUtility":
                    return f"{IconsFontAwesome5.ICON_GAMEPAD} "
                return ""

            current_path = pathlib.Path.cwd()
            prefix = ""
            if "Widgets" not in str(current_path):
                prefix = "Widgets\\"

            score_text = f"{score[1]:06.2f}" if score[1] is not None else "Ø"
            texture_file = prefix + GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(score[0].custom_skill.skill_id)
            texture_file = score[0].custom_skill.get_texture()
            
            PyImGui.table_next_row()
            PyImGui.table_next_column()

            if score[0].is_enabled and CustomBehaviorParty().get_typology_is_enabled(score[0].utility_skill_typology) and CustomBehaviorParty().get_party_is_enabled():
                if score[0].utility_skill_typology == UtilitySkillTypology.FOLLOWING:
                    PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.FOLLOWING_COLOR)
                elif score[0].utility_skill_typology == UtilitySkillTypology.COMBAT:
                    PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.COMBAT_COLOR)
                elif score[0].utility_skill_typology == UtilitySkillTypology.BOTTING:
                    PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.BOTTING_COLOR)
                elif score[0].utility_skill_typology == UtilitySkillTypology.LOOTING:
                    PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.LOOTING_COLOR)
                elif score[0].utility_skill_typology == UtilitySkillTypology.CHESTING:
                    PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.CHESTING_COLOR)
                elif score[0].utility_skill_typology == UtilitySkillTypology.DEAMON:
                    PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Border, UtilitySkillTypologyColor.DEAMON_COLOR)
                else:
                    PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 0)
                    PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 255, 255, 200)))
                    
                if ImGui.ImageButton(f"{score[0].custom_skill.skill_name}", texture_file, 35, 35):
                    score[0].is_enabled = False
                    
                PyImGui.pop_style_var(1)
                PyImGui.pop_style_color(1)
                
            else:
                PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)
                PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(255, 0, 0, 255)))
                if ImGui.ImageButton(f"{score[0].custom_skill.skill_name}", texture_file, 35,35):
                    score[0].is_enabled = True
                PyImGui.pop_style_var(1)
                PyImGui.pop_style_color(1)
                PyImGui.same_line(10, 0)
                ImGui.DrawTexture(prefix + f"CustomBehaviors\\gui\\textures\\x.png", 20, 20)

            # ImGui.DrawTexture(texture_file, 50, 50)
            PyImGui.table_next_column()
            
            skill : CustomSkillUtilityBase = score[0]
            PyImGui.text(f"{skill.custom_skill.skill_name} - Slot:{skill.custom_skill.skill_slot}")
            
            PyImGui.bullet_text("score")
            PyImGui.same_line(0, -1)
            PyImGui.text_colored(f"{label_generic_utility(skill)}{score_text}", Color(0, 255, 0, 255).to_tuple_normalized())

            if WITH_DETAIL:
                PyImGui.bullet_text("required ressource")
                PyImGui.same_line(0, -1)
                PyImGui.text_colored(f"{skill.mana_required_to_cast}",  Utils.RGBToNormal(27, 126, 246, 255))
                PyImGui.bullet_text(f"allowed in : {[x.name for x in skill.allowed_states]}")
                PyImGui.bullet_text(f"pre_check : {skill.are_common_pre_checks_valid(instance.get_final_state())}")

                buff_configuration: BuffConfigurationPerProfession | None = skill.get_buff_configuration()
                if buff_configuration is not None:
                    PyImGui.bullet_text(f"Buff configuration : ")
                    for profession in BuffConfigurationPerProfession.ALL_PROFESSIONS:
                        PyImGui.same_line(0, 5)

                        buff_configuration_per_profession = buff_configuration.get_by_profession(profession)

                        prefix_root_folder = ""
                        if "Widgets" in str(current_path):
                            prefix_root_folder = "..\\"

                        texture_path =  prefix_root_folder + f"Textures\\Profession_Icons\\[{profession.value}] - {profession.name}.png"
                        icon_size = 26

                        if buff_configuration_per_profession.is_activated:
                            PyImGui.push_style_var(ImGui.ImGuiStyleVar.FrameBorderSize, 3)  # 1px border
                            PyImGui.push_style_color(PyImGui.ImGuiCol.Border, Utils.ColorToTuple(Utils.RGBToColor(3, 244, 60, 255)))
                            if ImGui.ImageButton(f"deactivate_{skill.custom_skill.skill_id}_{profession.name}", texture_path, icon_size, icon_size):
                                buff_configuration_per_profession.is_activated = False
                            ImGui.show_tooltip(f"Deactivate buff for {profession.name}")    
                            PyImGui.pop_style_var(1)
                            PyImGui.pop_style_color(1)
                        else:
                            if ImGui.ImageButton(f"activate_{skill.custom_skill.skill_id}_{profession.name}", texture_path, icon_size, icon_size):
                                buff_configuration_per_profession.is_activated = True
                            ImGui.show_tooltip(f"Activate buff for {profession.name}")

                skill.customized_debug_ui(instance.get_final_state())

            PyImGui.table_next_row()

        PyImGui.end_table()









            

