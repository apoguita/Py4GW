from Py4GWCoreLib import *

# — define these three color‐tuples so display_title_progress can use them —
icon_teal         = Color(33, 51, 58, 255).to_tuple_normalized()  # teal for all icons
heading_gray      = Color(139, 131, 99, 255).to_tuple_normalized()  # bright gray for section headings
text_color        = Color(139, 131, 99, 255).to_tuple_normalized()  # off-white for body text

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

def display_title_progress(title_name, title_id, tiers):
    """
    Renders a title exactly as Guild Wars 1 does—but with a slim, teal‐colored bar
    whose overlay text is horizontally centered.
    """
    title = Player.GetTitle(title_id)
    points = title.current_points

    # 1) Determine current tier
    current_tier = 0
    for i, (tier_points, tier_label) in enumerate(tiers):
        if points >= tier_points:
            current_tier = i + 1
        else:
            break

    tier_label = tiers[current_tier - 1][1] if current_tier > 0 else "Unknown"
    max_points = tiers[-1][0] if tiers else 1

    # 2) Draw the title text (“Not Too Grumpy (6)”) in heading_gray
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, heading_gray)
    PyImGui.text(f"{tier_label} (Tier {current_tier})")
    PyImGui.pop_style_color(1)

    # 3) Calculate fill fraction and overlay text
    fraction = 0.0
    if max_points > 0:
        fraction = float(points) / float(max_points)
        fraction = max(0.0, min(1.0, fraction))
    overlay = f"{points:,} / {max_points:,}"

    # 4) Make the bar very slim by reducing FramePadding to (0, 2)
    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0.0, 2.0)

    # 5) Use icon_teal for the filled portion
    PyImGui.push_style_color(PyImGui.ImGuiCol.PlotHistogram,       icon_teal)
    PyImGui.push_style_color(PyImGui.ImGuiCol.PlotHistogramHovered, icon_teal)

    # 6) Query available width via get_content_region_avail()[0] and draw the bar
    avail_width, _ = PyImGui.get_content_region_avail()
    start_x, start_y = PyImGui.get_cursor_pos()

    PyImGui.progress_bar(fraction, avail_width, " ") # " " to remove all text, "" would result in "xx.x %" on the bar 

    # Center overlay text on the progress bar
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, heading_gray)

    text_width, text_height = PyImGui.calc_text_size(overlay)
    bar_height = PyImGui.get_cursor_pos_y() - start_y
    
    y_offset = -1
    center_x = start_x + (avail_width - text_width) / 2
    center_y = start_y + (bar_height - text_height) / 2 + y_offset

    PyImGui.set_cursor_pos(center_x, center_y)
    PyImGui.text(overlay)

    PyImGui.pop_style_color(1)

    PyImGui.pop_style_color(2)
    PyImGui.pop_style_var(1)
    PyImGui.spacing()

# Example usage
# Display all titles
#display_title_track("Vanguard Title", 40, vanguard_tiers)
#display_title_track("Norn Title", 41, norn_tiers)
#display_title_track("Asura Title", 38, asura_tiers)
#display_title_track("Deldrimor Title", 39, deldrimor_tiers)
#display_title_track("Sunspear Title", 17, sunspear_tiers)
#display_title_track("Lightbringer Title", 20, lightbringer_tiers)


def display_faction(title_name, title_id, get_data_func, tier_list):
    """
    Renders two centered‐overlay, slim teal bars for Kurzick/Luxon:
      1) “Steward of the Luxons (6)”
         ───────────────────────── (bar with “1,745,000 / 1,850,000” centered)
      2) “Luxon”
         ───────────────────────── (bar with “22,620 / 37,000” centered)
    """
    # 1) Retrieve data from the game API
    current_unspent, total_earned, max_unspent = get_data_func()
    title = Player.GetTitle(title_id)
    points = title.current_points  # equals total_earned

    # 2) Determine current campaign tier
    current_tier = 0
    for i, (required_points, tier_label) in enumerate(tier_list):
        if points >= required_points:
            current_tier = i + 1
        else:
            break

    tier_label = tier_list[current_tier - 1][1] if current_tier > 0 else "Unknown"

    # Next reputation threshold for title (or last tier if already at max)
    if current_tier < len(tier_list):
        next_rep_threshold = tier_list[current_tier][0]
    else:
        next_rep_threshold = tier_list[-1][0]

    # --- FACTION TITLE BAR ("Steward of the Luxons (6)") ---
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, heading_gray)
    PyImGui.text(f"{tier_label} (Tier {current_tier})")
    PyImGui.pop_style_color(1)

    rep_fraction = 0.0
    if next_rep_threshold > 0:
        rep_fraction = float(points) / float(next_rep_threshold)
        rep_fraction = max(0.0, min(1.0, rep_fraction))
    rep_overlay = f"{points:,} / {next_rep_threshold:,}"

    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0.0, 2.0)
    PyImGui.push_style_color(PyImGui.ImGuiCol.PlotHistogram,       icon_teal)
    PyImGui.push_style_color(PyImGui.ImGuiCol.PlotHistogramHovered, icon_teal)

    avail_width, _ = PyImGui.get_content_region_avail()
    PyImGui.progress_bar(rep_fraction, avail_width, rep_overlay)

    PyImGui.pop_style_color(2)
    PyImGui.pop_style_var(1)
    PyImGui.spacing()

    # --- UNSPENT FACTION BAR ("Luxon") ---
    PyImGui.push_style_color(PyImGui.ImGuiCol.Text, heading_gray)
    PyImGui.text(f"{title_name}")
    PyImGui.pop_style_color(1)

    unspent_fraction = 0.0
    if max_unspent > 0:
        unspent_fraction = float(current_unspent) / float(max_unspent)
        unspent_fraction = max(0.0, min(1.0, unspent_fraction))
    unspent_overlay = f"{current_unspent:,} / {max_unspent:,}"

    PyImGui.push_style_var2(ImGui.ImGuiStyleVar.FramePadding, 0.0, 2.0)
    PyImGui.push_style_color(PyImGui.ImGuiCol.PlotHistogram,       icon_teal)
    PyImGui.push_style_color(PyImGui.ImGuiCol.PlotHistogramHovered, icon_teal)

    avail_width2, _ = PyImGui.get_content_region_avail()
    PyImGui.progress_bar(unspent_fraction, avail_width2, unspent_overlay)

    PyImGui.pop_style_color(2)
    PyImGui.pop_style_var(1)
    PyImGui.spacing()

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
    "luxon_regions", "kurzick_regions", "nightfall_regions", "eotn_region_titles", "display_title_progress"
]
