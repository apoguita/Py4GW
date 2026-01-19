from Py4GWCoreLib import *
import PyImGui, Py4GW
import os
from typing import Generator, Any
BOT_NAME = "LDoA Codex"

profession_bot: dict[str, Botting] = {}
PROFESSION = ""

bot = Botting(
        BOT_NAME,
        upkeep_auto_inventory_management_active=False,
        upkeep_auto_combat_active=False,
        upkeep_auto_loot_active=False,
    )
    

class QuestData:
        def __init__(self,
                 npc_coords: tuple[float, float],
                 first_dialog: int,
                 second_dialog: int,
                 final_dialog: int,
                 quest_path: list[tuple[float, float]],
                 npc_name: str):
            self.npc_coords = npc_coords
            self.first_dialog = first_dialog
            self.second_dialog = second_dialog
            self.final_dialog = final_dialog
            self.quest_path = quest_path
            self.npc_name = npc_name
    
   
def FirstTimeAscalon(bot: Botting) -> None:
    def _get_quest_with_sir_tydius():
        profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
        quest_with_sir_tydius: dict[str, int] = {
            "Warrior": 0x80DD01,
            "Ranger": 0x80DE01,
            "Monk": 0x80DC01,
            "Necromancer": 0x80DA01,
            "Mesmer": 0x80D901,
            "Elementalist": 0x80DB01,
        }
        yield from bot.Dialogs._coro_at_xy(11687.05, 3445.20, quest_with_sir_tydius.get(profession, 0))
              
    bot.States.AddHeader(f"{BOT_NAME}")
    bot.Move.XYAndDialog(9983, -483,0x805001, "Town Cryer")
    bot.Move.XYAndDialog(11687.05, 3445.20,0x805007, "Sir Tydius reward")
    bot.States.AddCustomState(lambda: _get_quest_with_sir_tydius(), "Get Profession Quest")
    bot.Templates.Aggressive(halt_on_death=True,auto_loot=False)
    bot.Items.SpawnAndDestroyBonusItems()
    bot.Items.Equip(ModelID.Bonus_Nevermore_Flatbow.value)
    path_to_exit = [(8119.07, 5391.31),(7120,5238)]
    bot.Move.FollowAutoPath(path_to_exit, step_name="to lakeside county exit")
    bot.Wait.ForMapLoad(target_map_id=146)
    
    
def _travel_to_ascalon_and_exit(bot: Botting) -> Generator:   
    yield from bot.Map._coro_travel(target_map_id=148) #ascalon city
    path_to_exit = [(8119.07, 5391.31),(7120,5238)]
    yield from bot.Move._coro_follow_auto_path(path_to_exit, step_name="to lakeside county exit")
    yield from bot.Wait._coro_for_map_load(target_map_id=146)
    
QUEST_MAP: dict[str, QuestData] = {
    "Warrior": QuestData(
        npc_coords=(6126, 3997),
        first_dialog=0x80DD07,
        second_dialog=0x805501,
        final_dialog=0x805507,
        quest_path=[(4668, -3311)],
        npc_name="Van"
    ),
    "Ranger": QuestData(
        npc_coords=(6152, 4203),
        first_dialog=0x80DE07,
        second_dialog=0x805601,
        final_dialog=0x805607,
        quest_path=[(5546, -4058)],
        npc_name="Artemis"
    ),
    "Monk": QuestData(
        npc_coords=(6008, 4203),
        first_dialog=0x80DC07,
        second_dialog=0x805401,
        final_dialog=0x805407,
        quest_path=[(3886, -4384),(5905, 4164)],
        npc_name="Ciglo"
    ),
    "Necromancer": QuestData(
        npc_coords=(6146, 4197),
        first_dialog=0x80DA07,
        second_dialog=0x805201,
        final_dialog=0x805207,
        quest_path=[(4321, 339)],
        npc_name="Verata"
    ),
    "Mesmer": QuestData(
        npc_coords=(6232, 3924),
        first_dialog=0x80D907,
        second_dialog=0x805101,
        final_dialog=0x805107,
        quest_path=[(4732, 989)],
        npc_name="Sebedoh"
    ),
    "Elementalist": QuestData(
        npc_coords=(6189, 4058),
        first_dialog=0x80DB07,
        second_dialog=0x805301,
        final_dialog=0x805307,
        quest_path=[(4912, -2723)],
        npc_name="Howland"
    )
}
    
def PrimaryProfessionQuest(bot: Botting) -> None:
    def _handle_primary_quest(bot: Botting):
        profession, _ = Agent.GetProfessionNames(Player.GetAgentID())
        quest_data = QUEST_MAP.get(profession)
        if quest_data is None:
            print(f"No primary profession quest data for profession: {profession}")
            return
        yield from bot.Move._coro_xy_and_dialog(quest_data.npc_coords[0], quest_data.npc_coords[1], quest_data.first_dialog, f"Reward with {quest_data.npc_name}")
        yield from bot.Dialogs._coro_at_xy(quest_data.npc_coords[0], quest_data.npc_coords[1], quest_data.second_dialog)
        yield from bot.Move._coro_follow_auto_path(quest_data.quest_path, "Go to quest location")
        yield from bot.Wait._coro_until_out_of_combat()
        yield from _travel_to_ascalon_and_exit(bot)
        yield from bot.Move._coro_xy_and_dialog(quest_data.npc_coords[0], quest_data.npc_coords[1], quest_data.final_dialog, f"Last Reward with {quest_data.npc_name}")
              
    bot.States.AddHeader(f"Primary Quest")
    bot.States.AddCustomState(lambda: _handle_primary_quest(bot), "Handle Primary Profession Quest")


def create_bot_routine(bot: Botting) -> None:
    FirstTimeAscalon(bot)
    PrimaryProfessionQuest(bot)
    

bot.SetMainRoutine(create_bot_routine)

def configure():
    global bot
    bot.UI.draw_configure_window()
    
    
def main():
    bot.Update()
    bot.UI.draw_window()

if __name__ == "__main__":
    main()
