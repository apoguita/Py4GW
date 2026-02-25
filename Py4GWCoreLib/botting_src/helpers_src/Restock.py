from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step, _fsm_step
from typing import Any, Generator, TYPE_CHECKING

from ...enums_src.Model_enums import ModelID

#region RESTOCK
class _Restock:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
        self._Events = parent.Events
    
    def _restock_item(self, model_id: int, desired_quantity: int) -> Generator[Any, Any, bool]:
        from ...Routines import Routines
        from ...Py4GWcorelib import ConsoleLog
        result = yield from Routines.Yield.Items.RestockItems(model_id, desired_quantity)
        if not result:
            yield
            return False
        yield
        return True
    
    @_yield_step(label="RestockBirthdayCupcake", counter_key="RESTOCK_BIRTHDAY_CUPCAKE")   
    def restock_birthday_cupcake (self):
        if self._config.upkeep.birthday_cupcake.is_active():
            qty = self._config.upkeep.birthday_cupcake.get("restock_quantity")
            yield from self._restock_item(ModelID.Birthday_Cupcake.value, qty)

    @_yield_step(label="RestockBCandyApple", counter_key="RESTOCK_CANDY_APPLE")   
    def restock_candy_apple (self):
        if self._config.upkeep.candy_apple.is_active():
            qty = self._config.upkeep.candy_apple.get("restock_quantity")
            yield from self._restock_item(ModelID.Candy_Apple.value, qty)

    @_yield_step(label="RestockHoneycomb", counter_key="RESTOCK_HONEYCOMB")
    def restock_honeycomb(self):
        if (self._config.upkeep.honeycomb.is_active() or
            self._config.upkeep.morale.is_active()):
            qty = self._config.upkeep.honeycomb.get("restock_quantity")
            yield from self._restock_item(ModelID.Honeycomb.value, qty)
             

    @_yield_step(label="RestockWarSupplies", counter_key="RESTOCK_WAR_SUPPLIES")
    def restock_war_supplies(self):
        if self._config.upkeep.war_supplies.is_active():
            qty = self._config.upkeep.war_supplies.get("restock_quantity")
            yield from self._restock_item(ModelID.War_Supplies.value, qty)

    @_yield_step(label="RestockEssenceOfCelerity", counter_key="RESTOCK_ESSENCE_OF_CELERITY")
    def restock_essence_of_celerity(self):
        if self._config.upkeep.essence_of_celerity.is_active():
            qty = self._config.upkeep.essence_of_celerity.get("restock_quantity")
            yield from self._restock_item(ModelID.Essence_Of_Celerity.value, qty)

    @_yield_step(label="RestockGrailOfMight", counter_key="RESTOCK_GRAIL_OF_MIGHT")
    def restock_grail_of_might(self):
        if self._config.upkeep.grail_of_might.is_active():
            qty = self._config.upkeep.grail_of_might.get("restock_quantity")
            yield from self._restock_item(ModelID.Grail_Of_Might.value, qty)

    @_yield_step(label="RestockArmorOfSalvation", counter_key="RESTOCK_ARMOR_OF_SALVATION")
    def restock_armor_of_salvation(self):
        if self._config.upkeep.armor_of_salvation.is_active():
            qty = self._config.upkeep.armor_of_salvation.get("restock_quantity")
            yield from self._restock_item(ModelID.Armor_Of_Salvation.value, qty)

    @_yield_step(label="RestockGoldenEgg", counter_key="RESTOCK_GOLDEN_EGG")
    def restock_golden_egg(self):
        if self._config.upkeep.golden_egg.is_active():
            qty = self._config.upkeep.golden_egg.get("restock_quantity")
            yield from self._restock_item(ModelID.Golden_Egg.value, qty)

    @_yield_step(label="RestockCandyCorn", counter_key="RESTOCK_CANDY_CORN")
    def restock_candy_corn(self):
        if self._config.upkeep.candy_corn.is_active():
            qty = self._config.upkeep.candy_corn.get("restock_quantity")
            yield from self._restock_item(ModelID.Candy_Corn.value, qty)

    @_yield_step(label="RestockSliceOfPumpkinPie", counter_key="RESTOCK_SLICE_OF_PUMPKIN_PIE")
    def restock_slice_of_pumpkin_pie(self):
        if self._config.upkeep.slice_of_pumpkin_pie.is_active():
            qty = self._config.upkeep.slice_of_pumpkin_pie.get("restock_quantity")
            yield from self._restock_item(ModelID.Slice_Of_Pumpkin_Pie.value, qty)

    @_yield_step(label="RestockDrakeKabob", counter_key="RESTOCK_DRAKE_KABOB")
    def restock_drake_kabob(self):
        if self._config.upkeep.drake_kabob.is_active():
            qty = self._config.upkeep.drake_kabob.get("restock_quantity")
            yield from self._restock_item(ModelID.Drake_Kabob.value, qty)

    @_yield_step(label="RestockBowlOfSkalefinSoup", counter_key="RESTOCK_BOWL_OF_SKALEFIN_SOUP")
    def restock_bowl_of_skalefin_soup(self):
        if self._config.upkeep.bowl_of_skalefin_soup.is_active():
            qty = self._config.upkeep.bowl_of_skalefin_soup.get("restock_quantity")
            yield from self._restock_item(ModelID.Bowl_Of_Skalefin_Soup.value, qty)

    @_yield_step(label="RestockPahnaiSalad", counter_key="RESTOCK_PAHNAI_SALAD")
    def restock_pahnai_salad(self):
        if self._config.upkeep.pahnai_salad.is_active():
            qty = self._config.upkeep.pahnai_salad.get("restock_quantity")
            yield from self._restock_item(ModelID.Pahnai_Salad.value, qty)