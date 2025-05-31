from Py4GWCoreLib import *

def display_title_track(title_name, title_id, tiers):
    title = Player.GetTitle(title_id)
    points = title.current_points

    # Find current tier
    current_tier = 0
    for i, (tier_points, tier_label) in enumerate(tiers):
        if points >= tier_points:
            current_tier = i + 1
        else:
            break

    max_points = tiers[-1][0]
    tier_name = tiers[current_tier - 1][1] if current_tier > 0 else "Unknown"

    PyImGui.text(f"{title_name}:")
    PyImGui.text(f"  {tier_name} (Tier {current_tier})")
    PyImGui.text(f"  Points: {points:,} / {max_points:,}")


# Title tier lists (reputation thresholds and names)
vanguard_tiers = [
    (1000, "Agent"), (4000, "Covert Agent"), (8000, "Stealth Agent"), (16000, "Mysterious Agent"),
    (26000, "Shadow Agent"), (40000, "Underground Agent"), (56000, "Special Agent"),
    (80000, "Valued Agent"), (110000, "Superior Agent"), (160000, "Secret Agent")
]

norn_tiers = [
    (1000, "Slayer of Imps"), (4000, "Slayer of Beasts"), (8000, "Slayer of Nightmares"),
    (16000, "Slayer of Giants"), (26000, "Slayer of Wurms"), (40000, "Slayer of Demons"),
    (56000, "Slayer of Heroes"), (80000, "Slayer of Champions"), (110000, "Slayer of Hordes"),
    (160000, "Slayer of All")
]

asura_tiers = [
    (1000, "Not Too Smelly"), (4000, "Not Too Dopey"), (8000, "Not Too Clumsy"),
    (16000, "Not Too Boring"), (26000, "Not Too Annoying"), (40000, "Not Too Grumpy"),
    (56000, "Not Too Silly"), (80000, "Not Too Lazy"), (110000, "Not Too Foolish"),
    (160000, "Not Too Shabby")
]

deldrimor_tiers = [
    (1000, "Delver"), (4000, "Stout Delver"), (8000, "Gutsy Delver"), (16000, "Risky Delver"),
    (26000, "Bold Delver"), (40000, "Daring Delver"), (56000, "Adventurous Delver"),
    (80000, "Courageous Delver"), (110000, "Epic Delver"), (160000, "Legendary Delver")
]

sunspear_tiers = [
    (50, "Sunspear Sergeant"), (100, "Sunspear Master Sergeant"),
    (175, "Second Spear"), (300, "First Spear"), (500, "Sunspear Captain"),
    (1000, "Sunspear Commander"), (2500, "Sunspear General"),
    (7500, "Sunspear Castellan"), (15000, "Spearmarshal"),
    (50000, "Legendary Spearmarshal")
]

lightbringer_tiers = [
    (100, "Lightbringer"), (300, "Adept Lightbringer"), (1000, "Brave Lightbringer"),
    (2500, "Mighty Lightbringer"), (7500, "Conquering Lightbringer"),
    (15000, "Vanquishing Lightbringer"), (25000, "Revered Lightbringer"),
    (50000, "Holy Lightbringer")
]

# Example usage
# Display all titles
#display_title_track("Vanguard Title", 40, vanguard_tiers)
#display_title_track("Norn Title", 41, norn_tiers)
#display_title_track("Asura Title", 38, asura_tiers)
#display_title_track("Deldrimor Title", 39, deldrimor_tiers)
#display_title_track("Sunspear Title", 17, sunspear_tiers)
#display_title_track("Lightbringer Title", 20, lightbringer_tiers)


def display_faction(title_name, title_id, get_data_func, tier_list):
    current, total_earned, max_faction = get_data_func()
    title = Player.GetTitle(title_id)
    points = title.current_points

    # Determine tier
    current_tier = 0
    for i, (required_points, name) in enumerate(tier_list):
        if points >= required_points:
            current_tier = i + 1
        else:
            break

    tier_title = tier_list[current_tier - 1][1] if current_tier > 0 else "Unknown"
    max_points = tier_list[-1][0]

    PyImGui.text(f"{title_name} Allegiance:")
    PyImGui.text(f"  {tier_title} ({current_tier})")
    PyImGui.text(f"  Points: {points:,} / {max_points:,}")
    PyImGui.text(f"  Unspent: {current:,} / {max_faction:,}")

# Tier data for both factions
kurzick_tiers = [
    (100_000, "Kurzick Supporter"),
    (250_000, "Friend of the Kurzicks"),
    (400_000, "Companion of the Kurzicks"),
    (550_000, "Ally of the Kurzicks"),
    (875_000, "Sentinel of the Kurzicks"),
    (1_200_000, "Steward of the Kurzicks"),
    (1_850_000, "Defender of the Kurzicks"),
    (2_500_000, "Warden of the Kurzicks"),
    (3_750_000, "Bastion of the Kurzicks"),
    (5_000_000, "Champion of the Kurzicks"),
    (7_500_000, "Hero of the Kurzicks"),
    (10_000_000, "Savior of the Kurzicks")
]

luxon_tiers = [
    (100_000, "Luxon Supporter"),
    (250_000, "Friend of the Luxons"),
    (400_000, "Companion of the Luxons"),
    (550_000, "Ally of the Luxons"),
    (875_000, "Sentinel of the Luxons"),
    (1_200_000, "Steward of the Luxons"),
    (1_850_000, "Defender of the Luxons"),
    (2_500_000, "Warden of the Luxons"),
    (3_750_000, "Bastion of the Luxons"),
    (5_000_000, "Champion of the Luxons"),
    (7_500_000, "Hero of the Luxons"),
    (10_000_000, "Savior of the Luxons")
]

#EXAMPLE Kurzick (TitleID 5), Luxon (TitleID 6)
#display_faction("Kurzick", 5, Player.GetKurzickData, kurzick_tiers)
#display_faction("Luxon", 6, Player.GetLuxonData, luxon_tiers)

# Factions-related regions
luxon_regions = {"Factions_TheJadeSea"}
kurzick_regions = {"Factions_EchovaldForest"}
# Nightfall regions
nightfall_regions = {
    "NF_Istan",
    "NF_Kourna",
    "NF_Vabbi"
}

# Eye of the North regions
eotn_region_titles = {
    "EOTN_Tarnished_Coast": [(38, "Asura Title", asura_tiers)],
    "EOTN_FarShiverpeaks": [(41, "Norn Title", norn_tiers)],
    "EOTN_CharrHomelands": [(40, "Vanguard Title", vanguard_tiers)]
}

__all__ = [
    "display_title_track", "display_faction",
    "vanguard_tiers", "norn_tiers", "asura_tiers", "deldrimor_tiers",
    "sunspear_tiers", "lightbringer_tiers", "kurzick_tiers", "luxon_tiers",
    "luxon_regions", "kurzick_regions", "nightfall_regions", "eotn_region_titles"
]