from Py4GWCoreLib import *

bot = Botting("Norn by Wick Divinus")

def Routine(bot: Botting) -> None:
    bot.Properties.ApplyNow("pause_on_danger", "active", True)
    bot.Properties.ApplyNow("halt_on_death","active", True)
    bot.Properties.ApplyNow("movement_timeout","value", 15000)
    bot.Properties.ApplyNow("auto_combat","active", True)
    #bot.Properties.Enable("birthday_cupcake")
    #bot.Properties.Enable("war_supplies")
    bot.Properties.Enable("honeycomb")
    bot.Properties.Enable("essence_of_celerity")
    bot.Properties.Enable("grail_of_might")
    bot.Properties.Enable("armor_of_salvation")
    
    bot.States.AddHeader("Travel to Olafstead")
    bot.Map.Travel(target_map_id=645) #Olafstead outpost
    bot.Party.SetHardMode(True)
    bot.States.AddHeader("EXIT OUTPOST HEADER")
    bot.Move.XY(-1440, 1147.5,"Exit Outpost")
    bot.Wait.ForMapLoad(target_map_id=553)
    #bot.Multibox.UsePConSet() #Conset
    bot.Multibox.UseConsumable(22269, 0) #Cupcake
    bot.Multibox.UseConsumable(28431, 0) #Apple
    bot.Multibox.UseConsumable(28432, 0) #Candy
    bot.Multibox.UseConsumable(22752, 0) #Egg
    bot.Multibox.UseConsumable(28436, 0) #Pies
    bot.Multibox.UseConsumable(35121, 0) #WarSupplies
    bot.Move.XY(-2484.73, 118.55, "Start")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-3059.12, -419.00, "Move to bridge")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-3301.01, -2008.23, "Move to shrine")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-2034, -4512, "Move to blessing")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Wait.ForTime(5000)
    bot.Interact.GetBlessing()
    bot.Wait.ForTime(10000)

    bot.Move.XY(-5278, -5771, "Aggro: Berzerker")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-5456, -7921, "Aggro: Berzerker")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-8793, -5837, "Aggro: Berzerker")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-14092, -9662, "Aggro: Vaettir and Berzerker")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-17260, -7906, "Aggro: Vaettir and Berzerker")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-21964, -12877, "Aggro: Jotun")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Wait.ForTime(5000)
    bot.Interact.GetBlessing()
    bot.Wait.ForTime(10000)

    bot.Move.XY(-22275, -12462, "Move to area 2")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-21671, -2163, "Aggro: Berzerker")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-19592, 772, "Aggro: Berzerker")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-13795, -751, "Aggro: Berzerker")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-17012, -5376, "Aggro: Berzerker")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Wait.ForTime(5000)
    bot.Interact.GetBlessing()
    bot.Wait.ForTime(10000)

    bot.Move.XY(-12071, -4274, "Aggro: Berzerker")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-8351, -2633, "Move to regroup")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-4362, -1610, "Aggro: Lake")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-4316, 4033, "Aggro: Lake")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-8809, 5639, "Aggro: Lake")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-14916, 2475, "Take blessing 3")
    bot.Wait.ForTime(5000)
    bot.Interact.GetBlessing()
    bot.Wait.ForTime(10000)

    bot.Move.XY(-11282, 5466, "Aggro: Elemental")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-16051, 6492, "Aggro: Elemental")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-16934, 11145, "Aggro: Elemental")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-19378, 14555, "Take blessing 4")
    bot.Wait.ForTime(5000)
    bot.Interact.GetBlessing()
    bot.Wait.ForTime(10000)

    bot.Move.XY(-22751, 14163, "Aggro: Elemental")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-15932, 9386, "Move to camp")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-13777, 8097, "Aggro: Lake")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-4729, 15385, "Take blessing 5")
    bot.Wait.ForTime(5000)
    bot.Interact.GetBlessing()
    bot.Wait.ForTime(10000)

    bot.Move.XY(-2290, 14879, "Aggro: Modnir")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-1810, 4679, "Move to boss")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-6911, 5240, "Aggro: Boss")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-15471, 6384, "Move to regroup")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(-411, 5874, "Aggro: Modniir")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(2859, 3982, "Aggro: Ice Imp")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(4909, -4259, "Aggro: Ice Imp")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(7514, -6587, "Aggro: Berserker")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(3800, -6182, "Aggro: Berserker")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(7755, -11467, "Aggro: Elementals and Griffins")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(15403, -4243, "Aggro: Elementals and Griffins")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(21597, -6798, "Take blessing 6")
    bot.Wait.ForTime(5000)
    bot.Interact.GetBlessing()
    bot.Wait.ForTime(10000)

    bot.Move.XY(24522, -6532, "Aggro: Unknown")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(22883, -4248, "Aggro: Unknown")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(18606, -1894, "Aggro: Unknown")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(14969, -4048, "Aggro: Unknown")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)

    bot.Move.XY(13599, -7339, "Aggro: Ice Imp")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)
    bot.Move.XY(10056, -4967, "Aggro: Ice Imp")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)
    bot.Move.XY(10147, -1630, "Aggro: Ice Imp")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)
    bot.Move.XY(8963, 4043, "Take blessing 7")
    bot.Wait.ForTime(5000)
    bot.Interact.GetBlessing()
    bot.Wait.ForTime(10000)
    bot.Move.XY(9339.46, 3859.12, "Aggro: Unknown")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)
    bot.Move.XY(15576, 7156, "Aggro: Berserker")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)
    bot.Move.XY(22838, 7914, "Take blessing 8")
    bot.Wait.ForTime(5000)
    bot.Interact.GetBlessing()
    bot.Wait.ForTime(10000)
    bot.Move.XY(22961, 12757, "Move to shrine")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)
    bot.Move.XY(18067, 8766, "Aggro: Modniir and Elemental")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)
    bot.Move.XY(13311, 11917, "Take blessing 9")
    bot.Wait.ForTime(5000)
    bot.Interact.GetBlessing()
    bot.Wait.ForTime(10000)
    bot.Move.XY(13714, 14520, "Aggro: Modniir and Elemental")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)
    bot.Move.XY(11126, 10443, "Aggro: Modniir and Elemental")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)
    bot.Move.XY(5575, 4696, "Aggro: Modniir and Elemental")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)
    bot.Move.XY(-503, 9182, "Aggro: Modniir and Elemental 2")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)
    bot.Move.XY(1582, 15275, "Aggro: Modniir and Elemental 2")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)
    bot.Move.XY(7857, 10409, "Aggro: Modniir and Elemental 2")
    bot.Wait.UntilOutOfCombat(Range.Spellcast)
    #bot.Party.Resign()
    bot.Multibox.ResignParty()
    bot.Wait.ForMapToChange(target_map_id=645)
    bot.States.JumpToStepName("[H]Travel to Olafstead_1")


    
bot.SetMainRoutine(Routine)


def main():
    bot.Update()
    bot.UI.draw_window()

if __name__ == "__main__":
    main()
