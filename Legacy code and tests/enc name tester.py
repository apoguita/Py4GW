import PyImGui
import PyAgent

counter = 0

"""def update():
    global counter
    counter += 1


def draw():
    global counter
    if PyImGui.begin("hello world"):
        PyImGui.text("Hello World from Python!")
        PyImGui.text(f"Counter: {counter}")
    PyImGui.end()"""
    
agent_id = 0
agent_enc_name = []
def main():
    global agent_id, agent_enc_name
    if PyImGui.begin("Hello World"):    
        agent_id = PyImGui.input_int("Agent ID", agent_id)
        if PyImGui.button("Get Agent Name"):
            agent_enc_name = PyAgent.PyAgent.GetAgentEncName(agent_id)   

        for byte in agent_enc_name:
            PyImGui.text(f"{byte} ")
            PyImGui.same_line(0,-1)
            
        PyImGui.new_line()
        PyImGui.separator()
        for byte in agent_enc_name:
            PyImGui.text(f"{chr(byte)} ")
            PyImGui.same_line(0,-1)
            

    PyImGui.end()

if __name__ == "__main__":
    main()