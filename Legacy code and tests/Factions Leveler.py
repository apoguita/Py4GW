import Py4GW
import PyImGui
from Py4GWCoreLib import *
from Py4GWCoreLib import Routines
from Py4GWCoreLib import GLOBAL_CACHE

from typing import List, Tuple

MODULE_NAME = "Factions Profession Leveler"

class FSM_Config:
    def __init__(self):
        self.FSM:FSM = FSM(MODULE_NAME)
        self.script_running = False
        self.combat_handler:SkillManager.Autocombat = SkillManager.Autocombat()
        self.combat_active = True
        self.run_timer = Timer()
        
        self.use_cupcakes = True
        self.amount_of_cupcakes = 50
        self.use_honeycombs = True
        self.amount_of_honeycombs = 100
        
        self.draw_follow_path = True
        self.path_to_draw = []

        self.initialize()
        
    def initialize(self):
        self.FSM.AddYieldRoutineStep(name = "Exit Monastery Overlook", coroutine_fn=self.ExitMonasteryOverlook)
        self.FSM.AddYieldRoutineStep(name = "Wait shing jea Monastery to Load 001",coroutine_fn = lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Shing Jea Monastery")))
        self.FSM.AddYieldRoutineStep(name = "Exit to Courtyard 001", coroutine_fn=self.ExitToCourtyard001)
        self.FSM.AddYieldRoutineStep(name = "Wait for Linnok Courtyard Map Load 001", coroutine_fn=lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Linnok Courtyard")))
        self.FSM.AddYieldRoutineStep(name = "Unlock Secondary and Exit", coroutine_fn=self.UnlockSecondaryAndExit)
        self.FSM.AddYieldRoutineStep(name = "Wait shing jea Monastery to Load 002",coroutine_fn = lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Shing Jea Monastery")))
        self.FSM.AddYieldRoutineStep(name = "Unlock Xunlai Storage", coroutine_fn=self.UnlockXunlaiStorage)
        self.FSM.AddYieldRoutineStep(name = "Craft Weapons", coroutine_fn=self.CraftWeapons)
        self.FSM.AddYieldRoutineStep(name = "Exit Shing Jea Monastery", coroutine_fn=self.ExitShingJeaMonastery)
        self.FSM.AddYieldRoutineStep(name = "Wait for Sunqua Vale Map Load 001", coroutine_fn=lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Sunqua Vale")))
        self.FSM.AddYieldRoutineStep(name = "Travel to Minister Cho", coroutine_fn=self.TravelToMinisterCho)
        minister_cho_map_id = 214
        self.FSM.AddYieldRoutineStep(name = "Wait for Minister Cho Map Load", coroutine_fn=lambda: self.WaitforMapLoad(minister_cho_map_id))
        self.FSM.AddYieldRoutineStep(name = "Prepare for Minister Cho Mission", coroutine_fn=self.PrepareForMinisterChoMission)
        self.FSM.AddYieldRoutineStep(name = "Wait for Minister Cho Mission Load", coroutine_fn=lambda: self.WaitforMapLoad(minister_cho_map_id))
        self.FSM.AddYieldRoutineStep(name = "Minister Cho Mission", coroutine_fn=self.MinisterChoMission)
        self.FSM.AddYieldRoutineStep(name = "Take Warning the Tengu and Exit", coroutine_fn=self.TakeWarningTheTenguandExit)
        self.FSM.AddYieldRoutineStep(name = "Wait for Kinya Province Map Load", coroutine_fn=lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Kinya Province"))) #236
        self.FSM.AddYieldRoutineStep(name = "Warning the Tengu", coroutine_fn=self.WarningTheTengu)
        self.FSM.AddYieldRoutineStep(name = "Wait shing jea Monastery to Load 003",coroutine_fn = lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Shing Jea Monastery")))
        self.FSM.AddYieldRoutineStep(name = "Exit Monastery Overlook 002", coroutine_fn=self.ExitMonasteryOverlook002)
        self.FSM.AddYieldRoutineStep(name = "Wait for Sunqua Vale Map Load 002", coroutine_fn=lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Sunqua Vale")))
        self.FSM.AddYieldRoutineStep(name = "Travel to Tsumei Village", coroutine_fn=self.TravelTsumeiVillage)
        self.FSM.AddYieldRoutineStep(name = "Wait for Tsumei Village Map Load", coroutine_fn=lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Tsumei Village")))
        self.FSM.AddYieldRoutineStep(name = "Exit Tsumei Village", coroutine_fn=self.ExitTsumeiVillage)
        self.FSM.AddYieldRoutineStep(name = "Wait for Panjiang Peninsula Map Load", coroutine_fn=lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Panjiang Peninsula")))
        self.FSM.AddYieldRoutineStep(name = "The Threat Grows", coroutine_fn=self.TheThreatGrows)
        self.FSM.AddYieldRoutineStep(name = "Wait shing jea Monastery to Load 004",coroutine_fn = lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Shing Jea Monastery")))
        self.FSM.AddYieldRoutineStep(name = "Exit to Courtyard 002", coroutine_fn=self.ExitToCourtyard002)
        self.FSM.AddYieldRoutineStep(name = "Wait for Linnok Courtyard Map Load 002", coroutine_fn=lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Linnok Courtyard")))
        self.FSM.AddYieldRoutineStep(name = "Finish quest and advance to Saoshang Trail", coroutine_fn=self.FinishQuestsAndAdvanceToSaoshangTrail)
        saoshang_trail_map_id = 313
        self.FSM.AddYieldRoutineStep(name = "Wait for Saoshang Trail Map Load", coroutine_fn=lambda: self.WaitforMapLoad(saoshang_trail_map_id))
        self.FSM.AddYieldRoutineStep(name = "Traverse Saoshang Trail", coroutine_fn=self.TraverseSaoshangTrail)
        self.FSM.AddYieldRoutineStep(name = "Wait for Seitung Harbor Map Load 001", coroutine_fn=lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Seitung Harbor")))
        self.FSM.AddYieldRoutineStep(name = "Take Reward and Exit Seitung Harbor", coroutine_fn=self.TakeRewardAndExitSeitungHarbor)
        self.FSM.AddYieldRoutineStep(name = "Wait for Jaya Bluffs Map Load", coroutine_fn=lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Jaya Bluffs")))
        self.FSM.AddYieldRoutineStep(name = "Go to Zen Daijun 001", coroutine_fn=self.GoToZenDaijunPart001)
        self.FSM.AddYieldRoutineStep(name = "Wait for Haiju Lagoon Map Load", coroutine_fn=lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Haiju Lagoon")))
        self.FSM.AddYieldRoutineStep(name = "Go to Zen Daijun 002", coroutine_fn=self.GoToZenDaijunPart002)
        zen_daijun_map_id = 213
        self.FSM.AddYieldRoutineStep(name = "Wait for Zen Daijun Map Load", coroutine_fn=lambda: self.WaitforMapLoad(zen_daijun_map_id))
        self.FSM.AddYieldRoutineStep(name = "Prepare for Zen Daijun Mission", coroutine_fn=self.PrepareForZenDaijunMission)
        self.FSM.AddYieldRoutineStep(name = "Zen Daijun Mission", coroutine_fn=self.ZenDaijunMission)
        self.FSM.AddYieldRoutineStep(name = "Wait for Seitung Harbor Map Load 002", coroutine_fn=lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Seitung Harbor")))
        self.FSM.AddYieldRoutineStep(name = "End Routines", coroutine_fn=self.Endroutine)
        
    #region HELPERS
    
    def _stop_execution(self):
        self.script_running = False
        self.FSM.stop()
        Py4GW.Console.Log(MODULE_NAME, "Script stopped.", Py4GW.Console.MessageType.Info)
        yield from Routines.Yield.wait(100)
        
    def _prepare_for_battle(self):
        
        profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
        if profession == "Warrior":
            yield from Routines.Yield.Skills.LoadSkillbar("OQcUEvq0jvIClLHAAAAAAAAAAA",log=False)
        elif profession == "Ranger":
            yield from Routines.Yield.Skills.LoadSkillbar("OgcUcLs1jvIPsv5yAAAAAAAAAA",log=False)
        elif profession == "Monk":
            yield from Routines.Yield.Skills.LoadSkillbar("OwcB0lkRuMAAAAAAAAAA",log=False)
        elif profession == "Necromancer":
            yield from Routines.Yield.Skills.LoadSkillbar("OAdTUOj8FxlTDAAAAAAAAAAA",log=False)
        elif profession == "Mesmer":
            yield from Routines.Yield.Skills.LoadSkillbar("OQdTAEx9FRDcZAAAAAAAAAAA",log=False)
        elif profession == "Elementalist":
            yield from Routines.Yield.Skills.LoadSkillbar("OgdToO28FRYcZAAAAAAAAAAA",log=False)
        elif profession == "Ritualist":
            yield from Routines.Yield.Skills.LoadSkillbar("OAej8JgHpMusvJAAAAAAAAAAAA",log=False)
        elif profession == "Assassin":
            yield from Routines.Yield.Skills.LoadSkillbar("OwBj0NfyoJPsLDAAAAAAAAAA",log=False)
            
        GLOBAL_CACHE.Party.LeaveParty()
        yield from Routines.Yield.wait(250)
        
        party_size = GLOBAL_CACHE.Map.GetMaxPartySize()
        
        zen_daijun_map_id = 213
        
        if party_size <= 4:
            HEALER_ID = 1
            GLOBAL_CACHE.Party.Henchmen.AddHenchman(HEALER_ID)
            yield from Routines.Yield.wait(200)
            SPIRITS_ID = 5
            GLOBAL_CACHE.Party.Henchmen.AddHenchman(SPIRITS_ID)
            yield from Routines.Yield.wait(200)
            GUARDIAN_ID = 2
            GLOBAL_CACHE.Party.Henchmen.AddHenchman(GUARDIAN_ID)
            yield from Routines.Yield.wait(200)
        elif GLOBAL_CACHE.Map.GetMapID() == GLOBAL_CACHE.Map.GetMapIDByName("Seitung Harbor"):
            GUARDIAN_ID = 2
            GLOBAL_CACHE.Party.Henchmen.AddHenchman(GUARDIAN_ID)
            yield from Routines.Yield.wait(200)
            DEADLY_ID = 3
            GLOBAL_CACHE.Party.Henchmen.AddHenchman(DEADLY_ID)
            yield from Routines.Yield.wait(200)
            SHOCK_ID = 1
            GLOBAL_CACHE.Party.Henchmen.AddHenchman(SHOCK_ID)
            yield from Routines.Yield.wait(200)
            SPIRITS_ID = 4
            GLOBAL_CACHE.Party.Henchmen.AddHenchman(SPIRITS_ID)
            yield from Routines.Yield.wait(200)
            HEALER_ID = 5
            GLOBAL_CACHE.Party.Henchmen.AddHenchman(HEALER_ID)
            yield from Routines.Yield.wait(200)
        elif GLOBAL_CACHE.Map.GetMapID() == zen_daijun_map_id:
            FIGHTER_ID = 3
            GLOBAL_CACHE.Party.Henchmen.AddHenchman(FIGHTER_ID)
            yield from Routines.Yield.wait(200)
            CUTTHROAT_ID = 2
            GLOBAL_CACHE.Party.Henchmen.AddHenchman(CUTTHROAT_ID)
            yield from Routines.Yield.wait(200)
            EARTH_ID = 1
            GLOBAL_CACHE.Party.Henchmen.AddHenchman(EARTH_ID)
            yield from Routines.Yield.wait(200)
            SPIRIT_ID = 8
            GLOBAL_CACHE.Party.Henchmen.AddHenchman(SPIRIT_ID)
            yield from Routines.Yield.wait(200)
            HEALER_ID = 5
            GLOBAL_CACHE.Party.Henchmen.AddHenchman(HEALER_ID)
            yield from Routines.Yield.wait(200)

        summoning_stone_in_bags = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Igneous_Summoning_Stone.value)
        if summoning_stone_in_bags < 1:
            GLOBAL_CACHE.Player.SendChatCommand("bonus")
            yield from Routines.Yield.wait(200)
            
        target_cupcake_count = self.amount_of_cupcakes 
        if self.use_cupcakes:
            model_id = ModelID.Birthday_Cupcake.value
            cupcake_in_bags = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
            cupcake_in_storage = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)

            cupcakes_needed = target_cupcake_count - cupcake_in_bags
            if cupcakes_needed > 0 and cupcake_in_storage > 0:
                # First, try to withdraw exactly what we need
                items_withdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, cupcakes_needed)
                yield from Routines.Yield.wait(250)

                if not items_withdrawn:
                    # Try withdrawing as much as possible instead
                    fallback_amount = min(cupcakes_needed, cupcake_in_storage)
                    items_withdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, fallback_amount)
                    yield from Routines.Yield.wait(250)

                    if not items_withdrawn:
                        Py4GW.Console.Log(MODULE_NAME, "Failed to withdraw cupcakes from storage.", Py4GW.Console.MessageType.Error)

        yield from Routines.Yield.wait(250)
        
        target_honeycomb_count = self.amount_of_honeycombs
        if self.use_honeycombs:
            model_id = ModelID.Honeycomb.value
            honey_in_bags = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
            honey_in_storage = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)

            honey_needed = target_honeycomb_count - honey_in_bags
            if honey_needed > 0 and honey_in_storage > 0:
                # Try withdrawing the full amount first
                items_withdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, honey_needed)
                yield from Routines.Yield.wait(250)

                if not items_withdrawn:
                    # Fallback to withdraw whatever is available
                    fallback_amount = min(honey_needed, honey_in_storage)
                    items_withdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, fallback_amount)
                    yield from Routines.Yield.wait(250)

                    if not items_withdrawn:
                        Py4GW.Console.Log(MODULE_NAME, "Failed to withdraw honeycombs from storage.", Py4GW.Console.MessageType.Error)

    def PopImp(self):
        summoning_stone = ModelID.Igneous_Summoning_Stone.value
        stone_id = GLOBAL_CACHE.Inventory.GetFirstModelID(summoning_stone)
        imp_effect_id = 2886
        has_effect = GLOBAL_CACHE.Effects.HasEffect(GLOBAL_CACHE.Player.GetAgentID(), imp_effect_id)

        imp_model_id = 513
        others = GLOBAL_CACHE.Party.GetOthers()
        cast_imp = True  # Assume we should cast

        for other in others:
            if GLOBAL_CACHE.Agent.GetModelID(other) == imp_model_id:
                if not GLOBAL_CACHE.Agent.IsDead(other):
                    # Imp is alive — no need to cast
                    cast_imp = False
                break  # Found the imp, no need to keep checking

        if stone_id and not has_effect and cast_imp:
            GLOBAL_CACHE.Inventory.UseItem(stone_id)
            yield from Routines.Yield.wait(500)

    def UseCupcake(self):
        if not self.use_cupcakes:
            return

        if ((not Routines.Checks.Map.MapValid()) and (not Map.IsExplorable())):
            return
        
        if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            return

        cupcake__id = GLOBAL_CACHE.Inventory.GetFirstModelID(ModelID.Birthday_Cupcake.value)
        cupcake_effect = GLOBAL_CACHE.Skill.GetID("Birthday_Cupcake_skill")
        
        if not GLOBAL_CACHE.Effects.HasEffect(GLOBAL_CACHE.Player.GetAgentID(), cupcake_effect) and cupcake__id:
            GLOBAL_CACHE.Inventory.UseItem(cupcake__id)
            yield from Routines.Yield.wait(500)
            
    def UseHoneycomb(self):
        if not self.use_honeycombs:
            return
        
        if ((not Routines.Checks.Map.MapValid()) and (not Map.IsExplorable())):
            return
        
        if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            return
        
        target_morale = 110
        
        while True:
            morale = GLOBAL_CACHE.Player.GetMorale()
            if morale >= target_morale:
                break

            honeycomb_id = GLOBAL_CACHE.Inventory.GetFirstModelID(ModelID.Honeycomb.value)
            if not honeycomb_id:
                break

            GLOBAL_CACHE.Inventory.UseItem(honeycomb_id)
            yield from Routines.Yield.wait(500)
        
        
    def AutoCombat(self):
        self.combat_handler.SetWeaponAttackAftercast()
        while True:
            if not (Routines.Checks.Map.MapValid() and 
                    Routines.Checks.Player.CanAct() and
                    Map.IsExplorable() and
                    not self.combat_handler.InCastingRoutine()):
                ActionQueueManager().ResetQueue("ACTION")
                yield from Routines.Yield.wait(100)
            else:
                yield from self.PopImp()
                yield from self.UseCupcake()
                yield from self.UseHoneycomb()
                
                if self.combat_active:
                    self.combat_handler.HandleCombat()  

            yield
        
    def _movement_eval_exit_on_map_loading(self):
        if GLOBAL_CACHE.Map.IsMapLoading():
            return True
        
        if not self.script_running:
            return True
        
        return False
    
    def Endroutine(self):
        self.script_running = False
        self.FSM.stop()
        Py4GW.Console.Log(MODULE_NAME, "Script ended.", Py4GW.Console.MessageType.Info)
        yield from Routines.Yield.wait(100)
    
    def WaitforMapLoad(self, target_map_id):
        wait_of_map_load = yield from Routines.Yield.Map.WaitforMapLoad(target_map_id)
        if not wait_of_map_load:
            Py4GW.Console.Log(MODULE_NAME, "Map load failed.", Py4GW.Console.MessageType.Error)
            yield from self._stop_execution()
        yield from Routines.Yield.wait(1000)
        
    from typing import Generator, Any, Tuple, List

    def follow_path(self, path: List[Tuple[float, float]], pause_on_danger: bool = False) -> Generator[Any, Any, bool]:
        self.path_to_draw = path.copy()
        pause_fn = (lambda: Routines.Checks.Agents.InDanger(aggro_area=Range.Earshot)) if pause_on_danger else None
        is_someone_dead = False
        players = GLOBAL_CACHE.Party.GetPlayers()
        henchmen = GLOBAL_CACHE.Party.GetHenchmen()
        heroes = GLOBAL_CACHE.Party.GetHeroes()

        
        for player in players:
            agent_id = GLOBAL_CACHE.Party.Players.GetAgentIDByLoginNumber(player.login_number)
            if GLOBAL_CACHE.Agent.IsDead(agent_id):
                is_someone_dead = True
                break
        for henchman in henchmen:
            if GLOBAL_CACHE.Agent.IsDead(henchman.agent_id):
                is_someone_dead = True
                break
            
        for hero in heroes:
            if GLOBAL_CACHE.Agent.IsDead(hero.agent_id):
                is_someone_dead = True
                break
            
        pause_fn = pause_fn or (lambda: is_someone_dead)
        
        
        success_movement = yield from Routines.Yield.Movement.FollowPath(
            path_points=path,
            custom_exit_condition=lambda: self._movement_eval_exit_on_map_loading(),
            log=False,
            custom_pause_fn= pause_fn,
        )

        if not success_movement:
            if GLOBAL_CACHE.Map.IsMapLoading():
                return True
            yield from self._stop_execution()
            return False

        if not self.script_running:
            yield from Routines.Yield.wait(100)
            return False

        return True


    def interact_with_agent(self,coords: Tuple[float, float],dialog_id: Optional[int] = None) -> Generator[Any, Any, bool]:
        result = yield from Routines.Yield.Agents.InteractWithAgentXY(*coords)
        if not result:
            yield from self._stop_execution()
            return False

        if not self.script_running:
            yield from Routines.Yield.wait(100)
            return False

        if dialog_id is not None:
            GLOBAL_CACHE.Player.SendDialog(dialog_id)
            yield from Routines.Yield.wait(500)

        return True
    
    def draw_path(self, points, rgba):
        if points and len(points) >= 2:
            color = Color(*rgba).to_dx_color()
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                z1 = DXOverlay.FindZ(x1, y1) - 125
                z2 = DXOverlay.FindZ(x2, y2) - 125
                DXOverlay().DrawLine3D(x1, y1, z1, x2, y2, z2, color, False)
            
    from typing import List, Tuple

    def chain_paths(self, waypoints: List[Tuple[float, float]], z: float):
        """
        Chains multiple (x, y) waypoints using AutoPathing().get_path.
        Each segment starts at the end of the previous.
        
        Parameters:
            waypoints: A list of 2D (x, y) target points.
            z: The elevation to use (same for all points).
        
        Returns:
            A full 2D path as List[(x, y)], chained across all waypoints.
        """
        if not waypoints or len(waypoints) < 2:
            return [(waypoints[0][0], waypoints[0][1])] if waypoints else []

        full_path: List[Tuple[float, float, float]] = []
        start: Tuple[float, float, float] = waypoints[0] + (z,)
        full_path.append(start)

        for target in waypoints[1:]:
            end: Tuple[float, float, float] = target + (z,)
            segment = yield from AutoPathing().get_path(start, end)
            full_path.extend(segment)
            start = segment[-1] if segment else end  # fallback in case of empty segment

        yield
        return [(x, y) for x, y, _ in full_path] 

    

    #region LOGIC
        
    def ExitMonasteryOverlook(self):             
        path_to_ludo = yield from AutoPathing().get_path_to(-7011, 5750)

        if not (yield from self.follow_path(path_to_ludo)):
            return

        I_AM_SURE = 0x85
        if not (yield from self.interact_with_agent((-7048, 5817), dialog_id=I_AM_SURE)):
            return

        
    def ExitToCourtyard001(self):
        path_to_courtyard = yield from AutoPathing().get_path_to(-3480, 9460)
        
        if not (yield from self.follow_path(path_to_courtyard)):
            return
        
                
    def UnlockSecondaryAndExit(self):
        path_to_togo = yield from AutoPathing().get_path_to(-159, 9174)
        if not (yield from self.follow_path(path_to_togo)):
            return
        
        profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
        UNLOCK_SECONDARY = 0x813D08 if profession != "Assassin" else 0x813D0E

        if not (yield from self.interact_with_agent((-92, 9217), dialog_id=UNLOCK_SECONDARY)):
            return
        
        cancel_button_frame_id = UIManager.GetFrameIDByHash(784833442)  # Cancel button frame ID
        if not cancel_button_frame_id:
            Py4GW.Console.Log(MODULE_NAME, "Cancel button frame ID not found.", Py4GW.Console.MessageType.Error)
            yield from self._stop_execution()
            return
        
        while not UIManager.FrameExists(cancel_button_frame_id):
            yield from Routines.Yield.wait(1000)
            return
        
        UIManager.FrameClick(cancel_button_frame_id)
        yield from Routines.Yield.wait(1000)
        
        cancel_button_frame_id = UIManager.GetFrameIDByHash(784833442)
        if not cancel_button_frame_id:
            Py4GW.Console.Log(MODULE_NAME, "Cancel button frame ID not found.", Py4GW.Console.MessageType.Error)
            yield from self._stop_execution()
            return
        
        while not UIManager.FrameExists(cancel_button_frame_id):
            yield from Routines.Yield.wait(1000)
            return
        
        UIManager.FrameClick(cancel_button_frame_id)
        yield from Routines.Yield.wait(1000)

        TAKE_REWARD = 0x813D07
        if not (yield from self.interact_with_agent((-92, 9217), dialog_id=TAKE_REWARD)):
            return
        TAKE_QUEST = 0x813E01
        if not (yield from self.interact_with_agent((-92, 9217), dialog_id=TAKE_QUEST)):
            return
        
        exit_path = path_to_togo.reverse() or []
        exit_path.append((-3762, 9471))  # Return to the starting point
        
        if not (yield from self.follow_path(exit_path)):
            return
        
                
    def UnlockXunlaiStorage(self):
        path_to_xunlai: List[Tuple[float, float]] = [(-4958, 9472),(-5465, 9727),(-4791, 10140),(-3945, 10328),(-3869, 10346),]
        if not (yield from self.follow_path(path_to_xunlai)):
            return

        UNLOCK_STORAGE = 0x84
        if not (yield from self.interact_with_agent((-3749, 10367), dialog_id=UNLOCK_STORAGE)):
            return  

        
    def CraftWeapons(self):
        path_to_crafter = yield from AutoPathing().get_path_to(-6423, 12183)
        if not (yield from self.follow_path(path_to_crafter)):
            return
    
        MELEE_CLASSES = ["Warrior", "Ranger", "Assassin"]
        profession,_ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
        
        if profession in MELEE_CLASSES:
            if not (yield from self.interact_with_agent((-6519, 12335))):
                return
        
            iron_in_storage = GLOBAL_CACHE.Inventory.GetModelCountInStorage(ModelID.Iron_Ingot.value)
            
            if iron_in_storage < 5:
                Py4GW.Console.Log(MODULE_NAME, "Not enough Iron Ingots (5) to craft weapons.", Py4GW.Console.MessageType.Error)
                yield from self._stop_execution()
                return

            items_withdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(ModelID.Iron_Ingot.value, 5)
            if not items_withdrawn:
                Py4GW.Console.Log(MODULE_NAME, "Failed to withdraw (5) Iron Ingots from storage.", Py4GW.Console.MessageType.Error)
                yield from self._stop_execution()
                return
            
            yield from Routines.Yield.wait(500)
            
            SAI_MODEL_ID = 11643
            merchant_item_list = GLOBAL_CACHE.Trading.Merchant.GetOfferedItems()
            for item_id in merchant_item_list:
                
                if GLOBAL_CACHE.Item.GetModelID(item_id) == SAI_MODEL_ID:
                    iron_ingots = GLOBAL_CACHE.Inventory.GetFirstModelID(ModelID.Iron_Ingot.value)
                    if iron_ingots:
                        trade_item_list = [iron_ingots]
                        quantity_list = [5]
                    
                        GLOBAL_CACHE.Trading.Crafter.CraftItem(item_id, 100, trade_item_list, quantity_list)
                        yield from Routines.Yield.wait(500)
                        break
        
            #equip crafted weapon
            crafted_weapon = GLOBAL_CACHE.Inventory.GetFirstModelID(SAI_MODEL_ID)
            if crafted_weapon:
                GLOBAL_CACHE.Inventory.EquipItem(crafted_weapon, GLOBAL_CACHE.Player.GetAgentID())
                yield from Routines.Yield.wait(500)
            else:
                Py4GW.Console.Log(MODULE_NAME, "Crafted weapon not found in inventory.", Py4GW.Console.MessageType.Error)
                yield from self._stop_execution()
                return
        else:
            yield from self._prepare_for_battle()
            wand = GLOBAL_CACHE.Inventory.GetFirstModelID(6508) #wand
            GLOBAL_CACHE.Inventory.EquipItem(wand, GLOBAL_CACHE.Player.GetAgentID())
            yield from Routines.Yield.wait(100)
            shield = GLOBAL_CACHE.Inventory.GetFirstModelID(6514) #shield
            GLOBAL_CACHE.Inventory.EquipItem(shield, GLOBAL_CACHE.Player.GetAgentID())
            yield from Routines.Yield.wait(100)
        
    def ExitShingJeaMonastery(self):
        path_to_exit = yield from AutoPathing().get_path_to(-14961,11453)
        if not (yield from self.follow_path(path_to_exit)):
            return
        
    def TravelToMinisterCho(self):
        path_to_minister = yield from AutoPathing().get_path_to(6698, 16095)
        
        if not (yield from self.follow_path(path_to_minister)):
            return

        GUARDMAN_ZUI_DLG4 = 0x80000B
        if not (yield from self.interact_with_agent((6637, 16147), dialog_id=GUARDMAN_ZUI_DLG4)):
            return
        
        yield from Routines.Yield.wait(5000)
        
    def PrepareForMinisterChoMission(self):
        ACCEPT_QUEST = 0x813E07
        if not (yield from self.interact_with_agent((7884, -10029), dialog_id=ACCEPT_QUEST)):
            return
        
        yield from self._prepare_for_battle()

        GLOBAL_CACHE.Map.EnterChallenge()

        yield from Routines.Yield.wait(4500)  # Wait for the map to load and the challenge to start
        
    def MinisterChoMission(self):
        autocombat = self.AutoCombat()
        GLOBAL_CACHE.Coroutines.append(autocombat)

        try:
            z = float(GLOBAL_CACHE.Agent.GetZPlane(GLOBAL_CACHE.Player.GetAgentID()))

            waypoints: list[tuple[float, float]] = [
                (6358, -7348),     # Start
                (507, -8910),      # First door
                (4889, -5043),     # Map tutorial
                (6216, -1108),     # Corner
                (2617, 642),       # Past bridge
                (0, 1137),         # First fight
                (-7454, -7384),    # Zoo
                (-9138, -4191),    # First zoo fight
                (-7109, -25),      # Bridge exit
                (-7443, 2243),     # Zoo exit
                (-16924, 2445)     # Minister Cho
            ]

            full_path = yield from self.chain_paths(waypoints, z)
   
            if not (yield from self.follow_path(full_path, pause_on_danger=True)):
                return
                    
            if not (yield from self.interact_with_agent((-17031, 2448))):
                return

            while True:
                mapid = GLOBAL_CACHE.Map.GetMapID() #251
                if (Routines.Checks.Map.MapValid() and (mapid == GLOBAL_CACHE.Map.GetMapIDByName("Ran Musu Gardens"))):
                    break
                yield from Routines.Yield.wait(1000)
        finally:  
            if autocombat in GLOBAL_CACHE.Coroutines:
                GLOBAL_CACHE.Coroutines.remove(autocombat)
                yield from Routines.Yield.wait(1000)
            
    def TakeWarningTheTenguandExit(self):
        TAKE_WARNING = 0x815301
        if not (yield from self.interact_with_agent((15846, 19013), dialog_id=TAKE_WARNING)):
            yield from self._stop_execution()
            return
        
        yield from self._prepare_for_battle()

        exit_path: List[Tuple[float, float]] = [(15911, 19050),(15495, 18564),(14813, 18021),(14629, 17285),
                     (15122, 16584),(14936, 15747),(14928, 15720),(14730,15176)]
        
        if not (yield from self.follow_path(exit_path)):
            yield from self._stop_execution()
            return
        
    def WarningTheTengu(self):
        first_half_path: List[Tuple[float, float]] = [(14621, 14767),(14018, 15121),(13218, 15462),(12393, 15581),(11960, 14900),
                                                    (11651, 14089),(11196, 13354),(10671, 12664),(10049, 12060),(9392, 11492),
                                                    (8582, 11284),(7736, 11456),(6909, 11701),(6132, 12084),(5413, 12572),
                                                    (4701, 13061),(3895, 13378),(3041, 13377),(2215, 13137),(1429, 12768),]
        
        if not (yield from self.follow_path(first_half_path)):
            yield from self._stop_execution()
            return
                
        autocombat = self.AutoCombat()
        GLOBAL_CACHE.Coroutines.append(autocombat)

        try:
        
            second_half_path: List[Tuple[float, float]] = [(687, 12331),(-115, 11996),(-920, 11681),(-1782, 11613),(-2636, 11539),
                                                            (-3250, 10969),(-3391, 10127),(-3580, 9285),(-3748, 8702),(-3906, 8316),
                                                            (-4093, 7476),(-3456, 6918),(-2696, 6496),(-1889, 6187),(-1097, 5864),
                                                            (-957, 5057),(-983, 4931),]
            
            if not (yield from self.follow_path(second_half_path, pause_on_danger=True)):
                yield from self._stop_execution()
                return
            
            CONTINUE_QUEST = 0x815304
            if not (yield from self.interact_with_agent((-1023, 4844), dialog_id=CONTINUE_QUEST)):
                yield from self._stop_execution()
                return

            path_to_kill_spot: List[Tuple[float, float]] = [(-988, 4912),(-950, 4435),(-1031, 3568),(-1525, 2870),(-2308, 2525),
                                                            (-3055, 2099),(-3749, 1590),(-4484, 1136),(-5011, 732),(-5011, 732),]
            
            if not (yield from self.follow_path(path_to_kill_spot, pause_on_danger=True)):
                yield from self._stop_execution()
                return

            yield from Routines.Yield.wait(1000)
            
            while Routines.Checks.Agents.InDanger(aggro_area=Range.Earshot):
                yield from Routines.Yield.wait(1000)
            
            path_to_kill_spot.reverse()
            
            if not (yield from self.follow_path(path_to_kill_spot, pause_on_danger=True)):
                yield from self._stop_execution()
                return
        
            TAKE_REWARD = 0x815307
            if not (yield from self.interact_with_agent((-1023, 4844), dialog_id=TAKE_REWARD)):
                yield from self._stop_execution()
                return

            TAKE_THE_THREAT_GROWS = 0x815401
            GLOBAL_CACHE.Player.SendDialog(TAKE_THE_THREAT_GROWS)
            yield from Routines.Yield.wait(500)
        finally:
            if autocombat in GLOBAL_CACHE.Coroutines:
                GLOBAL_CACHE.Coroutines.remove(autocombat)
        
        GLOBAL_CACHE.Map.Travel(GLOBAL_CACHE.Map.GetMapIDByName("Shing Jea Monastery"))
        yield from Routines.Yield.wait(1000)
        
    def ExitMonasteryOverlook002(self):
        exit_path: List[Tuple[float, float]] = [(-8418, 9301),(-8951, 9581),(-9709, 10009),(-10484, 10372),(-11332, 10190),
                                                (-12179, 10020),(-13030, 10122),(-13824, 10473),(-15000,11500)]
        
        if not (yield from self.follow_path(exit_path)):
            yield from self._stop_execution()
            return
        
    def TravelTsumeiVillage(self):
        path_to_tsumei: List[Tuple[float, float]] = [(20323, -8150),(19816, -8562),(19191, -9163),(18379, -9169),(17586, -8827),
                                                    (16846, -8378),(16031, -8414),(15318, -8902),(14598, -9388),(13879, -9872),
                                                    (13166, -10318),(12450, -10801),(11676, -11158),(10872, -11493),(10068, -11818),
                                                    (9217, -11718),(8381, -11475),(7548, -11234),(6706, -11073),(5933, -11466),
                                                    (5174, -11887),(4396, -12252),(3543, -12353),(2676, -12348),(1812, -12398),
                                                    (978, -12172),(144, -11957),(-716, -11988),(-1570, -12149),(-2420, -12325),
                                                    (-3268, -12482),(-4093, -12744),(-4669, -13016),(-4900, -13900)]
        
        if not (yield from self.follow_path(path_to_tsumei)):
            yield from self._stop_execution()
            return
        
    def ExitTsumeiVillage(self):
        exit_path: List[Tuple[float, float]] = [(-5289, -13950),(-5691, -14470),(-6344, -15031),(-7165, -15295),(-8011, -15455),
                                                (-8829, -15745),(-9676, -15940),(-10532, -16069),(-11170, -16560),(-11600,-17400)]
        
        if not (yield from self.follow_path(exit_path)):
            yield from self._stop_execution()
            return

    def TheThreatGrows(self):
        path_to_quest: List[Tuple[float, float]] = [(9687, 16174),(9884, 15533),(10191, 14723),(10528, 13927),(10791, 13105),
                                                    (10803, 12239),(10680, 11382),(10549, 10523),(10419, 9670),(10287, 8812),
                                                    (9922, 8028),(9700, 7250)]

        if not (yield from self.follow_path(path_to_quest)):
            yield from self._stop_execution()
            return
        
        autocombat = self.AutoCombat()
        GLOBAL_CACHE.Coroutines.append(autocombat)

        try:
            SISTER_TAI_MODEL_ID = 3316
            while True:
                sister_tai_agent_id = Routines.Agents.GetAgentIDByModelID(SISTER_TAI_MODEL_ID)
                
                if (not Routines.Checks.Agents.InDanger(aggro_area=Range.Spellcast)) and GLOBAL_CACHE.Agent.HasQuest(sister_tai_agent_id):
                    break
                yield from Routines.Yield.wait(1000)
                
        finally:  
            if autocombat in GLOBAL_CACHE.Coroutines:
                GLOBAL_CACHE.Coroutines.remove(autocombat)
                yield from Routines.Yield.wait(3000)
            
        sister_tai_agent_id = Routines.Agents.GetAgentIDByModelID(SISTER_TAI_MODEL_ID)
        x,y = GLOBAL_CACHE.Agent.GetXY(sister_tai_agent_id)
        ACCEPT_REWARD = 0x815407
        if not (yield from self.interact_with_agent((x, y), dialog_id=ACCEPT_REWARD)):
            yield from self._stop_execution()
            return
        
        TAKE_QUEST = 0x815501
        GLOBAL_CACHE.Player.SendDialog(TAKE_QUEST)
        yield from Routines.Yield.wait(500)
        
        GLOBAL_CACHE.Map.Travel(GLOBAL_CACHE.Map.GetMapIDByName("Shing Jea Monastery"))
        yield from Routines.Yield.wait(1000)
        
    def ExitToCourtyard002(self):
        yield from self._prepare_for_battle()
        
        path_to_courtyard: List[Tuple[float, float]] = [(-8861, 8508),(-8350, 8960),(-7558, 9307),(-6718, 9488),(-5849, 9469),
                                                        (-5036, 9469),(-4168, 9461),(-3980, 9460),(-3480,9460)]
             
        if not (yield from self.follow_path(path_to_courtyard)):
            return
        
    def FinishQuestsAndAdvanceToSaoshangTrail(self):
        path_to_togo: List[Tuple[float, float]] = [(-3281, 9442),(-2673, 9447),(-1790, 9441),(-904, 9434),(-159, 9174),]

        if not (yield from self.follow_path(path_to_togo)):
            return
        
        ACCEPT_QUEST = 0x815507
        if not (yield from self.interact_with_agent((-92, 9217), dialog_id=ACCEPT_QUEST)):
            return
        
        TAKE_QUEST = 0x815601
        if not (yield from self.interact_with_agent((-92, 9217), dialog_id=TAKE_QUEST)):
            return
        
        CONTINUE = 0x80000B
        if not (yield from self.interact_with_agent((538, 10125), dialog_id=CONTINUE)):
            return

    def TraverseSaoshangTrail(self):
        CONTINUE = 0x815604
        if not (yield from self.interact_with_agent((1254, 10875), dialog_id=CONTINUE)):
            return
        
        path_to_saoshang: List[Tuple[float, float]] = [(1185, 10837),(1574, 10532),(2364, 10186),(2918, 9910),(3647, 10072),
                                                        (4136, 10793),(4491, 11404),(4821, 12209),(5187, 12987),(5552, 13518),
                                                        (5821, 13790),(6608, 14098),(7653, 13843),(8063, 13118),(8290, 12662),
                                                        (8630, 11880),(8367, 11063),(8152, 10532),(8447, 10019),(9281, 10453),
                                                        (10074, 11029),(10471, 11219),(11275, 11554),(12030, 11856),(12628, 12208),
                                                        (12906, 12459),(13653, 12899),(14468, 13194),(15310, 13406),(16600, 13150)]

        autocombat = self.AutoCombat()
        GLOBAL_CACHE.Coroutines.append(autocombat)

        try:
            if not (yield from self.follow_path(path_to_saoshang, pause_on_danger=True)):
                return
        finally:  
            if autocombat in GLOBAL_CACHE.Coroutines:
                GLOBAL_CACHE.Coroutines.remove(autocombat)
                yield from Routines.Yield.wait(3000)
                
    def TakeRewardAndExitSeitungHarbor(self):
        TAKE_REWARD = 0x815607
        if not (yield from self.interact_with_agent((16368, 12011), dialog_id=TAKE_REWARD)):
            return
        
        yield from self._prepare_for_battle()
        
        path_to_exit: List[Tuple[float, float]] = [(16404, 12067),(16835, 12615),(17477, 13201),(18250, 13437),(19037, 13272),
                                                    (18744, 14040),(18289, 14775),(18566, 15587),(18790, 16400),(18097, 16895),
                                                    (17317, 17275),(16777,17540)]
        
        if not (yield from self.follow_path(path_to_exit)):
            return

        
    
    def GoToZenDaijunPart001(self):
        path_to_zendaijun: List[Tuple[float, float]] = [(10062, -12912),(9347, -12883),(8607, -12472),(8352, -11650),
                                                        (8219, -10799),(8430, -9975),(8944, -9277),(9687, -8848),(10551, -8773),
                                                        (11417, -8733),(12241, -8676),(12984, -8557),(13850, -8478),(14707, -8558),
                                                        (15090, -8652),(16063, -8316),(16619, -8324),(17361, -7878),(18011, -7306),
                                                        (18660, -6735),(19014, -6520),(19606, -6088),(19882, -5267),(20179, -4464),
                                                        (19923, -3871),(19720, -2907),(20225, -2204),(20901, -1664),(21436, -994),
                                                        (21699, -167 ),(22085, 836  ),(22598, 1205 ),(22951, 1457 ),(23616, 1587)]
        
        autocombat = self.AutoCombat()
        GLOBAL_CACHE.Coroutines.append(autocombat)

        try:
            if not (yield from self.follow_path(path_to_zendaijun, pause_on_danger=True)):
                return
        finally:  
            if autocombat in GLOBAL_CACHE.Coroutines:
                GLOBAL_CACHE.Coroutines.remove(autocombat)
                yield from Routines.Yield.wait(3000)
                
    def GoToZenDaijunPart002(self):
        path_to_zendaijun: List[Tuple[float, float]] = [
                                                    (-12066, -6836), (-11556, -6363), (-11383, -5516), (-11082, -4717), (-10654, -3960),
                                                    (-10146, -3268), (-9151, -2746), (-8527, -2650), (-7670, -2543), (-6808, -2449),
                                                    (-5933, -2379), (-5315, -2086), (-5045, -1296), (-5100, -468), (-4435, 82),
                                                    (-3819, 675), (-2648, 1246), (-1843, 1566), (-1013, 1696), (-226, 1328),
                                                    (604, 1100), (1436, 873), (2153, 480), (2808, -45), (3410, -663),
                                                    (3986, -1311), (4534, -1985), (5185, -2546), (5810, -2619), (5861, -3431),
                                                    (5671, -4255), (5397, -4727), (5473, -5397), (5848, -6176), (6495, -6723),
                                                    (7349, -6730), (8210, -6637), (8984, -6914), (9520, -7567), (9563, -8418),
                                                    (9285, -9239), (9211, -9753), (9372, -10605), (9537, -11454), (9941, -12223),
                                                    (10519, -12867), (11183, -13431), (11781, -14043), (11694, -14886), (11033, -15467),
                                                    (10997, -16286), (11289, -17079), (11918, -17681), (12605, -18199), (13350, -18643),
                                                    (14139, -19014), (14916, -19388), (15667, -19822), (16368, -20323), (16812, -21046),
                                                    (16784, -21887), (16571, -22196),
                                                ]

        
        autocombat = self.AutoCombat()
        GLOBAL_CACHE.Coroutines.append(autocombat)

        try:
            if not (yield from self.follow_path(path_to_zendaijun, pause_on_danger=True)):
                return
            
            CONTINUE = 0x80000B
            if not (yield from self.interact_with_agent((16489, -22213), dialog_id=CONTINUE)):
                return
            
        finally:  
            if autocombat in GLOBAL_CACHE.Coroutines:
                GLOBAL_CACHE.Coroutines.remove(autocombat)
                yield from Routines.Yield.wait(6000)
       
    def PrepareForZenDaijunMission(self):
        yield from self._prepare_for_battle()
        GLOBAL_CACHE.Map.EnterChallenge()
        yield from Routines.Yield.wait(6500)  # Wait for the map to load and the challenge to start
                 
    def ZenDaijunMission(self):
        autocombat = self.AutoCombat()
        GLOBAL_CACHE.Coroutines.append(autocombat)

        try:
            path_to_mission001: List[Tuple[float, float]] = [(16209, 11436),(15963, 11216),(15963, 11216),(15678, 10945),(14834, 10261),
                                                          (13806, 10172),(12878, 10531),(12185, 10801),(12185, 10801),(11665, 11386),
                                                    ]

            if not (yield from self.follow_path(path_to_mission001, pause_on_danger=True)):
                return
                    
            yield from Routines.Yield.wait(1000)
            
            if not (yield from self.interact_with_agent((11665, 11386))):
                return
            
            path_to_mission002: List[Tuple[float, float]] = [(11778, 11357),(11578, 10636),(10668, 10063),(9674, 9621),(9432, 8855),
                                                            (9990, 8394),(10546, 8083),(11333, 7338),(11203, 6624),(11291, 7054),
                                                            (11439, 6399),(10720, 6401),(11164, 6355),(11604, 5498),(11655, 4416),
                                                            (11503, 3382),(10571, 3564),(9797, 4083),(9288, 4538),(9049, 4791),
                                                            (8179, 4976),(7606, 3947),(7221, 3334),(6365, 2676),(5874, 2333),
                                                            (4996, 1462),(4754,1451)
                                                    ]

            if not (yield from self.follow_path(path_to_mission002, pause_on_danger=True)):
                return
            
            yield from Routines.Yield.wait(1000)
                    
            if not (yield from self.interact_with_agent((4754,1451))):
                return
            
            path_to_mission003: List[Tuple[float, float]] = [(4892, 1523),(5648, 1911),(5941, 1166),(5605, 132),(5170, -844),
                                                            (4163, -1129),(3101, -900),(2084, -523),(1260, 155),(554, 969),
                                                            (-131, 1797),(68, 2814),(568, 3807),(805, 4636),(468, 5633),
                                                            (-23, 6374),(-363, 6868),(-1040, 7713),(-1960, 8288),(-2880, 8726),
                                                            (-4059, 8273),(-4981, 8589),(-5457, 8807),(-6451, 8854),(-6986, 8796),
                                                            (-7930, 8726),(-8792, 8658),(-9888, 8290),(-9587, 7820),(-9354, 7509),
                                                            (-9808, 7193),(-11056, 5854),(-10904, 5217),(-11331, 5927),(-10923, 5216),
                                                            (-10554, 4751),(-10242, 4154),(-10915, 3609),(-11792, 2876),(-12651, 2898),
                                                            (-13285, 2865),(-14370, 2116),(-14454, 1373),(-14327, 905),(-14206, 1528),
                                                            (-14179, 913),(-13788, 147),(-13379, -197),(-13039, -375),(-12539, -326),
                                                            (-12327, 76),(-11758, 697),(-10961, 479),(-10308, 60),(-9882, -149),
                                                    ]

            if not (yield from self.follow_path(path_to_mission003, pause_on_danger=True)):
                return
            
            GLOBAL_CACHE.Party.Heroes.FlagAllHeroes(-8656, -712)
            yield from Routines.Yield.wait(3000)
            
            path_to_mission004: List[Tuple[float, float]] = [(-8625, -742),(-8298, -1270),(-8198, -1147),(-7851, -1458),]

            if not (yield from self.follow_path(path_to_mission004, pause_on_danger=True)):
                return
            
            while True:
                mapid = GLOBAL_CACHE.Map.GetMapID() #251
                if (Routines.Checks.Map.MapValid() and (mapid == GLOBAL_CACHE.Map.GetMapIDByName("Seitung Harbor"))):
                    break
                yield from Routines.Yield.wait(1000)
        finally:  
            if autocombat in GLOBAL_CACHE.Coroutines:
                GLOBAL_CACHE.Coroutines.remove(autocombat)
                yield from Routines.Yield.wait(3000)
                
    def EvaluateLevel10(self):
        level = GLOBAL_CACHE.Agent.GetLevel(GLOBAL_CACHE.Player.GetAgentID())
        if level < 10:
            zen_daijun_map_id = 213
            GLOBAL_CACHE.Map.Travel(zen_daijun_map_id)
            yield from Routines.Yield.wait(1000)
            self.FSM.jump_to_state_by_name("Wait for Zen Daijun Map Load")
            return
        
        TAKE_QUEST = 0x815D01
        if not (yield from self.interact_with_agent((16927, 9004), dialog_id=TAKE_QUEST)):
            return
        
        BOOK_PASSAGE = 0x81
        if not (yield from self.interact_with_agent((16927, 9004), dialog_id=BOOK_PASSAGE)):
            return
        
        I_AM_SURE = 0x84
        GLOBAL_CACHE.Player.SendDialog(I_AM_SURE)  # Accept the quest to book passage


main_FSM = FSM_Config()
selected_step = 0

#region GUI
def ShowMainWindow():
    global selected_step
    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize): 
        
        PyImGui.text("Current State: " + main_FSM.FSM.get_current_step_name())
        PyImGui.text("Script Running: " + str(main_FSM.script_running))
        
        main_FSM.draw_follow_path = PyImGui.checkbox("Draw Follow Path", main_FSM.draw_follow_path)

        
        PyImGui.text("Time Elapsed: " + str(main_FSM.run_timer.FormatElapsedTime("hh:mm:ss")))
        
        main_FSM.use_cupcakes = PyImGui.checkbox("Use Cupcakes", main_FSM.use_cupcakes)
        main_FSM.amount_of_cupcakes = PyImGui.slider_int("Amount of Cupcakes", main_FSM.amount_of_cupcakes, 1, 100)
        main_FSM.use_honeycombs = PyImGui.checkbox("Use Honeycombs", main_FSM.use_honeycombs)
        main_FSM.amount_of_honeycombs = PyImGui.slider_int("Amount of Honeycombs", main_FSM.amount_of_honeycombs, 1, 100)

        if PyImGui.button("Start"):
            main_FSM.script_running = True
            main_FSM.run_timer.Reset()
            main_FSM.FSM.restart()
            
        PyImGui.same_line(0,-1)
            
        if PyImGui.button("Stop"):
            main_FSM.script_running = False
            main_FSM.run_timer.Stop()
            main_FSM.FSM.stop()
            
        fsm_steps = main_FSM.FSM.get_state_names()
        selected_step = PyImGui.combo("FSM Steps",selected_step,  fsm_steps)
        if PyImGui.button("start at Step"):
            if selected_step < len(fsm_steps):
                main_FSM.script_running = True
                main_FSM.FSM.reset()
                main_FSM.run_timer.Reset()
                main_FSM.FSM.jump_to_state_by_name(fsm_steps[selected_step])
                
        others = GLOBAL_CACHE.Party.GetOthers()
        if others:
            for other in others:
                name = GLOBAL_CACHE.Agent.GetName(other)
                PyImGui.text(f"Other: {name} (ID: {other})")

    PyImGui.end()

    if main_FSM.draw_follow_path:
        main_FSM.draw_path(main_FSM.path_to_draw, (255, 0, 255, 255))

def main():
    global main_FSM
    try:
        ShowMainWindow()
        
        if main_FSM.FSM.finished:
            if main_FSM.script_running:
                main_FSM.script_running = False
                main_FSM.FSM.stop()

        if main_FSM.script_running:
            main_FSM.FSM.update()
    

    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

    
if __name__ == "__main__":
    main()