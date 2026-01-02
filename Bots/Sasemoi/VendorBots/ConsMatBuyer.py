import Py4GW
from Py4GWCoreLib import Routines, Console
from Py4GWCoreLib import Botting
from Py4GWCoreLib import ModelID

bot = Botting(
    "Material Buyer",
)


def create_bot_routine(bot: Botting) -> None:
    InitBot(bot)


def InitBot(bot: Botting) -> None:
    bot.States.AddHeader("Init Bot")
    bot.Move.XY(2989.08, -2204.94)
    bot.Interact.WithNpcAtXY(2989.08, -2204.94)
    bot.States.AddCustomState(lambda: BuyIronIngots(bot), "Buy Iron Ingots")

def BuyIronIngots(bot: Botting):
    for _ in range(25):
      yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Iron_Ingot.value)
      yield from Routines.Yield.Merchant.BuyMaterial(ModelID.Bone.value)



bot.SetMainRoutine(create_bot_routine)
base_path = Console.get_projects_path()


def configure():
    global bot
    bot.UI.draw_configure_window()

def main():
    bot.Update()
    projects_path = Console.get_projects_path()
    widgets_path = projects_path + "\\Widgets\\Config\\textures\\"
    bot.UI.draw_window(icon_path=widgets_path + "YAVB 2.0 mascot.png")

if __name__ == "__main__":
    main()
