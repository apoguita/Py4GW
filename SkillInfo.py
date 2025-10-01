import Py4GW
import PyImGui
from PyAgent import Profession, AttributeClass
from Py4GWCoreLib import *
import webbrowser
from fractions import Fraction

MODULE_NAME = "Skill Altas"
TEXTURE_FOLDER = "Textures\\Game UI\\Skill Description\\"
PROFESSION_TEXTURE_FOLDER = "Textures\\Profession_Icons\\"

import re
from typing import Any

def DrawCompareSkills():
    def compare_text(display_name, val_a, val_b):
        PyImGui.table_next_row()
        
        # Color by equality
        color = ColorPalette.GetColor("Green") if val_a == val_b else ColorPalette.GetColor("Red")
        normalized = color.to_tuple_normalized()

        # Skill A Column
        PyImGui.table_next_column()
        PyImGui.text_colored(f"{display_name}: {val_a}", normalized)

        # Skill B Column
        PyImGui.table_next_column()
        PyImGui.text_colored(f"{display_name}: {val_b}", normalized)

    global hovered_skill, askill_a, askill_b
    window_flags = PyImGui.WindowFlags.AlwaysAutoResize
    if PyImGui.begin("compare", window_flags):
        hs = GLOBAL_CACHE.SkillBar.GetHoveredSkillID()
        if hs != 0:
            hovered_skill = hs

        PyImGui.text(f"Hovered Skill ID: {hovered_skill}")
        askill_a = PyImGui.input_int("Skill A", askill_a)
        askill_b = PyImGui.input_int("Skill B", askill_b)

        if askill_a != 0 and askill_b != 0:
            if PyImGui.begin_table("Skills Comparison Table", 2, PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg):
                PyImGui.table_setup_column("Skill A")
                PyImGui.table_setup_column("Skill B")
                PyImGui.table_headers_row()

                skill_a = PySkill.Skill(askill_a)
                skill_b = PySkill.Skill(askill_b)

                # Texture + Name
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                ImGui.DrawTexture(GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(askill_a), 96, 96)
                PyImGui.text(f"ID: {askill_a}")
                PyImGui.text(f"Name: {GLOBAL_CACHE.Skill.GetNameFromWiki(askill_a)}")

                PyImGui.table_next_column()
                ImGui.DrawTexture(GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(askill_b), 96, 96)
                PyImGui.text(f"ID: {askill_b}")
                PyImGui.text(f"Name: {GLOBAL_CACHE.Skill.GetNameFromWiki(askill_b)}")

                # Field comparisons
                compare_text("special", skill_a.special, skill_b.special)
                compare_text("combo_req", skill_a.combo_req, skill_b.combo_req)
                compare_text("effect1", skill_a.effect1, skill_b.effect1)
                compare_text("condition", skill_a.condition, skill_b.condition)
                compare_text("effect2", skill_a.effect2, skill_b.effect2)
                compare_text("weapon_req", skill_a.weapon_req, skill_b.weapon_req)
                compare_text("title", skill_a.title, skill_b.title)
                compare_text("id_pvp", skill_a.id_pvp, skill_b.id_pvp)
                compare_text("combo", skill_a.combo, skill_b.combo)
                compare_text("target", skill_a.target, skill_b.target)
                compare_text("skill_equip_type", skill_a.skill_equip_type, skill_b.skill_equip_type)
                compare_text("overcast", skill_a.overcast, skill_b.overcast)
                compare_text("energy_cost", skill_a.energy_cost, skill_b.energy_cost)
                compare_text("health_cost", skill_a.health_cost, skill_b.health_cost)
                compare_text("adrenaline", skill_a.adrenaline, skill_b.adrenaline)
                compare_text("activation", skill_a.activation, skill_b.activation)
                compare_text("aftercast", skill_a.aftercast, skill_b.aftercast)
                compare_text("duration_0pts", skill_a.duration_0pts, skill_b.duration_0pts)
                compare_text("duration_15pts", skill_a.duration_15pts, skill_b.duration_15pts)
                compare_text("recharge", skill_a.recharge, skill_b.recharge)
                compare_text("skill_arguments", skill_a.skill_arguments, skill_b.skill_arguments)
                compare_text("scale_0pts", skill_a.scale_0pts, skill_b.scale_0pts)
                compare_text("scale_15pts", skill_a.scale_15pts, skill_b.scale_15pts)
                compare_text("bonus_scale_0pts", skill_a.bonus_scale_0pts, skill_b.bonus_scale_0pts)
                compare_text("bonus_scale_15pts", skill_a.bonus_scale_15pts, skill_b.bonus_scale_15pts)
                compare_text("aoe_range", skill_a.aoe_range, skill_b.aoe_range)
                compare_text("const_effect", skill_a.const_effect, skill_b.const_effect)
                compare_text("caster_overhead_animation_id", skill_a.caster_overhead_animation_id, skill_b.caster_overhead_animation_id)
                compare_text("caster_body_animation_id", skill_a.caster_body_animation_id, skill_b.caster_body_animation_id)
                compare_text("target_body_animation_id", skill_a.target_body_animation_id, skill_b.target_body_animation_id)
                compare_text("target_overhead_animation_id", skill_a.target_overhead_animation_id, skill_b.target_overhead_animation_id)
                compare_text("h0004", skill_a.h0004, skill_b.h0004)
                compare_text("h0032", skill_a.h0032, skill_b.h0032)
                compare_text("h0037", skill_a.h0037, skill_b.h0037)

                PyImGui.end_table()

    PyImGui.end()
    


selected_skill = 2235
compare_skills = False

table_start = (0.0, 0.0)
table_end = (0.0, 0.0)

hovered_skill = 0
askill_a = 0
askill_b = 0

@dataclass
class SkillData:
    skill_id: int
    name_from_wiki: str
    name: str
    texture_path: str
    profession : Profession
    profession_name: str
    attribute: AttributeClass
    attribute_name: str
    campaign : str
    health_cost: int
    overcast_cost: int
    adrenaline_cost: int
    energy_cost: int
    activation_time: float
    aftercast_time: float
    recharge_time: int
    weapon_req: int
    skill_type: int
    skill_type_description: str
    description: str
    concise_description: str

    is_elite: bool
    is_pve: bool
    
    def __init__(self, skill_id: int):
        self.skill_id = skill_id
        self.name_from_wiki = GLOBAL_CACHE.Skill.GetNameFromWiki(skill_id)
        self.name = GLOBAL_CACHE.Skill.GetName(skill_id)
        self.texture_path = GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(skill_id)
        self.profession_name = GLOBAL_CACHE.Skill.GetProfession(skill_id)[1]
        self.attribute = GLOBAL_CACHE.Skill.Attribute.GetAttribute(skill_id)
        self.attribute_name = self.attribute.GetName() if self.attribute.GetName() != "Unknown" else "No Attribute"

        self.campaign = GLOBAL_CACHE.Skill.GetCampaign(skill_id)[1]
        
        self.health_cost = GLOBAL_CACHE.Skill.Data.GetHealthCost(skill_id)
        self.overcast_cost = GLOBAL_CACHE.Skill.Data.GetOvercast(skill_id)
        self.adrenaline_cost = GLOBAL_CACHE.Skill.Data.GetAdrenaline(skill_id)
        self.energy_cost = GLOBAL_CACHE.Skill.Data.GetEnergyCost(skill_id)
        self.activation_time = GLOBAL_CACHE.Skill.Data.GetActivation(skill_id)
        self.aftercast_time = GLOBAL_CACHE.Skill.Data.GetAftercast(skill_id)
        self.recharge_time = GLOBAL_CACHE.Skill.Data.GetRecharge(skill_id)
        self.weapon_req = GLOBAL_CACHE.Skill.Data.GetWeaponReq(skill_id)
        self.skill_type, self.skill_type_description = GLOBAL_CACHE.Skill.GetType(skill_id)

        self.description = self.resolve_skill_description(GLOBAL_CACHE.Skill.GetDescription(skill_id))
        self.concise_description = self.resolve_skill_description(GLOBAL_CACHE.Skill.GetConciseDescription(skill_id))

        self.is_elite = GLOBAL_CACHE.Skill.Flags.IsElite(skill_id)
        self.is_pve = GLOBAL_CACHE.Skill.Flags.IsPvE(skill_id)
        
    def resolve_skill_description(self, raw_desc: str, attribute_level: int = 0) -> str:
        """
        Replace all [! ... !] progression tags in a skill description using the correct progression values.
        If attribute_level is given, resolve using that rank.
        If not, resolve as a min–max range from level 0 to 15.
        """

        # Get all progression fields (now supports multiple)
        progressions = Skill.GetProgressionData(self.skill_id)
        if not progressions:
            return raw_desc

        # Wrap all progressions into known_fields format
        known_fields: list[dict[str, Any]] = [{
            "attribute": attr,
            "field": field_name,
            "values": values_dict
        } for attr, field_name, values_dict in progressions]

        def format_value(v: float) -> str:
            """Format numbers like 20.0 → 20, 17.50 → 17.5"""
            return f"{v:.2f}".rstrip('0').rstrip('.') if '.' in f"{v:.2f}" else str(int(v))

        def match_score(tag_values: list[float], values: dict[int, float]) -> float:
            """Compare tag values to progression data at levels 0, 12, 15"""
            v0 = values.get(0, 0.0)
            v12 = values.get(12, v0)
            v15 = values.get(15, v0)
            if len(tag_values) == 1:
                return abs(tag_values[0] - v15)
            elif len(tag_values) == 2:
                return abs(tag_values[0] - v0) + abs(tag_values[1] - v15)
            elif len(tag_values) == 3:
                return abs(tag_values[0] - v0) + abs(tag_values[1] - v12) + abs(tag_values[2] - v15)
            return float('inf')

        def find_best_field(tag_values: list[float]) -> dict[str, Any]:
            """Find the best matching field based on tag values"""
            best_field = known_fields[0]
            best_score = match_score(tag_values, best_field["values"])

            for field in known_fields[1:]:
                score = match_score(tag_values, field["values"])
                if score < best_score:
                    best_score = score
                    best_field = field

            return best_field

        def replace_tag(match: re.Match) -> str:
            tag_values = [float(g) for g in match.groups() if g is not None]

            best_field = find_best_field(tag_values)
            values = best_field["values"]

            if attribute_level and attribute_level > 0:
                level = max(0, min(attribute_level, max(values.keys())))
                resolved_value = values.get(level)
                if resolved_value is None:
                    available_levels = sorted(k for k in values if k <= level)
                    resolved_value = values[available_levels[-1]] if available_levels else 0.0
                return format_value(resolved_value)
            else:
                # If attribute_level is not set, preserve the tag range
                if len(tag_values) == 1:
                    return format_value(tag_values[0])
                elif len(tag_values) == 2:
                    return f"{format_value(tag_values[0])}...{format_value(tag_values[1])}"
                else:
                    return f"{format_value(tag_values[0])}...{format_value(tag_values[1])}...{format_value(tag_values[2])}"


        # Regex pattern for [!x!], [!x...y!], [!x...y...z!]
        pattern = r'\[\!(\d+(?:\.\d+)?)(?:\.\.\.(\d+(?:\.\d+)?))?(?:\.\.\.(\d+(?:\.\d+)?))?\!\]'
        return re.sub(pattern, replace_tag, raw_desc)    
        
    def GetProfessionColor(self) -> Tuple[Color, Color]:
        profession = self.profession_name    
        color = ColorPalette.GetColor("Gray")         
        if profession == "Warrior":
            color = ColorPalette.GetColor("GW_Warrior")
        elif profession == "Ranger":
            color = ColorPalette.GetColor("GW_Ranger")
        elif profession == "Monk":
            color = ColorPalette.GetColor("GW_Monk")
        elif profession == "Necromancer":   
            color = ColorPalette.GetColor("GW_Necromancer")
        elif profession == "Mesmer":
            color = ColorPalette.GetColor("GW_Mesmer")
        elif profession == "Elementalist":
            color = ColorPalette.GetColor("GW_Elementalist")
        elif profession == "Assassin":  
            color = ColorPalette.GetColor("GW_Assassin")
        elif profession == "Ritualist":
            color = ColorPalette.GetColor("GW_Ritualist")
        elif profession == "Paragon":
            color = ColorPalette.GetColor("GW_Paragon")
        elif profession == "Dervish":
            color = ColorPalette.GetColor("GW_Dervish")
            
        faded_color = Color(color.r, color.g, color.b, 25)
        return color, faded_color
        
    def draw_background_frame(self):
        color, faded_color = self.GetProfessionColor()
        #Draw Background Frame
        #Outline
        PyImGui.draw_list_add_rect(
                table_start[0]-2, table_start[1]-2,
                table_end[0]+2, table_end[1]+2,
                color.to_color(),  # Golden yellow outline
                0.0,  # Corner rounding
                PyImGui.DrawFlags._NoFlag,
                2.0   # Line thickness
            )
        #Background
        PyImGui.draw_list_add_rect_filled(
                table_start[0], table_start[1],
                table_end[0], table_end[1],
                faded_color.to_color(),
                0.0,
                PyImGui.DrawFlags._NoFlag
            )
        
    def draw_skill_icon(self):
        # Texture column
        PyImGui.begin_group()
        texture_path = GLOBAL_CACHE.Skill.ExtraData.GetTexturePath(self.skill_id)
        ImGui.DrawTexture(texture_path, 96, 96)
        if self.is_elite:
            text_color = ColorPalette.GetColor("GW_Gold").to_tuple_normalized()
            PyImGui.text_colored("Elite Skill", text_color)
        else:
            text_color = ColorPalette.GetColor("GW_White").to_tuple_normalized()
              
        att_desc = self.attribute_name if not self.is_pve else "PvE"

        PyImGui.text_wrapped(f"{att_desc}")
        PyImGui.text_wrapped(f"{self.campaign}")
        PyImGui.text(f"ID: {self.skill_id}")

        PyImGui.end_group()
        if PyImGui.is_item_hovered():
            if PyImGui.begin_tooltip():
                PyImGui.text(f"ID: {self.skill_id}")
                PyImGui.text(f"Texture: {texture_path}")
                PyImGui.text(f"Attribute: {att_desc}")
                PyImGui.text(f"Profession: {self.profession_name}")
                PyImGui.text(f"Campaign: {self.campaign}")
                PyImGui.text(f"Elite: {'Yes' if self.is_elite else 'No'}")
                PyImGui.end_tooltip()
                
    def draw_title(self):
        PyImGui.begin_group()
        ImGui.push_font("Bold", 22)
        if self.is_elite:
            text_color = ColorPalette.GetColor("GW_Gold").to_tuple_normalized()
        else:
            text_color = ColorPalette.GetColor("GW_White").to_tuple_normalized()
            
        PyImGui.text_colored(f"{self.name_from_wiki}", text_color)
        ImGui.pop_font()
        PyImGui.end_group()
        
        if PyImGui.is_item_hovered():
            if PyImGui.begin_tooltip():
                PyImGui.text(f"Name: {self.name_from_wiki}")
                PyImGui.text(f"Dictionary Name: {self.name}")
                PyImGui.end_tooltip()

    def is_maintained(self):
        is_enchantment = GLOBAL_CACHE.Skill.Flags.IsEnchantment(self.skill_id)
        if not is_enchantment:
            return False
        duration_0, duration_15 = GLOBAL_CACHE.Skill.Attribute.GetDuration(self.skill_id)
        return duration_0 > 10_000 and duration_15 > 10_000
    
    def is_sacrifice(self):
        return self.health_cost > 0

    def is_overcast(self):
        return self.overcast_cost > 0

    def is_adrenaline(self):
        return self.adrenaline_cost > 0

    def is_energy(self):
        return self.energy_cost > 0

    def is_activation_time(self):
        return self.activation_time > 0.0

    def is_recharge(self):
        return self.recharge_time > 0
                    
    def draw_upkeep(self):
        if self.is_maintained():
            PyImGui.begin_group()
            ImGui.push_font("Bold", 20)
            PyImGui.text("-1")
            ImGui.pop_font()
            PyImGui.same_line(0,5)
            ImGui.DrawTexture(TEXTURE_FOLDER + "upkeep.png", 22, 22)
            PyImGui.end_group()
            if PyImGui.is_item_hovered():
                if PyImGui.begin_tooltip():
                    energy_pips = GLOBAL_CACHE.Agent.GetEnergyPips(GLOBAL_CACHE.Player.GetAgentID())
                    PyImGui.text(f"Skill is maintained")
                    PyImGui.text(f"You can upkeep {energy_pips}x this skill")
                    PyImGui.end_tooltip()
                    
    def draw_sacrifice(self):
        if self.is_sacrifice():
            PyImGui.begin_group()
            ImGui.push_font("Bold", 20)
            PyImGui.text(f"{self.health_cost}%")
            ImGui.pop_font()
            PyImGui.same_line(0,5)
            ImGui.DrawTexture(TEXTURE_FOLDER + "sacrifice.png", 22, 22)
            PyImGui.end_group()
            if PyImGui.is_item_hovered():
                if PyImGui.begin_tooltip():
                    max_health = GLOBAL_CACHE.Agent.GetMaxHealth(GLOBAL_CACHE.Player.GetAgentID())
                    PyImGui.text(f"Health Cost: {self.health_cost}%")
                    PyImGui.text(f"HP Cost: {math.ceil(max_health * (self.health_cost / 100))}")
                    PyImGui.end_tooltip()

    def draw_overcast(self):
        if self.is_overcast():
            PyImGui.begin_group()
            ImGui.push_font("Bold", 20)
            PyImGui.text(f"{self.overcast_cost}")
            ImGui.pop_font()
            PyImGui.same_line(0,5)
            ImGui.DrawTexture(TEXTURE_FOLDER + "overcast.png", 22, 22)
            PyImGui.end_group()
            if PyImGui.is_item_hovered():
                if PyImGui.begin_tooltip():
                    PyImGui.text(f"Overcast: {self.overcast_cost}")
                    PyImGui.end_tooltip()

    def draw_adrenaline(self):
        if self.is_adrenaline():
            PyImGui.begin_group()
            ImGui.push_font("Bold", 20)
            PyImGui.text(f"{math.ceil(self.adrenaline_cost / 25)}")
            ImGui.pop_font()
            PyImGui.same_line(0,5)
            ImGui.DrawTexture(TEXTURE_FOLDER + "adrenaline.png", 22, 22)
            PyImGui.end_group()
            if PyImGui.is_item_hovered():
                if PyImGui.begin_tooltip():
                    PyImGui.text(f"Adrenaline hits: {math.ceil(self.adrenaline_cost / 25)}")
                    PyImGui.text(f"Adrenaline points: {self.adrenaline_cost}")
                    PyImGui.end_tooltip()

    def draw_energy(self):
        if self.is_energy():
            PyImGui.begin_group()
            ImGui.push_font("Bold", 20)
            PyImGui.text(f"{self.energy_cost}")
            ImGui.pop_font()
            PyImGui.same_line(0,5)
            ImGui.DrawTexture(TEXTURE_FOLDER + "energy.png", 22, 22)
            PyImGui.end_group()
            if PyImGui.is_item_hovered():
                if PyImGui.begin_tooltip():
                    PyImGui.text(f"Energy Cost: {self.energy_cost}")
                    energy_pips = GLOBAL_CACHE.Agent.GetEnergyPips(GLOBAL_CACHE.Player.GetAgentID())
                    PyImGui.text(f"Energy Pips: {energy_pips}")
                    max_energy = GLOBAL_CACHE.Agent.GetMaxEnergy(GLOBAL_CACHE.Player.GetAgentID())
                    PyImGui.text(f"Energy: {max_energy}")

                    if energy_pips > 0:
                        recoup_time = round(self.energy_cost / (energy_pips * 0.33), 2)
                        PyImGui.text(f"Time to Recoup Cost: {recoup_time} seconds")
                    else:
                        PyImGui.text("No regeneration (0 pips)")
                    
                    PyImGui.end_tooltip()

    def draw_activation_time(self):
        if self.is_activation_time():
            PyImGui.begin_group()
            fraction = Fraction(self.activation_time).limit_denominator(10)  # limit to reasonable fractions like 1/4, 1/2
            ImGui.push_font("Bold", 20)
            PyImGui.text(f"{fraction}")
            ImGui.pop_font()
            PyImGui.same_line(0,5)
            ImGui.DrawTexture(TEXTURE_FOLDER + "activation.png", 22, 22)
            PyImGui.end_group()
            if PyImGui.is_item_hovered():
                if PyImGui.begin_tooltip():
                    PyImGui.text(f"Activation Time: {self.activation_time} seconds")
                    PyImGui.text(f"Aftercast: {self.aftercast_time}")
                    PyImGui.end_tooltip()

    def draw_recharge(self):
        if self.is_recharge():
            PyImGui.begin_group()
            ImGui.push_font("Bold", 20)
            PyImGui.text(f"{self.recharge_time}")
            ImGui.pop_font()
            PyImGui.same_line(0,5)
            ImGui.DrawTexture(TEXTURE_FOLDER + "recharge.png", 22, 22)
            PyImGui.end_group()
            if PyImGui.is_item_hovered():
                if PyImGui.begin_tooltip():
                    PyImGui.text(f"Recharge Time: {self.recharge_time} seconds")
                    PyImGui.end_tooltip()
                    
    def strip_skill_type(self, desc: str) -> str:
        if not desc:
            return ""
        parts = desc.split(".", 1)
        return parts[1].strip() if len(parts) > 1 else ""


    def draw_description(self):
        PyImGui.begin_group()
        if self.is_elite:
            elite_status = "Elite "
        else:
            elite_status = ""
        
        skill_type, skill_type_description = GLOBAL_CACHE.Skill.GetType(self.skill_id)

        if SkillType(skill_type) != SkillType.Attack:
            formatted_type = (f"{skill_type_description}. ")
        else:
            weapon_req = GLOBAL_CACHE.Skill.Data.GetWeaponReq(self.skill_id)
            
            if weapon_req in WeaporReq._value2member_map_:
                weapon_enum = WeaporReq(weapon_req)
                weapon_req_desc = weapon_enum.name + " " + skill_type_description
            else:
                weapon_enum = WeaporReq.None_
                weapon_req_desc = skill_type_description
            formatted_type = f"{weapon_req_desc}. "
        trimmed_desc = self.strip_skill_type(GLOBAL_CACHE.Skill.GetDescription(self.skill_id))
        parsed_desc = self.resolve_skill_description(trimmed_desc, 0)
        description = f"{elite_status}{formatted_type}{parsed_desc}"
        PyImGui.text_wrapped(f"{description}")
        PyImGui.end_group()
        if PyImGui.is_item_hovered():
            if PyImGui.begin_tooltip():
                PyImGui.push_text_wrap_pos(400)
                concise = GLOBAL_CACHE.Skill.GetConciseDescription(self.skill_id)
                concise = self.resolve_skill_description(concise, 0)
                PyImGui.text_wrapped(f"{concise}")
                PyImGui.pop_text_wrap_pos()
                PyImGui.end_tooltip()
        
    def DrawSkillCard(self):
        global table_start, table_end
        
        PyImGui.begin_group()
        table_start = PyImGui.get_cursor_screen_pos()
        self.draw_background_frame()
        
        if PyImGui.begin_table(f"Skill Table##{self.skill_id}", 2, PyImGui.TableFlags.NoFlag):
            PyImGui.table_setup_column("Texture", init_width_or_weight=100.0, flags=PyImGui.TableColumnFlags.WidthFixed)
            PyImGui.table_setup_column("Skill Name", init_width_or_weight=100.0, flags=PyImGui.TableColumnFlags.WidthStretch)
            PyImGui.table_next_row()
            PyImGui.table_next_column()
            
            self.draw_skill_icon()
            PyImGui.table_next_column()
            self.draw_title()
            self.draw_upkeep()
            PyImGui.same_line(0,-1)
            self.draw_sacrifice()
            PyImGui.same_line(0,-1)
            self.draw_overcast()
            PyImGui.same_line(0,-1)
            self.draw_adrenaline()
            PyImGui.same_line(0,-1) 
            self.draw_energy()
            PyImGui.same_line(0,-1) 
            self.draw_activation_time()
            PyImGui.same_line(0,-1) 
            self.draw_recharge()
            PyImGui.same_line(0,-1)
            PyImGui.new_line()
            self.draw_description()
    
            PyImGui.end_table()
        PyImGui.end_group()
        table_end = PyImGui.get_item_rect_max()
    
 
window_module = ImGui.WindowModule(module_name="Skill Atlas", window_name=MODULE_NAME, window_size=(500, 600), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
 
class FilterButton:
    def __init__(self, profession: str, texture_path: str, width: int = 32, height: int = 32):
        self.profession_name = profession
        self.texture_path = texture_path
        self.active = False
        self.width = width
        self.height = height

    def draw(self):
        self.active = ImGui.image_toggle_button(
            f"##{self.profession_name}_button",
            self.texture_path,
            self.active,
            self.width,
            self.height
        )
             
             
ProfessionButtons = [
    FilterButton("Warrior", PROFESSION_TEXTURE_FOLDER + "[1] - Warrior.png"),
    FilterButton("Ranger", PROFESSION_TEXTURE_FOLDER + "[2] - Ranger.png"),
    FilterButton("Monk", PROFESSION_TEXTURE_FOLDER + "[3] - Monk.png"),
    FilterButton("Necromancer", PROFESSION_TEXTURE_FOLDER + "[4] - Necromancer.png"),
    FilterButton("Mesmer", PROFESSION_TEXTURE_FOLDER + "[5] - Mesmer.png"),
    FilterButton("Elementalist", PROFESSION_TEXTURE_FOLDER + "[6] - Elementalist.png"),
    FilterButton("Assassin", PROFESSION_TEXTURE_FOLDER + "[7] - Assassin.png"),
    FilterButton("Ritualist", PROFESSION_TEXTURE_FOLDER + "[8] - Ritualist.png"),
    FilterButton("Paragon", PROFESSION_TEXTURE_FOLDER + "[9] - Paragon.png"),
    FilterButton("Dervish", PROFESSION_TEXTURE_FOLDER + "[10] - Dervish.png")
]
    
def DrawMainWindow():
    if ImGui.gw_window.begin( name = window_module.window_name,
                                  pos  = (window_module.window_pos[0], window_module.window_pos[1]),
                                  size = (window_module.window_size[0], window_module.window_size[1]),
                                  collapsed = window_module.collapse,
                                  pos_cond = PyImGui.ImGuiCond.FirstUseEver,
                                  size_cond = PyImGui.ImGuiCond.Always):
        
        window_size = PyImGui.get_window_size()
        PyImGui.text(f"window_width: {window_size[0]}")
        PyImGui.same_line(0,-1)
        PyImGui.text(f"window_height: {window_size[1]}")
        
        for index, button in enumerate(ProfessionButtons):
            button.draw()
            if index < len(ProfessionButtons) - 1:
                PyImGui.same_line(0, 5)


    ImGui.gw_window.end(window_module.window_name)



def main():
    global selected_skill, compare_skills, table_start, table_end
    
    if not Routines.Checks.Map.MapValid():
        return
    
    try:
        DrawMainWindow()
        window_flags = PyImGui.WindowFlags.AlwaysAutoResize
        if PyImGui.begin("move", window_flags):
            hovered_skill = GLOBAL_CACHE.SkillBar.GetHoveredSkillID()
            PyImGui.text(f"Hovered Skill ID: {hovered_skill}")
            if hovered_skill != 0:
                selected_skill = hovered_skill

            selected_skill = PyImGui.input_int("Selected Skill ID", selected_skill)

            compare_skills = ImGui.toggle_button("Compare Skills", compare_skills)
            if compare_skills:
                DrawCompareSkills()

            if selected_skill != 0:
                skill = SkillData(selected_skill)
                skill.DrawSkillCard()
      
                
        PyImGui.end()
    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

    
if __name__ == "__main__":
    main()
    
