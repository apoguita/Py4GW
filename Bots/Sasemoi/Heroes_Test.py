import Py4GW
from Py4GWCoreLib import Routines, ConsoleLog, Console
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Botting, HeroType
from Bots.Sasemoi.bot_helpers.bot_mystic_healing_support import MysticHealingSupport

bot = Botting(
    "Heroes Test Bot",
    upkeep_auto_inventory_management_active=False,
    upkeep_auto_loot_active=False,
    config_log_actions=False
)

hero_list = [
    HeroType.Gwen,
    HeroType.MOX,
    HeroType.Melonni
]

def SetupHeroManagedCoroutine(hero_type, hero_index):
    ConsoleLog("Hero Testing", "Setting up Gwen Mystic Healing Support Routine...", Py4GW.Console.MessageType.Info)
    yield from _healing_support_routine(hero_type.value, hero_index=hero_index, delay_ms=0)

def create_bot_routine(bot: Botting) -> None:
    InitBot(bot)
    SenquaValeRoutine(bot)


def InitBot(bot: Botting) -> None:
    bot.States.AddHeader("Init Party")
    MysticHealingSupport.SetupHealingParty(bot, hero_list=hero_list)


def SenquaValeRoutine(bot: Botting) -> None:
    bot.States.AddHeader("Senqua Vale")
    bot.Move.XYAndExitMap(-4642.57, -13018.57, target_map_name="Sunqua Vale")  # Sunqua Vale
    bot.Party.FlagAllHeroes(-5041.78, -13095.50)
    
    MysticHealingSupport.InitHeroComanagedRoutines(bot, hero_list=hero_list)
    
    bot.Wait.ForTime(2000)
    bot.Move.XY(-5041.78, -13095.50)
    bot.Move.XY(-4642.57, -13018.57)
    bot.States.JumpToStepName("XY_1")



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

def _healing_support_routine(hero_id: int, hero_index: int = 1, delay_ms: int = 0):
    ConsoleLog("[Mystic Healing Support]", f"Starting healing support routine for hero ID: {hero_id} at party index {hero_index}", Py4GW.Console.MessageType.Info)

    delay_timer = ThrottledTimer(delay_ms)
    delay_timer.Start()

    skillbar = GLOBAL_CACHE.SkillBar.GetHeroSkillbar(hero_index)
    mystic_healing = skillbar[0]
    cautery = skillbar[1] if len(skillbar) > 1 else None

    while True:
        # Initial delay before starting routine
        if not delay_timer.IsExpired():
            yield from Routines.Yield.wait(250)
            continue

        # Check if map has fully loaded
        if not Routines.Checks.Map.MapValid():
            yield from Routines.Yield.wait(1000)
            continue
        
        if not GLOBAL_CACHE.Map.IsExplorable():
            yield from Routines.Yield.wait(1000)
            continue
        
        
        if (cautery is not None and cautery.recharge == 0):
            # GLOBAL_CACHE.Party.Heroes.UseSkill(hero_agent_id=hero_agent_id, slot=2, target_id=hero_agent_id)
            yield from Routines.Yield.Keybinds.HeroSkill(hero_index, 2)
            yield from Routines.Yield.wait(2000)  # Wait 5 seconds before next heal attempt

        if (mystic_healing.recharge == 0):
            yield from Routines.Yield.Keybinds.HeroSkill(hero_index, 1)
            yield from Routines.Yield.wait(1000)
          
        yield from Routines.Yield.wait(150)  # Main loop wait time