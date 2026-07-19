"""Mission catalog — names, campaigns, and regions for the selection UI."""

from __future__ import annotations

from dataclasses import dataclass

CAMPAIGN_PROPHECIES = 0
CAMPAIGN_FACTIONS = 1
CAMPAIGN_NIGHTFALL = 2
CAMPAIGN_OTHER = 3

CAMPAIGN_NAMES = {
    CAMPAIGN_PROPHECIES: 'Prophecies',
    CAMPAIGN_FACTIONS: 'Factions',
    CAMPAIGN_NIGHTFALL: 'Nightfall',
    CAMPAIGN_OTHER: 'Eye of the North',
}


@dataclass(frozen=True)
class CatalogEntry:
    quest_id: int
    name: str
    campaign: int
    region: str
    stub: bool = False


# Full catalog from MissionCatalogData.au3. Only Phase-1 missions are playable.
CATALOG: list[CatalogEntry] = [
    CatalogEntry(936, 'The Great Northern Wall', CAMPAIGN_PROPHECIES, 'Ascalon'),
    CatalogEntry(937, 'Fort Ranik', CAMPAIGN_PROPHECIES, 'Ascalon'),
    CatalogEntry(938, 'Ruins of Surmia', CAMPAIGN_PROPHECIES, 'Ascalon'),
    CatalogEntry(939, 'Nolani Academy', CAMPAIGN_PROPHECIES, 'Ascalon'),
    CatalogEntry(940, 'Borlis Pass', CAMPAIGN_PROPHECIES, 'Northern Shiverpeaks'),
    CatalogEntry(941, 'The Frost Gate', CAMPAIGN_PROPHECIES, 'Northern Shiverpeaks'),
    CatalogEntry(942, 'Gates of Kryta', CAMPAIGN_PROPHECIES, 'Kryta'),
    CatalogEntry(943, "D'Alessio Seaboard", CAMPAIGN_PROPHECIES, 'Kryta'),
    CatalogEntry(944, 'Divinity Coast', CAMPAIGN_PROPHECIES, 'Kryta'),
    CatalogEntry(945, 'The Wilds', CAMPAIGN_PROPHECIES, 'Maguuma Jungle'),
    CatalogEntry(946, 'Bloodstone Fen', CAMPAIGN_PROPHECIES, 'Maguuma Jungle'),
    CatalogEntry(947, 'Aurora Glade', CAMPAIGN_PROPHECIES, 'Maguuma Jungle'),
    CatalogEntry(948, 'Riverside Province', CAMPAIGN_PROPHECIES, 'Kryta'),
    CatalogEntry(949, 'Sanctum Cay', CAMPAIGN_PROPHECIES, 'Kryta'),
    CatalogEntry(950, 'Dunes of Despair', CAMPAIGN_PROPHECIES, 'Crystal Desert'),
    CatalogEntry(951, 'Thirsty River', CAMPAIGN_PROPHECIES, 'Crystal Desert'),
    CatalogEntry(952, 'Elona Reach', CAMPAIGN_PROPHECIES, 'Crystal Desert'),
    CatalogEntry(953, 'Augury Rock', CAMPAIGN_PROPHECIES, 'Crystal Desert'),
    CatalogEntry(954, "The Dragon's Lair", CAMPAIGN_PROPHECIES, 'Crystal Desert'),
    CatalogEntry(955, 'Ice Caves of Sorrow', CAMPAIGN_PROPHECIES, 'Southern Shiverpeaks'),
    CatalogEntry(956, 'Iron Mines of Moladune', CAMPAIGN_PROPHECIES, 'Southern Shiverpeaks'),
    CatalogEntry(957, 'Thunderhead Keep', CAMPAIGN_PROPHECIES, 'Southern Shiverpeaks'),
    CatalogEntry(958, 'Ring of Fire', CAMPAIGN_PROPHECIES, 'Ring of Fire'),
    CatalogEntry(959, "Abaddon's Mouth", CAMPAIGN_PROPHECIES, 'Ring of Fire'),
    CatalogEntry(960, "Hell's Precipice", CAMPAIGN_PROPHECIES, 'Ring of Fire'),
    CatalogEntry(996, "Abaddon's Gate", CAMPAIGN_PROPHECIES, 'Ring of Fire'),
    CatalogEntry(1000, 'Finding the Bloodstone', CAMPAIGN_PROPHECIES, 'Southern Shiverpeaks'),
    CatalogEntry(993, 'Ruins of Morah', CAMPAIGN_PROPHECIES, 'Southern Shiverpeaks'),
    CatalogEntry(1119, "Minister Cho's Estate", CAMPAIGN_FACTIONS, 'Shing Jea'),
    CatalogEntry(961, 'Zen Daijun', CAMPAIGN_FACTIONS, 'Shing Jea'),
    CatalogEntry(962, 'Vizunah Square', CAMPAIGN_FACTIONS, 'Kaineng City'),
    CatalogEntry(963, 'Nahpui Quarter', CAMPAIGN_FACTIONS, 'Kaineng City'),
    CatalogEntry(964, 'Tahnnakai Temple', CAMPAIGN_FACTIONS, 'Kaineng City'),
    CatalogEntry(967, 'Sunjiang District', CAMPAIGN_FACTIONS, 'Kaineng City'),
    CatalogEntry(971, 'Raisu Palace', CAMPAIGN_FACTIONS, 'Kaineng City'),
    CatalogEntry(972, 'Imperial Sanctum', CAMPAIGN_FACTIONS, 'Kaineng City'),
    CatalogEntry(968, 'The Eternal Grove', CAMPAIGN_FACTIONS, 'Echovald Forest', stub=True),
    CatalogEntry(965, 'Arborstone', CAMPAIGN_FACTIONS, 'Echovald Forest'),
    CatalogEntry(966, 'Boreas Seabed', CAMPAIGN_FACTIONS, 'The Jade Sea'),
    CatalogEntry(970, 'Gyala Hatchery', CAMPAIGN_FACTIONS, 'The Jade Sea'),
    CatalogEntry(969, 'Unwaking Waters', CAMPAIGN_FACTIONS, 'The Jade Sea'),
    CatalogEntry(978, 'Chahbek Village', CAMPAIGN_NIGHTFALL, 'Istan'),
    CatalogEntry(979, 'Jokanur Diggins', CAMPAIGN_NIGHTFALL, 'Istan'),
    CatalogEntry(980, 'Blacktide Den', CAMPAIGN_NIGHTFALL, 'Istan'),
    CatalogEntry(981, 'Consulate Docks', CAMPAIGN_NIGHTFALL, 'Vabbi'),
    CatalogEntry(982, 'Venta Cemetery', CAMPAIGN_NIGHTFALL, 'Vabbi'),
    CatalogEntry(983, 'Kodonur Crossroads', CAMPAIGN_NIGHTFALL, 'Kourna'),
    CatalogEntry(1181, 'Pogahn Passage', CAMPAIGN_NIGHTFALL, 'Kourna'),
    CatalogEntry(984, 'Rilohn Refuge', CAMPAIGN_NIGHTFALL, 'Kourna'),
    CatalogEntry(985, 'Moddok Crevice', CAMPAIGN_NIGHTFALL, 'Kourna'),
    CatalogEntry(986, 'Tihark Orchard', CAMPAIGN_NIGHTFALL, 'Kourna'),
    CatalogEntry(988, 'Dasha Vestibule', CAMPAIGN_NIGHTFALL, 'Realm of Torment'),
    CatalogEntry(987, 'Dzagonur Bastion', CAMPAIGN_NIGHTFALL, 'Realm of Torment'),
    CatalogEntry(990, "Jennur's Horde", CAMPAIGN_NIGHTFALL, 'Kourna'),
    CatalogEntry(991, 'Nundu Bay', CAMPAIGN_NIGHTFALL, 'Kourna'),
    CatalogEntry(992, 'Gate of Desolation', CAMPAIGN_NIGHTFALL, 'Realm of Torment'),
    CatalogEntry(994, 'Gate of Pain', CAMPAIGN_NIGHTFALL, 'Realm of Torment'),
    CatalogEntry(995, 'Gate of Madness', CAMPAIGN_NIGHTFALL, 'Realm of Torment'),
    CatalogEntry(989, 'Grand Court of Sebelkeh', CAMPAIGN_NIGHTFALL, 'Vabbi'),
    CatalogEntry(1005, 'Assault on the Stronghold', CAMPAIGN_OTHER, 'Eye of the North', stub=True),
    CatalogEntry(1003, 'Against the Charr', CAMPAIGN_OTHER, 'Eye of the North'),
    CatalogEntry(1007, 'Blood Washes Blood', CAMPAIGN_OTHER, 'Eye of the North'),
    CatalogEntry(1008, 'A Gate Too Far', CAMPAIGN_OTHER, 'Eye of the North'),
    CatalogEntry(1010, 'A Time for Heroes', CAMPAIGN_OTHER, 'Eye of the North'),
    CatalogEntry(1006, 'Curse of the Nornbear', CAMPAIGN_OTHER, 'Eye of the North'),
    CatalogEntry(1002, 'G.O.L.E.M.', CAMPAIGN_OTHER, 'Eye of the North'),
    CatalogEntry(1001, 'The Elusive Golemancer', CAMPAIGN_OTHER, 'Eye of the North'),
    CatalogEntry(1004, 'Warband of Brothers', CAMPAIGN_OTHER, 'Eye of the North'),
]

CATALOG_BY_ID: dict[int, CatalogEntry] = {e.quest_id: e for e in CATALOG}


def get_name(quest_id: int) -> str:
    entry = CATALOG_BY_ID.get(quest_id)
    return entry.name if entry else f'Quest {quest_id}'


def filter_by_campaign(campaign: int | None) -> list[CatalogEntry]:
    if campaign is None:
        return list(CATALOG)
    return [e for e in CATALOG if e.campaign == campaign]
