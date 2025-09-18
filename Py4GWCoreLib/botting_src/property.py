from __future__ import annotations
from collections import defaultdict
from typing import Dict, Iterable, Optional, Final, Any


from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .config import BotConfig  # for type checkers only

STEP_NAMES: Final[tuple[str, ...]] = (
    "ALCOHOL_COUNTER",
    "AUTO_COMBAT",
    "CANCEL_SKILL_REWARD_WINDOW",
    "CELERITY_COUNTER",
    "CITY_SPEED_COUNTER",
    "CONSETS_COUNTER",
    "CRAFT_ITEM",
    "CUPCAKES_COUNTER",
    "CUSTOM_STEP",
    "DIALOG_AT",
    "DP_REMOVAL_COUNTER",
    "ENTER_CHALLENGE",
    "EQUIP_ITEM",
    "FLAG_ALL_HEROES",
    "FOLLOW_PATH",
    "GET_PATH_TO",
    "GRAIL_COUNTER",
    "HALT_ON_DEATH",
    "HEADER_COUNTER",
    "HONEYCOMBS_COUNTER",
    "IMP_COUNTER",
    "LEAVE_PARTY",
    "LOG_ACTIONS",
    "MORALE_COUNTER",
    "MOVE_TO",
    "MOVEMENT_TIMEOUT",
    "MOVEMENT_TOLERANCE",
    "ON_FOLLOW_PATH_FAILED",
    "PAUSE_ON_DANGER",
    "PROPERTY",
    "SALVATION_COUNTER",
    "SEND_CHAT_MESSAGE",
    "SET_PATH_TO",
    "SPAWN_BONUS",
    "TRAVEL",
    "UPDATE_PLAYER_DATA",
    "WAIT_FOR_MAP_LOAD",
    "WASTE_TIME",
    "WITHDRAW_ITEMS",
    "UNKNOWN"
)
ALLOWED_STEPS: Final[frozenset[str]] = frozenset(STEP_NAMES)

class StepNameCounters:
    def __init__(self, seed: Dict[str, int] | None = None,
                 allowed: Iterable[str] = ALLOWED_STEPS) -> None:
        self._allowed = frozenset(s.upper() for s in allowed)
        self._counts: defaultdict[str, int] = defaultdict(int)
        if seed:
            for k, v in seed.items():
                ku = k.upper()
                if ku in self._allowed:
                    self._counts[ku] = int(v)

    def _canon(self, name: str) -> str:
        return name.upper()

    def _key_or_none(self, name: str) -> str:
        k = self._canon(name)
        return k if k in self._allowed else "UNKNOWN"

    def next_index(self, name: str) -> int:
        key = self._key_or_none(name)
        self._counts[key] += 1
        return self._counts[key]

    def get_index(self, name: str) -> int:
        return self._counts[self._key_or_none(name)]

    def reset_index(self, name: str, to: int = 0) -> None:
        self._counts[self._key_or_none(name)] = to

    def set_index(self, name: str, to: int) -> None:
        self._counts[self._key_or_none(name)] = to

    def clear_all(self) -> None:
        self._counts.clear()


class Property:
    """
    A flexible property system for BotConfig.
    - Always has an `active` flag.
    - Can have any number of extra fields (with defaults).
    """

    def __init__(self, parent: "BotConfig", name: str,
                 active: bool = True,
                 extra_fields: Optional[Dict[str, Any]] = None):
        self.parent = parent
        self.name = name

        # store defaults and current values
        self._defaults: Dict[str, Any] = {"active": active}
        self._values: Dict[str, Any] = {"active": active}

        if extra_fields:
            self._defaults.update(extra_fields)
            self._values.update(extra_fields)
            
    # ---- internal apply ----
    def _apply(self, field: str, value: Any):
        self._values[field] = value

    def get_now(self, field: str = "active") -> Any:
        self.get(field)
    
    def set_now(self, field: str, value: Any) -> None:
        self._apply(field, value)
  

    # ---- getters/setters ----
    def get(self, field: str = "active") -> Any:
        if field not in self._values:
            raise KeyError(f"Unknown field '{field}' in Property {self.name}")
        return self._values[field]

    def set(self, field: str, value: Any) -> None:
        if field not in self._values:
            raise KeyError(f"Unknown field '{field}' in Property {self.name}")
        step_name = f"{self.name}_{field}_SET_{self.parent.get_counter('PROPERTY')}"
        self.parent.FSM.AddState(
            name=step_name,
            execute_fn=lambda f=field, v=value: self._apply(f, v),
        )


    def is_active(self) -> bool:
        return bool(self._values["active"])

    def enable(self) -> None:
        step_name = f"{self.name}_ENABLE_{self.parent.get_counter('PROPERTY')}"
        self.parent.FSM.AddState(
            name=step_name,
            execute_fn=lambda: self._apply("active", True),
        )

    def disable(self) -> None:
        step_name = f"{self.name}_DISABLE_{self.parent.get_counter('PROPERTY')}"
        self.parent.FSM.AddState(
            name=step_name,
            execute_fn=lambda: self._apply("active", False),
        )

    def set_active(self, active: bool) -> None:
        step_name = f"{self.name}_ACTIVE_{self.parent.get_counter('PROPERTY')}"
        self.parent.FSM.AddState(
            name=step_name,
            execute_fn=lambda v=active: self._apply("active", v),
        )

    def reset(self, field: str = "active") -> None:
        if field not in self._defaults:
            raise KeyError(f"Unknown field '{field}' in Property {self.name}")
        step_name = f"{self.name}_{field}_RESET_{self.parent.get_counter('PROPERTY')}"
        default_value = self._defaults[field]
        self.parent.FSM.AddState(
            name=step_name,
            execute_fn=lambda f=field, v=default_value: self._apply(f, v),
        )

    def reset_all(self) -> None:
        for f, v in self._defaults.items():
            self.reset(f)


    # ---- representation ----
    def __repr__(self) -> str:
        return f"Property({self.name}, {self._values})"



class ConfigProperties:
    def __init__(self, parent: "BotConfig",
                 log_actions: bool = False,
                 halt_on_death: bool = True,
                 pause_on_danger: bool = False,
                 movement_timeout: int = 15000,
                 movement_tolerance: int = 150,
                 draw_path: bool = True,
                 use_occlusion: bool = True,
                 snap_to_ground: bool = True,
                 snap_to_ground_segments: int = 8,
                 floor_offset: int = 20,
                 follow_path_color: Any = None
                 ):
        from ..Py4GWcorelib import Color
        self.parent = parent

        if follow_path_color is None:
            follow_path_color = Color(255,255,255,255)
        # simple properties with only one field
        self.log_actions = Property(parent, "log_actions", active=log_actions)
        self.halt_on_death = Property(parent, "halt_on_death", active=halt_on_death)
        self.pause_on_danger = Property(parent, "pause_on_danger", active=pause_on_danger)
        self.movement_timeout = Property(parent, "movement_timeout", extra_fields={"value": movement_timeout})
        self.movement_tolerance = Property(parent, "movement_tolerance", extra_fields={"value": movement_tolerance})
        self.draw_path = Property(parent, "draw_path", active=draw_path)
        self.use_occlusion = Property(parent, "use_occlusion", active=use_occlusion)
        self.snap_to_ground = Property(parent, "snap_to_ground", active=snap_to_ground)
        self.snap_to_ground_segments = Property(parent, "snap_to_ground_segments", extra_fields={"value": snap_to_ground_segments})
        self.floor_offset = Property(parent, "floor_offset", extra_fields={"value": floor_offset})
        self.follow_path_color = Property(parent, "follow_path_color", extra_fields={"value": follow_path_color})

        self.follow_path_succeeded = Property(parent, "follow_path_succeeded", extra_fields={"value": False})
        self.dialog_at_succeeded = Property(parent, "dialog_at_succeeded", extra_fields={"value": False})

        # more properties can be added here
        
class UpkeepData:
    def __init__(self, parent: "BotConfig",
                 alcohol_active: bool = False,
                 alcohol_target_drunk_level: int = 2,
                 alcohol_disable_visual: bool = True,
                 armor_of_salvation_active: bool = False,
                 armor_of_salvation_restock: int = 0,
                 auto_combat_active: bool = True,
                 auto_inventory_management_active: bool = True,
                 auto_loot_active: bool = True,
                 birthday_cupcake_active: bool = False,
                 birthday_cupcake_restock: int = 0,
                 blue_rock_candy_active: bool = False,
                 blue_rock_candy_restock: int = 0,
                 bowl_of_skalefin_soup_active: bool = False,
                 bowl_of_skalefin_soup_restock: int = 0,
                 candy_apple_active: bool = False,
                 candy_apple_restock: int = 0,
                 candy_corn_active: bool = False,
                 candy_corn_restock: int = 0,
                 city_speed_active: bool = False,
                 drake_kabob_active: bool = False,
                 drake_kabob_restock: int = 0,
                 essence_of_celerity_active: bool = False,
                 essence_of_celerity_restock: int = 0,
                 four_leaf_clover_active: bool = False,
                 four_leaf_clover_restock: int = 0,
                 golden_egg_active: bool = False,
                 golden_egg_restock: int = 0,
                 grail_of_might_active: bool = False,
                 grail_of_might_restock: int = 0,
                 green_rock_candy_active: bool = False,
                 green_rock_candy_restock: int = 0,
                 hero_ai_active: bool = False,
                 honeycomb_active: bool = False,
                 honeycomb_restock: int = 0,
                 imp_active: bool = False,
                 morale_active:bool = False,
                 morale_target_level: int = 110,
                 pahnai_salad_active: bool = False,
                 pahnai_salad_restock: int = 0,
                 red_rock_candy_active: bool = False,
                 red_rock_candy_restock: int = 0,
                 slice_of_pumpkin_pie_active: bool = False,
                 slice_of_pumpkin_pie_restock: int = 0,
                 war_supplies_active: bool = False,
                 war_supplies_restock: int = 0,
                 #merchants
                 identify_kits_active: bool = True,
                 identify_kits_restock: int = 2,
                 salvage_kits_active: bool = True,
                 salvage_kits_restock: int = 4
                 ):
        self.parent = parent

        self.alcohol = Property(parent,"alcohol", active=alcohol_active,
            extra_fields={
                "target_drunk_level": alcohol_target_drunk_level,        # Drunk level to maintain
                "disable_visual": alcohol_disable_visual         # hide drunk visual effect
            }
        )

        self.city_speed = Property(parent,"city_speed", active=city_speed_active)

        self.morale = Property(parent, "morale",
            active=morale_active,
            extra_fields={"target_morale": morale_target_level,}
        )

        self.armor_of_salvation = Property(parent, "armor_of_salvation", active=armor_of_salvation_active,
                                           extra_fields={"restock_quantity": armor_of_salvation_restock,}
        )
        self.essence_of_celerity = Property(parent, "essence_of_celerity", active=essence_of_celerity_active,
            extra_fields={"restock_quantity": essence_of_celerity_restock,}
        )
        self.grail_of_might = Property(parent, "grail_of_might", active=grail_of_might_active,
            extra_fields={"restock_quantity": grail_of_might_restock,}
        )
        self.blue_rock_candy = Property(parent, "blue_rock_candy", active=blue_rock_candy_active,
            extra_fields={"restock_quantity": blue_rock_candy_restock,}
        )
        self.green_rock_candy = Property(parent, "green_rock_candy", active=green_rock_candy_active,
            extra_fields={"restock_quantity": green_rock_candy_restock,}
        )
        self.red_rock_candy = Property(parent, "red_rock_candy", active=red_rock_candy_active,
            extra_fields={"restock_quantity": red_rock_candy_restock,}
        )
        self.birthday_cupcake = Property(parent, "birthday_cupcake", active=birthday_cupcake_active,
            extra_fields={"restock_quantity": birthday_cupcake_restock,}
        )
        self.slice_of_pumpkin_pie = Property(parent, "slice_of_pumpkin_pie", active=slice_of_pumpkin_pie_active,
            extra_fields={"restock_quantity": slice_of_pumpkin_pie_restock,}
        )
        self.bowl_of_skalefin_soup = Property(parent, "bowl_of_skalefin_soup", active=bowl_of_skalefin_soup_active,
            extra_fields={"restock_quantity": bowl_of_skalefin_soup_restock,}
        )
        self.candy_apple = Property(parent, "candy_apple", active=candy_apple_active,
            extra_fields={"restock_quantity": candy_apple_restock,}
        )
        self.candy_corn = Property(parent, "candy_corn", active=candy_corn_active,
            extra_fields={"restock_quantity": candy_corn_restock,}
        )
        self.drake_kabob = Property(parent, "drake_kabob", active=drake_kabob_active,
            extra_fields={"restock_quantity": drake_kabob_restock,}
        )
        self.golden_egg = Property(parent, "golden_egg", active=golden_egg_active,
            extra_fields={"restock_quantity": golden_egg_restock,}
        )
        self.pahnai_salad = Property(parent, "pahnai_salad", active=pahnai_salad_active,
            extra_fields={"restock_quantity": pahnai_salad_restock,}
        )
        self.war_supplies = Property(parent, "war_supplies", active=war_supplies_active,
            extra_fields={"restock_quantity": war_supplies_restock,}
        )
        self.honeycomb = Property(parent, "honeycomb", active=honeycomb_active,
            extra_fields={"restock_quantity": honeycomb_restock,}
        )
        self.four_leaf_clover = Property(parent, "four_leaf_clover", active=four_leaf_clover_active,
            extra_fields={"restock_quantity": four_leaf_clover_restock,}
        )

        self.imp = Property(parent, "imp", active=imp_active)
        self.auto_combat = Property(parent, "auto_combat", active=auto_combat_active)
        self.hero_ai = Property(parent, "hero_ai", active=hero_ai_active)
        
        self.auto_inventory_management = Property(parent, "auto_inventory_management", active=auto_inventory_management_active)
        self.auto_loot = Property(parent, "auto_loot", active=auto_loot_active)
        
        self.identify_kits = Property(parent, "identify_kits", active=identify_kits_active,
            extra_fields={"restock_quantity": identify_kits_restock,}
        )

        self.salvage_kits = Property(parent, "salvage_kits", active=salvage_kits_active,
            extra_fields={"restock_quantity": salvage_kits_restock,}
        )

    def __repr__(self) -> str:
        return (
            f"UpkeepData("
            f"alcohol={self.alcohol}, "
            f"city_speed={self.city_speed}, "
            f"morale={self.morale}, "
            f"armor_of_salvation={self.armor_of_salvation}, "
            f"essence_of_celerity={self.essence_of_celerity}, "
            f"grail_of_might={self.grail_of_might}, "
            f"blue_rock_candy={self.blue_rock_candy}, "
            f"green_rock_candy={self.green_rock_candy}, "
            f"red_rock_candy={self.red_rock_candy}, "
            f"birthday_cupcake={self.birthday_cupcake}, "
            f"slice_of_pumpkin_pie={self.slice_of_pumpkin_pie}, "
            f"bowl_of_skalefin_soup={self.bowl_of_skalefin_soup}, "
            f"candy_apple={self.candy_apple}, "
            f"candy_corn={self.candy_corn}, "
            f"drake_kabob={self.drake_kabob}, "
            f"golden_egg={self.golden_egg}, "
            f"pahnai_salad={self.pahnai_salad}, "
            f"war_supplies={self.war_supplies}, "
        )
