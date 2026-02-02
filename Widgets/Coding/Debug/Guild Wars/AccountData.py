from turtle import title

from PyParty import Hero
from Py4GWCoreLib import Map, Agent, Player, GLOBAL_CACHE, Color, ImGui
from Py4GWCoreLib import ProfessionShort, Campaign, Routines, Utils
from Py4GWCoreLib.native_src.context.WorldContext import AttributeStruct
from Py4GWCoreLib.native_src.context.AvailableCharacterContext import AvailableCharacterStruct
import PyImGui
import PyPlayer
import PyAgent
import PySkillbar

from typing import Optional, Dict, List, Tuple

from Sources.ApoSource.account_data_src.rank_data_src import RankData
from Sources.ApoSource.account_data_src.faction_data_src import FactionData
from Sources.ApoSource.account_data_src.experience_data_src import ExperienceData
from Sources.ApoSource.account_data_src.title_data_src import TitleData
from Sources.ApoSource.account_data_src.quest_data_src import QuestData

MODULE_NAME = "Account Info"

class AgentData:
    class GeneralData:
        def __init__(self, agent_id:int):
            self.agent_id: int = agent_id
            self.owner_id: int = 0
            self.hero_id: int = 0 #need to implement
            self.login_number: int = 0
            self.player_number: int = 0
            self.name: str = ""
            self.name_requested: bool = False
            self.professions: Tuple[int, int] = (0,0)
            self.level: int = 0
            self.energy_data: tuple[float, float, int] = (0.0, 0.0, 0) #energy, max_energy, energy_pips
            self.hp_data: tuple[float, float, float] = (0.0, 0.0, 0.0) #hp, max_hp, hp_regen
            self.dager_status: int = 0
            self.weapon_type: int = 0
            self.attributes: list[AttributeStruct] = []
            self.model_id: int = 0
            self.coords: Tuple[float, float, float] = (0.0, 0.0, 0.0)
            self.zplane: int = 0
            self.rotation_angle: float = 0.0
            self.velocity_vector: Tuple[float, float] = (0.0, 0.0)
            self.can_be_viewed_in_party_window: bool = False
            self.overcast: float = 0.0
            
        def update(self):
            self.owner_id = Agent.GetOwnerID(self.agent_id)
            self.login_number = Agent.GetLoginNumber(self.agent_id)
            self.player_number = Agent.GetPlayerNumber(self.agent_id)
            if not self.name_requested:
                Agent.RequestName(self.agent_id)
                self.name_requested = True
                
            if self.name_requested and self.name == "":
                if Agent.IsNameReady(self.agent_id):
                    self.name = Agent.GetNameByID(self.agent_id)
               
            prof1, prof2 = Agent.GetProfessionIDs(self.agent_id)  
            if prof1 is None: prof1 = 0
            if prof2 is None: prof2 = 0   
            self.professions = (prof1, prof2)
            self.level = Agent.GetLevel(self.agent_id)
            energy = Agent.GetEnergy(self.agent_id)
            max_energy = Agent.GetMaxEnergy(self.agent_id)
            energy_pips = Agent.GetEnergyPips(self.agent_id)
            self.energy_data = (energy, max_energy, energy_pips)
            hp = Agent.GetHealth(self.agent_id)
            max_hp = Agent.GetMaxHealth(self.agent_id)
            hp_regen = Agent.GetHealthRegen(self.agent_id)
            self.hp_data = (hp, max_hp, hp_regen)
            self.dager_status = Agent.GetDaggerStatus(self.agent_id)
            self.weapon_type = Agent.GetWeaponType(self.agent_id)[0]
            self.attributes = Agent.GetAttributes(self.agent_id)
            self.model_id = Agent.GetModelID(self.agent_id)
            x,y,z = Agent.GetXYZ(self.agent_id)
            self.coords = (x,y,z)
            self.zplane = int(Agent.GetZPlane(self.agent_id))
            self.rotation_angle = Agent.GetRotationAngle(self.agent_id)
            self.velocity_vector = Agent.GetVelocityXY(self.agent_id)
            self.can_be_viewed_in_party_window = Agent.CanBeViewedInPartyWindow(self.agent_id)
            self.overcast = Agent.GetOvercast(self.agent_id)

    class Flags:
        def __init__(self):
            self.is_moving: bool = False
            self.is_knocked_down: bool = False
            self.is_bleeding: bool = False
            self.is_crippled: bool = False
            self.is_deep_wounded: bool = False
            self.is_poisoned: bool = False
            self.is_conditioned: bool = False
            self.is_enchanted: bool = False
            self.is_hexed: bool = False
            self.is_degen_hexed: bool = False
            self.is_dead: bool = False
            self.is_weapon_spelled: bool = False
            self.is_in_combat_stance: bool = False
            self.is_aggressive: bool = False
            self.is_attacking: bool = False
            self.is_casting: bool = False
            self.is_idle: bool = False
            self.is_martial: bool = False
            self.is_caster: bool = False
            self.is_melee: bool = False
            self.is_ranged: bool = False
            
        def update(self, agent_id:int):
            self.is_moving = Agent.IsMoving(agent_id)
            self.is_knocked_down = Agent.IsKnockedDown(agent_id)
            self.is_bleeding = Agent.IsBleeding(agent_id)
            self.is_crippled = Agent.IsCrippled(agent_id)
            self.is_deep_wounded = Agent.IsDeepWounded(agent_id)
            self.is_poisoned = Agent.IsPoisoned(agent_id)
            self.is_conditioned = Agent.IsConditioned(agent_id)
            self.is_enchanted = Agent.IsEnchanted(agent_id)
            self.is_hexed = Agent.IsHexed(agent_id)
            self.is_degen_hexed = Agent.IsDegenHexed(agent_id)
            self.is_dead = Agent.IsDead(agent_id)
            self.is_weapon_spelled = Agent.IsWeaponSpelled(agent_id)
            self.is_in_combat_stance = Agent.IsInCombatStance(agent_id)
            self.is_aggressive = Agent.IsAggressive(agent_id)
            self.is_attacking = Agent.IsAttacking(agent_id)
            self.is_casting = Agent.IsCasting(agent_id)
            self.is_idle = Agent.IsIdle(agent_id)
            self.is_martial = Agent.IsMartial(agent_id)
            self.is_caster = Agent.IsCaster(agent_id)
            self.is_melee = Agent.IsMelee(agent_id)
            self.is_ranged = Agent.IsRanged(agent_id)
            
    class SkillbarData:
        def __init__(self):
            self.agent_id: int = 0
            self.disabled: int = 0
            self.casting: int = 0
            self.casting_skill_id: int = 0
            self.skills: dict[int,tuple[int, PySkillbar.SkillbarSkill]] = {} #slot, (skill_id, skill_data)
            
        def update(self):
            self.agent_id = GLOBAL_CACHE.SkillBar.GetAgentID()
            self.disabled = GLOBAL_CACHE.SkillBar.GetDisabled()
            self.casting = GLOBAL_CACHE.SkillBar.GetCasting()
            self.casting_skill_id = Agent.GetCastingSkillID(self.agent_id)
            
            for i in range(1,9):
                skill_data = GLOBAL_CACHE.SkillBar.GetSkillBySlot(i)
                if skill_data:
                    self.skills[i] = (skill_data.id.id, skill_data)


            
    def __init__(self):
        self.agent_id: int = Player.GetAgentID()
        self.general_data = AgentData.GeneralData(self.agent_id)
        self.flags = AgentData.Flags()
        self.skillbar_data = AgentData.SkillbarData()
        

    

class PlayerData:
    def __init__(self):
        self.target_id: int = 0
        self.observing_id: int = 0
        self.player_uuid: Tuple[int, int, int, int] = (0,0,0,0)
        self.missions_completed: List[int] = []
        self.missions_bonus: List[int] = []
        self.missions_completed_hm: List[int] = []
        self.missions_bonus_hm: List[int] = []
        self.controlled_minions: List[Tuple[int, int]] = []
        self.learnable_character_skills: List[int] = []
        self.unlocked_character_skills: List[int] = []
        
        self.show_details: dict[str, bool] = {}
        
    def update(self):
        self.target_id = Player.GetTargetID()
        self.observing_id = Player.GetObservingID()
        self.player_uuid = Player.GetPlayerUUID()
        self.missions_completed = Player.GetMissionsCompleted()
        self.missions_bonus = Player.GetMissionsBonusCompleted()
        self.missions_completed_hm = Player.GetMissionsCompletedHM()
        self.missions_bonus_hm = Player.GetMissionsBonusCompletedHM()
        self.controlled_minions = Player.GetControlledMinions()
        self.learnable_character_skills = Player.GetLearnableCharacterSkills()
        self.unlocked_character_skills = Player.GetUnlockedCharacterSkills()
        
    def draw_content(self):
        PyImGui.text(f"Target ID: {self.target_id}")
        PyImGui.text(f"Observing ID: {self.observing_id}")
        PyImGui.text(f"Player UUID:")
        PyImGui.same_line(0,-1)
        for i, uuid_part in enumerate(self.player_uuid):
            PyImGui.text(f"{uuid_part}")
            if i < len(self.player_uuid) - 1:
                PyImGui.same_line(0,-1)

        if PyImGui.collapsing_header("Missions Completed", PyImGui.TreeNodeFlags.NoFlag):
            
            self.show_details["missions_not_completed"] = PyImGui.checkbox("Show Not Completed Missions", self.show_details.get("missions_not_completed", False))
            
            expanded_flags = []  # list of (map_id, completed)
            bits_per_entry = 32

            PyImGui.text(f"entries:{len(self.missions_completed)} -{len(self.missions_completed) * bits_per_entry} total missions tracked.")
            for i, mission_status in enumerate(self.missions_completed):
                base_map_id = i * bits_per_entry
                # explode bits
                for bit in range(bits_per_entry):
                    map_id = base_map_id + bit
                    completed = (mission_status >> bit) & 1
                    expanded_flags.append((map_id, completed))
                    map_status = "Completed" if completed else "Not Completed"
                    # show depending on filter
                    if self.show_details["missions_not_completed"] or completed:
                        status_txt = "Completed" if completed else "Not Completed"
                        PyImGui.text_colored(
                            f"MapID {map_id} - {Map.GetMapName(map_id)} - {status_txt}",
                            Utils.TrueFalseColor(bool(completed))
                        )


            if PyImGui.button("copy to clipboard"):
                # flatten only completed map IDs for convenience
                completed_ids = [mid for mid, flag in expanded_flags if flag]
                PyImGui.set_clipboard_text(", ".join(map(str, completed_ids)))


        if PyImGui.collapsing_header("Missions Bonus Completed", PyImGui.TreeNodeFlags.NoFlag):
            self.show_details["missions_bonus_not_completed"] = PyImGui.checkbox(
                "Show Not Completed Bonus", self.show_details.get("missions_bonus_not_completed", False)
            )

            expanded_flags = []
            bits_per_entry = 32
            PyImGui.text(f"entries:{len(self.missions_bonus)} -{len(self.missions_bonus) * bits_per_entry} total missions tracked.")
            for i, mission_status in enumerate(self.missions_bonus):
                base_map_id = i * bits_per_entry
                for bit in range(bits_per_entry):
                    map_id = base_map_id + bit
                    completed = (mission_status >> bit) & 1
                    expanded_flags.append((map_id, completed))
                    map_status = "Completed" if completed else "Not Completed"

                    if self.show_details["missions_bonus_not_completed"] or completed:
                        status_txt = "Completed" if completed else "Not Completed"
                        PyImGui.text_colored(
                            f"MapID {map_id} - {Map.GetMapName(map_id)} - {status_txt}",
                            Utils.TrueFalseColor(bool(completed))
                        )

            if PyImGui.button("copy to clipboard##missions_bonus"):
                completed_ids = [mid for mid, flag in expanded_flags if flag]
                PyImGui.set_clipboard_text(", ".join(map(str, completed_ids)))
        
        if PyImGui.collapsing_header("Missions Completed HM", PyImGui.TreeNodeFlags.NoFlag):
            self.show_details["missions_hm_not_completed"] = PyImGui.checkbox(
                "Show Not Completed Missions (HM)", self.show_details.get("missions_hm_not_completed", False)
            )

            expanded_flags = []
            bits_per_entry = 32
            PyImGui.text(f"entries:{len(self.missions_completed_hm)} -{len(self.missions_completed_hm) * bits_per_entry} total missions tracked.")
            for i, mission_status in enumerate(self.missions_completed_hm):
                base_map_id = i * bits_per_entry
                for bit in range(bits_per_entry):
                    map_id = base_map_id + bit
                    completed = (mission_status >> bit) & 1
                    expanded_flags.append((map_id, completed))
                    map_status = "Completed" if completed else "Not Completed"

                    if self.show_details["missions_hm_not_completed"] or completed:
                        status_txt = "Completed" if completed else "Not Completed"
                        PyImGui.text_colored(
                            f"MapID {map_id} - {Map.GetMapName(map_id)} - {status_txt}",
                            Utils.TrueFalseColor(bool(completed))
                        )

            if PyImGui.button("copy to clipboard##missions_completed_hm"):
                completed_ids = [mid for mid, flag in expanded_flags if flag]
                PyImGui.set_clipboard_text(", ".join(map(str, completed_ids)))
        
        if PyImGui.collapsing_header("Missions Bonus Completed HM", PyImGui.TreeNodeFlags.NoFlag):
            self.show_details["missions_bonus_hm_not_completed"] = PyImGui.checkbox("Show Not Completed Bonus (HM)", self.show_details.get("missions_bonus_hm_not_completed", False))
            
            expanded_flags = []
            bits_per_entry = 32
            PyImGui.text(f"entries:{len(self.missions_bonus_hm)} -{len(self.missions_bonus_hm) * bits_per_entry} total missions tracked.")
            for i, mission_status in enumerate(self.missions_bonus_hm):
                base_map_id = i * bits_per_entry
                for bit in range(bits_per_entry):
                    map_id = base_map_id + bit
                    completed = (mission_status >> bit) & 1
                    expanded_flags.append((map_id, completed))
                    
                    if self.show_details["missions_bonus_hm_not_completed"] or completed:
                        status_txt = "Completed" if completed else "Not Completed"
                        PyImGui.text_colored(
                            f"MapID {map_id} - {Map.GetMapName(map_id)} - {status_txt}",
                            Utils.TrueFalseColor(bool(completed))
                        )

            if PyImGui.button("copy to clipboard##missions_bonus_hm"):
                completed_ids = [mid for mid, flag in expanded_flags if flag]
                PyImGui.set_clipboard_text(", ".join(map(str, completed_ids)))
        
        
        if PyImGui.collapsing_header("Controlled Minions", PyImGui.TreeNodeFlags.NoFlag):
            for agent_id, minion_count in self.controlled_minions:
                PyImGui.text(f"Agent ID: {agent_id} - Minion Count: {minion_count}")
        if PyImGui.collapsing_header("Learnable Character Skills", PyImGui.TreeNodeFlags.NoFlag):
            for skill_id in self.learnable_character_skills:
                PyImGui.text(f"Skill ID: {skill_id}")
        if PyImGui.collapsing_header("Unlocked Character Skills", PyImGui.TreeNodeFlags.NoFlag):
            self.show_details["show_locked_skills"] = PyImGui.checkbox(
                "Show Locked Skills",
                self.show_details.get("show_locked_skills", False)
            )

            bits_per_entry = 32
            expanded_flags = []
            show_locked = self.show_details["show_locked_skills"]
            PyImGui.text(f"entries:{len(self.unlocked_character_skills)} -{len(self.unlocked_character_skills) * bits_per_entry} total skills tracked.")
            for i, skill_mask in enumerate(self.unlocked_character_skills):
                base_skill_id = i * bits_per_entry
                for bit in range(bits_per_entry):
                    skill_id = base_skill_id + bit
                    unlocked = (skill_mask >> bit) & 1
                    expanded_flags.append((skill_id, unlocked))

                    if show_locked or unlocked:
                        PyImGui.text_colored(
                            f"Skill ID {skill_id} - {GLOBAL_CACHE.Skill.GetName(skill_id)}",
                            Utils.TrueFalseColor(bool(unlocked))
                        )

            if PyImGui.button("copy to clipboard##unlocked_skills"):
                unlocked_ids = [sid for sid, flag in expanded_flags if flag]
                PyImGui.set_clipboard_text(", ".join(map(str, unlocked_ids)))


class AccountInfo: 
    #region AccountData
    class AccountData:
        def __init__(self, account_name: str ="", account_email: str ="", available_characters: List[AvailableCharacterStruct] = []):
            self.account_name: str = account_name
            self.account_email: str = account_email
            self.available_characters: List[AvailableCharacterStruct] = available_characters

        def draw_content(self):
            PyImGui.text(f"Account Name: {self.account_name}")
            PyImGui.text(f"Account Email: {self.account_email}")
            
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
                for char in self.available_characters:
                    PyImGui.table_next_row()

                    # Level
                    PyImGui.table_set_column_index(0)
                    PyImGui.text(str(char.level))
                    # Name
                    PyImGui.table_set_column_index(1)
                    PyImGui.text(char.player_name)

                    # Map
                    PyImGui.table_set_column_index(2)
                    PyImGui.text(Map.GetMapName(char.map_id))

                    # Professions
                    PyImGui.table_set_column_index(3)
                    primary = ProfessionShort(char.primary).name
                    secondary = ProfessionShort(char.secondary).name
                    PyImGui.text(f"{primary}/{secondary}")

                    # Campaign
                    PyImGui.table_set_column_index(4)
                    PyImGui.text(Campaign(char.campaign).name)

                    # Type
                    PyImGui.table_set_column_index(5)
                    PyImGui.text("PvP" if char.is_pvp else "PvE")

                PyImGui.end_table()

    #region AccountInfo
    def __init__(self):
        self.account_data = AccountInfo.AccountData()
        self.rank_data = RankData()
        self.faction_data = FactionData()
        self.experience = ExperienceData()
        self.title_data = TitleData()
        self.fetch_and_handle_quests = False
        self.quest_data = QuestData()
        self.player_data = PlayerData()
        
    def update(self):
        account_name = Player.GetAccountName()
        account_email = Player.GetAccountEmail()
        available_characters = Map.Pregame.GetAvailableCharacterList()
        self.account_data = AccountInfo.AccountData(account_name, account_email, available_characters)
        self.rank_data.update()
        self.faction_data.update()
        self.experience.update()
        self.title_data.update()   
        if self.fetch_and_handle_quests:    
            self.quest_data.update()
            
        self.player_data.update()


    def draw_content(self, window_width: float, window_height: float):
        if PyImGui.begin_tab_bar("AccountInfoTabs"):
            if PyImGui.begin_tab_item("Faction"):
                if PyImGui.begin_child("FactionsChild", (0, 0), False, PyImGui.WindowFlags.NoFlag):
                    if PyImGui.collapsing_header("Rank Data", PyImGui.TreeNodeFlags.NoFlag):
                        self.rank_data.draw_content()
                    self.faction_data.draw_content()
                    PyImGui.end_child()
                PyImGui.end_tab_item()
                
            if PyImGui.begin_tab_item("Titles"):
                if PyImGui.begin_child("TitlesChild", (0, 0), False, PyImGui.WindowFlags.NoFlag):
                    self.title_data.draw_content()
                    PyImGui.end_child()
                PyImGui.end_tab_item()
                
            if PyImGui.begin_tab_item("Account"):
                if PyImGui.begin_child("AccountChild", (0, 0), False, PyImGui.WindowFlags.NoFlag):
                    self.account_data.draw_content()
                    PyImGui.end_child()
                PyImGui.end_tab_item()
                
            if PyImGui.begin_tab_item("Quest Log"):
                if PyImGui.begin_child("QuestLogChild", (0, 0), False, PyImGui.WindowFlags.NoFlag):
                    self.fetch_and_handle_quests = PyImGui.checkbox("Fetch and Handle Quests", self.fetch_and_handle_quests)
                    if self.fetch_and_handle_quests:
                        self.quest_data.draw_content(window_width, window_height)
                    PyImGui.end_child()
                PyImGui.end_tab_item()
                
            if PyImGui.begin_tab_item("Player Data"):
                if PyImGui.begin_child("PlayerDataChild", (0, 0), False, PyImGui.WindowFlags.NoFlag):
                    self.experience.draw_content()
                    self.player_data.draw_content()
                    PyImGui.end_child()
                PyImGui.end_tab_item()
            PyImGui.end_tab_bar()

        

def tooltip():
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Account Data Monitor", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()

    # Description
    PyImGui.text("A comprehensive diagnostic dashboard that aggregates deep")
    PyImGui.text("character information. It provides a real-time overview of")
    PyImGui.text("stats, progression, and currency across the account.")
    PyImGui.spacing()

    # Features
    PyImGui.text_colored("Features:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Stat Tracking: Detailed view of Morale, Experience, and Attribute points")
    PyImGui.bullet_text("Title Progress: Live monitoring of track ranks (Sunspear, Lightbringer, etc.)")
    PyImGui.bullet_text("Currency Management: Displays current Faction counts for Kurzick, Luxon, and Imperial")
    PyImGui.bullet_text("Quest Log: Inspects active quest data and mission completion states")
    PyImGui.bullet_text("Skill Bar Audit: Visualizes equipped skills, attributes, and hero configurations")
    PyImGui.bullet_text("Modular Tabs: Organized into Factions, Titles, Quests, and Player Data sections")

    PyImGui.spacing()
    PyImGui.separator()
    PyImGui.spacing()

    # Credits
    PyImGui.text_colored("Credits:", title_color.to_tuple_normalized())
    PyImGui.bullet_text("Developed by Apo")

    PyImGui.end_tooltip()

def draw_window(account_info: AccountInfo):
    MIN_WIDTH = 400
    MIN_HEIGHT = 600

    if PyImGui.begin(MODULE_NAME):
        window_size = PyImGui.get_window_size()
        new_width = max(window_size[0], MIN_WIDTH)
        new_height = max(window_size[1], MIN_HEIGHT)

        # only update size if it changed
        if new_width != window_size[0] or new_height != window_size[1]:
            PyImGui.set_window_size(new_width, new_height, PyImGui.ImGuiCond.Always)

        # child region adjusts automatically
        if PyImGui.begin_child("AccountInfoChild", (new_width - 20, 0), True, PyImGui.WindowFlags.NoFlag):
            account_info.draw_content(new_width, new_height)
            PyImGui.end_child()
        PyImGui.end()

account_info = AccountInfo()
def main():
    account_info.update()
    draw_window(account_info)



if __name__ == "__main__":
    main()
