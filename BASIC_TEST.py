import PyKeystroke
import PyImGui

VK_RETURN = 0x0D; Enter = VK_RETURN

def draw_window():
    if PyImGui.begin("dialog tester"):
        if PyImGui.button("enter character"):
            PyKeystroke.PyScanCodeKeystroke().PushKey(Enter)
            
    PyImGui.end()

def main():
    draw_window()


if __name__ == "__main__":
    main()
