
import PyImGui

from Py4GWCoreLib.native_src.context.WorldContext import TitleStruct
from Py4GWCoreLib import Player,ColorPalette, GLOBAL_CACHE, TITLE_TIERS, TITLE_NAME, TITLE_CATEGORIES
from typing import Optional
from Py4GWCoreLib.native_src.context.WorldContext import TitleStruct
#region TitleData 
class TitleData:
    def __init__(self):
        self.titles: dict[int, TitleStruct] = {}
        self.active_title_id: Optional[int] = None

    def update(self):
        title_array = Player.GetTitleArray()
        for title_id in title_array:
            title = Player.GetTitle(title_id)
            if title:
                self.titles[title_id] = title
        self.active_title_id = Player.GetActiveTitleID()

    def get_current_tier(self, title_id: int, current_points: int):
        tiers = TITLE_TIERS.get(title_id, [])
        if not tiers:
            return None, None  # unmanaged

        current_tier = None
        for t in tiers:
            if current_points >= t.required:
                current_tier = t
            else:
                break

        if not current_tier:
            return None, None

        # find next tier (if any)
        idx = tiers.index(current_tier)
        next_tier = tiers[idx + 1] if idx + 1 < len(tiers) else None

        return current_tier, next_tier
    
    def _get_total_completion_ratio(self, title: TitleStruct) -> float:
        tiers = TITLE_TIERS.get(title.title_id, [])
        if not tiers:
            return 0.0

        max_required = tiers[-1].required
        ratio = title.current_points / max_required if max_required > 0 else 0.0
        return ratio



    def _draw_title(self, title: TitleStruct, managed: bool):
        title_name = TITLE_NAME.get(title.title_id, f"Unknown ({title.title_id})")

        if not managed:
            PyImGui.text(f"{title_name}")
            PyImGui.text(f"Title ID: {title.title_id}")
            PyImGui.text(f"Current Points: {title.current_points}")
            PyImGui.text(f"Has Tiers: {title.has_tiers}")
            PyImGui.text(f"Is Percentage Based: {title.is_percentage_based}")
            PyImGui.text(f"Current Title Tier Index: {title.current_title_tier_index}")
            PyImGui.text(f"Points Needed Current Rank: {title.points_needed_current_rank}")
            PyImGui.text(f"Points Needed Next Rank: {title.points_needed_next_rank}")
            
            PyImGui.separator()
            return

        # Get tier info
        current_tier, next_tier = self.get_current_tier(title.title_id, title.current_points)
        tiers = TITLE_TIERS.get(title.title_id, [])
        avail_width = PyImGui.get_content_region_avail()[0]

        # -------- Determine start/end range --------
        if not current_tier:
            # Unranked → progress to first tier
            start_req = 0
            end_req = tiers[0].required if tiers else 1  # avoid 0 division
            PyImGui.text(f"{title_name} (0)")
        elif next_tier:
            # Mid progression
            start_req = current_tier.required
            end_req = next_tier.required
            PyImGui.text(f"{current_tier.name} ({current_tier.tier})")
        else:
            # Max tier
            start_req = current_tier.required
            end_req = start_req
            PyImGui.text(f"{current_tier.name} ({current_tier.tier}) [MAX]")

        # -------- Compute progress --------
        progress = (title.current_points - start_req) / (end_req - start_req) if end_req > start_req else 1.0  
        progress = max(0.0, min(progress, 1.0))

        # -------- Label text --------
        if not current_tier:
            label_text = f"{title.current_points:,} / {end_req:,}"
        elif next_tier:
            label_text = f"{title.current_points:,} / {end_req:,}"
        else:
            label_text = f"{title.current_points:,} / MAX"

        PyImGui.push_style_color(PyImGui.ImGuiCol.PlotHistogram, ColorPalette.GetColor("midnight_violet").to_tuple_normalized())
        PyImGui.progress_bar(progress, avail_width, label_text)
        PyImGui.pop_style_color(1)
        PyImGui.separator()

    def draw_content(self):
        # prepare categorized + uncategorized collections
        categorized_titles = {cat: [] for cat in TITLE_CATEGORIES}
        unmanaged_titles = []

        if self.active_title_id:
            PyImGui.text(f"Active Title: {TITLE_NAME.get(self.active_title_id, f'Unknown ({self.active_title_id})')}")
            PyImGui.separator()

        # distribute titles by category or unmanaged
        for title in self.titles.values():
            found_category = None
            for cat, ids in TITLE_CATEGORIES.items():
                if title.title_id in ids:
                    categorized_titles[cat].append(title)
                    found_category = cat
                    break
            if not found_category:
                unmanaged_titles.append(title)

        # draw each category group
        for category, titles in categorized_titles.items():
            if not titles:
                continue
            titles.sort(key=lambda t: self._get_total_completion_ratio(t), reverse=True)

            if PyImGui.collapsing_header(category, PyImGui.TreeNodeFlags.NoFlag):
                for title in titles:
                    self._draw_title(title, managed=True)
