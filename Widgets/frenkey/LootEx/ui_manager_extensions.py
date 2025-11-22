from time import sleep
import PyUIManager
from Widgets.frenkey.LootEx import enum
from Py4GWCoreLib import UIManager
from Py4GWCoreLib.Py4GWcorelib import ConsoleLog


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
    def IsConfirmMaterialsWindowOpen() -> bool:
        salvage_lower_kit_id = UIManager.GetChildFrameID(140452905, [6,100])
        # salvage_lower_kit_yes_button_id = UIManager.GetChildFrameID(140452905, [
        #                                                             6, 100, 6])
        # salvage_lower_kit_no_button_id = UIManager.GetChildFrameID(140452905, [
        #                                                            6, 100, 4])

        return UIManagerExtensions.IsElementVisible(salvage_lower_kit_id)

    @staticmethod
    def ConfirmLesserSalvage():
        salvage_lower_kit_yes_button_id = UIManager.GetChildFrameID(140452905, [
                                                                    6, 100, 6])
        UIManager.FrameClick(salvage_lower_kit_yes_button_id)

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
        salvage_window_frame_id = UIManager.GetFrameIDByHash(684387150)
        # salvage_window_salvage_button_id = UIManager.GetChildFrameID(684387150, [2])
        # salvage_window_cancel_button_id = UIManager.GetChildFrameID(684387150, [1])

        return UIManagerExtensions.IsElementVisible(salvage_window_frame_id)

    @staticmethod
    def Test():
        salvage_window_frame_id = UIManager.GetFrameIDByHash(684387150)
        
        for i in range(1):
            for j in range(100):
                id = UIManager.GetChildFrameID(684387150, [5, i, j])
                
                if UIManagerExtensions.IsElementVisible(id):
                    frame_obj = PyUIManager.UIFrame(id)
                    frame_obj.get_context()
                    
                    ConsoleLog("LootEx", f"Found visible element with ID: {id} at ({i}, {j}) | template_type: {frame_obj.template_type}")
                    # UIManager.FrameClick(id)
                elif id > 0:
                    ConsoleLog("LootEx", f"Element with ID: {id} at ({i}, {j}) is not visible or does not exist.")
        
    @staticmethod
    def SelectSalvageOptionAndSalvage(option: enum.SalvageOption) -> bool:
        """
        Select a salvage option in the salvage window.

        Args:
            option (enum.SalvageOption): The salvage option to select.

        Returns:
            bool: True if the option was successfully selected, False otherwise.
        """
        options = UIManagerExtensions.GetSalvageOptions()

        if option in options:
            ConsoleLog("LootEx", f"Selecting salvage option: {option.name}")           
                                
            # UIManager.FrameClick(options[option])
            PyUIManager.UIManager.test_mouse_action(options[option], 7, 0, 0)              
            UIManagerExtensions.ConfirmSalvageOption()
            
            return True
        else:
            ConsoleLog("LootEx", f"Salvage option {option.name} not available.")
            UIManagerExtensions.CancelSalvageOption()

        return False

    @staticmethod
    def ConfirmSalvageOption() -> bool:
        salvage_window_salvage_button_id = UIManager.GetChildFrameID(684387150, [
                                                                     2])
        visible = UIManagerExtensions.IsElementVisible(
            salvage_window_salvage_button_id)

        if not visible:
            return False

        ConsoleLog("LootEx", f"Confirm salvage.")   
        UIManager.FrameClick(salvage_window_salvage_button_id)
        return True
    
    @staticmethod
    def CancelSalvageOption() -> bool:
        salvage_window_cancel_button_id = UIManager.GetChildFrameID(684387150, [1])
        visible = UIManagerExtensions.IsElementVisible(
            salvage_window_cancel_button_id)

        if not visible:
            return False

        ConsoleLog("LootEx", f"Cancel salvage.")   
        UIManager.FrameClick(salvage_window_cancel_button_id)
        return True

    @staticmethod
    def GetSalvageOptions() -> dict[enum.SalvageOption, int]:
        salvage_window_mod_one_id = UIManager.GetChildFrameID(684387150, [
                                                              5, 0])
        salvage_window_mod_two_id = UIManager.GetChildFrameID(684387150, [
                                                              5, 1])
        salvage_window_mod_three_id = UIManager.GetChildFrameID(684387150, [
                                                                5, 2])
        salvage_window_materials_id = UIManager.GetChildFrameID(684387150, [
                                                                5, 3])

        options: dict[enum.SalvageOption, int] = {}

        if UIManagerExtensions.IsElementVisible(salvage_window_mod_one_id):
            options[enum.SalvageOption.Prefix] = salvage_window_mod_one_id

        if UIManagerExtensions.IsElementVisible(salvage_window_mod_two_id):
            options[enum.SalvageOption.Suffix] = salvage_window_mod_two_id

        if UIManagerExtensions.IsElementVisible(salvage_window_mod_three_id):
            options[enum.SalvageOption.Inherent] = salvage_window_mod_three_id

        if UIManagerExtensions.IsElementVisible(salvage_window_materials_id):
            options[enum.SalvageOption.RareCraftingMaterials] = salvage_window_materials_id
            options[enum.SalvageOption.CraftingMaterials] = salvage_window_materials_id

        return options
