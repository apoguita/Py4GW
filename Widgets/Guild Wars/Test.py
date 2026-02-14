from typing import Optional


MODULE_NAME = "Test"
MODULE_CATEGORY = "Guild Wars"
MODULE_ICON = "Textures\\Consumables\\Armor_of_Salvation.png"
MODULE_TAGS = ["Testing", "Example", "Demo"]

class ModuleInfo:
    def __init__(self, name : Optional[str] = None, category : Optional[str] = None, icon : Optional[str] = None, tags : Optional[list[str]] = None):
        self.name : Optional[str] = name
        self.category : Optional[str] = category
        self.icon : Optional[str] = icon
        self.tags : Optional[list[str]] = tags

MODULE_INFO = ModuleInfo(
    name = "Test",
    category = "Guild Wars",
    icon = "Textures\\Consumables\\Armor_of_Salvation.png",
    tags = ["Testing", "Example", "Demo"]
)

# def tooltip():
#     pass

def on_enable():
    pass

def on_disable():
    pass
    
def configure():
    pass
    
def draw():
    pass
    
def update():
    pass

def main():
    pass
    
if __name__ == "__main__":
    main()
