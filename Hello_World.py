import PyImGui


def draw_window():
    if PyImGui.begin("HeroAI test"):
        pass
    PyImGui.end()

def main():
    draw_window()

if __name__ == "__main__":
    main()
