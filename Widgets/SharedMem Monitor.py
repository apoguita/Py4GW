from Py4GWCoreLib import *
from ctypes import Structure, c_uint, c_float, c_bool, c_wchar
from multiprocessing import shared_memory
from ctypes import sizeof

MODULE_NAME = "Py4GWSharedMemoryManager Monitor"
  
SMM = GLOBAL_CACHE.ShMem    
NUMBER_OF_SKILLS = 8

def configure():
    pass  

def main():
    if not Routines.Checks.Map.MapValid():
        return
    if PyImGui.begin(f"{MODULE_NAME}"):
        PyImGui.text(f"Py4GW Shared Memory Manager - {SMM.shm_name}")
        PyImGui.separator()

        maps = SMM.GetMapsFromPlayers()

        for map_id, map_region, map_district in maps:
            map_name = GLOBAL_CACHE.Map.GetMapName(map_id)
            map_label = f"Map: {map_name} - Region: {map_region} - District: {map_district}"
            if PyImGui.tree_node(map_label):
                PyImGui.text("Parties in this map:")

                party_ids = SMM.GetPartiesFromMaps(map_id, map_region, map_district)
                for party_id in party_ids:
                    party_label = f"Party ID: {party_id}"
                    if PyImGui.tree_node(party_label):
                        players = SMM.GetPlayersFromParty(party_id, map_id, map_region, map_district)
                        players.sort(key=lambda p: p.PartyPosition)

                        for player in players:
                            if PyImGui.tree_node(player.CharacterName):
                                if PyImGui.tree_node("Player Info"):
                                    PyImGui.text(f"Player Slot Number: {player.SlotNumber}")
                                    PyImGui.text(f"Is Slot Active: {player.IsSlotActive}")
                                    PyImGui.text(f"Is Account: {player.IsAccount}")
                                    PyImGui.text(f"IsHero: {player.IsHero}")
                                    PyImGui.text(f"IsPet: {player.IsPet}")
                                    PyImGui.text(f"IsNPC: {player.IsNPC}")
                                    PyImGui.text(f"Account Email: {player.AccountEmail}")
                                    PyImGui.text(f"Account Name: {player.AccountName}")
                                    PyImGui.text(f"Player ID: {player.PlayerID}")
                                    PyImGui.text(f"Owner Player ID: {player.OwnerPlayerID}")
                                    PyImGui.text(f"HeroID: {player.HeroID}")
                                    PyImGui.text(f"MapID: {player.MapID}")
                                    PyImGui.text(f"Map Region: {player.MapRegion}")
                                    PyImGui.text(f"Map District: {player.MapDistrict}")
                                    PyImGui.text(f"Player HP: {int(player.PlayerHP*player.PlayerMaxHP)} / {player.PlayerMaxHP} Regen Pips: {player.PlayerHealthRegen:.2f}")
                                    PyImGui.text(f"Player Energy: {int(player.PlayerEnergy*player.PlayerMaxEnergy)} / {player.PlayerMaxEnergy} Regen Pips: {player.PlayerEnergyRegen:.2f}")
                                    PyImGui.text(f"Player XYZ: ({player.PlayerPosX:.2f}, {player.PlayerPosY:.2f}, {player.PlayerPosZ:.2f})")
                                    PyImGui.text(f"Player Facing Angle: {Utils.RadToDeg(player.PlayerFacingAngle):.2f}")
                                    PyImGui.text(f"Player Target ID: {player.PlayerTargetID}")
                                    PyImGui.text(f"Player Login Number: {player.PlayerLoginNumber}")
                                    PyImGui.text(f"Player Is Ticked: {player.PlayerIsTicked}")
                                    PyImGui.text(f"Party ID: {player.PartyID}")
                                    PyImGui.text(f"Party Position: {player.PartyPosition}")
                                    PyImGui.text(f"Party Is Leader: {player.PatyIsPartyLeader}")
                                    timestamp = datetime.fromtimestamp(player.LastUpdated / 1000)
                                    milliseconds = int(timestamp.microsecond / 1000)
                                    PyImGui.text(f"Last Updated: {timestamp.strftime('%H:%M:%S')}.{milliseconds:03d}")
                                    PyImGui.tree_pop()
                                    PyImGui.separator()
                                    
                                hero_ai_options = SMM.GetHeroAIOptions(player.AccountEmail)
                                if hero_ai_options is not None:
                                    if PyImGui.tree_node("HeroAI Configs"):
                                        PyImGui.text(f"FlagPosX: {hero_ai_options.FlagPosX:.2f}")
                                        PyImGui.text(f"FlagPosY: {hero_ai_options.FlagPosY:.2f}")
                                        PyImGui.text(f"FlagFacingAngle: {Utils.RadToDeg(hero_ai_options.FlagFacingAngle):.2f}")
                                        PyImGui.tree_pop()
                                        
                                        if PyImGui.begin_table("GameOptionTable", 5):
                                            PyImGui.table_next_row()
                                            PyImGui.table_next_column()
                                            hero_ai_options.Following = ImGui.toggle_button(IconsFontAwesome5.ICON_RUNNING + "##Following", hero_ai_options.Following,40,40)
                                            ImGui.show_tooltip("Following")
                                            PyImGui.table_next_column()
                                            hero_ai_options.Avoidance = ImGui.toggle_button(IconsFontAwesome5.ICON_PODCAST + "##Avoidance", hero_ai_options.Avoidance,40,40)
                                            ImGui.show_tooltip("Avoidance")
                                            PyImGui.table_next_column()
                                            hero_ai_options.Looting = ImGui.toggle_button(IconsFontAwesome5.ICON_COINS + "##Looting", hero_ai_options.Looting,40,40)
                                            ImGui.show_tooltip("Looting")
                                            PyImGui.table_next_column()
                                            hero_ai_options.Targeting = ImGui.toggle_button(IconsFontAwesome5.ICON_BULLSEYE + "##Targeting", hero_ai_options.Targeting,40,40)
                                            ImGui.show_tooltip("Targeting")
                                            PyImGui.table_next_column()
                                            hero_ai_options.Combat = ImGui.toggle_button(IconsFontAwesome5.ICON_SKULL_CROSSBONES + "##Combat", hero_ai_options.Combat,40,40)
                                            ImGui.show_tooltip("Combat")
                                            PyImGui.end_table()
                                            
                                        if PyImGui.begin_table("SkillsTable", NUMBER_OF_SKILLS + 1):
                                            PyImGui.table_next_row()
                                            for i in range(NUMBER_OF_SKILLS):
                                                PyImGui.table_next_column()
                                                hero_ai_options.Skills[i] = ImGui.toggle_button(f"{i+1}##Skill{i}", hero_ai_options.Skills[i], 22, 22)
                                                ImGui.show_tooltip(f"Skill {i + 1}")
                                            PyImGui.end_table()

                                if PyImGui.tree_node("Buffs"):
                                    buffs = [buff for buff in player.PlayerBuffs if buff != 0]
                                    PyImGui.text(f"Number of Buffs: {len(buffs)}")
                                    if len(buffs) == 0:
                                        PyImGui.text("No buffs found for this player.")
                                    else:
                                        for buff_id in buffs:
                                            buff_name = GLOBAL_CACHE.Skill.GetName(buff_id)
                                            PyImGui.text(f"Buff ID: {buff_id} - Name: {buff_name}")
                                    PyImGui.tree_pop()

                                if PyImGui.tree_node("Heroes"):
                                    heroes = SMM.GetHeroesFromPlayers(player.PlayerID)
                                    PyImGui.text(f"Number of Heroes: {len(heroes)}")
                                    if len(heroes) == 0:
                                        PyImGui.text("No heroes found for this player.")
                                    else:
                                        for hero in heroes:
                                            if PyImGui.tree_node(hero.CharacterName):
                                                if PyImGui.tree_node("Hero Info"):
                                                    PyImGui.text(f"Hero Slot Number: {hero.SlotNumber}")
                                                    PyImGui.text(f"Hero ID: {hero.HeroID}")
                                                    PyImGui.text(f"Hero Player ID: {hero.PlayerID}")
                                                    PyImGui.text(f"Hero HP: {int(hero.PlayerHP*hero.PlayerMaxHP)} / {hero.PlayerMaxHP} Regen Pips: {hero.PlayerHealthRegen:.2f}")
                                                    PyImGui.text(f"Hero Energy: {int(hero.PlayerEnergy*hero.PlayerMaxEnergy)} / {hero.PlayerMaxEnergy} Regen Pips: {hero.PlayerEnergyRegen:.2f}")
                                                    PyImGui.text(f"Hero XYZ: ({hero.PlayerPosX:.2f}, {hero.PlayerPosY:.2f}, {hero.PlayerPosZ:.2f})")
                                                    PyImGui.text(f"Hero Facing Angle: {Utils.RadToDeg(hero.PlayerFacingAngle):.2f}")
                                                    PyImGui.text(f"Hero Target ID: {hero.PlayerTargetID}")
                                                    timestamp = datetime.fromtimestamp(hero.LastUpdated / 1000)
                                                    milliseconds = int(timestamp.microsecond / 1000)
                                                    PyImGui.text(f"Last Updated: {timestamp.strftime('%H:%M:%S')}.{milliseconds:03d}")
                                                    PyImGui.tree_pop()
                                                    PyImGui.separator()

                                                if PyImGui.tree_node("Buffs"):
                                                    hero_buffs = [buff for buff in hero.PlayerBuffs if buff != 0]
                                                    PyImGui.text(f"Number of Buffs: {len(hero_buffs)}")
                                                    if len(hero_buffs) == 0:
                                                        PyImGui.text("No buffs found for this hero.")
                                                    else:
                                                        for buff_id in hero_buffs:
                                                            buff_name = GLOBAL_CACHE.Skill.GetName(buff_id)
                                                            PyImGui.text(f"Buff ID: {buff_id} - Name: {buff_name}")
                                                    PyImGui.tree_pop()
                                                PyImGui.tree_pop()
                                        PyImGui.tree_pop()

                                if PyImGui.tree_node("Pet"):
                                    pets = SMM.GetPetsFromPlayers(player.PlayerID)
                                    PyImGui.text(f"Number of Pets: {len(pets)}")
                                    if len(pets) == 0:
                                        PyImGui.text("No pets found for this player.")
                                    else:
                                        for pet in pets:
                                            if PyImGui.tree_node(pet.CharacterName):
                                                if PyImGui.tree_node("Pet Info"):
                                                    PyImGui.text(f"Pet Slot Number: {pet.SlotNumber}")
                                                    PyImGui.text(f"Pet ID: {pet.PlayerID}")
                                                    PyImGui.text(f"Pet Owner Player ID: {pet.OwnerPlayerID}")
                                                    PyImGui.text(f"Pet HP: {int(pet.PlayerHP*pet.PlayerMaxHP)} / {pet.PlayerMaxHP} Regen Pips: {pet.PlayerHealthRegen:.2f}")
                                                    PyImGui.text(f"Pet Energy: {int(pet.PlayerEnergy*pet.PlayerMaxEnergy)} / {pet.PlayerMaxEnergy} Regen Pips: {pet.PlayerEnergyRegen:.2f}")
                                                    PyImGui.text(f"Pet XYZ: ({pet.PlayerPosX:.2f}, {pet.PlayerPosY:.2f}, {pet.PlayerPosZ:.2f})")
                                                    PyImGui.text(f"Pet Facing Angle: {Utils.RadToDeg(pet.PlayerFacingAngle):.2f}")
                                                    PyImGui.text(f"Pet Target ID: {pet.PlayerTargetID}")
                                                    timestamp = datetime.fromtimestamp(pet.LastUpdated / 1000)
                                                    milliseconds = int(timestamp.microsecond / 1000)
                                                    PyImGui.text(f"Last Updated: {timestamp.strftime('%H:%M:%S')}.{milliseconds:03d}")
                                                    PyImGui.tree_pop()
                                                    PyImGui.separator()

                                                if PyImGui.tree_node("Buffs"):
                                                    pet_buffs = [buff for buff in pet.PlayerBuffs if buff != 0]
                                                    PyImGui.text(f"Number of Buffs: {len(pet_buffs)}")
                                                    if len(pet_buffs) == 0:
                                                        PyImGui.text("No buffs found for this pet.")
                                                    else:
                                                        for buff_id in pet_buffs:
                                                            buff_name = GLOBAL_CACHE.Skill.GetName(buff_id)
                                                            PyImGui.text(f"Buff ID: {buff_id} - Name: {buff_name}")
                                                    PyImGui.tree_pop()
                                                PyImGui.tree_pop()
                                        PyImGui.tree_pop()
                                PyImGui.tree_pop()
                                PyImGui.separator()
                        PyImGui.tree_pop()
                PyImGui.tree_pop()
    PyImGui.end()
    


    
if __name__ == "__main__":
    main()
