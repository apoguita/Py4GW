from Py4GWCoreLib import FSM
from .FSMHelpers import _FSM_Helpers


#region FSM
class YAVB_FSM:
    def __init__(self, parent):
        self.parent = parent
        self.FSM:FSM = parent.FSM
        self.FSM_Helpers:_FSM_Helpers = parent.FSM_Helpers

            
    def _initialize_fsm(self):
        self.FSM.AddState(name="Deactivate Inventory Handler",execute_fn=self.FSM_Helpers.DeactivateInventoryHandler,)
        self.FSM.AddState(name = "Deactivate Hero AI",execute_fn=self.FSM_Helpers.DeactivateHeroAI)
        self.FSM.AddYieldRoutineStep(name = "Travel to Longeyes Ledge",coroutine_fn=self.FSM_Helpers.TravelToLongeyesLedge)
        self.FSM.AddYieldRoutineStep(name = "Load SkillBar",coroutine_fn=self.FSM_Helpers.LoadSkillBar,)
        self.FSM.AddYieldRoutineStep(name = "Inventory Handling",coroutine_fn=self.FSM_Helpers.InventoryHandling,)
        self.FSM.AddYieldRoutineStep(name = "Withdraw Cupcake",coroutine_fn=self.FSM_Helpers.WitdrawBirthdayCupcake)
        self.FSM.AddYieldRoutineStep(name = "Withdraw Pumpkin Cookie",coroutine_fn=self.FSM_Helpers.WitdrawPumpkinCookie)
        self.FSM.AddYieldRoutineStep(name = "Set Hard Mode",coroutine_fn=self.FSM_Helpers.SetHardMode)
        self.FSM.AddYieldRoutineStep(name = "Leave Outpost",coroutine_fn=self.FSM_Helpers.LeaveOutpost,)
        self.FSM.AddYieldRoutineStep(name = "Wait for Bjora Marches Map Load",coroutine_fn=self.FSM_Helpers.WaitforBjoraMarchesMapLoad)
        self.FSM.AddState(name = "Add Bjora Marches Stuck Coroutine",
                          execute_fn=self.FSM_Helpers.AddBjoraMarchesStuckCoroutine,
                          run_once=True,
                          transition_delay_ms=100)
        self.FSM.AddYieldRoutineStep(name = "Set Norn Title",coroutine_fn=self.FSM_Helpers.SetNornTitle)
        self.FSM.AddState(name = "Use Cupcake",
                          execute_fn=self.FSM_Helpers.UseCupcake,
                          transition_delay_ms=100)
        self.FSM.AddYieldRoutineStep(name = "Traverse Bjora Marches", coroutine_fn=self.FSM_Helpers.TraverseBjoraMarches)
        self.FSM.AddYieldRoutineStep(name = "Wait for Jaga Moraine Map Load", coroutine_fn=self.FSM_Helpers.WaitforJagaMoraineMapLoad)
        self.FSM.AddState(name = "Remove Bjora Marches Stuck Coroutine",
                          execute_fn=self.FSM_Helpers.RemoveBjoraMarchesStuckCoroutine,
                          run_once=True,
                          transition_delay_ms=100)
        self.FSM.AddState(name = "Add Skill Casting Coroutine",execute_fn=self.FSM_Helpers.AddSkillCastingCoroutine)
        self.FSM.AddYieldRoutineStep(name = "Take Bounty", coroutine_fn=self.FSM_Helpers.TakeBounty)
        self.FSM.AddYieldRoutineStep(name = "Farming Route 1", coroutine_fn=self.FSM_Helpers.FarmingRoute1)
        self.FSM.AddYieldRoutineStep(name = "Wait for lef aggro ball", coroutine_fn=self.FSM_Helpers.WaitforLeftAggroBall)
        self.FSM.AddYieldRoutineStep(name = "Farming Route 2", coroutine_fn=self.FSM_Helpers.FarmingRoute2)
        self.FSM.AddYieldRoutineStep(name = "Wait for right aggro ball", coroutine_fn=self.FSM_Helpers.WaitforRightAggroBall)
        self.FSM.AddYieldRoutineStep(name = "Farming Route to Kill Spot", coroutine_fn=self.FSM_Helpers.FarmingRoutetoKillSpot)
        self.FSM.AddYieldRoutineStep(name = "Kill Enemies", coroutine_fn=self.FSM_Helpers.KillEnemies)
        self.FSM.AddState(name = "Remove Skill Casting Coroutine",execute_fn=self.FSM_Helpers.RemoveSkillCastingCoroutine)
        self.FSM.AddYieldRoutineStep(name = "Loot Items", coroutine_fn=self.FSM_Helpers.LootItems)
        self.FSM.AddYieldRoutineStep(name = "Identify and Salvage Items", coroutine_fn=self.FSM_Helpers.IdentifyAndSalvageItems)
        self.FSM.AddYieldRoutineStep(name = "Inventory Check", coroutine_fn=self.FSM_Helpers.CheckInventory)
        self.FSM.AddYieldRoutineStep(name = "Exit Jaga Moraine", coroutine_fn=self.FSM_Helpers.ExitJagaMoraine)
        self.FSM.AddYieldRoutineStep(name = "Wait for Bjora Marches return Map Load", coroutine_fn=self.FSM_Helpers.WaitforBjoraMarches_returnMapLoad)
        self.FSM.AddYieldRoutineStep(name = "Return to Jaga Moraine", coroutine_fn=self.FSM_Helpers.ReturnToJagaMoraine)
        

#endregion