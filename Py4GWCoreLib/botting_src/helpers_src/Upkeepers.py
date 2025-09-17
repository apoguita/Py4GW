from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingHelpers
    
from .decorators import _yield_step, _fsm_step
from typing import Any, Generator, TYPE_CHECKING, Tuple, List, Optional, Callable

#region UPKEEPERS
class _Upkeepers:
    def __init__(self, parent: "BottingHelpers"):
        self.parent = parent.parent
        self._config = parent._config
    
    def upkeep_auto_combat(self):
        from ...Routines import Routines
        while True:
            #print (f"autocombat is: {self._config.upkeep.auto_combat.is_active()}")
            if self._config.upkeep.auto_combat.is_active():
                yield from self._config.build_handler.ProcessSkillCasting()
            else:
                yield from Routines.Yield.wait(500)       
                
    def upkeep_hero_ai(self):
        from ....Py4GW_widget_manager import get_widget_handler
        from ...Routines import Routines
        handler = get_widget_handler()
        if self._config.upkeep.hero_ai.is_active() and not handler.is_widget_enabled("HeroAI"):
            handler.enable_widget("HeroAI")
        elif not self._config.upkeep.hero_ai.is_active() and handler.is_widget_enabled("HeroAI"):
            handler.disable_widget("HeroAI")
        yield from Routines.Yield.wait(500)
        
    def upkeep_auto_inventory_management(self):
        from ...py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
        from ...Routines import Routines
        inventory_handler = AutoInventoryHandler()
        #self._parent.inventory_handler.module_active = False
        if self._config.upkeep.auto_inventory_management.is_active() and not inventory_handler.module_active:
            inventory_handler.module_active = True
        elif not self._config.upkeep.auto_inventory_management.is_active() and inventory_handler.module_active:
            inventory_handler.module_active = False
            
        yield from Routines.Yield.wait(500)

    def upkeep_armor_of_salvation(self):    
        from ...Routines import Routines
        while True:
            if self._config.upkeep.armor_of_salvation.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_ArmorOfSalvation()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_essence_of_celerity(self):
        from ...Routines import Routines
        while True: 
            if self._config.upkeep.essence_of_celerity.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_EssenceOfCelerity()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_grail_of_might(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.grail_of_might.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_GrailOfMight()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_green_rock_candy(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.green_rock_candy.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_GreenRockCandy()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_red_rock_candy(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.red_rock_candy.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_RedRockCandy()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_blue_rock_candy(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.blue_rock_candy.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_BlueRockCandy()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_birthday_cupcake(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.birthday_cupcake.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_BirthdayCupcake()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_slice_of_pumpkin_pie(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.slice_of_pumpkin_pie.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_SliceOfPumpkinPie()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_bowl_of_skalefin_soup(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.bowl_of_skalefin_soup.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_BowlOfSkalefinSoup()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_candy_apple(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.candy_apple.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_CandyApple()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_candy_corn(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.candy_corn.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_CandyCorn()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_drake_kabob(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.drake_kabob.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_DrakeKabob()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_golden_egg(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.golden_egg.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_GoldenEgg()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_pahnai_salad(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.pahnai_salad.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_PahnaiSalad()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_war_supplies(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.war_supplies.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_WarSupplies()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_alcohol(self):
        import PyEffects
        from ...Routines import Routines
        target_alc_level = 2
        disable_drunk_effects = False
        if disable_drunk_effects:
            PyEffects.PyEffects.ApplyDrunkEffect(0, 0)
        while True:
            if self._config.upkeep.alcohol.is_active():
                
                yield from Routines.Yield.Upkeepers.Upkeep_Alcohol(target_alc_level, disable_drunk_effects)
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_city_speed(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.city_speed.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_City_Speed()
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_morale(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.honeycomb.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_Morale(110)
            elif (self._config.upkeep.four_leaf_clover.is_active()):
                yield from Routines.Yield.Upkeepers.Upkeep_Morale(100)
            elif self._config.upkeep.morale.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_Morale(110)
            else:
                yield from Routines.Yield.wait(500)

    def upkeep_imp(self):
        from ...Routines import Routines
        while True:
            if self._config.upkeep.imp.is_active():
                yield from Routines.Yield.Upkeepers.Upkeep_Imp()
            else:
                yield from Routines.Yield.wait(500)
    