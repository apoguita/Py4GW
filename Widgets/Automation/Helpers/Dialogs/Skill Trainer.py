from Py4GWCoreLib import *

MODULE_NAME = "Skill Learner"

skill_id_input = 0
status_message = ""


def main():
    global skill_id_input, status_message

    if PyImGui.begin(MODULE_NAME):
        PyImGui.text("Enter the Skill ID to learn:")
        skill_id_input = PyImGui.input_int("Skill ID", skill_id_input)

        PyImGui.separator()

        if PyImGui.button("Learn Skill"):
            if skill_id_input > 0:
                Player.BuySkill(skill_id_input)
                status_message = f"Sent request to learn skill {skill_id_input}"
            else:
                status_message = "Please enter a valid Skill ID"

        if status_message:
            PyImGui.text(status_message)

    PyImGui.end()


if __name__ == "__main__":
    main()
