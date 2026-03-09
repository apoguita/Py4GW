import Py4GW
import PyUIManager

from Py4GWCoreLib.GWUI import GWUI
from Py4GWCoreLib.UIManager import UIManager
from Sources.frenkeyLib.ItemHandling.Rules.types import SalvageMode


class UIManagerExtensions:
    @staticmethod
    def IsElementVisible(frame_id: int) -> bool:
        """
        Check if a specific frame is open in the UI.

        Args:
            frame_id (int): The ID of the frame to check.

        Returns:
            bool: True if the frame is open, False otherwise.
        """
        return isinstance(frame_id, int) and frame_id > 0
    
    @staticmethod
    def GetSalvageOptions() -> dict[SalvageMode, int]:
        salvage_window_mod_one_id = UIManager.GetChildFrameID(684387150, [
                                                              5, 0])
        salvage_window_mod_two_id = UIManager.GetChildFrameID(684387150, [
                                                              5, 1])
        salvage_window_mod_three_id = UIManager.GetChildFrameID(684387150, [
                                                                5, 2])
        salvage_window_materials_id = UIManager.GetChildFrameID(684387150, [
                                                                5, 3])

        options: dict[SalvageMode, int] = {}

        if UIManagerExtensions.IsElementVisible(salvage_window_mod_one_id):
            options[SalvageMode.Prefix] = salvage_window_mod_one_id

        if UIManagerExtensions.IsElementVisible(salvage_window_mod_two_id):
            options[SalvageMode.Suffix] = salvage_window_mod_two_id

        if UIManagerExtensions.IsElementVisible(salvage_window_mod_three_id):
            options[SalvageMode.Inscription] = salvage_window_mod_three_id

        if UIManagerExtensions.IsElementVisible(salvage_window_materials_id):
            options[SalvageMode.RareCraftingMaterials] = salvage_window_materials_id

        return options
    
    @staticmethod
    def ConfirmSalvageOption() -> bool:
        salvage_window_salvage_button_id = UIManager.GetChildFrameID(684387150, [
                                                                     2])
        visible = UIManagerExtensions.IsElementVisible(
            salvage_window_salvage_button_id)

        if not visible:
            return False

        UIManager.FrameClick(salvage_window_salvage_button_id)
        return True
    
    @staticmethod
    def CancelSalvageOption() -> bool:
        salvage_window_cancel_button_id = UIManager.GetChildFrameID(684387150, [1])
        visible = UIManagerExtensions.IsElementVisible(
            salvage_window_cancel_button_id)

        if not visible:
            return False

        UIManager.FrameClick(salvage_window_cancel_button_id)
        return True
    
    @staticmethod
    def SelectSalvageOptionAndSalvage(option: SalvageMode) -> bool:
        """
        Select a salvage option in the salvage window.

        Args:
            option (SalvageMode): The salvage option to select.

        Returns:
            bool: True if the option was successfully selected, False otherwise.
        """
        options = UIManagerExtensions.GetSalvageOptions()

        if option in options:
            # UIManager.FrameClick(options[option])
            PyUIManager.UIManager.test_mouse_action(options[option], 8, 0, 0)              
            UIManagerExtensions.ConfirmSalvageOption()
            
            return True
        else:
            UIManagerExtensions.CancelSalvageOption()

        return False
    
    @staticmethod
    def SelectSalvageOption(option: SalvageMode) -> bool:
        """
        Select a salvage option in the salvage window.

        Args:
            option (SalvageMode): The salvage option to select.

        Returns:
            bool: True if the option was successfully selected, False otherwise.
        """
        options = UIManagerExtensions.GetSalvageOptions()

        if option in options:       
            # UIManager.FrameClick(options[option])
            PyUIManager.UIManager.test_mouse_action(options[option], 8, 0, 0)
            
            return True

        return False
    
    @staticmethod
    def IsUpgradeWindowOpen() -> bool:
        upgrade_window_frame_id = UIManager.GetFrameIDByHash(2612519688)
        return UIManagerExtensions.IsElementVisible(upgrade_window_frame_id)
    
    @staticmethod
    def IsMerchantWindowOpen() -> bool:
        merchant_window_frame_id = UIManager.GetFrameIDByHash(3613855137)
        # merchant_window_frame_inner_id = UIManager.GetChildFrameID(3613855137, [
        #                                                            0])
        # merchant_window_funds_id = UIManager.GetFrameIDByHash(3068881268)
        # merchant_window_buy_button_id = UIManager.GetFrameIDByHash(1532320307)

        return UIManagerExtensions.IsElementVisible(merchant_window_frame_id)
        
    @staticmethod
    def IsCollectorOpen() -> bool:        
        merchant_buy_button = 1532320307
        crafter_craft_button = 1517397806
        exchange_collector_button = UIManager.GetChildFrameID(3613855137, [
                                                                   0, 0, 6])
        sell_tab = UIManager.GetChildFrameID(3613855137, [0, 4294967294])

        return UIManagerExtensions.IsElementVisible(exchange_collector_button) and not UIManagerExtensions.IsElementVisible(sell_tab)
    
    @staticmethod
    def IsSkillTrainerOpen() -> bool:     
        display_type_button_id = UIManager.GetChildFrameID(1746895597,[3])
        sell_tab = UIManager.GetChildFrameID(3613855137, [0, 4294967294])

        return UIManagerExtensions.IsElementVisible(display_type_button_id) and not UIManagerExtensions.IsElementVisible(sell_tab)
    
    @staticmethod
    def IsCrafterOpen() -> bool:
        crafter_craft_button_id = UIManager.GetFrameIDByHash(1517397806)

        return UIManagerExtensions.IsElementVisible(crafter_craft_button_id)

    @staticmethod
    def IsConfirmLesserMaterialsWindowOpen() -> bool:
        # salvage_lower_kit_id = UIManager.GetChildFrameID(140452905, [6,110])
        salvage_lower_kit_yes_button_id = UIManager.GetChildFrameID(140452905, [6, 110, 6])
        # salvage_lower_kit_no_button_id = UIManager.GetChildFrameID(140452905, [
        #                                                            6, 110, 4])

        return UIManagerExtensions.IsElementVisible(salvage_lower_kit_yes_button_id)

    @staticmethod
    def ConfirmLesserSalvage():
        salvage_lower_kit_yes_button_id = UIManager.GetChildFrameID(140452905, [6, 110, 6])
        
        UIManager.FrameClick(salvage_lower_kit_yes_button_id)
        PyUIManager.UIManager.test_mouse_action(salvage_lower_kit_yes_button_id, 8, 0, 0) 

    @staticmethod
    def ConfirmModMaterialSalvage():
        salvage_with_mods_yes_button_id = UIManager.GetChildFrameID(684387150, [
                                                                    0, 6])
        UIManager.FrameClick(salvage_with_mods_yes_button_id)
        PyUIManager.UIManager.test_mouse_action(salvage_with_mods_yes_button_id, 8, 0, 0) 
        
    @staticmethod
    def ConfirmModMaterialSalvageVisible():
        salvage_with_mods_yes_button_id = UIManager.GetChildFrameID(684387150, [
                                                                    0, 6])
        return UIManagerExtensions.IsElementVisible(salvage_with_mods_yes_button_id)  
        
    @staticmethod
    def CancelLesserSalvage():
        salvage_lower_kit_no_button_id = UIManager.GetChildFrameID(140452905, [
                                                                   6, 100, 4])
        UIManager.FrameClick(salvage_lower_kit_no_button_id)
    
    @staticmethod
    def IsSalvageWindowOpen() -> bool:
        # salvage_window_frame_id = UIManager.GetFrameIDByHash(684387150)
        salvage_window_salvage_button_id = UIManager.GetChildFrameID(684387150, [2])
        # salvage_window_cancel_button_id = UIManager.GetChildFrameID(684387150, [1])

        return UIManagerExtensions.IsElementVisible(salvage_window_salvage_button_id)
    
    @staticmethod
    def IsSalvageWindowNoIdentifiedOpen() -> bool:
        # salvage_window_frame_id = UIManager.GetFrameIDByHash(140452905)
        salvage_window_salvage_button_id = UIManager.GetChildFrameID(140452905, [6, 111, 6])
        # salvage_window_cancel_button_id = UIManager.GetChildFrameID(140452905, [6,111,4])

        return UIManagerExtensions.IsElementVisible(salvage_window_salvage_button_id)
    
    @staticmethod
    def ConfirmSalvageWindowNoIdentified():
        salvage_window_salvage_button_id = UIManager.GetChildFrameID(140452905, [6, 111, 6])
        UIManager.FrameClick(salvage_window_salvage_button_id)
            
    
    @staticmethod
    def AnySalvageRelatedWindowOpen() -> bool:
        return UIManagerExtensions.IsSalvageWindowOpen() or UIManagerExtensions.IsConfirmLesserMaterialsWindowOpen() or UIManagerExtensions.ConfirmModMaterialSalvageVisible()
