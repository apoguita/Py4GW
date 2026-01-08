from Py4GWCoreLib import Botting
from Widgets.CustomBehaviors.primitives.botting.botting_helpers import BottingHelpers
from Widgets.CustomBehaviors.primitives.parties.custom_behavior_party import CustomBehaviorParty

def bot_routine(bot_instance: Botting):

    CustomBehaviorParty().set_party_is_blessing_enabled(True)

    bot_instance.Templates.Routines.UseCustomBehaviors(
        on_player_critical_death=BottingHelpers.botting_unrecoverable_issue,
        on_party_death=BottingHelpers.botting_unrecoverable_issue,
        on_player_critical_stuck=BottingHelpers.botting_unrecoverable_issue)

    bot_instance.Templates.Aggressive()

    # Set up the FSM states properly
    bot_instance.States.AddHeader("STARTING_POINT")
    bot_instance.Party.SetHardMode(False)

    bot_instance.States.AddHeader("MAIN_LOOP")
    bot_instance.Templates.Aggressive()
    bot_instance.Wait.ForTime(3000)
    bot_instance.Templates.Pacifist()
    bot_instance.Wait.ForTime(4000)
    bot_instance.Templates.Aggressive()
    bot_instance.Wait.ForTime(3000)

    bot_instance.Wait.ForTime(10000000)

    bot_instance.States.JumpToStepName("[H]STARTING_POINT_1")

    bot_instance.States.AddHeader("END")

bot = Botting("Example")
bot.SetMainRoutine(bot_routine)

def main():
    bot.Update()
    bot.UI.draw_window()

if __name__ == "__main__":
    main()
