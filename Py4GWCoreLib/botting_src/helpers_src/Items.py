from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step, _fsm_step
from typing import Any, Generator, TYPE_CHECKING, Tuple, List, Optional, Callable

from ...Py4GWcorelib import ConsoleLog, Console
from ...enums_src.Model_enums import ModelID

#region ITEMS
class _Items:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
        self._Events = parent.Events


    @_yield_step(label="WithdrawItems", counter_key="WITHDRAW_ITEMS")
    def withdraw(self, model_id:int, quantity:int) -> Generator[Any, Any, bool]:
        from ...Routines import Routines
        from ...Py4GWcorelib import ConsoleLog
        import Py4GW
        result = yield from Routines.Yield.Items.WithdrawItems(model_id, quantity)
        if not result:
            ConsoleLog("WithdrawItems", f"Failed to withdraw ({quantity}) items from storage.", Py4GW.Console.MessageType.Error)
            self._Events.on_unmanaged_fail()
            return False

        return True

    @_yield_step(label="CraftItem", counter_key="CRAFT_ITEM")
    def craft(self, output_model_id: int, count: int,
                trade_model_ids: list[int], quantity_list: list[int]):
        from ...Routines import Routines
        from ...Py4GWcorelib import ConsoleLog
        import Py4GW
        result = yield from Routines.Yield.Items.CraftItem(output_model_id=output_model_id,
                                                            count=count,
                                                            trade_model_ids=trade_model_ids,
                                                            quantity_list=quantity_list)
        if not result:
            ConsoleLog("CraftItem", f"Failed to craft item ({output_model_id}).", Py4GW.Console.MessageType.Error)
            self._Events.on_unmanaged_fail()
            return False

        return True

    def _equip(self, model_id: int):
        from ...Routines import Routines
        import Py4GW
        from ...Py4GWcorelib import ConsoleLog
        result = yield from Routines.Yield.Items.EquipItem(model_id)
        if not result:
            ConsoleLog("EquipItem", f"Failed to equip item ({model_id}).", Py4GW.Console.MessageType.Error)
            self._Events.on_unmanaged_fail()
            return False

        return True

    @_yield_step(label="EquipItem", counter_key="EQUIP_ITEM")
    def equip(self, model_id: int):
        return (yield from self._equip(model_id))
    
        
    @_yield_step(label="DestroyItem", counter_key="DESTROY_ITEM")
    def destroy(self, model_id: int) -> Generator[Any, Any, bool]:
        from ...Routines import Routines
        from ...Py4GWcorelib import ConsoleLog
        import Py4GW
        result = yield from Routines.Yield.Items.DestroyItem(model_id)
        if not result:
            ConsoleLog("DestroyItem", f"Failed to destroy item ({model_id}).", Py4GW.Console.MessageType.Error)
            self._Events.on_unmanaged_fail()
            return False

        return True
    
    def _destroy_bonus_items(self, 
                            exclude_list: List[int] = [ModelID.Igneous_Summoning_Stone.value, 
                                                        ModelID.Bonus_Nevermore_Flatbow.value]
                            ) -> Generator[Any, Any, None]:
        from ...Routines import Routines
        bonus_items = [ModelID.Bonus_Luminescent_Scepter.value,
                        ModelID.Bonus_Nevermore_Flatbow.value,
                        ModelID.Bonus_Rhinos_Charge.value,
                        ModelID.Bonus_Serrated_Shield.value,
                        ModelID.Bonus_Soul_Shrieker.value,
                        ModelID.Bonus_Tigers_Roar.value,
                        ModelID.Bonus_Wolfs_Favor.value,
                        ModelID.Igneous_Summoning_Stone.value
                        ]
        
        #remove excluded items from the list
        for model in exclude_list:
            if model in bonus_items:
                bonus_items.remove(model)

        for model in bonus_items:
            ConsoleLog("DestroyBonusItems", f"Destroying bonus item ({model}).", Console.MessageType.Info, log=False)
            result = yield from Routines.Yield.Items.DestroyItem(model)
        

    @_yield_step(label="DestroyBonusItems", counter_key="DESTROY_BONUS_ITEMS")
    def destroy_bonus_items(self, 
                            exclude_list: List[int] = [ModelID.Igneous_Summoning_Stone.value, 
                                                        ModelID.Bonus_Nevermore_Flatbow.value]
                            ) -> Generator[Any, Any, None]:
        yield from self._destroy_bonus_items(exclude_list)
        

        
    def _spawn_bonus_items(self):
        from ...Routines import Routines
        yield from Routines.Yield.Items.SpawnBonusItems()
        
    @_yield_step(label="SpawnBonusItems", counter_key="SPAWN_BONUS")
    def spawn_bonus_items(self):
        yield from self._spawn_bonus_items()
        
    @_yield_step(label="AutoIdentifyItems", counter_key="AUTO_IDENTIFY")
    def auto_identify_items(self) -> Generator[Any, Any, None]:
        from ...py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
        inventory_handler = AutoInventoryHandler()
        current_state =  inventory_handler.module_active
        inventory_handler.module_active = False
        yield from inventory_handler.IdentifyItems()
        inventory_handler.module_active = current_state
        
    @_yield_step(label="AutoSalvageItems", counter_key="AUTO_SALVAGE")
    def auto_salvage_items(self) -> Generator[Any, Any, None]:
        from ...py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
        inventory_handler = AutoInventoryHandler()
        current_state =  inventory_handler.module_active
        inventory_handler.module_active = False
        yield from inventory_handler.SalvageItems()
        inventory_handler.module_active = current_state
        
    @_yield_step(label="AutodepositItems", counter_key="AUTO_DEPOSIT")
    def auto_deposit_items(self) -> Generator[Any, Any, None]:
        from ...py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
        inventory_handler = AutoInventoryHandler()
        current_state =  inventory_handler.module_active
        inventory_handler.module_active = False
        yield from inventory_handler.DepositItemsAuto()
        inventory_handler.module_active = current_state
        
    @_yield_step(label="AutodepositGold", counter_key="AUTO_DEPOSIT_GOLD")
    def auto_deposit_gold(self) -> Generator[Any, Any, None]:
        from ...py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
        from ...Routines import Routines
        inventory_handler = AutoInventoryHandler()
        current_state =  inventory_handler.module_active
        inventory_handler.module_active = False
        yield from Routines.Yield.Items.DepositGold(inventory_handler.keep_gold, log =False)
        inventory_handler.module_active = current_state
        
    @_yield_step(label="AutoIDAndSalvage", counter_key="AUTO_ID_AND_SALVAGE")
    def auto_id_and_salvage(self) -> Generator[Any, Any, None]:
        from ...py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
        inventory_handler = AutoInventoryHandler()
        current_state =  inventory_handler.module_active
        inventory_handler.module_active = False
        yield from inventory_handler.IdentifyItems()
        yield from inventory_handler.SalvageItems()
        inventory_handler.module_active = current_state
        
    @_yield_step(label="AutoIDAndSalvageAndDeposit", counter_key="AUTO_ID_SALVAGE_DEPOSIT")
    def auto_id_and_salvage_and_deposit(self) -> Generator[Any, Any, None]:
        from ...py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
        from ...Routines import Routines
        inventory_handler = AutoInventoryHandler()
        current_state =  inventory_handler.module_active
        inventory_handler.module_active = False
        yield from inventory_handler.IdentifyItems()
        yield from inventory_handler.SalvageItems()
        yield from inventory_handler.DepositItemsAuto()
        yield from Routines.Yield.Items.DepositGold(inventory_handler.keep_gold, log =False)
        inventory_handler.module_active = current_state
        
    