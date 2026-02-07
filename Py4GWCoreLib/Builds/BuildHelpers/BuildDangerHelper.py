import time
from Py4GWCoreLib import *
from typing import Iterable, List, Tuple

# Create type definitions for tables
ModelIterable = Iterable[int]
DangerEntry = Tuple[Iterable[int], str]
DangerTable = Iterable[DangerEntry]


# I have assumed a range of 500 for normal cripple/kd dangers and 2000 for special cases. This can be extended later if needed

class BuildDangerHelper:
    '''
    Helper class to manage danger detection for builds.
    It encapsulates the logic for checking cripple/kd dangers,
    spellcaster dangers, and body block detection with internal state.
    '''
    
    def __init__(
        self,
        cripple_kd_table: DangerTable = (),
        spellcast_table: DangerTable = (),
        scan_throttle_ms: float = 0.1,
        danger_check_cooldown: float = 0.1,
        spell_caster_check_cooldown: float = 1.0,
        extreme_kd_danger: List[str] | None = None,
        log_enabled: bool = False
    ):
        self.name = "BuildDangerHelper"
        self.log_enabled = log_enabled

        # tables provided by caller (tuples of (list_of_ids, name))
        self.cripple_kd_table: DangerTable = cripple_kd_table
        self.spellcast_table: DangerTable = spellcast_table
        self.extreme_kd_danger = extreme_kd_danger

        # timing / throttle configuration
        self.scan_throttle_ms = scan_throttle_ms
        self.danger_check_cooldown = danger_check_cooldown
        self.spell_caster_check_cooldown = spell_caster_check_cooldown

        # internal state / caches
        self._last_cripple_kd_check = 0.0
        self._last_cripple_kd_scan_time = 0.0
        self._last_spellcaster_check = 0.0
        self._last_scan_time_spellcaster = 0.0

        # movement / stuck detection state
        self.prev_pos = None
        self.last_move_time = time.time()

        # build lookup sets from provided tables
        self._rebuild_caches()

    def _rebuild_caches(self):
        '''
        Rebuild internal lookup sets from the provided tables.
        '''

        # aggregate all model ids for quick membership checks
        self.cripple_kd_models: set = set()
        self.extreme_kd_range_models: set = set()

        for model_ids, category in self.cripple_kd_table:
            # build set of normal-range models

            self.cripple_kd_models.update(model_ids)

            # build set of extreme-range (special-case) models based on configured terms
            # New behavior: callers can provide self.extreme_kd_danger (List[str]) containing
            # substrings to match against category names (case-insensitive). Models from
            # matching categories are collected into self.extreme_kd_range_models.
            terms = getattr(self, "extreme_kd_danger_list", None)
            if terms:
                norm_terms = [str(t).lower() for t in terms]
                lname = category.lower()
                if any(term in lname for term in norm_terms):
                    self.extreme_kd_range_models.update(model_ids)

        # build spellcaster id set from the spellcast table
        self.spellcaster_models = set()
        for model_ids, category in self.spellcast_table:
            self.spellcaster_models.update(model_ids)

        # Log the spellcaster models for debugging
        #ConsoleLog(self.name, f"Spellcaster models: {self.spellcaster_models}", Py4GW.Console.MessageType.Debug, True)


    def enemy_category_from_model_id(self, model_id: int) -> str:
        """
        Returns the category name for a given model ID.
        """

        for entry, name in self.cripple_kd_table:
            if model_id in entry:
                return name

        for entry, name in self.spellcast_table:
            if model_id in entry:
                return name

        return "Unknown"

    def check_cripple_kd(self, x: float, y: float) -> bool:
        """
        Checks for cripple/kd danger based on given (x, y) position.
        Returns True if a danger is detected according to the BuildDangerHelper's provided danger tables.
        Reports a fake chat warning.
        """
    
        # No models configured
        if (len(self.cripple_kd_models) == 0 and len(self.extreme_kd_range_models) == 0):
            return False
    
        now = time.time()

        # throttle checks based on last check times
        if now - self._last_cripple_kd_check < self.danger_check_cooldown:
            return False
        if now - self._last_cripple_kd_scan_time < self.scan_throttle_ms:
            return False
        self._last_cripple_kd_scan_time = now

        # Gather enemy agents within normal and extreme ranges
        close_enemies = Routines.Agents.GetFilteredEnemyArray(x, y, max_distance=500.0)
        far_enemies = Routines.Agents.GetFilteredEnemyArray(x, y, max_distance=2000.0)

        # Check close-range enemies first
        for enemy_id in close_enemies:
            model_id = Agent.GetModelID(enemy_id)
            if model_id in self.cripple_kd_models:
                enemy_category = self.enemy_category_from_model_id(model_id)
                Player.SendFakeChat(ChatChannel.CHANNEL_WARNING, f"Cripple/KD danger - {enemy_category} spotted!")
                self._last_cripple_kd_check = now
                return True

        # No extreme range models were configured - no more danger detection needed
        if len(self.extreme_kd_range_models) == 0:
            return False
       
        # Check far-range enemies for extreme-range models
        for enemy_id in far_enemies:
            model_id = Agent.GetModelID(enemy_id)
            if model_id in self.extreme_kd_range_models:
                enemy_category = self.enemy_category_from_model_id(model_id)
                Player.SendFakeChat(ChatChannel.CHANNEL_WARNING, f"Cripple/KD danger - {enemy_category} spotted!")
                self._last_cripple_kd_check = now
                return True

        return False

    def check_spellcaster(self, custom_distance: float = 2000.0, include_non_specified: bool = True) -> bool:
        """
        Checks for spellcaster danger within the specified distance.
        Returns True if a spellcaster is detected and reports a fake chat warning.
        """

        if not include_non_specified and len(self.spellcaster_models) == 0:
            return False

        # Throttle checks based on last check times
        now = time.time()
        if now - self._last_spellcaster_check < self.spell_caster_check_cooldown:
            return False

        if now - self._last_scan_time_spellcaster < self.scan_throttle_ms:
            return False
        self._last_scan_time_spellcaster = now

        # Get player position coordinates
        (x, y) = Player.GetXY()
        if not (x and y):
            return False

        # Scan for nearby enemies
        nearby_enemies = Routines.Agents.GetFilteredEnemyArray(x, y, max_distance=custom_distance)
        special_caster_found = False 
        
        # Check nearby enemies against specific provided spellcaster models
        for enemy_id in nearby_enemies:
            model_id = Agent.GetModelID(enemy_id)
            if model_id in self.spellcaster_models:
                special_caster_found = True
                break

        # If allowed, check for any spellcaster not in the specified table
        nearby_spellcaster = Routines.Agents.GetNearestEnemyCaster(custom_distance, aggressive_only=False) if include_non_specified else 0

        # Report if any spellcaster was danger found
        if special_caster_found or nearby_spellcaster:
            Player.SendFakeChat(ChatChannel.CHANNEL_WARNING, "Spellcaster - spotted!")
            self._last_spellcaster_check = now
            return True

        return False

    def body_block_detection(self, seconds: float = 2.0) -> bool:
        """
        Wrapped version of BodyBlockDetection using instance movement state.
        """
        nearby_enemies = Routines.Agents.GetNearestEnemy(Range.Touch.value)
        if not nearby_enemies:
            return False

        pos = Player.GetXY()
        if not pos:
            return False

        if not self.prev_pos:
            self.prev_pos = pos
            self.last_move_time = time.time()
            return False

        if Utils.Distance(pos, self.prev_pos) > Range.Touch.value:
            self.prev_pos = pos
            self.last_move_time = time.time()
            return False

        return time.time() - self.last_move_time >= seconds

    def update_tables(self, cripple_kd_table: DangerTable = (), spellcast_table: DangerTable = ()):
        """
        Replace underlying tables and rebuild caches if needed.
        """
        if cripple_kd_table:
            self.cripple_kd_table = cripple_kd_table
        if spellcast_table:
            self.spellcast_table = spellcast_table
        self._rebuild_caches()
