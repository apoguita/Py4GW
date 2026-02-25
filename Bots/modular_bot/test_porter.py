
from Sources.modular_bot import ModularBot, Phase
from Sources.modular_bot.recipes import Mission, list_available_missions, mission_run
from Sources.modular_bot.hero_setup import draw_setup_tab


bot = ModularBot(
    name="apo check",
    phases=[Mission("porter_check")],
    loop=True)


def main():
    bot.update()
