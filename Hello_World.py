from Py4GWCoreLib import ImGui, GLOBAL_CACHE, TitleID
import PyImGui, Py4GW
import os

MODULE_NAME = "Window Manipulator"

title = "Hello World"
def Draw_Window():  
    global title
    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        # Free input field
        title = PyImGui.input_text("Window Title", title, 0)
        if PyImGui.button(f"set title to {title}"):
            Py4GW.Console.set_window_title(title)

        PyImGui.separator()
        PyImGui.text("Quick test buttons:")

        if PyImGui.button("Spanish José"):
            Py4GW.Console.set_window_title("José")

        if PyImGui.button("French élève"):
            Py4GW.Console.set_window_title("Français – élève")

        if PyImGui.button("German München"):
            Py4GW.Console.set_window_title("München")

        if PyImGui.button("Russian Москва"):
            Py4GW.Console.set_window_title("Москва")

        if PyImGui.button("Chinese 标题测试"):
            Py4GW.Console.set_window_title("标题测试")

        if PyImGui.button("Japanese 日本語テスト"):
            Py4GW.Console.set_window_title("日本語テスト")

        if PyImGui.button("Korean 한글 테스트"):
            Py4GW.Console.set_window_title("한글 테스트")

        if PyImGui.button("Emoji 🌍🚀🔥"):
            Py4GW.Console.set_window_title("Hello 🌍🚀🔥")

    PyImGui.end()



def main():
    Draw_Window()


if __name__ == "__main__":
    main()
