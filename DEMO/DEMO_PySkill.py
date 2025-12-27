# Import all req# Necessary Imports
import Py4GW        #Miscelanious functions and classes
import PyImGui     #ImGui wrapper
import PySkill      #Skill functions and classes

# End Necessary Imports

module_name = "PySkill_DEMO"

input_skill_id = 0

def DrawWindow():
    global module_name
    global input_skill_id
    
    if PyImGui.begin(module_name):
        
        # Input field for Skill ID
        input_skill_id = PyImGui.input_int("Skill ID", input_skill_id)
        PyImGui.separator()
        
        if input_skill_id != 0:
            # Create Skill instance based on input
            skill_instance = PySkill.Skill(input_skill_id)
            
            # Basic skill information
            # Basic skill information
            PyImGui.text(f"Skill ID: {skill_instance.id.id}")
            PyImGui.text(f"Skill Name: {skill_instance.id.GetName()}")
            PyImGui.text(f"Skill Type: {skill_instance.type.GetName()}")
            PyImGui.text(f"Profession: {skill_instance.profession.GetName()}")
            PyImGui.text(f"Attribute: {skill_instance.attribute.GetName()}")
            PyImGui.separator()
            
            # Skill Costs and Timers
            PyImGui.text(f"Energy Cost: {skill_instance.energy_cost}")
            PyImGui.text(f"Health Cost: {skill_instance.health_cost}")
            PyImGui.text(f"Adrenaline Cost: {skill_instance.adrenaline}")
            PyImGui.text(f"Overcast: {skill_instance.overcast}")
            PyImGui.text(f"Activation Time: {skill_instance.activation}")
            PyImGui.text(f"Aftercast Time: {skill_instance.aftercast}")
            PyImGui.text(f"Recharge Time: {skill_instance.recharge}")
            PyImGui.separator()

            # Skill Flags and Range
            PyImGui.text(f"Is Touch Range: {'Yes' if skill_instance.is_touch_range else 'No'}")
            PyImGui.text(f"Is Elite: {'Yes' if skill_instance.is_elite else 'No'}")
            PyImGui.text(f"Is Half Range: {'Yes' if skill_instance.is_half_range else 'No'}")
            PyImGui.text(f"Is PvP: {'Yes' if skill_instance.is_pvp else 'No'}")
            PyImGui.text(f"Is PvE: {'Yes' if skill_instance.is_pve else 'No'}")
            PyImGui.text(f"Is Playable: {'Yes' if skill_instance.is_playable else 'No'}")
            PyImGui.text(f"AoE Range: {skill_instance.aoe_range}")
            PyImGui.separator()
            
            # Duration and Scaling Information
            if PyImGui.collapsing_header("Duration and Scaling"):
                PyImGui.text(f"Duration (0 points): {skill_instance.duration_0pts}")
                PyImGui.text(f"Duration (15 points): {skill_instance.duration_15pts}")
                PyImGui.text(f"Scale (0 points): {skill_instance.scale_0pts}")
                PyImGui.text(f"Scale (15 points): {skill_instance.scale_15pts}")
                PyImGui.text(f"Bonus Scale (0 points): {skill_instance.bonus_scale_0pts}")
                PyImGui.text(f"Bonus Scale (15 points): {skill_instance.bonus_scale_15pts}")
                PyImGui.separator()

            # Combo and Skill Arguments
            if PyImGui.collapsing_header("Combo and Arguments"):
                PyImGui.text(f"Combo Requirement: {skill_instance.combo_req}")
                PyImGui.text(f"Combo Effect: {skill_instance.combo}")
                PyImGui.text(f"Skill Arguments: {skill_instance.skill_arguments}")
                PyImGui.text(f"Target: {skill_instance.target}")
                PyImGui.separator()

            # Weapon and Condition Requirements
            if PyImGui.collapsing_header("Weapon and Condition Requirements"):
                PyImGui.text(f"Weapon Requirement: {skill_instance.weapon_req}")
                PyImGui.text(f"Condition: {skill_instance.condition}")
                PyImGui.text(f"Effect 1: {skill_instance.effect1}")
                PyImGui.text(f"Effect 2: {skill_instance.effect2}")
                PyImGui.text(f"Special: {skill_instance.special}")
                PyImGui.separator()

            # Campaign, Titles, and Skill Information
            if PyImGui.collapsing_header("Campaign, Titles, and Skill Info"):
                PyImGui.text(f"Campaign: {skill_instance.campaign.GetName()}")
                PyImGui.text(f"Title ID: {skill_instance.title}")
                PyImGui.text(f"PvP Skill ID: {skill_instance.id_pvp}")
                PyImGui.separator()

            # Animations and Icon Information
            if PyImGui.collapsing_header("Animations and Icons"):
                PyImGui.text(f"Caster Overhead Animation ID: {skill_instance.caster_overhead_animation_id}")
                PyImGui.text(f"Caster Body Animation ID: {skill_instance.caster_body_animation_id}")
                PyImGui.text(f"Target Body Animation ID: {skill_instance.target_body_animation_id}")
                PyImGui.text(f"Target Overhead Animation ID: {skill_instance.target_overhead_animation_id}")
                PyImGui.text(f"Projectile Animation 1 ID: {skill_instance.projectile_animation1_id}")
                PyImGui.text(f"Projectile Animation 2 ID: {skill_instance.projectile_animation2_id}")
                PyImGui.text(f"Icon File ID: {skill_instance.icon_file_id}")
                PyImGui.text(f"Icon File ID 2: {skill_instance.icon_file2_id}")
                PyImGui.separator()

            # Skill Descriptions
            if PyImGui.collapsing_header("Skill Descriptions"):
                PyImGui.text(f"Skill Name ID: {skill_instance.name_id}")
                PyImGui.text(f"Concise Description ID: {skill_instance.concise}")
                PyImGui.text(f"Full Description ID: {skill_instance.description_id}")
                PyImGui.separator()

            # Additional Flags and Miscellaneous
            if PyImGui.collapsing_header("Additional Flags and Miscellaneous"):
                PyImGui.text(f"Is Stacking: {'Yes' if skill_instance.is_stacking else 'No'}")
                PyImGui.text(f"Is Non-Stacking: {'Yes' if skill_instance.is_non_stacking else 'No'}")
                PyImGui.text(f"Is Unused: {'Yes' if skill_instance.is_unused else 'No'}")
                PyImGui.separator()

        PyImGui.end()

# main() must exist in every script and is the entry point for your plugin's execution.
def main():
    try:
        DrawWindow()
    
    # Handle specific exceptions to provide detailed error messages
    except ImportError as e:
        Py4GW.Console.Log("PySkill_DEMO", f"ImportError encountered: {str(e)}")
    except ValueError as e:
        Py4GW.Console.Log("PySkill_DEMO", f"ValueError encountered: {str(e)}")
    except Exception as e:
        Py4GW.Console.Log("PySkill_DEMO", f"Unexpected error encountered: {str(e)}")
    finally:
        pass  # Replace with your actual code

# This ensures that main() is called when the script is executed directly.
if __name__ == "__main__":
    main()
