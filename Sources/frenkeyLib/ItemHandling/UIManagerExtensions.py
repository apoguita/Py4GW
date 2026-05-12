import Py4GW
import PyUIManager

from Py4GWCoreLib.Inventory import Inventory
from Py4GWCoreLib.GWUI import GWUI
from Py4GWCoreLib.UIManager import UIManager
from Sources.frenkeyLib.ItemHandling.Rules.types import SalvageMode


class UIManagerExtensions:
    @staticmethod
    def _frame_exists(frame_id: int) -> bool:
        return isinstance(frame_id, int) and frame_id > 0 and UIManager.FrameExists(frame_id)

    @staticmethod
    def IsElementVisible(frame_id: int) -> bool:
        """
        Check if a specific frame is open in the UI.

        Args:
            frame_id (int): The ID of the frame to check.

        Returns:
            bool: True if the frame is open, False otherwise.
        """
        return UIManagerExtensions._frame_exists(frame_id)

    @staticmethod
    def _find_first_visible_frame(frame_ids: list[int]) -> int:
        for frame_id in frame_ids:
            if UIManagerExtensions._frame_exists(frame_id):
                return frame_id
        return 0

    @staticmethod
    def _click_frame(frame_id: int) -> bool:
        if not UIManagerExtensions._frame_exists(frame_id):
            return False

        UIManager.FrameClick(frame_id)
        PyUIManager.UIManager.test_mouse_action(frame_id, 8, 0, 0)
        return True

    @staticmethod
    def _get_confirm_salvage_window_frame_id() -> int:
        candidate_frame_ids = [
            UIManager.GetChildFrameID(140452905, [6, 110, 6]),
            UIManager.GetChildFrameID(140452905, [6, 111, 6]),
            UIManager.GetChildFrameID(140452905, [6, 100, 6]),
            UIManager.GetChildFrameID(684387150, [0, 6]),
        ]
        return UIManagerExtensions._find_first_visible_frame(candidate_frame_ids)

    @staticmethod
    def _get_salvage_option_entries():
        try:
            visible_entries_by_parent = Inventory._build_visible_frame_entry_map()
            _, _, option_entries = Inventory._get_salvage_choice_dialog_options(visible_entries_by_parent)
            return option_entries
        except Exception:
            return []
    
    @staticmethod
    def GetSalvageOptions() -> dict[SalvageMode, int]:
        options: dict[SalvageMode, int] = {}

        option_entries = UIManagerExtensions._get_salvage_option_entries()
        if option_entries:
            for order, entry in enumerate(option_entries, start=1):
                entry["order"] = order
                path_root_frame_ids = list(entry["path_root_frame_ids"]) if "path_root_frame_ids" in entry else [int(entry["frame_id"])]
                entry["text"] = Inventory._collect_salvage_choice_option_text(
                    path_root_frame_ids,
                    children_map=Inventory._build_frame_children_map(),
                    max_depth=2,
                )

            material_entry, _ = Inventory._choose_salvage_choice_dialog_option(option_entries, strategy=0)
            upgrade_entry, _ = Inventory._choose_salvage_choice_dialog_option(option_entries, strategy=1)

            if material_entry is not None:
                material_frame_id = int(material_entry["frame_id"])
                options[SalvageMode.LesserCraftingMaterials] = material_frame_id
                options[SalvageMode.RareCraftingMaterials] = material_frame_id

            if upgrade_entry is not None:
                upgrade_frame_id = int(upgrade_entry["frame_id"])
                options[SalvageMode.Prefix] = upgrade_frame_id
                options[SalvageMode.Suffix] = upgrade_frame_id
                options[SalvageMode.Inscription] = upgrade_frame_id

            if options:
                return options

        salvage_window_mod_one_id = UIManager.GetChildFrameID(684387150, [5, 0])
        salvage_window_mod_two_id = UIManager.GetChildFrameID(684387150, [5, 1])
        salvage_window_mod_three_id = UIManager.GetChildFrameID(684387150, [5, 2])
        salvage_window_materials_id = UIManager.GetChildFrameID(684387150, [5, 3])

        if UIManagerExtensions.IsElementVisible(salvage_window_mod_one_id):
            options[SalvageMode.Prefix] = salvage_window_mod_one_id

        if UIManagerExtensions.IsElementVisible(salvage_window_mod_two_id):
            options[SalvageMode.Suffix] = salvage_window_mod_two_id

        if UIManagerExtensions.IsElementVisible(salvage_window_mod_three_id):
            options[SalvageMode.Inscription] = salvage_window_mod_three_id

        if UIManagerExtensions.IsElementVisible(salvage_window_materials_id):
            options[SalvageMode.LesserCraftingMaterials] = salvage_window_materials_id
            options[SalvageMode.RareCraftingMaterials] = salvage_window_materials_id

        return options
    
    @staticmethod
    def ConfirmSalvageOption() -> bool:
        salvage_window_salvage_button_id = Inventory._get_salvage_choice_confirm_frame_id()
        if salvage_window_salvage_button_id == 0:
            salvage_window_salvage_button_id = UIManager.GetChildFrameID(684387150, [2])

        if not UIManagerExtensions.IsElementVisible(salvage_window_salvage_button_id):
            return False

        return UIManagerExtensions._click_frame(salvage_window_salvage_button_id)
    
    @staticmethod
    def CancelSalvageOption() -> bool:
        salvage_window_cancel_button_id = UIManager.GetChildFrameID(684387150, [1])
        if not UIManagerExtensions.IsElementVisible(salvage_window_cancel_button_id):
            return False

        return UIManagerExtensions._click_frame(salvage_window_cancel_button_id)
    
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
            if UIManagerExtensions._click_frame(options[option]):
                return UIManagerExtensions.ConfirmSalvageOption()
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
            return UIManagerExtensions._click_frame(options[option])

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
        return Inventory.IsSalvageChoiceMaterialConfirmVisible() or UIManagerExtensions._get_confirm_salvage_window_frame_id() != 0

    @staticmethod
    def ConfirmLesserSalvage():
        inventory = Inventory.inventory_instance()
        try:
            inventory.AcceptSalvageWindow()
        except Exception:
            pass
        return UIManagerExtensions._click_frame(UIManagerExtensions._get_confirm_salvage_window_frame_id())

    @staticmethod
    def ConfirmModMaterialSalvage():
        inventory = Inventory.inventory_instance()
        try:
            inventory.AcceptSalvageWindow()
        except Exception:
            pass
        return UIManagerExtensions._click_frame(UIManagerExtensions._get_confirm_salvage_window_frame_id())
        
    @staticmethod
    def ConfirmModMaterialSalvageVisible():
        return Inventory.IsSalvageChoiceMaterialConfirmVisible() or UIManagerExtensions._get_confirm_salvage_window_frame_id() != 0
        
    @staticmethod
    def CancelLesserSalvage():
        salvage_lower_kit_no_button_id = UIManager.GetChildFrameID(140452905, [
                                                                   6, 100, 4])
        UIManager.FrameClick(salvage_lower_kit_no_button_id)
    
    @staticmethod
    def IsSalvageWindowOpen() -> bool:
        salvage_window_salvage_button_id = Inventory._get_salvage_choice_confirm_frame_id()
        if salvage_window_salvage_button_id == 0:
            salvage_window_salvage_button_id = UIManager.GetChildFrameID(684387150, [2])

        return UIManagerExtensions.IsElementVisible(salvage_window_salvage_button_id)
    
    @staticmethod
    def IsSalvageWindowNoIdentifiedOpen() -> bool:
        salvage_window_salvage_button_id = UIManager.GetChildFrameID(140452905, [6, 111, 6])
        return UIManagerExtensions.IsElementVisible(salvage_window_salvage_button_id)
    
    @staticmethod
    def ConfirmSalvageWindowNoIdentified():
        inventory = Inventory.inventory_instance()
        try:
            inventory.AcceptSalvageWindow()
        except Exception:
            pass
        return UIManagerExtensions._click_frame(UIManager.GetChildFrameID(140452905, [6, 111, 6]))
            
    
    @staticmethod
    def AnySalvageRelatedWindowOpen() -> bool:
        return (
            UIManagerExtensions.IsSalvageWindowOpen()
            or UIManagerExtensions.IsConfirmLesserMaterialsWindowOpen()
            or UIManagerExtensions.ConfirmModMaterialSalvageVisible()
            or UIManagerExtensions.IsSalvageWindowNoIdentifiedOpen()
        )
