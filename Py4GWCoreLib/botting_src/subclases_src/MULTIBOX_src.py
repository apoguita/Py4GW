#region STATES
from typing import TYPE_CHECKING, Callable, Optional, Tuple
from Py4GWCoreLib import Color
import PyImGui
from Py4GW_widget_manager import get_widget_handler

if TYPE_CHECKING:
    from Py4GWCoreLib.botting_src.helpers import BottingClass

from ...enums import ModelID

#region Multibox
class _MULTIBOX:
    def __init__(self, parent: "BottingClass"):
        self.parent = parent
        self._config = parent.config
        self._helpers = parent.helpers
        
    def ResignParty(self):
        self._helpers.Multibox.resign_party()

    def DonateFaction(self):
        self._helpers.Multibox.donate_faction()
        
    def SendDialogToTarget(self, dialog_id: int):
        self._helpers.Multibox.send_dialog_to_target(dialog_id)
        
    def PixelStack(self):
        self._helpers.Multibox.pixel_stack()
        
    def InteractWithTarget(self):
        self._helpers.Multibox.interact_with_target()
        
    def UseConsumable(self, item_id, skill_id):
        self._helpers.Multibox.use_consumable((item_id, skill_id, 0, 0))
        
    def UseEssenceOfCelerity(self):
        from ...GlobalCache import GLOBAL_CACHE
        self._helpers.Multibox.use_consumable((ModelID.Essence_Of_Celerity.value, 
                                               GLOBAL_CACHE.Skill.GetID("Essence_of_Celerity_item_effect"), 0, 0))
        
    def UseGrailOfMight(self):
        from ...GlobalCache import GLOBAL_CACHE
        self._helpers.Multibox.use_consumable((ModelID.Grail_Of_Might.value, 
                                               GLOBAL_CACHE.Skill.GetID("Grail_of_Might_item_effect"), 0, 0))
        
    def UseArmorOfSalvation(self):
        from ...GlobalCache import GLOBAL_CACHE
        self._helpers.Multibox.use_consumable((ModelID.Armor_Of_Salvation.value, 
                                               GLOBAL_CACHE.Skill.GetID("Armor_of_Salvation_item_effect"), 0, 0))
    
    def UseBirthdayCupcake(self):
        from ...GlobalCache import GLOBAL_CACHE
        self._helpers.Multibox.use_consumable((ModelID.Birthday_Cupcake.value, 
                                               GLOBAL_CACHE.Skill.GetID("Birthday_Cupcake_skill"), 0, 0))
        
    def UseGoldenEgg(self):
        from ...GlobalCache import GLOBAL_CACHE
        self._helpers.Multibox.use_consumable((ModelID.Golden_Egg.value, 
                                               GLOBAL_CACHE.Skill.GetID("Golden_Egg_skill"), 0, 0))
        
    def UseCandyCorn(self):
        from ...GlobalCache import GLOBAL_CACHE
        self._helpers.Multibox.use_consumable((ModelID.Candy_Corn.value, 
                                               GLOBAL_CACHE.Skill.GetID("Candy_Corn_skill"), 0, 0))
        
    def UseCandyApple(self):
        from ...GlobalCache import GLOBAL_CACHE
        self._helpers.Multibox.use_consumable((ModelID.Candy_Apple.value, 
                                               GLOBAL_CACHE.Skill.GetID("Candy_Apple_skill"), 0, 0))
        
    def UsePumpkinPie(self):
        from ...GlobalCache import GLOBAL_CACHE
        self._helpers.Multibox.use_consumable((ModelID.Slice_Of_Pumpkin_Pie.value, 
                                               GLOBAL_CACHE.Skill.GetID("Pie_Induced_Ecstasy"), 0, 0))
        
    def UseDrakeKabob(self):
        from ...GlobalCache import GLOBAL_CACHE
        self._helpers.Multibox.use_consumable((ModelID.Drake_Kabob.value, 
                                               GLOBAL_CACHE.Skill.GetID("Drake_Skin"), 0, 0))
        
    def UseBowlOfSkalefinSoup(self):
        from ...GlobalCache import GLOBAL_CACHE
        self._helpers.Multibox.use_consumable((ModelID.Bowl_Of_Skalefin_Soup.value, 
                                               GLOBAL_CACHE.Skill.GetID("Skale_Vigor"), 0, 0))
        
    def UsePahnaiSalad(self):
        from ...GlobalCache import GLOBAL_CACHE
        self._helpers.Multibox.use_consumable((ModelID.Pahnai_Salad.value, 
                                               GLOBAL_CACHE.Skill.GetID("Pahnai_Salad_item_effect"), 0, 0))
        
    def UseWarSupplies(self):
        from ...GlobalCache import GLOBAL_CACHE
        self._helpers.Multibox.use_consumable((ModelID.War_Supplies.value, GLOBAL_CACHE.Skill.GetID("Well_Supplied"), 0, 0))
   
   
    def UseConset(self):
        self.UseEssenceOfCelerity()
        self.UseGrailOfMight()
        self.UseArmorOfSalvation()

    def UsePcons(self):
        self.UseBirthdayCupcake()
        self.UseGoldenEgg()
        self.UseCandyCorn()
        self.UseCandyApple()
        self.UsePumpkinPie()
        self.UseDrakeKabob()
        self.UseBowlOfSkalefinSoup()
        self.UsePahnaiSalad()
        self.UseWarSupplies()

    def UseAllConsumables(self):
        self.UseEssenceOfCelerity()
        self.UseGrailOfMight()
        self.UseArmorOfSalvation()
        self.UseBirthdayCupcake()
        self.UseGoldenEgg()
        self.UseCandyCorn()
        self.UseCandyApple()
        self.UsePumpkinPie()
        self.UseDrakeKabob()
        self.UseBowlOfSkalefinSoup()
        self.UsePahnaiSalad()
        self.UseWarSupplies()

    def RestockAllPcons(self, quantity: int = 250):
        self._helpers.Multibox.restock_all_pcons(quantity)

    def RestockConset(self, quantity: int = 250):
        self._helpers.Multibox.restock_conset(quantity)

    def RestockResurrectionScroll(self, quantity: int = 250):
        self._helpers.Multibox.restock_resurrection_scroll(quantity)

    def EnableWidget(self, widget_name: str):
        self._helpers.Multibox.enable_widget(widget_name)

    def DisableWidget(self, widget_name: str):
        self._helpers.Multibox.disable_widget(widget_name)

    def ApplyWidgetPolicy(
        self,
        enable_widgets: tuple[str, ...] = (),
        disable_widgets: tuple[str, ...] = (),
        apply_local: bool = True,
    ):
        """Apply widget enable/disable policy locally and via multibox messaging."""
        if apply_local:
            widget_handler = get_widget_handler()
            for widget_name in enable_widgets:
                if not widget_handler.is_widget_enabled(widget_name):
                    widget_handler.enable_widget(widget_name)
            for widget_name in disable_widgets:
                if widget_handler.is_widget_enabled(widget_name):
                    widget_handler.disable_widget(widget_name)

        for widget_name in enable_widgets:
            self.EnableWidget(widget_name)
        for widget_name in disable_widgets:
            self.DisableWidget(widget_name)

    def SummonAllAccounts(self):
        self._helpers.Multibox.summon_all_accounts()
        
    def SummonAccount(self, account_email: str):
        self._helpers.Multibox.summon_account_by_email(account_email)
        
    def InviteAllAccounts(self):
        self._helpers.Multibox.invite_all_accounts()
        
    def InviteAccount(self, account_email: str):
        self._helpers.Multibox.invite_account_by_email(account_email)
        
    def KickAllAccounts(self):
        self._helpers.Multibox.kick_all_accounts()

    def KickAccount(self, account_email: str):
        self._helpers.Multibox.kick_account_by_email(account_email)

    def LeavePartyOnAllAccounts(self):
        self._helpers.Multibox.leave_party_on_all_accounts()

    def AbandonQuest(self, quest_id: int):
        """Abandon a quest for the leader and broadcast to all other accounts via multibox messaging."""
        self._helpers.Multibox.abandon_quest(quest_id)

#endregion
