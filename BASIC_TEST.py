import PyKeystroke
import PyImGui
import Py4GW

VK_RETURN = 0x0D; Enter = VK_RETURN

def draw_window():
    if PyImGui.begin("dialog tester"):
        if PyImGui.button("enter character"):
            PyKeystroke.PyScanCodeKeystroke().PushKey(Enter)
            
        if PyImGui.button("print hello"):
            Py4GW.Console.Log("test script", "hello world")
            
    PyImGui.end()

def main():
    draw_window()


if __name__ == "__main__":
    main()
