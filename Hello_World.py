from Py4GWCoreLib import *
import PyImGui
from Py4GW import Console



MODULE_NAME = "Gw config Manager"
class Preferences:
    def __init__(self):
        self.TextLanguage = ServerLanguage.English.value
        self.AudioLanguage = ServerLanguage.English.value
        self.ChatFilterLevel = 0  # setting not working
        
    def Load(self):
        self.TextLanguage = UIManager.GetIntPreference(NumberPreference.TextLanguage.value)
        self.AudioLanguage = UIManager.GetIntPreference(NumberPreference.AudioLanguage.value)
        self.ChatFilterLevel = UIManager.GetIntPreference(NumberPreference.ChatFilterLevel.value)
        
    def GetTextLanguage(self) -> tuple[int, str]:
        return self.TextLanguage, ServerLanguage(self.TextLanguage).name
    
    def SetTextLanguage(self, language: int):
        self.TextLanguage = language
        UIManager.SetIntPreference(NumberPreference.TextLanguage.value, language)
        
    def GetAudioLanguage(self) -> tuple[int, str]:
        return self.AudioLanguage, ServerLanguage(self.AudioLanguage).name

    def SetAudioLanguage(self, language: int):
        self.AudioLanguage = language
        UIManager.SetIntPreference(NumberPreference.AudioLanguage.value, language)
        

GwPreferences = Preferences()


def Draw_Window():
    GwPreferences.Load()
    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.text(GwPreferences.GetTextLanguage()[1])
        PyImGui.text(GwPreferences.GetAudioLanguage()[1])
        
        chat_filter_level = UIManager.GetEnumPreference(NumberPreference.ChatFilterLevel.value)
        PyImGui.text("Chat Filter Level: " + str(chat_filter_level))


    PyImGui.end()


def main():
    Draw_Window()


if __name__ == "__main__":
    main()
