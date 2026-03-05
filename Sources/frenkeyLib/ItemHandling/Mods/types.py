from enum import Enum, IntEnum

from Py4GWCoreLib.enums_src.Item_enums import ItemType

class ItemBaneSpecies(IntEnum):
    Undead = 0
    Charr = 1
    Trolls = 2
    Plants = 3
    Skeletons = 4
    Giants = 5
    Dwarves = 6
    Tengus = 7
    Demons = 8
    Dragons = 9
    Ogres = 10
    Unknown = -1
    
class ItemModifierParam(IntEnum):
    LabelInName = 0x0
    Description = 0x8
    
class ItemUpgradeType(IntEnum):    
    Unknown = 0
    Prefix = 1
    Suffix = 2
    Inscription = 3
    UpgradeRune = 4
    AppliesToRune = 5
    
class ModifierIdentifier(IntEnum):
    Armor1 = 0x27b
    Armor2 = 0x23c
    ArmorEnergyRegen = 0x22e
    ArmorMinusAttacking = 0x201
    ArmorPenetration = 0x23f
    ArmorPlus = 0x210
    ArmorPlusAttacking = 0x217
    ArmorPlusCasting = 0x218
    ArmorPlusEnchanted = 0x219
    ArmorPlusHexed = 0x21c
    ArmorPlusAbove = 0x21a
    ArmorPlusVsDamage = 0x211
    ArmorPlusVsElemental = 0x212
    ArmorPlusVsPhysical = 0x215
    ArmorPlusVsPhysical2 = 0x216
    ArmorPlusVsSpecies = 0x214
    ArmorPlusWhileDown = 0x21b
    AttributePlusOne = 0x241
    AttributePlusOneItem = 0x283
    AttributeRequirement = 0x279
    BaneSpecies = 0x8
    Damage = 0x27a
    Damage2 = 0x248
    DamageCustomized = 0x249
    DamagePlusEnchanted = 0x226
    DamagePlusHexed = 0x229
    DamagePlusPercent = 0x223
    DamagePlusStance = 0x22a
    DamagePlusVsHexed = 0x225
    DamagePlusVsSpecies = 0x224
    DamagePlusWhileDown = 0x228
    DamagePlusWhileUp = 0x227
    DamageTypeProperty = 0x24b
    Energy = 0x27c
    Energy2 = 0x22c
    EnergyDegen = 0x20c
    EnergyGainOnHit = 0x251
    EnergyMinus = 0x20b
    EnergyPlus = 0x22d
    EnergyPlusEnchanted = 0x22f
    EnergyPlusHexed = 0x232
    EnergyPlusWhileBelow = 0x231
    Furious = 0x23b
    HalvesCastingTimeAttribute = 0x221
    HalvesCastingTimeGeneral = 0x220
    HalvesCastingTimeItemAttribute = 0x280
    HalvesSkillRechargeAttribute = 0x239
    HalvesSkillRechargeGeneral = 0x23a
    HalvesSkillRechargeItemAttribute = 0x282
    HeadpieceAttribute = 0x21f
    HeadpieceGenericAttribute = 0x284
    HealthDegen = 0x20e
    HealthMinus = 0x20d
    HealthPlus = 0x234
    HealthPlus2 = 0x289
    HealthPlusEnchanted = 0x236
    HealthPlusHexed = 0x237
    HealthPlusStance = 0x238
    EnergyPlusWhileDown = 0x230
    HealthStealOnHit = 0x252
    HighlySalvageable = 0x260
    IncreaseConditionDuration = 0x246
    IncreaseEnchantmentDuration = 0x22b
    IncreasedSaleValue = 0x25f
    Infused = 0x262
    OfTheProfession = 0x28a
    ReceiveLessDamage = 0x207
    ReceiveLessPhysDamageEnchanted = 0x208
    ReceiveLessPhysDamageHexed = 0x209
    ReceiveLessPhysDamageStance = 0x20a
    ReduceConditionDuration = 0x285
    ReduceConditionTupleDuration = 0x277
    ReducesDiseaseDuration = 0x247
    TargetItemType = 0x25b
    TooltipDescription = 0x253
    AttributeRune = 0x21e
    Upgrade = 0x240

class ItemUpgradeId(IntEnum):
    Unknown = -1
    Icy_Axe = 0x0081
    Ebon_Axe = 0x0082
    Shocking_Axe = 0x0083
    Fiery_Axe = 0x0084
    Barbed_Axe = 0x0092
    Crippling_Axe = 0x0094
    Cruel_Axe = 0x0096
    Furious_Axe = 0x0099
    Poisonous_Axe = 0x009E
    Heavy_Axe = 0x00A1
    Zealous_Axe = 0x00A3
    Vampiric_Axe = 0x00A7
    Sundering_Axe = 0x00AB
    OfDefense_Axe = 0x00C5
    OfWarding_Axe = 0x00C7
    OfShelter_Axe = 0x00CD
    OfSlaying_Axe = 0x00D4
    OfFortitude_Axe = 0x00D9
    OfEnchanting_Axe = 0x00DE
    OfAxeMastery = 0x00E8
    OfTheProfession_Axe = 0x0226
    Icy_Bow = 0x0085
    Ebon_Bow = 0x0086
    Shocking_Bow = 0x0087
    Fiery_Bow = 0x0088
    Poisonous_Bow = 0x009F
    Zealous_Bow = 0x00A5
    Vampiric_Bow = 0x00A9
    Sundering_Bow = 0x00AD
    OfDefense_Bow = 0x00C6
    OfWarding_Bow = 0x00C8
    OfShelter_Bow = 0x00CE
    OfSlaying_Bow = 0x00D5
    OfFortitude_Bow = 0x00DA
    OfEnchanting_Bow = 0x00DF
    OfMarksmanship = 0x00E9
    Barbed_Bow = 0x0147
    Crippling_Bow = 0x0148
    Silencing_Bow = 0x0149
    OfTheProfession_Bow = 0x0227
    Icy_Daggers = 0x012E
    Ebon_Daggers = 0x012F
    Fiery_Daggers = 0x0130
    Shocking_Daggers = 0x0131
    Zealous_Daggers = 0x0132
    Vampiric_Daggers = 0x0133
    Sundering_Daggers = 0x0134
    Barbed_Daggers = 0x0135
    Crippling_Daggers = 0x0136
    Cruel_Daggers = 0x0137
    Poisonous_Daggers = 0x0138
    Silencing_Daggers = 0x0139
    Furious_Daggers = 0x013A
    OfDefense_Daggers = 0x0141
    OfWarding_Daggers = 0x0142
    OfShelter_Daggers = 0x0143
    OfEnchanting_Daggers = 0x0144
    OfFortitude_Daggers = 0x0145
    OfDaggerMastery = 0x0146
    OfTheProfession_Daggers = 0x0228
    OfAptitude_Focus = 0x0217
    OfFortitude_Focus = 0x0218
    OfDevotion_Focus = 0x0219
    OfValor_Focus = 0x021A
    OfEndurance_Focus = 0x021B
    OfSwiftness_Focus = 0x021C
    Icy_Hammer = 0x0089
    Ebon_Hammer = 0x008A
    Shocking_Hammer = 0x008B
    Fiery_Hammer = 0x008C
    Cruel_Hammer = 0x0097
    Furious_Hammer = 0x009A
    Heavy_Hammer = 0x00A2
    Zealous_Hammer = 0x00A4
    Vampiric_Hammer = 0x00A8
    Sundering_Hammer = 0x00AC
    OfWarding_Hammer = 0x00C9
    OfDefense_Hammer = 0x00CC
    OfShelter_Hammer = 0x00CF
    OfSlaying_Hammer = 0x00D6
    OfFortitude_Hammer = 0x00DB
    OfEnchanting_Hammer = 0x00E0
    OfHammerMastery = 0x00EA
    OfTheProfession_Hammer = 0x0229
    
    IHaveThePower = 0x015C
    LetTheMemoryLiveAgain = 0x015E
    TooMuchInformation = 0x0163
    GuidedByFate = 0x0164
    StrengthAndHonor = 0x0165
    VengeanceIsMine = 0x0166
    DontFearTheReaper = 0x0167
    DanceWithDeath = 0x0168
    BrawnOverBrains = 0x0169
    ToThePain = 0x016A
    IgnoranceIsBliss = 0x01B6
    LifeIsPain = 0x01B7
    ManForAllSeasons = 0x01B8
    SurvivalOfTheFittest = 0x01B9
    MightMakesRight = 0x01BA
    KnowingIsHalfTheBattle = 0x01BB
    FaithIsMyShield = 0x01BC
    DownButNotOut = 0x01BD
    HailToTheKing = 0x01BE
    BeJustAndFearNot = 0x01BF
    LiveForToday = 0x01C0
    SerenityNow = 0x01C1
    ForgetMeNot = 0x01C2
    NotTheFace = 0x01C3
    LeafOnTheWind = 0x01C4
    LikeARollingStone = 0x01C5
    RidersOnTheStorm = 0x01C6
    SleepNowInTheFire = 0x01C7
    ThroughThickAndThin = 0x01C8
    TheRiddleOfSteel = 0x01C9
    FearCutsDeeper = 0x01CA
    ICanSeeClearlyNow = 0x01CB
    SwiftAsTheWind = 0x01CC
    StrengthOfBody = 0x01CD
    CastOutTheUnclean = 0x01CE
    PureOfHeart = 0x01CF
    SoundnessOfMind = 0x01D0
    OnlyTheStrongSurvive = 0x01D1
    LuckOfTheDraw = 0x01D2
    ShelteredByFaith = 0x01D3
    NothingToFear = 0x01D4
    RunForYourLife = 0x01D5
    MasterOfMyDomain = 0x01D6
    AptitudeNotAttitude = 0x01D7
    SeizeTheDay = 0x01D8
    HaveFaith = 0x01D9
    HaleAndHearty = 0x01DA
    DontCallItAComeback = 0x01DB
    IAmSorrow = 0x01DC
    DontThinkTwice = 0x01DD
    ShowMeTheMoney = 0x021E
    MeasureForMeasure = 0x021F
    
    Icy_Scythe = 0x016B
    Ebon_Scythe = 0x016C
    Zealous_Scythe = 0x016F
    Vampiric_Scythe = 0x0171
    Sundering_Scythe = 0x0173
    Barbed_Scythe = 0x0174
    Crippling_Scythe = 0x0175
    Cruel_Scythe = 0x0176
    Poisonous_Scythe = 0x0177
    Heavy_Scythe = 0x0178
    Furious_Scythe = 0x0179
    OfDefense_Scythe = 0x0188
    OfWarding_Scythe = 0x0189
    OfShelter_Scythe = 0x018A
    OfEnchanting_Scythe = 0x018B
    OfFortitude_Scythe = 0x018C
    OfScytheMastery = 0x018D
    Fiery_Scythe = 0x020B
    Shocking_Scythe = 0x020C
    OfTheProfession_Scythe = 0x022C
    OfValor_Shield = 0x0151
    OfEndurance_Shield = 0x0152
    OfFortitude_Shield = 0x0161
    OfDevotion_Shield = 0x0162
    Fiery_Spear = 0x016D
    Shocking_Spear = 0x016E
    Zealous_Spear = 0x0170
    Vampiric_Spear = 0x0172
    Sundering_Spear = 0x017A
    Barbed_Spear = 0x017B
    Crippling_Spear = 0x017C
    Cruel_Spear = 0x017D
    Poisonous_Spear = 0x017E
    Silencing_Spear = 0x017F
    Furious_Spear = 0x0180
    Heavy_Spear = 0x0181
    OfDefense_Spear = 0x018E
    OfWarding_Spear = 0x018F
    OfShelter_Spear = 0x0190
    OfEnchanting_Spear = 0x0191
    OfFortitude_Spear = 0x0192
    OfSpearMastery = 0x0193
    Icy_Spear = 0x020D
    Ebon_Spear = 0x020E
    OfTheProfession_Spear = 0x022D
    
    Defensive_Staff = 0x0091
    Insightful_Staff = 0x009C
    Hale_Staff = 0x009D
    OfAttribute_Staff = 0x00C3
    OfWarding_Staff = 0x00CA
    OfShelter_Staff = 0x00D0
    OfDefense_Staff = 0x00D2
    OfSlaying_Staff = 0x00D7
    OfFortitude_Staff = 0x00DC
    OfEnchanting_Staff = 0x00E1
    OfMastery_Staff = 0x0153
    OfDevotion_Staff = 0x0154
    OfValor_Staff = 0x0155
    OfEndurance_Staff = 0x0156
    Swift_Staff = 0x020F
    Adept_Staff = 0x0210
    OfTheProfession_Staff = 0x022B
    Icy_Sword = 0x008D
    Ebon_Sword = 0x008E
    Shocking_Sword = 0x008F
    Fiery_Sword = 0x0090
    Barbed_Sword = 0x0093
    Crippling_Sword = 0x0095
    Cruel_Sword = 0x0098
    Furious_Sword = 0x009B
    Poisonous_Sword = 0x00A0
    Zealous_Sword = 0x00A6
    Vampiric_Sword = 0x00AA
    Sundering_Sword = 0x00AE
    OfWarding_Sword = 0x00CB
    OfShelter_Sword = 0x00D1
    OfDefense_Sword = 0x00D3
    OfSlaying_Sword = 0x00D8
    OfFortitude_Sword = 0x00DD
    OfEnchanting_Sword = 0x00E2
    OfSwordsmanship = 0x00EB
    OfTheProfession_Sword = 0x022E
    OfMemory_Wand = 0x015F
    OfQuickening_Wand = 0x0160
    OfTheProfession_Wand = 0x022A
    
    Survivor = 0x01E6
    Radiant = 0x01E5
    Stalwart = 0x01E7
    Brawlers = 0x01E8
    Blessed = 0x01E9
    Heralds = 0x01EA
    Sentrys = 0x01EB
    Knights = 0x01F9
    Lieutenants = 0x0208
    Stonefist = 0x0209
    Dreadnought = 0x01FA
    Sentinels = 0x01FB
    Frostbound = 0x01FC
    Pyrebound = 0x01FE
    Stormbound = 0x01FF
    Scouts = 0x0201
    Earthbound = 0x01FD
    Beastmasters = 0x0200
    Wanderers = 0x01F6
    Disciples = 0x01F7
    Anchorites = 0x01F8
    Bloodstained = 0x020A
    Tormentors = 0x01EC
    Bonelace = 0x01EE
    MinionMasters = 0x01EF
    Blighters = 0x01F0
    Undertakers = 0x01ED
    Virtuosos = 0x01E4
    Artificers = 0x01E2
    Prodigys = 0x01E3
    Hydromancer = 0x01F2
    Geomancer = 0x01F3
    Pyromancer = 0x01F4
    Aeromancer = 0x01F5
    Prismatic = 0x01F1
    Vanguards = 0x01DE
    Infiltrators = 0x01DF
    Saboteurs = 0x01E0
    Nightstalkers = 0x01E1
    Shamans = 0x0204
    GhostForge = 0x0205
    Mystics = 0x0206
    Windwalker = 0x0202
    Forsaken = 0x0203
    Centurions = 0x0207
    
    OfAttunement = 0x0211
    OfRecovery = 0x0213
    OfRestoration = 0x0214
    OfClarity = 0x0215
    OfPurity = 0x0216
    OfMinorVigor = 0x00FF
    OfMinorVigor2 = 0x00C2
    OfSuperiorVigor = 0x0101
    OfMajorVigor = 0x0100
    OfVitae = 0x0212
    OfMinorAbsorption = 0x00FC
    OfMinorTactics = 0x1501
    OfMinorStrength = 0x1101
    OfMinorAxeMastery = 0x1201
    OfMinorHammerMastery = 0x1301
    OfMinorSwordsmanship = 0x1401
    OfMajorAbsorption = 0x00FD
    OfMajorTactics = 0x1502
    OfMajorStrength = 0x1102
    OfMajorAxeMastery = 0x1202
    OfMajorHammerMastery = 0x1302
    OfMajorSwordsmanship = 0x1402
    OfSuperiorAbsorption = 0x00FE
    OfSuperiorTactics = 0x1503
    OfSuperiorStrength = 0x1103
    OfSuperiorAxeMastery = 0x1203
    OfSuperiorHammerMastery = 0x1303
    OfSuperiorSwordsmanship = 0x1403
    OfMinorWildernessSurvival = 0x1801
    OfMinorExpertise = 0x1701
    OfMinorBeastMastery = 0x1601
    OfMinorMarksmanship = 0x1901
    OfMajorWildernessSurvival = 0x1802
    OfMajorExpertise = 0x1702
    OfMajorBeastMastery = 0x1602
    OfMajorMarksmanship = 0x1902
    OfSuperiorWildernessSurvival = 0x1803
    OfSuperiorExpertise = 0x1703
    OfSuperiorBeastMastery = 0x1603
    OfSuperiorMarksmanship = 0x1903
    OfMinorHealingPrayers = 0x0D01
    OfMinorSmitingPrayers = 0x0E01
    OfMinorProtectionPrayers = 0x0F01
    OfMinorDivineFavor = 0x1001
    OfMajorHealingPrayers = 0x0D02
    OfMajorSmitingPrayers = 0x0E02
    OfMajorProtectionPrayers = 0x0F02
    OfMajorDivineFavor = 0x1002
    OfSuperiorHealingPrayers = 0x0D03
    OfSuperiorSmitingPrayers = 0x0E03
    OfSuperiorProtectionPrayers = 0x0F03
    OfSuperiorDivineFavor = 0x1003
    OfMinorBloodMagic = 0x0401
    OfMinorDeathMagic = 0x0501
    OfMinorCurses = 0x0701
    OfMinorSoulReaping = 0x0601
    OfMajorBloodMagic = 0x0402
    OfMajorDeathMagic = 0x0502
    OfMajorCurses = 0x0702
    OfMajorSoulReaping = 0x0602
    OfSuperiorBloodMagic = 0x0403
    OfSuperiorDeathMagic = 0x0503
    OfSuperiorCurses = 0x0703
    OfSuperiorSoulReaping = 0x0603
    OfMinorFastCasting = 0x0001
    OfMinorDominationMagic = 0x0201
    OfMinorIllusionMagic = 0x0101
    OfMinorInspirationMagic = 0x0301
    OfMajorFastCasting = 0x0002
    OfMajorDominationMagic = 0x0202
    OfMajorIllusionMagic = 0x0102
    OfMajorInspirationMagic = 0x0302
    OfSuperiorFastCasting = 0x0003
    OfSuperiorDominationMagic = 0x0203
    OfSuperiorIllusionMagic = 0x0103
    OfSuperiorInspirationMagic = 0x0303
    OfMinorEnergyStorage = 0x0C01
    OfMinorFireMagic = 0x0A01
    OfMinorAirMagic = 0x0801
    OfMinorEarthMagic = 0x0901
    OfMinorWaterMagic = 0x0B01
    OfMajorEnergyStorage = 0x0C02
    OfMajorFireMagic = 0x0A02
    OfMajorAirMagic = 0x0802
    OfMajorEarthMagic = 0x0902
    OfMajorWaterMagic = 0x0B02
    OfSuperiorEnergyStorage = 0x0C03
    OfSuperiorFireMagic = 0x0A03
    OfSuperiorAirMagic = 0x0803
    OfSuperiorEarthMagic = 0x0903
    OfSuperiorWaterMagic = 0x0B03
    OfMinorCriticalStrikes = 0x2301
    OfMinorDaggerMastery = 0x1D01
    OfMinorDeadlyArts = 0x1E01
    OfMinorShadowArts = 0x1F01
    OfMajorCriticalStrikes = 0x2302
    OfMajorDaggerMastery = 0x1D02
    OfMajorDeadlyArts = 0x1E02
    OfMajorShadowArts = 0x1F02
    OfSuperiorCriticalStrikes = 0x2303
    OfSuperiorDaggerMastery = 0x1D03
    OfSuperiorDeadlyArts = 0x1E03
    OfSuperiorShadowArts = 0x1F03
    OfMinorChannelingMagic = 0x2201
    OfMinorRestorationMagic = 0x2101
    OfMinorCommuning = 0x2001
    OfMinorSpawningPower = 0x2401
    OfMajorChannelingMagic = 0x2202
    OfMajorRestorationMagic = 0x2102
    OfMajorCommuning = 0x2002
    OfMajorSpawningPower = 0x2402
    OfSuperiorChannelingMagic = 0x2203
    OfSuperiorRestorationMagic = 0x2103
    OfSuperiorCommuning = 0x2003
    OfSuperiorSpawningPower = 0x2403
    OfMinorMysticism = 0x2C01
    OfMinorEarthPrayers = 0x2B01
    OfMinorScytheMastery = 0x2901
    OfMinorWindPrayers = 0x2A01
    OfMajorMysticism = 0x2C02
    OfMajorEarthPrayers = 0x2B02
    OfMajorScytheMastery = 0x2902
    OfMajorWindPrayers = 0x2A02
    OfSuperiorMysticism = 0x2C03
    OfSuperiorEarthPrayers = 0x2B03
    OfSuperiorScytheMastery = 0x2903
    OfSuperiorWindPrayers = 0x2A03
    OfMinorLeadership = 0x2801
    OfMinorMotivation = 0x2701
    OfMinorCommand = 0x2601
    OfMinorSpearMastery = 0x2501
    OfMajorLeadership = 0x2802
    OfMajorMotivation = 0x2702
    OfMajorCommand = 0x2602
    OfMajorSpearMastery = 0x2502
    OfSuperiorLeadership = 0x2803
    OfSuperiorMotivation = 0x2703
    OfSuperiorCommand = 0x2603
    OfSuperiorSpearMastery = 0x2503
    
    UpgradeMinorRune_Warrior = 0x00B3
    AppliesToMinorRune_Warrior = 0x0167
    UpgradeMajorRune_Warrior = 0x00B9
    AppliesToMajorRune_Warrior = 0x0173
    UpgradeSuperiorRune_Warrior = 0x00BF
    AppliesToSuperiorRune_Warrior = 0x017F
    UpgradeMinorRune_Ranger = 0x00B4
    AppliesToMinorRune_Ranger = 0x0169
    UpgradeMajorRune_Ranger = 0x00BA
    AppliesToMajorRune_Ranger = 0x0175
    UpgradeSuperiorRune_Ranger = 0x00C0
    AppliesToSuperiorRune_Ranger = 0x0181
    UpgradeMinorRune_Monk = 0x00B2
    AppliesToMinorRune_Monk = 0x0165
    UpgradeMajorRune_Monk = 0x00B8
    AppliesToMajorRune_Monk = 0x0171
    UpgradeSuperiorRune_Monk = 0x00BE
    AppliesToSuperiorRune_Monk = 0x017D
    UpgradeMinorRune_Necromancer = 0x00B0
    AppliesToMinorRune_Necromancer = 0x0161
    UpgradeMajorRune_Necromancer = 0x00B6
    AppliesToMajorRune_Necromancer = 0x016D
    UpgradeSuperiorRune_Necromancer = 0x00BC
    AppliesToSuperiorRune_Necromancer = 0x0179
    UpgradeMinorRune_Mesmer = 0x00AF
    AppliesToMinorRune_Mesmer = 0x015F
    UpgradeMajorRune_Mesmer = 0x00B5
    AppliesToMajorRune_Mesmer = 0x016B
    UpgradeSuperiorRune_Mesmer = 0x00BB
    AppliesToSuperiorRune_Mesmer = 0x0177
    UpgradeMinorRune_Elementalist = 0x00B1
    AppliesToMinorRune_Elementalist = 0x0163
    UpgradeMajorRune_Elementalist = 0x00B7
    AppliesToMajorRune_Elementalist = 0x016F
    UpgradeSuperiorRune_Elementalist = 0x00BD
    AppliesToSuperiorRune_Elementalist = 0x017B
    UpgradeMinorRune_Assassin = 0x013B
    AppliesToMinorRune_Assassin = 0x0277
    UpgradeMajorRune_Assassin = 0x014C
    AppliesToMajorRune_Assassin = 0x0279
    UpgradeSuperiorRune_Assassin = 0x013D
    AppliesToSuperiorRune_Assassin = 0x027B
    UpgradeMinorRune_Ritualist = 0x013E
    AppliesToMinorRune_Ritualist = 0x027D
    UpgradeMajorRune_Ritualist = 0x013F
    AppliesToMajorRune_Ritualist = 0x027F
    UpgradeSuperiorRune_Ritualist = 0x0140
    AppliesToSuperiorRune_Ritualist = 0x0281
    UpgradeMinorRune_Dervish = 0x0182
    AppliesToMinorRune_Dervish = 0x0305
    UpgradeMajorRune_Dervish = 0x0183
    AppliesToMajorRune_Dervish = 0x0307
    UpgradeSuperiorRune_Dervish = 0x0184
    AppliesToSuperiorRune_Dervish = 0x0309
    UpgradeMinorRune_Paragon = 0x0185
    AppliesToMinorRune_Paragon = 0x030B
    UpgradeMajorRune_Paragon = 0x0186
    AppliesToMajorRune_Paragon = 0x030D
    UpgradeSuperiorRune_Paragon = 0x0187
    AppliesToSuperiorRune_Paragon = 0x030F

class ItemUpgrade(Enum):
    Unknown = ItemUpgradeId.Unknown
    Adept = {
        ItemType.Staff: ItemUpgradeId.Adept_Staff,
    }
    Icy = {
        ItemType.Axe: ItemUpgradeId.Icy_Axe,
        ItemType.Bow: ItemUpgradeId.Icy_Bow,
        ItemType.Daggers: ItemUpgradeId.Icy_Daggers,
        ItemType.Hammer: ItemUpgradeId.Icy_Hammer,
        ItemType.Scythe: ItemUpgradeId.Icy_Scythe,
        ItemType.Spear: ItemUpgradeId.Icy_Spear,
        ItemType.Sword: ItemUpgradeId.Icy_Sword,
    }
    Ebon = {
        ItemType.Axe: ItemUpgradeId.Ebon_Axe,
        ItemType.Bow: ItemUpgradeId.Ebon_Bow,
        ItemType.Daggers: ItemUpgradeId.Ebon_Daggers,
        ItemType.Hammer: ItemUpgradeId.Ebon_Hammer,
        ItemType.Scythe: ItemUpgradeId.Ebon_Scythe,
        ItemType.Spear: ItemUpgradeId.Ebon_Spear,
        ItemType.Sword: ItemUpgradeId.Ebon_Sword,
    }
    Shocking = {
        ItemType.Axe: ItemUpgradeId.Shocking_Axe,
        ItemType.Bow: ItemUpgradeId.Shocking_Bow,
        ItemType.Daggers: ItemUpgradeId.Shocking_Daggers,
        ItemType.Hammer: ItemUpgradeId.Shocking_Hammer,
        ItemType.Scythe: ItemUpgradeId.Shocking_Scythe,
        ItemType.Spear: ItemUpgradeId.Shocking_Spear,
        ItemType.Sword: ItemUpgradeId.Shocking_Sword,
    }
    Fiery = {
        ItemType.Axe: ItemUpgradeId.Fiery_Axe,
        ItemType.Bow: ItemUpgradeId.Fiery_Bow,
        ItemType.Daggers: ItemUpgradeId.Fiery_Daggers,
        ItemType.Hammer: ItemUpgradeId.Fiery_Hammer,
        ItemType.Scythe: ItemUpgradeId.Fiery_Scythe,
        ItemType.Spear: ItemUpgradeId.Fiery_Spear,
        ItemType.Sword: ItemUpgradeId.Fiery_Sword,
    }
    Barbed = {
        ItemType.Axe: ItemUpgradeId.Barbed_Axe,
        ItemType.Bow: ItemUpgradeId.Barbed_Bow,
        ItemType.Daggers: ItemUpgradeId.Barbed_Daggers,
        ItemType.Scythe: ItemUpgradeId.Barbed_Scythe,
        ItemType.Spear: ItemUpgradeId.Barbed_Spear,
        ItemType.Sword: ItemUpgradeId.Barbed_Sword,
    }
    Crippling = {
        ItemType.Axe: ItemUpgradeId.Crippling_Axe,
        ItemType.Bow: ItemUpgradeId.Crippling_Bow,
        ItemType.Daggers: ItemUpgradeId.Crippling_Daggers,
        ItemType.Scythe: ItemUpgradeId.Crippling_Scythe,
        ItemType.Spear: ItemUpgradeId.Crippling_Spear,
        ItemType.Sword: ItemUpgradeId.Crippling_Sword,
    }
    Cruel = {
        ItemType.Axe: ItemUpgradeId.Cruel_Axe,
        ItemType.Daggers: ItemUpgradeId.Cruel_Daggers,
        ItemType.Hammer: ItemUpgradeId.Cruel_Hammer,
        ItemType.Scythe: ItemUpgradeId.Cruel_Scythe,
        ItemType.Spear: ItemUpgradeId.Cruel_Spear,
        ItemType.Sword: ItemUpgradeId.Cruel_Sword,
    }
    Poisonous = {
        ItemType.Axe: ItemUpgradeId.Poisonous_Axe,
        ItemType.Bow: ItemUpgradeId.Poisonous_Bow,
        ItemType.Daggers: ItemUpgradeId.Poisonous_Daggers,
        ItemType.Scythe: ItemUpgradeId.Poisonous_Scythe,
        ItemType.Spear: ItemUpgradeId.Poisonous_Spear,
        ItemType.Sword: ItemUpgradeId.Poisonous_Sword,
    }
    Silencing = {
        ItemType.Bow: ItemUpgradeId.Silencing_Bow,
        ItemType.Daggers: ItemUpgradeId.Silencing_Daggers,
        ItemType.Spear: ItemUpgradeId.Silencing_Spear,
    }
    Furious = {
        ItemType.Axe: ItemUpgradeId.Furious_Axe,
        ItemType.Daggers: ItemUpgradeId.Furious_Daggers,
        ItemType.Hammer: ItemUpgradeId.Furious_Hammer,
        ItemType.Scythe: ItemUpgradeId.Furious_Scythe,
        ItemType.Spear: ItemUpgradeId.Furious_Spear,
        ItemType.Sword: ItemUpgradeId.Furious_Sword,
    }
    Heavy = {
        ItemType.Axe: ItemUpgradeId.Heavy_Axe,
        ItemType.Hammer: ItemUpgradeId.Heavy_Hammer,
        ItemType.Scythe: ItemUpgradeId.Heavy_Scythe,
        ItemType.Spear: ItemUpgradeId.Heavy_Spear,
    }
    Zealous = {
        ItemType.Axe: ItemUpgradeId.Zealous_Axe,
        ItemType.Bow: ItemUpgradeId.Zealous_Bow,
        ItemType.Daggers: ItemUpgradeId.Zealous_Daggers,
        ItemType.Hammer: ItemUpgradeId.Zealous_Hammer,
        ItemType.Scythe: ItemUpgradeId.Zealous_Scythe,
        ItemType.Spear: ItemUpgradeId.Zealous_Spear,
        ItemType.Sword: ItemUpgradeId.Zealous_Sword,
    }
    Vampiric = {
        ItemType.Axe: ItemUpgradeId.Vampiric_Axe,
        ItemType.Bow: ItemUpgradeId.Vampiric_Bow,
        ItemType.Daggers: ItemUpgradeId.Vampiric_Daggers,
        ItemType.Hammer: ItemUpgradeId.Vampiric_Hammer,
        ItemType.Scythe: ItemUpgradeId.Vampiric_Scythe,
        ItemType.Spear: ItemUpgradeId.Vampiric_Spear,
        ItemType.Sword: ItemUpgradeId.Vampiric_Sword,
    }
    Swift = {
        ItemType.Staff: ItemUpgradeId.Swift_Staff,
    }
    Sundering = {
        ItemType.Axe: ItemUpgradeId.Sundering_Axe,
        ItemType.Bow: ItemUpgradeId.Sundering_Bow,
        ItemType.Daggers: ItemUpgradeId.Sundering_Daggers,
        ItemType.Hammer: ItemUpgradeId.Sundering_Hammer,
        ItemType.Scythe: ItemUpgradeId.Sundering_Scythe,
        ItemType.Spear: ItemUpgradeId.Sundering_Spear,
        ItemType.Sword: ItemUpgradeId.Sundering_Sword,
    }
    Defensive = {
        ItemType.Staff: ItemUpgradeId.Defensive_Staff,
    }
    Insightful = {
        ItemType.Staff: ItemUpgradeId.Insightful_Staff,
    }
    Hale = {
        ItemType.Staff: ItemUpgradeId.Hale_Staff,
    }
    OfDefense = {
        ItemType.Axe: ItemUpgradeId.OfDefense_Axe,
        ItemType.Bow: ItemUpgradeId.OfDefense_Bow,
        ItemType.Daggers: ItemUpgradeId.OfDefense_Daggers,
        ItemType.Hammer: ItemUpgradeId.OfDefense_Hammer,
        ItemType.Staff: ItemUpgradeId.OfDefense_Staff,
        ItemType.Scythe: ItemUpgradeId.OfDefense_Scythe,
        ItemType.Spear: ItemUpgradeId.OfDefense_Spear,
        ItemType.Sword: ItemUpgradeId.OfDefense_Sword,
    }
    OfWarding = {
        ItemType.Axe: ItemUpgradeId.OfWarding_Axe,
        ItemType.Bow: ItemUpgradeId.OfWarding_Bow,
        ItemType.Daggers: ItemUpgradeId.OfWarding_Daggers,
        ItemType.Hammer: ItemUpgradeId.OfWarding_Hammer,
        ItemType.Staff: ItemUpgradeId.OfWarding_Staff,
        ItemType.Scythe: ItemUpgradeId.OfWarding_Scythe,
        ItemType.Spear: ItemUpgradeId.OfWarding_Spear,
        ItemType.Sword: ItemUpgradeId.OfWarding_Sword,
    }
    OfShelter = {
        ItemType.Axe: ItemUpgradeId.OfShelter_Axe,
        ItemType.Bow: ItemUpgradeId.OfShelter_Bow,
        ItemType.Daggers: ItemUpgradeId.OfShelter_Daggers,
        ItemType.Hammer: ItemUpgradeId.OfShelter_Hammer,
        ItemType.Staff: ItemUpgradeId.OfShelter_Staff,
        ItemType.Scythe: ItemUpgradeId.OfShelter_Scythe,
        ItemType.Spear: ItemUpgradeId.OfShelter_Spear,
        ItemType.Sword: ItemUpgradeId.OfShelter_Sword,
    }
    OfSlaying = {
        ItemType.Axe: ItemUpgradeId.OfSlaying_Axe,
        ItemType.Bow: ItemUpgradeId.OfSlaying_Bow,
        ItemType.Hammer: ItemUpgradeId.OfSlaying_Hammer,
        ItemType.Sword: ItemUpgradeId.OfSlaying_Sword,
        ItemType.Staff: ItemUpgradeId.OfSlaying_Staff,
    }
    OfFortitude = {
        ItemType.Axe: ItemUpgradeId.OfFortitude_Axe,
        ItemType.Bow: ItemUpgradeId.OfFortitude_Bow,
        ItemType.Daggers: ItemUpgradeId.OfFortitude_Daggers,
        ItemType.Hammer: ItemUpgradeId.OfFortitude_Hammer,
        ItemType.Staff: ItemUpgradeId.OfFortitude_Staff,
        ItemType.Scythe: ItemUpgradeId.OfFortitude_Scythe,
        ItemType.Spear: ItemUpgradeId.OfFortitude_Spear,
        ItemType.Sword: ItemUpgradeId.OfFortitude_Sword,
        ItemType.Offhand: ItemUpgradeId.OfFortitude_Focus,
        ItemType.Shield: ItemUpgradeId.OfFortitude_Shield,
    }
    OfEnchanting = {
        ItemType.Axe: ItemUpgradeId.OfEnchanting_Axe,
        ItemType.Bow: ItemUpgradeId.OfEnchanting_Bow,
        ItemType.Daggers: ItemUpgradeId.OfEnchanting_Daggers,
        ItemType.Hammer: ItemUpgradeId.OfEnchanting_Hammer,
        ItemType.Staff: ItemUpgradeId.OfEnchanting_Staff,
        ItemType.Scythe: ItemUpgradeId.OfEnchanting_Scythe,
        ItemType.Spear: ItemUpgradeId.OfEnchanting_Spear,
        ItemType.Sword: ItemUpgradeId.OfEnchanting_Sword,
    }
    OfTheProfession = {
        ItemType.Axe: ItemUpgradeId.OfTheProfession_Axe,
        ItemType.Bow: ItemUpgradeId.OfTheProfession_Bow,
        ItemType.Daggers: ItemUpgradeId.OfTheProfession_Daggers,
        ItemType.Hammer: ItemUpgradeId.OfTheProfession_Hammer,
        ItemType.Staff: ItemUpgradeId.OfTheProfession_Staff,
        ItemType.Scythe: ItemUpgradeId.OfTheProfession_Scythe,
        ItemType.Spear: ItemUpgradeId.OfTheProfession_Spear,
        ItemType.Sword: ItemUpgradeId.OfTheProfession_Sword,
        ItemType.Wand: ItemUpgradeId.OfTheProfession_Wand,
    }
    OfAxeMastery = {
        ItemType.Axe: ItemUpgradeId.OfAxeMastery,
    }
    OfMarksmanship = {
        ItemType.Bow: ItemUpgradeId.OfMarksmanship,
    }
    OfDaggerMastery = {
        ItemType.Daggers: ItemUpgradeId.OfDaggerMastery,
    }
    OfHammerMastery = {
        ItemType.Hammer: ItemUpgradeId.OfHammerMastery,
    }
    OfScytheMastery = {
        ItemType.Scythe: ItemUpgradeId.OfScytheMastery,
    }
    OfSpearMastery = {
        ItemType.Spear: ItemUpgradeId.OfSpearMastery,
    }
    OfSwordsmanship = {
        ItemType.Sword: ItemUpgradeId.OfSwordsmanship,
    }
    OfAttribute = {
        ItemType.Staff: ItemUpgradeId.OfAttribute_Staff,
    }
    OfMastery = {
        ItemType.Staff: ItemUpgradeId.OfMastery_Staff,
    }
    OfMemory = {
        ItemType.Wand: ItemUpgradeId.OfMemory_Wand,
    }
    OfQuickening = {
        ItemType.Wand: ItemUpgradeId.OfQuickening_Wand,
    }
    OfAptitude = {
        ItemType.Offhand: ItemUpgradeId.OfAptitude_Focus,
    }
    OfDevotion = {
        ItemType.Shield: ItemUpgradeId.OfDevotion_Shield,
        ItemType.Offhand: ItemUpgradeId.OfDevotion_Focus,
        ItemType.Staff: ItemUpgradeId.OfDevotion_Staff,
    }
    OfValor = {
        ItemType.Offhand: ItemUpgradeId.OfValor_Focus,
        ItemType.Shield: ItemUpgradeId.OfValor_Shield,
        ItemType.Staff: ItemUpgradeId.OfValor_Staff,
    }
    OfEndurance = {
        ItemType.Offhand: ItemUpgradeId.OfEndurance_Focus,
        ItemType.Shield: ItemUpgradeId.OfEndurance_Shield,
        ItemType.Staff: ItemUpgradeId.OfEndurance_Staff,
    }
    OfSwiftness = {
        ItemType.Offhand: ItemUpgradeId.OfSwiftness_Focus,
    }
    BeJustAndFearNot = ItemUpgradeId.BeJustAndFearNot
    DownButNotOut = ItemUpgradeId.DownButNotOut
    FaithIsMyShield = ItemUpgradeId.FaithIsMyShield
    ForgetMeNot = ItemUpgradeId.ForgetMeNot
    HailToTheKing = ItemUpgradeId.HailToTheKing
    IgnoranceIsBliss = ItemUpgradeId.IgnoranceIsBliss
    KnowingIsHalfTheBattle = ItemUpgradeId.KnowingIsHalfTheBattle
    LifeIsPain = ItemUpgradeId.LifeIsPain
    LiveForToday = ItemUpgradeId.LiveForToday
    ManForAllSeasons = ItemUpgradeId.ManForAllSeasons
    MightMakesRight = ItemUpgradeId.MightMakesRight
    SerenityNow = ItemUpgradeId.SerenityNow
    SurvivalOfTheFittest = ItemUpgradeId.SurvivalOfTheFittest
    BrawnOverBrains = ItemUpgradeId.BrawnOverBrains
    DanceWithDeath = ItemUpgradeId.DanceWithDeath
    DontFearTheReaper = ItemUpgradeId.DontFearTheReaper
    DontThinkTwice = ItemUpgradeId.DontThinkTwice
    GuidedByFate = ItemUpgradeId.GuidedByFate
    StrengthAndHonor = ItemUpgradeId.StrengthAndHonor
    ToThePain = ItemUpgradeId.ToThePain
    TooMuchInformation = ItemUpgradeId.TooMuchInformation
    VengeanceIsMine = ItemUpgradeId.VengeanceIsMine
    IHaveThePower = ItemUpgradeId.IHaveThePower
    LetTheMemoryLiveAgain = ItemUpgradeId.LetTheMemoryLiveAgain
    CastOutTheUnclean = ItemUpgradeId.CastOutTheUnclean
    FearCutsDeeper = ItemUpgradeId.FearCutsDeeper
    ICanSeeClearlyNow = ItemUpgradeId.ICanSeeClearlyNow
    LeafOnTheWind = ItemUpgradeId.LeafOnTheWind
    LikeARollingStone = ItemUpgradeId.LikeARollingStone
    LuckOfTheDraw = ItemUpgradeId.LuckOfTheDraw
    MasterOfMyDomain = ItemUpgradeId.MasterOfMyDomain
    NotTheFace = ItemUpgradeId.NotTheFace
    NothingToFear = ItemUpgradeId.NothingToFear
    OnlyTheStrongSurvive = ItemUpgradeId.OnlyTheStrongSurvive
    PureOfHeart = ItemUpgradeId.PureOfHeart
    RidersOnTheStorm = ItemUpgradeId.RidersOnTheStorm
    RunForYourLife = ItemUpgradeId.RunForYourLife
    ShelteredByFaith = ItemUpgradeId.ShelteredByFaith
    SleepNowInTheFire = ItemUpgradeId.SleepNowInTheFire
    SoundnessOfMind = ItemUpgradeId.SoundnessOfMind
    StrengthOfBody = ItemUpgradeId.StrengthOfBody
    SwiftAsTheWind = ItemUpgradeId.SwiftAsTheWind
    TheRiddleOfSteel = ItemUpgradeId.TheRiddleOfSteel
    ThroughThickAndThin = ItemUpgradeId.ThroughThickAndThin
    MeasureForMeasure = ItemUpgradeId.MeasureForMeasure
    ShowMeTheMoney = ItemUpgradeId.ShowMeTheMoney
    AptitudeNotAttitude = ItemUpgradeId.AptitudeNotAttitude
    DontCallItAComeback = ItemUpgradeId.DontCallItAComeback
    HaleAndHearty = ItemUpgradeId.HaleAndHearty
    HaveFaith = ItemUpgradeId.HaveFaith
    IAmSorrow = ItemUpgradeId.IAmSorrow
    SeizeTheDay = ItemUpgradeId.SeizeTheDay
    SurvivorInsignia = ItemUpgradeId.Survivor
    RadiantInsignia = ItemUpgradeId.Radiant
    StalwartInsignia = ItemUpgradeId.Stalwart
    BrawlersInsignia = ItemUpgradeId.Brawlers
    BlessedInsignia = ItemUpgradeId.Blessed
    HeraldsInsignia = ItemUpgradeId.Heralds
    SentrysInsignia = ItemUpgradeId.Sentrys
    KnightsInsignia = ItemUpgradeId.Knights
    LieutenantsInsignia = ItemUpgradeId.Lieutenants
    StonefistInsignia = ItemUpgradeId.Stonefist
    DreadnoughtInsignia = ItemUpgradeId.Dreadnought
    SentinelsInsignia = ItemUpgradeId.Sentinels
    FrostboundInsignia = ItemUpgradeId.Frostbound
    PyreboundInsignia = ItemUpgradeId.Pyrebound
    StormboundInsignia = ItemUpgradeId.Stormbound
    ScoutsInsignia = ItemUpgradeId.Scouts
    EarthboundInsignia = ItemUpgradeId.Earthbound
    BeastmastersInsignia = ItemUpgradeId.Beastmasters
    WanderersInsignia = ItemUpgradeId.Wanderers
    DisciplesInsignia = ItemUpgradeId.Disciples
    AnchoritesInsignia = ItemUpgradeId.Anchorites
    BloodstainedInsignia = ItemUpgradeId.Bloodstained
    TormentorsInsignia = ItemUpgradeId.Tormentors
    BonelaceInsignia = ItemUpgradeId.Bonelace
    MinionMastersInsignia = ItemUpgradeId.MinionMasters
    BlightersInsignia = ItemUpgradeId.Blighters
    UndertakersInsignia = ItemUpgradeId.Undertakers
    VirtuososInsignia = ItemUpgradeId.Virtuosos
    ArtificersInsignia = ItemUpgradeId.Artificers
    ProdigysInsignia = ItemUpgradeId.Prodigys
    HydromancerInsignia = ItemUpgradeId.Hydromancer
    GeomancerInsignia = ItemUpgradeId.Geomancer
    PyromancerInsignia = ItemUpgradeId.Pyromancer
    AeromancerInsignia = ItemUpgradeId.Aeromancer
    PrismaticInsignia = ItemUpgradeId.Prismatic
    VanguardsInsignia = ItemUpgradeId.Vanguards
    InfiltratorsInsignia = ItemUpgradeId.Infiltrators
    SaboteursInsignia = ItemUpgradeId.Saboteurs
    NightstalkersInsignia = ItemUpgradeId.Nightstalkers
    ShamansInsignia = ItemUpgradeId.Shamans
    GhostForgeInsignia = ItemUpgradeId.GhostForge
    MysticsInsignia = ItemUpgradeId.Mystics
    WindwalkerInsignia = ItemUpgradeId.Windwalker
    ForsakenInsignia = ItemUpgradeId.Forsaken
    CenturionsInsignia = ItemUpgradeId.Centurions
    RuneOfMinorVigor = ItemUpgradeId.OfMinorVigor
    RuneOfMinorVigor2 = ItemUpgradeId.OfMinorVigor2
    RuneOfVitae = ItemUpgradeId.OfVitae
    RuneOfAttunement = ItemUpgradeId.OfAttunement
    RuneOfMajorVigor = ItemUpgradeId.OfMajorVigor
    RuneOfRecovery = ItemUpgradeId.OfRecovery
    RuneOfRestoration = ItemUpgradeId.OfRestoration
    RuneOfClarity = ItemUpgradeId.OfClarity
    RuneOfPurity = ItemUpgradeId.OfPurity
    RuneOfSuperiorVigor = ItemUpgradeId.OfSuperiorVigor
    WarriorRuneOfMinorAbsorption = ItemUpgradeId.OfMinorAbsorption
    WarriorRuneOfMinorTactics = ItemUpgradeId.OfMinorTactics
    WarriorRuneOfMinorStrength = ItemUpgradeId.OfMinorStrength
    WarriorRuneOfMinorAxeMastery = ItemUpgradeId.OfMinorAxeMastery
    WarriorRuneOfMinorHammerMastery = ItemUpgradeId.OfMinorHammerMastery
    WarriorRuneOfMinorSwordsmanship = ItemUpgradeId.OfMinorSwordsmanship
    WarriorRuneOfMajorAbsorption = ItemUpgradeId.OfMajorAbsorption
    WarriorRuneOfMajorTactics = ItemUpgradeId.OfMajorTactics
    WarriorRuneOfMajorStrength = ItemUpgradeId.OfMajorStrength
    WarriorRuneOfMajorAxeMastery = ItemUpgradeId.OfMajorAxeMastery
    WarriorRuneOfMajorHammerMastery = ItemUpgradeId.OfMajorHammerMastery
    WarriorRuneOfMajorSwordsmanship = ItemUpgradeId.OfMajorSwordsmanship
    WarriorRuneOfSuperiorAbsorption = ItemUpgradeId.OfSuperiorAbsorption
    WarriorRuneOfSuperiorTactics = ItemUpgradeId.OfSuperiorTactics
    WarriorRuneOfSuperiorStrength = ItemUpgradeId.OfSuperiorStrength
    WarriorRuneOfSuperiorAxeMastery = ItemUpgradeId.OfSuperiorAxeMastery
    WarriorRuneOfSuperiorHammerMastery = ItemUpgradeId.OfSuperiorHammerMastery
    WarriorRuneOfSuperiorSwordsmanship = ItemUpgradeId.OfSuperiorSwordsmanship
    UpgradeMinorRuneWarrior = ItemUpgradeId.UpgradeMinorRune_Warrior
    UpgradeMajorRuneWarrior = ItemUpgradeId.UpgradeMajorRune_Warrior
    UpgradeSuperiorRuneWarrior = ItemUpgradeId.UpgradeSuperiorRune_Warrior
    AppliesToMinorRuneWarrior = ItemUpgradeId.AppliesToMinorRune_Warrior
    AppliesToMajorRuneWarrior = ItemUpgradeId.AppliesToMajorRune_Warrior
    AppliesToSuperiorRuneWarrior = ItemUpgradeId.AppliesToSuperiorRune_Warrior
    RangerRuneOfMinorWildernessSurvival = ItemUpgradeId.OfMinorWildernessSurvival
    RangerRuneOfMinorExpertise = ItemUpgradeId.OfMinorExpertise
    RangerRuneOfMinorBeastMastery = ItemUpgradeId.OfMinorBeastMastery
    RangerRuneOfMinorMarksmanship = ItemUpgradeId.OfMinorMarksmanship
    RangerRuneOfMajorWildernessSurvival = ItemUpgradeId.OfMajorWildernessSurvival
    RangerRuneOfMajorExpertise = ItemUpgradeId.OfMajorExpertise
    RangerRuneOfMajorBeastMastery = ItemUpgradeId.OfMajorBeastMastery
    RangerRuneOfMajorMarksmanship = ItemUpgradeId.OfMajorMarksmanship
    RangerRuneOfSuperiorWildernessSurvival = ItemUpgradeId.OfSuperiorWildernessSurvival
    RangerRuneOfSuperiorExpertise = ItemUpgradeId.OfSuperiorExpertise
    RangerRuneOfSuperiorBeastMastery = ItemUpgradeId.OfSuperiorBeastMastery
    RangerRuneOfSuperiorMarksmanship = ItemUpgradeId.OfSuperiorMarksmanship
    UpgradeMinorRuneRanger = ItemUpgradeId.UpgradeMinorRune_Ranger
    UpgradeMajorRuneRanger = ItemUpgradeId.UpgradeMajorRune_Ranger
    UpgradeSuperiorRuneRanger = ItemUpgradeId.UpgradeSuperiorRune_Ranger
    AppliesToMinorRuneRanger = ItemUpgradeId.AppliesToMinorRune_Ranger
    AppliesToMajorRuneRanger = ItemUpgradeId.AppliesToMajorRune_Ranger
    AppliesToSuperiorRuneRanger = ItemUpgradeId.AppliesToSuperiorRune_Ranger
    MonkRuneOfMinorHealingPrayers = ItemUpgradeId.OfMinorHealingPrayers
    MonkRuneOfMinorSmitingPrayers = ItemUpgradeId.OfMinorSmitingPrayers
    MonkRuneOfMinorProtectionPrayers = ItemUpgradeId.OfMinorProtectionPrayers
    MonkRuneOfMinorDivineFavor = ItemUpgradeId.OfMinorDivineFavor
    MonkRuneOfMajorHealingPrayers = ItemUpgradeId.OfMajorHealingPrayers
    MonkRuneOfMajorSmitingPrayers = ItemUpgradeId.OfMajorSmitingPrayers
    MonkRuneOfMajorProtectionPrayers = ItemUpgradeId.OfMajorProtectionPrayers
    MonkRuneOfMajorDivineFavor = ItemUpgradeId.OfMajorDivineFavor
    MonkRuneOfSuperiorHealingPrayers = ItemUpgradeId.OfSuperiorHealingPrayers
    MonkRuneOfSuperiorSmitingPrayers = ItemUpgradeId.OfSuperiorSmitingPrayers
    MonkRuneOfSuperiorProtectionPrayers = ItemUpgradeId.OfSuperiorProtectionPrayers
    MonkRuneOfSuperiorDivineFavor = ItemUpgradeId.OfSuperiorDivineFavor
    UpgradeMinorRuneMonk = ItemUpgradeId.UpgradeMinorRune_Monk
    UpgradeMajorRuneMonk = ItemUpgradeId.UpgradeMajorRune_Monk
    UpgradeSuperiorRuneMonk = ItemUpgradeId.UpgradeSuperiorRune_Monk
    AppliesToMinorRuneMonk = ItemUpgradeId.AppliesToMinorRune_Monk
    AppliesToMajorRuneMonk = ItemUpgradeId.AppliesToMajorRune_Monk
    AppliesToSuperiorRuneMonk = ItemUpgradeId.AppliesToSuperiorRune_Monk
    NecromancerRuneOfMinorBloodMagic = ItemUpgradeId.OfMinorBloodMagic
    NecromancerRuneOfMinorDeathMagic = ItemUpgradeId.OfMinorDeathMagic
    NecromancerRuneOfMinorCurses = ItemUpgradeId.OfMinorCurses
    NecromancerRuneOfMinorSoulReaping = ItemUpgradeId.OfMinorSoulReaping
    NecromancerRuneOfMajorBloodMagic = ItemUpgradeId.OfMajorBloodMagic
    NecromancerRuneOfMajorDeathMagic = ItemUpgradeId.OfMajorDeathMagic
    NecromancerRuneOfMajorCurses = ItemUpgradeId.OfMajorCurses
    NecromancerRuneOfMajorSoulReaping = ItemUpgradeId.OfMajorSoulReaping
    NecromancerRuneOfSuperiorBloodMagic = ItemUpgradeId.OfSuperiorBloodMagic
    NecromancerRuneOfSuperiorDeathMagic = ItemUpgradeId.OfSuperiorDeathMagic
    NecromancerRuneOfSuperiorCurses = ItemUpgradeId.OfSuperiorCurses
    NecromancerRuneOfSuperiorSoulReaping = ItemUpgradeId.OfSuperiorSoulReaping
    UpgradeMinorRuneNecromancer = ItemUpgradeId.UpgradeMinorRune_Necromancer
    UpgradeMajorRuneNecromancer = ItemUpgradeId.UpgradeMajorRune_Necromancer
    UpgradeSuperiorRuneNecromancer = ItemUpgradeId.UpgradeSuperiorRune_Necromancer
    AppliesToMinorRuneNecromancer = ItemUpgradeId.AppliesToMinorRune_Necromancer
    AppliesToMajorRuneNecromancer = ItemUpgradeId.AppliesToMajorRune_Necromancer
    AppliesToSuperiorRuneNecromancer = ItemUpgradeId.AppliesToSuperiorRune_Necromancer
    MesmerRuneOfMinorFastCasting = ItemUpgradeId.OfMinorFastCasting
    MesmerRuneOfMinorDominationMagic = ItemUpgradeId.OfMinorDominationMagic
    MesmerRuneOfMinorIllusionMagic = ItemUpgradeId.OfMinorIllusionMagic
    MesmerRuneOfMinorInspirationMagic = ItemUpgradeId.OfMinorInspirationMagic
    MesmerRuneOfMajorFastCasting = ItemUpgradeId.OfMajorFastCasting
    MesmerRuneOfMajorDominationMagic = ItemUpgradeId.OfMajorDominationMagic
    MesmerRuneOfMajorIllusionMagic = ItemUpgradeId.OfMajorIllusionMagic
    MesmerRuneOfMajorInspirationMagic = ItemUpgradeId.OfMajorInspirationMagic
    MesmerRuneOfSuperiorFastCasting = ItemUpgradeId.OfSuperiorFastCasting
    MesmerRuneOfSuperiorDominationMagic = ItemUpgradeId.OfSuperiorDominationMagic
    MesmerRuneOfSuperiorIllusionMagic = ItemUpgradeId.OfSuperiorIllusionMagic
    MesmerRuneOfSuperiorInspirationMagic = ItemUpgradeId.OfSuperiorInspirationMagic
    UpgradeMinorRuneMesmer = ItemUpgradeId.UpgradeMinorRune_Mesmer
    UpgradeMajorRuneMesmer = ItemUpgradeId.UpgradeMajorRune_Mesmer
    UpgradeSuperiorRuneMesmer = ItemUpgradeId.UpgradeSuperiorRune_Mesmer
    AppliesToMinorRuneMesmer = ItemUpgradeId.AppliesToMinorRune_Mesmer
    AppliesToMajorRuneMesmer = ItemUpgradeId.AppliesToMajorRune_Mesmer
    AppliesToSuperiorRuneMesmer = ItemUpgradeId.AppliesToSuperiorRune_Mesmer
    ElementalistRuneOfMinorEnergyStorage = ItemUpgradeId.OfMinorEnergyStorage
    ElementalistRuneOfMinorFireMagic = ItemUpgradeId.OfMinorFireMagic
    ElementalistRuneOfMinorAirMagic = ItemUpgradeId.OfMinorAirMagic
    ElementalistRuneOfMinorEarthMagic = ItemUpgradeId.OfMinorEarthMagic
    ElementalistRuneOfMinorWaterMagic = ItemUpgradeId.OfMinorWaterMagic
    ElementalistRuneOfMajorEnergyStorage = ItemUpgradeId.OfMajorEnergyStorage
    ElementalistRuneOfMajorFireMagic = ItemUpgradeId.OfMajorFireMagic
    ElementalistRuneOfMajorAirMagic = ItemUpgradeId.OfMajorAirMagic
    ElementalistRuneOfMajorEarthMagic = ItemUpgradeId.OfMajorEarthMagic
    ElementalistRuneOfMajorWaterMagic = ItemUpgradeId.OfMajorWaterMagic
    ElementalistRuneOfSuperiorEnergyStorage = ItemUpgradeId.OfSuperiorEnergyStorage
    ElementalistRuneOfSuperiorFireMagic = ItemUpgradeId.OfSuperiorFireMagic
    ElementalistRuneOfSuperiorAirMagic = ItemUpgradeId.OfSuperiorAirMagic
    ElementalistRuneOfSuperiorEarthMagic = ItemUpgradeId.OfSuperiorEarthMagic
    ElementalistRuneOfSuperiorWaterMagic = ItemUpgradeId.OfSuperiorWaterMagic
    UpgradeMinorRuneElementalist = ItemUpgradeId.UpgradeMinorRune_Elementalist
    UpgradeMajorRuneElementalist = ItemUpgradeId.UpgradeMajorRune_Elementalist
    UpgradeSuperiorRuneElementalist = ItemUpgradeId.UpgradeSuperiorRune_Elementalist
    AppliesToMinorRuneElementalist = ItemUpgradeId.AppliesToMinorRune_Elementalist
    AppliesToMajorRuneElementalist = ItemUpgradeId.AppliesToMajorRune_Elementalist
    AppliesToSuperiorRuneElementalist = ItemUpgradeId.AppliesToSuperiorRune_Elementalist
    AssassinRuneOfMinorCriticalStrikes = ItemUpgradeId.OfMinorCriticalStrikes
    AssassinRuneOfMinorDaggerMastery = ItemUpgradeId.OfMinorDaggerMastery
    AssassinRuneOfMinorDeadlyArts = ItemUpgradeId.OfMinorDeadlyArts
    AssassinRuneOfMinorShadowArts = ItemUpgradeId.OfMinorShadowArts
    AssassinRuneOfMajorCriticalStrikes = ItemUpgradeId.OfMajorCriticalStrikes
    AssassinRuneOfMajorDaggerMastery = ItemUpgradeId.OfMajorDaggerMastery
    AssassinRuneOfMajorDeadlyArts = ItemUpgradeId.OfMajorDeadlyArts
    AssassinRuneOfMajorShadowArts = ItemUpgradeId.OfMajorShadowArts
    AssassinRuneOfSuperiorCriticalStrikes = ItemUpgradeId.OfSuperiorCriticalStrikes
    AssassinRuneOfSuperiorDaggerMastery = ItemUpgradeId.OfSuperiorDaggerMastery
    AssassinRuneOfSuperiorDeadlyArts = ItemUpgradeId.OfSuperiorDeadlyArts
    AssassinRuneOfSuperiorShadowArts = ItemUpgradeId.OfSuperiorShadowArts
    UpgradeMinorRuneAssassin = ItemUpgradeId.UpgradeMinorRune_Assassin
    UpgradeMajorRuneAssassin = ItemUpgradeId.UpgradeMajorRune_Assassin
    UpgradeSuperiorRuneAssassin = ItemUpgradeId.UpgradeSuperiorRune_Assassin
    AppliesToMinorRuneAssassin = ItemUpgradeId.AppliesToMinorRune_Assassin
    AppliesToMajorRuneAssassin = ItemUpgradeId.AppliesToMajorRune_Assassin
    AppliesToSuperiorRuneAssassin = ItemUpgradeId.AppliesToSuperiorRune_Assassin
    RitualistRuneOfMinorChannelingMagic = ItemUpgradeId.OfMinorChannelingMagic
    RitualistRuneOfMinorRestorationMagic = ItemUpgradeId.OfMinorRestorationMagic
    RitualistRuneOfMinorCommuning = ItemUpgradeId.OfMinorCommuning
    RitualistRuneOfMinorSpawningPower = ItemUpgradeId.OfMinorSpawningPower
    RitualistRuneOfMajorChannelingMagic = ItemUpgradeId.OfMajorChannelingMagic
    RitualistRuneOfMajorRestorationMagic = ItemUpgradeId.OfMajorRestorationMagic
    RitualistRuneOfMajorCommuning = ItemUpgradeId.OfMajorCommuning
    RitualistRuneOfMajorSpawningPower = ItemUpgradeId.OfMajorSpawningPower
    RitualistRuneOfSuperiorChannelingMagic = ItemUpgradeId.OfSuperiorChannelingMagic
    RitualistRuneOfSuperiorRestorationMagic = ItemUpgradeId.OfSuperiorRestorationMagic
    RitualistRuneOfSuperiorCommuning = ItemUpgradeId.OfSuperiorCommuning
    RitualistRuneOfSuperiorSpawningPower = ItemUpgradeId.OfSuperiorSpawningPower
    UpgradeMinorRuneRitualist = ItemUpgradeId.UpgradeMinorRune_Ritualist
    UpgradeMajorRuneRitualist = ItemUpgradeId.UpgradeMajorRune_Ritualist
    UpgradeSuperiorRuneRitualist = ItemUpgradeId.UpgradeSuperiorRune_Ritualist
    AppliesToMinorRuneRitualist = ItemUpgradeId.AppliesToMinorRune_Ritualist
    AppliesToMajorRuneRitualist = ItemUpgradeId.AppliesToMajorRune_Ritualist
    AppliesToSuperiorRuneRitualist = ItemUpgradeId.AppliesToSuperiorRune_Ritualist
    DervishRuneOfMinorMysticism = ItemUpgradeId.OfMinorMysticism
    DervishRuneOfMinorEarthPrayers = ItemUpgradeId.OfMinorEarthPrayers
    DervishRuneOfMinorScytheMastery = ItemUpgradeId.OfMinorScytheMastery
    DervishRuneOfMinorWindPrayers = ItemUpgradeId.OfMinorWindPrayers
    DervishRuneOfMajorMysticism = ItemUpgradeId.OfMajorMysticism
    DervishRuneOfMajorEarthPrayers = ItemUpgradeId.OfMajorEarthPrayers
    DervishRuneOfMajorScytheMastery = ItemUpgradeId.OfMajorScytheMastery
    DervishRuneOfMajorWindPrayers = ItemUpgradeId.OfMajorWindPrayers
    DervishRuneOfSuperiorMysticism = ItemUpgradeId.OfSuperiorMysticism
    DervishRuneOfSuperiorEarthPrayers = ItemUpgradeId.OfSuperiorEarthPrayers
    DervishRuneOfSuperiorScytheMastery = ItemUpgradeId.OfSuperiorScytheMastery
    DervishRuneOfSuperiorWindPrayers = ItemUpgradeId.OfSuperiorWindPrayers
    UpgradeMinorRuneDervish = ItemUpgradeId.UpgradeMinorRune_Dervish
    UpgradeMajorRuneDervish = ItemUpgradeId.UpgradeMajorRune_Dervish
    UpgradeSuperiorRuneDervish = ItemUpgradeId.UpgradeSuperiorRune_Dervish
    AppliesToMinorRuneDervish = ItemUpgradeId.AppliesToMinorRune_Dervish
    AppliesToMajorRuneDervish = ItemUpgradeId.AppliesToMajorRune_Dervish
    AppliesToSuperiorRuneDervish = ItemUpgradeId.AppliesToSuperiorRune_Dervish
    ParagonRuneOfMinorLeadership = ItemUpgradeId.OfMinorLeadership
    ParagonRuneOfMinorMotivation = ItemUpgradeId.OfMinorMotivation
    ParagonRuneOfMinorCommand = ItemUpgradeId.OfMinorCommand
    ParagonRuneOfMinorSpearMastery = ItemUpgradeId.OfMinorSpearMastery
    ParagonRuneOfMajorLeadership = ItemUpgradeId.OfMajorLeadership
    ParagonRuneOfMajorMotivation = ItemUpgradeId.OfMajorMotivation
    ParagonRuneOfMajorCommand = ItemUpgradeId.OfMajorCommand
    ParagonRuneOfMajorSpearMastery = ItemUpgradeId.OfMajorSpearMastery
    ParagonRuneOfSuperiorLeadership = ItemUpgradeId.OfSuperiorLeadership
    ParagonRuneOfSuperiorMotivation = ItemUpgradeId.OfSuperiorMotivation
    ParagonRuneOfSuperiorCommand = ItemUpgradeId.OfSuperiorCommand
    ParagonRuneOfSuperiorSpearMastery = ItemUpgradeId.OfSuperiorSpearMastery
    UpgradeMinorRuneParagon = ItemUpgradeId.UpgradeMinorRune_Paragon
    UpgradeMajorRuneParagon = ItemUpgradeId.UpgradeMajorRune_Paragon
    UpgradeSuperiorRuneParagon = ItemUpgradeId.UpgradeSuperiorRune_Paragon
    AppliesToMinorRuneParagon = ItemUpgradeId.AppliesToMinorRune_Paragon
    AppliesToMajorRuneParagon = ItemUpgradeId.AppliesToMajorRune_Paragon
    AppliesToSuperiorRuneParagon = ItemUpgradeId.AppliesToSuperiorRune_Paragon

    @property
    def item_type_id_map(self) -> dict[ItemType, "ItemUpgradeId"]:
        return self.value if isinstance(self.value, dict) else {}
    
    @property
    def upgrade_ids(self) -> tuple["ItemUpgradeId", ...]:
        if isinstance(self.value, dict):
            return tuple(self.value.values())
        
        return (self.value,)

    def get_item_type(self, upgrade_id: "ItemUpgradeId") -> ItemType:
        if isinstance(self.value, dict):
            for item_type, item_upgrade_id in self.value.items():
                if item_upgrade_id == upgrade_id:
                    return item_type
        
        return ItemType.Unknown

    def has_id(self, upgrade_id: "ItemUpgradeId") -> bool:
        if isinstance(self.value, dict):
            return upgrade_id in self.value.values()
        
        return upgrade_id == self.value    