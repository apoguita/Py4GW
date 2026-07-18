from Py4GWCoreLib import *
from typing import Callable


class BaseElement:
    def render(self):
        raise NotImplementedError()


class Text(BaseElement):
    def __init__(self, text: str):
        self.text = text

    def render(self):
        PyImGui.text(self.text)


class Button(BaseElement):
    def __init__(self, label: str, callback: Callable = lambda: True):
        self.label = label
        self.callback = callback

    def render(self):
        if PyImGui.button(self.label):
            if self.callback:
                self.callback()


class RawCode(BaseElement):
    def __init__(self, func: Callable):
        self.func = func

    def render(self):
        self.func()


class WindowElement(BaseElement):
    def __init__(self, title: str, flags: int = 0):
        self.title = title
        self.flags = flags
        self.children: list[BaseElement] = []

    def add(self, element: BaseElement):
        self.children.append(element)

    def inject_code(self, func: Callable):
        self.children.append(RawCode(func))

    def render(self):
        if PyImGui.begin(self.title, self.flags):
            for child in self.children:
                child.render()
            PyImGui.end()
