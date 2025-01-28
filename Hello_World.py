from Py4GWCoreLib import *
import re

def format_skill_name(skill_name):
    """
    Formats a skill name by removing punctuation, replacing spaces with underscores,
    and preserving capitalization.
    """
    # Remove punctuation using regex
    skill_name = re.sub(r'[^\w\s]', '', skill_name)
    # Replace spaces with underscores
    skill_name = skill_name.replace(' ', '_')
    # Return the formatted skill name
    return skill_name


def format_skills(skill_list):
    """
    Takes a list of skill names and returns a formatted list with the required structure.
    """
    return [format_skill_name(skill) for skill in skill_list]

def safe_int(value):
    """
    Safely convert a value to an integer.
    Returns 0 if the value is not a valid integer.
    """
    if isinstance(value, int):
        return value  # Already an integer
    if isinstance(value, str) and value.isdigit():
        return int(value)  # Convert valid string integers like '15'
    try:
        # Attempt to extract the first valid integer if possible
        return int(value.split()[0]) if isinstance(value, str) else 0
    except (ValueError, AttributeError):
        return 0  # Default to 0 for any invalid cases

def DrawWindow():

    if PyImGui.begin("Hello World!"):
        profession = PyAgent.Profession("Necromancer")
        PyImGui.text(f"profession {profession.GetName()}")

        agent_instance = Agent.agent_instance(Player.GetTargetID())
        model_id = agent_instance.living_agent.player_number
        PyImGui.text(f"model_id {model_id}")
        if model_id in ModelData:
            data = ModelData[model_id]
            skills_used = data.get('skills_used', [])
            formatted_skills = format_skills(skills_used)

            PyImGui.text(f"Skills Used: {formatted_skills}")

            # Example: Use the formatted skill names for further processing
            for skill in formatted_skills:
                PyImGui.text(f"Formatted Skill: {Skill.GetID(skill)}")

            PyImGui.separator()

            PyImGui.text(f"skillbar {Agent.GetNPCSkillbar(Player.GetTargetID())}")


    PyImGui.end()


def main():
        DrawWindow()

if __name__ == "__main__":
    main()

