from Py4GWCoreLib import *

MODULE_NAME = "tester for everything"

class ButtonColor:
    def __init__(self, button_color:Color, hovered_color:Color, active_color:Color):
        self.button_color = button_color
        self.hovered_color = hovered_color
        self.active_color = active_color
      

ButtonColors = {
    "Celerity": ButtonColor(button_color = Color(129, 33, 188, 255), hovered_color = Color(165, 100, 200, 255), active_color = Color(135, 225, 230, 255)),  
    "GrailOfMight": ButtonColor(button_color=Color(70,0,10,255), hovered_color=Color(160,0,15,255), active_color=Color(252,225,115,255)),
    "ArmorOfSalvation": ButtonColor(button_color = Color(96, 60, 15, 255),hovered_color = Color(187, 149, 38, 255),active_color = Color(225, 150, 0, 255)),
    "CandyCane": ButtonColor(button_color = Color(63, 91, 54, 255),hovered_color = Color(149, 72, 34, 255),active_color = Color(96, 172, 28, 255)),
    "BirthdayCupcake": ButtonColor(button_color = Color(138, 54, 80, 255),hovered_color = Color(255, 186, 198, 255),active_color = Color(205, 94, 215, 255)),
    "GoldenEgg": ButtonColor(button_color = Color(245, 227, 143, 255),hovered_color = Color(253, 248, 234, 255),active_color = Color(129, 82, 35, 255)),
    "CandyCorn": ButtonColor(button_color = Color(239, 174, 33, 255),hovered_color = Color(206, 178, 148, 255),active_color = Color(239, 77, 16, 255)),
    "CandyApple": ButtonColor(button_color = Color(75, 26, 28, 255),hovered_color = Color(202, 60, 88, 255),active_color = Color(179, 0, 39, 255)),
    "PumpkinPie": ButtonColor(button_color = Color(224, 176, 126, 255),hovered_color = Color(226, 209, 210, 255),active_color = Color(129, 87, 54, 255)),
    "DrakeKabob": ButtonColor(button_color = Color(28, 28, 28, 255),hovered_color = Color(190, 187, 184, 255),active_color = Color(94, 26, 13, 255)),
    "SkalefinSoup": ButtonColor(button_color = Color(68, 85, 142, 255),hovered_color = Color(255, 255, 107, 255),active_color = Color(106, 139, 51, 255)),
    "PahnaiSalad": ButtonColor(button_color = Color(113, 43, 25, 255),hovered_color = Color(185, 157, 90, 255),active_color = Color(137, 175, 10, 255)),
    "WarSupplies": ButtonColor(button_color = Color(51, 26, 13, 255),hovered_color = Color(113, 43, 25, 255),active_color = Color(202, 115, 77, 255)),
    "Alcohol": ButtonColor(button_color = Color(58, 41, 50, 255),hovered_color = Color(169, 145, 111, 255),active_color = Color(173, 173, 156, 255)),
    "Blank": ButtonColor(button_color= Color(0, 0, 0, 0), hovered_color=Color(0, 0, 0, 0), active_color=Color(0, 0, 0, 0)),
}


def main():
    global flag_color

    if PyImGui.begin("Flagging Mockup", PyImGui.WindowFlags.AlwaysAutoResize):
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["Celerity"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_GLOBE_ASIA}##commands_pcon_celerity", 
                                ButtonColors["Celerity"].button_color, 
                                ButtonColors["Celerity"].hovered_color, 
                                ButtonColors["Celerity"].active_color, 
                                width=30, height=30):
            pass
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Esence of Celerity")
        
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["GrailOfMight"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_WINE_GLASS}##commands_pcon_grail_of_might", 
                                ButtonColors["GrailOfMight"].button_color, 
                                ButtonColors["GrailOfMight"].hovered_color, 
                                ButtonColors["GrailOfMight"].active_color, 
                                width=30, height=30):
            pass
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Grail of Might")
        
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["ArmorOfSalvation"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_SPLOTCH}##commands_pcon_ArmorOfSalvation", 
                                ButtonColors["ArmorOfSalvation"].button_color, 
                                ButtonColors["ArmorOfSalvation"].hovered_color, 
                                ButtonColors["ArmorOfSalvation"].active_color, 
                                width=30, height=30):
            pass
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Armor of Salvation")
        
        PyImGui.same_line(0,-1)
        PyImGui.text("|")
        PyImGui.same_line(0,-1)
        
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["CandyCane"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_CANDY_CANE}##commands_pcon_CandyCane", 
                                ButtonColors["CandyCane"].button_color, 
                                ButtonColors["CandyCane"].hovered_color, 
                                ButtonColors["CandyCane"].active_color, 
                                width=30, height=30):
            pass
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Rainbow Candy Cane / Honeycomb")
        PyImGui.separator()
        
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["BirthdayCupcake"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_BIRTHDAY_CAKE}##commands_pcon_BirthdayCupcake", 
                                ButtonColors["BirthdayCupcake"].button_color, 
                                ButtonColors["BirthdayCupcake"].hovered_color, 
                                ButtonColors["BirthdayCupcake"].active_color, 
                                width=30, height=30):
            pass
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Birthday Cupcake")
        
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["GoldenEgg"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_EGG}##commands_pcon_GoldenEgg", 
                                ButtonColors["GoldenEgg"].button_color, 
                                ButtonColors["GoldenEgg"].hovered_color, 
                                ButtonColors["GoldenEgg"].active_color, 
                                width=30, height=30):
            pass
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Golden Egg")
        
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["CandyCorn"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_CARROT}##commands_pcon_CandyCorn", 
                                ButtonColors["CandyCorn"].button_color, 
                                ButtonColors["CandyCorn"].hovered_color, 
                                ButtonColors["CandyCorn"].active_color, 
                                width=30, height=30):
            pass
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Candy Corn")
        
        PyImGui.same_line(0,-1)
        PyImGui.text("|")
        PyImGui.same_line(0,-1)
        
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["Alcohol"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_WINE_BOTTLE}##commands_pcon_Alcohol", 
                                ButtonColors["Alcohol"].button_color, 
                                ButtonColors["Alcohol"].hovered_color, 
                                ButtonColors["Alcohol"].active_color, 
                                width=30, height=30):
            pass
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Alcohol")
        PyImGui.separator()
        PyImGui.same_line(0,-1)
        
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["CandyApple"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_APPLE_ALT}##commands_pcon_CandyApple", 
                                ButtonColors["CandyApple"].button_color, 
                                ButtonColors["CandyApple"].hovered_color, 
                                ButtonColors["CandyApple"].active_color, 
                                width=30, height=30):
            pass
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Candy Apple")
        
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["PumpkinPie"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_CHEESE}##commands_pcon_PumpkinPie", 
                                ButtonColors["PumpkinPie"].button_color, 
                                ButtonColors["PumpkinPie"].hovered_color, 
                                ButtonColors["PumpkinPie"].active_color, 
                                width=30, height=30):
            pass
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Slice of Pumpkin Pie")
        
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["DrakeKabob"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_SLASH}##commands_pcon_DrakeKabob", 
                                ButtonColors["DrakeKabob"].button_color, 
                                ButtonColors["DrakeKabob"].hovered_color, 
                                ButtonColors["DrakeKabob"].active_color, 
                                width=30, height=30):
            pass
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Drake Kabob")

        PyImGui.separator()
        PyImGui.same_line(0,-1)
        
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["SkalefinSoup"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_MORTAR_PESTLE}##commands_pcon_SkalefinSoup", 
                                ButtonColors["SkalefinSoup"].button_color, 
                                ButtonColors["SkalefinSoup"].hovered_color, 
                                ButtonColors["SkalefinSoup"].active_color, 
                                width=30, height=30):
            pass
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Skalefin Soup")
        
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["PahnaiSalad"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_RING}##commands_pcon_PahnaiSalad", 
                                ButtonColors["PahnaiSalad"].button_color, 
                                ButtonColors["PahnaiSalad"].hovered_color, 
                                ButtonColors["PahnaiSalad"].active_color, 
                                width=30, height=30):
            pass
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("Pahnai Salad")
        
        PyImGui.same_line(0,-1)
        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, ButtonColors["WarSupplies"].active_color.to_tuple_normalized())
        if ImGui.colored_button(f"{IconsFontAwesome5.ICON_TOOLBOX}##commands_pcon_WarSupplies", 
                                ButtonColors["WarSupplies"].button_color, 
                                ButtonColors["WarSupplies"].hovered_color, 
                                ButtonColors["WarSupplies"].active_color, 
                                width=30, height=30):
            pass
        PyImGui.pop_style_color(1)
        ImGui.show_tooltip("War Supplies")
        
    PyImGui.end()
    
if __name__ == "__main__":
    main()
