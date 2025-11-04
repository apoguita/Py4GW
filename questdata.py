from turtle import title

from PyParty import Hero
from Py4GWCoreLib import ImGui, ColorPalette, TITLE_TIERS, TITLE_NAME, GLOBAL_CACHE, TITLE_CATEGORIES, Utils
from Py4GWCoreLib import Routines, Overlay
import PyImGui
import Py4GW
import PyQuest
from PyPlayer import PyTitle
from typing import Optional, Dict, List, Tuple
import re
import time

MODULE_NAME = "Account Info"
BASE_PATH = Py4GW.Console.get_projects_path()
TEXTURE_BASE_PATH = BASE_PATH + "\\Textures\\Faction_Icons\\"

# ===============================
# COLOR MAPS for quest markup tags
# ===============================
COLOR_MAP: Dict[str, Tuple[float, float, float, float]] = {
    "@warning": ColorPalette.GetColor("red").to_tuple_normalized(),
    "@Warning": ColorPalette.GetColor("red").to_tuple_normalized(),
    "@Quest":   ColorPalette.GetColor("bright_green").to_tuple_normalized(),
    "@quest":   ColorPalette.GetColor("bright_green").to_tuple_normalized(),
    "Header":  ColorPalette.GetColor("creme").to_tuple_normalized(),
    
}

def render_wrapped_bullet(text: str, max_width: float = 400.0):
    """
    Custom bullet renderer that allows wrapped text.
    The bullet is rendered in the left column; text wraps in the right column.
    """
    import PyImGui

    bullet_col_width = PyImGui.get_text_line_height()
    text_col_width = max_width - bullet_col_width

    if PyImGui.begin_table("bullet_table", 2, PyImGui.TableFlags.NoBordersInBody):
        PyImGui.table_setup_column("bullet", PyImGui.TableColumnFlags.WidthFixed, bullet_col_width)
        PyImGui.table_setup_column("text", PyImGui.TableColumnFlags.WidthStretch)

        PyImGui.table_next_row()
        PyImGui.table_set_column_index(0)
        #PyImGui.text("•")  # draw bullet manually (you could use u2022 or custom icon)
        PyImGui.bullet_text("")  # draw bullet using ImGui's bullet
        PyImGui.table_set_column_index(1)

        PyImGui.push_text_wrap_pos(PyImGui.get_cursor_pos_x() + text_col_width)
        PyImGui.text_wrapped(text)
        PyImGui.pop_text_wrap_pos()

        PyImGui.end_table()


def strip_markup_tags(text: str) -> str:
    """Return plain readable text from markup."""
    if not text:
        return ""

    clean = text
    clean = re.sub(r"<p>|</p>", "\n\n", clean, flags=re.IGNORECASE)
    clean = re.sub(r"<brx>|<br>|<brx/>", "\n", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\{s\}|\{sc\}", "• ", clean, flags=re.IGNORECASE)
    clean = re.sub(r"<c=@[^>]+>|</c>", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"<[^>]+>", "", clean)
    clean = re.sub(r"\{[^}]+\}", "", clean)
    clean = re.sub(r"[ \t]+", " ", clean)
    return clean.strip()


# ========================================
# TOKENIZER + RENDERER: Unified Entry Point
# ========================================
def render_markup_text(text: str, max_width: float = 400.0):
    """
    Tokenizes and renders Guild Wars-style quest markup directly to ImGui.
    Performs safe pre-splitting to avoid breaking inside paired tags (<c=@...>...</c>),
    while still handling standalone tags like <brx>, {s}, and {sc}.
    """
    # --- Get style and backup current spacing ---
    # Tighten ONLY for this call
    style = PyImGui.StyleConfig()
    style.Pull()
    _orig_cell = style.CellPadding
    _orig_item = style.ItemSpacing
    style.CellPadding = (_orig_cell[0], 0.0)   # ↓ vertical padding inside table rows
    style.ItemSpacing = (_orig_item[0], 0.0)   # ↓ spacing between stacked rows
    style.Push()

    try:
        # --- Identify atomic (non-breakable) blocks ---
        atomic_blocks = re.findall(r"<c=@[^>]+>.*?</c>", text, flags=re.IGNORECASE)
        tmp_placeholder = text
        block_map = {}
        for i, block in enumerate(atomic_blocks):
            key = f"@@BLOCK{i}@@"
            block_map[key] = block
            tmp_placeholder = tmp_placeholder.replace(block, key)

        # --- Split text safely (words + tags + placeholders) ---
        tag_or_text = re.compile(r"(<[^>]+>|\{[^}]+\}|@@BLOCK\d+@@|[^\{\}<@\n\r]+|\n+|\r+)")
        parts = tag_or_text.findall(tmp_placeholder)
        lines, current_line, visible = [], [], ""
        inside_bullet = False

        def flush_line():
            nonlocal current_line, visible
            if current_line:
                lines.append("".join(current_line).rstrip())
                current_line = []
                visible = ""

        for part in parts:
            low = part.lower()
            
            # --- Handle newlines explicitly ---
            if part == "\n" or part == "\r" or part == "\r\n" or "\n" in part:
                flush_line()
                lines.append("")
                inside_bullet = False
                continue

            # --- Handle explicit breaks ---
            if low in ("<brx>", "<br>", "<brx/>"):
                flush_line()
                inside_bullet = False
                continue
            if low in ("<p>", "</p>"):
                flush_line()
                lines.append("")  # paragraph break
                inside_bullet = False
                continue

            # --- Bullet start ---
            if low in ("{s}", "{sc}"):
                inside_bullet = True
                current_line.append(part)
                continue

            # --- Protected atomic color blocks ---
            if part.startswith("@@BLOCK"):
                block = block_map[part]
                inner_text = re.sub(r"^<c=@[^>]+>|</c>$", "", block, flags=re.IGNORECASE)
                visible_width = PyImGui.calc_text_size(visible + inner_text)[0]
                if visible_width > max_width and visible and not inside_bullet:
                    flush_line()
                current_line.append(block)
                visible += inner_text
                continue

            # --- Tags (non-visible markup) ---
            if part.startswith("<") or part.startswith("{"):
                current_line.append(part)
                continue

            # --- Word-based wrapping (disabled for bullets) ---
            if inside_bullet:
                # append directly without wrapping logic
                current_line.append(part)
                visible += part
                continue

            words = part.split(" ")
            for w in words:
                if not w:
                    #current_line.append(" ")
                    visible += ""
                    continue
                test = (visible + " " + w).strip() if visible else w
                if PyImGui.calc_text_size(test)[0] > max_width and visible:
                    flush_line()
                    current_line.append(w)
                    visible = w
                else:
                    if visible:
                        current_line.append(" ")
                    current_line.append(w)
                    visible = test

        if current_line:
            flush_line()

        # --- Tokenize and render each split line ---
        pattern = re.compile(r"(<[^>]+>|\{[^}]+\})")
        for line in lines:
            tokens, pos = [], 0
            for match in pattern.finditer(line):
                start, end = match.span()
                if start > pos:
                    tokens.append({"type": "text", "value": line[pos:start]})
                tag = match.group(0).strip()

                if tag.lower().startswith("<c=@"):
                    tokens.append({"type": "color_start", "value": tag[3:-1].strip()})
                elif tag.lower() == "</c>":
                    tokens.append({"type": "color_end"})
                elif tag.lower() in ("<brx>", "<br>", "<brx/>"):
                    tokens.append({"type": "line_break"})
                elif tag.lower() in ("<p>", "</p>"):
                    tokens.append({"type": "paragraph"})
                elif tag.lower() == "{sc}":
                    tokens.append({"type": "bullet", "gray": True})
                elif tag.lower() == "{s}":
                    tokens.append({"type": "bullet", "gray": False})
                pos = end
            if pos < len(line):
                tokens.append({"type": "text", "value": line[pos:]})

            color_stack, inside_bullet, gray_bullet = [], False, False
            for token in tokens:
                t = token["type"]
                v = token.get("value")
                v = v.strip() if isinstance(v, str) else v

                if t == "text":
                    if inside_bullet:
                        PyImGui.push_style_color(
                            PyImGui.ImGuiCol.Text,
                            (0.6, 0.6, 0.6, 1.0) if gray_bullet else (1.0, 1.0, 1.0, 1.0),
                        )
                        #PyImGui.bullet_text(v)
                        render_wrapped_bullet(v, max_width=max_width)
                        PyImGui.pop_style_color(1)
                        inside_bullet = False
                        gray_bullet = False
                    elif color_stack:
                        current_color = color_stack[-1]
                        color = COLOR_MAP.get(current_color, (1, 1, 1, 1))
                        PyImGui.text_colored(v, color)
                        PyImGui.same_line(0, 2)
                    else:
                        PyImGui.text(f"{v}")
                        PyImGui.same_line(0, 2)
                elif t == "color_start":
                    color_stack.append(v)
                elif t == "color_end" and color_stack:
                    color_stack.pop()
                elif t == "paragraph":
                    PyImGui.new_line()
                elif t == "line_break":
                    PyImGui.new_line()
                elif t == "bullet":
                    inside_bullet = True
                    gray_bullet = token.get("gray", False)
            PyImGui.new_line()

    finally:
        # --- Restore spacing ---
        style.CellPadding = _orig_cell
        style.ItemSpacing = _orig_item
        style.Push()


quest = None

# requested state tracking:
# name_requested_map          -> did we fetch (Name + Location) for this quest_id yet?
# full_quest_names_requested_map     -> did we queue full string fetch for this *active quest* yet?
name_requested_map: Dict[int, bool] = {}
force_refresh = True
full_quest_requested_list: list[int] = []

def _request_names_coroutine(quest_ids: List[int]):
    global name_requested_map, force_refresh

    start = time.time()
    for quest_id in quest_ids:
        if not name_requested_map.get(quest_id, False) or force_refresh:
            # ask only for cheap/basic fields
            GLOBAL_CACHE.Quest.RequestQuestName(quest_id)
            GLOBAL_CACHE.Quest.RequestQuestLocation(quest_id)

            # wait until both are ready and valid
            while True:
                got_name = GLOBAL_CACHE.Quest.IsQuestNameReady(quest_id)
                got_loc  = GLOBAL_CACHE.Quest.IsQuestLocationReady(quest_id)

                if got_name and got_loc:
                    nm  = GLOBAL_CACHE.Quest.GetQuestName(quest_id)
                    loc = GLOBAL_CACHE.Quest.GetQuestLocation(quest_id)

                    # if game reported Timeout
                    if nm == "Timeout" or loc == "Timeout":
                        print(f"Reporting Timeout for quest ID {quest_id}")
                        name_requested_map[quest_id] = True
                        break  # exit wait loop

                    # we're good
                    # (you can print debug if you want)
                    # print(f"[BASIC OK] {quest_id}: {nm} @ {loc}")
                    name_requested_map[quest_id] = True
                    break

                yield from Routines.Yield.wait(50)
    print (f"Completed BASIC fetch for {len(quest_ids)} quests in {time.time() - start:.2f} seconds.")

def _request_names_coroutine_parallel(quest_ids: List[int]):
    global name_requested_map, force_refresh

    start = time.time()

    # 1 Fire requests for all quests at once
    for quest_id in quest_ids:
        if not name_requested_map.get(quest_id, False) or force_refresh:
            GLOBAL_CACHE.Quest.RequestQuestName(quest_id)
            GLOBAL_CACHE.Quest.RequestQuestLocation(quest_id)

    # 2 Wait for all quests to be ready
    remaining = set(
        q for q in quest_ids
        if not name_requested_map.get(q, False) or force_refresh
    )

    while remaining:
        done = []
        for quest_id in list(remaining):
            got_name = GLOBAL_CACHE.Quest.IsQuestNameReady(quest_id)
            got_loc  = GLOBAL_CACHE.Quest.IsQuestLocationReady(quest_id)

            if got_name and got_loc:
                nm  = GLOBAL_CACHE.Quest.GetQuestName(quest_id)
                loc = GLOBAL_CACHE.Quest.GetQuestLocation(quest_id)

                # handle Timeout
                if nm == "Timeout" or loc == "Timeout":
                    print(f"Reporting Timeout for quest ID {quest_id}")
                #else:
                #    print(f"[BASIC OK] {quest_id}: {nm} @ {loc}")

                name_requested_map[quest_id] = True
                done.append(quest_id)

        for quest_id in done:
            remaining.discard(quest_id)

        if remaining:
            yield from Routines.Yield.wait(50)

    print(f"Completed BASIC fetch for {len(quest_ids)} quests in {time.time() - start:.2f} seconds.")
    force_refresh = False



def _request_quest_data_coroutine(quest_id: int):
    global full_quest_requested_list

    start = time.time()

    #GLOBAL_CACHE.Quest.RequestQuestName(quest_id)
    GLOBAL_CACHE.Quest.RequestQuestObjectives(quest_id)
    #GLOBAL_CACHE.Quest.RequestQuestLocation(quest_id)
    GLOBAL_CACHE.Quest.RequestQuestNPC(quest_id)
    GLOBAL_CACHE.Quest.RequestQuestDescription(quest_id)

    full_quest_requested_list.append(quest_id)
    
    while True:
        name_ready      = True #GLOBAL_CACHE.Quest.IsQuestNameReady(quest_id)
        obj_ready       = GLOBAL_CACHE.Quest.IsQuestObjectivesReady(quest_id)
        loc_ready       = True #GLOBAL_CACHE.Quest.IsQuestLocationReady(quest_id)
        npc_ready       = GLOBAL_CACHE.Quest.IsQuestNPCReady(quest_id)
        desc_ready      = GLOBAL_CACHE.Quest.IsQuestDescriptionReady(quest_id)

        if name_ready and obj_ready and loc_ready and npc_ready and desc_ready:
            print(f"Completed FULL fetch for quest ID {quest_id} {GLOBAL_CACHE.Quest.GetQuestName(quest_id)} in {time.time() - start:.2f} seconds.")
            break
        yield from Routines.Yield.wait(100)

quest_name = ""
def draw_window():
    global quest,force_refresh, quest_name, full_quest_requested_list, active_quest
    MIN_WIDTH = 400
    MIN_HEIGHT = 600
    
    if PyImGui.begin(MODULE_NAME):
        window_size = PyImGui.get_window_size()
        new_width = max(window_size[0], MIN_WIDTH)
        new_height = max(window_size[1], MIN_HEIGHT)

        # only update size if it changed
        if new_width != window_size[0] or new_height != window_size[1]:
            PyImGui.set_window_size(new_width, new_height, PyImGui.ImGuiCond.Always)

        PyImGui.push_style_color(PyImGui.ImGuiCol.Text, COLOR_MAP["Header"])
        ImGui.text("Active Quests:", font_size=18)
        PyImGui.pop_style_color(1)
        PyImGui.same_line(0, -1)
        
        # if this is the first frame OR we just pressed refresh,
        # queue the BASIC (name+location) fetch for the whole log ONCE.
        active_quest = GLOBAL_CACHE.Quest.GetActiveQuest()
        quest = GLOBAL_CACHE.Quest.GetQuestData(active_quest)

        if active_quest not in full_quest_requested_list or force_refresh:
        #if quest_requested != active_quest:
            if force_refresh:
                GLOBAL_CACHE.Coroutines.append(
                    _request_names_coroutine(GLOBAL_CACHE.Quest.GetQuestLogIds())
                )
            
            GLOBAL_CACHE.Coroutines.append(_request_quest_data_coroutine(active_quest))
            force_refresh = False

        # the button returns True only on the frame it's clicked.
        # assign that result back into force_refresh so next frame we know to run again.
        if PyImGui.button("Refresh Quest Info"):
            GLOBAL_CACHE.Quest.RequestQuestInfo(active_quest, update_marker=True)
            force_refresh = True

        
        #quest_log = GLOBAL_CACHE.Quest.GetQuestLogIds()
        #for quest_id in quest_log:
        #    if (quest_id not in quest_data_cache) or force_refresh:
        #        quest_data_cache[quest_id] = GLOBAL_CACHE.Quest.GetQuestData(quest_id)
                
            
        if PyImGui.begin_child("QuestTreeChild", (new_width - 20, 250), True, PyImGui.WindowFlags.NoFlag):
            # Build the grouping structure
            grouped_quests: Dict[str, List[int]] = {}

            for qid in GLOBAL_CACHE.Quest.GetQuestLogIds():
                quest_data = GLOBAL_CACHE.Quest.GetQuestData(qid)
                if not quest_data:
                    continue

                # Primary quests go into their own group
                if quest_data.is_primary:
                    grouped_quests.setdefault("Primary", []).append(qid)
                else:
                    # Group by quest location (fallback to "Unknown Location")
                    location = "Unknown Location"
                    if GLOBAL_CACHE.Quest.IsQuestLocationReady(qid):
                        location = GLOBAL_CACHE.Quest.GetQuestLocation(qid)
                        if location == "Timeout" or not location:
                            location = "Unknown Location"
                    grouped_quests.setdefault(location, []).append(qid)

            # --- Order groups ---
            ordered_groups: list[tuple[str, list[int]]] = []
            if "Primary" in grouped_quests:
                ordered_groups.append(("Primary", grouped_quests.pop("Primary")))

            # Sort other groups alphabetically by location name
            for loc in sorted(grouped_quests.keys(), key=lambda s: s.lower()):
                ordered_groups.append((loc, grouped_quests[loc]))

            # --- Draw the tree ---
            for location, quest_ids in ordered_groups:
                # Sort quest IDs alphabetically by name (fallback to ID if not ready)
                sorted_qids = sorted(
                    quest_ids,
                    key=lambda qid: (
                        GLOBAL_CACHE.Quest.GetQuestName(qid)
                        if GLOBAL_CACHE.Quest.IsQuestNameReady(qid)
                        else str(qid)
                    ).lower()
                )

                ImGui.push_font("Regular", 18)
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, COLOR_MAP["Header"])
                opened = PyImGui.tree_node(f"{location} Quests ({len(sorted_qids)})")
                PyImGui.pop_style_color(1)
                ImGui.pop_font()

                if opened:
                    for qid in sorted_qids:
                        quest_data = GLOBAL_CACHE.Quest.GetQuestData(qid)
                        quest_name = (
                            GLOBAL_CACHE.Quest.GetQuestName(qid)
                            if GLOBAL_CACHE.Quest.IsQuestNameReady(qid)
                            else f"Quest ID {qid}"
                        )

                        # --- draw the quest name ---
                        if qid == active_quest:
                            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, COLOR_MAP["Header"])
                        PyImGui.text(f"{quest_name}")
                        text_size = PyImGui.calc_text_size(quest_name)
                        text_pos = PyImGui.get_item_rect_min()
                        total_width = text_size[0]
                        max_height = text_size[1]

                        # --- draw "(Completed)" next to it if needed ---
                        if quest_data.is_completed:
                            PyImGui.same_line(0, 5)
                            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, COLOR_MAP["Header"])
                            completed_text = "(Completed)"
                            PyImGui.text(completed_text)
                            PyImGui.pop_style_color(1)
                            total_width += 5 + PyImGui.calc_text_size(completed_text)[0]

                        if qid == active_quest:
                            PyImGui.pop_style_color(1)
                        # === highlight active quest ===
                        if qid == active_quest:
                            style = PyImGui.StyleConfig()
                            style.Pull()
                            padding_x = style.CellPadding[0] if style.CellPadding else 0.0
                            style.Push()

                            # get full child dimensions
                            child_pos = PyImGui.get_window_pos()
                            child_size = PyImGui.get_window_size()

                            # margin in pixels around the text (controls vertical overflow)
                            v_margin = 3.0  # expand highlight up/down by 3px each side

                            rect_min = (child_pos[0] + padding_x, text_pos[1] - v_margin)
                            rect_max = (
                                child_pos[0] + child_size[0] - padding_x,
                                text_pos[1] + max_height + v_margin
                            )

                            color = ColorPalette.GetColor("white").copy()
                            color.a = 50
                            PyImGui.draw_list_add_rect_filled(
                                rect_min[0], rect_min[1],
                                rect_max[0], rect_max[1],
                                color.to_color(),
                                3.0, 0  # slight rounding
                            )

                        # overlay invisible button covering both texts
                        PyImGui.set_cursor_screen_pos(*text_pos)
                        if PyImGui.invisible_button(f"quest_btn_{qid}", total_width, max_height):
                            GLOBAL_CACHE.Quest.SetActiveQuest(qid)
                            GLOBAL_CACHE.Quest.RequestQuestInfo(active_quest, update_marker=True)
                            force_refresh = True





                    PyImGui.tree_pop()



            PyImGui.end_child()


            
        # child region adjusts automatically
        if PyImGui.begin_child("AccountInfoChild", (new_width - 20, 0), False, PyImGui.WindowFlags.NoFlag):
            child_width = PyImGui.get_content_region_avail()[0]
            

            if GLOBAL_CACHE.Quest.IsQuestNameReady(active_quest):
                quest_name = GLOBAL_CACHE.Quest.GetQuestName(active_quest)
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, COLOR_MAP["Header"])
                ImGui.text(f"{quest_name}", font_size=20)
                PyImGui.pop_style_color(1)
            else:
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, COLOR_MAP["Header"])
                ImGui.text(f"Quest Name Not Fetched Yet", font_size=20)
                PyImGui.pop_style_color(1)

            PyImGui.push_style_color(PyImGui.ImGuiCol.Text, COLOR_MAP["Header"])
            ImGui.text("Quest Summary:", font_size=18)
            PyImGui.pop_style_color(1)
            
            if GLOBAL_CACHE.Quest.IsQuestObjectivesReady(active_quest):
                quest_objectives = GLOBAL_CACHE.Quest.GetQuestObjectives(active_quest)
                
                render_markup_text(quest_objectives, max_width=child_width)
                
            if GLOBAL_CACHE.Quest.IsQuestNPCReady(active_quest):
                quest_npc = f"{GLOBAL_CACHE.Quest.GetQuestNPC(active_quest)} ({GLOBAL_CACHE.Map.GetMapName(quest.map_from)})"
                PyImGui.push_style_color(PyImGui.ImGuiCol.Text, COLOR_MAP["Header"])
                PyImGui.text_wrapped(f"{quest_npc}")
                PyImGui.pop_style_color(1)
            
            if GLOBAL_CACHE.Quest.IsQuestDescriptionReady(active_quest):
                quest_description = GLOBAL_CACHE.Quest.GetQuestDescription(active_quest)
                render_markup_text(quest_description, max_width=child_width)

            PyImGui.separator()
            PyImGui.text(f"From: {GLOBAL_CACHE.Map.GetMapName(quest.map_from)}")
            PyImGui.text(f"To: {GLOBAL_CACHE.Map.GetMapName(quest.map_to)}")
            PyImGui.text(f"Marker X,Y: ({quest.marker_x}, {quest.marker_y})")
            PyImGui.text(f"h0024: {quest.h0024}")
            
            PyImGui.separator()
            is_current = "Yes" if quest.is_current_mission_quest else "No"
            PyImGui.text_colored(f"Is Current Mission Quest: {is_current}", Utils.TrueFalseColor(quest.is_current_mission_quest))
            is_area_primary = "Yes" if quest.is_area_primary else "No"
            PyImGui.text_colored(f"Is Area Primary: {is_area_primary}", Utils.TrueFalseColor(quest.is_area_primary))

                
            PyImGui.end_child()
        PyImGui.end()


def main():
    draw_window()



if __name__ == "__main__":
    main()
