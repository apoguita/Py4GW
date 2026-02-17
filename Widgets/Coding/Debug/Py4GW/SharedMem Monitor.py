from datetime import datetime, timedelta
from Py4GW import PingHandler
import PyImGui

from Py4GWCoreLib import *
from Py4GWCoreLib.GlobalCache.SharedMemory import AccountStruct
from Py4GWCoreLib.GlobalCache.shared_memory_src.TitlesStruct import TitleUnitStruct
from Py4GWCoreLib.GlobalCache.shared_memory_src.FactionStruct import FactionStruct
from typing import Callable
from multiprocessing import shared_memory
from ctypes import sizeof

MODULE_NAME = "Py4GW Shared Memory Manager Monitor"
  
SMM = GLOBAL_CACHE.ShMem    
BASE_PATH = Py4GW.Console.get_projects_path()
FACTIONS_TEXTURE_BASE_PATH = BASE_PATH + "\\Textures\\Faction_Icons\\"
GAME_UI_TEXTURE_BASE_PATH = BASE_PATH + "\\Textures\\Game UI\\"

active_players :list[AccountStruct] = []

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Shared Memory Monitor", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("A high-level synchronization and debugging utility for the")
    PyImGui.text("Py4GW Shared Memory Manager (SMM). It provides a cross-process")
    PyImGui.text("view of account data, character states, and faction progress.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Multi-Instance Tracking: Monitor all active players across different game instances")
    PyImGui.bullet_text("Account Analytics: Real-time display of Faction points, Luxon/Kurzick standing, and Title progress")
    PyImGui.bullet_text("Character Discovery: View available characters and account-wide metadata stored in shared memory")
    PyImGui.bullet_text("Live Vitals: Instant tracking of Agent health, energy, experience, and level data")
    PyImGui.bullet_text("Data Visualization: Includes specialized tabs for Factions, Player attributes, and Experience metrics")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")
    PyImGui.bullet_text("Contributors: frenkey")

    PyImGui.end_tooltip()

def begin_striped_table(label: str, columns: int = 2, width: float = 0.0):
    PyImGui.push_style_color(PyImGui.ImGuiCol.TableRowBg, Color(128, 128, 128, 128).to_tuple_normalized())  # light gray
    PyImGui.push_style_color(PyImGui.ImGuiCol.TableRowBgAlt, Color(64, 64, 64, 128).to_tuple_normalized()) # slightly darker

    flags = (
        PyImGui.TableFlags.Borders |
        PyImGui.TableFlags.RowBg |
        PyImGui.TableFlags.SizingStretchProp
    )

    return PyImGui.begin_table(label, columns, flags, width, 0)
    

def end_striped_table():
    PyImGui.end_table()
    PyImGui.pop_style_color(2)



#region AccountInfo
def draw_account_info(player: AccountStruct):

    current_tick = Py4GW.Game.get_tick_count64()
    age_ms = max(0, current_tick - player.LastUpdated) # Time since update in ms
    timestamp = datetime.now() - timedelta(milliseconds=age_ms)
    milliseconds = int(timestamp.microsecond / 1000)

    num_heroes = SMM.GetNumHeroesFromPlayers(player.AgentData.AgentID)
    num_pets = SMM.GetNumPetsFromPlayers(player.AgentData.AgentID)
    player_buffs = [buff.SkillId for buff in player.AgentData.Buffs.Buffs if buff.SkillId != 0]
    num_buffs = len(player_buffs)

    if begin_striped_table("AccountInfoTable", 2):

        def row(label, value):
            PyImGui.table_next_row()
            PyImGui.table_set_column_index(0); PyImGui.text(label)
            PyImGui.table_set_column_index(1); value()

        # --- Basic info rows ---
        row("Account Email",     lambda: PyImGui.text(player.AccountEmail))
        row("Account Name",      lambda: PyImGui.text(player.AccountName))
        row("Character Name",    lambda: PyImGui.text(player.AgentData.CharacterName))
        row("Slot Number",       lambda: PyImGui.text(str(player.SlotNumber)))
        row("Last Updated",      lambda: PyImGui.text(f"{timestamp.strftime('%H:%M:%S')}.{milliseconds:03d}"))

        # -----------------------------------
        # HEROES
        # -----------------------------------
        PyImGui.table_next_row()
        PyImGui.table_set_column_index(0); PyImGui.text("Heroes")
        PyImGui.table_set_column_index(1)
        if PyImGui.tree_node(f"Heroes ({num_heroes})"):
            heroes = SMM.GetHeroesFromPlayers(player.AgentData.AgentID)
            for hero in heroes:
                PyImGui.text(f"{hero.AgentData.CharacterName} (HeroID: {hero.AgentData.HeroID})")
            PyImGui.tree_pop()

        # -----------------------------------
        # PETS
        # -----------------------------------
        PyImGui.table_next_row()
        PyImGui.table_set_column_index(0); PyImGui.text("Pets")
        PyImGui.table_set_column_index(1)
        if PyImGui.tree_node(f"Pets ({num_pets})"):
            pets = SMM.GetPetsFromPlayers(player.AgentData.AgentID)
            for pet in pets:
                PyImGui.text(f"{pet.AgentData.CharacterName} (PlayerID: {pet.AgentData.AgentID})")
            PyImGui.tree_pop()

        # -----------------------------------
        # BUFFS
        # -----------------------------------
        PyImGui.table_next_row()
        PyImGui.table_set_column_index(0); PyImGui.text("Buffs")
        PyImGui.table_set_column_index(1)
        if PyImGui.tree_node(f"Buffs ({num_buffs})"):
            for buff_id in player_buffs:
                buff_name = GLOBAL_CACHE.Skill.GetName(buff_id)
                PyImGui.text(f"Buff ID: {buff_id} - Name: {buff_name}")
            PyImGui.tree_pop()

        end_striped_table()
        
        PyImGui.spacing()
        PyImGui.spacing()
        
    # --------------------------------------------------------
    # Collapsing Header + TABLE 2: Legacy Data
    # --------------------------------------------------------
    if PyImGui.collapsing_header("Account LegacyData (used on legacy scripts)"):

        if begin_striped_table("LegacyDataTable", 2):

            def lrow(label, value):
                PyImGui.table_next_row()
                PyImGui.table_set_column_index(0); PyImGui.text(label)
                PyImGui.table_set_column_index(1); PyImGui.text(str(value))

            lrow("PlayerID",       player.AgentData.AgentID)
            lrow("OwnerPlayerID",  player.AgentData.OwnerAgentID)
            lrow("MapID",          player.AgentData.Map.MapID)
            lrow("Map Region",     player.AgentData.Map.Region)
            lrow("Map District",   player.AgentData.Map.District)
            lrow("Map Language",   player.AgentData.Map.Language)
            lrow("Is Slot Active", player.IsSlotActive)
            lrow("Is Account",     player.IsAccount)
            lrow("IsHero",         player.IsHero)
            lrow("IsPet",          player.IsPet)
            lrow("IsNPC",          player.IsNPC)
            lrow("HeroID",         player.AgentData.HeroID)
            lrow("PartyID",         player.AgentPartyData.PartyID)

            lrow(
                "Player HP",
                f"{int(player.AgentData.Health.Current * player.AgentData.Health.Max)} / "
                f"{player.AgentData.Health.Max}  Regen: {player.AgentData.Health.Regen:.2f}"
            )

            lrow(
                "Player Energy",
                f"{int(player.AgentData.Energy.Current * player.AgentData.Energy.Max)} / "
                f"{player.AgentData.Energy.Max}  Regen: {player.AgentData.Energy.Regen:.2f}"
            )

            lrow(
                "Player XYZ",
                f"({player.AgentData.Pos.x:.2f}, {player.AgentData.Pos.y:.2f}, {player.AgentData.Pos.z:.2f})"
            )

            lrow("Facing Angle", f"{Utils.RadToDeg(player.AgentData.RotationAngle):.2f}")
            lrow("Target ID",    player.AgentData.TargetID)
            lrow("Login Number", player.AgentData.LoginNumber)
            lrow("Is Ticked",    player.AgentPartyData.IsTicked)

            end_striped_table()

#region HeroAI Info
def draw_heroai_info(player: AccountStruct):
    hero_ai_options = GLOBAL_CACHE.ShMem.GetHeroAIOptions(player.AccountEmail)
    if hero_ai_options is None:
        PyImGui.text("No HeroAI options found for this account.")
        return

    if begin_striped_table("HeroAIOptionsTable", 2):

        def row(label, value):
            PyImGui.table_next_row()
            PyImGui.table_set_column_index(0); PyImGui.text(label)
            PyImGui.table_set_column_index(1); value()

        row("Following", lambda: PyImGui.text(str(hero_ai_options.Following)))
        row("Avoidance", lambda: PyImGui.text(str(hero_ai_options.Avoidance)))
        row("Looting",   lambda: PyImGui.text(str(hero_ai_options.Looting)))
        row("Targeting", lambda: PyImGui.text(str(hero_ai_options.Targeting)))
        row("Combat",    lambda: PyImGui.text(str(hero_ai_options.Combat)))

        # Skills
        PyImGui.table_next_row()
        PyImGui.table_set_column_index(0); PyImGui.text("Skills")
        PyImGui.table_set_column_index(1)
        for idx, enabled in enumerate(hero_ai_options.Skills):
            PyImGui.text(f"Skill Slot {idx + 1}: {'Enabled' if enabled else 'Disabled'}")

        end_striped_table()

#endregion HeroAI Info

#region Rank Info          
def draw_rank_info(player: AccountStruct):
    if PyImGui.collapsing_header("Rank Data", PyImGui.TreeNodeFlags.NoFlag):
        PyImGui.text(f"Rank: {player.RankData.Rank}")
        PyImGui.text(f"Rating: {player.RankData.Rating}")
        PyImGui.text(f"Qualifier Points: {player.RankData.QualifierPoints}")
        PyImGui.text(f"Wins: {player.RankData.Wins}")
        PyImGui.text(f"Losses: {player.RankData.Losses}")
        PyImGui.text(f"Tournament Reward Points: {player.RankData.TournamentRewardPoints}")

#region Faction Data
class FactionNode:
    TEXTURE_PATHS = {
        "Balthazar": FACTIONS_TEXTURE_BASE_PATH + "Faction_(Balthazar).jpg",
        "Kurzick":   FACTIONS_TEXTURE_BASE_PATH + "Faction_(Kurzick).jpg",
        "Luxon":     FACTIONS_TEXTURE_BASE_PATH + "Faction_(Luxon).jpg",
        "Imperial":  FACTIONS_TEXTURE_BASE_PATH + "Faction_(Imperial).jpg",
    }

    def __init__(self, name: str, current: int, total_earned: int, max: int):
        self.name = name
        self.current = current
        self.total_earned = total_earned
        self.max = max
        self.texture_path = self.TEXTURE_PATHS[name]
        
    def draw_content(self):
        """Draw the faction entry (icon + stats + bar)."""
        square_side = 45
        texture_size = (square_side, square_side)
        progress = 0.0 if self.max <= 0 else self.current / self.max

        if PyImGui.begin_table(f"FactionOuter_{self.name}", 2, PyImGui.TableFlags.SizingStretchProp):
            PyImGui.table_setup_column("TextureCol", PyImGui.TableColumnFlags.WidthFixed, texture_size[0] + 5)
            PyImGui.table_setup_column("ContentCol", PyImGui.TableColumnFlags.WidthStretch, 1)
            PyImGui.table_next_row()

            # --- Column 1: Texture ---
            PyImGui.table_next_column()
            ImGui.DrawTexture(self.texture_path, *texture_size)

            # --- Column 2: Text + Bar ---
            PyImGui.table_next_column()
            if PyImGui.begin_table(f"FactionInner_{self.name}", 1, PyImGui.TableFlags.SizingStretchProp):
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text(f"{self.name} (Current: {self.current}, Total: {self.total_earned}, Max: {self.max})")

                PyImGui.table_next_row()
                PyImGui.table_next_column()
                avail_width = PyImGui.get_content_region_avail()[0]
                PyImGui.push_style_color(
                    PyImGui.ImGuiCol.PlotHistogram,
                    ColorPalette.GetColor("midnight_violet").to_tuple_normalized(),
                )
                PyImGui.progress_bar(progress, avail_width, f"{self.current:,}/{self.max:,}")
                PyImGui.pop_style_color(1)
                PyImGui.end_table()

            PyImGui.end_table()
            
class FactionData:
    """Container for all faction nodes."""
    def __init__(self, player: AccountStruct):
        factions_data: FactionStruct = player.FactionData
        kurzick_data = factions_data.Kurzick
        luxon_data = factions_data.Luxon
        imperial_data = factions_data.Imperial
        balthazar_data = factions_data.Balthazar
        self.nodes = [
            FactionNode("Balthazar", balthazar_data.Current, balthazar_data.TotalEarned, balthazar_data.Max),
            FactionNode("Kurzick",   kurzick_data.Current, kurzick_data.TotalEarned, kurzick_data.Max),
            FactionNode("Luxon",     luxon_data.Current, luxon_data.TotalEarned, luxon_data.Max),
            FactionNode("Imperial",  imperial_data.Current, imperial_data.TotalEarned, imperial_data.Max),
        ]

    def draw_content(self):
        PyImGui.text("Faction Data:")
        for node in self.nodes:
            node.draw_content()
            
#region Title Data
class TitleData:
    def __init__(self, player: AccountStruct):
        title_array : list[Any] = player.TitlesData.Titles
        self.titles: dict[int, TitleUnitStruct] = {}
        for title in title_array:
             self.titles[title.TitleID] = title
        
        self.active_title_id: int = player.TitlesData.ActiveTitleID

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
        tiers = TITLE_TIERS.get(title.TitleID, [])
        if not tiers:
            return 0.0

        max_required = tiers[-1].required
        ratio = title.CurrentPoints / max_required if max_required > 0 else 0.0
        return ratio



    def _draw_title(self, title: TitleStruct, managed: bool):
        title_name = TITLE_NAME.get(title.TitleID, f"Unknown ({title.TitleID})")
        py_title = Player.GetTitle(title.TitleID)
        if py_title is None:
            PyImGui.text(f"{title_name} - (Title data not found in Player)")
            PyImGui.separator()
            return

        if not managed:
            PyImGui.text(f"{title_name}")
            PyImGui.text(f"Title ID: {title.TitleID}")
            PyImGui.text(f"Current Points: {title.CurrentPoints}")
            PyImGui.text(f"Has Tiers: {py_title.has_tiers}")
            PyImGui.text(f"Is Percentage Based: {py_title.is_percentage_based}")
            PyImGui.text(f"Current Title Tier Index: {py_title.current_title_tier_index}")
            PyImGui.text(f"Points Needed Current Rank: {py_title.points_needed_current_rank}")
            PyImGui.text(f"Points Needed Next Rank: {py_title.points_needed_next_rank}")
            
            PyImGui.separator()
            return

        # Get tier info
        current_tier, next_tier = self.get_current_tier(title.TitleID, title.CurrentPoints)
        tiers = TITLE_TIERS.get(title.TitleID, [])
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
        progress = (title.CurrentPoints - start_req) / (end_req - start_req) if end_req > start_req else 1.0  
        progress = max(0.0, min(progress, 1.0))

        # -------- Label text --------
        if not current_tier:
            label_text = f"{title.CurrentPoints:,} / {end_req:,}"
        elif next_tier:
            label_text = f"{title.CurrentPoints:,} / {end_req:,}"
        else:
            label_text = f"{title.CurrentPoints:,} / MAX"
            
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
                if title.TitleID in ids:
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
                    
def draw_available_characters(player: AccountStruct):
    PyImGui.text("Available Characters:")

    if PyImGui.begin_table("##char_table", 6, PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg):
        # Headers
        table_flags = PyImGui.TableFlags.NoFlag
        PyImGui.table_setup_column("Lvl",table_flags,  init_width_or_weight=60.0)
        PyImGui.table_setup_column("Name",table_flags,  init_width_or_weight=300.0)
        PyImGui.table_setup_column("Map",table_flags,  init_width_or_weight=300.0)
        PyImGui.table_setup_column("Profs",table_flags,  init_width_or_weight=115.0)
        PyImGui.table_setup_column("Campaign",table_flags,  init_width_or_weight=230.0)
        PyImGui.table_setup_column("Type",table_flags,  init_width_or_weight=60.0)
        

        PyImGui.table_headers_row()

        # Rows
        for char in player.AvailableCharacters.Characters:
            if char.Name == "":
                continue  # skip empty slots
            PyImGui.table_next_row()

            # Level
            PyImGui.table_set_column_index(0)
            PyImGui.text(str(char.Level if char.Level <= 20 else 20))
            # Name
            PyImGui.table_set_column_index(1)
            PyImGui.text(char.Name)

            # Map
            PyImGui.table_set_column_index(2)
            PyImGui.text(Map.GetMapName(char.MapID))

            # Professions
            PyImGui.table_set_column_index(3)
            primary = ProfessionShort(char.Professions[0]).name
            secondary = ProfessionShort(char.Professions[1]).name
            PyImGui.text(f"{primary}/{secondary}")

            # Campaign
            PyImGui.table_set_column_index(4)
            PyImGui.text(Campaign(char.CampaignID).name)

            # Type
            PyImGui.table_set_column_index(5)
            PyImGui.text("PvP" if char.IsPvP else "PvE")

        PyImGui.end_table()

#region Player Data
class PlayerData:
    BITS_PER_ENTRY = 32
    show_details_global: dict[str, bool] = {}
    skill_name_cache: dict[int, str] = {}

    def __init__(self, player: AccountStruct):
        self.target_id: int = player.AgentData.TargetID
        self.observing_id: int = player.AgentData.ObservingID
        self.player_uuid: Tuple[int, int, int, int] = player.AgentData.UUID

        # RAW ARRAYS
        self.missions_completed: List[int] = player.MissionData.NormalModeCompleted
        self.missions_bonus: List[int] = player.MissionData.NormalModeBonus
        self.missions_completed_hm: List[int] = player.MissionData.HardModeCompleted
        self.missions_bonus_hm: List[int] = player.MissionData.HardModeBonus
        self.unlocked_character_skills: List[int] = player.UnlockedSkills.Skills

        # UI toggles (checkbox states)
        self.show_details = PlayerData.show_details_global

        # ========================
        # INTERNAL CACHES ADDED
        # ========================
        self._cache_expanded = {
            "missions_completed":      {"raw": None, "expanded": []},
            "missions_bonus":          {"raw": None, "expanded": []},
            "missions_completed_hm":   {"raw": None, "expanded": []},
            "missions_bonus_hm":       {"raw": None, "expanded": []},
            "unlocked_skills":         {"raw": None, "expanded": []},
        }

        # Caches map names forever
        self._map_name_cache: dict[int, str] = {}
        self._skill_name_cache: dict[int, str] = PlayerData.skill_name_cache

    # =====================================================================
    # CACHING HELPERS (NO SIGNATURE CHANGES)
    # =====================================================================

    def _expand_bit_array(self, raw_list: List[int], cache_entry: dict) -> list:
        """
        Turn the bitfield into [(id, bool)] using EXACT same (id, flag) pairs.
        Recomputes only when raw changes.
        """
        if raw_list is cache_entry["raw"]:
            return cache_entry["expanded"]

        if raw_list == cache_entry["raw"]:
            return cache_entry["expanded"]

        # New array → rebuild
        cache_entry["raw"] = list(raw_list)
        out = []
        bits = self.BITS_PER_ENTRY

        for i, mask in enumerate(raw_list):
            base = i * bits
            for bit in range(bits):
                entry_id = base + bit
                flag = bool((mask >> bit) & 1)
                out.append((entry_id, flag))

        cache_entry["expanded"] = out
        return out

    def _get_map_name(self, map_id: int) -> str:
        """Store map names permanently."""
        if map_id not in self._map_name_cache:
            map_name = Map.GetMapName(map_id)
            if not map_name:
                map_name = "Unknown"
            self._map_name_cache[map_id] = map_name
        return self._map_name_cache[map_id]

    def _get_skill_name(self, skill_id: int) -> str:
        if skill_id not in self._skill_name_cache:
            self._skill_name_cache[skill_id] = GLOBAL_CACHE.Skill.GetName(skill_id)
        return self._skill_name_cache[skill_id]

    # =====================================================================
    # DRAW — EXACT SAME STRUCTURE YOU PROVIDED
    # =====================================================================

    def draw_content(self):
        PyImGui.text(f"Target ID: {self.target_id}")
        PyImGui.text(f"Observing ID: {self.observing_id}")
        PyImGui.text("Player UUID:")
        PyImGui.same_line(0, -1)
        for i, part in enumerate(self.player_uuid):
            PyImGui.text(f"{part}")
            if i < 3:
                PyImGui.same_line(0, -1)

        # ------------------------------------------------------------
        # MISSIONS COMPLETED
        # ------------------------------------------------------------
        if PyImGui.collapsing_header("Missions Completed", PyImGui.TreeNodeFlags.NoFlag):

            # EXACT checkbox usage, NO CHANGE
            self.show_details["missions_not_completed"] = PyImGui.checkbox(
                "Show Not Completed Missions",
                self.show_details.get("missions_not_completed", False)
            )

            expanded = self._expand_bit_array(
                self.missions_completed,
                self._cache_expanded["missions_completed"]
            )

            PyImGui.text(f"entries:{len(self.missions_completed)} -{len(self.missions_completed)*32} total missions tracked.")
            show = self.show_details["missions_not_completed"]

            for map_id, completed in expanded:
                if self._get_map_name(map_id) == "undefined":
                    continue  # skip unknown maps
                if show or completed:
                    status = "Completed" if completed else "Not Completed"
                    PyImGui.text_colored(
                        f"MapID {map_id} - {self._get_map_name(map_id)} - {status}",
                        Utils.TrueFalseColor(completed)
                    )

            if PyImGui.button("copy to clipboard"):
                done = [mid for mid, flag in expanded if flag]
                PyImGui.set_clipboard_text(", ".join(map(str, done)))

        # ------------------------------------------------------------
        # MISSIONS BONUS COMPLETED
        # ------------------------------------------------------------
        if PyImGui.collapsing_header("Missions Bonus Completed", PyImGui.TreeNodeFlags.NoFlag):

            self.show_details["missions_bonus_not_completed"] = PyImGui.checkbox(
                "Show Not Completed Bonus",
                self.show_details.get("missions_bonus_not_completed", False)
            )

            expanded = self._expand_bit_array(
                self.missions_bonus,
                self._cache_expanded["missions_bonus"]
            )

            PyImGui.text(f"entries:{len(self.missions_bonus)} -{len(self.missions_bonus)*32} total missions tracked.")
            show = self.show_details["missions_bonus_not_completed"]

            for map_id, completed in expanded:
                if self._get_map_name(map_id) == "undefined":
                    continue  # skip unknown maps
                if show or completed:
                    status = "Completed" if completed else "Not Completed"
                    PyImGui.text_colored(
                        f"MapID {map_id} - {self._get_map_name(map_id)} - {status}",
                        Utils.TrueFalseColor(completed)
                    )

            if PyImGui.button("copy to clipboard##missions_bonus"):
                done = [mid for mid, flag in expanded if flag]
                PyImGui.set_clipboard_text(", ".join(map(str, done)))

        # ------------------------------------------------------------
        # HM COMPLETED
        # ------------------------------------------------------------
        if PyImGui.collapsing_header("Missions Completed HM", PyImGui.TreeNodeFlags.NoFlag):

            self.show_details["missions_hm_not_completed"] = PyImGui.checkbox(
                "Show Not Completed Missions (HM)",
                self.show_details.get("missions_hm_not_completed", False)
            )

            expanded = self._expand_bit_array(
                self.missions_completed_hm,
                self._cache_expanded["missions_completed_hm"]
            )

            PyImGui.text(f"entries:{len(self.missions_completed_hm)} -{len(self.missions_completed_hm)*32} total missions tracked.")
            show = self.show_details["missions_hm_not_completed"]

            for map_id, completed in expanded:
                if self._get_map_name(map_id) == "undefined":
                    continue  # skip unknown maps
                if show or completed:
                    status = "Completed" if completed else "Not Completed"
                    PyImGui.text_colored(
                        f"MapID {map_id} - {self._get_map_name(map_id)} - {status}",
                        Utils.TrueFalseColor(completed)
                    )

            if PyImGui.button("copy to clipboard##missions_completed_hm"):
                done = [mid for mid, flag in expanded if flag]
                PyImGui.set_clipboard_text(", ".join(map(str, done)))

        # ------------------------------------------------------------
        # HM BONUS COMPLETED
        # ------------------------------------------------------------
        if PyImGui.collapsing_header("Missions Bonus Completed HM", PyImGui.TreeNodeFlags.NoFlag):

            self.show_details["missions_bonus_hm_not_completed"] = PyImGui.checkbox(
                "Show Not Completed Bonus (HM)",
                self.show_details.get("missions_bonus_hm_not_completed", False)
            )

            expanded = self._expand_bit_array(
                self.missions_bonus_hm,
                self._cache_expanded["missions_bonus_hm"]
            )

            PyImGui.text(f"entries:{len(self.missions_bonus_hm)} -{len(self.missions_bonus_hm)*32} total missions tracked.")
            show = self.show_details["missions_bonus_hm_not_completed"]

            for map_id, completed in expanded:
                if self._get_map_name(map_id) == "undefined":
                    continue  # skip unknown maps
                if show or completed:
                    status = "Completed" if completed else "Not Completed"
                    PyImGui.text_colored(
                        f"MapID {map_id} - {self._get_map_name(map_id)} - {status}",
                        Utils.TrueFalseColor(completed)
                    )

            if PyImGui.button("copy to clipboard##missions_bonus_hm"):
                done = [mid for mid, flag in expanded if flag]
                PyImGui.set_clipboard_text(", ".join(map(str, done)))

        # ------------------------------------------------------------
        # UNLOCKED SKILLS
        # ------------------------------------------------------------
        if PyImGui.collapsing_header("Unlocked Character Skills", PyImGui.TreeNodeFlags.NoFlag):

            self.show_details["show_locked_skills"] = PyImGui.checkbox(
                "Show Locked Skills",
                self.show_details.get("show_locked_skills", False)
            )

            expanded = self._expand_bit_array(
                self.unlocked_character_skills,
                self._cache_expanded["unlocked_skills"]
            )

            PyImGui.text(f"entries:{len(self.unlocked_character_skills)} -{len(self.unlocked_character_skills)*32} total skills tracked.")
            show = self.show_details["show_locked_skills"]

            for skill_id, unlocked in expanded:
                if show or unlocked:
                    PyImGui.text_colored(
                        f"Skill ID {skill_id} - {self._get_skill_name(skill_id)}",
                        Utils.TrueFalseColor(unlocked)
                    )

            if PyImGui.button("copy to clipboard##unlocked_skills"):
                done = [sid for sid, flag in expanded if flag]
                PyImGui.set_clipboard_text(", ".join(map(str, done)))
                
#region Experience Data
class ExperienceData:
    def __init__(self, player: AccountStruct):
        self.level = player.ExperienceData.Level
        self.experience = player.ExperienceData.Experience
        self.progress_pct = player.ExperienceData.ProgressPct
        self.current_skill_points = player.ExperienceData.CurrentSkillPoints
        self.total_earned_skill_points = player.ExperienceData.TotalEarnedSkillPoints


    def draw_content(self):
        # Outer table: 1 column, 2 rows
        if PyImGui.begin_table("ExperienceOuter", 1, PyImGui.TableFlags.SizingStretchProp):

            # Row 1 → nested 3-column table
            PyImGui.table_next_row()
            PyImGui.table_next_column()

            if PyImGui.begin_table(
                "ExperienceHeader", 3,
                PyImGui.TableFlags.SizingStretchProp
            ):
                # Column setup: left/right auto, middle stretch
                PyImGui.table_setup_column("LevelCol",  PyImGui.TableColumnFlags.WidthFixed, 0)
                PyImGui.table_setup_column("SpacerCol", PyImGui.TableColumnFlags.WidthStretch, 1)
                PyImGui.table_setup_column("SkillCol",  PyImGui.TableColumnFlags.WidthFixed, 0)

                PyImGui.table_next_row()

                # Col 1: Level (sticks left)
                PyImGui.table_next_column()
                PyImGui.text(f"Level: {self.level}")

                # Col 2: Spacer (auto stretches, left empty)
                PyImGui.table_next_column()

                # Col 3: Skill points (sticks right)
                PyImGui.table_next_column()
                PyImGui.text(f"Skill Points: {self.current_skill_points}/{self.total_earned_skill_points}")

                PyImGui.end_table()
            

            # Row 2 → progress bar
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            avail_width = PyImGui.get_content_region_avail()[0]
            PyImGui.push_style_color(PyImGui.ImGuiCol.PlotHistogram, ColorPalette.GetColor("dark_green").to_tuple_normalized())
            PyImGui.progress_bar(self.progress_pct / 100.0, avail_width, f"{self.experience:,} xp")
            PyImGui.pop_style_color(1)
            
            PyImGui.end_table()     
            
#region Health Data
class HealthData:
    def __init__(self, player: AccountStruct):
        self.Health = player.AgentData.Health.Current    # 0.0 - 1.0
        self.MaxHealth = player.AgentData.Health.Max
        self.HealthPips = player.AgentData.Health.Pips
        self.player = player

    def draw_content(self):

        if PyImGui.begin_table("ExperienceOuter", 1, PyImGui.TableFlags.SizingStretchProp):
            PyImGui.table_next_row()
            PyImGui.table_next_column()

            # --- Compute current HP ---
            current_hp = int(self.Health * self.MaxHealth)

            # --- Build pips string ---
            if self.HealthPips > 0:
                pips_str = ">" * self.HealthPips
            elif self.HealthPips < 0:
                pips_str = "<" * abs(self.HealthPips)
            else:
                pips_str = ""

            # --- Caption ---
            caption = f"{current_hp} {pips_str}"

            # --- Draw progress bar using normalized health ---
            def _get_health_color():
                #default 
                color = ColorPalette.GetColor("firebrick").to_tuple_normalized()
                if self.player.AgentData.Is_DegenHexed:
                    color = ColorPalette.GetColor("dark_magenta").to_tuple_normalized()
            
                if self.player.AgentData.Is_Poisoned:
                      color = ColorPalette.GetColor("olive").to_tuple_normalized()
                      
                if self.player.AgentData.Is_Bleeding:
                      color = ColorPalette.GetColor("light_coral").to_tuple_normalized()
                    
                return color
            

            bar_start_pos = PyImGui.get_cursor_pos() 
            avail_width = PyImGui.get_content_region_avail()[0] 
            PyImGui.push_style_color( PyImGui.ImGuiCol.PlotHistogram, _get_health_color() ) 
            PyImGui.progress_bar(self.Health, avail_width, caption) 
            PyImGui.pop_style_color(1)
            bar_height = 20
            cur_x, cur_y = bar_start_pos
            icon_y = cur_y + (bar_height - 16) * 0.5

            # start drawing 4px inside the bar
            x = cur_x + 4

            # -----------------------------------------
            #  ICON: HEXED  (down arrow)
            # -----------------------------------------
            if self.player.AgentData.Is_Hexed:
                PyImGui.set_cursor_pos(x, icon_y)
                ImGui.DrawTextureExtended(
                    texture_path=GAME_UI_TEXTURE_BASE_PATH + "ui_skill_identifier.png",
                    size=(16, 16),
                    uv0=(0.125, 0.5),
                    uv1=(0.25, 0.75),
                    tint=(255,255,255,255),
                    border_color=(255,255,255,0)
                )
                x += 18   # spacing to next icon

            # -----------------------------------------
            #  ICON: CONDITIONED  (faded down arrow)
            # -----------------------------------------
            if self.player.AgentData.Is_Conditioned:
                PyImGui.set_cursor_pos(x, icon_y)
                ImGui.DrawTextureExtended(
                    texture_path=GAME_UI_TEXTURE_BASE_PATH + "ui_skill_identifier.png",
                    size=(16, 16),
                    uv0=(0.125, 0.5),
                    uv1=(0.25, 0.75),
                    tint=(255,255,255,125),
                    border_color=(255,255,255,0)
                )
                x += 18

            # -----------------------------------------
            #  ICON: ENCHANTED  (up arrow)
            # -----------------------------------------
            if self.player.AgentData.Is_Enchanted:
                PyImGui.set_cursor_pos(x, icon_y)
                ImGui.DrawTextureExtended(
                    texture_path=GAME_UI_TEXTURE_BASE_PATH + "ui_skill_identifier.png",
                    size=(16, 16),
                    uv0=(0.625, 0.0),
                    uv1=(0.75, 0.25),
                    tint=(255,255,255,255),
                    border_color=(255,255,255,0)
                )
                x += 18

            # -----------------------------------------
            #  ICON: WEAPON SPELLED  (weapon spell icon)
            # -----------------------------------------
            if self.player.AgentData.Is_WeaponSpelled:
                PyImGui.set_cursor_pos(x, icon_y - 2)
                ImGui.DrawTextureExtended(
                    texture_path=GAME_UI_TEXTURE_BASE_PATH + "ui_skill_identifier.png",
                    size=(20, 20),
                    uv0=(0.35, 0.5),
                    uv1=(0.5, 0.8),
                    tint=(255,255,255,255),
                    border_color=(255,255,255,0)
                )
                x += 22



            PyImGui.end_table()
 

#region Agent Data
class AgentData:
    def __init__(self, player: AccountStruct):
        agent_data = player.AgentData
        self.UUID: list[int] = list(agent_data.UUID)
        self.AgentID: int = agent_data.AgentID
        self.OwnerID: int = agent_data.OwnerAgentID
        self.TargetID: int = agent_data.TargetID
        self.ObservingID: int = agent_data.ObservingID
        self.PlayerNumber: int = agent_data.PlayerNumber
        self.Profession: list[int] = list(agent_data.Profession)
        self.Level: int = agent_data.Level
        self.Energy: float = agent_data.Energy.Current
        self.MaxEnergy: float = agent_data.Energy.Max
        self.EnergyPips: int = agent_data.Energy.Pips
        self.Health: float = agent_data.Health.Current
        self.MaxHealth: float = agent_data.Health.Max
        self.HealthPips: int = agent_data.Health.Pips
        self.LoginNumber: int = agent_data.LoginNumber
        self.DaggerStatus: int = agent_data.DaggerStatus
        self.WeaponType: int = agent_data.WeaponType
        self.WeaponItemType: int = agent_data.WeaponItemType
        self.OffhandItemType: int = agent_data.OffhandItemType
        self.Overcast: float = agent_data.Overcast
        self.WeaponAttackSpeed: float = agent_data.WeaponAttackSpeed
        self.AttackSpeedModifier: float = agent_data.AttackSpeedModifier
        self.VisualEffectsMask: int = agent_data.VisualEffectsMask
        self.ModelState: int = agent_data.ModelState
        self.AnimationSpeed: float = agent_data.AnimationSpeed
        self.AnimationCode: int = agent_data.AnimationCode
        self.AnimationID: int = agent_data.AnimationID
        self.XYZ: list[float] = agent_data.Pos.to_list()
        self.ZPlane: int = agent_data.ZPlane
        self.RotationAngle: float = agent_data.RotationAngle
        self.VelocityVector: list[float] = agent_data.Velocity.to_list()

#region main
def main():
    global active_players
    if not Routines.Checks.Map.MapValid():
        return
    
    active_players = GLOBAL_CACHE.ShMem.GetAllActivePlayers()
    
    if PyImGui.begin(f"{MODULE_NAME}"):
        if PyImGui.collapsing_header("Shared Memory Info"):
            PyImGui.text(f"Py4GW SMM - {SMM.shm_name}")       
            PyImGui.text(f"SMM Size: {Utils.format_bytes(SMM.size)}")
            PyImGui.text(f"Max Number of Players: {SMM.max_num_players}")
            PyImGui.text(f"Number of Active Players: {SMM.GetNumActivePlayers()}")
            PyImGui.text(f"Number of active Slots: {SMM.GetNumActiveSlots()}")
            ImGui.show_tooltip("\n".join([f"{i}. | Slot:{acc.SlotNumber} {acc.AccountEmail} | {acc.AgentData.CharacterName}" for i, acc in enumerate(SMM.GetAllAccounts().AccountData) if SMM.GetAllAccounts()._is_slot_active(i)]))                        
        
        MIN_WIDTH = 500
        MIN_HEIGHT = 700

        # Enforce minimum window size on this same window
        window_size = PyImGui.get_window_size()
        new_width = max(window_size[0], MIN_WIDTH)
        new_height = max(window_size[1], MIN_HEIGHT)

        # only update size if it changed
        if new_width != window_size[0] or new_height != window_size[1]:
            PyImGui.set_window_size(new_width, new_height, PyImGui.ImGuiCond.Always)

        # child region adjusts automatically
        if PyImGui.begin_child(
            "AccountsInfoChild",
            (new_width - 20, 0),
            True,
            PyImGui.WindowFlags.NoFlag
        ):
            for player in active_players:
                if PyImGui.begin_tab_bar("##Accounts"):
                    if PyImGui.begin_tab_item(f"{player.AgentData.CharacterName}"):
                        if PyImGui.begin_tab_bar("##AccountDetails"):
                            #Account Info Tab
                            if PyImGui.begin_tab_item("Account Info"):
                                draw_account_info(player)  # Draw Account Info
                                PyImGui.end_tab_item()                            
                            #Hero AI Tab
                            if PyImGui.begin_tab_item("Hero AI"):
                                if PyImGui.begin_child("HeroAIChild", (0, 0), False, PyImGui.WindowFlags.NoFlag):
                                    draw_heroai_info(player)
                                    PyImGui.end_child()
                                PyImGui.end_tab_item()                            
                            #Rank/Faction Info Tab
                            if PyImGui.begin_tab_item("Faction"):
                                if PyImGui.begin_child("FactionsChild", (0, 0), False, PyImGui.WindowFlags.NoFlag):
                                    draw_rank_info(player)
                                    FactionData(player).draw_content()
                                    PyImGui.end_child()
                                PyImGui.end_tab_item()
                            #Title Info Tab
                            if PyImGui.begin_tab_item("Titles"):
                                if PyImGui.begin_child("TitlesChild", (0, 0), False, PyImGui.WindowFlags.NoFlag):
                                    TitleData(player).draw_content()
                                    PyImGui.end_child()
                                PyImGui.end_tab_item()
                            #Available Characters Tab
                            if PyImGui.begin_tab_item("Available Characters"):
                                if PyImGui.begin_child("AvailableCharsChild", (0, 0), False, PyImGui.WindowFlags.NoFlag):
                                    draw_available_characters(player)
                                    PyImGui.end_child()
                                PyImGui.end_tab_item()
                            #Player Data Tab
                            if PyImGui.begin_tab_item("Player"):
                                if PyImGui.begin_child("PlayerDataChild", (0, 0), False, PyImGui.WindowFlags.NoFlag):
                                    PlayerData(player).draw_content()
                                    PyImGui.end_child()
                                PyImGui.end_tab_item()
                            #Experience Data Tab
                            if PyImGui.begin_tab_item("Agent"):
                                if PyImGui.begin_child("ExperienceDataChild", (0, 0), False, PyImGui.WindowFlags.NoFlag):
                                    ExperienceData(player).draw_content()
                                    HealthData(player).draw_content()
                                    PyImGui.end_child()
                                PyImGui.end_tab_item()
                            PyImGui.end_tab_bar()
                        PyImGui.end_tab_item()
                    PyImGui.end_tab_bar()
            PyImGui.end_child()

    PyImGui.end()



    
if __name__ == "__main__":
    main()
