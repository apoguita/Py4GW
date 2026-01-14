# Necessary Imports
import Py4GW        #Miscelanious functions and classes
import PyImGui     #ImGui wrapper
import PySkill      #Skill functions and classes
import PySkillbar   #Skillbar functions and classes

# End Necessary Imports


Module_Name = "Skillbar_DEMO"

input_skillbar_index = 0  # Input field to select a skill index
skillbar_instance = PySkillbar.Skillbar()  # Create an instance of Skillbar
skill_template = "OABDQZxWSDNxM3gpBVVtg7ibhA"
input_skill_slot = 1
target_agentID = 0

def draw_skilldata(input_skill_id):

    PyImGui.separator()
    
    if input_skill_id != 0:
        # Create SkillID and SkillType instances based on input
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
            from Py4GWCoreLib.Skill import Skill
            PyImGui.text(f"Campaign: {Skill.GetCampaign(input_skill_id)[1]}")
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



def draw_window():
    global Module_Name
    global input_skillbar_index
    global skillbar_instance
    global skill_template
    global input_skill_slot
    global target_agentID

    # Refresh skillbar context
    skillbar_instance.GetContext()
    

    if PyImGui.begin(Module_Name):

        if PyImGui.collapsing_header("Methods"):
            PyImGui.text("Skill Template (Outpost Exclusive)")
            skill_template = PyImGui.input_text("Template String", skill_template)
            if PyImGui.button("Load Skill Template"):
                if skillbar_instance.LoadSkillTemplate(skill_template):
                    Py4GW.Console.Log(Module_Name,"Template Loaded Successfully!")
                else:
                    Py4GW.Console.Log(Module_Name,"Failed to Load Template")
            PyImGui.separator()
            
            # Input field for selecting skill slot (limited to 1..8)
            PyImGui.text("Select Skill Slot (1-8)")
            input_skill_slot = PyImGui.input_int("Skill Slot", input_skill_slot)
            if input_skill_slot < 1:  # Limit to minimum of 1
                input_skill_slot = 1
            elif input_skill_slot > 8:  # Limit to maximum of 8
                input_skill_slot = 8
                
            target_agentID = PyImGui.input_int("Target AgentID", target_agentID)
            
            # Use the skill from the selected slot
            if PyImGui.button("Use Selected Skill"):
                skillbar_instance.UseSkill(input_skill_slot, target_agentID)
                #function can accept 0 and will take current Target
            PyImGui.separator()
        
        PyImGui.separator()
        
        if PyImGui.collapsing_header("Skillbar"):
            for index, skill in enumerate(skillbar_instance.skills):
                if PyImGui.collapsing_header(f"Skill {index + 1}"):
                    PyImGui.text(f"Skill {index + 1}:")
                    PyImGui.text(f"  Skill ID: {skill.id.id}")
                    PyImGui.text(f"  Adrenaline A: {skill.adrenaline_a}")
                    PyImGui.text(f"  Adrenaline B: {skill.adrenaline_b}")
                    PyImGui.text(f"  Recharge: {skill.recharge} (this is the timestamp when casted)")
                    PyImGui.text(f"  Event: {skill.event}")
                    PyImGui.separator()
                    if PyImGui.collapsing_header(f"SkillData({skill.id.id})"):
                        draw_skilldata(skill.id.id)
                    PyImGui.separator()


        PyImGui.end()


# main() must exist in every script and is the entry point for your plugin's execution.
def main():
    try:
        draw_window()

    # Handle specific exceptions to provide detailed error messages
    except ImportError as e:
        Py4GW.Console.Log("YourModule", f"ImportError encountered: {str(e)}")
    except ValueError as e:
        Py4GW.Console.Log("YourModule", f"ValueError encountered: {str(e)}")
    except Exception as e:
        # Catch-all for any other exceptions
        Py4GW.Console.Log("YourModule", f"Unexpected error encountered: {str(e)}")
    finally:
        # Optional: Code that will run whether an exception occurred or not
        # This can include cleanup tasks, logging, or final steps
        pass  # Replace with your actual code


# This ensures that main() is called when the script is executed directly.
if __name__ == "__main__":
    main()
