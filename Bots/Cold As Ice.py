from Py4GWCoreLib import *
bot = Botting("Cold As Ice")

def EquipSkillBar(): 
    global bot

    profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())

    if profession == "Dervish":
        yield from Routines.Yield.Skills.LoadSkillbar("OgSCU8pkcQZwnwWIAAAAAAAA")
    elif profession == "Ritualist":    
        yield from Routines.Yield.Skills.LoadSkillbar("OASjUwHKIRyBlBfCbhAAAAAAAAA")
    elif profession == "Warrior":
        yield from Routines.Yield.Skills.LoadSkillbar("OQQTU4DHHaLUOoM4TAAAAAAAAAA")
    elif profession == "Ranger":
        yield from Routines.Yield.Skills.LoadSkillbar("OgQTU4DfHaLUOoM4TAAAAAAAAAA")
    elif profession == "Necromancer":
         yield from Routines.Yield.Skills.LoadSkillbar("OApCU8pkcQZwnwWIAAAAAAAA")
    elif profession == "Elementalist":
         yield from Routines.Yield.Skills.LoadSkillbar("OgRDU8x8QbhyBlBfCAAAAAAAAA")
    elif profession == "Mesmer":
        yield from Routines.Yield.Skills.LoadSkillbar("OQRDATxHTbhyBlBfCAAAAAAAAA")
    elif profession == "Monk":
        yield from Routines.Yield.Skills.LoadSkillbar("OwQTU4DDHaLUOoM4TAAAAAAAAAA")
    elif profession == "Assasin":
        yield from Routines.Yield.Skills.LoadSkillbar("OwRjUwH84QbhyBlBfCAAAAAAAAA")
    elif profession == "Paragon":
        yield from Routines.Yield.Skills.LoadSkillbar("OQSCU8pkcQZwnwWIAAAAAAAA")    

def Routine(bot: Botting) -> None:
    bot.Map.Travel(target_map_name="Sifhalla")
    bot.Wait.ForMapLoad(target_map_id=643)
    bot.Properties.Enable("pause_on_danger")
    bot.Properties.Disable("halt_on_death")
    bot.Properties.Set("movement_timeout",value=-1)
    bot.Properties.Enable("auto_combat")
    bot.Items.SpawnBonusItems()
    bot.Items.Equip(ModelID.Bonus_Nevermore_Flatbow.value) #simple swap to prevent error
    bot.Items.Equip(6515) #Necro Bonus Staff
    bot.States.AddCustomState(EquipSkillBar, "Equip Skill Bar")
    bot.States.AddHeader("Cold As Ice")
    bot.Move.XYAndDialog(14380, 23968, 0x834401) #Cold As Ice
    bot.Dialogs.AtXY(14380, 23968, 0x85) #I am Ready
    bot.Wait.ForMapLoad(target_map_id=690) #Special Sifhalla Map
    bot.Wait.ForTime(5000)
    bot.Move.XY(14553, 23043)
    bot.Wait.ForTime(2000)
    bot.SkillBar.UseSkill(114)
    bot.Wait.UntilOnCombat()
    bot.Wait.UntilOutOfCombat()
    bot.Multibox.ResignParty()
    bot.Wait.ForTime(20000)
    bot.Wait.ForMapLoad(target_map_id=643)
    bot.Move.XYAndDialog(14380, 23968, 0x834407) #Rewards
bot.SetMainRoutine(Routine)

def main():
    bot.Update()
    bot.UI.draw_window(icon_path="IAU.png")


if __name__ == "__main__":
    main()