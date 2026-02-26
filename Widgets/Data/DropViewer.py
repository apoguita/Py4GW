from Sources.oazix.CustomBehaviors import start_drop_viewer

"""
Drop Viewer Widget
Displays the Drop Tracker Window.
"""

def draw():
    """
    Draws the drop viewer window.
    This function is called by the Widget Manager when the widget is enabled.
    """
    start_drop_viewer.draw_window()

def update():
    start_drop_viewer.update()

def main():
    pass

def configure():
    pass
