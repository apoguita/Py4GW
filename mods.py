from Py4GWCoreLib import *

armor_mods = {
        # region warrior
        '240801F9' : "Knight's Insignia",
        '24080208' : "Lieutenant's Insignia",
        '24080209' : "Stonefist Insignia",
        '240801FA' : "Dreadnought Insignia",
        '240801FB' : "Sentinel's Insignia",
        '240800FC' : "Rune of Minor Absorption",
        '21E81501' : "Rune of Minor Tactics",
        '21E81101' : "Rune of Minor Strength",
        '21E81201' : "Rune of Minor Axe Mastery",
        '21E81301' : "Rune of Minor Hammer Mastery",
        '21E81401' : "Rune of Minor Swordsmanship",
        '240800FD' : "Rune of Major Absorption",
        '21E81502' : "Rune of Major Tactics",
        '21E81102' : "Rune of Major Strength",
        '21E81202' : "Rune of Major Axe Mastery",
        '21E81302' : "Rune of Major Hammer Mastery",
        '21E81402' : "Rune of Major Swordsmanship",
        '240800FE' : "Rune of Superior Absorption",
        '21E81503' : "Rune of Superior Tactics",
        '21E81103' : "Rune of Superior Strength",
        '21E81203' : "Rune of Superior Axe Mastery",
        '21E81303' : "Rune of Superior Hammer Mastery",
        '21E81403' : "Rune of Superior Swordsmanship",
        # endregion
        # region ranger
        '240801FC' : "Frostbound Insignia",
        '240801FE' : "Pyrebound Insignia",
        '240801FF' : "Stormbound Insignia",
        '24080201' : "Scout's Insignia",
        '240801FD' : "Earthbound Insignia",
        '24080200' : "Beastmaster's Insignia",
        '21E81801' : "Rune of Minor Wilderness Survival",
        '21E81701' : "Rune of Minor Expertise",
        '21E81601' : "Rune of Minor Beast Mastery",
        '21E81901' : "Rune of Minor Marksmanship",
        '21E81802' : "Rune of Major Wilderness Survival",
        '21E81702' : "Rune of Major Expertise",
        '21E81602' : "Rune of Major Beast Mastery",
        '21E81902' : "Rune of Major Marksmanship",
        '21E81803' : "Rune of Superior Wilderness Survival",
        '21E81703' : "Rune of Superior Expertise",
        '21E81603' : "Rune of Superior Beast Mastery",
        '21E81903' : "Rune of Superior Marksmanship",
        # endregion
        # region monk
        '240801F6' : "Wanderer's Insignia",
        '240801F7' : "Disciple's Insignia",
        '240801F8' : "Anchorite's Insignia",
        '21E80D01' : "Rune of Minor Healing Prayers",
        '21E80E01' : "Rune of Minor Smiting Prayers",
        '21E80F01' : "Rune of Minor Protection Prayers",
        '21E81001' : "Rune of Minor Divine Favor",
        '21E80D02' : "Rune of Major Healing Prayers",
        '21E80E02' : "Rune of Major Smiting Prayers",
        '21E80F02' : "Rune of Major Protection Prayers",
        '21E81002' : "Rune of Major Divine Favor",
        '21E80D03' : "Rune of Superior Healing Prayers",
        '21E80E03' : "Rune of Superior Smiting Prayers",
        '21E80F03' : "Rune of Superior Protection Prayers",
        '21E81003' : "Rune of Superior Divine Favor",
        # endregion
        # region necromancer
        '2408020A' : "Bloodstained Insignia",
        '240801EC' : "Tormentor's Insignia",
        '240801EE' : "Bonelace Insignia",
        '240801EF' : "Minion Master's Insignia",
        '240801F0' : "Blighter's Insignia",
        '240801ED' : "Undertaker's Insignia",
        '21E80401' : "Rune of Minor Blood Magic",
        '21E80501' : "Rune of Minor Death Magic",
        '21E80701' : "Rune of Minor Curses",
        '21E80601' : "Rune of Minor Soul Reaping",
        '21E80402' : "Rune of Major Blood Magic",
        '21E80502' : "Rune of Major Death Magic",
        '21E80702' : "Rune of Major Curses",
        '21E80602' : "Rune of Major Soul Reaping",
        '21E80403' : "Rune of Superior Blood Magic",
        '21E80503' : "Rune of Superior Death Magic",
        '21E80703' : "Rune of Superior Curses",
        '21E80603' : "Rune of Superior Soul Reaping",
        # endregion
        # region mesmer
        '240801E4' : "Virtuoso's Insignia",
        '240801E2' : "Artificer's Insignia",
        '240801E3' : "Prodigy's Insignia",
        '21E80001' : "Rune of Minor Fast Casting",
        '21E80201' : "Rune of Minor Domination Magic",
        '21E80101' : "Rune of Minor Illusion Magic",
        '21E80301' : "Rune of Minor Inspiration Magic",
        '21E80002' : "Rune of Major Fast Casting",
        '21E80202' : "Rune of Major Domination Magic",
        '21E80102' : "Rune of Major Illusion Magic",
        '21E80302' : "Rune of Major Inspiration Magic",
        '21E80003' : "Rune of Superior Fast Casting",
        '21E80203' : "Rune of Superior Domination Magic",
        '21E80103' : "Rune of Superior Illusion Magic",
        '21E80303' : "Rune of Superior Inspiration Magic",
        # endregion
        # region elementalist
        '240801F2' : "Hydromancer Insignia",
        '240801F3' : "Geomancer Insignia",
        '240801F4' : "Pyromancer Insignia",
        '240801F5' : "Aeromancer Insignia",
        '240801F1' : "Prismatic Insignia",
        '21E80C01' : "Rune of Minor Energy Storage",
        '21E80A01' : "Rune of Minor Fire Magic",
        '21E80801' : "Rune of Minor Air Magic",
        '21E80901' : "Rune of Minor Earth Magic",
        '21E80B01' : "Rune of Minor Water Magic",
        '21E80C02' : "Rune of Major Energy Storage",
        '21E80A02' : "Rune of Major Fire Magic",
        '21E80802' : "Rune of Major Air Magic",
        '21E80902' : "Rune of Major Earth Magic",
        '21E80B02' : "Rune of Major Water Magic",
        '21E80C03' : "Rune of Superior Energy Storage",
        '21E80A03' : "Rune of Superior Fire Magic",
        '21E80803' : "Rune of Superior Air Magic",
        '21E80903' : "Rune of Superior Earth Magic",
        '21E80B03' : "Rune of Superior Water Magic",
        # endregion
        # region assassin
        '240801DE' : "Vanguard's Insignia",
        '240801DF' : "Infiltrator's Insignia",
        '240801E0' : "Saboteur's Insignia",
        '240801E1' : "Nightstalker's Insignia",
        '21E82301' : "Rune of Minor Critical Strikes",
        '21E81D01' : "Rune of Minor Dagger Mastery",
        '21E81E01' : "Rune of Minor Deadly Arts",
        '21E81F01' : "Rune of Minor Shadow Arts",
        '21E82302' : "Rune of Major Critical Strikes",
        '21E81D02' : "Rune of Major Dagger Mastery",
        '21E81E02' : "Rune of Major Deadly Arts",
        '21E81F02' : "Rune of Major Shadow Arts",
        '21E82303' : "Rune of Superior Critical Strikes",
        '21E81D03' : "Rune of Superior Dagger Mastery",
        '21E81E03' : "Rune of Superior Deadly Arts",
        '21E81F03' : "Rune of Superior Shadow Arts",
        # endregion
        # region ritualist
        '24080204' : "Shaman's Insignia",
        '24080205' : "Ghost Forge Insignia",
        '24080206' : "Mystic's Insignia",
        '21E82201' : "Rune of Minor Channeling Magic",
        '21E82101' : "Rune of Minor Restoration Magic",
        '21E82001' : "Rune of Minor Communing",
        '21E82401' : "Rune of Minor Spawning Power",
        '21E82202' : "Rune of Major Channeling Magic",
        '21E82102' : "Rune of Major Restoration Magic",
        '21E82002' : "Rune of Major Communing",
        '21E82402' : "Rune of Major Spawning Power",
        '21E82203' : "Rune of Superior Channeling Magic",
        '21E82103' : "Rune of Superior Restoration Magic",
        '21E82003' : "Rune of Superior Communing",
        '21E82403' : "Rune of Superior Spawning Power",
        # endregion
        # region dervish
        '24080202' : "Windwalker Insignia",
        '24080203' : "Forsaken Insignia",
        '21E82C01' : "Rune of Minor Mysticism",
        '21E82B01' : "Rune of Minor Earth Prayers",
        '21E82901' : "Rune of Minor Scythe Mastery",
        '21E82A01' : "Rune of Minor Wind Prayers",
        '21E82C02' : "Rune of Major Mysticism",
        '21E82B02' : "Rune of Major Earth Prayers",
        '21E82902' : "Rune of Major Scythe Mastery",
        '21E82A02' : "Rune of Major Wind Prayers",
        '21E82C03' : "Rune of Superior Mysticism",
        '21E82B03' : "Rune of Superior Earth Prayers",
        '21E82903' : "Rune of Superior Scythe Mastery",
        '21E82A03' : "Rune of Superior Wind Prayers",
        # endregion
        # region paragon
        '24080207' : "Centurion's Insignia",
        '21E82801' : "Rune of Minor Leadership",
        '21E82701' : "Rune of Minor Motivation",
        '21E82601' : "Rune of Minor Command",
        '21E82501' : "Rune of Minor Spear Mastery",
        '21E82802' : "Rune of Major Leadership",
        '21E82702' : "Rune of Major Motivation",
        '21E82602' : "Rune of Major Command",
        '21E82502' : "Rune of Major Spear Mastery",
        '21E82803' : "Rune of Superior Leadership",
        '21E82703' : "Rune of Superior Motivation",
        '21E82603' : "Rune of Superior Command",
        '21E82503' : "Rune of Superior Spear Mastery",
        # endregion
        # region common
        '240801E6' : "Survivor Insignia",
        '240801E5' : "Radiant Insignia",
        '240801E7' : "Stalwart Insignia",
        '240801E8' : "Brawler's Insignia",
        '240801E9' : "Blessed Insignia",
        '240801EA' : "Herald's Insignia",
        '240801EB' : "Sentry's Insignia",
        '24080211' : "Rune of Attunement",
        '24080213' : "Rune of Recovery",
        '24080214' : "Rune of Restoration",
        '24080215' : "Rune of Clarity",
        '24080216' : "Rune of Purity",
        '240800FF' : "Rune of Minor Vigor",
        '240800C2' : "Rune of Minor Vigor",
        '24080101' : "Rune of Superior Vigor",
        '24080100' : "Rune of Major Vigor",
        '24080212' : "Rune of Vitae"
        # endregion
    }

def GetMods(item_id, mod_list):
    mods = []
    for mod in Item.Customization.Modifiers.GetModifiers(item_id):
        mod_hex = f'{mod.GetIdentifier():04x}{mod.GetArg():04x}'.upper()
        if mod_hex in mod_list:
            mods.append(mod_list[mod_hex])
    return mods
            
first = True
def main():
    global first, armor_mods

    try:
        if first:
            first = False

            bags_to_check = ItemArray.CreateBagList(22)
            item_array = ItemArray.GetItemArray(bags_to_check)
            for item_id in item_array:
                mods = GetMods(item_id,armor_mods)
                for mod in mods:
                    Py4GW.Console.Log('Mods', f'ItemID: {item_id} contains mod: {mod}', Py4GW.Console.MessageType.Info)

    except ImportError as e:
        Py4GW.Console.Log('BOT', f'ImportError encountered: {str(e)}', Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log('BOT', f'Stack trace: {traceback.format_exc()}', Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log('BOT', f'ValueError encountered: {str(e)}', Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log('BOT', f'Stack trace: {traceback.format_exc()}', Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log('BOT', f'TypeError encountered: {str(e)}', Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log('BOT', f'Stack trace: {traceback.format_exc()}', Py4GW.Console.MessageType.Error)
    except Exception as e:
        Py4GW.Console.Log('BOT', f'Unexpected error encountered: {str(e)}', Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log('BOT', f'Stack trace: {traceback.format_exc()}', Py4GW.Console.MessageType.Error)
    finally:
        pass

if __name__ == '__main__':
    main()