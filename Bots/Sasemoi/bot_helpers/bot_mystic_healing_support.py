import Py4GW
from Py4GWCoreLib import Botting, Routines
from Py4GWCoreLib import HeroType
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import ConsoleLog

# default_hero_list = [HeroType.Gwen, HeroType.Norgu, HeroType.MOX, HeroType.Kahmu, HeroType.Melonni, HeroType.ZhedShadowhoof, HeroType.Vekk]
# cautery_hero_ids = [HeroType.MOX.value, HeroType.Kahmu.value, HeroType.Melonni.value]


default_hero_list = [
    HeroType.Gwen,
    HeroType.MOX,
    HeroType.Melonni
]
default_hero_template_list = [
    (HeroType.Gwen, "OQpjAwDjKP3XlAAAAAAAAAAAAA"), # Mystic Healing + Echo
    (HeroType.MOX, "Ogmioys8cfpxAAAAAAAAAAAA"), # Mystic Healing + Cautery
    (HeroType.Melonni, "Ogmioys8cfpxAAAAAAAAAAAA") # Mystic Healing + Cautery
]


class MysticHealingSupport:
    def __init__(self):
        pass

    @staticmethod
    def SetupHealingParty(bot: Botting, hero_list: list[tuple[HeroType, str]] = default_hero_template_list):
        '''Sets up the party with specified Mystic Healing Support heroes.'''

        ConsoleLog("Mystic Healing Support", "Setting up party with Mystic Healing Support Heroes...", Py4GW.Console.MessageType.Info)
        bot.Party.LeaveParty()
        for i, (hero_type, template) in enumerate(hero_list):
            bot.Party.AddHero(hero_type.value)
            bot.States.AddCustomState(
                lambda hero_index=i + 1, hero_template=template: Routines.Yield.Skills.LoadHeroSkillbar(hero_index, hero_template),
                f"Load Skillbar for {hero_type.name}"
            )


    @staticmethod
    def InitHeroComanagedRoutines(bot: Botting, hero_list: list[HeroType] = default_hero_list):
        '''Initialize Mystic Healing Support routines for a given list of heroes.'''

        ConsoleLog("Mystic Healing Support", "Initializing Mystic Healing Support Routines for Heroes...", Py4GW.Console.MessageType.Info)
        for i, hero_type in enumerate(hero_list):
            bot.States.AddManagedCoroutine(
                _get_coroutine_name(hero_type.name),
                lambda hero_id=hero_type.value, index=i: _healing_support_routine(hero_id, hero_index=index + 1, delay_ms=index * 750)
              )

    
    @staticmethod
    def RemoveHeroComanagedRoutines(bot: Botting, hero_list: list[HeroType] = default_hero_list):
        '''Removes the Mystic Healing Support routines for a given list of heroes.'''
        ConsoleLog("Mystic Healing Support", "Removing Mystic Healing Support Routines for Heroes...", Py4GW.Console.MessageType.Info)
        for hero_type in hero_list:
            bot.States.RemoveManagedCoroutine(_get_coroutine_name(hero_type.name))


def _healing_support_routine(hero_id: int, hero_index: int = 0, delay_ms: int = 0):
    '''Coroutine that provides Mystic Healing support for a specified hero.'''
   
    ConsoleLog("[Mystic Healing Support]", f"Starting healing support routine for hero ID: {hero_id} at party index {hero_index}", Py4GW.Console.MessageType.Debug)

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

def _get_coroutine_name(hero_name: str) -> str:
    return f"Mystic Healing Support - {hero_name}"