import Py4GW

class PathLocator:

    @staticmethod
    def get_custom_behaviors_root_directory() -> str:
        return Py4GW.Console.get_projects_path() + "\\Sources\\oazix\\CustomBehaviors"
    
    @staticmethod
    def get_project_root_directory() -> str:
        return Py4GW.Console.get_projects_path()
    
    @staticmethod
    def get_texture_fallback() -> str:
        return PathLocator.get_custom_behaviors_root_directory() + "\\gui\\textures\\no_bg.png"
    
    