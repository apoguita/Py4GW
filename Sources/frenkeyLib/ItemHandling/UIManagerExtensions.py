from typing import NamedTuple, Optional

import Py4GW
import PyUIManager

from Py4GWCoreLib.Inventory import Inventory
from Py4GWCoreLib.GWUI import GWUI
from Py4GWCoreLib.UIManager import UIManager
from Py4GWCoreLib.enums_src.Item_enums import SalvageMode
from Py4GWCoreLib.py4gwcorelib_src.FrameCache import frame_cache

FramePath = NamedTuple("FramePath", [("FrameID", int), ("child_indices", list[int])])

class UIManagerExtensions:
    SALVAGE_OPTIONS_FRAME = FramePath(684387150, [])
        
    CANCEL_SALVAGE_OPTIONS_FRAME = FramePath(684387150, [1])
    CONFIRM_SALVAGE_OPTIONS_FRAME = FramePath(684387150, [2])
    
    OPTIONS_SALVAGE_OPTIONS_FRAME = FramePath(684387150, [5])
    OPTION_PREFIX_SALVAGE_OPTIONS_FRAME = FramePath(684387150, [5, 0])
    OPTION_SUFFIX_SALVAGE_OPTIONS_FRAME = FramePath(684387150, [5, 1])
    OPTION_INSCRIPTION_SALVAGE_OPTIONS_FRAME = FramePath(684387150, [5, 2])
    OPTION_MATERIALS_SALVAGE_OPTIONS_FRAME = FramePath(684387150, [5, 3])
    
    MATERIAL_OPTION_CONFIRMATION_FRAME = FramePath(684387150, [0])
    CANCEL_MATERIAL_OPTION_CONFIRMATION_FRAME = FramePath(684387150, [0, 4])
    CONFIRM_MATERIAL_OPTION_CONFIRMATION_FRAME = FramePath(684387150, [0, 6])
    
    LESSER_SALVAGE_FRAME = FramePath(140452905, [6, 111])
    CANCEL_LESSER_SALVAGE_FRAME = FramePath(140452905, [6, 111, 4])
    CONFIRM_LESSER_SALVAGE_FRAME = FramePath(140452905, [6, 111, 6])
    
    EXPERT_SALVAGE_UNIDENTIFIED_FRAME = FramePath(140452905, [6, 112])
    CANCEL_EXPERT_SALVAGE_UNIDENTIFIED_FRAME = FramePath(140452905, [6, 112, 4])
    CONFIRM_EXPERT_SALVAGE_UNIDENTIFIED_FRAME = FramePath(140452905, [6, 112, 6])
    
    UPGRADE_WINDOW_FRAME = FramePath(2612519688, [])
    
    MERCHANT_WINDOW_FRAME = FramePath(3613855137, [])
    
    COLLECTOR_WINDOW_FRAME = FramePath(3613855137, [0, 0, 6])
    
    SKILL_TRAINER_WINDOW_FRAME = FramePath(1746895597, [3])
    
    CRAFTER_WINDOW_FRAME = FramePath(1517397806, [])
    
    @staticmethod
    def GetFrame(frame_path: FramePath) -> int:
        if not frame_path.child_indices:
            return UIManager.GetFrameIDByHash(frame_path.FrameID)
        
        return UIManager.GetChildFrameID(frame_path.FrameID, frame_path.child_indices)
    
    @staticmethod
    @frame_cache(category="UIManagerExtensions", source_lib="FrameExists")
    def FrameExists(frame_id: int) -> bool:
        return isinstance(frame_id, int) and frame_id > 0 and UIManager.FrameExists(frame_id)

    @staticmethod
    def ClickFrame(frame_id: int) -> bool:
        if not UIManagerExtensions.FrameExists(frame_id):
            return False

        UIManager.FrameClick(frame_id)
        PyUIManager.UIManager.test_mouse_action(frame_id, 8, 0, 0)
        return True
    
    @staticmethod
    @frame_cache(category="UIManagerExtensions", source_lib="IsElementVisible")
    def IsElementVisible(frame_id: int) -> bool:
        """
        Check if a specific frame is open in the UI.

        Args:
            frame_id (int): The ID of the frame to check.

        Returns:
            bool: True if the frame is open, False otherwise.
        """
        return UIManagerExtensions.FrameExists(frame_id)

    class SkillTrainerWindow:
        @staticmethod
        @frame_cache(category="UIManagerExtensions.SkillTrainerWindow", source_lib="IsOpen")
        def IsOpen() -> bool:
            display_type_button_id = UIManager.GetChildFrameID(1746895597,[3])
            return UIManagerExtensions.IsElementVisible(display_type_button_id)

    class MerchantWindow:
        @staticmethod
        @frame_cache(category="UIManagerExtensions.MerchantWindow", source_lib="IsOpen")
        def IsOpen() -> bool:
            merchant_window_frame_id = UIManagerExtensions.GetFrame(UIManagerExtensions.MERCHANT_WINDOW_FRAME)
            return UIManagerExtensions.IsElementVisible(merchant_window_frame_id)
        
    class CollectorWindow:
        @staticmethod
        @frame_cache(category="UIManagerExtensions.CollectorWindow", source_lib="IsOpen")
        def IsOpen() -> bool:
            collector_window_frame_id = UIManagerExtensions.GetFrame(UIManagerExtensions.COLLECTOR_WINDOW_FRAME)
            return UIManagerExtensions.IsElementVisible(collector_window_frame_id)
        
    class CrafterWindow:
        @staticmethod
        @frame_cache(category="UIManagerExtensions.CrafterWindow", source_lib="IsOpen")
        def IsOpen() -> bool:
            crafter_window_frame_id = UIManagerExtensions.GetFrame(UIManagerExtensions.CRAFTER_WINDOW_FRAME)
            return UIManagerExtensions.IsElementVisible(crafter_window_frame_id)

    class UpgradeWindow:
        @staticmethod
        @frame_cache(category="UIManagerExtensions.UpgradeWindow", source_lib="IsOpen")
        def IsOpen() -> bool:
            upgrade_window_frame_id = UIManagerExtensions.GetFrame(UIManagerExtensions.UPGRADE_WINDOW_FRAME)
            return UIManagerExtensions.IsElementVisible(upgrade_window_frame_id)

    class SalvageOptionsWindow:    
        @staticmethod
        @frame_cache(category="UIManagerExtensions.SalvageOptionsWindow", source_lib="IsOpen")
        def IsOpen() -> bool:
            salvage_options_frame_id = UIManagerExtensions.GetFrame(UIManagerExtensions.SALVAGE_OPTIONS_FRAME)
            return UIManagerExtensions.IsElementVisible(salvage_options_frame_id)
        
        @staticmethod
        def Cancel() -> bool:
            cancel_button_frame_id = UIManagerExtensions.GetFrame(UIManagerExtensions.CANCEL_SALVAGE_OPTIONS_FRAME)
            if not UIManagerExtensions.IsElementVisible(cancel_button_frame_id):
                return False

            return UIManagerExtensions.ClickFrame(cancel_button_frame_id)
        
        @staticmethod
        def Confirm() -> bool:
            confirm_button_frame_id = UIManagerExtensions.GetFrame(UIManagerExtensions.CONFIRM_SALVAGE_OPTIONS_FRAME)
            if not UIManagerExtensions.IsElementVisible(confirm_button_frame_id):
                return False

            return UIManagerExtensions.ClickFrame(confirm_button_frame_id)
        
        @staticmethod
        def GetSalvageOptionFramePath(mode: SalvageMode) -> Optional[FramePath]:
            match mode:
                case SalvageMode.Prefix:
                    return UIManagerExtensions.OPTION_PREFIX_SALVAGE_OPTIONS_FRAME
                
                case SalvageMode.Suffix:
                    return UIManagerExtensions.OPTION_SUFFIX_SALVAGE_OPTIONS_FRAME
                
                case SalvageMode.Inscription:
                    return UIManagerExtensions.OPTION_INSCRIPTION_SALVAGE_OPTIONS_FRAME
                
                case SalvageMode.RareCraftingMaterials | SalvageMode.LesserCraftingMaterials:
                    return UIManagerExtensions.OPTION_MATERIALS_SALVAGE_OPTIONS_FRAME
                
                case _:
                    return None
        
        @staticmethod
        def IsOptionVisible(mode: SalvageMode) -> bool:
            option_frame = UIManagerExtensions.SalvageOptionsWindow.GetSalvageOptionFramePath(mode)
            if option_frame is None:
                return False
            
            option_button_frame_id = UIManagerExtensions.GetFrame(option_frame)
            return UIManagerExtensions.IsElementVisible(option_button_frame_id)
        
        @staticmethod
        def SelectOption(mode: SalvageMode) -> bool:
            option_frame = UIManagerExtensions.SalvageOptionsWindow.GetSalvageOptionFramePath(mode)
            if option_frame is None:
                return False

            option_button_frame_id = UIManagerExtensions.GetFrame(option_frame)
            if not UIManagerExtensions.IsElementVisible(option_button_frame_id):
                return False

            return UIManagerExtensions.ClickFrame(option_button_frame_id)
    
    class SalvageConfirmationPopup:
        @staticmethod
        @frame_cache(category="UIManagerExtensions.SalvageConfirmationPopup", source_lib="IsOpen")
        def IsOpen() -> bool:
            confirmation_popup_frame_id = UIManagerExtensions.GetFrame(UIManagerExtensions.MATERIAL_OPTION_CONFIRMATION_FRAME)
            return UIManagerExtensions.IsElementVisible(confirmation_popup_frame_id)
        
        @staticmethod
        def Cancel() -> bool:
            cancel_button_frame_id = UIManagerExtensions.GetFrame(UIManagerExtensions.CANCEL_MATERIAL_OPTION_CONFIRMATION_FRAME)
            
            if not UIManagerExtensions.IsElementVisible(cancel_button_frame_id):
                return False
            
            return UIManagerExtensions.ClickFrame(cancel_button_frame_id)
        
        @staticmethod
        def Confirm() -> bool:
            confirm_button_frame_id = UIManagerExtensions.GetFrame(UIManagerExtensions.CONFIRM_MATERIAL_OPTION_CONFIRMATION_FRAME)
            
            if not UIManagerExtensions.IsElementVisible(confirm_button_frame_id):
                return False
            
            return UIManagerExtensions.ClickFrame(confirm_button_frame_id)
    
    class LesserSalvageWindow:
        @staticmethod
        @frame_cache(category="UIManagerExtensions.LesserSalvageWindow", source_lib="IsOpen")
        def IsOpen() -> bool:
            lesser_salvage_frame_id = UIManagerExtensions.GetFrame(UIManagerExtensions.LESSER_SALVAGE_FRAME)
            return UIManagerExtensions.IsElementVisible(lesser_salvage_frame_id)
        
        @staticmethod
        def Cancel() -> bool:           
            cancel_button_frame_id = UIManagerExtensions.GetFrame(UIManagerExtensions.CANCEL_LESSER_SALVAGE_FRAME)
            
            if not UIManagerExtensions.IsElementVisible(cancel_button_frame_id):
                return False
            
            return UIManagerExtensions.ClickFrame(cancel_button_frame_id)
        
        @staticmethod
        def Confirm() -> bool:
            confirm_button_frame_id = UIManagerExtensions.GetFrame(UIManagerExtensions.CONFIRM_LESSER_SALVAGE_FRAME)
            
            if not UIManagerExtensions.IsElementVisible(confirm_button_frame_id):
                return False
            
            return UIManagerExtensions.ClickFrame(confirm_button_frame_id)

    class ExpertSalvageUnidentifiedWindow:
        @staticmethod
        @frame_cache(category="UIManagerExtensions.ExpertSalvageUnidentifiedWindow", source_lib="IsOpen")
        def IsOpen() -> bool:
            expert_salvage_unidentified_frame_id = UIManagerExtensions.GetFrame(UIManagerExtensions.EXPERT_SALVAGE_UNIDENTIFIED_FRAME)
            return UIManagerExtensions.IsElementVisible(expert_salvage_unidentified_frame_id)
        
        @staticmethod
        def Cancel() -> bool:           
            cancel_button_frame_id = UIManagerExtensions.GetFrame(UIManagerExtensions.CANCEL_EXPERT_SALVAGE_UNIDENTIFIED_FRAME)
            
            if not UIManagerExtensions.IsElementVisible(cancel_button_frame_id):
                return False
            
            return UIManagerExtensions.ClickFrame(cancel_button_frame_id)
        
        @staticmethod
        def Confirm() -> bool:
            confirm_button_frame_id = UIManagerExtensions.GetFrame(UIManagerExtensions.CONFIRM_EXPERT_SALVAGE_UNIDENTIFIED_FRAME)
            
            if not UIManagerExtensions.IsElementVisible(confirm_button_frame_id):
                return False
            
            return UIManagerExtensions.ClickFrame(confirm_button_frame_id)
    
    @staticmethod
    @frame_cache(category="UIManagerExtensions", source_lib="IsAnySalvageWindowOpen")
    def AnySalvageWindowOpen() -> bool:
        return (
            UIManagerExtensions.SalvageConfirmationPopup.IsOpen() or
            UIManagerExtensions.SalvageOptionsWindow.IsOpen() or
            UIManagerExtensions.LesserSalvageWindow.IsOpen() or
            UIManagerExtensions.ExpertSalvageUnidentifiedWindow.IsOpen()
        )
    
    @staticmethod
    def CancelAnySalvageRelatedWindow() -> bool:
        # No need to check if the salvage confirmation popup is open first, as we can cancel it wit hthe salvage options window cancel button, so we can just try to cancel both and it will work regardless of which one is open.
        '''
        if UIManagerExtensions.SalvageConfirmationPopup.IsOpen():
            return UIManagerExtensions.SalvageConfirmationPopup.Cancel()
        '''
        if UIManagerExtensions.SalvageOptionsWindow.IsOpen():
            return UIManagerExtensions.SalvageOptionsWindow.Cancel()        
        
        elif UIManagerExtensions.LesserSalvageWindow.IsOpen():            
            return UIManagerExtensions.LesserSalvageWindow.Cancel()
        
        elif UIManagerExtensions.ExpertSalvageUnidentifiedWindow.IsOpen():
            return UIManagerExtensions.ExpertSalvageUnidentifiedWindow.Cancel()
        
        return False
    
    @staticmethod
    def ConfirmAnySalvageRelatedWindow() -> bool:
        if UIManagerExtensions.SalvageConfirmationPopup.IsOpen():
            return UIManagerExtensions.SalvageConfirmationPopup.Confirm()
        
        elif UIManagerExtensions.SalvageOptionsWindow.IsOpen():
            return UIManagerExtensions.SalvageOptionsWindow.Confirm()
                
        elif UIManagerExtensions.LesserSalvageWindow.IsOpen():            
            return UIManagerExtensions.LesserSalvageWindow.Confirm()
        
        elif UIManagerExtensions.ExpertSalvageUnidentifiedWindow.IsOpen():
            return UIManagerExtensions.ExpertSalvageUnidentifiedWindow.Confirm()
        
        return False

